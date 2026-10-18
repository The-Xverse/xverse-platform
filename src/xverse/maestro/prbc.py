"""Original-holder cgroup-v2 boundary component, not a launcher or run admission.

The trusted original owner supplies an exclusive delegated parent and explicit
approval facts. This library cannot authenticate those facts. No child insertion,
thaw, workload callback, M3 outcome or normal provider handle is supplied here.
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
import ctypes
import math
import os
import stat
import sys
import threading
import time
from typing import Any
import uuid

from .supervisor import CancellationLatch
from .time import HostDeadline


class BoundaryError(ValueError):
    def __init__(self, code: str, record: "BoundaryRecord | None" = None):
        self.code = code
        self.record = record
        super().__init__(code)


def _text(value: object) -> None:
    if (
        type(value) is not str
        or not value
        or len(value) > 128
        or any(not (c.isascii() and (c.isalnum() or c in "-_.:")) for c in value)
    ):
        raise BoundaryError("ML-ADMISSION-BOUNDARY-IDENTITY")


def _uint(value: object, maximum: int) -> None:
    if type(value) is not int or not 0 <= value <= maximum:
        raise BoundaryError("ML-ADMISSION-BOUNDARY-INTEGER")


@dataclass(frozen=True)
class BoundaryDescriptor:
    run_id: str
    unit_id: str
    generation: int
    boundary_id: str
    creation_epoch: int

    def __post_init__(self) -> None:
        for value in (self.run_id, self.boundary_id):
            _text(value)
        # Logical XDL references are data, never filesystem paths or authority.
        if (
            type(self.unit_id) is not str
            or not 0 < len(self.unit_id) <= 128
            or any(not 33 <= ord(c) <= 126 for c in self.unit_id)
        ):
            raise BoundaryError("ML-ADMISSION-BOUNDARY-IDENTITY")
        _uint(self.generation, 2**32 - 1)
        _uint(self.creation_epoch, 2**64 - 1)

    @property
    def key(self) -> tuple[str, str, int, str, int]:
        return (
            self.run_id,
            self.unit_id,
            self.generation,
            self.boundary_id,
            self.creation_epoch,
        )


@dataclass(frozen=True)
class BoundaryAdmission:
    run_id: str
    supervisor_session: str
    affa_session: str
    bootstrap_approval_ref: str
    cleanup_approval_ref: str
    reservation_approval_ref: str | None
    teardown_deadline: HostDeadline
    initial_epoch: int

    def __post_init__(self) -> None:
        for value in (
            self.run_id,
            self.supervisor_session,
            self.affa_session,
            self.bootstrap_approval_ref,
            self.cleanup_approval_ref,
        ):
            _text(value)
        if self.reservation_approval_ref is not None:
            _text(self.reservation_approval_ref)
        if type(self.teardown_deadline) is not HostDeadline:
            raise BoundaryError("ML-ADMISSION-BOUNDARY-DEADLINE")
        _text(self.teardown_deadline.session)
        self.teardown_deadline.__post_init__()
        _uint(self.initial_epoch, 2**64 - 2)  # reserve one cancellation increment


@dataclass(frozen=True)
class BoundaryLimits:
    operation_seconds: float
    freeze_seconds: float = 1
    poll_seconds: float = 0.005
    max_members: int = 128
    max_control_bytes: int = 16384

    def __post_init__(self) -> None:
        for value, maximum in (
            (self.operation_seconds, 5),
            (self.freeze_seconds, 1),
            (self.poll_seconds, 0.05),
        ):
            try:
                valid = (
                    type(value) in (int, float)
                    and math.isfinite(value)
                    and 0 < value <= maximum
                )
            except OverflowError:
                valid = False
            if not valid:
                raise BoundaryError("ML-ADMISSION-BOUNDARY-LIMIT")
        _uint(self.max_members, 128)
        _uint(self.max_control_bytes, 16384)
        if self.max_members < 1 or self.max_control_bytes < 128:
            raise BoundaryError("ML-ADMISSION-BOUNDARY-LIMIT")


@dataclass(frozen=True)
class BoundaryRecord:
    descriptor: BoundaryDescriptor
    state: str
    release_epoch: int
    identity_retained: bool
    membership_complete: bool
    residual_count: int | None
    termination_observed: bool
    diagnostic: str | None
    ready_for_execution: bool = field(default=False, init=False)

    @property
    def boundary_released(self) -> bool:
        return self.state == "released"


class BoundaryOps(ABC):
    @abstractmethod
    def create_frozen(
        self, descriptor: BoundaryDescriptor, **options: Any
    ) -> BoundaryRecord:
        raise NotImplementedError

    @abstractmethod
    def residual_membership(self, descriptor: BoundaryDescriptor) -> tuple[int, ...]:
        raise NotImplementedError


@dataclass
class _Entry:
    descriptor: BoundaryDescriptor
    name: str
    reservation: object
    state: str = "reserved"
    allocated: bool = False
    fd: int = -1
    identity: tuple[int, int] | None = None
    c1: object | None = None
    complete: bool = False
    count: int | None = None
    terminated: bool = False
    diagnostic: str | None = None
    terminal: BoundaryRecord | None = None
    external_released: bool = False


def _identity(fd: int) -> tuple[int, int]:
    value = os.fstat(fd)
    if not stat.S_ISDIR(value.st_mode) or value.st_nlink == 0:
        raise BoundaryError("ML-OWNERSHIP-BOUNDARY-IDENTITY")
    return value.st_dev, value.st_ino


def _cgroup2(fd: int) -> None:
    if sys.platform != "linux":
        raise BoundaryError("ML-ADMISSION-CGROUP-UNSUPPORTED")
    libc = ctypes.CDLL(None, use_errno=True)
    call = libc.fstatfs
    call.argtypes = (ctypes.c_int, ctypes.c_void_p)
    call.restype = ctypes.c_int
    data = ctypes.create_string_buffer(512)
    if call(fd, data) != 0 or ctypes.c_long.from_buffer(data).value != 0x63677270:
        raise BoundaryError("ML-ADMISSION-CGROUP-FILESYSTEM")


class ProcessBoundaryOps(BoundaryOps):
    """Private original registry; caller facts never become authenticated approval.

    The holder must control the delegated parent exclusively. Kernel calls require
    separate outer supervision. All children use private fresh names; no operation
    targets the parent or an adopted path. There is no public insertion/Release API.
    """

    def __init__(
        self,
        parent_fd: int,
        admission: BoundaryAdmission,
        latch: CancellationLatch,
        limits: BoundaryLimits,
    ):
        if (
            type(parent_fd) is not int
            or parent_fd < 0
            or type(admission) is not BoundaryAdmission
        ):
            raise BoundaryError("ML-ADMISSION-BOUNDARY-INPUT")
        if type(latch) is not CancellationLatch or type(limits) is not BoundaryLimits:
            raise BoundaryError("ML-ADMISSION-BOUNDARY-INPUT")
        latch._check()
        deadline = admission.teardown_deadline
        self._admission = BoundaryAdmission(
            admission.run_id,
            admission.supervisor_session,
            admission.affa_session,
            admission.bootstrap_approval_ref,
            admission.cleanup_approval_ref,
            admission.reservation_approval_ref,
            HostDeadline(deadline.session, deadline.monotonic_seconds),
            admission.initial_epoch,
        )
        self._limits = BoundaryLimits(
            limits.operation_seconds,
            limits.freeze_seconds,
            limits.poll_seconds,
            limits.max_members,
            limits.max_control_bytes,
        )
        remaining = deadline.monotonic_seconds - time.monotonic()
        if not 0 < remaining <= 300 + 16 * 5 + 10 + 2 + 2:
            raise BoundaryError("ML-ADMISSION-BOUNDARY-DEADLINE")
        self._root_fd = os.dup(parent_fd)
        try:
            os.set_inheritable(self._root_fd, False)
            _cgroup2(self._root_fd)
            self._root_identity = _identity(self._root_fd)
            domain_fd = os.open(
                "cgroup.type",
                os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=self._root_fd,
            )
            try:
                if os.read(domain_fd, 128).strip() != b"domain":
                    raise BoundaryError("ML-ADMISSION-CGROUP-DOMAIN")
            finally:
                os.close(domain_fd)
            for control in (
                "cgroup.events",
                "cgroup.procs",
                "cgroup.freeze",
                "cgroup.kill",
            ):
                info = os.stat(control, dir_fd=self._root_fd, follow_symlinks=False)
                if not stat.S_ISREG(info.st_mode):
                    raise BoundaryError("ML-ADMISSION-CGROUP-CONTROL")
        except Exception:
            os.close(self._root_fd)
            self._root_fd = -1
            raise
        self._original = self
        self._pid = os.getpid()
        self._latch = latch
        self._entries: dict[tuple, _Entry] = {}
        self._reservations: dict[tuple, object] = {}
        self._caps: dict[tuple, object] = {}
        self._lock = threading.Lock()
        self._operation_deadline: float | None = None

    def __reduce_ex__(self, protocol: int):
        raise TypeError("original boundary registries cannot be serialized")

    def _holder(self) -> None:
        if self._original is not self or self._pid != os.getpid() or self._root_fd < 0:
            raise BoundaryError("ML-OWNERSHIP-BOUNDARY-HOLDER")
        self._latch._check()

    @property
    def release_epoch(self) -> int:
        self._holder()
        return self._admission.initial_epoch + self._latch.epoch

    @property
    def ready_for_execution(self) -> bool:
        return False

    def _deadline(self) -> None:
        deadline = self._admission.teardown_deadline.monotonic_seconds
        if self._operation_deadline is not None:
            deadline = min(deadline, self._operation_deadline)
        if time.monotonic() >= deadline:
            raise BoundaryError("ML-TIMEOUT-BOUNDARY-AUTHORITY")

    @contextmanager
    def _operation(self, deadline=None):
        explicit = self._admission.teardown_deadline.monotonic_seconds
        if deadline is not None:
            if (
                type(deadline) is not HostDeadline
                or deadline.session != self._admission.teardown_deadline.session
            ):
                raise BoundaryError("ML-TEARDOWN-DEADLINE")
            deadline.__post_init__()
            explicit = deadline.monotonic_seconds
            if (
                not 0 < explicit - time.monotonic() <= 5
                or explicit > self._admission.teardown_deadline.monotonic_seconds
            ):
                raise BoundaryError("ML-TEARDOWN-DEADLINE")
        self._operation_deadline = min(
            explicit,
            self._admission.teardown_deadline.monotonic_seconds,
            time.monotonic() + self._limits.operation_seconds,
        )
        try:
            yield
        finally:
            self._operation_deadline = None

    def _descriptor(self, descriptor: BoundaryDescriptor) -> BoundaryDescriptor:
        if type(descriptor) is not BoundaryDescriptor:
            raise BoundaryError("ML-ADMISSION-BOUNDARY-DESCRIPTOR")
        value = BoundaryDescriptor(*descriptor.key)
        if (
            value.run_id != self._admission.run_id
            or value.creation_epoch != self._admission.initial_epoch
        ):
            raise BoundaryError("ML-OWNERSHIP-BOUNDARY-SCOPE")
        return value

    def _entry(self, descriptor: BoundaryDescriptor) -> _Entry:
        self._holder()
        value = self._descriptor(descriptor)
        if value.key not in self._entries:
            raise BoundaryError("ML-OWNERSHIP-BOUNDARY-UNKNOWN")
        return self._entries[value.key]

    def _snapshot(self, entry: _Entry) -> BoundaryRecord:
        return BoundaryRecord(
            entry.descriptor,
            entry.state,
            self.release_epoch,
            entry.fd >= 0,
            entry.complete,
            entry.count,
            entry.terminated,
            entry.diagnostic,
        )

    def record(
        self, descriptor: BoundaryDescriptor, *, deadline=None
    ) -> BoundaryRecord:
        entry = self._entry(descriptor)
        with self._cleanup_lock(deadline):
            return entry.terminal or self._snapshot(entry)

    def _authority(self, entry: _Entry, *, reservation: bool = False) -> None:
        self._holder()
        self._deadline()
        key = entry.descriptor.key
        cap = self._caps.get(key)
        if cap is not None and cap is entry.c1:
            return
        if (
            reservation
            and entry.c1 is None
            and self._admission.reservation_approval_ref is not None
            and (self._reservations.get(key) is entry.reservation)
        ):
            return
        raise BoundaryError("ML-OWNERSHIP-BOUNDARY-CAPABILITY")

    def _removed(self, entry: _Entry) -> bool:
        info = os.fstat(entry.fd)
        if (info.st_dev, info.st_ino) != entry.identity:
            raise BoundaryError("ML-OWNERSHIP-BOUNDARY-IDENTITY")
        # Kernfs link counts do not use the ordinary filesystem unlink predicate.
        # These kernel-owned control files cannot be individually removed by users.
        for name in ("cgroup.events", "cgroup.procs", "cgroup.freeze"):
            try:
                fd = os.open(
                    name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=entry.fd
                )
            except FileNotFoundError:
                continue
            else:
                os.close(fd)
                return False
        return True

    def _verify(self, entry: _Entry) -> None:
        if _identity(self._root_fd) != self._root_identity or entry.fd < 0:
            raise BoundaryError("ML-OWNERSHIP-BOUNDARY-IDENTITY")
        if _identity(entry.fd) != entry.identity:
            raise BoundaryError("ML-OWNERSHIP-BOUNDARY-IDENTITY")
        value = os.stat(entry.name, dir_fd=self._root_fd, follow_symlinks=False)
        if (
            not stat.S_ISDIR(value.st_mode)
            or (value.st_dev, value.st_ino) != entry.identity
        ):
            raise BoundaryError("ML-OWNERSHIP-BOUNDARY-SUBSTITUTED")

    def _read(self, entry: _Entry, name: str) -> str:
        self._deadline()
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=entry.fd)
        try:
            data = bytearray()
            while True:
                piece = os.read(fd, self._limits.max_control_bytes + 1 - len(data))
                if not piece:
                    break
                data.extend(piece)
                if len(data) > self._limits.max_control_bytes:
                    raise BoundaryError("ML-TEARDOWN-MEMBERSHIP-BOUND")
            return data.decode("ascii")
        finally:
            os.close(fd)

    def _write(self, entry: _Entry, name: str, value: bytes) -> None:
        self._deadline()
        self._verify(entry)
        fd = os.open(name, os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=entry.fd)
        try:
            self._deadline()
            if os.write(fd, value) != len(value):
                raise BoundaryError("ML-TEARDOWN-BOUNDARY-WRITE")
        finally:
            os.close(fd)

    def _fields(self, entry: _Entry, name: str) -> dict[str, int]:
        pairs = self._read(entry, name).splitlines()
        values = {}
        for line in pairs:
            parts = line.split()
            if (
                len(parts) != 2
                or parts[0] in values
                or not parts[1].isascii()
                or not parts[1].isdigit()
                or len(parts[1]) > 20
            ):
                raise BoundaryError("ML-TEARDOWN-MEMBERSHIP-UNKNOWN")
            values[parts[0]] = int(parts[1])
            if values[parts[0]] > 2**64 - 1:
                raise BoundaryError("ML-TEARDOWN-MEMBERSHIP-UNKNOWN")
        return values

    def _events(self, entry: _Entry) -> dict[str, int]:
        values = self._fields(entry, "cgroup.events")
        if any(values.get(k) not in (0, 1) for k in ("populated", "frozen")):
            raise BoundaryError("ML-TEARDOWN-MEMBERSHIP-UNKNOWN")
        return values

    def _freeze(self, entry: _Entry) -> None:
        self._write(entry, "cgroup.freeze", b"1")
        until = min(
            self._admission.teardown_deadline.monotonic_seconds,
            time.monotonic() + self._limits.freeze_seconds,
        )
        while self._events(entry)["frozen"] != 1:
            if time.monotonic() >= until:
                raise BoundaryError("ML-TIMEOUT-BOUNDARY-FREEZE")
            time.sleep(min(self._limits.poll_seconds, max(0, until - time.monotonic())))

    def _members(self, entry: _Entry) -> tuple[int, ...]:
        self._verify(entry)
        if self._fields(entry, "cgroup.stat").get("nr_descendants") != 0:
            raise BoundaryError("ML-TEARDOWN-NESTED-BOUNDARY")
        before = self._events(entry)
        samples = []
        for _ in range(2):
            tokens = self._read(entry, "cgroup.procs").split()
            if len(tokens) > self._limits.max_members or any(
                not p.isascii()
                or not p.isdigit()
                or len(p) > 10
                or not 0 < int(p) < 2**31
                for p in tokens
            ):
                raise BoundaryError("ML-TEARDOWN-MEMBERSHIP-UNKNOWN")
            members = tuple(sorted(map(int, tokens)))
            if len(set(members)) != len(members):
                raise BoundaryError("ML-TEARDOWN-MEMBERSHIP-UNKNOWN")
            samples.append(members)
        after = self._events(entry)
        self._verify(entry)
        if (
            before != after
            or after["frozen"] != 1
            or samples[0] != samples[1]
            or (bool(samples[1]) != bool(after["populated"]))
        ):
            raise BoundaryError("ML-TEARDOWN-MEMBERSHIP-UNKNOWN")
        self._deadline()
        entry.complete, entry.count = True, len(samples[1])
        return samples[1]

    def _reservation_empty(self, entry: _Entry) -> None:
        """Read-only CP-02 proof; the reservation grants no freeze/kill right."""
        self._verify(entry)
        if self._fields(entry, "cgroup.stat").get("nr_descendants") != 0:
            raise BoundaryError("ML-TEARDOWN-NESTED-BOUNDARY")
        before = self._events(entry)
        if (
            before["populated"]
            or self._read(entry, "cgroup.procs").strip()
            or (self._events(entry) != before)
        ):
            raise BoundaryError("ML-OWNERSHIP-RESERVATION-NOT-EMPTY")
        self._verify(entry)
        self._deadline()
        entry.complete, entry.count = True, 0

    def _error(
        self, entry: _Entry, exc: Exception, state: str = "unresolved"
    ) -> BoundaryError:
        self._latch.cancel("boundary-unresolved")
        entry.state, entry.complete, entry.count = state, False, None
        entry.diagnostic = (
            exc.code if isinstance(exc, BoundaryError) else "ML-TEARDOWN-BOUNDARY-IO"
        )
        return BoundaryError(entry.diagnostic, self._snapshot(entry))

    def create_frozen(
        self, descriptor: BoundaryDescriptor, **options: Any
    ) -> BoundaryRecord:
        self._holder()
        value = self._descriptor(descriptor)
        if options:
            raise BoundaryError("ML-ADMISSION-BOUNDARY-OPTIONS")
        with self._lock, self._operation():
            self._deadline()
            if self._latch.cancelled:
                raise BoundaryError("ML-CANCELLED-BOUNDARY-STAGE")
            if value.key in self._entries:
                entry = self._entries[value.key]
                if entry.state == "frozen":
                    try:
                        self._authority(entry)
                        self._members(entry)
                        with self._latch._lock:
                            if self._latch.cancelled:
                                raise BoundaryError("ML-CANCELLED-BOUNDARY-LATE-STAGE")
                            return self._snapshot(entry)
                    except (OSError, UnicodeError, BoundaryError) as exc:
                        raise self._error(entry, exc) from exc
                raise BoundaryError("ML-CONFLICT-BOUNDARY-STAGE", self._snapshot(entry))
            if len(self._entries) >= 16 or any(
                (e.descriptor.unit_id, e.descriptor.generation)
                == (value.unit_id, value.generation)
                for e in self._entries.values()
            ):
                raise BoundaryError("ML-CONFLICT-BOUNDARY-GENERATION")
            entry = _Entry(value, "mlb-" + uuid.uuid4().hex, object())
            self._entries[value.key] = entry  # reservation precedes allocation
            self._reservations[value.key] = entry.reservation
            try:
                entry.state = "creating"
                os.mkdir(entry.name, mode=0o700, dir_fd=self._root_fd)
                entry.allocated = True
                entry.fd = os.open(
                    entry.name,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                    dir_fd=self._root_fd,
                )
                entry.identity = _identity(entry.fd)
                _cgroup2(entry.fd)
                self._verify(entry)
                if self._read(entry, "cgroup.type").strip() != "domain":
                    raise BoundaryError("ML-ADMISSION-CGROUP-DOMAIN")
                # C1 is retained before any future child insertion can be admitted.
                entry.c1 = object()
                self._caps[value.key] = entry.c1
                self._write(entry, "cgroup.max.depth", b"0")
                self._write(entry, "cgroup.max.descendants", b"0")
                self._freeze(entry)
                self._members(entry)
                with self._latch._lock:
                    if self._latch.cancelled:
                        raise BoundaryError("ML-CANCELLED-BOUNDARY-LATE-STAGE")
                    self._deadline()
                    entry.state = "frozen"
                    return self._snapshot(entry)
            except (OSError, UnicodeError, BoundaryError) as exc:
                raise self._error(entry, exc, "partial") from exc

    def residual_membership(self, descriptor: BoundaryDescriptor) -> tuple[int, ...]:
        entry = self._entry(descriptor)
        with self._lock, self._operation():
            if entry.state == "released":
                raise BoundaryError("ML-OWNERSHIP-BOUNDARY-OBSERVATION-CLOSED")
            try:
                self._authority(entry)
                return self._members(entry)
            except (OSError, UnicodeError, BoundaryError) as exc:
                raise self._error(entry, exc) from exc

    @contextmanager
    def _cleanup_lock(self, deadline):
        if not self._lock.acquire(blocking=deadline is None):
            raise BoundaryError("ML-TEARDOWN-CONFLICT")
        try:
            yield
        finally:
            self._lock.release()

    def terminate(self, descriptor, *, deadline):
        """Original C1 force/empty observation, retaining the frozen boundary."""
        entry = self._entry(descriptor)
        with self._cleanup_lock(deadline), self._operation(deadline):
            if entry.terminal is not None:
                return entry.terminal
            try:
                self._authority(entry)
                self._verify(entry)
                self._freeze(entry)
                members = self._members(entry)
                if members:
                    self._write(entry, "cgroup.kill", b"1")
                    while self._events(entry)["populated"]:
                        self._deadline()
                        time.sleep(self._limits.poll_seconds)
                    entry.terminated = True
                if self._members(entry):
                    raise BoundaryError("ML-TEARDOWN-BOUNDARY-LIVE")
                entry.state, entry.diagnostic = "empty", None
                self._deadline()
                return self._snapshot(entry)
            except (OSError, UnicodeError, BoundaryError) as exc:
                raise self._error(entry, exc) from exc

    def release_empty(self, descriptor, *, deadline):
        """Remove only a previously observed empty original frozen boundary."""
        entry = self._entry(descriptor)
        with self._cleanup_lock(deadline), self._operation(deadline):
            if entry.terminal is not None:
                return entry.terminal
            if entry.state != "empty":
                raise BoundaryError("ML-TEARDOWN-BOUNDARY-NOT-STOPPED")
            try:
                self._authority(entry)
                self._verify(entry)
                if self._members(entry):
                    raise BoundaryError("ML-TEARDOWN-BOUNDARY-LIVE")
                self._deadline()
                os.rmdir(entry.name, dir_fd=self._root_fd)
                if not self._removed(entry):
                    raise BoundaryError("ML-TEARDOWN-BOUNDARY-RELEASE")
                try:
                    os.stat(entry.name, dir_fd=self._root_fd, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise BoundaryError("ML-TEARDOWN-BOUNDARY-SUBSTITUTED")
                self._deadline()
                os.close(entry.fd)
                entry.fd = -1
                entry.state, entry.diagnostic = "released", None
                entry.terminal = self._snapshot(entry)
                return entry.terminal
            except (OSError, UnicodeError, BoundaryError) as exc:
                raise self._error(entry, exc) from exc

    def force_cleanup(
        self, descriptor: BoundaryDescriptor, *, deadline=None
    ) -> BoundaryRecord:
        entry = self._entry(descriptor)
        with self._cleanup_lock(deadline), self._operation(deadline):
            if entry.terminal is not None:
                return entry.terminal
            entry.state = "release_pending"
            try:
                self._authority(entry, reservation=True)
                self._verify(entry)
                reservation_only = entry.c1 is None
                if reservation_only:
                    self._reservation_empty(entry)
                    members = ()
                else:
                    self._freeze(entry)
                    members = self._members(entry)
                if members:
                    self._authority(entry)  # reservation alone has no kill right
                    self._write(entry, "cgroup.kill", b"1")
                    while self._events(entry)["populated"]:
                        self._deadline()
                        time.sleep(self._limits.poll_seconds)
                    self._members(entry)
                    entry.terminated = True
                self._authority(entry, reservation=True)
                if reservation_only:
                    self._reservation_empty(entry)
                elif self._members(entry):
                    raise BoundaryError("ML-TEARDOWN-BOUNDARY-LIVE")
                self._verify(entry)
                self._deadline()
                os.rmdir(entry.name, dir_fd=self._root_fd)
                # Unlink is the kernel terminal fence, not a requested-release flag.
                if not self._removed(entry):
                    raise BoundaryError("ML-TEARDOWN-BOUNDARY-RELEASE")
                try:
                    os.stat(entry.name, dir_fd=self._root_fd, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise BoundaryError("ML-TEARDOWN-BOUNDARY-SUBSTITUTED")
                self._deadline()
                os.close(entry.fd)
                entry.fd = -1
                entry.state, entry.diagnostic = "released", None
                entry.terminal = self._snapshot(entry)
                return entry.terminal
            except (OSError, UnicodeError, BoundaryError) as exc:
                return self._error(entry, exc).record

    def dispose_external_release(self, descriptor: BoundaryDescriptor) -> None:
        """Dispose local FD only after exact externally removed identity is observed.

        Never promotes the previous unresolved cleanup into an authorized success.
        """
        entry = self._entry(descriptor)
        with self._lock:
            if entry.fd >= 0:
                if not self._removed(entry):
                    raise BoundaryError("ML-OWNERSHIP-BOUNDARY-STILL-RETAINED")
                os.close(entry.fd)
                entry.fd = -1
                entry.external_released = True

    def close(self) -> None:
        self._holder()
        with self._lock:
            if any(
                e.fd >= 0
                or (e.allocated and e.state != "released" and not e.external_released)
                for e in self._entries.values()
            ):
                raise BoundaryError("ML-OWNERSHIP-BOUNDARY-RETAINED")
            os.close(self._root_fd)
            self._root_fd = -1
