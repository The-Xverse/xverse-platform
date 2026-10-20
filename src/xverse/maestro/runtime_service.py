"""Candidate host admission facade; no top-level export or approval signer.

The trusted host must authenticate and review approvals before configuring the
fixed allowlist. Hashes/declarations here never prove that review happened.
Execution defaults closed; synthetic records are not actual M1 permission.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import threading

from xverse.argus.schema import canonical_bytes
from .owner import _Original, OwnerError, _deadline
from .runtime_admission import (
    FacilityAttestation, RunAuthorization, RUNTIME_CASES, admission_digest, _digest, _text,
)
from .runtime_entry import _OriginalRuntimeRun, _OriginalRuntimeRegistry, RuntimeScope
from .runtime_evidence import RuntimeEvidenceFiles, RuntimeEvidencePins, _file, verify_runtime_evidence
from .time import HostDeadline


def _pin(data):return 'sha256:'+hashlib.sha256(data).hexdigest()


class RuntimeServiceError(OwnerError):
    pass


@dataclass(frozen=True)
class ApprovedRuntime:
    """Fixed trusted-host pins, supplied outside a submitted run request."""
    run_id: str
    authorization_digest: str
    facility_digest: str
    readiness_digest: str
    design_digest: str
    implementation_digest: str
    environment_digest: str

    def canonical_bytes(self):
        _text(self.run_id)
        for name in self.__dataclass_fields__:
            if name!='run_id':_digest(getattr(self,name))
        return canonical_bytes(asdict(self))


@dataclass(frozen=True)
class RuntimeReadiness:
    """Externally reviewed statements, not self-authenticating approval."""
    approval_ref: str
    authorization_digest: str
    facility_digest: str
    design_digest: str
    implementation_digest: str
    environment_digest: str
    source_review_digest: str
    verification_review_digest: str
    source_parent_count: int
    runtime_cases: tuple[str,...]
    source_dispositions_approved: bool
    verification_complete: bool
    independent_review_recorded: bool
    execution_approved: bool
    blocking_findings: tuple[str,...]

    def canonical_bytes(self):
        _text(self.approval_ref)
        for name in ('authorization_digest','facility_digest','design_digest','implementation_digest',
                     'environment_digest','source_review_digest','verification_review_digest'):
            _digest(getattr(self,name))
        if (type(self.source_parent_count) is not int or self.source_parent_count!=18
            or type(self.runtime_cases) is not tuple or self.runtime_cases!=RUNTIME_CASES
            or type(self.blocking_findings) is not tuple or len(self.blocking_findings)>128):
            raise RuntimeServiceError('ML-RUNTIME-READINESS-SCOPE')
        for value in self.blocking_findings:_text(value)
        if any(type(getattr(self,n)) is not bool for n in ('source_dispositions_approved',
            'verification_complete','independent_review_recorded','execution_approved')):
            raise RuntimeServiceError('ML-RUNTIME-READINESS-FLAGS')
        return canonical_bytes(asdict(self))


def readiness_digest(value):
    if type(value) is not RuntimeReadiness:raise RuntimeServiceError('ML-RUNTIME-READINESS-TYPE')
    return _pin(b'xverse.maestro.runtime-readiness.v1\0'+value.canonical_bytes())


@dataclass(frozen=True)
class ReadinessFiles:
    approval: int = field(repr=False)
    source_review: int = field(repr=False)
    verification_review: int = field(repr=False)


@dataclass(frozen=True)
class RuntimeSubmission:
    run: _OriginalRuntimeRun = field(repr=False)
    authorization: RunAuthorization
    facility: FacilityAttestation
    evidence: RuntimeEvidenceFiles = field(repr=False)
    readiness: RuntimeReadiness
    reviews: ReadinessFiles = field(repr=False)


class _StartWindow(_Original):
    """A restriction on separately owned bootstrap authority, never a grant."""
    def __init__(self,authorization,expected_digest,bootstrap):
        if type(authorization) is not RunAuthorization or admission_digest(authorization)!=expected_digest:
            raise RuntimeServiceError('ML-RUNTIME-START-AUTHORIZATION')
        boot=bootstrap.admission
        if (authorization.run_id!=boot.run_id or authorization.approval_ref!=boot.approval_ref
            or authorization.lifecycle_digest!='sha256:'+boot.lifecycle_digest
            or authorization.bootstrap_digest!=_pin(bootstrap.private_bytes)
            or authorization.cleanup_until!=boot.generation):
            raise RuntimeServiceError('ML-RUNTIME-START-AUTHORIZATION')
        self._retain()
        self.authorization,self.bootstrap=authorization,bootstrap
        self._pins=(authorization,bootstrap,expected_digest,bootstrap.private_bytes)

    def _holder(self):
        super()._holder()
        if (self.authorization is not self._pins[0] or self.bootstrap is not self._pins[1]
            or admission_digest(self.authorization)!=self._pins[2] or self.bootstrap.private_bytes!=self._pins[3]):
            raise RuntimeServiceError('ML-RUNTIME-START-AUTHORIZATION-REPLACED')

    def check(self):
        self._holder()
        if not self.authorization.not_before<=datetime.now(timezone.utc)<self.authorization.expires_at:
            raise RuntimeServiceError('ML-RUNTIME-START-WINDOW')


class RuntimeService(_Original):
    """Candidate interface for a trusted host; empty/disabled policy cannot start."""
    def __init__(self,approved_runs=(),*,execution_enabled=False,maximum_runs=128):
        if (type(approved_runs) is not tuple or len(approved_runs)>128
            or any(type(p) is not ApprovedRuntime for p in approved_runs) or type(execution_enabled) is not bool):
            raise RuntimeServiceError('ML-RUNTIME-SERVICE-POLICY')
        snapshots=tuple(p.canonical_bytes() for p in approved_runs)
        if len({p.run_id for p in approved_runs})!=len(approved_runs):
            raise RuntimeServiceError('ML-RUNTIME-SERVICE-POLICY')
        self._retain()
        self._approved=self._approved_pin=approved_runs
        self._policy_bytes=snapshots
        self._enabled=self._enabled_pin=execution_enabled
        self._registry=self._registry_pin=_OriginalRuntimeRegistry(maximum_runs)
        self._entries=self._entries_pin={}
        self._log=()
        self._lock=threading.Lock()

    def _holder(self):
        super()._holder()
        if (self._approved is not self._approved_pin or self._enabled is not self._enabled_pin
            or tuple(p.canonical_bytes() for p in self._approved)!=self._policy_bytes
            or self._registry is not self._registry_pin or self._entries is not self._entries_pin
            or tuple(self._entries.items())!=self._log):
            raise RuntimeServiceError('ML-RUNTIME-SERVICE-REPLACED')
        self._registry._holder()

    def _binding(self,request):
        if (type(request) is not RuntimeSubmission or type(request.run) is not _OriginalRuntimeRun
            or type(request.authorization) is not RunAuthorization or type(request.facility) is not FacilityAttestation
            or type(request.evidence) is not RuntimeEvidenceFiles or type(request.readiness) is not RuntimeReadiness
            or type(request.reviews) is not ReadinessFiles):
            raise RuntimeServiceError('ML-RUNTIME-SERVICE-INPUT')
        evidence=request.evidence;reviews=request.reviews
        if (type(evidence.runtime_cases) is not tuple or len(evidence.runtime_cases)!=len(RUNTIME_CASES)
            or any(type(row) is not tuple or len(row)!=2 for row in evidence.runtime_cases)
            or tuple(row[0] for row in evidence.runtime_cases)!=RUNTIME_CASES
            or any(type(fd) is not int or fd<0 for fd in (evidence.authorization,evidence.facility,
                *(row[1] for row in evidence.runtime_cases),reviews.approval,reviews.source_review,reviews.verification_review))):
            raise RuntimeServiceError('ML-RUNTIME-SERVICE-FILES')
        return (request.run,request.authorization.canonical_bytes(),request.facility.canonical_bytes(),
            request.readiness.canonical_bytes(),(evidence.authorization,evidence.facility,evidence.runtime_cases),
            (reviews.approval,reviews.source_review,reviews.verification_review))

    def inspect(self,request,*,deadline):
        self._holder();self._binding(request);request.run._holder()
        if type(deadline) is not HostDeadline:raise RuntimeServiceError('ML-RUNTIME-SERVICE-DEADLINE')
        _deadline(deadline,request.run._pins[0].session)
        policy=next((p for p in self._approved if p.run_id==request.authorization.run_id),None)
        if policy is None:raise RuntimeServiceError('ML-RUNTIME-SERVICE-NOT-APPROVED')
        ready=request.readiness
        if (readiness_digest(ready)!=policy.readiness_digest or ready.authorization_digest!=policy.authorization_digest
            or ready.facility_digest!=policy.facility_digest or ready.design_digest!=policy.design_digest
            or ready.implementation_digest!=policy.implementation_digest or ready.environment_digest!=policy.environment_digest):
            raise RuntimeServiceError('ML-RUNTIME-READINESS-PIN')
        if (not ready.source_dispositions_approved or not ready.verification_complete
            or not ready.independent_review_recorded or not ready.execution_approved or ready.blocking_findings):
            raise RuntimeServiceError('ML-RUNTIME-READINESS-BLOCKED')
        if (_file(request.reviews.approval,deadline)!=ready.canonical_bytes()
            or _pin(_file(request.reviews.source_review,deadline))!=ready.source_review_digest
            or _pin(_file(request.reviews.verification_review,deadline))!=ready.verification_review_digest):
            raise RuntimeServiceError('ML-RUNTIME-READINESS-BYTES')
        run=request.run;launcher=run._pins[1]
        return verify_runtime_evidence(run._pins[0],launcher.config,request.authorization,request.facility,
            request.evidence,launcher.boundaries,deadline=deadline,
            expected_authorization_digest=policy.authorization_digest,expected_facility_digest=policy.facility_digest,
            expected_design_digest=policy.design_digest,expected_implementation_digest=policy.implementation_digest,
            expected_environment_digest=policy.environment_digest)

    def register(self,request,*,deadline):
        self._holder()
        if not self._enabled:raise RuntimeServiceError('ML-RUNTIME-SERVICE-DISABLED')
        binding=self._binding(request);key=request.run._pins[0].run_id
        if not self._lock.acquire(False):raise RuntimeServiceError('ML-RUNTIME-SERVICE-CONFLICT')
        try:
            old=self._entries.get(key)
            if old is not None:
                if old[0] is not request or old[1]!=binding:raise RuntimeServiceError('ML-RUNTIME-SERVICE-REPEAT')
                return self._registry._run(key)
            self.inspect(request,deadline=deadline)
            policy=next(p for p in self._approved if p.run_id==key)
            window=_StartWindow(request.authorization,policy.authorization_digest,request.run._pins[1].config)
            self._registry.reserve(request.run,start_window=window)
            self._entries[key]=(request,binding)
            self._log=tuple(self._entries.items())
            return request.run
        finally:self._lock.release()

    def _submission_for(self,run_id):
        self._holder()
        if type(run_id) is not str:raise RuntimeServiceError('ML-RUNTIME-SERVICE-IDENTITY')
        row=self._entries.get(run_id)
        if row is None:raise RuntimeServiceError('ML-RUNTIME-SERVICE-UNKNOWN')
        if self._binding(row[0])!=row[1]:raise RuntimeServiceError('ML-RUNTIME-SERVICE-REPLACED')
        return row[0]

    def start(self,run_id,scope):
        request=self._submission_for(run_id)
        if request.run._scope is None:
            if not self._lock.acquire(False):raise RuntimeServiceError('ML-RUNTIME-SERVICE-CONFLICT')
            try:
                if type(scope) is not RuntimeScope:raise RuntimeServiceError('ML-RUNTIME-SERVICE-SCOPE')
                request.run._validate_scope(scope)
                self.inspect(request,deadline=scope.startup)
            finally:self._lock.release()
        return self._registry.start(run_id,scope)

    def stop(self,run_id,*,reason='runtime-stop'):
        _Original._holder(self)
        return self._registry_pin.stop(run_id,reason=reason)

    def collect(self,run_id):
        self._submission_for(run_id)
        return self._registry.collect(run_id)

    def restart(self,run_id,unit_id,*,permit,generation,deadline):
        self._submission_for(run_id)
        return self._registry.restart(run_id,unit_id,permit=permit,generation=generation,deadline=deadline)

    def restart_many(self,run_id,requests,*,deadline):
        self._submission_for(run_id)
        return self._registry.restart_many(run_id,requests,deadline=deadline)

    def restart_result(self,run_id,ticket):
        self._submission_for(run_id)
        return self._registry.restart_result(run_id,ticket)

    def replace_controller(self,run_id,*,session_id,deadline):
        self._submission_for(run_id)
        return self._registry.replace_controller(run_id,session_id=session_id,deadline=deadline)

    def controller_recovery_result(self,run_id,ticket):
        self._submission_for(run_id)
        return self._registry.controller_recovery_result(run_id,ticket)
