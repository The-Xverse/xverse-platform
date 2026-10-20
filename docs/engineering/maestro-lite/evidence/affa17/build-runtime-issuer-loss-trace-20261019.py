"""Bind the partial whole-entry repair to exact existing verification, no execution."""
import ast
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
root = base.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
parent_path = base / 'runtime-pending-stop-partial-traceability.json'
parent = read(parent_path)
manifests = {s: read(base / f'runtime-issuer-loss-20261019{s}/frozen-inputs.json') for s in 'abc'}
assert manifests['b'] == manifests['c']
assert all(sha(root / n) == h for n, h in manifests['b'].items())
production = {n: h for n, h in manifests['b'].items() if n.startswith('src/') and n.endswith(('.py', '.c'))}
assert len(production) == 81
assert [n for n, h in production.items() if manifests['a'][n] != h] == ['src/xverse/maestro/run_closure.py']
verifications = {s: read(base / f'runtime-issuer-loss-20261019{s}/verification.json') for s in 'abc'}
assert verifications['a']['external_fallback_cases'] == 4
assert verifications['b']['primary_cleanup_cases'] == 4 and verifications['b']['external_fallback_cases'] == 0
assert verifications['b']['counts'] == {'source':dict(passed=79,failed=0,errors=0), 'wheel':dict(passed=78,failed=1,errors=1)}
assert verifications['c']['counts'] == {p:dict(passed=6,failed=0,errors=0) for p in ('source','wheel')}
folder = base / 'capa-20261019-runtime-issuer-loss-v2'
capa, capa_check = read(folder / 'register.json'), read(folder / 'verification-recheck.json')
preservation = read(folder / 'parent-preservation.json')
assert capa_check['register_sha256'] == preservation['register_sha256'] == sha(folder / 'register.json')
assert preservation['parent_preserved'] and preservation['parent_evidence_bindings_checked'] == 170
assert len(capa['records']) == 37 and len(capa['evidence']) == 198
for s, verification in verifications.items():
    out = base / f'runtime-issuer-loss-20261019{s}'
    assert verification['frozen_manifest_sha256'] == sha(out / 'frozen-inputs.json')
    for item in verification['root_receipts'] + verification['whole_entry_cases']:
        assert sha(out / item['path']) == item['sha256']

endpoints = {
    'closure': 'src/xverse/maestro/run_closure.py::RunClosure.__init__',
    'context': 'src/xverse/maestro/run_broker.py::RunBroker._cleanup_context',
    'start': 'src/xverse/maestro/runtime_entry.py::_OriginalRuntimeRun.start',
    'stop': 'src/xverse/maestro/runtime_entry.py::_OriginalRuntimeRun.stop',
    'registry-start': 'src/xverse/maestro/runtime_entry.py::_OriginalRuntimeRegistry.start',
    'registry-stop': 'src/xverse/maestro/runtime_entry.py::_OriginalRuntimeRegistry.stop',
    'registry-collect': 'src/xverse/maestro/runtime_entry.py::_OriginalRuntimeRegistry.collect',
    'test': 'tests/thesis_lite/maestro/test_runtime_issuer_loss.py::test_original_whole_start_retains_primary_cleanup_after_issuer_loss',
}
bindings = {}
for key, endpoint in endpoints.items():
    file, name = endpoint.split('::')
    scope = ast.parse((root / file).read_text())
    for part in name.split('.'):
        scope = next(n for n in scope.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name == part)
    bindings[key] = dict(endpoint=endpoint, line=scope.lineno, file_sha256=sha(root / file),
        frozen_manifest='runtime-issuer-loss-20261019b/frozen-inputs.json')

allocation = {
    'ML-SR-011': ['stop','registry-stop','context','closure'],
    'ML-SR-012': ['context','closure'],
    'ML-SR-013': ['closure','start'],
    'ML-SR-019': ['stop','context','closure'],
    'ML-SR-020': ['start','closure'],
    'ML-SR-022': ['start','registry-start','registry-collect'],
    'ML-SR-023': ['closure'],
}
evidence = [dict(path=f'runtime-issuer-loss-20261019{s}/verification.json',
    sha256=sha(base / f'runtime-issuer-loss-20261019{s}/verification.json')) for s in 'abc']
