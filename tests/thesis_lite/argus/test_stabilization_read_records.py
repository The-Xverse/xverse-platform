"""Thesis S1 FR-002/FR-003: ``EvidenceStore.read_records`` resumes a clean, byte-verified read and always
returns exactly the records of a complete ``read_run``; any changed byte, identity or manifest falls back to
a complete read, and damaged evidence never yields a resumable checkpoint."""

from __future__ import annotations

import os

import pytest

from xverse.argus import EvidenceStore
from xverse.argus import reader as reader_module

try:
    from tests.thesis_lite.argus import support as S
except ImportError:  # pragma: no cover - copied tests-directory layout
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parent))
    import support as S


def _full(root):
    return tuple(EvidenceStore.read_run(root).records())


def _append(run, index):
    run.append_event(event_id=f"e{index}", producer_id="p1", event_kind="annotation",
                     clocks={"source": {"domain": "d1", "unit": "ns", "value": index}})
    run.flush_buffer()


def _clean_checkpoint(tmp_path, count=8):
    root = S.run_root(tmp_path)
    run = S.open_run(root)
    for index in range(count):
        _append(run, index)
    records, checkpoint = EvidenceStore.read_records(root)
    assert checkpoint is not None and records == _full(root)
    return root, run, checkpoint


def test_resumed_reads_equal_complete_reads_after_every_append(tmp_path, monkeypatch):
    root = S.run_root(tmp_path)
    run = S.open_run(root)
    calls = []
    original = reader_module.read_run
    monkeypatch.setattr(reader_module, "read_run", lambda *a, **kw: calls.append(1) or original(*a, **kw))
    checkpoint = None
    for index in range(40):
        _append(run, index)
        records, checkpoint = EvidenceStore.read_records(root, checkpoint=checkpoint)
        assert checkpoint is not None
        assert records == tuple(original(root).records())
    assert len(calls) == 1  # only the first read was complete; the others resumed the verified scan


def test_same_size_prefix_rewrite_falls_back_and_matches_complete_read(tmp_path, monkeypatch):
    root, run, checkpoint = _clean_checkpoint(tmp_path)
    stream = root / "events.jsonl"
    data = bytearray(stream.read_bytes())
    position = data.index(b'"e3"') + 2
    data[position] = ord("9")  # same length, changed byte inside an already verified record
    with open(stream, "r+b") as handle:
        handle.write(bytes(data))
    calls = []
    original = reader_module.read_run
    monkeypatch.setattr(reader_module, "read_run", lambda *a, **kw: calls.append(1) or original(*a, **kw))
    records, following = EvidenceStore.read_records(root, checkpoint=checkpoint)
    assert calls, "a changed prefix byte must force a complete read"
    assert records == tuple(original(root).records())
    assert "e3" not in {r["eventId"] for r in records} or records == _full(root)


def test_truncation_falls_back_and_reports_damage(tmp_path):
    root, run, checkpoint = _clean_checkpoint(tmp_path)
    stream = root / "events.jsonl"
    size = stream.stat().st_size
    os.truncate(stream, size - 5)
    records, following = EvidenceStore.read_records(root, checkpoint=checkpoint)
    assert records == _full(root)
    assert following is None  # a truncated stream is damaged: no resumable checkpoint
    assert EvidenceStore.read_run(root).diagnostics


def test_replaced_file_with_new_inode_falls_back(tmp_path, monkeypatch):
    root, run, checkpoint = _clean_checkpoint(tmp_path)
    stream = root / "events.jsonl"
    copy = root / "events.copy"
    copy.write_bytes(stream.read_bytes())
    os.replace(copy, stream)  # identical bytes, different inode
    calls = []
    original = reader_module.read_run
    monkeypatch.setattr(reader_module, "read_run", lambda *a, **kw: calls.append(1) or original(*a, **kw))
    records, _ = EvidenceStore.read_records(root, checkpoint=checkpoint)
    assert calls and records == tuple(original(root).records())


@pytest.mark.parametrize("line", [
    b'{"not":"canonical" }\n',  # non-canonical foreign line
    b"not json\n",
    b"",  # duplicate of an accepted record, filled in below
])
def test_foreign_append_is_scanned_by_the_same_rules(tmp_path, line):
    root, run, checkpoint = _clean_checkpoint(tmp_path)
    stream = root / "events.jsonl"
    if not line:
        line = stream.read_bytes().splitlines(keepends=True)[0]  # duplicate eventId and stale ordinal
    with open(stream, "ab") as handle:
        handle.write(line)
    records, following = EvidenceStore.read_records(root, checkpoint=checkpoint)
    assert records == _full(root)
    assert following is None  # the foreign line produced a diagnostic: never resumable


def test_changed_manifest_forces_complete_read(tmp_path, monkeypatch):
    root, run, checkpoint = _clean_checkpoint(tmp_path)
    run.finalize()  # publishes a new manifest
    calls = []
    original = reader_module.read_run
    monkeypatch.setattr(reader_module, "read_run", lambda *a, **kw: calls.append(1) or original(*a, **kw))
    records, _ = EvidenceStore.read_records(root, checkpoint=checkpoint)
    assert calls and records == tuple(original(root).records())


def test_checkpoint_of_another_root_is_not_used(tmp_path, monkeypatch):
    root, run, checkpoint = _clean_checkpoint(tmp_path)
    other = S.run_root(tmp_path, "other")
    other_run = S.open_run(other)
    _append(other_run, 0)
    calls = []
    original = reader_module.read_run
    monkeypatch.setattr(reader_module, "read_run", lambda *a, **kw: calls.append(1) or original(*a, **kw))
    records, _ = EvidenceStore.read_records(other, checkpoint=checkpoint)
    assert calls and records == tuple(original(other).records())
