"""Actual worker writer-stage faults; exact mechanisms, no private stream access."""
from dataclasses import asdict
from importlib.resources import files
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.persistence import PersistenceClient
from xverse.maestro.run_closure import RunClosure
from .test_terminal_runtime import scheduled, run, retain, verify
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


# Independent expected public states from the original closure contracts; no
# expectation is selected from the candidate's returned writer observation.
EXPECTED={
    'fsync-once':('abort-completed','failed','failed','usable',True,True,'W-01'),
    'fsync-persistent':('flush-error','open','open','unknown',False,False,'W-01'),
    'recovery':('finalize-error','failed','open','unknown',False,False,'W-04'),
    'artifact-check':('finalize-error','failed','open','unknown',False,False,'W-05'),
    'manifest-replace':('finalize-error','failed','open','unknown',False,False,'W-06'),
    'abort-entry':('abort-error','open','open','usable',True,False,None),
}


@pytest.fixture
def run_bootstrap_binary(request,tmp_path):
    mode=request.param;assert mode in EXPECTED
    trace=tmp_path/'original-writer-faults.jsonl'
    code='''import os,json
from xverse.argus import recovery,writer as module
from xverse.argus.writer import EvidenceRun
from xverse.maestro import persistence_worker
mode=MODE
fd=os.open(TRACE,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
phase=None
writer=None
faults=0
def log(operation,result):
    os.write(fd,(json.dumps(dict(operation=operation,result=result,phase=phase,
        writer_state=writer.writer_state if writer is not None else None))+'\\n').encode())
finalize=EvidenceRun.finalize
flush=EvidenceRun.flush_buffer
abort=EvidenceRun.abort
fsync=os.fsync
replace=os.replace
recover=recovery.recover_stream
check_artifact=module.verify_index_entry
def failure(operation):
    global faults
    faults+=1;log(operation,'injected-error');raise OSError('owned exact writer failure')
def sync(*args,**kwargs):
    if (phase=='finalize' and mode in ('fsync-once','fsync-persistent','abort-entry')
        and (faults==0 or mode=='fsync-persistent')):
        failure('os.fsync')
    if phase=='flush' and mode=='fsync-persistent':failure('os.fsync')
    return fsync(*args,**kwargs)
def publication(*args,**kwargs):
    if phase=='finalize' and mode=='manifest-replace':failure('os.replace')
    return replace(*args,**kwargs)
def recover_run(*args,**kwargs):
    if phase=='finalize' and mode=='recovery':failure('recover_stream')
    return recover(*args,**kwargs)
def artifact(*args,**kwargs):
    if phase=='finalize' and mode=='artifact-check':failure('verify_index_entry')
    return check_artifact(*args,**kwargs)
def final(self,*args,**kwargs):
    global phase,writer
    writer=self;phase='finalize';log('finalize','entered')
    try:
        result=finalize(self,*args,**kwargs);log('finalize','returned');return result
    except BaseException:
        log('finalize','raised');raise
    finally:phase=None
def flushed(self,*args,**kwargs):
    global phase,writer
    # A finalize's own public flush retains finalize context; the later fresh
    # policy flush is distinct. Ordinary productive flushes are untouched.
    if phase=='finalize':return flush(self,*args,**kwargs)
    if writer is not self:return flush(self,*args,**kwargs)
    phase='flush';log('flush_buffer','entered')
    try:
        result=flush(self,*args,**kwargs);log('flush_buffer','returned');return result
    except BaseException:
        log('flush_buffer','raised');raise
    finally:phase=None
def aborted(self,*args,**kwargs):
    global phase
    phase='abort';log('abort','entered')
    try:
        if mode=='abort-entry':failure('abort-entry')
        result=abort(self,*args,**kwargs);log('abort','returned');return result
    except BaseException:
        log('abort','raised');raise
    finally:phase=None
os.fsync=sync
os.replace=publication
recovery.recover_stream=recover_run
module.verify_index_entry=artifact
EvidenceRun.finalize=final
EvidenceRun.flush_buffer=flushed
EvidenceRun.abort=aborted
status=persistence_worker.main()
os.close(fd)
os._exit(status)
'''.replace('MODE',repr(mode)).replace('TRACE',repr(str(trace)))
    original=files('xverse.maestro').joinpath('native/bootstrap.c').read_text()
    anchor='args[2]="-m";args[3]="xverse.maestro.persistence_worker"';assert original.count(anchor)==1
    source=original.replace(anchor,'args[2]="-c";args[3]='+json.dumps(code))
    root=tmp_path/'owned-writer-stage-helper';root.mkdir()
    path=root/'bootstrap.c';path.write_text(source);binary=root/'run-bootstrap'
    command=['cc','-DRUN_BOOTSTRAP','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wconversion','-Wshadow',str(path),'-lcrypto','-o',str(binary)]
    result=subprocess.run(command,capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr.decode()
    output=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if not output:return binary
    target=Path(output);target.mkdir(parents=True,exist_ok=True)
    receipt=dict(mode=mode,expected_public_states=EXPECTED[mode],command=command,returncode=0,
        original_native_source_sha256=hashlib.sha256(original.encode()).hexdigest(),fixed_fault_code=code,
        fixed_fault_code_sha256=hashlib.sha256(code.encode()).hexdigest(),
        compiled_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        original_fixture=str(tmp_path),trace_file=str(trace),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        production_fault_mode_added=False,admission_precedes_birth=True,private_stream_access=False)
    with (target/('native-writer-helper-'+mode+'.json')).open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    return binary


@pytest.mark.parametrize('run_bootstrap_binary',list(EXPECTED),indirect=True)
def test_actual_native_writer_failure_preserves_original_state_and_cleanup(request,monkeypatch,run_bootstrap_binary):
    mode=request.node.callspec.params['run_bootstrap_binary']
    expected_stage,after,durable,usability,attempted,completed,_=EXPECTED[mode]
    stack,_,driver=scheduled(request,monkeypatch);broker,_,client,work=stack
    result=run(driver)
    # Retain actual outcomes before checking the independently authored expectations.
    retain(stack,result,'native-writer-'+mode)
    assert result.execution_succeeded and result.terminal_recorded,result.diagnostic
    assert result.terminal is not None,result.diagnostic
    facts=result.terminal.public_data();w=facts['writer']
    assert facts['diagnostic'] is None and facts['report']['eligible'],facts
    assert w is not None,facts
    assert w['before_state']=='open' and w['finalize_attempted'] and not w['finalize_completed']
    assert (w['stage'],w['after_state'],w['durable_writer_state'],w['abort_usability'],
            w['abort_attempted'],w['abort_completed'])==EXPECTED[mode][:6],w
    assert not w['evidence_complete'],w
    # Original collection/report acknowledgements are not an artifact index in
    # the still-open durable manifest. Closed verification cannot infer that index.
    assert facts['report']['collectionComplete'] and result.collection.public_data()['collectionComplete']
    assert w['collection_verified'] is (durable=='failed'),w
    assert w['collection_complete'] is (durable=='failed'),w
    assert facts['storageDrain']['worker_reaped'] and facts['storageDrain']['returncode']==0
    raw=(work.parent/'argus/manifest.json').read_bytes();reader=EvidenceStore.read_run(work.parent/'argus')
    assert reader.manifest['writerState']==durable and w['manifest_sha256']==hashlib.sha256(raw).hexdigest()
    checked=verify(client,work.parent/'argus');assert not checked.complete
    assert checked.lifecycle.manifest_sha256==w['manifest_sha256']
    trace=[json.loads(s) for s in (work.parent/'original-writer-faults.jsonl').read_text().splitlines()]
    injected=[r for r in trace if r['result']=='injected-error'];assert injected
    entered=[r['operation'] for r in trace if r['result']=='entered']
    assert entered==(['finalize','flush_buffer','abort'] if attempted else
                    ['finalize','flush_buffer'] if mode=='fsync-persistent' else ['finalize'])
    if attempted:
        flush_at=next(i for i,r in enumerate(trace) if r['operation']=='flush_buffer' and r['result']=='returned')
        abort_at=next(i for i,r in enumerate(trace) if r['operation']=='abort' and r['result']=='entered')
        assert flush_at<abort_at
    sequence=client._sequence
    with monkeypatch.context() as patch:
        patch.setattr(PersistenceClient,'_rpc',lambda *a,**k:pytest.fail('writer RPC after terminal outcome'))
        closed=RunClosure(broker.session,dispatcher=driver).close(deadline(6))
    assert closed.cleanup_complete and closed.root_reaped and all(h.process_reaped for h in closed.helpers),closed
    assert all(b.empty and b.released for b in closed.boundaries)
    assert closed.terminal_reports==(result.terminal,) and not closed.writers
    assert client._sequence==sequence and not client._closure_attempted
    assert (work.parent/'argus/manifest.json').read_bytes()==raw
    assert not closed.lifecycle_complete and not closed.ready_for_execution
    output=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if not output:return
    target=Path(output)
    closure=asdict(closed);closure['terminal_reports']=[r.public_data() for r in closed.terminal_reports]
    row=dict(mode=mode,receipt=facts,closure=closure,trace=trace,manifest_sha256=hashlib.sha256(raw).hexdigest(),
        original_fixture=str(work.parent),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        no_writer_rpc_replay=True,private_stream_access=False,full_TR03_complete=False,full_TR06_complete=False,
        full_M1_complete=False,scientific_result=False)
    with (target/('native-writer-result-'+mode+'.json')).open('x') as f:json.dump(row,f,indent=2);f.write('\n')
