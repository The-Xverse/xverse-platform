"""Actual full-phase declared dispatch over original staged processes."""

import copy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse_xdl.lifecycle import FileEvidenceJournal
from xverse.maestro.dispatcher import FiniteDispatcher
from xverse.maestro.projection import Limits
from xverse.maestro.providers import ProcessReadiness, ProbePolicy
from xverse.maestro.schedule_plan import admit_schedule
from xverse.maestro.time import HostDeadline
from .test_bootstrap import (
    boot_stack as boot_stack,
    supervisor_binary as supervisor_binary,
)
from .test_boundary import environment as environment, native as native
from .test_launcher import binaries as binaries
from .test_provider import second


def full_stack(
    request,
    monkeypatch,
    *,
    pauses=1,
    duration=0,
    implicit=False,
    skip=False,
    request_limit=1024,
    cleanup_only=False,
):
    from . import test_bootstrap, test_launcher

    docs = test_launcher.documents

    def documents():
        data = docs()
        scenario = data["scenario.json"]["spec"]
        template = scenario["steps"][0]
        definitions = [
            ("prepare-source", "source", "prepare", 0, []),
            ("prepare-sink", "sink", "prepare", 0, []),
            ("start-source", "source", "start", 0, ["prepare-source"]),
            ("start-sink", "sink", "start", duration, ["prepare-sink", "start-source"]),
            ("observe-source", "source", "observe", 1, ["start-source"]),
            ("observe-sink", "sink", "observe", 1, ["start-sink"]),
            ("stop-sink", "sink", "stop", 2, ["observe-sink"]),
            ("cleanup-sink", "sink", "cleanup", 2, ["stop-sink"]),
            ("stop-source", "source", "stop", 3, ["observe-source"]),
            ("cleanup-source", "source", "cleanup", 3, ["stop-source"]),
        ]
        if implicit:
            definitions = [d for d in definitions if d[2] not in ("stop", "cleanup")]
        if cleanup_only:
            definitions = [
                (
                    ("cleanup-a-source" if unit == "source" else "cleanup-z-sink")
                    if phase == "cleanup"
                    else name,
                    unit,
                    phase,
                    3 if phase == "cleanup" else tick,
                    ["observe-" + unit] if phase == "cleanup" else deps,
                )
                for name, unit, phase, tick, deps in definitions
                if phase != "stop"
            ]
            definitions = [d for d in definitions if d[2] != "cleanup"] + list(
                reversed([d for d in definitions if d[2] == "cleanup"])
            )
        steps = []
        for name, unit, phase, tick, deps in definitions:
            item = copy.deepcopy(template)
            item["id"] = name
            item["targetRef"]["element"] = unit + "-instance"
            item["actionKind"] = "validate" if phase == "prepare" else phase
            item["action"]["operation"] = item["actionKind"]
            item["schedule"]["at"] = tick
            item["schedule"]["tolerance"]["value"] = (
                duration if name == "start-source" else 0
            )
            ext = item["extensions"]["io.xverse.experiment"]
            ext["target"]["element"] = name
            ext["phase"] = phase
            ext["dependsOn"] = deps
            ext["duration"]["value"] = duration if name == "start-source" else 0
            steps.append(item)
        scenario["steps"] = steps
        return data

    monkeypatch.setattr(test_launcher, "documents", documents)
    prepare = test_launcher.prepare_lifecycle
    monkeypatch.setattr(
        test_launcher,
        "prepare_lifecycle",
        lambda *a, **kw: prepare(*a, limits=Limits(horizon_ticks=3), **kw),
    )
    configure = test_bootstrap.configured

    def configured(*args, **kwargs):
        config, pin, work = configure(*args, **kwargs)
        plan = admit_schedule(
            config.prepared,
            policies=tuple(
                ProbePolicy(u.unit_id, 5, 5, 0.5) for u in config.prepared.units
            ),
            ticks=(0, 3) if skip else (0,) * pauses + (1, 2, 3),
            active_seconds=8 if pauses > 1 else 4.8,
            operation_seconds=0.5,
            poll_seconds=0.05,
            request_limit=request_limit,
        )
        body = json.loads(config.private_bytes)
        body["schedule"] = json.loads(plan.canonical_bytes)
        return (
            replace(config, schedule=plan, private_bytes=canonical_bytes(body)),
            pin,
            work,
        )

    monkeypatch.setattr(test_bootstrap, "configured", configured)
    stack = request.getfixturevalue("boot_stack")

    def retain():
        directory = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
        if not directory:
            return
        records = FileEvidenceJournal(stack[4].parent / "m3.jsonl").public_records()
        events = EvidenceStore.read_run(stack[4].parent / "argus").records()
        from jsonschema import Draft202012Validator

        validator = Draft202012Validator(
            json.loads(
                Path(__file__).with_name("lifecycle-payload-v2.schema.json").read_text()
            )
        )
        for event in events:
            payload = event.get("extensions", {}).get("xverse.maestro")
            if payload is None:
                continue
            validator.validate(payload)
            for reference in payload["sourceRefs"]:
                if reference["kind"] == "m3-record":
                    record = next(
                        r for r in records if r["sequence"] == reference["sequence"]
                    )
                    assert (
                        reference["sha256"]
                        == "sha256:"
                        + hashlib.sha256(canonical_bytes(record)).hexdigest()
                    )
        (
            Path(directory)
            / (
                "dispatcher-snapshot-"
                + str(os.getpid())
                + "-"
                + request.node.name
                + ".json"
            )
        ).write_text(
            json.dumps(
                {
                    "events": events,
                    "public_m3": records,
                    "schedule": json.loads(stack[3].schedule.canonical_bytes),
                    "source_sha256": hashlib.sha256(
                        Path(__file__).read_bytes()
                    ).hexdigest(),
                    "lifecycle_complete": False,
                }
            )
        )

    request.addfinalizer(retain)
    return stack


