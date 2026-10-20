"""Owned diagnostic syscall durations; private raw traces stay outside repository."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
PYTHON='/tmp/maestro-lite-affa-verify-20261018/bin/python'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=read(OUT/'teardown-v2-frozen-inputs.json')
assert all(sha(ROOT/n)==h for n,h in frozen.items())
cwd=Path(read(OUT/'teardown-v2-wheel-receipt.json')['cwd'])
node=str(cwd/'tests/thesis_lite/maestro/test_dispatcher.py')+'::test_full_five_phase_dispatch_records_actual_outcomes_and_dispositions'
rows=[]
for attempt in range(1,4):
    name='teardown-v2-syscall-'+str(attempt)
    harness=OUT/(name+'-harness');harness.mkdir()
    private=Path(tempfile.mkdtemp(prefix='maestro-affa17-private-syscall-'))
    raw=private/'syscalls.log'
    env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',MAESTRO_BOUNDARY_RECEIPTS=str(harness));env.pop('PYTHONPATH',None)
    command=['strace','-f','-ttt','-T','-e','trace=fsync,fdatasync,poll,ppoll,pselect6,waitid','-o',str(raw),PYTHON,'-I',str(OUT/'diagnose-teardown-timing.py'),str(OUT/(name+'-rpc.json')),node,str(private/'pytest')]
    began=time.monotonic()
    with (OUT/(name+'.log')).open('w') as log:
        result=subprocess.run(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=30)
    assert all(sha(ROOT/n)==h for n,h in frozen.items())
    durations={}
    for line in raw.read_text().splitlines():
        found=re.search(r' (fsync|fdatasync|poll|ppoll|pselect6|waitid)\(.*<([0-9.]+)>$',line)
        if found:durations.setdefault(found[1],[]).append(float(found[2]))
    summaries={k:dict(count=len(v),maximum_seconds=max(v),total_seconds=sum(v),over_20ms=sum(t>0.02 for t in v)) for k,v in durations.items()}
    rows.append(dict(command=command,cwd=str(cwd),returncode=result.returncode,
        elapsed_seconds=time.monotonic()-began,explicit_private_directory=str(private),
        private_trace_sha256=sha(raw),private_trace_not_committed=True,syscall_durations=summaries,
        diagnostic_instrumentation_can_affect_timing=True,
        log_sha256=sha(OUT/(name+'.log')),rpc_sha256=sha(OUT/(name+'-rpc.json'))))
    (OUT/(name+'-receipt.json')).write_text(json.dumps(rows[-1],indent=2)+'\n')
    print(name,result.returncode,json.dumps(summaries),flush=True)
(OUT/'teardown-v2-syscall-diagnostics.json').write_text(json.dumps(dict(attempts=rows,original_failed_run_retained=True,product_inputs_unchanged=True,operation_bounds_unchanged=True),indent=2)+'\n')
