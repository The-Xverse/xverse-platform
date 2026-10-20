"""Actual durable M3/Argus records; no in-memory writer substitutes."""

from dataclasses import replace
import hashlib
import json
import fcntl
import os
import time

import pytest
from jsonschema import Draft202012Validator
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse_xdl.lifecycle import FileEvidenceJournal
from xverse.maestro.lifecycle_evidence import LifecycleReceipt
from xverse.maestro.owner import GateConnection
from xverse.maestro.time import HostDeadline
from xverse.maestro.launcher import CatalogLauncher
from .test_provider import runtime, second
from .test_bootstrap import (
    boot_stack as boot_stack,
    supervisor_binary as supervisor_binary,
)
from .test_boundary import environment as environment, native as native
from .test_launcher import binaries as binaries


def records(stack):
    root = stack[4].parent
    return FileEvidenceJournal(
        root / "m3.jsonl"
    ).public_records(), EvidenceStore.read_run(root / "argus").records()


def test_real_start_probe_and_dependency_records_before_ready_return(boot_stack):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    b, lb, hb, gb = second(boot_stack, owner, original)
    facade.bind(lb, hb)
    ready = facade.start(descriptor.unit_id, descriptor, gate, original)
    receipt = owner.persistence.probe_receipt(descriptor.unit_id)
    assert type(receipt) is LifecycleReceipt
    assert receipt.sample_sequence == ready.sequence and not receipt.lifecycle_complete
    m3, events = records(boot_stack)
    unit_records = [r for r in m3 if r["executionId"] == handle.execution_id]
    assert unit_records[0]["kind"] == "intent"
    assert sum(r["kind"] == "outcome" for r in unit_records) == 1
    assert (
        unit_records[-1]["kind"] == "observation"
        and unit_records[-1]["status"] == "running"
    )
    actions = [r["extensions"]["xverse.maestro"]["action"] for r in events]
    assert actions[:2] == ["intent", "intent"]
    assert actions[-3:] == ["started", "probe", "ready"]
    assert all(action == "probe" for action in actions[2:-3])
    assert all(
        r["causationId"]
        for r in events
        if r["extensions"]["xverse.maestro"]["action"] != "intent"
    )
    assert facade.start(b.unit_id, b, gb, original).ready
    m3, events = records(boot_stack)
    target = [
        r
        for r in events
        if r["extensions"]["xverse.maestro"]["unitId"] == b.unit_id
        and r["extensions"]["xverse.maestro"]["action"] == "started"
    ][0]
    deps = target["extensions"]["xverse.maestro"]["dependencies"]
    assert (
        len(deps) == 1
        and deps[0]["unitId"] == descriptor.unit_id
        and deps[0]["generation"] == 1
    )
    source_event = next(e for e in events if e["eventId"] == deps[0]["probeEventId"])
    assert source_event["ingestionOrdinal"] < target["ingestionOrdinal"]
    assert source_event["extensions"]["xverse.maestro"]["action"] == "health"
    assert len([r for r in m3 if r["kind"] == "outcome"]) == 2


def test_public_source_hashes_and_payload_schema_match_actual_records(boot_stack):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    assert facade.start(descriptor.unit_id, descriptor, gate, original).ready
    facade.check_health(original, force=True)
    m3, events = records(boot_stack)
    schema = json.loads(
        (
            __import__("pathlib")
            .Path(__file__)
            .with_name("lifecycle-payload-v2.schema.json")
        ).read_text()
    )
    validator = Draft202012Validator(schema)
    for event in events:
        payload = event["extensions"]["xverse.maestro"]
        validator.validate(payload)
        for reference in payload["sourceRefs"]:
            if reference["kind"] == "m3-record":
                record = next(r for r in m3 if r["sequence"] == reference["sequence"])
                assert (
                    reference["sha256"]
                    == "sha256:" + hashlib.sha256(canonical_bytes(record)).hexdigest()
                )
    encoded = json.dumps(events)
    for private in (
        handle.opaque_id,
        handle.resource_identity,
        "private-process-nonce-",
        "MAESTRO_VISIBLE",
        "declared-image",
    ):
        assert private not in encoded
    assert [r["extensions"]["xverse.maestro"]["action"] for r in events].count(
        "started"
    ) == 1
    assert events[-1]["extensions"]["xverse.maestro"]["action"] == "health"


