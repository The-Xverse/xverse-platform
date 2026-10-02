"""X-COM observation projection import (frozen v1.0).

Maps the owned C++ ``ObservationRecord`` accessors by value from a documented, versioned
serialized projection. The narrower tool-gateway protobuf observation is rejected as the full
projection, payload visibility invariants are enforced fail-closed, and no callback, hub handle,
provider handle, tap handle or delivery authority enters Argus (``detailed-design.md`` section 5,
boundary ``ARGUS2-XB-03``/``ARGUS2-XB-04``).
"""

from __future__ import annotations

from typing import Any

from .clocks import validate_clock
from .diagnostics import EvidenceDiagnostic, diagnostic
from .limits import EvidenceLimits
from .schema import (
    INTERACTION_KINDS,
    OBSERVATION_KEYS,
    ORIGIN_KINDS,
    PAYLOAD_VIEW_STATES,
    PROVIDER_OUTCOMES,
    UPSTREAM_CONTRACT_VERSION,
    reject_unknown_keys,
    require_supported_major,
    validate_extensions,
)

__all__ = [
    "PROJECTION_ENVELOPE_KEYS",
    "REQUIRED_OBSERVATION_FIELDS",
    "validate_observation_record",
    "validate_projection",
]

PROJECTION_ENVELOPE_KEYS = ("projectionVersion", "upstreamContractVersion", "exporter", "records", "extensions")

REQUIRED_OBSERVATION_FIELDS = (
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
    "sourcePayloadSize",
    "providerOutcome",
    "payloadViewState",
    "payloadSchemaState",
    "visibleBytesHex",
    "visibleByteCount",
    "tapId",
    "counters",
)
REQUIRED_IDENTITY_FIELDS = ("contractId", "schemaId")
COUNTER_KEYS = ("queued", "accepted", "dropped", "coalesced")


def _closed_set_diagnostic(field: str, value: Any, allowed: tuple[str, ...], pointer: str) -> EvidenceDiagnostic:
    return diagnostic(
        "ARGUS2-SCHEMA-UNKNOWN-FIELD",
        f"{field} value {value!r} is outside the frozen closed set",
        pointer=f"{pointer}/{field}",
        remediation=f"Use one of {', '.join(allowed)}.",
    )


def _nonnegative_int(value: Any, field: str, pointer: str) -> list[EvidenceDiagnostic]:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return [
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                f"{field} must be a non-negative integer",
                pointer=f"{pointer}/{field}",
                remediation="Supply an exact non-negative integer.",
            )
        ]
    return []


def _string(value: Any, field: str, pointer: str, *, empty_code: str = "ARGUS2-INPUT-FIELD-INVALID") -> list[EvidenceDiagnostic]:
    if not isinstance(value, str) or value == "":
        return [
            diagnostic(
                empty_code,
                f"{field} must be a non-empty string",
                pointer=f"{pointer}/{field}",
                remediation="Supply the declared value exactly.",
            )
        ]
    return []


