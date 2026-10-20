"""Original in-memory failure facts, never durable ACK/ownership or causal proof."""
from dataclasses import FrozenInstanceError, asdict
import json
import os
from pathlib import Path
import select
import signal
import time
import pytest
from xverse.maestro.persistence import PersistenceRPCFailure
from xverse.maestro.dispatcher import FiniteDispatcher
from .test_persistence import storage as storage, deadline
from .test_boundary import environment as environment
from .test_runtime_entry import runtime as runtime
from .test_launcher import binaries as binaries
from .test_affa_native import authority_binary as authority_binary
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary


def retain(name,**facts):
    out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:(Path(out)/('rpc-failure-'+name+'.json')).write_text(json.dumps(facts,indent=2)+'\n')


@pytest.mark.parametrize('mode,stage,code',[('flush-ignoreterm','receive','ML-PERSIST-TIMEOUT'),('flush-fail','acknowledgement','ML-PERSIST-ACK')])
def test_actual_worker_failure_retains_original_request_and_cleanup(storage,mode,stage,code):
    start,_,config,_,latch=storage;owner,client,announce,_=start(mode)
    original_end=deadline(.35);began=time.monotonic_ns()
    with pytest.raises(ValueError) as raised:owner.commit_intent(config.prepared.units[0].unit_id,original_end)
    failure=client.rpc_failure
    assert type(failure) is PersistenceRPCFailure and failure.stage==stage and failure.diagnostic==code
    assert failure.kind=='commit' and failure.sequence==2 and failure.operation.startswith('ml-') and len(failure.operation)==35
    assert failure.session=='host-session' and failure.deadline_ns==int(original_end.monotonic_seconds*1e9)
    assert began<=failure.started_ns<=failure.failed_ns<=time.monotonic_ns()
    assert select.select([announce],[],[],0)[0] and os.read(announce,1) in (b'H',b'F')
    assert latch.cancelled and client._failed and raised.value.rpc_failure is failure
    with pytest.raises(FrozenInstanceError):failure.stage='changed'
    with pytest.raises(ValueError):client._rpc('abort',{},deadline(.3))
    assert client.rpc_failure is failure
    drained=client.drain(deadline(1));assert drained.worker_reaped and not drained.cleanup_complete
    assert client.rpc_failure is failure
    payload=asdict(failure);assert set(payload)=={'kind','stage','session','sequence','operation','started_ns','deadline_ns','failed_ns','diagnostic'}
    retain(mode,failure=payload,actual_wait=drained.worker_reaped,actual_M1_admissions=0)


def test_successful_call_and_conflict_do_not_fabricate_failure(storage):
    start,_,config,_,_=storage;owner,client,_,_=start()
    assert client.rpc_failure is None
    client._lock.acquire()
    try:
        with pytest.raises(ValueError,match='CONFLICT'):client._rpc('abort',{},deadline(.3))
    finally:client._lock.release()
    assert client.rpc_failure is None
    owner.commit_intent(config.prepared.units[0].unit_id,deadline(1))
    assert client.rpc_failure is None


def test_actual_stopped_storage_returns_original_context_after_runtime_cleanup(runtime,monkeypatch):
    entry,scope,_=runtime;original=FiniteDispatcher._statement;stopped=[]
    def statement(self,kind,step,**kw):
        if not stopped:
            os.kill(entry._storage.process.pid,signal.SIGSTOP);stopped.append(True)
        return original(self,kind,step,**kw)
    monkeypatch.setattr(FiniteDispatcher,'_statement',statement)
    result=entry.start(scope)
    assert not result.execution_succeeded and result.closure.root_reaped
    assert all(h.process_reaped for h in result.closure.helpers)
    failure=result.persistence_failure
    assert failure is entry._runtime_pins[1].rpc_failure and failure.kind=='schedule'
    assert failure.stage=='receive' and failure.diagnostic=='ML-PERSIST-TIMEOUT'
    assert failure.failed_ns>=failure.deadline_ns and not result.ready_for_execution
    assert entry.start(scope) is result
    retain('whole-runtime',failure=asdict(failure),original_root_wait=result.closure.root_reaped,actual_helpers_reaped=True,actual_M1_admissions=0)


@pytest.mark.parametrize('mode,stage',[('init-hang','receive'),('init-fail','acknowledgement')])
def test_constructor_failure_keeps_context_when_no_client_is_returned(storage,mode,stage):
    start,_,_,_,latch=storage
    with pytest.raises(ValueError) as raised:start(mode)
    failure=raised.value.rpc_failure
    assert type(failure) is PersistenceRPCFailure and failure.kind=='init' and failure.sequence==1
    assert failure.stage==stage and failure.operation.startswith('ml-') and latch.cancelled
    retain(mode,failure=asdict(failure),client_returned=False,actual_M1_admissions=0)
