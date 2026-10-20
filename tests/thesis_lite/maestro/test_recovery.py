"""Original issuer/journal reconstruction; no new Release or writer."""

from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import signal

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.recovery import IssuerRecovery, RecoveryError
from xverse.maestro.run_closure import RunClosure
from xverse.maestro.teardown import ReverseTeardown
from .test_bootstrap import (
    boot_stack as boot_stack,
    supervisor_binary as supervisor_binary,
)
from .test_boundary import environment as environment, native as native
from .test_launcher import binaries as binaries, deadline
from .test_provider import runtime, second


def started(stack, *, two=False):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(stack)
    if two:
        b, lb, hb, gb = second(stack, owner, original)
        facade.bind(lb, hb)
    assert facade.start(descriptor.unit_id, descriptor, gate, original).ready
    if two:
        assert facade.start(b.unit_id, b, gb, original).ready
    return facade, owner, descriptor, launcher, handle, gate, original


def reconciler(stack, facade, owner):
    return IssuerRecovery(
        stack[0],
        owner,
        policies=tuple(facade._policies.values()),
        operation_seconds=0.2,
    )


def retain(stack, result, name):
    output = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if output:
        from xverse_xdl.lifecycle import FileEvidenceJournal

        (Path(output) / f"recovery-public-{os.getpid()}-{name}.json").write_text(
            json.dumps(
                {
                    "result": asdict(result),
                    "events": EvidenceStore.read_run(
                        stack[4].parent / "argus"
                    ).records(),
                    "public_m3": FileEvidenceJournal(
                        stack[4].parent / "m3.jsonl"
                    ).public_records(),
                    "source_sha256": hashlib.sha256(
                        Path(__file__).read_bytes()
                    ).hexdigest(),
                }
            )
        )


def test_original_two_unit_recovery_retires_old_view_and_requires_new_health(
    boot_stack,
):
    facade, owner, a, launcher, handle, gate, original = started(boot_stack, two=True)
    old_sequence = facade._sequence
    before = EvidenceStore.read_run(boot_stack[4].parent / "argus").records()
    recovery = reconciler(boot_stack, facade, owner)
    active, terminal = deadline(1.5), deadline(7)
    result = recovery.reconcile(active, terminal)
    assert result.ordinary_reconciled and result.cleanup is None
    assert not result.fresh_ready and not result.lifecycle_complete
    assert recovery.view is not facade and not recovery.view.observations
    with pytest.raises(ValueError):
        facade.check_health(original, force=True)
    assert not owner.latch.cancelled
    assert all(
        v.ready and v.sequence > old_sequence
        for v in recovery.view.check_health(deadline(1), force=True)
    )
    after = EvidenceStore.read_run(boot_stack[4].parent / "argus").records()

    def count(events):
        return sum(
            e.get("extensions", {}).get("xverse.maestro", {}).get("action") == "started"
            for e in events
        )

    assert count(after) == count(before) == 2
    assert recovery.reconcile(active, terminal) is result
    with pytest.raises(RecoveryError):
        recovery.reconcile(deadline(1), terminal)
    closed = RunClosure(boot_stack[0], teardown=ReverseTeardown(recovery.view)).close(
        deadline(6)
    )
    assert closed.cleanup_complete and closed.normal_unit_records_complete
    retain(boot_stack, result, "normal")


def test_reconstructed_view_and_original_owner_never_reopen_start(boot_stack):
    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    recovery = reconciler(boot_stack, facade, owner)
    assert recovery.reconcile(deadline(1), deadline(7)).ordinary_reconciled
    with pytest.raises(ValueError):
        recovery.view.start(a.unit_id, a, gate, deadline(1))
    with pytest.raises(ValueError):
        owner.release(a.unit_id, a, gate, deadline(1))
    assert not owner.latch.cancelled
    assert recovery.view.check_health(deadline(1), force=True)[0].ready


