"""XDL1-SR-001-U: declared Scenario selection and binding unit cases."""

from __future__ import annotations

from xverse_xdl.validate import validate_files

from tests.thesis_lite.xdl import support as S


def _codes(result):
    return [item.code for item in result.diagnostics]


def test_system_missing_rejected():
    resources = S.declared()
    resources.pop(0)
    result = S.compile_declared(resources)
    assert result.plan is None
    assert "XDL1-PLAN-SYSTEM-MISSING" in _codes(result)


def test_system_ambiguous_rejected():
    second = S.system_resource()
    second["metadata"]["name"] = "sample-loop-2"
    resources = S.declared()
    resources.append(second)
    result = S.compile_declared(resources)
    assert result.plan is None
    assert "XDL1-PLAN-SYSTEM-AMBIGUOUS" in _codes(result)


def test_scenario_missing_rejected():
    resources = S.declared()
    resources.pop(4)
    result = S.compile_declared(resources)
    assert result.plan is None
    assert "XDL1-PLAN-SCENARIO-MISSING" in _codes(result)


def test_scenario_ambiguous_rejected():
    second = S.scenario_resource()
    second["metadata"]["name"] = "sample-observation-run-2"
    resources = S.declared()
    resources.append(second)
    result = S.compile_declared(resources)
    assert result.plan is None
    assert "XDL1-PLAN-SCENARIO-AMBIGUOUS" in _codes(result)


def test_deployment_ambiguous_rejected():
    second = S.deployment_resource()
    second["metadata"]["name"] = "local-simulated-loop-2"
    resources = S.declared()
    resources.append(second)
    result = S.compile_declared(resources)
    assert result.plan is None
    assert "XDL1-PLAN-DEPLOYMENT-AMBIGUOUS" in _codes(result)


def test_deployment_unbound_rejected():
    scenario = S.scenario_resource()
    del scenario["spec"]["deploymentRef"]
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-DEPLOYMENT-UNBOUND" in _codes(result)


def test_deployment_absent_compiles_with_null_deployment():
    scenario = S.scenario_resource()
    del scenario["spec"]["deploymentRef"]
    resources = S.declared(scenario=scenario)
    del resources[3]
    result = S.compile_declared(resources)
    assert result.is_valid
    assert result.plan["selection"]["deployment"] is None
    assert result.plan["bindings"] == []


def test_scenario_identity_parameters_and_seed_emitted():
    result = S.compile_declared(S.declared())
    assert result.is_valid
    selection = result.plan["selection"]
    assert selection["scenario"]["name"] == "sample-observation-run"
    assert selection["scenario"]["kind"] == "Scenario"
    assert selection["system"]["name"] == "sample-loop"
    assert result.plan["seed"] == {"value": 7, "unitSemantics": "experiment-seed"}
    assert [item["id"] for item in result.plan["parameters"]] == ["gain", "enabled"]
    assert result.plan["parameters"][0]["value"] == 1.5
    assert result.plan["parameters"][1]["value"] is True


def test_static_readiness_recorded_as_declaration_only():
    validation = validate_files(S.FIXTURE_PATHS, profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    assert validation.is_valid
    result = S.compile_declared(S.declared(), static_readiness=validation.readiness)
    assert result.is_valid
    readiness = result.plan["selection"]["staticReadiness"]
    expected = dict(validation.readiness)
    assert readiness == expected
    assert set(readiness.values()) <= {"Ready", "NotReady", "NotEvaluated"}
    assert result.plan["nonReadiness"]["executableArtifactAvailability"] is False
