"""Actual owned Linux children/Argus; not native X-COM or Autoverse acceptance."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.execution import (
    CanonicalSubmission, EffectiveConfiguration, ExecutionInputError, ExperimentSelection,
    FixedProcessInstallation, InstallationFile, LifecyclePhase, PhaseReceipt,
    ProcessOwnershipError, PublicExecutionService, plan_lifecycle, prepare_execution,
)
from xverse_xdl import SourceInput, compile_experiment_sources
from test_inspection import inputs
from test_planning import permit_for


class OwnedProvider:
    provider_id = 'owned-test-provider'
    implementation_digest = 'sha256:' + '1'*64

    @property
    def installation_digest(self):
        return self.installation.installation_digest

    def __init__(self, root):
        self.root = root
        self.output = root / 'consumed.json'
        self.child = None
        self.calls = []
        self.fail_ready = False
        self.fail_after_launch = False
        self.unknown_cleanup = False
        script = root / 'owned_fixture.py'
        script.write_text('''import json,sys,time
from pathlib import Path
data=json.load(sys.stdin)
parameters={p["id"]:p["value"] for p in data["parameters"]}
data["result"]=data["initial"]["sample-count"]*parameters["gain"] if parameters["enabled"] else 0
Path("consumed.json").write_text(json.dumps(data))
while True: time.sleep(.05)
''')
        executable = Path(sys.executable).resolve()
        pins = tuple(InstallationFile(p, 'sha256:' + hashlib.sha256(p.read_bytes()).hexdigest())
                     for p in (executable, script))
        self.installation = FixedProcessInstallation(executable, ('-I', str(script)), root, (), pins)

    def prepare_effective_configuration(self, submission, inspection):
        plan = inspection.to_data()['plan']
        return EffectiveConfiguration(submission.documents, json.dumps({
            'initial': plan['initialConditions'], 'parameters': plan['parameters'],
            'seed': plan['seed']}, sort_keys=True).encode(), self.installation_digest)

    def validate_runtime(self, configuration, prepared):
        self.installation.verify()
        plan = prepared.inspection.to_data()['plan']
        steps = plan['lifecycleIntent']
        if (plan['faultSchedule'] or plan['flows'] or len(steps) != 1
                or steps[0]['actionKind'] != 'start' or steps[0]['schedule']['atTicks'] != 0
                or steps[0]['dependsOn'] or steps[0]['duration'] is not None
                or len(plan['observers']) != 1 or len(plan['metrics']) != 1
                or plan['observers'][0]['payloadPolicy']['payloadSchema'] != 'urn:xverse:test:consumed-input'
                or plan['metrics'][0]['calculationRef'] != 'urn:xverse:test:count-times-gain'
                or plan['timeMappings']):
            raise ExecutionInputError('TEST-UNSUPPORTED-SEMANTICS')

    def lifecycle_phases(self, configuration, prepared):
        logical = prepared.inspection.to_data()['units'][0]['logicalId']
        return tuple(LifecyclePhase(key, logical, self.provider_id, operation, needs, 3)
                     for key, operation, needs in (('prepare', 'prepare', ()),
                         ('launch', 'start', ('prepare',)), ('ready', 'ready', ('launch',))))

    def dispatch(self, phase, configuration, context):
        self.calls.append(phase.phase_id)
        if phase.operation == 'prepare':
            return PhaseReceipt('prepared')
        if phase.operation == 'start':
            try:
                self.child = self.installation.launch()
            except ProcessOwnershipError as error:
                self.child = error.child
                raise
            self.child.configure(configuration.private_config)
            if self.fail_after_launch:
                raise RuntimeError('private provider path must not enter diagnostics')
            return PhaseReceipt('started', (self.child.reference,))
        if self.fail_ready:
            raise RuntimeError('No readiness')
        while time.monotonic() < context.deadline:
            if self.child.observe() != 'running':
                raise RuntimeError('Child exited')
            if self.output.exists():
                observed = json.loads(self.output.read_bytes())
                return PhaseReceipt('ready', (self.child.reference,), 'interface',
                    json.dumps({'observerId': 'sample-observer',
                        'metricId': 'sample-count', 'value': observed['result'],
                        'consumedInitial': observed['initial']}).encode())
            time.sleep(.005)
        raise RuntimeError('Readiness deadline')

    def cleanup(self, phase, configuration, context):
        self.calls.append('cleanup-' + phase.phase_id)
        if phase.operation != 'start' or self.child is None:
            return 'released'
        if self.unknown_cleanup:
            return 'unknown'
        return self.child.stop(deadline=context.deadline)

    def observe_runtime(self, configuration, context):
        status = self.child.observe()
        return 'exited' if status in ('exited', 'released') else status


@pytest.fixture
def runtime(inputs, tmp_path):
    request, host = inputs
    documents = []
    for name, raw in request.documents:
        value = json.loads(raw)
        if value['kind'] == 'System':
            value['spec']['flows'] = []
        if value['kind'] == 'Scenario':
            value['spec']['faults'] = []
            step = value['spec']['steps'][1]
            step['schedule']['at'] = 0
            extension = step['extensions']['io.xverse.experiment']
            extension['dependsOn'] = []
            extension.pop('duration')
            value['spec']['steps'] = [step]
            observer = value['spec']['observers'][0]
            observer['targetRef']['element'] = 'source-instance'
            observer['samplingIntent'] = 'Observe the consumed startup input once'
            observer['payloadSchema'] = 'urn:xverse:test:consumed-input'
            observer['evidenceSinkRef'] = 'urn:xverse:test:argus:startup-input'
            value['spec']['metrics'][0]['calculationRef'] = 'urn:xverse:test:count-times-gain'
            value['spec']['initialConditions']['sample-count'] = 23
        documents.append((name, json.dumps(value).encode()))
    documents = tuple(documents)
    compiled = compile_experiment_sources([SourceInput(n, b) for n, b in documents],
        profile_schema_paths=[s.path for s in host.schemas])
    assert compiled.is_valid, compiled.diagnostics
    plan = compiled.plan
    request = CanonicalSubmission(request.run_id, documents, 'sha256:' + plan['digest']['value'],
        'sha256:' + plan['provenance']['inputSemanticDigest']['value'],
        ExperimentSelection(*(plan['selection'][k]['uri'] for k in ('system', 'deployment', 'scenario'))))
    provider_root = tmp_path / 'provider'
    provider_root.mkdir()
    provider = OwnedProvider(provider_root)
    prepared = prepare_execution(request, host, (provider,))
    graph = plan_lifecycle(prepared, provider.lifecycle_phases(prepared.providers[0].configuration, prepared))
    service = PublicExecutionService(tmp_path / 'service', host, (provider,))
    permit = permit_for(prepared, host, graph, service)
    yield service, prepared, graph, permit, provider
    if provider.child is not None:
        outcome = provider.child.stop(deadline=time.monotonic() + 2)
        if outcome == 'unknown':
            # Test-only release of the original Popen child when simulating a
            # missing kernel handle. No PID lookup, name or process-group kill.
            provider.child._process.terminate()
            provider.child._process.wait(timeout=2)
            provider.child.stop(deadline=time.monotonic() + 2)
    if not service._closed:
        snapshot = service._runs.get(request.run_id)
        if snapshot and snapshot.state not in ('stopped', 'failed', 'unknown'):
            service.stop(request.run_id, expected_version=service.read(request.run_id)['stateVersion'])
        service.close()


def start(runtime):
    service, prepared, graph, permit, _ = runtime
    return service.start(prepared, graph, permit, idempotency_key='start-once')


def test_actual_child_consumes_frozen_edited_inputs_and_argus_retains_identity(runtime):
    service, prepared, _, _, provider = runtime
    result = start(runtime)
    assert result['state'] == 'running', result
    consumed = json.loads(provider.output.read_text())
    assert consumed['initial']['sample-count'] == 23
    assert consumed['parameters'] == prepared.inspection.to_data()['plan']['parameters']
    assert consumed['result'] == 34.5
    assert start(runtime) == result
    assert provider.calls == ['prepare', 'launch', 'ready']
    assert all(o['readinessKind'] != 'functional' for o in result['observations'])
    terminal = service.stop(result['runId'], expected_version=result['stateVersion'])
    assert terminal['state'] == 'stopped' and terminal['cleanup'] == 'released'
    assert provider.child.observe() == 'released'
    assert provider.calls[-2:] == ['cleanup-launch', 'cleanup-prepare']
    assert service.stop(result['runId'], expected_version=terminal['stateVersion']) == terminal
    assert service.stop(result['runId'], expected_version=result['stateVersion']) == terminal
    assert terminal['stopOperationId'] and terminal['stopOperationId'] != terminal['operationId']
    reader = EvidenceStore.read_run(service.root / (result['runId'] + '.argus'))
    assert reader.recorded_evidence_status == reader.assessed_evidence_status == 'complete'
    records = [r for r in reader.records() if r.get('producerId') == 'maestro-public-execution']
    assert len(records) == len(terminal['observations'])
    assert {r['correlationId'] for r in records if 'correlationId' in r} == {result['correlationId']}
    assert records[0]['eventId'] == result['correlationId']
    events = {r['eventId']: r for r in records}
    for record in records:
        data = record['extensions']['io.xverse.maestro.execution']
        assert data['planDigest'] == prepared.submission.expected_plan_digest
        assert data['inputSemanticDigest'] == prepared.submission.expected_input_semantic_digest
        assert record['clocks']['host']['unit'] == 'ns'
        if record.get('causationId'):
            assert record['causationId'] in events
    assert str(provider.root) not in json.dumps(terminal)
    measured = next(r for r in records if r['extensions']['io.xverse.maestro.execution']['readinessKind'])
    assert measured['extensions']['io.xverse.maestro.execution']['observation']['value'] == 34.5
    stopped = next(r for r in records if r['extensions']['io.xverse.maestro.execution']['kind'] == 'run-terminal')
    assert stopped['extensions']['io.xverse.maestro.execution']['operationId'] == terminal['stopOperationId']


@pytest.mark.parametrize('failure', ['fail_ready', 'fail_after_launch'])
def test_partial_launch_and_failed_readiness_clean_actual_owned_child(runtime, failure):
    service, prepared, _, _, provider = runtime
    setattr(provider, failure, True)
    result = start(runtime)
    assert result['state'] == 'failed' and result['cleanup'] == 'released'
    assert provider.child.observe() == 'released'
    assert 'cleanup-launch' in provider.calls
    assert start(runtime) == result  # failed start is not silently retried
    reader = EvidenceStore.read_run(service.root / (prepared.submission.run_id + '.argus'))
    assert reader.manifest['writerState'] == 'failed'


def test_missing_or_expired_permit_and_stale_configuration_have_zero_dispatch(runtime):
    service, prepared, graph, permit, provider = runtime
    for invalid in (None, replace(permit, preparation_digest='sha256:' + '0'*64),
                    replace(permit, not_before=permit.not_before - 120, expires_at=permit.expires_at - 120)):
        with pytest.raises(ExecutionInputError):
            service.start(prepared, graph, invalid, idempotency_key='start-once')
    changed = replace(prepared.providers[0], configuration=replace(
        prepared.providers[0].configuration, private_config=b'changed'))
    with pytest.raises(ExecutionInputError, match='MPX-PREPARATION-STALE'):
        service.start(replace(prepared, providers=(changed,)), graph, permit, idempotency_key='start-once')
    assert provider.calls == [] and not provider.output.exists()
    assert not tuple(service.root.glob('*.argus'))


def test_conflicts_and_versions_do_not_dispatch_or_stop_again(runtime):
    service, prepared, graph, permit, provider = runtime
    result = start(runtime)
    with pytest.raises(ExecutionInputError, match='MPX-START-CONFLICT'):
        service.start(prepared, graph, permit, idempotency_key='another-body')
    with pytest.raises(ExecutionInputError, match='MPX-STATE-VERSION-CONFLICT'):
        service.stop(result['runId'], expected_version=result['stateVersion'] - 1)
    assert provider.child.observe() == 'running'
    with pytest.raises(ExecutionInputError, match='MPX-ACTIVE-RUNS'):
        service.close()


def test_recovery_reports_unknown_without_replaying_or_signaling(runtime):
    service, prepared, graph, permit, provider = runtime
    result = start(runtime)
    service.stop(result['runId'], expected_version=result['stateVersion'])
    service.close()
    before = list(provider.calls)
    reopened = PublicExecutionService(service.root, service.host, (provider,))
    try:
        snapshot = reopened.start(prepared, graph, permit, idempotency_key='start-once')
        assert snapshot['state'] == snapshot['cleanup'] == 'unknown'
        assert reopened.stop(result['runId'], expected_version=0) == snapshot
        assert provider.calls == before
    finally:
        reopened.close()


def test_unknown_cleanup_does_not_claim_stopped_and_can_never_signal_by_pid(runtime):
    service, _, _, _, provider = runtime
    result = start(runtime)
    provider.unknown_cleanup = True
    terminal = service.stop(result['runId'], expected_version=result['stateVersion'])
    assert terminal['state'] == terminal['cleanup'] == 'unknown'
    assert provider.child.observe() == 'running'
    before = list(provider.calls)
    assert service.stop(result['runId'], expected_version=terminal['stateVersion']) == terminal
    assert provider.calls == before


def test_argus_open_failure_prevents_effects(runtime, monkeypatch):
    _, _, _, _, provider = runtime
    def fail(*_args, **_kwargs):
        raise OSError('private path')
    monkeypatch.setattr(EvidenceStore, 'open_run', fail)
    result = start(runtime)
    assert result['state'] == 'failed' and result['evidenceWriter'] == 'failed'
    assert provider.calls == []


def test_single_root_owner_and_installation_change_fail_before_effects(runtime):
    service, _, _, _, provider = runtime
    with pytest.raises(ExecutionInputError, match='MPX-RUNTIME-ROOT-BUSY'):
        PublicExecutionService(service.root, service.host, (provider,))
    provider.installation.files[1].path.write_text('changed')
    with pytest.raises(ExecutionInputError, match='MPX-INSTALLATION-CHANGED'):
        start(runtime)
    assert provider.calls == []


def test_writer_fsync_failure_after_launch_still_releases_child_and_stays_failed(runtime, monkeypatch):
    from xverse.argus.writer import EvidenceRun
    original = EvidenceRun.flush_buffer
    calls = 0
    def interrupted(writer):
        nonlocal calls
        calls += 1
        if calls == 5:  # start phase outcome: the actual child already exists
            raise OSError('private filesystem information')
        return original(writer)
    monkeypatch.setattr(EvidenceRun, 'flush_buffer', interrupted)
    _, _, _, _, provider = runtime
    result = start(runtime)
    assert provider.child is not None and provider.child.observe() == 'released'
    assert result['state'] == 'failed' and result['cleanup'] == 'released'
    assert result['evidenceWriter'] == 'failed'
    assert result['failureCode'] == 'MPX-EVIDENCE-WRITE-FAILED'
    assert 'private filesystem' not in json.dumps(result)


def test_kernel_handle_acquisition_failure_retains_partial_child_as_unknown(runtime, monkeypatch):
    import os
    def unavailable(*_args):
        raise OSError('no kernel handle')
    monkeypatch.setattr(os, 'pidfd_open', unavailable)
    _, _, _, _, provider = runtime
    result = start(runtime)
    assert provider.child is not None
    assert result['state'] == result['cleanup'] == 'unknown'
    assert result['failureCode'] == 'MPX-PROCESS-OWNERSHIP-UNAVAILABLE'
    assert provider.child.observe() == 'unknown'


def test_changed_birth_witness_never_sends_a_signal(runtime, monkeypatch):
    import signal
    service, _, _, _, provider = runtime
    result = start(runtime)
    birth = provider.child._birth
    provider.child._birth = 'changed'
    def forbidden(*_args):
        pytest.fail('Ownership mismatch attempted a signal')
    with monkeypatch.context() as guarded:
        guarded.setattr(signal, 'pidfd_send_signal', forbidden)
        assert provider.child.observe() == 'unknown'
        terminal = service.stop(result['runId'], expected_version=result['stateVersion'])
        assert terminal['state'] == terminal['cleanup'] == 'unknown'
    provider.child._birth = birth


def test_read_is_inert_and_runtime_observation_detects_actual_exit(runtime):
    service, _, _, _, provider = runtime
    result = start(runtime)
    before = list(provider.calls)
    assert service.read(result['runId']) == result
    assert provider.calls == before
    live = service.observe(result['runId'], expected_version=result['stateVersion'])
    assert live['state'] == 'running'
    assert live['observations'][-1]['kind'] == 'runtime-observation'
    assert live['observations'][-1]['hostClock']['unit'] == 'ns'
    provider.child.stop(deadline=time.monotonic() + 2)
    terminal = service.observe(result['runId'], expected_version=live['stateVersion'])
    assert terminal['state'] == 'failed' and terminal['cleanup'] == 'released'
    assert terminal['failureCode'] == 'MPX-RUNTIME-EXITED'


def test_permit_expiry_triggers_owned_cleanup_without_a_browser(runtime):
    service, prepared, graph, permit, provider = runtime
    now = time.time()
    short = replace(permit, not_before=now - 1, expires_at=now + 1)
    result = service.start(prepared, graph, short, idempotency_key='short-run')
    assert result['state'] == 'running'
    deadline = time.monotonic() + 4
    while time.monotonic() < deadline:
        observed = service.read(result['runId'])
        if observed['state'] == 'failed':
            break
        time.sleep(.02)
    assert observed['state'] == 'failed' and observed['cleanup'] == 'released'
    assert observed['failureCode'] == 'MPX-RUN-DEADLINE'
    assert provider.child.observe() == 'released'


def test_stop_during_launch_never_advances_to_running_or_replays(runtime, monkeypatch):
    import threading
    service, prepared, _, _, provider = runtime
    launched = threading.Event()
    release = threading.Event()
    original = provider.dispatch
    def paused(phase, configuration, context):
        receipt = original(phase, configuration, context)
        if phase.operation == 'start':
            launched.set()
            assert release.wait(timeout=2)
        return receipt
    monkeypatch.setattr(provider, 'dispatch', paused)
    starts = []
    stops = []
    launch_thread = threading.Thread(target=lambda: starts.append(start(runtime)))
    launch_thread.start()
    try:
        assert launched.wait(timeout=3)
        current = service.read(prepared.submission.run_id)
        stop_thread = threading.Thread(target=lambda: stops.append(service.stop(
            prepared.submission.run_id, expected_version=current['stateVersion'])))
        stop_thread.start()
        assert service._runs[prepared.submission.run_id].cancel.wait(timeout=1)
    finally:
        release.set()
        launch_thread.join(timeout=4)
    stop_thread.join(timeout=4)
    assert not launch_thread.is_alive() and not stop_thread.is_alive()
    assert starts[0]['state'] == stops[0]['state'] == 'failed'
    assert provider.child.observe() == 'released'
    assert 'ready' not in provider.calls


def test_root_replacement_keeps_cleanup_and_evidence_in_original_directory(runtime, monkeypatch):
    service, prepared, _, _, provider = runtime
    prior_root = service.root.with_name('original-service')
    original = provider.dispatch
    def replace_root(phase, configuration, context):
        receipt = original(phase, configuration, context)
        if phase.operation == 'start':
            service.root.rename(prior_root)
            service.root.mkdir(mode=0o700)
        return receipt
    monkeypatch.setattr(provider, 'dispatch', replace_root)
    with pytest.raises(ExecutionInputError, match='MPX-RUNTIME-ROOT-CHANGED'):
        start(runtime)
    assert provider.child.observe() == 'released'
    assert not tuple(service.root.iterdir())
    reader = EvidenceStore.read_run(prior_root / (prepared.submission.run_id + '.argus'))
    assert reader.manifest['writerState'] == 'failed'
    assert service._runs[prepared.submission.run_id].cleanup_state == 'released'


def test_damaged_claim_and_malformed_registry_have_stable_errors(runtime):
    service, prepared, _, _, provider = runtime
    with pytest.raises(ExecutionInputError, match='MPX-RUN-ID-INVALID'):
        service.read([])
    with pytest.raises(ExecutionInputError, match='MPX-PROVIDER-REGISTRY-INVALID'):
        PublicExecutionService(service.root / 'invalid', service.host, [provider])
    claim = service.root / (prepared.submission.run_id + '.claim.json')
    claim.write_text(json.dumps({'runId': prepared.submission.run_id}))
    with pytest.raises(ExecutionInputError, match='MPX-CLAIM-INVALID'):
        start(runtime)
    assert provider.calls == []


def test_aggregate_cleanup_deadline_retains_unknown_instead_of_false_release(runtime, monkeypatch):
    service, _, _, _, provider = runtime
    running = start(runtime)
    service.cleanup_budget_seconds = .01
    original = provider.cleanup
    def slow(phase, configuration, context):
        result = original(phase, configuration, context)
        time.sleep(.03)
        return result
    monkeypatch.setattr(provider, 'cleanup', slow)
    result = service.stop(running['runId'], expected_version=running['stateVersion'])
    assert result['state'] == result['cleanup'] == 'unknown'
    # Intent fsync itself may exhaust this deliberately tiny budget before any
    # signal. Both a still-live child and an exited child must remain unknown to
    # the aggregate result; fixture teardown owns the actual release.
    assert provider.child.observe() in ('running', 'exited', 'released')
    assert 'cleanup-prepare' not in provider.calls


def test_runtime_grant_is_bound_to_actual_root_and_environment(runtime):
    service, prepared, graph, permit, provider = runtime
    for changed in (replace(permit, runtime_binding_digest=None),
                    replace(permit, environment_id='another-host')):
        with pytest.raises(ExecutionInputError):
            service.start(prepared, graph, changed, idempotency_key='wrong-runtime')
    other = PublicExecutionService(service.root / 'other-runtime', service.host, (provider,))
    try:
        with pytest.raises(ExecutionInputError, match='MPX-RUNTIME-BINDING-MISMATCH'):
            other.start(prepared, graph, permit, idempotency_key='wrong-runtime')
    finally:
        other.close()
    assert provider.calls == [] and provider.child is None
    assert not tuple(service.root.glob('*.claim.json'))


def test_changed_installed_command_is_stale_even_when_provider_code_and_xdl_match(runtime):
    service, prepared, graph, permit, provider = runtime
    provider.installation = replace(provider.installation,
        environment=(('HOST_CONFIG_CHANGED', 'true'),))
    with pytest.raises(ExecutionInputError, match='MPX-PREPARATION-STALE'):
        service.start(prepared, graph, permit, idempotency_key='changed-installation')
    assert provider.calls == [] and provider.child is None


def test_unexpected_host_provider_failure_does_not_expose_private_details(runtime, monkeypatch):
    _, _, _, _, provider = runtime
    def unavailable(*_args):
        raise OSError('private host installation path')
    monkeypatch.setattr(provider, 'validate_runtime', unavailable)
    with pytest.raises(ExecutionInputError, match='MPX-PROVIDER-ADMISSION-FAILED') as caught:
        start(runtime)
    assert 'private host' not in str(caught.value) and provider.child is None


def test_interrupted_start_cleans_original_child_before_propagating(runtime, monkeypatch):
    service, prepared, _, _, provider = runtime
    original = provider.dispatch
    def interrupted(phase, configuration, context):
        receipt = original(phase, configuration, context)
        if phase.operation == 'start':
            raise KeyboardInterrupt()
        return receipt
    monkeypatch.setattr(provider, 'dispatch', interrupted)
    with pytest.raises(KeyboardInterrupt):
        start(runtime)
    assert provider.child.observe() == 'released'
    result = service.read(prepared.submission.run_id)
    assert result['state'] == 'failed' and result['cleanup'] == 'released'
