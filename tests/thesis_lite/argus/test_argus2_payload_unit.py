"""ARGUS2-SR-009-U: payload visibility, loss and interval/snapshot semantics (frozen unit cases)."""

from __future__ import annotations

import pytest

from xverse.argus import EvidenceError, EvidenceStore

try:
    from tests.thesis_lite.argus import support as S
except ImportError:  # pragma: no cover - copied tests-directory layout
    import sys as _argus2_sys
    from pathlib import Path as _argus2_path

    _argus2_sys.path.insert(0, str(_argus2_path(__file__).resolve().parent))
    import support as S


def _open(tmp_path, name="run", **kwargs):
    return S.open_run(S.run_root(tmp_path, name), **kwargs)


def _stored(tmp_path, index=0) -> dict:
    records = [item for item in EvidenceStore.read_run(S.run_root(tmp_path)).records() if item["eventKind"] == "observation"]
    return records[index]["observation"]


def _omitted(**overrides) -> dict:
    base = dict(
        payloadViewState="omitted",
        visibleBytesHex="",
        visibleByteCount=0,
        sourcePayloadSize=1024,
    )
    base.update(overrides)
    return S.observation_record(**base)


def test_metadata_only_omitted_carries_no_payload_bytes(tmp_path):
    run = _open(tmp_path)
    run.import_observation(S.projection([_omitted()]))
    run.finalize()
    stored = _stored(tmp_path)
    assert stored["visibleByteCount"] == 0
    assert stored["visibleBytesHex"] == ""
    assert stored["sourcePayloadSize"] == 1024


def test_redacted_carries_no_payload_bytes(tmp_path):
    run = _open(tmp_path)
    run.import_observation(
        S.projection([_omitted(payloadViewState="redacted")])
    )
    run.finalize()
    stored = _stored(tmp_path)
    assert stored["visibleByteCount"] == 0
    assert stored["visibleBytesHex"] == ""


def test_truncated_retains_explicit_bounded_prefix(tmp_path):
    run = _open(tmp_path)
    run.import_observation(
        S.projection(
            [S.observation_record(sourcePayloadSize=8, visibleBytesHex="00ff", visibleByteCount=2, payloadViewState="truncated")]
        )
    )
    run.finalize()
    stored = _stored(tmp_path)
    assert stored["payloadViewState"] == "truncated"
    assert stored["visibleByteCount"] == 2
    assert stored["sourcePayloadSize"] == 8


def test_complete_visibility_equals_source_payload_size(tmp_path):
    run = _open(tmp_path)
    run.import_observation(S.projection([S.observation_record()]))
    run.finalize()
    stored = _stored(tmp_path)
    assert stored["payloadViewState"] == "complete"
    assert stored["visibleByteCount"] == stored["sourcePayloadSize"]
    assert bytes.fromhex(stored["visibleBytesHex"]) == bytes.fromhex("00ff1020")


def test_visibility_states_remain_distinguishable_after_read(tmp_path):
    run = _open(tmp_path)
    run.import_observation(
        S.projection(
            [
                _omitted(),
                _omitted(payloadViewState="redacted"),
                S.observation_record(sourcePayloadSize=8, visibleBytesHex="00ff", visibleByteCount=2, payloadViewState="truncated"),
                S.observation_record(),
            ]
        )
    )
    run.finalize()
    records = [item for item in EvidenceStore.read_run(S.run_root(tmp_path)).records() if item["eventKind"] == "observation"]
    states = [(item["observation"]["payloadViewState"], item["observation"]["visibleByteCount"]) for item in records]
    assert states == [("omitted", 0), ("redacted", 0), ("truncated", 2), ("complete", 4)]


def test_snapshot_counters_backpressure_and_validity_preserved(tmp_path):
    snapshot = S.snapshot(queued=3, accepted=5, dropped=1, coalesced=2, backpressureRejections=4)
    run = _open(tmp_path)
    run.import_snapshot(snapshot)
    run.finalize()
    stored = [item["snapshot"] for item in EvidenceStore.read_run(S.run_root(tmp_path)).records() if item["eventKind"] == "snapshot"][0]
    for field in ("queued", "accepted", "dropped", "coalesced", "backpressureRejections"):
        assert stored[field] == snapshot[field]
    assert stored["validityEffect"] == snapshot["validityEffect"]
    assert stored["validityState"] == snapshot["validityState"]
    assert stored["intervalProvenance"] == snapshot["intervalProvenance"]


def test_closed_interval_without_bounds_rejected(tmp_path):
    snapshot = S.snapshot()
    snapshot["intervalProvenance"].pop("start")
    snapshot["intervalProvenance"].pop("end")
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.import_snapshot(snapshot)
    assert "ARGUS2-INPUT-INTERVAL-INCOMPLETE" in error.value.codes


def test_unclosed_interval_recorded_and_forces_incomplete(tmp_path):
    snapshot = S.snapshot()
    snapshot["intervalProvenance"]["closure"] = "unclosed"
    snapshot["intervalProvenance"].pop("start")
    snapshot["intervalProvenance"].pop("end")
    run = _open(tmp_path)
    run.import_snapshot(snapshot)
    manifest = run.finalize()
    assert manifest.evidence_status == "incomplete"
    assert "ARGUS2-REASON-UNCLOSED-INTERVAL" in manifest.evidence_reasons


def test_known_drop_remains_visible_after_stream_closure(tmp_path):
    run = _open(tmp_path)
    run.import_observation(
        S.projection([_omitted(counters={"queued": 1, "accepted": 1, "dropped": 1, "coalesced": 0})])
    )
    run.finalize()
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert "ARGUS2-LOSS-KNOWN-DROP" in {item.code for item in reader.diagnostics}
    assert "ARGUS2-REASON-KNOWN-LOSS" in reader.manifest["evidenceReasons"]
    assert reader.manifest["evidenceStatus"] == "incomplete"


def test_degraded_validity_interval_forces_incomplete(tmp_path):
    run = _open(tmp_path)
    run.import_snapshot(S.snapshot(validityState="degraded", experimentValidityDegraded=True))
    manifest = run.finalize()
    assert manifest.evidence_status == "incomplete"
    assert "ARGUS2-LOSS-DEGRADED-INTERVAL" in {item.code for item in manifest.diagnostics}


def test_invalid_validity_interval_forces_incomplete(tmp_path):
    run = _open(tmp_path)
    run.import_snapshot(S.snapshot(validityState="invalid", experimentValidityDegraded=True))
    manifest = run.finalize()
    assert manifest.evidence_status == "incomplete"
    assert "ARGUS2-LOSS-INVALID-INTERVAL" in {item.code for item in manifest.diagnostics}


def test_retention_counters_do_not_substitute_for_interval_closure(tmp_path):
    run = _open(
        tmp_path,
        obligations=[{"obligationId": "o1", "kind": "interval-closure", "required": True}],
    )
    run.import_observation(
        S.projection([_omitted(counters={"queued": 1, "accepted": 1, "dropped": 0, "coalesced": 0})])
    )
    manifest = run.finalize()
    assert "ARGUS2-REASON-UNMET-OBLIGATION" in manifest.evidence_reasons


def test_no_unobserved_payload_is_synthesized(tmp_path):
    run = _open(tmp_path)
    run.import_observation(S.projection([_omitted(payloadViewState="redacted", sourcePayloadSize=4096)]))
    run.finalize()
    stored = _stored(tmp_path)
    assert stored["visibleBytesHex"] == ""
    assert stored["visibleByteCount"] == 0
    assert stored["sourcePayloadSize"] == 4096
