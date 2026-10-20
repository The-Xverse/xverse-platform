from pathlib import Path
import hashlib,json,subprocess,platform,ast
root=Path('/home/jefferson/xverse-platform-worktrees/maestro-lite-closure-20261018')
thesis=Path('/home/jefferson/distributed_safety_critical_thesis')
base=root/'docs/engineering/maestro-lite';out=base/'evidence/closure15';old=out.parent/'scheduler14'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda n,d:(out/n).write_text(json.dumps(d,indent=2)+'\n')
revision='ML3-CLOSURE15-2026-10-18-v5';parent='42729bd9a01ff63481e3a131acab5e93c3d2f9b0'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==parent
trace=json.loads((old/'traceability.json').read_text());trace.update(work_item='ML3-CLOSURE15',maturity='partial_original_run_resource_and_incomplete_writer_closure_candidate')
code={
'ML-SR-010':['run_closure.py::close'],
'ML-SR-011':['run_closure.py::close','run_closure.py::cancel'],
'ML-SR-012':['bootstrap.py::birth','bootstrap.py::_holder','run_closure.py::_holder','run_closure.py::close'],
'ML-SR-013':['run_closure.py::close','run_closure.py::RunClosureResult','run_closure.py::HelperClosure','run_closure.py::IssuedBoundaryClosure'],
'ML-SR-018':['writer_closure.py::WriterClosure','writer_closure.py::close_writer','writer_closure.py::decode_closure'],
'ML-SR-019':['run_closure.py::close','persistence.py::close_incomplete'],
'ML-SR-020':['persistence.py::close_incomplete','writer_closure.py::unresolved'],
'ML-SR-022':['run_closure.py::close','persistence.py::close_incomplete'],
'ML-SR-023':['persistence_worker.py::serve'],
'ML-SR-024':['run_closure.py::__init__']}
checks={
'ML-SR-010':['test_partial_bootstrap_closes_exact_resources_without_normal_unit_records'],
'ML-SR-011':['test_normal_conflicts_reject_and_independent_cancel_does_not_wait','test_unit_mutation_conflict_rejects_before_closure_cancellation','test_cancel_bypasses_active_closure_locks_and_real_blocked_storage','test_active_dispatcher_normal_conflict_preserves_its_original_authority'],
'ML-SR-012':['test_original_inventory_content_substitution_rejects_before_any_cleanup','test_copied_and_changed_scope_reject_before_mutation','test_invalid_original_adapter_alias_keeps_cleanup_only_root_and_c1_authority','test_failed_adapter_construction_retains_original_birth_and_unknown_writer','test_unacknowledged_original_birth_remains_unresolved_after_root_and_c1_cleanup'],
'ML-SR-013':['test_all_original_helpers_and_extra_boundary_close_with_separate_writer_facts','test_controllerless_owned_unit_cleanup_uses_original_reverse_graph','test_forced_native_issuer_loss_does_not_fabricate_direct_wait','test_short_original_window_returns_unknown_without_a_new_cleanup_deadline'],
'ML-SR-018':['test_actual_writer_fault_stage_keeps_public_state_and_durable_manifest_separate','test_malformed_actual_closure_ack_is_not_current_writer_evidence'],
'ML-SR-019':['test_actual_storage_stall_keeps_unknown_state_and_still_closes_owned_boundaries','test_invalid_original_adapter_alias_keeps_cleanup_only_root_and_c1_authority'],
'ML-SR-020':['test_actual_storage_stall_keeps_unknown_state_and_still_closes_owned_boundaries','test_short_original_window_returns_unknown_without_a_new_cleanup_deadline'],
'ML-SR-022':['test_all_original_helpers_and_extra_boundary_close_with_separate_writer_facts','test_actual_writer_fault_stage_keeps_public_state_and_durable_manifest_separate'],
'ML-SR-023':['test_full_dispatcher_result_precedes_full_helper_closure'],
'ML-SR-024':['test_invalid_closure_budget_has_no_effect','test_invalid_close_reason_rejects_before_unit_or_helper_mutation']}
reverse={}
for row in trace['requirements']:
 for field, refs in [('code',['src/xverse/maestro/'+p for p in code.get(row['id'],[])]),('verification',['tests/thesis_lite/maestro/test_closure.py::'+p for p in checks.get(row['id'],[])])]:
  for endpoint in refs:
   if not any(r['endpoint']==endpoint for r in row[field]):row[field].append({'endpoint':endpoint})
 for ref in row['code']+row['verification']:
  name,_,symbol=ref['endpoint'].partition('::');path=root/name;ref['file_sha256']=sha(path)
  if symbol and path.suffix=='.py':
   names={n.name for n in ast.walk(ast.parse(path.read_text())) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))};assert symbol in names,ref['endpoint']
  reverse.setdefault(ref['endpoint'],[]).append(row['id'])
 assert not row['full_requirement_closure']
