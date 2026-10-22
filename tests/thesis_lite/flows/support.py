"""Owned Phase 6 fixtures (FR-013): camera and radar flows over the Maestro fixture graph.

``documents(kind)`` builds the XDL documents of the ``uniform`` set (equal-valued flow-policy
payloads on the camera and radar Components; ``xcom_plan`` activatable) or the ``distinct`` set
(the radar payload differs only in ``queueDepth``; ``XCOM-PLAN-POLICY-CONFLICT``). Every time
domain is monotonic; the camera flow is received in ``control-time`` through a directed Scenario
mapping. The committed copies under ``fixtures/<set>/`` are checked against this builder.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from xverse_xdl.experiment_plan import compile_experiment_plan
from xverse_xdl.validate import validate_sources

from ..faults import support as faults_support

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCHEMAS = tuple(sorted((ROOT / "xdl" / "profiles").glob("*.schema.json")))
NAMESPACE = "org.xverse.experiment"
API = "xverse.io/xdl/v1alpha1"
PLANNED_TICKS = tuple(range(0, 41, 2))
XCOM_PROFILE = "xcom-profile.json"
FLOW_POLICY = {"ordering": "fifo", "reliability": "best-effort", "deadlineMs": 0, "retry": 0, "queueDepth": 4,
               "overflow": "reject", "observationPoints": []}


def _target(kind: str, name: str) -> dict[str, str]:
    """Return an X-COM payload target naming its attachment resource."""

    return {"apiVersion": API, "kind": kind, "namespace": NAMESPACE, "name": name}


def _xcom(kind: str, target: dict[str, str], policy: dict[str, Any]) -> dict[str, Any]:
    """Return one ``io.xverse.xcom`` payload."""

    return {"schemaVersion": "0.1", "kind": kind, "target": target, "policy": policy}


def _sensor_component(base: dict[str, Any], name: str, interface: str, policy: dict[str, Any]) -> dict[str, Any]:
    """Return a sensor Component with an element-level interface-policy and a resource-level flow-policy."""

    doc = copy.deepcopy(base)
    doc["metadata"]["name"] = name
    spec = doc["spec"]
    spec["interfaces"] = [{"compatibility": "exact", "direction": "output", "id": interface, "payloadSchema": f"urn:xverse:experiment:{interface}-v1",
                           "unitSemantics": "dimensionless",
                           "extensions": {"io.xverse.xcom": _xcom("interface-policy", _target("Component", name), {
                               "interactionKind": "message", "schemaId": f"{interface}-schema", "schemaVersion": "1.0.0",
                               "encoding": "json", "semanticCompatibility": "exact"})}}]
    spec["endpoints"] = [{"direction": "output", "id": f"{interface}-out", "interfaceId": interface, "ownerId": name}]
    doc["extensions"] = {"io.xverse.xcom": _xcom("flow-policy", _target("Component", name), policy)}
    return doc


def documents(kind: str = "uniform", *, radar_policy: dict[str, Any] | None = None, camera_policy: dict[str, Any] | None = None,
              intents: dict[str, str] | None = None, quality: dict[str, dict[str, Any]] | None = None,
              mappings: list[dict[str, Any]] | None = None, tokens: tuple[str, ...] = (), omit_camera_policy: bool = False,
              deployment_policy: dict[str, Any] | None = None, scenario_policy: dict[str, Any] | None = None,
              second_provider: bool = False) -> dict[str, dict[str, Any]]:
    """Return the fixture documents keyed by file name.

    @param kind ``uniform`` or ``distinct``.
    @param radar_policy, camera_policy Overrides of the flow-policy payloads (refusal fixtures).
    @param intents Overrides of ``deliveryIntent`` per flow id.
    @param quality Overrides of ``quality`` per flow id.
    @param mappings Override of the Scenario ``timeMappings``.
    @param tokens Extra provider capability tokens (the V02 mask fixture declares reliable/unordered).
    @param omit_camera_policy Drop the camera Component's flow-policy (attribution falls back to the Deployment).
    @param deployment_policy Resource-level Deployment flow-policy (an X-COM payload on the Deployment).
    @param scenario_policy Resource-level Scenario flow-policy (ignored by binding, listed as ``ignoredPayloads``).
    @param second_provider Also attach a network-provider at the target element (two qualifying providers).
    """

    docs = faults_support.documents()
    base_component = docs.pop("component.json")
    camera = dict(FLOW_POLICY, **(camera_policy or {}))
    radar = dict(FLOW_POLICY, **({"queueDepth": 2} if kind == "distinct" else {}), **(radar_policy or {}))
    docs["camera-component.json"] = _sensor_component(base_component, "camera-sensor", "camera-frames", camera)
    if omit_camera_policy:
        del docs["camera-component.json"]["extensions"]
    docs["radar-component.json"] = _sensor_component(base_component, "radar-sensor", "radar-tracks", radar)
    docs["ecu-component.json"] = copy.deepcopy(base_component)
    docs["ecu-component.json"]["metadata"]["name"] = "aeb-ecu"
    ecu = docs["ecu-component.json"]["spec"]
    ecu["interfaces"] = [
        {"compatibility": "exact", "direction": "input", "id": i, "payloadSchema": f"urn:xverse:experiment:{i}-v1", "unitSemantics": "dimensionless"}
        for i in ("camera-frames", "radar-tracks")
    ]
    ecu["endpoints"] = [{"direction": "input", "id": f"{i}-in", "interfaceId": i, "ownerId": "aeb-ecu"} for i in ("camera-frames", "radar-tracks")]
    system = docs["system.json"]["spec"]
    system["timeDomains"].append({"clockClass": "logical", "epoch": "0", "id": "control-time", "monotonic": True, "rate": "1"})
    system["timeDomains"].append({"clockClass": "monotonic", "epoch": "recording-host-boot", "id": "bridge-recorder-monotonic",
                                  "monotonic": True, "rate": "wall-rate"})  # V06 bridge origin domain (FR-013, M2)
    ref = lambda name: {"apiVersion": API, "kind": "Component", "name": name, "namespace": NAMESPACE}
    system["componentInstances"] = [
        {"componentRef": ref("camera-sensor"), "id": "source-instance", "nodeId": "producer-node"},
        {"componentRef": ref("radar-sensor"), "id": "radar-instance", "nodeId": "producer-node"},
        {"componentRef": ref("aeb-ecu"), "id": "sink-instance", "nodeId": "sink-node"},
    ]
    system["interfaces"] = [
        {"compatibility": "exact", "direction": "bidirectional", "id": i, "payloadSchema": f"urn:xverse:experiment:{i}-v1", "unitSemantics": "dimensionless"}
        for i in ("camera-frames", "radar-tracks")
    ]
    system["endpoints"] = [
        {"direction": "output", "id": "camera-out", "interfaceId": "camera-frames", "ownerId": "source-instance"},
        {"direction": "output", "id": "radar-out", "interfaceId": "radar-tracks", "ownerId": "radar-instance"},
        {"direction": "input", "id": "camera-in", "interfaceId": "camera-frames", "ownerId": "sink-instance"},
        {"direction": "input", "id": "radar-in", "interfaceId": "radar-tracks", "ownerId": "sink-instance"},
    ]
    qualities = {
        "camera-flow": {"freshness": {"value": 6, "unit": "tick"}, "deadline": {"value": 5, "unit": "tick"}, "receiverTimeDomainId": "control-time"},
        "radar-flow": {"freshness": {"value": 6, "unit": "tick"}, "deadline": {"value": 5, "unit": "tick"}},
    }
    qualities.update(quality or {})
    system["flows"] = [
        {"deliveryIntent": (intents or {}).get(fid, "ordered"), "destinationEndpointIds": [dst], "id": fid, "interfaceId": iface,
         "sourceEndpointId": src, "timeDomainId": "experiment-time", "quality": qualities[fid]}
        for fid, src, dst, iface in (("camera-flow", "camera-out", "camera-in", "camera-frames"), ("radar-flow", "radar-out", "radar-in", "radar-tracks"))
    ]
    for flow in system["flows"]:
        if not flow["quality"]:
            del flow["quality"]
    deployment = docs["deployment.json"]
    deployment["spec"]["targets"][0]["capabilities"] = ["execute-model", "xcom.delivery.best-effort", "xcom.ordering.per-route-fifo", *tokens]
    deployment["extensions"] = {"io.xverse.xcom": _xcom("network-provider", _target("Deployment", deployment["metadata"]["name"]), {
        "requiredCapabilities": ["execute-model"], "fidelity": "declared", "limitations": ["owned Phase 6 fixture"]})}
    if second_provider:
        deployment["spec"]["targets"][0]["extensions"] = {"io.xverse.xcom": _xcom("network-provider", _target("Deployment", deployment["metadata"]["name"]), {
            "requiredCapabilities": ["execute-model"], "fidelity": "declared", "limitations": ["second owned provider"]})}
    if deployment_policy is not None:
        target = deployment["spec"]["targets"][0]
        target["extensions"] = {"io.xverse.xcom": _xcom("network-provider", _target("Deployment", deployment["metadata"]["name"]), {
            "requiredCapabilities": ["execute-model"], "fidelity": "declared", "limitations": ["owned Phase 6 fixture"]})}
        deployment["extensions"] = {"io.xverse.xcom": _xcom("flow-policy", _target("Deployment", deployment["metadata"]["name"]),
                                                            dict(FLOW_POLICY, **deployment_policy))}
    scenario = docs["scenario.json"]["spec"]
    scenario["timeMappings"] = mappings if mappings is not None else [
        {"sourceTimeDomainId": "experiment-time", "targetTimeDomainId": "control-time", "mapping": "offset:1tick", "tolerance": {"value": 2, "unit": "tick"}}]
    for observer in scenario.get("observers") or ():
        observer["targetRef"]["element"] = "camera-flow"
    scenario["faults"] = []
    if scenario_policy is not None:
        docs["scenario.json"].setdefault("extensions", {})["io.xverse.xcom"] = _xcom(
            "flow-policy", _target("Scenario", docs["scenario.json"]["metadata"]["name"]), dict(FLOW_POLICY, **scenario_policy))
    profile = copy.deepcopy(docs["profile.json"])
    profile["metadata"]["name"] = "xcom-lite"
    profile["spec"].update(extensionNamespace="io.xverse.xcom", schemaRef="https://xverse.io/profiles/xcom/v0.1/schema.json",
                           documentationRef="https://xverse.io/profiles/xcom/v0.1/README.md")
    docs[XCOM_PROFILE] = profile
    return docs


def compile_fixture(docs: dict[str, dict[str, Any]], faults: list[dict[str, Any]] | None = None) -> tuple[dict[str, Any], tuple[Any, ...]]:
    """Validate and compile ``docs``; return ``(plan, contributing resources)``."""

    docs = copy.deepcopy(docs)
    if faults:
        docs["scenario.json"]["spec"]["faults"] = faults
    validation = validate_sources([(name, json.dumps(value).encode()) for name, value in sorted(docs.items())], profile_schema_paths=SCHEMAS)
    assert validation.is_valid, [(d.code, d.message) for d in validation.diagnostics]
    result = compile_experiment_plan(validation.resources)
    assert result.is_valid, [(d.code, d.message) for d in result.diagnostics]
    plan = json.loads(json.dumps(result.plan, default=lambda value: dict(value) if hasattr(value, "items") else list(value)))
    keys = {(e["kind"], e["name"]) for e in plan["provenance"]["resources"]}
    contributors = tuple(r for r in validation.resources if (r.identity.kind, r.identity.name) in keys)
    return plan, contributors


def write_fixtures() -> None:
    """Write the committed fixture copies (run once; the drift test compares them)."""

    for kind in ("uniform", "distinct"):
        folder = FIXTURES / kind
        folder.mkdir(parents=True, exist_ok=True)
        for name, doc in sorted(documents(kind).items()):
            (folder / name).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
