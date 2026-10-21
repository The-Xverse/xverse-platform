"""Finite declared lifecycle over already-issued original resources (partial U5).

Host health/lease service is independent of the supervised finite tick source.
Execution facts never establish full admission, helper closure or U7/U8 coverage.
"""

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
import re
import select
import threading
import time
import uuid

from xverse.argus.schema import canonical_bytes
from .admission import _verify_prepared
from .bootstrap import BootstrapSession
from .affa_client import AuthorityConnection
from .run_broker import RunUnitIssuer
from .controller import ControllerSession
from .owner import _Original, OwnerError, GateConnection
from .persistence import PersistenceError
from .providers import ProcessReadiness
from .teardown import ReverseTeardown, TeardownResult
from .time import HostDeadline


@dataclass(frozen=True)
class _Statement:
    channel_kind: str
    request_bytes: bytes = field(repr=False)


@dataclass(frozen=True)
class StepExecution:
    step_id: str
    disposition: str
    dispatch_tick: int | None
    completion_tick: int | None
    normal_recorded: bool


@dataclass(frozen=True, eq=False)
class RestartRequest:
    run_id: str
    unit_id: str
    generation: int
    deadline: HostDeadline


@dataclass(frozen=True)
class RestartResult:
    unit_id: str
    generation: int
    disposition: str
    execution_id: str | None
    diagnostic: str | None


@dataclass(frozen=True, eq=False)
class ControllerRecoveryRequest:
    run_id: str
    session_id: str
    deadline: HostDeadline


@dataclass(frozen=True)
class ControllerRecoveryResult:
    session_id: str
    disposition: str
    ordinary_reconciled: bool
    diagnostic: str | None


@dataclass(frozen=True)
class DispatchResult:
    run_id: str
    lifecycle_digest: str
    execution_succeeded: bool
    steps: tuple[StepExecution, ...]
    cleanup: TeardownResult
    terminal_recorded: bool
    diagnostic: str | None
    health_scans: int
    lease_renewals: int
    collection: object = field(default=None, repr=False)
    terminal: object = field(default=None, repr=False)
    lifecycle_complete: bool = field(default=False, init=False)
    ready_for_execution: bool = field(default=False, init=False)


def validate_schedule_reply(reply, request, dispatcher, operation, channel):
    client = dispatcher.client
    plan = client.schedule
    if channel == "tick":
        expected = {
            "index": request["index"],
            "tick": plan.ticks[request["index"] - 1],
            "schedule_digest": plan.digest,
        }
        if (
            type(reply) is not dict
            or reply != expected
            or type(reply.get("tick")) is not int
            or type(reply.get("index")) is not int
        ):
            raise PersistenceError("ML-SCHEDULE-TICK-ACK")
        return
    kind = request["kind"]
    clock_tick = dispatcher._tick
    if kind == "tick-complete":
        if (
            type(reply) is not dict
            or set(reply) != {"kind", "index", "tick", "event"}
            or reply["kind"] != kind
            or reply["index"] != request["index"]
            or reply["tick"] != request["tick"]
            or type(reply["index"]) is not int
            or type(reply["tick"]) is not int
        ):
            raise PersistenceError("ML-SCHEDULE-ACK")
        events = [reply["event"]]
        m3 = client._evidence_m3
        expected = [("validate", "succeeded", None, "schedule")]
    else:
        if (
            type(reply) is not dict
            or set(reply) != {"kind", "events", "m3_sequence"}
            or reply["kind"] != kind
            or type(reply["events"]) is not list
            or type(reply["m3_sequence"]) is not int
            or reply["m3_sequence"] < client._evidence_m3
        ):
            raise PersistenceError("ML-SCHEDULE-ACK")
        events = reply["events"]
        m3 = reply["m3_sequence"]
        disposition = request.get("disposition")
        status = {
            "completed": "succeeded",
            "failed": "failed",
            "blocked": "skipped",
            "cancelled": "cancelled",
            "unresolved": "unresolved",
        }
        if kind == "begin":
            expected = [("validate", "succeeded", None, "begin")]
        elif kind == "step-dispatch":
            expected = [("validate" if dispatcher._lazy and request['handle'] is None else "intent",
                         "pending", None, "dispatch")]
        elif kind == "step-complete":
            phase = dispatcher._steps[request["step"]].phase
            action = {
                "prepare": "validate",
                "start": "started",
                "observe": "probe",
                "stop": "stop",
                "cleanup": "cleanup",
            }[phase]
            expected = [
                (action, "succeeded", None, "phase"),
                ("disposition", "succeeded", "completed", "disposition"),
            ]
        elif kind == "failure":
            expected = [
                (
                    "cancel"
                    if request["cause"] == "cancellation"
                    else (
                        "health-loss" if request["observation_missing"] else "validate"
                    ),
                    "cancelled"
                    if request["cause"] == "cancellation"
                    else ("unknown" if request["observation_missing"] else "failed"),
                    None,
                    "schedule",
                )
            ]
        elif kind in ("step-disposition", "unit-disposition"):
            expected = [("disposition", status[disposition], disposition, "schedule")]
        elif kind == "run-terminal":
            expected = [
                ("run-terminal", request["outcome"], None, "terminal"),
                (
                    "disposition",
                    request["outcome"],
                    {
                        "succeeded": "completed",
                        "failed": "failed",
                        "cancelled": "cancelled",
                        "unresolved": "unresolved",
                    }[request["outcome"]],
                    "disposition",
                ),
            ]
        else:
            raise PersistenceError("ML-SCHEDULE-ACK")
    if len(events) != len(expected):
        raise PersistenceError("ML-SCHEDULE-ACK")
    unit = request.get("unit")
    step = request.get("step")
    if step:
        unit = dispatcher._steps[step].unit_id
    prior = client._schedule_last_event
    producer = client._schedule_sequence
    ordinal = client._evidence_ordinal
    if kind == "step-complete":
        phase = dispatcher._steps[step].phase
        if phase in ("start", "observe"):
            receipt = client._probe_receipts.get(unit)
            if receipt is None:
                raise PersistenceError("ML-SCHEDULE-ACK")
            prior = next(
                e["eventId"]
                for e in json.loads(receipt.public_bytes)
                if e["extensions"]["xverse.maestro"]["action"] in ("probe", "health")
            )
        elif phase in ("stop", "cleanup"):
            prior = client._teardown_receipts[unit].event_id
    for event, (action, outcome, disposition, suffix) in zip(events, expected):
        if (
            type(event) is not dict
            or set(event)
            != {
                "eventId",
                "producerId",
                "eventKind",
                "producerSequence",
                "correlationId",
                "causationId",
                "clocks",
                "annotation",
                "extensions",
                "ingestionOrdinal",
            }
            or event["eventId"] != operation + "-" + suffix
            or event["producerId"] != "maestro.scheduler14"
            or event["eventKind"] != "annotation"
            or type(event["producerSequence"]) is not int
            or event["producerSequence"] != producer + 1
            or type(event["ingestionOrdinal"]) is not int
            or event["ingestionOrdinal"] <= ordinal
            or event["correlationId"] != client.run_id
            or event["causationId"] != prior
            or event["annotation"] != {"text": "Maestro scheduled " + action}
            or type(event["extensions"]) is not dict
            or set(event["extensions"]) != {"xverse.maestro"}
        ):
            raise PersistenceError("ML-SCHEDULE-ACK")
        value = event["extensions"]["xverse.maestro"]
        base = {
            "schemaVersion": "2.0",
            "lifecycleDigest": "sha256:" + plan.lifecycle_digest,
            "runId": client.run_id,
            "sessionId": client.session,
            "scope": "step" if step else ("unit" if unit else "run"),
            "unitId": unit,
            "generation": dispatcher._generation(unit),
            "operationId": operation,
            "action": action,
            "outcome": outcome,
            "dependencies": [],
        }
        if step:
            base["stepId"] = step
        if kind == 'step-complete' and suffix == 'phase' and action in ('started', 'probe', 'stop', 'cleanup'):
            base['handleRef'] = 'handle-' + hashlib.sha256(canonical_bytes([
                client.run_id, asdict(dispatcher.facade._bindings[unit].handle)])).hexdigest()
            if action in ('started', 'probe'):
                from .lifecycle_evidence import _parents
                dependencies = []
                for parent in _parents(dispatcher.prepared, unit):
                    receipt = client._probe_receipts.get(parent)
                    if receipt is None:
                        raise PersistenceError('ML-SCHEDULE-ACK')
                    sample = next(e for e in json.loads(receipt.public_bytes)
                        if e['extensions']['xverse.maestro']['action'] in ('probe', 'health'))
                    dependencies.append(dict(unitId=parent, generation=dispatcher._generation(parent),
                                             probeEventId=sample['eventId']))
                base['dependencies'] = dependencies
        if disposition:
            base["disposition"] = disposition
        if kind == "tick-complete":
            base["obligationId"] = "tick-" + str(request["index"])
        if action in ("probe", "health-loss"):
            base["probeId"] = "running"
        if kind in ("failure", "step-disposition", "unit-disposition", "run-terminal"):
            base["cause"] = request["cause"]
        if kind == "failure":
            base["diagnosticCode"] = request["diagnostic"]
            if request["observation_missing"] and unit in dispatcher.facade._bindings:
                # Mirror of the worker's lost-observation handleRef (F-10, findings 441-443).
                base['handleRef'] = 'handle-' + hashlib.sha256(canonical_bytes([
                    client.run_id, asdict(dispatcher.facade._bindings[unit].handle)])).hexdigest()
        if (
            type(value) is not dict
            or set(value) != set(base) | {"sourceRefs"}
            or any(value.get(k) != v for k, v in base.items())
        ):
            raise PersistenceError("ML-SCHEDULE-ACK")
        refs = value["sourceRefs"]
        if type(refs) is not list or not 1 <= len(refs) <= 3:
            raise PersistenceError("ML-SCHEDULE-ACK")
        for ref in refs:
            if (
                type(ref) is not dict
                or set(ref) != {"kind", "id", "sequence", "sha256"}
                or type(ref["sequence"]) is not int
                or type(ref["sha256"]) is not str
                or re.fullmatch("sha256:[0-9a-f]{64}", ref["sha256"]) is None
            ):
                raise PersistenceError("ML-SCHEDULE-ACK")
            if ref["kind"] == "admitted-lifecycle":
                if ref != {
                    "kind": "admitted-lifecycle",
                    "id": "schedule-admission",
                    "sequence": 0,
                    "sha256": "sha256:"
                    + hashlib.sha256(plan.canonical_bytes).hexdigest(),
                }:
                    raise PersistenceError("ML-SCHEDULE-ACK")
            elif ref["kind"] == "m3-record":
                if not 1 <= ref["sequence"] <= m3 or ref["id"] != "m3-record-" + str(
                    ref["sequence"]
                ):
                    raise PersistenceError("ML-SCHEDULE-ACK")
            else:
                raise PersistenceError("ML-SCHEDULE-ACK")
        normal = kind in (
            "step-dispatch",
            "step-complete",
            "step-disposition",
            "unit-disposition",
        ) or (kind == "failure" and unit is not None)
        if dispatcher._lazy and (kind in ('step-dispatch', 'step-complete') and request['handle'] is None
            or kind in ('failure', 'step-disposition', 'unit-disposition') and unit not in dispatcher.owner._claims):
            if refs != [{"kind": "admitted-lifecycle", "id": "schedule-admission", "sequence": 0,
                         "sha256": "sha256:" + hashlib.sha256(plan.canonical_bytes).hexdigest()}]:
                raise PersistenceError("ML-SCHEDULE-ACK")
            if m3 != client._evidence_m3:
                raise PersistenceError("ML-SCHEDULE-ACK")
            normal = False
        if normal and (
            m3 <= client._evidence_m3
            or refs[0]["kind"] != "m3-record"
            or refs[0]["sequence"] != m3
        ):
            raise PersistenceError("ML-SCHEDULE-ACK")
        clocks = event["clocks"]
        if type(clocks) is not dict or set(clocks) != {"host", "utc", "simulation"}:
            raise PersistenceError("ML-SCHEDULE-ACK")
        for name, domain, measurement, expected_value in (
            ("host", "host:" + client.session, "s", request["observed_at"]),
            ("utc", "utc:" + client.session, "s", None),
            ("simulation", dispatcher.prepared.clock.domain, "tick", clock_tick),
        ):
            clock = clocks[name]
            if (
                type(clock) is not dict
                or set(clock) != {"domain", "unit", "value"}
                or clock["domain"] != domain
                or clock["unit"] != measurement
                or type(clock["value"]) not in (int, float)
                or not math.isfinite(clock["value"])
                or (expected_value is not None and clock["value"] != expected_value)
            ):
                raise PersistenceError("ML-SCHEDULE-ACK")
        producer = event["producerSequence"]
        ordinal = event["ingestionOrdinal"]
        prior = event["eventId"]
    client._schedule_sequence = producer
    client._schedule_last_event = prior
    client._evidence_ordinal = ordinal
    client._evidence_m3 = m3


