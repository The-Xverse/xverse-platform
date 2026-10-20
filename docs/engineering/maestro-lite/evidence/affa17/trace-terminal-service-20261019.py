"""Add exact component endpoints without closing inherited requirements/parents."""
import ast
import hashlib
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
OUT=BASE/'terminal-service-boundary-20261019d'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(OUT/'verification.json')['source_passed']==37
root=Path(read(OUT/'running.json')['frozen_source_root']);manifest=read(OUT/'frozen-inputs.json')
parent=BASE/'original-runtime-collection-partial-traceability.json';trace=read(parent)
trace['revision']='ML3-AFFA17-2026-10-19-terminal-service-partial'
trace['prior_component_trace']=dict(path=str(parent),sha256=sha(parent))
trace['evidence_snapshot']=dict(path=str(OUT/'verification.json'),sha256=sha(OUT/'verification.json'))
assert trace['software_requirements_retained']==24 and trace['source_parents_retained']==18

def endpoint(name):
    path,symbol=name.split('::');assert sha(root/path)==manifest[path]==sha(BASE.parents[4]/path)
    if path.endswith('.py'):
        nodes=ast.parse((root/path).read_text()).body;node=None
        for part in symbol.split('.'):
            node=next(n for n in nodes if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==part)
            nodes=getattr(node,'body',[])
        line=node.lineno
    else:
        rows=(root/path).read_text().splitlines();line=next(i for i,s in enumerate(rows,1) if ('int '+symbol+'(') in s)
    return dict(endpoint=name,line=line,file_sha256=manifest[path],frozen_manifest='terminal-service-boundary-20261019d/frozen-inputs.json')
code=[endpoint(n) for n in [
 'src/xverse/maestro/bootstrap.py::BootstrapSession._service_terminal',
 'src/xverse/maestro/bootstrap.py::BootstrapSession._rpc',
 'src/xverse/maestro/bootstrap.py::BootstrapSession._live',
 'src/xverse/maestro/run_broker.py::RunBroker.service_terminal',
 'src/xverse/maestro/collection_runtime.py::collect_outputs',
 'src/xverse/maestro/native/bootstrap.c::terminal_fence',
 'src/xverse/maestro/native/bootstrap.c::main']]
tests=[endpoint('tests/thesis_lite/maestro/test_terminal_service.py::'+n.name)
       for n in ast.parse((root/'tests/thesis_lite/maestro/test_terminal_service.py').read_text()).body
       if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
links=['ML-SR-009','ML-SR-010','ML-SR-011','ML-SR-019','ML-SR-020','ML-SR-021']
delta=dict(maturity='partial_component_evidence_only',code=code,tests=tests,
    verification='terminal-service-boundary-20261019d/verification.json',full_requirement_closure=False)
for r in trace['requirements']:
    if r['id'] in links:r['component_deltas'].append(delta)
for e in code+tests:
    trace['reverse_endpoint_requirements'][e['endpoint']]=links
trace['deferred_regression']=dict(finding=135,immediate_repair_deferred_by_author=True,release_gate_open=True,cause_established=False)
assert len(trace['requirements'])==24 and trace['source_parent_semantics_validated'] is False
for k in ('full_M1_complete','stable_increment17','accepted','merged','U7_U8_complete','full_candidate_review_complete'):
    assert trace[k] is False
with (BASE/'terminal-service-partial-traceability.json').open('x') as f:f.write(json.dumps(trace,indent=2)+'\n')
print(json.dumps(dict(new_endpoints=len(code)+len(tests),requirements_retained=24,source_parents_retained=18,full_requirement_closure=False)))
