"""IC09–IC11 exact original output admission and actual worker pre-sink pin."""
from dataclasses import replace
import json
from pathlib import Path
import time

import pytest
from xverse.maestro.artifacts import ArtifactDeclaration, CollectionError
from xverse.maestro.collection_plan import admit_collection, bind_collection, decode_collection
from xverse.maestro.coverage import ArtifactExpectation, admit_coverage, canonical
from xverse.maestro.projection import prepare_lifecycle
from .test_preparation import compiled, PIN


def inputs():
    result, resources = compiled()
    prepared = prepare_lifecycle(result, resources, provider_descriptors=(PIN,))
    a, b = [u.unit_id for u in prepared.units]
    ad = admit_coverage(prepared, result, resources, run_id='collection-plan', host_session='collection-host',
        contexts=[(uid, g, uid + '-g' + str(g)) for uid in (a, b) for g in (1, 2)],
        health_policies={uid: (1, 2) for uid in (a, b)}, active_start=0, active_end=5,
        artifacts=[ArtifactExpectation('a-1.bin', unit_id=a, generation=1, maximum_bytes=100),
                   ArtifactExpectation('a-2.bin', required=False, unit_id=a, generation=2, maximum_bytes=200),
                   ArtifactExpectation('collection-result.json', maximum_bytes=4096)])
    return ad, (ArtifactDeclaration(a, 1, 'a/one', 'a-1.bin'),
                ArtifactDeclaration(a, 2, 'a/two', 'a-2.bin', required=False))


def plan(ad, declarations, **changes):
    kwargs = dict(expected_digest=ad.digest, source_root='/owned/output', source_identity=(1, 2),
                  declarations=declarations, metadata_path='collection-result.json', operation_seconds=.5,
                  per_unit_teardown_seconds=1, collection_seconds=2, terminal_seconds=1, drain_seconds=1)
    kwargs.update(changes)
    return admit_collection(ad, **kwargs)


def test_original_full_output_universe_includes_inactive_future_context():
    ad, declarations = inputs()
    admitted = plan(ad, declarations)
    assert admitted.byte_limits == (100, 200)
    assert admitted.terminal_reserve_seconds == 6
    assert admitted.additional_requests == 6
    assert decode_collection(json.loads(admitted.canonical_bytes), ad, ad.digest) == admitted
    assert bind_collection(admitted, ad, ad.digest, generation_ns=11_000_000_000,
                           schedule=None, exports=()) == admitted
    with pytest.raises(CollectionError, match='RESERVE'):
        bind_collection(admitted, ad, ad.digest, generation_ns=10_000_000_000, schedule=None, exports=())


@pytest.mark.parametrize('mode', ['missing', 'extra', 'generation', 'required', 'unit'])
def test_dropped_or_changed_output_is_rejected_before_filesystem(mode):
    ad, declarations = inputs()
    if mode == 'missing':
        declarations = declarations[:1]
    elif mode == 'extra':
        declarations = (*declarations, replace(declarations[0], source='other', destination='extra'))
    else:
        changes = dict(generation=2) if mode == 'generation' else dict(required=False) if mode == 'required' else dict(unit_id='foreign')
        declarations = (replace(declarations[0], **changes), declarations[1])
    with pytest.raises(CollectionError, match='OUTPUT-UNIVERSE'):
        plan(ad, declarations)


@pytest.mark.parametrize('field,value', [('operation_seconds', True), ('collection_seconds', 11),
    ('terminal_seconds', 3), ('per_unit_teardown_seconds', 6), ('drain_seconds', 0),
    ('collection_seconds', float('nan')), ('operation_seconds', float('inf'))])
def test_all_original_budgets_are_explicit_finite_and_bounded(field, value):
    ad, declarations = inputs()
    with pytest.raises(CollectionError, match='BUDGET'):
        plan(ad, declarations, **{field: value})


