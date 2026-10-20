"""Original native workload waits plus actual normal M3/Argus teardown evidence."""

import hashlib
import json
import os
from pathlib import Path
import select
import signal

import pytest
from xverse.argus import EvidenceStore
from xverse_xdl.lifecycle import FileEvidenceJournal
from xverse.maestro.teardown import ReverseTeardown
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def ready(stack):
    broker, facade, _, _ = stack
    end = stage_all(stack)
    for unit in broker.owner._prepared.resource_order:
        issuer = broker.issuer(unit)
        assert facade.start(
            unit, issuer.recipe.descriptor, broker.connection, end
        ).ready
    return ReverseTeardown(facade, per_unit_seconds=0.8)


def test_native_reverse_teardown_has_original_wait_and_normal_records(broker_stack):
    broker, facade, _, work = broker_stack
    controller = ready(broker_stack)
    result = controller.run(deadline(2))
    assert result.unit_cleanup_complete and result.normal_records_complete
    assert all(not u.emergency and u.generation == 1 for u in result.units)
    assert [u.unit_id for u in result.units] == list(
        reversed(broker.owner._prepared.resource_order)
    )
    assert not select.select([broker.connection.child._capability.fileno()], [], [], 0)[
        0
    ]
    for issuer in broker.issuers:
        assert issuer._stop_ack.state & 8 and issuer._retire_ack.state & 128
    records = FileEvidenceJournal(work.parent / "m3.jsonl").public_records()
    assert [r["status"] for r in records if r["status"] in ("stopped", "cleaned")] == [
        "stopped",
        "cleaned",
    ] * 2
    events = EvidenceStore.read_run(work.parent / "argus").records()
    assert len([e for e in events if e["producerId"] == "maestro.teardown13"]) == 8
    before = len(records)
    assert controller.run(deadline(1)) is result
    assert len(FileEvidenceJournal(work.parent / "m3.jsonl").records) == before
    output = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if output:
        (
            Path(output) / ("native-teardown-public-" + str(os.getpid()) + ".json")
        ).write_text(
            json.dumps(
                dict(
                    public_m3=records,
                    argus_events=events,
                    source_sha256=hashlib.sha256(
                        Path(__file__).read_bytes()
                    ).hexdigest(),
                    native_workload_waits_observed=True,
                    original_helper_reaping_is_separate=True,
                    full_M1_complete=False,
                )
            )
        )


def test_scoped_native_leaf_cleanup_keeps_other_original_unit_live(broker_stack):
    broker, facade, _, work = broker_stack
    controller = ready(broker_stack)
    source, sink = broker.owner._prepared.resource_order
    stopped = controller.phase(sink, "stop", deadline(1))
    assert stopped.leader_reaped and stopped.boundary_empty and not stopped.emergency
    cleaned = controller.phase(sink, "cleanup", deadline(1))
    assert cleaned.unit_cleanup_complete and cleaned.normal_records_complete
    assert not broker.owner._closed and not broker.owner.latch.cancelled
    assert broker.connection.epoch == 0
    assert facade.check_unit_health(source, deadline(0.5)).ready
    count = len(FileEvidenceJournal(work.parent / "m3.jsonl").records)
    assert controller.phase(sink, "stop", deadline(1)) is stopped
    assert controller.phase(sink, "cleanup", deadline(1)) is cleaned
    assert len(FileEvidenceJournal(work.parent / "m3.jsonl").records) == count


def test_native_prerequisite_stop_requires_dependent_cleanup(broker_stack):
    broker, _, _, work = broker_stack
    controller = ready(broker_stack)
    source = broker.owner._prepared.resource_order[0]
    before = len(FileEvidenceJournal(work.parent / "m3.jsonl").records)
    with pytest.raises(ValueError, match="DEPENDENTS"):
        controller.phase(source, "stop", deadline(1))
    assert len(FileEvidenceJournal(work.parent / "m3.jsonl").records) == before
    assert not broker.owner.latch.cancelled


