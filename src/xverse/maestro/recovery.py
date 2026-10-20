"""Reconstruct an observation/cleanup view inside the surviving original supervisor."""

from dataclasses import asdict, dataclass, field
import math
import re
import threading
import time
import uuid

from xverse.argus.schema import canonical_bytes
from .bootstrap import BootstrapSession
from .launcher import CatalogLauncher, ProcessObservation
from .run_broker import RunUnitIssuer
from .lifecycle_evidence import _digest
from .owner import _Original, ReleaseOwner, OwnerError
from .providers import ProcessReadiness, ProbePolicy, _Binding
from .run_closure import RunClosure, RunClosureResult
from .time import HostDeadline


class RecoveryError(OwnerError):
    pass


@dataclass(frozen=True)
class _RecoveryStatement:
    body: bytes = field(repr=False)


@dataclass(frozen=True)
class RecoverySource:
    sequence: int
    sha256: str


@dataclass(frozen=True)
class UnitReconciliation:
    unit_id: str
    status: str
    native_running: bool | None
    handle_digest: str | None
    sources: tuple[RecoverySource, ...]


@dataclass(frozen=True)
class ReconciliationResult:
    run_id: str
    lifecycle_digest: str
    view_epoch: int
    ordinary_reconciled: bool
    units: tuple[UnitReconciliation, ...]
    cleanup: RunClosureResult | None
    diagnostic: str | None
    fresh_ready: bool = field(default=False, init=False)
    lifecycle_complete: bool = field(default=False, init=False)
    ready_for_execution: bool = field(default=False, init=False)


def validate_snapshot(controller, request, reply):
    if (
        type(reply) is not dict
        or set(reply)
        != {
            "recovery_id",
            "session",
            "view_epoch",
            "lifecycle_digest",
            "m3_sequence",
            "last_sample_sequence",
            "rows",
        }
        or reply["recovery_id"] != request["recovery_id"]
        or reply["session"] != controller.owner.session
        or type(reply["view_epoch"]) is not int
        or reply["view_epoch"] != controller.owner._view_epoch
        or reply["lifecycle_digest"] != controller.owner._prepared.lifecycle_digest
        or type(reply["m3_sequence"]) is not int
        or reply["m3_sequence"] < controller.client._evidence_m3
        or type(reply["last_sample_sequence"]) is not int
        or not 0 <= reply["last_sample_sequence"] <= 8192
        or type(reply["rows"]) is not list
        or len(reply["rows"]) != len(request["units"])
    ):
        raise RecoveryError("ML-RECOVERY-ACK")
    for sent, row in zip(request["units"], reply["rows"]):
        if (
            type(row) is not dict
            or set(row)
            != {
                "unit",
                "status",
                "permit_consumed",
                "handle_digest",
                "last_sample_sequence",
                "sources",
            }
            or row["unit"] != sent["unit"]
            or row["status"] not in ("owned", "stopped", "released", "cleanup-only", "never-issued")
            or type(row["permit_consumed"]) is not bool
            or type(row["last_sample_sequence"]) is not int
            or not 0 <= row["last_sample_sequence"] <= reply["last_sample_sequence"]
            or type(row["sources"]) is not list
            or len(row["sources"])
            != {"owned": 2, "stopped": 2, "released": 2, "cleanup-only": 1, "never-issued": 0}[row["status"]]
        ):
            raise RecoveryError("ML-RECOVERY-ACK")
        if row["status"] in ("owned", "stopped", "released"):
            if (
                sent["handle"] is None
                or row["handle_digest"] != _digest(sent["handle"])
                or not row["permit_consumed"]
            ):
                raise RecoveryError("ML-RECOVERY-ACK")
        elif row["handle_digest"] is not None:
            raise RecoveryError("ML-RECOVERY-ACK")
        if row["status"] == "never-issued":
            if (
                sent["claim"] is not None
                or sent["handle"] is not None
                or row["permit_consumed"]
            ):
                raise RecoveryError("ML-RECOVERY-ACK")
        elif not row["permit_consumed"] or sent["claim"] is None:
            raise RecoveryError("ML-RECOVERY-ACK")
        for ref in row["sources"]:
            if (
                type(ref) is not dict
                or set(ref) != {"kind", "id", "sequence", "sha256"}
                or ref["kind"] != "m3-record"
                or type(ref["sequence"]) is not int
                or not 0 < ref["sequence"] <= reply["m3_sequence"]
                or ref["id"] != "m3-record-" + str(ref["sequence"])
                or type(ref["sha256"]) is not str
                or re.fullmatch("sha256:[a-f0-9]{64}", ref["sha256"]) is None
            ):
                raise RecoveryError("ML-RECOVERY-ACK")
        claim = controller.owner._claims.get(row["unit"])
        if (
            claim
            and row["sources"][0]["sha256"] != "sha256:" + claim.intent_digest.hex()
        ):
            raise RecoveryError("ML-RECOVERY-ACK")


