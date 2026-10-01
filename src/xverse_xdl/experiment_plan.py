"""Pure, offline resolved-experiment-plan compiler (XDL Lite Phase 1, feature XDL1).

This module compiles an already normalized and validated XDL v1alpha1 resource set plus the
explicitly admitted ``io.xverse.experiment`` Profile payloads into one canonical *resolved
experiment plan* v1 value, or rejects the input with stable structured diagnostics and no plan.

The compiler is a pure, offline, bounded function library:

* it reads only in-memory :class:`~xverse_xdl.models.NormalizedResource` values;
* it opens no file, starts no process or thread, opens no socket, and performs no registry or
  network access;
* it reads no ambient clock, locale, environment variable, user or working directory;
* semantically equivalent declared intent (any YAML/JSON encoding, any input or payload order)
  yields byte-identical canonical plan bytes and the same domain-separated plan digest, while
  resource byte hashes and volatile run data stay outside the plan body.

It defines no competing configuration language and no execution: the plan records declared
intent validation only. The frozen contract it realizes is
``docs/engineering/xdl-lite/detailed-design.md``.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from fractions import Fraction
from typing import Any

from .diagnostics import diagnostic_to_data, make_diagnostic
from .models import (
    Diagnostic, FrozenMap, LoadLimits, NormalizedResource, ResourceIdentity, Severity,
    StaticReadiness, ValidationGate, freeze,
)
from .normalize import canonical_json
from .validate import validate_files, validate_sources

__all__ = [
    "DEFAULT_GENERATED_AT",
    "DIAGNOSTIC_CODES",
    "ExperimentLimits",
    "ExperimentPlanResult",
    "GENERATOR_TASK",
    "GENERATOR_VERSION",
    "INPUT_DOMAIN_SEPARATOR",
    "PAYLOAD_KINDS",
    "PHASE_ORDER",
    "PLAN_DOMAIN_SEPARATOR",
    "PLAN_STATUS",
    "PLAN_VERSION",
    "PROFILE_NAMESPACE",
    "PROFILE_RESOURCE_VERSION",
    "PROFILE_SCHEMA_ID",
    "PROFILE_SCHEMA_VERSION",
    "RESOURCE_DOMAIN_SEPARATOR",
    "SUPPORTED_REALIZATION_CLASSES",
    "TIME_UNIT_TICKS",
    "TRIGGER_KIND_ORDER",
    "canonical_plan_bytes",
    "compile_experiment_files",
    "compile_experiment_plan",
    "compile_experiment_sources",
    "compute_plan_digest",
    "experiment_plan_status",
    "plan_matches_digest",
    "plan_public_data",
    "resource_semantic_digest",
]

# --------------------------------------------------------------------------------------
# Frozen identities, vocabulary and domain separators (detailed-design.md sections 3, 10)
# --------------------------------------------------------------------------------------

API_VERSION = "xverse.io/xdl/v1alpha1"
PROFILE_NAMESPACE = "io.xverse.experiment"
PROFILE_RESOURCE_VERSION = "0.1.0"
PROFILE_SCHEMA_VERSION = "0.1"
PROFILE_SCHEMA_ID = "https://xverse.io/profiles/experiment-lite/v0.1/schema.json"
PLAN_VERSION = "1"
PLAN_STATUS = "resolved"
GENERATOR_TASK = "XDL1"
GENERATOR_VERSION = "0.1.0"
DEFAULT_GENERATED_AT = "1970-01-01T00:00:00Z"

PLAN_DOMAIN_SEPARATOR = b"xverse.xdl.experiment-plan.v1\x00"
RESOURCE_DOMAIN_SEPARATOR = b"xverse.xdl.experiment-resource.v1\x00"
INPUT_DOMAIN_SEPARATOR = b"xverse.xdl.experiment-input.v1\x00"

TIME_UNIT_TICKS = {"tick": 1, "ns": 1, "us": 1000, "ms": 1000000, "s": 1000000000}
PHASE_ORDER = {"prepare": 0, "start": 1, "observe": 2, "stop": 3, "cleanup": 4}
TRIGGER_KIND_ORDER = {"time": 0, "declared-order": 1}
KIND_RANK = {"node": 0, "component-instance": 1, "step": 2}
SUPPORTED_REALIZATION_CLASSES = ("simulated", "virtual", "hybrid")
PAYLOAD_KINDS = ("scenario-intent", "step-intent", "fault-intent", "realization-intent")
EXPECTED_KIND_BY_SURFACE = {
    "scenario-root": "scenario-intent",
    "scenario-step": "step-intent",
    "scenario-fault": "fault-intent",
    "deployment-binding": "realization-intent",
}

NON_READINESS_STATEMENT = (
    "This resolved plan records declared intent validation only; it is not evidence of executable "
    "artifact availability, runtime fitness, live readiness, compatibility, parity, certification, "
    "or execution."
)

RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
DATETIME_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)
DIGEST_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SECRET_ASSIGNMENT = re.compile(r"(?:password|passwd|secret|token|api[_-]?key)\s*[:=]", re.IGNORECASE)
_SECRET_PRIVATE_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE)
_SECRET_URI_USERINFO = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://[^/?#@\s]*@")

# Closed diagnostics catalogue (detailed-design.md section 9); each value is its gate.
DIAGNOSTIC_GATES = {
    "XDL1-PLAN-PROFILE-ABSENT": ValidationGate.POLICY,
    "XDL1-PLAN-PROFILE-DUPLICATE": ValidationGate.POLICY,
    "XDL1-PLAN-PROFILE-VERSION-UNSUPPORTED": ValidationGate.POLICY,
    "XDL1-PLAN-PROFILE-SCHEMAREF-UNSUPPORTED": ValidationGate.POLICY,
    "XDL1-PLAN-PROFILE-PAYLOAD-ABSENT": ValidationGate.POLICY,
    "XDL1-PLAN-PROFILE-PAYLOAD-KIND": ValidationGate.BINDING,
    "XDL1-PLAN-PROFILE-PAYLOAD-DUPLICATE": ValidationGate.POLICY,
    "XDL1-PLAN-PROFILE-TARGET-MISMATCH": ValidationGate.BINDING,
    "XDL1-PLAN-SYSTEM-MISSING": ValidationGate.POLICY,
    "XDL1-PLAN-SYSTEM-AMBIGUOUS": ValidationGate.POLICY,
    "XDL1-PLAN-SCENARIO-MISSING": ValidationGate.POLICY,
    "XDL1-PLAN-SCENARIO-AMBIGUOUS": ValidationGate.POLICY,
    "XDL1-PLAN-DEPLOYMENT-AMBIGUOUS": ValidationGate.POLICY,
    "XDL1-PLAN-DEPLOYMENT-UNBOUND": ValidationGate.BINDING,
    "XDL1-PLAN-SEED-MISSING": ValidationGate.SEMANTIC,
    "XDL1-PLAN-SEED-RANGE": ValidationGate.SEMANTIC,
    "XDL1-PLAN-PARAMETER-DUPLICATE": ValidationGate.SEMANTIC,
    "XDL1-PLAN-PARAMETER-VALUE-TYPE": ValidationGate.SEMANTIC,
    "XDL1-PLAN-PARAMETER-BOUND": ValidationGate.SEMANTIC,
    "XDL1-PLAN-QUANTITY-NONFINITE": ValidationGate.SEMANTIC,
    "XDL1-PLAN-QUANTITY-NEGATIVE": ValidationGate.SEMANTIC,
    "XDL1-PLAN-QUANTITY-OVERFLOW": ValidationGate.SEMANTIC,
    "XDL1-PLAN-TIME-UNIT-UNKNOWN": ValidationGate.SEMANTIC,
    "XDL1-PLAN-TIME-PRECISION": ValidationGate.SEMANTIC,
    "XDL1-PLAN-TIME-DOMAIN-UNRESOLVED": ValidationGate.SEMANTIC,
    "XDL1-PLAN-TIME-MAPPING-MISSING": ValidationGate.BINDING,
    "XDL1-PLAN-FAULT-TRIGGER-MISSING": ValidationGate.SEMANTIC,
    "XDL1-PLAN-FAULT-DURATION-INVALID": ValidationGate.SEMANTIC,
    "XDL1-PLAN-DEPENDENCY-MISSING": ValidationGate.SEMANTIC,
    "XDL1-PLAN-DEPENDENCY-CYCLE": ValidationGate.SEMANTIC,
    "XDL1-PLAN-SCHEDULE-AMBIGUOUS": ValidationGate.SEMANTIC,
    "XDL1-PLAN-BOUND-EXCEEDED": ValidationGate.POLICY,
    "XDL1-PLAN-ARTIFACT-PIN-MISSING": ValidationGate.BINDING,
    "XDL1-PLAN-ARTIFACT-REFERENCE-UNRESOLVED": ValidationGate.BINDING,
    "XDL1-PLAN-REALIZATION-UNSUPPORTED": ValidationGate.POLICY,
    "XDL1-PLAN-DELIVERY-UNSUPPORTED": ValidationGate.BINDING,
    "XDL1-PLAN-RETRY-UNSUPPORTED": ValidationGate.BINDING,
    "XDL1-PLAN-METRIC-LINK-INCOMPLETE": ValidationGate.BINDING,
    "XDL1-PLAN-OBSERVER-UNRESOLVED": ValidationGate.BINDING,
    "XDL1-PLAN-SECRET-IN-PUBLIC-ARTIFACT": ValidationGate.POLICY,
    "XDL1-PLAN-INPUT-MUTATED": ValidationGate.POLICY,
    "XDL1-PLAN-DIGEST-SELFCHECK": ValidationGate.POLICY,
}
DIAGNOSTIC_CODES = tuple(DIAGNOSTIC_GATES)


# --------------------------------------------------------------------------------------
# Bounded library limits (detailed-design.md section 10.2)
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ExperimentLimits:
    """Finite platform library bounds; every field must be a positive number."""

    max_resources: int = 1_000
    max_bytes_per_file: int = 5_242_880
    max_parameters: int = 256
    max_steps: int = 256
    max_faults: int = 256
    max_observers: int = 256
    max_metrics: int = 256
    max_dependencies_per_step: int = 64
    max_flows: int = 1_024
    max_bindings: int = 512
    max_ticks: int = 9_007_199_254_740_991
    max_seed: int = 9_007_199_254_740_991
    max_number_magnitude: float = 1e15
    max_text_length: int = 200
    max_limitations: int = 64
    max_diagnostics: int = 256

    def __post_init__(self) -> None:
        """Reject any non-positive bound that would make bounded compilation ambiguous."""

        for name, value in self.__dict__.items():
            if value <= 0:
                raise ValueError(f"all experiment limits must be positive: {name}")


@dataclass(frozen=True)
class ExperimentPlanResult:
    """Diagnostics, an optional resolved plan, and the volatile run envelope."""

    diagnostics: tuple[Diagnostic, ...]
    plan: dict[str, Any] | None
    run: FrozenMap = field(default_factory=FrozenMap)

    @property
    def is_valid(self) -> bool:
        """Return whether no error diagnostic exists and a plan was emitted."""

        return self.plan is not None and not any(
            item.severity is Severity.ERROR for item in self.diagnostics
        )


# --------------------------------------------------------------------------------------
# Small immutable-structure accessors
# --------------------------------------------------------------------------------------


def _map(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else FrozenMap()


def _seq(value: Any) -> tuple[Any, ...]:
    return tuple(value) if isinstance(value, (list, tuple)) else ()


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _plain(value: Any) -> Any:
    """Return a fresh plain JSON-compatible copy of an immutable normalized value."""

    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(child) for child in value]
    return value


def _identity_data(identity: ResourceIdentity) -> dict[str, str]:
    return {
        "apiVersion": identity.api_version,
        "kind": identity.kind,
        "namespace": identity.namespace,
        "name": identity.name,
        "uri": identity.uri,
    }


def _element_identity(value: Any) -> ResourceIdentity:
    source = _map(value)
    return ResourceIdentity(
        str(source.get("apiVersion", "")), str(source.get("kind", "")),
        str(source.get("namespace", "")), str(source.get("name", "")),
    )


def _element_id(value: Any) -> str | None:
    return _text(_map(value).get("element"))


def _element_ref_data(value: Any) -> dict[str, Any]:
    source = _map(value)
    identity = _element_identity(source)
    entry = _identity_data(identity)
    entry["element"] = _text(source.get("element"))
    return entry


def _spec(resource: NormalizedResource) -> Mapping[str, Any]:
    return _map(resource.content)


def _collection(resource: NormalizedResource, name: str) -> tuple[Mapping[str, Any], ...]:
    return tuple(item for item in _seq(_spec(resource).get(name)) if isinstance(item, Mapping))


def _element_collection(resource: NormalizedResource, element_id: str | None) -> str | None:
    if element_id is None:
        return None
    for collection, group in _map(resource.elements).items():
        if _map(group).get(element_id) is not None:
            return str(collection)
    return None


# --------------------------------------------------------------------------------------
# Diagnostic helpers
# --------------------------------------------------------------------------------------


def _error(
    diagnostics: list[Diagnostic], code: str, message: str, correction: str, *,
    pointer: str = "", resource: ResourceIdentity | None = None, related: Sequence[str] = (),
) -> None:
    diagnostics.append(make_diagnostic(
        code, DIAGNOSTIC_GATES[code], message, correction,
        pointer=pointer, resource=resource, related=related,
    ))


def _ordered(diagnostics: Sequence[Diagnostic], limits: ExperimentLimits) -> tuple[Diagnostic, ...]:
    values = tuple(sorted(diagnostics, key=lambda item: item.sort_key))
    if len(values) > limits.max_diagnostics:
        extra = make_diagnostic(
            "XDL1-PLAN-BOUND-EXCEEDED", DIAGNOSTIC_GATES["XDL1-PLAN-BOUND-EXCEEDED"],
            f"diagnostic count {len(values)} exceeds max_diagnostics {limits.max_diagnostics}",
            "Reduce the number of declared defects in one compile.",
        )
        values = tuple(sorted(values[: limits.max_diagnostics - 1] + (extra,), key=lambda item: item.sort_key))
    return values


# --------------------------------------------------------------------------------------
# Canonical identity helpers (detailed-design.md section 8)
# --------------------------------------------------------------------------------------


def _digest_member(value: bytes) -> dict[str, str]:
    return {"algorithm": "sha256", "value": hashlib.sha256(value).hexdigest()}


def _canonical_resource(resource: NormalizedResource) -> NormalizedResource:
    """Return a provenance-stable copy with extension payloads ordered by pointer.

    The accepted canonical serialization preserves array order, so a reordered but
    semantically equivalent extension payload list would otherwise change the resource
    digest. The declaration order of payload values is preserved; only the attachment
    order is canonicalized.
    """

    groups: dict[str, Any] = {}
    for namespace, entry in _map(resource.extensions).items():
        payloads = tuple(sorted(
            _seq(_map(entry).get("payloads")),
            key=lambda item: str(_map(item).get("pointer")),
        ))
        groups[str(namespace)] = {"profile": _map(entry).get("profile"), "payloads": payloads}
    return replace(resource, extensions=freeze(groups))


def resource_semantic_digest(resource: NormalizedResource) -> str:
    """Return the domain-separated semantic digest of one normalized resource."""

    body = canonical_json(_canonical_resource(resource), include_source_map=False).encode("utf-8")
    return hashlib.sha256(RESOURCE_DOMAIN_SEPARATOR + body).hexdigest()


def _input_semantic_digest(resources: Sequence[NormalizedResource]) -> str:
    canonical = tuple(_canonical_resource(resource) for resource in resources)
    body = canonical_json(canonical, include_source_map=False).encode("utf-8")
    return hashlib.sha256(INPUT_DOMAIN_SEPARATOR + body).hexdigest()


def _normalize_numbers(value: Any) -> Any:
    """Emit every mathematically integral number in its single integer form."""

    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite number in plan body")
        return int(value) if value.is_integer() else value
    if isinstance(value, Mapping):
        return {str(key): _normalize_numbers(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_numbers(child) for child in value]
    return value


def canonical_plan_bytes(plan: Mapping[str, Any]) -> bytes:
    """Return the byte-stable canonical JSON encoding of a plan value."""

    return json.dumps(
        _normalize_numbers(plan), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def _plan_body(plan: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in plan.items() if key != "digest"}


def compute_plan_digest(plan: Mapping[str, Any]) -> str:
    """Return the domain-separated SHA-256 digest over the plan body."""

    return hashlib.sha256(PLAN_DOMAIN_SEPARATOR + canonical_plan_bytes(_plan_body(plan))).hexdigest()


def plan_matches_digest(plan: Mapping[str, Any]) -> bool:
    """Return whether the recorded digest equals the recomputed body digest."""

    digest = plan.get("digest")
    if not isinstance(digest, Mapping) or digest.get("algorithm") != "sha256":
        return False
    value = digest.get("value")
    if not isinstance(value, str) or not DIGEST_HEX_PATTERN.match(value):
        return False
    return value == compute_plan_digest(plan)


def experiment_plan_status(plan: Mapping[str, Any]) -> str:
    """Return the closed plan status."""

    return str(plan.get("status"))


# --------------------------------------------------------------------------------------
# Run envelope
# --------------------------------------------------------------------------------------


def _validate_run_envelope(run_id: str | None, generated_at: str | None) -> None:
    if run_id is not None and (
        not isinstance(run_id, str) or len(run_id) > 128 or not RUN_ID_PATTERN.match(run_id)
    ):
        raise ValueError("run_id must match [A-Za-z0-9][A-Za-z0-9_.-]* and be at most 128 characters")
    if generated_at is not None and (
        not isinstance(generated_at, str) or not DATETIME_PATTERN.match(generated_at)
    ):
        raise ValueError("generated_at must be an explicit RFC 3339 date-time")


def _run_envelope(
    *, run_id: str | None, generated_at: str | None, status: str,
    plan_digest: str | None, source_byte_digests: Mapping[str, str],
) -> FrozenMap:
    return freeze({
        "runId": run_id,
        "generatedAt": generated_at if generated_at is not None else DEFAULT_GENERATED_AT,
        "sourceByteDigests": dict(source_byte_digests),
        "planDigest": plan_digest,
        "status": status,
        "compilerVersion": GENERATOR_VERSION,
    })


def _rejected(
    diagnostics: Sequence[Diagnostic], limits: ExperimentLimits, *,
    run_id: str | None, generated_at: str | None,
    source_byte_digests: Mapping[str, str] | None = None,
) -> ExperimentPlanResult:
    return ExperimentPlanResult(
        _ordered(diagnostics, limits), None,
        _run_envelope(
            run_id=run_id, generated_at=generated_at, status="rejected", plan_digest=None,
            source_byte_digests=source_byte_digests or {},
        ),
    )


# --------------------------------------------------------------------------------------
# Profile payload access
# --------------------------------------------------------------------------------------


def _experiment_payloads(resource: NormalizedResource) -> tuple[tuple[str, Mapping[str, Any]], ...]:
    entry = _map(_map(resource.extensions).get(PROFILE_NAMESPACE))
    result: list[tuple[str, Mapping[str, Any]]] = []
    for item in _seq(entry.get("payloads")):
        payload = _map(item)
        result.append((str(payload.get("pointer", "")), _map(payload.get("value"))))
    return tuple(result)


_ATTACHMENT_PATTERN = re.compile(
    r"^/(?:extensions|spec/(?P<collection>[A-Za-z]+)/(?P<index>[0-9]+)/extensions)/"
    + re.escape(PROFILE_NAMESPACE)
    + r"$"
)
_SURFACES = {"steps": "scenario-step", "faults": "scenario-fault", "bindings": "deployment-binding"}


def _attachment(pointer: str) -> tuple[str, int | None]:
    """Return the attachment surface and element index for one payload pointer."""

    match = _ATTACHMENT_PATTERN.match(pointer)
    if match is None:
        return "unknown", None
    collection = match.group("collection")
    if collection is None:
        return "scenario-root", None
    surface = _SURFACES.get(collection, "unknown")
    return surface, int(match.group("index"))


def _payloads_by_surface(resource: NormalizedResource) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for pointer, payload in _experiment_payloads(resource):
        surface, _index = _attachment(pointer)
        result[surface] = payload
    return result


# --------------------------------------------------------------------------------------
# Compilation
# --------------------------------------------------------------------------------------


def compile_experiment_plan(
    resources: Sequence[NormalizedResource], *,
    static_readiness: Mapping[str, Any] | None = None,
    run_id: str | None = None,
    generated_at: str | None = None,
    expected_input_semantic_digests: Mapping[str, str] | None = None,
    limits: ExperimentLimits | None = None,
) -> ExperimentPlanResult:
    """Compile an immutable normalized resource set into one resolved experiment plan.

    @param resources Immutable normalized XDL resources of the closed input set.
    @param static_readiness Optional accepted declaration-only readiness map.
    @param run_id Optional caller-supplied volatile run identifier.
    @param generated_at Optional explicit RFC 3339 generation time; defaults to the sentinel.
    @param expected_input_semantic_digests Optional caller-pinned resource/input digests.
    @param limits Optional finite library bounds.
    @return An :class:`ExperimentPlanResult`; a declared defect always yields ``plan is None``.
    """

    active = limits if limits is not None else ExperimentLimits()
    _validate_run_envelope(run_id, generated_at)
    entries = tuple(resources)
    if any(not isinstance(entry, NormalizedResource) for entry in entries):
        raise ValueError("resources must be NormalizedResource values")

    diagnostics: list[Diagnostic] = []
    entry_digests: dict[str, str] = {}
    for entry in entries:
        try:
            entry_digests[entry.identity.uri] = resource_semantic_digest(entry)
        except (ValueError, OverflowError):
            # Non-canonical content is rejected by the declared gates before identity is used.
            continue

    def reject() -> ExperimentPlanResult:
        return _rejected(diagnostics, active, run_id=run_id, generated_at=generated_at)

    if len(entries) > active.max_resources:
        _error(
            diagnostics, "XDL1-PLAN-BOUND-EXCEEDED",
            f"{len(entries)} resources exceed max_resources {active.max_resources}",
            "Reduce the closed input set to the declared bound.",
        )
        return reject()

    # S7 -- admitted Profile admission.
    profiles = [
        entry for entry in entries
        if entry.identity.kind == "Profile"
        and _spec(entry).get("extensionNamespace") == PROFILE_NAMESPACE
    ]
    if not profiles:
        _error(
            diagnostics, "XDL1-PLAN-PROFILE-ABSENT",
            f"no Profile resource declares extension namespace {PROFILE_NAMESPACE}",
            "Supply exactly one admitted experiment Profile resource.",
        )
        return reject()
    if len(profiles) > 1:
        _error(
            diagnostics, "XDL1-PLAN-PROFILE-DUPLICATE",
            f"{len(profiles)} Profile resources declare extension namespace {PROFILE_NAMESPACE}",
            "Supply exactly one admitted experiment Profile resource.",
            related=tuple(sorted(entry.identity.uri for entry in profiles)),
        )
        return reject()
    profile = profiles[0]
    profile_spec = _spec(profile)
    compatible = tuple(str(item) for item in _seq(profile_spec.get("compatibleApiVersions")))
    if profile.revision != PROFILE_RESOURCE_VERSION or API_VERSION not in compatible:
        _error(
            diagnostics, "XDL1-PLAN-PROFILE-VERSION-UNSUPPORTED",
            "the admitted experiment Profile version or compatibleApiVersions is not supported",
            f"Use metadata.version {PROFILE_RESOURCE_VERSION} and list {API_VERSION}.",
            pointer="/spec/compatibleApiVersions", resource=profile.identity,
        )
        return reject()
    if profile_spec.get("schemaRef") != PROFILE_SCHEMA_ID:
        _error(
            diagnostics, "XDL1-PLAN-PROFILE-SCHEMAREF-UNSUPPORTED",
            "the admitted experiment Profile schemaRef is not supported",
            f"Use schemaRef {PROFILE_SCHEMA_ID}.",
            pointer="/spec/schemaRef", resource=profile.identity,
        )
        return reject()

    # S8 -- selection.
    systems = [entry for entry in entries if entry.identity.kind == "System"]
    if not systems:
        _error(diagnostics, "XDL1-PLAN-SYSTEM-MISSING", "no System resource is present",
               "Supply exactly one System resource.")
        return reject()
    if len(systems) > 1:
        _error(
            diagnostics, "XDL1-PLAN-SYSTEM-AMBIGUOUS", "more than one System resource is present",
            "Supply exactly one System resource.",
            related=tuple(sorted(entry.identity.uri for entry in systems)),
        )
        return reject()
    system = systems[0]

    scenarios = [
        entry for entry in entries if entry.identity.kind == "Scenario"
        and _element_identity(_spec(entry).get("systemRef")) == system.identity
    ]
    if not scenarios:
        _error(diagnostics, "XDL1-PLAN-SCENARIO-MISSING", "no Scenario references the selected System",
               "Supply exactly one Scenario bound to the selected System.")
        return reject()
    if len(scenarios) > 1:
        _error(
            diagnostics, "XDL1-PLAN-SCENARIO-AMBIGUOUS", "more than one Scenario references the selected System",
            "Supply exactly one Scenario bound to the selected System.",
            related=tuple(sorted(entry.identity.uri for entry in scenarios)),
        )
        return reject()
    scenario = scenarios[0]

    deployments = [
        entry for entry in entries if entry.identity.kind == "Deployment"
        and _element_identity(_spec(entry).get("systemRef")) == system.identity
    ]
    if len(deployments) > 1:
        _error(
            diagnostics, "XDL1-PLAN-DEPLOYMENT-AMBIGUOUS", "more than one Deployment references the selected System",
            "Supply at most one Deployment for the selected System.",
            related=tuple(sorted(entry.identity.uri for entry in deployments)),
        )
        return reject()
    deployment = deployments[0] if deployments else None
    if deployment is not None:
        declared = _spec(scenario).get("deploymentRef")
        if declared is None:
            _error(
                diagnostics, "XDL1-PLAN-DEPLOYMENT-UNBOUND",
                "a Deployment is present but the selected Scenario declares no deploymentRef",
                "Reference the supplied Deployment from the Scenario.",
                pointer="/spec/deploymentRef", resource=scenario.identity,
            )
            return reject()
        if _element_identity(declared) != deployment.identity:
            _error(
                diagnostics, "XDL1-PLAN-DEPLOYMENT-UNBOUND",
                "the selected Scenario deploymentRef does not match the supplied Deployment",
                "Reference the supplied Deployment from the Scenario or remove it.",
                pointer="/spec/deploymentRef", resource=scenario.identity,
            )
            return reject()

    if not _check_payloads(entries, diagnostics):
        return reject()

    scenario_payload = _payloads_by_surface(scenario).get("scenario-root")
    if not scenario_payload:
        _error(
            diagnostics, "XDL1-PLAN-PROFILE-PAYLOAD-ABSENT",
            "the selected Scenario carries no scenario-intent payload",
            f"Attach one {PROFILE_NAMESPACE} scenario-intent payload to the Scenario.",
            resource=scenario.identity,
        )
        return reject()

    # S9-S11 -- quantities, order and intent compilation.
    plan = _compile_sections(
        entries=entries, system=system, deployment=deployment, scenario=scenario,
        profile=profile, scenario_payload=scenario_payload, static_readiness=static_readiness,
        limits=active, diagnostics=diagnostics,
    )
    if plan is None or any(item.severity is Severity.ERROR for item in diagnostics):
        return reject()

    if _secret_leaf(plan) is not None:
        _error(
            diagnostics, "XDL1-PLAN-SECRET-IN-PUBLIC-ARTIFACT",
            "an emitted plan value matches a credential or private-key pattern",
            "Remove the credential-like value from the declared public intent.",
        )
        return reject()

    # S12 -- identity, late mutation detection and digest self-check.
    contributions = _contributing_resources(entries, system, deployment, scenario, profile)
    contributing_digests = {
        entry.identity.uri: resource_semantic_digest(entry) for entry in contributions
    }
    if any(
        uri in entry_digests and contributing_digests[uri] != entry_digests[uri]
        for uri in contributing_digests
    ):
        _error(
            diagnostics, "XDL1-PLAN-INPUT-MUTATED",
            "a contributing input resource changed after it was hashed",
            "Supply one immutable revision of every contributing resource.",
        )
        return reject()
    plan["provenance"]["resources"] = _provenance_section(contributions)
    input_digest = _input_semantic_digest(contributions)
    plan["provenance"]["inputSemanticDigest"] = {"algorithm": "sha256", "value": input_digest}

    if expected_input_semantic_digests is not None:
        mismatch = _check_expected_digests(
            expected_input_semantic_digests, contributing_digests, input_digest
        )
        if mismatch is not None:
            _error(diagnostics, "XDL1-PLAN-INPUT-MUTATED", mismatch,
                   "Recompute the expected input digests from the exact admitted revision.")
            return reject()

    try:
        digest_value = compute_plan_digest(plan)
        plan["digest"] = {"algorithm": "sha256", "value": digest_value}
        consistent = plan_matches_digest(plan)
    except (ValueError, OverflowError):
        _error(
            diagnostics, "XDL1-PLAN-QUANTITY-NONFINITE",
            "a declared value is not representable in the canonical plan encoding",
            "Supply finite JSON numbers only.",
        )
        return reject()
    if not consistent:
        _error(
            diagnostics, "XDL1-PLAN-DIGEST-SELFCHECK",
            "the recomputed plan digest does not match the emitted digest",
            "Recompile the plan; no inconsistent plan is emitted.",
        )
        return reject()

    return ExperimentPlanResult(
        _ordered(diagnostics, active), plan,
        _run_envelope(
            run_id=run_id, generated_at=generated_at, status="resolved",
            plan_digest=plan["digest"]["value"], source_byte_digests={},
        ),
    )


# --------------------------------------------------------------------------------------
# Payload admission
# --------------------------------------------------------------------------------------


def _check_payloads(entries: Sequence[NormalizedResource], diagnostics: list[Diagnostic]) -> bool:
    """Validate every experiment payload attachment, kind and target identity."""

    ok = True
    for resource in entries:
        seen: dict[str, int] = {}
        for pointer, payload in _experiment_payloads(resource):
            surface, index = _attachment(pointer)
            seen[pointer] = seen.get(pointer, 0) + 1
            expected = EXPECTED_KIND_BY_SURFACE.get(surface)
            if expected is None:
                _error(
                    diagnostics, "XDL1-PLAN-PROFILE-PAYLOAD-KIND",
                    "an experiment payload is attached at an unsupported extension point",
                    "Attach scenario/step/fault payloads to a Scenario and realization payloads to a Deployment binding.",
                    pointer=pointer, resource=resource.identity,
                )
                ok = False
                continue
            if payload.get("kind") != expected:
                _error(
                    diagnostics, "XDL1-PLAN-PROFILE-PAYLOAD-KIND",
                    f"payload kind {payload.get('kind')!r} does not match its attachment point ({expected})",
                    f"Use kind {expected} at this attachment point.",
                    pointer=pointer, resource=resource.identity,
                )
                ok = False
                continue
            owner = _attachment_owner(resource, surface, index)
            if owner is None or not _target_matches(_map(payload.get("target")), owner):
                _error(
                    diagnostics, "XDL1-PLAN-PROFILE-TARGET-MISMATCH",
                    "the payload target does not match its owning resource or element",
                    "Set target to the exact owning resource/element identity.",
                    pointer=f"{pointer}/target", resource=resource.identity,
                )
                ok = False
        for pointer, count in seen.items():
            if count > 1:
                _error(
                    diagnostics, "XDL1-PLAN-PROFILE-PAYLOAD-DUPLICATE",
                    f"{count} experiment payloads are attached at one attachment pointer",
                    "Attach exactly one payload per extension point.",
                    pointer=pointer, resource=resource.identity,
                )
                ok = False
    return ok


def _attachment_owner(
    resource: NormalizedResource, surface: str, index: int | None
) -> Mapping[str, Any] | None:
    if surface == "scenario-root":
        return {"identity": resource.identity, "element": None}
    collection = _SURFACES_INVERSE.get(surface)
    if collection is None or index is None:
        return None
    items = _collection(resource, collection)
    if index >= len(items):
        return None
    element = _text(items[index].get("id"))
    if element is None:
        return None
    return {"identity": resource.identity, "element": element}


_SURFACES_INVERSE = {
    "scenario-step": "steps", "scenario-fault": "faults", "deployment-binding": "bindings",
}


def _target_matches(target: Mapping[str, Any], owner: Mapping[str, Any]) -> bool:
    identity = owner["identity"]
    if (
        target.get("apiVersion") != identity.api_version
        or target.get("kind") != identity.kind
        or target.get("namespace") != identity.namespace
        or target.get("name") != identity.name
    ):
        return False
    element = owner.get("element")
    if element is None:
        return "element" not in target
    return target.get("element") == element


# --------------------------------------------------------------------------------------
# Quantities, parameters and seed
# --------------------------------------------------------------------------------------


def _ticks(
    value: Any, unit: Any, limits: ExperimentLimits, diagnostics: list[Diagnostic], pointer: str,
) -> int | None:
    """Convert one declared quantity to exact canonical ticks, or report the defect."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _error(diagnostics, "XDL1-PLAN-QUANTITY-NONFINITE", "declared quantity is not a JSON number",
               "Supply a finite numeric quantity.", pointer=pointer)
        return None
    if isinstance(value, float) and not math.isfinite(value):
        _error(diagnostics, "XDL1-PLAN-QUANTITY-NONFINITE", "declared quantity is not finite",
               "Supply a finite numeric quantity.", pointer=pointer)
        return None
    if unit not in TIME_UNIT_TICKS:
        _error(diagnostics, "XDL1-PLAN-TIME-UNIT-UNKNOWN",
               f"declared time unit {unit!r} is outside the closed vocabulary",
               f"Use one of {', '.join(sorted(TIME_UNIT_TICKS))}.", pointer=pointer)
        return None
    if value < 0:
        _error(diagnostics, "XDL1-PLAN-QUANTITY-NEGATIVE", "declared quantity is negative",
               "Supply a non-negative quantity.", pointer=pointer)
        return None
    exact = Fraction(value) * TIME_UNIT_TICKS[unit]
    if exact.denominator != 1:
        _error(diagnostics, "XDL1-PLAN-TIME-PRECISION",
               f"declared quantity {value!r} {unit} is not an exact integer tick",
               "Supply a quantity that lands exactly on the canonical tick grid.", pointer=pointer)
        return None
    ticks = exact.numerator
    if ticks > limits.max_ticks:
        _error(diagnostics, "XDL1-PLAN-QUANTITY-OVERFLOW",
               f"declared quantity exceeds max_ticks {limits.max_ticks}",
               "Reduce the declared quantity within the finite platform bound.", pointer=pointer)
        return None
    return ticks


