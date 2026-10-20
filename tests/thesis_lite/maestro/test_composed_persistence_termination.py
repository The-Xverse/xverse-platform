"""Selected CP07/08/12 actual worker/termination controls; full matrix open."""
from dataclasses import asdict
from importlib.resources import files
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.affa_protocol import AuthorityKind as K
from xverse.maestro.run_closure import RunClosure
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_terminal_runtime import scheduled, run, verify
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_composed_authority_interruptions import (
    Barrier, heartbeat_binary as heartbeat_binary, sentinel as sentinel,
    read_owned, observed_members, wait_for, retain,
)
from .test_run_broker import broker_stack as broker_stack
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as original_binaries, deadline


@pytest.fixture
def binaries(original_binaries, request, tmp_path):
    if 'termination' not in request.node.name:
        return original_binaries
    source = Path(__file__).with_name('catalog_workload_leader_descendant.c')
    binary = tmp_path/'owned-leader-descendant'
    command = ['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', str(source), '-o', str(binary)]
    result = subprocess.run(command, capture_output=True, check=True, timeout=20)
    retain('descendant-compiler-'+tmp_path.name+'.json', dict(command=command, returncode=result.returncode,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        original_fixture=str(tmp_path), compiler=subprocess.check_output(['cc', '--version'], text=True).splitlines()[0]))
    return dict(original_binaries, workload=binary)


@pytest.fixture
def run_bootstrap_binary(request, tmp_path):
    mode = request.node.callspec.params.get('mode', 'disabled')
    assert mode in ('disabled', 'before-intent-append', 'after-intent-flush')
    trace = tmp_path/'owned-intent-frontier.jsonl'
    code = '''import json,os,signal,time
from xverse.argus.writer import EvidenceRun
from xverse.maestro import persistence_worker
mode=MODE_LITERAL
fd=os.open(TRACE_LITERAL,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
append=EvidenceRun.append_event
flush=EvidenceRun.flush_buffer
pending=None
def log(action,payload):
    os.write(fd,(json.dumps(dict(action=action,observed_ns=time.monotonic_ns(),payload=payload))+'\\n').encode())
    os.fsync(fd)
def appended(self,*args,**kwargs):
    global pending
    payload=kwargs.get('extensions',{}).get('xverse.maestro',{})
    intent=(payload.get('scope')=='unit' and payload.get('action')=='intent'
        and kwargs.get('producer_id')=='maestro.owner7')
    if intent:
        log('before-intent-append',payload)
        if mode=='before-intent-append':os.kill(os.getpid(),signal.SIGSTOP)
    result=append(self,*args,**kwargs)
    if intent:
        log('intent-append-returned',payload)
        pending=payload
    return result
def flushed(self,*args,**kwargs):
    global pending
    result=flush(self,*args,**kwargs)
    if pending is not None:
        payload=pending;pending=None
        log('after-intent-flush',payload)
        if mode=='after-intent-flush':os.kill(os.getpid(),signal.SIGSTOP)
    return result
EvidenceRun.append_event=appended
EvidenceRun.flush_buffer=flushed
status=persistence_worker.main()
os.close(fd)
os._exit(status)
'''.replace('MODE_LITERAL', repr(mode)).replace('TRACE_LITERAL', repr(str(trace)))
    original = files('xverse.maestro').joinpath('native/bootstrap.c').read_text()
    anchor = 'args[2]="-m";args[3]="xverse.maestro.persistence_worker"'
    assert original.count(anchor) == 1
    source = original.replace(anchor, 'args[2]="-c";args[3]='+json.dumps(code))
    folder = tmp_path/'owned-intent-helper'
    folder.mkdir()
    path, binary = folder/'bootstrap.c', folder/'run-bootstrap'
    path.write_text(source)
    command = ['cc', '-DRUN_BOOTSTRAP', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
        '-Wconversion', '-Wshadow', str(path), '-lcrypto', '-o', str(binary)]
    result = subprocess.run(command, capture_output=True, check=True, timeout=30)
    retain('intent-helper-'+tmp_path.name+'.json', dict(mode=mode, command=command, returncode=result.returncode,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        original_native_source_sha256=hashlib.sha256(original.encode()).hexdigest(), fixed_role3_code=code,
        compiled_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        original_fixture=str(tmp_path), trace=str(trace), private_stream_access=False,
        production_fault_mode=False, admission_precedes_birth=True))
    return binary


