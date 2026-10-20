"""Repeat the failed full source run without concurrent wheel-suite load.

Keep the actual passing installed-wheel receipt and its exact product/test inputs.
Never relabel the failed concurrent run as passing or loosen its operation bounds.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

root = Path(__file__).resolve().parents[5]
out = Path(__file__).resolve().parent
python = '/tmp/maestro-lite-recovery-verify-20261018/bin/python'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda name: json.loads((out / name).read_text())
before_manifest = read('failed-full-v1/source-manifest.json')
manifest = read('source-manifest.json')
changed = {p for p,h in before_manifest['input_sha256'].items() if manifest['input_sha256'].get(p) != h}
assert changed == {
    'docs/engineering/maestro-lite/review-recovery16.md',
    'docs/engineering/maestro-lite/evidence/recovery16/prepare-verification.py',
}
assert set(manifest['input_sha256']) - set(before_manifest['input_sha256']) == {
    'docs/engineering/maestro-lite/evidence/recovery16/verify-serialized-source.py'
}
assert all(sha(root / p) == h for p,h in manifest['input_sha256'].items())
wheel = read('wheel-consumer-tests-receipt.json')
assert wheel['returncode'] == 0 and sha(out / 'wheel-consumer-tests.log') == wheel['log_sha256']
identity = read('installed-module-identity.json')
for name, entry in identity.items():
    assert sha(Path(entry['file'])) == entry['sha256']
    path = root / 'src' / Path(*name.split('.'))
    path = path.with_suffix('.py') if path.with_suffix('.py').is_file() else path / '__init__.py'
    assert sha(path) == entry['sha256']
assert len(identity) == 27
sys.argv = ['verify-recovery16.py', python]
spec = importlib.util.spec_from_file_location('recovery_verifier',root / 'docs/engineering/maestro-lite/verify-recovery16.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ENV['PYTHONPATH'] = str(root / 'src')
receipt = module.run('platform-tests-serial', [python,'-m','pytest','tests','-q','--disable-warnings'], root, 1100)
module.audit_harness(
    [receipt, wheel], read('installed-native-source.json'),
    read('installed-catalog-native-source.json'), read('installed-bootstrap-native-source.json'),
    manifest['input_sha256'], identity, module.trace_check(),
)
(out / 'serialized-verification-inputs.json').write_text(json.dumps({
    'revision':manifest['revision'],
    'failed_full_run_retained':True,
    'product_test_native_inputs_unchanged':True,
    'changed_metadata_only':sorted(changed),
    'new_serial_driver':True,
    'installed_wheel_suite_reused_after_passing':True,
    'actual_installed_module_hashes_rechecked':27,
    'full_source_repeated_without_concurrent_wheel_suite':True,
    'product_and_fixture_deadlines_unchanged':True,
    'failed_manifest_sha256':sha(out / 'failed-full-v1/source-manifest.json'),
    'current_manifest_sha256':sha(out / 'source-manifest.json'),
},indent=2)+'\n')
