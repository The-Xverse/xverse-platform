"""Audit exact controller candidates; keep failed disposal receipts explicitly missing."""
from pathlib import Path
import hashlib
import json
from jsonschema import Draft202012Validator
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse_xdl.lifecycle import FileEvidenceJournal

OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for revision,phase,status,expected in [
    ('controller-v3','source',1,'7 failed, 4 passed'),
    ('controller-v4','source',1,'11 passed, 7 errors'),
    ('controller-v5','source',0,'11 passed'),
    ('controller-v5','wheel',0,'11 passed'),
]:
    name=revision+'-'+phase
    running=read(OUT/(revision+'-running.json'));root=Path(running['frozen_source_root'])
    manifest=read(OUT/(revision+'-frozen-inputs.json'))
    assert all(sha(root/n)==h for n,h in manifest.items())
    identity=read(OUT/(revision+'-installed-identity.json'));assert len(identity)==34
    for n,r in identity.items():assert sha(Path(r['file']))==r['sha256']==sha(root/'src/xverse/maestro'/n)
    receipt=read(OUT/(name+'-receipt.json'))
    assert receipt['returncode']==status and receipt['public_capture_returncode']==0
    assert receipt['log_sha256']==sha(OUT/(name+'.log'))
    assert expected in (OUT/(name+'.log')).read_text()
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
        assert r['original_C1_released'] and 1<=r['helper_count']<=4
        waits.append(dict(receipt=str(p.relative_to(OUT)),sha256=sha(p),facts=r))
    assert len(roots)==10
    assert len(waits)==(3 if revision=='controller-v4' else 10)
    public=read(OUT/(name+'-public-evidence-index.json'))
    for r in public:assert sha(OUT/r['snapshot'])==r['sha256']
    assert not any(g['source']=='original fixture' for r in public for g in r['reader_gaps'])
    private=Path(receipt['original_private_basetemp'])
    fixtures=[p for p in private.iterdir() if p.name.startswith('test_') and p.is_dir() and not p.is_symlink()]
    assert len(fixtures)==10
    extra=[]
    # Actual retained source files can still be projected independently of the
    # missing wait receipt. Never create a replacement wait record from these.
    if revision=='controller-v4':
        for fixture in fixtures:
            if (directory/('run-broker-waits-'+fixture.name+'.json')).exists():continue
            m3=list(FileEvidenceJournal(fixture/'m3.jsonl').public_records())
            events=list(EvidenceStore.read_run(fixture/'argus').records())
            data=dict(normal_wait_receipt_missing=True,original_fixture=str(fixture),m3=m3,argus=events,
                missing_normal_receipt_not_reconstructed=True)
            path=directory/'retained-after-disposal-error'/(fixture.name+'.json')
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(data,indent=2)+'\n')
            extra.append(dict(snapshot=str(path.relative_to(OUT)),sha256=sha(path)))
        assert len(extra)==7
    validator=Draft202012Validator(read(root/'tests/thesis_lite/maestro/lifecycle-payload-v2.schema.json'))
    exports=[]
    for path in directory.glob('controller-replacement-public-*.json'):
        facts=read(path)
        assert facts['source_sha256']==sha(root/'tests/thesis_lite/maestro/test_controller.py')
        assert facts['original_controller_dead_reaped'] and facts['original_storage_authority_handles_retained']
        assert facts['fresh_native_probes'] and facts['old_session']!=facts['new_session']
        assert facts['actual_resource_generation'] in (1,2)
        exports.append(dict(snapshot=str(path.relative_to(OUT)),sha256=sha(path)))
    assert len(exports)==(0 if revision=='controller-v3' else 2)
    links=0
    for r in [*public,*extra,*exports]:
        facts=read(OUT/r['snapshot'])
        records={m['sequence']:m for m in facts.get('m3',facts.get('public_m3',[]))}
        for event in facts.get('argus',facts.get('argus_events',[])):
            payload=event.get('extensions',{}).get('xverse.maestro')
            if payload is None:continue
            validator.validate(payload)
            for ref in payload['sourceRefs']:
                if ref['kind']=='m3-record':
                    assert ref['sha256']=='sha256:'+hashlib.sha256(canonical_bytes(records[ref['sequence']])).hexdigest()
                    links+=1
    rows.append(dict(revision=revision,phase=phase,returncode=status,roots_absent=len(roots),root_receipts=roots,
        original_helper_wait_receipts=waits,missing_normal_wait_receipts=len(roots)-len(waits),
        normal_public_snapshots=len(public),retained_sources_after_disposal_error=extra,
        explicit_controller_exports=exports,actual_public_source_hash_links_verified=links,
        original_fixtures_lost=0,source_manifest_sha256=sha(OUT/(revision+'-frozen-inputs.json'))))
result=dict(revision='ML3-AFFA17-2026-10-18-controller-v5-focused',phases=rows,
    current_source_checks_passed=11,current_installed_checks_passed=11,
    actual_original_controller_death_wait_and_new_session=True,
    actual_original_issuer_generation1_and_2_reconciliation=True,
    no_start_intents_replayed=True,full_current_regression=False,
    full_M1_complete=False,stable_increment17=False,accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False)
(OUT/'controller-focused-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ('revision','phase','returncode','roots_absent','missing_normal_wait_receipts','actual_public_source_hash_links_verified')} for r in rows]))
