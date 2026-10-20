"""Real declared transitive quiescence/restart and current-generation guards."""
import copy
import hashlib
import json
import os
from pathlib import Path

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.prbc import BoundaryDescriptor
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_generation_claim import ready, release
from .test_run_renewal import target
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def advance(stack, controller, unit):
    broker, facade, _, _ = stack
    old = broker.issuer(unit).recipe.descriptor
    descriptor = BoundaryDescriptor(old.run_id, unit, old.generation + 1,
        'explicit-' + str(broker.issuer(unit).slot) + '-' + str(old.generation + 1),
        broker.session.boundaries.release_epoch)
    broker.session.boundaries.create_frozen(descriptor)
    end = deadline(1.3)
    prepared = broker._prepare_generation(controller, unit, descriptor, end)
    fresh = broker.advance_generation(prepared, end)
    handle = fresh.stage(end)
    facade.bind(fresh, handle)
    assert facade.start(unit, descriptor, broker.connection, end).ready
    return handle


def test_old_cached_dependent_cleanup_cannot_stop_prerequisite_of_live_replacement(request, monkeypatch):
    stack, controller, leaf, _ = ready(request, monkeypatch)
    broker, facade, _, work = stack
    source = broker.owner._prepared.resource_order[0]
    release(controller, leaf)
    fresh = advance(stack, controller, leaf)
    before = FileEvidenceJournal(work.parent / 'm3.jsonl').records
    with pytest.raises(ValueError, match='DEPENDENTS'):
        controller.phase(source, 'stop', deadline(0.8))
    assert FileEvidenceJournal(work.parent / 'm3.jsonl').records == before
    assert broker.issuer(leaf)._handle is fresh
    assert not broker.owner.latch.cancelled
    assert facade.check_unit_health(source, deadline(0.5)).ready
    assert facade.check_unit_health(leaf, deadline(0.5)).ready


def chain(monkeypatch):
    from . import test_launcher
    original = test_launcher.documents

    def documents():
        data = original()
        system = data['system.json']['spec']
        deployment = data['deployment.json']['spec']
        scenario = data['scenario.json']['spec']
        for name in ('terminal', 'unrelated'):
            instance = copy.deepcopy(system['componentInstances'][1])
            instance.update(id=name + '-instance')
            system['componentInstances'].append(instance)
            binding = copy.deepcopy(deployment['bindings'][1])
            binding['id'] = name + '-binding'
            binding['logicalRef']['element'] = name + '-instance'
            binding['extensions']['io.xverse.experiment']['target']['element'] = name + '-binding'
            deployment['bindings'].append(binding)
            step = copy.deepcopy(scenario['steps'][1])
            step['id'] = 'start-' + name
            step['targetRef']['element'] = name + '-instance'
            ext = step['extensions']['io.xverse.experiment']
            ext['target']['element'] = step['id']
            ext['dependsOn'] = ['start-sink'] if name == 'terminal' else []
            scenario['steps'].append(step)
        system['endpoints'].extend([
            dict(direction='output', id='sink-out', interfaceId='sample-stream', ownerId='sink-instance'),
            dict(direction='input', id='terminal-in', interfaceId='sample-stream', ownerId='terminal-instance')])
        flow = copy.deepcopy(system['flows'][0])
        flow.update(id='second-flow', sourceEndpointId='sink-out', destinationEndpointIds=['terminal-in'])
        system['flows'].append(flow)
        return data

    monkeypatch.setattr(test_launcher, 'documents', documents)


def test_actual_transitive_restart_requires_new_generations_and_fresh_probes(request, monkeypatch):
    chain(monkeypatch)
    stack, controller, _, _ = ready(request, monkeypatch)
    broker, facade, client, work = stack
    units = {u.unit_id.rsplit('/', 1)[-1]: u.unit_id for u in broker.owner._prepared.units}
    source, middle, leaf, sibling = [units[n + '-instance'] for n in ('source', 'sink', 'terminal', 'unrelated')]
    original = {u: broker.issuer(u)._handle for u in units.values()}
    worker = client.process
    broker.renew(target(broker), deadline(1))
    before = FileEvidenceJournal(work.parent / 'm3.jsonl').records
    for unit in (source, middle):
        with pytest.raises(ValueError, match='DEPENDENTS'):
            controller.phase(unit, 'stop', deadline(0.8))
    assert FileEvidenceJournal(work.parent / 'm3.jsonl').records == before
    for unit in (leaf, middle, source):
        release(controller, unit)
        assert facade.check_unit_health(sibling, deadline(0.5)).ready
    epochs = [broker.connection.epoch]
    for unit in (source, middle, leaf):
        broker.renew(target(broker), deadline(1))
        fresh = advance(stack, controller, unit)
        assert fresh.execution_id != original[unit].execution_id
        assert controller.phase(unit, 'cleanup', deadline(0.5)).generation == 1
        assert facade.check_unit_health(unit, deadline(0.5)).ready
        assert facade.check_unit_health(sibling, deadline(0.5)).ready
        epochs.append(broker.connection.epoch)
    assert epochs == [0, 1, 2, 3]
    assert broker.issuer(sibling)._handle is original[sibling]
    assert client.process is worker
    events = EvidenceStore.read_run(work.parent / 'argus').records()
    for unit, expected in [(middle, {source}), (leaf, {source, middle})]:
        payloads = [e['extensions']['xverse.maestro'] for e in events
            if e.get('extensions', {}).get('xverse.maestro', {}).get('unitId') == unit
            and e['extensions']['xverse.maestro'].get('generation') == 2
            and e['extensions']['xverse.maestro'].get('action') == 'ready']
        assert len(payloads) == 1
        deps = payloads[0]['dependencies']
        assert {d['unitId'] for d in deps} == expected
        assert all(d['generation'] == 2 for d in deps)
        assert all(any(e['eventId'] == d['probeEventId']
            and e['extensions']['xverse.maestro']['generation'] == 2 for e in events) for d in deps)
    directory = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if directory:
        (Path(directory) / ('transitive-restart-public-' + str(os.getpid()) + '.json')).write_text(json.dumps(dict(
            public_m3=FileEvidenceJournal(work.parent / 'm3.jsonl').public_records(), argus_events=events,
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            actual_native_epochs=epochs, original_worker_retained=True, unrelated_original_handle_live=True,
            quiescence_order=[leaf, middle, source], restart_order=[source, middle, leaf], full_M1_complete=False)))
