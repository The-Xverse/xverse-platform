"""Private whole-run execution using explicit owned bootstrap/permits, no M1 vectors."""
from dataclasses import asdict, replace
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

import pytest
from xverse.maestro.artifacts import ArtifactDeclaration
from xverse.maestro.bootstrap import BootstrapAdmission, encode_bootstrap, seal_helper_image
from xverse.maestro.bootstrap_launcher import OriginalBootstrapRegistry
from xverse.maestro.collection_plan import admit_collection
from xverse.maestro.coverage import ArtifactExpectation, admit_coverage
from xverse.maestro.persistence import PersistenceClient, PersistenceError
from xverse.maestro.prbc import BoundaryDescriptor
from xverse.maestro.projection import Limits
from xverse.maestro.providers import ProbePolicy
from xverse.maestro.public_blobs import admit_broker_artifact
from xverse.maestro.run_broker import UnitAdmission
from xverse.maestro.runtime_entry import RuntimeScope, _OriginalRuntimeRun
from xverse.maestro.runtime_verification import runtime_admission_digest
from xverse.maestro.schedule_plan import admit_schedule
from xverse.maestro.time import HostDeadline
from . import test_launcher
from .test_bootstrap_launcher import pin
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_terminal_runtime import verify
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations


@pytest.fixture
def runtime(environment,binaries,authority_binary,run_bootstrap_binary,tmp_path,monkeypatch,request):
    factory,_,_=environment;manager,_=factory(seconds=45,run_id='fixture-run')
    controller_recovery=getattr(request,'param',None)=='recovery'
    original_docs=test_launcher.documents
    def documents():
        data=original_docs();scenario=data['scenario.json']['spec'];template=scenario['steps'][0]
        scenario['steps']=[]
        for name,unit,phase,tick,deps in [
            ('prepare-source','source','prepare',0,[]),('prepare-sink','sink','prepare',0,[]),
            ('start-source','source','start',0,['prepare-source']),('start-sink','sink','start',0,['prepare-sink','start-source']),
            ('observe-source','source','observe',1,['start-source']),('observe-sink','sink','observe',1,['start-sink']),
            ('stop-sink','sink','stop',2,['observe-sink']),('cleanup-sink','sink','cleanup',2,['stop-sink']),
            ('stop-source','source','stop',3,['observe-source']),('cleanup-source','source','cleanup',3,['stop-source'])]:
            step=copy.deepcopy(template);step['id']=name;step['targetRef']['element']=unit+'-instance'
            step['actionKind']='validate' if phase=='prepare' else phase;step['action']['operation']=step['actionKind']
            step['schedule']['at']=tick;ext=step['extensions']['io.xverse.experiment']
            ext['target']['element']=name;ext['phase']=phase;ext['dependsOn']=deps;scenario['steps'].append(step)
        return data
    monkeypatch.setattr(test_launcher,'documents',documents)
    prepare=test_launcher.prepare_lifecycle
    monkeypatch.setattr(test_launcher,'prepare_lifecycle',lambda *a,**kw:prepare(*a,limits=Limits(horizon_ticks=3),**kw))
    encode=test_launcher.encode_configuration
    def configuration(prepared,result,resources,**kw):
        import time
        schedule=admit_schedule(prepared,policies=tuple(ProbePolicy(u.unit_id,5,5,.5) for u in prepared.units),
            ticks=(0,1,2,3),active_seconds=20 if controller_recovery else 4.8,operation_seconds=.5,per_unit_seconds=1,poll_seconds=.05,
            request_limit=1024,service_operation_count=4,recovery_operation_seconds=3 if controller_recovery else None)
        source=Path(kw['journal_path']).parent/'work';st=source.stat()
        declarations=tuple(ArtifactDeclaration(u.unit_id,1,u.binding_id+'.marker','outputs/'+u.binding_id+'.txt') for u in prepared.units)
        coverage=admit_coverage(prepared,result,resources,run_id=kw['run_id'],host_session=kw['session'],
            contexts=[(b.unit_id,b.generation,b.execution_id) for b in kw['bindings']],
            health_policies={p.unit_id:(p.cadence_seconds,p.freshness_seconds) for p in schedule.policies},
            active_start=time.monotonic(),active_end=time.monotonic()+schedule.active_seconds,source_digests=(pin(schedule.canonical_bytes),),
            artifacts=[*(ArtifactExpectation(d.destination,True,32,d.unit_id,1) for d in declarations),ArtifactExpectation('collection-result.json',maximum_bytes=16384)])
        collection=admit_collection(coverage,expected_digest=coverage.digest,source_root=str(source),source_identity=(st.st_dev,st.st_ino),
            declarations=declarations,metadata_path='collection-result.json',operation_seconds=.5,per_unit_teardown_seconds=1,
            collection_seconds=2,terminal_seconds=2,drain_seconds=2)
        return encode(prepared,result,resources,**kw,schedule=schedule,coverage=coverage,collection=collection,
            broker_artifact=admit_broker_artifact(coverage,expected_digest=coverage.digest))
    monkeypatch.setattr(test_launcher,'encode_configuration',configuration)
    config,_,work=test_launcher.configured(tmp_path,manager,dict(binaries,launcher=authority_binary))
    images=tuple(seal_helper_image(p,digest=pin(p.read_bytes()),argv0=sys.executable if p==Path(sys.executable).resolve() else str(p))
        for p in (binaries['launcher'],binaries['bound-gate'],Path(sys.executable).resolve(),authority_binary))
    supervisor=seal_helper_image(run_bootstrap_binary,digest=pin(run_bootstrap_binary.read_bytes()),argv0=str(run_bootstrap_binary))
    boot=encode_bootstrap(BootstrapAdmission(config.run_id,config.prepared.lifecycle_digest,'bootstrap-approval',pin(b'owned-environment'),
        supervisor.digest,manager._admission.teardown_deadline,deadline(4.8),images[:3],images[3],manager._root_fd))
    launcher=OriginalBootstrapRegistry(1).reserve(boot,supervisor,manager)
    units=tuple(UnitAdmission(BoundaryDescriptor(config.run_id,u.unit_id,1,'work-'+str(i),0),(('MAESTRO_VISIBLE','declared'),),1)
                for i,u in enumerate(config.prepared.units))
    entry=_OriginalRuntimeRun(config,launcher,units,controller_sessions=2 if controller_recovery else 1,
        allow_controller_recovery=controller_recovery)
    active=HostDeadline(config.session,config.coverage.data(config.coverage.digest)['end']-.01)
    terminal=HostDeadline(config.session,active.monotonic_seconds+config.schedule.terminal_reserve_seconds+4+.01)
    scope=RuntimeScope(deadline(2),active,terminal,HostDeadline(config.session,terminal.monotonic_seconds+3))
    output=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        (Path(output)/('entry-original-inputs-'+tmp_path.name+'.json')).write_text(json.dumps(dict(
            original_admission=json.loads(config.coverage.public_bytes),admission_digest=config.coverage.digest,
            original_collection=json.loads(config.collection.canonical_bytes),generation_ns=config.generation_ns,
            runtime_digest=runtime_admission_digest(config.coverage,config.collection,config.generation_ns),
            original_fixture=str(tmp_path),full_M1_complete=False),indent=2)+'\n')
    try:yield entry,scope,work
    finally:
        out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
        failure_retainer=getattr(request.node,'_runtime_failure_retainer',None)
        if failure_retainer is not None:
            failure_retainer(entry,scope,work,manager,out)
        elif entry._result is not None:
            result=entry._result
            if out and result.dispatch is not None:
                dispatch=result.dispatch
                (Path(out)/('runtime-dispatch-'+tmp_path.name+'.json')).write_text(json.dumps(dict(
                    diagnostic=dispatch.diagnostic,execution_succeeded=dispatch.execution_succeeded,
                    terminal_recorded=dispatch.terminal_recorded,steps=[asdict(s) for s in dispatch.steps],
                    cleanup=asdict(dispatch.cleanup),health_scans=dispatch.health_scans,
                    lease_renewals=dispatch.lease_renewals,full_M1_complete=False),indent=2)+'\n')
            assert result.startup.supervisor_reaped and result.startup.registered_helpers_reaped
            assert result.startup.unacknowledged_births==0
            assert launcher._process.stderr.read()==b''
            if out:
                closure=asdict(result.closure);closure['cleanup_complete']=result.cleanup_complete
                closure['terminal_reports']=[r.public_data() for r in result.closure.terminal_reports]
                (Path(out)/('runtime-entry-waits-'+tmp_path.name+'.json')).write_text(json.dumps(dict(
                    case=request.node.name,startup=asdict(result.startup),closure=closure,diagnostics=result.diagnostics,
                    original_fixture=str(tmp_path),original_root_wait=entry._session._root_result is not None,
                    actual_original_helper_waits=all(c._result is not None for c in entry._session._children.values()),
                    all_original_C1_released=all(e.state=='released' for e in manager._entries.values()),
                    full_M1_complete=False),indent=2)+'\n')
            entry.dispose()
        else:launcher.dispose()
        for image in (*images,supervisor):os.close(image.descriptor)


