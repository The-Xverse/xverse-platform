"""Add verified fenced-normal endpoints without promoting any full requirement."""
import ast
import hashlib
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
OUT=BASE/'fenced-teardown-20261019a'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(OUT/'verification.json')['component_scope_passed']
root=Path(read(OUT/'running.json')['frozen_source_root']);manifest=read(OUT/'frozen-inputs.json')
parent=BASE/'lazy-dispatch-partial-traceability.json';trace=read(parent)
trace['revision']='ML3-AFFA17-2026-10-19-fenced-normal-teardown-partial'
trace['prior_component_trace']=dict(path=str(parent),sha256=sha(parent))
trace['evidence_snapshot']=dict(path=str(OUT/'verification.json'),sha256=sha(OUT/'verification.json'))
def endpoint(name):
    path,symbol=name.split('::');assert sha(root/path)==manifest[path]==sha(BASE.parents[4]/path)
    nodes=ast.parse((root/path).read_text()).body
    for part in symbol.split('.'):
        node=next(n for n in nodes if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==part);nodes=node.body
    return dict(endpoint=name,line=node.lineno,file_sha256=manifest[path],
                frozen_manifest='fenced-teardown-20261019a/frozen-inputs.json')
code=[endpoint(n) for n in [
 'src/xverse/maestro/teardown.py::ReverseTeardown._terminal_scope',
 'src/xverse/maestro/teardown.py::ReverseTeardown.run',
 'src/xverse/maestro/persistence.py::PersistenceClient.record_teardown',
 'src/xverse/maestro/persistence.py::PersistenceClient._rpc',
 'src/xverse/maestro/persistence_worker.py::serve',
 'src/xverse/maestro/teardown_evidence.py::TeardownJournal.record',
 'src/xverse/maestro/dispatcher.py::FiniteDispatcher._cleanup']]
tests=[endpoint('tests/thesis_lite/maestro/test_fenced_teardown.py::'+n.name)
       for n in ast.parse((root/'tests/thesis_lite/maestro/test_fenced_teardown.py').read_text()).body
       if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
tests.append(endpoint('tests/thesis_lite/maestro/test_lazy_dispatcher.py::test_actual_implicit_normal_teardown_occurs_after_original_native_cancel'))
links=['ML-SR-006','ML-SR-007','ML-SR-009','ML-SR-010','ML-SR-011','ML-SR-019','ML-SR-020','ML-SR-021']
delta=dict(maturity='partial_component_evidence_only',code=code,tests=tests,
    verification='fenced-teardown-20261019a/verification.json',full_requirement_closure=False,
    limitations=['full report/writer and authoritative closed-reader runtime composition remain pending',
                 'prior failed timing/paused scopes and full M1/runtime/global/candidate-review gates remain open'])
for r in trace['requirements']:
    if r['id'] in links:r['component_deltas'].append(delta)
for e in code+tests:trace['reverse_endpoint_requirements'][e['endpoint']]=links
assert len(trace['requirements'])==trace['software_requirements_retained']==24
assert trace['source_parents_retained']==18 and trace['source_parent_semantics_validated'] is False
for k in ('full_M1_complete','stable_increment17','accepted','merged','U7_U8_complete','full_candidate_review_complete'):
    assert trace[k] is False
with (BASE/'fenced-normal-teardown-partial-traceability.json').open('x') as f:f.write(json.dumps(trace,indent=2)+'\n')
print(json.dumps(dict(new_endpoints=len(code)+len(tests),requirements_retained=24,source_parents_retained=18,full_requirement_closure=False)))
