"""ARGUS2-SR-010-U: bounded read-only replay/export and metric-input links (frozen unit cases)."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess

import pytest

from xverse.argus import EvidenceLimits, EvidenceStore

try:
    from tests.thesis_lite.argus import support as S
except ImportError:  # pragma: no cover - copied tests-directory layout
    import sys as _argus2_sys
    from pathlib import Path as _argus2_path

    _argus2_sys.path.insert(0, str(_argus2_path(__file__).resolve().parent))
    import support as S


def _finalized(tmp_path, name="run", **kwargs):
    run = S.open_run(S.run_root(tmp_path, name), **kwargs)
    for index in range(3):
        run.append_event(event_id=f"e{index}", producer_id="p1", event_kind="annotation")
    return run, run.finalize()


def test_read_run_returns_records_in_ingestion_ordinal_order(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    for index, value in enumerate((30, 20, 10)):
        run.append_event(
            event_id=f"e{index}",
            producer_id="p1",
            event_kind="annotation",
            clocks={"source": {"domain": "d1", "unit": "ns", "value": value}},
        )
    run.finalize()
    records = EvidenceStore.read_run(S.run_root(tmp_path)).records()
    assert [item["ingestionOrdinal"] for item in records] == [1, 2, 3]


def test_repeated_json_export_is_byte_equal(tmp_path):
    _finalized(tmp_path)
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert reader.export_json() == reader.export_json()


def test_repeated_jsonl_export_is_byte_equal(tmp_path):
    _finalized(tmp_path)
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert reader.export_jsonl() == reader.export_jsonl()


def test_reader_verifies_manifest_and_artifact_hashes(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    (S.run_root(tmp_path) / "evidence.json").write_text("{}\n", encoding="utf-8")
    run.record_artifact("evidence.json")
    run.finalize()
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert reader.diagnostics == ()
    assert reader.manifest["artifacts"][0]["path"] == "evidence.json"


def test_corrupt_artifact_yields_diagnostic_and_bounded_partial_result(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    root = S.run_root(tmp_path)
    (root / "evidence.json").write_text('{"v":1}\n', encoding="utf-8")
    run.record_artifact("evidence.json")
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    (root / "evidence.json").write_text('{"v":2}\n', encoding="utf-8")
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-CORRUPT-ARTIFACT-HASH" in {item.code for item in reader.diagnostics}
    assert [item["eventId"] for item in reader.records()] == ["e1"]


def test_reader_bound_exceeded_yields_bounded_partial_result(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    for index in range(4):
        run.append_event(event_id=f"e{index}", producer_id="p1", event_kind="annotation")
    run.finalize()
    before = S.file_hashes(S.run_root(tmp_path))
    reader = EvidenceStore.read_run(S.run_root(tmp_path), limits=EvidenceLimits(max_read_records=2))
    assert len(reader.records()) == 2
    assert "ARGUS2-BOUND-EXCEEDED" in {item.code for item in reader.diagnostics}
    assert S.file_hashes(S.run_root(tmp_path)) == before


def test_metric_inputs_link_to_captured_selection_without_computation(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    root = S.run_root(tmp_path)
    (root / "evidence").mkdir()
    (root / "evidence" / "sample-observer.json").write_text("{}\n", encoding="utf-8")
    run.record_artifact("evidence/sample-observer.json")
    run.finalize()
    entries = EvidenceStore.read_run(root).metric_inputs()
    assert entries
    entry = entries[0]
    assert entry["metricId"] == "sample-count"
    assert entry["observerIds"] == ["sample-observer"]
    assert entry["calculationRef"] and entry["unitSemantics"] and entry["timeDomainIds"]
    assert entry["selection"] == ["evidence/sample-observer.json"]
    assert entry["selectionStatus"] == "complete"


def test_incomplete_metric_selection_is_reported_not_filled(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    run.finalize()
    entries = EvidenceStore.read_run(S.run_root(tmp_path)).metric_inputs()
    entry = entries[0]
    assert entry["selection"] == []
    assert entry["selectionStatus"] == "incomplete"


def test_replay_performs_no_execution_or_oracle_invocation(tmp_path, monkeypatch):
    _finalized(tmp_path)

    def blocked(*args, **kwargs):
        raise AssertionError("replay must not execute components, oracles, subprocesses or sockets")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(subprocess, "run", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert reader.records()
    assert reader.export_json()
    assert reader.export_jsonl()


def test_cli_verify_reports_json_and_exit_status(tmp_path):
    _finalized(tmp_path)
    complete = S.cli("verify", str(S.run_root(tmp_path)))
    assert complete.returncode == 0
    assert json.loads(complete.stdout)["evidenceStatus"] == "complete"

    run = S.open_run(S.run_root(tmp_path, "incomplete"))
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation", causation_id="missing")
    run.finalize()
    incomplete = S.cli("verify", str(S.run_root(tmp_path, "incomplete")))
    assert incomplete.returncode == 1
    assert json.loads(incomplete.stdout)["evidenceStatus"] == "incomplete"

    usage = S.cli("verify")
    assert usage.returncode == 2


def test_cli_export_matches_api_export(tmp_path):
    _finalized(tmp_path)
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    json_export = S.cli("export", str(S.run_root(tmp_path)), "--format", "json")
    assert json_export.returncode == 0
    assert json_export.stdout == reader.export_json()
    jsonl_export = S.cli("export", str(S.run_root(tmp_path)), "--format", "jsonl")
    assert jsonl_export.returncode == 0
    assert jsonl_export.stdout == reader.export_jsonl()


def test_reader_leaves_the_run_root_byte_identical(tmp_path):
    _finalized(tmp_path)
    root = S.run_root(tmp_path)
    before = S.file_hashes(root)
    reader = EvidenceStore.read_run(root)
    reader.records()
    reader.export_json()
    reader.export_jsonl()
    assert S.file_hashes(root) == before


def _good_stream_entry(records: bytes) -> dict:
    return {
        "path": "events.jsonl",
        "mediaType": "application/x-ndjson",
        "schemaVersion": "1.0",
        "bytes": len(records),
        "sha256": hashlib.sha256(records).hexdigest(),
    }


def _write_manifest(root, manifest: dict) -> None:
    (root / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )


def test_reader_rejects_traversal_or_absolute_recorded_path_before_io(tmp_path):
    records = S.annotation_event_bytes("e1")
    good = _good_stream_entry(records)
    cases = {
        "stream-traversal": {"eventStream": {**good, "path": "../escape.jsonl"}},
        "stream-absolute": {"eventStream": {**good, "path": "/etc/passwd"}},
        "artifact-traversal": {
            "artifacts": [
                {
                    "path": "sub/../escape.json",
                    "mediaType": "application/json",
                    "schemaVersion": "1.0",
                    "bytes": 2,
                    "sha256": "00" * 32,
                    "role": "evidence",
                }
            ]
        },
    }
    for name, override in cases.items():
        root = tmp_path / name
        S.synthetic_run(root, records, **override)
        reader = EvidenceStore.read_run(root)
        assert "ARGUS2-PATH-ESCAPE" in {item.code for item in reader.diagnostics}, name
        assert reader.assessed_evidence_status == "incomplete", name


def test_reader_rejects_symlink_manifest_stream_or_artifact_before_io(tmp_path):
    records = S.annotation_event_bytes("e1")

    root = tmp_path / "manifest-link"
    S.synthetic_run(root, records)
    (root / "manifest.json").rename(root / "manifest.real.json")
    os.symlink(root / "manifest.real.json", root / "manifest.json")
    assert "ARGUS2-PATH-SYMLINK" in {item.code for item in EvidenceStore.read_run(root).diagnostics}

    root = tmp_path / "stream-link"
    S.synthetic_run(root, records)
    (root / "events.jsonl").rename(root / "events.real.jsonl")
    os.symlink(root / "events.real.jsonl", root / "events.jsonl")
    assert "ARGUS2-PATH-SYMLINK" in {item.code for item in EvidenceStore.read_run(root).diagnostics}

    root = tmp_path / "artifact-link"
    S.synthetic_run(root, records)
    (tmp_path / "outside.json").write_bytes(b"{}")
    os.symlink(tmp_path / "outside.json", root / "alias.json")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["artifacts"] = [
        {
            "path": "alias.json",
            "mediaType": "application/json",
            "schemaVersion": "1.0",
            "bytes": 2,
            "sha256": "00" * 32,
            "role": "evidence",
        }
    ]
    _write_manifest(root, manifest)
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-PATH-SYMLINK" in {item.code for item in reader.diagnostics}
    assert reader.assessed_evidence_status == "incomplete"


def test_reader_rejects_nonregular_manifest_stream_or_artifact_before_io(tmp_path):
    records = S.annotation_event_bytes("e1")

    root = tmp_path / "manifest-dir"
    root.mkdir()
    (root / "manifest.json").mkdir()
    assert "ARGUS2-PATH-NOT-REGULAR" in {item.code for item in EvidenceStore.read_run(root).diagnostics}

    root = tmp_path / "stream-fifo"
    S.synthetic_run(root, records)
    (root / "events.jsonl").unlink()
    os.mkfifo(root / "events.jsonl")
    assert "ARGUS2-PATH-NOT-REGULAR" in {item.code for item in EvidenceStore.read_run(root).diagnostics}

    root = tmp_path / "artifact-dir"
    S.synthetic_run(root, records)
    (root / "artdir").mkdir()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["artifacts"] = [
        {
            "path": "artdir",
            "mediaType": "application/json",
            "schemaVersion": "1.0",
            "bytes": 0,
            "sha256": "00" * 32,
            "role": "evidence",
        }
    ]
    _write_manifest(root, manifest)
    assert "ARGUS2-PATH-NOT-REGULAR" in {item.code for item in EvidenceStore.read_run(root).diagnostics}


def test_reader_manifest_read_rejected_over_max_manifest_bytes_before_parse(tmp_path):
    root = tmp_path / "run"
    S.synthetic_run(root, S.annotation_event_bytes("e1"))
    before = (root / "manifest.json").read_bytes()
    reader = EvidenceStore.read_run(root, limits=EvidenceLimits(max_manifest_bytes=10))
    assert "ARGUS2-BOUND-EXCEEDED" in {item.code for item in reader.diagnostics}
    assert "max_manifest_bytes" in reader.diagnostics[0].message
    assert reader.records() == []
    assert (root / "manifest.json").read_bytes() == before


def test_reader_event_line_rejected_over_max_event_bytes_before_parse(tmp_path):
    good = S.annotation_event_bytes("e1")
    long_record = {
        "schemaVersion": "1.0",
        "runId": "run-synthetic",
        "eventId": "e2",
        "producerId": "p1",
        "ingestionOrdinal": 2,
        "eventKind": "annotation",
        "annotation": {"text": "x" * 2000},
    }
    long_line = json.dumps(long_record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
    root = tmp_path / "run"
    S.synthetic_run(root, good + long_line)
    reader = EvidenceStore.read_run(root, limits=EvidenceLimits(max_event_bytes=len(good.rstrip(b"\n"))))
    assert "ARGUS2-BOUND-EXCEEDED" in {item.code for item in reader.diagnostics}
    assert any("max_event_bytes" in item.message for item in reader.diagnostics)
    assert [item["eventId"] for item in reader.records()] == ["e1"]


def test_reader_stream_rejected_over_max_events_total_bound(tmp_path):
    first = S.annotation_event_bytes("e1")
    second = S.annotation_event_bytes("e2")
    root = tmp_path / "run"
    S.synthetic_run(root, first + second)
    reader = EvidenceStore.read_run(
        root, limits=EvidenceLimits(max_events=1, max_event_bytes=len(first.rstrip(b"\n")))
    )
    assert "ARGUS2-BOUND-EXCEEDED" in {item.code for item in reader.diagnostics}
    assert any("max_events" in item.message for item in reader.diagnostics)
    assert len(reader.records()) <= 1


def test_reader_caller_limits_authoritative_over_damaged_manifest_echo(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    for index in range(4):
        run.append_event(event_id=f"e{index}", producer_id="p1", event_kind="annotation")
    run.finalize()
    root = S.run_root(tmp_path)
    path = root / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["limits"] = {key: 10**9 for key in EvidenceLimits().to_data()}
    _write_manifest(root, manifest)
    reader = EvidenceStore.read_run(root, limits=EvidenceLimits(max_read_records=2))
    assert len(reader.records()) == 2
    assert "ARGUS2-BOUND-EXCEEDED" in {item.code for item in reader.diagnostics}

    manifest["limits"] = {"bogus": 1}
    _write_manifest(root, manifest)
    reader = EvidenceStore.read_run(root, limits=EvidenceLimits(max_read_records=2))
    assert "ARGUS2-INPUT-FIELD-INVALID" in {item.code for item in reader.diagnostics}
    assert len(reader.records()) == 2


def test_manifest_wrong_container_shape_yields_stable_corrupt_manifest_diagnostic(tmp_path):
    records = S.annotation_event_bytes("e1")
    for name, member, value in (
        ("artifacts", "artifacts", 5),
        ("obligations", "obligations", "x"),
        ("metricInputs", "metricInputs", 7),
        ("eventStream", "eventStream", []),
    ):
        root = tmp_path / name
        S.synthetic_run(root, records)
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        manifest[member] = value
        _write_manifest(root, manifest)
        reader = EvidenceStore.read_run(root)
        assert "ARGUS2-CORRUPT-MANIFEST-SHAPE" in {item.code for item in reader.diagnostics}, name
        assert reader.assessed_evidence_status == "incomplete", name

    root = tmp_path / "array"
    root.mkdir()
    (root / "manifest.json").write_bytes(b"[1,2,3]\n")
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-CORRUPT-MANIFEST-SHAPE" in {item.code for item in reader.diagnostics}
    assert reader.assessed_evidence_status == "incomplete"


def test_event_line_not_a_json_object_yields_stable_corrupt_event_diagnostic(tmp_path):
    for index, payload in enumerate((b"[1,2,3]\n", b"42\n", b'"text"\n', b"null\n")):
        root = tmp_path / f"run{index}"
        S.synthetic_run(root, payload)
        reader = EvidenceStore.read_run(root)
        assert "ARGUS2-CORRUPT-EVENT" in {item.code for item in reader.diagnostics}, payload
        assert reader.records() == []
        assert reader.assessed_evidence_status == "incomplete"


def test_cli_verify_exit_zero_requires_assessed_complete(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    root = S.run_root(tmp_path)
    complete = S.cli("verify", str(root))
    assert complete.returncode == 0
    assert json.loads(complete.stdout)["assessedEvidenceStatus"] == "complete"

    stream = root / "events.jsonl"
    stream.write_bytes(stream.read_bytes().rstrip(b"\n"))
    corrupt = S.cli("verify", str(root))
    assert corrupt.returncode == 1
    payload = json.loads(corrupt.stdout)
    assert payload["recordedEvidenceStatus"] == "complete"
    assert payload["assessedEvidenceStatus"] == "incomplete"


def test_unreadable_manifest_returns_assessed_incomplete_without_fabrication(tmp_path):
    root = tmp_path / "run"
    S.synthetic_run(root, S.annotation_event_bytes("e1"))
    corrupt = b"\xff\xfe not json {"
    (root / "manifest.json").write_bytes(corrupt)
    reader = EvidenceStore.read_run(root)
    assert reader.assessed_evidence_status == "incomplete"
    assert reader.records() == []
    assert reader.diagnostics
    assert (root / "manifest.json").read_bytes() == corrupt


def test_mutating_returned_records_cannot_change_subsequent_read_or_export(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation", annotation={"text": "n"})
    run.finalize()
    root = S.run_root(tmp_path)
    first = EvidenceStore.read_run(root)
    baseline = first.export_json()

    records = first.records()
    records[0]["eventId"] = "evil"
    records[0]["annotation"]["text"] = "mutated"
    manifest = first.manifest
    manifest["runId"] = "evil"
    manifest.setdefault("artifacts", []).append({"path": "evil"})
    for entry in first.metric_inputs():
        entry["selectionStatus"] = "evil"

    assert first.export_json() == baseline
    second = EvidenceStore.read_run(root)
    assert second.records()[0]["eventId"] == "e1"
    assert second.export_json() == baseline
