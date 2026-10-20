"""IC01–IC08: actual pre-workload directory pins and incremental bounded file I/O."""
import copy
from dataclasses import replace
import os
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.artifacts import (
    ArtifactDeclaration, CollectionAdmission, CollectionError, CollectionSource,
)
from xverse.maestro.time import HostDeadline
from .test_collection import directories, declaration, end, writer


def identity(path):
    value = path.stat()
    return value.st_dev, value.st_ino


def test_early_pin_actual_later_bytes_and_single_binding(directories, monkeypatch):
    source, target = directories
    declarations = [declaration()]
    with CollectionSource(source, identity(source)) as pin:
        # The output appears after the pin; admission must not discover another root.
        (source / 'item').write_bytes(b'actual later output')
        until = end()
        with pin.bind(target, declarations, until, byte_limits=[64]) as admission:
            assert pin.bind(target, declarations, until, byte_limits=[64]) is admission
            row = admission.collect_next(0, until)
            assert row.status == 'collected' and row.content == b'actual later output'
            assert (target / 'copied').read_bytes() == row.content
            assert admission.collect(until).artifacts[0] is row
            with pytest.raises(CollectionError, match='ORIGINAL'):
                pin.bind(target, declarations, end(3), byte_limits=[64])
            with pytest.raises(CollectionError, match='ORIGINAL'):
                pin.bind(target, declarations, until, byte_limits=[65])
            with pytest.raises(CollectionError, match='ORIGINAL'):
                pin.bind(target, declarations, until)
            with pytest.raises(CollectionError, match='ORIGINAL'):
                pin.bind(target, declarations,
                         HostDeadline(until.session, until.monotonic_seconds - 0.1), byte_limits=[64])
            with pytest.raises(CollectionError, match='ORIGINAL'):
                CollectionAdmission(source, target, declarations, until, source_pin=pin)
        with pytest.raises(TypeError):
            copy.copy(pin)


@pytest.mark.parametrize('mode', ['wrong-inode', 'replace', 'missing', 'symlink', 'closed'])
def test_original_source_is_never_replaced_by_later_discovery(directories, mode):
    source, target = directories
    expected = identity(source)
    if mode == 'wrong-inode':
        with pytest.raises(CollectionError, match='ROOT-CHANGED'):
            CollectionSource(source, (expected[0], expected[1] + 1))
        return
    with CollectionSource(source, expected) as pin:
        if mode == 'closed':
            pin.close()
        else:
            source.rename(source.with_name('old'))
            if mode == 'replace':
                source.mkdir()
            elif mode == 'symlink':
                source.symlink_to(source.with_name('old'), target_is_directory=True)
        with pytest.raises(CollectionError, match='ROOT-CHANGED|ORIGINAL'):
            pin.bind(target, [declaration()], end())
    assert not (target / 'copied').exists()


@pytest.mark.parametrize('bad', [True, [1, 2], (True, 2), (1,), (1, -1)])
def test_source_identity_requires_two_exact_nonnegative_integers(directories, bad):
    with pytest.raises(CollectionError, match='SOURCE-IDENTITY'):
        CollectionSource(directories[0], bad)


def test_incremental_order_repeat_and_whole_result_share_actual_rows(directories, monkeypatch):
    source, target = directories
    (source / 'one').write_bytes(b'one')
    (source / 'two').write_bytes(b'two')
    declarations = [declaration(source='one', destination='a'), declaration(source='two', destination='b')]
    until = end()
    with CollectionAdmission(source, target, declarations, until) as admission:
        for invalid in (True, -1, 1, '0', 2):
            with pytest.raises(CollectionError, match='ORDER'):
                admission.collect_next(invalid, until)
        first = admission.collect_next(0, until)
        (source / 'one').write_bytes(b'changed after accepted snapshot')
        with monkeypatch.context() as patch:
            patch.setattr(admission, '_read', lambda *a: pytest.fail('matching repeat rereads'))
            assert admission.collect_next(0, until) is first
        result = admission.collect(until)
        assert result.collection_complete and result.artifacts[0] is first
        assert admission.collect_next(1, until) is result.artifacts[1]
        assert (target / 'a').read_bytes() == b'one'


def test_one_aggregate_end_and_expired_item_outcomes_are_not_retried(directories, monkeypatch):
    source, target = directories
    for name in ('one', 'two'):
        (source / name).write_bytes(b'output')
    until = end()
    declarations = [declaration(source='one', destination='a'), declaration(source='two', destination='b')]
    with CollectionAdmission(source, target, declarations, until) as admission:
        earlier = HostDeadline(until.session, until.monotonic_seconds - 0.1)
        first = admission.collect_next(0, earlier)
        assert first.status == 'collected'
        with pytest.raises(CollectionError, match='ORIGINAL'):
            admission.collect_next(1, end(3))
        monkeypatch.setattr(time, 'monotonic', lambda: until.monotonic_seconds + 1)
        second = admission.collect_next(1, until)
        assert second.status == 'error' and second.diagnostic == 'ML-COLLECTION-TIMEOUT'
        assert admission.collect_next(0, until) is first
        assert admission.collect_next(1, until) is second
        result = admission.collect(until)
        assert not result.collection_complete and result.artifacts == (first, second)
    assert not (target / 'b').exists()


@pytest.mark.parametrize('caps', [[True], [-1], [1048577], [], 'bad'])
def test_original_per_item_cap_shape_rejects_before_files(directories, caps):
    with pytest.raises(CollectionError, match='BYTE-LIMITS'):
        CollectionAdmission(*directories, [declaration()], end(), byte_limits=caps)


def test_each_original_cap_is_applied_before_read_or_copy(directories):
    source, target = directories
    (source / 'one').write_bytes(b'1234')
    (source / 'two').write_bytes(b'')
    until = end()
    declarations = [declaration(source='one', destination='a'), declaration(source='two', destination='b')]
    with CollectionAdmission(source, target, declarations, until, byte_limits=[3, 0]) as admission:
        first = admission.collect_next(0, until)
        second = admission.collect_next(1, until)
        assert first.status == 'error' and first.diagnostic == 'ML-COLLECTION-SIZE'
        assert second.status == 'collected' and second.content == b''
    assert not (target / 'a').exists() and (target / 'b').read_bytes() == b''


