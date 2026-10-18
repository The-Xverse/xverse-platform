"""Real original-child readiness: expectations frozen in provider-expected.json."""

from dataclasses import replace
import copy
import signal
import time

import pytest

from xverse.maestro.providers import ProbePolicy, ProcessReadiness
from xverse.maestro.launcher import CatalogLauncher, make_launch_recipe
from xverse.maestro.owner import GateConnection
from xverse.maestro.time import HostDeadline
from .test_bootstrap import (
    boot_stack as boot_stack,
    supervisor_binary as supervisor_binary,
)
from .test_boundary import environment as environment, native as native
from .test_owner import stack as stack
from .test_launcher import binaries as binaries


def runtime(stack, *, freshness=2.0):
    session, manager, latch, config, work, boundary, start, clients, owners = stack
    owner, storage, descriptor, launcher, handle, gate, original = start()
    policies = tuple(
        ProbePolicy(u.unit_id, freshness, min(0.5, freshness), 1.0)
        for u in config.prepared.units
    )
    facade = ProcessReadiness(owner, policies=policies)
    facade.bind(launcher, handle)
    return facade, owner, descriptor, launcher, handle, gate, original


def second(stack, owner, original):
    session, manager, latch, config, work, boundary, start, clients, owners = stack
    unit = config.prepared.units[1].unit_id
    owner.commit_intent(unit, original)
    descriptor = boundary("workload-two", unit)
    recipe = make_launch_recipe(
        owner,
        descriptor,
        environment={"MAESTRO_VISIBLE": "declared"},
        helper_artifact_digest=owner._unit(unit).provider.artifact_digest,
        deadline=original,
    )
    launcher = session.catalog(owner, recipe, boundary("launcher-two"), original)
    clients.append(launcher)
    handle = launcher.stage(original)
    gate = session.gate(
        owner,
        descriptor,
        boundary("gate-two"),
        original,
        lease_ns=min(session._lease, time.monotonic_ns() + 3_000_000_000),
    )
    clients.append(gate)
    return descriptor, launcher, handle, gate


def test_real_current_generation_probe_precedes_dependent_release(
    boot_stack, monkeypatch
):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    b, lb, hb, gb = second(boot_stack, owner, original)
    facade.bind(lb, hb)
    assert not facade.observations
    a = facade.start(descriptor.unit_id, descriptor, gate, original)
    assert a.ready and a.probe_id == "running" and a.generation == 1
    assert a.handle_digest and not a.ready_for_execution
    prior = a.sequence
    observed = facade.start(b.unit_id, b, gb, original)
    assert observed.ready
    assert facade.observation(descriptor.unit_id).sequence > prior
    assert facade.next_health_deadline.session == owner.session
    assert not facade.ready_for_execution
    # No parent process creation is needed for health queries.
    monkeypatch.setattr(
        "subprocess.Popen", lambda *a, **k: pytest.fail("unexpected Popen")
    )
    assert len(facade.check_health(original, force=True)) == 2
    assert all(o.ready for o in facade.observations)
    assert all(
        (boot_stack[4] / (u.binding_id + ".marker")).read_text() == "EXEC\n"
        for u in boot_stack[3].prepared.units
    )
    with pytest.raises(ValueError):
        facade.start(descriptor.unit_id, descriptor, gate, original)


@pytest.mark.parametrize("mode", ["unreleased", "dead", "issuer-loss", "final-guard"])
def test_failed_prerequisite_cannot_release_dependent(boot_stack, monkeypatch, mode):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    b, lb, hb, gb = second(boot_stack, owner, original)
    facade.bind(lb, hb)
    if mode != "unreleased":
        assert facade.start(descriptor.unit_id, descriptor, gate, original).ready
    if mode == "dead":
        signal.pidfd_send_signal(launcher._childfd, signal.SIGKILL)
        time.sleep(0.01)
    elif mode == "issuer-loss":
        # Use SIGSTOP, then cancellation/reaping through the original bootstrap.
        signal.pidfd_send_signal(launcher._pidfd, signal.SIGSTOP)
    elif mode == "final-guard":
        exchange = GateConnection.exchange

        def lose_after_arm(self, packet, expected, until):
            reply = exchange(self, packet, expected, until)
            if self is gb and packet.kind == 3:
                signal.pidfd_send_signal(launcher._childfd, signal.SIGKILL)
            return reply

        monkeypatch.setattr(GateConnection, "exchange", lose_after_arm)
    with pytest.raises((ValueError, TimeoutError)):
        facade.start(b.unit_id, b, gb, original)
    assert boot_stack[2].cancelled
    assert not facade.observations or not any(o.ready for o in facade.observations)
    assert not (
        boot_stack[4] / (owner._unit(b.unit_id).binding_id + ".marker")
    ).exists()
    if mode == "issuer-loss":
        signal.pidfd_send_signal(launcher._pidfd, signal.SIGCONT)


