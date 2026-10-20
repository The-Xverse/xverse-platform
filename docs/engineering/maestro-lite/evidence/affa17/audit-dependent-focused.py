"""Audit original failed controls and the later focused restart/renewal evidence."""
from pathlib import Path
import hashlib
import json
import zipfile
from jsonschema import Draft202012Validator

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[4]
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
rows=[]
for name,status,text,dist in [
    ('dependent-stale-red',1,'1 failed','advance-v2'),
    ('dependent-v1-focused',1,'3 failed, 10 passed','dependent-v1'),
    ('dependent-v2-focused',0,'14 passed','dependent-v2'),
]:
    receipt=read(OUT/(name+'-receipt.json'))
    assert receipt['returncode']==status and receipt['log_sha256']==sha(OUT/(name+'.log'))
    assert text in (OUT/(name+'.log')).read_text()
    consumer=Path(receipt['consumer'])
    validator=Draft202012Validator(read(consumer/'tests/thesis_lite/maestro/lifecycle-payload-v2.schema.json'))
    directory=OUT/(name+'-harness')
    roots=[];waits=[]
    for p in directory.glob('maestro-component-*.json'):
        r=read(p)
        assert r['root_removed'] and r['workers_reaped']
        assert not (Path(r['parent_path'])/r['root_name']).exists()
        roots.append(dict(receipt=str(p.relative_to(OUT)),sha256=sha(p)))
    for p in directory.glob('run-broker-waits-*.json'):
        r=read(p)
        assert r['bootstrap_reaped'] and r['registered_helpers_reaped'] and r['storage_reaped'] and r['original_C1_released']
        waits.append(dict(receipt=str(p.relative_to(OUT)),sha256=sha(p)))
    public=read(OUT/(name+'-public-evidence-index.json'))
    for r in public:assert sha(OUT/r['snapshot'])==r['sha256']
    assert not any(g['source']=='original fixture' for r in public for g in r['reader_gaps'])
    special=[]
    for pattern,test in [('actual-generation-restart-public-*.json','test_generation_restart.py'),('transitive-restart-public-*.json','test_generation_dependents.py')]:
        for p in directory.glob(pattern):
            facts=read(p)
            assert facts['source_sha256']==sha(consumer/'tests/thesis_lite/maestro'/test)
            m3={r['sequence']:r for r in facts['public_m3']};links=0
            for e in facts['argus_events']:
                payload=e.get('extensions',{}).get('xverse.maestro')
                if payload is None:continue
                validator.validate(payload)
                for ref in payload['sourceRefs']:
                    if ref['kind']=='m3-record':
                        assert ref['sha256']=='sha256:'+hashlib.sha256(canonical(m3[ref['sequence']])).hexdigest()
                        links+=1
            if test=='test_generation_dependents.py':
                assert facts['actual_native_epochs']==[0,1,2,3]
                assert facts['original_worker_retained'] and facts['unrelated_original_handle_live']
                assert facts['quiescence_order']==list(reversed(facts['restart_order']))
            special.append(dict(snapshot=str(p.relative_to(OUT)),sha256=sha(p),source_links=links))
    rows.append(dict(phase=name,returncode=status,receipt_sha256=sha(OUT/(name+'-receipt.json')),consumer=str(consumer),
        roots_absent=len(roots),root_receipts=roots,helper_wait_receipts=waits,public_snapshots=len(public),
        actual_public_source_hash_links=sum(r['source_links'] for r in public),
        snapshots_with_gaps=sum(bool(r['reader_gaps']) for r in public),explicit_generation_exports=special))
assert [r['roots_absent'] for r in rows]==[1,13,14]
assert [r['public_snapshots'] for r in rows]==[1,13,14]
python='/tmp/maestro-lite-affa-dependent2-verify-20261018/bin/python'
import subprocess
code="""from pathlib import Path
import importlib,json,hashlib
base=Path(importlib.import_module('xverse.maestro').__file__).parent
print(json.dumps({str(p.relative_to(base)):{'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in list(base.glob('*.py'))+list((base/'native').glob('*.c'))}))"""
identity=json.loads(subprocess.check_output([python,'-I','-c',code],text=True))
assert len(identity)==32
with zipfile.ZipFile(OUT/'dependent-v2-dist/xverse_xdl-0.4.0-py3-none-any.whl') as wheel:
    for n,r in identity.items():
        assert r['sha256']==sha(ROOT/'src/xverse/maestro'/n)==hashlib.sha256(wheel.read('xverse/maestro/'+n)).hexdigest()
(OUT/'dependent-v2-installed-identity.json').write_text(json.dumps(identity,indent=2)+'\n')
result=dict(revision='ML3-AFFA17-2026-10-18-dependent-v2-focused',phases=rows,
    installed_modules=28,native_resources=4,source_and_wheel_identity_matched=True,
    full_current_regression=False,full_M1_complete=False,stable_increment17=False,accepted=False,merged=False,
    canonical_note_edited=False,factory_run_created=False)
(OUT/'dependent-focused-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({r['phase']:{k:r[k] for k in ('returncode','roots_absent','public_snapshots','actual_public_source_hash_links','snapshots_with_gaps')} for r in rows}))
