"""Original-worker finite tick source and schedule evidence; no launch authority."""

from datetime import datetime, timezone
from dataclasses import replace, asdict
import re
from xverse_xdl.lifecycle import OwnedResourceHandle
from xverse_xdl.models import freeze
from .lifecycle_evidence import _digest, _parents
import hashlib
import math
import time

from .persistence import PersistenceError


class ScheduleJournal:
    def __init__(self, evidence, plan, teardown=None):
        self.evidence, self.plan = evidence, plan
        self.cursor, self.tick, self.pending = 0, 0, None
        self.sequence = 0
        self.last_event = None
        self.teardown = teardown
        self.full = self.closing = self.terminal = False
        self.steps, self.completed, self.units, self.failures, self.handles = (
            {},
            set(),
            {},
            set(),
            {},
        )
        self.dispositions = {}
        self.request_sequence = 0
        self.lazy = getattr(evidence, 'collection_source', None) is not None
        self.retired_handles = {}

    def validate_generation(self, body, claims):
        """Reject a live logical step before successor permit consumption."""
        if not self.lazy:
            return
        unit = body.get('unit')
        if (type(unit) is not str or unit not in claims or not self.full
            or self.closing or self.terminal or self.pending is None
            or type(body.get('generation')) is not int
            or body['generation'] != self._generation(unit, claims) + 1
            or unit not in self.handles
            or asdict(self.handles[unit]) != body.get('handle')
            or any(s.unit_id == unit and s.step_id in self.steps and s.step_id not in self.completed
                   for s in self.evidence.permits._prepared.steps)):
            raise PersistenceError('ML-SCHEDULE-GENERATION-PHASE')

    def commit_generation(self, body, claims):
        """Called only after the original generation operation durably succeeded."""
        if not self.lazy:
            return
        unit, generation = body['unit'], body['generation']
        old = self.handles.get(unit)
        if (old is None or asdict(old) != body['handle']
            or self._generation(unit, claims) != generation):
            raise PersistenceError('ML-SCHEDULE-GENERATION-ORIGINAL')
        self.retired_handles[unit, generation - 1] = old
        del self.handles[unit]

    def _generation(self, unit, claims):
        claim = claims.get(unit)
        if claim is not None:
            saved = self.evidence.permits._issued.get(id(claim.receipt))
            if saved is None or saved[0] is not claim.receipt:
                raise PersistenceError("ML-SCHEDULE-CLAIM")
            return saved[1].details['generation']
        if self.lazy and unit not in self.evidence.start_attempts:
            return 0
        return next(b.generation for u, b, a in self.evidence.permits._checked if u.unit_id == unit)

    def _logical_source(self, unit, phase, kind, status, details, claims, deadline, check):
        if self.lazy and unit not in claims:
            # No M3 record can be attributed to a permit which was never consumed.
            return None
        return self._m3(unit, phase, kind, status, details, claims, deadline, check)

    def admit_start_claim(self, unit):
        if not self.lazy:
            return
        step = next((s for s in self.evidence.permits._prepared.steps
                     if s.unit_id == unit and s.phase == 'start'), None)
        state = self.steps.get(step.step_id) if step else None
        if (not self.full or self.closing or self.terminal or self.pending is None
            or state is None or not state.get('logical') or state.get('claim_attempted')
            or step.step_id in self.completed
            or not step.at_ticks <= self.tick <= step.latest_ticks):
            raise PersistenceError('ML-SCHEDULE-START-CLAIM')
        state['claim_attempted'] = True

    def pull(self, body, deadline, check):
        check(deadline)
        if self.closing or self.terminal:
            raise PersistenceError("ML-SCHEDULE-CLOSED")
        if (
            type(body) is not dict
            or set(body) != {"index", "previous"}
            or type(body["index"]) is not int
            or body["index"] != self.cursor + 1
            or type(body["previous"]) is not int
            or body["previous"] != self.tick
            or self.pending is not None
            or self.cursor >= len(self.plan.ticks)
        ):
            raise PersistenceError("ML-SCHEDULE-TICK-REQUEST")
        self.tick = self.plan.ticks[self.cursor]
        self.pending = self.cursor + 1
        return {
            "index": self.pending,
            "tick": self.tick,
            "schedule_digest": self.plan.digest,
        }

    def record(self, body, claims, operation, deadline, check):
        check(deadline)
        if type(body) is dict and body.get("kind") != "tick-complete":
            return self._control(body, claims, operation, deadline, check)
        if self.closing or self.terminal:
            raise PersistenceError("ML-SCHEDULE-CLOSED")
        if (
            type(body) is not dict
            or set(body) != {"kind", "index", "tick", "observed_at"}
            or body["kind"] != "tick-complete"
            or type(body["index"]) is not int
            or body["index"] != self.pending
            or type(body["tick"]) is not int
            or body["tick"] != self.tick
        ):
            raise PersistenceError("ML-SCHEDULE-TICK-RECORD")
        if self.full:
            prepared = self.evidence.permits._prepared
            eligible = prepared.eligible_steps(self.tick, self.completed)
            if any(
                s.step_id not in self.steps and self._admissible(s, claims)
                for s in eligible
            ) or any(
                state["due"] <= self.tick
                for key, state in self.steps.items()
                if key not in self.completed
            ):
                raise PersistenceError("ML-SCHEDULE-TICK-UNFINISHED")
        payload = {
            "schemaVersion": "2.0",
            "lifecycleDigest": "sha256:" + self.plan.lifecycle_digest,
            "runId": self.evidence.permits._run_id,
            "sessionId": deadline.session,
            "scope": "run",
            "unitId": None,
            "generation": 0,
            "operationId": operation,
            "action": "validate",
            "outcome": "succeeded",
            "obligationId": "tick-" + str(self.pending),
            "sourceRefs": [
                {
                    "kind": "admitted-lifecycle",
                    "id": "schedule-admission",
                    "sequence": 0,
                    "sha256": "sha256:"
                    + hashlib.sha256(self.plan.canonical_bytes).hexdigest(),
                }
            ],
            "dependencies": [],
        }
        fields = self._append(payload, body["observed_at"], claims, deadline, check)
        self.cursor += 1
        self.pending = None
        return {
            "kind": "tick-complete",
            "index": self.cursor,
            "tick": self.tick,
            "event": fields,
        }

    def _append(
        self,
        payload,
        observed_at,
        claims,
        deadline,
        check,
        *,
        suffix="schedule",
        cause=None,
    ):
        try:
            valid = (
                type(observed_at) in (int, float)
                and math.isfinite(observed_at)
                and 0 <= time.monotonic() - observed_at <= 5
            )
        except OverflowError:
            valid = False
        if not valid:
            raise PersistenceError("ML-SCHEDULE-OBSERVATION")
        self.evidence.history = self.evidence._history(claims)
        self.evidence._mirrors(claims)
        self.evidence.reserve_event(claims)
        check(deadline)
        now = datetime.now(timezone.utc)
        fields = {
            "eventId": payload["operationId"] + "-" + suffix,
            "producerId": "maestro.scheduler14",
            "eventKind": "annotation",
            "producerSequence": self.sequence + 1,
            "correlationId": self.evidence.permits._run_id,
            "causationId": cause if cause is not None else self.last_event,
            "clocks": {
                "host": {
                    "domain": "host:" + deadline.session,
                    "unit": "s",
                    "value": observed_at,
                },
                "utc": {
                    "domain": "utc:" + deadline.session,
                    "unit": "s",
                    "value": now.timestamp(),
                },
                "simulation": {
                    "domain": self.evidence.permits._prepared.clock.domain,
                    "unit": "tick",
                    "value": self.tick,
                },
            },
            "annotation": {"text": "Maestro scheduled " + payload["action"]},
            "extensions": {"xverse.maestro": payload},
        }
        ordinal = self.evidence.writer.append_event(
            event_id=fields["eventId"],
            producer_id=fields["producerId"],
            event_kind="annotation",
            producer_sequence=fields["producerSequence"],
            correlation_id=fields["correlationId"],
            causation_id=fields["causationId"],
            clocks=fields["clocks"],
            annotation=fields["annotation"],
            extensions=fields["extensions"],
        )
        check(deadline)
        self.evidence.writer.flush_buffer()
        check(deadline)
        fields["ingestionOrdinal"] = ordinal
        self.evidence.events[fields["eventId"]] = fields
        self.evidence._mirrors(claims)
        check(deadline)
        self.sequence += 1
        self.last_event = fields["eventId"]
        return fields

    def _payload(
        self,
        operation,
        session,
        *,
        unit=None,
        step=None,
        action,
        outcome,
        refs=None,
        generation=0,
        **extra,
    ):
        value = {
            "schemaVersion": "2.0",
            "lifecycleDigest": "sha256:" + self.plan.lifecycle_digest,
            "runId": self.evidence.permits._run_id,
            "sessionId": session,
            "scope": "step" if step else ("unit" if unit else "run"),
            "unitId": unit,
            "generation": generation,
            "operationId": operation,
            "action": action,
            "outcome": outcome,
            "dependencies": [],
            "sourceRefs": refs
            or [
                {
                    "kind": "admitted-lifecycle",
                    "id": "schedule-admission",
                    "sequence": 0,
                    "sha256": "sha256:"
                    + hashlib.sha256(self.plan.canonical_bytes).hexdigest(),
                }
            ],
        }
        if step:
            value["stepId"] = step
        value.update(extra)
        return value

    def _handle(self, unit, body, claims):
        try:
            handle = OwnedResourceHandle(**body)
        except (ValueError, TypeError) as error:
            raise PersistenceError("ML-SCHEDULE-HANDLE") from error
        claim = claims.get(unit)
        target = next(
            (u for u in self.evidence.permits._prepared.units if u.unit_id == unit),
            None,
        )
        if claim is None or target is None:
            raise PersistenceError("ML-SCHEDULE-UNIT")
        start = next(a for a in target.plan.actions if a.phase == "start")
        if (
            (
                handle.execution_id,
                handle.action_id,
                handle.provider_id,
                handle.provider_kind,
            )
            != (
                claim.receipt.execution_id,
                start.action_id,
                target.plan.provider_id,
                target.plan.provider_kind,
            )
            or type(handle.opaque_id) is not str
            or re.fullmatch("[0-9a-f]{64}", handle.opaque_id) is None
            or type(handle.resource_identity) is not str
            or re.fullmatch("maestro-boundary:[0-9a-f]{64}", handle.resource_identity)
            is None
            or (unit in self.handles and self.handles[unit] != handle)
        ):
            raise PersistenceError("ML-SCHEDULE-HANDLE")
        if self.lazy:
            issued = self.evidence.issued_handles.get((unit, self._generation(unit, claims)))
            if issued is None or issued[0] != handle:
                raise PersistenceError("ML-SCHEDULE-ORIGINAL-HANDLE")
        self.handles[unit] = handle
        return handle

    def _m3(self, unit, phase, kind, status, details, claims, deadline, check):
        self.evidence.reserve_event(claims)
        before = self.evidence._history(claims)
        self.evidence._mirrors(claims)
        claim = claims.get(unit)
        if claim is None:
            raise PersistenceError("ML-SCHEDULE-CLAIM")
        saved = self.evidence.permits._issued[id(claim.receipt)][1]
        target = next(
            u for u in self.evidence.permits._prepared.units if u.unit_id == unit
        )
        action = next(a for a in target.plan.actions if a.phase == phase)
        record = replace(
            saved,
            sequence=0,
            kind=kind,
            action_id=action.action_id,
            status=status,
            permit_nonce=None,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=freeze(
                {
                    "maestroRunId": self.evidence.permits._run_id,
                    "maestroUnitId": unit,
                    "generation": saved.details["generation"],
                    "lifecycleDigest": self.plan.lifecycle_digest,
                    "schedule": details,
                }
            ),
        )
        check(deadline)
        self.evidence.permits._journal.append(record)
        check(deadline)
        actual = self.evidence.permits._journal.records
        if actual != (*before, replace(record, sequence=len(before) + 1)):
            raise PersistenceError("ML-SCHEDULE-M3-ACK")
        self.evidence.history = actual
        public = next(
            r
            for r in self.evidence.permits._journal.public_records()
            if r["sequence"] == len(actual)
        )
        return {
            "kind": "m3-record",
            "id": "m3-record-" + str(len(actual)),
            "sequence": len(actual),
            "sha256": _digest(public),
        }

    def _phase_source(self, step):
        unit = step.unit_id
        if step.phase in ("start", "observe"):
            sample = self.evidence.samples.get(unit)
            if (
                sample is None
                or not sample["ready"]
                or not sample["started"]
                or not 0
                <= time.monotonic() - sample["observed_at"]
                <= sample["freshness"]
                or sample["handle"] != self.handles[unit]
                or (self.teardown and self.teardown.states.get(unit, {}).get("stopped"))
            ):
                raise PersistenceError("ML-SCHEDULE-NO-READINESS")
            event = self.evidence.events[sample["event"]]
        elif step.phase in ("stop", "cleanup"):
            state = self.teardown.states.get(unit, {}) if self.teardown else {}
            if not state.get("stopped" if step.phase == "stop" else "cleaned"):
                raise PersistenceError("ML-SCHEDULE-NO-TEARDOWN")
            event = self.evidence.events[state["event"]]
            if event["extensions"]["xverse.maestro"]["action"] != step.phase:
                raise PersistenceError("ML-SCHEDULE-NO-TEARDOWN")
        else:
            return None, None
        return event["extensions"]["xverse.maestro"]["sourceRefs"][0], event["eventId"]

    def _control(self, body, claims, operation, deadline, check):
        kind = body.get("kind")
        try:
            observed = body.get("observed_at")
            valid = (
                type(observed) in (int, float)
                and math.isfinite(observed)
                and 0 <= time.monotonic() - observed <= 5
            )
        except OverflowError:
            valid = False
        if not valid:
            raise PersistenceError("ML-SCHEDULE-OBSERVATION")
        if "cause" in body and body["cause"] not in (
            "normal",
            "journal-failure",
            "argus-failure",
            "cancellation",
            "readiness-failure",
            "issuer-loss",
            "deadline-exceeded",
            "external",
        ):
            raise PersistenceError("ML-SCHEDULE-CAUSE")
        events = []
        prepared = self.evidence.permits._prepared
        if self.terminal:
            raise PersistenceError("ML-SCHEDULE-TERMINAL")

        def emit(
            action,
            outcome,
            *,
            unit=None,
            step=None,
            refs=None,
            suffix="schedule",
            causation=None,
            **extra,
        ):
            generation = 0
            if unit is not None:
                generation = self._generation(unit, claims)
            payload = self._payload(
                operation,
                deadline.session,
                unit=unit,
                step=step,
                action=action,
                outcome=outcome,
                refs=refs,
                generation=generation,
                **extra,
            )
            event = self._append(
                payload,
                body["observed_at"],
                claims,
                deadline,
                check,
                suffix=suffix,
                cause=causation,
            )
            events.append(event)
            return event

        if kind == "begin":
            if (
                set(body) != {"kind", "observed_at"}
                or self.full
                or self.cursor
                or self.pending
                or (bool(claims or self.evidence.start_attempts) if self.lazy
                    else set(claims) != {u.unit_id for u in prepared.units})
                or self.evidence.samples
                or (self.teardown and self.teardown.states)
                or self.request_sequence
                + self.plan.required_requests
                - (1 if self.lazy else 1 + 2 * len(prepared.units))
                - 1
                > self.plan.request_limit
            ):
                raise PersistenceError("ML-SCHEDULE-BEGIN")
            emit("validate", "succeeded", suffix="begin")
            self.full = True
        elif not self.full:
            raise PersistenceError("ML-SCHEDULE-NOT-BEGUN")
        elif kind in ("step-dispatch", "step-complete"):
            if (
                set(body) != {"kind", "step", "index", "tick", "observed_at", "handle"}
                or self.closing
                or type(body["tick"]) is not int
                or body["tick"] != self.tick
                or type(body["index"]) is not int
                or body["index"] != self.pending
            ):
                raise PersistenceError("ML-SCHEDULE-STEP-REQUEST")
            step = next((s for s in prepared.steps if s.step_id == body["step"]), None)
            if step is None:
                raise PersistenceError("ML-SCHEDULE-STEP")
            logical = self.lazy and body['handle'] is None
            if logical:
                if (step.unit_id in claims or step.unit_id in self.evidence.start_attempts
                    or not (step.phase == 'prepare' or kind == 'step-dispatch' and step.phase == 'start')):
                    raise PersistenceError("ML-SCHEDULE-HANDLE")
            else:
                self._handle(step.unit_id, body["handle"], claims)
            if kind == "step-dispatch":
                if (
                    not self._admissible(step, claims)
                    or self.tick + step.duration_ticks > step.latest_ticks
                    or step.step_id in self.steps
                    or step not in prepared.eligible_steps(self.tick, self.completed)
                ):
                    raise PersistenceError("ML-SCHEDULE-STEP-ORDER")
                source = self._logical_source(
                    step.unit_id,
                    step.phase,
                    "intent",
                    "pending",
                    {"step": step.step_id, "tick": self.tick, "kind": kind},
                    claims,
                    deadline,
                    check,
                )
                emit(
                    "validate" if logical else "intent",
                    "pending",
                    unit=step.unit_id,
                    step=step.step_id,
                    refs=[source] if source else None,
                    suffix="dispatch",
                )
                self.steps[step.step_id] = {"due": self.tick + step.duration_ticks, 'logical': logical}
            else:
                state = self.steps.get(step.step_id)
                if (
                    state is None
                    or step.step_id in self.completed
                    or not state["due"] <= self.tick <= step.latest_ticks
                ):
                    raise PersistenceError("ML-SCHEDULE-STEP-WINDOW")
                actual, cause = self._phase_source(step)
                phase_fields = {}
                start_source = None
                if step.phase in ('start', 'observe', 'stop', 'cleanup'):
                    phase_fields['handleRef'] = 'handle-' + _digest([
                        self.evidence.permits._run_id, asdict(self.handles[step.unit_id])])[7:]
                if step.phase in ('start', 'observe'):
                    dependencies = []
                    for parent in _parents(prepared, step.unit_id):
                        sample = self.evidence.samples.get(parent)
                        if (sample is None or not sample['ready']
                            or not 0 <= body['observed_at'] - sample['observed_at'] <= sample['freshness']):
                            raise PersistenceError('ML-SCHEDULE-NO-READINESS')
                        dependencies.append(dict(unitId=parent, generation=sample['generation'],
                                                 probeEventId=sample['event']))
                    phase_fields['dependencies'] = dependencies
                if step.phase == 'start':
                    started = [event for event in self.evidence.events.values()
                        if (p := event['extensions']['xverse.maestro'])['scope'] == 'unit'
                        and p['unitId'] == step.unit_id and p['generation'] == self._generation(step.unit_id, claims)
                        and p['action'] == 'started' and p['outcome'] == 'succeeded']
                    if len(started) != 1:
                        raise PersistenceError('ML-SCHEDULE-NO-START')
                    start_source = started[0]['extensions']['xverse.maestro']['sourceRefs'][0]
                source = self._logical_source(
                    step.unit_id,
                    step.phase,
                    "outcome",
                    "completed",
                    {"step": step.step_id, "tick": self.tick, "kind": kind},
                    claims,
                    deadline,
                    check,
                )
                refs = ([source] if source else []) + ([actual] if actual else []) + ([start_source] if start_source else [])
                action = {
                    "prepare": "validate",
                    "start": "started",
                    "observe": "probe",
                    "stop": "stop",
                    "cleanup": "cleanup",
                }[step.phase]
                phase_event = emit(
                    action,
                    "succeeded",
                    unit=step.unit_id,
                    step=step.step_id,
                    refs=refs or None,
                    suffix="phase",
                    causation=cause,
                    **phase_fields,
                    **({"probeId": "running"} if action == "probe" else {}),
                )
                emit(
                    "disposition",
                    "succeeded",
                    unit=step.unit_id,
                    step=step.step_id,
                    refs=[source] if source else None,
                    suffix="disposition",
                    causation=phase_event["eventId"],
                    disposition="completed",
                )
                self.completed.add(step.step_id)
                self.dispositions[step.step_id] = "completed"
        elif kind == "failure":
            unit = body.get("unit")
            if (
                set(body)
                != {
                    "kind",
                    "unit",
                    "phase",
                    "observation_missing",
                    "cause",
                    "diagnostic",
                    "observed_at",
                }
                or unit in self.failures
                or (unit is not None and unit not in {u.unit_id for u in prepared.units})
                or (not self.lazy and unit is not None and unit not in claims)
                or body["phase"]
                not in ("prepare", "start", "observe", "stop", "cleanup")
                or type(body["observation_missing"]) is not bool
                or (body["observation_missing"] and unit is None)
                or type(body["diagnostic"]) is not str
                or re.fullmatch("ML-[A-Z-]+", body["diagnostic"]) is None
            ):
                raise PersistenceError("ML-SCHEDULE-FAILURE")
            refs = None
            if unit is not None:
                source = self._logical_source(
                    unit,
                    body["phase"],
                    "observation",
                    "unknown" if body["observation_missing"] else "failed",
                    {
                        "kind": kind,
                        "diagnostic": body["diagnostic"],
                        "observationMissing": body["observation_missing"],
                    },
                    claims,
                    deadline,
                    check,
                )
                refs = [source] if source else None
            emit(
                "cancel"
                if body["cause"] == "cancellation"
                else ("health-loss" if body["observation_missing"] else "validate"),
                "cancelled"
                if body["cause"] == "cancellation"
                else ("unknown" if body["observation_missing"] else "failed"),
                unit=unit,
                refs=refs,
                cause=body["cause"],
                diagnosticCode=body["diagnostic"],
                **({"probeId": "running"} if body["observation_missing"] else {}),
                # The lost observation names the handle issued for the unit's current generation (F-10, findings 441, 445).
                **({"handleRef": "handle-" + _digest([self.evidence.permits._run_id, asdict(
                    self.evidence.issued_handles[unit, self._generation(unit, claims)][0])])[7:]}
                   if body["observation_missing"] and unit is not None
                   and (unit, self._generation(unit, claims)) in self.evidence.issued_handles else {}),
            )
            self.failures.add(unit)
            self.closing = True
        elif kind == "step-disposition":
            if set(body) != {"kind", "step", "disposition", "cause", "observed_at"}:
                raise PersistenceError("ML-SCHEDULE-DISPOSITION")
            step = next((s for s in prepared.steps if s.step_id == body["step"]), None)
            if (
                step is None
                or step.step_id in self.completed
                or body["disposition"]
                not in ("failed", "blocked", "cancelled", "unresolved")
            ):
                raise PersistenceError("ML-SCHEDULE-DISPOSITION")
            if body["disposition"] == "failed" and step.step_id not in self.steps:
                raise PersistenceError("ML-SCHEDULE-DISPOSITION")
            self.closing = True
            source = self._logical_source(
                step.unit_id,
                step.phase,
                "outcome",
                body["disposition"],
                {"step": step.step_id, "kind": kind, "cause": body["cause"]},
                claims,
                deadline,
                check,
            )
            emit(
                "disposition",
                {
                    "failed": "failed",
                    "blocked": "skipped",
                    "cancelled": "cancelled",
                    "unresolved": "unresolved",
                }[body["disposition"]],
                unit=step.unit_id,
                step=step.step_id,
                refs=[source] if source else None,
                disposition=body["disposition"],
                cause=body["cause"],
            )
            self.completed.add(step.step_id)
            self.dispositions[step.step_id] = body["disposition"]
        elif kind == "unit-disposition":
            if (
                set(body) != {"kind", "unit", "disposition", "cause", "observed_at"}
                or body["unit"] in self.units
                or body["unit"] not in {u.unit_id for u in prepared.units}
                or not self.lazy and body['unit'] not in claims
            ):
                raise PersistenceError("ML-SCHEDULE-UNIT-DISPOSITION")
            unit = body["unit"]
            disposition = body["disposition"]
            if disposition not in (
                "completed",
                "failed",
                "cancelled",
                "blocked",
                "unresolved",
            ):
                raise PersistenceError("ML-SCHEDULE-UNIT-DISPOSITION")
            if disposition == "completed" and (
                not self.teardown.states.get(unit, {}).get("cleaned")
                or any(
                    self.dispositions.get(s.step_id) != "completed"
                    for s in prepared.steps
                    if s.unit_id == unit
                )
            ):
                raise PersistenceError("ML-SCHEDULE-UNIT-DISPOSITION")
            source = self._logical_source(
                unit,
                "cleanup",
                "observation",
                disposition,
                {"kind": kind, "cause": body["cause"]},
                claims,
                deadline,
                check,
            )
            emit(
                "disposition",
                {
                    "completed": "succeeded",
                    "failed": "failed",
                    "blocked": "skipped",
                    "cancelled": "cancelled",
                    "unresolved": "unresolved",
                }[disposition],
                unit=unit,
                refs=[source] if source else None,
                disposition=disposition,
                cause=body["cause"],
            )
            self.units[unit] = disposition
            if disposition != "completed":
                self.closing = True
        elif kind == "run-terminal":
            if set(body) != {"kind", "outcome", "cause", "observed_at"} or body[
                "outcome"
            ] not in ("succeeded", "failed", "cancelled", "unresolved"):
                raise PersistenceError("ML-SCHEDULE-RUN-TERMINAL")
            if set(self.units) != {u.unit_id for u in prepared.units} or self.completed != {
                s.step_id for s in prepared.steps
            }:
                raise PersistenceError("ML-SCHEDULE-RUN-TERMINAL")
            if body["outcome"] == "succeeded" and (
                self.closing
                or self.cursor != len(self.plan.ticks)
                or any(v != "completed" for v in self.units.values())
            ):
                raise PersistenceError("ML-SCHEDULE-RUN-TERMINAL")
            event = emit(
                "run-terminal", body["outcome"], suffix="terminal", cause=body["cause"]
            )
            emit(
                "disposition",
                body["outcome"],
                suffix="disposition",
                causation=event["eventId"],
                cause=body["cause"],
                disposition={
                    "succeeded": "completed",
                    "failed": "failed",
                    "cancelled": "cancelled",
                    "unresolved": "unresolved",
                }[body["outcome"]],
            )
            self.closing = self.terminal = True
        else:
            raise PersistenceError("ML-SCHEDULE-REQUEST")
        return {
            "kind": kind,
            "events": events,
            "m3_sequence": len(self.evidence.history),
        }

    def _admissible(self, step, claims):
        if step.phase == "stop":
            return self._admissible_stop(step.unit_id, claims)
        if step.phase == "cleanup":
            return self.teardown.states.get(step.unit_id, {}).get("stopped") or (
                self.tick == self.evidence.permits._prepared.clock.horizon_ticks
                and self._admissible_stop(step.unit_id, claims)
                and not any(
                    s.unit_id == step.unit_id and s.phase == "stop"
                    for s in self.evidence.permits._prepared.steps
                )
            )
        return True

    def _admissible_stop(self, unit, claims):
        return all(
            self.teardown.states.get(other, {}).get("cleaned")
            for other in claims
            if other != unit
            and unit in _parents(self.evidence.permits._prepared, other)
        )
