"""Current-generation process probes and dependent Release (partial U4/U5).

Only the catalog's explicit ``running`` condition is admitted. This is sampled
process existence after exec, never application readiness or full run admission.
"""

from dataclasses import dataclass, field, replace, asdict
import math
import select
import threading
import time

from xverse_xdl.lifecycle import OwnedResourceHandle

from .launcher import CatalogLauncher, ProcessObservation
from .owner import _Original, _hash, OwnerError, ReleaseOwner
from .prbc import BoundaryDescriptor
from .time import HostDeadline


class ReadinessError(OwnerError):
    pass


def _positive(value):
    try:
        valid = type(value) in (int, float) and math.isfinite(value) and 0 < value <= 5
    except OverflowError:
        valid = False
    if not valid:
        raise ReadinessError("ML-PROBE-BOUND")


@dataclass(frozen=True)
class ProbePolicy:
    unit_id: str
    freshness_seconds: float
    cadence_seconds: float
    timeout_seconds: float
    attempts: int = 3

    def __post_init__(self):
        if type(self.unit_id) is not str or not self.unit_id:
            raise ReadinessError("ML-PROBE-UNIT")
        for value in (
            self.freshness_seconds,
            self.cadence_seconds,
            self.timeout_seconds,
        ):
            _positive(value)
        if (
            self.cadence_seconds > self.freshness_seconds
            or type(self.attempts) is not int
            or not 1 <= self.attempts <= 3
        ):
            raise ReadinessError("ML-PROBE-BOUND")


@dataclass(frozen=True)
class ReadinessObservation:
    unit_id: str
    generation: int
    handle_digest: str
    probe_id: str
    action_id: str
    host_session: str
    observed_at: float
    sequence: int
    ready: bool
    ready_for_execution: bool = field(default=False, init=False)


@dataclass(frozen=True)
class _Binding:
    launcher: CatalogLauncher
    handle: OwnedResourceHandle


@dataclass(frozen=True)
class _ProbeFailure:
    unit_id: str
    host_session: str
    observed_at: float


_CREATE = object()


class DependencyGuard(_Original):
    """One active facade operation; observations supplied by callers are rejected."""

    def __init__(self, key, coordinator, unit_id, deadline):
        if key is not _CREATE:
            raise ReadinessError("ML-PROBE-GUARD")
        self._retain()
        self._coordinator, self._unit_id, self._deadline = (
            coordinator,
            unit_id,
            deadline,
        )

    def _validate(self, owner, unit_id, deadline):
        """Validate original operation identity without taking a new sample."""
        self._holder()
        coordinator = self._coordinator
        coordinator._holder()
        if (
            coordinator._guard is not self
            or owner is not coordinator._owner
            or unit_id != self._unit_id
            or deadline != self._deadline
        ):
            raise ReadinessError("ML-PROBE-GUARD")
        return coordinator

    def check(self, owner, unit_id, deadline):
        coordinator = self._validate(owner, unit_id, deadline)
        coordinator._check_prerequisites(unit_id, deadline)