@pytest.mark.parametrize('mode', ['cap', 'reserve', 'digest', 'extra', 'bool-generation', 'metadata', 'internal', 'root'])
def test_sealed_collection_input_is_independently_rederived(mode):
    ad, declarations = inputs()
    row = json.loads(plan(ad, declarations).canonical_bytes)
    if mode == 'cap': row['byte_limits'][0] += 1
    elif mode == 'reserve': row['terminal_reserve_seconds'] += 1
    elif mode == 'digest': row['coverage_digest'] = 'sha256:' + '0' * 64
    elif mode == 'extra': row['nativeAuthority'] = True
    elif mode == 'bool-generation': row['declarations'][0]['generation'] = True
    elif mode == 'metadata': row['metadata_path'] = 'unknown.json'
    elif mode == 'internal': row['metadata_path'] = 'broker-projection.json'
    elif mode == 'root': row['source_root'] = '/owned/../other'
    with pytest.raises(ValueError):
        decode_collection(row, ad, ad.digest)


def configure_worker(monkeypatch, mode='valid'):
    from . import test_launcher
    from xverse.maestro.public_blobs import admit_broker_artifact
    original = test_launcher.encode_configuration
    saved = {}
    def encode(prepared, result, resources, **kw):
        root = Path(kw['journal_path']).parent / 'work'
        stat = root.stat()
        artifacts = [ArtifactExpectation('collection-result.json', maximum_bytes=4096)]
        ad = admit_coverage(prepared, result, resources, run_id=kw['run_id'], host_session=kw['session'],
            contexts=[(b.unit_id, b.generation, b.execution_id) for b in kw['bindings']],
            health_policies={u.unit_id: (.5, 2) for u in prepared.units},
            active_start=time.monotonic(), active_end=kw['generation_deadline'].monotonic_seconds - 8,
            artifacts=artifacts)
        collection = admit_collection(ad, expected_digest=ad.digest, source_root=str(root),
            source_identity=(stat.st_dev, stat.st_ino + (1 if mode == 'wrong-inode' else 0)),
            declarations=(), metadata_path='collection-result.json', operation_seconds=.5,
            per_unit_teardown_seconds=1, collection_seconds=2, terminal_seconds=1, drain_seconds=1)
        result = original(prepared, result, resources, **kw, coverage=ad,
            broker_artifact=admit_broker_artifact(ad, expected_digest=ad.digest), collection=collection)
        saved.update(config=result, root=root)
        return result
    monkeypatch.setattr(test_launcher, 'encode_configuration', encode)
    return saved


def test_original_worker_rejects_wrong_source_before_journal_or_writer(request, monkeypatch):
    saved = configure_worker(monkeypatch, 'wrong-inode')
    with pytest.raises(ValueError):
        request.getfixturevalue('broker_stack')
    root = saved['root']
    assert not (root.parent / 'm3.jsonl').exists()
    assert not (root.parent / 'argus').exists()
    assert not list(root.glob('*.marker'))


def test_actual_worker_pinned_source_substitution_prevents_first_claim(request, monkeypatch):
    from xverse.argus import EvidenceStore
    saved = configure_worker(monkeypatch)
    broker, facade, client, work = request.getfixturevalue('broker_stack')
    assert json.loads(saved['config'].private_bytes)['version'] == 6
    assert client.collection is saved['config'].collection and client._sequence == 1
    records = EvidenceStore.read_run(work.parent / 'argus').records()
    assert len(records) == 1 and records[0]['producerId'] == 'maestro.validation17'
    old = work.with_name('original-work')
    work.rename(old)
    work.mkdir()
    try:
        with pytest.raises(ValueError):
            broker.owner.commit_intent(client.prepared.units[0].unit_id, deadline(.8))
        assert client._failed and not client._claims
        assert not list(work.glob('*.marker')) and not list(old.glob('*.marker'))
    finally:
        work.rmdir()
        old.rename(work)


def test_original_collection_metadata_pin_rejects_changed_parent_without_rpc(request, monkeypatch):
    saved = configure_worker(monkeypatch)
    broker, facade, client, work = request.getfixturevalue('broker_stack')
    before = client._sequence
    original = client.collection
    client.collection = replace(original)
    try:
        with pytest.raises(ValueError, match='COLLECTION-REPLACED'):
            client._holder()
        assert client._sequence == before
    finally:
        client.collection = original


from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline
