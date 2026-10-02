"""ARGUS2-SR-001-U: run admission and verified plan binding (frozen unit cases)."""

from __future__ import annotations

import copy

import pytest

from xverse.argus import EvidenceError, EvidenceStore

try:
    from tests.thesis_lite.argus import support as S
except ImportError:  # pragma: no cover - copied tests-directory layout
    import sys as _argus2_sys
    from pathlib import Path as _argus2_path

    _argus2_sys.path.insert(0, str(_argus2_path(__file__).resolve().parent))
    import support as S


def _plan() -> dict:
    return copy.deepcopy(S.neutral_plan())


def _fresh(tmp_path, name="run"):
    return S.run_root(tmp_path, name)


def test_fresh_run_opens_with_verified_plan_and_separated_provenance(tmp_path):
    plan = _plan()
    root = _fresh(tmp_path)
    run = EvidenceStore.open_run(
        root, run_id="run-a", plan=plan, source_byte_digests={"scenario.xdl": "ab" * 32}
    )
    assert run.run_id == "run-a"
    manifest = run.finalize()
    assert manifest.plan["semanticDigest"]["value"] == plan["digest"]["value"]
    provenance = manifest.data["sourceByteProvenance"]
    assert provenance["scenario.xdl"]["value"] == "ab" * 32
    assert provenance["scenario.xdl"]["value"] != manifest.plan["semanticDigest"]["value"]


def test_plan_digest_mutation_rejected(tmp_path):
    plan = _plan()
    plan["acceptanceIntent"] = "mutated after digest computation"
    with pytest.raises(EvidenceError) as error:
        EvidenceStore.open_run(_fresh(tmp_path), run_id="run-a", plan=plan)
    assert "ARGUS2-PLAN-DIGEST-MISMATCH" in error.value.codes
    assert not _fresh(tmp_path).exists()


def test_plan_matches_digest_api_is_reused_not_reimplemented(tmp_path, monkeypatch):
    from xverse_xdl import experiment_plan

    monkeypatch.setattr(experiment_plan, "plan_matches_digest", lambda plan: False)
    with pytest.raises(EvidenceError) as error:
        EvidenceStore.open_run(_fresh(tmp_path), run_id="run-a", plan=_plan())
    assert "ARGUS2-PLAN-DIGEST-MISMATCH" in error.value.codes
    assert not _fresh(tmp_path).exists()


def test_unsupported_plan_major_version_rejected(tmp_path):
    plan = _plan()
    plan["planVersion"] = "2"
    with pytest.raises(EvidenceError) as error:
        EvidenceStore.open_run(_fresh(tmp_path), run_id="run-a", plan=plan)
    assert "ARGUS2-PLAN-VERSION-UNSUPPORTED" in error.value.codes
    assert not _fresh(tmp_path).exists()


def test_envelope_run_id_conflict_rejected(tmp_path):
    with pytest.raises(EvidenceError) as error:
        EvidenceStore.open_run(
            _fresh(tmp_path), run_id="run-a", plan=_plan(), run_envelope={"runId": "run-b"}
        )
    assert "ARGUS2-PLAN-ENVELOPE-CONFLICT" in error.value.codes
    assert not _fresh(tmp_path).exists()


def test_existing_run_root_rejected_without_overwrite(tmp_path):
    root = _fresh(tmp_path)
    root.mkdir()
    sentinel = root / "sentinel.bin"
    sentinel.write_bytes(b"sentinel-bytes")
    with pytest.raises(EvidenceError) as error:
        EvidenceStore.open_run(root, run_id="run-a", plan=_plan())
    assert "ARGUS2-STATE-RUN-EXISTS" in error.value.codes
    assert sentinel.read_bytes() == b"sentinel-bytes"
    assert sorted(item.name for item in root.iterdir()) == ["sentinel.bin"]


def test_unsafe_run_id_rejected(tmp_path):
    with pytest.raises(EvidenceError) as error:
        EvidenceStore.open_run(_fresh(tmp_path), run_id="../escape", plan=_plan())
    assert "ARGUS2-INPUT-FIELD-INVALID" in error.value.codes
    assert not _fresh(tmp_path).exists()


def test_open_records_accepted_api_profile_and_plan_versions(tmp_path):
    plan = _plan()
    run = EvidenceStore.open_run(_fresh(tmp_path), run_id="run-a", plan=plan)
    manifest = run.finalize()
    assert manifest.plan["apiVersion"] == plan["selection"]["system"]["apiVersion"]
    assert manifest.plan["profileVersion"] == plan["profile"]["resource"]["version"]
    assert manifest.plan["planVersion"] == plan["planVersion"]


