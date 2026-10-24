"""Simulator-time fault triggers (ADR-ML3-SIMTIME-0001; thesis WP-10 option A).

A prepared lifecycle that declares a ``SimulationClock`` keeps every fault's onset and duration in exact
nanoseconds of simulator time, on the declared step grid, checked against the scenario horizon in simulator
time. Message and assurance entries act at a remote relay in the declared clock-source unit; ``freeze`` entries
act through the step-hold handshake, in which the clock-source unit holds the simulator step and Maestro decides
and applies the freeze or thaw through its owned process boundary. ``SimTimeFaultScheduler`` keeps the interface
of the tick-driven ``FaultScheduler`` and is polled by the dispatcher without blocking. Nothing here starts a
process or opens a socket: the channel socket is supplied by the trusted caller.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import json
import math
import os
import re
import socket
import struct
import time
from typing import Any

from .boundary import BoundaryHandle, BoundaryOutcome, InjectionBoundary
from .resolve import INF
from .scheduler import APPLIED, CANCELLED, CLEARED, FAILED_TO_APPLY, FINAL_OUTCOMES, INCOMPLETE_CLEARING, Decision
from .vocabulary import ARBITRATION, ASSURANCE, COLLECTION_BOUNDARY, MESSAGE, PROCESS, FaultError, FaultParameters, kind_spec, validate_parameters

PHYSICAL_UNITS = ("ns", "us", "ms", "s")
RELAY, HOLD = "relay", "hold"
RELAY_KINDS = ("delay", "loss", "stale", "assurance.proposal-unsafe", "assurance.proposal-mistimed", "assurance.evidence-loss")
HOLD_KINDS = ("freeze",)
MAX_STEP_NS = 10_000_000_000
MAX_HORIZON_NS = 3_600_000_000_000
MAX_HOST_SECONDS = 5.0
FRAME_MAX = 4096
POLL_FRAMES = 64
PROTOCOL = "XVERSE-FAULT-SIMTIME-PROTOCOL"
_IDENT = re.compile(r"[A-Za-z0-9_.:#/-]{1,256}")
_REASON = re.compile(r"[a-z0-9-]{1,64}")


# --------------------------------------------------------------------------------------------------------------
# Binding and resolution
# --------------------------------------------------------------------------------------------------------------


def _optional_seconds(value: Any) -> bool:
    return value is None or (type(value) in (int, float) and math.isfinite(value) and 0 < value <= MAX_HOST_SECONDS)


@dataclass(frozen=True)
class SimulationClock:
    """The declared simulator clock of one Maestro run (ADR-ML3-SIMTIME-0001 decision 1).

    ``max_step_host_s``, ``handshake_s`` and ``hold_bound_s`` are D-4c measurements; ``None`` means unmeasured,
    and admission then refuses any held (``freeze``) entry.
    """

    domain: str
    source_unit: str
    step_ns: int
    horizon_ns: int
    max_step_host_s: float | None = None
    handshake_s: float | None = None
    hold_bound_s: float | None = None

    def __post_init__(self) -> None:
        if (type(self.domain) is not str or not _IDENT.fullmatch(self.domain)
                or type(self.source_unit) is not str or not _IDENT.fullmatch(self.source_unit)):
            raise ValueError("simulation clock needs a domain and a source unit identifier")
        if type(self.step_ns) is not int or not 1 <= self.step_ns <= MAX_STEP_NS:
            raise ValueError("simulation clock step_ns must be an integer in 1..1e10")
        if type(self.horizon_ns) is not int or not self.step_ns <= self.horizon_ns <= MAX_HORIZON_NS:
            raise ValueError("simulation clock horizon_ns must be an integer in step_ns..3.6e12")
        for name in ("max_step_host_s", "handshake_s", "hold_bound_s"):
            if not _optional_seconds(getattr(self, name)):
                raise ValueError(f"simulation clock {name} must be None or finite in (0, 5]")

    @property
    def measured(self) -> bool:
        """Return whether every D-4c value of the handshake is known."""

        return None not in (self.max_step_host_s, self.handshake_s, self.hold_bound_s)


@dataclass(frozen=True)
class SimEntry:
    """One simulator-timed entry with its grid decisions fixed before any run."""

    entry_id: str
    fault_id: str
    fault_kind: str
    boundary_class: str
    mode: str
    target_uri: str
    target_collection: str
    target_element: str
    at_ns: int
    duration_ns: int
    onset_step: int
    clear_step: int
    parameters: FaultParameters
    recovery: str
    activation: str
    executable: bool = True
    trigger_kind: str = "time"
    declared_order: int | None = None

    @property
    def tie_key(self) -> tuple[float, str]:
        return (INF, self.fault_id)

    @property
    def held_steps(self) -> int:
        return self.clear_step - self.onset_step


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    return value if isinstance(value, Sequence) and not isinstance(value, str) else ()


def _ceil_div(value: int, step: int) -> int:
    return -(-value // step)


def resolve_simtime(plan: Mapping[str, Any], clock: SimulationClock) -> tuple[SimEntry, ...]:
    """Resolve every entry of ``plan["faultSchedule"]`` in simulator time; fail closed on any rule.

    @param plan Compiled Phase 1 experiment plan (mapping form).
    @param clock The declared simulation clock.
    @return Entries in compiled listing order.
    @raises FaultError With a stable ``XVERSE-FAULT-*`` code on the first violation.
    """

    if type(clock) is not SimulationClock:
        raise FaultError("XVERSE-FAULT-SIMTIME-CLOCK", "a SimulationClock binding is required")
    system_uri = str(_mapping(_mapping(plan.get("selection")).get("system")).get("uri", ""))
    if not system_uri:
        raise FaultError("XVERSE-FAULT-PLAN", "plan selection names no system")
    entries: list[SimEntry] = []
    for item in _sequence(plan.get("faultSchedule")):
        entry = _mapping(item)
        fault_id = str(entry.get("faultId", ""))
        spec = kind_spec(entry.get("faultKind"))
        target = _mapping(entry.get("targetRef"))
        collection, element = entry.get("collection"), target.get("element")
        if str(target.get("uri", "")) != system_uri or not isinstance(element, str) or collection not in COLLECTION_BOUNDARY:
            raise FaultError("XVERSE-FAULT-TARGET", f"fault {fault_id!r} targets no System element with a declared boundary")
        if spec.kind in RELAY_KINDS and collection == "flows":
            mode = RELAY
        elif spec.kind in HOLD_KINDS and collection == "componentInstances":
            mode = HOLD
        else:
            raise FaultError("XVERSE-FAULT-SIMTIME-KIND", f"fault {fault_id!r} kind {spec.kind!r} on {collection} is not admitted in simulator time")
        if mode == HOLD and element == clock.source_unit:
            raise FaultError("XVERSE-FAULT-SIMTIME-SOURCE", f"fault {fault_id!r} would freeze the clock-source unit")
        trigger = _mapping(entry.get("trigger"))
        duration = _mapping(entry.get("duration"))
        at, unit = trigger.get("atTicks"), trigger.get("declaredUnit")
        span, span_unit = duration.get("ticks"), duration.get("unit")
        if (trigger.get("kind") != "time" or unit not in PHYSICAL_UNITS or span_unit not in PHYSICAL_UNITS
                or entry.get("timeDomainId") != clock.domain):
            raise FaultError("XVERSE-FAULT-SIMTIME-TRIGGER", f"fault {fault_id!r} needs a time trigger and duration in ns/us/ms/s of domain {clock.domain!r}")
        if type(at) is not int or at < 0 or type(span) is not int or span < 0:
            raise FaultError("XVERSE-FAULT-DURATION", f"fault {fault_id!r} has no exact compiled ns onset and duration")
        parameters = validate_parameters(spec, _sequence(entry.get("parameters")), fault_id)
        if parameters.arbitration is not None or ARBITRATION in parameters.values:
            raise FaultError("XVERSE-FAULT-PARAMETER", f"fault {fault_id!r}: arbitration is not admitted in simulator time")
        if "delay-ticks" in parameters.values:
            raise FaultError("XVERSE-FAULT-PARAMETER", f"fault {fault_id!r}: simulator-time delay takes 'delay-ns', not 'delay-ticks'")
        onset = _ceil_div(at, clock.step_ns)
        clear = onset + _ceil_div(span, clock.step_ns)
        if clear * clock.step_ns > clock.horizon_ns:
            raise FaultError("XVERSE-FAULT-HORIZON", f"fault {fault_id!r} clears beyond the simulator horizon")
        entries.append(SimEntry(
            entry_id=str(entry.get("entryId", f"fault:{fault_id}")), fault_id=fault_id, fault_kind=spec.kind,
            boundary_class=ASSURANCE if spec.boundary_class == ASSURANCE else (MESSAGE if mode == RELAY else PROCESS),
            mode=mode, target_uri=system_uri, target_collection=str(collection), target_element=element,
            at_ns=at, duration_ns=span, onset_step=onset, clear_step=clear, parameters=parameters,
            recovery=str(entry.get("recovery", "")), activation=str(entry.get("activation", ""))))
    seen: set[str] = set()
    for entry in entries:
        if entry.fault_id in seen:
            raise FaultError("XVERSE-FAULT-PLAN", f"fault id {entry.fault_id!r} is repeated")
        seen.add(entry.fault_id)
    by_target: dict[tuple[str, str], list[SimEntry]] = {}
    for entry in entries:
        by_target.setdefault((entry.target_collection, entry.target_element), []).append(entry)
    for group in by_target.values():
        group.sort(key=lambda e: (e.onset_step, e.fault_id))
        for first, second in zip(group, group[1:]):
            if second.onset_step <= first.clear_step:
                raise FaultError("XVERSE-FAULT-OVERLAP", f"faults {first.fault_id!r} and {second.fault_id!r} overlap on one target in simulator time")
    return tuple(entries)


def thaw_check(entries: Sequence[SimEntry], clock: SimulationClock, thaw_bound_s: float) -> str | None:
    """Return the refusal code for the held entries, or ``None`` when every one fits (decision 3)."""

    held = [e for e in entries if e.mode == HOLD]
    if not held:
        return None
    if not clock.measured:
        return "ML-SCHEDULE-FAULT-SIMTIME-UNMEASURED"
    if clock.handshake_s > clock.hold_bound_s:
        return "ML-SCHEDULE-FAULT-SIMTIME-HOLD"
    if not (math.isfinite(thaw_bound_s) and thaw_bound_s > 0):
        return "ML-SCHEDULE-FAULT-SIMTIME-THAW"
    for entry in held:
        if entry.held_steps * clock.max_step_host_s + 2 * clock.handshake_s > thaw_bound_s:
            return "ML-SCHEDULE-FAULT-SIMTIME-THAW"
    return None


# --------------------------------------------------------------------------------------------------------------
# Channel and frames
# --------------------------------------------------------------------------------------------------------------

_COMMON = {"v", "kind", "seq"}
HUB_FRAMES = {
    "armed": {"entry"},
    "time": {"step", "simNs"},
    "hold": {"entry", "phase", "step", "simNs"},
    "applied": {"entry", "step", "simNs", "items"},
    "cleared": {"entry", "step", "simNs", "items"},
    "failed": {"entry", "phase", "step", "simNs", "reason"},
}
MAESTRO_FRAMES = {
    "arm": {"entry", "fault", "faultKind", "mode", "collection", "element", "atNs", "durationNs", "onsetStep",
            "clearStep", "parameters", "seed", "stepNs"},
    "ack": {"entry", "phase", "step", "outcome"},
    "close": {"reason"},
}


def encode_frame(body: Mapping[str, Any]) -> bytes:
    """Return the canonical bytes of one frame; refuse a frame outside the size bound."""

    data = json.dumps(dict(body), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    if len(data) > FRAME_MAX:
        raise FaultError(PROTOCOL, "frame exceeds 4096 bytes")
    return data


def _int(value: Any, low: int = 0) -> bool:
    return type(value) is int and low <= value <= 2**62


def _refuse_constant(name: str) -> Any:
    raise ValueError(f"non-finite JSON constant {name}")


def decode_hub_frame(data: bytes) -> dict[str, Any]:
    """Decode and check one hub frame against the closed contract (shape only; state is checked by the scheduler)."""

    if type(data) is not bytes or not 0 < len(data) <= FRAME_MAX:
        raise FaultError(PROTOCOL, "frame size")
    try:
        body = json.loads(data.decode("utf-8"), parse_constant=_refuse_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise FaultError(PROTOCOL, "frame is not JSON") from error
    if type(body) is not dict or encode_frame(body) != data:
        raise FaultError(PROTOCOL, "frame is not canonical JSON")
    kind = body.get("kind")
    if kind not in HUB_FRAMES or set(body) != _COMMON | HUB_FRAMES[kind] or body["v"] != 1 or not _int(body["seq"], 1):
        raise FaultError(PROTOCOL, "frame outside the contract")
    if "entry" in body and (type(body["entry"]) is not str or not _IDENT.fullmatch(body["entry"])):
        raise FaultError(PROTOCOL, "frame entry")
    if "phase" in body and body["phase"] not in ("apply", "clear"):
        raise FaultError(PROTOCOL, "frame phase")
    for name in ("step", "simNs", "items"):
        if name in body and not _int(body[name]):
            raise FaultError(PROTOCOL, f"frame {name}")
    if kind == "failed" and (type(body["reason"]) is not str or not _REASON.fullmatch(body["reason"])):
        raise FaultError(PROTOCOL, "frame reason")
    return body


class HubChannel:
    """The owned control channel to the clock-source unit, over a socket supplied by the trusted caller.

    The socket is AF_UNIX ``SOCK_SEQPACKET``, connected or listening. A listening socket accepts exactly one peer
    whose ``SO_PEERCRED`` uid equals this process's uid. Every operation is non-blocking.
    """

    def __init__(self, sock: socket.socket) -> None:
        if (type(sock) is not socket.socket or sock.family != socket.AF_UNIX
                or sock.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) != socket.SOCK_SEQPACKET):
            raise FaultError("XVERSE-FAULT-SIMTIME-CHANNEL", "the hub channel must be an AF_UNIX SOCK_SEQPACKET socket")
        sock.setblocking(False)
        listening = bool(sock.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN))
        self._listener = sock if listening else None
        self._peer: socket.socket | None = None if listening else sock
        self._accepted = not listening
        self.peer_credentials: tuple[int, int, int] | None = None
        self._send_seq = 0
        self._recv_seq = 0
        self.closed = False
        if self._peer is not None:
            self._check_peer(self._peer)

    def _check_peer(self, peer: socket.socket) -> None:
        raw = peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
        pid, uid, gid = struct.unpack("3i", raw)
        if uid != os.getuid():
            raise FaultError("XVERSE-FAULT-SIMTIME-CHANNEL", "the hub peer runs under another uid")
        self.peer_credentials = (pid, uid, gid)

    @property
    def connected(self) -> bool:
        """Accept the single peer of a listening channel if one is waiting; return whether a peer is present."""

        if self._peer is None and self._listener is not None and not self.closed:
            try:
                peer, _ = self._listener.accept()
            except (BlockingIOError, InterruptedError):
                return False
            peer.setblocking(False)
            try:
                self._check_peer(peer)
            except FaultError:
                peer.close()
                raise
            self._peer, self._accepted = peer, True
        if self._listener is not None and self._peer is not None:
            try:
                extra, _ = self._listener.accept()
            except (BlockingIOError, InterruptedError):
                pass
            else:
                extra.close()
                raise FaultError("XVERSE-FAULT-SIMTIME-CHANNEL", "a second hub peer connected")
        return self._peer is not None

    def send(self, kind: str, **fields: Any) -> int:
        """Send one Maestro frame; return its sequence number."""

        if self.closed or self._peer is None:
            raise FaultError("XVERSE-FAULT-SIMTIME-CHANNEL", "the hub channel is not connected")
        if kind not in MAESTRO_FRAMES or set(fields) != MAESTRO_FRAMES[kind]:
            raise FaultError(PROTOCOL, f"Maestro frame {kind!r} outside the contract")
        self._send_seq += 1
        data = encode_frame({"v": 1, "kind": kind, "seq": self._send_seq, **fields})
        try:
            if self._peer.send(data) != len(data):
                raise FaultError("XVERSE-FAULT-SIMTIME-CHANNEL", "short send")
        except (BlockingIOError, InterruptedError, OSError) as error:
            raise FaultError("XVERSE-FAULT-SIMTIME-CHANNEL", "the hub channel refused a frame") from error
        return self._send_seq

    def receive(self, limit: int = POLL_FRAMES) -> list[dict[str, Any]]:
        """Return up to ``limit`` waiting hub frames, decoded and sequence-checked; never block."""

        frames: list[dict[str, Any]] = []
        if self.closed or self._peer is None:
            return frames
        while len(frames) < limit:
            try:
                data = self._peer.recv(FRAME_MAX + 1)
            except (BlockingIOError, InterruptedError):
                break
            except OSError as error:
                raise FaultError("XVERSE-FAULT-SIMTIME-CHANNEL", "the hub channel failed") from error
            if not data:
                raise FaultError("XVERSE-FAULT-SIMTIME-CHANNEL", "the hub closed the channel")
            frame = decode_hub_frame(data)
            if frame["seq"] != self._recv_seq + 1:
                raise FaultError(PROTOCOL, "hub sequence gap")
            self._recv_seq = frame["seq"]
            frames.append(frame)
        return frames

    def close(self, reason: str = "run-ended") -> None:
        """Send ``close`` (best effort) and release the sockets."""

        if self.closed:
            return
        try:
            if self._peer is not None:
                self.send("close", reason=reason)
        except FaultError:
            pass
        self.closed = True
        for sock in (self._peer, self._listener):
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass


# --------------------------------------------------------------------------------------------------------------
# Scheduler
# --------------------------------------------------------------------------------------------------------------


@dataclass
class _State:
    entry: SimEntry
    handle: BoundaryHandle | None = None
    final: str | None = None
    armed: bool = False
    applied: bool = False
    cleared: bool = False


class SimTimeFaultScheduler:
    """Apply and clear simulator-timed entries from the clock-source unit's reports (decisions 4–7).

    The interface matches ``FaultScheduler``: ``start``, ``advance(tick)``, ``cancel``, ``finish``,
    ``outcomes``, ``decisions``, ``run_failed``, ``incomplete`` and ``failure_diagnostic``.
    """

    def __init__(
        self,
        run_id: str,
        entries: Sequence[SimEntry],
        clock: SimulationClock,
        channel: HubChannel,
        process_boundaries: Mapping[tuple[str, str], InjectionBoundary],
        *,
        source_live: Callable[[], bool],
        seed: int = 0,
        listener: Any = None,
        host_ns: Callable[[], int] = time.monotonic_ns,
    ) -> None:
        if type(clock) is not SimulationClock or type(channel) is not HubChannel:
            raise FaultError("XVERSE-FAULT-SIMTIME-CLOCK", "a SimulationClock and a HubChannel are required")
        self.run_id = run_id
        self.seed = int(seed)
        self.clock = clock
        self.channel = channel
        self._boundaries = dict(process_boundaries)
        self._states = {e.entry_id: _State(e) for e in entries}
        self._source_live = source_live
        self._listener = listener
        self._host_ns = host_ns
        self.decisions: list[Decision] = []
        self.incomplete = False
        self.run_failed = False
        self.failure_diagnostic: str | None = None
        self.blocked_targets: set[tuple[str, str]] = set()
        self._started = False
        self._arm_sent = False
        self._step = -1
        self._tick = 0

    # -- helpers ---------------------------------------------------------------------------------------------

    def _ordered(self) -> list[_State]:
        return sorted(self._states.values(), key=lambda s: s.entry.tie_key)

    def _record(self, state: _State, phase: str, outcome: str, diagnostic: str | None = None, **detail: Any) -> Decision:
        detail.setdefault("hostNs", self._host_ns())
        decision = Decision(self._tick, state.entry.entry_id, phase, outcome, diagnostic, dict(detail))
        self.decisions.append(decision)
        if self._listener is not None:
            self._listener.decision(state.entry, decision)
        return decision

    def _finalize(self, state: _State, outcome: str, diagnostic: str | None = None, **detail: Any) -> None:
        if state.final is None:
            state.final = outcome
            self._record(state, "final", outcome, diagnostic, **detail)

    def _fail(self, state: _State | None, diagnostic: str) -> None:
        if state is None or state.entry.parameters.on_apply_failure != "continue":
            if not self.run_failed:
                self.run_failed = True
                self.failure_diagnostic = diagnostic

    def _protocol(self, reason: str) -> None:
        if not self.run_failed:
            self.run_failed = True
            self.failure_diagnostic = f"{PROTOCOL}: {reason}"

    def _clock(self, frame: Mapping[str, Any]) -> dict[str, int]:
        return {"simulatorNs": frame["simNs"], "simulatorStep": frame["step"]}

    # -- lifecycle -------------------------------------------------------------------------------------------

    def start(self) -> None:
        """Issue the exact process handles; the hub is armed later, once the clock-source unit is live."""

        if self._started:
            raise FaultError("XVERSE-FAULT-SCHEDULER", "scheduler already started")
        self._started = True
        for state in self._ordered():
            entry = state.entry
            if entry.mode != HOLD:
                continue
            boundary = self._boundaries.get((entry.target_collection, entry.target_element))
            issued = boundary.arm(self.run_id, entry) if boundary is not None else BoundaryOutcome(False, "XVERSE-FAULT-TARGET")
            if isinstance(issued, BoundaryOutcome):
                self._finalize(state, FAILED_TO_APPLY, issued.diagnostic)
                self._fail(state, f"fault {entry.fault_id} failed to arm")
                continue
            state.handle = issued

    def _arm(self) -> None:
        for state in self._ordered():
            if state.final is not None:
                continue
            e = state.entry
            self.channel.send("arm", entry=e.entry_id, fault=e.fault_id, faultKind=e.fault_kind, mode=e.mode,
                              collection=e.target_collection, element=e.target_element, atNs=e.at_ns,
                              durationNs=e.duration_ns, onsetStep=e.onset_step, clearStep=e.clear_step,
                              parameters=dict(e.parameters.values), seed=self.seed, stepNs=self.clock.step_ns)
        self._arm_sent = True

    def _pending_point(self, state: _State) -> int | None:
        """Return the next step at which the hub must report for ``state``, or ``None``."""

        if state.final is not None or not state.armed:
            return None
        if not state.applied:
            return state.entry.onset_step
        if not state.cleared:
            return state.entry.clear_step
        return None

    def _handle(self, frame: dict[str, Any]) -> None:
        kind = frame["kind"]
        if "step" in frame:
            if frame["simNs"] != frame["step"] * self.clock.step_ns or frame["step"] < self._step:
                return self._protocol("hub clock is off the step grid or went back")
            self._step = frame["step"]
        state = self._states.get(frame.get("entry")) if "entry" in frame else None
        if "entry" in frame and state is None:
            return self._protocol("unknown entry")
        if kind == "armed":
            if not self._arm_sent or state.armed or state.final is not None:
                return self._protocol("armed out of order")
            state.armed = True
            return None
        if not all(s.armed or s.final is not None for s in self._states.values()):
            return self._protocol("hub report before every entry was armed")
        # every other report: the hub may not pass a pending point of another entry
        for other in self._states.values():
            point = self._pending_point(other)
            if point is not None and self._step > point and other is not state:
                return self._protocol(f"hub passed step {point} of {other.entry.entry_id}")
        if kind == "time":
            return None
        expected = self._pending_point(state)
        phase = frame.get("phase") or ("apply" if kind == "applied" else "clear")
        if expected is None or frame["step"] != expected or (phase == "apply") == state.applied:
            return self._protocol(f"{kind} for {state.entry.entry_id} at step {frame['step']} is out of order")
        entry = state.entry
        if kind == "hold":
            if entry.mode != HOLD:
                return self._protocol("hold for a relay entry")
            boundary = self._boundaries[(entry.target_collection, entry.target_element)]
            if phase == "apply":
                outcome = boundary.apply(state.handle, self._tick, dict(entry.parameters.values, _kind=entry.fault_kind))
                if outcome.ok:
                    state.applied = True
                    self._record(state, "apply", APPLIED, **self._clock(frame), mode="step-hold")
                    self.channel.send("ack", entry=entry.entry_id, phase="apply", step=frame["step"], outcome="applied")
                else:
                    self._record(state, "apply", "apply-failed", outcome.diagnostic, **self._clock(frame))
                    self.channel.send("ack", entry=entry.entry_id, phase="apply", step=frame["step"], outcome="refused")
                    self._finalize(state, FAILED_TO_APPLY, outcome.diagnostic)
                    self._fail(state, f"fault {entry.fault_id} failed to apply")
            else:
                outcome = boundary.clear(state.handle, self._tick)
                if outcome.ok:
                    state.cleared = True
                    self._record(state, "clear", CLEARED, **self._clock(frame), mode="step-hold")
                    self.channel.send("ack", entry=entry.entry_id, phase="clear", step=frame["step"], outcome="cleared")
                    self._finalize(state, CLEARED)
                else:
                    self._record(state, "clear", "clear-failed", outcome.diagnostic, **self._clock(frame))
                    self.channel.send("ack", entry=entry.entry_id, phase="clear", step=frame["step"], outcome="refused")
                    self.blocked_targets.add((entry.target_collection, entry.target_element))
                    self.incomplete = True
                    self._finalize(state, INCOMPLETE_CLEARING, outcome.diagnostic)
            return None
        if entry.mode != RELAY:
            return self._protocol(f"{kind} report for a held entry")
        if kind == "applied":
            state.applied = True
            self._record(state, "apply", APPLIED, **self._clock(frame), mode="remote-relay", items=frame["items"])
        elif kind == "cleared":
            state.cleared = True
            self._record(state, "clear", CLEARED, **self._clock(frame), mode="remote-relay", items=frame["items"])
            self._finalize(state, CLEARED)
        else:  # failed
            if phase == "apply":
                self._record(state, "apply", "apply-failed", "XVERSE-FAULT-BOUNDARY-REFUSED", **self._clock(frame), reason=frame["reason"])
                self._finalize(state, FAILED_TO_APPLY, "XVERSE-FAULT-BOUNDARY-REFUSED")
                self._fail(state, f"fault {entry.fault_id} failed to apply")
            else:
                self._record(state, "clear", "clear-failed", "XVERSE-FAULT-BOUNDARY-REFUSED", **self._clock(frame), reason=frame["reason"])
                self.incomplete = True
                self._finalize(state, INCOMPLETE_CLEARING, "XVERSE-FAULT-BOUNDARY-REFUSED")
        return None

    def advance(self, tick: int) -> list[Decision]:
        """Read every waiting hub frame and act on it; return the decisions taken now. Never blocks."""

        if not self._started:
            raise FaultError("XVERSE-FAULT-SCHEDULER", "advance before start")
        self._tick = int(tick)
        before = len(self.decisions)
        if self.run_failed or self.channel.closed:
            return self.decisions[before:]
        try:
            if not self._arm_sent:
                if not self._source_live() or not self.channel.connected:
                    return self.decisions[before:]
                self._arm()
            for frame in self.channel.receive():
                self._handle(frame)
                if self.run_failed:
                    break
        except FaultError as error:
            self._protocol(error.code if error.code != PROTOCOL else str(error))
        if self.run_failed:
            self.channel.close("run-failed")
        return self.decisions[before:]

    def _end(self, reason: str, *, never: str) -> None:
        for state in self._ordered():
            entry = state.entry
            if state.final is not None:
                continue
            if state.applied and not state.cleared:
                if entry.mode == HOLD:
                    outcome = self._boundaries[(entry.target_collection, entry.target_element)].clear(state.handle, self._tick)
                    if outcome.ok:
                        state.cleared = True
                        self._record(state, "clear", CLEARED, reason=reason)
                        diagnostic = "XVERSE-FAULT-SIMTIME-NOT-REACHED" if never == "XVERSE-FAULT-NEVER-DUE" else never
                        self._finalize(state, CANCELLED, diagnostic, reason=reason)
                    else:
                        self._record(state, "clear", "clear-failed", outcome.diagnostic, reason=reason)
                        self.incomplete = True
                        self._finalize(state, INCOMPLETE_CLEARING, outcome.diagnostic)
                else:
                    self.incomplete = True
                    self._finalize(state, INCOMPLETE_CLEARING, "XVERSE-FAULT-SIMTIME-NOT-CLEARED", reason=reason)
            else:
                self._finalize(state, CANCELLED, never, reason=reason)
        for state in self._states.values():
            boundary = self._boundaries.get((state.entry.target_collection, state.entry.target_element))
            if boundary is not None and state.handle is not None:
                boundary.release(state.handle)
        self.channel.close(reason)

    def cancel(self, tick: int, reason: str = "cancelled", *, ended_by: str | None = None) -> list[Decision]:
        """Thaw active freezes, finalize every entry as cancelled, and close the channel."""

        self._tick = int(tick)
        before = len(self.decisions)
        self._end(reason, never="XVERSE-FAULT-CANCELLED")  # no crash is admitted in simulator time
        return self.decisions[before:]

    def finish(self, tick: int) -> dict[str, str]:
        """Finalize every entry at the end of the run; return the final outcome per entry id."""

        self._tick = int(tick)
        if not self.run_failed and not self.channel.closed and self._arm_sent:
            try:
                for frame in self.channel.receive():
                    self._handle(frame)
            except FaultError as error:
                self._protocol(error.code)
        self._end("run-finished", never="XVERSE-FAULT-NEVER-DUE")
        if any(state.final not in FINAL_OUTCOMES for state in self._states.values()):
            self.incomplete = True
        return {entry_id: state.final or CANCELLED for entry_id, state in self._states.items()}

    @property
    def outcomes(self) -> dict[str, str | None]:
        return {entry_id: state.final for entry_id, state in self._states.items()}


__all__ = [
    "HOLD", "RELAY", "HubChannel", "SimEntry", "SimTimeFaultScheduler", "SimulationClock", "decode_hub_frame",
    "encode_frame", "resolve_simtime", "thaw_check",
]