class ProcessReadiness(_Original):
    """Compose already admitted/staged original resources; no new start authority.

    Calling start performs one Release and bounded declared running probes. Normal
    M3 outcomes, automatic cadence scheduling and reverse teardown are downstream.
    The original caller retains all C1 cleanup capabilities on every failure.
    """

    ready_for_execution = False

    def __init__(self, owner, *, policies, _cleanup_recovery=None):
        if type(owner) is not ReleaseOwner or type(policies) is not tuple:
            raise ReadinessError("ML-PROBE-INPUT")
        owner._holder()
        from .persistence import PersistenceClient

        if type(owner.persistence) is not PersistenceClient:
            raise ReadinessError("ML-PROBE-PERSISTENCE")
        if _cleanup_recovery is None:
            owner.persistence._available()
        else:
            from .recovery import IssuerRecovery
            if type(_cleanup_recovery) is not IssuerRecovery:
                raise ReadinessError('ML-PROBE-CLEANUP-CAPABILITY')
            _Original._holder(_cleanup_recovery)
            if (_cleanup_recovery.owner is not owner or not owner.latch.cancelled
                or _cleanup_recovery._coordinator is None or _cleanup_recovery._view is not None
                or _cleanup_recovery._scope is None or _cleanup_recovery._retired_view_epoch is None
                or _cleanup_recovery._retired_view_epoch != owner._view_epoch
                or _cleanup_recovery.controller._recovery is not _cleanup_recovery):
                raise ReadinessError('ML-PROBE-CLEANUP-CAPABILITY')
            _cleanup_recovery._coordinator._validate_controller_borrow(
                _cleanup_recovery.controller, _cleanup_recovery._request)
            owner.persistence._holder()
        prepared = owner._prepared
        units = prepared.units
        if any(type(p) is not ProbePolicy for p in policies):
            raise ReadinessError("ML-PROBE-POLICY")
        for policy in policies:
            policy.__post_init__()
        if len(policies) != len(units) or {p.unit_id for p in policies} != {
            u.unit_id for u in units
        }:
            raise ReadinessError("ML-PROBE-POLICY-SET")
        if owner.persistence.coverage is not None:
            admission = owner.persistence.coverage
            expected = {u['unitId']: (u['cadence'], u['freshness']) for u in admission.data(owner.persistence.coverage_digest)['units']}
            if any((p.cadence_seconds, p.freshness_seconds) != expected.get(p.unit_id) for p in policies):
                raise ReadinessError("ML-COVERAGE-RUNTIME-POLICY")
        for unit in units:
            actions = [a for a in unit.plan.actions if a.phase == "observe"]
            if (
                unit.provider.kind != "process"
                or len(actions) != 1
                or actions[0].condition != "running"
            ):
                raise ReadinessError("ML-PROBE-UNSUPPORTED")
        self._retain()
        self._cleanup_only = _cleanup_recovery is not None
        self._cleanup_source = _cleanup_recovery
        self._cleanup_pin = self._cleanup_only, _cleanup_recovery
        self._owner, self._prepared = owner, prepared
        self._pins = owner, prepared, owner.session
        self._policies = {p.unit_id: p for p in policies}
        self._policy_pin = tuple(policies)
        reverse = {}
        for edge in prepared.graph_edges:
            reverse.setdefault(edge.target, set()).add(edge.source)
        prerequisites = {}
        for unit in units:
            seen, todo = set(), [(unit.unit_id, "dispatch")]
            while todo:
                node = todo.pop()
                if node in seen:
                    continue
                seen.add(node)
                todo.extend(reverse.get(node, ()))
            prerequisites[unit.unit_id] = tuple(
                u.unit_id
                for u in units
                if u.unit_id != unit.unit_id and (u.unit_id, "ready") in seen
            )
        self._prerequisites = prerequisites
        self._prerequisite_pin = tuple(prerequisites.items())
        self._bindings, self._observations = {}, {}
        self._registry_pins = self._bindings, self._observations
        self._released, self._attempted = set(), set()
        self._state_pins = self._released, self._attempted
        self._suspended, self._terminated = set(), {}  # Phase 5: frozen units; units killed by a fault
        self._sequence, self._guard = 0, None
        self._probe_failure = None
        self._lock = threading.Lock()
        self._view_epoch = owner._view_epoch
        owner._register_view(self)

    def _holder(self):
        super()._holder()
        owner, prepared, session = self._pins
        if (
            self._owner is not owner
            or self._prepared is not prepared
            or owner._prepared is not prepared
            or owner.session != session
            or self._bindings is not self._registry_pins[0]
            or self._observations is not self._registry_pins[1]
            or self._released is not self._state_pins[0]
            or self._attempted is not self._state_pins[1]
            or tuple(self._policies.values()) != self._policy_pin
            or tuple(self._prerequisites.items()) != self._prerequisite_pin
            or (self._cleanup_only, self._cleanup_source) != self._cleanup_pin
        ):
            raise ReadinessError("ML-PROBE-REPLACED")
        owner._holder()
        owner._view_registry()
        if (
            self._view_epoch != owner._view_epoch
            or owner._views.get(id(self)) is not self
        ):
            raise ReadinessError("ML-PROBE-STALE-VIEW")
        owner.latch._check()

    def _check(self, deadline):
        self._holder()
        if self._cleanup_only:
            raise ReadinessError('ML-PROBE-CLEANUP-ONLY')
        return self._owner._check(deadline)

    def _bound(self, unit_id):
        binding = self._bindings.get(unit_id)
        if (
            type(binding) is not _Binding
            or self._owner._launchers.get(unit_id) is not binding.launcher
            or binding.launcher.owner is not self._owner
            or binding.launcher.unit_id != unit_id
        ):
            raise ReadinessError("ML-PROBE-ISSUER")
        binding.launcher._issued(binding.handle)
        return binding

    def bind(self, launcher, handle):
        from .run_broker import RunUnitIssuer

        self._holder()
        if self._cleanup_only:
            raise ReadinessError('ML-PROBE-CLEANUP-ONLY')
        self._owner._dispatch_access()
        if (
            type(launcher) not in (CatalogLauncher, RunUnitIssuer)
            or type(handle) is not OwnedResourceHandle
        ):
            raise ReadinessError("ML-PROBE-BINDING")
        if not self._lock.acquire(blocking=False):
            raise ReadinessError("ML-PROBE-CONFLICT")
        try:
            launcher._issued(handle)
            unit = launcher.unit_id
            if (
                launcher.owner is not self._owner
                or self._owner._launchers.get(unit) is not launcher
                or unit not in self._policies
                or unit in self._bindings
                or type(launcher) is CatalogLauncher
                and launcher.recipe.descriptor.generation != 1
            ):
                raise ReadinessError("ML-PROBE-BINDING")
            self._bindings[unit] = _Binding(launcher, handle)
        finally:
            self._lock.release()

    def _query(self, unit_id, deadline):
        try:
            return self._query_original(unit_id, deadline)
        except Exception:
            if unit_id in self._policies:
                self._probe_failure = _ProbeFailure(
                    unit_id, self._pins[2], time.monotonic()
                )
            raise

    def _query_original(self, unit_id, deadline):
        until = self._check(deadline)
        if unit_id not in self._released:
            raise ReadinessError("ML-PROBE-UNRELEASED")
        binding = self._bound(unit_id)
        policy = self._policies[unit_id]
        action = next(
            a for a in self._owner._unit(unit_id).plan.actions if a.phase == "observe"
        )
        began = time.monotonic()
        limit = min(
            until / 1e9, began + policy.timeout_seconds, began + action.timeout_seconds
        )
        observed = binding.launcher.observe(
            binding.handle, HostDeadline(self._pins[2], limit)
        )
        self._check(deadline)
        self._bound(unit_id)
        now = time.monotonic()
        if (
            type(observed) is not ProcessObservation
            or observed.handle != binding.handle
            or observed.host_session != self._pins[2]
            or type(observed.observed_at) not in (int, float)
            or not math.isfinite(observed.observed_at)
            or not began <= observed.observed_at <= now
            or now > limit
            or now - observed.observed_at > policy.freshness_seconds
        ):
            raise ReadinessError("ML-PROBE-OBSERVATION")
        self._sequence += 1
        value = ReadinessObservation(
            unit_id,
            binding.launcher.recipe.descriptor.generation,
            _hash(asdict(binding.handle)).hex(),
            "running",
            action.action_id,
            self._pins[2],
            observed.observed_at,
            self._sequence,
            bool(observed.running),
        )
        self._observations[unit_id] = value
        self._owner.persistence.record_probe(self, value, deadline)
        self._check(deadline)
        return value

    def _fresh(self, unit_id):
        binding = self._bound(unit_id)
        value = self._observations.get(unit_id)
        if (
            value is None
            or not value.ready
            or value.host_session != self._pins[2]
            or value.generation != binding.launcher.recipe.descriptor.generation
            or value.handle_digest != _hash(asdict(binding.handle)).hex()
            or not 0
            <= time.monotonic() - value.observed_at
            <= self._policies[unit_id].freshness_seconds
        ):
            raise ReadinessError("ML-PROBE-NOT-FRESH")
        return value

    def _check_prerequisites(self, unit_id, deadline):
        self._check(deadline)
        prerequisites = self._prerequisites[unit_id]
        for prerequisite in prerequisites:
            if not self._query(prerequisite, deadline).ready:
                raise ReadinessError("ML-PROBE-DEPENDENCY")
        # Check the complete set after the final RPC, including earlier replies.
        for prerequisite in prerequisites:
            self._fresh(prerequisite)
        self._check(deadline)

    def start(self, unit_id, descriptor, gate, deadline):
        self._holder()
        self._owner._start_access()
        self._check(deadline)
        if not self._lock.acquire(blocking=False):
            raise ReadinessError("ML-PROBE-CONFLICT")
        try:
            self._probe_failure = None
            if unit_id not in self._policies or unit_id in self._attempted:
                raise ReadinessError("ML-PROBE-START")
            binding = self._bound(unit_id)
            if (
                type(descriptor) is not BoundaryDescriptor
                or descriptor != binding.launcher.recipe.descriptor
            ):
                raise ReadinessError("ML-PROBE-BOUNDARY")
            self._attempted.add(unit_id)
            # Native prerequisites are observed by the mandatory original broker
            # guard after ARM, immediately before RELEASE. Keep early live checks
            # for unrelated units; legacy release retains the full preflight.
            from .run_broker import RunUnitIssuer
            final_parents = self._prerequisites[unit_id] if type(binding.launcher) is RunUnitIssuer else ()
            for active in self._prepared.resource_order:
                if (active in self._released and active not in final_parents
                    and not self._query(active, deadline).ready):
                    raise ReadinessError("ML-PROBE-HEALTH")
            self._guard = DependencyGuard(_CREATE, self, unit_id, deadline)
            self._owner.release(
                unit_id, descriptor, gate, deadline, readiness_guard=self._guard
            )
            self._released.add(unit_id)
            for attempt in range(self._policies[unit_id].attempts):
                value = self._query(unit_id, deadline)
                if value.ready:
                    return self._fresh(unit_id)
                if attempt + 1 < self._policies[unit_id].attempts:
                    # Finite local yield; no sleep extends the original deadline.
                    select.select(
                        [],
                        [],
                        [],
                        min(
                            0.005, max(0, deadline.monotonic_seconds - time.monotonic())
                        ),
                    )
            raise ReadinessError("ML-PROBE-NOT-READY")
        except Exception:
            self.cancel("readiness-start-failed")
            raise
        finally:
            self._guard = None
            self._lock.release()

    def suspend_health(self, unit_id):
        """Phase 5: a frozen unit is not probed until resumed; its prior observation stands."""
        if type(unit_id) is not str or unit_id not in self._policies:
            raise ReadinessError("ML-PROBE-UNIT")
        self._suspended.add(unit_id)

    def resume_health(self, unit_id):
        """Phase 5: resume probing after a thaw."""
        self._suspended.discard(unit_id)

    def terminate_by_fault(self, unit_id, entry_id):
        """Phase 5: record the intended termination before a kill, so the death is attributed."""
        if type(unit_id) is not str or unit_id not in self._policies:
            raise ReadinessError("ML-PROBE-UNIT")
        self._terminated[unit_id] = entry_id

    def check_unit_health(self, unit_id, deadline):
        """Observe only the exact declared unit under its original operation end."""
        self._check(deadline)
        if type(unit_id) is not str or unit_id not in self._policies:
            raise ReadinessError("ML-PROBE-UNIT")
        if unit_id not in self._released:
            raise ReadinessError("ML-PROBE-UNRELEASED")
        if unit_id in self._terminated:
            self.cancel("terminated-by-fault")
            raise ReadinessError("ML-PROBE-TERMINATED-BY-FAULT")
        if unit_id in self._suspended and unit_id in self._observations:
            return self._observations[unit_id]
        if not self._lock.acquire(blocking=False):
            raise ReadinessError("ML-PROBE-CONFLICT")
        try:
            self._probe_failure = None
            if not self._query(unit_id, deadline).ready:
                raise ReadinessError("ML-PROBE-HEALTH")
            return self._fresh(unit_id)
        except Exception:
            self.cancel("readiness-health-failed")
            raise
        finally:
            self._lock.release()

    def check_health(self, deadline, *, force=False):
        self._check(deadline)
        if type(force) is not bool:
            raise ReadinessError("ML-PROBE-INPUT")
        if not self._lock.acquire(blocking=False):
            raise ReadinessError("ML-PROBE-CONFLICT")
        try:
            self._probe_failure = None
            values = []
            for unit_id in self._prepared.resource_order:
                if unit_id not in self._released:
                    continue
                if unit_id in self._terminated:
                    raise ReadinessError("ML-PROBE-TERMINATED-BY-FAULT")
                if unit_id in self._suspended:
                    continue
                prior = self._observations.get(unit_id)
                if (
                    force
                    or prior is None
                    or time.monotonic() - prior.observed_at
                    >= self._policies[unit_id].cadence_seconds
                ):
                    if not self._query(unit_id, deadline).ready:
                        raise ReadinessError("ML-PROBE-HEALTH")
                values.append(self._fresh(unit_id))
            return tuple(values)
        except Exception:
            self.cancel("readiness-health-failed")
            raise
        finally:
            self._lock.release()

    @property
    def next_health_deadline(self):
        self._holder()
        if self._owner.latch.cancelled or not self._released:
            return None
        deadlines = tuple(
            value.observed_at + self._policies[unit].cadence_seconds
            for unit, value in self._observations.items()
            if unit in self._released and unit not in self._suspended
        )
        if not deadlines:
            return None
        return HostDeadline(
            self._pins[2],
            min(deadlines),
        )

    def observation(self, unit_id):
        self._holder()
        value = self._observations.get(unit_id)
        return (
            replace(value, ready=False)
            if value is not None and self._owner.latch.cancelled
            else value
        )

    @property
    def observations(self):
        self._holder()
        return tuple(
            self.observation(u.unit_id)
            for u in self._prepared.units
            if u.unit_id in self._observations
        )

    def cancel(self, reason="readiness-cancel"):
        # Cancellation must not wait for the normal operation lock.
        super()._holder()
        self._pins[0].cancel(reason)
        for unit, value in tuple(self._registry_pins[1].items()):
            self._registry_pins[1][unit] = replace(value, ready=False)
