"""Track the start-intent fixture correction without changing CAPA authority."""
from datetime import datetime, timezone
import copy
import difflib
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
root = base.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
parent = base/'capa-20261019-composed-authority/register.json'
data = copy.deepcopy(read(parent))
out = base/'capa-20261019-intent-termination'
out.mkdir()
data['parent_register'] = dict(path=str(parent.relative_to(root)), sha256=sha(parent))
for suffix in ('a', 'b'):
    folder = base/('composed-intent-termination-20261019'+suffix)
    for name in ('verification', 'native-retention'):
        path = folder/(name+'.json')
        data['evidence']['E-INTENT-'+suffix.upper()+'-'+name] = dict(kind='file', path=str(path.relative_to(root)), sha256=sha(path))
review = root/'docs/engineering/maestro-lite/review-affa17.md'
text = review.read_text()
span = text[text.index('\n256.')+1:text.index('\n257.')]
data['evidence']['review:256'] = dict(kind='review_span', path=str(review.relative_to(root)),
    start='256.', end='257.', sha256=hashlib.sha256(span.encode()).hexdigest())
test = 'tests/thesis_lite/maestro/test_composed_persistence_termination.py'
sources = {suffix: Path(read(base/('composed-intent-termination-20261019'+suffix)/'running.json')['frozen_source_root'])
    for suffix in ('a', 'b')}
patch = out/'256.patch'
with patch.open('x') as stream:
    stream.writelines(difflib.unified_diff((sources['a']/test).read_text().splitlines(True),
        (sources['b']/test).read_text().splitlines(True), fromfile='before/'+test, tofile='after/'+test))
data['evidence']['E-INTENT-PATCH-256'] = dict(kind='file', path=str(patch.relative_to(root)), sha256=sha(patch))
refs = ['review:256', 'E-INTENT-PATCH-256', 'E-INTENT-A-verification', 'E-INTENT-B-verification']
row = copy.deepcopy(data['records'][-1])
now = datetime.now(timezone.utc).isoformat()
row.update(capa_id='ML-CAPA-256', incident_ids=['review:256'], state='FIX_CANDIDATE',
    root_cause_status='HYPOTHESIS', root_cause_summary='Unit/intent trigger also observes normal stop and cleanup intents. Require the original start-intent producer maestro.owner7; retain actual old trace and successful loader lifecycle. Independent cause confirmation remains absent.',
    root_cause_evidence_refs=refs, candidate_patch_sha256=sha(patch),
    reproducer_id='test_original_intent_frontier_loader_and_loss[disabled]',
    prevention_test_id='test_original_intent_frontier_loader_and_loss[disabled]',
    affected_versions=['composed-intent-termination-20261019a exact frozen fixture'],
    created_at=now, updated_at=now, observation_window_end=None, lesson_ids=[])
data['records'].append(row)
data['selected_findings'].append(256)
data['action_plans'][row['capa_id']] = dict(
    containment='Fail loader gate before fault cohorts; preserve original complete lifecycle and failing assertions.',
    correction=dict(status='implemented_in_owned_fixture_only', evidence_refs=refs),
    prevention=dict(status='local_check_passed', evidence_refs=refs,
        limits='Same-session source/wheel native controls, not independent causal confirmation.'),
    effectiveness=dict(status='NOT_DEMONSTRATED', observation_plan=None, independent_confirmation=False),
    next_action='Independent causal review and defined effectiveness observation; preserve original failure and full17 gates.')
with (out/'register.json').open('x') as stream:
    json.dump(data, stream, indent=2); stream.write('\n')
print(json.dumps(dict(records=len(data['records']), evidence=len(data['evidence']), register=str(out/'register.json'))))
