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

def retain_archive(target, entries):
    if target.exists():
        with tarfile.open(target, mode='r:gz') as retained:
            members=retained.getmembers()
            assert all(m.isfile() for m in members)
            assert {m.name for m in members}=={name for _,name in entries}
            assert len(members)==len(entries)
            for path,name in entries:
                with retained.extractfile(name) as stream:
                    assert stream.read()==path.read_bytes()
        return
    with target.open('xb') as stream:
        with tarfile.open(fileobj=stream,mode='w:gz') as retained:
            for path,name in entries:retained.add(path,arcname=name,recursive=False)

OUT=Path(sys.argv[1]).resolve(strict=True)
TOOL=int(sys.argv[2]);EXIT=int(sys.argv[3])
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=read(OUT/'running.json');source=Path(run['frozen_source_root'])
manifest=read(OUT/'frozen-inputs.json');identity=read(OUT/'installed-identity.json')
assert len(identity)==(45 if 'boundary-red-' in OUT.name else 46) and all(sha(source/n)==h for n,h in manifest.items())
assert all(sha(Path(row['file']))==row['sha256']==manifest['src/xverse/maestro/'+n] for n,row in identity.items())
link=read(OUT/'original-phase-link.json') if (OUT/'original-phase-link.json').exists() else None
wheel=(Path(link['original_namespace']) if link else OUT)/'dist/xverse_xdl-0.4.0-py3-none-any.whl'
archive=(Path(link['original_namespace']) if link else OUT)/'tested-inputs.tar.gz'
receipts=[(phase,read(OUT/(phase+'-receipt.json'))) for phase in ('source','wheel') if (OUT/(phase+'-receipt.json')).exists()]
assert receipts
phases=[];waits=[];roots=[];source_links=0;gaps=[];external=[];terminal=[];captures=[];extra=[]
for phase,receipt in receipts:
    log=OUT/(phase+'.log');assert sha(log)==receipt['log_sha256']
    assert receipt['input_manifest_sha256']==sha(OUT/'frozen-inputs.json') and receipt['public_capture_returncode']==0
    summary=log.read_text().splitlines()[-1]
    counts={k:int(m.group(1)) if (m:=re.search(r'(\d+) '+k,summary)) else 0 for k in ('passed','failed','errors')}
    assert counts['passed']+counts['failed']==read(OUT/'collection-receipt.json')['collected']
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
            if b['case'].startswith('native-writer-'):
                assert writer['durable_writer_state']==reader.manifest['writerState']
            else:
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
        elif b['case'].startswith('native-writer-'):
            assert facts['diagnostic'] is None and facts['report']['eligible']
            assert facts['writer'] is not None and not facts['writer']['evidence_complete']
            assert reader.manifest['writerState'] in ('open','failed')
        elif b['case'].startswith('nonopen-'):
            assert facts['report']['entry'] is None and not facts['report']['eligible']
            assert b['diagnostic']=='ML-SCHEDULE-EVIDENCE-INCOMPLETE'
            if b['case'].endswith('-changed-receipt'):
                assert facts['writer'] is None and facts['diagnostic'] is not None
                assert facts['lastAcknowledgedWriterState']=='open'
            else:
                row=facts['writer'];assert row is not None and facts['diagnostic'] is None
                assert row['before_state']==row['after_state']==reader.manifest['writerState']
                assert row['stage']=='not-open'
                assert not any(row[k] for k in ('finalize_attempted','finalize_completed','abort_attempted','abort_completed'))
                assert row['evidence_complete'] is (reader.manifest['writerState']=='closed')
            system=[e for e in reader.records() if e['eventKind'] in ('run-closed','run-failed')]
            assert len(system)==(1 if reader.manifest['writerState']=='failed' else 0)
        else:
            assert b['case'] in ('required-missing','changed-required','changed-optional')
            assert not facts['report']['eligible'] and facts['writer']['abort_completed']
            assert not facts['writer']['finalize_attempted'] and reader.manifest['writerState']=='failed'
        terminal.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p),case=b['case'],
            acknowledged_writer=facts['writer'] is not None,durable_writer_state=reader.manifest['writerState']))
    native_stage_controls=[];native_stage_files=[]
    expected={
      'fsync-once':('abort-completed','failed','failed','usable',True,True,'W-01'),
      'fsync-persistent':('flush-error','open','open','unknown',False,False,'W-01'),
      'recovery':('finalize-error','failed','open','unknown',False,False,'W-04'),
      'artifact-check':('finalize-error','failed','open','unknown',False,False,'W-05'),
      'manifest-replace':('finalize-error','failed','open','unknown',False,False,'W-06'),
      'abort-entry':('abort-error','open','open','usable',True,False,None)}
    for p in harness.glob('native-writer-result-*.json'):
        b=read(p);mode=b['mode'];e=expected[mode];w=b['receipt']['writer']
        assert b['source_sha256']==manifest['tests/thesis_lite/maestro/test_terminal_native_writer_failures.py']
        assert b['no_writer_rpc_replay'] and not b['private_stream_access']
        assert not any(b[k] for k in ('full_TR03_complete','full_TR06_complete','full_M1_complete','scientific_result'))
        assert tuple(w[k] for k in ('stage','after_state','durable_writer_state','abort_usability','abort_attempted','abort_completed'))==e[:6]
        original=Path(b['original_fixture']);assert sha(original/'argus/manifest.json')==b['manifest_sha256']==w['manifest_sha256']
        closed=b['closure'];assert closed['root_reaped'] and closed['inventory_complete'] and closed['unacknowledged_births']==0
        assert closed['normal_unit_records_complete'] and closed['authority_fenced']
        assert {h['role'] for h in closed['helpers']}=={3,4,5} and all(h['process_reaped'] for h in closed['helpers'])
        assert all(r['empty'] and r['released'] for r in closed['boundaries'])
        assert all(r['issued'] is False or r['direct_child_reaped'] is True for r in closed['native_units'])
        assert closed['terminal_reports']==[b['receipt']] and closed['writers']==[]
        assert not closed['lifecycle_complete'] and not closed['ready_for_execution']
        h=harness/('native-writer-helper-'+mode+'.json');r=read(h)
        assert r['admission_precedes_birth'] and not r['production_fault_mode_added'] and not r['private_stream_access']
        assert tuple(r['expected_public_states'])==e and r['source_sha256']==b['source_sha256']
        assert r['original_native_source_sha256']==manifest['src/xverse/maestro/native/bootstrap.c']
        code=r['fixed_fault_code'];assert hashlib.sha256(code.encode()).hexdigest()==r['fixed_fault_code_sha256']
        assert '._stream' not in code
        compiled=Path(r['command'][-4]);binary=Path(r['command'][-1]);trace=Path(r['trace_file'])
        assert sha(compiled)==r['compiled_source_sha256'] and sha(binary)==r['binary_sha256']
        native=(source/'src/xverse/maestro/native/bootstrap.c').read_text()
        anchor='args[2]="-m";args[3]="xverse.maestro.persistence_worker"';assert native.count(anchor)==1
        assert compiled.read_text()==native.replace(anchor,'args[2]="-c";args[3]='+json.dumps(code))
        actual=[json.loads(line) for line in trace.read_text().splitlines()];assert actual==b['trace']
        assert all(set(row)=={'operation','result','phase','writer_state'} for row in actual)
        errors=[row for row in actual if row['result']=='injected-error'];assert errors
        operations=[row['operation'] for row in actual if row['result']=='entered']
        assert operations==(['finalize','flush_buffer','abort'] if e[4] else ['finalize','flush_buffer'] if mode=='fsync-persistent' else ['finalize'])
        if e[4]:
            fresh=next(i for i,row in enumerate(actual) if row['operation']=='flush_buffer' and row['result']=='returned')
            abort=next(i for i,row in enumerate(actual) if row['operation']=='abort' and row['result']=='entered');assert fresh<abort
        native_stage_files.extend((compiled,binary,trace))
        native_stage_controls.append(dict(mode=mode,result=str(p.relative_to(OUT)),result_sha256=sha(p),
            helper_sha256=sha(h),original_trace_sha256=sha(trace),injected_operations=[r['operation'] for r in errors],
            original_manifest_sha256=b['manifest_sha256'],contract_row=e[6],full_row_universal_coverage=False))
    assert len(native_stage_controls)==(1 if OUT.name=='native-writer-stages-20261019a' else 6)
    # The initial test expectation failed before five closure assertions. Preserve
    # every actual injected mechanism/trace, including those incomplete controls.
    for p in harness.glob('native-writer-helper-*.json'):
        r=read(p);assert r['mode'] in expected and r['admission_precedes_birth'] and not r['private_stream_access']
        assert r['source_sha256']==manifest['tests/thesis_lite/maestro/test_terminal_native_writer_failures.py']
        code=r['fixed_fault_code'];assert hashlib.sha256(code.encode()).hexdigest()==r['fixed_fault_code_sha256']
        compiled=Path(r['command'][-4]);binary=Path(r['command'][-1]);trace=Path(r['trace_file'])
        assert sha(compiled)==r['compiled_source_sha256'] and sha(binary)==r['binary_sha256']
        assert '._stream' not in code
        assert [json.loads(line) for line in trace.read_text().splitlines()]
        native_stage_files.extend(p for p in (compiled,binary,trace) if p not in native_stage_files)
    if native_stage_files:
        private=Path(receipt['original_private_basetemp'])
        retain_archive(OUT/(phase+'-native-stage-helpers-and-traces.tar.gz'),
            [(p,str(p.relative_to(private))) for p in native_stage_files])
    delegation_controls=[]
    for p in harness.glob('dependency-delegation-*.json'):
        b=read(p);assert b['source_sha256']==manifest['tests/thesis_lite/maestro/test_dependency_delegation.py']
        assert b['deadlines_unchanged'] and not b['scientific_result']
        red='guard-delegation-red-' in OUT.name
        mode=b['mode'];assert mode in ('normal','parent-dies-after-arm','changed-end')
        probes=[e for e in b['events'] if e['channel']=='rpc' and e['kind']=='probe' and e['unit']==b['parent']]
        arms=[e for e in b['events'] if e['channel']=='native' and e['kind']=='ARM']
        releases=[e for e in b['events'] if e['channel']=='native' and e['kind']=='RELEASE']
        assert len(probes)==b['parent_probes'] and len(arms)==b['native_arms'] and len(releases)==b['native_releases']
        assert all(e['end']==b['original_fixed_end'] for e in probes)
        assert len(arms)==(0 if mode=='changed-end' else 1)
        assert len(releases)==(1 if mode=='normal' else 0)
        assert b['execution_succeeded'] is (mode=='normal')
        expected=(3 if red else 2) if mode=='normal' else (2 if red else 1) if mode=='parent-dies-after-arm' else 1
        assert len(probes)==expected
        if mode=='normal':
            assert any(e['channel']=='native' and e['kind']=='QUERY' and e['slot']!=arms[0]['slot']
                       and e['began']>=arms[0]['ended'] for e in b['events'])
            assert probes[-1]['ended']<=releases[0]['began']
        delegation_controls.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p),mode=mode,
            parent_probes=len(probes),native_arms=len(arms),native_releases=len(releases),
            observed_failure=b.get('observed_failure'),original_fixed_end=b['original_fixed_end']))
    offline_controls=[]
    for p in harness.glob('offline-boundary-*.json'):
        b=read(p);assert b['source_sha256']==manifest['tests/thesis_lite/maestro/test_offline_boundary.py']
        assert b['synthetic_facts'] and b['unchanged_evidence'] and not b['scientific_result']
        inputs=Path(b['original_inputs']);assert sha(inputs)==b['input_sha256']
        body=read(inputs);root=Path(body['root'])
        assert all(sha(root/name)==h for name,h in b['evidence_sha256'].items())
        target=OUT/(phase+'-'+p.stem+'-inputs.json')
        with target.open('xb') as stream:stream.write(inputs.read_bytes())
        red='boundary-red-' in OUT.name
        if red:
            assert b['returncode']==1 and 'Offline verifier imported runtime component: xverse.maestro.collection_runtime' in b['stderr']
        else:
            assert b['returncode']==0 and not b['stderr']
            result=json.loads(b['stdout']);assert result['complete']
            assert not any(n.split('.')[2] in result['denied_modules'] for n in result['modules'])
        offline_controls.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p),
            late_teardown=b['late_teardown'],returncode=b['returncode'],
            unchanged_evidence=True,retained_inputs=target.name,input_sha256=sha(target)))
    diagnostic_controls=[]
    for p in harness.glob('primary-diagnostic-*.json'):
        b=read(p);assert b['source_sha256']==manifest['tests/thesis_lite/maestro/test_dispatch_diagnostics.py']
        assert all(b[k] for k in ('actual_original_helper_stopped','original_cleanup_invoked','original_bounds_preserved'))
        assert not any(b[k] for k in ('execution_succeeded','lifecycle_complete','ready_for_execution','scientific_result'))
        expected='ML-PERSIST-TIMEOUT' if b['target']=='storage' else 'ML-CONTROLLER-TIMEOUT'
        assert b['original_failure']['diagnostic']==expected
        assert b['cleanup']['starts_closed'] and b['cleanup']['units']==[]
        red='primary-red-' in OUT.name
        assert b['observed_diagnostic']==('ML-SCHEDULE-CLEANUP-INCOMPLETE' if red else expected)
        assert (Path(b['original_fixture'])/'argus/manifest.json').is_file()
        diagnostic_controls.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p),
            target=b['target'],primary_diagnostic=expected,observed_diagnostic=b['observed_diagnostic'],
            original_cleanup_returned=b['original_cleanup']['returned'] is not None))
    helper_closures=[]
    for p in harness.glob('terminal-helper-closure-*.json'):
        b=read(p);assert b['source_sha256']==manifest['tests/thesis_lite/maestro/test_terminal_helper_closure.py']
        assert b['no_writer_rpc_replay'] and not b['full_M1_complete'] and not b['scientific_result']
        assert hashlib.sha256(canonical(b['original_terminal'])).hexdigest()==b['original_terminal_sha256']
        closed=b['closure'];original=Path(b['original_fixture'])
        assert sha(original/'argus/manifest.json')==b['original_manifest_sha256']
        assert closed['root_reaped'] and closed['inventory_complete'] and closed['unacknowledged_births']==0
        assert closed['normal_unit_records_complete'] and closed['authority_fenced']
        assert {h['role'] for h in closed['helpers']}=={3,4,5} and all(h['process_reaped'] for h in closed['helpers'])
        assert all(r['empty'] and r['released'] for r in closed['boundaries'])
        assert all(r['issued'] is False or r['direct_child_reaped'] is True for r in closed['native_units'])
        assert closed['terminal_reports']==[b['original_terminal']] and closed['writers']==[]
        assert not closed['lifecycle_complete'] and not closed['ready_for_execution']
        if b['case']=='closed':assert not closed['diagnostics']
        else:assert b['case'] in ('lost-close-ack','required-missing') and 'ML-CLOSURE-REPORT-INCOMPLETE' in closed['diagnostics']
        helper_closures.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p),case=b['case'],
            original_terminal_sha256=b['original_terminal_sha256'],manifest_sha256=b['original_manifest_sha256']))
    helper_files=[];helper_rows=[]
    for p in harness.glob('terminal-fault-helper-*.json'):
        b=read(p);assert b['source_sha256']==manifest['tests/thesis_lite/maestro/test_terminal_faults.py']
        assert b['original_native_source_sha256']==manifest['src/xverse/maestro/native/bootstrap.c']
        assert b['fixed_fault_code_sha256']==hashlib.sha256(b['fixed_fault_code'].encode()).hexdigest()
        assert not b['production_fault_mode_added'] and b['admission_precedes_birth'] and b['returncode']==0
        command=b['command'];compiled=Path(command[-4]);binary=Path(command[-1])
        assert compiled.name=='bootstrap.c' and binary.name=='run-bootstrap'
        assert sha(compiled)==b['compiled_source_sha256'] and sha(binary)==b['binary_sha256']
        original=(source/'src/xverse/maestro/native/bootstrap.c').read_text()
        anchor='args[2]=\"-m\";args[3]=\"xverse.maestro.persistence_worker\"'
        assert original.count(anchor)==1
        expected=original.replace(anchor,'args[2]=\"-c\";args[3]='+json.dumps(b['fixed_fault_code']))
        assert compiled.read_text()==expected
        assert compiled.stat().st_size<1<<20 and binary.stat().st_size<1<<20
        helper_files.extend((compiled,binary))
        helper_rows.append(dict(receipt=str(p.relative_to(OUT)),receipt_sha256=sha(p),mode=b['mode'],
            binary_sha256=sha(binary),compiled_source_sha256=sha(compiled),fault_code_sha256=b['fixed_fault_code_sha256']))
    if helper_files:
        target=OUT/(phase+'-owned-fault-helpers.tar.gz')
        with target.open('xb') as stream:
            with tarfile.open(fileobj=stream,mode='w:gz') as tar:
                for p in helper_files:tar.add(p,arcname=p.parent.parent.name+'/'+p.parent.name+'/'+p.name,recursive=False)
        helper_archive_sha=sha(target)
    else:helper_archive_sha=None
    timings=[]
    for p in harness.glob('lazy-operations-*.json'):
        b=read(p);assert b['observational_only'] and b['original_assertions_and_bounds_preserved']
        probes=[r for r in b['operations'] if r['kind']=='probe']
        timings.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p),probe_count=len(probes),
            max_probe_seconds=max((r['ended']-r['began'] for r in probes),default=None),
            min_probe_budget_at_entry=min((r['end']-r['began'] for r in probes),default=None),
            min_probe_remaining_at_return=min((r['end']-r['ended'] for r in probes),default=None),
            rpc_diagnostics=[dict(kind=r['kind'],diagnostic=r['diagnostic']) for r in b['operations'] if r['diagnostic']]))
    extra.append(dict(phase=phase,actual_native_writer_failure_controls=native_stage_controls,dependency_delegation_controls=delegation_controls,offline_boundary_controls=offline_controls,primary_diagnostic_controls=diagnostic_controls,actual_terminal_helper_closures=helper_closures,admitted_owned_fault_helpers=helper_rows,helper_archive_sha256=helper_archive_sha,
                      actual_original_rpc_timings=timings))
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
    retain_archive(target,[(p,str(p.relative_to(private))) for p in files])
    index=dict(original_basetemp=str(private),files={str(p.relative_to(private)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files},
               archive_sha256=sha(target))
    index_path=OUT/(phase+'-public-output-index.json')
    if index_path.exists():assert read(index_path)==index
    else:
        with index_path.open('x') as stream:json.dump(index,stream,indent=2);stream.write('\n')
    captures.append(dict(phase=phase,files=len(files),bytes=total,archive_sha256=sha(target),index_sha256=sha(OUT/(phase+'-public-output-index.json'))))
assert EXIT==(0 if all(r['returncode']==0 for r in phases) else 1)
result=dict(observed_original_tool_session=TOOL,observed_tool_terminal_exit=EXIT,phases=phases,
    phase_scope_passed=EXIT==0,full_source_wheel_scope_passed=len(phases)==2 and EXIT==0,original_source_failure_preserved=True,
    owned_fault_helpers_and_timings=extra,
    original_broker_waits=waits,original_roots_absent=roots,actual_source_links=source_links,reader_gaps=gaps,
    externally_pinned_closed_recomputations=external,original_terminal_outcomes=terminal,retained_actual_public_outputs=captures,
    installed_files=len(identity),source_manifest_sha256=sha(OUT/'frozen-inputs.json'),installed_identity_sha256=sha(OUT/'installed-identity.json'),
    source_archive_sha256=sha(archive),wheel_sha256=sha(wheel),auditor_sha256=sha(Path(__file__)),
    original_input_public_pins_captured_before_run=bool(external),
    all_nine_full_runtime_cases_complete=False,full_platform_regression=False,full_M1_complete=False,
    stable_increment17=False,accepted=False,merged=False,canonical_note_edited=False,factory_run_created=False,scientific_result=False)
with (OUT/'verification.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(phases=phases,original_broker_waits=len(waits),absent_roots=len(roots),source_links=source_links,
    external_recomputations=len(external),terminal_outcomes=len(terminal),reader_gaps=len(gaps),full_increment_complete=False)))
