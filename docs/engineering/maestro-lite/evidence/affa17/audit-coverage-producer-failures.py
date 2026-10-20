"""Audit retained failed producer snapshots without promoting missing wait facts."""
from pathlib import Path
import hashlib,json,re
OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for version,passed,failed in [(1,184,21),(2,198,9)]:
    tag='coverage-producers-v'+str(version)
    receipt=read(OUT/(tag+'-source-receipt.json'));root=Path(receipt['frozen_source_root'])
    log=OUT/(tag+'-source.log')
    assert receipt['returncode']==1 and receipt['public_capture_returncode']==0 and sha(log)==receipt['log_sha256']
    assert str(failed)+' failed, '+str(passed)+' passed' in log.read_text()
    assert not (OUT/(tag+'-wheel-receipt.json')).exists()
    frozen=read(OUT/(tag+'-frozen-inputs.json'));assert all(sha(root/n)==h for n,h in frozen.items())
    identity=read(OUT/(tag+'-installed-identity.json'));assert len(identity)==38
    for n,f in identity.items():assert sha(Path(f['file']))==f['sha256']==sha(root/'src/xverse/maestro'/n)
    roots=[];waits=[];births=[]
    directory=OUT/(tag+'-source-harness')
    for f in directory.glob('maestro-component-*.json'):
        j=read(f);assert j['root_removed'] and j['workers_reaped'] and not (Path(j['parent_path'])/j['root_name']).exists()
        roots.append(dict(path=str(f.relative_to(OUT)),sha256=sha(f)))
    for f in directory.glob('run-broker-waits-*.json'):
        j=read(f);assert j['bootstrap_reaped'] and j['registered_helpers_reaped'] and j['storage_reaped'] and j['original_C1_released']
        waits.append(dict(path=str(f.relative_to(OUT)),sha256=sha(f)))
    for f in directory.glob('bootstrap-children-*.json'):
        j=read(f);assert j['supervisor_reaped'] and j['registered_children_reaped'] and j['all_original_boundaries_released']
        births.append(dict(path=str(f.relative_to(OUT)),sha256=sha(f),facts=j))
    public=read(OUT/(tag+'-source-public-evidence-index.json'))
    assert all(sha(OUT/f['snapshot'])==f['sha256'] for f in public)
    result=dict(revision=tag+'-exact-failed-source',source_checks_passed=passed,source_checks_failed=failed,
        wheel_executed=False,receipt_sha256=sha(OUT/(tag+'-source-receipt.json')),
        source_manifest_sha256=sha(OUT/(tag+'-frozen-inputs.json')),installed_identity_sha256=sha(OUT/(tag+'-installed-identity.json')),
        failed_endpoints=re.findall(r'^FAILED (.+)$',log.read_text(),re.M),owned_roots_absent=roots,
        actual_normal_helper_waits=waits,captured_bootstrap_receipts_only=births,
        no_inference_of_missing_wait_receipts=True,public_snapshots=len(public),actual_source_links=sum(f['source_links'] for f in public),
        original_fixtures_lost=sum(any(g['source']=='original fixture' for g in f['reader_gaps']) for f in public),
        affected_regression_passed=False,full_M1_complete=False,stable_increment17=False,accepted=False,merged=False)
    (OUT/(tag+'-failure-verification.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(version=version,passed=passed,failed=failed,roots_absent=len(roots),actual_waits=len(waits),public_snapshots=len(public))))
