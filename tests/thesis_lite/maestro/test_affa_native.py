"""Owned native AFFA controls; standalone fixture, not bootstrap/run admission."""

from dataclasses import replace
import array
import hashlib
import hmac
from importlib.resources import files
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time

import pytest
from xverse.maestro.affa_protocol import (
    AuthorityConfig,
    AuthorityFrame,
    AuthorityKind as K,
    AuthorityRecipe,
    AuthorityUnit,
)
from xverse.maestro.bootstrap import _sealed, seal_helper_image
from xverse.maestro.prbc import BoundaryDescriptor
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries


def digest(data):
    return hashlib.sha256(data).digest()


@pytest.fixture(scope="module")
def authority_binary(tmp_path_factory):
    source = files("xverse.maestro").joinpath("native/run_authority.c")
    local = tmp_path_factory.mktemp("affa-native")
    path = local / "authority.c"
    path.write_bytes(source.read_bytes())
    binary = local / "authority"
    command = [
        "cc",
        "-std=c11",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        str(path),
        "-lcrypto",
        "-o",
        str(binary),
    ]
    subprocess.run(command, check=True, capture_output=True, timeout=30)
    output = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if output:
        target = Path(output)
        target.mkdir(parents=True, exist_ok=True)
        (target / "affa-native.bin").write_bytes(binary.read_bytes())
        (target / "affa-native.json").write_text(
            json.dumps(
                {
                    "command": command,
                    "returncode": 0,
                    "source_sha256": digest(path.read_bytes()).hex(),
                    "binary_sha256": digest(binary.read_bytes()).hex(),
                }
            )
        )
    return binary


# F-02 (finding 403): ADVANCE frames must carry a nonzero ticket; rpc() replaces this placeholder
# with the supervisor-equivalent WATCH token of the boundary descriptor being sent.
WATCH_PLACEHOLDER = b"W" * 32


class Harness:
    def __init__(self, manager, cwd, image, units):
        self.manager, self.cwd, self.image, self.units = manager, cwd, image, units
        self.fds, self.childfds, self.sequence, self.epoch = [], [], 0, 0
        self.config = self.channel = self.process = None
        self.closed = False
        self.watch_key = None

    def end(self):
        return min(
            time.monotonic_ns() + 2_000_000_000,
            self.config.generation_ns if self.closed else self.lease,
        )

    def watch_token(self, fd):
        """The supervisor's WATCH token for a boundary descriptor (F-02, finding 403)."""
        st = os.fstat(fd)
        return hmac.new(self.watch_key, b"MLWT" + st.st_dev.to_bytes(8, "big") + st.st_ino.to_bytes(8, "big"),
                        hashlib.sha256).digest()

    def rpc(self, frame, fds=()):
        if frame.kind is K.ADVANCE and fds and frame.ticket == WATCH_PLACEHOLDER:
            frame = replace(frame, ticket=self.watch_token(fds[0]))
        self.sequence += 1
        end = self.end()
        if frame.kind is K.RELEASE:
            end = min(end, self.units[frame.slot - 1]["ticket_end"])
        frame = replace(
            frame, sequence=self.sequence, deadline_ns=end, epoch=self.epoch
        )
        ancillary = (
            [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", fds))]
            if fds
            else []
        )
        self.channel.sendmsg([frame.encode()], ancillary)
        raw, anc, flags, _ = self.channel.recvmsg(
            321, socket.CMSG_SPACE(16) + socket.CMSG_SPACE(12)
        )
        received, peers = [], []
        try:
            for level, kind, value in anc:
                if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                    rights = array.array("i")
                    rights.frombytes(value)
                    received.extend(rights)
                elif level == socket.SOL_SOCKET and kind == socket.SCM_CREDENTIALS:
                    import struct

                    peers.append(struct.unpack("3i", value))
                else:
                    raise AssertionError("unexpected ancillary data")
            assert not flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC)
            assert len(peers) == 1 and peers[0] == (
                self.process.pid,
                os.getuid(),
                os.getgid(),
            )
            reply = AuthorityFrame.decode(raw)
            assert reply.sequence == self.sequence and reply.scope == self.config.scope
            self.epoch = reply.epoch
            if reply.kind in (K.CANCELLED, K.REJECTED):
                self.closed = True
            assert len(received) == (1 if reply.kind is K.STAGED else 0)
            self.childfds.extend(received)
            received = []
            return reply
        finally:
            for fd in received:
                os.close(fd)

    def frame(self, kind, index):
        u = self.units[index]
        return AuthorityFrame(
            kind,
            1,
            self.end(),
            self.config.scope,
            index + 1,
            self.epoch,
            u["generation"],
            u["operation"],
            digest(b"action" + bytes([index])),
            u["intent"],
            u["mirror"],
            u["boundary"],
            ticket=(u.get("ticket", bytes(32)) if kind is K.RELEASE
                    else WATCH_PLACEHOLDER if kind is K.ADVANCE else bytes(32)),
            handle=u.get("handle", bytes(32)),
        )

    def stage(self, index):
        reply = self.rpc(self.frame(K.STAGE, index))
        assert reply.kind is K.STAGED
        self.units[index]["handle"] = reply.handle

    def arm(self, index):
        reply = self.rpc(self.frame(K.ARM, index))
        assert reply.kind is K.ARMED
        self.units[index]["ticket"] = reply.ticket
        self.units[index]["ticket_end"] = reply.deadline_ns

    def release(self, index):
        return self.rpc(
            replace(self.frame(K.RELEASE, index), ticket=self.units[index]["ticket"])
        )

    def cancel(self):
        reply = self.rpc(AuthorityFrame(K.CANCEL, 1, self.end(), self.config.scope))
        assert reply.kind is K.CANCELLED
        return reply

    def stop_retire(self, index):
        stopped = self.rpc(self.frame(K.STOP, index))
        assert stopped.kind is K.STOPPED and stopped.state & 8
        retired = self.rpc(self.frame(K.RETIRE, index))
        assert retired.kind is K.RETIRED and retired.state & 128
        self.units[index]["stop_state"] = stopped.state
        self.units[index]["retire_state"] = retired.state
        return retired


