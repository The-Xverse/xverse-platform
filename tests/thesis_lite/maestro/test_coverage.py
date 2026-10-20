"""Neutral authored coverage fixtures; no provider workload or scientific result."""
from copy import deepcopy
from dataclasses import replace
import builtins
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest
from jsonschema import Draft202012Validator
from xverse.argus import EvidenceStore
from xverse.maestro.coverage import (ArtifactExpectation,CoverageAdmission,CoverageError,
    admit_coverage,assess_preclosure,verify_closed,canonical,digest)
from xverse.maestro.projection import prepare_lifecycle
from xverse_xdl.lifecycle import FileEvidenceJournal,EvidenceRecord
from xverse_xdl.models import freeze
from .test_preparation import compiled,PIN

SCHEMA=json.loads(Path(__file__).with_name('lifecycle-coverage-v2.schema.json').read_text())
VALIDATOR=Draft202012Validator(SCHEMA)


class Fixture:
    """Writes synthetic observations through real accepted journal/writer APIs."""
    def __init__(self,path,*,failed=False,future=True,required_output=False,optional_output=False,freshness=5,teardown_refs=False):
        self.teardown_refs=teardown_refs
        self.result,self.resources=compiled()
        self.prepared=prepare_lifecycle(self.result,self.resources,provider_descriptors=(PIN,))
        self.units=list(self.prepared.units);self.a,self.b=[u.unit_id for u in self.units]
        contexts=[(u.unit_id,g,'synthetic-execution-'+str(i)+'-g'+str(g)) for i,u in enumerate(self.units) for g in ((1,2) if future else (1,))]
        artifacts=[]
        if required_output or optional_output:artifacts=[ArtifactExpectation('synthetic-output.json',required=required_output,unit_id=self.a,generation=1)]
        self.admission=admit_coverage(self.prepared,self.result,self.resources,run_id='coverage-fixture',host_session='coverage-host',
            contexts=contexts,health_policies={u.unit_id:(1,freshness) for u in self.units},active_start=0,active_end=5,artifacts=artifacts)
        self.ad=self.admission.data(self.admission.digest)
        self.root=path/'argus';self.journal=FileEvidenceJournal(path/'synthetic-m3.jsonl')
        self.writer=EvidenceStore.open_run(self.root,run_id='coverage-fixture',plan=self.result.plan,
            clocks={'host':dict(domain='host:coverage-host',unit='s',value=0),'utc':dict(domain='utc:coverage-host',unit='s',value=1700000000)})
        self.events=[];self.seq={};self.sample={};self.intent={};self.issued={};self.cleanup={};self.counter=0
        self.handles={u.unit_id:'handle-'+hashlib.sha256(u.unit_id.encode()).hexdigest() for u in self.units}
        self.emit('validate',None,0,scope='run',generation=0,producer='maestro.validation17',anchor=True)
        self.broker=dict(schemaVersion='1.0',runId=self.ad['runId'],lifecycleDigest=self.ad['lifecycleDigest'],hostSession='coverage-host',
            observedAt=4.6,admittedUnits=[dict(unitId=u.unit_id,initialGeneration=1,maximumGeneration=2 if future else 1) for u in self.units],
            futureContexts=[c for c in self.ad['contexts'] if c['generation']!=1],generations=[],epochs=[dict(kind='ready',epoch=0,sequence=0)],
            startsClosedLocally=True,authorityRevocationRequested=False,nativeCancellationAcknowledged=False,cancellationRequested=failed)
        for i,u in enumerate(self.units):
            uid=u.unit_id;blocked=failed and uid==self.b
            row=dict(unitId=uid,generation=1,stageAttempted=not blocked,issued=not blocked,intentEventId=None,issuedEventId=None,
                handleRef=self.handles[uid] if not blocked else None,releaseObserved=not blocked,
                releaseRequestedAt=(0.1 if i==0 else 0.45) if not blocked else None,
                releaseAcknowledgedAt=(0.2 if i==0 else 0.5) if not blocked else None,
                stopRequestedAt=(0.6 if failed else 3.9 if i==0 else 3.6) if not blocked else None,
                stopAcknowledgedAt=(0.61 if failed else 4.0 if i==0 else 3.7) if not blocked else None,
                directChildReaped=True if not blocked else None,nativeRetired=True if not blocked else None,c1Released=True if not blocked else None)
            self.broker['generations'].append(row)
            if blocked:continue
            self.intent[uid]=self.emit('intent',uid,0.05 if i==0 else .3,phase='start',kind='intent',status='pending',producer='maestro.owner7')
            self.issued[uid]=self.emit('issued',uid,.1 if i==0 else .4,phase='start',kind='observation',status='staged',cause=self.intent[uid],producer='maestro.issuance17')
            row.update(intentEventId=self.intent[uid],issuedEventId=self.issued[uid])
            started=self.emit('started',uid,.21 if i==0 else .51,phase='start',kind='outcome',status='failed' if failed else 'running',
                cause=self.issued[uid],outcome='failed' if failed else 'succeeded')
            if not failed:
                self.sample[uid]=self.emit('probe',uid,.22 if i==0 else .52,phase='observe',kind='observation',status='running',cause=started)
                self.emit('ready',uid,.22 if i==0 else .52,source=self.last_source,cause=self.sample[uid])
        if not failed:
            for i in range(1,4):
                for uid,t in [(self.a,float(i)),(self.b,i+.3)]:
                    self.sample[uid]=self.emit('health',uid,t,phase='observe',kind='observation',status='running',cause=self.sample[uid])
        for uid,t in ([(self.a,.61)] if failed else [(self.b,3.7),(self.a,4.0)]):
            stopped=self.emit('stop',uid,t,phase='stop',kind='outcome',status='stopped',cause=self.sample.get(uid,self.issued[uid]),producer='maestro.teardown13')
            self.cleanup[uid]=self.emit('cleanup',uid,t+.05,phase='cleanup',kind='outcome',status='cleaned',cause=stopped,producer='maestro.teardown13')
        for step in self.ad['steps']:
            uid=step['unitId'];blocked=failed and uid==self.b
            self.emit('disposition',uid,4.2,scope='step',step=step['stepId'],generation=0 if blocked else 1,
                outcome='skipped' if blocked else 'failed' if failed else 'succeeded',disposition='blocked' if blocked else 'failed' if failed else 'completed',
                cause=self.cleanup.get(uid),producer='maestro.scheduler14')
        for uid in (self.a,self.b):
            blocked=failed and uid==self.b
            self.emit('disposition',uid,4.3,generation=0 if blocked else 1,outcome='skipped' if blocked else 'failed' if failed else 'succeeded',
                disposition='blocked' if blocked else 'failed' if failed else 'completed',cause=self.cleanup.get(uid),producer='maestro.scheduler14')
        collect=self.emit('collect',None,4.5,scope='run',generation=0,producer='maestro.scheduler14')
        terminal=self.emit('run-terminal',None,4.7,scope='run',generation=0,outcome='failed' if failed else 'succeeded',cause=collect,producer='maestro.scheduler14')
        self.emit('disposition',None,4.71,scope='run',generation=0,outcome='failed' if failed else 'succeeded',disposition='failed' if failed else 'completed',cause=terminal,producer='maestro.scheduler14')
        self.writer.flush_buffer()

    def emit(self,action,unit,t,*,phase=None,kind=None,status=None,source=None,cause=None,producer='maestro.outcomes12',outcome='succeeded',scope='unit',step=None,generation=1,disposition=None,anchor=False,annotation_text='Synthetic coverage contract fixture',handle_ref=None):
        self.counter+=1;operation='synthetic-op-'+str(self.counter);eid=operation+'-'+action
        if anchor:eid=self.ad['runId']
        if phase:
            u=next(u for u in self.units if u.unit_id==unit);context=next(c for c in self.ad['contexts'] if c['unitId']==unit and c['generation']==generation)
            details=dict(maestroRunId=self.ad['runId'],maestroUnitId=unit,generation=generation,lifecycleDigest=self.prepared.lifecycle_digest)
            if phase in ('stop','cleanup'):
                details['teardown']=dict(leader_reaped=True,empty=True,released=phase=='cleanup')
                if self.teardown_refs:
                    details['teardown'].update(unit=unit,generation=generation,phase=phase,stage='outcome',
                        step='synthetic-teardown-'+str(self.counter),session='coverage-host',observed_at=t,
                        boundary_digest=digest(['synthetic-boundary',unit]),handle_digest=digest(['synthetic-handle',unit]),
                        force_observed=False)
            record=EvidenceRecord(kind,0,'2026-10-19T00:00:00+00:00',context['executionId'],next(a.action_id for a in u.plan.actions if a.phase==phase),
                u.plan.catalog_identity,u.plan.digest,None,None,status,u.plan.environment_identity,u.plan.resource_revisions,u.plan.artifact_digests,u.plan.selection,
                handle_id=None if action=='intent' else 'synthetic-private-handle',handle_action_id=next(a.action_id for a in u.plan.actions if a.phase=='start') if action!='intent' else None,
                handle_provider_id=u.plan.provider_id if action!='intent' else None,handle_provider_kind=u.plan.provider_kind if action!='intent' else None,
                handle_resource_identity='synthetic-private-boundary' if action!='intent' else None,details=freeze(details))
            self.journal.append(record);r=self.journal.public_records()[-1]
            source=dict(kind='m3-record',id='m3-record-'+str(r['sequence']),sequence=r['sequence'],sha256=digest(r))
            self.last_source=source
        if source is None:source=dict(kind='admitted-lifecycle',id='original-coverage-admission',sequence=0,sha256=self.admission.digest)
        sources=[source]
        if self.teardown_refs and action in ('stop','cleanup'):
            proof=details['teardown']
            sources.append(dict(kind='broker-record',id=proof['step'],sequence=self.seq.get(producer,0)+1,sha256=digest(proof)))
        deps=[]
        if unit is not None and action in ('started','probe','ready','health'):
            for parent in next(u['parents'] for u in self.ad['units'] if u['unitId']==unit):
                deps.append(dict(unitId=parent,generation=1,probeEventId=self.sample[parent]))
        payload=dict(schemaVersion='2.0',lifecycleDigest=self.ad['lifecycleDigest'],runId=self.ad['runId'],sessionId='coverage-host',scope=scope,
            unitId=unit,generation=generation,operationId=operation,action=action,outcome='pending' if action=='intent' else outcome,sourceRefs=sources,dependencies=deps)
        if action in ('probe','ready','health'):payload['probeId']='running'
        if unit is not None and action in ('issued','started','probe','ready','health','stop','cleanup'):payload['handleRef']=self.handles[unit]
        if handle_ref is not None:payload['handleRef']=handle_ref
        if step is not None:payload['stepId']=step
        if disposition:payload.update(disposition=disposition,cause='normal')
        self.seq[producer]=self.seq.get(producer,0)+1
        fields=dict(eventId=eid,producerId=producer,eventKind='annotation',producerSequence=self.seq[producer],correlationId=None if anchor else self.ad['runId'],causationId=cause,
            clocks=dict(host=dict(domain='host:coverage-host',unit='s',value=t),utc=dict(domain='utc:coverage-host',unit='s',value=1700000000+t)),
            annotation=dict(text=annotation_text),extensions={'xverse.maestro':payload})
        ordinal=self.writer.append_event(event_id=eid,producer_id=producer,event_kind='annotation',producer_sequence=fields['producerSequence'],
            correlation_id=fields['correlationId'],causation_id=cause,clocks=fields['clocks'],annotation=fields['annotation'],extensions=fields['extensions'])
        fields['ingestionOrdinal']=ordinal;self.events.append(fields)
        return eid

    def arguments(self):
        retained=dict(schemaVersion='1.0',runId=self.ad['runId'],lifecycleDigest=self.ad['lifecycleDigest'],trustBoundary='Synthetic caller-retained fixture',annotations=self.events,publicM3=list(self.journal.public_records()))
        contents={self.ad['retainedPath']:canonical(retained),self.ad['brokerPath']:canonical(self.broker)}
        entries=[]
        for path,data in contents.items():
            (self.root/path).write_bytes(data);entries.append(self.writer.record_artifact(path))
        return dict(expected_admission_digest=self.admission.digest,annotations=deepcopy(self.events),public_m3=list(self.journal.public_records()),
                    broker=deepcopy(self.broker),artifact_entries=entries,artifact_bytes=contents)

    def provisional(self):
        result=assess_preclosure(self.admission,**self.arguments());VALIDATOR.validate(result.report());return result

    def close(self,*,abort=False,report=None):
        report=report or self.provisional()
        (self.root/self.ad['reportPath']).write_bytes(report.public_bytes)
        self.writer.record_artifact(self.ad['reportPath'],schema_version='2.0')
        if abort:self.writer.abort(reason='Synthetic explicit failure')
        else:self.writer.finalize()
        return report


