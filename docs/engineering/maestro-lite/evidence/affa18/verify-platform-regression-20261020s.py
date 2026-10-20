"""Increment18 run s (successor of run r, which ended 3 failed under an unrelated CARLA load, finding 409; same bytes e290ce78c, launched on the author's go with that load still present): checkpoint 18-3 plus the native F-02 watch proof (finding 403) across bootstrap.c,
run_authority.c, affa_protocol.py, bootstrap.py, affa_client.py and run_broker.py, with the F-02 controls;
2104 collected, environment h (wheel of this tree), TMPDIR on tmpfs, probe outside the basetemp.

Successor of verify-platform-regression-20261020g.py. The only difference from driver g is the
snapshot: the transitive statement budget is back at its admitted 0.3 s (the g repair was
rejected at schedule admission, finding 367); the crash-point module gains the release-before-send controls (2096 collected).
Inherited from g:

0. The source snapshot is NOT identical to runs a/b/c: exactly the two test files of the
   fixture window-margin repair differ (tests/thesis_lite/maestro/test_shared_dispatcher.py,
   tests/thesis_lite/maestro/test_active_restart.py). The driver asserts that no other
   frozen input changed and retains the unified diff against run c's archive.
0b. Environment d installs plugin v3, which additionally logs gen-2 garbage-collection
   pauses of every session (MAESTRO_GC_LOG) for correlation with operation stalls.
0c. The driver runs an fsync-latency probe on the same filesystem as the private basetemp
   for the whole session and retains it as evidence (observation only).
   Inherited from driver c:

1. PYTHON is the separately prepared environment from platform-environment-20261020d.
2. A preflight asserts `python -m build --version` and `hatchling` import succeed and
   binds the preparation receipt identity before any pytest process starts.
3. The driver refuses to start while the original run a has no terminal receipt.
4. The source snapshot must be byte-identical to run a's frozen manifest (1903 files),
   so the only intended variation between a and b is the verification environment.
5. The outer deadline is 7200 s instead of 3600 s because the outer session contains
   the 1501 Maestro cases and the existing Argus integration case re-runs 1796 cases
   in a nested child; the prior Maestro-only phase alone took 1344 s.

This is source verification in the isolated candidate, not a wheel claim, not an
acceptance, not a factory run, and not scientific evidence.
"""
from pathlib import Path
import hashlib
import json
import os
import platform
import re
import signal
import subprocess
import sys
import tarfile
import tempfile
import time

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
AFFA17 = BASE.parent / "affa17"
PRIOR = AFFA17 / "integrated-maestro-20261019b"
ORIGINAL = AFFA17 / "platform-regression-20261019a"
PRIOR_RUN = AFFA17 / "platform-regression-20261020g"
UNREPAIRED_RUN = AFFA17 / "platform-regression-20261020c"
ENVIRONMENT = BASE / "platform-environment-20261020h"
OUT = BASE / "platform-regression-20261020s"
PYTHON = "/tmp/maestro-lite-platform-regression-target-20261020h/bin/python"
PLUGIN_SOURCE = AFFA17 / "maestro_receipt_namespace_v3.py"
REPAIRED = ("tests/thesis_lite/maestro/test_shared_dispatcher.py", "tests/thesis_lite/maestro/test_active_restart.py",
            "tests/thesis_lite/maestro/test_schedule_worker.py",  # finding 374: nanosecond lease comparison
            "src/xverse/maestro/dispatcher.py",  # finding 379: run-terminal statement budget
            "tests/thesis_lite/maestro/test_runtime_entry.py",  # finding 382: ENVIRONMENT_DIGEST constant
            "src/xverse/maestro/native/run_authority.c",  # findings 394-397 F-01; 403 F-02
            "src/xverse/maestro/native/bootstrap.c", "src/xverse/maestro/affa_protocol.py", "src/xverse/maestro/bootstrap.py",
            "src/xverse/maestro/affa_client.py", "src/xverse/maestro/run_broker.py",  # finding 403: native watch proof
            "tests/thesis_lite/maestro/test_affa_native.py", "tests/thesis_lite/maestro/test_affa_client.py",
            "tests/thesis_lite/maestro/test_affa_protocol.py")  # finding 403: harness key, tickets
ADDED = ("tests/thesis_lite/maestro/test_runtime_actual.py", "tests/thesis_lite/maestro/test_composed_post_release_loss.py",
         "tests/thesis_lite/maestro/test_runtime_lane_admission.py", "tests/thesis_lite/maestro/test_affa_release_timeout_fence.py",
         "tests/thesis_lite/maestro/test_affa_watch_token.py")
