"""Real freeze-only guard component tests; no admitted lifecycle/launcher."""
import array
import hashlib
from importlib.resources import files
import json
import os
from pathlib import Path
import select
import signal
import socket
import struct
import subprocess
import time
import uuid

import pytest

from .test_boundary import descriptor, _write
from .test_boundary import environment as environment
from .test_boundary import native as native

WIRE = struct.Struct('!4sIQQ32sQ')
SCOPE = hashlib.sha256(b'owned-test-scope-not-admission').digest()


def message(kind, seq, deadline, scope=SCOPE, reason=0):
    return WIRE.pack(b'LG05', kind, seq, deadline, scope, reason)


def receive(channel):
    assert select.select([channel], [], [], 3)[0], 'native guard reply deadline'
    packet = channel.recv(65)
    assert len(packet) == WIRE.size
    value = WIRE.unpack(packet)
    assert value[0] == b'LG05' and value[4] == SCOPE
    return value


def frozen(fd):
    value = os.open('cgroup.events', os.O_RDONLY, dir_fd=fd)
    try:
        return b'frozen 1\n' in os.read(value, 1024)
    finally:
        os.close(value)


@pytest.fixture(scope='module')
def guard_binary(tmp_path_factory):
    source = files('xverse.maestro').joinpath('native/lease_guard.c')
    data = source.read_bytes()
    root = tmp_path_factory.mktemp('leaseguard-native')
    local = root / 'lease_guard.c'
    local.write_bytes(data)
    binary = root / 'lease-guard'
    command = ['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
               str(local), '-o', str(binary)]
    result = subprocess.run(command, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr.decode()
    receipts = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if receipts:
        output = Path(receipts)
        output.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        (output / ('leaseguard-native-' + digest + '.bin')).write_bytes(binary.read_bytes())
        (output / ('leaseguard-native-' + digest + '.json')).write_text(json.dumps({
            'source_sha256': hashlib.sha256(data).hexdigest(),
            'binary_sha256': digest, 'command': command, 'returncode': result.returncode,
            'compiler': subprocess.check_output(['cc', '--version'], text=True).splitlines()[0],
            'source_origin': str(source), 'role': 'freeze-only component, no runtime admission',
        }, indent=2) + '\n')
    return binary


@pytest.fixture
def guards(guard_binary, tmp_path):
    children = []
    receipts = Path(os.environ.get('MAESTRO_BOUNDARY_RECEIPTS', str(tmp_path)))
    receipts.mkdir(parents=True, exist_ok=True)
    record = receipts / ('leaseguard-children-' + uuid.uuid4().hex + '.json')
    runs = []

    def save():
        pending = record.with_suffix('.pending')
        with pending.open('w') as stream:
            json.dump({'scope': 'test bootstrap only, not runtime C1', 'runs': runs}, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(pending, record)
        parent = os.open(receipts, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)

    def start(cgfd, lease=.25, generation=3, reserve=.5, args=None, sndbuf=None):
        owner, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        if sndbuf:
            child.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, sndbuf)
        now = time.monotonic_ns()
        deadline = now + int(lease * 1e9)
        argv = [str(guard_binary), str(cgfd), str(child.fileno()),
                str(now + int(generation * 1e9)), str(deadline),
                str(int(reserve * 1e9)), SCOPE.hex()]
        if args:
            for index, value in args.items():
                argv[index] = value
        identity = os.fstat(cgfd)
        receipt = {'command': argv, 'state': 'reserved', 'reaped': False,
                   'boundary_identity': [identity.st_dev, identity.st_ino]}
        runs.append(receipt)
        save()
        try:
            process = subprocess.Popen(argv, pass_fds=(cgfd, child.fileno()),
                                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
        finally:
            child.close()
        children.append((process, owner, receipt))
        receipt.update(pid=process.pid, state='created')
        save()
        return process, owner, deadline

    yield start
    for process, channel, receipt in children:
        channel.close()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            # Test maintenance owns this original Popen. No discovery/adoption.
            process.kill()
            process.wait(timeout=2)
            receipt['external_test_kill_required'] = True
        receipt.update(reaped=True, state='reaped', returncode=process.returncode)
    save()


def ready(guards, manager, unit, **options):
    fd = manager._entries[unit.key].fd
    process, channel, deadline = guards(fd, **options)
    response = receive(channel)
    assert response == (b'LG05', 16, 0, deadline, SCOPE, 0)
    return process, channel, deadline, fd


def test_expiry_is_native_and_preserves_live_membership(environment, native, guards):
    factory, spawn, _ = environment
    manager, _ = factory(seconds=8)
    unit, sentinel = descriptor(), descriptor('sentinel')
    manager.create_frozen(unit)
    manager.create_frozen(sentinel)
    process, marker, line = spawn(native, manager, unit)
    assert line.startswith('CHILD ')
    _, sentinel_marker, sentinel_line = spawn(native, manager, sentinel)
    assert sentinel_line.startswith('CHILD ')
    guard, channel, _, fd = ready(guards, manager, unit, lease=.3)
    _write(fd, 'cgroup.freeze', b'0')  # test-only thaw, no production Release API
    assert select.select([marker], [], [], 1)[0]
    assert os.read(marker, 1) == b'M'
    before = time.monotonic()
    # No Python tick, provider routine, storage call or heartbeat services the guard.
    terminal = receive(channel)
    assert terminal[1] == 18 and terminal[5] == 1
    assert time.monotonic() - before < 2
    assert guard.wait(timeout=2) == 0 and frozen(fd)
    assert manager.residual_membership(unit) and process.poll() is None
    assert manager.residual_membership(sentinel)
    assert not select.select([sentinel_marker], [], [], 0)[0]
    assert manager.force_cleanup(unit).termination_observed
    assert manager.force_cleanup(sentinel).termination_observed


def test_renewal_is_absolute_and_acknowledged(environment, guards):
    factory, _, _ = environment
    manager, _ = factory(seconds=8)
    unit = descriptor()
    manager.create_frozen(unit)
    process, channel, original, fd = ready(guards, manager, unit, lease=.25)
    extended = time.monotonic_ns() + 650_000_000
    channel.send(message(1, 1, extended))
    assert receive(channel) == (b'LG05', 17, 1, extended, SCOPE, 0)
    _write(fd, 'cgroup.freeze', b'0')
    time.sleep(max(0, (original - time.monotonic_ns()) / 1e9) + .04)
    assert not frozen(fd)
    assert receive(channel) == (b'LG05', 18, 1, extended, SCOPE, 1)
    assert process.wait(timeout=2) == 0 and frozen(fd)
    assert manager.force_cleanup(unit).boundary_released


@pytest.mark.parametrize('control', ['cancel', 'close'])
def test_cancel_or_control_loss_freezes(environment, guards, control):
    factory, _, _ = environment
    manager, _ = factory()
    unit = descriptor()
    manager.create_frozen(unit)
    process, channel, deadline, fd = ready(guards, manager, unit, lease=1)
    _write(fd, 'cgroup.freeze', b'0')
    if control == 'cancel':
        channel.send(message(2, 1, deadline))
        assert receive(channel) == (b'LG05', 18, 1, deadline, SCOPE, 5)
        with pytest.raises((BrokenPipeError, ConnectionResetError)):
            process.wait(timeout=2)
            channel.send(message(1, 2, deadline + 1))
    else:
        channel.close()
    assert process.wait(timeout=2) == 0 and frozen(fd)


@pytest.mark.parametrize('bad', ['magic', 'kind', 'scope', 'sequence', 'reason',
                                'short', 'long', 'zero', 'past', 'same', 'too_long',
                                'reserve', 'cancel_deadline', 'uintmax'])
def test_bad_commands_freeze_without_renewal(environment, guards, bad):
    factory, _, _ = environment
    manager, _ = factory()
    unit = descriptor()
    manager.create_frozen(unit)
    process, channel, deadline, fd = ready(guards, manager, unit, lease=1)
    packet = message(1, 1, deadline + 50_000_000)
    if bad == 'magic':
        packet = b'BAD!' + packet[4:]
    elif bad == 'kind':
        packet = message(18, 1, deadline)
    elif bad == 'scope':
        packet = message(1, 1, deadline + 1, b'x' * 32)
    elif bad == 'sequence':
        packet = message(1, 2, deadline + 1)
    elif bad == 'reason':
        packet = message(1, 1, deadline + 1, reason=1)
    elif bad == 'short':
        packet = packet[:-1]
    elif bad == 'long':
        packet += b'extra'
    elif bad == 'zero':
        packet = b''
    elif bad == 'past':
        packet = message(1, 1, time.monotonic_ns() - 1)
    elif bad == 'same':
        packet = message(1, 1, deadline)
    elif bad == 'too_long':
        packet = message(1, 1, time.monotonic_ns() + 6_000_000_000)
    elif bad == 'reserve':
        packet = message(1, 1, time.monotonic_ns() + 2_900_000_000)
    elif bad == 'cancel_deadline':
        packet = message(2, 1, deadline + 1)
    elif bad == 'uintmax':
        packet = message(1, 1, 2**64 - 1)
    _write(fd, 'cgroup.freeze', b'0')
    channel.send(packet)
    terminal = receive(channel)
    assert terminal[1] == 18 and terminal[5] == (3 if bad == 'zero' else 4)
    assert terminal[2] == 0 and terminal[3] == deadline
    assert process.wait(timeout=2) == 0 and frozen(fd)


@pytest.mark.parametrize('count', [1, 32])
def test_passed_descriptors_are_closed_and_rejected(environment, guards, count):
    factory, _, _ = environment
    manager, _ = factory()
    unit = descriptor()
    manager.create_frozen(unit)
    process, channel, deadline, fd = ready(guards, manager, unit, lease=1)
    _write(fd, 'cgroup.freeze', b'0')
    channel.sendmsg([message(1, 1, deadline + 1)],
                    [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array('i', [fd] * count))])
    terminal = receive(channel)
    assert terminal[1] == 18 and terminal[5] == 4
    assert process.wait(timeout=2) == 0 and frozen(fd)


def test_forked_sender_cannot_renew_inherited_channel(environment, guards):
    factory, _, _ = environment
    manager, _ = factory()
    unit = descriptor()
    manager.create_frozen(unit)
    process, channel, deadline, fd = ready(guards, manager, unit, lease=1)
    _write(fd, 'cgroup.freeze', b'0')
    child = os.fork()
    if child == 0:
        try:
            channel.send(message(1, 1, deadline + 1))
        finally:
            os._exit(0)
    assert os.waitpid(child, 0)[1] == 0
    terminal = receive(channel)
    assert terminal[1] == 18 and terminal[5] == 4
    assert process.wait(timeout=2) == 0 and frozen(fd)


def test_queued_heartbeat_after_expiry_does_not_revive(environment, guards):
    factory, _, _ = environment
    manager, _ = factory()
    unit = descriptor()
    manager.create_frozen(unit)
    process, channel, _, fd = ready(guards, manager, unit, lease=.15)
    os.kill(process.pid, signal.SIGSTOP)  # exact original test Popen, never discovered PID
    os.waitid(os.P_PID, process.pid, os.WSTOPPED)
    _write(fd, 'cgroup.freeze', b'0')
    time.sleep(.2)
    # This intentionally demonstrates that SIGSTOP is outside any bounded lease proof.
    assert not frozen(fd)
    channel.send(message(1, 1, time.monotonic_ns() + 500_000_000))
    os.kill(process.pid, signal.SIGCONT)
    terminal = receive(channel)
    assert terminal[1] == 18 and terminal[5] == 1 and terminal[2] == 0
    assert process.wait(timeout=2) == 0 and frozen(fd)


def test_authority_expired_does_not_gain_late_freeze_right(environment, guards):
    factory, _, _ = environment
    manager, _ = factory()
    unit = descriptor()
    manager.create_frozen(unit)
    process, channel, _, fd = ready(guards, manager, unit, lease=.1, generation=.45, reserve=.2)
    os.kill(process.pid, signal.SIGSTOP)
    os.waitid(os.P_PID, process.pid, os.WSTOPPED)
    _write(fd, 'cgroup.freeze', b'0')
    time.sleep(.5)
    os.kill(process.pid, signal.SIGCONT)
    terminal = receive(channel)
    assert terminal[1] == 19 and terminal[5] == 7
    assert process.wait(timeout=2) == 70 and not frozen(fd)
    # Original outer C1, not restored guard authority, still owns cleanup.
    assert manager.force_cleanup(unit).boundary_released


def test_deleted_boundary_is_unresolved(environment, guards):
    factory, _, _ = environment
    manager, _ = factory()
    unit = descriptor()
    manager.create_frozen(unit)
    process, channel, deadline, _ = ready(guards, manager, unit, lease=1)
    assert manager.force_cleanup(unit).boundary_released
    channel.send(message(2, 1, deadline))
    terminal = receive(channel)
    assert terminal[1] == 19 and terminal[5] == 6
    assert process.wait(timeout=2) == 70


def test_killed_guard_is_not_a_fail_closed_fence(environment, guards):
    factory, _, _ = environment
    manager, _ = factory()
    unit = descriptor()
    manager.create_frozen(unit)
    process, channel, _, fd = ready(guards, manager, unit, lease=.1)
    _write(fd, 'cgroup.freeze', b'0')
    process.kill()
    assert process.wait(timeout=2) == -signal.SIGKILL
    time.sleep(.15)
    assert not frozen(fd)
    assert channel.recv(64) == b''
    assert manager.force_cleanup(unit).boundary_released


def test_reply_backpressure_cannot_block_freeze(environment, guards):
    factory, _, _ = environment
    manager, _ = factory()
    unit = descriptor()
    manager.create_frozen(unit)
    process, channel, deadline, fd = ready(guards, manager, unit, lease=1, sndbuf=1024)
    _write(fd, 'cgroup.freeze', b'0')
    channel.setblocking(False)
    for seq in range(1, 128):
        try:
            channel.send(message(1, seq, deadline + seq))
        except (BlockingIOError, BrokenPipeError, ConnectionResetError):
            break
    assert process.wait(timeout=2) == 0 and frozen(fd)


def test_original_supervisor_pidfd_independent_of_socket_loss(environment, guard_binary):
    factory, _, _ = environment
    manager, _ = factory(seconds=8)
    unit = descriptor()
    manager.create_frozen(unit)
    fd = manager._entries[unit.key].fd
    result = subprocess.run([os.sys.executable, '-I',
                             str(Path(__file__).with_name('leaseguard_owner.py')),
                             str(guard_binary), str(fd)],
                            pass_fds=(fd,), capture_output=True, text=True, timeout=8)
    assert result.returncode == 0, result.stdout + result.stderr
    proof = json.loads(result.stdout)
    assert proof['reason'] == 2 and proof['guard_reaped'] and proof['owner_reaped']
    assert proof['socket_still_open'] and frozen(fd)


@pytest.mark.parametrize('args', [[], ['bad'], ['3', '4', '-1', '1', '1', 'a' * 64],
                                    ['3', '4', '18446744073709551616', '1', '1', 'a' * 64]])
def test_native_cli_rejects_invalid_input(guard_binary, args):
    assert subprocess.run([str(guard_binary), *args], timeout=3).returncode == 64


@pytest.mark.parametrize('bad', [
    {5: '0'}, {5: '1000000001'}, {6: 'A' * 64}, {6: 'a' * 63},
    {3: '18446744073709551615'}, {4: '0'},
])
def test_bootstrap_rejects_bad_limits_scope(environment, guards, bad):
    factory, _, _ = environment
    manager, _ = factory()
    unit = descriptor()
    manager.create_frozen(unit)
    process, channel, _ = guards(manager._entries[unit.key].fd, args=bad)
    assert process.wait(timeout=2) == 64 and channel.recv(64) == b''
