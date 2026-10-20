"""Read-only engineering profile over original retained OPEN evidence; no native run."""
from pathlib import Path
import cProfile
import hashlib
import importlib
import io
import json
import pstats
import time
from xverse.argus import EvidenceStore
from xverse.maestro.coverage import FIELDS
from xverse.maestro.lifecycle_evidence import OutcomeJournal

BASE=Path(__file__).resolve().parent;OUT=BASE/'mirror-profile-20261019a'
assert not OUT.exists();OUT.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
namespace=BASE/'terminal-scope-20261019a'
index=json.loads((namespace/'source-public-evidence-index.json').read_bytes())
entry=next(e for e in index if 'test_actual_lazy_nominal_stage' in e['snapshot'])
p=namespace/entry['snapshot'];assert sha(p)==entry['sha256']
snapshot=json.loads(p.read_bytes());root=Path(snapshot['original_fixture'])/'argus'
manifest=root/'manifest.json';stream=root/'events.jsonl'
assert json.loads(manifest.read_bytes())['writerState']=='open'
assert manifest.stat().st_size<=1<<20 and stream.stat().st_size<=16<<20
before={p.name:sha(p) for p in (manifest,stream)}
actual=EvidenceStore.read_run(root).records()
# Diagnostic checker reuses actual caller-owned public fields. It does not
# reconstruct claims or confer their original authority; claim loop stays empty.
checker=object.__new__(OutcomeJournal);checker.root=root;checker.retained_claims={}
checker.events={e['eventId']:{k:e.get(k) for k in FIELDS} for e in actual
                if e.get('extensions',{}).get('xverse.maestro') is not None}
profile=cProfile.Profile();elapsed=[]
profile.enable()
for _ in range(8):
    began=time.perf_counter();checker._mirrors({});elapsed.append(time.perf_counter()-began)
profile.disable()
assert before=={p.name:sha(p) for p in (manifest,stream)}
profile.dump_stats(str(OUT/'profile.pstats'))
buffer=io.StringIO();pstats.Stats(profile,stream=buffer).sort_stats('cumulative').print_stats(24)
with (OUT/'profile.txt').open('x') as output:output.write(buffer.getvalue())
module=Path(importlib.import_module('xverse.maestro.lifecycle_evidence').__file__)
report=dict(original_public_snapshot=str(p),original_public_snapshot_sha256=sha(p),original_root=str(root),
 original_bytes=before,events=len(actual),caller_field_events=len(checker.events),
 measured_seconds=elapsed,source_sha256=sha(module),profile_sha256=sha(OUT/'profile.pstats'),
 detail_sha256=sha(OUT/'profile.txt'),script_sha256=sha(Path(__file__)),
 diagnostic_only=True,claim_authority_reconstructed=False,original_claim_checks_exercised=False,
 evidence_mutated=False,native_run_started=False,scientific_result=False,timeout_root_cause_proven=False)
with (OUT/'receipt.json').open('x') as output:json.dump(report,output,indent=2);output.write('\n')
print(json.dumps(dict(events=len(actual),caller_fields=len(checker.events),seconds=elapsed)))
print(buffer.getvalue())
