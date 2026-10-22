#!/usr/bin/env python3
"""Interleaved A/B for the F-08/F-09 v2 candidate (finding 438), successor of ab-f08-repair-20261021a.py.

Per finding 442 each arm is one installed version: a candidate venv (mkvenv.sh) whose interpreter
runs the tests with no PYTHONPATH, so the test process and the native-started worker import the
same package. Both arms run the same test tree (v2 changes src only). Records pass/fail per node,
every ML- code and T3 variant per run, the host load, and each arm's installed dispatcher.py and
teardown.py hashes. Read-only toward the tree; writes only <out> and /dev/shm.
Usage: ab-f08v2-20261021b.py <tests-tree> <out> <iterations> <venv-A> <venv-B>
"""
import hashlib, json, os, re, subprocess, sys, tempfile, time
from collections import Counter
from pathlib import Path

tree = Path(sys.argv[1]); out = Path(sys.argv[2]); iterations = int(sys.argv[3])
ARMS = {'A': Path(sys.argv[4]), 'B': Path(sys.argv[5])}
NODES = [
    'tests/thesis_lite/maestro/test_time_context_controls.py::test_paused_simulation_does_not_hold_the_run_past_its_host_deadline',
    'tests/thesis_lite/maestro/test_terminal_runtime.py::test_actual_native_report_close_and_external_closed_recomputation[False]',
    'tests/thesis_lite/maestro/test_dispatcher.py::test_duration_defers_step_completion_until_actual_tick',
    'tests/thesis_lite/maestro/test_dispatcher.py::test_paused_ticks_still_service_host_health_and_original_leases',
    'tests/thesis_lite/maestro/test_native_storage_faults.py::test_storage_full_inside_the_original_worker_fails_closed[C0-never-armed]',
]
out.mkdir(parents=True, exist_ok=True)
root = Path(tempfile.mkdtemp(prefix='maestro-ab-f08v2-', dir='/dev/shm'))
installed = {}
for arm, venv in ARMS.items():
    sp = Path(subprocess.run([str(venv / 'bin/python'), '-I', '-c', 'import xverse.maestro,os;print(os.path.dirname(xverse.maestro.__file__))'],
                             check=True, capture_output=True, text=True).stdout.strip())
    installed[arm] = {'venv': str(venv), 'maestro': str(sp),
                      **{n: hashlib.sha256((sp / n).read_bytes()).hexdigest() for n in ('dispatcher.py', 'teardown.py', 'coverage.py')}}
records = []
load = lambda: [float(x) for x in Path('/proc/loadavg').read_text().split()[:3]]
for i in range(iterations):
    for arm in (('A', 'B') if i % 2 == 0 else ('B', 'A')):
        tmp = Path(tempfile.mkdtemp(prefix=f'{arm}{i}-', dir=root))
        env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1',
                   PYTEST_PLUGINS='maestro_receipt_namespace', TMPDIR=str(tmp))
        env.pop('PYTHONPATH', None); env.pop('PYTEST_ADDOPTS', None)
        before = load(); t0 = time.monotonic()
        p = subprocess.run([str(ARMS[arm] / 'bin/python'), '-m', 'pytest', '-q', '-rA', '-p', 'no:cacheprovider',
                            '--basetemp', str(tmp / 'bt'), *NODES], cwd=tree, env=env, capture_output=True, text=True, timeout=1800)
        elapsed = time.monotonic() - t0
        text = p.stdout + p.stderr
        log = out / f'{arm}-{i:02d}.log'; log.write_text(text)
        outcome = {n: ('PASSED' if f'PASSED {n}' in text else 'FAILED' if f'FAILED {n}' in text else 'OTHER') for n in NODES}
        rec = {'iteration': i, 'arm': arm, 'returncode': p.returncode, 'elapsed_seconds': elapsed,
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
                    'runs_with_any_failure': sum(any(v != 'PASSED' for v in r['outcomes'].values()) for r in rs),
                    'runs_with_persist_timeout': sum('ML-PERSIST-TIMEOUT' in r['codes'] for r in rs),
                    't3_variants': dict(Counter(v for r in rs for v in r['t3_variants']))}
(out / 'receipt.json').write_text(json.dumps({'tree': str(tree), 'installed': installed, 'nodes': NODES, 'iterations': iterations,
    'records': records, 'summary': summary, 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'accepted': False, 'merged': False}, indent=1))
subprocess.run(['rm', '-rf', str(root)])
print(json.dumps(summary, indent=1))