def row(report,suffix,unit=None,generation=None):
    rows=[r for r in report['rows'] if (r['obligationId'].endswith('.'+suffix) or r['obligationId']=='ob.'+suffix)
        and (unit is None or r['unitId']==unit) and (generation is None or r['generation']==generation)]
    assert len(rows)==1,[(r['obligationId'],r['unitId']) for r in rows]
    return rows[0]


def test_original_universe_and_provisional_nominal_cannot_promote_execution(tmp_path):
    f=Fixture(tmp_path);report=f.provisional().report()
    assert report['normalRecordStatus']=='complete' and report['emergencyFactStatus']=='not-needed'
    assert report['overallStatus']=='incomplete' and report['assessmentStage']=='pre-closure'
    for u in (f.a,f.b):
        assert row(report,'unit-disposition',u)['status']=='satisfied'
        assert row(report,'intent',u,2)['status']=='not-applicable'
    assert not any(r['obligationId']=='ob.artifact.'+hashlib.sha256(f.ad['reportPath'].encode()).hexdigest() for r in report['rows'])
    f.writer.abort(reason='Synthetic test completed')


@pytest.mark.parametrize('failed',[False,True])
def test_actual_closed_writer_independent_coverage_separates_execution_outcome(tmp_path,failed):
    f=Fixture(tmp_path,failed=failed);f.close()
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in f.root.iterdir() if p.is_file()}
    result=verify_closed(f.admission,f.root,expected_admission_digest=f.admission.digest);report=result.coverage.report()
    VALIDATOR.validate(report)
    assert report['overallStatus']=='complete' and report['normalRecordStatus']=='complete'
    assert result.writer_state=='closed' and result.accepted_reader_executed and result.manifest_sha256
    assert not result.reader_diagnostics
    assert {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in f.root.iterdir() if p.is_file()}==before


