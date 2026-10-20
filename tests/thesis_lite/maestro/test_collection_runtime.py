"""IC12–IC17 actual original collection; synthetic decision tables are labelled."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import time

import pytest
from jsonschema import Draft202012Validator
from xverse.argus import EvidenceStore
from xverse.maestro.artifacts import ArtifactDeclaration
from xverse.maestro.collection_plan import admit_collection
from xverse.maestro.collection_runtime import decode_context, output_available, starts_fenced
from xverse.maestro.coverage import ArtifactExpectation, admit_coverage, canonical
from xverse.maestro.persistence import PersistenceClient
from xverse.maestro.public_blobs import admit_broker_artifact
from xverse.maestro.teardown import ReverseTeardown
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def configure(monkeypatch, *, optional=False, extra=False, missing=False, retained=False):
    from . import test_launcher
    original = test_launcher.encode_configuration
    saved = {}
    def encode(prepared, result, resources, **kw):
        root = Path(kw['journal_path']).parent / 'work'; stat = root.stat()
        declarations = tuple(ArtifactDeclaration(u.unit_id, 1,
            'missing' if missing else u.binding_id + '.marker', 'outputs/' + u.binding_id + '.txt',
            required=not optional) for u in prepared.units)
        if extra:
            u = prepared.units[0]
            declarations += (ArtifactDeclaration(u.unit_id, 1, 'optional-absent', 'outputs/optional.txt', required=False),)
        artifacts = [ArtifactExpectation(d.destination, d.required, 32, d.unit_id, d.generation) for d in declarations]
        artifacts += [ArtifactExpectation('collection-result.json', maximum_bytes=16384)]
        ad = admit_coverage(prepared, result, resources, run_id=kw['run_id'], host_session=kw['session'],
            contexts=[(b.unit_id, b.generation, b.execution_id) for b in kw['bindings']],
            health_policies={u.unit_id: (.5, 2) for u in prepared.units}, active_start=time.monotonic(),
            active_end=kw['generation_deadline'].monotonic_seconds - 8, artifacts=artifacts)
        plan = admit_collection(ad, expected_digest=ad.digest, source_root=str(root),
            source_identity=(stat.st_dev, stat.st_ino), declarations=declarations,
            metadata_path='collection-result.json', operation_seconds=.5, per_unit_teardown_seconds=1,
            collection_seconds=2, terminal_seconds=1, drain_seconds=1)
        additional = {}
        if retained:
            from xverse.maestro.evidence import PublicExport
            additional['public_exports'] = (PublicExport('retained-inputs.json', 1 << 20),)
        config = original(prepared, result, resources, **kw, coverage=ad,
            broker_artifact=admit_broker_artifact(ad, expected_digest=ad.digest), collection=plan, **additional)
        saved.update(config=config, root=root)
        return config
    monkeypatch.setattr(test_launcher, 'encode_configuration', encode)
    return saved


def start_and_stop(stack):
    broker, facade, client, work = stack
    until = stage_all(stack)
    for uid in client.prepared.resource_order:
        issuer = broker.issuer(uid)
        assert facade.start(uid, issuer.recipe.descriptor, broker.connection, until).ready
    until = time.monotonic() + .5
    while not all((work / (u.binding_id + '.marker')).exists() for u in client.prepared.units):
        assert time.monotonic() < until, 'owned native workload did not produce its declared marker'
        time.sleep(.005)
    stopper = ReverseTeardown(facade, per_unit_seconds=.8)
    observations = []
    for name in ('_record', '_cleanup'):
        original = getattr(stopper, name)
        def observed(*args, _original=original, _name=name, **kwargs):
            began = time.monotonic(); error = None
            try:
                return _original(*args, **kwargs)
            except Exception as exc:
                error = dict(type=type(exc).__name__, code=str(exc) if str(exc).startswith('ML-') else None,
                             errno=getattr(exc, 'errno', None))
                raise
            finally:
                from xverse.maestro.time import HostDeadline
                ends = [v.monotonic_seconds for v in args if type(v) is HostDeadline]
                observations.append(dict(method=_name, began=began, ended=time.monotonic(),
                    deadline=ends[-1] if ends else None, diagnostic=error))
        setattr(stopper, name, observed)
    try:
        cleanup = stopper.run(deadline(3))
    finally:
        receipt_root = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
        if receipt_root:
            (Path(receipt_root) / ('collection-teardown-observations-' + work.parent.name + '.json')).write_text(
                json.dumps(dict(operations=observations, assertions_and_bounds_unchanged=True,
                                timing_instrumentation=True), indent=2) + '\n')
    assert cleanup.unit_cleanup_complete and cleanup.normal_records_complete
    return cleanup


def metadata(client, work, receipt):
    body = receipt.public_data(); raw = (work.parent / 'argus' / body['entry']['path']).read_bytes()
    assert body['entry']['bytes'] == len(raw)
    assert body['entry']['sha256'] == hashlib.sha256(raw).hexdigest()
    result = json.loads(raw)
    assert result['runId'] == client.run_id and result['admissionDigest'] == client.coverage_digest
    assert result['hostSession'] == client.session and result['contextDigest'] == body['contextDigest']
    assert result['contextDigest'] == 'sha256:' + hashlib.sha256(canonical(result['context'])).hexdigest()
    return result


def retain(client, work, receipt, data, *, case='nominal', **extra):
    root = os.environ.get('MAESTRO_BOUNDARY_RECEIPTS')
    if root:
        (Path(root) / ('collection-runtime-public-' + str(os.getpid()) + '-' + case + '.json')).write_text(json.dumps(dict(
            metadata=data, receipt=receipt.public_data(), admission=json.loads(client.coverage.public_bytes),
            admission_digest=client.coverage_digest, source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            original_fixture=str(work.parent), full_M1_complete=False, scientific_result=False, **extra), indent=2) + '\n')


def test_actual_original_native_outputs_index_metadata_event_and_matching_repeat(request, monkeypatch):
    configure(monkeypatch, extra=True)
    stack = request.getfixturevalue('broker_stack'); broker, facade, client, work = stack
    start_and_stop(stack)
    end = deadline(2)
    receipt = client.collect_outputs(broker, end)
    result = metadata(client, work, receipt)
    assert result['collectionComplete'] and result['startsFenced'] and not receipt.lifecycle_complete
    assert [r['status'] for r in result['items']] == ['collected', 'collected', 'missing']
    assert [r['required'] for r in result['items']] == [True, True, False]
    for row in result['items'][:2]:
        assert row['bytes'] == 5 and row['sha256'] == hashlib.sha256(b'EXEC\n').hexdigest()
        assert (work.parent / 'argus' / row['destination']).read_bytes() == b'EXEC\n'
    assert all(r['directChildReaped'] is True and r['c1Empty'] is True and r['c1Released'] is True
               for r in result['context']['broker']['generations'])
    count = client._sequence
    with monkeypatch.context() as patch:
        patch.setattr(PersistenceClient, '_rpc', lambda *a, **kw: pytest.fail('repeat collection RPC'))
        assert client.collect_outputs(broker, end) is receipt
        with pytest.raises(ValueError):
            client.collect_outputs(broker, deadline(1))
        assert client._sequence == count
    event = receipt.public_data()['event']
    validator = Draft202012Validator(json.loads(Path(__file__).with_name('lifecycle-payload-v2.schema.json').read_text()))
    validator.validate(event['extensions']['xverse.maestro'])
    assert event['extensions']['xverse.maestro']['action'] == 'collect'
    assert event['clocks']['host']['value'] >= result['finishedAt'] >= result['startedAt']
    assert not any(e.get('extensions', {}).get('xverse.maestro', {}).get('action') == 'run-terminal'
                   for e in EvidenceStore.read_run(work.parent / 'argus').records())
    client.abort(deadline(.8))
    reader = EvidenceStore.read_run(work.parent / 'argus')
    assert receipt.public_data()['entry'] in reader.manifest['artifacts']
    assert not any('ARTIFACT' in d.code or 'CAUSAL' in d.code for d in reader.diagnostics)
    retain(client, work, receipt, result)


def test_actual_collection_retained_inputs_and_provisional_coverage_after_closed_reader(request, monkeypatch):
    from xverse.maestro.coverage import assess_preclosure
    configure(monkeypatch, retained=True)
    stack = request.getfixturevalue('broker_stack'); broker, facade, client, work = stack
    start_and_stop(stack)
    receipt = client.collect_outputs(broker, deadline(2)); data = metadata(client, work, receipt)
    published = client.publish_broker_artifact(broker, deadline(.8))
    export = client.export_public_inputs(client._public_exports[0], deadline(.8))
    client.abort(deadline(.8))
    root = work.parent / 'argus'; reader = EvidenceStore.read_run(root)
    assert reader.manifest['writerState'] == 'failed'
    assert not any('ARTIFACT' in d.code or 'CAUSAL' in d.code for d in reader.diagnostics)
    retained = json.loads((root / export.declaration.relative_path).read_bytes())
    projection = published.public_data()
    actual_broker = json.loads((root / projection['entry']['path']).read_bytes())
    entries = reader.manifest['artifacts']
    actual_bytes = {e['path']: (root / e['path']).read_bytes() for e in entries}
    report = assess_preclosure(client.coverage, expected_admission_digest=client.coverage_digest,
        annotations=retained['annotations'], public_m3=retained['publicM3'], broker=actual_broker,
        artifact_entries=entries, artifact_bytes=actual_bytes).report()
    assert next(r for r in report['rows'] if r['obligationId'] == 'ob.collect')['status'] == 'satisfied'
    assert next(r for r in report['rows'] if r['obligationId'] == 'ob.run-terminal')['status'] == 'missing'
    assert report['overallStatus'] == 'incomplete'
    retain(client, work, receipt, data, case='coverage', retained=retained, broker=actual_broker,
           provisional_report=report, actual_entries=entries)


@pytest.mark.parametrize('issued', [False, True])
def test_actual_never_issued_or_live_output_is_unavailable_even_when_optional(request, monkeypatch, issued):
    configure(monkeypatch, optional=True)
    stack = request.getfixturevalue('broker_stack'); broker, facade, client, work = stack
    if issued:
        until = stage_all(stack)
        uid = client.prepared.resource_order[0]; issuer = broker.issuer(uid)
        assert facade.start(uid, issuer.recipe.descriptor, broker.connection, until).ready
    else:
        for u in client.prepared.units:
            (work / (u.binding_id + '.marker')).write_bytes(b'pre-existing untrusted bytes')
    receipt = client.collect_outputs(broker, deadline(2)); result = metadata(client, work, receipt)
    assert not result['collectionComplete'] and all(r['status'] == 'unavailable' for r in result['items'])
    assert all(r['bytes'] is None and r['entry'] is None for r in result['items'])
    assert not (work.parent / 'argus' / 'outputs').exists()
    assert receipt.public_data()['event']['extensions']['xverse.maestro']['outcome'] == 'unknown'


@pytest.mark.parametrize('optional', [False, True])
def test_actual_quiescent_required_and_optional_missing_are_distinct(request, monkeypatch, optional):
    configure(monkeypatch, optional=optional, missing=True)
    stack = request.getfixturevalue('broker_stack'); broker, facade, client, work = stack
    start_and_stop(stack)
    receipt = client.collect_outputs(broker, deadline(2)); result = metadata(client, work, receipt)
    assert [r['status'] for r in result['items']] == ['missing', 'missing']
    assert result['collectionComplete'] is optional


@pytest.mark.parametrize('mode', ['symlink', 'oversized', 'existing-destination', 'metadata-conflict'])
def test_actual_output_or_metadata_failure_never_overwrites_or_gains_trusted_credit(request, monkeypatch, tmp_path, mode):
    configure(monkeypatch)
    stack = request.getfixturevalue('broker_stack'); broker, facade, client, work = stack
    start_and_stop(stack)
    root = work.parent / 'argus'; d = client.collection.declarations[0]
    if mode == 'symlink':
        (work / d.source).unlink(); (work / d.source).symlink_to(work / client.collection.declarations[1].source)
    elif mode == 'oversized':
        (work / d.source).write_bytes(b'x' * 33)
    elif mode == 'existing-destination':
        (root / 'outputs').mkdir(); (root / d.destination).write_bytes(b'pre-existing')
    else:
        (root / 'collection-result.json').write_bytes(b'pre-existing metadata')
    if mode == 'metadata-conflict':
        with pytest.raises(ValueError):
            client.collect_outputs(broker, deadline(2))
        assert (root / 'collection-result.json').read_bytes() == b'pre-existing metadata'
        assert not any(e.get('extensions', {}).get('xverse.maestro', {}).get('action') == 'collect'
                       for e in EvidenceStore.read_run(root).records())
    else:
        receipt = client.collect_outputs(broker, deadline(2)); result = metadata(client, work, receipt)
        assert not result['collectionComplete'] and result['items'][0]['status'] == 'error'
        assert result['items'][0]['entry'] is None and result['items'][0]['sha256'] is None
        if mode == 'existing-destination':
            assert (root / d.destination).read_bytes() == b'pre-existing'


@pytest.mark.parametrize('mode', ['begin', 'item', 'finish', 'lost-finish'])
def test_actual_bad_or_lost_ack_retains_uncertainty_without_second_collection(request, monkeypatch, mode):
    configure(monkeypatch)
    stack = request.getfixturevalue('broker_stack'); broker, facade, client, work = stack
    start_and_stop(stack); rpc = PersistenceClient._rpc
    def damaged(self, kind, body, until, **kwargs):
        op, end, result = rpc(self, kind, body, until, **kwargs)
        if mode == 'begin' and kind == 'public-blob' and body['purpose'] == 'collection-context':
            result['contextDigest'] = 'sha256:' + '0' * 64
        elif mode == 'item' and kind == 'collect' and body['action'] == 'item':
            result['item']['sha256'] = result['item']['entry']['sha256'] = '0' * 64
        elif kind == 'collect' and body['action'] == 'finish':
            if mode == 'finish':
                result['entry']['sha256'] = '0' * 64; result['metadataDigest'] = 'sha256:' + '0' * 64
            elif mode == 'lost-finish':
                raise ValueError('owned lost original collection finish ACK')
        return op, end, result
    with monkeypatch.context() as patch:
        patch.setattr(PersistenceClient, '_rpc', damaged)
        until = deadline(2)
        with pytest.raises(ValueError):
            client.collect_outputs(broker, until)
        count = client._sequence
        with pytest.raises(ValueError):
            client.collect_outputs(broker, until)
        assert client._sequence == count and client._failed and client._collection_outcome is None


def test_invalid_collection_end_conflicts_and_copied_plan_reject_before_cancellation(request, monkeypatch):
    configure(monkeypatch)
    broker, facade, client, work = request.getfixturevalue('broker_stack')
    before = client._sequence
    with pytest.raises(ValueError): client.collect_outputs(broker, deadline(3))
    client._collection_lock.acquire()
    try:
        with pytest.raises(ValueError): client.collect_outputs(broker, deadline(2))
    finally: client._collection_lock.release()
    original = client.collection; client.collection = replace(original)
    try:
        with pytest.raises(ValueError): client.collect_outputs(broker, deadline(2))
    finally: client.collection = original
    assert client._sequence == before and not broker.owner.latch.cancelled and not client._collection_attempted


@pytest.mark.parametrize('mode', ['native', 'dead-unreaped', 'dead-reaped', 'flags-only', 'wait-unknown', 'c1-live', 'unissued'])
def test_synthetic_closed_quiescence_table_never_uses_local_flags_as_authority(tmp_path, mode):
    from .test_coverage import Fixture
    f = Fixture(tmp_path)
    try:
        b = deepcopy(f.broker)
        ad = admit_coverage(f.prepared, f.result, f.resources, run_id='coverage-fixture', host_session='coverage-host',
            contexts=[(r['unitId'], r['generation'], r['executionId']) for r in f.ad['contexts']],
            health_policies={u.unit_id: (1, 5) for u in f.units}, active_start=0, active_end=5,
            artifacts=[ArtifactExpectation('output.bin', unit_id=f.a, generation=1), ArtifactExpectation('collection.json')])
        d = ArtifactDeclaration(f.a, 1, 'output', 'output.bin')
        plan = admit_collection(ad, expected_digest=ad.digest, source_root=str(tmp_path), source_identity=(1, 2),
            declarations=[d], metadata_path='collection.json', operation_seconds=.5, per_unit_teardown_seconds=1,
            collection_seconds=2, terminal_seconds=1, drain_seconds=1)
        b['cancellationRequested'] = True
        for r in b['generations']: r.update(c1Empty=True, c1TerminationObserved=False)
        native = mode in ('native', 'wait-unknown', 'c1-live', 'unissued')
        if native:
            b['nativeCancellationAcknowledged'] = True
            b['epochs'].append(dict(kind='cancelled', epoch=1, sequence=1))
        dead = mode in ('dead-unreaped', 'dead-reaped')
        b['authorityRevocationRequested'] = dead or mode == 'flags-only'
        ctx = dict(schemaVersion='1.0', broker=b, authority=dict(issuerDead=dead, issuerReaped=mode == 'dead-reaped'),
                   collectionDeadlineNs=time.monotonic_ns() + 1_000_000_000)
        if mode == 'wait-unknown': b['generations'][0]['directChildReaped'] = None
        if mode == 'c1-live': b['generations'][0].update(c1Empty=False, c1Released=False)
        if mode == 'unissued':
            b['generations'][0].update(issued=False, stageAttempted=False, releaseObserved=False, handleRef=None,
                releaseRequestedAt=None, releaseAcknowledgedAt=None)
        decoded = decode_context(canonical(ctx), ad, ad.digest, plan, time.monotonic_ns() + 5_000_000_000, time.monotonic())
        assert starts_fenced(decoded) is native or mode == 'dead-reaped'
        assert output_available(decoded, d) is (mode in ('native', 'dead-reaped'))
    finally: f.writer.abort(reason='Synthetic quiescence decision table; no native proof')
