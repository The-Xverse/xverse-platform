"""Increment19 A/B e (findings 477 (iv), 479): load-aware interior budgets under natural load.

Arms on the same 12 tests of finding 467, from the candidate worktree's tests (unchanged since main):
  A = /dev/shm/affa19-venv-c1, product of dabf858a5 (head without E1),
  B = /dev/shm/affa19-venv-budget, worktree src with E1 (verified equal by the implementer, 479).
Pre-registered expectation (477 (iv)): B failures at most A's, fewer ML-PERSIST-TIMEOUT and
ML-SCHEDULE-TEARDOWN-INCOMPLETE, no new failure class. Pairs alternate order; stops early when the
external load source is gone (pgrep -x llama-server). No retry, no edit, no generated load beyond one
test process at a time. Usage: ab-budget-loaded-20261021e.py <out-dir> <pairs>
"""
from pathlib import Path
import json, os, re, subprocess, sys, tempfile, time, shutil
HERE = Path(__file__).resolve().parent
TREE = HERE.parents[4]
ARMS = dict(A=Path('/dev/shm/affa19-venv-c1/bin/python'), B=Path('/dev/shm/affa19-venv-budget/bin/python'))
OUT = Path(sys.argv[1]).resolve(); OUT.mkdir(parents=True, exist_ok=False); PAIRS = int(sys.argv[2])
TESTS = [l.split('"')[1] for l in (HERE / 'rerun-v-nested-failures-20261021.sh').read_text().splitlines()
         if l.strip().startswith('"tests/')]
assert len(TESTS) == 12
load = lambda: Path('/proc/loadavg').read_text().split()[:3]
external = lambda: subprocess.run(['pgrep', '-x', 'llama-server'], capture_output=True).returncode == 0
summary = {a: dict(runs=0, failed={}, codes={}, refusals=0) for a in ARMS}
for i in range(PAIRS):
    if not external():
        print(json.dumps(dict(stopped_early_at_pair=i, reason='external load source gone')), flush=True); break
    for arm in (('A', 'B') if i % 2 == 0 else ('B', 'A')):
        tmp = Path(tempfile.mkdtemp(prefix=f'affa19-abd-{arm}{i}-', dir='/dev/shm'))
        guard = OUT / f'{arm}-{i:02d}.guard.jsonl'; log = OUT / f'{arm}-{i:02d}.log'
        env = {k: v for k, v in os.environ.items() if k not in ('PYTEST_ADDOPTS',)}
        env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1',
                   PYTEST_PLUGINS='maestro_receipt_namespace,guard_trace_plugin', PYTHONPATH=str(HERE / 'guard-trace'),
                   GUARD_TRACE_OUT=str(guard), TMPDIR=str(tmp), MAESTRO_FULL_RECEIPT_ROOT=str(tmp / 'r'),
                   MAESTRO_BOUNDARY_RECEIPTS=str(tmp / 'r'))
        before = load(); began = time.monotonic()
        with log.open('x') as stream:
            code = subprocess.run([str(ARMS[arm]), '-m', 'pytest', '-q', '-ra', '-p', 'no:cacheprovider',
                                   '--basetemp', str(tmp / 'bt'), *TESTS], cwd=TREE, env=env,
                                  stdout=stream, stderr=subprocess.STDOUT, timeout=1200).returncode
        text = log.read_text(); shutil.rmtree(tmp, ignore_errors=True)
        failed = re.findall(r'^FAILED (\S+)', text, re.M)
        codes = re.findall(r'^E\s+AssertionError: (ML-[A-Z0-9-]+)', text, re.M)
        refusals = [json.loads(l) for l in guard.read_text().splitlines()] if guard.exists() else []
        row = dict(i=i, arm=arm, load_before=before, load_after=load(), seconds=round(time.monotonic() - began, 1),
                   returncode=code, failed=failed, codes=codes, refusals=refusals)
        print(json.dumps(row), flush=True)
        s = summary[arm]; s['runs'] += 1; s['refusals'] += len(refusals)
        for f in failed: s['failed'][f] = s['failed'].get(f, 0) + 1
        for c in codes: s['codes'][c] = s['codes'].get(c, 0) + 1
(OUT / 'summary.json').write_text(json.dumps(dict(driver_sha256=__import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest(),
                                                  arms={k: str(v) for k, v in ARMS.items()}, summary=summary), indent=1) + '\n')
print(json.dumps(summary, indent=1))
