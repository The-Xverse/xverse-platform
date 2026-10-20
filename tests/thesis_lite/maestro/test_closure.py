"""Original full-run resource closure; expected controls precede implementation."""

from dataclasses import asdict, replace
import copy
import hashlib
import json
import os
from pathlib import Path
import signal

import pytest
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse.maestro.run_closure import RunClosure, ClosureError
from xverse.maestro.teardown import ReverseTeardown
from .test_bootstrap import (
    boot_stack as boot_stack,
    supervisor_binary as supervisor_binary,
)
from .test_boundary import environment as environment, native as native
from .test_launcher import binaries as binaries, deadline
from .test_provider import runtime


def retain(result, stack, name):
    root = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if root:
        reader = EvidenceStore.read_run(stack[4].parent / "argus")
        data = dict(
            result=asdict(result),
            manifest=reader.manifest,
            recorded=reader.recorded_evidence_status,
            assessed=reader.assessed_evidence_status,
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        )
        (Path(root) / f"closure-public-{os.getpid()}-{name}.json").write_text(
            json.dumps(data)
        )


def test_all_original_helpers_and_extra_boundary_close_with_separate_writer_facts(
    boot_stack,
):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    root = boot_stack[0]
    extra = boot_stack[5]("extra-unhandled")
    closer = RunClosure(root, teardown=ReverseTeardown(facade))
    until = deadline(7)
    result = closer.close(until)
    assert result.cleanup_complete
    assert len(result.helpers) == 3 and len(result.boundaries) == 5
    assert all(h.process_reaped for h in result.helpers)
    assert next(h for h in result.helpers if h.role == 1).direct_child_reaped
    assert any(b.unit_id == extra.unit_id and b.released for b in result.boundaries)
    writer = result.writers[0]
    assert writer.acknowledged and writer.before_state == "open"
    assert writer.after_state == "failed" and writer.abort_completed
    assert writer.abort_usability == "usable" and writer.after_usability == "unusable"
    assert writer.durable_recorded_status == "incomplete"
    reader = EvidenceStore.read_run(boot_stack[4].parent / "argus")
    assert (
        writer.manifest_sha256
        == hashlib.sha256(canonical_bytes(reader.manifest)).hexdigest()
    )
    assert not result.lifecycle_complete and not result.ready_for_execution
    assert closer.close(until) is result
    with pytest.raises(ClosureError):
        closer.close(until, reason="different")
    retain(result, boot_stack, "normal")


def test_partial_bootstrap_closes_exact_resources_without_normal_unit_records(
    boot_stack,
):
    owner, storage, descriptor, launcher, handle, gate, original = boot_stack[6]()
    result = RunClosure(boot_stack[0]).close(deadline(5))
    assert result.cleanup_complete and not result.normal_unit_records_complete
    assert not (boot_stack[4] / "source-binding.marker").exists()
    assert result.writers[0].abort_completed
    retain(result, boot_stack, "staged")


def test_actual_storage_stall_keeps_unknown_state_and_still_closes_owned_boundaries(
    boot_stack,
):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    storage = owner.persistence
    signal.pidfd_send_signal(storage.process._capability.fileno(), signal.SIGSTOP)
    result = RunClosure(boot_stack[0], terminal_seconds=0.1).close(deadline(4))
    assert result.cleanup_complete
    writer = result.writers[0]
    assert not writer.acknowledged and writer.after_state is None
    assert writer.last_acknowledged_state == "open"
    assert writer.manifest_sha256 is None and not writer.abort_completed
    retain(result, boot_stack, "storage-stall")


def test_forced_native_issuer_loss_does_not_fabricate_direct_wait(boot_stack):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    signal.pidfd_send_signal(launcher.process._capability.fileno(), signal.SIGKILL)
    result = RunClosure(boot_stack[0]).close(deadline(5))
    assert result.root_reaped and all(b.released for b in result.boundaries)
    assert not result.cleanup_complete
    assert next(h for h in result.helpers if h.role == 1).direct_child_reaped is False
    retain(result, boot_stack, "issuer-loss")


