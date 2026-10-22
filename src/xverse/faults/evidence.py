"""Argus evidence for fault schedules (FR-007): one annotation event per decision, causally chained.

``FaultEvidence`` is the scheduler listener. It writes an ``intent`` event per executable entry at
``start`` and one event per later decision through the accepted Argus writer API, with the
``io.xverse.faults`` extension carrying the entry, phase, tick, outcome and diagnostic. Causation
runs intent → apply decision → clear decision. ``reconstruct`` rebuilds the per-entry chains
offline from the run's records and reports whether every applied entry was cleared.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .resolve import ResolvedEntry
from .scheduler import APPLIED, CLEARED, Decision

EXTENSION = "io.xverse.faults"
PRODUCER = "xverse.faults"


def closure_obligation(obligation_id: str = "faults-causal-closure") -> dict[str, Any]:
    """Return the run-level ``causal-closure`` obligation the fault chain must satisfy."""

    return {"obligationId": obligation_id, "kind": "causal-closure", "required": True, "detail": {"producer": PRODUCER}}


class FaultEvidence:
    """Scheduler listener writing Argus annotation events through an open writer."""

    def __init__(self, writer: Any, run_id: str, clocks: Callable[[int], Mapping[str, Any]]) -> None:
        """Create the listener.

        @param writer Open Argus run writer (``append_event``).
        @param run_id Run identity (recorded in the extension payloads; not a causal reference).
        @param clocks Callable returning the host/utc/simulation clock mapping for a tick.
        """

        self._writer = writer
        self._run_id = run_id
        self._clocks = clocks
        self._sequence = 0
        self._intent: dict[str, str] = {}
        self._last: dict[str, str] = {}
        self.event_ids: list[str] = []

    def _append(self, event_id: str, cause: str | None, tick: int, text: str, payload: Mapping[str, Any], correlation: str | None = None) -> str:
        """Append one annotation event and return its id.

        Argus resolves correlation and causation ids against accepted events, so decisions
        correlate to their entry's intent event; the intent itself carries no correlation.
        """

        self._sequence += 1
        self._writer.append_event(
            event_id=event_id,
            producer_id=PRODUCER,
            event_kind="annotation",
            producer_sequence=self._sequence,
            correlation_id=correlation,
            causation_id=cause,
            clocks=self._clocks(tick),
            annotation={"text": text},
            extensions={EXTENSION: dict(payload)},
        )
        self.event_ids.append(event_id)
        return event_id

    def intent(self, entry: ResolvedEntry, tick: int) -> str:
        """Write the intent event of ``entry`` (before any application)."""

        event_id = f"fault.{entry.fault_id}.intent"
        payload = {
            "entryId": entry.entry_id, "faultId": entry.fault_id, "faultKind": entry.fault_kind,
            "boundaryClass": entry.boundary_class, "phase": "intent", "tick": tick,
            "dueTick": entry.due_tick, "effectiveTick": entry.effective_tick, "durationTicks": entry.duration_ticks,
            "parameters": dict(entry.parameters.values), "executable": entry.executable, "runId": self._run_id,
        }
        self._intent[entry.entry_id] = self._last[entry.entry_id] = self._append(event_id, None, tick, "fault intent " + entry.fault_id, payload)
        return event_id

    def decision(self, entry: ResolvedEntry, decision: Decision) -> None:
        """Write one event for a scheduler decision, chained to the entry's previous event."""

        if entry.entry_id not in self._intent:
            self.intent(entry, decision.tick)
        phase = decision.phase if decision.phase != "final" else "outcome"
        event_id = f"fault.{entry.fault_id}.{phase}.{self._sequence + 1}"
        payload = {
            "entryId": entry.entry_id, "faultId": entry.fault_id, "faultKind": entry.fault_kind,
            "boundaryClass": entry.boundary_class, "phase": phase, "tick": decision.tick,
            "outcome": decision.outcome, "diagnostic": decision.diagnostic, "detail": dict(decision.detail),
        }
        cause = self._last[entry.entry_id]
        self._last[entry.entry_id] = self._append(event_id, cause, decision.tick, f"fault {entry.fault_id} {phase} {decision.outcome}", payload, correlation=self._intent[entry.entry_id])


@dataclass
class Chain:
    """Reconstructed per-entry chain."""

    fault_id: str
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def phases(self) -> list[tuple[str, str | None]]:
        """Return ``(phase, outcome)`` pairs in record order."""

        return [(e[EXTENSION]["phase"], e[EXTENSION].get("outcome")) for e in self.events]

    @property
    def applied(self) -> bool:
        """Return whether an ``apply`` decision succeeded."""

        return any(p == "apply" and o == APPLIED for p, o in self.phases)

    @property
    def cleared(self) -> bool:
        """Return whether a ``clear`` decision succeeded."""

        return any(p == "clear" and o == CLEARED for p, o in self.phases)

    @property
    def status(self) -> str:
        """Return ``closed``, ``open``, ``apply-failed`` or ``not-applied``."""

        if self.applied:
            return "closed" if self.cleared else "open"
        if any(o == "apply-failed" for _, o in self.phases):
            return "apply-failed"
        return "not-applied"


def reconstruct(records: Sequence[Mapping[str, Any]]) -> dict[str, Chain]:
    """Rebuild the fault chains from Argus records and verify their causation links.

    @param records Records as returned by ``EvidenceReader.records()``.
    @return Mapping fault id to its chain, in record order; chains with a broken causation link are
            marked by a ``broken`` key in their last event.
    """

    by_id: dict[str, Mapping[str, Any]] = {}
    chains: dict[str, Chain] = {}
    for record in records:
        extensions = record.get("extensions") if isinstance(record, Mapping) else None
        if not isinstance(extensions, Mapping) or EXTENSION not in extensions:
            continue
        event_id = str(record.get("eventId"))
        by_id[event_id] = record
        fault_id = str(extensions[EXTENSION].get("faultId"))
        chain = chains.setdefault(fault_id, Chain(fault_id))
        cause = record.get("causationId")
        entry = {"eventId": event_id, "causationId": cause, EXTENSION: dict(extensions[EXTENSION])}
        if cause is not None and cause not in by_id:
            entry["broken"] = True
        chain.events.append(entry)
    return chains


def closure_report(chains: Mapping[str, Chain]) -> dict[str, Any]:
    """Summarize per-entry closure; ``complete`` is false when an applied entry stayed open."""

    statuses = {fault_id: chain.status for fault_id, chain in chains.items()}
    broken = sorted(f for f, c in chains.items() if any(e.get("broken") for e in c.events))
    return {"statuses": statuses, "open": sorted(f for f, s in statuses.items() if s == "open"), "broken": broken,
            "complete": not any(s == "open" for s in statuses.values()) and not broken}
