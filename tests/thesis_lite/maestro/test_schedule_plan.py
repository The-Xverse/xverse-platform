"""Pure admission expectations; no provider, file or worker effects are permitted."""

from dataclasses import FrozenInstanceError
import json
import pytest
from xverse.maestro.schedule_plan import admit_schedule, decode_schedule
from xverse.maestro.providers import ProbePolicy
from .test_preparation import prepared


def admitted(**options):
    value = prepared()
    defaults = dict(
        policies=tuple(ProbePolicy(u.unit_id, 2, 1, 0.1) for u in value.units),
        ticks=(0, 0, value.clock.horizon_ticks),
        active_seconds=1,
        operation_seconds=0.1,
        request_limit=128,
    )
    defaults.update(options)
    return value, admit_schedule(value, **defaults)


def test_exact_pure_admission_and_round_trip():
    value, plan = admitted()
    # 2 units, one prerequisite, 6 own attempts, 1 prior scan, 17 early-health
    # slots per unit, 2 explicit steps and three declared ticks including pause.
    assert plan.health_scan_seconds == 0.2 and plan.health_slots == 17
    assert plan.required_requests == 77
    assert plan.required_events == 156
    assert plan.ticks == (0, 0, 10000)
    assert decode_schedule(value, json.loads(plan.canonical_bytes)) == plan
    assert not plan.ready_for_execution
    with pytest.raises(FrozenInstanceError):
        plan.digest = "forged"


@pytest.mark.parametrize(
    "name,value",
    [
        ("active_seconds", True),
        ("active_seconds", 0),
        ("active_seconds", 301),
        ("operation_seconds", float("nan")),
        ("operation_seconds", float("inf")),
        ("operation_seconds", 10**500),
        ("poll_seconds", 0.1),
        ("per_unit_seconds", 6),
        ("request_limit", 127),
        ("request_limit", 8193),
        ("event_limit", 8193),
        ("event_limit", 1),
        ("ticks", (1, 10000)),
        ("ticks", (0, 1, 0, 10000)),
        ("ticks", (0, True, 10000)),
        ("ticks", (0, 10001)),
        ("ticks", (0,)),
        ("ticks", []),
        ("policies", ()),
        ("operation_seconds", 0.3),
    ],
)
def test_invalid_admission_rejects(name, value):
    with pytest.raises(ValueError):
        admitted(**{name: value})


def test_budget_is_independent_of_tick_pauses_and_covers_health():
    _, short = admitted()
    _, long = admitted(active_seconds=40, request_limit=8192)
    assert long.health_slots > short.health_slots
    assert long.required_requests > short.required_requests
    assert long.required_events > short.required_events
    with pytest.raises(ValueError):
        admitted(active_seconds=40)


def test_worker_rederives_instead_of_trusting_serialized_budget():
    value, plan = admitted()
    for key in (
        "required_requests",
        "required_events",
        "health_slots",
        "health_scan_seconds",
        "version",
    ):
        body = json.loads(plan.canonical_bytes)
        body[key] += 1
        with pytest.raises(ValueError):
            decode_schedule(value, body)
    body = json.loads(plan.canonical_bytes)
    body["surprise"] = 1
    with pytest.raises(ValueError):
        decode_schedule(value, body)


def test_subnormal_cadence_rejects_derived_budget_without_overflow():
    from xverse.maestro.schedule_plan import ScheduleError

    value = prepared()
    with pytest.raises(ScheduleError):
        admit_schedule(
            value,
            policies=tuple(ProbePolicy(u.unit_id, 1, 1e-320, 0.1) for u in value.units),
            ticks=(0, 10000),
            active_seconds=1,
            operation_seconds=5e-324,
            poll_seconds=5e-324,
            request_limit=8192,
        )


def test_admission_itself_has_no_storage_or_process_effect(monkeypatch):
    value = prepared()
    policies = tuple(ProbePolicy(u.unit_id, 2, 1, 0.1) for u in value.units)

    def forbidden(*args, **kwargs):
        pytest.fail("admission performed I/O")

    monkeypatch.setattr("builtins.open", forbidden)
    monkeypatch.setattr("os.open", forbidden)
    monkeypatch.setattr("subprocess.Popen", forbidden)
    result = admit_schedule(
        value,
        policies=policies,
        ticks=(0, 10000),
        active_seconds=1,
        operation_seconds=0.1,
    )
    assert result.required_requests == 75
