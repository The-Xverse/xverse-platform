"""ARGUS2-SR-012-U: additive packaging, installed-wheel compatibility and preserved contracts."""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile

from xverse.argus import EvidenceStore

try:
    from tests.thesis_lite.argus import support as S
except ImportError:  # pragma: no cover - copied tests-directory layout
    import sys as _argus2_sys
    from pathlib import Path as _argus2_path

    _argus2_sys.path.insert(0, str(_argus2_path(__file__).resolve().parent))
    import support as S

_PROTECTED_TREES = ("src/xverse/xcom", "src/xverse_xdl", "xdl", "proto")


def test_xverse_argus_imports_from_installed_wheel():
    _wheel, target = S.wheel_and_target()
    completed = S.installed_python(
        "import xverse.argus, sys; print(xverse.argus.__file__)", target
    )
    assert completed.returncode == 0, completed.stderr
    assert str(target) in completed.stdout
    assert "/workspace/src" not in completed.stdout


def test_xverse_xdl_imports_from_installed_wheel():
    _wheel, target = S.wheel_and_target()
    completed = S.installed_python(
        "import xverse_xdl.experiment_plan as e; print(e.__file__)", target
    )
    assert completed.returncode == 0, completed.stderr
    assert str(target) in completed.stdout


def test_existing_xdl_console_entry_point_preserved():
    _wheel, target = S.wheel_and_target()
    script = (
        "import importlib.metadata as md, json;"
        "dist = md.distribution('xverse-xdl');"
        "print(json.dumps({'name': dist.metadata['Name'],"
        " 'entry_points': {e.name: e.value for e in dist.entry_points}}))"
    )
    completed = S.installed_python(script, target)
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["name"] == "xverse-xdl"
    assert payload["entry_points"]["xdl"] == "xverse_xdl.cli:main"


def test_additive_xverse_argus_console_entry_point_present():
    _wheel, target = S.wheel_and_target()
    script = (
        "import importlib.metadata as md, json;"
        "dist = md.distribution('xverse-xdl');"
        "print(json.dumps({e.name: e.value for e in dist.entry_points}))"
    )
    completed = S.installed_python(script, target)
    assert completed.returncode == 0, completed.stderr
    entry_points = json.loads(completed.stdout)
    assert entry_points["xverse-argus"] == "xverse.argus.cli:main"


def test_wheel_does_not_package_the_xcom_cpp_tree():
    wheel, _target = S.wheel_and_target()
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    assert "xverse/argus/__init__.py" in names
    assert "xverse_xdl/__init__.py" in names
    assert not [name for name in names if "xcom" in name and name.endswith((".hpp", ".cpp"))]


def test_unknown_major_schema_rejected_from_installed_wheel(tmp_path):
    _wheel, target = S.wheel_and_target()
    root = S.synthetic_run(tmp_path / "run", S.annotation_event_bytes(), schemaVersion="2.0")
    script = (
        "import json, sys;"
        "from xverse.argus import EvidenceStore;"
        "r = EvidenceStore.read_run(sys.argv[1]);"
        "print(json.dumps([d.code for d in r.diagnostics]))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script, str(root)],
        cwd=str(S.HERE),
        text=True,
        capture_output=True,
        check=False,
        env=S.installed_env(target),
    )
    assert completed.returncode == 0, completed.stderr
    assert "ARGUS2-SCHEMA-MAJOR-UNSUPPORTED" in json.loads(completed.stdout)


def test_additive_unknown_field_behaviour_is_explicit(tmp_path):
    _wheel, target = S.wheel_and_target()
    unknown_root = S.synthetic_run(tmp_path / "unknown", S.annotation_event_bytes(unknown=True))
    known_root = S.synthetic_run(
        tmp_path / "known",
        S.annotation_event_bytes(extensions={"argus.note": {"v": 1}}),
    )
    script = (
        "import json, sys;"
        "from xverse.argus import EvidenceStore;"
        "unknown = EvidenceStore.read_run(sys.argv[1]);"
        "known = EvidenceStore.read_run(sys.argv[2]);"
        "print(json.dumps({'unknown': [d.code for d in unknown.diagnostics],"
        " 'extension': json.loads(known.export_json())['records'][0].get('extensions')}))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script, str(unknown_root), str(known_root)],
        cwd=str(S.HERE),
        text=True,
        capture_output=True,
        check=False,
        env=S.installed_env(target),
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert "ARGUS2-SCHEMA-UNKNOWN-FIELD" in payload["unknown"]
    assert payload["extension"] == {"argus.note": {"v": 1}}


def test_owned_argus_tests_run_against_installed_wheel_with_empty_pythonpath(tmp_path):
    _wheel, target = S.wheel_and_target()
    destination = tmp_path / "owned"
    destination.mkdir()
    S.copy_owned_tests(destination)
    environment = S.installed_env(target)
    environment["PYTHONPATH"] = str(target)
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(destination)],
        cwd=str(destination),
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    assert completed.returncode == 0, f"{completed.stdout}\n{completed.stderr}"
    assert "failed" not in completed.stdout


def test_no_accepted_cpp_or_xdl_source_is_modified():
    tokens = ("xverse.argus", "ARGUS2", "argus2")
    for tree in _PROTECTED_TREES:
        base = S.ROOT / tree
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            assert not any(token in text for token in tokens), path


def test_xdl_cli_behaviour_is_preserved():
    _wheel, target = S.wheel_and_target()
    completed = subprocess.run(
        [sys.executable, "-m", "xverse_xdl", "version", "--format", "json"],
        cwd=str(S.HERE),
        text=True,
        capture_output=True,
        check=False,
        env=S.installed_env(target),
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["supportedApiVersions"] == ["xverse.io/xdl/v1alpha1"]
    _ = EvidenceStore
