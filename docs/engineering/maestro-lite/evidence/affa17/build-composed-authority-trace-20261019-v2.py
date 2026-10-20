"""Bind selected composed controls without closing original requirements/cases."""
import ast
import copy
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
candidate = base.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
def ref(p):
    return dict(path=str(p.relative_to(base)), sha256=sha(p))
folder = base/'composed-authority-20261019c'
verified, frozen = read(folder/'verification.json'), read(folder/'frozen-inputs.json')
root = Path(read(folder/'running.json')['frozen_source_root'])
assert all(sha(root/n) == h == sha(candidate/n) for n, h in frozen.items())
assert verified['original_exec_exit'] == 0 and len(verified['cases']) == 18
assert len(verified['root_receipts']) == len(verified['wait_receipts']) == len(verified['snapshots']) == 18
assert sum(r['cleanup_complete'] for r in verified['cases']) == 4
parent = base/'native-writer-stream-partial-traceability.json'
prior = read(parent)
def endpoint(path, name):
    tree = ast.parse((root/path).read_text())
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
    return dict(endpoint=path+'::'+name, line=node.lineno, file_sha256=frozen[path],
        frozen_manifest='composed-authority-20261019c/frozen-inputs.json')
code = [endpoint('src/xverse/maestro/run_broker.py', name) for name in ('stage', 'release', 'cancel')]
code += [endpoint('src/xverse/maestro/run_closure.py', 'close')]
test_path = 'tests/thesis_lite/maestro/test_composed_authority_interruptions.py'
tests = [endpoint(test_path, name) for name in ('test_atomic_release_cancel_stage',
    'test_pre_handle_crash_survival', 'execute', 'instrument', 'sentinel')]
native = 'tests/thesis_lite/maestro/unrelated_heartbeat_fixture.c'
tests.append(dict(endpoint=native+'::main', line=next(i for i,line in enumerate((root/native).read_text().splitlines(), 1) if line.startswith('int main(')), file_sha256=frozen[native],
    frozen_manifest='composed-authority-20261019c/frozen-inputs.json'))
ids = ['ML-SR-'+str(n).zfill(3) for n in (9, 10, 11, 12, 13, 18, 19, 20, 23, 24)]
requirements = copy.deepcopy(prior['requirements'])
reverse = copy.deepcopy(prior['reverse_endpoint_requirements'])
for row in requirements:
    assert not row['full_requirement_closure']
    if row['id'] in ids:
        row['component_deltas'].append(dict(maturity='selected_composed_native_interruptions_verified',
            code=code, tests=tests, evidence=ref(folder/'verification.json'), full_requirement_closure=False,
            scope='Original dispatcher/terminal path; selected Stage/Release/Cancel/issuance windows and original helper loss, exact C1 cleanup with active unrelated heartbeat and genuine unknown waits.'))
for item in code+tests:
    reverse[item['endpoint']] = sorted(set(reverse.get(item['endpoint'], [])) | set(ids))
table = Path('/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/engineering/successors/ML-DESIGN-2026-10-03-v2/authority-crash-tables.json')
result = dict(schema_version=1, revision='ML3-AFFA17-2026-10-19-composed-authority-v2',
    scope='Selected deterministic composed authority interruptions; full selected increment17 remains open',
    parent_trace=ref(parent), supersedes_trace=ref(base/'composed-authority-partial-traceability.json'), requirements=requirements, source_parent_register=prior['source_parent_register'],
    reverse_endpoint_requirements=reverse, evidence=ref(folder/'verification.json'),
    failed_observations=[ref(base/('composed-authority-20261019'+s)/'verification.json') for s in ('a', 'b')],
    native_retention=[ref(base/('composed-authority-20261019'+s)/'native-retention.json') for s in ('a', 'b', 'c')],
    CAPA=ref(base/'capa-20261019-composed-authority/register.json'),
    CAPA_validation=ref(base/'capa-20261019-composed-authority/verification-recheck.json'),
    independent_expected_table=dict(path=str(table), sha256=sha(table), maturity='DRAFT',
        inspected_before_implementation_finding=249, digest_observation='post_execution; not pre-execution custody proof'),
    software_requirements_retained=24, source_parents_retained=18, scenario_pairs_retained=30,
    endpoint_obligations_retained=90, full_runtime_cases_retained=9,
    current_affected_counts=verified['phases'], production_sources_unchanged=True,
    original_root_receipts=18, original_wait_receipts=18, source_links=verified['source_links'],
    physical_cleanup_complete_contexts=4, workload_wait_unknown_contexts=14,
    selected_full_runtime_case_dispositions={
        'test_atomic_release_cancel_stage': 'PARTIAL: five selected original v6 interleavings, source/wheel',
        'test_pre_handle_crash_survival': 'PARTIAL: four selected original helper-loss windows, source/wheel'},
    finding_dispositions={'249': 'selected_composed_gap_controls_verified', '250': 'fixture_observation_corrected_locally',
        '251': 'queued_ACK_and_birth_observation_expectations_corrected_locally',
        '252': 'auditor_validates_exact_missing_normal_mirror_set', '253': 'bounded_same_session_review_only'},
    open_findings=[135, 222], remaining_gates=prior['remaining_gates'],
    full_crash_matrix_complete=False, runtime_cases_fully_complete=False,
    source_parent_semantics_validated=False, all_seven_phase3_tasks_complete=False,
    full_source_wheel_scope_passed=False, full_M1_complete=False, whole_platform_regression=False,
    full_candidate_review_complete=False, stable_increment17=False, independent_CAPA_effectiveness=False,
    accepted=False, merged=False, canonical_note_edited=False, factory_run_created=False, scientific_result=False)
assert len(requirements) == 24
path = base/'composed-authority-partial-traceability-v2.json'
with path.open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(trace=ref(path), source_links=result['source_links'], contexts=18)))
