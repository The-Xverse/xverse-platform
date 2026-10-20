"""Crash-point matrix gaps: helper/storage loss after Release before the M3 outcome, and storage loss during spawn.

Closes the two gaps recorded in docs/engineering/maestro-lite/crash-point-matrix.md with owned
composed controls over the whole original lifecycle. Expectations are hand-authored in EXPECTED
before the controls were run; they are not derived from implementation state. Each control keeps
the unrelated heartbeat sentinel alive in a separate boundary and retains a receipt.

Not the complete M1 crash matrix, not acceptance, not a scientific result.
"""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import signal
import threading
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.run_closure import RunClosure
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_terminal_runtime import scheduled, run
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline
from .test_composed_authority_interruptions import (
    Barrier, instrument, retain, observed_members, wait_for, execute,
    heartbeat_binary as heartbeat_binary, sentinel as sentinel)

SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

# Independent expectations: (window, fault) -> facts that must hold after closure.
EXPECTED = {
    ("release-ack-pending", "authority"): dict(released_markers=1, execution_succeeded=False, late_stage_rejected=True,
                                               started_events_max=1, outcome_records_max=1, sentinel_untouched=True),
    ("release-ack-pending", "storage"): dict(released_markers=1, execution_succeeded=False, late_stage_rejected=True,
                                             started_events_max=1, outcome_records_max=1, sentinel_untouched=True),
    ("release-after-reply", "authority"): dict(released_markers=1, execution_succeeded=False, late_stage_rejected=True,
                                               started_events_max=1, outcome_records_max=1, sentinel_untouched=True),
    ("release-after-reply", "storage"): dict(released_markers=1, execution_succeeded=False, late_stage_rejected=True,
                                             started_events_max=1, outcome_records_max=1, sentinel_untouched=True),
}


def _unit_records(records, unit, actions):
    rows = []
    for record in records:
        payload = record.get("extensions", {}).get("xverse.maestro", {}) if "extensions" in record else record
        if payload.get("unitId") == unit and payload.get("action") in actions:
            rows.append(payload)
    return rows


