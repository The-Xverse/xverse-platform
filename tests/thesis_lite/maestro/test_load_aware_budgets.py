"""Seeded controls for load-aware interior budgets (ADR-ML3-BUDGET-0001, finding 477).

The per-run estimator is seeded the way test_candidate_guards_and_f10_limits.py seeds the v2 guard:
a seeded estimate stands for earlier slow spans of that kind in the same run, so each sizing or
decision path runs in every execution. On the head without this change the seeds have nowhere to
go and each control fails at its first assertion about the new behaviour. Worker-side code is
involved: run with one installed version (finding 442).
"""
import random
import time

import pytest

from xverse.maestro.persistence import PersistenceClient
from xverse.maestro.terminal_runtime import finalizable
from .test_terminal_runtime import scheduled, run, verify
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries


def seed(driver, **spans):
    """On the head without the estimator the seed has nowhere to go; the stimulus is unchanged."""
    times = getattr(driver, "_times", None)
    for kind, seconds in spans.items():
        if times is not None:
            times.seen[kind.replace("_", ":", 1)] = seconds


def teardowns(driver):
    return (*driver._teardown_history, driver.teardown)


def spy_phase_deadlines(monkeypatch, driver):
    from xverse.maestro.teardown import ReverseTeardown
    phase, seen = ReverseTeardown.phase, []

    def recording(self, unit, name, deadline):
        seen.append((name, deadline.monotonic_seconds, driver._active_end, driver._work_end, self._terminal_scope()))
        return phase(self, unit, name, deadline)

    monkeypatch.setattr(ReverseTeardown, "phase", recording)
    return seen


def test_sizing_helpers_keep_todays_deadline_whenever_the_need_fits():
    """(e) Pure identity and bounds of the sizing functions."""
    from xverse.maestro.service_time import NORMAL_SHARE, sized
    from xverse.maestro.teardown import ReverseTeardown
    holder = type("Holder", (), {"_interior_trace": []})()
    rng = random.Random(477)
    for _ in range(2000):
        now, window = rng.uniform(0, 100), rng.uniform(0.01, 5)
        base = now + window
        cap = now + rng.uniform(0, 20)
        need = rng.uniform(0, 3 * window)
        value = sized(base, now, need, window, cap)
        if need <= NORMAL_SHARE * window:
            assert value == base
        else:
            assert base <= value <= max(base, cap)
        began, end0 = now, now + window
        normal, end = ReverseTeardown._split(holder, began, end0, max(end0, cap), need, "unit", "u")
        if need <= NORMAL_SHARE * window:
            assert normal == began + NORMAL_SHARE * (end0 - began) and end == end0  # exact (finding 480 (7))
        else:
            assert normal >= began + NORMAL_SHARE * window - 1e-9 and end >= end0
            assert end <= max(end0, min(max(end0, cap), began + 5)) + 1e-9  # per-request bound (owner)
            assert end - normal >= (1 - NORMAL_SHARE) * window - 1e-9  # the emergency share is kept


def test_slow_teardown_records_never_end_on_the_emergency_path(request, monkeypatch):
    """(a) Each teardown record takes 0.15 s longer and an earlier slow phase is known. Where the
    lease-renewal margin leaves an active-phase stop too little room, M1 refuses it before the
    dispatch and the terminal teardown, sized within its own slack, cleans every unit normally:
    no emergency, a finalizable documented failure or a success, a usable channel. The head
    without this change ends on the emergency path (ML-SCHEDULE-TEARDOWN-INCOMPLETE)."""
    stack, _, driver = scheduled(request, monkeypatch)
    client = stack[2]
    seed(driver, phase_stop=0.45, phase_cleanup=0.45)
    record = PersistenceClient.record_teardown

    def slow(self, controller, step, deadline):
        time.sleep(0.15)
        return record(self, controller, step, deadline)

    monkeypatch.setattr(PersistenceClient, "record_teardown", slow)
    deadlines = spy_phase_deadlines(monkeypatch, driver)
    result = run(driver)
    trace = [e for t in teardowns(driver) for e in getattr(t, "_interior_trace", ())]
    print("BUDGET-A", dict(diagnostic=result.diagnostic, interior=getattr(driver, "_interior_trace", None), teardown=trace))
    assert result.diagnostic == "ML-SCHEDULE-SERVICE-DEADLINE", result.diagnostic  # pinned (finding 480 (7))
    assert not client._failed and client.rpc_failure is None and result.terminal_recorded
    assert result.cleanup.unit_cleanup_complete and result.cleanup.normal_records_complete, result.cleanup
    assert not any(getattr(t, "_emergencies", None) for t in teardowns(driver))
    assert finalizable(result.terminal.public_data()["report"])
    assert any("widened" in e for e in driver._interior_trace + trace), (driver._interior_trace, trace)
    assert [e["site"] for e in driver._interior_trace if e.get("stopped")] == ["step-dispatch"]
    assert all(end <= active_end for _, end, active_end, _, terminal in deadlines if not terminal)
    assert all(e["end"] - e["normal"] >= 0.4 * e["window"] - 1e-9 for e in trace), trace


