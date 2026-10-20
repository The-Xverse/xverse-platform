from pathlib import Path
import hashlib,json,subprocess,platform,ast
root=Path('/home/jefferson/xverse-platform-worktrees/maestro-lite-recovery-20261018')
thesis=Path('/home/jefferson/distributed_safety_critical_thesis')
base=root/'docs/engineering/maestro-lite';out=base/'evidence/recovery16';old=out.parent/'closure15'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda n,d:(out/n).write_text(json.dumps(d,indent=2)+'\n')
revision='ML3-RECOVERY16-2026-10-18-v3';parent='6083439ad3443a79487f4a6a5f8962eeb2973efa'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==parent
trace=json.loads((old/'traceability.json').read_text());trace.update(work_item='ML3-RECOVERY16',maturity='partial_surviving_original_supervisor_reconciliation_candidate')
code={
'ML-SR-006':['recovery.py::_until'],
'ML-SR-007':['recovery.py::reconcile','providers.py::check_unit_health','dispatcher.py::_effect'],
'ML-SR-008':['recovery.py::_query','providers.py::check_unit_health'],
'ML-SR-011':['recovery.py::cancel','recovery.py::reconcile'],
'ML-SR-012':['recovery.py::_holder','owner.py::_view_registry'],
'ML-SR-013':['recovery.py::reconcile'],
'ML-SR-014':['recovery.py::IssuerRecovery','recovery.py::validate_snapshot','recovery_evidence.py::snapshot','owner.py::_retire_views','owner.py::_start_access','persistence.py::reconcile_snapshot'],
'ML-SR-016':['recovery.py::reconcile'],
'ML-SR-018':['recovery_evidence.py::snapshot'],
'ML-SR-019':['recovery.py::reconcile'],
'ML-SR-020':['recovery.py::ReconciliationResult'],
'ML-SR-022':['recovery.py::RecoverySource'],
'ML-SR-023':['providers.py::_holder'],
'ML-SR-024':['recovery.py::__init__']}
checks={
'ML-SR-006':['test_changed_host_session_rejects_without_borrowing_old_freshness'],
'ML-SR-007':['test_real_rpc_capacity_is_checked_before_retirement_on_both_sides'],
'ML-SR-008':['test_real_original_native_query_stall_returns_unknown_and_cleanup_only'],
'ML-SR-011':['test_normal_recovery_conflict_has_no_retirement_or_cancellation','test_recovery_lock_covers_failure_cleanup_and_cancel_remains_independent'],
'ML-SR-012':['test_original_recovery_object_is_not_an_authority_after_fork','test_copied_active_recovery_statement_cannot_authorize_snapshot_rpc','test_replacement_owner_cannot_adopt_original_issuer_objects'],
'ML-SR-013':['test_staged_handle_without_normal_durable_outcome_is_cleanup_only','test_dead_original_native_issuer_never_becomes_replacement_ownership'],
'ML-SR-014':['test_original_two_unit_recovery_retires_old_view_and_requires_new_health','test_reconstruction_calls_no_start_stage_claim_or_new_writer','test_reconstructed_view_and_original_owner_never_reopen_start'],
'ML-SR-016':['test_reconstructed_view_and_original_owner_never_reopen_start'],
'ML-SR-018':['test_durable_or_exact_handle_loss_blocks_recovery_and_preserves_original_cleanup'],
'ML-SR-019':['test_actual_storage_stall_cannot_restore_old_positive_evidence'],
'ML-SR-020':['test_bad_original_snapshot_ack_never_restores_an_observation_view'],
'ML-SR-022':['test_original_two_unit_recovery_retires_old_view_and_requires_new_health'],
'ML-SR-023':['test_original_two_unit_recovery_retires_old_view_and_requires_new_health'],
'ML-SR-024':['test_invalid_recovery_operation_budget_has_no_effect']}
reverse={}
for row in trace['requirements']:
 for field, refs in [('code',['src/xverse/maestro/'+p for p in code.get(row['id'],[])]),('verification',['tests/thesis_lite/maestro/test_recovery.py::'+p for p in checks.get(row['id'],[])])]:
  for endpoint in refs:
   if not any(r['endpoint']==endpoint for r in row[field]):row[field].append({'endpoint':endpoint})
 if row['id'] in ('ML-SR-007','ML-SR-008','ML-SR-011','ML-SR-023'):
  for test in ('test_scheduled_observe_queries_only_its_declared_original_unit','test_targeted_health_input_and_lock_conflicts_preserve_original_readiness'):
   row['verification'].append({'endpoint':'tests/thesis_lite/maestro/test_dispatch_observe.py::'+test})
 for ref in row['code']+row['verification']:
  name,_,symbol=ref['endpoint'].partition('::');path=root/name;ref['file_sha256']=sha(path)
  if symbol and path.suffix=='.py':
   names={n.name for n in ast.walk(ast.parse(path.read_text())) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))};assert symbol in names,ref['endpoint']
  reverse.setdefault(ref['endpoint'],[]).append(row['id'])
 assert not row['full_requirement_closure']
