"""S1b finding 30: a health slot whose due time falls inside the unit's Stop bracket.

Diagnostic reproduction written before any repair. Live symptom (run set
s1c2-part2-dev7-20261024, runs ...T051109-freeze-vcu and ...T051454-nominal): the
carla-adapter-instance health slot 5 ends at Release-ACK + 5*5 s, which lies inside
the retained [stopRequestedAt, stopAcknowledgedAt] bracket. ``health_window``
(src/xverse/maestro/coverage.py:805 at 311016739; now :811-813) therefore returns
``applicable=None`` and ``assess`` (coverage.py:773-774 at 311016739; now :778-779) overwrites the already-satisfied status with
``unverifiable``, although valid health observations were retained inside the slot
and before the Stop request. The terminal report then lists ``normal-records``,
``required-coverage`` and ``uncertain-applicability`` (terminal_runtime.py:138-140).

The RED test states the expected behaviour after a repair: a complete, consistent
set of original Release/Stop bounds whose only uncertainty is the slot's due time
inside the Stop bracket is discharged by a valid in-slot observation taken no later
than the Stop request; the row becomes applicable/satisfied. The controls pin the
fail-closed behaviour that any repair must keep: the same bracket WITHOUT an in-slot
observation stays unverifiable, and missing bounds stay unverifiable even with an
observation (existing CV07 semantics). Synthetic fixture; no live data is replayed
except the recorded floating-point brackets (copied as constants) in the
classification control.
"""
from types import SimpleNamespace

import pytest

from xverse.maestro.coverage import _Assessment,assess_preclosure,verify_closed
from .test_coverage import Fixture,row

# Unit ``a`` in the neutral Fixture: cadence 1 s, Release-ACK 0.2 s, health samples at
# 1.0, 2.0 and 3.0 s, so slot 3 is [2.2, 3.2] and holds the sample at 3.0 s.
SLOT3_END=3.2


def _assess(f,stop):
    if stop is not None:
        f.broker['generations'][0].update(stopRequestedAt=stop[0],stopAcknowledgedAt=stop[1])
    return f.provisional().report()


def _health3_sample(f):
    sample=[e for e in f.events if e['extensions']['xverse.maestro']['action']=='health'
            and e['extensions']['xverse.maestro']['unitId']==f.a and e['clocks']['host']['value']==3.0]
    assert len(sample)==1
    return sample[0]['eventId']


def test_red_slot_due_inside_stop_bracket_with_in_slot_sample_is_satisfied(tmp_path):
    """Failed on ee91697a4 by design (finding 30); passes after S1a-6 (DR-20). Live geometry:
    Stop requested 0.076 s before the slot end and acknowledged 0.025 s after it; samples
    precede the request."""
    f=Fixture(tmp_path)
    try:
        report=_assess(f,(SLOT3_END-0.05,SLOT3_END+0.05))
        health=row(report,'health.3',f.a,1)
        # Before S1a-6 this was (None, 'unverifiable', 'Applicability is not established ...').
        observed=(health['applicable'],health['status'],health['diagnostic'])
        # Expected after the S1a-6 repair.
        assert health['applicable'] is True and health['status']=='satisfied',observed
        assert health['evidenceIds']==[_health3_sample(f)] and health['diagnostic'] is None
        assert row(report,'health.4',f.a,1)['status']=='not-applicable'
        assert report['normalRecordStatus']=='complete'
        # terminal_runtime.py:140 blocks on any applicable None row.
        assert not any(r['applicable'] is None for r in report['rows'])
    finally:
        f.writer.abort(reason='Synthetic finding 30 reproduction')