@pytest.mark.parametrize('case',['closed','lost-close-ack'])
def test_whole_original_start_returns_after_actual_terminal_and_helper_closure(runtime,monkeypatch,case):
    entry,scope,work=runtime
    original=PersistenceClient._rpc
    def rpc(self,kind,body,end,**kw):
        reply=original(self,kind,body,end,**kw)
        if case=='lost-close-ack' and kind=='terminal-report' and body['action']=='close':raise PersistenceError('ML-TEST-LOST-ACK')
        return reply
    monkeypatch.setattr(PersistenceClient,'_rpc',rpc)
    result=entry.start(scope)
    assert result.execution_succeeded and result.cleanup_complete,result
    assert not result.diagnostics and result.closure.normal_unit_records_complete
    assert result.closure.root_reaped and {h.role for h in result.closure.helpers}=={3,4,5}
    assert all(u.direct_child_reaped and u.native_retired for u in result.closure.native_units)
    assert not result.lifecycle_complete and not result.ready_for_execution
    if case=='closed':
        assert result.dispatch.terminal.public_data()['writer']['evidence_complete']
        assert verify(entry._storage,work.parent/'argus').complete
    else:
        assert result.dispatch.terminal.public_data()['writer'] is None
        assert entry._storage.last_writer_state=='open' and entry._storage._failed
    with monkeypatch.context() as patch:
        patch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('matching run replay created process'))
        assert entry.start(scope) is result
        assert entry.collect(result.run_id) is result.dispatch.collection
        with pytest.raises(ValueError,match='REPEAT'):entry.start(replace(scope,startup=deadline(1)))
        with pytest.raises(ValueError,match='IDENTITY'):entry.collect('foreign')
    assert not result.closure.writers and result.closure.terminal_reports==(result.dispatch.terminal,)


