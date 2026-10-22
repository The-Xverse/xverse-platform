"""Closed time grammar of the Phase 6 flow runtime (data model "TimeMapping"; D6-4, D6-6).

Quantities use the unit set of ``TIME_UNIT_TICKS`` (1 tick = 1 ns) and must convert to a
non-negative integral number of nanoseconds. A mapping string is ``identity`` or
``offset:<signed integer><unit>``; mappings are directed and never inverted. Float seconds are
converted with round-half-even over ``Decimal(repr(x))``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
import math
import re
from typing import Any

from xverse_xdl.experiment_plan import TIME_UNIT_TICKS

from .codes import MAPPING_UNSUPPORTED, FlowError

_OFFSET = re.compile(r"^offset:([+-]?[0-9]+)(tick|ns|us|ms|s)$")


@dataclass(frozen=True)
class TimeMapping:
    """Directed pure-offset mapping from ``source`` to ``target`` with a tolerance (ns)."""

    source: str
    target: str
    offset_ns: int
    tolerance_ns: int

    def to_json(self) -> dict[str, Any]:
        """Return the serialized mapping."""

        return {"source": self.source, "target": self.target, "offsetNs": self.offset_ns, "toleranceNs": self.tolerance_ns}


def _finite_number(value: Any) -> bool:
    """Return whether ``value`` is a finite int or float (not bool)."""

    return type(value) in (int, float) and math.isfinite(value)


def parse_quantity_ns(quantity: Any, *, code: str) -> int:
    """Convert an XDL quantity ``{value, unit}`` to non-negative integral nanoseconds.

    @param quantity Mapping with ``value`` (int or float) and ``unit`` (a ``TIME_UNIT_TICKS`` key).
    @param code Stable code raised on refusal.
    @return The value in nanoseconds.
    @raises FlowError ``code`` when the shape, unit, sign or integrality is invalid.
    """

    if not isinstance(quantity, Mapping) or set(quantity) != {"value", "unit"}:
        raise FlowError(code, "quantity must be {value, unit}")
    value, unit = quantity["value"], quantity["unit"]
    if not _finite_number(value) or unit not in TIME_UNIT_TICKS:
        raise FlowError(code, "quantity value or unit is not admitted", {"unit": str(unit)})
    try:
        ns = Decimal(repr(value)) * TIME_UNIT_TICKS[unit]
    except InvalidOperation as error:  # pragma: no cover - finite numbers always convert
        raise FlowError(code, "quantity value is not a number") from error
    if ns < 0 or ns != ns.to_integral_value():
        raise FlowError(code, "quantity is negative or not an integral number of nanoseconds")
    return int(ns)


def parse_mapping(text: Any) -> int:
    """Return the offset (ns) of a closed-grammar mapping string.

    @raises FlowError ``XVERSE-FLOW-MAPPING-UNSUPPORTED`` for any other string.
    """

    if text == "identity":
        return 0
    match = _OFFSET.match(text) if isinstance(text, str) else None
    if match is None:
        raise FlowError(MAPPING_UNSUPPORTED, "mapping is not identity or offset:<int><unit>")
    return int(match.group(1)) * TIME_UNIT_TICKS[match.group(2)]


def seconds_to_ns(seconds: Any) -> int:
    """Convert non-negative finite seconds to integer ns with round-half-even.

    @raises ValueError for a bool, a non-finite or a negative value.
    """

    if not _finite_number(seconds) or seconds < 0:
        raise ValueError("seconds must be a finite, non-negative int or float")
    return int((Decimal(repr(seconds)) * 10**9).to_integral_value(ROUND_HALF_EVEN))
