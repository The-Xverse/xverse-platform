"""Original storage-worker start/probe evidence; partial U7, never coverage closure."""

from dataclasses import dataclass, field, replace, asdict
from datetime import datetime, timezone
import hashlib
import math
import re
import time

from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse_xdl.lifecycle import OwnedResourceHandle
from xverse_xdl.models import freeze
from .persistence import PersistenceError


def _digest(value):
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


@dataclass(frozen=True)
class LifecycleReceipt:
    unit_id: str
    sample_sequence: int
    event_ids: tuple[str, ...]
    m3_sequences: tuple[int, ...]
    public_bytes: bytes = field(repr=False)
    lifecycle_complete: bool = field(default=False, init=False)


def _parents(prepared, unit_id):
    reverse = {}
    for edge in prepared.graph_edges:
        reverse.setdefault(edge.target, set()).add(edge.source)
    todo, seen = [(unit_id, "dispatch")], set()
    while todo:
        node = todo.pop()
        if node not in seen:
            seen.add(node)
            todo.extend(reverse.get(node, ()))
    return tuple(
        u.unit_id
        for u in prepared.units
        if u.unit_id != unit_id and (u.unit_id, "ready") in seen
    )


class OutcomeJournal:
    """Lives only inside the original persistence process; no control authority."""

    def __init__(self, permits, writer, evidence_root):
        self.permits, self.writer, self.root = permits, writer, evidence_root
        self.history = ()
        self.samples = {}
        self.events = {}
        self.sequence = 0
        self.event_limit = 8192

    def reserve_event(self, claims):
        if len(self.events) + len(claims) >= self.event_limit:
            raise PersistenceError("ML-SCHEDULE-EVENT-CAPACITY")

    def _history(self, claims):
        records = self.permits._journal.records
        if records[: len(self.history)] != self.history:
            raise PersistenceError("ML-EVIDENCE-HISTORY")
        allowed = list(self.history)
        for claim in claims.values():
            saved = self.permits._issued.get(id(claim.receipt))
            if (
                saved is None
                or saved[0] is not claim.receipt
                or saved[1] not in records
            ):
                raise PersistenceError("ML-EVIDENCE-INTENT")
            if saved[1] not in allowed:
                allowed.append(saved[1])
        if tuple(sorted(allowed, key=lambda r: r.sequence)) != records:
            raise PersistenceError("ML-EVIDENCE-HISTORY")
        return records

    def _mirrors(self, claims):
        events = EvidenceStore.read_run(self.root).records()
        indexed = {}
        for event in events:
            if event["eventId"] in indexed:
                raise PersistenceError("ML-EVIDENCE-MIRROR")
            indexed[event["eventId"]] = event
        for claim in claims.values():
            event = indexed.get(claim.event_id, {})
            payload = event.get("extensions", {}).get("xverse.maestro", {})
            refs = payload.get("sourceRefs", [])
            if (
                payload.get("action") != "intent"
                or payload.get("unitId") != claim.receipt.unit_id
                or len(refs) != 1
                or refs[0].get("sha256") != "sha256:" + claim.intent_digest.hex()
                or _digest([claim.event_id, event.get("ingestionOrdinal"), payload])
                != "sha256:" + claim.flush_digest.hex()
            ):
                raise PersistenceError("ML-EVIDENCE-MIRROR")
        for event_id, expected in self.events.items():
            actual = indexed.get(event_id, {})
            if any(actual.get(k) != v for k, v in expected.items()):
                raise PersistenceError("ML-EVIDENCE-MIRROR")

    def record(self, body, claims, operation, deadline, check):
        check(deadline)
        if set(body) != {
            "unit",
            "claim",
            "generation",
            "handle",
            "sample_sequence",
            "session",
            "observed_at",
            "ready",
            "freshness",
        }:
            raise PersistenceError("ML-EVIDENCE-INPUT")
        unit_id = body["unit"]
        claim = claims.get(unit_id)
        if claim is None or body["claim"] != claim.operation:
            raise PersistenceError("ML-EVIDENCE-INTENT")
        if (
            type(body["generation"]) is not int
            or body["generation"] != 1
            or body["session"] != deadline.session
            or type(body["ready"]) is not bool
            or type(body["sample_sequence"]) is not int
            or not 0 < body["sample_sequence"] <= 8192
        ):
            raise PersistenceError("ML-EVIDENCE-SAMPLE")
        for name in ("observed_at", "freshness"):
            value = body[name]
            try:
                valid = type(value) in (int, float) and math.isfinite(value)
            except OverflowError:
                valid = False
            if not valid:
                raise PersistenceError("ML-EVIDENCE-TIME")
        if (
            not 0 < body["freshness"] <= 5
            or not 0 <= time.monotonic() - body["observed_at"] <= body["freshness"]
        ):
            raise PersistenceError("ML-EVIDENCE-TIME")
        unit = next(u for u in self.permits._prepared.units if u.unit_id == unit_id)
        start = next(a for a in unit.plan.actions if a.phase == "start")
        observe = next(a for a in unit.plan.actions if a.phase == "observe")
        if observe.condition != "running" or unit.provider.kind != "process":
            raise PersistenceError("ML-EVIDENCE-PROVIDER")
        try:
            handle = OwnedResourceHandle(**body["handle"])
        except (TypeError, ValueError) as error:
            raise PersistenceError("ML-EVIDENCE-HANDLE") from error
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
                "process",
            )
            or type(handle.opaque_id) is not str
            or re.fullmatch("[0-9a-f]{64}", handle.opaque_id) is None
            or type(handle.resource_identity) is not str
            or re.fullmatch("maestro-boundary:[0-9a-f]{64}", handle.resource_identity)
            is None
        ):
            raise PersistenceError("ML-EVIDENCE-HANDLE")
        prior = self.samples.get(unit_id)
        if prior and (
            prior["handle"] != handle
            or body["sample_sequence"] <= prior["sequence"]
            or body["observed_at"] < prior["observed_at"]
            or body["freshness"] != prior["freshness"]
        ):
            raise PersistenceError("ML-EVIDENCE-SEQUENCE")
        self._history(claims)
        self._mirrors(claims)
        check(deadline)
        dependencies = []
        for parent in _parents(self.permits._prepared, unit_id):
            sample = self.samples.get(parent)
            if (
                sample is None
                or not sample["ready"]
                or not 0
                <= time.monotonic() - sample["observed_at"]
                <= sample["freshness"]
            ):
                raise PersistenceError("ML-EVIDENCE-DEPENDENCY")
            dependencies.append(
                {"unitId": parent, "generation": 1, "probeEventId": sample["event"]}
            )
        emitted = []
        sequences = []
        now = datetime.now(timezone.utc)
        saved = self.permits._issued[id(claim.receipt)][1]
        details = freeze(
            {
                "maestroRunId": self.permits._run_id,
                "maestroUnitId": unit_id,
                "generation": 1,
                "lifecycleDigest": self.permits._prepared.lifecycle_digest,
                "sampleSequence": body["sample_sequence"],
                "hostSession": body["session"],
                "observedAt": body["observed_at"],
                "handleDigest": _digest(asdict(handle)),
            }
        )
        base = replace(
            saved,
            sequence=0,
            timestamp=now.isoformat(),
            handle_id=handle.opaque_id,
            handle_action_id=handle.action_id,
            handle_provider_id=handle.provider_id,
            handle_provider_kind=handle.provider_kind,
            handle_resource_identity=handle.resource_identity,
            details=details,
        )

        def append_m3(kind, action, status):
            check(deadline)
            record = replace(base, kind=kind, action_id=action, status=status)
            before = self._history(claims)
            self.permits._journal.append(record)
            check(deadline)
            history = self.permits._journal.records
            expected = replace(record, sequence=len(before) + 1)
            if history != (*before, expected):
                raise PersistenceError("ML-EVIDENCE-M3-ACK")
            self.history = history
            public = [
                r
                for r in self.permits._journal.public_records()
                if r["sequence"] == expected.sequence
            ]
            if len(public) != 1:
                raise PersistenceError("ML-EVIDENCE-PUBLIC")
            sequences.append(expected.sequence)
            return {
                "kind": "m3-record",
                "id": "m3-record-" + str(expected.sequence),
                "sequence": expected.sequence,
                "sha256": _digest(public[0]),
            }

        def mirror(action, outcome, source, causation, probe=False):
            check(deadline)
            self.reserve_event(claims)
            event_id = operation + "-" + action
            payload = {
                "schemaVersion": "2.0",
                "lifecycleDigest": "sha256:" + self.permits._prepared.lifecycle_digest,
                "runId": self.permits._run_id,
                "sessionId": body["session"],
                "scope": "unit",
                "unitId": unit_id,
                "generation": 1,
                "operationId": operation,
                "action": action,
                "outcome": outcome,
                "sourceRefs": [source],
                "dependencies": dependencies,
                "handleRef": "handle-"
                + _digest([self.permits._run_id, asdict(handle)])[7:],
            }
            if probe:
                payload["probeId"] = "running"
            fields = {
                "eventId": event_id,
                "producerId": "maestro.outcomes12",
                "eventKind": "annotation",
                "producerSequence": self.sequence + 1,
                "correlationId": self.permits._run_id,
                "causationId": causation,
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
                "annotation": {"text": "Maestro " + action + " " + outcome},
                "extensions": {"xverse.maestro": payload},
            }
            ordinal = self.writer.append_event(
                event_id=event_id,
                producer_id=fields["producerId"],
                event_kind="annotation",
                producer_sequence=fields["producerSequence"],
                correlation_id=fields["correlationId"],
                causation_id=causation,
                clocks=fields["clocks"],
                annotation=fields["annotation"],
                extensions=fields["extensions"],
            )
            check(deadline)
            self.writer.flush_buffer()
            check(deadline)
            fields["ingestionOrdinal"] = ordinal
            self.events[event_id] = fields
            self.sequence += 1
            emitted.append(fields)
            return event_id

        started = bool(prior and prior["started"])
        cause = prior["event"] if prior else claim.event_id
        if body["ready"] and not started:
            source = append_m3("outcome", start.action_id, "running")
            cause = mirror("started", "succeeded", source, cause)
            started = True
        source = append_m3(
            "observation",
            observe.action_id,
            "running" if body["ready"] else "not-ready",
        )
        action = "health" if prior and prior["started"] else "probe"
        probe_event = mirror(
            action, "succeeded" if body["ready"] else "failed", source, cause, True
        )
        if body["ready"] and not (prior and prior["started"]):
            mirror("ready", "succeeded", source, probe_event, True)
        elif not body["ready"] and prior and prior["started"]:
            mirror("health-loss", "failed", source, probe_event, True)
        self._mirrors(claims)
        check(deadline)
        self.samples[unit_id] = {
            "handle": handle,
            "sequence": body["sample_sequence"],
            "observed_at": body["observed_at"],
            "freshness": body["freshness"],
            "ready": body["ready"],
            "started": started,
            "event": probe_event,
        }
        return {
            "unit": unit_id,
            "sample_sequence": body["sample_sequence"],
            "events": emitted,
            "m3_sequences": sequences,
        }


