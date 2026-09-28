#!/usr/bin/env python3
"""Validate the bounded T017 X-COM Profile v0.1 / activation-plan v1 contracts offline.

The tool is deterministic, offline, single-threaded, bounded, and read-only. It checks the two
JSON schemas, the digest/provenance contract, the bounded positive fixtures, and a controlled
negative-case set with one distinct nonzero exit class per failure family. It performs no network
access, starts no child process, and writes no file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, NamedTuple

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[1]
PROFILE_SCHEMA_REL = Path("xdl/profiles/xcom-v0.1.schema.json")
PLAN_SCHEMA_REL = Path("src/xverse/xcom/contracts/v1/activation-plan.schema.json")
FIXTURES_REL = Path("tests/xcom/activation_plan/fixtures")
EXPECTED_SUMMARY_REL = FIXTURES_REL / "expected-summary.txt"
DOCS_REL = Path("docs/engineering/xcom/t017")
TASKS_REL = Path("specs/007-xcom-core/tasks.md")
SELF_SOURCE = Path(__file__).resolve()

OK = 0
SCHEMA_INVALID = 2
PROFILE_INVALID = 3
PLAN_INVALID = 4
DIGEST_INVALID = 5
IO_ERROR = 6
BOUNDARY_INVALID = 7

EXIT_NAMES = {
    OK: "OK",
    SCHEMA_INVALID: "SCHEMA_INVALID",
    PROFILE_INVALID: "PROFILE_INVALID",
    PLAN_INVALID: "PLAN_INVALID",
    DIGEST_INVALID: "DIGEST_INVALID",
    IO_ERROR: "IO_ERROR",
    BOUNDARY_INVALID: "BOUNDARY_INVALID",
}

MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
MAX_FIXTURE_BYTES = 1 * 1024 * 1024
MAX_AGGREGATE_BYTES = 16 * 1024 * 1024
MAX_DEPTH = 100
MAX_NODES = 100_000
WALL_BOUND_SECONDS = 60

DOMAIN_SEPARATOR = b"xverse.xcom.activation-plan.v1\x00"
DIGEST_HEX = re.compile(r"^[0-9a-f]{64}$")

PROFILE_KINDS = (
    "interface-policy",
    "flow-policy",
    "network-provider",
    "observation-policy",
    "validation-policy",
)
PROFILE_FORM_DEFS = {
    "interface-policy": "interfacePolicy",
    "flow-policy": "flowPolicy",
    "network-provider": "networkProviderPolicy",
    "observation-policy": "observationPolicy",
    "validation-policy": "validationPolicy",
}

REQUIRED_PLAN_MEMBERS = (
    "planVersion",
    "digest",
    "generator",
    "provenance",
    "contracts",
    "endpoints",
    "routes",
    "providers",
    "policies",
    "observationPoints",
    "stimulation",
    "clockDomains",
    "activationOrder",
    "diagnostics",
    "status",
    "inputResolution",
)

# Every required-content group of contracts/communication-plan.md mapped to its plan member.
COMMUNICATION_PLAN_GROUPS = {
    "plan format version": "planVersion",
    "canonical digest": "digest",
    "generator version": "generator",
    "generation time": "provenance",
    "resource identities/api versions/source digests/graph digest": "provenance",
    "communication contracts and schema/version references": "contracts",
    "endpoint roles": "endpoints",
    "route graph": "routes",
    "selected provider ids and capability requirements": "providers",
    "queue/ordering/reliability/deadline/retry/overflow/backpressure policies": "policies",
    "allowed observation points and payload policies": "observationPoints",
    "allowed stimulation actions and permit-policy references": "stimulation",
    "clock domains": "clockDomains",
    "activation order": "activationOrder",
    "deterministic diagnostics": "diagnostics",
}

COLLECTION_KEYS = {
    "contracts": "contractId",
    "endpoints": "endpointId",
    "routes": "routeId",
    "providers": "providerId",
    "observationPoints": "tapId",
    "clockDomains": "clockDomainId",
}

AUTHORIZED_PATH_PREFIXES = (
    "docs/engineering/xcom/t017/",
    "reports/xcom-queue/t017-package.json",
    "specs/007-xcom-core/contracts/xdl-profile.md",
    "specs/007-xcom-core/tasks.md",
    "xdl/profiles/xcom-v0.1.schema.json",
    "src/xverse/xcom/contracts/v1/activation-plan.schema.json",
    "scripts/validate_xcom_plan.py",
    "tests/xcom/activation_plan/",
)

REF002_RECORD_REL = Path("docs/architecture/sads-requirements-traceability.json")
REF002_DIRECT_IDS = tuple(f"XVE-SYS-{number:04d}" for number in range(139, 159))
REF002_PROMOTION_TOKENS = frozenset(
    {"implemented", "verified", "demonstrated", "production", "accepted", "complete", "satisfied"}
)

FORBIDDEN_SOURCE_IMPORTS = (
    "socket",
    "subprocess",
    "http.client",
    "urllib",
    "requests",
    "ftplib",
    "smtplib",
    "telnetlib",
    "asyncio",
)

PUBLIC_SAFETY_PATTERNS = (
    ("absolute host path", re.compile(r"/(?:home|Users|root)/[A-Za-z0-9._-]+")),
    (
        "credential assignment",
        re.compile(r"(?i)(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+"),
    ),
    (
        "private IPv4 address",
        re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"),
    ),
    ("private key marker", re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY")),
)


class Finding(NamedTuple):
    """One classified validation defect."""

    code: int
    message: str


class PlanError(Exception):
    """Raised for an input or dependency failure that maps to one exit class."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def exit_name(code: int) -> str:
    return EXIT_NAMES.get(code, f"UNKNOWN-{code}")


