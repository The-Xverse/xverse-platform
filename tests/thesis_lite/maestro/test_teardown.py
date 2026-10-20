"""Actual owned reverse teardown; expected cases precede product implementation."""

import copy
import hashlib
import fcntl
import json
import os
from pathlib import Path
import signal
import time

import pytest
from xverse.argus import EvidenceStore
from xverse_xdl.lifecycle import FileEvidenceJournal
from xverse.maestro.teardown import ReverseTeardown
from xverse.maestro.time import HostDeadline
from .test_provider import runtime, second
from .test_bootstrap import (
    boot_stack as boot_stack,
    supervisor_binary as supervisor_binary,
)
from .test_boundary import environment as environment, native as native
from .test_launcher import binaries as binaries, deadline


def pair(stack):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(stack)
    b, lb, hb, gb = second(stack, owner, original)
    facade.bind(lb, hb)
    assert facade.start(descriptor.unit_id, descriptor, gate, original).ready
    assert facade.start(b.unit_id, b, gb, original).ready
    return facade, owner, (descriptor, launcher, handle, gate), (b, lb, hb, gb)


def test_normal_reverse_stop_reap_and_separate_release_with_durable_records(boot_stack):
    facade, owner, a, b = pair(boot_stack)
    controller = ReverseTeardown(facade, per_unit_seconds=0.8)
    result = controller.run(deadline(2), reason="normal-stop")
    assert [u.unit_id for u in result.units] == [b[0].unit_id, a[0].unit_id]
    assert (
        result.starts_closed
        and result.unit_cleanup_complete
        and result.normal_records_complete
    )
    assert all(not u.emergency for u in result.units)
    assert not result.lifecycle_complete and not result.ready_for_execution
    root = boot_stack[4].parent
    records = FileEvidenceJournal(root / "m3.jsonl").public_records()
    events = EvidenceStore.read_run(root / "argus").records()
    m3_teardown = [r for r in records if r["status"] in ("stopped", "cleaned")]
    assert [r["status"] for r in m3_teardown] == [
        "stopped",
        "cleaned",
        "stopped",
        "cleaned",
    ]
    assert [r["executionId"] for r in m3_teardown] == [b[2].execution_id] * 2 + [
        a[2].execution_id
    ] * 2
    payloads = [
        r["extensions"]["xverse.maestro"]
        for r in events
        if r.get("producerId") == "maestro.teardown13"
    ]
    assert [p["action"] for p in payloads] == [
        "intent",
        "stop",
        "intent",
        "cleanup",
    ] * 2
    assert [p["outcome"] for p in payloads] == [
        "pending",
        "succeeded",
        "pending",
        "succeeded",
    ] * 2
    from jsonschema import Draft202012Validator
    from xverse.argus.schema import canonical_bytes

    validator = Draft202012Validator(
        json.loads(
            Path(__file__).with_name("lifecycle-payload-v2.schema.json").read_text()
        )
    )
    for event in events:
        payload = event["extensions"]["xverse.maestro"]
        validator.validate(payload)
        for reference in payload["sourceRefs"]:
            if reference["kind"] == "m3-record":
                source = next(
                    r for r in records if r["sequence"] == reference["sequence"]
                )
                assert (
                    reference["sha256"]
                    == "sha256:" + hashlib.sha256(canonical_bytes(source)).hexdigest()
                )
    serialized = json.dumps(events)
    assert (
        "private-process-nonce-" not in serialized
        and "maestro-boundary:" not in serialized
    )
    receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt_dir:
        (
            Path(receipt_dir) / ("teardown-public-" + str(os.getpid()) + ".json")
        ).write_text(
            json.dumps(
                {
                    "public_m3": records,
                    "argus_events": events,
                    "source_sha256": hashlib.sha256(
                        Path(__file__).read_bytes()
                    ).hexdigest(),
                    "lifecycle_complete": False,
                }
            )
        )
    before = len(records)
    assert controller.run(deadline(1), reason="normal-stop") is result
    assert len(FileEvidenceJournal(root / "m3.jsonl").records) == before
    with pytest.raises(ValueError):
        controller.run(deadline(1), reason="changed")
    with pytest.raises(ValueError):
        facade.start(a[0].unit_id, a[0], a[3], deadline(1))


