"""ARGUS2-SR-002-U: versioned event stream and atomic run manifest (frozen unit cases)."""

from __future__ import annotations

import copy
import json

import pytest

from xverse.argus import EvidenceError, EvidenceLimits, EvidenceStore

try:
    from tests.thesis_lite.argus import support as S
except ImportError:  # pragma: no cover - copied tests-directory layout
    import sys as _argus2_sys
    from pathlib import Path as _argus2_path

    _argus2_sys.path.insert(0, str(_argus2_path(__file__).resolve().parent))
    import support as S


def _manifest(root) -> dict:
    return json.loads((root / "manifest.json").read_text(encoding="utf-8"))


def _open(tmp_path, **kwargs):
    return S.open_run(S.run_root(tmp_path), **kwargs)


def test_append_event_writes_one_canonical_jsonl_line(tmp_path):
    run = _open(tmp_path)
    ordinal = run.append_event(
        event_id="e1", producer_id="p1", event_kind="annotation", annotation={"text": "n"}
    )
    assert ordinal == 1
    raw = (S.run_root(tmp_path) / "events.jsonl").read_bytes()
    assert raw.endswith(b"\n") and raw.count(b"\n") == 1
    parsed = json.loads(raw.decode("utf-8"))
    canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":"), allow_nan=False)
    assert canonical.encode("utf-8") + b"\n" == raw
    assert run.finalize().event_count == 1


def test_open_manifest_published_with_open_state_before_appends(tmp_path):
    run = _open(tmp_path)
    assert run.writer_state == "open"
    manifest = _manifest(S.run_root(tmp_path))
    assert manifest["writerState"] == "open"
    assert manifest["evidenceStatus"] == "unassessed"
    assert manifest["eventStream"]["bytes"] == 0
    assert manifest["eventStream"]["sha256"] == __import__("hashlib").sha256(b"").hexdigest()


def test_finalize_satisfied_obligations_publishes_complete_manifest(tmp_path):
    run = _open(
        tmp_path,
        obligations=[{"obligationId": "o1", "kind": "no-known-loss", "required": True}],
    )
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    manifest = run.finalize()
    assert manifest.writer_state == "closed"
    assert manifest.evidence_status == "complete"
    assert manifest.evidence_reasons == []


def test_finalize_unmet_required_obligation_classified_incomplete(tmp_path):
    run = _open(
        tmp_path,
        obligations=[{"obligationId": "o1", "kind": "causal-closure", "required": True}],
    )
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.append_event(event_id="e2", producer_id="p1", event_kind="annotation", causation_id="e9")
    manifest = run.finalize()
    assert manifest.writer_state == "closed"
    assert manifest.evidence_status == "incomplete"
    assert "ARGUS2-REASON-UNMET-OBLIGATION" in manifest.evidence_reasons
    assert "ARGUS2-REASON-UNRESOLVED-CAUSATION" in manifest.evidence_reasons


def test_closed_stream_with_missing_artifact_classified_incomplete(tmp_path):
    run = _open(tmp_path)
    (S.run_root(tmp_path) / "evidence.json").write_text('{"a":1}\n', encoding="utf-8")
    run.record_artifact("evidence.json")
    (S.run_root(tmp_path) / "evidence.json").unlink()
    manifest = run.finalize()
    assert manifest.evidence_status == "incomplete"
    assert "ARGUS2-REASON-MISSING-ARTIFACT" in manifest.evidence_reasons
    assert "ARGUS2-MISSING-ARTIFACT" in {item.code for item in manifest.diagnostics}


