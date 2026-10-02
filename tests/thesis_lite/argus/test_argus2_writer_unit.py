"""ARGUS2-SR-006-U: single-writer state, durability and recovery (frozen unit cases)."""

from __future__ import annotations

import json
import os

import pytest

from xverse.argus import EvidenceError, EvidenceLimits, EvidenceStore

try:
    from tests.thesis_lite.argus import support as S
except ImportError:  # pragma: no cover - copied tests-directory layout
    import sys as _argus2_sys
    from pathlib import Path as _argus2_path

    _argus2_sys.path.insert(0, str(_argus2_path(__file__).resolve().parent))
    import support as S


def _open(tmp_path, name="run", **kwargs):
    return S.open_run(S.run_root(tmp_path, name), **kwargs)


def test_writer_state_transitions_from_open_to_closed(tmp_path):
    run = _open(tmp_path)
    assert run.writer_state == "open"
    run.finalize()
    assert run.writer_state == "closed"


def test_append_after_finalize_is_illegal_transition(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    before = (S.run_root(tmp_path) / "events.jsonl").read_bytes()
    with pytest.raises(EvidenceError) as error:
        run.append_event(event_id="e2", producer_id="p1", event_kind="annotation")
    assert "ARGUS2-STATE-ILLEGAL-TRANSITION" in error.value.codes
    assert (S.run_root(tmp_path) / "events.jsonl").read_bytes() == before


def test_second_in_process_writer_for_same_run_conflict(tmp_path):
    _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        _open(tmp_path)
    assert "ARGUS2-STATE-WRITER-CONFLICT" in error.value.codes


def test_existing_run_root_rejected_before_any_write(tmp_path):
    root = S.run_root(tmp_path)
    root.mkdir()
    before = sorted(item.name for item in root.iterdir())
    with pytest.raises(EvidenceError) as error:
        S.open_run(root)
    assert "ARGUS2-STATE-RUN-EXISTS" in error.value.codes
    assert sorted(item.name for item in root.iterdir()) == before == []


def test_flush_buffer_is_the_appended_line_durability_point(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    data = (S.run_root(tmp_path) / "events.jsonl").read_bytes()
    assert b'"eventId":"e1"' in data
    run.flush_buffer()
    assert (S.run_root(tmp_path) / "events.jsonl").read_bytes() == data


def test_finalize_replaces_manifest_atomically_without_residue(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    root = S.run_root(tmp_path)
    names = sorted(item.name for item in root.iterdir())
    assert names == ["events.jsonl", "manifest.json"]
    assert not any(name.startswith("manifest.json.tmp-") for name in names)


def test_interrupted_finalize_publishes_failed_state(tmp_path, monkeypatch):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    manifest_path = S.run_root(tmp_path) / "manifest.json"
    before_manifest = manifest_path.read_bytes()
    before_stream = (S.run_root(tmp_path) / "events.jsonl").read_bytes()

    def boom(*args, **kwargs):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(EvidenceError) as error:
        run.finalize()
    assert "ARGUS2-IO-FAILURE" in error.value.codes
    assert run.writer_state == "failed"
    assert manifest_path.read_bytes() == before_manifest
    assert (S.run_root(tmp_path) / "events.jsonl").read_bytes() == before_stream


def test_abort_publishes_failed_state_and_best_effort_event(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.abort(reason="caller-stop")
    assert run.writer_state == "failed"
    manifest = EvidenceStore.read_run(S.run_root(tmp_path)).manifest
    assert manifest["writerState"] == "failed"
    assert manifest["evidenceStatus"] != "complete"
    assert b'run-failed' in (S.run_root(tmp_path) / "events.jsonl").read_bytes()


def test_reopen_for_writing_is_refused(tmp_path):
    run = _open(tmp_path)
    run.finalize()
    with pytest.raises(EvidenceError) as error:
        _open(tmp_path)
    assert "ARGUS2-STATE-RUN-EXISTS" in error.value.codes
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert reader.manifest["writerState"] == "closed"


def test_only_manifest_and_stream_are_written_by_the_writer(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.flush_buffer()
    names = sorted(item.name for item in S.run_root(tmp_path).iterdir())
    assert names == ["events.jsonl", "manifest.json"]


def _open_manifest_len(root) -> int:
    # The exact serialized manifest bytes written: canonical JSON plus its single trailing newline.
    return (root / "manifest.json").stat().st_size


def test_finalize_manifest_bound_exceeded_preserves_prior_manifest(tmp_path):
    S.open_run(S.run_root(tmp_path, "probe"))
    open_len = _open_manifest_len(S.run_root(tmp_path, "probe"))
    root = S.run_root(tmp_path, "target")
    run = S.open_run(root, limits=EvidenceLimits(max_manifest_bytes=open_len))
    (root / "evidence.json").write_text("{}\n", encoding="utf-8")
    run.record_artifact("evidence.json")
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    before = (root / "manifest.json").read_bytes()
    with pytest.raises(EvidenceError) as error:
        run.finalize()
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes
    assert "max_manifest_bytes" in error.value.diagnostics[0].message
    assert run.writer_state != "closed"
    assert (root / "manifest.json").read_bytes() == before


def test_abort_manifest_bound_exceeded_preserves_prior_manifest(tmp_path):
    S.open_run(S.run_root(tmp_path, "probe"))
    open_len = _open_manifest_len(S.run_root(tmp_path, "probe"))
    root = S.run_root(tmp_path, "target")
    run = S.open_run(root, limits=EvidenceLimits(max_manifest_bytes=open_len))
    (root / "evidence.json").write_text("{}\n", encoding="utf-8")
    run.record_artifact("evidence.json")
    before = (root / "manifest.json").read_bytes()
    with pytest.raises(EvidenceError) as error:
        run.abort(reason="caller-stop")
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes
    assert "max_manifest_bytes" in error.value.diagnostics[0].message
    assert (root / "manifest.json").read_bytes() == before
    assert run.writer_state != "closed"
