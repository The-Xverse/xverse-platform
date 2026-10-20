"""Real v6 lazy claims/Stage and complete logical terminal universe, partial full17."""
import hashlib
import json
import os
from pathlib import Path
import signal
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.artifacts import ArtifactDeclaration
from xverse.maestro.collection_plan import admit_collection
from xverse.maestro.coverage import ArtifactExpectation, admit_coverage
from xverse.maestro.dispatcher import FiniteDispatcher
from xverse.maestro.evidence import PublicExport
from xverse.maestro.public_blobs import admit_broker_artifact
from xverse.maestro.time import HostDeadline
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline



@pytest.fixture(autouse=True)
def observe_original_operations(monkeypatch, request):
    from xverse.maestro.persistence import PersistenceClient
    original = PersistenceClient._rpc
    records = []
    def observed(self, kind, body, end, **kw):
        began = time.monotonic(); error = None
        try:
            return original(self, kind, body, end, **kw)
        except Exception as exc:
            error = str(exc) if str(exc).startswith('ML-') else type(exc).__name__
            raise
        finally:
            records.append(dict(kind=kind, action=body.get('kind', body.get('action')), unit=body.get('unit'),
                step=body.get('step'), began=began, ended=time.monotonic(), end=end.monotonic_seconds,
                observed_at=body.get('observed_at'), generation=body.get('generation'),
                diagnostic=error))
    monkeypatch.setattr(PersistenceClient, '_rpc', observed)
    yield
    out = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        target = Path(out); target.mkdir(parents=True, exist_ok=True)
        (target/('lazy-operations-'+request.node.name.replace('[','-').replace(']','')+'.json')).write_text(
            json.dumps(dict(operations=records,observational_only=True,original_assertions_and_bounds_preserved=True),indent=2)+'\n')


def dispatch_first_start(driver):
    driver._active_end=time.monotonic()+3
    driver._send('begin',deadline(.5))
    driver._send('tick',deadline(.5),index=1,previous=0)
    driver._index=1
    unit=driver.prepared.resource_order[0]
    prepare=next(s for s in driver.prepared.steps if s.unit_id==unit and s.phase=='prepare')
    driver._statement('step-dispatch',prepare);driver._statement('step-complete',prepare)
    start=next(s for s in driver.prepared.steps if s.unit_id==unit and s.phase=='start')
    driver._statement('step-dispatch',start)
    return unit


def scheduled(request, monkeypatch, *, implicit=False, optional=False):
    from . import test_launcher, test_shared_dispatcher
    encode = test_launcher.encode_configuration
    def configuration(prepared, result, resources, **kw):
        schedule = kw['schedule']; root = Path(kw['journal_path']).parent / 'work'; st = root.stat()
        declarations = tuple(ArtifactDeclaration(u.unit_id, 1, u.binding_id+'.marker',
                             'outputs/'+u.binding_id+'.txt', required=not optional) for u in prepared.units)
        coverage = admit_coverage(prepared, result, resources, run_id=kw['run_id'], host_session=kw['session'],
            contexts=[(b.unit_id,b.generation,b.execution_id) for b in kw['bindings']],
            health_policies={p.unit_id:(p.cadence_seconds,p.freshness_seconds) for p in schedule.policies},
            active_start=time.monotonic(), active_end=time.monotonic()+schedule.active_seconds,
            source_digests=('sha256:'+hashlib.sha256(schedule.canonical_bytes).hexdigest(),),
            artifacts=[*(ArtifactExpectation(d.destination, d.required, 32, d.unit_id, 1) for d in declarations),
                       ArtifactExpectation('collection-result.json',maximum_bytes=16384)])
        collection = admit_collection(coverage, expected_digest=coverage.digest, source_root=str(root),
            source_identity=(st.st_dev,st.st_ino), declarations=declarations, metadata_path='collection-result.json',
            operation_seconds=.5, per_unit_teardown_seconds=1, collection_seconds=2, terminal_seconds=2, drain_seconds=2)
        return encode(prepared, result, resources, **kw, coverage=coverage, collection=collection,
            broker_artifact=admit_broker_artifact(coverage, expected_digest=coverage.digest),
            public_exports=(PublicExport('retained-inputs.json',1<<20),))
    monkeypatch.setattr(test_launcher,'encode_configuration',configuration)
    monkeypatch.setattr(test_shared_dispatcher,'stage_all',lambda stack:None)
    return test_shared_dispatcher.scheduled(request,monkeypatch,implicit=implicit)


