"""Audit exact snapshots, original public facts, and actual collection/terminal order."""
from pathlib import Path
import hashlib
import json
import re
import sys
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse_xdl.lifecycle import FileEvidenceJournal

OUT=Path(sys.argv[1]).resolve(strict=True)
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result_path=OUT/('result-after-wheel.json' if (OUT/'result-after-wheel.json').exists() else 'result-after-source.json')
result=read(result_path);run=read(OUT/'running.json');root=Path(run['frozen_source_root'])
manifest=read(OUT/'frozen-inputs.json');assert all(sha(root/n)==h for n,h in manifest.items())
identity=read(OUT/'installed-identity.json');assert len(identity)==41
assert all(sha(Path(r['file']))==r['sha256']==sha(root/'src/xverse/maestro'/n) for n,r in identity.items())
assert sha(OUT/'dist/xverse_xdl-0.4.0-py3-none-any.whl')==result['wheel_sha256']
roots=[];waits=[];links=0;exports=[];phases=[];gaps=[]
for receipt in result['receipts']:
    phase='wheel' if '-I' in receipt['command'] else 'source';log=OUT/(phase+'.log')
    assert sha(log)==receipt['log_sha256'] and receipt['public_capture_returncode']==0
    summary=log.read_text().splitlines()[-1]
    counts={kind:int(m.group(1)) if (m:=re.search(r'(\d+) '+kind,summary)) else 0 for kind in ('passed','failed','errors')}
    assert counts['passed']+counts['failed']==result['collected_per_phase']
    assert (receipt['returncode']==0)==(counts['failed']==counts['errors']==0)
    phases.append(dict(phase=phase,returncode=receipt['returncode'],**counts))
    directory=OUT/(phase+'-harness')
    for p in directory.glob('maestro-component-*.json'):
        d=read(p);assert d['root_removed'] and d['workers_reaped']
        assert not (Path(d['parent_path'])/d['root_name']).exists()
        roots.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
    for p in directory.glob('run-broker-waits-*.json'):
        d=read(p);assert all(d[k] for k in ('bootstrap_reaped','registered_helpers_reaped','storage_reaped','original_C1_released'))
        waits.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
    for e in read(OUT/(phase+'-public-evidence-index.json')):
        p=OUT/e['snapshot'];assert sha(p)==e['sha256'];d=read(p)
        assert d['original_fixture'] and not any(g['source']=='original fixture' for g in d['reader_gaps'])
        original=Path(d['original_fixture'])
        actual=list(FileEvidenceJournal(original/'m3.jsonl').public_records()) if (original/'m3.jsonl').is_file() else []
        events=list(EvidenceStore.read_run(original/'argus').records())
        assert actual==d['m3'] and events==d['argus']
        byseq={r['sequence']:r for r in actual};count=0
        for event in events:
            for ref in event.get('extensions',{}).get('xverse.maestro',{}).get('sourceRefs',[]):
                if ref['kind']=='m3-record':
                    assert ref['sha256']=='sha256:'+hashlib.sha256(canonical_bytes(byseq[ref['sequence']])).hexdigest();count+=1
        assert count==e['source_links'];links+=count
        if e['reader_gaps']:gaps.append(dict(snapshot=e['snapshot'],gaps=e['reader_gaps']))
    for p in directory.glob('lazy-dispatch-test*.json'):
        d=read(p);assert d['source_sha256']==sha(root/'tests/thesis_lite/maestro/test_lazy_dispatcher.py')
        assert d['terminal_recorded'] and not d['full_lifecycle_complete'] and not d['full_M1_complete'] and not d['scientific_result']
        original=Path(d['original_fixture']);reader=EvidenceStore.read_run(original/'argus')
        assert reader.manifest['writerState']=='failed' and reader.records()==d['argus_events']
        receipt=d['collection'];assert receipt and receipt['entry'] in reader.manifest['artifacts']
        raw=(original/'argus'/receipt['entry']['path']).read_bytes();metadata=json.loads(raw)
        assert receipt['entry']['sha256']==hashlib.sha256(raw).hexdigest() and receipt['entry']['bytes']==len(raw)
        assert metadata['contextDigest']=='sha256:'+hashlib.sha256(canonical_bytes(metadata['context'])).hexdigest()
        assert receipt['metadataDigest']=='sha256:'+hashlib.sha256(raw).hexdigest()
        events=reader.records();payload=lambda e:e.get('extensions',{}).get('xverse.maestro',{})
        collect=next(e for e in events if payload(e).get('action')=='collect')
        unit_dispositions=[e for e in events if payload(e).get('action')=='disposition' and payload(e)['scope']=='unit']
        terminals=[e for e in events if payload(e).get('action')=='run-terminal'];assert len(terminals)==1 and len(unit_dispositions)==2
        assert all(e['ingestionOrdinal']>collect['ingestionOrdinal'] for e in unit_dispositions+terminals)
        if d['case']=='nominal':
            assert d['execution_succeeded'] and receipt['collectionComplete'] and metadata['collectionComplete']
            assert all(payload(e)['generation']==1 for e in unit_dispositions)
            prepare=[e for e in events if payload(e).get('stepId','').startswith('prepare-')]
            assert len(prepare)==6 and all(payload(e)['generation']==0 for e in prepare)
            for item in metadata['items']:
                data=(original/'argus'/item['destination']).read_bytes()
                assert item['status']=='collected' and data==b'EXEC\n' and item['sha256']==hashlib.sha256(data).hexdigest()
                assert item['entry'] in reader.manifest['artifacts']
        else:
            assert d['case']=='controller-stall' and not d['execution_succeeded'] and not metadata['collectionComplete']
            assert not d['public_m3'] and all(payload(e)['generation']==0 for e in unit_dispositions)
            assert all(item['status']=='unavailable' and item['entry'] is None for item in metadata['items'])
        exports.append(dict(phase=phase,case=d['case'],path=str(p.relative_to(OUT)),sha256=sha(p),
                            actual_collection_before_terminal=True,actual_closed_reader_checked=True))
passed=result['component_checks_passed']
if passed:assert len(exports)==4
summary=dict(phases=phases,component_scope_passed=passed,collected_per_phase=result['collected_per_phase'],
    original_roots_absent=roots,original_broker_waits=waits,original_source_links=links,reader_gaps=gaps,
    actual_lazy_exports=exports,original_fixtures_lost=0,exact_installed_files=41,
    source_manifest_sha256=sha(OUT/'frozen-inputs.json'),installed_identity_sha256=sha(OUT/'installed-identity.json'),
    wheel_sha256=result['wheel_sha256'],original_private_collection_plan_independently_rederived=False,
    failed_broader_scopes_repaired=False,full_platform_regression=False,full_M1_complete=False,
    all_nine_runtime_cases_complete=False,stable_increment17=False,accepted=False,merged=False,
    canonical_note_edited=False,factory_run_created=False,scientific_result=False)
with (OUT/('verification.json' if passed else 'failure-verification.json')).open('x') as f:f.write(json.dumps(summary,indent=2)+'\n')
print(json.dumps(dict(phases=phases,roots=len(roots),broker_waits=len(waits),source_links=links,
                     actual_lazy_exports=len(exports),component_scope_passed=passed,full_increment_complete=False)))
