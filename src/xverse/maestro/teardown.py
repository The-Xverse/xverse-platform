"""Reverse owned unit teardown; full run/helper/evidence closure remains pending."""

from dataclasses import dataclass, field, replace
import math
import threading
import time
import uuid

from xverse_xdl.lifecycle import OwnedResourceHandle
from .owner import _Original, OwnerError
from .launcher import CatalogLauncher
from .lifecycle_evidence import _parents
from .providers import ProcessReadiness
from .time import HostDeadline


class TeardownError(OwnerError):
    pass


@dataclass(frozen=True)
class UnitTeardown:
    unit_id: str
    generation: int
    leader_reaped: bool
    boundary_empty: bool
    boundary_released: bool
    normal_records_complete: bool
    emergency: bool
    diagnostic: str | None

    @property
    def unit_cleanup_complete(self):
        return self.leader_reaped and self.boundary_empty and self.boundary_released


@dataclass(frozen=True)
class TeardownResult:
    run_id: str
    lifecycle_digest: str
    reason: str
    units: tuple[UnitTeardown, ...]
    starts_closed: bool
    lifecycle_complete: bool = field(default=False, init=False)
    ready_for_execution: bool = field(default=False, init=False)

    @property
    def unit_cleanup_complete(self):
        return bool(self.units) and all(u.unit_cleanup_complete for u in self.units)

    @property
    def normal_records_complete(self):
        return bool(self.units) and all(u.normal_records_complete for u in self.units)


@dataclass(frozen=True)
class _Step:
    step_id: str
    unit_id: str
    phase: str
    stage: str
    descriptor: object
    handle: OwnedResourceHandle
    observed_at: float
    leader_reaped: bool = False
    empty: bool = False
    released: bool = False
    force_observed: bool = False


