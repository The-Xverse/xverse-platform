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


def reconstruct_flows(payloads: Iterable[Mapping[str, Any]], record: FlowBindingRecord) -> dict[str, dict[str, Any]]:
    """Recompute per-flow counts from recorded ``io.xverse.flows`` payloads and compare summaries.

    @param payloads The extension payloads of a run's flow events, in append order.
    @param record The binding record of the run.
    @return ``{flowId: {"ok": bool, "mismatches": [...]}}``.
    """

    bound = {b.flow_id for b in record.bindings}
    seen: dict[str, dict[str, Any]] = {f: {"withheld": 0, "gap": 0, "deadline": 0, "verdicts": {v: 0 for v in VERDICTS}, "summary": None} for f in bound}
    for payload in payloads:
        flow = payload.get("flowId")
        if flow not in seen:
            continue
        state = seen[flow]
        event = payload.get("event")
        if event == "withheld":
            state["withheld"] += 1
            state["verdicts"][payload["verdict"]] += 1
            if payload.get("verdict") == DELIVERED or payload.get("delivered"):
                state.setdefault("bad", []).append("withheld event for a delivered item")
        elif event == "gap":
            state["gap"] += 1
        elif event == "deadline-missed":
            state["deadline"] += 1
        elif event == "summary":
            state["summary"] = payload
    result: dict[str, dict[str, Any]] = {}
    for flow, state in seen.items():
        mismatches = list(state.get("bad", []))
        summary = state["summary"]
        if summary is None:
            mismatches.append("no summary")
        else:
            if summary.get("withheldCount") != state["withheld"]:
                mismatches.append("withheldCount")
            if summary.get("gapCount") != state["gap"]:
                mismatches.append("gapCount")
            if summary.get("deadlineMissedCount") != state["deadline"]:
                mismatches.append("deadlineMissedCount")
            for verdict, count in state["verdicts"].items():
                if verdict != DELIVERED and verdict != OUT_OF_ORDER and summary.get("counts", {}).get(verdict) != count:
                    mismatches.append(f"counts.{verdict}")
        result[flow] = {"ok": not mismatches, "mismatches": mismatches}
    return result