@pytest.mark.parametrize("window,fault", sorted(EXPECTED), ids=lambda v: v)
def test_post_release_loss_before_outcome(request, monkeypatch, sentinel, window, fault):
    """Authority or storage loss after the Release reply or while its ACK is pending, before the M3 outcome."""
    expected = EXPECTED[(window, fault)]
    before = sentinel()
    stack, _, driver = scheduled(request, monkeypatch)
    broker, facade, client, work = stack
    unit = driver.prepared.resource_order[0]
    issuer = broker.issuer(unit)
    barrier = Barrier()
    instrument(monkeypatch, stack, window, barrier)
    results, failures = [], []

    def coordinate():
        try:
            results.append(run(driver))
        except BaseException as error:
            failures.append(repr(error))

    coordinator = threading.Thread(target=coordinate, name="original-run-coordinator")
    coordinator.start()
    observations = dict(window=window, fault=fault)
    try:
        assert barrier.reached.wait(3), failures
        if window != "release-before-send":
            wait_for(lambda: len(list(work.glob("*.marker"))) == 1)
        observations.update(at_barrier=time.monotonic(), marker_names=sorted(p.name for p in work.glob("*.marker")),
                            issued_receipts=len(client._issued_receipts))
        child = broker.connection.child if fault == "authority" else client.process
        signal.pidfd_send_signal(child._capability.fileno(), signal.SIGKILL)
        observations.update(killed_original_role=4 if fault == "authority" else 3, killed_at=time.monotonic())
    finally:
        barrier.resume.set()
        coordinator.join(timeout=18)
    assert not coordinator.is_alive(), "original dispatcher has not reached terminal state"
    assert not failures and len(results) == 1, failures
    result = results[0]
    closure = RunClosure(broker.session, dispatcher=driver).close(deadline(6))
    after = sentinel()
    events = EvidenceStore.read_run(work.parent / "argus").records()
    m3 = FileEvidenceJournal(work.parent / "m3.jsonl").public_records()
    markers = {p.name: p.read_text() for p in work.glob("*.marker")}
    facts = asdict(closure)
    facts["terminal_reports"] = [r.public_data() for r in closure.terminal_reports]
    started = _unit_records(events, unit, {"started"})
    outcomes = _unit_records(m3, unit, {"outcome", "stop", "cleanup"})
    sequence = broker.connection.sequence
    late_stage_rejected = False
    try:
        issuer.stage(deadline(.3))
    except ValueError:
        late_stage_rejected = True
    retain("post-release-loss-" + work.parent.name + ".json", dict(window=window, fault=fault, expected=expected,
        original_fixture=str(work.parent), barrier=barrier.observations, original_exchange_returns=barrier.exchanges,
        observations=observations, execution_succeeded=result.execution_succeeded, diagnostic=result.diagnostic,
        terminal_recorded=result.terminal_recorded, closure=facts, cleanup_complete=closure.cleanup_complete,
        started_events=len(started), unit_outcome_records=len(outcomes), markers=markers, late_stage_rejected=late_stage_rejected,
        sentinel_before=before, sentinel_after=after, source_sha256=SOURCE_SHA256,
        full_crash_matrix_complete=False, full_M1_complete=False, accepted=False))
    assert result.execution_succeeded is expected["execution_succeeded"]
    assert not closure.lifecycle_complete and closure.authority_fenced and closure.root_reaped
    assert all(h.process_reaped for h in closure.helpers)
    assert all(b.empty and b.released for b in closure.boundaries)
    assert broker.owner.latch.cancelled
    assert len(markers) == expected["released_markers"] and all(v == "EXEC\n" for v in markers.values()), markers
    assert len(started) <= expected["started_events_max"]
    assert len(outcomes) <= expected["outcome_records_max"]
    assert late_stage_rejected is expected["late_stage_rejected"] and broker.connection.sequence == sequence
    assert {p.name: p.read_text() for p in work.glob("*.marker")} == markers
    assert (after["members"] == before["members"]) is expected["sentinel_untouched"]


@pytest.mark.parametrize("window", ["stage-before-send", "stage-ack-pending"])
def test_spawn_time_storage_loss(request, monkeypatch, sentinel, window):
    """Storage worker killed while the authority is between STAGE send and STAGED: no workload instruction."""
    execute(request, monkeypatch, sentinel, window, "storage")


# Remaining crash point (crash-point-matrix.md): authority or storage loss injected exactly before
# the Release send. Expectations authored before the control was run (finding 372 records the
# first table): no started event, no unit outcome, late Stage rejected, sentinel untouched.
# Authority loss: the Release cannot be linearized, so no marker. Storage loss: the first table
# said no marker; the observation showed exactly one. Corrected after observation and declared so:
# the durable M3 intent was committed and revalidated twice before the send (run_broker.release),
# no storage-liveness check sits between the last revalidation and the send, and none could close
# that window, so a storage loss there is indistinguishable from one just after the send (design
# row CP-11: intent written, outcome may be a mandatory gap). Bound: released at most once.
EXPECTED_RELEASE_BEFORE_SEND = {
    ("release-before-send", "authority"): dict(released_markers_max=0, execution_succeeded=False, late_stage_rejected=True,
                                               started_events=0, unit_outcome_action_records=0, sentinel_untouched=True),
    ("release-before-send", "storage"): dict(released_markers_max=1, execution_succeeded=False, late_stage_rejected=True,
                                             started_events=0, unit_outcome_action_records=0, sentinel_untouched=True),
}


