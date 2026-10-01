"""XDL1-SR-014-U / XDL1-SR-018-U: stable structured diagnostics and fail-closed rejection."""

from __future__ import annotations

from xverse_xdl.experiment_plan import PROFILE_NAMESPACE
from xverse_xdl.models import Severity

from tests.thesis_lite.xdl import support as S


def _codes(result):
    return [item.code for item in result.diagnostics]


def _defective_scenario():
    scenario = S.scenario_resource()
    del scenario["extensions"][PROFILE_NAMESPACE]["seed"]
    scenario["spec"]["steps"][0]["extensions"][PROFILE_NAMESPACE]["duration"] = {
        "value": 1, "unit": "min",
    }
    del scenario["spec"]["faults"][0]["extensions"][PROFILE_NAMESPACE]["duration"]
    scenario["spec"]["metrics"][0]["observerIds"] = []
    return scenario


def test_diagnostics_sorted_deterministically():
    resources = S.declared(scenario=_defective_scenario())
    forward = S.compile_declared(resources)
    reverse = S.compile_declared(list(reversed(resources)))
    assert forward.plan is None and reverse.plan is None
    assert len(forward.diagnostics) >= 3
    assert [item.code for item in forward.diagnostics] == [item.code for item in reverse.diagnostics]
    keys = [item.sort_key for item in forward.diagnostics]
    assert keys == sorted(keys)


def test_error_diagnostic_has_stable_code_pointer_and_correction():
    result = S.compile_declared(S.declared(scenario=_defective_scenario()))
    assert result.diagnostics
    for item in result.diagnostics:
        assert item.code.startswith(("XDL1-PLAN-", "XDL-"))
        assert isinstance(item.gate.name, str) and item.gate.name
        assert item.severity is Severity.ERROR
        assert item.pointer == "" or item.pointer.startswith("/")
        assert item.correction


def test_rejection_returns_no_plan():
    for variant in (
        _defective_scenario(),
        _scenario_without_seed(),
        _scenario_with_unknown_unit(),
    ):
        result = S.compile_declared(S.declared(scenario=variant))
        assert result.plan is None
        assert not result.is_valid


def _scenario_without_seed():
    scenario = S.scenario_resource()
    del scenario["extensions"][PROFILE_NAMESPACE]["seed"]
    return scenario


def _scenario_with_unknown_unit():
    scenario = S.scenario_resource()
    scenario["spec"]["steps"][0]["extensions"][PROFILE_NAMESPACE]["duration"] = {
        "value": 1, "unit": "min",
    }
    return scenario


def test_result_is_valid_false_without_plan():
    result = S.compile_declared(S.declared(scenario=_scenario_without_seed()))
    assert result.plan is None
    assert result.is_valid is False


def test_rejected_run_envelope_has_null_plan_digest():
    result = S.compile_declared(
        S.declared(scenario=_scenario_without_seed()), run_id="rejected-run"
    )
    assert result.plan is None
    assert result.run["status"] == "rejected"
    assert result.run["planDigest"] is None
    assert result.run["runId"] == "rejected-run"


def test_secret_bearing_leaf_rejected_without_echo():
    offending = "token = abc123"
    intent = S.scenario_intent()
    intent["parameters"] = [
        {"id": "credential-note", "valueType": "string", "value": offending,
         "unitSemantics": "dimensionless"},
    ]
    scenario = S.scenario_resource()
    scenario["extensions"][PROFILE_NAMESPACE] = intent
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-SECRET-IN-PUBLIC-ARTIFACT" in _codes(result)
    for item in result.diagnostics:
        assert offending not in item.message
        assert offending not in item.correction
