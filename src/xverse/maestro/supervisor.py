"""Linux direct-child monitoring; no launch, containment or lifecycle authority.

The trusted original parent supplies its actual Popen before dispatching work. It
must retain exclusive wait ownership. This component bounds only monitoring after
registration, not spawn/registration, descendants, or an arbitrary kernel stall.
"""

from dataclasses import dataclass, field
import math
import os
import select
import signal
import subprocess
import threading
import time
import uuid


class SupervisionError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _seconds(value: object, maximum: float) -> None:
    try:
        valid = (
            type(value) in (int, float)
            and math.isfinite(value)
            and 0 < value <= maximum
        )
    except OverflowError:
        valid = False
    if not valid:
        raise SupervisionError("ML-ADMISSION-WATCH-LIMIT")


@dataclass(frozen=True)
class WatchLimits:
    operation_seconds: float
    term_seconds: float
    kill_seconds: float
    poll_seconds: float

    def __post_init__(self) -> None:
        for value in (self.operation_seconds, self.term_seconds, self.kill_seconds):
            _seconds(value, 5)
        _seconds(self.poll_seconds, 0.05)


class CancellationLatch:
    """One original-process close latch, independent of any coordinator run lock."""

    def __init__(self) -> None:
        self._original = self
        self._pid = os.getpid()
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._reason: str | None = None

    def _check(self) -> None:
        if self._original is not self or self._pid != os.getpid():
            raise SupervisionError("ML-OWNERSHIP-LATCH")

    @property
    def cancelled(self) -> bool:
        self._check()
        return self._event.is_set()

    @property
    def epoch(self) -> int:
        return int(self.cancelled)

    @property
    def reason(self) -> str | None:
        self._check()
        return self._reason

    def cancel(self, reason: str) -> int:
        self._check()
        if (
            type(reason) is not str
            or not reason
            or len(reason) > 64
            or any(not (c.isascii() and (c.isalnum() or c in "-_")) for c in reason)
        ):
            raise SupervisionError("ML-ADMISSION-CANCEL-REASON")
        with self._lock:
            if not self._event.is_set():
                self._reason = reason
                self._event.set()
        return 1


@dataclass(frozen=True)
class WorkerObservation:
    worker_ref: str
    host_session: str
    disposition: str
    returncode: int | None
    worker_reaped: bool
    identity_retained: bool
    cancel_epoch: int
    signals_sent: tuple[str, ...]
    retained_at: float
    observed_at: float
    diagnostic: str | None
    cleanup_complete: bool = field(default=False, init=False)
    ready_for_execution: bool = field(default=False, init=False)


@dataclass
class _Worker:
    process: subprocess.Popen
    descriptor: int
    limits: WatchLimits
    retained_at: float
    operation_deadline: float
    term_deadline: float
    final_deadline: float
    watch_lock: threading.Lock = field(default_factory=threading.Lock)
    result: WorkerObservation | None = None


