"""Tick-driven, deterministic fault scheduler (FR-003–FR-005, FR-008).

``FaultScheduler.advance(tick)`` is called by Maestro's dispatcher at every planned tick. It clears
entries whose window ends, then applies entries that are due, in ``(declaredOrder or inf,
faultId)`` order, through the exact boundary handles armed at ``start``. Overlaps on one target are
arbitrated as resolved (``serialize`` waits, ``supersede`` cancels the active entry first). Every
entry ends in exactly one outcome; a clearing failure marks the run incomplete and blocks the
target; an application failure ends the run unless the entry declared ``on-apply-failure:
continue``. The decision sequence depends only on the resolved entries, the seed and the ticks.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .boundary import BoundaryHandle, BoundaryOutcome, InjectionBoundary
from .resolve import INF, ResolvedEntry, effective_tick
from .vocabulary import UNEXECUTED, FaultError

APPLIED, CLEARED = "applied", "cleared"
FAILED_TO_APPLY, INCOMPLETE_CLEARING, CANCELLED = "failed-to-apply", "incomplete-clearing", "cancelled"
FINAL_OUTCOMES = (APPLIED, CLEARED, FAILED_TO_APPLY, INCOMPLETE_CLEARING, CANCELLED, UNEXECUTED)


@dataclass(frozen=True)
class Decision:
    """One scheduler decision: what happened to which entry at which tick."""

    tick: int
    entry_id: str
    phase: str
    outcome: str
    diagnostic: str | None = None
    detail: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class _State:
    """Mutable per-entry state."""

    entry: ResolvedEntry
    handle: BoundaryHandle | None = None
    boundary: InjectionBoundary | None = None
    final: str | None = None
    applied_tick: int | None = None
    clear_tick: int | None = None
    waiting: bool = False


class FaultScheduler:
    """Apply and clear resolved entries over the planned ticks through exact boundary handles."""

    def __init__(
        self,
        run_id: str,
        entries: Sequence[ResolvedEntry],
        boundaries: Mapping[tuple[str, str], InjectionBoundary],
        planned_ticks: Sequence[int],
        *,
        seed: int = 0,
        listener: Any = None,
    ) -> None:
        """Create the scheduler.

        @param run_id Run identity every handle is bound to.
        @param entries Resolved entries (from ``resolve_schedule``).
        @param boundaries Map ``(collection, element)`` to the boundary owning that target.
        @param planned_ticks Maestro's planned tick list.
        @param seed Run seed (the relays derive their generators from it; recorded in decisions).
        @param listener Optional object with ``decision(entry, decision)`` called for every decision.
        """

        self.run_id = run_id
        self.seed = int(seed)
        self._ticks = tuple(planned_ticks)
        self._boundaries = dict(boundaries)
        self._states: dict[str, _State] = {entry.entry_id: _State(entry) for entry in entries}
        self._listener = listener
        self.decisions: list[Decision] = []
        self.blocked_targets: set[tuple[str, str]] = set()
        self.incomplete = False
        self.run_failed = False
        self.failure_diagnostic: str | None = None
        self._started = False

    # -- helpers -------------------------------------------------------------------------------

    def _record(self, tick: int, state: _State, phase: str, outcome: str, diagnostic: str | None = None, **detail: Any) -> Decision:
        """Append a decision and notify the listener."""

        decision = Decision(tick, state.entry.entry_id, phase, outcome, diagnostic, dict(detail))
        self.decisions.append(decision)
        if self._listener is not None:
            self._listener.decision(state.entry, decision)
        return decision

    def _finalize(self, tick: int, state: _State, outcome: str, diagnostic: str | None = None, **detail: Any) -> None:
        """Set the entry's single final outcome (first final outcome wins)."""

        if state.final is None:
            state.final = outcome
            self._record(tick, state, "final", outcome, diagnostic, **detail)

    def _target(self, entry: ResolvedEntry) -> tuple[str, str]:
        """Return the target key of ``entry``."""

        return (entry.target_collection, entry.target_element)

    def _active_on(self, target: tuple[str, str]) -> _State | None:
        """Return the state currently applied on ``target``."""

        for state in self._states.values():
            if state.applied_tick is not None and state.clear_tick is None and state.final is None and self._target(state.entry) == target:
                return state
        return None

    # -- lifecycle -----------------------------------------------------------------------------

    def start(self) -> None:
        """Arm every executable entry; declared-only entries are finalized as not executed."""

        if self._started:
            raise FaultError("XVERSE-FAULT-SCHEDULER", "scheduler already started")
        self._started = True
        for state in sorted(self._states.values(), key=lambda item: item.entry.tie_key):
            entry = state.entry
            if not entry.executable:
                self._finalize(self._ticks[0], state, UNEXECUTED, "XVERSE-FAULT-DECLARED-ONLY")
                continue
            boundary = self._boundaries.get(self._target(entry))
            if boundary is None:
                self._finalize(self._ticks[0], state, FAILED_TO_APPLY, "XVERSE-FAULT-TARGET", reason="no boundary for target")
                self._fail(state)
                continue
            issued = boundary.arm(self.run_id, entry)
            if isinstance(issued, BoundaryOutcome):
                self._finalize(self._ticks[0], state, FAILED_TO_APPLY, issued.diagnostic, **dict(issued.detail))
                self._fail(state)
                continue
            state.handle, state.boundary = issued, boundary

    def _fail(self, state: _State) -> None:
        """Apply the entry's failure policy to the run."""

        if state.entry.parameters.on_apply_failure != "continue" and not self.run_failed:
            self.run_failed = True
            self.failure_diagnostic = f"fault {state.entry.fault_id} failed to apply"

    def _due(self, state: _State, tick: int) -> bool:
        """Return whether ``state`` is due at ``tick``."""

        entry = state.entry
        if state.final is not None or state.applied_tick is not None or state.handle is None:
            return False
        if entry.trigger_kind == "time":
            return entry.effective_tick is not None and tick >= entry.effective_tick
        lower = [s for s in self._states.values() if s.entry.declared_order is not None and s.entry.declared_order < (entry.declared_order or 0)]
        return all(s.applied_tick is not None or s.final is not None for s in lower)

    def _apply(self, state: _State, tick: int) -> None:
        """Apply ``state`` at ``tick`` after arbitration on its target."""

        entry = state.entry
        target = self._target(entry)
        if target in self.blocked_targets:
            self._finalize(tick, state, CANCELLED, "XVERSE-FAULT-TARGET-BLOCKED")
            return
        active = self._active_on(target)
        if active is not None:
            policy = entry.parameters.arbitration
            if policy == "serialize":
                if not state.waiting:
                    state.waiting = True
                    self._record(tick, state, "arbitration", "waiting", detail_policy="serialize", active=active.entry.entry_id)
                return
            if policy == "supersede":
                self._clear(active, tick, superseded_by=entry.entry_id)
                if self._target(entry) in self.blocked_targets:
                    self._finalize(tick, state, CANCELLED, "XVERSE-FAULT-TARGET-BLOCKED")
                    return
            else:
                self._finalize(tick, state, CANCELLED, "XVERSE-FAULT-OVERLAP")
                return
        parameters = dict(entry.parameters.values, _kind=entry.fault_kind)
        outcome = state.boundary.apply(state.handle, tick, parameters)
        if not outcome.ok:
            self._record(tick, state, "apply", "apply-failed", outcome.diagnostic, **dict(outcome.detail))
            self._finalize(tick, state, FAILED_TO_APPLY, outcome.diagnostic)
            self._fail(state)
            return
        state.applied_tick = tick
        state.waiting = False
        window_end = tick + entry.duration_ticks
        state.clear_tick = None
        state.entry_clear_at = effective_tick(window_end, self._ticks) if window_end > tick else tick  # type: ignore[attr-defined]
        self._record(tick, state, "apply", APPLIED, effective_tick=tick, window_end=window_end, clear_at=state.entry_clear_at)

    def _clear(self, state: _State, tick: int, *, superseded_by: str | None = None) -> None:
        """Clear ``state`` at ``tick``; failure blocks the target and marks the run incomplete."""

        outcome = state.boundary.clear(state.handle, tick)
        if not outcome.ok:
            self._record(tick, state, "clear", "clear-failed", outcome.diagnostic, **dict(outcome.detail))
            self.blocked_targets.add(self._target(state.entry))
            self.incomplete = True
            self._finalize(tick, state, INCOMPLETE_CLEARING, outcome.diagnostic)
            state.clear_tick = tick
            return
        state.clear_tick = tick
        if superseded_by is not None:
            self._record(tick, state, "clear", CLEARED, superseded_by=superseded_by)
            self._finalize(tick, state, CANCELLED, "XVERSE-FAULT-SUPERSEDED", superseded_by=superseded_by)
        else:
            self._record(tick, state, "clear", CLEARED)
            self._finalize(tick, state, CLEARED)

    def advance(self, tick: int) -> list[Decision]:
        """Run clearing then application for ``tick``; return the decisions taken at this tick."""

        if not self._started:
            raise FaultError("XVERSE-FAULT-SCHEDULER", "advance before start")
        if tick not in self._ticks:
            raise FaultError("XVERSE-FAULT-TICKS", f"tick {tick} is not a planned tick")
        before = len(self.decisions)
        for state in sorted(self._states.values(), key=lambda item: item.entry.tie_key):
            clear_at = getattr(state, "entry_clear_at", None)
            if state.applied_tick is not None and state.clear_tick is None and state.final is None and clear_at is not None and tick >= clear_at:
                self._clear(state, tick)
        if not self.run_failed:
            for state in sorted(self._states.values(), key=lambda item: item.entry.tie_key):
                if self._due(state, tick):
                    self._apply(state, tick)
                    if self.run_failed:
                        break
        return self.decisions[before:]

    def cancel(self, tick: int, reason: str = "cancelled") -> list[Decision]:
        """Clear every active entry and finalize the rest as cancelled."""

        before = len(self.decisions)
        for state in sorted(self._states.values(), key=lambda item: item.entry.tie_key):
            if state.applied_tick is not None and state.clear_tick is None and state.final is None:
                self._clear(state, tick, superseded_by=None)
                if state.final == CLEARED:
                    state.final = None
                    self._states[state.entry.entry_id].final = CANCELLED
                    self._record(tick, state, "final", CANCELLED, "XVERSE-FAULT-CANCELLED", reason=reason)
            elif state.final is None:
                self._finalize(tick, state, CANCELLED, "XVERSE-FAULT-CANCELLED", reason=reason)
        return self.decisions[before:]

    def finish(self, tick: int) -> dict[str, str]:
        """Finalize every entry at the end of the run; return the final outcome per entry id."""

        for state in sorted(self._states.values(), key=lambda item: item.entry.tie_key):
            if state.final is None:
                if state.applied_tick is not None and state.clear_tick is None:
                    self._clear(state, tick)
                else:
                    self._finalize(tick, state, CANCELLED, "XVERSE-FAULT-NEVER-DUE")
        for state in self._states.values():
            if state.boundary is not None and state.handle is not None:
                state.boundary.release(state.handle)
        if any(state.final not in FINAL_OUTCOMES for state in self._states.values()):
            self.incomplete = True
        return {entry_id: state.final or CANCELLED for entry_id, state in self._states.items()}

    @property
    def outcomes(self) -> dict[str, str | None]:
        """Return the current final outcome per entry id (``None`` while pending)."""

        return {entry_id: state.final for entry_id, state in self._states.items()}
