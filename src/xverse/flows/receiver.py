"""Receiver-side enforcement: verdicts, gaps, freshness, deadline liveness and queue (D6-1).

Precedence (contract rule 10): clock-error > duplicate > out-of-order > stale > queue-full >
delivered. State updates follow the data-model table. The deadline is a liveness bound on
deliveries: the k-th ``deadline-missed`` event is raised when a reading satisfies
``now > anchor + k * deadline``, the anchor being route activation or the last delivery; it is
checked at every reception (before the verdict) and every poll. Sequences are consecutive at the
sender; ``gapBefore`` counts the sequences skipped above the highest seen.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from .binding import FlowBinding
from .clock import ReceiverClock
from .codes import CLOCK_REGRESSION, TOLERANCE

CLOCK_ERROR, DUPLICATE, OUT_OF_ORDER, STALE, QUEUE_FULL, DELIVERED = (
    "clock-error", "duplicate", "out-of-order", "stale", "queue-full", "delivered")
VERDICTS = (CLOCK_ERROR, DUPLICATE, OUT_OF_ORDER, STALE, QUEUE_FULL, DELIVERED)


@dataclass(frozen=True)
class FlowItem:
    """One sender item: flow, consecutive sequence and origin time (sender domain, ns)."""

    flow_id: str
    sequence: int
    origin_ns: int


@dataclass(frozen=True)
class ItemVerdict:
    """The receiver's verdict on one item."""

    flow_id: str
    sequence: int
    origin_ns: int
    reception_ns: int
    age_ns: int | None
    verdict: str
    delivered: bool
    gap_before: int
    fills_gap: bool
    diagnostic: str | None = None

    def to_json(self) -> dict[str, Any]:
        """Return the evidence payload of this verdict."""

        data = asdict(self)
        return {"flowId": data["flow_id"], "sequence": data["sequence"], "originNs": data["origin_ns"],
                "receptionNs": data["reception_ns"], "ageNs": data["age_ns"], "verdict": data["verdict"],
                "delivered": data["delivered"], "gapBefore": data["gap_before"], "fillsGap": data["fills_gap"],
                "diagnostic": data["diagnostic"]}


