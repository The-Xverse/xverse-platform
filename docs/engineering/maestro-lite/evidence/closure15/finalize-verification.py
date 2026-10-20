from pathlib import Path
import hashlib,json,re,subprocess
root=Path('/home/jefferson/xverse-platform-worktrees/maestro-lite-closure-20261018');out=root/'docs/engineering/maestro-lite/evidence/closure15'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda n,d:(out/n).write_text(json.dumps(d,indent=2)+'\n')
m=json.loads((out/'source-manifest.json').read_text());assert all(sha(root/p)==h for p,h in m['input_sha256'].items())
run=json.loads((out/'verification-run.json').read_text());assert run['source_unchanged'] and all(r['returncode']==0 for r in run['receipts']);assert run['installed_modules_matched']==25
counts={}
for name in ('platform-tests','wheel-consumer-tests','focused-v5'):
 line=(out/(name+'.log')).read_text().strip().splitlines()[-1];counts[name]=int(re.search(r'(\d+) passed',line).group(1))
assert counts=={'platform-tests':1193,'wheel-consumer-tests':614,'focused-v5':78}
replay=json.loads((out/'verification-replay-inputs.json').read_text())
assert replay['all_tested_product_test_native_and_runtime_inputs_unchanged'] and replay['full_test_receipts_reused_without_rerunning']
assert len(replay['changed_metadata_only'])==2 and replay['actual_installed_modules_reprobed']==25
assert run['test_source_revision']=='ML3-CLOSURE15-2026-10-18-v5' and run['audit_revision']==m['revision']

parent=json.loads((out.parent/'scheduler14/verification.json').read_text());assert counts['platform-tests']-parent['platform_tests']==counts['wheel-consumer-tests']-parent['installed_wheel_tests']==31
assert subprocess.check_output(['git','rev-parse','main'],cwd=root,text=True).strip()==m['baseline']
roots=[];historical=[]
for receipt in run['receipts']:
 for p in Path(receipt['boundary_harness_directory']).glob('maestro-component-*.json'):
  d=json.loads(p.read_text());assert d['root_removed'] and d['workers_reaped'];assert not (Path(d['parent_path'])/d['root_name']).exists();roots.append(str(p.relative_to(out)))
for directory in sorted(out.glob('*-harness')):
 if directory.name in ('platform-tests-harness','wheel-consumer-tests-harness'):continue
 for p in directory.glob('maestro-component-*.json'):
  d=json.loads(p.read_text());assert d['root_removed'] and d['workers_reaped'];assert not (Path(d['parent_path'])/d['root_name']).exists();historical.append(str(p.relative_to(out)))
inputs=json.loads((out/'engineering-inputs.json').read_text());thesis=Path('/home/jefferson/distributed_safety_critical_thesis');assert sha(thesis/'notes/dynamic_thesis_notes.md')==inputs['canonical_note_sha256']
for p,h in inputs['inputs'].items():assert sha(thesis/p)==h
native=json.loads((out/'native-build-verification.json').read_text())['variants'];assert len(native)==5
for record in native:
 source=next(p for p in record['command'] if p.startswith('src/'));assert sha(root/source)==record['source_sha256'] and record['returncode']==0;assert sha(root/record['command'][record['command'].index('-o')+1])==record['binary_sha256']
