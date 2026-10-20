"""Audit exact native closure/scheduling attempts, preserving failed predecessors."""
from pathlib import Path
import hashlib
import json
from jsonschema import Draft202012Validator
from xverse.argus.schema import canonical_bytes

OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for revision,phase,status,summary in [
    ('shared-v1','source',1,'1 failed, 60 passed'),
    ('shared-v2','source',1,'3 failed, 84 passed'),
    ('shared-v3','source',0,'87 passed'),
    ('shared-v3','wheel',0,'87 passed')]:
    root=Path(read(OUT/(revision+'-running.json'))['frozen_source_root'])
    inputs=read(OUT/(revision+'-frozen-inputs.json'))
    assert all(sha(root/n)==h for n,h in inputs.items())
    identity=read(OUT/(revision+'-installed-identity.json'));assert len(identity)==34
    for n,r in identity.items():assert sha(Path(r['file']))==r['sha256']==sha(root/'src/xverse/maestro'/n)
    name=revision+'-'+phase
    receipt=read(OUT/(name+'-receipt.json'))
    assert receipt['returncode']==status and receipt['public_capture_returncode']==0
    assert receipt['log_sha256']==sha(OUT/(name+'.log'))
    assert summary in (OUT/(name+'.log')).read_text()
    directory=OUT/(name+'-harness')
    roots=[];waits=[]
    for p in directory.glob('maestro-component-*.json'):
        r=read(p)
        assert r['root_removed'] and r['workers_reaped']
        assert not (Path(r['parent_path'])/r['root_name']).exists()
        roots.append(dict(receipt=str(p.relative_to(OUT)),sha256=sha(p)))
    for p in directory.glob('run-broker-waits-*.json'):
        r=read(p)
        assert r['bootstrap_reaped'] and r['registered_helpers_reaped'] and r['storage_reaped']
        assert r['original_C1_released'] and r['helper_count'] in (2,3)
        waits.append(dict(receipt=str(p.relative_to(OUT)),sha256=sha(p)))
    assert len(roots)==61 and len(waits)==12
    public=read(OUT/(name+'-public-evidence-index.json'))
    assert len(public)==12
    for r in public:assert sha(OUT/r['snapshot'])==r['sha256']
    assert not any(g['source']=='original fixture' for r in public for g in r['reader_gaps'])
    schema=Draft202012Validator(read(root/'tests/thesis_lite/maestro/lifecycle-payload-v2.schema.json'))
    explicit=[]
    for pattern,test in [('shared-closure-public-*.json','test_shared_closure.py'),('shared-dispatch-public-*.json','test_shared_dispatcher.py')]:
        for path in directory.glob(pattern):
            facts=read(path)
            assert facts['source_sha256']==sha(root/'tests/thesis_lite/maestro'/test)
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
            explicit.append(dict(snapshot=str(path.relative_to(OUT)),sha256=sha(path)))
    assert len(explicit)==(7 if revision=='shared-v1' else 6 if revision=='shared-v2' else 8)
    links=0
    for row in [*public,*explicit]:
        facts=read(OUT/row['snapshot'])
        m3={r['sequence']:r for r in facts.get('m3',facts.get('public_m3',[]))}
        for event in facts.get('argus',facts.get('argus_events',[])):
            payload=event.get('extensions',{}).get('xverse.maestro')
            if payload is None:continue
            schema.validate(payload)
            for ref in payload['sourceRefs']:
                if ref['kind']=='m3-record':
                    assert ref['sha256']=='sha256:'+hashlib.sha256(canonical_bytes(m3[ref['sequence']])).hexdigest()
                    links+=1
    rows.append(dict(revision=revision,phase=phase,returncode=status,owned_roots_absent=len(roots),root_receipts=roots,
        original_helper_wait_receipts=waits,public_snapshots=len(public),explicit_closed_exports=explicit,
        actual_public_source_hash_links_verified=links,original_fixtures_lost=0,
        snapshots_with_gaps=sum(bool(r['reader_gaps']) for r in public),
        source_manifest_sha256=sha(OUT/(revision+'-frozen-inputs.json'))))
result=dict(revision='ML3-AFFA17-2026-10-18-shared-v3-components',phases=rows,source_checks_passed=87,
    installed_checks_passed=87,actual_shared_controller_five_phase_and_pauses=True,
    original_normal_and_unknown_workload_waits_separated=True,default_v1_pacing_unchanged=True,
    full_current_source_regression=False,full_M1_complete=False,U7_U8_complete=False,stable_increment17=False,
    accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False)
(OUT/'shared-component-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ('revision','phase','returncode','owned_roots_absent','public_snapshots','actual_public_source_hash_links_verified','snapshots_with_gaps')} for r in rows]))
