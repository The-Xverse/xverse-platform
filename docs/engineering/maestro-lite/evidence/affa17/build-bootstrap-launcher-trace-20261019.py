"""Bidirectional partial startup trace; preserves the full unclosed024 scope."""
import ast
import copy
import hashlib
import json
from pathlib import Path

base=Path(__file__).resolve().parent
candidate=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
def ref(p):return dict(path=str(p.relative_to(base)),sha256=sha(p))
folders=['bootstrap-launcher-20261019a','bootstrap-launcher-unknown-20261019a']
frozen={name:read(base/name/'frozen-inputs.json') for name in folders}
for manifest in frozen.values():
    assert all(sha(candidate/n)==h for n,h in manifest.items())
verified=read(base/folders[0]/'verification-v2.json')
unknown=read(base/folders[1]/'verification.json')
assert verified['counts']=={p:dict(passed=71,failed=0,errors=0) for p in ('source','wheel')}
assert len(unknown['phases'])==2 and all(r['passed']==3 for r in unknown['phases'])
assert all(unknown['all_78_previous_production_sources_unchanged'] for _ in [0])
parent=base/'runtime-admission-partial-traceability.json';prior=read(parent)
source='src/xverse/maestro/bootstrap_launcher.py'
tests='tests/thesis_lite/maestro/'
def endpoint(path,name):
    manifest=folders[1] if path.endswith('test_bootstrap_launch_unknown.py') else folders[0]
    tree=ast.parse((candidate/path).read_text())
    scope=tree
    parts=name.split('.')
    if len(parts)==2:scope=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==parts[0])
    node=next(n for n in scope.body if isinstance(n,ast.FunctionDef) and n.name==parts[-1])
    return dict(endpoint=path+'::'+name,line=node.lineno,file_sha256=frozen[manifest][path],frozen_manifest=manifest+'/frozen-inputs.json')
code_names={
    9:['_image','OriginalBootstrapLauncher.launch','OriginalBootstrapLauncher.cancel'],
    10:['OriginalBootstrapLauncher.launch','OriginalBootstrapLauncher.cancel','OriginalBootstrapLauncher.drain'],
    11:['OriginalBootstrapLauncher.launch','OriginalBootstrapLauncher.drain','OriginalBootstrapLauncher.dispose','OriginalBootstrapRegistry.reserve'],
    12:['OriginalBootstrapLauncher._holder','OriginalBootstrapLauncher.launch','OriginalBootstrapRegistry.reserve'],
    13:['OriginalBootstrapLauncher._reap_failed','OriginalBootstrapLauncher.drain','OriginalBootstrapLauncher.dispose'],
    18:['OriginalBootstrapLauncher.outcome','OriginalBootstrapLauncher.drain'],
    23:['OriginalBootstrapLauncher.launch','OriginalBootstrapRegistry.reserve'],
    24:['_image','OriginalBootstrapLauncher.launch','OriginalBootstrapRegistry.reserve'],
}
test_names={
    'repeat':('test_bootstrap_launcher.py','test_original_ready_matching_repeat_and_changed_repeat_without_cancel'),
    'inputs':('test_bootstrap_launcher.py','test_rejection_before_creation_preserves_latch_and_original_parent'),
    'failed':('test_bootstrap_launcher.py','test_failed_registration_preserves_original_wait_and_never_recreates'),
    'cancel':('test_bootstrap_launcher.py','test_cancel_during_stopped_ready_does_not_wait_on_startup_lock'),
    'registry':('test_bootstrap_launcher.py','test_original_registry_reservations_capacity_and_no_copy'),
    'capacity':('test_bootstrap_launcher.py','test_registry_capacity_rejects'),
    'composition':('test_launcher_composition.py','test_actual_original_startup_through_terminal_and_helper_closure'),
    'unknown':('test_bootstrap_launch_unknown.py','test_failed_original_identity_is_retained_without_adoption_or_recreation'),
}
test_keys={9:['inputs','failed','cancel','unknown'],10:['failed','cancel','composition'],
    11:['repeat','cancel','registry'],12:['registry','unknown'],13:['failed','composition','unknown'],
    18:['repeat','composition','unknown'],23:['composition','capacity'],24:['inputs','unknown','capacity']}
