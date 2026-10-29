"""Actual C++ exchange -> public Maestro -> actual Argus, not Autoverse acceptance.

XVERSE_MPX_NATIVE_EXCHANGE must explicitly name the built owned test artifact.
Missing prerequisites fail actionably; no skip or synthetic fallback proves native.
"""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.execution import (
    CanonicalSubmission, ExecutionInputError, FixedProcessInstallation, InstallationFile,
    NativeObservationBatch, PhaseReceipt, PublicExecutionService, plan_lifecycle,
    ProcessOwnershipError, prepare_execution,
)
from xverse_xdl import SourceInput, compile_experiment_sources
from test_runtime import OwnedProvider, inputs, runtime
from test_planning import permit_for


class NativeProvider(OwnedProvider):
    """Test-only host mapper; all executable fields are fixed host registration."""
    def __init__(self, root, executable):
        super().__init__(root)
        self.output = root / 'native-projection.json'
        self.installation = FixedProcessInstallation(executable, (), root, (),
            (InstallationFile(executable, 'sha256:' + hashlib.sha256(executable.read_bytes()).hexdigest()),))
        self.batch_transform = lambda value: value

    def prepare_effective_configuration(self, submission, inspection):
        plan = inspection.to_data()['plan']
        flow = plan['flows'][0]
        system = submission.selection.system_ref
        documents = [json.loads(raw) for _, raw in submission.documents]
        declaration = next(d for d in documents if d['kind'] == 'System')
        interface = next(i for i in declaration['spec']['interfaces'] if i['id'] == flow['interfaceId'])
        count = plan['initialConditions']['sample-count']
        configuration = {'providerId': self.provider_id,
            'planDigest': submission.expected_plan_digest,
            'inputSemanticDigest': submission.expected_input_semantic_digest,
            'interfaceId': system + '#' + flow['interfaceId'],
            'schemaId': interface['payloadSchema'], 'routeId': system + '#' + flow['id'],
            'sourceEndpointId': system + '#' + flow['sourceEndpointId'],
            'destinationEndpointId': system + '#' + flow['destinationEndpointIds'][0],
            'tapCapacity': plan['initialConditions'].get('native-observer-capacity', 4),
            'deferPoll': plan['initialConditions'].get('native-observer-deferred', False),
            'messages': [str(count).encode().hex(), str(count + 1).encode().hex()]}
        from xverse.maestro.execution import EffectiveConfiguration
        return EffectiveConfiguration(submission.documents, json.dumps(configuration).encode(), self.installation_digest)

    def validate_runtime(self, configuration, prepared):
        self.installation.verify()
        plan = prepared.inspection.to_data()['plan']
        if (len(plan['flows']) != 1 or plan['faultSchedule'] or plan['timeMappings']
                or len(plan['lifecycleIntent']) != 1
                or plan['lifecycleIntent'][0]['actionKind'] != 'start'
                or plan['lifecycleIntent'][0]['schedule']['atTicks'] != 0
                or plan['parameters']):
            raise ExecutionInputError('TEST-UNSUPPORTED-NATIVE-SEMANTICS')
        assert plan['bindings'][0]['artifactRefs'][0]['digest'] == self.installation.files[0].digest
        data = json.loads(configuration.private_config)
        assert all(len(data[k].encode()) <= 128 for k in
            ('providerId', 'interfaceId', 'schemaId', 'routeId', 'sourceEndpointId', 'destinationEndpointId'))

    def observation_clock_declarations(self, configuration, run_id, operation_id):
        # Declared origin of the new native process clock, not an observed host
        # reading. Argus persists its domain; no host/native mapping is asserted.
        return {'elapsed': {'domain': 'native-' + operation_id, 'unit': 'ns', 'value': 0}}

    def dispatch(self, phase, configuration, context):
        if phase.operation == 'prepare':
            return PhaseReceipt('prepared')
        if phase.operation == 'start':
            try:
                self.child = self.installation.launch()
            except ProcessOwnershipError as error:
                self.child = error.child
                raise
            data = json.loads(configuration.private_config)
            data.update({'runId': context.run_id, 'correlationId': context.correlation_id,
                'operationId': context.operation_id,
                'causationId': context.intent_event_id, 'nativeClockDomain': 'native-' + context.operation_id,
                'installationDigest': self.installation_digest})
            self.child.configure(json.dumps(data).encode())
            return PhaseReceipt('started', (self.child.reference,))
        while time.monotonic() < context.deadline:
            if self.child.observe() != 'running':
                raise ExecutionInputError('TEST-NATIVE-CHILD-EXITED')
            if self.output.exists():
                return PhaseReceipt('ready', (self.child.reference,), 'interface')
            time.sleep(.005)
        raise ExecutionInputError('TEST-NATIVE-READY-TIMEOUT')

    def read_observation_batch(self, configuration, context):
        with self.output.open('rb') as stream:
            raw = stream.read(65537)
        if len(raw) > 65536:
            raise ExecutionInputError('MPX-NATIVE-BATCH-INVALID')
        value = self.batch_transform(json.loads(raw))
        witness = value['extensions']['io.xverse.maestro.execution']
        return NativeObservationBatch(self.provider_id, witness['batchSequence'], json.dumps(value).encode())


