"""XDL1-SR-003-U / XDL1-SR-007-U / XDL1-SR-013-U / XDL1-SR-018-U: deterministic order."""

from __future__ import annotations

from xverse_xdl.experiment_plan import PROFILE_NAMESPACE, compile_experiment_plan

from tests.thesis_lite.xdl import support as S

PHASES = ["prepare", "start", "observe", "stop", "cleanup"]


def _codes(result):
    return [item.code for item in result.diagnostics]


def _step(step_id, *, phase="start", at=0, unit="ms", domain="experiment-time", depends_on=()):
    return {
        "id": step_id,
        "actionKind": "apply",
        "targetRef": S.resource_ref("System", "sample-loop", element="source-instance"),
        "timeDomainId": domain,
        "schedule": {"at": at, "unit": unit},
        "action": {"operation": "apply"},
        "extensions": {
            PROFILE_NAMESPACE: {
                "schemaVersion": "0.1", "kind": "step-intent",
                "target": S.resource_ref("Scenario", "sample-observation-run", element=step_id),
                "phase": phase, "dependsOn": list(depends_on), "parameters": [],
            },
        },
    }


def _fault(fault_id, *, trigger, duration=(1, "ms"), domain=None):
    payload = {
        "schemaVersion": "0.1", "kind": "fault-intent",
        "target": S.resource_ref("Scenario", "sample-observation-run", element=fault_id),
        "trigger": trigger,
        "duration": {"value": duration[0], "unit": duration[1]},
    }
    if domain is not None:
        payload["timeDomainId"] = domain
    return {
        "id": fault_id,
        "targetRef": S.resource_ref("System", "sample-loop", element="source-instance"),
        "faultKind": "delay", "activation": "scheduled", "recovery": "automatic",
        "maturity": "prototype",
        "extensions": {PROFILE_NAMESPACE: payload},
    }


def _observer(observer_id, *, domain="experiment-time"):
    return {
        "id": observer_id,
        "targetRef": S.resource_ref("System", "sample-loop", element="sample-flow"),
        "timeDomainId": domain,
        "samplingIntent": "observe every declared sample",
        "payloadSchema": "urn:xverse:experiment:sample-v1",
        "unitSemantics": "dimensionless",
        "evidenceSinkRef": f"urn:xverse:experiment:evidence:{observer_id}",
    }


def _metric(metric_id, observer_id):
    return {
        "id": metric_id, "observerIds": [observer_id],
        "calculationRef": f"urn:xverse:experiment:metric:{metric_id}",
        "unitSemantics": "count", "acceptance": "declared acceptance text only",
    }


def test_lifecycle_order_key_phase_rank():
    scenario = S.scenario_resource()
    scenario["spec"]["steps"] = [
        _step("step-cleanup", phase="cleanup"),
        _step("step-start", phase="start"),
        _step("step-prepare", phase="prepare"),
        _step("step-stop", phase="stop"),
        _step("step-observe", phase="observe"),
    ]
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.is_valid, _codes(result)
    phases = [entry["phase"] for entry in result.plan["lifecycleIntent"]]
    assert phases == PHASES


def test_schedule_declared_order_ambiguity_rejected():
    scenario = S.scenario_resource()
    scenario["spec"]["faults"] = [
        _fault("alpha-fault", trigger={"kind": "declared-order", "order": 3}),
        _fault("beta-fault", trigger={"kind": "declared-order", "order": 3}),
    ]
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-SCHEDULE-AMBIGUOUS" in _codes(result)


def test_schedule_equal_ticks_tie_break_by_fault_id():
    scenario = S.scenario_resource()
    scenario["spec"]["faults"] = [
        _fault("beta-fault", trigger={"kind": "time", "at": 5, "unit": "ms"}, domain="experiment-time"),
        _fault("alpha-fault", trigger={"kind": "time", "at": 5, "unit": "ms"}, domain="experiment-time"),
    ]
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.is_valid, _codes(result)
    assert [entry["faultId"] for entry in result.plan["faultSchedule"]] == ["alpha-fault", "beta-fault"]


def test_dependency_order_stable_tie_break():
    resources = S.declared()
    forward = S.compile_declared(resources)
    reverse = S.compile_declared(list(reversed(resources)))
    assert forward.is_valid and reverse.is_valid, _codes(forward) + _codes(reverse)
    assert forward.plan["dependencyOrder"] == reverse.plan["dependencyOrder"]
    kinds = [(entry["kind"], entry["id"]) for entry in forward.plan["dependencyOrder"]]
    assert kinds == [
        ("node", "producer-node"), ("node", "sink-node"),
        ("component-instance", "source-instance"), ("component-instance", "sink-instance"),
        ("step", "prepare-source"), ("step", "start-source"),
    ]


def test_dependency_cycle_rejected():
    system = S.system_resource()
    system["spec"]["endpoints"].append({
        "id": "sink-out", "ownerId": "sink-instance", "interfaceId": "sample-stream", "direction": "output",
    })
    system["spec"]["endpoints"].append({
        "id": "source-in", "ownerId": "source-instance", "interfaceId": "sample-stream", "direction": "input",
    })
    system["spec"]["flows"] = [
        system["spec"]["flows"][0],
        {
            "id": "return-flow", "sourceEndpointId": "sink-out",
            "destinationEndpointIds": ["source-in"], "interfaceId": "sample-stream",
            "deliveryIntent": "ordered",
        },
    ]
    result = S.compile_declared(S.declared(system=system))
    assert result.plan is None
    diagnostic = S.find(result, "XDL1-PLAN-DEPENDENCY-CYCLE")
    assert diagnostic is not None
    assert set(diagnostic.related) == {"source-instance", "sink-instance"}


def test_dependency_missing_rejected():
    scenario = S.scenario_resource()
    scenario["spec"]["steps"][1]["extensions"][PROFILE_NAMESPACE]["dependsOn"] = ["undeclared-step"]
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-DEPENDENCY-MISSING" in _codes(result)


def test_step_depends_on_self_rejected():
    scenario = S.scenario_resource()
    scenario["spec"]["steps"][0]["extensions"][PROFILE_NAMESPACE]["dependsOn"] = ["prepare-source"]
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-DEPENDENCY-CYCLE" in _codes(result)


def test_observer_and_metric_order_stable():
    scenario = S.scenario_resource()
    scenario["spec"]["observers"] = [_observer("observer-b"), _observer("observer-a")]
    scenario["spec"]["metrics"] = [_metric("metric-b", "observer-b"), _metric("metric-a", "observer-a")]
    resources = S.declared(scenario=scenario)
    forward = S.compile_declared(resources)
    reverse = S.compile_declared(list(reversed(resources)))
    assert forward.is_valid and reverse.is_valid, _codes(forward) + _codes(reverse)
    assert [entry["observerId"] for entry in forward.plan["observers"]] == ["observer-a", "observer-b"]
    assert [entry["metricId"] for entry in forward.plan["metrics"]] == ["metric-a", "metric-b"]
    assert forward.plan["observers"] == reverse.plan["observers"]
    assert forward.plan["metrics"] == reverse.plan["metrics"]
    assert forward.plan["metrics"][0]["observerIds"] == ["observer-a"]
    assert forward.plan["metrics"][0]["timeDomainIds"] == ["experiment-time"]
