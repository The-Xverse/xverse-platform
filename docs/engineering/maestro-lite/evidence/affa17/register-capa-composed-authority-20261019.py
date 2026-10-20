"""Append selected fixture/auditor incidents; never close or promote a CAPA."""
from datetime import datetime, timezone
import copy
import difflib
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
candidate = base.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
parent = base/'capa-20261019-writer-stream/register.json'
data = copy.deepcopy(read(parent))
out = base/'capa-20261019-composed-authority'
out.mkdir()
data['parent_register'] = dict(path=str(parent.relative_to(candidate)), sha256=sha(parent))
evidence = data['evidence']

def file_ref(key, path):
    evidence[key] = dict(kind='file', path=str(path.relative_to(candidate)), sha256=sha(path))

for suffix in ('a', 'b', 'c'):
    folder = base/('composed-authority-20261019'+suffix)
    file_ref('E-COMPOSED-'+suffix.upper(), folder/'verification.json')
    file_ref('E-COMPOSED-NATIVE-'+suffix.upper(), folder/'native-retention.json')
review = candidate/'docs/engineering/maestro-lite/review-affa17.md'
text = review.read_text()
for number in (250, 251, 252):
    start, end = str(number)+'.', str(number+1)+'.'
    span = text[text.index('\n'+start)+1:text.index('\n'+end)]
    evidence['review:'+str(number)] = dict(kind='review_span', path=str(review.relative_to(candidate)),
        start=start, end=end, sha256=hashlib.sha256(span.encode()).hexdigest())
test = 'tests/thesis_lite/maestro/test_composed_authority_interruptions.py'
frozen = {s: Path(read(base/('composed-authority-20261019'+s)/'running.json')['frozen_source_root'])
    for s in ('a', 'b', 'c')}
patches = {
    250: ((frozen['a']/test).read_text(), (frozen['b']/test).read_text(), test),
    251: ((frozen['b']/test).read_text(), (frozen['c']/test).read_text(), test),
    252: ((base/'audit-composed-authority-20261019-initial.py').read_text(),
          (base/'audit-composed-authority-20261019.py').read_text(),
          'docs/engineering/maestro-lite/evidence/affa17/audit-composed-authority-20261019.py'),
}
summaries = {
    250: 'Active heartbeat observation incorrectly called a frozen-only certification API. Exact retained-fd observational reads preserve the strict production contract; local correction only.',
    251: 'Fixture assumed helper SIGKILL prevented receipt of a genuine already-queued ACK and sampled certified membership across clone3. Trace actual exchange returns and bounded observational birth, preserving no-start and unknown-wait semantics.',
    252: 'Auditor reused a blanket zero-reader-gaps expectation for deliberate crash contexts. Recompute exact missing mirror set and validate every existing hash; preserve genuine missing normal evidence.',
}
for number, (old, new, path) in patches.items():
    patch = out/(str(number)+'.patch')
    with patch.open('x') as stream:
        stream.writelines(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
            fromfile='before/'+path, tofile='after/'+path))
    file_ref('E-COMPOSED-PATCH-'+str(number), patch)
    refs = ['review:'+str(number), 'E-COMPOSED-PATCH-'+str(number), 'E-COMPOSED-C']
    refs += ['E-COMPOSED-A'] if number == 250 else ['E-COMPOSED-B'] if number == 251 else []
    row = copy.deepcopy(data['records'][-1])
    now = datetime.now(timezone.utc).isoformat()
    row.update(capa_id='ML-CAPA-'+str(number), incident_ids=['review:'+str(number)],
        state='FIX_CANDIDATE', root_cause_status='HYPOTHESIS', root_cause_summary=summaries[number],
        root_cause_evidence_refs=refs, candidate_patch_sha256=sha(patch),
        reproducer_id='test_composed_authority_interruptions.py' if number != 252 else 'audit-composed-authority-20261019-initial.py',
        prevention_test_id='test_composed_authority_interruptions.py' if number != 252 else 'audit-composed-authority-20261019.py',
        affected_versions=['composed-authority-'+('a' if number == 250 else 'b')+' original frozen test/auditor inputs'],
        created_at=now, updated_at=now, observation_window_end=None, lesson_ids=[])
    data['records'].append(row)
    data['selected_findings'].append(number)
    data['action_plans'][row['capa_id']] = dict(
        containment='Preserve original failed controls and incomplete evidence. No production change or full-case acceptance.',
        correction=dict(status='implemented_in_owned_fixture_or_auditor_only', evidence_refs=refs),
        prevention=dict(status='local_check_passed', evidence_refs=refs,
            limits='Same-session controls/review only; no independent cause confirmation or effectiveness window.'),
        effectiveness=dict(status='NOT_DEMONSTRATED', observation_plan=None, independent_confirmation=False),
        next_action='Independent causal review and defined effectiveness observation; full17 and CAPA135/222 stay open.')
with (out/'register.json').open('x') as stream:
    json.dump(data, stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(register=str(out/'register.json'), records=len(data['records']), evidence=len(evidence))))
