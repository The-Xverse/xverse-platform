"""ARGUS2-VALIDATION: intended-use scenarios ARGUS2-VS-01..07 (frozen validation identifiers)."""

from __future__ import annotations

import json
import os
import socket
import subprocess

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


def _omitted(**overrides):
    base = dict(payloadViewState="omitted", visibleBytesHex="", visibleByteCount=0, sourcePayloadSize=1024)
    base.update(overrides)
    return S.observation_record(**base)


# ARGUS2-VS-01 -------------------------------------------------------------------------


def test_caller_opens_run_from_real_compiled_plan_and_persists_events(tmp_path):
    from xverse_xdl.experiment_plan import compile_experiment_files

    plan = compile_experiment_files(S.FIXTURE_PATHS, profile_schema_paths=(S.profile_schema_path(),)).plan
    run = EvidenceStore.open_run(S.run_root(tmp_path), run_id="run-vs01", plan=plan)
    run.append_event(event_id="e1", producer_id="producer.alpha", event_kind="annotation")
    manifest = run.finalize()
    assert manifest.plan["semanticDigest"]["value"] == plan["digest"]["value"]
    assert EvidenceStore.read_run(S.run_root(tmp_path)).records()[0]["eventId"] == "e1"


def test_evidence_stream_records_identity_clocks_and_causation(tmp_path):
    run = _open(tmp_path)
    run.append_event(
        event_id="e1",
        producer_id="producer.alpha",
        event_kind="annotation",
        clocks={"source": {"domain": "clock.source", "unit": "ns", "value": 1}},
    )
    run.append_event(
        event_id="e2",
        producer_id="producer.alpha",
        event_kind="annotation",
        clocks={"source": {"domain": "clock.source", "unit": "ns", "value": 2}},
        causation_id="e1",
    )
    run.finalize()
    records = EvidenceStore.read_run(S.run_root(tmp_path)).records()
    assert records[0]["clocks"]["source"] == {"domain": "clock.source", "unit": "ns", "value": 1}
    assert records[1]["causationId"] == "e1"


def test_manifest_published_open_then_closed_with_verified_artifacts(tmp_path):
    run = _open(tmp_path)
    root = S.run_root(tmp_path)
    (root / "evidence.json").write_text("{}\n", encoding="utf-8")
    run.record_artifact("evidence.json")
    open_manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert open_manifest["writerState"] == "open"
    manifest = run.finalize()
    assert manifest.writer_state == "closed"
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-CORRUPT-ARTIFACT-HASH" not in {item.code for item in reader.diagnostics}


# ARGUS2-VS-02 -------------------------------------------------------------------------


def test_owned_observation_projection_preserves_visibility_and_loss(tmp_path):
    produced = S.run_producer()
    run = _open(tmp_path)
    run.import_observation(produced["projection"])
    run.import_snapshot(produced["snapshot"])
    run.finalize()
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    observations = [item["observation"] for item in reader.records() if item["eventKind"] == "observation"]
    assert [item["payloadViewState"] for item in observations] == [
        "omitted",
        "redacted",
        "truncated",
        "complete",
    ]
    assert "ARGUS2-REASON-KNOWN-LOSS" in reader.manifest["evidenceReasons"]


def test_metadata_only_redacted_and_truncated_payloads_remain_distinct(tmp_path):
    run = _open(tmp_path)
    run.import_observation(
        S.projection(
            [
                _omitted(),
                _omitted(payloadViewState="redacted"),
                S.observation_record(sourcePayloadSize=8, visibleBytesHex="00ff", visibleByteCount=2, payloadViewState="truncated"),
            ]
        )
    )
    run.finalize()
    records = [item["observation"] for item in EvidenceStore.read_run(S.run_root(tmp_path)).records()]
    assert [(item["payloadViewState"], item["visibleByteCount"]) for item in records] == [
        ("omitted", 0),
        ("redacted", 0),
        ("truncated", 2),
    ]


