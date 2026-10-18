from pathlib import Path
import hashlib,json,subprocess,platform,ast
root=Path('/home/jefferson/xverse-platform-worktrees/maestro-lite-scheduler-20261018')
thesis=Path('/home/jefferson/distributed_safety_critical_thesis')
base=root/'docs/engineering/maestro-lite';out=base/'evidence/scheduler14';old=out.parent/'teardown13'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda n,d:(out/n).write_text(json.dumps(d,indent=2)+'\n')
revision='ML3-SCHEDULER14-2026-10-18-v6';parent='4b1c42753fa8bf874720cf181740db0729d5039c'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==parent
trace=json.loads((out/'working-traceability.json').read_text());trace.update(work_item='ML3-SCHEDULER14',maturity='partial_finite_lifecycle_dispatcher_candidate')
code={
'ML-SR-003':['dispatcher.py::_admissible','schedule_evidence.py::_admissible'],
'ML-SR-004':['dispatcher.py::run','schedule_evidence.py::_control','dispatcher.py::_effect'],
'ML-SR-007':['schedule_evidence.py::_phase_source','dispatcher.py::_effect'],
'ML-SR-008':['dispatcher.py::_service','dispatcher.py::_end','providers.py::_query'],
'ML-SR-009':['dispatcher.py::_service'],
'ML-SR-011':['dispatcher.py::run','dispatcher.py::cancel','owner.py::_dispatch_access'],
'ML-SR-012':['dispatcher.py::_holder','schedule_evidence.py::_handle','persistence.py::schedule_call'],
'ML-SR-013':['dispatcher.py::_cleanup','teardown.py::phase','teardown.py::run'],
'ML-SR-015':['dispatcher.py::run','schedule_evidence.py::pull'],
'ML-SR-016':['schedule_evidence.py::_control','schedule_evidence.py::_m3','dispatcher.py::validate_schedule_reply'],
'ML-SR-018':['dispatcher.py::DispatchResult','dispatcher.py::StepExecution'],
'ML-SR-019':['dispatcher.py::_cleanup','dispatcher.py::run'],
'ML-SR-020':['dispatcher.py::run','persistence.py::schedule_call'],
'ML-SR-022':['dispatcher.py::run'],
'ML-SR-023':['persistence_worker.py::serve'],
'ML-SR-024':['schedule_plan.py::decode_schedule','dispatcher.py::__init__']}
checks={
'ML-SR-003':['test_implicit_horizon_stop_respects_dependencies_before_compiler_rank'],
'ML-SR-004':['test_full_five_phase_dispatch_records_actual_outcomes_and_dispositions','test_duration_defers_step_completion_until_actual_tick','test_missed_tick_window_has_no_fabricated_step_or_probe_success'],
'ML-SR-007':['test_independent_worker_rejects_step_success_without_real_readiness','test_missing_prerequisite_probe_names_the_actual_original_unit'],
'ML-SR-008':['test_paused_ticks_still_service_host_health_and_original_leases','test_missing_prerequisite_probe_names_the_actual_original_unit'],
'ML-SR-009':['test_actual_tick_worker_stall_returns_incomplete_with_owned_cleanup'],
'ML-SR-011':['test_normal_conflict_rejects_without_cancelling_but_operator_cancel_bypasses_locks'],
'ML-SR-012':['test_copied_statement_cannot_issue_original_schedule_rpc','test_invalid_dispatch_scope_rejects_without_release_or_cancellation'],
'ML-SR-013':['test_terminal_service_failure_still_attempts_original_c1_cleanup','test_implicit_horizon_stop_respects_dependencies_before_compiler_rank'],
'ML-SR-015':['test_paused_ticks_still_service_host_health_and_original_leases','test_duration_defers_step_completion_until_actual_tick'],
'ML-SR-016':['test_full_five_phase_dispatch_records_actual_outcomes_and_dispositions','test_bad_schedule_ack_never_becomes_completed_step_authority'],
'ML-SR-018':['test_unexpected_effect_failure_records_honest_dispositions_and_cleanup'],
'ML-SR-019':['test_actual_tick_worker_stall_returns_incomplete_with_owned_cleanup','test_bad_schedule_ack_never_becomes_completed_step_authority','test_terminal_service_failure_still_attempts_original_c1_cleanup'],
'ML-SR-020':['test_actual_tick_worker_stall_returns_incomplete_with_owned_cleanup'],
'ML-SR-022':['test_full_five_phase_dispatch_records_actual_outcomes_and_dispositions'],
'ML-SR-024':['test_actual_remaining_rpc_budget_rejects_before_any_release']}
reverse={}
for row in trace['requirements']:
 for field, refs in [('code',['src/xverse/maestro/'+p for p in code.get(row['id'],[])]),('verification',['tests/thesis_lite/maestro/test_dispatcher.py::'+p for p in checks.get(row['id'],[])])]:
  for endpoint in refs:
   if not any(r['endpoint']==endpoint for r in row[field]):row[field].append({'endpoint':endpoint})
 if row['id']=='ML-SR-013':row['verification'].append({'endpoint':'tests/thesis_lite/maestro/test_schedule_worker.py::test_short_scoped_window_retains_emergency_c1_reserve'})
 for ref in row['code']+row['verification']:
  name,_,symbol=ref['endpoint'].partition('::');path=root/name;ref['file_sha256']=sha(path)
  if symbol and path.suffix=='.py':
   names={n.name for n in ast.walk(ast.parse(path.read_text())) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))};assert symbol in names,ref['endpoint']
  reverse.setdefault(ref['endpoint'],[]).append(row['id'])
 assert not row['full_requirement_closure']
