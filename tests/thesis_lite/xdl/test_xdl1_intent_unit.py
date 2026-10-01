"""XDL1-SR-002-U..XDL1-SR-010-U, XDL1-SR-012-U, XDL1-SR-015-U intent unit cases."""

from __future__ import annotations

from xverse_xdl.experiment_plan import PROFILE_NAMESPACE, NON_READINESS_STATEMENT

from tests.thesis_lite.xdl import support as S

XDL_KINDS = {"System", "Component", "Deployment", "Scenario", "Profile"}


def _codes(result):
    return [item.code for item in result.diagnostics]


def _single_instance_system():
    """Return the neutral System with exactly one declared component instance."""

    system = S.system_resource()
    system["spec"]["componentInstances"] = [system["spec"]["componentInstances"][0]]
    return system


def _scenario(**tweaks):
    scenario = S.scenario_resource()
    for key, value in tweaks.items():
        scenario["spec"][key] = value
    return scenario


def _fault_payload(scenario):
    return scenario["spec"]["faults"][0]["extensions"][PROFILE_NAMESPACE]


def test_components_and_flows_map_to_existing_kinds():
    result = S.compile_declared(S.declared())
    assert result.is_valid, _codes(result)
    components = result.plan["components"]
    assert components[0]["scope"] == "system"
    instances = [item for item in components if item["scope"] == "component-instance"]
    assert [item["instanceId"] for item in instances] == ["source-instance", "sink-instance"]
    assert instances[0]["componentRef"]["kind"] == "Component"
    assert instances[0]["componentRef"]["uri"] == "xdl://org.xverse.experiment/component/sample-source"
    assert instances[0]["nodeId"] == "producer-node"
    assert instances[0]["modelRefs"][0]["id"] == "sample-model"
    flows = result.plan["flows"]
    assert flows[0]["id"] == "sample-flow"
    assert flows[0]["sourceEndpointId"] == "source-out"
    assert flows[0]["destinationEndpointIds"] == ["sink-in"]
    assert flows[0]["interfaceId"] == "sample-stream"
    assert flows[0]["deliveryIntent"] == "ordered"


def test_system_core_parameters_projected_to_system_scope():
    result = S.compile_declared(S.declared(system=_single_instance_system()))
    assert result.is_valid, _codes(result)
    components = result.plan["components"]
    assert components[0]["scope"] == "system"
    assert components[0]["instanceId"] is None
    assert components[0]["componentRef"] is None
    assert components[0]["nodeId"] is None
    assert [item["id"] for item in components[0]["declaredParameters"]] == ["loop-count"]
    instances = [item for item in components if item["scope"] == "component-instance"]
    assert [item["id"] for item in instances[0]["declaredParameters"]] == ["nominal-rate"]
    assert all(
        item["id"] != "loop-count"
        for entry in instances
        for item in entry["declaredParameters"]
    )
    assert all(item["id"] != "nominal-rate" for item in components[0]["declaredParameters"])


def test_system_core_parameters_not_dropped_when_component_parameters_present():
    system = _single_instance_system()
    system["spec"]["parameters"] = [
        {"id": "loop-count", "valueType": "integer", "unitSemantics": "count", "mutability": "constant"},
        {"id": "sample-window", "valueType": "integer", "unitSemantics": "count", "mutability": "configuration"},
    ]
    result = S.compile_declared(S.declared(system=system))
    assert result.is_valid, _codes(result)
    ids = [
        item["id"]
        for entry in result.plan["components"]
        for item in entry["declaredParameters"]
    ]
    assert sorted(ids) == ["loop-count", "nominal-rate", "sample-window"]
    assert len(ids) == 3
    assert len(set(ids)) == 3


def test_system_scope_entry_always_present_with_empty_declared_parameters():
    system = _single_instance_system()
    system["spec"].pop("parameters", None)
    result = S.compile_declared(S.declared(system=system))
    assert result.is_valid, _codes(result)
    components = result.plan["components"]
    assert components[0]["scope"] == "system"
    assert components[0]["declaredParameters"] == []
    assert components[0]["modelRefs"] == []
    assert components[1]["scope"] == "component-instance"


def test_no_new_top_level_resource_kind_emitted():
    result = S.compile_declared(S.declared())
    assert result.is_valid, _codes(result)
    plan = result.plan
    assert XDL_KINDS.intersection(plan) == set()
    references = []

    def walk(value):
        if isinstance(value, dict):
            if {"apiVersion", "kind", "namespace", "name"} <= set(value):
                references.append(value["kind"])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(plan)
    assert references, "declared resource references must be present"
    assert set(references) <= XDL_KINDS
    assert plan["bindings"][0]["realizationClass"] == "simulated"


