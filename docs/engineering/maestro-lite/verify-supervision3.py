"""Verify a prebuilt installed candidate, retaining exact commands and bounded logs."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/engineering/maestro-lite/evidence/supervision3"
PYTHON = Path(os.path.abspath(sys.argv[1]))
ENV = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
ENV.pop("PYTHONPATH", None)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + "\n")


def snapshot():
    manifest = json.loads((OUT / "source-manifest.json").read_text())
    return {p: sha(ROOT / p) for p in manifest["input_sha256"]}


def run(name, command, cwd, timeout):
    began = time.monotonic()
    with (OUT / (name + ".log")).open("w") as log:
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                env=ENV,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=timeout,
            )
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = "harness-timeout"
    receipt = dict(
        command=list(map(str, command)),
        cwd=str(cwd),
        returncode=code,
        elapsed_seconds=time.monotonic() - began,
        timeout_seconds=timeout,
        PYTHONPATH="unset",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        log_sha256=sha(OUT / (name + ".log")),
    )
    save(name + "-receipt.json", receipt)
    print(name, code, flush=True)
    return receipt


if __name__ == "__main__":
    before = snapshot()
    assert (
        before == json.loads((OUT / "source-manifest.json").read_text())["input_sha256"]
    )
    modules = [
        "xverse.maestro",
        "xverse.maestro.projection",
        "xverse.maestro.time",
        "xverse.maestro.admission",
        "xverse.maestro.supervisor",
        "xverse_xdl.lifecycle",
        "xverse_xdl.catalog",
        "xverse.argus",
    ]
    probe = """import hashlib,importlib,json,pathlib,sys
modules = json.loads(sys.argv[1])
root = sys.argv[2]
assert not any(root in p for p in sys.path)
print(json.dumps({n:{'file':str(pathlib.Path(importlib.import_module(n).__file__).resolve()),
'sha256':hashlib.sha256(pathlib.Path(importlib.import_module(n).__file__).read_bytes()).hexdigest()}
for n in modules}))
"""
    with tempfile.TemporaryDirectory(
        prefix="maestro-supervision3-consumer-"
    ) as temporary:
        consumer = Path(temporary)
        identity = json.loads(
            subprocess.check_output(
                [str(PYTHON), "-I", "-c", probe, json.dumps(modules), str(ROOT)],
                cwd=consumer,
                env=ENV,
                text=True,
            )
        )
        for name, record in identity.items():
            path = Path("src") / Path(*name.split("."))
            path = (
                path.with_suffix(".py")
                if (ROOT / path).with_suffix(".py").is_file()
                else path / "__init__.py"
            )
            assert sha(ROOT / path) == record["sha256"], name
            assert str(ROOT) not in record["file"], name
        save("installed-module-identity.json", identity)
        (consumer / "tests/thesis_lite").mkdir(parents=True)
        for part in ["tests/__init__.py", "tests/thesis_lite/__init__.py"]:
            shutil.copyfile(ROOT / part, consumer / part)
        shutil.copytree(
            ROOT / "tests/thesis_lite/maestro",
            consumer / "tests/thesis_lite/maestro",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        shutil.copytree(ROOT / "xdl/profiles", consumer / "xdl/profiles")
        save(
            "environment-packages.json",
            json.loads(
                subprocess.check_output(
                    [
                        str(PYTHON),
                        "-I",
                        "-c",
                        "import importlib.metadata as m,json;print(json.dumps(sorted((d.metadata['Name'],d.version) for d in m.distributions())))",
                    ],
                    cwd=consumer,
                    env=ENV,
                    text=True,
                )
            ),
        )
        with ThreadPoolExecutor(max_workers=2) as executor:
            full = executor.submit(
                run,
                "platform-tests",
                [str(PYTHON), "-m", "pytest", "tests", "-q", "--disable-warnings"],
                ROOT,
                300,
            )
            wheel = executor.submit(
                run,
                "wheel-consumer-tests",
                [
                    str(PYTHON),
                    "-I",
                    "-m",
                    "pytest",
                    str(consumer / "tests/thesis_lite/maestro"),
                    "-q",
                    "--disable-warnings",
                ],
                consumer,
                120,
            )
            receipts = [full.result(), wheel.result()]
    stable = before == snapshot()
    save(
        "verification-run.json",
        dict(
            source_unchanged=stable,
            receipts=receipts,
            installed_modules_matched=len(identity),
        ),
    )
    assert stable and all(r["returncode"] == 0 for r in receipts)
