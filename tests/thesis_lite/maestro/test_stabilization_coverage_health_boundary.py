"""S1b finding 30: a health slot whose due time falls inside the unit's Stop bracket.

Diagnostic reproduction written before any repair. Live symptom (run set
s1c2-part2-dev7-20261024, runs ...T051109-freeze-vcu and ...T051454-nominal): the
carla-adapter-instance health slot 5 ends at Release-ACK + 5*5 s, which lies inside
the retained [stopRequestedAt, stopAcknowledgedAt] bracket. ``health_window``
(src/xverse/maestro/coverage.py:805) therefore returns ``applicable=None`` and
``assess`` (coverage.py:773-774) overwrites the already-satisfied status with
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

from xverse.maestro.coverage import _Assessment,assess_preclosure
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
    """FAILS on ee91697a4 by design (finding 30). Live geometry: Stop requested 0.076 s
    before the slot end and acknowledged 0.025 s after it; samples precede the request."""
    f=Fixture(tmp_path)
    try:
        report=_assess(f,(SLOT3_END-0.05,SLOT3_END+0.05))
        health=row(report,'health.3',f.a,1)
        # Current behaviour, recorded for the diagnosis: applicable None -> unverifiable.
        observed=(health['applicable'],health['status'],health['diagnostic'])
        # Expected after repair.
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
    applicable,window=_Assessment.health_window(stub,dict(unit=unit,slot=slot),r,None)
    assert applicable is expected,(window,r['stopRequestedAt'],r['stopAcknowledgedAt'])
