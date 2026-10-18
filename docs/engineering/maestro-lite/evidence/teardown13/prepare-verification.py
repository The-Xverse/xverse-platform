from pathlib import Path
import hashlib,json,subprocess,platform
root=Path('/home/jefferson/xverse-platform-worktrees/maestro-lite-teardown-20261018')
thesis=Path('/home/jefferson/distributed_safety_critical_thesis')
out=root/'docs/engineering/maestro-lite/evidence/teardown13';old=out.parent/'outcomes12'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda n,d:(out/n).write_text(json.dumps(d,indent=2)+'\n')
revision='ML3-TEARDOWN13-2026-10-18-v4';parent='f292416e85cb21eef503364c20fdc884a0c9572c'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==parent
trace=json.loads((old/'traceability.json').read_text());trace.update(work_item='ML3-TEARDOWN13',maturity='partial_reverse_unit_teardown_candidate')
code={
'ML-SR-010':['src/xverse/maestro/prbc.py::terminate','src/xverse/maestro/prbc.py::release_empty'],
'ML-SR-011':['src/xverse/maestro/teardown.py::run','src/xverse/maestro/teardown.py::cancel','src/xverse/maestro/teardown.py::_order'],
'ML-SR-012':['src/xverse/maestro/launcher.py::revalidate_issued','src/xverse/maestro/persistence.py::record_teardown','src/xverse/maestro/teardown.py::_jobs'],
'ML-SR-013':['src/xverse/maestro/teardown.py::_normal','src/xverse/maestro/teardown.py::_emergency','src/xverse/maestro/prbc.py::record'],
'ML-SR-016':['src/xverse/maestro/teardown_evidence.py::TeardownJournal','src/xverse/maestro/teardown_evidence.py::record','src/xverse/maestro/teardown_evidence.py::validate_teardown_reply'],
'ML-SR-018':['src/xverse/maestro/teardown.py::TeardownResult','src/xverse/maestro/teardown.py::UnitTeardown'],
'ML-SR-019':['src/xverse/maestro/teardown.py::_emergency'],
'ML-SR-022':['src/xverse/maestro/teardown.py::run']}
tests={
'ML-SR-010':['test_c1_termination_retains_controls_until_separate_release','test_release_without_stop_observation_cannot_kill_or_remove'],
'ML-SR-011':['test_normal_reverse_stop_reap_and_separate_release_with_durable_records','test_identity_and_nonblocking_conflicts_have_no_teardown_effect'],
'ML-SR-012':['test_copied_active_step_cannot_authorize_normal_record','test_missing_original_registry_never_adopts_handle','test_original_issuer_loss_preserves_explicit_unresolved_reap','test_lost_original_c1_is_unresolved_and_other_owned_cleanup_continues'],
'ML-SR-013':['test_normal_reverse_stop_reap_and_separate_release_with_durable_records','test_already_exited_leader_with_live_descendant_requires_c1_cleanup','test_emergency_status_conflict_never_blocks_or_infers_release','test_expired_c1_deadline_and_lock_conflict_cannot_mutate'],
'ML-SR-016':['test_normal_reverse_stop_reap_and_separate_release_with_durable_records','test_stage_only_teardown_never_fabricates_start_outcome','test_missing_normal_record_or_ack_uses_original_cleanup_only'],
'ML-SR-018':['test_original_issuer_loss_preserves_explicit_unresolved_reap','test_actual_teardown_flush_fault_retains_missing_normal_records'],
'ML-SR-019':['test_missing_normal_record_or_ack_uses_original_cleanup_only','test_actual_teardown_flush_fault_retains_missing_normal_records','test_lost_original_c1_is_unresolved_and_other_owned_cleanup_continues'],
'ML-SR-022':['test_normal_reverse_stop_reap_and_separate_release_with_durable_records']}
reverse={}
for row in trace['requirements']:
 for endpoint in code.get(row['id'],[]):row['code'].append({'endpoint':endpoint})
 for symbol in tests.get(row['id'],[]):row['verification'].append({'endpoint':'tests/thesis_lite/maestro/test_teardown.py::'+symbol})
 for ref in row['code']+row['verification']:
  ref['file_sha256']=sha(root/ref['endpoint'].partition('::')[0]);reverse.setdefault(ref['endpoint'],[]).append(row['id'])
 assert not row['full_requirement_closure']
