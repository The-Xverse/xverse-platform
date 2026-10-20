from pathlib import Path
import hashlib,json,re,subprocess
root=Path('/home/jefferson/xverse-platform-worktrees/maestro-lite-bootstrap-20261018')
out=root/'docs/engineering/maestro-lite/evidence/bootstrap10'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda name,data:(out/name).write_text(json.dumps(data,indent=2)+'\n')
m=json.loads((out/'source-manifest.json').read_text())
assert all(sha(root/p)==h for p,h in m['input_sha256'].items())
run=json.loads((out/'verification-run.json').read_text())
assert run['source_unchanged'] and all(r['returncode']==0 for r in run['receipts'])
assert run['receipts'][0]['PYTHONPATH']==str(root/'src') and run['receipts'][1]['PYTHONPATH']=='unset'
audit=json.loads((out/'harness-audit.json').read_text())
roots=[]
for receipt in run['receipts']:
 for p in Path(receipt['boundary_harness_directory']).glob('maestro-component-*.json'):
  d=json.loads(p.read_text());assert d['root_removed'] and d['workers_reaped']
  assert not (Path(d['parent_path'])/d['root_name']).exists()
  roots.append(str(p.relative_to(out)))
assert subprocess.check_output(['git','rev-parse','main'],cwd=root,text=True).strip()=='c2997c0f810d117cf45b2e34a4011b3ba7219494'
inputs=json.loads((out/'engineering-inputs.json').read_text());thesis=Path('/home/jefferson/distributed_safety_critical_thesis')
assert sha(thesis/'notes/dynamic_thesis_notes.md')==inputs['canonical_note_sha256']
for p,h in inputs['inputs'].items():assert sha(thesis/p)==h
native=json.loads((out/'native-build-verification.json').read_text())['variants'];assert len(native)==5
for record in native:
 source=next(p for p in record['command'] if p.startswith('src/'))
 assert sha(root/source)==record['source_sha256'] and record['returncode']==0
counts={}
for name in ('platform-tests','wheel-consumer-tests','focused-v4-tests'):
 line=(out/(name+'.log')).read_text().strip().splitlines()[-1]
 counts[name]=int(re.search(r'(\d+) passed',line).group(1))
parent=json.loads((out.parent/'launcher9/verification.json').read_text())
bootstrap_cases=counts['platform-tests']-parent['platform_tests']
assert bootstrap_cases==counts['wheel-consumer-tests']-parent['installed_wheel_tests']==counts['focused-v4-tests']-22==29
assert run['installed_modules_matched']==16
trace=json.loads((out/'traceability.json').read_text());assert len(trace['requirements'])==24
assert len(trace['source_parent_register']['requirements'])==18
assert all(p['software_mapping'] is None and not p['full_parent_closure'] for p in trace['source_parent_register']['requirements'])
review={'review_type':'separate same-agent read-only component review; not independent full-candidate review','revision':m['revision'],'source_manifest_sha256':sha(out/'source-manifest.json'),'findings_recorded_before_repairs':13,'repaired_findings':list(range(1,14)),'open_minor_findings':[14],'launcher_finding_10_resolved':True,'rejected_v2_source_evidence':'pre-repair-v3.tar.gz','rejected_v3_source_evidence':'pre-repair-v4.tar.gz','read_only_records':['docs/engineering/maestro-lite/review-bootstrap10.md','docs/engineering/maestro-lite/review-bootstrap10-follow-ups.md'],'actual_negative_probes':['pidfd-identity-probe.log','borrowed-signal-probe.log'],'source_and_installed_regressions_repeated_after_final_signal_repair':True,'accepted':False,'merged':False,'runtime_ready':False}
save('read-only-final-review.json',review)
# Task criteria are immutable inputs; completion flags are a separate progress record.
tasks=root/'docs/engineering/maestro-lite/tasks-bootstrap10.md'
normalize=lambda s:re.sub(r'(?m)^- \[[ xX]\]', '- [ ]',s)
assert normalize(tasks.read_text())==normalize((out/'frozen-task-plan.md').read_text())
tasks.write_text(tasks.read_text().replace('- [ ]','- [x]'))
verification={'schema_version':1,'revision':m['revision'],'maturity':'verified_partial_supervised_helper_bootstrap_original_child_capability_candidate_not_accepted','baseline':'c2997c0f810d117cf45b2e34a4011b3ba7219494','parent_candidate_commit':'9616ec973188bb392b3b820c584ba90be47ac210','platform_tests':counts['platform-tests'],'platform_subtests':24,'installed_wheel_tests':counts['wheel-consumer-tests'],'focused_bootstrap_and_launcher_tests':counts['focused-v4-tests'],'new_bootstrap_cases':bootstrap_cases,'source_inputs_frozen':len(m['input_sha256']),'installed_modules_matched':16,'installed_native_sources_matched':3,'strict_native_variants':5,'partial_trace_endpoints_checked':run['partial_endpoints_checked'],'external_specification_inputs_verified':len(inputs['inputs']),'selected_parent_inputs_checked':inputs['parent_selected_inputs_verified'],'intentional_parent_changes':inputs['intentional_parent_source_changes'],'final_regression_owned_roots_absent':len(roots),'root_receipts':sorted(roots),'harness_audit':audit,'review':review,'all_24_requirements_retained':True,'all_18_source_parents_unvalidated_null_mapped':True,'all_30_pairs_90_declared_endpoints_and_nine_runtime_cases_remain_binding':True,'component_task_criteria_unchanged':True,'component_progress_record':str(tasks.relative_to(root)),'full_phase3_tasks_complete':False,'runtime_ready':False,'accepted':False,'merged':False,'factory_run_created':False,'canonical_note_edited':False,'goal_active':True,'remaining_gates':['minor public-session label pin (finding 14)','independent original supervisor creation/admission and durable bootstrap-permit authentication/consumption','exact tested environment/ABI and interpreter/module/shared-library dependency admission','complete original-owner/guard-loss/M1 and kernel-stall limitations','provider facade/current-generation readiness/health and dependency scheduling','reverse lifecycle teardown/restart/recovery/normal M3 outcomes','U7/U8 evidence obligations/coverage/collection/results','G1/G3/G4/G5, nine full-runtime cases, independent full review and explicit acceptance'],'limits':['registered helper reaping does not prove workload direct-child or descendant reaping','lost birth ACK remains unresolved, including separate external local-FD disposal','forced launcher-helper loss retains unresolved workload direct-child reap; C1 kill/empty/release is separate','helper activation/unfreeze/exec observations confer no lifecycle readiness or success','original supervisor and artifact/input sealing require external supervised admission; no recursive bootstrap bound claimed','own-process KCMP_FILE availability is mandatory; tested x86-64 only','kernel scheduling/I/O stalls are not hard bounded','scientific protocol and dissertation results are unchanged'],'evidence_file_sha256':{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='verification.json'}}
save('verification.json',verification)
print(json.dumps({k:verification[k] for k in ('revision','platform_tests','installed_wheel_tests','new_bootstrap_cases','final_regression_owned_roots_absent','partial_trace_endpoints_checked')}))