def _quantity(
    value: Any, limits: ExperimentLimits, diagnostics: list[Diagnostic], pointer: str,
) -> dict[str, Any] | None:
    """Return ``{value, unit, ticks}`` for a declared ``{value, unit}`` quantity."""

    source = _map(value)
    if not source:
        return None
    declared, unit = source.get("value"), source.get("unit")
    ticks = _ticks(declared, unit, limits, diagnostics, pointer)
    if ticks is None:
        return None
    return {"value": _plain(declared), "unit": str(unit), "ticks": ticks}


def _check_parameters(
    values: Any, limits: ExperimentLimits, diagnostics: list[Diagnostic], pointer: str,
) -> list[dict[str, Any]]:
    """Validate a declared parameter list and return its canonical projection."""

    parameters = _seq(values)
    if len(parameters) > limits.max_parameters:
        _error(diagnostics, "XDL1-PLAN-BOUND-EXCEEDED",
               f"{len(parameters)} parameters exceed max_parameters {limits.max_parameters}",
               "Reduce the declared parameter count.", pointer=pointer)
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for index, raw in enumerate(parameters):
        item = _map(raw)
        item_pointer = f"{pointer}/{index}"
        identifier = _text(item.get("id"))
        if identifier is None:
            continue
        if identifier in seen:
            _error(diagnostics, "XDL1-PLAN-PARAMETER-DUPLICATE",
                   f"parameter id {identifier!r} is declared more than once",
                   "Use a unique parameter id.", pointer=item_pointer)
            continue
        seen.add(identifier)
        value_type = _text(item.get("valueType"))
        value = item.get("value")
        if not _value_matches(value_type, value, limits, diagnostics, item_pointer):
            continue
        result.append({
            "id": identifier, "valueType": value_type, "value": _plain(value),
            "unitSemantics": _text(item.get("unitSemantics")),
            "mutability": _text(item.get("mutability")),
        })
    return result