def threaded_run(driver):
    results, failures = [], []
    def coordinate():
        try:
            results.append(run(driver))
        except BaseException as error:
            failures.append(repr(error))
    thread = threading.Thread(target=coordinate, name='original-run-coordinator')
    thread.start()
    return thread, results, failures


def finish(stack, driver, sentinel, before, thread, results, failures, case, observations):
    thread.join(timeout=18)
    assert not thread.is_alive(), 'original dispatcher not terminal'
    assert not failures and len(results) == 1, failures
    result = results[0]
    broker, _, client, work = stack
    closure = RunClosure(broker.session, dispatcher=driver).close(deadline(6))
    after = sentinel()
    facts = asdict(closure)
    facts['terminal_reports'] = [r.public_data() for r in closure.terminal_reports]
    checked = verify(client, work.parent/'argus')
    row = dict(case=case, observations=observations, original_fixture=str(work.parent),
        closure=facts, cleanup_complete=closure.cleanup_complete,
        execution_succeeded=result.execution_succeeded, diagnostic=result.diagnostic,
        terminal_recorded=result.terminal_recorded,
        terminal=result.terminal.public_data() if result.terminal else None,
        original_runtime_verification_complete=checked.complete,
        public_m3=list(FileEvidenceJournal(work.parent/'m3.jsonl').public_records()),
        argus_events=EvidenceStore.read_run(work.parent/'argus').records(),
        markers={p.name:p.read_text() for p in work.glob('*.marker')},
        sentinel_before=before, sentinel_after=after,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        full_crash_matrix_complete=False, full_M1_complete=False, accepted=False)
    retain('intent-termination-'+work.parent.name+'.json', row)
    assert closure.root_reaped and closure.authority_fenced
    assert all(h.process_reaped for h in closure.helpers)
    assert all(b.empty and b.released for b in closure.boundaries)
    assert not closure.lifecycle_complete
    return result, closure, row


@pytest.mark.parametrize('mode', ['disabled', 'before-intent-append', 'after-intent-flush'])
def test_original_intent_frontier_loader_and_loss(request, monkeypatch, sentinel, mode):
    before = sentinel()
    stack, _, driver = scheduled(request, monkeypatch)
    broker, _, client, work = stack
    trace = work.parent/'owned-intent-frontier.jsonl'
    exchanges = []
    exchange = broker.connection._exchange
    def observe(frame, **kw):
        exchanges.append(dict(kind=frame.kind.name, began=time.monotonic()))
        return exchange(frame, **kw)
    monkeypatch.setattr(broker.connection, '_exchange', observe)
    thread, results, failures = threaded_run(driver)
    observations = dict(mode=mode, exchanges=exchanges)
    if mode != 'disabled':
        fd = client.process._capability.fileno()
        end = min(time.monotonic()+2, client.coverage.data(client.coverage_digest)['end'])
        stopped = None
        while time.monotonic() < end:
            stopped = os.waitid(os.P_PIDFD, fd, os.WSTOPPED|os.WNOHANG|os.WNOWAIT)
            if stopped is not None:
                break
            time.sleep(.001)
        assert stopped is not None and stopped.si_code == os.CLD_STOPPED and stopped.si_status == signal.SIGSTOP
        observations['original_pidfd_stop'] = dict(code=stopped.si_code, status=stopped.si_status,
            observed=time.monotonic())
        signal.pidfd_send_signal(fd, signal.SIGKILL)
        observations['original_helper_killed'] = time.monotonic()
    result, closure, row = finish(stack, driver, sentinel, before, thread, results, failures,
        'intent-'+mode, observations)
    actual = [json.loads(line) for line in trace.read_text().splitlines()]
    retain('intent-frontier-trace-'+work.parent.name+'.json', dict(original_fixture=str(work.parent),
        trace=actual, trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest()))
    if mode == 'disabled':
        assert result.execution_succeeded and result.terminal_recorded, result.diagnostic
        assert row['original_runtime_verification_complete'] and closure.cleanup_complete
        assert len(actual) == 6
    else:
        assert not result.execution_succeeded and not row['original_runtime_verification_complete']
        assert not row['markers'] and closure.cleanup_complete
        assert all(f.issued is False for f in closure.native_units)
        assert not any(e['kind'] in ('STAGE', 'ARM', 'RELEASE') for e in exchanges)
        assert [e['action'] for e in actual] == (['before-intent-append'] if mode == 'before-intent-append'
            else ['before-intent-append', 'intent-append-returned', 'after-intent-flush'])
        assert all(e['payload'] == actual[0]['payload'] for e in actual)
        mirrors = [e for e in row['argus_events'] if e.get('extensions', {}).get('xverse.maestro', {}).get('action') == 'intent']
        assert len(mirrors) == int(mode == 'after-intent-flush')
        source = actual[0]['payload']['sourceRefs'][0]
        assert any(r['sequence'] == source['sequence'] for r in row['public_m3'])


