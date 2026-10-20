"""Whole-run stop is independent of pending startup and ordinary registry views."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import pytest
from xverse.maestro.runtime_entry import _OriginalRuntimeRegistry
from .test_runtime_entry import runtime as runtime
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries
from .test_affa_native import authority_binary as authority_binary
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary


@pytest.mark.parametrize('route',['direct','registry','registry-view-loss'])
def test_pending_original_process_return_stop_routes_use_only_original_cleanup(runtime,request,monkeypatch,route):
    entry,scope,work=runtime;owner=entry._pins[1];registry=_OriginalRuntimeRegistry(1)
    if route!='direct':registry.reserve(entry)
    original_map=registry._entries;popen=subprocess.Popen;created=[];reached=threading.Event();release=threading.Event()
    results=[];errors=[];facts={};normal_lock_held=False
    class HeldPopen(popen):
        def __init__(self,*a,**kw):
            super().__init__(*a,**kw);created.append(self);reached.set()
            assert release.wait(3), 'test did not release original Popen return'
    def retain(value,end,root,manager,out):
        assert facts.get('primary_original_root_wait') and not manager._entries
        assert not list(root.glob('*.marker'))
        assert value._result is results[0] and value._result.closure is None
        if not value._disposed:value.dispose()
        if out:(Path(out)/('pending-stop-'+route+'.json')).write_text(json.dumps(facts,indent=2)+'\n')
    request.node._runtime_failure_retainer=retain
    monkeypatch.setattr(subprocess,'Popen',HeldPopen)
    def start():
        try:results.append(entry.start(scope) if route=='direct' else registry.start('fixture-run',scope))
        except Exception as error:errors.append(str(error) if str(error).startswith('ML-') else type(error).__name__)
    thread=threading.Thread(target=start);thread.start()
    try:
        assert reached.wait(2) and len(created)==1
        assert entry._lock.locked() and owner._lock.locked() and not owner.outcome.process_returned
        assert owner._capability_pin is None and not owner.boundaries._latch.cancelled
        stop=entry.stop if route=='direct' else registry.stop
        with pytest.raises(ValueError):stop('foreign',reason='owned-pending-stop')
        assert not owner.boundaries._latch.cancelled
        if route!='direct':
            assert registry._lock.acquire(False);normal_lock_held=True
        if route=='registry-view-loss':
            registry._entries={}
            with pytest.raises(ValueError,match='REGISTRY-REPLACED'):registry.collect('fixture-run')
        begin=time.monotonic_ns();epoch=stop('fixture-run',reason='owned-pending-stop');ended=time.monotonic_ns()
        assert epoch==1 and owner.boundaries._latch.cancelled and owner._capability_pin is None
        assert stop('fixture-run',reason='owned-pending-stop')==epoch
        with pytest.raises(ValueError,match='REPEAT'):stop('fixture-run',reason='changed-stop')
        assert len(created)==1 and not results
        facts.update(route=route,stop_begin_ns=begin,stop_end_ns=ended,stop_epoch=epoch,
            run_lock_held=True,startup_lock_held=True,normal_registry_lock_held=normal_lock_held,
            ordinary_registry_view_lost=route=='registry-view-loss',matching_stop_retained=True,
            no_returned_capability_at_stop=True,foreign_id_rejected=True)
    finally:
        release.set();thread.join(5)
        if normal_lock_held:registry._lock.release()
        if results:
            result=results[0]
            # Inspect original physical outcome before restoring any ordinary view.
            facts.update(primary_original_root_wait=owner._failed_wait is not None,
                startup=asdict(result.startup),diagnostics=list(result.diagnostics),
                dispatch_returned=result.dispatch is not None,closure_returned=result.closure is not None,
                execution_succeeded=result.execution_succeeded,cleanup_complete=result.cleanup_complete,
                creation_count=len(created),start_errors=errors,actual_M1_admissions=0,
                ordinary_map_restored_after_actual_cleanup=route=='registry-view-loss')
            assert facts['primary_original_root_wait']
        registry._entries=original_map
    assert not thread.is_alive() and not errors and len(results)==1
    result=results[0]
    assert result.dispatch is None and result.closure is None and result.execution_succeeded is None
    assert not result.cleanup_complete and not result.ready_for_execution
    assert result.startup.supervisor_reaped and not result.startup.registered
    assert result.startup.registered_helpers_reaped is None and result.startup.unacknowledged_births is None
    assert result.diagnostics==('ML-BOOT-LAUNCH-CANCELLED',)
    replay=entry.start(scope) if route=='direct' else registry.start('fixture-run',scope)
    assert replay is result and len(created)==1
    assert (entry.collect('fixture-run') if route=='direct' else registry.collect('fixture-run')) is None
    facts.update(matching_result_retained=True,collection_absent=True)
