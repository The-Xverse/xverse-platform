"""XDL1-SR-006-U: explicit time-domain reference and mapping unit cases."""

from __future__ import annotations

from xverse_xdl.experiment_plan import PROFILE_NAMESPACE, compile_experiment_sources

from tests.thesis_lite.xdl import support as S


def _codes(result):
    return [item.code for item in result.diagnostics]


def _with_mapping(scenario, *, tolerance=(1, "ms")):
    value, unit = tolerance
    scenario["spec"]["timeMappings"] = [{
        "sourceTimeDomainId": "experiment-time",
        "targetTimeDomainId": "control-time",
        "mapping": "declared identity mapping",
        "tolerance": {"value": value, "unit": unit},
    }]
    return scenario


def _two_domain_scenario():
    scenario = S.scenario_resource()
    scenario["spec"]["steps"][1]["timeDomainId"] = "control-time"
    scenario["spec"]["observers"][0]["timeDomainId"] = "control-time"
    return _with_mapping(scenario)


def test_time_domain_reference_unresolved_rejected():
    scenario = S.scenario_resource()
    scenario["spec"]["faults"][0]["extensions"][PROFILE_NAMESPACE]["timeDomainId"] = "missing-time"
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-TIME-DOMAIN-UNRESOLVED" in _codes(result)


def test_time_mapping_missing_rejected():
    scenario = S.scenario_resource()
    scenario["spec"]["observers"][0]["timeDomainId"] = "control-time"
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-TIME-MAPPING-MISSING" in _codes(result)
    loader_result = compile_experiment_sources(
        S.json_sources(S.declared(scenario=scenario)), profile_schema_paths=S.PROFILE_SCHEMA_REFS
    )
    assert loader_result.plan is None
    assert "XDL-SEMANTIC-TIME-MAPPING" in _codes(loader_result)


def test_time_mapping_tolerance_ticks_recorded():
    result = S.compile_declared(S.declared(scenario=_two_domain_scenario()))
    assert result.is_valid, _codes(result)
    mappings = result.plan["timeMappings"]
    assert len(mappings) == 1
    assert mappings[0]["declaredIndex"] == 0
    assert mappings[0]["sourceTimeDomainId"] == "experiment-time"
    assert mappings[0]["targetTimeDomainId"] == "control-time"
    assert mappings[0]["mapping"] == "declared identity mapping"
    assert mappings[0]["tolerance"] == {"value": 1, "unit": "ms", "ticks": 1000000}


def test_time_domain_used_by_entries_recorded():
    result = S.compile_declared(S.declared(scenario=_two_domain_scenario()))
    assert result.is_valid, _codes(result)
    used = {entry["id"]: entry["usedBy"] for entry in result.plan["timeDomains"]}
    assert used["experiment-time"] == ["step:prepare-source", "flow:sample-flow", "fault:stale-sample"]
    assert used["control-time"] == ["step:start-source", "observer:sample-observer"]
