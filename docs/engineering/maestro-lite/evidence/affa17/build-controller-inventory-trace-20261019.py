"""Partial terminal controller/future-universe evidence, with exact requirement mapping."""
import ast
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
ns='terminal-controller-inventory-20261019b';v=read(BASE/ns/'verification.json')
prior=BASE/'terminal-loss-partial-traceability.json';trace=read(prior)
manifest=read(BASE/ns/'frozen-inputs.json');old=read(BASE/'guard-delegation-20261019e/frozen-inputs.json')
assert all(manifest[p]==h for p,h in old.items() if p.startswith(('src/','xdl/')))
mapping={
 'ML-SR-013':['src/xverse/maestro/run_closure.py::RunClosure.close','src/xverse/maestro/controller.py::ControllerSession.retire'],
 'ML-SR-014':['src/xverse/maestro/controller.py::ControllerSession._start_access'],
 'ML-SR-017':['src/xverse/maestro/coverage.py::_Assessment.inactive','src/xverse/maestro/coverage.py::verify_closed',
              'src/xverse/maestro/runtime_verification.py::verify_runtime_closed','src/xverse/maestro/terminal_runtime.py::WorkerTerminal.publish'],
 'ML-SR-018':['src/xverse/maestro/terminal_runtime.py::WorkerTerminal.publish',
              'src/xverse/maestro/terminal_writer.py::close_runtime_writer','src/xverse/maestro/run_closure.py::RunClosure.close'],
 'ML-SR-023':['src/xverse/maestro/dispatcher.py::FiniteDispatcher.run','src/xverse/maestro/runtime_verification.py::verify_runtime_closed'],
 'ML-SR-024':['src/xverse/maestro/controller.py::admit_controller','src/xverse/maestro/bootstrap.py::BootstrapSession._spawn_role'],
}
tests=['tests/thesis_lite/maestro/test_terminal_controller_inventory.py::scheduled',
 'tests/thesis_lite/maestro/test_terminal_controller_inventory.py::test_original_terminal_report_keeps_retired_current_controllers_and_future_universe']
reverse=trace['reverse_endpoint_requirements'];endpoints={}
for key in sorted({k for keys in mapping.values() for k in keys}|set(tests)):
 path,name=key.split('::');file=ROOT/path;assert sha(file)==manifest[path];body=ast.parse(file.read_text()).body
 for part in name.split('.'):
  node=next(n for n in body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==part);body=node.body
 endpoints[key]=dict(endpoint=key,line=node.lineno,file_sha256=sha(file),frozen_manifest=ns+'/frozen-inputs.json')
 reverse[key]=sorted(set(reverse.get(key,[])+[rid for rid,keys in mapping.items() if key in keys or key in tests]))
for row in trace['requirements']:
 if row['id'] in mapping:row['component_deltas'].append(dict(
  maturity='partial_original_terminal_controller_inventory_and_unused_future_universe',
  code=[endpoints[k] for k in mapping[row['id']]],tests=[endpoints[k] for k in tests],
  verification=ns+'/verification.json',phases=v['phases'],offline_counterexamples=len(v['offline_counterexamples']),
  full_requirement_closure=False,limits=['Two declared generation2 contexts remain unused; no issued generation2 claim',
  'Successor admitted only after productive steps and remains unreconciled; no productive controller recovery',
  'Current one-start finite-plan/controller/view pins preserved',
  'Restart/evidence-lifetime API clarification pending; full17/M1/regression/independent review remain open']))
trace.update(revision='ML3-AFFA17-2026-10-19-terminal-controller-inventory-partial',
 scope='Retired/current terminal controller waits and complete unused future universe; full17 incomplete',
 prior_component_trace=dict(path=str(prior),sha256=sha(prior)),
 evidence=dict(path=ns+'/verification.json',sha256=sha(BASE/ns/'verification.json')),
 controller_inventory_affected_scope_passed=v['affected_source_wheel_scope_passed'],
 full_selected_increment_scope_passed=False)
trace['additional_evidence'].append(dict(path='terminal-controller-inventory-20261019a/verification.json',
 sha256=sha(BASE/'terminal-controller-inventory-20261019a/verification.json')))
assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18
assert not any(r['full_requirement_closure'] for r in trace['requirements'])
with (BASE/'terminal-controller-inventory-partial-traceability.json').open('x') as f:json.dump(trace,f,indent=2);f.write('\n')
review=dict(scope='Separate limited read-only review of terminal controller/future-universe controls; not complete-candidate independent review',
 source_manifest_sha256=sha(BASE/ns/'frozen-inputs.json'),production_src_xdl_unchanged=True,
 findings_before_implementation=[199,200],new_source_defect=None,
 checks=['Controller capacity reserved before original native admission',
 'Original generation contexts/collection/schedule fixed before execution; unused permits not consumed',
 'Original dispatcher/controller/facade pins retained; successor start access rejected without reconciliation',
 'Controller retirement/admission only after all productive steps, within original total/operation bounds',
 'Closed original report retains all future-generation rows and both helper slots/waits',
 'Copy-only mutations update indexed hashes; audit proves exactly selected artifact plus copied manifest differ',
 'Unchanged external original admission rejects universe/row deletion; original bytes remain immutable'],
 limits=['No issued generation2 or productive controller recovery',
 'No fresh default receipt-environment invocation in this two-case scope',
 'DRAFT restart/evidence-lifetime semantics need reconciliation before dependent code'],
 full_candidate_review_complete=False,accepted=False)
with (BASE/'terminal-controller-inventory-source-review-20261019.json').open('x') as f:json.dump(review,f,indent=2);f.write('\n')
print(json.dumps(dict(requirements=24,source_parents=18,code_endpoints=len(endpoints)-len(tests),test_endpoints=len(tests),
 offline_counterexamples=len(v['offline_counterexamples']),production_changed=False,full_increment_complete=False)))