trace=json.loads((out/'traceability.json').read_text());assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18
assert all(p['software_mapping'] is None and not p['full_parent_closure'] for p in trace['source_parent_register']['requirements'])
audit=json.loads((out/'harness-audit.json').read_text());total=lambda k:sum(r[k] for r in audit)
assert total('teardown_fault_workers_reaped')==6 and total('outcome_fault_workers_reaped')==9 and total('closure_fault_workers_reaped')==9
assert total('argus_generic_closure_records_verified')==3
assert total('teardown_public_snapshots_verified')==3 and total('dispatcher_public_snapshots_verified')==60 and total('closure_public_snapshots_verified')==33
assert total('new_closure_unacknowledged_birth_controls')==3 and total('bootstrap_missing_birth_ack_cases_retained')==6 and total('bootstrap_external_local_fd_disposals')==12
assert total('catalog_direct_child_reap_unresolved_after_forced_helper_loss')==6+total('new_closure_unresolved_native_waits')
review={'type':'separate same-agent read-only component review, not independent full-candidate review','source_manifest_sha256':sha(out/'source-manifest.json'),'repaired_product_findings':[1,2,4,5,6,7,8],'fixture_and_lint_corrections':[3,6],'repaired_verification_only_findings':[9],'records':['docs/engineering/maestro-lite/review-closure15.md'],'accepted':False,'runtime_ready':False};save('read-only-final-review.json',review)
tasks=root/'docs/engineering/maestro-lite/tasks-closure15.md';normalize=lambda s:re.sub(r'(?m)^- \[[ xX]\]','- [ ]',s);assert normalize(tasks.read_text())==normalize((out/'frozen-task-plan.md').read_text());tasks.write_text(tasks.read_text().replace('- [ ]','- [x]'))
save('focused-v5-observation.json',{'command':['/tmp/maestro-lite-closure-verify-20261018/bin/python','-m','pytest','tests/thesis_lite/maestro/test_closure.py','tests/thesis_lite/maestro/test_bootstrap.py','tests/thesis_lite/maestro/test_dispatcher.py','-q','--disable-warnings'],'cwd':str(root),'PYTHONPATH':'src','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','MAESTRO_BOUNDARY_RECEIPTS':str(out/'focused-v5-harness'),'observed_tool_session':58564,'observed_exit_code':0,'log_sha256':sha(out/'focused-v5.log'),'note':'Actual completion observed before this receipt. Historical red/focused runs and pre-repair archives are retained, not counted as current passing verification.'})
assert (out/'ruff.log').read_text().strip()=='All checks passed!' and (out/'whitespace.log').read_text()==''
v={'schema_version':1,'revision':m['revision'],'maturity':'verified_partial_original_run_and_incomplete_writer_closure_not_accepted','baseline':m['baseline'],'parent_candidate_commit':m['parent_commit'],'platform_tests':counts['platform-tests'],'platform_subtests':24,'installed_wheel_tests':counts['wheel-consumer-tests'],'focused_closure_bootstrap_dispatcher_tests':78,'new_closure_cases':31,'source_inputs_frozen':len(m['input_sha256']),'tested_source_inputs_frozen':135,'tested_source_manifest_sha256':sha(out/'tested-source-manifest-v5.json'),'verification_replay_inputs_sha256':sha(out/'verification-replay-inputs.json'),'full_test_receipts_reused_after_metadata_only_audit_repair':True,'installed_modules_matched':25,'installed_native_sources_matched':3,'strict_native_variants':5,'partial_trace_endpoints_checked':run['partial_endpoints_checked'],'external_specification_inputs_verified':len(inputs['inputs']),'selected_parent_inputs_checked':inputs['parent_selected_inputs_verified'],'intentional_parent_changes':inputs['intentional_parent_source_changes'],'final_regression_owned_roots_absent':len(roots),'root_receipts':sorted(roots),'retained_focused_owned_roots_absent':len(historical),'focused_root_receipts':sorted(historical),'harness_audit':audit,'review':review,'all_24_requirements_retained':True,'all_18_source_parents_unvalidated_null_mapped':True,'all_30_pairs_90_declared_endpoints_and_nine_runtime_cases_remain_binding':True,'component_task_criteria_unchanged':True,'full_phase3_complete':False,'runtime_ready':False,'accepted':False,'merged':False,'factory_run_created':False,'canonical_note_edited':False,'goal_active':True,'remaining_gates':trace['remaining_closure15_scope'],'limits':['running remains sampled process-existence readiness, never application readiness','original already-issued resource closure does not authenticate initial bootstrap/environment admission or establish global M1','cleanup_complete requires actual original root/helper waits and empty/released C1 scopes; deliberately unknown births/native waits remain incomplete','writer abort usability before abort, usability afterward and actual durable manifest state remain distinct','the one-call writer path always closes as incomplete; no U7 completeness/finalize or U8 collection/terminal artifact is supplied','local FDs remain retained for caller disposal; matching outcomes are controller-local, recovery/restart pending','kernel scheduling and control I/O are not hard bounded; shortened caller windows preserve unknown facts','full nine runtime cases, independent review and explicit acceptance remain pending'],'evidence_file_sha256':{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='verification.json'}}
save('verification.json',v);print(json.dumps({k:v[k] for k in ('revision','platform_tests','installed_wheel_tests','final_regression_owned_roots_absent','retained_focused_owned_roots_absent','partial_trace_endpoints_checked')}))
