"""Recheck exact inert preflight work products and preserved authorization gates."""
import hashlib
import json
from pathlib import Path

base=Path(__file__).resolve().parent
root=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
folder=base/'runtime-admission-20261019b'
frozen=read(folder/'frozen-inputs.json')
assert all(sha(root/n)==h for n,h in frozen.items())
prior=read(base/'composed-issuer-loss-20261019c/frozen-inputs.json')
assert all(prior[n]==h for n,h in frozen.items() if n.startswith('src/') and n in prior)
assert [n for n in frozen if n.startswith('src/') and n not in prior]==['src/xverse/maestro/runtime_admission.py']
inputs=read(root/'docs/engineering/maestro-lite/coverage-runtime-closure-inputs.json')
assert all(sha(Path(r['path']))==r['sha256'] for r in inputs['inputs'])
capa_path=base/'capa-20261019-runtime-admission/register.json'
capa=read(capa_path)
for key,item in capa['evidence'].items():
    path=root/item['path']
    if item['kind']=='file':digest=sha(path)
    else:
        text=path.read_text()
        digest=hashlib.sha256(text[text.index('\n'+item['start'])+1:text.index('\n'+item['end'])].encode()).hexdigest()
    assert digest==item['sha256'],key
trace_path=base/'runtime-admission-partial-traceability.json'
trace=read(trace_path)
assert len(trace['requirements'])==24 and all(not r['full_requirement_closure'] for r in trace['requirements'])
for row in trace['requirements']:
    for delta in row['component_deltas']:
        if delta.get('maturity')=='inert_joint_runtime_admission_binding_unit_verified':
            for endpoint in delta['code']+delta['tests']:
                path,name=endpoint['endpoint'].split('::')
                assert frozen[path]==endpoint['file_sha256']
                assert 'def '+name.split('.')[-1]+'(' in (root/path).read_text().splitlines()[endpoint['line']-1]
for name in ('parent_trace','evidence','original_fixture_failure','CAPA','CAPA_validation'):
    row=trace[name];assert sha(base/row['path'])==row['sha256']
assert trace['actual_runtime_contexts']==trace['actual_M1_admissions']==0
assert not trace['public_entry_implementation']['public_start']
assert 'runtime_admission' not in (root/'src/xverse/maestro/__init__.py').read_text()
result=dict(checker_sha256=sha(Path(__file__)),source_and_test_frozen_files_unchanged=len(frozen),
    original_draft_input_bindings_unchanged=len(inputs['inputs']),all_76_previous_production_sources_unchanged=True,
    capa_records=len(capa['records']),capa_evidence_bindings=len(capa['evidence']),partial_requirement_rows=24,
    trace_sha256=sha(trace_path),latest_capa_sha256=sha(capa_path),actual_M1_admissions=0,
    full_increment17_complete=False,accepted=False,merged=False)
with (base/'runtime-admission-work-products-check.json').open('x') as stream:
    json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(result))
