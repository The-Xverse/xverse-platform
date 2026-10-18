"""Original native-supervisor helper bootstrap; partial U2/U3/U4, not a run facade.

The external admitted runner supplies the first genuine native Popen/socket and
sealed images. Operation paths create no Popen and accept no caller command.
"""

from dataclasses import dataclass, field
import array
import fcntl
import hashlib
import os
from pathlib import Path
import select
import signal
import socket
import stat
import struct
import subprocess
import threading
import time

from .owner import _Original, _deadline, _hash, _pin, OwnerError
from .child import _PidfdCapability
from .prbc import BoundaryDescriptor, ProcessBoundaryOps
from .supervisor import CancellationLatch
from .time import HostDeadline

SEALS = fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL
WIRE = struct.Struct("!4sIQQ32sQQ32sQQQ")
HEADER = struct.Struct("!4sIQQ32s")
ZERO = bytes(32)
_CREATE = object()


class BootstrapError(OwnerError):
    pass


def _sealed(data, label):
    fd = os.memfd_create(label, os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    try:
        view = memoryview(data)
        while view:
            count = os.write(fd, view)
            if count <= 0:
                raise BootstrapError("ML-BOOT-INPUT-WRITE")
            view = view[count:]
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, SEALS)
        return fd
    except Exception:
        os.close(fd)
        raise


@dataclass(frozen=True)
class HelperImage:
    descriptor: int = field(repr=False)
    digest: str
    argv0: str


def seal_helper_image(path, *, digest, argv0):
    """External admission I/O, outside bounded operation/registration claims."""
    _pin(digest)
    if (
        type(argv0) is not str
        or not Path(argv0).is_absolute()
        or "\0" in argv0
        or len(argv0.encode()) > 4096
    ):
        raise BootstrapError("ML-BOOT-IMAGE-ARGV0")
    source = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        info = os.fstat(source)
        if not stat.S_ISREG(info.st_mode) or not 64 <= info.st_size <= 32 * 1024 * 1024:
            raise BootstrapError("ML-BOOT-IMAGE-LIMIT")
        data = bytearray()
        while len(data) <= info.st_size:
            part = os.read(source, min(16384, info.st_size + 1 - len(data)))
            if not part:
                break
            data.extend(part)
        if (
            len(data) != info.st_size
            or data[:4] != b"\x7fELF"
            or hashlib.sha256(data).digest() != _pin(digest)
        ):
            raise BootstrapError("ML-BOOT-IMAGE-PIN")
        return HelperImage(_sealed(data, "maestro-helper-image"), digest, argv0)
    finally:
        os.close(source)


@dataclass(frozen=True)
class BootstrapAdmission:
    run_id: str
    lifecycle_digest: str
    approval_ref: str
    environment_digest: str
    supervisor_artifact_digest: str
    generation: HostDeadline
    lease: HostDeadline
    images: tuple[HelperImage, HelperImage, HelperImage] = field(repr=False)


@dataclass(frozen=True)
class BootstrapInput:
    admission: BootstrapAdmission
    private_bytes: bytes = field(repr=False)

    @property
    def scope(self):
        return hashlib.sha256(self.private_bytes).digest()


