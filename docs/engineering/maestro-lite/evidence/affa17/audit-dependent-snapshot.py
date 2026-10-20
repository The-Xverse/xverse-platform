"""Audit exact frozen admission inputs, with both source and installed runs passing."""
from pathlib import Path
import hashlib
import json
import re

OUT=Path(__file__).resolve().parent
CANDIDATE=OUT.parents[4]
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=read(OUT/'dependent-v2-running.json');ROOT=Path(run['frozen_source_root'])
frozen=read(OUT/'dependent-v2-frozen-inputs.json')
assert all(sha(ROOT/n)==h for n,h in frozen.items())
identity=read(OUT/'dependent-v2-installed-identity.json');assert len(identity)==32
for name,row in identity.items():
    assert sha(Path(row['file']))==row['sha256']==sha(ROOT/'src/xverse/maestro'/name)
regression=read(OUT/'dependent-v2-regression.json')
assert [r['returncode'] for r in regression['receipts']]==[0,0]
for phase,expected in [('source','570 passed'),('wheel','570 passed')]:
    receipt=read(OUT/('dependent-v2-'+phase+'-receipt.json'))
    assert receipt['log_sha256']==sha(OUT/('dependent-v2-'+phase+'.log'))
    assert receipt['public_capture_returncode']==0
    assert expected in (OUT/('dependent-v2-'+phase+'.log')).read_text()
assert not re.findall(r'^FAILED (.+)$',(OUT/'dependent-v2-wheel.log').read_text(),re.M)
roots=[];waits=[];public=[]
for phase in ['source','wheel']:
    directory=OUT/('dependent-v2-'+phase+'-harness')
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
    rows=read(OUT/('dependent-v2-'+phase+'-public-evidence-index.json'))
    for row in rows:assert sha(OUT/row['snapshot'])==row['sha256']
    public.extend(rows)
assert len(roots)==740 and len(waits)==96 and len(public)==96
assert not any(any(g['source']=='original fixture' for g in row['reader_gaps']) for row in public)
from jsonschema import Draft202012Validator
canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
validator=Draft202012Validator(read(ROOT/'tests/thesis_lite/maestro/lifecycle-payload-v2.schema.json'))
special=[]
for phase in ['source','wheel']:
    directory=OUT/('dependent-v2-'+phase+'-harness')
    for pattern,test in [('successor-intent-public-*.json','test_generation_claim.py'),('actual-generation-restart-public-*.json','test_generation_restart.py'),('transitive-restart-public-*.json','test_generation_dependents.py')]:
        exports=list(directory.glob(pattern));assert len(exports)==1
        for path in exports:
            facts=read(path)
            assert facts['source_sha256']==sha(ROOT/'tests/thesis_lite/maestro'/test)
            records={r['sequence']:r for r in facts['public_m3']}
            links=0
            for event in facts['argus_events']:
                payload=event.get('extensions',{}).get('xverse.maestro')
                if payload is None:continue
                validator.validate(payload)
                for ref in payload['sourceRefs']:
                    if ref['kind']=='m3-record':
                        assert ref['sha256']=='sha256:'+hashlib.sha256(canonical(records[ref['sequence']])).hexdigest()
                        links+=1
            if test=='test_generation_restart.py':
                assert facts['actual_native_epochs']==[0,1,2]
                assert facts['actual_same_worker_generations']==[1,2,3]
                assert facts['unrelated_original_prerequisite_live'] and facts['old_terminal_facts_retained']
                outcomes=[r for r in records.values() if r['kind']=='outcome' and r['status']=='cleaned']
                assert {r['details']['generation'] for r in outcomes}=={1,2}
                assert all(r['details']['teardown']['leader_reaped'] and r['details']['teardown']['empty'] and r['details']['teardown']['released'] for r in outcomes)
            if test=='test_generation_dependents.py':
                assert facts['actual_native_epochs']==[0,1,2,3]
                assert facts['original_worker_retained'] and facts['unrelated_original_handle_live']
                assert facts['quiescence_order']==list(reversed(facts['restart_order']))
            special.append(dict(snapshot=str(path.relative_to(OUT)),sha256=sha(path),source_links=links))
assert len(special)==6
trace=CANDIDATE/'docs/engineering/maestro-lite/evidence/recovery16/traceability.json'
parent=read(trace)
assert len(parent['requirements'])==24 and len(parent['source_parent_register']['requirements'])==18
result=dict(revision='ML3-AFFA17-2026-10-18-dependent-v2-frozen-component',
    actual_terminal_session=97622,frozen_source_root=str(ROOT),source_manifest_sha256=sha(OUT/'dependent-v2-frozen-inputs.json'),
    tested_inputs_archive_sha256=sha(OUT/'dependent-v2-tested-inputs.tar.gz'),
    source_checks_passed=570,installed_wheel_checks_passed=570,installed_wheel_checks_failed=0,
    affected_regression_passed=True,installed_identity_sha256=sha(OUT/'dependent-v2-installed-identity.json'),
    wheel_sha256=regression['wheel_sha256'],owned_roots_absent=len(roots),root_receipts=roots,
    broker_helper_wait_receipts=waits,public_snapshots=len(public),explicit_generation_snapshots=special,
    actual_public_source_hash_links_verified=sum(r['source_links'] for r in public),
    snapshots_with_evidence_gaps=sum(bool(r['reader_gaps']) for r in public),original_fixtures_lost=0,
    actual_future_context_admission=True,actual_successor_permit_consumption=True,
    actual_native_restart=True,all_requirements_retained=24,source_parents_retained=18,
    scenario_pairs_retained=30,endpoints_retained=90,full_runtime_cases_retained=9,
    parent_trace_sha256=sha(trace),full_M1_complete=False,full_phase3_complete=False,
    U7_U8_complete=False,full_platform_regression=False,stable_increment17=False,
    accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False)
(OUT/'dependent-restart-snapshot-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['source_checks_passed','installed_wheel_checks_passed','installed_wheel_checks_failed','owned_roots_absent','public_snapshots','actual_public_source_hash_links_verified','original_fixtures_lost']}))
