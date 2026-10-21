"""DV05-N and DV06-N real-process gaps (increment19, finding 437).

Each stimulus meets the actual owned stack: a never-returning probe, one dropped Cancel delivery,
a never-returning collect, a never-returning cleanup operation and a Cancel during restart
quiescence. DV05-N requires an independent deadline, a fail-closed fence, no detached worker and an
unresolved result when containment cannot release; DV06-N requires no unintended target and no
release of a quiesced restart. SLACK is a harness allowance on a shared host, not a kernel guarantee.
"""
from dataclasses import replace
import signal
import threading
import time

import pytest

from xverse.maestro.owner import GateConnection
from xverse.maestro.persistence import PersistenceClient
from xverse.maestro.run_broker import RunUnitIssuer
from xverse.maestro.run_closure import RunClosure
from xverse.maestro.teardown import ReverseTeardown
from xverse.maestro.time import HostDeadline
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_bootstrap import boot_stack as boot_stack, supervisor_binary as supervisor_binary
from .test_boundary import environment as environment, native as native
from .test_launcher import binaries as binaries, deadline
from .test_owner import stack as stack
from .test_persistence import storage as storage
from .test_provider import runtime, second
from .test_releasegate import guard_binary as guard_binary
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_collection_runtime import configure, start_and_stop

SLACK = 0.5


def frozen(fd):
    import os
    with open(os.open("cgroup.events", os.O_RDONLY, dir_fd=fd), "rb") as events:
        return b"frozen 1" in events.read()


def test_never_returning_probe_returns_by_its_own_bound_without_a_detached_worker(boot_stack):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    b, lb, hb, gb = second(boot_stack, owner, original)
    facade.bind(lb, hb)
    assert facade.start(descriptor.unit_id, descriptor, gate, original).ready
    action = next(a for a in owner._unit(descriptor.unit_id).plan.actions if a.phase == "observe")
    bound = min(facade._policies[descriptor.unit_id].timeout_seconds, action.timeout_seconds)
    threads = set(threading.enumerate())
    signal.pidfd_send_signal(launcher._pidfd, signal.SIGSTOP)
    try:
        began = time.monotonic()
        with pytest.raises((ValueError, TimeoutError)) as raised:
            facade.start(b.unit_id, b, gb, original)
        elapsed = time.monotonic() - began
    finally:
        signal.pidfd_send_signal(launcher._pidfd, signal.SIGCONT)
    remaining = original.monotonic_seconds - began
    print("DV05-PROBE", dict(elapsed=elapsed, bound=bound, original_remaining=remaining, error=str(raised.value)))
    assert elapsed <= bound + SLACK
    assert elapsed < remaining
    assert set(threading.enumerate()) == threads
    assert boot_stack[2].cancelled
    assert not (boot_stack[4] / (owner._unit(b.unit_id).binding_id + ".marker")).exists()


def test_one_dropped_cancel_delivery_is_still_fenced(storage, native, guard_binary, monkeypatch):
    start, stage, config, manager, latch = storage
    owner, client, announce, release = start()
    unit_id = config.prepared.units[0].unit_id
    original = deadline(4)
    owner.commit_intent(unit_id, original)
    unit_id, descriptor, child, marker, gate = stage(owner, guard_binary, native)
    deliveries, armed = [], []
    cancel, exchange = GateConnection.cancel, GateConnection.exchange

    def drop_first(self, reason="owner-cancel"):
        deliveries.append((reason, time.monotonic(), not deliveries))
        if len(deliveries) == 1:
            return None  # this one Cancel never reaches the native guard
        return cancel(self, reason)

    def cancel_after_arm(self, packet, expected, until):
        reply = exchange(self, packet, expected, until)
        if self is gate and packet.kind == 3 and not armed:
            armed.append(time.monotonic())
            owner.cancel("dv05-dropped-cancel")
        return reply

    with monkeypatch.context() as patch:
        patch.setattr(GateConnection, "cancel", drop_first)
        patch.setattr(GateConnection, "exchange", cancel_after_arm)
        with pytest.raises(ValueError) as raised:
            owner.release(unit_id, descriptor, gate, original)
    assert armed and deliveries and deliveries[0][2] and latch.cancelled
    import select
    assert not select.select([marker], [], [], 0.05)[0]  # no workload instruction reached the child
    fd = manager._entries[descriptor.key].fd
    lease_end = gate.lease_ns / 1e9
    try:
        gate.process.wait(timeout=max(0.0, lease_end - time.monotonic()) + 0.5 + SLACK)
    except Exception:
        pass
    exited = gate.process.poll()
    print("DV05-CANCEL", dict(error=str(raised.value), deliveries=[(r, round(t - armed[0], 3), d) for r, t, d in deliveries],
                              guard_exit=exited, exited_before_lease=time.monotonic() < lease_end, frozen=frozen(fd)))
    assert exited == 0 and frozen(fd)
    assert not select.select([marker], [], [], 0)[0]
    assert manager.force_cleanup(descriptor).termination_observed
    assert child.wait(timeout=2) == 0


