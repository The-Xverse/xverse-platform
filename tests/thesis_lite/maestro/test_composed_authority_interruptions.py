"""Selected original v6 race/crash windows, not the complete M1 crash matrix."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import threading
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.affa_protocol import AuthorityKind as K
from xverse.maestro.persistence import PersistenceClient
from xverse.maestro.prbc import BoundaryDescriptor
from xverse.maestro.run_closure import RunClosure
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_terminal_runtime import scheduled, run
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment, _write
from .test_launcher import binaries as binaries, deadline


def retain(name, data):
    target = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if target:
        path = Path(target) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x') as stream:
            json.dump(data, stream, indent=2)
            stream.write('\n')


def read_owned(directory, name):
    """Observation through retained fd, not certified frozen-membership evidence."""
    fd = os.open(name, os.O_RDONLY, dir_fd=directory)
    try:
        return os.read(fd, 4096)
    finally:
        os.close(fd)


def observed_members(directory):
    return tuple(sorted(map(int, read_owned(directory, 'cgroup.procs').split())))


@pytest.fixture(scope='module')
def heartbeat_binary(tmp_path_factory):
    source = Path(__file__).with_name('unrelated_heartbeat_fixture.c')
    binary = tmp_path_factory.mktemp('unrelated-heartbeat') / 'heartbeat'
    command = ['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', str(source), '-o', str(binary)]
    result = subprocess.run(command, capture_output=True, check=True, timeout=20)
    retain('heartbeat-compiler.json', dict(command=command, returncode=result.returncode,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        compiler=subprocess.check_output(['cc', '--version'], text=True).splitlines()[0],
        role='owned isolation harness only; not an admitted runtime provider'))
    return binary


@pytest.fixture
def sentinel(environment, heartbeat_binary):
    factory, spawn, _ = environment
    manager, latch = factory(seconds=45, run_id='unrelated-run')
    descriptor = BoundaryDescriptor('unrelated-run', 'sentinel', 1, 'unrelated-heartbeat', 0)
    manager.create_frozen(descriptor)
    worker, pipe, line = spawn(heartbeat_binary, manager, descriptor)
    assert line.startswith('CHILD '), line
    members = manager.residual_membership(descriptor)
    assert members == (int(line.split()[1]),)
    entry = manager._entries[descriptor.key]
    identity = os.fstat(entry.fd)
    # Explicit test-only stimulation, never a runtime Release or M3 operation.
    _write(entry.fd, 'cgroup.freeze', b'0')
    assert select.select([pipe], [], [], .5)[0]
    assert os.read(pipe, 4096).strip(b'S') == b''

    def observe():
        assert not latch.cancelled and worker.poll() is None
        assert observed_members(entry.fd) == members
        current = os.fstat(entry.fd)
        assert (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino)
        assert read_owned(entry.fd, 'cgroup.freeze').strip() == b'0'
        while select.select([pipe], [], [], 0)[0]:
            assert os.read(pipe, 4096).strip(b'S') == b''
        began = time.monotonic()
        assert select.select([pipe], [], [], .3)[0], 'no fresh unrelated heartbeat'
        data = os.read(pipe, 4096)
        assert data and data.strip(b'S') == b''
        return dict(boundary_identity=[identity.st_dev, identity.st_ino], members=list(members),
            fresh_heartbeat_began=began, fresh_heartbeat_observed=time.monotonic(),
            parent_alive=True, unfrozen=True, cancellation_latch=False,
            membership_observation_only=True)

    try:
        yield observe
    finally:
        result = manager.force_cleanup(descriptor)
        assert result.boundary_released and result.termination_observed
        assert worker.wait(timeout=2) == 0


class Barrier:
    """Instrumentation only: never changes a frame, handle, pin or deadline."""
    def __init__(self):
        self.reached = threading.Event()
        self.resume = threading.Event()
        self.once = False
        self.observations = []
        self.exchanges = []

    def stop(self, label):
        if self.once:
            return
        self.once = True
        self.observations.append(dict(label=label, reached=time.monotonic()))
        self.reached.set()
        assert self.resume.wait(2), 'original authority barrier expired'
        self.observations[-1]['resumed'] = time.monotonic()


def instrument(monkeypatch, stack, window, barrier):
    broker, _, client, _ = stack
    connection = broker.connection
    exchange, receive = connection._exchange, connection._receive
    local = threading.local()
    kind = K.STAGE if window.startswith('stage-') else K.RELEASE

    def wrapped_exchange(request, **kw):
        local.kind = request.kind
        try:
            if request.kind == kind and window.endswith('before-send'):
                barrier.stop(window)
            reply = exchange(request, **kw)
            barrier.exchanges.append(dict(request=request.kind.name, reply=reply.kind.name,
                sequence=reply.sequence, state=reply.state, returned=time.monotonic()))
            if request.kind == kind and window.endswith('after-reply'):
                barrier.stop(window)
            return reply
        finally:
            local.kind = None

    def wrapped_receive(until):
        if getattr(local, 'kind', None) == kind and window.endswith('ack-pending'):
            barrier.stop(window)
        return receive(until)

    monkeypatch.setattr(connection, '_exchange', wrapped_exchange)
    monkeypatch.setattr(connection, '_receive', wrapped_receive)
    if window.startswith('issuance-'):
        record = PersistenceClient.record_issued

        def issued(self, issuer, statement, end):
            if self is client and window == 'issuance-before-record':
                barrier.stop(window)
            result = record(self, issuer, statement, end)
            if self is client and window == 'issuance-after-record':
                barrier.stop(window)
            return result

        monkeypatch.setattr(PersistenceClient, 'record_issued', issued)


def wait_for(predicate):
    end = time.monotonic() + .25
    while not predicate() and time.monotonic() < end:
        time.sleep(.001)
    assert predicate(), 'original native window was not observed'


def execute(request, monkeypatch, sentinel, window, fault):
    before_sentinel = sentinel()
    stack, _, driver = scheduled(request, monkeypatch)
    broker, facade, client, work = stack
    unit = driver.prepared.resource_order[0]
    issuer = broker.issuer(unit)
    barrier = Barrier()
    instrument(monkeypatch, stack, window, barrier)
    results, failures = [], []

    def coordinate():
        try:
            results.append(run(driver))
        except BaseException as error:
            failures.append(repr(error))

    coordinator = threading.Thread(target=coordinate, name='original-run-coordinator')
    coordinator.start()
    observations = {}
    try:
        assert barrier.reached.wait(3), failures
        descriptor = issuer._image.admission.descriptor
        manager = broker.session.boundaries
        if window == 'stage-ack-pending':
            fd = manager._entries[descriptor.key].fd
            wait_for(lambda: len(observed_members(fd)) == 1)
            assert read_owned(fd, 'cgroup.freeze').strip() == b'1'
        if window.startswith('release-') and window != 'release-before-send':
            wait_for(lambda: len(list(work.glob('*.marker'))) == 1)
        observations.update(at_barrier=time.monotonic(),
            members=list(observed_members(manager._entries[descriptor.key].fd)),
            marker_names=sorted(p.name for p in work.glob('*.marker')),
            issued_receipts=len(client._issued_receipts), host_handle_retained=issuer._handle is not None)
        if fault == 'cancel':
            driver.cancel('owned-composed-cancel')
            observations['cancellation'] = asdict(broker.cancel('owned-composed-cancel'))
        else:
            child = broker.connection.child if fault == 'authority' else client.process
            signal.pidfd_send_signal(child._capability.fileno(), signal.SIGKILL)
            observations['killed_original_role'] = 4 if fault == 'authority' else 3
        observations['effect_completed'] = time.monotonic()
    finally:
        barrier.resume.set()
        coordinator.join(timeout=18)
    assert not coordinator.is_alive(), 'original dispatcher has not reached terminal state'
    assert not failures and len(results) == 1, failures
    result = results[0]
    closure = RunClosure(broker.session, dispatcher=driver).close(deadline(6))
    after_sentinel = sentinel()
    events = EvidenceStore.read_run(work.parent / 'argus').records()
    m3 = FileEvidenceJournal(work.parent / 'm3.jsonl').public_records()
    markers = {p.name: p.read_text() for p in work.glob('*.marker')}
    facts = asdict(closure)
    facts['terminal_reports'] = [r.public_data() for r in closure.terminal_reports]
    retain('composed-authority-' + work.parent.name + '.json', dict(window=window, fault=fault,
        original_fixture=str(work.parent), barrier=barrier.observations,
        original_exchange_returns=barrier.exchanges, observations=observations,
        host_handle_after_run=issuer._handle is not None,
        execution_succeeded=result.execution_succeeded, diagnostic=result.diagnostic,
        terminal_recorded=result.terminal_recorded,
        terminal=result.terminal.public_data() if result.terminal else None,
        closure=facts, cleanup_complete=closure.cleanup_complete, public_m3=m3,
        argus_events=events, markers=markers, sentinel_before=before_sentinel, sentinel_after=after_sentinel,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        full_runtime_case_complete=False, full_M1_complete=False, accepted=False))
    assert not result.execution_succeeded and not closure.lifecycle_complete
    assert closure.authority_fenced and closure.root_reaped
    assert all(h.process_reaped for h in closure.helpers)
    assert all(b.empty and b.released for b in closure.boundaries)
    assert broker.owner.latch.cancelled
    assert not any(e.get('extensions', {}).get('xverse.maestro', {}).get('action') == 'started' for e in events)
    released = window.startswith('release-') and window != 'release-before-send'
    assert len(markers) == int(released), markers
    assert all(value == 'EXEC\n' for value in markers.values()), markers
    assert not facade._bindings or set(facade._bindings) <= {unit}
    # A real issued fact is allowed to survive. It cannot authorize a late start.
    sequence = broker.connection.sequence
    with pytest.raises(ValueError):
        issuer.stage(deadline(.3))
    assert broker.connection.sequence == sequence
    assert {p.name: p.read_text() for p in work.glob('*.marker')} == markers
    if window == 'stage-ack-pending':
        first = next(f for f in closure.native_units if f.unit_id == unit)
        stage_ack = any(e['reply'] == 'STAGED' for e in barrier.exchanges)
        assert first.issued is (True if stage_ack else None)
        assert first.direct_child_reaped is None
        assert not closure.cleanup_complete
        assert 'ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN' in closure.diagnostics
    if window == 'issuance-after-record':
        assert observations['issued_receipts'] == 1
    if window == 'issuance-before-record':
        assert observations['issued_receipts'] == 0


@pytest.mark.parametrize('window', ['stage-before-send', 'stage-ack-pending',
    'release-before-send', 'release-ack-pending', 'release-after-reply'])
def test_atomic_release_cancel_stage(request, monkeypatch, sentinel, window):
    execute(request, monkeypatch, sentinel, window, 'cancel')


@pytest.mark.parametrize('window,fault', [('stage-before-send', 'authority'),
    ('stage-ack-pending', 'authority'), ('issuance-before-record', 'storage'),
    ('issuance-after-record', 'storage')])
def test_pre_handle_crash_survival(request, monkeypatch, sentinel, window, fault):
    execute(request, monkeypatch, sentinel, window, fault)
