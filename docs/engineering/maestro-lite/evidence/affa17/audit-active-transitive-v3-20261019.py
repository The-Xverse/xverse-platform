"""Read original cohort inputs and native observations without rewriting evidence."""
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

out = Path(sys.argv[1]).resolve(strict=True)
handle, original_exit = int(sys.argv[2]), int(sys.argv[3])
read = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
running = read(out / 'running.json')
frozen = read(out / 'frozen-inputs.json')
source = Path(running['frozen_source_root'])
assert all(sha(source / name) == value for name, value in frozen.items())
identity = read(out / 'installed-identity.json')
assert len(identity) == 46
assert all(sha(Path(row['file'])) == row['sha256'] == frozen['src/xverse/maestro/' + name]
           for name, row in identity.items())
installed = Path(sysconfig.get_path('purelib'))
packaged = []
wheel_path = out / 'dist/xverse_xdl-0.4.0-py3-none-any.whl'
with zipfile.ZipFile(wheel_path) as wheel:
    for name, value in frozen.items():
        if name.startswith('src/') and name.endswith(('.py', '.c')):
            entry = name.removeprefix('src/')
            assert hashlib.sha256(wheel.read(entry)).hexdigest() == value == sha(installed / entry)
            packaged.append(entry)
assert len(packaged) == 76
phases, cases, waits, roots, snapshots = [], [], [], [], []
collected = read(out / 'collection-receipt.json')['collected']
assert collected == 56
for phase in ('source', 'wheel'):
    receipt = read(out / (phase + '-receipt.json'))
    log = out / (phase + '.log')
    assert sha(log) == receipt['log_sha256'] and receipt['public_capture_returncode'] == 0
    summary = log.read_text().splitlines()[-1]
    counts = {name: int(m.group(1)) if (m := re.search(r'(\d+) ' + name, summary)) else 0
              for name in ('passed', 'failed', 'errors')}
    assert sum(counts.values()) == collected
    assert (receipt['returncode'] == 0) == (counts['failed'] == counts['errors'] == 0)
    phases.append(dict(phase=phase, returncode=receipt['returncode'], **counts))
    harness = out / (phase + '-harness')
    for path in harness.glob('run-broker-waits-*.json'):
        row = read(path)
        assert all(row[key] for key in ('bootstrap_reaped', 'registered_helpers_reaped',
                                        'storage_reaped', 'original_C1_released'))
        waits.append(dict(path=str(path.relative_to(out)), sha256=sha(path)))
    for path in harness.glob('maestro-component-*.json'):
        row = read(path)
        assert row['root_removed'] and row['workers_reaped']
        assert not (Path(row['parent_path']) / row['root_name']).exists()
        roots.append(dict(path=str(path.relative_to(out)), sha256=sha(path)))
    for row in read(out / (phase + '-public-evidence-index.json')):
        assert sha(out / row['snapshot']) == row['sha256']
        snapshots.append(dict(phase=phase, **row))
    compiled = read(harness / 'cohort-workload.json')
    assert compiled['source_sha256'] == frozen['tests/thesis_lite/maestro/catalog_workload_current.c']
    assert compiled['binary_sha256'] == sha(harness / 'cohort-workload.bin')
    for mode in ('cohort', 'omitted-dependent', 'mid-storage-loss', 'cleaned-leaf'):
        path = harness / ('cohort-' + mode + '.json')
        pin_path = harness / ('cohort-inputs-' + mode + '.json')
        row, pin = read(path), read(pin_path)
        assert row['source_sha256'] == pin['source_sha256'] == frozen['tests/thesis_lite/maestro/test_active_transitive_restart.py']
        assert row['original_fixture'] == pin['original_fixture']
        schedule = pin['original_schedule']
        assert schedule['version'] == 4 and schedule['use_action_timeouts'] is True
        assert schedule['operation_seconds'] == .3 and schedule['active_seconds'] == 20
        assert schedule['restart_operation_seconds'] == schedule['per_unit_seconds'] == 2
        assert len(schedule['action_timeouts']) == 20
        admission = CoverageAdmission(canonical(pin['original_admission']))
        body = admission.data(pin['admission_digest'])
        assert 'sha256:' + hashlib.sha256(canonical(schedule)).hexdigest() in body['sourceDigests']
        plan = decode_collection(pin['original_collection'], admission, pin['admission_digest'])
        assert runtime_admission_digest(admission, plan, pin['generation_ns']) == pin['runtime_digest']
        assert len(body['units']) == 4 and len(body['contexts']) == 8
        chosen, outcomes = row['chosen'], row['outcomes']
        assert len(chosen) == len(outcomes) == len(row['tickets'])
        assert all(ticket['generation'] == 2 and ticket['deadline']['monotonic_seconds'] <= body['end']
                   for ticket in row['tickets'])
        assert row['unrelated'] not in chosen
        fixture = Path(row['original_fixture'])
        m3 = list(FileEvidenceJournal(fixture / 'm3.jsonl').public_records())
        assert m3 == row['public_m3']
        for observation in row['live_unrelated']:
            assert observation['handle'] == row['old_handles'][row['unrelated']]
        assert not row['full_selected_increment17_complete'] and not row['scientific_result']
        checked = None
        if mode == 'omitted-dependent':
            assert [r['disposition'] for r in outcomes] == ['rejected', 'rejected']
            assert all(r['diagnostic'] == 'ML-GENERATION-DEPENDENTS' for r in outcomes)
            assert not row['prepared_order'] and {r['details']['generation'] for r in m3} == {1}
        elif mode == 'mid-storage-loss':
            assert [r['disposition'] for r in outcomes] == ['completed', 'failed', 'cancelled']
            assert row['prepared_order'] == chosen[:2] and row['diagnostic']
        else:
            assert all(r['disposition'] == 'completed' for r in outcomes)
            assert row['prepared_order'] == chosen
            for unit, result in zip(chosen, outcomes):
                execution = next(c['executionId'] for c in body['contexts']
                                 if c['unitId'] == unit and c['generation'] == 2)
                assert result['execution_id'] == execution != row['old_handles'][unit]['execution_id']
                for generation in (1, 2):
                    cleaned = [r for r in m3 if r['details']['maestroUnitId'] == unit
                               and r['details']['generation'] == generation
                               and r['kind'] == 'outcome' and r['status'] == 'cleaned']
                    assert len(cleaned) == 1
            if mode == 'cohort':
                old_cleaned = [r['details']['maestroUnitId'] for r in m3
                               if r['details']['generation'] == 1 and r['kind'] == 'outcome'
                               and r['status'] == 'cleaned' and r['details']['maestroUnitId'] in chosen]
                assert old_cleaned == list(reversed(chosen))
                events = EvidenceStore.read_run(fixture / 'argus').records()
                for unit, parents in ((chosen[1], chosen[:1]), (chosen[2], chosen[:2])):
                    ready = [e['extensions']['xverse.maestro'] for e in events
                             if e.get('extensions', {}).get('xverse.maestro', {}).get('unitId') == unit
                             and e['extensions']['xverse.maestro'].get('generation') == 2
                             and e['extensions']['xverse.maestro'].get('action') == 'ready']
                    assert len(ready) == 1 and {d['unitId'] for d in ready[0]['dependencies']} == set(parents)
                    assert all(d['generation'] == 2 for d in ready[0]['dependencies'])
        operations = read(next(harness.glob('lazy-operations-*all_generations-' + mode + '.json')))['operations']
        for bound in row['statement_bounds']:
            observed = [o for o in operations if o['kind'] == 'schedule'
                        and o['action'] == bound['kind'] and o['step'] == bound['step']]
            assert len(observed) == 1 and observed[0]['end'] == bound['end']
            assert 0 < bound['remaining'] <= bound['cap']
            assert observed[0]['end'] - observed[0]['began'] <= bound['cap']
        if mode != 'mid-storage-loss' and row['diagnostic'] is None:
            final = next(b for b in row['statement_bounds'] if b['kind'] == 'step-complete'
                         and b['step'] == 'cleanup-unrelated')
            assert schedule['operation_seconds'] < final['remaining'] <= final['cap'] == 1
        for ticket in row['tickets']:
            unit = ticket['unit_id']
            generation = next((i for i, o in enumerate(operations)
                               if o['kind'] == 'generation' and o['unit'] == unit), None)
            if generation is None:
                continue
            end = operations[generation]['end']
            assert 0 < end - operations[generation]['began'] <= schedule['restart_operation_seconds']
            assert end <= ticket['deadline']['monotonic_seconds']
            for observed in operations[generation:]:
                if observed['kind'] == 'probe' and observed['unit'] == unit and observed['generation'] == 2:
                    assert observed['end'] == end
                    break
                if observed['diagnostic']:
                    break
                assert observed['end'] == end
        closure = row['closure']
        if closure is not None:
            assert closure['root_reaped'] and all(h['process_reaped'] for h in closure['helpers'])
            assert all(b['empty'] and b['released'] for b in closure['boundaries'])
            assert not closure['lifecycle_complete'] and not closure['ready_for_execution']
            cleanup_complete = (closure['inventory_complete'] and closure['root_reaped']
                and closure['unacknowledged_births'] == 0
                and all(h['process_reaped'] and (h['role'] not in (1, 4) or h['direct_child_reaped']) for h in closure['helpers'])
                and all(b['empty'] and b['released'] for b in closure['boundaries'])
                and (not any(h['role'] == 4 for h in closure['helpers']) or closure['authority_fenced'] is True))
            if mode == 'mid-storage-loss':
                assert not cleanup_complete
                assert 'ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN' in closure['diagnostics']
        if mode != 'mid-storage-loss' and row['diagnostic'] is None:
            checked = verify_runtime_closed(admission, plan, fixture / 'argus',
                expected_admission_digest=pin['admission_digest'], generation_ns=pin['generation_ns'],
                expected_runtime_digest=pin['runtime_digest'])
            assert checked.complete and cleanup_complete and closure['normal_unit_records_complete']
            assert row['terminal']['report']['eligible'] and row['terminal']['writer']['evidence_complete']
            assert row['terminal']['writer']['durable_writer_state'] == 'closed'
            for declaration in plan.declarations:
                assert (fixture / 'argus' / declaration.destination).read_bytes() == b'EXEC\n'
        cases.append(dict(phase=phase, mode=mode, dispositions=[r['disposition'] for r in outcomes],
                          diagnostic=row['diagnostic'], receipt_sha256=sha(path), inputs_sha256=sha(pin_path),
                          independent_closed_complete=bool(checked and checked.complete)))
assert len(waits) == len(roots) == 32 and len(cases) == 8
passed = all(p['returncode'] == 0 for p in phases)
assert original_exit == (0 if passed else 1)
result = dict(original_exec_session=handle, original_exec_exit=original_exit, phases=phases, cases=cases,
              wait_receipts=waits, root_receipts=roots, snapshots=snapshots, packaged_sources=len(packaged),
              source_links=sum(s['source_links'] for s in snapshots),
              independent_closed_complete=sum(c['independent_closed_complete'] for c in cases),
              source_manifest_sha256=sha(out / 'frozen-inputs.json'), wheel_sha256=sha(wheel_path),
              auditor_sha256=sha(Path(__file__)), component_scope_passed=passed,
              full_selected_increment17_complete=False, full_M1_complete=False,
              whole_platform_regression=False, accepted=False, merged=False)
with (out / 'verification.json').open('x') as stream:
    json.dump(result, stream, indent=2); stream.write('\n')
print(json.dumps({key: result[key] for key in ('phases', 'source_links', 'packaged_sources',
                                              'independent_closed_complete', 'component_scope_passed')}))
