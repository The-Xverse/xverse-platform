"""Frozen evidence schemas, canonical serialization and closed-field validation.

Owns the event-record schema (``eventSchemaVersion = "1.0"``) and manifest schema
(``manifestVersion = "1.0"``) of ``detailed-design.md`` sections 2-4. Serialization is canonical
(sorted keys, compact separators, ``allow_nan=False``). Unknown fields are rejected outside
``extensions`` and preserved verbatim inside it. No I/O is performed here.
"""

from __future__ import annotations

import json
import math
import re
from collections import deque
from typing import Any

from .diagnostics import EvidenceDiagnostic, EvidenceError, diagnostic
from .limits import EvidenceLimits

__all__ = [
    "ANNOTATION_KEYS",
    "ARTIFACT_ENTRY_KEYS",
    "CLOCK_KEYS",
    "EVENT_KEYS",
    "EVENT_KINDS",
    "EVENT_SCHEMA_VERSION",
    "EXTENSION_NAMESPACE_PATTERN",
    "MANIFEST_VERSION",
    "MAX_JSON_NESTING",
    "OBLIGATION_KEYS",
    "OBLIGATION_KINDS",
    "OBSERVATION_KEYS",
    "SNAPSHOT_KEYS",
    "WRITER_EMITTED_KINDS",
    "canonical_bytes",
    "canonical_json",
    "find_nonfinite",
    "json_depth_exceeded",
    "json_text_depth_exceeded",
    "parse_json_bounded",
    "parse_major",
    "reject_unknown_keys",
    "require_supported_major",
    "validate_extensions",
]

EVENT_SCHEMA_VERSION = "1.0"
MANIFEST_VERSION = "1.0"
PROJECTION_VERSION = "1.0"
UPSTREAM_CONTRACT_VERSION = "1.0.0"
SNAPSHOT_VERSION = "1.0"
ARGUS_VERSION = "0.1.0"

EVENT_KINDS = ("run-opened", "run-closed", "run-failed", "observation", "snapshot", "annotation")
WRITER_EMITTED_KINDS = ("run-opened", "run-closed", "run-failed")
OBLIGATION_KINDS = ("causal-closure", "interval-closure", "no-known-loss", "min-observations")

EVENT_KEYS = (
    "schemaVersion",
    "runId",
    "eventId",
    "producerId",
    "ingestionOrdinal",
    "eventKind",
    "producerSequence",
    "correlationId",
    "causationId",
    "clocks",
    "observation",
    "snapshot",
    "annotation",
    "extensions",
)
OBSERVATION_KEYS = (
    "contractId",
    "contractVersion",
    "interfaceId",
    "endpointId",
    "schemaId",
    "schemaVersion",
    "interactionKind",
    "origin",
    "sourceClock",
    "observationClock",
    "sequence",
    "correlationId",
    "causationId",
    "routeId",
    "providerId",
    "sourcePayloadSize",
    "providerOutcome",
    "payloadViewState",
    "payloadSchemaState",
    "visibleBytesHex",
    "visibleByteCount",
    "tapId",
    "counters",
    "extensions",
)
SNAPSHOT_KEYS = (
    "snapshotVersion",
    "handle",
    "queued",
    "accepted",
    "dropped",
    "coalesced",
    "backpressureRejections",
    "experimentValidityDegraded",
    "declaredTapId",
    "validityEffect",
    "validityState",
    "intervalProvenance",
    "extensions",
)
CLOCK_KEYS = ("domain", "unit", "value")
ANNOTATION_KEYS = ("text",)
ARTIFACT_ENTRY_KEYS = ("path", "mediaType", "schemaVersion", "bytes", "sha256", "role")
OBLIGATION_KEYS = ("obligationId", "kind", "required", "detail")

EXTENSION_NAMESPACE_PATTERN = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
_VERSION_PATTERN = re.compile(r"^([0-9]+)\.([0-9]+)$")

# Internal defensive JSON nesting bound (not a caller-configured ``EvidenceLimits`` field and not a
# scientific or safety threshold). Python's ``json`` encoder/decoder and ``copy.deepcopy`` recurse,
# so a small but deeply nested payload can raise an uncaught ``RecursionError`` instead of a stable
# diagnostic. Every manifest, event-line and admitted caller value is checked against this finite
# bound *iteratively* before any recursive operation, so a damaged or hostile input is rejected
# deterministically as bounded data and no recursion error can escape (``AR-RVW-001``).
MAX_JSON_NESTING = 128
_DEPTH_MESSAGE = "JSON nesting exceeds the bounded maximum depth"