def _value_matches(
    value_type: str | None, value: Any, limits: ExperimentLimits,
    diagnostics: list[Diagnostic], pointer: str,
) -> bool:
    """Check one declared parameter value against its declared ``valueType``."""

    if value_type == "boolean":
        if isinstance(value, bool):
            return True
    elif value_type == "integer":
        if isinstance(value, int) and not isinstance(value, bool):
            if abs(value) <= limits.max_seed:
                return True
            _error(diagnostics, "XDL1-PLAN-PARAMETER-BOUND", "integer parameter exceeds the finite bound",
                   "Reduce the parameter value.", pointer=pointer)
            return False
    elif value_type == "number":
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
            if abs(value) <= limits.max_number_magnitude:
                return True
            _error(diagnostics, "XDL1-PLAN-PARAMETER-BOUND",
                   "number parameter exceeds max_number_magnitude",
                   "Reduce the parameter magnitude.", pointer=pointer)
            return False
    elif value_type == "string":
        if isinstance(value, str):
            if 1 <= len(value) <= limits.max_text_length:
                return True
            _error(diagnostics, "XDL1-PLAN-PARAMETER-BOUND", "string parameter exceeds max_text_length",
                   "Shorten the declared text.", pointer=pointer)
            return False
    _error(diagnostics, "XDL1-PLAN-PARAMETER-VALUE-TYPE",
           f"parameter value does not match its declared valueType {value_type!r}",
           "Supply a value of the declared JSON type within the finite bound.", pointer=pointer)
    return False


