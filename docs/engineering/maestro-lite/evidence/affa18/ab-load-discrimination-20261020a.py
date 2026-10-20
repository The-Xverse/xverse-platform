#!/usr/bin/env python3
"""A/B discrimination for run r's three failures (finding 409).

Alternates the four failing node IDs (two outer, two reported by the nested child) between
A = d52683ad (pre-F-02, run p's configuration, environment f) and B = e290ce78 (F-02, run r's
configuration, environment h), each from a `git archive` snapshot on tmpfs with TMPDIR on tmpfs.
Interleaving A/B per iteration exposes both arms to the same host load. Read-only toward the
candidate worktree; writes only to the output directory and /dev/shm.
"""
import hashlib, json, os, subprocess, sys, tempfile, time
from pathlib import Path

repo = Path(sys.argv[1]); out = Path(sys.argv[2]); iterations = int(sys.argv[3])
ARMS = {
    'A': ('d52683ad52e995e7ef443af16b813bb7cc5722a7', '/tmp/maestro-lite-platform-regression-target-20261020f/bin/python'),
    'B': ('e290ce78cd1fbec052a2130e7aedf7b70990e279', '/tmp/maestro-lite-platform-regression-target-20261020h/bin/python'),
}
NODES = [
    'tests/thesis_lite/maestro/test_shared_dispatcher.py::test_paused_shared_ticks_renew_both_original_leases_and_observe_health',
    'tests/thesis_lite/maestro/test_terminal_faults.py::test_actual_nonopen_writer_close_requires_original_report_receipt[True-closed]',
    'tests/thesis_lite/maestro/test_dispatcher.py::test_paused_ticks_still_service_host_health_and_original_leases',
    'tests/thesis_lite/maestro/test_launcher_composition.py::test_actual_original_startup_through_terminal_and_helper_closure[closed]',
]
out.mkdir(parents=True, exist_ok=True)
root = Path(tempfile.mkdtemp(prefix='maestro-ab-20261020a-', dir='/dev/shm'))
trees = {}
for arm, (commit, _) in ARMS.items():
    tree = root / arm; tree.mkdir()
    archive = subprocess.run(['git', '-C', str(repo), 'archive', commit], check=True, capture_output=True).stdout
    subprocess.run(['tar', '-x', '-C', str(tree)], input=archive, check=True)
    trees[arm] = {'path': str(tree), 'commit': commit, 'archive_sha256': hashlib.sha256(archive).hexdigest()}
records = []
def load():
    return [float(x) for x in Path('/proc/loadavg').read_text().split()[:3]]
for i in range(iterations):
    for arm in (('A', 'B') if i % 2 == 0 else ('B', 'A')):
        commit, python = ARMS[arm]; tree = Path(trees[arm]['path'])
        tmp = Path(tempfile.mkdtemp(prefix=f'{arm}{i}-', dir=root))
        # Same selected environment as driver r (verify-platform-regression-20261020r.py:156).
        env = dict(os.environ, PYTHONPATH=str(tree / 'src'), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
                   PYTHONDONTWRITEBYTECODE='1', PYTEST_PLUGINS='maestro_receipt_namespace',
                   MAESTRO_GC_LOG=str(out / f'{arm}-{i:02d}-gc.jsonl'), TMPDIR=str(tmp))
        env.pop('PYTEST_ADDOPTS', None)
        before = load(); t0 = time.monotonic()
        p = subprocess.run([python, '-m', 'pytest', '-q', '-rA', '-p', 'no:cacheprovider', '--basetemp', str(tmp / 'bt'), *NODES],
                           cwd=tree, env=env, capture_output=True, text=True, timeout=1800)
        elapsed = time.monotonic() - t0
        log = out / f'{arm}-{i:02d}.log'; log.write_text(p.stdout + p.stderr)
        outcome = {n: ('PASSED' if f'PASSED {n}' in p.stdout else 'FAILED' if f'FAILED {n}' in p.stdout else 'OTHER') for n in NODES}
        rec = {'iteration': i, 'arm': arm, 'commit': commit, 'returncode': p.returncode, 'elapsed_seconds': elapsed,
               'loadavg_before': before, 'loadavg_after': load(), 'outcomes': outcome,
               'log': log.name, 'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest()}
        records.append(rec); print(json.dumps({k: rec[k] for k in ('iteration', 'arm', 'returncode', 'elapsed_seconds')}), flush=True)
summary = {}
for arm in ARMS:
    rs = [r for r in records if r['arm'] == arm]
    summary[arm] = {n: sum(r['outcomes'][n] == 'FAILED' for r in rs) for n in NODES} | {'runs': len(rs)}
(out / 'receipt.json').write_text(json.dumps({'trees': trees, 'nodes': NODES, 'iterations': iterations,
    'records': records, 'failures_per_arm': summary,
    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'accepted': False, 'merged': False}, indent=1))
subprocess.run(['rm', '-rf', str(root)])
print(json.dumps(summary, indent=1))
