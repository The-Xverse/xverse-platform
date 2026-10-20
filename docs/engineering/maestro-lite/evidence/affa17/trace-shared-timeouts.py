"""Diagnostic parent-only RPC observations on unchanged shared-v2 exact inputs."""
from pathlib import Path
import json
import os
import subprocess
import tempfile

OUT=Path(__file__).resolve().parent
frozen=Path(json.loads((OUT/'shared-v2-running.json').read_text())['frozen_source_root'])
private=Path(tempfile.mkdtemp(prefix='maestro-affa17-shared-v2-rpc-diagnostic-'))
script=private/'observe.py'
script.write_text('''import json,time,sys
from pathlib import Path
import pytest
from xverse.maestro.persistence import PersistenceClient
class Observed:
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self,item):
        original=PersistenceClient._rpc
        rows=[]
        def observed(client,kind,body,deadline):
            began=time.monotonic()
            row=dict(kind=kind,control=body.get('kind'),phase=body.get('phase'),stage=body.get('stage'),remaining=deadline.monotonic_seconds-began)
            try:
                value=original(client,kind,body,deadline)
                row['returned']=True
                return value
            except Exception as error:
                row['error']=str(error)
                raise
            finally:
                row['elapsed']=time.monotonic()-began
                rows.append(row)
        PersistenceClient._rpc=observed
        yield
        PersistenceClient._rpc=original
        Path(sys.argv[1],item.name+'.json').write_text(json.dumps(rows,indent=2))
raise SystemExit(pytest.main(sys.argv[2:],plugins=[Observed()]))
''')
python='/tmp/maestro-lite-affa-shared2-verify-20261018/bin/python'
command=[python,str(script),str(private),
    str(frozen/'tests/thesis_lite/maestro/test_shared_dispatcher.py')+'::test_paused_shared_ticks_renew_both_original_leases_and_observe_health',
    str(frozen/'tests/thesis_lite/maestro/test_dispatcher.py')+'::test_implicit_horizon_stop_respects_dependencies_before_compiler_rank',
    '-q','--basetemp',str(private/'fixtures')]
env=dict(os.environ,PYTHONPATH=str(frozen/'src'),PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONDONTWRITEBYTECODE='1',MAESTRO_BOUNDARY_RECEIPTS=str(OUT/'shared-v2-rpc-diagnostic-harness'))
with (OUT/'shared-v2-rpc-diagnostic.log').open('w') as log:
    p=subprocess.run(command,cwd=frozen,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
rows=[]
for trace in private.glob('test_*.json'):
    facts=json.loads(trace.read_text())
    rows.append(dict(test=trace.stem,requests=len(facts),failures=[r for r in facts if 'error'in r],
        shortest_limits=sorted(facts,key=lambda r:r['remaining'])[:5],longest=sorted(facts,key=lambda r:r['elapsed'],reverse=True)[:5]))
result=dict(command=command,returncode=p.returncode,original_private_root=str(private),observations=rows,
    instrumentation='parent timing only; unchanged worker and original immutable deadlines',diagnostic_not_uninstrumented_verification=True)
(OUT/'shared-v2-rpc-diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