def test_c1_termination_retains_controls_until_separate_release(boot_stack):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    owner, storage, descriptor, launcher, handle, gate, original = start()
    owner.release(descriptor.unit_id, descriptor, gate, original)
    observed = manager.terminate(descriptor, deadline=deadline(1))
    assert (
        observed.state == "empty"
        and observed.identity_retained
        and observed.residual_count == 0
    )
    assert not observed.boundary_released
    assert manager.residual_membership(descriptor) == ()
    until = time.monotonic() + 0.5
    while not launcher.observe(handle, deadline(0.5)).leader_reaped:
        assert time.monotonic() < until
    released = manager.release_empty(descriptor, deadline=deadline(1))
    assert released.boundary_released and not released.identity_retained
    assert manager.force_cleanup(descriptor).boundary_released


def test_release_without_stop_observation_cannot_kill_or_remove(boot_stack):
    owner, storage, descriptor, launcher, handle, gate, original = boot_stack[6]()
    with pytest.raises(ValueError):
        boot_stack[1].release_empty(descriptor, deadline=deadline(0.5))
    assert not boot_stack[1].record(descriptor).boundary_released
    assert not list(boot_stack[4].glob("*.marker"))


def test_stage_only_teardown_never_fabricates_start_outcome(boot_stack):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    result = ReverseTeardown(facade, per_unit_seconds=1).run(deadline(2))
    assert result.unit_cleanup_complete and result.normal_records_complete
    assert not list(boot_stack[4].glob("*.marker"))
    records = FileEvidenceJournal(boot_stack[4].parent / "m3.jsonl").public_records()
    assert not any(r["kind"] == "outcome" and r["status"] == "running" for r in records)
    assert [r["status"] for r in records if r["kind"] == "outcome"] == [
        "stopped",
        "cleaned",
    ]


def test_already_exited_leader_with_live_descendant_requires_c1_cleanup(
    monkeypatch, request
):
    from . import test_bootstrap

    configured = test_bootstrap.configured
    monkeypatch.setattr(
        test_bootstrap,
        "configured",
        lambda path, manager, binaries: configured(
            path, manager, binaries, mode="descendant"
        ),
    )
    stack = request.getfixturevalue("boot_stack")
    facade, owner, descriptor, launcher, handle, gate, original = runtime(stack)
    owner.release(descriptor.unit_id, descriptor, gate, original)
    until = time.monotonic() + 0.5
    while not launcher.observe(handle, deadline(0.5)).leader_reaped:
        assert time.monotonic() < until
    result = ReverseTeardown(facade, per_unit_seconds=1).run(deadline(2))
    assert result.unit_cleanup_complete and result.normal_records_complete
    assert result.units[0].leader_reaped and result.units[0].boundary_empty


@pytest.mark.parametrize(
    "mode", ["foreign-session", "copy", "owner-lock", "facade-lock"]
)
def test_identity_and_nonblocking_conflicts_have_no_teardown_effect(boot_stack, mode):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    controller = ReverseTeardown(facade, per_unit_seconds=1)
    if mode == "copy":
        with pytest.raises(TypeError):
            copy.copy(controller)
    elif mode == "foreign-session":
        with pytest.raises(ValueError):
            controller.run(HostDeadline("foreign", time.monotonic() + 1))
    else:
        lock = owner._lock if mode == "owner-lock" else facade._lock
        lock.acquire()
        try:
            began = time.monotonic()
            with pytest.raises(ValueError):
                controller.run(deadline(1))
            assert time.monotonic() - began < 0.1
            controller.cancel("conflict-cancel")
            assert boot_stack[2].cancelled
        finally:
            lock.release()
    assert not boot_stack[1].record(descriptor).boundary_released


def test_original_issuer_loss_preserves_explicit_unresolved_reap(boot_stack):
    facade, owner, a, b = pair(boot_stack)
    signal.pidfd_send_signal(b[1]._pidfd, signal.SIGKILL)
    time.sleep(0.01)
    result = ReverseTeardown(facade, per_unit_seconds=0.8).run(deadline(2))
    assert all(u.boundary_empty and u.boundary_released for u in result.units)
    lost = next(u for u in result.units if u.unit_id == b[0].unit_id)
    assert (
        lost.emergency and not lost.leader_reaped and not lost.normal_records_complete
    )
    assert not result.normal_records_complete and not result.lifecycle_complete
    receipt = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt:
        (
            Path(receipt) / ("teardown-issuer-loss-" + str(os.getpid()) + ".json")
        ).write_text(
            json.dumps(
                {
                    "original_issuer_loss": True,
                    "unresolved_direct_child_reap": True,
                    "boundaries_released": True,
                }
            )
        )