OUTER_DEADLINE_SECONDS = 7200
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())

# Original run a must be terminal; never duplicate a live run.
original_receipt = ORIGINAL / "source-receipt.json"
assert original_receipt.is_file(), "original run a has no terminal receipt; do not start a duplicate"
original = read(original_receipt)
prior_receipt = PRIOR_RUN / "source-receipt.json"
assert prior_receipt.is_file(), "run b has no terminal receipt; do not start a duplicate"
prior = read(prior_receipt)
original_manifest = read(ORIGINAL / "frozen-inputs.json")
assert len(original_manifest) == 1903

# Prior complete Maestro regression and its 273 inputs remain the accepted precondition.
assert read(PRIOR / "result-after-wheel.json")["full_maestro_regression_passed"]
for phase in ("source", "wheel"):
    audit = read(PRIOR / ("maestro_full-" + phase + "-terminal-audit/audit.json"))
    assert audit["original_returncode"] == 0 and not audit["receipt_parse_errors"]
    assert audit["all_recorded_roots_removed_and_workers_reaped"]
    assert audit["observed_counts"] == dict(passed=1501, failed=0, skipped=0, errors=0, xfailed=0, xpassed=0)
maestro = read(PRIOR / "frozen-inputs.json")
assert len(maestro) == 273
maestro_changed = sorted(n for n, h in maestro.items() if sha(ROOT / n) != h)
assert maestro_changed == sorted(n for n in REPAIRED if n in maestro), maestro_changed

# Prepared environment identity and build-tool preflight (finding 357).
preparation = read(ENVIRONMENT / "preparation.json")
assert preparation["python"] == PYTHON
assert preparation["plugin_sha256"] == sha(PLUGIN_SOURCE)
assert Path(PYTHON).is_file()
OUT.mkdir(exist_ok=False)

def save(name, value):
    with (OUT / name).open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")

preflight = {}
for label, command in (
    ("build", [PYTHON, "-m", "build", "--version"]),
    ("hatchling", [PYTHON, "-I", "-c", "import hatchling, importlib.metadata as m; print(m.version('hatchling'))"]),
    ("pytest", [PYTHON, "-m", "pytest", "--version"]),
    ("plugin", [PYTHON, "-I", "-c", "import maestro_receipt_namespace as m, hashlib; print(hashlib.sha256(open(m.__file__,'rb').read()).hexdigest())"]),
):
    done = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60)
    preflight[label] = dict(command=command, returncode=done.returncode,
                            stdout=done.stdout.strip(), stderr=done.stderr.strip())
    assert done.returncode == 0, label
versions_code = ("import json; from importlib.metadata import version; print(json.dumps({n: version(n) for n in "
                 + repr(sorted(preparation["build_versions"])) + "}))")
actual_versions = json.loads(subprocess.check_output([PYTHON, "-I", "-c", versions_code], text=True))
assert actual_versions == preparation["build_versions"], actual_versions
assert preflight["plugin"]["stdout"] == sha(PLUGIN_SOURCE), preflight["plugin"]
save("preflight.json", dict(checks=preflight, build_versions=actual_versions, plugin_sha256=sha(PLUGIN_SOURCE),
    preparation_sha256=sha(ENVIRONMENT / "preparation.json"),
    pip_list_sha256=sha(ENVIRONMENT / "pip-list.log"), passed=True))

paths = set()
for directory in ("src", "tests", "scripts", "xdl", "specs", ".specify", "docs/architecture", "docs/adr", "docs/engineering/xcom"):
    for p in (ROOT / directory).rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
            assert not p.is_symlink(), str(p)
            paths.add(p)
for name in ("pyproject.toml", "README.md", "LICENSE", "AGENTS.md"):
    paths.add(ROOT / name)
paths.update(ROOT / n for n in maestro)
frozen = {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}
changed_vs_original = sorted(n for n in set(frozen) | set(original_manifest) if frozen.get(n) != original_manifest.get(n))
assert changed_vs_original == sorted(REPAIRED + ADDED), changed_vs_original
assert all(n not in original_manifest for n in ADDED)
# The repaired files are untracked in Git; diff against run c's archived snapshot instead.
import difflib
diff = ""
with tarfile.open(UNREPAIRED_RUN / "tested-inputs.tar.gz") as archive:
    for name in REPAIRED:
        before = archive.extractfile(name).read().decode().splitlines(keepends=True)
        after = (ROOT / name).read_text().splitlines(keepends=True)
        diff += "".join(difflib.unified_diff(before, after, "c/" + name, "h/" + name))
