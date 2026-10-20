"""Add disposal observations without changing any parent evidence binding."""
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
parent_path = base/'capa-20261019-runtime-issuer-loss-v2/register.json'
parent = read(parent_path)
data = copy.deepcopy(parent)
red = read(base/'runtime-disposal-20261019a/verification.json')
repair = read(base/'runtime-disposal-20261019c/verification.json')
assert red['counts']=={p:dict(passed=0,failed=3,errors=0) for p in ('source','wheel')}
assert repair['counts']=={p:dict(passed=157,failed=0,errors=0) for p in ('source','wheel')}
assert len(repair['phases'])==30
out = base/'capa-20261019-runtime-disposal'
out.mkdir(exist_ok=False)
data['parent_register'] = dict(path=str(parent_path.relative_to(root)),sha256=sha(parent_path))

def ref(key,path):
    assert key not in data['evidence'],key
    data['evidence'][key] = dict(kind='file',path=str(path.relative_to(root)),sha256=sha(path))

for key,path in {
    'E-DISPOSAL-RED-A':base/'runtime-disposal-20261019a/verification.json',
    'E-DISPOSAL-REPAIR-C':base/'runtime-disposal-20261019c/verification.json',
    'E-DISPOSAL-ADR-0010':root/'docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0010.md',
    'E-DISPOSAL-SETUP-345':base/'runtime-disposal-20261019b/setup-failure.json',
    'E-DISPOSAL-AUDITOR':base/'audit-runtime-disposal-20261019.py',
    'E-DISPOSAL-DRIVER-C':base/'verify-runtime-disposal-20261019c.py',
}.items():ref(key,path)

review = root/'docs/engineering/maestro-lite/review-affa17.md'
text = review.read_text()
for number in (343,344,345):
    key = 'review:'+str(number)
    assert key not in data['evidence']
    start,end = str(number)+'.',str(number+1)+'.'
    span = text[text.index('\n'+start)+1:text.index('\n'+end)]
    data['evidence'][key] = dict(kind='review_span',path=str(review.relative_to(root)),
        start=start,end=end,sha256=hashlib.sha256(span.encode()).hexdigest())

sources = {s:Path(read(base/f'runtime-disposal-20261019{s}/running.json')['frozen_source_root']) for s in 'ac'}
for number,files in {
    338:['src/xverse/maestro/persistence.py'],
    344:['src/xverse/maestro/run_broker.py','tests/thesis_lite/maestro/test_runtime_disposal.py'],
}.items():
    path = out/f'{number}.patch'
    with path.open('x') as stream:
        for name in files:
            stream.writelines(difflib.unified_diff((sources['a']/name).read_text().splitlines(True),
                (sources['c']/name).read_text().splitlines(True),fromfile='before/'+name,tofile='after/'+name))
    ref('E-DISPOSAL-PATCH-'+str(number),path)
path = out/'345.patch'
with path.open('x') as stream:
    stream.writelines(difflib.unified_diff((base/'verify-runtime-disposal-20261019b.py').read_text().splitlines(True),
        (base/'verify-runtime-disposal-20261019c.py').read_text().splitlines(True),fromfile='before/driver',tofile='after/driver'))
ref('E-DISPOSAL-PATCH-345',path)

summaries = {
    338:'Client-local unresolved drain blocks disposal after an actual original-root helper wait. Controlled original observation-loss cases support verifying the original BootstrapChild wait for local disposal while preserving earlier drain/result. The precise old nominal local-drain value remains unretained; timeout337 is not explained. Same-session local support only.',
    344:'Broker image disposal repeats raw descriptor numbers after successful or partial outer disposal; guarded actual reuse controls reproduce the attempted foreign close. A pinned single-use close ledger and retained close uncertainty prevent retargeting,including an actual-close-then-error control. Same-session local support only.',
    345:'Copied verification driver changed the output identity but retained the old target-environment spelling. Fresh-environment guard rejected before build/install/pytest; successor c corrects both identities and preserves the failed setup archive.',
}
now = datetime.now(timezone.utc).isoformat()
for number in (338,344,345):
    identity = 'ML-CAPA-'+str(number)
    row = next((r for r in data['records'] if r['capa_id']==identity),None)
    if row is None:
        row = copy.deepcopy(data['records'][-1])
        row.update(capa_id=identity,incident_ids=['review:'+str(number)],root_cause_evidence_refs=[],
            created_at=now,lesson_ids=[],observation_window_end=None)
        data['records'].append(row)
        data['selected_findings'].append(number)
    refs = ['E-DISPOSAL-RED-A','E-DISPOSAL-REPAIR-C','E-DISPOSAL-ADR-0010',
        'review:343','review:344','E-DISPOSAL-PATCH-'+str(number)] if number!=345 else [
        'review:345','E-DISPOSAL-SETUP-345','E-DISPOSAL-PATCH-345','E-DISPOSAL-DRIVER-C','E-DISPOSAL-REPAIR-C']
    row.update(state='FIX_CANDIDATE',root_cause_status='HYPOTHESIS',root_cause_summary=summaries[number],
        root_cause_evidence_refs=list(dict.fromkeys(row['root_cause_evidence_refs']+refs)),
        candidate_patch_sha256=sha(out/f'{number}.patch'),updated_at=now,
        prevention_test_id='test_original_runtime_disposal_preserves_wait_facts_and_reused_descriptor' if number!=345 else 'verify-runtime-disposal-20261019c.py')
    if number!=338:
        row.update(reproducer_id='runtime-disposal-20261019a guarded reused descriptor' if number==344 else 'runtime-disposal-20261019b fresh environment assertion',
            affected_versions=['runtime-disposal-20261019a' if number==344 else 'verify-runtime-disposal-20261019b.py'])
    data['action_plans'][identity] = dict(
        containment='Preserve original failures,unknown waits and canary guards. No historical timeout,normal-evidence or full-case promotion.',
        correction=dict(status='implemented_uncommitted',evidence_refs=refs),
        prevention=dict(status='local_exact_source_wheel_checks_passed',evidence_refs=refs,
            limits='Same-session local controls only; no organizational independence or effectiveness window.'),
        effectiveness=dict(status='NOT_DEMONSTRATED',observation_plan=None,independent_confirmation=False),
        next_action='Separate causal review and defined effectiveness observation; retain original complete lifecycle/M1/regression/source-parent gates.')

# Parent preservation is a prerequisite to writing the successor,not just schema validation.
assert all(data['evidence'].get(k)==v for k,v in parent['evidence'].items())
for old in parent['records']:
    new = next(r for r in data['records'] if r['capa_id']==old['capa_id'])
    assert new['created_at']==old['created_at'] and new['policy_sha256']==old['policy_sha256']
    assert set(old['incident_ids'])<=set(new['incident_ids'])
    assert set(old['root_cause_evidence_refs'])<=set(new['root_cause_evidence_refs'])
assert data['schema_sha256']==parent['schema_sha256'] and data['policy_sha256']==parent['policy_sha256']
assert len(data['records'])==39
with (out/'register.json').open('x') as stream:
    json.dump(data,stream,indent=2)
    stream.write('\n')
print(json.dumps(dict(records=len(data['records']),evidence=len(data['evidence']),parent_bindings_preserved=len(parent['evidence']))))
