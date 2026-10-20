from pathlib import Path
import hashlib,json,subprocess,platform
root=Path('/home/jefferson/xverse-platform-worktrees/maestro-lite-outcomes-20261018')
thesis=Path('/home/jefferson/distributed_safety_critical_thesis')
out=root/'docs/engineering/maestro-lite/evidence/outcomes12';old=out.parent/'provider11'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda n,d:(out/n).write_text(json.dumps(d,indent=2)+'\n')
revision='ML3-OUTCOMES12-2026-10-18-v4';parent='89bf5e3a6386c496dffac2a1cef0bb73e48c08dd'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==parent
trace=json.loads((old/'traceability.json').read_text());trace.update(work_item='ML3-OUTCOMES12',maturity='partial_durable_start_probe_evidence_candidate')
code={
'ML-SR-005':['src/xverse/maestro/lifecycle_evidence.py::_history','src/xverse/maestro/lifecycle_evidence.py::_mirrors'],
'ML-SR-007':['src/xverse/maestro/persistence.py::record_probe','src/xverse/maestro/lifecycle_evidence.py::_parents','src/xverse/maestro/lifecycle_evidence.py::record','src/xverse/maestro/lifecycle_evidence.py::validate_receipt'],
'ML-SR-008':['src/xverse/maestro/lifecycle_evidence.py::record'],
'ML-SR-009':['src/xverse/maestro/persistence.py::record_probe','src/xverse/maestro/persistence_worker.py::serve'],
'ML-SR-012':['src/xverse/maestro/persistence.py::record_probe'],
'ML-SR-016':['src/xverse/maestro/lifecycle_evidence.py::OutcomeJournal','src/xverse/maestro/lifecycle_evidence.py::_digest','src/xverse/maestro/lifecycle_evidence.py::validate_receipt','src/xverse/maestro/lifecycle_evidence.py::LifecycleReceipt'],
'ML-SR-018':['src/xverse/maestro/lifecycle_evidence.py::LifecycleReceipt'],
'ML-SR-019':['src/xverse/maestro/persistence.py::_fail','src/xverse/maestro/providers.py::cancel']}
tests={
'ML-SR-005':['test_original_durable_history_loss_blocks_new_ready'],
'ML-SR-007':['test_real_start_probe_and_dependency_records_before_ready_return','test_only_exact_current_observation_can_be_recorded','test_pending_exec_has_probe_record_without_false_started_credit'],
'ML-SR-008':['test_public_source_hashes_and_payload_schema_match_actual_records'],
'ML-SR-009':['test_real_journal_lock_after_release_times_out_without_ready','test_original_storage_worker_failure_after_release_never_returns_ready'],
'ML-SR-012':['test_only_exact_current_observation_can_be_recorded'],
'ML-SR-016':['test_public_source_hashes_and_payload_schema_match_actual_records','test_substituted_actual_worker_ack_never_returns_ready'],
'ML-SR-018':['test_original_storage_worker_failure_after_release_never_returns_ready'],
'ML-SR-019':['test_original_storage_worker_failure_after_release_never_returns_ready','test_original_durable_history_loss_blocks_new_ready']}
reverse={}
for row in trace['requirements']:
 for endpoint in code.get(row['id'],[]):row['code'].append({'endpoint':endpoint})
 for symbol in tests.get(row['id'],[]):row['verification'].append({'endpoint':'tests/thesis_lite/maestro/test_outcomes.py::'+symbol})
 for ref in row['code']+row['verification']:
  ref['file_sha256']=sha(root/ref['endpoint'].partition('::')[0]);reverse.setdefault(ref['endpoint'],[]).append(row['id'])
 assert not row['full_requirement_closure']
trace['reverse_endpoint_requirements']=reverse
trace['remaining_outcomes12_scope']=['missing-observation normal failure/disposition records','automatic health/tick/schedule budget admission','normal stop/cleanup and reverse teardown','restart/recovery','dual coverage/U8','initial helper admission and full M1/runtime review/acceptance']
save('traceability.json',trace)
inputs=json.loads((old/'engineering-inputs.json').read_text())
for name,h in inputs['inputs'].items():assert sha(thesis/name)==h
assert sha(thesis/'notes/dynamic_thesis_notes.md')==inputs['canonical_note_sha256']
assert sha(root/'tests/thesis_lite/maestro/lifecycle-payload-v2.schema.json')==sha(thesis/'specs/024-maestro-lite-lifecycle/engineering/successors/ML-DESIGN-2026-10-03-v2/lifecycle-payload.schema.json')
mp=thesis/'specs/024-maestro-lite-lifecycle/review/continuation-2026-10-18/provider11/candidate-manifest.json';manifest=json.loads(mp.read_text())
intentional=['docs/engineering/maestro-lite/README.md','src/xverse/maestro/persistence.py','src/xverse/maestro/persistence_worker.py','src/xverse/maestro/providers.py','tests/thesis_lite/maestro/test_provider.py']
for name,h in manifest['candidate_file_sha256'].items():
 if name not in intentional:assert sha(root/name)==h,name
inputs.update(thesis_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=thesis,text=True).strip(),revision=revision,parent_candidate_commit=parent,parent_manifest_sha256=sha(mp),parent_selected_inputs_verified=len(manifest['candidate_file_sha256']),intentional_parent_source_changes=intentional)
save('engineering-inputs.json',inputs)
records=[]
for row in json.loads((old/'native-build-verification.json').read_text())['variants']:
 command=[s.replace('evidence/provider11','evidence/outcomes12') for s in row['command']];binary=root/command[command.index('-o')+1];logfile=binary.with_suffix('.log')
 with logfile.open('w') as log:r=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 source=next(s for s in command if s.startswith('src/'));assert r.returncode==0
 records.append(dict(command=command,returncode=r.returncode,source_sha256=sha(root/source),log_sha256=sha(logfile),binary_sha256=sha(binary)))
save('native-build-verification.json',{'variants':records})
(out/'frozen-task-plan.md').write_bytes((root/'docs/engineering/maestro-lite/tasks-outcomes12.md').read_bytes())
paths=set(json.loads((old/'source-manifest.json').read_text())['input_sha256'])
paths.update(['src/xverse/maestro/lifecycle_evidence.py','tests/thesis_lite/maestro/test_outcomes.py','tests/thesis_lite/maestro/outcome_fixture.py','tests/thesis_lite/maestro/lifecycle-payload-v2.schema.json','docs/engineering/maestro-lite/ADR-ML3-OUTCOMES-0001.md','docs/engineering/maestro-lite/unit-specification-outcomes12.md','docs/engineering/maestro-lite/outcomes-expected.json','docs/engineering/maestro-lite/review-outcomes12.md','docs/engineering/maestro-lite/verify-outcomes12.py','docs/engineering/maestro-lite/evidence/outcomes12/prepare-verification.py','docs/engineering/maestro-lite/evidence/outcomes12/frozen-task-plan.md'])
save('source-manifest.json',{'revision':revision,'parent_commit':parent,'baseline':manifest['accepted_main_baseline'],'input_sha256':{name:sha(root/name) for name in sorted(paths)}})
save('host-environment.json',{'platform':platform.platform(),'uname':list(platform.uname()),'python':platform.python_version(),'cc':subprocess.check_output(['cc','--version'],text=True).splitlines()[0],'wheel_sha256':sha(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl'),'factory_run_created':False,'full_runtime_ready':False})
print(json.dumps({'revision':revision,'frozen_inputs':len(paths),'partial_endpoints':len(reverse),'parent_blobs':len(manifest['candidate_file_sha256'])}))