class FiniteDispatcher(_Original):
    def __init__(self, facade, bootstrap, *, gates, controller=None, allow_restarts=False,
                 allow_controller_recovery=False):
        if (
            type(facade) is not ProcessReadiness
            or type(bootstrap) is not BootstrapSession
            or type(gates) is not tuple
        ):
            raise OwnerError("ML-SCHEDULE-INPUT")
        facade._holder()
        bootstrap._holder()
        self._retain()
        self.facade = facade
        self.owner = facade._owner
        self.client = self.owner.persistence
        self.bootstrap = bootstrap
        self.prepared = self.owner._prepared
        self.plan = self.client.schedule
        self._lazy = self._lazy_pin = self.client.collection is not None
        units = {u.unit_id for u in self.prepared.units}
        self._initial_requests = 1 if self._lazy else 1 + 2 * len(units)
        if (
            self.plan is None
            or getattr(self.client.process, "_root", None) is not bootstrap
            or tuple(facade._policies.values()) != self.plan.policies
            or self.client._sequence
            + self.plan.required_requests
            - self._initial_requests
            > self.client._request_limit
            or facade._released
            or facade._attempted
            or bootstrap.boundaries is not self.owner.supervisor.boundaries
            or (bool(facade._bindings or self.owner._claims or self.owner._attempted)
                if self._lazy else set(facade._bindings) != units)
        ):
            raise OwnerError("ML-SCHEDULE-ADMISSION")
        self.gates = dict(gates)
        if len(self.gates) != len(gates) or set(self.gates) != units:
            raise OwnerError("ML-SCHEDULE-GATES")
        self._bindings = tuple(facade._bindings.items())
        self._gate_pins = tuple(self.gates.items())
        broker = self.owner._run_broker_pin
        self._broker = broker
        self._controller = controller
        if controller is not None:
            if (type(controller) is not ControllerSession or broker is None
                or controller.broker is not broker or broker._current_controller is not controller):
                raise OwnerError("ML-SCHEDULE-CONTROLLER")
            controller._start_access()
        self._native = broker is not None
        if self._lazy:
            if (not self._native or set(broker._issuers) != units
                or any(g is not broker.connection for g in self.gates.values())
                or any(i._attempted or i._handle is not None for i in broker.issuers)):
                raise OwnerError("ML-SCHEDULE-LAZY-ADMISSION")
            broker._holder()
            broker.connection.child._ordinary()
        self._service_calls = (self.plan.service_operation_count
            if self.plan.service_operation_count is not None else len(self.gates)+1)
        required_service = (4 if controller is not None else 3) if self._native else len(self.gates)+1
        if self._service_calls < required_service:
            raise OwnerError("ML-SCHEDULE-SERVICE-CAPACITY")
        self._backend_pins = (broker, controller, self._native, self._service_calls)
        if self._native and (self.client._sequence + self.plan.required_requests
            - self._initial_requests
            + (self.plan.health_slots if self.plan.service_operation_count is None else 0)
            > self.client._request_limit):
            raise OwnerError("ML-SCHEDULE-ADMISSION")
        for unit, binding in self._bindings:
            gate = self.gates[unit]
            if self._native:
                if (type(binding.launcher) is not RunUnitIssuer
                    or broker.issuer(unit) is not binding.launcher
                    or type(gate) is not AuthorityConnection or gate is not broker.connection
                    or gate.child._root is not bootstrap
                    or bootstrap._clients.get(gate.child._slot) is not gate):
                    raise OwnerError("ML-SCHEDULE-ISSUER")
            elif (
                type(gate) is not GateConnection
                or binding.launcher.process._root is not bootstrap
                or gate.process._root is not bootstrap
                or gate.latch is not self.owner.latch
                or gate.scope
                != self.owner.scope(
                    unit, binding.launcher.recipe.descriptor, gate.artifact_digest
                )
            ):
                raise OwnerError("ML-SCHEDULE-ISSUER")
            binding.launcher._issued(binding.handle)
            if self._native:
                gate.child._ordinary()
            else:
                gate._live()
        self._pins = (
            facade,
            self.owner,
            self.client,
            bootstrap,
            self.prepared,
            self.plan,
        )
        self._steps = {s.step_id: s for s in self.prepared.steps}
        self.teardown = ReverseTeardown(
            facade, per_unit_seconds=self.plan.per_unit_seconds
        )
        self._lock = threading.Lock()
        self._active = None
        self._result = None
        self._scope = None
        self._tick = 0
        self._index = 0
        self._pending = {}
        self._outcomes = {}
        self._active_end = self._work_end = 0
        self.health_scans = self.lease_renewals = 0
        self._cancel_requested = False
        self._terminal_phase = False
        self._collection_receipt = None
        if type(allow_restarts) is not bool:
            raise OwnerError("ML-SCHEDULE-RESTART-ADMISSION")
        self._allow_restarts = allow_restarts
        self._restart_contexts = tuple(self.client._future_contexts) if allow_restarts else ()
        # Conservative finite RPC bound per context: normal teardown, generation,
        # release revalidation and all own/prerequisite/live-unit probe attempts.
        self._restart_cost = 32 + 4 * len(units) + 4 * sum(p.attempts for p in self.plan.policies)
        self._restart_reserve = len(self._restart_contexts) * self._restart_cost
        if allow_restarts and (
            not self._lazy or not self._native or controller is None or not self._restart_contexts
            or self.plan.restart_operation_seconds is None
            or self.client._sequence + self.plan.required_requests - self._initial_requests
               + self._restart_reserve > self.client._request_limit
            or self.plan.required_events + 3 * self._restart_reserve > self.plan.event_limit
            or controller._sequence + len(self.prepared.steps) + self.plan.health_slots
               + 3 * len(self._restart_contexts) > 1024
        ):
            raise OwnerError("ML-SCHEDULE-RESTART-CAPACITY")
        self._restart_pins = (allow_restarts, self._restart_contexts, self._restart_cost, self._restart_reserve)
        self._restart_lock = threading.Lock()
        self._restart_open = False
        self._restart_pending = None
        self._restart_busy = False
        self._restart_requests = {}
        self._restart_results = {}
        self._teardown_history = ()
        if type(allow_controller_recovery) is not bool:
            raise OwnerError("ML-SCHEDULE-RECOVERY-ADMISSION")
        self._allow_controller_recovery = allow_controller_recovery
        self._recovery_max = broker._controller_budget - len(broker._controllers) if broker else 0
        self._recovery_cost = 32 + 8 * len(units) + 4 * sum(p.attempts for p in self.plan.policies)
        self._recovery_reserve = self._recovery_max * self._recovery_cost if allow_controller_recovery else 0
        if allow_controller_recovery and (
            not self._lazy or not self._native or controller is None or self._recovery_max < 1
            or self.plan.recovery_operation_seconds is None
            or self.client._sequence + self.plan.required_requests - self._initial_requests
                + self._restart_reserve + self._recovery_reserve > self.client._request_limit
            or self.plan.required_events + 3 * (self._restart_reserve + self._recovery_reserve) > self.plan.event_limit
        ):
            raise OwnerError("ML-SCHEDULE-RECOVERY-CAPACITY")
        self._recovery_pins = (allow_controller_recovery, self._recovery_max,
                               self._recovery_cost, self._recovery_reserve)
        self._recovery_pending = self._recovery_active = None
        self._recovery_end = None
        self._recovery_requests = {}
        self._recovery_results = {}
        self._recovery_health_scans = 0

    def _holder(self):
        super()._holder()
        if (
            any(
                a is not b
                for a, b in zip(
                    (
                        self.facade,
                        self.owner,
                        self.client,
                        self.bootstrap,
                        self.prepared,
                        self.plan,
                    ),
                    self._pins,
                )
            )
            or tuple(self.facade._bindings.items()) != self._bindings
            or tuple(self.gates.items()) != self._gate_pins
            or self._lazy is not self._lazy_pin
            or (self._broker, self._controller, self._native, self._service_calls) != self._backend_pins
            or (self._allow_restarts, self._restart_contexts, self._restart_cost,
                self._restart_reserve) != self._restart_pins
            or (self._allow_controller_recovery, self._recovery_max, self._recovery_cost,
                self._recovery_reserve) != self._recovery_pins
        ):
            raise OwnerError("ML-SCHEDULE-REPLACED")
        self.facade._holder()
        self.bootstrap._holder()

    def _restartable(self, unit, generation):
        if self._generation(unit) + 1 != generation:
            return False
        normal = self.teardown._cleaned.get(unit)
        return (unit in self.facade._released and unit not in self.teardown._stopped
                or normal is not None and normal.generation == generation - 1
                and normal.unit_cleanup_complete and normal.normal_records_complete)

    def restart(self, run_id, unit_id, *, permit, generation, deadline):
        """Single-member explicit cohort; returns the retained original ticket."""
        return self.restart_many(run_id, ((unit_id, permit, generation),), deadline=deadline)[0]

    def restart_many(self, run_id, requests, *, deadline):
        """Queue one explicit, dependency-ordered cohort; no resource mutation."""
        self._holder()
        if (not self._allow_restarts or type(run_id) is not str or run_id != self.owner._run_id
            or type(requests) is not tuple or not 1 <= len(requests) <= len(self._restart_contexts)
            or type(deadline) is not HostDeadline or deadline.session != self.owner.session):
            raise OwnerError("ML-SCHEDULE-RESTART-INPUT")
        deadline.__post_init__()
        checked = {}
        for request in requests:
            if (type(request) is not tuple or len(request) != 3 or type(request[0]) is not str
                or type(request[2]) is not int or request[0] in checked):
                raise OwnerError("ML-SCHEDULE-RESTART-INPUT")
            unit, permit, generation = request
            context = next((c for c in self._restart_contexts
                            if c.binding.unit_id == unit and c.binding.generation == generation), None)
            if context is None or permit is not context.binding.permit:
                raise OwnerError("ML-SCHEDULE-RESTART-PERMIT")
            checked[unit] = generation
        keys = tuple((u, checked[u]) for u in self.prepared.resource_order if u in checked)
        with self._restart_lock:
            old = tuple(self._restart_requests.get(key) for key in keys)
            if any(ticket is not None for ticket in old):
                if any(ticket is None or ticket.deadline != deadline for ticket in old):
                    raise OwnerError("ML-SCHEDULE-RESTART-REPEAT")
                return old
            if (not self._restart_open or self.owner._dispatch_owner is not self
                or self._terminal_phase or self.owner.latch.cancelled
                or not time.monotonic() < deadline.monotonic_seconds <= self._active_end):
                raise OwnerError("ML-SCHEDULE-RESTART-CLOSED")
            if self._restart_pending is not None or self._restart_busy or self._recovery_pending is not None:
                raise OwnerError("ML-SCHEDULE-RESTART-CONFLICT")
            if any(not self._restartable(unit, generation) for unit, generation in keys):
                raise OwnerError("ML-SCHEDULE-RESTART-GENERATION")
            tickets = tuple(RestartRequest(run_id, unit, generation, deadline) for unit, generation in keys)
            for key, ticket in zip(keys, tickets):
                self._restart_requests[key] = ticket
            self._restart_pending = tickets
            return tickets

    def restart_result(self, ticket):
        self._holder()
        with self._restart_lock:
            if (type(ticket) is not RestartRequest
                or self._restart_requests.get((ticket.unit_id, ticket.generation)) is not ticket):
                raise OwnerError("ML-SCHEDULE-RESTART-ORIGINAL")
            return self._restart_results.get(id(ticket))

    def _close_restarts(self):
        with self._restart_lock:
            self._restart_open = False
            if self._restart_pending is not None:
                for ticket in self._restart_pending:
                    self._restart_results[id(ticket)] = RestartResult(ticket.unit_id, ticket.generation,
                        "rejected", None, "ML-SCHEDULE-RESTART-CLOSED")
                self._restart_pending = None
            if self._recovery_pending is not None:
                ticket = self._recovery_pending
                self._recovery_results[id(ticket)] = ControllerRecoveryResult(ticket.session_id,
                    "rejected", False, "ML-SCHEDULE-RECOVERY-CLOSED")
                self._recovery_pending = None

    def replace_controller(self, run_id, *, session_id, deadline):
        """Queue an explicit original-controller handover; never infer recovery."""
        _Original._holder(self)
        if (not self._allow_controller_recovery or type(run_id) is not str or run_id != self.owner._run_id
            or type(session_id) is not str or re.fullmatch('[A-Za-z0-9_.:-]{1,64}', session_id) is None
            or session_id == self.owner.session or type(deadline) is not HostDeadline
            or deadline.session != self.owner.session):
            raise OwnerError("ML-SCHEDULE-RECOVERY-INPUT")
        deadline.__post_init__()
        with self._restart_lock:
            old = self._recovery_requests.get(session_id)
            if old is not None:
                if old.deadline != deadline:
                    raise OwnerError("ML-SCHEDULE-RECOVERY-REPEAT")
                return old
            if self._restart_busy or self._restart_pending is not None or self._recovery_pending is not None:
                raise OwnerError("ML-SCHEDULE-RECOVERY-CONFLICT")
            self._holder()
            if (not self._restart_open or self.owner._dispatch_owner is not self or self._terminal_phase
                or self.owner.latch.cancelled
                or not time.monotonic() < deadline.monotonic_seconds <= self._active_end):
                raise OwnerError("ML-SCHEDULE-RECOVERY-CLOSED")
            if (len(self._recovery_requests) >= self._recovery_max
                or len(self._broker._controllers) >= self._broker._controller_budget
                or any(c.session_id == session_id for c in self._broker._controllers)):
                raise OwnerError("ML-SCHEDULE-RECOVERY-CAPACITY")
            ticket = ControllerRecoveryRequest(run_id, session_id, deadline)
            self._recovery_requests[session_id] = ticket
            self._recovery_pending = ticket
            return ticket

    def controller_recovery_result(self, ticket):
        _Original._holder(self)
        with self._restart_lock:
            if (type(ticket) is not ControllerRecoveryRequest
                or self._recovery_requests.get(ticket.session_id) is not ticket):
                raise OwnerError("ML-SCHEDULE-RECOVERY-ORIGINAL")
            return self._recovery_results.get(id(ticket))

    def _validate_controller_borrow(self, controller, ticket):
        """Only original in-flight transition may borrow, never replace, ownership."""
        _Original._holder(self)
        if (type(controller) is not ControllerSession or type(ticket) is not ControllerRecoveryRequest
            or not self._allow_controller_recovery or self._recovery_active is not ticket
            or self._recovery_requests.get(ticket.session_id) is not ticket or not self._restart_busy
            or self.owner._dispatch_owner is not self or self.owner._dispatch_thread != threading.get_ident()
            or controller.broker is not self._broker or self._broker._current_controller is not controller
            or controller.session_id != ticket.session_id or self.client is not self._broker.storage
            or self._recovery_end is None
            or self._recovery_end.monotonic_seconds > ticket.deadline.monotonic_seconds):
            raise OwnerError("ML-SCHEDULE-RECOVERY-ORIGINAL")

    def _commit_controller_view(self, controller, ticket, *, cleanup_only=False):
        self._validate_controller_borrow(controller, ticket)
        recovery = controller._recovery
        if (recovery is None or recovery._coordinator is not self or recovery._request is not ticket
            or recovery.controller is not controller or recovery.owner is not self.owner
            or recovery._result is None or recovery._view is None
            or not cleanup_only and (not recovery._result.ordinary_reconciled
                                     or controller._view is not recovery._view or controller._phase != 'active')
            or cleanup_only and not self.owner.latch.cancelled):
            raise OwnerError("ML-SCHEDULE-RECOVERY-VIEW")
        view = recovery._view
        view._holder()
        if view._owner is not self.owner or tuple(view._policies.values()) != self.plan.policies:
            raise OwnerError("ML-SCHEDULE-RECOVERY-VIEW")
        old = self.teardown
        current = ReverseTeardown(view, per_unit_seconds=self.plan.per_unit_seconds)
        for name in ('_stopped', '_stop_results', '_cleaned', '_receipts', '_intents'):
            getattr(current, name).update(getattr(old, name))
        current._known_reaps.update(old._known_reaps)
        self._teardown_history += (old,)
        self.teardown, self.facade, self._controller = current, view, controller
        self._bindings = tuple(view._bindings.items())
        self._pins = (view, self.owner, self.client, self.bootstrap, self.prepared, self.plan)
        self._backend_pins = (self._broker, controller, self._native, self._service_calls)

    def _drain_controller_recovery(self):
        if self._recovery_pending is None:
            return False
        if self.owner._dispatch_owner is not self or self.owner._dispatch_thread != threading.get_ident():
            raise OwnerError("ML-OWNER-CONFLICT")
        with self._restart_lock:
            ticket = self._recovery_pending
            if ticket is None:
                return False
            self._recovery_pending = None
            self._recovery_active = ticket
            self._restart_busy = True
        successor = None
        mutated = False
        try:
            self._holder()
            now = time.monotonic()
            if now >= ticket.deadline.monotonic_seconds:
                raise OwnerError("ML-SCHEDULE-RECOVERY-DEADLINE")
            # Original broker remains authority even when the old controller died.
            end = self._end()
            end = HostDeadline(self.owner.session, min(end.monotonic_seconds, ticket.deadline.monotonic_seconds))
            self._broker.renew(HostDeadline(self.owner.session,
                min(now + 5, self.bootstrap._generation / 1e9 - 2)), end)
            self.lease_renewals += 2
            if self._recovery_health_scans >= self._recovery_max:
                raise OwnerError("ML-SCHEDULE-RECOVERY-CAPACITY")
            scan = min(self._active_end, ticket.deadline.monotonic_seconds,
                       time.monotonic() + self.plan.health_scan_seconds, self.bootstrap._lease / 1e9)
            self.facade.check_health(HostDeadline(self.owner.session, scan), force=True)
            self._recovery_health_scans += 1
            self.health_scans += 1
            until = self._end(recovery=True)
            until = HostDeadline(self.owner.session, min(until.monotonic_seconds, ticket.deadline.monotonic_seconds))
            if until.monotonic_seconds - time.monotonic() < (1 + 2 * len(self.owner._launchers)) * .25 + self.plan.operation_seconds:
                raise OwnerError("ML-SCHEDULE-RECOVERY-DEADLINE")
            self._recovery_end = until
            before = self.client._sequence
            mutated = True
            retirement = self._controller.retire(until, terminate=True)
            if not (retirement.original_child_dead and retirement.original_child_reaped and retirement.own_boundary_released):
                raise OwnerError("ML-SCHEDULE-RECOVERY-RETIRE")
            successor = self._broker.admit_controller(ticket.session_id, until)
            view = successor.reconcile(self.plan.policies, until,
                HostDeadline(self.owner.session, self._work_end), _coordinator=self, _request=ticket)
            self._commit_controller_view(successor, ticket)
            if view is not self.facade or self.client._sequence - before > self._recovery_cost:
                raise OwnerError("ML-SCHEDULE-RECOVERY-INCOMPLETE")
            outcome = ControllerRecoveryResult(ticket.session_id, 'completed', True, None)
        except Exception as error:
            diagnostic = str(error) if re.fullmatch('ML-[A-Z-]+', str(error)) else 'ML-SCHEDULE-RECOVERY-FAILED'
            if mutated:
                self.owner.cancel('dispatcher-controller-recovery-failed')
                if successor is not None and successor._recovery is not None and successor._recovery._view is not None:
                    self._commit_controller_view(successor, ticket, cleanup_only=True)
            outcome = ControllerRecoveryResult(ticket.session_id, 'failed' if mutated else 'rejected', False, diagnostic)
            with self._restart_lock:
                self._recovery_results[id(ticket)] = outcome
            if mutated:
                raise
        finally:
            with self._restart_lock:
                if id(ticket) not in self._recovery_results:
                    self._recovery_results[id(ticket)] = locals().get('outcome',
                        ControllerRecoveryResult(ticket.session_id, 'failed' if mutated else 'rejected',
                                                 False, 'ML-SCHEDULE-RECOVERY-INTERRUPTED'))
                self._recovery_active = None
                self._recovery_end = None
                self._restart_busy = False
        return True

    def _restart_end(self, ticket, *, phase=None, restart=False):
        current = self._end(unit=ticket.unit_id, phase=phase, restart=restart)
        return HostDeadline(self.owner.session, min(current.monotonic_seconds,
                                                    ticket.deadline.monotonic_seconds))

    def _quiesce_restart_unit(self, ticket):
        unit = ticket.unit_id
        normal = self.teardown._cleaned.get(unit)
        if normal is not None and normal.generation == ticket.generation - 1:
            if not self.teardown._released_current(unit, self._restart_end(ticket)):
                raise OwnerError("ML-GENERATION-PRIOR-RELEASE")
            return
        unit_end = min(ticket.deadline.monotonic_seconds, self._active_end,
                       time.monotonic() + self.plan.per_unit_seconds)
        for phase in ("stop", "cleanup"):
            self._service()
            bound = self._restart_end(ticket, phase=phase)
            until = HostDeadline(self.owner.session, min(bound.monotonic_seconds, unit_end))
            self._controller.request(unit, phase, until)
            result = self.teardown.phase(unit, phase, until)
            if (result.emergency or not result.leader_reaped or not result.boundary_empty
                or phase == "cleanup" and not result.normal_records_complete):
                raise OwnerError("ML-SCHEDULE-RESTART-TEARDOWN")

    def _restart_unit(self, ticket):
        from .prbc import BoundaryDescriptor
        self._service()
        unit = ticket.unit_id
        old_teardown = self.teardown
        began_sequence = self.client._sequence
        descriptor = BoundaryDescriptor(self.owner._run_id, unit, ticket.generation,
            "restart-" + uuid.uuid4().hex, self.bootstrap.boundaries.release_epoch)
        # One sealed original operation end through actual release/fresh probes.
        until = self._restart_end(ticket, restart=True)
        self.bootstrap.boundaries.create_frozen(descriptor, deadline=until)
        prepared = self._broker._prepare_generation(old_teardown, unit, descriptor, until)
        issuer = self._broker.advance_generation(prepared, until)
        # Authentic ADVANCE already retired the old binding, including on Stage loss.
        self._bindings = tuple(self.facade._bindings.items())
        current = ReverseTeardown(self.facade, per_unit_seconds=self.plan.per_unit_seconds)
        for name in ("_stopped", "_stop_results", "_cleaned"):
            getattr(current, name).update({u: value for u, value in getattr(old_teardown, name).items() if u != unit})
        current._receipts.update(old_teardown._receipts)
        current._intents.update({key: value for key, value in old_teardown._intents.items() if key[0] != unit})
        current._known_reaps.update(old_teardown._known_reaps - {unit})
        self._teardown_history += (old_teardown,)
        self.teardown = current
        handle = issuer.stage(until)
        self.facade.bind(issuer, handle)
        self._bindings = tuple(self.facade._bindings.items())
        self._controller.request(unit, "start", until)
        observation = self.facade.start(unit, descriptor, self.gates[unit], until)
        if not observation.ready or self.client._sequence - began_sequence > self._restart_cost:
            raise OwnerError("ML-SCHEDULE-RESTART-INCOMPLETE")
        return RestartResult(unit, ticket.generation, "completed", handle.execution_id, None)

    def _drain_restart(self):
        if (self.owner._dispatch_owner is not self
            or self.owner._dispatch_thread != threading.get_ident()):
            raise OwnerError("ML-OWNER-CONFLICT")
        with self._restart_lock:
            tickets = self._restart_pending
            if tickets is None:
                return False
            selected = {ticket.unit_id for ticket in tickets}
            if any(self._steps[key].unit_id in selected for key in self._pending):
                return False
            self._restart_pending = None
            self._restart_busy = True
        mutated = False
        current = tickets[0]
        failure = "ML-SCHEDULE-RESTART-INTERRUPTED"
        try:
            from .lifecycle_evidence import _parents
            self._holder()
            if self.owner.latch.cancelled:
                raise OwnerError("ML-SCHEDULE-CANCELLED")
            for ticket in tickets:
                current = ticket
                if time.monotonic() >= ticket.deadline.monotonic_seconds:
                    raise OwnerError("ML-SCHEDULE-RESTART-DEADLINE")
                if not self._restartable(ticket.unit_id, ticket.generation):
                    raise OwnerError("ML-SCHEDULE-RESTART-GENERATION")
                issuer = self._broker.issuer(ticket.unit_id)
                issuer.revalidate_issued(issuer._handle)
                bound = self._restart_end(ticket)
                if any(ticket.unit_id in _parents(self.prepared, other)
                       and other not in selected and not self.teardown._released_current(other, bound)
                       for other in self.owner._claims if other != ticket.unit_id):
                    raise OwnerError("ML-GENERATION-DEPENDENTS")
            # Every dependency check above completes before the first stop.
            mutated = True
            by_unit = {ticket.unit_id: ticket for ticket in tickets}
            for unit in self.teardown._order():
                if unit in selected:
                    current = by_unit[unit]
                    self._quiesce_restart_unit(current)
            for ticket in tickets:
                current = ticket
                outcome = self._restart_unit(ticket)
                with self._restart_lock:
                    self._restart_results[id(ticket)] = outcome
        except BaseException as error:
            failure = str(error) if re.fullmatch("ML-[A-Z-]+", str(error)) else "ML-SCHEDULE-RESTART-FAILED"
            if mutated:
                self.owner.cancel("dispatcher-restart-failed")
                raise
            if not isinstance(error, Exception):
                raise
        finally:
            with self._restart_lock:
                for ticket in tickets:
                    if id(ticket) not in self._restart_results:
                        disposition = "rejected" if not mutated else "failed" if ticket is current else "cancelled"
                        self._restart_results[id(ticket)] = RestartResult(ticket.unit_id, ticket.generation,
                            disposition, None, failure)
                self._restart_busy = False
        return True

    def _quiesce_finished_restarts(self):
        """Normal terminal cleanup, never an implicit grant of a restart request."""
        if not self._restart_requests:
            return False
        from .lifecycle_evidence import _parents
        stopping = {s.unit_id for s in self.prepared.eligible_steps(self._tick, self._outcomes)
                    if s.phase in ("stop", "cleanup")}
        changed = False
        for unit in self.teardown._order():
            if unit not in self.facade._released:
                continue
            generation = self._generation(unit)
            ticket = self._restart_requests.get((unit, generation))
            result = self._restart_results.get(id(ticket)) if ticket is not None else None
            steps = [s for s in self.prepared.steps if s.unit_id == unit]
            if (result is None or result.disposition != "completed"
                or any(s.step_id not in self._outcomes or self._outcomes[s.step_id].disposition != "completed" for s in steps)
                or not (self._tick == self.prepared.clock.horizon_ticks
                        or stopping.intersection(_parents(self.prepared, unit)))):
                continue
            unit_end = min(self._active_end, time.monotonic() + self.plan.per_unit_seconds)
            for phase in ("stop", "cleanup"):
                self._service()
                cap = self._end(unit=unit, phase=phase)
                outcome = self.teardown.phase(unit, phase, HostDeadline(self.owner.session,
                    min(unit_end, cap.monotonic_seconds)))
                if outcome.emergency or phase == "cleanup" and not outcome.normal_records_complete:
                    raise OwnerError("ML-SCHEDULE-TEARDOWN-INCOMPLETE")
            changed = True
        return changed

    def _generation(self, unit):
        if unit is None:
            return 0
        claim = self.owner._claims.get(unit)
        if claim is not None:
            return claim.receipt.generation
        if self._lazy:
            return (self._broker.issuer(unit)._image.admission.descriptor.generation
                    if unit in self.owner._attempted else 0)
        raise OwnerError("ML-SCHEDULE-CLAIM")

    def _send(self, kind, deadline, **values):
        body = dict(values)
        if kind != "tick":
            body.update(kind=kind, observed_at=time.monotonic())
        statement = _Statement(
            "tick" if kind == "tick" else "schedule", canonical_bytes(body)
        )
        self._active = statement
        try:
            return self.client.schedule_call(self, statement, deadline)
        finally:
            self._active = None

    def _end(self, *, terminal=False, restart=False, recovery=False, unit=None, phase=None):
        now = time.monotonic()
        budget = self.plan.recovery_operation_seconds if recovery else self.plan.restart_operation_seconds if restart else self.plan.operation_seconds
        if not restart and self.plan.use_action_timeouts and unit is not None and phase is not None:
            budget = next((seconds for uid, name, seconds in self.plan.action_timeouts
                           if uid == unit and name == phase), None)
            if budget is None:
                raise OwnerError("ML-SCHEDULE-ACTION-TIMEOUT")
        end = min(
            self._work_end if terminal else self._active_end,
            now + budget,
        )
        end = min(end, self.bootstrap._lease / 1e9)
        if terminal and self._lazy and self._terminal_phase:
            service_end = HostDeadline(self.owner.session, min(end, now + .5))
            lease = self._broker.service_terminal(service_end)
            return HostDeadline(self.owner.session, min(end, lease / 1e9 - .05))
        health = self.facade.next_health_deadline
        if health is not None:
            end = min(end, health.monotonic_seconds - self.plan.health_scan_seconds)
        for unit, gate in self.gates.items():
            if unit not in self.teardown._stopped:
                end = min(end, gate.lease_ns / 1e9)
        if end <= now:
            raise OwnerError("ML-SCHEDULE-SERVICE-DEADLINE")
        return HostDeadline(self.owner.session, end)

    def _service(self, *, terminal=False):
        if not terminal:
            self._drain_controller_recovery()
        if self.owner.latch.cancelled:
            raise OwnerError("ML-SCHEDULE-CANCELLED")
        limit = self._work_end if terminal else self._active_end
        renew_budget = self._service_calls * self.plan.operation_seconds
        renew_margin = renew_budget + self.plan.operation_seconds
        def lease_ends():
            return [self.bootstrap._lease / 1e9] + [
                gate.lease_ns / 1e9 for unit, gate in self.gates.items()
                if unit not in self.teardown._stopped]
        leases = lease_ends()
        health = self.facade.next_health_deadline
        service = self.plan.health_scan_seconds + renew_margin
        now = time.monotonic()
        # Do not spend the old lease's renewal reserve on an earlier health scan.
        if (health and now >= health.monotonic_seconds - service
            and min(leases) - now <= service):
            self._renew_service(limit)
            leases = lease_ends()
            health = self.facade.next_health_deadline
        if health and time.monotonic() >= health.monotonic_seconds - service:
            if self.health_scans - self._recovery_health_scans >= self.plan.health_slots:
                raise OwnerError("ML-SCHEDULE-HEALTH-CAPACITY")
            until = min(limit, health.monotonic_seconds, min(leases) - renew_budget)
            if until <= time.monotonic():
                raise OwnerError("ML-SCHEDULE-SERVICE-DEADLINE")
            self.facade.check_health(
                HostDeadline(self.owner.session, until), force=True
            )
            self.health_scans += 1
        if min(lease_ends()) - time.monotonic() <= renew_margin:
            self._renew_service(limit)

    def _renew_service(self, limit):
        now = time.monotonic()
        leases = [self.bootstrap._lease / 1e9] + [
            gate.lease_ns / 1e9 for unit, gate in self.gates.items()
            if unit not in self.teardown._stopped]
        health = self.facade.next_health_deadline
        health_end = (
            health.monotonic_seconds - self.plan.health_scan_seconds
            if health
            else limit
        )
        until = HostDeadline(
            self.owner.session,
            min(limit, health_end, now + self.plan.operation_seconds, min(leases)),
        )
        next_end = min(time.monotonic() + 5, self.bootstrap._generation / 1e9 - 2)
        if next_end <= self.bootstrap._lease / 1e9:
            raise OwnerError("ML-SCHEDULE-LEASE-EXHAUSTED")
        if self._native:
            if self._controller is not None:
                old_controller = self._controller
                try:
                    old_controller.request(None, "heartbeat", until)
                except Exception:
                    # A matching request may arrive after the service safe point.
                    # Its coordinator transition renews under its own original end.
                    if self._recovery_pending is not None and not self.owner.latch.cancelled:
                        self._drain_controller_recovery()
                        if self._controller is not old_controller:
                            return
                    raise
            self._broker.renew(HostDeadline(self.owner.session, next_end), until)
            self.lease_renewals += 2
            return
        self.bootstrap.renew(HostDeadline(self.owner.session, next_end), until)
        self.lease_renewals += 1
        for unit, gate in self.gates.items():
            if unit in self.teardown._stopped:
                continue
            target = min(next_end, time.monotonic() + 4.8)
            if target > gate.lease_ns / 1e9:
                gate.renew(
                    HostDeadline(self.owner.session, target),
                    HostDeadline(
                        self.owner.session,
                        min(
                            limit,
                            health_end,
                            time.monotonic() + self.plan.operation_seconds,
                            gate.lease_ns / 1e9,
                        ),
                    ),
                )
                self.lease_renewals += 1


    def _statement(self, kind, step, *, terminal=False):
        self._service(terminal=terminal)
        binding = self.facade._bindings.get(step.unit_id)
        if binding is None and (not self._lazy or not (step.phase == 'prepare'
            or kind == 'step-dispatch' and step.phase == 'start')):
            raise OwnerError("ML-SCHEDULE-HANDLE")
        return self._send(
            kind,
            self._end(terminal=terminal, unit=step.unit_id, phase=step.phase),
            step=step.step_id,
            index=self._index,
            tick=self._tick,
            handle=asdict(binding.handle) if binding is not None else None,
        )

    def _effect(self, step):
        self._service()
        unit = step.unit_id
        until = self._end(unit=unit, phase=step.phase)
        binding = self.facade._bindings.get(unit)
        if self._controller is not None:
            self._controller.request(unit, step.phase, until)
        if step.phase == "prepare":
            _verify_prepared(
                self.prepared, self.client._result_input, self.client._resources
            )
        elif step.phase == "start":
            if self._lazy:
                self.owner.commit_intent(unit, until)
                issuer = self._broker.issuer(unit)
                handle = issuer.stage(until)
                self.facade.bind(issuer, handle)
                self._bindings = tuple(self.facade._bindings.items())
                binding = self.facade._bindings[unit]
            self.facade.start(
                unit, binding.launcher.recipe.descriptor, self.gates[unit], until
            )
        elif step.phase == "observe":
            self.facade.check_unit_health(unit, until)
        else:
            if step.phase == "cleanup" and unit not in self.teardown._stopped:
                stopped = self.teardown.phase(unit, "stop", until)
                if stopped.emergency:
                    raise OwnerError("ML-SCHEDULE-TEARDOWN-INCOMPLETE")
            result = self.teardown.phase(unit, step.phase, until)
            if result.emergency:
                raise OwnerError("ML-SCHEDULE-TEARDOWN-INCOMPLETE")

    def _cleanup(self):
        if self._lazy:
            end = min(self._work_end, time.monotonic() + self.plan.operation_seconds,
                      self.bootstrap._lease / 1e9)
            self._broker.cancel('dispatcher-terminal-fence', deadline=HostDeadline(self.owner.session, end))
            self._broker.service_terminal(HostDeadline(self.owner.session, end))
            self._terminal_phase = True
            end = min(self._work_end, time.monotonic() + len(self.prepared.units) * self.plan.per_unit_seconds)
            return self.teardown.run(HostDeadline(self.owner.session, end), reason='dispatcher-terminal')
        try:
            if not self.owner.latch.cancelled:
                for unit in self.teardown._order():
                    if self._lazy and unit not in self.facade._bindings:
                        continue
                    if unit in self.teardown._cleaned:
                        continue
                    self._service(terminal=True)
                    for phase in ("stop", "cleanup"):
                        result = self.teardown.phase(
                            unit, phase, self._end(terminal=True)
                        )
                        if result.emergency:
                            break
                    if self.owner.latch.cancelled:
                        break
        except Exception:
            self.owner.cancel("dispatcher-cleanup-failed")
        end = min(
            self._work_end,
            time.monotonic() + len(self.prepared.units) * self.plan.per_unit_seconds,
        )
        return self.teardown.run(
            HostDeadline(self.owner.session, end), reason="dispatcher-terminal"
        )

    def _admissible(self, step):
        if step.phase == "stop":
            return self._admissible_stop(step.unit_id)
        if step.phase == "cleanup":
            return step.unit_id in self.teardown._stopped or (
                self._tick == self.prepared.clock.horizon_ticks
                and self._admissible_stop(step.unit_id)
                and not any(
                    s.unit_id == step.unit_id and s.phase == "stop"
                    for s in self.prepared.steps
                )
            )
        return True

    def _admissible_stop(self, unit):
        from .lifecycle_evidence import _parents

        return all(
            (self.teardown._released_current(other, self._end(terminal=True))
                if self._native else other in self.teardown._cleaned)
            for other in self.owner._claims
            if other != unit and unit in _parents(self.prepared, other)
        )

    def run(self, active_deadline, terminal_deadline):
        self._holder()
        for deadline in (active_deadline, terminal_deadline):
            if (
                type(deadline) is not HostDeadline
                or deadline.session != self.owner.session
            ):
                raise OwnerError("ML-SCHEDULE-SESSION")
            deadline.__post_init__()
        scope = (active_deadline, terminal_deadline)
        if self._result is not None:
            if scope != self._scope:
                raise OwnerError("ML-SCHEDULE-REPEAT")
            return self._result
        if not self._lock.acquire(False):
            raise OwnerError("ML-SCHEDULE-CONFLICT")
        locks = []
        claimed = False
        try:
            for lock in (self.facade._lock, self.owner._lock):
                if not lock.acquire(False):
                    raise OwnerError("ML-SCHEDULE-CONFLICT")
                locks.append(lock)
            if self.owner._dispatch_owner is not None:
                raise OwnerError("ML-SCHEDULE-CONFLICT")
            now = time.monotonic()
            reserve = self.plan.terminal_reserve_seconds
            if self._lazy:
                reserve += self.client.collection.collection_seconds + self.client.collection.terminal_seconds
                admission = self.client.coverage.data(self.client.coverage_digest)
                if active_deadline.monotonic_seconds > admission['end']:
                    raise OwnerError("ML-SCHEDULE-COVERAGE-END")
            if (
                not 0
                < active_deadline.monotonic_seconds - now
                <= self.plan.active_seconds
                or terminal_deadline.monotonic_seconds
                < active_deadline.monotonic_seconds + reserve
                or terminal_deadline.monotonic_seconds
                > self.bootstrap._generation / 1e9
                or self.client._sequence
                + self.plan.required_requests
                - self._initial_requests
                + self._restart_reserve
                > self.client._request_limit
                or self.facade._released
                or self.facade._attempted
            ):
                raise OwnerError("ML-SCHEDULE-DEADLINE")
            self.owner._dispatch_owner = self
            self.owner._dispatch_thread = threading.get_ident()
            claimed = True
            for lock in reversed(locks):
                lock.release()
            locks = []
            self._active_end = active_deadline.monotonic_seconds
            self._work_end = terminal_deadline.monotonic_seconds - 2
            if self._lazy:
                self._work_end = min(terminal_deadline.monotonic_seconds - self.client.collection.drain_seconds,
                                     self.bootstrap._generation / 1e9 - 2)
            self._scope = scope
            with self._restart_lock:
                self._restart_open = self._allow_restarts or self._allow_controller_recovery
            diagnostic = None
            terminal = False
            current = None
            try:
                self._send("begin", self._end())
                for index in range(1, len(self.plan.ticks) + 1):
                    cycle_began = time.monotonic()
                    self._service()
                    tick = self._send(
                        "tick", self._end(), index=index, previous=self._tick
                    )
                    self._tick = tick["tick"]
                    self._index = index
                    if any(
                        s.latest_ticks < self._tick and s.step_id not in self._outcomes
                        for s in self.prepared.steps
                    ):
                        raise OwnerError("ML-SCHEDULE-WINDOW-MISSED")
                    while True:
                        self._service()
                        changed = False
                        for key, (started, due) in tuple(self._pending.items()):
                            if self._tick >= due:
                                current = self._steps[key]
                                self._statement("step-complete", current)
                                self._outcomes[key] = StepExecution(
                                    key, "completed", started, self._tick, True
                                )
                                del self._pending[key]
                                changed = True
                                current = None
                        if self._drain_restart():
                            changed = True
                        if self._quiesce_finished_restarts():
                            changed = True
                        eligible = self.prepared.eligible_steps(
                            self._tick, self._outcomes
                        )
                        for step in eligible:
                            if step.step_id in self._pending or not self._admissible(
                                step
                            ):
                                continue
                            current = step
                            self._statement("step-dispatch", step)
                            self._pending[step.step_id] = (
                                self._tick,
                                self._tick + step.duration_ticks,
                            )
                            self._effect(step)
                            changed = True
                            current = None
                            # Recompute combined eligibility after every completed effect.
                            break
                        if not changed:
                            break
                    self._send(
                        "tick-complete", self._end(), index=index, tick=self._tick
                    )
                    if index < len(self.plan.ticks):
                        end = self._end().monotonic_seconds
                        pause = self.plan.poll_seconds
                        if self.plan.service_operation_count is not None:
                            pause = max(0, pause - (time.monotonic()-cycle_began))
                        select.select(
                            [],
                            [],
                            [],
                            min(pause, max(0, end - time.monotonic())),
                        )
                if self._pending or set(self._outcomes) != set(self._steps):
                    raise OwnerError("ML-SCHEDULE-INCOMPLETE")
            except Exception as error:
                code = str(error)
                diagnostic = (
                    code
                    if re.fullmatch("ML-[A-Z-]+", code)
                    else "ML-SCHEDULE-OPERATION-FAILED"
                )
                if self._cancel_requested:
                    diagnostic = "ML-SCHEDULE-CANCELLED"
                failure = None if self._cancel_requested else self.facade._probe_failure
                unit = (
                    failure.unit_id
                    if failure
                    else (
                        current.unit_id
                        if current and not self._cancel_requested
                        else None
                    )
                )
                phase = (
                    "observe" if failure else (current.phase if current else "prepare")
                )
                self.owner.cancel("dispatcher-failed")
                try:
                    self._send(
                        "failure",
                        HostDeadline(
                            self.owner.session,
                            min(
                                self._work_end,
                                # Terminal-section statement: per-unit budget like run-terminal,
                                # capped by the admitted work window (finding 386).
                                time.monotonic() + self.plan.per_unit_seconds,
                            ),
                        ),
                        unit=unit,
                        phase=phase,
                        observation_missing=failure is not None,
                        cause="cancellation"
                        if self._cancel_requested
                        else (
                            "deadline-exceeded"
                            if "TIMEOUT" in diagnostic or "WINDOW" in diagnostic
                            else "external"
                        ),
                        diagnostic=diagnostic,
                    )
                except Exception:
                    pass
            self._close_restarts()
            try:
                cleanup = self._cleanup()
            except Exception:
                self.owner.cancel("dispatcher-cleanup-incomplete")
                cleanup = TeardownResult(
                    self.owner._run_id,
                    self.prepared.lifecycle_digest,
                    "dispatcher-terminal",
                    (),
                    True,
                )
                diagnostic = diagnostic or "ML-SCHEDULE-CLEANUP-INCOMPLETE"
            if self._lazy:
                self._terminal_phase = True
                try:
                    plan = self.client.collection
                    collection_end = min(time.monotonic() + plan.collection_seconds,
                                         self._work_end - plan.terminal_seconds,
                                         self.bootstrap._generation / 1e9 - plan.terminal_seconds - plan.drain_seconds)
                    self._collection_receipt = self.client.collect_outputs(
                        self._broker, HostDeadline(self.owner.session, collection_end))
                    if not self._collection_receipt.public_data()['collectionComplete']:
                        diagnostic = diagnostic or "ML-SCHEDULE-COLLECTION-INCOMPLETE"
                except Exception:
                    diagnostic = diagnostic or "ML-SCHEDULE-COLLECTION-INCOMPLETE"
            for step in self.prepared.steps:
                if step.step_id in self._outcomes:
                    continue
                disposition = (
                    "cancelled"
                    if self._cancel_requested
                    else ("failed" if step.step_id in self._pending else "blocked")
                )
                recorded = False
                try:
                    self._send(
                        "step-disposition",
                        HostDeadline(
                            self.owner.session,
                            min(
                                self._work_end,
                                # Terminal-section statement: per-unit budget like run-terminal,
                                # capped by the admitted work window (finding 386).
                                time.monotonic() + self.plan.per_unit_seconds,
                            ),
                        ),
                        step=step.step_id,
                        disposition=disposition,
                        cause="cancellation" if self._cancel_requested else "external",
                    )
                    recorded = True
                except Exception:
                    pass
                self._outcomes[step.step_id] = StepExecution(
                    step.step_id,
                    disposition,
                    self._pending.get(step.step_id, (None, None))[0],
                    None,
                    recorded,
                )
            if not cleanup.unit_cleanup_complete or not cleanup.normal_records_complete:
                diagnostic = diagnostic or "ML-SCHEDULE-CLEANUP-INCOMPLETE"
            succeeded = (
                diagnostic is None
                and cleanup.unit_cleanup_complete
                and cleanup.normal_records_complete
            )
            try:
                for unit in self.prepared.units:
                    self._send(
                        "unit-disposition",
                        HostDeadline(
                            self.owner.session,
                            min(
                                self._work_end,
                                # Terminal-section statement: per-unit budget like run-terminal,
                                # capped by the admitted work window (finding 386).
                                time.monotonic() + self.plan.per_unit_seconds,
                            ),
                        ),
                        unit=unit.unit_id,
                        disposition="completed"
                        if succeeded
                        else ("cancelled" if self._cancel_requested else
                              "blocked" if self._lazy and self._generation(unit.unit_id) == 0 else "unresolved"),
                        cause="normal"
                        if succeeded
                        else ("cancellation" if self._cancel_requested else "external"),
                    )
                self._send(
                    "run-terminal",
                    HostDeadline(
                        self.owner.session,
                        min(
                            self._work_end,
                            # Terminal statement takes the per-unit budget like teardown and
                            # cleanup (finding 379); the operation budget is cadence-bound.
                            time.monotonic() + self.plan.per_unit_seconds,
                        ),
                    ),
                    outcome="succeeded"
                    if succeeded
                    else ("cancelled" if self._cancel_requested else "failed"),
                    cause="normal"
                    if succeeded
                    else ("cancellation" if self._cancel_requested else "external"),
                )
                terminal = True
            except Exception:
                diagnostic = diagnostic or "ML-SCHEDULE-TERMINAL-INCOMPLETE"
            self.owner.cancel("dispatcher-terminal")
            report_receipt = None
            if self._lazy:
                try:
                    report_end = min(time.monotonic() + self.client.collection.terminal_seconds,
                                     self._work_end)
                    report_receipt = self.client.finish_run(
                        self._broker, HostDeadline(self.owner.session, report_end))
                    facts = report_receipt.public_data()
                    if (facts['diagnostic'] is not None or facts['writer'] is None
                        or facts['report'] is None or not facts['report']['eligible']
                        or not facts['writer']['evidence_complete']):
                        diagnostic = diagnostic or 'ML-SCHEDULE-EVIDENCE-INCOMPLETE'
                except Exception:
                    diagnostic = diagnostic or 'ML-SCHEDULE-EVIDENCE-INCOMPLETE'
            self._result = DispatchResult(
                self.owner._run_id,
                self.prepared.lifecycle_digest,
                succeeded and terminal,
                tuple(self._outcomes[s.step_id] for s in self.prepared.steps),
                cleanup,
                terminal,
                diagnostic,
                self.health_scans,
                self.lease_renewals,
                self._collection_receipt,
                report_receipt,
            )
            return self._result
        finally:
            self._close_restarts()
            for lock in reversed(locks):
                lock.release()
            if claimed:
                self.owner._dispatch_owner = self.owner._dispatch_thread = None
            self._lock.release()

    def cancel(self, reason="dispatcher-cancel"):
        super()._holder()
        self._cancel_requested = True
        self._pins[1].cancel(reason)
