"""Tick-driven flow harness (D6-11; detailed design §8; data model "Per-tick order").

``FlowRunHarness`` builds one Phase 5 message relay and one receiver per bound flow and drives
the Phase 5 ``FaultScheduler`` over the experiment plan's planned ticks. Per tick: advance the
scheduler (clears, then applies); drain each relay's release outbox, then its delayed items;
pass the sender items offered at that tick through the relay; let the receiver judge them and
poll. After ``finish`` or ``cancel`` the outboxes are drained once more and every receiver makes a
final poll, so nothing a relay releases bypasses the receiver (gate G3). The Maestro dispatcher
is not involved.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from xverse.faults.boundary import MessageRelayBoundary
from xverse.faults.resolve import ResolvedEntry
from xverse.faults.scheduler import FaultScheduler

from .binding import FlowBindingRecord
from .clock import TickClock
from .codes import HARNESS, FlowError
from .receiver import FlowItem, FlowReceiver

COMPLETED, INCOMPLETE, FAILED = "completed", "incomplete", "failed"


@dataclass(frozen=True)
class HarnessResult:
    """Outcome of one harness run."""

    status: str
    final_tick: int
    summaries: Mapping[str, Mapping[str, Any]]
    outcomes: Mapping[str, str]
    held_at_end: Mapping[str, int]
    incomplete: bool
    failure: str | None = None
    decisions: tuple[Any, ...] = field(default_factory=tuple)


class FlowRunHarness:
    """Drive bound flows, their relays and receivers over planned ticks."""

    def __init__(self, record: FlowBindingRecord, plan_ticks: Sequence[int], entries: Sequence[ResolvedEntry], *,
                 seed: int, clock: TickClock, listener: Any = None, run_id: str = "flows-harness", drain: bool = True) -> None:
        """Create the harness.

        @param record An activatable binding record.
        @param plan_ticks The experiment plan's planned ticks (repeats are removed).
        @param entries Resolved fault entries (``resolve_schedule``); message faults target ``flows``.
        @param seed Run seed for the relays and the scheduler.
        @param clock Deterministic tick clock shared by senders and receivers.
        @param listener Optional ``FlowEvidence``-like listener.
        @param run_id Run identity for fault handles.
        @param drain Whether receivers drain their buffers at each poll.
        """

        if not record.activatable():
            raise FlowError(HARNESS, "the binding record is not activatable")
        ticks = tuple(sorted(set(int(t) for t in plan_ticks)))
        if not ticks:
            raise FlowError(HARNESS, "no planned ticks")
        self.record = record
        self.ticks = ticks
        self.clock = clock
        self._listener = listener
        self._offers: dict[int, dict[str, list[int]]] = {}
        self.relays = {b.flow_id: MessageRelayBoundary(b.flow_id, seed=seed) for b in record.bindings}
        self.receivers = {b.flow_id: FlowReceiver(b, clock, listener=listener, drain=drain) for b in record.bindings}
        boundaries = {("flows", flow_id): relay for flow_id, relay in self.relays.items()}
        self.scheduler = FaultScheduler(run_id, entries, boundaries, ticks, seed=seed, listener=None)
        self._started = False
        self._finished = False

    def offer(self, tick: int, flow_id: str, sequence: int) -> None:
        """Queue sender item ``sequence`` of ``flow_id`` for ``tick``."""

        if flow_id not in self.relays:
            raise FlowError(HARNESS, f"flow {flow_id!r} is not bound")
        if tick not in self.ticks:
            raise FlowError(HARNESS, f"tick {tick} is not a planned tick")
        self._offers.setdefault(int(tick), {}).setdefault(flow_id, []).append(int(sequence))

    def _receive_all(self, flow_id: str, items: Sequence[Any]) -> None:
        """Hand relay output to the flow's receiver in order."""

        receiver = self.receivers[flow_id]
        for item in items:
            receiver.receive(item)

    def _drain_outboxes(self) -> None:
        """Forward every relay's released items to its receiver."""

        for flow_id in sorted(self.relays):
            self._receive_all(flow_id, self.relays[flow_id].take_outbox())

    def _final(self) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
        """Final drain and poll; return summaries and held counts; emit summaries."""

        self._drain_outboxes()
        summaries: dict[str, dict[str, Any]] = {}
        held: dict[str, int] = {}
        for flow_id in sorted(self.receivers):
            receiver = self.receivers[flow_id]
            receiver.poll()
            held[flow_id] = self.relays[flow_id].held_count()
            summaries[flow_id] = receiver.summary(held_at_end=held[flow_id])
            if self._listener is not None:
                self._listener.summary(receiver.binding, summaries[flow_id])
        return summaries, held

    def run(self) -> HarnessResult:
        """Drive every planned tick (design §8 lifecycle)."""

        tick = self.ticks[0]
        outcomes: Mapping[str, Any] = {}
        try:
            self.clock.at(tick)
            self.scheduler.start()
            self._started = True
            for receiver in self.receivers.values():
                receiver.activate()
            for tick in self.ticks:
                self.clock.at(tick)
                self.scheduler.advance(tick)
                if self.scheduler.run_failed:
                    self.scheduler.cancel(tick, "run-failed")
                    outcomes = {k: v or "cancelled" for k, v in self.scheduler.outcomes.items()}
                    summaries, held = self._final()
                    return HarnessResult(FAILED, tick, summaries, outcomes, held, True, self.scheduler.failure_diagnostic,
                                         tuple(self.scheduler.decisions))
                for flow_id in sorted(self.relays):
                    relay = self.relays[flow_id]
                    self._receive_all(flow_id, relay.take_outbox())
                    self._receive_all(flow_id, relay.drain(tick))
                    for sequence in sorted(self._offers.get(tick, {}).get(flow_id, ())):
                        binding = self.receivers[flow_id].binding
                        item = FlowItem(flow_id, sequence, self.clock.read(binding.sender_domain))
                        self._receive_all(flow_id, relay.submit(item, tick))
                    self.receivers[flow_id].poll()
            outcomes = self.scheduler.finish(tick)
            self._finished = True
            summaries, held = self._final()
        except Exception as error:
            if self._started and not self._finished:
                self.scheduler.cancel(tick, "harness-error")
                outcomes = {k: v or "cancelled" for k, v in self.scheduler.outcomes.items()}
            try:
                self._final()
            except Exception:  # pragma: no cover - cleanup must not mask the original error
                pass
            raise error
        incomplete = bool(self.scheduler.incomplete) or any(held.values())
        return HarnessResult(INCOMPLETE if incomplete else COMPLETED, tick, summaries, dict(outcomes), held, incomplete, None,
                             tuple(self.scheduler.decisions))
