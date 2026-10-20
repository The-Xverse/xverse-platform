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
    label=p.name.removesuffix('-receipt.json');log=out/(label+'.log')
    assert row['returncode']==row['public_capture_returncode']==0 and sha(log)==row['log_sha256']
    assert re.search(r'\b2 passed\b',log.read_text().splitlines()[-1])
    phases.append(dict(phase=row['phase'],passed=2,failed=0,returncode=0))
    harness=out/(label+'-harness')
    for q in harness.glob('maestro-component-*.json'):
        d=read(q);key=(d['parent_path'],d['root_name']);assert key not in seen;seen.add(key)
        assert d['root_removed'] and d['workers_reaped'] and not (Path(d['parent_path'])/d['root_name']).exists()
        roots.append(dict(path=str(q.relative_to(out)),sha256=sha(q)))
    for q in harness.glob('runtime-unknown-birth-*.json'):
        d=read(q);a,b=d['primary_startup'],d['after_external_startup']
        assert a==b and a['birth_attempted'] and not a['registered'] and a['supervisor_reaped'] is None
        assert a['process_returned'] is (d['case']=='pidfd-open-loss')
        assert not a['cleanup_complete'] and not a['ready_for_execution']
        assert not d['dispatch_returned'] and not d['closure_returned'] and not d['cleanup_complete']
        assert d['diagnostics']==['ML-BOOT-LAUNCH-FAILED'] and d['creation_count']==1
        assert d['matching_result_retained'] and d['actual_external_original_wait'] and d['external_descriptor_disposal']
        assert type(d['external_returncode']) is int and d['actual_M1_admissions']==0
        cases.append(dict(path=str(q.relative_to(out)),sha256=sha(q),phase=row['phase'],**d))
    assert not read(out/(label+'-public-evidence-index.json'))
assert len(phases)==2 and {p['phase'] for p in phases}=={'source','wheel'} and len(roots)==len(cases)==4
assert read(out/'collection-receipt.json')['collected']==2 and int(sys.argv[3])==0
result=dict(original_exec_session=int(sys.argv[2]),original_exec_exit=0,phases=phases,root_receipts=roots,cases=cases,
    packaged_sources=81,production_sources_identical_to_startup_ownership_c=True,source_manifest_sha256=sha(out/'frozen-inputs.json'),
    actual_external_original_waits=4,product_unknown_outcomes_preserved=True,matching_result_replay_verified=True,
    actual_M1_admissions=0,actual_service_runtime_runs=0,source_links=0,full_late_birth_matrix=False,
    whole_platform_regression=False,full_M1_complete=False,stable_increment17=False,
    unresolved_findings=[135,222,286,287],accepted=False,merged=False,auditor_sha256=sha(Path(__file__)))
with (out/'verification.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(phases=phases,roots=4,external_waits=4,whole_runtime_unknown_preserved=True)))
