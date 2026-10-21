"""DV10 storage faults inside the actual original persistence worker (increment19, finding 424).

Uses the owned facility of ADR-ML3-WRITER-FAULT-0001: a copy of the original bootstrap source in
which only the role3 child receives a sealed LD_PRELOAD image (owned_storage_fault.c). The image
returns ENOSPC from write() on one exact public path once armed; this simulates a full file
system at the write call. The production bootstrap.c and persistence_worker are not changed; the
role3 wrapper only arms the image at a named public record and then calls the original main.
"""
from dataclasses import asdict
import hashlib
from importlib.resources import files
import json
import os
from pathlib import Path
import subprocess
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.persistence import PersistenceClient
from xverse.maestro.run_closure import RunClosure
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_terminal_runtime import scheduled, run, verify
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline

# case: (target relative to the fixture root, armed at load, arming rule inside role3)
CASES = {
    'C0-never-armed': ('argus/events.jsonl', 0, 'never'),
    'C1-argus-full-at-ready': ('argus/events.jsonl', 0, 'argus-ready'),
    'C2-m3-outcome-write': ('m3.jsonl', 0, 'm3-outcome'),
    'C3-m3-stop-write': ('m3.jsonl', 0, 'm3-stopped'),
    'C4-argus-open': ('argus/events.jsonl', 1, 'load'),
}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

ROLE3 = r'''import ctypes,fcntl,hashlib,json,os,time
from xverse.argus.writer import EvidenceRun
from xverse.maestro import persistence_worker
from xverse_xdl.lifecycle import FileEvidenceJournal
rule=RULE_LITERAL
fd=os.open(TRACE_LITERAL,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
def log(operation,**values):
    os.write(fd,(json.dumps(dict(operation=operation,observed_ns=time.monotonic_ns(),**values))+'\n').encode())
image=os.environ.get('LD_PRELOAD')
assert image and image.startswith('/proc/self/fd/')
image_fd=int(image.rsplit('/',1)[1])
seals=fcntl.fcntl(image_fd,fcntl.F_GET_SEALS)
assert seals&15==15
image_hash=hashlib.sha256(os.pread(image_fd,IMAGE_SIZE_LITERAL,0)).hexdigest()
assert image_hash==IMAGE_HASH_LITERAL
library=ctypes.CDLL(None)
library.owned_storage_probe.restype=ctypes.c_uint
assert library.owned_storage_probe()==0x53464631
library.owned_storage_arm.argtypes=[];library.owned_storage_arm.restype=None
log('loader',image_sha256=image_hash,seals=seals)
append_event=EvidenceRun.append_event
journal_append=FileEvidenceJournal.append
def event(self,*args,**kwargs):
    payload=(kwargs.get('extensions') or {}).get('xverse.maestro') or {}
    if rule=='argus-ready' and payload.get('action')=='ready':
        library.owned_storage_arm();log('armed',at='argus-ready',unit=payload.get('unitId'))
    try:return append_event(self,*args,**kwargs)
    except OSError as error:
        log('argus-append-raised',errno=error.errno,action=payload.get('action'));raise
def journal(self,record):
    if (rule=='m3-outcome' and record.kind=='outcome') or (rule=='m3-stopped' and record.status=='stopped'):
        library.owned_storage_arm();log('armed',at=rule,kind=record.kind,status=record.status)
    try:return journal_append(self,record)
    except OSError as error:
        log('m3-append-raised',errno=error.errno,kind=record.kind,status=record.status);raise
EvidenceRun.append_event=event
FileEvidenceJournal.append=journal
status=persistence_worker.main()
log('worker-exit',status=status)
os.close(fd)
os._exit(status)
'''


