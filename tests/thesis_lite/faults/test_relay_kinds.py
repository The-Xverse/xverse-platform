"""Phase 6 amendment A1 at relay level: duplicate, reorder, release outbox and held count."""

from __future__ import annotations

from xverse.faults import resolve_schedule
from xverse.faults.boundary import MessageRelayBoundary

from .support import PLANNED_TICKS, compiled_plan, fault, parameter


def _armed(kind, params):
    entry = resolve_schedule(compiled_plan([fault("f-x", kind, "sample-flow", at=2, duration=4, parameters=params)]), PLANNED_TICKS)[0]
    relay = MessageRelayBoundary("sample-flow", seed=3)
    handle = relay.arm("run-1", entry)
    assert relay.apply(handle, 2, dict(entry.parameters.values, _kind=kind)).ok
    return relay, handle


def test_duplicate_delivers_n_plus_one_copies_at_the_same_tick():
    relay, handle = _armed("duplicate", [parameter("copies", 2)])
    assert relay.submit("a", 2) == ["a", "a", "a"]
    assert relay.clear(handle, 4).ok and relay.submit("b", 4) == ["b"] and relay.take_outbox() == []


def test_reorder_releases_full_blocks_reversed_and_partial_blocks_through_the_outbox():
    relay, handle = _armed("reorder", [parameter("window", 2)])
    assert relay.submit(1, 2) == [] and relay.submit(2, 2) == [] and relay.held_count() == 2
    assert relay.submit(3, 4) == [3, 2, 1] and relay.held_count() == 0
    assert relay.submit(4, 4) == [] and relay.submit(5, 4) == []
    assert relay.clear(handle, 6).ok
    assert relay.take_outbox() == [5, 4] and relay.take_outbox() == [] and relay.held_count() == 0


def test_delay_clear_also_feeds_the_outbox():
    relay, handle = _armed("delay", [parameter("delay-ticks", 10)])
    assert relay.submit("x", 2) == [] and relay.held_count() == 1
    assert relay.clear(handle, 4).ok and relay.take_outbox() == ["x"] and relay.held_count() == 0


def test_release_keeps_held_items_counted():
    relay, handle = _armed("reorder", [parameter("window", 3)])
    relay.submit(1, 2)
    relay.release(handle)
    assert relay.held_count() == 1 and relay.take_outbox() == []
