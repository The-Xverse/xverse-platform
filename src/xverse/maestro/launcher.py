"""Catalog-selected native frozen birth and original issuer registry; partial U3/U4.

Initial helper creation and executable/environment admission remain trusted
bootstrap obligations. No C1 transfer, discovery, readiness or normal outcome.
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
import threading
import time

from xverse_xdl.lifecycle import OwnedResourceHandle
from .child import check_child, open_child_pidfd, wait_child
from .owner import (
    OwnerError,
    ReleaseOwner,
    GateConnection,
    _Original,
    _hash,
    _pin,
    _deadline,
)
from .prbc import BoundaryDescriptor
from .persistence import SEALS

_WIRE = struct.Struct("!4sIQQ32sQQQQ32sQ")
_HEADER = struct.Struct("!4sIQQQII32s32s")
_ZERO = bytes(32)


class LauncherError(OwnerError):
    pass


@dataclass(frozen=True)
class LaunchPacket:
    kind: int
    sequence: int
    deadline_ns: int
    scope: bytes
    device: int
    inode: int
    reason: int = 0
    child_pid: int = 0
    token: bytes = field(default=_ZERO, repr=False)
    state: int = 0

    def __post_init__(self):
        for value in (
            self.kind,
            self.sequence,
            self.deadline_ns,
            self.device,
            self.inode,
            self.reason,
            self.child_pid,
            self.state,
        ):
            if type(value) is not int or not 0 <= value < 2**64:
                raise LauncherError("ML-LAUNCH-WIRE-INTEGER")
        if (
            self.kind not in (1, 2, 3, 16, 17, 18, 19, 20)
            or self.reason > 7
            or not self.deadline_ns
        ):
            raise LauncherError("ML-LAUNCH-WIRE-HEADER")
        if any(type(v) is not bytes or len(v) != 32 for v in (self.scope, self.token)):
            raise LauncherError("ML-LAUNCH-WIRE-DIGEST")
        if self.kind in (1, 2, 3) and (not self.sequence or self.reason or self.state):
            raise LauncherError("ML-LAUNCH-WIRE-COMMAND")
        if self.kind == 16 and (
            self.sequence
            or self.reason
            or self.child_pid
            or self.token != _ZERO
            or self.state
        ):
            raise LauncherError("ML-LAUNCH-WIRE-READY")
        if self.kind == 1 and (self.child_pid or self.token != _ZERO):
            raise LauncherError("ML-LAUNCH-WIRE-STAGE")
        if (
            (self.child_pid == 0) != (self.token == _ZERO)
            or self.child_pid == 1
            or (self.state & 0xFFFFFFE0)
        ):
            raise LauncherError("ML-LAUNCH-WIRE-CHILD")
        if self.kind in (17, 20) and not self.child_pid:
            raise LauncherError("ML-LAUNCH-WIRE-CHILD")

    def encode(self):
        self.__post_init__()
        return _WIRE.pack(
            b"LC09",
            self.kind,
            self.sequence,
            self.deadline_ns,
            self.scope,
            self.reason,
            self.device,
            self.inode,
            self.child_pid,
            self.token,
            self.state,
        )

    @classmethod
    def decode(cls, data):
        if type(data) is not bytes or len(data) != 128:
            raise LauncherError("ML-LAUNCH-WIRE-SIZE")
        (
            magic,
            kind,
            sequence,
            deadline,
            scope,
            reason,
            device,
            inode,
            pid,
            token,
            state,
        ) = _WIRE.unpack(data)
        if magic != b"LC09":
            raise LauncherError("ML-LAUNCH-WIRE-MAGIC")
        return cls(
            kind, sequence, deadline, scope, device, inode, reason, pid, token, state
        )


@dataclass(frozen=True)
class LaunchRecipe:
    unit_id: str
    descriptor: BoundaryDescriptor
    execution_id: str
    action_id: str
    device: int
    inode: int
    generation_ns: int
    operation_deadline_ns: int
    scope: bytes
    private_bytes: bytes = field(repr=False)
    environment: tuple = field(repr=False)


def make_launch_recipe(
    owner, descriptor, *, environment, helper_artifact_digest, deadline
):
    """Observe original C1 and derive a recipe; delegate executable/cwd lookup."""
    if (
        type(owner) is not ReleaseOwner
        or type(descriptor) is not BoundaryDescriptor
        or type(environment) is not dict
    ):
        raise LauncherError("ML-LAUNCH-INPUT")
    owner._check(deadline)
    unit = owner._unit(descriptor.unit_id)
    claim = owner._claims.get(unit.unit_id)
    if claim is None or claim.attempted or owner._check(deadline) > claim.deadline_ns:
        raise LauncherError("ML-LAUNCH-INTENT")
    if (
        unit.provider.kind != "process"
        or unit.plan.process_action is None
        or helper_artifact_digest != unit.provider.artifact_digest
    ):
        raise LauncherError("ML-LAUNCH-PROVIDER")
    owner.scope(unit.unit_id, descriptor, helper_artifact_digest)
    action = unit.plan.process_action
    action.__post_init__()
    if set(environment) != set(action.environment_names):
        raise LauncherError("ML-LAUNCH-ENVIRONMENT")
    if owner.persistence is None:
        execution = claim.receipt.execution_id
        resources = owner.permits._resources
    else:
        execution = owner.persistence._claim_execution_id(claim.receipt)
        resources = owner.persistence._resources
    deployment = next(
        (r for r in resources if r.identity.uri == unit.plan.selection["deployment"]),
        None,
    )
    if deployment is None:
        raise LauncherError("ML-LAUNCH-ARTIFACT")
    binding = next(
        (b for b in deployment.content["bindings"] if b["id"] == unit.binding_id), None
    )
    candidates = [
        a
        for a in deployment.content.get("artifacts", ())
        if binding is not None
        and a["id"] in binding["artifactIds"]
        and a["sourceRef"] == Path(action.executable).as_uri()
        and a.get("digest") in unit.plan.artifact_digests
    ]
    if len(candidates) != 1:
        raise LauncherError("ML-LAUNCH-ARTIFACT")
    digest = _pin(candidates[0]["digest"])
    manager = owner.supervisor.boundaries
    members = manager.residual_membership(descriptor)
    entry = manager._entry(descriptor)
    if members or manager.record(descriptor).state != "frozen":
        raise LauncherError("ML-LAUNCH-NOT-EMPTY")
    info = os.fstat(entry.fd)
    generation = int(manager._admission.teardown_deadline.monotonic_seconds * 1e9)
    argv = (action.executable, *action.arguments)
    values = (
        *argv,
        action.working_directory,
        *(name + "=" + environment[name] for name in sorted(environment)),
    )
    if len(argv) > 64 or len(environment) > 32:
        raise LauncherError("ML-LAUNCH-LIMIT")
    parts = []
    for value in values:
        if type(value) is not str or "\0" in value:
            raise LauncherError("ML-LAUNCH-STRING")
        data = value.encode()
        if len(data) > 4096:
            raise LauncherError("ML-LAUNCH-STRING")
        parts.append(struct.pack("!I", len(data)) + data + b"\0")
    scope = _hash(
        [
            "xverse.maestro.launcher9",
            owner._prepared.lifecycle_digest,
            unit.plan.digest,
            list(descriptor.key),
            execution,
            claim.operation,
            claim.deadline_ns,
            info.st_dev,
            info.st_ino,
            generation,
            helper_artifact_digest,
            values,
        ]
    )
    private = _HEADER.pack(
        b"LCF9",
        1,
        generation,
        info.st_dev,
        info.st_ino,
        len(argv),
        len(environment),
        digest,
        scope,
    ) + b"".join(parts)
    if len(private) > 65536:
        raise LauncherError("ML-LAUNCH-LIMIT")
    start = next(a.action_id for a in unit.plan.actions if a.phase == "start")
    return LaunchRecipe(
        unit.unit_id,
        descriptor,
        execution,
        start,
        info.st_dev,
        info.st_ino,
        generation,
        claim.deadline_ns,
        hashlib.sha256(private).digest(),
        private,
        tuple(sorted(environment.items())),
    )


def sealed_recipe_fd(recipe):
    """Bootstrap-only private input creation, outside bounded RPC claims."""
    if type(recipe) is not LaunchRecipe or not 104 < len(recipe.private_bytes) <= 65536:
        raise LauncherError("ML-LAUNCH-RECIPE")
    fd = os.memfd_create(
        "maestro-private-launch", os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING
    )
    try:
        view = memoryview(recipe.private_bytes)
        while view:
            n = os.write(fd, view)
            if n <= 0:
                raise LauncherError("ML-LAUNCH-RECIPE-WRITE")
            view = view[n:]
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, SEALS)
        return fd
    except Exception:
        os.close(fd)
        raise


@dataclass(frozen=True)
class ProcessObservation:
    handle: OwnedResourceHandle
    host_session: str
    observed_at: float
    exec_pipe_closed: bool
    leader_alive: bool
    leader_reaped: bool
    exec_error: bool
    returncode: int | None
    ready_for_execution: bool = field(default=False, init=False)
    cleanup_complete: bool = field(default=False, init=False)

    @property
    def running(self):
        return self.exec_pipe_closed and self.leader_alive and not self.exec_error


@dataclass(frozen=True)
class LauncherDrain:
    helper_reaped: bool
    direct_child_reaped: bool
    identity_retained: bool
    diagnostic: str | None
    cleanup_complete: bool = field(default=False, init=False)


class CatalogLauncher(_Original):
    def __init__(
        self, process, channel, owner, recipe, *, helper_artifact_digest, deadline
    ):
        check_child(process, live=True)
        if (
            type(channel) is not socket.socket
            or type(owner) is not ReleaseOwner
            or type(recipe) is not LaunchRecipe
        ):
            raise LauncherError("ML-LAUNCH-INPUT")
        if (
            channel.family != socket.AF_UNIX
            or channel.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE)
            != socket.SOCK_SEQPACKET
            or not channel.getsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED)
        ):
            raise LauncherError("ML-LAUNCH-SOCKET")
        _pin(helper_artifact_digest)
        if (
            owner._unit(recipe.unit_id).provider.artifact_digest
            != helper_artifact_digest
        ):
            raise LauncherError("ML-LAUNCH-PROVIDER")
        owner._check(deadline)
        expected = make_launch_recipe(
            owner,
            recipe.descriptor,
            environment=dict(recipe.environment),
            helper_artifact_digest=helper_artifact_digest,
            deadline=deadline,
        )
        if recipe != expected:
            raise LauncherError("ML-LAUNCH-RECIPE-MISMATCH")
        self._retain()
        self.process, self.channel, self.owner = process, channel, owner
        self.unit_id, self.recipe = recipe.unit_id, recipe
        self._pins = (process, channel, owner, recipe)
        self._pid_pin = process.pid
        info = os.fstat(channel.fileno())
        self._socket_identity = (info.st_dev, info.st_ino)
        self._stage_lock = threading.Lock()
        self._stage_started = False
        self._pidfd = -1
        self._childfd = -1
        self._child_pid = 0
        self._token = _ZERO
        self._sequence = 0
        self._handle = None
        self._lock = threading.Lock()
        self._cancelled = False
        self._drained = None
        self._drain_end = None
        channel.setblocking(False)
        try:
            self._pidfd = open_child_pidfd(process)
            self._live()
            reply, fd = self._receive(_deadline(deadline, owner.session), 1)
            try:
                expected = LaunchPacket(
                    16,
                    0,
                    recipe.generation_ns,
                    recipe.scope,
                    recipe.device,
                    recipe.inode,
                )
                info = os.fstat(fd)
                if (
                    reply != expected
                    or not stat.S_ISDIR(info.st_mode)
                    or (info.st_dev, info.st_ino) != (recipe.device, recipe.inode)
                ):
                    raise LauncherError("ML-LAUNCH-READY")
            finally:
                os.close(fd)
            self._check_boundary(empty=True)
            owner._register_launcher(self)
        except Exception:
            self.cancel("launcher-registration-failed")
            if self._pidfd >= 0:
                os.close(self._pidfd)
            self._pidfd = -1
            raise

    def _holder(self):
        super()._holder()
        if (
            any(
                a is not b
                for a, b in zip(
                    (self.process, self.channel, self.owner, self.recipe), self._pins
                )
            )
            or self.unit_id != self.recipe.unit_id
        ):
            raise LauncherError("ML-LAUNCH-REPLACED")
        self.owner._holder()

    def _live(self):
        self._holder()
        check_child(self._pins[0], live=True)
        info = os.fstat(self._pins[1].fileno())
        if (info.st_dev, info.st_ino) != self._socket_identity:
            raise LauncherError("ML-LAUNCH-SOCKET-REPLACED")
        if (
            self._pidfd < 0
            or self.process.pid != self._pid_pin
            or self._cancelled
            or self.owner._pins[3].cancelled
        ):
            raise LauncherError("ML-LAUNCH-CLOSED")
        if (
            wait_child(self._pins[0], self._pidfd) is not None
            or select.select([self._pidfd], [], [], 0)[0]
        ):
            raise LauncherError("ML-LAUNCH-ISSUER")

    def _check_boundary(self, empty=False):
        manager = self.owner.supervisor.boundaries
        members = manager.residual_membership(self.recipe.descriptor)
        entry = manager._entry(self.recipe.descriptor)
        info = os.fstat(entry.fd)
        if (info.st_dev, info.st_ino) != (self.recipe.device, self.recipe.inode) or (
            empty and members
        ):
            raise LauncherError("ML-LAUNCH-BOUNDARY")
        return members

    def _receive(self, until, count):
        while True:
            self._live()
            remaining = (until - time.monotonic_ns()) / 1e9
            if remaining <= 0:
                raise LauncherError("ML-LAUNCH-TIMEOUT")
            if not select.select([self._pins[1]], [], [], min(remaining, 0.01))[0]:
                continue
            try:
                data, anc, flags, _ = self._pins[1].recvmsg(
                    129,
                    socket.CMSG_SPACE(12) + socket.CMSG_SPACE(32),
                    socket.MSG_CMSG_CLOEXEC,
                )
            except BlockingIOError:
                continue
            credentials = []
            received = []
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
                self._live()
                if (
                    not valid
                    or credentials != [(self._pid_pin, os.getuid(), os.getgid())]
                    or len(received) != count
                    or time.monotonic_ns() >= until
                ):
                    raise LauncherError("ML-LAUNCH-SENDER")
                reply = LaunchPacket.decode(data)
                fd = received.pop() if count else -1
                return reply, fd
            finally:
                for fd in received:
                    os.close(fd)

    def _rpc(self, kind, deadline, expected, count):
        if not self._lock.acquire(False):
            raise LauncherError("ML-LAUNCH-CONFLICT")
        try:
            self._live()
            until = _deadline(deadline, self.owner.session)
            if until > self.recipe.generation_ns - 2_000_000_000 or (
                kind == 1 and until > self.recipe.operation_deadline_ns
            ):
                raise LauncherError("ML-LAUNCH-DEADLINE")
            request = LaunchPacket(
                kind,
                self._sequence + 1,
                until,
                self.recipe.scope,
                self.recipe.device,
                self.recipe.inode,
                child_pid=self._child_pid,
                token=self._token,
            )
            if self._pins[1].send(request.encode()) != 128:
                raise LauncherError("ML-LAUNCH-SEND")
            reply, fd = self._receive(until, count)
            try:
                self._sequence = request.sequence
                if (
                    reply.kind,
                    reply.sequence,
                    reply.deadline_ns,
                    reply.scope,
                    reply.device,
                    reply.inode,
                    reply.reason,
                ) != (
                    expected,
                    request.sequence,
                    until,
                    request.scope,
                    request.device,
                    request.inode,
                    0,
                ):
                    raise LauncherError("ML-LAUNCH-ACK")
                if kind != 1 and (reply.child_pid, reply.token) != (
                    self._child_pid,
                    self._token,
                ):
                    raise LauncherError("ML-LAUNCH-HANDLE")
                return reply, fd
            except Exception:
                if fd >= 0:
                    os.close(fd)
                raise
        except Exception:
            self.cancel("launcher-uncertain")
            raise
        finally:
            self._lock.release()

    def stage(self, deadline):
        if not self._stage_lock.acquire(False):
            raise LauncherError("ML-LAUNCH-CONFLICT")
        try:
            self._live()
            if self._stage_started:
                raise LauncherError("ML-LAUNCH-REPLAY")
            self._stage_started = True
            claim = self.owner._stage_claim(self.unit_id, deadline)
            if (
                self.owner._check(deadline) > self.recipe.operation_deadline_ns
                or claim.deadline_ns != self.recipe.operation_deadline_ns
            ):
                raise LauncherError("ML-LAUNCH-DEADLINE")
            self._check_boundary(empty=True)
            reply, fd = self._rpc(1, deadline, 17, 1)
            try:
                signal.pidfd_send_signal(fd, 0)
                if reply.state != 5 or self._check_boundary() != (reply.child_pid,):
                    raise LauncherError("ML-LAUNCH-STAGE")
                self._child_pid, self._token, self._childfd = (
                    reply.child_pid,
                    reply.token,
                    fd,
                )
                self._handle = OwnedResourceHandle(
                    self._token.hex(),
                    self.recipe.execution_id,
                    self.recipe.action_id,
                    "maestro-process-v1",
                    "process",
                    "maestro-boundary:" + self.recipe.scope.hex(),
                )
                return self._handle
            except Exception:
                os.close(fd)
                self.cancel("launcher-stage-invalid")
                raise

        finally:
            self._stage_lock.release()

    def _issued(self, handle):
        self._live()
        if (
            type(handle) is not OwnedResourceHandle
            or self._handle is None
            or handle != self._handle
        ):
            raise LauncherError("ML-LAUNCH-HANDLE")
        if self._childfd < 0 or select.select([self._childfd], [], [], 0)[0]:
            raise LauncherError("ML-LAUNCH-CHILD-EXIT")

    def _validate_release(self, descriptor, gate):
        self._issued(self._handle)
        if (
            descriptor != self.recipe.descriptor
            or type(gate) is not GateConnection
            or gate._boundary_proven != (self.recipe.device, self.recipe.inode)
        ):
            raise LauncherError("ML-LAUNCH-GATE-BOUNDARY")
        if self._check_boundary() != (self._child_pid,):
            raise LauncherError("ML-LAUNCH-MEMBERSHIP")

    def observe(self, handle, deadline):
        self._holder()
        self._live()
        if self._handle is None or handle != self._handle:
            raise LauncherError("ML-LAUNCH-HANDLE")
        reply, _ = self._rpc(3, deadline, 20, 0)
        flags = reply.state & 0xFFFFFFFF
        if flags & 4 and select.select([self._childfd], [], [], 0)[0]:
            flags &= ~4
        code = None
        if flags & 8:
            raw = reply.state >> 32
            if os.WIFEXITED(raw):
                code = os.WEXITSTATUS(raw)
            elif os.WIFSIGNALED(raw):
                code = -os.WTERMSIG(raw)
        return ProcessObservation(
            handle,
            self.owner.session,
            time.monotonic(),
            bool(flags & 2),
            bool(flags & 4),
            bool(flags & 8),
            bool(flags & 16),
            code,
        )

    def cancel(self, reason="launcher-cancel"):
        super()._holder()
        self._cancelled = True
        self._pins[2]._pins[3].cancel(reason)
        try:
            self._pins[1].shutdown(socket.SHUT_WR)
        except OSError:
            pass

    def drain(self, deadline):
        self._holder()
        if self._drained and self._drained.helper_reaped:
            return self._drained
        if not self._cancelled:
            raise LauncherError("ML-LAUNCH-STILL-OPEN")
        until = _deadline(deadline, self.owner.session)
        if (
            until - time.monotonic_ns() > 2_000_000_000
            or until > self.recipe.generation_ns
        ):
            raise LauncherError("ML-LAUNCH-DRAIN-LIMIT")
        self._drain_end = min(self._drain_end or until, until)
        while True:
            try:
                result = wait_child(self._pins[0], self._pidfd, consume=True)
            except OSError:
                self._drained = LauncherDrain(
                    False, False, True, "ML-LAUNCH-WAIT-UNRESOLVED"
                )
                return self._drained
            if result is not None:
                code = (
                    result.si_status
                    if result.si_code == os.CLD_EXITED
                    else -result.si_status
                )
                self._pins[0].returncode = code
                self._drained = LauncherDrain(
                    True,
                    code == 0,
                    True,
                    None if code == 0 else "ML-LAUNCH-CHILD-REAP-UNRESOLVED",
                )
                return self._drained
            remaining = (self._drain_end - time.monotonic_ns()) / 1e9
            if remaining <= 0:
                self._drained = LauncherDrain(
                    False, False, True, "ML-LAUNCH-DRAIN-UNRESOLVED"
                )
                return self._drained
            select.select([self._pidfd], [], [], min(remaining, 0.01))

    def dispose(self):
        self._holder()
        if not self._drained or not self._drained.helper_reaped:
            raise LauncherError("ML-LAUNCH-RETAINED")
        for name in ("_pidfd", "_childfd"):
            fd = getattr(self, name)
            if fd >= 0:
                os.close(fd)
                setattr(self, name, -1)
        self._pins[1].close()