def _check_seed(
    payload: Mapping[str, Any], limits: ExperimentLimits,
    diagnostics: list[Diagnostic], resource: ResourceIdentity,
) -> dict[str, Any] | None:
    """Validate the mandatory explicit seed and return its projection."""

    seed = _map(payload.get("seed"))
    if not seed:
        _error(diagnostics, "XDL1-PLAN-SEED-MISSING", "the experiment payload declares no explicit seed",
               "Declare an explicit seed; no default is invented.", resource=resource)
        return None
    value = seed.get("value")
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= limits.max_seed:
        _error(diagnostics, "XDL1-PLAN-SEED-RANGE",
               f"seed must be an integer in 0..{limits.max_seed}",
               "Declare a seed within the finite platform bound.", resource=resource)
        return None
    return {"value": value, "unitSemantics": _text(seed.get("unitSemantics"))}


# --------------------------------------------------------------------------------------
# Intent sections
# --------------------------------------------------------------------------------------


def _compile_sections(
    *, entries: Sequence[NormalizedResource], system: NormalizedResource,
    deployment: NormalizedResource | None, scenario: NormalizedResource, profile: NormalizedResource,
    scenario_payload: Mapping[str, Any], static_readiness: Mapping[str, Any] | None,
    limits: ExperimentLimits, diagnostics: list[Diagnostic],
) -> dict[str, Any] | None:
    """Assemble every plan section except provenance/digest, or ``None`` on any defect."""

    system_spec = _spec(system)
    scenario_spec = _spec(scenario)
    time_domain_ids = tuple(
        str(item.get("id")) for item in _collection(system, "timeDomains") if _text(item.get("id"))
    )
    flows = _collection(system, "flows")
    steps = _collection(scenario, "steps")
    faults = _collection(scenario, "faults")
    observers = _collection(scenario, "observers")
    metrics = _collection(scenario, "metrics")
    bindings = _collection(deployment, "bindings") if deployment is not None else ()

    for count, bound, label in (
        (len(flows), limits.max_flows, "flows"),
        (len(steps), limits.max_steps, "steps"),
        (len(faults), limits.max_faults, "faults"),
        (len(observers), limits.max_observers, "observers"),
        (len(metrics), limits.max_metrics, "metrics"),
        (len(bindings), limits.max_bindings, "bindings"),
    ):
        if count > bound:
            _error(diagnostics, "XDL1-PLAN-BOUND-EXCEEDED",
                   f"declared {label} ({count}) exceed the library bound {bound}",
                   "Reduce the declared entity count.")

    seed = _check_seed(scenario_payload, limits, diagnostics, scenario.identity)
    parameters = _check_parameters(scenario_payload.get("parameters"), limits, diagnostics,
                                   f"/extensions/{PROFILE_NAMESPACE}/parameters")

    fault_payloads = {str(item.get("id")): _payload_for_fault(scenario, str(item.get("id"))) for item in faults}
    used_domains: set[str] = set()
    for item in steps:
        if _text(item.get("timeDomainId")) in time_domain_ids:
            used_domains.add(str(item.get("timeDomainId")))
    for item in observers:
        if _text(item.get("timeDomainId")) in time_domain_ids:
            used_domains.add(str(item.get("timeDomainId")))
    for item in flows:
        if _text(item.get("timeDomainId")) in time_domain_ids:
            used_domains.add(str(item.get("timeDomainId")))
    for payload in fault_payloads.values():
        domain = _text(payload.get("timeDomainId"))
        if domain in time_domain_ids:
            used_domains.add(domain)

    _check_time_mappings(scenario, used_domains, diagnostics)

    components = _components_section(entries, system, limits, diagnostics)
    time_domain_section = _time_domains_section(
        system, steps, observers, flows, fault_payloads, time_domain_ids
    )
    time_mappings = _time_mappings_section(scenario, limits, diagnostics)
    dependency_order = _dependency_order(system, scenario, limits, diagnostics)
    flows_section = _flows_section(flows)
    binding_section = _bindings_section(deployment, system, limits, diagnostics)
    lifecycle = _lifecycle_section(scenario, steps, limits, diagnostics)
    fault_schedule = _fault_section(
        scenario, system, deployment, faults, fault_payloads, time_domain_ids, limits, diagnostics
    )
    observer_section, metric_section = _observation_section(
        system, deployment, scenario, observers, metrics, time_domain_ids, diagnostics
    )
    limitations = _limitations_section(
        entries, system, deployment, scenario, profile, scenario_payload, limits, diagnostics
    )

    # Total compiled-parameter scope (detailed-design.md section 10.3 scope 2, XDL1-DD-13):
    # every parameter compiled from an extension parameterList, counted over the finished
    # sections before identity finalization. This is the single place the total scope is
    # enforced; a value above max_parameters rejects with no plan of any kind.
    total_parameters = (
        len(parameters)
        + sum(len(entry["parameters"]) for entry in lifecycle)
        + sum(len(entry["parameters"]) for entry in fault_schedule)
    )
    if total_parameters > limits.max_parameters:
        _error(
            diagnostics, "XDL1-PLAN-BOUND-EXCEEDED",
            f"total compiled parameter count {total_parameters} exceeds max_parameters {limits.max_parameters}",
            "Reduce the total declared experiment parameter count across the plan.",
            pointer="/parameters",
        )

    if any(item.severity is Severity.ERROR for item in diagnostics):
        return None

    plan: dict[str, Any] = {
        "planVersion": PLAN_VERSION,
        "generator": {"task": GENERATOR_TASK, "version": GENERATOR_VERSION},
        "profile": {
            "namespace": PROFILE_NAMESPACE,
            "schemaVersion": PROFILE_SCHEMA_VERSION,
            "schemaRef": PROFILE_SCHEMA_ID,
            "resource": _identity_data(profile.identity) | {"version": profile.revision},
            "resourceDigest": _digest_member(bytes.fromhex(resource_semantic_digest(profile))),
        },
        "selection": {
            "system": _selection_entry(system),
            "deployment": _selection_entry(deployment) if deployment is not None else None,
            "scenario": _selection_entry(scenario),
            "staticReadiness": _readiness_section(deployment, static_readiness),
        },
        "seed": seed,
        "parameters": parameters,
        "components": components,
        "timeDomains": time_domain_section,
        "timeMappings": time_mappings,
        "dependencyOrder": dependency_order,
        "flows": flows_section,
        "bindings": binding_section,
        "lifecycleIntent": lifecycle,
        "faultSchedule": fault_schedule,
        "observers": observer_section,
        "metrics": metric_section,
        "initialConditions": _plain(scenario_spec.get("initialConditions")) or {},
        "acceptanceIntent": _text(scenario_spec.get("acceptanceIntent")),
        "limitations": limitations,
        "nonReadiness": {
            "statement": NON_READINESS_STATEMENT,
            "claim": "declared-intent-validation-only",
            "executableArtifactAvailability": False,
            "runtimeFitness": False,
            "liveReadiness": False,
            "compatibilityOrParity": False,
        },
        "provenance": {"inputSemanticDigest": None, "resources": []},
        "status": PLAN_STATUS,
    }
    return plan


