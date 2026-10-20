"""Actual owned startup/waits; no synthetic M1 attestation or public run entry."""
from dataclasses import asdict, replace
import copy
import hashlib
import json
import os
from pathlib import Path
import pickle
import select
import signal
import subprocess
import sys
import threading
import time

import pytest
from xverse.maestro.bootstrap import BootstrapAdmission, HelperImage, encode_bootstrap, seal_helper_image
from xverse.maestro.bootstrap_launcher import BootstrapLaunchError, OriginalBootstrapLauncher, OriginalBootstrapRegistry
from xverse.maestro.time import HostDeadline
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary


def pin(data):
    return 'sha256:'+hashlib.sha256(data).hexdigest()


@pytest.fixture(scope='module')
def registration_faults(tmp_path_factory):
    root = tmp_path_factory.mktemp('registration-faults')
    source = Path(__file__).with_name('bootstrap_registration_fault.c')
    result = {}
    receipts = []
    for mode in ('malformed','stopped'):
        target = root/mode
        command = ['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',
                   *(['-DSTOP_READY'] if mode=='stopped' else []),str(source),'-o',str(target)]
        subprocess.run(command,check=True,capture_output=True,timeout=20)
        result[mode] = target
        receipts.append(dict(mode=mode,command=command,returncode=0,
            source_sha256=pin(source.read_bytes()),binary_sha256=pin(target.read_bytes())))
    out = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        Path(out).mkdir(parents=True,exist_ok=True)
        (Path(out)/'registration-fault-native.json').write_text(json.dumps(receipts,indent=2)+'\n')
    return result


@pytest.fixture
def startup(environment,binaries,authority_binary,run_bootstrap_binary,request,tmp_path):
    factory,_,_ = environment
    manager,latch = factory(seconds=45,run_id='fixture-run')
    images, owners, extra_fds = [], [], []
    sources = (binaries['launcher'],binaries['bound-gate'],Path(sys.executable).resolve(),authority_binary)
    for source in sources:
        images.append(seal_helper_image(source,digest=pin(source.read_bytes()),
            argv0=sys.executable if source==Path(sys.executable).resolve() else str(source)))

    def reserve(source=run_bootstrap_binary,*,transform=None,registry=None):
        supervisor = seal_helper_image(source,digest=pin(source.read_bytes()),argv0=str(source))
        extra_fds.append(supervisor.descriptor)
        admission = BootstrapAdmission('fixture-run',hashlib.sha256(b'owned-launch-plan').hexdigest(),
            'bootstrap-approval',pin(b'owned-environment'),supervisor.digest,
            manager._admission.teardown_deadline,deadline(4.8),tuple(images[:3]),images[3],manager._root_fd)
        config = encode_bootstrap(admission)
        if transform:
            config,supervisor = transform(config,supervisor)
        owner = (registry.reserve(config,supervisor,manager) if registry else
                 OriginalBootstrapLauncher(config,supervisor,manager))
        owners.append(owner)
        return owner

    yield reserve,manager,latch,extra_fds
    observations=[]
    retainer=getattr(request.node,'_launcher_failure_retainer',None)
    for owner in (() if retainer else owners):
        if owner._birth_attempted and not owner._disposed:
            owner.drain(deadline(1.8))
        observations.append(dict(outcome=asdict(owner.outcome),
            original_pid=owner._process.pid if owner._process is not None else None,
            actual_wait_observed=owner._failed_wait is not None or bool(owner._session and owner._session._root_result),
            actual_root_returncode=owner._process.returncode if owner._process is not None else None))
        owner.dispose()
    if retainer:observations=retainer(owners)
    for image in images:
        os.close(image.descriptor)
    for fd in extra_fds:
        os.close(fd)
    assert not manager._entries
    out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        (Path(out)/('launcher-waits-'+tmp_path.name+'.json')).write_text(json.dumps(dict(
            case=request.node.name,owners=observations,original_parent_identity=list(manager._root_identity),
            helpers_created=0,workloads_created=0,full_M1_complete=False),indent=2)+'\n')


def no_birth(monkeypatch):
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('unexpected creation'))


def test_original_ready_matching_repeat_and_changed_repeat_without_cancel(startup,monkeypatch):
    reserve,manager,latch,_=startup
    owner=reserve(); end=deadline(2)
    session=owner.launch(end)
    before=session._sequence
    with monkeypatch.context() as patch:
        no_birth(patch)
        assert owner.launch(end) is session
        with pytest.raises(ValueError,match='LAUNCH-REPEAT'):
            owner.launch(deadline(1))
    assert not latch.cancelled and not session._closed and session._sequence==before
    assert owner.outcome.registered and not owner.outcome.ready_for_execution
    assert not owner.outcome.cleanup_complete
    with pytest.raises(ValueError,match='RETAINED'):
        owner.dispose()
    result=owner.drain(deadline(1.8))
    assert result.supervisor_reaped and result.registered_helpers_reaped
    assert result.unacknowledged_births==0 and not result.cleanup_complete
    assert session._root_result is not None and owner._failed_wait is None
    owner.dispose();owner.dispose()
    with pytest.raises(ValueError,match='DISPOSED'):
        owner.launch(end)


