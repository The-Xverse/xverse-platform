"""Prepare verification environment f for increment18 (findings 393, 397): a wheel of the two-pass tree.

Successor of affa17/prepare-platform-environment-20261020d.py. Differences: the candidate wheel is built
here from the increment18 worktree (python -m build --wheel --no-isolation, the recipe of the earlier
drivers) instead of reusing the 2026-10-19 wheel; the build uses environment d's interpreter, which has
the pinned build tools. Same pinned build tools and the same receipt-namespace plugin v3 are installed
into the new environment. Executes no product tests.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
AFFA17 = BASE.parent / "affa17"
OUT = BASE / "platform-environment-20261020f"
TARGET = Path("/tmp/maestro-lite-platform-regression-target-20261020f")
PYTHON = TARGET / "bin/python"
BUILD_PYTHON = Path("/tmp/maestro-lite-platform-regression-target-20261020d/bin/python")
REFERENCE = AFFA17 / "platform-environment-20261019b"
PLUGIN = AFFA17 / "maestro_receipt_namespace_v3.py"
INSTALLED_NAME = "maestro_receipt_namespace.py"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
OUT.mkdir(exist_ok=False)
assert not TARGET.exists() and BUILD_PYTHON.is_file()

def save(name, value):
    with (OUT / name).open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")

commands = []
def run(label, command, **kwargs):
    with (OUT / (label + ".log")).open("x") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=300, **kwargs)
    commands.append(dict(command=[str(c) for c in command], returncode=result.returncode,
                         log=label + ".log", log_sha256=sha(OUT / (label + ".log"))))
    save(label + "-receipt.json", commands[-1])
    assert result.returncode == 0, label

reference = json.loads((REFERENCE / "preparation.json").read_bytes())
assert sha(REFERENCE / "preparation.json") == "0ee24c73d11f73a9e0aa7e33647d1723f4fc04ec8f88c909899b8ff0b979204d"
versions = reference["build_versions"]
packages = sorted(versions)
version_code = "import json; from importlib.metadata import version; print(json.dumps({n:version(n) for n in " + repr(packages) + "}))"
sources = {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / "src").rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
save("wheel-sources.json", sources)
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
status = subprocess.check_output(["git", "status", "--porcelain", "--", "src"], cwd=ROOT, text=True)
run("candidate-build", [str(BUILD_PYTHON), "-m", "build", "--wheel", "--no-isolation", "--outdir", str(OUT / "dist"), str(ROOT)])
wheel = next((OUT / "dist").glob("*.whl"))
assert {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / "src").rglob("*")) if p.is_file() and "__pycache__" not in p.parts} == sources
run("venv", [sys.executable, "-m", "venv", "--system-site-packages", str(TARGET)])
run("build-tools", [str(PYTHON), "-m", "pip", "install", "--index-url", "https://pypi.org/simple",
    *[name + "==" + versions[name] for name in packages]])
run("candidate-wheel", [str(PYTHON), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)])
actual = json.loads(subprocess.check_output([str(PYTHON), "-I", "-c", version_code], text=True))
assert actual == versions
site = Path(subprocess.check_output([str(PYTHON), "-I", "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"], text=True).strip())
assert site.is_relative_to(TARGET), site
installed_authority = site / "xverse/maestro/native/run_authority.c"
assert sha(installed_authority) == sha(ROOT / "src/xverse/maestro/native/run_authority.c"), "installed helper differs from the tree"
installed_plugin = site / INSTALLED_NAME
shutil.copyfile(PLUGIN, installed_plugin)
assert sha(installed_plugin) == sha(PLUGIN)
probe = subprocess.run([str(PYTHON), "-I", "-c", "import maestro_receipt_namespace as m; print(m.__file__)"],
                       text=True, capture_output=True, timeout=60)
assert probe.returncode == 0 and str(installed_plugin) in probe.stdout, probe
save("plugin-receipt.json", dict(source=str(PLUGIN.relative_to(ROOT)), sha256=sha(PLUGIN),
    installed=str(installed_plugin), import_probe_stdout=probe.stdout.strip()))
run("pip-list", [str(PYTHON), "-m", "pip", "list", "--format=json"])
save("preparation.json", dict(driver_sha256=sha(Path(__file__)), python=str(PYTHON), base_executable=sys.executable,
    build_python=str(BUILD_PYTHON), candidate_git_head=head, candidate_src_status=status, wheel=wheel.name,
    candidate_wheel_sha256=sha(wheel), wheel_source_count=len(sources), wheel_sources_sha256=sha(OUT / "wheel-sources.json"),
    installed_run_authority_sha256=sha(installed_authority), build_versions=actual,
    plugin_sha256=sha(PLUGIN), plugin_installed=str(installed_plugin), commands=commands,
    reference_preparation_sha256=sha(REFERENCE / "preparation.json"),
    original_runtime_environment_mutated=False, product_tests_executed=False, runtime_execution=False,
    platform_regression_passed=False, accepted=False, merged=False))
print(json.dumps(dict(prepared_python=str(PYTHON), wheel=wheel.name, wheel_sha256=sha(wheel), installed_run_authority_sha256=sha(installed_authority))))
