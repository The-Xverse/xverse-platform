"""Verify original runtime coverage producers and affected frozen source/wheel assembly."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import time

CANDIDATE=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
PYTHON='/tmp/maestro-lite-affa-coverage-producers3-verify-20261019/bin/python'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda n,d:(OUT/n).write_text(json.dumps(d,indent=2)+'\n')
ROOT=Path(tempfile.mkdtemp(prefix='maestro-affa17-coverage-producers-v3-frozen-'))
for n in ['src','xdl']:
    shutil.copytree(CANDIDATE/n,ROOT/n,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
(ROOT/'tests/thesis_lite').mkdir(parents=True)
for n in ['tests/__init__.py','tests/thesis_lite/__init__.py','pyproject.toml','README.md','LICENSE']:
    shutil.copyfile(CANDIDATE/n,ROOT/n)
shutil.copytree(CANDIDATE/'tests/thesis_lite/maestro',ROOT/'tests/thesis_lite/maestro',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
paths=[p for p in ROOT.rglob('*') if p.is_file()]
frozen={str(p.relative_to(ROOT)):sha(p) for p in paths}
assert all(sha(CANDIDATE/n)==h for n,h in frozen.items())
save('coverage-producers-v3-frozen-inputs.json',frozen)
with tarfile.open(OUT/'coverage-producers-v3-tested-inputs.tar.gz','w:gz') as archive:
    for p in paths:archive.add(p,arcname=str(p.relative_to(ROOT)))
consumer=Path(tempfile.mkdtemp(prefix='maestro-affa17-coverage-producers-v3-consumer-'))
shutil.copytree(ROOT/'tests',consumer/'tests')
shutil.copytree(ROOT/'xdl',consumer/'xdl')
env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONPATH',None)
code='''from pathlib import Path
import importlib,json,hashlib
base=Path(importlib.import_module('xverse.maestro').__file__).parent
print(json.dumps({str(p.relative_to(base)):{'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in list(base.glob('*.py'))+list((base/'native').glob('*.c'))}))'''
identity=json.loads(subprocess.check_output([PYTHON,'-I','-c',code],cwd=consumer,env=env,text=True))
assert len(identity)==38
for n,r in identity.items():assert r['sha256']==sha(ROOT/'src/xverse/maestro'/n)
save('coverage-producers-v3-installed-identity.json',identity)
files=['test_coverage_producers.py','test_coverage.py','test_coverage_native.py','test_retained_inputs.py','test_broker_projection.py','test_run_teardown.py','test_shared_dispatcher.py','test_shared_closure.py','test_persistence.py','test_schedule_plan.py','test_schedule_worker.py','test_dispatcher.py','test_dispatch_observe.py']
rows=[]
save('coverage-producers-v3-running.json',dict(original_candidate=str(CANDIDATE),frozen_source_root=str(ROOT),consumer=str(consumer),verification_python=PYTHON,installed_identity_sha256=sha(OUT/'coverage-producers-v3-installed-identity.json')))
for phase,cwd,isolated in [('source',ROOT,False),('wheel',consumer,True)]:
    name='coverage-producers-v3-'+phase
    private=Path(tempfile.mkdtemp(prefix='maestro-affa17-'+name+'-private-'))
    environment=dict(env,MAESTRO_BOUNDARY_RECEIPTS=str(OUT/(name+'-harness')))
    if not isolated:environment['PYTHONPATH']=str(ROOT/'src')
    command=[PYTHON,*(['-I'] if isolated else []),'-m','pytest',*[str(cwd/'tests/thesis_lite/maestro'/n) for n in files],'-q','--basetemp',str(private)]
    began=time.monotonic()
    with (OUT/(name+'.log')).open('w') as log:
        result=subprocess.run(command,cwd=cwd,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=480)
    assert all(sha(ROOT/n)==h for n,h in frozen.items())
    assert all(sha(Path(r['file']))==r['sha256'] for r in identity.values())
    capture=[PYTHON,'-I',str(OUT/'capture-retained-teardown.py'),name,str(private)]
    with (OUT/(name+'-public-capture.log')).open('w') as log:
        observed=subprocess.run(capture,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=30)
    row=dict(command=command,cwd=str(cwd),returncode=result.returncode,elapsed_seconds=time.monotonic()-began,
             original_private_basetemp=str(private),public_capture_returncode=observed.returncode,
             frozen_source_root=str(ROOT),log_sha256=sha(OUT/(name+'.log')),input_manifest_sha256=sha(OUT/'coverage-producers-v3-frozen-inputs.json'))
    rows.append(row);save(name+'-receipt.json',row)
    save('coverage-producers-v3-regression.json',dict(receipts=rows,all_requested_phases_executed=len(rows)==2,
        affected_regression_passed=len(rows)==2 and all(r['returncode']==0 and r['public_capture_returncode']==0 for r in rows),
        candidate_matches_snapshot_at_this_observation=all((CANDIDATE/n).exists() and sha(CANDIDATE/n)==h for n,h in frozen.items()),
        installed_maestro_modules=34,native_resources=4,wheel_sha256=sha(OUT/'coverage-producers-v3-dist/xverse_xdl-0.4.0-py3-none-any.whl'),
        full_current_source_regression=False,verification_scope='original_runtime_coverage_producers_and_affected_composition',prospective_restart_tests_not_in_this_scope=[],full_M1_complete=False,stable_increment17=False,accepted=False,merged=False))
    print(name,result.returncode,flush=True)
    if result.returncode or observed.returncode:raise SystemExit(result.returncode or observed.returncode)
