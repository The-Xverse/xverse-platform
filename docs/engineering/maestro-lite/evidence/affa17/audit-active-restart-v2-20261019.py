"""Read-only original-input audit of explicit restart and exact installed bytes."""
import hashlib
import json
from pathlib import Path
import re
import sys
import sysconfig
import zipfile

from xverse.argus import EvidenceStore
from xverse.maestro.collection_plan import decode_collection
from xverse.maestro.coverage import CoverageAdmission, canonical
from xverse.maestro.runtime_verification import runtime_admission_digest, verify_runtime_closed
from xverse_xdl.lifecycle import FileEvidenceJournal

OUT=Path(sys.argv[1]).resolve(strict=True);TOOL=int(sys.argv[2]);EXIT=int(sys.argv[3])
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
running=read(OUT/'running.json');source=Path(running['frozen_source_root'])
frozen=read(OUT/'frozen-inputs.json')
assert all(sha(source/n)==h for n,h in frozen.items())
identity=read(OUT/'installed-identity.json');assert len(identity)==46
assert all(sha(Path(r['file']))==r['sha256']==frozen['src/xverse/maestro/'+n] for n,r in identity.items())
installed=Path(sysconfig.get_path('purelib'));packaged=[]
with zipfile.ZipFile(OUT/'dist/xverse_xdl-0.4.0-py3-none-any.whl') as wheel:
    for name,value in frozen.items():
        if name.startswith('src/') and name.endswith(('.py','.c')):
            entry=name.removeprefix('src/')
            assert hashlib.sha256(wheel.read(entry)).hexdigest()==value==sha(installed/entry)
            packaged.append(entry)