def test_never_returning_collect_is_bounded_and_retains_no_outcome(request, monkeypatch):
    configure(monkeypatch)
    stack = request.getfixturevalue("broker_stack")
    broker, facade, client, work = stack
    start_and_stop(stack)
    rpc, stopped = PersistenceClient._rpc, []

    def stall(self, kind, body, until, **kw):
        if kind == "collect" and not stopped:
            signal.pidfd_send_signal(self.process._capability.fileno(), signal.SIGSTOP)
            stopped.append(time.monotonic())
        return rpc(self, kind, body, until, **kw)

    until = deadline(2)
    with monkeypatch.context() as patch:
        patch.setattr(PersistenceClient, "_rpc", stall)
        with pytest.raises((ValueError, OSError)) as raised:
            client.collect_outputs(broker, until)
        returned = time.monotonic()
    print("DV05-COLLECT", dict(error=str(raised.value), late=returned - until.monotonic_seconds,
                               failure=client.rpc_failure and client.rpc_failure.diagnostic))
    assert stopped and returned <= until.monotonic_seconds + SLACK
    assert client._failed and client._collection_outcome is None
    count = client._sequence
    with pytest.raises(ValueError):
        client.collect_outputs(broker, deadline(1))
    assert client._sequence == count
    assert client.drain(deadline(1)).worker_reaped


def test_never_returning_cleanup_operation_is_bounded_and_containment_still_releases(request, monkeypatch):
    configure(monkeypatch)
    stack = request.getfixturevalue("broker_stack")
    broker, facade, client, work = stack
    until = stage_all(stack)
    for uid in client.prepared.resource_order:
        issuer = broker.issuer(uid)
        assert facade.start(uid, issuer.recipe.descriptor, broker.connection, until).ready
    markers_by = time.monotonic() + 0.5
    while not all((work / (u.binding_id + ".marker")).exists() for u in client.prepared.units):
        assert time.monotonic() < markers_by, "owned native workload did not produce its declared marker"
        time.sleep(0.005)
    retire, stopped = RunUnitIssuer.retire_owned, []
    authority = broker.connection.child

    def stall(self, handle, end):
        if not stopped:
            signal.pidfd_send_signal(authority._capability.fileno(), signal.SIGSTOP)
            stopped.append((self.unit_id, time.monotonic()))
        return retire(self, handle, end)

    monkeypatch.setattr(RunUnitIssuer, "retire_owned", stall)
    end = deadline(3)
    cleanup = error = None
    try:
        cleanup = ReverseTeardown(facade, per_unit_seconds=0.8).run(end)
    except (ValueError, OSError) as exc:
        error = str(exc)
    returned = time.monotonic()
    closure = RunClosure(broker.session).close(deadline(6))
    print("DV05-CLEANUP", dict(error=error, late=returned - end.monotonic_seconds, stopped=stopped,
                               units=cleanup and [(u.unit_id, u.unit_cleanup_complete, u.normal_records_complete,
                                                   u.emergency, u.diagnostic) for u in cleanup.units],
                               closure_complete=closure.cleanup_complete, diagnostics=closure.diagnostics))
    assert stopped and returned <= end.monotonic_seconds + SLACK
    assert cleanup is None or not cleanup.normal_records_complete
    assert closure.root_reaped and all(h.process_reaped for h in closure.helpers)
    assert all(b.empty and b.released for b in closure.boundaries)
    assert not closure.lifecycle_complete