@pytest.fixture
def authority(environment, authority_binary, binaries, tmp_path):
    factory, _, root = environment
    manager, _ = factory(seconds=40)
    cwd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    image = seal_helper_image(
        binaries["workload"],
        digest="sha256:" + digest(binaries["workload"].read_bytes()).hex(),
        argv0=str(binaries["workload"]),
    )
    h = Harness(manager, cwd, image, [])
    parent = peer = None
    forced = False
    try:
        records = []
        for i in range(2):
            desc = BoundaryDescriptor("run", f"u{i}", 1, f"initial-{i}", 0)
            manager.create_frozen(desc)
            cg = manager._entries[desc.key].fd
            recipe = AuthorityRecipe(
                ("/fixture", f"u{i}.marker", "single"), ("MAESTRO_VISIBLE=declared",)
            ).encode()
            recipe_fd = _sealed(recipe, "owned-affa-recipe")
            h.fds.append(recipe_fd)
            st, work = os.fstat(cg), os.fstat(cwd)
            records.append(
                AuthorityUnit(
                    digest(bytes([i + 1])),
                    bytes.fromhex(image.digest[7:]),
                    digest(recipe),
                    st.st_dev,
                    st.st_ino,
                    work.st_dev,
                    work.st_ino,
                    1,
                    2,
                )
            )
            h.units.append(
                dict(
                    descriptor=desc,
                    cg=cg,
                    recipe=recipe_fd,
                    generation=1,
                    operation=bytes([i + 1]) * 16,
                    intent=digest(b"intent" + bytes([i])),
                    mirror=digest(b"mirror" + bytes([i])),
                    boundary=digest(b"boundary" + bytes([i])),
                )
            )
        h.lease = time.monotonic_ns() + 4_800_000_000
        h.config = AuthorityConfig(
            int(manager._admission.teardown_deadline.monotonic_seconds * 1e9),
            h.lease,
            0,
            digest(b"owned-AFFA-run"),
            digest(b"original-supervisor"),
            tuple(records),
        )
        config_fd = _sealed(h.config.encode(), "owned-affa-config")
        h.fds.append(config_fd)
        # F-02 (finding 403): a direct launch plays the supervisor and supplies its own sealed watch key.
        h.watch_key = os.urandom(32)
        key_fd = _sealed(h.watch_key, "owned-affa-watch-key")
        h.fds.append(key_fd)
        parent, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        parent.settimeout(3)
        h.channel = parent
        h.process = subprocess.Popen(
            [str(authority_binary), str(peer.fileno()), str(config_fd), str(key_fd)],
            pass_fds=(peer.fileno(), config_fd, key_fd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        peer.close()
        peer = None
        data, anc, flags, _ = parent.recvmsg(321, socket.CMSG_SPACE(12))
        ready = AuthorityFrame.decode(data)
        assert (
            ready.kind is K.READY and ready.scope == h.config.scope and ready.epoch == 0
        )
        for i, u in enumerate(h.units):
            r = records[i]
            frame = AuthorityFrame(
                K.REGISTER,
                1,
                h.end(),
                h.config.scope,
                i + 1,
                0,
                1,
                first=r.binding,
                second=r.image,
                third=r.recipe,
                fourth=u["boundary"],
            )
            assert (
                h.rpc(frame, (u["cg"], image.descriptor, cwd, u["recipe"])).kind
                is K.REGISTERED
            )
        for i in range(2):
            assert h.rpc(h.frame(K.INTENT, i)).kind is K.INTENT_RECORDED
        yield h, tmp_path
    finally:
        if peer:
            peer.close()
        if parent:
            parent.close()
        if h.process:
            try:
                h.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                forced = True
                pidfd = os.pidfd_open(h.process.pid)
                try:
                    signal.pidfd_send_signal(pidfd, signal.SIGKILL)
                finally:
                    os.close(pidfd)
                h.process.wait(timeout=3)
            h.process.stderr.close()
        for fd in h.childfds + h.fds:
            os.close(fd)
        os.close(image.descriptor)
        os.close(cwd)
        output = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
        if output:
            (
                Path(output)
                / f"affa-standalone-reaped-{os.getpid()}-{tmp_path.name}.json"
            ).write_text(
                json.dumps(
                    {
                        "authority_reaped": h.process is not None
                        and h.process.returncode is not None,
                        "returncode": h.process.returncode if h.process else None,
                        "external_authority_kill": forced
                        or getattr(h, "external_authority_kill", False),
                        "component_only": True,
                        "source_sha256": digest(Path(__file__).read_bytes()).hex(),
                    }
                )
            )


def wait_marker(path, count=1):
    end = time.monotonic() + 1
    while time.monotonic() < end:
        if path.exists() and path.read_bytes().count(b"EXEC\n") == count:
            return
        time.sleep(0.005)
    raise AssertionError("expected actual workload marker")


def test_one_cancel_fences_both_units_before_release(authority):
    h, work = authority
    for i in range(2):
        h.stage(i)
        h.arm(i)
    assert h.cancel().epoch == 1
    for i in range(2):
        assert h.release(i).kind is K.REJECTED
        assert not (work / f"u{i}.marker").exists()
        h.stop_retire(i)


def test_committed_release_before_cancel_runs_once_and_other_unit_never_runs(authority):
    h, work = authority
    for i in range(2):
        h.stage(i)
        h.arm(i)
    assert h.release(0).kind is K.RELEASED
    wait_marker(work / "u0.marker")
    h.cancel()
    assert h.release(1).kind is K.REJECTED
    for i in range(2):
        h.stop_retire(i)
    assert (work / "u0.marker").read_bytes() == b"EXEC\n"
    assert not (work / "u1.marker").exists()


def test_duplicate_ticket_cannot_release_twice(authority):
    h, work = authority
    h.stage(0)
    h.arm(0)
    assert h.release(0).kind is K.RELEASED
    wait_marker(work / "u0.marker")
    assert h.release(0).kind is K.REJECTED
    h.stop_retire(0)
    assert (work / "u0.marker").read_bytes() == b"EXEC\n"


def test_selective_generation_advance_keeps_unrelated_original_resource_running(
    authority,
):
    h, work = authority
    for i in range(2):
        h.stage(i)
        h.arm(i)
        assert h.release(i).kind is K.RELEASED
    wait_marker(work / "u0.marker")
    wait_marker(work / "u1.marker")
    old = h.frame(K.QUERY, 0)
    h.stop_retire(0)
    retained = os.dup(h.units[0]["cg"])
    h.fds.append(retained)
    assert h.manager.force_cleanup(h.units[0]["descriptor"]).boundary_released
    info = os.fstat(retained)
    missing = []
    for name in ("cgroup.events", "cgroup.procs", "cgroup.freeze"):
        try:
            control = os.open(
                name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=retained
            )
        except FileNotFoundError as error:
            missing.append(error.errno)
        else:
            os.close(control)
            raise AssertionError("original boundary control still present")
    output = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if output:
        (Path(output) / f"affa-removed-observation-{os.getpid()}.json").write_text(
            json.dumps(
                {
                    "original_identity": [info.st_dev, info.st_ino],
                    "actual_nlink": info.st_nlink,
                    "missing_control_errno": missing,
                    "original_C1_release_observed": True,
                }
            )
        )
    desc = BoundaryDescriptor("run", "u0", 2, "next-0", 0)
    h.manager.create_frozen(desc)
    fd = h.manager._entries[desc.key].fd
    u = h.units[0]
    u.update(
        generation=2,
        operation=b"n" * 16,
        intent=digest(b"new-intent"),
        mirror=digest(b"new-mirror"),
        boundary=digest(b"new-boundary"),
    )
    u.pop("handle")
    u.pop("ticket")
    advanced = h.rpc(h.frame(K.ADVANCE, 0), (fd,))
    assert advanced.kind is K.ADVANCED and advanced.epoch == 1
    u["descriptor"], u["cg"] = desc, fd
    h.stage(0)
    h.arm(0)
    assert h.release(0).kind is K.RELEASED
    wait_marker(work / "u0.marker", 2)
    assert h.rpc(h.frame(K.QUERY, 1)).state & 4
    cached = h.rpc(old)
    assert cached.generation == 1 and cached.state & 256 and not cached.state & 4
    assert h.rpc(h.frame(K.QUERY, 0)).state & 4
    assert h.rpc(replace(old, kind=K.STOP)).state == u["stop_state"]
    assert h.rpc(replace(old, kind=K.RETIRE)).state == u["retire_state"]
    assert h.rpc(h.frame(K.QUERY, 0)).state & 4
    h.cancel()
    for i in range(2):
        h.stop_retire(i)


def test_generation_advance_cannot_change_the_original_action_digest(authority):
    h, work = authority
    h.stage(0)
    h.arm(0)
    assert h.release(0).kind is K.RELEASED
    wait_marker(work / "u0.marker")
    h.stop_retire(0)
    assert h.manager.force_cleanup(h.units[0]["descriptor"]).boundary_released
    desc = BoundaryDescriptor("run", "u0", 2, "next-action-negative", 0)
    h.manager.create_frozen(desc)
    fd = h.manager._entries[desc.key].fd
    frame = AuthorityFrame(
        K.ADVANCE,
        1,
        h.end(),
        h.config.scope,
        1,
        h.epoch,
        2,
        b"n" * 16,
        digest(b"wrong-action"),
        digest(b"new-intent"),
        digest(b"new-mirror"),
        digest(b"new-boundary"),
        ticket=WATCH_PLACEHOLDER,
    )
    assert h.rpc(frame, (fd,)).kind is K.REJECTED
    assert (work / "u0.marker").read_bytes() == b"EXEC\n"


def test_cancelled_stage_creates_no_workload(authority):
    h, work = authority
    h.cancel()
    for index in range(2):
        assert h.rpc(h.frame(K.STAGE, index)).kind is K.REJECTED
        assert h.manager.residual_membership(h.units[index]["descriptor"]) == ()
        assert not (work / f"u{index}.marker").exists()


@pytest.mark.parametrize(
    "mode",
    [
        "wrong-ticket",
        "forged-handle",
        "changed-proof",
        "extra-rights",
        "stale-epoch",
        "short",
        "reserved",
        "unknown-kind",
    ],
)
def test_native_malformed_or_forged_release_never_executes_workload(authority, mode):
    import struct

    h, work = authority
    for index in range(2):
        h.stage(index)
        h.arm(index)
    frame = replace(
        h.frame(K.RELEASE, 0),
        sequence=h.sequence + 1,
        deadline_ns=min(h.end(), h.units[0]["ticket_end"]),
    )
    data = bytearray(frame.encode())
    extra = ()
    if mode == "wrong-ticket":
        data[224] ^= 1
    elif mode == "forged-handle":
        data[256] ^= 1
    elif mode == "changed-proof":
        data[128] ^= 1
    elif mode == "extra-rights":
        extra = [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [h.cwd]))]
    elif mode == "stale-epoch":
        data[64:72] = struct.pack("!Q", h.epoch + 1)
    elif mode == "short":
        data.pop()
    elif mode == "reserved":
        data[-1] = 1
    else:
        data[4:8] = struct.pack("!I", 15)
    h.channel.sendmsg([bytes(data)], extra)
    raw = h.channel.recv(321)
    if raw:
        response = AuthorityFrame.decode(raw)
        assert response.kind is K.REJECTED and response.sequence == h.sequence + 1
        assert response.scope == h.config.scope
        h.sequence += 1
        h.epoch = response.epoch
        h.closed = True
        if mode == "extra-rights":
            import resource

            soft, hard = resource.prlimit(h.process.pid, resource.RLIMIT_NOFILE)
            resource.prlimit(
                h.process.pid, resource.RLIMIT_NOFILE, (min(soft, 128), hard)
            )
            stale = replace(h.frame(K.QUERY, 0), kind=K.STAGE, handle=bytes(32))
            for _ in range(200):
                assert h.rpc(stale, (h.cwd,)).kind is K.REJECTED
        for index in range(2):
            h.stop_retire(index)
    else:
        assert h.process.wait(timeout=3) == 0
    for index in range(2):
        assert not (work / f"u{index}.marker").exists()
        assert h.manager.residual_membership(h.units[index]["descriptor"]) == ()