assert len(packaged)==76
phases=[];cases=[];waits=[];roots=[];source_links=0;guards=[]
for phase in ('source','wheel'):
    receipt=read(OUT/(phase+'-receipt.json'));log=OUT/(phase+'.log')
    assert sha(log)==receipt['log_sha256'] and receipt['public_capture_returncode']==0
    summary=log.read_text().splitlines()[-1]
    counts={k:int(m.group(1)) if (m:=re.search(r'(\d+) '+k,summary)) else 0 for k in ('passed','failed','errors')}
    assert sum(counts.values())==read(OUT/'collection-receipt.json')['collected']
    assert (receipt['returncode']==0)==(counts['failed']==counts['errors']==0)
    phases.append(dict(phase=phase,returncode=receipt['returncode'],**counts))
    harness=OUT/(phase+'-harness')
    for p in harness.glob('run-broker-waits-*.json'):
        row=read(p)
        assert all(row[k] for k in ('bootstrap_reaped','registered_helpers_reaped','storage_reaped','original_C1_released'))
        waits.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
    for p in harness.glob('maestro-component-*.json'):
        row=read(p);assert row['root_removed'] and row['workers_reaped']
        assert not (Path(row['parent_path'])/row['root_name']).exists()
        roots.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
    for row in read(OUT/(phase+'-public-evidence-index.json')):
        assert sha(OUT/row['snapshot'])==row['sha256']
        source_links+=row['source_links']
    for mode in ('leaf','external-thread','parent-reject','controller-loss','stage-storage-loss'):
        path=harness/('active-restart-'+mode+'.json');row=read(path)
        pin=read(harness/('active-restart-inputs-'+mode+'.json'))
        assert row['source_sha256']==pin['source_sha256']==frozen['tests/thesis_lite/maestro/test_active_restart.py']
        assert row['original_fixture']==pin['original_fixture']
        assert row['restart_operation_seconds']==1 and row['scheduled_operation_seconds']==.5 and row['active_seconds']==4.8
        schedule=pin['original_schedule']
        assert schedule['version']==3 and schedule['restart_operation_seconds']==1
        assert schedule['operation_seconds']==.5 and schedule['active_seconds']==4.8
        admission=CoverageAdmission(canonical(pin['original_admission']));body=admission.data(pin['admission_digest'])
        assert 'sha256:'+hashlib.sha256(canonical(schedule)).hexdigest() in body['sourceDigests']
        plan=decode_collection(pin['original_collection'],admission,pin['admission_digest'])
        assert runtime_admission_digest(admission,plan,pin['generation_ns'])==pin['runtime_digest']
        assert len(body['units'])==2 and len(body['contexts'])==4
        assert len(row['tickets'])==len(row['restart_results'])==1
        ticket=row['tickets'][0];result=row['restart_results'][0];unit=ticket['unit_id']
        assert ticket['generation']==2 and ticket['deadline']['monotonic_seconds']<=body['end']
        fixture=Path(row['original_fixture']);root=fixture/'argus'
        m3=list(FileEvidenceJournal(fixture/'m3.jsonl').public_records());assert m3==row['public_m3']
        closure=row['closure'];assert closure is not None and closure['root_reaped']
        assert all(x['empty'] and x['released'] for x in closure['boundaries'])
        assert all(x['process_reaped'] for x in closure['helpers'])
        assert not closure['lifecycle_complete'] and not closure['ready_for_execution']
        checked=None
        if mode in ('leaf','external-thread','parent-reject'):
            checked=verify_runtime_closed(admission,plan,root,
                expected_admission_digest=pin['admission_digest'],generation_ns=pin['generation_ns'],
                expected_runtime_digest=pin['runtime_digest'])
            assert checked.complete and closure['normal_unit_records_complete']
            facts=row['terminal'];assert facts['diagnostic'] is None and facts['report']['eligible']
            assert facts['writer']['evidence_complete'] and facts['writer']['durable_writer_state']=='closed'
            assert closure['diagnostics']==[] and not closure['writers']
        if mode in ('leaf','external-thread'):
            assert result['disposition']=='completed' and result['diagnostic'] is None
            assert row['execution_threads'] and all(a==b for a,b in row['execution_threads'])
            execution=next(c['executionId'] for c in body['contexts'] if c['unitId']==unit and c['generation']==2)
            assert result['execution_id']==execution!=row['old_handles'][unit]['execution_id']
            observed={}
            for record in m3:
                observed.setdefault(record['details']['maestroUnitId'],set()).add(record['details']['generation'])
            assert observed[unit]=={1,2} and all(g=={1} for u,g in observed.items() if u!=unit)
            for generation in (1,2):
                terminal=[r for r in m3 if r['details']['maestroUnitId']==unit and r['details']['generation']==generation
                          and r['kind']=='outcome' and r['status']=='cleaned']
                assert len(terminal)==1
            native=[n for n in closure['native_units'] if n['unit_id']==unit]
            assert {n['generation'] for n in native}=={1,2}
            assert all(n['issued'] and n['direct_child_reaped'] and n['native_retired'] for n in native)
            output=next(a['path'] for a in body['artifacts'] if a['unitId']==unit and a['generation']==2)
            assert (root/output).read_bytes()==b'EXEC\n'
            compile_receipt=read(harness/'current-workload.json')
            assert compile_receipt['source_sha256']==frozen['tests/thesis_lite/maestro/catalog_workload_current.c']
            assert compile_receipt['binary_sha256']==sha(harness/'current-workload.bin')
            op_file=next(harness.glob('lazy-operations-*'+mode+'*.json'))
            operations=read(op_file)['operations']
            start=next(i for i,r in enumerate(operations) if r['kind']=='generation' and r['generation']==2)
            group=[]
            for r in operations[start:]:
                if group and r['kind'] in ('schedule','tick','teardown'):break
                group.append(r)
                if r['kind']=='probe' and r['generation']==2 and r['unit']==unit:break
            end=group[0]['end']
            assert 0<end-group[0]['began']<=1 and end<=ticket['deadline']['monotonic_seconds']
            assert all(r['end']==end and not r['diagnostic'] for r in group)
            assert any(r['kind']=='issued' and r['generation']==2 for r in group)
            assert any(r['kind']=='probe' and r['generation']==2 for r in group)
        elif mode=='parent-reject':
            assert result['disposition']=='rejected' and result['diagnostic']=='ML-GENERATION-DEPENDENTS'
            assert {r['details']['generation'] for r in m3}=={1} and not row['execution_threads']
        elif mode=='controller-loss':
            assert result['disposition']=='failed' and row['diagnostic'] and not row['execution_threads']
            assert row['terminal'] and not row['terminal']['report']['eligible']
            assert not row['terminal']['writer']['evidence_complete']
        else:
            assert result['disposition']=='failed' and row['execution_threads'] and row['diagnostic']
            assert 'ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN' in closure['diagnostics']
            unknown=[n for n in closure['native_units'] if n['unit_id']==unit and n['generation']==2]
            assert len(unknown)==1 and unknown[0]['issued'] is None and unknown[0]['direct_child_reaped'] is None
            assert closure['writers'] and not closure['writers'][0]['acknowledged']
            assert closure['writers'][0]['last_acknowledged_state']=='open'
            assert EvidenceStore.read_run(root).manifest['writerState']=='open'
        cases.append(dict(phase=phase,mode=mode,disposition=result['disposition'],
            original_inputs_sha256=sha(harness/('active-restart-inputs-'+mode+'.json')),
            receipt_sha256=sha(path),closed_offline_complete=bool(checked and checked.complete),
            workload_wait_unknown=mode=='stage-storage-loss',scientific_result=False))
    for mode in ('normal','parent-dies-after-arm','changed-end'):
        path=harness/('dependency-delegation-'+mode+'.json');row=read(path)
        assert row['parent_probes']==(1 if mode=='normal' else 0)
        assert row['native_arms']==(0 if mode=='changed-end' else 1)
        assert row['native_releases']==(1 if mode=='normal' else 0)
        assert row['source_sha256']==frozen['tests/thesis_lite/maestro/test_dependency_delegation.py']
        guards.append(dict(path=str(path.relative_to(OUT)),sha256=sha(path)))
    for mode in ('normal','unrelated-dead'):
        path=harness/('dependency-unrelated-'+mode+'.json');row=read(path);events=row['events']
        arms=[e for e in events if e['channel']=='native' and e['kind']=='ARM']
        releases=[e for e in events if e['channel']=='native' and e['kind']=='RELEASE']
        if mode=='normal':
            parent=[e for e in events if e['channel']=='rpc' and e['kind']=='probe' and e['unit']==row['parent']]
            unrelated=[e for e in events if e['channel']=='rpc' and e['kind']=='probe' and e['unit']==row['unrelated']]
            assert len(parent)==len(unrelated)==len(arms)==len(releases)==1
            assert unrelated[0]['ended']<=arms[0]['began']<=arms[0]['ended']<=parent[0]['began']
            assert parent[0]['ended']<=releases[0]['began']
        else:assert not arms and not releases
        guards.append(dict(path=str(path.relative_to(OUT)),sha256=sha(path)))
assert len(cases)==10 and len(guards)==10 and len(waits)==len(roots)==24
passed=all(p['returncode']==0 for p in phases)
assert EXIT==(0 if passed else 1)
result=dict(original_tool_session=TOOL,original_tool_exit=EXIT,phases=phases,cases=cases,
    original_wait_receipts=waits,original_root_receipts=roots,source_links=source_links,
    packaged_python_c_sources=len(packaged),guard_receipts=guards,
    source_manifest_sha256=sha(OUT/'frozen-inputs.json'),wheel_sha256=sha(OUT/'dist/xverse_xdl-0.4.0-py3-none-any.whl'),
    auditor_sha256=sha(Path(__file__)),component_scope_passed=passed,
    old_fixed_half_second_failures_not_waived=True,full_selected_increment17_complete=False,
    productive_controller_recovery=False,transitive_active_restart=False,full_M1_complete=False,accepted=False)
with (OUT/'verification.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(phases=phases,cases=len(cases),guards=len(guards),waits=len(waits),roots=len(roots),source_links=source_links,packaged_sources=len(packaged),full17=False)))
