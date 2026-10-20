"""Current exact b/c scope, bidirectional trace, unchanged inputs and open gates."""
import ast
import hashlib
import json
from pathlib import Path

base=Path(__file__).resolve().parent;root=base.parents[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
b=read(base/'runtime-entry-20261019b/frozen-inputs.json');c=read(base/'runtime-entry-20261019c/frozen-inputs.json')
assert all(sha(root/n)==h for n,h in c.items())
assert {n:h for n,h in b.items() if n.startswith('src/')}=={n:h for n,h in c.items() if n.startswith('src/')}
assert all(b[n]==c[n] for n in ('tests/thesis_lite/maestro/test_runtime_evidence.py','tests/thesis_lite/maestro/test_runtime_evidence_window.py'))
prior=read(base/'bootstrap-launcher-unknown-20261019a/frozen-inputs.json')
assert all(prior[n]==h for n,h in c.items() if n.startswith('src/') and n in prior)
assert set(n for n in c if n.startswith('src/') and n not in prior)=={'src/xverse/maestro/runtime_evidence.py','src/xverse/maestro/runtime_entry.py'}
inputs=read(root/'docs/engineering/maestro-lite/coverage-runtime-closure-inputs.json')
assert all(sha(Path(r['path']))==r['sha256'] for r in inputs['inputs'])
capa_path=base/'capa-20261019-runtime-entry/register.json';capa=read(capa_path)
checked=read(capa_path.parent/'verification-recheck.json')
assert sha(capa_path)==checked['register_sha256'] and checked['records_validated']==16 and checked['evidence_bindings_verified']==76
for key,item in capa['evidence'].items():
    p=root/item['path']
    if item['kind']=='file':digest=sha(p)
    else:
        s=p.read_text();digest=hashlib.sha256(s[s.index('\n'+item['start'])+1:s.index('\n'+item['end'])].encode()).hexdigest()
    assert digest==item['sha256'],key
assert all(capa['action_plans'][r['capa_id']]['effectiveness']['status']=='NOT_DEMONSTRATED' for r in capa['records'])
assert {r['capa_id'] for r in capa['records'] if r['state']=='UNRESOLVED'}=={'ML-CAPA-135','ML-CAPA-222'}
trace_path=base/'runtime-entry-partial-traceability.json';trace=read(trace_path)
assert len(trace['requirements'])==24 and all(not r['full_requirement_closure'] for r in trace['requirements'])
endpoints=0
for row in trace['requirements']:
    for delta in row['component_deltas']:
        if delta.get('maturity') not in ('actual_external_file_bytes_current_host_checks_inert_verified','private_original_whole_lifecycle_owned_composition_verified'):continue
        for item in delta['code']+delta['tests']:
            path,name=item['endpoint'].split('::');frozen=read(base/item['frozen_manifest'])
            assert frozen[path]==item['file_sha256']==sha(root/path)
            tree=ast.parse((root/path).read_text());scope=tree;parts=name.split('.')
            if len(parts)==2:scope=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==parts[0])
            node=next(n for n in scope.body if isinstance(n,ast.FunctionDef) and n.name==parts[-1])
            assert node.lineno==item['line'] and row['id'] in trace['reverse_endpoint_requirements'][item['endpoint']]
            endpoints+=1
for name in ('parent_trace','evidence','selected_evidence_file_checks','initial_entry_evidence','original_probe_driver_failure','original_actual_expiry_failure','CAPA','CAPA_validation'):
    item=trace[name];assert sha(base/item['path'])==item['sha256']
assert sha(root/trace['ADR']['path'])==trace['ADR']['sha256']
vb=read(base/'runtime-entry-20261019b/verification.json');vc=read(base/'runtime-entry-20261019c/verification.json')
assert vb['counts']=={p:dict(passed=26,failed=1,errors=0) for p in ('source','wheel')}
assert vc['counts']=={p:dict(passed=67,failed=0,errors=0) for p in ('source','wheel')}
selected=[r for r in vb['phases'] if r['cohort'] in ('runtime_evidence','runtime_evidence_window')]
assert all(r['returncode']==0 for r in selected)
assert all(sum(r['passed'] for r in selected if r['phase']==p)==19 for p in ('source','wheel'))
assert trace['selected_checks_per_phase']==86 and trace['actual_M1_admissions']==0
assert not trace['public_entry_implementation']['public_start'] and not trace['stable_increment17']
assert 'runtime_entry' not in (root/'src/xverse/maestro/__init__.py').read_text()
tasks=Path('/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/tasks.md');task_text=tasks.read_text()
assert task_text.count('- [ ] P3-T')==7 and '- [X] P3-T' not in task_text and sha(trace_path) in task_text
handoff=base/'continuation-runtime-entry-20261019.md'
assert sha(capa_path) in handoff.read_text() and sha(trace_path) in handoff.read_text()
products=['docs/engineering/maestro-lite/ADR-ML3-RUNTIME-0003.md','docs/engineering/maestro-lite/runtime-entry-composition.md',
    'docs/engineering/maestro-lite/runtime-entry.md','docs/engineering/maestro-lite/capa.md','docs/engineering/maestro-lite/README.md',
    str(handoff.relative_to(root))]
result=dict(checker_sha256=sha(Path(__file__)),current_c_frozen_files_unchanged=len(c),
    original_draft_input_bindings_unchanged=len(inputs['inputs']),all_78_previous_production_sources_unchanged=True,
    current_b_c_production_bytes_identical=True,new_forward_reverse_endpoint_links_checked=endpoints,
    partial_requirement_rows=24,capa_records=16,capa_bindings=76,selected_evidence_checks_per_phase=19,
    current_entry_adjacent_checks_per_phase=67,selected_checks_per_phase=86,
    trace_sha256=sha(trace_path),latest_capa_sha256=sha(capa_path),
    spec_kit_tasks=dict(path=str(tasks),sha256=sha(tasks),all_seven_unchecked=True),
    work_product_hashes={n:sha(root/n) for n in products},actual_M1_admissions=0,
    full_increment17_complete=False,stable_increment17=False,accepted=False,merged=False)
with (base/'runtime-entry-work-products-check.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(result))
