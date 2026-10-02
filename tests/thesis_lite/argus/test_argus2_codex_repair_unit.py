"""Regression cases for malformed evidence found in the direct Codex review."""

import json
import os
from unittest.mock import patch

import pytest

from xverse.argus import EvidenceLimits, EvidenceStore
from xverse.argus.recovery import recover_stream

try:
    from tests.thesis_lite.argus import support as S
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import support as S


@pytest.mark.parametrize("field", ["artifacts", "obligations", "limits", "plan",
                                  "sourceByteProvenance", "evidenceReasons", "clockDomains"])
def test_null_manifest_members_cannot_be_assessed_complete(tmp_path, field):
    root = S.synthetic_run(tmp_path / field, S.annotation_event_bytes("e1"), **{field: None})
    reader = EvidenceStore.read_run(root)
    assert reader.diagnostics
    assert json.loads(reader.export_json())["evidenceStatus"] == "incomplete"


@pytest.mark.parametrize("obligation", [None, [], {},
    {"obligationId": "o1", "kind": "no-known-loss", "required": "yes"},
    {"obligationId": "o1", "kind": "min-observations", "required": True, "detail": {"minimum": 0}},
    {"obligationId": "o1", "kind": "no-known-loss", "required": True, "detail": None}])
def test_malformed_nested_obligations_cannot_be_ignored(tmp_path, obligation):
    root = S.synthetic_run(tmp_path / "run", S.annotation_event_bytes("e1"), obligations=[obligation])
    reader = EvidenceStore.read_run(root)
    assert reader.diagnostics
    assert reader.assessed_evidence_status == "incomplete"


@pytest.mark.parametrize("value", [None, True, -1, "1", 9])
def test_manifest_event_count_must_match_verified_records(tmp_path, value):
    root = S.synthetic_run(tmp_path / "run", S.annotation_event_bytes("e1"), eventCount=value)
    reader = EvidenceStore.read_run(root)
    assert reader.diagnostics
    assert reader.assessed_evidence_status == "incomplete"


def test_reader_honours_collection_bounds_before_verification(tmp_path):
    root = S.synthetic_run(tmp_path / "run", S.annotation_event_bytes("e1"),
        artifacts=[{"path": "never-read"}] * 2)
    with patch("xverse.argus.reader.verify_index_entry", side_effect=AssertionError("unbounded verification")):
        reader = EvidenceStore.read_run(root, limits=EvidenceLimits(max_artifacts=1))
    assert reader.assessed_evidence_status == "incomplete"
    assert "ARGUS2-BOUND-EXCEEDED" in {d.code for d in reader.diagnostics}


def test_stream_read_io_failure_returns_stable_diagnostic(tmp_path):
    root = tmp_path / "run"
    root.mkdir()
    (root / "events.jsonl").write_bytes(S.annotation_event_bytes("e1"))
    with patch("xverse.argus.recovery.os.fdopen", side_effect=OSError("read unavailable")):
        result = recover_stream(root, limits=EvidenceLimits())
    assert "ARGUS2-IO-FAILURE" in {d.code for d in result.diagnostics}


def test_artifact_read_io_failure_is_reported_without_traceback(tmp_path):
    run = S.open_run(tmp_path / "run")
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    (tmp_path / "run" / "data.txt").write_bytes(b"data")
    run.record_artifact("data.txt")
    run.finalize()
    original = os.read

    def fail_artifact(descriptor, size):
        if os.readlink(f"/proc/self/fd/{descriptor}").endswith("/data.txt"):
            raise OSError("read unavailable")
        return original(descriptor, size)

    with patch("xverse.argus.artifacts.os.read", side_effect=fail_artifact):
        reader = EvidenceStore.read_run(tmp_path / "run")
    assert reader.manifest["runId"]
    assert reader.records()
    assert "ARGUS2-IO-FAILURE" in {d.code for d in reader.diagnostics}
    assert reader.assessed_evidence_status == "incomplete"


def test_parent_directory_replacement_cannot_redirect_stream_read(tmp_path):
    root = tmp_path / "run"
    (root / "sub").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "sub" / "events.jsonl").write_bytes(S.annotation_event_bytes("inside"))
    (outside / "events.jsonl").write_bytes(S.annotation_event_bytes("outside"))
    original = os.open

    def swap_parent(path, flags, *args, **kwargs):
        descriptor = original(path, flags, *args, **kwargs)
        if path == "sub":
            (root / "sub").rename(root / "held")
            (root / "sub").symlink_to(outside, target_is_directory=True)
        return descriptor

    with patch("xverse.argus.recovery.os.open", side_effect=swap_parent):
        result = recover_stream(root, relative="sub/events.jsonl", limits=EvidenceLimits())
    assert [r["eventId"] for r in result.records] == ["inside"]


