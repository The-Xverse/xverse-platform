"""ARGUS2 terminal-review repair continuation: additive adversarial unit cases.

These cases strengthen the frozen ``AR-F01``–``AR-F05`` repair without weakening any inherited
assertion. They exercise hostile evidence that the pre-continuation draft could still crash or
silently misreport: malformed manifest/event containers that previously raised an uncaught
``TypeError``, unbounded recovery diagnostic emission, and non-finite/non-JSON admitted caller
content that previously escaped as a raw ``ValueError``/``TypeError`` during serialization.
"""

from __future__ import annotations

import hashlib
import json
import os

import pytest

from xverse.argus import EvidenceError, EvidenceLimits, EvidenceStore
from xverse.argus.recovery import recover_stream

try:
    from tests.thesis_lite.argus import support as S
except ImportError:  # pragma: no cover - copied tests-directory layout
    import sys as _argus2_sys
    from pathlib import Path as _argus2_path

    _argus2_sys.path.insert(0, str(_argus2_path(__file__).resolve().parent))
    import support as S


# AR-F01: bounded diagnostic emission -------------------------------------------------


def test_recovery_diagnostic_emission_stops_at_caller_bound(tmp_path):
    root = tmp_path / "recover"
    root.mkdir()
    # Fifty independently damaged lines would once have appended fifty diagnostics in memory.
    (root / "events.jsonl").write_bytes(b"not json\n" * 50)
    result = recover_stream(root, limits=EvidenceLimits(max_diagnostic_count=3))
    assert len(result.diagnostics) <= 3
    assert any(item.code == "ARGUS2-BOUND-EXCEEDED" for item in result.diagnostics)
    assert all(item.code != "" for item in result.diagnostics)
    # The bounded read is still non-mutating.
    assert (root / "events.jsonl").read_bytes() == b"not json\n" * 50


