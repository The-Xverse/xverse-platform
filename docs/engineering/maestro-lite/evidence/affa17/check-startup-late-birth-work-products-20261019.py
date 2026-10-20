"""Verify exact unchanged production and partial late/unknown-birth scope."""
import ast,hashlib,json
from pathlib import Path
base=Path(__file__).resolve().parent;root=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_bytes())
prior=read(base/'startup-ownership-20261019c/frozen-inputs.json');manifests={}
for s in ('a','b'):
    m=read(base/f'startup-late-birth-20261019{s}/frozen-inputs.json');manifests[s]=m
    assert all(sha(root/n)==h for n,h in m.items())
    assert {n:h for n,h in m.items() if n.startswith('src/')}=={n:h for n,h in prior.items() if n.startswith('src/')}
p=base/'startup-late-birth-partial-traceability.json';trace=read(p);reverse={};occurrences=0
assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18
for row in trace['requirements']:
    assert not row['full_requirement_closure']
    for delta in row['component_deltas']:
        assert not delta['full_requirement_closure']
        for item in delta['code']+delta['tests']:
            path,name=item['endpoint'].split('::');m=read(base/item['frozen_manifest'])
            assert sha(root/path)==m[path]==item['file_sha256']
            t=ast.parse((root/path).read_text());parts=name.split('.');scope=t
            if len(parts)==2:scope=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name==parts[0])
            n=next(n for n in scope.body if isinstance(n,ast.FunctionDef) and n.name==parts[-1]);assert n.lineno==item['line']
            reverse.setdefault(item['endpoint'],set()).add(row['id']);occurrences+=1
assert {e:sorted(ids) for e,ids in reverse.items()}==trace['reverse_endpoint_requirements']
assert len(reverse)==12 and sum(len(ids) for ids in reverse.values())==occurrences==64
for key in ('parent_trace','current_scope','ADR','CAPA','CAPA_validation'):
    item=trace[key];q=Path(item['path'])
    if not q.is_absolute():q=(root if str(q).startswith('docs/') else base)/q
    assert sha(q)==item['sha256'],key
for item in trace['evidence']:assert sha(base/item['path'])==item['sha256']
va,vb=[read(base/f'startup-late-birth-20261019{s}/verification.json') for s in ('a','b')]
for v,expected in ((va,4),(vb,2)):
    assert {row['phase']:row['passed'] for row in v['phases']}=={'source':expected,'wheel':expected}
    assert v['production_sources_identical_to_startup_ownership_c'] and v['packaged_sources']==81
    assert v['actual_M1_admissions']==v['actual_service_runtime_runs']==0
    for item in v['root_receipts']+v['cases']:
        folder='startup-late-birth-20261019a' if v is va else 'startup-late-birth-20261019b'
        assert sha(base/folder/item['path'])==item['sha256']
assert len(va['root_receipts'])==8 and len(vb['root_receipts'])==4
assert va['product_original_waits']==va['external_original_waits']==vb['actual_external_original_waits']==4
assert va['unknown_outcomes_preserved_after_external_reap'] and vb['product_unknown_outcomes_preserved']
assert trace['selected_checks_passed_per_phase']==75 and trace['new_checks_passed_per_phase']==6
capa=read(base/trace['CAPA']['path']);assert len(capa['records'])==25 and len(capa['evidence'])==133
for key,item in capa['evidence'].items():
    q=root/item['path']
    if item['kind']=='file':digest=sha(q)
    else:
        text=q.read_text();digest=hashlib.sha256(text[text.index('\n'+item['start'])+1:text.index('\n'+item['end'])].encode()).hexdigest()
    assert digest==item['sha256'],key
assert {r['capa_id'] for r in capa['records'] if r['state']=='UNRESOLVED'}=={'ML-CAPA-135','ML-CAPA-222','ML-CAPA-286','ML-CAPA-287'}
inputs=read(root/'docs/engineering/maestro-lite/coverage-runtime-closure-inputs.json')
assert len(inputs['inputs'])==8 and all(sha(Path(i['path']))==i['sha256'] for i in inputs['inputs'])
for key in ('stable_increment17','whole_platform_regression','full_M1_complete','full_candidate_review_complete','source_parent_semantics_validated','all_seven_phase3_tasks_complete','independent_CAPA_effectiveness','accepted','merged','scientific_result'):assert trace[key] is False
assert trace['actual_M1_admissions']==0 and trace['open_findings']==[135,222,286,287]
tasks=Path('/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/tasks.md')
assert tasks.read_text().count('- [ ] P3-T')==7 and sha(p) in tasks.read_text()
handoff=base/'continuation-startup-late-birth-20261019.md';assert sha(p) in handoff.read_text()
products=['docs/engineering/maestro-lite/startup-late-birth.md','docs/engineering/maestro-lite/README.md','docs/engineering/maestro-lite/bootstrap-launcher.md',str(handoff.relative_to(root))]
result=dict(checker_sha256=sha(Path(__file__)),production_sources_unchanged=81,new_endpoint_links=64,new_endpoints=12,requirement_rows_retained=24,new_checks_passed_per_phase=6,selected_checks_passed_per_phase=75,new_roots_removed=12,new_product_original_waits=4,new_external_original_waits=8,unknown_product_outcomes_preserved=True,source_parent_semantics_validated=False,original_draft_input_bindings_unchanged=8,capa_records=25,capa_bindings=133,trace_sha256=sha(p),spec_kit_tasks=dict(path=str(tasks),sha256=sha(tasks),all_seven_unchecked=True),work_product_hashes={q:sha(root/q) for q in products},actual_M1_admissions=0,stable_increment17=False,accepted=False,merged=False)
with (base/'startup-late-birth-work-products-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
