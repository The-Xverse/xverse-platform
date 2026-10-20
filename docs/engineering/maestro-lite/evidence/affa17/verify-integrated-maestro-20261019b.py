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
OUT = Path(__file__).resolve().parent / 'integrated-maestro-20261019b'
PYTHON = '/tmp/maestro-lite-integrated-maestro-target-20261019b/bin/python'
OUT.mkdir(exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, data):
    with (OUT / name).open('x') as stream:
        stream.write(json.dumps(data, indent=2) + '\n')

ROOT = Path(tempfile.mkdtemp(prefix='maestro-integrated-maestro-20261019b-source-'))
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
consumer = Path(tempfile.mkdtemp(prefix='maestro-integrated-maestro-20261019b-consumer-'))
shutil.copytree(ROOT / 'tests', consumer / 'tests')
shutil.copytree(ROOT / 'xdl', consumer / 'xdl')
env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1')
env.pop('PYTHONPATH', None)
code = """from pathlib import Path
import importlib,json,hashlib
base=Path(importlib.import_module('xverse.maestro').__file__).parent
print(json.dumps({str(p.relative_to(base)):{'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in list(base.glob('*.py'))+list((base/'native').glob('*.c'))}))"""
identity = json.loads(subprocess.check_output([PYTHON, '-I', '-c', code], cwd=consumer, env=env, text=True))
assert len(identity) == 51
for n, row in identity.items():
    assert sha(Path(row['file'])) == row['sha256'] == sha(ROOT / 'src/xverse/maestro' / n)
save('installed-identity.json', identity)
save('running.json', dict(candidate=str(CANDIDATE), frozen_source_root=str(ROOT), consumer=str(consumer),
    verification_python=PYTHON, installed_identity_sha256=sha(OUT / 'installed-identity.json')))
plugin=OUT/'receipt_namespace.py'
with plugin.open('x') as stream:stream.write('''import os
from pathlib import Path
import pytest
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    root=Path(os.environ['MAESTRO_FULL_RECEIPT_ROOT'])
    target=root/item.path.stem
    target.mkdir(parents=True,exist_ok=True)
    os.environ['MAESTRO_BOUNDARY_RECEIPTS']=str(target)
''')
compile(plugin.read_text(),str(plugin),'exec')
save('control-inputs.json',dict(driver_sha256=sha(Path(__file__)),plugin_sha256=sha(plugin),
    purpose='one required combined current Maestro regression, no unchanged retry',
    full_platform_regression=False,original_stability_findings=[135,222,286,287,318,324,330,331,332,337,338]))
collect_command=[PYTHON,'-m','pytest',str(ROOT/'tests/thesis_lite/maestro'),'-q','--collect-only']
with (OUT/'collected.log').open('x') as log:
    collected=subprocess.run(collect_command,cwd=ROOT,env=dict(env,PYTHONPATH=str(ROOT/'src')),stdout=log,stderr=subprocess.STDOUT,timeout=60)
assert collected.returncode==0
match=re.search(r'(\d+) tests? collected',(OUT/'collected.log').read_text());assert match
expected=int(match.group(1));assert expected>0
save('collection-receipt.json',dict(command=collect_command,returncode=0,collected=expected,log_sha256=sha(OUT/'collected.log')))
rows=[]
for phase,cwd,isolated in [('source',ROOT,False),('wheel',consumer,True)]:
    label='maestro_full-'+phase
    private=Path(tempfile.mkdtemp(prefix='maestro-integrated-20261019b-'+phase+'-private-'))
    harness=OUT/(label+'-harness');harness.mkdir()
    environment=dict(env,MAESTRO_FULL_RECEIPT_ROOT=str(harness),MAESTRO_BOUNDARY_RECEIPTS=str(harness))
    if not isolated:environment['PYTHONPATH']=str(ROOT/'src')
    args=[str(cwd/'tests/thesis_lite/maestro'),'-q','-ra','--basetemp',str(private)]
    wrapper="import importlib.util,pytest; spec=importlib.util.spec_from_file_location('owned_receipt_namespace',"+repr(str(plugin))+"); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); raise SystemExit(pytest.main("+repr(args)+",plugins=[module]))"
    command=[PYTHON,*(['-I'] if isolated else []),'-c',wrapper]
    began=time.monotonic();timed_out=False
    with (OUT/(label+'.log')).open('x') as log:
        process=subprocess.Popen(command,cwd=cwd,env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        save(label+'-started.json',dict(command=command,cwd=str(cwd),original_pid=process.pid,private_basetemp=str(private),
            receipt_root=str(harness),collected=expected,plugin_sha256=sha(plugin)))
        print(label,'started',process.pid,'collected',expected,flush=True)
        try:code=process.wait(timeout=3600)
        except subprocess.TimeoutExpired:
            timed_out=True
            try:os.killpg(process.pid,__import__('signal').SIGKILL)
            except ProcessLookupError:pass
            code=process.wait()
    assert all(sha(ROOT/n)==h for n,h in frozen.items())
    assert all(sha(Path(row['file']))==row['sha256'] for row in identity.values())
    row=dict(cohort='maestro_full',phase=phase,command=command,cwd=str(cwd),returncode=code,
        elapsed_seconds=time.monotonic()-began,original_private_basetemp=str(private),
        original_pid=process.pid,outer_timeout=timed_out,descendant_cleanup_unknown=timed_out,
        log_sha256=sha(OUT/(label+'.log')),input_manifest_sha256=sha(OUT/'frozen-inputs.json'),
        receipt_namespace='per actual test module before fixture setup',plugin_sha256=sha(plugin))
    save(label+'-receipt.json',row);rows.append(row)
    save('result-after-'+phase+'.json',dict(receipts=rows,collected_per_phase=expected,
        all_requested_phases_executed=len(rows)==2,full_maestro_regression_passed=len(rows)==2 and all(r['returncode']==0 for r in rows),
        full_platform_regression=False,full_M1_complete=False,stable_increment17=False,accepted=False,merged=False))
    print(label,'terminal',code,flush=True)
raise SystemExit(0 if all(r['returncode']==0 for r in rows) else 1)
