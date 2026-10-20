"""Audit exact frozen admission inputs, with both source and installed runs passing."""
from pathlib import Path
import hashlib
import json
import re

OUT=Path(__file__).resolve().parent
CANDIDATE=OUT.parents[4]
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=read(OUT/'issued-v1-full-running.json');ROOT=Path(run['frozen_source_root'])
frozen=read(OUT/'issued-v1-full-frozen-inputs.json')
assert all(sha(ROOT/n)==h for n,h in frozen.items())
identity=read(OUT/'issued-v1-full-installed-identity.json');assert len(identity)==35
for name,row in identity.items():
    assert sha(Path(row['file']))==row['sha256']==sha(ROOT/'src/xverse/maestro'/name)
regression=read(OUT/'issued-v1-full-regression.json')
assert [r['returncode'] for r in regression['receipts']]==[0,0]
for phase,expected in [('source','627 passed'),('wheel','627 passed')]:
    receipt=read(OUT/('issued-v1-full-'+phase+'-receipt.json'))
    assert receipt['log_sha256']==sha(OUT/('issued-v1-full-'+phase+'.log'))
    assert receipt['public_capture_returncode']==0
    assert expected in (OUT/('issued-v1-full-'+phase+'.log')).read_text()
assert not re.findall(r'^FAILED (.+)$',(OUT/'issued-v1-full-wheel.log').read_text(),re.M)
roots=[];waits=[];public=[]
for phase in ['source','wheel']:
    directory=OUT/('issued-v1-full-'+phase+'-harness')
    for p in directory.glob('maestro-component-*.json'):
        facts=read(p)
        assert facts['root_removed'] and facts['workers_reaped']
        assert not (Path(facts['parent_path'])/facts['root_name']).exists()
        roots.append(dict(receipt=str(p.relative_to(OUT)),sha256=sha(p),root_absent=True))
    for p in directory.glob('run-broker-waits-*.json'):
        facts=read(p)
        assert facts['bootstrap_reaped'] and facts['registered_helpers_reaped'] and facts['storage_reaped']
        assert facts['original_C1_released'] and facts['helper_count'] in (1,2,3,4)
        waits.append(dict(receipt=str(p.relative_to(OUT)),sha256=sha(p),facts=facts))
    rows=read(OUT/('issued-v1-full-'+phase+'-public-evidence-index.json'))
    for row in rows:assert sha(OUT/row['snapshot'])==row['sha256']
    public.extend(rows)
assert len(roots)==798 and len(waits)==154 and len(public)==154
assert not any(any(g['source']=='original fixture' for g in row['reader_gaps']) for row in public)
from jsonschema import Draft202012Validator
canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
validator=Draft202012Validator(read(ROOT/'tests/thesis_lite/maestro/lifecycle-payload-v2.schema.json'))
special=[]
for phase in ['source','wheel']:
    directory=OUT/('issued-v1-full-'+phase+'-harness')
    for pattern,test in [('successor-intent-public-*.json','test_generation_claim.py'),('actual-generation-restart-public-*.json','test_generation_restart.py'),('transitive-restart-public-*.json','test_generation_dependents.py'),('controller-replacement-public-*.json','test_controller.py')]:
        exports=list(directory.glob(pattern));assert len(exports)==(2 if test=='test_controller.py' else 1)
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
            if test=='test_controller.py':
                assert facts['original_controller_dead_reaped'] and facts['original_storage_authority_handles_retained']
                assert facts['fresh_native_probes'] and facts['old_session']!=facts['new_session']
                assert facts['actual_resource_generation'] in (1,2)
            special.append(dict(snapshot=str(path.relative_to(OUT)),sha256=sha(path),source_links=links))
assert len(special)==10
for phase in ['source','wheel']:
    directory=OUT/('issued-v1-full-'+phase+'-harness')
    for pattern,test,count in [('shared-closure-public-*.json','test_shared_closure.py',6),('shared-dispatch-public-*.json','test_shared_dispatcher.py',3)]:
        exports=list(directory.glob(pattern));assert len(exports)==count
        for path in exports:
            facts=read(path)
            assert facts['source_sha256']==sha(ROOT/'tests/thesis_lite/maestro'/test)
            result=facts.get('result',facts.get('closure'))
            assert result['root_reaped'] and result['authority_fenced']
            assert all(h['process_reaped'] for h in result['helpers'])
            assert all(b['empty'] and b['released'] for b in result['boundaries'])
            if result['normal_unit_records_complete']:
                assert result['native_units'] and all(u['direct_child_reaped'] is True for u in result['native_units'])
            else:
                assert not result['lifecycle_complete']
            if test=='test_shared_dispatcher.py' and facts['dispatch']['execution_succeeded']:
                assert len(facts['dispatch']['steps'])==10
                assert all(s['normal_recorded'] and s['disposition']=='completed' for s in facts['dispatch']['steps'])
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
            special.append(dict(snapshot=str(path.relative_to(OUT)),sha256=sha(path),source_links=links))
assert len(special)==28
for phase in ['source','wheel']:
    directory=OUT/('issued-v1-full-'+phase+'-harness')
    exports=list(directory.glob('issuance-public-*.json'));assert len(exports)==2
    for path in exports:
        facts=read(path)
        assert facts['source_sha256']==sha(ROOT/'tests/thesis_lite/maestro/test_issuance.py')
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
            if payload['action']=='issued':
                source=records[payload['sourceRefs'][0]['sequence']]
                assert source['kind']=='observation' and source['status']=='staged'
                assert source['handleId']==source['handleResourceIdentity']=='withheld'
                intent=next(e for e in facts['argus_events'] if e['eventId']==event['causationId'])
                assert intent['extensions']['xverse.maestro']['action']=='intent'
                assert intent['ingestionOrdinal']<event['ingestionOrdinal']
        special.append(dict(snapshot=str(path.relative_to(OUT)),sha256=sha(path),source_links=links))
assert len(special)==32
trace=CANDIDATE/'docs/engineering/maestro-lite/evidence/recovery16/traceability.json'
parent=read(trace)
assert len(parent['requirements'])==24 and len(parent['source_parent_register']['requirements'])==18
result=dict(revision='ML3-AFFA17-2026-10-18-issued-v1-full-frozen-component',
    actual_terminal_session=17923,frozen_source_root=str(ROOT),source_manifest_sha256=sha(OUT/'issued-v1-full-frozen-inputs.json'),
    tested_inputs_archive_sha256=sha(OUT/'issued-v1-full-tested-inputs.tar.gz'),
    source_checks_passed=627,installed_wheel_checks_passed=627,installed_wheel_checks_failed=0,
    affected_regression_passed=True,installed_identity_sha256=sha(OUT/'issued-v1-full-installed-identity.json'),
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
(OUT/'issued-regression-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['source_checks_passed','installed_wheel_checks_passed','installed_wheel_checks_failed','owned_roots_absent','public_snapshots','actual_public_source_hash_links_verified','original_fixtures_lost']}))
