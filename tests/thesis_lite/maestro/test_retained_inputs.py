"""Original caller fields and actual isolated-worker public export; no full coverage claim."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path

import pytest
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse.maestro.evidence import PublicExport, PublicInputError, export_declarations, ANNOTATION_FIELDS
from xverse.maestro.teardown import ReverseTeardown
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_generation_claim import release
from .test_generation_dependents import advance
from .test_generation_worker import prepare as future_prepare
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def prepare(monkeypatch, mode='valid', maximum=1<<20):
    from . import test_launcher
    original=test_launcher.encode_configuration
    retained={}
    def encode(*args,**kwargs):
        declaration=PublicExport('retained-inputs.json',maximum)
        config=original(*args,**kwargs,public_exports=(declaration,))
        data=json.loads(config.private_bytes)
        if mode=='version':data['version']=2
        elif mode=='extra':data['public_exports'][0]['nativeScope']='forbidden'
        elif mode=='empty':data['public_exports']=[]
        elif mode=='bool-limit':data['public_exports'][0]['maximum_bytes']=True
        if mode!='valid':config=replace(config,private_bytes=canonical_bytes(data))
        retained.update(config=config,declaration=declaration)
        return config
    monkeypatch.setattr(test_launcher,'encode_configuration',encode)
    return retained


def read_export(stack,receipt):
    path=stack[3].parent/'argus'/receipt.declaration.relative_path
    data=path.read_bytes()
    entry=receipt.public_entry()
    assert entry['sha256']==hashlib.sha256(data).hexdigest() and entry['bytes']==len(data)
    return json.loads(data)


def retain(stack,receipt,suffix):
    root=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if root:
        body=read_export(stack,receipt)
        (Path(root)/('retained-public-'+str(os.getpid())+'-'+suffix+'.json')).write_text(json.dumps(dict(
            retained=body,index_entry=receipt.public_entry(),
            public_m3=FileEvidenceJournal(stack[3].parent/'m3.jsonl').public_records(),
            argus_events=EvidenceStore.read_run(stack[3].parent/'argus').records(),
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),full_M1_complete=False)))


def test_actual_original_append_fields_export_and_index_without_new_claims(request,monkeypatch):
    saved=prepare(monkeypatch)
    stack=request.getfixturevalue('broker_stack')
    broker,facade,client,work=stack
    assert json.loads(saved['config'].private_bytes)['version']==3
    end=stage_all(stack)
    for unit in broker.owner._prepared.resource_order:
        issuer=broker.issuer(unit)
        assert facade.start(unit,issuer.recipe.descriptor,broker.connection,end).ready
    worker=client.process
    before=FileEvidenceJournal(work.parent/'m3.jsonl').records
    original_attempts=set(client._attempted)
    receipt=client.export_public_inputs(saved['declaration'],deadline(2))
    body=read_export(stack,receipt)
    assert body['publicM3']==list(FileEvidenceJournal(work.parent/'m3.jsonl').public_records())
    assert client.process is worker and client._attempted==original_attempts
    assert FileEvidenceJournal(work.parent/'m3.jsonl').records==before
    actual={e['eventId']:e for e in EvidenceStore.read_run(work.parent/'argus').records()}
    assert len(body['annotations'])==len(actual)
    for event in body['annotations']:
        assert set(event)==ANNOTATION_FIELDS
        assert all(actual[event['eventId']].get(k)==v for k,v in event.items())
        assert 'schemaVersion' not in event and 'runId' not in event
    with monkeypatch.context() as patch:
        patch.setattr(client,'_rpc',lambda *a:pytest.fail('matching repeat must not write'))
        assert client.export_public_inputs(saved['declaration'],deadline(1)) is receipt
    retain(stack,receipt,'normal')
    assert EvidenceStore.read_run(work.parent/'argus').manifest['artifacts']==[]
    client.abort(deadline(1))
    closed=EvidenceStore.read_run(work.parent/'argus')
    assert closed.manifest['artifacts']==[receipt.public_entry()]
    assert not any('ARTIFACT' in d.code for d in closed.diagnostics)


def test_original_open_worker_exports_after_cancel_without_reopening_starts(request,monkeypatch):
    saved=prepare(monkeypatch)
    stack=request.getfixturevalue('broker_stack')
    broker,_,client,work=stack
    stage_all(stack)
    broker.owner.cancel('retained-input-cancelled')
    assert broker.owner.latch.cancelled
    receipt=client.export_public_inputs(saved['declaration'],deadline(1.5))
    body=read_export(stack,receipt)
    assert len(body['annotations'])==4 and not list(work.glob('*.marker'))
    assert not any(r['kind']=='outcome' and r['status']=='running' for r in body['publicM3'])
    with pytest.raises(ValueError):
        client.commit_intent(broker.owner._prepared.resource_order[0],deadline(0.5))


def test_public_export_never_creates_intents_for_never_issued_units(request,monkeypatch):
    saved=prepare(monkeypatch)
    stack=request.getfixturevalue('broker_stack')
    broker,_,client,work=stack
    receipt=client.export_public_inputs(saved['declaration'],deadline(1.5))
    body=read_export(stack,receipt)
    assert body['annotations']==body['publicM3']==[] and not client._claims
    assert all(not issuer._attempted for issuer in broker.issuers)
    assert not list(work.glob('*.marker'))


def test_retained_export_preserves_original_and_successor_generation_sources(request,monkeypatch):
    future_prepare(request,monkeypatch)
    saved=prepare(monkeypatch)
    stack=request.getfixturevalue('broker_stack')
    broker,_,client,_=stack
    end=stage_all(stack)
    for target in broker.owner._prepared.resource_order:
        issuer=broker.issuer(target)
        assert stack[1].start(target,issuer.recipe.descriptor,broker.connection,end).ready
    controller=ReverseTeardown(stack[1],per_unit_seconds=0.8)
    unit=broker.owner._prepared.resource_order[-1]
    release(controller,unit);advance(stack,controller,unit)
    receipt=client.export_public_inputs(saved['declaration'],deadline(2))
    body=read_export(stack,receipt)
    intents=[e for e in body['annotations'] if e['extensions']['xverse.maestro']['unitId']==unit
        and e['extensions']['xverse.maestro']['action']=='intent' and e['producerId']=='maestro.owner7']
    assert {e['extensions']['xverse.maestro']['generation'] for e in intents}=={1,2}
    assert len({e['eventId'] for e in intents})==2
    retain(stack,receipt,'generation')


@pytest.mark.parametrize('mode',['version','extra','empty','bool-limit'])
def test_malformed_sealed_export_rejects_before_writer_or_journal(request,monkeypatch,tmp_path,mode):
    prepare(monkeypatch,mode)
    with pytest.raises(ValueError):request.getfixturevalue('broker_stack')
    assert not (tmp_path/'m3.jsonl').exists() and not (tmp_path/'argus').exists()


@pytest.mark.parametrize('condition',['existing','small','missing-mirror','changed-intent-clock'])
def test_failed_actual_export_never_certifies_a_public_receipt(request,monkeypatch,condition):
    saved=prepare(monkeypatch,maximum=100 if condition=='small' else 1<<20)
    stack=request.getfixturevalue('broker_stack')
    broker,_,client,work=stack
    stage_all(stack)
    target=work.parent/'argus'/'retained-inputs.json'
    if condition=='existing':target.write_bytes(b'existing')
    if condition in ('missing-mirror','changed-intent-clock'):
        reader=EvidenceStore.read_run(work.parent/'argus')
        path=work.parent/'argus'/reader.manifest['eventStream']['path']
        events=[json.loads(line) for line in path.read_bytes().splitlines()]
        if condition=='missing-mirror':events.pop()
        else:events[0]['clocks']['host']['value']+=0.001
        path.write_bytes(b''.join(canonical_bytes(e)+b'\n' for e in events))
    with pytest.raises(ValueError):client.export_public_inputs(saved['declaration'],deadline(1.5))
    assert not client._export_receipts and broker.owner.latch.cancelled
    if condition=='existing':assert target.read_bytes()==b'existing'
    else:assert not target.exists()
    assert not list(work.glob('*.marker'))


def test_malformed_actual_export_ack_rejects_without_publishing_receipt(request,monkeypatch):
    saved=prepare(monkeypatch)
    stack=request.getfixturevalue('broker_stack')
    broker,_,client,work=stack
    original=client._rpc
    def damaged(kind,body,until):
        operation,end,reply=original(kind,body,until)
        if kind=='public-export':reply['m3Count']=True
        return operation,end,reply
    monkeypatch.setattr(client,'_rpc',damaged)
    with pytest.raises(ValueError):client.export_public_inputs(saved['declaration'],deadline(1.5))
    assert (work.parent/'argus'/'retained-inputs.json').exists()
    assert not client._export_receipts and broker.owner.latch.cancelled


def test_undeclared_copied_scope_and_conflicting_export_reject_before_rpc(request,monkeypatch):
    saved=prepare(monkeypatch)
    stack=request.getfixturevalue('broker_stack')
    _,_,client,_=stack
    before=client._sequence
    with pytest.raises(ValueError,match='ORIGINAL'):
        client.export_public_inputs(replace(saved['declaration']),deadline(1))
    assert client._sequence==before and not client.latch.cancelled
    assert client._lock.acquire(False)
    try:
        with pytest.raises(ValueError,match='CONFLICT'):
            client.export_public_inputs(saved['declaration'],deadline(1))
    finally:client._lock.release()
    assert client._sequence==before and not client.latch.cancelled


def test_default_export_absence_preserves_original_v1_configuration_bytes(request,monkeypatch):
    from . import test_launcher
    original=test_launcher.encode_configuration
    def encode(*args,**kwargs):
        first=original(*args,**kwargs)
        explicit=original(*args,**kwargs,public_exports=())
        assert first.private_bytes==explicit.private_bytes and not explicit.public_exports
        assert json.loads(first.private_bytes)['version']==1
        return explicit
    monkeypatch.setattr(test_launcher,'encode_configuration',encode)
    request.getfixturevalue('broker_stack')


def test_export_declarations_reject_unbounded_duplicates_unsafe_or_oversized_values():
    class Poison:
        def __iter__(self):pytest.fail('unadmitted iterator')
    with pytest.raises(PublicInputError):export_declarations(Poison())
    with pytest.raises(PublicInputError):export_declarations([PublicExport('same.json',1)]*2)
    with pytest.raises(PublicInputError):export_declarations([PublicExport('a.json',16<<20),PublicExport('b.json',1)])
    for path in ('../escape','/absolute','events.jsonl','manifest.json','lifecycle-coverage.json','nested/file.json'):
        with pytest.raises(PublicInputError):PublicExport(path,1000)
    with pytest.raises(PublicInputError):PublicExport('safe.json',True)


@pytest.mark.parametrize('data',[b'',b'x'*65537,b'{}',b'{"duplicate":1,"duplicate":2}'])
def test_missing_or_noncanonical_original_retention_cannot_be_substituted(data):
    from types import SimpleNamespace
    from xverse.maestro.evidence import retained_intent
    with pytest.raises(ValueError):retained_intent(SimpleNamespace(public_event_bytes=data,event_id='original'))


def test_default_empty_export_preserves_original_v2_future_configuration_bytes(request,monkeypatch):
    from . import test_launcher
    future_prepare(request,monkeypatch)
    original=test_launcher.encode_configuration
    def encode(*args,**kwargs):
        first=original(*args,**kwargs)
        explicit=original(*args,**kwargs,public_exports=())
        assert first.private_bytes==explicit.private_bytes and not explicit.public_exports
        assert json.loads(first.private_bytes)['version']==2
        return explicit
    monkeypatch.setattr(test_launcher,'encode_configuration',encode)
    request.getfixturevalue('broker_stack')
