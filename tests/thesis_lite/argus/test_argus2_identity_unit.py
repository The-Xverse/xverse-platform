"""ARGUS2-SR-003-U: event identity, producer sequence and causal references (frozen unit cases)."""

from __future__ import annotations

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


def _open(tmp_path, **kwargs):
    return S.open_run(S.run_root(tmp_path), **kwargs)


def _read_records(root) -> list[dict]:
    return EvidenceStore.read_run(root).records()


def _rewrite_first_line(root, mutate) -> None:
    stream = root / "events.jsonl"
    lines = stream.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[0])
    mutate(record)
    lines[0] = json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False)
    stream.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_valid_event_persists_all_declared_identity_fields(tmp_path):
    run = _open(tmp_path)
    run.append_event(
        event_id="e7",
        producer_id="p7",
        event_kind="annotation",
        producer_sequence=3,
        correlation_id="c7",
        causation_id="e6",
        annotation={"text": "n"},
    )
    run.finalize()
    record = _read_records(S.run_root(tmp_path))[0]
    assert record["schemaVersion"] == "1.0"
    assert record["runId"] == "run-a"
    assert record["eventId"] == "e7"
    assert record["producerId"] == "p7"
    assert record["ingestionOrdinal"] == 1
    assert record["eventKind"] == "annotation"
    assert record["producerSequence"] == 3
    assert record["correlationId"] == "c7"
    assert record["causationId"] == "e6"


def test_ingestion_ordinal_follows_append_order_not_clock_order(tmp_path):
    run = _open(tmp_path)
    for index, value in enumerate((300, 200, 100)):
        run.append_event(
            event_id=f"e{index}",
            producer_id="p1",
            event_kind="annotation",
            clocks={"source": {"domain": "d1", "unit": "ns", "value": value}},
        )
    run.finalize()
    records = _read_records(S.run_root(tmp_path))
    assert [item["ingestionOrdinal"] for item in records] == [1, 2, 3]
    assert [item["clocks"]["source"]["value"] for item in records] == [300, 200, 100]