def validate_observation_record(
    record: Any, *, pointer: str, limits: EvidenceLimits
) -> tuple[dict[str, Any] | None, list[EvidenceDiagnostic]]:
    """Validate one projection record against the frozen field mapping."""

    diagnostics: list[EvidenceDiagnostic] = []
    if not isinstance(record, dict):
        return None, [
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                f"projection record at {pointer} must be an object",
                pointer=pointer,
                remediation="Supply a frozen observation record object.",
            )
        ]
    diagnostics.extend(reject_unknown_keys(record, OBSERVATION_KEYS, pointer=pointer))
    diagnostics.extend(validate_extensions(record.get("extensions"), pointer=f"{pointer}/extensions", limits=limits))

    for field in REQUIRED_IDENTITY_FIELDS:
        diagnostics.extend(_string(record.get(field), field, pointer, empty_code="ARGUS2-INPUT-IDENTITY-MISSING"))
    for field in REQUIRED_OBSERVATION_FIELDS:
        if field not in record:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-PROJECTION-INCOMPLETE",
                    f"projection record is missing required field {field!r}",
                    pointer=f"{pointer}/{field}",
                    remediation="Supply every owned accessor field; missing metadata is never fabricated.",
                )
            )

    if record.get("interactionKind") not in INTERACTION_KINDS:
        diagnostics.append(_closed_set_diagnostic("interactionKind", record.get("interactionKind"), INTERACTION_KINDS, pointer))
    if record.get("origin") not in ORIGIN_KINDS:
        diagnostics.append(_closed_set_diagnostic("origin", record.get("origin"), ORIGIN_KINDS, pointer))
    if record.get("providerOutcome") not in PROVIDER_OUTCOMES:
        diagnostics.append(_closed_set_diagnostic("providerOutcome", record.get("providerOutcome"), PROVIDER_OUTCOMES, pointer))
    if record.get("payloadViewState") not in PAYLOAD_VIEW_STATES:
        diagnostics.append(_closed_set_diagnostic("payloadViewState", record.get("payloadViewState"), PAYLOAD_VIEW_STATES, pointer))
    if record.get("payloadSchemaState") != "undecoded":
        diagnostics.append(
            diagnostic(
                "ARGUS2-SCHEMA-UNKNOWN-FIELD",
                "payloadSchemaState must be 'undecoded'; this slice never claims decoder success",
                pointer=f"{pointer}/payloadSchemaState",
                remediation="Do not assert decoder success in this slice.",
            )
        )

    for field in ("contractVersion", "schemaVersion"):
        diagnostics.extend(_string(record.get(field), field, pointer))
    diagnostics.extend(_nonnegative_int(record.get("sourcePayloadSize"), "sourcePayloadSize", pointer))

    for clock_field in ("sourceClock", "observationClock"):
        _validated, clock_diagnostics = validate_clock(
            record.get(clock_field), pointer=f"{pointer}/{clock_field}", limits=limits
        )
        diagnostics.extend(clock_diagnostics)

    counters = record.get("counters")
    if not isinstance(counters, dict):
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                "counters must be an object",
                pointer=f"{pointer}/counters",
                remediation="Supply the four retention-time counters.",
            )
        )
    else:
        diagnostics.extend(reject_unknown_keys(counters, COUNTER_KEYS, pointer=f"{pointer}/counters"))
        for key in COUNTER_KEYS:
            diagnostics.extend(_nonnegative_int(counters.get(key), f"counters/{key}", pointer))

    sequence = record.get("sequence")
    if sequence is not None:
        diagnostics.extend(_nonnegative_int(sequence, "sequence", pointer))

    visible_hex = record.get("visibleBytesHex")
    visible_count = record.get("visibleByteCount")
    if not isinstance(visible_hex, str) or visible_hex != visible_hex.lower() or len(visible_hex) % 2 != 0:
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                "visibleBytesHex must be lowercase even-length hexadecimal text",
                pointer=f"{pointer}/visibleBytesHex",
                remediation="Encode visible bytes as lowercase hex.",
            )
        )
    else:
        try:
            decoded_length = len(bytes.fromhex(visible_hex))
        except ValueError:
            decoded_length = -1
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    "visibleBytesHex is not valid hexadecimal text",
                    pointer=f"{pointer}/visibleBytesHex",
                    remediation="Encode visible bytes as lowercase hex.",
                )
            )
        if decoded_length >= 0 and visible_count != decoded_length:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-PAYLOAD-LENGTH",
                    "visibleByteCount does not match the encoded visible bytes",
                    pointer=f"{pointer}/visibleByteCount",
                    remediation="Bytes are never synthesized, padded or truncated to fit.",
                )
            )

    diagnostics.extend(_nonnegative_int(visible_count, "visibleByteCount", pointer))
    if isinstance(visible_count, int) and not isinstance(visible_count, bool) and visible_count > limits.max_payload_bytes:
        diagnostics.append(
            diagnostic(
                "ARGUS2-BOUND-EXCEEDED",
                f"visible payload bytes exceed max_payload_bytes {limits.max_payload_bytes}",
                pointer=f"{pointer}/visibleByteCount",
                remediation="Reduce the visible payload bound or the stored prefix.",
            )
        )

    state = record.get("payloadViewState")
    source_size = record.get("sourcePayloadSize")
    if state in PAYLOAD_VIEW_STATES and isinstance(visible_count, int) and isinstance(source_size, int):
        if state in ("omitted", "redacted") and not (visible_count == 0 and visible_hex == ""):
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    f"payloadViewState {state!r} must carry no visible bytes",
                    pointer=f"{pointer}/visibleBytesHex",
                    remediation="Withheld content is never reconstructed.",
                )
            )
        elif state == "complete" and visible_count != source_size:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    "payloadViewState 'complete' requires visibleByteCount == sourcePayloadSize",
                    pointer=f"{pointer}/visibleByteCount",
                    remediation="Mark incomplete content as truncated.",
                )
            )
        elif state == "truncated" and not (0 < visible_count < source_size):
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    "payloadViewState 'truncated' requires 0 < visibleByteCount < sourcePayloadSize",
                    pointer=f"{pointer}/visibleByteCount",
                    remediation="Retain an explicit bounded prefix.",
                )
            )

    if diagnostics:
        return None, diagnostics
    preserved = dict(record)
    return preserved, []


