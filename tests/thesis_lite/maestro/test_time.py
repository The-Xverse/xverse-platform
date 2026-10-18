"""Integer ticks and session/domain separation; no host watchdog claimed."""

import math

import pytest

from xverse.maestro.time import (
    ClockContext,
    HostDeadline,
    TickDomain,
    advance_tick,
    compare_host_deadline,
    utc_elapsed,
)

CONTEXT = ClockContext(TickDomain("simulation", 10), "host-1", "utc-1")


@pytest.mark.parametrize(
    "current,proposed,expected", [(0, 0, 0), (0, 1, 1), (4, 4, 4), (4, 10, 10)]
)
def test_valid_zero_pause_progression_and_horizon(current, proposed, expected):
    assert advance_tick(CONTEXT, current, proposed) == expected


@pytest.mark.parametrize(
    "current,proposed",
    [
        (0, True),
        (False, 0),
        (0, 1.0),
        (1.0, 2),
        (0, math.nan),
        (0, math.inf),
        (0, -1),
        (4, 3),
        (0, 11),
        (11, 11),
        (12, 10),
        (0, "1"),
    ],
)
def test_invalid_tick_values_reject_without_mutating_context(current, proposed):
    with pytest.raises(ValueError):
        advance_tick(CONTEXT, current, proposed)
    assert CONTEXT.tick.horizon_ticks == 10


@pytest.mark.parametrize("horizon", [True, -1, 1.0, math.inf])
def test_tick_domain_rejects_invalid_horizon(horizon):
    with pytest.raises(ValueError):
        TickDomain("simulation", horizon)


def test_host_deadlines_are_session_qualified():
    deadline = HostDeadline("host-1", 10)
    assert compare_host_deadline(deadline, HostDeadline("host-1", 9)) == 1
    with pytest.raises(ValueError):
        compare_host_deadline(deadline, HostDeadline("host-2", 10))
    with pytest.raises(ValueError):
        HostDeadline("", 10)
    with pytest.raises(ValueError):
        HostDeadline("host-1", True)


def test_utc_jump_and_simulation_pause_never_move_host_deadline():
    deadline = HostDeadline("host-1", 10)
    before = deadline.monotonic_seconds
    assert (
        utc_elapsed(100, 90, previous_session="utc-1", current_session="utc-1") == -10
    )
    assert advance_tick(CONTEXT, 4, 4) == 4
    assert deadline.monotonic_seconds == before
    with pytest.raises(ValueError):
        utc_elapsed(100, 200, previous_session="utc-1", current_session="utc-2")


@pytest.mark.parametrize("bad", [math.nan, math.inf, True, "1", 10**1000])
def test_utc_numeric_values_are_finite(bad):
    with pytest.raises(ValueError):
        utc_elapsed(0, bad, previous_session="u", current_session="u")
