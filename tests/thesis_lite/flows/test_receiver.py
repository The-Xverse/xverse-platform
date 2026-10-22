"""V03/V05: receiver verdict precedence, state table, gaps, deadline liveness and queue (contract rules 7-12)."""

from __future__ import annotations

from xverse.flows import FlowItem, FlowReceiver
from xverse.flows.binding import FlowBinding, FlowPolicy
from xverse.flows.timebase import TimeMapping


class ManualClock:
    """Clock whose reading the test sets explicitly."""

    def __init__(self):
        self.now = 0

    def read(self, domain):
        return self.now


class Recorder:
    """Listener capturing receiver notifications."""

    def __init__(self):
        self.verdicts, self.deadlines, self.summaries = [], [], []

    def verdict(self, binding, result):
        self.verdicts.append(result)

    def deadline(self, binding, k, now):
        self.deadlines.append((k, now))

    def summary(self, binding, summary):
        self.summaries.append(summary)


def make(freshness=0, deadline=0, queue=8, offset=0, tolerance=0, ordering="fifo", drain=True, listener=None):
    binding = FlowBinding("f", "a", "b", "c", "ordered", FlowPolicy(ordering, "best-effort", queue, "reject", 0, 0), "best_effort",
                          "per_route_fifo", "p", "s", "r", TimeMapping("s", "r", offset, tolerance), freshness, deadline)
    clock = ManualClock()
    receiver = FlowReceiver(binding, clock, listener=listener, drain=drain, ordering=ordering)
    receiver.activate()
    return receiver, clock


def at(receiver, clock, now, seq, origin):
    clock.now = now
    return receiver.receive(FlowItem("f", seq, origin))


def test_v03_age_through_the_mapping_and_tolerance():
    receiver, clock = make(offset=1, tolerance=2)
    assert at(receiver, clock, 11, 0, 10).age_ns == 0
    late = at(receiver, clock, 12, 1, 12)  # age -1, within tolerance: kept negative, delivered
    assert (late.age_ns, late.verdict) == (-1, "delivered")
    bad = at(receiver, clock, 12, 2, 14)  # age -3 < -2
    assert (bad.verdict, bad.diagnostic, bad.delivered) == ("clock-error", "XVERSE-FLOW-TOLERANCE", False)
    assert at(receiver, clock, 13, 2, 12).verdict == "duplicate"  # the tolerance-failed item was received (state table)


def test_v04_clock_regression_does_not_move_the_baseline():
    receiver, clock = make()
    assert at(receiver, clock, 10, 0, 10).verdict == "delivered"
    regressed = at(receiver, clock, 9, 1, 9)
    assert (regressed.verdict, regressed.diagnostic) == ("clock-error", "XVERSE-FLOW-CLOCK-REGRESSION")
    assert at(receiver, clock, 11, 1, 11).verdict == "delivered"  # not marked seen by the regression


def test_v05_precedence_first_item_and_gaps_on_fifo():
    receiver, clock = make(freshness=5)
    first = at(receiver, clock, 1, 0, 1)
    assert (first.verdict, first.gap_before) == ("delivered", 0)
    jump = at(receiver, clock, 2, 3, 2)
    assert (jump.verdict, jump.gap_before) == ("delivered", 2)
    assert at(receiver, clock, 3, 3, 3).verdict == "duplicate"
    behind = at(receiver, clock, 4, 1, 4)
    assert (behind.verdict, behind.delivered, behind.fills_gap) == ("out-of-order", False, False)
    stale = at(receiver, clock, 20, 4, 10)
    assert (stale.verdict, stale.delivered, stale.age_ns) == ("stale", False, 10)
    assert at(receiver, clock, 21, 4, 21).verdict == "duplicate"  # the stale item was received
    summary = receiver.summary()
    assert summary["counts"] == {"clock-error": 0, "duplicate": 2, "out-of-order": 1, "stale": 1, "queue-full": 0, "delivered": 2}
    assert (summary["deliveredCount"], summary["withheldCount"], summary["gapCount"], summary["filledGapCount"]) == (2, 4, 1, 0)


def test_v05_unordered_unit_receiver_delivers_gap_fillers():
    receiver, clock = make(ordering="unordered")
    at(receiver, clock, 1, 0, 1)
    at(receiver, clock, 2, 3, 2)
    filler = at(receiver, clock, 3, 1, 3)
    assert (filler.verdict, filler.delivered, filler.fills_gap) == ("out-of-order", True, True)
    assert receiver.summary()["filledGapCount"] == 1


def test_v05_deadline_k_events_per_missed_interval():
    rec = Recorder()
    receiver, clock = make(deadline=5, listener=rec)
    at(receiver, clock, 3, 0, 3)  # delivered: anchor 3
    clock.now = 9
    receiver.poll()
    assert rec.deadlines == [(1, 9)]
    clock.now = 14
    receiver.poll()
    assert rec.deadlines == [(1, 9), (2, 14)]
    at(receiver, clock, 15, 1, 15)  # delivery resets the anchor
    clock.now = 33  # 3.6 deadlines of silence: three events
    receiver.poll()
    assert [k for k, _ in rec.deadlines[2:]] == [1, 2, 3] and receiver.summary()["deadlineMissedCount"] == 5


def test_v05_strict_inequality_and_activation_anchor():
    receiver, clock = make(deadline=5)
    clock.now = 5
    receiver.poll()
    assert receiver.deadline_missed_count == 0
    clock.now = 6
    receiver.poll()
    assert receiver.deadline_missed_count == 1


def test_v05_queue_full_is_a_received_withheld_verdict():
    receiver, clock = make(queue=1, drain=False)
    assert at(receiver, clock, 1, 0, 1).verdict == "delivered"
    full = at(receiver, clock, 2, 1, 2)
    assert (full.verdict, full.delivered) == ("queue-full", False)
    assert at(receiver, clock, 3, 1, 3).verdict == "duplicate"
    assert receiver.summary()["queueFullCount"] == 1


def test_v05_unordered_out_of_order_with_full_buffer_keeps_its_verdict():
    receiver, clock = make(ordering="unordered", queue=2, drain=False)
    at(receiver, clock, 1, 0, 1)
    at(receiver, clock, 2, 2, 2)
    held = at(receiver, clock, 3, 1, 3)
    assert (held.verdict, held.delivered, held.diagnostic) == ("out-of-order", False, "queue-full")


def test_activation_is_the_deadline_anchor_not_a_regression_baseline():
    receiver, clock = make(deadline=5)
    clock.now = 10
    receiver.activate()
    assert at(receiver, clock, 8, 0, 8).verdict == "delivered"  # the data model compares to the previous reception only
    assert receiver.held_buffer() == 1
