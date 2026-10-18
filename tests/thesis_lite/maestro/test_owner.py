from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import copy
import threading
import sys
import time

import pytest
import jsonschema

from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse.maestro.admission import PermitSession, permit_digest
from xverse.maestro.owner import (
    GateConnection,
    OwnerError,
    ReleaseOwner,
    StageSupervisor,
)
from xverse.maestro.prbc import BoundaryDescriptor
from xverse.maestro.fence import GatePacket
from xverse.maestro.supervisor import CancellationLatch
from xverse.maestro.time import HostDeadline
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_admission import context
from .test_boundary import environment as environment
from .test_boundary import native as native
from .test_releasegate import guard_binary as guard_binary


def session(tmp_path, *, generation=1):
    prepared, result, resources, bindings, approvals = context()
    now = datetime.now(timezone.utc)
    bs, aps = [], []
    for b, a in zip(bindings, approvals):
        permit = replace(
            b.permit,
            not_before=now - timedelta(seconds=60),
            expires_at=now + timedelta(seconds=60),
        )
        bs.append(replace(b, generation=generation, permit=permit))
        aps.append(
            replace(
                a,
                generation=generation,
                permit_content_digest=permit_digest(permit),
                not_before=now - timedelta(seconds=60),
                expires_at=now + timedelta(seconds=60),
            )
        )
    return PermitSession(
        prepared,
        result,
        resources,
        run_id="fixture-run",
        bindings=bs,
        approvals=aps,
        now=now,
        journal=FileEvidenceJournal(tmp_path / "m3.jsonl"),
        initial_generation=generation,
    )


