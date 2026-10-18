from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
from importlib.resources import files
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import copy
import array
import signal

import pytest

from xverse.argus import EvidenceStore
from xverse.maestro.admission import PermitApproval, PermitBinding, permit_digest
from xverse.maestro.launcher import (
    CatalogLauncher,
    LaunchPacket,
    make_launch_recipe,
    sealed_recipe_fd,
)
from xverse.maestro.owner import GateConnection, ReleaseOwner, StageSupervisor
from xverse.maestro.persistence import (
    PersistenceClient,
    encode_configuration,
    sealed_input_fd,
)
from xverse.maestro.prbc import BoundaryDescriptor
from xverse.maestro.projection import ProviderDescriptor, prepare_lifecycle
from xverse.maestro.time import HostDeadline
from xverse_xdl.lifecycle import ExecutionPermit
from .test_preparation import compiled, documents
from .test_boundary import environment as environment


def deadline(seconds=3):
    return HostDeadline("host-session", time.monotonic() + seconds)


@pytest.fixture(scope="module")
def binaries(tmp_path_factory):
    root = tmp_path_factory.mktemp("catalog-launcher-native")
    definitions = [
        (
            "launcher",
            files("xverse.maestro").joinpath("native/catalog_launcher.c"),
            ["-lcrypto"],
        ),
        (
            "bound-gate",
            files("xverse.maestro").joinpath("native/lease_guard.c"),
            ["-DMAESTRO_RELEASE_GATE=1", "-DMAESTRO_BOUNDARY_ACK=1"],
        ),
        (
            "plain-gate",
            files("xverse.maestro").joinpath("native/lease_guard.c"),
            ["-DMAESTRO_RELEASE_GATE=1"],
        ),
        ("workload", Path(__file__).with_name("catalog_workload.c"), []),
    ]
    outputs = {}
    for name, source, extra in definitions:
        local = root / (name + ".c")
        local.write_bytes(source.read_bytes())
        binary = root / name
        cmd = [
            "cc",
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(local),
            *extra,
            "-o",
            str(binary),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        outputs[name] = binary
        receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
        if receipt_dir:
            target = Path(receipt_dir)
            target.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256(binary.read_bytes()).hexdigest()
            base = target / ("catalog-native-" + name + "-" + digest)
            base.with_suffix(".bin").write_bytes(binary.read_bytes())
            base.with_suffix(".json").write_text(
                json.dumps(
                    {
                        "command": cmd,
                        "returncode": 0,
                        "name": name,
                        "source_sha256": hashlib.sha256(local.read_bytes()).hexdigest(),
                        "binary_sha256": digest,
                    }
                )
            )
    return outputs


def configured(tmp_path, manager, binaries, mode="single"):
    work = tmp_path / "work"
    work.mkdir()
    image = tmp_path / "declared-image"
    image.write_bytes(binaries["workload"].read_bytes())
    if mode == "badelf":
        image.write_bytes(b"\x7fELF" + bytes(60))
    image.chmod(0o700)
    docs = documents()
    deployment = docs["deployment.json"]["spec"]
    digest = "sha256:" + hashlib.sha256(image.read_bytes()).hexdigest()
    deployment["artifacts"][0].update(
        artifactKind="executable",
        digest=digest,
        sourceRef=image.as_uri(),
    )
    for binding in deployment["bindings"]:
        payload = binding["extensions"]["io.xverse.runtime.compatibility"]
        payload["provider"] = {"id": "maestro-process-v1", "kind": "process"}
        payload["process"] = {
            "executable": str(image),
            "arguments": [binding["id"] + ".marker", mode],
            "workingDirectory": str(work),
            "environmentNames": ["MAESTRO_VISIBLE"],
            "inheritedHandles": "closed",
            "implicitShell": False,
        }
    result, resources = compiled(docs)
    helper_pin = (
        "sha256:" + hashlib.sha256(binaries["launcher"].read_bytes()).hexdigest()
    )
    prepared = prepare_lifecycle(
        result,
        resources,
        provider_descriptors=(
            ProviderDescriptor(
                "maestro-process-v1", "process", helper_pin, "isolated-fixture"
            ),
        ),
    )
    now = datetime.now(timezone.utc)
    bindings = []
    approvals = []
    for index, unit in enumerate(prepared.units):
        plan = unit.plan
        permit = ExecutionPermit(
            permit_id="owned-process-permit-" + str(index),
            nonce="private-process-nonce-" + str(index),
            plan_digest=plan.digest,
            catalog_identity=plan.catalog_identity,
            environment_identity=plan.environment_identity,
            permitted_actions=tuple(a.action_id for a in plan.actions),
            approval_evidence_ref="urn:xverse:test:process-approval:" + str(index),
            issuer_label="owned-test-approval",
            operation_classes=tuple(sorted({a.operation for a in plan.actions})),
            exclusions=("legacy-execution",),
            public_safety_classification="public-safe",
            not_before=now - timedelta(seconds=30),
            expires_at=now + timedelta(seconds=90),
        )
        binding = PermitBinding(
            unit.unit_id, "owned-process-execution-" + str(index), 1, permit
        )
        bindings.append(binding)
        approvals.append(
            PermitApproval(
                permit.approval_evidence_ref,
                permit.issuer_label,
                "fixture-run",
                unit.unit_id,
                binding.execution_id,
                1,
                prepared.lifecycle_digest,
                plan.digest,
                unit.provider.provider_id,
                unit.provider.kind,
                helper_pin,
                plan.environment_identity,
                plan.artifact_digests,
                permit_digest(permit),
                now - timedelta(seconds=30),
                now + timedelta(seconds=90),
            )
        )
    config = encode_configuration(
        prepared,
        result,
        resources,
        run_id="fixture-run",
        bindings=bindings,
        approvals=approvals,
        session="host-session",
        generation_deadline=manager._admission.teardown_deadline,
        journal_path=tmp_path / "m3.jsonl",
        evidence_root=tmp_path / "argus",
    )
    return config, helper_pin, work


@pytest.fixture
def launch_stack(tmp_path, environment, binaries, monkeypatch, request):
    factory, spawn, root = environment
    manager, latch = factory(seconds=35, run_id="fixture-run")
    options = getattr(request, "param", {})
    config, helper_pin, work = configured(
        tmp_path, manager, binaries, options.get("mode", "single")
    )
    parent, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    cfg = sealed_input_fd(config)
    storage_fds = (peer.fileno(), cfg)
    storage_command = [
        sys.executable,
        "-I",
        "-m",
        "xverse.maestro.persistence_worker",
        str(peer.fileno()),
        str(cfg),
    ]
    extra_pipes = []
    if options.get("storage_after_arm"):
        announce, announce_write = os.pipe()
        release_read, release_write = os.pipe()
        extra_pipes = [announce, announce_write, release_read, release_write]
        storage_command = [
            sys.executable,
            "-I",
            str(Path(__file__).with_name("persistence_fixture.py")),
            str(peer.fileno()),
            str(cfg),
            str(announce_write),
            str(release_read),
            "revalidate3-hang",
        ]
        storage_fds = (*storage_fds, announce_write, release_read)
    process = subprocess.Popen(
        storage_command,
        pass_fds=storage_fds,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    peer.close()
    os.close(cfg)
    client = PersistenceClient(process, parent, config, latch, deadline=deadline())
    owner = ReleaseOwner.from_persistence(
        client, StageSupervisor(manager, latch), latch
    )
    launchers = []
    gate_processes = []
    raw_helpers = []

    def launch(original=None, *, stage=True, private_transform=None, sealed=True):
        original = original or deadline(4.5)
        unit_id = config.prepared.units[0].unit_id
        owner.commit_intent(unit_id, original)
        descriptor = BoundaryDescriptor(
            "fixture-run", unit_id, 1, "catalog-boundary", 0
        )
        manager.create_frozen(descriptor)
        recipe = make_launch_recipe(
            owner,
            descriptor,
            environment={"MAESTRO_VISIBLE": "declared"},
            helper_artifact_digest=helper_pin,
            deadline=original,
        )
        if private_transform is None:
            source = sealed_recipe_fd(recipe)
        elif sealed:
            source = sealed_recipe_fd(
                replace(recipe, private_bytes=private_transform(recipe.private_bytes))
            )
        else:
            path = tmp_path / "unsealed-input"
            path.write_bytes(private_transform(recipe.private_bytes))
            source = os.open(path, os.O_RDONLY)
        channel, other = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        channel.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        boundary = manager._entries[descriptor.key].fd
        monkeypatch.setenv("MAESTRO_AMBIENT_SECRET", "not-inherited")
        child = subprocess.Popen(
            [
                str(binaries["launcher"]),
                str(boundary),
                str(other.fileno()),
                str(source),
            ],
            pass_fds=(boundary, other.fileno(), source),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        other.close()
        os.close(source)
        raw_helpers.append((child, channel, "launcher"))
        launcher = CatalogLauncher(
            child,
            channel,
            owner,
            recipe,
            helper_artifact_digest=helper_pin,
            deadline=original,
        )
        launchers.append(launcher)
        handle = launcher.stage(original) if stage else None
        return descriptor, launcher, handle, original

    def gate(descriptor, original, *, actual_descriptor=None, bound=True):
        boundary = manager._entries[(actual_descriptor or descriptor).key].fd
        channel, other = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        channel.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        gate_binary = binaries["bound-gate" if bound else "plain-gate"]
        pin = "sha256:" + hashlib.sha256(gate_binary.read_bytes()).hexdigest()
        scope = owner.scope(descriptor.unit_id, descriptor, pin)
        until = time.monotonic_ns() + 4_000_000_000
        child = subprocess.Popen(
            [
                str(gate_binary),
                str(boundary),
                str(other.fileno()),
                str(config.generation_ns),
                str(until),
                "500000000",
                scope.hex(),
                "0",
            ],
            pass_fds=(boundary, other.fileno()),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        other.close()
        raw_helpers.append((child, channel, "gate"))
        connection = GateConnection(
            child,
            channel,
            scope=scope,
            epoch=0,
            lease_ns=until,
            artifact_digest=pin,
            latch=latch,
            deadline=original,
            boundaries=manager if bound else None,
            descriptor=descriptor if bound else None,
        )
        gate_processes.append(connection)
        return connection

    yield owner, client, manager, config, work, launch, gate
    owner.cancel("test-catalog-teardown")
    for launcher in launchers:
        launcher.cancel("test-catalog-teardown")
        observed = launcher.drain(deadline(1.5))
        assert observed.helper_reaped and observed.direct_child_reaped
        launcher.dispose()
    for entry in manager._entries.values():
        if entry.state != "released":
            cleanup = manager.force_cleanup(entry.descriptor)
            assert cleanup.boundary_released and cleanup.residual_count == 0
    for connection in gate_processes:
        connection.channel.close()
        connection.process.wait(timeout=2)
        connection.dispose()
    for child, channel, kind in raw_helpers:
        channel.close()
        child.wait(timeout=2)
        assert child.stderr.read() == b""
        child.stderr.close()
    for fd in extra_pipes:
        os.close(fd)
    if not client._failed and not client._aborted:
        client.abort(deadline(1))
    assert client.drain(deadline(1)).worker_reaped
    assert client.process.stderr.read() == b""
    client.process.stderr.close()
    client.dispose()
    receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt_dir:
        (
            Path(receipt_dir)
            / ("catalog-children-" + str(os.getpid()) + "-" + tmp_path.name + ".json")
        ).write_text(
            json.dumps(
                {
                    "helpers_reaped": True,
                    "direct_children_reaped": True,
                    "launcher_count": len(launchers),
                    "gate_count": len(gate_processes),
                    "storage_count": 1,
                    "bootstrap_rejected_helpers_reaped": len(raw_helpers)
                    - len(launchers)
                    - len(gate_processes),
                }
            )
        )


def test_actual_catalog_frozen_birth_bound_gate_exec_and_cleanup(
    launch_stack, tmp_path
):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch()
    marker = work / "source-binding.marker"
    assert not marker.exists()
    before = launcher.observe(handle, deadline())
    assert before.leader_alive and not before.exec_pipe_closed and not before.running
    connection = gate(descriptor, original)
    result = owner.release(descriptor.unit_id, descriptor, connection, original)
    assert result.native_unfreeze_observed and not result.ready_for_execution
    until = time.monotonic() + 1
    while not marker.exists() and time.monotonic() < until:
        time.sleep(0.005)
    assert marker.read_text() == "EXEC\n"
    observed = launcher.observe(replace(handle), deadline())
    assert observed.running and not observed.ready_for_execution
    owner.cancel()
    drained = launcher.drain(deadline(1))
    assert (
        drained.helper_reaped
        and drained.direct_child_reaped
        and not drained.cleanup_complete
    )
    cleanup = manager.force_cleanup(descriptor)
    assert cleanup.boundary_released and cleanup.residual_count == 0
    client.abort(deadline(1))
    reader = EvidenceStore.read_run(tmp_path / "argus")
    assert (
        reader.manifest["writerState"] == "failed"
        and reader.records()[0]["extensions"]["xverse.maestro"]["generation"] == 1
    )


def test_changed_source_after_stage_executes_only_sealed_catalog_bytes(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch()
    image = Path(owner._unit(descriptor.unit_id).plan.process_action.executable)
    image.write_bytes(b"changed source after sealing")
    connection = gate(descriptor, original)
    owner.release(descriptor.unit_id, descriptor, connection, original)
    marker = work / "source-binding.marker"
    until = time.monotonic() + 1
    while not marker.exists() and time.monotonic() < until:
        time.sleep(0.005)
    assert (
        marker.read_text() == "EXEC\n" and launcher.observe(handle, deadline()).running
    )


def test_image_tamper_before_stage_is_not_executed(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch(stage=False)
    Path(owner._unit(descriptor.unit_id).plan.process_action.executable).write_bytes(
        b"bad image"
    )
    with pytest.raises(ValueError):
        launcher.stage(original)
    assert not (work / "source-binding.marker").exists()
    assert not manager.residual_membership(descriptor)


def test_different_sealed_native_input_cannot_echo_original_context(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack

    def changed(data):
        value = bytearray(data)
        value[50] ^= 1
        return bytes(value)

    with pytest.raises(ValueError):
        launch(private_transform=changed)
    assert not (work / "source-binding.marker").exists()


def test_unsealed_regular_input_is_rejected_by_native_helper(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    with pytest.raises(ValueError):
        launch(private_transform=lambda data: data, sealed=False)
    assert not (work / "source-binding.marker").exists()


def test_forged_recipe_cannot_change_declared_arguments(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch(stage=False)
    recipe = launcher.recipe
    wrong = replace(recipe, private_bytes=recipe.private_bytes[:-1] + b"x")
    with pytest.raises(ValueError, match="RECIPE-MISMATCH"):
        CatalogLauncher(
            launcher.process,
            launcher.channel,
            owner,
            wrong,
            helper_artifact_digest=config.prepared.units[0].provider.artifact_digest,
            deadline=original,
        )
    assert not launcher._stage_started and not manager.residual_membership(descriptor)


def test_original_registry_rejects_forged_handle_fork_and_second_stage(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch()
    with pytest.raises(ValueError, match="HANDLE"):
        launcher.observe(replace(handle, resource_identity="foreign"), deadline())
    with pytest.raises(ValueError, match="REPLAY"):
        launcher.stage(original)
    with pytest.raises(TypeError):
        copy.copy(launcher)
    pid = os.fork()
    if pid == 0:
        try:
            launcher.observe(handle, deadline())
        except ValueError:
            os._exit(0)
        os._exit(1)
    assert os.waitpid(pid, 0)[1] == 0 and not launcher._cancelled
    receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt_dir:
        (Path(receipt_dir) / ("catalog-fork-reaping-" + str(pid) + ".json")).write_text(
            json.dumps(
                {
                    "fork_child_reaped": True,
                    "source_sha256": hashlib.sha256(
                        Path(__file__).read_bytes()
                    ).hexdigest(),
                }
            )
        )
    assert not (work / "source-binding.marker").exists()


def test_stage_reservation_rejects_concurrent_request_without_dispatch(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch(stage=False)
    launcher._stage_lock.acquire()
    try:
        with pytest.raises(ValueError, match="CONFLICT"):
            launcher.stage(original)
        assert not launcher._stage_started and not manager.residual_membership(
            descriptor
        )
    finally:
        launcher._stage_lock.release()
    assert launcher.stage(original).execution_id == "owned-process-execution-0"


def test_replaced_socket_fd_cannot_retain_original_issuer_authority(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch()
    first, second = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    try:
        os.dup2(first.fileno(), launcher.channel.fileno())
        with pytest.raises(ValueError, match="SOCKET-REPLACED"):
            launcher.observe(handle, deadline())
    finally:
        first.close()
        second.close()
    assert not (work / "source-binding.marker").exists()


def test_unbound_legacy_gate_cannot_release_catalog_staged_child(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch()
    connection = gate(descriptor, original, bound=False)
    with pytest.raises(ValueError, match="GATE-BOUNDARY"):
        owner.release(descriptor.unit_id, descriptor, connection, original)
    assert connection._sequence == 0 and not (work / "source-binding.marker").exists()


def test_gate_must_attest_exact_original_c1_boundary(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch()
    sibling = BoundaryDescriptor(
        "fixture-run", config.prepared.units[1].unit_id, 1, "sibling", 0
    )
    manager.create_frozen(sibling)
    with pytest.raises(ValueError):
        gate(descriptor, original, actual_descriptor=sibling)
    assert not (work / "source-binding.marker").exists()


@pytest.mark.parametrize("launch_stack", [{"mode": "descendant"}], indirect=True)
def test_dead_leader_does_not_hide_live_contained_descendant(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch()
    connection = gate(descriptor, original)
    owner.release(descriptor.unit_id, descriptor, connection, original)
    marker = work / "source-binding.marker"
    until = time.monotonic() + 1
    while time.monotonic() < until:
        if marker.exists() and "DESCENDANT" in marker.read_text():
            break
        time.sleep(0.005)
    assert "DESCENDANT" in marker.read_text()
    observed = launcher.observe(handle, deadline())
    assert not observed.running and observed.leader_reaped
    manager._freeze(manager._entries[descriptor.key])
    assert manager.residual_membership(descriptor)
    assert manager.force_cleanup(descriptor).termination_observed


@pytest.mark.parametrize("launch_stack", [{"storage_after_arm": True}], indirect=True)
def test_storage_timeout_after_arm_never_executes_catalog_workload(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch()
    connection = gate(descriptor, original)
    with pytest.raises(ValueError):
        owner.release(descriptor.unit_id, descriptor, connection, original)
    assert connection._sequence == 1 and client._failed and owner.latch.cancelled
    assert not (work / "source-binding.marker").exists()
    drained = launcher.drain(deadline(1))
    assert drained.helper_reaped and drained.direct_child_reaped
    cleanup = manager.force_cleanup(descriptor)
    assert cleanup.boundary_released and cleanup.residual_count == 0


def test_cancelled_late_stage_cannot_birth_after_boundary_removal(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch(stage=False)
    signal.pidfd_send_signal(launcher._pidfd, signal.SIGSTOP)
    try:
        with pytest.raises(ValueError):
            launcher.stage(deadline(0.15))
        assert launcher._cancelled and owner.latch.cancelled
        cleanup = manager.force_cleanup(descriptor)
        assert cleanup.boundary_released and cleanup.residual_count == 0
    finally:
        signal.pidfd_send_signal(launcher._pidfd, signal.SIGCONT)
    assert launcher.drain(deadline(1)).helper_reaped
    assert not (work / "source-binding.marker").exists()


def test_queued_stage_rejects_original_removed_boundary_fd(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch(stage=False)
    signal.pidfd_send_signal(launcher._pidfd, signal.SIGSTOP)
    try:
        recipe = launcher.recipe
        packet = LaunchPacket(
            1,
            1,
            int(original.monotonic_seconds * 1e9),
            recipe.scope,
            recipe.device,
            recipe.inode,
        )
        assert launcher.channel.send(packet.encode()) == 128
        cleanup = manager.force_cleanup(descriptor)
        assert cleanup.boundary_released and cleanup.residual_count == 0
    finally:
        signal.pidfd_send_signal(launcher._pidfd, signal.SIGCONT)
    until = time.monotonic() + 1
    while time.monotonic() < until:
        if os.waitid(os.P_PIDFD, launcher._pidfd, os.WEXITED | os.WNOHANG | os.WNOWAIT):
            break
        time.sleep(0.005)
    else:
        pytest.fail("native Stage did not reject its removed original boundary")
    assert not (work / "source-binding.marker").exists()


def test_actual_issuer_eof_loss_closes_release_and_reaps_child(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch()
    connection = gate(descriptor, original)
    launcher.channel.shutdown(socket.SHUT_WR)
    until = time.monotonic() + 1
    while time.monotonic() < until:
        if os.waitid(os.P_PIDFD, launcher._pidfd, os.WEXITED | os.WNOHANG | os.WNOWAIT):
            break
        time.sleep(0.005)
    else:
        pytest.fail("native issuer did not terminate on EOF")
    with pytest.raises(ValueError):
        owner.release(descriptor.unit_id, descriptor, connection, original)
    assert connection._sequence == 0 and not (work / "source-binding.marker").exists()


def test_actual_child_loss_before_release_keeps_catalog_silent(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch()
    connection = gate(descriptor, original)
    signal.pidfd_send_signal(launcher._childfd, signal.SIGKILL)
    until = time.monotonic() + 1
    while time.monotonic() < until:
        observed = launcher.observe(handle, deadline())
        if observed.leader_reaped:
            break
        time.sleep(0.005)
    assert observed.leader_reaped and not observed.running
    with pytest.raises(ValueError):
        owner.release(descriptor.unit_id, descriptor, connection, original)
    assert connection._sequence == 0 and not (work / "source-binding.marker").exists()


@pytest.mark.parametrize("launch_stack", [{"mode": "badelf"}], indirect=True)
def test_failed_exec_has_error_ack_and_no_running_or_readiness_credit(launch_stack):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch()
    connection = gate(descriptor, original)
    owner.release(descriptor.unit_id, descriptor, connection, original)
    until = time.monotonic() + 1
    while time.monotonic() < until:
        observed = launcher.observe(handle, deadline())
        if observed.leader_reaped:
            break
        time.sleep(0.005)
    assert observed.exec_error and observed.returncode == 127
    assert not observed.running and not observed.ready_for_execution
    assert not (work / "source-binding.marker").exists()


@pytest.mark.parametrize("mode", ["unknown-kind", "scope", "rights", "duplicate"])
def test_native_rejects_malformed_or_duplicate_control_and_closes_insertion(
    launch_stack, mode
):
    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch(stage=mode == "duplicate")
    recipe = launcher.recipe
    packet = bytearray(
        LaunchPacket(
            1,
            1,
            int(original.monotonic_seconds * 1e9),
            recipe.scope,
            recipe.device,
            recipe.inode,
        ).encode()
    )
    if mode == "unknown-kind":
        packet[7] = 99
    if mode == "scope":
        packet[24] ^= 1
    fd = os.open("/dev/null", os.O_RDONLY)
    try:
        anc = (
            [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [fd]))]
            if mode == "rights"
            else []
        )
        assert launcher.channel.sendmsg([packet], anc) == 128
    finally:
        os.close(fd)
    until = time.monotonic() + 1
    while time.monotonic() < until:
        if os.waitid(os.P_PIDFD, launcher._pidfd, os.WEXITED | os.WNOHANG | os.WNOWAIT):
            break
        time.sleep(0.005)
    else:
        pytest.fail("native malformed-control rejection did not terminate")
    assert not (work / "source-binding.marker").exists()
