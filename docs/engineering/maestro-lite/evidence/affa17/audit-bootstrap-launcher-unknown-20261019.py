"""Actual external owned waits cannot supply missing runtime identity/wait."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sys
import sysconfig
import zipfile

out=Path(sys.argv[1]).resolve(strict=True)
handle,exit_code=int(sys.argv[2]),int(sys.argv[3])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
frozen,running=read(out/'frozen-inputs.json'),read(out/'running.json')
root=Path(running['frozen_source_root'])
prior=read(out.parent/'bootstrap-launcher-20261019a/frozen-inputs.json')
assert all(sha(root/n)==h for n,h in frozen.items())
assert all(prior[n]==h for n,h in frozen.items() if n.startswith('src/'))
assert frozen['tests/thesis_lite/maestro/test_bootstrap_launch_unknown.py']
installed=Path(sysconfig.get_path('purelib'));packaged=[]
with zipfile.ZipFile(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl') as wheel:
    for n,h in frozen.items():
        if n.startswith('src/') and n.endswith(('.py','.c')):
            entry=n.removeprefix('src/')
            assert hashlib.sha256(wheel.read(entry)).hexdigest()==h==sha(installed/entry)
            packaged.append(entry)
assert len(packaged)==78
phases=[];roots=[];cases=[];seen=set()
for p in sorted(out.glob('*-receipt.json')):
    receipt=read(p)
    if 'cohort' not in receipt:continue
    label=p.name.removesuffix('-receipt.json');log=out/(label+'.log')
    assert receipt['returncode']==receipt['public_capture_returncode']==0 and sha(log)==receipt['log_sha256']
    assert re.search(r'3 passed',log.read_text().splitlines()[-1])
    phases.append(dict(phase=receipt['phase'],passed=3,failed=0,errors=0))
    assert read(out/(label+'-public-evidence-index.json'))==[]
    harness=out/(label+'-harness')
    for p in harness.glob('maestro-component-*.json'):
        row=read(p);identity=row['parent_path'],row['root_name']
        assert identity not in seen;seen.add(identity)
        assert row['root_removed'] and row['workers_reaped'] and not (Path(row['parent_path'])/row['root_name']).exists()
        roots.append(dict(path=str(p.relative_to(out)),sha256=sha(p)))
    for p in harness.glob('launcher-unknown-*.json'):
        row=read(p);facts=row['runtime_outcome'];wait=row['external_original_wait']
        assert facts['birth_attempted'] and not facts['registered']
        assert facts['supervisor_reaped'] is facts['registered_helpers_reaped'] is facts['unacknowledged_births'] is None
        assert not facts['cleanup_complete'] and not facts['ready_for_execution']
        assert row['runtime_wait_still_unknown'] and row['ordinary_disposal_rejected'] and row['external_descriptor_disposal']
        assert wait['si_pid']==row['external_original_pid'] and wait['si_code']==os.CLD_KILLED and wait['si_status']==signal.SIGKILL
        assert row['helpers_created']==row['workloads_created']==0 and not row['full_M1_complete']
        assert facts['process_returned'] is ('lost-popen-return' not in row['case'])
        cases.append(dict(phase=receipt['phase'],case=row['case'],path=str(p.relative_to(out)),sha256=sha(p)))
assert len(phases)==2 and len(roots)==len(cases)==6 and exit_code==0
assert read(out/'collection-receipt.json')['collected']==3
result=dict(original_exec_session=handle,original_exec_exit=exit_code,phases=phases,
    cases=cases,root_receipts=roots,packaged_sources=78,all_78_previous_production_sources_unchanged=True,
    actual_owned_supervisor_births=6,external_original_waits=6,runtime_original_waits=0,
    actual_helpers=0,actual_workloads=0,actual_M1_admissions=0,
    unknown_runtime_states_preserved=True,ordinary_disposal_rejected=True,
    auditor_sha256=sha(Path(__file__)),source_manifest_sha256=sha(out/'frozen-inputs.json'),
    full_M1_complete=False,whole_platform_regression=False,stable_increment17=False,accepted=False,merged=False)
with (out/'verification.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(phases=phases,external_original_waits=6,runtime_original_waits=0)))
