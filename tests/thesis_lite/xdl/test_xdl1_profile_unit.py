"""XDL1-SR-017-U / XDL1-SR-016-U: admitted, fail-closed Profile extension unit cases."""

from __future__ import annotations

from xverse_xdl.experiment_plan import PROFILE_NAMESPACE, compile_experiment_sources

from tests.thesis_lite.xdl import support as S


def _codes(result):
    return [item.code for item in result.diagnostics]


def test_profile_absent_rejected():
    resources = S.declared()
    resources.pop(2)  # no admitted Profile resource is supplied
    result = S.compile_declared(resources)
    assert result.plan is None
    assert _codes(result) == ["XDL1-PLAN-PROFILE-ABSENT"]
    assert result.diagnostics[0].gate.name == "POLICY"


def test_profile_duplicate_rejected():
    profile = S.profile_resource()
    duplicate = S.copy_resource(profile)
    duplicate["metadata"]["name"] = "other-experiment"
    resources = S.declared(profile=profile)
    resources.append(duplicate)
    result = S.compile_declared(resources)
    assert result.plan is None
    assert "XDL1-PLAN-PROFILE-DUPLICATE" in _codes(result)


def test_profile_version_unsupported_rejected():
    profile = S.profile_resource()
    profile["metadata"]["version"] = "0.2.0"
    result = S.compile_declared(S.declared(profile=profile))
    assert result.plan is None
    assert "XDL1-PLAN-PROFILE-VERSION-UNSUPPORTED" in _codes(result)


def test_profile_schemaref_unsupported_rejected():
    profile = S.profile_resource()
    profile["spec"]["schemaRef"] = "https://xverse.io/profiles/xcom/v0.1/schema.json"
    result = S.compile_declared(S.declared(profile=profile))
    assert result.plan is None
    assert "XDL1-PLAN-PROFILE-SCHEMAREF-UNSUPPORTED" in _codes(result)


def test_profile_unknown_namespace_rejected():
    scenario = S.scenario_resource()
    scenario["extensions"]["io.xverse.unknown"] = {"schemaVersion": "0.1"}
    result = compile_experiment_sources(
        S.json_sources(S.declared(scenario=scenario)),
        profile_schema_paths=S.PROFILE_SCHEMA_REFS,
    )
    assert result.plan is None
    assert "XDL-SEMANTIC-PROFILE-MISSING" in _codes(result)
    assert not any(code.startswith("XDL1-PLAN-") for code in _codes(result))


def test_profile_payload_kind_mismatch_rejected():
    scenario = S.scenario_resource()
    scenario["spec"]["steps"][0]["extensions"][PROFILE_NAMESPACE] = S.scenario_intent()
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-PROFILE-PAYLOAD-KIND" in _codes(result)


def test_profile_payload_duplicate_rejected():
    from xverse_xdl.experiment_plan import compile_experiment_plan

    payload = S.scenario_intent()
    pointer = f"/extensions/{PROFILE_NAMESPACE}"
    resource = S.normalize(
        S.scenario_resource(), extra_payloads=((PROFILE_NAMESPACE, pointer, payload),)
    )
    resources = (
        S.normalize(S.system_resource()), S.normalize(S.component_resource()),
        S.normalize(S.profile_resource()), S.normalize(S.deployment_resource()), resource,
    )
    result = compile_experiment_plan(resources)
    assert result.plan is None
    assert "XDL1-PLAN-PROFILE-PAYLOAD-DUPLICATE" in _codes(result)


def test_profile_payload_target_mismatch_rejected():
    scenario = S.scenario_resource()
    scenario["extensions"][PROFILE_NAMESPACE]["target"] = S.resource_ref("Scenario", "other-run")
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-PROFILE-TARGET-MISMATCH" in _codes(result)


def test_profile_scenario_intent_absent_rejected():
    scenario = S.scenario_resource()
    del scenario["extensions"]
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-PROFILE-PAYLOAD-ABSENT" in _codes(result)


def test_profile_unknown_field_rejected():
    scenario = S.scenario_resource()
    scenario["extensions"][PROFILE_NAMESPACE]["undeclaredField"] = "value"
    result = compile_experiment_sources(
        S.json_sources(S.declared(scenario=scenario)),
        profile_schema_paths=S.PROFILE_SCHEMA_REFS,
    )
    assert result.plan is None
    assert "XDL-SEMANTIC-EXTENSION-SCHEMA" in _codes(result)
