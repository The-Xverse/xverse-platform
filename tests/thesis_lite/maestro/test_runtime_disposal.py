"""Original late helper waits and local disposal retries never retarget reused FDs."""
from dataclasses import asdict
import errno
import hashlib
import json
import os
from pathlib import Path

import pytest
from xverse.maestro import persistence as persistence_module
from xverse.maestro.affa_client import AuthorityConnection
from xverse.maestro.dispatcher import FiniteDispatcher
from xverse.maestro.owner import OwnerError
from .test_runtime_entry import runtime as runtime
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline
from .test_affa_native import authority_binary as authority_binary
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary


@pytest.mark.parametrize('case', ['late-root-wait', 'broker-repeat', 'entry-retry', 'broker-close-error'])
def test_original_runtime_disposal_preserves_wait_facts_and_reused_descriptor(runtime,request,monkeypatch,case):
    entry,scope,work=runtime
    owner=entry._pins[1]
    real_close=os.close
    original_wait=persistence_module.wait_child
    real_dispose=AuthorityConnection.dispose
    state=dict(mask=case=='late-root-wait',guard=False,canary=None,
        closed_images=set(),targets=(),reject_once=case=='entry-retry',
        close_error_once=case=='broker-close-error')
    facts=dict(case=case,original_fixture=str(work.parent),full_M1_complete=False,
        actual_M1_admissions=0,full_runtime_case_complete=False,
        hidden_client_wait_observations=0,live_disposal_rejected=False,
        protected_close_attempts=0,disposal_errors=[],external_local_disposal=False,
        external_storage_drain_refresh=False,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())

    def observed_wait(process,fd,*,consume=False):
        storage=entry._runtime_pins[1]
        if storage is not None and process is storage._pins[0] and consume:
            if state['mask']:
                facts['hidden_client_wait_observations']+=1
                return None  # injected observation loss, never a positive kernel receipt
            result=original_wait(process,fd,consume=consume)
            facts['late_original_wait_observed']=result is not None and result is process._result
            return result
        return original_wait(process,fd,consume=consume)

    def closing(fd):
        if state['guard'] and fd==state['canary']:
            facts['protected_close_attempts']+=1
            raise OSError(errno.EPERM,'owned canary close denied before syscall')
        result=real_close(fd)
        if fd in state['targets']:
            state['closed_images'].add(fd)
            if state['close_error_once']:
                state['close_error_once']=False
                facts['injected_close_error_after_actual_close']=True
                raise OSError(errno.EINTR,'owned ambiguous close result after actual close')
        return result

    def authority_dispose(connection):
        if connection is entry._runtime_pins[2].connection and state['reject_once']:
            state['reject_once']=False
            facts['injected_client_disposal_rejection']=True
            raise OwnerError('ML-TEST-DISPOSE-REJECTED')
        return real_dispose(connection)

    original_run=FiniteDispatcher.run
    def running(driver,*a,**kw):
        storage=entry._runtime_pins[1]
        assert storage.process._result is None and storage._drained is None
        fd=storage._pidfd
        with pytest.raises(ValueError,match='RETAINED'):
            storage.dispose()
        assert storage._pidfd==fd and storage.channel.fileno()>=0
        facts['live_disposal_rejected']=True
        return original_run(driver,*a,**kw)

    def retain(value,end,root,manager,out):
        storage=value._runtime_pins[1]
        session=value._runtime_pins[0]
        broker=value._runtime_pins[2]
        try:
            assert session is not None and session._root_result is not None
            assert all(c._result is not None for c in session._children.values())
            assert all(e.state=='released' for e in manager._entries.values())
            facts.update(actual_original_root_wait=True,actual_original_helper_waits=True,
                all_original_C1_released=True,product_disposed=value._disposed)
            if not value._disposed:
                facts['external_local_disposal']=True
                state['mask']=False
                state['reject_once']=False
                if storage._drained is None or not storage._drained.worker_reaped:
                    # A distinct harness observation after the real root wait;
                    # preserve the held old receipt/result, never rewrite them.
                    facts['external_storage_drain_refresh']=True
                    assert storage.drain(deadline(1)).worker_reaped
                targets=tuple(fd for image in broker._pins[4]
                    for fd in (image.image_fd,image.cwd_fd,image.recipe_fd))
                if not set(targets)<=state['closed_images']:
                    broker.dispose()
                owner.dispose()
        finally:
            if out:
                with (Path(out)/('runtime-disposal-'+case+'.json')).open('x') as stream:
                    json.dump(facts,stream,indent=2)
                    stream.write('\n')

    request.node._runtime_failure_retainer=retain
    monkeypatch.setattr(persistence_module,'wait_child',observed_wait)
    monkeypatch.setattr(FiniteDispatcher,'run',running)
    result=entry.start(scope)
    storage,broker=entry._runtime_pins[1:3]
    assert result.closure is not None and result.closure.root_reaped
    assert all(h.process_reaped for h in result.closure.helpers)
    assert all(b.empty and b.released for b in result.closure.boundaries)
    assert storage.process is storage._pins[0] and storage.process._result is not None
    old_drain=storage._drained
    old_drain_data=asdict(old_drain) if old_drain is not None else None
    startup=asdict(result.startup)
    facts.update(primary_startup=startup,earlier_drain=old_drain_data,
        primary_diagnostics=list(result.diagnostics),primary_execution_succeeded=result.execution_succeeded,
        root_wait_before_disposal=True,registered_helper_wait_before_disposal=True)
    if case=='late-root-wait':
        assert facts['hidden_client_wait_observations'] and old_drain is not None
        assert not old_drain.worker_reaped
    state['mask']=False
    state['targets']=tuple(fd for image in broker._pins[4]
        for fd in (image.image_fd,image.cwd_fd,image.recipe_fd))
    monkeypatch.setattr(os,'close',closing)
    if case=='entry-retry':
        monkeypatch.setattr(AuthorityConnection,'dispose',authority_dispose)
    try:
        if case=='broker-repeat':
            broker.dispose()
        elif case=='entry-retry':
            with pytest.raises(OwnerError,match='ML-TEST-DISPOSE-REJECTED'):
                entry.dispose()
            assert not entry._disposed
        elif case=='broker-close-error':
            with pytest.raises(OwnerError,match='ML-RUN-DISPOSE-UNRESOLVED'):
                broker.dispose()
            assert state['closed_images']==set(state['targets'])
        if case!='late-root-wait':
            released=[]
            for fd in state['targets']:
                try:os.fstat(fd)
                except OSError as error:
                    assert error.errno==errno.EBADF
                    released.append(fd)
            path=work.parent/('owned-canary-'+case)
            canary=os.open(path,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
            if released and canary!=released[0]:
                os.dup2(canary,released[0])  # target was verified closed; no foreign FD is overwritten
                real_close(canary)
                canary=released[0]
            state['canary']=canary
            os.write(canary,b'KEEP\n')
            identity=os.fstat(canary)
            facts['reused_released_broker_fd']=canary in released
            state['guard']=True
        try:
            if case=='broker-close-error':
                with pytest.raises(OwnerError,match='ML-RUN-DISPOSE-UNRESOLVED'):
                    broker.dispose()
                with pytest.raises(OwnerError,match='ML-RUN-DISPOSE-UNRESOLVED'):
                    entry.dispose()
                assert not entry._disposed and not facts['protected_close_attempts']
                assert os.pread(state['canary'],5,0)==b'KEEP\n'
                assert storage._drained is old_drain and entry._result is result
                facts.update(close_uncertainty_retained=True,canary_untouched=True,
                    earlier_drain_unchanged=True,original_result_unchanged=True)
                return
            if case=='broker-repeat':broker.dispose()
            entry.dispose()
        except Exception as error:
            facts['disposal_errors'].append(type(error).__name__+': '+str(error))
        assert not facts['disposal_errors'],facts['disposal_errors']
        assert not facts['protected_close_attempts']
        assert entry._disposed
        assert storage._drained is old_drain
        assert (asdict(old_drain) if old_drain is not None else None)==old_drain_data
        assert asdict(result.startup)==startup and entry._result is result
        if case=='late-root-wait':assert facts['late_original_wait_observed']
        entry.dispose()
        storage.dispose()
        if state['canary'] is not None:
            current=os.fstat(state['canary'])
            assert (current.st_dev,current.st_ino)==(identity.st_dev,identity.st_ino)
            assert os.pread(state['canary'],5,0)==b'KEEP\n'
            facts['canary_untouched']=True
        facts.update(product_disposed=True,matching_disposal_retained=True,
            earlier_drain_unchanged=True,original_result_unchanged=True)
    finally:
        state['guard']=False
        if state['canary'] is not None:
            real_close(state['canary'])
            state['canary']=None
