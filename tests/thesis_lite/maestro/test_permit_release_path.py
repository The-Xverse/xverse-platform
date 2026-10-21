"""DV03-N observed on the native Release path (increment19, finding 432).

Admission-level tests already reject expired, not-yet-valid and replayed permits; here the same
stimuli meet the real persistence worker, native gate and owned boundary: a permit that expires
between intent and Release, and an intent-only restart where a second original worker reopens the
same M3 journal after the first was killed. A permit not yet valid is refused when the configuration
is sealed, before any worker exists, so "not yet valid at claim" is not constructible on the Release
path (finding 435); that test asserts the seal-time refusal and its zero effect instead.
"""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import os
import select
import signal
import socket
import subprocess
import sys
import time

import pytest

from xverse.maestro.admission import AdmissionError, permit_digest
from xverse.maestro.persistence import PersistenceClient, encode_configuration, sealed_input_fd
from xverse.maestro.owner import ReleaseOwner, StageSupervisor
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_admission import context
from .test_boundary import environment as environment, native as native
from .test_persistence import deadline, storage as storage
from .test_releasegate import guard_binary as guard_binary


def sealed(tmp_path, manager, *, not_before, expires_at, evidence="argus"):
    """test_persistence.configuration with explicit validity times and Argus root."""
    prepared, result, resources, bindings, approvals = context()
    new_bindings, new_approvals = [], []
    for binding, approval in zip(bindings, approvals):
        permit = replace(binding.permit, not_before=not_before, expires_at=expires_at)
        new_bindings.append(replace(binding, generation=1, permit=permit))
        new_approvals.append(replace(approval, generation=1, permit_content_digest=permit_digest(permit),
                                     not_before=not_before, expires_at=expires_at))
    return encode_configuration(prepared, result, resources, run_id="fixture-run", bindings=new_bindings,
                                approvals=new_approvals, session="host-session",
                                generation_deadline=manager._admission.teardown_deadline,
                                journal_path=tmp_path / "m3.jsonl", evidence_root=tmp_path / evidence)


def no_workload(marker, gate):
    assert gate._sequence == 0
    assert not select.select([marker], [], [], 0.05)[0]


def test_permit_expiring_between_intent_and_release_blocks_release(storage, native, guard_binary, tmp_path):
    start, stage, config, manager, latch = storage
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(seconds=2.5)
    owner, client, announce, release = start(override=sealed(tmp_path, manager, not_before=now - timedelta(seconds=30),
                                                             expires_at=expiry))
    unit_id = config.prepared.units[0].unit_id
    original = deadline(4)  # inside the fixture's teardown deadline (finding 435)
    owner.commit_intent(unit_id, original)
    unit_id, descriptor, child, marker, gate = stage(owner, guard_binary, native)
    wait = (expiry - datetime.now(timezone.utc)).total_seconds() + 0.3
    assert wait > 0, "stage outlived the permit before the stimulus"
    time.sleep(wait)
    with pytest.raises(ValueError) as raised:
        owner.release(unit_id, descriptor, gate, original)
    assert str(raised.value) == "ML-PERSIST-ACK", raised.value  # the worker refuses the expired permit (findings 463-465)
    no_workload(marker, gate)
    assert latch.cancelled
    assert manager.force_cleanup(descriptor).termination_observed
    assert child.wait(timeout=2) == 0
    assert client.drain(deadline(1)).worker_reaped


def test_not_yet_valid_permit_is_refused_at_seal_before_any_worker(storage, tmp_path):
    start, stage, config, manager, latch = storage
    now = datetime.now(timezone.utc)
    with pytest.raises(AdmissionError) as refused:
        sealed(tmp_path, manager, not_before=now + timedelta(seconds=30), expires_at=now + timedelta(seconds=60))
    assert str(refused.value) == "ML-PERMIT-M3: XVERSE-PERMIT-NOT-YET-VALID"
    assert not (tmp_path / "m3.jsonl").exists()
    assert not (tmp_path / "argus").exists()
    assert not latch.cancelled


def open_original_worker(selected, manager, latch):
    """test_persistence.storage.start without fault modes, bound to a caller-chosen run boundary."""
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    cfg = sealed_input_fd(selected)
    try:
        process = subprocess.Popen([sys.executable, "-I", "-m", "xverse.maestro.persistence_worker",
                                    str(child.fileno()), str(cfg)], pass_fds=(child.fileno(), cfg),
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    finally:
        child.close()
        os.close(cfg)
    try:
        client = PersistenceClient(process, parent, selected, latch, deadline=deadline(3))
    except BaseException:
        process.kill()
        process.wait(timeout=5)
        raise
    return process, ReleaseOwner.from_persistence(client, StageSupervisor(manager, latch), latch), client


def test_intent_only_restart_cannot_reclaim_through_a_new_original_worker(storage, environment, tmp_path):
    start, stage, config, manager, latch = storage
    factory, spawn, root = environment
    now = datetime.now(timezone.utc)
    times = dict(not_before=now - timedelta(seconds=30), expires_at=now + timedelta(seconds=60))
    owner, client, announce, release = start(override=sealed(tmp_path, manager, **times))
    unit_id = config.prepared.units[0].unit_id
    owner.commit_intent(unit_id, deadline(4))
    signal.pidfd_send_signal(client._pidfd, signal.SIGKILL)
    with pytest.raises((ValueError, OSError)):  # the product callers catch both (finding 435)
        client.abort(deadline(1))
    assert client._failed and latch.cancelled
    assert client.drain(deadline(1)).worker_reaped
    # Inside the same run the cancelled latch already refuses a second original worker.
    with pytest.raises(ValueError):
        start(override=sealed(tmp_path, manager, evidence="argus-same-run", **times))
    records = len(FileEvidenceJournal(tmp_path / "m3.jsonl").records)
    # A fresh run boundary reopening the same M3 journal: the restart proper.
    manager2, latch2 = factory(seconds=30, run_id="fixture-run")
    refused, process = None, None
    try:
        process, second, second_client = open_original_worker(
            sealed(tmp_path, manager2, evidence="argus-reopened", **times), manager2, latch2)
    except (ValueError, OSError) as error:
        refused = ("init", str(error))
    else:
        try:
            second.commit_intent(unit_id, deadline(4))
        except (ValueError, OSError) as error:
            refused = ("intent", str(error))
        finally:
            second_client.drain(deadline(1))
    print("DV03-P3", refused)
    assert refused is not None, "a new original worker reclaimed an intent-only unit"
    assert len(FileEvidenceJournal(tmp_path / "m3.jsonl").records) == records
    if process is not None:
        assert process.wait(timeout=5) is not None