@pytest.mark.parametrize('mutation',['unit','issued','health','step-disposition','unit-disposition'])
def test_deletions_never_shrink_original_template_universe(tmp_path,mutation):
    f=Fixture(tmp_path);base=f.arguments();original=assess_preclosure(f.admission,**base).report()
    selected=[]
    for event in base['annotations']:
        p=event['extensions']['xverse.maestro']
        remove=(p['unitId']==f.a if mutation=='unit' else p['action']==mutation and p['unitId']==f.a if mutation in ('issued','health')
            else p['action']=='disposition' and p['scope']==('step' if mutation=='step-disposition' else 'unit') and p['unitId']==f.a)
        if not remove:selected.append(event)
    base['annotations']=selected
    changed=assess_preclosure(f.admission,**base).report()
    assert [r['obligationId'] for r in changed['rows']]==[r['obligationId'] for r in original['rows']]
    assert changed['normalRecordStatus']!='complete'
    if mutation=='health':assert changed['expectedObligationsDigest']==original['expectedObligationsDigest']
    f.writer.abort(reason='Synthetic deletion control')


def test_missing_normal_outcome_remains_missing_with_complete_emergency_facts(tmp_path):
    f=Fixture(tmp_path);args=f.arguments()
    args['annotations']=[e for e in args['annotations'] if not (e['extensions']['xverse.maestro']['action']=='started' and e['extensions']['xverse.maestro']['unitId']==f.a)]
    for e in args['annotations']:
        p=e['extensions']['xverse.maestro']
        if p['scope']=='unit' and p['unitId']==f.a and p['action']=='disposition':p['cause']='journal-failure'
    result=assess_preclosure(f.admission,**args).report()
    assert row(result,'outcome',f.a,1)['status']=='missing'
    assert result['normalRecordStatus']=='incomplete' and result['emergencyFactStatus']=='complete'
    assert result['overallStatus']=='incomplete'
    f.writer.abort(reason='Synthetic normal gap')


