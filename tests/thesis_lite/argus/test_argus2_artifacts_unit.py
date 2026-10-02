"""ARGUS2-SR-007-U: confined artifact store and reverification (frozen unit cases)."""

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


def _open(tmp_path, name="run", **kwargs):
    return S.open_run(S.run_root(tmp_path, name), **kwargs)


def test_safe_run_relative_artifact_paths_are_indexed(tmp_path):
    run = _open(tmp_path)
    root = S.run_root(tmp_path)
    (root / "evidence.json").write_text('{"v":1}\n', encoding="utf-8")
    run.record_artifact("evidence.json", role="evidence")
    manifest = run.finalize()
    entry = manifest.artifacts[0]
    assert entry["path"] == "evidence.json"
    assert entry["role"] == "evidence"
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-CORRUPT-ARTIFACT-HASH" not in {item.code for item in reader.diagnostics}


def test_traversal_segment_rejected(tmp_path):
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.record_artifact("sub/../evil.json")
    assert "ARGUS2-PATH-ESCAPE" in error.value.codes
    assert not (tmp_path / "evil.json").exists()


def test_absolute_artifact_path_rejected(tmp_path):
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.record_artifact("/etc/passwd")
    assert "ARGUS2-PATH-UNSAFE" in error.value.codes


def test_unsafe_artifact_name_rejected(tmp_path):
    run = _open(tmp_path)
    for name in ("a\\b.json", "bad name.json", "a//b.json"):
        with pytest.raises(EvidenceError) as error:
            run.record_artifact(name)
        assert "ARGUS2-PATH-UNSAFE" in error.value.codes


def test_escaping_symlink_rejected(tmp_path):
    run = _open(tmp_path)
    target = tmp_path / "outside.json"
    target.write_text("{}\n", encoding="utf-8")
    os.symlink(target, S.run_root(tmp_path) / "link.json")
    with pytest.raises(EvidenceError) as error:
        run.record_artifact("link.json")
    assert "ARGUS2-PATH-SYMLINK" in error.value.codes


def test_symlink_resolving_inside_run_root_still_rejected(tmp_path):
    run = _open(tmp_path)
    root = S.run_root(tmp_path)
    (root / "real.json").write_text("{}\n", encoding="utf-8")
    os.symlink(root / "real.json", root / "alias.json")
    with pytest.raises(EvidenceError) as error:
        run.record_artifact("alias.json")
    assert "ARGUS2-PATH-SYMLINK" in error.value.codes


def test_non_regular_file_rejected(tmp_path):
    run = _open(tmp_path)
    (S.run_root(tmp_path) / "subdir").mkdir()
    with pytest.raises(EvidenceError) as error:
        run.record_artifact("subdir")
    assert "ARGUS2-PATH-NOT-REGULAR" in error.value.codes


def test_missing_indexed_artifact_reported(tmp_path):
    run = _open(tmp_path)
    root = S.run_root(tmp_path)
    (root / "evidence.json").write_text("{}\n", encoding="utf-8")
    run.record_artifact("evidence.json")
    (root / "evidence.json").unlink()
    manifest = run.finalize()
    assert manifest.evidence_status == "incomplete"
    assert "ARGUS2-REASON-MISSING-ARTIFACT" in manifest.evidence_reasons
    assert "ARGUS2-MISSING-ARTIFACT" in {item.code for item in manifest.diagnostics}


def test_byte_mutated_artifact_hash_mismatch(tmp_path):
    run = _open(tmp_path)
    root = S.run_root(tmp_path)
    (root / "evidence.json").write_text('{"v":1}\n', encoding="utf-8")
    run.record_artifact("evidence.json")
    run.finalize()
    (root / "evidence.json").write_text('{"v":2}\n', encoding="utf-8")
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-CORRUPT-ARTIFACT-HASH" in {item.code for item in reader.diagnostics}


def test_size_mutated_artifact_size_mismatch(tmp_path):
    run = _open(tmp_path)
    root = S.run_root(tmp_path)
    (root / "evidence.json").write_text('{"v":1}\n', encoding="utf-8")
    run.record_artifact("evidence.json")
    run.finalize()
    (root / "evidence.json").write_text('{"value":100}\n', encoding="utf-8")
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-CORRUPT-ARTIFACT-SIZE" in {item.code for item in reader.diagnostics}


def test_no_write_occurs_outside_the_run_root(tmp_path):
    run = _open(tmp_path)
    (S.run_root(tmp_path) / "real.json").write_text("{}\n", encoding="utf-8")
    before = {item.name for item in tmp_path.iterdir()}
    attempts = ["sub/../escape.json", "/absolute.json", "back\\slash.json"]
    for attempt in attempts:
        with pytest.raises(EvidenceError):
            run.record_artifact(attempt)
    assert {item.name for item in tmp_path.iterdir()} == before


def test_artifact_reverification_is_read_only(tmp_path):
    run = _open(tmp_path)
    root = S.run_root(tmp_path)
    (root / "evidence.json").write_text('{"v":1}\n', encoding="utf-8")
    run.record_artifact("evidence.json")
    run.finalize()
    before = S.file_hashes(root)
    first = EvidenceStore.read_run(root)
    second = EvidenceStore.read_run(root)
    assert [item["path"] for item in first.manifest["artifacts"]] == [
        item["path"] for item in second.manifest["artifacts"]
    ]
    assert first.diagnostics == second.diagnostics
    assert S.file_hashes(root) == before


def test_mutating_returned_artifact_view_cannot_rewrite_indexed_hash(tmp_path):
    run = _open(tmp_path)
    root = S.run_root(tmp_path)
    (root / "evidence.json").write_text('{"v":1}\n', encoding="utf-8")
    entry = run.record_artifact("evidence.json")
    original_sha = entry["sha256"]
    original_bytes = entry["bytes"]
    entry["sha256"] = "0" * 64
    entry["bytes"] = 0
    entry["path"] = "rewritten.json"
    entry["role"] = "tampered"
    manifest = run.finalize()
    indexed = manifest.artifacts[0]
    assert indexed["path"] == "evidence.json"
    assert indexed["sha256"] == original_sha
    assert indexed["bytes"] == original_bytes
    assert indexed["role"] == "evidence"


def test_reader_artifact_path_confinement_checked_before_read(tmp_path):
    root = S.run_root(tmp_path)
    S.synthetic_run(root, S.annotation_event_bytes("e1"))
    target = tmp_path / "outside.json"
    target.write_bytes(b"secret")
    os.symlink(target, root / "alias.json")
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"] = [
        {
            "path": "alias.json",
            "mediaType": "application/json",
            "schemaVersion": "1.0",
            "bytes": 6,
            "sha256": "00" * 32,
            "role": "evidence",
        }
    ]
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    reader = EvidenceStore.read_run(root)
    assert "ARGUS2-PATH-SYMLINK" in {item.code for item in reader.diagnostics}
    assert reader.assessed_evidence_status == "incomplete"
