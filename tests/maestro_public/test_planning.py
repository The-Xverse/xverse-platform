"""Real compiled logical identities; no dispatch, fixture does not claim live admission."""
from dataclasses import replace
import time

import pytest
from xverse.maestro.execution import (
    ExecutionInputError, HostExecutionPermit, LifecyclePhase, plan_lifecycle,
    prepare_execution,
)
from test_inspection import inputs
from test_admission import Provider


@pytest.fixture
def prepared(inputs):
    request, host = inputs
    result = prepare_execution(request, host, (Provider(),))
    logical = result.inspection.to_data()['units'][0]['logicalId']
    phases = tuple(LifecyclePhase(key, logical, Provider.provider_id, operation, needs)
        for key, operation, needs in (
            ('prepare', 'prepare', ()), ('launch', 'start', ('prepare',)),
            ('health', 'ready', ('launch',))))
    return result, host, phases


def test_phase_order_is_dependency_derived_and_permutation_stable(prepared):
    result, _, phases = prepared
    graph = plan_lifecycle(result, phases[::-1])
    assert tuple(p.phase_id for p in graph.phases) == ('prepare', 'launch', 'health')
    assert graph == plan_lifecycle(result, phases)
    assert graph.preparation_digest == result.digest


@pytest.mark.parametrize('change,code', [
    (lambda p: p + (p[0],), 'MPX-PHASE-DUPLICATE'),
    (lambda p: (replace(p[0], logical_id='xdl://elsewhere'),) + p[1:], 'MPX-PHASE-OWNERSHIP'),
    (lambda p: (replace(p[0], provider_id='other'),) + p[1:], 'MPX-PHASE-OWNERSHIP'),
    (lambda p: (replace(p[0], needs=('missing',)),) + p[1:], 'MPX-PHASE-DEPENDENCY-MISSING'),
    (lambda p: (replace(p[0], needs=('health',)),) + p[1:], 'MPX-PHASE-CYCLE'),
    (lambda p: p[:2], 'MPX-PHASE-COVERAGE'),
    (lambda p: (p[0], replace(p[1], needs=()), p[2]), 'MPX-PHASE-ORDER'),
    (lambda p: p + (replace(p[0], phase_id='unobserved'),), 'MPX-PHASE-UNOBSERVED'),
])
def test_invalid_expansion_cannot_become_a_runtime_graph(prepared, change, code):
    result, _, phases = prepared
    with pytest.raises(ExecutionInputError, match=code):
        plan_lifecycle(result, change(phases))


@pytest.mark.parametrize('seconds', [float('nan'), float('inf'), -1, 0, True, 301])
def test_phase_time_budget_must_be_finite_and_bounded(prepared, seconds):
    _, _, phases = prepared
    with pytest.raises(ExecutionInputError, match='MPX-PHASE-INVALID'):
        replace(phases[0], timeout_seconds=seconds)


def permit_for(result, host, graph, service=None):
    now = time.time()
    return HostExecutionPermit('host-grant', host.identity(), result.digest, graph.digest,
        host.host_id, 'explicit-owned-test-authorization', now - 1, now + 60,
        runtime_binding_digest=service.runtime_binding_digest if service else None)


def test_permission_is_exact_and_expiring_but_does_not_dispatch(prepared):
    result, host, phases = prepared
    graph = plan_lifecycle(result, phases)
    permit = permit_for(result, host, graph)
    permit.validate(result, host, graph)
    assert permit.digest.startswith('sha256:')
    with pytest.raises(ExecutionInputError, match='MPX-PERMIT-TIME'):
        permit.validate(result, host, graph, now=permit.expires_at)
    with pytest.raises(ExecutionInputError, match='MPX-PERMIT-MISMATCH'):
        replace(permit, preparation_digest='sha256:' + '0'*64).validate(result, host, graph)
    with pytest.raises(ExecutionInputError, match='MPX-PHASE-GRAPH-INVALID'):
        permit.validate(result, host, replace(graph, phases=phases[::-1]))


def test_permission_is_not_physical_or_private_runtime_authority(prepared):
    result, host, phases = prepared
    graph = plan_lifecycle(result, phases)
    permit = permit_for(result, host, graph)
    with pytest.raises(ExecutionInputError, match='MPX-PERMIT-INVALID'):
        replace(permit, scope='physical')


@pytest.mark.parametrize('target_class,realization', [('physical', 'virtual'), ('remote', 'virtual')])
def test_nonlocal_or_physical_declarations_cannot_use_simulation_grant(inputs, target_class, realization, monkeypatch):
    import json, subprocess
    from xverse.argus import EvidenceStore
    from xverse.maestro.execution import CanonicalSubmission
    from xverse_xdl import SourceInput, compile_experiment_sources
    request, host = inputs
    def forbidden(*_args, **_kwargs):
        pytest.fail('A rejected target caused a process or writer effect')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(EvidenceStore, 'open_run', forbidden)
    documents = []
    for name, raw in request.documents:
        value = json.loads(raw)
        if value['kind'] == 'Deployment':
            value['spec']['targets'][0]['targetClass'] = target_class
            if target_class == 'physical':
                value['spec']['targets'][0]['externalAssetRef'] = 'urn:xverse:test:physical-declaration-not-authorized'
            value['spec']['bindings'][0]['realizationClass'] = realization
        documents.append((name, json.dumps(value).encode()))
    documents = tuple(documents)
    compiled = compile_experiment_sources([SourceInput(n, b) for n, b in documents],
        profile_schema_paths=[s.path for s in host.schemas])
    if target_class == 'physical':
        # Selected compiler rejects physical targets before any executable plan
        # exists. Preserve that authoritative boundary; never forge a plan to
        # claim the prototype ran or admitted this physical declaration.
        assert not compiled.is_valid
        assert 'XDL1-PLAN-REALIZATION-UNSUPPORTED' in {d.code for d in compiled.diagnostics}
        return
    assert compiled.is_valid, compiled.diagnostics
    host = replace(host, targets=(replace(host.targets[0],
        realization_classes=(realization,), target_classes=(target_class,)),))
    submission = CanonicalSubmission(request.run_id, documents,
        'sha256:' + compiled.plan['digest']['value'],
        'sha256:' + compiled.plan['provenance']['inputSemanticDigest']['value'], request.selection)
    prepared = prepare_execution(submission, host, (Provider(),))
    logical = prepared.inspection.to_data()['units'][0]['logicalId']
    phases = (LifecyclePhase('prepare', logical, Provider.provider_id, 'prepare'),
        LifecyclePhase('start', logical, Provider.provider_id, 'start', ('prepare',)),
        LifecyclePhase('ready', logical, Provider.provider_id, 'ready', ('start',)))
    graph = plan_lifecycle(prepared, phases)
    with pytest.raises(ExecutionInputError, match='MPX-PERMIT-SCOPE'):
        permit_for(prepared, host, graph).validate(prepared, host, graph)