trace['reverse_endpoint_requirements']=reverse
trace['remaining_teardown13_scope']=['full helper closure and all issued resource integration','missing-observation normal failure/disposition records','automatic health/tick/schedule budget admission','restart/controller recovery','dual coverage/U8','initial helper admission and full M1/runtime review/acceptance']
save('traceability.json',trace)
inputs=json.loads((old/'engineering-inputs.json').read_text())
for name,h in inputs['inputs'].items():assert sha(thesis/name)==h
assert sha(thesis/'notes/dynamic_thesis_notes.md')==inputs['canonical_note_sha256']
assert sha(root/'tests/thesis_lite/maestro/lifecycle-payload-v2.schema.json')==sha(thesis/'specs/024-maestro-lite-lifecycle/engineering/successors/ML-DESIGN-2026-10-03-v2/lifecycle-payload.schema.json')
mp=thesis/'specs/024-maestro-lite-lifecycle/review/continuation-2026-10-18/outcomes12/candidate-manifest.json';manifest=json.loads(mp.read_text())
intentional=['docs/engineering/maestro-lite/README.md','src/xverse/maestro/prbc.py','src/xverse/maestro/launcher.py','src/xverse/maestro/persistence.py','src/xverse/maestro/persistence_worker.py','tests/thesis_lite/maestro/outcome_fixture.py']
for name,h in manifest['candidate_file_sha256'].items():
 if name not in intentional:assert sha(root/name)==h,name
inputs.update(thesis_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=thesis,text=True).strip(),revision=revision,parent_candidate_commit=parent,parent_manifest_sha256=sha(mp),parent_selected_inputs_verified=len(manifest['candidate_file_sha256']),intentional_parent_source_changes=intentional)
save('engineering-inputs.json',inputs)
records=[]
for row in json.loads((old/'native-build-verification.json').read_text())['variants']:
 command=[s.replace('evidence/outcomes12','evidence/teardown13') for s in row['command']];binary=root/command[command.index('-o')+1];logfile=binary.with_suffix('.log')
 with logfile.open('w') as log:r=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 source=next(s for s in command if s.startswith('src/'));assert r.returncode==0
 records.append(dict(command=command,returncode=r.returncode,source_sha256=sha(root/source),log_sha256=sha(logfile),binary_sha256=sha(binary)))
save('native-build-verification.json',{'variants':records})
(out/'frozen-task-plan.md').write_bytes((root/'docs/engineering/maestro-lite/tasks-teardown13.md').read_bytes())
paths=set(json.loads((old/'source-manifest.json').read_text())['input_sha256'])
paths.update(['src/xverse/maestro/teardown.py','src/xverse/maestro/teardown_evidence.py','tests/thesis_lite/maestro/test_teardown.py','docs/engineering/maestro-lite/ADR-ML3-TEARDOWN-0001.md','docs/engineering/maestro-lite/unit-specification-teardown13.md','docs/engineering/maestro-lite/teardown-expected.json','docs/engineering/maestro-lite/review-teardown13.md','docs/engineering/maestro-lite/verify-teardown13.py','docs/engineering/maestro-lite/evidence/teardown13/prepare-verification.py','docs/engineering/maestro-lite/evidence/teardown13/frozen-task-plan.md'])
save('source-manifest.json',{'revision':revision,'parent_commit':parent,'baseline':manifest['accepted_main_baseline'],'input_sha256':{name:sha(root/name) for name in sorted(paths)}})
save('host-environment.json',{'platform':platform.platform(),'uname':list(platform.uname()),'python':platform.python_version(),'cc':subprocess.check_output(['cc','--version'],text=True).splitlines()[0],'wheel_sha256':sha(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl'),'factory_run_created':False,'full_runtime_ready':False})
print(json.dumps({'revision':revision,'frozen_inputs':len(paths),'partial_endpoints':len(reverse),'parent_blobs':len(manifest['candidate_file_sha256'])}))
