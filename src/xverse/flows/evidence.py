"""Argus evidence of the flow runtime (FR-009; contract rule 13; design §7).

``FlowEvidence`` is the receiver listener. It appends one annotation event per withheld item, per
delivered out-of-order item, per ``gapBefore > 0`` and per deadline miss, and one summary per flow,
through the accepted Argus writer API (producer ``xverse.flows``, extension ``io.xverse.flows``).
Event ids are ``fl.<h>.<kind>.<n>`` with ``h`` the 16-hex-character flow-id hash.
``reconstruct_flows`` recomputes the counts offline from the recorded payloads.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from .binding import FlowBinding, FlowBindingRecord, flow_hash
from .receiver import DELIVERED, OUT_OF_ORDER, VERDICTS, ItemVerdict

EXTENSION = "io.xverse.flows"
PRODUCER = "xverse.flows"
MAX_EVENT_ID = 128


class FlowEvidence:
    """Receiver listener writing Argus annotation events."""

    def __init__(self, writer: Any, run_id: str, clocks: Callable[[int | None], Mapping[str, Any]], tick: Callable[[], int | None] = lambda: None) -> None:
        """Create the listener.

        @param writer Open Argus run writer (``append_event``).
        @param run_id Run identity recorded in the payloads.
        @param clocks Callable returning the clock mapping for a tick (``None``: host/utc only).
        @param tick Callable returning the current tick, or ``None`` outside a tick-driven run.
        """

        self._writer = writer
        self._run_id = run_id
        self._clocks = clocks
        self._tick = tick
        self._sequence = 0
        self._counters: dict[tuple[str, str], int] = {}
        self.event_ids: list[str] = []

    def _event_id(self, flow_id: str, kind: str) -> str:
        """Return the next event id of ``kind`` for ``flow_id``."""

        key = (flow_id, kind)
        self._counters[key] = self._counters.get(key, 0) + 1
        event_id = f"fl.{flow_hash(flow_id)}.{kind}.{self._counters[key]}" if kind != "sum" else f"fl.{flow_hash(flow_id)}.sum"
        if len(event_id) > MAX_EVENT_ID:  # pragma: no cover - bounded by construction
            raise ValueError("event id too long")
        return event_id

    def _append(self, event_id: str, text: str, payload: Mapping[str, Any]) -> None:
        """Append one annotation event."""

        self._sequence += 1
        self._writer.append_event(
            event_id=event_id, producer_id=PRODUCER, event_kind="annotation", producer_sequence=self._sequence,
            clocks=self._clocks(self._tick()), annotation={"text": text},
            extensions={EXTENSION: dict(payload, runId=self._run_id)},
        )
        self.event_ids.append(event_id)

    def verdict(self, binding: FlowBinding, result: ItemVerdict) -> None:
        """Record the verdict events of one item."""

        payload = result.to_json()
        if result.gap_before > 0:
            self._append(self._event_id(binding.flow_id, "g"), f"flow {binding.flow_id} gap {result.gap_before}", dict(payload, event="gap"))
        if not result.delivered:
            self._append(self._event_id(binding.flow_id, "w"), f"flow {binding.flow_id} withheld {result.verdict}", dict(payload, event="withheld"))
        elif result.verdict == OUT_OF_ORDER:
            self._append(self._event_id(binding.flow_id, "o"), f"flow {binding.flow_id} out-of-order delivered", dict(payload, event="out-of-order"))

    def deadline(self, binding: FlowBinding, k: int, now: int) -> None:
        """Record one deadline miss."""

        self._append(self._event_id(binding.flow_id, "d"), f"flow {binding.flow_id} deadline missed",
                     {"flowId": binding.flow_id, "event": "deadline-missed", "k": k, "readingNs": now})

    def summary(self, binding: FlowBinding, summary: Mapping[str, Any]) -> None:
        """Record the per-flow summary."""

        self._append(self._event_id(binding.flow_id, "sum"), f"flow {binding.flow_id} summary", dict(summary, event="summary"))


def _expected_verdict(payload: Mapping[str, Any], binding: FlowBinding) -> str | None:
    """Re-derive the verdict class a recorded item must carry from its own fields and the binding.

    Returns ``None`` when the recorded fields alone cannot decide (duplicate, out-of-order and
    queue-full depend on receiver history, which is checked through counts instead).
    """

    if payload.get("diagnostic") == "XVERSE-FLOW-CLOCK-REGRESSION":
        return "clock-error"
    reception, origin = payload.get("receptionNs"), payload.get("originNs")
    if type(reception) is not int or type(origin) is not int:
        return "invalid"
    age = reception - (origin + binding.mapping.offset_ns)
    if payload.get("ageNs") != age:
        return "invalid"
    if age < -binding.mapping.tolerance_ns:
        return "clock-error"
    stale = binding.freshness_ns > 0 and max(age, 0) > binding.freshness_ns
    if payload.get("verdict") in ("duplicate", "out-of-order"):
        return None
    if payload.get("verdict") == "queue-full":
        return "stale" if stale else None  # stale outranks queue-full and is decidable from the item (N2)
    return "stale" if stale else "delivered"


def reconstruct_flows(payloads: Iterable[Mapping[str, Any]], record: FlowBindingRecord) -> dict[str, dict[str, Any]]:
    """Check recorded ``io.xverse.flows`` payloads against the binding record (contract rule 13).

    Every recorded event's verdict is re-derived where its own fields decide it (age through the
    mapping, tolerance, freshness, regression); counts of withheld, out-of-order, gap and deadline
    events are compared with the per-flow summary; foreign flows, unknown verdicts or events and
    duplicate summaries are reported. Delivered in-order items are counted, not recorded, so their
    verdicts are checked through ``deliveredCount`` only (stated limit).

    @param payloads The extension payloads of a run's flow events, in append order.
    @param record The binding record of the run.
    @return ``{flowId: {"ok": bool, "mismatches": [...]}}`` plus ``"<foreign>"`` when foreign flows appear.
    """

    bindings = {b.flow_id: b for b in record.bindings}
    state = {f: {"withheld": {v: 0 for v in VERDICTS}, "ooo_delivered": 0, "fills": 0, "gap": 0, "deadline": 0,
                 "summaries": [], "bad": []} for f in bindings}
    foreign: list[str] = []
    for payload in payloads:
        flow = payload.get("flowId")
        if flow not in state:
            foreign.append(str(flow))
            continue
        entry = state[flow]
        event = payload.get("event")
        verdict = payload.get("verdict")
        if event in ("withheld", "out-of-order", "gap"):
            if verdict not in VERDICTS:
                entry["bad"].append(f"unknown verdict {verdict!r}")
                continue
            expected = _expected_verdict(payload, bindings[flow])
            if expected == "invalid":
                entry["bad"].append(f"inconsistent age for sequence {payload.get('sequence')}")
            elif expected is not None and expected != verdict:
                entry["bad"].append(f"sequence {payload.get('sequence')}: recorded {verdict}, derived {expected}")
        if event == "withheld":
            if payload.get("delivered"):
                entry["bad"].append("withheld event for a delivered item")
            entry["withheld"][verdict] += 1
        elif event == "out-of-order":
            if verdict != OUT_OF_ORDER or not payload.get("delivered"):
                entry["bad"].append("out-of-order event is not a delivered out-of-order item")
            entry["ooo_delivered"] += 1
            entry["fills"] += 1 if payload.get("fillsGap") else 0
        elif event == "gap":
            if not isinstance(payload.get("gapBefore"), int) or payload["gapBefore"] <= 0:
                entry["bad"].append("gap event without gapBefore > 0")
            entry["gap"] += 1
            if payload.get("delivered") and payload.get("fillsGap"):
                entry["bad"].append("gap event cannot fill a gap")
        elif event == "deadline-missed":
            entry["deadline"] += 1
        elif event == "summary":
            entry["summaries"].append(payload)
        else:
            entry["bad"].append(f"unknown event {event!r}")
    result: dict[str, dict[str, Any]] = {}
    for flow, entry in state.items():
        mismatches = list(entry["bad"])
        if len(entry["summaries"]) != 1:
            mismatches.append(f"{len(entry['summaries'])} summaries")
        else:
            summary = entry["summaries"][0]
            counts = summary.get("counts") or {}
            withheld_total = sum(entry["withheld"].values())
            checks = {
                "withheldCount": withheld_total,
                "gapCount": entry["gap"],
                "deadlineMissedCount": entry["deadline"],
                "queueFullCount": entry["withheld"]["queue-full"],
            }
            for field_name, value in checks.items():
                if summary.get(field_name) != value:
                    mismatches.append(field_name)
            for verdict in ("clock-error", "duplicate", "stale", "queue-full"):
                if counts.get(verdict) != entry["withheld"][verdict]:
                    mismatches.append(f"counts.{verdict}")
            if counts.get(OUT_OF_ORDER) != entry["withheld"][OUT_OF_ORDER] + entry["ooo_delivered"]:
                mismatches.append("counts.out-of-order")
            if summary.get("filledGapCount") != entry["fills"]:
                mismatches.append("filledGapCount")
            delivered = summary.get("deliveredCount")
            if not isinstance(delivered, int) or delivered != counts.get(DELIVERED, -1) + entry["ooo_delivered"]:
                mismatches.append("deliveredCount")
            held = summary.get("heldAtEnd")
            if not isinstance(held, int) or held < 0:
                mismatches.append("heldAtEnd")
        result[flow] = {"ok": not mismatches, "mismatches": mismatches}
    if foreign:
        result["<foreign>"] = {"ok": False, "mismatches": sorted(set(foreign))}
    return result
