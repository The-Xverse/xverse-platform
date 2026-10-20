"""Explicit active restart original source/wheel native composition plus affected admission checks; no full lifecycle claim."""
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
OUT = Path(__file__).resolve().parent / 'native-writer-stream-20261019c'
PYTHON = '/tmp/maestro-lite-affa-active-control-deadlines-target-20261019c/bin/python'
assert OUT.is_dir() and {p.name for p in OUT.iterdir()} <= {'dist', 'build.log'}, 'existing evidence namespace'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, data):
    with (OUT / name).open('x') as stream:
        stream.write(json.dumps(data, indent=2) + '\n')

ROOT = Path(tempfile.mkdtemp(prefix='maestro-native-writer-stream-20261019c-source-'))
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
(OUT/'dist').mkdir()
original_wheel = OUT.parent/'active-control-deadlines-20261019c/dist/xverse_xdl-0.4.0-py3-none-any.whl'
shutil.copyfile(original_wheel,OUT/'dist'/original_wheel.name)
save('installed-reuse.json',dict(original_wheel=str(original_wheel),sha256=sha(original_wheel),immutable_installed_environment=True))
consumer = Path(tempfile.mkdtemp(prefix='maestro-native-writer-stream-20261019c-consumer-'))
shutil.copytree(ROOT / 'tests', consumer / 'tests')
shutil.copytree(ROOT / 'xdl', consumer / 'xdl')
env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1')
env.pop('PYTHONPATH', None)
code = """from pathlib import Path
import importlib,json,hashlib
base=Path(importlib.import_module('xverse.maestro').__file__).parent
print(json.dumps({str(p.relative_to(base)):{'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in list(base.glob('*.py'))+list((base/'native').glob('*.c'))}))"""
identity = json.loads(subprocess.check_output([PYTHON, '-I', '-c', code], cwd=consumer, env=env, text=True))
assert len(identity) == 46
for n, row in identity.items():
    assert sha(Path(row['file'])) == row['sha256'] == sha(ROOT / 'src/xverse/maestro' / n)
save('installed-identity.json', identity)
save('running.json', dict(candidate=str(CANDIDATE), frozen_source_root=str(ROOT), consumer=str(consumer),
    verification_python=PYTHON, installed_identity_sha256=sha(OUT / 'installed-identity.json')))
files = ['test_native_writer_stream_faults.py']
command = [PYTHON, '-m', 'pytest', str(ROOT / 'tests/thesis_lite/maestro' / files[0]), '-q', '--collect-only']
with (OUT / 'collected.log').open('x') as log:
    collected = subprocess.run(command, cwd=ROOT, env=dict(env, PYTHONPATH=str(ROOT/'src')),
        stdout=log, stderr=subprocess.STDOUT, timeout=30)
assert collected.returncode == 0
match = re.search(r'(\d+) tests collected', (OUT/'collected.log').read_text());assert match
expected=int(match.group(1));assert expected==4
save('collection-receipt.json',dict(command=command,cwd=str(ROOT),returncode=0,collected=expected,
    log_sha256=sha(OUT/'collected.log')))
shutil.copyfile(OUT.parent/'capture-retained-teardown.py',OUT/'capture-public.py')
rows=[]
for group,selector in [('loader','loader'),('faults','not loader')]:
    for phase,cwd,isolated in [('source',ROOT,False),('wheel',consumer,True)]:
        label=group+'-'+phase
        private=Path(tempfile.mkdtemp(prefix='maestro-native-writer-stream-20261019c-'+label+'-private-'))
        environment=dict(env,MAESTRO_BOUNDARY_RECEIPTS=str(OUT/(label+'-harness')))
        if not isolated:environment['PYTHONPATH']=str(ROOT/'src')
        command=[PYTHON,*(['-I'] if isolated else []),'-m','pytest',str(cwd/'tests/thesis_lite/maestro'/files[0]),
            '-q','-k',selector,'--basetemp',str(private)]
        began=time.monotonic()
        with (OUT/(label+'.log')).open('x') as log:
            result=subprocess.run(command,cwd=cwd,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=300)
        assert all(sha(ROOT/n)==h for n,h in frozen.items())
        assert all(sha(Path(row['file']))==row['sha256'] for row in identity.values())
        with (OUT/(label+'-public-capture.log')).open('x') as log:
            capture=subprocess.run([PYTHON,'-I',str(OUT/'capture-public.py'),label,str(private)],
                cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=30)
        row=dict(group=group,phase=phase,command=command,cwd=str(cwd),returncode=result.returncode,
            elapsed_seconds=time.monotonic()-began,original_private_basetemp=str(private),
            public_capture_returncode=capture.returncode,log_sha256=sha(OUT/(label+'.log')),
            input_manifest_sha256=sha(OUT/'frozen-inputs.json'))
        save(label+'-receipt.json',row);rows.append(row)
        save('result-after-'+label+'.json',dict(receipts=rows,collected_per_phase=4,
            all_groups_executed=len(rows)==4,component_checks_passed=len(rows)==4 and all(r['returncode']==r['public_capture_returncode']==0 for r in rows),
            source_manifest_sha256=sha(OUT/'frozen-inputs.json'),wheel_sha256=sha(OUT/'dist/xverse_xdl-0.4.0-py3-none-any.whl'),
            full_platform_regression=False,full_M1_complete=False,stable_increment17=False,accepted=False,merged=False))
        print(label,result.returncode,flush=True)
    if group=='loader' and any(r['returncode'] or r['public_capture_returncode'] for r in rows):
        save('stages-not-executed.json',dict(reason='original loader proof failed',W02='NOT_DEMONSTRATED',W03='NOT_DEMONSTRATED'))
        raise SystemExit(1)
raise SystemExit(0 if all(r['returncode']==r['public_capture_returncode']==0 for r in rows) else 1)