@pytest.fixture
def native(runtime, request):
    base, prior, _, _, original = runtime
    base.close()
    explicit = os.environ.get('XVERSE_MPX_NATIVE_EXCHANGE')
    assert explicit, 'Build xverse_maestro_public_native_exchange, then set XVERSE_MPX_NATIVE_EXCHANGE to that owned artifact'
    executable = Path(explicit).resolve(strict=True)
    assert executable.is_file() and os.access(executable, os.X_OK)
    provider = NativeProvider(original.root, executable)
    # Restore an actual declared XDL flow. Pin the real native executable as its
    # selected deployment artifact; no test model artifact is treated as executable.
    documents = []
    fixture_system = Path(__file__).resolve().parents[1] / 'thesis_lite/argus/fixtures/system.json'
    original_flow = json.loads(fixture_system.read_bytes())['spec']['flows']
    for name, raw in prior.submission.documents:
        value = json.loads(raw)
        if value['kind'] == 'System':
            value['spec']['flows'] = original_flow
        if value['kind'] == 'Deployment':
            value['spec']['targets'][0]['targetClass'] = 'process'
            value['spec']['bindings'][0]['realizationClass'] = 'virtual'
            value['spec']['artifacts'][0].update({'digest': provider.installation.files[0].digest,
                'artifactKind': 'executable', 'sourceRef': 'urn:xverse:test:owned-native-exchange'})
        if value['kind'] == 'Scenario':
            value['extensions']['io.xverse.experiment']['parameters'] = []
            value['spec']['observers'][0]['targetRef']['element'] = 'sample-flow'
            value['spec']['observers'][0]['payloadSchema'] = 'urn:xverse:test:native-echo'
            value['spec']['metrics'][0]['calculationRef'] = 'urn:xverse:test:bytes-received'
            value['spec']['initialConditions'].update(getattr(request, 'param', {}))
        documents.append((name, json.dumps(value).encode()))
    documents = tuple(documents)
    host = replace(base.host, targets=(replace(base.host.targets[0],
        target_classes=('process',), realization_classes=('virtual',)),))
    compiled = compile_experiment_sources([SourceInput(n, b) for n, b in documents],
        profile_schema_paths=[s.path for s in host.schemas])
    assert compiled.is_valid, compiled.diagnostics
    request = CanonicalSubmission(prior.submission.run_id, documents,
        'sha256:' + compiled.plan['digest']['value'],
        'sha256:' + compiled.plan['provenance']['inputSemanticDigest']['value'], prior.submission.selection)
    prepared = prepare_execution(request, host, (provider,))
    graph = plan_lifecycle(prepared, provider.lifecycle_phases(prepared.providers[0].configuration, prepared))
    service = PublicExecutionService(base.root / 'native-service', host, (provider,))
    try:
        result = service.start(prepared, graph, permit_for(prepared, host, graph, service), idempotency_key='native-once')
        assert result['state'] == 'running', result
        yield service, prepared, provider, result
    finally:
        if provider.child:
            provider.child.stop(deadline=time.monotonic() + 2)
        current = service.read(request.run_id)
        if current['state'] not in ('stopped', 'failed', 'unknown'):
            service.stop(request.run_id, expected_version=current['stateVersion'])
        service.close()


