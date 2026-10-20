"""Actual original worker internal flush/close boundary, with no private stream access."""
from dataclasses import asdict
import hashlib
from importlib.resources import files
import json
import os
from pathlib import Path
import subprocess

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.persistence import PersistenceClient
from xverse.maestro.run_closure import RunClosure
from xverse.maestro.runtime_verification import runtime_admission_digest
from .owned_writer_stream_worker import ROLE3, ROLE5
from .test_terminal_runtime import scheduled, run, retain, verify
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


EXPECTED = {
    'loader-only': ('finalize-completed', 'closed', 'closed', 'unknown', False, False),
    'seeded-flush-once': ('abort-completed', 'failed', 'failed', 'usable', True, True),
    'seeded-flush-persistent': ('flush-error', 'open', 'open', 'unknown', False, False),
    'close-after': ('flush-error', 'open', 'open', 'unknown', False, False),
}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.fixture
def run_bootstrap_binary(request, tmp_path):
    mode = request.param
    assert mode in EXPECTED
    root = tmp_path / 'owned-stream-helper'
    root.mkdir()
    target = tmp_path / 'argus/events.jsonl'
    native_trace, python_trace, role5_trace = [tmp_path / name for name in (
        'owned-stream-syscalls.jsonl', 'owned-stream-public.jsonl', 'owned-stream-role5.jsonl')]
    source = Path(__file__).with_name('owned_writer_stream_fault.c')
    header = root / 'owned-writer-fault-config.h'
    header.write_text('#define OWNED_MODE ' + str(list(EXPECTED).index(mode)) + '\n'
        + '#define OWNED_TARGET ' + json.dumps(str(target)) + '\n'
        + '#define OWNED_TRACE ' + json.dumps(str(native_trace)) + '\n')
    library = root / 'owned-stream-fault.so'
    flags = ['-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-Wconversion', '-Wshadow']
    library_command = ['cc', *flags, '-shared', '-fPIC', '-I', str(root), str(source), '-o', str(library)]
    completed = subprocess.run(library_command, capture_output=True, timeout=30)
    assert completed.returncode == 0, completed.stderr.decode()
    image = library.read_bytes()
    assert 0 < len(image) <= 1 << 20
    code = (ROLE3.replace('MODE_LITERAL', repr(mode)).replace('TRACE_LITERAL', repr(str(python_trace)))
        .replace('IMAGE_SIZE_LITERAL', str(len(image))).replace('IMAGE_HASH_LITERAL', repr(sha(library))))
    role5 = ROLE5.replace('TRACE_LITERAL', repr(str(role5_trace)))
    original = files('xverse.maestro').joinpath('native/bootstrap.c').read_text()
    modified = original
    for anchor, replacement in (
        ('args[2]="-m";args[3]="xverse.maestro.persistence_worker"', 'args[2]="-c";args[3]=' + json.dumps(code)),
        ('args[2]="-m";args[3]="xverse.maestro.controller_worker"', 'args[2]="-c";args[3]=' + json.dumps(role5)),
        ('static int birth(', 'static const unsigned char owned_stream_image[]={'
            + ','.join(str(b) for b in image) + '};\nstatic int birth('),
        ('char *environment[]={NULL};syscall(SYS_execveat,', '''char owned_preload[64];
        char *environment[]={NULL,NULL};
        if(role==3){
            int owned_fd=(int)syscall(SYS_memfd_create,"owned-stream-image",MFD_CLOEXEC|MFD_ALLOW_SEALING);
            if(owned_fd<0)_exit(126);
            size_t owned_used=0;
            while(owned_used<sizeof(owned_stream_image)){
                ssize_t amount=write(owned_fd,owned_stream_image+owned_used,sizeof(owned_stream_image)-owned_used);
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
    command = ['cc', '-DRUN_BOOTSTRAP', *flags, str(compiled_source), '-lcrypto', '-o', str(binary)]
    completed = subprocess.run(command, capture_output=True, timeout=30)
    assert completed.returncode == 0, completed.stderr.decode()
    output = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        out = Path(output)
        out.mkdir(parents=True, exist_ok=True)
        for suffix, path in (('library.so', library), ('configuration.h', header), ('bootstrap.c', compiled_source), ('bootstrap.bin', binary)):
            with (out / ('stream-helper-' + mode + '-' + suffix)).open('xb') as stream:
                stream.write(path.read_bytes())
        row = dict(mode=mode, expected=EXPECTED[mode], library_command=library_command, bootstrap_command=command,
            original_source_sha256=hashlib.sha256(original.encode()).hexdigest(),
            fixture_source_sha256=sha(Path(__file__)), library_source_sha256=sha(source),
            library_sha256=sha(library), configuration_sha256=sha(header), bootstrap_source_sha256=sha(compiled_source),
            bootstrap_sha256=sha(binary), role3_code=code, role5_code=role5,
            original_fixture=str(tmp_path), target=str(target), library_size=len(image),
            private_stream_access=False, admission_precedes_birth=True, production_bootstrap_changed=False)
        with (out / ('stream-helper-' + mode + '.json')).open('x') as stream:
            json.dump(row, stream, indent=2)
            stream.write('\n')
    return binary


@pytest.mark.parametrize('run_bootstrap_binary', list(EXPECTED), indirect=True)
def test_native_stream_fault_preserves_public_writer_and_original_cleanup(request, monkeypatch, run_bootstrap_binary):
    mode = request.node.callspec.params['run_bootstrap_binary']
    stack, _, driver = scheduled(request, monkeypatch)
    broker, _, client, work = stack
    result = closure = None
    output = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        with (Path(output) / ('stream-inputs-' + mode + '.json')).open('x') as stream:
            json.dump(dict(original_admission=json.loads(client.coverage.public_bytes), admission_digest=client.coverage_digest,
                original_collection=json.loads(client.collection.canonical_bytes), original_schedule=json.loads(client.schedule.canonical_bytes),
                generation_ns=client.generation_ns, runtime_digest=runtime_admission_digest(client.coverage, client.collection, client.generation_ns),
                native_bootstrap_digest=broker.session.config.admission.supervisor_artifact_digest,
                bootstrap_configuration_sha256=hashlib.sha256(broker.session.config.private_bytes).hexdigest(),
                original_fixture=str(work.parent), fixture_source_sha256=sha(Path(__file__))), stream, indent=2)
            stream.write('\n')
    try:
        result = run(driver)
        retain(stack, result, 'native-stream-' + mode)
        assert result.execution_succeeded and result.terminal_recorded, result.diagnostic
        facts = result.terminal.public_data()
        writer = facts['writer']
        assert facts['diagnostic'] is None and facts['report']['eligible'], facts
        assert writer['before_state'] == 'open' and writer['finalize_attempted']
        assert (writer['stage'], writer['after_state'], writer['durable_writer_state'], writer['abort_usability'],
                writer['abort_attempted'], writer['abort_completed']) == EXPECTED[mode], writer
        assert writer['finalize_completed'] is (mode == 'loader-only')
        assert writer['evidence_complete'] is (mode == 'loader-only')
        public = [json.loads(line) for line in (work.parent / 'owned-stream-public.jsonl').read_text().splitlines()]
        native = [json.loads(line) for line in (work.parent / 'owned-stream-syscalls.jsonl').read_text().splitlines()]
        role5 = json.loads((work.parent / 'owned-stream-role5.jsonl').read_text())
        assert role5['preload_absent'] and role5['symbol_absent']
        loaded = [r for r in public if r['operation'] == 'loader']
        assert len(loaded) == 1 and loaded[0]['seals'] & 15 == 15
        assert sum(r['operation'] == 'load' for r in native) == 1
        faults = [r for r in native if r['action'].startswith('injected-')]
        assert bool(faults) is (mode != 'loader-only')
        if mode.startswith('seeded-flush-'):
            returned = next(r['observed_ns'] for r in public if r['operation'] == 'finalize-public-flush' and r['result'] == 'wrapper-returned')
            armed = next(r['observed_ns'] for r in native if r['operation'] == 'arm')
            seeded = next(r['observed_ns'] for r in public if r['operation'] == 'fixture-annotation' and r['result'] == 'seed-write-failed')
            assert armed < faults[0]['observed_ns'] < seeded < returned < faults[1]['observed_ns']
            assert all(r['operation'] == 'write' and not r['native_called'] and r['errno'] == 5 and r['returned_result'] == -1 for r in faults)
            assert (len(faults) == 2) if mode == 'seeded-flush-once' else (len(faults) >= 3)
        elif mode == 'close-after':
            assert len(faults) == 1
            assert faults[0]['operation'] == 'close' and faults[0]['native_called']
            assert faults[0]['native_result'] == 0 and faults[0]['returned_result'] == -1 and faults[0]['errno'] == 5
        if writer['abort_attempted']:
            fresh = next(r['observed_ns'] for r in public if r['operation'] == 'flush_buffer' and r['result'] == 'returned')
            abort = next(r['observed_ns'] for r in public if r['operation'] == 'abort' and r['result'] == 'entered')
            assert fresh < abort and sum(r['operation'] == 'abort' and r['result'] == 'entered' for r in public) == 1
        else:
            assert not any(r['operation'] == 'abort' for r in public)
        raw = (work.parent / 'argus/manifest.json').read_bytes()
        assert EvidenceStore.read_run(work.parent / 'argus').manifest['writerState'] == EXPECTED[mode][2]
        assert writer['manifest_sha256'] == hashlib.sha256(raw).hexdigest()
        assert verify(client, work.parent / 'argus').complete is (mode == 'loader-only')
        sequence = client._sequence
        with monkeypatch.context() as patch:
            patch.setattr(PersistenceClient, '_rpc', lambda *a, **k: pytest.fail('writer replay after original close'))
            closure = RunClosure(broker.session, dispatcher=driver).close(deadline(6))
        assert closure.cleanup_complete and closure.root_reaped
        assert all(h.process_reaped for h in closure.helpers) and all(b.empty and b.released for b in closure.boundaries)
        assert closure.terminal_reports == (result.terminal,) and not closure.writers
        assert client._sequence == sequence and (work.parent / 'argus/manifest.json').read_bytes() == raw
        assert not closure.lifecycle_complete and not closure.ready_for_execution
    finally:
        if output:
            row = dict(mode=mode, original_fixture=str(work.parent), fixture_source_sha256=sha(Path(__file__)),
                receipt=result.terminal.public_data() if result and result.terminal else None,
                execution_succeeded=result.execution_succeeded if result else None, diagnostic=result.diagnostic if result else None,
                closure={**asdict(closure), 'terminal_reports':[r.public_data() for r in closure.terminal_reports]} if closure else None,
                private_stream_access=False, full_TR03_complete=False, full_TR06_complete=False,
                full_M1_complete=False, scientific_result=False)
            with (Path(output) / ('stream-result-' + mode + '.json')).open('x') as stream:
                json.dump(row, stream, indent=2)
                stream.write('\n')
