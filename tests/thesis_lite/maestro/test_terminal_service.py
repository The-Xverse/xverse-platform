"""Actual BS17 terminal fencing and short cleanup leases; no full closure claim."""
import copy
import json
import os
from pathlib import Path
import select
import signal
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.bootstrap import BootstrapPacket
from xverse.maestro.time import HostDeadline
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def test_actual_terminal_service_preserves_original_writer_past_both_old_leases(broker_stack):
    broker, _, client, work = broker_stack
    root = broker.session; old_root, old_issuer = root._lease, broker.connection._lease
    original = client.process, root.process, root._generation, client.generation_ns
    assert broker.cancel('terminal-test', deadline=deadline(.5)).native_epoch_confirmed
    assert broker.service_terminal(deadline(.5)) == root._lease
    assert root._terminal and root.latch.cancelled
    # Kill/reap the original issuer after native root terminal ACK. This alone
    # grants no productive wait or cleanup credit.
    death = broker.connection.revoke(deadline(.7))
    assert death.issuer_dead and death.issuer_reaped and not death.workload_waits_known
    finish = max(old_root, old_issuer) / 1e9 + .15
    leases = [root._lease]
    while time.monotonic() < finish:
        select.select([], [], [], min(.65, finish - time.monotonic()))
        leases.append(broker.service_terminal(deadline(.5)))
        assert root.latch.cancelled
        assert not select.select([root._pidfd_capability.fileno()], [], [], 0)[0]
        assert not select.select([client._pidfd], [], [], 0)[0]
    assert (client.process, root.process, root._generation, client.generation_ns) == original
    assert all(a <= b for a, b in zip(leases, leases[1:]))
    assert root._lease <= root._generation - 2_000_000_000
    assert client.abort(deadline(.8)) == 'failed'  # Actual original-worker ACK after old ends.
    reader = EvidenceStore.read_run(work.parent / 'argus')
    assert reader.manifest['writerState'] == 'failed'
    out = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        (Path(out) / ('terminal-service-' + work.parent.name + '.json')).write_text(json.dumps(dict(
            old_bootstrap_lease_ns=old_root, old_authority_lease_ns=old_issuer,
            observed_after=time.monotonic(), original_generation_ns=root._generation,
            renewed_bootstrap_leases_ns=leases, issuer_dead=True, issuer_reaped=True,
            workload_waits_known=False, original_writer_abort_ack=True,
            cancelled_latch_retained=True, full_lifecycle_complete=False), indent=2) + '\n')


def test_terminal_service_rejects_before_original_cancellation_and_invalid_end(broker_stack):
    broker = broker_stack[0]; root = broker.session
    before = root._sequence, root._lease
    with pytest.raises(ValueError, match='TERMINAL-STATE'):
        broker.service_terminal(deadline(.5))
    assert before == (root._sequence, root._lease) and not root.latch.cancelled
    broker.cancel('terminal-test', deadline=deadline(.5))
    for invalid in (HostDeadline('foreign', time.monotonic() + .5), deadline(6)):
        with pytest.raises(ValueError):
            broker.service_terminal(invalid)
        assert before == (root._sequence, root._lease) and not root._terminal_attempted
    with pytest.raises(TypeError):
        copy.copy(broker)


@pytest.mark.parametrize('which', ['broker', 'root'])
def test_terminal_service_lock_conflict_has_no_bootstrap_effects(broker_stack, which):
    broker = broker_stack[0]; root = broker.session
    broker.cancel('terminal-test', deadline=deadline(.5))
    lock = broker._lock if which == 'broker' else root._lock
    before = root._sequence, root._lease
    lock.acquire()
    try:
        with pytest.raises(ValueError, match='CONFLICT'):
            broker.service_terminal(deadline(.5))
    finally:
        lock.release()
    assert before == (root._sequence, root._lease) and not root._terminal_attempted