def test_control_bracket_without_in_slot_sample_stays_unverifiable(tmp_path):
    """Must keep passing after any repair: the slot is genuinely undecided (missing vs
    inactive) when no valid observation is retained in it; never satisfied, never
    rounded into not-applicable (review-affa17 finding 96)."""
    f=Fixture(tmp_path)
    try:
        f.broker['generations'][0].update(stopRequestedAt=SLOT3_END-0.05,stopAcknowledgedAt=SLOT3_END+0.05)
        args=f.arguments();sample=_health3_sample(f)
        args['annotations']=[e for e in args['annotations'] if e['eventId']!=sample]
        report=assess_preclosure(f.admission,**args).report()
        health=row(report,'health.3',f.a,1)
        assert health['applicable'] is None and health['status']=='unverifiable'
        assert report['normalRecordStatus']=='unverifiable'
    finally:
        f.writer.abort(reason='Synthetic finding 30 control')


@pytest.mark.parametrize('stop,applicable,status',[
    (None,True,'satisfied'),                                     # Fixture default Stop [3.9, 4.0]
    ((SLOT3_END+0.01,SLOT3_END+0.1),True,'satisfied'),           # due before Stop request
    ((SLOT3_END-0.1,SLOT3_END-0.01),False,'not-applicable'),     # due after Stop ACK
])
def test_control_slot_due_outside_stop_bracket(tmp_path,stop,applicable,status):
    f=Fixture(tmp_path)
    try:
        report=_assess(f,stop)
        health=row(report,'health.3',f.a,1)
        assert (health['applicable'],health['status'])==(applicable,status)
        assert report['normalRecordStatus']=='complete'
    finally:
        f.writer.abort(reason='Synthetic finding 30 control')


def test_control_missing_stop_bound_with_sample_stays_unverifiable(tmp_path):
    """A missing retained fact is not the bracket case: keep CV07 fail-closed."""
    f=Fixture(tmp_path)
    try:
        f.broker['generations'][0].pop('stopAcknowledgedAt')
        health=row(f.provisional().report(),'health.3',f.a,1)
        assert health['applicable'] is None and health['status']=='unverifiable'
    finally:
        f.writer.abort(reason='Synthetic finding 30 control')


# Recorded carla-adapter-instance generation-1 broker brackets, copied verbatim from
# broker-projection.json under .x-verse-build/runs/lite-stabilization-s1/
# s1c2-part2-dev7-20261024/dev-s1c2p1-20261024<name>/maestro-tmp/test_live_closed_loop0/
# argus-maestro/; cadence 5 s from the harness probe policy.
LIVE={
    'T051109-freeze-vcu':dict(releaseRequestedAt=1399321.287641925,releaseAcknowledgedAt=1399321.289444218,stopRequestedAt=1399346.213120387,stopAcknowledgedAt=1399346.313671428),
    'T051454-nominal':dict(releaseRequestedAt=1399546.351270475,releaseAcknowledgedAt=1399546.352955349,stopRequestedAt=1399571.332347959,stopAcknowledgedAt=1399571.36629344),
    'T051014-freeze-vcu':dict(releaseRequestedAt=1399266.735419706,releaseAcknowledgedAt=1399266.737270242,stopRequestedAt=1399291.817167774,stopAcknowledgedAt=1399291.956895546),
    'T050838-nominal':dict(releaseRequestedAt=1399167.477296139,releaseAcknowledgedAt=1399167.479054562,stopRequestedAt=1399191.893708963,stopAcknowledgedAt=1399192.04624077),
}


@pytest.mark.parametrize('name,slot,expected',[
    ('T051109-freeze-vcu',4,True),('T051109-freeze-vcu',5,None),('T051109-freeze-vcu',6,False),
    ('T051454-nominal',5,None),
    ('T051014-freeze-vcu',5,True),('T051014-freeze-vcu',6,False),
    ('T050838-nominal',5,False),
])
def test_control_recorded_live_brackets_classify_as_observed(name,slot,expected):
    """Pins the mechanism with the recorded floats: slot 5 ends 0.076 s / 0.021 s after
    the Stop request and before its ACK in the failing runs. White-box over the pure
    window rule only; the admitted active end is taken as generous (assumption)."""
    r=dict(LIVE[name],releaseObserved=True);unit='u'
    stub=SimpleNamespace(units={unit:dict(cadence=5)},terminal_end=r['releaseAcknowledgedAt']+60,
        ad=dict(start=r['releaseRequestedAt']-10,end=r['releaseAcknowledgedAt']+60))
    applicable,window,cut=_Assessment.health_window(stub,dict(unit=unit,slot=slot),r,None)
    assert applicable is expected,(window,r['stopRequestedAt'],r['stopAcknowledgedAt'])
    # S1a-6: the Stop-request cut is exposed only for the consistent bracket case.
    assert cut==(r['stopRequestedAt'] if expected is None else None)


