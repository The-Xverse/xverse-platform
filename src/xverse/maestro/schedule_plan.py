"""Pure finite dispatcher admission; no tick, process or I/O is executed here."""

from dataclasses import asdict, dataclass
import hashlib
import json
import math

from .projection import PreparedLifecycle
from .providers import ProbePolicy
from .lifecycle_evidence import _parents

MAX_REQUESTS = 8192
MAX_EVENTS = 8192


class ScheduleError(ValueError):
    pass


def _seconds(value, maximum, name):
    try:
        valid = (
            type(value) in (int, float)
            and math.isfinite(value)
            and 0 < value <= maximum
        )
    except OverflowError:
        valid = False
    if not valid:
        raise ScheduleError("ML-SCHEDULE-" + name)


def _integer(value, maximum, name, minimum=1):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ScheduleError("ML-SCHEDULE-" + name)


def _canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


@dataclass(frozen=True)
class ScheduleAdmission:
    lifecycle_digest: str
    policies: tuple[ProbePolicy, ...]
    ticks: tuple[int, ...]
    active_seconds: float
    operation_seconds: float
    poll_seconds: float
    per_unit_seconds: float
    request_limit: int
    event_limit: int
    terminal_reserve_seconds: float
    health_horizon_seconds: float
    health_scan_seconds: float
    health_slots: int
    required_requests: int
    required_events: int
    canonical_bytes: bytes
    digest: str

    @property
    def ready_for_execution(self):
        return False


def admit_schedule(
    prepared,
    *,
    policies,
    ticks,
    active_seconds,
    operation_seconds,
    poll_seconds=0.01,
    per_unit_seconds=1,
    request_limit=128,
    event_limit=MAX_EVENTS,
):
    if (
        type(prepared) is not PreparedLifecycle
        or type(policies) is not tuple
        or type(ticks) is not tuple
    ):
        raise ScheduleError("ML-SCHEDULE-INPUT")
    _seconds(active_seconds, 300, "ACTIVE")
    _seconds(operation_seconds, 5, "OPERATION")
    _seconds(poll_seconds, 0.05, "POLL")
    _seconds(per_unit_seconds, 5, "TEARDOWN")
    _integer(request_limit, MAX_REQUESTS, "REQUEST-LIMIT", 128)
    _integer(event_limit, MAX_EVENTS, "EVENT-LIMIT")
    units = tuple(u.unit_id for u in prepared.units)
    if (
        not units
        or len(units) > 16
        or len(policies) != len(units)
        or any(type(p) is not ProbePolicy for p in policies)
    ):
        raise ScheduleError("ML-SCHEDULE-POLICIES")
    for policy in policies:
        policy.__post_init__()
    by_unit = {p.unit_id: p for p in policies}
    if set(by_unit) != set(units) or len(by_unit) != len(policies):
        raise ScheduleError("ML-SCHEDULE-POLICIES")
    policies = tuple(by_unit[u] for u in units)
    if not 1 <= len(ticks) <= MAX_EVENTS:
        raise ScheduleError("ML-SCHEDULE-TICK-LIMIT")
    prior = 0
    for tick in ticks:
        _integer(tick, prepared.clock.horizon_ticks, "TICK", 0)
        if tick < prior:
            raise ScheduleError("ML-SCHEDULE-TICK-REWIND")
        prior = tick
    if ticks[0] != 0 or ticks[-1] != prepared.clock.horizon_ticks:
        raise ScheduleError("ML-SCHEDULE-TICK-HORIZON")
    if any(
        s.phase not in ("prepare", "start", "observe", "stop", "cleanup")
        for s in prepared.steps
    ):
        raise ScheduleError("ML-SCHEDULE-PHASE")
    n = len(units)
    scan = n * operation_seconds
    cadence = min(p.cadence_seconds for p in policies)
    period = cadence - scan - (n + 2) * operation_seconds
    if period <= scan or poll_seconds > period:
        raise ScheduleError("ML-SCHEDULE-HEALTH-CAPACITY")
    # Early scans shorten actual spacing. Count that conservative spacing, not
    # just ceil(active/cadence); pauses never shrink the host obligation universe.
    reserve = (
        n * per_unit_seconds + (len(prepared.steps) + 2 * n + 2) * operation_seconds + 2
    )
    horizon = active_seconds + reserve
    if horizon > 394:
        raise ScheduleError("ML-SCHEDULE-GENERATION-CAPACITY")
    slot_bound = horizon / period
    if not math.isfinite(slot_bound) or slot_bound > MAX_REQUESTS:
        raise ScheduleError("ML-SCHEDULE-EVIDENCE-CAPACITY")
    slots = math.ceil(slot_bound) + 2
    own = sum(p.attempts for p in policies)
    parents = sum(len(_parents(prepared, u)) for u in units)
    prior_health = n * (n - 1) // 2
    explicit = n * sum(s.phase == "observe" for s in prepared.steps)
    samples = own + 2 * parents + prior_health + n * slots + explicit
    # Init + claims + staging and two Release revalidations + probe records;
    # four teardown records; two calls (three annotations) per successful step;
    # tick pull/completion; per-unit diagnostic/disposition; begin/terminal/abort.
    requests = (
        1
        + 4 * n
        + samples
        + 4 * n
        + 2 * len(prepared.steps)
        + 2 * len(ticks)
        + 2 * n
        + 3
    )
    events = n + 3 * samples + 4 * n + 3 * len(prepared.steps) + len(ticks) + 2 * n + 4
    if requests > request_limit or events > event_limit:
        raise ScheduleError("ML-SCHEDULE-EVIDENCE-CAPACITY")
    body = dict(
        version=1,
        lifecycle_digest=prepared.lifecycle_digest,
        policies=[asdict(p) for p in policies],
        ticks=list(ticks),
        active_seconds=active_seconds,
        operation_seconds=operation_seconds,
        poll_seconds=poll_seconds,
        per_unit_seconds=per_unit_seconds,
        request_limit=request_limit,
        event_limit=event_limit,
        terminal_reserve_seconds=reserve,
        health_horizon_seconds=horizon,
        health_scan_seconds=scan,
        health_slots=slots,
        required_requests=requests,
        required_events=events,
    )
    encoded = _canonical(body)
    return ScheduleAdmission(
        prepared.lifecycle_digest,
        policies,
        ticks,
        active_seconds,
        operation_seconds,
        poll_seconds,
        per_unit_seconds,
        request_limit,
        event_limit,
        reserve,
        horizon,
        scan,
        slots,
        requests,
        events,
        encoded,
        hashlib.sha256(b"maestro.schedule14\0" + encoded).hexdigest(),
    )


def decode_schedule(prepared, body):
    """Recompute every derived value; serialized budgets never authorize themselves."""
    if type(body) is not dict:
        raise ScheduleError("ML-SCHEDULE-SERIALIZATION")
    try:
        policies = tuple(ProbePolicy(**p) for p in body["policies"])
        schedule = admit_schedule(
            prepared,
            policies=policies,
            ticks=tuple(body["ticks"]),
            **{
                k: body[k]
                for k in (
                    "active_seconds",
                    "operation_seconds",
                    "poll_seconds",
                    "per_unit_seconds",
                    "request_limit",
                    "event_limit",
                )
            },
        )
        if _canonical(body) != schedule.canonical_bytes:
            raise ScheduleError("ML-SCHEDULE-SERIALIZATION")
        return schedule
    except (KeyError, TypeError, OverflowError) as error:
        raise ScheduleError("ML-SCHEDULE-SERIALIZATION") from error
