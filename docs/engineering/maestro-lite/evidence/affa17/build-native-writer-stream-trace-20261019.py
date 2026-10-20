"""Bind exact bounded writer mechanisms without changing the original full scope."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re

base=Path(__file__).resolve().parent
candidate=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
def ref(p):return dict(path=str(p.relative_to(base)),sha256=sha(p))
out=base/'native-writer-stream-20261019c'
verified=read(out/'verification.json');frozen=read(out/'frozen-inputs.json')
root=Path(read(out/'running.json')['frozen_source_root'])
assert all(sha(root/n)==h==sha(candidate/n) for n,h in frozen.items())
parent=base/'active-control-deadlines-verified-scope-traceability.json';prior=read(parent)
def py(path,name):
    tree=ast.parse((root/path).read_text())
    node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
    return dict(endpoint=path+'::'+name,line=node.lineno,file_sha256=frozen[path],frozen_manifest='native-writer-stream-20261019c/frozen-inputs.json')
code=[py('src/xverse/maestro/terminal_writer.py','close_runtime_writer')]
tests=[py('tests/thesis_lite/maestro/test_native_writer_stream_faults.py',name)
    for name in ('run_bootstrap_binary','test_native_stream_fault_preserves_public_writer_and_original_cleanup')]
cpath='tests/thesis_lite/maestro/owned_writer_stream_fault.c';text=(root/cpath).read_text()
for name in ('write','close','matching','owned_writer_arm','owned_writer_probe'):
    match=re.search(r'^(?:static )?(?:ssize_t|int|void|unsigned) '+name+r'\(',text,re.M);assert match
    tests.append(dict(endpoint=cpath+'::'+name,line=text[:match.start()].count('\n')+1,
        file_sha256=frozen[cpath],frozen_manifest='native-writer-stream-20261019c/frozen-inputs.json'))
worker='tests/thesis_lite/maestro/owned_writer_stream_worker.py'
tests.append(dict(endpoint=worker+'::ROLE3/ROLE5',line=2,file_sha256=frozen[worker],frozen_manifest='native-writer-stream-20261019c/frozen-inputs.json'))
requirements=copy.deepcopy(prior['requirements']);reverse=copy.deepcopy(prior['reverse_endpoint_requirements'])
ids=['ML-SR-018','ML-SR-023','ML-SR-024']
for row in requirements:
    assert not row['full_requirement_closure']
    if row['id'] in ids:row['component_deltas'].append(dict(maturity='owned_native_writer_stage_mechanism_verified',
        code=code,tests=tests,evidence=ref(out/'verification.json'),full_requirement_closure=False,
        scope='Actual role3 loader and role5 isolation; preconditioned W02 and real successful close followed by injected EIO; no isolated W02/full-row/M1 claim'))
for endpoint in code+tests:
    reverse[endpoint['endpoint']]=sorted(set(reverse.get(endpoint['endpoint'],[]))|set(ids))
phases=[dict(phase=phase,passed=sum(r['passed'] for r in verified['phases'] if r['phase']==phase),
    failed=sum(r['failed'] for r in verified['phases'] if r['phase']==phase)) for phase in ('source','wheel')]
assert phases==[dict(phase='source',passed=4,failed=0),dict(phase='wheel',passed=4,failed=0)]
result=dict(schema_version=1,revision='ML3-AFFA17-2026-10-19-native-writer-stream-v1',
    scope='Conditional native writer failure mechanisms; full selected increment17 remains open',parent_trace=ref(parent),
    requirements=requirements,source_parent_register=prior['source_parent_register'],reverse_endpoint_requirements=reverse,
    evidence=ref(out/'verification.json'),original_failed_mechanism=ref(base/'native-writer-stream-20261019a/verification.json'),
    CAPA=ref(base/'capa-20261019-writer-stream/register.json'),CAPA_validation=ref(base/'capa-20261019-writer-stream/verification-recheck.json'),
    software_requirements_retained=24,source_parents_retained=18,scenario_pairs_retained=30,endpoint_obligations_retained=90,
    full_runtime_cases_retained=9,current_affected_counts=phases,production_sources_unchanged=True,
    original_root_receipts=8,original_wait_receipts=8,source_links=verified['source_links'],normal_closed_copies=2,
    W02=dict(preconditioned_native_write_mechanism=True,seed_fault_explicit=True,isolated_healthy_prefix='NOT_DEMONSTRATED',full_row_complete=False),
    W03=dict(actual_successful_close_then_EIO=True,fresh_flush_fails_no_abort=True,full_row_complete=False),
    finding_dispositions={'244':'owned_loader_and_conditional_stage_mechanisms_verified','246':'original_failed_mechanism_preserved_seeded_successor_verified_locally',
        '247':'pin_recorder_corrected_before_dispatch_verification','248':'bounded_same_session_review_only'},
    open_findings=[135,222],remaining_gates=prior['remaining_gates'],full_TR03_complete=False,full_TR06_complete=False,
    source_parent_semantics_validated=False,all_seven_phase3_tasks_complete=False,full_source_wheel_scope_passed=False,
    full_M1_complete=False,whole_platform_regression=False,full_candidate_review_complete=False,stable_increment17=False,
    accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False,scientific_result=False)
path=base/'native-writer-stream-partial-traceability.json'
with path.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(trace=ref(path),phases=phases,source_links=result['source_links'])))