def test_a_stop_that_no_longer_fits_is_refused_and_the_run_ends_as_a_documented_failure(request, monkeypatch):
    """(b), (f) M1: the stop step is never dispatched; normal terminal teardown and the whole
    terminal sequence still fit, so the report is finalizable and the channel usable."""
    stack, _, driver = scheduled(request, monkeypatch)
    client = stack[2]
    seed(driver, phase_stop=3600.0)
    result = run(driver)
    facts = result.terminal.public_data()
    print("BUDGET-B", dict(diagnostic=result.diagnostic, trace=getattr(driver, "_interior_trace", None),
                           outcomes={k: v.disposition for k, v in driver._outcomes.items()}))
    assert result.diagnostic == "ML-SCHEDULE-SERVICE-DEADLINE" and not result.execution_succeeded
    assert [e["site"] for e in driver._interior_trace if e.get("stopped")] == ["step-dispatch"]
    assert all(driver._outcomes[s.step_id].disposition == "blocked"
               for s in driver.prepared.steps if s.phase in ("stop", "cleanup"))  # never dispatched
    assert not client._failed and client.rpc_failure is None and result.terminal_recorded
    assert result.cleanup.unit_cleanup_complete and result.cleanup.normal_records_complete, result.cleanup
    assert facts["report"]["blockers"] == ["terminal-outcome"] and finalizable(facts["report"]), facts["report"]
    assert facts["writer"]["finalize_completed"] and verify(client, stack[3].parent / "argus").complete


def test_a_restart_that_cannot_finish_is_rejected_before_any_mutation(request, monkeypatch):
    """(c) M1 before restart mutation: rejected with the existing code; the generation is unchanged
    and the run continues."""
    from xverse.maestro.time import HostDeadline
    from .test_terminal_controller_inventory import scheduled as restart_scheduled
    stack, controller, driver = restart_scheduled(request, monkeypatch, restarts=True, restart_leaf_artifact=True)
    broker, facade, client, work = stack
    source, leaf = driver.prepared.resource_order
    context = next(c for c in client._future_contexts if c.binding.unit_id == leaf)
    seed(driver, restart_unit=3600.0)
    tickets, statement = [], driver._statement

    def enqueue(kind, step, **kw):
        response = statement(kind, step, **kw)
        if kind == "step-complete" and step.step_id == "observe-sink" and not tickets:
            end = HostDeadline(client.session, driver._active_end)
            tickets.append(driver.restart(client.run_id, leaf, permit=context.binding.permit, generation=2, deadline=end))
        return response

    monkeypatch.setattr(driver, "_statement", enqueue)
    result = run(driver)
    outcome = driver.restart_result(tickets[0]) if tickets else None
    print("BUDGET-C", dict(outcome=outcome, diagnostic=result.diagnostic, trace=getattr(driver, "_interior_trace", None)))
    assert outcome is not None and outcome.disposition == "rejected", outcome
    assert outcome.diagnostic == "ML-SCHEDULE-RESTART-DEADLINE" and outcome.execution_id is None
    assert [e["site"] for e in driver._interior_trace if e.get("stopped")] == ["restart"]
    assert driver._generation(leaf) == 1 and not driver._teardown_history
    assert not client._failed and client.rpc_failure is None


def test_widened_deadlines_stay_inside_every_outer_bound(request, monkeypatch):
    """(d) Seeded phase estimates widen the active phases; every deadline stays at or below the
    active end, health scans and renewals still happen, and no lease is exhausted."""
    stack, _, driver = scheduled(request, monkeypatch)
    client = stack[2]
    seed(driver, phase_stop=0.25, phase_cleanup=0.25)  # sized beyond 0.6 x 0.5 s, still fits (M1 passes)
    deadlines = spy_phase_deadlines(monkeypatch, driver)
    result = run(driver)
    print("BUDGET-D", dict(diagnostic=result.diagnostic, trace=getattr(driver, "_interior_trace", None),
                           scans=driver.health_scans, renewals=driver.lease_renewals))
    assert result.execution_succeeded and result.diagnostic is None, result.diagnostic
    assert any("widened" in e for e in driver._interior_trace)
    active = [d for d in deadlines if not d[4]]
    assert active and all(end <= active_end for _, end, active_end, _, _ in active)
    assert all(end <= work_end for _, end, _, work_end, _ in deadlines)
    assert not any(e.get("stopped") for e in driver._interior_trace)
    assert driver.lease_renewals >= 1  # renewals still happen (finding 480 (7))
    assert not client._failed and client.rpc_failure is None


