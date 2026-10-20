"""Original low-level supervisor startup; not full M1/run authorization.

The trusted bootstrap owner supplies approval and exclusive C1 context. Full
entry policy and facility evidence remain outside this component. Host/kernel
scheduling of initial Popen is not claimed bounded under host failure.
"""
from dataclasses import dataclass, field
import fcntl
import hashlib
import os
import re
import select
import signal
import socket
import stat
import subprocess
import threading
import time

from .bootstrap import (
    BootstrapError, BootstrapInput, BootstrapSession, HelperImage, SEALS,
    encode_bootstrap, sealed_bootstrap_fd,
)
from .child import _PidfdCapability
from .owner import _Original, _deadline, _pin
from .prbc import ProcessBoundaryOps
from .time import HostDeadline


class BootstrapLaunchError(BootstrapError):
    def __init__(self, code, owner):
        super().__init__(code)
        self.owner = owner  # original retained owner; never serialized as authority


@dataclass(frozen=True)
class BootstrapLaunchOutcome:
    birth_attempted: bool
    process_returned: bool
    registered: bool
    supervisor_reaped: bool | None
    registered_helpers_reaped: bool | None
    diagnostic: str | None
    cleanup_complete: bool = field(default=False, init=False)
    ready_for_execution: bool = field(default=False, init=False)


def _image(fd, digest, deadline):
    """Hash the actual sealed description without changing its file offset."""
    expected = _pin(digest)
    info = os.fstat(fd)
    if (not stat.S_ISREG(info.st_mode) or not 64 <= info.st_size <= 32*1024*1024
        or fcntl.fcntl(fd, fcntl.F_GET_SEALS) & SEALS != SEALS):
        raise BootstrapError('ML-BOOT-LAUNCH-IMAGE')
    hasher, offset = hashlib.sha256(), 0
    while offset < info.st_size:
        _deadline(deadline, deadline.session)
        data = os.pread(fd, min(16384, info.st_size-offset), offset)
        if not data or offset == 0 and data[:4] != b'\x7fELF':
            raise BootstrapError('ML-BOOT-LAUNCH-IMAGE')
        hasher.update(data); offset += len(data)
    after = os.fstat(fd)
    if ((after.st_dev, after.st_ino, after.st_size) != (info.st_dev, info.st_ino, info.st_size)
        or hasher.digest() != expected):
        raise BootstrapError('ML-BOOT-LAUNCH-IMAGE-PIN')