def test_actual_terminal_root_rejects_valid_ordinary_native_renewal(broker_stack):
    broker = broker_stack[0]; root = broker.session
    broker.cancel('terminal-test', deadline=deadline(.5)); broker.service_terminal(deadline(.5))
    before = root._sequence
    with pytest.raises(ValueError, match='CLOSED'):
        root.renew(deadline(4.95), deadline(.5))
    assert root._sequence == before
    # Bypass only the Python sender to exercise actual native rejection. This is
    # a valid ordinary renewal shape/end, with no leaked or recovered descriptor.
    end = deadline(.5)
    frame = BootstrapPacket(3, root._sequence + 1, int(end.monotonic_seconds * 1e9), root.config.scope,
                            state=int((time.monotonic() + 4.95) * 1e9), version=2)
    assert root.channel.send(frame.encode()) == 128
    assert select.select([root._pidfd_capability.fileno()], [], [], 2)[0]
    assert select.select([broker.storage._pidfd], [], [], 1)[0]


@pytest.mark.parametrize('failure', ['lease-expiry', 'storage-death'])
def test_actual_terminal_root_keeps_original_failure_watchdogs(broker_stack, failure):
    broker = broker_stack[0]; root = broker.session
    broker.cancel('terminal-test', deadline=deadline(.5)); broker.service_terminal(deadline(.5))
    if failure == 'storage-death':
        signal.pidfd_send_signal(broker.storage.process._capability.fileno(), signal.SIGKILL)
        limit = 2
    else:
        limit = max(0, root._lease / 1e9 - time.monotonic()) + 2
    assert select.select([root._pidfd_capability.fileno()], [], [], limit)[0]
    assert select.select([broker.storage._pidfd], [], [], 1)[0]


@pytest.mark.parametrize('kind', [5, 6, 21, 22])
def test_terminal_packets_remain_invalid_in_legacy_bs10(kind):
    with pytest.raises(ValueError):
        BootstrapPacket(kind, 1, 1, bytes(32), version=1)


def test_synthetic_local_cancel_flags_cannot_grant_terminal_service(broker_stack):
    from xverse.maestro.run_broker import RunCancellation
    broker = broker_stack[0]; root = broker.session
    assert not broker.connection._epoch_history[-1].kind.name == 'CANCELLED'
    root.latch.cancel('synthetic-test-flag'); broker.owner._closed = True
    broker._cancel_result = RunCancellation(True, 1, 0, False, False, None)
    before = root._sequence
    try:
        with pytest.raises(ValueError, match='TERMINAL-FENCE'):
            broker.service_terminal(deadline(.5))
        assert root._sequence == before and not root._terminal_attempted
        with pytest.raises(ValueError, match='TERMINAL-FENCE'):
            root._service_terminal(deadline(.5), authority=broker.connection)
        with pytest.raises(ValueError, match='TERMINAL-STATE'):
            root._service_terminal(deadline(.5), authority=object())
        assert root._sequence == before and not root._terminal_attempted
    finally:
        broker._cancel_result = None  # Restore actual cancellation for owned fixture cleanup.


@pytest.mark.parametrize('failure', ['lost', 'changed'])
def test_actual_terminal_ack_uncertainty_closes_original_root_without_replay(broker_stack, monkeypatch, failure):
    from dataclasses import replace
    broker = broker_stack[0]; root = broker.session
    broker.cancel('terminal-test', deadline=deadline(.5))
    receive = root._receive
    def observed(until, *, cleanup=False, terminal=False):
        reply, fds = receive(until, cleanup=cleanup, terminal=terminal)
        if reply.kind == 21:
            assert not fds
            if failure == 'lost':
                raise ValueError('ML-TEST-LOST-TERMINAL-ACK')
            reply = replace(reply, state=reply.state + 1)
        return reply, fds
    monkeypatch.setattr(root, '_receive', observed)
    with pytest.raises(ValueError):
        broker.service_terminal(deadline(.5))
    assert root._terminal_attempted and not root._terminal and root._closed and root.latch.cancelled
    sequence = root._sequence
    with pytest.raises(ValueError):
        broker.service_terminal(deadline(.5))
    assert root._sequence == sequence