def test_staged_handle_without_normal_durable_outcome_is_cleanup_only(boot_stack):
    facade, owner, a, launcher, handle, gate, original = runtime(boot_stack)
    result = reconciler(boot_stack, facade, owner).reconcile(deadline(1), deadline(7))
    assert not result.ordinary_reconciled and result.cleanup is not None
    assert result.cleanup.cleanup_complete and owner.latch.cancelled
    assert not (boot_stack[4] / "source-binding.marker").exists()
    retain(boot_stack, result, "staged")


@pytest.mark.parametrize("fault", ["journal", "mirror", "handle"])
def test_durable_or_exact_handle_loss_blocks_recovery_and_preserves_original_cleanup(
    boot_stack, fault
):
    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    if fault == "journal":
        (boot_stack[4].parent / "m3.jsonl").unlink()
    elif fault == "mirror":
        root = boot_stack[4].parent / "argus"
        for path in root.glob("*.jsonl"):
            path.unlink()
    else:
        launcher._handle = replace(handle, opaque_id="f" * 64)
    result = reconciler(boot_stack, facade, owner).reconcile(deadline(1), deadline(7))
    assert not result.ordinary_reconciled and result.cleanup is not None
    assert all(b.released for b in result.cleanup.boundaries)
    assert owner.latch.cancelled
    retain(boot_stack, result, fault)


@pytest.mark.parametrize("target", ["owner", "view", "root"])
def test_normal_recovery_conflict_has_no_retirement_or_cancellation(boot_stack, target):
    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    recovery = reconciler(boot_stack, facade, owner)
    lock = {"owner": owner._lock, "view": facade._lock, "root": boot_stack[0]._lock}[
        target
    ]
    lock.acquire()
    try:
        with pytest.raises(RecoveryError):
            recovery.reconcile(deadline(1), deadline(7))
        assert not owner.latch.cancelled and facade.observation(a.unit_id).ready
        recovery.cancel()
        assert owner.latch.cancelled
    finally:
        lock.release()


def test_real_original_native_query_stall_returns_unknown_and_cleanup_only(boot_stack):
    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    signal.pidfd_send_signal(launcher.process._capability.fileno(), signal.SIGSTOP)
    result = reconciler(boot_stack, facade, owner).reconcile(deadline(1), deadline(7))
    assert not result.ordinary_reconciled and result.cleanup is not None
    assert result.cleanup.root_reaped and all(
        b.released for b in result.cleanup.boundaries
    )
    assert not result.cleanup.cleanup_complete
    retain(boot_stack, result, "issuer-stall")


def test_changed_host_session_rejects_without_borrowing_old_freshness(boot_stack):
    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    recovery = reconciler(boot_stack, facade, owner)
    with pytest.raises(RecoveryError):
        recovery.reconcile(
            replace(deadline(1), session="new-host-session"), deadline(7)
        )
    assert not owner.latch.cancelled and facade.observation(a.unit_id).ready


@pytest.mark.parametrize(
    "mode", ["source", "handle", "epoch", "sample", "status", "extra", "unit"]
)
def test_bad_original_snapshot_ack_never_restores_an_observation_view(
    boot_stack, monkeypatch, mode
):
    from xverse.maestro.persistence import PersistenceClient

    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    recovery = reconciler(boot_stack, facade, owner)
    rpc = PersistenceClient._rpc

    def altered(self, kind, body, until):
        operation, end, result = rpc(self, kind, body, until)
        if kind == "recovery":
            result = json.loads(json.dumps(result))
            if mode == "source":
                result["rows"][0]["sources"][0]["sha256"] = "sha256:" + "f" * 64
            elif mode == "handle":
                result["rows"][0]["handle_digest"] = "sha256:" + "f" * 64
            elif mode == "epoch":
                result["view_epoch"] += 1
            elif mode == "sample":
                result["last_sample_sequence"] = True
            elif mode == "status":
                result["rows"][0]["permit_consumed"] = False
            elif mode == "extra":
                result["extra"] = True
            else:
                result["rows"][0]["unit"] = "foreign-unit"
        return operation, end, result

    monkeypatch.setattr(PersistenceClient, "_rpc", altered)
    result = recovery.reconcile(deadline(1), deadline(7))
    assert not result.ordinary_reconciled and recovery.view is None
    assert result.cleanup and all(b.released for b in result.cleanup.boundaries)
    assert owner.latch.cancelled
    retain(boot_stack, result, "bad-ack-" + mode)


