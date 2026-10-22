"""Injection boundaries: the only places a fault may act, each guarded by an exact handle (FR-006).

A boundary issues one opaque handle per (run, entry) on ``arm``; ``apply``, ``clear`` and
``revalidate`` accept that exact handle only. The message and observation relays are owned
in-process fixtures with the same protocol the Phase 6 X-COM-backed boundary will implement. The
process boundary wraps an owned process operation set (Maestro's launcher ``fault`` operation on
its ``OwnedResourceHandle``) and never discovers or signals anything else.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
import hashlib
import secrets
from typing import Any, Protocol

from .resolve import ResolvedEntry
from .vocabulary import MESSAGE, OBSERVATION, PROCESS

HANDLE_DIAGNOSTIC = "XVERSE-FAULT-HANDLE"


@dataclass(frozen=True)
class BoundaryHandle:
    """Opaque handle bound to one run, one entry and one boundary instance."""

    run_id: str
    entry_id: str
    boundary_class: str
    nonce: str


@dataclass(frozen=True)
class BoundaryOutcome:
    """Result of one boundary operation; ``ok`` false carries a public-safe diagnostic."""

    ok: bool
    diagnostic: str | None = None
    detail: Mapping[str, Any] = field(default_factory=dict)


class InjectionBoundary(Protocol):
    """Operations every boundary class offers to the scheduler."""

    boundary_class: str

    def arm(self, run_id: str, entry: ResolvedEntry) -> BoundaryHandle | BoundaryOutcome: ...

    def apply(self, handle: BoundaryHandle, tick: int, parameters: Mapping[str, Any]) -> BoundaryOutcome: ...

    def clear(self, handle: BoundaryHandle, tick: int) -> BoundaryOutcome: ...

    def revalidate(self, handle: BoundaryHandle) -> bool: ...

    def release(self, handle: BoundaryHandle) -> None: ...


class CounterGenerator:
    """Seeded, counter-based unit-interval generator (no ``random`` module state)."""

    def __init__(self, seed: int, salt: str) -> None:
        """Create the generator for ``seed`` and a per-entry ``salt``."""

        self._seed, self._salt, self._counter = int(seed), salt, 0

    def next(self) -> float:
        """Return the next value in [0, 1) as a pure function of (seed, salt, counter)."""

        digest = hashlib.sha256(f"{self._seed}:{self._salt}:{self._counter}".encode()).digest()
        self._counter += 1
        return int.from_bytes(digest[:8], "big") / float(1 << 64)


class _HandleRegistry:
    """Exact-handle bookkeeping shared by the boundary classes."""

    def __init__(self, boundary_class: str) -> None:
        """Create an empty registry for ``boundary_class``."""

        self.boundary_class = boundary_class
        self._issued: dict[tuple[str, str], BoundaryHandle] = {}

    def issue(self, run_id: str, entry: ResolvedEntry) -> BoundaryHandle | BoundaryOutcome:
        """Issue one handle per (run, entry); a second request is refused."""

        key = (run_id, entry.entry_id)
        if key in self._issued:
            return BoundaryOutcome(False, HANDLE_DIAGNOSTIC, {"reason": "already-armed"})
        handle = BoundaryHandle(run_id, entry.entry_id, self.boundary_class, secrets.token_hex(16))
        self._issued[key] = handle
        return handle

    def check(self, handle: Any) -> bool:
        """Return whether ``handle`` is exactly one this registry issued and not released."""

        return isinstance(handle, BoundaryHandle) and self._issued.get((handle.run_id, handle.entry_id)) == handle

    def release(self, handle: Any) -> None:
        """Forget ``handle`` when it is one of ours."""

        if self.check(handle):
            del self._issued[(handle.run_id, handle.entry_id)]


@dataclass
class _ActiveMessageFault:
    """State of the fault currently applied on a message relay."""

    kind: str
    parameters: Mapping[str, Any]
    since_tick: int
    generator: CounterGenerator | None = None
    counter: int = 0


class MessageRelayBoundary:
    """Owned in-process message relay for one declared flow.

    ``submit(item, tick)`` returns the items delivered at this tick in order; ``drain(tick)``
    releases delayed items whose hold has elapsed. Counters expose what happened for the tests.
    """

    boundary_class = MESSAGE

    def __init__(self, target_element: str, *, seed: int = 0) -> None:
        """Create a relay for ``target_element`` with the run ``seed`` for ratio-based loss."""

        self.target_element = target_element
        self._seed = seed
        self._registry = _HandleRegistry(MESSAGE)
        self._active: dict[str, _ActiveMessageFault] = {}
        self._held: list[tuple[int, Any]] = []
        self._last_delivered: Any = None
        self.delivered: list[tuple[int, Any]] = []
        self.dropped: list[tuple[int, Any]] = []
        self.replayed: list[tuple[int, Any]] = []
        self.refuse_apply = False
        self.refuse_clear = False

    def arm(self, run_id: str, entry: ResolvedEntry) -> BoundaryHandle | BoundaryOutcome:
        """Issue the exact handle for ``entry`` (message kinds only)."""

        if entry.boundary_class != MESSAGE or entry.target_element != self.target_element:
            return BoundaryOutcome(False, "XVERSE-FAULT-TARGET", {"reason": "boundary mismatch"})
        return self._registry.issue(run_id, entry)

    def apply(self, handle: BoundaryHandle, tick: int, parameters: Mapping[str, Any]) -> BoundaryOutcome:
        """Start holding, dropping or replaying according to the entry's kind."""

        if not self._registry.check(handle):
            return BoundaryOutcome(False, HANDLE_DIAGNOSTIC)
        if self.refuse_apply:
            return BoundaryOutcome(False, "XVERSE-FAULT-BOUNDARY-REFUSED", {"reason": "fixture refusal"})
        kind = str(parameters.get("_kind", ""))
        if self._active:
            return BoundaryOutcome(False, "XVERSE-FAULT-BOUNDARY-BUSY", {"active": sorted(self._active)})
        generator = CounterGenerator(self._seed, handle.entry_id) if "loss-ratio" in parameters else None
        self._active[handle.entry_id] = _ActiveMessageFault(kind, dict(parameters), tick, generator)
        return BoundaryOutcome(True, detail={"kind": kind, "tick": tick})

    def clear(self, handle: BoundaryHandle, tick: int) -> BoundaryOutcome:
        """Stop the fault; delayed items are released at this tick."""

        if not self._registry.check(handle) or handle.entry_id not in self._active:
            return BoundaryOutcome(False, HANDLE_DIAGNOSTIC)
        if self.refuse_clear:
            return BoundaryOutcome(False, "XVERSE-FAULT-BOUNDARY-REFUSED", {"reason": "fixture refusal"})
        del self._active[handle.entry_id]
        released = [item for _, item in self._held]
        for item in released:
            self._deliver(tick, item)
        self._held.clear()
        return BoundaryOutcome(True, detail={"released": len(released), "tick": tick})

    def revalidate(self, handle: BoundaryHandle) -> bool:
        """Return whether ``handle`` is exactly one this relay issued."""

        return self._registry.check(handle)

    def release(self, handle: BoundaryHandle) -> None:
        """Forget ``handle``; any active fault of it is dropped without delivery changes."""

        self._active.pop(getattr(handle, "entry_id", None), None)
        self._registry.release(handle)

    def _deliver(self, tick: int, item: Any) -> None:
        """Record a delivery."""

        self._last_delivered = item
        self.delivered.append((tick, item))

    def drain(self, tick: int) -> list[Any]:
        """Release delayed items whose hold elapsed by ``tick``; return them in order."""

        released: list[Any] = []
        remaining: list[tuple[int, Any]] = []
        for due, item in self._held:
            if tick >= due:
                self._deliver(tick, item)
                released.append(item)
            else:
                remaining.append((due, item))
        self._held = remaining
        return released

    def submit(self, item: Any, tick: int) -> list[Any]:
        """Offer ``item`` at ``tick``; return what the relay delivers now (possibly a replay)."""

        released = self.drain(tick)
        active = next(iter(self._active.values()), None)
        if active is None:
            self._deliver(tick, item)
            return released + [item]
        if active.kind == "delay":
            self._held.append((tick + int(active.parameters["delay-ticks"]), item))
            return released
        if active.kind == "loss":
            active.counter += 1
            drop = (active.counter % int(active.parameters["every"]) == 0) if "every" in active.parameters else (active.generator.next() < float(active.parameters["loss-ratio"]))
            if drop:
                self.dropped.append((tick, item))
                return released
            self._deliver(tick, item)
            return released + [item]
        if active.kind == "stale":
            if self._last_delivered is None:
                self.dropped.append((tick, item))
                return released
            self.replayed.append((tick, self._last_delivered))
            self.delivered.append((tick, self._last_delivered))
            return released + [self._last_delivered]
        return BoundaryOutcome(False, "XVERSE-FAULT-KIND")  # pragma: no cover - resolution prevents it


