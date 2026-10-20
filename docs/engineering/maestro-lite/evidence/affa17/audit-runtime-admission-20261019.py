"""Audit inert joint-admission checks; no synthetic receipt becomes M1 evidence."""
import hashlib
import json
from pathlib import Path
import re
import sys
import sysconfig
import zipfile

out = Path(sys.argv[1]).resolve(strict=True)
handle, exit_code = int(sys.argv[2]), int(sys.argv[3])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
frozen, running = read(out/'frozen-inputs.json'), read(out/'running.json')
root = Path(running['frozen_source_root'])
assert all(sha(root/n) == h for n,h in frozen.items())
prior = read(out.parent/'composed-issuer-loss-20261019c/frozen-inputs.json')
assert all(prior[n] == h for n,h in frozen.items() if n.startswith('src/') and n in prior)
added = [n for n in frozen if n.startswith('src/') and n not in prior]
assert added == ['src/xverse/maestro/runtime_admission.py']
installed = Path(sysconfig.get_path('purelib'))
packaged = []
with zipfile.ZipFile(out/'dist/xverse_xdl-0.4.0-py3-none-any.whl') as wheel:
    for n,h in frozen.items():
        if n.startswith('src/') and n.endswith(('.py','.c')):
            entry = n.removeprefix('src/')
            assert hashlib.sha256(wheel.read(entry)).hexdigest() == h == sha(installed/entry)
            packaged.append(entry)
assert len(packaged) == 77
phases, roots = [], []
seen = set()
for path in sorted(out.glob('*-receipt.json')):
    receipt = read(path)
    if 'cohort' not in receipt:
        continue
    label = path.name.removesuffix('-receipt.json')
    log = out/(label+'.log')
    assert sha(log) == receipt['log_sha256'] and receipt['public_capture_returncode'] == 0
    last = log.read_text().splitlines()[-1]
    counts = {k:int(m.group(1)) if (m:=re.search(r'(\d+) '+k,last)) else 0 for k in ('passed','failed','errors')}
    assert (receipt['returncode'] == 0) == (counts['failed'] == counts['errors'] == 0)
    phases.append(dict(cohort=receipt['cohort'],phase=receipt['phase'],returncode=receipt['returncode'],**counts))
    harness = out/(label+'-harness')
    for p in harness.glob('maestro-component-*.json'):
        row = read(p); identity = row['parent_path'],row['root_name']
        assert identity not in seen; seen.add(identity)
        assert row['root_removed'] and row['workers_reaped']
        assert not (Path(row['parent_path'])/row['root_name']).exists()
        roots.append(dict(path=str(p.relative_to(out)),sha256=sha(p),
            scope='empty owned parent reservation only; not runtime/helper/M1 evidence'))
    assert not list(harness.glob('run-broker-waits-*.json'))
    assert read(out/(label+'-public-evidence-index.json')) == []
counts = {phase:{k:sum(r[k] for r in phases if r['phase']==phase) for k in ('passed','failed','errors')}
    for phase in ('source','wheel')}
if out.name.endswith('19a'):
    assert counts == {p:dict(passed=0,failed=0,errors=35) for p in ('source','wheel')}
    assert len(roots) == 70 and (out/'regression-not-executed.json').exists()
    assert read(out/'collection-receipt.json')['collected'] == 141
    for phase in ('source','wheel'):
        assert 'ML-COVERAGE-RUNTIME-SCHEDULE-SOURCE' in (out/('runtime_admission-'+phase+'.log')).read_text()
else:
    assert counts == {p:dict(passed=146,failed=0,errors=0) for p in ('source','wheel')}
    assert len(roots) == 80 and read(out/'collection-receipt.json')['collected'] == 146
    assert {r['cohort'] for r in phases} == {'runtime_admission','admission','preparation','run_bootstrap_values'}
    assert all(r['passed']==40 for r in phases if r['cohort']=='runtime_admission')
test = root/'tests/thesis_lite/maestro/test_runtime_admission.py'
assert 'SYNTHETIC-NOT-EXECUTED:' in test.read_text()
assert 'synthetic-bootstrap-authorization' in test.read_text()
assert 'ready_for_execution' in test.read_text()
assert exit_code == (0 if all(r['returncode']==0 for r in phases) else 1)
result = dict(original_exec_session=handle,original_exec_exit=exit_code,phases=phases,counts=counts,
    packaged_sources=77,all_76_previous_production_sources_unchanged=True,added_production_sources=added,
    root_receipts=roots,original_source_manifest_sha256=sha(out/'frozen-inputs.json'),auditor_sha256=sha(Path(__file__)),
    unit_attestations='SYNTHETIC_INERT_NOT_M1_RECEIPTS',empty_parent_reservations=len(roots),
    actual_runtime_contexts=0,actual_runtime_helpers=0,actual_M1_admissions=0,
    public_start_implemented=False,live_artifact_facility_validation_complete=False,
    full_M1_complete=False,whole_platform_regression=False,stable_increment17=False,accepted=False,merged=False)
with (out/'verification.json').open('x') as stream:
    json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(counts=counts,packaged_sources=77,empty_reservations=len(roots),actual_M1_admissions=0)))
