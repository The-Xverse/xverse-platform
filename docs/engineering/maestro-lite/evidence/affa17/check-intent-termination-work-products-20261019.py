"""Final read-only input/endpoint/link checks; does not rerun native controls."""
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
root = base.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
frozen = read(base/'composed-intent-termination-20261019b/frozen-inputs.json')
assert all(sha(root/n) == h for n, h in frozen.items())
inputs = read(root/'docs/engineering/maestro-lite/coverage-runtime-closure-inputs.json')
assert all(sha(Path(r['path'])) == r['sha256'] for r in inputs['inputs'])
capa = read(base/'capa-20261019-intent-termination/register.json')
for key, item in capa['evidence'].items():
    p = root/item['path']
    if item['kind'] == 'file':
        digest = sha(p)
    else:
        text = p.read_text()
        digest = hashlib.sha256(text[text.index('\n'+item['start'])+1:text.index('\n'+item['end'])].encode()).hexdigest()
    assert digest == item['sha256'], key
trace_path = base/'composed-intent-termination-partial-traceability.json'
trace = read(trace_path)
assert len(trace['requirements']) == 24
assert all(not r['full_requirement_closure'] for r in trace['requirements'])
for row in trace['requirements']:
    for delta in row['component_deltas']:
        if delta.get('maturity') == 'selected_original_intent_and_termination_frontiers_verified':
            for endpoint in delta['code']+delta['tests']:
                path, name = endpoint['endpoint'].split('::')
                assert frozen[path] == endpoint['file_sha256']
                assert name in (root/path).read_text().splitlines()[endpoint['line']-1], endpoint
for name in ('parent_trace', 'evidence', 'CAPA', 'CAPA_validation'):
    ref = trace[name]
    assert sha(base/ref['path']) == ref['sha256']
for suffix in ('a', 'b'):
    folder = base/('composed-intent-termination-20261019'+suffix)
    for row in read(folder/'native-retention.json'):
        assert sha(folder/row['binary']) == row['binary_sha256']
for path in (root/'tests/thesis_lite/maestro/test_composed_persistence_termination.py',
             root/'tests/thesis_lite/maestro/catalog_workload_leader_descendant.c'):
    assert all(line.rstrip() == line for line in path.read_text().splitlines())
result = dict(checker_sha256=sha(Path(__file__)), source_and_test_frozen_files_unchanged=len(frozen),
    draft_input_bindings_unchanged=len(inputs['inputs']), capa_records=len(capa['records']),
    capa_evidence_bindings=len(capa['evidence']), partial_requirement_rows=24,
    trace_sha256=sha(trace_path), latest_capa_sha256=sha(base/'capa-20261019-intent-termination/register.json'),
    full_increment17_complete=False, accepted=False, merged=False)
with (base/'composed-intent-termination-work-products-check.json').open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(result))
