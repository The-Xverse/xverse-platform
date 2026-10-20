"""Actual original worker failure-state controls using hash-admitted owned helper."""
from importlib.resources import files
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.persistence import PersistenceClient
from .test_terminal_runtime import scheduled, run, retain
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


@pytest.fixture
def run_bootstrap_binary(request,tmp_path):
    mode=request.param
    assert mode in ('failed','closed')
    # This code is embedded in the admitted test binary, not selected by a runtime
    # flag/environment/config or written into the installed package.
    code='''import os
from xverse.argus.writer import EvidenceRun
from xverse.maestro import persistence_worker
original=EvidenceRun.record_artifact
hit=False
def report_index(self,path,*args,**kwargs):
    global hit
    if path!='lifecycle-coverage.json':return original(self,path,*args,**kwargs)
    if hit:raise AssertionError('owned report fault replay')
    hit=True
    if MODE=='failed':
        self.abort(reason='Owned report-index fault: actual writer failed before close')
    else:
        original(self,path,*args,**kwargs)
        self.finalize()
    raise OSError('owned lost report index acknowledgement after public closure')
EvidenceRun.record_artifact=report_index
os._exit(persistence_worker.main())
'''.replace('MODE',repr(mode))
    original=files('xverse.maestro').joinpath('native/bootstrap.c').read_text()
    anchor='args[2]="-m";args[3]="xverse.maestro.persistence_worker"'
    assert original.count(anchor)==1
    source=original.replace(anchor,'args[2]="-c";args[3]='+json.dumps(code))
    root=tmp_path/'owned-report-fault-helper';root.mkdir()
    path=root/'bootstrap.c';path.write_text(source);binary=root/'run-bootstrap'
    command=['cc','-DRUN_BOOTSTRAP','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wconversion','-Wshadow',str(path),'-lcrypto','-o',str(binary)]
    result=subprocess.run(command,capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr.decode()
    output=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        out=Path(output);out.mkdir(parents=True,exist_ok=True)
        (out/('terminal-fault-helper-'+request.node.name.replace('[','-').replace(']','')+'.json')).write_text(json.dumps(dict(
            mode=mode,command=command,returncode=result.returncode,
            original_native_source_sha256=hashlib.sha256(original.encode()).hexdigest(),
            fixed_fault_code=code,fixed_fault_code_sha256=hashlib.sha256(code.encode()).hexdigest(),
            compiled_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
            original_fixture=str(tmp_path),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            production_fault_mode_added=False,admission_precedes_birth=True),indent=2)+'\n')
    return binary


@pytest.mark.parametrize('run_bootstrap_binary',['failed','closed'],indirect=True)
@pytest.mark.parametrize('changed_receipt',[False,True])
def test_actual_nonopen_writer_close_requires_original_report_receipt(request,monkeypatch,run_bootstrap_binary,changed_receipt):
    stack,_,driver=scheduled(request,monkeypatch);client=stack[2]
    original=PersistenceClient._rpc
    def observed(self,kind,body,end,**kw):
        result=original(self,kind,body,end,**kw)
        if self is client and changed_receipt and kind=='terminal-report' and body['action']=='publish':
            operation,until,reply=result;reply=dict(reply,annotationCount=reply['annotationCount']+1)
            return operation,until,reply
        return result
    monkeypatch.setattr(PersistenceClient,'_rpc',observed)
    result=run(driver)
    assert result.execution_succeeded and result.terminal_recorded,result.diagnostic
    assert result.terminal is not None,result.diagnostic
    facts=result.terminal.public_data();report=facts['report']
    assert report is not None and report['entry'] is None and not report['eligible'],facts
    assert report['stage']=='report-write' and report['blockers']==['publication']
    reader=EvidenceStore.read_run(stack[3].parent/'argus');actual=reader.manifest['writerState']
    assert actual in ('closed','failed')
    system=[e for e in reader.records() if e['eventKind'] in ('run-failed','run-closed')]
    # Accepted abort appends run-failed; finalize publishes its manifest without
    # appending run-closed. Closed/failed public APIs cannot reopen the writer.
    assert len(system)==(1 if actual=='failed' else 0)
    if changed_receipt:
        assert facts['writer'] is None and facts['diagnostic'] is not None
        assert facts['lastAcknowledgedWriterState']==client.last_writer_state=='open'
        assert client._failed
    else:
        assert facts['diagnostic'] is None,facts
        writer=facts['writer'];assert writer is not None,facts
        assert writer['before_state']==writer['after_state']==writer['durable_writer_state']==actual
        assert writer['stage']=='not-open'
        assert not any(writer[k] for k in ('finalize_attempted','finalize_completed','abort_attempted','abort_completed'))
        assert writer['evidence_complete'] is (actual=='closed')
        assert facts['lastAcknowledgedWriterState']==client.last_writer_state==actual
        assert client._aborted and not client._failed
    assert result.diagnostic=='ML-SCHEDULE-EVIDENCE-INCOMPLETE'
    assert facts['storageDrain']['worker_reaped']
    assert not result.lifecycle_complete and not result.terminal.lifecycle_complete
    # Common retention reads only owned public bytes and never supplies authority.
    retain(stack,result,'nonopen-'+actual+('-changed-receipt' if changed_receipt else ''))
