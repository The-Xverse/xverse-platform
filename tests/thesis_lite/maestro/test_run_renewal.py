"""Actual original BS17/shared-AFFA renewal; original operation ends stay fixed."""
import select
import signal
import time

import pytest
from xverse.maestro.affa_protocol import AuthorityKind as K
from xverse.maestro.time import HostDeadline
from xverse.argus import EvidenceStore
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_generation_claim import ready
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def target(broker):
    return HostDeadline(broker.owner.session, time.monotonic() + 4.9)


def test_actual_shared_renewal_keeps_original_live_handles_past_old_lease(request, monkeypatch):
    stack, _, _, _ = ready(request, monkeypatch)
    broker, facade, _, work = stack
    old = max(broker.session._lease, broker.connection._lease)
    originals = [(i, i._handle, i.recipe.operation_deadline_ns) for i in broker.issuers]
    epoch = broker.connection.epoch
    lease = target(broker)
    before = FileEvidenceJournal(work.parent / 'm3.jsonl').records
    result = broker.renew(lease, deadline(1))
    assert FileEvidenceJournal(work.parent / 'm3.jsonl').records == before
    assert result.bootstrap_lease_ns == result.authority_lease_ns == int(lease.monotonic_seconds * 1e9)
    assert result.epoch == epoch and not result.ready_for_execution
    select.select([], [], [], max(0, old / 1e9 + 0.03 - time.monotonic()))
    for issuer, handle, end in originals:
        assert broker.issuer(issuer.unit_id) is issuer and issuer._handle is handle
        assert issuer.recipe.operation_deadline_ns == end
        assert facade.check_unit_health(issuer.unit_id, deadline(0.5)).ready
    assert broker.connection.epoch == epoch


@pytest.mark.parametrize('kind', ['unchanged', 'session', 'too-long'])
def test_invalid_renewal_rejects_before_rpc_or_cancellation(request, monkeypatch, kind):
    stack, _, _, _ = ready(request, monkeypatch)
    broker = stack[0]
    lease = target(broker)
    if kind == 'unchanged':
        lease = HostDeadline(broker.owner.session, broker.connection._lease / 1e9)
    elif kind == 'session':
        lease = HostDeadline('different-session', lease.monotonic_seconds)
    else:
        lease = deadline(6)
    before = broker.connection.sequence, broker.session._sequence, broker.connection._lease, broker.session._lease
    with pytest.raises(ValueError):
        broker.renew(lease, deadline(0.5))
    assert before == (broker.connection.sequence, broker.session._sequence, broker.connection._lease, broker.session._lease)
    assert not broker.owner.latch.cancelled and broker._cancel_result is None


@pytest.mark.parametrize('name', ['owner', 'broker'])
def test_renewal_lock_conflict_has_no_effects(request, monkeypatch, name):
    stack, _, _, _ = ready(request, monkeypatch)
    broker = stack[0]
    lock = broker.owner._lock if name == 'owner' else broker._lock
    before = broker.connection.sequence, broker.session._sequence
    lock.acquire()
    try:
        with pytest.raises(ValueError, match='CONFLICT'):
            broker.renew(target(broker), deadline(0.5))
    finally:
        lock.release()
    assert before == (broker.connection.sequence, broker.session._sequence)
    assert not broker.owner.latch.cancelled and broker._cancel_result is None


def test_stopped_storage_prevents_shared_renewal_and_fences_authority(request, monkeypatch):
    stack, _, _, _ = ready(request, monkeypatch)
    broker, _, client, _ = stack
    before = broker.connection._lease, broker.session._lease
    signal.pidfd_send_signal(client.process._capability.fileno(), signal.SIGSTOP)
    with pytest.raises(ValueError):
        broker.renew(target(broker), deadline(0.35))
    assert before == (broker.connection._lease, broker.session._lease)
    assert broker._cancel_result is not None and broker.owner.latch.cancelled
    observed = broker.connection.revoke(deadline(1))
    assert observed.issuer_dead and observed.issuer_reaped
    assert not observed.workload_waits_known


def test_cancellation_before_native_renewal_ack_commit_cannot_succeed(request, monkeypatch):
    stack, _, _, _ = ready(request, monkeypatch)
    broker = stack[0]
    receive = broker.connection._receive
    seen = []

    def cancel_before_commit(until):
        reply, fds = receive(until)
        if reply.kind is K.RENEWED:
            seen.append(reply)
            broker.cancel('renewal-ack-race', deadline=deadline(0.5))
        return reply, fds

    monkeypatch.setattr(broker.connection, '_receive', cancel_before_commit)
    with pytest.raises(ValueError):
        broker.renew(target(broker), deadline(1))
    assert len(seen) == 1  # Actual native reply, never a constructed success.
    assert broker._cancel_result is not None and broker.owner.latch.cancelled
    assert broker.connection._revoked


def test_missing_actual_mirror_prevents_renewal_without_claiming_either_lease(request, monkeypatch):
    stack, _, _, _ = ready(request, monkeypatch)
    broker, _, _, work = stack
    reader = EvidenceStore.read_run(work.parent / 'argus')
    (work.parent / 'argus' / reader.manifest['eventStream']['path']).unlink()
    before = broker.connection._lease, broker.session._lease
    with pytest.raises(ValueError):
        broker.renew(target(broker), deadline(0.8))
    assert before == (broker.connection._lease, broker.session._lease)
    assert broker._cancel_result is not None and broker.owner.latch.cancelled
