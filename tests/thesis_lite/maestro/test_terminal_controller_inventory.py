"""Original v6 terminal inventory: retired/current controllers and unused future contexts."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import signal
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.artifacts import ArtifactDeclaration
from xverse.maestro.collection_plan import admit_collection
from xverse.maestro.coverage import ArtifactExpectation,admit_coverage,canonical
from xverse.maestro.evidence import PublicExport
from xverse.maestro.persistence import PersistenceClient
from xverse.maestro.public_blobs import admit_broker_artifact
from xverse.maestro.run_broker import RunBroker
from xverse.maestro.run_closure import RunClosure
from xverse.maestro.runtime_verification import runtime_admission_digest
from xverse.maestro.time import HostDeadline
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_generation_worker import successor
from .test_terminal_runtime import run,verify
from .test_lazy_dispatcher import observe_original_operations as observe_original_operations
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries,deadline


def scheduled(request,monkeypatch,*,restarts=False,restart_leaf_artifact=False,transitive=False,restart_artifact_names=(),
              controller_recovery=False):
    from . import test_launcher,test_shared_dispatcher
    if transitive:
        from .test_generation_dependents import chain
        chain(monkeypatch)
    encode=test_launcher.encode_configuration
    def configuration(prepared,result,resources,**kw):
        schedule=kw['schedule'];root=Path(kw['journal_path']).parent/'work';st=root.stat()
        futures=tuple(successor(b,a,2) for b,a in zip(kw['bindings'],kw['approvals']))
        contexts=(*kw['bindings'],*(c.binding for c in futures))
        outputs=tuple(ArtifactDeclaration(u.unit_id,2 if (restart_leaf_artifact and u.unit_id==prepared.resource_order[-1]
            or u.unit_id.rsplit('/',1)[-1] in restart_artifact_names) else 1,
            u.binding_id+'.marker','outputs/'+u.binding_id+'.txt') for u in prepared.units)
        coverage=admit_coverage(prepared,result,resources,run_id=kw['run_id'],host_session=kw['session'],
            contexts=[(b.unit_id,b.generation,b.execution_id) for b in contexts],
            health_policies={p.unit_id:(p.cadence_seconds,p.freshness_seconds) for p in schedule.policies},
            active_start=time.monotonic(),active_end=time.monotonic()+schedule.active_seconds,
            source_digests=('sha256:'+hashlib.sha256(schedule.canonical_bytes).hexdigest(),),
            artifacts=[*(ArtifactExpectation(d.destination,True,32,d.unit_id,d.generation) for d in outputs),
                       ArtifactExpectation('collection-result.json',maximum_bytes=16384)])
        collection=admit_collection(coverage,expected_digest=coverage.digest,source_root=str(root),
            source_identity=(st.st_dev,st.st_ino),declarations=outputs,metadata_path='collection-result.json',
            operation_seconds=.5,per_unit_teardown_seconds=1,collection_seconds=2,terminal_seconds=2,drain_seconds=2)
        return encode(prepared,result,resources,**kw,future_contexts=futures,coverage=coverage,collection=collection,
            broker_artifact=admit_broker_artifact(coverage,expected_digest=coverage.digest),
            public_exports=(PublicExport('retained-inputs.json',1<<20),))
    monkeypatch.setattr(test_launcher,'encode_configuration',configuration)
    monkeypatch.setattr(test_shared_dispatcher,'stage_all',lambda stack:None)
    if restarts or controller_recovery:
        dispatcher=test_shared_dispatcher.FiniteDispatcher
        monkeypatch.setattr(test_shared_dispatcher,'FiniteDispatcher',
            lambda *a,**kw:dispatcher(*a,**kw,allow_restarts=restarts,allow_controller_recovery=controller_recovery))
    admit=RunBroker.admit
    # The shared schedule fixture asks this adapter for one session. The actual
    # original admission reserves two before native authority/config construction.
    monkeypatch.setattr(RunBroker,'admit',classmethod(
        lambda cls,*a,**kw:admit(*a,**dict(kw,controller_sessions=2))))
    return test_shared_dispatcher.scheduled(request,monkeypatch,
        restart_operation_seconds=2.0 if transitive and restarts else 1.0 if restarts else None,transitive=transitive,
        recovery_operation_seconds=3.0 if controller_recovery else None)


@pytest.mark.parametrize('mode',['successor-live','successor-dead'])
def test_original_terminal_report_keeps_retired_current_controllers_and_future_universe(request,monkeypatch,mode):
    stack,old,driver=scheduled(request,monkeypatch);broker,facade,client,work=stack
    ad=client.coverage.data(client.coverage_digest);current=[];transitions=[];closed=None;result=None
    assert len(client._future_contexts)==len(ad['units'])==2 and len(ad['contexts'])==4
    pins=dict(original_admission=json.loads(client.coverage.public_bytes),admission_digest=client.coverage_digest,
        original_collection=json.loads(client.collection.canonical_bytes),generation_ns=client.generation_ns,
        runtime_digest=runtime_admission_digest(client.coverage,client.collection,client.generation_ns),
        original_fixture=str(work.parent),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    output=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        target=Path(output);target.mkdir(parents=True,exist_ok=True)
        with (target/('controller-inventory-inputs-'+mode+'.json')).open('x') as f:json.dump(pins,f,indent=2);f.write('\n')
    cleanup=driver._cleanup
    def replace_after_productive_steps():
        assert len(driver._outcomes)==len(driver.prepared.steps)==10
        assert all(s.disposition=='completed' for s in driver._outcomes.values())
        def end():return HostDeadline(client.session,min(driver._work_end,broker.session._lease/1e9,time.monotonic()+.5))
        retired=old.retire(end(),terminate=True)
        assert retired.original_child_dead and retired.original_child_reaped and retired.own_boundary_released
        fresh=broker.admit_controller('terminal-successor',end());current.append(fresh)
        assert broker._current_controller is fresh and fresh.session_id!=old.session_id
        # Terminal inventory admission is not recovery and grants no productive
        # access. The original dispatcher still retains its original controller.
        with pytest.raises(ValueError,match='NOT-RECONCILED'):fresh._start_access()
        assert driver._controller is old and driver.facade is facade
        transitions.append(dict(old_session=old.session_id,new_session=fresh.session_id,
            old_retirement=asdict(retired),old_slot=old.process._slot,new_slot=fresh.process._slot,
            successor_productive_access_rejected=True,observed_at=time.monotonic()))
        return cleanup()
    monkeypatch.setattr(driver,'_cleanup',replace_after_productive_steps)
    finish=PersistenceClient.finish_run
    def terminal(self,owner,end):
        if self is client and mode=='successor-dead':
            fresh=current[0];fd=fresh.process._capability.fileno()
            signal.pidfd_send_signal(fd,signal.SIGKILL)
            until=min(end.monotonic_seconds,time.monotonic()+.1);observed=None
            while time.monotonic()<until:
                observed=os.waitid(os.P_PIDFD,fd,os.WEXITED|os.WNOHANG|os.WNOWAIT)
                if observed is not None:break
                select.select([],[],[],.001)
            assert observed is not None and observed.si_code==os.CLD_KILLED and observed.si_status==signal.SIGKILL
            transitions[0]['successor_death_observed_without_reap']=True
        return finish(self,owner,end)
    monkeypatch.setattr(PersistenceClient,'finish_run',terminal)
    no_replay=False;counterexamples=[]
    try:
        result=run(driver)
        assert len(transitions)==len(current)==1
        assert result.execution_succeeded and result.terminal_recorded,result.diagnostic
        facts=result.terminal.public_data();assert facts['diagnostic'] is None,facts
        assert facts['report']['eligible'] and facts['writer']['evidence_complete'],facts
        checked=verify(client,work.parent/'argus');assert checked.complete,checked
        report=checked.lifecycle.coverage.report();future=[r for r in report['rows'] if r['generation']==2]
        assert future and {r['unitId'] for r in future}=={c.binding.unit_id for c in client._future_contexts}
        assert all(r['applicable'] is False and r['status']=='not-applicable' for r in future)
        records=FileEvidenceJournal(work.parent/'m3.jsonl').records
        assert {r.details['generation'] for r in records}=={1}
        journal=FileEvidenceJournal(work.parent/'m3.jsonl')
        assert all(not journal.permit_consumed(c.binding.permit.permit_id,c.binding.permit.nonce) for c in client._future_contexts)
        raw=(work.parent/'argus/manifest.json').read_bytes();before=client._sequence
        with monkeypatch.context() as patch:
            patch.setattr(PersistenceClient,'_rpc',lambda *a,**k:pytest.fail('writer replay after original closed result'))
            closed=RunClosure(broker.session,dispatcher=driver).close(deadline(6))
        no_replay=True
        assert closed.cleanup_complete and closed.root_reaped and closed.normal_unit_records_complete,closed
        assert len(closed.helpers)==4 and sum(h.role==5 for h in closed.helpers)==2
        assert all(h.process_reaped for h in closed.helpers) and all(b.empty and b.released for b in closed.boundaries)
        slots={h.slot for h in closed.helpers if h.role==5}
        assert slots=={old.process._slot,current[0].process._slot}
        assert closed.terminal_reports==(result.terminal,) and not closed.writers and not closed.diagnostics
        assert not closed.lifecycle_complete and not closed.ready_for_execution
        assert client._sequence==before and (work.parent/'argus/manifest.json').read_bytes()==raw
        original_root=work.parent/'argus'
        original_bytes={str(p.relative_to(original_root)):hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in original_root.rglob('*') if p.is_file()}
        for fault in ('drop-future-context','drop-future-report-rows'):
            copied=work.parent/('forged-'+fault);shutil.copytree(original_root,copied)
            path=ad['brokerPath'] if fault=='drop-future-context' else ad['reportPath']
            document=json.loads((copied/path).read_bytes())
            if fault=='drop-future-context':
                assert len(document['futureContexts'])==2
                document['futureContexts']=document['futureContexts'][1:]
            else:
                assert any(row['generation']==2 for row in document['rows'])
                document['rows']=[row for row in document['rows'] if row['generation']!=2]
            data=canonical(document);(copied/path).write_bytes(data)
            forged_manifest=json.loads((copied/'manifest.json').read_bytes())
            entries=[entry for entry in forged_manifest['artifacts'] if entry['path']==path];assert len(entries)==1
            entries[0].update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            (copied/'manifest.json').write_bytes(canonical(forged_manifest))
            generic=EvidenceStore.read_run(copied)
            assert generic.manifest['writerState']=='closed'
            assert not any('ARTIFACT' in d.code for d in generic.diagnostics)
            rejected=verify(client,copied);assert not rejected.complete
            counterexamples.append(dict(fault=fault,root=str(copied),
                changed_artifact=path,artifact_bytes=len(data),artifact_sha256=hashlib.sha256(data).hexdigest(),
                manifest_sha256=hashlib.sha256((copied/'manifest.json').read_bytes()).hexdigest(),
                original_external_pins_unchanged=True,copied_index_hashes_updated=True,
                diagnostics=list(rejected.diagnostics),
                normal_status=rejected.lifecycle.coverage.report()['normalRecordStatus']))
            assert original_bytes=={str(p.relative_to(original_root)):hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in original_root.rglob('*') if p.is_file()}
    finally:
        if output:
            closure=asdict(closed) if closed is not None else None
            if closure is not None:closure['terminal_reports']=[r.public_data() for r in closed.terminal_reports]
            reader=EvidenceStore.read_run(work.parent/'argus')
            row=dict(mode=mode,transitions=transitions,closure=closure,
                receipt=result.terminal.public_data() if result and result.terminal else None,
                diagnostic=result.diagnostic if result else None,execution_succeeded=result.execution_succeeded if result else None,
                manifest=reader.manifest,manifest_sha256=hashlib.sha256((work.parent/'argus/manifest.json').read_bytes()).hexdigest(),
                argus_events=reader.records(),public_m3=list(FileEvidenceJournal(work.parent/'m3.jsonl').public_records()),
                original_fixture=str(work.parent),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                no_writer_rpc_replay=no_replay,actual_generation2_issued=False,productive_controller_recovery=False,
                offline_counterexamples=counterexamples,
                original_bounds_preserved=True,full_TR06_complete=False,full_M1_complete=False,scientific_result=False)
            with (target/('controller-inventory-'+mode+'.json')).open('x') as f:json.dump(row,f,indent=2);f.write('\n')