def encode_bootstrap(admission):
    if (
        type(admission) is not BootstrapAdmission
        or type(admission.images) is not tuple
        or len(admission.images) != 3
    ):
        raise BootstrapError("ML-BOOT-ADMISSION")
    for value in (admission.run_id, admission.approval_ref):
        if (
            type(value) is not str
            or not 0 < len(value) <= 128
            or any(ord(c) < 33 or ord(c) > 126 for c in value)
        ):
            raise BootstrapError("ML-BOOT-ADMISSION")
    if type(admission.lifecycle_digest) is not str:
        raise BootstrapError("ML-BOOT-LIFECYCLE-DIGEST")
    _pin("sha256:" + admission.lifecycle_digest)
    _pin(admission.environment_digest)
    _pin(admission.supervisor_artifact_digest)
    if (
        type(admission.generation) is not HostDeadline
        or type(admission.lease) is not HostDeadline
        or admission.generation.session != admission.lease.session
    ):
        raise BootstrapError("ML-BOOT-SESSION")
    admission.generation.__post_init__()
    lease = _deadline(admission.lease, admission.generation.session)
    generation = int(admission.generation.monotonic_seconds * 1e9)
    if (
        not lease <= generation - 2_000_000_000
        or not 2 < admission.generation.monotonic_seconds - time.monotonic() <= 394
    ):
        raise BootstrapError("ML-BOOT-GENERATION")
    context = _hash(
        [
            admission.run_id,
            admission.lifecycle_digest,
            admission.approval_ref,
            admission.environment_digest,
            admission.supervisor_artifact_digest,
        ]
    )
    parts = [HEADER.pack(b"BC10", 1, generation, lease, context)]
    for image in admission.images:
        if (
            type(image) is not HelperImage
            or type(image.descriptor) is not int
            or not 3 <= image.descriptor < 2**31
        ):
            raise BootstrapError("ML-BOOT-IMAGE")
        pin = _pin(image.digest)
        if fcntl.fcntl(image.descriptor, fcntl.F_GET_SEALS) & SEALS != SEALS:
            raise BootstrapError("ML-BOOT-IMAGE-SEALS")
        name = image.argv0.encode()
        if not 0 < len(name) <= 4096 or b"\0" in name or not name.startswith(b"/"):
            raise BootstrapError("ML-BOOT-IMAGE-ARGV0")
        parts.append(
            struct.pack("!I32sI", image.descriptor, pin, len(name)) + name + b"\0"
        )
    private = b"".join(parts)
    if len(private) > 65536:
        raise BootstrapError("ML-BOOT-INPUT-LIMIT")
    return BootstrapInput(admission, private)


def sealed_bootstrap_fd(config):
    if (
        type(config) is not BootstrapInput
        or encode_bootstrap(config.admission) != config
    ):
        raise BootstrapError("ML-BOOT-CONFIG")
    return _sealed(config.private_bytes, "maestro-private-bootstrap")


@dataclass(frozen=True)
class BootstrapPacket:
    kind: int
    sequence: int
    deadline: int
    scope: bytes
    slot: int = 0
    pid: int = 0
    token: bytes = field(default=ZERO, repr=False)
    state: int = 0
    reason: int = 0

    def __post_init__(self):
        if any(
            type(v) is not int or not 0 <= v < 2**64
            for v in (
                self.kind,
                self.sequence,
                self.deadline,
                self.slot,
                self.pid,
                self.state,
                self.reason,
            )
        ):
            raise BootstrapError("ML-BOOT-WIRE-INTEGER")
        if (
            self.kind not in (1, 2, 3, 16, 17, 18, 19)
            or not self.deadline
            or self.reason
            or self.slot > 64
        ):
            raise BootstrapError("ML-BOOT-WIRE-HEADER")
        if any(type(v) is not bytes or len(v) != 32 for v in (self.scope, self.token)):
            raise BootstrapError("ML-BOOT-WIRE-DIGEST")
        if (self.pid == 0) != (self.token == ZERO) or self.pid == 1:
            raise BootstrapError("ML-BOOT-WIRE-CHILD")
        if self.kind in (1, 2, 17, 18) and not self.slot:
            raise BootstrapError("ML-BOOT-WIRE-SLOT")
        if self.kind in (2, 17, 18) and not self.pid:
            raise BootstrapError("ML-BOOT-WIRE-CHILD")
        if self.kind in (3, 16, 19) and (self.slot or self.pid):
            raise BootstrapError("ML-BOOT-WIRE-GLOBAL")
        if self.kind in (1, 2, 3, 17, 18, 19) and not self.sequence:
            raise BootstrapError("ML-BOOT-WIRE-SEQUENCE")
        if (
            self.kind == 1
            and (self.pid or self.state not in (1, 2, 3))
            or self.kind == 2
            and self.state
            or self.kind == 17
            and self.state
            or self.kind == 18
            and self.state != 1
            or self.kind == 16
            and self.sequence
        ):
            raise BootstrapError("ML-BOOT-WIRE-STATE")

    def encode(self):
        self.__post_init__()
        return WIRE.pack(
            b"BS10",
            self.kind,
            self.sequence,
            self.deadline,
            self.scope,
            self.slot,
            self.pid,
            self.token,
            self.state,
            self.reason,
            0,
        )

    @classmethod
    def decode(cls, data):
        if type(data) is not bytes or len(data) != 128:
            raise BootstrapError("ML-BOOT-WIRE-SIZE")
        magic, kind, seq, until, scope, slot, pid, token, state, reason, reserved = (
            WIRE.unpack(data)
        )
        if magic != b"BS10" or reserved:
            raise BootstrapError("ML-BOOT-WIRE-MAGIC")
        return cls(kind, seq, until, scope, slot, pid, token, state, reason)