@pytest.mark.parametrize('field',['stopRequestedAt','stopAcknowledgedAt','releaseAcknowledgedAt'])
def test_missing_original_interval_bounds_leave_health_unverifiable(tmp_path,field):
    f=Fixture(tmp_path);args=f.arguments();base=assess_preclosure(f.admission,**args).report()
    args['broker']['generations'][0].pop(field)
    result=assess_preclosure(f.admission,**args).report()
    assert len(result['rows'])==len(base['rows'])
    assert row(result,'health.1',f.a,1)['status']=='unverifiable'
    f.writer.abort(reason='Synthetic missing endpoint')


@pytest.mark.parametrize('mutation',['generation','handle','source','dependency','clock','duplicate','timestamp','disposition-source'])
def test_inconsistent_original_identities_never_complete(tmp_path,mutation):
    f=Fixture(tmp_path);args=f.arguments()
    if mutation=='duplicate':args['annotations'].append(deepcopy(args['annotations'][0]))
    else:
        event=next(e for e in args['annotations'] if e['extensions']['xverse.maestro']['action']==('disposition' if mutation=='disposition-source' else 'ready') and e['extensions']['xverse.maestro']['unitId']==(f.a if mutation=='generation' else f.b) and e['extensions']['xverse.maestro']['scope']=='unit')
        p=event['extensions']['xverse.maestro']
        if mutation=='generation':p['generation']=2
        elif mutation=='handle':p['handleRef']='foreign-handle'
        elif mutation=='source':p['sourceRefs'][0]['sha256']='sha256:'+'0'*64
        elif mutation=='dependency':p['dependencies'][0]['generation']=2
        elif mutation=='timestamp':
            source=args['public_m3'][p['sourceRefs'][0]['sequence']-1]
            source['timestamp']='2026-10-19T00:00:00'
            p['sourceRefs'][0]['sha256']=digest(source)
        elif mutation=='disposition-source':
            other=next(e for e in args['annotations'] if e['extensions']['xverse.maestro']['unitId']==f.a and e['extensions']['xverse.maestro']['action']=='intent')
            p['sourceRefs']=deepcopy(other['extensions']['xverse.maestro']['sourceRefs'])
        else:event['clocks']['host']['domain']='host:replacement'
    result=assess_preclosure(f.admission,**args).report()
    assert result['normalRecordStatus']!='complete'
    if mutation=='generation':assert row(result,'ready',f.a,1)['status']=='conflicting'
    if mutation=='timestamp':assert 'timestamp' in row(result,'input-integrity')['diagnostic']
    if mutation=='disposition-source':assert row(result,'unit-disposition',f.b)['status']=='conflicting'
    f.writer.abort(reason='Synthetic identity control')