def test_copied_active_recovery_statement_cannot_authorize_snapshot_rpc(
    boot_stack, monkeypatch
):
    from xverse.maestro.persistence import PersistenceClient
    from xverse.maestro.recovery import _RecoveryStatement

    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    recovery = reconciler(boot_stack, facade, owner)
    method = PersistenceClient.reconcile_snapshot

    def checked(self, controller, statement, until):
        before = self._sequence
        with pytest.raises(ValueError):
            method(self, controller, _RecoveryStatement(statement.body), until)
        assert self._sequence == before and not self._failed
        return method(self, controller, statement, until)

    monkeypatch.setattr(PersistenceClient, "reconcile_snapshot", checked)
    assert recovery.reconcile(deadline(1), deadline(7)).ordinary_reconciled


def test_reconstruction_calls_no_start_stage_claim_or_new_writer(
    boot_stack, monkeypatch
):
    from xverse.maestro.owner import ReleaseOwner
    from xverse.maestro.launcher import CatalogLauncher
    from xverse.maestro.bootstrap import BootstrapSession

    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    recovery = reconciler(boot_stack, facade, owner)

    def prohibited(*args, **kwargs):
        pytest.fail("recovery attempted a new mutation/creator")

    with monkeypatch.context() as patch:
        for cls, name in [
            (ReleaseOwner, "release"),
            (ReleaseOwner, "commit_intent"),
            (CatalogLauncher, "stage"),
            (BootstrapSession, "persistence"),
            (BootstrapSession, "catalog"),
            (BootstrapSession, "gate"),
        ]:
            patch.setattr(cls, name, prohibited)
        patch.setattr(EvidenceStore, "open_run", prohibited)
        assert recovery.reconcile(deadline(1), deadline(7)).ordinary_reconciled


def test_replacement_owner_cannot_adopt_original_issuer_objects(boot_stack):
    from xverse.maestro.owner import ReleaseOwner, StageSupervisor

    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    replacement = ReleaseOwner.from_persistence(
        owner.persistence, StageSupervisor(boot_stack[1], boot_stack[2]), boot_stack[2]
    )
    replacement._claims.update(owner._claims)
    replacement._launchers.update(owner._launchers)
    recovery = reconciler(boot_stack, facade, replacement)
    result = recovery.reconcile(deadline(1), deadline(7))
    assert not result.ordinary_reconciled and recovery.view is None
    assert result.cleanup and all(b.released for b in result.cleanup.boundaries)
    retain(boot_stack, result, "replacement-owner")


def test_actual_storage_stall_cannot_restore_old_positive_evidence(boot_stack):
    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    signal.pidfd_send_signal(
        owner.persistence.process._capability.fileno(), signal.SIGSTOP
    )
    recovery = reconciler(boot_stack, facade, owner)
    result = recovery.reconcile(deadline(1), deadline(7))
    assert not result.ordinary_reconciled and result.cleanup
    assert result.cleanup.cleanup_complete
    assert not result.cleanup.writers[0].acknowledged
    retain(boot_stack, result, "storage-stall")


def test_real_rpc_capacity_is_checked_before_retirement_on_both_sides(boot_stack):
    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    recovery = reconciler(boot_stack, facade, owner)
    import time
    from xverse.maestro.time import HostDeadline

    root = boot_stack[0]
    while owner.persistence._sequence < 126:
        if min(root._lease, gate.lease_ns) / 1e9 - time.monotonic() < 2:
            next_end = min(time.monotonic() + 4.8, root._generation / 1e9 - 2)
            if next_end > root._lease / 1e9:
                root.renew(HostDeadline(owner.session, next_end), deadline(0.5))
            gate_end = min(time.monotonic() + 4.5, root._lease / 1e9 - 0.1)
            if gate_end > gate.lease_ns / 1e9:
                gate.renew(HostDeadline(owner.session, gate_end), deadline(0.5))
        assert facade.check_health(deadline(1), force=True)[0].ready
    epoch = owner._view_epoch
    with pytest.raises(RecoveryError):
        recovery.reconcile(deadline(1), deadline(7))
    assert owner._view_epoch == epoch and not owner.latch.cancelled
    body = {
        "recovery_id": "a" * 32,
        "session": owner.session,
        "view_epoch": epoch + 1,
        "units": [
            {
                "unit": u.unit_id,
                "claim": owner._claims[u.unit_id].operation
                if u.unit_id in owner._claims
                else None,
                "handle": asdict(handle) if u.unit_id == a.unit_id else None,
            }
            for u in owner._prepared.units
        ],
    }
    with pytest.raises(ValueError):
        owner.persistence._rpc("recovery", body, deadline(1))
    assert owner.latch.cancelled
    assert RunClosure(boot_stack[0]).close(deadline(4)).cleanup_complete


