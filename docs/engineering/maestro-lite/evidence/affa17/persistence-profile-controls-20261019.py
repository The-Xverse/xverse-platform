"""Diagnostic overlay: original tests/oracles, actual hash-admitted worker timings."""
from importlib.resources import files
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest
from . import test_lazy_dispatcher, test_shared_dispatcher
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries


@pytest.fixture
def run_bootstrap_binary(request, tmp_path):
    profile=tmp_path/'original-worker-costs.jsonl'
    code='''import os,json,time,functools
from xverse.argus import EvidenceStore
from xverse.argus.writer import EvidenceRun
from xverse.argus.reader import EvidenceReader
from xverse_xdl.lifecycle import FileEvidenceJournal
from xverse.maestro.admission import PermitSession,_PreparationProof
from xverse.maestro.lifecycle_evidence import OutcomeJournal
from xverse.maestro import persistence_worker as worker
fd=os.open(PROFILE,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
state={'rpc':0,'kind':None,'unit':None,'deadline':None}
depth=0
count=0
def observed(original,label):
    @functools.wraps(original)
    def call(*args,**kwargs):
        global depth,count
        began=time.monotonic();current=depth;depth+=1;error=None
        try:return original(*args,**kwargs)
        except BaseException as exc:
            error=type(exc).__name__;raise
        finally:
            ended=time.monotonic();depth-=1
            if count<4096:
                row=dict(state,label=label,began=began,ended=ended,depth=current,error=error)
                os.write(fd,(json.dumps(row,separators=(',',':'))+'\\n').encode());count+=1
    return call
receive=worker._receive
def request(*args,**kwargs):
    value=receive(*args,**kwargs)
    frame=value[0] if isinstance(value,tuple) else value
    state.update(rpc=frame['sequence'],kind=frame['kind'],unit=frame['body'].get('unit'),
                 deadline=frame['deadline']/1e9)
    return value
worker._receive=request
worker._send=observed(worker._send,'reply.send')
EvidenceStore.read_run=classmethod(observed(EvidenceStore.read_run.__func__,'argus.read_run'))
for cls,names,prefix in (
    (EvidenceReader,('records',),'argus.reader'),
    (EvidenceRun,('append_event','flush_buffer'),'argus.writer'),
    (FileEvidenceJournal,('append','public_records','_reload'),'m3'),
    (PermitSession,('revalidate_start_intent',),'permit'),
    (_PreparationProof,('check',),'preparation'),
    (OutcomeJournal,('_history','_mirrors','record'),'outcomes')):
    for name in names:setattr(cls,name,observed(getattr(cls,name),prefix+'.'+name))
original=FileEvidenceJournal.records
FileEvidenceJournal.records=property(observed(original.fget,'m3.records'),doc=original.__doc__)
status=worker.main()
os.close(fd)
os._exit(status)
'''.replace('PROFILE',repr(str(profile)))
    original=files('xverse.maestro').joinpath('native/bootstrap.c').read_text()
    anchor='args[2]="-m";args[3]="xverse.maestro.persistence_worker"'
    assert original.count(anchor)==1
    source=original.replace(anchor,'args[2]="-c";args[3]='+json.dumps(code))
    root=tmp_path/'owned-cost-profile-helper';root.mkdir()
    path=root/'bootstrap.c';path.write_text(source);binary=root/'run-bootstrap'
    command=['cc','-DRUN_BOOTSTRAP','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wconversion','-Wshadow',str(path),'-lcrypto','-o',str(binary)]
    result=subprocess.run(command,capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr.decode()
    receipt=dict(command=command,returncode=result.returncode,profile_file=str(profile),
        original_native_source_sha256=hashlib.sha256(original.encode()).hexdigest(),
        fixed_diagnostic_code=code,fixed_diagnostic_code_sha256=hashlib.sha256(code.encode()).hexdigest(),
        compiled_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        original_fixture=str(tmp_path),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        production_diagnostic_mode_added=False,admission_precedes_birth=True,
        unchanged_original_assertions_and_bounds=True,observer_io_overhead_included=True,
        no_private_request_or_response_material_recorded=True)
    output=os.environ['MAESTRO_BOUNDARY_RECEIPTS'];out=Path(output);out.mkdir(parents=True,exist_ok=True)
    target=out/('worker-cost-helper-'+request.node.name.replace('[','-').replace(']','')+'.json')
    with target.open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    return binary


@pytest.mark.parametrize('case',['lazy-nominal','paused-shared'])
def test_original_persistence_costs_with_unchanged_oracles(request,monkeypatch,case):
    if case=='lazy-nominal':
        test_lazy_dispatcher.test_actual_lazy_nominal_stages_only_at_eligible_start_then_collects_before_terminal(request,monkeypatch)
    else:
        test_shared_dispatcher.test_paused_shared_ticks_renew_both_original_leases_and_observe_health(request,monkeypatch)
