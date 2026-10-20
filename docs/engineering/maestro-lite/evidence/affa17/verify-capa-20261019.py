"""Validate selected CAPA work products; no state transitions or gate effects."""
import difflib
import hashlib
import json
from pathlib import Path
import jsonschema

base = Path(__file__).resolve().parent
candidate = base.parents[4]
folder = base / 'capa-20261019'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
path = folder / 'register.json'
data = read(path)
schema_path = folder / 'forge-cre-capa-record-v1.schema.json'
schema = read(schema_path)
jsonschema.Draft202012Validator.check_schema(schema)
validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
assert sha(schema_path) == data['schema_sha256'] == data['source_pattern']['sha256']
policy = candidate / 'docs/engineering/maestro-lite/capa-policy.json'
assert sha(policy) == data['policy_sha256']
assert data['mode'] == 'OBSERVE_ONLY' and data['selected_findings'] == [135, 222, 238]
assert all(data[k] is False for k in ('historical_backfill_complete', 'automatic_workflow_implemented',
    'capability025_capa_integration', 'full_increment17_complete', 'accepted', 'merged', 'scientific_result'))
for key, item in data['evidence'].items():
    source = candidate / item['path']
    assert source.is_file() and not source.is_symlink()
    if item['kind'] == 'file':
        digest = sha(source)
    else:
        assert item['kind'] == 'review_span'
        text = source.read_text()
        span = text[text.index('\n' + item['start']) + 1:text.index('\n' + item['end'])]
        digest = hashlib.sha256(span.encode()).hexdigest()
    assert digest == item['sha256'], key
ids = {record['capa_id'] for record in data['records']}
assert ids == {'ML-CAPA-135', 'ML-CAPA-222', 'ML-CAPA-238'} and len(data['records']) == 3
for record in data['records']:
    validator.validate(record)
    assert record['policy_sha256'] == data['policy_sha256']
    assert record['observation_window_end'] is None and not record['lesson_ids']
    assert record['state'] != 'EFFECTIVE' and record['root_cause_status'] != 'VERIFIED'
    assert set(record['root_cause_evidence_refs']) <= data['evidence'].keys()
    plan = data['action_plans'][record['capa_id']]
    assert plan['effectiveness'] == dict(status='NOT_DEMONSTRATED', observation_plan=None, independent_confirmation=False)
    for stage in ('correction', 'prevention'):
        assert set(plan[stage]['evidence_refs']) <= data['evidence'].keys()
    if record['capa_id'] != 'ML-CAPA-238':
        assert record['state'] == 'UNRESOLVED' and record['root_cause_status'] == 'UNKNOWN'
        assert record['root_cause_summary'] is None and record['candidate_patch_sha256'] is None
        assert record['prevention_test_id'] is None
    else:
        assert record['state'] == 'FIX_CANDIDATE' and record['root_cause_status'] == 'HYPOTHESIS'
        assert record['candidate_patch_sha256'] == sha(folder / 'cancel-preflight.patch')
        assert plan['prevention']['status'] == 'local_test_passed'
old = Path(read(base / 'active-controller-recovery-20261019d/running.json')['frozen_source_root'])
new = Path(read(base / 'active-control-deadlines-20261019c/running.json')['frozen_source_root'])
relative = 'src/xverse/maestro/dispatcher.py'
assert sha(new / relative) == sha(candidate / relative)
expected = ''.join(difflib.unified_diff((old / relative).read_text().splitlines(keepends=True),
    (new / relative).read_text().splitlines(keepends=True), fromfile='a/' + relative, tofile='b/' + relative))
assert (folder / 'cancel-preflight.patch').read_text() == expected
red = read(base / 'active-control-deadlines-20261019b/counterexample-verification.json')
assert red['phases'] == [dict(phase='source', passed=12, failed=1), dict(phase='wheel', passed=12, failed=1)]
assert all(c['unchanged_frontier'] and c['actual_outcome']['disposition'] == 'failed' for c in red['counterexamples'])
green = read(base / 'active-control-deadlines-20261019c/verification.json')
assert all(p['passed'] == 13 and p['failed'] == 0 for p in green['phases'])
scope = read(base / 'active-control-deadlines-verified-scope.json')
assert scope['source_failure']['finding'] == 222 and scope['phases'][0]['failed'] == 1
original = read(base / 'runtime-collection-execution-20261019b/failure-verification.json')
assert not original['cause_established'] and original['release_gate_open']
result = dict(register_sha256=sha(path), policy_sha256=sha(policy), schema_sha256=sha(schema_path),
    verifier_sha256=sha(Path(__file__)), records_validated=3, evidence_bindings_verified=len(data['evidence']),
    states={r['capa_id']:r['state'] for r in data['records']},
    local_red_green_patch_bound=True, independent_cause_confirmation=False, effectiveness_demonstrated=False,
    full_CAPA_workflow_implemented=False, full_Maestro_backfill_complete=False,
    capability025_capa_integration=False, full_increment17_complete=False, accepted=False, merged=False)
with (folder / 'verification.json').open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(result))
