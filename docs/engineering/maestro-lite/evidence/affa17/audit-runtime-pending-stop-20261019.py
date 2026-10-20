"""Original pending stop routes; normal locks/views never substitute for cleanup."""
import hashlib,json,re,sys,sysconfig,zipfile
from pathlib import Path
out=Path(sys.argv[1]).resolve(strict=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_bytes())
frozen=read(out/'frozen-inputs.json');root=Path(read(out/'running.json')['frozen_source_root']);assert all(sha(root/n)==h for n,h in frozen.items())
prior=read(out.parent/'startup-ownership-20261019c/frozen-inputs.json')
assert {n:h for n,h in prior.items() if n.startswith('src/')}=={n:h for n,h in frozen.items() if n.startswith('src/')}
installed=Path(sysconfig.get_path('purelib'));count=0
with zipfile.ZipFile(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl') as wheel:
    for n,h in frozen.items():
        if n.startswith('src/') and n.endswith(('.py','.c')):
            entry=n.removeprefix('src/');assert hashlib.sha256(wheel.read(entry)).hexdigest()==h==sha(installed/entry);count+=1
assert count==81
phases=[];roots=[];cases=[];seen=set()
for p in sorted(out.glob('*-receipt.json')):
    receipt=read(p)
    if 'cohort' not in receipt:continue
    label=p.name.removesuffix('-receipt.json');log=out/(label+'.log')
    assert receipt['returncode']==receipt['public_capture_returncode']==0 and sha(log)==receipt['log_sha256']
    assert re.search(r'\b3 passed\b',log.read_text().splitlines()[-1])
    phases.append(dict(phase=receipt['phase'],passed=3,failed=0,returncode=0));harness=out/(label+'-harness')
    for q in harness.glob('maestro-component-*.json'):
        d=read(q);identity=(d['parent_path'],d['root_name']);assert identity not in seen;seen.add(identity)
        assert d['root_removed'] and d['workers_reaped'] and not (Path(d['parent_path'])/d['root_name']).exists();roots.append(dict(path=str(q.relative_to(out)),sha256=sha(q)))
    for q in harness.glob('pending-stop-*.json'):
        d=read(q);a=d['startup'];assert d['route'] in ('direct','registry','registry-view-loss')
        assert d['run_lock_held'] and d['startup_lock_held'] and d['matching_stop_retained'] and d['stop_epoch']==1
        assert d['normal_registry_lock_held'] is (d['route']!='direct') and d['ordinary_registry_view_lost'] is (d['route']=='registry-view-loss')
        assert d['stop_end_ns']>=d['stop_begin_ns'] and d['no_returned_capability_at_stop'] and d['foreign_id_rejected']
        assert d['primary_original_root_wait'] and d['creation_count']==1 and not d['start_errors']
        assert not d['dispatch_returned'] and not d['closure_returned'] and d['execution_succeeded'] is None and not d['cleanup_complete']
        assert a['birth_attempted'] and a['process_returned'] and a['supervisor_reaped'] and not a['registered']
        assert a['registered_helpers_reaped'] is None and a['unacknowledged_births'] is None
        assert d['diagnostics']==['ML-BOOT-LAUNCH-CANCELLED'] and d['matching_result_retained'] and d['collection_absent']
        assert d['actual_M1_admissions']==0
        cases.append(dict(path=str(q.relative_to(out)),sha256=sha(q),phase=receipt['phase'],**d))
    assert not read(out/(label+'-public-evidence-index.json'))
assert len(phases)==2 and {p['phase'] for p in phases}=={'source','wheel'} and len(roots)==len(cases)==6
assert read(out/'collection-receipt.json')['collected']==3 and int(sys.argv[3])==0
result=dict(original_exec_session=int(sys.argv[2]),original_exec_exit=0,phases=phases,root_receipts=roots,cases=cases,packaged_sources=81,
    production_sources_identical_to_startup_ownership_c=True,source_manifest_sha256=sha(out/'frozen-inputs.json'),actual_M1_admissions=0,
    actual_service_runtime_runs=0,source_links=0,whole_platform_regression=False,full_M1_complete=False,stable_increment17=False,
    unresolved_findings=[135,222,286,287],accepted=False,merged=False,auditor_sha256=sha(Path(__file__)))
with (out/'verification.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(phases=phases,owned_roots_removed=6,original_product_waits=6,normal_lock_independence_verified=True)))
