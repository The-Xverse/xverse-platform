"""Read-only legacy readiness regression and original source retention."""
import hashlib
import json
from pathlib import Path
import re
import sys
import sysconfig
import zipfile
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse_xdl.lifecycle import FileEvidenceJournal

OUT=Path(sys.argv[1]).resolve(strict=True);TOOL=int(sys.argv[2]);EXIT=int(sys.argv[3])
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
running=read(OUT/'running.json');source=Path(running['frozen_source_root'])
frozen=read(OUT/'frozen-inputs.json');assert all(sha(source/n)==h for n,h in frozen.items())
installed=Path(sysconfig.get_path('purelib'));packaged=[]
with zipfile.ZipFile(OUT/'dist/xverse_xdl-0.4.0-py3-none-any.whl') as wheel:
    for n,h in frozen.items():
        if n.startswith('src/') and n.endswith(('.py','.c')):
            entry=n.removeprefix('src/')
            assert hashlib.sha256(wheel.read(entry)).hexdigest()==h==sha(installed/entry)
            packaged.append(entry)
assert len(packaged)==76
phases=[];roots=[];snapshots=[];links=0;gaps=[]
for phase in ('source','wheel'):
    receipt=read(OUT/(phase+'-receipt.json'));log=OUT/(phase+'.log')
    assert sha(log)==receipt['log_sha256'] and receipt['returncode']==receipt['public_capture_returncode']==0
    assert re.search(r'\b35 passed\b',log.read_text().splitlines()[-1])
    phases.append(dict(phase=phase,passed=35,returncode=0))
    harness=OUT/(phase+'-harness');private=Path(receipt['original_private_basetemp'])
    current_roots=list(harness.glob('maestro-component-*.json'));assert len(current_roots)==23
    for p in current_roots:
        row=read(p);assert row['root_removed'] and row['workers_reaped']
        assert not (Path(row['parent_path'])/row['root_name']).exists()
        roots.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
    # The broker capture adapter has no classic-stack receipts; retain actual
    # legacy sources directly, preserving unavailable or contradictory facts.
    destination=OUT/(phase+'-legacy-public');destination.mkdir()
    for journal in sorted(private.glob('*/m3.jsonl')):
        fixture=journal.parent;errors=[];events=[];m3=[]
        try:m3=list(FileEvidenceJournal(journal).public_records())
        except Exception as e:errors.append(dict(source='M3',error=type(e).__name__+': '+str(e)))
        try:events=list(EvidenceStore.read_run(fixture/'argus').records())
        except Exception as e:errors.append(dict(source='Argus',error=type(e).__name__+': '+str(e)))
        indexed={r['sequence']:r for r in m3};matched=set();count=0
        for e in events:
            for ref in e.get('extensions',{}).get('xverse.maestro',{}).get('sourceRefs',[]):
                if ref.get('kind')=='m3-record':
                    original=indexed.get(ref['sequence'])
                    if original is not None and ref['sha256']=='sha256:'+hashlib.sha256(canonical_bytes(original)).hexdigest():
                        count+=1;matched.add(ref['sequence'])
                    else:errors.append(dict(source='M3 reference',event=e['eventId'],reference=ref))
        unmirrored=sorted(indexed.keys()-matched)
        if unmirrored:errors.append(dict(source='Argus mirror',unmirrored=unmirrored))
        path=destination/(fixture.name+'.json')
        save(path,dict(original_fixture=str(fixture),m3=m3,argus=events,source_links=count,reader_gaps=errors))
        snapshots.append(dict(path=str(path.relative_to(OUT)),sha256=sha(path),source_links=count))
        links+=count
        if errors:gaps.append(dict(phase=phase,fixture=str(fixture),reader_gaps=errors))
assert EXIT==0 and len(roots)==46
result=dict(original_tool_session=TOOL,original_tool_exit=EXIT,phases=phases,
    packaged_sources=76,original_root_receipts=roots,legacy_public_snapshots=snapshots,
    source_links=links,reader_gaps=gaps,auditor_sha256=sha(Path(__file__)),
    source_manifest_sha256=sha(OUT/'frozen-inputs.json'),component_scope_passed=True,
    full_M1_complete=False,full_selected_increment17_complete=False,accepted=False)
save(OUT/'verification.json',result)
print(json.dumps(dict(phases=phases,root_receipts=len(roots),snapshots=len(snapshots),source_links=links,gap_sets=len(gaps))))