def _selection_entry(resource: NormalizedResource) -> dict[str, Any]:
    entry = _identity_data(resource.identity)
    entry["version"] = resource.revision
    entry["semanticDigest"] = _digest_member(bytes.fromhex(resource_semantic_digest(resource)))
    return entry


def _readiness_section(
    deployment: NormalizedResource | None, static_readiness: Mapping[str, Any] | None,
) -> dict[str, str]:
    if deployment is None or static_readiness is None:
        return {}
    value = static_readiness.get(deployment.identity.uri)
    if value is None:
        return {}
    resolved = value.value if isinstance(value, StaticReadiness) else str(value)
    return {deployment.identity.uri: resolved}


def _core_declared_parameters(
    resource: NormalizedResource, *, pointer: str, limits: ExperimentLimits,
    diagnostics: list[Diagnostic],
) -> list[dict[str, Any]]:
    """Project a declaring core parameter list and enforce the declared-core bound.

    ``System.spec.parameters[]`` and each referenced ``Component.spec.parameters[]`` are
    declared core parameter *projections* (scope 3 of ``detailed-design.md`` section 10.3);
    each declaring list is independently bounded by ``max_parameters``. Only declared
    references are projected: no value or default is copied.
    """

    declared = _collection(resource, "parameters")
    if len(declared) > limits.max_parameters:
        _error(
            diagnostics, "XDL1-PLAN-BOUND-EXCEEDED",
            f"declared core parameter count {len(declared)} on {resource.identity.uri} "
            f"exceeds max_parameters {limits.max_parameters}",
            "Reduce the declared core parameter count.",
            pointer=pointer, resource=resource.identity,
        )
    return [
        {
            "id": _text(parameter.get("id")),
            "valueType": _text(parameter.get("valueType")),
            "unitSemantics": _text(parameter.get("unitSemantics")),
            "mutability": _text(parameter.get("mutability")),
        }
        for parameter in declared
    ]


def _core_model_refs(resource: NormalizedResource) -> list[dict[str, Any]]:
    """Project a declaring resource's model references as declared references only."""

    return [
        {
            "id": _text(model.get("id")),
            "modelKind": _text(model.get("modelKind")),
            "externalRef": _text(model.get("externalRef")),
            "maturity": _text(model.get("maturity")),
        }
        for model in _collection(resource, "models")
    ]


def _components_section(
    entries: Sequence[NormalizedResource], system: NormalizedResource,
    limits: ExperimentLimits, diagnostics: list[Diagnostic],
) -> list[dict[str, Any]]:
    """Emit the frozen ``components`` surface: one System-scope entry first, then instances.

    The always-present System-scope entry is the deterministic destination for every
    declared ``System.spec.parameters[]`` and ``System.spec.models[]`` entry
    (``XDL1-DD-14``); it is never dropped and never copied into a component-instance entry.
    """

    by_identity = {entry.identity: entry for entry in entries}
    result: list[dict[str, Any]] = [{
        "scope": "system",
        "instanceId": None,
        "componentRef": None,
        "nodeId": None,
        "declaredParameters": _core_declared_parameters(
            system, pointer="/spec/parameters", limits=limits, diagnostics=diagnostics,
        ),
        "modelRefs": _core_model_refs(system),
    }]
    for instance in _collection(system, "componentInstances"):
        reference = _map(instance.get("componentRef"))
        identity = _element_identity(reference)
        component = by_identity.get(identity)
        declared = [] if component is None else _core_declared_parameters(
            component, pointer="/spec/parameters", limits=limits, diagnostics=diagnostics,
        )
        models = [] if component is None else _core_model_refs(component)
        result.append({
            "scope": "component-instance",
            "instanceId": _text(instance.get("id")),
            "componentRef": _identity_data(identity),
            "nodeId": _text(instance.get("nodeId")),
            "declaredParameters": declared,
            "modelRefs": models,
        })
    return result


