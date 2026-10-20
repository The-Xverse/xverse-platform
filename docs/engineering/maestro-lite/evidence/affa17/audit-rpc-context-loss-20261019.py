"""Audit inert service policy, restricting native denials and retained regressions."""
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
from xverse.maestro.coverage import CoverageAdmission,canonical
from xverse.maestro.collection_plan import decode_collection
from xverse.maestro.runtime_verification import runtime_admission_digest,verify_runtime_closed
from xverse_xdl.lifecycle import FileEvidenceJournal

out=Path(sys.argv[1]).resolve(strict=True);handle,exit_code=int(sys.argv[2]),int(sys.argv[3])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
frozen,running=read(out/'frozen-inputs.json'),read(out/'running.json')
root=Path(running['frozen_source_root']);assert all(sha(root/n)==h for n,h in frozen.items())
prior=read(out.parent/'rpc-failure-20261019a/frozen-inputs.json')
changed=[n for n,h in frozen.items() if n.startswith('src/') and n in prior and prior[n]!=h]
added=[n for n in frozen if n.startswith('src/') and n not in prior]
assert set(changed)==(set() if out.name.endswith('19a') else {'src/xverse/maestro/persistence.py','src/xverse/maestro/runtime_entry.py'})
assert not added
installed=Path(sysconfig.get_path('purelib'));packaged=[]
with zipfile.ZipFile(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl') as wheel:
    for n,h in frozen.items():
        if n.startswith('src/') and n.endswith(('.py','.c')):
            entry=n.removeprefix('src/')
            assert hashlib.sha256(wheel.read(entry)).hexdigest()==h==sha(installed/entry)
            packaged.append(entry)
assert len(packaged)==81
phases=[];roots=[];launchers=[];root_waits=[];broker_waits=[];denials=[];cases=[];snapshots=[];closed=[];seen=set();classification={};contexts=[];startup_cases=[];storage_waits=[];losses=[]
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
    for path in harness.glob('rpc-context-loss-*.json'):
        row=read(path);f=row['original_failure'];fault=row['fault']
        assert row['actual_M1_admissions']==0
        assert all(row[k] for k in ('actual_root_wait','actual_helpers_reaped','original_C1_released','no_workload_output','original_metadata_restored_after_actual_cleanup'))
        assert f['kind']=='schedule' and f['stage']=='receive' and f['diagnostic']=='ML-PERSIST-TIMEOUT'
        assert re.fullmatch('ml-[0-9a-f]{32}',f['operation']) and f['failed_ns']>=f['deadline_ns']
        if out.name.endswith('19a'):
            assert not row['observation_unavailable'] and not row['diagnostics']
            if fault=='owner-tag':assert not row['primary_returned'] and row['primary_errors']==['OwnerError: ML-OWNER-HOLDER']
            else:assert fault in ('context-reference','context-content') and row['primary_returned'] and not row['primary_errors']
        else:
            assert row['primary_returned'] and not row['primary_errors'] and row['observation_unavailable']
            assert row['diagnostics']==['ML-RUNTIME-RPC-CONTEXT-UNRESOLVED']
        losses.append(dict(path=str(path.relative_to(out)),sha256=sha(path),fault=fault,primary_returned=row['primary_returned'],observation_unavailable=row['observation_unavailable']))
    for path in harness.glob('rpc-failure-*.json'):
        row=read(path);f=row['failure'];case=path.stem.removeprefix('rpc-failure-')
        assert row['actual_M1_admissions']==0
        assert set(f)=={'kind','stage','session','sequence','operation','started_ns','deadline_ns','failed_ns','diagnostic'}
        assert f['session']=='host-session' and f['started_ns']<=f['failed_ns']
        assert re.fullmatch('ml-[0-9a-f]{32}',f['operation'])
        assert f['stage']==('acknowledgement' if case.endswith('-fail') else 'receive')
        assert f['diagnostic']==('ML-PERSIST-ACK' if case.endswith('-fail') else 'ML-PERSIST-TIMEOUT')
        assert f['kind']==('init' if case.startswith('init-') else 'schedule' if case=='whole-runtime' else 'commit')
        assert f['sequence']==1 if case.startswith('init-') else f['sequence']>=2
        if f['diagnostic']=='ML-PERSIST-TIMEOUT':assert f['failed_ns']>=f['deadline_ns']
        contexts.append(dict(label=label,path=str(path.relative_to(out)),sha256=sha(path),case=case,failure=f))
    for path in harness.glob('persistence-children-*.json'):
        row=read(path);assert row['all_children_reaped']
        storage_waits.append(dict(path=str(path.relative_to(out)),sha256=sha(path),**row))
    for path in harness.glob('runtime-startup-fault-*.json'):
        row=read(path);obs=row['observations'];primary=obs['primary'];assert primary and obs['fallback'] is None
        closure=primary['closure'];assert closure['root_reaped'] and all(h['process_reaped'] for h in closure['helpers'])
        assert all(b['empty'] and b['released'] for b in closure['boundaries'])
        assert obs['actual_original_root_wait'] and obs['all_original_C1_released'] and not obs['primary_exceptions']
        startup_cases.append(dict(path=str(path.relative_to(out)),sha256=sha(path),case=row['case'],helpers=obs['actual_registered_helpers']))
    for path in harness.glob('launcher-waits-*.json'):
        row=read(path)
        assert row['helpers_created']==row['workloads_created']==0
        for owner in row['owners']:
            facts=owner['outcome'];assert not facts['ready_for_execution'] and not facts['cleanup_complete']
            if facts['birth_attempted']:assert facts['supervisor_reaped'] and owner['actual_wait_observed']
        launchers.append(dict(path=str(path.relative_to(out)),sha256=sha(path)))
    for path in harness.glob('run-bootstrap-waits-*.json'):
        row=read(path);drain=row['bootstrap_drain']
        assert drain['supervisor_reaped'] and drain['registered_children_reaped']
        assert row['original_helpers_actually_reaped'] and row['all_original_C1_released']
        root_waits.append(dict(path=str(path.relative_to(out)),sha256=sha(path),
            registered_helpers=row['original_helper_count'],unacknowledged_births=drain['unacknowledged_births'],
            workload_waits_unknown=row['workload_direct_child_waits_unknown']))
    for path in harness.glob('run-broker-waits-*.json'):
        row=read(path)
        assert all(row[k] for k in ('bootstrap_reaped','registered_helpers_reaped','storage_reaped','original_C1_released'))
        broker_waits.append(dict(path=str(path.relative_to(out)),sha256=sha(path),helper_count=row['helper_count']))
    for path in harness.glob('window-denial-*.json'):
        row=read(path);assert row['actual_M1_admissions']==0
        if row['case']=='helper-birth':
            assert row['before']==row['after'] and row['original_root_wait'] and row['original_helpers']==0
            assert row['expiry_and_corruption_cleanup_preserved']
        else:
            assert row['case']=='controller-allocation' and row['new_controller_count']==0
            assert row['corruption_cancel_preserved'] and row['original_helpers']==2
        denials.append(dict(path=str(path.relative_to(out)),sha256=sha(path),case=row['case']))
    for path in harness.glob('runtime-entry-waits-*.json'):
        row=read(path);closure=row['closure']
        identity=row['original_fixture']
        assert identity not in classification
        classification[identity]=not ('concurrent_stop' in row['case'] or 'registry_loss_stop' in row['case'] or 'actual_stopped_storage' in row['case'] or 'diagnostic_metadata_loss' in row['case'])
        assert row['original_root_wait'] and row['actual_original_helper_waits'] and row['all_original_C1_released']
        assert closure['root_reaped'] and all(h['process_reaped'] for h in closure['helpers'])
        assert all(b['empty'] and b['released'] for b in closure['boundaries']) and not closure['lifecycle_complete']
        cases.append(dict(path=str(path.relative_to(out)),sha256=sha(path),case=row['case']))
    for item in read(out/(label+'-public-evidence-index.json')):
        assert sha(out/item['snapshot'])==item['sha256'];projection=read(out/item['snapshot'])
        fixture=Path(projection['original_fixture']);m3=[];events=[];gaps=[]
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
        admission_path=harness/('entry-original-inputs-'+fixture.name+'.json')
        if not admission_path.is_file():continue  # old owned broker boundary, not full v6 entry
        inputs=read(admission_path);admission=CoverageAdmission(canonical(inputs['original_admission']))
        plan=decode_collection(inputs['original_collection'],admission,inputs['admission_digest'])
        assert runtime_admission_digest(admission,plan,inputs['generation_ns'])==inputs['runtime_digest']
        verified=verify_runtime_closed(admission,plan,fixture/'argus',expected_admission_digest=inputs['admission_digest'],
            generation_ns=inputs['generation_ns'],expected_runtime_digest=inputs['runtime_digest'])
        assert str(fixture) in classification
        assert verified.complete is classification[str(fixture)]
        if verified.complete:
            original=fixture/'argus';assert not any(p.is_symlink() for p in original.rglob('*'))
            files={str(p.relative_to(original)):sha(p) for p in original.rglob('*') if p.is_file()}
            destination=out/'retained-closed-public'/(label+'-'+fixture.name);destination.parent.mkdir(exist_ok=True)
            shutil.copytree(original,destination)
            assert {str(p.relative_to(destination)):sha(p) for p in destination.rglob('*') if p.is_file()}==files
            closed.append(dict(path=str(destination.relative_to(out)),files=files))
counts={phase:{k:sum(r[k] for r in phases if r['phase']==phase) for k in ('passed','failed','errors')} for phase in ('source','wheel')}
if out.name.endswith('19a'):
    assert exit_code==1 and counts=={p:dict(passed=0,failed=3,errors=0) for p in ('source','wheel')}
    assert read(out/'collection-receipt.json')['collected']==31 and (out/'regression-not-executed.json').is_file()
    assert len(roots)==6 and len(losses)==6 and len(cases)==4 and not closed
else:
    assert exit_code==0 and counts=={p:dict(passed=60,failed=0,errors=0) for p in ('source','wheel')}
    assert read(out/'collection-receipt.json')['collected']==60
    assert len(roots)==120 and len(losses)==6 and len(contexts)==10 and len(startup_cases)==12 and len(cases)==14 and len(closed)==4
result=dict(original_exec_session=handle,original_exec_exit=exit_code,phases=phases,counts=counts,
    packaged_sources=81,changed_production_sources=changed,added_production_sources=added,
    other_production_sources_unchanged=81-len(changed),root_receipts=roots,launcher_receipts=launchers,
    original_bootstrap_waits=root_waits,broker_waits=broker_waits,restricting_window_denials=denials,
    whole_entry_cases=cases,snapshots=snapshots,rpc_failure_contexts=contexts,context_loss_cases=losses,startup_cases=startup_cases,storage_waits=storage_waits,source_links=sum(r['source_links'] for r in snapshots),
    retained_durable_closed_roots=closed,actual_service_runtime_runs=0,actual_M1_admissions=0,
    unchanged_deadlines=True,first_failure_retention_verified=not out.name.endswith('19a'),
    auditor_sha256=sha(Path(__file__)),source_manifest_sha256=sha(out/'frozen-inputs.json'),
    source_parent_semantics_validated=False,real_operator_approval_verified=False,top_level_start_exported=False,
    full_M1_complete=False,whole_platform_regression=False,stable_increment17=False,
    unresolved_findings=[135,222,286,287],accepted=False,merged=False)
with (out/'verification.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(counts=counts,roots=len(roots),contexts=len(contexts),startup_cases=len(startup_cases),context_loss_cases=len(losses),source_links=result['source_links'],closed=len(closed))))
