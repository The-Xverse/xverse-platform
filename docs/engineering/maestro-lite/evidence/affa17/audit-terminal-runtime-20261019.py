"""Exact native report evidence, external original pins, original waits and gaps."""
from pathlib import Path
import hashlib
import json
import re
import sys
import tarfile
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse_xdl.lifecycle import FileEvidenceJournal
from xverse.maestro.coverage import CoverageAdmission,canonical
from xverse.maestro.collection_plan import decode_collection
from xverse.maestro.runtime_verification import runtime_admission_digest,verify_runtime_closed

OUT=Path(sys.argv[1]).resolve(strict=True)
TOOL=int(sys.argv[2]);EXIT=int(sys.argv[3])
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=read(OUT/'running.json');source=Path(run['frozen_source_root'])
manifest=read(OUT/'frozen-inputs.json');identity=read(OUT/'installed-identity.json')
assert len(identity)==44 and all(sha(source/n)==h for n,h in manifest.items())
assert all(sha(Path(row['file']))==row['sha256']==manifest['src/xverse/maestro/'+n] for n,row in identity.items())
link=read(OUT/'original-phase-link.json') if (OUT/'original-phase-link.json').exists() else None
wheel=(Path(link['original_namespace']) if link else OUT)/'dist/xverse_xdl-0.4.0-py3-none-any.whl'
archive=(Path(link['original_namespace']) if link else OUT)/'tested-inputs.tar.gz'
receipts=[(phase,read(OUT/(phase+'-receipt.json'))) for phase in ('source','wheel') if (OUT/(phase+'-receipt.json')).exists()]
assert receipts
phases=[];waits=[];roots=[];source_links=0;gaps=[];external=[];terminal=[];captures=[]
for phase,receipt in receipts:
    log=OUT/(phase+'.log');assert sha(log)==receipt['log_sha256']
    assert receipt['input_manifest_sha256']==sha(OUT/'frozen-inputs.json') and receipt['public_capture_returncode']==0
    summary=log.read_text().splitlines()[-1]
    counts={k:int(m.group(1)) if (m:=re.search(r'(\d+) '+k,summary)) else 0 for k in ('passed','failed','errors')}
    assert counts['passed']+counts['failed']==96
    assert (receipt['returncode']==0)==(counts['failed']==counts['errors']==0)
    phases.append(dict(phase=phase,returncode=receipt['returncode'],**counts))
    harness=OUT/(phase+'-harness')
    for p in harness.glob('run-broker-waits-*.json'):
        b=read(p);assert all(b[k] for k in ('bootstrap_reaped','registered_helpers_reaped','storage_reaped','original_C1_released'))
        waits.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
    for p in harness.glob('maestro-component-*.json'):
        b=read(p);assert b['root_removed'] and b['workers_reaped']
        assert not (Path(b['parent_path'])/b['root_name']).exists()
        roots.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
    for b in read(OUT/(phase+'-public-evidence-index.json')):
        p=OUT/b['snapshot'];assert sha(p)==b['sha256'];data=read(p)
        assert data['original_fixture'] and not any(g['source']=='original fixture' for g in data['reader_gaps'])
        original=Path(data['original_fixture'])
        records=list(FileEvidenceJournal(original/'m3.jsonl').public_records()) if (original/'m3.jsonl').is_file() else []
        events=EvidenceStore.read_run(original/'argus').records()
        assert records==data['m3'] and events==data['argus']
        by_sequence={r['sequence']:r for r in records};count=0
        for event in events:
            for ref in event.get('extensions',{}).get('xverse.maestro',{}).get('sourceRefs',[]):
                if ref['kind']=='m3-record':
                    assert ref['sha256']=='sha256:'+hashlib.sha256(canonical_bytes(by_sequence[ref['sequence']])).hexdigest()
                    count+=1
        assert count==b['source_links'];source_links+=count
        if data['reader_gaps']:gaps.append(dict(snapshot=b['snapshot'],gaps=data['reader_gaps']))
    for p in harness.glob('terminal-original-inputs-*.json'):
        b=read(p);assert b['source_sha256']==manifest['tests/thesis_lite/maestro/test_terminal_runtime.py']
        ad=CoverageAdmission(canonical(b['original_admission']));ad.data(b['admission_digest'])
        plan=decode_collection(b['original_collection'],ad,b['admission_digest'])
        assert runtime_admission_digest(ad,plan,b['generation_ns'])==b['runtime_digest']
        checked=verify_runtime_closed(ad,plan,Path(b['original_fixture'])/'argus',
            expected_admission_digest=b['admission_digest'],expected_runtime_digest=b['runtime_digest'],generation_ns=b['generation_ns'])
        external.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p),writer_state=checked.lifecycle.writer_state,
            collection_verified=checked.collection_verified,collection_complete=checked.collection_complete,
            evidence_complete=checked.complete,diagnostics=list(checked.diagnostics),
            coverage_status=checked.lifecycle.coverage.report()['overallStatus'],manifest_sha256=checked.lifecycle.manifest_sha256))
    for p in harness.glob('terminal-runtime-*.json'):
        b=read(p);assert b['source_sha256']==manifest['tests/thesis_lite/maestro/test_terminal_runtime.py']
        assert b['native_helper_closure_not_inferred'] and not b['full_M1_complete'] and not b['scientific_result']
        root=Path(b['original_fixture'])/'argus';raw=(root/'manifest.json').read_bytes()
        assert sha(root/'manifest.json')==b['manifest_sha256']
        reader=EvidenceStore.read_run(root);assert reader.manifest==b['manifest']
        facts=b['receipt'];assert facts and facts['storageDrain']['worker_reaped']
        if facts['report'] is not None and facts['report']['entry'] is not None:
            entry=facts['report']['entry'];actual=(root/entry['path']).read_bytes()
            assert len(actual)==entry['bytes'] and hashlib.sha256(actual).hexdigest()==entry['sha256']
            assert json.loads(actual)['assessmentStage']=='pre-closure'
        if facts['writer'] is not None:
            writer=facts['writer'];assert writer['manifest_sha256']==hashlib.sha256(raw).hexdigest()
            assert writer['after_state']==reader.manifest['writerState']
        if b['case'] in ('explicit','implicit','preflight'):
            assert facts['report']['eligible'] and facts['writer']['evidence_complete']
            assert reader.manifest['writerState']=='closed'
        elif b['case']=='lost-close-ack':
            assert facts['writer'] is None and facts['lastAcknowledgedWriterState']=='open'
            assert reader.manifest['writerState']=='closed'
        elif b['case'] in ('lost-report-ack','changed-report-ack'):
            assert facts['writer'] is None and facts['lastAcknowledgedWriterState']=='open'
            assert reader.manifest['writerState']=='open'
        else:
            assert b['case'] in ('required-missing','changed-required','changed-optional')
            assert not facts['report']['eligible'] and facts['writer']['abort_completed']
            assert not facts['writer']['finalize_attempted'] and reader.manifest['writerState']=='failed'
        terminal.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p),case=b['case'],
            acknowledged_writer=facts['writer'] is not None,durable_writer_state=reader.manifest['writerState']))
    private=Path(receipt['original_private_basetemp']);files=[];total=0
    for p in sorted(private.rglob('*')):
        if not p.is_file() or p.is_symlink():continue
        rel=p.relative_to(private)
        if 'argus' not in rel.parts and p.name not in ('m3.jsonl','synthetic-m3.jsonl'):continue
        assert p.stat().st_size<=16<<20
        total+=p.stat().st_size;assert total<=128<<20
        files.append(p)
    assert files and len(files)<2048
    target=OUT/(phase+'-public-output-bytes.tar.gz')
    with target.open('xb') as stream:
        with tarfile.open(fileobj=stream,mode='w:gz') as tar:
            for p in files:tar.add(p,arcname=str(p.relative_to(private)),recursive=False)
    index=dict(original_basetemp=str(private),files={str(p.relative_to(private)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files},
               archive_sha256=sha(target))
    with (OUT/(phase+'-public-output-index.json')).open('x') as stream:json.dump(index,stream,indent=2);stream.write('\n')
    captures.append(dict(phase=phase,files=len(files),bytes=total,archive_sha256=sha(target),index_sha256=sha(OUT/(phase+'-public-output-index.json'))))
assert EXIT==(0 if all(r['returncode']==0 for r in phases) else 1)
result=dict(observed_original_tool_session=TOOL,observed_tool_terminal_exit=EXIT,phases=phases,
    phase_scope_passed=EXIT==0,full_source_wheel_scope_passed=False,original_source_failure_preserved=True,
    original_broker_waits=waits,original_roots_absent=roots,actual_source_links=source_links,reader_gaps=gaps,
    externally_pinned_closed_recomputations=external,original_terminal_outcomes=terminal,retained_actual_public_outputs=captures,
    installed_files=44,source_manifest_sha256=sha(OUT/'frozen-inputs.json'),installed_identity_sha256=sha(OUT/'installed-identity.json'),
    source_archive_sha256=sha(archive),wheel_sha256=sha(wheel),auditor_sha256=sha(Path(__file__)),
    original_input_public_pins_captured_before_run=bool(external),
    all_nine_full_runtime_cases_complete=False,full_platform_regression=False,full_M1_complete=False,
    stable_increment17=False,accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False,scientific_result=False)
with (OUT/'verification.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(phases=phases,original_broker_waits=len(waits),absent_roots=len(roots),source_links=source_links,
    external_recomputations=len(external),terminal_outcomes=len(terminal),reader_gaps=len(gaps),full_increment_complete=False)))
