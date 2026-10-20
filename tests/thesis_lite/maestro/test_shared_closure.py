"""Actual shared-authority terminal closure and late-request fencing."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import signal
import threading
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.run_closure import RunClosure
from xverse.maestro.teardown import ReverseTeardown
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_controller import setup, old_dead
from .test_generation_claim import ready, release
from .test_generation_dependents import advance
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def retain(result, stack, suffix):
    root = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if not root:
        return
    work = stack[3]
    reader = EvidenceStore.read_run(work.parent / 'argus')
    records = FileEvidenceJournal(work.parent / 'm3.jsonl').public_records()
    try:
        events = reader.records()
    except Exception:
        events = []
    (Path(root) / ('shared-closure-public-' + str(os.getpid()) + '-' + suffix + '.json')).write_text(json.dumps(dict(
        result=asdict(result), public_m3=records, argus_events=events,
        manifest=reader.manifest, source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        helper_waits_do_not_replace_workload_waits=True, full_M1_complete=False)))


@pytest.mark.parametrize('generation2', [False, True])
def test_actual_shared_closure_keeps_all_original_generation_waits_and_writer_facts(request, monkeypatch, generation2):
    stack, old_teardown, unit = setup(request, monkeypatch)
    broker, facade, _, _ = stack
    if generation2:
        release(old_teardown, unit)
        advance(stack, old_teardown, unit)
    controller = broker.admit_controller('closing-controller', deadline(1))
    assert controller.request(None, 'heartbeat', deadline(0.5))
    closer = RunClosure(broker.session, teardown=ReverseTeardown(facade))
    end = deadline(8)
    result = closer.close(end)
    assert result.cleanup_complete and result.normal_unit_records_complete
    assert result.authority_fenced and result.root_reaped
    assert {h.role for h in result.helpers} == {3,4,5}
    assert all(h.process_reaped for h in result.helpers)
    assert all(b.empty and b.released for b in result.boundaries)
    assert all(f.issued is True and f.direct_child_reaped is True and f.native_retired is True for f in result.native_units)
    assert len(result.native_units) == (3 if generation2 else 2)
    writer = result.writers[0]
    assert writer.acknowledged and writer.abort_completed
    assert writer.before_state == 'open' and writer.after_state == 'failed'
    assert writer.durable_recorded_status == 'incomplete'
    assert not result.lifecycle_complete and not result.ready_for_execution
    assert closer.close(end) is result
    with pytest.raises(ValueError, match='REPEAT'):
        closer.close(end, reason='changed')
    retain(result, stack, str(generation2))


@pytest.mark.parametrize('target', ['authority', 'storage'])
def test_actual_helper_loss_keeps_native_workload_waits_unknown(request, monkeypatch, target):
    stack, _, _, _ = ready(request, monkeypatch)
    broker, _, client, _ = stack
    child = broker.connection.child if target == 'authority' else client.process
    signal.pidfd_send_signal(child._capability.fileno(), signal.SIGKILL if target=='authority' else signal.SIGSTOP)
    result = RunClosure(broker.session, broker=broker, terminal_seconds=0.1).close(deadline(5))
    assert result.root_reaped and result.authority_fenced
    assert all(h.process_reaped for h in result.helpers)
    assert all(b.empty and b.released for b in result.boundaries)
    assert not result.cleanup_complete and not result.normal_unit_records_complete
    assert next(h for h in result.helpers if h.role==4).direct_child_reaped is False
    assert 'ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN' in result.diagnostics
    retain(result, stack, target)


def test_stopped_authority_with_queued_request_is_dead_before_scope_release(broker_stack):
    broker, _, _, work = broker_stack
    unit = broker.owner._prepared.resource_order[0]
    end = deadline(1.2)
    broker.owner.commit_intent(unit, end)
    child = broker.connection.child
    signal.pidfd_send_signal(child._capability.fileno(), signal.SIGSTOP)
    failures = []
    def stage():
        try:
            broker.issuer(unit).stage(end)
        except Exception as error:
            failures.append(type(error).__name__)
    requester = threading.Thread(target=stage)
    requester.start()
    until = time.monotonic()+0.5
    while not broker.connection._lock.locked() and time.monotonic()<until:
        time.sleep(0.005)
    assert broker.connection._lock.locked()
    result = RunClosure(broker.session, broker=broker, terminal_seconds=0.1).close(deadline(5))
    requester.join(timeout=1)
    assert not requester.is_alive() and failures
    assert child._result is not None and result.authority_fenced
    assert all(b.empty and b.released for b in result.boundaries)
    assert not result.cleanup_complete
    assert next(f for f in result.native_units if f.unit_id==unit).issued is None
    assert not list(work.glob('*.marker'))
    with pytest.raises(ProcessLookupError):
        signal.pidfd_send_signal(child._capability.fileno(), signal.SIGCONT)
    retain(result, broker_stack, 'queued')


@pytest.mark.parametrize('name', ['broker', 'owner', 'facade', 'teardown'])
def test_shared_closure_normal_conflict_has_no_cancel_effect(request, monkeypatch, name):
    stack, teardown, _, _ = ready(request, monkeypatch)
    broker, facade, _, _ = stack
    lock = {'broker':broker._lock,'owner':broker.owner._lock,'facade':facade._lock,'teardown':teardown._lock}[name]
    closer = RunClosure(broker.session, teardown=teardown)
    lock.acquire()
    try:
        with pytest.raises(ValueError, match='CONFLICT'):
            closer.close(deadline(6))
        assert not broker.owner.latch.cancelled and broker.owner._dispatch_owner is None
    finally:
        lock.release()


def test_original_never_attempted_generations_need_no_invented_child_wait(broker_stack):
    broker = broker_stack[0]
    result = RunClosure(broker.session, broker=broker).close(deadline(5))
    assert result.cleanup_complete and not result.normal_unit_records_complete
    assert len(result.native_units)==2
    assert all(f.issued is False and f.direct_child_reaped is None for f in result.native_units)
    assert result.authority_fenced and all(b.released for b in result.boundaries)
    retain(result, broker_stack, 'never-issued')
