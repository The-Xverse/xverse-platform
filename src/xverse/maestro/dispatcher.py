"""Finite declared lifecycle over already-issued original resources (partial U5).

Host health/lease service is independent of the supervised finite tick source.
Execution facts never establish full admission, helper closure or U7/U8 coverage.
"""

from dataclasses import asdict, dataclass, field
import json
import math
import re
import select
import threading
import time

from xverse.argus.schema import canonical_bytes
from .admission import _verify_prepared
from .bootstrap import BootstrapSession
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
            expected = [("intent", "pending", None, "dispatch")]
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
            "generation": 1 if unit else 0,
            "operationId": operation,
            "action": action,
            "outcome": outcome,
            "dependencies": [],
        }
        if step:
            base["stepId"] = step
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
                import hashlib

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
    def __init__(self, facade, bootstrap, *, gates):
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
        if (
            self.plan is None
            or getattr(self.client.process, "_root", None) is not bootstrap
            or tuple(facade._policies.values()) != self.plan.policies
            or self.client._sequence
            + self.plan.required_requests
            - (1 + 2 * len(self.prepared.units))
            > self.client._request_limit
            or facade._released
            or facade._attempted
            or bootstrap.boundaries is not self.owner.supervisor.boundaries
            or set(facade._bindings) != {u.unit_id for u in self.prepared.units}
        ):
            raise OwnerError("ML-SCHEDULE-ADMISSION")
        self.gates = dict(gates)
        if len(self.gates) != len(gates) or set(self.gates) != set(facade._bindings):
            raise OwnerError("ML-SCHEDULE-GATES")
        self._bindings = tuple(facade._bindings.items())
        self._gate_pins = tuple(self.gates.items())
        for unit, binding in self._bindings:
            gate = self.gates[unit]
            if (
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
        ):
            raise OwnerError("ML-SCHEDULE-REPLACED")
        self.facade._holder()
        self.bootstrap._holder()

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

    def _end(self, *, terminal=False):
        now = time.monotonic()
        end = min(
            self._work_end if terminal else self._active_end,
            now + self.plan.operation_seconds,
        )
        end = min(end, self.bootstrap._lease / 1e9)
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
        if self.owner.latch.cancelled:
            raise OwnerError("ML-SCHEDULE-CANCELLED")
        limit = self._work_end if terminal else self._active_end
        renew_budget = (len(self.gates) + 1) * self.plan.operation_seconds
        renew_margin = renew_budget + self.plan.operation_seconds
        leases = [self.bootstrap._lease / 1e9] + [
            g.lease_ns / 1e9
            for u, g in self.gates.items()
            if u not in self.teardown._stopped
        ]
        health = self.facade.next_health_deadline
        service = self.plan.health_scan_seconds + renew_margin
        if health and time.monotonic() >= health.monotonic_seconds - service:
            if self.health_scans >= self.plan.health_slots:
                raise OwnerError("ML-SCHEDULE-HEALTH-CAPACITY")
            until = min(limit, health.monotonic_seconds, min(leases) - renew_budget)
            if until <= time.monotonic():
                raise OwnerError("ML-SCHEDULE-SERVICE-DEADLINE")
            self.facade.check_health(
                HostDeadline(self.owner.session, until), force=True
            )
            self.health_scans += 1
        now = time.monotonic()
        if min(leases) - now <= renew_margin:
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
        binding = self.facade._bindings[step.unit_id]
        return self._send(
            kind,
            self._end(terminal=terminal),
            step=step.step_id,
            index=self._index,
            tick=self._tick,
            handle=asdict(binding.handle),
        )

    def _effect(self, step):
        until = self._end()
        unit = step.unit_id
        binding = self.facade._bindings[unit]
        if step.phase == "prepare":
            _verify_prepared(
                self.prepared, self.client._result_input, self.client._resources
            )
        elif step.phase == "start":
            self.facade.start(
                unit, binding.launcher.recipe.descriptor, self.gates[unit], until
            )
        elif step.phase == "observe":
            self.facade.check_health(until, force=True)
        else:
            if step.phase == "cleanup" and unit not in self.teardown._stopped:
                stopped = self.teardown.phase(unit, "stop", until)
                if stopped.emergency:
                    raise OwnerError("ML-SCHEDULE-TEARDOWN-INCOMPLETE")
            result = self.teardown.phase(unit, step.phase, until)
            if result.emergency:
                raise OwnerError("ML-SCHEDULE-TEARDOWN-INCOMPLETE")

    def _cleanup(self):
        try:
            if not self.owner.latch.cancelled:
                for unit in self.teardown._order():
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
            other in self.teardown._cleaned
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
            if (
                not 0
                < active_deadline.monotonic_seconds - now
                <= self.plan.active_seconds
                or terminal_deadline.monotonic_seconds
                < active_deadline.monotonic_seconds + self.plan.terminal_reserve_seconds
                or terminal_deadline.monotonic_seconds
                > self.bootstrap._generation / 1e9
                or self.client._sequence
                + self.plan.required_requests
                - (1 + 2 * len(self.prepared.units))
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
            self._scope = scope
            diagnostic = None
            terminal = False
            current = None
            try:
                self._send("begin", self._end())
                for index in range(1, len(self.plan.ticks) + 1):
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
                        select.select(
                            [],
                            [],
                            [],
                            min(self.plan.poll_seconds, max(0, end - time.monotonic())),
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
                                time.monotonic() + self.plan.operation_seconds,
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
                diagnostic = "ML-SCHEDULE-CLEANUP-INCOMPLETE"
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
                                time.monotonic() + self.plan.operation_seconds,
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
                                time.monotonic() + self.plan.operation_seconds,
                            ),
                        ),
                        unit=unit.unit_id,
                        disposition="completed"
                        if succeeded
                        else ("cancelled" if self._cancel_requested else "unresolved"),
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
                            time.monotonic() + self.plan.operation_seconds,
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
            )
            return self._result
        finally:
            for lock in reversed(locks):
                lock.release()
            if claimed:
                self.owner._dispatch_owner = self.owner._dispatch_thread = None
            self._lock.release()

    def cancel(self, reason="dispatcher-cancel"):
        super()._holder()
        self._cancel_requested = True
        self._pins[1].cancel(reason)
