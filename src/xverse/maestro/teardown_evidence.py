"""Original-worker normal stop/cleanup records; not run/evidence closure."""

from dataclasses import dataclass, field, replace, asdict
from datetime import datetime, timezone
import math
import re
import time
from xverse_xdl.lifecycle import OwnedResourceHandle
from xverse_xdl.models import freeze
from .lifecycle_evidence import _digest, _parents
from .persistence import PersistenceError


@dataclass(frozen=True)
class TeardownReceipt:
    unit_id: str
    phase: str
    stage: str
    operation: str
    event_id: str
    m3_sequence: int
    public_bytes: bytes = field(repr=False)
    lifecycle_complete: bool = field(default=False, init=False)


def public_step(body):
    return {
        k: body[k]
        for k in (
            "unit",
            "generation",
            "phase",
            "stage",
            "step",
            "session",
            "observed_at",
            "boundary_digest",
            "leader_reaped",
            "empty",
            "released",
            "force_observed",
        )
    } | {"handle_digest": _digest(body["handle"])}


class TeardownJournal:
    def __init__(self, evidence):
        self.evidence = evidence
        self.pending = {}
        self.states = {}
        self.handles = {}
        self.sequence = 0

    def record(self, body, claims, operation, deadline, check):
        keys = {
            "unit",
            "claim",
            "generation",
            "phase",
            "stage",
            "handle",
            "step",
            "intent",
            "session",
            "observed_at",
            "boundary_digest",
            "leader_reaped",
            "empty",
            "released",
            "force_observed",
        }
        if set(body) != keys:
            raise PersistenceError("ML-TEARDOWN-RECORD-INPUT")
        check(deadline)
        unit_id, phase, stage = body["unit"], body["phase"], body["stage"]
        claim = claims.get(unit_id)
        if (
            claim is None
            or body["claim"] != claim.operation
            or phase not in ("stop", "cleanup")
            or stage not in ("intent", "outcome")
        ):
            raise PersistenceError("ML-TEARDOWN-RECORD-SCOPE")
        if (
            type(body["generation"]) is not int
            or body["generation"] != 1
            or body["session"] != deadline.session
            or type(body["step"]) is not str
            or re.fullmatch("td-[0-9a-f]{32}", body["step"]) is None
            or type(body["boundary_digest"]) is not str
            or re.fullmatch("sha256:[0-9a-f]{64}", body["boundary_digest"]) is None
        ):
            raise PersistenceError("ML-TEARDOWN-RECORD-SCOPE")
        try:
            valid = (
                type(body["observed_at"]) in (int, float)
                and math.isfinite(body["observed_at"])
                and 0 <= time.monotonic() - body["observed_at"] <= 5
            )
        except OverflowError:
            valid = False
        if not valid or any(
            type(body[k]) is not bool
            for k in ("leader_reaped", "empty", "released", "force_observed")
        ):
            raise PersistenceError("ML-TEARDOWN-RECORD-OBSERVATION")
        try:
            handle = OwnedResourceHandle(**body["handle"])
        except (TypeError, ValueError) as error:
            raise PersistenceError("ML-TEARDOWN-RECORD-HANDLE") from error
        permits = self.evidence.permits
        unit = next(u for u in permits._prepared.units if u.unit_id == unit_id)
        start = next(a for a in unit.plan.actions if a.phase == "start")
        action = next(a for a in unit.plan.actions if a.phase == phase)
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
                unit.plan.provider_id,
                unit.plan.provider_kind,
            )
            or type(handle.opaque_id) is not str
            or re.fullmatch("[0-9a-f]{64}", handle.opaque_id) is None
            or type(handle.resource_identity) is not str
            or re.fullmatch("maestro-boundary:[0-9a-f]{64}", handle.resource_identity)
            is None
        ):
            raise PersistenceError("ML-TEARDOWN-RECORD-HANDLE")
        previous = self.handles.get(unit_id)
        sample = self.evidence.samples.get(unit_id)
        if (previous is not None and previous != (handle, body["boundary_digest"])) or (
            sample is not None and sample["handle"] != handle
        ):
            raise PersistenceError("ML-TEARDOWN-RECORD-HANDLE")
        state = self.states.setdefault(unit_id, {"stopped": False, "cleaned": False})
        key = unit_id, phase
        if stage == "intent":
            if (
                body["intent"] is not None
                or key in self.pending
                or state["cleaned"]
                or (phase == "stop" and state["stopped"])
                or (phase == "cleanup" and not state["stopped"])
            ):
                raise PersistenceError("ML-TEARDOWN-RECORD-ORDER")
            if any(
                body[k]
                for k in ("leader_reaped", "empty", "released", "force_observed")
            ):
                raise PersistenceError("ML-TEARDOWN-RECORD-OBSERVATION")
            if phase == "stop" and any(
                unit_id in _parents(permits._prepared, other)
                and not self.states.get(other, {}).get("cleaned")
                for other in claims
                if other != unit_id
            ):
                raise PersistenceError("ML-TEARDOWN-RECORD-DEPENDENTS")
        else:
            if (
                body["intent"] != self.pending.get(key)
                or key not in self.pending
                or not body["leader_reaped"]
                or not body["empty"]
                or body["released"] != (phase == "cleanup")
            ):
                raise PersistenceError("ML-TEARDOWN-RECORD-OBSERVATION")
            if (phase == "stop" and state["stopped"]) or (
                phase == "cleanup" and state["cleaned"]
            ):
                raise PersistenceError("ML-TEARDOWN-RECORD-ORDER")
        self.evidence.reserve_event(claims)
        before = self.evidence._history(claims)
        self.evidence._mirrors(claims)
        check(deadline)
        saved = permits._issued[id(claim.receipt)][1]
        now = datetime.now(timezone.utc)
        status = (
            "pending"
            if stage == "intent"
            else ("stopped" if phase == "stop" else "cleaned")
        )
        proof = public_step(body)
        record = replace(
            saved,
            sequence=0,
            kind=stage,
            action_id=action.action_id,
            status=status,
            timestamp=now.isoformat(),
            permit_nonce=None,
            handle_id=handle.opaque_id,
            handle_action_id=handle.action_id,
            handle_provider_id=handle.provider_id,
            handle_provider_kind=handle.provider_kind,
            handle_resource_identity=handle.resource_identity,
            details=freeze(
                {
                    "maestroRunId": permits._run_id,
                    "maestroUnitId": unit_id,
                    "generation": 1,
                    "lifecycleDigest": permits._prepared.lifecycle_digest,
                    "teardown": proof,
                }
            ),
        )
        permits._journal.append(record)
        check(deadline)
        history = permits._journal.records
        stored = replace(record, sequence=len(before) + 1)
        if history != (*before, stored):
            raise PersistenceError("ML-TEARDOWN-RECORD-M3")
        self.evidence.history = history
        public = [
            r
            for r in permits._journal.public_records()
            if r["sequence"] == stored.sequence
        ]
        if len(public) != 1:
            raise PersistenceError("ML-TEARDOWN-RECORD-M3")
        source = [
            {
                "kind": "m3-record",
                "id": "m3-record-" + str(stored.sequence),
                "sequence": stored.sequence,
                "sha256": _digest(public[0]),
            }
        ]
        if stage == "outcome":
            source.append(
                {
                    "kind": "broker-record",
                    "id": body["step"],
                    "sequence": self.sequence + 1,
                    "sha256": _digest(proof),
                }
            )
        prior_event = state.get("event") or (
            sample["event"] if sample else claim.event_id
        )
        payload = {
            "schemaVersion": "2.0",
            "lifecycleDigest": "sha256:" + permits._prepared.lifecycle_digest,
            "runId": permits._run_id,
            "sessionId": body["session"],
            "scope": "unit",
            "unitId": unit_id,
            "generation": 1,
            "operationId": operation,
            "action": "intent" if stage == "intent" else phase,
            "outcome": "pending" if stage == "intent" else "succeeded",
            "sourceRefs": source,
            "dependencies": [],
            "handleRef": "handle-" + _digest([permits._run_id, asdict(handle)])[7:],
        }
        event_id = operation + "-" + phase + "-" + stage
        fields = {
            "eventId": event_id,
            "producerId": "maestro.teardown13",
            "eventKind": "annotation",
            "producerSequence": self.sequence + 1,
            "correlationId": permits._run_id,
            "causationId": prior_event,
            "clocks": {
                "host": {
                    "domain": "host:" + body["session"],
                    "unit": "s",
                    "value": body["observed_at"],
                },
                "utc": {
                    "domain": "utc:" + body["session"],
                    "unit": "s",
                    "value": now.timestamp(),
                },
            },
            "annotation": {"text": "Maestro " + phase + " " + stage},
            "extensions": {"xverse.maestro": payload},
        }
        ordinal = self.evidence.writer.append_event(
            event_id=event_id,
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
        self.evidence.events[event_id] = fields
        self.evidence._mirrors(claims)
        check(deadline)
        self.sequence += 1
        self.handles[unit_id] = handle, body["boundary_digest"]
        state["event"] = event_id
        if stage == "intent":
            self.pending[key] = operation
        else:
            state["stopped" if phase == "stop" else "cleaned"] = True
        return {
            "unit": unit_id,
            "phase": phase,
            "stage": stage,
            "m3_sequence": stored.sequence,
            "event": fields,
        }


def validate_teardown_reply(body, request, client, controller, operation):
    phase, stage = request["phase"], request["stage"]
    if (
        type(body) is not dict
        or set(body) != {"unit", "phase", "stage", "m3_sequence", "event"}
        or any(body[k] != request[k] for k in ("unit", "phase", "stage"))
    ):
        raise PersistenceError("ML-TEARDOWN-RECORD-ACK")
    seq = body["m3_sequence"]
    event = body["event"]
    keys = {
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
    if (
        type(seq) is not int
        or seq <= client._evidence_m3
        or type(event) is not dict
        or set(event) != keys
        or event["eventId"] != operation + "-" + phase + "-" + stage
        or event["producerId"] != "maestro.teardown13"
        or event["eventKind"] != "annotation"
        or event["producerSequence"] != client._teardown_sequence + 1
        or type(event["producerSequence"]) is not int
        or type(event["ingestionOrdinal"]) is not int
        or event["ingestionOrdinal"] <= client._evidence_ordinal
        or event["correlationId"] != client.run_id
        or event["annotation"] != {"text": "Maestro " + phase + " " + stage}
    ):
        raise PersistenceError("ML-TEARDOWN-RECORD-ACK")
    prior = client._teardown_receipts.get(request["unit"])
    if prior is not None:
        cause = prior.event_id
    else:
        receipt = client._probe_receipts.get(request["unit"])
        if receipt is not None:
            import json

            cause = next(
                e["eventId"]
                for e in json.loads(receipt.public_bytes)
                if e["extensions"]["xverse.maestro"]["action"] in ("probe", "health")
            )
        else:
            cause = controller.owner._claims[request["unit"]].event_id
    if event["causationId"] != cause:
        raise PersistenceError("ML-TEARDOWN-RECORD-ACK")
    payload = (
        event["extensions"].get("xverse.maestro")
        if type(event["extensions"]) is dict
        and set(event["extensions"]) == {"xverse.maestro"}
        else None
    )
    expected = {
        "schemaVersion": "2.0",
        "lifecycleDigest": "sha256:" + client.prepared.lifecycle_digest,
        "runId": client.run_id,
        "sessionId": client.session,
        "scope": "unit",
        "unitId": request["unit"],
        "generation": 1,
        "operationId": operation,
        "action": "intent" if stage == "intent" else phase,
        "outcome": "pending" if stage == "intent" else "succeeded",
        "dependencies": [],
        "handleRef": "handle-" + _digest([client.run_id, request["handle"]])[7:],
    }
    if (
        type(payload) is not dict
        or set(payload) != set(expected) | {"sourceRefs"}
        or any(payload.get(k) != v for k, v in expected.items())
    ):
        raise PersistenceError("ML-TEARDOWN-RECORD-ACK")
    refs = payload["sourceRefs"]
    if type(refs) is not list or len(refs) != (1 if stage == "intent" else 2):
        raise PersistenceError("ML-TEARDOWN-RECORD-ACK")
    m3 = refs[0]
    if (
        type(m3) is not dict
        or set(m3) != {"kind", "id", "sequence", "sha256"}
        or m3["kind"] != "m3-record"
        or m3["id"] != "m3-record-" + str(seq)
        or type(m3["sequence"]) is not int
        or m3["sequence"] != seq
        or type(m3["sha256"]) is not str
        or re.fullmatch("sha256:[0-9a-f]{64}", m3["sha256"]) is None
    ):
        raise PersistenceError("ML-TEARDOWN-RECORD-ACK")
    if stage == "outcome" and refs[1] != {
        "kind": "broker-record",
        "id": request["step"],
        "sequence": client._teardown_sequence + 1,
        "sha256": _digest(public_step(request)),
    }:
        raise PersistenceError("ML-TEARDOWN-RECORD-ACK")
    clocks = event["clocks"]
    if type(clocks) is not dict or set(clocks) != {"host", "utc"}:
        raise PersistenceError("ML-TEARDOWN-RECORD-ACK")
    for name in ("host", "utc"):
        clock = clocks[name]
        if (
            type(clock) is not dict
            or set(clock) != {"domain", "unit", "value"}
            or clock["domain"] != name + ":" + client.session
            or clock["unit"] != "s"
            or type(clock["value"]) not in (int, float)
            or not math.isfinite(clock["value"])
            or (name == "host" and clock["value"] != request["observed_at"])
        ):
            raise PersistenceError("ML-TEARDOWN-RECORD-ACK")
