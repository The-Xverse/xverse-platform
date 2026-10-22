"""Injected receiver clocks (data model "Time and age"; detailed design §7).

``ReceiverClock.read(domain)`` returns an integer reading in nanoseconds. ``TickClock`` is the
deterministic harness clock: at tick ``t`` a domain reads ``t + offset(domain)`` (1 tick = 1 ns).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol


class ReceiverClock(Protocol):
    """Clock read once per received item and per poll."""

    def read(self, domain: str) -> int:
        """Return the current reading of ``domain`` in nanoseconds."""
        ...


class TickClock:
    """Deterministic clock driven by planned ticks; undeclared domains read offset 0."""

    def __init__(self, offsets: Mapping[str, int] | None = None) -> None:
        """Create the clock.

        @param offsets Per-domain offsets in ns added to the tick.
        """

        self.offsets = dict(offsets or {})
        self.tick = 0

    def at(self, tick: int) -> None:
        """Set the current tick."""

        self.tick = int(tick)

    def read(self, domain: str) -> int:
        """Return ``tick + offset(domain)``."""

        return self.tick + int(self.offsets.get(domain, 0))
