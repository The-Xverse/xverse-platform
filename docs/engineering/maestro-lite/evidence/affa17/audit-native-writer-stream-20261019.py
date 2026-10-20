"""Audit exact owned loader/syscall observations, including failed mechanisms."""
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import sysconfig
import zipfile
from xverse.argus import EvidenceStore
from xverse.maestro.coverage import CoverageAdmission, canonical
from xverse.maestro.collection_plan import decode_collection
from xverse.maestro.runtime_verification import runtime_admission_digest, verify_runtime_closed
from xverse_xdl.lifecycle import FileEvidenceJournal

out = Path(sys.argv[1]).resolve(strict=True)
handle, exit_code = int(sys.argv[2]), int(sys.argv[3])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
frozen, running = read(out/'frozen-inputs.json'), read(out/'running.json')
source = Path(running['frozen_source_root'])
assert all(sha(source/n) == h for n,h in frozen.items())
prior = read(out.parent/'active-control-deadlines-20261019c/frozen-inputs.json')
assert all(prior[n] == h for n,h in frozen.items() if n.startswith('src/'))
installed = Path(sysconfig.get_path('purelib'))
wheel_path = out/'dist/xverse_xdl-0.4.0-py3-none-any.whl'
packaged = []
with zipfile.ZipFile(wheel_path) as wheel:
    for name,value in frozen.items():
        if name.startswith('src/') and name.endswith(('.py','.c')):
            entry = name.removeprefix('src/')
            assert hashlib.sha256(wheel.read(entry)).hexdigest() == value == sha(installed/entry)
            packaged.append(entry)
assert len(packaged) == 76
test_path = 'tests/thesis_lite/maestro/test_native_writer_stream_faults.py'
tree = ast.parse((source/test_path).read_text())
expected = ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)
    and any(isinstance(t,ast.Name) and t.id=='EXPECTED' for t in n.targets)))
patch_loop = next(n for n in ast.walk(tree) if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple)
    and [t.id for t in n.target.elts] == ['anchor','replacement'])
