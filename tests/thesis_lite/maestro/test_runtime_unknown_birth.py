"""Whole-entry unknown startup remains unknown after external original-child reap."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import subprocess
import pytest
from .test_runtime_entry import runtime as runtime
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries
from .test_affa_native import authority_binary as authority_binary
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary


@pytest.mark.parametrize('case',['birth-exception','pidfd-open-loss'])
def test_whole_runtime_returns_incomplete_unknown_birth_without_replay_or_adoption(runtime,request,monkeypatch,case):
    entry,scope,_=runtime;owner=entry._pins[1];popen=subprocess.Popen;pidfd_open=os.pidfd_open
    created=[];facts={}
    class ControlledPopen(popen):
        def __init__(self,*a,**kw):
            super().__init__(*a,**kw)
            created.append(dict(process=self,pidfd=pidfd_open(self.pid,0)))
            if case=='birth-exception':raise OSError('owned actual birth before constructor return')
    def product_open(pid,*a,**kw):
        if case=='pidfd-open-loss' and created and pid==created[0]['process'].pid:raise OSError('owned product pidfd failure')
        return pidfd_open(pid,*a,**kw)
    def retain(value,end,work,manager,out):
        assert facts.get('actual_external_original_wait') and not manager._entries
        # Product has no original capability; disposal stays unavailable even
        # though this test bootstrap owns and has reaped the actual direct child.
        assert owner.outcome.supervisor_reaped is None and owner._capability_pin is None
        if owner._channel_pin is not None:owner._channel_pin.close()
        if created:created[0]['process'].stderr.close()
        os.close(owner._fd_pin)
        if out:(Path(out)/('runtime-unknown-birth-'+case+'.json')).write_text(json.dumps(facts,indent=2)+'\n')
    request.node._runtime_failure_retainer=retain
    monkeypatch.setattr(subprocess,'Popen',ControlledPopen);monkeypatch.setattr(os,'pidfd_open',product_open)
    try:
        result=entry.start(scope)
        assert len(created)==1 and result.dispatch is None and result.closure is None
        assert result.execution_succeeded is None and not result.cleanup_complete and not result.ready_for_execution
        assert result.startup.birth_attempted and result.startup.process_returned is (case=='pidfd-open-loss')
        assert result.startup.supervisor_reaped is None and not result.startup.registered
        assert result.diagnostics==('ML-BOOT-LAUNCH-FAILED',) and result.persistence_failure is None
        assert entry.start(scope) is result and len(created)==1
        assert entry.collect('fixture-run') is None
        with pytest.raises(ValueError,match='RETAINED'):entry.dispose()
        facts.update(case=case,primary_startup=asdict(result.startup),diagnostics=list(result.diagnostics),
            dispatch_returned=False,closure_returned=False,cleanup_complete=result.cleanup_complete,
            matching_result_retained=True,creation_count=len(created),actual_M1_admissions=0)
    finally:
        if created:
            held=created[0]
            try:signal.pidfd_send_signal(held['pidfd'],signal.SIGKILL)
            except ProcessLookupError:pass
            wait=os.waitid(os.P_PIDFD,held['pidfd'],os.WEXITED)
            held['process'].returncode=wait.si_status if wait.si_code==os.CLD_EXITED else -wait.si_status
            os.close(held['pidfd'])
            facts.update(actual_external_original_wait=True,external_returncode=held['process'].returncode,
                after_external_startup=asdict(owner.outcome),external_descriptor_disposal=True)
    assert facts['primary_startup']==facts['after_external_startup']
    assert entry.start(scope) is result and not result.cleanup_complete and len(created)==1
    with pytest.raises(ValueError,match='RETAINED'):entry.dispose()