@pytest.fixture
def run_bootstrap_binary(request, tmp_path):
    case = request.param
    target_name, at_load, rule = CASES[case]
    root = tmp_path / 'owned-storage-helper'
    root.mkdir()
    target = (tmp_path / target_name).resolve() if (tmp_path / target_name).exists() else tmp_path.resolve() / target_name
    native_trace, python_trace = tmp_path / 'owned-storage-syscalls.jsonl', tmp_path / 'owned-storage-public.jsonl'
    source = Path(__file__).with_name('owned_storage_fault.c')
    header = root / 'owned-storage-fault-config.h'
    header.write_text('#define OWNED_ARM_AT_LOAD ' + str(at_load) + '\n'
                      + '#define OWNED_TARGET ' + json.dumps(str(target)) + '\n'
                      + '#define OWNED_TRACE ' + json.dumps(str(native_trace)) + '\n')
    library = root / 'owned-storage-fault.so'
    flags = ['-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-Wconversion', '-Wshadow']
    completed = subprocess.run(['cc', *flags, '-shared', '-fPIC', '-I', str(root), str(source), '-o', str(library)],
                               capture_output=True, timeout=30)
    assert completed.returncode == 0, completed.stderr.decode()
    image = library.read_bytes()
    assert 0 < len(image) <= 1 << 20
    code = (ROLE3.replace('RULE_LITERAL', repr(rule)).replace('TRACE_LITERAL', repr(str(python_trace)))
            .replace('IMAGE_SIZE_LITERAL', str(len(image))).replace('IMAGE_HASH_LITERAL', repr(sha(library))))
    original = files('xverse.maestro').joinpath('native/bootstrap.c').read_text()
    modified = original
    for anchor, replacement in (
        ('args[2]="-m";args[3]="xverse.maestro.persistence_worker"', 'args[2]="-c";args[3]=' + json.dumps(code)),
        ('static int birth(', 'static const unsigned char owned_storage_image[]={'
            + ','.join(str(b) for b in image) + '};\nstatic int birth('),
        ('char *environment[]={NULL};syscall(SYS_execveat,', '''char owned_preload[64];
        char *environment[]={NULL,NULL};
        if(role==3){
            int owned_fd=(int)syscall(SYS_memfd_create,"owned-storage-image",MFD_CLOEXEC|MFD_ALLOW_SEALING);
            if(owned_fd<0)_exit(126);
            size_t owned_used=0;
            while(owned_used<sizeof(owned_storage_image)){
                ssize_t amount=write(owned_fd,owned_storage_image+owned_used,sizeof(owned_storage_image)-owned_used);
                if(amount<=0)_exit(126);
                owned_used+=(size_t)amount;
            }
            if(fcntl(owned_fd,F_ADD_SEALS,SEALS)<0||fcntl(owned_fd,F_SETFD,0)<0)_exit(126);
            int owned_length=snprintf(owned_preload,sizeof(owned_preload),"LD_PRELOAD=/proc/self/fd/%d",owned_fd);
            if(owned_length<=0||(size_t)owned_length>=sizeof(owned_preload))_exit(126);
            environment[0]=owned_preload;
        }
        syscall(SYS_execveat,'''),
    ):
        assert modified.count(anchor) == 1
        modified = modified.replace(anchor, replacement)
    compiled_source = root / 'bootstrap.c'
    compiled_source.write_text(modified)
    binary = root / 'run-bootstrap'
    completed = subprocess.run(['cc', '-DRUN_BOOTSTRAP', *flags, str(compiled_source), '-lcrypto', '-o', str(binary)],
                               capture_output=True, timeout=30)
    assert completed.returncode == 0, completed.stderr.decode()
    output = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        out = Path(output)
        out.mkdir(parents=True, exist_ok=True)
        with (out / ('storage-fault-helper-' + case + '.json')).open('x') as stream:
            json.dump(dict(case=case, target=str(target), rule=rule, at_load=at_load, library_sha256=sha(library),
                           library_source_sha256=sha(source), bootstrap_source_sha256=sha(compiled_source),
                           original_source_sha256=hashlib.sha256(original.encode()).hexdigest(), role3_code=code,
                           production_bootstrap_changed=False, fixture_source_sha256=sha(Path(__file__))), stream, indent=2)
            stream.write('\n')
    return binary


def traces(work):
    read = lambda name: [json.loads(line) for line in (work.parent / name).read_text().splitlines()] \
        if (work.parent / name).exists() else []
    return read('owned-storage-public.jsonl'), read('owned-storage-syscalls.jsonl')


def markers(work):
    return sorted(p.name for p in work.glob('*.marker'))


def m3(work):
    return list(FileEvidenceJournal(work.parent / 'm3.jsonl').public_records())