trace['reverse_endpoint_requirements']=reverse
trace.pop('remaining_teardown13_scope',None)
trace['remaining_scheduler14_scope']=['full helper/all-issued-resource closure and global M1/epoch cancellation','initial original-supervisor/authenticated bootstrap-permit and exact environment/dependency admission','controller recovery and explicit restart','U7 pure provisional and independent closed-writer dual coverage','U8 collection and independently reported closure/results','nine full runtime cases; G1/G3/G4/G5; independent full review and explicit acceptance','downstream full phases 4-9']
save('traceability.json',trace)
inputs=json.loads((old/'engineering-inputs.json').read_text())
for name,h in inputs['inputs'].items():assert sha(thesis/name)==h
assert sha(thesis/'notes/dynamic_thesis_notes.md')==inputs['canonical_note_sha256']
mp=thesis/'specs/024-maestro-lite-lifecycle/review/continuation-2026-10-18/teardown13/candidate-manifest.json';manifest=json.loads(mp.read_text())
intentional=['docs/engineering/maestro-lite/README.md']+['src/xverse/maestro/'+p for p in ['lifecycle_evidence.py','owner.py','persistence.py','persistence_worker.py','providers.py','teardown.py','teardown_evidence.py']]
for name,h in manifest['candidate_file_sha256'].items():
 if name not in intentional:assert sha(root/name)==h,name
inputs.update(thesis_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=thesis,text=True).strip(),revision=revision,parent_candidate_commit=parent,parent_manifest_sha256=sha(mp),parent_selected_inputs_verified=len(manifest['candidate_file_sha256']),intentional_parent_source_changes=intentional)
save('engineering-inputs.json',inputs)
records=[]
for row in json.loads((old/'native-build-verification.json').read_text())['variants']:
 command=[s.replace('evidence/teardown13','evidence/scheduler14') for s in row['command']];binary=root/command[command.index('-o')+1];logfile=binary.with_suffix('.log')
 with logfile.open('w') as log:r=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 source=next(s for s in command if s.startswith('src/'));assert r.returncode==0
 records.append(dict(command=command,returncode=r.returncode,source_sha256=sha(root/source),log_sha256=sha(logfile),binary_sha256=sha(binary)))
save('native-build-verification.json',{'variants':records})
(out/'frozen-task-plan.md').write_bytes((base/'tasks-scheduler14.md').read_bytes())
paths=set(json.loads((old/'source-manifest.json').read_text())['input_sha256'])
paths.update(['src/xverse/maestro/'+p for p in ['schedule_plan.py','schedule_evidence.py','dispatcher.py']])
paths.update(['tests/thesis_lite/maestro/'+p for p in ['test_schedule_plan.py','test_schedule_worker.py','test_dispatcher.py']])
paths.update(['docs/engineering/maestro-lite/'+p for p in ['ADR-ML3-SCHEDULER-0001.md','unit-specification-scheduler14.md','scheduler-expected.json','review-scheduler14.md','verify-scheduler14.py','evidence/scheduler14/prepare-verification.py','evidence/scheduler14/frozen-task-plan.md']])
save('source-manifest.json',{'revision':revision,'parent_commit':parent,'baseline':manifest['accepted_main_baseline'],'input_sha256':{name:sha(root/name) for name in sorted(paths)}})
save('host-environment.json',{'platform':platform.platform(),'uname':list(platform.uname()),'python':platform.python_version(),'cc':subprocess.check_output(['cc','--version'],text=True).splitlines()[0],'wheel_sha256':sha(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl'),'factory_run_created':False,'full_runtime_ready':False})
print(json.dumps({'revision':revision,'frozen_inputs':len(paths),'partial_endpoints':len(reverse),'parent_blobs':len(manifest['candidate_file_sha256'])}))