def dispatcher(stack):
    owner, storage, a, la, ha, ga, original = stack[6]()
    b, lb, hb, gb = second(stack, owner, original)
    facade = ProcessReadiness(owner, policies=storage.schedule.policies)
    facade.bind(la, ha)
    facade.bind(lb, hb)
    return FiniteDispatcher(facade, stack[0], gates=((a.unit_id, ga), (b.unit_id, gb)))


def ends(driver):
    active = HostDeadline(
        driver.owner.session, time.monotonic() + driver.plan.active_seconds - 0.05
    )
    return active, HostDeadline(
        driver.owner.session,
        active.monotonic_seconds + driver.plan.terminal_reserve_seconds + 0.01,
    )


def test_full_five_phase_dispatch_records_actual_outcomes_and_dispositions(
    request, monkeypatch
):
    stack = full_stack(request, monkeypatch)
    driver = dispatcher(stack)
    bounds = ends(driver)
    trace = []
    for method in ("_send", "_effect"):
        original = getattr(FiniteDispatcher, method)

        def observed(self, *args, _method=method, _original=original, **kwargs):
            began = time.monotonic()
            try:
                return _original(self, *args, **kwargs)
            except Exception as error:
                trace.append(
                    {
                        "method": _method,
                        "kind": str(args[0]) if _method == "_send" else args[0].step_id,
                        "elapsed": time.monotonic() - began,
                        "error_type": type(error).__name__,
                        "diagnostic": str(error),
                    }
                )
                raise

        monkeypatch.setattr(FiniteDispatcher, method, observed)
    result = driver.run(*bounds)
    receipt = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt:
        (Path(receipt) / "dispatcher-operation-observations.json").write_text(
            json.dumps(trace, indent=2)
        )
    assert result.execution_succeeded and result.terminal_recorded, result
    assert len(result.steps) == 10 and all(
        s.disposition == "completed" and s.normal_recorded for s in result.steps
    )
    assert (
        result.cleanup.unit_cleanup_complete and result.cleanup.normal_records_complete
    )
    assert not result.lifecycle_complete and not result.ready_for_execution
    assert driver.run(*bounds) is result
    with pytest.raises(ValueError):
        driver.run(
            HostDeadline(driver.owner.session, bounds[0].monotonic_seconds + 0.01),
            bounds[1],
        )
    events = EvidenceStore.read_run(stack[4].parent / "argus").records()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(
        json.loads(
            Path(__file__).with_name("lifecycle-payload-v2.schema.json").read_text()
        )
    )
    phases = []
    dispositions = []
    for event in events:
        payload = event["extensions"]["xverse.maestro"]
        validator.validate(payload)
        if payload["scope"] == "step" and payload["action"] not in (
            "intent",
            "disposition",
        ):
            phases.append(payload["action"])
        if payload["scope"] == "step" and payload["action"] == "disposition":
            dispositions.append(payload)
    assert sorted(phases) == sorted(
        ["validate", "started", "probe", "stop", "cleanup"] * 2
    )
    assert len(dispositions) == 10 and all(
        p["disposition"] == "completed" for p in dispositions
    )
    receipt = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt:
        (
            Path(receipt) / ("dispatcher-public-" + str(os.getpid()) + ".json")
        ).write_text(
            json.dumps(
                {
                    "events": events,
                    "source_sha256": hashlib.sha256(
                        Path(__file__).read_bytes()
                    ).hexdigest(),
                    "lifecycle_complete": False,
                }
            )
        )