class ObservationRelayBoundary:
    """Owned in-process observation relay for one declared sensor output."""

    boundary_class = OBSERVATION

    def __init__(self, target_element: str) -> None:
        """Create a relay for ``target_element``."""

        self.target_element = target_element
        self._registry = _HandleRegistry(OBSERVATION)
        self._active: str | None = None
        self.delivered: list[tuple[int, Any]] = []
        self.suppressed: list[tuple[int, Any]] = []
        self.refuse_clear = False

    def arm(self, run_id: str, entry: ResolvedEntry) -> BoundaryHandle | BoundaryOutcome:
        """Issue the exact handle for ``entry`` (observation kinds only)."""

        if entry.boundary_class != OBSERVATION or entry.target_element != self.target_element:
            return BoundaryOutcome(False, "XVERSE-FAULT-TARGET", {"reason": "boundary mismatch"})
        return self._registry.issue(run_id, entry)

    def apply(self, handle: BoundaryHandle, tick: int, parameters: Mapping[str, Any]) -> BoundaryOutcome:
        """Start suppressing observations."""

        if not self._registry.check(handle):
            return BoundaryOutcome(False, HANDLE_DIAGNOSTIC)
        if self._active is not None:
            return BoundaryOutcome(False, "XVERSE-FAULT-BOUNDARY-BUSY")
        self._active = handle.entry_id
        return BoundaryOutcome(True, detail={"tick": tick})

    def clear(self, handle: BoundaryHandle, tick: int) -> BoundaryOutcome:
        """Resume observations."""

        if not self._registry.check(handle) or self._active != handle.entry_id:
            return BoundaryOutcome(False, HANDLE_DIAGNOSTIC)
        if self.refuse_clear:
            return BoundaryOutcome(False, "XVERSE-FAULT-BOUNDARY-REFUSED")
        self._active = None
        return BoundaryOutcome(True, detail={"tick": tick})

    def revalidate(self, handle: BoundaryHandle) -> bool:
        """Return whether ``handle`` is exactly one this relay issued."""

        return self._registry.check(handle)

    def release(self, handle: BoundaryHandle) -> None:
        """Forget ``handle``."""

        if self._active == getattr(handle, "entry_id", None):
            self._active = None
        self._registry.release(handle)

    def observe(self, sample: Any, tick: int) -> bool:
        """Offer ``sample``; return whether it was delivered (false while suppressed)."""

        if self._active is not None:
            self.suppressed.append((tick, sample))
            return False
        self.delivered.append((tick, sample))
        return True


