from pathlib import Path
import ast, hashlib, json, subprocess, platform
root=Path('/home/jefferson/xverse-platform-worktrees/maestro-lite-provider-20261018')
thesis=Path('/home/jefferson/distributed_safety_critical_thesis')
out=root/'docs/engineering/maestro-lite/evidence/provider11'
old=out.parent/'bootstrap10'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda name,data:(out/name).write_text(json.dumps(data,indent=2)+'\n')
revision='ML3-PROVIDER11-2026-10-18-v4'
parent='a31d09367a7c5c02f909b04e5bcab658863d28a3'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==parent
# Preserve all original feature/source-parent allocations; refresh exact endpoint bytes.
trace=json.loads((old/'traceability.json').read_text())
trace.update(work_item='ML3-PROVIDER11',maturity='partial_original_process_readiness_dependency_admission_candidate')
newcode={
 'ML-SR-007':['ProcessReadiness','_check_prerequisites','_query','_fresh','DependencyGuard'],
 'ML-SR-008':['check_health','next_health_deadline','cancel'],
 'ML-SR-009':['ProbePolicy','_query','start'],
 'ML-SR-012':['bind','_bound','_holder'],
 'ML-SR-024':['ProcessReadiness','ProbePolicy']}
newtests={
 'ML-SR-007':['test_real_current_generation_probe_precedes_dependent_release','test_failed_prerequisite_cannot_release_dependent','test_expired_actual_reply_cannot_be_reused','test_step_dependency_without_flow_still_blocks_dependent','test_query_exhaustion_is_not_ready_and_never_releases_twice'],
 'ML-SR-008':['test_sampled_health_loss_invalidates_ready','test_external_cancel_invalidates_exposed_snapshots'],
 'ML-SR-009':['test_exact_identity_and_deadline_rejections_before_dispatch','test_local_coordinator_storage_owner_is_not_bounded_provider_admission'],
 'ML-SR-012':['test_exact_identity_and_deadline_rejections_before_dispatch','test_bootstrap_public_session_label_checked_before_dispatch','test_fabricated_dependency_guard_rejected_before_release'],
 'ML-SR-024':['test_invalid_policy_values','test_all_policy_domains_are_finite_and_explicit','test_complete_admitted_policy_set_and_running_catalog_condition']}
reverse={}
for row in trace['requirements']:
 for sym in newcode.get(row['id'],[]):row['code'].append({'endpoint':'src/xverse/maestro/providers.py::'+sym})
 for sym in newtests.get(row['id'],[]):row['verification'].append({'endpoint':'tests/thesis_lite/maestro/test_provider.py::'+sym})
 for ref in row['code']+row['verification']:
  name=ref['endpoint'].partition('::')[0]
  ref['file_sha256']=sha(root/name)
  reverse.setdefault(ref['endpoint'],[]).append(row['id'])
 assert not row['full_requirement_closure']
trace['reverse_endpoint_requirements']=reverse
trace['remaining_provider11_scope']=['full normal M3/Argus outcomes','autonomous finite tick/health scheduler','initial helper admission and authenticated durable bootstrap permits','reverse teardown/restart/recovery','U7/U8','full M1/runtime and independent review/acceptance']
save('traceability.json',trace)
inputs=json.loads((old/'engineering-inputs.json').read_text())
for name,h in inputs['inputs'].items():assert sha(thesis/name)==h,name
assert sha(thesis/'notes/dynamic_thesis_notes.md')==inputs['canonical_note_sha256']
manifest_path=thesis/'specs/024-maestro-lite-lifecycle/review/continuation-2026-10-18/bootstrap10/candidate-manifest.json'
manifest=json.loads(manifest_path.read_text())
intentional=['docs/engineering/maestro-lite/README.md','src/xverse/maestro/owner.py','src/xverse/maestro/bootstrap.py']
for name,h in manifest['candidate_file_sha256'].items():
 if name not in intentional:assert sha(root/name)==h,name
inputs.update(thesis_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=thesis,text=True).strip(),revision=revision,parent_candidate_commit=parent,parent_manifest_sha256=sha(manifest_path),parent_selected_inputs_verified=len(manifest['candidate_file_sha256']),intentional_parent_source_changes=intentional)
save('engineering-inputs.json',inputs)
# Five strict native build variants, all exact source resources preserved.
variants=json.loads((old/'native-build-verification.json').read_text())['variants']
records=[]
for record in variants:
 command=[s.replace('evidence/bootstrap10','evidence/provider11') for s in record['command']]
 binary=root/command[command.index('-o')+1]
 logfile=binary.with_suffix('.log')
 with logfile.open('w') as log:result=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 source=next(s for s in command if s.startswith('src/'))
 assert result.returncode==0
 records.append(dict(command=command,returncode=result.returncode,source_sha256=sha(root/source),log_sha256=sha(logfile),binary_sha256=sha(binary)))
save('native-build-verification.json',{'variants':records})
# Freeze input bytes before installed/source regressions. Mutable task flags excluded.
task=root/'docs/engineering/maestro-lite/tasks-provider11.md'
(out/'frozen-task-plan.md').write_bytes(task.read_bytes())
paths=set(json.loads((old/'source-manifest.json').read_text())['input_sha256'])
paths.update(['src/xverse/maestro/providers.py','tests/thesis_lite/maestro/test_provider.py','docs/engineering/maestro-lite/ADR-ML3-PROVIDER-0001.md','docs/engineering/maestro-lite/unit-specification-provider11.md','docs/engineering/maestro-lite/provider-expected.json','docs/engineering/maestro-lite/review-provider11.md','docs/engineering/maestro-lite/verify-provider11.py','docs/engineering/maestro-lite/evidence/provider11/prepare-verification.py','docs/engineering/maestro-lite/evidence/provider11/frozen-task-plan.md'])
save('source-manifest.json',{'revision':revision,'parent_commit':parent,'baseline':manifest['accepted_main_baseline'],'input_sha256':{name:sha(root/name) for name in sorted(paths)}})
save('host-environment.json',{'platform':platform.platform(),'uname':list(platform.uname()),'python':platform.python_version(),'cc':subprocess.check_output(['cc','--version'],text=True).splitlines()[0],'wheel_sha256':sha(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl'),'factory_run_created':False,'full_runtime_ready':False})
print(json.dumps({'revision':revision,'frozen_inputs':len(paths),'partial_endpoints':len(reverse),'parent_blobs':len(manifest['candidate_file_sha256'])}))
