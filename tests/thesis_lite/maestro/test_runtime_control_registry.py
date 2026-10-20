"""Original private run/control registry; separate owned bootstrap scope only."""
from dataclasses import asdict, replace
import copy
import json
import os
from pathlib import Path
import subprocess
import threading

import pytest
from xverse.maestro.dispatcher import FiniteDispatcher
from xverse.maestro.runtime_entry import _OriginalRuntimeRun, _OriginalRuntimeRegistry
from .test_runtime_entry import runtime as runtime
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries
from .test_affa_native import authority_binary as authority_binary
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_terminal_runtime import verify
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations


def retain(entry,work,case,**facts):
    out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        (Path(out)/('runtime-registry-'+work.parent.name+'.json')).write_text(json.dumps(dict(
            case=case,original_fixture=str(work.parent),full_M1_complete=False,**facts),indent=2)+'\n')


@pytest.mark.parametrize('capacity',[0,129,True,None])
def test_registry_capacity_is_explicit(capacity):
    with pytest.raises(ValueError,match='CAPACITY'):_OriginalRuntimeRegistry(capacity)


def test_original_registry_rejects_reconstruction_loss_and_cross_registration(runtime,monkeypatch):
    entry,scope,_=runtime;registry=_OriginalRuntimeRegistry(1)
    assert registry.reserve(entry) is entry
    with pytest.raises(TypeError):copy.copy(registry)
    with monkeypatch.context() as patch:
        patch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('reservation/control rejection created process'))
        assert registry.reserve(entry) is entry
        other=_OriginalRuntimeRun(*entry._pins[:3])
        with pytest.raises(ValueError,match='REGISTRY-REPEAT'):registry.reserve(other)
        with pytest.raises(ValueError,match='REGISTRY-ORIGINAL'):_OriginalRuntimeRegistry(1).reserve(entry)
        with pytest.raises(ValueError,match='UNKNOWN'):registry.start('foreign',scope)
        for operation in (lambda:registry.restart('fixture-run','unit',permit=None,generation=2,deadline=scope.active),
            lambda:registry.restart_many('fixture-run',(),deadline=scope.active),
            lambda:registry.replace_controller('fixture-run',session_id='successor',deadline=scope.active)):
            with pytest.raises(ValueError,match='NOT-ACTIVE'):operation()
        log=registry._cleanup_log;registry._cleanup_log=()
        try:
            with pytest.raises(ValueError,match='CLEANUP-LOST'):registry.stop('fixture-run')
            with pytest.raises(ValueError,match='CLEANUP-LOST'):registry.reserve(entry)
        finally:registry._cleanup_log=log
    assert not entry._launcher._birth_attempted and not entry._launcher.boundaries._latch.cancelled


def test_original_registry_whole_run_replay_and_retained_collection(runtime,monkeypatch):
    entry,scope,work=runtime;registry=_OriginalRuntimeRegistry(1);registry.reserve(entry)
    result=registry.start('fixture-run',scope)
    assert result.execution_succeeded and result.cleanup_complete
    assert verify(entry._storage,work.parent/'argus').complete
    with monkeypatch.context() as patch:
        patch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('registry replay created process'))
        assert registry.start('fixture-run',scope) is result
        assert registry.collect('fixture-run') is result.dispatch.collection
        assert registry.reserve(entry) is entry
        with pytest.raises(ValueError,match='REPEAT'):registry.start('fixture-run',replace(scope,startup=scope.active))
        with pytest.raises(ValueError,match='UNKNOWN'):_OriginalRuntimeRegistry(1).collect('fixture-run')
    retain(entry,work,'closed',original_run_retained=True,no_second_start=True)


def test_actual_original_registry_loss_stop_uses_only_retained_cleanup(runtime,monkeypatch):
    entry,scope,work=runtime;registry=_OriginalRuntimeRegistry(1);registry.reserve(entry)
    reached=threading.Event();resume=threading.Event();results=[];errors=[];held=[]
    statement=FiniteDispatcher._statement
    def observed(self,kind,step,**kw):
        result=statement(self,kind,step,**kw)
        if kind=='step-complete' and step.phase=='start' and not held:
            held.append(True);reached.set();assert resume.wait(1.5)
        return result
    monkeypatch.setattr(FiniteDispatcher,'_statement',observed)
    def start():
        try:results.append(registry.start('fixture-run',scope))
        except BaseException as error:errors.append(repr(error))
    thread=threading.Thread(target=start);thread.start();original_map=registry._entries
    try:
        assert reached.wait(2)
        registry._entries={}
        with pytest.raises(ValueError,match='REGISTRY-REPLACED'):registry.collect('fixture-run')
        with pytest.raises(ValueError,match='REGISTRY-REPLACED'):entry.collect('fixture-run')
        assert registry.stop('fixture-run',reason='owned-registry-loss')==1
        with monkeypatch.context() as patch:
            patch.setattr(entry._driver,'cancel',lambda *a,**kw:pytest.fail('matching registry stop repeated cancellation'))
            assert registry.stop('fixture-run',reason='owned-registry-loss')==1
    finally:
        resume.set();thread.join(6)
        # Restore only the same original ordinary map after factual cleanup.
        if results:
            assert results[0].closure.root_reaped and all(b.empty and b.released for b in results[0].closure.boundaries)
        registry._entries=original_map
    assert not thread.is_alive() and not errors and len(results)==1,errors
    result=results[0]
    assert not result.execution_succeeded and not result.closure.normal_unit_records_complete
    assert result.closure.root_reaped and all(h.process_reaped for h in result.closure.helpers)
    assert not (work/'sink-binding.marker').exists()
    retain(entry,work,'registry-loss-stop',ordinary_rejected=True,original_cleanup_log_used=True,
        original_map_restored_after_actual_cleanup=True)


@pytest.mark.parametrize('runtime',['recovery'],indirect=True)
def test_actual_registry_controller_recovery_preserves_productive_original_run(runtime,monkeypatch):
    entry,scope,work=runtime;registry=_OriginalRuntimeRegistry(1);registry.reserve(entry);tickets=[]
    original=FiniteDispatcher._statement;old=[]
    def observed(self,kind,step,**kw):
        reply=original(self,kind,step,**kw)
        if kind=='step-complete' and step.phase=='prepare' and not tickets:
            old.append(self._controller)
            ticket=registry.replace_controller('fixture-run',session_id='registry-successor',deadline=scope.active)
            tickets.append(ticket)
            assert registry.replace_controller('fixture-run',session_id=ticket.session_id,deadline=scope.active) is ticket
            assert registry.controller_recovery_result('fixture-run',ticket) is None
            with pytest.raises(ValueError,match='RECOVERY-ORIGINAL'):
                registry.controller_recovery_result('fixture-run',replace(ticket))
        return reply
    monkeypatch.setattr(FiniteDispatcher,'_statement',observed)
    result=registry.start('fixture-run',scope)
    assert len(tickets)==1 and result.execution_succeeded and result.cleanup_complete,result
    outcome=registry.controller_recovery_result('fixture-run',tickets[0])
    assert outcome.disposition=='completed' and outcome.ordinary_reconciled
    assert entry._driver._controller is not old[0] and entry._driver._controller.session_id==tickets[0].session_id
    assert len(entry._broker._controllers)==2 and old[0].process._result is not None
    assert all((work/(u.binding_id+'.marker')).read_bytes()==b'EXEC\n' for u in entry._persistence.prepared.units)
    assert sum(h.role==5 for h in result.closure.helpers)==2
    assert verify(entry._storage,work.parent/'argus').complete
    assert registry.collect('fixture-run') is result.dispatch.collection
    retain(entry,work,'productive-recovery',recovery=asdict(outcome),original_worker_retained=True,
        original_authority_retained=True,controller_helpers=2,active_seconds=entry._persistence.schedule.active_seconds,
        recovery_seconds=entry._persistence.schedule.recovery_operation_seconds)