class ReverseTeardown(_Original):
    def __init__(self, facade, *, per_unit_seconds=1):
        if type(facade) is not ProcessReadiness:
            raise TeardownError("ML-TEARDOWN-FACADE")
        facade._holder()
        try:
            valid = (
                type(per_unit_seconds) in (int, float)
                and math.isfinite(per_unit_seconds)
                and 0 < per_unit_seconds <= 5
            )
        except OverflowError:
            valid = False
        if not valid:
            raise TeardownError("ML-TEARDOWN-BUDGET")
        self._retain()
        self.facade = facade
        self.owner = facade._owner
        self.manager = self.owner.supervisor.boundaries
        self.session = self.owner.session
        self._registry = self.owner._launchers
        self._pins = (facade, self.owner, self.manager, self.session, self._registry)
        self._cap = per_unit_seconds
        self._lock = threading.Lock()
        self._active = None
        self._intents = {}
        self._receipts = {}
        self._known_reaps = set()
        self._stopped = {}
        self._stop_results = {}
        self._cleaned = {}
        self._result = None
        self._reason = None

    def _holder(self):
        super()._holder()
        if (
            self.facade is not self._pins[0]
            or self.owner is not self._pins[1]
            or self.manager is not self._pins[2]
            or self.session != self._pins[3]
            or self.owner._launchers is not self._pins[4]
        ):
            raise TeardownError("ML-TEARDOWN-REPLACED")
        self.facade._holder()
        self.manager._holder()

    def _deadline(self, deadline, *, cached=False):
        if type(deadline) is not HostDeadline or deadline.session != self.session:
            raise TeardownError("ML-TEARDOWN-SESSION")
        deadline.__post_init__()
        if not cached and (
            not 0 < deadline.monotonic_seconds - time.monotonic() <= 80
            or deadline.monotonic_seconds
            > self.manager._admission.teardown_deadline.monotonic_seconds
        ):
            raise TeardownError("ML-TEARDOWN-DEADLINE")
        return deadline.monotonic_seconds

    def _order(self):
        units = self.owner._prepared.units
        parents = {
            u.unit_id: set(_parents(self.owner._prepared, u.unit_id)) for u in units
        }
        result = []
        while parents:
            ready = sorted(
                (u for u in units if u.unit_id in parents and not parents[u.unit_id]),
                key=lambda u: (u.compiler_rank, u.unit_id),
            )
            if not ready:
                raise TeardownError("ML-TEARDOWN-GRAPH")
            unit = ready[0].unit_id
            result.append(unit)
            parents.pop(unit)
            for values in parents.values():
                values.discard(unit)
        return tuple(reversed(result))

    def _jobs(self, deadline):
        units = set(self._order())
        with self.manager._cleanup_lock(deadline):
            entries = {
                e.descriptor.unit_id: e.descriptor
                for e in self.manager._entries.values()
                if e.descriptor.unit_id in units
                and e.descriptor.generation == 1
                and e.fd >= 0
            }
        jobs = []
        for unit in self._order():
            if unit in self._cleaned:
                continue
            descriptor = entries.get(unit)
            launcher = self._registry.get(unit)
            handle = None
            if type(launcher) is CatalogLauncher:
                launcher._holder()
                if launcher.owner is not self.owner or launcher.recipe.unit_id != unit:
                    raise TeardownError("ML-TEARDOWN-ISSUER")
                if descriptor != launcher.recipe.descriptor:
                    raise TeardownError("ML-TEARDOWN-BOUNDARY")
                handle = launcher._handle
            if descriptor is not None:
                jobs.append((unit, descriptor, launcher, handle))
        return tuple(jobs)

    def _record(self, unit, phase, stage, descriptor, handle, deadline, **observed):
        step = _Step(
            "td-" + uuid.uuid4().hex,
            unit,
            phase,
            stage,
            descriptor,
            handle,
            time.monotonic(),
            **observed,
        )
        self._active = step
        receipt = self.owner.persistence.record_teardown(self, step, deadline)
        self._receipts[step.step_id] = receipt
        if stage == "intent":
            self._intents[unit, phase] = receipt
        return receipt

    def _stop(self, job, deadline):
        unit, descriptor, launcher, handle = job
        if unit in self._stop_results:
            return self._stop_results[unit]
        if (
            type(launcher) is not CatalogLauncher
            or type(handle) is not OwnedResourceHandle
        ):
            raise TeardownError("ML-TEARDOWN-NO-HANDLE")
        launcher.revalidate_issued(handle)
        self._record(unit, "stop", "intent", descriptor, handle, deadline)
        boundary = self.manager.terminate(descriptor, deadline=deadline)
        empty = (
            boundary.membership_complete
            and boundary.residual_count == 0
            and boundary.identity_retained
        )
        if not empty:
            raise TeardownError("ML-TEARDOWN-NOT-EMPTY")
        while True:
            observed = launcher.observe(handle, deadline)
            if observed.leader_reaped and not observed.leader_alive:
                break
            if time.monotonic() >= deadline.monotonic_seconds:
                raise TeardownError("ML-TEARDOWN-REAP-TIMEOUT")
            time.sleep(
                min(0.005, max(0, deadline.monotonic_seconds - time.monotonic()))
            )
        self._known_reaps.add(unit)
        self._record(
            unit,
            "stop",
            "outcome",
            descriptor,
            handle,
            deadline,
            leader_reaped=True,
            empty=True,
            force_observed=boundary.termination_observed,
        )
        self._stopped[unit] = boundary
        self.facade._released.discard(unit)
        self.facade._attempted.add(unit)
        if unit in self.facade._observations:
            self.facade._observations[unit] = replace(
                self.facade._observations[unit], ready=False
            )
        result = UnitTeardown(unit, 1, True, True, False, False, False, None)
        self._stop_results[unit] = result
        return result

    def _cleanup(self, job, deadline):
        unit, descriptor, launcher, handle = job
        if unit in self._cleaned:
            return self._cleaned[unit]
        if unit not in self._stopped:
            raise TeardownError("ML-TEARDOWN-NOT-STOPPED")
        launcher.revalidate_issued(handle)
        current = self.manager.record(descriptor, deadline=deadline)
        if current.state != "empty" or not current.identity_retained:
            raise TeardownError("ML-TEARDOWN-NOT-STOPPED")
        boundary = self._stopped[unit]
        self._record(unit, "cleanup", "intent", descriptor, handle, deadline)
        released = self.manager.release_empty(descriptor, deadline=deadline)
        if not released.boundary_released or released.residual_count != 0:
            raise TeardownError("ML-TEARDOWN-NOT-RELEASED")
        self._record(
            unit,
            "cleanup",
            "outcome",
            descriptor,
            handle,
            deadline,
            leader_reaped=True,
            empty=True,
            released=True,
            force_observed=boundary.termination_observed,
        )
        result = UnitTeardown(unit, 1, True, True, True, True, False, None)
        self._cleaned[unit] = result
        return result

    def _normal(self, job, deadline):
        self._stop(job, deadline)
        return self._cleanup(job, deadline)

    def phase(self, unit, phase, deadline):
        """One original scoped stop or cleanup; other units retain admission."""
        self._holder()
        self.owner._dispatch_access()
        if (
            type(unit) is not str
            or type(phase) is not str
            or phase not in ("stop", "cleanup")
        ):
            raise TeardownError("ML-TEARDOWN-PHASE")
        cache = self._stop_results if phase == "stop" else self._cleaned
        self._deadline(deadline, cached=unit in cache)
        if unit in cache:
            return cache[unit]
        if self._result is not None or self.owner._closed or self.owner.latch.cancelled:
            raise TeardownError("ML-TEARDOWN-CLOSED")
        if not self._lock.acquire(False):
            raise TeardownError("ML-TEARDOWN-CONFLICT")
        locks = []
        try:
            for lock in (self.facade._lock, self.owner._lock):
                if not lock.acquire(False):
                    raise TeardownError("ML-TEARDOWN-CONFLICT")
                locks.append(lock)
            jobs = self._jobs(deadline)
            job = next((j for j in jobs if j[0] == unit), None)
            if job is None:
                raise TeardownError("ML-TEARDOWN-NO-HANDLE")
            if phase == "stop" and any(
                unit in _parents(self.owner._prepared, other)
                and other not in self._cleaned
                for other in self.owner._claims
                if other != unit
            ):
                raise TeardownError("ML-TEARDOWN-DEPENDENTS")
            if phase == "cleanup" and unit not in self._stopped:
                raise TeardownError("ML-TEARDOWN-NOT-STOPPED")
            began = time.monotonic()
            end = min(deadline.monotonic_seconds, began + self._cap)
            normal_end = began + 0.6 * (end - began)
            try:
                return (self._stop if phase == "stop" else self._cleanup)(
                    job, HostDeadline(self.session, normal_end)
                )
            except (ValueError, OSError):
                return self._emergency(
                    job,
                    HostDeadline(self.session, end),
                    "ML-TEARDOWN-NORMAL-INCOMPLETE",
                )
        finally:
            self._active = None
            for lock in reversed(locks):
                lock.release()
            self._lock.release()

    def _emergency(self, job, deadline, diagnostic):
        unit, descriptor, launcher, handle = job
        self.owner.cancel("teardown-normal-incomplete")
        reaped = unit in self._known_reaps
        boundary = None
        for attempt in range(3):
            try:
                boundary = self.manager.force_cleanup(descriptor, deadline=deadline)
            except (ValueError, OSError):
                try:
                    boundary = self.manager.record(descriptor, deadline=deadline)
                except (ValueError, OSError):
                    boundary = None
            if (
                boundary is None
                or boundary.boundary_released
                or boundary.diagnostic != "ML-TEARDOWN-MEMBERSHIP-UNKNOWN"
            ):
                break
            if attempt < 2 and time.monotonic() < deadline.monotonic_seconds:
                time.sleep(
                    min(0.005, max(0, deadline.monotonic_seconds - time.monotonic()))
                )
        if type(launcher) is CatalogLauncher:
            try:
                drained = launcher.drain(deadline)
                reaped = reaped or drained.direct_child_reaped
            except (ValueError, OSError):
                pass
        empty = (
            boundary is not None
            and boundary.membership_complete
            and boundary.residual_count == 0
        )
        return UnitTeardown(
            unit,
            1,
            reaped,
            empty,
            boundary is not None and boundary.boundary_released,
            False,
            True,
            diagnostic,
        )

    def run(self, deadline, *, reason="normal-stop"):
        self._holder()
        self.owner._dispatch_access()
        if (
            type(reason) is not str
            or not 0 < len(reason) <= 128
            or any(ord(c) < 32 or ord(c) > 126 for c in reason)
        ):
            raise TeardownError("ML-TEARDOWN-REASON")
        self._deadline(deadline, cached=self._result is not None)
        if self._result is not None:
            if reason != self._reason:
                raise TeardownError("ML-TEARDOWN-REPEAT")
            return self._result
        if not self._lock.acquire(False):
            raise TeardownError("ML-TEARDOWN-CONFLICT")
        locks = []
        try:
            for lock in (self.facade._lock, self.owner._lock):
                if not lock.acquire(False):
                    raise TeardownError("ML-TEARDOWN-CONFLICT")
                locks.append(lock)
            jobs = self._jobs(deadline)
            end = min(
                deadline.monotonic_seconds, time.monotonic() + len(jobs) * self._cap
            )
            self.owner._closed = True
            for unit, value in tuple(self.facade._observations.items()):
                self.facade._observations[unit] = replace(value, ready=False)
            results = list(self._cleaned.values())
            for job in jobs:
                began = time.monotonic()
                unit_end = min(end, began + self._cap)
                normal_end = began + 0.6 * (unit_end - began)
                try:
                    if self.owner.latch.cancelled:
                        raise TeardownError("ML-TEARDOWN-CANCELLED")
                    results.append(
                        self._normal(job, HostDeadline(self.session, normal_end))
                    )
                except (ValueError, OSError):
                    results.append(
                        self._emergency(
                            job,
                            HostDeadline(self.session, unit_end),
                            "ML-TEARDOWN-NORMAL-INCOMPLETE",
                        )
                    )
                finally:
                    self._active = None
            self.owner.cancel("teardown-complete")
            self._reason = reason
            self._result = TeardownResult(
                self.owner._run_id,
                self.owner._prepared.lifecycle_digest,
                reason,
                tuple(sorted(results, key=lambda u: self._order().index(u.unit_id))),
                True,
            )
            return self._result
        finally:
            for lock in reversed(locks):
                lock.release()
            self._lock.release()

    def cancel(self, reason="teardown-cancel"):
        super()._holder()
        self._pins[1].cancel(reason)
