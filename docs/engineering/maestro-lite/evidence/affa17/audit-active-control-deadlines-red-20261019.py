"""Retain the original cancellation-classification counterexample unchanged."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

out = Path(sys.argv[1]).resolve(strict=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
frozen = read(out / 'frozen-inputs.json')
root = Path(read(out / 'running.json')['frozen_source_root'])
assert all(sha(root / n) == h for n, h in frozen.items())
with zipfile.ZipFile(out / 'dist/xverse_xdl-0.4.0-py3-none-any.whl') as wheel:
    packaged = [n for n in frozen if n.startswith('src/') and n.endswith(('.py', '.c'))]
    assert len(packaged) == 76
    assert all(hashlib.sha256(wheel.read(n.removeprefix('src/'))).hexdigest() == frozen[n] for n in packaged)
phases, counterexamples, roots, waits, snapshots = [], [], [], [], []
for phase in ('source', 'wheel'):
    receipt = read(out / (phase + '-receipt.json'))
    assert receipt['returncode'] == 1 and receipt['public_capture_returncode'] == 0
    log = out / (phase + '.log')
    assert sha(log) == receipt['log_sha256'] and '1 failed, 12 passed' in log.read_text().splitlines()[-1]
    phases.append(dict(phase=phase, passed=12, failed=1))
    harness = out / (phase + '-harness')
    path = harness / 'control-deadline-restart-cancel-queued.json'
    row = read(path)
    assert row['outcomes'][0]['disposition'] == 'failed'
    assert row['outcomes'][0]['diagnostic'] == 'ML-SCHEDULE-CANCELLED'
    assert row['closure'] is None and not row['execution_succeeded']
    assert row['transitions'] and all(t['before'] == t['after'] for t in row['transitions'])
    counterexamples.append(dict(phase=phase, receipt_sha256=sha(path),
        unchanged_frontier=True, actual_outcome=row['outcomes'][0], explicit_closure_not_reached=True))
    for path in harness.glob('maestro-component-*.json'):
        row = read(path)
        assert row['root_removed'] and row['workers_reaped']
        assert not (Path(row['parent_path']) / row['root_name']).exists()
        roots.append(dict(path=str(path.relative_to(out)), sha256=sha(path)))
    for path in harness.glob('run-broker-waits-*.json'):
        row = read(path)
        assert all(row[k] for k in ('bootstrap_reaped', 'registered_helpers_reaped', 'storage_reaped', 'original_C1_released'))
        waits.append(dict(path=str(path.relative_to(out)), sha256=sha(path)))
    for item in read(out / (phase + '-public-evidence-index.json')):
        assert sha(out / item['snapshot']) == item['sha256'] and not item['reader_gaps']
        snapshots.append(dict(phase=phase, **item))
assert len(roots) == len(waits) == len(snapshots) == 20
result = dict(original_exec_session=8035, original_exec_exit=1, phases=phases,
    counterexamples=counterexamples, original_root_receipts=roots, original_wait_receipts=waits,
    snapshots=snapshots, source_links=sum(s['source_links'] for s in snapshots),
    frozen_manifest_sha256=sha(out / 'frozen-inputs.json'), auditor_sha256=sha(Path(__file__)),
    production_failure_is_classification_only=True, unauthorized_launch_demonstrated=False,
    full_increment17_complete=False, accepted=False, merged=False)
with (out / 'counterexample-verification.json').open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(phases=phases, unchanged_frontier_counterexamples=2,
    roots=len(roots), waits=len(waits), source_links=result['source_links'])))
