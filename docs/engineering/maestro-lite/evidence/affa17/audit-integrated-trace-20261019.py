"""Reconcile historical requirement references with a frozen candidate, read-only."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
root = base.parents[4]
out = base / 'integrated-maestro-20261019a'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
manifest = read(out / 'frozen-inputs.json')
frozen = Path(read(out / 'running.json')['frozen_source_root'])
assert all(sha(frozen / n) == digest for n, digest in manifest.items())
collection = read(out / 'collection-receipt.json')
assert sha(out / 'collected.log') == collection['log_sha256']
cases = [line for line in (out / 'collected.log').read_text().splitlines() if '::' in line]
assert len(cases) == len(set(cases)) == collection['collected'] == 1495
source_inventory = read(out / 'source-terminal-failure-inventory.json')
assert source_inventory['source_failed'] == 2 and source_inventory['source_passed'] == 1493
assert source_inventory['source_log_sha256'] == sha(out / 'maestro_full-source.log')
assert source_inventory['source_receipt_sha256'] == sha(out / 'maestro_full-source-receipt.json')
failed = {item['test'] for item in source_inventory['source_failures']}
assert failed <= set(cases)

def resolve_parent(current, parent):
    path = Path(parent['path'])
    choices = [path] if path.is_absolute() else [root / path, current.parent / path, base / path]
    actual = {p.resolve() for p in choices if p.is_file() and sha(p) == parent['sha256']}
    assert len(actual) == 1, (str(current), parent)
    return actual.pop()

head = base / 'runtime-pending-stop-partial-traceability.json'
chain, seen, references = [], set(), {}
requirements = {}
path = head
while path not in seen:
    seen.add(path)
    data = read(path)
    assert len(data['requirements']) == 24
    chain.append(dict(path=str(path.relative_to(root)), sha256=sha(path)))
    for row in data['requirements']:
        req = row['id']
        requirements.setdefault(req, dict(id=req, feature_parents=row['feature_parents'],
            endpoints=[], full_requirement_closure=False))
        groups = [row, *row.get('component_deltas', [])]
        for group in groups:
            for role, key in [('code', 'code'), ('test', 'tests'), ('test', 'verification')]:
                for item in group.get(key, []):
                    if not isinstance(item, dict) or 'endpoint' not in item:
                        continue
                    identity = req, role, item['endpoint']
                    record = references.setdefault(identity, dict(requirement=req, role=role,
                        endpoint=item['endpoint'], historical_references=[]))
                    record['historical_references'].append(dict(trace=str(path.relative_to(root)),
                        trace_sha256=sha(path), declared_file_sha256=item.get('file_sha256'),
                        declared_line=item.get('line'), frozen_manifest=item.get('frozen_manifest')))
    parent = data.get('parent_trace')
    if parent is None:
        break
    assert isinstance(parent, dict)
    path = resolve_parent(path, parent)
else:
    raise AssertionError('cyclic historical trace')
assert len(chain) == 26 and set(requirements) == {'ML-SR-' + str(n).zfill(3) for n in range(1, 25)}

trees = {}
reverse = {}
for (_, _, endpoint), record in sorted(references.items()):
    file, separator, name = endpoint.partition('::')
    current_sha = manifest.get(file)
    record['current_frozen_file_sha256'] = current_sha
    record['present_in_frozen_inventory'] = current_sha is not None
    record['historical_file_identities'] = sorted({r['declared_file_sha256']
        for r in record['historical_references'] if r['declared_file_sha256'] is not None})
    record['has_exact_current_file_reference'] = current_sha is not None and current_sha in record['historical_file_identities']
    record['current_endpoint_resolves'] = None
    record['current_line'] = None
    if separator and current_sha is not None and file.endswith('.py'):
        scope = trees.setdefault(file, ast.parse((frozen / file).read_text()))
        for part in name.split('.'):
            scope = next((node for node in getattr(scope, 'body', []) if isinstance(node,
                (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == part), None)
            if scope is None:
                break
        record['current_endpoint_resolves'] = scope is not None
        if scope is not None:
            record['current_line'] = scope.lineno
    record['current_collected_cases'] = []
    if record['role'] == 'test':
        prefix = file + '::' + name.replace('.', '::')
        record['current_collected_cases'] = [case for case in cases if case == prefix or case.startswith(prefix + '[')]
    record['original_source_failed_cases'] = sorted(failed & set(record['current_collected_cases']))
    record['current_semantic_mapping_revalidated'] = False
    requirements[record['requirement']]['endpoints'].append(record)
    reverse.setdefault(endpoint, set()).add(record['requirement'])

counts = Counter()
for record in references.values():
    counts['requirement_endpoint_links'] += 1
    counts['code_links' if record['role'] == 'code' else 'test_links'] += 1
    if not record['present_in_frozen_inventory']:
        counts['links_to_files_outside_frozen_inventory'] += 1
    elif record['current_endpoint_resolves'] is False:
        counts['links_with_missing_current_python_endpoint'] += 1
    elif record['current_endpoint_resolves'] is None:
        counts['links_without_python_endpoint_analysis'] += 1
    if not record['has_exact_current_file_reference']:
        counts['links_without_exact_current_file_reference'] += 1
    if record['role'] == 'test' and not record['current_collected_cases']:
        counts['test_links_without_current_collection_match'] += 1

result = dict(auditor_sha256=sha(Path(__file__)), scope='historical structural reconciliation only',
    head_trace_sha256=sha(head), frozen_manifest_sha256=sha(out / 'frozen-inputs.json'),
    original_collection_sha256=sha(out / 'collection-receipt.json'),
    source_failure_inventory_sha256=sha(out / 'source-terminal-failure-inventory.json'),
    chain=chain, requirements=list(requirements.values()),
    reverse_endpoint_requirements={key: sorted(value) for key, value in sorted(reverse.items())},
    counts=dict(counts), unique_endpoints=len(reverse), source_original_passed=1493,
    source_original_failed=2, wheel_terminal_receipt_present=(out / 'maestro_full-wheel-receipt.json').exists(),
    current_semantic_mappings_revalidated=False, full_requirements_closed=False,
    source_parent_semantics_validated=False, complete_runtime_cases_proven=False,
    native_execution_repeated=False, actual_M1_admissions=0, stable_increment17=False,
    accepted=False, merged=False)
with (out / 'trace-reconciliation-source-checkpoint.json').open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(chain_length=len(chain), requirements=len(requirements),
    unique_endpoints=len(reverse), counts=dict(counts), current_semantic_mappings_revalidated=False)))