def json_depth_exceeded(value: Any, *, maximum: int = MAX_JSON_NESTING) -> bool:
    """Return whether a parsed JSON-like value nests deeper than ``maximum`` (iterative, no recursion).

    A container that reappears on the current descent path is a circular reference; it is reported as
    exceeding the bound so the caller rejects it with a stable diagnostic rather than hanging, and the
    traversal always terminates (``AR-RVW-001``).
    """

    stack: list[tuple[Any, int, bool]] = [(value, 1, False)]
    path: set[int] = set()
    while stack:
        item, depth, exiting = stack.pop()
        if exiting:
            path.discard(id(item))
            continue
        if depth > maximum:
            return True
        if isinstance(item, (dict, list, tuple)):
            identity = id(item)
            if identity in path:
                return True
            path.add(identity)
            stack.append((item, depth, True))
            members = item.values() if isinstance(item, dict) else item
            for member in members:
                if isinstance(member, (dict, list, tuple)):
                    stack.append((member, depth + 1, False))
    return False


def json_text_depth_exceeded(text: str, *, maximum: int = MAX_JSON_NESTING) -> bool:
    """Return whether raw JSON ``text`` nests deeper than ``maximum`` without decoding it.

    The scan is linear and ignores brackets inside JSON strings (honouring backslash escapes), so an
    adversarially deep document is refused *before* ``json.loads`` can recurse into a ``RecursionError``.
    """

    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "{[":
            depth += 1
            if depth > maximum:
                return True
        elif character in "}]":
            depth -= 1
    return False


def parse_json_bounded(text: str, *, maximum: int = MAX_JSON_NESTING) -> Any:
    """Parse JSON text with a pre-decoded nesting bound; raise ``ValueError`` instead of recursing.

    A too-deep document is rejected with ``ValueError`` before ``json.loads`` so the caller can map it
    to one stable bounded diagnostic. A residual ``RecursionError`` (e.g. a platform with a lower
    recursion limit) is also converted to ``ValueError`` so no recursion exception escapes.
    """

    if json_text_depth_exceeded(text, maximum=maximum):
        raise ValueError(_DEPTH_MESSAGE)
    def unique_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON object member")
            result[key] = value
        return result

    try:
        return json.loads(text, object_pairs_hook=unique_members)
    except RecursionError:
        raise ValueError(_DEPTH_MESSAGE) from None

INTERACTION_KINDS = ("signal_state_update", "message_event", "service_request", "service_response")
ORIGIN_KINDS = ("component", "validation_tool", "replay", "provider_generated")
PROVIDER_OUTCOMES = ("not_attempted", "accepted", "rejected")
PAYLOAD_VIEW_STATES = ("omitted", "complete", "truncated", "redacted")
VALIDITY_EFFECTS = ("none", "degrade_on_loss", "invalidate_on_loss")
VALIDITY_STATES = ("valid", "degraded", "invalid")
INTERVAL_CLOSURES = ("closed", "unclosed", "unavailable")


def canonical_json(value: Any) -> str:
    """Return the canonical JSON text: sorted keys, compact separators, no NaN/Infinity.

    Excessive nesting is rejected with ``ValueError`` *before* the recursive encoder runs, and any
    residual encoder ``RecursionError`` is converted to the same ``ValueError``, so callers always see
    a stable bounded failure instead of an uncaught recursion error (``AR-RVW-001``).
    """

    if json_depth_exceeded(value):
        raise ValueError(_DEPTH_MESSAGE)
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        )
    except RecursionError:
        raise ValueError(_DEPTH_MESSAGE) from None


def canonical_bytes(value: Any) -> bytes:
    """Return the canonical UTF-8 bytes of a JSON-compatible value."""

    return canonical_json(value).encode("utf-8")


