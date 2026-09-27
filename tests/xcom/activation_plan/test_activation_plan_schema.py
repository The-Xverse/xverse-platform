"""Validation tests for the canonical activation-plan v1 schema (T017).

The tests import the repository-owned validator's pure functions; they perform no network access,
start no child process, and write no file.
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_xcom_plan.py"
FIXTURES = ROOT / "tests" / "xcom" / "activation_plan" / "fixtures"


def load_validator():
    """Load a fresh validator module from its repository path."""

    spec = spec_from_file_location("validate_xcom_plan_plan_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("validator module could not be loaded")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()
PLAN_SCHEMA = validator.load_json(ROOT / validator.PLAN_SCHEMA_REL)


def _plan(name: str) -> dict:
    path = FIXTURES / "plan" / "valid" / name
    return json.loads(path.read_text(encoding="utf-8"))


def _codes(findings) -> set[int]:
    return {finding.code for finding in findings}


def test_valid_plan_accepted():
    """CHK-05..CHK-09: the activatable plan passes structure, ordering, and digest checks."""

    plan = _plan("plan-activatable.json")
    assert validator.validate_plan_structure(plan, PLAN_SCHEMA) == []
    assert validator.check_digest(plan) == []


def test_inspectable_plan_accepted():
    """CHK-07, NEG-A10: an inspectable plan with an unresolved input is accepted."""

    plan = _plan("plan-inspectable.json")
    assert plan["status"] == "inspectable"
    assert "unresolved" in plan["inputResolution"].values()
    assert validator.validate_plan_structure(plan, PLAN_SCHEMA) == []
    assert validator.check_digest(plan) == []


def test_plan_schema_closed_and_covers_required_content():
    """CHK-05, CHK-06: the schema is closed, versioned, and covers every content group."""

    assert validator.check_schema_structure(PLAN_SCHEMA, "plan schema") == []
    assert validator.check_plan_contract(PLAN_SCHEMA) == []
    assert PLAN_SCHEMA["properties"]["planVersion"]["const"] == "1"
    assert set(validator.COMMUNICATION_PLAN_GROUPS.values()) <= set(PLAN_SCHEMA["required"])


def test_plan_negatives():
    """NEG-A01..NEG-A22: each controlled plan defect yields its declared outcome."""

    cases = [case for case in validator.negative_cases(ROOT) if case[0].startswith("NEG-A")]
    assert len(cases) == 22
    for case_id, expected, check in cases:
        findings = check()
        if expected == validator.OK:
            assert findings == [], f"{case_id}: expected acceptance, got {sorted(_codes(findings))}"
        else:
            assert expected in _codes(findings), f"{case_id}: expected {expected}, got {sorted(_codes(findings))}"


def test_ordering_uniqueness_branches_exercised_directly():
    """NEG-A17..NEG-A21: every implemented ordering/uniqueness branch rejects directly."""

    plan = _plan("plan-activatable.json")

    undeclared = copy.deepcopy(plan)
    undeclared["activationOrder"] = ["controller-a", "route-undeclared"]
    assert validator.PLAN_INVALID in _codes(validator.check_ordering(undeclared))

    unordered = copy.deepcopy(plan)
    unordered["diagnostics"].append({"code": "XCOM-PLAN-AA", "severity": "info", "targetId": "route-ctrl"})
    assert validator.PLAN_INVALID in _codes(validator.check_ordering(unordered))

    duplicate_diagnostics = copy.deepcopy(plan)
    duplicate_diagnostics["diagnostics"].append(copy.deepcopy(duplicate_diagnostics["diagnostics"][0]))
    assert validator.PLAN_INVALID in _codes(validator.check_ordering(duplicate_diagnostics))

    unordered_resources = copy.deepcopy(plan)
    unordered_resources["provenance"]["resources"].reverse()
    assert validator.PLAN_INVALID in _codes(validator.check_ordering(unordered_resources))

    duplicate_resources = copy.deepcopy(plan)
    duplicate_resources["provenance"]["resources"].append(
        copy.deepcopy(duplicate_resources["provenance"]["resources"][0])
    )
    assert validator.PLAN_INVALID in _codes(validator.check_ordering(duplicate_resources))


def test_ordering_totality_over_optional_version():
    """T017-IR-008 closure: a mixed optional-`version` provenance duplicate is rejected, not raised."""

    plan = copy.deepcopy(_plan("plan-activatable.json"))
    resources = plan["provenance"]["resources"]
    without_version = copy.deepcopy(resources[1])
    without_version.pop("version")
    resources.append(without_version)

    # The mutated plan is schema-valid, yet it carries a duplicate identity.
    assert validator._json_schema_findings(PLAN_SCHEMA, plan, validator.PLAN_INVALID, "plan") == []
    findings = validator.validate_plan_structure(plan, PLAN_SCHEMA)
    assert validator.PLAN_INVALID in _codes(findings)
    assert validator.exit_code(findings) == validator.PLAN_INVALID
    assert validator.PLAN_INVALID in _codes(validator.check_ordering(plan))


def test_activatable_with_unresolved_input_rejected():
    """NEG-A09: an activatable plan with any unresolved input is rejected."""

    plan = _plan("plan-activatable.json")
    plan["inputResolution"]["ownership"] = "unresolved"
    findings = validator.validate_plan_structure(plan, PLAN_SCHEMA)
    assert validator.PLAN_INVALID in _codes(findings)