class OwnedProcessOperations(Protocol):
    """What a process boundary needs from an owned process: Maestro's launcher ``fault`` operation."""

    def fault(self, operation: str) -> BoundaryOutcome: ...

    def revalidate(self) -> bool: ...


class ProcessBoundary:
    """Process faults on one owned unit through its owned operation set (kill, freeze, thaw)."""

    boundary_class = PROCESS

    def __init__(self, target_element: str, operations: OwnedProcessOperations, *, intend: Callable[[str, int], None] | None = None) -> None:
        """Create the boundary for ``target_element`` over ``operations``.

        @param target_element Component instance id the boundary acts on.
        @param operations Owned operation set bound to the unit's exact handle.
        @param intend Callback recording an intended termination before a kill (durable intent first).
        """

        self.target_element = target_element
        self._operations = operations
        self._intend = intend
        self._registry = _HandleRegistry(PROCESS)
        self._active: dict[str, str] = {}

    def arm(self, run_id: str, entry: ResolvedEntry) -> BoundaryHandle | BoundaryOutcome:
        """Issue the exact handle for ``entry`` (process kinds only)."""

        if entry.boundary_class != PROCESS or entry.target_element != self.target_element:
            return BoundaryOutcome(False, "XVERSE-FAULT-TARGET", {"reason": "boundary mismatch"})
        # The unit may start after arming (lazy binding); liveness is checked at apply time.
        return self._registry.issue(run_id, entry)

    def apply(self, handle: BoundaryHandle, tick: int, parameters: Mapping[str, Any]) -> BoundaryOutcome:
        """Kill or freeze the owned process; the intent is recorded before a kill."""

        if not self._registry.check(handle):
            return BoundaryOutcome(False, HANDLE_DIAGNOSTIC)
        kind = str(parameters.get("_kind", ""))
        if kind not in ("crash", "freeze"):
            return BoundaryOutcome(False, "XVERSE-FAULT-KIND")
        if not self._operations.revalidate():
            return BoundaryOutcome(False, "XVERSE-FAULT-BOUNDARY-GONE", {"reason": "owned process not live"})
        if self._active:
            return BoundaryOutcome(False, "XVERSE-FAULT-BOUNDARY-BUSY", {"active": sorted(self._active)})
        operation = "kill" if kind == "crash" else "freeze"
        if operation == "kill" and self._intend is not None:
            self._intend(handle.entry_id, tick)
        outcome = self._operations.fault(operation)
        if outcome.ok:
            self._active[handle.entry_id] = kind
        return outcome

    def clear(self, handle: BoundaryHandle, tick: int) -> BoundaryOutcome:
        """Thaw a frozen process; a crash clears trivially (recovery is the plan's declaration)."""

        if not self._registry.check(handle) or handle.entry_id not in self._active:
            return BoundaryOutcome(False, HANDLE_DIAGNOSTIC)
        kind = self._active[handle.entry_id]
        outcome = self._operations.fault("thaw") if kind == "freeze" else BoundaryOutcome(True, detail={"crash": "cleared-by-definition"})
        if outcome.ok:
            del self._active[handle.entry_id]
        return outcome

    def revalidate(self, handle: BoundaryHandle) -> bool:
        """Return whether ``handle`` is ours and the owned process still revalidates."""

        return self._registry.check(handle) and self._operations.revalidate()

    def release(self, handle: BoundaryHandle) -> None:
        """Forget ``handle``."""

        self._active.pop(getattr(handle, "entry_id", None), None)
        self._registry.release(handle)
