"""Audit actual issuance observations and explicitly retained deletion controls."""
from pathlib import Path
import hashlib
import json
from jsonschema import Draft202012Validator
from xverse.argus.schema import canonical_bytes

OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=read(OUT/'issued-v1-running.json');root=Path(run['frozen_source_root'])
frozen=read(OUT/'issued-v1-frozen-inputs.json')
assert all(sha(root/n)==h for n,h in frozen.items())
identity=read(OUT/'issued-v1-installed-identity.json');assert len(identity)==35
for n,r in identity.items():assert sha(Path(r['file']))==r['sha256']==sha(root/'src/xverse/maestro'/n)
validator=Draft202012Validator(read(root/'tests/thesis_lite/maestro/lifecycle-payload-v2.schema.json'))
phases=[]
for phase in ['source','wheel']:
    name='issued-v1-'+phase
    receipt=read(OUT/(name+'-receipt.json'))
    assert receipt['returncode']==0 and receipt['public_capture_returncode']==0
    assert receipt['log_sha256']==sha(OUT/(name+'.log'))
    assert '6 passed' in (OUT/(name+'.log')).read_text()
    directory=OUT/(name+'-harness')
    roots=[];waits=[]
    for p in directory.glob('maestro-component-*.json'):
        r=read(p);assert r['root_removed'] and r['workers_reaped']
        assert not (Path(r['parent_path'])/r['root_name']).exists()
        roots.append(dict(receipt=str(p.relative_to(OUT)),sha256=sha(p)))
    for p in directory.glob('run-broker-waits-*.json'):
        r=read(p)
        assert r['bootstrap_reaped'] and r['registered_helpers_reaped'] and r['storage_reaped'] and r['original_C1_released']
        waits.append(dict(receipt=str(p.relative_to(OUT)),sha256=sha(p)))
    assert len(roots)==len(waits)==6
    public=read(OUT/(name+'-public-evidence-index.json'));assert len(public)==6
    explicit=list(directory.glob('issuance-public-*.json'));assert len(explicit)==2
    links=0;issued=0;gaps=[]
    for p in [*(OUT/r['snapshot'] for r in public),*explicit]:
        facts=read(p)
        if p in explicit:assert facts['source_sha256']==sha(root/'tests/thesis_lite/maestro/test_issuance.py')
        records={r['sequence']:r for r in facts.get('m3',facts.get('public_m3',[]))}
        events=facts.get('argus',facts.get('argus_events',[]))
        for event in events:
            payload=event.get('extensions',{}).get('xverse.maestro')
            if payload is None:continue
            validator.validate(payload)
            for ref in payload['sourceRefs']:
                if ref['kind']=='m3-record':
                    assert ref['sha256']=='sha256:'+hashlib.sha256(canonical_bytes(records[ref['sequence']])).hexdigest()
                    links+=1
            if payload['action']=='issued':
                issued+=1
                source=records[payload['sourceRefs'][0]['sequence']]
                assert source['status']=='staged' and source['kind']=='observation'
                assert source['handleId']==source['handleResourceIdentity']=='withheld' and source['permitNonce'] is None
                assert source['details']['generation']==payload['generation']
                assert 'nativeTicket' not in source and event['producerId']=='maestro.issuance17'
                intent=next(e for e in events if e['eventId']==event['causationId'])
                assert intent['extensions']['xverse.maestro']['action']=='intent'
                assert intent['ingestionOrdinal']<event['ingestionOrdinal']
        if facts.get('reader_gaps'):
            assert p.name.startswith('test_missing_issued_mirror_')
            assert len(facts['reader_gaps'])==2 and all(g['source']=='Argus mirror' for g in facts['reader_gaps'])
            gaps.append(dict(snapshot=str(p.relative_to(OUT)),gaps=facts['reader_gaps']))
    assert len(gaps)==1
    for r in public:assert sha(OUT/r['snapshot'])==r['sha256']
    phases.append(dict(phase=phase,checks_passed=6,owned_roots_absent=6,root_receipts=roots,
        original_helper_wait_receipts=waits,public_snapshots=6,explicit_exports=2,
        actual_source_hash_links=links,issued_annotations_including_explicit_copies=issued,
        intentional_deleted_mirror_gaps=gaps,original_fixtures_lost=0))
result=dict(revision='ML3-AFFA17-2026-10-18-issued-v1',actual_terminal_session=4475,
    frozen_source_root=str(root),frozen_inputs_sha256=sha(OUT/'issued-v1-frozen-inputs.json'),
    installed_identity_sha256=sha(OUT/'issued-v1-installed-identity.json'),
    wheel_sha256=sha(OUT/'issued-v1-dist/xverse_xdl-0.4.0-py3-none-any.whl'),phases=phases,
    actual_issued_event_before_release=True,full_current_source_regression=False,
    U7_U8_complete=False,full_M1_complete=False,stable_increment17=False,accepted=False,merged=False,
    canonical_note_edited=False,factory_run_created=False)
(OUT/'issuance-component-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ['phase','checks_passed','owned_roots_absent','actual_source_hash_links','original_fixtures_lost']} for r in phases]))