# --------------------------------------------------------------------------------------
# Bounded, read-only input
# --------------------------------------------------------------------------------------


def read_text_bounded(path: Path, *, max_bytes: int = MAX_DOCUMENT_BYTES) -> str:
    """Read a UTF-8 document, failing closed when it exceeds the declared per-file bound."""

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise PlanError(IO_ERROR, f"input unreadable: {path}: {exc}") from exc
    if size > max_bytes:
        raise PlanError(IO_ERROR, f"input {path} is {size} bytes, over the {max_bytes}-byte bound")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PlanError(IO_ERROR, f"input unreadable: {path}: {exc}") from exc
    if len(text.encode("utf-8")) > max_bytes:
        raise PlanError(IO_ERROR, f"input {path} exceeds the {max_bytes}-byte bound")
    return text


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build an object from JSON member pairs, failing closed on a repeated member name."""

    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PlanError(IO_ERROR, f"duplicate JSON member {key!r}")
        result[key] = value
    return result


def parse_json_text(text: str, label: str = "document") -> Any:
    """Parse a JSON document, rejecting malformed JSON and duplicate object members."""

    try:
        return json.loads(text, object_pairs_hook=_pairs_without_duplicates)
    except PlanError as exc:
        raise PlanError(exc.code, f"{label}: {exc.message}") from exc
    except json.JSONDecodeError as exc:
        raise PlanError(IO_ERROR, f"malformed JSON in {label}: {exc}") from exc


def load_json(path: Path, *, max_bytes: int = MAX_DOCUMENT_BYTES) -> Any:
    """Parse a bounded JSON document."""

    return parse_json_text(read_text_bounded(path, max_bytes=max_bytes), str(path))


def measure_shape(value: Any) -> tuple[int, int]:
    """Return (maximum depth, node count) for a parsed JSON value."""

    depth = 0
    nodes = 0
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        current, level = stack.pop()
        nodes += 1
        depth = max(depth, level)
        if isinstance(current, dict):
            for child in current.values():
                stack.append((child, level + 1))
        elif isinstance(current, list):
            for child in current:
                stack.append((child, level + 1))
    return depth, nodes


def check_input_bounds(
    value: Any, *, size_bytes: int | None = None, max_bytes: int = MAX_DOCUMENT_BYTES
) -> list[Finding]:
    """Reject an input that exceeds the declared size, depth, or node bound."""

    findings: list[Finding] = []
    if size_bytes is not None and size_bytes > max_bytes:
        findings.append(Finding(IO_ERROR, f"input size {size_bytes} exceeds {max_bytes}"))
    depth, nodes = measure_shape(value)
    if depth > MAX_DEPTH:
        findings.append(Finding(IO_ERROR, f"input depth {depth} exceeds {MAX_DEPTH}"))
    if nodes > MAX_NODES:
        findings.append(Finding(IO_ERROR, f"input node count {nodes} exceeds {MAX_NODES}"))
    return findings


def check_wall_bound(elapsed_seconds: float, *, bound: float = WALL_BOUND_SECONDS) -> list[Finding]:
    """Reject a run that exceeded the declared wall-clock bound."""

    if elapsed_seconds > bound:
        return [Finding(IO_ERROR, f"elapsed {elapsed_seconds:.3f}s exceeds the {bound}s wall bound")]
    return []


# --------------------------------------------------------------------------------------
# Canonical serialization and digest
# --------------------------------------------------------------------------------------


def _normalize_numbers(value: Any, path: str = "$") -> Any:
    """Emit every mathematically integral number in its single integer form.

    JSON Schema ``integer`` accepts an integral float token such as ``100.0``; the canonical
    serialization contract requires integral numbers without a fraction, so ``100`` and ``100.0``
    must produce identical canonical bytes and therefore the same digest. A non-finite number is
    rejected fail-closed.
    """

    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise PlanError(DIGEST_INVALID, f"non-finite number at {path}")
        if value.is_integer():
            return int(value)
        return value
    if isinstance(value, dict):
        return {key: _normalize_numbers(child, f"{path}/{key}") for key, child in value.items()}
    if isinstance(value, list):
        return [_normalize_numbers(child, f"{path}/{index}") for index, child in enumerate(value)]
    return value


def canonical_bytes(value: Any) -> bytes:
    """Byte-stable canonical encoding: member-name order, no insignificant whitespace."""

    return json.dumps(
        _normalize_numbers(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_body(plan: dict[str, Any]) -> dict[str, Any]:
    """The digested region: the plan value with the top-level digest member removed."""

    return {key: value for key, value in plan.items() if key != "digest"}


def reordered_copy(value: Any) -> Any:
    """Return a copy whose object members are in reverse order (a non-canonical key ordering)."""

    if isinstance(value, dict):
        return {key: reordered_copy(value[key]) for key in reversed(list(value.keys()))}
    if isinstance(value, list):
        return [reordered_copy(item) for item in value]
    return value


def compute_digest(plan: dict[str, Any]) -> str:
    """Domain-separated SHA-256 over the canonical serialization of the plan body."""

    body = canonical_bytes(canonical_body(plan))
    return hashlib.sha256(DOMAIN_SEPARATOR + body).hexdigest()


def check_digest(plan: dict[str, Any]) -> list[Finding]:
    """Reject a missing, malformed, or drifted plan digest."""

    digest = plan.get("digest")
    if not isinstance(digest, dict):
        return [Finding(DIGEST_INVALID, "plan digest member is missing or not an object")]
    if digest.get("algorithm") != "sha256":
        return [Finding(DIGEST_INVALID, "plan digest algorithm must be sha256")]
    value = digest.get("value")
    if not isinstance(value, str) or not DIGEST_HEX.fullmatch(value):
        return [Finding(DIGEST_INVALID, "plan digest value must be 64 lowercase hex characters")]
    try:
        recomputed = compute_digest(plan)
    except PlanError as exc:
        return [Finding(exc.code, exc.message)]
    if recomputed != value:
        return [Finding(DIGEST_INVALID, f"recorded digest {value} does not match recomputed {recomputed}")]
    return []


# --------------------------------------------------------------------------------------
# Schema structure and contract coverage
# --------------------------------------------------------------------------------------


def _closed_findings(node: Any, label: str, path: str = "$") -> list[Finding]:
    findings: list[Finding] = []
    if isinstance(node, dict):
        if node.get("type") == "object" and isinstance(node.get("properties"), dict):
            if node.get("additionalProperties") is not False:
                findings.append(Finding(SCHEMA_INVALID, f"{label}: object at {path} is not closed"))
        for key, child in node.items():
            findings.extend(_closed_findings(child, label, f"{path}/{key}"))
    elif isinstance(node, list):
        for index, child in enumerate(node):
            findings.extend(_closed_findings(child, label, f"{path}/{index}"))
    return findings


def check_schema_structure(schema: Any, label: str = "schema") -> list[Finding]:
    """Assert a valid Draft 2020-12 schema with every object definition closed."""

    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [Finding(SCHEMA_INVALID, f"{label}: not a valid Draft 2020-12 schema: {exc.message}")]
    except Exception as exc:  # pragma: no cover - defensive
        return [Finding(SCHEMA_INVALID, f"{label}: schema check failed: {exc}")]
    return _closed_findings(schema, label)


def check_profile_contract(schema: dict[str, Any]) -> list[Finding]:
    """Check the Profile discriminator, version, and form grammar."""

    findings: list[Finding] = []
    required = set(schema.get("required", []))
    for member in ("schemaVersion", "kind", "target", "policy"):
        if member not in required:
            findings.append(Finding(PROFILE_INVALID, f"profile schema must require {member}"))
    properties = schema.get("properties", {})
    if properties.get("schemaVersion", {}).get("const") != "0.1":
        findings.append(Finding(PROFILE_INVALID, "profile schemaVersion must be const '0.1'"))
    defs = schema.get("$defs", {})
    kinds = defs.get("kind", {}).get("enum")
    if not isinstance(kinds, list) or set(kinds) != set(PROFILE_KINDS) or len(kinds) != len(PROFILE_KINDS):
        findings.append(Finding(PROFILE_INVALID, "profile kind enum must be exactly the five permitted forms"))
    for kind, def_name in PROFILE_FORM_DEFS.items():
        form = defs.get(def_name)
        if not isinstance(form, dict):
            findings.append(Finding(PROFILE_INVALID, f"profile form {kind} must be declared as {def_name}"))
            continue
        if form.get("additionalProperties") is not False:
            findings.append(Finding(PROFILE_INVALID, f"profile form {kind} must be a closed object"))
        if not form.get("required"):
            findings.append(Finding(PROFILE_INVALID, f"profile form {kind} must declare required members"))
    return findings


def check_plan_contract(schema: dict[str, Any]) -> list[Finding]:
    """Check the plan version, required-member coverage, and digest/provenance members."""

    findings: list[Finding] = []
    required = set(schema.get("required", []))
    for member in REQUIRED_PLAN_MEMBERS:
        if member not in required:
            findings.append(Finding(PLAN_INVALID, f"plan schema must require {member}"))
    for group, member in COMMUNICATION_PLAN_GROUPS.items():
        if member not in required:
            findings.append(Finding(PLAN_INVALID, f"plan content group '{group}' is uncovered"))
    properties = schema.get("properties", {})
    if properties.get("planVersion", {}).get("const") != "1":
        findings.append(Finding(PLAN_INVALID, "plan planVersion must be const '1'"))
    status = properties.get("status", {}).get("enum")
    if set(status or []) != {"inspectable", "activatable"}:
        findings.append(Finding(PLAN_INVALID, "plan status must be exactly {inspectable, activatable}"))
    resolution = properties.get("inputResolution", {}).get("$ref")
    if resolution != "#/$defs/inputResolution":
        findings.append(Finding(PLAN_INVALID, "plan inputResolution must reference the declared input-resolution def"))
    else:
        state = schema.get("$defs", {}).get("inputResolution", {})
        if state.get("additionalProperties") is not False:
            findings.append(Finding(PLAN_INVALID, "plan inputResolution must be a closed object"))
        if sorted(state.get("required", [])) != sorted(
            ["identity", "schema", "capability", "time", "ownership", "policy"]
        ):
            findings.append(Finding(PLAN_INVALID, "plan inputResolution must declare the six input states"))
    provenance = schema.get("$defs", {}).get("provenance", {})
    if sorted(provenance.get("required", [])) != sorted(["generatedAt", "graphDigest", "resources"]):
        findings.append(Finding(PLAN_INVALID, "plan provenance must require generatedAt, graphDigest, resources"))
    return findings


# --------------------------------------------------------------------------------------
# Instance validation
# --------------------------------------------------------------------------------------


def _json_schema_findings(
    schema: dict[str, Any], instance: Any, code: int, label: str
) -> list[Finding]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: (list(error.absolute_path), error.message))
    findings: list[Finding] = []
    for error in errors:
        path = "/".join(str(part) for part in error.absolute_path)
        findings.append(Finding(code, f"{label} invalid at {path or '<root>'}: {error.message}"))
    return findings


def validate_profile_payload(payload: Any, schema: dict[str, Any]) -> list[Finding]:
    """Validate one Profile payload against the closed v0.1 schema."""

    if not isinstance(payload, dict):
        return [Finding(PROFILE_INVALID, "profile payload must be an object")]
    return _json_schema_findings(schema, payload, PROFILE_INVALID, "profile payload")


def _target_identity(payload: Any) -> tuple[Any, ...] | None:
    if not isinstance(payload, dict):
        return None
    target = payload.get("target")
    if not isinstance(target, dict):
        return None
    return (
        target.get("apiVersion"),
        target.get("kind"),
        target.get("namespace"),
        target.get("name"),
        target.get("version"),
    )


def validate_profile_set(payloads: list[Any], schema: dict[str, Any]) -> list[Finding]:
    """Validate a set of Profile payloads and reject a duplicate/conflicting attachment."""

    findings: list[Finding] = []
    seen: dict[tuple[Any, ...], str] = {}
    for payload in payloads:
        findings.extend(validate_profile_payload(payload, schema))
        identity = _target_identity(payload)
        if identity is None:
            continue
        if identity in seen:
            findings.append(
                Finding(PROFILE_INVALID, f"conflicting Profile payloads for decorated identity {identity}")
            )
        else:
            seen[identity] = str(payload.get("kind"))
    return findings


def _order_token(value: Any) -> Any:
    """Map one identity element to a totally orderable, hashable token.

    An absent optional member (``None``) sorts before any string and never conflates with the empty
    string. This keeps the ordering/uniqueness check total over schema-valid inputs that mix present
    and absent optional members (for example a provenance resource whose optional ``version`` is
    declared on exactly one of two otherwise identical identities); without it ``sorted`` raises
    ``TypeError`` and the declared ``PLAN_INVALID`` rejection is never reached (T017-IR-008).
    """

    if isinstance(value, tuple):
        return tuple((0, "") if element is None else (1, str(element)) for element in value)
    return (0, "") if value is None else (1, str(value))


def _is_sorted(values: list[Any]) -> bool:
    tokens = [_order_token(value) for value in values]
    return tokens == sorted(tokens)


def check_ordering(plan: dict[str, Any]) -> list[Finding]:
    """Enforce deterministic collection order and unique identifiers."""

    findings: list[Finding] = []
    endpoint_ids = set()
    route_ids = set()

    for collection, key in COLLECTION_KEYS.items():
        items = plan.get(collection)
        if not isinstance(items, list):
            findings.append(Finding(PLAN_INVALID, f"plan collection {collection} must be an array"))
            continue
        keys: list[str] = []
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get(key), str):
                findings.append(Finding(PLAN_INVALID, f"plan {collection} entry must carry a string {key}"))
                continue
            keys.append(item[key])
        if len(keys) != len(set(keys)):
            findings.append(Finding(PLAN_INVALID, f"plan {collection} carries a duplicate {key}"))
        if not _is_sorted(keys):
            findings.append(Finding(PLAN_INVALID, f"plan {collection} is not ordered by {key}"))
        if collection == "endpoints":
            endpoint_ids = set(keys)
        if collection == "routes":
            route_ids = set(keys)

    diagnostics = plan.get("diagnostics")
    if isinstance(diagnostics, list):
        diag_keys = [
            (entry.get("code"), entry.get("targetId"))
            for entry in diagnostics
            if isinstance(entry, dict)
        ]
        if len(diag_keys) != len(set(diag_keys)):
            findings.append(Finding(PLAN_INVALID, "plan diagnostics carries a duplicate (code, targetId)"))
        if not _is_sorted(diag_keys):
            findings.append(Finding(PLAN_INVALID, "plan diagnostics is not ordered by (code, targetId)"))

    provenance = plan.get("provenance")
    if isinstance(provenance, dict) and isinstance(provenance.get("resources"), list):
        resource_keys = [
            (
                entry.get("apiVersion"),
                entry.get("kind"),
                entry.get("namespace"),
                entry.get("name"),
                entry.get("version"),
            )
            for entry in provenance["resources"]
            if isinstance(entry, dict)
        ]
        if len(resource_keys) != len(set(resource_keys)):
            findings.append(Finding(PLAN_INVALID, "plan provenance resources carries a duplicate identity"))
        if not _is_sorted(resource_keys):
            findings.append(Finding(PLAN_INVALID, "plan provenance resources is not ordered by identity"))

    order = plan.get("activationOrder")
    if isinstance(order, list):
        if len(order) != len(set(order)):
            findings.append(Finding(PLAN_INVALID, "plan activationOrder carries a duplicate entry"))
        declared = endpoint_ids | route_ids
        undeclared = [entry for entry in order if entry not in declared]
        if undeclared:
            findings.append(
                Finding(
                    PLAN_INVALID,
                    f"plan activationOrder names undeclared ids {sorted(undeclared, key=_order_token)}",
                )
            )

    return findings


def validate_plan_structure(plan: Any, schema: dict[str, Any]) -> list[Finding]:
    """Validate plan required-content, closedness, ordering, and the inspectable rule."""

    if not isinstance(plan, dict):
        return [Finding(PLAN_INVALID, "plan must be an object")]
    findings = _json_schema_findings(schema, plan, PLAN_INVALID, "plan")
    # Ordering is only meaningful once the collection shapes are otherwise valid.
    if not findings:
        findings.extend(check_ordering(plan))
    return findings


# --------------------------------------------------------------------------------------
# Boundary, public-safety, and offline-source rules
# --------------------------------------------------------------------------------------


def check_authorized_paths(paths: list[str]) -> list[Finding]:
    """Reject a candidate change outside the T017-authorized path set."""

    findings: list[Finding] = []
    for path in paths:
        if not any(path == prefix or path.startswith(prefix) for prefix in AUTHORIZED_PATH_PREFIXES):
            findings.append(Finding(BOUNDARY_INVALID, f"candidate path is not authorized for T017: {path}"))
    return findings


def load_changed_paths(path: Path) -> list[str]:
    """Read a caller-supplied candidate changed-path list, one repository-relative path per line."""

    paths: list[str] = []
    for line in read_text_bounded(path).splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            paths.append(stripped)
    return paths


def check_ref002(entries: list[Any]) -> list[Finding]:
    """Reject the authoritative REF-002 record if any direct communication target is promoted.

    The record is the machine-readable allocation shared with the program register; a target is
    promoted when its disposition or maturity leaves the accepted ``allocated``/``deferred``
    ``architectural-target`` state. Every one of the twenty direct communication IDs must be present.
    """

    findings: list[Finding] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        source_id = entry.get("source_id")
        if source_id not in REF002_DIRECT_IDS:
            continue
        seen.add(source_id)
        disposition = str(entry.get("disposition", "")).strip().lower()
        maturity = str(entry.get("maturity", "")).strip().lower()
        if disposition in REF002_PROMOTION_TOKENS or maturity in REF002_PROMOTION_TOKENS:
            findings.append(
                Finding(BOUNDARY_INVALID, f"REF-002 {source_id} is promoted ({disposition}/{maturity})")
            )
    missing = sorted(set(REF002_DIRECT_IDS) - seen)
    if missing:
        findings.append(Finding(BOUNDARY_INVALID, f"REF-002 record omits direct communication ids {missing}"))
    return findings


def check_public_safety(text: str, label: str = "content") -> list[Finding]:
    """Reject a public-safety leak in a declared artifact."""

    findings: list[Finding] = []
    for name, pattern in PUBLIC_SAFETY_PATTERNS:
        match = pattern.search(text)
        if match:
            findings.append(Finding(BOUNDARY_INVALID, f"{label}: {name} detected"))
    return findings


def check_offline_source(source: str, label: str = "validator source") -> list[Finding]:
    """Reject a source file that imports a network or child-process module."""

    findings: list[Finding] = []
    for module in FORBIDDEN_SOURCE_IMPORTS:
        pattern = re.compile(rf"^\s*(?:import|from)\s+{re.escape(module)}\b", re.MULTILINE)
        if pattern.search(source):
            findings.append(Finding(SCHEMA_INVALID, f"{label}: forbidden import of {module}"))
    return findings


def check_stage(*, checkbox_marked: bool, implementation_present: bool) -> list[Finding]:
    """Reject a plan-stage candidate that marks the task complete before implementation."""

    if checkbox_marked and not implementation_present:
        return [Finding(BOUNDARY_INVALID, "task checkbox is marked before the implementation work product exists")]
    return []


# --------------------------------------------------------------------------------------
# Whole-repository verification
# --------------------------------------------------------------------------------------


def _positive_profile_payloads(root: Path) -> list[tuple[Path, Any]]:
    directory = root / FIXTURES_REL / "profile" / "valid"
    return [(path, load_json(path)) for path in sorted(directory.glob("*.json"))]


def _positive_plans(root: Path) -> list[tuple[Path, Any]]:
    directory = root / FIXTURES_REL / "plan" / "valid"
    return [(path, load_json(path)) for path in sorted(directory.glob("*.json"))]


def _task_checkbox_marked(root: Path) -> bool:
    match = re.search(r"^- \[([ Xx])\] T017\b", (root / TASKS_REL).read_text(encoding="utf-8"), re.MULTILINE)
    return bool(match and match.group(1).lower() == "x")


def run_checks(root: Path = ROOT, changed_paths: list[str] | None = None) -> list[Finding]:
    """Run every positive and structural check against the real repository artifacts.

    ``changed_paths`` is the caller-supplied candidate changed-path set. The validator is offline and
    starts no child process, so it cannot derive the Git diff itself; when the caller supplies the set
    (for example ``--verify --changed-paths <file>``) the authorized-path boundary is checked against
    the real candidate. The deterministic gate performs the same boundary check externally with
    ``git diff --name-only``; no boundary is claimed when no set is supplied.
    """

    start = time.monotonic()
    findings: list[Finding] = []
    try:
        profile_schema = load_json(root / PROFILE_SCHEMA_REL)
        plan_schema = load_json(root / PLAN_SCHEMA_REL)
    except PlanError as exc:
        return [Finding(exc.code, exc.message)]

    findings.extend(check_schema_structure(profile_schema, "profile schema"))
    findings.extend(check_schema_structure(plan_schema, "plan schema"))
    findings.extend(check_profile_contract(profile_schema))
    findings.extend(check_plan_contract(plan_schema))
    findings.extend(
        check_input_bounds(
            profile_schema, size_bytes=(root / PROFILE_SCHEMA_REL).stat().st_size, max_bytes=MAX_DOCUMENT_BYTES
        )
    )
    findings.extend(
        check_input_bounds(
            plan_schema, size_bytes=(root / PLAN_SCHEMA_REL).stat().st_size, max_bytes=MAX_DOCUMENT_BYTES
        )
    )

    aggregate = 0
    try:
        profiles = _positive_profile_payloads(root)
        plans = _positive_plans(root)
    except PlanError as exc:
        return [Finding(exc.code, exc.message)]

    for path, payload in profiles:
        size = path.stat().st_size
        aggregate += size
        findings.extend(check_input_bounds(payload, size_bytes=size, max_bytes=MAX_FIXTURE_BYTES))
        findings.extend(validate_profile_payload(payload, profile_schema))
    findings.extend(validate_profile_set([payload for _, payload in profiles], profile_schema))

    for path, plan in plans:
        size = path.stat().st_size
        aggregate += size
        findings.extend(check_input_bounds(plan, size_bytes=size, max_bytes=MAX_FIXTURE_BYTES))
        findings.extend(validate_plan_structure(plan, plan_schema))
        findings.extend(check_digest(plan))

    if aggregate > MAX_AGGREGATE_BYTES:
        findings.append(Finding(IO_ERROR, f"aggregate fixture size {aggregate} exceeds {MAX_AGGREGATE_BYTES}"))

    artifact_paths = [root / PROFILE_SCHEMA_REL, root / PLAN_SCHEMA_REL]
    artifact_paths.extend(path for path, _ in profiles)
    artifact_paths.extend(path for path, _ in plans)
    for path in artifact_paths:
        try:
            text = read_text_bounded(path)
        except PlanError as exc:
            findings.append(Finding(exc.code, exc.message))
            continue
        findings.extend(check_public_safety(text, path.name))

    try:
        findings.extend(check_offline_source(read_text_bounded(SELF_SOURCE)))
    except PlanError as exc:
        findings.append(Finding(exc.code, exc.message))

    if changed_paths is not None:
        findings.extend(check_authorized_paths(list(changed_paths)))

    try:
        ref_record = load_json(root / REF002_RECORD_REL)
    except PlanError as exc:
        findings.append(Finding(exc.code, exc.message))
    else:
        requirements = ref_record.get("requirements") if isinstance(ref_record, dict) else None
        if not isinstance(requirements, list):
            findings.append(Finding(BOUNDARY_INVALID, "REF-002 record must carry a requirements array"))
        else:
            findings.extend(check_ref002(requirements))

    findings.extend(
        check_stage(
            checkbox_marked=_task_checkbox_marked(root),
            implementation_present=(root / DOCS_REL / "implementation.md").is_file(),
        )
    )
    findings.extend(check_wall_bound(time.monotonic() - start))
    return findings


def exit_code(findings: list[Finding]) -> int:
    if not findings:
        return OK
    return min(finding.code for finding in findings)


def verify_summary(root: Path = ROOT) -> str:
    plan_schema = load_json(root / PLAN_SCHEMA_REL)
    profile_schema = load_json(root / PROFILE_SCHEMA_REL)
    return (
        "X-COM activation-plan validation passed: "
        f"profileKinds={len(profile_schema['$defs']['kind']['enum'])} "
        f"planMembers={len(plan_schema['required'])} "
        f"collections={len(COLLECTION_KEYS)} "
        f"digestVectors={len(_positive_plans(root))} "
        f"exitClasses={len(EXIT_NAMES) - 1}"
    )


# --------------------------------------------------------------------------------------
# Negative cases
# --------------------------------------------------------------------------------------


def _copies(root: Path) -> dict[str, Any]:
    bases: dict[str, Any] = {}
    for path, payload in _positive_profile_payloads(root):
        bases[path.stem] = json.loads(json.dumps(payload))
    for path, plan in _positive_plans(root):
        bases[path.stem] = json.loads(json.dumps(plan))
    return bases


def parse_probe(text: str, label: str = "probe document") -> list[Finding]:
    """Return the finding for a document the parser must reject, or [] when it is accepted."""

    try:
        parse_json_text(text, label)
    except PlanError as exc:
        return [Finding(exc.code, exc.message)]
    return []


def deep_probe_value(depth: int = MAX_DEPTH + 1) -> Any:
    """Build a probe document that exceeds the declared nesting-depth bound."""

    value: Any = {"leaf": 1}
    for _ in range(depth):
        value = {"n": value}
    return value


def negative_cases(root: Path = ROOT) -> list[tuple[str, int, Callable[[], list[Finding]]]]:
    """Return the declared controlled negative cases as (id, expected exit, check)."""

    profile_schema = load_json(root / PROFILE_SCHEMA_REL)
    plan_schema = load_json(root / PLAN_SCHEMA_REL)
    ref_requirements = load_json(root / REF002_RECORD_REL)["requirements"]
    bases = _copies(root)
    interface = bases["interface-policy"]
    flow = bases["flow-policy"]
    network = bases["network-provider"]
    observation = bases["observation-policy"]
    validation = bases["validation-policy"]
    plan = bases["plan-activatable"]
    plan = json.loads(json.dumps(plan))
    plan["digest"]["value"] = compute_digest(plan)
    inspectable = bases["plan-inspectable"]

    def mutate(base: dict[str, Any], change: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
        value = json.loads(json.dumps(base))
        change(value)
        return value

    cases: list[tuple[str, int, Callable[[], list[Finding]]]] = []

    def profile_case(case_id: str, base: dict[str, Any], change: Callable[[dict[str, Any]], None]) -> None:
        cases.append((case_id, PROFILE_INVALID, lambda: validate_profile_payload(mutate(base, change), profile_schema)))

    profile_case("NEG-P01", interface, lambda p: p.pop("schemaVersion"))
    profile_case("NEG-P02", interface, lambda p: p.__setitem__("schemaVersion", "0.2"))
    profile_case("NEG-P03", interface, lambda p: p.pop("kind"))
    profile_case("NEG-P04", interface, lambda p: p.__setitem__("kind", "unknown-policy"))
    profile_case("NEG-P05", interface, lambda p: p.__setitem__("unknownField", 1))
    profile_case("NEG-P06", interface, lambda p: p["policy"].pop("interactionKind"))
    profile_case("NEG-P07", flow, lambda p: p["policy"].__setitem__("overflow", "unknown-token"))
    profile_case("NEG-P08", network, lambda p: p["policy"].pop("requiredCapabilities"))
    profile_case("NEG-P09", observation, lambda p: p["policy"].__setitem__("payloadAccess", "allow-listed"))
    profile_case(
        "NEG-P10",
        validation,
        lambda p: (p["policy"].__setitem__("serviceEmulation", True), p["policy"].pop("permitPolicyRef")),
    )
    profile_case("NEG-P11", interface, lambda p: p["policy"].__setitem__("unknownMember", 1))
    profile_case("NEG-P12", interface, lambda p: p.__setitem__("providerAddress", "127.0.0.1"))
    profile_case("NEG-P13", interface, lambda p: p["policy"].__setitem__("permit", "permit-1"))
    conflicting = mutate(flow, lambda p: p.__setitem__("target", json.loads(json.dumps(interface["target"]))))
    cases.append(
        (
            "NEG-P14",
            PROFILE_INVALID,
            lambda: validate_profile_set([mutate(interface, lambda _p: None), conflicting], profile_schema),
        )
    )

    def plan_case(case_id: str, change: Callable[[dict[str, Any]], None], base: dict[str, Any] | None = None) -> None:
        source = plan if base is None else base
        cases.append((case_id, PLAN_INVALID, lambda: validate_plan_structure(mutate(source, change), plan_schema)))

    plan_case("NEG-A01", lambda p: p.pop("planVersion"))
    plan_case("NEG-A02", lambda p: p.__setitem__("planVersion", "2"))
    plan_case("NEG-A03", lambda p: p.pop("clockDomains"))
    plan_case("NEG-A04", lambda p: p.__setitem__("unknownField", 1))
    plan_case("NEG-A05", lambda p: p.pop("routes"))
    plan_case("NEG-A06", lambda p: p.pop("activationOrder"))
    plan_case("NEG-A07", lambda p: p.pop("policies"))
    plan_case("NEG-A08", lambda p: p.pop("diagnostics"))
    plan_case(
        "NEG-A09",
        lambda p: (p.__setitem__("status", "activatable"), p["inputResolution"].__setitem__("time", "unresolved")),
    )
    cases.append(
        (
            "NEG-A10",
            OK,
            lambda: validate_plan_structure(mutate(inspectable, lambda _p: None), plan_schema),
        )
    )
    plan_case(
        "NEG-A11",
        lambda p: p["routes"].append(
            {"routeId": "route-ctrl", "from": "plant-a", "to": "controller-a", "contractId": "contract-ctrl"}
        ),
    )
    plan_case("NEG-A12", lambda p: p.__setitem__("endpoints", list(reversed(p["endpoints"]))))
    plan_case("NEG-A13", lambda p: p.__setitem__("activationOrder", ["controller-a", "controller-a"]))
    plan_case("NEG-A14", lambda p: p.pop("digest"))
    plan_case("NEG-A15", lambda p: p.pop("provenance"))
    plan_case("NEG-A16", lambda p: p["provenance"].pop("graphDigest"))
    plan_case("NEG-A17", lambda p: p.__setitem__("activationOrder", ["controller-a", "route-undeclared"]))
    plan_case(
        "NEG-A18",
        lambda p: p["diagnostics"].append(
            {"code": "XCOM-PLAN-AA", "severity": "info", "targetId": "route-ctrl"}
        ),
    )
    plan_case("NEG-A19", lambda p: p["provenance"]["resources"].reverse())
    plan_case(
        "NEG-A20",
        lambda p: p["diagnostics"].append(json.loads(json.dumps(p["diagnostics"][0]))),
    )
    plan_case(
        "NEG-A21",
        lambda p: p["provenance"]["resources"].append(
            json.loads(json.dumps(p["provenance"]["resources"][0]))
        ),
    )
    plan_case(
        "NEG-A22",
        lambda p: p["provenance"]["resources"].append(
            {
                "apiVersion": "xverse.io/xdl/v1alpha1",
                "kind": "Component",
                "namespace": "xcom",
                "name": "plant-a",
                "sourceDigest": {
                    "algorithm": "sha256",
                    "value": "3333333333333333333333333333333333333333333333333333333333333333",
                },
            }
        ),
    )

    def naive_bytes(value: Any) -> bytes:
        return json.dumps(value, sort_keys=False, separators=(", ", ": "), ensure_ascii=False).encode("utf-8")

    def d01() -> list[Finding]:
        # A digest recorded over a non-canonical (reversed key-order, whitespace) serialization of
        # the same body: the domain separator is correct, so only the ordering defect is exercised.
        candidate = json.loads(json.dumps(plan))
        body = reordered_copy(canonical_body(candidate))
        candidate["digest"]["value"] = hashlib.sha256(DOMAIN_SEPARATOR + naive_bytes(body)).hexdigest()
        return check_digest(candidate)

    def d02() -> list[Finding]:
        candidate = json.loads(json.dumps(plan))
        candidate["digest"]["value"] = hashlib.sha256(canonical_bytes(canonical_body(candidate))).hexdigest()
        return check_digest(candidate)

    def d03() -> list[Finding]:
        candidate = json.loads(json.dumps(plan))
        candidate["digest"]["value"] = compute_digest(candidate)
        candidate["generator"]["version"] = "0.2.0"
        return check_digest(candidate)

    def d04() -> list[Finding]:
        candidate = json.loads(json.dumps(plan))
        candidate["digest"]["value"] = hashlib.sha256(
            DOMAIN_SEPARATOR + canonical_bytes(candidate)
        ).hexdigest()
        return check_digest(candidate)

    cases.extend(
        [
            ("NEG-D01", DIGEST_INVALID, d01),
            ("NEG-D02", DIGEST_INVALID, d02),
            ("NEG-D03", DIGEST_INVALID, d03),
            ("NEG-D04", DIGEST_INVALID, d04),
        ]
    )

    cases.extend(
        [
            (
                "NEG-V01",
                SCHEMA_INVALID,
                lambda: check_schema_structure({"type": "not-a-real-type"}, "probe schema"),
            ),
            (
                "NEG-V02",
                SCHEMA_INVALID,
                lambda: check_schema_structure(
                    {"type": "object", "properties": {"a": {"type": "string"}}}, "probe schema"
                ),
            ),
            ("NEG-V03", SCHEMA_INVALID, lambda: check_offline_source("import socket\n", "probe source")),
            ("NEG-V04", IO_ERROR, lambda: check_input_bounds({"a": 1}, size_bytes=MAX_DOCUMENT_BYTES + 1)),
            ("NEG-V05", IO_ERROR, lambda: parse_probe('{"a": 1, "a": 2}')),
            (
                "NEG-V06",
                IO_ERROR,
                lambda: check_input_bounds(
                    {"kind": "interface-policy"}, size_bytes=MAX_FIXTURE_BYTES + 1, max_bytes=MAX_FIXTURE_BYTES
                ),
            ),
            ("NEG-V07", IO_ERROR, lambda: check_input_bounds(deep_probe_value())),
            ("NEG-V08", IO_ERROR, lambda: check_wall_bound(WALL_BOUND_SECONDS + 1)),
        ]
    )

    cases.extend(
        [
            ("NEG-G01", BOUNDARY_INVALID, lambda: check_authorized_paths(["src/xverse_xdl/xcom_plan.py"])),
            (
                "NEG-G02",
                BOUNDARY_INVALID,
                lambda: check_authorized_paths(["src/xverse/xcom/src/activation_plan.cpp"]),
            ),
            (
                "NEG-G03",
                BOUNDARY_INVALID,
                lambda: check_ref002(
                    [
                        dict(entry, disposition="implemented", maturity="implemented")
                        if entry.get("source_id") == "XVE-SYS-0139"
                        else entry
                        for entry in ref_requirements
                    ]
                ),
            ),
            (
                "NEG-G04",
                BOUNDARY_INVALID,
                lambda: check_public_safety("path=/home/agent/secret\npassword = hunter2\n", "probe"),
            ),
            (
                "NEG-G05",
                BOUNDARY_INVALID,
                lambda: check_stage(checkbox_marked=True, implementation_present=False),
            ),
        ]
    )
    return cases


def self_test(root: Path = ROOT) -> int:
    """Run the positive check and every declared negative case; return an exit class."""

    positive = run_checks(root)
    if positive:
        print(f"positive artifacts: {exit_name(exit_code(positive))} (exit {exit_code(positive)})")
        for finding in positive:
            print(f"  {exit_name(finding.code)}: {finding.message}")
        return exit_code(positive)

    print("positive artifacts: passed")
    declared = negative_cases(root)
    class_counts: dict[int, int] = {}
    for case_id, expected, check in declared:
        findings = check()
        codes = {finding.code for finding in findings}
        if expected == OK:
            if findings:
                print(f"{case_id}: expected acceptance, got {sorted(codes)}")
                return exit_code(findings)
            class_counts[OK] = class_counts.get(OK, 0) + 1
            print(f"{case_id}: {exit_name(OK)} (exit {OK})")
            continue
        if expected not in codes:
            print(f"{case_id}: expected {exit_name(expected)} (exit {expected}), got {sorted(codes) or 'no finding'}")
            return expected
        class_counts[expected] = class_counts.get(expected, 0) + 1
        print(f"{case_id}: {exit_name(expected)} (exit {expected})")
    summary = " ".join(f"{exit_name(code)}={class_counts[code]}" for code in sorted(class_counts))
    print(f"cases={len(declared)} {summary}")
    print("X-COM activation-plan self-test passed")
    return OK


def human_summary(root: Path = ROOT) -> str:
    """Deterministic human-readable contract summary."""

    profile_schema = load_json(root / PROFILE_SCHEMA_REL)
    plan_schema = load_json(root / PLAN_SCHEMA_REL)
    lines = [
        "task=T017",
        f"profileSchema={PROFILE_SCHEMA_REL.as_posix()}",
        f"planSchema={PLAN_SCHEMA_REL.as_posix()}",
        f"profileKinds={len(profile_schema['$defs']['kind']['enum'])}",
        f"planRequiredMembers={len(plan_schema['required'])}",
        f"planCollections={len(COLLECTION_KEYS)}",
        "digestAlgorithm=sha256",
        f"digestDomainSeparator={DOMAIN_SEPARATOR[:-1].decode('ascii')}",
        f"digestVectors={len(_positive_plans(root))}",
        f"exitClasses={len(EXIT_NAMES) - 1}",
    ]
    return "\n".join(lines) + "\n"


def check_human(root: Path = ROOT) -> int:
    """Assert the committed human-readable summary matches the artifacts."""

    try:
        expected = read_text_bounded(root / EXPECTED_SUMMARY_REL)
    except PlanError as exc:
        print(f"{exit_name(exc.code)}: {exc.message}")
        return exc.code
    actual = human_summary(root)
    if actual != expected:
        print(f"{exit_name(BOUNDARY_INVALID)}: human summary drift")
        return BOUNDARY_INVALID
    print("human summary: consistent")
    return OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--verify", action="store_true", help="check the real artifacts and fixtures")
    group.add_argument("--self-test", action="store_true", help="run the controlled negative cases")
    group.add_argument("--check-human", action="store_true", help="check the committed human summary")
    parser.add_argument(
        "--changed-paths",
        metavar="FILE",
        default=None,
        help="with --verify, read the candidate changed-path set and check the authorized boundary",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        return self_test()
    if args.check_human:
        return check_human()
    changed_paths: list[str] | None = None
    if args.changed_paths:
        try:
            changed_paths = load_changed_paths(Path(args.changed_paths))
        except PlanError as exc:
            print(f"{exit_name(exc.code)}: {exc.message}")
            return exc.code
    try:
        findings = run_checks(changed_paths=changed_paths)
    except PlanError as exc:
        findings = [Finding(exc.code, exc.message)]
    if findings:
        for finding in findings:
            print(f"{exit_name(finding.code)}: {finding.message}")
        return exit_code(findings)
    print(verify_summary())
    return OK


if __name__ == "__main__":
    sys.exit(main())
