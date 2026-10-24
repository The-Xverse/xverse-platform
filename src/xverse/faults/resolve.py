"""Resolution of a compiled Phase 1 fault schedule against the planned tick list (FR-002–FR-004).

Resolution is a pure function of the compiled plan and the planned ticks. It assigns each entry a
boundary class, due and effective ticks (first planned tick at or after the due tick), the exact
compiled duration in ticks, the clearing tick, the tie key and the arbitration, and it fails closed
on unknown kinds, unsupported targets, horizons and undeclared overlaps. Nothing is applied.
"""

from __future__ import annotations

from bisect import bisect_left
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .vocabulary import (
    ARBITRATIONS,
    COLLECTION_BOUNDARY,
    FaultError,
    FaultParameters,
    KindSpec,
    kind_spec,
    validate_parameters,
)

INF = float("inf")


@dataclass(frozen=True)
class ResolvedEntry:
    """One schedule entry with its execution decisions fixed before any run."""

    entry_id: str
    fault_id: str
    fault_kind: str
    boundary_class: str
    executable: bool
    target_uri: str
    target_collection: str
    target_element: str
    trigger_kind: str
    declared_order: int | None
    due_tick: int | None
    effective_tick: int | None
    duration_ticks: int
    clear_tick: int | None
    tie_key: tuple[float, str]
    parameters: FaultParameters
    recovery: str
    activation: str

    @property
    def window(self) -> tuple[int, int] | None:
        """Return ``(effectiveTick, clearTick)`` for time-triggered entries, else ``None``."""

        if self.effective_tick is None or self.clear_tick is None:
            return None
        return (self.effective_tick, self.clear_tick)


def _mapping(value: Any) -> Mapping[str, Any]:
    """Return ``value`` when it is a mapping, else an empty mapping."""

    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    """Return ``value`` when it is a non-string sequence, else an empty tuple."""

    return value if isinstance(value, Sequence) and not isinstance(value, str) else ()


def effective_tick(due: int, planned_ticks: Sequence[int]) -> int | None:
    """Return the first planned tick at or after ``due``, or ``None`` beyond the last planned tick."""

    index = bisect_left(planned_ticks, due)
    return planned_ticks[index] if index < len(planned_ticks) else None


def _planned(planned_ticks: Sequence[int]) -> tuple[int, ...]:
    """Validate the planned tick list (non-empty, non-negative integers, non-decreasing: Maestro
    allows pauses that repeat a tick) and return its distinct ticks in order."""

    ticks = tuple(planned_ticks)
    if not ticks or any(type(tick) is not int or tick < 0 for tick in ticks) or any(b < a for a, b in zip(ticks, ticks[1:])):
        raise FaultError("XVERSE-FAULT-TICKS", "planned ticks must be a non-decreasing list of non-negative integers")
    return tuple(sorted(set(ticks)))


def resolve_entry(entry: Mapping[str, Any], system_uri: str, planned_ticks: Sequence[int]) -> ResolvedEntry:
    """Resolve one compiled entry; fail closed on any rule violation."""

    fault_id = str(entry.get("faultId", ""))
    spec: KindSpec = kind_spec(entry.get("faultKind"))
    target = _mapping(entry.get("targetRef"))
    collection = entry.get("collection")
    element = target.get("element")
    if str(target.get("uri", "")) != system_uri or not isinstance(element, str) or collection not in COLLECTION_BOUNDARY:
        raise FaultError("XVERSE-FAULT-TARGET", f"fault {fault_id!r} targets no System element with a declared boundary")
    boundary = COLLECTION_BOUNDARY[str(collection)]
    if spec.executable and boundary != spec.boundary_class:
        raise FaultError("XVERSE-FAULT-TARGET", f"fault {fault_id!r} kind {spec.kind!r} needs a {spec.boundary_class} target, got {boundary}")
    duration = _mapping(entry.get("duration")).get("ticks")
    if type(duration) is not int or duration < 0:
        raise FaultError("XVERSE-FAULT-DURATION", f"fault {fault_id!r} has no exact compiled tick duration")
    trigger = _mapping(entry.get("trigger"))
    kind = trigger.get("kind")
    ticks = _planned(planned_ticks)
    due = effective = clear = None
    order: int | None = None
    if kind == "time":
        at = trigger.get("atTicks")
        if type(at) is not int or at < 0:
            raise FaultError("XVERSE-FAULT-TRIGGER", f"fault {fault_id!r} time trigger has no resolved tick")
        due = at
        effective = effective_tick(due, ticks)
        clear = None if effective is None else effective_tick(effective + duration, ticks)
        if effective is None or clear is None:
            raise FaultError("XVERSE-FAULT-HORIZON", f"fault {fault_id!r} is due or clears beyond the last planned tick")
    elif kind == "declared-order":
        order = trigger.get("order")
        if type(order) is not int or order < 0:
            raise FaultError("XVERSE-FAULT-TRIGGER", f"fault {fault_id!r} declared-order trigger has no order")
    else:
        raise FaultError("XVERSE-FAULT-TRIGGER", f"fault {fault_id!r} carries no resolvable trigger")
    parameters = validate_parameters(spec, _sequence(entry.get("parameters")), fault_id)
    if "delay-ns" in parameters.values:  # simulator-time parameter (ADR-ML3-SIMTIME-0001); tick mode keeps delay-ticks
        raise FaultError("XVERSE-FAULT-PARAMETER", f"fault {fault_id!r} parameter 'delay-ns' needs a simulation-clock binding")
    return ResolvedEntry(
        entry_id=str(entry.get("entryId", f"fault:{fault_id}")),
        fault_id=fault_id,
        fault_kind=spec.kind,
        boundary_class=spec.boundary_class if spec.executable else boundary,
        executable=spec.executable,
        target_uri=system_uri,
        target_collection=str(collection),
        target_element=element,
        trigger_kind=str(kind),
        declared_order=order,
        due_tick=due,
        effective_tick=effective,
        duration_ticks=duration,
        clear_tick=clear,
        tie_key=(float(order) if order is not None else INF, fault_id),
        parameters=parameters,
        recovery=str(entry.get("recovery", "")),
        activation=str(entry.get("activation", "")),
    )


