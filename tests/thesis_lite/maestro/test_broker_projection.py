"""Actual original broker facts; public projections never act as authority."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import signal

import pytest
from xverse.maestro.time import HostDeadline
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_generation_claim import ready,release
from .test_generation_dependents import advance
from .test_generation_worker import prepare
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def retain(stack,projection,suffix):
    root=os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if root:
        (Path(root)/('broker-projection-public-'+str(os.getpid())+'-'+suffix+'.json')).write_text(json.dumps(dict(
            projection=projection.public_data(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            full_M1_complete=False)))


def test_original_full_never_issued_and_future_inventory_precedes_any_start(request,monkeypatch):
    prepare(request,monkeypatch)
    stack=request.getfixturevalue('broker_stack')
    broker,_,client,work=stack
    projection=broker.public_projection(deadline(0.5))
    body=projection.public_data()
    assert {u['unitId'] for u in body['admittedUnits']}=={u.unit_id for u in client.prepared.units}
    assert len(body['futureContexts'])==4 and len(body['generations'])==2
    assert [e['epoch'] for e in body['epochs']]==[0]
    assert not body['startsClosedLocally'] and not body['nativeCancellationAcknowledged']
    assert all(r['issued'] is False and r['stageAttempted'] is False and r['intentEventId'] is None
        and r['issuedEventId'] is None and r['releaseObserved'] is False for r in body['generations'])
    assert not client._claims and not list(work.glob('*.marker'))
    retain(stack,projection,'never-issued')


def test_actual_release_has_original_clock_bracket_without_projection_rpc(broker_stack,monkeypatch):
    broker,facade,client,work=broker_stack
    end=stage_all(broker_stack)
    for unit in broker.owner._prepared.resource_order:
        issuer=broker.issuer(unit)
        assert facade.start(unit,issuer.recipe.descriptor,broker.connection,end).ready
    counts=client._sequence,broker.connection.sequence
    with monkeypatch.context() as patch:
        patch.setattr(client,'_rpc',lambda *a:pytest.fail('projection issued storage RPC'))
        patch.setattr(broker.connection,'_exchange',lambda *a,**kw:pytest.fail('projection issued native RPC'))
        projection=broker.public_projection(deadline(0.5))
    body=projection.public_data()
    assert (client._sequence,broker.connection.sequence)==counts
    assert body['hostSession']==broker.owner.session
    for row in body['generations']:
        assert row['issued'] is True and row['releaseObserved'] is True
        assert row['releaseRequestedAt']<=row['releaseAcknowledgedAt']<=body['observedAt']
        assert row['issuedEventId']==client._issued_receipts[row['unitId'],row['generation']].event_id
        assert row['directChildReaped'] is None and row['nativeRetired'] is None and row['c1Released'] is None
    def keys(value):
        if isinstance(value,dict):return set(value)|set().union(*(keys(v) for v in value.values()))
        if isinstance(value,list):return set().union(*(keys(v) for v in value))
        return set()
    assert not keys(body)&{'pid','fd','scope','ticket','nonce','handle','native_ack'}
    for issuer in broker.issuers:assert issuer._handle.opaque_id.encode() not in projection.public_bytes
    retain(broker_stack,projection,'released')


def test_actual_generation_projection_keeps_old_cleanup_and_rejects_deleted_old_entry(request,monkeypatch):
    stack,controller,unit,_=ready(request,monkeypatch)
    broker=stack[0]
    release(controller,unit);advance(stack,controller,unit)
    projection=broker.public_projection(deadline(0.5))
    body=projection.public_data()
    assert [e['epoch'] for e in body['epochs']]==[0,1]
    rows={r['generation']:r for r in body['generations'] if r['unitId']==unit}
    assert set(rows)=={1,2}
    assert rows[1]['directChildReaped'] is True and rows[1]['nativeRetired'] is True and rows[1]['c1Released'] is True
    assert rows[2]['releaseObserved'] is True and rows[2]['directChildReaped'] is None
    retain(stack,projection,'generation')
    old=broker._generation_issuers.pop((unit,1))
    try:
        with pytest.raises(ValueError,match='REPLACED'):broker.public_projection(deadline(0.5))
    finally:broker._generation_issuers[unit,1]=old
    # Restore the original ordered registry, not a newly invented inventory.
    original=dict(broker._generation_issuer_log)
    broker._generation_issuers.clear();broker._generation_issuers.update(original)


def test_actual_unacknowledged_stage_remains_unknown(broker_stack):
    broker,_,client,work=broker_stack
    unit=broker.owner._prepared.resource_order[0]
    broker.owner.commit_intent(unit,deadline(1))
    signal.pidfd_send_signal(broker.connection.child._capability.fileno(),signal.SIGSTOP)
    with pytest.raises(ValueError):broker.issuer(unit).stage(deadline(0.3))
    projection=broker.public_projection(deadline(0.5))
    body=projection.public_data()
    assert body['startsClosedLocally'] and body['authorityRevocationRequested']
    assert body['nativeCancellationAcknowledged'] is False
    rows={r['unitId']:r for r in body['generations']}
    assert rows[unit]['stageAttempted'] is True and rows[unit]['issued'] is None
    assert rows[unit]['directChildReaped'] is None and rows[unit]['issuedEventId'] is None
    assert not list(work.glob('*.marker'))
    retain(broker_stack,projection,'unknown')


@pytest.mark.parametrize('field',['_release_ack','_epoch_history'])
def test_original_ack_replacement_rejects_without_rpc(broker_stack,field):
    broker,facade,_,_=broker_stack
    end=stage_all(broker_stack)
    unit=broker.owner._prepared.resource_order[0]
    issuer=broker.issuer(unit)
    assert facade.start(unit,issuer.recipe.descriptor,broker.connection,end).ready
    target=issuer if field=='_release_ack' else broker.connection
    original=getattr(target,field)
    bad=replace(original,epoch=original.epoch+1) if field=='_release_ack' else (*original,original[-1])
    setattr(target,field,bad)
    try:
        with pytest.raises(ValueError,match='REPLACED'):broker.public_projection(deadline(0.5))
    finally:setattr(target,field,original)


def test_normal_projection_conflict_and_foreign_deadline_do_not_mutate(broker_stack):
    broker,_,client,_=broker_stack
    before=client._sequence,broker.connection.sequence
    assert broker._lock.acquire(False)
    try:
        with pytest.raises(ValueError,match='CONFLICT'):broker.public_projection(deadline(0.5))
    finally:broker._lock.release()
    with pytest.raises(ValueError,match='HOST-SESSION'):
        broker.public_projection(HostDeadline('foreign',deadline(0.5).monotonic_seconds))
    assert not broker.owner.latch.cancelled and (client._sequence,broker.connection.sequence)==before


def test_independent_cancel_during_projection_prevents_mixed_epoch_snapshot(broker_stack,monkeypatch):
    from xverse.maestro import evidence
    broker=broker_stack[0]
    original=evidence._bounded
    def cancelled(*args):
        data=original(*args)
        broker.cancel('projection-independent-cancel')
        return data
    monkeypatch.setattr(evidence,'_bounded',cancelled)
    with pytest.raises(ValueError,match='CONFLICT'):broker.public_projection(deadline(1.5))
    assert broker.owner.latch.cancelled
    monkeypatch.setattr(evidence,'_bounded',original)
    body=broker.public_projection(deadline(0.5)).public_data()
    assert body['startsClosedLocally'] and body['nativeCancellationAcknowledged']
