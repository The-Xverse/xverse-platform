"""Actual two-binding scheduling and owned-child rollback; no message exchange claim."""
import json
import time

import pytest
from xverse.maestro.execution import (
    CanonicalSubmission, PhaseReceipt, PublicExecutionService, plan_lifecycle, prepare_execution,
    LifecyclePhase,
)
from xverse_xdl import SourceInput, compile_experiment_sources
from test_runtime import OwnedProvider, inputs, runtime
from test_planning import permit_for


class PairProvider(OwnedProvider):
    def __init__(self, root):
        super().__init__(root)
        self.children = {}
        self.fail_sink = False

    def lifecycle_phases(self, configuration, prepared):
        result = []
        for unit in prepared.inspection.to_data()['units']:
            name = unit['logicalRef']['element'].split('-')[0]
            start_needs = (name + '-prepare',)
            if name == 'sink':
                start_needs += ('source-ready',)
            for phase, operation, needs in (
                ('prepare', 'prepare', ()), ('start', 'start', start_needs),
                ('ready', 'ready', (name + '-start',))):
                result.append(LifecyclePhase(name + '-' + phase, unit['logicalId'],
                    self.provider_id, operation, needs, 3))
        return tuple(result)

    def dispatch(self, phase, configuration, context):
        self.calls.append(phase.phase_id)
        if phase.operation == 'prepare':
            return PhaseReceipt('prepared')
        if phase.operation == 'start':
            child = self.installation.launch()
            self.children[phase.logical_id] = child
            child.configure(configuration.private_config)
            if self.fail_sink and '#sink-instance' in phase.logical_id:
                raise RuntimeError('Injected failure after second child acquisition')
            return PhaseReceipt('started', (child.reference,))
        child = self.children[phase.logical_id]
        assert child.observe() == 'running'
        return PhaseReceipt('ready', (child.reference,), 'liveness')

    def cleanup(self, phase, configuration, context):
        self.calls.append('cleanup-' + phase.phase_id)
        child = self.children.get(phase.logical_id)
        if phase.operation != 'start' or child is None:
            return 'released'
        return child.stop(deadline=context.deadline)

    def observe_runtime(self, configuration, context):
        return 'running' if all(c.observe() == 'running' for c in self.children.values()) else 'exited'


@pytest.mark.parametrize('fail_sink', [False, True])
def test_actual_multi_element_dependency_and_reverse_rollback(runtime, fail_sink):
    base, prior, _, _, original = runtime
    base.close()
    documents = []
    for name, raw in prior.submission.documents:
        document = json.loads(raw)
        if document['kind'] == 'Deployment':
            sink = json.loads(json.dumps(document['spec']['bindings'][0]))
            sink['id'] = 'sink-binding'
            sink['logicalRef']['element'] = 'sink-instance'
            sink['extensions']['io.xverse.experiment']['target']['element'] = 'sink-binding'
            document['spec']['bindings'].append(sink)
        documents.append((name, json.dumps(document).encode()))
    documents = tuple(documents)
    result = compile_experiment_sources([SourceInput(n, b) for n, b in documents],
        profile_schema_paths=[s.path for s in base.host.schemas])
    assert result.is_valid, result.diagnostics
    request = CanonicalSubmission(prior.submission.run_id, documents,
        'sha256:' + result.plan['digest']['value'],
        'sha256:' + result.plan['provenance']['inputSemanticDigest']['value'], prior.submission.selection)
    provider = PairProvider(original.root)
    provider.fail_sink = fail_sink
    prepared = prepare_execution(request, base.host, (provider,))
    graph = plan_lifecycle(prepared, provider.lifecycle_phases(prepared.providers[0].configuration, prepared))
    service = PublicExecutionService(base.root / 'pair-service', base.host, (provider,))
    try:
        running = service.start(prepared, graph, permit_for(prepared, base.host, graph, service), idempotency_key='pair-once')
        assert len(provider.children) == 2
        assert provider.calls.index('source-ready') < provider.calls.index('sink-start')
        assert {p.logical_id for p in graph.phases} == set(provider.children)
        if fail_sink:
            assert running['state'] == 'failed' and running['cleanup'] == 'released'
        else:
            assert running['state'] == 'running'
            running = service.stop(request.run_id, expected_version=running['stateVersion'])
            assert running['state'] == 'stopped' and running['cleanup'] == 'released'
        assert provider.calls.index('cleanup-sink-start') < provider.calls.index('cleanup-source-start')
        assert all(c.observe() == 'released' for c in provider.children.values())
    finally:
        for child in provider.children.values():
            child.stop(deadline=time.monotonic() + 2)
        snapshot = service.read(request.run_id)
        if snapshot['state'] not in ('failed', 'stopped', 'unknown'):
            service.stop(request.run_id, expected_version=snapshot['stateVersion'])
        service.close()
