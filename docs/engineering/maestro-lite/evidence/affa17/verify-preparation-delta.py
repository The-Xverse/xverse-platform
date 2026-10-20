"""Exact signed-zero delta over retained516/516 baseline; not full regression."""
from pathlib import Path
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import time

ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
PYTHON='/tmp/maestro-lite-affa-verify-20261018/bin/python'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
save=lambda n,d:(OUT/n).write_text(json.dumps(d,indent=2)+'\n')
previous=read(OUT/'preparation-v1-frozen-inputs.json')
current={n:sha(ROOT/n) for n in previous}
changed=[n for n,h in current.items() if h!=previous[n]]
assert sorted(changed)==['src/xverse/maestro/admission.py','tests/thesis_lite/maestro/test_admission.py']
save('preparation-v2-frozen-inputs.json',current)
with tarfile.open(OUT/'preparation-v2-tested-inputs.tar.gz','w:gz') as archive:
    for n in current:archive.add(ROOT/n,arcname=n)
consumer=Path(tempfile.mkdtemp(prefix='maestro-affa17-preparation-v2-consumer-'))
(consumer/'tests/thesis_lite').mkdir(parents=True)
for n in ['tests/__init__.py','tests/thesis_lite/__init__.py']:shutil.copyfile(ROOT/n,consumer/n)
shutil.copytree(ROOT/'tests/thesis_lite/maestro',consumer/'tests/thesis_lite/maestro',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
shutil.copytree(ROOT/'xdl/profiles',consumer/'xdl/profiles')
env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1');env.pop('PYTHONPATH',None)
code='''from pathlib import Path
import importlib,json,hashlib
base=Path(importlib.import_module('xverse.maestro').__file__).parent
rows={str(p.relative_to(base)):{'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in list(base.glob('*.py'))+list((base/'native').glob('*.c'))}
print(json.dumps(rows))'''
identity=json.loads(subprocess.check_output([PYTHON,'-I','-c',code],cwd=consumer,env=env,text=True))
assert len(identity)==31
for n,r in identity.items():
    assert r['sha256']==sha(ROOT/'src/xverse/maestro'/n)
    assert r['file'].startswith('/tmp/maestro-lite-affa-verify-20261018/lib/')
save('preparation-v2-installed-identity.json',identity)
rows=[]
for label,cwd,isolated in [('source',ROOT,False),('wheel',consumer,True)]:
    name='preparation-v2-'+label
    private=Path(tempfile.mkdtemp(prefix='maestro-affa17-'+name+'-private-'))
    environment=dict(env,MAESTRO_BOUNDARY_RECEIPTS=str(OUT/(name+'-harness')))
    if not isolated:environment['PYTHONPATH']=str(ROOT/'src')
    command=[PYTHON,*(['-I'] if isolated else []),'-m','pytest',str(cwd/'tests/thesis_lite/maestro/test_admission.py'),'-q','--basetemp',str(private)]
    began=time.monotonic()
    with (OUT/(name+'.log')).open('w') as log:
        result=subprocess.run(command,cwd=cwd,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    assert all(sha(ROOT/n)==h for n,h in current.items())
    row=dict(command=command,cwd=str(cwd),returncode=result.returncode,
             elapsed_seconds=time.monotonic()-began,original_private_basetemp=str(private),
             log_sha256=sha(OUT/(name+'.log')),input_manifest_sha256=sha(OUT/'preparation-v2-frozen-inputs.json'))
    rows.append(row);save(name+'-receipt.json',row)
    print(name,result.returncode,flush=True)
    if result.returncode:raise SystemExit(result.returncode)
result=dict(parent_baseline='preparation-component-verification.json',parent_manifest_sha256=sha(OUT/'preparation-v1-frozen-inputs.json'),
            changed_inputs=changed,receipts=rows,installed_maestro_modules=27,native_resources=4,
            wheel_sha256=sha(OUT/'preparation-v2-dist/xverse_xdl-0.4.0-py3-none-any.whl'),
            affected_delta_passed=True,full_current_source_regression=False,full_M1_complete=False,
            stable_increment17=False,accepted=False,merged=False)
save('preparation-v2-delta-verification.json',result)
