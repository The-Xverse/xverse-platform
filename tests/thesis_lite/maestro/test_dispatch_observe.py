"""Exact declared observation scope over actual two-unit native ownership."""

import pytest
from xverse.maestro.dispatcher import FiniteDispatcher
from xverse.maestro.providers import ProcessReadiness
from .test_dispatcher import full_stack, dispatcher, ends
from .test_recovery import started
from .test_launcher import deadline, binaries as binaries
from .test_bootstrap import (
    boot_stack as boot_stack,
    supervisor_binary as supervisor_binary,
)
from .test_boundary import environment as environment, native as native


def test_scheduled_observe_queries_only_its_declared_original_unit(request, monkeypatch):
    stack = full_stack(request, monkeypatch)
    driver = dispatcher(stack)
    active = [None]
    observed = []
    effect = FiniteDispatcher._effect
    query = ProcessReadiness._query

    def counted(self, unit, until):
        if active[0] is not None:
            observed.append((active[0], unit))
        return query(self, unit, until)

    def scoped(self, step):
        active[0] = step.unit_id if step.phase == "observe" else None
        try:
            return effect(self, step)
        finally:
            active[0] = None

    monkeypatch.setattr(ProcessReadiness, "_query", counted)
    monkeypatch.setattr(FiniteDispatcher, "_effect", scoped)
    result = driver.run(*ends(driver))
    expected = [(s.unit_id, s.unit_id) for s in driver.prepared.steps if s.phase == "observe"]
    assert observed == expected
    assert result.execution_succeeded, result


def test_targeted_health_input_and_lock_conflicts_preserve_original_readiness(boot_stack):
    facade, owner, unit, launcher, handle, gate, original = started(boot_stack, two=True)
    before = facade.observations
    sequence = owner.persistence._sequence
    for unknown in (True, "undeclared-unit"):
        with pytest.raises(ValueError):
            facade.check_unit_health(unknown, deadline())
    facade._lock.acquire()
    try:
        with pytest.raises(ValueError):
            facade.check_unit_health(unit.unit_id, deadline())
    finally:
        facade._lock.release()
    assert facade.observations == before
    assert owner.persistence._sequence == sequence and not owner.latch.cancelled
    sample = facade.check_unit_health(unit.unit_id, deadline())
    assert sample.ready and sample.unit_id == unit.unit_id
    assert sample.sequence > before[0].sequence
