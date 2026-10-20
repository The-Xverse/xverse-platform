"""Read-only native race/crash evidence audit; never executes a workload."""
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
assert all(sha(source/n) == h for n, h in frozen.items())
previous = read(out.parent/'active-control-deadlines-20261019c/frozen-inputs.json')
assert all(previous[n] == h for n, h in frozen.items() if n.startswith('src/'))
installed = Path(sysconfig.get_path('purelib'))
packaged = []
with zipfile.ZipFile(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl') as wheel:
    for name, value in frozen.items():
        if name.startswith('src/') and name.endswith(('.py', '.c')):
            entry = name.removeprefix('src/')
            assert hashlib.sha256(wheel.read(entry)).hexdigest() == value == sha(installed/entry)
            packaged.append(entry)
assert len(packaged) == 76
expected = {('cancel', w) for w in ('stage-before-send', 'stage-ack-pending',
    'release-before-send', 'release-ack-pending', 'release-after-reply')}
expected |= {('authority', w) for w in ('stage-before-send', 'stage-ack-pending')}
expected |= {('storage', w) for w in ('issuance-before-record', 'issuance-after-record')}
phases, roots, waits, snapshots, cases = [], [], [], [], []
seen_roots, seen_fixtures = set(), set()
for phase in ('source', 'wheel'):
    label = 'interruptions-'+phase
    receipt = read(out/(label+'-receipt.json'))
    log = out/(label+'.log')
    assert sha(log) == receipt['log_sha256'] and receipt['public_capture_returncode'] == 0
    last = log.read_text().splitlines()[-1]
    counts = {k: int(m.group(1)) if (m := re.search(r'(\d+) '+k, last)) else 0
        for k in ('passed', 'failed', 'errors')}
    assert sum(counts.values()) == 9
    assert (receipt['returncode'] == 0) == (counts['failed'] == counts['errors'] == 0)
    phases.append(dict(phase=phase, returncode=receipt['returncode'], **counts))
    harness = out/(label+'-harness')
    phase_roots, phase_waits, phase_cases, phase_snapshots = [], [], [], []
    for path in harness.glob('maestro-component-*.json'):
        row = read(path)
        identity = row['parent_path'], row['root_name']
        assert identity not in seen_roots
        seen_roots.add(identity)
        assert row['root_removed'] and row['workers_reaped']
        assert not (Path(row['parent_path'])/row['root_name']).exists()
        phase_roots.append(dict(path=str(path.relative_to(out)), sha256=sha(path)))
    assert len(phase_roots) == 9
    for path in harness.glob('run-broker-waits-*.json'):
        row = read(path)
        assert all(row[k] for k in ('bootstrap_reaped', 'registered_helpers_reaped',
            'storage_reaped', 'original_C1_released'))
        phase_waits.append(dict(path=str(path.relative_to(out)), sha256=sha(path)))
    for item in read(out/(label+'-public-evidence-index.json')):
        assert sha(out/item['snapshot']) == item['sha256']
        projection = read(out/item['snapshot'])
        fixture = Path(projection['original_fixture'])
        assert str(fixture) not in seen_fixtures
        seen_fixtures.add(str(fixture))
        assert projection['m3'] == list(FileEvidenceJournal(fixture/'m3.jsonl').public_records())
        assert projection['argus'] == list(EvidenceStore.read_run(fixture/'argus').records())
        by_sequence = {r['sequence']: r for r in projection['m3']}
        mirrored, links = set(), 0
        for event in projection['argus']:
            for ref in event.get('extensions', {}).get('xverse.maestro', {}).get('sourceRefs', []):
                if ref.get('kind') == 'm3-record':
                    assert ref['sequence'] in by_sequence
                    assert ref['sha256'] == 'sha256:'+hashlib.sha256(canonical_bytes(by_sequence[ref['sequence']])).hexdigest()
                    mirrored.add(ref['sequence'])
                    links += 1
        missing = by_sequence.keys()-mirrored
        assert links == item['source_links']
        assert projection['reader_gaps'] == item['reader_gaps']
        assert {g['m3_sequence'] for g in item['reader_gaps']} == missing
        assert all(g['source'] == 'Argus mirror' and g['error'] ==
            'original M3 record lacks an actual Argus reference' for g in item['reader_gaps'])
        phase_snapshots.append(dict(phase=phase, **item))
    compiler = read(harness/'heartbeat-compiler.json')
    assert compiler['source_sha256'] == frozen['tests/thesis_lite/maestro/unrelated_heartbeat_fixture.c']
    assert compiler['returncode'] == 0
    assert sha(Path(compiler['command'][-1])) == compiler['binary_sha256']
    for path in harness.glob('composed-authority-*.json'):
        row = read(path)
        fixture = Path(row['original_fixture'])
        assert row['source_sha256'] == frozen['tests/thesis_lite/maestro/test_composed_authority_interruptions.py']
        assert row['public_m3'] == list(FileEvidenceJournal(fixture/'m3.jsonl').public_records())
        assert row['argus_events'] == list(EvidenceStore.read_run(fixture/'argus').records())
        assert (row['fault'], row['window']) in expected
        before, after = row['sentinel_before'], row['sentinel_after']
        assert before['members'] == after['members'] and before['boundary_identity'] == after['boundary_identity']
        for sentinel in (before, after):
            assert sentinel['parent_alive'] and sentinel['unfrozen'] and not sentinel['cancellation_latch']
            assert sentinel['membership_observation_only']
            assert sentinel['fresh_heartbeat_began'] <= sentinel['fresh_heartbeat_observed']
        point = row['barrier'][0]
        assert point['reached'] <= row['observations']['at_barrier'] <= row['observations']['effect_completed'] <= point['resumed']
        assert after['fresh_heartbeat_began'] > point['resumed']
        closure = row['closure']
        assert closure['authority_fenced'] and closure['root_reaped'] and closure['inventory_complete']
        assert closure['unacknowledged_births'] == 0
        assert all(h['process_reaped'] for h in closure['helpers'])
        assert all(b['empty'] and b['released'] for b in closure['boundaries'])
        direct = all(h['process_reaped'] and (h['role'] not in (1, 4) or h['direct_child_reaped']) for h in closure['helpers'])
        assert row['cleanup_complete'] == direct
        assert not row['execution_succeeded'] and not closure['lifecycle_complete']
        assert not any(e.get('extensions', {}).get('xverse.maestro', {}).get('action') == 'started' for e in row['argus_events'])
        released = row['window'].startswith('release-') and row['window'] != 'release-before-send'
        assert len(row['markers']) == int(released)
        assert all(text == 'EXEC\n' for text in row['markers'].values())
        if not direct:
            assert 'ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN' in closure['diagnostics']
        if row['terminal']:
            assert closure['terminal_reports'] == [row['terminal']]
            report = row['terminal'].get('report')
            if report:
                assert not report['eligible']
        if 'original_exchange_returns' in row:
            staged = [e for e in row['original_exchange_returns'] if e['reply'] == 'STAGED']
            committed = [e for e in row['original_exchange_returns'] if e['reply'] == 'RELEASED']
            if row['window'] == 'release-after-reply':
                assert len(committed) == 1 and committed[0]['returned'] <= point['reached']
            if row['window'] == 'stage-ack-pending':
                first = next(f for f in closure['native_units'] if 'source-instance' in f['unit_id'])
                assert first['issued'] is (True if staged else None)
                assert first['direct_child_reaped'] is None and not direct
            assert row['host_handle_after_run'] == bool(staged)
        pin = read(harness/('terminal-original-inputs-'+fixture.name+'.json'))
        admission = CoverageAdmission(canonical(pin['original_admission']))
        plan = decode_collection(pin['original_collection'], admission, pin['admission_digest'])
        assert runtime_admission_digest(admission, plan, pin['generation_ns']) == pin['runtime_digest']
        checked = verify_runtime_closed(admission, plan, fixture/'argus', expected_admission_digest=pin['admission_digest'],
            generation_ns=pin['generation_ns'], expected_runtime_digest=pin['runtime_digest'])
        assert not checked.complete
        if exit_code == 0:
            destination = out/'retained-public'/(phase+'-'+fixture.name)
            destination.parent.mkdir(exist_ok=True)
            original = fixture/'argus'
            assert not any(p.is_symlink() for p in original.rglob('*'))
            original_bytes = {str(p.relative_to(original)): sha(p) for p in original.rglob('*') if p.is_file()}
            shutil.copytree(original, destination)
            assert {str(p.relative_to(destination)): sha(p) for p in destination.rglob('*') if p.is_file()} == original_bytes
        phase_cases.append(dict(phase=phase, fault=row['fault'], window=row['window'],
            receipt=str(path.relative_to(out)), sha256=sha(path), cleanup_complete=direct,
            original_runtime_verification_complete=checked.complete))
    if exit_code == 0:
        assert len(phase_waits) == len(phase_snapshots) == len(phase_cases) == 9
        assert {(r['fault'], r['window']) for r in phase_cases} == expected
    elif '20261019a' in out.name:
        assert not phase_waits and not phase_snapshots and not phase_cases
    roots += phase_roots
    waits += phase_waits
    snapshots += phase_snapshots
    cases += phase_cases
passed = all(r['returncode'] == 0 for r in phases)
assert exit_code == (0 if passed else 1)
result = dict(original_exec_session=handle, original_exec_exit=exit_code, phases=phases,
    packaged_sources=len(packaged), production_sources_unchanged=True, root_receipts=roots,
    wait_receipts=waits, snapshots=snapshots, cases=cases, source_links=sum(r['source_links'] for r in snapshots),
    original_source_manifest_sha256=sha(out/'frozen-inputs.json'), auditor_sha256=sha(Path(__file__)),
    runtime_cases_fully_complete=False, full_crash_matrix_complete=False, full_M1_complete=False,
    stable_increment17=False, independent_CAPA_effectiveness=False, accepted=False, merged=False)
with (out/'verification.json').open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(phases=phases, cases=len(cases), native_waits=len(waits), roots=len(roots),
    source_links=result['source_links'])))
