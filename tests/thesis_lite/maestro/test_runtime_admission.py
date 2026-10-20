"""Joint preflight vectors: synthetic attestations, no execution/M1 approval."""
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest
from xverse.maestro.bootstrap import BootstrapAdmission, encode_bootstrap, seal_helper_image
from xverse.maestro.collection_plan import admit_collection
from xverse.maestro.coverage import ArtifactExpectation, admit_coverage
from xverse.maestro.persistence import encode_configuration
from xverse.maestro.persistence_worker import _decode_binding, _decode_approval
from xverse.maestro.providers import ProbePolicy
from xverse.maestro.public_blobs import admit_broker_artifact
from xverse.maestro.runtime_admission import (
    FacilityAttestation, RunAuthorization, RUNTIME_CASES, FENCE_PROPERTIES, HELPER_ROLES,
    admission_digest, validate_run_admission,
)
from xverse.maestro.schedule_plan import admit_schedule
from xverse.maestro.time import HostDeadline
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, configured
from .test_affa_native import authority_binary as authority_binary
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary


pin = lambda value: 'sha256:'+hashlib.sha256(value).hexdigest()


@pytest.fixture
def inputs(tmp_path, environment, binaries, authority_binary, run_bootstrap_binary):
    factory, _, _ = environment
    manager, _ = factory(seconds=45, run_id='fixture-run')
    original, _, work = configured(tmp_path, manager, dict(binaries, launcher=authority_binary))
    body = json.loads(original.private_bytes)
    bindings = tuple(_decode_binding(row) for row in body['bindings'])
    approvals = tuple(_decode_approval(row) for row in body['approvals'])
    prepared = original.prepared
    schedule = admit_schedule(prepared, policies=tuple(ProbePolicy(u.unit_id,5,5,.5) for u in prepared.units),
        ticks=(0,prepared.clock.horizon_ticks), active_seconds=4.8, operation_seconds=.5,
        per_unit_seconds=1, request_limit=512, service_operation_count=4)
    began = time.monotonic()
    coverage = admit_coverage(prepared, original.result, original.resources, run_id=original.run_id,
        host_session=original.session, contexts=[(b.unit_id,b.generation,b.execution_id) for b in bindings],
        health_policies={p.unit_id:(p.cadence_seconds,p.freshness_seconds) for p in schedule.policies},
        active_start=began, active_end=began+schedule.active_seconds,
        source_digests=(pin(schedule.canonical_bytes),),
        artifacts=[ArtifactExpectation('collection-result.json', maximum_bytes=4096)])
    st = work.stat()
    collection = admit_collection(coverage, expected_digest=coverage.digest, source_root=str(work),
        source_identity=(st.st_dev,st.st_ino), declarations=(), metadata_path='collection-result.json',
        operation_seconds=.5, per_unit_teardown_seconds=1, collection_seconds=2, terminal_seconds=2, drain_seconds=2)
    persistence = encode_configuration(prepared, original.result, original.resources, run_id=original.run_id,
        bindings=bindings, approvals=approvals, session=original.session,
        generation_deadline=manager._admission.teardown_deadline, journal_path=body['journal_path'],
        evidence_root=body['evidence_root'], schedule=schedule, coverage=coverage, collection=collection,
        broker_artifact=admit_broker_artifact(coverage, expected_digest=coverage.digest))
    paths = (binaries['launcher'],binaries['bound-gate'],Path(sys.executable).resolve(),authority_binary)
    images = tuple(seal_helper_image(path,digest=pin(path.read_bytes()),argv0=str(path)) for path in paths)
    try:
        boot = encode_bootstrap(BootstrapAdmission(original.run_id,prepared.lifecycle_digest,
            'synthetic-bootstrap-authorization',pin(b'synthetic-environment'),pin(run_bootstrap_binary.read_bytes()),
            manager._admission.teardown_deadline,HostDeadline(original.session,began+4.8),
            images[:3],images[3],manager._root_fd))
        artifacts = (boot.admission.supervisor_artifact_digest,*(i.digest for i in images))
        facility = FacilityAttestation(boot.admission.environment_digest,pin(b'synthetic-implementation'),
            pin(b'synthetic-design'),'synthetic-kernel-identity',tuple(zip(HELPER_ROLES,artifacts)),
            tuple((name,pin(('SYNTHETIC-NOT-EXECUTED:'+name).encode())) for name in RUNTIME_CASES),FENCE_PROPERTIES)
        now = datetime.now(timezone.utc)
        authorization = RunAuthorization(boot.admission.approval_ref,original.run_id,'sha256:'+prepared.lifecycle_digest,
            pin(persistence.private_bytes),pin(boot.private_bytes),admission_digest(facility),
            now-timedelta(seconds=1),now+timedelta(seconds=60),boot.admission.generation)
        kwargs = dict(expected_authorization_digest=admission_digest(authorization),expected_facility_digest=admission_digest(facility),
            expected_design_digest=facility.design_digest,expected_implementation_digest=facility.implementation_digest,
            expected_environment_digest=facility.environment_digest,now=now,host_now=HostDeadline(original.session,began+.001))
        yield persistence,boot,authorization,facility,kwargs
    finally:
        for image in images:
            os.close(image.descriptor)


