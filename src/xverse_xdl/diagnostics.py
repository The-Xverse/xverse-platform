"""Stable diagnostic construction and serialization."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from .models import Diagnostic, ResourceIdentity, Severity, SourceLocation, ValidationGate


def escape_pointer_token(value: object) -> str:
    """Escape one value for use as an RFC 6901 JSON Pointer token."""

    return str(value).replace("~", "~0").replace("/", "~1")


def pointer_from_path(path: Iterable[object]) -> str:
    """Convert an iterable of path components to an RFC 6901 JSON Pointer."""

    tokens = tuple(path)
    return "" if not tokens else "/" + "/".join(escape_pointer_token(item) for item in tokens)


def make_diagnostic(
    code: str,
    gate: ValidationGate,
    message: str,
    correction: str,
    *,
    severity: Severity = Severity.ERROR,
    pointer: str = "",
    resource: ResourceIdentity | None = None,
    location: SourceLocation | None = None,
    related: Sequence[str] = (),
) -> Diagnostic:
    """Construct a stable diagnostic with normalized tuple-valued related data."""

    return Diagnostic(
        code=code,
        gate=gate,
        severity=severity,
        message=message,
        correction=correction,
        pointer=pointer,
        resource=resource,
        location=location,
        related=tuple(related),
    )


def sorted_diagnostics(values: Iterable[Diagnostic]) -> tuple[Diagnostic, ...]:
    """Return diagnostics in their deterministic user-facing order."""

    return tuple(sorted(values, key=lambda item: item.sort_key))


def diagnostic_to_data(value: Diagnostic) -> dict[str, Any]:
    """Serialize a diagnostic to JSON-compatible public report data."""

    result: dict[str, Any] = {
        "code": value.code,
        "gate": value.gate.name.lower(),
        "severity": value.severity.value,
        "resource": value.resource.uri if value.resource else None,
        "pointer": value.pointer,
        "message": value.message,
        "correction": value.correction,
        "related": list(value.related),
    }
    if value.location:
        result["location"] = {
            "source": value.location.source,
            "line": value.location.line,
            "column": value.location.column,
        }
    else:
        result["location"] = None
    return result
