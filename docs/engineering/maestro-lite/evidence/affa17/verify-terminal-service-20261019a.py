"""Exact isolated source/wheel collection execution checks; no full runtime claim."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import time

CANDIDATE = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent / 'terminal-service-20261019a'
PYTHON = '/tmp/maestro-lite-affa-terminal-service-20261019a/bin/python'
assert OUT.is_dir() and {p.name for p in OUT.iterdir()} <= {'dist', 'build.log'}, 'existing evidence namespace'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, data):
    with (OUT / name).open('x') as stream:
        stream.write(json.dumps(data, indent=2) + '\n')

ROOT = Path(tempfile.mkdtemp(prefix='maestro-terminal-service-20261019a-source-'))
for name in ('src', 'xdl'):
    shutil.copytree(CANDIDATE / name, ROOT / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
(ROOT / 'tests/thesis_lite').mkdir(parents=True)
for name in ('tests/__init__.py', 'tests/thesis_lite/__init__.py', 'pyproject.toml', 'README.md', 'LICENSE'):
    shutil.copyfile(CANDIDATE / name, ROOT / name)
shutil.copytree(CANDIDATE / 'tests/thesis_lite/maestro', ROOT / 'tests/thesis_lite/maestro',
                ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
paths = [p for p in ROOT.rglob('*') if p.is_file()]
frozen = {str(p.relative_to(ROOT)): sha(p) for p in paths}
assert all(sha(CANDIDATE / n) == h for n, h in frozen.items())
save('frozen-inputs.json', frozen)
with tarfile.open(OUT / 'tested-inputs.tar.gz', 'w:gz') as archive:
    for p in paths:
        archive.add(p, arcname=str(p.relative_to(ROOT)))
consumer = Path(tempfile.mkdtemp(prefix='maestro-terminal-service-20261019a-consumer-'))
shutil.copytree(ROOT / 'tests', consumer / 'tests')
shutil.copytree(ROOT / 'xdl', consumer / 'xdl')
env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1')
env.pop('PYTHONPATH', None)
code = """from pathlib import Path
import importlib,json,hashlib
base=Path(importlib.import_module('xverse.maestro').__file__).parent
print(json.dumps({str(p.relative_to(base)):{'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in list(base.glob('*.py'))+list((base/'native').glob('*.c'))}))"""
identity = json.loads(subprocess.check_output([PYTHON, '-I', '-c', code], cwd=consumer, env=env, text=True))
assert len(identity) == 41
for n, row in identity.items():
    assert sha(Path(row['file'])) == row['sha256'] == sha(ROOT / 'src/xverse/maestro' / n)
save('installed-identity.json', identity)
save('running.json', dict(candidate=str(CANDIDATE), frozen_source_root=str(ROOT), consumer=str(consumer),
    verification_python=PYTHON, installed_identity_sha256=sha(OUT / 'installed-identity.json')))
files = ['test_terminal_service.py', 'test_run_renewal.py', 'test_run_bootstrap.py', 'test_bootstrap.py', 'test_collection_runtime.py']
command = [PYTHON, '-m', 'pytest', *[str(ROOT / 'tests/thesis_lite/maestro' / n) for n in files], '-q', '--collect-only']
with (OUT / 'collected.log').open('x') as log:
    collected = subprocess.run(command, cwd=ROOT, env=dict(env, PYTHONPATH=str(ROOT / 'src')),
        stdout=log, stderr=subprocess.STDOUT, timeout=30)
assert collected.returncode == 0
match = re.search(r'(\d+) tests collected', (OUT / 'collected.log').read_text()); assert match
expected = int(match.group(1))
save('collection-receipt.json', dict(command=command, cwd=str(ROOT), returncode=0, collected=expected,
    log_sha256=sha(OUT / 'collected.log')))
shutil.copyfile(OUT.parent / 'capture-retained-teardown.py', OUT / 'capture-public.py')
rows = []
for phase, cwd, isolated in [('source', ROOT, False), ('wheel', consumer, True)]:
    private = Path(tempfile.mkdtemp(prefix='maestro-terminal-service-20261019a-' + phase + '-private-'))
    environment = dict(env, MAESTRO_BOUNDARY_RECEIPTS=str(OUT / (phase + '-harness')))
    if not isolated:
        environment['PYTHONPATH'] = str(ROOT / 'src')
    command = [PYTHON, *(['-I'] if isolated else []), '-m', 'pytest',
        *[str(cwd / 'tests/thesis_lite/maestro' / n) for n in files], '-q', '--basetemp', str(private)]
    began = time.monotonic()
    with (OUT / (phase + '.log')).open('x') as log:
        result = subprocess.run(command, cwd=cwd, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=300)
    assert all(sha(ROOT / n) == h for n, h in frozen.items())
    assert all(sha(Path(row['file'])) == row['sha256'] for row in identity.values())
    capture = [PYTHON, '-I', str(OUT / 'capture-public.py'), phase, str(private)]
    with (OUT / (phase + '-public-capture.log')).open('x') as log:
        observed = subprocess.run(capture, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=30)
    row = dict(command=command, cwd=str(cwd), returncode=result.returncode,
        elapsed_seconds=time.monotonic() - began, original_private_basetemp=str(private),
        public_capture_returncode=observed.returncode, frozen_source_root=str(ROOT),
        log_sha256=sha(OUT / (phase + '.log')), input_manifest_sha256=sha(OUT / 'frozen-inputs.json'))
    save(phase + '-receipt.json', row); rows.append(row)
    # Separate immutable phase summaries; do not replace historical interim files.
    save('result-after-' + phase + '.json', dict(receipts=rows, collected_per_phase=expected,
        all_requested_phases_executed=len(rows) == 2, component_checks_passed=len(rows) == 2
        and all(r['returncode'] == r['public_capture_returncode'] == 0 for r in rows),
        source_manifest_sha256=sha(OUT / 'frozen-inputs.json'),
        installed_identity_sha256=sha(OUT / 'installed-identity.json'),
        wheel_sha256=sha(OUT / 'dist/xverse_xdl-0.4.0-py3-none-any.whl'),
        installed_maestro_modules=37, native_resources=4, full_platform_regression=False,
        full_M1_complete=False, stable_increment17=False, accepted=False, merged=False))
    print(phase, result.returncode, 'collected', expected, flush=True)
    if result.returncode or observed.returncode:
        raise SystemExit(result.returncode or observed.returncode)