def test_shared_total_debit_survives_steps_and_failed_copy(directories):
    source, target = directories
    declarations = []
    for index in range(17):
        (source / str(index)).write_bytes(b'x' * (1 << 20))
        declarations.append(ArtifactDeclaration('unit-' + str(index // 8), 1, str(index), str(index)))
    (target / '0').write_bytes(b'pre-existing target')
    until = end(8)
    with CollectionAdmission(source, target, declarations, until) as admission:
        rows = [admission.collect_next(index, until) for index in range(17)]
        assert rows[0].status == 'error'
        assert sum(row.status == 'collected' for row in rows) == 15
        assert rows[-1].diagnostic == 'ML-COLLECTION-SIZE'
        assert admission.collect(until).artifacts == tuple(rows)
    assert (target / '0').read_bytes() == b'pre-existing target'
    assert not (target / '16').exists()


def test_item_and_whole_index_share_original_ack_and_closed_bytes(directories, monkeypatch):
    source, target = directories
    (source / 'item').write_bytes(b'indexed in a bounded step')
    run = writer(source, target)
    until = end()
    with CollectionAdmission(source, target, [declaration()], until) as admission:
        row = admission.collect_next(0, until)
        with pytest.raises(CollectionError, match='ORIGINAL'):
            admission.index_item(run, 0, replace(row), until)
        entry = admission.index_item(run, 0, row, until)
        with monkeypatch.context() as patch:
            patch.setattr(run, 'record_artifact', lambda *a, **kw: pytest.fail('repeat index'))
            assert admission.index_item(run, 0, row, until) is entry
            assert admission.index(run, admission.collect(until), until) == (entry,)
        run.finalize()
    reader = EvidenceStore.read_run(target)
    assert reader.manifest['artifacts'] == [entry.public_entry()]
    assert not any('ARTIFACT' in item.code for item in reader.diagnostics)


@pytest.mark.parametrize('mode', ['bad-ack', 'lost-ack'])
def test_uncertain_index_is_single_attempt_and_never_republished(directories, monkeypatch, mode):
    source, target = directories
    (source / 'item').write_bytes(b'index may already be durable')
    run = writer(source, target)
    until = end()
    calls = []
    original = run.record_artifact
    def uncertain(*args, **kwargs):
        calls.append(1)
        receipt = original(*args, **kwargs)
        if mode == 'lost-ack':
            raise OSError('owned lost public index ACK')
        receipt['bytes'] = True
        return receipt
    with CollectionAdmission(source, target, [declaration()], until) as admission:
        row = admission.collect_next(0, until)
        monkeypatch.setattr(run, 'record_artifact', uncertain)
        with pytest.raises((OSError, CollectionError)):
            admission.index_item(run, 0, row, until)
        with pytest.raises(CollectionError, match='INDEX-UNCERTAIN'):
            admission.index_item(run, 0, row, until)
        with pytest.raises(CollectionError, match='INDEX-UNCERTAIN'):
            admission.index(run, admission.collect(until), until)
        assert calls == [1]
    run.abort(reason='owned uncertain index')


@pytest.mark.parametrize('mode', ['deadline', 'declaration', 'row'])
def test_same_object_metadata_replacement_cannot_extend_or_rewrite_original(directories, mode):
    source, target = directories
    (source / 'item').write_bytes(b'original output')
    until = end()
    declared = declaration()
    with CollectionAdmission(source, target, [declared], until) as admission:
        row = admission.collect_next(0, until)
        if mode == 'deadline':
            object.__setattr__(until, 'monotonic_seconds', until.monotonic_seconds + 1)
        elif mode == 'declaration':
            object.__setattr__(declared, 'destination', 'changed')
        else:
            object.__setattr__(row, 'content', b'forged output')
        with pytest.raises(CollectionError, match='ORIGINAL'):
            admission.collect_next(0, until)


def test_step_and_index_conflicts_do_not_mutate_cursor(directories):
    source, target = directories
    until = end()
    with CollectionAdmission(source, target, [declaration()], until) as admission:
        admission._lock.acquire()
        try:
            with pytest.raises(CollectionError, match='CONFLICT'):
                admission.collect_next(0, until)
            with pytest.raises(CollectionError, match='CONFLICT'):
                admission.index_item(None, 0, None, until)
        finally:
            admission._lock.release()
        assert admission.collect_next(0, until).status == 'missing'


@pytest.mark.parametrize('whole', [False, True])
def test_changed_original_index_receipt_cannot_rewrite_acknowledged_cache(directories, monkeypatch, whole):
    source, target = directories
    (source / 'item').write_bytes(b'acknowledged original bytes')
    run = writer(source, target)
    until = end()
    with CollectionAdmission(source, target, [declaration()], until) as admission:
        row = admission.collect_next(0, until)
        result = admission.collect(until)
        entry = admission.index(run, result, until)[0] if whole else admission.index_item(run, 0, row, until)
        object.__setattr__(entry, 'sha256', '0' * 64)
        monkeypatch.setattr(run, 'record_artifact', lambda *a, **kw: pytest.fail('mutated repeat index'))
        with pytest.raises(CollectionError, match='INDEX-REPLACED'):
            admission.index_item(run, 0, row, until)
        with pytest.raises(CollectionError, match='INDEX-REPLACED'):
            admission.index(run, result, until)
    run.abort(reason='owned changed original receipt')


def test_unavailable_next_retains_scope_without_read_or_copy(directories, monkeypatch):
    source, target = directories
    (source / 'item').write_bytes(b'untrusted live output')
    until = end()
    with CollectionAdmission(source, target, [declaration(required=False)], until) as admission:
        monkeypatch.setattr(admission, '_read', lambda *a: pytest.fail('unavailable output read'))
        monkeypatch.setattr(admission, '_copy', lambda *a: pytest.fail('unavailable output copy'))
        row = admission.unavailable_next(0, until)
        assert row.status == 'unavailable' and row.content is None
        assert admission.unavailable_next(0, until) is row
        assert not admission.collect(until).collection_complete
    assert not (target / 'copied').exists()


def test_only_admitted_destination_parents_created_for_actual_copy(directories):
    source, target = directories
    (source / 'item').write_bytes(b'actual nested output')
    until = end()
    with CollectionAdmission(source, target, [declaration(destination='one/two/copy')], until,
                             create_parents=True) as admission:
        assert admission.collect_next(0, until).status == 'collected'
    assert (target / 'one/two/copy').read_bytes() == b'actual nested output'
