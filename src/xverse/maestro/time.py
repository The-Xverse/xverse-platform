"""Pure clock validation for Maestro; no host clock or workload is sampled."""

from dataclasses import dataclass
import math


def _integer(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _finite(value: object, name: str) -> None:
    try:
        valid = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"{name} must be finite")


def _session(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("a nonempty clock session is required")


@dataclass(frozen=True)
class TickDomain:
    domain: str
    horizon_ticks: int

    def __post_init__(self) -> None:
        _session(self.domain)
        _integer(self.horizon_ticks, "horizon_ticks")


@dataclass(frozen=True)
class ClockContext:
    tick: TickDomain
    host_session: str
    utc_session: str

    def __post_init__(self) -> None:
        if not isinstance(self.tick, TickDomain):
            raise ValueError("tick must declare a TickDomain")
        _session(self.host_session)
        _session(self.utc_session)


@dataclass(frozen=True)
class HostDeadline:
    session: str
    monotonic_seconds: float

    def __post_init__(self) -> None:
        _session(self.session)
        _finite(self.monotonic_seconds, "host deadline")
        if self.monotonic_seconds < 0:
            raise ValueError("host deadline must be nonnegative")


def advance_tick(context: ClockContext, current_tick: int, proposal: int) -> int:
    """Allow zero and pauses; reject invalid current state as well as proposals."""
    current = _integer(current_tick, "current tick")
    proposed = _integer(proposal, "proposed tick")
    if current > context.tick.horizon_ticks or proposed > context.tick.horizon_ticks:
        raise ValueError("tick exceeds the declared horizon")
    if proposed < current:
        raise ValueError("tick rewind is forbidden")
    return proposed


def compare_host_deadline(left: HostDeadline, right: HostDeadline) -> int:
    if left.session != right.session:
        raise ValueError("host deadlines belong to different sessions")
    return (left.monotonic_seconds > right.monotonic_seconds) - (
        left.monotonic_seconds < right.monotonic_seconds
    )


def utc_elapsed(
    previous_utc: float,
    current_utc: float,
    *,
    previous_session: str,
    current_session: str,
) -> float:
    """Explicit UTC-only arithmetic; a clock jump never changes HostDeadline."""
    _session(previous_session)
    _session(current_session)
    if previous_session != current_session:
        raise ValueError("UTC observations belong to different sessions")
    _finite(previous_utc, "previous UTC")
    _finite(current_utc, "current UTC")
    delta = current_utc - previous_utc
    _finite(delta, "UTC interval")
    return delta
