"""Additive exact-snapshot partial trace; all original requirement gates retained."""
import ast
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
prior=BASE/'terminal-nonopen-helper-partial-traceability.json'
trace=read(prior)
trace['revision']='ML3-AFFA17-2026-10-19-scope-offline-partial'
trace['scope']='Original scoped terminal assessment, primary-error retention and inert offline codec boundary; partial full17'
trace['prior_component_trace']=dict(path=str(prior),sha256=sha(prior))
namespace='offline-boundary-20261019d'
manifest=read(BASE/namespace/'frozen-inputs.json')
verified=read(BASE/namespace/'verification.json')
code=[];tests=[];reverse={}

def endpoint(path,name,requirements):
    source=ROOT/path
    assert sha(source)==manifest[path]
    body=ast.parse(source.read_text()).body
    for part in name.split('.'):
        node=next(n for n in body if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==part)
        body=node.body
    key=path+'::'+name
    row=dict(endpoint=key,line=node.lineno,file_sha256=sha(source),frozen_manifest=namespace+'/frozen-inputs.json')
    reverse[key]=requirements
    (tests if path.startswith('tests/') else code).append((requirements,row))

scope=['ML-SR-015','ML-SR-016','ML-SR-017','ML-SR-018','ML-SR-023']
offline=['ML-SR-017','ML-SR-018','ML-SR-020','ML-SR-021','ML-SR-022','ML-SR-023']
errors=['ML-SR-009','ML-SR-013','ML-SR-019','ML-SR-020','ML-SR-023']
for name in ('RuntimeEvidenceScope.validate','runtime_admission_digest'):
    endpoint('src/xverse/maestro/evidence_scope.py',name,scope)
for name in ('_terminal_annotation','_payload','_Assessment.terminal_intent','_Assessment.health_window','_Assessment.input_digests','_assessment_bounds','assess_preclosure','verify_closed'):
    endpoint('src/xverse/maestro/coverage.py',name,scope)
endpoint('src/xverse/maestro/terminal_runtime.py','WorkerTerminal.publish',scope)
endpoint('src/xverse/maestro/dispatcher.py','FiniteDispatcher.run',errors)
for name in ('decode_broker_data','decode_context','starts_fenced','output_available','validate_item','document'):
    endpoint('src/xverse/maestro/collection_evidence.py',name,offline)
endpoint('src/xverse/maestro/public_blobs.py','decode_broker_data',offline)
endpoint('src/xverse/maestro/collection_runtime.py','decode_context',offline)
endpoint('src/xverse/maestro/runtime_verification.py','verify_runtime_closed',offline)
for name in ('test_original_runtime_scope_admits_terminal_facts_without_late_productive_credit','test_original_joint_scope_does_not_admit_late_readiness','test_terminal_records_beyond_original_generation_minus_drain_stay_invalid','test_substituted_scope_is_rejected_before_any_evidence_read','test_late_productive_payload_remains_outside_original_active_interval','test_producer_name_cannot_turn_late_start_intent_into_teardown_proof'):
    endpoint('tests/thesis_lite/maestro/test_evidence_scope.py',name,scope)
endpoint('tests/thesis_lite/maestro/test_dispatch_diagnostics.py','test_actual_primary_helper_timeout_survives_secondary_cleanup_ack_loss',errors)
for name in ('test_closed_verification_in_fresh_process_has_no_runtime_imports','test_runtime_decoder_keeps_original_exception_identity'):
    endpoint('tests/thesis_lite/maestro/test_offline_boundary.py',name,offline)
for row in trace['requirements']:
    row['component_deltas']=[]
    c=[r for ids,r in code if row['id'] in ids];t=[r for ids,r in tests if row['id'] in ids]
    if c:
        row['component_deltas'].append(dict(maturity='partial_exact_scope_not_full_requirement_closure',code=c,tests=t,
            verification=namespace+'/verification.json',phases=verified['phases'],full_requirement_closure=False))
trace['reverse_endpoint_requirements']=reverse
trace['evidence']=dict(path=namespace+'/verification.json',sha256=sha(BASE/namespace/'verification.json'))
trace['additional_evidence']=[dict(path=n,sha256=sha(BASE/n)) for n in (
    'terminal-scope-20261019a/verification.json','terminal-primary-red-20261019a/verification.json',
    'terminal-primary-20261019b/verification.json','offline-boundary-red-20261019c/verification.json',
    'offline-codec-extraction-20261019.json')]
trace['full_source_wheel_scope_passed']=verified['full_source_wheel_scope_passed']
assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18
assert not any(r['full_requirement_closure'] for r in trace['requirements'])
assert not any(r['full_parent_closure'] for r in trace['source_parent_register']['requirements'])
with (BASE/'terminal-scope-offline-partial-traceability.json').open('x') as stream:
    json.dump(trace,stream,indent=2);stream.write('\n')
print(json.dumps(dict(requirements=24,source_parents=18,code_endpoints=len(code),test_functions=len(tests),full_increment_complete=False)))
