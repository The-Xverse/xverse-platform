"""Actual kernel helper bootstrap, with expected cases frozen before product code."""

from dataclasses import replace, asdict
import hashlib
import array
import copy
import threading
from importlib.resources import files
import json
import os
from pathlib import Path
import signal
import select
import struct
import socket
import subprocess
import sys
import time

import pytest

from xverse.argus import EvidenceStore
from xverse.maestro.bootstrap import (
    BootstrapAdmission,
    BootstrapPacket,
    _sealed,
    BootstrapSession,
    encode_bootstrap,
    seal_helper_image,
    sealed_bootstrap_fd,
)
from xverse.maestro.launcher import make_launch_recipe
from xverse.maestro.owner import ReleaseOwner, StageSupervisor
from xverse.maestro.persistence import PersistenceClient, sealed_input_fd
from xverse.maestro.prbc import BoundaryDescriptor
from .test_launcher import binaries as binaries, configured, deadline
from .test_boundary import environment as environment, native as native


@pytest.fixture(scope="module")
def supervisor_binary(tmp_path_factory):
    root = tmp_path_factory.mktemp("bootstrap-native")
    source = root / "bootstrap.c"
    source.write_bytes(
        files("xverse.maestro").joinpath("native/bootstrap.c").read_bytes()
    )
    binary = root / "bootstrap"
    cmd = [
        "cc",
        "-std=c11",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-Wconversion",
        "-Wshadow",
        str(source),
        "-lcrypto",
        "-o",
        str(binary),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=30)
    receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt_dir:
        output = Path(receipt_dir)
        output.mkdir(exist_ok=True, parents=True)
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        base = output / ("bootstrap-native-" + digest)
        base.with_suffix(".bin").write_bytes(binary.read_bytes())
        base.with_suffix(".json").write_text(
            json.dumps(
                {
                    "command": cmd,
                    "returncode": 0,
                    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "binary_sha256": digest,
                }
            )
        )
    return binary