def test_duration_defers_step_completion_until_actual_tick(request, monkeypatch):
    stack = full_stack(request, monkeypatch, duration=1)
    driver = dispatcher(stack)
    result = driver.run(*ends(driver))
    assert result.execution_succeeded, result
    source = next(s for s in result.steps if s.step_id == "start-source")
    sink = next(s for s in result.steps if s.step_id == "start-sink")
    assert source.dispatch_tick == 0 and source.completion_tick == 1
    assert sink.dispatch_tick == 1


def test_paused_ticks_still_service_host_health_and_original_leases(
    request, monkeypatch
):
    stack = full_stack(request, monkeypatch, pauses=40)
    driver = dispatcher(stack)
    result = driver.run(*ends(driver))
    assert result.execution_succeeded, result
    assert result.health_scans >= 1 and result.lease_renewals >= 3
    assert all(s.disposition == "completed" for s in result.steps)


def test_unexpected_effect_failure_records_honest_dispositions_and_cleanup(
    request, monkeypatch
):
    stack = full_stack(request, monkeypatch)
    driver = dispatcher(stack)
    original = FiniteDispatcher._effect

    def failing(self, step):
        if step.step_id == "start-source":
            raise RuntimeError("owned unexpected effect failure")
        return original(self, step)

    monkeypatch.setattr(FiniteDispatcher, "_effect", failing)
    result = driver.run(*ends(driver))
    assert not result.execution_succeeded and result.terminal_recorded
    assert (
        result.cleanup.unit_cleanup_complete
        and not result.cleanup.normal_records_complete
    )
    assert not list(stack[4].glob("*.marker"))
    assert any(s.disposition == "failed" for s in result.steps)
    assert any(s.disposition == "blocked" for s in result.steps)
    events = EvidenceStore.read_run(stack[4].parent / "argus").records()
    assert not any(
        e.get("extensions", {}).get("xverse.maestro", {}).get("action") == "health-loss"
        for e in events
    )


def test_missing_prerequisite_probe_names_the_actual_original_unit(
    request, monkeypatch
):
    import signal

    stack = full_stack(request, monkeypatch)
    driver = dispatcher(stack)
    source = driver.prepared.units[0].unit_id
    original = FiniteDispatcher._effect

    def lose(self, step):
        if step.step_id == "start-sink":
            signal.pidfd_send_signal(
                self.facade._bindings[source].launcher._childfd, signal.SIGKILL
            )
            time.sleep(0.02)
        return original(self, step)

    monkeypatch.setattr(FiniteDispatcher, "_effect", lose)
    result = driver.run(*ends(driver))
    assert not result.execution_succeeded and result.cleanup.unit_cleanup_complete
    events = EvidenceStore.read_run(stack[4].parent / "argus").records()
    failures = [
        e["extensions"]["xverse.maestro"]
        for e in events
        if e.get("producerId") == "maestro.scheduler14"
        and e["extensions"]["xverse.maestro"]["action"] == "health-loss"
    ]
    assert (
        len(failures) == 1
        and failures[0]["unitId"] == source
        and failures[0]["outcome"] == "unknown"
    )
    assert not (stack[4] / (driver.prepared.units[1].binding_id + ".marker")).exists()


