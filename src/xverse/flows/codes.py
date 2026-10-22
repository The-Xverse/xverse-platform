"""Stable diagnostic codes of the Phase 6 flow runtime (detailed design §2).

Binding refusals are collected, never raised. ``FlowError`` is raised only for programming misuse
(an invalid harness call, an over-long evidence id) and carries a stable code and a mapping detail.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

INPUT_MISMATCH = "XVERSE-FLOW-INPUT-MISMATCH"
XCOM_PLAN = "XVERSE-FLOW-XCOM-PLAN"
XCOM_CROSSCHECK = "XVERSE-FLOW-XCOM-CROSSCHECK"
UNSUPPORTED = "XVERSE-FLOW-UNSUPPORTED"
POLICY_MISSING = "XVERSE-FLOW-POLICY-MISSING"
POLICY_CONFLICT = "XVERSE-FLOW-POLICY-CONFLICT"
PROVIDER = "XVERSE-FLOW-PROVIDER"
CLOCK_UNKNOWN = "XVERSE-FLOW-CLOCK-UNKNOWN"
MAPPING_MISSING = "XVERSE-FLOW-MAPPING-MISSING"
MAPPING_UNSUPPORTED = "XVERSE-FLOW-MAPPING-UNSUPPORTED"
QUALITY_INVALID = "XVERSE-FLOW-QUALITY-INVALID"
TOLERANCE = "XVERSE-FLOW-TOLERANCE"
CLOCK_REGRESSION = "XVERSE-FLOW-CLOCK-REGRESSION"
ORIGIN_MISSING = "XVERSE-FLOW-ORIGIN-MISSING"
HARNESS = "XVERSE-FLOW-HARNESS"


class FlowError(RuntimeError):
    """Programming-misuse failure with a stable code."""

    def __init__(self, code: str, message: str, detail: Mapping[str, Any] | None = None) -> None:
        """Create the failure.

        @param code Stable ``XVERSE-FLOW-*`` code.
        @param message Public-safe explanation.
        @param detail JSON-safe detail mapping.
        """

        super().__init__(f"{code}: {message}")
        self.code = code
        self.detail = dict(detail or {})


def refusal(code: str, flow_id: str | None = None, **detail: Any) -> dict[str, Any]:
    """Return one binding refusal record ``{flowId, code, detail}``."""

    return {"flowId": flow_id, "code": code, "detail": dict(detail)}
