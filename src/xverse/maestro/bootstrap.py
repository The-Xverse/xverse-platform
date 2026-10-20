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
    authority_image: HelperImage | None = field(default=None, repr=False)
    boundary_parent: int | None = field(default=None, repr=False)


@dataclass(frozen=True)
class BootstrapInput:
    admission: BootstrapAdmission
    private_bytes: bytes = field(repr=False)

    @property
    def scope(self):
        return hashlib.sha256(self.private_bytes).digest()

    @property
    def version(self):
        return 2 if self.admission.authority_image is not None else 1


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
    successor = admission.authority_image is not None
    if successor:
        if type(admission.boundary_parent) is not int or admission.boundary_parent < 3:
            raise BootstrapError("ML-BOOT-PARENT")
        info = os.fstat(admission.boundary_parent)
        if not stat.S_ISDIR(info.st_mode):
            raise BootstrapError("ML-BOOT-PARENT")
        parent = struct.pack(
            "!QQQ", admission.boundary_parent, info.st_dev, info.st_ino
        )
    elif admission.boundary_parent is not None:
        raise BootstrapError("ML-BOOT-PARENT")
    parts = [
        HEADER.pack(
            b"BC17" if successor else b"BC10",
            2 if successor else 1,
            generation,
            lease,
            context,
        )
    ]
    if successor:
        parts.append(parent)
    images = admission.images + ((admission.authority_image,) if successor else ())
    for image in images:
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
    version: int = 1

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
        watch = self.kind in (4, 20) and self.version == 2
        if (
            type(self.version) is not int
            or self.version not in (1, 2)
            or self.kind
            not in (
                (1, 2, 3, 4, 5, 6, 16, 17, 18, 19, 20, 21, 22)
                if self.version == 2
                else (1, 2, 3, 16, 17, 18, 19)
            )
            or not self.deadline
            or self.reason
            or self.slot > (128 if watch else 64)
        ):
            raise BootstrapError("ML-BOOT-WIRE-HEADER")
        if any(type(v) is not bytes or len(v) != 32 for v in (self.scope, self.token)):
            raise BootstrapError("ML-BOOT-WIRE-DIGEST")
        # F-02 (finding 403): a v2 WATCH reply (kind 20) carries the supervisor's watch token with pid 0.
        if ((self.pid == 0) != (self.token == ZERO) and not (watch and self.kind == 20)) or self.pid == 1:
            raise BootstrapError("ML-BOOT-WIRE-CHILD")
        if watch and (
            not self.slot
            or self.pid
            or (self.token == ZERO) != (self.kind == 4)
            or self.state
            or not self.sequence
        ):
            raise BootstrapError("ML-BOOT-WIRE-WATCH")
        if self.kind in (1, 2, 17, 18) and not self.slot:
            raise BootstrapError("ML-BOOT-WIRE-SLOT")
        if self.kind in (2, 17, 18) and not self.pid:
            raise BootstrapError("ML-BOOT-WIRE-CHILD")
        if self.kind in (3, 5, 6, 16, 19, 21, 22) and (self.slot or self.pid):
            raise BootstrapError("ML-BOOT-WIRE-GLOBAL")
        if self.kind in (1, 2, 3, 5, 6, 17, 18, 19, 21, 22) and not self.sequence:
            raise BootstrapError("ML-BOOT-WIRE-SEQUENCE")
        if (
            self.kind == 1
            and (
                self.pid
                or self.state not in ((1, 2, 3, 4, 5) if self.version == 2 else (1, 2, 3))
            )
            or self.kind in (2, 5)
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
            b"BS17" if self.version == 2 else b"BS10",
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
    def decode(cls, data, *, version=1):
        if type(data) is not bytes or len(data) != 128:
            raise BootstrapError("ML-BOOT-WIRE-SIZE")
        magic, kind, seq, until, scope, slot, pid, token, state, reason, reserved = (
            WIRE.unpack(data)
        )
        if (
            type(version) is not int
            or version not in (1, 2)
            or magic != (b"BS17" if version == 2 else b"BS10")
            or reserved
        ):
            raise BootstrapError("ML-BOOT-WIRE-MAGIC")
        return cls(kind, seq, until, scope, slot, pid, token, state, reason, version)


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
            or config.version == 2
            and config.admission.boundary_parent != boundaries._root_fd
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
        self._issued, self._clients = {}, {}
        self._issued_log, self._client_log = (), ()
        self._authority_input = None
        self._watches, self._watch_log = {}, ()
        self._watch_registry = self._watches
        self._watch_tokens, self._watch_token_log = {}, ()
        self._watch_token_registry = self._watch_tokens
        self._registries = (
            self._children,
            self._pending,
            self._birth_deadlines,
            self._issued,
            self._clients,
        )
        self._lock = threading.Lock()
        self._closed, self._drained, self._drain_end = False, None, None
        self._root_result = None
        self._terminal = self._terminal_attempted = False
        self._start_window=self._start_window_pin=None
        self._pidfd_capability = None
        channel.setblocking(False)
        try:
            self._pidfd_capability = _PidfdCapability(self._pidfd)
            self._pidfd_capability_pin = self._pidfd_capability
            self._live()
            packet, fds = self._receive(self._until(deadline))
            if fds or packet != BootstrapPacket(
                16,
                0,
                self._lease,
                config.scope,
                state=self._lease,
                version=config.version,
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
                (
                    self._children,
                    self._pending,
                    self._birth_deadlines,
                    self._issued,
                    self._clients,
                ),
                self._registries,
            )
        ):
            raise BootstrapError("ML-BOOT-REGISTRY-REPLACED")
        if self._pidfd_capability is not self._pidfd_capability_pin:
            raise BootstrapError("ML-BOOT-PIDFD-REPLACED")
        self._pidfd_capability.check(self._pidfd)
        self.boundaries._holder()
        self.latch._check()
        if (
            tuple(sorted(self._issued.items())) != self._issued_log
            or tuple(sorted(self._clients.items())) != self._client_log
            or self._watches is not self._watch_registry
            or tuple(self._watches.items()) != self._watch_log
            or self._watch_tokens is not self._watch_token_registry
            or tuple(self._watch_tokens.items()) != self._watch_token_log
        ):
            raise BootstrapError("ML-BOOT-INVENTORY-REPLACED")

    def _live(self, *, terminal=False):
        self._holder()
        if (
            self._closed
            or terminal != self._terminal
            or self.latch.cancelled and not terminal
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

    def _receive(self, until, *, cleanup=False, terminal=False):
        while True:
            self._holder() if cleanup else self._live(terminal=terminal)
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
                packet = BootstrapPacket.decode(data, version=self.config.version)
                if packet.scope != self.config.scope:
                    raise BootstrapError("ML-BOOT-SCOPE")
                result = received[:]
                received.clear()
                return packet, result
            finally:
                for fd in received:
                    os.close(fd)

    def _rpc(self, kind, deadline, *, slot=0, child=None, state=0, fds=(), terminal=False):
        if terminal and (self.config.version != 2 or kind not in (5, 6)
                         or slot or child is not None or fds):
            raise BootstrapError("ML-BOOT-TERMINAL-OPERATION")
        # Entry5 is allowed only after the original latch closes; reply receipt
        # still checks original liveness/lease. Ordinary RPCs remain prohibited.
        if terminal and kind == 5:
            self._holder()
            if not self.latch.cancelled or self._terminal or self._closed:
                raise BootstrapError("ML-BOOT-TERMINAL-STATE")
        else:
            self._live(terminal=terminal)
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
            version=self.config.version,
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
            if not terminal:
                reply, received = self._receive(until)  # Retain default observation hook.
            elif kind == 5:
                reply, received = self._receive(until, cleanup=True)
            else:
                reply, received = self._receive(until, terminal=True)
            expected = {1: 17, 2: 18, 3: 19, 4: 20, 5: 21, 6: 22}[kind]
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

    def bind_start_authorization(self,window):
        from .runtime_service import _StartWindow
        self._holder()
        if self._start_window is not self._start_window_pin:
            raise BootstrapError('ML-BOOT-AUTHORIZATION-REPLACED')
        if type(window) is not _StartWindow or window.bootstrap is not self.config:
            raise BootstrapError('ML-BOOT-AUTHORIZATION')
        window._holder()
        if self._start_window is not None and self._start_window is not window:
            raise BootstrapError('ML-BOOT-AUTHORIZATION-REPEAT')
        self._start_window=self._start_window_pin=window

    def check_start_authorization(self):
        self._holder()
        if self._start_window is not self._start_window_pin:
            raise BootstrapError('ML-BOOT-AUTHORIZATION-REPLACED')
        if self._start_window is not None:self._start_window.check()

    def birth(self, role, helper, unit, peer, input_fd, deadline):
        """Trusted role adapters supply original registered boundaries/private FDs."""
        if not self._lock.acquire(False):
            raise BootstrapError("ML-BOOT-CONFLICT")
        try:
            self._live()
            self.check_start_authorization()
            if (
                type(role) is not int
                or role not in ((3, 4, 5) if self.config.version == 2 else (1, 2, 3))
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
                and role not in (3, 4, 5)
                or helper != unit
                and role in (3, 4, 5)
                or self._slot >= 64
                or role == 4
                and (not self._watches or any(v[0] == 4 for v in self._issued.values()))
            ):
                raise BootstrapError("ML-BOOT-BIRTH-SCOPE")
            self.check_start_authorization()
            self._slot += 1
            self._birth_deadlines[self._slot] = self._until(deadline)
            self._issued[self._slot] = (role, helper, unit)
            self._issued_log = tuple(sorted(self._issued.items()))
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

    def watch(self, descriptor, deadline):
        """Retain an exact original C1 leaf in the independent native watchdog."""
        if not self._lock.acquire(False):
            raise BootstrapError("ML-BOOT-CONFLICT")
        try:
            self._live()
            if self.config.version != 2 or type(descriptor) is not BoundaryDescriptor:
                raise BootstrapError("ML-BOOT-WATCH-INPUT")
            entry = self.boundaries._entry(descriptor)
            self.boundaries._authority(entry)
            self.boundaries._verify(entry)
            identity = BootstrapChild._fd_identity(entry.fd)
            if identity in self._watches or len(self._watches) >= 128:
                raise BootstrapError("ML-BOOT-WATCH-SCOPE")
            slot = len(self._watches) + 1
            reply, _ = self._rpc(4, deadline, slot=slot, fds=(entry.fd,))
            if reply.pid or reply.token == ZERO or reply.state:
                self.cancel("bootstrap-watch-uncertain")
                raise BootstrapError("ML-BOOT-WATCH-ACK")
            self._watches[identity] = descriptor
            self._watch_log = tuple(self._watches.items())
            self._watch_tokens[identity] = reply.token  # F-02: echoed on ADVANCE, verified natively
            self._watch_token_log = tuple(self._watch_tokens.items())
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

    def _service_terminal(self, deadline, *, authority):
        """Irreversible original BS17 cleanup service; no ordinary authority renewal."""
        from .affa_client import AuthorityConnection
        from .affa_protocol import AuthorityKind
        self._holder()
        if (self.config.version != 2 or not self.latch.cancelled
            or type(authority) is not AuthorityConnection):
            raise BootstrapError("ML-BOOT-TERMINAL-STATE")
        authority._holder()
        child = authority.child
        if (child._root is not self or self._clients.get(child._slot) is not authority
            or not (any(r.kind is AuthorityKind.CANCELLED for r in authority._epoch_history)
                    or child._result is not None and select.select(
                        [child._capability.fileno()], [], [], 0)[0])):
            raise BootstrapError("ML-BOOT-TERMINAL-FENCE")
        until = self._until(deadline)
        if not self._lock.acquire(False):
            raise BootstrapError("ML-BOOT-CONFLICT")
        try:
            if not self._terminal:
                if self._terminal_attempted:
                    raise BootstrapError("ML-BOOT-TERMINAL-UNCERTAIN")
                self._terminal_attempted = True
                reply, _ = self._rpc(5, deadline, terminal=True)
                if reply.state != self._lease:
                    self.cancel("terminal-fence-ack-mismatch")
                    raise BootstrapError("ML-BOOT-TERMINAL-ACK")
                self._terminal = True
            self._live(terminal=True)
            # Each renewal is short; fixed generation and caller ends never move.
            target = min(time.monotonic_ns() + 4_900_000_000,
                         self._generation - 2_000_000_000)
            if target > self._lease:
                reply, _ = self._rpc(6, deadline, state=target, terminal=True)
                if reply.state != target:
                    self.cancel("terminal-lease-ack-mismatch")
                    raise BootstrapError("ML-BOOT-LEASE-ACK")
                self._lease = target
            if time.monotonic_ns() >= until:
                self.cancel("terminal-service-late")
                raise BootstrapError("ML-BOOT-LATE-ACK")
            return self._lease
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

    @property
    def authority_scope(self):
        self._holder()
        return _hash(
            ["AF17", self.config.scope.hex(), self.boundaries._admission.affa_session]
        )

    @property
    def authority_supervisor(self):
        self._holder()
        return _hash(
            [
                self.config.scope.hex(),
                self.boundaries._admission.supervisor_session,
                self.session,
            ]
        )

    def authority(self, config, helper, deadline):
        """Original private transport only; actual M3/Argus broker still required."""
        from .affa_protocol import AuthorityConfig
        from .affa_client import AuthorityConnection

        self._live()
        if (
            self.config.version != 2
            or type(config) is not AuthorityConfig
            or self._authority_input is not None
            or config.generation_ns != self._generation
            or config.lease_ns > self._lease
            or config.epoch != self.boundaries.release_epoch
            or config.scope != self.authority_scope
            or config.supervisor_session != self.authority_supervisor
        ):
            raise BootstrapError("ML-AFFA-BOOTSTRAP-CONFIG")
        if (
            sum(u.max_generation - u.generation + 1 for u in config.units) + 2
            > self.boundaries._limits.max_boundaries
        ):
            raise BootstrapError("ML-AFFA-C1-CAPACITY")
        for unit in config.units:
            descriptor = self._watches.get((unit.boundary_device, unit.boundary_inode))
            if descriptor is None:
                raise BootstrapError("ML-AFFA-UNWATCHED")
            entry = self.boundaries._entry(descriptor)
            self.boundaries._authority(entry)
            self.boundaries._verify(entry)
        self._authority_input = config
        child, channel = self._spawn_role(
            4,
            helper,
            helper,
            _sealed(config.encode(), "maestro-original-authority"),
            deadline,
        )
        try:
            client = AuthorityConnection(_CREATE, child, channel, config)
            self._clients[child._slot] = client
            self._client_log = tuple(sorted(self._clients.items()))
            client._ready(deadline)
            self.boundaries.bind_authority(client)
            return client
        except Exception:
            channel.close()
            self.cancel("bootstrap-authority-client-failed")
            raise

    def persistence(self, config, helper, deadline):
        from .persistence import PersistenceClient, PersistenceInput, sealed_input_fd

        if (
            type(config) is not PersistenceInput
            or config.run_id != self.config.admission.run_id
            or type(config.private_bytes) is not bytes
            or not 0 < len(config.private_bytes) <= 65536
        ):
            raise BootstrapError("ML-BOOT-PERSISTENCE")
        self._context(config.prepared.lifecycle_digest)
        child, channel = self._spawn_role(
            3, helper, helper, sealed_input_fd(config), deadline
        )
        try:
            client = PersistenceClient(
                child, channel, config, self.latch, deadline=deadline
            )
            self._clients[child._slot] = client
            self._client_log = tuple(sorted(self._clients.items()))
            return client
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
            client = CatalogLauncher(
                child,
                channel,
                owner,
                recipe,
                helper_artifact_digest=pin,
                deadline=deadline,
            )
            self._clients[child._slot] = client
            self._client_log = tuple(sorted(self._clients.items()))
            return client
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
            client = GateConnection(
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
            self._clients[child._slot] = client
            self._client_log = tuple(sorted(self._clients.items()))
            return client
        except Exception:
            self.cancel("bootstrap-client-failed")
            raise
