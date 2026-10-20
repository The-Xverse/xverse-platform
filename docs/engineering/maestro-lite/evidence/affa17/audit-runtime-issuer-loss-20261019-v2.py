"""Audit original whole-entry registry-loss red/repair; never infer wait facts."""
import hashlib
import json
from pathlib import Path
import re
import sys
import sysconfig
import zipfile

from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse.maestro.collection_plan import decode_collection
from xverse.maestro.coverage import CoverageAdmission, canonical
from xverse.maestro.runtime_verification import runtime_admission_digest, verify_runtime_closed
from xverse_xdl.lifecycle import FileEvidenceJournal

out = Path(sys.argv[1]).resolve(strict=True)
handle, original_exit = int(sys.argv[2]), int(sys.argv[3])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
frozen = read(out / 'frozen-inputs.json')
source = Path(read(out / 'running.json')['frozen_source_root'])
assert all(sha(source / n) == digest for n, digest in frozen.items())
old = read(out.parent / 'integrated-maestro-20261019a/frozen-inputs.json')
production = {n: h for n, h in frozen.items() if n.startswith('src/') and n.endswith(('.py', '.c'))}
assert len(production) == 81
changed = sorted(n for n, h in production.items() if old[n] != h)
repaired = out.name.endswith('19b')
assert changed == (['src/xverse/maestro/run_closure.py'] if repaired else [])
installed = Path(sysconfig.get_path('purelib'))
with zipfile.ZipFile(next((out / 'dist').glob('*.whl'))) as wheel:
    for name, digest in production.items():
        entry = name.removeprefix('src/')
        assert hashlib.sha256(wheel.read(entry)).hexdigest() == digest == sha(installed / entry)

phases, roots, cases, projections = [], [], [], []
seen = set()
for path in sorted(out.glob('*-receipt.json')):
    receipt = read(path)
    if 'cohort' not in receipt:
        continue
    label = path.name.removesuffix('-receipt.json')
    log = out / (label + '.log')
    assert sha(log) == receipt['log_sha256'] and receipt['public_capture_returncode'] == 0
    assert receipt['input_manifest_sha256'] == sha(out / 'frozen-inputs.json')
    last = log.read_text().splitlines()[-1]
    counts = {key: int(match.group(1)) if (match := re.search(r'(\d+) ' + key, last)) else 0
              for key in ('passed', 'failed', 'errors')}
    assert (receipt['returncode'] == 0) == (counts['failed'] == counts['errors'] == 0)
    phases.append(dict(cohort=receipt['cohort'], phase=receipt['phase'],
        returncode=receipt['returncode'], receipt_sha256=sha(path), **counts))
    harness = out / (label + '-harness')
    for raw in harness.glob('maestro-component-*.json'):
        row = read(raw)
        identity = row['parent_path'], row['root_name']
        assert identity not in seen
        seen.add(identity)
        assert row['root_removed'] and row['workers_reaped']
        assert not (Path(row['parent_path']) / row['root_name']).exists()
        roots.append(dict(path=str(raw.relative_to(out)), sha256=sha(raw)))
    for raw in harness.glob('runtime-issuer-loss-*.json'):
        row = read(raw)
        assert row['injection_reached'] and row['ordinary_rejected'] and row['original_stop_returned']
        assert row['native_members_before_loss'] and row['start_lock_held']
        assert row['handle_published_before_loss'] is (row['window'] == 'after-release')
        assert row['release_ack_before_loss'] is (row['window'] == 'after-release')
        assert row['primary_returned'] and not row['primary_exceptions']
        assert row['actual_original_root_wait'] and row['actual_original_helper_waits']
        assert row['all_original_C1_released'] and row['ordinary_map_restored_after_actual_cleanup']
        assert row['actual_M1_admissions'] == 0 and not row['full_runtime_case_complete']
        primary = row['primary_closure']
        if repaired:
            assert primary is not None and row['fallback'] is None
            assert primary['root_reaped'] and all(h['process_reaped'] for h in primary['helpers'])
            assert all(b['empty'] and b['released'] for b in primary['boundaries'])
            assert not primary['cleanup_complete'] and not primary['normal_unit_records_complete']
            assert row['explicit_original_cleanup_constructor_accepted_without_IO']
            assert row['copied_broker_rejected_without_IO']
            assert row['matching_result_retained'] and row['matching_collection_retained']
            assert row['replay_original_process_unchanged']
            before, after = row['sentinel_before'], row['sentinel_after']
            for key in ('boundary_identity', 'members', 'parent_alive', 'unfrozen', 'cancellation_latch'):
                assert before[key] == after[key]
            assert after['fresh_heartbeat_observed'] > before['fresh_heartbeat_observed']
            assert not row['markers'].get('sink-binding.marker')
            if row['window'] == 'before-handle':
                assert not row['markers']
        else:
            assert primary is None and row['fallback'] is not None
            assert row['fallback']['root_reaped']
            assert row['diagnostics'] == ['ML-RUNTIME-ENTRY-CLOSURE-UNRESOLVED']
            assert 'sentinel_after' not in row  # first failed assertion prevented this observation
        fixture = Path(row['original_fixture'])
        original_path = harness / ('entry-original-inputs-' + fixture.name + '.json')
        original = read(original_path)
        admission = CoverageAdmission(canonical(original['original_admission']))
        plan = decode_collection(original['original_collection'], admission, original['admission_digest'])
        assert runtime_admission_digest(admission, plan, original['generation_ns']) == original['runtime_digest']
        verified = verify_runtime_closed(admission, plan, fixture / 'argus',
            expected_admission_digest=original['admission_digest'], generation_ns=original['generation_ns'],
            expected_runtime_digest=original['runtime_digest'])
        assert not verified.complete
        cases.append(dict(phase=receipt['phase'], path=str(raw.relative_to(out)), sha256=sha(raw),
            window=row['window'], primary_closure_returned=primary is not None,
            external_fallback=row['fallback'] is not None, original_inputs_sha256=sha(original_path),
            offline_complete=False, sentinel_after_observed='sentinel_after' in row))
    for item in read(out / (label + '-public-evidence-index.json')):
        raw = out / item['snapshot']
        assert sha(raw) == item['sha256']
        data = read(raw)
        fixture = Path(data['original_fixture'])
        records = list(FileEvidenceJournal(fixture / 'm3.jsonl').public_records()) if (fixture / 'm3.jsonl').is_file() else []
        assert data['m3'] == records
        try:
            events = list(EvidenceStore.read_run(fixture / 'argus').records())
        except Exception:
            assert any(g['source'] == 'Argus' for g in data['reader_gaps'])
            events = []
        assert data['argus'] == events
        by_sequence = {r['sequence']: r for r in records}
        links = 0
        for event in events:
            for ref in event.get('extensions', {}).get('xverse.maestro', {}).get('sourceRefs', []):
                if ref.get('kind') == 'm3-record' and (actual := by_sequence.get(ref['sequence'])) is not None:
                    if ref['sha256'] == 'sha256:' + hashlib.sha256(canonical_bytes(actual)).hexdigest():
                        links += 1
        assert links == item['source_links'] == data['actual_normal_source_hashes_verified']
        projections.append(dict(label=label, **item))

