"""Actual effective-source compilation; host fixtures do not establish live runtime admission."""
from dataclasses import replace
import json

import pytest
from xverse.maestro.execution import EffectiveConfiguration,ExecutionInputError,prepare_execution
from test_inspection import inputs


class Provider:
    provider_id='owned-test-provider'
    implementation_digest='sha256:'+'1'*64
    def __init__(self,effective=None):self.effective=effective;self.calls=0
    def prepare_effective_configuration(self,submission,inspection):
        self.calls+=1
        return EffectiveConfiguration(self.effective or submission.documents,b'private host configuration')
    def start(self,*_args):pytest.fail('Effective preparation dispatched a runtime')


def test_effective_documents_are_independently_compiled_without_runtime_authority(inputs):
    request,host=inputs;provider=Provider()
    prepared=prepare_execution(request,host,(provider,))
    assert provider.calls==1
    assert prepared.providers[0].configuration.documents==request.documents
    summary=prepared.summary()
    assert summary['executionAllowed'] is False and summary['runtimeAdmission']=='not_checked'
    assert b'private host configuration' not in json.dumps(summary).encode()
    assert 'private host configuration' not in repr(prepared)
    assert request.documents[0][1].decode() not in repr(prepared)
    assert summary['providers'][0]['effectiveSourceDigests']


def test_preset_generating_different_xdl_cannot_echo_its_way_to_admission(inputs):
    request,host=inputs
    documents=[]
    for name,raw in request.documents:
        value=json.loads(raw)
        if value['kind']=='Scenario':value['spec']['initialConditions']['sample-count']=17
        documents.append((name,json.dumps(value).encode()))
    provider=Provider(tuple(documents))
    with pytest.raises(ExecutionInputError,match='MPX-EFFECTIVE-INPUT-MISMATCH'):
        prepare_execution(request,host,(provider,))


def test_missing_changed_or_duplicate_host_provider_rejects(inputs):
    request,host=inputs
    with pytest.raises(ExecutionInputError,match='MPX-PROVIDER-UNAVAILABLE'):
        prepare_execution(request,host,())
    changed=Provider();changed.implementation_digest='sha256:'+'2'*64
    with pytest.raises(ExecutionInputError,match='MPX-PROVIDER-IDENTITY-MISMATCH'):
        prepare_execution(request,host,(changed,))
    with pytest.raises(ExecutionInputError,match='MPX-PROVIDER-IDENTITY-MISMATCH'):
        prepare_execution(request,host,(Provider(),Provider()))


def test_provider_configuration_and_registry_bounds_are_checked(inputs):
    request,host=inputs
    with pytest.raises(ExecutionInputError):EffectiveConfiguration(request.documents,b'x'*(1024*1024+1))
    with pytest.raises(ExecutionInputError):prepare_execution(request,host,[Provider()])


@pytest.mark.parametrize('identity',[None,[], 'unregistered'])
def test_malformed_provider_identity_has_a_stable_public_error(inputs,identity):
    request,host=inputs;provider=Provider();provider.provider_id=identity
    with pytest.raises(ExecutionInputError,match='MPX-PROVIDER-IDENTITY-MISMATCH'):
        prepare_execution(request,host,(provider,))
