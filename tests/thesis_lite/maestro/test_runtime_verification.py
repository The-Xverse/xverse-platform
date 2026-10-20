"""TR02/TR05 synthetic observations through actual accepted Argus writer/reader.

No native runtime, worker orchestration, helper cleanup or scientific result is
established by these controls. The universe is externally fixed before writing.
"""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.artifacts import ArtifactDeclaration
from xverse.maestro.collection_plan import admit_collection
from xverse.maestro.collection_runtime import document
from xverse.maestro.coverage import ArtifactExpectation, CoverageError, admit_coverage, canonical
from xverse.maestro.runtime_verification import runtime_admission_digest, verify_runtime_closed
from .test_coverage import Fixture


class RuntimeFixture(Fixture):
    generation_ns=10_000_000_000
    collection_started_at=4.5
    collection_finished_at=4.51
    collection_event_at=4.52
    collection_context_observed_at=4.45
    final_observed_at=4.8

    def __init__(self,path,mutation=None):
        self.source=path/'source';self.source.mkdir()
        self.mutation=mutation
        self.runtime_entries=[];self.runtime_bytes={}
        super().__init__(path,required_output=True)

    def emit(self,action,unit,t,**kw):
        if action=='validate' and not hasattr(self,'collection_plan'):
            self.admission=admit_coverage(self.prepared,self.result,self.resources,
                run_id=self.ad['runId'],host_session=self.ad['hostSession'],
                contexts=[(r['unitId'],r['generation'],r['executionId']) for r in self.ad['contexts']],
                health_policies={u.unit_id:(1,5) for u in self.units},active_start=0,active_end=5,
                artifacts=[ArtifactExpectation('synthetic-output.json',True,32,self.a,1),
                           ArtifactExpectation('collection.json',True,16384)])
            self.ad=self.admission.data(self.admission.digest)
            stat=self.source.stat()
            self.collection_plan=admit_collection(self.admission,expected_digest=self.admission.digest,
                source_root=str(self.source),source_identity=(stat.st_dev,stat.st_ino),
                declarations=[ArtifactDeclaration(self.a,1,'payload','synthetic-output.json',media_type='application/json')],
                metadata_path='collection.json',operation_seconds=.5,per_unit_teardown_seconds=.1,
                collection_seconds=2,terminal_seconds=.5,drain_seconds=.5)
        if action=='collect':
            self.broker.update(observedAt=self.final_observed_at,cancellationRequested=True,nativeCancellationAcknowledged=True)
            self.broker['epochs'].append(dict(kind='cancelled',epoch=1,sequence=1))
            for row in self.broker['generations']:
                row.update(c1Empty=True,c1TerminationObserved=True)
            context=dict(schemaVersion='1.0',broker=deepcopy(self.broker),
                authority=dict(issuerDead=False,issuerReaped=False),collectionDeadlineNs=6_000_000_000)
            context['broker']['observedAt']=self.collection_context_observed_at
            raw=b'{"synthetic":true}'
            self.index('synthetic-output.json',raw)
            entry=self.runtime_entries[-1]
            items=[dict(unitId=self.a,generation=1,source='payload',destination='synthetic-output.json',
                required=True,mediaType='application/json',status='collected',bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest(),diagnostic=None,entry=entry)]
            if self.mutation=='shrink-items':items=[]
            if self.mutation=='lost-quiescence':context['broker']['generations'][0].update(c1Empty=False,c1Released=False)
            if self.mutation=='shrink-units':context['broker']['generations'].pop()
            body=document(self.collection_plan,context,items,self.collection_started_at,self.collection_finished_at)
            if self.mutation=='substitute-plan':body['collectionPlanDigest']='sha256:'+'0'*64
            if self.mutation=='changed-source-identity':body['sourceRootIdentity']=[0,0]
            raw=canonical(body);self.index('collection.json',raw)
            digest=hashlib.sha256(raw).hexdigest()
            kw['annotation_text']='Maestro original declared collection sha256:'+('0'*64 if self.mutation=='changed-event-hash' else digest)
            t=self.collection_event_at
        return super().emit(action,unit,t,**kw)

    def index(self,path,data):
        (self.root/path).write_bytes(data)
        self.runtime_entries.append(self.writer.record_artifact(path,media_type='application/json',schema_version='1.0',role='evidence'))
        self.runtime_bytes[path]=data

    def arguments(self):
        if self.mutation=='changed-final-handle':self.broker['generations'][0]['handleRef']='handle-'+'0'*64
        if self.mutation=='stale-final':self.broker['observedAt']=4.49
        result=super().arguments()
        result['artifact_entries']+=self.runtime_entries
        result['artifact_bytes'].update(self.runtime_bytes)
        return result

    def provisional(self):
        from xverse.maestro.coverage import assess_preclosure
        from xverse.maestro.evidence_scope import RuntimeEvidenceScope
        from .test_coverage import VALIDATOR
        result=assess_preclosure(self.admission,**self.arguments(),
            runtime_scope=RuntimeEvidenceScope(self.collection_plan.canonical_bytes,self.generation_ns),
            expected_runtime_digest=self.pins['expected_runtime_digest'])
        VALIDATOR.validate(result.report())
        return result

    @property
    def pins(self):
        return dict(expected_admission_digest=self.admission.digest,
            expected_runtime_digest=runtime_admission_digest(self.admission,self.collection_plan,self.generation_ns),
            generation_ns=self.generation_ns)

    def verify(self,**changes):
        return verify_runtime_closed(self.admission,self.collection_plan,self.root,**dict(self.pins,**changes))