def collect(native):
    service, _, _, result = native
    return service.collect_native_observations(result['runId'],
        expected_version=service.read(result['runId'])['stateVersion'])


def test_actual_cpp_exchange_and_original_native_records_share_maestro_argus_identity(native):
    service, prepared, provider, started = native
    original = json.loads(provider.output.read_bytes())
    collected = collect(native)
    source = collected['nativeSources'][provider.provider_id]
    assert source['state'] == 'available' and source['importedRecords'] == 2
    assert len(source['lastArgusOrdinals']) == 2
    assert len(source['lastSnapshotArgusOrdinals']) == 1
    assert len(source['lastInputArgusOrdinals']) == 2
    assert collect(native) == collected  # same original source batch, no replay
    terminal = service.stop(started['runId'], expected_version=collected['stateVersion'])
    assert terminal['state'] == 'stopped' and terminal['cleanup'] == 'released'
    reader = EvidenceStore.read_run(service.root / (started['runId'] + '.argus'))
    assert reader.recorded_evidence_status == reader.assessed_evidence_status == 'complete'
    records = reader.records()
    native_records = [r for r in records if r['eventKind'] == 'observation']
    assert [r['observation'] for r in native_records] == original['records']
    assert [bytes.fromhex(r['observation']['visibleBytesHex']) for r in native_records] == [b'23', b'24']
    receipt = original['extensions']['io.xverse.native.receipt']
    assert receipt['receivedPayloadsHex'] == [b'23'.hex(), b'24'.hex()] and receipt['routeReleased'] is True
    events = {r['eventId'] for r in records}
    assert all(r['correlationId'] == started['correlationId'] and r['causationId'] in events for r in native_records)
    assert all(r['observation']['sourceClock']['domain'].startswith('native-') for r in native_records)
    assert all(r['observation']['routeId'] == prepared.submission.selection.system_ref + '#sample-flow' for r in native_records)
    assert {r['ingestionOrdinal'] for r in native_records} == set(source['lastArgusOrdinals'])
    input_facts = {r['eventId']: r for r in records if 'io.xverse.native.input' in r.get('extensions', {})}
    assert set(input_facts) == {r['causationId'] for r in native_records}
    assert [input_facts[f['eventId']]['extensions']['io.xverse.native.input']
        for f in original['extensions']['io.xverse.native.inputs']] == original['extensions']['io.xverse.native.inputs']
    assert provider.child.observe() == 'released'


@pytest.mark.parametrize('native', [{'native-observer-capacity': 1,
    'native-observer-deferred': True}], indirect=True)
def test_actual_native_observer_pressure_does_not_change_delivery_and_loss_is_original(native):
    service, _, provider, started = native
    original = json.loads(provider.output.read_bytes())
    receipt = original['extensions']['io.xverse.native.receipt']
    assert receipt['receivedPayloadsHex'] == [b'23'.hex(), b'24'.hex()]
    assert len(original['records']) == 1
    assert original['records'][0]['counters']['dropped'] == 0  # true at retention
    final = original['extensions']['io.xverse.native.snapshots'][0]
    assert final['dropped'] == 1 and final['validityState'] == 'degraded'
    collected = collect(native)
    terminal = service.stop(started['runId'], expected_version=collected['stateVersion'])
    assert terminal['state'] == 'stopped' and terminal['cleanup'] == 'released'
    reader = EvidenceStore.read_run(service.root / (started['runId'] + '.argus'))
    assert reader.recorded_evidence_status == reader.assessed_evidence_status == 'incomplete'
    snapshot = next(r['snapshot'] for r in reader.records() if r['eventKind'] == 'snapshot')
    assert snapshot == final
    assert provider.child.observe() == 'released'


@pytest.mark.parametrize('field', ['runId', 'planDigest', 'inputSemanticDigest', 'installationDigest'])
def test_another_source_identity_is_not_joined_and_owned_native_child_is_cleaned(native, field):
    service, _, provider, started = native
    def altered(value):
        value['extensions']['io.xverse.maestro.execution'][field] = 'wrong'
        return value
    provider.batch_transform = altered
    result = collect(native)
    assert result['state'] == 'failed' and result['failureCode'] == 'MPX-NATIVE-SOURCE-MISMATCH'
    assert provider.child.observe() == 'released'
    reader = EvidenceStore.read_run(service.root / (started['runId'] + '.argus'))
    assert not [r for r in reader.records() if r['eventKind'] == 'observation']


def test_transport_gap_is_separate_from_native_counters_and_blocks_complete_evidence(native):
    service, _, provider, started = native
    def gap(value):
        value['extensions']['io.xverse.maestro.execution']['batchSequence'] = 2
        return value
    provider.batch_transform = gap  # explicit transport-fault injection, not native data generation
    result = collect(native)
    assert result['observationTransportGaps'] == 1 and result['state'] == 'running'
    terminal = service.stop(started['runId'], expected_version=result['stateVersion'])
    assert terminal['state'] == 'stopped' and terminal['evidenceWriter'] == 'failed'
    reader = EvidenceStore.read_run(service.root / (started['runId'] + '.argus'))
    assert reader.assessed_evidence_status == 'incomplete'
    for record in reader.records():
        if record['eventKind'] == 'observation':
            assert record['observation']['counters']['dropped'] == record['observation']['counters']['coalesced'] == 0


def test_same_native_sequence_with_changed_body_conflicts_and_does_not_reimport(native):
    service, _, provider, started = native
    collect(native)
    def changed(value):
        value['records'][0]['sourceClock']['value'] += 1
        return value
    provider.batch_transform = changed
    result = collect(native)
    assert result['state'] == 'failed' and result['failureCode'] == 'MPX-NATIVE-SEQUENCE-CONFLICT'
    reader = EvidenceStore.read_run(service.root / (started['runId'] + '.argus'))
    assert len([r for r in reader.records() if r['eventKind'] == 'observation']) == 2


@pytest.mark.parametrize('fault,code', [('route', 'MPX-NATIVE-ROUTE-MISMATCH'),
    ('schema', 'MPX-NATIVE-EVIDENCE-IMPORT-FAILED')])
def test_foreign_route_and_malformed_original_projection_reject_without_repair(native, fault, code):
    _, _, provider, _ = native
    def altered(value):
        if fault == 'route':
            value['records'][0]['routeId'] = 'another-route'
        else:
            del value['records'][0]['sourceClock']
        return value
    provider.batch_transform = altered
    result = collect(native)
    assert result['state'] == 'failed' and result['failureCode'] == code
    assert provider.child.observe() == 'released'


def test_undeclared_native_clock_is_rejected_before_record_import(native):
    service, _, provider, started = native
    def altered(value):
        value['records'][0]['sourceClock']['domain'] = 'undeclared-native-domain'
        return value
    provider.batch_transform = altered
    result = collect(native)
    assert result['state'] == 'failed' and result['failureCode'] == 'MPX-NATIVE-CLOCK-UNDECLARED'
    reader = EvidenceStore.read_run(service.root / (started['runId'] + '.argus'))
    assert not [r for r in reader.records() if r['eventKind'] == 'observation']
    assert provider.child.observe() == 'released'


