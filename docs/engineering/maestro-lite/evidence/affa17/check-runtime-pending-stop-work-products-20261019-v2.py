"""Bind retained partial pending-stop work products; never rerun a workload."""
import ast
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
root = base.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
folder = base / 'runtime-pending-stop-20261019a'
manifest = read(folder / 'frozen-inputs.json')
assert all(sha(root / name) == digest for name, digest in manifest.items())
prior = read(base / 'startup-ownership-20261019c/frozen-inputs.json')
production = {n: h for n, h in manifest.items() if n.startswith('src/')}
assert len(production) == 118
assert len([n for n in production if n.endswith(('.py', '.c'))]) == 81
assert production == {n: h for n, h in prior.items() if n.startswith('src/')}

trace_path = base / 'runtime-pending-stop-partial-traceability.json'
trace = read(trace_path)
assert len(trace['requirements']) == 24
assert len({row['id'] for row in trace['requirements']}) == 24
assert len(trace['source_parent_register']['requirements']) == 18
reverse = {}
occurrences = 0
for row in trace['requirements']:
    assert row['full_requirement_closure'] is False
    for delta in row['component_deltas']:
        assert delta['full_requirement_closure'] is False
        assert delta['evidence'] == trace['evidence']
        for item in delta['code'] + delta['tests']:
            path, name = item['endpoint'].split('::')
            assert sha(root / path) == item['file_sha256'] == manifest[path]
            assert read(base / item['frozen_manifest']) == manifest
            scope = ast.parse((root / path).read_text())
            parts = name.split('.')
            if len(parts) == 2:
                scope = next(n for n in scope.body if isinstance(n, ast.ClassDef) and n.name == parts[0])
            endpoint = next(n for n in scope.body if isinstance(n, ast.FunctionDef) and n.name == parts[-1])
            assert endpoint.lineno == item['line']
            reverse.setdefault(item['endpoint'], set()).add(row['id'])
            occurrences += 1
assert {e: sorted(ids) for e, ids in reverse.items()} == trace['reverse_endpoint_requirements']
assert len(reverse) == 8 and sum(map(len, reverse.values())) == occurrences == 56
for key in ('parent_trace', 'source_parent_register', 'evidence', 'ADR', 'CAPA', 'CAPA_validation'):
    item = trace[key]
    path = Path(item['path'])
    if not path.is_absolute():
        path = (root if str(path).startswith('docs/') else base) / path
    assert sha(path) == item['sha256'], key

verification = read(folder / 'verification.json')
assert verification['original_exec_session'] == 1503 and verification['original_exec_exit'] == 0
assert {r['phase']: (r['passed'], r['failed'], r['returncode']) for r in verification['phases']} == {
    'source': (3, 0, 0), 'wheel': (3, 0, 0)}
assert verification['production_sources_identical_to_startup_ownership_c']
assert verification['source_manifest_sha256'] == sha(folder / 'frozen-inputs.json')
assert verification['packaged_sources'] == 81
assert verification['auditor_sha256'] == sha(base / 'audit-runtime-pending-stop-20261019.py')
assert len(verification['root_receipts']) == len(verification['cases']) == 6
assert {(r['phase'], r['route']) for r in verification['cases']} == {
    (p, r) for p in ('source', 'wheel') for r in ('direct', 'registry', 'registry-view-loss')}
for item in verification['root_receipts'] + verification['cases']:
    assert sha(folder / item['path']) == item['sha256']
for item in verification['root_receipts']:
    facts = read(folder / item['path'])
    assert facts['root_removed'] and facts['workers_reaped']
    assert not (Path(facts['parent_path']) / facts['root_name']).exists()
for case in verification['cases']:
    assert case['primary_original_root_wait'] and case['creation_count'] == 1
    assert case['matching_result_retained'] and case['collection_absent']
    assert case['startup']['registered_helpers_reaped'] is None
    assert case['startup']['unacknowledged_births'] is None
    assert case['execution_succeeded'] is None and not case['cleanup_complete']

capa = read(base / trace['CAPA']['path'])
capa_check = read(base / trace['CAPA_validation']['path'])
assert len(capa['records']) == capa_check['records_validated'] == 26
assert len(capa['evidence']) == capa_check['evidence_bindings_verified'] == 139
assert capa_check['register_sha256'] == trace['CAPA']['sha256']
assert {r['capa_id'] for r in capa['records'] if r['state'] == 'UNRESOLVED'} == {
    'ML-CAPA-135', 'ML-CAPA-222', 'ML-CAPA-286', 'ML-CAPA-287', 'ML-CAPA-318'}
for key, item in capa['evidence'].items():
    path = root / item['path']
    if item['kind'] == 'file':
        digest = sha(path)
    else:
        text = path.read_text()
        digest = hashlib.sha256(text[text.index('\n' + item['start']) + 1:text.index('\n' + item['end'])].encode()).hexdigest()
    assert digest == item['sha256'], key
assert capa_check['effectiveness_demonstrated'] is False
assert capa_check['independent_cause_confirmation'] is False
assert capa_check['automatic_workflow_implemented'] is False

combined = trace['combined_regression']
assert combined['status'] == 'LIVE_NOT_TERMINAL'  # immutable trace snapshot only
assert combined['complete_failure_inventory'] is False
assert combined['original_exec_session'] == 53866 and combined['collected_per_phase'] == 1495
item = combined['provisional_counterevidence']
assert sha(base / item['path']) == item['sha256']
inputs = read(root / 'docs/engineering/maestro-lite/coverage-runtime-closure-inputs.json')
assert len(inputs['inputs']) == 8
assert all(sha(Path(item['path'])) == item['sha256'] for item in inputs['inputs'])
assert trace['selected_checks_passed_per_phase'] == 78 and trace['new_checks_passed_per_phase'] == 3
assert trace['open_findings'] == [135, 222, 286, 287, 318]
for key in ('stable_increment17', 'whole_platform_regression', 'full_M1_complete',
            'full_candidate_review_complete', 'source_parent_semantics_validated',
            'all_seven_phase3_tasks_complete', 'independent_CAPA_effectiveness',
            'accepted', 'merged', 'scientific_result'):
    assert trace[key] is False
assert trace['actual_M1_admissions'] == trace['actual_service_runtime_runs'] == 0
tasks = Path('/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/tasks.md')
assert tasks.read_text().count('- [ ] P3-T') == 7 and sha(trace_path) in tasks.read_text()
handoff = base / 'continuation-integrated-live-20261019.md'
assert sha(trace_path) in handoff.read_text()
products = [root / 'docs/engineering/maestro-lite/runtime-pending-stop.md',
            root / 'docs/engineering/maestro-lite/README.md', handoff, tasks]
result = dict(checker_sha256=sha(Path(__file__)), frozen_files_checked=len(manifest),
    unchanged_source_tree_files=118, unchanged_packaged_python_c_files=81, partial_requirement_rows=24, source_parent_rows=18,
    new_endpoints=8, endpoint_links=56, new_checks_per_phase=3, selected_checks_per_phase=78,
    actual_original_product_waits=6, owned_reservations_absent=6,
    unregistered_helper_unknowns_preserved=True, draft_input_bindings_checked=8,
    capa_records=26, capa_evidence_bindings=139, trace_sha256=sha(trace_path),
    combined_regression_state_is_historical_snapshot=True, full_regression_proven=False,
    work_product_hashes={str(p): sha(p) for p in products},
    actual_M1_admissions=0, stable_increment17=False, accepted=False, merged=False)
with (base / 'runtime-pending-stop-work-products-check-v2.json').open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(result))
