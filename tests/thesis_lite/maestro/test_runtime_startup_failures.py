"""Actual owned helper-registration loss; primary/fallback facts stay separate."""
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import subprocess

import pytest
from xverse.maestro.bootstrap import BootstrapSession
from xverse.maestro.dispatcher import FiniteDispatcher
from xverse.maestro.owner import OwnerError
from xverse.maestro.run_broker import RunBroker
from xverse.maestro.run_closure import RunClosure
from xverse.maestro.runtime_entry import _OriginalRuntimeRun
from .test_runtime_entry import runtime as runtime
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries
from .test_affa_native import authority_binary as authority_binary
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary


def closure_data(value):
    if value is None:return None
    result=asdict(value);result['cleanup_complete']=value.cleanup_complete
    result['terminal_reports']=[r.public_data() for r in value.terminal_reports]
    return result


@pytest.mark.parametrize('fault',['zero-controllers','too-many-controllers','bool-controllers','unit-order','unit-epoch','session','unit-run','unit-generation'])
def test_constructor_conflicts_reject_before_process_or_C1(runtime,monkeypatch,fault):
    entry,_,_=runtime;config,launcher,units=entry._pins[:3];kw={}
    if fault=='zero-controllers':kw['controller_sessions']=0
    elif fault=='too-many-controllers':kw['controller_sessions']=17
    elif fault=='bool-controllers':kw['controller_sessions']=True
    elif fault=='unit-order':units=tuple(reversed(units))
    elif fault=='unit-epoch':units=(replace(units[0],descriptor=replace(units[0].descriptor,creation_epoch=1)),*units[1:])
    elif fault=='session':config=replace(config,session='foreign')
    elif fault=='unit-run':units=(replace(units[0],descriptor=replace(units[0].descriptor,run_id='foreign')),*units[1:])
    else:units=(replace(units[0],descriptor=replace(units[0].descriptor,generation=0)),*units[1:])
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('constructor created process'))
    with pytest.raises(ValueError,match='ML-RUNTIME-ENTRY'):_OriginalRuntimeRun(config,launcher,units,**kw)
    assert not launcher._birth_attempted and not launcher.boundaries._entries
    assert not launcher.boundaries._latch.cancelled


@pytest.mark.parametrize('fault',['after-storage','after-authority','after-controller','session-alias','broker-alias','launcher-alias'])
def test_original_startup_failure_returns_primary_cleanup_without_fallback(runtime,request,monkeypatch,fault):
    entry,scope,work=runtime;launcher=entry._pins[1];retained={};observations={}
    def retain(value,end,root,manager,out):
        # Capture primary before any external cleanup, including an exception
        # that prevented creation of a RuntimeResult. Never rewrite that result.
        primary=value._result
        observations['primary']=None if primary is None else dict(
            startup=asdict(primary.startup),closure=closure_data(primary.closure),diagnostics=primary.diagnostics,
            dispatch_returned=primary.dispatch is not None)
        session=launcher._session
        broker=retained.get('broker',value._runtime_pins[2]);driver=value._runtime_pins[3]
        fallback=None
        if session is not None and (not session._drained or not session._drained.supervisor_reaped
            or not session._drained.registered_children_reaped or any(e.state!='released' for e in manager._entries.values())):
            fallback=RunClosure(session,dispatcher=driver,broker=broker).close(end.closure,reason='external-owned-startup-fallback')
        observations['fallback']=closure_data(fallback)
        assert session is not None and session._root_result is not None
        assert all(c._result is not None for c in session._children.values())
        assert all(e.state=='released' for e in manager._entries.values())
        assert not list(root.glob('*.marker'))
        observations['actual_original_root_wait']=True
        observations['actual_registered_helpers']=len(session._children)
        observations['all_original_C1_released']=True
        observations['ordinary_alias_restoration_after_cleanup']=True
        value._session,value._storage,value._broker,value._driver=value._runtime_pins
        value._launcher=launcher
        if broker is not None:broker.dispose()
        assert launcher._process.stderr.read()==b''
        launcher.dispose()
        if out:
            (Path(out)/('runtime-startup-fault-'+root.parent.name+'.json')).write_text(json.dumps(dict(
                case=fault,observations=observations,original_fixture=str(root.parent),
                full_M1_complete=False,source_sha256=__import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
    request.node._runtime_failure_retainer=retain
    persistence=BootstrapSession.persistence;admit=RunBroker.admit;controller=RunBroker.admit_controller
    def storage(self,*a,**kw):
        result=persistence(self,*a,**kw)
        if fault=='after-storage':raise OwnerError('ML-TEST-AFTER-STORAGE')
        return result
    def authority(cls,*a,**kw):
        result=admit(*a,**kw);retained['broker']=result
        if fault=='after-authority':raise OwnerError('ML-TEST-AFTER-AUTHORITY')
        return result
    def control(self,*a,**kw):
        result=controller(self,*a,**kw)
        if fault=='after-controller':raise OwnerError('ML-TEST-AFTER-CONTROLLER')
        return result
    def dispatch(self,*a,**kw):
        assert fault.endswith('-alias')
        setattr(entry,{'session-alias':'_session','broker-alias':'_broker','launcher-alias':'_launcher'}[fault],object())
        raise OwnerError('ML-TEST-ORDINARY-ALIAS-LOST')
    monkeypatch.setattr(BootstrapSession,'persistence',storage)
    monkeypatch.setattr(RunBroker,'admit',classmethod(authority))
    monkeypatch.setattr(RunBroker,'admit_controller',control)
    if fault.endswith('-alias'):monkeypatch.setattr(FiniteDispatcher,'run',dispatch)
    result=None;errors=[]
    try:result=entry.start(scope)
    except Exception as error:errors.append(type(error).__name__+': '+str(error))
    observations['primary_exceptions']=errors
    assert not errors,errors
    assert result is not None and result.closure is not None,result
    assert result.closure.root_reaped and all(h.process_reaped for h in result.closure.helpers)
    assert all(b.empty and b.released for b in result.closure.boundaries)
    assert result.dispatch is None and result.execution_succeeded is None
    assert result.diagnostics and not result.ready_for_execution and not result.lifecycle_complete
    assert not list(work.glob('*.marker'))
    if fault.endswith('-alias'):
        with pytest.raises(ValueError,match='ENTRY-REPLACED'):entry.collect('fixture-run')