@pytest.mark.parametrize('window', ['stop-before-send', 'stop-ack-pending', 'stop-after-reply'])
def test_original_termination_with_live_leader_descendant(request, monkeypatch, sentinel, window):
    before = sentinel()
    stack, _, driver = scheduled(request, monkeypatch)
    broker, _, client, work = stack
    barrier, local = Barrier(), threading.local()
    exchange, receive = broker.connection._exchange, broker.connection._receive
    exchanges = []
    def observed_exchange(frame, **kw):
        local.kind = frame.kind
        try:
            if frame.kind == K.STOP and window == 'stop-before-send':
                barrier.stop(window)
            reply = exchange(frame, **kw)
            exchanges.append(dict(kind=frame.kind.name, reply=reply.kind.name, state=reply.state,
                slot=reply.slot, returned=time.monotonic()))
            if frame.kind == K.STOP and window == 'stop-after-reply':
                barrier.stop(window)
            return reply
        finally:
            local.kind = None
    def observed_receive(until):
        if getattr(local, 'kind', None) == K.STOP and window == 'stop-ack-pending':
            barrier.stop(window)
        return receive(until)
    monkeypatch.setattr(broker.connection, '_exchange', observed_exchange)
    monkeypatch.setattr(broker.connection, '_receive', observed_receive)
    thread, results, failures = threaded_run(driver)
    observations = dict(window=window, exchanges=exchanges)
    try:
        assert barrier.reached.wait(4), failures
        sink = broker.issuer(driver.prepared.resource_order[-1])
        descriptor = sink._image.admission.descriptor
        fd = broker.session.boundaries._entries[descriptor.key].fd
        if window != 'stop-before-send':
            wait_for(lambda: not observed_members(fd))
        observations['sink_members_at_barrier'] = list(observed_members(fd))
        observations['markers_before_loss'] = {p.name:p.read_text() for p in work.glob('*.marker')}
        assert len(observations['markers_before_loss']) == 2
        assert all(v == 'EXEC\nDESCENDANT\n' for v in observations['markers_before_loss'].values())
        if window == 'stop-before-send':
            assert len(observations['sink_members_at_barrier']) == 2
        child = client.process if window == 'stop-after-reply' else broker.connection.child
        signal.pidfd_send_signal(child._capability.fileno(), signal.SIGKILL)
        observations['killed_role'] = 3 if window == 'stop-after-reply' else 4
        observations['killed_at'] = time.monotonic()
    finally:
        barrier.resume.set()
    result, closure, row = finish(stack, driver, sentinel, before, thread, results, failures,
        window, observations)
    assert not result.execution_succeeded and not row['original_runtime_verification_complete']
    assert row['markers'] == observations['markers_before_loss']
    if window == 'stop-after-reply':
        fact = next(f for f in closure.native_units if f.unit_id == sink.unit_id)
        assert fact.direct_child_reaped is True
    if not closure.cleanup_complete:
        assert 'ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN' in closure.diagnostics
