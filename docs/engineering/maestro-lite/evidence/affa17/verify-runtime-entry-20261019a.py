"""Original launcher/registry source/wheel owned startup and v6 composition; full increment17 remains open."""
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
OUT = Path(__file__).resolve().parent / 'runtime-entry-20261019a'
PYTHON = '/tmp/maestro-lite-runtime-entry-target-20261019a/bin/python'
OUT.mkdir(exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, data):
    with (OUT / name).open('x') as stream:
        stream.write(json.dumps(data, indent=2) + '\n')

ROOT = Path(tempfile.mkdtemp(prefix='maestro-runtime-entry-20261019a-source-'))
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
build_python = '/tmp/maestro-lite-affa-verify-20261018/bin/python'
assert not Path(PYTHON).parent.parent.exists(), 'new installed environment required'
subprocess.run(['/tmp/maestro-lite-affa-active-controller-recovery-target-20261019d/bin/python', '-m', 'venv', '--system-site-packages', str(Path(PYTHON).parent.parent)], check=True, timeout=30)
with (OUT / 'build.log').open('x') as log:
    subprocess.run([build_python, '-m', 'build', '--wheel', '--no-isolation', '--outdir', str(OUT/'dist'), str(ROOT)], stdout=log, stderr=subprocess.STDOUT, check=True, timeout=60)
wheel = next((OUT/'dist').glob('*.whl'))
with (OUT/'install.log').open('x') as log:
    subprocess.run([PYTHON, '-m', 'pip', 'install', '--no-deps', '--force-reinstall', str(wheel)], stdout=log, stderr=subprocess.STDOUT, check=True, timeout=60)
consumer = Path(tempfile.mkdtemp(prefix='maestro-runtime-entry-20261019a-consumer-'))
shutil.copytree(ROOT / 'tests', consumer / 'tests')
shutil.copytree(ROOT / 'xdl', consumer / 'xdl')
env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1')
env.pop('PYTHONPATH', None)
code = """from pathlib import Path
import importlib,json,hashlib
base=Path(importlib.import_module('xverse.maestro').__file__).parent
print(json.dumps({str(p.relative_to(base)):{'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in list(base.glob('*.py'))+list((base/'native').glob('*.c'))}))"""
identity = json.loads(subprocess.check_output([PYTHON, '-I', '-c', code], cwd=consumer, env=env, text=True))
assert len(identity) == 50
for n, row in identity.items():
    assert sha(Path(row['file'])) == row['sha256'] == sha(ROOT / 'src/xverse/maestro' / n)
save('installed-identity.json', identity)
save('running.json', dict(candidate=str(CANDIDATE), frozen_source_root=str(ROOT), consumer=str(consumer),
    verification_python=PYTHON, installed_identity_sha256=sha(OUT / 'installed-identity.json')))
files = ['test_runtime_evidence.py', 'test_runtime_entry.py', 'test_runtime_admission.py', 'test_bootstrap_launcher.py']
command = [PYTHON, '-m', 'pytest', *[str(ROOT / 'tests/thesis_lite/maestro' / n) for n in files], '-q', '--collect-only']
with (OUT / 'collected.log').open('x') as log:
    collected = subprocess.run(command, cwd=ROOT, env=dict(env, PYTHONPATH=str(ROOT / 'src')),
        stdout=log, stderr=subprocess.STDOUT, timeout=30)
assert collected.returncode == 0
match = re.search(r'(\d+) tests collected', (OUT / 'collected.log').read_text()); assert match
expected = int(match.group(1))
save('collection-receipt.json', dict(command=command, cwd=str(ROOT), returncode=0, collected=expected,
    log_sha256=sha(OUT / 'collected.log')))
shutil.copyfile(OUT.parent / 'capture-runtime-entry-20261019.py', OUT / 'capture-public.py')
rows = []
for name in files:
    cohort=name.removeprefix('test_').removesuffix('.py')
    for phase,cwd,isolated in [('source',ROOT,False),('wheel',consumer,True)]:
        label=cohort+'-'+phase
        private=Path(tempfile.mkdtemp(prefix='maestro-runtime-entry-20261019a-'+label+'-private-'))
        environment=dict(env,MAESTRO_BOUNDARY_RECEIPTS=str(OUT/(label+'-harness')))
        if not isolated:environment['PYTHONPATH']=str(ROOT/'src')
        command=[PYTHON,*(['-I'] if isolated else []),'-m','pytest',str(cwd/'tests/thesis_lite/maestro'/name),'-q','--basetemp',str(private)]
        began=time.monotonic()
        with (OUT/(label+'.log')).open('x') as log:
            result=subprocess.run(command,cwd=cwd,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=300)
        assert all(sha(ROOT/n)==h for n,h in frozen.items())
        assert all(sha(Path(row['file']))==row['sha256'] for row in identity.values())
        with (OUT/(label+'-public-capture.log')).open('x') as log:
            capture=subprocess.run([PYTHON,'-I',str(OUT/'capture-public.py'),label,str(private)],cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=30)
        row=dict(cohort=cohort,phase=phase,command=command,cwd=str(cwd),returncode=result.returncode,elapsed_seconds=time.monotonic()-began,
            original_private_basetemp=str(private),public_capture_returncode=capture.returncode,log_sha256=sha(OUT/(label+'.log')),input_manifest_sha256=sha(OUT/'frozen-inputs.json'))
        save(label+'-receipt.json',row);rows.append(row)
        save('result-after-'+label+'.json',dict(receipts=rows,collected_per_phase=expected,all_requested_cohorts_executed=len(rows)==2*len(files),
            component_checks_passed=len(rows)==2*len(files) and all(r['returncode']==r['public_capture_returncode']==0 for r in rows),
            source_manifest_sha256=sha(OUT/'frozen-inputs.json'),wheel_sha256=sha(OUT/'dist/xverse_xdl-0.4.0-py3-none-any.whl'),
            full_platform_regression=False,full_M1_complete=False,stable_increment17=False,accepted=False,merged=False))
        print(label,result.returncode,flush=True)
    if any(r['returncode'] or r['public_capture_returncode'] for r in rows):
        save('regression-not-executed.json',dict(reason='original requested cohort failed; no unchanged retry',remaining_modules=files[files.index(name)+1:]))
        raise SystemExit(1)
raise SystemExit(0 if all(r['returncode']==r['public_capture_returncode']==0 for r in rows) else 1)