def test_joint_read_only_pins_are_inert_and_no_sink_provider_or_child_is_created(inputs, monkeypatch):
    persistence,boot,authorization,facility,kwargs = inputs
    root = Path(json.loads(persistence.private_bytes)['journal_path']).parent
    before = {p.name for p in root.iterdir()}
    def forbidden(*args,**kw):
        pytest.fail('preflight attempted a mutation or execution')
    from xverse.argus import EvidenceStore
    from xverse.maestro.prbc import ProcessBoundaryOps
    from xverse_xdl.lifecycle import FileEvidenceJournal
    with monkeypatch.context() as patch:
        patch.setattr(subprocess,'Popen',forbidden)
        patch.setattr(EvidenceStore,'open_run',forbidden)
        patch.setattr(FileEvidenceJournal,'__init__',forbidden)
        patch.setattr(ProcessBoundaryOps,'create_frozen',forbidden)
        result = validate_run_admission(persistence,boot,authorization,facility,**kwargs)
    assert result.run_id == persistence.run_id and result.cleanup_until == boot.admission.generation
    assert not result.ready_for_execution and {p.name for p in root.iterdir()} == before
    with pytest.raises(FrozenInstanceError):
        result.run_id = 'changed'


@pytest.mark.parametrize('field', ['expected_authorization_digest','expected_facility_digest','expected_design_digest',
    'expected_implementation_digest','expected_environment_digest'])
def test_every_external_pin_is_required_and_bundle_rehash_cannot_replace_it(inputs,field):
    persistence,boot,authorization,facility,kwargs = inputs
    kwargs = dict(kwargs, **{field:pin(b'foreign')})
    with pytest.raises(ValueError):
        validate_run_admission(persistence,boot,authorization,facility,**kwargs)


@pytest.mark.parametrize('change', ['missing-case','duplicate-case','receipt-reuse','missing-property','wrong-helper',
    'mutable-rows','unknown-role','malformed-digest','kernel-identity'])
def test_facility_claim_universe_is_closed_even_with_a_new_caller_hash(inputs,change):
    persistence,boot,authorization,facility,kwargs = inputs
    values = facility.runtime_case_receipts
    if change == 'missing-case':facility=replace(facility,runtime_case_receipts=values[:-1])
    elif change == 'duplicate-case':facility=replace(facility,runtime_case_receipts=(*values[:-1],values[0]))
    elif change == 'receipt-reuse':facility=replace(facility,runtime_case_receipts=tuple((n,values[0][1]) for n,_ in values))
    elif change == 'missing-property':facility=replace(facility,enforced_properties=facility.enforced_properties[:-1])
    elif change == 'wrong-helper':facility=replace(facility,helper_artifacts=tuple((n,pin(b'foreign')) for n,_ in facility.helper_artifacts))
    elif change == 'mutable-rows':facility=replace(facility,runtime_case_receipts=list(values))
    elif change == 'unknown-role':facility=replace(facility,helper_artifacts=(('unknown',pin(b'x')), *facility.helper_artifacts[1:]))
    elif change == 'malformed-digest':facility=replace(facility,environment_digest='sha256:bad')
    else:facility=replace(facility,kernel_identity='')
    with pytest.raises(ValueError):
        digest=admission_digest(facility)
        authorization=replace(authorization,facility_digest=digest)
        kwargs=dict(kwargs,expected_facility_digest=digest,expected_authorization_digest=admission_digest(authorization))
        validate_run_admission(persistence,boot,authorization,facility,**kwargs)


@pytest.mark.parametrize('change', ['expired','future','naive-now','foreign-host','past-host','expired-lease',
    'changed-cleanup','changed-run','changed-lifecycle','changed-bootstrap-pin','changed-persistence-pin',
    'changed-facility-pin','unit-approval-reused'])