class BootstrapChild(_Original):
    """Original native-issued direct child; only the issuing registry constructs it."""

    def __init__(self, key, root, packet, fd, *, cleanup_only=False):
        if key is not _CREATE:
            raise BootstrapError("ML-BOOT-CHILD-ISSUER")
        self._retain()
        self._root, self._slot, self._fd = root, packet.slot, fd
        self._pid_pin, self._token = packet.pid, packet.token
        self._cleanup_only, self._active = cleanup_only, False
        self._pins = (root, packet.slot, fd, packet.pid, packet.token)
        self._wait_lock = threading.Lock()
        self._result = None
        self._returncode = None
        self._capability = _PidfdCapability(fd)
        self._capability_pin = self._capability
        # This verifies actual original-parent wait ownership without consuming it.
        try:
            os.waitid(
                os.P_PIDFD,
                self._capability.fileno(),
                os.WEXITED | os.WNOHANG | os.WNOWAIT,
            )
        except Exception:
            self._capability.close()
            raise

    @staticmethod
    def _fd_identity(fd):
        info = os.fstat(fd)
        return info.st_dev, info.st_ino

    @property
    def pid(self):
        return self._pid_pin

    @property
    def returncode(self):
        return self._returncode

    @returncode.setter
    def returncode(self, value):
        self._holder()
        if self._result is None or value != self._returncode:
            raise BootstrapError("ML-BOOT-UNOBSERVED-WAIT")

    def _holder(self):
        super()._holder()
        root, slot, fd, pid, token = self._pins
        root._holder()
        if (
            (self._root, self._slot, self._fd, self._pid_pin, self._token) != self._pins
            or root._children.get(slot) is not self
            or self._capability is not self._capability_pin
        ):
            raise BootstrapError("ML-BOOT-CHILD-REPLACED")
        self._capability.check(fd)

    def _ordinary(self):
        self._holder()
        self._root._live()
        if self._cleanup_only or not self._active:
            raise BootstrapError("ML-BOOT-CHILD-NOT-ACTIVE")

    def _wait(self, fd, *, consume=False):
        self._holder()
        try:
            self._capability.check(fd)
        except (ValueError, OSError) as error:
            raise OSError("ML-BOOT-WAIT-FD-UNRESOLVED") from error
        if not self._wait_lock.acquire(False):
            raise BootstrapError("ML-BOOT-WAIT-CONFLICT")
        try:
            if self._result is not None:
                return self._result
            result = os.waitid(
                os.P_PIDFD,
                self._capability.fileno(),
                os.WEXITED | os.WNOHANG | (0 if consume else os.WNOWAIT),
            )
            if result is not None and consume:
                self._result = result
                self._returncode = (
                    result.si_status
                    if result.si_code == os.CLD_EXITED
                    else -result.si_status
                )
            return result
        finally:
            self._wait_lock.release()


@dataclass(frozen=True)
class BootstrapDrain:
    supervisor_reaped: bool
    registered_children_reaped: bool
    unacknowledged_births: int
    supervisor_returncode: int | None
    final_workload_freeze_acknowledged: bool
    diagnostic: str | None
    cleanup_complete: bool = field(default=False, init=False)
    ready_for_execution: bool = field(default=False, init=False)


