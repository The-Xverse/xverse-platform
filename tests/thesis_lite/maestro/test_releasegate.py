"""Actual native gate with fixed owned children; not an admitted ML3 lifecycle."""

from dataclasses import replace
import errno
import hashlib
from importlib.resources import files
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time

import pytest

from xverse.maestro.fence import GatePacket
from .test_boundary import descriptor
from .test_boundary import environment as environment
from .test_boundary import native as native
from .test_leaseguard import guards as guards, SCOPE, frozen


@pytest.fixture(scope="module")
def guard_binary(tmp_path_factory):
    source = files("xverse.maestro").joinpath("native/lease_guard.c")
    data = source.read_bytes()
    root = tmp_path_factory.mktemp("releasegate-native")
    local = root / "lease_guard.c"
    local.write_bytes(data)
    binary = root / "release-gate"
    cmd = [
        "cc",
        "-std=c11",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-DMAESTRO_RELEASE_GATE=1",
        str(local),
        "-o",
        str(binary),
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr.decode()
    receipts = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipts:
        output = Path(receipts)
        output.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        (output / ("releasegate-native-" + digest + ".bin")).write_bytes(
            binary.read_bytes()
        )
        (output / ("releasegate-native-" + digest + ".json")).write_text(
            json.dumps(
                {
                    "source_sha256": hashlib.sha256(data).hexdigest(),
                    "binary_sha256": digest,
                    "command": cmd,
                    "returncode": result.returncode,
                    "compiler": subprocess.check_output(
                        ["cc", "--version"], text=True
                    ).splitlines()[0],
                    "build_variant": "explicit RG06 one-use unfreeze gate",
                    "role": "owned kernel component tests, no operator/run admission",
                },
                indent=2,
            )
            + "\n"
        )
    return binary


def receive(channel):
    assert select.select([channel], [], [], 2)[0]
    return GatePacket.decode(channel.recv(257))


def empty(kind, sequence, deadline, epoch=7):
    return GatePacket(kind, sequence, deadline, SCOPE, epoch)


def arm_packet(deadline, sequence=1):
    # Explicit test facts, never claimed to be actual M3/Argus/supervisor approvals.
    return GatePacket(
        3,
        sequence,
        deadline,
        SCOPE,
        7,
        operation=b"o" * 32,
        intent=b"i" * 32,
        flush=b"f" * 32,
        stage=b"a" * 32,
    )


def staged(environment, native, guards, *, lease=1.5):
    factory, spawn, _ = environment
    manager, _ = factory(seconds=8)
    unit = descriptor()
    manager.create_frozen(unit)
    child, marker, line = spawn(native, manager, unit)
    assert line.startswith("CHILD ")
    fd = manager._entries[unit.key].fd
    process, channel, deadline = guards(fd, lease=lease, generation=6, args={7: "7"})
    ready = receive(channel)
    assert ready == empty(16, 0, deadline)
    return manager, unit, child, marker, fd, process, channel, deadline


def arm(channel, deadline, sequence=1):
    request = arm_packet(deadline, sequence)
    channel.send(request.encode())
    ticket = receive(channel)
    assert ticket.kind == 20 and ticket.reason == 0 and ticket.epoch == 7
    assert ticket.deadline_ns == deadline and ticket.sequence == sequence
    assert ticket.nonce != bytes(32)
    assert replace(ticket, kind=3, nonce=bytes(32)) == request
    return ticket


def silent(marker):
    assert not select.select([marker], [], [], 0.02)[0]


def test_actual_release_then_cancel_runs_one_fixed_child(environment, native, guards):
    manager, unit, child, marker, fd, process, channel, deadline = staged(
        environment, native, guards
    )
    silent(marker)
    ticket = arm(channel, deadline)
    silent(marker)
    channel.send(replace(ticket, kind=4, sequence=2).encode())
    released = receive(channel)
    assert released.kind == 21 and released.epoch == 7 and released.nonce == bytes(32)
    assert select.select([marker], [], [], 1)[0] and os.read(marker, 1) == b"M"
    assert not frozen(fd) and child.poll() is None
    channel.send(empty(2, 3, deadline).encode())
    stopped = receive(channel)
    assert stopped.kind == 18 and stopped.epoch == 8 and stopped.reason == 5
    assert process.wait(timeout=2) == 0 and frozen(fd)
    assert manager.force_cleanup(unit).termination_observed


def test_cancel_before_release_executes_no_workload(environment, native, guards):
    manager, unit, _, marker, fd, process, channel, deadline = staged(
        environment, native, guards
    )
    ticket = arm(channel, deadline)
    channel.send(empty(2, 2, deadline).encode())
    closed = receive(channel)
    assert closed.kind == 18 and closed.epoch == 8
    assert process.wait(timeout=2) == 0 and frozen(fd)
    with pytest.raises((BrokenPipeError, ConnectionResetError)):
        channel.send(replace(ticket, kind=4, sequence=3).encode())
    silent(marker)
    assert manager.force_cleanup(unit).boundary_released


@pytest.mark.parametrize(
    "bad",
    [
        "scope",
        "epoch",
        "operation",
        "intent",
        "flush",
        "stage",
        "nonce",
        "deadline",
        "reserved",
        "kind",
        "short",
        "long",
        "legacy",
    ],
)
def test_bad_release_never_unfreezes(environment, native, guards, bad):
    manager, unit, _, marker, fd, process, channel, deadline = staged(
        environment, native, guards
    )
    ticket = arm(channel, deadline)
    release = replace(ticket, kind=4, sequence=2)
    if bad in ("scope", "operation", "intent", "flush", "stage", "nonce"):
        release = replace(release, **{bad: b"x" * 32})
    elif bad == "epoch":
        release = replace(release, epoch=8)
    elif bad == "deadline":
        release = replace(release, deadline_ns=deadline + 1)
    data = release.encode()
    if bad == "reserved":
        data = data[:-1] + b"X"
    elif bad == "kind":
        data = data[:7] + b"\x09" + data[8:]
    elif bad == "short":
        data = data[:-1]
    elif bad == "long":
        data += b"X"
    elif bad == "legacy":
        data = b"LG05" + data[4:64]
    channel.send(data)
    closed = receive(channel)
    assert closed.kind == 18 and closed.epoch == 8 and closed.reason == 4
    assert process.wait(timeout=2) == 0 and frozen(fd)
    silent(marker)
    assert manager.force_cleanup(unit).termination_observed


@pytest.mark.parametrize("missing_offset", [72, 104, 136, 168])
def test_missing_stage_or_durable_ack_identity_denies_arm(
    environment, native, guards, missing_offset
):
    manager, unit, _, marker, fd, process, channel, deadline = staged(
        environment, native, guards
    )
    data = arm_packet(deadline).encode()
    data = data[:missing_offset] + bytes(32) + data[missing_offset + 32 :]
    channel.send(data)
    response = receive(channel)
    assert response.kind == 18 and response.reason == 4 and response.epoch == 8
    assert process.wait(timeout=2) == 0 and frozen(fd)
    silent(marker)
    assert manager.force_cleanup(unit).termination_observed


def test_ticket_ttl_not_extended_by_lease_renewal(environment, native, guards):
    manager, unit, _, marker, fd, process, channel, deadline = staged(
        environment, native, guards, lease=0.5
    )
    expiry = time.monotonic_ns() + 150_000_000
    ticket = arm(channel, expiry)
    channel.send(empty(1, 2, deadline + 800_000_000).encode())
    assert receive(channel).kind == 17
    time.sleep(0.2)
    channel.send(replace(ticket, kind=4, sequence=3).encode())
    response = receive(channel)
    assert response.kind == 18 and response.epoch == 8
    assert process.wait(timeout=2) == 0 and frozen(fd)
    silent(marker)
    assert manager.force_cleanup(unit).boundary_released


@pytest.mark.parametrize("replay", ["release", "arm"])
def test_consumed_ticket_cannot_release_or_arm_again(
    environment, native, guards, replay
):
    manager, unit, _, marker, fd, process, channel, deadline = staged(
        environment, native, guards
    )
    ticket = arm(channel, deadline)
    channel.send(replace(ticket, kind=4, sequence=2).encode())
    assert receive(channel).kind == 21
    assert select.select([marker], [], [], 1)[0] and os.read(marker, 1) == b"M"
    command = (
        replace(ticket, kind=4, sequence=3)
        if replay == "release"
        else arm_packet(deadline, 3)
    )
    channel.send(command.encode())
    assert receive(channel).kind == 18
    assert process.wait(timeout=2) == 0 and frozen(fd)
    assert manager.force_cleanup(unit).termination_observed


def test_forked_sender_cannot_release_original_ticket(environment, native, guards):
    manager, unit, _, marker, fd, process, channel, deadline = staged(
        environment, native, guards
    )
    ticket = arm(channel, deadline)
    pid = os.fork()
    if pid == 0:
        try:
            channel.send(replace(ticket, kind=4, sequence=2).encode())
        finally:
            os._exit(0)
    assert os.waitpid(pid, 0)[1] == 0
    assert receive(channel).kind == 18
    assert process.wait(timeout=2) == 0 and frozen(fd)
    silent(marker)
    assert manager.force_cleanup(unit).termination_observed


def test_delayed_production_gate_cannot_thaw_after_exact_cleanup(
    environment, native, guards
):
    manager, unit, child, marker, fd, process, channel, deadline = staged(
        environment, native, guards
    )
    sentinel = descriptor("sentinel")
    manager.create_frozen(sentinel)
    sentinel_fd = manager._entries[sentinel.key].fd
    ticket = arm(channel, deadline)
    # The production binary already retains its freeze control FD from bootstrap.
    retained = os.open("cgroup.freeze", os.O_WRONLY, dir_fd=fd)
    try:
        os.kill(process.pid, signal.SIGSTOP)
        os.waitid(os.P_PID, process.pid, os.WSTOPPED)
        channel.send(replace(ticket, kind=4, sequence=2).encode())
        assert manager.force_cleanup(unit).boundary_released
        assert child.wait(timeout=2) == 0
        # The only pipe bytes possible are EOF; fixed child never executed its marker.
        assert os.read(marker, 1) == b""
        with pytest.raises(OSError) as error:
            os.write(retained, b"0")
        assert error.value.errno in (errno.ENODEV, errno.ENOENT)
        os.kill(process.pid, signal.SIGCONT)
        assert process.wait(timeout=2) == 70
        try:
            packet = channel.recv(257)
        except ConnectionResetError:
            packet = b""  # final ACK may be unavailable; never synthesize it
        if packet:
            response = GatePacket.decode(packet)
            assert response.kind == 19 and response.epoch == 8
        assert frozen(sentinel_fd)
        assert manager.force_cleanup(sentinel).boundary_released
    finally:
        os.close(retained)
        if process.poll() is None:
            os.kill(process.pid, signal.SIGCONT)


@pytest.mark.parametrize("epoch", ["-1", "True", str(2**64 - 1), str(2**64)])
def test_invalid_initial_epoch_rejected(environment, native, guards, epoch):
    factory, _, _ = environment
    manager, _ = factory()
    unit = descriptor()
    manager.create_frozen(unit)
    process, channel, _ = guards(manager._entries[unit.key].fd, args={7: epoch})
    assert process.wait(timeout=2) == 64 and channel.recv(257) == b""
