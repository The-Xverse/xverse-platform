"""ARGUS2-SR-011-U: caller authority, offline operation and absence of control authority."""

from __future__ import annotations

import uuid

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


def test_caller_supplied_run_identity_is_required(tmp_path):
    with pytest.raises(EvidenceError) as error:
        EvidenceStore.open_run(S.run_root(tmp_path), run_id=None, plan=S.neutral_plan())
    assert "ARGUS2-INPUT-AUTHORITY-MISSING" in error.value.codes
    assert not S.run_root(tmp_path).exists()


def test_caller_supplied_limits_are_echoed_not_defaulted(tmp_path):
    limits = EvidenceLimits(max_events=7, max_payload_bytes=11)
    run = _open(tmp_path, limits=limits)
    manifest = run.finalize()
    assert manifest.limits == limits.to_data()


def test_caller_supplied_obligations_are_taken_verbatim(tmp_path):
    obligations = [{"obligationId": "o1", "kind": "no-known-loss", "required": False}]
    run = _open(tmp_path, obligations=obligations)
    manifest = run.finalize()
    assert manifest.obligations == obligations


def test_unknown_obligation_kind_rejected(tmp_path):
    with pytest.raises(EvidenceError) as error:
        _open(
            tmp_path,
            obligations=[{"obligationId": "o1", "kind": "best-effort", "required": True}],
        )
    assert "ARGUS2-INPUT-FIELD-INVALID" in error.value.codes
    assert not S.run_root(tmp_path).exists()


def test_no_network_access_during_open_append_finalize(tmp_path, monkeypatch):
    import socket

    def blocked(*args, **kwargs):
        raise AssertionError("no network access is permitted")

    monkeypatch.setattr(socket, "socket", blocked)
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    assert len(EvidenceStore.read_run(S.run_root(tmp_path)).records()) == 1


def test_no_subprocess_or_service_is_started(tmp_path, monkeypatch):
    import subprocess

    def blocked(*args, **kwargs):
        raise AssertionError("no subprocess, service or daemon is permitted")

    monkeypatch.setattr(subprocess, "run", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    run = _open(tmp_path)
    run.import_observation(S.projection([S.observation_record()]))
    run.finalize()
    assert EvidenceStore.read_run(S.run_root(tmp_path)).records()


def test_no_metric_computation_or_oracle_capability_is_exposed():
    import xverse.argus

    forbidden = ("compute_metric", "metric_value", "oracle", "evaluate_metric", "calculate")
    names = [name.lower() for name in xverse.argus.__all__]
    assert not any(any(token in name for token in forbidden) for name in names)


def test_no_control_or_actuation_output_is_produced(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.finalize()
    produced = sorted(item.name for item in S.run_root(tmp_path).iterdir())
    assert produced == ["events.jsonl", "manifest.json"]


def test_only_json_and_jsonl_artifacts_are_written(tmp_path):
    run = _open(tmp_path)
    run.append_event(event_id="e1", producer_id="p1", event_kind="annotation")
    run.import_observation(S.projection([S.observation_record()]))
    run.import_snapshot(S.snapshot())
    run.finalize()
    for item in S.run_root(tmp_path).iterdir():
        assert item.suffix in (".json", ".jsonl"), item.name


def test_no_remote_lookup_or_environment_discovery(tmp_path, monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.invalid:8080")
    monkeypatch.setenv("HOME", "/nonexistent-home")
    monkeypatch.setenv("USER", "env-user")
    run = S.open_run(S.run_root(tmp_path), run_id="run-a", plan=S.neutral_plan())
    manifest = run.finalize()
    assert manifest.data["runId"] == "run-a"
    assert manifest.limits == EvidenceLimits().to_data()
    assert "openedAt" not in manifest.data
    assert "env-user" not in (S.run_root(tmp_path) / "manifest.json").read_text(encoding="utf-8")


# Keep the standard-library identity module referenced without generating identities.
_ = uuid


def test_admitted_caller_objects_are_not_aliased_after_admission(tmp_path):
    envelope = {
        "runId": "run-a",
        "openedAt": {"domain": "clock.open", "unit": "ns", "value": 1},
        "extensions": {"argus.note": {"v": [1]}},
    }
    digests = {"source.xdl": "ab" * 32}
    clocks = {"source": {"domain": "clock.source", "unit": "ns", "value": 5}}
    obligations = [
        {"obligationId": "o1", "kind": "no-known-loss", "required": False, "detail": {"note": {"v": [1]}}}
    ]
    run = _open(tmp_path, run_envelope=envelope, source_byte_digests=digests, clocks=clocks, obligations=obligations)

    envelope["runId"] = "run-evil"
    envelope["openedAt"]["value"] = 9
    envelope["openedAt"]["unit"] = "s"
    envelope["extensions"]["argus.note"]["v"].append(2)
    digests["source.xdl"] = "cd" * 32
    clocks["source"]["value"] = 9
    obligations[0]["kind"] = "best-effort"
    obligations[0]["detail"]["note"]["v"].append(2)

    manifest = run.finalize()
    assert manifest.data["runId"] == "run-a"
    assert manifest.data["openedAt"] == {"domain": "clock.open", "unit": "ns", "value": 1}
    assert manifest.data["sourceByteProvenance"]["source.xdl"]["value"] == "ab" * 32
    assert manifest.data["clockDomains"] == ["clock.source"]
    assert manifest.obligations[0]["kind"] == "no-known-loss"
    assert manifest.obligations[0]["detail"]["note"]["v"] == [1]
