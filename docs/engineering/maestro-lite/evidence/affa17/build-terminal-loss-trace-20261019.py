"""Exact partial storage/root-loss delta; preserve the entire selected scope."""
import ast
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
name='terminal-loss-20261019a';v=read(BASE/name/'verification.json')
prior=BASE/'native-writer-stages-partial-traceability.json';trace=read(prior)
manifest=read(BASE/name/'frozen-inputs.json');old=read(BASE/'guard-delegation-20261019e/frozen-inputs.json')
assert all(manifest[p]==h for p,h in old.items() if p.startswith(('src/','xdl/')))
mapping={
 'ML-SR-013':['src/xverse/maestro/run_closure.py::RunClosure.close'],
 'ML-SR-018':['src/xverse/maestro/terminal_runtime.py::finish_run','src/xverse/maestro/runtime_verification.py::verify_runtime_closed'],
 'ML-SR-019':['src/xverse/maestro/persistence.py::PersistenceClient._fail','src/xverse/maestro/persistence.py::PersistenceClient.drain',
              'src/xverse/maestro/run_closure.py::RunClosure.close'],
 'ML-SR-020':['src/xverse/maestro/terminal_runtime.py::finish_run','src/xverse/maestro/persistence.py::PersistenceClient._rpc'],
 'ML-SR-021':['src/xverse/maestro/artifacts.py::CollectionSource._verify','src/xverse/maestro/public_blobs.py::write_public_bytes'],
 'ML-SR-023':['src/xverse/maestro/terminal_runtime.py::finish_run'],
 'ML-SR-024':['src/xverse/maestro/bootstrap.py::BootstrapSession.persistence'],
}
test_key='tests/thesis_lite/maestro/test_terminal_storage_root_loss.py::test_original_post_collection_loss_retains_unknown_ack_and_original_cleanup'
reverse=trace['reverse_endpoint_requirements'];endpoints={}
for key in sorted({k for keys in mapping.values() for k in keys}|{test_key}):
 path,name=key.split('::');file=ROOT/path;assert sha(file)==manifest[path]
 body=ast.parse(file.read_text()).body
 for part in name.split('.'):
  node=next(n for n in body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==part);body=node.body
 endpoints[key]=dict(endpoint=key,line=node.lineno,file_sha256=sha(file),
                     frozen_manifest='terminal-loss-20261019a/frozen-inputs.json')
 reverse[key]=sorted(set(reverse.get(key,[])+[rid for rid,keys in mapping.items() if key in keys or key==test_key]))
for row in trace['requirements']:
 if row['id'] in mapping:
  row['component_deltas'].append(dict(maturity='partial_post_collection_storage_and_root_loss',
   code=[endpoints[k] for k in mapping[row['id']]],tests=[endpoints[test_key]],
   verification='terminal-loss-20261019a/verification.json',phases=v['phases'],full_requirement_closure=False,
   limits=['Loss occurs after productive teardown, collection and terminal records',
          'Native terminal fence already exists; these controls do not prove the initial cancellation response during productive execution',
          'Original evidence path loss stays explicit; byte verification uses only the retained original directory identity',
          'No complete TR06, old/current-generation/controller composition, M1 or full regression claim']))
trace.update(revision='ML3-AFFA17-2026-10-19-original-storage-root-loss-partial',
 scope='Four actual post-collection storage/root loss controls; full selected increment17 remains incomplete',
 prior_component_trace=dict(path=str(prior),sha256=sha(prior)),
 evidence=dict(path='terminal-loss-20261019a/verification.json',sha256=sha(BASE/'terminal-loss-20261019a/verification.json')),
 terminal_loss_affected_scope_passed=v['affected_source_wheel_scope_passed'],
 full_selected_increment_scope_passed=False)
trace['additional_evidence'].append(dict(path='native-writer-stages-20261019c/verification.json',
 sha256=sha(BASE/'native-writer-stages-20261019c/verification.json')))
assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18
assert not any(r['full_requirement_closure'] for r in trace['requirements'])
with (BASE/'terminal-loss-partial-traceability.json').open('x') as f:json.dump(trace,f,indent=2);f.write('\n')
review=dict(scope='Separate limited read-only review of post-collection loss controls; not complete-candidate review',
 source_manifest_sha256=sha(BASE/'terminal-loss-20261019a/frozen-inputs.json'),production_src_xdl_unchanged=True,
 findings_before_implementation=[197],checks=[
 'Original coverage/collection/generation pinned before execution',
 'Fault only after successful original collection, productive cleanup and terminal records',
 'Original pidfd signals with WNOWAIT observation; no substituted signal/wait ownership',
 'Root renames confined to owned temporary fixtures; original pathname not restored or recreated',
 'Retained evidence identity and unchanged manifest/M3/event bytes independently checked',
 'Unknown terminal ACKs, last acknowledged open writer and independent closed-verifier rejection kept separate',
 'Cached original terminal outcome and original helper/C1/root waits with RPC replay forbidden',
 'No operational deadline, production mechanism, scientific protocol or acceptance change'],
 new_source_finding=None,limits=['No default export-environment invocation in this four-case scope',
 'The productive gate is already terminal-fenced before fault; no new cancellation-causality claim',
 'Old/current generations/controller sessions and loss during productive execution remain separate'],
 full_candidate_review_complete=False,accepted=False)
with (BASE/'terminal-loss-source-review-20261019.json').open('x') as f:json.dump(review,f,indent=2);f.write('\n')
print(json.dumps(dict(requirements=24,source_parents=18,code_endpoints=len(endpoints)-1,test_functions=1,
 production_changed=False,full_increment_complete=False)))