def find_nonfinite(value: Any, *, max_reports: int = 1) -> list[EvidenceDiagnostic]:
    """Return bounded ``ARGUS2-INPUT-NONFINITE`` diagnostics for NaN/Infinity anywhere in ``value``.

    ``json.loads`` accepts the non-standard ``NaN``/``Infinity``/``-Infinity`` tokens, and an
    overflowing literal such as ``1e400`` parses to ``inf``; a damaged manifest can therefore carry a
    non-finite number at any depth. The reader rejects such content before it is assessed or exported
    so no non-finite value ever enters the trusted result and no ``allow_nan=False`` serialization
    error escapes later. The scan is iterative (no unbounded recursion on hostile nesting) and bounded
    by ``max_reports`` so damaged input cannot amplify diagnostics.
    """

    diagnostics: list[EvidenceDiagnostic] = []
    if max_reports is None or max_reports <= 0:
        return diagnostics
    queue: deque[tuple[str, Any]] = deque([("", value)])
    while queue and len(diagnostics) < max_reports:
        pointer, item = queue.popleft()
        if isinstance(item, float):
            if not math.isfinite(item):
                diagnostics.append(
                    diagnostic(
                        "ARGUS2-INPUT-NONFINITE",
                        "manifest input contains a NaN or Infinity value",
                        pointer=pointer or "/",
                        remediation="Non-finite values are rejected; they never enter the result.",
                    )
                )
            continue
        if isinstance(item, dict):
            for key, member in item.items():
                queue.append((f"{pointer}/{key}", member))
        elif isinstance(item, list):
            for index, member in enumerate(item):
                queue.append((f"{pointer}/{index}", member))
    return diagnostics


def parse_major(version: Any) -> int | None:
    """Return the major component of a ``<major>.<minor>`` string, or ``None`` if malformed."""

    if not isinstance(version, str):
        return None
    match = _VERSION_PATTERN.match(version)
    if match is None:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def require_supported_major(
    version: Any, *, field: str, pointer: str
) -> list[EvidenceDiagnostic]:
    """Return a rejection when ``version`` is not a supported ``1.x`` schema version."""

    major = parse_major(version)
    if major is None or major != 1:
        return [
            diagnostic(
                "ARGUS2-SCHEMA-MAJOR-UNSUPPORTED",
                f"{field} major version is not supported: {version!r}",
                pointer=pointer,
                remediation="Use a supported 1.x schema version; do not coerce the value.",
            )
        ]
    return []


def reject_unknown_keys(
    value: Any,
    allowed: tuple[str, ...],
    *,
    pointer: str,
    allow: tuple[str, ...] = (),
) -> list[EvidenceDiagnostic]:
    """Return a rejection per key outside ``allowed`` (plus ``allow``)."""

    if not isinstance(value, dict):
        return [
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                f"expected an object at {pointer}",
                pointer=pointer,
                remediation="Supply a JSON object with only the frozen fields.",
            )
        ]
    permitted = set(allowed) | set(allow)
    result: list[EvidenceDiagnostic] = []
    for key in value:
        if key not in permitted:
            result.append(
                diagnostic(
                    "ARGUS2-SCHEMA-UNKNOWN-FIELD",
                    f"unknown field {key!r} at {pointer}",
                    pointer=f"{pointer}/{key}",
                    remediation="Remove the field or place additive data under the extensions object.",
                )
            )
    return result


def validate_extensions(value: Any, *, pointer: str, limits: EvidenceLimits) -> list[EvidenceDiagnostic]:
    """Validate an additive ``extensions`` namespace map; values are preserved but never interpreted."""

    if value is None:
        return []
    if not isinstance(value, dict):
        return [
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                f"extensions at {pointer} must be an object",
                pointer=pointer,
                remediation="Supply an object of namespace -> JSON value.",
            )
        ]
    result: list[EvidenceDiagnostic] = []
    for namespace in value:
        if not isinstance(namespace, str) or EXTENSION_NAMESPACE_PATTERN.match(namespace) is None:
            result.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    f"invalid extensions namespace {namespace!r}",
                    pointer=pointer,
                    remediation="Namespace keys must match ^[a-z][a-z0-9._-]{0,63}$.",
                )
            )
    return result


def raise_if(diagnostics: list[EvidenceDiagnostic], limits: EvidenceLimits | None = None) -> None:
    """Raise ``EvidenceError`` if any diagnostics were collected (bounded by the caller limit)."""

    if not diagnostics:
        return
    maximum = limits.max_diagnostic_count if limits is not None else None
    values = tuple(diagnostics) if maximum is None else tuple(diagnostics[:maximum])
    raise EvidenceError(values)
