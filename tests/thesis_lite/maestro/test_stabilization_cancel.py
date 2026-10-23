"""S1a (thesis specs/029-lite-stabilization FR-004 to FR-007): a run cancelled while an ordinary persistence
call is about to be sent, or is in flight, keeps a healthy storage owner. The terminal records are
persisted, the writer is closed honestly (finalized, or aborted), and the issued units' native facts are
attested.

Reproduction before repair (S1-T03): on main 8b3d8c8e8 the cancel poisons storage (``_fail()``), so the
writer stays ``open`` with the opening manifest (research R-2; review-stabilization-s1a.md)."""

import threading

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro import persistence as persistence_module
from xverse.maestro.persistence import PersistenceClient

from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_runtime_entry import runtime as runtime

TARGET = 2  # the second ordinary tick-complete statement: every unit is issued by then


@pytest.mark.parametrize('mode', ['pre-send', 'in-flight'])
def test_cancel_during_ordinary_persistence_call_keeps_storage_and_aborts_writer(runtime, monkeypatch, mode):
    entry, scope, work = runtime
    seen = []
    stopped = threading.Event()

    def stop():
        if not stopped.is_set():
            stopped.set()
            assert entry.stop('fixture-run', reason='owned-cancel-' + mode) == 1

    def target(kind, body):
        if kind == 'schedule' and isinstance(body, dict) and body.get('kind') == 'tick-complete':
            seen.append(True)
            return len(seen) == TARGET
        return False

    original_rpc = PersistenceClient._rpc
    original_receive = persistence_module._receive
    armed = threading.local()

    def rpc(self, kind, body, end, **kw):
        hit = target(kind, body) and not stopped.is_set()
        if hit and mode == 'pre-send':
            stop()  # the call itself is refused before it is sent
        armed.value = hit and mode == 'in-flight'
        try:
            return original_rpc(self, kind, body, end, **kw)
        finally:
            armed.value = False

    def receive(*args, **kwargs):
        if getattr(armed, 'value', False):
            armed.value = False
            stop()  # the request is sent; its reply is still pending
        return original_receive(*args, **kwargs)

    monkeypatch.setattr(PersistenceClient, '_rpc', rpc)
    monkeypatch.setattr(persistence_module, '_receive', receive)
    result = entry.start(scope)
    assert stopped.is_set(), 'the targeted call was never reached'
    assert not result.execution_succeeded
    storage = entry._storage
    # FR-005: a cancel is not a storage failure
    assert not storage._failed, result.diagnostics
    assert result.dispatch.diagnostic == 'ML-SCHEDULE-CANCELLED'
    # FR-006: the healthy owner closes the writer, either through the normal terminal path (finalized
    # ``closed``) or through RunClosure's abort (``failed``), and the manifest matches the stream
    assert storage.last_writer_state in ('closed', 'failed'), storage.last_writer_state
    reader = EvidenceStore.read_run(work.parent / 'argus')
    assert reader.manifest['writerState'] == storage.last_writer_state
    reasons = set(reader.assessed_evidence_reasons)
    assert not {r for r in reasons if 'CORRUPT' in r or 'MUTATED' in r or 'WRITER-STATE' in r}, reasons
    # the evidence never presents the cancelled run as a success
    terminal = result.dispatch.terminal.public_data() if result.dispatch.terminal is not None else None
    if terminal is not None:
        assert terminal['report']['terminalSucceeded'] is False and terminal['report']['eligible'] is False
        assert 'terminal-outcome' in terminal['report']['blockers']
    # FR-007: every issued unit is attested as reaped and retired, so cleanup is complete
    issued = [u for u in result.closure.native_units if u.issued is True]
    assert issued and all(u.direct_child_reaped is True and u.native_retired is True for u in issued), result.closure.native_units
    assert result.cleanup_complete, result.closure.diagnostics
