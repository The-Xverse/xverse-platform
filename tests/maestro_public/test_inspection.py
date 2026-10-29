"""Public static inspection against the actual compiler; no runtime admission claim."""
from dataclasses import replace
import hashlib
from pathlib import Path

import pytest
from xverse_xdl import SourceInput,compile_experiment_sources
from xverse.maestro.execution import (
    CanonicalSubmission,ExecutionInputError,ExperimentSelection,InspectionHost,SchemaPin,TargetBinding,
    inspect_submission,
)


@pytest.fixture
def inputs():
    root=Path(__file__).resolve().parents[1]/'thesis_lite/argus/fixtures'
    documents=tuple((p.name,p.read_bytes()) for p in sorted(root.glob('*.json')))
    schema=Path(__file__).resolve().parents[2]/'xdl/profiles/experiment-lite-v0.1.schema.json'
    compiled=compile_experiment_sources([SourceInput(n,b) for n,b in documents],profile_schema_paths=[schema])
    assert compiled.is_valid
    plan=compiled.plan
    request=CanonicalSubmission('public-inspection-fixture',documents,'sha256:'+plan['digest']['value'],
        'sha256:'+plan['provenance']['inputSemanticDigest']['value'],
        ExperimentSelection(*(plan['selection'][kind]['uri'] for kind in ('system','deployment','scenario'))))
    host=InspectionHost('owned-test-host',(TargetBinding('model-unit-target','owned-test-provider',
        'sha256:'+'1'*64,('simulated',),('model-unit',)),),
        (SchemaPin(schema,'sha256:'+hashlib.sha256(schema.read_bytes()).hexdigest()),))
    return request,host


def test_public_receipt_keeps_exact_input_and_plan_identity_and_never_grants_runtime(inputs):
    request,host=inputs
    receipt=inspect_submission(request,host)
    value=receipt.to_data()
    assert value['planDigest']==request.expected_plan_digest
    assert value['inputSemanticDigest']==request.expected_input_semantic_digest
    assert value['runId']==request.run_id
    assert value['executionAllowed'] is False
    assert value['runtimeAdmission']=='not_checked' and value['readiness']=='not_checked'
    assert value['units'][0]['logicalId'].endswith('#source-instance')
    value['plan']['bindings'].clear()
    assert receipt.to_data()['plan']['bindings']
    assert receipt.inspection_digest==inspect_submission(request,host).inspection_digest


@pytest.mark.parametrize('field',['expected_plan_digest','expected_input_semantic_digest'])
def test_changed_expected_identity_rejects_before_execution(inputs,field):
    request,host=inputs
    with pytest.raises(ExecutionInputError,match='MPX-EFFECTIVE-INPUT-MISMATCH'):
        inspect_submission(replace(request,**{field:'sha256:'+'f'*64}),host)


def test_unknown_or_incompatible_host_target_does_not_gain_authority(inputs):
    request,host=inputs
    for changed in (replace(host,targets=()),replace(host,targets=(replace(host.targets[0],realization_classes=('physical',)),))):
        with pytest.raises(ExecutionInputError,match='MPX-TARGET-UNSUPPORTED'):
            inspect_submission(request,changed)


def test_imported_executable_text_is_invalid_xdl_not_an_instruction(inputs):
    request,host=inputs
    changed=replace(request,documents=(('arbitrary.yaml',b'run: echo not-a-command'),))
    with pytest.raises(ExecutionInputError,match='MPX-XDL-INVALID'):
        inspect_submission(changed,host)


def test_schema_replacement_is_detected_before_compile(inputs,tmp_path):
    request,host=inputs
    schema=tmp_path/'schema.json';schema.write_bytes(host.schemas[0].path.read_bytes())
    changed=replace(host,schemas=(SchemaPin(schema,host.schemas[0].digest),))
    schema.write_text('{}')
    with pytest.raises(ExecutionInputError,match='MPX-SCHEMA-CHANGED'):
        inspect_submission(request,changed)


def test_submission_bounds_and_duplicate_names_reject(inputs):
    request,_=inputs
    for docs in (list(request.documents),request.documents+(request.documents[0],),
                 (('../outside.yaml',b'{}'),),(('large.yaml',b'x'*(1024*1024+1)),)):
        with pytest.raises(ExecutionInputError):replace(request,documents=docs)


def test_explicit_selection_cannot_drift_from_compiled_inputs(inputs):
    request,host=inputs
    changed=replace(request,selection=replace(request.selection,scenario_ref='xdl://other/scenario/another'))
    with pytest.raises(ExecutionInputError,match='MPX-SELECTION-MISMATCH'):
        inspect_submission(changed,host)


def test_static_inspection_never_dispatches_or_opens_evidence_writer(inputs,monkeypatch):
    import subprocess
    from xverse.argus import EvidenceStore
    def forbidden(*_args,**_kwargs):pytest.fail('Static inspection crossed the execution boundary')
    monkeypatch.setattr(subprocess,'Popen',forbidden)
    monkeypatch.setattr(EvidenceStore,'open_run',forbidden)
    request,host=inputs
    assert inspect_submission(request,host).to_data()['executionAllowed'] is False


def test_compiler_io_fault_does_not_expose_private_host_details(inputs,monkeypatch):
    import xverse.maestro.execution.inspection as module
    def unavailable(*_args,**_kwargs):raise OSError('private host installation path')
    monkeypatch.setattr(module,'compile_experiment_sources',unavailable)
    request,host=inputs
    with pytest.raises(ExecutionInputError) as caught:inspect_submission(request,host)
    assert str(caught.value)=='MPX-COMPILER-UNAVAILABLE'


def test_installed_cli_and_public_inspection_agree_on_effective_identities(inputs,tmp_path):
    import json,subprocess,sys
    request,host=inputs
    paths=[]
    for name,raw in request.documents:
        path=tmp_path/name;path.write_bytes(raw);paths.append(str(path))
    command=[sys.executable,'-I','-m','xverse_xdl','experiment','compile','--format','json']
    for schema in host.schemas:command+=['--profile-schema',str(schema.path)]
    result=subprocess.run(command+paths,capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stdout+result.stderr
    plan=json.loads(result.stdout)['plan']
    observed=inspect_submission(request,host).to_data()
    assert observed['planDigest']=='sha256:'+plan['digest']['value']
    assert observed['inputSemanticDigest']=='sha256:'+plan['provenance']['inputSemanticDigest']['value']
