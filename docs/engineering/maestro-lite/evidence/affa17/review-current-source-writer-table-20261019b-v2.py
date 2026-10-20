"""Compare existing W-row branch observations; no native execution or gate change."""
import hashlib
import json
from pathlib import Path

from xverse.argus import EvidenceStore

base = Path(__file__).resolve().parent
out = base/'integrated-maestro-20261019b'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
table_path = Path('/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/engineering/successors/ML-DESIGN-2026-10-03-v2/writer-closure-tables.json')
assert sha(table_path)=='2c985f915ccaa84ac8d08eb22597da02add7d361a46633a3ff764e1d89c07e6a'
table = {r['id']:r for r in read(table_path)['stage_rows']}
assert set(table)=={f'W-{n:02d}' for n in range(1,8)}
assert 'healthy' not in json.dumps(table['W-02']).lower()
audit_path = out/'maestro_full-source-terminal-audit/audit.json'
audit = read(audit_path)
assert audit['observed_counts']['passed']==1501 and audit['original_returncode']==0
inventory = {r['path']:r['sha256'] for r in audit['receipt_inventory']}
started = read(out/'maestro_full-source-started.json')
private = Path(started['private_basetemp'])
mapping = {
    'W-01':[('native','fsync-once'),('native','fsync-persistent')],
    'W-02':[('stream','seeded-flush-once'),('stream','seeded-flush-persistent')],
    'W-03':[('stream','close-after')],
    'W-04':[('native','recovery')],
    'W-05':[('native','artifact-check')],
    'W-06':[('native','manifest-replace')],
    'W-07':[('stream','loader-only')],
}
rows = []
for identity,controls in mapping.items():
    observations = []
    for kind,mode in controls:
        module = 'test_terminal_native_writer_failures' if kind=='native' else 'test_native_writer_stream_faults'
        prefix = 'native-writer-result-' if kind=='native' else 'stream-result-'
        path = out/'maestro_full-source-harness'/module/(prefix+mode+'.json')
        assert sha(path)==inventory[str(path.relative_to(out))]
        data = read(path)
        fixture = Path(data['original_fixture'])
        assert fixture.is_relative_to(private)
        trace_path = fixture/('original-writer-faults.jsonl' if kind=='native' else 'owned-stream-public.jsonl')
        trace = [json.loads(line) for line in trace_path.read_text().splitlines()]
        if kind=='native':assert trace==data['trace']
        stage_exit = [r for r in trace if r['operation']=='finalize' and r['result'] in ('raised','returned')]
        assert len(stage_exit)==1 and stage_exit[0]['writer_state'] in table[identity]['possible_state']
        writer = data['receipt']['writer']
        manifest_path = fixture/'argus/manifest.json'
        actual_manifest = EvidenceStore.read_run(fixture/'argus').manifest
        assert sha(manifest_path)==writer['manifest_sha256']
        assert actual_manifest['writerState']==writer['durable_writer_state']
        closure = data['closure']
        assert closure['root_reaped']
        assert all(h['process_reaped'] for h in closure['helpers'])
        assert all(b['empty'] and b['released'] for b in closure['boundaries'])
        assert not data['full_TR03_complete'] and not data['full_TR06_complete']
        assert not data['full_M1_complete'] and not data['private_stream_access']
        if writer['abort_attempted']:
            fresh = next(i for i,r in enumerate(trace) if r['operation']=='flush_buffer' and r['result']=='returned')
            aborted = [i for i,r in enumerate(trace) if r['operation']=='abort' and r['result']=='entered']
            assert len(aborted)==1 and fresh<aborted[0]
            assert writer['abort_usability']=='usable' and writer['abort_completed']
        native_ref = None
        if kind=='stream':
            native_path = fixture/'owned-stream-syscalls.jsonl'
            native = [json.loads(line) for line in native_path.read_text().splitlines()]
            faults = [r for r in native if r['action'].startswith('injected-')]
            if identity=='W-02':
                seed = next(r['observed_ns'] for r in trace if r['operation']=='fixture-annotation' and r['result']=='seed-write-failed')
                returned = next(r['observed_ns'] for r in trace if r['operation']=='finalize-public-flush' and r['result']=='wrapper-returned')
                assert len(faults)>=2 and faults[0]['observed_ns']<seed<returned<faults[1]['observed_ns']
                assert all(r['operation']=='write' and r['native_called']==0 and r['errno']==5 for r in faults)
            elif identity=='W-03':
                assert len(faults)==1 and faults[0]['operation']=='close'
                assert faults[0]['native_called']==1 and faults[0]['native_result']==0 and faults[0]['returned_result']==-1
            else:assert not faults
            native_ref = dict(path=str(native_path),sha256=sha(native_path))
        observations.append(dict(mode=mode,receipt=dict(path=str(path.relative_to(out)),sha256=sha(path)),
            public_trace=dict(path=str(trace_path),sha256=sha(trace_path)),native_trace=native_ref,
            finalize_exit_state=stage_exit[0]['writer_state'],after_policy_state=writer['after_state'],
            abort_usability=writer['abort_usability'],abort_attempted=writer['abort_attempted'],
            abort_completed=writer['abort_completed'],observed_manifest_sha256=sha(manifest_path),
            observed_manifest_state=actual_manifest['writerState'],reader_diagnostics=writer['reader_diagnostics'],
            original_helpers_reaped_and_C1_released=True,
            failed_annotation_seed_precondition=identity=='W-02',healthy_prefix_claim=False))
    rows.append(dict(id=identity,expected_stage=table[identity]['stage'],observations=observations,
        disposition='scoped_branch_support_not_full_runtime_case_closure',full_row_universe_proven=False))
result = dict(schema_version=1,reviewer_sha256=sha(Path(__file__)),source_audit_sha256=sha(audit_path),
    table=dict(path=str(table_path),sha256=sha(table_path)),rows=rows,
    stage_rows_with_scoped_support=7,supporting_control_executions=9,
    W01_persistent_usability_requires_positive_probe=True,
    W02_healthy_prefix_not_stated_in_frozen_row=True,W02_healthy_prefix_demonstrated=False,
    stage_exit_and_post_policy_states_kept_separate=True,
    actual_final_manifest_observations_retained=True,manifest_bytes_at_exact_failure_boundary_retained=False,
    full_TR03_complete=False,full_TR06_complete=False,full_M1_complete=False,
    gate_waiver=False,native_execution_performed=False,product_source_changed=False,
    independent_semantic_confirmation=False,accepted=False,merged=False,scientific_result=False)
with (out/'source-writer-table-review.json').open('x') as stream:
    json.dump(result,stream,indent=2)
    stream.write('\n')
print(json.dumps(dict(stage_rows=7,supporting_controls=9,native_reexecutions=0,
    full_runtime_closure=False,review_sha256=sha(out/'source-writer-table-review.json'))))
