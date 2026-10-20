"""Trace exact current b evidence/c composition without hiding either failed run."""
import ast
import copy
import hashlib
import json
from pathlib import Path

base=Path(__file__).resolve().parent;candidate=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
def ref(p):return dict(path=str(p.relative_to(base)),sha256=sha(p))
names=('runtime-entry-20261019b','runtime-entry-20261019c')
manifests={n:read(base/n/'frozen-inputs.json') for n in names}
b,c=(read(base/n/'verification.json') for n in names)
assert all(sha(candidate/n)==h for n,h in manifests[names[1]].items())
assert {n:h for n,h in manifests[names[0]].items() if n.startswith('src/')}=={n:h for n,h in manifests[names[1]].items() if n.startswith('src/')}
selected=[p for p in b['phases'] if p['cohort'] in ('runtime_evidence','runtime_evidence_window')]
assert len(selected)==4 and all(p['returncode']==0 for p in selected)
assert all(sum(p['passed'] for p in selected if p['phase']==phase)==19 for phase in ('source','wheel'))
assert c['counts']=={p:dict(passed=67,failed=0,errors=0) for p in ('source','wheel')}
parent=base/'bootstrap-launcher-partial-traceability.json';prior=read(parent)
code_files={'evidence':'src/xverse/maestro/runtime_evidence.py','entry':'src/xverse/maestro/runtime_entry.py'}
test_files={'evidence':'tests/thesis_lite/maestro/test_runtime_evidence.py','window':'tests/thesis_lite/maestro/test_runtime_evidence_window.py','entry':'tests/thesis_lite/maestro/test_runtime_entry.py'}
def endpoint(path,name):
    folder=names[0] if path in (test_files['evidence'],test_files['window']) else names[1]
    assert manifests[folder][path]==sha(candidate/path)
    tree=ast.parse((candidate/path).read_text());scope=tree;parts=name.split('.')
    if len(parts)==2:scope=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==parts[0])
    node=next(n for n in scope.body if isinstance(n,ast.FunctionDef) and n.name==parts[-1])
    return dict(endpoint=path+'::'+name,line=node.lineno,file_sha256=sha(candidate/path),frozen_manifest=folder+'/frozen-inputs.json')
code=[endpoint(code_files['evidence'],n) for n in ('_file','verify_runtime_evidence')]
entry=[endpoint(code_files['entry'],n) for n in ('_OriginalRuntimeRun.start','_OriginalRuntimeRun.stop','_OriginalRuntimeRun.collect',
    '_OriginalRuntimeRun._validate_scope','RuntimeResult.execution_succeeded','RuntimeResult.cleanup_complete')]
checks=[endpoint(test_files['evidence'],n) for n in ('test_actual_file_reads_and_current_original_host_checks_are_inert',
    'test_changed_original_files_reject_without_trusting_metadata_alone','test_bounded_actual_receipt_inputs_reject',
    'test_change_during_actual_pread_rejects','test_current_host_and_original_parent_are_required')]
window=endpoint(test_files['window'],'test_actual_start_window_expiring_during_receipt_read_rejects')
entry_tests=[endpoint(test_files['entry'],n) for n in ('test_whole_original_start_returns_after_actual_terminal_and_helper_closure',
    'test_changed_ends_reject_before_any_creation_or_latch_mutation',
    'test_original_stop_repeats_and_start_conflict_do_not_need_start_lock','test_actual_concurrent_stop_preserves_original_cleanup_facts')]
