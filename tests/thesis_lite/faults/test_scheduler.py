"""U-SCH-01…09, U-BND-01…05, U-EVD-01…03: scheduler, relays and evidence on owned fixtures (V03–V08, V11, V12)."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from xverse.argus import EvidenceStore
from xverse.faults import FaultError, resolve_schedule
from xverse.faults.boundary import (
    BoundaryHandle,
    BoundaryOutcome,
    CounterGenerator,
    MessageRelayBoundary,
    ObservationRelayBoundary,
    ProcessBoundary,
)
from xverse.faults.evidence import FaultEvidence, closure_obligation, closure_report, reconstruct
from xverse.faults.scheduler import FaultScheduler

from .support import PLANNED_TICKS, compiled_plan, fault, parameter, six_kind_faults


@dataclass
class FakeProcess:
    """Owned-operation fake recording kill/freeze/thaw calls; ``live`` controls revalidation."""

    live: bool = True
    refuse: set = field(default_factory=set)
    calls: list = field(default_factory=list)

    def fault(self, operation: str) -> BoundaryOutcome:
        self.calls.append(operation)
        if operation in self.refuse:
            return BoundaryOutcome(False, "XVERSE-FAULT-BOUNDARY-REFUSED", {"operation": operation})
        if operation == "kill":
            self.live = False
        return BoundaryOutcome(True, detail={"operation": operation})

    def revalidate(self) -> bool:
        return self.live


def boundaries(seed=0, *, intents=None):
    flow = MessageRelayBoundary("sample-flow", seed=seed)
    sensor = ObservationRelayBoundary("front-sensor")
    source = ProcessBoundary("source-instance", FakeProcess(), intend=(lambda e, t: intents.append((e, t))) if intents is not None else None)
    sink = ProcessBoundary("sink-instance", FakeProcess())
    return {("flows", "sample-flow"): flow, ("sensors", "front-sensor"): sensor,
            ("componentInstances", "source-instance"): source, ("componentInstances", "sink-instance"): sink}


def run_all(entries, bounds, seed=0, listener=None, run_id="run-a"):
    scheduler = FaultScheduler(run_id, entries, bounds, PLANNED_TICKS, seed=seed, listener=listener)
    scheduler.start()
    for tick in PLANNED_TICKS:
        scheduler.advance(tick)
        for boundary in bounds.values():
            if isinstance(boundary, MessageRelayBoundary):
                boundary.submit(f"item@{tick}", tick)
            if isinstance(boundary, ObservationRelayBoundary):
                boundary.observe(f"sample@{tick}", tick)
    outcomes = scheduler.finish(PLANNED_TICKS[-1])
    return scheduler, outcomes


def test_u_sch_01_same_plan_and_seed_identical_decisions():
    plan = compiled_plan(six_kind_faults())
    entries = resolve_schedule(plan, PLANNED_TICKS)
    first, out1 = run_all(entries, boundaries(seed=7), seed=7)
    second, out2 = run_all(entries, boundaries(seed=7), seed=7)
    assert first.decisions == second.decisions and out1 == out2
    assert out1 == {"fault:f-delay": "cleared", "fault:f-loss": "cleared", "fault:f-stale": "cleared",
                    "fault:f-crash": "cleared", "fault:f-freeze": "cleared", "fault:f-dropout": "cleared"}
    assert not first.incomplete and not first.run_failed


def test_u_sch_02_boundary_refusal_and_failure_policy():
    entries = resolve_schedule(compiled_plan([fault("f-s", "stale", "sample-flow", at=2, duration=2)]), PLANNED_TICKS)
    bounds = boundaries(); bounds[("flows", "sample-flow")].refuse_apply = True
    scheduler, outcomes = run_all(entries, bounds)
    assert outcomes == {"fault:f-s": "failed-to-apply"} and scheduler.run_failed
    entries = resolve_schedule(compiled_plan([fault("f-s", "stale", "sample-flow", at=2, duration=2, parameters=[parameter("on-apply-failure", "continue")])]), PLANNED_TICKS)
    bounds = boundaries(); bounds[("flows", "sample-flow")].refuse_apply = True
    scheduler, outcomes = run_all(entries, bounds)
    assert outcomes == {"fault:f-s": "failed-to-apply"} and not scheduler.run_failed


def test_u_sch_03_clearing_failure_blocks_target_and_marks_incomplete():
    faults = [fault("f-a", "stale", "sample-flow", at=2, duration=2), fault("f-b", "stale", "sample-flow", at=16, duration=2)]
    entries = resolve_schedule(compiled_plan(faults), PLANNED_TICKS)
    bounds = boundaries(); bounds[("flows", "sample-flow")].refuse_clear = True
    scheduler, outcomes = run_all(entries, bounds)
    assert outcomes["fault:f-a"] == "incomplete-clearing" and outcomes["fault:f-b"] == "cancelled"
    assert scheduler.incomplete and ("flows", "sample-flow") in scheduler.blocked_targets
    assert any(d.diagnostic == "XVERSE-FAULT-TARGET-BLOCKED" for d in scheduler.decisions)


def test_u_sch_04_serialize_waits_until_the_earlier_clears():
    faults = [fault("f-a", "stale", "sample-flow", at=2, duration=6),
              fault("f-b", "stale", "sample-flow", at=4, duration=2, parameters=[parameter("arbitration", "serialize")])]
    entries = resolve_schedule(compiled_plan(faults), PLANNED_TICKS)
    scheduler, outcomes = run_all(entries, boundaries())
    applied = {d.entry_id: d.tick for d in scheduler.decisions if d.phase == "apply" and d.outcome == "applied"}
    assert applied["fault:f-a"] == 2 and applied["fault:f-b"] == 8  # f-a clears at 8 (first planned tick >= 2+6)
    assert outcomes == {"fault:f-a": "cleared", "fault:f-b": "cleared"}
    assert any(d.phase == "arbitration" and d.outcome == "waiting" for d in scheduler.decisions)


def test_u_sch_05_supersede_cancels_the_earlier_entry():
    faults = [fault("f-a", "stale", "sample-flow", at=2, duration=6),
              fault("f-b", "stale", "sample-flow", at=4, duration=2, parameters=[parameter("arbitration", "supersede")])]
    entries = resolve_schedule(compiled_plan(faults), PLANNED_TICKS)
    scheduler, outcomes = run_all(entries, boundaries())
    assert outcomes == {"fault:f-a": "cancelled", "fault:f-b": "cleared"}
    applied = {d.entry_id: d.tick for d in scheduler.decisions if d.phase == "apply" and d.outcome == "applied"}
    assert applied["fault:f-b"] == 4


def test_u_sch_06_cancellation_mid_window():
    entries = resolve_schedule(compiled_plan([fault("f-a", "stale", "sample-flow", at=2, duration=20)]), PLANNED_TICKS)
    scheduler = FaultScheduler("run-a", entries, boundaries(), PLANNED_TICKS)
    scheduler.start(); scheduler.advance(0); scheduler.advance(2)
    decisions = scheduler.cancel(4, "operator")
    assert scheduler.outcomes == {"fault:f-a": "cancelled"}
    assert any(d.phase == "clear" and d.outcome == "cleared" for d in decisions)
    finals = [d for d in scheduler.decisions if d.phase == "final"]
    assert [(d.entry_id, d.outcome) for d in finals] == [("fault:f-a", "cancelled")]  # exactly one final per entry


def test_u_sch_06c_run_ending_entry_is_finalized_as_applied():
    entries = resolve_schedule(compiled_plan([fault("f-c", "crash", "source-instance", at=2, duration=0),
                                              fault("f-s", "stale", "sample-flow", at=2, duration=4)]), PLANNED_TICKS)
    scheduler = FaultScheduler("run-a", entries, boundaries(), PLANNED_TICKS)
    scheduler.start(); scheduler.advance(0); scheduler.advance(2); scheduler.cancel(2, "run-failed", ended_by="fault:f-c")
    finals = sorted((d.entry_id, d.outcome, d.diagnostic) for d in scheduler.decisions if d.phase == "final")
    assert finals == [("fault:f-c", "applied", "XVERSE-FAULT-ENDED-RUN"), ("fault:f-s", "cancelled", "XVERSE-FAULT-CANCELLED")]


def test_u_sch_06b_cancel_with_a_failing_clear_finalizes_once_as_incomplete():
    entries = resolve_schedule(compiled_plan([fault("f-a", "stale", "sample-flow", at=2, duration=20)]), PLANNED_TICKS)
    bounds = boundaries(); bounds[("flows", "sample-flow")].refuse_clear = True
    scheduler = FaultScheduler("run-a", entries, bounds, PLANNED_TICKS)
    scheduler.start(); scheduler.advance(0); scheduler.advance(2); scheduler.cancel(4, "run-failed")
    finals = [d for d in scheduler.decisions if d.phase == "final"]
    assert [(d.entry_id, d.outcome) for d in finals] == [("fault:f-a", "incomplete-clearing")] and scheduler.incomplete


def test_u_sch_07_foreign_or_revoked_handle_is_refused():
    relay = MessageRelayBoundary("sample-flow")
    entry = resolve_schedule(compiled_plan([fault("f-a", "stale", "sample-flow", at=2, duration=2)]), PLANNED_TICKS)[0]
    handle = relay.arm("run-a", entry)
    foreign = BoundaryHandle("run-b", entry.entry_id, "message", handle.nonce)
    assert relay.apply(foreign, 2, {"_kind": "stale"}).diagnostic == "XVERSE-FAULT-HANDLE"
    assert relay.arm("run-a", entry).diagnostic == "XVERSE-FAULT-HANDLE"
    relay.release(handle)
    assert relay.apply(handle, 2, {"_kind": "stale"}).diagnostic == "XVERSE-FAULT-HANDLE"
    assert relay.delivered == [] and relay.dropped == []


def test_u_sch_08_vanished_owned_child():
    process = FakeProcess(live=False)
    boundary = ProcessBoundary("source-instance", process)
    entry = resolve_schedule(compiled_plan([fault("f-c", "crash", "source-instance", at=2, duration=0)]), PLANNED_TICKS)[0]
    handle = boundary.arm("run-a", entry)  # arming does not need a live unit (lazy binding)
    assert boundary.apply(handle, 2, {"_kind": "crash"}).diagnostic == "XVERSE-FAULT-BOUNDARY-GONE"
    boundary = ProcessBoundary("source-instance", process)
    entries = resolve_schedule(compiled_plan([fault("f-c", "crash", "source-instance", at=2, duration=0)]), PLANNED_TICKS)
    bounds = boundaries(); bounds[("componentInstances", "source-instance")] = boundary
    scheduler, outcomes = run_all(entries, bounds)
    assert outcomes == {"fault:f-c": "failed-to-apply"} and scheduler.run_failed and process.calls == []


def test_u_sch_08b_kill_after_the_fault_window_is_refused():
    process = FakeProcess()
    boundary = ProcessBoundary("source-instance", process)
    entry = resolve_schedule(compiled_plan([fault("f-c", "crash", "source-instance", at=2, duration=0)]), PLANNED_TICKS)[0]
    handle = boundary.arm("run-a", entry)
    assert boundary.apply(handle, 2, {"_kind": "crash"}).ok and boundary.clear(handle, 2).ok
    boundary.release(handle)
    assert boundary.apply(handle, 4, {"_kind": "crash"}).diagnostic == "XVERSE-FAULT-HANDLE"
    assert process.calls == ["kill"]


def test_u_sch_08c_refused_kill_retracts_the_termination_record():
    intents, retracted = [], []
    process = FakeProcess(refuse={"kill"})
    boundary = ProcessBoundary("source-instance", process, intend=lambda e, t: intents.append(e), retract=retracted.append)
    entry = resolve_schedule(compiled_plan([fault("f-c", "crash", "source-instance", at=2, duration=0)]), PLANNED_TICKS)[0]
    handle = boundary.arm("run-a", entry)
    assert not boundary.apply(handle, 2, {"_kind": "crash"}).ok
    assert intents == ["fault:f-c"] and retracted == ["fault:f-c"]


def test_u_sch_09_seeded_loss_is_counter_based():
    a, b = CounterGenerator(7, "x"), CounterGenerator(7, "x")
    assert [a.next() for _ in range(5)] == [b.next() for _ in range(5)]
    assert [CounterGenerator(8, "x").next() for _ in range(5)] != [CounterGenerator(7, "x").next() for _ in range(5)]
    entries = resolve_schedule(compiled_plan([fault("f-l", "loss", "sample-flow", at=0, duration=32, parameters=[parameter("loss-ratio", 0.5)])]), PLANNED_TICKS)
    drops = []
    for seed in (3, 3, 4):
        bounds = boundaries(seed=seed)
        run_all(entries, bounds, seed=seed)
        drops.append([tick for tick, _ in bounds[("flows", "sample-flow")].dropped])
    assert drops[0] == drops[1] and drops[0] != drops[2]


def test_u_bnd_01_delay_holds_then_releases_in_order():
    relay = MessageRelayBoundary("sample-flow")
    entry = resolve_schedule(compiled_plan([fault("f-d", "delay", "sample-flow", at=2, duration=4, parameters=[parameter("delay-ticks", 3)])]), PLANNED_TICKS)[0]
    handle = relay.arm("run-a", entry)
    assert relay.submit("a", 0) == ["a"]
    assert relay.apply(handle, 2, {"_kind": "delay", "delay-ticks": 3}).ok
    assert relay.submit("b", 2) == [] and relay.submit("c", 4) == []
    assert relay.submit("d", 8) == ["b", "c"]  # b due at 5, c at 7; d held until 11
    assert relay.clear(handle, 8).detail["released"] == 1
    assert [item for _, item in relay.delivered] == ["a", "b", "c", "d"]


def test_u_bnd_02_loss_every_and_counters_frozen():
    relay = MessageRelayBoundary("sample-flow")
    entry = resolve_schedule(compiled_plan([fault("f-l", "loss", "sample-flow", at=2, duration=4, parameters=[parameter("every", 2)])]), PLANNED_TICKS)[0]
    handle = relay.arm("run-a", entry)
    assert relay.apply(handle, 2, {"_kind": "loss", "every": 2}).ok
    delivered = [relay.submit(f"i{n}", 2) for n in range(4)]
    assert delivered == [["i0"], [], ["i2"], []] and [i for _, i in relay.dropped] == ["i1", "i3"]
    assert relay.clear(handle, 8).ok
    assert relay.submit("i4", 8) == ["i4"] and len(relay.dropped) == 2


def test_u_bnd_03_stale_replays_last_item():
    relay = MessageRelayBoundary("sample-flow")
    entry = resolve_schedule(compiled_plan([fault("f-s", "stale", "sample-flow", at=2, duration=2)]), PLANNED_TICKS)[0]
    handle = relay.arm("run-a", entry)
    relay.submit("fresh-0", 0)
    assert relay.apply(handle, 2, {"_kind": "stale"}).ok
    assert relay.submit("fresh-1", 2) == ["fresh-0"] and relay.submit("fresh-2", 4) == ["fresh-0"]
    assert relay.clear(handle, 4).ok and relay.submit("fresh-3", 8) == ["fresh-3"]
    assert [i for _, i in relay.replayed] == ["fresh-0", "fresh-0"]


def test_u_bnd_04_sensor_dropout_suppresses_then_resumes():
    relay = ObservationRelayBoundary("front-sensor")
    entry = resolve_schedule(compiled_plan([fault("f-o", "sensorDropout", "front-sensor", at=2, duration=2)]), PLANNED_TICKS)[0]
    handle = relay.arm("run-a", entry)
    assert relay.observe("s0", 0) and relay.apply(handle, 2, {"_kind": "sensorDropout"}).ok
    assert not relay.observe("s1", 2) and relay.clear(handle, 4).ok and relay.observe("s2", 4)
    assert [s for _, s in relay.suppressed] == ["s1"] and [s for _, s in relay.delivered] == ["s0", "s2"]


def test_u_bnd_05_process_boundary_records_intent_before_kill_and_thaws():
    intents = []
    bounds = boundaries(intents=intents)
    faults = [fault("f-crash", "crash", "source-instance", at=4, duration=0), fault("f-freeze", "freeze", "sink-instance", at=4, duration=4)]
    entries = resolve_schedule(compiled_plan(faults), PLANNED_TICKS)
    scheduler, outcomes = run_all(entries, bounds)
    assert intents == [("fault:f-crash", 4)]
    assert bounds[("componentInstances", "source-instance")]._operations.calls == ["kill"]
    assert bounds[("componentInstances", "sink-instance")]._operations.calls == ["freeze", "thaw"]
    assert outcomes == {"fault:f-crash": "cleared", "fault:f-freeze": "cleared"}


def _clocks(tick: int):
    return {"host": {"domain": "host:test", "unit": "s", "value": 100.0 + tick},
            "utc": {"domain": "utc:test", "unit": "s", "value": 1_700_000_000.0 + tick},
            "simulation": {"domain": "experiment-time", "unit": "tick", "value": tick}}


def _open_run(tmp_path, plan, name="run"):
    return EvidenceStore.open_run(tmp_path / name, run_id="run-a", plan=plan, obligations=[closure_obligation()], clocks=_clocks(0))


def test_u_evd_01_four_event_chain_with_causation(tmp_path):
    plan = compiled_plan(six_kind_faults())
    entries = resolve_schedule(plan, PLANNED_TICKS)
    writer = _open_run(tmp_path, plan)
    evidence = FaultEvidence(writer, "run-a", _clocks)
    for entry in entries:
        evidence.intent(entry, 0)
    run_all(entries, boundaries(), listener=evidence)
    writer.finalize()
    reader = EvidenceStore.read_run(tmp_path / "run")
    chains = reconstruct(reader.records())
    report = closure_report(chains)
    assert set(chains) == {"f-delay", "f-loss", "f-stale", "f-crash", "f-freeze", "f-dropout"}
    assert report["complete"] and report["open"] == [] and report["broken"] == []
    chain = chains["f-delay"]
    assert chain.phases[:4] == [("intent", None), ("apply", "applied"), ("clear", "cleared"), ("outcome", "cleared")]
    assert chain.events[1]["causationId"] == chain.events[0]["eventId"] and chain.events[2]["causationId"] == chain.events[1]["eventId"]
    assert chain.events[0][EXTENSION_KEY]["faultKind"] == "delay"
    assert reader.assessed_evidence_status == "complete"


EXTENSION_KEY = "io.xverse.faults"


def test_u_evd_01b_same_plan_gives_identical_argus_chains(tmp_path):
    """V03: two runs of one plan and seed give identical per-entry chains (phases, outcomes, ticks)."""

    plan = compiled_plan(six_kind_faults())
    entries = resolve_schedule(plan, PLANNED_TICKS)
    shapes = []
    for name in ("run-1", "run-2"):
        writer = _open_run(tmp_path, plan, name)
        evidence = FaultEvidence(writer, "run-a", _clocks)
        for entry in entries:
            evidence.intent(entry, 0)
        run_all(entries, boundaries(seed=5), seed=5, listener=evidence)
        writer.finalize()
        chains = reconstruct(EvidenceStore.read_run(tmp_path / name).records())
        shapes.append({f: [(e["eventId"], e[EXTENSION_KEY]["phase"], e[EXTENSION_KEY].get("outcome"), e[EXTENSION_KEY]["tick"]) for e in c.events]
                       for f, c in chains.items()})
    assert shapes[0] == shapes[1]


def test_u_evd_02_failure_chains(tmp_path):
    plan = compiled_plan([fault("f-a", "stale", "sample-flow", at=2, duration=2, parameters=[parameter("on-apply-failure", "continue")]),
                          fault("f-b", "sensorDropout", "front-sensor", at=2, duration=2)])
    entries = resolve_schedule(plan, PLANNED_TICKS)
    bounds = boundaries(); bounds[("flows", "sample-flow")].refuse_apply = True; bounds[("sensors", "front-sensor")].refuse_clear = True
    writer = _open_run(tmp_path, plan)
    evidence = FaultEvidence(writer, "run-a", _clocks)
    run_all(entries, bounds, listener=evidence)
    writer.finalize()
    chains = reconstruct(EvidenceStore.read_run(tmp_path / "run").records())
    assert chains["f-a"].status == "apply-failed" and chains["f-b"].status == "open"
    report = closure_report(chains)
    assert not report["complete"] and report["open"] == ["f-b"]


def test_u_evd_03_missing_closure_is_visible_offline(tmp_path):
    plan = compiled_plan([fault("f-a", "stale", "sample-flow", at=2, duration=2)])
    entries = resolve_schedule(plan, PLANNED_TICKS)
    writer = _open_run(tmp_path, plan)
    evidence = FaultEvidence(writer, "run-a", _clocks)
    scheduler = FaultScheduler("run-a", entries, boundaries(), PLANNED_TICKS, listener=evidence)
    scheduler.start(); scheduler.advance(0); scheduler.advance(2)
    writer.finalize()  # the run closes without the clearing decision
    chains = reconstruct(EvidenceStore.read_run(tmp_path / "run").records())
    assert chains["f-a"].status == "open" and not closure_report(chains)["complete"]


def test_scheduler_rejects_unplanned_ticks_and_double_start():
    entries = resolve_schedule(compiled_plan([fault("f-a", "stale", "sample-flow", at=2, duration=2)]), PLANNED_TICKS)
    scheduler = FaultScheduler("run-a", entries, boundaries(), PLANNED_TICKS)
    with pytest.raises(FaultError) as caught:
        scheduler.advance(0)
    assert caught.value.code == "XVERSE-FAULT-SCHEDULER"
    scheduler.start()
    with pytest.raises(FaultError) as caught:
        scheduler.advance(3)
    assert caught.value.code == "XVERSE-FAULT-TICKS"
