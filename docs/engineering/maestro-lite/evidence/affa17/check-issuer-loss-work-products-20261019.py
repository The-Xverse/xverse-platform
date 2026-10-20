"""Check exact current repair inputs, AST scope, endpoints and evidence bindings."""
import ast
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
root = base.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
folder = base/'composed-issuer-loss-20261019c'
frozen = read(folder/'frozen-inputs.json')
assert all(sha(root/n) == h for n,h in frozen.items())
inputs = read(root/'docs/engineering/maestro-lite/coverage-runtime-closure-inputs.json')
assert all(sha(Path(r['path'])) == r['sha256'] for r in inputs['inputs'])
capa_path = base/'capa-20261019-issuer-loss/register.json'
capa = read(capa_path)
for key,item in capa['evidence'].items():
    path = root/item['path']
    if item['kind'] == 'file':
        digest = sha(path)
    else:
        text = path.read_text()
        digest = hashlib.sha256(text[text.index('\n'+item['start'])+1:text.index('\n'+item['end'])].encode()).hexdigest()
    assert digest == item['sha256'],key
trace_path = base/'issuer-loss-partial-traceability.json'
trace = read(trace_path)
assert len(trace['requirements']) == 24 and all(not r['full_requirement_closure'] for r in trace['requirements'])
for row in trace['requirements']:
    for delta in row['component_deltas']:
        if delta.get('maturity') == 'original_cleanup_context_repair_verified_locally':
            for endpoint in delta['code']+delta['tests']:
                path,name = endpoint['endpoint'].split('::')
                assert frozen[path] == endpoint['file_sha256']
                assert 'def '+name.split('.')[-1]+'(' in (root/path).read_text().splitlines()[endpoint['line']-1]
for name in ('parent_trace','evidence','original_red','original_counterexample',
             'partial_repair_and_harness_failure','CAPA','CAPA_validation'):
    ref = trace[name]
    assert sha(base/ref['path']) == ref['sha256']
baseline = base/'composed-issuer-loss-20261019a'
old_source = Path(read(baseline/'running.json')['frozen_source_root'])
old_frozen = read(baseline/'frozen-inputs.json')
changed = [n for n,h in frozen.items() if n.startswith('src/') and old_frozen[n] != h]
assert set(changed) == {'src/xverse/maestro/run_broker.py','src/xverse/maestro/run_closure.py'}
allowed = {'RunBroker':{'_holder','_cleanup_context','cancel'},'RunUnitIssuer':{'cancel'},'RunClosure':{'close'}}
for path in changed:
    trees = []
    for source in (old_source,root):
        tree = ast.parse((source/path).read_text())
        for node in tree.body:
            if isinstance(node,ast.ClassDef) and node.name in allowed:
                node.body = [f for f in node.body if not isinstance(f,ast.FunctionDef) or f.name not in allowed[node.name]]
        trees.append(ast.dump(tree,include_attributes=False))
    assert trees[0] == trees[1],path
for suffix in ('a','b','c'):
    out = base/('composed-issuer-loss-20261019'+suffix)
    for row in read(out/'native-retention.json'):
        assert sha(out/row['binary']) == row['binary_sha256']
        assert sha(out/row['compiler_receipt']) == row['compiler_receipt_sha256']
result = dict(checker_sha256=sha(Path(__file__)),source_and_test_frozen_files_unchanged=len(frozen),
    original_draft_input_bindings_unchanged=len(inputs['inputs']),capa_records=len(capa['records']),
    capa_evidence_bindings=len(capa['evidence']),partial_requirement_rows=24,
    changed_production_sources=changed,all_other_production_AST_unchanged=True,
    trace_sha256=sha(trace_path),latest_capa_sha256=sha(capa_path),
    full_increment17_complete=False,accepted=False,merged=False)
with (base/'issuer-loss-work-products-check.json').open('x') as stream:
    json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(result))
