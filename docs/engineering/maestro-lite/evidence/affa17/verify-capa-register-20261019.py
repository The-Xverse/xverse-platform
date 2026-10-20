"""Read-only schema/evidence check for selected observation registers, no transitions."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import jsonschema

candidate=Path(__file__).resolve().parents[5]
folder=Path(sys.argv[1]).resolve(strict=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
data=read(folder/'register.json')
schema_path=candidate/data['schema_path'] if 'schema_path' in data else folder/'forge-cre-capa-record-v1.schema.json'
assert sha(schema_path)==data['schema_sha256']
schema=read(schema_path)
validator=jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker())
ids=set()
for row in data['records']:
    validator.validate(row)
    assert row['capa_id'] not in ids
    ids.add(row['capa_id'])
    assert row['policy_sha256']==data['policy_sha256']
    assert row['state'] not in ('EFFECTIVE','PREVENTION_TESTED','CAUSE_VERIFIED')
    assert row['root_cause_status']!='VERIFIED' and row['observation_window_end'] is None
    assert set(row['root_cause_evidence_refs'])<=data['evidence'].keys()
    plan=data['action_plans'][row['capa_id']]
    assert plan['effectiveness']['status']=='NOT_DEMONSTRATED' and not plan['effectiveness']['independent_confirmation']
    for stage in ('correction','prevention'):assert set(plan[stage]['evidence_refs'])<=data['evidence'].keys()
for key,item in data['evidence'].items():
    source=candidate/item['path']
    assert source.is_file() and not source.is_symlink()
    if item['kind']=='file':digest=sha(source)
    else:
        assert item['kind']=='review_span'
        text=source.read_text();span=text[text.index('\n'+item['start'])+1:text.index('\n'+item['end'])]
        digest=hashlib.sha256(span.encode()).hexdigest()
    assert digest==item['sha256'],key
if 'parent_register' in data:assert sha(candidate/data['parent_register']['path'])==data['parent_register']['sha256']
assert data['mode']=='OBSERVE_ONLY' and not data['automatic_workflow_implemented']
assert not data['historical_backfill_complete'] and not data['capability025_capa_integration']
result=dict(command=sys.argv,python=sys.version,platform=platform.platform(),jsonschema=importlib.metadata.version('jsonschema'),
    verifier_sha256=sha(Path(__file__)),register_sha256=sha(folder/'register.json'),records_validated=len(ids),
    evidence_bindings_verified=len(data['evidence']),states={r['capa_id']:r['state'] for r in data['records']},
    independent_cause_confirmation=False,effectiveness_demonstrated=False,automatic_workflow_implemented=False,
    full_increment17_complete=False,accepted=False,merged=False)
with (folder/'verification-recheck.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(result))
