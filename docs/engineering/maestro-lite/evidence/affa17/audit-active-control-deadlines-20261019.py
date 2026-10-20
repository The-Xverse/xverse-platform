"""Read-only original-input audit; never reopens the original writer."""
import ast
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

out = Path(sys.argv[1]).resolve(strict=True)
handle, exit_code = int(sys.argv[2]), int(sys.argv[3])
read = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
frozen = read(out / 'frozen-inputs.json')
running = read(out / 'running.json')
source = Path(running['frozen_source_root'])
assert all(sha(source / name) == value for name, value in frozen.items())
installed = Path(sysconfig.get_path('purelib'))
wheel_path = out / 'dist/xverse_xdl-0.4.0-py3-none-any.whl'
packaged = []
with zipfile.ZipFile(wheel_path) as wheel:
    for name, value in frozen.items():
        if name.startswith('src/') and name.endswith(('.py', '.c')):
            entry = name.removeprefix('src/')
            assert hashlib.sha256(wheel.read(entry)).hexdigest() == value == sha(installed / entry)
            packaged.append(entry)
assert len(packaged) == 76
prior = read(out.parent / 'active-controller-recovery-20261019d/frozen-inputs.json')
assert [name for name in frozen if name.startswith('src/') and frozen[name] != prior.get(name)] == ['src/xverse/maestro/dispatcher.py']
prior_source = Path(read(out.parent / 'active-controller-recovery-20261019d/running.json')['frozen_source_root'])
old = ast.parse((prior_source / 'src/xverse/maestro/dispatcher.py').read_text())
new = ast.parse((source / 'src/xverse/maestro/dispatcher.py').read_text())
method = next(n for n in ast.walk(new) if isinstance(n, ast.FunctionDef) and n.name == '_drain_restart')
guards = [n for n in method.body if isinstance(n, ast.Try)][0].body
check = guards.pop(2)
assert ast.dump(check) == ast.dump(ast.parse('if self.owner.latch.cancelled:\n    raise OwnerError("ML-SCHEDULE-CANCELLED")').body[0])
assert ast.dump(old) == ast.dump(new), 'unreviewed production delta'
expected = read(out / 'collection-receipt.json')['collected']
assert expected == 13 and exit_code == 0
phases, cases, roots, waits, snapshots, retained = [], [], [], [], [], []
seen_roots = set()
for phase in ('source', 'wheel'):
    receipt = read(out / (phase + '-receipt.json'))
    log = out / (phase + '.log')
    assert sha(log) == receipt['log_sha256'] and receipt['public_capture_returncode'] == receipt['returncode'] == 0
    summary = log.read_text().splitlines()[-1]
    counts = {key:int(m.group(1)) if (m := re.search(r'(\d+) ' + key, summary)) else 0
              for key in ('passed', 'failed', 'errors')}
    assert counts == dict(passed=13, failed=0, errors=0)
    phases.append(dict(phase=phase, **counts))
    harness = out / (phase + '-harness')
    for path in harness.glob('maestro-component-*.json'):
        row = read(path)
        identity = row['parent_path'], row['root_name']
        assert identity not in seen_roots
        seen_roots.add(identity)
        assert row['root_removed'] and row['workers_reaped']
        assert not (Path(row['parent_path']) / row['root_name']).exists()
        roots.append(dict(path=str(path.relative_to(out)), sha256=sha(path)))
    for path in harness.glob('run-broker-waits-*.json'):
        row = read(path)
        assert all(row[k] for k in ('bootstrap_reaped', 'registered_helpers_reaped', 'storage_reaped', 'original_C1_released'))
        waits.append(dict(path=str(path.relative_to(out)), sha256=sha(path)))
    for item in read(out / (phase + '-public-evidence-index.json')):
        assert sha(out / item['snapshot']) == item['sha256'] and not item['reader_gaps']
        projection = read(out / item['snapshot'])
        fixture = Path(projection['original_fixture'])
        assert not fixture.is_symlink()
        assert projection['m3'] == list(FileEvidenceJournal(fixture / 'm3.jsonl').public_records())
        assert projection['argus'] == list(EvidenceStore.read_run(fixture / 'argus').records())
        snapshots.append(dict(phase=phase, **item))
    compiled = read(harness / 'recovery-workload.json')
    assert compiled['source_sha256'] == frozen['tests/thesis_lite/maestro/catalog_workload_current.c']
    assert compiled['binary_sha256'] == sha(harness / 'recovery-workload.bin')
    for control in ('restart', 'recovery'):
        for mode in ('past', 'foreign-session', 'beyond-active', 'expire-queued', 'cancel-queued'):
            case = control + '-' + mode
            path = harness / ('control-deadline-' + case + '.json')
            pin_path = harness / ('control-deadline-inputs-' + case + '.json')
            row, pin = read(path), read(pin_path)
            assert row['source_sha256'] == pin['source_sha256'] == frozen['tests/thesis_lite/maestro/test_active_control_deadlines.py']
            assert row['original_fixture'] == pin['original_fixture']
            admission = CoverageAdmission(canonical(pin['original_admission']))
            body = admission.data(pin['admission_digest'])
            plan = decode_collection(pin['original_collection'], admission, pin['admission_digest'])
            assert runtime_admission_digest(admission, plan, pin['generation_ns']) == pin['runtime_digest']
            schedule = pin['original_schedule']
            assert 'sha256:' + hashlib.sha256(canonical(schedule)).hexdigest() in body['sourceDigests']
            assert schedule['version'] == 5 and schedule['active_seconds'] == 20
            assert schedule['restart_operation_seconds'] == 2 and schedule['recovery_operation_seconds'] == 3
            assert len(body['units']) == 4 and len(body['contexts']) == 8
            fixture = Path(row['original_fixture'])
            m3 = list(FileEvidenceJournal(fixture / 'm3.jsonl').public_records())
            assert m3 == row['public_m3'] and {r['details']['generation'] for r in m3} == {1}
            assert len(row['queue']) == 1 and row['queue'][0]['before'] == row['queue'][0]['after']
            assert all(t['before'] == t['after'] for t in row['transitions'])
            queue = row['queue'][0]
            if mode in ('expire-queued', 'cancel-queued'):
                assert len(row['tickets']) == len(row['outcomes']) == 1 and not row['errors']
                outcome = row['outcomes'][0]
                assert outcome['disposition'] == 'rejected'
                assert any(t['outcome'] == outcome for t in row['transitions'])
                if mode == 'expire-queued':
                    assert queue['queued_at'] < queue['end']['monotonic_seconds'] <= queue['expired_at']
                    assert outcome['diagnostic'] == 'ML-SCHEDULE-' + ('RESTART' if control == 'restart' else 'RECOVERY') + '-DEADLINE'
                else:
                    assert queue['cancel_thread'] != queue['coordinator_thread']
                    assert queue['after_cancel']['authority_sequence'] > queue['after']['authority_sequence']
            else:
                assert len(row['errors']) == 1 and not row['tickets'] and not row['transitions']
                if mode == 'past':
                    assert queue['end']['monotonic_seconds'] < queue['queued_at']
                elif mode == 'foreign-session':
                    assert queue['end']['session'] != body['hostSession']
                else:
                    assert queue['end']['monotonic_seconds'] > queue['active_end']
            assert queue['active_end'] <= body['end'] and queue['work_end'] > queue['active_end']
            closure = row['closure']
            assert closure['root_reaped'] and closure['cleanup_complete']
            assert all(h['process_reaped'] for h in closure['helpers'])
            assert all(b['empty'] and b['released'] for b in closure['boundaries'])
            assert sum(h['role'] == 5 for h in closure['helpers']) == 1
            assert not closure['lifecycle_complete'] and not closure['ready_for_execution']
            checked = verify_runtime_closed(admission, plan, fixture / 'argus',
                expected_admission_digest=pin['admission_digest'], generation_ns=pin['generation_ns'],
                expected_runtime_digest=pin['runtime_digest'])
            if mode == 'cancel-queued':
                assert not row['execution_succeeded'] and row['diagnostic'] == 'ML-SCHEDULE-CANCELLED'
            else:
                assert row['execution_succeeded'] and row['diagnostic'] is None and checked.complete
                public = fixture / 'argus'
                assert not any(p.is_symlink() for p in public.rglob('*'))
                original = {str(p.relative_to(public)):sha(p) for p in public.rglob('*') if p.is_file()}
                destination = out / 'closed-public' / (phase + '-' + case)
                destination.parent.mkdir(exist_ok=True)
                assert not destination.exists()
                shutil.copytree(public, destination)
                assert {str(p.relative_to(destination)):sha(p) for p in destination.rglob('*') if p.is_file()} == original
                assert verify_runtime_closed(admission, plan, destination,
                    expected_admission_digest=pin['admission_digest'], generation_ns=pin['generation_ns'],
                    expected_runtime_digest=pin['runtime_digest']).complete
                retained.append(dict(phase=phase, case=case, path=str(destination.relative_to(out)), files=original))
            cases.append(dict(phase=phase, control=control, mode=mode, receipt_sha256=sha(path),
                original_inputs_sha256=sha(pin_path), independent_closed_complete=checked.complete,
                execution_succeeded=row['execution_succeeded'], diagnostic=row['diagnostic']))
assert len(cases) == len(waits) == len(snapshots) == 20 and len(retained) == 16
result = dict(original_exec_session=handle, original_exec_exit=exit_code, phases=phases, cases=cases,
    production_delta_only_cancellation_preflight=True,
    packaged_sources=packaged, original_root_receipts=roots, original_wait_receipts=waits, snapshots=snapshots,
    source_links=sum(s['source_links'] for s in snapshots), retained_closed_public=retained,
    source_manifest_sha256=sha(out / 'frozen-inputs.json'), wheel_sha256=sha(wheel_path),
    auditor_sha256=sha(Path(__file__)), full_increment17_complete=False, full_M1_complete=False,
    whole_platform_regression=False, accepted=False, merged=False)
with (out / 'verification.json').open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(phases=phases, cases=len(cases), roots=len(roots), waits=len(waits),
    source_links=result['source_links'], preserved_closed_roots=len(retained))))