class OriginalBootstrapLauncher(_Original):
    """One original creation attempt, actual wait ownership and no implicit retry."""
    def __init__(self, config, supervisor_image, boundaries):
        if (type(config) is not BootstrapInput or config.version != 2
            or type(supervisor_image) is not HelperImage or type(boundaries) is not ProcessBoundaryOps):
            raise BootstrapError('ML-BOOT-LAUNCH-INPUT')
        boundaries._holder()
        self._retain()
        self.config, self.supervisor_image, self.boundaries = config, supervisor_image, boundaries
        self._pins = config, supervisor_image, boundaries, config.private_bytes
        self._image_pin = supervisor_image.descriptor, supervisor_image.digest, supervisor_image.argv0
        self._supervisor_fd = os.dup(supervisor_image.descriptor)
        self._fd_pin = self._supervisor_fd
        self._lock, self._drain_lock = threading.Lock(), threading.Lock()
        self._scope = self._session = self._process = self._channel = None
        self._pidfd = self._capability = self._failed_wait = None
        self._birth_attempted = self._process_returned = self._disposed = False
        self._diagnostic = None

    def _holder(self):
        super()._holder()
        if ((self.config, self.supervisor_image, self.boundaries) != self._pins[:3]
            or any(a is not b for a,b in zip((self.config,self.supervisor_image,self.boundaries),self._pins))
            or self.config.private_bytes != self._pins[3]
            or (self.supervisor_image.descriptor,self.supervisor_image.digest,self.supervisor_image.argv0) != self._image_pin
            or self._supervisor_fd != self._fd_pin):
            raise BootstrapError('ML-BOOT-LAUNCH-REPLACED')
        self.boundaries._holder()

    def _same_arguments(self, config, image, boundaries):
        return config is self._pins[0] and image is self._pins[1] and boundaries is self._pins[2]

    def _check(self, deadline):
        self._holder()
        if self._disposed:
            raise BootstrapError('ML-BOOT-LAUNCH-DISPOSED')
        until = _deadline(deadline, self.config.admission.generation.session)
        if until > int(self.config.admission.lease.monotonic_seconds*1e9):
            raise BootstrapError('ML-BOOT-LAUNCH-END')
        if self.boundaries._latch.cancelled:
            raise BootstrapError('ML-BOOT-LAUNCH-CANCELLED')

    @property
    def outcome(self):
        self._holder()
        drained = self._session._drained if self._session is not None else None
        return BootstrapLaunchOutcome(self._birth_attempted, self._process_returned, self._session is not None,
            bool(drained.supervisor_reaped) if drained else True if self._failed_wait is not None else None,
            bool(drained.registered_children_reaped) if drained else None, self._diagnostic)

    def launch(self, deadline):
        self._holder()
        if self._disposed:
            raise BootstrapError('ML-BOOT-LAUNCH-DISPOSED')
        if not self._lock.acquire(False):
            raise BootstrapError('ML-BOOT-LAUNCH-CONFLICT')
        private, peer = None, None
        try:
            if self._scope is not None:
                if deadline != self._scope:
                    raise BootstrapError('ML-BOOT-LAUNCH-REPEAT')
                if self._session is not None and self._diagnostic is None:
                    return self._session
                raise BootstrapLaunchError(self._diagnostic or 'ML-BOOT-LAUNCH-UNKNOWN', self)
            self._scope = deadline
            self._check(deadline)
            boot, manager = self.config.admission, self.boundaries
            if (boot.boundary_parent != manager._root_fd or boot.run_id != manager._admission.run_id
                or boot.approval_ref != manager._admission.bootstrap_approval_ref
                or boot.generation != manager._admission.teardown_deadline
                or self.supervisor_image.digest != boot.supervisor_artifact_digest
                or encode_bootstrap(boot) != self.config):
                raise BootstrapError('ML-BOOT-LAUNCH-CONTEXT')
            _image(self._supervisor_fd, boot.supervisor_artifact_digest, deadline)
            for image in (*boot.images, boot.authority_image):
                _image(image.descriptor, image.digest, deadline)
            self._check(deadline)
            private = sealed_bootstrap_fd(self.config)
            self._channel, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            self._channel.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
            self._check(deadline)
            self._birth_attempted = True
            self._process = subprocess.Popen(
                [self.supervisor_image.argv0, str(peer.fileno()), str(private)],
                executable='/proc/self/fd/'+str(self._supervisor_fd),
                pass_fds=tuple(dict.fromkeys((self._supervisor_fd, peer.fileno(), private,
                    manager._root_fd, *(i.descriptor for i in (*boot.images,boot.authority_image))))),
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            self._process_returned = True
            self._pidfd = os.pidfd_open(self._process.pid, 0)
            self._capability = _PidfdCapability(self._pidfd)
            self._check(deadline)
            self._session = BootstrapSession(self._process, self._channel, self.config,
                manager, manager._latch, deadline=deadline)
            self._check(deadline)
            return self._session
        except BaseException as error:
            code = str(error)
            self._diagnostic = code if re.fullmatch(r'ML-[A-Z0-9-]+', code) else 'ML-BOOT-LAUNCH-FAILED'
            if type(self._scope) is HostDeadline:
                end = min(self.config.admission.generation.monotonic_seconds,
                    self._scope.monotonic_seconds+2, time.monotonic()+2)
                try:
                    self.cancel('bootstrap-launch-failed')
                    if end > time.monotonic():
                        if self._session is not None:
                            self._session.drain(HostDeadline(self._scope.session,end))
                        else:
                            self._reap_failed(end)
                except (ValueError, OSError):
                    pass  # original state remains retained/unknown, never fabricated
            if isinstance(error, Exception):
                raise BootstrapLaunchError(self._diagnostic, self) from error
            raise
        finally:
            if peer is not None:
                peer.close()
            if private is not None:
                os.close(private)
            self._lock.release()

    def cancel(self, reason='bootstrap-launch-cancel'):
        self._holder()
        self.boundaries._latch.cancel(reason)  # independent of the startup lock
        if self._session is not None:
            self._session.cancel(reason)
        elif self._capability is not None and time.monotonic() < self.config.admission.generation.monotonic_seconds:
            try:
                signal.pidfd_send_signal(self._capability.fileno(), signal.SIGKILL)
            except ProcessLookupError:
                pass

    def _reap_failed(self, end):
        if self._capability is None:
            return  # no discovered PID/path fallback for a missing original pidfd
        while self._failed_wait is None:
            self._failed_wait = os.waitid(os.P_PIDFD,self._capability.fileno(),os.WEXITED|os.WNOHANG)
            if self._failed_wait is not None:
                observed = self._failed_wait
                self._process.returncode = observed.si_status if observed.si_code == os.CLD_EXITED else -observed.si_status
                return
            if time.monotonic() >= end:
                return
            select.select([self._capability.fileno()],[],[],min(.01,max(0,end-time.monotonic())))

    def drain(self, deadline):
        self._holder()
        if self._lock.locked() or not self._drain_lock.acquire(False):
            raise BootstrapError('ML-BOOT-LAUNCH-CONFLICT')
        try:
            end = _deadline(deadline,self.config.admission.generation.session)/1e9
            if end-time.monotonic() > 2 or end > self.config.admission.generation.monotonic_seconds:
                raise BootstrapError('ML-BOOT-LAUNCH-DRAIN-END')
            self.cancel()
            if self._session is not None:
                self._session.drain(deadline)  # original session is sole root wait consumer
            else:
                self._reap_failed(end)
            return self.outcome
        finally:
            self._drain_lock.release()

    def dispose(self):
        self._holder()
        if self._disposed:
            return
        if self._lock.locked() or not self._drain_lock.acquire(False):
            raise BootstrapError('ML-BOOT-LAUNCH-CONFLICT')
        try:
            if self._session is not None:
                drained = self._session._drained
                if not drained or not drained.supervisor_reaped or not drained.registered_children_reaped or self._session._pending:
                    raise BootstrapError('ML-BOOT-LAUNCH-RETAINED')
                for client in self._session._clients.values():
                    client.dispose()
                self._session.dispose()
            elif self._birth_attempted and self._failed_wait is None:
                raise BootstrapError('ML-BOOT-LAUNCH-RETAINED')
            elif self._channel is not None:
                self._channel.close()
            if self._process is not None:
                self._process.stderr.close()
            if self._capability is not None:
                self._capability.close()
            if self._pidfd is not None:
                os.close(self._pidfd)
            os.close(self._supervisor_fd)
            self._supervisor_fd = self._fd_pin = -1
            self._disposed = True
        finally:
            self._drain_lock.release()


class OriginalBootstrapRegistry(_Original):
    """Bounded original reservations; terminal IDs are never evicted/recreated."""
    def __init__(self, maximum_runs):
        if type(maximum_runs) is not int or not 1 <= maximum_runs <= 128:
            raise BootstrapError('ML-BOOT-REGISTRY-CAPACITY')
        self._retain()
        self._maximum = self._maximum_pin = maximum_runs
        self._entries = self._registry = {}
        self._log = ()
        self._lock = threading.Lock()

    def reserve(self, config, supervisor_image, boundaries):
        self._holder()
        if not self._lock.acquire(False):
            raise BootstrapError('ML-BOOT-REGISTRY-CONFLICT')
        try:
            if (self._entries is not self._registry or self._maximum != self._maximum_pin
                or tuple(self._entries.items()) != self._log):
                raise BootstrapError('ML-BOOT-REGISTRY-REPLACED')
            if type(config) is not BootstrapInput or encode_bootstrap(config.admission) != config:
                raise BootstrapError('ML-BOOT-LAUNCH-INPUT')
            key = config.admission.run_id
            if key in self._entries:
                original = self._entries[key]
                if not original._same_arguments(config, supervisor_image, boundaries):
                    raise BootstrapError('ML-BOOT-REGISTRY-REPEAT')
                return original
            if len(self._entries) >= self._maximum:
                raise BootstrapError('ML-BOOT-REGISTRY-FULL')
            owner = OriginalBootstrapLauncher(config,supervisor_image,boundaries)
            self._entries[key] = owner
            self._log = tuple(self._entries.items())
            return owner
        finally:
            self._lock.release()