def test_source_byte_digests_never_substitute_semantic_identity(tmp_path):
    plan = _plan()
    different = "cd" * 32
    run = EvidenceStore.open_run(
        _fresh(tmp_path), run_id="run-a", plan=plan, source_byte_digests={"plan.src": different}
    )
    manifest = run.finalize()
    assert manifest.plan["semanticDigest"]["value"] == plan["digest"]["value"]
    assert manifest.data["sourceByteProvenance"]["plan.src"]["value"] == different


def test_no_ambient_clock_or_random_identity_at_open(tmp_path):
    plan_a = _plan()
    plan_b = _plan()
    run_a = EvidenceStore.open_run(_fresh(tmp_path, "a"), run_id="run-a", plan=plan_a)
    run_b = EvidenceStore.open_run(_fresh(tmp_path, "b"), run_id="run-a", plan=plan_b)
    manifest_a = run_a.finalize()
    manifest_b = run_b.finalize()
    assert "openedAt" not in manifest_a.data
    assert manifest_a.plan == manifest_b.plan
    assert manifest_a.data["runId"] == manifest_b.data["runId"] == "run-a"


def test_nested_obligation_detail_deep_snapshotted_against_caller_mutation(tmp_path):
    obligations = [
        {"obligationId": "o1", "kind": "min-observations", "required": True, "detail": {"minimum": 5}}
    ]
    root = _fresh(tmp_path)
    run = EvidenceStore.open_run(root, run_id="run-a", plan=_plan(), obligations=obligations)
    obligations[0]["detail"]["minimum"] = 0
    manifest = run.finalize()
    assert manifest.obligations[0]["detail"]["minimum"] == 5
    assert manifest.evidence_status == "incomplete"
    assert "ARGUS2-REASON-UNMET-OBLIGATION" in manifest.evidence_reasons


def test_non_json_encodable_or_nonfinite_obligation_detail_rejected_at_admission(tmp_path):
    nonfinite = {
        "obligationId": "o1",
        "kind": "min-observations",
        "required": True,
        "detail": {"minimum": float("nan")},
    }
    with pytest.raises(EvidenceError) as error:
        EvidenceStore.open_run(_fresh(tmp_path, "nan"), run_id="run-a", plan=_plan(), obligations=[nonfinite])
    assert "ARGUS2-INPUT-FIELD-INVALID" in error.value.codes
    assert not _fresh(tmp_path, "nan").exists()

    weird = {
        "obligationId": "o2",
        "kind": "min-observations",
        "required": True,
        "detail": {"minimum": object()},
    }
    with pytest.raises(EvidenceError) as error:
        EvidenceStore.open_run(_fresh(tmp_path, "obj"), run_id="run-a", plan=_plan(), obligations=[weird])
    assert "ARGUS2-INPUT-FIELD-INVALID" in error.value.codes
    assert not _fresh(tmp_path, "obj").exists()


def test_envelope_digests_clocks_and_extensions_deep_snapshotted(tmp_path):
    envelope = {
        "runId": "run-a",
        "openedAt": {"domain": "clock.open", "unit": "ns", "value": 1},
        "extensions": {"argus.note": {"v": [1]}},
    }
    digests = {"source.xdl": "ab" * 32}
    clocks = {"source": {"domain": "clock.source", "unit": "ns", "value": 5}}
    run = EvidenceStore.open_run(
        _fresh(tmp_path),
        run_id="run-a",
        plan=_plan(),
        run_envelope=envelope,
        source_byte_digests=digests,
        clocks=clocks,
    )
    envelope["runId"] = "run-evil"
    envelope["openedAt"]["value"] = 999
    envelope["openedAt"]["unit"] = "s"
    envelope["extensions"]["argus.note"]["v"].append(2)
    digests["source.xdl"] = "cd" * 32
    clocks["source"]["value"] = 999
    manifest = run.finalize()
    assert manifest.data["runId"] == "run-a"
    assert manifest.data["openedAt"] == {"domain": "clock.open", "unit": "ns", "value": 1}
    assert manifest.data["sourceByteProvenance"]["source.xdl"]["value"] == "ab" * 32
    assert manifest.data["clockDomains"] == ["clock.source"]
