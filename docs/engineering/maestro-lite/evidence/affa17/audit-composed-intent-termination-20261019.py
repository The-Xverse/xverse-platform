"""Inspect actual CP07/08/12 sources, original waits and honest evidence gaps."""
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
test = 'tests/thesis_lite/maestro/test_composed_persistence_termination.py'
tree = ast.parse((source/test).read_text())
helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run_bootstrap_binary')
assignment = next(n for n in helper.body if isinstance(n, ast.Assign) and n.targets[0].id == 'code')
code_template = ast.literal_eval(assignment.value.func.value.func.value)
old_anchor = 'args[2]="-m";args[3]="xverse.maestro.persistence_worker"'
original_native = (source/'src/xverse/maestro/native/bootstrap.c').read_text()
seen_roots, seen_fixtures = set(), set()
phases, roots, waits, snapshots, cases, retained = [], [], [], [], [], []
groups = ('loader',) if (out/'stages-not-executed.json').exists() else ('loader', 'faults')
for group in groups:
    for phase in ('source', 'wheel'):
        label = group+'-'+phase
        receipt = read(out/(label+'-receipt.json'))
        log = out/(label+'.log')
        assert sha(log) == receipt['log_sha256'] and receipt['public_capture_returncode'] == 0
        last = log.read_text().splitlines()[-1]
        counts = {k:int(m.group(1)) if (m:=re.search(r'(\d+) '+k, last)) else 0
            for k in ('passed', 'failed', 'errors', 'deselected')}
        assert sum(counts[k] for k in ('passed', 'failed', 'errors')) == (1 if group == 'loader' else 5)
        assert counts['deselected'] == (5 if group == 'loader' else 1)
        assert (receipt['returncode'] == 0) == (counts['failed'] == counts['errors'] == 0)
        phases.append(dict(group=group, phase=phase, returncode=receipt['returncode'], **counts))
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
        for path in harness.glob('run-broker-waits-*.json'):
            row = read(path)
            assert all(row[k] for k in ('bootstrap_reaped', 'registered_helpers_reaped', 'storage_reaped', 'original_C1_released'))
            phase_waits.append(dict(path=str(path.relative_to(out)), sha256=sha(path)))
        for item in read(out/(label+'-public-evidence-index.json')):
            assert sha(out/item['snapshot']) == item['sha256']
            projection = read(out/item['snapshot'])
            fixture = Path(projection['original_fixture'])
            assert str(fixture) not in seen_fixtures
            seen_fixtures.add(str(fixture))
            assert projection['m3'] == list(FileEvidenceJournal(fixture/'m3.jsonl').public_records())
            assert projection['argus'] == list(EvidenceStore.read_run(fixture/'argus').records())
            by_sequence = {r['sequence']:r for r in projection['m3']}
            mirrored, links = set(), 0
            for event in projection['argus']:
                for ref in event.get('extensions', {}).get('xverse.maestro', {}).get('sourceRefs', []):
                    if ref.get('kind') == 'm3-record':
                        assert ref['sequence'] in by_sequence
                        assert ref['sha256'] == 'sha256:'+hashlib.sha256(canonical_bytes(by_sequence[ref['sequence']])).hexdigest()
                        mirrored.add(ref['sequence']); links += 1
            missing = by_sequence.keys()-mirrored
            assert item['source_links'] == links and item['reader_gaps'] == projection['reader_gaps']
            assert {g['m3_sequence'] for g in item['reader_gaps']} == missing
            assert all(g['source'] == 'Argus mirror' and g['error'] ==
                'original M3 record lacks an actual Argus reference' for g in item['reader_gaps'])
            phase_snapshots.append(dict(group=group, phase=phase, **item))
        for path in harness.glob('intent-termination-*.json'):
            row = read(path); fixture = Path(row['original_fixture'])
            assert row['source_sha256'] == frozen[test]
            helper_path = harness/('intent-helper-'+fixture.name+'.json')
            meta = read(helper_path)
            code = code_template.replace('MODE_LITERAL', repr(meta['mode'])).replace('TRACE_LITERAL', repr(meta['trace']))
            assert code == meta['fixed_role3_code']
            assert meta['source_sha256'] == frozen[test]
            assert meta['original_native_source_sha256'] == frozen['src/xverse/maestro/native/bootstrap.c']
            compiled = fixture/'owned-intent-helper/bootstrap.c'
            binary = fixture/'owned-intent-helper/run-bootstrap'
            assert sha(compiled) == meta['compiled_source_sha256'] and sha(binary) == meta['binary_sha256']
            assert compiled.read_text().replace('args[2]="-c";args[3]='+json.dumps(code), old_anchor) == original_native
            assert not any(isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                and n.value.id == 'self' and n.attr.startswith('_') for n in ast.walk(ast.parse(code)))
            trace_path = Path(meta['trace'])
            trace = [json.loads(line) for line in trace_path.read_text().splitlines()]
            assert all(a['observed_ns'] <= b['observed_ns'] for a, b in zip(trace, trace[1:]))
            assert row['public_m3'] == list(FileEvidenceJournal(fixture/'m3.jsonl').public_records())
            assert row['argus_events'] == list(EvidenceStore.read_run(fixture/'argus').records())
            closed = row['closure']
            assert closed['root_reaped'] and closed['authority_fenced'] and closed['inventory_complete']
            assert all(h['process_reaped'] for h in closed['helpers'])
            assert all(b['empty'] and b['released'] for b in closed['boundaries'])
            direct = all(h['process_reaped'] and (h['role'] not in (1,4) or h['direct_child_reaped']) for h in closed['helpers'])
            assert direct == row['cleanup_complete'] and not closed['lifecycle_complete']
            before, after = row['sentinel_before'], row['sentinel_after']
            assert before['members'] == after['members'] and before['boundary_identity'] == after['boundary_identity']
            assert all(s['unfrozen'] and s['parent_alive'] and not s['cancellation_latch'] for s in (before,after))
            assert after['fresh_heartbeat_began'] <= after['fresh_heartbeat_observed']
            mode = meta['mode']
            if row['case'].startswith('intent-') and mode != 'disabled':
                observed = row['observations']
                assert observed['original_pidfd_stop']['status'] == 19
                assert trace[-1]['observed_ns']/1e9 <= observed['original_pidfd_stop']['observed'] <= observed['original_helper_killed']
                assert not any(e['kind'] in ('STAGE','ARM','RELEASE') for e in observed['exchanges'])
                assert not row['markers'] and direct and all(f['issued'] is False for f in closed['native_units'])
                actions = [e['action'] for e in trace]
                assert actions == (['before-intent-append'] if mode == 'before-intent-append'
                    else ['before-intent-append','intent-append-returned','after-intent-flush'])
                first = trace[0]['payload']; ref = first['sourceRefs'][0]
                actual = next(r for r in row['public_m3'] if r['sequence'] == ref['sequence'])
                assert actual['kind'] == 'intent' and actual['actionId'] == 'start'
                assert ref['sha256'] == 'sha256:'+hashlib.sha256(canonical_bytes(actual)).hexdigest()
                mirrors = [e for e in row['argus_events'] if e.get('extensions', {}).get('xverse.maestro', {}).get('action') == 'intent']
                assert len(mirrors) == int(mode == 'after-intent-flush')
                assert not row['execution_succeeded'] and not row['original_runtime_verification_complete']
            elif row['case'].startswith('stop-'):
                observed = row['observations']
                compiler = read(harness/('descendant-compiler-'+fixture.name+'.json'))
                assert compiler['source_sha256'] == frozen['tests/thesis_lite/maestro/catalog_workload_leader_descendant.c']
                assert sha(Path(compiler['command'][-1])) == compiler['binary_sha256']
                assert row['markers'] == observed['markers_before_loss'] and len(row['markers']) == 2
                assert all(v == 'EXEC\nDESCENDANT\n' for v in row['markers'].values())
                assert len(observed['sink_members_at_barrier']) == (2 if row['case'] == 'stop-before-send' else 0)
                if row['case'] == 'stop-after-reply':
                    ack = next(e for e in observed['exchanges'] if e['reply'] == 'STOPPED')
                    assert ack['state'] & 8 and ack['returned'] <= observed['killed_at']
                    sink = next(f for f in closed['native_units'] if 'sink-instance' in f['unit_id'])
                    assert sink['direct_child_reaped'] is True
                if not direct:
                    assert 'ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN' in closed['diagnostics']
                assert not row['execution_succeeded'] and not row['original_runtime_verification_complete']
            else:
                assert row['case'] == 'intent-disabled' and row['execution_succeeded'] and direct
                assert row['original_runtime_verification_complete']
                assert len(trace) == (18 if '20261019a' in out.name else 6)
            pin = read(harness/('terminal-original-inputs-'+fixture.name+'.json'))
            admission = CoverageAdmission(canonical(pin['original_admission']))
            plan = decode_collection(pin['original_collection'], admission, pin['admission_digest'])
            assert runtime_admission_digest(admission, plan, pin['generation_ns']) == pin['runtime_digest']
            checked = verify_runtime_closed(admission, plan, fixture/'argus',
                expected_admission_digest=pin['admission_digest'], generation_ns=pin['generation_ns'],
                expected_runtime_digest=pin['runtime_digest'])
            assert checked.complete == row['original_runtime_verification_complete']
            target = out/'retained-public'/(label+'-'+fixture.name)
            target.parent.mkdir(exist_ok=True)
            original = fixture/'argus'
            assert not any(p.is_symlink() for p in original.rglob('*'))
            originals = {str(p.relative_to(original)):sha(p) for p in original.rglob('*') if p.is_file()}
            shutil.copytree(original, target)
            assert {str(p.relative_to(target)):sha(p) for p in target.rglob('*') if p.is_file()} == originals
            retained.append(dict(path=str(target.relative_to(out)), files=originals, independently_complete=checked.complete))
            phase_cases.append(dict(group=group, phase=phase, case=row['case'], receipt=str(path.relative_to(out)),
                sha256=sha(path), helper_sha256=sha(helper_path), trace_sha256=sha(trace_path),
                cleanup_complete=direct, independently_complete=checked.complete))
        expected = 1 if group == 'loader' else 5
        assert len(phase_roots) == len(phase_waits) == len(phase_snapshots) == len(phase_cases) == expected
        roots += phase_roots; waits += phase_waits; snapshots += phase_snapshots; cases += phase_cases
passed = all(p['returncode'] == 0 for p in phases)
assert exit_code == (0 if passed else 1)
result = dict(original_exec_session=handle, original_exec_exit=exit_code, phases=phases, cases=cases,
    packaged_sources=len(packaged), production_sources_unchanged=True, root_receipts=roots, wait_receipts=waits,
    snapshots=snapshots, source_links=sum(s['source_links'] for s in snapshots), retained_public=retained,
    original_source_manifest_sha256=sha(out/'frozen-inputs.json'), auditor_sha256=sha(Path(__file__)),
    full_CP07_row_complete=False, full_CP08_row_complete=False, full_CP12_row_complete=False,
    full_crash_matrix_complete=False, full_M1_complete=False, stable_increment17=False, accepted=False, merged=False)
with (out/'verification.json').open('x') as stream:
    json.dump(result, stream, indent=2); stream.write('\n')
print(json.dumps(dict(phases=phases, cases=len(cases), roots=len(roots), waits=len(waits),
    source_links=result['source_links'], complete_public=sum(r['independently_complete'] for r in retained))))