def test_native_import_io_failure_after_records_does_not_block_actual_owned_cleanup(native, monkeypatch):
    from xverse.argus.writer import EvidenceRun
    service, _, provider, started = native
    original = EvidenceRun.import_observation
    def failed_after_write(writer, projection):
        original(writer, projection)
        raise OSError('private native evidence path')
    monkeypatch.setattr(EvidenceRun, 'import_observation', failed_after_write)
    result = collect(native)
    assert result['state'] == 'failed' and result['evidenceWriter'] == 'failed'
    assert result['failureCode'] == 'MPX-NATIVE-EVIDENCE-IMPORT-FAILED'
    assert result['cleanup'] == 'released' and provider.child.observe() == 'released'
    reader = EvidenceStore.read_run(service.root / (started['runId'] + '.argus'))
    assert reader.assessed_evidence_status == 'incomplete'
    assert len([r for r in reader.records() if r['eventKind'] == 'observation']) == 2
    assert 'private native evidence' not in json.dumps(result)


@pytest.mark.parametrize('provider_id,sequence,raw', [
    ([], 1, b'{}'), ('source', True, b'{}'), ('source', 0, b'{}'),
    ('source', 1, b'x'*65537), ('source', 1, b'{bad'),
    ('source', 1, json.dumps({'records': [{}]*33}).encode()),
])
def test_native_batch_input_limits_have_stable_errors_without_runtime(provider_id, sequence, raw):
    with pytest.raises(ExecutionInputError, match='MPX-NATIVE-BATCH-INVALID'):
        NativeObservationBatch(provider_id, sequence, raw)


def test_unknown_upstream_cause_remains_absent_without_run_level_substitution(native):
    service, _, provider, started = native
    def unknown(value):
        for original in value['extensions']['io.xverse.native.inputs']:
            original['upstreamCausationId'] = None
        return value
    provider.batch_transform = unknown  # explicit trace-loss injection on actual input records
    result = collect(native)
    assert result['state'] == 'running'
    service.stop(started['runId'], expected_version=result['stateVersion'])
    reader = EvidenceStore.read_run(service.root / (started['runId'] + '.argus'))
    inputs = [r for r in reader.records() if 'io.xverse.native.input' in r.get('extensions', {})]
    assert len(inputs) == 2
    assert all('causationId' not in r for r in inputs)
    assert all(r['extensions']['io.xverse.native.input']['upstreamCausationId'] is None for r in inputs)


def test_foreign_input_producer_cannot_be_relabelled_as_original_native_evidence(native):
    _, _, provider, _ = native
    def altered(value):
        value['extensions']['io.xverse.native.inputs'][0]['producerId'] = 'maestro-public-execution'
        return value
    provider.batch_transform = altered
    result = collect(native)
    assert result['state'] == 'failed' and result['failureCode'] == 'MPX-NATIVE-INPUT-INVALID'
    assert provider.child.observe() == 'released'


def test_actual_native_partial_start_retains_unknown_child_until_original_owner_reconciles(native, monkeypatch):
    prior, submission, original, started = native
    current = prior.read(started['runId'])
    prior.stop(started['runId'], expected_version=current['stateVersion'])
    root = original.root / 'partial-native'
    root.mkdir()
    provider = NativeProvider(root, original.installation.executable)
    prepared = prepare_execution(submission.submission, prior.host, (provider,))
    graph = plan_lifecycle(prepared, provider.lifecycle_phases(prepared.providers[0].configuration, prepared))
    service = PublicExecutionService(root / 'service', prior.host, (provider,))
    def unavailable(*_args):
        raise OSError('kernel handle unavailable')
    try:
        with monkeypatch.context() as fault:
            fault.setattr(os, 'pidfd_open', unavailable)
            result = service.start(prepared, graph, permit_for(prepared, prior.host, graph, service),
                idempotency_key='partial-native')
        assert result['state'] == result['cleanup'] == 'unknown'
        assert result['failureCode'] == 'MPX-PROCESS-OWNERSHIP-UNAVAILABLE'
        assert provider.child is not None and provider.child.observe() == 'unknown'
    finally:
        if provider.child is not None:
            # Test owner retains the original Popen, never a reconstructed PID.
            provider.child._process.terminate()
            provider.child._process.wait(timeout=2)
            provider.child.stop(deadline=time.monotonic() + 2)
        service.close()