@pytest.mark.parametrize('fault',['clock','startup','terminal','closure'])
def test_changed_ends_reject_before_any_creation_or_latch_mutation(runtime,monkeypatch,fault):
    entry,scope,_=runtime
    if fault=='clock':scope=replace(scope,startup=HostDeadline('foreign',scope.startup.monotonic_seconds))
    elif fault=='startup':scope=replace(scope,startup=scope.active)
    elif fault=='terminal':scope=replace(scope,terminal=scope.active)
    else:scope=replace(scope,closure=HostDeadline(scope.closure.session,entry._persistence.generation_ns/1e9+1))
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('invalid scope created process'))
    with pytest.raises(ValueError,match='ENTRY-END'):entry.start(scope)
    assert entry._scope is None and not entry._launcher.boundaries._entries
    assert not entry._launcher.boundaries._latch.cancelled


def test_original_stop_repeats_and_start_conflict_do_not_need_start_lock(runtime,monkeypatch):
    entry,scope,_=runtime
    with pytest.raises(TypeError):copy.copy(entry)
    entry._lock.acquire()
    try:
        with pytest.raises(ValueError,match='CONFLICT'):entry.start(scope)
        with pytest.raises(ValueError,match='IDENTITY'):entry.stop('foreign')
        assert not entry._launcher.boundaries._latch.cancelled
        assert entry.stop('fixture-run',reason='owned-stop')==1
        with monkeypatch.context() as patch:
            patch.setattr(entry._launcher,'cancel',lambda *a,**kw:pytest.fail('matching stop repeated cancellation'))
            assert entry.stop('fixture-run',reason='owned-stop')==1
        with pytest.raises(ValueError,match='REPEAT'):entry.stop('fixture-run',reason='changed')
    finally:entry._lock.release()
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('cancelled run created process'))
    with pytest.raises(ValueError,match='CANCELLED'):entry.start(scope)
    assert entry._scope is None and entry._launcher.boundaries._latch.reason=='owned-stop'


def test_actual_concurrent_stop_preserves_original_cleanup_facts(runtime,monkeypatch):
    from xverse.maestro.dispatcher import FiniteDispatcher
    entry,scope,work=runtime;reached=threading.Event();resume=threading.Event()
    original=FiniteDispatcher._statement;results=[];errors=[];held=[]
    def statement(self,kind,step,**kw):
        result=original(self,kind,step,**kw)
        if kind=='step-complete' and step.phase=='start' and not held:
            held.append(True);reached.set()
            assert resume.wait(1.5)
        return result
    monkeypatch.setattr(FiniteDispatcher,'_statement',statement)
    def run():
        try:results.append(entry.start(scope))
        except BaseException as error:errors.append(repr(error))
    thread=threading.Thread(target=run);thread.start()
    try:
        assert reached.wait(2)
        assert entry._lock.locked()
        with pytest.raises(ValueError,match='CONFLICT'):entry.start(scope)
        with pytest.raises(ValueError,match='CONFLICT'):entry.collect('fixture-run')
        assert (work/'source-binding.marker').read_bytes()==b'EXEC\n'
        assert not (work/'sink-binding.marker').exists()
        assert entry.stop('fixture-run',reason='owned-active-stop')==1
        with monkeypatch.context() as patch:
            patch.setattr(entry._driver,'cancel',lambda *a,**kw:pytest.fail('matching active stop repeated cancellation'))
            assert entry.stop('fixture-run',reason='owned-active-stop')==1
    finally:resume.set();thread.join(6)
    assert not thread.is_alive() and not errors and len(results)==1,errors
    result=results[0]
    assert result.closure is not None and result.closure.root_reaped
    assert all(h.process_reaped for h in result.closure.helpers)
    assert all(b.empty and b.released for b in result.closure.boundaries)
    assert not result.execution_succeeded
    assert not result.closure.normal_unit_records_complete
    native=result.closure.native_units
    assert sum(u.issued is True for u in native)==1
    assert all(u.direct_child_reaped is None and u.native_retired is None for u in native if u.issued is False)
    confirmed=all(u.direct_child_reaped is True and u.native_retired is True for u in native if u.issued is True)
    assert result.cleanup_complete is confirmed
    if not confirmed:assert 'ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN' in result.closure.diagnostics
    assert 'ML-CLOSURE-REPORT-INCOMPLETE' in result.closure.diagnostics
    assert not (work/'sink-binding.marker').exists()