def validate_projection(
    projection: Any, *, limits: EvidenceLimits
) -> tuple[dict[str, Any] | None, list[EvidenceDiagnostic]]:
    """Validate a projection envelope and every record it carries."""

    diagnostics: list[EvidenceDiagnostic] = []
    if not isinstance(projection, dict):
        return None, [
            diagnostic(
                "ARGUS2-INPUT-PROJECTION-INCOMPLETE",
                "observation projection must be an object envelope",
                remediation="Supply the versioned projection envelope.",
            )
        ]
    diagnostics.extend(reject_unknown_keys(projection, PROJECTION_ENVELOPE_KEYS, pointer="/projection"))
    diagnostics.extend(validate_extensions(projection.get("extensions"), pointer="/projection/extensions", limits=limits))
    if diagnostics:
        return None, diagnostics

    diagnostics.extend(require_supported_major(projection.get("projectionVersion"), field="projectionVersion", pointer="/projection/projectionVersion"))
    if projection.get("upstreamContractVersion") != UPSTREAM_CONTRACT_VERSION:
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-PROJECTION-INCOMPLETE",
                "projection envelope must declare the owned upstream observation contract version",
                pointer="/projection/upstreamContractVersion",
                remediation=f"Declare upstreamContractVersion {UPSTREAM_CONTRACT_VERSION}.",
            )
        )
    exporter = projection.get("exporter")
    if not isinstance(exporter, dict) or "task" not in exporter or "toolVersion" not in exporter:
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-PROJECTION-INCOMPLETE",
                "projection envelope must declare an exporter task and toolVersion",
                pointer="/projection/exporter",
                remediation="Declare the producing tool identity.",
            )
        )
    records = projection.get("records")
    if not isinstance(records, list) or not records:
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-PROJECTION-INCOMPLETE",
                "projection envelope must carry at least one record",
                pointer="/projection/records",
                remediation="Supply at least one owned observation record.",
            )
        )
        return None, diagnostics
    validated_records: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        validated, record_diagnostics = validate_observation_record(
            record, pointer=f"/projection/records/{index}", limits=limits
        )
        diagnostics.extend(record_diagnostics)
        if validated is not None:
            validated_records.append(validated)
    if diagnostics:
        return None, diagnostics
    envelope = {
        "projectionVersion": projection.get("projectionVersion"),
        "upstreamContractVersion": projection.get("upstreamContractVersion"),
        "exporter": dict(exporter),
        "records": validated_records,
    }
    if "extensions" in projection:
        envelope["extensions"] = projection["extensions"]
    return envelope, []
