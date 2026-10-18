from dataclasses import FrozenInstanceError, replace
import copy
import hashlib
import json
import os
from pathlib import Path
import pickle
import select
import subprocess
import time
import uuid

import pytest

from xverse.maestro.prbc import (
    BoundaryAdmission,
    BoundaryDescriptor,
    BoundaryError,
    BoundaryLimits,
    ProcessBoundaryOps,
)
from xverse.maestro.supervisor import CancellationLatch
from xverse.maestro.time import HostDeadline


@pytest.fixture(scope="module")
def native(tmp_path_factory):
    target = tmp_path_factory.mktemp("boundary-native") / "boundary-fixture"
    command = [
        "cc",
        "-std=c11",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        str(Path(__file__).with_name("boundary_fixture.c")),
        "-o",
        str(target),
    ]
    subprocess.run(command, check=True, capture_output=True, timeout=20)
    receipt_dir = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
    if receipt_dir:
        output = Path(receipt_dir)
        output.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        (output / ("native-" + digest + ".json")).write_text(
            json.dumps(
                {
                    "command": command,
                    "returncode": 0,
                    "source_sha256": hashlib.sha256(
                        Path(__file__).with_name("boundary_fixture.c").read_bytes()
                    ).hexdigest(),
                    "binary_sha256": digest,
                    "compiler": subprocess.check_output(
                        ["cc", "--version"], text=True
                    ).splitlines()[0],
                    "role": "fixed component-test fixture, not admitted launcher",
                },
                indent=2,
            )
            + "\n"
        )
        (output / ("native-" + digest + ".bin")).write_bytes(target.read_bytes())
    return target


def _write(directory, name, data):
    fd = os.open(name, os.O_WRONLY, dir_fd=directory)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def _remove_owned_tree(parent_fd, name):
    """External test harness authority over its own fresh test subtree only."""
    fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY, dir_fd=parent_fd)
    try:
        _write(fd, "cgroup.kill", b"1")
        for item in os.scandir(fd):
            if item.is_dir(follow_symlinks=False):
                _remove_owned_tree(fd, item.name)
        deadline = time.monotonic() + 3
        while True:
            try:
                os.rmdir(name, dir_fd=parent_fd)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.005)
    finally:
        os.close(fd)


