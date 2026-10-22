"""Increment19 run t: the first full platform Python run with one installed version (finding 455).

Successor in purpose of increment18 run s (verify-platform-regression-20261020s.py); not a byte
successor, because that driver reads increment17 evidence and imports src through PYTHONPATH.
Per finding 442 the native-started persistence worker always imports the interpreter's installed
package, so a PYTHONPATH run mixes versions whenever src differs from the install. This driver:

1. requires a clean candidate worktree and freezes HEAD as a git archive (sha256 recorded),
   extracted to tmpfs; tests run from that frozen tree, never from the live worktree;
2. builds the wheel from the frozen tree with the regression target environment h's build tools
   (no isolation) and installs it without dependencies into a new --system-site-packages venv
   (candidate-venv/mkvenv.sh), then verifies that the installed xverse equals the frozen src;
3. runs `python -m pytest tests` from the frozen tree with no PYTHONPATH, the receipt-namespace
   plugin, TMPDIR and basetemp on tmpfs, receipts on tmpfs, and an fsync probe on the same
   filesystem (observation only); outer deadline 7200 s;
4. records collection count, host condition at launch and end, return code, elapsed time and the
   receipt-tree size; it never retries and never edits anything outside its output directory and
   /dev/shm.

Not an acceptance, not a factory run, not scientific evidence.
Usage: verify-platform-regression-20261021t.py <out-dir>
"""
from pathlib import Path
import hashlib, json, os, platform, re, signal, subprocess, sys, tempfile, time

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
OUT = Path(sys.argv[1]).resolve()
BUILD_PYTHON = "/tmp/maestro-lite-platform-regression-target-20261020h/bin/python"
MKVENV = BASE / "candidate-venv" / "mkvenv.sh"
OUTER_DEADLINE_SECONDS = 7200
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
host = lambda: dict(loadavg=Path("/proc/loadavg").read_text().split(),
                    top=subprocess.run(["ps", "-eo", "pid,etimes,pcpu,rss,comm", "--sort=-pcpu"],
                                       capture_output=True, text=True).stdout.splitlines()[:12])

status = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True)
assert not status.strip(), "candidate worktree has tracked changes; commit before a frozen run:\n" + status
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
OUT.mkdir(parents=True, exist_ok=False)

def save(name, value):
    with (OUT / name).open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")

work = Path(tempfile.mkdtemp(prefix="maestro-platform-20261021t-", dir="/dev/shm"))
archive = subprocess.run(["git", "archive", head], cwd=ROOT, check=True, capture_output=True).stdout
(OUT / "tested-inputs.sha256").write_text(hashlib.sha256(archive).hexdigest() + "  git-archive-" + head + ".tar\n")
tree = work / "tree"; tree.mkdir()
subprocess.run(["tar", "-x", "-C", str(tree)], input=archive, check=True)
wheels = work / "wheel"
with (OUT / "build.log").open("x") as log:
    subprocess.run([BUILD_PYTHON, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(wheels), str(tree)],
                   stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)
wheel = next(wheels.glob("*.whl"))
venv = work / "venv"
with (OUT / "venv.log").open("x") as log:
    subprocess.run(["bash", str(MKVENV), str(venv), str(wheel)], stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)
PYTHON = str(venv / "bin" / "python")
installed = Path(subprocess.check_output([PYTHON, "-I", "-c", "import xverse,os;print(os.path.dirname(xverse.__file__))"],
                                         text=True).strip())
mismatch = subprocess.run(["diff", "-rq", "-x", "__pycache__", "-x", "xcom", str(tree / "src" / "xverse"), str(installed)],
                          capture_output=True, text=True)
assert mismatch.returncode == 0, mismatch.stdout
session_tmpdir = work / "tmpdir"; session_tmpdir.mkdir()
private = work / "basetemp"
harness = work / "receipts"; harness.mkdir()
env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1",
           PYTEST_PLUGINS="maestro_receipt_namespace", MAESTRO_GC_LOG=str(OUT / "gc-pauses.jsonl"),
           TMPDIR=str(session_tmpdir), MAESTRO_FULL_RECEIPT_ROOT=str(harness), MAESTRO_BOUNDARY_RECEIPTS=str(harness))
for name in ("PYTHONPATH", "PYTEST_ADDOPTS"):
    env.pop(name, None)
command = [PYTHON, "-m", "pytest", "tests", "-q", "--collect-only"]
with (OUT / "collected.log").open("x") as log:
    collection = subprocess.run(command, cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=300)
