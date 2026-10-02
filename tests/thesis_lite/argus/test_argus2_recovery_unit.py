"""ARGUS2-SR-006-U: bounded, non-mutating evidence-stream recovery (frozen unit cases)."""

from __future__ import annotations

import os

from xverse.argus import EvidenceLimits, EvidenceStore

try:
    from tests.thesis_lite.argus import support as S
except ImportError:  # pragma: no cover - copied tests-directory layout
    import sys as _argus2_sys
    from pathlib import Path as _argus2_path

    _argus2_sys.path.insert(0, str(_argus2_path(__file__).resolve().parent))
    import support as S


def test_truncated_last_jsonl_record_detected_without_recount(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.append_event(event_id="e2", producer_id="p1", event_kind="annotation")
    run.finalize()
    stream = S.run_root(tmp_path) / "events.jsonl"
    stream.write_bytes(stream.read_bytes().rstrip(b"\n"))
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert "ARGUS2-CORRUPT-STREAM-TRUNCATED" in {item.code for item in reader.diagnostics}
    assert len(reader.records()) == 1
    assert reader.manifest["eventCount"] == 2


def test_recovery_reads_a_bounded_prefix_and_writes_nothing(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    for index in range(3):
        run.append_event(event_id=f"e{index}", producer_id="p1", event_kind="annotation")
    run.finalize()
    root = S.run_root(tmp_path)
    stream = root / "events.jsonl"
    stream.write_bytes(stream.read_bytes() + b'{"partial":')
    before = S.file_hashes(root)
    reader = EvidenceStore.read_run(root)
    records = reader.records()
    assert [item["eventId"] for item in records] == ["e0", "e1", "e2"]
    assert "ARGUS2-CORRUPT-STREAM-TRUNCATED" in {item.code for item in reader.diagnostics}
    assert S.file_hashes(root) == before


def test_recovery_uses_nofollow_and_bounded_reads_without_unbounded_read(tmp_path, monkeypatch):
    import pathlib

    run = S.open_run(S.run_root(tmp_path))
    for index in range(3):
        run.append_event(event_id=f"e{index}", producer_id="p1", event_kind="annotation")
    run.finalize()
    root = S.run_root(tmp_path)

    link_root = tmp_path / "link"
    S.synthetic_run(link_root, S.annotation_event_bytes("e1"))
    (link_root / "events.jsonl").rename(link_root / "events.real.jsonl")
    os.symlink(link_root / "events.real.jsonl", link_root / "events.jsonl")
    assert "ARGUS2-PATH-SYMLINK" in {item.code for item in EvidenceStore.read_run(link_root).diagnostics}

    line = S.annotation_event_bytes("e1")
    over = tmp_path / "over"
    S.synthetic_run(over, line * 4)
    reader = EvidenceStore.read_run(
        over, limits=EvidenceLimits(max_events=1, max_event_bytes=len(line.rstrip(b"\n")))
    )
    assert "ARGUS2-BOUND-EXCEEDED" in {item.code for item in reader.diagnostics}

    def forbidden(self):
        raise AssertionError(f"unbounded read_bytes used on {self}")

    monkeypatch.setattr(pathlib.Path, "read_bytes", forbidden)
    reader = EvidenceStore.read_run(root)
    assert [item["eventId"] for item in reader.records()] == ["e0", "e1", "e2"]
    monkeypatch.undo()