def test_authorization_never_extends_original_scope_or_mixes_clock_domains(inputs,change):
    persistence,boot,authorization,facility,kwargs=inputs
    if change=='expired':authorization=replace(authorization,expires_at=kwargs['now'])
    elif change=='future':authorization=replace(authorization,not_before=kwargs['now']+timedelta(seconds=1))
    elif change=='naive-now':kwargs=dict(kwargs,now=kwargs['now'].replace(tzinfo=None))
    elif change=='foreign-host':kwargs=dict(kwargs,host_now=replace(kwargs['host_now'],session='foreign'))
    elif change=='past-host':kwargs=dict(kwargs,host_now=replace(kwargs['host_now'],monotonic_seconds=0))
    elif change=='expired-lease':kwargs=dict(kwargs,host_now=boot.admission.lease)
    elif change=='changed-cleanup':authorization=replace(authorization,cleanup_until=replace(authorization.cleanup_until,monotonic_seconds=authorization.cleanup_until.monotonic_seconds+1))
    elif change=='changed-run':authorization=replace(authorization,run_id='foreign')
    elif change=='changed-lifecycle':authorization=replace(authorization,lifecycle_digest=pin(b'foreign'))
    elif change=='changed-bootstrap-pin':authorization=replace(authorization,bootstrap_digest=pin(b'foreign'))
    elif change=='changed-persistence-pin':authorization=replace(authorization,persistence_digest=pin(b'foreign'))
    elif change=='changed-facility-pin':authorization=replace(authorization,facility_digest=pin(b'foreign'))
    else:
        shared=json.loads(persistence.private_bytes)['approvals'][0]['approval_ref']
        authorization=replace(authorization,approval_ref=shared)
        boot=encode_bootstrap(replace(boot.admission,approval_ref=shared))
        authorization=replace(authorization,bootstrap_digest=pin(boot.private_bytes))
    kwargs=dict(kwargs,expected_authorization_digest=admission_digest(authorization))
    with pytest.raises(ValueError):
        validate_run_admission(persistence,boot,authorization,facility,**kwargs)


@pytest.mark.parametrize('change', ['private-bytes','config-prepared','generation','legacy','bootstrap-bytes','bootstrap-admission',
    'oversized-persistence','oversized-bootstrap','unavailable-image','nonbytes-persistence','nonbytes-bootstrap'])
def test_original_serializer_inputs_are_rederived_without_sinks(inputs,change):
    persistence,boot,authorization,facility,kwargs=inputs
    if change=='private-bytes':persistence=replace(persistence,private_bytes=persistence.private_bytes+b' ')
    elif change=='config-prepared':persistence=replace(persistence,prepared=None)
    elif change=='generation':persistence=replace(persistence,generation_ns=persistence.generation_ns+1)
    elif change=='legacy':
        body=json.loads(persistence.private_bytes);body['version']=5
        persistence=replace(persistence,private_bytes=json.dumps(body).encode())
    elif change=='bootstrap-bytes':boot=replace(boot,private_bytes=b'changed')
    elif change=='bootstrap-admission':boot=replace(boot,admission=None)
    elif change=='oversized-persistence':persistence=replace(persistence,private_bytes=b' '*(1048576+1))
    elif change=='oversized-bootstrap':boot=replace(boot,private_bytes=b' '*(65536+1))
    elif change=='unavailable-image':
        images=boot.admission.images
        boot=replace(boot,admission=replace(boot.admission,images=(replace(images[0],descriptor=1048576),*images[1:])))
    elif change=='nonbytes-persistence':persistence=replace(persistence,private_bytes='not-bytes')
    else:boot=replace(boot,private_bytes='not-bytes')
    authorization=replace(authorization,
        persistence_digest=pin(persistence.private_bytes) if type(persistence.private_bytes) is bytes else authorization.persistence_digest,
        bootstrap_digest=pin(boot.private_bytes) if type(boot.private_bytes) is bytes else authorization.bootstrap_digest)
    kwargs=dict(kwargs,expected_authorization_digest=admission_digest(authorization))
    with pytest.raises(ValueError):
        validate_run_admission(persistence,boot,authorization,facility,**kwargs)


def test_bootstrap_start_window_can_expire_before_original_cleanup_end_without_changing_either(inputs):
    persistence,boot,authorization,facility,kwargs=inputs
    authorization=replace(authorization,expires_at=kwargs['now']+timedelta(seconds=.01))
    kwargs=dict(kwargs,expected_authorization_digest=admission_digest(authorization))
    result=validate_run_admission(persistence,boot,authorization,facility,**kwargs)
    assert result.cleanup_until is authorization.cleanup_until
    with pytest.raises(ValueError):
        validate_run_admission(persistence,boot,authorization,facility,**dict(kwargs,now=authorization.expires_at))