@pytest.mark.parametrize(
    "mode", ["forged-handle", "wrong-session", "copy", "registry", "lock", "expired"]
)
def test_exact_identity_and_deadline_rejections_before_dispatch(boot_stack, mode):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    if mode == "forged-handle":
        with pytest.raises(ValueError):
            facade.bind(launcher, replace(handle, execution_id="forged"))
    elif mode == "wrong-session":
        with pytest.raises(ValueError):
            facade.start(
                descriptor.unit_id,
                descriptor,
                gate,
                HostDeadline("foreign", original.monotonic_seconds),
            )
    elif mode == "copy":
        with pytest.raises(TypeError):
            copy.copy(facade).start(descriptor.unit_id, descriptor, gate, original)
    elif mode == "registry":
        old = facade._bindings
        facade._bindings = dict(old)
        with pytest.raises(ValueError):
            facade.start(descriptor.unit_id, descriptor, gate, original)
        facade._bindings = old
    elif mode == "lock":
        facade._lock.acquire()
        try:
            with pytest.raises(ValueError):
                facade.start(descriptor.unit_id, descriptor, gate, original)
            facade.cancel("test-conflict")
            assert boot_stack[2].cancelled
        finally:
            facade._lock.release()
    elif mode == "expired":
        with pytest.raises(ValueError):
            facade.start(
                descriptor.unit_id,
                descriptor,
                gate,
                HostDeadline(owner.session, time.monotonic() - 0.01),
            )
    assert not list(boot_stack[4].glob("*.marker"))


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), 0, -1, 6])
def test_invalid_policy_values(value):
    with pytest.raises(ValueError):
        ProbePolicy("unit", value, 0.1, 1)


@pytest.mark.parametrize("mode", ["missing", "duplicate", "unknown", "unsupported"])
def test_complete_admitted_policy_set_and_running_catalog_condition(boot_stack, mode):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    owner, storage, descriptor, launcher, handle, gate, original = start()
    policies = tuple(ProbePolicy(u.unit_id, 1, 0.1, 1) for u in config.prepared.units)
    if mode == "missing":
        policies = policies[:-1]
    elif mode == "duplicate":
        policies = (*policies, policies[0])
    elif mode == "unknown":
        policies = (*policies[:-1], replace(policies[-1], unit_id="unknown"))
    else:
        # Test-only frozen-input replacement, with no product callback.
        unit = config.prepared.units[0]
        actions = tuple(
            replace(a, condition="application-ready") if a.phase == "observe" else a
            for a in unit.plan.actions
        )
        plan = replace(unit.plan, actions=actions)
        owner._prepared = replace(
            config.prepared,
            units=(replace(unit, plan=plan), *config.prepared.units[1:]),
        )
        owner._context_pin = (owner._prepared, owner._run_id)
    with pytest.raises(ValueError):
        ProcessReadiness(owner, policies=policies)
    assert not list(work.glob("*.marker"))


def test_sampled_health_loss_invalidates_ready(boot_stack):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    assert facade.start(descriptor.unit_id, descriptor, gate, original).ready
    signal.pidfd_send_signal(launcher._childfd, signal.SIGKILL)
    time.sleep(0.01)
    with pytest.raises(ValueError):
        facade.check_health(original, force=True)
    assert boot_stack[2].cancelled and not any(o.ready for o in facade.observations)


