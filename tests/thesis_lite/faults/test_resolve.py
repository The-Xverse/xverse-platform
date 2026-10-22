"""U-FLT-01 … U-FLT-10: vocabulary and schedule resolution (thesis V01, V02, V04, V11)."""

from __future__ import annotations

import pytest

from xverse.faults import FaultError, VOCABULARY, resolve_schedule

from .support import PLANNED_TICKS, SYSTEM_URI, compiled_plan, fault, parameter, six_kind_faults


def test_u_flt_01_six_kinds_resolve_without_side_effects():
    plan = compiled_plan(six_kind_faults())
    entries = resolve_schedule(plan, PLANNED_TICKS)
    assert [e.fault_id for e in entries] == sorted(e.fault_id for e in entries) or len(entries) == 6
    by_id = {e.fault_id: e for e in entries}
    assert by_id["f-delay"].boundary_class == "message" and by_id["f-crash"].boundary_class == "process"
    assert by_id["f-dropout"].boundary_class == "observation"
    assert all(e.executable for e in entries) and all(e.target_uri == SYSTEM_URI for e in entries)
    assert by_id["f-delay"].parameters.values == {"delay-ticks": 1}
    assert by_id["f-loss"].parameters.values == {"every": 2}


def test_u_flt_02_unknown_kind():
    with pytest.raises(FaultError) as caught:
        resolve_schedule(compiled_plan([fault("f-x", "meteor", "sample-flow")]), PLANNED_TICKS)
    assert caught.value.code == "XVERSE-FAULT-KIND"


def test_u_flt_03_target_without_boundary_or_wrong_class():
    with pytest.raises(FaultError) as caught:
        resolve_schedule(compiled_plan([fault("f-x", "delay", "source-instance", parameters=[parameter("delay-ticks", 1)])]), PLANNED_TICKS)
    assert caught.value.code == "XVERSE-FAULT-TARGET"
    with pytest.raises(FaultError) as caught:
        resolve_schedule(compiled_plan([fault("f-y", "crash", "experiment-time")]), PLANNED_TICKS)
    assert caught.value.code == "XVERSE-FAULT-TARGET"


def test_u_flt_04_overlap_needs_serialize_or_supersede():
    overlapping = [
        fault("f-a", "stale", "sample-flow", at=2, duration=6),
        fault("f-b", "stale", "sample-flow", at=4, duration=2),
    ]
    with pytest.raises(FaultError) as caught:
        resolve_schedule(compiled_plan(overlapping), PLANNED_TICKS)
    assert caught.value.code == "XVERSE-FAULT-OVERLAP"
    overlapping[1] = fault("f-b", "stale", "sample-flow", at=4, duration=2, parameters=[parameter("arbitration", "reject")])
    with pytest.raises(FaultError) as caught:
        resolve_schedule(compiled_plan(overlapping), PLANNED_TICKS)
    assert caught.value.code == "XVERSE-FAULT-OVERLAP"
    for policy in ("serialize", "supersede"):
        overlapping[1] = fault("f-b", "stale", "sample-flow", at=4, duration=2, parameters=[parameter("arbitration", policy)])
        entries = resolve_schedule(compiled_plan(overlapping), PLANNED_TICKS)
        assert {e.fault_id: e.parameters.arbitration for e in entries} == {"f-a": None, "f-b": policy}
    separate = [fault("f-a", "stale", "sample-flow", at=2, duration=2), fault("f-b", "stale", "sample-flow", at=8, duration=2)]
    assert len(resolve_schedule(compiled_plan(separate), PLANNED_TICKS)) == 2


def test_u_flt_05_horizon():
    with pytest.raises(FaultError) as caught:
        resolve_schedule(compiled_plan([fault("f-late", "stale", "sample-flow", at=40, duration=1)]), PLANNED_TICKS)
    assert caught.value.code == "XVERSE-FAULT-HORIZON"
    with pytest.raises(FaultError) as caught:
        resolve_schedule(compiled_plan([fault("f-long", "stale", "sample-flow", at=16, duration=100)]), PLANNED_TICKS)
    assert caught.value.code == "XVERSE-FAULT-HORIZON"


def test_u_flt_06_effective_tick_between_planned_ticks():
    entries = resolve_schedule(compiled_plan([fault("f-gap", "stale", "sample-flow", at=5, duration=2)]), PLANNED_TICKS)
    entry = entries[0]
    assert (entry.due_tick, entry.effective_tick, entry.clear_tick) == (5, 8, 16)
    assert entry.window == (8, 16)


