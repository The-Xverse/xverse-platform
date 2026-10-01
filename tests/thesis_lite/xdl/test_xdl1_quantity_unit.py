"""XDL1-SR-005-U / XDL1-SR-019-U: explicit parameters, seed, quantities and bounds."""

from __future__ import annotations

import copy

import pytest

from xverse_xdl.experiment_plan import (
    PROFILE_NAMESPACE, TIME_UNIT_TICKS, ExperimentLimits, compile_experiment_files,
)

from tests.thesis_lite.xdl import support as S


def _codes(result):
    return [item.code for item in result.diagnostics]


def _scenario_with_intent(intent):
    scenario = S.scenario_resource()
    scenario["extensions"][PROFILE_NAMESPACE] = intent
    return scenario


def _scenario_with_step_duration(value, unit):
    scenario = S.scenario_resource()
    scenario["spec"]["steps"][0]["extensions"][PROFILE_NAMESPACE]["duration"] = {
        "value": value, "unit": unit,
    }
    return scenario


def test_seed_missing_rejected():
    intent = S.scenario_intent()
    del intent["seed"]
    result = S.compile_declared(S.declared(scenario=_scenario_with_intent(intent)))
    assert result.plan is None
    assert "XDL1-PLAN-SEED-MISSING" in _codes(result)


def test_seed_above_maximum_rejected():
    intent = S.scenario_intent()
    intent["seed"] = {"value": 9007199254740992, "unitSemantics": "experiment-seed"}
    result = S.compile_declared(S.declared(scenario=_scenario_with_intent(intent)))
    assert result.plan is None
    assert "XDL1-PLAN-SEED-RANGE" in _codes(result)


def test_seed_negative_rejected():
    intent = S.scenario_intent()
    intent["seed"] = {"value": -1, "unitSemantics": "experiment-seed"}
    result = S.compile_declared(S.declared(scenario=_scenario_with_intent(intent)))
    assert result.plan is None
    assert "XDL1-PLAN-SEED-RANGE" in _codes(result)


def test_parameter_duplicate_rejected():
    intent = S.scenario_intent()
    intent["parameters"] = [
        {"id": "gain", "valueType": "number", "value": 1.0, "unitSemantics": "dimensionless"},
        {"id": "gain", "valueType": "number", "value": 2.0, "unitSemantics": "dimensionless"},
    ]
    result = S.compile_declared(S.declared(scenario=_scenario_with_intent(intent)))
    assert result.plan is None
    assert "XDL1-PLAN-PARAMETER-DUPLICATE" in _codes(result)


def test_parameter_value_type_mismatch_rejected():
    intent = S.scenario_intent()
    intent["parameters"] = [
        {"id": "gain", "valueType": "integer", "value": "10", "unitSemantics": "dimensionless"},
    ]
    result = S.compile_declared(S.declared(scenario=_scenario_with_intent(intent)))
    assert result.plan is None
    assert "XDL1-PLAN-PARAMETER-VALUE-TYPE" in _codes(result)


def test_parameter_bound_exceeded_rejected():
    intent = S.scenario_intent()
    intent["parameters"] = [
        {"id": "gain", "valueType": "number", "value": 1e16, "unitSemantics": "dimensionless"},
    ]
    result = S.compile_declared(S.declared(scenario=_scenario_with_intent(intent)))
    assert result.plan is None
    assert "XDL1-PLAN-PARAMETER-BOUND" in _codes(result)


def test_quantity_nonfinite_rejected():
    scenario = _scenario_with_step_duration(float("nan"), "ms")
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-QUANTITY-NONFINITE" in _codes(result)


def test_quantity_negative_rejected():
    result = S.compile_declared(S.declared(scenario=_scenario_with_step_duration(-1, "ms")))
    assert result.plan is None
    assert "XDL1-PLAN-QUANTITY-NEGATIVE" in _codes(result)


def test_quantity_overflow_ticks_rejected():
    result = S.compile_declared(S.declared(scenario=_scenario_with_step_duration(9007199255, "ms")))
    assert result.plan is None
    assert "XDL1-PLAN-QUANTITY-OVERFLOW" in _codes(result)


def test_time_unit_unknown_rejected():
    result = S.compile_declared(S.declared(scenario=_scenario_with_step_duration(1, "min")))
    assert result.plan is None
    assert "XDL1-PLAN-TIME-UNIT-UNKNOWN" in _codes(result)


def test_time_precision_noninteger_tick_rejected():
    scenario = S.scenario_resource()
    scenario["spec"]["steps"][0]["schedule"] = {"at": 0.5, "unit": "ns"}
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-TIME-PRECISION" in _codes(result)


