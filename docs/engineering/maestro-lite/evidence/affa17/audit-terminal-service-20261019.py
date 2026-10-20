"""Exact terminal component evidence, never a full lifecycle/acceptance result."""
from pathlib import Path
import hashlib
import json
import sys
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse_xdl.lifecycle import FileEvidenceJournal

OUT=Path(sys.argv[1]).resolve(strict=True)
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=read(OUT/'result-after-wheel.json')
assert result['component_checks_passed'] and result['all_requested_phases_executed']
run=read(OUT/'running.json'); root=Path(run['frozen_source_root'])
manifest=read(OUT/'frozen-inputs.json')
assert all(sha(root/n)==h for n,h in manifest.items())
identity=read(OUT/'installed-identity.json');assert len(identity)==41
assert all(sha(Path(v['file']))==v['sha256']==sha(root/'src/xverse/maestro'/n) for n,v in identity.items())
assert sha(OUT/'dist/xverse_xdl-0.4.0-py3-none-any.whl')==result['wheel_sha256']
roots=[];waits=[];bootstrap=[];services=[];public=[]
for phase in ('source','wheel'):
    receipt=read(OUT/(phase+'-receipt.json'));assert receipt['returncode']==receipt['public_capture_returncode']==0
    log=OUT/(phase+'.log');assert sha(log)==receipt['log_sha256']
    assert str(result['collected_per_phase'])+' passed' in log.read_text()
    directory=OUT/(phase+'-harness')
    for p in directory.glob('maestro-component-*.json'):
        d=read(p);assert d['root_removed'] and d['workers_reaped']
        assert not (Path(d['parent_path'])/d['root_name']).exists()
        roots.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
    for p in directory.glob('run-broker-waits-*.json'):
        d=read(p);assert all(d[k] for k in ('bootstrap_reaped','registered_helpers_reaped','storage_reaped','original_C1_released'))
        waits.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
    for p in directory.glob('bootstrap-children-*.json'):
        d=read(p);assert all(d[k] for k in ('supervisor_reaped','registered_children_reaped','all_original_boundaries_released'))
        assert d['source_sha256']==sha(root/'tests/thesis_lite/maestro/test_bootstrap.py')
        bootstrap.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p),unacknowledged_births=d['unacknowledged_births']))
    for p in directory.glob('run-bootstrap-waits-*.json'):
        d=read(p);assert d['bootstrap_drain']['supervisor_reaped'] and d['original_helpers_actually_reaped'] and d['all_original_C1_released']
        bootstrap.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p)))
    service=list(directory.glob('terminal-service-*.json'));assert len(service)==1
    p=service[0];d=read(p)
    assert d['observed_after']*1e9>max(d['old_bootstrap_lease_ns'],d['old_authority_lease_ns'])
    assert d['issuer_dead'] and d['issuer_reaped'] and d['original_writer_abort_ack'] and d['cancelled_latch_retained']
    assert not d['workload_waits_known'] and not d['full_lifecycle_complete']
    assert d['renewed_bootstrap_leases_ns']==sorted(d['renewed_bootstrap_leases_ns'])
    assert max(d['renewed_bootstrap_leases_ns'])<=d['original_generation_ns']-2_000_000_000
    services.append(dict(path=str(p.relative_to(OUT)),sha256=sha(p),original_writer_ack_past_old_leases=True))
    index=read(OUT/(phase+'-public-evidence-index.json'))
    for entry in index:
        p=OUT/entry['snapshot'];assert sha(p)==entry['sha256'];d=read(p)
        assert d['original_fixture'] and not any(g['source']=='original fixture' for g in d['reader_gaps'])
        original=Path(d['original_fixture'])
        actual_m3=list(FileEvidenceJournal(original/'m3.jsonl').public_records()) if (original/'m3.jsonl').is_file() else []
        actual_events=list(EvidenceStore.read_run(original/'argus').records())
        assert actual_m3==d['m3'] and actual_events==d['argus']
        byseq={r['sequence']:r for r in actual_m3};links=0
        for event in actual_events:
            for ref in event.get('extensions',{}).get('xverse.maestro',{}).get('sourceRefs',[]):
                if ref['kind']=='m3-record':
                    assert ref['sha256']=='sha256:'+hashlib.sha256(canonical_bytes(byseq[ref['sequence']])).hexdigest();links+=1
        assert links==entry['source_links'];public.append(entry)
summary=dict(collected_per_phase=result['collected_per_phase'],source_passed=result['collected_per_phase'],
    installed_wheel_passed=result['collected_per_phase'],wheel_sha256=result['wheel_sha256'],
    original_roots_absent=roots,original_broker_helper_waits=waits,original_bootstrap_receipts=bootstrap,
    terminal_service_controls=services,source_links=sum(e['source_links'] for e in public),
    original_fixtures_lost=0,exact_installed_files=41,source_manifest_sha256=sha(OUT/'frozen-inputs.json'),
    default_receive_hook_control_executed=any("test_bootstrap.py" in n for n in read(OUT/"collection-receipt.json")["command"]),full_terminal_dispatcher_verified=False,full_writer_closure_verified=False,
    deferred_teardown_failure_repaired=False,full_platform_regression=False,full_M1_complete=False,
    stable_increment17=False,accepted=False,merged=False,factory_run_created=False,scientific_result=False)
with (OUT/'verification.json').open('x') as f:f.write(json.dumps(summary,indent=2)+'\n')
print(json.dumps(dict(source=result['collected_per_phase'],wheel=result['collected_per_phase'],roots=len(roots),
    broker_waits=len(waits),bootstrap_receipts=len(bootstrap),source_links=summary['source_links'],old_lease_survival_controls=len(services))))
