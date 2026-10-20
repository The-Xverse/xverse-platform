"""Add exact lazy-runtime endpoints while retaining every original open obligation."""
import ast
import hashlib
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
OUT=BASE/'lazy-dispatch-boundary-20261019d'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit=read(OUT/'verification.json');assert audit['component_scope_passed']
root=Path(read(OUT/'running.json')['frozen_source_root']);manifest=read(OUT/'frozen-inputs.json')
parent=BASE/'terminal-service-partial-traceability.json';trace=read(parent)
trace['revision']='ML3-AFFA17-2026-10-19-lazy-dispatch-partial'
trace['prior_component_trace']=dict(path=str(parent),sha256=sha(parent))
trace['evidence_snapshot']=dict(path=str(OUT/'verification.json'),sha256=sha(OUT/'verification.json'))

def endpoint(name):
    path,symbol=name.split('::');assert sha(root/path)==manifest[path]==sha(BASE.parents[4]/path)
    nodes=ast.parse((root/path).read_text()).body
    for part in symbol.split('.'):
        node=next(n for n in nodes if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==part)
        nodes=getattr(node,'body',[])
    return dict(endpoint=name,line=node.lineno,file_sha256=manifest[path],
                frozen_manifest='lazy-dispatch-boundary-20261019d/frozen-inputs.json')
code=[endpoint(n) for n in [
 'src/xverse/maestro/dispatcher.py::FiniteDispatcher.__init__',
 'src/xverse/maestro/dispatcher.py::FiniteDispatcher._generation',
 'src/xverse/maestro/dispatcher.py::FiniteDispatcher._statement',
 'src/xverse/maestro/dispatcher.py::FiniteDispatcher._effect',
 'src/xverse/maestro/dispatcher.py::FiniteDispatcher._end',
 'src/xverse/maestro/dispatcher.py::FiniteDispatcher._cleanup',
 'src/xverse/maestro/dispatcher.py::FiniteDispatcher.run',
 'src/xverse/maestro/dispatcher.py::validate_schedule_reply',
 'src/xverse/maestro/schedule_evidence.py::ScheduleJournal.admit_start_claim',
 'src/xverse/maestro/schedule_evidence.py::ScheduleJournal._generation',
 'src/xverse/maestro/schedule_evidence.py::ScheduleJournal._logical_source',
 'src/xverse/maestro/schedule_evidence.py::ScheduleJournal._handle',
 'src/xverse/maestro/schedule_evidence.py::ScheduleJournal._control']]
# Worker main defines its private sealed-init/commit branch; bind the whole module.
worker='src/xverse/maestro/persistence_worker.py'
assert sha(root/worker)==manifest[worker]
code.append(dict(endpoint=worker+'::main',file_sha256=manifest[worker],
                 frozen_manifest='lazy-dispatch-boundary-20261019d/frozen-inputs.json'))
tests=[endpoint('tests/thesis_lite/maestro/test_lazy_dispatcher.py::'+n.name)
       for n in ast.parse((root/'tests/thesis_lite/maestro/test_lazy_dispatcher.py').read_text()).body
       if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
links=['ML-SR-003','ML-SR-004','ML-SR-005','ML-SR-006','ML-SR-009','ML-SR-010','ML-SR-011',
       'ML-SR-015','ML-SR-016','ML-SR-019','ML-SR-020','ML-SR-021','ML-SR-023']
delta=dict(maturity='partial_component_evidence_only',code=code,tests=tests,
    verification='lazy-dispatch-boundary-20261019d/verification.json',full_requirement_closure=False,
    limitations=['failed broader c29/1 and b25/23+2 remain open',
                 'native cancellation before normal teardown still pending',
                 'final report/writer closure/independent closed-reader coverage still pending',
                 'full M1, source parents, nine runtime cases and independent full review remain open'])
for r in trace['requirements']:
    if r['id'] in links:r['component_deltas'].append(delta)
for e in code+tests:trace['reverse_endpoint_requirements'][e['endpoint']]=links
trace['latest_broader_regression']=dict(path='lazy-dispatch-20261019c/failure-verification.json',
    source_passed=29,source_failed=1,installed_wheel_executed=False,cause_established=False)
assert len(trace['requirements'])==trace['software_requirements_retained']==24
assert trace['source_parents_retained']==18 and trace['source_parent_semantics_validated'] is False
for k in ('full_M1_complete','stable_increment17','accepted','merged','U7_U8_complete','full_candidate_review_complete'):
    assert trace[k] is False
with (BASE/'lazy-dispatch-partial-traceability.json').open('x') as f:f.write(json.dumps(trace,indent=2)+'\n')
print(json.dumps(dict(new_endpoints=len(code)+len(tests),requirements_retained=24,source_parents_retained=18,full_requirement_closure=False)))