@pytest.mark.parametrize('mode',['missing-report','changed-row','false-applicability','corrupt-report','failed-writer'])
def test_closed_reader_rejects_report_loss_tampering_or_failed_closure(tmp_path,mode):
    f=Fixture(tmp_path);report=f.provisional()
    if mode in ('changed-row','false-applicability'):
        body=report.report()
        if mode=='changed-row':body['rows'].pop()
        else:body['rows'][0].update(applicable=False,status='not-applicable')
        report=replace(report,public_bytes=canonical(body))
    f.close(abort=mode=='failed-writer',report=report)
    path=f.root/f.ad['reportPath']
    if mode=='missing-report':path.unlink()
    elif mode=='corrupt-report':path.write_bytes(b'{corrupt')
    result=verify_closed(f.admission,f.root,expected_admission_digest=f.admission.digest)
    assert result.coverage.report()['overallStatus']!='complete'
    if mode in ('missing-report','corrupt-report'):assert result.reader_diagnostics


def test_open_reader_is_not_artifact_index_or_closed_coverage_proof(tmp_path):
    f=Fixture(tmp_path);f.provisional()
    result=verify_closed(f.admission,f.root,expected_admission_digest=f.admission.digest)
    assert result.writer_state=='open' and result.coverage.report()['overallStatus']!='complete'
    f.writer.abort(reason='Synthetic open writer')


