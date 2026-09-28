"""Governance regression tests for the accepted X-COM task-ownership reconciliation.

The terminal R-01 repair bound delivered tasks to exact candidate revisions. The later
user decision accepts T011–T016 and T021–T024 together at one reviewed successor
revision. These tests bind that decision, the byte-stable projection, the checked
capability ledger, and the analysis disposition.

The tests are offline and deterministic.  They load the repository-owned validator as a pure
module -- no child process, no network, no ambient or secret input, and no file writes -- and
they assert only public-safe identifiers already present in the repository.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_xcom_task_ownership.py"
REGISTER_JSON = ROOT / "docs" / "engineering" / "xcom" / "task-ownership.json"
REGISTER_MD = ROOT / "docs" / "engineering" / "xcom" / "task-ownership.md"
TASKS_MD = ROOT / "specs" / "007-xcom-core" / "tasks.md"
ANALYSIS_MD = ROOT / "specs" / "007-xcom-core" / "analysis.md"
DECISION_MD = ROOT / "docs" / "engineering" / "xcom" / "t011-t024-acceptance-decision.md"

ACCEPTED_RANGE = (
    "T011", "T012", "T013", "T014", "T015", "T016",
    "T021", "T022", "T023", "T024",
)
ACCEPTED_REVISION = "2f08355c418a20eb00cbea18506f85bf2ea883b7"
ACCEPTED_ONLY = {*ACCEPTED_RANGE, "T025"}


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_xcom_task_ownership_r01_test", VALIDATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise AssertionError("task-ownership validator module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = _load_validator()


def _register_text() -> str:
    return REGISTER_JSON.read_text(encoding="utf-8")


def _register_model() -> dict:
    return json.loads(_register_text())


def _reconciliation(model: dict) -> dict:
    result: dict = {}
    for slice_record in model["slices"]:
        for task, entry in slice_record.get("reconciliation", {}).items():
            result[task] = entry
    return result


def test_validator_declares_the_accepted_range():
    assert validator.DELIVERED_TASKS == {}
    assert set(validator.ACCEPTED_TASKS) == ACCEPTED_ONLY


def test_accepted_tasks_record_status_revision_and_decision_reason():
    model = _register_model()
    reconciliation = _reconciliation(model)
    for task in ACCEPTED_RANGE:
        entry = reconciliation[task]
        assert entry["status"] == "accepted", task
        assert entry["revision"] == ACCEPTED_REVISION, task
        reason = entry["reason"]
        assert reason.strip(), task
        assert "User accepted" in reason and "2026-09-28" in reason
        assert "checkbox is open" not in reason, task


def test_only_decided_tasks_are_marked_accepted():
    model = _register_model()
    reconciliation = _reconciliation(model)
    accepted = {
        task for task, entry in reconciliation.items() if entry["status"] == "accepted"
    }
    assert accepted == ACCEPTED_ONLY
    assert all(validator.ACCEPTED_TASKS[task] == ACCEPTED_REVISION for task in ACCEPTED_RANGE)
    assert validator.ACCEPTED_TASKS["T025"] == "4b01586b438a8587d231ee8828d896c206c06a96"


def test_projection_is_the_byte_stable_register_projection():
    model = _register_model()
    assert REGISTER_MD.read_text(encoding="utf-8") == validator.project_markdown(model)


def test_validator_accepts_the_positive_fixture():
    model = _register_model()
    findings = validator.run_checks(
        model,
        raw_text=_register_text(),
        markdown_text=REGISTER_MD.read_text(encoding="utf-8"),
    )
    assert findings.exit_code() == validator.EXIT_OK, findings.diagnostics()


def test_capability_ledger_checks_the_accepted_range():
    lines = TASKS_MD.read_text(encoding="utf-8").splitlines()
    for task in ACCEPTED_RANGE:
        matching = [line for line in lines if line.startswith(f"- [X] {task} ")]
        assert matching, f"{task} is not checked complete in tasks.md"
        assert not any(
            line.startswith(f"- [ ] {task} ") for line in lines
        ), f"{task} is still open in tasks.md"


def test_analysis_records_external_acceptance():
    analysis = ANALYSIS_MD.read_text(encoding="utf-8")
    assert "Accepted at exact successor revision" in analysis
    assert "still require reconciliation" not in analysis
    assert "2026-09-27 terminal review R-01 repair" in analysis
    assert "2026-09-28 user acceptance" in analysis


def test_repository_decision_binds_the_accepted_revision_and_scope():
    decision = DECISION_MD.read_text(encoding="utf-8")
    assert ACCEPTED_REVISION in decision
    assert "2026-09-28" in decision
    for task in ACCEPTED_RANGE:
        assert task in decision
    assert "T026" not in decision
