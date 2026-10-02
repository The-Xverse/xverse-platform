"""Explicit clock-domain representation with no ambient clock and no cross-domain conversion.

A clock value is ``{"domain": <str>, "unit": <str>, "value": <finite number>}``. Domains and units
are caller-supplied and preserved verbatim; no unit is inferred and no value is rescaled, compared
or sorted across domains (``detailed-design.md`` section 6, invariant ``ARGUS2-INV-04``).
"""

from __future__ import annotations

import math
from typing import Any

from .diagnostics import EvidenceDiagnostic, diagnostic
from .limits import EvidenceLimits
from .schema import CLOCK_KEYS, reject_unknown_keys

__all__ = ["clock_domain", "clock_equal", "validate_clock", "validate_clocks"]


def _is_finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value))


def validate_clock(
    value: Any, *, pointer: str, limits: EvidenceLimits
) -> tuple[dict[str, Any] | None, list[EvidenceDiagnostic]]:
    """Validate one clock value; return the preserved value and any diagnostics."""

    diagnostics = reject_unknown_keys(value, CLOCK_KEYS, pointer=pointer)
    if not isinstance(value, dict):
        return None, diagnostics
    domain = value.get("domain")
    unit = value.get("unit")
    if not isinstance(domain, str) or domain == "":
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-CLOCK-MISSING",
                f"clock value at {pointer} declares no domain identity",
                pointer=f"{pointer}/domain",
                remediation="Declare an explicit caller-supplied clock domain; no domain is inferred.",
            )
        )
    elif len(domain) > limits.max_text_length:
        diagnostics.append(
            diagnostic(
                "ARGUS2-BOUND-EXCEEDED",
                f"clock domain at {pointer} exceeds max_text_length",
                pointer=f"{pointer}/domain",
                remediation="Shorten the declared clock domain.",
            )
        )
    if not isinstance(unit, str) or unit == "":
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-UNIT-MISSING",
                f"clock value at {pointer} declares no unit/representation",
                pointer=f"{pointer}/unit",
                remediation="Declare the caller's unit; no unit is inferred.",
            )
        )
    elif len(unit) > limits.max_text_length:
        diagnostics.append(
            diagnostic(
                "ARGUS2-BOUND-EXCEEDED",
                f"clock unit at {pointer} exceeds max_text_length",
                pointer=f"{pointer}/unit",
                remediation="Shorten the declared clock unit.",
            )
        )
    number = value.get("value")
    if not _is_finite_number(number):
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-NONFINITE",
                f"clock value at {pointer} is missing or not finite",
                pointer=f"{pointer}/value",
                remediation="Supply a finite JSON number; non-finite values are never repaired.",
            )
        )
    if diagnostics:
        return None, diagnostics
    return {"domain": domain, "unit": unit, "value": number}, []


def validate_clocks(
    value: Any, *, pointer: str, limits: EvidenceLimits
) -> tuple[dict[str, Any] | None, list[EvidenceDiagnostic]]:
    """Validate a mapping of clock identifier -> clock value."""

    if not isinstance(value, dict) or not value:
        return None, [
            diagnostic(
                "ARGUS2-INPUT-CLOCK-MISSING",
                f"no clocks declared at {pointer}",
                pointer=pointer,
                remediation="Declare the explicit source/observation clocks this record requires.",
            )
        ]
    result: dict[str, Any] = {}
    diagnostics: list[EvidenceDiagnostic] = []
    for name, clock in value.items():
        if not isinstance(name, str) or name == "":
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    f"invalid clock identifier at {pointer}",
                    pointer=pointer,
                    remediation="Use a non-empty clock identifier.",
                )
            )
            continue
        validated, clock_diagnostics = validate_clock(
            clock, pointer=f"{pointer}/{name}", limits=limits
        )
        diagnostics.extend(clock_diagnostics)
        if validated is not None:
            result[name] = validated
    if diagnostics:
        return None, diagnostics
    return result, []


def clock_domain(value: Any) -> str | None:
    """Return the declared domain of a preserved clock value, if present."""

    if isinstance(value, dict):
        domain = value.get("domain")
        if isinstance(domain, str):
            return domain
    return None


def clock_equal(left: Any, right: Any) -> bool:
    """Return whether two preserved clock values are exactly equal (no rescaling)."""

    return left == right