def test_expired_actual_reply_cannot_be_reused(boot_stack, monkeypatch):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(
        boot_stack, freshness=0.01
    )
    assert facade.start(descriptor.unit_id, descriptor, gate, original).ready
    b, lb, hb, gb = second(boot_stack, owner, original)
    facade.bind(lb, hb)
    observe = CatalogLauncher.observe

    def expired(self, handle, until):
        value = observe(self, handle, until)
        return replace(value, observed_at=time.monotonic() - 1)

    monkeypatch.setattr(CatalogLauncher, "observe", expired)
    with pytest.raises(ValueError):
        facade.start(b.unit_id, b, gb, original)
    assert boot_stack[2].cancelled
    assert not (
        boot_stack[4] / (owner._unit(b.unit_id).binding_id + ".marker")
    ).exists()


def test_bootstrap_public_session_label_checked_before_dispatch(boot_stack):
    session = boot_stack[0]
    before = session._sequence
    session.session = "substituted"
    with pytest.raises(ValueError):
        session.renew(
            HostDeadline("substituted", time.monotonic() + 2),
            HostDeadline("substituted", time.monotonic() + 1),
        )
    assert session._sequence == before
    session.session = session.config.admission.generation.session


@pytest.mark.parametrize(
    "field,value",
    [
        ("timeout_seconds", True),
        ("timeout_seconds", 10**1000),
        ("cadence_seconds", 0.6),
        ("attempts", True),
        ("attempts", 0),
        ("attempts", 4),
    ],
)
def test_all_policy_domains_are_finite_and_explicit(field, value):
    arguments = dict(
        unit_id="unit",
        freshness_seconds=0.5,
        cadence_seconds=0.1,
        timeout_seconds=1,
        attempts=3,
    )
    arguments[field] = value
    with pytest.raises(ValueError):
        ProbePolicy(**arguments)


def test_step_dependency_without_flow_still_blocks_dependent(monkeypatch, request):
    from . import test_launcher

    documents = test_launcher.documents

    def step_only():
        docs = documents()
        docs["system.json"]["spec"]["flows"] = []
        docs["scenario.json"]["spec"]["observers"][0]["targetRef"]["element"] = (
            "source-instance"
        )
        return docs

    monkeypatch.setattr(test_launcher, "documents", step_only)
    stack = request.getfixturevalue("boot_stack")
    facade, owner, descriptor, launcher, handle, gate, original = runtime(stack)
    assert not any(e.kind == "flow" for e in stack[3].prepared.graph_edges)
    b, lb, hb, gb = second(stack, owner, original)
    facade.bind(lb, hb)
    with pytest.raises(ValueError, match="ML-PROBE-UNRELEASED"):
        facade.start(b.unit_id, b, gb, original)
    assert not list(stack[4].glob("*.marker"))


def test_query_exhaustion_is_not_ready_and_never_releases_twice(
    boot_stack, monkeypatch
):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    observe = CatalogLauncher.observe
    queries = []

    def pending(self, handle, until):
        value = observe(self, handle, until)
        queries.append(value)
        return replace(value, exec_pipe_closed=False)

    monkeypatch.setattr(CatalogLauncher, "observe", pending)
    with pytest.raises(ValueError, match="ML-PROBE-NOT-READY"):
        facade.start(descriptor.unit_id, descriptor, gate, original)
    assert len(queries) == 3
    assert not facade.observation(descriptor.unit_id).ready
    assert boot_stack[2].cancelled


def test_external_cancel_invalidates_exposed_snapshots(boot_stack):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    historic = facade.start(descriptor.unit_id, descriptor, gate, original)
    owner.cancel("external-test-cancel")
    assert historic.ready  # A historical observation is never authority.
    assert not facade.observation(descriptor.unit_id).ready
    assert not any(o.ready for o in facade.observations)
    assert facade.next_health_deadline is None


def test_fabricated_dependency_guard_rejected_before_release(boot_stack):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    with pytest.raises(ValueError, match="ML-OWNER-READINESS-GUARD"):
        owner.release(
            descriptor.unit_id, descriptor, gate, original, readiness_guard=object()
        )
    assert not list(boot_stack[4].glob("*.marker"))


def test_local_coordinator_storage_owner_is_not_bounded_provider_admission(stack):
    owner = stack[0]
    policies = tuple(ProbePolicy(u.unit_id, 1, 0.1, 1) for u in owner._prepared.units)
    with pytest.raises(ValueError, match="ML-PROBE-PERSISTENCE"):
        ProcessReadiness(owner, policies=policies)