def test_stopped_authority_cannot_release_an_expired_original_ticket(authority):
    h, work = authority
    h.stage(0)
    h.arm(0)
    pidfd = os.pidfd_open(h.process.pid)
    try:
        signal.pidfd_send_signal(pidfd, signal.SIGSTOP)
        frame = replace(
            h.frame(K.RELEASE, 0),
            sequence=h.sequence + 1,
            deadline_ns=h.units[0]["ticket_end"],
        )
        h.channel.send(frame.encode())
        time.sleep(max(0, (frame.deadline_ns - time.monotonic_ns()) / 1e9) + 0.03)
        signal.pidfd_send_signal(pidfd, signal.SIGCONT)
        assert h.channel.recv(321) == b""
        assert h.process.wait(timeout=3) == 0
    finally:
        try:
            signal.pidfd_send_signal(pidfd, signal.SIGCONT)
        except ProcessLookupError:
            pass
        os.close(pidfd)
    assert not (work / "u0.marker").exists()
    assert h.manager.residual_membership(h.units[0]["descriptor"]) == ()


def test_native_authority_rejects_an_actual_forked_peer(authority):
    h, work = authority
    frame = replace(h.frame(K.STAGE, 0), sequence=h.sequence + 1, deadline_ns=h.end())
    child = os.fork()
    if child == 0:
        try:
            h.channel.send(frame.encode())
        except OSError:
            os._exit(71)
        os._exit(0)
    got, status = os.waitpid(child, 0)
    assert got == child and os.waitstatus_to_exitcode(status) == 0
    assert h.channel.recv(321) == b""
    assert h.process.wait(timeout=3) == 0
    assert not list(work.glob("*.marker"))
    output = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if output:
        (Path(output) / f"affa-foreign-peer-reaped-{os.getpid()}.json").write_text(
            json.dumps(
                {
                    "original_fork_child_reaped": True,
                    "returncode": 0,
                    "source_sha256": digest(Path(__file__).read_bytes()).hex(),
                }
            )
        )


