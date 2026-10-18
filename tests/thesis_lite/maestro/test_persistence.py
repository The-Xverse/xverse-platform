from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import sys
import time
import copy
import threading
import fcntl
import signal

import pytest

from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse.maestro.admission import PermitSession, permit_digest
from xverse.argus.writer import EvidenceRun
from xverse.maestro.owner import GateConnection, ReleaseOwner, StageSupervisor
from xverse.maestro.persistence import (
    _frame,
    PersistenceClient,
    encode_configuration,
    sealed_input_fd,
)
from xverse.maestro.prbc import BoundaryDescriptor
from xverse.maestro.time import HostDeadline
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_admission import context
from .test_boundary import environment as environment
from .test_boundary import native as native
from .test_releasegate import guard_binary as guard_binary


def deadline(seconds=3):
    return HostDeadline("host-session", time.monotonic() + seconds)


def configuration(tmp_path, manager):
    prepared, result, resources, bindings, approvals = context()
    now = datetime.now(timezone.utc)
    new_bindings, new_approvals = [], []
    for binding, approval in zip(bindings, approvals):
        permit = replace(
            binding.permit,
            not_before=now - timedelta(seconds=30),
            expires_at=now + timedelta(seconds=60),
        )
        new_bindings.append(replace(binding, generation=1, permit=permit))
        new_approvals.append(
            replace(
                approval,
                generation=1,
                permit_content_digest=permit_digest(permit),
                not_before=now - timedelta(seconds=30),
                expires_at=now + timedelta(seconds=60),
            )
        )
    return encode_configuration(
        prepared,
        result,
        resources,
        run_id="fixture-run",
        bindings=new_bindings,
        approvals=new_approvals,
        session="host-session",
        generation_deadline=manager._admission.teardown_deadline,
        journal_path=tmp_path / "m3.jsonl",
        evidence_root=tmp_path / "argus",
    )


