"""Audit exact retained component facts without promoting full requirements."""
from pathlib import Path
import ast
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
inputs = read(OUT/'component-v4-inputs.json')
assert all(sha(ROOT/n)==h for n,h in inputs.items())
wheel = read(OUT/'component-v5-wheel-receipt.json')
assert wheel['returncode'] == 0 and wheel['log_sha256'] == sha(OUT/'component-v5-wheel.log')
assert all(sha(ROOT/n)==h for n,h in wheel['input_sha256'].items())
for row in list(wheel['installed_modules'].values())+list(wheel['installed_native_resources'].values()):
    assert sha(Path(row['file'])) == row['sha256']
# Capture the original red bootstrap fixtures that used pytest's default receipt dir.
# Retain only the exact initial log's closed-time window and its five node prefixes.
red = OUT/'bootstrap-native-red.log'
recovered = OUT/'bootstrap-initial-red-harness'
recovered.mkdir(exist_ok=True)
low,high = red.stat().st_mtime-10, red.stat().st_mtime+1
originals = []
for p in Path('/tmp/pytest-of-jefferson').glob('pytest-*/test_*/maestro-component-*.json'):
    if low <= p.stat().st_mtime <= high:
        target = recovered/p.name
        if not target.exists():
            shutil.copyfile(p,target)
        originals.append(dict(original=str(p),retained=str(target.relative_to(ROOT)),sha256=sha(p)))
(OUT/'bootstrap-initial-red-receipt-recovery.json').write_text(json.dumps(originals,indent=2)+'\n')
roots,waits,standalone = [],[],[]
for directory in sorted(OUT.glob('*harness')):
    for p in sorted(directory.glob('maestro-component-*.json')):
        data = read(p)
        assert data['root_removed'] and data['workers_reaped'], str(p)
        actual = Path(data['parent_path'])/data['root_name']
        assert not actual.exists(), str(actual)
        roots.append(dict(receipt=str(p.relative_to(ROOT)),sha256=sha(p),root_absent=True))
    for p in sorted(directory.glob('run-bootstrap-waits-*.json')):
        data = read(p)
        result = data['bootstrap_drain']
        assert result['supervisor_reaped'] and result['registered_children_reaped']
        assert data['original_helpers_actually_reaped'] and data['all_original_C1_released']
        waits.append(dict(receipt=str(p.relative_to(ROOT)),sha256=sha(p),
            helpers_reaped=data['original_helper_count'],unacknowledged_births=result['unacknowledged_births'],
            native_final_freeze_acknowledged=result['final_workload_freeze_acknowledged']))
    for p in sorted(directory.glob('affa-standalone-reaped-*.json')):
        data=read(p)
        assert data['authority_reaped'], str(p)
        standalone.append(dict(receipt=str(p.relative_to(ROOT)),sha256=sha(p),facts=data))
current_dirs={'component-v5-source-harness','component-v5-wheel-harness'}
current_roots=[r for r in roots if Path(r['receipt']).parent.name in current_dirs]
current_waits=[r for r in waits if Path(r['receipt']).parent.name in current_dirs]
assert len(current_roots)==152 and len(current_waits)==60
# All24 requirements and all18 parents remain binding. Add delta endpoints, do not
# rewrite historical verification as a current full-platform run.
parent=ROOT/'docs/engineering/maestro-lite/evidence/recovery16/traceability.json'
trace=read(parent)
code=['src/xverse/maestro/'+n for n in ['affa_protocol.py','affa_client.py','bootstrap.py','native/bootstrap.c','native/run_authority.c']]
tests=['tests/thesis_lite/maestro/'+n for n in ['test_affa_protocol.py','test_affa_config.py','test_affa_native.py','test_run_bootstrap_values.py','test_run_bootstrap.py','test_affa_client.py','test_bootstrap.py']]
assert len(trace['requirements'])==24 and len(trace['source_parent_register']['requirements'])==18
partial={'ML-SR-%03d'%n for n in [5,6,7,8,9,10,11,12,13,14,16,17,18,19,20,22,23,24]}
rows=[]
for r in trace['requirements']:
    assert not r['full_requirement_closure']
    rows.append(dict(id=r['id'],status='partial_component_evidence' if r['id'] in partial else 'inherited_open',
        full_requirement_closure=False,new_code=code if r['id'] in partial else [],
        new_component_checks=tests if r['id'] in partial else []))
result=dict(revision='ML3-AFFA17-2026-10-18-bootstrap-client-component-v5',
    parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    source_terminal_session=71797,source_returncode=0,source_checks=137,
    wheel_terminal_session=52389,wheel_returncode=0,wheel_checks=137,
    source_log_sha256=sha(OUT/'component-v5-source.log'),wheel_log_sha256=sha(OUT/'component-v5-wheel.log'),
    input_sha256=wheel['input_sha256'],installed_maestro_modules=len(wheel['installed_modules']),
    installed_native_resources=len(wheel['installed_native_resources']),current_owned_roots_absent=len(current_roots),
    current_bootstrap_supervisors_reaped=len(current_waits),
    current_original_AFFA_helpers_reaped=sum(r['helpers_reaped'] for r in current_waits),
    current_unacknowledged_births=sum(r['unacknowledged_births'] for r in current_waits),
    current_standalone_authorities_reaped=sum(Path(r['receipt']).parent.name in current_dirs for r in standalone),
    initial_red_default_root_receipts_missing=5,
    all_history_root_absence_proven=False,
    all_retained_root_receipts_audited=len(roots),all_retained_roots=roots,bootstrap_wait_receipts=waits,
    standalone_receipts=standalone,requirements=rows,parent_trace_sha256=sha(parent),
    source_parents=trace['source_parent_register'],
    direct_workload_waits_not_proven_by_bootstrap=True,
    actual_M3_Argus_broker_integration=False,authenticated_C1_epoch_bridge=False,
    controller_replacement_integration=False,process_mode_admission=False,
    full_platform_regression=False,full_M1_complete=False,full_phase3_complete=False,
    independent_full_candidate_review=False,accepted=False,merged=False,
    canonical_note_edited=False,factory_run_created=False,stable_increment17=False)
(OUT/'bootstrap-client-component-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['source_checks','wheel_checks','current_owned_roots_absent',
    'current_bootstrap_supervisors_reaped','current_original_AFFA_helpers_reaped','current_unacknowledged_births',
    'all_retained_root_receipts_audited','stable_increment17']}))
