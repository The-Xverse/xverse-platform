"""Verify exact diagnostic candidate and bounded partial claims; no gate transitions."""
import ast
import hashlib
import json
from pathlib import Path
base=Path(__file__).resolve().parent;root=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_bytes())
manifest=read(base/'rpc-failure-20261019a/frozen-inputs.json')
assert all(sha(root/n)==h for n,h in manifest.items())
prior=read(base/'runtime-service-20261019c/frozen-inputs.json')
assert [n for n,h in manifest.items() if n.startswith('src/') and prior.get(n)!=h]==['src/xverse/maestro/runtime_entry.py','src/xverse/maestro/persistence.py'] or set(n for n,h in manifest.items() if n.startswith('src/') and prior.get(n)!=h)=={'src/xverse/maestro/runtime_entry.py','src/xverse/maestro/persistence.py'}
p=base/'rpc-failure-partial-traceability.json';trace=read(p)
assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18
reverse={};occurrences=0
for row in trace['requirements']:
    assert not row['full_requirement_closure']
    for delta in row['component_deltas']:
        assert not delta['full_requirement_closure']
        for item in delta['code']+delta['tests']:
            path,name=item['endpoint'].split('::');assert manifest[path]==sha(root/path)==item['file_sha256']
            tree=ast.parse((root/path).read_text());parts=name.split('.');scope=tree
            if len(parts)==2:scope=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==parts[0])
            node=next(n for n in scope.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==parts[-1])
            assert node.lineno==item['line'];reverse.setdefault(item['endpoint'],set()).add(row['id']);occurrences+=1
assert {e:sorted(ids) for e,ids in reverse.items()}==trace['reverse_endpoint_requirements']
assert len(reverse)==9 and sum(len(ids) for ids in reverse.values())==occurrences==36
for key in ('parent_trace','evidence','retained_failure_localization','production_delta','ADR','CAPA','CAPA_validation'):
    item=trace[key];path=Path(item['path'])
    if not path.is_absolute():path=(root if str(path).startswith('docs/') else base)/path
    assert sha(path)==item['sha256'],key
v=read(base/'rpc-failure-20261019a/verification.json')
assert v['counts']=={phase:dict(passed=57,failed=0,errors=0) for phase in ('source','wheel')}
assert v['packaged_sources']==81 and v['all_79_other_production_sources_unchanged']
assert len(v['root_receipts'])==114 and len(v['rpc_failure_contexts'])==10 and len(v['startup_cases'])==12
assert v['source_links']==254 and len(v['retained_durable_closed_roots'])==4
assert v['auditor_sha256']==sha(base/'audit-rpc-failure-20261019a.py')
for item in v['retained_durable_closed_roots']:
    folder=base/'rpc-failure-20261019a'/item['path']
    assert {str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file()}==item['files']
for item in v['rpc_failure_contexts']:
    assert sha(base/'rpc-failure-20261019a'/item['path'])==item['sha256']
assert v['actual_M1_admissions']==v['actual_service_runtime_runs']==trace['actual_M1_admissions']==0
assert trace['open_findings']==[135,222,286,287]
for k in ('stable_increment17','whole_platform_regression','full_M1_complete','full_candidate_review_complete','source_parent_semantics_validated','all_seven_phase3_tasks_complete','independent_CAPA_effectiveness','accepted','merged','scientific_result'):assert trace[k] is False
capa=read(base/trace['CAPA']['path']);assert len(capa['records'])==22 and len(capa['evidence'])==104
for key,item in capa['evidence'].items():
    path=root/item['path']
    if item['kind']=='file':digest=sha(path)
    else:
        s=path.read_text();digest=hashlib.sha256(s[s.index('\n'+item['start'])+1:s.index('\n'+item['end'])].encode()).hexdigest()
    assert digest==item['sha256'],key
assert {r['capa_id'] for r in capa['records'] if r['state']=='UNRESOLVED'}=={'ML-CAPA-135','ML-CAPA-222','ML-CAPA-286','ML-CAPA-287'}
inputs=read(root/'docs/engineering/maestro-lite/coverage-runtime-closure-inputs.json')
assert len(inputs['inputs'])==8 and all(sha(Path(i['path']))==i['sha256'] for i in inputs['inputs'])
tasks=Path('/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/tasks.md')
assert tasks.read_text().count('- [ ] P3-T')==7 and sha(p) in tasks.read_text()
assert 'runtime_service' not in (root/'src/xverse/maestro/__init__.py').read_text()
handoff=base/'continuation-rpc-failure-20261019.md';assert sha(p) in handoff.read_text()
products=['docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0006.md','docs/engineering/maestro-lite/rpc-failure-context.md','docs/engineering/maestro-lite/README.md','docs/engineering/maestro-lite/runtime-entry-composition.md',str(handoff.relative_to(root))]
result=dict(checker_sha256=sha(Path(__file__)),current_frozen_files_verified=len(manifest),production_packaged_sources=81,all_79_other_production_sources_unchanged=True,original_draft_input_bindings_unchanged=8,new_forward_reverse_endpoint_links_checked=occurrences,unique_endpoints=len(reverse),partial_requirement_rows=24,selected_checks_passed_per_phase=57,actual_failure_contexts=10,owned_parent_reservations_removed=114,source_links=254,retained_closed_original_input_roots=4,capa_records=22,capa_bindings=104,trace_sha256=sha(p),spec_kit_tasks=dict(path=str(tasks),sha256=sha(tasks),all_seven_unchecked=True),work_product_hashes={n:sha(root/n) for n in products},actual_M1_admissions=0,unresolved_findings=[135,222,286,287],stable_increment17=False,accepted=False,merged=False)
with (base/'rpc-failure-work-products-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
