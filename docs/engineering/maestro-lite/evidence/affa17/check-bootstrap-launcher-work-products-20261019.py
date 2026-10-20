"""Check current selected source/tests/trace/CAPA and unchanged full-scope gates."""
import ast
import hashlib
import json
from pathlib import Path

base=Path(__file__).resolve().parent;root=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
manifests={n:read(base/n/'frozen-inputs.json') for n in ('bootstrap-launcher-20261019a','bootstrap-launcher-unknown-20261019a')}
for frozen in manifests.values():assert all(sha(root/n)==h for n,h in frozen.items())
prior=read(base/'runtime-admission-20261019b/frozen-inputs.json')
latest=manifests['bootstrap-launcher-unknown-20261019a']
assert all(prior[n]==h for n,h in latest.items() if n.startswith('src/') and n in prior)
assert [n for n in latest if n.startswith('src/') and n not in prior]==['src/xverse/maestro/bootstrap_launcher.py']
inputs=read(root/'docs/engineering/maestro-lite/coverage-runtime-closure-inputs.json')
assert all(sha(Path(r['path']))==r['sha256'] for r in inputs['inputs'])
capa_path=base/'capa-20261019-bootstrap-launcher/register.json';capa=read(capa_path)
checked=read(capa_path.parent/'verification-recheck.json')
assert sha(capa_path)==checked['register_sha256'] and checked['records_validated']==13 and checked['evidence_bindings_verified']==64
for key,item in capa['evidence'].items():
    path=root/item['path']
    if item['kind']=='file':digest=sha(path)
    else:
        text=path.read_text();digest=hashlib.sha256(text[text.index('\n'+item['start'])+1:text.index('\n'+item['end'])].encode()).hexdigest()
    assert digest==item['sha256'],key
assert all(capa['action_plans'][r['capa_id']]['effectiveness']['status']=='NOT_DEMONSTRATED' for r in capa['records'])
assert {r['capa_id'] for r in capa['records'] if r['state']=='UNRESOLVED'}=={'ML-CAPA-135','ML-CAPA-222'}
trace_path=base/'bootstrap-launcher-partial-traceability.json';trace=read(trace_path)
assert len(trace['requirements'])==24 and all(not r['full_requirement_closure'] for r in trace['requirements'])
endpoints=0
for row in trace['requirements']:
    for delta in row['component_deltas']:
        if delta.get('maturity')!='original_internal_bootstrap_startup_owned_verified':continue
        for endpoint in delta['code']+delta['tests']:
            path,name=endpoint['endpoint'].split('::');manifest=read(base/endpoint['frozen_manifest'])
            assert manifest[path]==endpoint['file_sha256']==sha(root/path)
            tree=ast.parse((root/path).read_text());scope=tree;parts=name.split('.')
            if len(parts)==2:scope=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==parts[0])
            node=next(n for n in scope.body if isinstance(n,ast.FunctionDef) and n.name==parts[-1])
            assert node.lineno==endpoint['line']
            assert row['id'] in trace['reverse_endpoint_requirements'][endpoint['endpoint']]
            endpoints+=1
for name in ('parent_trace','evidence','unknown_evidence','original_collector_failure','CAPA','CAPA_validation'):
    ref=trace[name];assert sha(base/ref['path'])==ref['sha256']
assert sha(root/trace['ADR']['path'])==trace['ADR']['sha256']
verified=read(base/'bootstrap-launcher-20261019a/verification-v2.json')
unknown=read(base/'bootstrap-launcher-unknown-20261019a/verification.json')
assert verified['counts']=={p:dict(passed=71,failed=0,errors=0) for p in ('source','wheel')}
assert len(unknown['phases'])==2 and all(p['passed']==3 and not p['failed'] and not p['errors'] for p in unknown['phases'])
assert unknown['runtime_original_waits']==0 and unknown['external_original_waits']==6
assert trace['selected_checks_per_phase']==74 and trace['actual_M1_admissions']==0
assert not trace['public_entry_implementation']['public_start'] and not trace['stable_increment17']
assert 'bootstrap_launcher' not in (root/'src/xverse/maestro/__init__.py').read_text()
thesis=Path('/home/jefferson/distributed_safety_critical_thesis')
tasks=thesis/'specs/024-maestro-lite-lifecycle/tasks.md';task_text=tasks.read_text()
assert task_text.count('- [ ] P3-T')==7 and '- [X] P3-T' not in task_text
assert sha(trace_path) in task_text and sha(capa_path) in (base/'continuation-bootstrap-launcher-20261019.md').read_text()
work_products=['docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0002.md',
    'docs/engineering/maestro-lite/bootstrap-launcher.md','docs/engineering/maestro-lite/runtime-entry.md',
    'docs/engineering/maestro-lite/capa.md','docs/engineering/maestro-lite/README.md',
    str((base/'continuation-bootstrap-launcher-20261019.md').relative_to(root))]
result=dict(checker_sha256=sha(Path(__file__)),source_test_frozen_files_unchanged={k:len(v) for k,v in manifests.items()},
    original_draft_input_bindings_unchanged=len(inputs['inputs']),all_77_previous_production_sources_unchanged=True,
    new_component_forward_reverse_endpoints_checked=endpoints,partial_requirement_rows=24,
    capa_records=13,capa_evidence_bindings=64,selected_checks_per_phase=74,
    trace_sha256=sha(trace_path),latest_capa_sha256=sha(capa_path),
    spec_kit_tasks=dict(path=str(tasks),sha256=sha(tasks),full_tasks_unchecked=7),
    work_product_hashes={n:sha(root/n) for n in work_products},
    actual_M1_admissions=0,full_increment17_complete=False,stable_increment17=False,accepted=False,merged=False)
with (base/'bootstrap-launcher-work-products-check.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(result))
