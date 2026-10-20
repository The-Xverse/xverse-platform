"""Original v6 issuer-registry loss and actual queued late-request fencing."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import threading
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.affa_protocol import AuthorityKind as K
from xverse.maestro.run_closure import RunClosure
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_terminal_runtime import scheduled
from .test_composed_persistence_termination import threaded_run
from .test_composed_authority_interruptions import (
    Barrier, heartbeat_binary as heartbeat_binary, sentinel as sentinel,
    instrument, read_owned, observed_members, wait_for, retain,
)
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def public_closure(result):
    if result is None:
        return None
    data = asdict(result)
    data['terminal_reports'] = [r.public_data() for r in result.terminal_reports]
    data['cleanup_complete'] = result.cleanup_complete
    return data


def save(stack, case, observations, before, after, results, failures, primary, fallback):
    broker, _, _, work = stack
    retain('issuer-loss-'+work.parent.name+'.json', dict(case=case, observations=observations,
        original_fixture=str(work.parent), primary=public_closure(primary),
        fallback=public_closure(fallback), dispatcher_failures=failures,
        dispatcher_result=dict(execution_succeeded=results[0].execution_succeeded,
            diagnostic=results[0].diagnostic, terminal_recorded=results[0].terminal_recorded)
            if results else None,
        public_m3=list(FileEvidenceJournal(work.parent/'m3.jsonl').public_records()),
        argus_events=EvidenceStore.read_run(work.parent/'argus').records(),
        markers={p.name:p.read_text() for p in work.glob('*.marker')},
        sentinel_before=before, sentinel_after=after,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        full_runtime_case_complete=False, full_M1_complete=False, accepted=False))


@pytest.mark.parametrize('fault', ['current-copy', 'generation-copy', 'generation-empty', 'generation-nonmapping'])
def test_original_registry_loss_denies_adoption_but_preserves_cancellation_and_cleanup(request, monkeypatch, sentinel, fault):
    before = sentinel()
    stack, _, driver = scheduled(request, monkeypatch)
    broker, facade, client, work = stack
    unit = driver.prepared.resource_order[0]
    issuer = broker.issuer(unit)
    barrier = Barrier()
    instrument(monkeypatch, stack, 'release-after-reply', barrier)
    thread, results, failures = threaded_run(driver)
    attribute = '_issuers' if fault == 'current-copy' else '_generation_issuers'
    original = getattr(broker, attribute)
    replacement = dict(original) if fault.endswith('copy') else {} if fault.endswith('empty') else None
    observations = dict(fault=fault, ordinary_rejected=False, cancellation_error=None,
        primary_error=None, restoration_after_original_cleanup=False)
    primary = fallback = None
    try:
        assert barrier.reached.wait(3), failures
        wait_for(lambda: (work/'source-binding.marker').is_file())
        observations['members_before_loss'] = list(observed_members(
            broker.session.boundaries._entries[issuer._image.admission.descriptor.key].fd))
        observations['actual_release_ack_before_loss'] = issuer._release_ack is not None
        setattr(broker, attribute, replacement)  # explicit ordinary-registry fault only
        sequence = broker.connection.sequence
        with pytest.raises(ValueError):
            broker.issuer(unit)
        with pytest.raises(ValueError):
            issuer.observe(issuer._handle, deadline(.3))
        assert broker.connection.sequence == sequence
        observations['ordinary_rejected'] = True
        try:
            driver.cancel('owned-registry-loss')
        except Exception as error:
            observations['cancellation_error'] = str(error)
        observations['cancellation_completed'] = time.monotonic()
    finally:
        barrier.resume.set()
        thread.join(timeout=18)
    try:
        assert not thread.is_alive(), 'original dispatcher not terminal'
        try:
            primary = RunClosure(broker.session, dispatcher=driver).close(deadline(6))
        except Exception as error:
            observations['primary_error'] = type(error).__name__+': '+str(error)
            # A primary defect must remain failed. Original-root cleanup protects
            # the owned fixture without reconstructing or adopting a broker.
            fallback = RunClosure(broker.session).close(deadline(6))
        closed = primary if primary is not None else fallback
        assert closed.root_reaped and all(h.process_reaped for h in closed.helpers)
        assert all(b.empty and b.released for b in closed.boundaries)
        after = sentinel()
        assert broker.connection.child._result is not None
        # Harness-only restoration after all original authority and scopes died.
        # It does not reopen starts or grant a replacement registry any rights.
        setattr(broker, attribute, original)
        observations['restoration_after_original_cleanup'] = True
        observations['restored_at'] = time.monotonic()
        assert broker.owner.latch.cancelled
        save(stack, fault, observations, before, after, results, failures, primary, fallback)
    finally:
        if getattr(broker, attribute) is not original:
            # Failed assertions still leave the original fixture responsible for
            # its own exact cleanup. This is never reported as runtime recovery.
            broker.session.cancel('owned-test-emergency')
            broker.session.drain(deadline(2))
            for entry in broker.session.boundaries._entries.values():
                if entry.state != 'released':
                    broker.session.boundaries.force_cleanup(entry.descriptor)
            setattr(broker, attribute, original)
    assert observations['cancellation_error'] is None, observations
    assert not failures and len(results) == 1, failures
    assert primary is not None and observations['primary_error'] is None, observations
    assert fallback is None
    assert not primary.cleanup_complete and not primary.lifecycle_complete
    assert 'ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN' in primary.diagnostics
    assert not list(work.glob('sink-binding.marker'))
    assert (work/'source-binding.marker').read_text() == 'EXEC\n'


@pytest.mark.parametrize('kind', [K.STAGE, K.RELEASE], ids=['stage', 'release'])
def test_original_queued_request_is_dead_before_exact_fallback_release(request, monkeypatch, sentinel, kind):
    before = sentinel()
    stack, _, driver = scheduled(request, monkeypatch)
    broker, _, _, work = stack
    connection, child = broker.connection, broker.connection.child
    fd = child._capability.fileno()
    exchange, receive = connection._exchange, connection._receive
    barrier, local = Barrier(), threading.local()
    observations, frames = dict(removal_fences=[]), []
    def stopped_exchange(frame, **kw):
        local.kind = frame.kind
        try:
            if frame.kind == kind and not frames:
                frames.append(frame)
                signal.pidfd_send_signal(fd, signal.SIGSTOP)
                end = time.monotonic()+.2
                stopped = None
                while time.monotonic() < end:
                    stopped = os.waitid(os.P_PIDFD, fd, os.WSTOPPED|os.WNOHANG|os.WNOWAIT)
                    if stopped is not None:
                        break
                    time.sleep(.001)
                assert stopped is not None and stopped.si_status == signal.SIGSTOP
                observations['original_stopped_at'] = time.monotonic()
            return exchange(frame, **kw)
        finally:
            local.kind = None
    def pending_receive(until):
        if getattr(local, 'kind', None) == kind:
            barrier.stop('actual-queued-'+kind.name)
        return receive(until)
    manager, cleanup = broker.session.boundaries, broker.session.boundaries.force_cleanup
    def scoped_cleanup(descriptor, **kw):
        if not descriptor.unit_id.startswith('helper:'):
            observations['removal_fences'].append(dict(unit=descriptor.unit_id,
                issuer_reaped=child._result is not None, pidfd_dead=bool(select.select([fd],[],[],0)[0]),
                before_removal=time.monotonic()))
        return cleanup(descriptor, **kw)
    monkeypatch.setattr(connection, '_exchange', stopped_exchange)
    monkeypatch.setattr(connection, '_receive', pending_receive)
    monkeypatch.setattr(manager, 'force_cleanup', scoped_cleanup)
    thread, results, failures = threaded_run(driver)
    try:
        assert barrier.reached.wait(3), failures
        observations['original_request_sent_at'] = barrier.observations[0]['reached']
        assert connection._lock.locked() and len(frames) == 1
        assert not list(work.glob('*.marker'))
        driver.cancel('owned-queued-cancel')
        cancelled = broker.cancel('owned-queued-cancel')
        observations['cancellation'] = asdict(cancelled)
        observations['original_wait_observed_at'] = time.monotonic()
        assert cancelled.issuer_dead and cancelled.issuer_reaped and child._result is not None
    finally:
        barrier.resume.set()
    thread.join(timeout=18)
    assert not thread.is_alive() and not failures and len(results) == 1, failures
    primary = RunClosure(broker.session, dispatcher=driver).close(deadline(6))
    after = sentinel()
    sequence = connection.sequence
    with pytest.raises(ValueError):
        exchange(frames[0])
    with pytest.raises(ProcessLookupError):
        signal.pidfd_send_signal(fd, signal.SIGCONT)
    observations['late_original_request_rejected'] = True
    assert connection.sequence == sequence and not list(work.glob('*.marker'))
    save(stack, 'queued-'+kind.name, observations, before, after, results, failures, primary, None)
    assert primary.root_reaped and primary.authority_fenced and not primary.cleanup_complete
    assert all(h.process_reaped for h in primary.helpers)
    assert all(b.empty and b.released for b in primary.boundaries)
    assert observations['removal_fences']
    assert all(r['issuer_reaped'] and r['pidfd_dead'] and
        r['before_removal'] >= observations['original_wait_observed_at'] for r in observations['removal_fences'])