env_anchor = ast.literal_eval(patch_loop.iter.elts[3].elts[0])
env_patch = ast.literal_eval(patch_loop.iter.elts[3].elts[1])
worker_tree = ast.parse((source/'tests/thesis_lite/maestro/owned_writer_stream_worker.py').read_text())
workers = {n.targets[0].id:ast.literal_eval(n.value) for n in worker_tree.body if isinstance(n,ast.Assign)}
original = (source/'src/xverse/maestro/native/bootstrap.c').read_text()
phases, cases, roots, waits, snapshots, retained = [], [], [], [], [], []
seen_roots = set()
for group in ('loader','faults'):
    modes = ['loader-only'] if group=='loader' else [m for m in expected if m!='loader-only']
    for phase in ('source','wheel'):
        label = group+'-'+phase
        receipt = read(out/(label+'-receipt.json'))
        log = out/(label+'.log')
        assert sha(log) == receipt['log_sha256'] and receipt['public_capture_returncode'] == 0
        last = log.read_text().splitlines()[-1]
        counts = {k:int(m.group(1)) if (m:=re.search(r'(\d+) '+k,last)) else 0 for k in ('passed','failed','errors','deselected')}
        assert counts['passed']+counts['failed']+counts['errors'] == len(modes)
        assert counts['deselected'] == 4-len(modes)
        assert (receipt['returncode']==0) == (counts['failed']==counts['errors']==0)
        phases.append(dict(group=group,phase=phase,returncode=receipt['returncode'],**counts))
        harness = out/(label+'-harness')
        for path in harness.glob('maestro-component-*.json'):
            row = read(path)
            identity = row['parent_path'],row['root_name']
            assert identity not in seen_roots
            seen_roots.add(identity)
            assert row['root_removed'] and row['workers_reaped']
            assert not (Path(row['parent_path'])/row['root_name']).exists()
            roots.append(dict(path=str(path.relative_to(out)),sha256=sha(path)))
        for path in harness.glob('run-broker-waits-*.json'):
            row=read(path)
            assert all(row[k] for k in ('bootstrap_reaped','registered_helpers_reaped','storage_reaped','original_C1_released'))
            waits.append(dict(path=str(path.relative_to(out)),sha256=sha(path)))
        for item in read(out/(label+'-public-evidence-index.json')):
            assert sha(out/item['snapshot'])==item['sha256'] and not item['reader_gaps']
            projection=read(out/item['snapshot']);fixture=Path(projection['original_fixture'])
            assert projection['m3']==list(FileEvidenceJournal(fixture/'m3.jsonl').public_records())
            assert projection['argus']==list(EvidenceStore.read_run(fixture/'argus').records())
            snapshots.append(dict(group=group,phase=phase,**item))
        for mode in modes:
            helper_path=harness/('stream-helper-'+mode+'.json')
            helper,row=read(helper_path),read(harness/('stream-result-'+mode+'.json'))
            fixture=Path(helper['original_fixture'])
            assert row['original_fixture']==str(fixture)
            assert helper['fixture_source_sha256']==row['fixture_source_sha256']==frozen[test_path]
            assert helper['library_source_sha256']==frozen['tests/thesis_lite/maestro/owned_writer_stream_fault.c']
            assert helper['original_source_sha256']==frozen['src/xverse/maestro/native/bootstrap.c']
            image=(harness/('stream-helper-'+mode+'-library.so')).read_bytes()
            assert hashlib.sha256(image).hexdigest()==helper['library_sha256'] and len(image)==helper['library_size']
            binary=harness/('stream-helper-'+mode+'-bootstrap.bin')
            compiled=harness/('stream-helper-'+mode+'-bootstrap.c')
            assert sha(binary)==helper['bootstrap_sha256'] and sha(compiled)==helper['bootstrap_source_sha256']
            assert sha(harness/('stream-helper-'+mode+'-configuration.h'))==helper['configuration_sha256']
            code=(workers['ROLE3'].replace('MODE_LITERAL',repr(mode)).replace('TRACE_LITERAL',repr(str(fixture/'owned-stream-public.jsonl')))
                .replace('IMAGE_SIZE_LITERAL',str(len(image))).replace('IMAGE_HASH_LITERAL',repr(helper['library_sha256'])))
            role5=workers['ROLE5'].replace('TRACE_LITERAL',repr(str(fixture/'owned-stream-role5.jsonl')))
            assert helper['role3_code']==code and helper['role5_code']==role5
            assert not any(isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name)
                and n.value.id in ('self','writer') and n.attr.startswith('_') for n in ast.walk(ast.parse(code)))
            derivative=compiled.read_text()
            array=re.search(r'static const unsigned char owned_stream_image\[\]=\{([0-9,]+)\};\n',derivative)
            assert array and bytes(map(int,array[1].split(',')))==image
            restored=derivative.replace(array[0],'').replace(env_patch,env_anchor)
            restored=restored.replace('args[2]="-c";args[3]='+json.dumps(code),'args[2]="-m";args[3]="xverse.maestro.persistence_worker"')
            restored=restored.replace('args[2]="-c";args[3]='+json.dumps(role5),'args[2]="-m";args[3]="xverse.maestro.controller_worker"')
            assert restored==original, 'unreviewed bootstrap changes'
            public_path,native_path=fixture/'owned-stream-public.jsonl',fixture/'owned-stream-syscalls.jsonl'
            public=[json.loads(x) for x in public_path.read_text().splitlines()]
            native=[json.loads(x) for x in native_path.read_text().splitlines()]
            assert len(native)<=512 and native_path.stat().st_size<=512*512
            assert all(a['observed_ns']<=b['observed_ns'] for a,b in zip(native,native[1:]))
            assert public[0]['image_sha256']==helper['library_sha256'] and public[0]['seals']&15==15
            role=read(fixture/'owned-stream-role5.jsonl')
            assert role['preload_absent'] and role['symbol_absent']
            faults=[r for r in native if r['action'].startswith('injected-')]
            demonstrated=False
            if mode=='close-after':
                assert len(faults)==1 and faults[0]['operation']=='close'
                assert faults[0]['native_called']==1 and faults[0]['native_result']==0 and faults[0]['returned_result']==-1
                demonstrated=True
            elif mode.startswith('seeded-flush-'):
                returned=next(r['observed_ns'] for r in public if r['operation']=='finalize-public-flush' and r['result']=='wrapper-returned')
                seed=next(r['observed_ns'] for r in public if r['operation']=='fixture-annotation' and r['result']=='seed-write-failed')
                assert faults[0]['observed_ns']<seed<returned<faults[1]['observed_ns']
                assert all(r['operation']=='write' and r['native_called']==0 and r['errno']==5 for r in faults)
                assert len(faults)==2 if mode=='seeded-flush-once' else len(faults)>=3
                demonstrated=True
            elif mode.startswith('flush-'):
                assert not faults and row['receipt']['writer']['finalize_completed']
            else:assert mode=='loader-only' and not faults
            actual=row['receipt']['writer']
            if demonstrated or mode=='loader-only':
                assert tuple(actual[k] for k in ('stage','after_state','durable_writer_state','abort_usability','abort_attempted','abort_completed'))==expected[mode]
            if actual['abort_attempted']:
                fresh=next(r['observed_ns'] for r in public if r['operation']=='flush_buffer' and r['result']=='returned')
                abort=next(r['observed_ns'] for r in public if r['operation']=='abort' and r['result']=='entered')
                assert fresh<abort
            else:assert not any(r['operation']=='abort' for r in public)
            pins=harness/('stream-inputs-'+mode+'.json')
            pin=read(pins if pins.exists() else harness/('terminal-original-inputs-'+fixture.name+'.json'))
            admission=CoverageAdmission(canonical(pin['original_admission']))
            plan=decode_collection(pin['original_collection'],admission,pin['admission_digest'])
            assert runtime_admission_digest(admission,plan,pin['generation_ns'])==pin['runtime_digest']
            if pins.exists():assert pin['native_bootstrap_digest']=='sha256:'+helper['bootstrap_sha256']
            checked=verify_runtime_closed(admission,plan,fixture/'argus',expected_admission_digest=pin['admission_digest'],
                generation_ns=pin['generation_ns'],expected_runtime_digest=pin['runtime_digest'])
            assert sha(fixture/'argus/manifest.json')==actual['manifest_sha256']
            if checked.complete:
                original_public=fixture/'argus'
                assert not any(p.is_symlink() for p in original_public.rglob('*'))
                original_bytes={str(p.relative_to(original_public)):sha(p) for p in original_public.rglob('*') if p.is_file()}
                destination=out/'closed-public'/(label+'-'+mode);destination.parent.mkdir(exist_ok=True)
                shutil.copytree(fixture/'argus',destination)
                assert {str(p.relative_to(destination)):sha(p) for p in destination.rglob('*') if p.is_file()}==original_bytes
                assert verify_runtime_closed(admission,plan,destination,expected_admission_digest=pin['admission_digest'],
                    generation_ns=pin['generation_ns'],expected_runtime_digest=pin['runtime_digest']).complete
                retained.append(dict(path=str(destination.relative_to(out)),files={str(p.relative_to(destination)):sha(p) for p in destination.rglob('*') if p.is_file()}))
            if row['closure'] is not None:
                closed=row['closure'];assert closed['inventory_complete'] and closed['root_reaped'] and closed['unacknowledged_births']==0
                assert all(h['process_reaped'] and (h['role'] not in (1,4) or h['direct_child_reaped']) for h in closed['helpers'])
                assert all(b['empty'] and b['released'] for b in closed['boundaries']) and closed['authority_fenced'] is True
                assert closed['terminal_reports']==[row['receipt']] and not closed['writers']
            elif demonstrated or mode=='loader-only':raise AssertionError('required original closure missing')
            cases.append(dict(group=group,phase=phase,mode=mode,helper_sha256=sha(helper_path),
                native_trace_sha256=sha(native_path),public_trace_sha256=sha(public_path),
                mechanism_demonstrated=demonstrated,independent_closed_complete=checked.complete,
                explicit_closure_retained=row['closure'] is not None,private_admission_pin_retained=pins.exists()))
assert len(cases)==len(waits)==len(roots)==len(snapshots)==8
passed=all(p['returncode']==0 for p in phases)
assert exit_code==(0 if passed else 1)
result=dict(original_exec_session=handle,original_exec_exit=exit_code,phases=phases,cases=cases,
    packaged_sources=76,production_sources_unchanged=True,root_receipts=roots,wait_receipts=waits,snapshots=snapshots,
    source_links=sum(s['source_links'] for s in snapshots),retained_closed_public=retained,
    source_manifest_sha256=sha(out/'frozen-inputs.json'),auditor_sha256=sha(Path(__file__)),
    W02_isolated_single_fault_complete=False,full_W02_row_complete=False,full_W03_row_complete=False,
    full_TR03_complete=False,full_TR06_complete=False,full_M1_complete=False,stable_increment17=False,accepted=False,merged=False)
with (out/'verification.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(phases=phases,cases=len(cases),source_links=result['source_links'],closed=len(retained))))