def test_reader_damaged_stream_never_returns_more_diagnostics_than_bound(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    root = S.run_root(tmp_path)
    (root / "events.jsonl").write_bytes(b"{}\n" * 40)
    reader = EvidenceStore.read_run(root, limits=EvidenceLimits(max_diagnostic_count=4))
    assert len(reader.diagnostics) <= 4
    assert reader.assessed_evidence_status == "incomplete"


# AR-F03: malformed containers never raise ---------------------------------------------


def test_reader_malformed_clock_domains_container_yields_stable_diagnostic(tmp_path):
    root = S.synthetic_run(tmp_path / "clock-domains", S.annotation_event_bytes("e1"), clockDomains=7)
    reader = EvidenceStore.read_run(root)  # must not raise
    assert "ARGUS2-CORRUPT-MANIFEST-SHAPE" in {item.code for item in reader.diagnostics}
    assert reader.assessed_evidence_status == "incomplete"
    assert reader.recorded_evidence_status == "complete"


def test_reader_malformed_metric_inputs_never_raise_on_export_or_cli(tmp_path):
    root = S.synthetic_run(
        tmp_path / "metric-inputs",
        S.annotation_event_bytes("e1"),
        metricInputs=[
            {"metricId": "m1", "observerIds": 5, "timeDomainIds": 5, "evidenceSinkRefs": 5}
        ],
    )
    reader = EvidenceStore.read_run(root)  # must not raise
    exported = reader.export_json()  # must not raise
    assert '"metricId":"m1"' in exported
    inputs = reader.metric_inputs()
    assert inputs[0]["observerIds"] == []
    assert inputs[0]["timeDomainIds"] == []
    assert inputs[0]["selectionStatus"] == "incomplete"
    completed = S.cli("export", str(root), "--format", "json")
    assert completed.returncode == 0
    assert "Traceback" not in completed.stderr


def test_reader_malformed_event_containers_never_raise(tmp_path):
    payloads = {
        "observation-list": b'{"schemaVersion":"1.0","runId":"run-synthetic","eventId":"e1","producerId":"p1","ingestionOrdinal":1,"eventKind":"observation","observation":[]}\n',
        "snapshot-int": b'{"schemaVersion":"1.0","runId":"run-synthetic","eventId":"e1","producerId":"p1","ingestionOrdinal":1,"eventKind":"snapshot","snapshot":5}\n',
        "identity-list": b'{"schemaVersion":"1.0","runId":"run-synthetic","eventId":"e1","producerId":[],"ingestionOrdinal":1,"eventKind":"annotation"}\n',
        "ordinal-list": b'{"schemaVersion":"1.0","runId":"run-synthetic","eventId":"e1","producerId":"p1","ingestionOrdinal":[],"eventKind":"annotation"}\n',
    }
    for name, payload in payloads.items():
        root = S.synthetic_run(tmp_path / name, payload)
        reader = EvidenceStore.read_run(root)  # must not raise
        assert reader.assessed_evidence_status == "incomplete", name
        assert reader.diagnostics, name


# AR-F05: admitted caller content snapshot / rejection ---------------------------------


def test_append_nonfinite_or_nonjson_extensions_rejected_at_admission(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    stream = S.run_root(tmp_path) / "events.jsonl"
    before = stream.read_bytes()
    with pytest.raises(EvidenceError) as error:
        run.append_event(
            event_id="e1",
            producer_id="p1",
            event_kind="annotation",
            extensions={"ns": float("nan")},
        )
    assert "ARGUS2-INPUT-FIELD-INVALID" in error.value.codes
    with pytest.raises(EvidenceError) as error:
        run.append_event(
            event_id="e2",
            producer_id="p1",
            event_kind="annotation",
            extensions={"ns": {1, 2}},
        )
    assert "ARGUS2-INPUT-FIELD-INVALID" in error.value.codes
    assert stream.read_bytes() == before


def test_admitted_annotation_is_an_independent_snapshot(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    annotation = {"text": "original"}
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation", annotation=annotation)
    annotation["text"] = "mutated"
    run.finalize()
    records = EvidenceStore.read_run(S.run_root(tmp_path)).records()
    assert records[0]["annotation"] == {"text": "original"}


def test_append_nonfinite_clocks_rejected_without_writing(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    stream = S.run_root(tmp_path) / "events.jsonl"
    before = stream.read_bytes()
    with pytest.raises(EvidenceError) as error:
        run.append_event(
            event_id="e1",
            producer_id="p1",
            event_kind="annotation",
            clocks={"source": {"domain": "d", "unit": "ns", "value": float("nan")}},
        )
    assert "ARGUS2-INPUT-NONFINITE" in error.value.codes
    assert stream.read_bytes() == before


# AR-F03: non-finite manifest input rejected before assessment or export ---------------


def test_reader_rejects_nonfinite_manifest_values_before_assessment_or_export(tmp_path):
    positions = {
        "limits": {"limits": {"max_events": float("nan")}},
        "clock-domains": {"clockDomains": [float("inf")]},
        "obligation-detail": {
            "obligations": [
                {
                    "obligationId": "o1",
                    "kind": "min-observations",
                    "required": True,
                    "detail": {"minimum": float("inf")},
                }
            ]
        },
        "evidence-reasons": {"evidenceReasons": [float("nan")]},
        "artifacts": {
            "artifacts": [
                {
                    "path": "a.json",
                    "mediaType": "application/json",
                    "schemaVersion": "1.0",
                    "bytes": float("nan"),
                    "sha256": "00" * 32,
                    "role": "evidence",
                }
            ]
        },
        "run-id": {"runId": float("-inf")},
    }
    for name, overrides in positions.items():
        root = S.synthetic_run(tmp_path / name, S.annotation_event_bytes("e1"), **overrides)
        reader = EvidenceStore.read_run(root)  # must not raise
        assert "ARGUS2-INPUT-NONFINITE" in {item.code for item in reader.diagnostics}, name
        assert reader.assessed_evidence_status == "incomplete", name
        # Recorded manifest facts stay separate from the assessed conclusion.
        assert reader.recorded_evidence_status == "complete", name
        document = json.loads(reader.export_json())  # must not raise on a non-finite manifest
        assert document["evidenceStatus"] == "incomplete", name
        assert document["assessedEvidenceStatus"] == "incomplete", name
        assert document["recordedEvidenceStatus"] == "complete", name
        assert reader.records() == [], name
        verified = S.cli("verify", str(root))
        assert verified.returncode == 1, (name, verified.stdout, verified.stderr)
        exported = S.cli("export", str(root))
        assert exported.returncode == 0, (name, exported.stderr)
        assert json.loads(exported.stdout)["evidenceStatus"] == "incomplete", name


def test_reader_rejects_nonfinite_manifest_tokens_from_raw_text(tmp_path):
    # ``json.loads`` accepts NaN/Infinity/-Infinity tokens and an overflowing literal such as 1e400
    # parses to inf; each must be rejected before assessment or export.
    for name, needle, replacement in (
        ("overflow", '"eventCount":1', '"eventCount":1e400'),
        ("negative-infinity", '"eventCount":1', '"eventCount":-Infinity'),
        ("nan-token", '"eventCount":1', '"eventCount":NaN'),
    ):
        root = S.synthetic_run(tmp_path / name, S.annotation_event_bytes("e1"))
        path = root / "manifest.json"
        text = path.read_text(encoding="utf-8")
        assert needle in text, name
        path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")
        reader = EvidenceStore.read_run(root)  # must not raise
        assert "ARGUS2-INPUT-NONFINITE" in {item.code for item in reader.diagnostics}, name
        assert reader.assessed_evidence_status == "incomplete", name
        assert json.loads(reader.export_json())["evidenceStatus"] == "incomplete", name


# AR-F04: the publication bound covers the exact serialized bytes incl. final newline ---


def test_manifest_publication_bound_includes_the_final_newline(tmp_path):
    S.open_run(S.run_root(tmp_path, "probe"), limits=EvidenceLimits(max_manifest_bytes=100_000))
    base_size = (S.run_root(tmp_path, "probe") / "manifest.json").stat().st_size

    # Find the fixed point where the caller bound equals the exact bytes written. The bound must be
    # measured on canonical bytes *plus* the single trailing newline, so that exact value is accepted.
    exact = None
    for limit in range(base_size - 8, base_size + 8):
        candidate = S.run_root(tmp_path, f"scan-{limit}")
        try:
            run = S.open_run(candidate, limits=EvidenceLimits(max_manifest_bytes=limit))
        except EvidenceError:
            continue
        size = (candidate / "manifest.json").stat().st_size
        if size == limit:
            exact = limit
            assert run.writer_state == "open"
            break
    assert exact is not None
    assert exact == (S.run_root(tmp_path, f"scan-{exact}") / "manifest.json").stat().st_size

    # One byte below the exact serialized size is refused before any run root is created.
    over_root = S.run_root(tmp_path, "over")
    with pytest.raises(EvidenceError) as error:
        S.open_run(over_root, limits=EvidenceLimits(max_manifest_bytes=exact - 1))
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes
    assert "max_manifest_bytes" in error.value.diagnostics[0].message
    assert not over_root.exists()


# AR-RVW-001: deeply nested JSON returns stable bounded diagnostics, never RecursionError -------


def _nested_lists(depth: int) -> list:
    value: list = []
    for _ in range(depth):
        value = [value]
    return value


def _deep_json(depth: int) -> str:
    return "[" * depth + "]" * depth


def test_canonical_serialization_rejects_deep_nesting_with_value_error_not_recursion_error():
    from xverse.argus.schema import canonical_json, json_depth_exceeded

    deep = _nested_lists(5000)
    assert json_depth_exceeded(deep) is True
    with pytest.raises(ValueError) as error:
        canonical_json(deep)
    assert not isinstance(error.value, RecursionError)
    # A shallow value is untouched.
    assert canonical_json({"a": [1, 2, 3]}) == '{"a":[1,2,3]}'


def test_json_nesting_scanner_ignores_brackets_inside_strings():
    from xverse.argus.schema import json_text_depth_exceeded, parse_json_bounded

    payload = json.dumps({"note": "[" * 500 + "]" * 500}, sort_keys=True, separators=(",", ":"))
    assert json_text_depth_exceeded(payload) is False
    assert parse_json_bounded(payload) == {"note": "[" * 500 + "]" * 500}


def test_reader_rejects_deeply_nested_manifest_without_recursion_error(tmp_path):
    root = S.synthetic_run(tmp_path / "deep-manifest", S.annotation_event_bytes("e1"))
    path = root / "manifest.json"
    text = path.read_text(encoding="utf-8")
    assert '"plan":{' in text
    path.write_text(text.replace('"plan":{', '"plan":{"deep":' + _deep_json(5000) + ",", 1), encoding="utf-8")
    reader = EvidenceStore.read_run(root)  # must not raise
    assert "ARGUS2-CORRUPT-MANIFEST-SHAPE" in {item.code for item in reader.diagnostics}
    assert reader.assessed_evidence_status == "incomplete"
    assert reader.records() == []
    exported = S.cli("export", str(root))
    assert exported.returncode == 0
    assert json.loads(exported.stdout)["evidenceStatus"] == "incomplete"


def test_reader_rejects_deeply_nested_event_line_without_recursion_error(tmp_path):
    root = S.synthetic_run(tmp_path / "deep-event", (_deep_json(5000) + "\n").encode())
    reader = EvidenceStore.read_run(root)  # must not raise
    assert "ARGUS2-CORRUPT-STREAM-TRUNCATED" in {item.code for item in reader.diagnostics}
    assert reader.assessed_evidence_status == "incomplete"
    assert reader.records() == []


def test_open_run_rejects_deeply_nested_obligation_without_recursion_error(tmp_path):
    root = S.run_root(tmp_path, "deep-obligation")
    obligation = {
        "obligationId": "o1",
        "kind": "min-observations",
        "required": True,
        "detail": {"minimum": 1, "nested": _nested_lists(5000)},
    }
    with pytest.raises(EvidenceError) as error:
        S.open_run(root, obligations=[obligation])
    assert "ARGUS2-INPUT-FIELD-INVALID" in error.value.codes
    assert not root.exists()


def test_append_event_rejects_deeply_nested_extensions_without_recursion_error(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    stream = S.run_root(tmp_path) / "events.jsonl"
    before = stream.read_bytes()
    with pytest.raises(EvidenceError) as error:
        run.append_event(
            event_id="e1",
            producer_id="p1",
            event_kind="annotation",
            extensions={"ns": _nested_lists(5000)},
        )
    assert "ARGUS2-INPUT-FIELD-INVALID" in error.value.codes
    assert stream.read_bytes() == before


def test_append_event_rejects_deeply_nested_observation_without_recursion_error(tmp_path):
    run = S.open_run(S.run_root(tmp_path))
    record = S.observation_record()
    record["extensions"] = {"ns": _nested_lists(5000)}
    with pytest.raises(EvidenceError) as error:
        run.append_event(
            event_id="e1",
            producer_id="p1",
            event_kind="observation",
            clocks={
                "source": {"domain": "clock.source", "unit": "ns", "value": 1},
                "observation": {"domain": "clock.observation", "unit": "ns", "value": 2},
            },
            observation=record,
        )
    assert "ARGUS2-INPUT-FIELD-INVALID" in error.value.codes


# AR-F03 enclosing depth: last accepted / first rejected depths at each wrapping boundary --------


def _nested_event_line(depth: int) -> bytes:
    """Return one canonical annotation event whose ``extensions`` nests ``depth`` lists deep."""

    record = {
        "schemaVersion": "1.0",
        "runId": "run-synthetic",
        "eventId": "e1",
        "producerId": "p1",
        "ingestionOrdinal": 1,
        "eventKind": "annotation",
        "extensions": {"ns": _nested_lists(depth)},
    }
    return json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def _event_export_boundary(tmp_path):
    """Return the (last accepted, first rejected) JSON-export depths for an admitted event."""

    from xverse.argus.schema import MAX_JSON_NESTING

    accepted = None
    for depth in range(MAX_JSON_NESTING - 24, MAX_JSON_NESTING):
        root = S.synthetic_run(tmp_path / f"export-{depth}", _nested_event_line(depth))
        reader = EvidenceStore.read_run(root)
        document = json.loads(reader.export_json())  # must never raise
        codes = {item["code"] for item in document["diagnostics"]}
        if "ARGUS2-BOUND-EXCEEDED" in codes:
            return accepted, depth, reader, root, document
        assert "ARGUS2-CORRUPT-STREAM-TRUNCATED" not in codes, depth
        accepted = depth
    raise AssertionError("no enclosing-depth export rejection was found")


def test_event_json_export_last_accepted_and_first_rejected_depths(tmp_path):
    accepted, rejected, reader, _root, document = _event_export_boundary(tmp_path)

    # The previous depth is fully representable: the record is exported and the primary status is
    # complete. The next depth is admitted by the parse bound but cannot be wrapped, so it must be
    # withheld with one stable bounded diagnostic and never presented as complete.
    assert accepted is not None
    assert rejected == accepted + 1
    assert document["records"] == []
    assert document["evidenceStatus"] == "incomplete"
    assert document["assessedEvidenceStatus"] == "incomplete"
    assert "ARGUS2-BOUND-EXCEEDED" in {item["code"] for item in document["diagnostics"]}

    # The admitted record stays in the trusted result; only the wrapped export withholds it.
    assert len(reader.records()) == 1
    assert reader.assessed_evidence_status == "incomplete"

    accepted_root = S.synthetic_run(tmp_path / "accepted", _nested_event_line(accepted))
    accepted_document = json.loads(EvidenceStore.read_run(accepted_root).export_json())
    assert len(accepted_document["records"]) == 1
    assert accepted_document["evidenceStatus"] == "complete"
    assert accepted_document["diagnostics"] == []


def test_cli_export_first_rejected_event_depth_is_bounded(tmp_path):
    accepted, rejected, _reader, root, _document = _event_export_boundary(tmp_path)

    rejected_export = S.cli("export", str(root), "--format", "json")
    assert rejected_export.returncode == 0
    assert "Traceback" not in rejected_export.stderr
    rejected_document = json.loads(rejected_export.stdout)
    assert rejected_document["evidenceStatus"] == "incomplete"
    assert "ARGUS2-BOUND-EXCEEDED" in {item["code"] for item in rejected_document["diagnostics"]}

    accepted_root = S.synthetic_run(tmp_path / "accepted-cli", _nested_event_line(accepted))
    accepted_export = S.cli("export", str(accepted_root), "--format", "json")
    assert accepted_export.returncode == 0
    accepted_document = json.loads(accepted_export.stdout)
    assert len(accepted_document["records"]) == 1
    assert accepted_document["evidenceStatus"] == "complete"
    assert rejected == accepted + 1


def test_obligation_admission_last_accepted_and_first_rejected_depths(tmp_path):
    from xverse.argus.schema import MAX_JSON_NESTING

    def obligation(depth: int) -> dict:
        return {
            "obligationId": "o1",
            "kind": "min-observations",
            "required": True,
            "detail": {"minimum": 1, "nested": _nested_lists(depth)},
        }

    accepted = None
    rejected = None
    for depth in range(MAX_JSON_NESTING - 24, MAX_JSON_NESTING + 2):
        root = S.run_root(tmp_path, f"obligation-{depth}")
        try:
            run = S.open_run(root, obligations=[obligation(depth)])
        except EvidenceError as error:
            # The first rejected depth must be a bounded EvidenceError from the manifest-preview
            # serialization, never an uncaught ValueError/RecursionError, and no run root is created.
            assert "ARGUS2-INPUT-FIELD-INVALID" in error.codes
            assert not root.exists()
            rejected = depth
            break
        assert run.writer_state == "open"
        accepted = depth

    assert accepted is not None
    assert rejected == accepted + 1

    # The accepted depth publishes a real open manifest and reads back as representable evidence.
    accepted_root = S.run_root(tmp_path, "obligation-accepted")
    S.open_run(accepted_root, obligations=[obligation(accepted)]).finalize()
    accepted_reader = EvidenceStore.read_run(accepted_root)
    accepted_document = json.loads(accepted_reader.export_json())
    assert accepted_document["evidenceStatus"] in ("complete", "incomplete")
    assert "Traceback" not in S.cli("export", str(accepted_root)).stderr


# AR-F01: reader/recovery confine and open the exact recorded eventStream.path ------------------


def _stream_meta(path: str, data: bytes) -> dict:
    """Return one frozen eventStream entry whose recorded facts describe ``data`` at ``path``."""

    return {
        "path": path,
        "mediaType": "application/x-ndjson",
        "schemaVersion": "1.0",
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _rewrite_manifest(root, **overrides) -> None:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest.update(overrides)
    (root / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )


def test_recovery_opens_the_exact_recorded_relative_path(tmp_path):
    root = tmp_path / "exact"
    root.mkdir()
    exact = S.annotation_event_bytes("exact")
    (root / "other.jsonl").write_bytes(exact)
    (root / "events.jsonl").write_bytes(S.annotation_event_bytes("decoy"))

    result = recover_stream(root, limits=EvidenceLimits(), relative="other.jsonl")

    assert [record["eventId"] for record in result.records] == ["exact"]
    assert result.byte_count == len(exact)
    assert result.sha256 == hashlib.sha256(exact).hexdigest()
    # A non-default recorded path names itself in every diagnostic; the canonical file is not read.
    assert all(item.path == "other.jsonl" for item in result.diagnostics)


def test_reader_missing_recorded_stream_path_never_reads_the_canonical_file(tmp_path):
    records = S.annotation_event_bytes("e1")
    root = S.synthetic_run(
        tmp_path / "missing",
        records,
        eventStream={**_stream_meta("events.jsonl", records), "path": "absent.jsonl"},
    )
    # events.jsonl is a perfectly valid canonical stream, but the manifest records a different file.
    # The reader must open the recorded path and report it missing -- never fall back to events.jsonl.
    assert (root / "events.jsonl").read_bytes() == records

    reader = EvidenceStore.read_run(root)  # must not raise
    assert "ARGUS2-MISSING-ARTIFACT" in {item.code for item in reader.diagnostics}
    assert reader.records() == []
    assert reader.assessed_evidence_status == "incomplete"
    document = json.loads(reader.export_json())
    assert document["evidenceStatus"] == "incomplete"
    assert document["assessedEvidenceStatus"] == "incomplete"
    assert document["records"] == []
    exported = S.cli("export", str(root), "--format", "json")
    assert exported.returncode == 0
    assert json.loads(exported.stdout)["evidenceStatus"] == "incomplete"


def test_reader_wrong_recorded_stream_path_metadata_never_claims_complete(tmp_path):
    canonical = S.annotation_event_bytes("e1")
    other = S.annotation_event_bytes("different")
    root = tmp_path / "wrong"
    S.synthetic_run(root, canonical)
    (root / "other.jsonl").write_bytes(other)
    # The recorded facts describe events.jsonl, but the recorded path points at other.jsonl.
    _rewrite_manifest(root, eventStream={**_stream_meta("events.jsonl", canonical), "path": "other.jsonl"})

    reader = EvidenceStore.read_run(root)  # must not raise
    codes = {item.code for item in reader.diagnostics}
    assert "ARGUS2-CORRUPT-ARTIFACT-SIZE" in codes or "ARGUS2-CORRUPT-ARTIFACT-HASH" in codes
    assert reader.assessed_evidence_status == "incomplete"
    document = json.loads(reader.export_json())
    assert document["evidenceStatus"] == "incomplete"
    assert document["assessedEvidenceStatus"] == "incomplete"


def test_reader_symlink_recorded_stream_path_rejected_even_when_confined(tmp_path):
    records = S.annotation_event_bytes("e1")
    root = tmp_path / "symlink"
    S.synthetic_run(root, records)
    (root / "events.jsonl").rename(root / "events.real.jsonl")
    os.symlink(root / "events.real.jsonl", root / "linked.jsonl")
    _rewrite_manifest(root, eventStream=_stream_meta("linked.jsonl", records))

    reader = EvidenceStore.read_run(root)  # must not raise
    assert "ARGUS2-PATH-SYMLINK" in {item.code for item in reader.diagnostics}
    assert reader.records() == []
    assert reader.assessed_evidence_status == "incomplete"
    assert json.loads(reader.export_json())["evidenceStatus"] == "incomplete"


def test_reader_opens_nested_recorded_stream_path_instead_of_the_canonical_file(tmp_path):
    nested = S.annotation_event_bytes("nested")
    decoy = S.annotation_event_bytes("decoy")
    root = tmp_path / "nested"
    S.synthetic_run(root, decoy)
    (root / "sub").mkdir()
    (root / "sub" / "events.jsonl").write_bytes(nested)
    _rewrite_manifest(root, eventStream=_stream_meta("sub/events.jsonl", nested))

    reader = EvidenceStore.read_run(root)  # must not raise
    # Only the exact recorded nested file is read; the canonical decoy is never substituted.
    assert [record["eventId"] for record in reader.records()] == ["nested"]
    assert reader.assessed_evidence_status == "complete"
    document = json.loads(reader.export_json())
    assert document["evidenceStatus"] == "complete"
    assert document["records"][0]["eventId"] == "nested"
