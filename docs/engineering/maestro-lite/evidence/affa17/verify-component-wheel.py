"""Exact installed component consumer; not full-platform or M1 acceptance."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
PYTHON = '/tmp/maestro-lite-affa-verify-20261018/bin/python'
FILES = ['test_affa_client.py', 'test_run_bootstrap.py', 'test_run_bootstrap_values.py',
         'test_affa_native.py', 'test_affa_config.py', 'test_affa_protocol.py', 'test_bootstrap.py']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
env.pop('PYTHONPATH', None)
consumer = Path(tempfile.mkdtemp(prefix='maestro-affa17-installed-component-'))
(consumer/'tests/thesis_lite').mkdir(parents=True)
for name in ['tests/__init__.py', 'tests/thesis_lite/__init__.py']:
    shutil.copyfile(ROOT/name, consumer/name)
shutil.copytree(ROOT/'tests/thesis_lite/maestro', consumer/'tests/thesis_lite/maestro',
                ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
shutil.copytree(ROOT/'xdl/profiles', consumer/'xdl/profiles')
modules = {}
for p in sorted((ROOT/'src/xverse/maestro').glob('*.py')):
    name = 'xverse.maestro' + ('.'+p.stem if p.stem != '__init__' else '')
    modules[name] = str(p.relative_to(ROOT))
code = '''import importlib, importlib.resources as r,hashlib,json
names=json.loads(__import__('sys').argv[1]); out={}
for name in names:
 p=__import__('pathlib').Path(importlib.import_module(name).__file__)
 out[name]={'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
print(json.dumps(out))'''
identity = json.loads(subprocess.check_output([PYTHON, '-I', '-c', code, json.dumps(modules)],
    cwd=consumer, env=env, text=True))
for name, source in modules.items():
    assert identity[name]['sha256'] == sha(ROOT/source), name
    assert identity[name]['file'].startswith('/tmp/maestro-lite-affa-verify-20261018/lib/'), name
resources = {}
for p in sorted((ROOT/'src/xverse/maestro/native').glob('*.c')):
    code = "from importlib.resources import files;import hashlib,json; p=files('xverse.maestro').joinpath('native/"+p.name+"');print(json.dumps({'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))"
    item = json.loads(subprocess.check_output([PYTHON,'-I','-c',code],cwd=consumer,env=env,text=True))
    assert item['sha256'] == sha(p) and item['file'].startswith('/tmp/maestro-lite-affa-verify-20261018/lib/')
    resources[p.name] = item
before = {str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'src/xverse/maestro').rglob('*')
    if p.suffix in ('.py','.c')}
before.update({'tests/thesis_lite/maestro/'+n:sha(ROOT/'tests/thesis_lite/maestro'/n) for n in FILES})
command = [PYTHON,'-I','-m','pytest',*[str(consumer/'tests/thesis_lite/maestro'/n) for n in FILES],'-q']
harness = OUT/'component-v5-wheel-harness'
env['MAESTRO_BOUNDARY_RECEIPTS'] = str(harness)
start = time.monotonic()
with (OUT/'component-v5-wheel.log').open('w') as log:
    result = subprocess.run(command,cwd=consumer,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
assert all(sha(ROOT/n)==h for n,h in before.items())
receipt = dict(command=command,cwd=str(consumer),PYTHONPATH='unset',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
    returncode=result.returncode,elapsed_seconds=time.monotonic()-start,timeout_seconds=300,
    log_sha256=sha(OUT/'component-v5-wheel.log'), input_sha256=before, installed_modules=identity,
    installed_native_resources=resources, wheel_sha256=sha(OUT/'component-dist/xverse_xdl-0.4.0-py3-none-any.whl'),
    full_platform_regression=False, full_M1_complete=False, accepted=False)
(OUT/'component-v5-wheel-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(returncode=result.returncode,modules=len(identity),native_resources=len(resources),consumer=str(consumer))))
raise SystemExit(result.returncode)
