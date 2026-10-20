"""Real disposable-controller birth/death and original-issuer reconciliation."""

import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.run_broker import RunBroker
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_generation_claim import ready, release
from .test_generation_dependents import advance
from .test_run_renewal import target
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def setup(request, monkeypatch, *, budget=2):
    original = RunBroker.admit
    monkeypatch.setattr(RunBroker, 'admit', classmethod(
        lambda cls, *a, **kw: original(*a, controller_sessions=budget, **kw)))
    stack, teardown, unit, _ = ready(request, monkeypatch)
    stack[0].renew(target(stack[0]), deadline(1))
    return stack, teardown, unit


def old_dead(old):
    signal.pidfd_send_signal(old.process._capability.fileno(), signal.SIGKILL)
    result = old.retire(deadline(0.8))
    assert result.original_child_dead and result.original_child_reaped and result.own_boundary_released
    assert not result.workload_waits_known and not result.ready_for_execution
    assert old.retire(deadline(0.5)) is result
    return result


def test_actual_role5_channel_inherits_no_productive_capabilities(request, monkeypatch):
    stack, _, unit = setup(request, monkeypatch)
    broker = stack[0]
    def forbidden(*a, **kw):
        pytest.fail('runtime controller Popen')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    controller = broker.admit_controller('controller-host-one', deadline(1))
    reply = controller.request(unit, 'observe', deadline(0.5))
    assert reply['host_session'] == controller.session_id != broker.owner.session
    assert controller.process._root is broker.session
    assert broker.session._issued[controller.process._slot][0] == 5
    forbidden = [broker.session.boundaries._root_fd, broker.connection.channel.fileno(),
        broker.storage.channel.fileno(), broker.connection.child._capability.fileno()]
    forbidden.extend(image.descriptor_fd for image in broker._pins[4])
    forbidden.extend(entry.fd for entry in broker.session.boundaries._entries.values() if entry.fd >= 0)
    identities = {(os.fstat(fd).st_dev, os.fstat(fd).st_ino) for fd in forbidden}
    child_fds = Path('/proc') / str(controller.process.pid) / 'fd'
    observed = {(p.stat().st_dev, p.stat().st_ino) for p in child_fds.iterdir()}
    assert not identities & observed
    controller._ordinary()


def test_actual_controller_death_preserves_original_storage_authority_and_workloads(request, monkeypatch):
    stack, _, _ = setup(request, monkeypatch)
    broker, facade, client, _ = stack
    handles = [(i, i._handle) for i in broker.issuers]
    authority = broker.connection.child
    old = broker.admit_controller('controller-host-one', deadline(1))
    old_dead(old)
    assert client.process is broker.storage.process and broker.connection.child is authority
    for issuer, handle in handles:
        assert broker.issuer(issuer.unit_id) is issuer and issuer._handle is handle
        assert facade.check_unit_health(issuer.unit_id, deadline(0.5)).ready
    assert not broker.owner.latch.cancelled
    with pytest.raises(ValueError):
        old.request(None, 'heartbeat', deadline(0.5))


def replace(stack, old):
    broker, facade, _, _ = stack
    old_dead(old)
    successor = broker.admit_controller('controller-host-two', deadline(1))
    assert successor.process is not old.process and successor.channel is not old.channel
    assert successor.descriptor != old.descriptor and successor.session_id != old.session_id
    with pytest.raises(ValueError, match='NOT-RECONCILED'):
        successor._start_access()
    recovered = successor.reconcile(tuple(facade._policies.values()), deadline(1.8), deadline(8))
    with pytest.raises(ValueError, match='STALE-VIEW'):
        facade.check_health(deadline(0.5), force=True)
    successor._start_access()
    assert successor.request(None, 'heartbeat', deadline(0.5))['host_session'] == successor.session_id
    assert recovered._observations and all(v.ready for v in recovered._observations.values())
    return successor, recovered


@pytest.mark.parametrize('fresh_generation', [False, True])
def test_actual_replacement_reconciles_original_handles_and_new_probes(request, monkeypatch, fresh_generation):
    stack, teardown, unit = setup(request, monkeypatch)
    broker, facade, client, work = stack
    if fresh_generation:
        release(teardown, unit)
        advance(stack, teardown, unit)
        broker.renew(target(broker), deadline(1))
    old = broker.admit_controller('controller-host-one', deadline(1))
    handles = {i.unit_id: i._handle for i in broker.issuers}
    worker = client.process
    prior_probe = {u: r.sample_sequence for u, r in client._probe_receipts.items()}
    before = [r for r in FileEvidenceJournal(work.parent / 'm3.jsonl').records if r.kind == 'intent' and r.action_id == 'start']
    successor, recovered = replace(stack, old)
    assert client.process is worker
    assert handles == {i.unit_id: i._handle for i in broker.issuers}
    after = [r for r in FileEvidenceJournal(work.parent / 'm3.jsonl').records if r.kind == 'intent' and r.action_id == 'start']
    assert after == before
    for u, sample in recovered._observations.items():
        assert sample.sequence > prior_probe[u]
        assert sample.generation == broker.issuer(u).recipe.descriptor.generation
    assert broker.issuer(unit).recipe.descriptor.generation == (2 if fresh_generation else 1)
    output = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        (Path(output) / ('controller-replacement-public-' + str(os.getpid()) + '-' + str(fresh_generation) + '.json')).write_text(json.dumps(dict(
            public_m3=FileEvidenceJournal(work.parent / 'm3.jsonl').public_records(),
            argus_events=EvidenceStore.read_run(work.parent / 'argus').records(),
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            original_controller_dead_reaped=True, original_storage_authority_handles_retained=True,
            old_session=old.session_id, new_session=successor.session_id,
            actual_resource_generation=broker.issuer(unit).recipe.descriptor.generation,
            fresh_native_probes=True, full_M1_complete=False)))


