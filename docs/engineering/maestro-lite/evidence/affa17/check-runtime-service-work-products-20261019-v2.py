"""Bound partial service trace to exact sources, original evidence and open gates."""
import ast
import hashlib
import json
from pathlib import Path
base=Path(__file__).resolve().parent;root=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
def check_binding(item):
    p=Path(item['path'])
    if not p.is_absolute():p=(root if str(p).startswith('docs/') else base)/p
    assert sha(p)==item['sha256'],str(p)
    return p
fb,fc=[read(base/f'runtime-service-20261019{x}/frozen-inputs.json') for x in ('b','c')]
assert all(sha(root/n)==h for n,h in fc.items())
changed=[n for n,h in fc.items() if fb[n]!=h]
assert set(changed)=={'src/xverse/maestro/bootstrap.py','tests/thesis_lite/maestro/test_runtime_start_window.py'}
br=Path(read(base/'runtime-service-20261019b/running.json')['frozen_source_root'])
old,new=[ast.parse(p.read_text()) for p in (br/'src/xverse/maestro/bootstrap.py',root/'src/xverse/maestro/bootstrap.py')]
birth=next(n for c in new.body if isinstance(c,ast.ClassDef) and c.name=='BootstrapSession' for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='birth')
body=next(n.body for n in ast.walk(birth) if isinstance(n,ast.Try) and any(isinstance(s,ast.AugAssign) and ast.unparse(s.target)=='self._slot' for s in n.body))
slot=next(i for i,n in enumerate(body) if isinstance(n,ast.AugAssign) and ast.unparse(n.target)=='self._slot')
assert ast.unparse(body[slot-1])=='self.check_start_authorization()';body.pop(slot-1)
assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False)
trace_path=base/'runtime-service-partial-traceability.json';trace=read(trace_path)
assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18
links=0;reverse={}
for row in trace['requirements']:
    assert not row['full_requirement_closure']
    for delta in row['component_deltas']:
        assert not delta['full_requirement_closure'] and delta['actual_service_runtime_runs']==0
        for binding in delta['evidence']:check_binding(binding)
        for item in delta['code']+delta['tests']:
            path,name=item['endpoint'].split('::');manifest=read(base/item['frozen_manifest'])
            frozen_root=Path(read((base/item['frozen_manifest']).parent/'running.json')['frozen_source_root'])
            assert sha(frozen_root/path)==manifest[path]==sha(root/path)==item['file_sha256']
            tree=ast.parse((frozen_root/path).read_text());scope=tree;parts=name.split('.')
            if len(parts)==2:scope=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==parts[0])
            node=next(n for n in scope.body if isinstance(n,ast.FunctionDef) and n.name==parts[-1])
            assert node.lineno==item['line'];reverse.setdefault(item['endpoint'],set()).add(row['id']);links+=1
assert {e:sorted(ids) for e,ids in reverse.items()}==trace['reverse_endpoint_requirements']
occurrences=links;links=sum(len(ids) for ids in reverse.values())
assert links==238 and len(reverse)==43 and occurrences==242
for key in ('parent_trace','original_service_failure','evidence_reuse','CAPA','CAPA_validation','ADR'):check_binding(trace[key])
for item in trace['evidence']:check_binding(item)
for suffix,expected in [('b',72),('c',31)]:
    v=read(base/f'runtime-service-20261019{suffix}/verification-v2.json')
    assert v['counts']=={p:dict(passed=expected,failed=0,errors=0) for p in ('source','wheel')}
    assert v['actual_service_runtime_runs']==v['actual_M1_admissions']==0 and v['source_links']==508
    assert len(v['retained_durable_closed_roots'])==8
    assert v['packaged_sources']==81 and v['all_76_other_production_sources_unchanged']
    assert v['auditor_sha256']==sha(base/'audit-runtime-service-20261019-v2.py')
    for item in v['retained_durable_closed_roots']:
        folder=base/f'runtime-service-20261019{suffix}'/item['path']
        assert {str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file()}==item['files']
    if suffix=='b':
        for phase in ('source','wheel'):
            assert sum(p['passed'] for p in v['phases'] if p['phase']==phase and p['cohort'] in ('runtime_service','bootstrap_launcher'))==42
capa=read(base/trace['CAPA']['path']);validated=read(base/trace['CAPA_validation']['path'])
assert len(capa['records'])==validated['records_validated']==22
assert len(capa['evidence'])==validated['evidence_bindings_verified']==104
assert validated['register_sha256']==trace['CAPA']['sha256']
for key,item in capa['evidence'].items():
    p=root/item['path']
    if item['kind']=='file':digest=sha(p)
    else:
        s=p.read_text();digest=hashlib.sha256(s[s.index('\n'+item['start'])+1:s.index('\n'+item['end'])].encode()).hexdigest()
    assert digest==item['sha256'],key
assert {r['capa_id'] for r in capa['records'] if r['state']=='UNRESOLVED'}=={'ML-CAPA-135','ML-CAPA-222','ML-CAPA-286','ML-CAPA-287'}
assert all(p['effectiveness']['status']=='NOT_DEMONSTRATED' for p in capa['action_plans'].values())
inputs=read(root/'docs/engineering/maestro-lite/coverage-runtime-closure-inputs.json')
assert len(inputs['inputs'])==8 and all(sha(Path(r['path']))==r['sha256'] for r in inputs['inputs'])
assert trace['open_findings']==[135,222,286,287] and trace['actual_M1_admissions']==0
for key in ('stable_increment17','full_M1_complete','whole_platform_regression','full_candidate_review_complete','source_parent_semantics_validated','all_seven_phase3_tasks_complete','accepted','merged'):assert trace[key] is False
assert 'runtime_service' not in (root/'src/xverse/maestro/__init__.py').read_text()
tasks=Path('/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/tasks.md')
assert tasks.read_text().count('- [ ] P3-T')==7 and sha(trace_path) in tasks.read_text()
handoff=base/'continuation-runtime-service-20261019.md'
assert sha(trace_path) in handoff.read_text() and trace['CAPA']['sha256'] in handoff.read_text()
products=['docs/engineering/maestro-lite/runtime-service.md','docs/engineering/maestro-lite/README.md','docs/engineering/maestro-lite/runtime-entry-composition.md','docs/engineering/maestro-lite/capa.md',str(handoff.relative_to(root))]
result=dict(checker_sha256=sha(Path(__file__)),current_frozen_files_verified=len(fc),production_packaged_sources=81,all_76_other_production_sources_unchanged=True,b_c_production_AST_delta_verified=True,original_draft_input_bindings_unchanged=8,new_forward_reverse_endpoint_links_checked=links,endpoint_occurrences_checked=occurrences,unique_endpoints=len(reverse),partial_requirement_rows=24,source_parents_retained=18,selected_checks_passed_per_phase=73,capa_records=22,capa_bindings=104,trace_sha256=sha(trace_path),latest_capa_sha256=trace['CAPA']['sha256'],spec_kit_tasks=dict(path=str(tasks),sha256=sha(tasks),all_seven_unchecked=True),work_product_hashes={p:sha(root/p) for p in products},actual_M1_admissions=0,actual_service_runtime_runs=0,unresolved_findings=[135,222,286,287],effectiveness_demonstrated=False,stable_increment17=False,accepted=False,merged=False)
with (base/'runtime-service-work-products-check-v2.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