def test_lifecycle_intent_fields_emitted():
    result = S.compile_declared(S.declared())
    assert result.is_valid, _codes(result)
    entry = result.plan["lifecycleIntent"][0]
    assert set(entry) == {
        "stepId", "actionKind", "targetRef", "timeDomainId", "phase", "schedule",
        "dependsOn", "duration", "parameters",
    }
    assert entry["stepId"] == "prepare-source"
    assert entry["phase"] == "prepare"
    assert entry["schedule"] == {
        "declaredAt": 0, "declaredUnit": "ms", "atTicks": 0,
        "tolerance": {"value": 0, "unit": "ms", "ticks": 0},
    }
    assert entry["duration"] == {"value": 1, "unit": "ms", "ticks": 1000000}
    assert entry["dependsOn"] == []


def test_protocol_binding_recorded_as_declaration():
    result = S.compile_declared(S.declared())
    assert result.is_valid, _codes(result)
    binding = result.plan["bindings"][0]
    assert binding["protocolBinding"] == {
        "standardRef": "urn:xverse:experiment:protocol:sample",
        "bindingKind": "sample-binding",
        "compatibility": "exact",
        "limitations": ["Declared reference only; nothing is resolved."],
    }
    assert binding["delivery"] == "in-place"
    assert binding["retry"] == {"policy": "bounded", "maxAttempts": 3}


def test_binding_keeps_logical_identity_distinct_from_realization():
    result = S.compile_declared(S.declared())
    assert result.is_valid, _codes(result)
    binding = result.plan["bindings"][0]
    assert binding["logicalRef"]["kind"] == "System"
    assert binding["logicalRef"]["element"] == "source-instance"
    assert binding["collection"] == "componentInstances"
    assert binding["realizationClass"] == "simulated"
    assert binding["targetId"] == "model-unit-target"
    assert binding["targetClass"] == "model-unit"
    assert binding["artifactRefs"][0]["id"] == "sample-artifact"


def test_fault_schedule_fields_emitted():
    result = S.compile_declared(S.declared())
    assert result.is_valid, _codes(result)
    entry = result.plan["faultSchedule"][0]
    assert entry["entryId"] == "fault:stale-sample"
    assert entry["entryKind"] == "fault"
    assert entry["faultId"] == "stale-sample"
    assert entry["faultKind"] == "delay"
    assert entry["collection"] == "componentInstances"
    assert entry["timeDomainId"] == "experiment-time"
    assert entry["trigger"] == {"kind": "time", "declaredAt": 5, "declaredUnit": "ms", "atTicks": 5000000}
    assert entry["duration"] == {"value": 2, "unit": "ms", "ticks": 2000000}
    assert entry["parameters"] == []


def test_fault_trigger_missing_rejected():
    scenario = S.scenario_resource()
    del _fault_payload(scenario)["trigger"]
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-FAULT-TRIGGER-MISSING" in _codes(result)


def test_fault_duration_invalid_rejected():
    scenario = S.scenario_resource()
    del _fault_payload(scenario)["duration"]
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-FAULT-DURATION-INVALID" in _codes(result)


def test_observer_references_emitted():
    result = S.compile_declared(S.declared())
    assert result.is_valid, _codes(result)
    entry = result.plan["observers"][0]
    assert set(entry) == {
        "observerId", "targetRef", "collection", "timeDomainId", "samplingIntent",
        "payloadPolicy", "evidenceSinkRef",
    }
    assert entry["observerId"] == "sample-observer"
    assert entry["collection"] == "flows"
    assert entry["payloadPolicy"] == {
        "payloadSchema": "urn:xverse:experiment:sample-v1", "unitSemantics": "dimensionless",
    }
    assert entry["evidenceSinkRef"] == "urn:xverse:experiment:evidence:sample-observer"


def test_observer_unresolved_rejected():
    scenario = S.scenario_resource()
    scenario["spec"]["observers"][0]["targetRef"]["element"] = "missing-element"
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-OBSERVER-UNRESOLVED" in _codes(result)


def test_metric_link_incomplete_rejected():
    scenario = S.scenario_resource()
    scenario["spec"]["metrics"][0]["observerIds"] = []
    result = S.compile_declared(S.declared(scenario=scenario))
    assert result.plan is None
    assert "XDL1-PLAN-METRIC-LINK-INCOMPLETE" in _codes(result)