with (OUT / "fixture-window-margin.diff").open("x") as stream:
    stream.write(diff)
assert "active_seconds=base_active_seconds+reserved_seconds" in diff and "active_seconds==5.8" in diff
save("frozen-inputs.json", frozen)
with tarfile.open(OUT / "tested-inputs.tar.gz", "w:gz") as archive:
    for p in sorted(paths):
        archive.add(p, arcname=str(p.relative_to(ROOT)))

session_tmpdir = Path(tempfile.mkdtemp(prefix="maestro-platform-20261020s-tmpdir-", dir="/dev/shm"))
env = dict(os.environ, PYTHONPATH=str(ROOT / "src"),
           PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1",
           PYTEST_PLUGINS="maestro_receipt_namespace", MAESTRO_GC_LOG=str(OUT / "gc-pauses.jsonl"),
           TMPDIR=str(session_tmpdir))
save("configuration.json", dict(
    driver_sha256=sha(Path(__file__)), candidate=str(ROOT),
    successor_of=dict(driver="verify-platform-regression-20261019b.py",
                      driver_sha256=sha(AFFA17 / "verify-platform-regression-20261019b.py"),
                      receipt_sha256=sha(prior_receipt), prior_returncode=prior["returncode"],
                      original_run_a_receipt_sha256=sha(original_receipt), original_returncode=original["returncode"]),
    harness_change=dict(plugin="maestro_receipt_namespace (PYTEST_PLUGINS, installed in environment c)",
                        plugin_sha256=sha(PLUGIN_SOURCE), replaces="integrated-maestro-20261019b/receipt_namespace.py via plugins=[module]",
                        child_sessions_receive_per_module_namespace=True, accepted_tests_changed=False),
    git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    git_branch=subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
    git_status=subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
    python=sys.version, executable=sys.executable, verification_python=PYTHON, platform=platform.platform(),
    pytest_version=preflight["pytest"]["stdout"],
    selected_environment={n: env[n] for n in ("PYTHONPATH", "PYTEST_DISABLE_PLUGIN_AUTOLOAD", "PYTHONDONTWRITEBYTECODE", "PYTEST_PLUGINS", "MAESTRO_GC_LOG", "TMPDIR")},
    environment_receipt=dict(path=str(ENVIRONMENT.relative_to(ROOT) / "preparation.json"),
                             sha256=sha(ENVIRONMENT / "preparation.json"), build_versions=actual_versions),
    maestro_manifest_sha256=sha(PRIOR / "frozen-inputs.json"),
    prior_audits={p: sha(PRIOR / ("maestro_full-" + p + "-terminal-audit/audit.json")) for p in ("source", "wheel")},
    scope="all collected platform Python tests in one source session; C++ suites are separate",
    source_snapshot_paths=len(frozen), source_snapshot_manifest_sha256=sha(OUT / "frozen-inputs.json"),
    source_snapshot_identical_to_original_run=False, changed_frozen_inputs_vs_run_a=changed_vs_original,
    fixture_repair_diff_sha256=sha(OUT / "fixture-window-margin.diff"), fixture_repair_finding=[362, 364, 367],
    host_condition_at_launch=dict(loadavg=Path("/proc/loadavg").read_text().split(),  # finding 409
        top=subprocess.run(["ps", "-eo", "pid,etimes,pcpu,rss,comm", "--sort=-pcpu"], capture_output=True, text=True).stdout.splitlines()[:12]),
    added_inputs={n: frozen[n] for n in ADDED}, session_tmpdir=str(session_tmpdir), session_tmpdir_filesystem="tmpfs:/dev/shm",
    private_basetemp_filesystem="tmpfs:/dev/shm", fidelity_declaration="evidence roots and journals on tmpfs; persistent-media fsync latency not represented",
    maestro_prior_manifest_changed_inputs=maestro_changed,
    outer_deadline_seconds=OUTER_DEADLINE_SECONDS,
    outer_deadline_rationale="outer session runs 1501 Maestro cases and a nested 1796-case child; Maestro-only phase took 1344 s",
    wheel_verification=False, factory_execution=False, accepted=False, merged=False))
