"""Verify actual late-return and honest unknown-birth facts without product promotion."""
import hashlib,json,re,sys,sysconfig,zipfile
from pathlib import Path
out=Path(sys.argv[1]).resolve(strict=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_bytes())
frozen=read(out/'frozen-inputs.json');running=read(out/'running.json');source=Path(running['frozen_source_root'])
assert all(sha(source/n)==h for n,h in frozen.items())
prior=read(out.parent/'startup-ownership-20261019c/frozen-inputs.json')
assert {n:h for n,h in prior.items() if n.startswith('src/')}=={n:h for n,h in frozen.items() if n.startswith('src/')}
installed=Path(sysconfig.get_path('purelib'));packaged=[]
with zipfile.ZipFile(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl') as wheel:
    for name,digest in frozen.items():
        if name.startswith('src/') and name.endswith(('.py','.c')):
            entry=name.removeprefix('src/');assert hashlib.sha256(wheel.read(entry)).hexdigest()==digest==sha(installed/entry);packaged.append(entry)
assert len(packaged)==81
phases=[];roots=[];cases=[];seen=set()
for p in sorted(out.glob('*-receipt.json')):
    row=read(p)
    if 'cohort' not in row:continue
    label=p.name.removesuffix('-receipt.json');log=out/(label+'.log');assert row['returncode']==row['public_capture_returncode']==0 and sha(log)==row['log_sha256']
    last=log.read_text().splitlines()[-1];assert re.search(r'\b4 passed\b',last) and 'failed' not in last and 'error' not in last
    phases.append(dict(phase=row['phase'],passed=4,failed=0,returncode=0))
    harness=out/(label+'-harness')
    for q in harness.glob('maestro-component-*.json'):
        d=read(q);key=(d['parent_path'],d['root_name']);assert key not in seen;seen.add(key)
        assert d['root_removed'] and d['workers_reaped'] and not (Path(d['parent_path'])/d['root_name']).exists();roots.append(dict(path=str(q.relative_to(out)),sha256=sha(q)))
    for q in harness.glob('late-birth-*.json'):
        d=read(q);case=d['case'];a,b=d['primary'],d['after_external_cleanup'];known=case in ('late-return','cancel-before-return')
        assert d['creation_count']==1 and len(d['launch_errors'])==1 and d['actual_M1_admissions']==0 and d['actual_original_root_wait']
        assert a==b and a['birth_attempted'] and not a['registered'] and not a['cleanup_complete'] and not a['ready_for_execution']
        assert a['process_returned'] is (case!='birth-exception') and a['supervisor_reaped'] is (True if known else None)
        assert a['registered_helpers_reaped'] is None and a['unacknowledged_births'] is None
        assert d['actual_product_wait'] is known and d['product_disposed'] is known
        assert d['external_root_cleanup'] is (not known) and d['external_descriptor_disposal'] is (not known)
        assert a['diagnostic']==('ML-OWNER-DEADLINE' if case=='late-return' else 'ML-BOOT-LAUNCH-CANCELLED' if case=='cancel-before-return' else 'ML-BOOT-LAUNCH-FAILED')
        if case=='late-return':assert d['original_return_ns']>d['original_start_end_ns']>d['original_birth_ns']
        if case=='birth-exception':assert d['original_return_ns'] is None
        cases.append(dict(path=str(q.relative_to(out)),sha256=sha(q),phase=row['phase'],**d))
    assert not read(out/(label+'-public-evidence-index.json'))
assert len(phases)==2 and len(roots)==len(cases)==8
assert {r['phase'] for r in phases}=={'source','wheel'}
assert read(out/'collection-receipt.json')['collected']==4
result=dict(original_exec_session=int(sys.argv[2]),original_exec_exit=int(sys.argv[3]),phases=phases,root_receipts=roots,cases=cases,
    packaged_sources=81,production_sources_identical_to_startup_ownership_c=True,source_manifest_sha256=sha(out/'frozen-inputs.json'),
    product_original_waits=sum(r['actual_product_wait'] for r in cases),external_original_waits=sum(r['external_root_cleanup'] for r in cases),
    unknown_outcomes_preserved_after_external_reap=True,implicit_replay_or_adoption=False,
    actual_M1_admissions=0,actual_service_runtime_runs=0,source_links=0,full_late_birth_matrix=False,whole_platform_regression=False,
    full_M1_complete=False,stable_increment17=False,unresolved_findings=[135,222,286,287],accepted=False,merged=False,auditor_sha256=sha(Path(__file__)))
assert result['original_exec_exit']==0 and result['product_original_waits']==result['external_original_waits']==4
with (out/'verification.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(phases=phases,roots=8,actual_original_waits=8,product_waits=4,external_waits=4,unknown_outcomes_preserved=True)))
