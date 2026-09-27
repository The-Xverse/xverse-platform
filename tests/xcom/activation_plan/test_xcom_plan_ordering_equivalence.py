"""Cross-language ordering-equivalence and regression checks for X-COM T020.

This module exercises the accepted T018 plan compiler (``src/xverse_xdl/xcom_plan.py``) and the
accepted T017 validator (``scripts/validate_xcom_plan.py``) read-only and cross-checks them against
the committed T017 plan fixtures. It performs no network access, starts no child process, and
writes no file; every path is derived from ``__file__`` at run time and every graph input is
bounded, repository-owned, and public-safe synthetic.
"""

from __future__ import annotations

import ast
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import re

from xverse_xdl import xcom_plan as compiler

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "scripts" / "validate_xcom_plan.py"
FIXTURES = ROOT / "tests" / "xcom" / "activation_plan" / "fixtures"
PLAN_FIXTURES = FIXTURES / "plan" / "valid"
VERIFICATION_PLAN = ROOT / "docs" / "engineering" / "xcom" / "t020" / "verification-plan.md"
CPP_SUITES = (
    "t020_ordering_equivalence_tests.cpp",
    "t020_malformed_plan_tests.cpp",
    "t020_drift_tests.cpp",
    "t020_bound_matrix_tests.cpp",
    "t020_regression_tests.cpp",
)

GOLDEN = {
    "plan-activatable.json": {
        "file": "8f32193b5fe9ad3546cbc291eaa276ffae6e41297fa8d990e26997f5c8bc0790",
        "digest": "7aaf63173194330d2debe9faaba2f5ed2125a611ce9f9accc124a9d215a5e4ce",
    },
    "plan-inspectable.json": {
        "file": "48be9d195ed0f324ad497437faeef6f34f6cc6a083989bf7ce3a800e4ec84cd1",
        "digest": "98c13f81e6945485e5ac74bbd0f44b271ca05b68c47a2ac5cc55c964c3030d3f",
    },
}

API = compiler.API_VERSION
NAMESPACE = "org.xverse.t020"


def load_validator():
    """Load a fresh T017 validator module from its repository path."""

    spec = spec_from_file_location("validate_xcom_plan_t020_test", VALIDATOR)
    if spec is None or spec.loader is None:
        raise AssertionError("validator module could not be loaded")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


# --------------------------------------------------------------------------------------
# Bounded, public-safe synthetic normalized graph
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
    resource = {"identity": _identity(kind, name), "revision": "0.1.0", "content": content}
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


def _target(kind: str, name: str) -> dict:
    return {"apiVersion": API, "kind": kind, "namespace": NAMESPACE, "name": name, "version": "0.1.0"}