def _time_domains_section(
    system: NormalizedResource, steps: Sequence[Mapping[str, Any]],
    observers: Sequence[Mapping[str, Any]], flows: Sequence[Mapping[str, Any]],
    fault_payloads: Mapping[str, Mapping[str, Any]], time_domain_ids: Sequence[str],
) -> list[dict[str, Any]]:
    domain_ids = list(time_domain_ids)
    used: dict[str, dict[str, list[str]]] = {
        key: {"step": [], "observer": [], "flow": [], "fault": []} for key in domain_ids
    }
    for item in steps:
        domain = _text(item.get("timeDomainId"))
        if domain in used:
            used[domain]["step"].append(str(item.get("id")))
    for item in observers:
        domain = _text(item.get("timeDomainId"))
        if domain in used:
            used[domain]["observer"].append(str(item.get("id")))
    for item in flows:
        domain = _text(item.get("timeDomainId"))
        if domain in used:
            used[domain]["flow"].append(str(item.get("id")))
    for fault_id, payload in fault_payloads.items():
        domain = _text(payload.get("timeDomainId"))
        if domain in used:
            used[domain]["fault"].append(fault_id)
    result: list[dict[str, Any]] = []
    for domain in _collection(system, "timeDomains"):
        domain_id = str(domain.get("id"))
        entry = {
            "id": domain_id,
            "clockClass": _text(domain.get("clockClass")),
            "epoch": _text(domain.get("epoch")),
            "rate": _text(domain.get("rate")),
            "monotonic": bool(domain.get("monotonic", False)),
            "canonicalUnit": "tick",
            "usedBy": [
                *[f"step:{value}" for value in sorted(used[domain_id]["step"])],
                *[f"observer:{value}" for value in sorted(used[domain_id]["observer"])],
                *[f"flow:{value}" for value in sorted(used[domain_id]["flow"])],
                *[f"fault:{value}" for value in sorted(used[domain_id]["fault"])],
            ],
        }
        result.append(entry)
    return result


def _time_mappings_section(
    scenario: NormalizedResource, limits: ExperimentLimits, diagnostics: list[Diagnostic],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, item in enumerate(_collection(scenario, "timeMappings")):
        tolerance = _quantity(item.get("tolerance"), limits, diagnostics,
                              f"/spec/timeMappings/{index}/tolerance")
        result.append({
            "declaredIndex": index,
            "sourceTimeDomainId": _text(item.get("sourceTimeDomainId")),
            "targetTimeDomainId": _text(item.get("targetTimeDomainId")),
            "mapping": _text(item.get("mapping")),
            "tolerance": tolerance,
        })
    return result


def _check_time_mappings(
    scenario: NormalizedResource, used_domains: set[str], diagnostics: list[Diagnostic],
) -> None:
    declared: set[frozenset[str]] = set()
    for item in _collection(scenario, "timeMappings"):
        source, target = _text(item.get("sourceTimeDomainId")), _text(item.get("targetTimeDomainId"))
        if source is not None and target is not None and source != target:
            declared.add(frozenset((source, target)))
    ordered = sorted(used_domains)
    for first_index, first in enumerate(ordered):
        for second in ordered[first_index + 1:]:
            if frozenset((first, second)) not in declared:
                _error(
                    diagnostics, "XDL1-PLAN-TIME-MAPPING-MISSING",
                    f"declared intent uses time domains {first!r} and {second!r} without a declared mapping",
                    "Declare a mapping and tolerance for every pair of used time domains.",
                    pointer="/spec/timeMappings", resource=scenario.identity,
                )


def _dependency_order(
    system: NormalizedResource, scenario: NormalizedResource,
    limits: ExperimentLimits, diagnostics: list[Diagnostic],
) -> list[dict[str, Any]]:
    instances = _collection(system, "componentInstances")
    steps = _collection(scenario, "steps")
    nodes = _collection(system, "nodes")
    endpoints = {str(item.get("id")): item for item in _collection(system, "endpoints")}
    instance_ids = {str(item.get("id")) for item in instances}
    step_ids = {str(item.get("id")) for item in steps}

    entries: dict[str, dict[str, Any]] = {}
    for index, node in enumerate(nodes):
        node_id = str(node.get("id"))
        if any(_text(instance.get("nodeId")) == node_id for instance in instances):
            entries[f"node:{node_id}"] = {"kind": "node", "id": node_id, "declaredIndex": index, "owner": "system"}
    for index, instance in enumerate(instances):
        entries[f"component-instance:{instance.get('id')}"] = {
            "kind": "component-instance", "id": str(instance.get("id")),
            "declaredIndex": index, "owner": "system",
        }
    for index, step in enumerate(steps):
        entries[f"step:{step.get('id')}"] = {
            "kind": "step", "id": str(step.get("id")), "declaredIndex": index, "owner": "scenario",
        }

    edges: dict[str, set[str]] = {key: set() for key in entries}
    incoming: dict[str, set[str]] = {key: set() for key in entries}
    for flow in _collection(system, "flows"):
        source_endpoint = endpoints.get(_text(flow.get("sourceEndpointId")))
        if source_endpoint is None:
            continue
        owner = _text(source_endpoint.get("ownerId"))
        if owner not in instance_ids:
            continue
        for destination_id in _seq(flow.get("destinationEndpointIds")):
            destination = endpoints.get(_text(destination_id))
            if destination is None:
                continue
            target_owner = _text(destination.get("ownerId"))
            if target_owner not in instance_ids or target_owner == owner:
                continue
            edges[f"component-instance:{owner}"].add(f"component-instance:{target_owner}")
            incoming[f"component-instance:{target_owner}"].add(f"component-instance:{owner}")

    for step in steps:
        step_id = str(step.get("id"))
        dependencies = _seq(_map(_payload_for_step(scenario, step_id)).get("dependsOn"))
        if len(dependencies) > limits.max_dependencies_per_step:
            _error(diagnostics, "XDL1-PLAN-BOUND-EXCEEDED",
                   "step dependency count exceeds max_dependencies_per_step",
                   "Reduce the declared dependencies.", resource=scenario.identity)
        for dependency in dependencies:
            name = _text(dependency)
            if name is None:
                continue
            if name not in step_ids:
                _error(
                    diagnostics, "XDL1-PLAN-DEPENDENCY-MISSING",
                    f"step {step_id!r} depends on undeclared step {name!r}",
                    "Declare every dependency within the same Scenario.",
                    resource=scenario.identity,
                )
                continue
            edges[f"step:{name}"].add(f"step:{step_id}")
            incoming[f"step:{step_id}"].add(f"step:{name}")

    def ready_key(key: str) -> tuple[int, int, str]:
        value = entries[key]
        return (KIND_RANK[value["kind"]], value["declaredIndex"], value["id"])

    remaining = {key: set(value) for key, value in incoming.items()}
    ready = sorted((key for key, value in remaining.items() if not value), key=ready_key)
    order: list[str] = []
    while ready:
        key = ready.pop(0)
        order.append(key)
        for successor in sorted(edges[key], key=ready_key):
            remaining[successor].discard(key)
            if not remaining[successor] and successor not in order and successor not in ready:
                ready.append(successor)
        ready.sort(key=ready_key)
    if len(order) != len(entries):
        unresolved = sorted(set(entries) - set(order), key=ready_key)
        _error(
            diagnostics, "XDL1-PLAN-DEPENDENCY-CYCLE",
            "the declared dependency graph contains a cycle",
            "Remove the dependency cycle; no partial order is emitted.",
            resource=system.identity, related=tuple(entries[key]["id"] for key in unresolved),
        )
        return []
    return [
        {"rank": rank, "kind": entries[key]["kind"], "id": entries[key]["id"], "owner": entries[key]["owner"]}
        for rank, key in enumerate(order)
    ]


def _payload_for_step(scenario: NormalizedResource, step_id: str) -> Mapping[str, Any]:
    for pointer, payload in _experiment_payloads(scenario):
        surface, index = _attachment(pointer)
        if surface != "scenario-step" or index is None:
            continue
        steps = _collection(scenario, "steps")
        if index < len(steps) and _text(steps[index].get("id")) == step_id:
            return payload
    return FrozenMap()


def _payload_for_fault(scenario: NormalizedResource, fault_id: str) -> Mapping[str, Any]:
    for pointer, payload in _experiment_payloads(scenario):
        surface, index = _attachment(pointer)
        if surface != "scenario-fault" or index is None:
            continue
        faults = _collection(scenario, "faults")
        if index < len(faults) and _text(faults[index].get("id")) == fault_id:
            return payload
    return FrozenMap()


def _payload_for_binding(deployment: NormalizedResource | None, binding_id: str) -> Mapping[str, Any]:
    if deployment is None:
        return FrozenMap()
    for pointer, payload in _experiment_payloads(deployment):
        surface, index = _attachment(pointer)
        if surface != "deployment-binding" or index is None:
            continue
        bindings = _collection(deployment, "bindings")
        if index < len(bindings) and _text(bindings[index].get("id")) == binding_id:
            return payload
    return FrozenMap()


def _flows_section(flows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": _text(item.get("id")),
            "sourceEndpointId": _text(item.get("sourceEndpointId")),
            "destinationEndpointIds": [str(value) for value in _seq(item.get("destinationEndpointIds"))],
            "interfaceId": _text(item.get("interfaceId")),
            "deliveryIntent": _text(item.get("deliveryIntent")),
            "networkId": _text(item.get("networkId")),
            "timeDomainId": _text(item.get("timeDomainId")),
        }
        for item in flows
    ]


