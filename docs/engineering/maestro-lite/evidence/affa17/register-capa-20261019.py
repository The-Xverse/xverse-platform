"""Create immutable selected CAPA observations from retained evidence, no actions."""
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

base = Path(__file__).resolve().parent
candidate = base.parents[4]
folder = base / 'capa-20261019'
folder.mkdir()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
def save(path, data):
    with path.open('x') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')

schema_source = Path('/home/jefferson/forge-c/specs/004-continuous-reliability-engineering/contracts/capa-record.schema.json')
schema = folder / 'forge-cre-capa-record-v1.schema.json'
with schema.open('xb') as stream:
    stream.write(schema_source.read_bytes())
source_ref = dict(repository='/home/jefferson/forge-c',
    head=subprocess.check_output(['git', '-C', '/home/jefferson/forge-c', 'rev-parse', 'HEAD'], text=True).strip(),
    path=str(schema_source), sha256=sha(schema_source), use='read-only schema pattern; no CRE implementation claim')
old_root = Path(read(base / 'active-controller-recovery-20261019d/running.json')['frozen_source_root'])
new_root = Path(read(base / 'active-control-deadlines-20261019c/running.json')['frozen_source_root'])
relative = 'src/xverse/maestro/dispatcher.py'
assert sha(candidate / relative) == sha(new_root / relative)
patch = folder / 'cancel-preflight.patch'
with patch.open('x') as stream:
    stream.writelines(difflib.unified_diff((old_root / relative).read_text().splitlines(keepends=True),
        (new_root / relative).read_text().splitlines(keepends=True), fromfile='a/' + relative, tofile='b/' + relative))
policy = candidate / 'docs/engineering/maestro-lite/capa-policy.json'
review = candidate / 'docs/engineering/maestro-lite/review-affa17.md'
text = review.read_text()
evidence = {}
def file_ref(key, path):
    evidence[key] = dict(kind='file', path=str(path.relative_to(candidate)), sha256=sha(path))
def review_ref(number):
    start, end = str(number) + '.', str(number + 1) + '.'
    snippet = text[text.index('\n' + start) + 1:text.index('\n' + end)]
    evidence['review:' + str(number)] = dict(kind='review_span', path=str(review.relative_to(candidate)),
        start=start, end=end, sha256=hashlib.sha256(snippet.encode()).hexdigest())
for number in (135, 222, 238, 239, 241, 242):
    review_ref(number)
for key, path in (
    ('E-135', base / 'runtime-collection-execution-20261019b/failure-verification.json'),
    ('E-CANCEL-RED', base / 'active-control-deadlines-20261019b/counterexample-verification.json'),
    ('E-CANCEL-PREVENTION', base / 'active-control-deadlines-20261019c/verification.json'),
    ('E-CURRENT-SCOPE', base / 'active-control-deadlines-verified-scope.json'),
    ('E-222-RECURRENCE', base / 'active-control-restart-regression-20261019a/restart-verification.json'),
    ('E-TRACE', base / 'active-control-deadlines-verified-scope-traceability.json'),
    ('E-PATCH', patch), ('E-SCHEMA', schema), ('E-POLICY', policy)):
    file_ref(key, path)
now = datetime.now(timezone.utc).isoformat()
common = dict(schema_version='1.0', created_at=now, updated_at=now, policy_sha256=sha(policy),
    observation_window_end=None, lesson_ids=[])