def test_snapshot_interval_closure_required_for_completeness(tmp_path):
    snapshot = S.snapshot()
    snapshot["intervalProvenance"]["closure"] = "unclosed"
    snapshot["intervalProvenance"].pop("start")
    snapshot["intervalProvenance"].pop("end")
    run = _open(
        tmp_path,
        obligations=[{"obligationId": "o1", "kind": "interval-closure", "required": True}],
    )
    run.import_snapshot(snapshot)
    manifest = run.finalize()
    assert manifest.evidence_status == "incomplete"
    assert "ARGUS2-REASON-UNCLOSED-INTERVAL" in manifest.evidence_reasons
    assert "ARGUS2-REASON-UNMET-OBLIGATION" in manifest.evidence_reasons


# ARGUS2-VS-03 -------------------------------------------------------------------------


def test_reader_reconstructs_evidence_read_only_deterministically(tmp_path):
    run = _open(tmp_path)
    for index in range(3):
        run.append_event(event_id=f"e{index}", producer_id="p1", event_kind="annotation")
    run.finalize()
    root = S.run_root(tmp_path)
    before = S.file_hashes(root)
    reader = EvidenceStore.read_run(root)
    assert reader.export_json() == reader.export_json()
    assert reader.export_jsonl() == reader.export_jsonl()
    assert S.file_hashes(root) == before


def test_metric_inputs_link_captured_selection_without_computation(tmp_path):
    run = _open(tmp_path)
    root = S.run_root(tmp_path)
    (root / "evidence").mkdir()
    (root / "evidence" / "sample-observer.json").write_text("{}\n", encoding="utf-8")
    run.record_artifact("evidence/sample-observer.json")
    run.finalize()
    entry = EvidenceStore.read_run(root).metric_inputs()[0]
    assert entry["selection"] == ["evidence/sample-observer.json"]
    assert "value" not in entry


