"""Deterministic Profile-aware activation-plan compiler (X-COM T018).

This module compiles an already normalized and validated XDL graph document plus the
``io.xverse.xcom`` Profile v0.1 payloads into the canonical activation-plan v1 value
defined by T017 (``src/xverse/xcom/contracts/v1/activation-plan.schema.json``).

The compiler is a pure, offline, bounded function library:

* it reads only the in-memory normalized graph document (or its JSON text form);
* it opens no file, starts no subprocess, opens no socket, and writes nothing;
* it imports only the Python standard library;
* every collection is ordered by its declared key, every diagnostic is ordered by
  ``(code, targetId)``, and the generation time is explicit or the fixed sentinel, so
  semantically equivalent inputs produce byte-identical canonical bytes and the same
  digest.

It does not implement the bounded C++ decoder (T019) and it defines no competing
configuration language: the plan is derived from declared graph members only.
"""

from __future__ import annotations

import hashlib
import copy
import json
import math
import re
from datetime import datetime
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "API_VERSION",
    "BACKPRESSURE_POLICIES",
    "CLOCK_SOURCES",
    "CompileLimits",
    "DEFAULT_GENERATED_AT",
    "DIAGNOSTIC_CODES",
    "ENDPOINT_ROLES",
    "ERROR_CODES",
    "GENERATOR_VERSION",
    "GRAPH_DOMAIN_SEPARATOR",
    "GraphView",
    "INTERFACE_KINDS",
    "ORDERING_VALUES",
    "OVERFLOW_POLICIES",
    "PLACEHOLDER_POLICY",
    "PLAN_DOMAIN_SEPARATOR",
    "PLAN_STATUS",
    "PLAN_TARGET",
    "PLAN_VERSION",
    "PROFILE_NAMESPACE",
    "PROVENANCE_KINDS",
    "RELIABILITY_VALUES",
    "RESOLUTION_STATES",
    "SCOPE_KINDS",
    "TASK_ID",
    "XcomPlanError",
    "canonical_plan_bytes",
    "compile_plan",
    "compile_plan_text",
    "compute_digest",
    "load_normalized_graph",
    "plan_matches_digest",
    "plan_status",
]

# --------------------------------------------------------------------------------------
# Closed vocabularies and fixed identifiers (T018 detailed design §2)
# --------------------------------------------------------------------------------------

TASK_ID = "T018"
GENERATOR_VERSION = "0.1.0"
PLAN_VERSION = "1"
PROFILE_NAMESPACE = "io.xverse.xcom"
API_VERSION = "xverse.io/xdl/v1alpha1"
DEFAULT_GENERATED_AT = "1970-01-01T00:00:00Z"
PLAN_TARGET = "xcom-plan"

PLAN_DOMAIN_SEPARATOR = b"xverse.xcom.activation-plan.v1\x00"
GRAPH_DOMAIN_SEPARATOR = b"xverse.xcom.normalized-graph.v1\x00"

# Plan identifier and version patterns (T017 activation-plan schema `$defs`).
PLAN_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")
PLAN_IDENTIFIER_MAX_LENGTH = 127
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+(?:\.[0-9]+)?$")
GENERATOR_VERSION_PATTERN = VERSION_PATTERN
DATETIME_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)
DIGEST_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")
ERROR_CODE_PATTERN = re.compile(r"^XCOM-[A-Z0-9-]{3,64}$")

SCOPE_KINDS = ("System", "Component", "Deployment", "Scenario", "Profile")
PROVENANCE_KINDS = ("Component", "Deployment", "Scenario")
INTERFACE_KINDS = (
    "interface-policy",
    "flow-policy",
    "network-provider",
    "observation-policy",
    "validation-policy",
)
ENDPOINT_ROLES = ("initiator", "responder")
CLOCK_SOURCES = ("monotonic", "local-validation-clock", "unmapped")
ORDERING_VALUES = ("fifo", "priority", "unordered")
RELIABILITY_VALUES = ("at-most-once", "at-least-once", "exactly-once", "best-effort")
OVERFLOW_POLICIES = (
    "drop-oldest",
    "drop-newest",
    "coalesce",
    "lossless-backpressure",
    "reject",
    "fail-closed",
)
BACKPRESSURE_POLICIES = ("fail-closed", "reject", "lossless-backpressure")
PAYLOAD_ACCESS_VALUES = ("metadata-only", "allow-listed")
VALIDITY_EFFECT_VALUES = ("none", "degrade-on-loss", "invalidate-on-loss")
RESOLUTION_STATES = ("resolved", "unresolved")
PLAN_STATUS = ("inspectable", "activatable")

POLICY_FIELDS = ("ordering", "reliability", "deadlineMs", "retry", "queueDepth", "overflow")

PLACEHOLDER_POLICY: Mapping[str, Any] = {
    "ordering": "unordered",
    "reliability": "best-effort",
    "deadlineMs": 0,
    "retry": 0,
    "queueDepth": 1,
    "overflow": "fail-closed",
    "backpressure": "fail-closed",
}

ERROR_CODES = (
    "XCOM-PLAN-INPUT",
    "XCOM-PLAN-BOUND",
    "XCOM-PLAN-IDENTITY",
    "XCOM-PLAN-DUPLICATE",
    "XCOM-PLAN-PROFILE",
    "XCOM-PLAN-CONTRACT",
    "XCOM-PLAN-POLICY",
    "XCOM-PLAN-CAPABILITY",
    "XCOM-PLAN-UNKNOWN",
)
DIAGNOSTIC_CODES = (
    "XCOM-PLAN-IDENTITY-UNRESOLVED",
    "XCOM-PLAN-SCHEMA-UNRESOLVED",
    "XCOM-PLAN-CAPABILITY-UNRESOLVED",
    "XCOM-PLAN-TIME-UNRESOLVED",
    "XCOM-PLAN-OWNERSHIP-UNRESOLVED",
    "XCOM-PLAN-POLICY-UNRESOLVED",
    "XCOM-PLAN-POLICY-CONFLICT",
)
# The failed class is bound/unknown; every other code is the rejected class.
FAILED_CODES = ("XCOM-PLAN-BOUND", "XCOM-PLAN-UNKNOWN")

ERROR_INPUT = "XCOM-PLAN-INPUT"
ERROR_BOUND = "XCOM-PLAN-BOUND"
ERROR_IDENTITY = "XCOM-PLAN-IDENTITY"
ERROR_DUPLICATE = "XCOM-PLAN-DUPLICATE"
ERROR_PROFILE = "XCOM-PLAN-PROFILE"
ERROR_CONTRACT = "XCOM-PLAN-CONTRACT"
ERROR_POLICY = "XCOM-PLAN-POLICY"
ERROR_CAPABILITY = "XCOM-PLAN-CAPABILITY"
ERROR_UNKNOWN = "XCOM-PLAN-UNKNOWN"

_PLAN_IDENTIFIER = PLAN_IDENTIFIER_PATTERN