def test_time_unit_scaling_exact_ticks():
    table = [("tick", 1), ("ns", 1), ("us", 1000), ("ms", 1000000), ("s", 1000000000)]
    for unit, expected in table:
        assert TIME_UNIT_TICKS[unit] == expected
        result = S.compile_declared(
            S.declared(scenario=_scenario_with_step_duration(1, unit))
        )
        assert result.is_valid, (unit, _codes(result))
        duration = result.plan["lifecycleIntent"][0]["duration"]
        assert duration["unit"] == unit
        assert duration["ticks"] == expected


def test_experiment_limits_nonpositive_raises_value_error():
    with pytest.raises(ValueError):
        ExperimentLimits(max_steps=0)
    with pytest.raises(ValueError):
        ExperimentLimits(max_ticks=-1)


# --------------------------------------------------------------------------------------
# Count-based ExperimentLimits bound coverage (resolves XDL1-RVW-001 / XDL1-RVW-003)
# --------------------------------------------------------------------------------------


def _parameter(identifier):
    return {
        "id": identifier, "valueType": "number", "value": 1.0,
        "unitSemantics": "dimensionless",
    }


def _scenario_with_extra_step():
    scenario = S.scenario_resource()
    steps = scenario["spec"]["steps"]
    clone = copy.deepcopy(steps[0])
    clone["id"] = "prepare-extra"
    clone["extensions"][PROFILE_NAMESPACE]["target"] = S.resource_ref(
        "Scenario", "sample-observation-run", element="prepare-extra"
    )
    steps.append(clone)
    return scenario


def test_max_parameters_per_payload_scope_exceeded_rejected():
    intent = S.scenario_intent()
    intent["parameters"] = [_parameter("gain"), _parameter("offset"), _parameter("bias")]
    result = S.compile_declared(
        S.declared(scenario=_scenario_with_intent(intent)),
        limits=ExperimentLimits(max_parameters=2),
    )
    assert result.plan is None
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_max_parameters_total_compiled_scope_exceeded_rejected():
    scenario = S.scenario_resource()
    scenario["extensions"][PROFILE_NAMESPACE] = S.scenario_intent()
    scenario["spec"]["steps"][0]["extensions"][PROFILE_NAMESPACE]["parameters"] = [_parameter("step-gain")]
    result = S.compile_declared(
        S.declared(scenario=scenario), limits=ExperimentLimits(max_parameters=2)
    )
    assert result.plan is None
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_max_parameters_declared_core_scope_exceeded_rejected():
    system = S.system_resource()
    system["spec"]["parameters"] = [
        {"id": "loop-count", "valueType": "integer", "unitSemantics": "count", "mutability": "constant"},
        {"id": "sample-window", "valueType": "integer", "unitSemantics": "count", "mutability": "constant"},
        {"id": "sample-margin", "valueType": "integer", "unitSemantics": "count", "mutability": "constant"},
    ]
    result = S.compile_declared(
        S.declared(system=system), limits=ExperimentLimits(max_parameters=2)
    )
    assert result.plan is None
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_max_parameters_all_scopes_at_bound_accepted():
    scenario = S.scenario_resource()
    intent = S.scenario_intent()
    intent["parameters"] = [_parameter("gain")]
    scenario["extensions"][PROFILE_NAMESPACE] = intent
    scenario["spec"]["steps"][0]["extensions"][PROFILE_NAMESPACE]["parameters"] = [_parameter("step-gain")]
    scenario["spec"]["steps"][1]["extensions"][PROFILE_NAMESPACE]["parameters"] = []
    system = S.system_resource()
    system["spec"]["parameters"] = [
        {"id": "loop-count", "valueType": "integer", "unitSemantics": "count", "mutability": "constant"},
        {"id": "sample-window", "valueType": "integer", "unitSemantics": "count", "mutability": "constant"},
    ]
    component = S.component_resource()
    component["spec"]["parameters"] = [
        {"id": "nominal-rate", "valueType": "integer", "unitSemantics": "hertz", "mutability": "configuration"},
        {"id": "sample-margin", "valueType": "integer", "unitSemantics": "count", "mutability": "configuration"},
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


def test_max_steps_exceeded_rejected():
    result = S.compile_declared(S.declared(), limits=ExperimentLimits(max_steps=1))
    assert result.plan is None
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_max_faults_exceeded_rejected():
    scenario = S.scenario_resource()
    clone = copy.deepcopy(scenario["spec"]["faults"][0])
    clone["id"] = "stale-sample-2"
    clone["extensions"][PROFILE_NAMESPACE]["target"]["element"] = "stale-sample-2"
    scenario["spec"]["faults"].append(clone)
    result = S.compile_declared(S.declared(scenario=scenario), limits=ExperimentLimits(max_faults=1))
    assert result.plan is None
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_max_observers_exceeded_rejected():
    scenario = S.scenario_resource()
    clone = copy.deepcopy(scenario["spec"]["observers"][0])
    clone["id"] = "sample-observer-2"
    scenario["spec"]["observers"].append(clone)
    result = S.compile_declared(
        S.declared(scenario=scenario), limits=ExperimentLimits(max_observers=1)
    )
    assert result.plan is None
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_max_metrics_exceeded_rejected():
    scenario = S.scenario_resource()
    clone = copy.deepcopy(scenario["spec"]["metrics"][0])
    clone["id"] = "sample-count-2"
    scenario["spec"]["metrics"].append(clone)
    result = S.compile_declared(S.declared(scenario=scenario), limits=ExperimentLimits(max_metrics=1))
    assert result.plan is None
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_max_dependencies_per_step_exceeded_rejected():
    scenario = _scenario_with_extra_step()
    scenario["spec"]["steps"][1]["extensions"][PROFILE_NAMESPACE]["dependsOn"] = [
        "prepare-source", "prepare-extra",
    ]
    result = S.compile_declared(
        S.declared(scenario=scenario), limits=ExperimentLimits(max_dependencies_per_step=1)
    )
    assert result.plan is None
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_max_flows_exceeded_rejected():
    system = S.system_resource()
    clone = copy.deepcopy(system["spec"]["flows"][0])
    clone["id"] = "sample-flow-2"
    system["spec"]["flows"].append(clone)
    result = S.compile_declared(S.declared(system=system), limits=ExperimentLimits(max_flows=1))
    assert result.plan is None
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_max_bindings_exceeded_rejected():
    deployment = S.deployment_resource()
    clone = copy.deepcopy(deployment["spec"]["bindings"][0])
    clone["id"] = "source-binding-2"
    clone.pop("extensions", None)
    deployment["spec"]["bindings"].append(clone)
    result = S.compile_declared(
        S.declared(deployment=deployment), limits=ExperimentLimits(max_bindings=1)
    )
    assert result.plan is None
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_max_resources_exceeded_rejected():
    result = S.compile_declared(S.declared()[:2], limits=ExperimentLimits(max_resources=1))
    assert result.plan is None
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_max_text_length_exceeded_rejected():
    deployment = S.deployment_resource()
    deployment["metadata"]["provenance"] = S.provenance()
    scenario = S.scenario_resource()
    scenario["metadata"]["provenance"] = S.provenance()
    intent = S.scenario_intent()
    intent["fidelityLimitations"] = ["abcde"]
    scenario["extensions"][PROFILE_NAMESPACE] = intent
    result = S.compile_declared(
        S.declared(deployment=deployment, scenario=scenario),
        limits=ExperimentLimits(max_text_length=4),
    )
    assert result.plan is None
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)


