"""Bind the reproduced cleanup repair and exact affected native regression."""
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
    return dict(path=str(p.relative_to(base)),sha256=sha(p))
folder = base/'composed-issuer-loss-20261019c'
verified,frozen = read(folder/'verification.json'),read(folder/'frozen-inputs.json')
root = Path(read(folder/'running.json')['frozen_source_root'])
assert all(sha(root/n) == h == sha(candidate/n) for n,h in frozen.items())
assert verified['counts'] == {p:dict(passed=54,failed=0,errors=0) for p in ('source','wheel')}
assert len(verified['root_receipts']) == len(verified['wait_receipts']) == len(verified['snapshots']) == 108
parent = base/'composed-intent-termination-partial-traceability.json'
prior = read(parent)
def endpoint(path,name):
    tree = ast.parse((root/path).read_text())
    if '.' in name:
        owner,method = name.split('.')
        scope = next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==owner)
        node = next(n for n in scope.body if isinstance(n,ast.FunctionDef) and n.name==method)
    else:
        node = next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
    return dict(endpoint=path+'::'+name,line=node.lineno,file_sha256=frozen[path],
        frozen_manifest='composed-issuer-loss-20261019c/frozen-inputs.json')
code = [endpoint('src/xverse/maestro/run_broker.py',name) for name in
    ('RunBroker._cleanup_context','RunBroker._holder','RunBroker.cancel','RunUnitIssuer.cancel')]
code += [endpoint('src/xverse/maestro/run_closure.py','RunClosure.close')]
test = 'tests/thesis_lite/maestro/test_composed_issuer_loss.py'
tests = [endpoint(test,name) for name in
    ('test_original_registry_loss_denies_adoption_but_preserves_cancellation_and_cleanup',
     'test_original_queued_request_is_dead_before_exact_fallback_release')]
# Every test module in the frozen collection remains explicitly identified by
# actual driver commands, rather than inferred from a count.
regression_files = sorted({r['cohort'] for p in folder.glob('*-receipt.json')
    if (r:=read(p)).get('cohort')})
assert len(regression_files) == 7
requirements = copy.deepcopy(prior['requirements'])
reverse = copy.deepcopy(prior['reverse_endpoint_requirements'])
ids = ['ML-SR-'+str(n).zfill(3) for n in (9,10,11,12,13,14,18,19,20,23,24)]
for row in requirements:
    assert not row['full_requirement_closure']
    if row['id'] in ids:
        row['component_deltas'].append(dict(maturity='original_cleanup_context_repair_verified_locally',
            code=code,tests=tests,evidence=ref(folder/'verification.json'),full_requirement_closure=False,
            scope='Original cleanup-only fencing survives ordinary registry loss; original descriptive inventory and unknown waits, no adoption; actual queued authority death before exact C1 release.'))
for item in code+tests:
    reverse[item['endpoint']] = sorted(set(reverse.get(item['endpoint'],[]))|set(ids))
baseline = read(base/'composed-issuer-loss-20261019a/frozen-inputs.json')
changes = [dict(path=p,previous_sha256=baseline[p],current_sha256=frozen[p]) for p in verified['changed_production_sources']]
result = dict(schema_version=1,revision='ML3-AFFA17-2026-10-19-issuer-loss-v1',
    scope='Original cleanup-context repair and54 affected checks per phase; full17 remains open',
    parent_trace=ref(parent),requirements=requirements,source_parent_register=prior['source_parent_register'],
    reverse_endpoint_requirements=reverse,evidence=ref(folder/'verification.json'),
    original_red=ref(base/'composed-issuer-loss-20261019a/verification.json'),
    original_counterexample=ref(base/'composed-issuer-loss-20261019a/counterexample-verification.json'),
    partial_repair_and_harness_failure=ref(base/'composed-issuer-loss-20261019b/verification.json'),
    native_retention=[ref(base/('composed-issuer-loss-20261019'+s)/'native-retention.json') for s in ('a','b','c')],
    CAPA=ref(base/'capa-20261019-issuer-loss/register.json'),
    CAPA_validation=ref(base/'capa-20261019-issuer-loss/verification-recheck.json'),
    changed_production_sources=changes,
    historical_component_deltas_remain_exact_old_source_evidence=True,
    all_other_packaged_sources_unchanged=74,packaged_sources=76,
    regression_module_cohorts=regression_files,current_affected_counts=verified['counts'],
    software_requirements_retained=24,source_parents_retained=18,scenario_pairs_retained=30,
    endpoint_obligations_retained=90,full_runtime_cases_retained=9,
    original_root_receipts=108,original_wait_receipts=108,source_links=verified['source_links'],
    externally_complete_closed_public_copies=len(verified['retained_closed_public']),
    normal_host_ACK_not_inferred_from_closed_copy=True,
    finding_dispositions={'258':'original_risks_reproduced','259':'local_original_cleanup_repair_verified',
        '260':'complete_cancel_chain_and_isolated_module_harness_verified','261':'bounded_same_session_review_only'},
    open_findings=[135,222],remaining_gates=prior['remaining_gates'],
    full_crash_matrix_complete=False,runtime_cases_fully_complete=False,
    source_parent_semantics_validated=False,all_seven_phase3_tasks_complete=False,
    full_source_wheel_scope_passed=False,full_M1_complete=False,whole_platform_regression=False,
    full_candidate_review_complete=False,stable_increment17=False,independent_CAPA_effectiveness=False,
    accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False,scientific_result=False)
path = base/'issuer-loss-partial-traceability.json'
with path.open('x') as stream:
    json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(trace=ref(path),counts=result['current_affected_counts'],contexts=108)))