trace['reverse_endpoint_requirements']=reverse
trace.pop('remaining_closure15_scope',None)
trace['remaining_recovery16_scope']=['initial original-supervisor/authenticated bootstrap-permit and exact environment/dependency admission','full M1/global epoch cancellation and independent supervision across all control paths','full cross-process controller recovery with independently surviving broker/admission and explicit fresh-generation restart; same-supervisor reconciliation is partial','U7 pure provisional and independent closed-writer dual coverage','U8 confined collection, bounded terminal-report artifact and independently reported closure/results','nine full runtime cases; G1/G3/G4/G5; independent full review and explicit acceptance','downstream full phases 4-9']
save('traceability.json',trace)
inputs=json.loads((old/'engineering-inputs.json').read_text())
for name,h in inputs['inputs'].items():assert sha(thesis/name)==h
assert sha(thesis/'notes/dynamic_thesis_notes.md')==inputs['canonical_note_sha256']
mp=thesis/'specs/024-maestro-lite-lifecycle/review/continuation-2026-10-18/closure15/candidate-manifest.json';manifest=json.loads(mp.read_text())
intentional=['docs/engineering/maestro-lite/README.md','src/xverse/maestro/owner.py','src/xverse/maestro/providers.py','src/xverse/maestro/dispatcher.py','src/xverse/maestro/persistence.py','src/xverse/maestro/persistence_worker.py']
for name,h in manifest['candidate_file_sha256'].items():
 if name not in intentional:assert sha(root/name)==h,name
inputs.update(thesis_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=thesis,text=True).strip(),revision=revision,parent_candidate_commit=parent,parent_manifest_sha256=sha(mp),parent_selected_inputs_verified=len(manifest['candidate_file_sha256']),intentional_parent_source_changes=intentional)
inputs['freshness']={'fetch':'successful current interaction','upstream_oid':'fe58918f9eaf2a6f39cdc9c93cfd4ce615ec84bf','incoming_note_commits':[],'pull':'not needed'}
save('engineering-inputs.json',inputs)
records=[]
for row in json.loads((old/'native-build-verification.json').read_text())['variants']:
 command=[s.replace('evidence/closure15','evidence/recovery16') for s in row['command']];binary=root/command[command.index('-o')+1];logfile=binary.with_suffix('.log')
 with logfile.open('w') as log:r=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 source=next(s for s in command if s.startswith('src/'));assert r.returncode==0
 records.append(dict(command=command,returncode=r.returncode,source_sha256=sha(root/source),log_sha256=sha(logfile),binary_sha256=sha(binary)))
save('native-build-verification.json',{'variants':records})
(out/'frozen-task-plan.md').write_bytes((base/'tasks-recovery16.md').read_bytes())
paths=set(json.loads((old/'source-manifest.json').read_text())['input_sha256'])
paths.update(['src/xverse/maestro/'+p for p in ['recovery.py','recovery_evidence.py']])
paths.update(['tests/thesis_lite/maestro/'+p for p in ['test_recovery.py','test_dispatch_observe.py']])
paths.update(['docs/engineering/maestro-lite/'+p for p in ['ADR-ML3-RECOVERY-0001.md','unit-specification-recovery16.md','recovery-expected.json','review-recovery16.md','verify-recovery16.py','evidence/recovery16/prepare-verification.py','evidence/recovery16/frozen-task-plan.md','evidence/recovery16/verify-serialized-source.py']])
save('source-manifest.json',{'revision':revision,'parent_commit':parent,'baseline':manifest['accepted_main_baseline'],'input_sha256':{name:sha(root/name) for name in sorted(paths)}})
save('host-environment.json',{'platform':platform.platform(),'uname':list(platform.uname()),'python':platform.python_version(),'cc':subprocess.check_output(['cc','--version'],text=True).splitlines()[0],'wheel_sha256':sha(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl'),'factory_run_created':False,'full_runtime_ready':False})
print(json.dumps({'revision':revision,'frozen_inputs':len(paths),'partial_endpoints':len(reverse),'parent_blobs':len(manifest['candidate_file_sha256'])}))
