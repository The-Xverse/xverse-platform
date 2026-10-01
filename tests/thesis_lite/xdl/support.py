"""Neutral fixture builders and normalized-resource helpers for the XDL1 compiler tests.

The helpers below construct *declared intent* only: they contain no scientific protocol
value, no credential, no host address and no execution request. Two entry surfaces are
supported so that both the accepted loader path and the pure normalized path can be
exercised:

* :data:`FIXTURE_PATHS` and :data:`PROFILE_SCHEMA_PATH` drive the accepted loader
  (``compile_experiment_files`` / ``compile_experiment_sources``);
* :func:`normalize` and the ``*_resource`` builders produce already-normalized
  :class:`~xverse_xdl.models.NormalizedResource` values for ``compile_experiment_plan``.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from xverse_xdl.experiment_plan import PROFILE_NAMESPACE
from xverse_xdl.models import (
    FrozenMap, NormalizedResource, ResourceIdentity, SourceLocation, freeze,
)
from xverse_xdl.semantics import EXTENSION_COLLECTIONS

ROOT = Path(__file__).resolve().parents[3]
API = "xverse.io/xdl/v1alpha1"
NAMESPACE = "org.xverse.experiment"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
PROFILE_SCHEMA_PATH = ROOT / "xdl" / "profiles" / "experiment-lite-v0.1.schema.json"
PROFILE_SCHEMA_REFS = (PROFILE_SCHEMA_PATH,)
FIXTURE_PATHS = tuple(
    FIXTURE_DIR / name
    for name in (
        "component.xdl.yaml", "system.xdl.yaml", "deployment.xdl.yaml",
        "scenario.xdl.yaml", "profile.xdl.yaml",
    )
)
PROFILE_SCHEMA_ID = "https://xverse.io/profiles/experiment-lite/v0.1/schema.json"


# --------------------------------------------------------------------------------------
# Declared-intent builders
# --------------------------------------------------------------------------------------


def resource_ref(kind: str, name: str, *, element: str | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "apiVersion": API, "kind": kind, "namespace": NAMESPACE, "name": name,
    }
    if element is not None:
        value["element"] = element
    return value


def provenance(*, limitations: tuple[str, ...] = ()) -> dict[str, Any]:
    value = {
        "source": "xverse-public-example", "revision": "xdl1-rev-1", "maturity": "prototype",
    }
    if limitations:
        value["limitations"] = list(limitations)
    return value


def profile_resource(**overrides: Any) -> dict[str, Any]:
    value = {
        "apiVersion": API,
        "kind": "Profile",
        "metadata": {
            "namespace": NAMESPACE, "name": "experiment-lite", "version": "0.1.0",
            "provenance": provenance(),
        },
        "spec": {
            "extensionNamespace": PROFILE_NAMESPACE,
            "compatibleApiVersions": [API],
            "schemaRef": PROFILE_SCHEMA_ID,
            "documentationRef": "https://xverse.io/profiles/experiment-lite/v0.1/README.md",
            "conflictPolicy": "reject",
        },
    }
    value.update(overrides)
    return value


def component_resource(**overrides: Any) -> dict[str, Any]:
    value = {
        "apiVersion": API,
        "kind": "Component",
        "metadata": {
            "namespace": NAMESPACE, "name": "sample-source", "version": "0.1.0",
            "provenance": provenance(),
        },
        "spec": {
            "capabilities": ["produce-samples"],
            "interfaces": [{
                "id": "sample-stream", "direction": "output",
                "payloadSchema": "urn:xverse:experiment:sample-v1",
                "unitSemantics": "dimensionless", "compatibility": "exact",
            }],
            "endpoints": [{
                "id": "samples-out", "ownerId": "sample-source",
                "interfaceId": "sample-stream", "direction": "output",
            }],
            "parameters": [{
                "id": "nominal-rate", "valueType": "integer", "unitSemantics": "hertz",
                "mutability": "configuration",
            }],
            "models": [{
                "id": "sample-model", "modelKind": "behavioral",
                "externalRef": "urn:xverse:experiment:model:sample",
                "inputs": [], "outputs": [], "maturity": "prototype",
            }],
        },
    }
    value.update(overrides)
    return value


def system_resource(**overrides: Any) -> dict[str, Any]:
    value = {
        "apiVersion": API,
        "kind": "System",
        "metadata": {
            "namespace": NAMESPACE, "name": "sample-loop", "version": "0.1.0",
            "provenance": provenance(),
        },
        "spec": {
            "defaultTimeDomainId": "experiment-time",
            "timeDomains": [
                {"id": "experiment-time", "clockClass": "simulation", "epoch": "0", "rate": "1", "monotonic": True},
                {"id": "control-time", "clockClass": "logical", "epoch": "0", "rate": "1", "monotonic": True},
            ],
            "nodes": [
                {"id": "producer-node", "roles": ["compute"]},
                {"id": "sink-node", "roles": ["compute"]},
            ],
            "componentInstances": [
                {
                    "id": "source-instance",
                    "componentRef": resource_ref("Component", "sample-source"),
                    "nodeId": "producer-node",
                },
                {
                    "id": "sink-instance",
                    "componentRef": resource_ref("Component", "sample-source"),
                    "nodeId": "sink-node",
                },
            ],
            "interfaces": [{
                "id": "sample-stream", "direction": "bidirectional",
                "payloadSchema": "urn:xverse:experiment:sample-v1",
                "unitSemantics": "dimensionless", "compatibility": "exact",
            }],
            "endpoints": [
                {"id": "source-out", "ownerId": "source-instance", "interfaceId": "sample-stream", "direction": "output"},
                {"id": "sink-in", "ownerId": "sink-instance", "interfaceId": "sample-stream", "direction": "input"},
            ],
            "flows": [{
                "id": "sample-flow", "sourceEndpointId": "source-out",
                "destinationEndpointIds": ["sink-in"], "interfaceId": "sample-stream",
                "deliveryIntent": "ordered", "timeDomainId": "experiment-time",
            }],
            "parameters": [{
                "id": "loop-count", "valueType": "integer", "unitSemantics": "count",
                "mutability": "constant",
            }],
        },
    }
    value.update(overrides)
    return value


def deployment_resource(**overrides: Any) -> dict[str, Any]:
    lifecycle = {"prepare": "prepare", "ready": "ready", "start": "start", "stop": "stop", "failure": "failure"}
    value = {
        "apiVersion": API,
        "kind": "Deployment",
        "metadata": {
            "namespace": NAMESPACE, "name": "local-simulated-loop", "version": "0.1.0",
            "provenance": provenance(limitations=("Declared realization intent only; no artifact is retrieved.",)),
        },
        "spec": {
            "systemRef": resource_ref("System", "sample-loop"),
            "targets": [{
                "id": "model-unit-target", "targetClass": "model-unit",
                "capabilities": ["execute-model"], "lifecycle": lifecycle,
            }],
            "artifacts": [{
                "id": "sample-artifact", "artifactKind": "model", "version": "1.0.0",
                "digest": "sha256:" + "ab" * 32,
                "sourceRef": "urn:xverse:experiment:artifact:sample", "maturity": "prototype",
            }],
            "bindings": [{
                "id": "source-binding",
                "logicalRef": resource_ref("System", "sample-loop", element="source-instance"),
                "realizationClass": "simulated",
                "targetId": "model-unit-target",
                "artifactIds": ["sample-artifact"],
                "lifecycle": lifecycle,
                "extensions": {
                    PROFILE_NAMESPACE: {
                        "schemaVersion": "0.1",
                        "kind": "realization-intent",
                        "target": resource_ref("Deployment", "local-simulated-loop", element="source-binding"),
                        "delivery": "in-place",
                        "retry": {"policy": "bounded", "maxAttempts": 3},
                        "protocolBinding": {
                            "standardRef": "urn:xverse:experiment:protocol:sample",
                            "bindingKind": "sample-binding",
                            "compatibility": "exact",
                            "limitations": ["Declared reference only; nothing is resolved."],
                        },
                    },
                },
            }],
            "readiness": {"requiredConditions": ["artifacts-pinned"], "failurePolicy": "fail-fast"},
        },
    }
    value.update(overrides)
    return value


def scenario_intent(**overrides: Any) -> dict[str, Any]:
    value = {
        "schemaVersion": "0.1",
        "kind": "scenario-intent",
        "target": resource_ref("Scenario", "sample-observation-run"),
        "seed": {"value": 7, "unitSemantics": "experiment-seed"},
        "parameters": [
            {"id": "gain", "valueType": "number", "value": 1.5, "unitSemantics": "dimensionless",
             "mutability": "configuration"},
            {"id": "enabled", "valueType": "boolean", "value": True, "unitSemantics": "dimensionless",
             "mutability": "configuration"},
        ],
        "fidelityLimitations": ["Declared intent only; no runtime result is claimed."],
    }
    value.update(overrides)
    return value


def scenario_resource(**overrides: Any) -> dict[str, Any]:
    value = {
        "apiVersion": API,
        "kind": "Scenario",
        "metadata": {
            "namespace": NAMESPACE, "name": "sample-observation-run", "version": "0.1.0",
            "provenance": provenance(limitations=("Acceptance expressions are declared text only.",)),
        },
        "spec": {
            "systemRef": resource_ref("System", "sample-loop"),
            "deploymentRef": resource_ref("Deployment", "local-simulated-loop"),
            "initialConditions": {"sample-count": 0},
            "steps": [
                {
                    "id": "prepare-source", "actionKind": "set-parameter",
                    "targetRef": resource_ref("System", "sample-loop", element="source-instance"),
                    "timeDomainId": "experiment-time",
                    "schedule": {"at": 0, "unit": "ms", "tolerance": {"value": 0, "unit": "ms"}},
                    "action": {"parameter": "nominal-rate", "value": 10},
                    "extensions": {
                        PROFILE_NAMESPACE: {
                            "schemaVersion": "0.1", "kind": "step-intent",
                            "target": resource_ref("Scenario", "sample-observation-run", element="prepare-source"),
                            "phase": "prepare", "dependsOn": [],
                            "duration": {"value": 1, "unit": "ms"}, "parameters": [],
                        },
                    },
                },
                {
                    "id": "start-source", "actionKind": "start",
                    "targetRef": resource_ref("System", "sample-loop", element="source-instance"),
                    "timeDomainId": "experiment-time",
                    "schedule": {"at": 10, "unit": "ms"},
                    "action": {"operation": "start"},
                    "extensions": {
                        PROFILE_NAMESPACE: {
                            "schemaVersion": "0.1", "kind": "step-intent",
                            "target": resource_ref("Scenario", "sample-observation-run", element="start-source"),
                            "phase": "start", "dependsOn": ["prepare-source"],
                            "duration": {"value": 1000000, "unit": "ns"}, "parameters": [],
                        },
                    },
                },
            ],
            "faults": [{
                "id": "stale-sample", "targetRef": resource_ref("System", "sample-loop", element="source-instance"),
                "faultKind": "delay", "activation": "scheduled", "recovery": "automatic", "maturity": "prototype",
                "extensions": {
                    PROFILE_NAMESPACE: {
                        "schemaVersion": "0.1", "kind": "fault-intent",
                        "target": resource_ref("Scenario", "sample-observation-run", element="stale-sample"),
                        "trigger": {"kind": "time", "at": 5, "unit": "ms"},
                        "timeDomainId": "experiment-time",
                        "duration": {"value": 2, "unit": "ms"}, "parameters": [],
                    },
                },
            }],
            "observers": [{
                "id": "sample-observer",
                "targetRef": resource_ref("System", "sample-loop", element="sample-flow"),
                "timeDomainId": "experiment-time",
                "samplingIntent": "observe every declared sample",
                "payloadSchema": "urn:xverse:experiment:sample-v1",
                "unitSemantics": "dimensionless",
                "evidenceSinkRef": "urn:xverse:experiment:evidence:sample-observer",
            }],
            "metrics": [{
                "id": "sample-count", "observerIds": ["sample-observer"],
                "calculationRef": "urn:xverse:experiment:metric:count",
                "unitSemantics": "count",
                "acceptance": "declared acceptance text only",
            }],
            "acceptanceIntent": "Demonstrate offline declared intent compilation only.",
        },
        "extensions": {PROFILE_NAMESPACE: scenario_intent()},
    }
    value.update(overrides)
    return value


# --------------------------------------------------------------------------------------
# Normalization helper (mirrors the accepted normalizer for the declared model surface)
# --------------------------------------------------------------------------------------


def normalize(
    resource: dict[str, Any], *, extra_payloads: tuple[tuple[str, str, dict[str, Any]], ...] = (),
) -> NormalizedResource:
    """Build one immutable normalized resource without schema validation.

    @param resource A declared XDL v1alpha1 resource mapping.
    @param extra_payloads Additional ``(namespace, pointer, payload)`` entries appended to a
        namespace group, used to model a duplicate payload at one attachment pointer.
    """

    identity = ResourceIdentity.from_mapping(resource)
    spec = resource.get("spec", {})
    grouped: dict[str, dict[str, Any]] = {}
    for collection, values in spec.items():
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, dict) and isinstance(value.get("id"), str):
                grouped.setdefault(collection, {})[value["id"]] = value

    payload_groups: dict[str, dict[str, Any]] = {}

    def collect(extensions: dict[str, Any], pointer: str) -> None:
        for namespace, payload in extensions.items():
            entry = payload_groups.setdefault(namespace, {"profile": "", "payloads": []})
            entry["payloads"].append({"pointer": f"{pointer}/{namespace}", "value": payload})

    if isinstance(resource.get("extensions"), dict):
        collect(resource["extensions"], "/extensions")
    for collection in EXTENSION_COLLECTIONS.get(identity.kind, ()):
        for index, item in enumerate(spec.get(collection, [])):
            if isinstance(item, dict) and isinstance(item.get("extensions"), dict):
                collect(item["extensions"], f"/spec/{collection}/{index}/extensions")
    for namespace, pointer, payload in extra_payloads:
        entry = payload_groups.setdefault(namespace, {"profile": "", "payloads": []})
        entry["payloads"].append({"pointer": pointer, "value": payload})

    return NormalizedResource(
        identity=identity,
        revision=resource["metadata"]["version"],
        provenance=freeze(resource["metadata"].get("provenance", {})),
        labels=freeze(resource["metadata"].get("labels", {})),
        elements=freeze(grouped),
        references=(),
        extensions=freeze(payload_groups),
        content=freeze(spec),
        source_map=freeze({"": {"source": "fixture", "line": None, "column": None}}),
    )


def default_set(**tweaks: Any) -> tuple[NormalizedResource, ...]:
    """Return the normalized neutral experiment set, ordered as declared intent."""

    return (
        normalize(tweaks.get("system", system_resource())),
        normalize(tweaks.get("component", component_resource())),
        normalize(tweaks.get("profile", profile_resource())),
        normalize(tweaks.get("deployment", deployment_resource())),
        normalize(tweaks.get("scenario", scenario_resource())),
    )


def codes(result) -> list[str]:
    """Return the diagnostic codes of a compile result in report order."""

    return [item.code for item in result.diagnostics]


def find(result, code: str):
    """Return the first diagnostic with *code*, or ``None``."""

    for item in result.diagnostics:
        if item.code == code:
            return item
    return None


def plain(value: Any) -> Any:
    """Recursively convert immutable normalized values to plain JSON-compatible data."""

    from xverse_xdl.models import FrozenMap as _FrozenMap

    if isinstance(value, _FrozenMap):
        return {str(key): plain(child) for key, child in value.items()}
    if isinstance(value, dict):
        return {str(key): plain(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(child) for child in value]
    return value


def copy_resource(resource: dict[str, Any]) -> dict[str, Any]:
    """Return an independent deep copy of a declared resource mapping."""

    return copy.deepcopy(resource)


def declared(**tweaks: Any) -> list[dict[str, Any]]:
    """Return the declared neutral experiment resources as an ordered list of mappings."""

    return [
        tweaks.get("system", system_resource()),
        tweaks.get("component", component_resource()),
        tweaks.get("profile", profile_resource()),
        tweaks.get("deployment", deployment_resource()),
        tweaks.get("scenario", scenario_resource()),
    ]


def compile_declared(resources: list[dict[str, Any]], **kwargs: Any):
    """Normalize declared resources without schema validation and compile them."""

    from xverse_xdl.experiment_plan import compile_experiment_plan

    return compile_experiment_plan(tuple(normalize(resource) for resource in resources), **kwargs)


def json_sources(resources: list[dict[str, Any]], *, prefix: str = "resource"):
    """Encode declared resources as named JSON byte sources for the accepted loader."""

    import json

    from xverse_xdl.loader import SourceInput

    return tuple(
        SourceInput(f"{prefix}-{index}.json", json.dumps(resource).encode("utf-8"))
        for index, resource in enumerate(resources)
    )


def yaml_sources(paths=FIXTURE_PATHS):
    """Read fixture files as named byte sources for the accepted loader."""

    from xverse_xdl.loader import SourceInput

    return tuple(SourceInput(path.name, path.read_bytes()) for path in paths)


__all__ = [
    "API", "FIXTURE_DIR", "FIXTURE_PATHS", "NAMESPACE", "PROFILE_SCHEMA_ID",
    "PROFILE_SCHEMA_PATH", "PROFILE_SCHEMA_REFS", "ROOT", "codes", "compile_declared",
    "component_resource", "copy_resource", "declared", "default_set", "deployment_resource",
    "find", "json_sources", "normalize", "plain", "profile_resource", "provenance",
    "resource_ref", "scenario_intent", "scenario_resource", "system_resource", "yaml_sources",
]

# SourceLocation is imported for the source-map shape parity with the accepted normalizer.
_ = SourceLocation
