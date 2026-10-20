"""Independent clock-scope boundaries through actual Argus, with synthetic facts."""
from copy import deepcopy
from dataclasses import replace
import hashlib

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.coverage import CoverageError,canonical,digest,verify_closed,assess_preclosure,_payload
from xverse.maestro.evidence_scope import RuntimeEvidenceScope
from xverse_xdl.models import freeze
from .test_runtime_verification import RuntimeFixture


class ClockFixture(RuntimeFixture):
    def __init__(self,path,*,terminal_time=5.1,late_teardown=False,late_ready=False):
        self.terminal_time=terminal_time;self.late_teardown=late_teardown;self.late_ready=late_ready
        self.added_health=False
        if late_teardown:
            self.collection_started_at=5.7;self.collection_finished_at=5.71
            self.collection_event_at=5.72;self.collection_context_observed_at=5.65
            self.final_observed_at=6.0;self.terminal_time=5.8
        else:self.final_observed_at=max(5.3,terminal_time+.02)
        super().__init__(path)

    def emit(self,action,unit,t,**kw):
        if self.late_ready and action=='ready' and unit==self.a:t=5.01
        if self.late_teardown:
            if action=='stop' and not self.added_health:
                self.added_health=True
                for uid,stamp in ((self.a,4.0),(self.b,4.3)):
                    self.sample[uid]=super().emit('health',uid,stamp,phase='observe',kind='observation',
                        status='running',cause=self.sample[uid])
            if action in ('stop','cleanup'):
                t=(5.1 if unit==self.b else 5.3)+(0 if action=='stop' else .05)
                if action=='stop':
                    row=next(r for r in self.broker['generations'] if r['unitId']==unit)
                    row.update(stopRequestedAt=t-.01,stopAcknowledgedAt=t)
                    # Explicit synthetic stop-intent proof, appended through the
                    # real public journal/writer APIs; no provider operation.
                    target=next(u for u in self.units if u.unit_id==unit)
                    saved=next(r for r in self.journal.records if r.details.get('maestroUnitId')==unit and r.kind=='intent')
                    proof=dict(unit=unit,generation=1,phase='stop',stage='intent',
                        step='synthetic-stop-'+hashlib.sha256(unit.encode()).hexdigest()[:24],session='coverage-host',
                        observed_at=t-.02,boundary_digest=digest(['synthetic-boundary',unit]),
                        leader_reaped=False,empty=False,released=False,force_observed=False,
                        handle_digest=digest(['synthetic-handle',unit]))
                    details=dict(saved.details);details['teardown']=proof
                    self.journal.append(replace(saved,sequence=0,kind='intent',status='pending',
                        action_id=next(a.action_id for a in target.plan.actions if a.phase=='stop'),details=freeze(details)))
                    public=self.journal.public_records()[-1]
                    ref=dict(kind='m3-record',id='m3-record-'+str(public['sequence']),sequence=public['sequence'],sha256=digest(public))
                    kw['cause']=super().emit('intent',unit,t-.02,source=ref,producer='maestro.teardown13',
                        cause=self.sample[unit],handle_ref=self.handles[unit])
            if action=='disposition' and kw.get('scope')=='step':t=5.5
            if action=='disposition' and kw.get('scope','unit')=='unit':t=5.6
        if action=='run-terminal':t=self.terminal_time
        if action=='disposition' and kw.get('scope')=='run':t=self.terminal_time+.01
        return super().emit(action,unit,t,**kw)


@pytest.mark.parametrize('late_teardown',[False,True])
def test_original_runtime_scope_admits_terminal_facts_without_late_productive_credit(tmp_path,late_teardown):
    f=ClockFixture(tmp_path,late_teardown=late_teardown);f.close()
    result=f.verify()
    assert result.complete,result.lifecycle.coverage.report()
    assert result.lifecycle.coverage.report()['inputDigests']['runtimeAdmission']==f.pins['expected_runtime_digest']
    strict=verify_closed(f.admission,f.root,expected_admission_digest=f.admission.digest)
    assert strict.coverage.report()['overallStatus']!='complete'
    assert f.ad['end']==5 and f.generation_ns==10_000_000_000


def test_original_joint_scope_does_not_admit_late_readiness(tmp_path):
    f=ClockFixture(tmp_path,late_ready=True);f.close()
    result=f.verify()
    assert not result.complete
    assert result.lifecycle.coverage.report()['normalRecordStatus']!='complete'


def test_terminal_records_beyond_original_generation_minus_drain_stay_invalid(tmp_path):
    f=ClockFixture(tmp_path,terminal_time=9.51);f.close()
    result=f.verify()
    assert not result.complete and result.lifecycle.coverage.report()['normalRecordStatus']!='complete'


@pytest.mark.parametrize('mutation',['no-pin','wrong-pin','changed-plan','changed-generation','fake-scope'])
def test_substituted_scope_is_rejected_before_any_evidence_read(tmp_path,monkeypatch,mutation):
    f=ClockFixture(tmp_path)
    scope=RuntimeEvidenceScope(f.collection_plan.canonical_bytes,f.generation_ns)
    pin=f.pins['expected_runtime_digest']
    if mutation=='no-pin':pin=None
    if mutation=='wrong-pin':pin='sha256:'+'0'*64
    if mutation=='changed-plan':scope=RuntimeEvidenceScope(replace(f.collection_plan,source_identity=(0,0)).canonical_bytes,f.generation_ns)
    if mutation=='changed-generation':scope=RuntimeEvidenceScope(f.collection_plan.canonical_bytes,f.generation_ns+1)
    if mutation=='fake-scope':scope=object()
    monkeypatch.setattr(EvidenceStore,'read_run',lambda *a,**kw:pytest.fail('I/O before original scope validation'))
    try:
        with pytest.raises(CoverageError):
            verify_closed(f.admission,f.root,expected_admission_digest=f.admission.digest,
                          runtime_scope=scope,expected_runtime_digest=pin)
    finally:f.writer.abort(reason='Synthetic scope-substitution control')


@pytest.mark.parametrize('action',['intent','issued','started','probe','ready','health'])
def test_late_productive_payload_remains_outside_original_active_interval(tmp_path,action):
    f=ClockFixture(tmp_path)
    event=deepcopy(next(e for e in f.events if e['extensions']['xverse.maestro']['scope']=='unit'
                        and e['extensions']['xverse.maestro']['action']==action))
    event['clocks']['host']['value']=5.01
    assert _payload(event,f.ad,terminal_end=9.5) is None
    f.writer.abort(reason='Synthetic late productive control')


def test_producer_name_cannot_turn_late_start_intent_into_teardown_proof(tmp_path):
    f=ClockFixture(tmp_path);args=f.arguments()
    event=next(e for e in args['annotations'] if e['extensions']['xverse.maestro']['action']=='intent')
    event['producerId']='maestro.teardown13';event['clocks']['host']['value']=5.01
    event['extensions']['xverse.maestro']['handleRef']=f.handles[event['extensions']['xverse.maestro']['unitId']]
    args['artifact_bytes'].pop(f.ad['retainedPath'])  # This control isolates source proof, not snapshot equality.
    result=assess_preclosure(f.admission,**args,
        runtime_scope=RuntimeEvidenceScope(f.collection_plan.canonical_bytes,f.generation_ns),
        expected_runtime_digest=f.pins['expected_runtime_digest'])
    assert not result.normal_complete
    assert next(r for r in result.report()['rows'] if r['obligationId']=='ob.input-integrity')['status']!='satisfied'
    f.writer.abort(reason='Synthetic forged late intent producer')