def validate_receipt(body, facade, observed, claim, operation, prior):
    """Validate retained public fields without coordinator-side storage I/O."""
    import json

    unit = observed.unit_id
    old = json.loads(prior.public_bytes) if prior else []
    was_started = any(
        e["extensions"]["xverse.maestro"]["action"]
        in ("started", "ready", "health", "health-loss")
        for e in old
    )
    new_start = observed.ready and not was_started
    actions = (
        ["started", "probe", "ready"]
        if new_start
        else (
            ["health"]
            if was_started and observed.ready
            else (["health", "health-loss"] if was_started else ["probe"])
        )
    )
    if (
        type(body) is not dict
        or set(body) != {"unit", "sample_sequence", "events", "m3_sequences"}
        or body["unit"] != unit
        or type(body["sample_sequence"]) is not int
        or body["sample_sequence"] != observed.sequence
        or type(body["events"]) is not list
        or len(body["events"]) != len(actions)
        or type(body["m3_sequences"]) is not list
        or len(body["m3_sequences"]) != (2 if new_start else 1)
        or any(type(n) is not int or n < 1 for n in body["m3_sequences"])
        or body["m3_sequences"] != sorted(set(body["m3_sequences"]))
    ):
        raise PersistenceError("ML-EVIDENCE-ACK")
    if prior and body["m3_sequences"][0] <= prior.m3_sequences[-1]:
        raise PersistenceError("ML-EVIDENCE-ACK")
    client = facade._owner.persistence
    handle = facade._bindings[unit].handle
    dependencies = []
    for parent in facade._prerequisites[unit]:
        receipt = client._probe_receipts.get(parent)
        if receipt is None:
            raise PersistenceError("ML-EVIDENCE-ACK")
        events = json.loads(receipt.public_bytes)
        matching = [
            e
            for e in events
            if e["extensions"]["xverse.maestro"]["action"] in ("probe", "health")
        ]
        if (
            len(matching) != 1
            or matching[0]["extensions"]["xverse.maestro"]["outcome"] != "succeeded"
        ):
            raise PersistenceError("ML-EVIDENCE-ACK")
        dependencies.append(
            {"unitId": parent, "generation": 1, "probeEventId": matching[0]["eventId"]}
        )
    prior_probes = [
        e
        for e in old
        if e["extensions"]["xverse.maestro"]["action"] in ("probe", "health")
    ]
    cause = prior_probes[0]["eventId"] if prior_probes else claim.event_id
    last_ordinal = client._evidence_ordinal
    expected_producer = client._evidence_sequence + 1
    if body["m3_sequences"][0] <= client._evidence_m3:
        raise PersistenceError("ML-EVIDENCE-ACK")
    first_event = True
    fields = {
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
    for event, action in zip(body["events"], actions):
        if type(event) is not dict or set(event) != fields:
            raise PersistenceError("ML-EVIDENCE-ACK")
        outcome = "succeeded" if observed.ready else "failed"
        seq = (
            body["m3_sequences"][0] if action == "started" else body["m3_sequences"][-1]
        )
        payload = (
            event["extensions"].get("xverse.maestro")
            if type(event["extensions"]) is dict
            and set(event["extensions"]) == {"xverse.maestro"}
            else None
        )
        expected = {
            "schemaVersion": "2.0",
            "lifecycleDigest": "sha256:" + facade._prepared.lifecycle_digest,
            "runId": client.run_id,
            "sessionId": client.session,
            "scope": "unit",
            "unitId": unit,
            "generation": 1,
            "operationId": operation,
            "action": action,
            "outcome": outcome,
            "dependencies": dependencies,
            "handleRef": "handle-" + _digest([client.run_id, asdict(handle)])[7:],
        }
        if action in ("probe", "ready", "health", "health-loss"):
            expected["probeId"] = "running"
        if (
            type(payload) is not dict
            or set(payload) != set(expected) | {"sourceRefs"}
            or any(payload.get(k) != v for k, v in expected.items())
        ):
            raise PersistenceError("ML-EVIDENCE-ACK")
        refs = payload["sourceRefs"]
        if (
            type(refs) is not list
            or len(refs) != 1
            or type(refs[0]) is not dict
            or set(refs[0]) != {"kind", "id", "sequence", "sha256"}
            or refs[0]["kind"] != "m3-record"
            or refs[0]["id"] != "m3-record-" + str(seq)
            or type(refs[0]["sequence"]) is not int
            or refs[0]["sequence"] != seq
            or type(refs[0]["sha256"]) is not str
            or re.fullmatch("sha256:[0-9a-f]{64}", refs[0]["sha256"]) is None
        ):
            raise PersistenceError("ML-EVIDENCE-ACK")
        clocks = event["clocks"]
        if type(clocks) is not dict or set(clocks) != {"host", "utc"}:
            raise PersistenceError("ML-EVIDENCE-ACK")
        for name in ("host", "utc"):
            clock = clocks[name]
            if (
                type(clock) is not dict
                or set(clock) != {"domain", "unit", "value"}
                or clock["domain"] != name + ":" + client.session
                or clock["unit"] != "s"
                or type(clock["value"]) not in (int, float)
                or not math.isfinite(clock["value"])
                or (name == "host" and clock["value"] != observed.observed_at)
            ):
                raise PersistenceError("ML-EVIDENCE-ACK")
        if (
            event["eventId"] != operation + "-" + action
            or event["producerId"] != "maestro.outcomes12"
            or event["eventKind"] != "annotation"
            or event["correlationId"] != client.run_id
            or event["causationId"] != cause
            or event["annotation"] != {"text": "Maestro " + action + " " + outcome}
            or type(event["producerSequence"]) is not int
            or event["producerSequence"] != expected_producer
            or type(event["ingestionOrdinal"]) is not int
            or event["ingestionOrdinal"] <= last_ordinal
            or (not first_event and event["ingestionOrdinal"] != last_ordinal + 1)
        ):
            raise PersistenceError("ML-EVIDENCE-ACK")
        last_ordinal = event["ingestionOrdinal"]
        expected_producer += 1
        first_event = False
        cause = event["eventId"]
