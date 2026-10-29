"""Public bounded XDL inspection for capability022; no execution authority.

Host installations/schema pins are independent of submitted documents. This first
layer performs static compilation and binding checks only. Runtime permissions,
provider effective-configuration admission and lifecycle dispatch are separate.
"""
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from xverse_xdl import (
    ElementIdentity, ExperimentLimits, ResourceIdentity, SourceInput,
    compile_experiment_sources,
)

_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$')
_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._/-]{0,255}$')
_DIGEST = re.compile(r'^sha256:[a-f0-9]{64}$')


def canonical(value):
    """Canonical service envelope, separate from authoritative XDL identity."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def sha256(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


class ExecutionInputError(ValueError):
    """Stable public boundary code; not itself proof that no effect occurred.

    Static inspection never dispatches. Runtime failures must additionally report
    their durable run observations and actual cleanup outcome.
    """
    def __init__(self, code, diagnostics=()):
        self.code = code
        self.diagnostics = tuple(diagnostics)
        super().__init__(code)


@dataclass(frozen=True)
class ExperimentSelection:
    """Explicit canonical resource URIs, independently checked against the plan."""
    system_ref: str
    deployment_ref: str
    scenario_ref: str

    def __post_init__(self):
        for kind,value in self.to_data().items():
            if (type(value) is not str or len(value)>512 or not value.startswith('xdl://')
                    or '/'+kind+'/' not in value):
                raise ExecutionInputError('MPX-SELECTION-INVALID')

    def to_data(self):
        return {'system':self.system_ref,'deployment':self.deployment_ref,'scenario':self.scenario_ref}


@dataclass(frozen=True)
class CanonicalSubmission:
    """Explicit immutable source bytes and expected independent compiler identity."""
    run_id: str
    documents: tuple[tuple[str, bytes], ...] = field(repr=False)
    expected_plan_digest: str
    expected_input_semantic_digest: str
    selection: ExperimentSelection

    def __post_init__(self):
        if (type(self.run_id) is not str or not _ID.fullmatch(self.run_id)
                or type(self.selection) is not ExperimentSelection
                or type(self.documents) is not tuple or not 1 <= len(self.documents) <= 128
                or any(type(v) is not str or not _DIGEST.fullmatch(v) for v in
                       (self.expected_plan_digest,self.expected_input_semantic_digest))):
            raise ExecutionInputError('MPX-SUBMISSION-INVALID')
        seen = set()
        total = 0
        for item in self.documents:
            if type(item) is not tuple or len(item) != 2:
                raise ExecutionInputError('MPX-SUBMISSION-INVALID')
            name, content = item
            if (type(name) is not str or not _NAME.fullmatch(name)
                    or '..' in PurePosixPath(name).parts or name in seen
                    or type(content) is not bytes or len(content) > 1024*1024):
                raise ExecutionInputError('MPX-SUBMISSION-INVALID')
            seen.add(name)
            total += len(content)
        if total > 8*1024*1024:
            raise ExecutionInputError('MPX-SUBMISSION-LIMIT')


@dataclass(frozen=True)
class SchemaPin:
    """A trusted-host local Profile schema, never a submitted lookup path."""
    path: Path
    digest: str

    def verify(self):
        if type(self.digest) is not str or not _DIGEST.fullmatch(self.digest):
            raise ExecutionInputError('MPX-SCHEMA-PIN-INVALID')
        try:
            with Path(self.path).open('rb') as stream:
                data = stream.read(1024*1024+1)
        except OSError:
            raise ExecutionInputError('MPX-SCHEMA-UNAVAILABLE') from None
        if len(data)>1024*1024 or sha256(data) != self.digest:
            raise ExecutionInputError('MPX-SCHEMA-CHANGED')


@dataclass(frozen=True)
class TargetBinding:
    """Static host registration; source metadata alone grants no execution."""
    target_id: str
    provider_id: str
    implementation_digest: str
    realization_classes: tuple[str, ...]
    target_classes: tuple[str, ...]

    def __post_init__(self):
        if (any(type(v) is not str or not _ID.fullmatch(v) for v in (self.target_id,self.provider_id))
                or type(self.implementation_digest) is not str or not _DIGEST.fullmatch(self.implementation_digest)
                or any(type(v) is not tuple or not v or len(v)>16
                       or any(type(s) is not str or not _ID.fullmatch(s) for s in v)
                       for v in (self.realization_classes,self.target_classes))):
            raise ExecutionInputError('MPX-HOST-BINDING-INVALID')


@dataclass(frozen=True)
class InspectionHost:
    """Immutable static host/schema/provider identity, without a runtime permit."""
    host_id: str
    targets: tuple[TargetBinding, ...]
    schemas: tuple[SchemaPin, ...] = ()

    def __post_init__(self):
        if (type(self.host_id) is not str or not _ID.fullmatch(self.host_id)
                or type(self.targets) is not tuple or len(self.targets)>128
                or any(type(v) is not TargetBinding for v in self.targets)
                or len({v.target_id for v in self.targets}) != len(self.targets)
                or type(self.schemas) is not tuple or len(self.schemas)>32
                or any(type(v) is not SchemaPin for v in self.schemas)):
            raise ExecutionInputError('MPX-HOST-BINDING-INVALID')

    def identity(self):
        """Hash public binding metadata without exposing host schema paths."""
        return sha256(canonical({'hostId':self.host_id,
            'targets':[{'targetId':v.target_id,'providerId':v.provider_id,
                'implementationDigest':v.implementation_digest,
                'realizationClasses':v.realization_classes,'targetClasses':v.target_classes} for v in self.targets],
            'schemas':[v.digest for v in self.schemas]}))


@dataclass(frozen=True)
class EffectiveInspection:
    """Immutable canonical inspection receipt. It confers no execution authority."""
    canonical_bytes: bytes = field(repr=False)

    def to_data(self):
        return json.loads(self.canonical_bytes)

    @property
    def inspection_digest(self):
        return sha256(b'xverse.maestro.public-inspection.v1\0'+self.canonical_bytes)


def inspect_submission(submission: CanonicalSubmission, host: InspectionHost) -> EffectiveInspection:
    """Compile exact submitted XDL and inspect static host bindings without effects.

    Runtime provider permission/readiness and effective configuration are not
    implied by this static receipt. No private runtime object is accepted.
    """
    if type(submission) is not CanonicalSubmission or type(host) is not InspectionHost:
        raise ExecutionInputError('MPX-INSPECTION-INPUT')
    for schema in host.schemas:
        schema.verify()
    try:
        compiled = compile_experiment_sources(
            [SourceInput(name,content) for name,content in submission.documents],
            profile_schema_paths=[v.path for v in host.schemas],
            run_id=submission.run_id,
            limits=ExperimentLimits(max_resources=128,max_bytes_per_file=1024*1024),
        )
    except (ValueError,TypeError,AttributeError,RecursionError,OSError):
        raise ExecutionInputError('MPX-COMPILER-UNAVAILABLE') from None
    for schema in host.schemas:
        schema.verify()
    if not compiled.is_valid or compiled.plan is None:
        raise ExecutionInputError('MPX-XDL-INVALID',tuple(d.code for d in compiled.diagnostics))
    plan=compiled.plan
    if any(plan['selection'][kind]['uri'] != value for kind,value in submission.selection.to_data().items()):
        raise ExecutionInputError('MPX-SELECTION-MISMATCH')
    actual_plan='sha256:'+plan['digest']['value']
    actual_input='sha256:'+plan['provenance']['inputSemanticDigest']['value']
    if (actual_plan != submission.expected_plan_digest or actual_input != submission.expected_input_semantic_digest):
        raise ExecutionInputError('MPX-EFFECTIVE-INPUT-MISMATCH')
    targets={v.target_id:v for v in host.targets}
    units=[]
    for binding in plan['bindings']:
        target=targets.get(binding['targetId'])
        if (target is None or binding['targetClass'] not in target.target_classes
                or binding['realizationClass'] not in target.realization_classes):
            raise ExecutionInputError('MPX-TARGET-UNSUPPORTED')
        logical=binding['logicalRef']
        identity=ElementIdentity(ResourceIdentity.from_mapping(logical),logical['element']).uri
        units.append({'logicalId':identity,'logicalRef':logical,'bindingId':binding['id'],
            'targetId':target.target_id,'providerId':target.provider_id,
            'implementationDigest':target.implementation_digest})
    if not units:
        raise ExecutionInputError('MPX-NO-BOUND-UNITS')
    return EffectiveInspection(canonical({'contractVersion':'1.0','stage':'static-inspection',
        'runId':submission.run_id,'planDigest':actual_plan,'inputSemanticDigest':actual_input,
        'sourceDigests':{name:sha256(content) for name,content in submission.documents},
        'hostBindingDigest':host.identity(),'units':units,'plan':plan,
        'executionAllowed':False,'runtimeAdmission':'not_checked','readiness':'not_checked'}))
