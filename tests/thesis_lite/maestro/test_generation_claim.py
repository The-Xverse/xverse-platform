"""Actual fresh successor consumption after original native/C1/normal release."""

from dataclasses import replace
import copy
import hashlib
import json
import os
from pathlib import Path

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.prbc import BoundaryDescriptor
from xverse.maestro.teardown import ReverseTeardown
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_generation_worker import prepare
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def ready(request, monkeypatch, *, future=True):
    retained = prepare(request, monkeypatch, "valid" if future else "default")
    stack = request.getfixturevalue("broker_stack")
    broker, facade, client, work = stack
    end = stage_all(stack)
    for unit in broker.owner._prepared.resource_order:
        issuer = broker.issuer(unit)
        assert facade.start(
            unit, issuer.recipe.descriptor, broker.connection, end
        ).ready
    controller = ReverseTeardown(facade, per_unit_seconds=0.8)
    unit = broker.owner._prepared.resource_order[-1]
    return stack, controller, unit, retained["config"]


def replacement(broker, unit):
    descriptor = BoundaryDescriptor(
        broker.storage.run_id,
        unit,
        2,
        "generation2-leaf",
        broker.session.boundaries.release_epoch,
    )
    broker.session.boundaries.create_frozen(descriptor)
    return descriptor


def release(controller, unit):
    assert not controller.phase(unit, "stop", deadline(1)).emergency
    assert controller.phase(unit, "cleanup", deadline(1)).normal_records_complete


def test_actual_successor_intent_uses_original_worker_and_preserves_old_identity(
    request, monkeypatch
):
    stack, controller, unit, config = ready(request, monkeypatch)
    broker, facade, client, work = stack
    original_worker = client.process
    old = broker.owner._claims[unit].receipt
    original_execution = client._claim_execution_id(old)
    old_handle = broker.issuer(unit)._handle
    release(controller, unit)
    descriptor = replacement(broker, unit)
    prepared = broker._prepare_generation(controller, unit, descriptor, deadline(1.2))
    prepared._holder()
    assert not prepared.ready_for_execution
    assert client.process is original_worker
    assert broker.connection.epoch == 0
    assert broker.issuer(unit)._handle is old_handle
    assert (
        client._claim_execution_id(old) == original_execution == old_handle.execution_id
    )
    selected = next(
        c
        for c in config.future_contexts
        if c.binding.unit_id == unit and c.binding.generation == 2
    )
    assert client._claim_execution_id(prepared.receipt) == selected.binding.execution_id
    client.revalidate_intent(prepared.receipt, deadline(0.4))
    journal = FileEvidenceJournal(work.parent / "m3.jsonl")
    assert journal.permit_consumed(
        selected.binding.permit.permit_id, selected.binding.permit.nonce
    )
    fresh = [
        r for r in journal.records if r.execution_id == selected.binding.execution_id
    ]
    assert (
        len(fresh) == 1
        and fresh[0].kind == "intent"
        and fresh[0].details["generation"] == 2
    )
    source = broker.owner._prepared.resource_order[0]
    assert facade.check_unit_health(source, deadline(0.5)).ready
    assert broker.session.boundaries.record(descriptor).state == "frozen"
    count = len(journal.records)
    with pytest.raises(ValueError):
        broker._prepare_generation(controller, unit, descriptor, deadline(0.5))
    with pytest.raises(ValueError):
        client.prepare_generation(broker, prepared.statement, deadline(0.5))
    with pytest.raises(TypeError):
        copy.copy(prepared)
    assert len(FileEvidenceJournal(work.parent / "m3.jsonl").records) == count
    output = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if output:
        (
            Path(output) / ("successor-intent-public-" + str(os.getpid()) + ".json")
        ).write_text(
            json.dumps(
                dict(
                    public_m3=journal.public_records(),
                    argus_events=EvidenceStore.read_run(
                        work.parent / "argus"
                    ).records(),
                    source_sha256=hashlib.sha256(
                        Path(__file__).read_bytes()
                    ).hexdigest(),
                    actual_same_worker_successor_consumption=True,
                    original_receipt_execution_preserved=True,
                    unrelated_original_unit_observed_live=True,
                    native_ADVANCE_executed=False,
                    new_generation_staged=False,
                    full_M1_complete=False,
                )
            )
        )


@pytest.mark.parametrize("phase", ["running", "stopped"])
def test_successor_consumption_requires_actual_prior_cleanup(
    request, monkeypatch, phase
):
    stack, controller, unit, config = ready(request, monkeypatch)
    broker, _, _, work = stack
    if phase == "stopped":
        assert not controller.phase(unit, "stop", deadline(1)).emergency
    descriptor = replacement(broker, unit)
    before = FileEvidenceJournal(work.parent / "m3.jsonl").records
    with pytest.raises(ValueError, match="PRIOR-RELEASE"):
        broker._prepare_generation(controller, unit, descriptor, deadline(0.8))
    assert FileEvidenceJournal(work.parent / "m3.jsonl").records == before
    assert not broker.owner.latch.cancelled


def test_generation_budget_is_not_a_successor_approval(request, monkeypatch):
    stack, controller, unit, _ = ready(request, monkeypatch, future=False)
    broker, _, _, work = stack
    release(controller, unit)
    descriptor = replacement(broker, unit)
    before = FileEvidenceJournal(work.parent / "m3.jsonl").records
    with pytest.raises(ValueError, match="NOT-ADMITTED"):
        broker._prepare_generation(controller, unit, descriptor, deadline(0.8))
    assert FileEvidenceJournal(work.parent / "m3.jsonl").records == before
    assert not broker.owner.latch.cancelled


def test_missing_actual_old_mirror_blocks_fresh_permit_consumption(
    request, monkeypatch
):
    stack, controller, unit, config = ready(request, monkeypatch)
    broker, _, _, work = stack
    release(controller, unit)
    descriptor = replacement(broker, unit)
    reader = EvidenceStore.read_run(work.parent / "argus")
    stream = work.parent / "argus" / reader.manifest["eventStream"]["path"]
    stream.unlink()
    with pytest.raises(ValueError):
        broker._prepare_generation(controller, unit, descriptor, deadline(0.8))
    context = next(
        c
        for c in config.future_contexts
        if c.binding.unit_id == unit and c.binding.generation == 2
    )
    journal = FileEvidenceJournal(work.parent / "m3.jsonl")
    assert not journal.permit_consumed(
        context.binding.permit.permit_id, context.binding.permit.nonce
    )
    assert not any(r.details.get("generation") == 2 for r in journal.records)


def test_copied_old_native_ack_cannot_authorize_a_successor(request, monkeypatch):
    stack, controller, unit, _ = ready(request, monkeypatch)
    broker, _, _, work = stack
    release(controller, unit)
    descriptor = replacement(broker, unit)
    issuer = broker.issuer(unit)
    original = issuer._stop_ack
    before = FileEvidenceJournal(work.parent / "m3.jsonl").records
    issuer._stop_ack = replace(original)
    try:
        with pytest.raises(ValueError):
            broker._prepare_generation(controller, unit, descriptor, deadline(0.8))
    finally:
        issuer._stop_ack = original
    assert FileEvidenceJournal(work.parent / "m3.jsonl").records == before
