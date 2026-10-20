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


def test_separately_admitted_restart_round_trip_preserves_phase_caps():
    value,old=admitted()
    _,new=admitted(restart_operation_seconds=.3)
    assert new.operation_seconds==old.operation_seconds==.1
    assert new.active_seconds==old.active_seconds==1
    assert new.terminal_reserve_seconds==old.terminal_reserve_seconds
    assert new.restart_operation_seconds==.3
    assert json.loads(old.canonical_bytes)['version']==1
    assert json.loads(new.canonical_bytes)['version']==3
    assert new.digest!=old.digest
    assert decode_schedule(value,json.loads(new.canonical_bytes))==new
    body=json.loads(new.canonical_bytes);body['restart_operation_seconds']=5
    with pytest.raises(ValueError):decode_schedule(value,body)


def test_action_bounds_are_rederived_from_original_catalog_and_old_versions_stay_fixed():
    value,old=admitted(restart_operation_seconds=.3)
    _,new=admitted(restart_operation_seconds=.3,use_action_timeouts=True)
    assert new.operation_seconds==old.operation_seconds==.1
    assert new.active_seconds==old.active_seconds==1
    assert json.loads(old.canonical_bytes)['version']==3
    assert json.loads(new.canonical_bytes)['version']==4
    assert new.use_action_timeouts is True
    expected=tuple((u.unit_id,a.phase,a.timeout_seconds) for u in value.units for a in u.plan.actions)
    assert new.action_timeouts==expected
    assert decode_schedule(value,json.loads(new.canonical_bytes))==new
    body=json.loads(new.canonical_bytes);body['action_timeouts'][0][2]+=.01
    with pytest.raises(ValueError):decode_schedule(value,body)
    body=json.loads(old.canonical_bytes);body['use_action_timeouts']=False
    with pytest.raises(ValueError):decode_schedule(value,body)


@pytest.mark.parametrize('flag',[1,None,'true',(),[]])
def test_action_timeout_mode_requires_explicit_boolean(flag):
    with pytest.raises(ValueError):admitted(use_action_timeouts=flag)


@pytest.mark.parametrize('timeout',[True,0,-1,float('nan'),float('inf'),5,10**500])
def test_restart_cap_is_finite_and_fits_original_health_period(timeout):
    with pytest.raises(ValueError):admitted(restart_operation_seconds=timeout)


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


def test_explicit_shared_controller_service_budget_is_rederived_and_v1_stays_exact():
    value, original = admitted()
    _, current = admitted(service_operation_count=4)
    old = json.loads(original.canonical_bytes)
    body = json.loads(current.canonical_bytes)
    assert old['version'] == 1 and 'service_operation_count' not in old
    assert original.service_operation_count is None
    assert body['version'] == 2 and body['service_operation_count'] == 4
    assert current.health_slots == 22 and current.required_requests == 109
    assert current.required_events == 186
    assert decode_schedule(value, body) == current
    for change in [dict(version=1),dict(version=3),dict(service_operation_count=True),dict(required_requests=108)]:
        with pytest.raises(ValueError):
            decode_schedule(value, dict(body, **change))
    for count in (0,33,True,1.5):
        with pytest.raises(ValueError):
            admitted(service_operation_count=count)


def test_recovery_bound_is_sealed_and_old_action_admission_remains_version4():
    value=prepared()
    options=dict(policies=tuple(ProbePolicy(u.unit_id,5,5,.5) for u in value.units),
                 ticks=(0,value.clock.horizon_ticks),active_seconds=20,operation_seconds=.3,
                 request_limit=1024,use_action_timeouts=True)
    old=admit_schedule(value,**options)
    fresh=admit_schedule(value,**options,recovery_operation_seconds=3)
    assert json.loads(old.canonical_bytes)['version']==4
    assert json.loads(fresh.canonical_bytes)['version']==5
    assert fresh.recovery_operation_seconds==3 and fresh.operation_seconds==old.operation_seconds
    assert fresh.action_timeouts==old.action_timeouts
    assert decode_schedule(value,json.loads(fresh.canonical_bytes))==fresh
    body=json.loads(fresh.canonical_bytes);body['recovery_operation_seconds']=.5
    with pytest.raises(ValueError):decode_schedule(value,body)


@pytest.mark.parametrize('cap',[True,0,5.1,float('nan'),float('inf')])
def test_recovery_bound_rejects_invalid_or_unusable_caps(cap):
    with pytest.raises(ValueError):admitted(recovery_operation_seconds=cap)
