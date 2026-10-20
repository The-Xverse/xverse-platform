"""Joint read-only runtime preflight; no approval, capability or process creation.

The trusted admission owner supplies externally pinned authorization/attestation
facts and verifies their actual evidence. This module checks their exact bindings;
it neither authenticates that owner nor proves a live facility from declarations.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime
import hashlib
import math
import re

from xverse.argus.schema import canonical_bytes
from xverse_xdl.lifecycle import ExecutionPermit
from .admission import PermitApproval, PermitBinding
from .bootstrap import BootstrapAdmission, BootstrapInput, HelperImage, encode_bootstrap
from .persistence import MAX_CONFIG, PersistenceInput, _strict_json, encode_configuration
from .projection import PreparedLifecycle
from .time import HostDeadline


RUNTIME_CASES = (
    'test_affa', 'test_trusted_launcher', 'test_prbc', 'test_bounded_bootstrap',
    'test_atomic_release_cancel_stage', 'test_lease_loss',
    'test_pre_handle_crash_survival', 'test_residual_membership', 'test_unrelated_sentinel',
)
FENCE_PROPERTIES = (
    'frozen-before-child', 'pre-registered-exact-c1', 'atomic-release-cancel-epoch',
    'original-pidfd-waits', 'independent-watchdog', 'late-request-fenced', 'unrelated-scope-isolation',
)
HELPER_ROLES = ('supervisor', 'catalog', 'gate', 'python', 'authority')


class RuntimeAdmissionError(ValueError):
    pass


def _deny(reason):
    raise RuntimeAdmissionError('ML-RUNTIME-'+reason)


def _digest(value):
    if type(value) is not str or re.fullmatch(r'sha256:[0-9a-f]{64}', value) is None:
        _deny('DIGEST')


def _text(value):
    if type(value) is not str or not 0 < len(value) <= 128 or any(not 33 <= ord(c) <= 126 for c in value):
        _deny('IDENTITY')


def _aware(value):
    if type(value) is not datetime or value.utcoffset() is None:
        _deny('UTC')


@dataclass(frozen=True)
class FacilityAttestation:
    """Trusted-owner facts; referenced receipts are not verified by this parser."""
    environment_digest: str
    implementation_digest: str
    design_digest: str
    kernel_identity: str
    helper_artifacts: tuple[tuple[str, str], ...]
    runtime_case_receipts: tuple[tuple[str, str], ...]
    enforced_properties: tuple[str, ...]

    def canonical_bytes(self):
        for value in (self.environment_digest, self.implementation_digest, self.design_digest):
            _digest(value)
        _text(self.kernel_identity)
        for values, names in ((self.helper_artifacts, HELPER_ROLES), (self.runtime_case_receipts, RUNTIME_CASES)):
            if (type(values) is not tuple or len(values) != len(names)
                or any(type(row) is not tuple or len(row) != 2 for row in values)):
                _deny('FACILITY-SET')
            if tuple(row[0] for row in values) != names:
                _deny('FACILITY-SET')
            for _, digest in values:
                _digest(digest)
        if len({digest for _, digest in self.runtime_case_receipts}) != len(RUNTIME_CASES):
            _deny('FACILITY-RECEIPTS')
        if type(self.enforced_properties) is not tuple or self.enforced_properties != FENCE_PROPERTIES:
            _deny('FACILITY-PROPERTIES')
        return canonical_bytes(asdict(self))


@dataclass(frozen=True)
class RunAuthorization:
    """Separately supplied bootstrap approval facts, never self-issued approval."""
    approval_ref: str
    run_id: str
    lifecycle_digest: str
    persistence_digest: str
    bootstrap_digest: str
    facility_digest: str
    not_before: datetime
    expires_at: datetime
    cleanup_until: HostDeadline

    def canonical_bytes(self):
        _text(self.approval_ref)
        _text(self.run_id)
        for value in (self.lifecycle_digest, self.persistence_digest, self.bootstrap_digest, self.facility_digest):
            _digest(value)
        _aware(self.not_before)
        _aware(self.expires_at)
        if self.not_before >= self.expires_at:
            _deny('UTC-WINDOW')
        if type(self.cleanup_until) is not HostDeadline:
            _deny('HOST-END')
        self.cleanup_until.__post_init__()
        _text(self.cleanup_until.session)
        body = asdict(self)
        body['not_before'], body['expires_at'] = self.not_before.isoformat(), self.expires_at.isoformat()
        body['cleanup_until'] = dict(session=self.cleanup_until.session,
            monotonic_hex=float(self.cleanup_until.monotonic_seconds).hex())
        return canonical_bytes(body)


def admission_digest(value):
    if type(value) not in (FacilityAttestation, RunAuthorization):
        _deny('TYPE')
    return 'sha256:'+hashlib.sha256(b'xverse.maestro.runtime-admission.v1\0'+value.canonical_bytes()).hexdigest()


@dataclass(frozen=True)
class AdmissionPins:
    """Descriptive checked bindings, not a transferable execution capability."""
    run_id: str
    lifecycle_digest: str
    authorization_digest: str
    facility_digest: str
    persistence_digest: str
    bootstrap_digest: str
    cleanup_until: HostDeadline
    ready_for_execution: bool = field(default=False, init=False)


def _reencode(persistence, body, generation_deadline):
    bindings, approvals = [], []
    for row in body['bindings']:
        row = dict(row); permit = dict(row.pop('permit'))
        for key in ('not_before', 'expires_at'):
            permit[key] = datetime.fromisoformat(permit[key])
        for key in ('permitted_actions', 'operation_classes', 'exclusions'):
            permit[key] = tuple(permit[key])
        bindings.append(PermitBinding(**row, permit=ExecutionPermit(**permit)))
    for row in body['approvals']:
        row = dict(row)
        for key in ('not_before', 'expires_at'):
            row[key] = datetime.fromisoformat(row[key])
        row['artifact_digests'] = tuple(row['artifact_digests'])
        approvals.append(PermitApproval(**row))
    return encode_configuration(persistence.prepared, persistence.result, persistence.resources,
        run_id=persistence.run_id, bindings=tuple(bindings), approvals=tuple(approvals),
        session=persistence.session, generation_deadline=generation_deadline,
        journal_path=body['journal_path'], evidence_root=body['evidence_root'],
        schedule=persistence.schedule, future_contexts=persistence.future_contexts,
        public_exports=persistence.public_exports, coverage=persistence.coverage,
        broker_artifact=persistence.broker_artifact, collection=persistence.collection)


def validate_run_admission(persistence, bootstrap, authorization, facility, *,
        expected_authorization_digest, expected_facility_digest, expected_design_digest,
        expected_implementation_digest, expected_environment_digest, now, host_now):
    """Recheck exact existing inputs before any helper, sink or C1 mutation.

    Expected pins come from the trusted admission owner, outside these records.
    Live descriptor/artifact/facility checks remain mandatory at execution use.
    """
    if (type(persistence) is not PersistenceInput or type(bootstrap) is not BootstrapInput
        or type(authorization) is not RunAuthorization or type(facility) is not FacilityAttestation):
        _deny('TYPE')
    if (type(persistence.private_bytes) is not bytes or not 0 < len(persistence.private_bytes) <= MAX_CONFIG
        or type(bootstrap.private_bytes) is not bytes or not 0 < len(bootstrap.private_bytes) <= 65536):
        _deny('INPUT-LIMIT')
    for value in (expected_authorization_digest, expected_facility_digest, expected_design_digest,
                  expected_implementation_digest, expected_environment_digest):
        _digest(value)
    if admission_digest(authorization) != expected_authorization_digest:
        _deny('AUTHORIZATION-PIN')
    if admission_digest(facility) != expected_facility_digest:
        _deny('FACILITY-PIN')
    if (facility.design_digest != expected_design_digest or facility.implementation_digest != expected_implementation_digest
        or facility.environment_digest != expected_environment_digest):
        _deny('EXTERNAL-PINS')
    _aware(now)
    if not authorization.not_before <= now < authorization.expires_at:
        _deny('START-WINDOW')
    if type(host_now) is not HostDeadline:
        _deny('HOST-NOW')
    host_now.__post_init__()
    _text(host_now.session)
    boot = bootstrap.admission
    if (type(boot) is not BootstrapAdmission or type(persistence.prepared) is not PreparedLifecycle
        or type(boot.images) is not tuple or len(boot.images) != 3
        or any(type(image) is not HelperImage for image in boot.images)
        or type(boot.authority_image) is not HelperImage
        or type(boot.generation) is not HostDeadline or type(boot.lease) is not HostDeadline
        or type(persistence.generation_ns) is not int):
        _deny('ORIGINAL-INPUT')
    if (bootstrap.version != 2 or persistence.session != host_now.session
        or boot.generation.session != host_now.session or boot.lease.session != host_now.session
        or authorization.cleanup_until != boot.generation
        or persistence.generation_ns != int(boot.generation.monotonic_seconds*1e9)):
        _deny('ORIGINAL-END')
    if not 0 < boot.lease.monotonic_seconds-host_now.monotonic_seconds <= 5:
        _deny('LEASE')
    if (authorization.run_id != persistence.run_id or boot.run_id != persistence.run_id
        or authorization.lifecycle_digest != 'sha256:'+persistence.prepared.lifecycle_digest
        or boot.lifecycle_digest != persistence.prepared.lifecycle_digest
        or boot.approval_ref != authorization.approval_ref
        or boot.environment_digest != expected_environment_digest):
        _deny('SCOPE')
    helpers = (boot.supervisor_artifact_digest, *(image.digest for image in boot.images), boot.authority_image.digest)
    if tuple(digest for _,digest in facility.helper_artifacts) != helpers:
        _deny('HELPER-PINS')
    try:
        body = _strict_json(persistence.private_bytes)
        if (body['version'] != 6 or persistence.schedule is None or persistence.coverage is None
            or persistence.collection is None or persistence.broker_artifact is None):
            _deny('FULL-LIFECYCLE-INPUT')
        if authorization.approval_ref in {a['approval_ref'] for a in body['approvals']}:
            _deny('SEPARATE-BOOTSTRAP-APPROVAL')
        rebuilt = _reencode(persistence, body, boot.generation)
        if rebuilt.private_bytes != persistence.private_bytes or encode_bootstrap(boot) != bootstrap:
            _deny('ORIGINAL-INPUT')
    except RuntimeAdmissionError:
        raise
    except (ValueError, OSError, TypeError, KeyError, AttributeError, OverflowError) as error:
        raise RuntimeAdmissionError('ML-RUNTIME-ORIGINAL-INPUT') from error
    persistence_digest = 'sha256:'+hashlib.sha256(persistence.private_bytes).hexdigest()
    bootstrap_digest = 'sha256:'+hashlib.sha256(bootstrap.private_bytes).hexdigest()
    if (authorization.persistence_digest != persistence_digest or authorization.bootstrap_digest != bootstrap_digest
        or authorization.facility_digest != expected_facility_digest):
        _deny('INPUT-PINS')
    coverage = persistence.coverage.data(persistence.coverage.digest)
    if not coverage['start'] <= host_now.monotonic_seconds < coverage['end']:
        _deny('ACTIVE-WINDOW')
    reserve = (persistence.schedule.terminal_reserve_seconds+persistence.collection.collection_seconds
        +persistence.collection.terminal_seconds+persistence.collection.drain_seconds)
    if not math.isfinite(reserve) or coverage['end']+reserve > boot.generation.monotonic_seconds:
        _deny('TERMINAL-RESERVE')
    return AdmissionPins(persistence.run_id, authorization.lifecycle_digest, expected_authorization_digest,
        expected_facility_digest, persistence_digest, bootstrap_digest, boot.generation)