def test_u_flt_07_tie_key_and_declared_order():
    faults = [
        fault("f-z", "stale", "sample-flow", at=2, duration=1),
        fault("f-a", "crash", "source-instance", at=2, duration=0),
        fault("f-ord", "freeze", "sink-instance", order=7, duration=2),
    ]
    entries = resolve_schedule(compiled_plan(faults), PLANNED_TICKS)
    keys = sorted(e.tie_key for e in entries)
    assert keys == [(7.0, "f-ord"), (float("inf"), "f-a"), (float("inf"), "f-z")]
    ordered = next(e for e in entries if e.fault_id == "f-ord")
    assert ordered.trigger_kind == "declared-order" and ordered.due_tick is None and ordered.window is None


def test_u_flt_08_duplicate_reorder_executable_assurance_declared_only():
    """Phase 6 amendment A1: duplicate/reorder execute on message relays; assurance hooks stay declared-only."""
    plan = compiled_plan([fault("f-dup", "duplicate", "sample-flow", at=2, duration=2, parameters=[parameter("copies", 2)])])
    entry = resolve_schedule(plan, PLANNED_TICKS)[0]
    assert entry.executable is True and entry.boundary_class == "message"
    assert VOCABULARY["duplicate"].executable is True and VOCABULARY["reorder"].executable is True
    assert all(not spec.executable for kind, spec in VOCABULARY.items() if kind.startswith("assurance."))


def test_u_flt_08b_overlap_now_covers_duplicate_and_reorder():
    """Amendment A1 side effect: an unarbitrated overlap with a duplicate on one flow is refused."""
    faults = [fault("f-delay", "delay", "sample-flow", at=2, duration=4, parameters=[parameter("delay-ticks", 1)]),
              fault("f-dup", "duplicate", "sample-flow", at=4, duration=2, parameters=[parameter("copies", 1)])]
    with pytest.raises(FaultError) as caught:
        resolve_schedule(compiled_plan(faults), PLANNED_TICKS)
    assert caught.value.code == "XVERSE-FAULT-OVERLAP"


def test_u_flt_09_parameter_schema():
    cases = (
        ("delay", "sample-flow", [parameter("delay-ticks", 0)]),
        ("delay", "sample-flow", [parameter("delay-ticks", 10**12)]),
        ("delay", "sample-flow", []),
        ("loss", "sample-flow", [parameter("loss-ratio", 1.5)]),
        ("loss", "sample-flow", [parameter("loss-ratio", 0.5), parameter("every", 2)]),
        ("stale", "sample-flow", [parameter("delay-ticks", 1)]),
        ("stale", "sample-flow", [parameter("arbitration", "later")]),
        ("stale", "sample-flow", [parameter("on-apply-failure", "ignore")]),
    )
    for kind, element, params in cases:
        with pytest.raises(FaultError) as caught:
            resolve_schedule(compiled_plan([fault("f-p", kind, element, parameters=params)]), PLANNED_TICKS)
        assert caught.value.code == "XVERSE-FAULT-PARAMETER", (kind, params)


def test_u_flt_10_durations_are_exact_compiled_ticks():
    plan = compiled_plan([fault("f-d", "stale", "sample-flow", at=2, duration=3)])
    entry = resolve_schedule(plan, PLANNED_TICKS)[0]
    assert entry.duration_ticks == plan["faultSchedule"][0]["duration"]["ticks"] == 3
    assert not hasattr(entry, "rounding")


def test_u_flt_11_paused_planned_ticks_are_accepted():
    entry = resolve_schedule(compiled_plan([fault("f-p", "stale", "sample-flow", at=1, duration=1)]), (0, 0, 1, 2, 3))[0]
    assert (entry.effective_tick, entry.clear_tick) == (1, 2)
    with pytest.raises(FaultError) as caught:
        resolve_schedule(compiled_plan([fault("f-p", "stale", "sample-flow", at=1, duration=1)]), (0, 2, 1, 3))
    assert caught.value.code == "XVERSE-FAULT-TICKS"


def test_u_flt_08c_duplicate_on_a_process_target_is_refused():
    """Amendment A1 side effect: an executable message kind needs a message (flow) target."""
    with pytest.raises(FaultError) as caught:
        resolve_schedule(compiled_plan([fault("f-dup", "duplicate", "source-instance", at=2, duration=2,
                                              parameters=[parameter("copies", 1)])]), PLANNED_TICKS)
    assert caught.value.code == "XVERSE-FAULT-TARGET"
