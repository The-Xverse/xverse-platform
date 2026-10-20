"""Extend exact bidirectional trace with selected public-intent/termination rows."""
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
folder = base/'composed-intent-termination-20261019b'
verified, frozen = read(folder/'verification.json'), read(folder/'frozen-inputs.json')
root = Path(read(folder/'running.json')['frozen_source_root'])
assert all(sha(root/n) == h == sha(candidate/n) for n, h in frozen.items())
assert verified['original_exec_exit'] == 0 and len(verified['cases']) == 12
assert len(verified['root_receipts']) == len(verified['wait_receipts']) == len(verified['snapshots']) == 12
assert sum(r['cleanup_complete'] for r in verified['cases']) == 6
parent = base/'composed-authority-partial-traceability-v2.json'
prior = read(parent)
def endpoint(path, name):
    tree = ast.parse((root/path).read_text())
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
    return dict(endpoint=path+'::'+name, line=node.lineno, file_sha256=frozen[path],
        frozen_manifest='composed-intent-termination-20261019b/frozen-inputs.json')
code = [endpoint('src/xverse/maestro/owner.py', '_persist_intent')]
code += [endpoint('src/xverse/maestro/run_broker.py', name) for name in ('stage', 'stop_owned')]
code += [endpoint('src/xverse/maestro/run_closure.py', 'close')]
test = 'tests/thesis_lite/maestro/test_composed_persistence_termination.py'
tests = [endpoint(test, name) for name in ('run_bootstrap_binary', 'binaries',
    'test_original_intent_frontier_loader_and_loss', 'test_original_termination_with_live_leader_descendant')]
native = 'tests/thesis_lite/maestro/catalog_workload_leader_descendant.c'
tests.append(dict(endpoint=native+'::main',
    line=next(i for i,line in enumerate((root/native).read_text().splitlines(),1) if line.startswith('int main(')),
    file_sha256=frozen[native], frozen_manifest='composed-intent-termination-20261019b/frozen-inputs.json'))
ids = ['ML-SR-'+str(n).zfill(3) for n in (5,6,9,10,11,12,13,16,17,18,19,20,23,24)]
requirements = copy.deepcopy(prior['requirements'])
reverse = copy.deepcopy(prior['reverse_endpoint_requirements'])
for row in requirements:
    assert not row['full_requirement_closure']
    if row['id'] in ids:
        row['component_deltas'].append(dict(maturity='selected_original_intent_and_termination_frontiers_verified',
            code=code, tests=tests, evidence=ref(folder/'verification.json'), full_requirement_closure=False,
            scope='Actual worker public append/flush and original pidfd loss before Stage; original STOP windows with admitted live leader+descendant and unrelated heartbeat. No full CP row, M1 or independent review claim.'))
for item in code+tests:
    reverse[item['endpoint']] = sorted(set(reverse.get(item['endpoint'],[]))|set(ids))
result = dict(schema_version=1, revision='ML3-AFFA17-2026-10-19-composed-intent-termination-v1',
    scope='Selected CP07/08/12 native frontiers; full increment17 remains open', parent_trace=ref(parent),
    requirements=requirements, source_parent_register=prior['source_parent_register'], reverse_endpoint_requirements=reverse,
    evidence=ref(folder/'verification.json'), original_failed_loader=ref(base/'composed-intent-termination-20261019a/verification.json'),
    native_retention=[ref(base/('composed-intent-termination-20261019'+s)/'native-retention.json') for s in ('a','b')],
    CAPA=ref(base/'capa-20261019-intent-termination/register.json'),
    CAPA_validation=ref(base/'capa-20261019-intent-termination/verification-recheck.json'),
    software_requirements_retained=24, source_parents_retained=18, scenario_pairs_retained=30,
    endpoint_obligations_retained=90, full_runtime_cases_retained=9,
    current_affected_counts=[dict(phase=p,passed=sum(r['passed'] for r in verified['phases'] if r['phase']==p),
        failed=sum(r['failed'] for r in verified['phases'] if r['phase']==p)) for p in ('source','wheel')],
    production_sources_unchanged=True, original_root_receipts=12, original_wait_receipts=12,
    source_links=verified['source_links'], normal_closed_public_copies=2,
    physical_cleanup_complete_contexts=6, workload_wait_unknown_contexts=6,
    CP07=dict(before_original_public_append=True, durable_start_intent_without_mirror=True, full_row_complete=False),
    CP08=dict(after_original_public_flush_return=True, worker_RPC_ACK_not_delivered=True,
        no_host_claim_or_native_ticket=True, full_row_complete=False),
    CP12=dict(live_leader_and_descendant=True, three_original_STOP_windows=True,
        cached_wait_preserved_after_storage_loss=True, full_row_complete=False),
    finding_dispositions={'255':'selected_remaining_branch_controls_verified',
        '256':'start_intent_fixture_selector_corrected_locally', '257':'bounded_same_session_review_only'},
    open_findings=[135,222], remaining_gates=prior['remaining_gates'],
    full_crash_matrix_complete=False, runtime_cases_fully_complete=False,
    source_parent_semantics_validated=False, all_seven_phase3_tasks_complete=False,
    full_source_wheel_scope_passed=False, full_M1_complete=False, whole_platform_regression=False,
    full_candidate_review_complete=False, stable_increment17=False, independent_CAPA_effectiveness=False,
    accepted=False, merged=False, canonical_note_edited=False, factory_run_created=False, scientific_result=False)
path = base/'composed-intent-termination-partial-traceability.json'
with path.open('x') as stream:
    json.dump(result, stream, indent=2); stream.write('\n')
print(json.dumps(dict(trace=ref(path), contexts=12, source_links=result['source_links'])))