def _bindings_section(
    deployment: NormalizedResource | None, system: NormalizedResource,
    limits: ExperimentLimits, diagnostics: list[Diagnostic],
) -> list[dict[str, Any]]:
    if deployment is None:
        return []
    bindings = _collection(deployment, "bindings")
    if len(bindings) > limits.max_bindings:
        _error(diagnostics, "XDL1-PLAN-BOUND-EXCEEDED", "declared bindings exceed max_bindings",
               "Reduce the declared binding count.")
    artifacts = {str(item.get("id")): item for item in _collection(deployment, "artifacts")}
    targets = {str(item.get("id")): item for item in _collection(deployment, "targets")}
    result: list[dict[str, Any]] = []
    for binding in bindings:
        binding_id = str(binding.get("id"))
        payload = _map(_payload_for_binding(deployment, binding_id))
        target = targets.get(_text(binding.get("targetId")))
        artifact_refs: list[dict[str, Any]] = []
        pinned = True
        for artifact_id in _seq(binding.get("artifactIds")):
            name = _text(artifact_id)
            artifact = artifacts.get(str(name))
            if artifact is None:
                _error(
                    diagnostics, "XDL1-PLAN-ARTIFACT-REFERENCE-UNRESOLVED",
                    f"binding {binding_id!r} references undeclared artifact {name!r}",
                    "Declare the artifact in the Deployment or remove the reference.",
                    resource=deployment.identity,
                )
                pinned = False
                continue
            digest = _text(artifact.get("digest"))
            if not digest:
                _error(
                    diagnostics, "XDL1-PLAN-ARTIFACT-PIN-MISSING",
                    f"artifact {name!r} has no immutable digest",
                    "Supply a pinned digest before declaring binding intent.",
                    resource=deployment.identity,
                )
                pinned = False
            artifact_refs.append({
                "id": name,
                "artifactKind": _text(artifact.get("artifactKind")),
                "version": _text(artifact.get("version")),
                "digest": digest,
                "sourceRef": _text(artifact.get("sourceRef")),
                "maturity": _text(artifact.get("maturity")),
            })
        realization = _text(binding.get("realizationClass"))
        target_class = _text(target.get("targetClass")) if target else None
        if realization == "physical" or target_class == "physical":
            _error(
                diagnostics, "XDL1-PLAN-REALIZATION-UNSUPPORTED",
                "a physical realization is declared; Phase 1 supports declared simulated/virtual/hybrid only",
                "Declare a simulated, virtual or hybrid realization.",
                resource=deployment.identity,
            )
        delivery = _text(payload.get("delivery"))
        retry = _map(payload.get("retry"))
        if delivery in {"in-place", "staged"} and not (artifact_refs and pinned):
            _error(
                diagnostics, "XDL1-PLAN-DELIVERY-UNSUPPORTED",
                f"delivery {delivery!r} requires at least one pinned artifact on the binding",
                "Pin an artifact or declare delivery 'none'.",
                resource=deployment.identity,
            )
        if delivery == "none" and retry:
            _error(
                diagnostics, "XDL1-PLAN-RETRY-UNSUPPORTED",
                "a retry policy is declared together with delivery 'none'",
                "Remove the retry policy or declare a delivery.",
                resource=deployment.identity,
            )
        retry_projection: dict[str, Any] | None = None
        if retry:
            policy = _text(retry.get("policy"))
            attempts = retry.get("maxAttempts")
            retry_projection = {
                "policy": policy,
                "maxAttempts": attempts if isinstance(attempts, int) and not isinstance(attempts, bool) else None,
            }
        protocol = _map(payload.get("protocolBinding"))
        protocol_projection = None
        if protocol:
            protocol_projection = {
                "standardRef": _text(protocol.get("standardRef")),
                "bindingKind": _text(protocol.get("bindingKind")),
                "compatibility": _text(protocol.get("compatibility")),
                "limitations": [str(value) for value in _seq(protocol.get("limitations"))],
            }
        logical = _map(binding.get("logicalRef"))
        result.append({
            "id": binding_id,
            "logicalRef": _element_ref_data(logical),
            "collection": _element_collection(
                system if _element_identity(logical) == system.identity else deployment,
                _element_id(logical),
            ),
            "realizationClass": realization,
            "targetId": _text(binding.get("targetId")),
            "targetClass": target_class,
            "artifactRefs": artifact_refs,
            "resourceIds": [str(value) for value in _seq(binding.get("resourceIds"))],
            "delivery": delivery,
            "retry": retry_projection,
            "protocolBinding": protocol_projection,
        })
    return result


