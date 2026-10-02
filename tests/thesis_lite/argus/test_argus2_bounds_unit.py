"""ARGUS2-SR-005-U: caller-configured finite bounds and stable diagnostics (frozen unit cases)."""

from __future__ import annotations

import pytest

from xverse.argus import EvidenceError, EvidenceLimits, EvidenceStore

try:
    from tests.thesis_lite.argus import support as S
except ImportError:  # pragma: no cover - copied tests-directory layout
    import sys as _argus2_sys
    from pathlib import Path as _argus2_path

    _argus2_sys.path.insert(0, str(_argus2_path(__file__).resolve().parent))
    import support as S


def _annotation(event_id: str = "e1", text: str = "n") -> dict:
    return {"event_id": event_id, "producer_id": "p1", "event_kind": "annotation", "annotation": {"text": text}}


def test_evidence_limits_requires_positive_integers():
    with pytest.raises(ValueError):
        EvidenceLimits(max_event_bytes=0)
    with pytest.raises(ValueError):
        EvidenceLimits(max_events=-1)


def test_max_event_bytes_at_bound_accepted_and_over_rejected(tmp_path):
    probe = S.open_run(S.run_root(tmp_path, "probe"))
    probe.append_event(**_annotation())
    line = (S.run_root(tmp_path, "probe") / "events.jsonl").read_bytes().rstrip(b"\n")
    length = len(line)
    at_bound = S.open_run(S.run_root(tmp_path, "at"), limits=EvidenceLimits(max_event_bytes=length))
    at_bound.append_event(**_annotation())
    with pytest.raises(EvidenceError) as error:
        over = S.open_run(S.run_root(tmp_path, "over"), limits=EvidenceLimits(max_event_bytes=length - 1))
        over.append_event(**_annotation())
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes
    assert "max_event_bytes" in error.value.diagnostics[0].message


def test_max_events_at_bound_accepted_and_over_rejected(tmp_path):
    run = S.open_run(S.run_root(tmp_path), limits=EvidenceLimits(max_events=2))
    run.append_event(**_annotation("e1"))
    run.append_event(**_annotation("e2"))
    with pytest.raises(EvidenceError) as error:
        run.append_event(**_annotation("e3"))
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes


def test_max_id_length_at_bound_accepted_and_over_rejected(tmp_path):
    limits = EvidenceLimits(max_id_length=4)
    run = S.open_run(S.run_root(tmp_path), run_id="r", limits=limits)
    run.append_event(event_id="abcd", producer_id="p", event_kind="annotation")
    with pytest.raises(EvidenceError) as error:
        run.append_event(event_id="abcde", producer_id="p", event_kind="annotation")
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes
    assert "max_id_length" in error.value.diagnostics[0].message


def test_max_text_length_at_bound_accepted_and_over_rejected(tmp_path):
    run = S.open_run(S.run_root(tmp_path), limits=EvidenceLimits(max_text_length=4))
    run.append_event(**_annotation("e1", "abcd"))
    with pytest.raises(EvidenceError) as error:
        run.append_event(**_annotation("e2", "abcde"))
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes


def test_max_payload_bytes_at_bound_accepted_and_over_rejected(tmp_path):
    run = S.open_run(S.run_root(tmp_path), limits=EvidenceLimits(max_payload_bytes=4))
    run.import_observation(S.projection([S.observation_record()]))
    with pytest.raises(EvidenceError) as error:
        run.import_observation(
            S.projection(
                [
                    S.observation_record(
                        sourcePayloadSize=8,
                        visibleBytesHex="00ff102030405060",
                        visibleByteCount=8,
                    )
                ]
            )
        )
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes
    assert "max_payload_bytes" in error.value.diagnostics[0].message


def test_max_artifacts_at_bound_accepted_and_over_rejected(tmp_path):
    run = S.open_run(S.run_root(tmp_path), limits=EvidenceLimits(max_artifacts=1))
    root = S.run_root(tmp_path)
    (root / "a.json").write_text("{}\n", encoding="utf-8")
    (root / "b.json").write_text("{}\n", encoding="utf-8")
    run.record_artifact("a.json")
    with pytest.raises(EvidenceError) as error:
        run.record_artifact("b.json")
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes


def test_max_obligations_at_bound_accepted_and_over_rejected(tmp_path):
    obligation = {"obligationId": "o1", "kind": "no-known-loss", "required": True}
    S.open_run(S.run_root(tmp_path, "at"), limits=EvidenceLimits(max_obligations=1), obligations=[obligation])
    with pytest.raises(EvidenceError) as error:
        S.open_run(
            S.run_root(tmp_path, "over"),
            limits=EvidenceLimits(max_obligations=1),
            obligations=[obligation, {"obligationId": "o2", "kind": "no-known-loss", "required": True}],
        )
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes


def test_max_diagnostic_count_bounds_returned_diagnostics(tmp_path):
    obligations = [
        {"obligationId": f"o{index}", "kind": "best-effort", "required": True} for index in range(5)
    ]
    with pytest.raises(EvidenceError) as error:
        S.open_run(
            S.run_root(tmp_path),
            limits=EvidenceLimits(max_diagnostic_count=2),
            obligations=obligations,
        )
    assert len(error.value.diagnostics) <= 2


def test_max_manifest_bytes_at_bound_accepted_and_over_rejected(tmp_path):
    boundary = None
    for limit in range(1, 4000):
        try:
            S.open_run(S.run_root(tmp_path, f"scan-{limit}"), limits=EvidenceLimits(max_manifest_bytes=limit))
        except EvidenceError:
            continue
        boundary = limit
        break
    assert boundary is not None
    with pytest.raises(EvidenceError) as error:
        S.open_run(
            S.run_root(tmp_path, "over"),
            limits=EvidenceLimits(max_manifest_bytes=boundary - 1),
        )
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes
    assert "max_manifest_bytes" in error.value.diagnostics[0].message


def test_max_causal_index_entries_at_bound_accepted_and_over_rejected(tmp_path):
    run = S.open_run(S.run_root(tmp_path), limits=EvidenceLimits(max_causal_index_entries=2))
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation", causation_id="x1")
    run.append_event(event_id="e2", producer_id="p1", event_kind="annotation", causation_id="x2")
    with pytest.raises(EvidenceError) as error:
        run.append_event(event_id="e3", producer_id="p1", event_kind="annotation", causation_id="x3")
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes
    assert "max_causal_index_entries" in error.value.diagnostics[0].message


def test_max_read_records_bounds_reader_result(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    for index in range(3):
        run.append_event(event_id=f"e{index}", producer_id="p1", event_kind="annotation")
    run.finalize()
    reader = EvidenceStore.read_run(S.run_root(tmp_path), limits=EvidenceLimits(max_read_records=2))
    assert len(reader.records()) <= 2
    assert "ARGUS2-BOUND-EXCEEDED" in {item.code for item in reader.diagnostics}


def test_each_exceeded_bound_produces_exactly_one_diagnostic(tmp_path):
    run = S.open_run(S.run_root(tmp_path), limits=EvidenceLimits(max_event_bytes=32))
    with pytest.raises(EvidenceError) as error:
        run.append_event(**_annotation())
    assert len(error.value.diagnostics) == 1
    assert error.value.diagnostics[0].code == "ARGUS2-BOUND-EXCEEDED"


def test_nonfinite_value_rejected_not_truncated(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    with pytest.raises(EvidenceError) as error:
        run.append_event(
            event_id="e1",
            producer_id="p1",
            event_kind="annotation",
            clocks={"source": {"domain": "d1", "unit": "ns", "value": float("inf")}},
        )
    assert "ARGUS2-INPUT-NONFINITE" in error.value.codes
    assert (S.run_root(tmp_path) / "events.jsonl").read_bytes() == b""


def test_max_diagnostic_count_caps_damaged_input_diagnostics(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    root = S.run_root(tmp_path)
    (root / "events.jsonl").write_bytes(b"not json\n" * 50)
    reader = EvidenceStore.read_run(root, limits=EvidenceLimits(max_diagnostic_count=3))
    assert len(reader.diagnostics) <= 3
    assert "ARGUS2-BOUND-EXCEEDED" in {item.code for item in reader.diagnostics}
    assert reader.assessed_evidence_status == "incomplete"