def test_stopped_old_authority_is_actually_revoked_before_original_c1_release(
    authority,
):
    import select

    h, work = authority
    h.stage(0)
    h.arm(0)
    pidfd = os.pidfd_open(h.process.pid)
    try:
        signal.pidfd_send_signal(pidfd, signal.SIGSTOP)
        frame = replace(
            h.frame(K.RELEASE, 0),
            sequence=h.sequence + 1,
            deadline_ns=h.units[0]["ticket_end"],
        )
        h.channel.send(frame.encode())
        h.external_authority_kill = True
        signal.pidfd_send_signal(pidfd, signal.SIGKILL)
        assert h.process.wait(timeout=3) == -signal.SIGKILL
        result = h.manager.force_cleanup(h.units[0]["descriptor"])
        assert result.boundary_released and result.membership_complete
        assert select.select([h.childfds[0]], [], [], 1)[0]
        with pytest.raises(ProcessLookupError):
            signal.pidfd_send_signal(pidfd, signal.SIGCONT)
        assert not (work / "u0.marker").exists()
        output = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
        if output:
            (Path(output) / f"affa-original-revocation-{os.getpid()}.json").write_text(
                json.dumps(
                    {
                        "original_authority_reaped": True,
                        "original_authority_revoked_before_C1_release": True,
                        "C1_boundary_release_observed": True,
                        "original_workload_pidfd_death_observed": True,
                        "native_direct_child_wait_confirmed": False,
                        "ordinary_ownership_recovered": False,
                        "lifecycle_complete": False,
                        "component_only": True,
                        "source_sha256": digest(Path(__file__).read_bytes()).hex(),
                    }
                )
            )
    finally:
        os.close(pidfd)