def _lifecycle_section(
    scenario: NormalizedResource, steps: Sequence[Mapping[str, Any]],
    limits: ExperimentLimits, diagnostics: list[Diagnostic],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for step in steps:
        step_id = str(step.get("id"))
        payload = _map(_payload_for_step(scenario, step_id))
        schedule = _map(step.get("schedule"))
        at_ticks = _ticks(schedule.get("at"), schedule.get("unit"), limits, diagnostics,
                          f"/spec/steps/{step_id}/schedule")
        result.append({
            "stepId": step_id,
            "actionKind": _text(step.get("actionKind")),
            "targetRef": _element_ref_data(step.get("targetRef")),
            "timeDomainId": _text(step.get("timeDomainId")),
            "phase": _text(payload.get("phase")),
            "schedule": {
                "declaredAt": _plain(schedule.get("at")),
                "declaredUnit": _text(schedule.get("unit")),
                "atTicks": at_ticks,
                "tolerance": _quantity(schedule.get("tolerance"), limits, diagnostics,
                                       f"/spec/steps/{step_id}/schedule/tolerance"),
            },
            "dependsOn": [str(value) for value in _seq(payload.get("dependsOn"))],
            "duration": _quantity(payload.get("duration"), limits, diagnostics,
                                  f"/spec/steps/{step_id}/duration"),
            "parameters": _check_parameters(payload.get("parameters"), limits, diagnostics,
                                            f"/spec/steps/{step_id}/parameters"),
        })
    result.sort(key=lambda item: (
        str(item["timeDomainId"] or ""),
        item["schedule"]["atTicks"] if item["schedule"]["atTicks"] is not None else -1,
        PHASE_ORDER.get(str(item["phase"]), 99),
        str(item["stepId"]),
    ))
    return result


def _fault_section(
    scenario: NormalizedResource, system: NormalizedResource, deployment: NormalizedResource | None,
    faults: Sequence[Mapping[str, Any]], fault_payloads: Mapping[str, Mapping[str, Any]],
    time_domain_ids: Sequence[str], limits: ExperimentLimits, diagnostics: list[Diagnostic],
) -> list[dict[str, Any]]:
    declared_orders: dict[int, list[str]] = {}
    result: list[dict[str, Any]] = []
    for fault in faults:
        fault_id = str(fault.get("id"))
        payload = _map(fault_payloads.get(fault_id))
        trigger = _map(payload.get("trigger"))
        kind = _text(trigger.get("kind")) if trigger else None
        time_domain = _text(payload.get("timeDomainId"))
        trigger_projection: dict[str, Any] | None = None
        sort_key: tuple[Any, ...] = (99, "", 0, fault_id)
        if kind == "time":
            at_ticks = _ticks(trigger.get("at"), trigger.get("unit"), limits, diagnostics,
                              f"/spec/faults/{fault_id}/trigger")
            if time_domain is None:
                _error(diagnostics, "XDL1-PLAN-TIME-DOMAIN-UNRESOLVED",
                       f"fault {fault_id!r} declares no time domain",
                       "Declare timeDomainId resolving to a System time domain.",
                       resource=scenario.identity)
            elif time_domain not in time_domain_ids:
                _error(diagnostics, "XDL1-PLAN-TIME-DOMAIN-UNRESOLVED",
                       f"fault time domain {time_domain!r} does not resolve to a System time domain",
                       "Reference a declared System time domain.", resource=scenario.identity)
            trigger_projection = {
                "kind": "time", "declaredAt": _plain(trigger.get("at")),
                "declaredUnit": _text(trigger.get("unit")), "atTicks": at_ticks,
            }
            sort_key = (0, str(time_domain or ""), at_ticks if at_ticks is not None else -1, fault_id)
        elif kind == "declared-order":
            order = trigger.get("order")
            if isinstance(order, int) and not isinstance(order, bool) and 0 <= order <= 1048575:
                declared_orders.setdefault(order, []).append(fault_id)
                trigger_projection = {"kind": "declared-order", "order": order}
                sort_key = (1, "", order, fault_id)
        if trigger_projection is None:
            _error(diagnostics, "XDL1-PLAN-FAULT-TRIGGER-MISSING",
                   f"fault {fault_id!r} carries no resolvable trigger",
                   "Declare exactly one time or declared-order trigger.", resource=scenario.identity)
        duration_value = payload.get("duration")
        if duration_value is None:
            _error(diagnostics, "XDL1-PLAN-FAULT-DURATION-INVALID",
                   f"fault {fault_id!r} declares no duration",
                   "Declare an explicit non-negative duration.", resource=scenario.identity)
            duration = None
        else:
            duration = _quantity(duration_value, limits, diagnostics, f"/spec/faults/{fault_id}/duration")
            if duration is None:
                _error(diagnostics, "XDL1-PLAN-FAULT-DURATION-INVALID",
                       f"fault {fault_id!r} duration is not a resolvable time quantity",
                       "Declare a finite non-negative duration with a closed time unit.",
                       resource=scenario.identity)
        target = _element_ref_data(fault.get("targetRef"))
        target_identity = _element_identity(fault.get("targetRef"))
        if target_identity == system.identity:
            fault_collection = _element_collection(system, _element_id(fault.get("targetRef")))
        elif deployment is not None and target_identity == deployment.identity:
            fault_collection = _element_collection(deployment, _element_id(fault.get("targetRef")))
        else:
            fault_collection = None
        result.append({
            "entryId": f"fault:{fault_id}",
            "entryKind": "fault",
            "faultId": fault_id,
            "faultKind": _text(fault.get("faultKind")),
            "targetRef": target,
            "collection": fault_collection,
            "activation": _text(fault.get("activation")),
            "recovery": _text(fault.get("recovery")),
            "maturity": _text(fault.get("maturity")),
            "timeDomainId": time_domain,
            "trigger": trigger_projection,
            "duration": duration,
            "parameters": _check_parameters(payload.get("parameters"), limits, diagnostics,
                                            f"/spec/faults/{fault_id}/parameters"),
            "_sortKey": sort_key,
        })
    for order, ids in declared_orders.items():
        if len(ids) > 1:
            _error(
                diagnostics, "XDL1-PLAN-SCHEDULE-AMBIGUOUS",
                f"faults {sorted(ids)} declare the same declared-order trigger value {order}",
                "Use a distinct declared-order value per fault.", resource=scenario.identity,
                related=tuple(sorted(ids)),
            )
    result.sort(key=lambda item: item.pop("_sortKey"))
    return result


def _observation_section(
    system: NormalizedResource, deployment: NormalizedResource | None,
    scenario: NormalizedResource, observers: Sequence[Mapping[str, Any]],
    metrics: Sequence[Mapping[str, Any]], time_domain_ids: Sequence[str],
    diagnostics: list[Diagnostic],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    observer_entries: list[dict[str, Any]] = []
    observer_domains: dict[str, str | None] = {}
    for observer in observers:
        observer_id = str(observer.get("id"))
        target = _map(observer.get("targetRef"))
        identity = _element_identity(target)
        element = _element_id(target)
        collection = None
        owner = system if identity == system.identity else (
            deployment if deployment is not None and identity == deployment.identity else None
        )
        if owner is not None:
            collection = _element_collection(owner, element)
        if collection is None:
            _error(diagnostics, "XDL1-PLAN-OBSERVER-UNRESOLVED",
                   f"observer {observer_id!r} target does not resolve to a declared element",
                   "Target a declared element of the selected System or Deployment.",
                   resource=scenario.identity)
        domain = _text(observer.get("timeDomainId"))
        observer_domains[observer_id] = domain
        observer_entries.append({
            "observerId": observer_id,
            "targetRef": _element_ref_data(target),
            "collection": collection,
            "timeDomainId": domain,
            "samplingIntent": _text(observer.get("samplingIntent")),
            "payloadPolicy": {
                "payloadSchema": _text(observer.get("payloadSchema")),
                "unitSemantics": _text(observer.get("unitSemantics")),
            },
            "evidenceSinkRef": _text(observer.get("evidenceSinkRef")),
        })
    observer_entries.sort(key=lambda item: (str(item["timeDomainId"] or ""), str(item["observerId"])))
    metric_entries: list[dict[str, Any]] = []
    for metric in metrics:
        metric_id = str(metric.get("id"))
        observer_ids = [str(value) for value in _seq(metric.get("observerIds"))]
        resolved = [value for value in observer_ids if value in observer_domains]
        domains: set[str] = set()
        for value in resolved:
            domain = observer_domains[value]
            if domain is not None and domain in time_domain_ids:
                domains.add(domain)
        if not observer_ids or len(resolved) != len(observer_ids) or not domains:
            _error(
                diagnostics, "XDL1-PLAN-METRIC-LINK-INCOMPLETE",
                f"metric {metric_id!r} has no resolving observer/time/unit linkage",
                "Link the metric to declared observers with resolving time domains.",
                resource=scenario.identity,
            )
        metric_entries.append({
            "metricId": metric_id,
            "observerIds": sorted(observer_ids),
            "calculationRef": _text(metric.get("calculationRef")),
            "unitSemantics": _text(metric.get("unitSemantics")),
            "acceptance": _text(metric.get("acceptance")),
            "timeDomainIds": sorted(domains),
            "status": "reference-only",
        })
    metric_entries.sort(key=lambda item: str(item["metricId"]))
    return observer_entries, metric_entries


def _limitations_section(
    entries: Sequence[NormalizedResource], system: NormalizedResource,
    deployment: NormalizedResource | None, scenario: NormalizedResource,
    profile: NormalizedResource, scenario_payload: Mapping[str, Any],
    limits: ExperimentLimits, diagnostics: list[Diagnostic],
) -> list[str]:
    merged: list[str] = []
    for resource in _contributing_resources(entries, system, deployment, scenario, profile):
        for value in _seq(_map(resource.provenance).get("limitations")):
            text = _text(value)
            if text is not None and text not in merged:
                merged.append(text)
    for value in _seq(scenario_payload.get("fidelityLimitations")):
        text = _text(value)
        if text is not None and text not in merged:
            merged.append(text)
    if len(merged) > limits.max_limitations:
        _error(diagnostics, "XDL1-PLAN-BOUND-EXCEEDED",
               f"{len(merged)} limitations exceed max_limitations {limits.max_limitations}",
               "Reduce the declared limitation count.")
    for value in merged:
        if len(value) > limits.max_text_length:
            _error(diagnostics, "XDL1-PLAN-BOUND-EXCEEDED",
                   "a declared limitation exceeds max_text_length",
                   "Shorten the declared text.")
    return merged


def _contributing_resources(
    entries: Sequence[NormalizedResource], system: NormalizedResource,
    deployment: NormalizedResource | None, scenario: NormalizedResource,
    profile: NormalizedResource,
) -> tuple[NormalizedResource, ...]:
    by_identity = {entry.identity: entry for entry in entries}
    contributing: list[NormalizedResource] = [system]
    if deployment is not None:
        contributing.append(deployment)
    contributing.append(scenario)
    contributing.append(profile)
    for instance in _collection(system, "componentInstances"):
        component = by_identity.get(_element_identity(_map(instance.get("componentRef"))))
        if component is not None and all(component is not item for item in contributing):
            contributing.append(component)
    unique: dict[tuple[str, str, str, str, str], NormalizedResource] = {}
    for resource in contributing:
        unique[(
            resource.identity.api_version, resource.identity.kind,
            resource.identity.namespace, resource.identity.name, resource.revision,
        )] = resource
    return tuple(unique[key] for key in sorted(unique))


def _provenance_section(contributions: Sequence[NormalizedResource]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for resource in contributions:
        entry = _identity_data(resource.identity)
        entry["version"] = resource.revision
        entry["semanticDigest"] = _digest_member(bytes.fromhex(resource_semantic_digest(resource)))
        result.append(entry)
    return result


def _check_expected_digests(
    expected: Mapping[str, str], resource_digests: Mapping[str, str], input_digest: str,
) -> str | None:
    for key, value in expected.items():
        actual = input_digest if key in {"input", "inputSemanticDigest"} else resource_digests.get(str(key))
        if actual is None:
            return f"expected input digest {key!r} does not match any contributing resource"
        if actual != value:
            return f"expected input digest {key!r} differs from the recomputed digest"
    return None


def _secret_leaf(value: Any) -> str | None:
    if isinstance(value, str):
        if (
            _SECRET_ASSIGNMENT.search(value)
            or _SECRET_PRIVATE_KEY.search(value)
            or _SECRET_URI_USERINFO.match(value)
        ):
            return value
        return None
    if isinstance(value, Mapping):
        for child in value.values():
            found = _secret_leaf(child)
            if found is not None:
                return found
        return None
    if isinstance(value, (list, tuple)):
        for child in value:
            found = _secret_leaf(child)
            if found is not None:
                return found
        return None
    return None


# --------------------------------------------------------------------------------------
# Loader-backed entry points
# --------------------------------------------------------------------------------------


def compile_experiment_sources(
    sources: Sequence[Any], *, profile_schema_paths: Sequence[Any] = (),
    run_id: str | None = None, generated_at: str | None = None,
    expected_input_semantic_digests: Mapping[str, str] | None = None,
    limits: ExperimentLimits | None = None,
) -> ExperimentPlanResult:
    """Run the accepted loader/validator over named bytes, then compile the plan."""

    active = limits if limits is not None else ExperimentLimits()
    _validate_run_envelope(run_id, generated_at)
    result = validate_sources(
        sources, profile_schema_paths=tuple(profile_schema_paths), limits=_load_limits(active)
    )
    byte_digests = {
        _source_name(value): hashlib.sha256(_source_bytes(value)).hexdigest() for value in sources
    }
    return _compile_validated(
        result, byte_digests=byte_digests, run_id=run_id, generated_at=generated_at,
        expected_input_semantic_digests=expected_input_semantic_digests, limits=active,
    )


def compile_experiment_files(
    paths: Sequence[Any], *, profile_schema_paths: Sequence[Any] = (),
    run_id: str | None = None, generated_at: str | None = None,
    expected_input_semantic_digests: Mapping[str, str] | None = None,
    limits: ExperimentLimits | None = None,
) -> ExperimentPlanResult:
    """Read explicitly supplied files, run the accepted loader, then compile the plan."""

    active = limits if limits is not None else ExperimentLimits()
    _validate_run_envelope(run_id, generated_at)
    result = validate_files(
        tuple(paths), profile_schema_paths=tuple(profile_schema_paths), limits=_load_limits(active)
    )
    byte_digests = {str(path): hashlib.sha256(_path_bytes(path)).hexdigest() for path in paths}
    return _compile_validated(
        result, byte_digests=byte_digests, run_id=run_id, generated_at=generated_at,
        expected_input_semantic_digests=expected_input_semantic_digests, limits=active,
    )


def _compile_validated(
    result: Any, *, byte_digests: Mapping[str, str], run_id: str | None, generated_at: str | None,
    expected_input_semantic_digests: Mapping[str, str] | None, limits: ExperimentLimits,
) -> ExperimentPlanResult:
    if any(item.severity is Severity.ERROR for item in result.diagnostics):
        return _rejected(
            list(result.diagnostics), limits, run_id=run_id, generated_at=generated_at,
            source_byte_digests=byte_digests,
        )
    compiled = compile_experiment_plan(
        result.resources, static_readiness=result.readiness, run_id=run_id,
        generated_at=generated_at, expected_input_semantic_digests=expected_input_semantic_digests,
        limits=limits,
    )
    if compiled.plan is not None:
        return ExperimentPlanResult(
            compiled.diagnostics, compiled.plan,
            _run_envelope(
                run_id=run_id, generated_at=generated_at, status="resolved",
                plan_digest=compiled.plan["digest"]["value"], source_byte_digests=byte_digests,
            ),
        )
    return ExperimentPlanResult(
        compiled.diagnostics, None,
        _run_envelope(
            run_id=run_id, generated_at=generated_at, status="rejected", plan_digest=None,
            source_byte_digests=byte_digests,
        ),
    )


def _load_limits(limits: ExperimentLimits) -> LoadLimits:
    return LoadLimits(
        max_bytes_per_file=limits.max_bytes_per_file, max_resources=limits.max_resources,
    )


def _source_name(value: Any) -> str:
    return str(getattr(value, "name", value[0] if isinstance(value, tuple) else value))


def _source_bytes(value: Any) -> bytes:
    data = getattr(value, "data", None)
    if data is not None:
        return bytes(data)
    if isinstance(value, tuple):
        return bytes(value[1])
    return b""


def _path_bytes(path: Any) -> bytes:
    with open(path, "rb") as stream:
        return stream.read()


# --------------------------------------------------------------------------------------
# Public report data
# --------------------------------------------------------------------------------------


def plan_public_data(result: ExperimentPlanResult) -> dict[str, Any]:
    """Return the stable machine-readable report envelope for a compile result."""

    return {
        "reportVersion": "1",
        "toolVersion": GENERATOR_VERSION,
        "valid": result.is_valid,
        "plan": result.plan,
        "run": _plain(result.run),
        "diagnostics": [diagnostic_to_data(item) for item in result.diagnostics],
    }
