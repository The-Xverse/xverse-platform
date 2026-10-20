"""Exact partial delta for native guard delegation; all original gates retained."""
import ast
import hashlib
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
prior=BASE/'terminal-scope-offline-partial-traceability.json';trace=read(prior)
name='guard-delegation-20261019e';v=read(BASE/name/'verification.json');manifest=read(BASE/name/'frozen-inputs.json')
trace.update(revision='ML3-AFFA17-2026-10-19-native-guard-delegation-partial',
 scope='Remove duplicate native delegation probe while preserving final live guard and legacy behavior; partial full17',
 prior_component_trace=dict(path=str(prior),sha256=sha(prior)))
ids=['ML-SR-007','ML-SR-008','ML-SR-009','ML-SR-012','ML-SR-016','ML-SR-023']
code=[];tests=[];reverse={}
def endpoint(path,name):
 file=ROOT/path;assert sha(file)==manifest[path]
 body=ast.parse(file.read_text()).body
 for part in name.split('.'):
  node=next(n for n in body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==part);body=node.body
 key=path+'::'+name
 row=dict(endpoint=key,line=node.lineno,file_sha256=sha(file),frozen_manifest='guard-delegation-20261019e/frozen-inputs.json')
 (tests if path.startswith('tests/') else code).append(row);reverse[key]=ids
for path,names in (
 ('src/xverse/maestro/providers.py',['DependencyGuard._validate','DependencyGuard.check','ProcessReadiness.start','ProcessReadiness._check_prerequisites']),
 ('src/xverse/maestro/owner.py',['ReleaseOwner.release']),
 ('src/xverse/maestro/run_broker.py',['RunBroker.release']),
 ('tests/thesis_lite/maestro/test_dependency_delegation.py',['test_native_delegation_keeps_final_live_guard_without_duplicate_owner_probe']),
 ('tests/thesis_lite/maestro/test_provider.py',['test_real_current_generation_probe_precedes_dependent_release','test_failed_prerequisite_cannot_release_dependent']),
 ('tests/thesis_lite/maestro/test_run_broker.py',['test_dependent_direct_release_requires_original_active_guard'])):
 for n in names:endpoint(path,n)
for row in trace['requirements']:
 row['component_deltas']=[]
 if row['id'] in ids:row['component_deltas']=[dict(maturity='partial_native_guard_delegation_verified_scope',
  code=code,tests=tests,verification=name+'/verification.json',phases=v['phases'],full_requirement_closure=False)]
trace['reverse_endpoint_requirements']=reverse
trace['evidence']=dict(path=name+'/verification.json',sha256=sha(BASE/name/'verification.json'))
trace['additional_evidence']=[dict(path=n,sha256=sha(BASE/n)) for n in (
 'guard-delegation-red-20261019a/verification.json','guard-delegation-red-20261019b/verification.json',
 'guard-delegation-red-20261019c/verification.json','guard-delegation-target-20261019d/verification.json',
 'guard-delegation-source-review-20261019.json','current-start-budget-analysis-20261019.json',
 'offline-boundary-20261019d/verification.json')]
trace['full_source_wheel_scope_passed']=v['full_source_wheel_scope_passed']
assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18
assert not any(r['full_requirement_closure'] for r in trace['requirements'])
with (BASE/'guard-delegation-partial-traceability.json').open('x') as f:json.dump(trace,f,indent=2);f.write('\n')
print(json.dumps(dict(requirements=24,source_parents=18,code_endpoints=len(code),test_functions=len(tests),full_increment_complete=False)))
