"""Actual original storage+AFFA composition; full admission/restart remain open."""

import copy
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys

import pytest
from xverse.argus import EvidenceStore
from xverse_xdl.lifecycle import FileEvidenceJournal
from xverse.maestro.bootstrap import (
    BootstrapAdmission,
    BootstrapSession,
    encode_bootstrap,
    sealed_bootstrap_fd,
    seal_helper_image,
)
from xverse.maestro.run_broker import RunBroker, UnitAdmission
from xverse.maestro.providers import ProcessReadiness, ProbePolicy
from xverse.maestro.prbc import BoundaryDescriptor
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary, digest
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, configured, deadline


@pytest.fixture
def broker_stack(
    environment, binaries, authority_binary, run_bootstrap_binary, tmp_path
):
    factory, _, _ = environment
    manager, latch = factory(seconds=45, run_id="fixture-run")
    config, pin, work = configured(
        tmp_path, manager, dict(binaries, launcher=authority_binary)
    )
    images = tuple(
        seal_helper_image(
            p,
            digest="sha256:" + digest(p.read_bytes()).hex(),
            argv0=sys.executable if p == Path(sys.executable).resolve() else str(p),
        )
        for p in (
            binaries["launcher"],
            binaries["bound-gate"],
            Path(sys.executable).resolve(),
            authority_binary,
        )
    )
    admission = BootstrapAdmission(
        "fixture-run",
        config.prepared.lifecycle_digest,
        "bootstrap-approval",
        "sha256:" + digest(b"owned-environment").hex(),
        "sha256:" + digest(run_bootstrap_binary.read_bytes()).hex(),
        manager._admission.teardown_deadline,
        deadline(4.8),
        images[:3],
        images[3],
        manager._root_fd,
    )
    boot = encode_bootstrap(admission)
    private = sealed_bootstrap_fd(boot)
    channel, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    channel.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    process = subprocess.Popen(
        [str(run_bootstrap_binary), str(peer.fileno()), str(private)],
        pass_fds=(
            peer.fileno(),
            private,
            manager._root_fd,
            *(i.descriptor for i in images),
        ),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    peer.close()
    os.close(private)
    session = storage = broker = None

    def boundary(name, unit):
        descriptor = BoundaryDescriptor("fixture-run", unit, 1, name, 0)
        manager.create_frozen(descriptor)
        return descriptor

    try:
        session = BootstrapSession(
            process, channel, boot, manager, latch, deadline=deadline(2)
        )
        storage = session.persistence(
            config, boundary("storage", "helper:storage"), deadline(2)
        )
        units = tuple(
            UnitAdmission(
                boundary("unit-" + str(i), u.unit_id),
                (("MAESTRO_VISIBLE", "declared"),),
                3,
            )
            for i, u in enumerate(config.prepared.units)
        )
        helper = boundary("authority", "helper:authority")
        broker = RunBroker.admit(session, storage, units, helper, deadline=deadline(2))
        facade = ProcessReadiness(
            broker.owner,
            policies=tuple(
                ProbePolicy(u.unit_id, 2, 0.5, 0.5) for u in config.prepared.units
            ),
        )
        yield broker, facade, storage, work
    finally:
        if broker:
            broker.cancel("owned-broker-teardown")
        if storage:
            if not storage._failed and not storage._aborted:
                try:
                    storage.abort(deadline(1))
                except (ValueError, OSError):
                    storage._fail()
            assert storage.drain(deadline(1)).worker_reaped
        if session:
            session.cancel("owned-broker-fixture-teardown")
            result = session.drain(deadline(1.8))
            assert result.supervisor_reaped and result.registered_children_reaped
            assert not result.unacknowledged_births
            if broker:
                broker.dispose()
            for client in session._clients.values():
                client.dispose()
            session.dispose()
        else:
            process.wait(timeout=3)
            channel.close()
        process.wait(timeout=1)
        assert process.stderr.read() == b""
        process.stderr.close()
        for entry in manager._entries.values():
            if entry.state != "released":
                result = manager.force_cleanup(entry.descriptor)
                assert result.boundary_released and result.residual_count == 0
        for image in images:
            os.close(image.descriptor)
        output = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
        if output and session:
            Path(output).mkdir(parents=True, exist_ok=True)
            (Path(output) / ("run-broker-waits-" + tmp_path.name + ".json")).write_text(
                json.dumps(
                    dict(
                        bootstrap_reaped=True,
                        registered_helpers_reaped=True,
                        storage_reaped=True,
                        helper_count=len(session._children),
                        original_C1_released=True,
                        full_M1_complete=False,
                    )
                )
            )


def stage_all(stack):
    broker, facade, storage, work = stack
    end = deadline(3)
    for unit in broker.owner._prepared.units:
        broker.owner.commit_intent(unit.unit_id, end)
    for issuer in broker.issuers:
        handle = issuer.stage(end)
        facade.bind(issuer, handle)
    return end


def test_actual_two_unit_global_release_and_durable_outcomes(broker_stack, monkeypatch):
    broker, facade, storage, work = broker_stack

    def forbidden(*args, **kwargs):
        pytest.fail("coordinator Popen during broker lifecycle")

    with monkeypatch.context() as patch:
        patch.setattr(subprocess, "Popen", forbidden)
        end = stage_all(broker_stack)
        for unit in broker.owner._prepared.resource_order:
            issuer = broker.issuer(unit)
            assert facade.start(
                unit, issuer.recipe.descriptor, broker.connection, end
            ).ready
    m3 = FileEvidenceJournal(work.parent / "m3.jsonl").public_records()
    assert sum(r["kind"] == "outcome" for r in m3) == 2
    events = EvidenceStore.read_run(work.parent / "argus").records()
    started = [
        e for e in events if e["extensions"]["xverse.maestro"]["action"] == "started"
    ]
    assert len(started) == 2
    assert started[1]["extensions"]["xverse.maestro"]["dependencies"]
    assert len(broker.connection._pidfds) == 2
    assert all(
        (work / (i.owner._unit(i.unit_id).binding_id + ".marker")).read_bytes()
        == b"EXEC\n"
        for i in broker.issuers
    )


def test_mirror_loss_before_stage_revokes_without_workload_birth(broker_stack):
    broker, _, _, work = broker_stack
    unit = broker.owner._prepared.units[0].unit_id
    broker.owner.commit_intent(unit, deadline(2))
    path = work.parent / "argus" / "events.jsonl"
    path.rename(path.with_name("saved-events.jsonl"))
    with pytest.raises(ValueError):
        broker.issuer(unit).stage(deadline(1))
    assert broker.owner.latch.cancelled and not broker.connection._pidfds
    assert not list(work.glob("*.marker"))


def test_cancel_fences_both_already_staged_units(broker_stack):
    broker, facade, _, work = broker_stack
    end = stage_all(broker_stack)
    result = broker.cancel("before-release")
    assert result.native_epoch_confirmed and result.frozen_units == 3
    for issuer in broker.issuers:
        with pytest.raises(ValueError):
            facade.start(
                issuer.unit_id, issuer.recipe.descriptor, broker.connection, end
            )
    assert not list(work.glob("*.marker"))


def test_worker_stall_does_not_hold_independent_native_cancel(broker_stack):
    import threading

    broker, _, storage, work = broker_stack
    unit = broker.owner._prepared.units[0].unit_id
    end = deadline(2)
    broker.owner.commit_intent(unit, end)
    signal.pidfd_send_signal(storage.process._capability.fileno(), signal.SIGSTOP)
    entered = threading.Event()
    original = storage.revalidate_intent
    errors = []

    def blocked(*args, **kwargs):
        entered.set()
        return original(*args, **kwargs)

    storage.revalidate_intent = blocked

    def stage():
        try:
            broker.issuer(unit).stage(end)
        except ValueError as error:
            errors.append(str(error))

    thread = threading.Thread(target=stage)
    thread.start()
    try:
        assert entered.wait(1)
        result = broker.cancel("worker-stall")
        assert result.native_epoch_confirmed or result.issuer_reaped
    finally:
        thread.join(3)
    assert not thread.is_alive() and errors
    assert not broker.connection._pidfds and not list(work.glob("*.marker"))


def test_original_issuer_and_registry_cannot_be_reconstructed(broker_stack):
    broker, _, _, _ = broker_stack
    end = stage_all(broker_stack)
    issuer = broker.issuers[0]
    with pytest.raises(TypeError):
        copy.copy(issuer)
    from dataclasses import replace

    with pytest.raises(ValueError):
        issuer.observe(replace(issuer._handle), end)


def test_dependent_direct_release_requires_original_active_guard(broker_stack):
    broker, _, _, work = broker_stack
    end = stage_all(broker_stack)
    sink = broker.issuer(broker.owner._prepared.resource_order[-1])
    with pytest.raises(ValueError):
        broker.owner.release(
            sink.unit_id, sink.recipe.descriptor, broker.connection, end
        )
    assert not (work / (sink.owner._unit(sink.unit_id).binding_id + ".marker")).exists()


@pytest.mark.parametrize("field", ["recipe", "handle"])
def test_issued_metadata_cannot_be_relabelled(broker_stack, field):
    from dataclasses import replace

    broker, _, _, _ = broker_stack
    stage_all(broker_stack)
    issuer = broker.issuers[0]
    if field == "recipe":
        issuer.recipe = replace(issuer.recipe, execution_id="forged")
    else:
        issuer._handle = replace(issuer._handle, execution_id="forged")
    with pytest.raises(ValueError):
        issuer.revalidate_issued(issuer._handle)


@pytest.mark.parametrize("fault", ["mirror", "journal"])
def test_actual_durable_loss_before_release_prevents_execution(broker_stack, fault):
    broker, facade, _, work = broker_stack
    end = stage_all(broker_stack)
    original = (
        work.parent / "argus" / "events.jsonl"
        if fault == "mirror"
        else work.parent / "m3.jsonl"
    )
    original.rename(original.with_name("saved-" + original.name))
    source = broker.issuer(broker.owner._prepared.resource_order[0])
    with pytest.raises(ValueError):
        facade.start(source.unit_id, source.recipe.descriptor, broker.connection, end)
    assert broker.owner.latch.cancelled and not list(work.glob("*.marker"))
    assert (
        broker._cancel_result.native_epoch_confirmed
        or broker._cancel_result.issuer_reaped
    )


def test_native_watchdog_observes_actual_storage_death_without_python_cancel(
    broker_stack,
):
    import select

    broker, facade, storage, _ = broker_stack
    end = stage_all(broker_stack)
    for unit in broker.owner._prepared.resource_order:
        issuer = broker.issuer(unit)
        assert facade.start(
            unit, issuer.recipe.descriptor, broker.connection, end
        ).ready
    signal.pidfd_send_signal(storage.process._capability.fileno(), signal.SIGKILL)
    assert select.select([broker.session._pidfd_capability.fileno()], [], [], 1)[0]
    assert select.select([broker.connection.child._capability.fileno()], [], [], 0)[0]
    assert not broker.owner.latch.cancelled
    manager = broker.session.boundaries
    for issuer in broker.issuers:
        assert (
            "frozen 1"
            in manager._read(
                manager._entry(issuer.recipe.descriptor), "cgroup.events"
            ).splitlines()
        )
