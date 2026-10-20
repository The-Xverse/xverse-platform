"""Original whole start must retain cleanup after internal issuer-registry loss."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time

import pytest
from xverse.maestro.affa_client import AuthorityConnection
from xverse.maestro.affa_protocol import AuthorityKind as K
from xverse.maestro.dispatcher import FiniteDispatcher
from xverse.maestro.run_broker import RunBroker
from xverse.maestro.run_closure import RunClosure
from xverse.maestro.runtime_entry import _OriginalRuntimeRegistry
from .test_runtime_entry import runtime as runtime
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline
from .test_affa_native import authority_binary as authority_binary
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_composed_authority_interruptions import (
    heartbeat_binary as heartbeat_binary, sentinel as sentinel, observed_members, wait_for,
)


def closure_data(result):
    if result is None:
        return None
    data = asdict(result)
    data['terminal_reports'] = [r.public_data() for r in result.terminal_reports]
    data['cleanup_complete'] = result.cleanup_complete
    return data


@pytest.mark.parametrize('window', ['before-handle', 'after-release'])
def test_original_whole_start_retains_primary_cleanup_after_issuer_loss(
        runtime, request, monkeypatch, sentinel, window):
    entry, scope, work = runtime
    registry = _OriginalRuntimeRegistry(1)
    registry.reserve(entry)
    source = entry._pins[2][0].descriptor.unit_id
    launcher = entry._pins[1]
    captured, facts = {}, dict(window=window, injection_reached=False,
        primary_returned=False, primary_exceptions=[], fallback=None,
        original_fixture=str(work.parent), full_M1_complete=False,
        full_runtime_case_complete=False, actual_M1_admissions=0,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    facts['sentinel_before'] = sentinel()

    def retain(value, end, root, manager, out):
        # This runs after the primary assertions, preserving failures before any
        # harness cleanup. Original descriptors are never acquired by discovery.
        primary = value._result
        facts['primary_returned'] = primary is not None
        facts['primary_closure'] = closure_data(primary.closure) if primary else None
        session = value._runtime_pins[0]
        broker = captured.get('broker', value._runtime_pins[2])
        try:
            if session is not None and (session._root_result is None
                    or any(c._result is None for c in session._children.values())
                    or any(e.state != 'released' for e in manager._entries.values())):
                fallback = RunClosure(session).close(end.closure, reason='external-owned-issuer-loss-fallback')
                facts['fallback'] = closure_data(fallback)
            assert session is not None and session._root_result is not None
            assert all(c._result is not None for c in session._children.values())
            assert all(e.state == 'released' for e in manager._entries.values())
            facts.update(actual_original_root_wait=True, actual_original_helper_waits=True,
                actual_registered_helpers=len(session._children), all_original_C1_released=True,
                ordinary_map_restored_after_actual_cleanup=False)
            if captured:
                broker._generation_issuers = captured['original_map']
                facts['ordinary_map_restored_after_actual_cleanup'] = True
            assert launcher._process.stderr.read() == b''
            if primary is not None:
                value.dispose()
            else:
                if broker is not None:
                    broker.dispose()
                launcher.dispose()
        finally:
            if out:
                with (Path(out) / ('runtime-issuer-loss-' + window + '.json')).open('x') as stream:
                    json.dump(facts, stream, indent=2)
                    stream.write('\n')

    request.node._runtime_failure_retainer = retain

    def lose(broker):
        assert not captured and entry._lock.locked()
        issuer = broker.issuer(source)
        boundary = broker.session.boundaries._entries[issuer._image.admission.descriptor.key]
        members = list(observed_members(boundary.fd))
        assert members, 'original native child must exist at injection'
        captured.update(broker=broker, original_map=broker._generation_issuers)
        facts.update(injection_reached=True, injected_at=time.monotonic(),
            native_members_before_loss=members, handle_published_before_loss=issuer._handle is not None,
            release_ack_before_loss=issuer._release_ack is not None,
            start_lock_held=True, ordinary_rejected=False)
        if window == 'before-handle':
            assert issuer._handle is None and issuer._release_ack is None
            assert not list(work.glob('*.marker'))
        else:
            assert issuer._handle is not None and issuer._release_ack is not None
            wait_for(lambda: (work / 'source-binding.marker').is_file())
            assert (work / 'source-binding.marker').read_bytes() == b'EXEC\n'
        broker._generation_issuers = {}
        sequence = broker.connection.sequence
        forged = object.__new__(RunBroker)
        forged.__dict__.update(broker.__dict__)
        with pytest.raises(ValueError):
            RunClosure(broker.session, broker=forged)
        closer = RunClosure(broker.session, broker=broker)
        assert closer._broker is broker and broker.connection.sequence == sequence
        facts['explicit_original_cleanup_constructor_accepted_without_IO'] = True
        facts['copied_broker_rejected_without_IO'] = True
        with pytest.raises(ValueError):
            broker.issuer(source)
        with pytest.raises(ValueError):
            issuer.observe(issuer._handle, deadline(.3))
        assert broker.connection.sequence == sequence
        facts['ordinary_rejected'] = True
        assert registry.stop('fixture-run', reason='owned-inner-issuer-loss') == 1
        assert registry.stop('fixture-run', reason='owned-inner-issuer-loss') == 1
        assert broker.owner.latch.cancelled
        facts['original_stop_returned'] = True

    exchange = AuthorityConnection._exchange
    statement = FiniteDispatcher._statement

    def staged(connection, frame, **kw):
        reply = exchange(connection, frame, **kw)
        broker = entry._runtime_pins[2]
        if (window == 'before-handle' and frame.kind == K.STAGE and not captured
                and broker is not None and connection is broker.connection):
            lose(broker)
        return reply

    def released(driver, kind, step, **kw):
        reply = statement(driver, kind, step, **kw)
        if (window == 'after-release' and kind == 'step-complete'
                and step.phase == 'start' and not captured):
            lose(entry._runtime_pins[2])
        return reply

    monkeypatch.setattr(AuthorityConnection, '_exchange', staged)
    monkeypatch.setattr(FiniteDispatcher, '_statement', released)
    try:
        result = registry.start('fixture-run', scope)
    except Exception as error:
        facts['primary_exceptions'].append(type(error).__name__ + ': ' + str(error))
        raise
    facts.update(primary_returned=True, execution_succeeded=result.execution_succeeded,
        primary_closure=closure_data(result.closure), startup=asdict(result.startup),
        diagnostics=list(result.diagnostics), markers={p.name:p.read_text() for p in work.glob('*.marker')})
    assert facts['injection_reached'] and facts['ordinary_rejected']
    assert result.dispatch is not None and not result.execution_succeeded
    assert result.closure is not None and result.closure.root_reaped
    assert all(h.process_reaped for h in result.closure.helpers)
    assert all(b.empty and b.released for b in result.closure.boundaries)
    assert not result.cleanup_complete and not result.lifecycle_complete and not result.ready_for_execution
    assert not result.closure.normal_unit_records_complete
    assert not (work / 'sink-binding.marker').exists()
    if window == 'before-handle':
        assert not list(work.glob('*.marker'))
    facts['sentinel_after'] = sentinel()
    process = launcher._process_pin
    monkeypatch.setattr(launcher, 'launch', lambda *a, **kw: pytest.fail('matching whole-start replay created a process'))
    assert registry.start('fixture-run', scope) is result
    assert launcher._process_pin is process
    assert registry.collect('fixture-run') is result.dispatch.collection
    facts.update(matching_result_retained=True, matching_collection_retained=True,
        replay_original_process_unchanged=True)