def closed_cleanly(broker, driver, client, monkeypatch):
    # Without a terminal outcome RunClosure makes its single designed close_incomplete attempt
    # (one closure request, never finalize); any other request would be a replay (finding 425).
    requests = []
    original = PersistenceClient._rpc

    def observed(self, kind, *args, **kwargs):
        requests.append(kind)
        return original(self, kind, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(PersistenceClient, '_rpc', observed)
        closure = RunClosure(broker.session, dispatcher=driver).close(deadline(6))
    print('CLOSURE-FULL', json.dumps({k: v for k, v in asdict(closure).items() if k not in ('writers', 'terminal_reports')}, default=str))
    print('CLOSURE', dict(requests=requests, writers=[asdict(w) for w in closure.writers],
                          diagnostics=getattr(closure, 'diagnostics', None)))
    assert requests in ([], ['closure']), requests
    assert closure.root_reaped and closure.inventory_complete and closure.unacknowledged_births == 0
    assert all(h.process_reaped for h in closure.helpers)
    assert all(b.empty and b.released for b in closure.boundaries)
    assert closure.authority_fenced in (True, None)
    # After a storage fault the native workload wait may be lost; physical cleanup is still shown
    # by the empty released boundaries (finding 426, as test_composed_persistence_termination).
    assert closure.cleanup_complete or 'ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN' in closure.diagnostics, asdict(closure)
    return closure


@pytest.mark.parametrize('run_bootstrap_binary', [c for c in CASES if c != 'C4-argus-open'], indirect=True)
def test_storage_full_inside_the_original_worker_fails_closed(request, monkeypatch, run_bootstrap_binary):
    case = request.node.callspec.params['run_bootstrap_binary']
    stack, _, driver = scheduled(request, monkeypatch)
    broker, _, client, work = stack
    result = run(driver)
    public, native = traces(work)
    faults = [r for r in native if r['action'] == 'injected-before-syscall']
    print('CASE', case, dict(succeeded=result.execution_succeeded, terminal=result.terminal_recorded,
                             diagnostic=result.diagnostic, failed=client._failed, faults=len(faults),
                             markers=markers(work), m3=[(r['kind'], r['status']) for r in m3(work)],
                             armed=[r for r in public if r['operation'] == 'armed'],
                             rpc_failure=(asdict(client.rpc_failure) if client.rpc_failure is not None else None),
                             raised=[r for r in public if r['operation'].endswith('raised')]))
    if case == 'C0-never-armed':
        assert result.execution_succeeded and result.terminal_recorded, result.diagnostic
        assert not faults and verify(client, work.parent / 'argus').complete
        closed_cleanly(broker, driver, client, monkeypatch)
        return
    assert faults and all(f['errno'] == 28 and not f['native_called'] for f in faults)
    assert not result.execution_succeeded
    records = m3(work)
    if case in ('C1-argus-full-at-ready', 'C2-m3-outcome-write'):
        assert markers(work) in ([], ['source-binding.marker']), markers(work)
    if case == 'C2-m3-outcome-write':
        assert not any(r['kind'] == 'outcome' for r in records), records
    if case == 'C3-m3-stop-write':
        assert not any(r['status'] == 'stopped' for r in records), records
    manifest = EvidenceStore.read_run(work.parent / 'argus').manifest
    assert manifest['writerState'] in ('open', 'failed'), manifest['writerState']
    closure = closed_cleanly(broker, driver, client, monkeypatch)
    assert not closure.normal_unit_records_complete
    assert not verify(client, work.parent / 'argus').complete


@pytest.mark.parametrize('run_bootstrap_binary', ['C4-argus-open'], indirect=True)
def test_argus_open_failure_rejects_before_any_release(request, monkeypatch, run_bootstrap_binary, tmp_path):
    began = time.monotonic()
    with pytest.raises(Exception) as raised:
        scheduled(request, monkeypatch)
    elapsed = time.monotonic() - began
    public = [json.loads(line) for line in (tmp_path / 'owned-storage-public.jsonl').read_text().splitlines()] \
        if (tmp_path / 'owned-storage-public.jsonl').exists() else []
    native = [json.loads(line) for line in (tmp_path / 'owned-storage-syscalls.jsonl').read_text().splitlines()] \
        if (tmp_path / 'owned-storage-syscalls.jsonl').exists() else []
    print('CASE C4', dict(error=type(raised.value).__name__, message=str(raised.value)[:200], elapsed=round(elapsed, 3),
                          faults=sum(r['action'] == 'injected-before-syscall' for r in native),
                          markers=sorted(p.name for p in tmp_path.rglob('*.marker'))))
    assert any(r['action'] == 'injected-before-syscall' and r['errno'] == 28 for r in native)
    assert not list(tmp_path.rglob('*.marker'))