@pytest.fixture
def boot_stack(environment, binaries, supervisor_binary, tmp_path, request):
    options = getattr(request, "param", {})
    factory, spawn, root = environment
    manager, latch = factory(seconds=45, run_id="fixture-run")
    config, helper_pin, work = configured(tmp_path, manager, binaries)
    images = tuple(
        seal_helper_image(
            source,
            digest="sha256:" + hashlib.sha256(source.read_bytes()).hexdigest(),
            argv0=argv0,
        )
        for source, argv0 in (
            (binaries["launcher"], str(binaries["launcher"])),
            (binaries["bound-gate"], str(binaries["bound-gate"])),
            (Path(sys.executable).resolve(), sys.executable),
        )
    )
    admission = BootstrapAdmission(
        "fixture-run",
        config.prepared.lifecycle_digest,
        "bootstrap-approval",
        "sha256:" + hashlib.sha256(b"owned-test-environment").hexdigest(),
        "sha256:" + hashlib.sha256(supervisor_binary.read_bytes()).hexdigest(),
        manager._admission.teardown_deadline,
        deadline(options.get("lease_seconds", 4.9)),
        images,
    )
    data = encode_bootstrap(admission)
    input_fd = sealed_bootstrap_fd(data)
    parent, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    process = subprocess.Popen(
        [str(supervisor_binary), str(peer.fileno()), str(input_fd)],
        pass_fds=(peer.fileno(), input_fd, *(i.descriptor for i in images)),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    peer.close()
    os.close(input_fd)
    try:
        session = BootstrapSession(
            process,
            parent,
            data,
            manager,
            latch,
            deadline=deadline(min(3, options.get("lease_seconds", 4.9) * 0.8)),
        )
    except Exception:
        process.wait(timeout=2)
        process.stderr.close()
        parent.close()
        for image in images:
            os.close(image.descriptor)
        raise
    clients, owners = [], []

    def boundary(name, unit=None):
        value = BoundaryDescriptor("fixture-run", unit or "helper:" + name, 1, name, 0)
        manager.create_frozen(value)
        return value

    def start():
        storage = session.persistence(
            config,
            boundary("storage"),
            deadline(min(3, (session._lease - time.monotonic_ns()) / 1e9 - 0.1)),
        )
        clients.append(storage)
        owner = ReleaseOwner.from_persistence(
            storage, StageSupervisor(manager, latch), latch
        )
        owners.append(owner)
        original = deadline(min(4, (session._lease - time.monotonic_ns()) / 1e9 - 0.2))
        unit = config.prepared.units[0].unit_id
        owner.commit_intent(unit, original)
        descriptor = boundary("workload", unit)
        recipe = make_launch_recipe(
            owner,
            descriptor,
            environment={"MAESTRO_VISIBLE": "declared"},
            helper_artifact_digest=helper_pin,
            deadline=original,
        )
        launcher = session.catalog(owner, recipe, boundary("launcher"), original)
        clients.append(launcher)
        handle = launcher.stage(original)
        gate = session.gate(
            owner,
            descriptor,
            boundary("gate"),
            original,
            lease_ns=min(session._lease, time.monotonic_ns() + 3_500_000_000),
        )
        clients.append(gate)
        return owner, storage, descriptor, launcher, handle, gate, original

    yield session, manager, latch, config, work, boundary, start, clients, owners
    for owner in owners:
        owner.cancel("test-bootstrap-teardown")
    from xverse.maestro.launcher import CatalogLauncher
    from xverse.maestro.persistence import PersistenceClient
    from xverse.maestro.owner import GateConnection

    launcher_drains = []
    for client in clients:
        if type(client) is CatalogLauncher:
            client.cancel("test-bootstrap-teardown")
            observed = client.drain(deadline(1))
            assert observed.helper_reaped
            launcher_drains.append(asdict(observed))
        elif type(client) is PersistenceClient:
            if not client._failed and not client._aborted:
                try:
                    client.abort(deadline(1))
                except (ValueError, OSError):
                    client._fail()
            assert client.drain(deadline(1)).worker_reaped
    session.cancel("test-bootstrap-teardown")
    observed = session.drain(deadline(1.8))
    assert observed.supervisor_reaped and observed.registered_children_reaped
    assert observed.unacknowledged_births == int(
        options.get("allow_unacknowledged", False)
    )
    for client in clients:
        client.dispose()
        if type(client) is GateConnection:
            client.channel.close()
    for entry in manager._entries.values():
        if entry.state != "released":
            cleaned = manager.force_cleanup(entry.descriptor)
            assert cleaned.boundary_released and cleaned.residual_count == 0
    if observed.unacknowledged_births:
        # Explicit external local-FD disposal, never normal ownership/cleanup success.
        session._pidfd_capability.close()
        os.close(session._pidfd)
        session.channel.close()
    else:
        session.dispose()
    process.wait(timeout=1)
    assert process.stderr.read() == b""
    process.stderr.close()
    for image in images:
        os.close(image.descriptor)
    receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt_dir:
        (
            Path(receipt_dir)
            / ("bootstrap-children-" + str(os.getpid()) + "-" + tmp_path.name + ".json")
        ).write_text(
            json.dumps(
                {
                    "supervisor_reaped": True,
                    "registered_children_reaped": True,
                    "children": len(session._children),
                    "catalog_direct_child_drains": launcher_drains,
                    "unacknowledged_births": observed.unacknowledged_births,
                    "external_local_fd_disposals": int(
                        bool(observed.unacknowledged_births)
                    )
                    * 2,
                    "supervisor_returncode": observed.supervisor_returncode,
                    "all_original_boundaries_released": True,
                    "source_sha256": hashlib.sha256(
                        Path(__file__).read_bytes()
                    ).hexdigest(),
                }
            )
        )


def test_three_actual_helpers_without_coordinator_popen(
    boot_stack, monkeypatch, tmp_path
):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack

    def no_popen(*args, **kwargs):
        pytest.fail("coordinator attempted Popen during helper bootstrap")

    with monkeypatch.context() as patch:
        patch.setattr(subprocess, "Popen", no_popen)
        owner, storage, descriptor, launcher, handle, gate, original = start()
        assert not (work / "source-binding.marker").exists()
        result = owner.release(descriptor.unit_id, descriptor, gate, original)
        assert result.native_unfreeze_observed and not result.ready_for_execution
        until = time.monotonic() + 1
        while (
            not (work / "source-binding.marker").exists() and time.monotonic() < until
        ):
            time.sleep(0.005)
        assert (work / "source-binding.marker").read_text() == "EXEC\n"
        assert launcher.observe(handle, deadline()).running
        assert len(session._children) == 3
        storage.abort(deadline(1))
    assert (
        EvidenceStore.read_run(tmp_path / "argus").manifest["writerState"] == "failed"
    )


def raw_storage(boot_stack, *, original=None):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    original = original or deadline(3)
    helper = boundary("raw-storage")
    parent, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    fd = sealed_input_fd(config)
    try:
        child = session.birth(3, helper, helper, peer, fd, original)
        return child, parent, helper, original
    except Exception:
        parent.close()
        raise
    finally:
        peer.close()
        os.close(fd)


def test_frozen_birth_precedes_helper_instructions_and_shared_actual_wait(boot_stack):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    child, channel, helper, original = raw_storage(boot_stack)
    try:
        assert child._wait(child._fd) is None
        assert manager.residual_membership(helper) == (child.pid,)
        assert not select.select([channel], [], [], 0.03)[0]
        session.activate(child, original)
        client = PersistenceClient(child, channel, config, latch, deadline=original)
        clients.append(client)
        client.abort(deadline(1))
        first = client.drain(deadline(1))
        assert first.worker_reaped
        session.cancel()
        second = session.drain(deadline(1))
        assert second.registered_children_reaped and child._result is not None
        assert child._wait(child._fd, consume=True) is child._result
    finally:
        if not clients:
            channel.close()


def test_cancel_before_activation_cannot_run_persistence_helper(boot_stack):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    child, channel, helper, original = raw_storage(boot_stack)
    try:
        session.cancel()
        with pytest.raises(ValueError):
            session.activate(child, original)
        assert session.drain(deadline(1)).registered_children_reaped
        assert channel.recv(1024) == b""
        assert not (work.parent / "argus").exists()
    finally:
        channel.close()


def test_late_genuine_birth_ack_retains_cleanup_only_pidfd(boot_stack, monkeypatch):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    receive = session._receive

    def delayed(until, *, cleanup=False):
        result = receive(until, cleanup=cleanup)
        if not cleanup:
            time.sleep(max(0, (until - time.monotonic_ns()) / 1e9) + 0.02)
        return result

    monkeypatch.setattr(session, "_receive", delayed)
    with pytest.raises(ValueError, match="LATE-ACK"):
        raw_storage(boot_stack, original=deadline(0.15))
    assert not session._pending and len(session._children) == 1
    child = next(iter(session._children.values()))
    assert child._cleanup_only and not child._active
    with pytest.raises(ValueError):
        session.activate(child, deadline())
    assert session.drain(deadline(1)).registered_children_reaped
    assert not (work.parent / "argus").exists()


@pytest.mark.parametrize("boot_stack", [{"allow_unacknowledged": True}], indirect=True)
def test_cancel_during_stopped_birth_keeps_unacknowledged_accounting(boot_stack):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    signal.pidfd_send_signal(session._pidfd, signal.SIGSTOP)
    try:
        with pytest.raises(ValueError):
            raw_storage(boot_stack, original=deadline(0.15))
        assert latch.cancelled and session._closed
    finally:
        signal.pidfd_send_signal(session._pidfd, signal.SIGCONT)
    observed = session.drain(deadline(1))
    assert (
        observed.unacknowledged_births == 1
        and observed.diagnostic == "ML-BOOT-DRAIN-UNRESOLVED"
    )
    assert not observed.cleanup_complete
    assert not (work.parent / "argus").exists()


def test_birth_helper_boundary_removed_before_native_dispatch(boot_stack):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    helper = boundary("removed-storage")
    signal.pidfd_send_signal(session._pidfd, signal.SIGSTOP)
    parent, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    source = sealed_input_fd(config)
    try:
        until = int(deadline(2).monotonic_seconds * 1e9)
        request = BootstrapPacket(1, 1, until, session.config.scope, slot=1, state=3)
        fd = manager._entries[helper.key].fd
        assert (
            session.channel.sendmsg(
                [request.encode()],
                [
                    (
                        socket.SOL_SOCKET,
                        socket.SCM_RIGHTS,
                        array.array("i", [fd, fd, peer.fileno(), source]),
                    )
                ],
            )
            == 128
        )
        assert manager.force_cleanup(helper).boundary_released
    finally:
        peer.close()
        os.close(source)
        signal.pidfd_send_signal(session._pidfd, signal.SIGCONT)
    until = time.monotonic() + 1
    while (
        time.monotonic() < until and not select.select([session._pidfd], [], [], 0)[0]
    ):
        time.sleep(0.005)
    assert select.select([session._pidfd], [], [], 0)[0]
    assert parent.recv(128) == b""
    parent.close()
    assert not (work.parent / "argus").exists()


def test_duplicate_activation_rejects_without_reissuing(boot_stack):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    child, channel, helper, original = raw_storage(boot_stack)
    try:
        session.activate(child, original)
        client = PersistenceClient(child, channel, config, latch, deadline=original)
        clients.append(client)
        with pytest.raises(ValueError, match="ACTIVATION"):
            session.activate(child, original)
        assert not latch.cancelled and len(session._children) == 1
        client.abort(deadline(1))
    finally:
        if not clients:
            channel.close()


def test_original_child_registry_copy_fork_and_replacement_denied(boot_stack):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    child, channel, helper, original = raw_storage(boot_stack)
    try:
        with pytest.raises(TypeError):
            copy.copy(session)
        with pytest.raises(TypeError):
            copy.copy(child)
        saved = session._children
        session._children = {}
        try:
            with pytest.raises(ValueError, match="REGISTRY-REPLACED"):
                child._holder()
        finally:
            session._children = saved
        pid = os.fork()
        if pid == 0:
            try:
                session.cancel()
            except ValueError:
                os._exit(0)
            os._exit(1)
        assert os.waitpid(pid, 0)[1] == 0 and not latch.cancelled
        receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
        if receipt_dir:
            (
                Path(receipt_dir) / ("bootstrap-fork-reaping-" + str(pid) + ".json")
            ).write_text(
                json.dumps(
                    {
                        "fork_child_reaped": True,
                        "source_sha256": hashlib.sha256(
                            Path(__file__).read_bytes()
                        ).hexdigest(),
                    }
                )
            )
    finally:
        channel.close()


def test_supervisor_socket_replacement_does_not_retain_authority(boot_stack):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    original = os.dup(session.channel.fileno())
    first, second = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    try:
        os.dup2(first.fileno(), session.channel.fileno())
        with pytest.raises(ValueError, match="REPLACED"):
            session._live()
    finally:
        os.dup2(original, session.channel.fileno())
        os.close(original)
        first.close()
        second.close()


def test_nonblocking_normal_lock_does_not_block_cancel(boot_stack):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    session._lock.acquire()
    try:
        with pytest.raises(ValueError, match="CONFLICT"):
            session.renew(deadline(4.9), deadline())
        thread = threading.Thread(target=session.cancel)
        thread.start()
        thread.join(timeout=0.5)
        assert not thread.is_alive() and latch.cancelled
    finally:
        session._lock.release()


@pytest.mark.parametrize("boot_stack", [{"lease_seconds": 0.3}], indirect=True)
def test_expired_native_lease_rejects_renewal(boot_stack):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    time.sleep(0.35)
    with pytest.raises(ValueError):
        session.renew(deadline(1), deadline(0.1))
    assert not session._children


def test_original_root_lease_renewal_is_exact_and_finite(boot_stack):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    previous = session._lease
    time.sleep(0.03)
    session.renew(deadline(4.9), deadline())
    assert session._lease > previous
    with pytest.raises(ValueError):
        session.renew(deadline(5.1), deadline())
    assert not latch.cancelled


def test_native_supervisor_loss_closes_child_ordinary_authority(boot_stack):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    child, channel, helper, original = raw_storage(boot_stack)
    try:
        signal.pidfd_send_signal(session._pidfd, signal.SIGKILL)
        until = time.monotonic() + 1
        while (
            time.monotonic() < until
            and not select.select([session._pidfd], [], [], 0)[0]
        ):
            time.sleep(0.005)
        with pytest.raises(ValueError):
            session.activate(child, original)
        # Existing exact pidfd remains usable for cleanup; no PID/name discovery.
        session.cancel()
        observed = session.drain(deadline(1))
        assert (
            observed.registered_children_reaped
            and not observed.final_workload_freeze_acknowledged
        )
        assert observed.diagnostic == "ML-BOOT-SUPERVISOR-UNRESOLVED"
        assert channel.recv(128) == b""
    finally:
        channel.close()


@pytest.mark.parametrize("mode", ["kind", "scope", "rights", "sequence", "foreign"])
def test_native_malformed_control_cancels_insertion(boot_stack, mode):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    packet = bytearray(
        BootstrapPacket(
            3,
            1,
            int(deadline(1).monotonic_seconds * 1e9),
            session.config.scope,
            state=session._lease,
        ).encode()
    )
    if mode == "kind":
        packet[7] = 99
    if mode == "scope":
        packet[24] ^= 1
    if mode == "sequence":
        packet[15] = 2
    fd = os.open("/dev/null", os.O_RDONLY)
    try:
        ancillary = (
            [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [fd]))]
            if mode == "rights"
            else []
        )
        if mode == "foreign":
            pid = os.fork()
            if pid == 0:
                os._exit(
                    0 if session.channel.sendmsg([packet], ancillary) == 128 else 1
                )
            assert os.waitpid(pid, 0)[1] == 0
            receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
            if receipt_dir:
                (
                    Path(receipt_dir) / ("bootstrap-peer-reaping-" + str(pid) + ".json")
                ).write_text(
                    json.dumps(
                        {
                            "fork_child_reaped": True,
                            "source_sha256": hashlib.sha256(
                                Path(__file__).read_bytes()
                            ).hexdigest(),
                        }
                    )
                )
        else:
            assert session.channel.sendmsg([packet], ancillary) == 128
    finally:
        os.close(fd)
    until = time.monotonic() + 1
    while (
        time.monotonic() < until and not select.select([session._pidfd], [], [], 0)[0]
    ):
        time.sleep(0.005)
    assert select.select([session._pidfd], [], [], 0)[0]


