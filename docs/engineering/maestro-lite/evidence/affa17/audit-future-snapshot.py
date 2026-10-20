"""Audit exact frozen admission inputs, including the failed installed case."""
from pathlib import Path
import hashlib
import json
import re

OUT=Path(__file__).resolve().parent
CANDIDATE=OUT.parents[4]
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=read(OUT/'future-v1-running.json');ROOT=Path(run['frozen_source_root'])
frozen=read(OUT/'future-v1-frozen-inputs.json')
assert all(sha(ROOT/n)==h for n,h in frozen.items())
identity=read(OUT/'future-v1-installed-identity.json');assert len(identity)==31
for name,row in identity.items():
    assert sha(Path(row['file']))==row['sha256']==sha(ROOT/'src/xverse/maestro'/name)
regression=read(OUT/'future-v1-regression.json')
assert [r['returncode'] for r in regression['receipts']]==[0,1]
for phase,expected in [('source','550 passed'),('wheel','1 failed, 549 passed')]:
    receipt=read(OUT/('future-v1-'+phase+'-receipt.json'))
    assert receipt['log_sha256']==sha(OUT/('future-v1-'+phase+'.log'))
    assert receipt['public_capture_returncode']==0
    assert expected in (OUT/('future-v1-'+phase+'.log')).read_text()
assert re.findall(r'^FAILED (.+)$',(OUT/'future-v1-wheel.log').read_text(),re.M)==[
    'tests/thesis_lite/maestro/test_dispatcher.py::test_unexpected_effect_failure_records_honest_dispositions_and_cleanup']
roots=[];waits=[];public=[]
for phase in ['source','wheel']:
    directory=OUT/('future-v1-'+phase+'-harness')
    for p in directory.glob('maestro-component-*.json'):
        facts=read(p)
        assert facts['root_removed'] and facts['workers_reaped']
        assert not (Path(facts['parent_path'])/facts['root_name']).exists()
        roots.append(dict(receipt=str(p.relative_to(OUT)),sha256=sha(p),root_absent=True))
    for p in directory.glob('run-broker-waits-*.json'):
        facts=read(p)
        assert facts['bootstrap_reaped'] and facts['registered_helpers_reaped'] and facts['storage_reaped']
        assert facts['original_C1_released'] and facts['helper_count'] in (1,2)
        waits.append(dict(receipt=str(p.relative_to(OUT)),sha256=sha(p),facts=facts))
    rows=read(OUT/('future-v1-'+phase+'-public-evidence-index.json'))
    for row in rows:assert sha(OUT/row['snapshot'])==row['sha256']
    public.extend(rows)
assert len(roots)==700 and len(waits)==56 and len(public)==56
assert not any(any(g['source']=='original fixture' for g in row['reader_gaps']) for row in public)
trace=CANDIDATE/'docs/engineering/maestro-lite/evidence/recovery16/traceability.json'
parent=read(trace)
assert len(parent['requirements'])==24 and len(parent['source_parent_register']['requirements'])==18
result=dict(revision='ML3-AFFA17-2026-10-18-future-admission-v1-frozen-component',
    actual_terminal_session=22317,frozen_source_root=str(ROOT),source_manifest_sha256=sha(OUT/'future-v1-frozen-inputs.json'),
    tested_inputs_archive_sha256=sha(OUT/'future-v1-tested-inputs.tar.gz'),
    source_checks_passed=550,installed_wheel_checks_passed=549,installed_wheel_checks_failed=1,
    affected_regression_passed=False,installed_identity_sha256=sha(OUT/'future-v1-installed-identity.json'),
    wheel_sha256=regression['wheel_sha256'],owned_roots_absent=len(roots),root_receipts=roots,
    broker_helper_wait_receipts=waits,public_snapshots=len(public),
    actual_public_source_hash_links_verified=sum(r['source_links'] for r in public),
    snapshots_with_evidence_gaps=sum(bool(r['reader_gaps']) for r in public),original_fixtures_lost=0,
    actual_future_context_admission=True,actual_successor_permit_consumption=False,
    actual_native_restart=False,all_requirements_retained=24,source_parents_retained=18,
    scenario_pairs_retained=30,endpoints_retained=90,full_runtime_cases_retained=9,
    parent_trace_sha256=sha(trace),full_M1_complete=False,full_phase3_complete=False,
    U7_U8_complete=False,full_platform_regression=False,stable_increment17=False,
    accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False)
(OUT/'future-admission-snapshot-attempt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['source_checks_passed','installed_wheel_checks_passed','installed_wheel_checks_failed','owned_roots_absent','public_snapshots','actual_public_source_hash_links_verified','original_fixtures_lost']}))