def test_max_bytes_per_file_exceeded_rejected(tmp_path):
    path = tmp_path / "oversized.xdl.yaml"
    path.write_bytes(b"ab")
    before = path.read_bytes()
    result = compile_experiment_files((path,), limits=ExperimentLimits(max_bytes_per_file=1))
    assert result.plan is None
    assert "XDL-PARSE-TOO-LARGE" in _codes(result)
    assert path.read_bytes() == before


def test_max_diagnostics_exceeded_fails_closed():
    scenario = S.scenario_resource()
    steps = scenario["spec"]["steps"]
    for step in steps:
        step["extensions"][PROFILE_NAMESPACE]["dependsOn"] = ["missing-step"]
    clone = copy.deepcopy(steps[0])
    clone["id"] = "prepare-extra"
    clone["extensions"][PROFILE_NAMESPACE]["target"] = S.resource_ref(
        "Scenario", "sample-observation-run", element="prepare-extra"
    )
    clone["extensions"][PROFILE_NAMESPACE]["dependsOn"] = ["missing-step"]
    steps.append(clone)
    result = S.compile_declared(
        S.declared(scenario=scenario),
        limits=ExperimentLimits(max_diagnostics=2, max_steps=8),
    )
    assert result.plan is None
    assert result.is_valid is False
    assert len(result.diagnostics) <= 2


def test_max_limitations_exceeded_rejected():
    baseline = S.compile_declared(S.declared())
    assert baseline.is_valid
    assert len(baseline.plan["limitations"]) == 3
    result = S.compile_declared(S.declared(), limits=ExperimentLimits(max_limitations=2))
    assert result.plan is None
    assert "XDL1-PLAN-BOUND-EXCEEDED" in _codes(result)
