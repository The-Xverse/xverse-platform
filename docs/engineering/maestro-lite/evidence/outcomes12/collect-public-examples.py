"""Supplemental public fixture bytes; deliberately no inferred suite attribution."""
from pathlib import Path
import hashlib,json
from jsonschema import Draft202012Validator
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse_xdl.lifecycle import FileEvidenceJournal
root=Path('/home/jefferson/xverse-platform-worktrees/maestro-lite-outcomes-20261018')
out=root/'docs/engineering/maestro-lite/evidence/outcomes12'
schema=json.loads((root/'tests/thesis_lite/maestro/lifecycle-payload-v2.schema.json').read_text())
validator=Draft202012Validator(schema)
examples=[]
for session in sorted(Path('/tmp/pytest-of-jefferson').glob('pytest-[0-9]*')):
 for pattern in ('test_real_start_probe_and_depe*','test_public_source_hashes_and_*'):
  for case in sorted(session.glob(pattern)):
   if case.is_symlink() or not (case/'m3.jsonl').is_file() or not (case/'argus/manifest.json').is_file():continue
   journal=FileEvidenceJournal(case/'m3.jsonl').public_records()
   reader=EvidenceStore.read_run(case/'argus');events=reader.records()
   if not any(e.get('extensions',{}).get('xverse.maestro',{}).get('action')=='started' for e in events):continue
   for event in events:
    if 'xverse.maestro' not in event.get('extensions',{}):continue
    payload=event['extensions']['xverse.maestro'];validator.validate(payload)
    for reference in payload['sourceRefs']:
     if reference['kind']=='m3-record':
      record=next(r for r in journal if r['sequence']==reference['sequence'])
      assert reference['sha256']=='sha256:'+hashlib.sha256(canonical_bytes(record)).hexdigest()
   encoded=json.dumps(events)
   assert 'private-process-nonce-' not in encoded and 'maestro-boundary:' not in encoded and 'MAESTRO_VISIBLE' not in encoded
   examples.append({'retained_pytest_session':session.name,'fixture_case':case.name,'public_m3_records':journal,'argus_events':events,'writer_state_observed':reader.manifest['writerState'],'lifecycle_complete':False})
assert examples
(out/'public-fixture-examples.json').write_text(json.dumps({'classification':'supplemental retained owned fixture bytes; no inferred source-versus-wheel suite attribution','schema_file_sha256':hashlib.sha256((root/'tests/thesis_lite/maestro/lifecycle-payload-v2.schema.json').read_bytes()).hexdigest(),'examples':examples,'full_runtime_ready':False},indent=2)+'\n')
print(json.dumps({'supplemental_public_examples':len(examples),'all_m3_source_hashes_and_payload_schemas_checked':True,'lifecycle_complete':False}))
