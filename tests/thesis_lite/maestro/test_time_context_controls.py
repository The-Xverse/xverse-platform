"""DV08 time-context controls (increment19, findings 414 and 417).

T1: a second simulation tick domain, or a non-simulation clock class, is rejected at preparation
with ML-TIME and zero effects. T2: a stalled real tick worker ends the run by its own terminal host
deadline. T3: a simulation held paused past the active end does not hold the run open; the host
deadline ends it while the tick is still 0. The 1.0 s return margin is a test-side tolerance for
the shared host (finding 417), not an admitted product bound.
"""

import time

import pytest

from xverse.maestro import PreparationError, prepare
from xverse.maestro.dispatcher import FiniteDispatcher
from .test_bootstrap import boot_stack as boot_stack, supervisor_binary as supervisor_binary
from .test_boundary import environment as environment, native as native
from .test_dispatcher import dispatcher, ends, full_stack
from .test_launcher import binaries as binaries, deadline
from .test_preparation import PIN, compiled, documents
from .test_preparation_rejections import effects as effects

RETURN_MARGIN_SECONDS = 1.0
AFTER_TICK_ZERO = {"observe-source", "observe-sink", "stop-sink", "cleanup-sink",
                   "stop-source", "cleanup-source"}
SECOND = {"clockClass": "simulation", "epoch": "0", "id": "second-time", "monotonic": True,
          "rate": "1"}


def second_unused(docs):
    docs["system.json"]["spec"]["timeDomains"].append(dict(SECOND))


def second_used(docs):
    second_unused(docs)
    docs["scenario.json"]["spec"]["steps"][1]["timeDomainId"] = "second-time"
    docs["scenario.json"]["spec"]["timeMappings"] = [{
        "sourceTimeDomainId": "experiment-time", "targetTimeDomainId": "second-time",
        "mapping": "declared identity mapping", "tolerance": {"value": 0, "unit": "tick"}}]


def logical_only(docs):
    docs["system.json"]["spec"]["timeDomains"][0]["clockClass"] = "logical"


@pytest.mark.parametrize("change", [second_unused, second_used, logical_only],
                         ids=["second-simulation-domain-unused", "second-simulation-domain-used",
                              "single-logical-domain"])
def test_unadmitted_time_domains_reject_whole_and_effect_free(change, effects, monkeypatch):
    docs = documents()
    change(docs)
    result, resources = compiled(docs)
    assert [d["clockClass"] for d in result.plan["timeDomains"]] != ["simulation"]
    attempts, arm = effects
    with monkeypatch.context() as m:
        arm(m)
        with pytest.raises(PreparationError) as raised:
            prepare(result, resources, provider_descriptors=(PIN,))
    assert attempts == []
    assert raised.value.code == "ML-TIME", str(raised.value)


def bounded_run(driver):
    active, terminal = ends(driver)
    result = driver.run(active, terminal)
    returned = time.monotonic()
    late = returned - terminal.monotonic_seconds
    assert late <= RETURN_MARGIN_SECONDS, dict(late_seconds=late, terminal=terminal.monotonic_seconds)
    print(f"return relative to terminal deadline: {late:+.3f} s")
    return result, late


def test_stalled_tick_worker_returns_by_its_terminal_deadline(request, monkeypatch):
    import signal

    stack = full_stack(request, monkeypatch)
    driver = dispatcher(stack)
    send = FiniteDispatcher._send

    def stopped(self, kind, until, **values):
        reply = send(self, kind, until, **values)
        if kind == "begin":
            signal.pidfd_send_signal(self.client._pidfd, signal.SIGSTOP)
        return reply

    monkeypatch.setattr(FiniteDispatcher, "_send", stopped)
    result, _ = bounded_run(driver)
    assert not result.execution_succeeded and result.cleanup.unit_cleanup_complete
    assert driver.client._failed and driver.client.drain(deadline(1)).worker_reaped
    assert not list(stack[4].glob("*.marker"))


def test_paused_simulation_does_not_hold_the_run_past_its_host_deadline(request, monkeypatch):
    stack = full_stack(request, monkeypatch, pauses=400, request_limit=2048)
    driver = dispatcher(stack)
    result, late = bounded_run(driver)
    assert not result.execution_succeeded, "the simulation advanced before the active end (finding 417)"
    late_steps = [s for s in result.steps if s.step_id in AFTER_TICK_ZERO]
    assert late_steps and all(s.disposition != "completed" for s in late_steps), result.steps
    assert all(s.completion_tick in (None, 0) for s in result.steps), result.steps
    assert result.cleanup.unit_cleanup_complete
    client = driver.client
    print("T3-VARIANT", result.diagnostic, dict(failed=client._failed, terminal_recorded=result.terminal_recorded,
                                                late_seconds=round(late, 3)))
    if result.diagnostic == "ML-SCHEDULE-SERVICE-DEADLINE":
        # Clean end: the active-end check fired between RPCs; the terminal record is durable.
        assert result.terminal_recorded and not client._failed and not client._aborted
    else:
        # F-08 (finding 418): an RPC sent at the active end with less budget than its service
        # time fails the persistence channel; the run still ends fail-closed, without a terminal
        # record and without fabricated facts. Tighten to the clean branch once F-08 is repaired.
        assert result.diagnostic in ("ML-PERSIST-TIMEOUT", "ML-PERSIST-SENDER"), result.diagnostic
        assert client._failed and not result.terminal_recorded
        assert client.drain(deadline(1)).worker_reaped
