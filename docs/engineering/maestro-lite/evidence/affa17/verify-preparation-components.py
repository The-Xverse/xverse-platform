"""Frozen affected component regression, sequential source/installed consumers."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import time

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
PYTHON='/tmp/maestro-lite-affa-verify-20261018/bin/python'
FILES=['test_admission.py','test_teardown.py','test_run_teardown.py','test_dispatcher.py','test_dispatch_observe.py','test_recovery.py','test_closure.py','test_boundary.py','test_affa_epoch.py','test_run_broker.py','test_storage_revalidate.py','test_bootstrap.py','test_persistence.py',
    'test_provider.py','test_outcomes.py','test_owner.py','test_affa_client.py','test_run_bootstrap.py',
    'test_run_bootstrap_values.py','test_affa_native.py','test_affa_config.py','test_affa_protocol.py']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda name,value:(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
env.pop('PYTHONPATH',None)
paths=[p for p in (ROOT/'src').rglob('*') if p.suffix in ('.py','.c')]
paths += [p for p in (ROOT/'tests/thesis_lite/maestro').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
before={str(p.relative_to(ROOT)):sha(p) for p in paths}
save('preparation-v1-frozen-inputs.json',before)
with tarfile.open(OUT/'preparation-v1-tested-inputs.tar.gz','w:gz') as archive:
    for p in paths:
        archive.add(p,arcname=str(p.relative_to(ROOT)))
consumer=Path(tempfile.mkdtemp(prefix='maestro-affa17-broker-installed-'))
(consumer/'tests/thesis_lite').mkdir(parents=True)
for name in ['tests/__init__.py','tests/thesis_lite/__init__.py']:
    shutil.copyfile(ROOT/name,consumer/name)
shutil.copytree(ROOT/'tests/thesis_lite/maestro',consumer/'tests/thesis_lite/maestro',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
shutil.copytree(ROOT/'xdl/profiles',consumer/'xdl/profiles')
code='''import importlib,hashlib,json,pathlib,sys
out={}
for name in json.loads(sys.argv[1]):
 p=pathlib.Path(importlib.import_module(name).__file__)
 out[name]={'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
print(json.dumps(out))'''
modules={'xverse.maestro'+('.'+p.stem if p.stem!='__init__' else ''):p for p in (ROOT/'src/xverse/maestro').glob('*.py')}
identity=json.loads(subprocess.check_output([PYTHON,'-I','-c',code,json.dumps(list(modules))],cwd=consumer,env=env,text=True))
for name,p in modules.items():
    assert identity[name]['sha256']==sha(p)
    assert identity[name]['file'].startswith('/tmp/maestro-lite-affa-verify-20261018/lib/')
resources={}
for p in (ROOT/'src/xverse/maestro/native').glob('*.c'):
    code="from importlib.resources import files;import json,hashlib;p=files('xverse.maestro').joinpath('native/"+p.name+"');print(json.dumps({'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))"
    row=json.loads(subprocess.check_output([PYTHON,'-I','-c',code],cwd=consumer,env=env,text=True))
    assert row['sha256']==sha(p) and row['file'].startswith('/tmp/maestro-lite-affa-verify-20261018/lib/')
    resources[p.name]=row
save('preparation-v1-installed-identity.json',dict(modules=identity,native_resources=resources))
receipts=[]
for name,isolated,cwd in [('preparation-v1-source',False,ROOT),('preparation-v1-wheel',True,consumer)]:
    environment=dict(env,MAESTRO_BOUNDARY_RECEIPTS=str(OUT/(name+'-harness')))
    if not isolated:
        environment['PYTHONPATH']=str(ROOT/'src')
    private_basetemp=Path(tempfile.mkdtemp(prefix='maestro-affa17-'+name+'-private-'))
    command=[PYTHON,*(['-I'] if isolated else []),'-m','pytest',*[str(cwd/'tests/thesis_lite/maestro'/n) for n in FILES],'-q','--basetemp',str(private_basetemp)]
    began=time.monotonic()
    with (OUT/(name+'.log')).open('w') as log:
        result=subprocess.run(command,cwd=cwd,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=420)
    assert all(sha(ROOT/n)==h for n,h in before.items())
    receipt=dict(command=command,cwd=str(cwd),returncode=result.returncode,timeout_seconds=420,
        elapsed_seconds=time.monotonic()-began,original_private_basetemp=str(private_basetemp),PYTHONPATH=environment.get('PYTHONPATH','unset'),
        log_sha256=sha(OUT/(name+'.log')),input_manifest_sha256=sha(OUT/'preparation-v1-frozen-inputs.json'))
    save(name+'-receipt.json',receipt)
    capture=[PYTHON,'-I',str(OUT/'capture-retained-teardown.py'),name,str(private_basetemp)]
    with (OUT/(name+'-public-capture.log')).open('w') as log:
        captured=subprocess.run(capture,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=30)
    receipt.update(public_capture_command=capture,public_capture_returncode=captured.returncode)
    save(name+'-receipt.json',receipt)
    receipts.append(receipt)
    save('preparation-v1-regression.json',dict(receipts=receipts,all_requested_phases_executed=len(receipts)==2,
        affected_regression_passed=len(receipts)==2 and all(r['returncode']==0 for r in receipts),
        installed_module_count=len(identity),native_resources=len(resources),
        wheel_sha256=sha(OUT/'preparation-v1-dist/xverse_xdl-0.4.0-py3-none-any.whl'),
        full_platform_regression=False,full_M1_complete=False,accepted=False,stable_increment17=False))
    if captured.returncode: raise SystemExit(captured.returncode)
    print(name,result.returncode,flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
assert len(receipts)==2
