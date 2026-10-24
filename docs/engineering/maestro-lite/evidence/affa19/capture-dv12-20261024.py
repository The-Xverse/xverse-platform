"""Capture one genuine official DV12 invocation; never accepts or repairs a run."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import signal
import subprocess
import time

EXTERNAL = Path('/media/jefferson/11c42dee-73a3-4c2b-ab42-a0440011d9e0/.x-verse-build/codex-20261024')
ROOT = (EXTERNAL / 'worktrees/xverse-platform/stabilization-s1a3-20261023').resolve(strict=True)
BASE = ROOT / 'docs/engineering/maestro-lite/evidence/affa19'
RUN = BASE / 'stabilization-s1a3/platform-regression-20261024j-codex-1'
TESTED = '4bedba9efd21c750b84322e5fc265eb6adf86cc9'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def stamp():
    return datetime.now(timezone.utc).isoformat()

class CaptureInterrupted(BaseException):
    pass

SPAWNING = False
PENDING_SIGNAL = None

def interrupt(signum, frame):
    global PENDING_SIGNAL
    if SPAWNING:
        PENDING_SIGNAL = signum
        return
    raise CaptureInterrupted(signum)

def group_exists(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False

def cleanup_group(process):
    result = dict(complete=False, term_sent=False, kill_sent=False, errors=[])
    if process is None:
        result['complete'] = True
        return result
    try:
        if group_exists(process.pid):
            try:
                os.killpg(process.pid, signal.SIGTERM)
                result['term_sent'] = True
            except ProcessLookupError:
                pass
            deadline = time.monotonic()+15
            while group_exists(process.pid) and time.monotonic() < deadline:
                process.poll()
                time.sleep(0.05)
            if group_exists(process.pid):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                    result['kill_sent'] = True
                except ProcessLookupError:
                    pass
        process.wait(timeout=15)
        deadline = time.monotonic()+5
        while group_exists(process.pid) and time.monotonic() < deadline:
            time.sleep(0.05)
        result['complete'] = not group_exists(process.pid)
    except Exception as error:
        result['errors'].append(repr(error))
    return result

def main():
    global SPAWNING
    validator = ROOT / 'scripts/validate_maestro_acceptance_evidence.py'
    paths = dict(configuration=RUN/'configuration.json', wheelReceipt=RUN/'wheel-receipt.json',
                 wheelLog=RUN/'wheel.log', g4=BASE/'acceptance-inputs/g4.json',
                 allowlist=BASE/'acceptance-inputs/allowlist.json', validator=validator)
    assert validator.read_bytes() == subprocess.check_output(
        ['git', 'show', TESTED+':scripts/validate_maestro_acceptance_evidence.py'], cwd=ROOT)
    outputs = [RUN / name for name in ('dv12-gate-verdict.json', 'dv12-stderr.log', 'dv12-execution-receipt.json')]
    assert not any(p.exists() or p.is_symlink() for p in outputs), 'capture already exists; preserve it'
    before = {name:sha(path) for name,path in paths.items()}
    command = ['/usr/bin/python3', '-I', str(validator), str(RUN), '--candidate', TESTED,
               '--g4', str(paths['g4']), '--allowlist', str(paths['allowlist']),
               '--scope', 'code', '--repo', str(ROOT)]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(EXTERNAL/'scratch/dv12'),
               XDG_CACHE_HOME=str(EXTERNAL/'cache'))
    Path(env['TMPDIR']).mkdir(parents=True, exist_ok=True)
    started = stamp()
    began = time.monotonic()
    timed_out = False
    failure = None
    rc = None
    process = None
    cleanup = dict(complete=False)
    signals = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP}
    for signum in signals:
        signal.signal(signum, interrupt)
    previous_mask = None
    with outputs[0].open('xb') as out, outputs[1].open('xb') as err:
        try:
            SPAWNING = True
            try:
                process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err, start_new_session=True)
            finally:
                SPAWNING = False
            if PENDING_SIGNAL is not None:
                raise CaptureInterrupted(PENDING_SIGNAL)
            try:
                rc = process.wait(timeout=900)
            except subprocess.TimeoutExpired:
                timed_out = True
        except BaseException as error:
            failure = repr(error)
        finally:
            previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, signals)
            cleanup = cleanup_group(process)
            if process is not None:
                rc = process.returncode
    after = {}
    for name, path in paths.items():
        try:
            after[name] = sha(path)
        except OSError as error:
            after[name] = dict(error=repr(error))
    try:
        gate = json.loads(outputs[0].read_bytes())
        gate_accepted = gate.get('accepted_as_evidence') is True and gate.get('blockers') == []
    except (ValueError, AttributeError):
        gate_accepted = False
    success = (rc == 0 and not timed_out and failure is None and before == after and gate_accepted
               and cleanup['complete'] is True and not cleanup.get('term_sent'))
    receipt = dict(command=command, repo=str(ROOT), run=str(RUN), candidate=TESTED, scope='code',
                   inputs_before=before, inputs_after=after, returncode=rc, timed_out=timed_out,
                   failure=failure, cleanup=cleanup, gate_sha256=sha(outputs[0]), stderr_sha256=sha(outputs[1]),
                   wrapper_path=str(Path(__file__).resolve()), wrapper_sha256=sha(Path(__file__)),
                   started_utc=started, finished_utc=stamp(), elapsed_seconds=time.monotonic()-began,
                   capture_passed=success, accepted=False, merged=False)
    with outputs[2].open('x') as stream:
        stream.write(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(dict(capture_passed=success, returncode=rc, timed_out=timed_out, receipt=str(outputs[2]))))
    signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
    return 0 if success else 1

if __name__ == '__main__':
    raise SystemExit(main())
