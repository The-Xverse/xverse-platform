"""ARGUS2-INTEGRATION: real compiler, owned C++ producer, wheel and preserved contracts.

These cases exercise the real accepted XDL compiler output, the real owned C++20 X-COM producer
fixture compiled against the accepted headers/implementation, and the offline built-and-installed
wheel. Synthetic dictionaries alone are not used for interoperability. Whole-system integration in
the pinned target assembly remains an external trusted-host gate.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from xverse.argus import EvidenceError, EvidenceStore

try:
    from tests.thesis_lite.argus import support as S
except ImportError:  # pragma: no cover - copied tests-directory layout
    import sys as _argus2_sys
    from pathlib import Path as _argus2_path

    _argus2_sys.path.insert(0, str(_argus2_path(__file__).resolve().parent))
    import support as S

_MAPPED_FIELDS = (
    "contractId",
    "contractVersion",
    "interfaceId",
    "endpointId",
    "schemaId",
    "schemaVersion",
    "interactionKind",
    "origin",
    "sourceClock",
    "observationClock",
    "sequence",
    "correlationId",
    "causationId",
    "routeId",
    "providerId",
    "sourcePayloadSize",
    "providerOutcome",
    "payloadViewState",
    "payloadSchemaState",
    "visibleBytesHex",
    "visibleByteCount",
    "tapId",
    "counters",
)


def test_real_accepted_xdl_compiler_output_written_and_reconstructed(tmp_path):
    from xverse_xdl.experiment_plan import compile_experiment_files

    result = compile_experiment_files(S.FIXTURE_PATHS, profile_schema_paths=(S.profile_schema_path(),))
    assert result.is_valid, [item.code for item in result.diagnostics]
    assert result.plan is not None and result.plan["digest"]["value"]
    root = S.run_root(tmp_path)
    run = EvidenceStore.open_run(root, run_id="run-integration", plan=result.plan)
    run.append_event(event_id="e1", producer_id="producer.alpha", event_kind="annotation", annotation={"text": "real"})
    manifest = run.finalize()
    assert manifest.evidence_status == "complete"
    reader = EvidenceStore.read_run(root)
    assert [item["eventId"] for item in reader.records()] == ["e1"]
    assert reader.manifest["plan"]["semanticDigest"]["value"] == result.plan["digest"]["value"]


def test_real_owned_cpp_observation_fixture_compiles_and_imports_by_value(tmp_path):
    produced = S.run_producer()
    records = produced["projection"]["records"]
    assert len(records) >= 4
    run = S.open_run(S.run_root(tmp_path), run_id="run-cpp")
    run.import_observation(produced["projection"])
    run.import_snapshot(produced["snapshot"])
    run.finalize()
    stored = [
        item["observation"]
        for item in EvidenceStore.read_run(S.run_root(tmp_path)).records()
        if item["eventKind"] == "observation"
    ]
    for source, imported in zip(records, stored):
        for field in _MAPPED_FIELDS:
            assert imported[field] == source[field], field


def test_real_owned_cpp_snapshot_fixture_preserves_interval_and_counters(tmp_path):
    produced = S.run_producer()
    snapshot = produced["snapshot"]
    run = S.open_run(S.run_root(tmp_path), run_id="run-cpp")
    run.import_snapshot(snapshot)
    run.finalize()
    stored = [
        item["snapshot"]
        for item in EvidenceStore.read_run(S.run_root(tmp_path)).records()
        if item["eventKind"] == "snapshot"
    ][0]
    for field in (
        "queued",
        "accepted",
        "dropped",
        "coalesced",
        "backpressureRejections",
        "experimentValidityDegraded",
        "declaredTapId",
        "validityEffect",
        "validityState",
        "intervalProvenance",
    ):
        assert stored[field] == snapshot[field], field


def test_owned_cpp_projection_roundtrip_with_accepted_xcom_headers(tmp_path):
    produced = S.run_producer()
    assert produced["contractVersion"] == "1.0.0"
    assert produced["projection"]["upstreamContractVersion"] == "1.0.0"
    run = S.open_run(S.run_root(tmp_path), run_id="run-cpp")
    run.import_observation(produced["projection"])
    run.finalize()
    document = json.loads(EvidenceStore.read_run(S.run_root(tmp_path)).export_json())
    observations = [item for item in document["records"] if item["eventKind"] == "observation"]
    assert len(observations) == len(produced["projection"]["records"])
    for source, stored in zip(produced["projection"]["records"], observations):
        assert stored["observation"]["contractId"] == source["contractId"]
        assert stored["observation"]["interfaceId"] == source["interfaceId"]


def test_installed_wheel_imports_xverse_argus_and_xverse_xdl_outside_source_tree():
    _wheel, target = S.wheel_and_target()
    completed = S.installed_python(
        "import xverse.argus, xverse_xdl.experiment_plan as e, sys;"
        "print(xverse.argus.__file__); print(e.__file__)",
        target,
    )
    assert completed.returncode == 0, completed.stderr
    assert str(target) in completed.stdout
    assert "/workspace/src" not in completed.stdout


def test_owned_argus_tests_repeat_against_installed_wheel_with_empty_pythonpath(tmp_path):
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


def test_existing_platform_pytest_regression_unchanged_in_assembled_target():
    root = S.platform_source_root()
    completed = subprocess.run(
        [
            sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "--ignore", str(root / "tests" / "thesis_lite" / "argus"),
            str(root / "tests"),
        ],
        cwd=str(root),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, f"{completed.stdout[-4000:]}\n{completed.stderr[-4000:]}"


def test_existing_xdl_cli_and_public_api_preserved_in_assembled_target():
    environment = dict(__import__("os").environ)
    environment.setdefault("PYTHONPATH", str(S.ROOT / "src"))
    version = subprocess.run(
        [sys.executable, "-m", "xverse_xdl", "version", "--format", "json"],
        cwd=str(S.HERE),
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    assert version.returncode == 0, version.stderr
    assert json.loads(version.stdout)["supportedApiVersions"] == ["xverse.io/xdl/v1alpha1"]
    from xverse_xdl.experiment_plan import compile_experiment_files

    result = compile_experiment_files(S.FIXTURE_PATHS, profile_schema_paths=(S.profile_schema_path(),))
    assert result.is_valid


def test_gateway_protobuf_observation_not_substituted_for_owned_projection(tmp_path):
    run = S.open_run(S.run_root(tmp_path), run_id="run-cpp")
    with pytest.raises(EvidenceError) as error:
        run.import_observation(S.projection([S.gateway_record()]))
    assert "ARGUS2-INPUT-PROJECTION-INCOMPLETE" in error.value.codes