class FlowReceiver:
    """Receiver of one bound flow."""

    def __init__(self, binding: FlowBinding, clock: ReceiverClock, *, listener: Any = None, drain: bool = True,
                 ordering: str | None = None) -> None:
        """Create the receiver.

        @param binding The flow's binding (policy, mapping, bounds).
        @param clock Injected receiver clock.
        @param listener Optional object with ``verdict``, ``deadline`` and ``summary`` callbacks.
        @param drain Whether ``poll`` drains the pending buffer (tests use ``False``).
        @param ordering Override of the policy ordering, for receiver-unit tests of ``unordered``.
        """

        self.binding = binding
        self._clock = clock
        self._listener = listener
        self._drain = drain
        self._fifo = (ordering or binding.policy.ordering) == "fifo"
        self._seen: set[int] = set()
        self._missing: set[int] = set()
        self._highest: int | None = None
        self._last_reception: int | None = None
        self._anchor: int | None = None
        self._k = 0
        self.pending = 0
        self.counts = {verdict: 0 for verdict in VERDICTS}
        self.delivered_count = 0
        self.withheld_count = 0
        self.gap_count = 0
        self.filled_gap_count = 0
        self.deadline_missed_count = 0
        self.first_sequence: int | None = None
        self.last_sequence: int | None = None
        self.max_age_ns: int | None = None
        self.verdicts: list[ItemVerdict] = []

    def _read(self) -> int:
        """Read the receiver-domain clock once."""

        return self._clock.read(self.binding.receiver_domain)

    def activate(self) -> None:
        """Start the route: the activation reading is the first deadline anchor."""

        self._anchor = self._read()  # deadline anchor only; the regression baseline is the previous reception (L2)
        self._k = 0

    def _check_deadline(self, now: int) -> None:
        """Raise one event per missed deadline interval since the anchor."""

        deadline = self.binding.deadline_ns
        if deadline <= 0 or self._anchor is None:
            return
        while now > self._anchor + (self._k + 1) * deadline:
            self._k += 1
            self.deadline_missed_count += 1
            if self._listener is not None:
                self._listener.deadline(self.binding, self._k, now)

    def poll(self) -> None:
        """Check the deadline at the current reading and drain the buffer when enabled."""

        self._check_deadline(self._read())
        if self._drain:
            self.pending = 0

    def receive(self, item: FlowItem) -> ItemVerdict:
        """Give ``item`` its verdict, update the state table and notify the listener."""

        now = self._read()
        self._check_deadline(now)
        seq = item.sequence
        mapping = self.binding.mapping
        age = now - (item.origin_ns + mapping.offset_ns)
        gap = 0 if self._highest is None or seq <= self._highest else seq - self._highest - 1
        diagnostic = None
        if self._last_reception is not None and now < self._last_reception:
            verdict, diagnostic = CLOCK_ERROR, CLOCK_REGRESSION
            gap, age_out = 0, None
            return self._finish(item, now, age_out, verdict, False, 0, False, diagnostic, update=False)
        if age < -mapping.tolerance_ns:
            return self._finish(item, now, age, CLOCK_ERROR, False, gap, False, TOLERANCE, update=True, advance=True)
        if seq in self._seen:
            return self._finish(item, now, age, DUPLICATE, False, 0, False, None, update=False, reception=True)
        if self._highest is not None and seq < self._highest:
            delivered = not self._fifo
            fills = delivered and seq in self._missing
            if delivered and self.pending >= self.binding.policy.queue_depth:
                # Precedence keeps the out-of-order verdict; the full buffer withholds it (finding 2).
                return self._finish(item, now, age, OUT_OF_ORDER, False, 0, False, "queue-full", update=True, advance=False)
            return self._finish(item, now, age, OUT_OF_ORDER, delivered, 0, fills, None, update=True, advance=False)
        freshness = self.binding.freshness_ns
        if freshness > 0 and max(age, 0) > freshness:
            return self._finish(item, now, age, STALE, False, gap, False, None, update=True, advance=True)
        if self.pending >= self.binding.policy.queue_depth:
            return self._finish(item, now, age, QUEUE_FULL, False, gap, False, None, update=True, advance=True)
        return self._finish(item, now, age, DELIVERED, True, gap, seq in self._missing, None, update=True, advance=True)

    def _finish(self, item: FlowItem, now: int, age: int | None, verdict: str, delivered: bool, gap: int, fills: bool,
                diagnostic: str | None, *, update: bool, advance: bool = False, reception: bool = False) -> ItemVerdict:
        """Apply the state table, record counts and notify."""

        seq = item.sequence
        if update or reception:
            self._last_reception = now
        if update:
            self._seen.add(seq)
            if advance:
                if gap > 0 and self._highest is not None:
                    self._missing.update(range(self._highest + 1, seq))
                self._highest = seq if self._highest is None else max(self._highest, seq)
        if fills:
            self._missing.discard(seq)
            self.filled_gap_count += 1
        if gap > 0:
            self.gap_count += 1
        if delivered:
            self.pending += 1
            self.delivered_count += 1
            self._anchor = now
            self._k = 0
        else:
            self.withheld_count += 1
        self.counts[verdict] += 1
        if self.first_sequence is None:
            self.first_sequence = seq
        self.last_sequence = seq
        if age is not None:
            self.max_age_ns = age if self.max_age_ns is None else max(self.max_age_ns, age)
        result = ItemVerdict(item.flow_id, seq, item.origin_ns, now, age, verdict, delivered, gap, fills, diagnostic)
        self.verdicts.append(result)
        if self._listener is not None:
            self._listener.verdict(self.binding, result)
        return result

    def held_buffer(self) -> int:
        """Return the number of delivered items pending in the receiver buffer (design §7)."""

        return self.pending

    def summary(self, held_at_end: int = 0) -> dict[str, Any]:
        """Return the per-flow summary."""

        return {"flowId": self.binding.flow_id, "counts": dict(self.counts), "deliveredCount": self.delivered_count,
                "withheldCount": self.withheld_count, "gapCount": self.gap_count, "filledGapCount": self.filled_gap_count,
                "deadlineMissedCount": self.deadline_missed_count, "queueFullCount": self.counts[QUEUE_FULL],
                "heldAtEnd": held_at_end, "firstSequence": self.first_sequence, "lastSequence": self.last_sequence,
                "maxAgeNs": self.max_age_ns}
