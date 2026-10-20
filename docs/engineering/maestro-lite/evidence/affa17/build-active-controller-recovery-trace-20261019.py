"""Trace the measured active-recovery component, retaining full17 gates."""
import ast
import copy
import hashlib
import json
from pathlib import Path

base=Path(__file__).resolve().parent;candidate=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
prior=base/'active-transitive-verified-scope-traceability.json'
trace=copy.deepcopy(read(prior));bundle=base/'active-controller-recovery-20261019d'
proof=read(bundle/'verification.json');frozen=read(bundle/'frozen-inputs.json')
assert proof['component_scope_passed'] and proof['independent_closed_complete']==18
assert len(proof['cases'])==20 and not proof['legacy_reader_gaps']
assert [p['passed'] for p in proof['phases']]==[94,94]
assert all(sha(candidate/path)==value for path,value in frozen.items())
def endpoint(file,symbol):
    nodes=ast.parse((candidate/file).read_text()).body
    for name in symbol.split('.'):
        node=next(n for n in nodes if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
        nodes=node.body
    assert sha(candidate/file)==frozen[file]
    return dict(endpoint=file+'::'+symbol,line=node.lineno,file_sha256=frozen[file],
                frozen_manifest='active-controller-recovery-20261019d/frozen-inputs.json')
def qualified(file,prefix,names):return [endpoint(file,prefix+name) for name in names]
dispatcher='src/xverse/maestro/dispatcher.py'
native_test=endpoint('tests/thesis_lite/maestro/test_active_controller_recovery.py',
    'test_original_active_replacement_retains_owner_writer_and_productive_access')
evidence=dict(path='active-controller-recovery-20261019d/verification.json',sha256=sha(bundle/'verification.json'))
groups=[
 ('explicit_original_coordinator_recovery',[4,9,11,14,22,24],
  qualified(dispatcher,'FiniteDispatcher.',('replace_controller','controller_recovery_result',
      '_validate_controller_borrow','_commit_controller_view','_drain_controller_recovery','_close_restarts','run')),
  [native_test]),
 ('sealed_recovery_and_original_service_bounds',[4,9,10,14,24],
  qualified(dispatcher,'FiniteDispatcher.',('__init__','_holder','_end','_service','_renew_service'))+
  qualified('src/xverse/maestro/schedule_plan.py','',('admit_schedule','decode_schedule')),
  [native_test,endpoint('tests/thesis_lite/maestro/test_schedule_plan.py',
      'test_recovery_bound_is_sealed_and_old_action_admission_remains_version4'),
   endpoint('tests/thesis_lite/maestro/test_schedule_plan.py','test_recovery_bound_rejects_invalid_or_unusable_caps'),
   endpoint('tests/thesis_lite/maestro/test_service_order.py','test_due_services_keep_original_scan_budget_and_earliest_deadlines')]),
 ('durable_current_and_released_generation_reconciliation',[6,12,14,16,23,24],
  qualified('src/xverse/maestro/recovery.py','IssuerRecovery.',('__init__','_holder','_query','reconcile'))+
  qualified('src/xverse/maestro/recovery.py','',('validate_snapshot',))+
  qualified('src/xverse/maestro/recovery_evidence.py','',('snapshot',))+
  qualified('src/xverse/maestro/controller.py','ControllerSession.',('reconcile',))+
  qualified('src/xverse/maestro/controller.py','',('admit_controller',)),[native_test]),
 ('genuine_cleanup_only_view_and_original_retirement',[7,8,9,10,12,13,14,18,19,22,23,24],
  qualified('src/xverse/maestro/providers.py','ProcessReadiness.',('__init__','_holder','_check','bind')),
  [native_test])]
for name,numbers,code,tests in groups:
    selected={f'ML-SR-{n:03}' for n in numbers}
    delta=dict(maturity='partial_verified_'+name,code=code,tests=tests,evidence=evidence,
               full_requirement_closure=False,scope='Ten declared owned native cases, same source/wheel production bytes; no universal recovery/timing claim')
    for requirement in trace['requirements']:
        assert requirement['full_requirement_closure'] is False
        if requirement['id'] in selected:requirement['component_deltas'].append(copy.deepcopy(delta))
    for item in code+tests:
        previous=trace['reverse_endpoint_requirements'].get(item['endpoint'],[])
        trace['reverse_endpoint_requirements'][item['endpoint']]=sorted(set(previous)|selected)
trace.update(revision='ML3-AFFA17-2026-10-19-active-controller-recovery-v5-partial',
    scope='Explicit productive active controller replacement component verified, including generations and heartbeat race; full17/stability/complete recovery matrix remain open',
    prior_component_trace=dict(path=str(prior),sha256=sha(prior)),evidence=evidence,
    current_affected_counts=proof['phases'],productive_controller_recovery_component_verified=True,
    productive_controller_recovery=False,independent_closed_recomputations=18,
    retained_closed_public_roots=len(proof['retained_closed_public']),
    open_findings=[135,213,222],old_fixed_active_end_failures_not_waived=True,
    full_selected_increment_scope_passed=False)
for path in (base/'active-controller-recovery-20261019a/verification.json',
             base/'active-controller-recovery-20261019b/verification.json',
             base/'active-controller-recovery-20261019c/verification.json',
             base/'active-controller-recovery-race-red-20261019a/race-red-verification.json'):
    trace['additional_evidence'].append(dict(path=str(path.relative_to(base)),sha256=sha(path)))
assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18
assert trace['scenario_pairs_retained']==30 and trace['endpoint_obligations_retained']==90
assert all(trace[key] is False for key in ('full_source_wheel_scope_passed','full_M1_complete',
    'full_candidate_review_complete','all_seven_phase3_tasks_complete','U7_U8_complete',
    'stable_increment17','accepted','merged','canonical_note_edited','factory_run_created'))
target=base/'active-controller-recovery-partial-traceability.json'
with target.open('x') as f:json.dump(trace,f,indent=2);f.write('\n')
print(json.dumps(dict(requirements=24,source_parents=18,pairs=30,endpoints=90,
                     groups=len(groups),full17=False,trace_sha256=sha(target))))
