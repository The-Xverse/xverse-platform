"""Classify structural trace observations without selecting semantic replacements."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
out = base / 'integrated-maestro-20261019a'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
audit_path = out / 'trace-reconciliation-source-checkpoint.json'
audit = read(audit_path)
manifest = read(out / 'frozen-inputs.json')
assert sha(out / 'frozen-inputs.json') == audit['frozen_manifest_sha256']
frozen = Path(read(out / 'running.json')['frozen_source_root'])
assert all(sha(frozen / n) == digest for n, digest in manifest.items())
definitions = {}

class Index(ast.NodeVisitor):
    def __init__(self):
        self.scope, self.nodes, self.constants = [], {}, set()

    def visit_ClassDef(self, node):
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node):
        name = '.'.join([*self.scope, node.name])
        self.nodes[name] = node
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Assign(self, node):
        if not self.scope:
            self.constants.update(t.id for t in node.targets if isinstance(t, ast.Name))
        self.generic_visit(node)

def index(file):
    if file not in definitions:
        result = Index()
        result.visit(ast.parse((frozen / file).read_text()))
        definitions[file] = result
    return definitions[file]

records = {}
for row in audit['requirements']:
    for original in row['endpoints']:
        key = original['role'], original['endpoint']
        if key in records:
            records[key]['requirements'].append(row['id'])
            continue
        role, endpoint = key
        file, _, name = endpoint.partition('::')
        record = dict(role=role, endpoint=endpoint, requirements=[row['id']],
            exact_current_definition_candidates=[], semantic_replacement_selected=False,
            current_collected_cases=original['current_collected_cases'],
            original_source_failed_cases=original['original_source_failed_cases'])
        if file not in manifest:
            record['kind'] = 'outside_this_maestro_regression_inventory'
        elif not file.endswith('.py'):
            record['kind'] = 'non_python_source_reference'
        else:
            indexed = index(file)
            candidates = ([name] if name in indexed.nodes else
                [n for n in indexed.nodes if '.' not in name and n.rsplit('.', 1)[-1] == name])
            for candidate in sorted(candidates):
                node = indexed.nodes[candidate]
                record['exact_current_definition_candidates'].append(dict(
                    endpoint=file + '::' + candidate, line=node.lineno,
                    end_line=node.end_lineno, file_sha256=manifest[file]))
            if name in indexed.nodes:
                record['kind'] = 'exact_qualified_python_callable'
            elif len(candidates) == 1:
                record['kind'] = 'unqualified_historical_name_with_one_current_candidate'
            elif candidates:
                record['kind'] = 'unqualified_historical_name_with_multiple_current_candidates'
            elif all(part in indexed.constants for part in name.split('/')):
                record['kind'] = 'embedded_source_template_constants'
            else:
                record['kind'] = 'no_current_callable_or_template_candidate'
            if role == 'test' and candidates and not original['current_collected_cases']:
                record['support_kind'] = 'python_fixture_or_helper_not_a_collected_test'
        if role == 'test' and original['current_collected_cases']:
            record['support_kind'] = 'collected_test_function'
        records[key] = record

counts = Counter(record['kind'] for record in records.values())
uncollected = [r for r in records.values() if r['role'] == 'test' and not r['current_collected_cases']]
result = dict(classifier_sha256=sha(Path(__file__)), input_audit_sha256=sha(audit_path),
    scope='current structural candidates and support types only',
    records=list(records.values()), unique_role_endpoint_references=len(records),
    unique_endpoints=len({r['endpoint'] for r in records.values()}), classifications=dict(counts),
    test_role_without_collection_match=uncollected,
    semantic_replacements_selected=False, current_requirement_mapping_revalidated=False,
    missing_implementations_inferred=False, missing_tests_inferred=False,
    full_requirements_closed=False, native_execution_repeated=False,
    actual_M1_admissions=0, stable_increment17=False, accepted=False, merged=False)
with (out / 'trace-reference-classification-source-checkpoint.json').open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(unique_role_endpoint_references=len(records), classifications=dict(counts),
    test_support_references_without_collection_match=len(uncollected), semantic_replacements_selected=False)))
