"""Stable, categorized Argus evidence diagnostics.

This module owns the closed diagnostic catalogue frozen by
``docs/engineering/argus-lite/unit-specifications.md`` section 5. Every diagnostic carries
``{code, category, severity, message, pointer?, path?, eventId?, remediation}`` and no diagnostic
is produced without a real violation. The module performs no I/O and reads no ambient state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = [
    "CATEGORY_BY_CODE",
    "EVIDENCE_REASON_CATEGORY",
    "SEVERITY_ERROR",
    "SEVERITY_FINDING",
    "EvidenceDiagnostic",
    "EvidenceError",
    "bound_diagnostics",
    "catalogue_codes",
    "category_for_code",
    "diagnostic",
]

SEVERITY_ERROR = "error"
SEVERITY_FINDING = "finding"


# Closed code -> category catalogue (unit-specifications.md section 5).
CATEGORY_BY_CODE: dict[str, str] = {}


def _add(category: str, *codes: str) -> None:
    for code in codes:
        if code in CATEGORY_BY_CODE:
            raise AssertionError(f"duplicate diagnostic code: {code}")
        CATEGORY_BY_CODE[code] = category


_add(
    "input-rejection",
    "ARGUS2-INPUT-FIELD-INVALID",
    "ARGUS2-INPUT-IDENTITY-MISSING",
    "ARGUS2-INPUT-DUPLICATE-EVENT",
    "ARGUS2-INPUT-NONFINITE",
    "ARGUS2-INPUT-CLOCK-MISSING",
    "ARGUS2-INPUT-UNIT-MISSING",
    "ARGUS2-INPUT-PROJECTION-INCOMPLETE",
    "ARGUS2-INPUT-PAYLOAD-LENGTH",
    "ARGUS2-INPUT-INTERVAL-INCOMPLETE",
    "ARGUS2-INPUT-AUTHORITY-MISSING",
)
_add("io-failure", "ARGUS2-IO-FAILURE")
_add("unsupported-schema", "ARGUS2-SCHEMA-MAJOR-UNSUPPORTED", "ARGUS2-SCHEMA-UNKNOWN-FIELD")
_add(
    "corrupt-artifact",
    "ARGUS2-CORRUPT-STREAM-TRUNCATED",
    "ARGUS2-CORRUPT-ARTIFACT-HASH",
    "ARGUS2-CORRUPT-ARTIFACT-SIZE",
    "ARGUS2-CORRUPT-MANIFEST-SHAPE",
    "ARGUS2-CORRUPT-EVENT",
    "ARGUS2-CORRUPT-RECORD-SHAPE",
    "ARGUS2-CORRUPT-RUN-ID-MISMATCH",
    "ARGUS2-CORRUPT-DUPLICATE-EVENT",
    "ARGUS2-CORRUPT-ORDINAL",
)
_add("missing-evidence", "ARGUS2-MISSING-ARTIFACT")
_add(
    "known-observation-loss",
    "ARGUS2-LOSS-KNOWN-DROP",
    "ARGUS2-LOSS-DEGRADED-INTERVAL",
    "ARGUS2-LOSS-INVALID-INTERVAL",
)
_add("bounds", "ARGUS2-BOUND-EXCEEDED")
_add(
    "path",
    "ARGUS2-PATH-ESCAPE",
    "ARGUS2-PATH-SYMLINK",
    "ARGUS2-PATH-UNSAFE",
    "ARGUS2-PATH-NOT-REGULAR",
)
_add("state", "ARGUS2-STATE-RUN-EXISTS", "ARGUS2-STATE-WRITER-CONFLICT", "ARGUS2-STATE-ILLEGAL-TRANSITION")
_add("clock", "ARGUS2-CLOCK-UNRESOLVED")
_add("causal", "ARGUS2-CAUSAL-UNRESOLVED")
_add("plan", "ARGUS2-PLAN-DIGEST-MISMATCH", "ARGUS2-PLAN-VERSION-UNSUPPORTED", "ARGUS2-PLAN-ENVELOPE-CONFLICT")

# Evidence reason codes are manifest facts (not diagnostics); where a reader surfaces one it
# uses this frozen category mapping.
EVIDENCE_REASON_CATEGORY: dict[str, str] = {
    "ARGUS2-REASON-TRUNCATED-STREAM": "corrupt-artifact",
    "ARGUS2-REASON-MISSING-ARTIFACT": "missing-evidence",
    "ARGUS2-REASON-MUTATED-ARTIFACT": "corrupt-artifact",
    "ARGUS2-REASON-UNMET-OBLIGATION": "missing-evidence",
    "ARGUS2-REASON-KNOWN-LOSS": "known-observation-loss",
    "ARGUS2-REASON-DEGRADED-INTERVAL": "known-observation-loss",
    "ARGUS2-REASON-INVALID-INTERVAL": "known-observation-loss",
    "ARGUS2-REASON-UNRESOLVED-CAUSATION": "causal",
    "ARGUS2-REASON-UNCLOSED-INTERVAL": "known-observation-loss",
    "ARGUS2-REASON-UNSUPPORTED-SCHEMA": "unsupported-schema",
    "ARGUS2-REASON-WRITER-STATE": "state",
    "ARGUS2-REASON-CORRUPT-MANIFEST": "corrupt-artifact",
    "ARGUS2-REASON-CORRUPT-EVENT": "corrupt-artifact",
}


def catalogue_codes() -> tuple[str, ...]:
    """Return every frozen diagnostic code."""

    return tuple(sorted(CATEGORY_BY_CODE))


def category_for_code(code: str) -> str | None:
    """Return the frozen category for a diagnostic or evidence reason code."""

    if code in CATEGORY_BY_CODE:
        return CATEGORY_BY_CODE[code]
    return EVIDENCE_REASON_CATEGORY.get(code)


@dataclass(frozen=True)
class EvidenceDiagnostic:
    """One stable, categorized evidence diagnostic."""

    code: str
    category: str
    severity: str
    message: str
    pointer: str | None = None
    path: str | None = None
    eventId: str | None = None
    remediation: str = ""

    def to_data(self) -> dict[str, Any]:
        """Return the canonical JSON-compatible diagnostic mapping."""

        return {
            "code": self.code,
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "pointer": self.pointer,
            "path": self.path,
            "eventId": self.eventId,
            "remediation": self.remediation,
        }


def diagnostic(
    code: str,
    message: str,
    *,
    pointer: str | None = None,
    path: str | None = None,
    event_id: str | None = None,
    remediation: str = "",
    severity: str = SEVERITY_ERROR,
) -> EvidenceDiagnostic:
    """Build one diagnostic, asserting that the code belongs to the closed catalogue."""

    category = CATEGORY_BY_CODE.get(code)
    if category is None:
        raise AssertionError(f"diagnostic code outside the frozen catalogue: {code}")
    return EvidenceDiagnostic(
        code=code,
        category=category,
        severity=severity,
        message=message,
        pointer=pointer,
        path=path,
        eventId=event_id,
        remediation=remediation,
    )


def bound_diagnostics(
    diagnostics: list[EvidenceDiagnostic] | tuple[EvidenceDiagnostic, ...], maximum: int
) -> tuple[EvidenceDiagnostic, ...]:
    """Return at most ``maximum`` diagnostics, preserving order (no diagnostic is emitted alone)."""

    values = tuple(diagnostics)
    if maximum is None or maximum <= 0:
        return ()
    return values[:maximum]


class EvidenceError(Exception):
    """Raised for a rejected evidence operation, carrying the stable diagnostics."""

    def __init__(self, diagnostics: EvidenceDiagnostic | tuple[EvidenceDiagnostic, ...] | list[EvidenceDiagnostic]) -> None:
        if isinstance(diagnostics, EvidenceDiagnostic):
            values: tuple[EvidenceDiagnostic, ...] = (diagnostics,)
        else:
            values = tuple(diagnostics)
        if not values:
            raise AssertionError("EvidenceError requires at least one diagnostic")
        self.diagnostics = values
        super().__init__(f"{values[0].code}: {values[0].message}")

    @property
    def codes(self) -> tuple[str, ...]:
        """Return the ordered diagnostic codes."""

        return tuple(item.code for item in self.diagnostics)
