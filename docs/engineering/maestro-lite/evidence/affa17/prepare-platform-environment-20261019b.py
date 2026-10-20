"""Prepare separate build-capable verification Python; execute no product tests."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

BASE = Path(__file__).resolve().parent
OUT = BASE / "platform-environment-20261019b"
TARGET = Path("/tmp/maestro-lite-platform-regression-target-20261019b")
PYTHON = TARGET / "bin/python"
PRIOR = BASE / "integrated-maestro-20261019b"
BUILD_PYTHON = "/tmp/maestro-lite-affa-verify-20261018/bin/python"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
OUT.mkdir(exist_ok=False)
assert not TARGET.exists()

def save(name, value):
    with (OUT / name).open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")

commands = []
def run(label, command, **kwargs):
    with (OUT / (label + ".log")).open("x") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=180, **kwargs)
    commands.append(dict(command=command, returncode=result.returncode,
                         log=label + ".log", log_sha256=sha(OUT / (label + ".log"))))
    save(label + "-receipt.json", commands[-1])
    assert result.returncode == 0, label

packages = ["build", "hatchling", "packaging", "pathspec", "pluggy", "pyproject-hooks", "trove-classifiers"]
version_code = "import json; from importlib.metadata import version; print(json.dumps({n:version(n) for n in " + repr(packages) + "}))"
versions = json.loads(subprocess.check_output([BUILD_PYTHON, "-I", "-c", version_code], text=True))
save("reference-build-versions.json", versions)
run("venv", [sys.executable, "-m", "venv", "--system-site-packages", str(TARGET)])
run("build-tools", [str(PYTHON), "-m", "pip", "install", "--index-url", "https://pypi.org/simple",
    *[name + "==" + versions[name] for name in packages]])
wheel = next((PRIOR / "dist").glob("*.whl"))
assert sha(wheel) == "e1a5119acd81e879214166307b4b4a4fcbe898feeeca7d68d7ab2bd596bdb1d7"
run("candidate-wheel", [str(PYTHON), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)])
actual = json.loads(subprocess.check_output([str(PYTHON), "-I", "-c", version_code], text=True))
assert actual == versions
run("pip-list", [str(PYTHON), "-m", "pip", "list", "--format=json"])
save("preparation.json", dict(driver_sha256=sha(Path(__file__)),
    python=str(PYTHON), candidate_wheel_sha256=sha(wheel), build_versions=actual,
    commands=commands, original_runtime_environment_mutated=False,
    product_tests_executed=False, runtime_execution=False, platform_regression_passed=False,
    accepted=False, merged=False))
print(json.dumps(dict(prepared_python=str(PYTHON), build_versions=actual, product_tests_executed=False)))