records = [
    dict(common, capa_id='ML-CAPA-238', incident_ids=['review:238', 'review:239'], state='FIX_CANDIDATE',
        root_cause_status='HYPOTHESIS',
        root_cause_summary='Local causal evidence: cancelled queued restart sets mutated=True before its first effect and reports failed. Early latch preflight corrects both original source/wheel counterexamples. Independent cause confirmation is not established.',
        root_cause_evidence_refs=['review:238', 'E-CANCEL-RED', 'E-CANCEL-PREVENTION', 'E-PATCH'],
        reproducer_id='test_original_control_rejection_keeps_unspent_authority[cancel-queued-restart]',
        prevention_test_id='test_original_control_rejection_keeps_unspent_authority[cancel-queued-restart]',
        candidate_patch_sha256=sha(patch), affected_versions=['recovery-d original dirty snapshot; exact identities in E-CANCEL-RED']),
    dict(common, capa_id='ML-CAPA-135', incident_ids=['review:135'], state='UNRESOLVED', root_cause_status='UNKNOWN',
        root_cause_summary=None, root_cause_evidence_refs=['review:135', 'E-135'],
        reproducer_id='test_implicit_horizon_stop_respects_dependencies_before_compiler_rank',
        prevention_test_id=None, candidate_patch_sha256=None,
        affected_versions=['runtime-collection-execution-20261019b; exact source/wheel hashes in E-135']),
    dict(common, capa_id='ML-CAPA-222', incident_ids=['review:222', 'review:242'], state='UNRESOLVED', root_cause_status='UNKNOWN',
        root_cause_summary=None, root_cause_evidence_refs=['review:222', 'review:242', 'E-222-RECURRENCE'],
        reproducer_id='test_original_active_explicit_restart_and_closed_generation_universe[leaf]',
        prevention_test_id=None, candidate_patch_sha256=None,
        affected_versions=['original v3 4.8s admission; retained transitive-d failure and active-control restart regression'])
]
plans = {
    'ML-CAPA-238':dict(containment='No ordinary restart effect after known cancellation; original run cancellation/cleanup retained.',
        correction=dict(status='implemented_uncommitted', evidence_refs=['E-PATCH', 'E-CANCEL-PREVENTION']),
        prevention=dict(status='local_test_passed', evidence_refs=['E-CANCEL-RED', 'E-CANCEL-PREVENTION'],
            limits='Same-session test ownership; no hidden holdout or organizational independence.'),
        effectiveness=dict(status='NOT_DEMONSTRATED', observation_plan=None, independent_confirmation=False),
        next_action='Obtain independent causal confirmation and define an appropriate effectiveness observation plan; retain full17 gates.'),
    'ML-CAPA-135':dict(containment='Continue independent work; keep stable17/release gate open.',
        correction=dict(status='not_implemented', evidence_refs=[]), prevention=dict(status='not_demonstrated', evidence_refs=[]),
        effectiveness=dict(status='NOT_DEMONSTRATED', observation_plan=None, independent_confirmation=False),
        next_action='Diagnose original implicit-horizon failure from retained sources. Preserve author-deferred immediate repair and original bounds.'),
    'ML-CAPA-222':dict(containment='Retain original 4.8s case and incomplete teardown; do not infer harmlessness from generation2 success.',
        correction=dict(status='not_implemented', evidence_refs=[]), prevention=dict(status='not_demonstrated', evidence_refs=[]),
        effectiveness=dict(status='NOT_DEMONSTRATED', observation_plan=None, independent_confirmation=False),
        recurrence=dict(status='observed_same_case_and_symptom', evidence_refs=['review:242', 'E-222-RECURRENCE'], same_cause_proven=False),
        next_action='Diagnose actual remaining lifecycle work/budget before a targeted correction. Do not extend old ends or rerun unchanged suites for green.')
}
save(folder / 'register.json', dict(schema_version='ML-CAPA-register-1', capability='024-maestro-lite-lifecycle',
    mode='OBSERVE_ONLY', source_pattern=source_ref, schema_sha256=sha(schema), policy_sha256=sha(policy),
    evidence=evidence, records=records, action_plans=plans, selected_findings=[135, 222, 238],
    historical_backfill_complete=False, automatic_workflow_implemented=False, capability025_capa_integration=False,
    full_increment17_complete=False, accepted=False, merged=False, scientific_result=False))
print(json.dumps(dict(path=str(folder / 'register.json'), sha256=sha(folder / 'register.json'), records=len(records))))
