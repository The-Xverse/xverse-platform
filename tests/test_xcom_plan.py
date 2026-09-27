"""Compiler unit, contract, determinism, bound, and negative tests for X-COM T018.

The tests exercise the deterministic Profile-aware plan compiler in
``src/xverse_xdl/xcom_plan.py``. They import the repository-owned T017 validator's pure
functions from ``scripts/validate_xcom_plan.py`` for independent cross-checking, and they
perform no network access, start no child process, and write no file. All graph inputs are
bounded, repository-owned, public-safe synthetic normalized-graph documents.
"""

from __future__ import annotations

import ast
import copy
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import re

from xverse_xdl import xcom_plan as compiler

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "src" / "xverse_xdl" / "xcom_plan.py"
VALIDATOR = ROOT / "scripts" / "validate_xcom_plan.py"
PROFILE_SCHEMA_PATH = ROOT / "xdl" / "profiles" / "xcom-v0.1.schema.json"
PLAN_SCHEMA_PATH = ROOT / "src" / "xverse" / "xcom" / "contracts" / "v1" / "activation-plan.schema.json"

NAMESPACE = "org.xverse.examples"
API = compiler.API_VERSION

FORM_DEFS = {
    "interface-policy": "interfacePolicy",
    "flow-policy": "flowPolicy",
    "network-provider": "networkProviderPolicy",
    "observation-policy": "observationPolicy",
    "validation-policy": "validationPolicy",
}


def load_validator():
    """Load a fresh T017 validator module from its repository path."""

    spec = spec_from_file_location("validate_xcom_plan_t018_test", VALIDATOR)
    if spec is None or spec.loader is None:
        raise AssertionError("validator module could not be loaded")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()