class BootstrapSession(_Original):
    def __init__(self, process, channel, config, boundaries, latch, *, deadline):
        if (
            type(process) is not subprocess.Popen
            or type(channel) is not socket.socket
            or type(config) is not BootstrapInput
            or type(boundaries) is not ProcessBoundaryOps
            or type(latch) is not CancellationLatch
        ):
            raise BootstrapError("ML-BOOT-INPUT")
        if (
            channel.family != socket.AF_UNIX
            or channel.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE)
            != socket.SOCK_SEQPACKET
            or not channel.getsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED)
        ):
            raise BootstrapError("ML-BOOT-SOCKET")
        if encode_bootstrap(config.admission) != config:
            raise BootstrapError("ML-BOOT-CONFIG")
        admission = boundaries._admission
        if (
            boundaries._latch is not latch
            or admission.run_id != config.admission.run_id
            or admission.bootstrap_approval_ref != config.admission.approval_ref
            or admission.teardown_deadline != config.admission.generation
        ):
            raise BootstrapError("ML-BOOT-ORIGINAL-C1")
        self._retain()
        self.process, self.channel, self.config, self.boundaries, self.latch = (
            process,
            channel,
            config,
            boundaries,
            latch,
        )
        self._pins = (process, channel, config, boundaries, latch)
        self.session = config.admission.generation.session
        self._generation = int(config.admission.generation.monotonic_seconds * 1e9)
        self._lease = int(config.admission.lease.monotonic_seconds * 1e9)
        self._pid_pin = process.pid
        self._socket_identity = BootstrapChild._fd_identity(channel.fileno())
        self._pidfd = os.pidfd_open(process.pid, 0)
        self._sequence, self._slot = 0, 0
        self._children, self._pending, self._birth_deadlines = {}, {}, {}
        self._registries = (self._children, self._pending, self._birth_deadlines)
        self._lock = threading.Lock()
        self._closed, self._drained, self._drain_end = False, None, None
        self._root_result = None
        self._pidfd_capability = None
        channel.setblocking(False)
        try:
            self._pidfd_capability = _PidfdCapability(self._pidfd)
            self._pidfd_capability_pin = self._pidfd_capability
            self._live()
            packet, fds = self._receive(self._until(deadline))
            if fds or packet != BootstrapPacket(
                16, 0, self._lease, config.scope, state=self._lease
            ):
                for fd in fds:
                    os.close(fd)
                raise BootstrapError("ML-BOOT-READY")
        except Exception:
            self.cancel("bootstrap-registration-failed")
            if self._pidfd_capability is not None:
                self._pidfd_capability.close()
            os.close(self._pidfd)
            self._pidfd = -1
            raise

    def _holder(self):
        super()._holder()
        if (
            any(
                a is not b
                for a, b in zip(
                    (
                        self.process,
                        self.channel,
                        self.config,
                        self.boundaries,
                        self.latch,
                    ),
                    self._pins,
                )
            )
            or self.session != self._pins[2].admission.generation.session
            or self.process.pid != self._pid_pin
            or BootstrapChild._fd_identity(self.channel.fileno())
            != self._socket_identity
        ):
            raise BootstrapError("ML-BOOT-REPLACED")
        if any(
            a is not b
            for a, b in zip(
                (self._children, self._pending, self._birth_deadlines), self._registries
            )
        ):
            raise BootstrapError("ML-BOOT-REGISTRY-REPLACED")
        if self._pidfd_capability is not self._pidfd_capability_pin:
            raise BootstrapError("ML-BOOT-PIDFD-REPLACED")
        self._pidfd_capability.check(self._pidfd)
        self.boundaries._holder()
        self.latch._check()

    def _live(self):
        self._holder()
        if (
            self._closed
            or self.latch.cancelled
            or time.monotonic_ns() >= self._lease
            or select.select([self._pidfd_capability.fileno()], [], [], 0)[0]
            or os.waitid(
                os.P_PIDFD,
                self._pidfd_capability.fileno(),
                os.WEXITED | os.WNOHANG | os.WNOWAIT,
            )
            is not None
        ):
            raise BootstrapError("ML-BOOT-CLOSED")

    def _until(self, deadline):
        until = _deadline(deadline, self.session)
        if until > self._lease or until > self._generation - 2_000_000_000:
            raise BootstrapError("ML-BOOT-DEADLINE")
        return until

    def _receive(self, until, *, cleanup=False):
        while True:
            self._holder() if cleanup else self._live()
            remaining = (until - time.monotonic_ns()) / 1e9
            if remaining <= 0:
                raise BootstrapError("ML-BOOT-TIMEOUT")
            if not select.select([self.channel], [], [], min(remaining, 0.01))[0]:
                continue
            try:
                data, anc, flags, _ = self.channel.recvmsg(
                    129,
                    socket.CMSG_SPACE(12) + socket.CMSG_SPACE(32),
                    socket.MSG_CMSG_CLOEXEC,
                )
            except BlockingIOError:
                continue
            received, credentials = [], []
            valid = not flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC)
            for level, kind, payload in anc:
                if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                    values = array.array("i")
                    values.frombytes(
                        payload[: len(payload) - len(payload) % values.itemsize]
                    )
                    received.extend(values)
                elif (
                    level == socket.SOL_SOCKET
                    and kind == socket.SCM_CREDENTIALS
                    and len(payload) == 12
                ):
                    credentials.append(struct.unpack("3i", payload))
                else:
                    valid = False
            try:
                if (
                    not valid
                    or credentials != [(self._pid_pin, os.getuid(), os.getgid())]
                    or not data
                ):
                    raise BootstrapError("ML-BOOT-SENDER")
                packet = BootstrapPacket.decode(data)
                if packet.scope != self.config.scope:
                    raise BootstrapError("ML-BOOT-SCOPE")
                result = received[:]
                received.clear()
                return packet, result
            finally:
                for fd in received:
                    os.close(fd)

    def _rpc(self, kind, deadline, *, slot=0, child=None, state=0, fds=()):
        self._live()
        until = self._until(deadline)
        packet = BootstrapPacket(
            kind,
            self._sequence + 1,
            until,
            self.config.scope,
            slot,
            child.pid if child else 0,
            child._token if child else ZERO,
            state,
        )
        if kind == 1:
            self._pending[slot] = packet
        anc = (
            [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", fds))]
            if fds
            else []
        )
        try:
            if self.channel.sendmsg([packet.encode()], anc) != 128:
                raise BootstrapError("ML-BOOT-SEND")
            self._sequence = packet.sequence
            reply, received = self._receive(until)
            expected = {1: 17, 2: 18, 3: 19}[kind]
            if (reply.kind, reply.sequence, reply.deadline, reply.slot) != (
                expected,
                packet.sequence,
                until,
                slot,
            ) or len(received) != (1 if kind == 1 else 0):
                for fd in received:
                    os.close(fd)
                raise BootstrapError("ML-BOOT-ACK")
            if time.monotonic_ns() >= until:
                if kind == 1:
                    try:
                        late = BootstrapChild(
                            _CREATE, self, reply, received[0], cleanup_only=True
                        )
                        self._children[slot] = late
                        self._pending.pop(slot)
                        received.clear()
                    finally:
                        for fd in received:
                            os.close(fd)
                raise BootstrapError("ML-BOOT-LATE-ACK")
            if child and (reply.pid, reply.token) != (child.pid, child._token):
                raise BootstrapError("ML-BOOT-HANDLE")
            return reply, received
        except Exception:
            self.cancel("bootstrap-uncertain")
            raise

    def birth(self, role, helper, unit, peer, input_fd, deadline):
        """Trusted role adapters supply original registered boundaries/private FDs."""
        if not self._lock.acquire(False):
            raise BootstrapError("ML-BOOT-CONFLICT")
        try:
            self._live()
            if (
                type(role) is not int
                or role not in (1, 2, 3)
                or type(helper) is not BoundaryDescriptor
                or type(unit) is not BoundaryDescriptor
                or type(peer) is not socket.socket
            ):
                raise BootstrapError("ML-BOOT-BIRTH-INPUT")
            for descriptor in (helper, unit):
                self.boundaries._authority(self.boundaries._entry(descriptor))
            helper_fd = self.boundaries._entry(helper).fd
            unit_fd = self.boundaries._entry(unit).fd
            if (
                helper == unit
                and role != 3
                or helper != unit
                and role == 3
                or self._slot >= 64
            ):
                raise BootstrapError("ML-BOOT-BIRTH-SCOPE")
            self._slot += 1
            self._birth_deadlines[self._slot] = self._until(deadline)
            reply, fds = self._rpc(
                1,
                deadline,
                slot=self._slot,
                state=role,
                fds=(helper_fd, unit_fd, peer.fileno(), input_fd),
            )
            try:
                child = BootstrapChild(_CREATE, self, reply, fds[0])
                self._children[child._slot] = child
                self._pending.pop(child._slot)
                return child
            except Exception:
                os.close(fds[0])
                self.cancel("bootstrap-birth-invalid")
                raise
        finally:
            self._lock.release()

    def activate(self, child, deadline):
        if not self._lock.acquire(False):
            raise BootstrapError("ML-BOOT-CONFLICT")
        try:
            if type(child) is not BootstrapChild or child._root is not self:
                raise BootstrapError("ML-BOOT-HANDLE")
            child._holder()
            if (
                child._active
                or child._cleanup_only
                or self._until(deadline) > self._birth_deadlines[child._slot]
            ):
                raise BootstrapError("ML-BOOT-ACTIVATION")
            self._rpc(2, deadline, slot=child._slot, child=child)
            child._active = True
        finally:
            self._lock.release()

    def renew(self, lease, deadline):
        if not self._lock.acquire(False):
            raise BootstrapError("ML-BOOT-CONFLICT")
        try:
            next_lease = _deadline(lease, self.session)
            if (
                next_lease < self._lease
                or next_lease > self._generation - 2_000_000_000
            ):
                raise BootstrapError("ML-BOOT-LEASE")
            reply, _ = self._rpc(3, deadline, state=next_lease)
            if reply.state != next_lease:
                self.cancel("bootstrap-lease-mismatch")
                raise BootstrapError("ML-BOOT-LEASE-ACK")
            self._lease = next_lease
        finally:
            self._lock.release()

    def cancel(self, reason="bootstrap-cancel"):
        super()._holder()
        self._closed = True
        self._pins[4].cancel(reason)
        try:
            self._pins[1].shutdown(socket.SHUT_WR)
        except OSError:
            pass

    def _recover_late(self, until):
        while self._pending and select.select([self.channel], [], [], 0)[0]:
            try:
                packet, fds = self._receive(until, cleanup=True)
            except (ValueError, OSError):
                break
            pending = self._pending.get(packet.slot)
            try:
                if (
                    pending is None
                    or (packet.kind, packet.sequence, packet.deadline)
                    != (17, pending.sequence, pending.deadline)
                    or len(fds) != 1
                ):
                    continue
                child = BootstrapChild(_CREATE, self, packet, fds[0], cleanup_only=True)
                self._children[child._slot] = child
                self._pending.pop(child._slot)
                fds.clear()
            finally:
                for fd in fds:
                    os.close(fd)

    def drain(self, deadline):
        self._holder()
        if not self._closed:
            raise BootstrapError("ML-BOOT-STILL-OPEN")
        until = _deadline(deadline, self.session)
        if until - time.monotonic_ns() > 2_000_000_000 or until > self._generation:
            raise BootstrapError("ML-BOOT-DRAIN-LIMIT")
        self._drain_end = min(self._drain_end or until, until)
        kill_at = time.monotonic_ns() + 500_000_000
        while True:
            self._recover_late(self._drain_end)
            complete = True
            for child in tuple(self._children.values()):
                try:
                    child._holder()
                except (ValueError, OSError):
                    complete = False
                    continue
                try:
                    signal.pidfd_send_signal(child._capability.fileno(), signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    if child._wait(child._capability.fileno(), consume=True) is None:
                        complete = False
                except OSError:
                    complete = False
            if self._root_result is None:
                try:
                    self._root_result = os.waitid(
                        os.P_PIDFD,
                        self._pidfd_capability.fileno(),
                        os.WEXITED | os.WNOHANG,
                    )
                    if self._root_result:
                        result = self._root_result
                        self.process.returncode = (
                            result.si_status
                            if result.si_code == os.CLD_EXITED
                            else -result.si_status
                        )
                except OSError:
                    complete = False
            if self._root_result and complete or time.monotonic_ns() >= self._drain_end:
                self._drained = BootstrapDrain(
                    bool(self._root_result),
                    complete,
                    len(self._pending),
                    self.process.returncode,
                    bool(self._root_result) and self.process.returncode == 0,
                    (
                        None
                        if self.process.returncode == 0
                        else "ML-BOOT-SUPERVISOR-UNRESOLVED"
                    )
                    if self._root_result and complete and not self._pending
                    else "ML-BOOT-DRAIN-UNRESOLVED",
                )
                return self._drained
            if time.monotonic_ns() >= kill_at and self._root_result is None:
                try:
                    signal.pidfd_send_signal(
                        self._pidfd_capability.fileno(), signal.SIGKILL
                    )
                except ProcessLookupError:
                    pass
            select.select(
                [self._pidfd_capability.fileno()],
                [],
                [],
                min(0.01, max(0, (self._drain_end - time.monotonic_ns()) / 1e9)),
            )

    def dispose(self):
        self._holder()
        if (
            not self._drained
            or not self._drained.supervisor_reaped
            or not self._drained.registered_children_reaped
            or self._pending
        ):
            raise BootstrapError("ML-BOOT-RETAINED")
        for child in self._children.values():
            child._holder()
            child._capability.close()
            os.close(child._fd)
        self._pidfd_capability.close()
        os.close(self._pidfd)
        self.channel.close()

    def _context(self, lifecycle_digest):
        self._live()
        if lifecycle_digest != self.config.admission.lifecycle_digest:
            raise BootstrapError("ML-BOOT-LIFECYCLE")

    def _spawn_role(self, role, helper, unit, private_fd, deadline):
        parent, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        try:
            child = self.birth(role, helper, unit, peer, private_fd, deadline)
            self.activate(child, deadline)
            return child, parent
        except Exception:
            parent.close()
            self.cancel("bootstrap-helper-failed")
            raise
        finally:
            peer.close()
            os.close(private_fd)

    def persistence(self, config, helper, deadline):
        from .persistence import PersistenceClient, PersistenceInput, sealed_input_fd

        if (
            type(config) is not PersistenceInput
            or config.run_id != self.config.admission.run_id
        ):
            raise BootstrapError("ML-BOOT-PERSISTENCE")
        self._context(config.prepared.lifecycle_digest)
        child, channel = self._spawn_role(
            3, helper, helper, sealed_input_fd(config), deadline
        )
        try:
            return PersistenceClient(
                child, channel, config, self.latch, deadline=deadline
            )
        except Exception:
            self.cancel("bootstrap-client-failed")
            raise

    def catalog(self, owner, recipe, helper, deadline):
        from .launcher import CatalogLauncher, LaunchRecipe, sealed_recipe_fd
        from .owner import ReleaseOwner

        if (
            type(owner) is not ReleaseOwner
            or type(recipe) is not LaunchRecipe
            or owner.supervisor.boundaries is not self.boundaries
        ):
            raise BootstrapError("ML-BOOT-CATALOG")
        self._context(owner._prepared.lifecycle_digest)
        pin = self.config.admission.images[0].digest
        if owner._unit(recipe.unit_id).provider.artifact_digest != pin:
            raise BootstrapError("ML-BOOT-CATALOG-PIN")
        child, channel = self._spawn_role(
            1, helper, recipe.descriptor, sealed_recipe_fd(recipe), deadline
        )
        try:
            return CatalogLauncher(
                child,
                channel,
                owner,
                recipe,
                helper_artifact_digest=pin,
                deadline=deadline,
            )
        except Exception:
            self.cancel("bootstrap-client-failed")
            raise

    def gate(
        self,
        owner,
        unit,
        helper,
        deadline,
        *,
        lease_ns,
        heartbeat_ns=500_000_000,
        epoch=0,
    ):
        from .owner import ReleaseOwner, GateConnection

        if (
            type(owner) is not ReleaseOwner
            or owner.supervisor.boundaries is not self.boundaries
        ):
            raise BootstrapError("ML-BOOT-GATE")
        self._context(owner._prepared.lifecycle_digest)
        if (
            any(
                type(v) is not int or not 0 <= v < 2**64
                for v in (lease_ns, heartbeat_ns, epoch)
            )
            or not time.monotonic_ns() < lease_ns <= self._lease
            or not 0 < heartbeat_ns <= 5_000_000_000
        ):
            raise BootstrapError("ML-BOOT-GATE-LEASE")
        pin = self.config.admission.images[1].digest
        scope = owner.scope(unit.unit_id, unit, pin)
        private = _sealed(
            struct.pack(
                "!QQQQ32s", self._generation, lease_ns, heartbeat_ns, epoch, scope
            ),
            "maestro-private-gate",
        )
        child, channel = self._spawn_role(2, helper, unit, private, deadline)
        try:
            return GateConnection(
                child,
                channel,
                scope=scope,
                epoch=epoch,
                lease_ns=lease_ns,
                artifact_digest=pin,
                latch=self.latch,
                deadline=deadline,
                boundaries=self.boundaries,
                descriptor=unit,
            )
        except Exception:
            self.cancel("bootstrap-client-failed")
            raise
