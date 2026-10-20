"""Bind the bounded control refinement without closing full requirements."""
import ast
import copy
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
candidate = base.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
parent = base / 'active-controller-recovery-verified-scope-traceability.json'
prior = read(parent)
out = base / 'active-control-deadlines-20261019c'
verified = read(out / 'verification.json')
frozen = read(out / 'frozen-inputs.json')
root = Path(read(out / 'running.json')['frozen_source_root'])
assert all(sha(root / n) == h == sha(candidate / n) for n, h in frozen.items())
def ref(p):
    return dict(path=str(p.relative_to(base)), sha256=sha(p))

def endpoint(path, name):
    nodes = ast.parse((root / path).read_text()).body
    parts = name.split('.')
    for part in parts:
        node = next(n for n in nodes if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == part)
        nodes = node.body
    return dict(endpoint=path + '::' + name, line=node.lineno, file_sha256=frozen[path],
        frozen_manifest='active-control-deadlines-20261019c/frozen-inputs.json')

code = [endpoint('src/xverse/maestro/dispatcher.py', 'FiniteDispatcher.' + name)
    for name in ('restart_many', 'restart_result', '_drain_restart', 'replace_controller',
                 'controller_recovery_result', '_drain_controller_recovery', '_close_restarts', 'cancel')]
tests = [endpoint('tests/thesis_lite/maestro/test_active_control_deadlines.py',
    'test_original_control_rejection_keeps_unspent_authority')]
ids = ['ML-SR-006', 'ML-SR-009', 'ML-SR-010', 'ML-SR-011', 'ML-SR-014', 'ML-SR-018', 'ML-SR-023', 'ML-SR-024']
requirements = copy.deepcopy(prior['requirements'])
reverse = copy.deepcopy(prior['reverse_endpoint_requirements'])
for row in requirements:
    assert not row['full_requirement_closure']
    if row['id'] in ids:
        row['component_deltas'].append(dict(maturity='partial_verified_active_control_rejection',
            code=code, tests=tests, evidence=ref(out / 'verification.json'), full_requirement_closure=False,
            scope='Ten exact native deadline/cancellation contexts per phase; no universal timing, epoch-race or recovery claim'))
for item in code + tests:
    reverse.setdefault(item['endpoint'], [])
    reverse[item['endpoint']] = sorted(set(reverse[item['endpoint']]) | set(ids))
result = dict(schema_version=1, revision='ML3-AFFA17-2026-10-19-active-control-deadlines-v1',
    scope='Rejected untouched expired/cancelled control requests; complete increment17 remains open',
    parent_trace=ref(parent), inherited_claims_apply_only_to_their_exact_frozen_inputs=True,
    requirements=requirements, source_parent_register=prior['source_parent_register'],
    reverse_endpoint_requirements=reverse, evidence=ref(out / 'verification.json'),
    original_counterexample=ref(base / 'active-control-deadlines-20261019b/counterexample-verification.json'),
    software_requirements_retained=24, source_parents_retained=18, scenario_pairs_retained=30,
    endpoint_obligations_retained=90, full_runtime_cases_retained=9,
    current_affected_counts=verified['phases'], normal_retained_closed_public_roots=16,
    original_root_receipts=len(verified['original_root_receipts']), original_wait_receipts=len(verified['original_wait_receipts']),
    source_links=verified['source_links'], open_findings=[135, 222],
    component_finding_dispositions={'236':'addressed_in_bounded_contexts', '237':'fixture_wiring_corrected',
        '238':'verified_preflight_classification_repair', '239':'original_failed_evidence_preserved_actual_ends_retained'},
    remaining_gates=prior['remaining_gates'], source_parent_semantics_validated=False,
    full_source_wheel_scope_passed=False, full_M1_complete=False, whole_platform_regression=False,
    full_candidate_review_complete=False, all_seven_phase3_tasks_complete=False,
    stable_increment17=False, accepted=False, merged=False, canonical_note_edited=False, factory_run_created=False)
assert len(result['requirements']) == 24
path = base / 'active-control-deadlines-partial-traceability.json'
with path.open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(path=str(path), sha256=sha(path), requirements=len(requirements))))
