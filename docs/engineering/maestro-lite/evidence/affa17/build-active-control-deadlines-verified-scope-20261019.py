"""Join distinct observed contexts; never double-count the two regression audits."""
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
def ref(path):
    return dict(path=str(path.relative_to(base)), sha256=sha(path))
primary = base / 'active-control-deadlines-20261019c'
regression = base / 'active-control-restart-regression-20261019a'
p = read(primary / 'verification.json')
r = read(regression / 'restart-verification.json')
t = read(regression / 'transitive-verification.json')
assert read(primary / 'frozen-inputs.json') == read(regression / 'frozen-inputs.json')
assert p['wheel_sha256'] == r['wheel_sha256'] == t['wheel_sha256']
roots = p['original_root_receipts'] + [dict(path=str(Path(regression.name) / a['path']), sha256=a['sha256'])
    for a in r['original_root_receipts']]
roots[:len(p['original_root_receipts'])] = [dict(path=str(Path(primary.name) / a['path']), sha256=a['sha256'])
    for a in p['original_root_receipts']]
identities = set()
for item in roots:
    path = base / item['path']
    assert sha(path) == item['sha256']
    data = read(path)
    key = data['parent_path'], data['root_name']
    assert key not in identities
    identities.add(key)
assert len(identities) == 38
assert r['phases'] == t['phases']
assert r['phases'][0]['passed'] == 8 and r['phases'][0]['failed'] == 1
assert r['phases'][1]['passed'] == 9 and r['phases'][1]['failed'] == 0
counts = [dict(phase=a['phase'], passed=a['passed'] + b['passed'], failed=a['failed'] + b['failed'])
    for a, b in zip(p['phases'], r['phases'])]
scope = dict(primary=ref(primary / 'verification.json'),
    restart_regression=ref(regression / 'restart-verification.json'),
    transitive_regression=ref(regression / 'transitive-verification.json'),
    exact_shared_frozen_inputs=True, immutable_shared_package=True, packaged_sources=76,
    phases=counts, original_root_receipts=roots, original_wait_receipts=38,
    unique_original_source_snapshots=38, source_links=p['source_links'] + r['source_links'],
    original_inputs_closed_recomputations=sum(c['independent_closed_complete'] for c in p['cases'])
        + sum(c['closed_offline_complete'] for c in r['cases']) + t['independent_closed_complete'],
    retained_byte_identical_closed_roots=len(p['retained_closed_public']) + len(t['retained_closed_public']),
    regression_audits_cover_same_18_contexts=True,
    source_failure=dict(finding=222, case='active-restart leaf', diagnostic='ML-SCHEDULE-TEARDOWN-INCOMPLETE',
        restart_disposition='completed', explicit_closure_not_reached=True, native_fixture_waits_retained=True),
    full_selected_increment17_complete=False, full_M1_complete=False, whole_platform_regression=False,
    accepted=False, merged=False)
path = base / 'active-control-deadlines-verified-scope.json'
with path.open('x') as stream:
    json.dump(scope, stream, indent=2)
    stream.write('\n')
parent = base / 'active-control-deadlines-partial-traceability.json'
trace = read(parent)
trace['revision'] = 'ML3-AFFA17-2026-10-19-active-control-deadlines-v2-affected-scope'
trace['parent_trace'] = ref(parent)
trace['evidence'] = ref(path)
trace['current_affected_counts'] = counts
trace['additional_affected_regression'] = [ref(regression / 'restart-verification.json'), ref(regression / 'transitive-verification.json')]
trace['source_links'] = scope['source_links']
trace['original_root_receipts'] = trace['original_wait_receipts'] = 38
trace['normal_retained_closed_public_roots'] = scope['retained_byte_identical_closed_roots']
trace['original_inputs_closed_recomputations'] = scope['original_inputs_closed_recomputations']
trace['component_finding_dispositions']['240'] = 'auditor_schema_corrected_without_native_repetition'
trace['component_finding_dispositions']['241'] = 'bounded_review_only'
trace['component_finding_dispositions']['242'] = 'old_222_reproduced_not_waived'
assert trace['open_findings'] == [135, 222]
target = base / 'active-control-deadlines-verified-scope-traceability.json'
with target.open('x') as stream:
    json.dump(trace, stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(scope=ref(path), trace=ref(target), phases=counts,
    source_links=scope['source_links'], closed=scope['original_inputs_closed_recomputations'],
    retained=scope['retained_byte_identical_closed_roots'])))