def _interface_policy() -> dict:
    return _payload(
        f"/spec/interfaces/0/extensions/{compiler.PROFILE_NAMESPACE}",
        {
            "schemaVersion": "0.1",
            "kind": "interface-policy",
            "target": _target("Component", "signal-source"),
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


def _network_provider() -> dict:
    return _payload(
        f"/spec/targets/0/extensions/{compiler.PROFILE_NAMESPACE}",
        {
            "schemaVersion": "0.1",
            "kind": "network-provider",
            "target": _target("Deployment", "local-deployment"),
            "policy": {
                "requiredCapabilities": ["message"],
                "fidelity": "declared",
                "limitations": ["no external peer in the first proof"],
            },
        },
    )


def _validation_policy() -> dict:
    return _payload(
        f"/spec/steps/0/extensions/{compiler.PROFILE_NAMESPACE}",
        {
            "schemaVersion": "0.1",
            "kind": "validation-policy",
            "target": _target("Scenario", "observe-sample-loop"),
            "policy": {
                "allowedActions": ["inject-message"],
                "injectionPoints": ["endpoint-controller"],
                "serviceEmulation": False,
                "timePolicy": "local-validation-clock",
                "quotas": {"maxActions": 8, "maxRateHz": 8},
                "permitPolicyRef": "local-permit",
            },
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
                {
                    "id": "samples-out",
                    "ownerId": "signal-source",
                    "interfaceId": "sample-stream",
                    "direction": "output",
                }
            ],
        },
        [_interface_policy(), _flow_policy()],
    )


def _system() -> dict:
    return _resource(
        "System",
        "sample-loop",
        {
            "nodes": [{"id": "producer-node"}, {"id": "observer-node"}],
            "componentInstances": [
                {
                    "id": "source-instance",
                    "componentRef": {
                        "apiVersion": API,
                        "kind": "Component",
                        "namespace": NAMESPACE,
                        "name": "signal-source",
                    },
                    "nodeId": "producer-node",
                }
            ],
            "interfaces": [{"id": "sample-stream", "direction": "bidirectional", "payloadSchema": "urn:x:1"}],
            "endpoints": [
                {
                    "id": "samples-out",
                    "ownerId": "source-instance",
                    "interfaceId": "sample-stream",
                    "direction": "output",
                },
                {
                    "id": "samples-in",
                    "ownerId": "observer-node",
                    "interfaceId": "sample-stream",
                    "direction": "input",
                },
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
                {
                    "id": "experiment-time",
                    "clockClass": "logical",
                    "epoch": "scenario-start",
                    "rate": "one-per-second",
                    "monotonic": True,
                }
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
            "deploymentRef": {
                "apiVersion": API,
                "kind": "Deployment",
                "namespace": NAMESPACE,
                "name": "local-deployment",
            },
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


def _diagnostic_graph() -> dict:
    """A bounded variant that compiles to an inspectable plan carrying ordered diagnostics."""

    return {"resources": [_system(), _component()]}


def _fixture(name: str) -> dict:
    return json.loads((PLAN_FIXTURES / name).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------
# CHK-20-01/02, SC-002: ordering equivalence and cross-language canonical agreement
# --------------------------------------------------------------------------------------


def test_t020_compiler_and_validator_agree_on_canonical_bytes():
    """T20-ORD-01: the compiler and the T017 validator agree on the canonical bytes."""

    plan = compiler.compile_plan(_graph())
    assert compiler.plan_matches_digest(plan)
    assert compiler.canonical_plan_bytes(plan) == validator.canonical_bytes(plan)
    # An integral-number variant shares the one canonical form.
    integral = json.loads(json.dumps(plan))
    integral["policies"]["deadlineMs"] = 100.0
    assert compiler.canonical_plan_bytes(integral) == compiler.canonical_plan_bytes(plan)
    assert compiler.compute_digest(integral) == compiler.compute_digest(plan)


def test_t020_equivalent_graphs_produce_byte_identical_plans():
    """T20-ORD-02, T20-DET-02: equivalent graphs compile to byte-identical plans and digests."""

    forward = compiler.compile_plan(_graph())
    reversed_resources = list(reversed(_graph()["resources"]))
    reverse = compiler.compile_plan({"resources": reversed_resources})
    assert compiler.canonical_plan_bytes(forward) == compiler.canonical_plan_bytes(reverse)
    assert compiler.compute_digest(forward) == compiler.compute_digest(reverse)
    assert forward["digest"] == reverse["digest"]
    # A repeated compilation of the same graph is identical.
    again = compiler.compile_plan(_graph())
    assert compiler.canonical_plan_bytes(again) == compiler.canonical_plan_bytes(forward)


def test_t020_diagnostic_ordering_is_deterministic():
    """T20-ORD-05: compiled diagnostics are ordered deterministically across equivalent inputs."""

    plan = compiler.compile_plan(_diagnostic_graph())
    assert plan["diagnostics"], "the diagnostic graph must carry at least one diagnostic"
    ordered = sorted((entry["code"], entry["targetId"]) for entry in plan["diagnostics"])
    assert [(entry["code"], entry["targetId"]) for entry in plan["diagnostics"]] == ordered

    reversed_resources = list(reversed(_diagnostic_graph()["resources"]))
    mirrored = compiler.compile_plan({"resources": reversed_resources})
    assert mirrored["diagnostics"] == plan["diagnostics"]


# --------------------------------------------------------------------------------------
# CHK-20-06/07: committed-fixture regression and malformed-plan matrix
# --------------------------------------------------------------------------------------


def test_t020_committed_fixtures_match_reference_digest():
    """T20-REG-03, T20-REG-07: each fixture matches its golden digest and file hash."""

    for name, golden in GOLDEN.items():
        path = PLAN_FIXTURES / name
        raw = path.read_bytes()
        plan = json.loads(raw)
        assert hashlib.sha256(raw).hexdigest() == golden["file"], name
        assert plan["digest"]["value"] == golden["digest"], name
        assert validator.compute_digest(plan) == golden["digest"], name
        assert validator.check_digest(plan) == [], name
        assert compiler.canonical_plan_bytes(plan) == validator.canonical_bytes(plan), name


def test_t020_malformed_plan_matrix_is_rejected():
    """T20-MAL-06, T20-MAL-08: declared plan-schema/digest mutations are flagged."""

    plan_schema = json.loads(
        (ROOT / "src" / "xverse" / "xcom" / "contracts" / "v1" / "activation-plan.schema.json").read_text(
            encoding="utf-8"
        )
    )
    base = _fixture("plan-activatable.json")

    missing = json.loads(json.dumps(base))
    missing.pop("clockDomains")
    assert validator.validate_plan_structure(missing, plan_schema), "a missing member must be rejected"

    unknown = json.loads(json.dumps(base))
    unknown["unknownT020Member"] = 1
    assert validator.validate_plan_structure(unknown, plan_schema), "an unknown member must be rejected"

    drifted = json.loads(json.dumps(base))
    drifted["generator"]["version"] = "9.9.9"
    digest_findings = validator.check_digest(drifted)
    assert any(finding.code == validator.DIGEST_INVALID for finding in digest_findings)

    assert validator.validate_plan_structure(base, plan_schema) == []
    assert validator.check_digest(base) == []


# --------------------------------------------------------------------------------------
# CHK-20-09/10: governance / traceability reconciliation
# --------------------------------------------------------------------------------------

FORBIDDEN_IMPORTS = frozenset(
    {"socket", "subprocess", "urllib", "http", "requests", "ftplib", "smtplib", "asyncio"}
)
ALLOWED_IMPORTS = frozenset(
    {"__future__", "ast", "hashlib", "importlib", "json", "pathlib", "re", "xverse_xdl"}
)


def test_t020_module_is_offline_and_pure():
    """T20-G03: this module imports only the standard library and repository modules and performs
    no network, subprocess, or filesystem-write access and embeds no absolute host path."""

    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module.split(".")[0])
    assert not (imported & FORBIDDEN_IMPORTS), sorted(imported & FORBIDDEN_IMPORTS)
    assert imported <= ALLOWED_IMPORTS, sorted(imported - ALLOWED_IMPORTS)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            raise AssertionError("the module must not open any file")

    host_path = re.compile("/" + "home" + "/" + "|/" + "Users" + "/" + "|/" + "root" + "/")
    assert host_path.search(source) is None


def test_t020_verification_plan_lists_every_implemented_test():
    """T20-G05, CHK-20-08: the plan's §8 tables and the implemented tests agree exactly."""

    document = VERIFICATION_PLAN.read_text(encoding="utf-8")
    section = document.split("## 8. Exact planned tests")[1].split("**Reconciliation rule.**")[0]

    listed_cpp = set(re.findall(r"T20[A-Za-z]+\.\w+", section))
    implemented_cpp: set[str] = set()
    for name in CPP_SUITES:
        source = (ROOT / "tests" / "xcom" / "activation_plan" / name).read_text(encoding="utf-8")
        implemented_cpp |= {
            f"{match.group(1)}.{match.group(2)}"
            for match in re.finditer(r"TEST\((T20[A-Za-z]+),\s*(\w+)\)", source)
        }
    assert implemented_cpp == listed_cpp, (
        f"missing from plan §8: {sorted(implemented_cpp - listed_cpp)}; "
        f"planned but absent: {sorted(listed_cpp - implemented_cpp)}"
    )

    listed_py = set(re.findall(r"test_t020_[a-z0-9_]+", section))
    module_source = Path(__file__).read_text(encoding="utf-8")
    implemented_py = set(re.findall(r"^def (test_t020_[a-z0-9_]+)\(", module_source, re.MULTILINE))
    assert implemented_py == listed_py, (
        f"missing from plan §8: {sorted(implemented_py - listed_py)}; "
        f"planned but absent: {sorted(listed_py - implemented_py)}"
    )
