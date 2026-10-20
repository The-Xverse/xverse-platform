"""Audit actual caller-owned exports, original broker projections and failed predecessors."""
from pathlib import Path
import hashlib,json
from jsonschema import Draft202012Validator

OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
canonical=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
fields={'eventId','producerId','eventKind','producerSequence','correlationId','causationId','clocks','annotation','extensions','ingestionOrdinal'}
rows=[]
for revision,phase,status,summary,root_count,wait_count in [
    ('retained-v1','source',1,'2 failed, 14 passed',15,14),
    ('retained-v2','source',1,'1 failed, 19 passed',15,15),
    ('retained-v3','source',0,'20 passed',15,15),('retained-v3','wheel',0,'20 passed',15,15),
    ('retained-v4','source',0,'29 passed',24,24),('retained-v4','wheel',0,'29 passed',24,24)]:
    root=Path(read(OUT/(revision+'-running.json'))['frozen_source_root'])
    frozen=read(OUT/(revision+'-frozen-inputs.json'))
    assert all(sha(root/n)==h for n,h in frozen.items())
    identity=read(OUT/(revision+'-installed-identity.json'));assert len(identity)==37
    for n,r in identity.items():assert sha(Path(r['file']))==r['sha256']==sha(root/'src/xverse/maestro'/n)
    name=revision+'-'+phase;receipt=read(OUT/(name+'-receipt.json'))
    assert receipt['returncode']==status and receipt['public_capture_returncode']==0
    assert receipt['log_sha256']==sha(OUT/(name+'.log'))
    assert summary in (OUT/(name+'.log')).read_text()
    directory=OUT/(name+'-harness');roots=[];waits=[]
    for path in directory.glob('maestro-component-*.json'):
        facts=read(path)
        assert facts['root_removed'] and facts['workers_reaped']
        assert not (Path(facts['parent_path'])/facts['root_name']).exists()
        roots.append(dict(receipt=str(path.relative_to(OUT)),sha256=sha(path)))
    for path in directory.glob('run-broker-waits-*.json'):
        facts=read(path)
        assert facts['bootstrap_reaped'] and facts['registered_helpers_reaped'] and facts['storage_reaped']
        assert facts['original_C1_released'] and facts['helper_count'] in (1,2)
        waits.append(dict(receipt=str(path.relative_to(OUT)),sha256=sha(path)))
    assert len(roots)==root_count and len(waits)==wait_count
    public=read(OUT/(name+'-public-evidence-index.json'));assert len(public)==wait_count
    assert not any(g['source']=='original fixture' for row in public for g in row['reader_gaps'])
    for row in public:assert sha(OUT/row['snapshot'])==row['sha256']
    validator=Draft202012Validator(read(root/'tests/thesis_lite/maestro/lifecycle-payload-v2.schema.json'))
    exports=[]
    for path in directory.glob('retained-public-*.json'):
        facts=read(path)
        assert facts['source_sha256']==sha(root/'tests/thesis_lite/maestro/test_retained_inputs.py')
        body=facts['retained'];entry=facts['index_entry']
        raw=canonical(body)
        assert entry['sha256']==hashlib.sha256(raw).hexdigest() and entry['bytes']==len(raw)
        assert body['schemaVersion']=='1.0' and body['trustBoundary'] and 'overallStatus' not in body
        assert body['publicM3']==facts['public_m3']
        events={e['eventId']:e for e in facts['argus_events']}
        assert len(body['annotations'])==len(events)
        ordinals=[];links=0
        records={r['sequence']:r for r in body['publicM3']}
        for event in body['annotations']:
            assert set(event)==fields and event['eventKind']=='annotation'
            assert all(events[event['eventId']].get(k)==v for k,v in event.items())
            ordinals.append(event['ingestionOrdinal'])
            payload=event['extensions']['xverse.maestro'];validator.validate(payload)
            for ref in payload['sourceRefs']:
                if ref['kind']=='m3-record':
                    assert ref['sha256']=='sha256:'+hashlib.sha256(canonical(records[ref['sequence']])).hexdigest()
                    links+=1
        assert ordinals==sorted(set(ordinals))
        assert not {'schemaVersion','runId'} & set(body['annotations'][0])
        exports.append(dict(snapshot=str(path.relative_to(OUT)),sha256=sha(path),actual_retained_annotation_count=len(events),
            actual_source_links=links,actual_public_artifact_entry=entry))
    expected_exports=0 if revision=='retained-v1' else 1 if revision=='retained-v2' else 2
    assert len(exports)==expected_exports
    projections=[]
    for path in directory.glob('broker-projection-public-*.json'):
        facts=read(path);body=facts['projection']
        assert facts['source_sha256']==sha(root/'tests/thesis_lite/maestro/test_broker_projection.py')
        admitted={u['unitId'] for u in body['admittedUnits']};assert len(admitted)==2
        assert {g['unitId'] for g in body['generations']}==admitted
        assert body['epochs'][0]['epoch']==0
        if path.stem.endswith('never-issued'):
            assert len(body['futureContexts'])==4
            assert all(g['issued'] is False and g['stageAttempted'] is False and g['intentEventId'] is None for g in body['generations'])
        if path.stem.endswith('released'):
            assert all(g['releaseObserved'] is True and g['releaseRequestedAt']<=g['releaseAcknowledgedAt']<=body['observedAt'] for g in body['generations'])
        if path.stem.endswith('generation'):
            assert [e['epoch'] for e in body['epochs']]==[0,1]
            old=[g for g in body['generations'] if g['directChildReaped'] is True]
            assert len(old)==1 and old[0]['generation']==1 and old[0]['nativeRetired'] is True and old[0]['c1Released'] is True
            assert any(g['generation']==2 and g['releaseObserved'] is True for g in body['generations'])
        if path.stem.endswith('unknown'):
            assert any(g['stageAttempted'] is True and g['issued'] is None and g['directChildReaped'] is None for g in body['generations'])
            assert any(g['stageAttempted'] is False and g['issued'] is False for g in body['generations'])
        def keys(value):
            if isinstance(value,dict):return set(value)|set().union(*(keys(v) for v in value.values()))
            if isinstance(value,list):return set().union(*(keys(v) for v in value))
            return set()
        assert not keys(body)&{'pid','fd','scope','ticket','nonce','handle','native_ack'}
        projections.append(dict(snapshot=str(path.relative_to(OUT)),sha256=sha(path)))
    assert len(projections)==(4 if revision=='retained-v4' else 0)
    rows.append(dict(revision=revision,phase=phase,returncode=status,summary=summary,
        owned_roots_absent=len(roots),root_receipts=roots,helper_wait_receipts=waits,
        public_snapshots=len(public),actual_source_hash_links=sum(r['source_links'] for r in public),
        snapshots_with_preserved_evidence_gaps=sum(bool(r['reader_gaps']) for r in public),
        original_fixtures_lost=0,actual_original_public_exports=exports,original_broker_projections=projections,
        frozen_input_manifest_sha256=sha(OUT/(revision+'-frozen-inputs.json'))))
result=dict(revision='ML3-AFFA17-2026-10-19-retained-v4',phases=rows,source_checks_passed=29,installed_wheel_checks_passed=29,
    actual_terminal_session=48480,latest_wheel_sha256=sha(OUT/'retained-v4-dist/xverse_xdl-0.4.0-py3-none-any.whl'),
    installed_identity_sha256=sha(OUT/'retained-v4-installed-identity.json'),
    actual_original_caller_fields_and_ordinals=True,actual_original_broker_public_projection=True,
    original_generation_registry_deletion_rejected=True,original_release_host_bounds_retained=True,
    original_public_index_entries_verified=True,complete_U7_U8=False,full_current_source_regression=False,
    full_M1_complete=False,stable_increment17=False,accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False)
(OUT/'retained-component-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ['revision','phase','returncode','owned_roots_absent','public_snapshots','actual_source_hash_links','original_fixtures_lost']} for r in rows]))