trace['reverse_endpoint_requirements']=reverse
trace.pop('remaining_scheduler14_scope',None)
trace['remaining_closure15_scope']=['initial original-supervisor/authenticated bootstrap-permit and exact environment/dependency admission','full M1/global epoch cancellation and independent supervision across all control paths','controller recovery and explicit fresh-generation restart','U7 pure provisional and independent closed-writer dual coverage','U8 confined collection, bounded terminal-report artifact and independently reported closure/results','nine full runtime cases; G1/G3/G4/G5; independent full review and explicit acceptance','downstream full phases 4-9']
save('traceability.json',trace)
inputs=json.loads((old/'engineering-inputs.json').read_text())
for name,h in inputs['inputs'].items():assert sha(thesis/name)==h
assert sha(thesis/'notes/dynamic_thesis_notes.md')==inputs['canonical_note_sha256']
mp=thesis/'specs/024-maestro-lite-lifecycle/review/continuation-2026-10-18/scheduler14/candidate-manifest.json';manifest=json.loads(mp.read_text())
intentional=['docs/engineering/maestro-lite/README.md','src/xverse/maestro/bootstrap.py','src/xverse/maestro/persistence.py','src/xverse/maestro/persistence_worker.py']
for name,h in manifest['candidate_file_sha256'].items():
 if name not in intentional:assert sha(root/name)==h,name
inputs.update(thesis_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=thesis,text=True).strip(),revision=revision,parent_candidate_commit=parent,parent_manifest_sha256=sha(mp),parent_selected_inputs_verified=len(manifest['candidate_file_sha256']),intentional_parent_source_changes=intentional)
inputs['freshness']={'fetch':'successful current interaction','upstream_oid':'fe58918f9eaf2a6f39cdc9c93cfd4ce615ec84bf','incoming_note_commits':[],'pull':'not needed'}
save('engineering-inputs.json',inputs)
records=[]
for row in json.loads((old/'native-build-verification.json').read_text())['variants']:
 command=[s.replace('evidence/scheduler14','evidence/closure15') for s in row['command']];binary=root/command[command.index('-o')+1];logfile=binary.with_suffix('.log')
 with logfile.open('w') as log:r=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 source=next(s for s in command if s.startswith('src/'));assert r.returncode==0
 records.append(dict(command=command,returncode=r.returncode,source_sha256=sha(root/source),log_sha256=sha(logfile),binary_sha256=sha(binary)))
save('native-build-verification.json',{'variants':records})
(out/'frozen-task-plan.md').write_bytes((base/'tasks-closure15.md').read_bytes())
paths=set(json.loads((old/'source-manifest.json').read_text())['input_sha256'])
paths.update(['src/xverse/maestro/'+p for p in ['writer_closure.py','run_closure.py']])
paths.update(['tests/thesis_lite/maestro/'+p for p in ['test_closure.py','closure_fixture.py']])
paths.update(['docs/engineering/maestro-lite/'+p for p in ['ADR-ML3-CLOSURE-0001.md','unit-specification-closure15.md','closure-expected.json','review-closure15.md','verify-closure15.py','evidence/closure15/prepare-verification.py','evidence/closure15/frozen-task-plan.md']])
save('source-manifest.json',{'revision':revision,'parent_commit':parent,'baseline':manifest['accepted_main_baseline'],'input_sha256':{name:sha(root/name) for name in sorted(paths)}})
save('host-environment.json',{'platform':platform.platform(),'uname':list(platform.uname()),'python':platform.python_version(),'cc':subprocess.check_output(['cc','--version'],text=True).splitlines()[0],'wheel_sha256':sha(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl'),'factory_run_created':False,'full_runtime_ready':False})
print(json.dumps({'revision':revision,'frozen_inputs':len(paths),'partial_endpoints':len(reverse),'parent_blobs':len(manifest['candidate_file_sha256'])}))
