"""Bounded two-phase verification of the IR-ML3-04 lane admission controls (finding 382).

Modules: the lane admission test (real pins from lane-admission-proposal-20261020.json through
MAESTRO_LANE_PROPOSAL), the F-01 release-timeout fence control and the AFFA client module that holds
the F-02 precondition test. Source phase: candidate src on PYTHONPATH; wheel phase: the exact candidate
wheel in the prepared environment d, test files copied outside the tree. Receipts retained through the
installed receipt-namespace plugin. Not a factory run, not acceptance, not M1, no lane activation.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
OUT = BASE / "lane-admission-20261020b"
ENV = BASE / "platform-environment-20261020d"
PYTHON = "/tmp/maestro-lite-platform-regression-target-20261020d/bin/python"
MODULES = ("tests/thesis_lite/maestro/test_runtime_lane_admission.py",
           "tests/thesis_lite/maestro/test_affa_release_timeout_fence.py",
           "tests/thesis_lite/maestro/test_affa_client.py")
PROPOSAL = BASE / "lane-admission-proposal-20261020.json"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())

preparation = read(ENV / "preparation.json")
assert preparation["python"] == PYTHON and Path(PYTHON).is_file()
installed = subprocess.run([PYTHON, "-I", "-c", "import xverse.maestro, hashlib, importlib.metadata as m; print(m.version('xverse-xdl'))"],
                           text=True, capture_output=True, timeout=60)
assert installed.returncode == 0, installed.stderr
OUT.mkdir(exist_ok=False)

def save(name, value):
    with (OUT / name).open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")

packaged = sorted(p for p in (ROOT / "src").rglob("*") if p.is_file() and p.suffix in (".py", ".c", ".h") and "__pycache__" not in p.parts)
inputs = {str(p.relative_to(ROOT)): sha(p) for p in [*packaged, *(ROOT / "tests/thesis_lite/maestro").iterdir()] if p.is_file()}
save("frozen-inputs.json", inputs)
save("configuration.json", dict(driver_sha256=sha(Path(__file__)), candidate=str(ROOT),
    git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    verification_python=PYTHON, environment_receipt_sha256=sha(ENV / "preparation.json"),
    candidate_wheel_sha256=preparation["candidate_wheel_sha256"], installed_xverse_xdl_version=installed.stdout.strip(),
    modules=list(MODULES), module_sha256={m: sha(ROOT / m) for m in MODULES},
    packaged_source_count=len(packaged), frozen_input_count=len(inputs), lane_admission_proposal_sha256=sha(PROPOSAL),
    private_basetemp_filesystem="tmpfs:/dev/shm", factory_execution=False, accepted=False, merged=False, admitted_m1_run=False))

rows = []
consumer = Path(tempfile.mkdtemp(prefix="lane-admission-consumer-", dir="/dev/shm"))
shutil.copytree(ROOT / "tests", consumer / "tests", ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
shutil.copytree(ROOT / "xdl", consumer / "xdl")  # profile schemas resolved by the preparation helper
for phase, cwd, isolated in (("source", ROOT, False), ("wheel", consumer, True)):
    private = Path(tempfile.mkdtemp(prefix="lane-admission-" + phase + "-private-", dir="/dev/shm"))
    harness = OUT / (phase + "-harness")
    harness.mkdir()
    env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1",
               PYTEST_PLUGINS="maestro_receipt_namespace", MAESTRO_FULL_RECEIPT_ROOT=str(harness),
               MAESTRO_BOUNDARY_RECEIPTS=str(harness), MAESTRO_LANE_PROPOSAL=str(PROPOSAL))
    if not isolated:
        env["PYTHONPATH"] = str(ROOT / "src")
    else:
        env.pop("PYTHONPATH", None)
    command = [PYTHON, *(["-I"] if isolated else []), "-m", "pytest", *[str(cwd / m) for m in MODULES],
               "-q", "-ra", "-p", "no:cacheprovider", "--basetemp", str(private)]
    began = time.monotonic()
    with (OUT / (phase + ".log")).open("x") as log:
        done = subprocess.run(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=1800)
    text = (OUT / (phase + ".log")).read_text()
    summary = next((line for line in reversed(text.splitlines()) if "passed" in line or "failed" in line), None)
    rows.append(dict(phase=phase, command=command, cwd=str(cwd), returncode=done.returncode,
                     elapsed_seconds=round(time.monotonic() - began, 3), private_basetemp=str(private),
                     log_sha256=sha(OUT / (phase + ".log")), summary=summary,
                     receipts=sorted(p.name for p in harness.rglob("lane-admission-*.json")) + sorted(p.name for p in harness.rglob("release-timeout-fence-*.json"))))
    print(phase, done.returncode, summary, flush=True)
changed = [n for n, h in inputs.items() if sha(ROOT / n) != h]
save("receipt.json", dict(phases=rows, changed_frozen_inputs=changed,
    passed=all(r["returncode"] == 0 for r in rows) and not changed,
    lane_admission_proposal_sha256=sha(PROPOSAL), controls=["lane admission with real pins (fail-closed)", "F-01 release-timeout fence", "F-02 unwatched ADVANCE rejection"], admitted_m1_run=False, lane_activated=False, accepted=False, merged=False))
raise SystemExit(0 if all(r["returncode"] == 0 for r in rows) and not changed else 1)
