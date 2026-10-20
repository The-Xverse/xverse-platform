"""Actual original-worker fresh permits through native advance, Stage and probes."""

import hashlib
import json
import os
from pathlib import Path

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.prbc import BoundaryDescriptor
from xverse.maestro.teardown import ReverseTeardown
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_generation_claim import ready, release
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def test_actual_same_run_leaf_generations1_2_3_preserve_live_prerequisite(
    request, monkeypatch
):
    stack, controller, unit, config = ready(request, monkeypatch)
    broker, facade, client, work = stack
    source = broker.owner._prepared.resource_order[0]
    original_source = broker.issuer(source)._handle
    original_worker = client.process
    executions = [broker.issuer(unit)._handle.execution_id]
    original_issuers = []
    observed_epochs = [broker.connection.epoch]
    for generation in (2, 3):
        old = broker.issuer(unit)
        original_issuers.append(old)
        release(controller, unit)
        old_stop = controller.phase(unit, "stop", deadline(0.5))
        old_clean = controller.phase(unit, "cleanup", deadline(0.5))
        descriptor = BoundaryDescriptor(
            client.run_id,
            unit,
            generation,
            "leaf-generation-" + str(generation),
            broker.session.boundaries.release_epoch,
        )
        broker.session.boundaries.create_frozen(descriptor)
        end = deadline(1.3)
        prepared = broker._prepare_generation(controller, unit, descriptor, end)
        fresh = broker.advance_generation(prepared, end)
        assert unit not in facade._bindings and unit not in facade._released
        handle = fresh.stage(end)
        facade.bind(fresh, handle)
        assert facade.start(unit, descriptor, broker.connection, end).ready
        observed_epochs.append(broker.connection.epoch)
        assert observed_epochs[-1] == generation - 1
        assert controller.phase(unit, "stop", deadline(0.5)) is old_stop
        assert controller.phase(unit, "cleanup", deadline(0.5)) is old_clean
        assert old.stop_owned(old._handle, deadline(0.5)).leader_reaped
        assert facade.check_unit_health(unit, deadline(0.5)).ready
        assert facade.check_unit_health(source, deadline(0.5)).ready
        assert broker.issuer(source)._handle is original_source
        assert client.process is original_worker
        executions.append(handle.execution_id)
        controller = ReverseTeardown(facade, per_unit_seconds=0.8)
    assert len(set(executions)) == 3
    records = FileEvidenceJournal(work.parent / "m3.jsonl").records
    for generation, execution in enumerate(executions, 1):
        assert any(
            r.execution_id == execution
            and r.kind == "intent"
            and r.action_id == "start"
            and r.details["generation"] == generation
            for r in records
        )
        assert any(
            r.execution_id == execution
            and r.kind == "outcome"
            and r.status == "running"
            and r.details["generation"] == generation
            for r in records
        )
    output = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if output:
        (
            Path(output)
            / ("actual-generation-restart-public-" + str(os.getpid()) + ".json")
        ).write_text(
            json.dumps(
                dict(
                    public_m3=FileEvidenceJournal(
                        work.parent / "m3.jsonl"
                    ).public_records(),
                    argus_events=EvidenceStore.read_run(
                        work.parent / "argus"
                    ).records(),
                    source_sha256=hashlib.sha256(
                        Path(__file__).read_bytes()
                    ).hexdigest(),
                    actual_same_worker_generations=[1, 2, 3],
                    unrelated_original_prerequisite_live=True,
                    actual_native_epochs=observed_epochs,
                    old_terminal_facts_retained=True,
                    full_M1_complete=False,
                )
            )
        )


def test_advance_cannot_extend_original_prepared_operation_end(request, monkeypatch):
    stack, controller, unit, _ = ready(request, monkeypatch)
    broker = stack[0]
    release(controller, unit)
    descriptor = BoundaryDescriptor(
        broker.storage.run_id,
        unit,
        2,
        "bounded-generation2",
        broker.session.boundaries.release_epoch,
    )
    broker.session.boundaries.create_frozen(descriptor)
    end = deadline(0.8)
    prepared = broker._prepare_generation(controller, unit, descriptor, end)
    with pytest.raises(ValueError, match="ORIGINAL-END"):
        broker.advance_generation(prepared, deadline(1.5))
    assert broker.connection.epoch == 0 and not broker.owner.latch.cancelled


def test_stopped_storage_after_preparation_fences_original_native(request, monkeypatch):
    import signal

    stack, controller, unit, _ = ready(request, monkeypatch)
    broker, _, client, _ = stack
    release(controller, unit)
    descriptor = BoundaryDescriptor(
        client.run_id,
        unit,
        2,
        "storage-stall-generation2",
        broker.session.boundaries.release_epoch,
    )
    broker.session.boundaries.create_frozen(descriptor)
    prepared = broker._prepare_generation(controller, unit, descriptor, deadline(1))
    signal.pidfd_send_signal(client.process._capability.fileno(), signal.SIGSTOP)
    with pytest.raises(ValueError):
        broker.advance_generation(prepared, deadline(0.35))
    assert broker._cancel_result is not None
    assert not broker.connection._advance_receipts
    assert (broker.issuer(unit).slot, 2) not in broker.connection._handles
    observed = broker.connection.revoke(deadline(1))
    assert observed.issuer_dead and observed.issuer_reaped
    assert not observed.workload_waits_known
    assert broker.session.boundaries.record(descriptor).state == "frozen"