def test_bad_schedule_ack_never_becomes_completed_step_authority(request, monkeypatch):
    from xverse.maestro.persistence import PersistenceClient

    stack = full_stack(request, monkeypatch)
    driver = dispatcher(stack)
    rpc = PersistenceClient._rpc

    def altered(self, kind, body, until):
        op, end, reply = rpc(self, kind, body, until)
        if kind == "schedule" and body["kind"] == "step-complete":
            reply["events"][0]["clocks"]["simulation"]["value"] += 1
        return op, end, reply

    monkeypatch.setattr(PersistenceClient, "_rpc", altered)
    result = driver.run(*ends(driver))
    assert not result.execution_succeeded and not result.terminal_recorded
    assert result.cleanup.unit_cleanup_complete and driver.client._failed
    assert not list(stack[4].glob("*.marker"))


def test_copied_statement_cannot_issue_original_schedule_rpc(request, monkeypatch):
    from xverse.maestro.persistence import PersistenceClient

    stack = full_stack(request, monkeypatch)
    driver = dispatcher(stack)
    before = driver.client._sequence
    call = PersistenceClient.schedule_call
    monkeypatch.setattr(
        PersistenceClient,
        "schedule_call",
        lambda self, owner, stmt, until: call(self, owner, replace(stmt), until),
    )
    result = driver.run(*ends(driver))
    assert driver.client._sequence == before
    assert not result.execution_succeeded and result.cleanup.unit_cleanup_complete
    assert not list(stack[4].glob("*.marker"))


def test_missed_tick_window_has_no_fabricated_step_or_probe_success(
    request, monkeypatch
):
    stack = full_stack(request, monkeypatch, skip=True)
    driver = dispatcher(stack)
    result = driver.run(*ends(driver))
    assert not result.execution_succeeded and result.terminal_recorded
    assert result.cleanup.unit_cleanup_complete
    events = EvidenceStore.read_run(stack[4].parent / "argus").records()
    assert not any(
        e.get("extensions", {}).get("xverse.maestro", {}).get("action") == "health-loss"
        for e in events
    )
    assert all(
        s.disposition != "completed"
        for s in result.steps
        if s.step_id.startswith("observe")
    )


def test_terminal_service_failure_still_attempts_original_c1_cleanup(
    request, monkeypatch
):
    stack = full_stack(request, monkeypatch, implicit=True)
    driver = dispatcher(stack)
    service = FiniteDispatcher._service

    def failed(self, *, terminal=False):
        if terminal:
            raise ValueError("owned terminal service unavailable")
        return service(self, terminal=terminal)

    monkeypatch.setattr(FiniteDispatcher, "_service", failed)
    result = driver.run(*ends(driver))
    assert not result.execution_succeeded and result.cleanup.unit_cleanup_complete
    assert not result.cleanup.normal_records_complete
    assert all(
        stack[1].record(binding.launcher.recipe.descriptor).boundary_released
        for _, binding in driver._bindings
    )


def test_actual_tick_worker_stall_returns_incomplete_with_owned_cleanup(
    request, monkeypatch
):
    import signal
    from .test_launcher import deadline

    stack = full_stack(request, monkeypatch)
    driver = dispatcher(stack)
    send = FiniteDispatcher._send

    def stopped(self, kind, until, **values):
        reply = send(self, kind, until, **values)
        if kind == "begin":
            signal.pidfd_send_signal(self.client._pidfd, signal.SIGSTOP)
        return reply

    monkeypatch.setattr(FiniteDispatcher, "_send", stopped)
    result = driver.run(*ends(driver))
    assert not result.execution_succeeded and result.cleanup.unit_cleanup_complete
    assert driver.client._failed and driver.client.drain(deadline(1)).worker_reaped
    assert not list(stack[4].glob("*.marker"))


def test_normal_conflict_rejects_without_cancelling_but_operator_cancel_bypasses_locks(
    request, monkeypatch
):
    import threading

    stack = full_stack(request, monkeypatch)
    driver = dispatcher(stack)
    original = FiniteDispatcher._effect
    observed = []

    def check(self, step):
        if not observed:

            def conflict():
                try:
                    self.facade.check_health(
                        HostDeadline(self.owner.session, time.monotonic() + 0.5)
                    )
                except ValueError:
                    observed.append("conflict")

            thread = threading.Thread(target=conflict)
            thread.start()
            thread.join(timeout=1)
            assert not thread.is_alive() and not self.owner.latch.cancelled
            self.facade._lock.acquire()
            self.owner._lock.acquire()
            try:
                thread = threading.Thread(target=self.cancel)
                thread.start()
                thread.join(timeout=1)
                assert not thread.is_alive() and self.owner.latch.cancelled
            finally:
                self.owner._lock.release()
                self.facade._lock.release()
        return original(self, step)

    monkeypatch.setattr(FiniteDispatcher, "_effect", check)
    result = driver.run(*ends(driver))
    assert observed == ["conflict"] and not result.execution_succeeded
    assert result.terminal_recorded and result.cleanup.unit_cleanup_complete
    assert all(s.disposition == "cancelled" for s in result.steps)


