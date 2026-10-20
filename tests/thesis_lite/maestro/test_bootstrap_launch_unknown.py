"""Unknown startup remains unknown after separate owned external harness cleanup."""
from dataclasses import asdict
import errno
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys

import pytest
from xverse.maestro.bootstrap import BootstrapAdmission, encode_bootstrap, seal_helper_image
from xverse.maestro.bootstrap_launcher import BootstrapLaunchError, OriginalBootstrapLauncher
from .test_bootstrap_launcher import pin, registration_faults as registration_faults
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


@pytest.fixture
def unknown_startup(environment,binaries,authority_binary,registration_faults,tmp_path,request):
    factory,_,_=environment
    manager,latch=factory(seconds=45,run_id='fixture-run')
    images=tuple(seal_helper_image(p,digest=pin(p.read_bytes()),
        argv0=sys.executable if p==Path(sys.executable).resolve() else str(p))
        for p in (binaries['launcher'],binaries['bound-gate'],Path(sys.executable).resolve(),authority_binary))
    binary=registration_faults['stopped']
    supervisor=seal_helper_image(binary,digest=pin(binary.read_bytes()),argv0=str(binary))
    boot=encode_bootstrap(BootstrapAdmission('fixture-run','a'*64,'bootstrap-approval',pin(b'owned-environment'),
        supervisor.digest,manager._admission.teardown_deadline,deadline(4.8),images[:3],images[3],manager._root_fd))
    owner=OriginalBootstrapLauncher(boot,supervisor,manager)
    external={}
    try:
        yield owner,external
    finally:
        # Original creation/FD retained by this test before injecting loss. This
        # external authority is never supplied back to the runtime owner.
        process=external.get('process',owner._process)
        fd=external.get('pidfd')
        observed=None
        if process is not None and fd is not None:
            try:signal.pidfd_send_signal(fd,signal.SIGKILL)
            except ProcessLookupError:pass
            assert select.select([fd],[],[],2)[0]
            observed=os.waitid(os.P_PIDFD,fd,os.WEXITED|os.WNOHANG)
            assert observed is not None and observed.si_code==os.CLD_KILLED and observed.si_status==signal.SIGKILL
            process.returncode=-observed.si_status
            assert process.stderr.read()==b''
            process.stderr.close();os.close(fd)
        assert owner._failed_wait is None and owner._session is None
        after=owner.outcome
        assert after.supervisor_reaped is None and not after.cleanup_complete
        with pytest.raises(ValueError,match='RETAINED'):owner.dispose()
        # Descriptors of the externally reaped owned test process are disposed
        # explicitly; this is not OriginalBootstrapLauncher.dispose success.
        if owner._channel is not None:owner._channel.close()
        if owner._pidfd is not None:os.close(owner._pidfd)
        os.close(owner._supervisor_fd)
        for image in (*images,supervisor):os.close(image.descriptor)
        assert not manager._entries
        out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
        if out:
            (Path(out)/('launcher-unknown-'+tmp_path.name+'.json')).write_text(json.dumps(dict(
                case=request.node.name,runtime_outcome=asdict(after),
                external_original_pid=process.pid if process is not None else None,
                external_original_wait={k:getattr(observed,k) for k in ('si_pid','si_uid','si_signo','si_status','si_code')} if observed is not None else None,
                runtime_wait_still_unknown=True,ordinary_disposal_rejected=True,
                external_descriptor_disposal=True,helpers_created=0,workloads_created=0,
                full_M1_complete=False),indent=2)+'\n')


@pytest.mark.parametrize('fault',['lost-popen-return','pidfd-open','pidfd-capability'])
def test_failed_original_identity_is_retained_without_adoption_or_recreation(unknown_startup,monkeypatch,fault):
    import xverse.maestro.bootstrap_launcher as module
    owner,external=unknown_startup
    popen,pidfd_open=subprocess.Popen,os.pidfd_open
    calls=[]
    def lost_return(*a,**kw):
        process=popen(*a,**kw);external['process']=process
        external['pidfd']=pidfd_open(process.pid,0)
        calls.append('lost-return')
        raise OSError(errno.EIO,'owned return-loss injection')
    def lost_pidfd(pid,flags):
        external['pidfd']=pidfd_open(pid,flags);calls.append('pidfd-open')
        raise OSError(errno.EMFILE,'owned original pidfd-open injection')
    def lost_capability(fd):
        external['pidfd']=os.dup(fd);calls.append('pidfd-capability')
        raise OSError(errno.EMFILE,'owned original capability injection')
    end=deadline(2)
    with monkeypatch.context() as patch:
        if fault=='lost-popen-return':patch.setattr(subprocess,'Popen',lost_return)
        elif fault=='pidfd-open':patch.setattr(os,'pidfd_open',lost_pidfd)
        else:patch.setattr(module,'_PidfdCapability',lost_capability)
        with pytest.raises(BootstrapLaunchError) as rejected:owner.launch(end)
    assert rejected.value.owner is owner and len(calls)==1
    facts=owner.outcome
    assert facts.birth_attempted and facts.process_returned is (fault!='lost-popen-return')
    assert not facts.registered and facts.supervisor_reaped is None
    assert facts.registered_helpers_reaped is None and facts.unacknowledged_births is None
    assert not facts.ready_for_execution and not facts.cleanup_complete
    assert owner.boundaries._latch.cancelled
    assert owner._capability is None and owner._failed_wait is None
    with monkeypatch.context() as patch:
        patch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('unknown birth replay'))
        patch.setattr(os,'pidfd_open',lambda *a,**kw:pytest.fail('original identity rediscovery'))
        with pytest.raises(BootstrapLaunchError):owner.launch(end)
        assert owner.drain(deadline(1)).supervisor_reaped is None
        with pytest.raises(ValueError,match='RETAINED'):owner.dispose()
    assert len(calls)==1
