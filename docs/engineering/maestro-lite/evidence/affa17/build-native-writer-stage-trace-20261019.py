"""Partial native failure delta; preserve all prior requirements and open gates."""
import ast
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
name='native-writer-stages-20261019c';v=read(BASE/name/'verification.json')
prior=BASE/'guard-delegation-partial-traceability.json';trace=read(prior)
manifest=read(BASE/name/'frozen-inputs.json');old=read(BASE/'guard-delegation-20261019e/frozen-inputs.json')
assert all(manifest[p]==h for p,h in old.items() if p.startswith(('src/','xdl/')))
ids=['ML-SR-013','ML-SR-018','ML-SR-023','ML-SR-024'];code=[];tests=[]
reverse=trace['reverse_endpoint_requirements']
def endpoint(path,name):
 file=ROOT/path;assert sha(file)==manifest[path];body=ast.parse(file.read_text()).body
 for part in name.split('.'):
  node=next(n for n in body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==part);body=node.body
 key=path+'::'+name
 row=dict(endpoint=key,line=node.lineno,file_sha256=sha(file),frozen_manifest='native-writer-stages-20261019c/frozen-inputs.json')
 (tests if path.startswith('tests/') else code).append(row);reverse[key]=sorted(set(reverse.get(key,[])+ids))
for path,names in (
 ('src/xverse/maestro/terminal_writer.py',['close_runtime_writer']),
 ('src/xverse/maestro/terminal_runtime.py',['WorkerTerminal.close','finish_run']),
 ('src/xverse/maestro/runtime_verification.py',['verify_runtime_closed']),
 ('src/xverse/maestro/run_closure.py',['RunClosure.close']),
 ('tests/thesis_lite/maestro/test_terminal_native_writer_failures.py',
  ['run_bootstrap_binary','test_actual_native_writer_failure_preserves_original_state_and_cleanup']),
 ('tests/thesis_lite/maestro/test_terminal_writer.py',
  ['test_actual_finalize_closed_reader_and_raw_manifest_hash','test_ineligible_actual_writer_flushes_then_aborts_incomplete',
   'test_finalize_error_with_positive_fresh_flush_permits_actual_abort','test_finalize_flush_error_open_state_is_not_abort_usability',
   'test_actual_manifest_publication_error_failed_writer_is_never_aborted',
   'test_eligibility_is_exact_boolean_before_writer_effects','test_expired_original_budget_has_no_finalize_or_abort_effect'])):
 for n in names:endpoint(path,n)
trace.update(revision='ML3-AFFA17-2026-10-19-native-writer-stage-partial',
 scope='Actual original worker failure mechanisms and helper cleanup; full selected increment17 remains incomplete',
 prior_component_trace=dict(path=str(prior),sha256=sha(prior)),
 evidence=dict(path=name+'/verification.json',sha256=sha(BASE/name/'verification.json')),
 native_writer_affected_scope_passed=v['full_source_wheel_scope_passed'],
 full_selected_increment_scope_passed=False)
for row in trace['requirements']:
 if row['id'] in ids:row['component_deltas'].append(dict(
  maturity='partial_original_native_writer_failure_composition',code=code,tests=tests,
  verification=name+'/verification.json',phases=v['phases'],full_requirement_closure=False,
  limits=['Faults injected at exact admitted call sites; not arbitrary physical disk faults',
         'W-02/W-03 and full TR03/TR06 remain open',
         'Cleanup observed after productive teardown; pre-release failures and generation/controller loss remain separate',
         'Guard-e source timeouts and full regression remain unresolved']))
trace['additional_evidence'] += [dict(path=p,sha256=sha(BASE/p)) for p in (
 'persistence-cost-20261019a/verification.json','native-writer-stages-20261019a/verification.json',
 'native-writer-stages-20261019b/verification.json')]
trace['stage_mechanism_dispositions']=dict(W01='one-shot/persistent fsync controls; usability separately observed',
 W02='unverified',W03='unverified',W04='owned post-close recovery-call exception',
 W05='owned post-close artifact-check exception',W06='owned os.replace publication exception',
 W07='prior exact normal finalize evidence retained, not newly executed in this six-fault matrix')
assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18
assert not any(r['full_requirement_closure'] for r in trace['requirements'])
with (BASE/'native-writer-stages-partial-traceability.json').open('x') as f:json.dump(trace,f,indent=2);f.write('\n')
review=dict(scope='Separate limited source review of native writer fault controls; not complete-candidate independent review',
 source_manifest_sha256=sha(BASE/name/'frozen-inputs.json'),
 production_src_xdl_unchanged_from_guard_e=True,
 findings_before_repairs=[191,192,193,194,195],
 checks=['Helper bytes sealed/hash-admitted before worker birth',
 'Injected os.fsync/recovery/artifact verification/os.replace call sites are scoped to original finalize',
 'No private stream read/replacement, writer reopen, deadline change or runtime fault selector',
 'Independent expected public states distinguish memory and durable manifest',
 'Fresh successful public flush required before abort; no abort of failed writer',
 'Original reports/external pins and helper cleanup retained; writer RPC replay forbidden',
 'Default receipt export optional and exercised by a separate original native invocation'],
 additional_source_finding=None,full_candidate_review_complete=False,accepted=False)
with (BASE/'native-writer-controls-source-review-20261019.json').open('x') as f:json.dump(review,f,indent=2);f.write('\n')
print(json.dumps(dict(requirements=24,source_parents=18,new_code_endpoints=len(code),new_test_endpoints=len(tests),
 production_changed=False,full_increment_complete=False)))