@pytest.fixture
def stack(tmp_path, environment):
    factory, spawn, root = environment
    permits = session(tmp_path)
    writer = EvidenceStore.open_run(
        tmp_path / "argus",
        run_id="fixture-run",
        plan=permits._result.plan,
        clocks={
            "host": {
                "domain": "host:host-session",
                "unit": "s",
                "value": time.monotonic(),
            },
            "utc": {
                "domain": "utc:host-session",
                "unit": "s",
                "value": datetime.now(timezone.utc).timestamp(),
            },
        },
    )
    manager, latch = factory(seconds=30, run_id="fixture-run")
    supervisor = StageSupervisor(manager, latch)
    owner = ReleaseOwner(permits, writer, supervisor, latch)
    children, connections = [], []

    def launch(binary, descriptor, lease=3):
        manager.create_frozen(descriptor)
        parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        artifact = "sha256:" + hashlib.sha256(Path(binary).read_bytes()).hexdigest()
        scope = owner.scope(descriptor.unit_id, descriptor, artifact)
        deadline_ns = time.monotonic_ns() + int(lease * 1e9)
        fd = manager._entries[descriptor.key].fd
        try:
            process = subprocess.Popen(
                [
                    str(binary),
                    str(fd),
                    str(child.fileno()),
                    str(
                        int(
                            manager._admission.teardown_deadline.monotonic_seconds * 1e9
                        )
                    ),
                    str(deadline_ns),
                    "500000000",
                    scope.hex(),
                    str(descriptor.creation_epoch),
                ],
                pass_fds=(fd, child.fileno()),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        finally:
            child.close()
        children.append((process, parent))
        connection = GateConnection(
            process,
            parent,
            scope=scope,
            epoch=descriptor.creation_epoch,
            lease_ns=deadline_ns,
            artifact_digest=artifact,
            latch=latch,
            deadline=HostDeadline("host-session", time.monotonic() + 1),
        )
        connections.append(connection)
        return connection

    yield owner, permits, writer, manager, spawn, launch
    owner.cancel()
    reaped = []
    for process, channel in children:
        channel.close()
        process.wait(timeout=3)
        reaped.append(process.pid)
    for connection in connections:
        connection.dispose()
    if writer.writer_state == "open":
        writer.abort(reason="owned integration test complete")
    receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt_dir:
        (
            Path(receipt_dir)
            / (
                "owner-native-reaping-"
                + str(os.getpid())
                + "-"
                + tmp_path.name
                + ".json"
            )
        ).write_text(
            json.dumps({"all_gate_children_reaped": True, "count": len(reaped)})
        )


def deadline(seconds=3):
    return HostDeadline("host-session", time.monotonic() + seconds)


def test_real_claim_flush_stage_and_credential_checked_release(
    stack, native, guard_binary
):
    owner, permits, writer, manager, spawn, launch = stack
    unit_id = permits._prepared.units[0].unit_id
    descriptor = BoundaryDescriptor("fixture-run", unit_id, 1, "owned-boundary", 0)
    start_deadline = deadline()
    event_id = owner.commit_intent(unit_id, start_deadline)
    assert len(permits._journal.records) == 1
    assert permits._journal.records[0].details["generation"] == 1
    manager.create_frozen(descriptor)
    child, marker, line = spawn(native, manager, descriptor)
    assert line.startswith("CHILD ")
    gate = launch(guard_binary, descriptor)
    assert not select.select([marker], [], [], 0.02)[0]
    result = owner.release(unit_id, descriptor, gate, start_deadline)
    assert result.native_unfreeze_observed and not result.ready_for_execution
    assert select.select([marker], [], [], 1)[0] and os.read(marker, 1) == b"M"
    with pytest.raises(OwnerError, match="CLAIM"):
        owner.release(unit_id, descriptor, gate, start_deadline)
    owner.cancel()
    gate.process.wait(timeout=2)
    assert manager.force_cleanup(descriptor).termination_observed
    assert child.wait(timeout=2) == 0
    manifest = writer.finalize()
    reader = EvidenceStore.read_run(writer._root)
    records = reader.records()
    assert records[0]["eventId"] == event_id
    payload = records[0]["extensions"]["xverse.maestro"]
    assert payload["action"] == "intent" and payload["generation"] == 1
    schema = json.loads(
        Path(__file__).with_name("lifecycle-payload-owner7.schema.json").read_text()
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(payload)
    public = permits._journal.public_records()[0]
    assert public["permitNonce"] == "withheld"
    assert payload["sourceRefs"][0]["sha256"] == (
        "sha256:" + hashlib.sha256(canonical_bytes(public)).hexdigest()
    )
    assert payload["sourceRefs"][0]["sequence"] == public["sequence"]
    text = reader.export_jsonl()
    assert "private-test-nonce" not in text and "permitNonce" not in payload
    assert manifest.writer_state == "closed"


def test_explicit_generation_one_and_original_receipt_revalidation(tmp_path):
    permits = session(tmp_path)
    receipt = permits.claim_start_intent(
        permits._prepared.units[0].unit_id, now=datetime.now(timezone.utc)
    )
    permits.revalidate_start_intent(receipt, now=datetime.now(timezone.utc))
    with pytest.raises(ValueError):
        permits.revalidate_start_intent(
            replace(receipt), now=datetime.now(timezone.utc)
        )


@pytest.mark.parametrize("fault", ["m3", "append", "flush"])
def test_durability_failure_never_registers_start_authority(stack, monkeypatch, fault):
    owner, permits, writer, manager, spawn, launch = stack

    def fail(*args, **kwargs):
        raise OSError("injected owned persistence failure")

    target, name = {
        "m3": (permits._journal, "claim_intent"),
        "append": (writer, "append_event"),
        "flush": (writer, "flush_buffer"),
    }[fault]
    with monkeypatch.context() as patch:
        patch.setattr(target, name, fail)
        with pytest.raises((OSError, ValueError)):
            owner.commit_intent(permits._prepared.units[0].unit_id, deadline())
    assert owner.latch.cancelled and not owner._claims
    assert len(permits._journal.records) == (0 if fault == "m3" else 1)
    with pytest.raises(OwnerError, match="CLOSED"):
        owner.commit_intent(permits._prepared.units[0].unit_id, deadline())


def test_late_actual_flush_does_not_register_authority(stack, monkeypatch):
    owner, permits, writer, manager, spawn, launch = stack
    actual = writer.flush_buffer
    original = deadline(1.5)
    flushed = []

    def slow_flush():
        actual()
        flushed.append(True)
        time.sleep(max(0, original.monotonic_seconds - time.monotonic()) + 0.03)

    with monkeypatch.context() as patch:
        patch.setattr(writer, "flush_buffer", slow_flush)
        with pytest.raises(OwnerError, match="DEADLINE"):
            owner.commit_intent(permits._prepared.units[0].unit_id, original)
    assert flushed == [True]
    assert owner.latch.cancelled and not owner._claims
    assert len(permits._journal.records) == 1
    writer.finalize()  # Seal this annotation-only test store for public readback.
    assert (
        EvidenceStore.read_run(writer._root).records()[0]["extensions"][
            "xverse.maestro"
        ]["action"]
        == "intent"
    )


def test_cancel_during_flush_does_not_wait_for_owner_lock(stack, monkeypatch):
    owner, permits, writer, manager, spawn, launch = stack
    entered, release = threading.Event(), threading.Event()
    actual = writer.flush_buffer
    errors = []

    def blocked_flush():
        actual()
        entered.set()
        assert release.wait(3)

    def commit():
        try:
            owner.commit_intent(permits._prepared.units[0].unit_id, deadline())
        except Exception as error:
            errors.append(error)

    with monkeypatch.context() as patch:
        patch.setattr(writer, "flush_buffer", blocked_flush)
        worker = threading.Thread(target=commit)
        worker.start()
        try:
            assert entered.wait(2)
            owner.cancel("test-cancel-during-flush")
            assert owner.latch.cancelled and worker.is_alive()
        finally:
            release.set()
            worker.join(3)
    assert not worker.is_alive() and len(errors) == 1
    assert not owner._claims and owner._closed


def staged(stack, native, guard_binary):
    owner, permits, writer, manager, spawn, launch = stack
    unit_id = permits._prepared.units[0].unit_id
    descriptor = BoundaryDescriptor("fixture-run", unit_id, 1, "owned-boundary", 0)
    manager.create_frozen(descriptor)
    child, marker, line = spawn(native, manager, descriptor)
    assert line.startswith("CHILD ")
    return unit_id, descriptor, child, marker, launch(guard_binary, descriptor)


@pytest.mark.parametrize(
    "condition", ["extended", "expired", "terminal", "missing", "copied"]
)
def test_release_requires_live_original_claim_and_deadline(
    stack, native, guard_binary, condition
):
    owner, permits, writer, manager, spawn, launch = stack
    unit_id, descriptor, child, marker, gate = staged(stack, native, guard_binary)
    original = deadline(1.5 if condition == "expired" else 2)
    if condition != "missing":
        owner.commit_intent(unit_id, original)
    if condition == "terminal":
        record = permits._journal.records[0]
        permits._journal.append(
            replace(
                record, kind="outcome", sequence=0, status="stopped", permit_nonce=None
            )
        )
    if condition == "copied":
        owner._claims[unit_id].receipt = replace(owner._claims[unit_id].receipt)
    if condition == "expired":
        time.sleep(max(0, original.monotonic_seconds - time.monotonic()) + 0.03)
    request = deadline(2.5) if condition in ("extended", "expired") else original
    with pytest.raises(ValueError):
        owner.release(unit_id, descriptor, gate, request)
    assert not select.select([marker], [], [], 0.03)[0]
    assert manager.force_cleanup(descriptor).termination_observed
    assert child.wait(timeout=2) == 0
    assert (
        not owner._claims.get(unit_id)
        or not owner._claims[unit_id].receipt.ready_for_execution
    )


@pytest.mark.parametrize(
    "change",
    ["journal", "permit-context", "writer", "supervisor", "gate-channel", "gate-scope"],
)
def test_replaced_original_authority_cannot_release(
    stack, native, guard_binary, tmp_path, change
):
    owner, permits, writer, manager, spawn, launch = stack
    unit_id, descriptor, child, marker, gate = staged(stack, native, guard_binary)
    original = deadline(2)
    owner.commit_intent(unit_id, original)
    restore = None
    if change == "journal":
        saved = permits._journal
        permits._journal = FileEvidenceJournal(tmp_path / "other.jsonl")

        def restore():
            return setattr(permits, "_journal", saved)
    elif change == "permit-context":
        saved = permits._run_id
        permits._run_id = "other-run"

        def restore():
            return setattr(permits, "_run_id", saved)
    elif change == "writer":
        saved = writer._plan_block
        writer._plan_block = dict(saved, digest="sha256:" + "f" * 64)

        def restore():
            return setattr(writer, "_plan_block", saved)
    elif change == "supervisor":
        saved = owner.supervisor.boundaries
        owner.supervisor.boundaries = object()

        def restore():
            return setattr(owner.supervisor, "boundaries", saved)
    elif change == "gate-channel":
        saved = gate.channel
        duplicate = socket.socket(fileno=os.dup(saved.fileno()))
        gate.channel = duplicate

        def restore():
            gate.channel = saved
            duplicate.close()
    else:
        saved = gate.scope
        gate.scope = b"f" * 32

        def restore():
            return setattr(gate, "scope", saved)

    try:
        with pytest.raises((ValueError, AttributeError)):
            owner.release(unit_id, descriptor, gate, original)
        assert not select.select([marker], [], [], 0.02)[0]
    finally:
        restore()
    owner.cancel()
    assert manager.force_cleanup(descriptor).termination_observed
    assert child.wait(timeout=2) == 0


def test_empty_frozen_boundary_is_not_a_stage_ack(stack, guard_binary):
    owner, permits, writer, manager, spawn, launch = stack
    unit_id = permits._prepared.units[0].unit_id
    descriptor = BoundaryDescriptor("fixture-run", unit_id, 1, "empty-boundary", 0)
    original = deadline()
    owner.commit_intent(unit_id, original)
    gate = launch(guard_binary, descriptor)
    with pytest.raises(OwnerError, match="STAGE"):
        owner.release(unit_id, descriptor, gate, original)
    assert owner.latch.cancelled and gate._sequence == 0
    cleanup = manager.force_cleanup(descriptor)
    assert cleanup.boundary_released and cleanup.residual_count == 0
    assert not cleanup.termination_observed


def test_public_projection_is_genuine_redacted_and_detached(tmp_path):
    permits = session(tmp_path)
    receipt = permits.claim_start_intent(
        permits._prepared.units[0].unit_id, now=datetime.now(timezone.utc)
    )
    public = permits.public_start_intent(receipt, now=datetime.now(timezone.utc))
    assert public == permits._journal.public_records()[0]
    assert public["permitNonce"] == "withheld"
    public["details"]["generation"] = 99
    assert permits._journal.public_records()[0]["details"]["generation"] == 1
    with pytest.raises(ValueError, match="RECEIPT"):
        permits.public_start_intent(replace(receipt), now=datetime.now(timezone.utc))


def test_generation_zero_session_is_not_runtime_release_authority(stack, tmp_path):
    owner, permits, writer, manager, spawn, launch = stack
    zero = session(tmp_path / "zero", generation=0)
    with pytest.raises(OwnerError, match="SCOPE"):
        ReleaseOwner(zero, writer, owner.supervisor, owner.latch)
    with pytest.raises(TypeError):
        copy.copy(owner)
    pid = os.fork()
    if pid == 0:
        try:
            owner.commit_intent(permits._prepared.units[0].unit_id, deadline())
        except OwnerError:
            os._exit(0)
        os._exit(1)
    assert os.waitpid(pid, 0)[1] == 0
    assert not permits._journal.records


@pytest.mark.parametrize(
    "mode", ["foreign", "malformed", "rights", "mismatch", "timeout"]
)
def test_gate_ready_requires_actual_child_credentials_and_exact_packet(tmp_path, mode):
    parent, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    scope = b"s" * 32
    until = time.monotonic_ns() + 2_000_000_000
    wire = GatePacket(
        16, 0, until, b"x" * 32 if mode == "mismatch" else scope, 0
    ).encode()
    script = Path(__file__).with_name("owner_peer.py")
    process = subprocess.Popen(
        [sys.executable, "-I", str(script), str(peer.fileno()), mode, wire.hex()],
        pass_fds=(peer.fileno(),),
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    latch = CancellationLatch()
    try:
        if mode == "foreign":
            peer.send(wire)  # Same bytes/socket, wrong kernel sender identity.
        peer.close()
        with pytest.raises(ValueError):
            GateConnection(
                process,
                parent,
                scope=scope,
                epoch=0,
                lease_ns=until,
                artifact_digest="sha256:"
                + hashlib.sha256(script.read_bytes()).hexdigest(),
                latch=latch,
                deadline=deadline(0.3),
            )
        assert latch.cancelled
    finally:
        peer.close()
        parent.close()
        process.stdin.close()
        assert process.wait(timeout=2) == 0
    receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt_dir:
        (
            Path(receipt_dir)
            / ("owner-peer-reaping-" + str(os.getpid()) + "-" + mode + ".json")
        ).write_text(
            json.dumps(
                {
                    "all_peer_children_reaped": True,
                    "mode": mode,
                    "source_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
                }
            )
        )


def test_cancel_targets_original_latch_after_public_alias_replacement(stack):
    owner, permits, writer, manager, spawn, launch = stack
    original = owner.latch
    foreign = CancellationLatch()
    owner.latch = foreign
    try:
        owner.cancel("original-latch-test")
        assert original.cancelled and not foreign.cancelled
    finally:
        owner.latch = original


def test_public_intent_projection_loss_closes_claims(tmp_path, monkeypatch):
    permits = session(tmp_path)
    receipt = permits.claim_start_intent(
        permits._prepared.units[0].unit_id, now=datetime.now(timezone.utc)
    )
    monkeypatch.setattr(permits._journal, "public_records", lambda: ())
    with pytest.raises(ValueError, match="DURABILITY"):
        permits.public_start_intent(receipt, now=datetime.now(timezone.utc))
    assert permits.claims_closed and len(permits._journal.records) == 1
