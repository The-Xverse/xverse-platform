"""Original runtime facts, not a complete run or scientific experiment."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import signal
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.coverage import CoverageAdmission, admit_coverage, assess_preclosure, canonical, digest
from xverse.maestro.evidence import PublicExport
from xverse.maestro.persistence import PersistenceClient, PersistenceError
from xverse.maestro.teardown import ReverseTeardown
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def configure(monkeypatch, mode='valid'):
    from . import test_launcher
    original = test_launcher.encode_configuration
    saved = {}
    def encode(prepared, result, resources, **kw):
        bindings = (*kw['bindings'], *(c.binding for c in kw.get('future_contexts', ())))
        schedule=kw.get('schedule')
        policies={p.unit_id:(p.cadence_seconds,p.freshness_seconds) for p in schedule.policies} if schedule else {u.unit_id:(.25 if mode=='policy' else .5,2) for u in prepared.units}
        admission = admit_coverage(prepared, result, resources, run_id=kw['run_id'], host_session=kw['session'],
            contexts=[(b.unit_id, b.generation, b.execution_id+('-wrong' if mode=='context' else '')) for b in bindings],
            health_policies=policies,source_digests=[digest(json.loads(schedule.canonical_bytes))] if schedule else (),
            active_start=time.monotonic(), active_end=kw['generation_deadline'].monotonic_seconds-2)
        declaration = PublicExport('retained-inputs.json', 1<<20)
        config = original(prepared, result, resources, **kw, coverage=admission, public_exports=(declaration,))
        body = json.loads(config.private_bytes)
        if mode=='digest': body['coverage']['digest']='sha256:'+'0'*64
        elif mode=='version': body['version']=3
        elif mode=='template':
            body['coverage']['inputs']['templates']=[]
        elif mode=='extra': body['coverage']['privateScope']='forbidden'
        if mode not in ('valid','context','policy'): config=replace(config, private_bytes=canonical(body))
        saved.update(config=config, declaration=declaration)
        return config
    monkeypatch.setattr(test_launcher, 'encode_configuration', encode)
    return saved


def retain(stack, saved, retained, projection, report):
    output=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if output:
        admission=saved['config'].coverage
        (Path(output)/('coverage-producer-public-'+str(os.getpid())+'.json')).write_text(json.dumps(dict(
            admission=json.loads(admission.public_bytes), admission_digest=admission.digest,
            retained=retained, broker=projection, report=report,
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            full_M1_complete=False, scientific_result=False)))


def test_real_validation_flush_precedes_stage_and_reader_resolves_original_correlations(request, monkeypatch):
    saved=configure(monkeypatch)
    stack=request.getfixturevalue('broker_stack')
    broker, facade, client, work=stack
    assert json.loads(saved['config'].private_bytes)['version']==4
    assert 'templates' not in json.loads(saved['config'].private_bytes)['coverage']['inputs']
    assert len(saved['config'].private_bytes)<=65536
    from xverse.maestro.coverage import decode_runtime_coverage
    assert decode_runtime_coverage(json.loads(saved['config'].private_bytes)['coverage']).public_bytes==client.coverage.public_bytes
    assert client.coverage is saved['config'].coverage and client._sequence==1
    root=EvidenceStore.read_run(work.parent/'argus')
    assert len(root.records())==1 and not client._claims and not list(work.glob('*.marker'))
    validation=root.records()[0]
    assert validation['eventId']==client.run_id and validation['ingestionOrdinal']==1
    assert validation['producerId']=='maestro.validation17'
    assert validation['extensions']['xverse.maestro']['sourceRefs'][0]['sha256']==client.coverage.digest
    end=stage_all(stack)
    for unit in client.prepared.resource_order:
        issuer=broker.issuer(unit)
        assert facade.start(unit,issuer.recipe.descriptor,broker.connection,end).ready
    cleanup=ReverseTeardown(facade,per_unit_seconds=.8).run(deadline(3))
    assert cleanup.normal_records_complete and cleanup.unit_cleanup_complete
    projection=broker.public_projection(deadline(.5)).public_data()
    receipt=client.export_public_inputs(saved['declaration'],deadline(2))
    raw=(work.parent/'argus'/receipt.declaration.relative_path).read_bytes()
    retained=json.loads(raw)
    assert retained['annotations'][0]['eventId']==client.run_id
    for row in projection['generations']:
        assert row['releaseAcknowledgedAt']<=row['stopRequestedAt']<=row['stopAcknowledgedAt']<=projection['observedAt']
        issuer=broker.issuer(row['unitId'])
        actual=broker.session.boundaries._entries[issuer._image.admission.descriptor.key].terminal
        assert row['c1TerminationObserved'] is actual.termination_observed
        assert row['directChildReaped'] is True and row['c1Empty'] is True and row['c1Released'] is True
    result=assess_preclosure(client.coverage,expected_admission_digest=client.coverage.digest,
        annotations=retained['annotations'],public_m3=retained['publicM3'],broker=projection,
        artifact_entries=[receipt.public_entry()],artifact_bytes={receipt.declaration.relative_path:raw})
    report=result.report()
    assert next(r for r in report['rows'] if r['obligationId']=='ob.run-validation')['status']=='satisfied'
    assert next(r for r in report['rows'] if r['obligationId']=='ob.input-integrity')['status']=='satisfied'
    assert all(r['status']=='satisfied' for r in report['rows'] if r['obligationId'].endswith(('.stop','.cleanup')))
    assert report['overallStatus']=='incomplete' and report['normalRecordStatus']!='complete'
    for suffix in ('collect','run-terminal'):
        assert next(r for r in report['rows'] if r['obligationId']=='ob.'+suffix)['status']=='missing'
    client.abort(deadline(1))
    reader=EvidenceStore.read_run(work.parent/'argus')
    assert not any('CAUSAL' in d.code for d in reader.diagnostics), reader.diagnostics
    assert reader.manifest['writerState']=='failed'
    retain(stack,saved,retained,projection,report)


@pytest.mark.parametrize('mode',['digest','version','template','extra','context'])
def test_bad_sealed_coverage_rejects_before_journal_writer_or_workload(request,monkeypatch,tmp_path,mode):
    configure(monkeypatch,mode)
    with pytest.raises(ValueError): request.getfixturevalue('broker_stack')
    assert not (tmp_path/'m3.jsonl').exists() and not (tmp_path/'argus').exists()
    assert not list(tmp_path.rglob('*.marker'))


def test_actual_policy_mismatch_cannot_release_workloads(request,monkeypatch,tmp_path):
    configure(monkeypatch,'policy')
    with pytest.raises(ValueError,match='RUNTIME-POLICY'): request.getfixturevalue('broker_stack')
    assert not list(tmp_path.rglob('*.marker'))


@pytest.mark.parametrize('mutation',['digest','context','session','lifecycle','end','template','shape'])
def test_worker_independently_rejects_coverage_before_creating_any_sink(request,monkeypatch,tmp_path,mutation):
    from xverse.maestro import persistence_worker
    from .test_preparation import ROOT
    # Source schemas are separate data files; the real isolated worker uses its
    # installed wheel. Unit lookup uses the same exact frozen schema bytes.
    monkeypatch.setattr(persistence_worker,'files',lambda name:ROOT/'xdl' if name=='xverse_xdl' else pytest.fail('unexpected package'))
    saved=configure(monkeypatch)
    request.getfixturevalue('broker_stack')
    data=json.loads(saved['config'].private_bytes)
    target=tmp_path/'independent-invalid-worker';target.mkdir()
    data.update(journal_path=str(target/'m3.jsonl'),evidence_root=str(target/'argus'))
    body=data['coverage']['inputs']
    if mutation=='digest':data['coverage']['digest']='sha256:'+'0'*64
    elif mutation=='context':body['contexts'][0]['executionId']='foreign-original-context'
    elif mutation=='session':body['hostSession']='foreign-session'
    elif mutation=='lifecycle':body['lifecycleDigest']='sha256:'+'0'*64
    elif mutation=='end':body['end']=data['generation_ns']/1e9+1
    elif mutation=='template':body['templates']=[]
    elif mutation=='shape':data['coverage']['nativeScope']='forbidden'
    if mutation!='digest':
        from xverse.maestro.coverage import _templates
        data['coverage']['digest']=digest(dict(body,templates=_templates(body)))
    with pytest.raises(ValueError):persistence_worker._load(data,lambda:None)
    assert list(target.iterdir())==[]


def test_reserved_run_identity_and_root_event_capacity_reject_purely(request,monkeypatch):
    from types import SimpleNamespace
    from xverse.maestro.coverage import bind_runtime_coverage
    saved=configure(monkeypatch)
    stack=request.getfixturevalue('broker_stack')
    client=stack[2];config=saved['config'];raw=json.loads(config.private_bytes)
    bindings=tuple(SimpleNamespace(**b) for b in raw['bindings'])
    args=dict(run_id=config.run_id,session=config.session,generation_ns=config.generation_ns,bindings=bindings)
    for identity in ('run-opened','run-closed','run-failed'):
        body=json.loads(config.coverage.public_bytes);body['runId']=identity
        changed=CoverageAdmission(canonical(body))
        with pytest.raises(ValueError,match='RUNTIME-IDENTITY'):
            bind_runtime_coverage(changed,changed.digest,client.prepared,config.result,config.resources,**dict(args,run_id=identity))
    policies=tuple(SimpleNamespace(unit_id=u.unit_id,cadence_seconds=.5,freshness_seconds=2) for u in client.prepared.units)
    with pytest.raises(ValueError,match='RUNTIME-CAPACITY'):
        bind_runtime_coverage(config.coverage,config.coverage.digest,client.prepared,config.result,config.resources,
            **args,schedule=SimpleNamespace(policies=policies,required_events=8192,event_limit=8192))
    sequence=stack[0].session._sequence
    with pytest.raises(ValueError,match='BOOT-PERSISTENCE'):
        stack[0].session.persistence(replace(config,private_bytes=b'x'*65537),None,deadline(.5))
    assert stack[0].session._sequence==sequence


def test_actual_shared_schedule_preserves_single_original_validation_and_distinct_tick_records(request,monkeypatch):
    from .test_shared_dispatcher import scheduled,run
    configure(monkeypatch)
    stack,controller,driver=scheduled(request,monkeypatch)
    result=run(driver)
    assert result.execution_succeeded and result.terminal_recorded
    client=stack[2]
    projection=stack[0].public_projection(deadline(.5)).public_data()
    declaration=client._public_exports[0]
    receipt=client.export_public_inputs(declaration,deadline(2))
    raw=(stack[3].parent/'argus'/declaration.relative_path).read_bytes();retained=json.loads(raw)
    validations=[e for e in retained['annotations'] if e['extensions']['xverse.maestro']['action']=='validate'
                 and e['extensions']['xverse.maestro']['scope']=='run']
    assert len(validations)>1 and sum(e['eventId']==client.run_id for e in validations)==1
    report=assess_preclosure(client.coverage,expected_admission_digest=client.coverage.digest,
        annotations=retained['annotations'],public_m3=retained['publicM3'],broker=projection,
        artifact_entries=[receipt.public_entry()],artifact_bytes={declaration.relative_path:raw}).report()
    assert next(r for r in report['rows'] if r['obligationId']=='ob.run-validation')['status']=='satisfied'
    assert report['overallStatus']=='incomplete'


@pytest.mark.parametrize('mode',['boolean','digest','operation','missing','lost'])
def test_actual_validation_init_ack_failure_closes_starts_and_retains_original_cleanup(request,monkeypatch,tmp_path,mode):
    configure(monkeypatch)
    original=PersistenceClient._rpc
    def damaged(self,kind,body,until):
        operation,end,facts=original(self,kind,body,until)
        if kind=='init':
            if mode=='lost': raise PersistenceError('test-only-lost-init-ack')
            if mode=='missing': facts.pop('validation')
            elif mode=='boolean': facts['validation']['ingestion_ordinal']=True
            elif mode=='digest': facts['validation']['admission_digest']='sha256:'+'0'*64
            elif mode=='operation': facts['validation']['operation_id']='ml-'+'0'*32
        return operation,end,facts
    monkeypatch.setattr(PersistenceClient,'_rpc',damaged)
    with pytest.raises(ValueError): request.getfixturevalue('broker_stack')
    assert not list(tmp_path.rglob('*.marker'))
    # Original worker really validated/flushed; loss of its receipt does not erase it.
    records=EvidenceStore.read_run(tmp_path/'argus').records()
    assert records and records[0]['producerId']=='maestro.validation17'


def test_validation_caller_field_mutation_is_not_hidden_by_boolean_integer_alias(request,monkeypatch):
    saved=configure(monkeypatch)
    stack=request.getfixturevalue('broker_stack')
    path=stack[3].parent/'argus'/'events.jsonl'
    records=[json.loads(line) for line in path.read_bytes().splitlines()]
    records[0]['extensions']['xverse.maestro']['generation']=False
    path.write_bytes(b''.join(canonical(e)+b'\n' for e in records))
    with pytest.raises(ValueError): stack[2].export_public_inputs(saved['declaration'],deadline(1))
    assert stack[2].latch.cancelled and not list(stack[3].glob('*.marker'))


@pytest.mark.parametrize('mutation',['copy','bytes'])
def test_original_runtime_admission_pin_rejects_replaced_object_or_bytes_before_rpc(request,monkeypatch,mutation):
    saved=configure(monkeypatch)
    stack=request.getfixturevalue('broker_stack');client=stack[2]
    original=client.coverage;data=original.public_bytes;pinned=client.coverage_digest;sequence=client._sequence
    try:
        if mutation=='copy':client.coverage=replace(original)
        else:
            body=json.loads(data);body['templates'].pop()
            object.__setattr__(original,'public_bytes',canonical(body))
        with pytest.raises(ValueError,match='RUNTIME-REPLACED'):
            client.export_public_inputs(saved['declaration'],deadline(.5))
        assert client._sequence==sequence and client.coverage_digest==pinned and not list(stack[3].glob('*.marker'))
    finally:
        client.coverage=original;object.__setattr__(original,'public_bytes',data)


@pytest.mark.parametrize('original,mutated',[(1,True),(0,False),(1,1.0),(0.0,-0.0),({'nested':[1]}, {'nested':[True]}),([1,2],[1]),({'a':1},{'b':1})])
def test_typed_mirror_comparison_preserves_canonical_json_distinctions(original,mutated):
    from xverse.maestro.lifecycle_evidence import _same_json
    assert _same_json(original,original) and not _same_json(original,mutated)
    assert (_same_json(original,mutated)) == (canonical(original)==canonical(mutated))


def test_real_stop_bracket_repeat_is_identical_and_projection_adds_no_rpc(broker_stack,monkeypatch):
    broker,facade,client,work=broker_stack
    end=stage_all(broker_stack)
    for unit in client.prepared.resource_order:
        issuer=broker.issuer(unit)
        assert facade.start(unit,issuer.recipe.descriptor,broker.connection,end).ready
    unit=client.prepared.resource_order[-1]
    issuer=broker.issuer(unit)
    issuer.stop_owned(issuer._handle,deadline(1))
    bracket=issuer._stop_bracket
    issuer.stop_owned(issuer._handle,deadline(1))
    assert issuer._stop_bracket is bracket
    before=(client._sequence,broker.connection.sequence)
    with monkeypatch.context() as patch:
        patch.setattr(client,'_rpc',lambda *a:pytest.fail('projection storage RPC'))
        patch.setattr(broker.connection,'_exchange',lambda *a,**kw:pytest.fail('projection native RPC'))
        projection=broker.public_projection(deadline(.5)).public_data()
    assert (client._sequence,broker.connection.sequence)==before
    row=next(r for r in projection['generations'] if r['unitId']==unit)
    assert (row['stopRequestedAt'],row['stopAcknowledgedAt'])==bracket
    assert row['directChildReaped'] is True and row['c1Released'] is None
    original=issuer._stop_bracket
    issuer._stop_bracket=(original[0],original[1]+.001)
    try:
        with pytest.raises(ValueError,match='REPLACED'):broker.public_projection(deadline(.5))
    finally:issuer._stop_bracket=original


def test_unacknowledged_stop_exports_open_original_bracket_without_normal_wait(broker_stack):
    broker,facade,client,_=broker_stack
    end=stage_all(broker_stack)
    for unit in client.prepared.resource_order:
        issuer=broker.issuer(unit)
        assert facade.start(unit,issuer.recipe.descriptor,broker.connection,end).ready
    unit=client.prepared.resource_order[-1]
    signal.pidfd_send_signal(broker.connection.child._capability.fileno(),signal.SIGSTOP)
    result=ReverseTeardown(facade,per_unit_seconds=.8).phase(unit,'stop',deadline(1))
    assert result.emergency and result.boundary_released and not result.normal_records_complete
    row=next(r for r in broker.public_projection(deadline(.5)).public_data()['generations'] if r['unitId']==unit)
    assert row['stopRequestedAt'] is not None and row['stopAcknowledgedAt'] is None
    assert row['directChildReaped'] is None
    assert row['c1TerminationObserved'] is True and row['c1Empty'] is True and row['c1Released'] is True
