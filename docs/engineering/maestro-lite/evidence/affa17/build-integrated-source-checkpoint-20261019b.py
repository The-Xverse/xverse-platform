"""Bind the completed current source phase; wheel and all wider gates stay open."""
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
root = base.parents[4]
out = base/'integrated-maestro-20261019b'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
reference = lambda p: dict(path=str(p.relative_to(root)),sha256=sha(p))
receipt_path = out/'maestro_full-source-receipt.json'
audit_path = out/'maestro_full-source-terminal-audit/audit.json'
receipt,audit = read(receipt_path),read(audit_path)
assert receipt['returncode']==audit['original_returncode']==0
assert not receipt['outer_timeout'] and audit['observed_counts']==dict(passed=1501,failed=0,skipped=0,errors=0,xfailed=0,xpassed=0)
assert audit['terminal_receipt_sha256']==sha(receipt_path)
assert len(audit['root_reservations'])==859 and audit['all_recorded_roots_removed_and_workers_reaped']
assert not audit['receipt_parse_errors'] and audit['source_links']==7094
assert audit['projection_reader_gaps']==248 and len(audit['receipt_inventory'])==2973
assert len(audit['public_projections'])==374
assert len(audit['original_input_closed_recomputations'])==64
assert sum(r.get('complete') is True for r in audit['original_input_closed_recomputations'])==8
assert sum(r.get('complete') is False for r in audit['original_input_closed_recomputations'])==56
for item in audit['receipt_inventory']+audit['public_projections']:
    assert sha(out/item['path'])==item['sha256']
for item in audit['root_reservations']:
    assert item['recorded_removed'] and item['recorded_workers_reaped'] and item['actual_path_absent']
manifest = read(out/'frozen-inputs.json')
assert len(manifest)==273 and manifest==read(base/'runtime-disposal-20261019c/frozen-inputs.json')
assert all(sha(root/n)==h for n,h in manifest.items())
old = read(base/'integrated-maestro-20261019a/frozen-inputs.json')
production = {n:h for n,h in manifest.items() if n.startswith('src/') and n.endswith(('.py','.c'))}
changed = sorted(n for n,h in production.items() if old[n]!=h)
assert len(production)==81 and changed==[
    'src/xverse/maestro/persistence.py','src/xverse/maestro/run_broker.py','src/xverse/maestro/run_closure.py']
folder = base/'capa-20261019-runtime-disposal'
capa,validation,preservation = [read(folder/n) for n in ('register.json','verification-recheck.json','parent-preservation.json')]
assert len(capa['records'])==39 and len(capa['evidence'])==210
assert validation['register_sha256']==preservation['register_sha256']==sha(folder/'register.json')
assert preservation['parent_preserved'] and preservation['parent_evidence_bindings_checked']==198
source_proposal = Path('/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/review/source-parent-semantics-proposal-20261019-v2/proposal.json')
assert sha(source_proposal)=='0183f57a7977a3d7ce4021e06ea0dfe56293552a66d910474224a16ce6960caf'
assert not read(source_proposal)['authority']['author_approved']
started = read(out/'maestro_full-wheel-started.json')
assert started['collected']==1501 and started['original_pid']==1449216
result = dict(schema_version=1,checkpoint='current_complete_source_phase_wheel_pending',
    original_driver_exec_session=97867,original_source_pytest_pid=receipt['original_pid'],
    source_terminal_receipt=reference(receipt_path),source_audit=reference(audit_path),
    source_log=reference(out/'maestro_full-source.log'),frozen_inputs=reference(out/'frozen-inputs.json'),
    audit_tool=reference(base/'audit-integrated-maestro-20261019b.py'),
    source_counts=audit['observed_counts'],source_phase_passed=True,
    frozen_input_files=273,packaged_python_c_files=81,changed_from_original_integrated_a=changed,
    other_packaged_sources_unchanged=78,recorded_owned_roots_absent=859,verified_source_links=7094,
    explicit_reader_reference_gaps=248,original_input_closed_recomputations=dict(complete=8,incomplete=56),
    partial_requirement_trace=reference(base/'runtime-disposal-partial-traceability.json'),
    capa_register=reference(folder/'register.json'),capa_validation=reference(folder/'verification-recheck.json'),
    capa_parent_preservation=reference(folder/'parent-preservation.json'),
    source_parent_projection=dict(path=str(source_proposal),sha256=sha(source_proposal),author_approval_recorded=False),
    original_wheel_started_receipt=reference(out/'maestro_full-wheel-started.json'),
    original_wheel_pytest_pid=started['original_pid'],wheel_terminal_receipt_present=(out/'maestro_full-wheel-receipt.json').exists(),
    historical_timeout_causes_unknown=[135,222,286,287,318,324,330,331,332,337],
    preserved_obligations=dict(software_requirements=24,source_parents=18,scenario_pairs=30,declared_endpoints=90,full_runtime_cases=9,full_P3_tasks=7),
    full_maestro_regression_passed=False,whole_platform_regression=False,full_runtime_cases_complete=False,
    actual_M1_admissions=0,independent_complete_review=False,CAPA_effectiveness_demonstrated=False,
    stable_increment17=False,accepted=False,merged=False,canonical_note_edited=False,scientific_result=False)
assert not result['wheel_terminal_receipt_present']
with (out/'source-phase-checkpoint.json').open('x') as stream:
    json.dump(result,stream,indent=2)
    stream.write('\n')
print(json.dumps(dict(source_passed=1501,recorded_owned_roots_absent=859,source_links=7094,
    explicit_gaps=248,wheel_terminal=False,checkpoint_sha256=sha(out/'source-phase-checkpoint.json'))))
