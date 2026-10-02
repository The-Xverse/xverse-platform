"""ARGUS2-SR-005-U: stable diagnostic categories and no-diagnostic-without-violation cases."""

from __future__ import annotations

import json
import os

import pytest

from xverse.argus import EvidenceError, EvidenceStore

try:
    from tests.thesis_lite.argus import support as S
except ImportError:  # pragma: no cover - copied tests-directory layout
    import sys as _argus2_sys
    from pathlib import Path as _argus2_path

    _argus2_sys.path.insert(0, str(_argus2_path(__file__).resolve().parent))
    import support as S

_REQUIRED_CATEGORY_PREFIX = {
    "input-rejection": "ARGUS2-INPUT-",
    "io-failure": "ARGUS2-IO-",
    "unsupported-schema": "ARGUS2-SCHEMA-",
    "corrupt-artifact": "ARGUS2-CORRUPT-",
    "missing-evidence": "ARGUS2-MISSING-",
    "known-observation-loss": "ARGUS2-LOSS-",
}


def test_diagnostic_categories_are_distinguishable(tmp_path, monkeypatch):
    collected: dict[str, tuple[str, str]] = {}

    run = S.open_run(S.run_root(tmp_path, "input"))
    with pytest.raises(EvidenceError) as error:
        run.append_event(event_id="e1", producer_id="p1", event_kind="telemetry")
    item = error.value.diagnostics[0]
    collected[item.category] = (item.code, "input")

    run = S.open_run(S.run_root(tmp_path, "io"))
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")

    def boom(*args, **kwargs):
        raise OSError("simulated atomic replace failure")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(EvidenceError) as error:
        run.finalize()
    item = error.value.diagnostics[0]
    collected[item.category] = (item.code, "io")
    monkeypatch.undo()

    run = S.open_run(S.run_root(tmp_path, "schema"))
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    manifest_path = S.run_root(tmp_path, "schema") / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schemaVersion"] = "2.0"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    reader = EvidenceStore.read_run(S.run_root(tmp_path, "schema"))
    item = reader.diagnostics[0]
    collected[item.category] = (item.code, "schema")

    run = S.open_run(S.run_root(tmp_path, "corrupt"))
    root = S.run_root(tmp_path, "corrupt")
    (root / "artifact.json").write_text('{"v":1}\n', encoding="utf-8")
    run.record_artifact("artifact.json")
    run.finalize()
    (root / "artifact.json").write_text('{"v":2}\n', encoding="utf-8")
    reader = EvidenceStore.read_run(root)
    item = next(item for item in reader.diagnostics if item.code == "ARGUS2-CORRUPT-ARTIFACT-HASH")
    collected[item.category] = (item.code, "corrupt")

    run = S.open_run(S.run_root(tmp_path, "missing"))
    root = S.run_root(tmp_path, "missing")
    (root / "artifact.json").write_text('{"v":1}\n', encoding="utf-8")
    run.record_artifact("artifact.json")
    (root / "artifact.json").unlink()
    manifest = run.finalize()
    item = next(item for item in manifest.diagnostics if item.code == "ARGUS2-MISSING-ARTIFACT")
    collected[item.category] = (item.code, "missing")

    run = S.open_run(S.run_root(tmp_path, "loss"))
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
    item = next(item for item in manifest.diagnostics if item.code == "ARGUS2-LOSS-KNOWN-DROP")
    collected[item.category] = (item.code, "loss")

    for category, prefix in _REQUIRED_CATEGORY_PREFIX.items():
        assert category in collected, category
        code, _ = collected[category]
        assert code.startswith(prefix), (category, code)
    codes = [code for code, _ in collected.values()]
    assert len(codes) == len(set(codes))


def test_no_diagnostic_without_actual_violation(tmp_path):
    run = S.open_run(
        S.run_root(tmp_path),
        limits=None,
        obligations=[{"obligationId": "o1", "kind": "no-known-loss", "required": True}],
    )
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation", annotation={"text": "n"})
    manifest = run.finalize()
    assert manifest.diagnostics == ()
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert reader.diagnostics == ()
    assert manifest.evidence_status == "complete"


def test_truncated_json_and_unknown_nested_key_yield_stable_bounded_diagnostics(tmp_path):
    truncated = tmp_path / "truncated"
    S.synthetic_run(truncated, b'{"broken":\n')
    reader = EvidenceStore.read_run(truncated)
    assert "ARGUS2-CORRUPT-STREAM-TRUNCATED" in {item.code for item in reader.diagnostics}
    assert reader.assessed_evidence_status == "incomplete"

    record = {
        "schemaVersion": "1.0",
        "runId": "run-synthetic",
        "eventId": "e1",
        "producerId": "p1",
        "ingestionOrdinal": 1,
        "eventKind": "annotation",
        "annotation": {"text": "n", "bogus": 1},
    }
    line = json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
    unknown = tmp_path / "unknown"
    S.synthetic_run(unknown, line)
    reader = EvidenceStore.read_run(unknown)
    assert "ARGUS2-SCHEMA-UNKNOWN-FIELD" in {item.code for item in reader.diagnostics}
    assert S.cli("verify", str(unknown)).returncode == 1


def test_no_uncaught_typeerror_or_valueerror_from_malformed_input(tmp_path):
    malformed_streams = [
        b"[1,2,3]\n",
        b"42\n",
        b'"text"\n',
        b"\n",
        b'{"schemaVersion":"1.0","runId":"run-synthetic","eventId":"e1","producerId":"p1",'
        b'"ingestionOrdinal":1,"eventKind":"annotation","clocks":5}\n',
        b'{"schemaVersion":"1.0","runId":"run-synthetic","eventId":"e1","producerId":"p1",'
        b'"ingestionOrdinal":1,"eventKind":"observation","clocks":{"source":{"domain":"d","unit":"ns","value":1}},'
        b'"observation":[]}\n',
        b'{"schemaVersion":"two","runId":"run-synthetic","eventId":"e1","producerId":"p1",'
        b'"ingestionOrdinal":1,"eventKind":"annotation"}\n',
    ]
    for index, records in enumerate(malformed_streams):
        root = tmp_path / f"run{index}"
        S.synthetic_run(root, records)
        reader = EvidenceStore.read_run(root)
        assert reader.assessed_evidence_status == "incomplete"
        assert reader.diagnostics
        assert S.cli("verify", str(root)).returncode == 1

    root = tmp_path / "manifest-shape"
    S.synthetic_run(root, S.annotation_event_bytes("e1"))
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["artifacts"] = 5
    (root / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-CORRUPT-MANIFEST-SHAPE" in {item.code for item in reader.diagnostics}
    assert reader.assessed_evidence_status == "incomplete"
    assert S.cli("verify", str(root)).returncode == 1