class WorkerMonitor:
    """Original-holder registry for exact owned direct children, not a run facade.

    Holding a reference or copying this object never reconstructs a registry. The
    original trusted holder must supply genuine children; this is not an approval
    authenticator or a security boundary against code within that holder process.
    """

    def __init__(self, latch: CancellationLatch) -> None:
        if type(latch) is not CancellationLatch:
            raise SupervisionError("ML-ADMISSION-LATCH")
        latch._check()
        if not all(
            (
                hasattr(os, "pidfd_open"),
                hasattr(os, "P_PIDFD"),
                hasattr(signal, "pidfd_send_signal"),
                hasattr(os, "waitid"),
            )
        ):
            raise SupervisionError("ML-ADMISSION-PIDFD-UNSUPPORTED")
        self._original = self
        self._pid = os.getpid()
        self._session = uuid.uuid4().hex
        self._latch = latch
        self._workers: dict[str, _Worker] = {}
        self._registry_lock = threading.Lock()

    @property
    def latch(self) -> CancellationLatch:
        self._check()
        return self._latch

    @property
    def ready_for_execution(self) -> bool:
        return False

    def _check(self) -> None:
        if self._original is not self or self._pid != os.getpid():
            raise SupervisionError("ML-OWNERSHIP-WORKER-HOLDER")
        self._latch._check()

    def _worker(self, worker_ref: str) -> _Worker:
        self._check()
        if type(worker_ref) is not str or worker_ref not in self._workers:
            raise SupervisionError("ML-OWNERSHIP-WORKER-UNKNOWN")
        return self._workers[worker_ref]

    def retain(self, process: subprocess.Popen, limits: WatchLimits) -> str:
        """Retain the trusted original parent's actual child before dispatch.

        No process is created, adopted from metadata or signalled by this method.
        Spawning and this registration require separate outer supervision.
        """
        self._check()
        if type(process) is not subprocess.Popen or type(limits) is not WatchLimits:
            raise SupervisionError("ML-ADMISSION-WORKER-INPUT")
        if (
            type(getattr(process, "pid", None)) is not int
            or process.pid <= 0
            or getattr(process, "returncode", 1) is not None
        ):
            raise SupervisionError("ML-OWNERSHIP-WORKER-INPUT")
        # Reconstruct instead of retaining mutable caller ownership of the object.
        limits = WatchLimits(
            limits.operation_seconds,
            limits.term_seconds,
            limits.kill_seconds,
            limits.poll_seconds,
        )
        with self._registry_lock:
            if self._latch.cancelled:
                raise SupervisionError("ML-CANCELLED-WORKER-REGISTRATION")
            if len(self._workers) >= 128 or any(
                w.process is process for w in self._workers.values()
            ):
                raise SupervisionError("ML-CONFLICT-WORKER-REGISTRATION")
            retained_at = time.monotonic()
            descriptor = -1
            try:
                descriptor = os.pidfd_open(process.pid, 0)
                # WNOWAIT verifies original parent wait ownership without reaping.
                os.waitid(os.P_PIDFD, descriptor, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                if self._latch.cancelled:
                    raise SupervisionError("ML-CANCELLED-WORKER-REGISTRATION")
                ref = uuid.uuid4().hex
                operation = retained_at + limits.operation_seconds
                term = operation + limits.term_seconds
                self._workers[ref] = _Worker(
                    process,
                    descriptor,
                    limits,
                    retained_at,
                    operation,
                    term,
                    term + limits.kill_seconds,
                )
                return ref
            except OSError as exc:
                self._latch.cancel("worker-registration-failed")
                raise SupervisionError("ML-OWNERSHIP-WORKER-REGISTER") from exc
            finally:
                if descriptor >= 0 and not any(
                    w.descriptor == descriptor for w in self._workers.values()
                ):
                    os.close(descriptor)

    def watch(self, worker_ref: str) -> WorkerObservation:
        """Observe and boundedly terminate one registered worker; never call it."""
        worker = self._worker(worker_ref)
        if not worker.watch_lock.acquire(blocking=False):
            raise SupervisionError("ML-CONFLICT-WORKER-WATCH")
        try:
            if worker.result is not None:
                return worker.result
            return self._watch(worker_ref, worker)
        finally:
            worker.watch_lock.release()

    def _watch(self, ref: str, worker: _Worker) -> WorkerObservation:
        disposition = "exited"
        sent: list[str] = []
        term_deadline = worker.term_deadline
        final_deadline = worker.final_deadline
        while True:
            now = time.monotonic()
            if disposition == "exited":
                # This short lock is never held by provider/storage/tick work.
                with self._latch._lock:
                    if self._latch._event.is_set():
                        disposition = "cancelled"
                    elif now >= worker.operation_deadline:
                        self._latch._reason = "worker-timeout"
                        self._latch._event.set()
                        disposition = "timed-out"
                if disposition != "exited":
                    # Early cancellation shortens, never extends original bounds.
                    term_deadline = min(term_deadline, now + worker.limits.term_seconds)
                    final_deadline = min(
                        final_deadline, term_deadline + worker.limits.kill_seconds
                    )
            try:
                exited = os.waitid(
                    os.P_PIDFD, worker.descriptor, os.WEXITED | os.WNOHANG | os.WNOWAIT
                )
            except OSError:
                return self._finish(
                    ref, worker, "unresolved", None, False, sent, "ML-OWNERSHIP-WAIT"
                )
            if exited is not None:
                try:
                    reaped = os.waitid(
                        os.P_PIDFD, worker.descriptor, os.WEXITED | os.WNOHANG
                    )
                    if reaped is None:
                        raise ChildProcessError()
                except OSError:
                    return self._finish(
                        ref,
                        worker,
                        "unresolved",
                        None,
                        False,
                        sent,
                        "ML-OWNERSHIP-WAIT",
                    )
                code = (
                    reaped.si_status
                    if reaped.si_code == os.CLD_EXITED
                    else -reaped.si_status
                )
                worker.process.returncode = code
                # Recheck cancellation/deadline at observation commitment.
                with self._latch._lock:
                    if disposition == "exited":
                        if self._latch._event.is_set():
                            disposition = "cancelled"
                        elif time.monotonic() >= worker.operation_deadline:
                            self._latch._reason = "worker-timeout"
                            self._latch._event.set()
                            disposition = "timed-out"
                    result = self._finish(
                        ref, worker, disposition, code, True, sent, None
                    )
                return result
            if disposition != "exited":
                # The observer may have been descheduled since the loop sample.
                now = time.monotonic()
                if now >= final_deadline:
                    return self._finish(
                        ref,
                        worker,
                        "unresolved",
                        None,
                        False,
                        sent,
                        "ML-TIMEOUT-WORKER-REAP",
                    )
                sig = None
                if now >= term_deadline and "KILL" not in sent:
                    sig = signal.SIGKILL
                elif not sent:
                    sig = signal.SIGTERM
                if sig is not None:
                    try:
                        if time.monotonic() >= final_deadline:
                            return self._finish(
                                ref,
                                worker,
                                "unresolved",
                                None,
                                False,
                                sent,
                                "ML-TIMEOUT-WORKER-REAP",
                            )
                        signal.pidfd_send_signal(worker.descriptor, sig)
                        sent.append("TERM" if sig == signal.SIGTERM else "KILL")
                    except OSError:
                        return self._finish(
                            ref,
                            worker,
                            "unresolved",
                            None,
                            False,
                            sent,
                            "ML-OWNERSHIP-SIGNAL",
                        )
                next_deadline = term_deadline if "KILL" not in sent else final_deadline
            else:
                next_deadline = worker.operation_deadline
            try:
                select.select(
                    [worker.descriptor],
                    [],
                    [],
                    max(
                        0,
                        min(
                            worker.limits.poll_seconds, next_deadline - time.monotonic()
                        ),
                    ),
                )
            except (OSError, ValueError):
                return self._finish(
                    ref, worker, "unresolved", None, False, sent, "ML-OWNERSHIP-OBSERVE"
                )

    def _finish(
        self,
        ref: str,
        worker: _Worker,
        disposition: str,
        code: int | None,
        reaped: bool,
        sent: list[str],
        diagnostic: str | None,
    ) -> WorkerObservation:
        if disposition == "unresolved":
            self._latch.cancel("worker-unresolved")
        if reaped:
            os.close(worker.descriptor)
            worker.descriptor = -1
        result = WorkerObservation(
            ref,
            self._session,
            disposition,
            code,
            reaped,
            worker.descriptor >= 0,
            self._latch.epoch,
            tuple(sent),
            worker.retained_at,
            time.monotonic(),
            diagnostic,
        )
        worker.result = result
        return result

    def dispose_reaped(self, worker_ref: str) -> None:
        """Close an unresolved child identity only after exact termination evidence.

        The cached uncertainty remains unchanged. This never certifies containment
        release or turns a stolen wait record into an original reaping observation.
        """
        worker = self._worker(worker_ref)
        if not worker.watch_lock.acquire(blocking=False):
            raise SupervisionError("ML-CONFLICT-WORKER-WATCH")
        try:
            if worker.descriptor < 0:
                return
            if (
                worker.result is None
                or not select.select([worker.descriptor], [], [], 0)[0]
            ):
                raise SupervisionError("ML-OWNERSHIP-WORKER-LIVE")
            try:
                reaped = os.waitid(
                    os.P_PIDFD, worker.descriptor, os.WEXITED | os.WNOHANG
                )
                if reaped is None:
                    raise SupervisionError("ML-OWNERSHIP-WORKER-LIVE")
                worker.process.returncode = (
                    reaped.si_status
                    if reaped.si_code == os.CLD_EXITED
                    else -reaped.si_status
                )
            except ChildProcessError:
                # Retained pidfd proves exact exit; another waiter consumed status.
                # Keep the cached original observation unresolved.
                pass
            except OSError as exc:
                raise SupervisionError("ML-OWNERSHIP-WORKER-DISPOSE") from exc
            os.close(worker.descriptor)
            worker.descriptor = -1
        finally:
            worker.watch_lock.release()
