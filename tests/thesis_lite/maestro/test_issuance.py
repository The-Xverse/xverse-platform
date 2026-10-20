"""Actual native issuance persistence and its pre-Release authority boundary."""
import copy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path

import pytest
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse.maestro.issuance_evidence import IssuanceStatement
from xverse.maestro.prbc import BoundaryDescriptor
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_generation_claim import ready, release
from .test_generation_dependents import advance
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def projection(stack, suffix):
    directory = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if directory:
        work=stack[3]
        (Path(directory)/('issuance-public-'+str(os.getpid())+'-'+suffix+'.json')).write_text(json.dumps(dict(
            public_m3=FileEvidenceJournal(work.parent/'m3.jsonl').public_records(),
            argus_events=EvidenceStore.read_run(work.parent/'argus').records(),
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),full_M1_complete=False)))


def test_actual_frozen_issuance_precedes_start_and_real_ready_causation(broker_stack):
    broker,facade,client,work=broker_stack
    end=stage_all(broker_stack)
    records=FileEvidenceJournal(work.parent/'m3.jsonl').public_records()
    assert not list(work.glob('*.marker'))
    issued=[r for r in records if r['kind']=='observation' and r['status']=='staged']
    assert len(issued)==2 and not any(r['kind']=='outcome' and r['status']=='running' for r in records)
    events=EvidenceStore.read_run(work.parent/'argus').records()
    public_issued=[e for e in events if e.get('extensions',{}).get('xverse.maestro',{}).get('action')=='issued']
    assert len(public_issued)==2
    for issuer in broker.issuers:
        receipt=client._issued_receipts[issuer.unit_id,1]
        assert issuer._issuance_proof[1] is receipt
        assert broker.session.boundaries.record(issuer.recipe.descriptor).state=='frozen'
        event=next(e for e in public_issued if e['eventId']==receipt.event_id)
        source=next(r for r in issued if r['sequence']==receipt.m3_sequence)
        ref=event['extensions']['xverse.maestro']['sourceRefs'][0]
        assert ref['sha256']=='sha256:'+hashlib.sha256(canonical_bytes(source)).hexdigest()
        assert source['handleId']=='withheld' and source['handleResourceIdentity']=='withheld'
        assert source['permitNonce'] is None
        assert facade.start(issuer.unit_id,issuer.recipe.descriptor,broker.connection,end).ready
    events=EvidenceStore.read_run(work.parent/'argus').records()
    for issuer in broker.issuers:
        started=next(e for e in events if e.get('extensions',{}).get('xverse.maestro',{}).get('unitId')==issuer.unit_id
            and e['extensions']['xverse.maestro']['action']=='started')
        assert started['causationId']==client._issued_receipts[issuer.unit_id,1].event_id
    projection(broker_stack,'normal')


def test_missing_issued_mirror_prevents_release_and_keeps_original_cleanup(broker_stack):
    broker,facade,client,work=broker_stack
    end=stage_all(broker_stack)
    reader=EvidenceStore.read_run(work.parent/'argus')
    stream=work.parent/'argus'/reader.manifest['eventStream']['path']
    lines=stream.read_bytes().splitlines(keepends=True)
    stream.write_bytes(b''.join(line for line in lines if json.loads(line).get('extensions',{}).get('xverse.maestro',{}).get('action')!='issued'))
    unit=broker.owner._prepared.resource_order[0]
    issuer=broker.issuer(unit)
    with pytest.raises(ValueError):
        facade.start(unit,issuer.recipe.descriptor,broker.connection,end)
    assert not list(work.glob('*.marker')) and broker.owner.latch.cancelled
    assert issuer._handle is not None  # Physical original issuance stays available for cleanup.


def test_foreign_or_replayed_statement_cannot_create_an_issuance_record(broker_stack):
    broker,_,client,work=broker_stack
    stage_all(broker_stack)
    issuer=broker.issuers[0]
    statement=IssuanceStatement(issuer,broker.owner._claims[issuer.unit_id].receipt,
        issuer._handle,issuer._issuance_proof[0],0.0,0)
    before=FileEvidenceJournal(work.parent/'m3.jsonl').records
    with pytest.raises(ValueError,match='ORIGINAL'):
        client.record_issued(issuer,statement,deadline(0.5))
    with pytest.raises(TypeError):
        copy.copy(statement)
    with pytest.raises(TypeError):
        copy.copy(issuer._issuance_proof[1])
    assert FileEvidenceJournal(work.parent/'m3.jsonl').records==before
    assert not broker.owner.latch.cancelled


def test_actual_new_generation_has_distinct_durable_issuance_and_retained_old_source(request,monkeypatch):
    stack,controller,unit,_=ready(request,monkeypatch)
    broker,facade,client,work=stack
    old=client._issued_receipts[unit,1]
    release(controller,unit)
    advance(stack,controller,unit)
    fresh=client._issued_receipts[unit,2]
    assert fresh is not old and fresh.event_id!=old.event_id and fresh.m3_sequence>old.m3_sequence
    assert client._issued_receipts[unit,1] is old
    records=FileEvidenceJournal(work.parent/'m3.jsonl').public_records()
    actual=[r for r in records if r['status']=='staged' and r['details']['maestroUnitId']==unit]
    assert {r['details']['generation'] for r in actual}=={1,2}
    assert facade.check_unit_health(unit,deadline(0.5)).ready
    projection(stack,'generation')


@pytest.mark.parametrize('mutation',['ordinal-bool','extra-record'])
def test_malformed_actual_issued_ack_never_publishes_a_receipt(broker_stack,monkeypatch,mutation):
    broker,_,client,work=broker_stack
    original=client._rpc
    def damaged(kind,body,until):
        operation,end,reply=original(kind,body,until)
        if kind=='issued':
            reply=json.loads(json.dumps(reply))
            if mutation=='ordinal-bool':
                reply['event']['ingestionOrdinal']=True
            else:
                reply['record']['nativeTicket']='not-a-public-source-field'
        return operation,end,reply
    monkeypatch.setattr(client,'_rpc',damaged)
    with pytest.raises(ValueError):
        stage_all(broker_stack)
    assert not client._issued_receipts and not list(work.glob('*.marker'))
    assert broker.owner.latch.cancelled
