"""Original-worker fresh intent after actual normal old-generation evidence."""

from dataclasses import asdict
from datetime import datetime, timezone

from .persistence import PersistenceError
from .lifecycle_evidence import _parents
from .owner import _persist_intent


def prepare_generation(evidence, teardown, body, claims, operation, deadline, check):
    check(deadline)
    if set(body) != {
        "unit",
        "generation",
        "prior",
        "handle",
        "boundary_digest",
        "cleanup_event",
    }:
        raise PersistenceError("ML-GENERATION-INPUT")
    unit = body["unit"]
    old = claims.get(unit)
    if (
        old is None
        or old.operation != body["prior"]
        or type(body["generation"]) is not int
    ):
        raise PersistenceError("ML-GENERATION-PRIOR")
    saved = evidence.permits._issued[id(old.receipt)][1]
    generation = saved.details["generation"]
    if body["generation"] != generation + 1:
        raise PersistenceError("ML-GENERATION-SEQUENCE")
    state = teardown._generation_states.get((unit, generation), {})
    handle = teardown._generation_handles.get((unit, generation))
    if (
        not state.get("stopped")
        or not state.get("cleaned")
        or body["cleanup_event"] != state.get("event")
        or handle is None
        or body["handle"] != asdict(handle[0])
        or body["boundary_digest"] != handle[1]
    ):
        raise PersistenceError("ML-GENERATION-NORMAL-RELEASE")
    if any(
        unit in _parents(evidence.permits._prepared, other)
        and not teardown.states.get(other, {}).get("cleaned")
        for other in claims
        if other != unit
    ):
        raise PersistenceError("ML-GENERATION-DEPENDENTS")
    evidence.reserve_event(claims)
    history = evidence._history(claims)
    evidence._mirrors(claims)
    check(deadline)
    cleanups = [
        r
        for r in history
        if r.execution_id == saved.execution_id
        and r.kind == "outcome"
        and r.status == "cleaned"
        and r.details.get("generation") == generation
    ]
    if len(cleanups) != 1:
        raise PersistenceError("ML-GENERATION-NORMAL-RELEASE")
    receipt = evidence.permits._claim_successor(
        unit,
        body["generation"],
        old.receipt,
        cleanups[0],
        now=datetime.now(timezone.utc),
    )
    check(deadline)
    fresh = _persist_intent(
        evidence.permits,
        evidence.writer,
        deadline.session,
        unit,
        deadline,
        check,
        operation,
        receipt=receipt,
    )
    evidence.retain_claim(fresh)
    claims[unit] = fresh
    if unit in evidence.samples:
        evidence.generation_samples[unit, generation] = evidence.samples.pop(unit)
    teardown.states.pop(unit, None)
    teardown.handles.pop(unit, None)
    evidence._history(claims)
    evidence._mirrors(claims)
    check(deadline)
    return dict(
        event=fresh.event_id,
        intent="sha256:" + fresh.intent_digest.hex(),
        flush="sha256:" + fresh.flush_digest.hex(),
        generation=body["generation"],
    )
