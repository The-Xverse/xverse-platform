"""Bounded read-only diagnostic of one original failed terminal path."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
OUT=Path(__file__).resolve().parent
run=json.loads((OUT/'coverage-v5-full-running.json').read_text());root=Path(run['frozen_source_root'])
plugin=Path(tempfile.mkdtemp(prefix='maestro-terminal-diagnostic-'))/'probe.py'
plugin.write_text("""import json,time
from pathlib import Path
import xverse.maestro.persistence as p
from xverse.maestro.dispatcher import FiniteDispatcher
observed=[]
receive=p._receive
def traced(*a,**kw):
    result=receive(*a,**kw)
    if result['kind'] in ('error','ok'):observed.append(dict(at=time.monotonic(),reply=result))
    return result
p._receive=traced
send=FiniteDispatcher._send
def traced_send(self,kind,deadline,**values):
    begin=time.monotonic()
    try:return send(self,kind,deadline,**values)
    except Exception as error:
        observed.append(dict(kind=kind,remaining_at_entry=deadline.monotonic_seconds-begin,elapsed=time.monotonic()-begin,error=str(error),values=values));raise
FiniteDispatcher._send=traced_send
def pytest_sessionfinish(session,exitstatus):
    Path(__file__).with_suffix('.json').write_text(json.dumps(dict(exitstatus=exitstatus,observations=observed),indent=2))
""")
private=Path(tempfile.mkdtemp(prefix='maestro-terminal-diagnostic-private-'))
code="import importlib.util,pytest; s=importlib.util.spec_from_file_location('terminal_probe',"+repr(str(plugin))+"); p=importlib.util.module_from_spec(s); s.loader.exec_module(p); raise SystemExit(pytest.main("+repr([str(root/'tests/thesis_lite/maestro/test_dispatcher.py')+'::test_missed_tick_window_has_no_fabricated_step_or_probe_success','-q','--basetemp',str(private)])+",plugins=[p]))"
env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONPATH=str(root/'src'),PYTHONDONTWRITEBYTECODE='1',MAESTRO_BOUNDARY_RECEIPTS=str(OUT/'coverage-terminal-diagnostic-harness'))
command=[run['verification_python'],'-c',code]
with (OUT/'coverage-terminal-diagnostic.log').open('w') as log:
    result=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60)
data=json.loads(plugin.with_suffix('.json').read_text())
data.update(command=command,cwd=str(root),returncode=result.returncode,original_private_basetemp=str(private),original_frozen_source=True,diagnostic_only=True,deadlines_changed=False,does_not_explain_historical_failure_if_not_reproduced=True)
(OUT/'coverage-terminal-diagnostic.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(dict(returncode=result.returncode,observations=len(data['observations']))))
