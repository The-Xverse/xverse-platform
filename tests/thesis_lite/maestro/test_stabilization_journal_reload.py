"""Thesis S1 FR-002/FR-003: the M3 journal reload parses only new lines after an unchanged, byte-verified
prefix, and always equals a complete reload; a changed prefix, a replaced file or a broken sequence is
detected exactly as before."""

import json
import os
from dataclasses import replace
from datetime import datetime, timezone

import pytest
from xverse_xdl import lifecycle as lifecycle_module
from xverse_xdl.lifecycle import EvidenceRecord, EvidenceWriteError, FileEvidenceJournal
from xverse_xdl.models import freeze


def _record(index):
    return EvidenceRecord(kind="observation", sequence=0, timestamp=datetime(2026, 10, 23, tzinfo=timezone.utc).isoformat(),
                          execution_id="s1", action_id=f"observe-{index}", catalog_identity="catalog", plan_digest="plan",
                          permit_id=None, permit_nonce=None, status="running", environment_identity="env",
                          resource_revisions=freeze({}), artifact_digests=(), selection=freeze({}))


def _complete(path):
    probe = FileEvidenceJournal.__new__(FileEvidenceJournal)
    probe.path = path
    FileEvidenceJournal._reload(probe)
    return tuple(probe._records)


def test_incremental_reload_equals_complete_reload_across_two_writers(tmp_path, monkeypatch):
    path = tmp_path / "m3.jsonl"
    first, second = FileEvidenceJournal(path), FileEvidenceJournal(path)
    loads = []
    original = json.loads
    monkeypatch.setattr(lifecycle_module.json, "loads", lambda *a, **kw: loads.append(1) or original(*a, **kw))
    for index in range(30):
        (first if index % 3 else second).append(_record(index))
        loads.clear()
        incremental = first.records
        parsed = len(loads)
        assert incremental == _complete(path)
        assert parsed <= 2  # only the new line(s) are parsed after the first complete reload
    assert [r.sequence for r in first.records] == list(range(1, 31))


def test_changed_prefix_byte_is_reparsed_and_still_validated(tmp_path):
    path = tmp_path / "m3.jsonl"
    journal = FileEvidenceJournal(path)
    for index in range(5):
        journal.append(_record(index))
    assert journal.records
    data = path.read_bytes().replace(b'"observe-2"', b'"observe-7"')  # same size, changed content
    with open(path, "r+b") as handle:
        handle.write(data)
    assert [r.action_id for r in journal.records][2] == "observe-7"
    assert journal.records == _complete(path)


def test_broken_sequence_in_prefix_is_detected(tmp_path):
    path = tmp_path / "m3.jsonl"
    journal = FileEvidenceJournal(path)
    for index in range(4):
        journal.append(_record(index))
    assert journal.records
    lines = path.read_bytes().splitlines(keepends=True)
    with open(path, "wb") as handle:
        handle.writelines([lines[0], lines[2], lines[1], lines[3]])
    with pytest.raises(EvidenceWriteError, match="sequence"):
        journal.records


def test_replaced_journal_file_is_reloaded_completely(tmp_path):
    path = tmp_path / "m3.jsonl"
    journal = FileEvidenceJournal(path)
    for index in range(3):
        journal.append(_record(index))
    assert journal.records
    other = tmp_path / "m3.copy"
    other.write_bytes(path.read_bytes().replace(b'"observe-0"', b'"observe-9"'))
    os.replace(other, path)
    assert journal.records[0].action_id == "observe-9" and journal.records == _complete(path)