def validate_static(plan: Mapping[str, Any], horizon_ticks: int) -> tuple[ResolvedEntry, ...]:
    """Validate a compiled schedule before the planned tick list exists (Maestro projection).

    Uses the dense tick list ``0..horizon`` so kinds, targets, parameters, exact durations and the
    horizon are checked; effective ticks are recomputed later against the real planned ticks.
    A ``crash`` whose declared XDL ``recovery`` is not ``manual`` is rejected while decision D5-2
    is open (``XVERSE-FAULT-RECOVERY``).

    @param plan Compiled Phase 1 experiment plan (mapping form).
    @param horizon_ticks The prepared clock horizon.
    @return The statically resolved entries.
    @raises FaultError On any rule violation.
    """

    horizon = int(horizon_ticks)
    if horizon < 0 or horizon > 1_000_000:
        raise FaultError("XVERSE-FAULT-TICKS", "horizon must be a non-negative integer within the engineering cap")
    entries = resolve_schedule(plan, tuple(range(horizon + 1)))  # every integer tick exists statically
    for entry in entries:
        if entry.fault_kind == "crash" and entry.recovery != "manual":
            raise FaultError("XVERSE-FAULT-RECOVERY", f"fault {entry.fault_id!r}: crash recovery {entry.recovery!r} is not supported in Lite (decision DLG-3); declare recovery: manual")
    return entries


def _overlaps(first: ResolvedEntry, second: ResolvedEntry) -> bool:
    """Return whether two entries on one target may hold the target at the same time."""

    if first.window is None or second.window is None:
        return True  # a declared-order entry's window is unknown before the run: conservative
    (a0, a1), (b0, b1) = first.window, second.window
    return a0 < b1 and b0 < a1


def resolve_schedule(plan: Mapping[str, Any], planned_ticks: Sequence[int]) -> tuple[ResolvedEntry, ...]:
    """Resolve every entry of ``plan["faultSchedule"]`` against ``planned_ticks``.

    @param plan Compiled Phase 1 experiment plan (mapping form).
    @param planned_ticks Maestro's planned tick list (ascending, from 0 to the horizon).
    @return Entries in compiled listing order (application order is decided per tick by ``tie_key``).
    @raises FaultError With a stable ``XVERSE-FAULT-*`` code on the first violation.
    """

    selection = _mapping(plan.get("selection"))
    system_uri = str(_mapping(selection.get("system")).get("uri", ""))
    if not system_uri:
        raise FaultError("XVERSE-FAULT-PLAN", "plan selection names no system")
    entries = tuple(resolve_entry(_mapping(item), system_uri, planned_ticks) for item in _sequence(plan.get("faultSchedule")))
    seen: set[str] = set()
    for entry in entries:
        if entry.fault_id in seen:
            raise FaultError("XVERSE-FAULT-PLAN", f"fault id {entry.fault_id!r} is repeated")
        seen.add(entry.fault_id)
    by_target: dict[tuple[str, str], list[ResolvedEntry]] = {}
    for entry in entries:
        if entry.executable:
            by_target.setdefault((entry.target_collection, entry.target_element), []).append(entry)
    for group in by_target.values():
        ordered = sorted(group, key=lambda item: item.tie_key)
        for index, later in enumerate(ordered):
            for earlier in ordered[:index]:
                if not _overlaps(earlier, later):
                    continue
                policy = later.parameters.arbitration
                if policy is None or policy == "reject" or policy not in ARBITRATIONS:
                    raise FaultError("XVERSE-FAULT-OVERLAP", f"faults {earlier.fault_id!r} and {later.fault_id!r} may overlap on one target without serialize/supersede arbitration")
    return entries
