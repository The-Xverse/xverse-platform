"""Separately supplied tap-snapshot projection import (frozen v1.0).

The owned C++ ``ObservationSnapshot`` carries no interval window, so ``intervalProvenance`` is
caller-supplied metadata imported with the snapshot and never inferred from counters. A closed
interval missing either bound is rejected; an unclosed/unavailable closure is accepted and recorded
as an unresolved interval. Retention counters never substitute for interval closure
(``detailed-design.md`` section 5.4, invariant ``ARGUS2-INV-09``).
"""

from __future__ import annotations

from typing import Any

from .clocks import validate_clock
from .diagnostics import EvidenceDiagnostic, diagnostic
from .limits import EvidenceLimits
from .schema import (
    INTERVAL_CLOSURES,
    SNAPSHOT_KEYS,
    VALIDITY_EFFECTS,
    VALIDITY_STATES,
    reject_unknown_keys,
    require_supported_major,
    validate_extensions,
)

__all__ = ["REQUIRED_SNAPSHOT_FIELDS", "validate_snapshot"]

REQUIRED_SNAPSHOT_FIELDS = (
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
)
INTERVAL_KEYS = ("streamId", "intervalId", "closure", "start", "end", "provenance")


def _counter_diagnostics(snapshot: dict[str, Any]) -> list[EvidenceDiagnostic]:
    diagnostics: list[EvidenceDiagnostic] = []
    for field in ("queued", "accepted", "dropped", "coalesced", "backpressureRejections"):
        value = snapshot.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-FIELD-INVALID",
                    f"{field} must be a non-negative integer",
                    pointer=f"/snapshot/{field}",
                    remediation="Supply an exact non-negative integer.",
                )
            )
    return diagnostics


def validate_snapshot(
    snapshot: Any, *, limits: EvidenceLimits
) -> tuple[dict[str, Any] | None, list[EvidenceDiagnostic]]:
    """Validate one caller-supplied snapshot projection."""

    diagnostics: list[EvidenceDiagnostic] = []
    if not isinstance(snapshot, dict):
        return None, [
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                "snapshot projection must be an object",
                remediation="Supply the frozen snapshot projection.",
            )
        ]
    diagnostics.extend(reject_unknown_keys(snapshot, SNAPSHOT_KEYS, pointer="/snapshot"))
    diagnostics.extend(validate_extensions(snapshot.get("extensions"), pointer="/snapshot/extensions", limits=limits))
    if diagnostics:
        return None, diagnostics

    for field in REQUIRED_SNAPSHOT_FIELDS:
        if field not in snapshot:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-INPUT-PROJECTION-INCOMPLETE",
                    f"snapshot is missing required field {field!r}",
                    pointer=f"/snapshot/{field}",
                    remediation="Supply every declared snapshot field; missing facts stay unavailable.",
                )
            )
    if diagnostics:
        return None, diagnostics

    diagnostics.extend(require_supported_major(snapshot.get("snapshotVersion"), field="snapshotVersion", pointer="/snapshot/snapshotVersion"))
    diagnostics.extend(_counter_diagnostics(snapshot))

    if snapshot.get("validityEffect") not in VALIDITY_EFFECTS:
        diagnostics.append(
            diagnostic(
                "ARGUS2-SCHEMA-UNKNOWN-FIELD",
                "validityEffect is outside the frozen closed set",
                pointer="/snapshot/validityEffect",
                remediation=f"Use one of {', '.join(VALIDITY_EFFECTS)}.",
            )
        )
    if snapshot.get("validityState") not in VALIDITY_STATES:
        diagnostics.append(
            diagnostic(
                "ARGUS2-SCHEMA-UNKNOWN-FIELD",
                "validityState is outside the frozen closed set",
                pointer="/snapshot/validityState",
                remediation=f"Use one of {', '.join(VALIDITY_STATES)}.",
            )
        )
    if not isinstance(snapshot.get("experimentValidityDegraded"), bool):
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-FIELD-INVALID",
                "experimentValidityDegraded must be a boolean",
                pointer="/snapshot/experimentValidityDegraded",
                remediation="Supply the declared boolean.",
            )
        )
    if not isinstance(snapshot.get("declaredTapId"), str) or snapshot.get("declaredTapId") == "":
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-IDENTITY-MISSING",
                "snapshot declares no declaredTapId",
                pointer="/snapshot/declaredTapId",
                remediation="Declare the producing tap identity.",
            )
        )

    interval = snapshot.get("intervalProvenance")
    if not isinstance(interval, dict):
        diagnostics.append(
            diagnostic(
                "ARGUS2-INPUT-INTERVAL-INCOMPLETE",
                "snapshot intervalProvenance must be an object",
                pointer="/snapshot/intervalProvenance",
                remediation="Declare the caller-supplied interval provenance.",
            )
        )
    else:
        diagnostics.extend(reject_unknown_keys(interval, INTERVAL_KEYS, pointer="/snapshot/intervalProvenance"))
        for field in ("streamId", "intervalId", "provenance"):
            if not isinstance(interval.get(field), str) or interval.get(field) == "":
                diagnostics.append(
                    diagnostic(
                        "ARGUS2-INPUT-INTERVAL-INCOMPLETE",
                        f"intervalProvenance.{field} must be a non-empty string",
                        pointer=f"/snapshot/intervalProvenance/{field}",
                        remediation="Declare the interval provenance explicitly.",
                    )
                )
        closure = interval.get("closure")
        if closure not in INTERVAL_CLOSURES:
            diagnostics.append(
                diagnostic(
                    "ARGUS2-SCHEMA-UNKNOWN-FIELD",
                    "intervalProvenance.closure is outside the frozen closed set",
                    pointer="/snapshot/intervalProvenance/closure",
                    remediation=f"Use one of {', '.join(INTERVAL_CLOSURES)}.",
                )
            )
        elif closure == "closed":
            for bound in ("start", "end"):
                if interval.get(bound) is None:
                    diagnostics.append(
                        diagnostic(
                            "ARGUS2-INPUT-INTERVAL-INCOMPLETE",
                            f"a closed interval must declare its {bound} bound",
                            pointer=f"/snapshot/intervalProvenance/{bound}",
                            remediation="The interval is never completed by inference.",
                        )
                    )
        for bound in ("start", "end"):
            if interval.get(bound) is not None:
                _validated, clock_diagnostics = validate_clock(
                    interval.get(bound),
                    pointer=f"/snapshot/intervalProvenance/{bound}",
                    limits=limits,
                )
                diagnostics.extend(clock_diagnostics)

    if diagnostics:
        return None, diagnostics
    preserved = {key: value for key, value in snapshot.items()}
    return preserved, []