def fake_terminal(now, *, units=6, per_unit=1.0, work_slack=300.0, lease_in=1e6, need=3600.0, lazy=False,
                  teardown_in=1e6):
    """A dispatcher stand-in for _run_end: only the fields the terminal sizing reads."""
    from types import SimpleNamespace as N
    from xverse.maestro.dispatcher import FiniteDispatcher
    teardown = N(_order=lambda: [f"u{i}" for i in range(units)], _cleaned={}, _stopped=set(),
                 _need=lambda unit, phase: need,
                 manager=N(_admission=N(teardown_deadline=N(monotonic_seconds=now + teardown_in))))
    fake = N(teardown=teardown, _work_end=now + work_slack, prepared=N(units=[None] * units),
             plan=N(per_unit_seconds=per_unit, operation_seconds=0.5, health_scan_seconds=0.15,
                    use_action_timeouts=False),
             _service_calls=3, bootstrap=N(_lease=(now + lease_in) * 1e9), gates={}, _lazy=lazy,
             facade=N(next_health_deadline=None), _interior_trace=[], _post_reserve=lambda: 2.0)
    fake._trace = lambda *a, **k: FiniteDispatcher._trace(fake, *a, **k)
    fake._sized = lambda *a, **k: FiniteDispatcher._sized(fake, *a, **k)
    return FiniteDispatcher._run_end, fake


def test_terminal_teardown_widening_respects_the_80_s_run_bound_and_live_leases():
    """(h) Finding 480 (1), (3): with 300 s of terminal slack and a large seeded estimate, the
    terminal window never exceeds teardown._deadline's 80 s nor a live lease minus the renewal
    margin; it is never below today's n x per-unit window. The 479 candidate returned about
    now + 298 s here, which run() rejects (ML-TEARDOWN-DEADLINE), losing the terminal teardown."""
    now = time.monotonic()
    run_end, fake = fake_terminal(now)
    value = run_end(fake)
    assert now + 6.0 <= value <= time.monotonic() + 79.0, value - now
    run_end, fake = fake_terminal(now, lease_in=30.0)  # non-lazy: nothing renews inside run()
    value = run_end(fake)
    assert now + 6.0 <= value <= now + 30.0, value - now
    run_end, fake = fake_terminal(now, lease_in=4.0, lazy=True)  # lazy: the records renew the lease
    value = run_end(fake)
    assert now + 6.0 < value <= time.monotonic() + 79.0, value - now
    run_end, fake = fake_terminal(now, teardown_in=40.0)  # the boundary teardown deadline caps it
    value = run_end(fake)
    assert now + 6.0 <= value <= now + 40.0, value - now
    run_end, fake = fake_terminal(now, need=0.1)  # the need fits: today's window exactly
    before = time.monotonic(); value = run_end(fake); after = time.monotonic()
    assert before + 6.0 <= value <= after + 6.0


def test_estimator_rejects_non_finite_or_negative_values():
    """Finding 480 (6): no NaN or negative estimate can reach a sizing or decision."""
    from xverse.maestro.service_time import ServiceTimes
    times = ServiceTimes()
    for bad in (float("nan"), float("inf"), -1.0, "1"):
        with pytest.raises(ValueError, match="finite number"):
            times.seed("phase:stop", bad)
        times.observe("phase:stop", bad)
    assert times.est("phase:stop") == 0.0
    times.seen["phase:stop"] = times.seen["tick"] = float("nan")  # written around the API
    assert times.est("phase:stop") == 0.0 and times.statement_max(0.5) == 0.0
    times.observe("tick", 0.2)
    assert times.statement_max(0.5) == 0.2 and times.statement_max(0.1) == 0.1


def test_a_refused_teardown_record_keeps_its_code_in_the_unit_result(request, monkeypatch):
    """(g) Finding 474 item 3: ML-TEARDOWN-RECORD-BUDGET is visible in UnitTeardown."""
    stack, _, driver = scheduled(request, monkeypatch)
    driver.teardown._record_seen = 3600.0
    result = run(driver)
    emergencies = {u: r.diagnostic for t in teardowns(driver) for u, r in getattr(t, "_emergencies", {}).items()}
    print("BUDGET-G", dict(diagnostic=result.diagnostic, emergencies=emergencies))
    assert not result.execution_succeeded
    assert emergencies and "ML-TEARDOWN-RECORD-BUDGET" in emergencies.values(), emergencies