def test_replay_never_executes_components_or_oracle(tmp_path, monkeypatch):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()

    def blocked(*args, **kwargs):
        raise AssertionError("replay must not execute components or oracles")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(subprocess, "run", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert reader.records() and reader.export_json() and reader.export_jsonl()


# ARGUS2-VS-04 -------------------------------------------------------------------------


def test_digest_mutation_and_unsupported_versions_rejected_without_partial_state(tmp_path):
    import copy

    mutated = copy.deepcopy(S.neutral_plan())
    mutated["acceptanceIntent"] = "mutated"
    with pytest.raises(EvidenceError) as error:
        _open(tmp_path, f"digest", plan=mutated)
    assert "ARGUS2-PLAN-DIGEST-MISMATCH" in error.value.codes
    unsupported = copy.deepcopy(S.neutral_plan())
    unsupported["planVersion"] = "2"
    with pytest.raises(EvidenceError) as error:
        _open(tmp_path, f"version", plan=unsupported)
    assert "ARGUS2-PLAN-VERSION-UNSUPPORTED" in error.value.codes
    assert sorted(item.name for item in tmp_path.iterdir()) == []


def test_duplicate_identity_and_nonfinite_values_rejected(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    with pytest.raises(EvidenceError) as error:
        run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    assert "ARGUS2-INPUT-DUPLICATE-EVENT" in error.value.codes
    with pytest.raises(EvidenceError) as error:
        run.append_event(
            event_id="e2",
            producer_id="p1",
            event_kind="annotation",
            clocks={"source": {"domain": "d1", "unit": "ns", "value": float("nan")}},
        )
    assert "ARGUS2-INPUT-NONFINITE" in error.value.codes


def test_missing_clock_domain_and_unit_rejected(tmp_path):
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.append_event(
            event_id="e1", producer_id="p1", event_kind="annotation",
            clocks={"source": {"unit": "ns", "value": 1}},
        )
    assert "ARGUS2-INPUT-CLOCK-MISSING" in error.value.codes
    with pytest.raises(EvidenceError) as error:
        run.append_event(
            event_id="e2", producer_id="p1", event_kind="annotation",
            clocks={"source": {"domain": "d1", "value": 1}},
        )
    assert "ARGUS2-INPUT-UNIT-MISSING" in error.value.codes


def test_exceeded_caller_bounds_rejected_with_stable_diagnostics(tmp_path):
    run = _open(tmp_path, limits=EvidenceLimits(max_event_bytes=32))
    with pytest.raises(EvidenceError) as error:
        run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    assert error.value.diagnostics[0].code == "ARGUS2-BOUND-EXCEEDED"
    assert error.value.diagnostics[0].category == "bounds"
    assert (S.run_root(tmp_path) / "events.jsonl").read_bytes() == b""


def test_unsafe_paths_and_symlink_escapes_rejected(tmp_path):
    run = _open(tmp_path)
    target = tmp_path / "outside.json"
    target.write_text("{}\n", encoding="utf-8")
    os.symlink(target, S.run_root(tmp_path) / "link.json")
    cases = [("sub/../escape.json", "ARGUS2-PATH-ESCAPE"), ("/absolute.json", "ARGUS2-PATH-UNSAFE"), ("link.json", "ARGUS2-PATH-SYMLINK")]
    for path, code in cases:
        with pytest.raises(EvidenceError) as error:
            run.record_artifact(path)
        assert code in error.value.codes
    assert not (tmp_path / "escape.json").exists()


# ARGUS2-VS-05 -------------------------------------------------------------------------


def test_truncated_stream_and_interrupted_finalize_report_incomplete(tmp_path, monkeypatch):
    run = _open(tmp_path, "truncated")
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.append_event(event_id="e2", producer_id="p1", event_kind="annotation")
    run.finalize()
    stream = S.run_root(tmp_path, "truncated") / "events.jsonl"
    stream.write_bytes(stream.read_bytes().rstrip(b"\n"))
    reader = EvidenceStore.read_run(S.run_root(tmp_path, "truncated"))
    assert "ARGUS2-CORRUPT-STREAM-TRUNCATED" in {item.code for item in reader.diagnostics}

    run = _open(tmp_path, "interrupted")
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")

    def boom(*args, **kwargs):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(EvidenceError) as error:
        run.finalize()
    assert "ARGUS2-IO-FAILURE" in error.value.codes
    assert run.writer_state == "failed"
    monkeypatch.undo()


def test_known_loss_and_unmet_obligation_never_become_complete(tmp_path):
    run = _open(
        tmp_path,
        obligations=[{"obligationId": "o1", "kind": "no-known-loss", "required": True}],
    )
    run.import_observation(
        S.projection([_omitted(counters={"queued": 1, "accepted": 1, "dropped": 1, "coalesced": 0})])
    )
    manifest = run.finalize()
    assert manifest.evidence_status == "incomplete"
    assert "ARGUS2-REASON-KNOWN-LOSS" in manifest.evidence_reasons
    assert "ARGUS2-REASON-UNMET-OBLIGATION" in manifest.evidence_reasons


def test_missing_causal_and_interval_closure_remain_visible(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation", causation_id="missing")
    run.import_snapshot(S.snapshot(validityState="degraded", experimentValidityDegraded=True))
    manifest = run.finalize()
    assert "ARGUS2-REASON-UNRESOLVED-CAUSATION" in manifest.evidence_reasons
    assert "ARGUS2-REASON-DEGRADED-INTERVAL" in manifest.evidence_reasons


def test_recovery_reads_bounded_prefix_without_mutating_originals(tmp_path):
    run = _open(tmp_path)
    for index in range(3):
        run.append_event(event_id=f"e{index}", producer_id="p1", event_kind="annotation")
    run.finalize()
    root = S.run_root(tmp_path)
    stream = root / "events.jsonl"
    stream.write_bytes(stream.read_bytes() + b'{"partial":')
    before = S.file_hashes(root)
    reader = EvidenceStore.read_run(root)
    assert [item["eventId"] for item in reader.records()] == ["e0", "e1", "e2"]
    assert "ARGUS2-CORRUPT-STREAM-TRUNCATED" in {item.code for item in reader.diagnostics}
    assert S.file_hashes(root) == before


# ARGUS2-VS-06 -------------------------------------------------------------------------


def test_installed_wheel_imports_argus_and_preserved_xdl_contracts():
    _wheel, target = S.wheel_and_target()
    completed = S.installed_python(
        "import xverse.argus, xverse_xdl.experiment_plan as e, sys;"
        "print(xverse.argus.__file__); print(e.__file__)",
        target,
    )
    assert completed.returncode == 0, completed.stderr
    assert str(target) in completed.stdout
    assert "/workspace/src" not in completed.stdout


def test_additive_unknown_field_and_unknown_major_behaviour_explicit(tmp_path):
    _wheel, target = S.wheel_and_target()
    unknown = S.synthetic_run(tmp_path / "unknown", S.annotation_event_bytes(unknown=True))
    major = S.synthetic_run(tmp_path / "major", S.annotation_event_bytes(), schemaVersion="2.0")
    script = (
        "import json, sys; from xverse.argus import EvidenceStore;"
        "a = EvidenceStore.read_run(sys.argv[1]); b = EvidenceStore.read_run(sys.argv[2]);"
        "print(json.dumps({'a': [d.code for d in a.diagnostics], 'b': [d.code for d in b.diagnostics]}))"
    )
    completed = subprocess.run(
        [__import__("sys").executable, "-c", script, str(unknown), str(major)],
        cwd=str(S.HERE), text=True, capture_output=True, check=False, env=S.installed_env(target),
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert "ARGUS2-SCHEMA-UNKNOWN-FIELD" in payload["a"]
    assert "ARGUS2-SCHEMA-MAJOR-UNSUPPORTED" in payload["b"]


def test_existing_xdl_cli_and_public_api_unchanged():
    environment = dict(os.environ)
    environment.setdefault("PYTHONPATH", str(S.ROOT / "src"))
    completed = subprocess.run(
        [__import__("sys").executable, "-m", "xverse_xdl", "version", "--format", "json"],
        cwd=str(S.HERE), text=True, capture_output=True, check=False, env=environment,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["supportedApiVersions"] == ["xverse.io/xdl/v1alpha1"]


# ARGUS2-VS-07 -------------------------------------------------------------------------


def test_repeated_reads_and_exports_are_byte_equal(tmp_path):
    run = _open(tmp_path)
    run.import_observation(S.projection([S.observation_record()]))
    run.finalize()
    first = EvidenceStore.read_run(S.run_root(tmp_path))
    second = EvidenceStore.read_run(S.run_root(tmp_path))
    assert first.export_json() == second.export_json()
    assert first.export_jsonl() == second.export_jsonl()


def test_retention_counters_do_not_substitute_for_interval_closure(tmp_path):
    run = _open(
        tmp_path,
        obligations=[{"obligationId": "o1", "kind": "interval-closure", "required": True}],
    )
    run.import_observation(
        S.projection([_omitted(counters={"queued": 1, "accepted": 1, "dropped": 0, "coalesced": 0})])
    )
    manifest = run.finalize()
    assert manifest.evidence_status == "incomplete"
    assert "ARGUS2-REASON-UNMET-OBLIGATION" in manifest.evidence_reasons


def test_ingestion_order_is_not_temporal_or_causal_order(tmp_path):
    run = _open(tmp_path)
    for index, value in enumerate((300, 100, 200)):
        run.append_event(
            event_id=f"e{index}", producer_id="p1", event_kind="annotation",
            clocks={"source": {"domain": "d1", "unit": "ns", "value": value}},
        )
    run.finalize()
    records = EvidenceStore.read_run(S.run_root(tmp_path)).records()
    assert [item["ingestionOrdinal"] for item in records] == [1, 2, 3]
    assert [item["clocks"]["source"]["value"] for item in records] == [300, 100, 200]


def test_canonical_serialization_independent_of_input_key_order(tmp_path):
    first = dict(reversed(list(S.observation_record().items())))
    second = dict(S.observation_record())
    run_a = _open(tmp_path, "a")
    run_a.import_observation(S.projection([first]))
    run_a.finalize()
    run_b = _open(tmp_path, "b")
    run_b.import_observation(S.projection([second]))
    run_b.finalize()
    assert EvidenceStore.read_run(S.run_root(tmp_path, "a")).export_jsonl() == EvidenceStore.read_run(
        S.run_root(tmp_path, "b")
    ).export_jsonl()


# ARGUS2-VS-08 (terminal-review repair AR-F01..AR-F05; ARGUS2-ADV-01..07) ---------------


def _stream_entry(records: bytes) -> dict:
    import hashlib

    return {
        "path": "events.jsonl",
        "mediaType": "application/x-ndjson",
        "schemaVersion": "1.0",
        "bytes": len(records),
        "sha256": hashlib.sha256(records).hexdigest(),
    }


def test_adversarial_reads_confined_and_bounded_before_io(tmp_path):
    records = S.annotation_event_bytes("e1")

    traversal = tmp_path / "traversal"
    S.synthetic_run(traversal, records, eventStream={**_stream_entry(records), "path": "../escape.jsonl"})
    assert "ARGUS2-PATH-ESCAPE" in {item.code for item in EvidenceStore.read_run(traversal).diagnostics}

    link = tmp_path / "link"
    S.synthetic_run(link, records)
    (link / "events.jsonl").rename(link / "events.real.jsonl")
    os.symlink(link / "events.real.jsonl", link / "events.jsonl")
    assert "ARGUS2-PATH-SYMLINK" in {item.code for item in EvidenceStore.read_run(link).diagnostics}

    oversized = tmp_path / "oversized"
    S.synthetic_run(oversized, records)
    reader = EvidenceStore.read_run(oversized, limits=EvidenceLimits(max_manifest_bytes=10))
    assert "ARGUS2-BOUND-EXCEEDED" in {item.code for item in reader.diagnostics}
    assert any("max_manifest_bytes" in item.message for item in reader.diagnostics)

    first = S.annotation_event_bytes("e1")
    long_record = {
        "schemaVersion": "1.0",
        "runId": "run-synthetic",
        "eventId": "e2",
        "producerId": "p1",
        "ingestionOrdinal": 2,
        "eventKind": "annotation",
        "annotation": {"text": "x" * 512},
    }
    long_line = json.dumps(long_record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
    line_bound = tmp_path / "line-bound"
    S.synthetic_run(line_bound, first + long_line)
    reader = EvidenceStore.read_run(
        line_bound, limits=EvidenceLimits(max_event_bytes=len(first.rstrip(b"\n")))
    )
    assert any("max_event_bytes" in item.message for item in reader.diagnostics)

    echoed = tmp_path / "echo"
    run = _open(tmp_path, "echo-source")
    for index in range(4):
        run.append_event(event_id=f"e{index}", producer_id="p1", event_kind="annotation")
    run.finalize()
    source_root = S.run_root(tmp_path, "echo-source")
    manifest = json.loads((source_root / "manifest.json").read_text(encoding="utf-8"))
    manifest["limits"] = {key: 10**9 for key in EvidenceLimits().to_data()}
    (source_root / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    reader = EvidenceStore.read_run(source_root, limits=EvidenceLimits(max_read_records=2))
    assert len(reader.records()) == 2
    assert "ARGUS2-BOUND-EXCEEDED" in {item.code for item in reader.diagnostics}
    _ = echoed


def test_adversarial_corrupt_evidence_assessed_incomplete_never_primary_complete(tmp_path):
    run = _open(tmp_path, "truncated")
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    root = S.run_root(tmp_path, "truncated")
    stream = root / "events.jsonl"
    stream.write_bytes(stream.read_bytes().rstrip(b"\n"))
    reader = EvidenceStore.read_run(root)
    assert reader.recorded_evidence_status == "complete"
    assert reader.assessed_evidence_status == "incomplete"
    assert reader.assessed_evidence_reasons
    assert json.loads(reader.export_json())["evidenceStatus"] == "incomplete"
    assert S.cli("verify", str(root)).returncode == 1

    run = _open(tmp_path, "shape")
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    root = S.run_root(tmp_path, "shape")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["artifacts"] = 5
    (root / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-CORRUPT-MANIFEST-SHAPE" in {item.code for item in reader.diagnostics}
    assert reader.assessed_evidence_status == "incomplete"
    assert "ARGUS2-REASON-CORRUPT-MANIFEST" in reader.assessed_evidence_reasons
    assert json.loads(reader.export_json())["evidenceStatus"] == "incomplete"


def test_adversarial_strict_schema_and_identities_yield_only_stable_diagnostics(tmp_path):
    def raw(record: dict) -> bytes:
        return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"

    base = {
        "schemaVersion": "1.0",
        "runId": "run-synthetic",
        "eventId": "e1",
        "producerId": "p1",
        "ingestionOrdinal": 1,
        "eventKind": "annotation",
    }
    cases = {
        "duplicate": raw(base) + raw(base),
        "ordinal": raw({**base, "eventId": "e1"}) + raw({**base, "eventId": "e2"}),
        "runid": raw({**base, "runId": "other-run"}),
        "missing": raw({"schemaVersion": "1.0", "producerId": "p1", "ingestionOrdinal": 1, "eventKind": "annotation"}),
        "nonfinite": raw(base).replace(b'"eventKind":"annotation"', b'"eventKind":"annotation","clocks":{"source":{"domain":"d","unit":"ns","value":NaN}}'),
        "container": b'{"schemaVersion":"1.0","runId":"run-synthetic","eventId":"e1","producerId":"p1","ingestionOrdinal":1,"eventKind":"annotation","clocks":5}\n',
    }
    expected = {
        "duplicate": "ARGUS2-CORRUPT-DUPLICATE-EVENT",
        "ordinal": "ARGUS2-CORRUPT-ORDINAL",
        "runid": "ARGUS2-CORRUPT-RUN-ID-MISMATCH",
        "missing": "ARGUS2-INPUT-IDENTITY-MISSING",
        "nonfinite": "ARGUS2-INPUT-NONFINITE",
        "container": "ARGUS2-INPUT-CLOCK-MISSING",
    }
    for name, payload in cases.items():
        root = tmp_path / name
        S.synthetic_run(root, payload)
        reader = EvidenceStore.read_run(root)  # must not raise
        assert expected[name] in {item.code for item in reader.diagnostics}, name
        assert reader.assessed_evidence_status == "incomplete", name
        assert S.cli("verify", str(root)).returncode == 1, name


def test_adversarial_manifest_byte_bound_enforced_at_every_publication(tmp_path):
    S.open_run(S.run_root(tmp_path, "probe"))
    # The exact serialized manifest bytes written: canonical JSON plus its single trailing newline.
    open_len = (S.run_root(tmp_path, "probe") / "manifest.json").stat().st_size

    root = S.run_root(tmp_path, "finalize")
    run = S.open_run(root, limits=EvidenceLimits(max_manifest_bytes=open_len))
    (root / "evidence.json").write_text("{}\n", encoding="utf-8")
    run.record_artifact("evidence.json")
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    before = (root / "manifest.json").read_bytes()
    with pytest.raises(EvidenceError) as error:
        run.finalize()
    assert "ARGUS2-BOUND-EXCEEDED" in error.value.codes
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


def test_adversarial_admission_snapshots_and_views_immune_to_caller_mutation(tmp_path):
    obligations = [
        {"obligationId": "o1", "kind": "min-observations", "required": True, "detail": {"minimum": 3}}
    ]
    run = _open(tmp_path, obligations=obligations)
    obligations[0]["detail"]["minimum"] = 0
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation", annotation={"text": "n"})
    manifest = run.finalize()
    assert manifest.obligations[0]["detail"]["minimum"] == 3
    assert manifest.evidence_status == "incomplete"
    assert "ARGUS2-REASON-UNMET-OBLIGATION" in manifest.evidence_reasons

    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    baseline = reader.export_json()
    records = reader.records()
    records[0]["eventId"] = "evil"
    records[0]["annotation"]["text"] = "mutated"
    reader.manifest["runId"] = "evil"
    for entry in reader.metric_inputs():
        entry["selectionStatus"] = "evil"
    assert reader.export_json() == baseline
    assert EvidenceStore.read_run(S.run_root(tmp_path)).records()[0]["eventId"] == "e1"