@pytest.mark.parametrize(
    "field,value",
    [
        ("terminal_seconds", True),
        ("drain_seconds", 3),
        ("boundary_seconds", float("nan")),
    ],
)
def test_invalid_closure_budget_has_no_effect(boot_stack, field, value):
    with pytest.raises(ClosureError):
        RunClosure(boot_stack[0], **{field: value})
    assert not boot_stack[2].cancelled


def test_normal_conflicts_reject_and_independent_cancel_does_not_wait(boot_stack):
    closer = RunClosure(boot_stack[0])
    boot_stack[0]._lock.acquire()
    try:
        with pytest.raises(ClosureError):
            closer.close(deadline(3))
        assert not boot_stack[2].cancelled
        closer.cancel()
        assert boot_stack[2].cancelled
    finally:
        boot_stack[0]._lock.release()
    result = closer.close(deadline(3))
    assert result.root_reaped


def test_copied_and_changed_scope_reject_before_mutation(boot_stack):
    closer = RunClosure(boot_stack[0])
    with pytest.raises((ValueError, TypeError)):
        copy.copy(closer)
    with pytest.raises(ClosureError):
        closer.close(replace(deadline(3), session="other"))
    assert not boot_stack[2].cancelled


def test_full_dispatcher_result_precedes_full_helper_closure(request, monkeypatch):
    from .test_dispatcher import full_stack, dispatcher, ends

    stack = full_stack(request, monkeypatch)
    driver = dispatcher(stack)
    execution = driver.run(*ends(driver))
    assert execution.execution_succeeded
    result = RunClosure(stack[0], dispatcher=driver).close(deadline(5))
    assert result.execution_succeeded is True and result.cleanup_complete
    assert result.normal_unit_records_complete and len(result.helpers) == 5
    assert result.writers[0].abort_completed
    assert not result.lifecycle_complete
    retain(result, stack, "full-dispatcher")