# Closed Profile v0.1 grammar table, drift-guarded against `xdl/profiles/xcom-v0.1.schema.json`
# (detailed design §2.3). `required` is the schema's required member set; `permitted` is the
# closed member set; `collections` is an element-level attachment allowance. Every form may also
# be attached at the resource level of a legal-target resource (see `_resource_level_legal`).
PROFILE_FORM_REQUIRED: Mapping[str, tuple[str, ...]] = {
    "interface-policy": (
        "interactionKind",
        "schemaId",
        "schemaVersion",
        "encoding",
        "semanticCompatibility",
    ),
    "flow-policy": (
        "ordering",
        "reliability",
        "deadlineMs",
        "retry",
        "queueDepth",
        "overflow",
        "observationPoints",
    ),
    "network-provider": ("requiredCapabilities", "fidelity", "limitations"),
    "observation-policy": ("filters", "payloadAccess", "bounds", "validityEffect"),
    "validation-policy": (
        "allowedActions",
        "injectionPoints",
        "serviceEmulation",
        "timePolicy",
        "quotas",
        "permitPolicyRef",
    ),
}
PROFILE_FORM_OPTIONAL: Mapping[str, tuple[str, ...]] = {
    "interface-policy": (),
    "flow-policy": (),
    "network-provider": (),
    "observation-policy": ("allowList",),
    "validation-policy": (),
}
PROFILE_FORM_PERMITTED: Mapping[str, tuple[str, ...]] = {
    kind: PROFILE_FORM_REQUIRED[kind] + PROFILE_FORM_OPTIONAL[kind] for kind in INTERFACE_KINDS
}
PROFILE_FORM_COLLECTIONS: Mapping[str, frozenset[str]] = {
    "interface-policy": frozenset({"interfaces"}),
    "flow-policy": frozenset({"flows"}),
    "network-provider": frozenset({"targets", "networkBindings"}),
    "observation-policy": frozenset({"observers"}),
    "validation-policy": frozenset({"steps"}),
}
PAYLOAD_MEMBERS = ("schemaVersion", "kind", "target", "policy")
TARGET_REQUIRED = ("apiVersion", "kind", "namespace", "name")
TARGET_MEMBERS = ("apiVersion", "kind", "namespace", "name", "version")
TARGET_KINDS = PROVENANCE_KINDS


class XcomPlanError(Exception):
    """A classified compilation failure carrying a stable code and a bounded message."""

    def __init__(self, code: str, message: str) -> None:
        """Initialize the failure with a stable code and a public-safe message."""

        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def error_outcome(code: str) -> str:
    """Return the closed outcome class (``failed``/``rejected``) for a stable error code."""

    return "failed" if code in FAILED_CODES else "rejected"


# --------------------------------------------------------------------------------------
# Bounds (T018 detailed design §3; unit-specifications §3.1)
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class CompileLimits:
    """Fail-closed offline-input and compiled-entity caps (not production values)."""

    max_bytes: int = 5 * 1024 * 1024
    max_depth: int = 100
    max_nodes: int = 100_000
    max_resources: int = 1_000
    max_endpoints: int = 4_096
    max_routes: int = 4_096
    max_providers: int = 256
    max_observation_points: int = 1_024
    max_clock_domains: int = 256
    max_diagnostics: int = 4_096

    def __post_init__(self) -> None:
        """Reject a non-positive limit that would make bounded compilation ambiguous."""

        values = (
            self.max_bytes,
            self.max_depth,
            self.max_nodes,
            self.max_resources,
            self.max_endpoints,
            self.max_routes,
            self.max_providers,
            self.max_observation_points,
            self.max_clock_domains,
            self.max_diagnostics,
        )
        for name, value in zip(self.__dataclass_fields__, values):
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise XcomPlanError(ERROR_INPUT, f"compile limit {name} must be a positive integer")


@dataclass(frozen=True, init=False)
class GraphView:
    """Caller-owned immutable snapshot of identity-sorted normalized resources."""

    _snapshot: tuple[Mapping[str, Any], ...]

    def __init__(self, resources: tuple[Mapping[str, Any], ...]) -> None:
        object.__setattr__(self, "_snapshot", copy.deepcopy(tuple(resources)))

    @property
    def resources(self) -> tuple[Mapping[str, Any], ...]:
        """Return a detached copy so callers cannot mutate a compiled view."""

        return copy.deepcopy(self._snapshot)


# --------------------------------------------------------------------------------------
# Small pure helpers
# --------------------------------------------------------------------------------------


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _identity_key(resource: Mapping[str, Any]) -> tuple[str, str, str, str]:
    identity = resource["identity"]
    return (
        str(identity["apiVersion"]),
        str(identity["kind"]),
        str(identity["namespace"]),
        str(identity["name"]),
    )


def _identity_of(resource: Mapping[str, Any]) -> dict[str, Any]:
    identity = resource["identity"]
    return {
        "apiVersion": identity["apiVersion"],
        "kind": identity["kind"],
        "namespace": identity["namespace"],
        "name": identity["name"],
    }


