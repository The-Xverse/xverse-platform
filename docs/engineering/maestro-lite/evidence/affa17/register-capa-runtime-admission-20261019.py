"""Track a synthetic fixture omission; do not promote M1 or CAPA effectiveness."""
from datetime import datetime, timezone
import copy
import difflib
import hashlib
import json
from pathlib import Path

base=Path(__file__).resolve().parent
root=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
parent=base/'capa-20261019-issuer-loss/register.json'
data=copy.deepcopy(read(parent))
out=base/'capa-20261019-runtime-admission'
out.mkdir()
data['parent_register']=dict(path=str(parent.relative_to(root)),sha256=sha(parent))
for suffix in ('a','b'):
    path=base/('runtime-admission-20261019'+suffix)/'verification.json'
    data['evidence']['E-RUNTIME-'+suffix.upper()]=dict(kind='file',path=str(path.relative_to(root)),sha256=sha(path))
adr=root/'docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0001.md'
data['evidence']['E-RUNTIME-ADR']=dict(kind='file',path=str(adr.relative_to(root)),sha256=sha(adr))
review=root/'docs/engineering/maestro-lite/review-affa17.md'
text=review.read_text();span=text[text.index('\n263.')+1:text.index('\n264.')]
data['evidence']['review:263']=dict(kind='review_span',path=str(review.relative_to(root)),start='263.',end='264.',sha256=hashlib.sha256(span.encode()).hexdigest())
test='tests/thesis_lite/maestro/test_runtime_admission.py'
sources={s:Path(read(base/('runtime-admission-20261019'+s)/'running.json')['frozen_source_root']) for s in ('a','b')}
patch=out/'263.patch'
with patch.open('x') as stream:
    stream.writelines(difflib.unified_diff((sources['a']/test).read_text().splitlines(True),
        (sources['b']/test).read_text().splitlines(True),fromfile='before/'+test,tofile='after/'+test))
data['evidence']['E-RUNTIME-PATCH-263']=dict(kind='file',path=str(patch.relative_to(root)),sha256=sha(patch))
refs=['review:263','E-RUNTIME-A','E-RUNTIME-B','E-RUNTIME-PATCH-263']
row=copy.deepcopy(data['records'][-1]);now=datetime.now(timezone.utc).isoformat()
row.update(capa_id='ML-CAPA-263',incident_ids=['review:263'],state='FIX_CANDIDATE',root_cause_status='HYPOTHESIS',
    root_cause_summary='Synthetic v6 fixture omits the mandatory original schedule source digest and fails before preflight. Bind exact original schedule bytes; retain all original fixture failures. No actual M1 admission or independent cause confirmation.',
    root_cause_evidence_refs=refs,candidate_patch_sha256=sha(patch),
    reproducer_id='test_runtime_admission.py fixture setup',prevention_test_id='test_runtime_admission.py',
    affected_versions=['runtime-admission-20261019a original frozen fixture'],
    created_at=now,updated_at=now,observation_window_end=None,lesson_ids=[])
data['records'].append(row);data['selected_findings'].append(263)
data['action_plans'][row['capa_id']]=dict(
    containment='Fail critical cohort before compatibility checks. Empty reservation cleanup is separate from execution or M1 evidence.',
    correction=dict(status='implemented_in_owned_fixture_only',evidence_refs=refs),
    prevention=dict(status='local_source_wheel_unit_checks_passed',evidence_refs=refs,
        limits='Synthetic/inert inputs; no operator approval, original M1 receipt verification or independent RCA.'),
    effectiveness=dict(status='NOT_DEMONSTRATED',observation_plan=None,independent_confirmation=False),
    next_action='Independent causal review and defined effectiveness observation; integrate actual runtime entry under full gates.')
with (out/'register.json').open('x') as stream:
    json.dump(data,stream,indent=2);stream.write('\n')
print(json.dumps(dict(records=len(data['records']),evidence=len(data['evidence']))))