match = re.search(r"(\d+) tests? collected", (OUT / "collected.log").read_text())
assert collection.returncode == 0 and match, "collection failed"
collected = int(match.group(1))
save("configuration.json", dict(
    driver_sha256=sha(__file__), candidate=str(ROOT), git_head=head,
    git_branch=subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
    archive_sha256=hashlib.sha256(archive).hexdigest(), frozen_tree=str(tree), wheel=wheel.name, wheel_sha256=sha(wheel),
    venv=str(venv), installed_package=str(installed), installed_equals_frozen_src=True, mkvenv_sha256=sha(MKVENV),
    build_python=BUILD_PYTHON, python=sys.version, platform=platform.platform(),
    selected_environment={n: env.get(n) for n in ("PYTHONPATH", "PYTEST_DISABLE_PLUGIN_AUTOLOAD", "PYTHONDONTWRITEBYTECODE",
                                                  "PYTEST_PLUGINS", "TMPDIR")},
    collected=collected, scope="all collected platform Python tests from the frozen tree, one installed version",
    host_condition_at_launch=host(), filesystems="tmpdir, basetemp and receipts on tmpfs:/dev/shm",
    outer_deadline_seconds=OUTER_DEADLINE_SECONDS, wheel_verification=True, factory_execution=False,
    accepted=False, merged=False))
probe_code = r"""
import json,os,signal,sys,time
target,out,seconds=sys.argv[1],sys.argv[2],float(sys.argv[3])
fd=os.open(target,os.O_RDWR|os.O_CREAT|os.O_TRUNC,0o600); stream=open(out,'w')
start=time.monotonic(); n=spikes=0; worst=0.0; stop=[False]
signal.signal(signal.SIGTERM, lambda *a: stop.__setitem__(0, True))
while not stop[0] and time.monotonic()-start<seconds:
    os.write(fd,b'x'*4096); t=time.monotonic(); os.fsync(fd); d=time.monotonic()-t; n+=1; worst=max(worst,d)
    if d>0.15:
        spikes+=1; stream.write(json.dumps(dict(monotonic=t,wall=time.time(),fsync_seconds=round(d,4)))+'\n'); stream.flush()
    time.sleep(0.25)
stream.write(json.dumps(dict(summary=True,samples=n,spikes_over_150ms=spikes,worst_seconds=round(worst,4),seconds=round(time.monotonic()-start,3)))+'\n'); stream.close()
os.close(fd); os.unlink(target)
"""
probe = subprocess.Popen([PYTHON, "-I", "-c", probe_code, str(session_tmpdir / "fsync-probe.bin"), str(OUT / "fsync-probe.jsonl"),
                          str(OUTER_DEADLINE_SECONDS)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
command = [PYTHON, "-m", "pytest", "tests", "-q", "-ra", "--basetemp", str(private)]
began = time.monotonic(); timed_out = False
with (OUT / "wheel.log").open("x") as log:
    process = subprocess.Popen(command, cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    save("wheel-started.json", dict(command=command, cwd=str(tree), original_pid=process.pid, collected=collected,
                                    start_unix_seconds=time.time(), outer_deadline_seconds=OUTER_DEADLINE_SECONDS))
    print("platform wheel started", process.pid, "collected", collected, flush=True)
    try:
        code = process.wait(timeout=OUTER_DEADLINE_SECONDS)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        code = process.wait()
probe.terminate()
try:
    probe.wait(timeout=10)
except subprocess.TimeoutExpired:
    probe.kill()
tail = (OUT / "wheel.log").read_text().splitlines()[-1:] or [""]
receipts = subprocess.run(["du", "-sb", str(harness)], capture_output=True, text=True).stdout.split()[:1]
save("wheel-receipt.json", dict(command=command, cwd=str(tree), returncode=code, original_pid=process.pid,
    elapsed_seconds=time.monotonic() - began, outer_timeout=timed_out, descendant_cleanup_unknown=timed_out,
    log_sha256=sha(OUT / "wheel.log"), summary_line=tail[0], collected=collected, git_head=head,
    archive_sha256=hashlib.sha256(archive).hexdigest(), receipts_bytes=int(receipts[0]) if receipts else None,
    receipts_root=str(harness), host_condition_at_end=host(),
    passed_exit_status=code == 0 and not timed_out, accepted=False, merged=False))
print("platform wheel terminal", code, tail[0], flush=True)
raise SystemExit(code if code else (1 if timed_out else 0))
