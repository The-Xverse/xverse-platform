"""Original launcher into existing v6 terminal/closure; partial entry, not M1."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

import pytest
from xverse.maestro.bootstrap import BootstrapAdmission, encode_bootstrap, seal_helper_image
from xverse.maestro.bootstrap_launcher import OriginalBootstrapRegistry
from xverse.maestro.persistence import PersistenceClient, PersistenceError
from xverse.maestro.prbc import BoundaryDescriptor
from xverse.maestro.providers import ProbePolicy
from xverse.maestro.run_broker import RunBroker, UnitAdmission
from xverse.maestro.run_closure import RunClosure
from . import test_run_broker
from .test_bootstrap_launcher import pin
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, configured, deadline
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_terminal_runtime import scheduled, run, verify, retain
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations


@pytest.fixture
def broker_stack(environment,binaries,authority_binary,run_bootstrap_binary,tmp_path):
    factory,_,_=environment
    manager,latch=factory(seconds=45,run_id='fixture-run')
    config,_,work=configured(tmp_path,manager,dict(binaries,launcher=authority_binary))
    images=tuple(seal_helper_image(p,digest=pin(p.read_bytes()),
        argv0=sys.executable if p==Path(sys.executable).resolve() else str(p))
        for p in (binaries['launcher'],binaries['bound-gate'],Path(sys.executable).resolve(),authority_binary))
    supervisor=seal_helper_image(run_bootstrap_binary,digest=pin(run_bootstrap_binary.read_bytes()),argv0=str(run_bootstrap_binary))
    boot=encode_bootstrap(BootstrapAdmission('fixture-run',config.prepared.lifecycle_digest,
        'bootstrap-approval',pin(b'owned-environment'),supervisor.digest,
        manager._admission.teardown_deadline,deadline(4.8),images[:3],images[3],manager._root_fd))
    registry=OriginalBootstrapRegistry(1)
    launcher=registry.reserve(boot,supervisor,manager)
    session=storage=broker=None
    def boundary(name,unit):
        descriptor=BoundaryDescriptor('fixture-run',unit,1,name,0)
        manager.create_frozen(descriptor)
        return descriptor
    try:
        session=launcher.launch(deadline(2))
        storage=session.persistence(config,boundary('storage','helper:storage'),deadline(2))
        units=tuple(UnitAdmission(boundary('unit-'+str(i),u.unit_id),(('MAESTRO_VISIBLE','declared'),),3)
                    for i,u in enumerate(config.prepared.units))
        broker=RunBroker.admit(session,storage,units,boundary('authority','helper:authority'),deadline=deadline(2))
        facade=test_run_broker.ProcessReadiness(broker.owner,
            policies=tuple(ProbePolicy(u.unit_id,2,.5,.5) for u in config.prepared.units))
        broker._owned_test_startup=launcher  # observational test reference, no authority API
        yield broker,facade,storage,work
    finally:
        if broker:broker.cancel('owned-launcher-composition-teardown')
        if storage:
            if not storage._failed and not storage._aborted:
                try:storage.abort(deadline(1))
                except (ValueError,OSError):storage._fail()
            assert storage.drain(deadline(1)).worker_reaped
        outcome=launcher.drain(deadline(1.8))
        assert outcome.supervisor_reaped and outcome.registered_helpers_reaped
        assert outcome.unacknowledged_births==0
        if broker:broker.dispose()
        assert launcher._process.stderr.read()==b''
        launcher.dispose()
        for entry in manager._entries.values():
            if entry.state!='released':
                result=manager.force_cleanup(entry.descriptor)
                assert result.boundary_released and result.residual_count==0
        for image in (*images,supervisor):os.close(image.descriptor)
        out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
        if out:
            (Path(out)/('launcher-composition-waits-'+tmp_path.name+'.json')).write_text(json.dumps(dict(
                outcome=asdict(outcome),original_pid=launcher._process.pid,
                actual_root_wait_observed=session._root_result is not None,
                original_helper_count=len(session._children),
                original_helpers_actually_reaped=all(c._result is not None for c in session._children.values()),
                all_original_C1_released=all(e.state=='released' for e in manager._entries.values()),
                full_M1_complete=False),indent=2)+'\n')


@pytest.mark.parametrize('case',['closed','lost-close-ack'])
def test_actual_original_startup_through_terminal_and_helper_closure(request,monkeypatch,case):
    stack,_,driver=scheduled(request,monkeypatch)
    broker,_,client,work=stack
    launcher=broker._owned_test_startup
    original=PersistenceClient._rpc
    def rpc(self,kind,body,end,**kw):
        reply=original(self,kind,body,end,**kw)
        if self is client and case=='lost-close-ack' and kind=='terminal-report' and body['action']=='close':
            raise PersistenceError('ML-TEST-LOST-ACK')
        return reply
    monkeypatch.setattr(PersistenceClient,'_rpc',rpc)
    result=run(driver)
    assert result.execution_succeeded and result.terminal is not None,result.diagnostic
    if case=='closed':
        assert result.terminal.public_data()['writer']['evidence_complete']
        assert verify(client,work.parent/'argus').complete
    else:
        assert result.terminal.public_data()['writer'] is None
        assert client._failed and client.last_writer_state=='open'
    before=(work.parent/'argus/manifest.json').read_bytes()
    closer=RunClosure(broker.session,dispatcher=driver);end=deadline(6)
    closed=closer.close(end)
    assert closed.cleanup_complete and closed.normal_unit_records_complete,closed
    assert closed.root_reaped and all(h.process_reaped for h in closed.helpers)
    assert {h.role for h in closed.helpers}=={3,4,5}
    assert all(b.empty and b.released for b in closed.boundaries)
    assert closed.terminal_reports==(result.terminal,) and closed.writers==()
    assert closer.close(end) is closed
    assert (work.parent/'argus/manifest.json').read_bytes()==before
    assert launcher.outcome.supervisor_reaped and launcher._failed_wait is None
    assert not closed.lifecycle_complete and not launcher.outcome.ready_for_execution
    retain(stack,result,'launcher-'+case)
    out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        closure=asdict(closed);closure['cleanup_complete']=closed.cleanup_complete
        closure['terminal_reports']=[r.public_data() for r in closed.terminal_reports]
        (Path(out)/('launcher-composition-'+work.parent.name+'.json')).write_text(json.dumps(dict(
            case=case,closure=closure,startup=asdict(launcher.outcome),
            original_fixture=str(work.parent),full_M1_complete=False,scientific_result=False),indent=2)+'\n')