requirements=copy.deepcopy(prior['requirements']);reverse=copy.deepcopy(prior['reverse_endpoint_requirements'])
for row in requirements:
    assert not row['full_requirement_closure']
    number=int(row['id'].removeprefix('ML-SR-'))
    if number not in code_names:continue
    code=[endpoint(source,n) for n in code_names[number]]
    checks=[endpoint(tests+test_names[k][0],test_names[k][1]) for k in test_keys[number]]
    row['component_deltas'].append(dict(maturity='original_internal_bootstrap_startup_owned_verified',code=code,tests=checks,
        evidence=[ref(base/folders[0]/'verification-v2.json'),ref(base/folders[1]/'verification.json')],
        full_requirement_closure=False,scope='Trusted low-level original startup/registry, live sealed artifact bytes, actual pidfd waits and retained unknowns; selected existing v6 terminal/closure composition only. No complete public entry or real facility/M1 admission.'))
    for item in code+checks:reverse[item['endpoint']]=sorted(set(reverse.get(item['endpoint'],[]))|{row['id']})
result=dict(schema_version=1,revision='ML3-AFFA17-2026-10-19-bootstrap-launcher-v1',
    scope='Internal original startup and bounded reservation within the still-required full runtime entry',
    parent_trace=ref(parent),requirements=requirements,source_parent_register=prior['source_parent_register'],
    reverse_endpoint_requirements=reverse,evidence=ref(base/folders[0]/'verification-v2.json'),
    unknown_evidence=ref(base/folders[1]/'verification.json'),
    original_collector_failure=ref(base/folders[0]/'audit-first-failure.json'),
    CAPA=ref(base/'capa-20261019-bootstrap-launcher/register.json'),
    CAPA_validation=ref(base/'capa-20261019-bootstrap-launcher/verification-recheck.json'),
    ADR=dict(path='docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0002.md',sha256=sha(candidate/'docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0002.md')),
    added_production_sources=[dict(path=source,sha256=frozen[folders[0]][source])],
    all_77_previous_production_sources_unchanged=True,packaged_sources=78,
    selected_checks_per_phase=74,first_frozen_run_checks_per_phase=71,additional_unknown_checks_per_phase=3,
    actual_owned_supervisor_births=18,actual_registered_helper_births=12,actual_composed_workload_births=8,
    external_only_unknown_waits=6,source_links=220,retained_durable_closed_roots=4,actual_M1_admissions=0,
    public_entry_implementation=dict(read_only_preflight=True,original_low_level_launcher=True,
        actual_sealed_executable_bytes_verified=True,bounded_bootstrap_reservation=True,
        real_authorization_receipt_facility_revalidation=False,full_run_control_registry=False,
        public_start=False,public_stop_collect_restart=False),
    software_requirements_retained=24,source_parents_retained=18,scenario_pairs_retained=30,
    endpoint_obligations_retained=90,full_runtime_cases_retained=9,
    finding_dispositions={'266':'internal_startup_ownership_layer_implemented',
        '267':'source_repeat_and_prebirth_side_effect_concerns_corrected',
        '268':'source_lifecycle_lock_gap_corrected',
        '269':'original_collector_failure_retained_successor_same_source_audit_passed',
        '270':'unknown_startup_controls_added_runtime_unknowns_preserved'},
    open_findings=[135,222],remaining_gates=prior['remaining_gates'],
    full_crash_matrix_complete=False,runtime_cases_fully_complete=False,source_parent_semantics_validated=False,
    all_seven_phase3_tasks_complete=False,full_source_wheel_scope_passed=False,full_M1_complete=False,
    whole_platform_regression=False,full_candidate_review_complete=False,stable_increment17=False,
    independent_CAPA_effectiveness=False,accepted=False,merged=False,canonical_note_edited=False,
    factory_run_created=False,scientific_result=False)
path=base/'bootstrap-launcher-partial-traceability.json'
with path.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(trace=ref(path),checks_per_phase=74,actual_M1_admissions=0)))
