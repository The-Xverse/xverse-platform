"""Capture available actual v2 projections and explicitly retain missing sources."""
from pathlib import Path
import hashlib
import json
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse_xdl.lifecycle import FileEvidenceJournal

OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for name in ['teardown-v2-source-harness','teardown-v2-wheel-harness']:
    directory=OUT/name
    for receipt in sorted(directory.glob('run-broker-waits-*.json')):
        node=receipt.stem.removeprefix('run-broker-waits-')
        candidates=[]
        for root in Path('/tmp/pytest-of-jefferson').glob('pytest-[0-9]*'):
            tmp=root/node
            argus=tmp/'argus'
            if tmp.is_dir() and argus.is_dir() and -0.1 <= receipt.stat().st_mtime-argus.stat().st_mtime <= 8:
                candidates.append(tmp)
        data=dict(original_receipt=str(receipt),receipt_sha256=sha(receipt),original_fixture=None,
            maturity='owned_component_public_source_projections_only',m3=[],argus=[],reader_gaps=[])
        if len(candidates)!=1:
            data['reader_gaps'].append(dict(source='original fixture',error='missing or ambiguous retained original sources',candidate_count=len(candidates)))
        else:
            tmp=candidates[0]
            data['original_fixture']=str(tmp)
            journal=tmp/'m3.jsonl'
            if journal.is_file():
                try:
                    data['m3']=list(FileEvidenceJournal(journal).public_records())
                except Exception as exc:
                    data['reader_gaps'].append(dict(source='M3',error=type(exc).__name__+': '+str(exc)))
            else:
                data['reader_gaps'].append(dict(source='M3',error='original journal missing'))
            try:
                data['argus']=list(EvidenceStore.read_run(tmp/'argus').records())
            except Exception as exc:
                data['reader_gaps'].append(dict(source='Argus',error=type(exc).__name__+': '+str(exc)))
        by_sequence={r['sequence']:r for r in data['m3']}
        links=0
        mirrored=set()
        for event in data['argus']:
            for ref in event.get('extensions',{}).get('xverse.maestro',{}).get('sourceRefs',[]):
                if ref.get('kind')=='m3-record':
                    actual=by_sequence.get(ref['sequence'])
                    if actual is None or ref['sha256']!='sha256:'+hashlib.sha256(canonical_bytes(actual)).hexdigest():
                        data['reader_gaps'].append(dict(source='M3 reference',event=event['eventId'],reference=ref,error='original source unavailable or hash mismatch'))
                    else:
                        links+=1
                        mirrored.add(ref['sequence'])
        for sequence in by_sequence.keys()-mirrored:
            data['reader_gaps'].append(dict(source='Argus mirror',m3_sequence=sequence,error='original M3 record lacks an actual Argus reference'))
        data['actual_normal_source_hashes_verified']=links
        target=directory/'public-evidence'/(node+'.json')
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(data,indent=2)+'\n')
        rows.append(dict(snapshot=str(target.relative_to(OUT)),sha256=sha(target),m3_records=len(data['m3']),
            argus_records=len(data['argus']),source_links=links,reader_gaps=data['reader_gaps']))
(OUT/'teardown-v2-public-evidence-index.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(dict(snapshots=len(rows),actual_source_hashes=sum(r['source_links'] for r in rows),
    snapshots_with_reader_gaps=sum(bool(r['reader_gaps']) for r in rows),
    original_fixtures_missing=sum(any(g['source']=='original fixture' for g in r['reader_gaps']) for r in rows))))
