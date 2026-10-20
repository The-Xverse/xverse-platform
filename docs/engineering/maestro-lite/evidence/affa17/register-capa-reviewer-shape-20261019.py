"""Retain a local reviewer failure/correction without changing runtime claims."""
import copy
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
root = base.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
parent_path = base/'capa-20261019-runtime-disposal/register.json'
parent = read(parent_path)
data = copy.deepcopy(parent)
out = base/'capa-20261019-reviewer-shape'
out.mkdir(exist_ok=False)
data['parent_register'] = dict(path=str(parent_path.relative_to(root)),sha256=sha(parent_path))
def ref(key,path):
    assert key not in data['evidence'],key
    data['evidence'][key] = dict(kind='file',path=str(path.relative_to(root)),sha256=sha(path))

for key,path in {
    'E-REVIEW353-ORIGINAL':base/'review-current-source-writer-table-20261019b.py',
    'E-REVIEW353-FAILED':base/'integrated-maestro-20261019b/writer-table-review-original-failure.json',
    'E-REVIEW353-CORRECTED':base/'review-current-source-writer-table-20261019b-v2.py',
    'E-REVIEW353-CHECKED':base/'integrated-maestro-20261019b/source-writer-table-review.json',
}.items():ref(key,path)
review = root/'docs/engineering/maestro-lite/review-affa17.md'
text = review.read_text()
span = text[text.index('\n353.')+1:text.index('\n354.')]
assert 'review:353' not in data['evidence']
data['evidence']['review:353'] = dict(kind='review_span',path=str(review.relative_to(root)),
    start='353.',end='354.',sha256=hashlib.sha256(span.encode()).hexdigest())
patch = out/'353.patch'
with patch.open('x') as stream:
    stream.writelines(difflib.unified_diff((base/'review-current-source-writer-table-20261019b.py').read_text().splitlines(True),
        (base/'review-current-source-writer-table-20261019b-v2.py').read_text().splitlines(True),
        fromfile='before/reviewer',tofile='after/reviewer'))
ref('E-REVIEW353-PATCH',patch)
refs = ['review:353','E-REVIEW353-ORIGINAL','E-REVIEW353-FAILED','E-REVIEW353-CORRECTED','E-REVIEW353-CHECKED','E-REVIEW353-PATCH']
now = datetime.now(timezone.utc).isoformat()
row = copy.deepcopy(data['records'][-1])
row.update(capa_id='ML-CAPA-353',incident_ids=['review:353'],state='FIX_CANDIDATE',
    root_cause_status='HYPOTHESIS',
    root_cause_summary='The review tool assumed asdict serialized a computed cleanup_complete property. Actual receipts retain explicit root/helper/C1 fields. The successor validates only those actual fields and retains its limited claim. Same-session local support only; no runtime failure or full cleanup inference.',
    root_cause_evidence_refs=refs,reproducer_id='source writer-table comparison KeyError cleanup_complete',
    prevention_test_id='same nine original source receipts through corrected table reviewer; no native execution',
    candidate_patch_sha256=sha(patch),affected_versions=['review-current-source-writer-table-20261019b.py only'],
    lesson_ids=[],observation_window_end=None,created_at=now,updated_at=now)
data['records'].append(row)
data['selected_findings'].append(353)
data['action_plans']['ML-CAPA-353'] = dict(
    containment='Preserve original reviewer/failure. Source1501 and its terminal audit stay unchanged.',
    correction=dict(status='implemented_in_read_only_reviewer',evidence_refs=refs),
    prevention=dict(status='same_original_receipts_reaudit_passed',evidence_refs=refs,
        limits='Local same-session evidence only; no native rerun,independent cause confirmation or effectiveness observation.'),
    effectiveness=dict(status='NOT_DEMONSTRATED',observation_plan=None,independent_confirmation=False),
    next_action='Use actual serialized contracts and preserve aggregate-claim limits; continue original wheel and full scope.')
assert all(data['evidence'].get(k)==v for k,v in parent['evidence'].items())
assert data['records'][:-1]==parent['records']
assert len(data['records'])==40 and len(data['evidence'])==216
with (out/'register.json').open('x') as stream:
    json.dump(data,stream,indent=2)
    stream.write('\n')
print(json.dumps(dict(records=40,evidence=216,parent_bindings_preserved=210)))
