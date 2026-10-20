"""Preserve issuer-loss red/successor evidence; no independent RCA promotion."""
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
parent = base/'capa-20261019-intent-termination/register.json'
data = copy.deepcopy(read(parent))
out = base/'capa-20261019-issuer-loss'
out.mkdir()
data['parent_register'] = dict(path=str(parent.relative_to(root)), sha256=sha(parent))
def ref(key, path):
    data['evidence'][key] = dict(kind='file', path=str(path.relative_to(root)), sha256=sha(path))
for suffix in ('a','b','c'):
    ref('E-ISSUER-'+suffix.upper(), base/('composed-issuer-loss-20261019'+suffix)/'verification.json')
ref('E-ISSUER-RED', base/'composed-issuer-loss-20261019a/counterexample-verification.json')
ref('E-ISSUER-ADR', root/'docs/engineering/maestro-lite/ADR-ML3-CLEANUP-0001.md')
review = root/'docs/engineering/maestro-lite/review-affa17.md'
text = review.read_text()
for number in (259,260):
    start,end = str(number)+'.',str(number+1)+'.'
    span = text[text.index('\n'+start)+1:text.index('\n'+end)]
    data['evidence']['review:'+str(number)] = dict(kind='review_span',path=str(review.relative_to(root)),
        start=start,end=end,sha256=hashlib.sha256(span.encode()).hexdigest())
source = {s:Path(read(base/('composed-issuer-loss-20261019'+s)/'running.json')['frozen_source_root']) for s in ('a','c')}
patch = out/'259.patch'
with patch.open('x') as stream:
    for name in ('src/xverse/maestro/run_broker.py','src/xverse/maestro/run_closure.py'):
        stream.writelines(difflib.unified_diff((source['a']/name).read_text().splitlines(True),
            (source['c']/name).read_text().splitlines(True),fromfile='before/'+name,tofile='after/'+name))
ref('E-ISSUER-PATCH-259',patch)
patch = out/'260.patch'
with patch.open('x') as stream:
    stream.writelines(difflib.unified_diff((base/'verify-composed-issuer-loss-20261019b.py').read_text().splitlines(True),
        (base/'verify-composed-issuer-loss-20261019c.py').read_text().splitlines(True),fromfile='before/verification-driver',tofile='after/verification-driver'))
ref('E-ISSUER-PATCH-260',patch)
summaries = {
    259:'Ordinary issuer-registry validation blocks run-wide and per-unit cancellation; closure also dereferences a replacement generation registry. Original cleanup-context validation and retained original inventory now preserve fencing/cleanup without adoption. Local causal support only.',
    260:'Multiple pytest modules sharing one harness directory collide on module-scoped heartbeat compiler receipts. Separate module cohorts and original evidence roots preserve every receipt without changing test assertions or runtime ends.',
}
for number in (259,260):
    refs = ['review:'+str(number),'E-ISSUER-PATCH-'+str(number),'E-ISSUER-B','E-ISSUER-C']
    if number == 259:
        refs += ['review:260','E-ISSUER-A','E-ISSUER-RED','E-ISSUER-ADR']
    row = copy.deepcopy(data['records'][-1]); now = datetime.now(timezone.utc).isoformat()
    row.update(capa_id='ML-CAPA-'+str(number),incident_ids=['review:'+str(number)],state='FIX_CANDIDATE',
        root_cause_status='HYPOTHESIS',root_cause_summary=summaries[number],root_cause_evidence_refs=refs,
        candidate_patch_sha256=sha(out/(str(number)+'.patch')),
        reproducer_id='test_original_registry_loss_denies_adoption_but_preserves_cancellation_and_cleanup' if number==259 else 'verify-composed-issuer-loss-20261019b.py',
        prevention_test_id='test_original_registry_loss_denies_adoption_but_preserves_cancellation_and_cleanup' if number==259 else 'verify-composed-issuer-loss-20261019c.py',
        affected_versions=['composed-issuer-loss-a and partial b' if number==259 else 'composed-issuer-loss-b combined module harness'],
        created_at=now,updated_at=now,observation_window_end=None,lesson_ids=[])
    if number == 259:
        row['incident_ids'].append('review:260')
    data['records'].append(row); data['selected_findings'].append(number)
    data['action_plans'][row['capa_id']] = dict(
        containment='Preserve failed native runs; original-root fallback cleanup remains separate from primary success. No ordinary adoption or acceptance.',
        correction=dict(status='implemented_uncommitted',evidence_refs=refs),
        prevention=dict(status='local_source_wheel_native_checks_passed',evidence_refs=refs,
            limits='Same-session evidence; no independent cause confirmation or effectiveness observation.'),
        effectiveness=dict(status='NOT_DEMONSTRATED',observation_plan=None,independent_confirmation=False),
        next_action='Independent causal review and defined effectiveness observation; retain full17 and unresolved135/222 gates.')
with (out/'register.json').open('x') as stream:
    json.dump(data,stream,indent=2); stream.write('\n')
print(json.dumps(dict(records=len(data['records']),evidence=len(data['evidence']),register=str(out/'register.json'))))
