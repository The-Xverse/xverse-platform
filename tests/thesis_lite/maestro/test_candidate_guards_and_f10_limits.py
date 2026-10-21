"""Targeted controls for the increment-19 product candidates (finding 463, after review 462).

F-08/F-09 v2: the guards are driven deterministically by seeding the per-run estimate the guard
keeps (a stimulus standing for an earlier slow round trip of that kind), so the refusal paths run
in every execution rather than by chance at the T3 active end. F-10: the limits of the relaxation
are checked by mutating the recorded lost observation as the assessor reads it; each mutation must
make the event conflicting. Worker-side code is involved: run with one installed version (442).
"""
import pytest

from xverse.maestro.dispatcher import FiniteDispatcher
from xverse.maestro.teardown import ReverseTeardown
from xverse.maestro.terminal_runtime import finalizable
from .test_terminal_runtime import scheduled, run, verify
from .test_dv09_native_failed_lifecycle import failed_run
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries


def observe(monkeypatch, cls, name, code):
    """Record every call of cls.name that raised `code`, with no change to its behaviour."""
    original, raised = getattr(cls, name), []

    def wrapper(self, *args, **kwargs):
        try:
            return original(self, *args, **kwargs)
        except Exception as error:
            if str(error) == code:
                raised.append(args[0] if args else None)
            raise

    monkeypatch.setattr(cls, name, wrapper)
    return raised


def test_f08_refuses_a_statement_below_its_observed_round_trip_and_keeps_the_terminal(request, monkeypatch):
    stack, _, driver = scheduled(request, monkeypatch)
    client = stack[2]
    driver._service_seen["tick-complete"] = 3600.0  # an earlier tick-complete took longer than any window
    refused = observe(monkeypatch, FiniteDispatcher, "_send", "ML-SCHEDULE-SERVICE-DEADLINE")
    sent, schedule_call = [], type(client).schedule_call

    def counting(self, dispatcher, statement, deadline):
        sent.append(statement)
        return schedule_call(self, dispatcher, statement, deadline)

    monkeypatch.setattr(type(client), "schedule_call", counting)
    result = run(driver)
    print("F08-TARGETED", dict(diagnostic=result.diagnostic, refused=refused, terminal=result.terminal_recorded,
                               failed=client._failed, sent=len(sent)))
    assert refused and refused[0] == "tick-complete"
    assert not any(b"\"kind\":\"tick-complete\"" in s.request_bytes for s in sent)  # refused before any send
    assert result.diagnostic == "ML-SCHEDULE-SERVICE-DEADLINE" and not result.execution_succeeded
    assert result.terminal_recorded and not client._failed and client.rpc_failure is None
    assert result.cleanup.unit_cleanup_complete
    # Findings 474 item 7, 475: a refused statement ends the run on the normal teardown path with
    # every lifecycle obligation recorded (ticks are not coverage obligations), so the run is a
    # documented failure: C1 finalizes it, offline evidence is complete, execution still failed.
    facts = result.terminal.public_data()
    assert facts["report"]["blockers"] == ["terminal-outcome"] and finalizable(facts["report"]), facts["report"]
    assert facts["writer"]["finalize_completed"] and not facts["writer"]["abort_attempted"], facts["writer"]
    assert verify(client, stack[3].parent / "argus").complete and not result.execution_succeeded


def test_f09_refuses_a_teardown_record_and_takes_the_emergency_path_with_a_usable_channel(request, monkeypatch):
    stack, _, driver = scheduled(request, monkeypatch)
    client = stack[2]
    driver.teardown._record_seen = 3600.0  # an earlier teardown record took longer than any phase window
    refused = observe(monkeypatch, ReverseTeardown, "_record", "ML-TEARDOWN-RECORD-BUDGET")
    result = run(driver)
    teardowns = (*driver._teardown_history, driver.teardown)
    handled = {u: (r.unit_cleanup_complete, r.normal_records_complete, r.emergency, r.diagnostic)
               for t in teardowns for u, r in {**t._stop_results, **t._cleaned}.items()}
    from xverse.maestro.run_closure import RunClosure
    from .test_launcher import deadline
    closure = RunClosure(stack[0].session, dispatcher=driver).close(deadline(6))
    print("F09-TARGETED", dict(diagnostic=result.diagnostic, refused=refused, terminal=result.terminal_recorded,
                               failed=client._failed, rpc_failure=client.rpc_failure, final_cleanup=result.cleanup,
                               handled=handled, closure_complete=closure.cleanup_complete,
                               boundaries=[(b.empty, b.released) for b in closure.boundaries],
                               helpers=[h.process_reaped for h in closure.helpers], diagnostics=closure.diagnostics))
    assert refused, "the F-09 guard never refused"
    assert not result.execution_succeeded
    assert not client._failed and client.rpc_failure is None  # refused before any send: no timeout, channel usable
    assert closure.root_reaped and all(h.process_reaped for h in closure.helpers)
    assert closure.boundaries and all(b.empty and b.released for b in closure.boundaries)
    # After the refusal the run ends on the emergency path: the dispatcher's final TeardownResult
    # carries no units and RunClosure performs the physical cleanup with the units unresolved
    # (finding 465; the same contract as finding 426), never a fabricated normal cleanup.
    assert "ML-CLOSURE-UNIT-UNRESOLVED" in closure.diagnostics and not closure.lifecycle_complete
    assert not result.cleanup.units
    # Finding 474 item 7: whatever terminal facts exist, none is finalizable or finalized.
    facts = result.terminal.public_data() if result.terminal is not None else None
    print("F09-REPORT", facts and facts["report"], facts and facts["writer"])
    assert facts is None or facts["report"] is None or not finalizable(facts["report"]), facts
    assert facts is None or facts["writer"] is None or not facts["writer"]["finalize_attempted"], facts


@pytest.mark.parametrize("mutation", ["dependency-added", "foreign-handle", "outcome-failed"])
def test_f10_relaxation_admits_only_the_exact_lost_observation(request, monkeypatch, mutation):
    from xverse.maestro import coverage as coverage_module
    result, checked, facts, coverage, open_rows, invalid, leaf_events = failed_run(request, monkeypatch)
    assert not invalid  # the unmutated record is accepted (F-10)
    work, client = request.getfixturevalue("broker_stack")[3], request.getfixturevalue("broker_stack")[2]
    payload, mutated, rejected = coverage_module._payload, [], []

    def mutate(event, ad, **kw):
        p = payload(event, ad, **kw)
        if p is not None and p.get("action") == "health-loss" and p.get("outcome") == "unknown":
            p = dict(p)
            if mutation == "dependency-added":
                p["dependencies"] = [dict(unitId=p["unitId"], generation=1, probeEventId=event["eventId"])]
            elif mutation == "foreign-handle":
                p["handleRef"] = "handle-" + "0" * 64
            else:
                p["outcome"] = "failed"
            mutated.append(event["eventId"])
        return p

    assess = coverage_module._Assessment.assess

    def observed(self):
        value = assess(self)
        rejected.extend(eid for eid in mutated if self.valid.get(eid) != "satisfied")
        return value

    with monkeypatch.context() as patch:
        patch.setattr(coverage_module, "_payload", mutate)
        patch.setattr(coverage_module._Assessment, "assess", observed)
        verify(client, work.parent / "argus")
    print("F10-LIMIT", mutation, dict(mutated=len(mutated), rejected=len(rejected)))
    assert mutated and set(rejected) == set(mutated), (mutated, rejected)