# S1a-6 (DR-20) fail-closed controls added with the repair.

def test_control_sample_after_stop_request_does_not_discharge(tmp_path):
    """Stop request 2.95 s, ACK 3.25 s: slot 3 [2.2, 3.2] ends inside the bracket, and its
    only sample (3.0 s) comes after the Stop request, so it stays unverifiable."""
    f=Fixture(tmp_path)
    try:
        report=_assess(f,(2.95,3.25))
        health=row(report,'health.3',f.a,1)
        assert health['applicable'] is None and health['status']=='unverifiable'
        assert row(report,'health.2',f.a,1)['status']=='satisfied'
    finally:
        f.writer.abort(reason='Synthetic S1a-6 control')


def _invalidate_health3(f):
    """Point the 3.0 s health sample at the unit's start-outcome M3 record: hash-valid, but
    not an observe/observation source, so source_ok rejects it."""
    sample=_health3_sample(f)
    started=next(e for e in f.events if e['extensions']['xverse.maestro']['action']=='started'
                 and e['extensions']['xverse.maestro']['unitId']==f.a)
    event=next(e for e in f.events if e['eventId']==sample)
    event['extensions']['xverse.maestro']['sourceRefs']=[dict(r) for r in started['extensions']['xverse.maestro']['sourceRefs']]


def test_control_invalid_sample_does_not_discharge(tmp_path):
    reference=Fixture(tmp_path/'reference')
    try:
        _invalidate_health3(reference)
        # In an applicable geometry the same sample is not accepted as evidence.
        assert row(reference.provisional().report(),'health.3',reference.a,1)['status']!='satisfied'
    finally:
        reference.writer.abort(reason='Synthetic S1a-6 control')
    f=Fixture(tmp_path/'bracket')
    try:
        _invalidate_health3(f)
        health=row(_assess(f,(SLOT3_END-0.05,SLOT3_END+0.05)),'health.3',f.a,1)
        assert health['applicable'] is None and health['status']=='unverifiable'
    finally:
        f.writer.abort(reason='Synthetic S1a-6 control')


@pytest.mark.parametrize('stop',[
    (SLOT3_END+0.05,SLOT3_END-0.05),   # Stop ACK before Stop request
    (SLOT3_END-0.05,99.0),             # Stop ACK beyond the terminal end
    (0.1,SLOT3_END+0.05),              # Stop request before Release ACK (0.2)
])
def test_control_inconsistent_bound_order_stays_unverifiable(tmp_path,stop):
    f=Fixture(tmp_path)
    try:
        health=row(_assess(f,stop),'health.3',f.a,1)
        assert health['applicable'] is None and health['status']=='unverifiable'
    finally:
        f.writer.abort(reason='Synthetic S1a-6 control')


def test_discharge_keeps_expectations_digest_independent_of_samples(tmp_path):
    """Deleting the discharging sample changes the row, never expectedObligationsDigest."""
    f=Fixture(tmp_path)
    try:
        f.broker['generations'][0].update(stopRequestedAt=SLOT3_END-0.05,stopAcknowledgedAt=SLOT3_END+0.05)
        args=f.arguments();full=assess_preclosure(f.admission,**args).report()
        sample=_health3_sample(f)
        args['annotations']=[e for e in args['annotations'] if e['eventId']!=sample]
        reduced=assess_preclosure(f.admission,**args).report()
        assert row(full,'health.3',f.a,1)['status']=='satisfied'
        assert row(reduced,'health.3',f.a,1)['status']=='unverifiable'
        assert full['expectedObligationsDigest']==reduced['expectedObligationsDigest']
    finally:
        f.writer.abort(reason='Synthetic S1a-6 control')


