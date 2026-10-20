from pathlib import Path
import hashlib,json,ast
root=Path('/home/jefferson/xverse-platform-worktrees/maestro-lite-scheduler-20261018');out=root/'docs/engineering/maestro-lite/evidence/scheduler14'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
trace=json.loads((out.parent/'teardown13/traceability.json').read_text())
trace.update(work_item='ML3-SCHEDULER14-WORKING',maturity='uncommitted_partial_foundations_full_dispatcher_pending',runtime_ready=False,trusted_whole_project_trace_validated=False)
code={
'ML-SR-004':['schedule_plan.py::admit_schedule'],
'ML-SR-008':['providers.py::next_health_deadline','teardown.py::_stop'],
'ML-SR-009':['persistence.py::_rpc','persistence_worker.py::serve'],
'ML-SR-010':['owner.py::renew'],
'ML-SR-011':['teardown.py::phase'],
'ML-SR-012':['teardown.py::_jobs'],
'ML-SR-013':['teardown.py::_stop','teardown.py::_cleanup','teardown.py::phase'],
'ML-SR-015':['schedule_plan.py::admit_schedule','schedule_evidence.py::pull','schedule_evidence.py::record'],
'ML-SR-016':['schedule_evidence.py::_append','lifecycle_evidence.py::reserve_event'],
'ML-SR-019':['persistence.py::_rpc'],
'ML-SR-022':['teardown.py::phase'],
'ML-SR-023':['persistence.py::encode_configuration'],
'ML-SR-024':['schedule_plan.py::decode_schedule']}
checks={
'ML-SR-004':['test_schedule_plan.py::test_exact_pure_admission_and_round_trip','test_schedule_plan.py::test_invalid_admission_rejects'],
'ML-SR-008':['test_schedule_worker.py::test_first_release_without_sample_has_no_invented_health_deadline','test_schedule_worker.py::test_scoped_stop_and_cleanup_keep_other_unit_health_and_repeat_facts'],
'ML-SR-009':['test_schedule_worker.py::test_original_worker_rejects_tick_state_forgery'],
'ML-SR-010':['test_schedule_worker.py::test_original_native_gate_renewal_updates_only_after_exact_ack','test_schedule_worker.py::test_invalid_gate_renewal_has_no_release_or_lease_change'],
'ML-SR-011':['test_schedule_worker.py::test_scoped_phase_rejects_prerequisite_or_premature_cleanup_without_effect'],
'ML-SR-012':['test_schedule_worker.py::test_scoped_stop_and_cleanup_keep_other_unit_health_and_repeat_facts'],
'ML-SR-013':['test_schedule_worker.py::test_scoped_stop_and_cleanup_keep_other_unit_health_and_repeat_facts'],
'ML-SR-015':['test_schedule_worker.py::test_actual_supervised_tick_pauses_interleave_with_durable_health','test_schedule_worker.py::test_original_worker_rejects_tick_state_forgery'],
'ML-SR-016':['test_schedule_worker.py::test_actual_supervised_tick_pauses_interleave_with_durable_health'],
'ML-SR-019':['test_schedule_worker.py::test_original_worker_rejects_tick_state_forgery'],
'ML-SR-022':['test_schedule_worker.py::test_scoped_stop_and_cleanup_keep_other_unit_health_and_repeat_facts'],
'ML-SR-023':['test_schedule_worker.py::test_legacy_session_keeps_original_cap_and_rejects_tick'],
'ML-SR-024':['test_schedule_plan.py::test_worker_rederives_instead_of_trusting_serialized_budget','test_schedule_plan.py::test_admission_itself_has_no_storage_or_process_effect']}
reverse={}
for row in trace['requirements']:
 for p in code.get(row['id'],[]):
  ref={'endpoint':'src/xverse/maestro/'+p}
  if not any(r['endpoint']==ref['endpoint'] for r in row['code']):row['code'].append(ref)
 for p in checks.get(row['id'],[]):
  ref={'endpoint':'tests/thesis_lite/maestro/'+p}
  if not any(r['endpoint']==ref['endpoint'] for r in row['verification']):row['verification'].append(ref)
 for ref in row['code']+row['verification']:
  name,_,symbol=ref['endpoint'].partition('::');path=root/name;ref['file_sha256']=sha(path)
  if symbol and path.suffix=='.py':
   names={n.name for n in ast.walk(ast.parse(path.read_text())) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))};assert symbol in names,ref['endpoint']
  reverse.setdefault(ref['endpoint'],[]).append(row['id'])
 assert not row['full_requirement_closure']
trace['reverse_endpoint_requirements']=reverse
trace['remaining_scheduler14_scope']=['full original FiniteDispatcher across all declared phases, windows, durations and dependency ordering','normal step validation/dispatch/outcome AND terminal disposition evidence; amend event admission to cover all separate annotations before Release','bounded missing-observation diagnostics (one per unit) and unit/run dispositions','automatic host health/lease scheduling independent of tick pauses','normal tick completion verification against actual completed/pending steps','typed original dispatcher/active-step client requests and validated receipts','full source/installed-wheel regression, separate final read-only review, stable source and thesis commits']
assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18
(out/'working-traceability.json').write_text(json.dumps(trace,indent=2)+'\n')
print(json.dumps({'partial_trace_endpoints':len(reverse),'full_requirement_closure':False}))
