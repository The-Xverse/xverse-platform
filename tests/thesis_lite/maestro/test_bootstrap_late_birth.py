"""Actual late/partially returned original birth; external reap never becomes product proof."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import threading
import time
import pytest
from xverse.maestro.bootstrap_launcher import BootstrapLaunchError
from .test_bootstrap_launcher import startup as startup, registration_faults as registration_faults
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline
from .test_affa_native import authority_binary as authority_binary
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary


@pytest.mark.parametrize('case',['late-return','cancel-before-return','birth-exception','pidfd-open-loss'])
def test_original_late_or_unknown_birth_never_replays_or_adopts_external_wait(startup,registration_faults,request,monkeypatch,case):
    reserve,manager,latch,_=startup;owner=reserve(registration_faults['stopped'])
    popen=subprocess.Popen;pidfd_open=os.pidfd_open;created=[];announced=threading.Event();release=threading.Event()
    errors=[];facts={};cache=[];request.node._launcher_failure_retainer=lambda owners:cache
    end=deadline(1);returned=[]
    class ControlledPopen(popen):
        def __init__(self,*a,**kw):
            super().__init__(*a,**kw)
            held=dict(process=self,pidfd=pidfd_open(self.pid,0),born_ns=time.monotonic_ns())
            created.append(held);announced.set()
            if case=='birth-exception':raise OSError('owned post-birth constructor exception')
            assert release.wait(3), 'owned caller did not release Popen return'
            held['return_ns']=time.monotonic_ns()
    def open_product(pid,*a,**kw):
        if case=='pidfd-open-loss' and created and pid==created[0]['process'].pid:
            raise OSError('owned product pidfd-open failure')
        return pidfd_open(pid,*a,**kw)
    monkeypatch.setattr(subprocess,'Popen',ControlledPopen)
    monkeypatch.setattr(os,'pidfd_open',open_product)
    def launch():
        try:returned.append(owner.launch(end))
        except Exception as error:errors.append(str(error) if str(error).startswith('ML-') else type(error).__name__)
    thread=threading.Thread(target=launch);thread.start()
    primary=None;external_root_cleanup=False;product_disposed=False
    try:
        assert announced.wait(2) and len(created)==1
        if case!='birth-exception':
            assert owner._lock.locked() and owner.outcome.birth_attempted
            assert not owner.outcome.process_returned and owner.outcome.supervisor_reaped is None
            with pytest.raises(ValueError,match='CONFLICT'):owner.drain(deadline(1))
            with pytest.raises(ValueError,match='CONFLICT'):owner.dispose()
            if case=='cancel-before-return':
                owner.cancel('owned-cancel-before-return')
                assert latch.cancelled and owner._capability_pin is None
            if case=='late-return':
                # Actual clock delay; do not alter original deadline or lease.
                while time.monotonic()<=end.monotonic_seconds+.02:time.sleep(.002)
            release.set()
        thread.join(5);assert not thread.is_alive() and len(errors)==1 and not returned
        primary=asdict(owner.outcome)
        assert primary['birth_attempted'] and not primary['registered'] and not primary['cleanup_complete']
        assert latch.cancelled and not manager._entries
        # Matching/changed repeats cannot create or adopt anything.
        before=len(created)
        with pytest.raises(BootstrapLaunchError):owner.launch(end)
        with pytest.raises(ValueError,match='REPEAT'):owner.launch(deadline(.5))
        assert len(created)==before==1
        known=case in ('late-return','cancel-before-return')
        assert primary['process_returned'] is (case!='birth-exception')
        assert primary['supervisor_reaped'] is (True if known else None)
        if known:
            with pytest.raises(ChildProcessError):os.waitid(os.P_PIDFD,created[0]['pidfd'],os.WEXITED|os.WNOHANG|os.WNOWAIT)
            owner.dispose();product_disposed=True
        else:
            assert owner._capability_pin is None and owner._failed_wait is None
            assert owner.drain(deadline(1)).supervisor_reaped is None
            with pytest.raises(ValueError,match='RETAINED'):owner.dispose()
    finally:
        release.set();thread.join(5);assert not thread.is_alive()
        if created:
            held=created[0];process=held['process']
            try:
                wait=os.waitid(os.P_PIDFD,held['pidfd'],os.WEXITED|os.WNOHANG|os.WNOWAIT)
                actual_product_wait=False
            except ChildProcessError:actual_product_wait=True
            if not actual_product_wait:
                external_root_cleanup=True
                signal.pidfd_send_signal(held['pidfd'],signal.SIGKILL)
                wait=os.waitid(os.P_PIDFD,held['pidfd'],os.WEXITED)
                process.returncode=wait.si_status if wait.si_code==os.CLD_EXITED else -wait.si_status
            after=asdict(owner.outcome)
            if not product_disposed:
                # Explicit external descriptor disposal, no product wait/state injection.
                if owner._capability_pin is not None:owner._capability_pin.close()
                if owner._pidfd_pin is not None:os.close(owner._pidfd_pin)
                if owner._channel_pin is not None:owner._channel_pin.close()
                process.stderr.close();os.close(owner._fd_pin)
            os.close(held['pidfd'])
            facts=dict(case=case,primary=primary,after_external_cleanup=after,actual_product_wait=actual_product_wait,
                external_root_cleanup=external_root_cleanup,product_disposed=product_disposed,
                external_descriptor_disposal=not product_disposed,original_birth_ns=held['born_ns'],
                original_return_ns=held.get('return_ns'),original_start_end_ns=int(end.monotonic_seconds*1e9),
                creation_count=len(created),launch_errors=errors,actual_original_root_wait=True,actual_M1_admissions=0)
            out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
            if out:(Path(out)/('late-birth-'+case+'.json')).write_text(json.dumps(facts,indent=2)+'\n')
            cache.append(dict(outcome=primary,original_pid=process.pid,actual_wait_observed=actual_product_wait,
                actual_root_returncode=process.returncode,external_root_cleanup=external_root_cleanup,
                external_descriptor_disposal=not product_disposed))
    if case in ('birth-exception','pidfd-open-loss'):
        assert external_root_cleanup and facts['after_external_cleanup']['supervisor_reaped'] is None
        assert facts['after_external_cleanup']['diagnostic']==primary['diagnostic']
    else:assert not external_root_cleanup and product_disposed