def test_actual_remaining_rpc_budget_rejects_before_any_release(request, monkeypatch):
    from .test_launcher import deadline

    stack = full_stack(request, monkeypatch, request_limit=128)
    driver = dispatcher(stack)
    claim = driver.owner._claims[driver.prepared.units[0].unit_id].receipt
    extra = driver.client._request_limit - driver.plan.required_requests + 1
    for _ in range(extra):
        driver.client.revalidate_intent(claim, deadline(0.5))
    with pytest.raises(ValueError):
        driver.run(*ends(driver))
    assert not driver.owner.latch.cancelled and not list(stack[4].glob("*.marker"))
    with pytest.raises(ValueError):
        driver.client._rpc(
            "schedule",
            {"kind": "begin", "observed_at": time.monotonic()},
            deadline(0.5),
        )
    assert driver.client._failed and not list(stack[4].glob("*.marker"))


def test_independent_worker_rejects_step_success_without_real_readiness(
    request, monkeypatch
):
    stack = full_stack(request, monkeypatch)
    driver = dispatcher(stack)
    original = FiniteDispatcher._effect

    def omitted(self, step):
        if step.step_id == "start-source":
            return
        return original(self, step)

    monkeypatch.setattr(FiniteDispatcher, "_effect", omitted)
    result = driver.run(*ends(driver))
    assert not result.execution_succeeded and driver.client._failed
    assert result.cleanup.unit_cleanup_complete and not list(stack[4].glob("*.marker"))
    events = EvidenceStore.read_run(stack[4].parent / "argus").records()
    assert not any(
        e.get("extensions", {}).get("xverse.maestro", {}).get("action") == "started"
        for e in events
    )


@pytest.mark.parametrize(
    "mode", ["foreign-session", "expired-active", "short-reserve", "copy"]
)
def test_invalid_dispatch_scope_rejects_without_release_or_cancellation(
    request, monkeypatch, mode
):
    stack = full_stack(request, monkeypatch)
    driver = dispatcher(stack)
    active, terminal = ends(driver)
    if mode == "copy":
        with pytest.raises(TypeError):
            copy.copy(driver)
    else:
        if mode == "foreign-session":
            active = HostDeadline("foreign", active.monotonic_seconds)
        elif mode == "expired-active":
            active = HostDeadline(driver.owner.session, time.monotonic() - 0.01)
        else:
            terminal = HostDeadline(
                driver.owner.session, active.monotonic_seconds + 0.1
            )
        with pytest.raises(ValueError):
            driver.run(active, terminal)
    assert not driver.owner.latch.cancelled and not list(stack[4].glob("*.marker"))


def test_implicit_horizon_stop_respects_dependencies_before_compiler_rank(
    request, monkeypatch
):
    stack = full_stack(request, monkeypatch, cleanup_only=True)
    driver = dispatcher(stack)
    complete = {s.step_id for s in driver.prepared.steps if s.phase != "cleanup"}
    static = driver.prepared.eligible_steps(3, complete)
    assert static[0].unit_id == driver.prepared.units[0].unit_id
    result = driver.run(*ends(driver))
    assert result.execution_succeeded, result
    events = EvidenceStore.read_run(stack[4].parent / "argus").records()
    cleanup = [
        e["extensions"]["xverse.maestro"]["stepId"]
        for e in events
        if e.get("producerId") == "maestro.scheduler14"
        and e["extensions"]["xverse.maestro"].get("stepId", "").startswith("cleanup-")
        and e["extensions"]["xverse.maestro"]["action"] == "intent"
    ]
    assert cleanup == ["cleanup-z-sink", "cleanup-a-source"]