@pytest.fixture
def environment(tmp_path):
    # Discovery selects a test parent; it never grants runtime ownership/recovery.
    current = Path(
        "/sys/fs/cgroup" + Path("/proc/self/cgroup").read_text().strip().split("::")[1]
    )
    root_name = "maestro-component-" + uuid.uuid4().hex
    parent_fd = os.open(current, os.O_RDONLY | os.O_DIRECTORY)
    receipt_root = Path(os.environ.get("MAESTRO_BOUNDARY_RECEIPTS", str(tmp_path)))
    receipt_root.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_root / (root_name + ".json")
    parent_identity = os.fstat(parent_fd)
    receipt = {
        "scope": "private owned component-test harness, not runtime C1",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "parent_identity": [parent_identity.st_dev, parent_identity.st_ino],
        "parent_path": str(current),
        "root_name": root_name,
        "state": "reserved",
        "root_removed": False,
        "workers_reaped": False,
    }

    def save():
        pending = receipt_path.with_suffix(".pending")
        with pending.open("w") as stream:
            json.dump(receipt, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(pending, receipt_path)
        receipt_fd = os.open(receipt_root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(receipt_fd)
        finally:
            os.close(receipt_fd)

    save()  # original harness reservation is retained before host allocation
    os.mkdir(root_name, mode=0o700, dir_fd=parent_fd)
    root_fd = os.open(root_name, os.O_RDONLY | os.O_DIRECTORY, dir_fd=parent_fd)
    identity = os.fstat(root_fd)
    receipt.update(root_identity=[identity.st_dev, identity.st_ino], state="allocated")
    save()
    monitors = []
    workers = []
    pipes = []

    def factory(*, seconds=4, reservation=True, epoch=0, operation=2):
        facts = BoundaryAdmission(
            "run",
            "supervisor",
            "affa",
            "bootstrap-approval",
            "cleanup-approval",
            "reservation-approval" if reservation else None,
            HostDeadline("host-session", time.monotonic() + seconds),
            epoch,
        )
        latch = CancellationLatch()
        manager = ProcessBoundaryOps(
            root_fd, facts, latch, BoundaryLimits(operation_seconds=operation)
        )
        monitors.append(manager)
        return manager, latch

    def spawn(native, manager, descriptor, mode="single", retained_fd=None):
        entry = manager._entries[descriptor.key]
        cgfd = retained_fd if retained_fd is not None else entry.fd
        read, write = os.pipe()
        pipes.append(read)
        try:
            process = subprocess.Popen(
                [str(native), str(cgfd), str(write), mode],
                pass_fds=(cgfd, write),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        finally:
            os.close(write)
        workers.append(process)
        assert select.select([process.stdout], [], [], 2)[0]
        line = process.stdout.readline().strip()
        return process, read, line

    yield factory, spawn, root_fd
    # Runtime library failures remain unresolved. Harness cleanup is separate evidence.
    try:
        for entry in list(os.scandir(root_fd)):
            if entry.is_dir(follow_symlinks=False):
                _remove_owned_tree(root_fd, entry.name)
        for process in workers:
            process.wait(timeout=3)
            process.stdout.close()
            process.stderr.close()
        receipt["workers_reaped"] = True
        for fd in pipes:
            os.close(fd)
        retained_parents = []
        for manager in monitors:
            for entry in manager._entries.values():
                if entry.fd >= 0:
                    manager.dispose_external_release(entry.descriptor)
            if manager._root_fd >= 0:
                try:
                    manager.close()
                except BoundaryError:
                    retained_parents.append(manager)
        os.rmdir(root_name, dir_fd=parent_fd)
        receipt.update(root_removed=True, state="released-by-test-harness")
        # Missing child identity cannot become ordinary library success. The
        # external harness has now removed its entire original, exact empty root.
        for manager in retained_parents:
            with pytest.raises(FileNotFoundError):
                os.open("cgroup.events", os.O_RDONLY, dir_fd=manager._root_fd)
            os.close(manager._root_fd)
            manager._root_fd = -1
        receipt["external_parent_descriptor_disposals"] = len(retained_parents)
    finally:
        save()
        os.close(root_fd)
        os.close(parent_fd)


def descriptor(unit="unit", epoch=0):
    return BoundaryDescriptor("run", unit, 0, "boundary-" + unit, epoch)


@pytest.mark.parametrize("field", ["generation", "creation_epoch"])
@pytest.mark.parametrize("bad", [True, -1, 1.5, "0", 2**80])
def test_invalid_descriptor_integers(field, bad):
    with pytest.raises(BoundaryError):
        replace(descriptor(), **{field: bad})


@pytest.mark.parametrize(
    "option",
    [
        "workload",
        "duration",
        "residual_children",
        "marker",
        "boundary_id",
        "epoch",
        "unknown",
    ],
)
def test_closed_options_reject_before_allocation(environment, option):
    factory, _, root = environment
    manager, _ = factory()
    before = tuple(os.listdir(root))
    with pytest.raises(BoundaryError, match="OPTIONS"):
        manager.create_frozen(descriptor(), **{option: True})
    assert tuple(os.listdir(root)) == before and not manager._entries


def test_real_cp03_empty_boundary_release(environment):
    factory, _, _ = environment
    manager, _ = factory()
    record = manager.create_frozen(descriptor())
    assert record.state == "frozen" and record.identity_retained
    assert record.membership_complete and record.residual_count == 0
    assert manager.residual_membership(descriptor()) == ()
    with pytest.raises(FrozenInstanceError):
        record.state = "released"
    result = manager.force_cleanup(descriptor())
    assert result.boundary_released and not result.identity_retained
    assert not result.termination_observed and not result.ready_for_execution
    assert manager.force_cleanup(descriptor()) is result
    with pytest.raises(BoundaryError, match="OBSERVATION-CLOSED"):
        manager.residual_membership(descriptor())
    manager.close()


def test_real_frozen_birth_force_cleanup_and_deleted_fd_fence(environment, native):
    factory, spawn, _ = environment
    manager, _ = factory()
    desc = descriptor()
    manager.create_frozen(desc)
    saved_fd = os.dup(manager._entries[desc.key].fd)
    try:
        worker, marker, line = spawn(native, manager, desc)
        assert line.startswith("CHILD "), line
        pid = int(line.split()[1])
        assert not select.select([marker], [], [], 0.03)[0], "frozen child ran marker"
        assert manager.residual_membership(desc) == (pid,)
        result = manager.force_cleanup(desc)
        assert result.boundary_released and result.termination_observed
        worker.wait(timeout=2)
        late, _, reply = spawn(native, manager, desc, retained_fd=saved_fd)
        assert reply.startswith("ERROR "), reply
        assert late.wait(timeout=2) == 77
    finally:
        os.close(saved_fd)


def test_real_leader_death_keeps_descendant_in_scope_and_sentinel_untouched(
    environment, native
):
    factory, spawn, _ = environment
    manager, _ = factory()
    desc, sentinel_desc = descriptor(), descriptor("sentinel")
    manager.create_frozen(desc)
    manager.create_frozen(sentinel_desc)
    leader, marker, line = spawn(native, manager, desc, "descendant")
    sentinel, sentinel_marker, sentinel_line = spawn(native, manager, sentinel_desc)
    assert line.startswith("CHILD ") and sentinel_line.startswith("CHILD ")
    leader_pid = int(line.split()[1])
    # Test-only thaw exercises membership. This is not an admitted Release method.
    _write(manager._entries[desc.key].fd, "cgroup.freeze", b"0")
    assert select.select([marker], [], [], 2)[0]
    first = os.read(marker, 1)
    assert first == b"M"
    assert select.select([marker], [], [], 2)[0]
    assert os.read(marker, 1) == b"D"
    leader.wait(timeout=2)  # fixture reaped its leader, descendant remains
    manager._freeze(manager._entries[desc.key])
    members = manager.residual_membership(desc)
    assert len(members) == 1 and leader_pid not in members
    assert manager.force_cleanup(desc).boundary_released
    assert manager.residual_membership(sentinel_desc) == (
        int(sentinel_line.split()[1]),
    )
    assert (
        sentinel.poll() is None and not select.select([sentinel_marker], [], [], 0)[0]
    )
    assert manager.force_cleanup(sentinel_desc).boundary_released


def test_cancel_before_stage_allocates_nothing(environment):
    factory, _, root = environment
    manager, latch = factory()
    latch.cancel("operator-stop")
    before = tuple(os.listdir(root))
    with pytest.raises(BoundaryError, match="CANCELLED"):
        manager.create_frozen(descriptor())
    assert tuple(os.listdir(root)) == before and not manager._entries


def test_cancel_during_allocation_retains_original_epoch_for_cleanup(
    environment, monkeypatch
):
    factory, _, _ = environment
    manager, latch = factory(epoch=8)
    original = os.mkdir

    def late_allocation(*args, **kwargs):
        original(*args, **kwargs)
        latch.cancel("during-stage")

    with monkeypatch.context() as patch:
        patch.setattr(os, "mkdir", late_allocation)
        with pytest.raises(BoundaryError, match="LATE-STAGE") as error:
            manager.create_frozen(descriptor(epoch=8))
    assert error.value.record.state == "partial"
    assert error.value.record.descriptor.creation_epoch == 8
    assert error.value.record.release_epoch == 9
    assert manager.force_cleanup(descriptor(epoch=8)).boundary_released


def test_fields_copies_and_replacement_registry_do_not_grant_authority(environment):
    factory, _, _ = environment
    manager, _ = factory()
    manager.create_frozen(descriptor())
    replacement, _ = factory()
    with pytest.raises(TypeError):
        copy.copy(manager)
    forged = object.__new__(ProcessBoundaryOps)
    forged.__dict__.update(manager.__dict__)
    for value in [forged, replacement]:
        with pytest.raises(BoundaryError, match="OWNERSHIP"):
            value.force_cleanup(descriptor())
    with pytest.raises(TypeError):
        pickle.dumps(manager)
    manager._caps.clear()
    manager._reservations.clear()
    result = manager.force_cleanup(descriptor())
    assert result.state == "unresolved" and result.identity_retained
    assert not result.boundary_released


def test_failed_release_retains_identity_then_original_retry_succeeds(
    environment, monkeypatch
):
    factory, _, _ = environment
    manager, _ = factory()
    manager.create_frozen(descriptor())
    with monkeypatch.context() as patch:
        patch.setattr(
            os,
            "rmdir",
            lambda *args, **kwargs: (_ for _ in ()).throw(PermissionError()),
        )
        failed = manager.force_cleanup(descriptor())
    assert failed.state == "unresolved" and failed.identity_retained
    assert manager.force_cleanup(descriptor()).boundary_released


def test_missing_membership_is_unknown_not_empty(environment, monkeypatch):
    factory, _, _ = environment
    manager, _ = factory()
    manager.create_frozen(descriptor())
    original = manager._read

    def unreadable(entry, name):
        if name == "cgroup.procs":
            raise PermissionError()
        return original(entry, name)

    with monkeypatch.context() as patch:
        patch.setattr(manager, "_read", unreadable)
        with pytest.raises(BoundaryError) as error:
            manager.residual_membership(descriptor())
    assert error.value.record.state == "unresolved"
    assert not error.value.record.membership_complete
    assert manager.force_cleanup(descriptor()).boundary_released


def test_non_cgroup_parent_rejects_without_effect(tmp_path):
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        facts = BoundaryAdmission(
            "run",
            "supervisor",
            "affa",
            "bootstrap",
            "cleanup",
            None,
            HostDeadline("host", time.monotonic() + 1),
            0,
        )
        with pytest.raises(BoundaryError, match="FILESYSTEM"):
            ProcessBoundaryOps(
                fd, facts, CancellationLatch(), BoundaryLimits(operation_seconds=1)
            )
        assert not list(tmp_path.iterdir())
    finally:
        os.close(fd)


@pytest.mark.parametrize("value", [True, 0, -1, float("nan"), float("inf"), 10**1000])
def test_bad_boundary_limits_are_closed_diagnostics(value):
    with pytest.raises(BoundaryError, match="ADMISSION"):
        BoundaryLimits(operation_seconds=1, freeze_seconds=value)


@pytest.mark.parametrize("reservation", [True, False])
def test_cp02_empty_reservation_is_not_c1(environment, monkeypatch, reservation):
    factory, _, _ = environment
    manager, _ = factory(reservation=reservation)
    original_read = manager._read

    def fail_before_c1(entry, name):
        if name == "cgroup.type":
            raise BoundaryError("ML-TEARDOWN-INJECTED-CP02")
        return original_read(entry, name)

    with monkeypatch.context() as patch:
        patch.setattr(manager, "_read", fail_before_c1)
        with pytest.raises(BoundaryError):
            manager.create_frozen(descriptor())
    assert manager._entries[descriptor().key].c1 is None
    with monkeypatch.context() as patch:
        patch.setattr(
            manager,
            "_write",
            lambda *args: (_ for _ in ()).throw(
                AssertionError("reservation mutated freeze/kill")
            ),
        )
        result = manager.force_cleanup(descriptor())
    assert result.boundary_released is reservation
    assert not result.termination_observed
    if not reservation:
        assert result.state == "unresolved" and result.identity_retained


def test_cp02_live_allocation_never_gains_force_or_freeze(
    environment, native, monkeypatch
):
    factory, spawn, _ = environment
    manager, _ = factory()
    original_read = manager._read

    def fail_before_c1(entry, name):
        if name == "cgroup.type":
            raise BoundaryError("ML-TEARDOWN-INJECTED-CP02")
        return original_read(entry, name)

    with monkeypatch.context() as patch:
        patch.setattr(manager, "_read", fail_before_c1)
        with pytest.raises(BoundaryError):
            manager.create_frozen(descriptor())
    worker, marker, line = spawn(native, manager, descriptor())
    assert line.startswith("CHILD ") and select.select([marker], [], [], 2)[0]
    with monkeypatch.context() as patch:
        patch.setattr(
            manager,
            "_write",
            lambda *args: (_ for _ in ()).throw(
                AssertionError("reservation used C1 right")
            ),
        )
        result = manager.force_cleanup(descriptor())
    assert result.state == "unresolved" and result.identity_retained
    assert worker.poll() is None


def test_lost_c1_cannot_fall_back_to_reservation(environment):
    factory, _, _ = environment
    manager, _ = factory()
    manager.create_frozen(descriptor())
    manager._caps.clear()
    result = manager.force_cleanup(descriptor())
    assert result.state == "unresolved" and result.identity_retained
    assert result.diagnostic == "ML-OWNERSHIP-BOUNDARY-CAPABILITY"


def test_expired_original_authority_stays_unresolved(environment):
    factory, _, _ = environment
    manager, _ = factory(seconds=0.1)
    manager.create_frozen(descriptor())
    time.sleep(0.11)
    result = manager.force_cleanup(descriptor())
    assert result.state == "unresolved" and result.identity_retained
    assert result.diagnostic == "ML-TIMEOUT-BOUNDARY-AUTHORITY"


def test_replaced_name_is_not_targeted(environment):
    factory, _, root = environment
    manager, _ = factory()
    manager.create_frozen(descriptor())
    entry = manager._entries[descriptor().key]
    os.rmdir(entry.name, dir_fd=root)
    os.mkdir(entry.name, dir_fd=root)
    result = manager.force_cleanup(descriptor())
    assert result.state == "unresolved" and result.identity_retained
    assert os.stat(entry.name, dir_fd=root).st_ino != entry.identity[1]


def test_unknown_membership_closes_new_stages(environment, monkeypatch):
    factory, _, _ = environment
    manager, latch = factory()
    manager.create_frozen(descriptor())
    original_read = manager._read

    def corrupt(entry, name):
        return "0\n" if name == "cgroup.procs" else original_read(entry, name)

    with monkeypatch.context() as patch:
        patch.setattr(manager, "_read", corrupt)
        with pytest.raises(BoundaryError):
            manager.residual_membership(descriptor())
    assert latch.cancelled
    with pytest.raises(BoundaryError, match="CANCELLED"):
        manager.create_frozen(descriptor("new"))
    assert manager.force_cleanup(descriptor()).boundary_released


def test_changed_creation_epoch_does_not_authorize_old_boundary(environment):
    factory, _, _ = environment
    manager, _ = factory()
    manager.create_frozen(descriptor())
    with pytest.raises(BoundaryError):
        manager.create_frozen(replace(descriptor(), creation_epoch=1))
    assert manager.force_cleanup(descriptor()).boundary_released


@pytest.mark.parametrize(
    "text", ["1\n1\n", "-1\n", "x\n", "9" * 5000, str(2**31) + "\n"]
)
def test_malformed_membership_stays_unknown(environment, monkeypatch, text):
    factory, _, _ = environment
    manager, latch = factory()
    manager.create_frozen(descriptor())
    original_read = manager._read
    with monkeypatch.context() as patch:
        patch.setattr(
            manager,
            "_read",
            lambda e, n: text if n == "cgroup.procs" else original_read(e, n),
        )
        with pytest.raises(BoundaryError) as error:
            manager.residual_membership(descriptor())
    assert not error.value.record.membership_complete
    assert error.value.record.residual_count is None and latch.cancelled
    assert manager.force_cleanup(descriptor()).boundary_released


def test_admission_and_limits_are_copied_from_caller(environment):
    factory, _, root = environment
    # Register this manager with the harness for independent final cleanup.
    manager, _ = factory()
    admission = manager._admission
    limits = BoundaryLimits(operation_seconds=2)
    other = ProcessBoundaryOps(root, admission, CancellationLatch(), limits)
    try:
        object.__setattr__(limits, "poll_seconds", float("nan"))
        object.__setattr__(admission.teardown_deadline, "monotonic_seconds", 0)
        other.create_frozen(descriptor())
        assert other.force_cleanup(descriptor()).boundary_released
        other.close()
    finally:
        # This extra manager created only the exact retained scope above.
        if other._root_fd >= 0:
            other.force_cleanup(descriptor())
            other.close()


def test_lost_identity_during_allocation_never_uses_name_as_authority(
    environment, monkeypatch
):
    factory, _, _ = environment
    manager, _ = factory()
    original_open = os.open

    def fail_child_open(path, flags, *args, **kwargs):
        if isinstance(path, str) and path.startswith("mlb-"):
            raise PermissionError()
        return original_open(path, flags, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(os, "open", fail_child_open)
        with pytest.raises(BoundaryError) as error:
            manager.create_frozen(descriptor())
    assert (
        error.value.record.state == "partial"
        and not error.value.record.identity_retained
    )
    result = manager.force_cleanup(descriptor())
    assert result.state == "unresolved" and not result.boundary_released


def test_deadline_rechecked_after_identity_work(environment, monkeypatch):
    factory, _, _ = environment
    manager, _ = factory(seconds=0.1)
    manager.create_frozen(descriptor())
    entry = manager._entries[descriptor().key]
    original_verify = manager._verify

    def slow_verify(value):
        original_verify(value)
        time.sleep(0.11)

    with monkeypatch.context() as patch:
        patch.setattr(manager, "_verify", slow_verify)
        patch.setattr(
            os,
            "write",
            lambda *args: (_ for _ in ()).throw(
                AssertionError("expired authority wrote")
            ),
        )
        with pytest.raises(BoundaryError, match="TIMEOUT"):
            manager._write(entry, "cgroup.freeze", b"1")


def test_forked_holder_cannot_use_original_c1(environment):
    factory, _, _ = environment
    manager, _ = factory()
    manager.create_frozen(descriptor())
    read, write = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read)
        try:
            manager.force_cleanup(descriptor())
            os.write(write, b"bad")
        except BoundaryError as error:
            os.write(write, error.code.encode())
        finally:
            os._exit(0)
    os.close(write)
    try:
        assert select.select([read], [], [], 2)[0]
        assert os.read(read, 128) == b"ML-OWNERSHIP-BOUNDARY-HOLDER"
    finally:
        os.close(read)
        os.kill(child, 9)
        os.waitpid(child, 0)
    assert manager.force_cleanup(descriptor()).boundary_released


def test_idempotent_stage_revalidation_failure_closes_starts(environment):
    factory, _, _ = environment
    manager, latch = factory()
    manager.create_frozen(descriptor())
    manager._caps.clear()
    with pytest.raises(BoundaryError):
        manager.create_frozen(descriptor())
    assert latch.cancelled
    assert manager.record(descriptor()).state == "unresolved"
    with pytest.raises(BoundaryError, match="CANCELLED"):
        manager.create_frozen(descriptor("new"))


def test_live_boundary_prevents_early_descriptor_disposal(environment):
    factory, _, _ = environment
    manager, _ = factory()
    manager.create_frozen(descriptor())
    with pytest.raises(BoundaryError, match="RETAINED"):
        manager.dispose_external_release(descriptor())
    with pytest.raises(BoundaryError, match="RETAINED"):
        manager.close()
    assert manager.force_cleanup(descriptor()).boundary_released


def test_long_original_lease_keeps_short_operation_budget(
    environment, native, monkeypatch
):
    factory, spawn, _ = environment
    manager, _ = factory(seconds=30, operation=0.05)
    original_deadline = manager._admission.teardown_deadline.monotonic_seconds
    manager.create_frozen(descriptor())
    worker, _, line = spawn(native, manager, descriptor())
    assert line.startswith("CHILD ")
    began = time.monotonic()
    with monkeypatch.context() as patch:
        patch.setattr(manager, "_events", lambda entry: {"populated": 1, "frozen": 1})
        result = manager.force_cleanup(descriptor())
    assert time.monotonic() - began < 1
    assert result.state == "unresolved" and result.identity_retained
    assert manager._admission.teardown_deadline.monotonic_seconds == original_deadline
    worker.wait(timeout=2)
    assert manager.force_cleanup(descriptor()).boundary_released
