"""Original helper closure after v6 terminal writer result; no writer RPC replay."""
import hashlib
import json
import os
from pathlib import Path

import pytest
from xverse.maestro.persistence import PersistenceClient,PersistenceError
from xverse.maestro.run_closure import RunClosure
from .test_terminal_runtime import scheduled,run
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries,deadline


@pytest.mark.parametrize('case',['closed','lost-close-ack','required-missing'])
def test_original_helper_closure_retains_terminal_outcome_without_replaying_writer(request,monkeypatch,case):
    stack,_,driver=scheduled(request,monkeypatch);broker,_,client,work=stack
    original_rpc=PersistenceClient._rpc;original_collect=PersistenceClient.collect_outputs
    def rpc(self,kind,body,end,**kw):
        result=original_rpc(self,kind,body,end,**kw)
        if self is client and case=='lost-close-ack' and kind=='terminal-report' and body['action']=='close':
            raise PersistenceError('ML-TEST-LOST-ACK')
        return result
    def collect(self,owner,end):
        if self is client and case=='required-missing':
            for p in work.glob('*.marker'):p.unlink()
        return original_collect(self,owner,end)
    monkeypatch.setattr(PersistenceClient,'_rpc',rpc)
    monkeypatch.setattr(PersistenceClient,'collect_outputs',collect)
    result=run(driver);assert result.terminal is not None,result.diagnostic
    before_failed=client._failed;before_writer=client.last_writer_state
    raw=(work.parent/'argus/manifest.json').read_bytes();calls=[]
    original_incomplete=PersistenceClient.close_incomplete
    def incomplete(self,end):
        calls.append(self)
        return original_incomplete(self,end)
    monkeypatch.setattr(PersistenceClient,'close_incomplete',incomplete)
    closer=RunClosure(broker.session,dispatcher=driver);end=deadline(6)
    closed=closer.close(end)
    assert not calls,'completed original writer must not receive abort-only closure RPC'
    assert closed.cleanup_complete and closed.root_reaped and closed.normal_unit_records_complete,closed
    assert {h.role for h in closed.helpers}=={3,4,5}
    assert all(h.process_reaped for h in closed.helpers)
    assert all(r.empty and r.released for r in closed.boundaries)
    assert closed.terminal_reports==(result.terminal,) and closed.writers==()
    assert closed.terminal_reports[0] is result.terminal
    assert closed.execution_succeeded is (case!='required-missing')
    if case=='closed':assert not closed.diagnostics
    else:assert 'ML-CLOSURE-REPORT-INCOMPLETE' in closed.diagnostics
    assert client._failed is before_failed and client.last_writer_state==before_writer
    assert not client._closure_attempted
    assert (work.parent/'argus/manifest.json').read_bytes()==raw
    assert closer.close(end) is closed
    assert not closed.lifecycle_complete and not closed.ready_for_execution
    output=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        from dataclasses import asdict
        target=Path(output);target.mkdir(parents=True,exist_ok=True)
        closure=asdict(closed)
        closure['terminal_reports']=[r.public_data() for r in closed.terminal_reports]
        (target/('terminal-helper-closure-'+work.parent.name+'.json')).write_text(json.dumps(dict(
            case=case,closure=closure,original_terminal=result.terminal.public_data(),
            original_terminal_sha256=hashlib.sha256(result.terminal.public_bytes).hexdigest(),
            original_manifest_sha256=hashlib.sha256(raw).hexdigest(),no_writer_rpc_replay=True,
            original_fixture=str(work.parent),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            full_M1_complete=False,scientific_result=False),indent=2)+'\n')