def _resource_key(resource: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return _identity_key(resource)


def _spec(resource: Mapping[str, Any]) -> Mapping[str, Any]:
    content = resource.get("content")
    return content if isinstance(content, Mapping) else {}


def _content_list(resource: Mapping[str, Any], collection: str) -> list[Any]:
    value = _spec(resource).get(collection)
    return list(value) if isinstance(value, (list, tuple)) else []


def _plan_id(value: Any, code: str, label: str) -> str:
    """Return *value* when it is a plan identifier, otherwise fail closed."""

    if (
        not isinstance(value, str)
        or not _PLAN_IDENTIFIER.match(value)
        or len(value) > PLAN_IDENTIFIER_MAX_LENGTH
    ):
        raise XcomPlanError(code, f"{label} is not a plan identifier")
    return value


def _reject_duplicate_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object, failing closed on a repeated member name."""

    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise XcomPlanError(ERROR_INPUT, "graph JSON repeats a member name")
        result[key] = value
    return result


def _measure_shape(value: Any) -> tuple[int, int]:
    """Return (maximum depth, node count), rejecting a non-finite number."""

    depth = 0
    nodes = 0
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        current, level = stack.pop()
        nodes += 1
        if level > depth:
            depth = level
        if isinstance(current, float) and not math.isfinite(current):
            raise XcomPlanError(ERROR_INPUT, "graph input contains a non-finite number")
        if isinstance(current, Mapping):
            for child in current.values():
                stack.append((child, level + 1))
        elif isinstance(current, (list, tuple)):
            for child in current:
                stack.append((child, level + 1))
    return depth, nodes


# --------------------------------------------------------------------------------------
# T018-U-01 Graph input loading and bounds
# --------------------------------------------------------------------------------------


def load_normalized_graph(document: Any, *, limits: CompileLimits | None = None) -> GraphView:
    """Validate and bound an admitted graph input into an immutable ``GraphView``.

    @param document A ``GraphView``, a ``{"resources": [...]}`` mapping, or a sequence of
        resource mappings produced by the accepted ``xverse_xdl`` normalization path.
    @param limits The offline-input bounds.
    @return An immutable, identity-sorted resource view.
    @raises XcomPlanError On malformed shape, a non-finite number, an invalid identity, a
        duplicate identity, or an over-bound input.
    """

    limits = limits if limits is not None else CompileLimits()
    if isinstance(document, GraphView):
        resources: Any = document.resources
    elif isinstance(document, Mapping):
        if "resources" not in document:
            raise XcomPlanError(ERROR_INPUT, "graph document must carry a resources array")
        resources: Any = document["resources"]
    elif _is_sequence(document):
        resources = list(document)
    else:
        raise XcomPlanError(ERROR_INPUT, "graph document must be an object or a resource sequence")
    if not isinstance(resources, (list, tuple)):
        raise XcomPlanError(ERROR_INPUT, "graph resources must be an array")
    if len(resources) > limits.max_resources:
        raise XcomPlanError(ERROR_BOUND, "graph resource count exceeds max_resources")

    entries: list[Mapping[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for entry in resources:
        if not isinstance(entry, Mapping):
            raise XcomPlanError(ERROR_INPUT, "graph resource entry must be an object")
        identity = entry.get("identity")
        if not isinstance(identity, Mapping):
            raise XcomPlanError(ERROR_INPUT, "graph resource entry must carry an identity object")
        api_version = identity.get("apiVersion")
        kind = identity.get("kind")
        namespace = identity.get("namespace")
        name = identity.get("name")
        if not all(isinstance(value, str) and value for value in (api_version, kind, namespace, name)):
            raise XcomPlanError(ERROR_INPUT, "graph resource identity members must be non-empty strings")
        if kind not in SCOPE_KINDS:
            raise XcomPlanError(ERROR_INPUT, "graph resource kind is not a declared XDL scope kind")
        _plan_id(namespace, ERROR_INPUT, "resource namespace")
        _plan_id(name, ERROR_INPUT, "resource name")
        key = (api_version, kind, namespace, name)
        if key in seen:
            raise XcomPlanError(ERROR_DUPLICATE, "graph carries a duplicate resource identity")
        seen.add(key)
        entries.append(entry)

    depth, nodes = _measure_shape(entries)
    if depth > limits.max_depth:
        raise XcomPlanError(ERROR_BOUND, "graph depth exceeds max_depth")
    if nodes > limits.max_nodes:
        raise XcomPlanError(ERROR_BOUND, "graph node count exceeds max_nodes")
    try:
        graph_bytes = json.dumps(entries, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise XcomPlanError(ERROR_INPUT, "graph resources must be JSON-compatible") from exc
    if len(graph_bytes) > limits.max_bytes:
        raise XcomPlanError(ERROR_BOUND, "graph input exceeds max_bytes")
    entries.sort(key=_identity_key)
    return GraphView(resources=tuple(entries))


def compile_plan_text(
    text: str,
    *,
    generated_at: str | None = None,
    generator_version: str = GENERATOR_VERSION,
    limits: CompileLimits | None = None,
) -> dict[str, Any]:
    """Bound, parse, and compile a normalized graph document supplied as JSON text."""

    active = limits if limits is not None else CompileLimits()
    if not isinstance(text, str):
        raise XcomPlanError(ERROR_INPUT, "graph text must be a string")
    if len(text.encode("utf-8")) > active.max_bytes:
        raise XcomPlanError(ERROR_BOUND, "graph text exceeds max_bytes")
    depth = 0
    inside_string = False
    escaped = False
    for character in text:
        if inside_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                inside_string = False
        elif character == '"':
            inside_string = True
        elif character in "{[":
            depth += 1
            if depth > active.max_depth + 2:
                raise XcomPlanError(ERROR_BOUND, "graph JSON exceeds max_depth")
        elif character in "}]":
            depth -= 1
    try:
        document = json.loads(text, object_pairs_hook=_reject_duplicate_members)
    except XcomPlanError:
        raise
    except json.JSONDecodeError as exc:
        raise XcomPlanError(ERROR_INPUT, f"graph JSON is malformed: {exc.msg}") from exc
    except RecursionError as exc:
        raise XcomPlanError(ERROR_BOUND, "graph JSON exceeds parser depth") from exc
    except ValueError as exc:
        raise XcomPlanError(ERROR_BOUND, "graph JSON exceeds numeric parser bounds") from exc
    return compile_plan(
        document,
        generated_at=generated_at,
        generator_version=generator_version,
        limits=active,
    )


# --------------------------------------------------------------------------------------
# T018-U-02 Profile payload index and closed grammar
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _ProfileRecord:
    resource_key: tuple[str, str, str, str]
    kind: str
    collection: str
    element_id: str | None
    pointer: str
    target: Mapping[str, Any]
    policy: Mapping[str, Any]

    @property
    def sort_key(self) -> tuple[str, tuple[str, str, str, str], str, str, str]:
        return (self.kind, self.resource_key, self.collection, self.element_id or "", self.pointer)


def _validate_policy_values(kind: str, policy: Mapping[str, Any]) -> None:
    """Enforce the Profile's closed value grammar before any policy is derived."""

    required = set(PROFILE_FORM_REQUIRED[kind])
    # A missing stimulation permit has the established XCOM-PLAN-POLICY classification.
    if kind == "validation-policy":
        required.discard("permitPolicyRef")
    if not required <= set(policy):
        raise XcomPlanError(ERROR_PROFILE, "profile policy is missing a required member")

    def choice(field: str, allowed: tuple[str, ...]) -> None:
        if not isinstance(policy[field], str) or policy[field] not in allowed:
            raise XcomPlanError(ERROR_PROFILE, f"profile policy {field} is outside its closed vocabulary")

    def integer(value: Any, label: str, low: int, high: int) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
            raise XcomPlanError(ERROR_PROFILE, f"profile policy {label} is outside its integer bounds")

    def identifiers(value: Any, label: str, *, nonempty: bool = False) -> None:
        if not isinstance(value, (list, tuple)) or (nonempty and not value):
            raise XcomPlanError(ERROR_PROFILE, f"profile policy {label} must be an identifier array")
        seen: set[str] = set()
        for item in value:
            identifier = _plan_id(item, ERROR_PROFILE, label)
            if identifier in seen:
                raise XcomPlanError(ERROR_PROFILE, f"profile policy {label} repeats an identifier")
            seen.add(identifier)

    if kind == "interface-policy":
        choice("interactionKind", ("signal", "message", "service"))
        choice("semanticCompatibility", ("exact", "backward-compatible", "forward-compatible", "none"))
        for field in ("schemaId", "encoding"):
            _plan_id(policy[field], ERROR_PROFILE, field)
        if not isinstance(policy["schemaVersion"], str) or not VERSION_PATTERN.fullmatch(policy["schemaVersion"]):
            raise XcomPlanError(ERROR_PROFILE, "profile policy schemaVersion is invalid")
    elif kind == "flow-policy":
        choice("ordering", ORDERING_VALUES)
        choice("reliability", RELIABILITY_VALUES)
        choice("overflow", OVERFLOW_POLICIES)
        for field, low, high in (("deadlineMs", 0, 600_000), ("retry", 0, 64), ("queueDepth", 1, 65_536)):
            integer(policy[field], field, low, high)
        identifiers(policy["observationPoints"], "observationPoints")
    elif kind == "network-provider":
        identifiers(policy["requiredCapabilities"], "requiredCapabilities", nonempty=True)
        choice("fidelity", ("exact", "bounded", "declared"))
        limitations = policy["limitations"]
        if (not isinstance(limitations, (list, tuple)) or len(set(map(str, limitations))) != len(limitations)
                or any(not isinstance(item, str) or not 1 <= len(item) <= 200 for item in limitations)):
            raise XcomPlanError(ERROR_PROFILE, "profile policy limitations are invalid")
    elif kind == "observation-policy":
        identifiers(policy["filters"], "filters")
        choice("payloadAccess", PAYLOAD_ACCESS_VALUES)
        choice("validityEffect", VALIDITY_EFFECT_VALUES)
        if "allowList" in policy:
            identifiers(policy["allowList"], "allowList", nonempty=True)
        elif policy["payloadAccess"] == "allow-listed":
            raise XcomPlanError(ERROR_PROFILE, "allow-listed observation requires allowList")
        bounds = policy["bounds"]
        if not isinstance(bounds, Mapping) or set(bounds) != {"maxPayloadBytes", "maxRateHz"}:
            raise XcomPlanError(ERROR_PROFILE, "observation bounds are invalid")
        integer(bounds["maxPayloadBytes"], "maxPayloadBytes", 0, 1_048_576)
        integer(bounds["maxRateHz"], "maxRateHz", 0, 100_000)
    else:
        identifiers(policy["allowedActions"], "allowedActions", nonempty=True)
        identifiers(policy["injectionPoints"], "injectionPoints")
        if not isinstance(policy["serviceEmulation"], bool):
            raise XcomPlanError(ERROR_PROFILE, "serviceEmulation must be boolean")
        choice("timePolicy", ("local-validation-clock", "unmapped"))
        quotas = policy["quotas"]
        if not isinstance(quotas, Mapping) or set(quotas) != {"maxActions", "maxRateHz"}:
            raise XcomPlanError(ERROR_PROFILE, "validation quotas are invalid")
        integer(quotas["maxActions"], "maxActions", 0, 100_000)
        integer(quotas["maxRateHz"], "maxRateHz", 0, 100_000)
        if "permitPolicyRef" in policy:
            _plan_id(policy["permitPolicyRef"], ERROR_PROFILE, "permitPolicyRef")
        elif policy["serviceEmulation"]:
            raise XcomPlanError(ERROR_POLICY, "service emulation requires a permit-policy reference")
        else:
            raise XcomPlanError(ERROR_PROFILE, "validation policy is missing permitPolicyRef")


def _validate_payload(value: Any) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    """Validate a payload against the closed Profile v0.1 grammar and return (target, policy)."""

    if not isinstance(value, Mapping):
        raise XcomPlanError(ERROR_PROFILE, "profile payload must be an object")
    unknown = set(value) - set(PAYLOAD_MEMBERS)
    if unknown:
        raise XcomPlanError(ERROR_PROFILE, "profile payload carries an unknown member")
    if value.get("schemaVersion") != "0.1":
        raise XcomPlanError(ERROR_PROFILE, "profile payload schemaVersion must be 0.1")
    kind = value.get("kind")
    if kind not in INTERFACE_KINDS:
        raise XcomPlanError(ERROR_PROFILE, "profile payload kind is not a declared form")
    target = value.get("target")
    if not isinstance(target, Mapping):
        raise XcomPlanError(ERROR_PROFILE, "profile payload target must be an object")
    if set(target) - set(TARGET_MEMBERS):
        raise XcomPlanError(ERROR_PROFILE, "profile payload target carries an unknown member")
    if any(member not in target for member in TARGET_REQUIRED):
        raise XcomPlanError(ERROR_PROFILE, "profile payload target is missing a required member")
    if target.get("apiVersion") != API_VERSION:
        raise XcomPlanError(ERROR_PROFILE, "profile payload target apiVersion is not admitted")
    if target.get("kind") not in TARGET_KINDS:
        raise XcomPlanError(ERROR_PROFILE, "profile payload target kind is not a legal decorated kind")
    if not isinstance(target.get("namespace"), str) or not isinstance(target.get("name"), str):
        raise XcomPlanError(ERROR_PROFILE, "profile payload target identity members must be strings")
    _plan_id(target["namespace"], ERROR_PROFILE, "target namespace")
    _plan_id(target["name"], ERROR_PROFILE, "target name")
    if "version" in target and (
        not isinstance(target["version"], str) or not VERSION_PATTERN.fullmatch(target["version"])
    ):
        raise XcomPlanError(ERROR_PROFILE, "profile payload target version is invalid")
    policy = value.get("policy")
    if not isinstance(policy, Mapping):
        raise XcomPlanError(ERROR_PROFILE, "profile payload policy must be an object")
    unknown_policy = set(policy) - set(PROFILE_FORM_PERMITTED[kind])
    if unknown_policy:
        raise XcomPlanError(ERROR_PROFILE, "profile payload policy is not the declared form for its kind")
    _validate_policy_values(kind, policy)
    return target, policy


def _parse_pointer(
    pointer: Any, resource: Mapping[str, Any]
) -> tuple[str, int | None, str | None]:
    """Resolve an attachment pointer to ``(collection, index, element_id)``."""

    if not isinstance(pointer, str):
        raise XcomPlanError(ERROR_PROFILE, "profile payload pointer must be a string")
    tokens = pointer.split("/")
    if len(tokens) < 3 or tokens[-1] != PROFILE_NAMESPACE or tokens[-2] != "extensions":
        raise XcomPlanError(ERROR_PROFILE, "profile payload pointer is not an admitted extension location")
    parent = tokens[1:-2]
    if not parent:
        return "", None, None
    if len(parent) == 3 and parent[0] == "spec" and parent[2].isdigit():
        collection = parent[1]
        index = int(parent[2])
        values = _spec(resource).get(collection)
        if not isinstance(values, (list, tuple)) or index >= len(values):
            raise XcomPlanError(ERROR_PROFILE, "profile payload pointer does not resolve to a declared element")
        item = values[index]
        if not isinstance(item, Mapping) or not isinstance(item.get("id"), str):
            raise XcomPlanError(ERROR_PROFILE, "profile payload pointer element has no identifier")
        return collection, index, item["id"]
    raise XcomPlanError(ERROR_PROFILE, "profile payload pointer is not an admitted extension location")


def _resource_level_legal(kind: str, resource: Mapping[str, Any]) -> None:
    """Reject a resource-level payload that is not legal for its kind and resource."""

    resource_kind = resource["identity"]["kind"]
    if kind == "interface-policy":
        if len(_content_list(resource, "interfaces")) != 1:
            raise XcomPlanError(
                ERROR_PROFILE, "resource-level interface-policy requires exactly one interface"
            )
        return
    if kind == "network-provider":
        if resource_kind != "Deployment":
            raise XcomPlanError(ERROR_PROFILE, "resource-level network-provider requires a Deployment")
        return
    if kind in ("observation-policy", "validation-policy"):
        if resource_kind != "Scenario":
            raise XcomPlanError(
                ERROR_PROFILE, f"resource-level {kind} requires a Scenario"
            )
        return
    # flow-policy: any legal-target resource (System cannot be a payload target).
    if resource_kind not in TARGET_KINDS:
        raise XcomPlanError(ERROR_PROFILE, "resource-level flow-policy requires a legal-target resource")


def _target_matches(target: Mapping[str, Any], resource: Mapping[str, Any]) -> bool:
    """Return whether a payload target names its attachment resource exactly."""

    identity = resource["identity"]
    if target.get("apiVersion") != identity["apiVersion"]:
        return False
    if target.get("kind") != identity["kind"]:
        return False
    if target.get("namespace") != identity["namespace"]:
        return False
    if target.get("name") != identity["name"]:
        return False
    if "version" in target and target.get("version") != resource.get("revision"):
        return False
    return True


def _index_profiles(
    resources: tuple[Mapping[str, Any], ...], state: "_State"
) -> tuple[_ProfileRecord, ...]:
    """Index, validate, and order every applied ``io.xverse.xcom`` Profile payload."""

    records: list[_ProfileRecord] = []
    seen: set[tuple[Any, ...]] = set()
    for resource in resources:
        resource_key = _resource_key(resource)
        extensions = resource.get("extensions")
        if not isinstance(extensions, Mapping):
            continue
        entry = extensions.get(PROFILE_NAMESPACE)
        if not isinstance(entry, Mapping):
            continue
        payloads = entry.get("payloads")
        if not isinstance(payloads, (list, tuple)):
            continue
        for payload_record in payloads:
            if not isinstance(payload_record, Mapping):
                raise XcomPlanError(ERROR_PROFILE, "profile payload record must be an object")
            pointer = payload_record.get("pointer")
            collection, _index, element_id = _parse_pointer(pointer, resource)
            target, policy = _validate_payload(payload_record.get("value"))
            kind = str(payload_record["value"]["kind"])
            if collection:
                if collection not in PROFILE_FORM_COLLECTIONS[kind]:
                    raise XcomPlanError(ERROR_PROFILE, "profile payload is attached at an illegal collection")
            else:
                _resource_level_legal(kind, resource)
            if not _target_matches(target, resource):
                state.identity_unresolved.append(str(resource["identity"]["name"]))
                continue
            key = (resource_key, kind, collection, element_id)
            if key in seen:
                raise XcomPlanError(ERROR_PROFILE, "duplicate profile payload for one decorated identity")
            seen.add(key)
            records.append(
                _ProfileRecord(
                    resource_key=resource_key,
                    kind=kind,
                    collection=collection,
                    element_id=element_id,
                    pointer=str(pointer),
                    target=target,
                    policy=policy,
                )
            )
    records.sort(key=lambda record: record.sort_key)
    return tuple(records)


# --------------------------------------------------------------------------------------
# Shared derivation state
# --------------------------------------------------------------------------------------


@dataclass
class _State:
    """Mutable derivation accumulators (internal to one pure compilation)."""

    identity_unresolved: list[str] = field(default_factory=list)
    capability_unresolved: list[str] = field(default_factory=list)
    policy_issues: list[tuple[str, str]] = field(default_factory=list)


# --------------------------------------------------------------------------------------
# T018-U-03 Scope, contracts, endpoints, routes, providers
# --------------------------------------------------------------------------------------


def _select_system(resources: tuple[Mapping[str, Any], ...]) -> Mapping[str, Any]:
    systems = [resource for resource in resources if resource["identity"]["kind"] == "System"]
    if len(systems) != 1:
        raise XcomPlanError(ERROR_IDENTITY, "exactly one System resource is required")
    return systems[0]


def _system_ref_matches(resource: Mapping[str, Any], system: Mapping[str, Any]) -> bool:
    reference = _spec(resource).get("systemRef")
    if not isinstance(reference, Mapping):
        return False
    identity = system["identity"]
    return (
        reference.get("apiVersion") == identity["apiVersion"]
        and reference.get("kind") == "System"
        and reference.get("namespace") == identity["namespace"]
        and reference.get("name") == identity["name"]
    )


def _select_related(
    resources: tuple[Mapping[str, Any], ...], system: Mapping[str, Any], kind: str
) -> Mapping[str, Any] | None:
    candidates = [
        resource
        for resource in resources
        if resource["identity"]["kind"] == kind and _system_ref_matches(resource, system)
    ]
    if len(candidates) > 1:
        raise XcomPlanError(ERROR_IDENTITY, f"at most one {kind} in System scope is supported")
    return candidates[0] if candidates else None


def _reachable_components(
    resources: tuple[Mapping[str, Any], ...], system: Mapping[str, Any], state: _State
) -> tuple[Mapping[str, Any], ...]:
    by_key = {_resource_key(resource): resource for resource in resources}
    reachable: list[Mapping[str, Any]] = []
    for instance in _content_list(system, "componentInstances"):
        if not isinstance(instance, Mapping):
            continue
        reference = instance.get("componentRef")
        if not isinstance(reference, Mapping):
            continue
        key = (
            str(reference.get("apiVersion", "")),
            str(reference.get("kind", "")),
            str(reference.get("namespace", "")),
            str(reference.get("name", "")),
        )
        resource = by_key.get(key)
        if resource is None or resource["identity"]["kind"] != "Component":
            state.identity_unresolved.append(str(reference.get("name", "")))
            continue
        if _resource_key(resource) not in {_resource_key(item) for item in reachable}:
            reachable.append(resource)
    return tuple(reachable)


def _derive_contracts(
    index: tuple[_ProfileRecord, ...],
    system: Mapping[str, Any],
    reachable: tuple[Mapping[str, Any], ...],
) -> list[dict[str, Any]]:
    by_key = {_resource_key(resource): resource for resource in reachable}
    in_scope = {_resource_key(system)} | set(by_key)
    result: dict[str, dict[str, Any]] = {}
    for record in index:
        if record.kind != "interface-policy" or record.resource_key not in in_scope:
            continue
        resource = by_key.get(record.resource_key) or system
        if record.collection:
            contract_id = record.element_id
        else:
            interfaces = _content_list(resource, "interfaces")
            contract_id = str(interfaces[0]["id"])
        contract_id = _plan_id(contract_id, ERROR_INPUT, "contract id")
        schema_id = record.policy.get("schemaId")
        schema_version = record.policy.get("schemaVersion")
        if not isinstance(schema_id, str) or not _PLAN_IDENTIFIER.match(schema_id):
            raise XcomPlanError(ERROR_CONTRACT, "interface-policy cannot yield a valid contract schemaId")
        if not isinstance(schema_version, str) or not VERSION_PATTERN.match(schema_version):
            raise XcomPlanError(ERROR_CONTRACT, "interface-policy cannot yield a valid contract schemaVersion")
        if contract_id in result:
            raise XcomPlanError(ERROR_DUPLICATE, "two interfaces yield one contract id")
        result[contract_id] = {
            "contractId": contract_id,
            "schemaId": schema_id,
            "schemaVersion": schema_version,
        }
    return [result[key] for key in sorted(result)]


def _derive_endpoints(system: Mapping[str, Any]) -> list[dict[str, Any]]:
    flows = _content_list(system, "flows")
    sources = {
        flow.get("sourceEndpointId") for flow in flows if isinstance(flow, Mapping)
    }
    destinations: set[Any] = set()
    for flow in flows:
        if not isinstance(flow, Mapping):
            continue
        for destination in flow.get("destinationEndpointIds") or ():
            destinations.add(destination)
    result: dict[str, str] = {}
    for endpoint in _content_list(system, "endpoints"):
        if not isinstance(endpoint, Mapping):
            raise XcomPlanError(ERROR_IDENTITY, "System endpoint entry must be an object")
        endpoint_id = _plan_id(endpoint.get("id"), ERROR_INPUT, "endpoint id")
        is_source = endpoint_id in sources
        is_destination = endpoint_id in destinations
        if is_source and is_destination:
            raise XcomPlanError(ERROR_IDENTITY, "endpoint carries conflicting derived roles")
        if is_source:
            role = "initiator"
        elif is_destination:
            role = "responder"
        else:
            direction = endpoint.get("direction")
            if direction == "output":
                role = "initiator"
            elif direction == "input":
                role = "responder"
            else:
                raise XcomPlanError(ERROR_IDENTITY, "endpoint role is ambiguous and is not guessed")
        if endpoint_id in result:
            raise XcomPlanError(ERROR_DUPLICATE, "System carries a duplicate endpoint id")
        result[endpoint_id] = role
    return [{"endpointId": key, "role": result[key]} for key in sorted(result)]


def _derive_routes(
    system: Mapping[str, Any], endpoints: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    endpoint_ids = {endpoint["endpointId"] for endpoint in endpoints}
    result: dict[str, dict[str, Any]] = {}
    for flow in _content_list(system, "flows"):
        if not isinstance(flow, Mapping):
            raise XcomPlanError(ERROR_IDENTITY, "System flow entry must be an object")
        route_id = _plan_id(flow.get("id"), ERROR_INPUT, "route id")
        destinations = flow.get("destinationEndpointIds") or ()
        if len(list(destinations)) != 1:
            raise XcomPlanError(ERROR_IDENTITY, "a flow must declare exactly one destination endpoint")
        source = flow.get("sourceEndpointId")
        destination = list(destinations)[0]
        if source not in endpoint_ids or destination not in endpoint_ids:
            raise XcomPlanError(ERROR_IDENTITY, "a route names an undeclared endpoint")
        contract_id = _plan_id(flow.get("interfaceId"), ERROR_INPUT, "route contract id")
        if route_id in endpoint_ids:
            raise XcomPlanError(ERROR_DUPLICATE, "a route id collides with an endpoint id")
        if route_id in result:
            raise XcomPlanError(ERROR_DUPLICATE, "System carries a duplicate route id")
        result[route_id] = {
            "routeId": route_id,
            "from": str(source),
            "to": str(destination),
            "contractId": contract_id,
        }
    return [result[key] for key in sorted(result)]


def _derive_providers(
    index: tuple[_ProfileRecord, ...],
    deployment: Mapping[str, Any] | None,
    state: _State,
) -> list[dict[str, Any]]:
    if deployment is None:
        return []
    deployment_key = _resource_key(deployment)
    targets = {
        str(target["id"]): target
        for target in _content_list(deployment, "targets")
        if isinstance(target, Mapping) and isinstance(target.get("id"), str)
    }
    all_capabilities = sorted(
        {str(capability) for target in targets.values() for capability in target.get("capabilities") or ()}
    )
    result: dict[str, dict[str, Any]] = {}
    for record in index:
        if record.kind != "network-provider" or record.resource_key != deployment_key:
            continue
        if record.collection == "targets" and record.element_id is not None:
            provider_id = _plan_id(record.element_id, ERROR_INPUT, "provider id")
            declared = sorted(
                {str(capability) for capability in targets.get(provider_id, {}).get("capabilities") or ()}
            )
        elif record.collection and record.element_id is not None:
            provider_id = _plan_id(record.element_id, ERROR_INPUT, "provider id")
            declared = list(all_capabilities)
        else:
            provider_id = _plan_id(deployment["identity"]["name"], ERROR_INPUT, "provider id")
            declared = list(all_capabilities)
        required = sorted({_plan_id(item, ERROR_INPUT, "required capability") for item in record.policy.get("requiredCapabilities") or ()})
        if provider_id in result:
            raise XcomPlanError(ERROR_DUPLICATE, "duplicate provider id")
        if not declared:
            # The accepted plan schema requires at least one declared capability, so a provider
            # with none cannot be represented; record an unresolved capability input (fail closed).
            state.capability_unresolved.append(provider_id)
            continue
        result[provider_id] = {
            "providerId": provider_id,
            "capabilities": declared,
            "requiredCapabilities": required,
        }
    return [result[key] for key in sorted(result)]


# --------------------------------------------------------------------------------------
# T018-U-04 Policies, observation, stimulation, clocks, activation order
# --------------------------------------------------------------------------------------


def _least_value(field_name: str, declared: list[Any]) -> Any:
    if field_name in ("ordering", "reliability", "overflow"):
        order = {
            "ordering": ORDERING_VALUES,
            "reliability": RELIABILITY_VALUES,
            "overflow": OVERFLOW_POLICIES,
        }[field_name]
        return min(declared, key=lambda value: order.index(value) if value in order else len(order))
    return min(declared)


def _map_backpressure(overflow: Any) -> str:
    if overflow == "lossless-backpressure":
        return "lossless-backpressure"
    if overflow == "fail-closed":
        return "fail-closed"
    return "reject"


def _derive_policies(
    index: tuple[_ProfileRecord, ...],
    in_scope_keys: set[tuple[str, str, str, str]],
    routes: list[dict[str, Any]],
    state: _State,
) -> dict[str, Any]:
    sources = [
        record.policy
        for record in index
        if record.kind == "flow-policy" and record.resource_key in in_scope_keys
    ]
    target = min((route["routeId"] for route in routes), default=PLAN_TARGET)
    values: dict[str, Any] = {}
    resolved = True
    for field_name in POLICY_FIELDS:
        declared = [source[field_name] for source in sources if field_name in source]
        if not declared:
            values[field_name] = PLACEHOLDER_POLICY[field_name]
            state.policy_issues.append(("XCOM-PLAN-POLICY-UNRESOLVED", target))
            resolved = False
        elif len(set(declared)) == 1:
            values[field_name] = declared[0]
        else:
            values[field_name] = _least_value(field_name, declared)
            state.policy_issues.append(("XCOM-PLAN-POLICY-CONFLICT", target))
            resolved = False
    if not resolved:
        return dict(PLACEHOLDER_POLICY)
    return {
        "ordering": values["ordering"],
        "reliability": values["reliability"],
        "deadlineMs": values["deadlineMs"],
        "retry": values["retry"],
        "queueDepth": values["queueDepth"],
        "overflow": values["overflow"],
        "backpressure": _map_backpressure(values["overflow"]),
    }


def _observation_policy_for(
    index: tuple[_ProfileRecord, ...],
    scenario: Mapping[str, Any],
    tap_id: str,
) -> _ProfileRecord | None:
    scenario_key = _resource_key(scenario)
    for record in index:
        if (
            record.kind == "observation-policy"
            and record.resource_key == scenario_key
            and record.collection == "observers"
            and record.element_id == tap_id
        ):
            return record
    return None


def _derive_observation_points(
    index: tuple[_ProfileRecord, ...],
    scenario: Mapping[str, Any] | None,
    routes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if scenario is None:
        return []
    route_ids = {route["routeId"] for route in routes}
    result: dict[str, dict[str, Any]] = {}
    for observer in _content_list(scenario, "observers"):
        if not isinstance(observer, Mapping):
            raise XcomPlanError(ERROR_IDENTITY, "Scenario observer entry must be an object")
        tap_id = _plan_id(observer.get("id"), ERROR_INPUT, "observation tap id")
        target_ref = observer.get("targetRef")
        if not isinstance(target_ref, Mapping) or target_ref.get("kind") != "System":
            raise XcomPlanError(ERROR_IDENTITY, "Scenario observer target must be a System element")
        if target_ref.get("element") not in route_ids:
            raise XcomPlanError(ERROR_IDENTITY, "Scenario observer target is not a declared route")
        payload_access = "metadata-only"
        validity_effect = "none"
        policy_record = _observation_policy_for(index, scenario, tap_id)
        if policy_record is not None:
            declared_access = policy_record.policy.get("payloadAccess")
            declared_effect = policy_record.policy.get("validityEffect")
            if declared_access in PAYLOAD_ACCESS_VALUES:
                payload_access = declared_access
            if declared_effect in VALIDITY_EFFECT_VALUES:
                validity_effect = declared_effect
        if tap_id in result:
            raise XcomPlanError(ERROR_DUPLICATE, "duplicate observation tap id")
        result[tap_id] = {
            "tapId": tap_id,
            "routeId": str(target_ref["element"]),
            "payloadAccess": payload_access,
            "validityEffect": validity_effect,
        }
    return [result[key] for key in sorted(result)]


def _derive_stimulation(
    index: tuple[_ProfileRecord, ...], scenario: Mapping[str, Any] | None
) -> dict[str, Any]:
    if scenario is None:
        return {"actions": [], "permitPolicyRefs": []}
    scenario_key = _resource_key(scenario)
    actions: set[str] = set()
    permits: set[str] = set()
    for record in index:
        if record.kind != "validation-policy" or record.resource_key != scenario_key:
            continue
        policy = record.policy
        if policy.get("serviceEmulation") is True and not policy.get("permitPolicyRef"):
            raise XcomPlanError(ERROR_POLICY, "service emulation requires a permit-policy reference")
        for action in policy.get("allowedActions") or ():
            actions.add(_plan_id(action, ERROR_POLICY, "stimulation action"))
        permit = policy.get("permitPolicyRef")
        if permit is not None:
            permits.add(_plan_id(permit, ERROR_POLICY, "stimulation permit reference"))
    return {"actions": sorted(actions), "permitPolicyRefs": sorted(permits)}


def _derive_clock_domains(
    system: Mapping[str, Any],
    index: tuple[_ProfileRecord, ...],
    scenario: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    domains = [
        domain
        for domain in _content_list(system, "timeDomains")
        if isinstance(domain, Mapping) and isinstance(domain.get("id"), str)
    ]
    referenced = min((str(domain["id"]) for domain in domains), default=None)
    time_policy: str | None = None
    if scenario is not None:
        scenario_key = _resource_key(scenario)
        for record in index:
            if record.kind == "validation-policy" and record.resource_key == scenario_key:
                candidate = record.policy.get("timePolicy")
                if candidate == "local-validation-clock":
                    time_policy = candidate
    result: dict[str, str] = {}
    for domain in domains:
        clock_domain_id = _plan_id(domain.get("id"), ERROR_INPUT, "clock domain id")
        if time_policy == "local-validation-clock" and clock_domain_id == referenced:
            source = "local-validation-clock"
        elif domain.get("monotonic") is True:
            source = "monotonic"
        else:
            source = "unmapped"
        if clock_domain_id in result:
            raise XcomPlanError(ERROR_DUPLICATE, "duplicate clock domain id")
        result[clock_domain_id] = source
    return [{"clockDomainId": key, "source": result[key]} for key in sorted(result)]


def _derive_activation_order(
    endpoints: list[dict[str, Any]], routes: list[dict[str, Any]]
) -> list[str]:
    """Return sorted endpoint ids followed by sorted route ids, each named exactly once."""

    order: list[str] = []
    for value in [endpoint["endpointId"] for endpoint in endpoints] + [route["routeId"] for route in routes]:
        if value not in order:
            order.append(value)
    if not order:
        raise XcomPlanError(ERROR_IDENTITY, "activation order must name at least one endpoint or route")
    return order


# --------------------------------------------------------------------------------------
# T018-U-06 Input resolution, diagnostics, status
# --------------------------------------------------------------------------------------


def _system_element_ids(system: Mapping[str, Any]) -> set[str]:
    elements: set[str] = set()
    for collection in ("nodes", "componentInstances", "devices"):
        for item in _content_list(system, collection):
            if isinstance(item, Mapping) and isinstance(item.get("id"), str):
                elements.add(item["id"])
    return elements


def _resolve(
    state: _State,
    system: Mapping[str, Any],
    deployment: Mapping[str, Any] | None,
    endpoints: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    providers: list[dict[str, Any]],
    clock_domains: list[dict[str, Any]],
) -> tuple[dict[str, str], list[tuple[str, str]]]:
    """Return the six input-resolution states and the unresolved diagnostics."""

    diagnostics: list[tuple[str, str]] = []
    identity = "resolved" if not state.identity_unresolved else "unresolved"
    for name in dict.fromkeys(state.identity_unresolved):
        diagnostics.append(("XCOM-PLAN-IDENTITY-UNRESOLVED", _safe_target(name)))

    contract_ids = {contract["contractId"] for contract in contracts}
    schema = "resolved"
    for route in routes:
        if route["contractId"] not in contract_ids:
            schema = "unresolved"
            diagnostics.append(("XCOM-PLAN-SCHEMA-UNRESOLVED", route["routeId"]))

    capability = "resolved"
    if routes and not providers:
        capability = "unresolved"
        diagnostics.append(("XCOM-PLAN-CAPABILITY-UNRESOLVED", PLAN_TARGET))
    for provider_id in dict.fromkeys(state.capability_unresolved):
        capability = "unresolved"
        diagnostics.append(("XCOM-PLAN-CAPABILITY-UNRESOLVED", _safe_target(provider_id)))
    for provider in providers:
        if not set(provider["requiredCapabilities"]) <= set(provider["capabilities"]):
            capability = "unresolved"
            diagnostics.append(("XCOM-PLAN-CAPABILITY-UNRESOLVED", provider["providerId"]))

    time = "resolved"
    if not clock_domains:
        time = "unresolved"
        diagnostics.append(("XCOM-PLAN-TIME-UNRESOLVED", PLAN_TARGET))
    for domain in clock_domains:
        if domain["source"] == "unmapped":
            time = "unresolved"
            diagnostics.append(("XCOM-PLAN-TIME-UNRESOLVED", domain["clockDomainId"]))

    ownership = "resolved"
    if deployment is None:
        ownership = "unresolved"
        diagnostics.append(("XCOM-PLAN-OWNERSHIP-UNRESOLVED", PLAN_TARGET))
    else:
        declared_elements = _system_element_ids(system)
        bindings: dict[str, int] = {}
        for binding in _content_list(deployment, "bindings"):
            logical_ref = binding.get("logicalRef") if isinstance(binding, Mapping) else None
            if isinstance(logical_ref, Mapping) and isinstance(logical_ref.get("element"), str):
                element = logical_ref["element"]
                bindings[element] = bindings.get(element, 0) + 1
        for binding_element, count in bindings.items():
            if count > 1:
                ownership = "unresolved"
                diagnostics.append(("XCOM-PLAN-OWNERSHIP-UNRESOLVED", _safe_target(binding_element)))
        for endpoint in endpoints:
            owner = _owner_of(system, endpoint["endpointId"])
            if owner is None or owner not in declared_elements:
                ownership = "unresolved"
                diagnostics.append(("XCOM-PLAN-OWNERSHIP-UNRESOLVED", endpoint["endpointId"]))

    policy = "resolved"
    for code, target in state.policy_issues:
        policy = "unresolved"
        diagnostics.append((code, target))

    resolution = {
        "identity": identity,
        "schema": schema,
        "capability": capability,
        "time": time,
        "ownership": ownership,
        "policy": policy,
    }
    return resolution, diagnostics


def _owner_of(system: Mapping[str, Any], endpoint_id: str) -> str | None:
    for endpoint in _content_list(system, "endpoints"):
        if isinstance(endpoint, Mapping) and endpoint.get("id") == endpoint_id:
            owner = endpoint.get("ownerId")
            return owner if isinstance(owner, str) else None
    return None


def _safe_target(value: str) -> str:
    """Return *value* when it is a plan identifier, otherwise the fixed plan target."""

    if isinstance(value, str) and _PLAN_IDENTIFIER.match(value) and len(value) <= PLAN_IDENTIFIER_MAX_LENGTH:
        return value
    return PLAN_TARGET


def _build_diagnostics(
    diagnostics: list[tuple[str, str]], limits: CompileLimits
) -> list[dict[str, str]]:
    unique: dict[tuple[str, str], None] = {}
    for code, target in diagnostics:
        unique[(code, _safe_target(target))] = None
    ordered = sorted(unique)
    if len(ordered) > limits.max_diagnostics:
        raise XcomPlanError(ERROR_BOUND, "compiled diagnostic count exceeds max_diagnostics")
    return [{"code": code, "severity": "error", "targetId": target} for code, target in ordered]


# --------------------------------------------------------------------------------------
# T018-U-05 Canonicalization, digest, and provenance
# --------------------------------------------------------------------------------------


def _normalize_numbers(value: Any, path: str = "$") -> Any:
    """Emit every mathematically integral number in its single integer form."""

    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise XcomPlanError(ERROR_UNKNOWN, f"non-finite number at {path}")
        if value.is_integer():
            return int(value)
        return value
    if isinstance(value, Mapping):
        return {str(key): _normalize_numbers(child, f"{path}/{key}") for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_numbers(child, f"{path}/{index}") for index, child in enumerate(value)]
    return value


def canonical_plan_bytes(value: Any) -> bytes:
    """Return the byte-stable canonical JSON encoding of *value*."""

    return json.dumps(
        _normalize_numbers(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _canonical_body(plan: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in plan.items() if key != "digest"}


def compute_digest(plan: Mapping[str, Any]) -> str:
    """Return the domain-separated SHA-256 digest over the plan body."""

    body = canonical_plan_bytes(_canonical_body(plan))
    return hashlib.sha256(PLAN_DOMAIN_SEPARATOR + body).hexdigest()


def plan_matches_digest(plan: Mapping[str, Any]) -> bool:
    """Return whether the recorded digest equals the recomputed body digest."""

    digest = plan.get("digest")
    if not isinstance(digest, Mapping) or digest.get("algorithm") != "sha256":
        return False
    value = digest.get("value")
    if not isinstance(value, str) or not DIGEST_HEX_PATTERN.match(value):
        return False
    return value == compute_digest(plan)


def plan_status(plan: Mapping[str, Any]) -> str:
    """Return the closed plan status."""

    return str(plan.get("status"))


def _digest_member(value: bytes) -> dict[str, str]:
    return {"algorithm": "sha256", "value": hashlib.sha256(value).hexdigest()}


def _canonical_resource(resource: Mapping[str, Any]) -> dict[str, Any]:
    """Return a provenance-stable copy of a resource.

    The accepted canonical-serialization contract preserves array order, so a reordered but
    semantically equivalent extension payload list would otherwise change the resource digest.
    The compiler therefore imposes one canonical payload order (by attachment pointer) for the
    provenance digests; the payload values themselves are untouched.
    """

    value = dict(resource)
    extensions = value.get("extensions")
    if isinstance(extensions, Mapping):
        normalized: dict[str, Any] = {}
        for namespace, entry in extensions.items():
            if isinstance(entry, Mapping):
                entry_copy = dict(entry)
                payloads = entry.get("payloads")
                if isinstance(payloads, (list, tuple)):
                    entry_copy["payloads"] = sorted(
                        payloads,
                        key=lambda item: str(item.get("pointer")) if isinstance(item, Mapping) else "",
                    )
                normalized[str(namespace)] = entry_copy
            else:
                normalized[str(namespace)] = entry
        value["extensions"] = normalized
    return value


def _graph_digest(resources: tuple[Mapping[str, Any], ...]) -> dict[str, str]:
    document = {"resources": [_canonical_resource(resource) for resource in resources]}
    return _digest_member(GRAPH_DOMAIN_SEPARATOR + canonical_plan_bytes(document))


def _provenance_resources(
    reachable: tuple[Mapping[str, Any], ...],
    deployment: Mapping[str, Any] | None,
    scenario: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    contributing: list[Mapping[str, Any]] = list(reachable)
    if deployment is not None:
        contributing.append(deployment)
    if scenario is not None:
        contributing.append(scenario)
    records: list[dict[str, Any]] = []
    for resource in contributing:
        identity = _identity_of(resource)
        record: dict[str, Any] = {
            "apiVersion": identity["apiVersion"],
            "kind": identity["kind"],
            "namespace": identity["namespace"],
            "name": identity["name"],
        }
        revision = resource.get("revision")
        if isinstance(revision, str) and VERSION_PATTERN.match(revision):
            record["version"] = revision
        record["sourceDigest"] = _digest_member(canonical_plan_bytes(_canonical_resource(resource)))
        records.append(record)
    records.sort(
        key=lambda item: (
            item["apiVersion"],
            item["kind"],
            item["namespace"],
            item["name"],
            item.get("version") or "",
        )
    )
    if not records:
        raise XcomPlanError(ERROR_INPUT, "no Component, Deployment, or Scenario resource contributes")
    return records


# --------------------------------------------------------------------------------------
# T018-U-07/U-08 Compilation, bounds, and failure semantics
# --------------------------------------------------------------------------------------


def _validate_generated_at(generated_at: str | None) -> str:
    if generated_at is None:
        return DEFAULT_GENERATED_AT
    if not isinstance(generated_at, str) or not DATETIME_PATTERN.fullmatch(generated_at):
        raise XcomPlanError(ERROR_INPUT, "generated_at must be an RFC 3339 date-time string")
    try:
        datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise XcomPlanError(ERROR_INPUT, "generated_at is not a real RFC 3339 date-time") from exc
    return generated_at


def _validate_generator_version(generator_version: str) -> str:
    if not isinstance(generator_version, str) or not GENERATOR_VERSION_PATTERN.match(generator_version):
        raise XcomPlanError(ERROR_INPUT, "generator version must be a plain version string")
    return generator_version


def _check_entity_caps(
    limits: CompileLimits,
    endpoints: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    providers: list[dict[str, Any]],
    observation_points: list[dict[str, Any]],
    clock_domains: list[dict[str, Any]],
) -> None:
    checks = (
        (len(endpoints), limits.max_endpoints, "endpoints"),
        (len(routes), limits.max_routes, "routes"),
        (len(providers), limits.max_providers, "providers"),
        (len(observation_points), limits.max_observation_points, "observation points"),
        (len(clock_domains), limits.max_clock_domains, "clock domains"),
    )
    for count, cap, label in checks:
        if count > cap:
            raise XcomPlanError(ERROR_BOUND, f"compiled {label} exceed the declared cap")


def compile_plan(
    graph: Any,
    *,
    generated_at: str | None = None,
    generator_version: str = GENERATOR_VERSION,
    limits: CompileLimits | None = None,
) -> dict[str, Any]:
    """Compile a normalized graph document into a canonical activation-plan v1 value.

    @param graph A ``GraphView``, a ``{"resources": [...]}`` mapping, or a resource sequence.
    @param generated_at An explicit deterministic RFC 3339 timestamp, or the fixed sentinel.
    @param generator_version The generator version recorded in ``generator``.
    @param limits The offline-input and compiled-entity bounds.
    @return A fresh plain ``dict`` plan tree owned by the caller.
    @raises XcomPlanError On a rejected (input/profile/identity/duplicate/contract/policy) or
        failed (bound/unknown) defect; no partial plan is returned.
    """

    active = limits if limits is not None else CompileLimits()
    view = load_normalized_graph(graph, limits=active)
    timestamp = _validate_generated_at(generated_at)
    version = _validate_generator_version(generator_version)

    resources = view.resources
    state = _State()
    system = _select_system(resources)
    deployment = _select_related(resources, system, "Deployment")
    scenario = _select_related(resources, system, "Scenario")
    reachable = _reachable_components(resources, system, state)
    index = _index_profiles(resources, state)

    contracts = _derive_contracts(index, system, reachable)
    endpoints = _derive_endpoints(system)
    routes = _derive_routes(system, endpoints)
    providers = _derive_providers(index, deployment, state)
    in_scope_keys = {_resource_key(system)} | {_resource_key(item) for item in reachable}
    if deployment is not None:
        in_scope_keys.add(_resource_key(deployment))
    if scenario is not None:
        in_scope_keys.add(_resource_key(scenario))
    policies = _derive_policies(index, in_scope_keys, routes, state)
    observation_points = _derive_observation_points(index, scenario, routes)
    stimulation = _derive_stimulation(index, scenario)
    clock_domains = _derive_clock_domains(system, index, scenario)
    activation_order = _derive_activation_order(endpoints, routes)

    _check_entity_caps(active, endpoints, routes, providers, observation_points, clock_domains)

    resolution, raw_diagnostics = _resolve(
        state, system, deployment, endpoints, routes, contracts, providers, clock_domains
    )
    diagnostics = _build_diagnostics(raw_diagnostics, active)

    plan: dict[str, Any] = {
        "planVersion": PLAN_VERSION,
        "generator": {"task": TASK_ID, "version": version},
        "provenance": {
            "generatedAt": timestamp,
            "graphDigest": _graph_digest(resources),
            "resources": _provenance_resources(reachable, deployment, scenario),
        },
        "contracts": contracts,
        "endpoints": endpoints,
        "routes": routes,
        "providers": providers,
        "policies": policies,
        "observationPoints": observation_points,
        "stimulation": stimulation,
        "clockDomains": clock_domains,
        "activationOrder": activation_order,
        "diagnostics": diagnostics,
        "status": "activatable" if all(value == "resolved" for value in resolution.values()) else "inspectable",
        "inputResolution": resolution,
    }
    plan["digest"] = {"algorithm": "sha256", "value": compute_digest(plan)}
    if not plan_matches_digest(plan):
        raise XcomPlanError(ERROR_UNKNOWN, "compiled plan digest self-check failed")
    return plan