@pytest.mark.parametrize('fault',['supervisor-bytes','helper-bytes','unsealed','private-bytes','parent','approval','run','generation','lease','cancelled'])
def test_rejection_before_creation_preserves_latch_and_original_parent(startup,monkeypatch,fault):
    reserve,manager,latch,extra_fds=startup
    def transform(config,image):
        admission=config.admission
        if fault=='supervisor-bytes':
            image=replace(image,digest=pin(b'incorrect-supervisor'))
            admission=replace(admission,supervisor_artifact_digest=image.digest)
        elif fault=='helper-bytes':
            helpers=(replace(admission.images[0],digest=pin(b'incorrect-helper')),*admission.images[1:])
            admission=replace(admission,images=helpers)
        elif fault=='unsealed':
            fd=os.memfd_create('owned-unsealed-image',os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING)
            os.write(fd,os.pread(image.descriptor,os.fstat(image.descriptor).st_size,0));extra_fds.append(fd)
            image=replace(image,descriptor=fd)
        elif fault=='private-bytes':
            return replace(config,private_bytes=config.private_bytes+b'X'),image
        elif fault=='parent':
            fd=os.dup(manager._root_fd);extra_fds.append(fd)
            admission=replace(admission,boundary_parent=fd)
        elif fault=='approval':
            admission=replace(admission,approval_ref='changed-approval')
        elif fault=='run':
            admission=replace(admission,run_id='changed-run')
        elif fault=='generation':
            admission=replace(admission,generation=HostDeadline(admission.generation.session,admission.generation.monotonic_seconds-1))
        return encode_bootstrap(admission),image
    owner=reserve(transform=transform)
    if fault=='cancelled':latch.cancel('owned-pre-cancel')
    before=os.fstat(manager._root_fd)
    with monkeypatch.context() as patch:
        no_birth(patch)
        with pytest.raises(BootstrapLaunchError) as rejected:
            owner.launch(deadline(4.9 if fault=='lease' else 2))
    assert rejected.value.owner is owner
    assert not owner.outcome.birth_attempted and not owner.outcome.process_returned
    assert owner.outcome.supervisor_reaped is None and not owner.outcome.cleanup_complete
    assert latch.cancelled==(fault=='cancelled')
    after=os.fstat(manager._root_fd)
    assert (before.st_dev,before.st_ino)==(after.st_dev,after.st_ino)
    assert not manager._entries


@pytest.mark.parametrize('fault',['malformed','stopped'])
def test_failed_registration_preserves_original_wait_and_never_recreates(startup,registration_faults,fault,monkeypatch):
    reserve,_,latch,_=startup
    owner=reserve(registration_faults[fault]);end=deadline(.25 if fault=='stopped' else 2)
    began=time.monotonic()
    with pytest.raises(BootstrapLaunchError) as rejected:
        owner.launch(end)
    assert rejected.value.owner is owner
    result=owner.outcome
    assert result.birth_attempted and result.process_returned and not result.registered
    assert result.supervisor_reaped and result.registered_helpers_reaped is None
    assert result.unacknowledged_births is None and not result.cleanup_complete
    assert owner._failed_wait is not None and owner._process.returncode==-signal.SIGKILL
    assert time.monotonic()<=end.monotonic_seconds+2 and time.monotonic()>began
    assert latch.cancelled
    with monkeypatch.context() as patch:
        no_birth(patch)
        with pytest.raises(BootstrapLaunchError):owner.launch(end)


def test_cancel_during_stopped_ready_does_not_wait_on_startup_lock(startup,registration_faults):
    reserve,_,latch,_=startup
    owner=reserve(registration_faults['stopped']);end=deadline(2)
    errors=[]
    def launch():
        try:owner.launch(end)
        except BootstrapLaunchError as error:errors.append(error)
    thread=threading.Thread(target=launch);thread.start()
    try:
        until=time.monotonic()+1.5;stopped=None
        while time.monotonic()<until:
            cap=owner._capability
            if cap:
                stopped=os.waitid(os.P_PIDFD,cap.fileno(),os.WSTOPPED|os.WNOHANG|os.WNOWAIT)
                if stopped:break
            time.sleep(.002)
        assert stopped is not None and stopped.si_code==os.CLD_STOPPED
        assert owner._lock.locked()
        with pytest.raises(ValueError,match='CONFLICT'):owner.drain(deadline(1))
        with pytest.raises(ValueError,match='CONFLICT'):owner.dispose()
        owner.cancel('owned-startup-cancel')
        assert latch.cancelled
    finally:
        owner.cancel('owned-startup-finally');thread.join(4)
    assert not thread.is_alive() and len(errors)==1
    assert owner.outcome.supervisor_reaped and not owner.outcome.registered
    assert owner._process.returncode==-signal.SIGKILL


def test_original_registry_reservations_capacity_and_no_copy(startup,monkeypatch):
    reserve,manager,latch,_=startup
    registry=OriginalBootstrapRegistry(1);owner=reserve(registry=registry)
    for original in (registry,owner):
        with pytest.raises(TypeError):copy.copy(original)
        with pytest.raises(TypeError):pickle.dumps(original)
    with monkeypatch.context() as patch:
        no_birth(patch)
        assert registry.reserve(owner.config,owner.supervisor_image,manager) is owner
        with pytest.raises(ValueError,match='REGISTRY-REPEAT'):
            registry.reserve(replace(owner.config),owner.supervisor_image,manager)
        other=encode_bootstrap(replace(owner.config.admission,run_id='other-run'))
        with pytest.raises(ValueError,match='REGISTRY-FULL'):
            registry.reserve(other,owner.supervisor_image,manager)
        # Matching reservation lookup does not redo a new/expired admission.
        import xverse.maestro.bootstrap_launcher as module
        patch.setattr(module,'encode_bootstrap',lambda *a:pytest.fail('new admission on matching lookup'))
        assert registry.reserve(owner.config,owner.supervisor_image,manager) is owner
    assert len(registry._entries)==1 and not latch.cancelled and not owner.outcome.birth_attempted


@pytest.mark.parametrize('capacity',[0,129,True,None])
def test_registry_capacity_rejects(capacity):
    with pytest.raises(ValueError,match='CAPACITY'):OriginalBootstrapRegistry(capacity)
