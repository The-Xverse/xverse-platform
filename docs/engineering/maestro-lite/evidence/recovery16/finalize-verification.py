"""Finalize the exact passing component evidence; no acceptance or runtime credit."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

root = Path('/home/jefferson/xverse-platform-worktrees/maestro-lite-recovery-20261018')
out = root / 'docs/engineering/maestro-lite/evidence/recovery16'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, data):
    (out / name).write_text(json.dumps(data, indent=2) + '\n')

manifest = json.loads((out / 'source-manifest.json').read_text())
assert all(sha(root / p) == h for p, h in manifest['input_sha256'].items())
run = json.loads((out / 'verification-run.json').read_text())
assert run['source_unchanged'] and all(r['returncode'] == 0 for r in run['receipts'])
assert run['installed_modules_matched'] == 27
counts = {}
for name in ('platform-tests-v3', 'wheel-consumer-tests-v3', 'focused-v4'):
    last = (out / (name + '.log')).read_text().strip().splitlines()[-1]
    counts[name] = int(re.search(r'(\d+) passed', last).group(1))
assert counts == {'platform-tests-v3': 1226, 'wheel-consumer-tests-v3': 647, 'focused-v4': 117}
assert '24 subtests passed' in (out / 'platform-tests-v3.log').read_text()
parent = json.loads((out.parent / 'closure15/verification.json').read_text())
assert counts['platform-tests-v3'] - parent['platform_tests'] == counts['wheel-consumer-tests-v3'] - parent['installed_wheel_tests'] == 33
assert subprocess.check_output(['git','rev-parse','main'],cwd=root,text=True).strip() == manifest['baseline']
roots, historical = [], []
final_directories = {Path(r['boundary_harness_directory']) for r in run['receipts']}
for directory in sorted(out.glob('*-harness')):
    for path in directory.glob('maestro-component-*.json'):
        receipt = json.loads(path.read_text())
        assert receipt['root_removed'] and receipt['workers_reaped']
        assert not (Path(receipt['parent_path']) / receipt['root_name']).exists()
        (roots if directory in final_directories else historical).append(str(path.relative_to(out)))
assert len(roots) == 1104
inputs = json.loads((out / 'engineering-inputs.json').read_text())
thesis = Path('/home/jefferson/distributed_safety_critical_thesis')
assert sha(thesis / 'notes/dynamic_thesis_notes.md') == inputs['canonical_note_sha256']
for path, digest in inputs['inputs'].items():
    assert sha(thesis / path) == digest
native = json.loads((out / 'native-build-verification.json').read_text())['variants']
assert len(native) == 5
for record in native:
    source = next(p for p in record['command'] if p.startswith('src/'))
    assert sha(root / source) == record['source_sha256'] and record['returncode'] == 0
    assert sha(root / record['command'][record['command'].index('-o') + 1]) == record['binary_sha256']
trace = json.loads((out / 'traceability.json').read_text())
assert len(trace['requirements']) == 24 and len(trace['source_parent_register']['requirements']) == 18
assert all(p['software_mapping'] is None and not p['full_parent_closure'] for p in trace['source_parent_register']['requirements'])
audit = json.loads((out / 'harness-audit.json').read_text())
def total(key):
    return sum(row[key] for row in audit)
assert total('teardown_fault_workers_reaped') == 6
assert total('outcome_fault_workers_reaped') == total('closure_fault_workers_reaped') == 9
assert total('argus_generic_closure_records_verified') == 3
assert total('teardown_public_snapshots_verified') == 3
assert total('dispatcher_public_snapshots_verified') == 63
assert total('closure_public_snapshots_verified') == 33
assert total('recovery_public_snapshots_verified') == 51
assert total('recovery_successful_ordinary_reconciliations') == total('recovery_fork_children_reaped') == 3
assert total('new_recovery_unresolved_native_waits') == 6
assert total('bootstrap_missing_birth_ack_cases_retained') == 6
assert total('bootstrap_external_local_fd_disposals') == 12
assert total('catalog_direct_child_reap_unresolved_after_forced_helper_loss') == 6 + total('new_closure_unresolved_native_waits') + total('new_recovery_unresolved_native_waits')
review = {'type':'separate same-agent read-only component review; independent full-candidate review pending', 'source_manifest_sha256':sha(out / 'source-manifest.json'), 'repaired_product_findings':[1,2,3,5,8], 'clarifications':[4], 'fixture_corrections':[3,6], 'regression_harness_findings':[7], 'records':['docs/engineering/maestro-lite/review-recovery16.md'], 'accepted':False, 'runtime_ready':False}
save('read-only-final-review.json', review)
tasks = root / 'docs/engineering/maestro-lite/tasks-recovery16.md'
def normalize(text):
    return re.sub(r'(?m)^- \[[ xX]\]', '- [ ]', text)
assert normalize(tasks.read_text()) == normalize((out / 'frozen-task-plan.md').read_text())
tasks.write_text(tasks.read_text().replace('- [ ]','- [x]'))
save('focused-v4-observation.json', {'observed_tool_session':79757, 'observed_exit_code':0, 'log_sha256':sha(out / 'focused-v4.log'), 'note':'Actual terminal completion observed. Historical failed/focused logs and pre-repair archives retained; not counted as current passing full regression.'})
assert (out / 'ruff.log').read_text().strip() == 'All checks passed!'
assert (out / 'whitespace.log').read_text() == ''
verification = {
 'schema_version':1, 'revision':manifest['revision'],
 'maturity':'verified_partial_surviving_original_supervisor_reconciliation_not_accepted',
 'baseline':manifest['baseline'], 'parent_candidate_commit':manifest['parent_commit'],
 'platform_tests':counts['platform-tests-v3'], 'platform_subtests':24,
 'installed_wheel_tests':counts['wheel-consumer-tests-v3'], 'focused_recovery_provider_closure_dispatcher_tests':117,
 'new_recovery_cases':31, 'new_targeted_observation_cases':2, 'source_inputs_frozen':len(manifest['input_sha256']),
 'installed_modules_matched':27,'installed_native_sources_matched':3,'strict_native_variants':5,
 'partial_trace_endpoints_checked':run['partial_endpoints_checked'],
 'external_specification_inputs_verified':len(inputs['inputs']),
 'selected_parent_inputs_checked':inputs['parent_selected_inputs_verified'],
 'intentional_parent_changes':inputs['intentional_parent_source_changes'],
 'final_regression_owned_roots_absent':len(roots),'root_receipts':sorted(roots),
 'retained_focused_owned_roots_absent':len(historical),'focused_root_receipts':sorted(historical),
 'harness_audit':audit,'review':review,
 'all_24_requirements_retained':True,'all_18_source_parents_unvalidated_null_mapped':True,
 'all_30_pairs_90_declared_endpoints_and_nine_runtime_cases_remain_binding':True,
 'component_task_criteria_unchanged':True,'full_phase3_complete':False,'runtime_ready':False,
 'accepted':False,'merged':False,'factory_run_created':False,'canonical_note_edited':False,'goal_active':True,
 'remaining_gates':trace['remaining_recovery16_scope'],
 'failed_concurrent_full_regression_retained':True,
 'full_source_and_wheel_repeated_after_targeted_observation_product_repair':True,
 'limits':[
  'same-surviving-supervisor reconstruction only; process restart requires independently surviving broker/admission',
  'original host clock unchanged; view epoch is not global M1 release epoch',
  'fresh process-existence health requires actual later Query/M3/Argus; application readiness not established',
  'old starts permanently retired; no new generation, execution, permit, Stage or Release',
  'unknown direct-child waits, missing public records and unacknowledged births remain unresolved',
  'local FDs remain caller-owned; no U7/U8 complete evidence or terminal artifact',
  'both earlier full regressions failed and are retained; serialization alone did not establish stability',
  'kernel scheduling/control I/O are not hard bounded; nine runtime cases and independent acceptance pending'],
 'evidence_file_sha256':{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='verification.json' and '__pycache__' not in p.parts}
}
save('verification.json', verification)
print(json.dumps({k:verification[k] for k in ('revision','platform_tests','installed_wheel_tests','final_regression_owned_roots_absent','retained_focused_owned_roots_absent','partial_trace_endpoints_checked')}))
