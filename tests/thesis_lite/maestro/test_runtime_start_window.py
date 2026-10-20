"""Restrict separately approved owned bootstrap; synthetic windows never enable it."""
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path
import subprocess
import time

import pytest
from xverse.maestro.runtime_admission import RunAuthorization,admission_digest
from xverse.maestro.runtime_service import _StartWindow
from .test_bootstrap_launcher import startup as startup,pin
from .test_run_bootstrap import run_stack as run_stack,run_bootstrap_binary as run_bootstrap_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries,deadline
from .test_affa_native import authority_binary as authority_binary
from .test_run_broker import broker_stack as broker_stack


def window(boot,seconds):
    now=datetime.now(timezone.utc)
    authorization=RunAuthorization(boot.admission.approval_ref,boot.admission.run_id,'sha256:'+boot.admission.lifecycle_digest,
        pin(b'SYNTHETIC-RESTRICTION-NOT-AUTHORITY'),pin(boot.private_bytes),pin(b'SYNTHETIC-NOT-M1'),
        now-timedelta(seconds=60),now+timedelta(seconds=seconds),boot.admission.generation)
    return _StartWindow(authorization,admission_digest(authorization),boot)


def test_actual_expiry_after_live_image_hash_rejects_before_original_Popen(startup,monkeypatch):
    import xverse.maestro.bootstrap_launcher as module
    reserve,manager,latch,_=startup;owner=reserve();restriction=window(owner.config,.5)
    owner.bind_start_authorization(restriction);image=module._image;delayed=[]
    def hashed(*a,**kw):
        result=image(*a,**kw)
        if not delayed:
            delayed.append(datetime.now(timezone.utc));time.sleep(.6)
        return result
    with monkeypatch.context() as patch:
        patch.setattr(module,'_image',hashed)
        patch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('expired image verification attempted creation'))
        with pytest.raises(ValueError,match='START-WINDOW'):owner.launch(deadline(2))
    assert len(delayed)==1 and delayed[0]<restriction.authorization.expires_at
    assert not owner._birth_attempted and not latch.cancelled and not manager._entries


@pytest.mark.parametrize('fault',['window-reference','authorization-bytes'])
def test_lost_restriction_rejects_birth_without_blocking_original_disposal(startup,monkeypatch,fault):
    reserve,_,latch,_=startup;owner=reserve();restriction=window(owner.config,30)
    owner.bind_start_authorization(restriction)
    if fault=='window-reference':owner._start_window=None
    else:object.__setattr__(restriction.authorization,'approval_ref','changed')
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('corrupt restriction attempted creation'))
    with pytest.raises(ValueError,match='AUTHORIZATION-REPLACED'):owner.launch(deadline(1))
    assert not owner._birth_attempted and not latch.cancelled
    owner.dispose()


def test_expired_root_helper_birth_keeps_original_wait_and_cleanup(run_stack,monkeypatch,tmp_path):
    session,_,_,helper,private,peer,_=run_stack
    restriction=window(session.config,-1);session.bind_start_authorization(restriction)
    before=(session._sequence,len(session._issued),len(session._pending))
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('denied helper attempted Popen'))
    with pytest.raises(ValueError,match='START-WINDOW'):session.birth(4,helper,helper,peer,private,deadline(1))
    assert before==(session._sequence,len(session._issued),len(session._pending))
    object.__setattr__(restriction.authorization,'approval_ref','changed')
    with pytest.raises(ValueError,match='AUTHORIZATION-REPLACED'):session.check_start_authorization()
    session.cancel('owned-expired-restriction-cleanup');observed=session.drain(deadline(1.8))
    assert observed.supervisor_reaped and observed.registered_children_reaped and observed.unacknowledged_births==0
    out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        (Path(out)/('window-denial-'+tmp_path.name+'.json')).write_text(json.dumps(dict(
            case='helper-birth',before=before,after=(session._sequence,len(session._issued),len(session._pending)),
            original_root_wait=session._root_result is not None,original_helpers=len(session._children),
            expiry_and_corruption_cleanup_preserved=True,actual_M1_admissions=0),indent=2)+'\n')


def test_actual_expiry_during_C1_validation_rejects_before_slot_or_BIRTH_RPC(run_stack,monkeypatch):
    root,manager,_,helper,private,peer,_=run_stack
    restriction=window(root.config,.2);root.bind_start_authorization(restriction)
    authority=manager._authority;rpc=root._rpc;observed=[]
    def checked(*a,**kw):
        result=authority(*a,**kw)
        if not observed:
            observed.append(datetime.now(timezone.utc));time.sleep(.3)
        return result
    def no_birth(kind,*a,**kw):
        if kind==1:pytest.fail('expired C1 validation reached BIRTH RPC')
        return rpc(kind,*a,**kw)
    before=(root._slot,root._sequence,len(root._issued),len(root._pending))
    with monkeypatch.context() as patch:
        patch.setattr(manager,'_authority',checked);patch.setattr(root,'_rpc',no_birth)
        with pytest.raises(ValueError,match='START-WINDOW'):root.birth(3,helper,helper,peer,private,deadline(1))
    assert len(observed)==1 and observed[0]<restriction.authorization.expires_at
    assert before==(root._slot,root._sequence,len(root._issued),len(root._pending))
    assert not root.latch.cancelled


def test_expired_controller_permission_rejects_before_new_C1_and_preserves_cancel(request,monkeypatch,tmp_path):
    from xverse.maestro.run_broker import RunBroker
    from xverse.maestro.prbc import ProcessBoundaryOps
    admit=RunBroker.admit
    monkeypatch.setattr(RunBroker,'admit',classmethod(lambda cls,*a,**kw:admit(*a,controller_sessions=1,**kw)))
    broker,_,_,_=request.getfixturevalue('broker_stack');root=broker.session
    restriction=window(root.config,-1);root.bind_start_authorization(restriction)
    before=(root._sequence,len(root._issued),len(root.boundaries._entries))
    with monkeypatch.context() as patch:
        patch.setattr(ProcessBoundaryOps,'create_frozen',lambda *a,**kw:pytest.fail('expired controller created C1'))
        with pytest.raises(ValueError,match='START-WINDOW'):broker.admit_controller('expired-successor',deadline(1))
    assert before==(root._sequence,len(root._issued),len(root.boundaries._entries))
    object.__setattr__(restriction.authorization,'approval_ref','changed')
    result=broker.cancel('owned-expired-controller-cleanup')
    assert result.native_epoch_confirmed or result.issuer_reaped
    out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        (Path(out)/('window-denial-'+tmp_path.name+'.json')).write_text(json.dumps(dict(
            case='controller-allocation',before=before,after=(root._sequence,len(root._issued),len(root.boundaries._entries)),
            original_helpers=len(root._children),new_controller_count=len(broker._controllers),
            corruption_cancel_preserved=True,actual_M1_admissions=0),indent=2)+'\n')
