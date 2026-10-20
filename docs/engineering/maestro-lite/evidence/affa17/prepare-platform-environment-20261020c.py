"""Prepare verification environment c: build-capable plus importable receipt-namespace plugin.

Successor of prepare-platform-environment-20261019b.py. Same pinned build tools and the
same candidate wheel; additionally installs maestro_receipt_namespace.py into site-packages
so PYTEST_PLUGINS can name it in every session that uses this interpreter, including
child sessions spawned with PYTHONPATH=<installed target> by accepted Argus tests.
Executes no product tests.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import sysconfig

BASE = Path(__file__).resolve().parent
OUT = BASE / "platform-environment-20261020c"
TARGET = Path("/tmp/maestro-lite-platform-regression-target-20261020c")
PYTHON = TARGET / "bin/python"
PRIOR = BASE / "integrated-maestro-20261019b"
REFERENCE = BASE / "platform-environment-20261019b"
PLUGIN = BASE / "maestro_receipt_namespace.py"
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

reference = json.loads((REFERENCE / "preparation.json").read_bytes())
assert sha(REFERENCE / "preparation.json") == "0ee24c73d11f73a9e0aa7e33647d1723f4fc04ec8f88c909899b8ff0b979204d"
versions = reference["build_versions"]
packages = sorted(versions)
version_code = "import json; from importlib.metadata import version; print(json.dumps({n:version(n) for n in " + repr(packages) + "}))"
run("venv", [sys.executable, "-m", "venv", "--system-site-packages", str(TARGET)])
run("build-tools", [str(PYTHON), "-m", "pip", "install", "--index-url", "https://pypi.org/simple",
    *[name + "==" + versions[name] for name in packages]])
wheel = next((PRIOR / "dist").glob("*.whl"))
assert sha(wheel) == "e1a5119acd81e879214166307b4b4a4fcbe898feeeca7d68d7ab2bd596bdb1d7"
run("candidate-wheel", [str(PYTHON), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)])
actual = json.loads(subprocess.check_output([str(PYTHON), "-I", "-c", version_code], text=True))
assert actual == versions
site = Path(subprocess.check_output([str(PYTHON), "-I", "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"], text=True).strip())
assert site.is_relative_to(TARGET), site
installed_plugin = site / PLUGIN.name
shutil.copyfile(PLUGIN, installed_plugin)
assert sha(installed_plugin) == sha(PLUGIN)
probe = subprocess.run([str(PYTHON), "-I", "-c", "import maestro_receipt_namespace as m; print(m.__file__)"],
                       text=True, capture_output=True, timeout=60)
assert probe.returncode == 0 and str(installed_plugin) in probe.stdout, probe
save("plugin-receipt.json", dict(source=str(PLUGIN.relative_to(BASE.parents[4])), sha256=sha(PLUGIN),
    installed=str(installed_plugin), import_probe_stdout=probe.stdout.strip()))
run("pip-list", [str(PYTHON), "-m", "pip", "list", "--format=json"])
save("preparation.json", dict(driver_sha256=sha(Path(__file__)), python=str(PYTHON),
    base_executable=sys.executable, candidate_wheel_sha256=sha(wheel), build_versions=actual,
    plugin_sha256=sha(PLUGIN), plugin_installed=str(installed_plugin), commands=commands,
    reference_preparation_sha256=sha(REFERENCE / "preparation.json"),
    original_runtime_environment_mutated=False, product_tests_executed=False, runtime_execution=False,
    platform_regression_passed=False, accepted=False, merged=False))
print(json.dumps(dict(prepared_python=str(PYTHON), build_versions=actual, plugin_sha256=sha(PLUGIN), product_tests_executed=False)))
