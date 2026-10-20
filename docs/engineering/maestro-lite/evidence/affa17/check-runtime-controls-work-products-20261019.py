"""Exact current production, retained counterevidence and unclosed full scope."""
import ast
import hashlib
import json
from pathlib import Path

base=Path(__file__).resolve().parent;root=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
b='runtime-controls-20261019b';d='runtime-controls-diagnostic-20261019d'
fb,fd=read(base/b/'frozen-inputs.json'),read(base/d/'frozen-inputs.json')
assert all(sha(root/n)==h for n,h in fd.items())
assert {n:h for n,h in fb.items() if n.startswith('src/')}=={n:h for n,h in fd.items() if n.startswith('src/')}
prior=read(base/'runtime-entry-20261019c/frozen-inputs.json')
assert [n for n,h in fd.items() if n.startswith('src/') and prior[n]!=h]==['src/xverse/maestro/runtime_entry.py']
inputs=read(root/'docs/engineering/maestro-lite/coverage-runtime-closure-inputs.json')
assert all(sha(Path(r['path']))==r['sha256'] for r in inputs['inputs'])
capa_path=base/'capa-20261019-runtime-controls/register.json';capa=read(capa_path)
checked=read(capa_path.parent/'verification-recheck.json')
assert sha(capa_path)==checked['register_sha256'] and checked['records_validated']==20 and checked['evidence_bindings_verified']==88
for key,item in capa['evidence'].items():
    p=root/item['path']
    if item['kind']=='file':digest=sha(p)
    else:
        s=p.read_text();digest=hashlib.sha256(s[s.index('\n'+item['start'])+1:s.index('\n'+item['end'])].encode()).hexdigest()
    assert digest==item['sha256'],key
assert {r['capa_id'] for r in capa['records'] if r['state']=='UNRESOLVED'}=={'ML-CAPA-135','ML-CAPA-222','ML-CAPA-286','ML-CAPA-287'}
assert all(capa['action_plans'][r['capa_id']]['effectiveness']['status']=='NOT_DEMONSTRATED' for r in capa['records'])
trace_path=base/'runtime-controls-partial-traceability.json';trace=read(trace_path)
assert len(trace['requirements'])==24 and all(not r['full_requirement_closure'] for r in trace['requirements'])
endpoints=0
for row in trace['requirements']:
    for delta in row['component_deltas']:
        if delta.get('maturity') not in ('original_pin_startup_cleanup_correction_owned_verified','private_original_registry_controls_partial_with_counterevidence'):continue
        for item in delta['code']+delta['tests']:
            path,name=item['endpoint'].split('::');manifest=read(base/item['frozen_manifest'])
            folder=(base/item['frozen_manifest']).parent
            frozen_root=Path(read(folder/'running.json')['frozen_source_root'])
            assert sha(frozen_root/path)==manifest[path]==item['file_sha256']
            if path.startswith('src/'):assert sha(root/path)==item['file_sha256']
            tree=ast.parse((frozen_root/path).read_text());scope=tree;parts=name.split('.')
            if len(parts)==2:scope=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==parts[0])
            node=next(n for n in scope.body if isinstance(n,ast.FunctionDef) and n.name==parts[-1])
            assert node.lineno==item['line'] and row['id'] in trace['reverse_endpoint_requirements'][item['endpoint']]
            endpoints+=1
for name in ('parent_trace','evidence','original_startup_failure','skipped_entry_regression','diagnostic_probe','rpc_observations','original_auditor_failure','CAPA','CAPA_validation'):
    item=trace[name];assert sha(base/item['path'])==item['sha256']
assert sha(root/trace['ADR']['path'])==trace['ADR']['sha256']
vb=read(base/b/'verification-v2.json');vd=read(base/d/'verification-v2.json')
assert vb['counts']=={'source':dict(passed=22,failed=0,errors=0),'wheel':dict(passed=21,failed=1,errors=0)}
assert vd['counts']=={p:dict(passed=2,failed=0,errors=0) for p in ('source','wheel')}
assert len(vb['startup_cases'])==12 and not any(r['fallback_used'] for r in vb['startup_cases'])
assert trace['open_findings']==[135,222,286,287] and not trace['stable_increment17']
assert trace['diagnostic_success_does_not_resolve_original_failures']
operations=[]
for p in (base/d).glob('*harness/lazy-operations-*'):
    operations+=read(p)['operations']
assert len(operations)==266 and all(o['ended']<=o['end'] for o in operations)
assert not trace['public_entry_implementation']['public_start'] and trace['actual_M1_admissions']==0
assert 'runtime_entry' not in (root/'src/xverse/maestro/__init__.py').read_text()
tasks=Path('/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/tasks.md');text=tasks.read_text()
assert text.count('- [ ] P3-T')==7 and '- [X] P3-T' not in text and sha(trace_path) in text
handoff=base/'continuation-runtime-controls-20261019.md'
assert sha(trace_path) in handoff.read_text() and sha(capa_path) in handoff.read_text()
products=['docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0004.md','docs/engineering/maestro-lite/runtime-controls.md',
    'docs/engineering/maestro-lite/runtime-entry-composition.md','docs/engineering/maestro-lite/README.md',
    'docs/engineering/maestro-lite/capa.md',str(handoff.relative_to(root))]
result=dict(checker_sha256=sha(Path(__file__)),current_frozen_files_unchanged=len(fd),current_b_c_d_production_bytes_identical=True,
    all_79_other_production_sources_unchanged=True,original_draft_input_bindings_unchanged=len(inputs['inputs']),
    new_forward_reverse_endpoint_links_checked=endpoints,partial_requirement_rows=24,capa_records=20,capa_bindings=88,
    startup_checks_passed_per_phase=14,unresolved_findings=[135,222,286,287],observed_diagnostic_RPCs=266,
    maximum_observed_RPC_seconds=max(o['ended']-o['began'] for o in operations),no_causal_or_stability_credit_from_probe=True,
    trace_sha256=sha(trace_path),latest_capa_sha256=sha(capa_path),
    spec_kit_tasks=dict(path=str(tasks),sha256=sha(tasks),all_seven_unchecked=True),
    work_product_hashes={n:sha(root/n) for n in products},actual_M1_admissions=0,
    full_increment17_complete=False,stable_increment17=False,accepted=False,merged=False)
with (base/'runtime-controls-work-products-check.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(result))