requirements=copy.deepcopy(prior['requirements']);reverse=copy.deepcopy(prior['reverse_endpoint_requirements'])
for row in requirements:
    assert not row['full_requirement_closure']
    n=int(row['id'].removeprefix('ML-SR-'));deltas=[]
    if n in (1,9,10,23,24):
        deltas.append(dict(maturity='actual_external_file_bytes_current_host_checks_inert_verified',code=code,tests=checks+[window],
            evidence=ref(base/names[0]/'verification.json'),full_requirement_closure=False,
            scope='Exact bytes of externally pinned approval/facility and nine receipt files, current original empty C1/kernel/self-pidfd and post-I/O clock windows only. All positive receipt vectors are SYNTHETIC/INERT; no receipt semantics, approval authentication or execution authority.'))
    if n in (9,10,11,12,13,18,20,22,23,24):
        deltas.append(dict(maturity='private_original_whole_lifecycle_owned_composition_verified',code=entry,tests=entry_tests,
            evidence=ref(base/names[1]/'verification.json'),full_requirement_closure=False,
            scope='Private separately approved owned bootstrap/permit composition through actual startup, v6 dispatcher/collection/terminal and RunClosure; original repeats/stop/physical facts remain separate from normal evidence. No complete public admitted run/control registry or full failure/restart/recovery matrix.'))
    for delta in deltas:
        row['component_deltas'].append(delta)
        for item in delta['code']+delta['tests']:reverse[item['endpoint']]=sorted(set(reverse.get(item['endpoint'],[]))|{row['id']})
result=dict(schema_version=1,revision='ML3-AFFA17-2026-10-19-runtime-entry-v1',parent_trace=ref(parent),
    requirements=requirements,source_parent_register=prior['source_parent_register'],reverse_endpoint_requirements=reverse,
    evidence=ref(base/names[1]/'verification.json'),selected_evidence_file_checks=ref(base/names[0]/'verification.json'),
    initial_entry_evidence=ref(base/'runtime-entry-20261019a/verification.json'),
    original_probe_driver_failure=ref(base/'runtime-entry-window-20261019a/verification.json'),
    original_actual_expiry_failure=ref(base/'runtime-entry-window-20261019b/verification.json'),
    CAPA=ref(base/'capa-20261019-runtime-entry/register.json'),CAPA_validation=ref(base/'capa-20261019-runtime-entry/verification-recheck.json'),
    ADR=dict(path='docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0003.md',sha256=sha(candidate/'docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0003.md')),
    new_production_sources=[dict(path=p,sha256=sha(candidate/p)) for p in code_files.values()],packaged_sources=80,
    all_78_previous_production_sources_unchanged=True,current_b_c_production_sources_identical=True,
    selected_checks_per_phase=86,current_entry_checks_per_phase=67,selected_prior_evidence_checks_per_phase=19,
    current_owned_whole_entry_contexts=6,current_M3_source_links=254,current_durable_closed_roots=4,
    current_original_supervisor_births=14,current_helpers=18,current_workloads=10,actual_M1_admissions=0,
    public_entry_implementation=dict(read_only_preflight=True,actual_evidence_files_read=True,current_original_host_checks=True,
        private_whole_lifecycle_composition=True,private_stop_matching_collect=True,
        real_approved_receipt_semantics=False,full_public_run_control_registry=False,
        public_start=False,public_stop_collect_restart=False),
    software_requirements_retained=24,source_parents_retained=18,scenario_pairs_retained=30,endpoint_obligations_retained=90,full_runtime_cases_retained=9,
    finding_dispositions={'272':'file_at_use_and_private_whole_run_components_implemented',
        '273':'source_current_clocks_parent_population_checks_refined','274':'source_scope_stop_and_identity_concerns_refined',
        '275':'new_actual_expiry_probe_added','276':'original_singular_collection_error_preserved_parser_corrected',
        '277':'original_expiry_counterexample_preserved_post_I_O_revalidation_verified',
        '278':'matching_stop_no_second_cancellation_verified','279':'failed_stop_oracle_preserved_actual_wait_facts_retained',
        '280':'same_session_bounded_component_and_evidence_review'},
    open_findings=[135,222],remaining_gates=prior['remaining_gates'],
    full_constructor_startup_failure_matrix=False,full_active_restart_recovery_entry_matrix=False,
    full_crash_matrix_complete=False,runtime_cases_fully_complete=False,source_parent_semantics_validated=False,
    all_seven_phase3_tasks_complete=False,full_source_wheel_scope_passed=False,full_M1_complete=False,
    whole_platform_regression=False,full_candidate_review_complete=False,stable_increment17=False,
    independent_CAPA_effectiveness=False,accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False,scientific_result=False)
path=base/'runtime-entry-partial-traceability.json'
with path.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(trace=ref(path),selected_checks_per_phase=86,actual_M1_admissions=0)))