def test_original_recovery_object_is_not_an_authority_after_fork(boot_stack):
    import copy

    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    recovery = reconciler(boot_stack, facade, owner)
    with pytest.raises((ValueError, TypeError)):
        copy.copy(recovery)
    pid = os.fork()
    if pid == 0:
        try:
            recovery.cancel()
        except ValueError:
            os._exit(0)
        os._exit(7)
    waited, status = os.waitpid(pid, 0)
    assert waited == pid and os.waitstatus_to_exitcode(status) == 0
    assert not owner.latch.cancelled
    directory = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if directory:
        (Path(directory) / f"recovery-fork-reaping-{os.getpid()}.json").write_text(
            json.dumps(
                {
                    "child_reaped": True,
                    "returncode": 0,
                    "source_sha256": hashlib.sha256(
                        Path(__file__).read_bytes()
                    ).hexdigest(),
                }
            )
        )


@pytest.mark.parametrize("operation", [True, 0, float("nan"), float("inf"), 5.1])
def test_invalid_recovery_operation_budget_has_no_effect(boot_stack, operation):
    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    with pytest.raises(ValueError):
        IssuerRecovery(
            boot_stack[0],
            owner,
            policies=tuple(facade._policies.values()),
            operation_seconds=operation,
        )
    assert not owner.latch.cancelled and facade.observation(a.unit_id).ready


def test_dead_original_native_issuer_never_becomes_replacement_ownership(boot_stack):
    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    signal.pidfd_send_signal(launcher.process._capability.fileno(), signal.SIGKILL)
    recovery = reconciler(boot_stack, facade, owner)
    result = recovery.reconcile(deadline(1), deadline(7))
    assert not result.ordinary_reconciled and recovery.view is None
    assert result.cleanup and result.cleanup.root_reaped
    assert all(b.released for b in result.cleanup.boundaries)
    assert not result.cleanup.cleanup_complete
    retain(boot_stack, result, "issuer-loss")


def test_recovery_lock_covers_failure_cleanup_and_cancel_remains_independent(
    boot_stack, monkeypatch
):
    import threading

    facade, owner, a, launcher, handle, gate, original = started(boot_stack)
    (boot_stack[4].parent / "m3.jsonl").unlink()
    recovery = reconciler(boot_stack, facade, owner)
    active, terminal = deadline(1.5), deadline(7)
    entered, release = threading.Event(), threading.Event()
    results, failures = [], []
    close = RunClosure.close

    def delayed(self, until, **kwargs):
        entered.set()
        if not release.wait(timeout=2):
            raise RuntimeError("owned test release missing")
        return close(self, until, **kwargs)

    monkeypatch.setattr(RunClosure, "close", delayed)

    def recovering():
        try:
            results.append(recovery.reconcile(active, terminal))
        except Exception as error:
            failures.append(error)

    thread = threading.Thread(target=recovering)
    thread.start()
    assert entered.wait(timeout=1)
    try:
        with pytest.raises(RecoveryError):
            recovery.reconcile(active, terminal)
        recovery.cancel("owned-recovery-cancel")
        assert owner.latch.cancelled
    finally:
        release.set()
        thread.join(timeout=3)
    assert not thread.is_alive() and not failures and results[0].cleanup
    retain(boot_stack, results[0], "concurrent-cleanup")