assert len(cases) == 4 and {(r['phase'], r['window']) for r in cases} == {
    (p, w) for p in ('source', 'wheel') for w in ('before-handle', 'after-release')}
counts = {p: {k: sum(r[k] for r in phases if r['phase'] == p) for k in ('passed', 'failed', 'errors')}
          for p in ('source', 'wheel')}
if repaired:
    assert original_exit == 0
    assert len(phases) == 16 and counts == {p:dict(passed=85, failed=0, errors=0) for p in ('source', 'wheel')}
else:
    assert original_exit == 1
    assert len(phases) == 2 and counts == {p:dict(passed=0, failed=2, errors=0) for p in ('source', 'wheel')}
    assert len(roots) == 4  # one environment root per test; managers share it
result = dict(auditor_sha256=sha(Path(__file__)), original_exec_session=handle,
    original_exec_exit=original_exit, phases=phases, counts=counts,
    frozen_manifest_sha256=sha(out / 'frozen-inputs.json'), packaged_python_c_files=81,
    changed_packaged_sources=changed, other_packaged_sources_unchanged=81-len(changed),
    root_receipts=roots, whole_entry_cases=cases, public_projections=projections,
    source_links=sum(r['source_links'] for r in projections), primary_cleanup_cases=4 if repaired else 0,
    external_fallback_cases=0 if repaired else 4, missing_red_post_sentinel_observations=0 if repaired else 4,
    original_wait_unknowns_preserved=True, actual_M1_admissions=0,
    historical_timeout_incidents_unresolved=[135,222,286,287,318,324,330,331,332],
    independent_cause_confirmation=False, CAPA_effectiveness_demonstrated=False,
    full_maestro_regression_passed=False, whole_platform_regression=False,
    stable_increment17=False, accepted=False, merged=False)
with (out / 'verification.json').open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(counts=counts, original_owned_roots_absent=len(roots),
    source_links=result['source_links'], primary_cleanup_cases=result['primary_cleanup_cases'],
    external_fallback_cases=result['external_fallback_cases'])))
