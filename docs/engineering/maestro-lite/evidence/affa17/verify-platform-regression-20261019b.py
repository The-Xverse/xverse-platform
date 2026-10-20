"""Successor combined platform Python regression in the separate build-capable environment.

Successor of verify-platform-regression-20261019a.py (finding 357: the original
environment lacked `build`/`hatchling`, which Argus support.wheel_and_target()
requires). Differences from the original driver, each recorded in configuration.json:

1. PYTHON is the separately prepared environment from platform-environment-20261019b.
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
PRIOR = BASE / "integrated-maestro-20261019b"
ORIGINAL = BASE / "platform-regression-20261019a"
ENVIRONMENT = BASE / "platform-environment-20261019b"
OUT = BASE / "platform-regression-20261019b"
PYTHON = "/tmp/maestro-lite-platform-regression-target-20261019b/bin/python"
OUTER_DEADLINE_SECONDS = 7200
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())

# Original run a must be terminal; never duplicate a live run.
original_receipt = ORIGINAL / "source-receipt.json"
assert original_receipt.is_file(), "original run a has no terminal receipt; do not start a duplicate"
original = read(original_receipt)
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
assert len(maestro) == 273 and all(sha(ROOT / n) == h for n, h in maestro.items())

# Prepared environment identity and build-tool preflight (finding 357).
preparation = read(ENVIRONMENT / "preparation.json")
assert preparation["python"] == PYTHON
assert sha(ENVIRONMENT / "preparation.json") == "0ee24c73d11f73a9e0aa7e33647d1723f4fc04ec8f88c909899b8ff0b979204d"
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
):
    done = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60)
    preflight[label] = dict(command=command, returncode=done.returncode,
                            stdout=done.stdout.strip(), stderr=done.stderr.strip())
    assert done.returncode == 0, label
versions_code = ("import json; from importlib.metadata import version; print(json.dumps({n: version(n) for n in "
                 + repr(sorted(preparation["build_versions"])) + "}))")
actual_versions = json.loads(subprocess.check_output([PYTHON, "-I", "-c", versions_code], text=True))
assert actual_versions == preparation["build_versions"], actual_versions
save("preflight.json", dict(checks=preflight, build_versions=actual_versions,
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
assert frozen == original_manifest, "source snapshot differs from original run a; successor would not isolate the environment variable"
save("frozen-inputs.json", frozen)
with tarfile.open(OUT / "tested-inputs.tar.gz", "w:gz") as archive:
    for p in sorted(paths):
        archive.add(p, arcname=str(p.relative_to(ROOT)))

env = dict(os.environ, PYTHONPATH=str(ROOT / "src"),
           PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
save("configuration.json", dict(
    driver_sha256=sha(Path(__file__)), candidate=str(ROOT),
    successor_of=dict(driver="verify-platform-regression-20261019a.py",
                      driver_sha256=sha(BASE / "verify-platform-regression-20261019a.py"),
                      receipt_sha256=sha(original_receipt), original_returncode=original["returncode"],
                      original_outer_timeout=original["outer_timeout"]),
    git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    git_branch=subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
    git_status=subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
    python=sys.version, executable=sys.executable, verification_python=PYTHON, platform=platform.platform(),
    pytest_version=preflight["pytest"]["stdout"],
    selected_environment={n: env[n] for n in ("PYTHONPATH", "PYTEST_DISABLE_PLUGIN_AUTOLOAD", "PYTHONDONTWRITEBYTECODE")},
    environment_receipt=dict(path=str(ENVIRONMENT.relative_to(ROOT) / "preparation.json"),
                             sha256=sha(ENVIRONMENT / "preparation.json"), build_versions=actual_versions),
    maestro_manifest_sha256=sha(PRIOR / "frozen-inputs.json"),
    prior_audits={p: sha(PRIOR / ("maestro_full-" + p + "-terminal-audit/audit.json")) for p in ("source", "wheel")},
    scope="all collected platform Python tests in one source session; C++ suites are separate",
    source_snapshot_paths=len(frozen), source_snapshot_manifest_sha256=sha(OUT / "frozen-inputs.json"),
    source_snapshot_identical_to_original_run=True,
    outer_deadline_seconds=OUTER_DEADLINE_SECONDS,
    outer_deadline_rationale="outer session runs 1501 Maestro cases and a nested 1796-case child; Maestro-only phase took 1344 s",
    wheel_verification=False, factory_execution=False, accepted=False, merged=False))
command = [PYTHON, "-m", "pytest", "tests", "-q", "--collect-only"]
with (OUT / "collected.log").open("x") as log:
    collection = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=60)
assert collection.returncode == 0
match = re.search(r"(\d+) tests? collected", (OUT / "collected.log").read_text())
assert match and int(match.group(1)) == 2080
save("collection-receipt.json", dict(command=command, cwd=str(ROOT), returncode=0,
    collected=2080, log_sha256=sha(OUT / "collected.log")))

private = Path(tempfile.mkdtemp(prefix="maestro-platform-20261019b-private-"))
harness = OUT / "source-harness"
harness.mkdir()
plugin = PRIOR / "receipt_namespace.py"
assert sha(plugin) == read(PRIOR / "control-inputs.json")["plugin_sha256"]
env.update(MAESTRO_FULL_RECEIPT_ROOT=str(harness), MAESTRO_BOUNDARY_RECEIPTS=str(harness))
args = [str(ROOT / "tests"), "-q", "-ra", "--basetemp", str(private)]
wrapper = ("import importlib.util,pytest; spec=importlib.util.spec_from_file_location('owned_receipt_namespace',"
           + repr(str(plugin)) + "); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); "
           + "raise SystemExit(pytest.main(" + repr(args) + ",plugins=[module]))")
command = [PYTHON, "-c", wrapper]
began = time.monotonic()
timed_out = False
with (OUT / "source.log").open("x") as log:
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log,
                               stderr=subprocess.STDOUT, start_new_session=True)
    save("source-started.json", dict(command=command, cwd=str(ROOT), original_pid=process.pid,
        private_basetemp=str(private), receipt_root=str(harness), collected=2080,
        plugin_sha256=sha(plugin), start_unix_seconds=time.time(),
        outer_deadline_seconds=OUTER_DEADLINE_SECONDS))
    print("platform source started", process.pid, "collected 2080", flush=True)
    try:
        code = process.wait(timeout=OUTER_DEADLINE_SECONDS)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        code = process.wait()

changed = [n for n, h in frozen.items() if not (ROOT / n).is_file() or sha(ROOT / n) != h]
save("source-receipt.json", dict(command=command, cwd=str(ROOT), returncode=code,
    original_pid=process.pid, elapsed_seconds=time.monotonic() - began,
    original_private_basetemp=str(private), outer_timeout=timed_out,
    outer_deadline_seconds=OUTER_DEADLINE_SECONDS,
    descendant_cleanup_unknown=timed_out, log_sha256=sha(OUT / "source.log"),
    input_manifest_sha256=sha(OUT / "frozen-inputs.json"), changed_frozen_inputs=changed,
    passed_exit_status=code == 0 and not timed_out and not changed,
    verification_python=PYTHON, successor_of="platform-regression-20261019a",
    terminal_evidence_audit_pending=True, full_runtime_cases_complete=False,
    actual_M1_admissions=0, stable_increment17=False, accepted=False, merged=False))
print("platform source terminal", code, "changed inputs", changed, flush=True)
raise SystemExit(code if code else (1 if changed or timed_out else 0))
