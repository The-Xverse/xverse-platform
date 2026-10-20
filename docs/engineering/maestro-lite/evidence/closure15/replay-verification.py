"""Repeat only the repaired audit after proving every tested runtime input unchanged."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time

ROOT = Path('/home/jefferson/xverse-platform-worktrees/maestro-lite-closure-20261018')
OUT = ROOT / 'docs/engineering/maestro-lite/evidence/closure15'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
save = lambda n, d: (OUT/n).write_text(json.dumps(d, indent=2)+'\n')
old = json.loads((OUT/'tested-source-manifest-v5.json').read_text())
changed = {'docs/engineering/maestro-lite/verify-closure15.py',
           'docs/engineering/maestro-lite/review-closure15.md'}
differences = {p: {'tested_sha256': h, 'audit_sha256': sha(ROOT/p)}
               for p, h in old['input_sha256'].items() if sha(ROOT/p) != h}
assert set(differences) == changed
assert all(sha(ROOT/p) == h for p, h in old['input_sha256'].items() if p not in changed)
paths = set(old['input_sha256']) | {'docs/engineering/maestro-lite/evidence/closure15/replay-verification.py'}
current = dict(old, revision='ML3-CLOSURE15-2026-10-18-v6',
               tested_source_manifest='tested-source-manifest-v5.json',
               tested_source_manifest_sha256=sha(OUT/'tested-source-manifest-v5.json'),
               input_sha256={p: sha(ROOT/p) for p in sorted(paths)})
save('source-manifest.json', current)
inputs = json.loads((OUT/'engineering-inputs.json').read_text())
inputs.update(revision=current['revision'], test_source_revision=old['revision'],
              verification_only_successor=True)
save('engineering-inputs.json', inputs)
receipts = [json.loads((OUT/(n+'-receipt.json')).read_text())
            for n in ['platform-tests', 'wheel-consumer-tests']]
for receipt in receipts:
    assert receipt['returncode'] == 0
    assert receipt['log_sha256'] == sha(OUT/('platform-tests.log' if receipt['command'][1] == '-m' else 'wheel-consumer-tests.log'))
identity = json.loads((OUT/'installed-module-identity.json').read_text())
probe = '''import hashlib,importlib,json,pathlib,sys
print(json.dumps({n:{'file':str(pathlib.Path(importlib.import_module(n).__file__).resolve()),'sha256':hashlib.sha256(pathlib.Path(importlib.import_module(n).__file__).read_bytes()).hexdigest()} for n in json.loads(sys.argv[1])}))'''
env = dict(os.environ); env.pop('PYTHONPATH', None)
with tempfile.TemporaryDirectory(prefix='maestro-closure15-audit-probe-') as temporary:
    actual = json.loads(subprocess.check_output([sys.executable, '-I', '-c', probe, json.dumps(list(identity))], cwd=temporary, env=env, text=True))
    assert actual == identity
    for name, resource_name in [('installed-native-source.json','lease_guard.c'),
                                ('installed-catalog-native-source.json','catalog_launcher.c'),
                                ('installed-bootstrap-native-source.json','bootstrap.c')]:
        record = json.loads((OUT/name).read_text())
        assert sha(Path(record['path'])) == record['sha256'] == sha(ROOT/('src/xverse/maestro/native/'+resource_name))
        assert str(ROOT) not in record['path']
save('verification-replay-inputs.json', dict(schema_version=1,
     test_revision=old['revision'], audit_revision=current['revision'],
     tested_source_manifest_sha256=sha(OUT/'tested-source-manifest-v5.json'),
     changed_metadata_only=differences, added_audit_script_sha256=sha(Path(__file__)),
     all_tested_product_test_native_and_runtime_inputs_unchanged=True,
     unchanged_frozen_inputs=len(old['input_sha256'])-len(changed),
     actual_installed_modules_reprobed=len(identity), native_resources_rechecked=3,
     full_test_receipts_reused_without_rerunning=True,
     original_audit_exit_code=1, original_failure_log='verification-driver.log',
     original_failure_log_sha256=sha(OUT/'verification-driver.log')))
sys.argv = [str(ROOT/'docs/engineering/maestro-lite/verify-closure15.py'), sys.executable]
spec = importlib.util.spec_from_file_location('closure_verifier', sys.argv[0])
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
began = time.monotonic()
module.audit_harness(receipts,
    json.loads((OUT/'installed-native-source.json').read_text()),
    json.loads((OUT/'installed-catalog-native-source.json').read_text()),
    json.loads((OUT/'installed-bootstrap-native-source.json').read_text()),
    module.snapshot(), identity, module.trace_check())
run = json.loads((OUT/'verification-run.json').read_text())
run.update(test_source_revision=old['revision'], audit_revision=current['revision'],
           verification_replay_inputs_sha256=sha(OUT/'verification-replay-inputs.json'),
           audit_repeated=True, full_tests_repeated=False,
           audit_elapsed_seconds=time.monotonic()-began)
save('verification-run.json', run)
print(json.dumps(dict(audit_returncode=0, test_receipts_reused=2,
                     product_and_test_changes=0, partial_endpoints=run['partial_endpoints_checked'])))
