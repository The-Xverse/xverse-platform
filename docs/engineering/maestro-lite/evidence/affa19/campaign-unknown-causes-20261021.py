#!/usr/bin/env python3
"""Step-4 root-cause campaign on the ten unknown-cause CAPA records (finding 461).

Each original reproducer runs repeatedly under two arms with one installed version each
(finding 442): A = the branch without the F-08/F-09 guard (venv of e9b346a05), B = v2 f4262c285.
Instrumentation is observation only: rpc_timeline_plugin (every persistence RPC with sent budget,
service time and diagnostic) and guard_trace_plugin (every v2 guard refusal). No deadline is
widened, no test is edited, and a pass is never taken as a cause. Per run it records each node's
outcome, every ML- code, and for a failed node the RPCs that were late or sent with less budget
than their own service time. Usage:
campaign-unknown-causes-20261021.py <tests-tree> <out> <iterations> <venv-A> <venv-B>
"""
import hashlib, json, os, re, subprocess, sys, tempfile, time
from collections import Counter
from pathlib import Path

tree, out, iterations = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
ARMS = {'A': Path(sys.argv[4]), 'B': Path(sys.argv[5])}
M = 'tests/thesis_lite/maestro/'
NODES = {  # CAPA record -> original reproducer (register reproducer_id)
    '135': M + 'test_dispatcher.py::test_implicit_horizon_stop_respects_dependencies_before_compiler_rank',
    '286': M + 'test_runtime_control_registry.py::test_actual_registry_controller_recovery_preserves_productive_original_run[recovery]',
    '287': M + 'test_runtime_entry.py::test_whole_original_start_returns_after_actual_terminal_and_helper_closure[closed]',
    '318': M + 'test_active_control_deadlines.py::test_original_control_rejection_keeps_unspent_authority[past-restart]',
    '324': M + 'test_collection_runtime.py::test_actual_collection_retained_inputs_and_provisional_coverage_after_closed_reader',
    '330': M + 'test_coverage_producers.py::test_actual_shared_schedule_preserves_single_original_validation_and_distinct_tick_records',
    '331': M + 'test_terminal_runtime.py::test_actual_lost_or_changed_ack_preserves_unknown_state_and_never_replays[lost-report-ack]',
    '332': M + 'test_terminal_storage_root_loss.py::test_original_post_collection_loss_retains_unknown_ack_and_original_cleanup[storage-stall]',
    '337': M + 'test_runtime_control_registry.py::test_original_registry_whole_run_replay_and_retained_collection',
    '359a': M + 'test_active_control_deadlines.py::test_original_control_rejection_keeps_unspent_authority[beyond-active-recovery]',
    '359b': M + 'test_active_restart.py::test_original_active_explicit_restart_and_closed_generation_universe[leaf]',
}
HERE = Path(__file__).resolve().parent
PLUGINS = [HERE / 'service-time-calibration', HERE / 'guard-trace']
LATE = {'ML-PERSIST-TIMEOUT', 'ML-PERSIST-SENDER', 'ML-PERSIST-LATE'}
out.mkdir(parents=True, exist_ok=True)
root = Path(tempfile.mkdtemp(prefix='maestro-campaign-', dir='/dev/shm'))
load = lambda: [float(x) for x in Path('/proc/loadavg').read_text().split()[:3]]
installed = {a: hashlib.sha256(Path(subprocess.check_output([str(v / 'bin/python'), '-I', '-c',
             'import xverse.maestro.dispatcher as d;print(d.__file__)'], text=True).strip()).read_bytes()).hexdigest()
             for a, v in ARMS.items()}
records = []
for i in range(iterations):
    for arm in (('A', 'B') if i % 2 == 0 else ('B', 'A')):
        tmp = Path(tempfile.mkdtemp(prefix=f'{arm}{i}-', dir=root))
        timeline, guard = tmp / 'timeline', out / f'{arm}-{i:02d}.guard.jsonl'
        env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(tmp),
                   PYTEST_PLUGINS='maestro_receipt_namespace,rpc_timeline_plugin,guard_trace_plugin',
                   PYTHONPATH=os.pathsep.join(map(str, PLUGINS)), RPC_TIMELINE_OUT=str(timeline), GUARD_TRACE_OUT=str(guard))
        env.pop('PYTEST_ADDOPTS', None)
        before = load(); t0 = time.monotonic()
        p = subprocess.run([str(ARMS[arm] / 'bin/python'), '-m', 'pytest', '-q', '-rA', '-p', 'no:cacheprovider',
                            '--basetemp', str(tmp / 'bt'), *NODES.values()], cwd=tree, env=env, capture_output=True,
                           text=True, timeout=3600)
        text = p.stdout + p.stderr
        log = out / f'{arm}-{i:02d}.log'; log.write_text(text)
        outcome = {k: ('PASSED' if f'PASSED {n}' in text else 'FAILED' if f'FAILED {n}' in text
                       else 'ERROR' if f'ERROR {n}' in text else 'OTHER') for k, n in NODES.items()}
        late = {}
        for f in (timeline.glob('*.json') if timeline.exists() else []):
            data = json.loads(f.read_text())
            key = next((k for k, n in NODES.items() if data['node'] == n), None)
            if key and outcome[key] != 'PASSED':
                late[key] = [dict(kind=r['kind'], action=r['action'], budget=round(r['budget'], 4),
                                  service=round(r['service'], 4), diagnostic=r['diagnostic'])
                             for r in data['records'] if r['diagnostic'] in LATE or r['budget'] < r['service']]
        rec = dict(iteration=i, arm=arm, returncode=p.returncode, elapsed_seconds=time.monotonic() - t0,
                   loadavg_before=before, loadavg_after=load(), outcomes=outcome,
                   codes=dict(Counter(re.findall(r'ML-[A-Z0-9]+(?:-[A-Z0-9]+)*', text))), late_rpcs_of_failed_nodes=late,
                   guard_refusals=[json.loads(l) for l in guard.read_text().splitlines()] if guard.exists() else [],
                   log=log.name, log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
        records.append(rec)
        print(json.dumps(dict(i=i, arm=arm, load=before[0], failed=[k for k, v in outcome.items() if v != 'PASSED'],
                              refusals=len(rec['guard_refusals']))), flush=True)
        subprocess.run(['rm', '-rf', str(tmp)])
summary = {a: dict(runs=sum(r['arm'] == a for r in records),
                   failures={k: sum(r['arm'] == a and r['outcomes'][k] != 'PASSED' for r in records) for k in NODES},
                   guard_refusals=sum(len(r['guard_refusals']) for r in records if r['arm'] == a)) for a in ARMS}
(out / 'receipt.json').write_text(json.dumps(dict(tree=str(tree), arms={a: str(v) for a, v in ARMS.items()},
    installed_dispatcher_sha256=installed, nodes=NODES, iterations=iterations, records=records, summary=summary,
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), causes_claimed=False, accepted=False), indent=1))
subprocess.run(['rm', '-rf', str(root)])
print(json.dumps(summary, indent=1))
