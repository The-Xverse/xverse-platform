"""Retain an actual old-package red control, then exercise the successor package."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import shutil
import tempfile
import time

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
consumer=Path(tempfile.mkdtemp(prefix='maestro-affa17-dependent-consumer-'))
(consumer/'tests/thesis_lite').mkdir(parents=True)
for name in ['tests/__init__.py','tests/thesis_lite/__init__.py']:
    shutil.copyfile(ROOT/name,consumer/name)
shutil.copytree(ROOT/'tests/thesis_lite/maestro',consumer/'tests/thesis_lite/maestro',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
shutil.copytree(ROOT/'xdl',consumer/'xdl')
rows=[]
for name,python,tests,expected in [
    ('dependent-v2-focused','/tmp/maestro-lite-affa-dependent2-verify-20261018/bin/python',
        ['test_run_renewal.py','test_generation_dependents.py','test_generation_restart.py'],0),
]:
    private=tempfile.mkdtemp(prefix='maestro-affa17-'+name+'-')
    command=[python,'-I','-m','pytest',*[str(consumer/'tests/thesis_lite/maestro'/t) for t in tests],'-q','--basetemp',private]
    env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONDONTWRITEBYTECODE='1',MAESTRO_BOUNDARY_RECEIPTS=str(OUT/(name+'-harness')));env.pop('PYTHONPATH',None)
    began=time.monotonic()
    with (OUT/(name+'.log')).open('w') as log:
        result=subprocess.run(command,cwd=consumer,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    row=dict(consumer=str(consumer),command=command,returncode=result.returncode,expected_returncode=expected,original_private_basetemp=private,elapsed_seconds=time.monotonic()-began,
        log_sha256=hashlib.sha256((OUT/(name+'.log')).read_bytes()).hexdigest())
    (OUT/(name+'-receipt.json')).write_text(json.dumps(row,indent=2)+'\n')
    with (OUT/(name+'-public-capture.log')).open('w') as log:
        capture=subprocess.run([python,'-I',str(OUT/'capture-retained-teardown.py'),name,private],cwd=consumer,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=30)
    assert capture.returncode==0
    print(name,result.returncode,flush=True)
    if result.returncode!=expected:raise SystemExit(result.returncode or 1)