@pytest.mark.parametrize("mode", ["copy", "changed", "duplicate", "foreign-session"])
def test_only_exact_current_observation_can_be_recorded(boot_stack, mode):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    observed = facade.start(descriptor.unit_id, descriptor, gate, original)
    before = owner.persistence._sequence
    forged = observed
    if mode == "copy":
        forged = replace(observed)
    elif mode == "changed":
        forged = replace(observed, sequence=observed.sequence + 1)
    elif mode == "foreign-session":
        forged = replace(observed, host_session="foreign")
    with pytest.raises(ValueError):
        owner.persistence.record_probe(facade, forged, original)
    assert owner.persistence._sequence == before


def test_pending_exec_has_probe_record_without_false_started_credit(
    boot_stack, monkeypatch
):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    observe = CatalogLauncher.observe

    def pending(self, handle, until):
        return replace(observe(self, handle, until), exec_pipe_closed=False)

    monkeypatch.setattr(CatalogLauncher, "observe", pending)
    with pytest.raises(ValueError):
        facade.start(descriptor.unit_id, descriptor, gate, original)
    m3, events = records(boot_stack)
    assert not any(r["kind"] == "outcome" for r in m3)
    probes = [
        r for r in events if r["extensions"]["xverse.maestro"]["action"] == "probe"
    ]
    assert len(probes) == 3 and all(
        r["extensions"]["xverse.maestro"]["outcome"] == "failed" for r in probes
    )
    assert not any(
        r["extensions"]["xverse.maestro"]["action"] in ("started", "ready")
        for r in events
    )


@pytest.mark.parametrize("fault", ["journal-loss", "journal-history", "argus-loss"])
def test_original_durable_history_loss_blocks_new_ready(boot_stack, monkeypatch, fault):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    root = boot_stack[4].parent
    exchange = GateConnection.exchange
    changed = []

    def lose_after_release(self, packet, expected, until):
        reply = exchange(self, packet, expected, until)
        if self is gate and packet.kind == 4 and not changed:
            changed.append(True)
            if fault == "journal-loss":
                (root / "m3.jsonl").rename(root / "saved-m3.jsonl")
                (root / "m3.jsonl").mkdir()
            elif fault == "journal-history":
                rows = (root / "m3.jsonl").read_text().splitlines()
                data = json.loads(rows[0])
                data["status"] = "changed"
                (root / "m3.jsonl").write_text(json.dumps(data) + "\n")
            else:
                (root / "argus" / "events.jsonl").rename(
                    root / "argus" / "saved-events.jsonl"
                )
        return reply

    monkeypatch.setattr(GateConnection, "exchange", lose_after_release)
    with pytest.raises(ValueError):
        facade.start(descriptor.unit_id, descriptor, gate, original)
    assert boot_stack[2].cancelled and not any(o.ready for o in facade.observations)
    assert not owner.persistence.probe_receipt(descriptor.unit_id)


