"""Bind inert joint preflight without replacing actual M1 or complete entry."""
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
folder=base/'runtime-admission-20261019b'
verified,frozen=read(folder/'verification.json'),read(folder/'frozen-inputs.json')
root=Path(read(folder/'running.json')['frozen_source_root'])
assert all(sha(root/n)==h==sha(candidate/n) for n,h in frozen.items())
assert verified['counts']=={p:dict(passed=146,failed=0,errors=0) for p in ('source','wheel')}
assert verified['actual_M1_admissions']==verified['actual_runtime_contexts']==0
parent=base/'issuer-loss-partial-traceability.json'
prior=read(parent)
def endpoint(path,name):
    tree=ast.parse((root/path).read_text())
    if '.' in name:
        owner,method=name.split('.')
        scope=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==owner)
        node=next(n for n in scope.body if isinstance(n,ast.FunctionDef) and n.name==method)
    else:node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    return dict(endpoint=path+'::'+name,line=node.lineno,file_sha256=frozen[path],
        frozen_manifest='runtime-admission-20261019b/frozen-inputs.json')
source='src/xverse/maestro/runtime_admission.py'
code=[endpoint(source,name) for name in ('FacilityAttestation.canonical_bytes','RunAuthorization.canonical_bytes',
    'admission_digest','validate_run_admission','_reencode')]
test='tests/thesis_lite/maestro/test_runtime_admission.py'
tests=[endpoint(test,name) for name in ('test_joint_read_only_pins_are_inert_and_no_sink_provider_or_child_is_created',
    'test_every_external_pin_is_required_and_bundle_rehash_cannot_replace_it',
    'test_facility_claim_universe_is_closed_even_with_a_new_caller_hash',
    'test_authorization_never_extends_original_scope_or_mixes_clock_domains',
    'test_original_serializer_inputs_are_rederived_without_sinks',
    'test_bootstrap_start_window_can_expire_before_original_cleanup_end_without_changing_either')]
ids=['ML-SR-'+str(n).zfill(3) for n in (1,5,9,10,23,24)]
requirements=copy.deepcopy(prior['requirements'])
reverse=copy.deepcopy(prior['reverse_endpoint_requirements'])
for row in requirements:
    assert not row['full_requirement_closure']
    if row['id'] in ids:
        row['component_deltas'].append(dict(maturity='inert_joint_runtime_admission_binding_unit_verified',
            code=code,tests=tests,evidence=ref(folder/'verification.json'),full_requirement_closure=False,
            scope='Read-only externally pinned authorization/attestation bindings and original v6/BS17 input rederivation only; synthetic attestations, no actual evidence verification, facility proof, launcher or start authority.'))
for item in code+tests:
    reverse[item['endpoint']]=sorted(set(reverse.get(item['endpoint'],[]))|set(ids))
result=dict(schema_version=1,revision='ML3-AFFA17-2026-10-19-runtime-admission-v1',
    scope='Joint read-only preflight within the complete runtime entry implementation; full entry remains required',
    parent_trace=ref(parent),requirements=requirements,source_parent_register=prior['source_parent_register'],
    reverse_endpoint_requirements=reverse,evidence=ref(folder/'verification.json'),
    original_fixture_failure=ref(base/'runtime-admission-20261019a/verification.json'),
    CAPA=ref(base/'capa-20261019-runtime-admission/register.json'),
    CAPA_validation=ref(base/'capa-20261019-runtime-admission/verification-recheck.json'),
    added_production_sources=[dict(path=source,sha256=frozen[source])],
    all_76_previous_production_sources_unchanged=True,packaged_sources=77,
    current_affected_counts=verified['counts'],joint_preflight_checks_per_phase=40,
    empty_owned_parent_reservations=80,actual_runtime_contexts=0,actual_M1_admissions=0,
    synthetic_unit_attestations_not_runtime_evidence=True,
    public_entry_implementation=dict(read_only_preflight=True,original_launcher=False,
        live_artifact_facility_revalidation=False,run_registry=False,
        public_start=False,public_stop_collect_restart=False),
    software_requirements_retained=24,source_parents_retained=18,scenario_pairs_retained=30,
    endpoint_obligations_retained=90,full_runtime_cases_retained=9,
    finding_dispositions={'262':'complete_entry_gap_identified_preflight_layer_implemented',
        '263':'synthetic_fixture_digest_omission_corrected_locally','264':'parser_bounds_and_input_diagnostics_refined',
        '265':'bounded_same_session_read_only_scope_review'},
    open_findings=[135,222],remaining_gates=prior['remaining_gates'],
    full_crash_matrix_complete=False,runtime_cases_fully_complete=False,
    source_parent_semantics_validated=False,all_seven_phase3_tasks_complete=False,
    full_source_wheel_scope_passed=False,full_M1_complete=False,whole_platform_regression=False,
    full_candidate_review_complete=False,stable_increment17=False,independent_CAPA_effectiveness=False,
    accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False,scientific_result=False)
path=base/'runtime-admission-partial-traceability.json'
with path.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(trace=ref(path),counts=result['current_affected_counts'],actual_M1_admissions=0)))
