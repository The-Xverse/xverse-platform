"""XDL1-VALIDATION: intended-use validation cases for Phase 1 XDL Lite.

The cases correspond one-to-one with the six XDL1-VS scenarios and exercise declared
intent compilation end to end: one canonical resolved plan, stable structured diagnostics,
version/hash verification without reparsing YAML, preserved accepted consumers and CLI
behaviour, declaration-only honesty, and explicit time/quantity validation. No case starts a
process, opens a socket, retrieves an artifact or claims readiness.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys

from xverse_xdl import xcom_plan
from xverse_xdl.catalog import build_lifecycle_plan, derive_catalog
from xverse_xdl.experiment_plan import (
    PROFILE_NAMESPACE, PROFILE_SCHEMA_ID, PROFILE_SCHEMA_VERSION, ExperimentLimits,
    canonical_plan_bytes, compile_experiment_files, compile_experiment_sources, plan_matches_digest,
)
from xverse_xdl.loader import SourceInput, load_sources
from xverse_xdl.normalize import canonical_json
from xverse_xdl.validate import validate_files
from tests.helpers import EXAMPLE_PATHS, PROFILE_SCHEMA

from tests.thesis_lite.xdl import support as S

RUNTIME_SCHEMA = S.ROOT / "xdl" / "profiles" / "runtime-compatibility-v0.1.schema.json"
RUNTIME_SCHEMA_V2 = S.ROOT / "xdl" / "profiles" / "runtime-compatibility-v0.2.schema.json"
SD0001_PATHS = tuple(sorted((S.ROOT / "xdl" / "candidates" / "sd0001").glob("*.xdl.yaml")))


def _codes(result):
    return [item.code for item in result.diagnostics]


def run_cli(*arguments: str):
    return subprocess.run(
        [sys.executable, "-m", "xverse_xdl", *arguments],
        cwd=S.ROOT, text=True, capture_output=True, check=False,
    )


def _step_duration_scenario(value, unit):
    scenario = S.scenario_resource()
    scenario["spec"]["steps"][0]["extensions"][PROFILE_NAMESPACE]["duration"] = {
        "value": value, "unit": unit,
    }
    return scenario


def _two_domain_scenario():
    scenario = S.scenario_resource()
    scenario["spec"]["steps"][1]["timeDomainId"] = "control-time"
    scenario["spec"]["observers"][0]["timeDomainId"] = "control-time"
    scenario["spec"]["timeMappings"] = [{
        "sourceTimeDomainId": "experiment-time",
        "targetTimeDomainId": "control-time",
        "mapping": "declared identity mapping",
        "tolerance": {"value": 1, "unit": "ms"},
    }]
    return scenario


def test_author_declared_experiment_yields_one_canonical_resolved_plan():
    result = compile_experiment_files(S.FIXTURE_PATHS, profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    assert result.is_valid, _codes(result)
    assert result.plan["planVersion"] == "1"
    assert result.plan["status"] == "resolved"
    assert result.plan["profile"]["schemaVersion"] == PROFILE_SCHEMA_VERSION
    assert canonical_plan_bytes(result.plan) == canonical_plan_bytes(result.plan)
    assert plan_matches_digest(result.plan) is True


def test_resolved_plan_records_seed_parameters_faults_observers_and_metrics():
    result = compile_experiment_files(S.FIXTURE_PATHS, profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    assert result.is_valid, _codes(result)
    plan = result.plan
    assert plan["seed"] == {"value": 7, "unitSemantics": "experiment-seed"}
    assert [item["id"] for item in plan["parameters"]] == ["gain", "enabled"]
    assert plan["faultSchedule"][0]["faultId"] == "stale-sample"
    assert plan["faultSchedule"][0]["trigger"]["kind"] == "time"
    assert plan["observers"][0]["observerId"] == "sample-observer"
    assert plan["metrics"][0]["status"] == "reference-only"
    assert plan["lifecycleIntent"][0]["stepId"] == "prepare-source"
    assert plan["initialConditions"] == {"sample-count": 0}


def test_integrator_receives_stable_structured_diagnostics_for_declared_defects():
    cases = [
        (_scenario_without_seed(), "XDL1-PLAN-SEED-MISSING"),
        (_step_duration_scenario(1, "min"), "XDL1-PLAN-TIME-UNIT-UNKNOWN"),
        (_step_duration_scenario(-1, "ms"), "XDL1-PLAN-QUANTITY-NEGATIVE"),
    ]
    for scenario, expected in cases:
        result = S.compile_declared(S.declared(scenario=scenario))
        assert result.plan is None, expected
        assert expected in _codes(result), (expected, _codes(result))
        keys = [item.sort_key for item in result.diagnostics]
        assert keys == sorted(keys)
        for item in result.diagnostics:
            assert item.correction


def _scenario_without_seed():
    scenario = S.scenario_resource()
    del scenario["extensions"][PROFILE_NAMESPACE]["seed"]
    return scenario


def test_rejected_compile_has_no_side_effect_and_no_partial_plan():
    paths = tuple(path for path in S.FIXTURE_PATHS if path.name != "scenario.xdl.yaml") + (
        S.FIXTURE_DIR / "invalid-scenario.xdl.yaml",
    )
    digests = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    result = compile_experiment_files(paths, profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    assert result.plan is None
    assert result.is_valid is False
    assert result.run["status"] == "rejected"
    assert result.run["planDigest"] is None
    assert result.diagnostics
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths} == digests


def test_downstream_consumer_verifies_versions_and_hashes_without_reparsing_yaml():
    result = compile_experiment_files(S.FIXTURE_PATHS, profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    assert result.is_valid
    document = result.plan
    reloaded = json.loads(json.dumps(document, sort_keys=True))
    assert reloaded["planVersion"] == "1"
    assert reloaded["profile"]["namespace"] == PROFILE_NAMESPACE
    assert reloaded["profile"]["schemaVersion"] == PROFILE_SCHEMA_VERSION
    assert reloaded["profile"]["schemaRef"] == PROFILE_SCHEMA_ID
    assert reloaded["profile"]["resource"]["version"] == "0.1.0"
    assert plan_matches_digest(reloaded) is True
    for entry in reloaded["provenance"]["resources"]:
        assert len(entry["semanticDigest"]["value"]) == 64
    assert len(reloaded["provenance"]["inputSemanticDigest"]["value"]) == 64


def test_equivalent_encodings_and_permutations_share_one_semantic_identity():
    documents, diagnostics = load_sources(S.yaml_sources())
    assert not diagnostics
    json_sources = tuple(
        SourceInput(path.name.replace(".xdl.yaml", ".xdl.json"), json.dumps(document.data).encode("utf-8"))
        for path, document in zip(S.FIXTURE_PATHS, documents)
    )
    yaml_result = compile_experiment_sources(S.yaml_sources(), profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    json_result = compile_experiment_sources(json_sources, profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    reversed_result = compile_experiment_sources(
        tuple(reversed(S.yaml_sources())), profile_schema_paths=S.PROFILE_SCHEMA_REFS
    )
    assert yaml_result.is_valid and json_result.is_valid and reversed_result.is_valid
    assert yaml_result.plan["digest"] == json_result.plan["digest"] == reversed_result.plan["digest"]
    assert (
        yaml_result.plan["provenance"]["inputSemanticDigest"]
        == json_result.plan["provenance"]["inputSemanticDigest"]
    )


def test_existing_loader_normalizer_catalog_and_xcom_consumers_remain_compatible():
    validation = validate_files(EXAMPLE_PATHS, profile_schema_paths=(PROFILE_SCHEMA,))
    assert validation.is_valid, _codes(validation)
    assert canonical_json(validation.resources) == canonical_json(validation.resources)
    sd0001 = validate_files(SD0001_PATHS, profile_schema_paths=(RUNTIME_SCHEMA, RUNTIME_SCHEMA_V2))
    assert sd0001.is_valid, _codes(sd0001)
    catalog = derive_catalog(sd0001.resources)
    assert catalog.is_valid and catalog.entries
    plan = build_lifecycle_plan(catalog.entries[0])
    assert plan.requires_execution_permit is True and plan.actions
    xcom_plan_value = xcom_plan.compile_plan(_xcom_graph())
    assert xcom_plan.plan_matches_digest(xcom_plan_value) is True


def test_existing_cli_commands_remain_byte_compatible():
    version = run_cli("version", "--format", "json")
    assert version.returncode == 0
    assert json.loads(version.stdout) == {
        "toolVersion": json.loads(version.stdout)["toolVersion"],
        "supportedApiVersions": ["xverse.io/xdl/v1alpha1"],
    }
    forward = run_cli(
        "normalize", "--profile-schema", str(PROFILE_SCHEMA), *(str(path) for path in EXAMPLE_PATHS)
    )
    repeat = run_cli(
        "normalize", "--profile-schema", str(PROFILE_SCHEMA), *(str(path) for path in EXAMPLE_PATHS)
    )
    validate = run_cli(
        "validate", "--format", "json", "--profile-schema", str(PROFILE_SCHEMA),
        *(str(path) for path in EXAMPLE_PATHS),
    )
    assert forward.returncode == repeat.returncode == validate.returncode == 0
    assert forward.stdout == repeat.stdout
    assert json.loads(validate.stdout)["valid"] is True


def test_plan_limitations_and_non_readiness_forbid_availability_claims():
    result = compile_experiment_files(S.FIXTURE_PATHS, profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    assert result.is_valid
    plan = result.plan
    assert plan["limitations"]
    non_readiness = plan["nonReadiness"]
    assert non_readiness["claim"] == "declared-intent-validation-only"
    assert non_readiness["executableArtifactAvailability"] is False
    assert non_readiness["runtimeFitness"] is False
    assert non_readiness["liveReadiness"] is False
    assert non_readiness["compatibilityOrParity"] is False
    assert "not evidence" in non_readiness["statement"]
    assert plan["status"] == "resolved"


def test_unsupported_physical_realization_rejected_without_default():
    deployment = S.deployment_resource()
    deployment["spec"]["bindings"][0]["realizationClass"] = "physical"
    deployment["spec"]["targets"][0]["targetClass"] = "physical"
    result = S.compile_declared(S.declared(deployment=deployment))
    assert result.plan is None
    assert "XDL1-PLAN-REALIZATION-UNSUPPORTED" in _codes(result)
    assert "XDL1-PLAN-DELIVERY-UNSUPPORTED" not in _codes(result)


def test_declared_time_domain_and_mapping_recorded_without_inference():
    result = S.compile_declared(S.declared(scenario=_two_domain_scenario()))
    assert result.is_valid, _codes(result)
    plan = result.plan
    assert plan["timeMappings"][0]["tolerance"] == {"value": 1, "unit": "ms", "ticks": 1000000}
    used = {entry["id"]: entry["usedBy"] for entry in plan["timeDomains"]}
    assert used["experiment-time"] == ["step:prepare-source", "flow:sample-flow", "fault:stale-sample"]
    assert used["control-time"] == ["step:start-source", "observer:sample-observer"]
    assert all(entry["canonicalUnit"] == "tick" for entry in plan["timeDomains"])


def test_nonfinite_negative_overflow_and_unknown_units_rejected():
    cases = [
        (_step_duration_scenario(float("nan"), "ms"), "XDL1-PLAN-QUANTITY-NONFINITE"),
        (_step_duration_scenario(-1, "ms"), "XDL1-PLAN-QUANTITY-NEGATIVE"),
        (_step_duration_scenario(9007199255, "ms"), "XDL1-PLAN-QUANTITY-OVERFLOW"),
        (_step_duration_scenario(1, "min"), "XDL1-PLAN-TIME-UNIT-UNKNOWN"),
    ]
    for scenario, expected in cases:
        result = S.compile_declared(S.declared(scenario=scenario))
        assert result.plan is None, expected
        assert expected in _codes(result), (expected, _codes(result))


# --------------------------------------------------------------------------------------
# XDL1-VS-07 -- declared finite bound scopes and System core-parameter projection
# (resolves XDL1-RVW-001 / XDL1-RVW-002 / XDL1-RVW-003)
# --------------------------------------------------------------------------------------


def _core_parameter(identifier, semantics="count"):
    return {
        "id": identifier, "valueType": "integer", "unitSemantics": semantics,
        "mutability": "constant",
    }


def _intent_parameter(identifier):
    return {
        "id": identifier, "valueType": "number", "value": 1.0,
        "unitSemantics": "dimensionless",
    }


def test_per_payload_parameter_bound_exceeded_rejected_without_plan():
    scenario = S.scenario_resource()
    intent = S.scenario_intent()
    intent["parameters"] = [_intent_parameter("gain"), _intent_parameter("offset"), _intent_parameter("bias")]
    scenario["extensions"][PROFILE_NAMESPACE] = intent
    result = S.compile_declared(S.declared(scenario=scenario), limits=ExperimentLimits(max_parameters=2))
    assert result.plan is None
    assert result.is_valid is False
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_total_compiled_parameter_bound_exceeded_rejected_without_plan():
    scenario = S.scenario_resource()
    scenario["spec"]["steps"][0]["extensions"][PROFILE_NAMESPACE]["parameters"] = [
        _intent_parameter("step-gain"),
    ]
    scenario["spec"]["steps"][1]["extensions"][PROFILE_NAMESPACE]["parameters"] = [
        _intent_parameter("step-offset"),
    ]
    # Each individual per-payload list is within the bound (2, 1 and 1); only the total
    # compiled-parameter count (4) exceeds max_parameters == 2.
    result = S.compile_declared(S.declared(scenario=scenario), limits=ExperimentLimits(max_parameters=2))
    assert len(S.scenario_intent()["parameters"]) == 2
    assert result.plan is None
    assert result.is_valid is False
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)
    assert result.run["planDigest"] is None


def test_declared_core_parameter_bound_exceeded_rejected_without_plan():
    system = S.system_resource()
    system["spec"]["parameters"] = [
        _core_parameter("loop-count"), _core_parameter("sample-window"), _core_parameter("sample-margin"),
    ]
    result = S.compile_declared(S.declared(system=system), limits=ExperimentLimits(max_parameters=2))
    assert result.plan is None
    assert result.is_valid is False
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_declared_limitation_bound_exceeded_rejected_without_plan():
    baseline = compile_experiment_files(S.FIXTURE_PATHS, profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    assert baseline.is_valid
    assert len(baseline.plan["limitations"]) == 3
    result = S.compile_declared(S.declared(), limits=ExperimentLimits(max_limitations=2))
    assert result.plan is None
    assert result.is_valid is False
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_parameter_counts_at_declared_bounds_compile_resolved_plan():
    scenario = S.scenario_resource()
    intent = S.scenario_intent()
    intent["parameters"] = [_intent_parameter("gain")]
    scenario["extensions"][PROFILE_NAMESPACE] = intent
    scenario["spec"]["steps"][0]["extensions"][PROFILE_NAMESPACE]["parameters"] = [_intent_parameter("step-gain")]
    scenario["spec"]["steps"][1]["extensions"][PROFILE_NAMESPACE]["parameters"] = []
    system = S.system_resource()
    system["spec"]["parameters"] = [_core_parameter("loop-count"), _core_parameter("sample-window")]
    component = S.component_resource()
    component["spec"]["parameters"] = [
        {"id": "nominal-rate", "valueType": "integer", "unitSemantics": "hertz", "mutability": "configuration"},
        _core_parameter("sample-margin", semantics="count"),
    ]
    result = S.compile_declared(
        S.declared(system=system, component=component, scenario=scenario),
        limits=ExperimentLimits(max_parameters=2),
    )
    assert result.is_valid, _codes(result)
    plan = result.plan
    compiled = (
        len(plan["parameters"])
        + sum(len(entry["parameters"]) for entry in plan["lifecycleIntent"])
        + sum(len(entry["parameters"]) for entry in plan["faultSchedule"])
    )
    assert compiled == 2
    assert plan_matches_digest(plan) is True


def test_system_core_parameters_projected_without_drop_or_duplication():
    system = S.system_resource()
    system["spec"]["componentInstances"] = [system["spec"]["componentInstances"][0]]
    system["spec"]["parameters"] = [_core_parameter("loop-count"), _core_parameter("sample-window")]
    result = S.compile_declared(S.declared(system=system))
    assert result.is_valid, _codes(result)
    components = result.plan["components"]
    assert components[0]["scope"] == "system"
    assert components[0]["instanceId"] is None and components[0]["componentRef"] is None
    projected = sorted(item["id"] for item in components[0]["declaredParameters"])
    assert projected == ["loop-count", "sample-window"]
    instance_ids = [
        item["id"] for entry in components[1:] for item in entry["declaredParameters"]
    ]
    assert "loop-count" not in instance_ids and "sample-window" not in instance_ids
    assert instance_ids.count("nominal-rate") == 1


def _xcom_graph() -> dict:
    api = xcom_plan.API_VERSION
    namespace = "org.xverse.examples"

    def identity(kind: str, name: str) -> dict:
        return {
            "apiVersion": api, "kind": kind, "namespace": namespace, "name": name,
            "uri": f"xdl://{namespace}/{kind.lower()}/{name}",
        }

    return {"resources": [
        {
            "identity": identity("Component", "signal-source"),
            "revision": "0.1.0",
            "content": {
                "capabilities": ["produce-samples"],
                "interfaces": [{"id": "sample-stream", "direction": "output", "payloadSchema": "urn:x:1"}],
                "endpoints": [{
                    "id": "samples-out", "ownerId": "signal-source",
                    "interfaceId": "sample-stream", "direction": "output",
                }],
            },
        },
        {
            "identity": identity("System", "sample-loop"),
            "revision": "0.1.0",
            "content": {
                "nodes": [{"id": "producer-node", "roles": ["compute"]}],
                "componentInstances": [{
                    "id": "source-instance",
                    "componentRef": {
                        "apiVersion": api, "kind": "Component",
                        "namespace": namespace, "name": "signal-source",
                    },
                    "nodeId": "producer-node",
                }],
                "interfaces": [{"id": "sample-stream", "direction": "output", "payloadSchema": "urn:x:1"}],
                "endpoints": [{
                    "id": "samples-out", "ownerId": "source-instance",
                    "interfaceId": "sample-stream", "direction": "output",
                }],
                "flows": [],
            },
        },
    ]}