# Finding 32 LOW-1: boundary, citation and offline cases pinned in the repository.

def _slot3_end(f):
    """Slot 3 end computed with the assessor's own arithmetic (Release-ACK + 3 * cadence 1)."""
    return f.broker['generations'][0]['releaseAcknowledgedAt']+3*1


@pytest.mark.parametrize('offset,discharged',[(0.0,True),(1e-9,False)])
def test_sample_exactly_at_stop_request_discharges_and_just_after_does_not(tmp_path,offset,discharged):
    """The 3.0 s sample is at the Stop request (offset 0) or 1e-9 s after it."""
    f=Fixture(tmp_path)
    try:
        health=row(_assess(f,(3.0-offset,SLOT3_END+0.05)),'health.3',f.a,1)
        assert (health['applicable'],health['status'])==((True,'satisfied') if discharged else (None,'unverifiable'))
        if discharged:assert health['evidenceIds']==[_health3_sample(f)]
    finally:
        f.writer.abort(reason='Synthetic finding 32 boundary')


@pytest.mark.parametrize('with_sample',[True,False])
def test_slot_end_exactly_at_stop_ack_is_the_bracket_case(tmp_path,with_sample):
    f=Fixture(tmp_path)
    try:
        end=_slot3_end(f)
        f.broker['generations'][0].update(stopRequestedAt=end-0.05,stopAcknowledgedAt=end)
        args=f.arguments()
        if not with_sample:args['annotations']=[e for e in args['annotations'] if e['eventId']!=_health3_sample(f)]
        health=row(assess_preclosure(f.admission,**args).report(),'health.3',f.a,1)
        assert (health['applicable'],health['status'])==((True,'satisfied') if with_sample else (None,'unverifiable'))
    finally:
        f.writer.abort(reason='Synthetic finding 32 boundary')


def test_citation_is_the_in_interval_sample_not_an_earlier_listed_post_request_one(tmp_path):
    """The 2.0 s sample is re-timed to 3.1 s, after the Stop request (3.05 s) but inside slot 3,
    and it precedes the 3.0 s sample in annotation order. Only the 3.0 s sample may be cited."""
    f=Fixture(tmp_path)
    try:
        late=next(e for e in f.events if e['extensions']['xverse.maestro']['action']=='health'
                  and e['extensions']['xverse.maestro']['unitId']==f.a and e['clocks']['host']['value']==2.0)
        late['clocks']['host']['value']=3.1;late['clocks']['utc']['value']=1700000000+3.1
        order=[e['eventId'] for e in f.events];assert order.index(late['eventId'])<order.index(_health3_sample(f))
        health=row(_assess(f,(3.05,SLOT3_END+0.05)),'health.3',f.a,1)
        assert health['applicable'] is True and health['status']=='satisfied'
        assert health['evidenceIds']==[_health3_sample(f)]
    finally:
        f.writer.abort(reason='Synthetic finding 32 citation')


def test_verify_closed_agrees_with_preclosure_on_a_discharged_slot(tmp_path):
    f=Fixture(tmp_path)
    f.broker['generations'][0].update(stopRequestedAt=SLOT3_END-0.05,stopAcknowledgedAt=SLOT3_END+0.05)
    online=f.close().report()
    result=verify_closed(f.admission,f.root,expected_admission_digest=f.admission.digest)
    offline=result.coverage.report()
    assert result.writer_state=='closed' and result.accepted_reader_executed and not result.reader_diagnostics
    assert row(online,'health.3',f.a,1)==row(offline,'health.3',f.a,1)
    assert row(offline,'health.3',f.a,1)['status']=='satisfied' and row(offline,'health.3',f.a,1)['applicable'] is True
    assert offline['expectedObligationsDigest']==online['expectedObligationsDigest']
    assert offline['overallStatus']=='complete' and offline['normalRecordStatus']=='complete'