command = [PYTHON, "-m", "pytest", "tests", "-q", "--collect-only"]
with (OUT / "collected.log").open("x") as log:
    collection = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=60)
assert collection.returncode == 0
match = re.search(r"(\d+) tests? collected", (OUT / "collected.log").read_text())
assert match and int(match.group(1)) == 2104
save("collection-receipt.json", dict(command=command, cwd=str(ROOT), returncode=0,
    collected=2104, log_sha256=sha(OUT / "collected.log")))

private = Path(tempfile.mkdtemp(prefix="maestro-platform-20261020s-private-", dir="/dev/shm"))
assert any(line.split()[1] == "/dev/shm" and line.split()[2] == "tmpfs" for line in Path("/proc/mounts").read_text().splitlines())
probe_code = r"""
import json,os,signal,sys,time
target,out,seconds=sys.argv[1],sys.argv[2],float(sys.argv[3])
fd=os.open(target,os.O_RDWR|os.O_CREAT|os.O_TRUNC,0o600); stream=open(out,'w')
start=time.monotonic(); n=spikes=0; worst=0.0
stop=[False]
signal.signal(signal.SIGTERM, lambda *a: stop.__setitem__(0, True))
while not stop[0] and time.monotonic()-start<seconds:
    os.write(fd,b'x'*4096); t=time.monotonic(); os.fsync(fd); d=time.monotonic()-t; n+=1; worst=max(worst,d)
    if d>0.15:
        spikes+=1; stream.write(json.dumps(dict(monotonic=t,wall=time.time(),fsync_seconds=round(d,4)))+'\n'); stream.flush()
    time.sleep(0.25)
stream.write(json.dumps(dict(summary=True,samples=n,spikes_over_150ms=spikes,worst_seconds=round(worst,4),started_monotonic=start,seconds=round(time.monotonic()-start,3),terminated=stop[0]))+'\n'); stream.close()
os.close(fd)
try: os.unlink(target)
except FileNotFoundError: pass
"""
probe = subprocess.Popen([PYTHON, "-I", "-c", probe_code, str(session_tmpdir / "fsync-probe.bin"), str(OUT / "fsync-probe.jsonl"), str(OUTER_DEADLINE_SECONDS)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
harness = OUT / "source-harness"
harness.mkdir()
plugin = PLUGIN_SOURCE
env.update(MAESTRO_FULL_RECEIPT_ROOT=str(harness), MAESTRO_BOUNDARY_RECEIPTS=str(harness))
command = [PYTHON, "-m", "pytest", str(ROOT / "tests"), "-q", "-ra", "--basetemp", str(private)]
began = time.monotonic()
timed_out = False
with (OUT / "source.log").open("x") as log:
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log,
                               stderr=subprocess.STDOUT, start_new_session=True)
    save("source-started.json", dict(command=command, cwd=str(ROOT), original_pid=process.pid,
        private_basetemp=str(private), receipt_root=str(harness), collected=2104,
        plugin_sha256=sha(plugin), start_unix_seconds=time.time(),
        outer_deadline_seconds=OUTER_DEADLINE_SECONDS))
    print("platform source started", process.pid, "collected", 2104, flush=True)
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
changed = [n for n, h in frozen.items() if not (ROOT / n).is_file() or sha(ROOT / n) != h]
save("source-receipt.json", dict(command=command, cwd=str(ROOT), returncode=code,
    original_pid=process.pid, elapsed_seconds=time.monotonic() - began,
    original_private_basetemp=str(private), outer_timeout=timed_out,
    outer_deadline_seconds=OUTER_DEADLINE_SECONDS,
    descendant_cleanup_unknown=timed_out, log_sha256=sha(OUT / "source.log"),
    input_manifest_sha256=sha(OUT / "frozen-inputs.json"), changed_frozen_inputs=changed,
    passed_exit_status=code == 0 and not timed_out and not changed,
    verification_python=PYTHON, successor_of="platform-regression-20261020g", plugin_sha256=sha(plugin),
    fsync_probe_present=(OUT / "fsync-probe.jsonl").is_file(), gc_log_present=(OUT / "gc-pauses.jsonl").is_file(),
    terminal_evidence_audit_pending=True, full_runtime_cases_complete=False,
    actual_M1_admissions=0, stable_increment17=False, accepted=False, merged=False))
print("platform source terminal", code, "changed inputs", changed, flush=True)
raise SystemExit(code if code else (1 if changed or timed_out else 0))
