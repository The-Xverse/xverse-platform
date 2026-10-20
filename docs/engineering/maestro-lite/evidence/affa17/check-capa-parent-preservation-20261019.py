"""Check additive evidence identities against the exact declared CAPA parent."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[5]
register = Path(sys.argv[1]).resolve(strict=True)
output = Path(sys.argv[2])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
child = json.loads(register.read_bytes())
reference = child['parent_register']
parent_path = root / reference['path']
parent = json.loads(parent_path.read_bytes())
assert sha(parent_path) == reference['sha256']
changed = sorted(key for key, value in parent['evidence'].items()
                 if child['evidence'].get(key) != value)
parent_records = {r['capa_id']: r for r in parent['records']}
child_records = {r['capa_id']: r for r in child['records']}
lost_records = sorted(parent_records.keys() - child_records.keys())
record_violations = []
for key in parent_records.keys() & child_records.keys():
    old, new = parent_records[key], child_records[key]
    if (any(old[field] != new[field] for field in ('created_at', 'policy_sha256'))
            or not set(old['incident_ids']) <= set(new['incident_ids'])
            or not set(old['root_cause_evidence_refs']) <= set(new['root_cause_evidence_refs'])):
        record_violations.append(key)
policy_changed = any(child[k] != parent[k] for k in ('schema_sha256', 'policy_sha256'))
passed = not (changed or lost_records or record_violations or policy_changed)
result = dict(checker_sha256=sha(Path(__file__)), command=sys.argv,
    register_sha256=sha(register), parent_register_sha256=sha(parent_path),
    parent_evidence_bindings_checked=len(parent['evidence']),
    changed_parent_evidence_ids=changed, lost_parent_records=lost_records,
    old_record_identity_or_reference_violations=sorted(record_violations),
    policy_or_schema_changed=policy_changed, parent_preserved=passed,
    returncode=0 if passed else 1, native_execution=False,
    semantic_correctness_proven=False, independent_cause_confirmation=False,
    effectiveness_demonstrated=False, accepted=False)
with output.open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(result))
raise SystemExit(result['returncode'])