def test_truncated_last_record_classified_incomplete(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    stream = S.run_root(tmp_path) / "events.jsonl"
    stream.write_bytes(stream.read_bytes().rstrip(b"\n"))
    run.finalize()
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    codes = {item.code for item in reader.diagnostics}
    assert "ARGUS2-CORRUPT-STREAM-TRUNCATED" in codes
    manifest = _manifest(S.run_root(tmp_path))
    assert "ARGUS2-REASON-TRUNCATED-STREAM" in manifest["evidenceReasons"]
    assert manifest["evidenceStatus"] == "incomplete"
    assert manifest["eventCount"] == 0


def test_known_loss_never_upgraded_to_complete_by_finalize(tmp_path):
    run = _open(tmp_path)
    run.import_observation(
        S.projection(
            [
                S.observation_record(
                    payloadViewState="omitted",
                    visibleBytesHex="",
                    visibleByteCount=0,
                    counters={"queued": 1, "accepted": 1, "dropped": 1, "coalesced": 0},
                )
            ]
        )
    )
    manifest = run.finalize()
    assert manifest.evidence_status == "incomplete"
    assert "ARGUS2-REASON-KNOWN-LOSS" in manifest.evidence_reasons


def test_stream_closure_and_evidence_completeness_are_separate_facts(tmp_path):
    run = _open(
        tmp_path,
        obligations=[{"obligationId": "o1", "kind": "causal-closure", "required": True}],
    )
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation", causation_id="e9")
    manifest = run.finalize()
    assert manifest.writer_state == "closed"
    assert manifest.evidence_status == "incomplete"


def test_artifact_index_entry_carries_frozen_fields(tmp_path):
    run = _open(tmp_path)
    (S.run_root(tmp_path) / "evidence.json").write_text('{"a":1}\n', encoding="utf-8")
    entry = run.record_artifact("evidence.json", media_type="application/json", role="evidence")
    manifest = run.finalize()
    indexed = manifest.artifacts[0]
    assert indexed["path"] == "evidence.json"
    assert indexed["mediaType"] == "application/json"
    assert indexed["schemaVersion"] == "1.0"
    assert isinstance(indexed["bytes"], int)
    assert indexed["sha256"] == entry["sha256"]
    assert indexed["role"] == "evidence"
    paths = [item["path"] for item in manifest.artifacts]
    assert len(paths) == len(set(paths))


def test_event_count_and_stream_hash_match_file_on_finalize(tmp_path):
    run = _open(tmp_path)
    for index in range(3):
        run.append_event(event_id=f"e{index}", producer_id="p1", event_kind="annotation")
    manifest = run.finalize()
    raw = (S.run_root(tmp_path) / "events.jsonl").read_bytes()
    assert manifest.event_count == 3
    assert manifest.data["eventStream"]["bytes"] == len(raw)
    assert manifest.data["eventStream"]["sha256"] == __import__("hashlib").sha256(raw).hexdigest()


def test_unsupported_manifest_major_version_rejected_on_read(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    path = S.run_root(tmp_path) / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["schemaVersion"] = "2.0"
    path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    original = path.read_bytes()
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert "ARGUS2-SCHEMA-MAJOR-UNSUPPORTED" in {item.code for item in reader.diagnostics}
    assert reader.records() == []
    assert path.read_bytes() == original


def test_extensions_namespaces_are_preserved_verbatim(tmp_path):
    run = _open(tmp_path)
    run.append_event(
        event_id="e1",
        producer_id="p1",
        event_kind="annotation",
        extensions={"argus.note": {"v": [1, 2, 3]}},
    )
    run.finalize()
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    document = json.loads(reader.export_json())
    record = [item for item in document["records"] if item["eventId"] == "e1"][0]
    assert record["extensions"] == {"argus.note": {"v": [1, 2, 3]}}


# Keep a copy import used by future cases without altering the frozen identifier set.
_ = copy


def _open_len(root) -> int:
    # The exact serialized manifest bytes written: canonical JSON plus its single trailing newline.
    return (root / "manifest.json").stat().st_size


def test_reader_exposes_recorded_and_assessed_status_separately(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert reader.recorded_evidence_status == "complete"
    assert reader.recorded_evidence_reasons == []
    assert reader.assessed_evidence_status == "complete"
    assert reader.assessed_evidence_reasons == []
    document = json.loads(reader.export_json())
    assert document["assessedEvidenceStatus"] == "complete"
    assert document["recordedEvidenceStatus"] == "complete"
    assert document["evidenceStatus"] == "complete"


def test_manifest_recorded_complete_with_corrupt_stream_assessed_incomplete(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    stream = S.run_root(tmp_path) / "events.jsonl"
    stream.write_bytes(stream.read_bytes().rstrip(b"\n"))
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert reader.recorded_evidence_status == "complete"
    assert reader.assessed_evidence_status == "incomplete"
    assert "ARGUS2-REASON-TRUNCATED-STREAM" in reader.assessed_evidence_reasons
    assert "ARGUS2-REASON-CORRUPT-EVENT" in reader.assessed_evidence_reasons
    document = json.loads(reader.export_json())
    assert document["evidenceStatus"] == "incomplete"
    assert document["recordedEvidenceStatus"] == "complete"


def test_corrupt_manifest_never_exported_as_primary_complete(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    path = S.run_root(tmp_path) / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["artifacts"] = 5
    path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert "ARGUS2-CORRUPT-MANIFEST-SHAPE" in {item.code for item in reader.diagnostics}
    assert reader.recorded_evidence_status == "complete"
    assert reader.assessed_evidence_status == "incomplete"
    assert "ARGUS2-REASON-CORRUPT-MANIFEST" in reader.assessed_evidence_reasons
    document = json.loads(reader.export_json())
    assert document["evidenceStatus"] == "incomplete"


def test_manifest_bound_measured_on_actual_serialized_bytes_at_open_finalize_and_abort(tmp_path):
    S.open_run(S.run_root(tmp_path, "probe"))
    open_len = _open_len(S.run_root(tmp_path, "probe"))

    root = S.run_root(tmp_path, "finalize")
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

    root = S.run_root(tmp_path, "abort")
    run = S.open_run(root, limits=EvidenceLimits(max_manifest_bytes=open_len))
    (root / "evidence.json").write_text("{}\n", encoding="utf-8")
    run.record_artifact("evidence.json")
    before = (root / "manifest.json").read_bytes()
    with pytest.raises(EvidenceError) as error:
        run.abort(reason="caller-stop")
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes
    assert (root / "manifest.json").read_bytes() == before