def test_real_journal_lock_after_release_times_out_without_ready(
    boot_stack, monkeypatch
):
    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    locked = os.open(boot_stack[4].parent / "m3.jsonl.lock", os.O_RDWR)
    exchange = GateConnection.exchange

    def block_after_release(self, packet, expected, until):
        value = exchange(self, packet, expected, until)
        if self is gate and packet.kind == 4:
            fcntl.flock(locked, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return value

    monkeypatch.setattr(GateConnection, "exchange", block_after_release)
    began = time.monotonic()
    try:
        with pytest.raises(ValueError):
            facade.start(
                descriptor.unit_id,
                descriptor,
                gate,
                HostDeadline(owner.session, began + 0.4),
            )
    finally:
        fcntl.flock(locked, fcntl.LOCK_UN)
        os.close(locked)
    assert time.monotonic() - began < 1.5
    assert boot_stack[2].cancelled and not any(o.ready for o in facade.observations)
    assert not owner.persistence.probe_receipt(descriptor.unit_id)


@pytest.mark.parametrize(
    "mode",
    [
        "action",
        "outcome",
        "source",
        "clock",
        "dependency",
        "causation",
        "extra",
        "sequence",
        "producer",
    ],
)
def test_substituted_actual_worker_ack_never_returns_ready(
    boot_stack, monkeypatch, mode
):
    from xverse.maestro.persistence import PersistenceClient

    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    rpc = PersistenceClient._rpc

    def altered(self, kind, body, deadline):
        operation, until, result = rpc(self, kind, body, deadline)
        if self is owner.persistence and kind == "probe":
            event = result["events"][0]
            payload = event["extensions"]["xverse.maestro"]
            if mode == "action":
                payload["action"] = "cleanup"
            elif mode == "outcome":
                payload["outcome"] = "unknown"
            elif mode == "source":
                payload["sourceRefs"][0]["sequence"] = 9999
            elif mode == "clock":
                event["clocks"]["host"]["domain"] = "host:foreign"
            elif mode == "dependency":
                payload["dependencies"] = [
                    {"unitId": "foreign", "generation": 1, "probeEventId": "foreign"}
                ]
            elif mode == "causation":
                event["causationId"] = "foreign"
            elif mode == "extra":
                payload["unexpected"] = True
            elif mode == "producer":
                event["producerSequence"] = 999
            else:
                result["m3_sequences"] = [True]
        return operation, until, result

    monkeypatch.setattr(PersistenceClient, "_rpc", altered)
    with pytest.raises(ValueError):
        facade.start(descriptor.unit_id, descriptor, gate, original)
    assert boot_stack[2].cancelled and not any(o.ready for o in facade.observations)
    assert not owner.persistence.probe_receipt(descriptor.unit_id)


@pytest.mark.parametrize("mode", ["append-fail", "flush-fail", "flush-hang"])
def test_original_storage_worker_failure_after_release_never_returns_ready(
    boot_stack, mode
):
    from pathlib import Path
    import socket
    import subprocess
    import sys
    from xverse.maestro.persistence import PersistenceClient, sealed_input_fd
    from xverse.maestro.owner import ReleaseOwner, StageSupervisor
    from xverse.maestro.launcher import make_launch_recipe
    from xverse.maestro.providers import ProcessReadiness, ProbePolicy
    from .test_launcher import deadline

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
        descriptor = boundary("fault-workload", unit)
        recipe = make_launch_recipe(
            owner,
            descriptor,
            environment={"MAESTRO_VISIBLE": "declared"},
            helper_artifact_digest=owner._unit(unit).provider.artifact_digest,
            deadline=original,
        )
        launcher = session.catalog(owner, recipe, boundary("fault-launcher"), original)
        clients.append(launcher)
        handle = launcher.stage(original)
        gate = session.gate(
            owner,
            descriptor,
            boundary("fault-gate"),
            original,
            lease_ns=min(session._lease, time.monotonic_ns() + 3_000_000_000),
        )
        clients.append(gate)
        facade = ProcessReadiness(
            owner,
            policies=tuple(
                ProbePolicy(u.unit_id, 2, 0.5, 1) for u in config.prepared.units
            ),
        )
        facade.bind(launcher, handle)
        began = time.monotonic()
        with pytest.raises(ValueError):
            facade.start(unit, descriptor, gate, deadline(0.4))
        assert time.monotonic() - began < 1.5
        assert latch.cancelled and not any(o.ready for o in facade.observations)
        assert storage.drain(deadline(1)).worker_reaped
        assert (
            storage.last_writer_state == "open"
        )  # Last ACK, not inferred durable closure.
        journal = FileEvidenceJournal(work.parent / "m3.jsonl").records
        assert any(r.kind in ("outcome", "observation") for r in journal)
        assert storage.probe_receipt(unit) is None
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
                / ("outcome-fault-worker-" + str(process.pid) + ".json")
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