def test_stalled_native_stop_is_revoked_before_fallback_release(broker_stack):
    broker, _, _, _ = broker_stack
    controller = ready(broker_stack)
    sink = broker.owner._prepared.resource_order[-1]
    signal.pidfd_send_signal(
        broker.connection.child._capability.fileno(), signal.SIGSTOP
    )
    result = controller.phase(sink, "stop", deadline(1))
    assert result.emergency and result.boundary_released
    assert not result.normal_records_complete and not result.leader_reaped
    assert broker.connection.child._result is not None
    with pytest.raises(ProcessLookupError):
        signal.pidfd_send_signal(
            broker.connection.child._capability.fileno(), signal.SIGCONT
        )


def test_bad_cleanup_ack_retains_actual_wait_but_no_normal_completeness(
    broker_stack, monkeypatch
):
    broker, _, storage, _ = broker_stack
    controller = ready(broker_stack)
    sink = broker.owner._prepared.resource_order[-1]
    assert not controller.phase(sink, "stop", deadline(1)).emergency
    original = storage._rpc

    def damaged(kind, body, end):
        operation, until, response = original(kind, body, end)
        if (
            kind == "teardown"
            and body["phase"] == "cleanup"
            and body["stage"] == "outcome"
        ):
            response = dict(response, m3_sequence=0)
        return operation, until, response

    monkeypatch.setattr(storage, "_rpc", damaged)
    result = controller.phase(sink, "cleanup", deadline(1))
    assert result.emergency and result.leader_reaped and result.boundary_released
    assert not result.normal_records_complete


def test_unstaged_native_units_are_fenced_without_invented_workload_wait(broker_stack):
    broker, facade, _, _ = broker_stack
    result = ReverseTeardown(facade, per_unit_seconds=0.8).run(deadline(2))
    assert result.starts_closed and broker._cancel_result.native_epoch_confirmed
    assert all(u.emergency and u.boundary_released for u in result.units)
    assert all(
        not u.leader_reaped and not u.normal_records_complete for u in result.units
    )
    assert all(issuer._handle is None for issuer in broker.issuers)


def test_native_broker_lock_conflict_does_not_mutate_normal_records(broker_stack):
    broker, _, _, work = broker_stack
    controller = ready(broker_stack)
    sink = broker.owner._prepared.resource_order[-1]
    before = FileEvidenceJournal(work.parent / "m3.jsonl").records
    with broker._lock:
        with pytest.raises(ValueError, match="CONFLICT"):
            controller.phase(sink, "stop", deadline(1))
        assert FileEvidenceJournal(work.parent / "m3.jsonl").records == before
        assert not broker.owner.latch.cancelled
        result = broker.cancel("test-independent-cancel", deadline=deadline(0.5))
        assert result.native_epoch_confirmed


def test_actual_native_wait_survives_later_c1_observation_failure(
    broker_stack, monkeypatch
):
    broker, _, _, _ = broker_stack
    controller = ready(broker_stack)
    sink = broker.owner._prepared.resource_order[-1]

    def unavailable(*args, **kwargs):
        raise ValueError("test-only-C1-observation-failure")

    monkeypatch.setattr(controller.manager, "terminate", unavailable)
    result = controller.phase(sink, "stop", deadline(1))
    assert result.emergency and result.leader_reaped and result.boundary_released
    assert not result.normal_records_complete
    assert broker.issuer(sink)._stop_ack.state & 8


def test_expired_repeated_revocation_retains_actual_original_helper_wait(broker_stack):
    import time
    from xverse.maestro.time import HostDeadline

    broker, _, _, _ = broker_stack
    first = broker.connection.revoke(deadline(0.5))
    assert first.issuer_dead and first.issuer_reaped
    repeated = broker.connection.revoke(
        HostDeadline(broker.session.session, time.monotonic() - 0.1)
    )
    assert (
        repeated.issuer_dead and repeated.issuer_reaped and repeated.diagnostic is None
    )
