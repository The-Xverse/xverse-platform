"""Original native control admission, host expiry and cancellation frontiers."""
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import select
import threading
import time

import pytest
from xverse.maestro.run_closure import RunClosure
from xverse.maestro.runtime_verification import runtime_admission_digest
from xverse.maestro.time import HostDeadline
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_active_controller_recovery import binaries as binaries
from .test_terminal_controller_inventory import scheduled
from .test_terminal_runtime import run, verify
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as original_binaries, deadline


@pytest.mark.parametrize('control', ['restart', 'recovery'])
@pytest.mark.parametrize('mode', ['past', 'foreign-session', 'beyond-active', 'expire-queued', 'cancel-queued'])
def test_original_control_rejection_keeps_unspent_authority(request, monkeypatch, control, mode):
    stack, controller, driver = scheduled(request, monkeypatch, restarts=True,
        transitive=True, controller_recovery=True)
    broker, facade, client, work = stack
    leaf = next(u for u in driver.prepared.resource_order if u.endswith('/terminal-instance'))
    future = next(c for c in client._future_contexts if c.binding.unit_id == leaf)
    session = 'rejected-successor-' + mode
    tickets, transitions, queue_facts, errors = [], [], [], []
    result = closure = None
    original_worker, original_authority = client.process, broker.connection.child
    path = Path(os.environ['MAESTRO_BOUNDARY_RECEIPTS']) if os.environ.get('MAESTRO_BOUNDARY_RECEIPTS') else None
    case = control + '-' + mode

    def frontier():
        records = FileEvidenceJournal(work.parent / 'm3.jsonl').public_records()
        return dict(storage_sequence=client._sequence, authority_sequence=broker.connection.sequence,
            m3_sha256=hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest(),
            controller_sessions=[c.session_id for c in broker._controllers],
            handles=[asdict(i._handle) if i._handle is not None else None for i in broker.issuers],
            generations=sorted([list(k) for k in broker._generation_issuers]),
            view_epoch=broker.owner._view_epoch,
            stopped=sorted(driver.teardown._stopped), cleaned=sorted(driver.teardown._cleaned))

    def submit(end, *, late=False):
        if control == 'restart':
            context = next(c for c in client._future_contexts if c.binding.unit_id != leaf) if late else future
            return driver.restart(client.run_id, context.binding.unit_id,
                permit=context.binding.permit, generation=2, deadline=end)
        return driver.replace_controller(client.run_id,
            session_id='late-successor' if late else session, deadline=end)

    def outcome(ticket):
        return driver.restart_result(ticket) if control == 'restart' else driver.controller_recovery_result(ticket)

    def watch(method, pending):
        original = getattr(driver, method)
        def observed():
            selected = bool(tickets) and getattr(driver, pending) is not None
            before = frontier() if selected else None
            try:
                return original()
            finally:
                if selected:
                    after = frontier()
                    value = outcome(tickets[0])
                    transitions.append(dict(method=method, before=before, after=after,
                        outcome=asdict(value) if value else None, observed_at=time.monotonic()))
                    assert before == after, 'rejected control performed an authority/resource effect'
        monkeypatch.setattr(driver, method, observed)

    watch('_drain_restart' if control == 'restart' else '_drain_controller_recovery',
          '_restart_pending' if control == 'restart' else '_recovery_pending')
    watch('_close_restarts', '_restart_pending' if control == 'restart' else '_recovery_pending')
    statement = driver._statement
    submitted = False
    def enqueue(kind, step, **kw):
        nonlocal submitted
        response = statement(kind, step, **kw)
        if submitted or kind != 'step-complete' or step.step_id != 'observe-unrelated':
            return response
        submitted = True
        now = time.monotonic()
        end = HostDeadline(client.session, now + .2 if mode == 'expire-queued' else driver._active_end)
        if mode == 'past':
            end = HostDeadline(client.session, now - .01)
        elif mode == 'foreign-session':
            end = HostDeadline('foreign-control-clock', end.monotonic_seconds)
        elif mode == 'beyond-active':
            end = HostDeadline(client.session, driver._active_end + .01)
        before = frontier()
        if mode in ('past', 'foreign-session', 'beyond-active'):
            with pytest.raises(ValueError) as failure:
                submit(end)
            errors.append(str(failure.value))
        else:
            ticket = submit(end)
            tickets.append(ticket)
            assert outcome(ticket) is None
            assert submit(end) is ticket
            with pytest.raises(ValueError, match='ORIGINAL'):
                outcome(replace(ticket))
        after = frontier()
        assert before == after, 'queue/admission performed an authority/resource effect'
        fact = dict(before=before, after=after, end=asdict(end), queued_at=now,
            active_end=driver._active_end, work_end=driver._work_end)
        if mode == 'expire-queued':
            # Real host time passes; no fake clock or replacement authority/end.
            select.select([], [], [], max(0, end.monotonic_seconds - time.monotonic()) + .002)
            fact['expired_at'] = time.monotonic()
            assert fact['expired_at'] >= end.monotonic_seconds
        elif mode == 'cancel-queued':
            failures = []
            def cancel():
                try:
                    driver.cancel('active-control-native-cancel')
                except BaseException as error:
                    failures.append(error)
            thread = threading.Thread(target=cancel)
            thread.start()
            thread.join(2)
            assert not thread.is_alive() and not failures, failures
            assert thread.ident != broker.owner._dispatch_thread and broker.owner.latch.cancelled
            fact.update(cancel_thread=thread.ident, coordinator_thread=broker.owner._dispatch_thread,
                after_cancel=frontier(), cancelled_at=time.monotonic())
        queue_facts.append(fact)
        return response
    monkeypatch.setattr(driver, '_statement', enqueue)
    if path:
        path.mkdir(parents=True, exist_ok=True)
        with (path / ('control-deadline-inputs-' + case + '.json')).open('x') as stream:
            json.dump(dict(original_admission=json.loads(client.coverage.public_bytes),
                admission_digest=client.coverage_digest, original_collection=json.loads(client.collection.canonical_bytes),
                original_schedule=json.loads(client.schedule.canonical_bytes), generation_ns=client.generation_ns,
                runtime_digest=runtime_admission_digest(client.coverage, client.collection, client.generation_ns),
                original_fixture=str(work.parent), source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), stream, indent=2)
            stream.write('\n')
    try:
        result = run(driver)
        assert submitted and len(queue_facts) == 1, result.diagnostic
        if tickets:
            value = outcome(tickets[0])
            assert value is not None and value.disposition == 'rejected', value
            assert any(t['outcome'] == asdict(value) for t in transitions), transitions
            if mode == 'expire-queued':
                assert value.diagnostic == 'ML-SCHEDULE-' + ('RESTART' if control == 'restart' else 'RECOVERY') + '-DEADLINE'
            assert submit(tickets[0].deadline) is tickets[0]
            before = frontier()
            with pytest.raises(ValueError, match='REPEAT'):
                submit(HostDeadline(client.session, tickets[0].deadline.monotonic_seconds + .01))
            assert frontier() == before
        else:
            assert len(errors) == 1 and not transitions
        before = frontier()
        with pytest.raises(ValueError, match='CLOSED'):
            submit(HostDeadline(client.session, driver._active_end), late=True)
        assert frontier() == before
        assert len(broker._controllers) == 1 and driver._controller is controller and driver.facade is facade
        assert not driver._teardown_history and broker._current_controller is controller
        assert client.process is original_worker and broker.connection.child is original_authority
        records = FileEvidenceJournal(work.parent / 'm3.jsonl').records
        assert {r.details['generation'] for r in records} == {1}
        journal = FileEvidenceJournal(work.parent / 'm3.jsonl')
        assert all(not journal.permit_consumed(c.binding.permit.permit_id, c.binding.permit.nonce)
                   for c in client._future_contexts)
        if mode == 'cancel-queued':
            assert not result.execution_succeeded and result.diagnostic == 'ML-SCHEDULE-CANCELLED'
            assert broker.owner.latch.cancelled
        else:
            assert result.execution_succeeded and result.terminal_recorded, result.diagnostic
            assert verify(client, work.parent / 'argus').complete
        closure = RunClosure(broker.session, dispatcher=driver).close(deadline(6))
        assert closure.cleanup_complete and closure.root_reaped, closure
        assert all(h.process_reaped for h in closure.helpers)
        assert all(b.empty and b.released for b in closure.boundaries)
        assert sum(h.role == 5 for h in closure.helpers) == 1
        assert not closure.lifecycle_complete and not closure.ready_for_execution
    finally:
        if path:
            with (path / ('control-deadline-' + case + '.json')).open('x') as stream:
                json.dump(dict(control=control, mode=mode, queue=queue_facts, transitions=transitions, errors=errors,
                    tickets=[asdict(t) for t in tickets], outcomes=[asdict(outcome(t)) if outcome(t) else None for t in tickets],
                    original_fixture=str(work.parent), public_m3=FileEvidenceJournal(work.parent / 'm3.jsonl').public_records(),
                    terminal=result.terminal.public_data() if result and result.terminal else None,
                    execution_succeeded=result.execution_succeeded if result else None,
                    diagnostic=result.diagnostic if result else None,
                    closure={**asdict(closure), 'terminal_reports':[r.public_data() for r in closure.terminal_reports]} if closure else None,
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    full_increment17_complete=False, scientific_result=False), stream, indent=2)
                stream.write('\n')