def test_report_artifact_loss_keeps_normal_record_status_separate(tmp_path):
    f=Fixture(tmp_path);f.close();(f.root/f.ad['reportPath']).unlink()
    result=verify_closed(f.admission,f.root,expected_admission_digest=f.admission.digest).coverage.report()
    assert result['normalRecordStatus']=='complete' and result['overallStatus']!='complete'
    own=next(r for r in result['rows'] if r['operationId']=='ob.coverage-report')
    assert own['status']=='missing'


def test_assessor_uses_no_ambient_clock_io_or_provider_callback(tmp_path,monkeypatch):
    f=Fixture(tmp_path);args=f.arguments()
    def forbidden(*a,**kw):pytest.fail('pure assessment performed I/O or clock work')
    with monkeypatch.context() as patch:
        patch.setattr(builtins,'open',forbidden);patch.setattr(os,'open',forbidden)
        patch.setattr(time,'monotonic',forbidden);patch.setattr(time,'time',forbidden)
        assert assess_preclosure(f.admission,**args).report()['overallStatus']=='incomplete'
    code="import sys;import xverse.maestro.coverage;assert 'xverse.maestro.providers' not in sys.modules;assert 'xverse.maestro.run_broker' not in sys.modules"
    subprocess.run([sys.executable,'-I','-c',code],check=True,cwd=tmp_path)
    f.writer.abort(reason='Synthetic purity control')


def test_original_admission_digest_and_template_deletion_are_checked(tmp_path):
    f=Fixture(tmp_path);args=f.arguments();ad=f.admission.data(f.admission.digest)
    ad['templates'].pop();tampered=CoverageAdmission(canonical(ad))
    with pytest.raises(CoverageError):assess_preclosure(tampered,**args)
    with pytest.raises(CoverageError):tampered.data(tampered.digest)
    ad=f.admission.data(f.admission.digest);ad['units'].pop();tampered=CoverageAdmission(canonical(ad))
    with pytest.raises(CoverageError):tampered.data(f.admission.digest)
    f.writer.abort(reason='Synthetic original admission control')


def test_required_artifact_missing_is_distinct_from_normal_record_coverage(tmp_path):
    f=Fixture(tmp_path,required_output=True);report=f.provisional().report()
    assert report['normalRecordStatus']=='complete'
    assert any(r['obligationClass']=='artifact' and r['status']=='missing' for r in report['rows'])
    f.writer.abort(reason='Synthetic missing required output')


def test_optional_missing_output_does_not_create_false_offline_corruption(tmp_path):
    f=Fixture(tmp_path,optional_output=True);f.close()
    result=verify_closed(f.admission,f.root,expected_admission_digest=f.admission.digest)
    assert result.coverage.report()['overallStatus']=='complete'