def test_controller_admission_rejects_live_old_duplicate_and_budget_without_effect(request, monkeypatch):
    stack, _, _ = setup(request, monkeypatch)
    broker = stack[0]
    old = broker.admit_controller('controller-host-one', deadline(1))
    count = len(broker.session._children)
    with pytest.raises(ValueError, match='OLD-LIVE'):
        broker.admit_controller('controller-host-two', deadline(0.5))
    with pytest.raises(ValueError, match='ADMISSION'):
        broker.admit_controller('controller-host-one', deadline(0.5))
    assert len(broker.session._children) == count and not broker.owner.latch.cancelled
    with pytest.raises(TypeError):
        copy.copy(old)
    old_dead(old)
    new = broker.admit_controller('controller-host-two', deadline(1))
    old_dead(new)
    with pytest.raises(ValueError, match='ADMISSION'):
        broker.admit_controller('controller-host-three', deadline(0.5))
    assert len(broker.session._children) == count + 1 and not broker.owner.latch.cancelled


def test_missing_durable_mirror_does_not_reconcile_controller(request, monkeypatch):
    stack, _, _ = setup(request, monkeypatch)
    broker, facade, _, work = stack
    old = broker.admit_controller('controller-host-one', deadline(1))
    old_dead(old)
    successor = broker.admit_controller('controller-host-two', deadline(1))
    reader = EvidenceStore.read_run(work.parent / 'argus')
    (work.parent / 'argus' / reader.manifest['eventStream']['path']).unlink()
    with pytest.raises(ValueError):
        successor.reconcile(tuple(facade._policies.values()), deadline(1.8), deadline(8))
    assert broker.owner.latch.cancelled


def test_stopped_controller_request_is_bounded_and_only_its_helper_is_retired(request, monkeypatch):
    stack, _, _ = setup(request, monkeypatch)
    broker, facade, _, _ = stack
    controller = broker.admit_controller('controller-host-one', deadline(1))
    signal.pidfd_send_signal(controller.process._capability.fileno(), signal.SIGSTOP)
    with pytest.raises(ValueError, match='TIMEOUT'):
        controller.request(None, 'heartbeat', deadline(0.15))
    result = controller.retire(deadline(0.8), terminate=True)
    assert result.original_child_dead and result.original_child_reaped and result.own_boundary_released
    for issuer in broker.issuers:
        assert facade.check_unit_health(issuer.unit_id, deadline(0.5)).ready
    assert not broker.owner.latch.cancelled


@pytest.mark.parametrize('budget', [0, 16])
def test_controller_capacity_is_explicit_and_checked_before_birth(request, monkeypatch, budget):
    if budget:
        original = RunBroker.admit
        monkeypatch.setattr(RunBroker, 'admit', classmethod(
            lambda cls, *a, **kw: original(*a, controller_sessions=budget, **kw)))
        with pytest.raises(ValueError, match='CONTROLLER-CAPACITY'):
            request.getfixturevalue('broker_stack')
    else:
        stack, _, _ = setup(request, monkeypatch, budget=0)
        broker = stack[0]
        before = len(broker.session._children), len(broker.session.boundaries._entries)
        with pytest.raises(ValueError, match='ADMISSION'):
            broker.admit_controller('controller-host-one', deadline(0.5))
        assert before == (len(broker.session._children), len(broker.session.boundaries._entries))
        assert not broker.owner.latch.cancelled


def test_controller_cannot_reuse_original_broker_host_session(request, monkeypatch):
    stack, _, _ = setup(request, monkeypatch)
    broker = stack[0]
    before = len(broker.session._children), len(broker.session.boundaries._entries)
    with pytest.raises(ValueError, match='HOST-SESSION'):
        broker.admit_controller(broker.owner.session, deadline(0.5))
    assert before == (len(broker.session._children), len(broker.session.boundaries._entries))
    assert not broker.owner.latch.cancelled


def test_controller_receiver_disposes_every_unexpected_right():
    import array
    import socket
    import time
    from xverse.argus.schema import canonical_bytes
    from xverse.maestro.controller import _receive
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    parent.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    descriptor = os.open('/dev/null', os.O_RDONLY)
    try:
        before = set(os.listdir('/proc/self/fd'))
        child.sendmsg([canonical_bytes(dict(version=1, kind='hello', sequence=0,
            scope='1'*64, session='owned-controller', body={}))],
            [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array('i', [descriptor]))])
        with pytest.raises(ValueError, match='PEER'):
            _receive(parent, (os.getpid(), os.getuid(), os.getgid()), time.monotonic_ns()+100_000_000, lambda: None)
        assert set(os.listdir('/proc/self/fd')) == before
    finally:
        os.close(descriptor)
        parent.close()
        child.close()