@pytest.mark.parametrize("window", ["before-stop", "between-stop-and-cleanup"])
def test_cancel_during_restart_quiescence_never_releases_the_new_generation(request, monkeypatch, window):
    from .test_terminal_controller_inventory import scheduled
    from .test_lazy_dispatcher import run
    stack, controller, driver = scheduled(request, monkeypatch, restarts=True, restart_leaf_artifact=True)
    broker, facade, client, work = stack
    source, leaf = driver.prepared.resource_order
    context = next(c for c in client._future_contexts if c.binding.unit_id == leaf)
    tickets, fired, quiescing = [], [], []
    statement = driver._statement

    def enqueue(kind, step, **kw):
        response = statement(kind, step, **kw)
        if kind == "step-complete" and step.step_id == "observe-sink" and not tickets:
            end = HostDeadline(client.session, driver._active_end)
            tickets.append(driver.restart(client.run_id, leaf, permit=context.binding.permit, generation=2, deadline=end))
        return response

    quiesce = driver._quiesce_restart_unit

    def observed_quiesce(ticket):
        quiescing.append(ticket)
        phase = driver.teardown.phase

        def cancelling(unit, name, until, *a, **kw):
            if window == "before-stop" and name == "stop" and not fired:
                fired.append(name)
                driver.cancel("dv06-restart-quiescence")
            result = phase(unit, name, until, *a, **kw)
            if window == "between-stop-and-cleanup" and name == "stop" and not fired:
                fired.append(name)
                driver.cancel("dv06-restart-quiescence")
            return result

        driver.teardown.phase = cancelling
        try:
            return quiesce(ticket)
        finally:
            driver.teardown.phase = phase

    monkeypatch.setattr(driver, "_statement", enqueue)
    monkeypatch.setattr(driver, "_quiesce_restart_unit", observed_quiesce)
    result = run(driver)
    outcome = driver.restart_result(tickets[0]) if tickets else None
    records = FileEvidenceJournal(work.parent / "m3.jsonl").records
    consumed = FileEvidenceJournal(work.parent / "m3.jsonl").permit_consumed(context.binding.permit.permit_id,
                                                                             context.binding.permit.nonce)
    closed = RunClosure(broker.session, dispatcher=driver).close(deadline(6))
    print("DV06-QUIESCE", window, dict(fired=fired, outcome=outcome, diagnostic=result.diagnostic,
                                       generations=sorted({r.details["generation"] for r in records}),
                                       consumed=consumed, closure_complete=closed.cleanup_complete,
                                       diagnostics=closed.diagnostics))
    assert tickets and quiescing and fired == ["stop"]
    assert outcome is not None and outcome.disposition != "completed"
    assert not result.execution_succeeded and broker.owner.latch.cancelled
    assert {r.details["generation"] for r in records} == {1}
    assert not consumed and not driver._teardown_history
    assert closed.root_reaped and all(h.process_reaped for h in closed.helpers)
    assert all(b.empty and b.released for b in closed.boundaries)
    assert closed.cleanup_complete, closed
    assert not closed.lifecycle_complete


def test_no_product_path_signals_or_waits_by_a_reusable_pid_number():
    """DV06-N PID reuse (finding 437): identity is pidfd/cgroup-based, so a recycled number has no target.

    Static guard: no Python or native product source signals by PID number; the only native waitpid
    calls target the caller's own unreaped direct child, whose number the kernel keeps reserved until
    that wait reaps it.
    """
    import re
    from importlib.resources import files
    root = files("xverse.maestro")
    python = {p.name: p.read_text() for p in root.iterdir() if p.name.endswith(".py")}
    native = {p.name: p.read_text() for p in root.joinpath("native").iterdir() if p.name.endswith(".c")}
    assert python and native
    assert not [n for n, s in python.items() if re.search(r"\bos\.(kill|killpg)\(", s)]
    assert not [n for n, s in native.items() if re.search(r"\b(kill|killpg|tkill|tgkill)\(|SYS_(t?g?kill|tkill)\b", s)]
    waits = {n: re.findall(r"waitpid\(([^,]+),", s) for n, s in native.items()}
    assert {n: w for n, w in waits.items() if w} == {"run_authority.c": ["e->pid"], "catalog_launcher.c": ["g->child"]}