def test_event_limit_bounds_short_records_independently_of_byte_limit(tmp_path):
    root = tmp_path / "run"
    root.mkdir()
    records = [json.loads(S.annotation_event_bytes(f"e{i}")) for i in range(3)]
    for i, record in enumerate(records, 1):
        record["ingestionOrdinal"] = i
    from xverse.argus.schema import canonical_bytes

    (root / "events.jsonl").write_bytes(b"".join(canonical_bytes(r) + b"\n" for r in records))
    result = recover_stream(root, limits=EvidenceLimits(max_events=1))
    assert len(result.records) == 1
    assert result.over_read_bound


@pytest.mark.parametrize("field", ["producerSequence", "correlationId", "causationId", "clocks", "extensions"])
def test_present_null_optional_event_field_is_rejected(tmp_path, field):
    from xverse.argus.schema import canonical_bytes

    record = json.loads(S.annotation_event_bytes("e1"))
    record[field] = None
    root = S.synthetic_run(tmp_path / "run", canonical_bytes(record) + b"\n")
    reader = EvidenceStore.read_run(root)
    assert reader.records() == []
    assert reader.assessed_evidence_status == "incomplete"


@pytest.mark.parametrize("field", ["path", "mediaType", "schemaVersion", "bytes", "sha256"])
def test_missing_stream_identity_member_is_not_inferred(tmp_path, field):
    root = S.synthetic_run(tmp_path / "run", S.annotation_event_bytes("e1"))
    manifest = json.loads((root / "manifest.json").read_text())
    del manifest["eventStream"][field]
    (root / "manifest.json").write_text(json.dumps(manifest))
    reader = EvidenceStore.read_run(root)
    assert reader.assessed_evidence_status == "incomplete"
    assert reader.diagnostics


def test_duplicate_manifest_members_are_not_silently_overwritten(tmp_path):
    root = S.synthetic_run(tmp_path / "run", S.annotation_event_bytes("e1"))
    text = (root / "manifest.json").read_text()
    (root / "manifest.json").write_text('{"obligations":null,' + text[1:])
    reader = EvidenceStore.read_run(root)
    assert reader.assessed_evidence_status == "incomplete"
    assert reader.diagnostics


def test_huge_version_component_yields_stable_unsupported_diagnostic(tmp_path):
    root = S.synthetic_run(tmp_path / "run", S.annotation_event_bytes("e1"), schemaVersion="9" * 5000 + ".0")
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-SCHEMA-MAJOR-UNSUPPORTED" in {d.code for d in reader.diagnostics}
    assert json.loads(reader.export_json())["evidenceStatus"] == "incomplete"


@pytest.mark.parametrize("overrides", [
    {"plan": {}},
    {"plan": {"apiVersion": "wrong", "profileVersion": "0.1.0", "planVersion": "1",
              "semanticDigest": {"algorithm": "sha256", "value": "0" * 64}}},
    {"sourceByteProvenance": {"input": {}}},
    {"sourceByteProvenance": {"input": {"algorithm": "sha256", "value": "bad"}}},
    {"openedAt": None}, {"finalizedAt": []}, {"extensions": None},
    {"unexpected": "unowned"}, {"evidenceReasons": ["unknown"]},
    {"metricInputs": [None]},
    {"metricInputs": [{"metricId": "m1", "observerIds": 7}]},
])
def test_nested_manifest_metadata_defects_cannot_be_assessed_complete(tmp_path, overrides):
    root = S.synthetic_run(tmp_path / "run", S.annotation_event_bytes("e1"), **overrides)
    reader = EvidenceStore.read_run(root)
    assert reader.assessed_evidence_status == "incomplete"
    assert reader.diagnostics
    assert json.loads(reader.export_json())["evidenceStatus"] == "incomplete"


def test_duplicate_artifact_identity_is_rejected(tmp_path):
    root = tmp_path / "run"
    run = S.open_run(root)
    (root / "data.txt").write_bytes(b"data")
    run.record_artifact("data.txt")
    run.finalize()
    manifest = json.loads((root / "manifest.json").read_text())
    manifest["artifacts"] *= 2
    (root / "manifest.json").write_text(json.dumps(manifest))
    reader = EvidenceStore.read_run(root)
    assert reader.assessed_evidence_status == "incomplete"
    assert reader.diagnostics
