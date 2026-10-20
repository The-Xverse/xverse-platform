"""Create a successor partial trace without rewriting historical verification."""
import ast
import copy
import hashlib
import json
from pathlib import Path

base=Path(__file__).resolve().parent
candidate=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
prior=base/'active-restart-partial-traceability.json'
trace=copy.deepcopy(read(prior))
bundle=base/'active-transitive-20261019d'
proof=read(bundle/'verification.json')
frozen=read(bundle/'frozen-inputs.json')
assert all(sha(candidate/name)==value for name,value in frozen.items())
assert proof['independent_closed_complete']==6
assert len(proof['cases'])==8 and proof['component_scope_passed'] is False
assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18

def endpoint(file,symbol):
    tree=ast.parse((candidate/file).read_text())
    nodes=tree.body
    for part in symbol.split('.'):
        node=next(n for n in nodes if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==part)
        nodes=getattr(node,'body',[])
    assert sha(candidate/file)==frozen[file]
    return dict(endpoint=file+'::'+symbol,line=node.lineno,file_sha256=frozen[file],
                frozen_manifest='active-transitive-20261019d/frozen-inputs.json')

methods=('restart_many','restart','restart_result','_restartable','_quiesce_restart_unit',
         '_restart_unit','_drain_restart','_quiesce_finished_restarts','_end',
         '_service','_renew_service','_statement','_effect','run')
code=[endpoint('src/xverse/maestro/dispatcher.py','FiniteDispatcher.'+name) for name in methods]
code += [endpoint('src/xverse/maestro/schedule_plan.py',name) for name in ('admit_schedule','decode_schedule')]
tests=[endpoint('tests/thesis_lite/maestro/test_active_transitive_restart.py',
                'test_original_transitive_cohort_retains_unrelated_and_all_generations'),
       endpoint('tests/thesis_lite/maestro/test_schedule_plan.py',
                'test_action_bounds_are_rederived_from_original_catalog_and_old_versions_stay_fixed'),
       endpoint('tests/thesis_lite/maestro/test_schedule_plan.py','test_action_timeout_mode_requires_explicit_boolean'),
       endpoint('tests/thesis_lite/maestro/test_service_order.py',
                'test_due_services_keep_original_scan_budget_and_earliest_deadlines')]
evidence=dict(path='active-transitive-20261019d/verification.json',sha256=sha(bundle/'verification.json'))
selected={f'ML-SR-{number:03}' for number in (4,6,7,8,9,10,11,12,13,16,17,18,19,23,24)}
delta=dict(maturity='partial_original_v4_transitive_restart_and_service_order',code=code,tests=tests,
           evidence=evidence,full_requirement_closure=False,
           scope='Eight cohort controls verified; six normal closed public recomputations. Overall affected suite still fails one old v3 fixed-active-end teardown.')
for requirement in trace['requirements']:
    assert requirement['full_requirement_closure'] is False
    if requirement['id'] in selected:
        requirement['component_deltas'].append(copy.deepcopy(delta))
for item in code+tests:
    old=trace['reverse_endpoint_requirements'].get(item['endpoint'],[])
    trace['reverse_endpoint_requirements'][item['endpoint']]=sorted(set(old)|selected)
trace.update(revision='ML3-AFFA17-2026-10-19-active-transitive-v4-partial',
    scope='Explicit transitive active restart component verified; full17, old fixed-active-end stability and productive controller recovery incomplete',
    prior_component_trace=dict(path=str(prior),sha256=sha(prior)),evidence=evidence,
    transitive_active_restart_component_verified=True,transitive_active_restart=False,
    active_restart_affected_scope_passed=False,full_selected_increment_scope_passed=False,
    current_affected_counts=proof['phases'],independent_closed_recomputations=6,
    retained_closed_public_roots=len(proof['retained_closed_public']),
    open_findings=[135,213,222],finding_222_is_not_waived=True,
    inherited_claims_apply_only_to_their_exact_frozen_inputs=True,
    current_thesis_head='904e8fc1e279ab84e3eefa9e80fba61926d43bba',
    stable_platform_parent='46e0ebfd332dd833322d764191a7cfe1e008bec1')
for directory in ('active-transitive-20261019b','active-transitive-20261019c'):
    path=base/directory/'verification.json'
    trace['additional_evidence'].append(dict(path=str(path.relative_to(base)),sha256=sha(path)))
assert all(trace[key] is False for key in ('full_source_wheel_scope_passed','full_M1_complete',
    'full_candidate_review_complete','all_seven_phase3_tasks_complete','U7_U8_complete',
    'stable_increment17','accepted','merged','canonical_note_edited','factory_run_created'))
target=base/'active-transitive-partial-traceability.json'
with target.open('x') as stream:json.dump(trace,stream,indent=2);stream.write('\n')
print(json.dumps(dict(requirements=24,source_parents=18,pairs=trace['scenario_pairs_retained'],
                     endpoints=trace['endpoint_obligations_retained'],new_endpoints=len(code)+len(tests),
                     full17=False,trace_sha256=sha(target))))
