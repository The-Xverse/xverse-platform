"""Preserve every exact-input diagnostic attempt; no new bound or product switch."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
PYTHON='/tmp/maestro-lite-affa-verify-20261018/bin/python'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=read(OUT/'preparation-v2-frozen-inputs.json')
assert all(sha(ROOT/n)==h for n,h in frozen.items())
identity=read(OUT/'preparation-v2-installed-identity.json')
assert all(sha(Path(r['file']))==r['sha256'] for r in identity.values())
receipt=read(OUT/'preparation-v1-wheel-receipt.json')
cwd=Path(receipt['cwd'])
node=str(cwd/'tests/thesis_lite/maestro/test_dispatcher.py')+'::test_full_five_phase_dispatch_records_actual_outcomes_and_dispositions'
rows=[]
for attempt in range(1,6):
    name='preparation-v2-nominal-'+str(attempt)
    harness=OUT/(name+'-harness')
    harness.mkdir()
    private=Path(tempfile.mkdtemp(prefix='maestro-affa17-teardown-diagnostic-'))
    env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',MAESTRO_BOUNDARY_RECEIPTS=str(harness))
    env.pop('PYTHONPATH',None)
    command=[PYTHON,'-I',str(OUT/'diagnose-teardown-timing.py'),str(OUT/(name+'-rpc.json')),node,str(private)]
    began=time.monotonic()
    with (OUT/(name+'.log')).open('w') as log:
        result=subprocess.run(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=30)
    assert all(sha(ROOT/n)==h for n,h in frozen.items())
    rows.append(dict(command=command,cwd=str(cwd),returncode=result.returncode,
        elapsed_seconds=time.monotonic()-began,explicit_private_basetemp=str(private),
        log_sha256=sha(OUT/(name+'.log')),rpc_sha256=sha(OUT/(name+'-rpc.json'))))
    (OUT/(name+'-receipt.json')).write_text(json.dumps(rows[-1],indent=2)+'\n')
    print(name,result.returncode,flush=True)
(OUT/'preparation-v2-nominal-cases.json').write_text(json.dumps(dict(attempts=rows,original_failed_run_retained=True,product_inputs_unchanged=True,operation_bounds_unchanged=True),indent=2)+'\n')
