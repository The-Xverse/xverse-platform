"""DV12-N acceptance-evidence gate (increment19, finding 456): every blocker on synthetic runs.

The gate script is loaded from scripts/ by path, as the repository's other validator tests do.
Synthetic receipts are labelled; no real run, allowlist or G4 record is approved here.
"""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("acceptance_gate", ROOT / "scripts" / "validate_maestro_acceptance_evidence.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
HEAD, ARCHIVE = "c" * 40, "a" * 64
ALLOW = [dict(kind="skipped", match="test_lane.py:7", reason="needs the lane proposal", approval="SYNTHETIC")]


def write_run(tmp_path, *, collected=3, summary="2 passed, 1 skipped in 1.00s", returncode=0, timeout=False,
              head=HEAD, archive=ARCHIVE, installed=True, extra=""):
    run = tmp_path / "run"
    run.mkdir()
    (run / "configuration.json").write_text(json.dumps(dict(git_head=head, archive_sha256=archive,
        installed_equals_frozen_src=installed, wheel_verification=True, synthetic=True)))
    (run / "wheel-receipt.json").write_text(json.dumps(dict(git_head=head, archive_sha256=archive, collected=collected,
        returncode=returncode, outer_timeout=timeout, synthetic=True)))
    (run / "wheel.log").write_text("..s\n" + extra + "SKIPPED [1] tests/test_lane.py:7: lane proposal absent\n" + summary + "\n")
    return run


def g4(tmp_path, **override):
    record = dict(gate="G4", disposition="waived", scope="FR-001-FR-012 draft", approval="SYNTHETIC", **override)
    path = tmp_path / "g4.json"
    path.write_text(json.dumps(record))
    return path


def verdict(run, tmp_path, *, g4_path="default", allowlist=ALLOW, candidate=HEAD):
    path = g4(tmp_path) if g4_path == "default" else g4_path
    return gate.check(run, candidate, path, allowlist, ARCHIVE)


def test_clean_synthetic_run_with_listed_skip_and_g4_record_passes(tmp_path):
    result = verdict(write_run(tmp_path), tmp_path)
    assert result["accepted_as_evidence"] and result["blockers"] == [], result


@pytest.mark.parametrize("case,expected", [
    (dict(collected=0, summary="no tests ran in 0.01s"), "B1-zero-tests"),
    (dict(collected=4), "B1-count-mismatch"),
    (dict(summary="1 passed, 1 failed, 1 skipped in 1.00s", returncode=1), "B2-failures"),
    (dict(timeout=True), "B2-outer-timeout"),
    ("unlisted-skip", "B3-skipped-unlisted"),
    (dict(collected=4, summary="2 passed, 1 skipped, 1 xpassed in 1.00s"), "B3-xpassed"),
    ("stale-head", "B4-stale-head"),
    (dict(archive="b" * 64), "B4-archive-mismatch"),
    ("missing-g4", "B5-missing-g4-disposition"),
])
def test_each_dv12_mutation_is_blocked_by_its_own_rule(tmp_path, case, expected):
    kwargs = case if isinstance(case, dict) else {}
    run = write_run(tmp_path, **kwargs)
    options = {}
    if case == "unlisted-skip":
        options["allowlist"] = []
    if case == "stale-head":
        options["candidate"] = "d" * 40
    if case == "missing-g4":
        options["g4_path"] = None
    result = verdict(run, tmp_path, **options)
    assert not result["accepted_as_evidence"]
    assert any(b.startswith(expected) for b in result["blockers"]), result["blockers"]


def test_g4_record_without_approval_or_with_unknown_disposition_is_missing(tmp_path):
    run = write_run(tmp_path)
    for name, override in (("no-approval", dict(approval="")), ("pending", dict(disposition="pending"))):
        record = dict(gate="G4", disposition="waived", scope="s", approval="SYNTHETIC")
        record.update(override)
        path = tmp_path / ("g4-" + name + ".json")
        path.write_text(json.dumps(record))
        result = gate.check(run, HEAD, path, ALLOW, ARCHIVE)
        assert "B5-missing-g4-disposition" in result["blockers"], (name, result)