@pytest.mark.parametrize("mode", ["wrong-pin", "unsealed-image", "bad-config"])
def test_native_independent_image_and_input_validation_rejects(
    boot_stack, supervisor_binary, binaries, tmp_path, mode
):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    data = session.config
    extra_fd = -1
    if mode == "wrong-pin":
        bad = replace(data.admission.images[0], digest="sha256:" + "0" * 64)
        data = encode_bootstrap(
            replace(data.admission, images=(bad, *data.admission.images[1:]))
        )
        private = data.private_bytes
    elif mode == "unsealed-image":
        extra_fd = os.open(binaries["launcher"], os.O_RDONLY)
        private = (
            data.private_bytes[:56]
            + struct.pack("!I", extra_fd)
            + data.private_bytes[60:]
        )
    else:
        private = b"FAIL" + data.private_bytes[4:]
    source = _sealed(private, "owned-invalid-bootstrap-input")
    parent, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    passed = (
        source,
        peer.fileno(),
        *(i.descriptor for i in data.admission.images),
        *((extra_fd,) if extra_fd >= 0 else ()),
    )
    process = subprocess.Popen(
        [str(supervisor_binary), str(peer.fileno()), str(source)],
        pass_fds=passed,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    peer.close()
    os.close(source)
    try:
        if mode == "wrong-pin":
            parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
            with pytest.raises(ValueError):
                BootstrapSession(
                    process, parent, data, manager, latch, deadline=deadline()
                )
        assert process.wait(timeout=2) == 64
        assert process.stderr.read() == b""
        receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
        if receipt_dir:
            (
                Path(receipt_dir)
                / ("bootstrap-input-reaping-" + str(process.pid) + ".json")
            ).write_text(
                json.dumps(
                    {
                        "child_reaped": True,
                        "mode": mode,
                        "returncode": 64,
                        "source_sha256": hashlib.sha256(
                            Path(__file__).read_bytes()
                        ).hexdigest(),
                    }
                )
            )
    finally:
        parent.close()
        process.stderr.close()
        if extra_fd >= 0:
            os.close(extra_fd)


def test_failed_persistence_constructor_keeps_actual_child_for_bootstrap_drain(
    boot_stack,
):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    private = json.loads(config.private_bytes)
    private["lifecycle_digest"] = "0" * 64
    bad = replace(config, private_bytes=json.dumps(private).encode())
    with pytest.raises(ValueError):
        session.persistence(bad, boundary("failed-storage"), deadline())
    assert latch.cancelled and len(session._children) == 1 and not session._pending
    observed = session.drain(deadline(1))
    assert observed.supervisor_reaped and observed.registered_children_reaped
    assert not (work.parent / "argus").exists()


@pytest.mark.parametrize("boot_stack", [{"lease_seconds": 3}], indirect=True)
def test_lease_expiry_kills_helpers_then_refreezes_original_workload(boot_stack):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    owner, storage, descriptor, launcher, handle, gate, original = start()
    owner.release(descriptor.unit_id, descriptor, gate, original)
    until = time.monotonic() + 1
    while not (work / "source-binding.marker").exists() and time.monotonic() < until:
        time.sleep(0.005)
    assert (work / "source-binding.marker").read_text() == "EXEC\n"
    until = session._lease / 1e9 + 1
    while (
        time.monotonic() < until and not select.select([session._pidfd], [], [], 0)[0]
    ):
        time.sleep(0.005)
    assert select.select([session._pidfd], [], [], 0)[0]
    assert manager.residual_membership(descriptor)
    # This is frozen containment, not workload reaping or successful teardown.
    assert (
        json.loads((work.parent / "argus" / "manifest.json").read_text())["writerState"]
        == "open"
    )


def test_unrelated_original_sentinel_survives_bootstrap_cancellation(
    boot_stack, environment, native
):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    factory, spawn, root = environment
    sentinel_descriptor = boundary("sentinel")
    sentinel, marker, line = spawn(native, manager, sentinel_descriptor)
    assert line.startswith("CHILD ")
    child, channel, helper, original = raw_storage(boot_stack)
    saved = os.dup(child._fd)
    foreign = os.pidfd_open(sentinel.pid, 0)
    try:
        os.dup2(foreign, child._fd)
        with pytest.raises(ValueError, match="MISMATCH"):
            child._holder()
        session.cancel()
        rejected = session.drain(deadline(1))
        assert rejected.supervisor_reaped and not rejected.registered_children_reaped
        assert not rejected.cleanup_complete
        assert manager.residual_membership(sentinel_descriptor) == (
            int(line.split()[1]),
        )
        assert sentinel.poll() is None and not select.select([marker], [], [], 0)[0]
        os.dup2(saved, child._fd)
        assert session.drain(deadline(1)).registered_children_reaped
    finally:
        os.dup2(saved, child._fd)
        os.close(saved)
        os.close(foreign)
        channel.close()


@pytest.mark.parametrize("mode", ["foreign", "reopened-same-pid"])
def test_foreign_pidfd_cannot_replace_supervisor_capability(boot_stack, mode):
    session, *_ = boot_stack
    child, channel, helper, original = raw_storage(boot_stack)
    saved = os.dup(session._pidfd)
    other = (
        os.pidfd_open(session._pid_pin, 0)
        if mode == "reopened-same-pid"
        else os.dup(child._fd)
    )
    try:
        os.dup2(other, session._pidfd)
        with pytest.raises(ValueError, match="MISMATCH"):
            session._live()
    finally:
        os.dup2(saved, session._pidfd)
        os.close(saved)
        os.close(other)
        channel.close()
    session._live()


def test_foreign_pidfd_cannot_replace_child_or_supplied_wait_fd(boot_stack):
    session, *_ = boot_stack
    child, channel, helper, original = raw_storage(boot_stack)
    saved = os.dup(child._fd)
    try:
        os.dup2(session._pidfd, child._fd)
        with pytest.raises(ValueError, match="MISMATCH"):
            child._holder()
        assert child._result is None
        os.dup2(saved, child._fd)
        with pytest.raises(OSError, match="WAIT-FD-UNRESOLVED"):
            child._wait(session._pidfd, consume=True)
        assert child._result is None
        session._live()
    finally:
        os.dup2(saved, child._fd)
        os.close(saved)
        channel.close()


def test_unavailable_pidfd_comparison_rejects_without_weaker_fallback(
    boot_stack, monkeypatch
):
    from xverse.maestro import child as child_module

    session, *_ = boot_stack

    def unavailable(*args):
        raise OSError(1, "owned comparison denial fixture")

    before = len(os.listdir("/proc/self/fd"))
    with monkeypatch.context() as patch:
        patch.setattr(child_module, "_same_description", unavailable)
        with pytest.raises(OSError):
            child_module._PidfdCapability(session._pidfd)
    assert len(os.listdir("/proc/self/fd")) == before
    session._live()


def test_persistence_failure_signals_original_child_not_borrowed_sentinel(
    boot_stack, environment, native
):
    session, manager, latch, config, work, boundary, start, clients, owners = boot_stack
    owner, storage, descriptor, launcher, handle, gate, original = start()
    _, spawn, _ = environment
    sentinel_descriptor = boundary("signal-sentinel")
    sentinel, marker, line = spawn(native, manager, sentinel_descriptor)
    saved = os.dup(storage._pidfd)
    foreign = os.pidfd_open(sentinel.pid, 0)
    try:
        os.dup2(foreign, storage._pidfd)
        with pytest.raises((ValueError, OSError)):
            storage.commit_intent(config.prepared.units[1].unit_id, deadline(1))
        assert latch.cancelled and storage._failed
        assert not select.select([foreign], [], [], 0.2)[0]
        assert sentinel.poll() is None
        assert manager.residual_membership(sentinel_descriptor) == (
            int(line.split()[1]),
        )
        assert not select.select([marker], [], [], 0)[0]
        assert not (work / "source-binding.marker").exists()
    finally:
        os.dup2(saved, storage._pidfd)
        os.close(saved)
        os.close(foreign)
    assert storage.drain(deadline(1)).worker_reaped
