"""Bind selected startup ownership repair to exact evidence; keep full gates open."""
import ast
import hashlib
import json
from pathlib import Path
base=Path(__file__).resolve().parent;root=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
folder=base/'startup-ownership-20261019c';manifest=read(folder/'frozen-inputs.json')
assert all(sha(root/n)==h for n,h in manifest.items())
prior=read(base/'rpc-context-loss-20261019c/frozen-inputs.json')
for suffix in ('a','b'):
    m=read(base/f'startup-ownership-20261019{suffix}/frozen-inputs.json')
    assert {n:h for n,h in m.items() if n.startswith('src/')}=={n:h for n,h in prior.items() if n.startswith('src/')}
assert {n for n,h in manifest.items() if n.startswith('src/') and prior.get(n)!=h}=={'src/xverse/maestro/bootstrap_launcher.py'}
p=base/'startup-ownership-partial-traceability.json';trace=read(p);reverse={};occurrences=0
assert len(trace['requirements'])==24 and {row['id'] for row in trace['requirements']}=={f'ML-SR-{i:03}' for i in range(1,25)}
for row in trace['requirements']:
    assert not row['full_requirement_closure']
    for delta in row['component_deltas']:
        assert not delta['full_requirement_closure']
        for item in delta['code']+delta['tests']:
            path,name=item['endpoint'].split('::');assert sha(root/path)==manifest[path]==item['file_sha256']
            tree=ast.parse((root/path).read_text());parts=name.split('.');scope=tree
            if len(parts)==2:scope=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==parts[0])
            node=next(n for n in scope.body if isinstance(n,ast.FunctionDef) and n.name==parts[-1]);assert node.lineno==item['line']
            reverse.setdefault(item['endpoint'],set()).add(row['id']);occurrences+=1
assert {e:sorted(ids) for e,ids in reverse.items()}==trace['reverse_endpoint_requirements']
assert len(reverse)==13 and sum(len(ids) for ids in reverse.values())==occurrences==65
for key in ('parent_trace','evidence','original_harness_failure','original_ownership_failure','ADR','CAPA','CAPA_validation'):
    item=trace[key];path=Path(item['path'])
    if not path.is_absolute():path=(root if str(path).startswith('docs/') else base)/path
    assert sha(path)==item['sha256'],key
va,vb,vc=[read(base/f'startup-ownership-20261019{s}/verification-v2.json') for s in ('a','b','c')]
assert va['counts']==vb['counts']=={phase:dict(passed=0,failed=5,errors=0) for phase in ('source','wheel')}
assert va['historical_harness_sentinel_waits_unknown'] and not va['startup_alias_cases'] and not va['sentinel_waits']
assert len(vb['startup_alias_cases'])==10 and sum(x['forbidden_signal_attempts'] for x in vb['startup_alias_cases'])==4
assert sum(x['external_root_cleanup'] for x in vb['startup_alias_cases'])==4
assert vc['counts']=={phase:dict(passed=69,failed=0,errors=0) for phase in ('source','wheel')}
assert vc['other_production_sources_unchanged']==80 and vc['packaged_sources']==81
assert len(vc['root_receipts'])==122 and len(vc['startup_alias_cases'])==len(vc['sentinel_waits'])==10
assert all(x['ordinary_rejected'] and not x['forbidden_signal_attempts'] and not x['external_root_cleanup'] and x['primary_original_wait_consumed'] for x in vc['startup_alias_cases'])
assert len(vc['startup_cases'])==12 and vc['source_links']==508 and len(vc['retained_durable_closed_roots'])==8
assert vc['auditor_sha256']==sha(base/'audit-startup-ownership-20261019-v2.py')
assert 'first_failure_retention_verified' not in vc
for item in vc['startup_alias_cases']+vc['sentinel_waits']:
    assert sha(folder/item['path'])==item['sha256']
for item in vc['retained_durable_closed_roots']:
    d=folder/item['path'];assert {str(f.relative_to(d)):sha(f) for f in d.rglob('*') if f.is_file()}==item['files']
capa=read(base/trace['CAPA']['path']);validated=read(base/trace['CAPA_validation']['path'])
assert len(capa['records'])==validated['records_validated']==25
assert len(capa['evidence'])==validated['evidence_bindings_verified']==133
for key,item in capa['evidence'].items():
    f=root/item['path']
    if item['kind']=='file':digest=sha(f)
    else:
        s=f.read_text();digest=hashlib.sha256(s[s.index('\n'+item['start'])+1:s.index('\n'+item['end'])].encode()).hexdigest()
    assert digest==item['sha256'],key
assert {row['capa_id'] for row in capa['records'] if row['state']=='UNRESOLVED'}=={'ML-CAPA-135','ML-CAPA-222','ML-CAPA-286','ML-CAPA-287'}
assert all(plan['effectiveness']['status']=='NOT_DEMONSTRATED' for plan in capa['action_plans'].values())
inputs=read(root/'docs/engineering/maestro-lite/coverage-runtime-closure-inputs.json')
assert len(inputs['inputs'])==8 and all(sha(Path(i['path']))==i['sha256'] for i in inputs['inputs'])
for k in ('stable_increment17','whole_platform_regression','full_M1_complete','full_candidate_review_complete','source_parent_semantics_validated','all_seven_phase3_tasks_complete','independent_CAPA_effectiveness','accepted','merged','scientific_result'):assert trace[k] is False
assert trace['actual_M1_admissions']==vc['actual_M1_admissions']==0 and trace['open_findings']==[135,222,286,287]
tasks=Path('/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/tasks.md')
assert tasks.read_text().count('- [ ] P3-T')==7 and sha(p) in tasks.read_text()
assert 'runtime_service' not in (root/'src/xverse/maestro/__init__.py').read_text()
handoff=base/'continuation-startup-ownership-20261019.md';assert sha(p) in handoff.read_text() and trace['CAPA']['sha256'] in handoff.read_text()
products=['docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0008.md','docs/engineering/maestro-lite/startup-ownership.md','docs/engineering/maestro-lite/bootstrap-launcher.md','docs/engineering/maestro-lite/capa.md','docs/engineering/maestro-lite/README.md',str(handoff.relative_to(root))]
result=dict(checker_sha256=sha(Path(__file__)),current_frozen_files_verified=len(manifest),packaged_sources=81,all_80_other_production_sources_unchanged=True,original_draft_input_bindings_unchanged=8,partial_requirement_rows=24,new_endpoints=13,new_forward_reverse_links=65,current_selected_passed_per_phase=69,root_reservations_removed=122,alias_cases=10,sentinel_waits=10,foreign_signal_attempts=0,external_root_fallbacks=0,historical_harness_sentinel_waits_unknown=True,actual_M3_links=508,retained_closed_original_input_roots=8,capa_records=25,capa_bindings=133,trace_sha256=sha(p),spec_kit_tasks=dict(path=str(tasks),sha256=sha(tasks),all_seven_unchecked=True),work_product_hashes={n:sha(root/n) for n in products},actual_M1_admissions=0,unresolved_findings=[135,222,286,287],stable_increment17=False,accepted=False,merged=False)
with (base/'startup-ownership-work-products-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