@pytest.fixture
def storage(tmp_path, environment):
    factory, spawn, root = environment
    manager, latch = factory(seconds=30, run_id="fixture-run")
    config = configuration(tmp_path, manager)
    clients, children, gates = [], [], []

    def start(mode=None, override=None):
        selected = override or config
        parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        cfg = sealed_input_fd(selected)
        announce, announce_write = os.pipe()
        release_read, release = os.pipe()
        if mode:
            command = [
                sys.executable,
                "-I",
                str(Path(__file__).with_name("persistence_fixture.py")),
                str(child.fileno()),
                str(cfg),
                str(announce_write),
                str(release_read),
                mode,
            ]
            inherited = (child.fileno(), cfg, announce_write, release_read)
        else:
            command = [
                sys.executable,
                "-I",
                "-m",
                "xverse.maestro.persistence_worker",
                str(child.fileno()),
                str(cfg),
            ]
            inherited = (child.fileno(), cfg)
        try:
            process = subprocess.Popen(
                command,
                pass_fds=inherited,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        finally:
            child.close()
            os.close(cfg)
            os.close(announce_write)
            os.close(release_read)
        children.append((process, parent, announce, release))
        client = PersistenceClient(
            process,
            parent,
            selected,
            latch,
            deadline=deadline(1.5 if mode and mode.startswith("init") else 3),
        )
        clients.append(client)
        owner = ReleaseOwner.from_persistence(
            client, StageSupervisor(manager, latch), latch
        )
        return owner, client, announce, release

    def stage(owner, binary, fixture):
        unit_id = config.prepared.units[0].unit_id
        descriptor = BoundaryDescriptor("fixture-run", unit_id, 1, "remote-owned", 0)
        manager.create_frozen(descriptor)
        child, marker, line = spawn(fixture, manager, descriptor)
        assert line.startswith("CHILD ")
        parent, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        fd = manager._entries[descriptor.key].fd
        artifact = "sha256:" + hashlib.sha256(binary.read_bytes()).hexdigest()
        scope = owner.scope(unit_id, descriptor, artifact)
        until = time.monotonic_ns() + 4_000_000_000
        try:
            gate_process = subprocess.Popen(
                [
                    str(binary),
                    str(fd),
                    str(peer.fileno()),
                    str(config.generation_ns),
                    str(until),
                    "500000000",
                    scope.hex(),
                    "0",
                ],
                pass_fds=(fd, peer.fileno()),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        finally:
            peer.close()
        connection = GateConnection(
            gate_process,
            parent,
            scope=scope,
            epoch=0,
            lease_ns=until,
            artifact_digest=artifact,
            latch=latch,
            deadline=deadline(1),
        )
        gates.append(connection)
        return unit_id, descriptor, child, marker, connection

    yield start, stage, config, manager, latch
    for gate in gates:
        gate.cancel("test-teardown")
        gate.channel.close()
        gate.process.wait(timeout=2)
        gate.dispose()
    drain_observations = []
    external_disposals = 0
    for client in clients:
        if not client._failed and not client._aborted:
            client.abort(deadline(1))
        result = client.drain(deadline(1))
        drain_observations.append(
            {"worker_reaped": result.worker_reaped, "diagnostic": result.diagnostic}
        )
        if result.diagnostic == "ML-PERSIST-WAIT-UNRESOLVED":
            assert client.process.returncode is not None
            os.close(client._pidfd)
            client._pidfd = -1
            client.channel.close()
            external_disposals += 1
        else:
            assert result.worker_reaped
            client.dispose()
    reaped = []
    for process, channel, announce, release in children:
        channel.close()
        os.close(announce)
        os.close(release)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()  # Test bootstrap's original direct child only.
            process.wait(timeout=2)
            pytest.fail("external test bootstrap kill required")
        assert process.stderr.read() == b""
        process.stderr.close()
        reaped.append(process.pid)
    receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt_dir:
        (
            Path(receipt_dir)
            / (
                "persistence-children-"
                + str(os.getpid())
                + "-"
                + tmp_path.name
                + ".json"
            )
        ).write_text(
            json.dumps(
                {
                    "all_children_reaped": True,
                    "storage_children": len(reaped),
                    "gate_children": len(gates),
                    "drain_observations": drain_observations,
                    "external_local_pidfd_disposals": external_disposals,
                    "constructor_rejection_bootstrap_reaps": len(children)
                    - len(clients),
                }
            )
        )


def test_isolated_actual_m3_argus_to_native_release(
    storage, native, guard_binary, tmp_path, monkeypatch
):
    start, stage, config, manager, latch = storage
    owner, client, announce, release = start()
    unit_id = config.prepared.units[0].unit_id
    original = deadline(3)

    def denied(*args, **kwargs):
        raise AssertionError("supervisor attempted storage I/O")

    with monkeypatch.context() as patch:
        for target, method in [
            (EvidenceStore, "open_run"),
            (EvidenceRun, "append_event"),
            (EvidenceRun, "flush_buffer"),
            (FileEvidenceJournal, "__init__"),
            (PermitSession, "revalidate_start_intent"),
        ]:
            patch.setattr(target, method, denied)
        event_id = owner.commit_intent(unit_id, original)
        unit_id, descriptor, child, marker, gate = stage(owner, guard_binary, native)
        assert not select.select([marker], [], [], 0.02)[0]
        result = owner.release(unit_id, descriptor, gate, original)
        assert result.native_unfreeze_observed and not result.ready_for_execution
        assert select.select([marker], [], [], 1)[0] and os.read(marker, 1) == b"M"
    owner.cancel()
    assert manager.force_cleanup(descriptor).termination_observed
    assert child.wait(timeout=2) == 0
    assert client.abort(deadline(1)) == "failed"
    assert client.drain(deadline(1)).worker_reaped
    reader = EvidenceStore.read_run(tmp_path / "argus")
    records = reader.records()
    payload = records[0]["extensions"]["xverse.maestro"]
    assert records[0]["eventId"] == event_id
    public = FileEvidenceJournal(tmp_path / "m3.jsonl").public_records()[0]
    assert (
        payload["sourceRefs"][0]["sha256"]
        == "sha256:" + hashlib.sha256(canonical_bytes(public)).hexdigest()
    )
    assert reader.manifest["writerState"] == "failed"


@pytest.mark.parametrize(
    "mode",
    [
        "claim-fail",
        "append-fail",
        "flush-fail",
        "claim-hang",
        "append-hang",
        "flush-hang",
    ],
)
def test_storage_failure_or_hang_keeps_workload_silent_and_c1_usable(
    storage, native, guard_binary, mode
):
    start, stage, config, manager, latch = storage
    owner, client, announce, release = start(mode)
    unit_id, descriptor, child, marker, gate = stage(owner, guard_binary, native)
    began = time.monotonic()
    with pytest.raises(ValueError):
        owner.commit_intent(unit_id, deadline(1.2))
    elapsed = time.monotonic() - began
    assert elapsed < 2.5  # Harness allowance, not a production timing claim.
    assert select.select([announce], [], [], 0)[0]
    assert os.read(announce, 1) in (b"F", b"H")
    assert latch.cancelled and client._failed and not owner._claims
    assert not select.select([marker], [], [], 0.02)[0]
    assert manager.force_cleanup(descriptor).termination_observed
    assert child.wait(timeout=2) == 0
    result = client.drain(deadline(1))
    assert (
        result.worker_reaped
        and not result.cleanup_complete
        and not result.ready_for_execution
    )
    assert (
        client.last_writer_state == "open"
    )  # Last acknowledged state, no inferred durable closure.


def test_cancel_while_flush_is_blocked_returns_without_storage_lock(storage):
    start, stage, config, manager, latch = storage
    owner, client, announce, release = start("flush-hang")
    errors = []

    def commit():
        try:
            owner.commit_intent(config.prepared.units[0].unit_id, deadline(3))
        except Exception as error:
            errors.append(error)

    worker = threading.Thread(target=commit)
    worker.start()
    try:
        assert select.select([announce], [], [], 2)[0] and os.read(announce, 1) == b"H"
        owner.cancel("cancel-isolated-flush")
        assert latch.cancelled
    finally:
        worker.join(2)
    assert not worker.is_alive() and len(errors) == 1 and not owner._claims
    assert client.drain(deadline(1)).worker_reaped


@pytest.mark.parametrize("mode", ["init-hang", "init-fail"])
def test_initialization_failure_is_bounded_before_owner_exists(storage, mode):
    start, stage, config, manager, latch = storage
    began = time.monotonic()
    with pytest.raises(ValueError):
        start(mode)
    assert time.monotonic() - began < 3 and latch.cancelled


@pytest.mark.parametrize("mode", ["revalidate-hang", "revalidate-fail"])
def test_actual_revalidation_failure_prevents_native_release(
    storage, native, guard_binary, mode
):
    start, stage, config, manager, latch = storage
    owner, client, announce, release = start(mode)
    unit_id = config.prepared.units[0].unit_id
    original = deadline(1.5)
    owner.commit_intent(unit_id, original)
    unit_id, descriptor, child, marker, gate = stage(owner, guard_binary, native)
    with pytest.raises(ValueError):
        owner.release(unit_id, descriptor, gate, original)
    assert latch.cancelled and gate._sequence == 0
    assert not select.select([marker], [], [], 0.02)[0]
    assert manager.force_cleanup(descriptor).termination_observed
    assert child.wait(timeout=2) == 0
    assert client.drain(deadline(1)).worker_reaped


@pytest.mark.parametrize("mode", ["abort-hang", "abort-fail"])
def test_abort_failure_keeps_last_acknowledged_state_separate(storage, mode):
    start, stage, config, manager, latch = storage
    owner, client, announce, release = start(mode)
    with pytest.raises(ValueError):
        client.abort(deadline(0.4))
    assert client.last_writer_state == "open" and client._failed
    assert client.drain(deadline(1)).worker_reaped


def test_unresponsive_to_term_worker_is_killed_and_reaped(storage):
    start, stage, config, manager, latch = storage
    owner, client, announce, release = start("flush-ignoreterm")
    with pytest.raises(ValueError):
        owner.commit_intent(config.prepared.units[0].unit_id, deadline(1.2))
    result = client.drain(deadline(1))
    assert result.worker_reaped and result.returncode == -9 and client._kill_sent


def test_copied_claim_and_original_deadline_cannot_be_replaced(storage):
    start, stage, config, manager, latch = storage
    owner, client, announce, release = start()
    original = deadline(2)
    receipt = client.commit_intent(config.prepared.units[0].unit_id, original)
    with pytest.raises(ValueError, match="CLAIM"):
        client.revalidate_intent(replace(receipt), original)
    with pytest.raises(ValueError, match="CLAIM"):
        client.revalidate_intent(receipt, deadline(2.5))
    with pytest.raises(TypeError):
        copy.copy(client)
    client.revalidate_intent(receipt, original)


def test_conflicting_rpc_does_not_burn_unrelated_unit_attempt(storage):
    start, stage, config, manager, latch = storage
    owner, client, announce, release = start()
    unit = config.prepared.units[1].unit_id
    assert client._lock.acquire(False)
    try:
        with pytest.raises(ValueError, match="CONFLICT"):
            client.commit_intent(unit, deadline())
        assert unit not in client._attempted and not client._failed
    finally:
        client._lock.release()
    receipt = client.commit_intent(unit, deadline())
    assert receipt.unit_id == unit


def test_changed_private_xdl_is_rejected_before_storage_creation(storage, tmp_path):
    start, stage, config, manager, latch = storage
    body = json.loads(config.private_bytes)
    body["lifecycle_digest"] = "f" * 64
    changed = replace(config, private_bytes=canonical_bytes(body))
    with pytest.raises(ValueError):
        start(override=changed)
    assert not (tmp_path / "m3.jsonl").exists()
    assert not (tmp_path / "argus").exists()


def test_input_is_kernel_sealed_and_original_wait_loss_is_unresolved(storage):
    start, stage, config, manager, latch = storage
    fd = sealed_input_fd(config)
    try:
        assert fcntl.fcntl(fd, fcntl.F_GET_SEALS) & fcntl.F_SEAL_WRITE
        with pytest.raises(OSError):
            os.pwrite(fd, b"x", 0)
    finally:
        os.close(fd)
    owner, client, announce, release = start()
    client.abort(deadline(1))
    assert (
        client.process.wait(timeout=1) == 0
    )  # Deliberately violate exclusive waiter contract.
    result = client.drain(deadline(1))
    assert not result.worker_reaped and result.identity_retained
    assert result.diagnostic == "ML-PERSIST-WAIT-UNRESOLVED"


@pytest.mark.parametrize(
    "mode", ["foreign", "malformed", "rights", "mismatch", "eof", "timeout"]
)
def test_service_handshake_requires_actual_child_and_exact_frame(
    storage, mode, tmp_path
):
    start, stage, config, manager, latch = storage
    parent, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    scope = hashlib.sha256(config.private_bytes).hexdigest()
    wire = canonical_bytes(
        _frame("hello", 0, "", 0, "f" * 64 if mode == "mismatch" else scope, {})
    )
    helper = Path(__file__).with_name("persistence_peer.py")
    child = subprocess.Popen(
        [sys.executable, "-I", str(helper), str(peer.fileno()), mode, wire.hex()],
        pass_fds=(peer.fileno(),),
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        if mode == "foreign":
            peer.send(wire)
        peer.close()
        with pytest.raises(ValueError):
            PersistenceClient(child, parent, config, latch, deadline=deadline(0.8))
        assert latch.cancelled
    finally:
        peer.close()
        parent.close()
        child.stdin.close()
        child.wait(timeout=2)
    receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt_dir:
        (
            Path(receipt_dir)
            / ("persistence-peer-reaping-" + str(os.getpid()) + "-" + mode + ".json")
        ).write_text(
            json.dumps(
                {
                    "child_reaped": True,
                    "mode": mode,
                    "source_sha256": hashlib.sha256(helper.read_bytes()).hexdigest(),
                }
            )
        )


def test_worker_revalidates_actual_new_terminal_m3_outcome(storage, tmp_path):
    start, stage, config, manager, latch = storage
    owner, client, announce, release = start()
    original = deadline(2)
    receipt = client.commit_intent(config.prepared.units[0].unit_id, original)
    journal = FileEvidenceJournal(tmp_path / "m3.jsonl")
    journal.append(
        replace(
            journal.records[0],
            kind="outcome",
            sequence=0,
            status="stopped",
            permit_nonce=None,
        )
    )
    with pytest.raises(ValueError):
        client.revalidate_intent(receipt, original)
    assert latch.cancelled and client._failed
    assert client.drain(deadline(1)).worker_reaped


def test_fork_cannot_use_original_persistence_client(storage):
    start, stage, config, manager, latch = storage
    owner, client, announce, release = start()
    pid = os.fork()
    if pid == 0:
        try:
            client.commit_intent(config.prepared.units[0].unit_id, deadline())
        except ValueError:
            os._exit(0)
        os._exit(1)
    assert os.waitpid(pid, 0)[1] == 0
    assert not client._claims and not latch.cancelled
    receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt_dir:
        (
            Path(receipt_dir)
            / ("persistence-fork-reaping-" + str(os.getpid()) + ".json")
        ).write_text(json.dumps({"fork_child_reaped": True}))


def test_successful_abort_closes_shared_start_latch(storage):
    start, stage, config, manager, latch = storage
    owner, client, announce, release = start()
    assert not latch.cancelled
    assert client.abort(deadline(1)) == "failed"
    assert latch.cancelled and latch.reason == "persistence-aborted"
    with pytest.raises(ValueError):
        owner.commit_intent(config.prepared.units[0].unit_id, deadline())
    assert not owner._claims


def test_worker_loss_at_availability_check_closes_shared_latch(storage):
    start, stage, config, manager, latch = storage
    owner, client, announce, release = start()
    signal.pidfd_send_signal(client._pidfd, signal.SIGKILL)
    assert select.select([client._pidfd], [], [], 1)[0]
    with pytest.raises(ValueError):
        owner.commit_intent(config.prepared.units[0].unit_id, deadline())
    assert latch.cancelled and client._failed and not owner._claims
    assert client.drain(deadline(1)).worker_reaped