def test_closed_original_collection_and_actual_reader_are_verified_read_only(tmp_path):
    f=RuntimeFixture(tmp_path);f.close()
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in f.root.iterdir() if p.is_file()}
    result=f.verify()
    assert result.collection_verified and result.collection_complete and result.complete
    assert not result.diagnostics
    assert json.loads(result.lifecycle.accepted_annotation_bytes)==f.events
    assert result.lifecycle.manifest_sha256==hashlib.sha256((f.root/'manifest.json').read_bytes()).hexdigest()
    assert before=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in f.root.iterdir() if p.is_file()}


@pytest.mark.parametrize('mutation,code',[
    ('shrink-items','ML-RUNTIME-COLLECTION-UNIVERSE'),
    ('substitute-plan','ML-RUNTIME-COLLECTION-DOCUMENT'),
    ('changed-source-identity','ML-RUNTIME-COLLECTION-DOCUMENT'),
    ('shrink-units','ML-EVIDENCE-BLOB-BROKER'),
    ('lost-quiescence','ML-RUNTIME-COLLECTION-OWNERSHIP'),
    ('changed-final-handle','ML-RUNTIME-COLLECTION-FINAL-FACTS'),
    ('stale-final','ML-RUNTIME-COLLECTION-FINAL-TIME'),
    ('changed-event-hash','ML-RUNTIME-COLLECTION-EVENT'),
])
def test_self_consistent_artifacts_cannot_replace_original_runtime_universe(tmp_path,mutation,code):
    f=RuntimeFixture(tmp_path,mutation);f.close()
    result=f.verify()
    assert not result.collection_verified and not result.complete
    assert result.diagnostics==(code,)


@pytest.mark.parametrize('change',['pin','generation','plan'])
def test_external_admission_substitution_is_rejected_before_evidence_io(tmp_path,monkeypatch,change):
    f=RuntimeFixture(tmp_path)
    from xverse.maestro import runtime_verification
    monkeypatch.setattr(runtime_verification,'verify_closed',lambda *a,**kw:pytest.fail('read before admission'))
    plan=f.collection_plan;pins=f.pins
    if change=='pin':pins['expected_runtime_digest']='sha256:'+'0'*64
    if change=='generation':pins['generation_ns']+=1
    if change=='plan':plan=replace(plan,source_identity=(0,0))
    try:
        with pytest.raises(CoverageError,match='ML-RUNTIME-ADMISSION-PIN'):
            verify_runtime_closed(f.admission,plan,f.root,**pins)
    finally:f.writer.abort(reason='Synthetic external-pin control')


def test_invalid_manifest_cannot_invoke_an_unbounded_second_reader(tmp_path,monkeypatch):
    f=RuntimeFixture(tmp_path);f.close()
    raw=json.loads((f.root/'manifest.json').read_bytes())
    raw['artifacts'].append(dict(path='unadmitted.json',bytes=1<<30))
    (f.root/'manifest.json').write_bytes(canonical(raw))
    monkeypatch.setattr(EvidenceStore,'read_run',lambda *a,**kw:pytest.fail('unbounded accepted reader'))
    result=f.verify()
    assert not result.collection_verified and result.diagnostics==('ML-RUNTIME-CLOSED-READER',)


def test_collected_destination_changed_after_closure_is_rejected(tmp_path):
    f=RuntimeFixture(tmp_path);f.close()
    (f.root/'synthetic-output.json').write_bytes(b'changed')
    result=f.verify()
    assert not result.collection_verified and result.diagnostics==('ML-RUNTIME-COLLECTION-INDEX',)
    assert not result.complete