def test_unbounded_inputs_or_bad_clock_cadence_reject_before_assessment(tmp_path):
    f=Fixture(tmp_path);args=f.arguments()
    class Poison:
        def __iter__(self):pytest.fail('unadmitted iterable callback')
    args['annotations']=Poison()
    with pytest.raises(CoverageError):assess_preclosure(f.admission,**args)
    with pytest.raises(CoverageError):admit_coverage(f.prepared,f.result,f.resources,run_id='r',host_session='s',
        contexts=[(u.unit_id,1,'exec-'+str(i)) for i,u in enumerate(f.units)],health_policies={u.unit_id:(1e-300,1) for u in f.units},active_start=0,active_end=5)
    f.writer.abort(reason='Synthetic malformed input')


def test_actual_indexed_output_byte_mutation_never_keeps_complete_coverage(tmp_path):
    f=Fixture(tmp_path,required_output=True);args=f.arguments()
    data=b'{"synthetic_output":true}'
    (f.root/'synthetic-output.json').write_bytes(data)
    args['artifact_entries'].append(f.writer.record_artifact('synthetic-output.json'))
    args['artifact_bytes']['synthetic-output.json']=data
    report=assess_preclosure(f.admission,**args)
    assert all(r['status']=='satisfied' for r in report.report()['rows'] if r['obligationClass']=='artifact')
    f.close(report=report)
    assert verify_closed(f.admission,f.root,expected_admission_digest=f.admission.digest).coverage.report()['overallStatus']=='complete'
    (f.root/'synthetic-output.json').write_bytes(b'corrupted')
    result=verify_closed(f.admission,f.root,expected_admission_digest=f.admission.digest)
    assert result.coverage.report()['overallStatus']!='complete' and result.reader_diagnostics


def test_stale_same_generation_prerequisite_is_not_fresh_evidence(tmp_path):
    f=Fixture(tmp_path,freshness=1);args=f.arguments()
    old=next(e['eventId'] for e in args['annotations'] if e['extensions']['xverse.maestro']['unitId']==f.a and e['extensions']['xverse.maestro']['action']=='probe')
    event=next(e for e in reversed(args['annotations']) if e['extensions']['xverse.maestro']['unitId']==f.b and e['extensions']['xverse.maestro']['action']=='health')
    event['extensions']['xverse.maestro']['dependencies'][0]['probeEventId']=old
    assert assess_preclosure(f.admission,**args).report()['normalRecordStatus']!='complete'
    f.writer.abort(reason='Synthetic stale dependency')


def test_bool_generation_and_capacity_do_not_alias_original_integers(tmp_path):
    f=Fixture(tmp_path);args=f.arguments()
    args['broker']['generations'][0]['generation']=True
    args['broker']['admittedUnits'][0]['initialGeneration']=True
    assert assess_preclosure(f.admission,**args).report()['normalRecordStatus']!='complete'
    f.writer.abort(reason='Synthetic integer type control')


def test_future_intent_without_acknowledged_issuer_never_becomes_inactive(tmp_path):
    f=Fixture(tmp_path)
    f.emit('intent',f.a,4.8,phase='start',kind='intent',status='pending',producer='maestro.owner7',generation=2)
    report=f.provisional().report()
    assert row(report,'intent',f.a,2)['applicable'] is True
    assert row(report,'outcome',f.a,2)['status']=='missing'
    assert row(report,'issued',f.a,2)['status']=='unverifiable'
    assert row(report,'run-terminal')['status']=='conflicting'
    f.writer.abort(reason='Synthetic future-context gap')


def test_missing_real_run_validation_is_not_reconstructed_from_correlation(tmp_path):
    f=Fixture(tmp_path);args=f.arguments()
    args['annotations']=[e for e in args['annotations'] if e['eventId']!=f.ad['runId']]
    report=assess_preclosure(f.admission,**args).report()
    assert row(report,'run-validation')['status']=='missing' and report['normalRecordStatus']!='complete'
    f.writer.abort(reason='Synthetic missing validation source')


