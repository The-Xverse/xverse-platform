"""SYNTHETIC/INERT service vectors; final start stubbed, all effects forbidden."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import copy
import os
import subprocess

import pytest
from xverse.maestro.runtime_admission import FacilityAttestation,RunAuthorization,RUNTIME_CASES,FENCE_PROPERTIES,HELPER_ROLES,admission_digest
from xverse.maestro.runtime_evidence import RuntimeEvidenceFiles
from xverse.maestro.runtime_entry import _OriginalRuntimeRun,_OriginalRuntimeRegistry
from xverse.maestro.runtime_service import ApprovedRuntime,RuntimeReadiness,ReadinessFiles,RuntimeSubmission,RuntimeService,readiness_digest
from .test_runtime_entry import runtime as runtime
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries,deadline
from .test_affa_native import authority_binary as authority_binary
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_bootstrap_launcher import pin


@pytest.fixture
def service_data(runtime,tmp_path,monkeypatch):
    from xverse.argus import EvidenceStore
    from xverse_xdl.lifecycle import FileEvidenceJournal
    from xverse.maestro.prbc import ProcessBoundaryOps
    def forbidden(*a,**kw):pytest.fail('SYNTHETIC service vector attempted process/C1/sink effect')
    monkeypatch.setattr(subprocess,'Popen',forbidden)
    monkeypatch.setattr(ProcessBoundaryOps,'create_frozen',forbidden)
    monkeypatch.setattr(EvidenceStore,'open_run',forbidden)
    monkeypatch.setattr(FileEvidenceJournal,'__init__',forbidden)
    entry,scope,work=runtime;fds=[];counter=[]
    def build(*,ready_changes=None,expires=30):
        counter.append(True);directory=tmp_path/('inert-service-'+str(len(counter)));directory.mkdir()
        config,launcher,_=entry._pins[:3];boot=launcher.config
        artifacts=(boot.admission.supervisor_artifact_digest,*(i.digest for i in (*boot.admission.images,boot.admission.authority_image)))
        blobs={name:('SYNTHETIC-INERT-NOT-EXECUTED:'+name).encode() for name in RUNTIME_CASES}
        facility=FacilityAttestation(boot.admission.environment_digest,pin(b'synthetic-implementation'),pin(b'synthetic-design'),
            os.uname().release,tuple(zip(HELPER_ROLES,artifacts)),tuple((name,pin(blobs[name])) for name in RUNTIME_CASES),FENCE_PROPERTIES)
        now=datetime.now(timezone.utc)
        authorization=RunAuthorization(boot.admission.approval_ref,config.run_id,'sha256:'+config.prepared.lifecycle_digest,
            pin(config.private_bytes),pin(boot.private_bytes),admission_digest(facility),now-timedelta(seconds=60),now+timedelta(seconds=expires),boot.admission.generation)
        blobs.update(authorization=authorization.canonical_bytes(),facility=facility.canonical_bytes(),
            source=b'SYNTHETIC-INERT-SOURCE-REVIEW-NOT-APPROVED',verification=b'SYNTHETIC-INERT-VERIFICATION-NOT-EXECUTED')
        ready=RuntimeReadiness('synthetic-readiness-unit-vector',admission_digest(authorization),admission_digest(facility),
            facility.design_digest,facility.implementation_digest,facility.environment_digest,pin(blobs['source']),pin(blobs['verification']),
            18,RUNTIME_CASES,True,True,True,True,())
        if ready_changes:ready=replace(ready,**ready_changes)
        blobs['readiness']=ready.canonical_bytes();paths={};opened={}
        for name,data in blobs.items():
            path=directory/name;path.write_bytes(data);paths[name]=path
            opened[name]=os.open(path,os.O_RDONLY|os.O_CLOEXEC);fds.append(opened[name])
        evidence=RuntimeEvidenceFiles(opened['authorization'],opened['facility'],tuple((name,opened[name]) for name in RUNTIME_CASES))
        request=RuntimeSubmission(entry,authorization,facility,evidence,ready,ReadinessFiles(opened['readiness'],opened['source'],opened['verification']))
        policy=ApprovedRuntime(config.run_id,admission_digest(authorization),admission_digest(facility),readiness_digest(ready),
            facility.design_digest,facility.implementation_digest,facility.environment_digest)
        return request,policy,paths
    try:yield entry,scope,build
    finally:
        assert not entry._pins[1]._birth_attempted and not entry._pins[1].boundaries._entries
        for fd in fds:os.close(fd)


def test_default_closed_and_inspection_never_creates_execution_authority(service_data):
    entry,scope,build=service_data;request,policy,_=build()
    with pytest.raises(ValueError,match='NOT-APPROVED'):RuntimeService().inspect(request,deadline=deadline(1))
    service=RuntimeService((policy,))
    checked=service.inspect(request,deadline=deadline(1))
    assert not checked.ready_for_execution and not checked.admission.ready_for_execution
    with pytest.raises(ValueError,match='DISABLED'):service.register(request,deadline=deadline(1))
    assert entry._registry_owner is None and entry._pins[1]._start_window is None
    with pytest.raises(TypeError):copy.copy(service)


def test_service_wiring_uses_original_registry_with_final_start_stubbed(service_data,monkeypatch):
    entry,scope,build=service_data;request,policy,_=build()
    service=RuntimeService((policy,),execution_enabled=True);calls=[];sentinel=object()
    monkeypatch.setattr(_OriginalRuntimeRun,'start',lambda self,value:(calls.append((self,value)),sentinel)[1])
    assert service.register(request,deadline=deadline(1)) is entry
    assert service.register(request,deadline=deadline(1)) is entry
    assert service.start('fixture-run',scope) is sentinel
    assert calls==[(entry,scope)] and service._registry._run('fixture-run') is entry
    assert entry._pins[1]._start_window.authorization is request.authorization
    assert not entry._pins[1]._birth_attempted and entry._result is None


@pytest.mark.parametrize('field',['source_dispositions_approved','verification_complete','independent_review_recorded','execution_approved','blocking_findings'])
def test_draft_partial_or_blocked_review_rejects_even_when_hash_is_allowed(service_data,field):
    entry,_,build=service_data
    request,policy,_=build(ready_changes={field:('ML-CAPA-286',) if field=='blocking_findings' else False})
    with pytest.raises(ValueError,match='READINESS-BLOCKED'):
        RuntimeService((policy,),execution_enabled=True).register(request,deadline=deadline(1))
    assert entry._registry_owner is None and entry._pins[1]._start_window is None


@pytest.mark.parametrize('field',['authorization_digest','facility_digest','readiness_digest','design_digest','implementation_digest','environment_digest'])
def test_external_policy_pins_cannot_be_replaced_by_bundle_rehash(service_data,field):
    entry,_,build=service_data;request,policy,_=build()
    changed=replace(policy,**{field:pin(b'foreign-external-pin')})
    with pytest.raises(ValueError):RuntimeService((changed,),execution_enabled=True).register(request,deadline=deadline(1))
    assert entry._registry_owner is None and entry._pins[1]._start_window is None


@pytest.mark.parametrize('name',['readiness','source','verification','authorization','facility','test_affa'])
def test_changed_actual_review_or_receipt_bytes_prevent_registration(service_data,name):
    entry,_,build=service_data;request,policy,paths=build();paths[name].write_bytes(b'changed')
    with pytest.raises(ValueError):RuntimeService((policy,),execution_enabled=True).register(request,deadline=deadline(1))
    assert entry._registry_owner is None


def test_original_reservation_conflicts_do_not_bind_or_widen_start_window(service_data):
    entry,_,build=service_data;request,policy,_=build();service=RuntimeService((policy,),execution_enabled=True)
    entry._lock.acquire()
    try:
        with pytest.raises(ValueError,match='CONFLICT'):service.register(request,deadline=deadline(1))
    finally:entry._lock.release()
    assert entry._pins[1]._start_window is None and entry._registry_owner is None
    _OriginalRuntimeRegistry(1).reserve(entry)
    with pytest.raises(ValueError,match='REGISTRY-ORIGINAL'):service.register(request,deadline=deadline(1))
    assert entry._pins[1]._start_window is None


def test_changed_repeat_and_metadata_corruption_block_ordinary_access_but_not_stop(service_data):
    entry,_,build=service_data;request,policy,_=build();service=RuntimeService((policy,),execution_enabled=True)
    service.register(request,deadline=deadline(1))
    with pytest.raises(ValueError,match='REPEAT'):service.register(replace(request),deadline=deadline(1))
    object.__setattr__(request.authorization,'approval_ref','changed')
    with pytest.raises(ValueError,match='SERVICE-REPLACED'):service.collect('fixture-run')
    assert service.stop('fixture-run',reason='inert-corruption-stop')==1
    assert entry._pins[1].boundaries._latch.cancelled


def test_authorization_and_files_are_revalidated_at_first_start(service_data,monkeypatch):
    entry,scope,build=service_data;request,policy,paths=build();service=RuntimeService((policy,),execution_enabled=True)
    service.register(request,deadline=deadline(1));calls=[]
    monkeypatch.setattr(_OriginalRuntimeRun,'start',lambda *a:calls.append(True))
    paths['source'].write_bytes(b'changed-after-register')
    with pytest.raises(ValueError,match='READINESS-BYTES'):service.start('fixture-run',scope)
    assert not calls and not entry._pins[1]._birth_attempted


def test_actual_expired_authorization_and_malformed_ids_deadlines_reject(service_data):
    entry,_,build=service_data;request,policy,_=build(expires=-1);service=RuntimeService((policy,),execution_enabled=True)
    with pytest.raises(ValueError,match='START-WINDOW'):service.register(request,deadline=deadline(1))
    with pytest.raises(ValueError,match='DEADLINE'):service.inspect(request,deadline=object())
    with pytest.raises(ValueError,match='IDENTITY'):service.collect([])
    assert entry._registry_owner is None