def run(driver):
    ad = driver.client.coverage.data(driver.client.coverage_digest)
    active = HostDeadline(driver.owner.session,min(ad['end']-.01,time.monotonic()+driver.plan.active_seconds-.05))
    plan = driver.client.collection
    terminal = HostDeadline(driver.owner.session,active.monotonic_seconds+driver.plan.terminal_reserve_seconds
                            +plan.collection_seconds+plan.terminal_seconds+.01)
    return driver.run(active,terminal)


def events(stack):
    return EvidenceStore.read_run(stack[3].parent/'argus').records()


def payload(event):
    return event.get('extensions',{}).get('xverse.maestro',{})


def retain(stack, result, case):
    broker,_,client,work=stack
    client.abort(deadline(.8))
    reader=EvidenceStore.read_run(work.parent/'argus')
    assert reader.manifest['writerState']==('closed' if result.execution_succeeded else 'failed')
    assert not any('CAUSAL' in d.code or 'ARTIFACT' in d.code for d in reader.diagnostics)
    out=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if out:
        retained=client._collection_outcome[2].public_data() if client._collection_outcome else None
        (Path(out)/('lazy-dispatch-'+work.parent.name+'.json')).write_text(json.dumps(dict(
            case=case,execution_succeeded=result.execution_succeeded,terminal_recorded=result.terminal_recorded,
            diagnostic=result.diagnostic,collection=retained,
            broker=broker.public_projection(deadline(.5)).public_data(),
            original_fixture=str(work.parent),public_m3=FileEvidenceJournal(work.parent/'m3.jsonl').public_records(),
            argus_events=reader.records(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            full_lifecycle_complete=False,full_M1_complete=False,scientific_result=False),indent=2)+'\n')


def test_actual_lazy_nominal_stages_only_at_eligible_start_then_collects_before_terminal(request,monkeypatch):
    stack,controller,driver=scheduled(request,monkeypatch)
    broker,view,client,work=stack
    assert driver._lazy and not view._bindings and not broker.owner._claims and not client._attempted
    assert not FileEvidenceJournal(work.parent/'m3.jsonl').records
    checkpoints=[]; original=broker.owner.commit_intent
    def commit(unit,end):
        earlier=events(stack)
        checkpoints.append((unit,earlier))
        assert any(payload(e).get('stepId')=='start-'+('source' if 'source-instance' in unit else 'sink')
                   and payload(e)['action']=='validate' and payload(e)['generation']==0 for e in earlier)
        assert broker.issuer(unit)._handle is None and unit not in broker.owner._claims
        return original(unit,end)
    monkeypatch.setattr(broker.owner,'commit_intent',commit)
    result=run(driver)
    assert result.execution_succeeded and result.terminal_recorded,result.diagnostic
    assert result.collection is client._collection_outcome[2] and result.collection.public_data()['collectionComplete']
    assert len(checkpoints)==2 and len(view._bindings)==2
    rows=events(stack); collect=next(e for e in rows if payload(e).get('action')=='collect')
    terminal=[e for e in rows if payload(e).get('action')=='run-terminal'
              or payload(e).get('scope')=='unit' and payload(e).get('action')=='disposition']
    assert len(terminal)==3 and all(e['ingestionOrdinal']>collect['ingestionOrdinal'] for e in terminal)
    prepared=[e for e in rows if payload(e).get('stepId','').startswith('prepare-')]
    assert len(prepared)==6 and all(payload(e)['generation']==0 for e in prepared)
    assert not any(r.action_id in {a.action_id for u in client.prepared.units for a in u.plan.actions if a.phase=='prepare'}
                   for r in FileEvidenceJournal(work.parent/'m3.jsonl').records)
    for unit in client.prepared.units:
        assert (work.parent/'argus'/'outputs'/(unit.binding_id+'.txt')).read_bytes()==b'EXEC\n'
    assert driver.run(*driver._scope) is result
    assert controller._sequence==10+result.lease_renewals//2
    retain(stack,result,'nominal')


def test_actual_controller_stall_keeps_never_claimed_units_at_generation_zero(request,monkeypatch):
    stack,controller,driver=scheduled(request,monkeypatch)
    signal.pidfd_send_signal(controller.process._capability.fileno(),signal.SIGSTOP)
    result=run(driver)
    assert not result.execution_succeeded and result.terminal_recorded,result.diagnostic
    assert not stack[0].owner._attempted and not stack[0].owner._claims
    assert not stack[1]._bindings and not FileEvidenceJournal(stack[3].parent/'m3.jsonl').records
    assert not list(stack[3].glob('*.marker'))
    dispositions=[payload(e) for e in events(stack) if payload(e).get('action')=='disposition']
    assert len(dispositions)==13 and all(p['generation']==0 for p in dispositions)
    units=[p for p in dispositions if p['scope']=='unit'];assert len(units)==2
    assert all(p['disposition']=='blocked' for p in units)
    assert result.collection and not result.collection.public_data()['collectionComplete']
    projection=stack[0].public_projection(deadline(.5)).public_data()
    assert all(r['stageAttempted'] is False and r['issued'] is False for r in projection['generations'])
    retain(stack,result,'controller-stall')


@pytest.mark.parametrize('bad',['foreign-gate','preclaimed','prebound'])
def test_lazy_constructor_rejects_foreign_authority_and_eager_initial_work(request,monkeypatch,bad):
    stack,_,driver=scheduled(request,monkeypatch);broker=stack[0]
    gates=tuple((u.unit_id,broker.connection) for u in broker.owner._prepared.units)
    if bad=='foreign-gate':
        gates=((gates[0][0],object()),*gates[1:])
    else:
        unit=dispatch_first_start(driver)
        broker.owner.commit_intent(unit,deadline(2))
        if bad=='prebound':
            handle=broker.issuer(unit).stage(deadline(1));stack[1].bind(broker.issuer(unit),handle)
    with pytest.raises(ValueError):
        FiniteDispatcher(stack[1],broker.session,gates=gates)


@pytest.mark.parametrize('kind',['step-complete','step-dispatch'])
def test_actual_worker_rejects_handle_free_productive_completion_or_observe(request,monkeypatch,kind):
    stack,_,driver=scheduled(request,monkeypatch)
    driver._send('begin',deadline(.5));tick=driver._send('tick',deadline(.5),index=1,previous=0)
    step=next(s for s in driver.prepared.steps if s.phase==('start' if kind=='step-complete' else 'observe'))
    with pytest.raises(ValueError):
        driver.client._rpc('schedule',dict(kind=kind,step=step.step_id,index=1,tick=tick['tick'],
                                          observed_at=time.monotonic(),handle=None),deadline(.5))
    assert not stack[0].owner._claims and not stack[1]._bindings and not list(stack[3].glob('*.marker'))


def test_actual_original_worker_rejects_start_claim_before_logical_dispatch(request,monkeypatch):
    stack,_,driver=scheduled(request,monkeypatch)
    unit=stack[0].owner._prepared.units[0].unit_id
    with pytest.raises(ValueError):
        stack[0].owner.commit_intent(unit,deadline(.5))
    assert not FileEvidenceJournal(stack[3].parent/'m3.jsonl').records
    assert not stack[0].owner._claims and not stack[1]._bindings
    assert unit in stack[0].owner._attempted and not list(stack[3].glob('*.marker'))


@pytest.mark.parametrize('fault',['commit-ack','stage-ack'])
def test_actual_unknown_attempt_cannot_become_never_claimed_or_productive_success(request,monkeypatch,fault):
    from xverse.maestro.affa_protocol import AuthorityKind as K
    stack,_,driver=scheduled(request,monkeypatch);broker,view,client,work=stack
    seen=[]
    if fault=='commit-ack':
        original=client._rpc
        def lost(kind,*args,**kw):
            reply=original(kind,*args,**kw)
            if kind=='commit':
                seen.append(reply);raise ValueError('ML-TEST-COMMIT-ACK-LOST')
            return reply
        monkeypatch.setattr(client,'_rpc',lost)
    else:
        original=broker.connection._exchange
        def lost(request,*args,**kw):
            reply=original(request,*args,**kw)
            if request.kind is K.STAGE:
                seen.append(reply);raise ValueError('ML-TEST-STAGE-ACK-LOST')
            return reply
        monkeypatch.setattr(broker.connection,'_exchange',lost)
    result=run(driver)
    assert len(seen)==1 and not result.execution_succeeded
    unit=broker.owner._prepared.resource_order[0]
    assert unit in broker.owner._attempted and not list(work.glob('*.marker'))
    assert not any(payload(e).get('scope')=='unit' and payload(e).get('action')=='disposition'
                   and payload(e).get('unitId')==unit and payload(e)['generation']==0 for e in events(stack))
    assert any(r.kind=='intent' and r.permit_nonce is not None for r in FileEvidenceJournal(work.parent/'m3.jsonl').records)
    assert broker.issuer(unit)._handle is None
    if fault=='stage-ack':
        assert broker.issuer(unit)._attempted
        row=next(r for r in broker.public_projection(deadline(.5)).public_data()['generations'] if r['unitId']==unit)
        assert row['issued'] is None and row['stageAttempted'] is True
    else:
        assert not broker.issuer(unit)._attempted and unit not in broker.owner._claims


def test_actual_worker_terminal_universe_includes_unit_without_a_claim(request,monkeypatch):
    stack,_,driver=scheduled(request,monkeypatch);client=driver.client
    driver._send('begin',deadline(.5))
    for step in driver.prepared.steps:
        client._rpc('schedule',dict(kind='step-disposition',step=step.step_id,disposition='blocked',cause='external',
                                   observed_at=time.monotonic()),deadline(.5))
    unit=driver.prepared.units[0].unit_id
    client._rpc('schedule',dict(kind='unit-disposition',unit=unit,disposition='blocked',cause='external',
                               observed_at=time.monotonic()),deadline(.5))
    with pytest.raises(ValueError):
        client._rpc('schedule',dict(kind='run-terminal',outcome='failed',cause='external',
                                   observed_at=time.monotonic()),deadline(.5))
    rows=events(stack)
    assert not any(payload(e).get('action')=='run-terminal' for e in rows)
    assert len([e for e in rows if payload(e).get('scope')=='unit' and payload(e).get('action')=='disposition'])==1
    assert not stack[0].owner._claims and not stack[1]._bindings


def test_actual_worker_rejects_synthetic_handle_without_original_issuance(request,monkeypatch):
    from dataclasses import asdict
    from xverse_xdl.lifecycle import OwnedResourceHandle
    stack,_,driver=scheduled(request,monkeypatch);unit=dispatch_first_start(driver)
    stack[0].owner.commit_intent(unit,deadline(1))
    claim=stack[0].owner._claims[unit].receipt
    target=next(u for u in driver.prepared.units if u.unit_id==unit)
    fake=OwnedResourceHandle('0'*64,driver.client._claim_execution_id(claim),
        next(a.action_id for a in target.plan.actions if a.phase=='start'),target.provider.provider_id,
        'process','maestro-boundary:'+'0'*64)
    start=next(s for s in driver.prepared.steps if s.unit_id==unit and s.phase=='start')
    with pytest.raises(ValueError):
        driver.client._rpc('schedule',dict(kind='step-complete',step=start.step_id,index=1,tick=0,
                            observed_at=time.monotonic(),handle=asdict(fake)),deadline(.5))
    assert not stack[0].issuer(unit)._attempted and not stack[1]._bindings
    assert not list(stack[3].glob('*.marker'))


def test_actual_implicit_normal_teardown_occurs_after_original_native_cancel(request,monkeypatch):
    stack,_,driver=scheduled(request,monkeypatch,implicit=True);broker=stack[0]
    cancel=broker.cancel;fenced=[]
    def observed(reason='run-cancel',**kw):
        reply=cancel(reason,**kw)
        if reason=='dispatcher-terminal-fence':
            assert reply.native_epoch_confirmed;fenced.append(time.monotonic())
        return reply
    monkeypatch.setattr(broker,'cancel',observed)
    result=run(driver)
    assert result.execution_succeeded and result.terminal_recorded,result.diagnostic
    assert len(fenced)==1 and result.cleanup.normal_records_complete and result.cleanup.unit_cleanup_complete
    normal=[r for r in FileEvidenceJournal(stack[3].parent/'m3.jsonl').records if 'teardown' in r.details]
    assert len(normal)==8 and all(r.details['teardown']['observed_at']>=fenced[0] for r in normal)
    assert result.collection.public_data()['collectionComplete']
    assert broker.owner.latch.cancelled and broker.session._terminal
    retain(stack,result,'nominal')