class IssuerRecovery(_Original):
    def __init__(self, bootstrap, owner, *, policies, operation_seconds=0.25, controller=None,
                 _coordinator=None, _request=None):
        if type(bootstrap) is not BootstrapSession or type(owner) is not ReleaseOwner:
            raise RecoveryError("ML-RECOVERY-INPUT")
        from .persistence import PersistenceClient

        if type(owner.persistence) is not PersistenceClient:
            raise RecoveryError("ML-RECOVERY-PERSISTENCE")
        bootstrap._holder()
        owner._holder()
        owner._view_registry()
        try:
            valid = (
                type(operation_seconds) in (int, float)
                and math.isfinite(operation_seconds)
                and 0 < operation_seconds <= 5
            )
        except OverflowError:
            valid = False
        if (
            not valid
            or type(policies) is not tuple
            or any(type(p) is not ProbePolicy for p in policies)
            or len(policies) != len(owner._prepared.units)
            or {p.unit_id for p in policies}
            != {u.unit_id for u in owner._prepared.units}
            or getattr(owner.persistence.process, "_root", None) is not bootstrap
            or owner.supervisor.boundaries is not bootstrap.boundaries
        ):
            raise RecoveryError("ML-RECOVERY-ADMISSION")
        for policy in policies:
            policy.__post_init__()
        self._retain()
        self.bootstrap, self.owner, self.client = bootstrap, owner, owner.persistence
        if controller is not None:
            from .controller import ControllerSession

            if (type(controller) is not ControllerSession
                or controller.broker.owner is not owner
                or controller.broker.session is not bootstrap
                or controller.broker._current_controller is not controller
                or controller is controller.broker._controllers[0]):
                raise RecoveryError("ML-RECOVERY-CONTROLLER")
            controller._ordinary()
        self.controller = self._controller_pin = controller
        if _coordinator is not None or _request is not None:
            from .dispatcher import FiniteDispatcher
            if type(_coordinator) is not FiniteDispatcher:
                raise RecoveryError("ML-RECOVERY-COORDINATOR")
            _coordinator._validate_controller_borrow(controller, _request)
        self._coordinator, self._request = _coordinator, _request
        self._borrow_pins = (_coordinator, _request)
        self._released_units = ()
        if _coordinator is not None:
            self._released_units = tuple(unit for unit in owner._launchers
                if _coordinator.teardown._released_current(unit, _coordinator._recovery_end))
        self._released_pin = self._released_units
        self._stopped_units = ()
        if _coordinator is not None:
            stopped = []
            for unit, result in _coordinator.teardown._stop_results.items():
                issuer = owner._launchers[unit]
                descriptor = issuer.recipe.descriptor
                if (unit not in self._released_units and result.generation == descriptor.generation
                    and not result.emergency and result.leader_reaped and result.boundary_empty):
                    record = bootstrap.boundaries.record(descriptor, deadline=_coordinator._recovery_end)
                    if record.state == 'empty' and record.identity_retained:
                        stopped.append(unit)
            self._stopped_units = tuple(stopped)
        self._stopped_pin = self._stopped_units
        self.policies, self.operation_seconds = policies, operation_seconds
        self._pins = (
            bootstrap,
            owner,
            self.client,
            owner._prepared,
            owner._launchers,
            owner._claims,
            policies,
            operation_seconds,
        )
        self._lock = threading.Lock()
        self._active = self._scope = self._result = self._view = None
        self._id = uuid.uuid4().hex
        self._retired_view_epoch = None

    def _holder(self):
        super()._holder()
        if any(
            a is not b
            for a, b in zip(
                (
                    self.bootstrap,
                    self.owner,
                    self.client,
                    self.owner._prepared,
                    self.owner._launchers,
                    self.owner._claims,
                    self.policies,
                    self.operation_seconds,
                ),
                self._pins,
            )
        ):
            raise RecoveryError("ML-RECOVERY-REPLACED")
        self.bootstrap._holder()
        self.owner._view_registry()
        self.client._holder()
        if self.controller is not self._controller_pin:
            raise RecoveryError("ML-RECOVERY-CONTROLLER")
        if (self._coordinator, self._request) != self._borrow_pins:
            raise RecoveryError("ML-RECOVERY-COORDINATOR")
        if self._released_units is not self._released_pin or self._stopped_units is not self._stopped_pin:
            raise RecoveryError("ML-RECOVERY-COORDINATOR")
        if self.controller is not None:
            self.controller._ordinary()

    @property
    def view(self):
        self._holder()
        return self._view

    def cancel(self, reason="recovery-cancel"):
        super()._holder()
        self._pins[0]._pins[4].cancel(reason)

    def _until(self, active):
        end = min(
            active.monotonic_seconds,
            time.monotonic() + self.operation_seconds,
            self.bootstrap._lease / 1e9,
        )
        return HostDeadline(self.owner.session, end)

    def _query(self, unit, launcher, handle, active):
        launcher.revalidate_issued(handle)
        began = time.monotonic()
        if unit in (*self._released_units, *self._stopped_units) and type(launcher) is RunUnitIssuer:
            from .affa_protocol import AuthorityKind
            self._coordinator._validate_controller_borrow(self.controller, self._request)
            reply = launcher._native(AuthorityKind.QUERY, self._until(active), cleanup=True)
            value = ProcessObservation(handle, self.owner.session, time.monotonic(),
                bool(reply.state & 2), bool(reply.state & 4), bool(reply.state & 8), bool(reply.state & 16), None)
        else:
            value = launcher.observe(handle, self._until(active))
        if (
            type(value) is not ProcessObservation
            or value.handle != handle
            or value.host_session != self.owner.session
            or not began <= value.observed_at <= time.monotonic()
        ):
            raise RecoveryError("ML-RECOVERY-ISSUER-OBSERVATION")
        launcher.revalidate_issued(handle)
        return value

    def reconcile(self, active_deadline, cleanup_deadline):
        self._holder()
        for until in (active_deadline, cleanup_deadline):
            if type(until) is not HostDeadline or until.session != self.owner.session:
                raise RecoveryError("ML-RECOVERY-SESSION")
            until.__post_init__()
        scope = (active_deadline, cleanup_deadline)
        if self._scope is not None and scope != self._scope:
            raise RecoveryError("ML-RECOVERY-REPEAT")
        if self._result is not None:
            return self._result
        borrowed = self._coordinator is not None
        if borrowed:
            self._coordinator._validate_controller_borrow(self.controller, self._request)
        n = len(self.owner._prepared.units)
        remaining = active_deadline.monotonic_seconds - time.monotonic()
        if (
            not 0 < remaining <= 5
            or cleanup_deadline.monotonic_seconds
            < active_deadline.monotonic_seconds + n + 2.75
            or int(cleanup_deadline.monotonic_seconds * 1e9)
            > self.bootstrap._generation
            or remaining < (1 + 2 * len(self.owner._launchers)) * self.operation_seconds
            or self.client._sequence + n + 2 > self.client._request_limit
        ):
            raise RecoveryError("ML-RECOVERY-DEADLINE")
        locks = []
        reserved = False
        retain_lock = False
        result_rows = []
        diagnostic = None
        successful = False
        try:
            self.owner._view_registry()
            views = tuple(self.owner._views.values())
            for lock in (
                self._lock,
                self.bootstrap._lock,
                self.owner._lock,
                *(v._lock for v in views),
            ):
                if not lock.acquire(False):
                    raise RecoveryError("ML-RECOVERY-CONFLICT")
                locks.append(lock)
            if self.owner._dispatch_owner is not None and not borrowed:
                raise RecoveryError("ML-RECOVERY-CONFLICT")
            self._scope = scope
            if borrowed:
                self._coordinator._validate_controller_borrow(self.controller, self._request)
            else:
                self.owner._dispatch_owner, self.owner._dispatch_thread = (
                    self,
                    threading.get_ident(),
                )
                reserved = True
            try:
                self.bootstrap._live()
                self.owner._check(active_deadline)
                self.owner._retire_views()
                self._retired_view_epoch = self.owner._view_epoch
                bindings = {}
                for unit, launcher in self.owner._launchers.items():
                    if (
                        type(launcher) not in (CatalogLauncher, RunUnitIssuer)
                        or launcher.owner is not self.owner
                    ):
                        raise RecoveryError("ML-RECOVERY-ISSUER")
                    if type(launcher) is RunUnitIssuer:
                        connection = launcher.broker.connection
                        if (launcher.broker is not self.owner._run_broker_pin
                            or connection.child._root is not self.bootstrap
                            or self.bootstrap._clients.get(connection.child._slot) is not connection):
                            raise RecoveryError("ML-RECOVERY-ISSUER")
                    elif (launcher.process._root is not self.bootstrap
                          or self.bootstrap._clients.get(launcher.process._slot) is not launcher):
                        raise RecoveryError("ML-RECOVERY-ISSUER")
                    handle = launcher._handle
                    if handle is not None:
                        self._query(unit, launcher, handle, active_deadline)
                        bindings[unit] = (launcher, handle)
                rows = []
                for unit in self.owner._prepared.units:
                    claim = self.owner._claims.get(unit.unit_id)
                    binding = bindings.get(unit.unit_id)
                    rows.append(
                        {
                            "unit": unit.unit_id,
                            "claim": claim.operation if claim else None,
                            "handle": asdict(binding[1]) if binding else None,
                        }
                    )
                body = {
                    "recovery_id": self._id,
                    "session": self.owner.session,
                    "view_epoch": self.owner._view_epoch,
                    "units": rows,
                }
                statement = _RecoveryStatement(canonical_bytes(body))
                self._active = statement
                try:
                    reply = self.client.reconcile_snapshot(
                        self, statement, self._until(active_deadline)
                    )
                finally:
                    self._active = None
                observed = {}
                for unit, (launcher, handle) in bindings.items():
                    observed[unit] = self._query(
                        unit, launcher, handle, active_deadline
                    )
                for row in reply["rows"]:
                    result_rows.append(
                        UnitReconciliation(
                            row["unit"],
                            row["status"],
                            observed[row["unit"]].running
                            if row["unit"] in observed
                            else None,
                            row["handle_digest"],
                            tuple(
                                RecoverySource(r["sequence"], r["sha256"])
                                for r in row["sources"]
                            ),
                        )
                    )
                empty_original = (borrowed and not bindings and not self.owner._claims
                    and all(row.status == 'never-issued' for row in result_rows)
                    and all(launcher._handle is None for launcher in self.owner._launchers.values()))
                if not bindings and not empty_original or any(
                    row.status == "cleanup-only" for row in result_rows
                ):
                    raise RecoveryError("ML-RECOVERY-CLEANUP-ONLY")
                for lock in reversed(locks[2:]):
                    lock.release()
                locks = locks[:2]
                view = ProcessReadiness(self.owner, policies=self.policies)
                view._sequence = reply["last_sample_sequence"]
                for unit, (launcher, handle) in bindings.items():
                    view._bindings[unit] = _Binding(launcher, handle)
                    view._attempted.add(unit)
                    if observed[unit].running:
                        view._released.add(unit)
                self.owner._check(active_deadline)
                self._view = view
                successful = True
            except Exception as error:
                message = str(error)
                diagnostic = (
                    message
                    if re.fullmatch("ML-[A-Z-]+", message)
                    else "ML-RECOVERY-UNRESOLVED"
                )
                self.cancel("recovery-incomplete")
            retain_lock = True
        finally:
            if reserved:
                self.owner._dispatch_owner = self.owner._dispatch_thread = None
            for lock in reversed(locks[1:] if retain_lock else locks):
                lock.release()
        try:
            cleanup = None
            if not successful and borrowed and self._view is None and self._retired_view_epoch is not None:
                # A genuine empty view restores cleanup access after epoch retirement;
                # it neither adopts handles nor grants ordinary reconciliation/readiness.
                self._view = ProcessReadiness(self.owner, policies=self.policies, _cleanup_recovery=self)
            if not successful and not borrowed:
                try:
                    cleanup = RunClosure(self.bootstrap).close(
                        cleanup_deadline, reason="recovery-incomplete"
                    )
                except Exception:
                    diagnostic = "ML-RECOVERY-CLEANUP-UNRESOLVED"
            self._result = ReconciliationResult(
                self.owner._run_id,
                self.owner._prepared.lifecycle_digest,
                self.owner._view_epoch,
                successful,
                tuple(result_rows),
                cleanup,
                diagnostic,
            )
            return self._result
        finally:
            self._lock.release()