def test_lost_original_c1_is_unresolved_and_other_owned_cleanup_continues(boot_stack):
    facade, owner, a, b = pair(boot_stack)
    manager = boot_stack[1]
    cap = manager._caps.pop(b[0].key)
    try:
        result = ReverseTeardown(facade, per_unit_seconds=0.8).run(deadline(2))
    finally:
        manager._caps[b[0].key] = cap
    lost = next(u for u in result.units if u.unit_id == b[0].unit_id)
    other = next(u for u in result.units if u.unit_id == a[0].unit_id)
    assert not lost.boundary_released and lost.emergency
    assert other.boundary_released and not result.normal_records_complete


@pytest.mark.parametrize("mode", ["m3-lock", "m3-loss", "ack-phase", "ack-outcome"])
def test_missing_normal_record_or_ack_uses_original_cleanup_only(
    boot_stack, monkeypatch, mode
):
    from xverse.maestro.persistence import PersistenceClient

    facade, owner, a, b = pair(boot_stack)
    locked = None
    if mode == "m3-lock":
        locked = os.open(boot_stack[4].parent / "m3.jsonl.lock", os.O_RDWR)
        fcntl.flock(locked, fcntl.LOCK_EX)
    elif mode == "m3-loss":
        path = boot_stack[4].parent / "m3.jsonl"
        path.rename(path.with_name("saved-m3.jsonl"))
        path.mkdir()
    else:
        rpc = PersistenceClient._rpc

        def altered(self, kind, body, until):
            op, end, result = rpc(self, kind, body, until)
            if kind == "teardown":
                if mode == "ack-phase":
                    result["phase"] = "cleanup" if body["phase"] == "stop" else "stop"
                else:
                    result["event"]["extensions"]["xverse.maestro"]["outcome"] = (
                        "succeeded"
                    )
            return op, end, result

        monkeypatch.setattr(PersistenceClient, "_rpc", altered)
    try:
        result = ReverseTeardown(facade, per_unit_seconds=0.8).run(deadline(2))
    finally:
        if locked is not None:
            fcntl.flock(locked, fcntl.LOCK_UN)
            os.close(locked)
    assert all(u.boundary_released for u in result.units)
    assert any(u.emergency for u in result.units) and not result.normal_records_complete
    assert boot_stack[2].cancelled


@pytest.mark.parametrize("cap", [True, 0, -1, float("nan"), float("inf"), 6])
def test_invalid_teardown_budget_rejects_before_effect(boot_stack, cap):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    with pytest.raises(ValueError):
        ReverseTeardown(facade, per_unit_seconds=cap)
    assert not list(boot_stack[4].glob("*.marker"))


def test_copied_active_step_cannot_authorize_normal_record(boot_stack, monkeypatch):
    from dataclasses import replace
    from xverse.maestro.persistence import PersistenceClient

    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    record = PersistenceClient.record_teardown
    before = owner.persistence._sequence

    def forged(self, controller, step, until):
        return record(self, controller, replace(step), until)

    monkeypatch.setattr(PersistenceClient, "record_teardown", forged)
    result = ReverseTeardown(facade, per_unit_seconds=0.8).run(deadline(1))
    assert owner.persistence._sequence == before
    assert result.units[0].emergency and not result.normal_records_complete
    assert result.units[0].boundary_released


def test_missing_original_registry_never_adopts_handle(boot_stack):
    facade, owner, a, b = pair(boot_stack)
    controller = ReverseTeardown(facade, per_unit_seconds=0.8)
    original = owner._launchers.pop(b[0].unit_id)
    try:
        result = controller.run(deadline(2))
    finally:
        owner._launchers[b[0].unit_id] = original
    lost = next(u for u in result.units if u.unit_id == b[0].unit_id)
    assert lost.emergency and not lost.normal_records_complete
    assert lost.boundary_released and not lost.leader_reaped