@pytest.mark.parametrize('terminated',[True,False])
def test_cleanup_only_c1_facts_are_independent_of_missing_ordinary_wait(tmp_path,terminated):
    f=Fixture(tmp_path);args=f.arguments()
    args['annotations']=[e for e in args['annotations'] if not (e['extensions']['xverse.maestro']['unitId']==f.a and e['extensions']['xverse.maestro']['action']=='started')]
    for e in args['annotations']:
        p=e['extensions']['xverse.maestro']
        if p['scope']=='unit' and p['unitId']==f.a and p['action']=='disposition':p.update(cause='issuer-loss',disposition='unresolved',outcome='unresolved')
        if p['scope']=='run' and p['action']=='run-terminal':p['outcome']='failed'
        if p['scope']=='run' and p['action']=='disposition':p.update(outcome='failed',disposition='failed')
    proof=args['broker']['generations'][0]
    proof.update(directChildReaped=None,nativeRetired=None,c1TerminationObserved=terminated,c1Empty=True,c1Released=True)
    report=assess_preclosure(f.admission,**args).report()
    assert row(report,'outcome',f.a,1)['status']=='missing' and report['normalRecordStatus']=='incomplete'
    assert report['emergencyFactStatus']==('complete' if terminated else 'unverifiable')
    assert report['overallStatus']=='incomplete'
    f.writer.abort(reason='Synthetic separate cleanup-only proof')



def test_other_run_validation_records_do_not_replace_or_duplicate_original_root(tmp_path):
    f=Fixture(tmp_path)
    f.emit('validate',None,4.8,scope='run',generation=0,producer='maestro.scheduler14')
    result=f.provisional().report()
    assert row(result,'run-validation')['status']=='satisfied'
    assert row(result,'run-terminal')['status']=='conflicting'
    f.writer.abort(reason='Synthetic late validation remains visible')


@pytest.mark.parametrize('mutation',[None,'hash','sequence','unit','session','time','shape'])
def test_original_teardown_proof_references_bind_paired_m3_and_exact_context(tmp_path,mutation):
    f=Fixture(tmp_path,teardown_refs=True);args=f.arguments()
    if mutation:
        event=next(e for e in args['annotations'] if e['extensions']['xverse.maestro']['action']=='stop')
        p=event['extensions']['xverse.maestro'];m3,ref=p['sourceRefs']
        source=args['public_m3'][m3['sequence']-1];proof=source['details']['teardown']
        if mutation=='hash':ref['sha256']='sha256:'+'0'*64
        elif mutation=='sequence':ref['sequence']+=1
        else:
            if mutation=='unit':proof['unit']=f.a if proof['unit']!=f.a else f.b
            elif mutation=='session':proof['session']='foreign-session'
            elif mutation=='time':proof['observed_at']+=.1
            elif mutation=='shape':proof['privateAuthority']='forbidden'
            m3['sha256']=digest(source);ref['sha256']=digest(proof)
    report=assess_preclosure(f.admission,**args).report()
    if mutation is None:assert report['normalRecordStatus']=='complete'
    else:
        assert report['normalRecordStatus']!='complete'
        assert row(report,'stop',f.b,1)['status']=='conflicting'
    f.writer.abort(reason='Synthetic teardown reference control')


def test_completed_never_issued_unit_is_not_a_false_inactive_start(tmp_path):
    f=Fixture(tmp_path,failed=True);args=f.arguments()
    for e in args['annotations']:
        p=e['extensions']['xverse.maestro']
        if p['unitId']==f.b and p['action']=='disposition':p.update(disposition='completed',outcome='succeeded')
    report=assess_preclosure(f.admission,**args).report()
    assert row(report,'unit-disposition',f.b)['status']=='conflicting'
    assert row(report,'intent',f.b,1)['applicable'] is None
    assert any(r['status']=='conflicting' for r in report['rows'] if r['unitId']==f.b and r['obligationClass']=='step-disposition')
    assert report['normalRecordStatus']!='complete'
    f.writer.abort(reason='Synthetic impossible completion')