def test_duplicate_event_identity_rejected_without_partial_record(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    before = (S.run_root(tmp_path) / "events.jsonl").read_bytes()
    with pytest.raises(EvidenceError) as error:
        run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    assert "ARGUS2-INPUT-DUPLICATE-EVENT" in error.value.codes
    assert run.writer_state == "open"
    assert (S.run_root(tmp_path) / "events.jsonl").read_bytes() == before


def test_missing_required_identity_field_rejected(tmp_path):
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.append_event(event_id="", producer_id="p1", event_kind="annotation")
    assert "ARGUS2-INPUT-IDENTITY-MISSING" in error.value.codes
    assert (S.run_root(tmp_path) / "events.jsonl").read_bytes() == b""


def test_unknown_event_schema_major_version_rejected(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    _rewrite_first_line(S.run_root(tmp_path), lambda record: record.update(schemaVersion="2.0"))
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert "ARGUS2-SCHEMA-MAJOR-UNSUPPORTED" in {item.code for item in reader.diagnostics}
    assert reader.records() == []


def test_causation_reference_indexed_without_invention(tmp_path):
    run = _open(
        tmp_path,
        obligations=[{"obligationId": "o1", "kind": "causal-closure", "required": True}],
    )
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.append_event(event_id="e2", producer_id="p1", event_kind="annotation", causation_id="e1")
    manifest = run.finalize()
    assert manifest.evidence_status == "complete"
    assert manifest.evidence_reasons == []


def test_unresolved_causation_remains_visible(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.append_event(event_id="e2", producer_id="p1", event_kind="annotation", causation_id="e9")
    manifest = run.finalize()
    assert "ARGUS2-REASON-UNRESOLVED-CAUSATION" in manifest.evidence_reasons
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert "ARGUS2-CAUSAL-UNRESOLVED" in {item.code for item in reader.diagnostics}


def test_unknown_event_kind_rejected(tmp_path):
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.append_event(event_id="e1", producer_id="p1", event_kind="telemetry")
    assert "ARGUS2-INPUT-FIELD-INVALID" in error.value.codes
    assert (S.run_root(tmp_path) / "events.jsonl").read_bytes() == b""


def test_caller_may_not_append_writer_emitted_kind(tmp_path):
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.append_event(event_id="e1", producer_id="p1", event_kind="run-opened")
    assert "ARGUS2-INPUT-FIELD-INVALID" in error.value.codes
    assert (S.run_root(tmp_path) / "events.jsonl").read_bytes() == b""


def test_annotation_text_bound_enforced(tmp_path):
    limits = EvidenceLimits(max_text_length=4)
    run = _open(tmp_path, limits=limits)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation", annotation={"text": "abcd"})
    with pytest.raises(EvidenceError) as error:
        run.append_event(event_id="e2", producer_id="p1", event_kind="annotation", annotation={"text": "abcde"})
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes
    lines = (S.run_root(tmp_path) / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_unknown_top_level_field_rejected(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    _rewrite_first_line(S.run_root(tmp_path), lambda record: record.update(extraField="x"))
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert "ARGUS2-SCHEMA-UNKNOWN-FIELD" in {item.code for item in reader.diagnostics}


def test_producer_sequence_is_not_used_for_ordering(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation", producer_sequence=5)
    run.append_event(event_id="e2", producer_id="p1", event_kind="annotation", producer_sequence=1)
    run.append_event(event_id="e3", producer_id="p1", event_kind="annotation", producer_sequence=3)
    run.finalize()
    records = _read_records(S.run_root(tmp_path))
    assert [(item["eventId"], item["producerSequence"]) for item in records] == [
        ("e1", 5),
        ("e2", 1),
        ("e3", 3),
    ]


def _raw_line(record: dict) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"


def _annotation_record(event_id: str, ordinal: int = 1, **extra) -> dict:
    record = {
        "schemaVersion": "1.0",
        "runId": "run-synthetic",
        "eventId": event_id,
        "producerId": "p1",
        "ingestionOrdinal": ordinal,
        "eventKind": "annotation",
    }
    record.update(extra)
    return record


def test_reader_rejects_event_missing_required_identity(tmp_path):
    record = {"schemaVersion": "1.0", "producerId": "p1", "ingestionOrdinal": 1, "eventKind": "annotation"}
    root = tmp_path / "run"
    S.synthetic_run(root, _raw_line(record))
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-INPUT-IDENTITY-MISSING" in {item.code for item in reader.diagnostics}
    assert reader.records() == []
    assert reader.assessed_evidence_status == "incomplete"


def test_reader_rejects_duplicate_event_id_within_run(tmp_path):
    line = S.annotation_event_bytes("dup")
    root = tmp_path / "run"
    S.synthetic_run(root, line + line)
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-CORRUPT-DUPLICATE-EVENT" in {item.code for item in reader.diagnostics}
    assert [item["eventId"] for item in reader.records()] == ["dup"]
    assert reader.assessed_evidence_status == "incomplete"


def test_reader_rejects_nonmonotonic_ingestion_ordinal(tmp_path):
    repeated = _raw_line(_annotation_record("e1", 1)) + _raw_line(_annotation_record("e2", 1))
    root = tmp_path / "repeat"
    S.synthetic_run(root, repeated)
    assert "ARGUS2-CORRUPT-ORDINAL" in {item.code for item in EvidenceStore.read_run(root).diagnostics}

    gapped = _raw_line(_annotation_record("e1", 1)) + _raw_line(_annotation_record("e2", 3))
    root = tmp_path / "gap"
    S.synthetic_run(root, gapped)
    assert "ARGUS2-CORRUPT-ORDINAL" in {item.code for item in EvidenceStore.read_run(root).diagnostics}

    not_one = _raw_line(_annotation_record("e1", 2))
    root = tmp_path / "not-one"
    S.synthetic_run(root, not_one)
    assert "ARGUS2-CORRUPT-ORDINAL" in {item.code for item in EvidenceStore.read_run(root).diagnostics}


def test_reader_rejects_event_runid_mismatch_with_manifest(tmp_path):
    line = S.annotation_event_bytes("e1").replace(b'"run-synthetic"', b'"other-run"')
    root = tmp_path / "run"
    S.synthetic_run(root, line)
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-CORRUPT-RUN-ID-MISMATCH" in {item.code for item in reader.diagnostics}
    assert reader.records() == []


def test_reader_rejects_nonfinite_clock_value_on_read(tmp_path):
    line = (
        b'{"schemaVersion":"1.0","runId":"run-synthetic","eventId":"e1","producerId":"p1",'
        b'"ingestionOrdinal":1,"eventKind":"annotation","clocks":{"source":{"domain":"d","unit":"ns","value":NaN}}}\n'
    )
    root = tmp_path / "nan"
    S.synthetic_run(root, line)
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-INPUT-NONFINITE" in {item.code for item in reader.diagnostics}
    assert reader.records() == []

    line = (
        b'{"schemaVersion":"1.0","runId":"run-synthetic","eventId":"e1","producerId":"p1",'
        b'"ingestionOrdinal":1,"eventKind":"annotation","clocks":{"source":{"domain":"d","unit":"ns","value":"x"}}}\n'
    )
    root = tmp_path / "nonnumeric"
    S.synthetic_run(root, line)
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-INPUT-NONFINITE" in {item.code for item in reader.diagnostics}
    assert reader.records() == []
