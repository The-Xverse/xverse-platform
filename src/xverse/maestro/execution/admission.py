"""Host-only provider preparation and effective-input equality.

Provider implementations are trusted installed host code, never project plugins.
This stage still dispatches no lifecycle operations. It independently compiles the
provider's actual effective documents rather than treating an echoed digest as
proof that those inputs will be consumed by a runtime.
"""
from dataclasses import dataclass, field
import json
from typing import Protocol

from .inspection import (
    CanonicalSubmission, EffectiveInspection, ExecutionInputError, InspectionHost,
    _DIGEST, canonical, inspect_submission, sha256,
)


@dataclass(frozen=True)
class EffectiveConfiguration:
    """Immutable provider input: actual documents plus a bounded private config.

    A later runtime must consume this same frozen value; it cannot regenerate
    another preset after admission. Private configuration is never a log payload.
    """
    documents: tuple[tuple[str,bytes], ...] = field(repr=False)
    private_config: bytes = field(repr=False)
    installation_digest: str | None = None

    def __post_init__(self):
        if (type(self.private_config) is not bytes or len(self.private_config)>1024*1024
                or self.installation_digest is not None and
                (type(self.installation_digest) is not str or not _DIGEST.fullmatch(self.installation_digest))):
            raise ExecutionInputError('MPX-PROVIDER-CONFIG-INVALID')


class ExecutionProvider(Protocol):
    """Reviewed host implementation boundary, independent of submitted content."""
    provider_id: str
    implementation_digest: str

    def prepare_effective_configuration(self, submission: CanonicalSubmission,
                                        inspection: EffectiveInspection) -> EffectiveConfiguration:
        """Purely map supported semantics into the actual frozen runtime inputs.

        Unsupported profiles/actions/fields must reject. A preset which ignores
        edits must return its real effective documents and will fail equality.
        """
        ...


@dataclass(frozen=True)
class PreparedProvider:
    provider_id: str
    implementation_digest: str
    configuration: EffectiveConfiguration = field(repr=False)
    configuration_digest: str


@dataclass(frozen=True)
class PreparedExecution:
    """Effective inputs verified; still no runtime permit or execution handle."""
    submission: CanonicalSubmission
    inspection: EffectiveInspection
    providers: tuple[PreparedProvider,...]
    digest: str

    def summary(self):
        """Public metadata excludes private provider configuration and host paths."""
        return {'stage':'effective-inputs-verified','runId':self.submission.run_id,
            'inspectionDigest':self.inspection.inspection_digest,
            'preparationDigest':self.digest,'executionAllowed':False,
            'runtimeAdmission':'not_checked','providers':[
                {'providerId':p.provider_id,'implementationDigest':p.implementation_digest,
                 'configurationDigest':p.configuration_digest,
                 'installationDigest':p.configuration.installation_digest,
                 'effectiveSourceDigests':{name:sha256(raw) for name,raw in p.configuration.documents}} for p in self.providers]}


def prepare_execution(submission: CanonicalSubmission, host: InspectionHost,
                      providers: tuple[ExecutionProvider,...]) -> PreparedExecution:
    """Independently verify installed providers' actual effective source mapping.

    The host registers implementations outside imported content. This function
    does not authorize or call start, stop, message submission or physical probes.
    """
    inspection=inspect_submission(submission,host)
    if type(providers) is not tuple or len(providers)>128:
        raise ExecutionInputError('MPX-PROVIDER-REGISTRY-INVALID')
    expected={t.provider_id:t.implementation_digest for t in host.targets}
    if any(expected[t.provider_id] != t.implementation_digest for t in host.targets):
        raise ExecutionInputError('MPX-PROVIDER-REGISTRY-INVALID')
    actual={}
    for provider in providers:
        identity=getattr(provider,'provider_id',None)
        if type(identity) is not str or identity in actual or identity not in expected or getattr(provider,'implementation_digest',None)!=expected[identity]:
            raise ExecutionInputError('MPX-PROVIDER-IDENTITY-MISMATCH')
        actual[identity]=provider
    selected={u['providerId'] for u in inspection.to_data()['units']}
    if not selected<=actual.keys():
        raise ExecutionInputError('MPX-PROVIDER-UNAVAILABLE')
    prepared=[]
    for identity in sorted(selected):
        provider=actual[identity]
        try:
            configuration=provider.prepare_effective_configuration(submission,inspection)
        except ExecutionInputError:
            raise
        except Exception:
            raise ExecutionInputError('MPX-PROVIDER-PREPARATION-FAILED') from None
        if type(configuration) is not EffectiveConfiguration:
            raise ExecutionInputError('MPX-PROVIDER-CONFIG-INVALID')
        # Constructing a new public submission also reapplies all source bounds.
        effective=CanonicalSubmission(submission.run_id,configuration.documents,
            submission.expected_plan_digest,submission.expected_input_semantic_digest,
            submission.selection)
        observed=inspect_submission(effective,host)
        # Byte differences are provenance, not semantic mismatches. Both sets
        # of actual source hashes are retained by their separate receipts.
        left,right=inspection.to_data(),observed.to_data()
        if (left['planDigest'],left['inputSemanticDigest']) != (right['planDigest'],right['inputSemanticDigest']):
            raise ExecutionInputError('MPX-EFFECTIVE-INPUT-MISMATCH')
        if (getattr(provider,'provider_id',None)!=identity
                or getattr(provider,'implementation_digest',None)!=expected[identity]):
            raise ExecutionInputError('MPX-PROVIDER-IDENTITY-MISMATCH')
        configuration_digest=sha256(canonical({'provider':identity,
            'implementationDigest':expected[identity],'effectiveSourceDigests':right['sourceDigests'],
            'installationDigest':configuration.installation_digest,
            'privateConfigurationDigest':sha256(configuration.private_config)}))
        prepared.append(PreparedProvider(identity,expected[identity],configuration,configuration_digest))
    fingerprint=sha256(b'xverse.maestro.prepared-execution.v1\0'+canonical({
        'inspectionDigest':inspection.inspection_digest,
        'providerConfigurations':[p.configuration_digest for p in prepared]}))
    return PreparedExecution(submission,inspection,tuple(prepared),fingerprint)