requirements, reverse = [], {}
for old in parent['requirements']:
    row = dict(id=old['id'], feature_parents=old['feature_parents'],
        inherited_status=old['inherited_status'], full_requirement_closure=False,
        prior_component_dispositions='inherit exact parent_trace; original claims remain revision-bound',
        component_deltas=[])
    if old['id'] in allocation:
        keys = allocation[old['id']]
        row['component_deltas'].append(dict(maturity='partial_original_whole_entry_issuer_loss_cleanup',
            scope='Original Stage-before-handle and post-release issuer loss; primary cleanup, strict ordinary rejection, copied-broker denial, original waits, incomplete evidence, sentinel and retained replay. Selected regression still has timeout/disposal counterevidence.',
            code=[bindings[k] for k in keys], tests=[bindings['test']], evidence=evidence,
            full_requirement_closure=False))
        for key in [*keys, 'test']:
            reverse.setdefault(bindings[key]['endpoint'], []).append(old['id'])
    requirements.append(row)
assert len(requirements) == 24 and len(reverse) == 8 and sum(map(len, reverse.values())) == 24
inputs = read(root / 'docs/engineering/maestro-lite/coverage-runtime-closure-inputs.json')
assert len(inputs['inputs']) == 8 and all(sha(Path(i['path'])) == i['sha256'] for i in inputs['inputs'])
result = dict(schema_version=1, revision='ML3-AFFA17-2026-10-19-runtime-issuer-loss-v1',
    parent_trace=dict(path=parent_path.name,sha256=sha(parent_path)), requirements=requirements,
    source_parent_register=parent['source_parent_register'], reverse_endpoint_requirements=reverse,
    evidence=evidence, ADR=dict(path='docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0009.md',
        sha256=sha(root / 'docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0009.md')),
    CAPA=dict(path=str((folder/'register.json').relative_to(base)),sha256=sha(folder/'register.json')),
    CAPA_validation=dict(path=str((folder/'verification-recheck.json').relative_to(base)),sha256=sha(folder/'verification-recheck.json')),
    CAPA_parent_preservation=dict(path=str((folder/'parent-preservation.json').relative_to(base)),sha256=sha(folder/'parent-preservation.json')),
    original_new_failures_per_phase=2,new_controls_passed_per_phase=2,
    selected_affected_counts={'source':dict(passed=85,failed=0,errors=0),'wheel':dict(passed=84,failed=1,errors=1)},
    selected_scope_is_disjoint_b_plus_missing_c=True, selected_affected_scope_passed=False,
    packaged_python_c_files=81,changed_packaged_sources=['src/xverse/maestro/run_closure.py'],
    other_packaged_sources_unchanged=80, current_recorded_roots_absent=sum(len(verifications[s]['root_receipts']) for s in 'bc'),
    original_red_recorded_roots_absent=len(verifications['a']['root_receipts']),
    current_source_links=sum(verifications[s]['source_links'] for s in 'bc'),
    source_parents_retained=18,scenario_pairs_retained=30,endpoint_obligations_retained=90,full_runtime_cases_retained=9,
    open_findings=[135,222,286,287,318,324,330,331,332,337,338],
    remaining_gates=parent['remaining_gates']+['storage disposal/partial-disposal counterevidence338','current selected regression337'],
    source_parent_semantics_validated=False,actual_M1_admissions=0,actual_service_runtime_runs=0,
    independent_CAPA_effectiveness=False,all_seven_phase3_tasks_complete=False,
    full_candidate_review_complete=False,full_M1_complete=False,whole_platform_regression=False,
    full_maestro_regression_passed=False,stable_increment17=False,accepted=False,merged=False,scientific_result=False)
with (base/'runtime-issuer-loss-partial-traceability.json').open('x') as stream:
    json.dump(result,stream,indent=2)
    stream.write('\n')
print(json.dumps(dict(requirement_rows=24,endpoints=8,links=24,
    trace_sha256=sha(base/'runtime-issuer-loss-partial-traceability.json'),
    selected_counts=result['selected_affected_counts'],current_roots=result['current_recorded_roots_absent'],
    source_links=result['current_source_links'],full_requirement_closure=False)))
