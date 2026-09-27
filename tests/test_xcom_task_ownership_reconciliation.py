"""Governance regression tests for the X-COM T007 task-ownership reconciliation.

Terminal review R-01 found that the capability task checkboxes for T012–T016 and T021–T024
were complete while ``docs/engineering/xcom/task-ownership.md`` still recorded each as
``unreconciled`` "because the capability task checkbox is open".  This test binds the repaired
state: the exact delivered candidate revision per task, the pending-external-acceptance reason,
the byte-stable human projection, the checked capability ledger, and the analysis disposition.

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

DELIVERED_RANGE = (
    "T012", "T013", "T014", "T015", "T016", "T021", "T022", "T023", "T024",
)
ACCEPTED_ONLY = {"T025"}


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


def test_validator_declares_the_delivered_range():
    assert set(validator.DELIVERED_TASKS) == set(DELIVERED_RANGE)


def test_delivered_tasks_record_status_revision_and_pending_reason():
    model = _register_model()
    reconciliation = _reconciliation(model)
    for task, revision in validator.DELIVERED_TASKS.items():
        entry = reconciliation[task]
        assert entry["status"] == "delivered", task
        assert entry["revision"] == revision, task
        reason = entry["reason"]
        assert reason.strip(), task
        assert "external Codex review" in reason and "user acceptance remain pending" in reason
        # The false checkbox-open reason must be gone from every delivered entry.
        assert "checkbox is open" not in reason, task


def test_no_delivered_task_is_marked_accepted():
    model = _register_model()
    reconciliation = _reconciliation(model)
    accepted = {
        task for task, entry in reconciliation.items() if entry["status"] == "accepted"
    }
    assert accepted == ACCEPTED_ONLY
    assert validator.ACCEPTED_TASKS == {
        "T025": "4b01586b438a8587d231ee8828d896c206c06a96"
    }


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


def test_capability_ledger_checks_the_delivered_range():
    lines = TASKS_MD.read_text(encoding="utf-8").splitlines()
    for task in DELIVERED_RANGE:
        matching = [line for line in lines if line.startswith(f"- [X] {task} ")]
        assert matching, f"{task} is not checked complete in tasks.md"
        assert not any(
            line.startswith(f"- [ ] {task} ") for line in lines
        ), f"{task} is still open in tasks.md"


def test_analysis_records_delivered_pending_acceptance():
    analysis = ANALYSIS_MD.read_text(encoding="utf-8")
    assert "Resolved for delivery; external acceptance pending" in analysis
    assert "still require reconciliation" not in analysis
    assert "2026-09-27 terminal review R-01 repair" in analysis
