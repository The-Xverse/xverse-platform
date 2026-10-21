#!/usr/bin/env python3
"""Interleaved A/B for the F-08/F-09 v2 candidate (finding 438), successor of ab-f08-repair-20261021a.py.

A and B are commits given on the command line (A: the branch without a repair, B: the v2 candidate). Each arm runs from
a `git archive` snapshot of src/, tests/, xdl/ and pyproject.toml on tmpfs, with the driver-r selected
environment (PYTHONPATH=<arm>/src, plugin autoload off), so both arms see the same host load per
iteration. Per run it records pass/fail of each node and every ML- diagnostic code and T3 variant line in
the output. Read-only toward the candidate worktree; writes only the output directory and /dev/shm.
Usage: ab-f08v2-20261021b.py <repo> <out> <iterations> <commit-A> <commit-B>
"""
import hashlib, json, os, re, subprocess, sys, tempfile, time
from collections import Counter
from pathlib import Path

repo = Path(sys.argv[1]); out = Path(sys.argv[2]); iterations = int(sys.argv[3])
PYTHON = '/tmp/maestro-lite-platform-regression-target-20261020h/bin/python'
ARMS = {'A': sys.argv[4], 'B': sys.argv[5]}
PATHS = ['src', 'tests', 'xdl', 'pyproject.toml']
NODES = [
    'tests/thesis_lite/maestro/test_time_context_controls.py::test_paused_simulation_does_not_hold_the_run_past_its_host_deadline',
    'tests/thesis_lite/maestro/test_terminal_runtime.py::test_actual_native_report_close_and_external_closed_recomputation[False]',
    'tests/thesis_lite/maestro/test_dispatcher.py::test_duration_defers_step_completion_until_actual_tick',
    'tests/thesis_lite/maestro/test_dispatcher.py::test_paused_ticks_still_service_host_health_and_original_leases',
    'tests/thesis_lite/maestro/test_native_storage_faults.py::test_storage_full_inside_the_original_worker_fails_closed[C0-never-armed]',
]
out.mkdir(parents=True, exist_ok=True)
root = Path(tempfile.mkdtemp(prefix='maestro-ab-f08-', dir='/dev/shm'))
trees = {}
for arm, commit in ARMS.items():
    tree = root / arm; tree.mkdir()
    full = subprocess.run(['git', '-C', str(repo), 'rev-parse', commit], check=True, capture_output=True, text=True).stdout.strip()
    archive = subprocess.run(['git', '-C', str(repo), 'archive', full, *PATHS], check=True, capture_output=True).stdout
    subprocess.run(['tar', '-x', '-C', str(tree)], input=archive, check=True)
    trees[arm] = {'path': str(tree), 'commit': full, 'paths': PATHS, 'archive_sha256': hashlib.sha256(archive).hexdigest()}
records = []
load = lambda: [float(x) for x in Path('/proc/loadavg').read_text().split()[:3]]
for i in range(iterations):
    for arm in (('A', 'B') if i % 2 == 0 else ('B', 'A')):
        tree = Path(trees[arm]['path'])
        tmp = Path(tempfile.mkdtemp(prefix=f'{arm}{i}-', dir=root))
        env = dict(os.environ, PYTHONPATH=str(tree / 'src'), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
                   PYTHONDONTWRITEBYTECODE='1', PYTEST_PLUGINS='maestro_receipt_namespace', TMPDIR=str(tmp))
        env.pop('PYTEST_ADDOPTS', None)
        before = load(); t0 = time.monotonic()
        p = subprocess.run([PYTHON, '-m', 'pytest', '-q', '-rA', '-p', 'no:cacheprovider', '--basetemp', str(tmp / 'bt'), *NODES],
                           cwd=tree, env=env, capture_output=True, text=True, timeout=1800)
        elapsed = time.monotonic() - t0
        text = p.stdout + p.stderr
        log = out / f'{arm}-{i:02d}.log'; log.write_text(text)
        outcome = {n: ('PASSED' if f'PASSED {n}' in text else 'FAILED' if f'FAILED {n}' in text else 'OTHER') for n in NODES}
        rec = {'iteration': i, 'arm': arm, 'commit': trees[arm]['commit'], 'returncode': p.returncode, 'elapsed_seconds': elapsed,
               'loadavg_before': before, 'loadavg_after': load(), 'outcomes': outcome,
               'codes': dict(Counter(re.findall(r'ML-[A-Z0-9]+(?:-[A-Z0-9]+)*', text))),
               't3_variants': re.findall(r'T3-VARIANT (ML-[A-Z-]+)', text),
               'log': log.name, 'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest()}
        records.append(rec)
        shrink = lambda n: n.rsplit('::', 1)[1][:40]
        print(json.dumps({'i': i, 'arm': arm, 'load': before[0], 'failed': [shrink(n) for n, v in outcome.items() if v != 'PASSED'],
                          'timeouts': rec['codes'].get('ML-PERSIST-TIMEOUT', 0), 't3': rec['t3_variants']}), flush=True)
summary = {}
for arm in ARMS:
    rs = [r for r in records if r['arm'] == arm]
    summary[arm] = {'runs': len(rs), 'failures': {n: sum(r['outcomes'][n] != 'PASSED' for r in rs) for n in NODES},
                    'runs_with_persist_timeout': sum('ML-PERSIST-TIMEOUT' in r['codes'] for r in rs),
                    't3_variants': dict(Counter(v for r in rs for v in r['t3_variants']))}
(out / 'receipt.json').write_text(json.dumps({'trees': trees, 'nodes': NODES, 'iterations': iterations, 'records': records,
    'summary': summary, 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'accepted': False, 'merged': False}, indent=1))
subprocess.run(['rm', '-rf', str(root)])
print(json.dumps(summary, indent=1))
