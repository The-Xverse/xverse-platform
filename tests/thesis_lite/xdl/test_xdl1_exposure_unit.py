"""XDL1-SR-016-U: additive public API and CLI exposure unit cases."""

from __future__ import annotations

import json
import subprocess
import sys

import xverse_xdl
from xverse_xdl.experiment_plan import (
    ExperimentLimits, ExperimentPlanResult, compile_experiment_files, compile_experiment_plan,
    compile_experiment_sources,
)
from xverse_xdl.models import FrozenMap

from tests.thesis_lite.xdl import support as S

PRE_XDL1_EXPORTS = {
    "SUPPORTED_API_VERSIONS", "CatalogBuildResult", "CatalogEntry", "Diagnostic", "ElementIdentity",
    "EvidenceRecord", "EvidenceWriteError", "ExecutionPermit", "FileEvidenceJournal", "FixtureProvider",
    "FrozenMap", "InMemoryEvidenceJournal", "IsolationAttestation", "LifecycleController",
    "LifecycleDiagnostic", "LifecycleError", "LifecyclePlan", "LifecycleProvider", "LifecycleResult",
    "LoadLimits", "NormalizedResource", "ResourceIdentity", "ResolvedReference", "Severity",
    "SourceInput", "SourceLocation", "OwnedResourceHandle", "PlanAction", "ProcessAction",
    "ProcessProvider", "RUNTIME_PROFILE_NAMESPACE", "StaticReadiness", "ValidationGate",
    "ValidationResult", "__version__", "build_lifecycle_plan", "canonical_json",
    "catalog_entry_public_data", "derive_catalog", "validate_files", "validate_sources",
}


def run_cli(*arguments: str):
    return subprocess.run(
        [sys.executable, "-m", "xverse_xdl", *arguments],
        cwd=S.ROOT, text=True, capture_output=True, check=False,
    )


def fixture_arguments() -> list[str]:
    return ["--profile-schema", str(S.PROFILE_SCHEMA_PATH), *(str(p) for p in S.FIXTURE_PATHS)]


def test_public_api_exports_present():
    for name in (
        "ExperimentLimits", "ExperimentPlanResult", "compile_experiment_plan",
        "compile_experiment_sources", "compile_experiment_files", "canonical_plan_bytes",
        "compute_plan_digest", "plan_matches_digest", "experiment_plan_status",
    ):
        assert hasattr(xverse_xdl, name), name
    assert callable(compile_experiment_plan)
    assert callable(compile_experiment_sources)
    assert callable(compile_experiment_files)
    assert ExperimentLimits().max_ticks == 9007199254740991


def test_init_all_is_additive_superset():
    assert PRE_XDL1_EXPORTS <= set(xverse_xdl.__all__)
    assert set(xverse_xdl.__all__) >= PRE_XDL1_EXPORTS


def test_compile_api_result_shape():
    valid = S.compile_declared(S.declared())
    invalid = S.compile_declared(S.declared(scenario=_without_seed()))
    assert isinstance(valid, ExperimentPlanResult)
    assert isinstance(valid.diagnostics, tuple)
    assert isinstance(valid.plan, dict)
    assert isinstance(valid.run, FrozenMap)
    assert valid.is_valid is True
    assert invalid.plan is None
    assert invalid.is_valid is False


def _without_seed():
    scenario = S.scenario_resource()
    from xverse_xdl.experiment_plan import PROFILE_NAMESPACE

    del scenario["extensions"][PROFILE_NAMESPACE]["seed"]
    return scenario


def test_compile_sources_uses_real_loader():
    result = compile_experiment_sources(S.yaml_sources(), profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    assert result.is_valid, [item.code for item in result.diagnostics]
    assert result.plan["selection"]["system"]["uri"] == "xdl://org.xverse.experiment/system/sample-loop"
    assert len(result.run["sourceByteDigests"]) == len(S.FIXTURE_PATHS)
    assert result.run["status"] == "resolved"


def test_cli_experiment_compile_json_emits_plan():
    completed = run_cli("experiment", "compile", "--format", "json", *fixture_arguments())
    assert completed.returncode == 0, completed.stderr
    value = json.loads(completed.stdout)
    assert set(value) == {"reportVersion", "toolVersion", "valid", "plan", "run", "diagnostics"}
    assert value["valid"] is True
    assert value["plan"] is not None
    assert value["run"]["status"] == "resolved"


def test_cli_experiment_compile_text_emits_summary():
    completed = run_cli("experiment", "compile", *fixture_arguments())
    assert completed.returncode == 0, completed.stderr
    digest = json.loads(
        run_cli("experiment", "compile", "--format", "json", *fixture_arguments()).stdout
    )["plan"]["digest"]["value"]
    assert f"resolved plan {digest}" in completed.stdout


def test_cli_experiment_compile_rejection_exits_one(tmp_path):
    output = tmp_path / "plan.json"
    completed = run_cli(
        "experiment", "compile", "--format", "json", "-o", str(output),
        "--profile-schema", str(S.PROFILE_SCHEMA_PATH),
        *(str(p) for p in S.FIXTURE_PATHS if p.name != "scenario.xdl.yaml"),
        str(S.FIXTURE_DIR / "invalid-scenario.xdl.yaml"),
    )
    assert completed.returncode == 1, completed.stderr
    value = json.loads(completed.stdout)
    assert value["plan"] is None
    assert value["diagnostics"]
    assert not output.exists()


def test_cli_invocation_error_exits_two():
    completed = run_cli(
        "experiment", "compile", "--expect-input-digest", "bogus", *fixture_arguments()
    )
    assert completed.returncode == 2
    assert "expect-input-digest" in completed.stderr
    assert completed.stdout == ""


def test_cli_output_path_collision_exits_two():
    target = S.FIXTURE_PATHS[0]
    before = target.read_bytes()
    completed = run_cli("experiment", "compile", "-o", str(target), *fixture_arguments())
    assert completed.returncode == 2
    assert target.read_bytes() == before
