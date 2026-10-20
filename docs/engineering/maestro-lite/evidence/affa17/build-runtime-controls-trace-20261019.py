"""Retain startup correction, private controls and unresolved full-run failures."""
import ast
import copy
import hashlib
import json
from pathlib import Path

base=Path(__file__).resolve().parent;candidate=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
def ref(p):return dict(path=str(p.relative_to(base)),sha256=sha(p))
b='runtime-controls-20261019b';d='runtime-controls-diagnostic-20261019d'
manifests={n:read(base/n/'frozen-inputs.json') for n in (b,d)}
assert all(sha(candidate/n)==h for n,h in manifests[d].items())
assert {n:h for n,h in manifests[b].items() if n.startswith('src/')}=={n:h for n,h in manifests[d].items() if n.startswith('src/')}
prior=read(base/'runtime-entry-20261019c/frozen-inputs.json')
changed=[n for n,h in manifests[d].items() if n.startswith('src/') and prior[n]!=h]
assert changed==['src/xverse/maestro/runtime_entry.py']
vb=read(base/b/'verification-v2.json');vd=read(base/d/'verification-v2.json')
assert all(p['passed']==14 and p['returncode']==0 for p in vb['phases'] if p['cohort']=='runtime_startup_failures')
assert vd['counts']=={p:dict(passed=2,failed=0,errors=0) for p in ('source','wheel')}
def endpoint(path,name,folder):
    frozen_root=Path(read(base/folder/'running.json')['frozen_source_root'])
    tree=ast.parse((frozen_root/path).read_text());parts=name.split('.');scope=tree
    if len(parts)==2:scope=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==parts[0])
    node=next(n for n in scope.body if isinstance(n,ast.FunctionDef) and n.name==parts[-1])
    return dict(endpoint=path+'::'+name,line=node.lineno,file_sha256=manifests[folder][path],frozen_manifest=folder+'/frozen-inputs.json')
source='src/xverse/maestro/runtime_entry.py';tests='tests/thesis_lite/maestro/'
cleanup_code=[endpoint(source,n,d) for n in ('_OriginalRuntimeRun.start','_OriginalRuntimeRun.stop')]
control_code=[endpoint(source,n,d) for n in ('_OriginalRuntimeRegistry.reserve','_OriginalRuntimeRegistry._run',
    '_OriginalRuntimeRegistry.stop','_OriginalRuntimeRegistry.replace_controller',
    '_OriginalRuntimeRun.replace_controller','_OriginalRuntimeRun.controller_recovery_result')]
failure_tests=[endpoint(tests+'test_runtime_startup_failures.py',n,b) for n in (
    'test_constructor_conflicts_reject_before_process_or_C1','test_original_startup_failure_returns_primary_cleanup_without_fallback')]
control_tests=[endpoint(tests+'test_runtime_control_registry.py',n,b) for n in (
    'test_original_registry_rejects_reconstruction_loss_and_cross_registration',
    'test_original_registry_whole_run_replay_and_retained_collection','test_actual_original_registry_loss_stop_uses_only_retained_cleanup')]
recovery_test=endpoint(tests+'test_runtime_control_registry.py','test_actual_registry_controller_recovery_preserves_productive_original_run',d)
parent=base/'runtime-entry-partial-traceability.json';prior_trace=read(parent)
requirements=copy.deepcopy(prior_trace['requirements']);reverse=copy.deepcopy(prior_trace['reverse_endpoint_requirements'])
for row in requirements:
    assert not row['full_requirement_closure'];n=int(row['id'].removeprefix('ML-SR-'));deltas=[]
    if n in (9,10,11,12,13,18,20,23,24):
        deltas.append(dict(maturity='original_pin_startup_cleanup_correction_owned_verified',code=cleanup_code,tests=failure_tests,
            evidence=ref(base/b/'verification-v2.json'),full_requirement_closure=False,
            scope='14 constructor/helper-return/ordinary-alias failure controls per phase;12 primary startup results withzero fallback. No workloads, full constructor matrix or public admission claimed.'))
    if n in (6,11,12,14,18,22,23,24):
        deltas.append(dict(maturity='private_original_registry_controls_partial_with_counterevidence',code=control_code,tests=control_tests+[recovery_test],
            evidence=[ref(base/b/'verification-v2.json'),ref(base/d/'verification-v2.json')],full_requirement_closure=False,
            scope='Original private registry/cleanup-log controls and genuine productive replacement. Registry source8/wheel7+1 failure retained; subsequent2-case observed probes pass without closing286/287 or proving stability. Public approval/full matrices/regression remain open.'))
    for delta in deltas:
        row['component_deltas'].append(delta)
        for item in delta['code']+delta['tests']:reverse[item['endpoint']]=sorted(set(reverse.get(item['endpoint'],[]))|{row['id']})
result=dict(schema_version=1,revision='ML3-AFFA17-2026-10-19-runtime-controls-v1',parent_trace=ref(parent),
    requirements=requirements,source_parent_register=prior_trace['source_parent_register'],reverse_endpoint_requirements=reverse,
    evidence=ref(base/b/'verification-v2.json'),original_startup_failure=ref(base/'runtime-startup-faults-20261019a/verification-v2.json'),
    skipped_entry_regression=ref(base/'runtime-controls-20261019c/verification-v2.json'),
    diagnostic_probe=ref(base/d/'verification-v2.json'),rpc_observations=ref(base/d/'rpc-observation-summary.json'),
    original_auditor_failure=ref(base/'runtime-controls-audit-first-failure-20261019.json'),
    CAPA=ref(base/'capa-20261019-runtime-controls/register.json'),CAPA_validation=ref(base/'capa-20261019-runtime-controls/verification-recheck.json'),
    ADR=dict(path='docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0004.md',sha256=sha(candidate/'docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0004.md')),
    changed_production_sources=[dict(path=source,sha256=sha(candidate/source))],packaged_sources=80,all_79_other_production_sources_unchanged=True,
    original_failure_counts_per_phase=dict(passed=11,failed=3,errors=0),current_startup_checks_passed_per_phase=14,
    main_controls_counts=vb['counts'],main_controls_case_counts_per_phase=dict(source=dict(passed=8,failed=0),wheel=dict(passed=7,failed=1)),
    diagnostic_counts=vd['counts'],diagnostic_success_does_not_resolve_original_failures=True,
    public_entry_implementation=dict(private_original_run_registry=True,private_controller_recovery_controls=True,
        independent_original_cleanup_log=True,public_approved_admission=False,public_start=False),
    software_requirements_retained=24,source_parents_retained=18,scenario_pairs_retained=30,endpoint_obligations_retained=90,full_runtime_cases_retained=9,
    open_findings=[135,222,286,287],remaining_gates=prior_trace['remaining_gates'],
    full_constructor_startup_failure_matrix=False,full_active_restart_recovery_entry_matrix=False,
    full_crash_matrix_complete=False,runtime_cases_fully_complete=False,source_parent_semantics_validated=False,
    all_seven_phase3_tasks_complete=False,full_source_wheel_scope_passed=False,full_M1_complete=False,
    whole_platform_regression=False,full_candidate_review_complete=False,stable_increment17=False,
    independent_CAPA_effectiveness=False,accepted=False,merged=False,actual_M1_admissions=0,
    canonical_note_edited=False,factory_run_created=False,scientific_result=False)
path=base/'runtime-controls-partial-traceability.json'
with path.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(trace=ref(path),startup_checks_passed_per_phase=14,unresolved=result['open_findings'])))