def test_metric_status_reference_only():
    result = S.compile_declared(S.declared())
    assert result.is_valid, _codes(result)
    entry = result.plan["metrics"][0]
    assert entry["status"] == "reference-only"
    assert entry["metricId"] == "sample-count"
    assert entry["observerIds"] == ["sample-observer"]
    assert entry["timeDomainIds"] == ["experiment-time"]
    assert "value" not in entry


def test_artifact_pin_missing_rejected():
    deployment = S.deployment_resource()
    del deployment["spec"]["artifacts"][0]["digest"]
    result = S.compile_declared(S.declared(deployment=deployment))
    assert result.plan is None
    assert "XDL1-PLAN-ARTIFACT-PIN-MISSING" in _codes(result)


def test_artifact_reference_unresolved_rejected():
    deployment = S.deployment_resource()
    deployment["spec"]["bindings"][0]["artifactIds"] = ["undeclared-artifact"]
    result = S.compile_declared(S.declared(deployment=deployment))
    assert result.plan is None
    assert "XDL1-PLAN-ARTIFACT-REFERENCE-UNRESOLVED" in _codes(result)


def test_initial_conditions_and_acceptance_intent_recorded_verbatim():
    result = S.compile_declared(S.declared())
    assert result.is_valid, _codes(result)
    assert result.plan["initialConditions"] == {"sample-count": 0}
    assert result.plan["acceptanceIntent"] == "Demonstrate offline declared intent compilation only."
    scenario = S.scenario_resource()
    del scenario["spec"]["acceptanceIntent"]
    without = S.compile_declared(S.declared(scenario=scenario))
    assert without.is_valid, _codes(without)
    assert without.plan["acceptanceIntent"] is None


def test_realization_physical_unsupported_rejected():
    deployment = S.deployment_resource()
    deployment["spec"]["bindings"][0]["realizationClass"] = "physical"
    result = S.compile_declared(S.declared(deployment=deployment))
    assert result.plan is None
    assert "XDL1-PLAN-REALIZATION-UNSUPPORTED" in _codes(result)


def test_delivery_without_pinned_artifact_rejected():
    deployment = S.deployment_resource()
    deployment["spec"]["bindings"][0]["artifactIds"] = []
    deployment["spec"]["bindings"][0]["extensions"][PROFILE_NAMESPACE]["delivery"] = "staged"
    result = S.compile_declared(S.declared(deployment=deployment))
    assert result.plan is None
    assert "XDL1-PLAN-DELIVERY-UNSUPPORTED" in _codes(result)


def test_retry_with_delivery_none_rejected():
    deployment = S.deployment_resource()
    payload = deployment["spec"]["bindings"][0]["extensions"][PROFILE_NAMESPACE]
    payload["delivery"] = "none"
    payload["retry"] = {"policy": "bounded", "maxAttempts": 3}
    result = S.compile_declared(S.declared(deployment=deployment))
    assert result.plan is None
    assert "XDL1-PLAN-RETRY-UNSUPPORTED" in _codes(result)


def test_limitations_merged_and_nonreadiness_present():
    result = S.compile_declared(S.declared())
    assert result.is_valid, _codes(result)
    assert result.plan["limitations"] == [
        "Declared realization intent only; no artifact is retrieved.",
        "Acceptance expressions are declared text only.",
        "Declared intent only; no runtime result is claimed.",
    ]
    assert result.plan["nonReadiness"] == {
        "statement": NON_READINESS_STATEMENT,
        "claim": "declared-intent-validation-only",
        "executableArtifactAvailability": False,
        "runtimeFitness": False,
        "liveReadiness": False,
        "compatibilityOrParity": False,
    }


def test_limitations_additive_do_not_widen_claim():
    base = S.compile_declared(S.declared())
    scenario = S.scenario_resource()
    scenario["extensions"][PROFILE_NAMESPACE]["fidelityLimitations"] = [
        "Declared intent only; no runtime result is claimed.",
        "An additional declared limitation is recorded without widening any claim.",
    ]
    extended = S.compile_declared(S.declared(scenario=scenario))
    assert base.is_valid and extended.is_valid
    assert set(base.plan["limitations"]) < set(extended.plan["limitations"])
    assert extended.plan["nonReadiness"]["executableArtifactAvailability"] is False
    assert extended.plan["nonReadiness"] == base.plan["nonReadiness"]
