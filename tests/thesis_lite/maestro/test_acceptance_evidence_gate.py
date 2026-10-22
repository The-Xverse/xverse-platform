"""DV12-N acceptance-evidence gate (increment19, finding 456): every blocker on synthetic runs.

The gate script is loaded from scripts/ by path, as the repository's other validator tests do.
Synthetic receipts are labelled; no real run, allowlist or G4 record is approved here.
"""
import hashlib
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
    log = "..s\n" + extra + "SKIPPED [1] tests/test_lane.py:7: lane proposal absent\n" + summary + "\n"
    (run / "wheel.log").write_text(log)
    (run / "wheel-receipt.json").write_text(json.dumps(dict(git_head=head, archive_sha256=archive, collected=collected,
        returncode=returncode, outer_timeout=timeout, log_sha256=hashlib.sha256(log.encode()).hexdigest(), synthetic=True)))
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


def test_allowlisted_xfail_passes_and_unlisted_blocks(tmp_path):
    """Finding 463: the xfail branch of B3 in both directions."""
    line = "XFAIL tests/test_d.py::test_x - DIVERGENT D-00\n"
    run = write_run(tmp_path, collected=4, summary="2 passed, 1 skipped, 1 xfailed in 1.00s", extra=line)
    allow = ALLOW + [dict(kind="xfailed", match="test_d.py::test_x", reason="design divergence", approval="SYNTHETIC")]
    assert gate.check(run, HEAD, g4(tmp_path), allow, ARCHIVE)["blockers"] == []
    assert any(b.startswith("B3-xfailed-unlisted") for b in gate.check(run, HEAD, g4(tmp_path), ALLOW, ARCHIVE)["blockers"])


def test_not_installed_wheel_and_missing_run_files_block(tmp_path):
    """Finding 463: B4 not-installed-wheel-of-frozen-src and B0."""
    run = write_run(tmp_path, installed=False)
    assert any(b.startswith("B4-not-installed") for b in verdict(run, tmp_path)["blockers"])
    (run / "wheel.log").unlink()
    assert verdict(run, tmp_path)["blockers"][0].startswith("B0-missing-run-files")


def test_code_scope_ignores_head_difference_when_code_is_identical_and_blocks_otherwise(tmp_path):
    """Finding 463: path-scoped staleness."""
    run = write_run(tmp_path)
    same = gate.check(run, "d" * 40, g4(tmp_path), ALLOW, None, ("x" * 64, "x" * 64))
    differ = gate.check(run, "d" * 40, g4(tmp_path), ALLOW, None, ("x" * 64, "y" * 64))
    assert same["blockers"] == [], same
    assert any(b.startswith("B4-code-mismatch") for b in differ["blockers"]), differ
    own = gate.check(run, "d" * 40, g4(tmp_path), ALLOW, "b" * 64, ("x" * 64, "x" * 64))
    assert any(b.startswith("B4-archive-mismatch") and "its own head" in b for b in own["blockers"]), own


@pytest.mark.parametrize("path,kept", [
    ("src/xverse/maestro/dispatcher.py", True),
    ("docs/engineering/maestro-lite/expected-table-trace-20261021.json", True),
    ("docs/engineering/maestro-lite/design-oracle/ML-DESIGN-2026-10-03-v2/writer-closure-tables.json", True),
    ("docs/engineering/xcom/x.md", True),
    ("specs/007-xcom-core/spec.md", True),
    ("docs/engineering/maestro-lite/README.md", True),
    ("docs/engineering/maestro-lite/review-sub/notes.md", True),
    ("docs/engineering/maestro-lite/evidence/affa19/run/wheel.log", False),
    ("docs/engineering/maestro-lite/review-affa19.md", False),
])
def test_code_scope_keeps_every_path_a_test_may_read(path, kept):
    """Finding 474 item 1: only evidence folders and top-level review logs are outside the scope."""
    assert gate.in_code_scope(path) is kept


def test_log_not_bound_to_receipt_blocks(tmp_path):
    """Finding 474 item 2: a replaced wheel.log is not this run's evidence."""
    run = write_run(tmp_path)
    (run / "wheel.log").write_text((run / "wheel.log").read_text().replace("..s", ".s."))
    assert any(b.startswith("B2-log-unbound") for b in verdict(run, tmp_path)["blockers"])


def test_grouped_skip_line_counts_its_n(tmp_path):
    """Finding 474 item 6: SKIPPED [2] reports two skips, so a fully listed run passes."""
    line = "SKIPPED [2] tests/test_lane.py:9: lane proposal absent\n"
    run = write_run(tmp_path, collected=5, summary="2 passed, 3 skipped in 1.00s", extra=line)
    allow = ALLOW + [dict(kind="skipped", match="test_lane.py:9", reason="needs the lane proposal", approval="SYNTHETIC")]
    assert gate.check(run, HEAD, g4(tmp_path), allow, ARCHIVE)["blockers"] == []