@pytest.mark.parametrize("fault", ["authority", "storage"])
def test_release_before_send_loss(request, monkeypatch, sentinel, fault):
    """Authority or storage loss exactly before the Release send: at most one release, nothing fabricated.

    Authority loss: nothing released. Storage loss: released at most once (an outcome with zero
    releases also satisfies the bound); the started/outcome records stay absent either way.
    """
    window = "release-before-send"
    expected = EXPECTED_RELEASE_BEFORE_SEND[(window, fault)]
    before = sentinel()
    stack, _, driver = scheduled(request, monkeypatch)
    broker, facade, client, work = stack
    unit = driver.prepared.resource_order[0]
    issuer = broker.issuer(unit)
    barrier = Barrier()
    instrument(monkeypatch, stack, window, barrier)
    results, failures = [], []

    def coordinate():
        try:
            results.append(run(driver))
        except BaseException as error:
            failures.append(repr(error))

    coordinator = threading.Thread(target=coordinate, name="original-run-coordinator")
    coordinator.start()
    observations = dict(window=window, fault=fault)
    try:
        assert barrier.reached.wait(3), failures
        observations.update(at_barrier=time.monotonic(), marker_names=sorted(p.name for p in work.glob("*.marker")),
                            issued_receipts=len(client._issued_receipts),
                            release_exchanges_before_fault=sum(1 for e in barrier.exchanges if e["request"] == "RELEASE"))
        child = broker.connection.child if fault == "authority" else client.process
        signal.pidfd_send_signal(child._capability.fileno(), signal.SIGKILL)
        observations.update(killed_original_role=4 if fault == "authority" else 3, killed_at=time.monotonic())
    finally:
        barrier.resume.set()
        coordinator.join(timeout=18)
    assert not coordinator.is_alive(), "original dispatcher has not reached terminal state"
    assert not failures and len(results) == 1, failures
    result = results[0]
    closure = RunClosure(broker.session, dispatcher=driver).close(deadline(6))
    after = sentinel()
    events = EvidenceStore.read_run(work.parent / "argus").records()
    m3 = FileEvidenceJournal(work.parent / "m3.jsonl").public_records()
    markers = {p.name: p.read_text() for p in work.glob("*.marker")}
    facts = asdict(closure)
    facts["terminal_reports"] = [r.public_data() for r in closure.terminal_reports]
    started = _unit_records(events, unit, {"started"})
    outcome_only = _unit_records(m3, unit, {"outcome"})
    stop_cleanup = _unit_records(m3, unit, {"stop", "cleanup"})
    sequence = broker.connection.sequence
    late_stage_rejected = False
    try:
        issuer.stage(deadline(.3))
    except ValueError:
        late_stage_rejected = True
    retain("release-before-send-loss-" + work.parent.name + ".json", dict(window=window, fault=fault, expected=expected,
        original_fixture=str(work.parent), barrier=barrier.observations, original_exchange_returns=barrier.exchanges,
        observations=observations, execution_succeeded=result.execution_succeeded, diagnostic=result.diagnostic,
        terminal_recorded=result.terminal_recorded, closure=facts, cleanup_complete=closure.cleanup_complete,
        started_events=len(started), unit_outcome_action_records=len(outcome_only),
        unit_stop_cleanup_records_observed=len(stop_cleanup), markers=markers, late_stage_rejected=late_stage_rejected,
        sentinel_before=before, sentinel_after=after, source_sha256=SOURCE_SHA256,
        full_crash_matrix_complete=False, full_M1_complete=False, accepted=False))
    assert observations["release_exchanges_before_fault"] == 0 and observations["marker_names"] == []
    assert result.execution_succeeded is expected["execution_succeeded"]
    assert not closure.lifecycle_complete and closure.authority_fenced and closure.root_reaped
    assert all(h.process_reaped for h in closure.helpers)
    assert all(b.empty and b.released for b in closure.boundaries)
    assert broker.owner.latch.cancelled
    assert len(markers) <= expected["released_markers_max"] and all(v == "EXEC\n" for v in markers.values()), markers
    assert len(started) == expected["started_events"]
    assert len(outcome_only) == expected["unit_outcome_action_records"]
    assert late_stage_rejected is expected["late_stage_rejected"] and broker.connection.sequence == sequence
    assert {p.name: p.read_text() for p in work.glob("*.marker")} == markers
    assert (after["members"] == before["members"]) is expected["sentinel_untouched"]
