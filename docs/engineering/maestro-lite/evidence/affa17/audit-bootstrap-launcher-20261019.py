"""Audit original startup wait records and v6 public evidence, not M1 approval."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import sysconfig
import zipfile
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse.maestro.coverage import CoverageAdmission, canonical
from xverse.maestro.collection_plan import decode_collection
from xverse.maestro.runtime_verification import runtime_admission_digest, verify_runtime_closed
from xverse_xdl.lifecycle import FileEvidenceJournal

out=Path(sys.argv[1]).resolve(strict=True)
handle,exit_code=int(sys.argv[2]),int(sys.argv[3])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
frozen,running=read(out/'frozen-inputs.json'),read(out/'running.json')
root=Path(running['frozen_source_root'])
assert all(sha(root/n)==h for n,h in frozen.items())
prior=read(out.parent/'runtime-admission-20261019b/frozen-inputs.json')
assert all(prior[n]==h for n,h in frozen.items() if n.startswith('src/') and n in prior)
added=[n for n in frozen if n.startswith('src/') and n not in prior]
assert added==['src/xverse/maestro/bootstrap_launcher.py']
installed=Path(sysconfig.get_path('purelib'));packaged=[]
with zipfile.ZipFile(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl') as wheel:
    for n,h in frozen.items():
        if n.startswith('src/') and n.endswith(('.py','.c')):
            entry=n.removeprefix('src/')
            assert hashlib.sha256(wheel.read(entry)).hexdigest()==h==sha(installed/entry)
            packaged.append(entry)
assert len(packaged)==78
phases=[];roots=[];startups=[];compositions=[];waits=[];snapshots=[];closed_roots=[]
seen_roots=set();seen_fixtures=set()
for path in sorted(out.glob('*-receipt.json')):
    receipt=read(path)
    if 'cohort' not in receipt:continue
    label=path.name.removesuffix('-receipt.json');log=out/(label+'.log')
    assert sha(log)==receipt['log_sha256'] and receipt['public_capture_returncode']==0
    last=log.read_text().splitlines()[-1]
    counts={k:int(m.group(1)) if (m:=re.search(r'(\d+) '+k,last)) else 0 for k in ('passed','failed','errors')}
    assert (receipt['returncode']==0)==(counts['failed']==counts['errors']==0)
    phases.append(dict(cohort=receipt['cohort'],phase=receipt['phase'],returncode=receipt['returncode'],**counts))
    harness=out/(label+'-harness')
    for p in harness.glob('maestro-component-*.json'):
        row=read(p);identity=row['parent_path'],row['root_name']
        assert identity not in seen_roots;seen_roots.add(identity)
        assert row['root_removed'] and row['workers_reaped']
        assert not (Path(row['parent_path'])/row['root_name']).exists()
        roots.append(dict(path=str(p.relative_to(out)),sha256=sha(p)))
    for p in harness.glob('launcher-waits-*.json'):
        row=read(p);assert row['helpers_created']==row['workloads_created']==0 and not row['full_M1_complete']
        assert len(row['owners'])==1
        owner=row['owners'][0];facts=owner['outcome']
        assert not facts['cleanup_complete'] and not facts['ready_for_execution']
        if facts['birth_attempted']:
            assert facts['process_returned'] and facts['supervisor_reaped'] and owner['actual_wait_observed']
            assert owner['original_pid']>1 and owner['actual_root_returncode'] is not None
            if facts['registered']:
                assert facts['registered_helpers_reaped'] and facts['unacknowledged_births']==0
            else:
                assert facts['registered_helpers_reaped'] is None and facts['unacknowledged_births'] is None
                assert owner['actual_root_returncode']==-9
        else:
            assert not facts['process_returned'] and facts['supervisor_reaped'] is None
            assert owner['original_pid'] is None and not owner['actual_wait_observed']
        startups.append(dict(label=label,case=row['case'],path=str(p.relative_to(out)),sha256=sha(p),
            actual_birth=facts['birth_attempted'],registered=facts['registered']))
    for p in harness.glob('launcher-composition-waits-*.json'):
        row=read(p);facts=row['outcome']
        assert facts['supervisor_reaped'] and facts['registered_helpers_reaped'] and facts['unacknowledged_births']==0
        assert not facts['cleanup_complete'] and not facts['ready_for_execution']
        assert row['original_helper_count']==3 and row['original_helpers_actually_reaped']
        assert row['actual_root_wait_observed'] and row['all_original_C1_released']
        waits.append(dict(path=str(p.relative_to(out)),sha256=sha(p)))
    for p in harness.glob('launcher-composition-*.json'):
        if p.name.startswith('launcher-composition-waits-'):continue
        row=read(p);closure=row['closure']
        assert closure['cleanup_complete'] and closure['normal_unit_records_complete'] and closure['root_reaped']
        assert {h['role'] for h in closure['helpers']}=={3,4,5} and all(h['process_reaped'] for h in closure['helpers'])
        assert all(b['empty'] and b['released'] for b in closure['boundaries'])
        assert len(closure['native_units'])==2
        assert all(u['issued'] and u['direct_child_reaped'] and u['native_retired'] for u in closure['native_units'])
        assert not closure['lifecycle_complete'] and not row['full_M1_complete'] and not row['scientific_result']
        assert len(closure['terminal_reports'])==1 and closure['writers']==[]
        terminal=closure['terminal_reports'][0]
        if row['case']=='closed':
            assert terminal['writer']['evidence_complete'] and not closure['diagnostics']
        else:
            assert row['case']=='lost-close-ack' and terminal['writer'] is None
            assert terminal['lastAcknowledgedWriterState']=='open' and 'ML-CLOSURE-REPORT-INCOMPLETE' in closure['diagnostics']
        compositions.append(dict(label=label,case=row['case'],path=str(p.relative_to(out)),sha256=sha(p)))
    for item in read(out/(label+'-public-evidence-index.json')):
        assert sha(out/item['snapshot'])==item['sha256']
        projection=read(out/item['snapshot']);fixture=Path(projection['original_fixture'])
        assert str(fixture) not in seen_fixtures;seen_fixtures.add(str(fixture))
        m3=list(FileEvidenceJournal(fixture/'m3.jsonl').public_records())
        events=list(EvidenceStore.read_run(fixture/'argus').records())
        assert m3==projection['m3'] and events==projection['argus']
        by_sequence={r['sequence']:r for r in m3};mirrored=set();links=0
        for event in events:
            for ref in event.get('extensions',{}).get('xverse.maestro',{}).get('sourceRefs',[]):
                if ref.get('kind')=='m3-record':
                    assert ref['sequence'] in by_sequence
                    assert ref['sha256']=='sha256:'+hashlib.sha256(canonical_bytes(by_sequence[ref['sequence']])).hexdigest()
                    mirrored.add(ref['sequence']);links+=1
        assert mirrored==by_sequence.keys() and not item['reader_gaps'] and not projection['reader_gaps']
        assert links==item['source_links'];snapshots.append(dict(label=label,**item))
        inputs=read(harness/('terminal-original-inputs-'+fixture.name+'.json'))
        admission=CoverageAdmission(canonical(inputs['original_admission']))
        plan=decode_collection(inputs['original_collection'],admission,inputs['admission_digest'])
        assert runtime_admission_digest(admission,plan,inputs['generation_ns'])==inputs['runtime_digest']
        checked=verify_runtime_closed(admission,plan,fixture/'argus',expected_admission_digest=inputs['admission_digest'],
            generation_ns=inputs['generation_ns'],expected_runtime_digest=inputs['runtime_digest'])
        assert checked.complete
        original=fixture/'argus';assert not any(p.is_symlink() for p in original.rglob('*'))
        files={str(p.relative_to(original)):sha(p) for p in original.rglob('*') if p.is_file()}
        destination=out/'retained-closed-public'/(label+'-'+fixture.name)
        destination.parent.mkdir(exist_ok=True);shutil.copytree(original,destination)
        assert {str(p.relative_to(destination)):sha(p) for p in destination.rglob('*') if p.is_file()}==files
        closed_roots.append(dict(path=str(destination.relative_to(out)),files=files,
            durable_closed_does_not_supply_missing_host_ack=True))
counts={phase:{k:sum(r[k] for r in phases if r['phase']==phase) for k in ('passed','failed','errors')} for phase in ('source','wheel')}
assert exit_code==0 and counts=={p:dict(passed=71,failed=0,errors=0) for p in ('source','wheel')}
assert read(out/'collection-receipt.json')['collected']==71
assert len(roots)==114 and len(startups)==30 and len(compositions)==len(waits)==len(snapshots)==len(closed_roots)==4
assert sum(r['actual_birth'] for r in startups)==8 and sum(r['registered'] for r in startups)==2
result=dict(original_exec_session=handle,original_exec_exit=exit_code,phases=phases,counts=counts,
    packaged_sources=78,all_77_previous_production_sources_unchanged=True,added_production_sources=added,
    root_receipts=roots,startup_cases=startups,composition_cases=compositions,wait_receipts=waits,snapshots=snapshots,
    actual_original_supervisor_births=12,actual_registered_helper_births=12,actual_composed_workload_births=8,
    source_links=sum(r['source_links'] for r in snapshots),retained_closed_public=closed_roots,
    auditor_sha256=sha(Path(__file__)),source_manifest_sha256=sha(out/'frozen-inputs.json'),
    unknown_birth_failure_path_executed=False,current_facility_revalidation_complete=False,public_start_implemented=False,
    actual_M1_admissions=0,full_M1_complete=False,whole_platform_regression=False,
    stable_increment17=False,accepted=False,merged=False)
with (out/'verification.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(counts=counts,roots=len(roots),actual_supervisors=12,source_links=result['source_links'],closed=len(closed_roots))))
