from pathlib import Path
import hashlib,json,re,subprocess
root=Path('/home/jefferson/xverse-platform-worktrees/maestro-lite-teardown-20261018')
out=root/'docs/engineering/maestro-lite/evidence/teardown13'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda n,d:(out/n).write_text(json.dumps(d,indent=2)+'\n')
m=json.loads((out/'source-manifest.json').read_text())
assert all(sha(root/p)==h for p,h in m['input_sha256'].items())
run=json.loads((out/'verification-run.json').read_text())
assert run['source_unchanged'] and all(r['returncode']==0 for r in run['receipts'])
assert run['installed_modules_matched']==20
counts={}
for name in ('platform-tests','wheel-consumer-tests','focused-v4'):
 line=(out/(name+'.log')).read_text().strip().splitlines()[-1]
 counts[name]=int(re.search(r'(\d+) passed',line).group(1))
parent=json.loads((out.parent/'outcomes12/verification.json').read_text())
assert counts['platform-tests']-parent['platform_tests']==counts['wheel-consumer-tests']-parent['installed_wheel_tests']==counts['focused-v4']-58==27
assert subprocess.check_output(['git','rev-parse','main'],cwd=root,text=True).strip()==m['baseline']
roots=[]
for receipt in run['receipts']:
 for p in Path(receipt['boundary_harness_directory']).glob('maestro-component-*.json'):
  d=json.loads(p.read_text());assert d['root_removed'] and d['workers_reaped']
  assert not (Path(d['parent_path'])/d['root_name']).exists()
  roots.append(str(p.relative_to(out)))
focused=[]
for directory in ('focused-v1-harness','focused-v2-harness','focused-v3-harness','focused-v4-harness'):
 paths=list((out/directory).glob('maestro-component-*.json'));assert paths
 for p in paths:
  d=json.loads(p.read_text());assert d['root_removed'] and d['workers_reaped']
  assert not (Path(d['parent_path'])/d['root_name']).exists()
  focused.append(str(p.relative_to(out)))
inputs=json.loads((out/'engineering-inputs.json').read_text());thesis=Path('/home/jefferson/distributed_safety_critical_thesis')
assert sha(thesis/'notes/dynamic_thesis_notes.md')==inputs['canonical_note_sha256']
for p,h in inputs['inputs'].items():assert sha(thesis/p)==h
native=json.loads((out/'native-build-verification.json').read_text())['variants'];assert len(native)==5
for record in native:
 source=next(p for p in record['command'] if p.startswith('src/'))
 assert sha(root/source)==record['source_sha256'] and record['returncode']==0
 assert sha(root/record['command'][record['command'].index('-o')+1])==record['binary_sha256']
trace=json.loads((out/'traceability.json').read_text())
assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18
assert all(p['software_mapping'] is None and not p['full_parent_closure'] for p in trace['source_parent_register']['requirements'])
audit=json.loads((out/'harness-audit.json').read_text())
assert sum(r['teardown_fault_workers_reaped'] for r in audit)==6
assert sum(r['outcome_fault_workers_reaped'] for r in audit)==9
assert sum(r['teardown_public_snapshots_verified'] for r in audit)==3
assert sum(r['deliberately_forced_teardown_issuer_loss_cases'] for r in audit)==3
assert sum(r['catalog_direct_child_reap_unresolved_after_forced_helper_loss'] for r in audit)==6
review={'type':'separate same-agent read-only component review, not independent full-candidate review','source_manifest_sha256':sha(out/'source-manifest.json'),'repaired_findings':[1,2,3,4,7,9],'verification_advisory_8_exercised':True,'issuer_loss_advisory_6_retained':True,'open_full_integration_limitations':[5],'records':['docs/engineering/maestro-lite/review-teardown13.md'],'accepted':False,'runtime_ready':False}
save('read-only-final-review.json',review)
tasks=root/'docs/engineering/maestro-lite/tasks-teardown13.md'
normalize=lambda s:re.sub(r'(?m)^- \[[ xX]\]','- [ ]',s)
assert normalize(tasks.read_text())==normalize((out/'frozen-task-plan.md').read_text())
tasks.write_text(tasks.read_text().replace('- [ ]','- [x]'))
save('focused-v4-observation.json',{'command':['/tmp/maestro-lite-teardown-verify-20261018/bin/python','-m','pytest','tests/thesis_lite/maestro/test_teardown.py','tests/thesis_lite/maestro/test_outcomes.py','tests/thesis_lite/maestro/test_provider.py','-q','--disable-warnings'],'cwd':str(root),'PYTHONPATH':'src','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','MAESTRO_BOUNDARY_RECEIPTS':str(out/'focused-v4-harness'),'observed_tool_session':89450,'observed_exit_code':0,'log_sha256':sha(out/'focused-v4.log'),'note':'Receipt written after observing actual shell completion; historical v1-v3 logs are retained failure/success controls, not current candidate verification.'})
v={'schema_version':1,'revision':m['revision'],'maturity':'verified_partial_reverse_unit_teardown_candidate_not_accepted','baseline':m['baseline'],'parent_candidate_commit':m['parent_commit'],'platform_tests':counts['platform-tests'],'platform_subtests':24,'installed_wheel_tests':counts['wheel-consumer-tests'],'focused_teardown_outcomes_provider_tests':85,'new_teardown_cases':27,'source_inputs_frozen':len(m['input_sha256']),'installed_modules_matched':20,'installed_native_sources_matched':3,'strict_native_variants':5,'partial_trace_endpoints_checked':run['partial_endpoints_checked'],'external_specification_inputs_verified':len(inputs['inputs']),'selected_parent_inputs_checked':inputs['parent_selected_inputs_verified'],'intentional_parent_changes':inputs['intentional_parent_source_changes'],'final_regression_owned_roots_absent':len(roots),'root_receipts':sorted(roots),'retained_focused_owned_roots_absent':len(focused),'focused_root_receipts':sorted(focused),'harness_audit':audit,'review':review,'all_24_requirements_retained':True,'all_18_source_parents_unvalidated_null_mapped':True,'all_30_pairs_90_declared_endpoints_and_nine_runtime_cases_remain_binding':True,'component_task_criteria_unchanged':True,'full_phase3_complete':False,'runtime_ready':False,'accepted':False,'merged':False,'factory_run_created':False,'canonical_note_edited':False,'goal_active':True,'remaining_gates':['full helper closure/all-issued-resource integration and global M1/epoch cancellation','original supervisor and authenticated durable bootstrap-permit admission','exact environment/ABI/interpreter/module/library dependency admission','missing-observation failure/disposition and complete declared step records','autonomous finite health/tick/dependency scheduler with call/event admission','restart/controller recovery','U7 dual coverage and U8 collection/results','nine full runtime cases','G1/G3/G4/G5, independent full review and explicit acceptance','full phases 4-9 Lite functionality'],'limits':['running is sampled process-existence readiness, never application readiness','caller drives health; no continuous or atomic multi-unit health guarantee','ReverseTeardown operates on already-issued original unit resources; full helper/run closure is pending','local start barrier is not full M1/global epoch cancellation proof','matching stop cache is controller-local; controller-loss reconstruction remains pending','unacknowledged births and deliberately forced launcher-loss child reap remain unresolved','kernel scheduling and control I/O stalls are not hard bounded','inherited private 128-request cap requires explicit full-scheduler budget admission'],'evidence_file_sha256':{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='verification.json'}}
save('verification.json',v)
print(json.dumps({k:v[k] for k in ('revision','platform_tests','installed_wheel_tests','final_regression_owned_roots_absent','retained_focused_owned_roots_absent','partial_trace_endpoints_checked')}))
