"""Audit actual recovery observations against original pre-execution inputs."""
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

out=Path(sys.argv[1]).resolve(strict=True);handle,exit_code=int(sys.argv[2]),int(sys.argv[3])
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=read(out/'frozen-inputs.json');running=read(out/'running.json')
source=Path(running['frozen_source_root'])
assert all(sha(source/name)==value for name,value in frozen.items())
installed=Path(sysconfig.get_path('purelib'));packaged=[]
wheel_path=out/'dist/xverse_xdl-0.4.0-py3-none-any.whl'
with zipfile.ZipFile(wheel_path) as wheel:
    for name,value in frozen.items():
        if name.startswith('src/') and name.endswith(('.py','.c')):
            entry=name.removeprefix('src/')
            assert hashlib.sha256(wheel.read(entry)).hexdigest()==value==sha(installed/entry)
            packaged.append(entry)
assert len(packaged)==76
identity=read(out/'installed-identity.json');assert len(identity)==46
assert all(sha(Path(row['file']))==row['sha256']==frozen['src/xverse/maestro/'+name]
           for name,row in identity.items())
expected=read(out/'collection-receipt.json')['collected'];assert expected==94
phases=[];cases=[];roots=[];waits=[];snapshots=[];retained=[];legacy=[];legacy_gaps=[]
for phase in ('source','wheel'):
    receipt=read(out/(phase+'-receipt.json'));log=out/(phase+'.log')
    assert sha(log)==receipt['log_sha256'] and receipt['public_capture_returncode']==0
    summary=log.read_text().splitlines()[-1]
    counts={key:int(m.group(1)) if (m:=re.search(r'(\d+) '+key,summary)) else 0 for key in ('passed','failed','errors')}
    assert sum(counts.values())==expected
    assert (receipt['returncode']==0)==(counts['failed']==counts['errors']==0)
    phases.append(dict(phase=phase,returncode=receipt['returncode'],**counts))
    harness=out/(phase+'-harness')
    for path in harness.glob('maestro-component-*.json'):
        row=read(path);assert row['root_removed'] and row['workers_reaped']
        assert not (Path(row['parent_path'])/row['root_name']).exists()
        roots.append(dict(path=str(path.relative_to(out)),sha256=sha(path)))
    for path in harness.glob('run-broker-waits-*.json'):
        row=read(path)
        assert all(row[key] for key in ('bootstrap_reaped','registered_helpers_reaped','storage_reaped','original_C1_released'))
        waits.append(dict(path=str(path.relative_to(out)),sha256=sha(path)))
    for row in read(out/(phase+'-public-evidence-index.json')):
        assert sha(out/row['snapshot'])==row['sha256']
        snapshots.append(dict(phase=phase,**row))
    private=Path(receipt['original_private_basetemp'])
    destination=out/(phase+'-legacy-public');destination.mkdir()
    for journal in sorted(private.glob('*/m3.jsonl')):
        fixture=journal.parent
        if fixture.name.startswith('test_original_active_replacemen'):
            continue
        errors=[];records=[];events=[]
        try:records=list(FileEvidenceJournal(journal).public_records())
        except Exception as error:errors.append(dict(source='M3',error=type(error).__name__+': '+str(error)))
        try:events=list(EvidenceStore.read_run(fixture/'argus').records())
        except Exception as error:errors.append(dict(source='Argus',error=type(error).__name__+': '+str(error)))
        indexed={r['sequence']:r for r in records};matched=set();links=0
        for event in events:
            for ref in event.get('extensions',{}).get('xverse.maestro',{}).get('sourceRefs',[]):
                if ref.get('kind')=='m3-record':
                    actual=indexed.get(ref['sequence'])
                    if actual is not None and ref['sha256']=='sha256:'+hashlib.sha256(canonical_bytes(actual)).hexdigest():
                        matched.add(ref['sequence']);links+=1
                    else:errors.append(dict(source='M3 reference',event=event['eventId'],reference=ref))
        if indexed.keys()-matched:errors.append(dict(source='Argus mirror',missing=sorted(indexed.keys()-matched)))
        path=destination/(fixture.name+'.json')
        with path.open('x') as f:json.dump(dict(original_fixture=str(fixture),m3=records,argus=events,reader_gaps=errors),f,indent=2);f.write('\n')
        legacy.append(dict(path=str(path.relative_to(out)),sha256=sha(path),source_links=links))
        if errors:legacy_gaps.append(dict(phase=phase,fixture=str(fixture),errors=errors))
    compiled=read(harness/'recovery-workload.json')
    assert compiled['source_sha256']==frozen['tests/thesis_lite/maestro/catalog_workload_current.c']
    assert compiled['binary_sha256']==sha(harness/'recovery-workload.bin')
    modes=('before-start','mixed-initial','planned','dead-before-drain','heartbeat-race','generation2','restart-after','stopped-then-recovery','cleaned-then-restart','snapshot-loss')
    for mode in modes:
        path=harness/('active-recovery-'+mode+'.json');pin_path=harness/('active-recovery-inputs-'+mode+'.json')
        row,pin=read(path),read(pin_path)
        assert row['source_sha256']==pin['source_sha256']==frozen['tests/thesis_lite/maestro/test_active_controller_recovery.py']
        assert row['original_fixture']==pin['original_fixture']
        schedule=pin['original_schedule'];assert schedule['version']==5
        assert schedule['recovery_operation_seconds']==3 and schedule['active_seconds']==20
        assert schedule['operation_seconds']==.3 and schedule['use_action_timeouts'] is True
        admission=CoverageAdmission(canonical(pin['original_admission']));body=admission.data(pin['admission_digest'])
        assert 'sha256:'+hashlib.sha256(canonical(schedule)).hexdigest() in body['sourceDigests']
        plan=decode_collection(pin['original_collection'],admission,pin['admission_digest'])
        assert runtime_admission_digest(admission,plan,pin['generation_ns'])==pin['runtime_digest']
        assert len(body['units'])==4 and len(body['contexts'])==8
        fixture=Path(row['original_fixture']);m3=list(FileEvidenceJournal(fixture/'m3.jsonl').public_records())
        assert m3==row['public_m3'] and not row['full_increment17_complete']
        assert len(row['outcomes'])==len(row['tickets'])==1
        outcome,ticket=row['outcomes'][0],row['tickets'][0]
        operations=read(next(harness.glob('lazy-operations-*productive_access-'+mode+'.json')))['operations']
        assert ticket['deadline']['monotonic_seconds']<=body['end']
        for borrowed in row['borrowed']:
            assert borrowed['owner_retained'] and borrowed['thread_retained']
            assert borrowed['new_session']==ticket['session_id']
            assert borrowed['end']<=ticket['deadline']['monotonic_seconds']
        complete=False
        if row['terminal'] is not None and row['diagnostic'] is None:
            assert outcome['disposition']=='completed' and outcome['ordinary_reconciled']
            assert all(row['old_retirement'][key] for key in ('original_child_dead','original_child_reaped','own_boundary_released'))
            assert all(r['session']==ticket['session_id'] for r in row['productive'])
            if mode!='heartbeat-race':assert row['productive']
            if mode in ('dead-before-drain','heartbeat-race'):assert row['threads'][0][0]!=row['threads'][0][1]
            leaf=next(c['unitId'] for c in body['contexts'] if c['unitId'].endswith('/terminal-instance'))
            snapshot=next(o for o in operations if o['kind']=='recovery')
            expected_states={u['unitId']:'never-issued' for u in body['units']}
            for unit,old in row['handles'].items():
                generation=next(c['generation'] for c in body['contexts'] if c['unitId']==unit and c['executionId']==old['execution_id'])
                terminal=[r['status'] for r in m3 if r['kind']=='outcome' and r['status'] in ('stopped','cleaned')
                          and r['details'].get('maestroUnitId')==unit and r['details'].get('generation')==generation
                          and r['details'].get('teardown',{}).get('observed_at',float('inf'))<snapshot['began']]
                expected_states[unit]=('released' if terminal[-1]=='cleaned' else 'stopped') if terminal else 'owned'
            assert row['expected_states']==expected_states
            rec=row['reconciliation'];assert rec['ordinary_reconciled'] and rec['cleanup'] is None
            assert {r['unit_id']:r['status'] for r in rec['units']}==expected_states
            assert set(row['new_probes'])=={u for u,state in expected_states.items() if state=='owned'}
            indexed={r['sequence']:r for r in m3}
            for unit in rec['units']:
                assert unit['native_running'] is (True if unit['status']=='owned' else None if unit['status']=='never-issued' else False)
                assert len(unit['sources'])==(0 if unit['status']=='never-issued' else 2)
                for ref in unit['sources']:
                    assert ref['sha256']=='sha256:'+hashlib.sha256(canonical(indexed[ref['sequence']])).hexdigest()
                if unit['status']=='never-issued':assert unit['handle_digest'] is None
                else:assert unit['handle_digest']=='sha256:'+hashlib.sha256(canonical(row['handles'][unit['unit_id']])).hexdigest()
            if mode=='before-start':assert set(expected_states.values())=={'never-issued'}
            if mode=='mixed-initial':assert list(expected_states.values()).count('owned')==1
            if mode=='stopped-then-recovery':assert expected_states[leaf]=='stopped'
            if mode=='cleaned-then-restart':assert expected_states[leaf]=='released'
            for probe in row['new_probes'].values():
                assert probe['host_session']==body['hostSession']!=ticket['session_id']
                assert snapshot['ended']<=probe['observed_at']<=row['borrowed'][0]['end']
            generations={r['details']['generation'] for r in m3}
            assert generations==({1,2} if mode in ('generation2','restart-after','cleaned-then-restart') else {1})
            assert {r['details']['maestroUnitId'] for r in m3 if r['details']['generation']==2}<= {leaf}
            for unit,probe in row['new_probes'].items():
                old=row['handles'][unit]
                assert probe['handle_digest']==hashlib.sha256(canonical(old)).hexdigest()
                expected_generation=next(c['generation'] for c in body['contexts']
                    if c['unitId']==unit and c['executionId']==old['execution_id'])
                assert probe['generation']==expected_generation and probe['ready']
            checked=verify_runtime_closed(admission,plan,fixture/'argus',expected_admission_digest=pin['admission_digest'],
                generation_ns=pin['generation_ns'],expected_runtime_digest=pin['runtime_digest'])
            assert checked.complete and row['terminal']['report']['eligible']
            assert row['terminal']['writer']['durable_writer_state']=='closed'
            assert row['closure']['normal_unit_records_complete']
            public=fixture/'argus';assert not any(p.is_symlink() for p in public.rglob('*'))
            original={str(p.relative_to(public)):sha(p) for p in public.rglob('*') if p.is_file()}
            destination=out/'closed-public'/(phase+'-'+mode);destination.parent.mkdir(exist_ok=True)
            shutil.copytree(public,destination)
            assert {str(p.relative_to(destination)):sha(p) for p in destination.rglob('*') if p.is_file()}==original
            assert verify_runtime_closed(admission,plan,destination,expected_admission_digest=pin['admission_digest'],
                generation_ns=pin['generation_ns'],expected_runtime_digest=pin['runtime_digest']).complete
            retained.append(dict(phase=phase,mode=mode,path=str(destination.relative_to(out)),files=original))
            for declaration in plan.declarations:assert (public/declaration.destination).read_bytes()==b'EXEC\n'
            complete=True
        if row['closure'] is not None:
            closure=row['closure']
            assert closure['root_reaped'] and all(h['process_reaped'] for h in closure['helpers'])
            assert all(b['empty'] and b['released'] for b in closure['boundaries'])
            assert len([h for h in closure['helpers'] if h['role']==5])==2
            assert not closure['lifecycle_complete'] and not closure['ready_for_execution']
        if mode=='snapshot-loss':
            closure=row['closure'];assert closure is not None
            assert outcome['disposition']=='failed' and not outcome['ordinary_reconciled']
            assert not closure['execution_succeeded'] and not closure['normal_unit_records_complete']
            assert closure['inventory_complete'] and closure['authority_fenced'] is True
            assert closure['unacknowledged_births']==0
            assert all(h['role'] not in (1,4) or h['direct_child_reaped'] for h in closure['helpers'])
            assert len(closure['native_units'])==4
            assert all(n['issued'] and n['direct_child_reaped'] and n['native_retired'] for n in closure['native_units'])
            assert not row['new_probes'] and not row['productive']
            assert any(o['kind']=='recovery' and o['diagnostic']=='ML-PERSIST-TIMEOUT' for o in operations)
        cases.append(dict(phase=phase,mode=mode,disposition=outcome['disposition'],diagnostic=row['diagnostic'],
            original_inputs_sha256=sha(pin_path),receipt_sha256=sha(path),independent_closed_complete=complete))
passed=all(p['returncode']==0 for p in phases)
assert exit_code==(0 if passed else 1) and roots and waits and len(cases)==20
result=dict(original_exec_session=handle,original_exec_exit=exit_code,phases=phases,cases=cases,
    packaged_sources=76,original_root_receipts=roots,original_wait_receipts=waits,snapshots=snapshots,
    source_links=sum(s['source_links'] for s in snapshots)+sum(s['source_links'] for s in legacy),
    legacy_snapshots=legacy,legacy_reader_gaps=legacy_gaps,retained_closed_public=retained,
    independent_closed_complete=sum(c['independent_closed_complete'] for c in cases),
    source_manifest_sha256=sha(out/'frozen-inputs.json'),wheel_sha256=sha(wheel_path),auditor_sha256=sha(Path(__file__)),
    component_scope_passed=passed,full_increment17_complete=False,full_M1_complete=False,
    whole_platform_regression=False,accepted=False,merged=False)
with (out/'verification.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({key:result[key] for key in ('phases','source_links','packaged_sources','independent_closed_complete','component_scope_passed')}))
