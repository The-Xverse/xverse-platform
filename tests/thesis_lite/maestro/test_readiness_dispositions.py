"""DV04-N on the real owned dispatcher stack (increment19, finding 431).

The prerequisite (source) is ready; before the dependent (sink) is released it dies, its issuer
stalls, or it dies right after the sink gate's ARM. The dependent must stay blocked, its start step
must not be completed, teardown must run, and the run must not succeed: the observations of DV04-N
asserted together rather than separately.
"""
from dataclasses import replace
import signal
import time

import pytest

from xverse.maestro.dispatcher import FiniteDispatcher
from xverse.maestro.owner import GateConnection
from .test_bootstrap import boot_stack as boot_stack, supervisor_binary as supervisor_binary
from .test_boundary import environment as environment, native as native
from .test_dispatcher import dispatcher, ends, full_stack
from .test_launcher import binaries as binaries
from .test_preparation import SINK, SOURCE

AFTER_START_SINK = {"observe-source", "observe-sink", "stop-sink", "cleanup-sink", "stop-source", "cleanup-source"}


def launcher_of(driver, unit):
    return next(binding.launcher for u, binding in driver._bindings if u == unit)


@pytest.mark.parametrize("mode", ["dead", "unknown-health", "final-guard", "stale-reply"])
def test_lost_prerequisite_blocks_dependent_start_and_tears_down(request, monkeypatch, mode):
    stack = full_stack(request, monkeypatch)
    driver = dispatcher(stack)
    source = launcher_of(driver, SOURCE)
    fired = []
    if mode == "stale-reply":
        # DV04 n1 (finding 450): the source's replies are older than its freshness during start-sink.
        observe, freshness = type(source).observe, driver.facade._policies[SOURCE].freshness_seconds
        deciding = []

        def stale(self, handle, until):
            value = observe(self, handle, until)
            if self is source and deciding:
                fired.append(time.monotonic())
                return replace(value, observed_at=time.monotonic() - freshness - 1)
            return value

        effect = FiniteDispatcher._effect

        def deciding_sink(self, step):
            if step.step_id == "start-sink":
                deciding.append(True)
            try:
                return effect(self, step)
            finally:
                deciding.clear()

        monkeypatch.setattr(type(source), "observe", stale)
        monkeypatch.setattr(FiniteDispatcher, "_effect", deciding_sink)
    elif mode in ("dead", "unknown-health"):
        effect = FiniteDispatcher._effect

        def before_sink(self, step):
            if step.step_id == "start-sink" and not fired:
                fired.append(time.monotonic())
                if mode == "dead":
                    signal.pidfd_send_signal(source._childfd, signal.SIGKILL)
                else:
                    signal.pidfd_send_signal(source._pidfd, signal.SIGSTOP)
            try:
                return effect(self, step)
            finally:
                # The issuer stall covers only the dependent's readiness decision (finding 431).
                if mode == "unknown-health" and step.step_id == "start-sink" and fired:
                    signal.pidfd_send_signal(source._pidfd, signal.SIGCONT)

        monkeypatch.setattr(FiniteDispatcher, "_effect", before_sink)
    else:
        exchange = GateConnection.exchange
        sink_gate = dict(driver.gates)[SINK]

        def lose_after_arm(self, packet, expected, until):
            reply = exchange(self, packet, expected, until)
            if self is sink_gate and packet.kind == 3 and not fired:
                fired.append(time.monotonic())
                signal.pidfd_send_signal(source._childfd, signal.SIGKILL)
            return reply

        monkeypatch.setattr(GateConnection, "exchange", lose_after_arm)
    active, terminal = ends(driver)
    result = driver.run(active, terminal)
    returned = time.monotonic()
    dispositions = {s.step_id: s.disposition for s in result.steps}
    print("DV04", mode, dict(fired=bool(fired), diagnostic=result.diagnostic, dispositions=dispositions,
                             markers=sorted(p.name for p in stack[4].glob("*.marker"))))
    assert fired, "stimulus never applied"
    assert not result.execution_succeeded
    assert dispositions["start-sink"] != "completed", dispositions
    assert all(dispositions[s] != "completed" for s in AFTER_START_SINK if s in dispositions), dispositions
    assert not (stack[4] / "sink-binding.marker").exists()
    assert result.cleanup.unit_cleanup_complete, result.cleanup
    assert returned <= terminal.monotonic_seconds