def test_expired_c1_deadline_and_lock_conflict_cannot_mutate(boot_stack):
    owner, storage, descriptor, launcher, handle, gate, original = boot_stack[6]()
    manager = boot_stack[1]
    with pytest.raises(ValueError):
        manager.terminate(
            descriptor, deadline=HostDeadline(owner.session, time.monotonic() - 0.01)
        )
    manager._lock.acquire()
    try:
        began = time.monotonic()
        with pytest.raises(ValueError):
            manager.terminate(descriptor, deadline=deadline(0.5))
        assert time.monotonic() - began < 0.1
    finally:
        manager._lock.release()
    assert not manager.record(descriptor).boundary_released


@pytest.mark.parametrize("mode", ["teardown-flush-fail", "teardown-flush-hang"])
def test_actual_teardown_flush_fault_retains_missing_normal_records(boot_stack, mode):
    import socket
    import subprocess
    import sys
    from xverse.maestro.persistence import PersistenceClient, sealed_input_fd
    from xverse.maestro.owner import ReleaseOwner, StageSupervisor
    from xverse.maestro.launcher import make_launch_recipe
    from xverse.maestro.providers import ProcessReadiness, ProbePolicy

    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    parent, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    fd = sealed_input_fd(config)
    process = subprocess.Popen(
        [
            sys.executable,
            "-I",
            str(Path(__file__).with_name("outcome_fixture.py")),
            str(peer.fileno()),
            str(fd),
            mode,
        ],
        pass_fds=(peer.fileno(), fd),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    peer.close()
    os.close(fd)
    try:
        storage = PersistenceClient(
            process, parent, config, latch, deadline=deadline(2)
        )
        clients.append(storage)
        owner = ReleaseOwner.from_persistence(
            storage, StageSupervisor(manager, latch), latch
        )
        owners.append(owner)
        original = deadline(3)
        unit = config.prepared.units[0].unit_id
        owner.commit_intent(unit, original)
        descriptor = boundary("phase-workload", unit)
        recipe = make_launch_recipe(
            owner,
            descriptor,
            environment={"MAESTRO_VISIBLE": "declared"},
            helper_artifact_digest=owner._unit(unit).provider.artifact_digest,
            deadline=original,
        )
        launcher = session.catalog(owner, recipe, boundary("phase-launcher"), original)
        clients.append(launcher)
        handle = launcher.stage(original)
        facade = ProcessReadiness(
            owner,
            policies=tuple(
                ProbePolicy(u.unit_id, 2, 0.5, 1) for u in config.prepared.units
            ),
        )
        facade.bind(launcher, handle)
        result = ReverseTeardown(facade, per_unit_seconds=1).run(deadline(2))
        assert result.units[0].boundary_released and result.units[0].emergency
        assert not result.normal_records_complete
        assert storage.drain(deadline(1)).worker_reaped
        records = FileEvidenceJournal(work.parent / "m3.jsonl").public_records()
        assert any(
            r["kind"] == "intent" and r["actionId"] != handle.action_id for r in records
        )
        assert not any(
            r["kind"] == "outcome" and r["status"] == "stopped" for r in records
        )
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=2)
        assert process.stderr.read() == b""
        process.stderr.close()
        receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
        if receipt_dir:
            (
                Path(receipt_dir)
                / ("teardown-fault-worker-" + str(process.pid) + ".json")
            ).write_text(
                json.dumps(
                    {
                        "worker_reaped": True,
                        "returncode": process.returncode,
                        "mode": mode,
                        "source_sha256": hashlib.sha256(
                            Path(__file__).with_name("outcome_fixture.py").read_bytes()
                        ).hexdigest(),
                    }
                )
            )


def test_emergency_status_conflict_never_blocks_or_infers_release(
    boot_stack, monkeypatch
):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    manager = boot_stack[1]

    def conflict(self, job, until):
        manager._lock.acquire()
        raise ValueError("owned post-snapshot manager conflict")

    monkeypatch.setattr(ReverseTeardown, "_normal", conflict)
    began = time.monotonic()
    try:
        result = ReverseTeardown(facade, per_unit_seconds=0.3).run(deadline(1))
    finally:
        manager._lock.release()
    assert time.monotonic() - began < 0.6
    assert result.units[0].emergency
    assert not result.units[0].boundary_empty and not result.units[0].boundary_released
    assert not result.normal_records_complete and not result.unit_cleanup_complete
    assert owner.latch.cancelled