@pytest.mark.parametrize("mode", ["flush-fail", "abort-before", "abort-after"])
def test_actual_writer_fault_stage_keeps_public_state_and_durable_manifest_separate(
    boot_stack, mode
):
    import socket
    import subprocess
    import sys
    from xverse.maestro.persistence import PersistenceClient, sealed_input_fd

    root, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    parent, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    fd = sealed_input_fd(config)
    process = subprocess.Popen(
        [
            sys.executable,
            "-I",
            str(Path(__file__).with_name("closure_fixture.py")),
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
        result = storage.close_incomplete(deadline(1))
        assert result.acknowledged and not result.abort_completed
        assert result.abort_attempted == (mode != "flush-fail")
        assert result.abort_usability == (
            "unknown" if mode == "flush-fail" else "usable"
        )
        assert result.after_usability == (
            "unusable" if mode == "abort-after" else "unknown"
        )
        assert result.after_state == ("failed" if mode == "abort-after" else "open")
        assert result.stage == (
            "flush-error" if mode == "flush-fail" else "abort-error"
        )
        reader = EvidenceStore.read_run(work.parent / "argus")
        assert (
            result.manifest_sha256
            == hashlib.sha256(canonical_bytes(reader.manifest)).hexdigest()
        )
        assert result.durable_recorded_status == (
            "incomplete" if mode == "abort-after" else "unassessed"
        )
        assert storage.close_incomplete(deadline(0.5)) is result
        assert storage.drain(deadline(1)).worker_reaped
    finally:
        process.wait(timeout=2)
        assert process.stderr.read() == b""
        process.stderr.close()
        directory = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
        if directory:
            (Path(directory) / f"closure-fault-worker-{process.pid}.json").write_text(
                json.dumps(
                    {
                        "mode": mode,
                        "worker_reaped": True,
                        "returncode": process.returncode,
                        "source_sha256": hashlib.sha256(
                            Path(__file__).with_name("closure_fixture.py").read_bytes()
                        ).hexdigest(),
                        "component_only_standalone_test_worker": True,
                    }
                )
            )


@pytest.mark.parametrize("target", ["owner", "facade", "controller"])
def test_unit_mutation_conflict_rejects_before_closure_cancellation(boot_stack, target):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    controller = ReverseTeardown(facade)
    closer = RunClosure(boot_stack[0], teardown=controller)
    lock = {
        "owner": owner._lock,
        "facade": facade._lock,
        "controller": controller._lock,
    }[target]
    lock.acquire()
    try:
        with pytest.raises(ClosureError):
            closer.close(deadline(5))
        assert not owner.latch.cancelled
        assert owner._dispatch_owner is None
    finally:
        lock.release()


def test_original_inventory_content_substitution_rejects_before_any_cleanup(boot_stack):
    owner, storage, descriptor, launcher, handle, gate, original = boot_stack[6]()
    root = boot_stack[0]
    saved = dict(root._issued)
    slot = next(iter(root._issued))
    role, helper, unit = root._issued[slot]
    root._issued[slot] = (1, helper, unit)
    try:
        with pytest.raises(ValueError):
            RunClosure(root)
        assert not root.latch.cancelled
    finally:
        root._issued.clear()
        root._issued.update(saved)


@pytest.mark.parametrize("mutation", ["stage", "state", "extra", "hash"])
def test_malformed_actual_closure_ack_is_not_current_writer_evidence(
    boot_stack, monkeypatch, mutation
):
    from xverse.maestro.persistence import PersistenceClient

    owner, storage, descriptor, launcher, handle, gate, original = boot_stack[6]()
    rpc = PersistenceClient._rpc

    def altered(self, kind, body, until):
        operation, end, response = rpc(self, kind, body, until)
        if kind == "closure":
            response = dict(response)
            if mutation == "stage":
                response["stage"] = "fabricated"
            elif mutation == "state":
                response["after_state"] = "open"
            elif mutation == "extra":
                response["extra"] = True
            else:
                response["manifest_sha256"] = "incorrect"
        return operation, end, response

    monkeypatch.setattr(PersistenceClient, "_rpc", altered)
    result = RunClosure(boot_stack[0]).close(deadline(5))
    assert result.cleanup_complete
    assert not result.writers[0].acknowledged and result.writers[0].after_state is None
    assert result.writers[0].last_acknowledged_state == "open"


def test_failed_adapter_construction_retains_original_birth_and_unknown_writer(
    boot_stack, monkeypatch
):
    from xverse.maestro.persistence import PersistenceClient

    root = boot_stack[0]
    boundary = boot_stack[5]("unconstructed-storage")

    def failed(*args, **kwargs):
        raise ValueError("owned constructor failure")

    with monkeypatch.context() as patch:
        patch.setattr(PersistenceClient, "__init__", failed)
        with pytest.raises(ValueError):
            root.persistence(boot_stack[3], boundary, deadline(1))
    assert len(root._issued) == 1 and not root._clients
    result = RunClosure(root).close(deadline(3))
    assert result.cleanup_complete and not result.helpers[0].client_retained
    assert len(result.writers) == 1 and not result.writers[0].acknowledged
    assert result.writers[0].last_acknowledged_state == "unknown"
    retain(result, boot_stack, "constructor-failure")


@pytest.mark.parametrize("boot_stack", [{"allow_unacknowledged": True}], indirect=True)
def test_unacknowledged_original_birth_remains_unresolved_after_root_and_c1_cleanup(
    boot_stack,
):
    root = boot_stack[0]
    boundary = boot_stack[5]("unacknowledged-storage")
    signal.pidfd_send_signal(root._pidfd_capability.fileno(), signal.SIGSTOP)
    with pytest.raises(ValueError):
        root.persistence(boot_stack[3], boundary, deadline(0.1))
    result = RunClosure(root).close(deadline(3))
    assert result.root_reaped and result.unacknowledged_births == 1
    assert all(b.released for b in result.boundaries)
    assert not result.cleanup_complete and not result.helpers[0].process_reaped
    retain(result, boot_stack, "unacknowledged-birth")


def test_short_original_window_returns_unknown_without_a_new_cleanup_deadline(
    boot_stack,
):
    import time

    owner, storage, descriptor, launcher, handle, gate, original = boot_stack[6]()
    closer = RunClosure(boot_stack[0])
    until = deadline(0.15)
    began = time.monotonic()
    result = closer.close(until)
    assert time.monotonic() - began < 0.8  # Harness allowance, not a kernel guarantee.
    assert not result.cleanup_complete and closer.close(until) is result
    with pytest.raises(ClosureError):
        closer.close(deadline(2))
    retain(result, boot_stack, "short-window")


def test_cancel_bypasses_active_closure_locks_and_real_blocked_storage(boot_stack):
    import threading
    import time

    owner, storage, descriptor, launcher, handle, gate, original = boot_stack[6]()
    signal.pidfd_send_signal(storage.process._capability.fileno(), signal.SIGSTOP)
    closer = RunClosure(boot_stack[0])
    results, failures = [], []

    def closing():
        try:
            results.append(closer.close(deadline(4)))
        except Exception as error:
            failures.append(error)

    thread = threading.Thread(target=closing)
    thread.start()
    until = time.monotonic() + 1
    while not closer._lock.locked() and thread.is_alive() and time.monotonic() < until:
        time.sleep(0.005)
    assert closer._lock.locked() and boot_stack[0]._lock.locked()
    closer.cancel("owned-concurrent-cancel")
    thread.join(timeout=3)
    assert not thread.is_alive() and not failures
    assert results[0].cleanup_complete and not results[0].writers[0].acknowledged
    retain(results[0], boot_stack, "concurrent-cancel")


def test_active_dispatcher_normal_conflict_preserves_its_original_authority(
    request, monkeypatch
):
    from .test_dispatcher import full_stack, dispatcher

    stack = full_stack(request, monkeypatch)
    driver = dispatcher(stack)
    closer = RunClosure(stack[0], dispatcher=driver)
    driver._lock.acquire()
    try:
        with pytest.raises(ClosureError):
            closer.close(deadline(3))
        assert not stack[2].cancelled
        closer.cancel()
        assert stack[2].cancelled
    finally:
        driver._lock.release()


def test_controllerless_owned_unit_cleanup_uses_original_reverse_graph(
    boot_stack, monkeypatch
):
    from .test_provider import second
    from xverse.maestro.prbc import ProcessBoundaryOps

    facade, owner, first, launcher, handle, gate, original = runtime(boot_stack)
    second_unit, second_launcher, second_handle, second_gate = second(
        boot_stack, owner, original
    )
    facade.bind(second_launcher, second_handle)
    assert facade.start(first.unit_id, first, gate, original).ready
    assert facade.start(second_unit.unit_id, second_unit, second_gate, original).ready
    seen = []
    cleanup = ProcessBoundaryOps.force_cleanup

    def observed(self, descriptor, **kwargs):
        if descriptor.unit_id in owner._prepared.resource_order:
            seen.append(descriptor.unit_id)
        return cleanup(self, descriptor, **kwargs)

    monkeypatch.setattr(ProcessBoundaryOps, "force_cleanup", observed)
    result = RunClosure(boot_stack[0]).close(deadline(5))
    assert result.cleanup_complete
    assert seen[:2] == list(reversed(owner._prepared.resource_order))
    retain(result, boot_stack, "reverse-controllerless")


@pytest.mark.parametrize("reason", ["contains space", "x" * 65, "nonascii-é"])
def test_invalid_close_reason_rejects_before_unit_or_helper_mutation(
    boot_stack, reason
):
    closer = RunClosure(boot_stack[0])
    with pytest.raises(ValueError):
        closer.close(deadline(2), reason=reason)
    assert not boot_stack[2].cancelled


def test_invalid_original_adapter_alias_keeps_cleanup_only_root_and_c1_authority(
    boot_stack,
):
    owner, storage, descriptor, launcher, handle, gate, original = boot_stack[6]()
    real = launcher.process
    launcher.process = gate.process
    try:
        result = RunClosure(boot_stack[0]).close(deadline(4))
        assert result.root_reaped and all(b.released for b in result.boundaries)
        assert "ML-CLOSURE-ADAPTER-UNRESOLVED" in result.diagnostics
        assert all(h.process_reaped for h in result.helpers)
    finally:
        launcher.process = real
    retain(result, boot_stack, "invalid-original-alias")
