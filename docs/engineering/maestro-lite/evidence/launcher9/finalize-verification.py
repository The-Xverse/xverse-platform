from pathlib import Path
import json, hashlib, re, subprocess
root = Path('/home/jefferson/xverse-platform-worktrees/maestro-lite-launcher-20261018')
out = root / 'docs/engineering/maestro-lite/evidence/launcher9'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
save = lambda name, data: (out/name).write_text(json.dumps(data, indent=2)+'\n')
manifest = json.loads((out/'source-manifest.json').read_text())
assert all(sha(root/p)==h for p,h in manifest['input_sha256'].items())
run = json.loads((out/'verification-run.json').read_text())
assert run['source_unchanged'] and all(r['returncode']==0 for r in run['receipts'])
assert run['receipts'][0]['PYTHONPATH']==str(root/'src')
assert run['receipts'][1]['PYTHONPATH']=='unset'
audit = json.loads((out/'harness-audit.json').read_text())
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
for record in json.loads((out/'native-build-verification.json').read_text())['variants']:
 source=next(p for p in record['command'] if p.startswith('src/'))
 assert sha(root/source)==record['source_sha256'] and record['returncode']==0
review={
 'review_type':'separate same-agent read-only component review; not independent full-candidate review',
 'revision':manifest['revision'],'source_manifest_sha256':sha(out/'source-manifest.json'),
 'findings_recorded_before_successor_repairs':9,'repaired_findings':list(range(1,10)),
 'open_minor_documentation_findings':[10],
 'review_records':['docs/engineering/maestro-lite/review-launcher9.md','docs/engineering/maestro-lite/review-launcher9-regression.md','docs/engineering/maestro-lite/review-launcher9-follow-ups.md'],
 'rejected_v2_source_and_evidence':'pre-repair-v3.tar.gz',
 'final_source_frozen':True,'full_source_and_copied_installed_regressions_passed':True,
 'all_final_regression_owned_roots_absent':len(roots),'accepted':False,'merged':False,'runtime_ready':False,
}
save('read-only-final-review.json',review)
counts={}
for name in ('platform-tests','wheel-consumer-tests','focused-v3-tests'):
 tail=(out/(name+'.log')).read_text().strip().splitlines()[-1]
 counts[name]=int(re.search(r'(\d+) passed',tail).group(1))
assert counts['focused-v3-tests']==22
trace=json.loads((out/'traceability.json').read_text());assert len(trace['requirements'])==24
parents=trace['source_parent_register']['requirements'];assert len(parents)==18
assert all(p['software_mapping'] is None and not p['full_parent_closure'] for p in parents)
verification={
 'schema_version':1,'revision':manifest['revision'],
 'maturity':'verified_partial_catalog_native_launcher_original_registry_candidate_not_accepted',
 'baseline':'c2997c0f810d117cf45b2e34a4011b3ba7219494',
 'parent_candidate_commit':'53c4e779b2835cd6b05a8e90ddd77d0956b57340',
 'platform_tests':counts['platform-tests'],'platform_subtests':24,
 'installed_wheel_tests':counts['wheel-consumer-tests'],'focused_launcher_tests':22,
 'source_inputs_frozen':len(manifest['input_sha256']),
 'installed_modules_matched':run['installed_modules_matched'],
 'installed_native_sources_matched':2,'strict_native_variants':4,
 'partial_trace_endpoints_checked':run['partial_endpoints_checked'],
 'external_specification_inputs_verified':len(inputs['inputs']),
 'selected_parent_inputs_checked':inputs['parent_selected_inputs_verified'],
 'intentional_parent_changes':inputs['intentional_parent_source_changes'],
 'final_regression_owned_roots_absent':len(roots),'root_receipts':sorted(roots),
 'harness_audit':audit,'review':review,
 'all_24_requirements_retained':True,'all_18_source_parents_unvalidated_null_mapped':True,
 'all_30_pairs_90_declared_endpoints_and_nine_runtime_cases_remain_binding':True,
 'runtime_ready':False,'accepted':False,'merged':False,'factory_run_created':False,
 'canonical_note_edited':False,'goal_active':True,
 'completed_precommit_tasks':['catalog_native_stage_exec_and_original_registry','actual_C1_bound_one_use_Release','22_positive_negative_late_storage_and_cleanup_cases','separate_reviews_and_successor_repairs','exact_source_wheel_and_partial_trace_regressions'],
 'remaining_gates':['trusted independently supervised helper bootstrap and helper/dependency/environment/FD admission','complete original-owner/guard-loss/M1 fencing and kernel-bound limitations','provider facade, current-generation probes/readiness and dependency scheduling','reverse lifecycle teardown, restart/recovery and normal M3 outcomes','U7/U8 evidence obligations, coverage, collection and results','G1/G3/G4/G5, nine actual-runtime cases, independent full review and explicit acceptance','minor docstring clarification recorded as finding 10'],
 'limits':['native direct-child reaping does not prove descendant/tree cleanup','unfreeze and exec observations confer no lifecycle readiness or success','component storage-after-Arm case does not close the full nine-case runtime matrix','kernel scheduling and I/O stalls are not hard bounded','scientific protocol and dissertation results are unchanged'],
 'evidence_file_sha256':{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='verification.json'},
}
save('verification.json',verification)
print(json.dumps({k:verification[k] for k in ['revision','platform_tests','installed_wheel_tests','final_regression_owned_roots_absent','partial_trace_endpoints_checked']}))