PLAN_SCHEMA = json.loads(PLAN_SCHEMA_PATH.read_text(encoding="utf-8"))
PROFILE_SCHEMA = json.loads(PROFILE_SCHEMA_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------
# Synthetic normalized-graph fixtures
# --------------------------------------------------------------------------------------


def _identity(kind: str, name: str) -> dict:
    return {
        "apiVersion": API,
        "kind": kind,
        "namespace": NAMESPACE,
        "name": name,
        "uri": f"xdl://{NAMESPACE}/{kind.lower()}/{name}",
    }


def _resource(kind: str, name: str, content: dict, payloads: list | None = None) -> dict:
    resource = {
        "identity": _identity(kind, name),
        "revision": "0.1.0",
        "content": content,
    }
    if payloads is not None:
        resource["extensions"] = {
            compiler.PROFILE_NAMESPACE: {
                "profile": f"xdl://{NAMESPACE}/profile/xcom",
                "payloads": payloads,
            }
        }
    return resource


def _payload(pointer: str, value: dict) -> dict:
    return {"pointer": pointer, "value": value}


def _target(kind: str, name: str, version: str | None = None) -> dict:
    target = {"apiVersion": API, "kind": kind, "namespace": NAMESPACE, "name": name}
    if version is not None:
        target["version"] = version
    return target


def _interface_policy() -> dict:
    return _payload(
        f"/spec/interfaces/0/extensions/{compiler.PROFILE_NAMESPACE}",
        {
            "schemaVersion": "0.1",
            "kind": "interface-policy",
            "target": _target("Component", "signal-source", "0.1.0"),
            "policy": {
                "interactionKind": "message",
                "schemaId": "sample.stream.v1",
                "schemaVersion": "1.0.0",
                "encoding": "json-utf8",
                "semanticCompatibility": "backward-compatible",
            },
        },
    )


def _flow_policy() -> dict:
    return _payload(
        f"/extensions/{compiler.PROFILE_NAMESPACE}",
        {
            "schemaVersion": "0.1",
            "kind": "flow-policy",
            "target": _target("Component", "signal-source"),
            "policy": {
                "ordering": "fifo",
                "reliability": "at-most-once",
                "deadlineMs": 100,
                "retry": 0,
                "queueDepth": 64,
                "overflow": "reject",
                "observationPoints": ["sample-observer"],
            },
        },
    )


def _network_provider(address_member: bool = False) -> dict:
    policy = {
        "requiredCapabilities": ["message"],
        "fidelity": "declared",
        "limitations": ["no external peer in the first proof"],
    }
    if address_member:
        policy["address"] = "loopback.invalid"
    return _payload(
        f"/spec/targets/0/extensions/{compiler.PROFILE_NAMESPACE}",
        {
            "schemaVersion": "0.1",
            "kind": "network-provider",
            "target": _target("Deployment", "local-deployment"),
            "policy": policy,
        },
    )


def _validation_policy(service_emulation_without_permit: bool = False) -> dict:
    policy = {
        "allowedActions": ["inject-message"],
        "injectionPoints": ["endpoint-controller"],
        "serviceEmulation": service_emulation_without_permit,
        "timePolicy": "local-validation-clock",
        "quotas": {"maxActions": 8, "maxRateHz": 8},
    }
    if not service_emulation_without_permit:
        policy["permitPolicyRef"] = "local-permit"
    return _payload(
        f"/spec/steps/0/extensions/{compiler.PROFILE_NAMESPACE}",
        {
            "schemaVersion": "0.1",
            "kind": "validation-policy",
            "target": _target("Scenario", "observe-sample-loop"),
            "policy": policy,
        },
    )


def _component() -> dict:
    return _resource(
        "Component",
        "signal-source",
        {
            "capabilities": ["produce-samples"],
            "interfaces": [{"id": "sample-stream", "direction": "output", "payloadSchema": "urn:x:1"}],
            "endpoints": [
                {"id": "samples-out", "ownerId": "signal-source", "interfaceId": "sample-stream", "direction": "output"}
            ],
        },
        [_interface_policy(), _flow_policy()],
    )


def _system() -> dict:
    return _resource(
        "System",
        "sample-loop",
        {
            "nodes": [{"id": "producer-node", "roles": ["compute"]}, {"id": "observer-node", "roles": ["compute"]}],
            "componentInstances": [
                {
                    "id": "source-instance",
                    "componentRef": {"apiVersion": API, "kind": "Component", "namespace": NAMESPACE, "name": "signal-source"},
                    "nodeId": "producer-node",
                }
            ],
            "interfaces": [{"id": "sample-stream", "direction": "bidirectional", "payloadSchema": "urn:x:1"}],
            "endpoints": [
                {"id": "samples-out", "ownerId": "source-instance", "interfaceId": "sample-stream", "direction": "output"},
                {"id": "samples-in", "ownerId": "observer-node", "interfaceId": "sample-stream", "direction": "input"},
            ],
            "flows": [
                {
                    "id": "sample-flow",
                    "sourceEndpointId": "samples-out",
                    "destinationEndpointIds": ["samples-in"],
                    "interfaceId": "sample-stream",
                    "deliveryIntent": "ordered",
                }
            ],
            "timeDomains": [
                {"id": "experiment-time", "clockClass": "logical", "epoch": "scenario-start", "rate": "one-per-second", "monotonic": True}
            ],
        },
    )


def _deployment() -> dict:
    return _resource(
        "Deployment",
        "local-deployment",
        {
            "systemRef": {"apiVersion": API, "kind": "System", "namespace": NAMESPACE, "name": "sample-loop"},
            "targets": [
                {
                    "id": "simulated-target",
                    "targetClass": "model-unit",
                    "capabilities": ["deterministic-step", "message"],
                    "lifecycle": {"prepare": "p", "ready": "r", "start": "s", "stop": "t", "failure": "f"},
                }
            ],
            "bindings": [
                {
                    "id": "source-binding",
                    "logicalRef": {
                        "apiVersion": API,
                        "kind": "System",
                        "namespace": NAMESPACE,
                        "name": "sample-loop",
                        "element": "source-instance",
                    },
                    "realizationClass": "simulated",
                    "targetId": "simulated-target",
                    "lifecycle": {"prepare": "p", "ready": "r", "start": "s", "stop": "t", "failure": "f"},
                }
            ],
            "readiness": {"requiredConditions": ["all references resolve"], "failurePolicy": "fail-fast"},
        },
        [_network_provider()],
    )


def _scenario() -> dict:
    return _resource(
        "Scenario",
        "observe-sample-loop",
        {
            "systemRef": {"apiVersion": API, "kind": "System", "namespace": NAMESPACE, "name": "sample-loop"},
            "deploymentRef": {"apiVersion": API, "kind": "Deployment", "namespace": NAMESPACE, "name": "local-deployment"},
            "initialConditions": {"sample-count": 0},
            "steps": [
                {
                    "id": "request-sample",
                    "actionKind": "set-parameter",
                    "targetRef": {
                        "apiVersion": API,
                        "kind": "System",
                        "namespace": NAMESPACE,
                        "name": "sample-loop",
                        "element": "source-instance",
                    },
                    "timeDomainId": "experiment-time",
                    "schedule": {"at": 0, "unit": "s"},
                    "action": {"parameter": "nominal-rate", "value": 10},
                }
            ],
            "observers": [
                {
                    "id": "sample-observer",
                    "targetRef": {
                        "apiVersion": API,
                        "kind": "System",
                        "namespace": NAMESPACE,
                        "name": "sample-loop",
                        "element": "sample-flow",
                    },
                    "timeDomainId": "experiment-time",
                }
            ],
            "metrics": [{"id": "sample-count", "observerIds": ["sample-observer"]}],
        },
        [_validation_policy()],
    )


def _graph() -> dict:
    return {"resources": [_system(), _component(), _deployment(), _scenario()]}


def _by_name(graph: dict, name: str) -> dict:
    for resource in graph["resources"]:
        if resource["identity"]["name"] == name:
            return resource
    raise AssertionError(f"resource {name} is absent")


def _remove_resource(graph: dict, name: str) -> dict:
    graph["resources"] = [r for r in graph["resources"] if r["identity"]["name"] != name]
    return graph


def _payloads_of(resource: dict) -> list:
    return resource["extensions"][compiler.PROFILE_NAMESPACE]["payloads"]


def _drop_payload(resource: dict, kind: str) -> None:
    _payloads_of(resource)[:] = [
        record for record in _payloads_of(resource) if record["value"]["kind"] != kind
    ]


def _error_code(callable_) -> str:
    try:
        callable_()
    except compiler.XcomPlanError as exc:
        return exc.code
    raise AssertionError("a rejected/failed compilation was expected")


def _unresolved_families(plan: dict) -> set[str]:
    return {family for family, state in plan["inputResolution"].items() if state == "unresolved"}


# --------------------------------------------------------------------------------------
# CHK-01/CHK-06: public API and constant drift guards
# --------------------------------------------------------------------------------------


def test_compiler_module_public_api():
    """CHK-01: the compiler exposes the declared public API and compiles offline."""

    for name in (
        "CompileLimits",
        "GraphView",
        "XcomPlanError",
        "load_normalized_graph",
        "compile_plan",
        "compile_plan_text",
        "canonical_plan_bytes",
        "compute_digest",
        "plan_matches_digest",
        "plan_status",
        "TASK_ID",
        "GENERATOR_VERSION",
        "PLAN_VERSION",
        "PROFILE_NAMESPACE",
        "PLAN_TARGET",
        "DEFAULT_GENERATED_AT",
        "PLAN_DOMAIN_SEPARATOR",
        "GRAPH_DOMAIN_SEPARATOR",
        "SCOPE_KINDS",
        "PROVENANCE_KINDS",
        "INTERFACE_KINDS",
        "ENDPOINT_ROLES",
        "CLOCK_SOURCES",
        "OVERFLOW_POLICIES",
        "BACKPRESSURE_POLICIES",
        "RESOLUTION_STATES",
        "PLAN_STATUS",
        "PLACEHOLDER_POLICY",
        "ERROR_CODES",
        "DIAGNOSTIC_CODES",
    ):
        assert hasattr(compiler, name), name
    view = compiler.load_normalized_graph(_graph())
    assert isinstance(view, compiler.GraphView)
    plan = compiler.compile_plan(view)
    assert compiler.plan_status(plan) == "activatable"


def test_compiler_constants_match_t017_schema():
    """CHK-06: compiler enums and code patterns equal the T017 activation-plan schema."""

    defs = PLAN_SCHEMA["$defs"]
    policies = defs["policies"]["properties"]
    assert set(compiler.ORDERING_VALUES) == set(policies["ordering"]["enum"])
    assert set(compiler.RELIABILITY_VALUES) == set(policies["reliability"]["enum"])
    assert set(compiler.OVERFLOW_POLICIES) == set(policies["overflow"]["enum"])
    assert set(compiler.BACKPRESSURE_POLICIES) == set(policies["backpressure"]["enum"])
    assert set(compiler.CLOCK_SOURCES) == set(defs["clockDomain"]["properties"]["source"]["enum"])
    assert set(compiler.RESOLUTION_STATES) == set(defs["inputResolution"]["properties"]["identity"]["enum"])
    assert set(compiler.PLAN_STATUS) == set(PLAN_SCHEMA["properties"]["status"]["enum"])
    assert set(compiler.PROVENANCE_KINDS) == set(defs["resourceRef"]["properties"]["kind"]["enum"])
    assert set(compiler.PAYLOAD_ACCESS_VALUES) == set(defs["observationPoint"]["properties"]["payloadAccess"]["enum"])
    assert set(compiler.VALIDITY_EFFECT_VALUES) == set(defs["observationPoint"]["properties"]["validityEffect"]["enum"])
    assert set(compiler.ENDPOINT_ROLES) <= set(defs["endpoint"]["properties"]["role"]["enum"])
    assert set(compiler.PLACEHOLDER_POLICY) == set(defs["policies"]["required"])
    assert defs["diagnostic"]["properties"]["code"]["pattern"] == compiler.ERROR_CODE_PATTERN.pattern
    for code in compiler.ERROR_CODES + compiler.DIAGNOSTIC_CODES:
        assert compiler.ERROR_CODE_PATTERN.match(code), code


def test_payload_grammar_matches_t017_profile_schema():
    """CHK-02, CHK-06: the closed compiler grammar equals the T017 Profile v0.1 schema."""

    assert set(PROFILE_SCHEMA["required"]) == set(compiler.PAYLOAD_MEMBERS)
    assert set(PROFILE_SCHEMA["$defs"]["kind"]["enum"]) == set(compiler.INTERFACE_KINDS)
    target = PROFILE_SCHEMA["$defs"]["target"]
    assert set(target["required"]) == set(compiler.TARGET_REQUIRED)
    assert set(target["properties"]) == set(compiler.TARGET_MEMBERS)
    assert set(target["properties"]["kind"]["enum"]) == set(compiler.TARGET_KINDS)
    for kind, def_name in FORM_DEFS.items():
        form = PROFILE_SCHEMA["$defs"][def_name]
        assert set(form["required"]) == set(compiler.PROFILE_FORM_REQUIRED[kind])
        assert set(form["properties"]) == set(compiler.PROFILE_FORM_PERMITTED[kind])
    assert set(compiler.PROFILE_FORM_COLLECTIONS) == set(compiler.INTERFACE_KINDS)


# --------------------------------------------------------------------------------------
# CHK-03/CHK-04/CHK-05: positive compilation, derivation, and status
# --------------------------------------------------------------------------------------


def test_positive_graph_compiles_to_activatable_plan():
    """CHK-03, CHK-05: a positive graph compiles to a fully resolved activatable plan."""

    plan = compiler.compile_plan(_graph())
    assert plan["planVersion"] == "1"
    assert plan["generator"] == {"task": "T018", "version": compiler.GENERATOR_VERSION}
    assert plan["provenance"]["generatedAt"] == compiler.DEFAULT_GENERATED_AT
    assert plan["status"] == "activatable"
    assert set(plan["inputResolution"].values()) == {"resolved"}
    assert plan["diagnostics"] == []
    assert plan["activationOrder"]
    assert plan["provenance"]["resources"], "at least one contributing resource is required"


def test_compiled_plan_passes_t017_schema_ordering_and_digest():
    """CHK-03: the T017 validator accepts the compiled plan with no findings."""

    plan = compiler.compile_plan(_graph())
    assert validator.validate_plan_structure(plan, PLAN_SCHEMA) == []
    assert validator.check_digest(plan) == []


def test_compiler_digest_agrees_with_t017_reference():
    """CHK-03, DET-01: the compiler digest equals the T017 reference for every compiled plan."""

    plan = compiler.compile_plan(_graph())
    assert compiler.compute_digest(plan) == validator.compute_digest(plan)
    assert compiler.canonical_plan_bytes(plan) == validator.canonical_bytes(plan)
    assert plan["digest"]["value"] == validator.compute_digest(plan)
    assert compiler.plan_matches_digest(plan) is True
    drifted = copy.deepcopy(plan)
    drifted["generator"]["version"] = "0.2.0"
    assert compiler.plan_matches_digest(drifted) is False


def test_positive_graph_derivation():
    """CHK-04: contracts, endpoints, routes, and providers equal the declared derivation."""

    plan = compiler.compile_plan(_graph())
    assert plan["contracts"] == [
        {"contractId": "sample-stream", "schemaId": "sample.stream.v1", "schemaVersion": "1.0.0"}
    ]
    assert plan["endpoints"] == [
        {"endpointId": "samples-in", "role": "responder"},
        {"endpointId": "samples-out", "role": "initiator"},
    ]
    assert plan["routes"] == [
        {"routeId": "sample-flow", "from": "samples-out", "to": "samples-in", "contractId": "sample-stream"}
    ]
    assert plan["providers"] == [
        {"providerId": "simulated-target", "capabilities": ["deterministic-step", "message"], "requiredCapabilities": ["message"]}
    ]
    resources = plan["provenance"]["resources"]
    assert [(r["kind"], r["name"]) for r in resources] == [
        ("Component", "signal-source"),
        ("Deployment", "local-deployment"),
        ("Scenario", "observe-sample-loop"),
    ]


def test_policies_observation_stimulation_clocks():
    """CHK-04: policies, observation points, stimulation, clocks, and order match the design."""

    plan = compiler.compile_plan(_graph())
    assert plan["policies"] == {
        "ordering": "fifo",
        "reliability": "at-most-once",
        "deadlineMs": 100,
        "retry": 0,
        "queueDepth": 64,
        "overflow": "reject",
        "backpressure": "reject",
    }
    assert plan["observationPoints"] == [
        {"tapId": "sample-observer", "routeId": "sample-flow", "payloadAccess": "metadata-only", "validityEffect": "none"}
    ]
    assert plan["stimulation"] == {"actions": ["inject-message"], "permitPolicyRefs": ["local-permit"]}
    assert plan["clockDomains"] == [{"clockDomainId": "experiment-time", "source": "local-validation-clock"}]
    assert plan["activationOrder"] == ["samples-in", "samples-out", "sample-flow"]


def test_inspectable_and_activatable_status_rule():
    """CHK-05: an unresolved family yields inspectable; all-resolved yields activatable."""

    activatable = compiler.compile_plan(_graph())
    assert compiler.plan_status(activatable) == "activatable"
    assert activatable["diagnostics"] == []

    graph = _graph()
    _remove_resource(graph, "local-deployment")
    inspectable = compiler.compile_plan(graph)
    assert compiler.plan_status(inspectable) == "inspectable"
    assert inspectable["diagnostics"], "an inspectable plan carries a diagnostic"
    for entry in inspectable["diagnostics"]:
        assert entry["severity"] == "error"
        assert compiler.ERROR_CODE_PATTERN.match(entry["code"])


def test_unresolved_family_matrix():
    """CHK-05, NEG-C16..NEG-C20, NEG-C27: each family is independently unresolved."""

    def capability_case() -> dict:
        graph = _graph()
        _drop_payload(_by_name(graph, "local-deployment"), "network-provider")
        return graph

    def schema_case() -> dict:
        graph = _graph()
        _drop_payload(_by_name(graph, "signal-source"), "interface-policy")
        return graph

    def time_case() -> dict:
        graph = _graph()
        _drop_payload(_by_name(graph, "observe-sample-loop"), "validation-policy")
        _by_name(graph, "sample-loop")["content"]["timeDomains"][0]["monotonic"] = False
        return graph

    def ownership_case() -> dict:
        graph = _graph()
        endpoints = _by_name(graph, "sample-loop")["content"]["endpoints"]
        endpoints[1]["ownerId"] = "ghost-node"
        return graph

    def policy_case() -> dict:
        graph = _graph()
        _drop_payload(_by_name(graph, "signal-source"), "flow-policy")
        return graph

    def identity_case() -> dict:
        graph = _graph()
        scenario = _by_name(graph, "observe-sample-loop")
        _payloads_of(scenario).append(
            _payload(
                f"/extensions/{compiler.PROFILE_NAMESPACE}",
                {
                    "schemaVersion": "0.1",
                    "kind": "observation-policy",
                    "target": _target("Scenario", "ghost-scenario"),
                    "policy": {
                        "filters": ["sample-flow"],
                        "payloadAccess": "metadata-only",
                        "bounds": {"maxPayloadBytes": 0, "maxRateHz": 1},
                        "validityEffect": "none",
                    },
                },
            )
        )
        return graph

    cases = [
        ("NEG-C16", "capability", "XCOM-PLAN-CAPABILITY-UNRESOLVED", capability_case),
        ("NEG-C17", "schema", "XCOM-PLAN-SCHEMA-UNRESOLVED", schema_case),
        ("NEG-C18", "time", "XCOM-PLAN-TIME-UNRESOLVED", time_case),
        ("NEG-C19", "ownership", "XCOM-PLAN-OWNERSHIP-UNRESOLVED", ownership_case),
        ("NEG-C20", "policy", "XCOM-PLAN-POLICY-UNRESOLVED", policy_case),
        ("NEG-C27", "identity", "XCOM-PLAN-IDENTITY-UNRESOLVED", identity_case),
    ]
    for case_id, family, code, builder in cases:
        plan = compiler.compile_plan(builder())
        assert compiler.plan_status(plan) == "inspectable", case_id
        assert _unresolved_families(plan) == {family}, (case_id, plan["inputResolution"])
        assert any(entry["code"] == code for entry in plan["diagnostics"]), case_id
        assert validator.validate_plan_structure(plan, PLAN_SCHEMA) == [], case_id
        assert validator.check_digest(plan) == [], case_id


# --------------------------------------------------------------------------------------
# CHK-07/CHK-08: bounds and determinism
# --------------------------------------------------------------------------------------


def test_reordered_equivalent_graph_is_byte_identical():
    """CHK-08, DET-01, DET-02: reordered-but-equivalent input yields identical bytes/digest."""

    graph = _graph()
    first = compiler.compile_plan(graph)
    second = compiler.compile_plan(_graph())
    assert compiler.canonical_plan_bytes(first) == compiler.canonical_plan_bytes(second)
    assert compiler.compute_digest(first) == compiler.compute_digest(second)

    reordered = _reorder(copy.deepcopy(graph))
    reordered["resources"] = list(reversed(reordered["resources"]))
    for resource in reordered["resources"]:
        extensions = resource.get("extensions")
        if extensions:
            payloads = extensions[compiler.PROFILE_NAMESPACE]["payloads"]
            extensions[compiler.PROFILE_NAMESPACE]["payloads"] = list(reversed(payloads))
    third = compiler.compile_plan(reordered)
    assert compiler.canonical_plan_bytes(first) == compiler.canonical_plan_bytes(third)
    assert compiler.compute_digest(first) == compiler.compute_digest(third)
    assert validator.compute_digest(first) == validator.compute_digest(third)


def _reorder(value):
    if isinstance(value, dict):
        return {key: _reorder(value[key]) for key in reversed(list(value.keys()))}
    if isinstance(value, list):
        return [_reorder(item) for item in value]
    return value


def test_canonical_bytes_stability_and_integral_numbers():
    """CHK-08, DET-03: canonical bytes are order-stable and normalize integral numbers."""

    assert compiler.canonical_plan_bytes({"a": 1}) == compiler.canonical_plan_bytes({"a": 1.0}) == b'{"a":1}'
    plan = compiler.compile_plan(_graph())
    reordered = _reorder(copy.deepcopy(plan))
    assert compiler.canonical_plan_bytes(plan) == compiler.canonical_plan_bytes(reordered)

    integral = json.loads(json.dumps(plan))
    integral["policies"]["deadlineMs"] = 100.0
    assert compiler.canonical_plan_bytes(plan) == compiler.canonical_plan_bytes(integral)
    assert compiler.compute_digest(plan) == compiler.compute_digest(integral)


def test_declared_bounds_enforced():
    """CHK-07, BND-01..BND-03, NEG-C21, NEG-C22: over-bound inputs/entities fail closed."""

    text = json.dumps(_graph())
    over_bytes = compiler.CompileLimits(max_bytes=len(text.encode("utf-8")) - 1)
    assert _error_code(lambda: compiler.compile_plan_text(text, limits=over_bytes)) == "XCOM-PLAN-BOUND"
    assert _error_code(lambda: compiler.compile_plan(_graph(), limits=compiler.CompileLimits(max_depth=2))) == "XCOM-PLAN-BOUND"
    assert _error_code(lambda: compiler.compile_plan(_graph(), limits=compiler.CompileLimits(max_nodes=1))) == "XCOM-PLAN-BOUND"
    assert _error_code(lambda: compiler.compile_plan(_graph(), limits=compiler.CompileLimits(max_resources=1))) == "XCOM-PLAN-BOUND"
    assert _error_code(lambda: compiler.compile_plan(_graph(), limits=compiler.CompileLimits(max_endpoints=1))) == "XCOM-PLAN-BOUND"
    assert _error_code(lambda: compiler.compile_plan(_graph(), limits=compiler.CompileLimits(max_routes=0))) == "XCOM-PLAN-INPUT"
    assert compiler.plan_status(compiler.compile_plan(_graph())) == "activatable"


def test_graph_view_revalidates_limits_and_does_not_alias_input():
    """A reusable view must remain bounded and immutable after its caller mutates the graph."""

    graph = _graph()
    view = compiler.load_normalized_graph(graph)
    manual = compiler.GraphView(tuple(graph["resources"]))
    baseline = compiler.compute_digest(compiler.compile_plan(view))
    for name in ("max_resources", "max_depth", "max_nodes", "max_bytes"):
        limits = compiler.CompileLimits(**{name: 1})
        assert _error_code(lambda: compiler.compile_plan(view, limits=limits)) == "XCOM-PLAN-BOUND"
        assert _error_code(lambda: compiler.compile_plan(manual, limits=limits)) == "XCOM-PLAN-BOUND"
    graph["resources"][0]["revision"] = "9.9.9"
    assert compiler.compute_digest(compiler.compile_plan(view)) == baseline
    assert compiler.compute_digest(compiler.compile_plan(manual)) == baseline
    view.resources[0]["revision"] = "8.8.8"
    assert compiler.compute_digest(compiler.compile_plan(view)) == baseline


def test_profile_policy_values_are_checked_before_plan_emission():
    """Malformed caller-supplied policy values never yield an activatable plan or raw TypeError."""

    for field, value in (("queueDepth", 0), ("queueDepth", []), ("reliability", "made-up")):
        graph = _graph()
        for resource in graph["resources"]:
            if "extensions" not in resource:
                continue
            for payload in _payloads_of(resource):
                if payload["value"]["kind"] == "flow-policy":
                    payload["value"]["policy"][field] = value
        assert _error_code(lambda: compiler.compile_plan(graph)) == "XCOM-PLAN-PROFILE"


def test_generated_at_rejects_impossible_calendar_and_clock_values():
    """An RFC 3339 shaped but impossible time must not cross the plan boundary."""

    for timestamp in ("2026-02-30T12:00:00Z", "2026-09-27T25:61:61Z", "2026-09-27T12:00:00+24:00"):
        assert _error_code(lambda: compiler.compile_plan(_graph(), generated_at=timestamp)) == "XCOM-PLAN-INPUT"
    plan = compiler.compile_plan(_graph(), generated_at="2024-02-29T23:59:59.123+01:30")
    assert validator.validate_plan_structure(plan, PLAN_SCHEMA) == []


def test_text_parser_failures_use_declared_error_codes():
    """Documents under the byte cap still fail closed when parser depth or integer limits trip."""

    deep = '{"resources":' + '[' * 20_000 + '0' + ']' * 20_000 + '}'
    huge_int = '{"resources":[],"n":' + '1' * 5_000 + '}'
    assert _error_code(lambda: compiler.compile_plan_text(deep)) == "XCOM-PLAN-BOUND"
    assert _error_code(lambda: compiler.compile_plan_text(huge_int)) == "XCOM-PLAN-BOUND"


# --------------------------------------------------------------------------------------
# NEG-C: compiler negative cases
# --------------------------------------------------------------------------------------


def test_compiler_negatives():
    """NEG-C01..NEG-C15, NEG-C23..NEG-C26: every declared defect is classified fail-closed."""

    def input_root_missing():
        return compiler.compile_plan({})

    def input_resources_not_list():
        return compiler.compile_plan({"resources": {"not": "a list"}})

    def input_entry_not_object():
        graph = _graph()
        graph["resources"][0] = 42
        return compiler.compile_plan(graph)

    def input_missing_identity_member():
        graph = _graph()
        del _by_name(graph, "sample-loop")["identity"]["name"]
        return compiler.compile_plan(graph)

    def input_non_finite():
        graph = _graph()
        _by_name(graph, "sample-loop")["content"]["timeDomains"][0]["rate"] = float("nan")
        return compiler.compile_plan(graph)

    def duplicate_resource():
        graph = _graph()
        graph["resources"].append(copy.deepcopy(_by_name(graph, "sample-loop")))
        return compiler.compile_plan(graph)

    def duplicate_json_member():
        return compiler.compile_plan_text('{"resources": [], "resources": []}')

    def ambiguous_system():
        graph = _graph()
        second = copy.deepcopy(_by_name(graph, "sample-loop"))
        second["identity"]["name"] = "second-system"
        graph["resources"].append(second)
        return compiler.compile_plan(graph)

    def multi_destination_flow():
        graph = _graph()
        _by_name(graph, "sample-loop")["content"]["flows"][0]["destinationEndpointIds"] = ["samples-in", "samples-out"]
        return compiler.compile_plan(graph)

    def conflicting_endpoint_role():
        graph = _graph()
        _by_name(graph, "sample-loop")["content"]["flows"][0]["destinationEndpointIds"] = ["samples-out"]
        return compiler.compile_plan(graph)

    def route_id_collision():
        graph = _graph()
        _by_name(graph, "sample-loop")["content"]["flows"][0]["id"] = "samples-out"
        return compiler.compile_plan(graph)

    def empty_activation_order():
        graph = _graph()
        system = _by_name(graph, "sample-loop")["content"]
        system["endpoints"] = []
        system["flows"] = []
        return compiler.compile_plan(graph)

    def unknown_payload_member():
        graph = _graph()
        _payloads_of(_by_name(graph, "signal-source"))[0]["value"]["extra"] = True
        return compiler.compile_plan(graph)

    def form_kind_mismatch():
        graph = _graph()
        _payloads_of(_by_name(graph, "signal-source"))[0]["value"]["policy"] = {"ordering": "fifo"}
        return compiler.compile_plan(graph)

    def duplicate_payload():
        graph = _graph()
        payloads = _payloads_of(_by_name(graph, "signal-source"))
        payloads.append(copy.deepcopy(payloads[0]))
        return compiler.compile_plan(graph)

    def payload_address_member():
        graph = _graph()
        _by_name(graph, "local-deployment")["extensions"][compiler.PROFILE_NAMESPACE]["payloads"] = [_network_provider(address_member=True)]
        return compiler.compile_plan(graph)

    def illegal_attachment_collection():
        graph = _graph()
        record = _payloads_of(_by_name(graph, "signal-source"))[0]
        record["pointer"] = f"/spec/endpoints/0/extensions/{compiler.PROFILE_NAMESPACE}"
        return compiler.compile_plan(graph)

    def observer_target_undeclared():
        graph = _graph()
        _by_name(graph, "observe-sample-loop")["content"]["observers"][0]["targetRef"]["element"] = "ghost-route"
        return compiler.compile_plan(graph)

    def service_emulation_without_permit():
        graph = _graph()
        scenario = _by_name(graph, "observe-sample-loop")
        scenario["extensions"][compiler.PROFILE_NAMESPACE]["payloads"] = [_validation_policy(service_emulation_without_permit=True)]
        return compiler.compile_plan(graph)

    def empty_provenance():
        graph = {"resources": [_system()]}
        return compiler.compile_plan(graph)

    cases = [
        ("NEG-C01", input_root_missing, "XCOM-PLAN-INPUT"),
        ("NEG-C01", input_resources_not_list, "XCOM-PLAN-INPUT"),
        ("NEG-C25", input_entry_not_object, "XCOM-PLAN-INPUT"),
        ("NEG-C02", input_missing_identity_member, "XCOM-PLAN-INPUT"),
        ("NEG-C03", input_non_finite, "XCOM-PLAN-INPUT"),
        ("NEG-C04", duplicate_resource, "XCOM-PLAN-DUPLICATE"),
        ("NEG-C23", duplicate_json_member, "XCOM-PLAN-INPUT"),
        ("NEG-C05", ambiguous_system, "XCOM-PLAN-IDENTITY"),
        ("NEG-C06", multi_destination_flow, "XCOM-PLAN-IDENTITY"),
        ("NEG-C07", conflicting_endpoint_role, "XCOM-PLAN-IDENTITY"),
        ("NEG-C08", route_id_collision, "XCOM-PLAN-DUPLICATE"),
        ("NEG-C24", empty_activation_order, "XCOM-PLAN-IDENTITY"),
        ("NEG-C09", unknown_payload_member, "XCOM-PLAN-PROFILE"),
        ("NEG-C10", form_kind_mismatch, "XCOM-PLAN-PROFILE"),
        ("NEG-C11", duplicate_payload, "XCOM-PLAN-PROFILE"),
        ("NEG-C12", payload_address_member, "XCOM-PLAN-PROFILE"),
        ("NEG-C13", illegal_attachment_collection, "XCOM-PLAN-PROFILE"),
        ("NEG-C14", observer_target_undeclared, "XCOM-PLAN-IDENTITY"),
        ("NEG-C15", service_emulation_without_permit, "XCOM-PLAN-POLICY"),
        ("NEG-C26", empty_provenance, "XCOM-PLAN-INPUT"),
    ]
    for case_id, builder, expected in cases:
        assert _error_code(builder) == expected, case_id


# --------------------------------------------------------------------------------------
# CHK-09/BND-04: governance and offline purity
# --------------------------------------------------------------------------------------


def test_compiler_is_offline_and_pure():
    """CHK-09, BND-04: the compiler is a pure, offline, public-safe source module."""

    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= {"__future__", "copy", "datetime", "hashlib", "json", "math", "re", "collections", "dataclasses", "typing"}
    for forbidden in ("os", "socket", "subprocess", "urllib", "requests", "shutil", "tempfile", "pathlib"):
        assert forbidden not in imported

    opening = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open"
    ]
    assert opening == []
    for token in ("/home/", "/Users/", "BEGIN RSA PRIVATE KEY", "BEGIN OPENSSH PRIVATE KEY"):
        assert token not in source
    assert "xcom-plan" == compiler.PLAN_TARGET


def test_verification_plan_lists_every_implemented_test():
    """Traceability: the T018 verification-plan test table and this module agree exactly."""

    plan = (ROOT / "docs" / "engineering" / "xcom" / "t018" / "verification-plan.md").read_text(encoding="utf-8")
    listed = set(re.findall(r"test_[a-z_]+\.py::(test_[a-z0-9_]+)", plan))
    implemented = set(re.findall(r"^def (test_[a-z0-9_]+)\(", Path(__file__).read_text(encoding="utf-8"), re.MULTILINE))
    assert implemented <= listed, f"tests missing from verification-plan.md: {sorted(implemented - listed)}"
    assert listed <= implemented, f"verification-plan.md lists absent tests: {sorted(listed - implemented)}"
