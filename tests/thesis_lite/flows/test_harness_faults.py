"""V07-V09 and rule 13: Phase 5 message faults through flow routes in the tick-driven harness."""

from __future__ import annotations

import pytest

from xverse.faults import resolve_schedule
from xverse.flows import FlowEvidence, FlowRunHarness, TickClock, bind, reconstruct_flows

from ..faults.support import fault, parameter
from .support import PLANNED_TICKS, compile_fixture, documents


class Writer:
    """Captures Argus append_event calls."""

    def __init__(self):
        self.events = []

    def append_event(self, **fields):
        self.events.append(fields)


def run(faults=(), *, refuse_apply=None, listener=None):
    plan, resources = compile_fixture(documents("uniform"), list(faults))
    record = bind(plan, resources)
    assert record.activatable(), record.refusals
    entries = resolve_schedule(plan, PLANNED_TICKS)
    harness = FlowRunHarness(record, PLANNED_TICKS, entries, seed=7, clock=TickClock({"control-time": 1}), listener=listener)
    if refuse_apply:
        harness.relays[refuse_apply].refuse_apply = True
    for tick in PLANNED_TICKS:
        for flow in ("camera-flow", "radar-flow"):
            harness.offer(tick, flow, tick // 2)
    return harness, harness.run()


def verdicts(harness, flow):
    return [(v.sequence, v.verdict, v.age_ns, v.gap_before) for v in harness.receivers[flow].verdicts]


def test_v07_nominal_all_delivered_without_deadline_misses():
    harness, result = run()
    assert result.status == "completed" and result.held_at_end == {"camera-flow": 0, "radar-flow": 0}
    for flow in ("camera-flow", "radar-flow"):
        summary = result.summaries[flow]
        assert summary["deliveredCount"] == len(PLANNED_TICKS) and summary["withheldCount"] == 0
        assert summary["gapCount"] == 0 and summary["deadlineMissedCount"] == 0 and summary["maxAgeNs"] == 0


def test_v07_delay_ages_grow_by_the_hold_and_clear_releases_through_the_outbox():
    harness, result = run([fault("f-delay", "delay", "camera-flow", at=10, duration=6, parameters=[parameter("delay-ticks", 4)])])
    camera = {seq: (verdict, age) for seq, verdict, age, _ in verdicts(harness, "camera-flow")}
    assert camera[5] == ("delivered", 4)  # offered at 10, released at its due tick 14
    assert camera[6] == ("delivered", 4) and camera[7] == ("delivered", 2)  # released early by the clear at 16
    assert result.summaries["camera-flow"]["deadlineMissedCount"] == 1  # silence 8..14 exceeds the 5-tick deadline
    assert result.summaries["radar-flow"]["deliveredCount"] == len(PLANNED_TICKS)  # V09 independence


def test_v07_long_delay_is_stale():
    harness, result = run([fault("f-delay", "delay", "camera-flow", at=10, duration=10, parameters=[parameter("delay-ticks", 8)])])
    assert ("stale" in {v for _, v, _, _ in verdicts(harness, "camera-flow")}) and result.summaries["camera-flow"]["counts"]["stale"] >= 1


def test_v07_loss_leaves_a_gap():
    harness, result = run([fault("f-loss", "loss", "radar-flow", at=10, duration=6, parameters=[parameter("every", 2)])])
    radar = verdicts(harness, "radar-flow")
    assert (7, "delivered", 0, 1) in radar and result.summaries["radar-flow"]["gapCount"] == 1
    assert result.summaries["camera-flow"]["gapCount"] == 0


def test_v07_relay_stale_replays_as_duplicates_then_a_gap():
    harness, result = run([fault("f-stale", "stale", "camera-flow", at=10, duration=4)])
    camera = verdicts(harness, "camera-flow")
    assert [(seq, verdict) for seq, verdict, _, _ in camera if verdict == "duplicate"] == [(4, "duplicate"), (4, "duplicate")]
    assert (7, "delivered", 0, 2) in camera


def test_v08_duplicate_copies():
    harness, result = run([fault("f-dup", "duplicate", "radar-flow", at=10, duration=2, parameters=[parameter("copies", 2)])])
    assert [v for s, v, _, _ in verdicts(harness, "radar-flow") if s == 5] == ["delivered", "duplicate", "duplicate"]
    assert result.summaries["radar-flow"]["counts"]["duplicate"] == 2


def test_v08_reorder_on_fifo_route():
    harness, result = run([fault("f-reorder", "reorder", "camera-flow", at=10, duration=8, parameters=[parameter("window", 2)])])
    camera = verdicts(harness, "camera-flow")
    assert (7, "delivered", 0, 2) in camera
    assert [(s, v) for s, v, _, _ in camera if s in (5, 6)] == [(6, "out-of-order"), (5, "out-of-order")]
    assert (8, "delivered") in [(s, v) for s, v, _, _ in camera]  # partial block released by the clear at 18
    assert result.summaries["camera-flow"]["filledGapCount"] == 0


def test_v08_partial_reorder_block_cleared_at_the_last_tick_reaches_the_receiver():
    # Resolution refuses a window clearing beyond the last planned tick (XVERSE-FAULT-HORIZON), so the
    # latest possible release is the clear at tick 40: the partial block [17, 18, 19] goes through the outbox.
    harness, result = run([fault("f-reorder", "reorder", "camera-flow", at=34, duration=6, parameters=[parameter("window", 4)])])
    camera = verdicts(harness, "camera-flow")
    assert [(s, v, g) for s, v, _, g in camera if s >= 17] == [
        (19, "delivered", 2), (18, "out-of-order", 0), (17, "out-of-order", 0), (20, "delivered", 0)]
    assert result.held_at_end["camera-flow"] == 0 and result.status == "completed"


def test_v07_failed_apply_ends_the_run_with_summaries():
    rec = Writer()
    evidence = FlowEvidence(rec, "run-x", lambda tick: {"simulation": {"domain": "experiment-time", "unit": "tick", "value": tick or 0}})
    harness, result = run([fault("f-delay", "delay", "camera-flow", at=10, duration=4, parameters=[parameter("delay-ticks", 2)])],
                          refuse_apply="camera-flow", listener=evidence)
    assert result.status == "failed" and result.failure and result.final_tick == 10
    assert {e["event_id"].rsplit(".", 1)[-1] for e in rec.events if e["event_id"].endswith(".sum")} == {"sum"}
    assert sum(1 for e in rec.events if e["event_id"].endswith(".sum")) == 2


def test_rule_13_evidence_reconstructs_offline_and_detects_tampering():
    writer = Writer()
    evidence = FlowEvidence(writer, "run-y", lambda tick: {"simulation": {"domain": "experiment-time", "unit": "tick", "value": tick or 0}})
    harness, result = run([fault("f-reorder", "reorder", "camera-flow", at=10, duration=8, parameters=[parameter("window", 2)]),
                           fault("f-loss", "loss", "radar-flow", at=10, duration=6, parameters=[parameter("every", 2)])], listener=evidence)
    payloads = [e["extensions"]["io.xverse.flows"] for e in writer.events]
    assert all(len(e["event_id"]) <= 128 for e in writer.events)
    ok = reconstruct_flows(payloads, harness.record)
    assert ok == {"camera-flow": {"ok": True, "mismatches": []}, "radar-flow": {"ok": True, "mismatches": []}}
    withheld = next(i for i, p in enumerate(payloads) if p.get("event") == "withheld")
    tampered = reconstruct_flows(payloads[:withheld] + payloads[withheld + 1:], harness.record)
    assert not tampered["camera-flow"]["ok"]
