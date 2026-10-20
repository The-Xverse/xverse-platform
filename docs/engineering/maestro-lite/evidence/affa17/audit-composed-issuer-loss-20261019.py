"""Audit original red/successor scopes, no-adoption and late-request ordering."""
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
from xverse.argus.schema import canonical_bytes
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
baseline_folder = out if out.name.endswith('19a') else out.parent/'composed-issuer-loss-20261019a'
baseline = read(baseline_folder/'frozen-inputs.json')
changed = [n for n,h in frozen.items() if n.startswith('src/') and baseline[n] != h]
assert set(changed) <= {'src/xverse/maestro/run_broker.py','src/xverse/maestro/run_closure.py'}
installed = Path(sysconfig.get_path('purelib'))
packaged = []
with zipfile.ZipFile(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl') as wheel:
    for name,value in frozen.items():
        if name.startswith('src/') and name.endswith(('.py','.c')):
            entry = name.removeprefix('src/')
            assert hashlib.sha256(wheel.read(entry)).hexdigest() == value == sha(installed/entry)
            packaged.append(entry)
assert len(packaged) == 76
receipts = []
for path in out.glob('*-receipt.json'):
    row = read(path)
    if 'public_capture_returncode' in row:
        receipts.append((path, row))
roots, waits, snapshots, cases, closed_roots, phases = [], [], [], [], [], []
seen_roots, seen_fixtures = set(), set()
for receipt_path, receipt in sorted(receipts):
    label = receipt_path.name.removesuffix('-receipt.json')
    phase = receipt.get('phase', 'wheel' if label.endswith('wheel') else 'source')
    log = out/(label+'.log')
    assert sha(log) == receipt['log_sha256'] and receipt['public_capture_returncode'] == 0
    last = log.read_text().splitlines()[-1]
    counts = {k:int(m.group(1)) if (m:=re.search(r'(\d+) '+k,last)) else 0 for k in ('passed','failed','errors')}
    phases.append(dict(label=label,phase=phase,returncode=receipt['returncode'],**counts))
    assert (receipt['returncode'] == 0) == (counts['failed'] == counts['errors'] == 0)
    harness = out/(label+'-harness')
    for path in harness.glob('maestro-component-*.json'):
        row = read(path); identity = row['parent_path'],row['root_name']
        assert identity not in seen_roots; seen_roots.add(identity)
        assert row['root_removed'] and row['workers_reaped']
        assert not (Path(row['parent_path'])/row['root_name']).exists()
        roots.append(dict(path=str(path.relative_to(out)),sha256=sha(path)))
    for path in harness.glob('run-broker-waits-*.json'):
        row = read(path)
        assert all(row[k] for k in ('bootstrap_reaped','registered_helpers_reaped','storage_reaped','original_C1_released'))
        waits.append(dict(path=str(path.relative_to(out)),sha256=sha(path)))
    for item in read(out/(label+'-public-evidence-index.json')):
        assert sha(out/item['snapshot']) == item['sha256']
        projection = read(out/item['snapshot']); fixture = Path(projection['original_fixture'])
        assert str(fixture) not in seen_fixtures; seen_fixtures.add(str(fixture))
        actual_m3, actual_argus, gaps = [], [], []
        journal = fixture/'m3.jsonl'
        if journal.is_file():
            try:
                actual_m3 = list(FileEvidenceJournal(journal).public_records())
            except Exception as error:
                gaps.append(dict(source='M3',error=type(error).__name__+': '+str(error)))
        else:
            gaps.append(dict(source='M3',error='original journal missing'))
        try:
            actual_argus = list(EvidenceStore.read_run(fixture/'argus').records())
        except Exception as error:
            gaps.append(dict(source='Argus',error=type(error).__name__+': '+str(error)))
        assert actual_m3 == projection['m3'] and actual_argus == projection['argus']
        by_sequence = {r['sequence']:r for r in actual_m3}
        mirrored, links = set(),0
        for event in actual_argus:
            for ref in event.get('extensions',{}).get('xverse.maestro',{}).get('sourceRefs',[]):
                if ref.get('kind') == 'm3-record':
                    actual = by_sequence.get(ref['sequence'])
                    if actual is None or ref['sha256'] != 'sha256:'+hashlib.sha256(canonical_bytes(actual)).hexdigest():
                        gaps.append(dict(source='M3 reference',event=event['eventId'],reference=ref,error='original source unavailable or hash mismatch'))
                    else:
                        links += 1; mirrored.add(ref['sequence'])
        for sequence in by_sequence.keys()-mirrored:
            gaps.append(dict(source='Argus mirror',m3_sequence=sequence,error='original M3 record lacks an actual Argus reference'))
        assert gaps == projection['reader_gaps'] == item['reader_gaps']
        assert links == item['source_links']
        snapshots.append(dict(label=label,**item))
        pin = harness/('terminal-original-inputs-'+fixture.name+'.json')
        if pin.exists():
            inputs = read(pin)
            admission = CoverageAdmission(canonical(inputs['original_admission']))
            plan = decode_collection(inputs['original_collection'], admission, inputs['admission_digest'])
            assert runtime_admission_digest(admission, plan, inputs['generation_ns']) == inputs['runtime_digest']
            checked = verify_runtime_closed(admission,plan,fixture/'argus',expected_admission_digest=inputs['admission_digest'],
                generation_ns=inputs['generation_ns'],expected_runtime_digest=inputs['runtime_digest'])
            if checked.complete:
                original = fixture/'argus'
                assert not any(p.is_symlink() for p in original.rglob('*'))
                originals = {str(p.relative_to(original)):sha(p) for p in original.rglob('*') if p.is_file()}
                destination = out/'retained-closed-public'/(label+'-'+fixture.name)
                destination.parent.mkdir(exist_ok=True)
                shutil.copytree(original,destination)
                assert {str(p.relative_to(destination)):sha(p) for p in destination.rglob('*') if p.is_file()} == originals
                closed_roots.append(dict(path=str(destination.relative_to(out)),files=originals))
    for path in harness.glob('issuer-loss-*.json'):
        row = read(path); obs = row['observations']; primary, fallback = row['primary'],row['fallback']
        result = primary or fallback
        assert row['source_sha256'] == frozen['tests/thesis_lite/maestro/test_composed_issuer_loss.py']
        assert result['root_reaped'] and result['authority_fenced']
        assert all(h['process_reaped'] for h in result['helpers'])
        assert all(b['empty'] and b['released'] for b in result['boundaries'])
        assert not result['cleanup_complete'] and not result['lifecycle_complete']
        assert 'ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN' in result['diagnostics']
        before,after = row['sentinel_before'],row['sentinel_after']
        assert before['members'] == after['members'] and before['boundary_identity'] == after['boundary_identity']
        assert all(r['parent_alive'] and r['unfrozen'] and not r['cancellation_latch'] for r in (before,after))
        assert after['fresh_heartbeat_began'] <= after['fresh_heartbeat_observed']
        if row['case'].startswith('queued-'):
            assert primary and fallback is None and not row['dispatcher_failures'] and not row['markers']
            assert obs['original_stopped_at'] <= obs['original_request_sent_at'] <= obs['original_wait_observed_at']
            assert obs['cancellation']['issuer_dead'] and obs['cancellation']['issuer_reaped']
            assert obs['late_original_request_rejected'] and obs['removal_fences']
            assert all(f['issuer_reaped'] and f['pidfd_dead'] and f['before_removal'] >= obs['original_wait_observed_at'] for f in obs['removal_fences'])
        else:
            assert obs['ordinary_rejected'] and obs['restoration_after_original_cleanup']
            assert len(row['markers']) == 1 and list(row['markers'].values()) == ['EXEC\n']
            assert obs['restored_at'] > after['fresh_heartbeat_observed']
            if exit_code == 0:
                assert obs['cancellation_error'] is None and not row['dispatcher_failures'] and row['dispatcher_result']
                assert primary and fallback is None and obs['primary_error'] is None
                assert len(primary['native_units']) == 2
            else:
                assert obs['cancellation_error'] == 'ML-RUN-REPLACED' and row['dispatcher_failures'] == ["OwnerError('ML-RUN-REPLACED')"]
                if out.name.endswith('19a') and row['case'] == 'generation-nonmapping':
                    assert primary is None and fallback and obs['primary_error'].startswith('AttributeError:')
        cases.append(dict(label=label,case=row['case'],receipt=str(path.relative_to(out)),sha256=sha(path),
            primary_returned=primary is not None,fallback_used=fallback is not None,cancellation_error=obs.get('cancellation_error')))
assert len(cases) == 12
assert len(roots) == len(waits) == len(snapshots)
counts = {p:{key:sum(r[key] for r in phases if r['phase']==p) for key in ('passed','failed','errors')} for p in ('source','wheel')}
expected = (dict(passed=2,failed=4,errors=0) if out.name.endswith('19a') else
    dict(passed=35,failed=4,errors=15) if out.name.endswith('19b') else dict(passed=54,failed=0,errors=0))
assert all(r == expected for r in counts.values())
assert len(roots) == (12 if out.name.endswith('19a') else 78 if out.name.endswith('19b') else 108)
assert exit_code == (0 if all(r['returncode'] == 0 for r in phases) else 1)
result = dict(original_exec_session=handle,original_exec_exit=exit_code,phases=phases,counts=counts,cases=cases,
    packaged_sources=76,changed_production_sources=changed,root_receipts=roots,wait_receipts=waits,snapshots=snapshots,
    source_links=sum(s['source_links'] for s in snapshots),retained_closed_public=closed_roots,
    auditor_sha256=sha(Path(__file__)),source_manifest_sha256=sha(out/'frozen-inputs.json'),
    independent_cause_confirmation=False,CAPA_effectiveness_demonstrated=False,full_M1_complete=False,
    full_platform_regression=False,stable_increment17=False,accepted=False,merged=False)
with (out/'verification.json').open('x') as stream:
    json.dump(result,stream,indent=2); stream.write('\n')
print(json.dumps(dict(counts=counts,native_contexts=len(roots),source_links=result['source_links'],closed=len(closed_roots))))
