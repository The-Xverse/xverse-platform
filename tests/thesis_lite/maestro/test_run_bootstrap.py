"""Real original-parent BS17 birth and independent exact-boundary watchdog."""

from dataclasses import asdict
import hashlib
from importlib.resources import files
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import time

import pytest
from xverse.maestro.affa_protocol import (
    AuthorityConfig,
    AuthorityFrame,
    AuthorityKind as K,
    AuthorityRecipe,
    AuthorityUnit,
)
from xverse.maestro.bootstrap import (
    BootstrapAdmission,
    BootstrapSession,
    encode_bootstrap,
    sealed_bootstrap_fd,
    _sealed,
    seal_helper_image,
)
from xverse.maestro.prbc import BoundaryDescriptor
from .test_affa_native import (
    Harness,
    authority_binary as authority_binary,
    digest,
    wait_marker,
)
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


@pytest.fixture(scope="module")
def run_bootstrap_binary(tmp_path_factory):
    root = tmp_path_factory.mktemp("run-bootstrap")
    source = root / "bootstrap.c"
    source.write_bytes(
        files("xverse.maestro").joinpath("native/bootstrap.c").read_bytes()
    )
    binary = root / "run-bootstrap"
    command = [
        "cc",
        "-DRUN_BOOTSTRAP",
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
    subprocess.run(command, check=True, capture_output=True, timeout=30)
    receipt = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt:
        Path(receipt).mkdir(parents=True, exist_ok=True)
        (Path(receipt) / "run-bootstrap-native.json").write_text(
            json.dumps(
                dict(
                    command=command,
                    returncode=0,
                    source_sha256=digest(source.read_bytes()).hex(),
                    binary_sha256=digest(binary.read_bytes()).hex(),
                )
            )
        )
    return binary


@pytest.fixture
def run_stack(environment, binaries, authority_binary, run_bootstrap_binary, tmp_path):
    factory, _, _ = environment
    manager, latch = factory(seconds=40)
    images = tuple(
        seal_helper_image(
            source,
            digest="sha256:" + digest(source.read_bytes()).hex(),
            argv0=str(source),
        )
        for source in (
            binaries["launcher"],
            binaries["bound-gate"],
            Path(sys.executable).resolve(),
            authority_binary,
        )
    )
    now = time.monotonic_ns()
    admission = BootstrapAdmission(
        "run",
        hashlib.sha256(b"owned-run-plan").hexdigest(),
        "bootstrap-approval",
        "sha256:" + digest(b"owned-environment").hex(),
        "sha256:" + digest(run_bootstrap_binary.read_bytes()).hex(),
        manager._admission.teardown_deadline,
        deadline(4.8),
        images[:3],
        images[3],
        manager._root_fd,
    )
    config = encode_bootstrap(admission)
    assert config.private_bytes[:8] == b"BC17\0\0\0\2"
    private = sealed_bootstrap_fd(config)
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
    session = None
    h = None
    cwd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    workload = seal_helper_image(
        binaries["workload"],
        digest="sha256:" + digest(binaries["workload"].read_bytes()).hex(),
        argv0=str(binaries["workload"]),
    )
    fds = []
    try:
        session = BootstrapSession(
            process, channel, config, manager, latch, deadline=deadline(2)
        )
        records, units = [], []
        for i in range(2):
            desc = BoundaryDescriptor("run", f"u{i}", 1, f"work-{i}", 0)
            manager.create_frozen(desc)
            cg = manager._entry(desc).fd
            recipe = AuthorityRecipe(
                ("/fixture", f"u{i}.marker", "single"), ("MAESTRO_VISIBLE=declared",)
            ).encode()
            recipe_fd = _sealed(recipe, "owned-bootstrap-recipe")
            fds.append(recipe_fd)
            info, work = os.fstat(cg), os.fstat(cwd)
            records.append(
                AuthorityUnit(
                    digest(bytes([i + 1])),
                    bytes.fromhex(workload.digest[7:]),
                    digest(recipe),
                    info.st_dev,
                    info.st_ino,
                    work.st_dev,
                    work.st_ino,
                    1,
                    2,
                )
            )
            units.append(
                dict(
                    descriptor=desc,
                    cg=cg,
                    recipe=recipe_fd,
                    generation=1,
                    operation=bytes([i + 1]) * 16,
                    intent=digest(b"intent" + bytes([i])),
                    mirror=digest(b"mirror" + bytes([i])),
                    boundary=digest(b"boundary" + bytes([i])),
                )
            )
        h = Harness(manager, cwd, workload, units)
        h.lease = session._lease
        h.config = AuthorityConfig(
            session._generation,
            h.lease,
            0,
            digest(b"owned-bootstrap-run"),
            digest(b"original-supervisor"),
            tuple(records),
        )
        helper = BoundaryDescriptor("run", "helper:authority", 1, "authority", 0)
        manager.create_frozen(helper)
        private = _sealed(h.config.encode(), "owned-bootstrap-authority")
        fds.append(private)
        native_channel, native_peer = socket.socketpair(
            socket.AF_UNIX, socket.SOCK_SEQPACKET
        )
        native_channel.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        native_channel.settimeout(2)
        h.channel = native_channel
        yield session, manager, h, helper, private, native_peer, tmp_path
    finally:
        if h and h.channel:
            h.channel.close()
        if "native_peer" in locals():
            native_peer.close()
        observed = None
        if session:
            session.cancel("owned-run-bootstrap-teardown")
            observed = session.drain(deadline(1.8))
            assert observed.supervisor_reaped and observed.registered_children_reaped
            if observed.unacknowledged_births:
                # Deliberately rejected birth has no ACK: external FD disposal is
                # separate from ordinary ownership/wait or issuance completeness.
                session._pidfd_capability.close()
                os.close(session._pidfd)
                session.channel.close()
            else:
                for client in session._clients.values():
                    client.dispose()
                session.dispose()
        else:
            process.wait(timeout=3)
            channel.close()
        process.wait(timeout=2)
        assert process.stderr.read() == b""
        process.stderr.close()
        # Issuer death and original-parent wait precede any C1 release below.
        for entry in manager._entries.values():
            if entry.state != "released":
                result = manager.force_cleanup(entry.descriptor)
                assert result.boundary_released and result.residual_count == 0
        if h:
            for fd in h.childfds:
                os.close(fd)
        for fd in fds:
            os.close(fd)
        for image in (*images, workload):
            os.close(image.descriptor)
        os.close(cwd)
        output = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
        if output and observed:
            (
                Path(output) / ("run-bootstrap-waits-" + tmp_path.name + ".json")
            ).write_text(
                json.dumps(
                    dict(
                        bootstrap_drain=asdict(observed),
                        original_helper_count=len(session._children),
                        original_helpers_actually_reaped=True,
                        all_original_C1_released=True,
                        workload_direct_child_waits_unknown=bool(
                            h and (h.childfds or session._clients)
                        ),
                        start_monotonic_ns=now,
                    )
                )
            )


def start_authority(stack, monkeypatch):
    session, manager, h, helper, private, peer, work = stack

    def forbidden(*args, **kwargs):
        pytest.fail("runtime attempted Popen")

    for unit in h.units:
        session.watch(unit["descriptor"], deadline(2))
    with monkeypatch.context() as patch:
        patch.setattr(subprocess, "Popen", forbidden)
        child = session.birth(4, helper, helper, peer, private, deadline(2))
        session.activate(child, deadline(1.8))
    h.process = child
    raw, anc, flags, _ = h.channel.recvmsg(321, socket.CMSG_SPACE(12))
    assert not flags and len(anc) == 1
    ready = AuthorityFrame.decode(raw)
    assert ready == AuthorityFrame(
        K.READY, 0, h.lease, h.config.scope, epoch=0, lease_ns=h.lease
    )
    for i, unit in enumerate(h.units):
        record = h.config.units[i]
        frame = AuthorityFrame(
            K.REGISTER,
            1,
            h.end(),
            h.config.scope,
            i + 1,
            0,
            1,
            first=record.binding,
            second=record.image,
            third=record.recipe,
            fourth=unit["boundary"],
        )
        assert (
            h.rpc(frame, (unit["cg"], h.image.descriptor, h.cwd, unit["recipe"])).kind
            is K.REGISTERED
        )
    for i in range(2):
        assert h.rpc(h.frame(K.INTENT, i)).kind is K.INTENT_RECORDED
    return child


def wait_dead(fd):
    assert select.select([fd], [], [], 2.5)[0]


def test_original_parent_birth_without_runtime_popen(run_stack, monkeypatch):
    session, _, h, _, _, _, work = run_stack
    child = start_authority(run_stack, monkeypatch)
    assert (
        os.waitid(
            os.P_PIDFD, child._capability.fileno(), os.WEXITED | os.WNOHANG | os.WNOWAIT
        )
        is None
    )
    for i in range(2):
        h.stage(i)
        h.arm(i)
        assert h.release(i).kind is K.RELEASED
        wait_marker(work / f"u{i}.marker")
    h.cancel()
    for i in range(2):
        h.stop_retire(i)
    assert len(session._children) == 1 and len(session._watches) == 2


@pytest.mark.parametrize("trigger", ["channel", "lease"])
def test_stopped_authority_cannot_thaw_after_watchdog_cleanup(
    run_stack, monkeypatch, trigger
):
    session, manager, h, _, _, _, work = run_stack
    child = start_authority(run_stack, monkeypatch)
    for i in range(2):
        h.stage(i)
        h.arm(i)
        assert h.release(i).kind is K.RELEASED
        wait_marker(work / f"u{i}.marker")
    signal.pidfd_send_signal(child._capability.fileno(), signal.SIGSTOP)
    # Ending the bootstrap's original private channel drives its independent native
    # watchdog while Python has not latched cancellation or performed C1 cleanup.
    if trigger == "channel":
        session.channel.shutdown(socket.SHUT_WR)
    else:
        assert select.select([child._capability.fileno()], [], [], 6)[0]
    wait_dead(child._capability.fileno())
    wait_dead(session._pidfd_capability.fileno())
    assert not session.latch.cancelled
    assert all(
        manager._read(manager._entry(u["descriptor"]), "cgroup.events").splitlines()[-1]
        == "frozen 1"
        for u in h.units
    )
    assert child._wait(child._capability.fileno(), consume=True) is not None
    assert child.returncode == -signal.SIGKILL
    with pytest.raises(ProcessLookupError):
        signal.pidfd_send_signal(child._capability.fileno(), signal.SIGCONT)


def test_authority_death_triggers_watchdog_before_lease(run_stack, monkeypatch):
    session, manager, h, _, _, _, _ = run_stack
    child = start_authority(run_stack, monkeypatch)
    for i in range(2):
        h.stage(i)
        h.arm(i)
        assert h.release(i).kind is K.RELEASED
    signal.pidfd_send_signal(child._capability.fileno(), signal.SIGKILL)
    wait_dead(session._pidfd_capability.fileno())
    assert time.monotonic_ns() < session._lease
    assert all(
        "frozen 1" in manager._read(manager._entry(u["descriptor"]), "cgroup.events")
        for u in h.units
    )


def test_unwatched_initial_scope_closes_without_issuance_ack(run_stack):
    session, _, h, helper, private, peer, _ = run_stack
    session.watch(h.units[0]["descriptor"], deadline(2))
    with pytest.raises(ValueError):
        session.birth(4, helper, helper, peer, private, deadline(1))
    assert not session._children and len(session._pending) == 1


def test_duplicate_watch_rejects_without_native_mutation(run_stack):
    session, _, h, _, _, _, _ = run_stack
    session.watch(h.units[0]["descriptor"], deadline(2))
    before = session._sequence
    with pytest.raises(ValueError, match="WATCH-SCOPE"):
        session.watch(h.units[0]["descriptor"], deadline(2))
    assert session._sequence == before and len(session._watches) == 1


def test_successor_disables_legacy_stage_and_gate_roles(run_stack):
    session, _, _, helper, private, peer, _ = run_stack
    for role in (1, 2):
        with pytest.raises(ValueError, match="BIRTH-INPUT"):
            session.birth(role, helper, helper, peer, private, deadline(1))
    assert not session._issued and session._sequence == 0


def test_native_duplicate_watch_rejected(run_stack):
    session, manager, h, _, _, _, _ = run_stack
    session.watch(h.units[0]["descriptor"], deadline(2))
    with pytest.raises(ValueError):
        session._rpc(4, deadline(1), slot=2, fds=(h.units[0]["cg"],))
    assert session.latch.cancelled and len(session._watches) == 1


def test_native_watch_rejects_actual_different_parent(run_stack):
    session, manager, _, _, _, _, _ = run_stack
    # Negative transport control confined to this fixture's original owned root.
    # These external fixture directories never become runtime C1 capabilities.
    os.mkdir("foreign-parent", dir_fd=manager._root_fd)
    parent = os.open(
        "foreign-parent", os.O_RDONLY | os.O_DIRECTORY, dir_fd=manager._root_fd
    )
    leaf = None
    try:
        os.mkdir("foreign-leaf", dir_fd=parent)
        leaf = os.open("foreign-leaf", os.O_RDONLY | os.O_DIRECTORY, dir_fd=parent)
        freeze = os.open("cgroup.freeze", os.O_WRONLY, dir_fd=leaf)
        try:
            os.write(freeze, b"1")
        finally:
            os.close(freeze)
        with pytest.raises(ValueError):
            session._rpc(4, deadline(1), slot=1, fds=(leaf,))
        assert not session._watches
    finally:
        if leaf is not None:
            os.close(leaf)
        os.close(parent)
