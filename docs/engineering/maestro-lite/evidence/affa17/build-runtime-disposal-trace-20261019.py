"""Bind local disposal verification without closing inherited full requirements."""
import ast
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
root = base.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
parent_path = base/'runtime-issuer-loss-partial-traceability.json'
parent = read(parent_path)
out = base/'runtime-disposal-20261019c'
manifest = read(out/'frozen-inputs.json')
assert all(sha(root/n)==h for n,h in manifest.items())
verification = read(out/'verification.json')
red = read(base/'runtime-disposal-20261019a/verification.json')
assert verification['counts']=={p:dict(passed=157,failed=0,errors=0) for p in ('source','wheel')}
assert len(verification['phases'])==30 and len(verification['disposal_cases'])==8
assert sum(r['product_disposed'] for r in verification['disposal_cases'])==6
assert red['counts']=={p:dict(passed=0,failed=3,errors=0) for p in ('source','wheel')}
folder = base/'capa-20261019-runtime-disposal'
capa,check,preservation = [read(folder/n) for n in ('register.json','verification-recheck.json','parent-preservation.json')]
assert check['register_sha256']==preservation['register_sha256']==sha(folder/'register.json')
assert preservation['parent_preserved'] and preservation['parent_evidence_bindings_checked']==198
assert len(capa['records'])==39

endpoints = {
    'storage':'src/xverse/maestro/persistence.py::PersistenceClient.dispose',
    'admit':'src/xverse/maestro/run_broker.py::RunBroker.admit',
    'broker':'src/xverse/maestro/run_broker.py::RunBroker.dispose',
    'entry':'src/xverse/maestro/runtime_entry.py::_OriginalRuntimeRun.dispose',
    'launcher':'src/xverse/maestro/bootstrap_launcher.py::OriginalBootstrapLauncher.dispose',
    'test':'tests/thesis_lite/maestro/test_runtime_disposal.py::test_original_runtime_disposal_preserves_wait_facts_and_reused_descriptor',
}
bindings = {}
for key,endpoint in endpoints.items():
    file,name = endpoint.split('::')
    scope = ast.parse((root/file).read_text())
    for part in name.split('.'):
        scope = next(n for n in scope.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==part)
    assert sha(root/file)==manifest[file]
    bindings[key] = dict(endpoint=endpoint,line=scope.lineno,file_sha256=manifest[file],
        frozen_manifest='runtime-disposal-20261019c/frozen-inputs.json')
allocation = {
    'ML-SR-011':['storage','broker','entry'],
    'ML-SR-012':['admit','storage','broker','entry'],
    'ML-SR-013':['storage','broker','launcher'],
    'ML-SR-019':['storage','broker','entry'],
    'ML-SR-020':['storage','entry'],
    'ML-SR-022':['storage','broker'],
    'ML-SR-023':[],
}
evidence = [dict(path=f'runtime-disposal-20261019{s}/verification.json',
    sha256=sha(base/f'runtime-disposal-20261019{s}/verification.json')) for s in 'ac']
requirements,reverse = [],{}
for old in parent['requirements']:
    row = dict(id=old['id'],feature_parents=old['feature_parents'],inherited_status=old['inherited_status'],
        full_requirement_closure=False,prior_component_dispositions='inherit exact parent_trace; historical claims remain revision-bound',component_deltas=[])
    if old['id'] in allocation:
        keys = allocation[old['id']]
        row['component_deltas'].append(dict(maturity='partial_original_wait_and_single_use_local_disposal',
            scope='Local disposal after original helper waits,unchanged earlier failure facts,repeated broker/entry disposal and ambiguous close-error retention. No full teardown/normal-evidence/runtime-case claim.',
            code=[bindings[k] for k in keys],tests=[bindings['test']],evidence=evidence,full_requirement_closure=False))
        for key in [*keys,'test']:
            reverse.setdefault(bindings[key]['endpoint'],[]).append(old['id'])
    requirements.append(row)
assert len(requirements)==24 and len(reverse)==6
inputs = read(root/'docs/engineering/maestro-lite/coverage-runtime-closure-inputs.json')
assert len(inputs['inputs'])==8 and all(sha(Path(i['path']))==i['sha256'] for i in inputs['inputs'])
result = dict(schema_version=1,revision='ML3-AFFA17-2026-10-19-runtime-disposal-v1',
    parent_trace=dict(path=parent_path.name,sha256=sha(parent_path)),requirements=requirements,
    source_parent_register=parent['source_parent_register'],reverse_endpoint_requirements=reverse,
    evidence=evidence,ADR=dict(path='docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0010.md',
        sha256=sha(root/'docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0010.md')),
    CAPA=dict(path=str((folder/'register.json').relative_to(base)),sha256=sha(folder/'register.json')),
    CAPA_validation=dict(path=str((folder/'verification-recheck.json').relative_to(base)),sha256=sha(folder/'verification-recheck.json')),
    CAPA_parent_preservation=dict(path=str((folder/'parent-preservation.json').relative_to(base)),sha256=sha(folder/'parent-preservation.json')),
    selected_affected_counts=verification['counts'],selected_affected_scope_passed=True,
    new_controls_passed_per_phase=4,original_failures_per_phase=3,
    successful_product_disposal_cases=6,intentionally_unresolved_close_error_cases=2,
    packaged_python_c_files=81,changed_packaged_sources=verification['changed_packaged_sources'],
    other_packaged_sources_unchanged=79,current_recorded_roots_absent=len(verification['root_receipts']),
    original_red_recorded_roots_absent=len(red['root_receipts']),current_source_links=verification['source_links'],
    current_source_projection_gaps=verification['source_projection_gaps'],
    source_parents_retained=18,scenario_pairs_retained=30,endpoint_obligations_retained=90,full_runtime_cases_retained=9,
    open_findings=[135,222,286,287,318,324,330,331,332,337,338,344,345],
    authority_limits=dict(actual_M1_admissions=0,full_runtime_cases_complete=False,full_increment17_complete=False,
        full_maestro_regression_passed=False,whole_platform_regression=False,stable_increment17=False,
        source_parent_semantics_validated=False,independent_complete_review=False,CAPA_effectiveness_demonstrated=False,
        accepted=False,merged=False,scientific_result=False))
with (base/'runtime-disposal-partial-traceability.json').open('x') as stream:
    json.dump(result,stream,indent=2)
    stream.write('\n')
print(json.dumps(dict(requirements=len(requirements),endpoints=len(reverse),links=sum(map(len,reverse.values())),
    source_parents=18,source_checks=157,wheel_checks=157,CAPA_records=39)))
