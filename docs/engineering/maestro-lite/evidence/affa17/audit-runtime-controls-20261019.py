"""Audit owned whole-entry/current-file scopes and original inert counterexamples."""
import hashlib
import json
import os
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

out=Path(sys.argv[1]).resolve(strict=True);handle,exit_code=int(sys.argv[2]),int(sys.argv[3])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
frozen,running=read(out/'frozen-inputs.json'),read(out/'running.json')
root=Path(running['frozen_source_root']);assert all(sha(root/n)==h for n,h in frozen.items())
prior=read(out.parent/'runtime-entry-20261019c/frozen-inputs.json')
changed=[n for n,h in frozen.items() if n.startswith('src/') and prior[n]!=h]
assert set(changed)<= {'src/xverse/maestro/runtime_entry.py'}
added=[n for n in frozen if n.startswith('src/') and n not in prior]
assert added==[]
installed=Path(sysconfig.get_path('purelib'));packaged=[]
with zipfile.ZipFile(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl') as wheel:
    for n,h in frozen.items():
        if n.startswith('src/') and n.endswith(('.py','.c')):
            entry=n.removeprefix('src/')
            assert hashlib.sha256(wheel.read(entry)).hexdigest()==h==sha(installed/entry)
            packaged.append(entry)
assert len(packaged)==80
phases=[];roots=[];cases=[];waits=[];snapshots=[];closed=[];seen=set();bootstrap_births=0;startup_cases=[];registry_cases=[];classification={}
for p in sorted(out.glob('*-receipt.json')):
    receipt=read(p)
    if 'cohort' not in receipt:continue
    label=p.name.removesuffix('-receipt.json');log=out/(label+'.log')
    assert sha(log)==receipt['log_sha256'] and receipt['public_capture_returncode']==0
    last=log.read_text().splitlines()[-1]
    counts={k:int(m.group(1)) if (m:=re.search(r'(\d+) '+k,last)) else 0 for k in ('passed','failed','errors')}
    assert (receipt['returncode']==0)==(counts['failed']==counts['errors']==0)
    phases.append(dict(cohort=receipt['cohort'],phase=receipt['phase'],returncode=receipt['returncode'],**counts))
    harness=out/(label+'-harness')
    for path in harness.glob('maestro-component-*.json'):
        row=read(path);identity=row['parent_path'],row['root_name']
        assert identity not in seen;seen.add(identity)
        assert row['root_removed'] and row['workers_reaped'] and not (Path(row['parent_path'])/row['root_name']).exists()
        roots.append(dict(path=str(path.relative_to(out)),sha256=sha(path)))
    for path in harness.glob('launcher-waits-*.json'):
        row=read(path)
        for owner in row['owners']:
            facts=owner['outcome'];assert not facts['cleanup_complete'] and not facts['ready_for_execution']
            if facts['birth_attempted']:
                assert facts['supervisor_reaped'] and owner['actual_wait_observed'];bootstrap_births+=1
    for path in harness.glob('runtime-startup-fault-*.json'):
        row=read(path);obs=row['observations'];primary,fallback=obs['primary'],obs['fallback']
        original=primary['closure'] if primary else None
        result=original or fallback
        assert result and result['root_reaped'] and all(h['process_reaped'] for h in result['helpers'])
        assert all(b['empty'] and b['released'] for b in result['boundaries'])
        assert obs['actual_original_root_wait'] and obs['all_original_C1_released']
        assert obs['ordinary_alias_restoration_after_cleanup'] and not row['full_M1_complete']
        if out.name.endswith('19a') and row['case'].endswith('-alias'):
            assert fallback and original is None
            if row['case']=='launcher-alias':assert primary is None and len(obs['primary_exceptions'])==1
            else:assert primary and not obs['primary_exceptions']
        else:
            assert primary and original and not obs['primary_exceptions'] and fallback is None
            assert primary['dispatch_returned'] is False
        classification[row['original_fixture']]=False
        startup_cases.append(dict(label=label,case=row['case'],path=str(path.relative_to(out)),sha256=sha(path),
            helper_births=obs['actual_registered_helpers'],fallback_used=fallback is not None,
            primary_result_retained=primary is not None,primary_exceptions=obs['primary_exceptions']))
    for path in harness.glob('runtime-registry-*.json'):
        row=read(path);assert not row['full_M1_complete']
        if row['case']=='registry-loss-stop':
            assert row['ordinary_rejected'] and row['original_cleanup_log_used'] and row['original_map_restored_after_actual_cleanup']
        elif row['case']=='productive-recovery':
            assert row['recovery']['disposition']=='completed' and row['recovery']['ordinary_reconciled']
            assert row['controller_helpers']==2 and row['active_seconds']==20 and row['recovery_seconds']==3
            assert row['original_worker_retained'] and row['original_authority_retained']
        else:assert row['case']=='closed' and row['original_run_retained'] and row['no_second_start']
        registry_cases.append(dict(label=label,case=row['case'],path=str(path.relative_to(out)),sha256=sha(path)))
    for path in harness.glob('runtime-entry-waits-*.json'):
        row=read(path);closure=row['closure'];startup=row['startup'];case=row['case']
        assert startup['supervisor_reaped'] and startup['registered_helpers_reaped'] and startup['unacknowledged_births']==0
        assert row['original_root_wait'] and row['actual_original_helper_waits'] and row['all_original_C1_released']
        assert closure['root_reaped'] and all(b['empty'] and b['released'] for b in closure['boundaries'])
        assert {h['role'] for h in closure['helpers']}=={3,4,5} and all(h['process_reaped'] for h in closure['helpers'])
        assert not closure['lifecycle_complete'] and not row['full_M1_complete']
        assert len(closure['native_units'])==2
        cancelled='concurrent_stop' in case or 'registry_loss_stop' in case
        classification[row['original_fixture']]=not cancelled
        if cancelled:
            assert not closure['normal_unit_records_complete']
            native=closure['native_units']
            confirmed=all(u['direct_child_reaped'] is True and u['native_retired'] is True for u in native if u['issued'] is True)
            assert closure['cleanup_complete'] is confirmed
            if not confirmed:assert 'ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN' in closure['diagnostics']
            assert sum(u['issued'] is True for u in closure['native_units'])==1
        else:
            assert closure['cleanup_complete'] and closure['normal_unit_records_complete'] and not row['diagnostics']
            assert all(u['issued'] and u['direct_child_reaped'] and u['native_retired'] for u in closure['native_units'])
            assert len(closure['terminal_reports'])==1 and not closure['writers']
            terminal=closure['terminal_reports'][0]
            if '[lost-close-ack]' in case:
                assert terminal['writer'] is None and terminal['lastAcknowledgedWriterState']=='open'
            else:assert terminal['writer']['evidence_complete'] and not closure['diagnostics']
        cases.append(dict(label=label,case=case,path=str(path.relative_to(out)),sha256=sha(path),
            helper_births=len(closure['helpers']),workload_births=sum(u['issued'] is True for u in closure['native_units'])))
        waits.append(dict(path=str(path.relative_to(out)),sha256=sha(path)))
    for item in read(out/(label+'-public-evidence-index.json')):
        assert sha(out/item['snapshot'])==item['sha256']
        projection=read(out/item['snapshot']);fixture=Path(projection['original_fixture']);gaps=[];m3=[];events=[]
        if (fixture/'m3.jsonl').is_file():
            try:m3=list(FileEvidenceJournal(fixture/'m3.jsonl').public_records())
            except Exception as error:gaps.append(dict(source='M3',error=type(error).__name__+': '+str(error)))
        else:gaps.append(dict(source='M3',error='original journal missing'))
        try:events=list(EvidenceStore.read_run(fixture/'argus').records())
        except Exception as error:gaps.append(dict(source='Argus',error=type(error).__name__+': '+str(error)))
        assert m3==projection['m3'] and events==projection['argus']
        by_sequence={r['sequence']:r for r in m3};mirrored=set();links=0
        for event in events:
            for ref in event.get('extensions',{}).get('xverse.maestro',{}).get('sourceRefs',[]):
                if ref.get('kind')=='m3-record':
                    actual=by_sequence.get(ref['sequence'])
                    if actual is None or ref['sha256']!='sha256:'+hashlib.sha256(canonical_bytes(actual)).hexdigest():
                        gaps.append(dict(source='M3 reference',event=event['eventId'],reference=ref,error='original source unavailable or hash mismatch'))
                    else:mirrored.add(ref['sequence']);links+=1
        for sequence in by_sequence.keys()-mirrored:gaps.append(dict(source='Argus mirror',m3_sequence=sequence,error='original M3 record lacks an actual Argus reference'))
        assert gaps==projection['reader_gaps']==item['reader_gaps'] and links==item['source_links']
        snapshots.append(dict(label=label,**item))
        inputs=read(harness/('entry-original-inputs-'+fixture.name+'.json'))
        admission=CoverageAdmission(canonical(inputs['original_admission']))
        plan=decode_collection(inputs['original_collection'],admission,inputs['admission_digest'])
        assert runtime_admission_digest(admission,plan,inputs['generation_ns'])==inputs['runtime_digest']
        checked=verify_runtime_closed(admission,plan,fixture/'argus',expected_admission_digest=inputs['admission_digest'],
            generation_ns=inputs['generation_ns'],expected_runtime_digest=inputs['runtime_digest'])
        assert checked.complete is classification[str(fixture)]
        if checked.complete:
            original=fixture/'argus';assert not any(p.is_symlink() for p in original.rglob('*'))
            files={str(p.relative_to(original)):sha(p) for p in original.rglob('*') if p.is_file()}
            destination=out/'retained-closed-public'/(label+'-'+fixture.name);destination.parent.mkdir(exist_ok=True)
            shutil.copytree(original,destination)
            assert {str(p.relative_to(destination)):sha(p) for p in destination.rglob('*') if p.is_file()}==files
            closed.append(dict(path=str(destination.relative_to(out)),files=files))
counts={phase:{k:sum(r[k] for r in phases if r['phase']==phase) for k in ('passed','failed','errors')} for phase in ('source','wheel')}
if out.name.endswith('19a'):
    assert exit_code==1 and counts=={p:dict(passed=11,failed=3,errors=0) for p in ('source','wheel')}
    assert not changed and len(roots)==28 and not cases and not closed and not registry_cases
    assert sum(r['fallback_used'] for r in startup_cases)==6
else:
    assert exit_code==0 and counts=={p:dict(passed=30,failed=0,errors=0) for p in ('source','wheel')}
    assert read(out/'collection-receipt.json')['collected']==30
    assert changed==['src/xverse/maestro/runtime_entry.py']
    assert len(roots)==52 and len(cases)==12 and len(closed)==8 and len(registry_cases)==6
    assert not any(r['fallback_used'] for r in startup_cases)
assert len(startup_cases)==12 and len(snapshots)==len(startup_cases)+len(cases)
assert sum(r['helper_births'] for r in startup_cases)==30
result=dict(original_exec_session=handle,original_exec_exit=exit_code,phases=phases,counts=counts,packaged_sources=80,
    all_79_other_production_sources_unchanged=True,changed_production_sources=changed,
    startup_cases=startup_cases,registry_cases=registry_cases,
    root_receipts=roots,whole_entry_cases=cases,wait_receipts=waits,snapshots=snapshots,
    actual_owned_supervisor_births=len(startup_cases)+len(cases),actual_startup_helpers=30,actual_helpers=30+sum(r['helper_births'] for r in cases),
    actual_workloads=sum(r['workload_births'] for r in cases),source_links=sum(r['source_links'] for r in snapshots),
    retained_durable_closed_roots=closed,auditor_sha256=sha(Path(__file__)),source_manifest_sha256=sha(out/'frozen-inputs.json'),
    actual_M1_admissions=0,public_admitted_start_implemented=False,
    full_M1_complete=False,whole_platform_regression=False,stable_increment17=False,accepted=False,merged=False)
with (out/'verification.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(counts=counts,roots=len(roots),startup_cases=len(startup_cases),fallbacks=sum(r['fallback_used'] for r in startup_cases),whole_entry_cases=len(cases),source_links=result['source_links'],closed=len(closed))))
