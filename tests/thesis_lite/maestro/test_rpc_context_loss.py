"""Optional diagnostics cannot erase actual original terminal cleanup results."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import pytest
from xverse.maestro.dispatcher import FiniteDispatcher
from xverse.maestro.run_closure import RunClosure
from .test_runtime_entry import runtime as runtime
from .test_persistence import storage as storage, deadline
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries
from .test_affa_native import authority_binary as authority_binary
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary


@pytest.mark.parametrize('fault',['owner-tag','context-reference','context-content'])
def test_diagnostic_metadata_loss_after_actual_cleanup_preserves_original_result(runtime,monkeypatch,fault):
    entry,scope,work=runtime;statement=FiniteDispatcher._statement;close=RunClosure.close
    stopped=[];observed={};original={};errors=[];result=None
    def blocked(self,*a,**kw):
        if not stopped:
            os.kill(entry._storage.process.pid,signal.SIGSTOP);stopped.append(True)
        return statement(self,*a,**kw)
    def closed(self,*a,**kw):
        outcome=close(self,*a,**kw);client=entry._runtime_pins[1]
        assert outcome.root_reaped and all(h.process_reaped for h in outcome.helpers)
        assert all(b.empty and b.released for b in outcome.boundaries)
        failure=client.rpc_failure;assert failure.diagnostic=='ML-PERSIST-TIMEOUT'
        original.update(client=client,owner=client._original,record=failure,stage=failure.stage)
        observed.update(original_failure=asdict(failure),actual_root_wait=True,actual_helpers_reaped=True,
            original_C1_released=True,no_workload_output=not list(work.glob('*.marker')))
        if fault=='owner-tag':client._original=object()
        elif fault=='context-reference':client._rpc_failure=object()
        else:object.__setattr__(failure,'stage','counterfeit-stage')
        return outcome
    monkeypatch.setattr(FiniteDispatcher,'_statement',blocked)
    monkeypatch.setattr(RunClosure,'close',closed)
    try:
        try:result=entry.start(scope)
        except Exception as error:errors.append(type(error).__name__+': '+str(error))
    finally:
        assert observed.get('actual_root_wait') and observed.get('original_C1_released')
        # Restore only original local metadata after factual cleanup, for disposal.
        client=original['client'];client._original=original['owner'];client._rpc_failure=original['record']
        object.__setattr__(original['record'],'stage',original['stage'])
        if result is None and entry._runtime_pins[2] is not None:entry._runtime_pins[2].dispose()
        output=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
        if output:
            (Path(output)/('rpc-context-loss-'+fault+'.json')).write_text(json.dumps(dict(
                fault=fault,primary_returned=result is not None,primary_errors=errors,
                observation_unavailable=result is not None and result.persistence_failure is None,
                diagnostics=list(result.diagnostics) if result is not None else [],
                original_metadata_restored_after_actual_cleanup=True,actual_M1_admissions=0,**observed),indent=2)+'\n')
    assert not errors,errors
    assert result is not None and result.closure.root_reaped and not result.execution_succeeded
    assert result.persistence_failure is None
    assert 'ML-RUNTIME-RPC-CONTEXT-UNRESOLVED' in result.diagnostics
    assert entry.start(scope) is result and not result.ready_for_execution


def test_unavailable_capture_cannot_bypass_original_rpc_cancellation(storage,monkeypatch):
    start,_,config,_,latch=storage;owner,client,_,_=start('flush-ignoreterm')
    first_pin=client._rpc_failure_pin;del client._rpc_failure_pin
    errors=[];external_fallback=False
    try:
        try:owner.commit_intent(config.prepared.units[0].unit_id,deadline(.35))
        except Exception as error:errors.append(error)
        primary_cancelled=latch.cancelled and client._failed
        with pytest.raises(ValueError,match='RPC-CONTEXT'):client.rpc_failure
    finally:
        client._rpc_failure_pin=first_pin
        if not client._failed:
            external_fallback=True;client._fail()  # Original owned fallback, explicitly recorded.
        drained=client.drain(deadline(1))
        out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
        if out:(Path(out)/'capture-unavailable.json').write_text(json.dumps(dict(
            primary_cancelled=primary_cancelled,external_fallback=external_fallback,
            actual_worker_wait=drained.worker_reaped,diagnostics=[str(e) for e in errors],actual_M1_admissions=0),indent=2)+'\n')
    assert primary_cancelled and not external_fallback and drained.worker_reaped
    assert len(errors)==1 and str(errors[0])=='ML-PERSIST-TIMEOUT'
