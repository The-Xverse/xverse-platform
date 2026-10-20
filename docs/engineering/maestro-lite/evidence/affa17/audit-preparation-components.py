"""Audit retained original component facts; never infer full M1 or acceptance."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
save=lambda n,d:(OUT/n).write_text(json.dumps(d,indent=2)+'\n')
frozen=read(OUT/'preparation-v1-frozen-inputs.json')
assert all(sha(ROOT/n)==h for n,h in frozen.items())
regression=read(OUT/'preparation-v1-regression.json')
for r in regression['receipts']:
    name='preparation-v1-source' if r['PYTHONPATH']!='unset' else 'preparation-v1-wheel'
    assert r['returncode']==0 and r['log_sha256']==sha(OUT/(name+'.log'))
    assert r['input_manifest_sha256']==sha(OUT/'preparation-v1-frozen-inputs.json')
identity=read(OUT/'preparation-v1-installed-identity.json')
for row in list(identity['modules'].values())+list(identity['native_resources'].values()):
    assert sha(Path(row['file']))==row['sha256']
assert len(identity['modules'])==27 and len(identity['native_resources'])==4
roots,brokers,boots,legacy,standalone=[],[],[],[],[]
for name in ['preparation-v1-source-harness','preparation-v1-wheel-harness']:
    directory=OUT/name
    for p in sorted(directory.glob('maestro-component-*.json')):
        facts=read(p)
        assert facts['root_removed'] and facts['workers_reaped']
        assert not (Path(facts['parent_path'])/facts['root_name']).exists()
        roots.append(dict(receipt=str(p.relative_to(ROOT)),sha256=sha(p),root_absent=True))
    for p in sorted(directory.glob('run-broker-waits-*.json')):
        facts=read(p)
        assert facts['bootstrap_reaped'] and facts['registered_helpers_reaped'] and facts['storage_reaped']
        assert facts['original_C1_released'] and facts['helper_count']==2 and not facts['full_M1_complete']
        brokers.append(dict(receipt=str(p.relative_to(ROOT)),sha256=sha(p),facts=facts))
    for p in sorted(directory.glob('run-bootstrap-waits-*.json')):
        facts=read(p)
        assert facts['bootstrap_drain']['supervisor_reaped'] and facts['bootstrap_drain']['registered_children_reaped']
        assert facts['original_helpers_actually_reaped'] and facts['all_original_C1_released']
        boots.append(dict(receipt=str(p.relative_to(ROOT)),sha256=sha(p),facts=facts))
    for p in sorted(directory.glob('bootstrap-children-*.json')):
        facts=read(p)
        assert facts['supervisor_reaped'] and facts['registered_children_reaped'] and facts['all_original_boundaries_released']
        legacy.append(dict(receipt=str(p.relative_to(ROOT)),sha256=sha(p),facts=facts))
    for p in sorted(directory.glob('affa-standalone-reaped-*.json')):
        facts=read(p)
        assert facts['authority_reaped']
        standalone.append(dict(receipt=str(p.relative_to(ROOT)),sha256=sha(p),facts=facts))
assert len(roots)>=448 and len(brokers)==40 and len(boots)==70 and len(legacy)>=150 and len(standalone)==34
native_teardowns=[]
for name in ['preparation-v1-source-harness','preparation-v1-wheel-harness']:
    found=list((OUT/name).glob('native-teardown-public-*.json'))
    assert len(found)==1
    for p in found:
        facts=read(p)
        assert facts['native_workload_waits_observed'] and facts['original_helper_reaping_is_separate']
        assert not facts['full_M1_complete']
        assert facts['source_sha256']==sha(ROOT/'tests/thesis_lite/maestro/test_run_teardown.py')
        assert [r['status'] for r in facts['public_m3'] if r['status'] in ('stopped','cleaned')]==['stopped','cleaned']*2
        assert len([e for e in facts['argus_events'] if e['producerId']=='maestro.teardown13'])==8
        native_teardowns.append(dict(receipt=str(p.relative_to(ROOT)),sha256=sha(p),facts=facts))
import re
counts=[]
for name in ['preparation-v1-source','preparation-v1-wheel']:
    passed=re.search(r'(\d+) passed', (OUT/(name+'.log')).read_text())
    assert passed
    counts.append(int(passed[1]))
assert counts==[516,516]
wheel_log=(OUT/'preparation-v1-wheel.log').read_text()
assert '516 passed' in wheel_log
assert not re.findall(r'^FAILED (.+)$',wheel_log,re.M)
public=read(OUT/'preparation-v1-source-public-evidence-index.json')+read(OUT/'preparation-v1-wheel-public-evidence-index.json')
for p in public:
    assert sha(OUT/p['snapshot'])==p['sha256']
assert len(public)==40 and sum(p['source_links'] for p in public)>66
# Preserve all parent allocations and closure obligations; this delta is partial.
parent=ROOT/'docs/engineering/maestro-lite/evidence/recovery16/traceability.json'
trace=read(parent)
assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18
endpoints={
 'ML-SR-001':['admission.py::_PreparationProof','admission.py::_preparation_data'],
 'ML-SR-005':['run_broker.py::admit','run_broker.py::stage'],
 'ML-SR-006':['run_broker.py::_until','run_broker.py::_native'],
 'ML-SR-007':['run_broker.py::release','providers.py::start'],
 'ML-SR-008':['run_broker.py::observe'],
 'ML-SR-009':['run_broker.py::_boundary','prbc.py::bind_authority','prbc.py::admit_epoch','prbc.py::_creation_epoch'],
 'ML-SR-010':['run_broker.py::cancel','teardown.py::_stop','teardown.py::_cleanup','run_broker.py::stop_owned','run_broker.py::retire_owned'],
 'ML-SR-011':['run_broker.py::cancel','affa_client.py::revoke'],
 'ML-SR-012':['run_broker.py::_holder','run_broker.py::revalidate_issued','affa_client.py::AuthorityEpochAdvance'],
 'ML-SR-013':['run_broker.py::stage','bootstrap.py::watch'],
 'ML-SR-014':['run_broker.py::revalidate_issued','prbc.py::admit_epoch'],
 'ML-SR-016':['run_broker.py::release'],
 'ML-SR-018':['persistence_worker.py::serve'],
 'ML-SR-019':['run_broker.py::release','persistence_worker.py::serve'],
 'ML-SR-020':['run_broker.py::RunCancellation'],
 'ML-SR-022':['run_broker.py::RunRecipe'],
 'ML-SR-023':['run_broker.py::_issued'],
 'ML-SR-024':['run_broker.py::UnitAdmission','prbc.py::BoundaryLimits']}
rows=[]
for row in trace['requirements']:
    assert not row['full_requirement_closure']
    refs=[]
    for endpoint in endpoints.get(row['id'],[]):
        file,symbol=endpoint.split('::')
        p=ROOT/'src/xverse/maestro'/file
        names={n.name for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        assert symbol in names
        refs.append(dict(endpoint='src/xverse/maestro/'+endpoint,file_sha256=sha(p)))
    rows.append(dict(id=row['id'],status='partial_broker_teardown_component' if refs else 'inherited_open',
        full_requirement_closure=False,delta_code=refs,
        delta_verification=['tests/thesis_lite/maestro/test_run_teardown.py','tests/thesis_lite/maestro/test_teardown.py','tests/thesis_lite/maestro/test_run_broker.py','tests/thesis_lite/maestro/test_storage_revalidate.py','tests/thesis_lite/maestro/test_affa_epoch.py','tests/thesis_lite/maestro/test_boundary.py'] if refs else []))
result=dict(revision='ML3-AFFA17-2026-10-18-preparation-proof-v1-component',parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    actual_terminal_session=83114,source_checks=counts[0],installed_wheel_checks=counts[1],installed_wheel_failed=0,returncode=0,
    affected_source_returncode=0,affected_installed_wheel_returncode=0,affected_regression_passed=True,
    source_manifest_sha256=sha(OUT/'preparation-v1-frozen-inputs.json'),tested_inputs_archive_sha256=sha(OUT/'preparation-v1-tested-inputs.tar.gz'),
    wheel_sha256=regression['wheel_sha256'],installed_maestro_modules=27,installed_native_resources=4,
    owned_roots_absent=len(roots),owned_root_receipts=roots,original_broker_wait_receipts=brokers,
    original_bootstrap_wait_receipts=boots,legacy_bootstrap_wait_receipts=legacy,standalone_wait_receipts=standalone,
    public_snapshots=len(public),actual_public_source_hash_links_verified=sum(p['source_links'] for p in public),damaged_evidence_snapshots_with_gaps=sum(bool(p['reader_gaps']) for p in public),
    public_evidence_index_sha256={n:sha(OUT/(n+'-public-evidence-index.json')) for n in ['preparation-v1-source','preparation-v1-wheel']},
    broker_workload_direct_child_waits_not_proven_by_helper_reaping=True,missing_normal_stop_cleanup_records_preserved=True,
    native_normal_teardown=True,native_normal_teardown_receipts=native_teardowns,
    minimum_actual_native_workload_waits_recorded=2*len(native_teardowns),
    initial_red_default_root_receipts_missing=5,all_history_root_absence_proven=False,
    requirements=rows,source_parent_register=trace['source_parent_register'],parent_trace_sha256=sha(parent),
    binding_full_ML_SR=24,binding_source_parents=18,binding_scenario_pairs=30,binding_endpoints=90,binding_full_runtime_cases=9,all_nine_phases_retained=True,
    actual_initial_generation_M3_Argus_broker_integration=True,authenticated_C1_epoch_bridge=True,native_generations_1_2_3_component_verified=True,full_fresh_generation_restart=False,
    fresh_generation_M3_contexts=False,controller_replacement_integration=False,dispatcher_teardown_run_closure_integration=False,
    U7_U8_complete=False,process_mode_admission=False,full_platform_regression=False,
    full_M1_complete=False,full_phase3_complete=False,independent_full_candidate_review=False,
    accepted=False,merged=False,stable_increment17=False,canonical_note_edited=False,factory_run_created=False)
result['original_public_source_fixtures_missing']=sum(any(g['source']=='original fixture' for g in row['reader_gaps']) for row in public)
assert result['original_public_source_fixtures_missing']==0
result['original_timeout_causes_proven']=False
result['signed_zero_pin_repair_pending']=True
result['unresolved_finding']='review-affa17.md finding39: signed-zero exact-input distinction; original finding35 failures retained and not a hard timing guarantee'
save('preparation-component-verification.json',result)
print(json.dumps({k:result[k] for k in ['source_checks','installed_wheel_checks','owned_roots_absent','public_snapshots',
    'actual_public_source_hash_links_verified','damaged_evidence_snapshots_with_gaps','stable_increment17']}))
