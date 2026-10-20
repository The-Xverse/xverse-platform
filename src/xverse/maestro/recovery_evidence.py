"""Original storage-owner durable reconciliation; read-only, never permit replay."""

from dataclasses import asdict
import re
from xverse_xdl.lifecycle import OwnedResourceHandle
from .lifecycle_evidence import _digest
from .persistence import PersistenceError


def _record_handle(record):
    return (
        record.handle_id,
        record.execution_id,
        record.handle_action_id,
        record.handle_provider_id,
        record.handle_provider_kind,
        record.handle_resource_identity,
    )


def snapshot(evidence, teardown, body, claims, deadline, check):
    check(deadline)
    prepared = evidence.permits._prepared
    if (
        type(body) is not dict
        or set(body) != {"recovery_id", "session", "view_epoch", "units"}
        or type(body["recovery_id"]) is not str
        or re.fullmatch("[a-f0-9]{32}", body["recovery_id"]) is None
        or type(body["view_epoch"]) is not int
        or body["view_epoch"] != getattr(evidence, "view_epoch", 0) + 1
        or body["view_epoch"] > 16
        or body["session"] != deadline.session
        or type(body["units"]) is not list
        or len(body["units"]) != len(prepared.units)
        or [row.get("unit") for row in body["units"] if type(row) is dict]
        != [u.unit_id for u in prepared.units]
    ):
        raise PersistenceError("ML-RECOVERY-REQUEST")
    if evidence.request_sequence + len(prepared.units) + 1 > evidence.request_limit:
        raise PersistenceError("ML-RECOVERY-CAPACITY")
    records = evidence._history(claims)
    evidence._mirrors(claims)
    check(deadline)
    public = {r["sequence"]: r for r in evidence.permits._journal.public_records()}
    rows = []
    for unit, request in zip(prepared.units, body["units"]):
        if type(request) is not dict or set(request) != {"unit", "claim", "handle"}:
            raise PersistenceError("ML-RECOVERY-REQUEST")
        claim = claims.get(unit.unit_id)
        sources = []
        status = "never-issued"
        consumed = False
        digest = None
        sample = evidence.samples.get(unit.unit_id)
        if claim is None:
            if request["claim"] is not None or request["handle"] is not None:
                raise PersistenceError("ML-RECOVERY-CLAIM")
        else:
            if request["claim"] != claim.operation:
                raise PersistenceError("ML-RECOVERY-CLAIM")
            saved = evidence.permits._issued.get(id(claim.receipt))
            if saved is None or saved[0] is not claim.receipt:
                raise PersistenceError("ML-RECOVERY-CLAIM")
            original = saved[1]
            consumed = evidence.permits._journal.permit_consumed(
                original.permit_id, original.permit_nonce
            )
            if consumed is not True or original not in records:
                raise PersistenceError("ML-RECOVERY-CONSUMPTION")
            sources.append(
                {
                    "kind": "m3-record",
                    "id": "m3-record-" + str(original.sequence),
                    "sequence": original.sequence,
                    "sha256": _digest(public[original.sequence]),
                }
            )
            status = "cleanup-only"
            if request["handle"] is not None:
                try:
                    handle = OwnedResourceHandle(**request["handle"])
                except (TypeError, ValueError) as error:
                    raise PersistenceError("ML-RECOVERY-HANDLE") from error
                expected = (
                    handle.opaque_id,
                    handle.execution_id,
                    handle.action_id,
                    handle.provider_id,
                    handle.provider_kind,
                    handle.resource_identity,
                )
                matching = [
                    r
                    for r in records
                    if _record_handle(r) == expected
                    and r.plan_digest == original.plan_digest
                    and r.catalog_identity == original.catalog_identity
                    and (r.permit_id, r.permit_nonce)
                    == (original.permit_id, original.permit_nonce)
                ]
                started = [
                    r
                    for r in matching
                    if r.kind == "outcome"
                    and r.action_id == handle.action_id
                    and r.status == "running"
                ]
                if sample is not None or matching:
                    state = teardown.states.get(unit.unit_id, {})
                    released = bool(state.get('stopped') and state.get('cleaned'))
                    stopped = bool(state.get('stopped') and not state.get('cleaned'))
                    if (
                        not matching
                        or not started
                        or sample is None
                        or sample["handle"] != handle
                        or not sample["started"]
                        or state and not (released or stopped)
                    ):
                        raise PersistenceError("ML-RECOVERY-HANDLE-DURABILITY")
                    digest = _digest(asdict(handle))
                    last = matching[-1]
                    if released or stopped:
                        identity = unit.unit_id, original.details['generation']
                        if (teardown._generation_states.get(identity) is not state
                            or teardown._generation_handles.get(identity, (None,))[0] != handle):
                            raise PersistenceError('ML-RECOVERY-RELEASE-DURABILITY')
                        phase = 'cleanup' if released else 'stop'
                        terminal = [r for r in records if _record_handle(r) == expected
                            and r.kind == 'outcome' and r.status == ('cleaned' if released else 'stopped')
                            and r.plan_digest == original.plan_digest and r.catalog_identity == original.catalog_identity
                            and r.details.get('maestroUnitId') == unit.unit_id
                            and r.details.get('generation') == identity[1]
                            and r.details.get('teardown', {}).get('phase') == phase
                            and r.details.get('teardown', {}).get('stage') == 'outcome'
                            and all(r.details.get('teardown', {}).get(k) is True for k in ('leader_reaped', 'empty'))
                            and r.details.get('teardown', {}).get('released') is released]
                        if len(terminal) != 1:
                            raise PersistenceError('ML-RECOVERY-RELEASE-DURABILITY')
                        last = terminal[0]
                        event = evidence.events.get(state.get('event'))
                        refs = event['extensions']['xverse.maestro']['sourceRefs'] if event else []
                        if not any(ref.get('kind') == 'm3-record' and ref.get('sequence') == last.sequence
                                   and ref.get('sha256') == _digest(public[last.sequence]) for ref in refs):
                            raise PersistenceError('ML-RECOVERY-RELEASE-DURABILITY')
                    sources.append(
                        {
                            "kind": "m3-record",
                            "id": "m3-record-" + str(last.sequence),
                            "sequence": last.sequence,
                            "sha256": _digest(public[last.sequence]),
                        }
                    )
                    status = "released" if released else "stopped" if stopped else "owned"
        rows.append(
            {
                "unit": unit.unit_id,
                "status": status,
                "permit_consumed": consumed,
                "handle_digest": digest,
                "last_sample_sequence": sample["sequence"] if sample else 0,
                "sources": sources,
            }
        )
    check(deadline)
    evidence.view_epoch = body["view_epoch"]
    for sample in evidence.samples.values():
        sample["ready"] = False
    return {
        "view_epoch": body["view_epoch"],
        "recovery_id": body["recovery_id"],
        "session": deadline.session,
        "lifecycle_digest": prepared.lifecycle_digest,
        "m3_sequence": len(records),
        "last_sample_sequence": max(
            (s["sequence"] for s in evidence.samples.values()), default=0
        ),
        "rows": rows,
    }
