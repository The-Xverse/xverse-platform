"""Validation tests for the bounded ``io.xverse.xcom`` Profile v0.1 schema (T017).

The tests import the repository-owned validator's pure functions; they perform no network access,
start no child process, and write no file.
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_xcom_plan.py"
FIXTURES = ROOT / "tests" / "xcom" / "activation_plan" / "fixtures"


def load_validator():
    """Load a fresh validator module from its repository path."""

    spec = spec_from_file_location("validate_xcom_plan_profile_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("validator module could not be loaded")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()
PROFILE_SCHEMA = validator.load_json(ROOT / validator.PROFILE_SCHEMA_REL)


def _profile_payloads() -> list[tuple[Path, dict]]:
    directory = FIXTURES / "profile" / "valid"
    return [(path, json.loads(path.read_text(encoding="utf-8"))) for path in sorted(directory.glob("*.json"))]


def _codes(findings) -> set[int]:
    return {finding.code for finding in findings}


def test_valid_profile_payload_accepted():
    """CHK-01..CHK-04: every declared form is accepted and the five kinds are covered."""

    payloads = _profile_payloads()
    assert payloads, "no positive Profile fixtures found"
    assert {payload["kind"] for _, payload in payloads} == set(validator.PROFILE_KINDS)
    for path, payload in payloads:
        assert validator.validate_profile_payload(payload, PROFILE_SCHEMA) == [], f"{path.name} rejected"
    assert validator.validate_profile_set([payload for _, payload in payloads], PROFILE_SCHEMA) == []


def test_profile_schema_is_closed_and_discriminated():
    """CHK-01..CHK-03: the schema is valid, closed, and fixes version and discriminator."""

    assert validator.check_schema_structure(PROFILE_SCHEMA, "profile schema") == []
    assert validator.check_profile_contract(PROFILE_SCHEMA) == []
    assert PROFILE_SCHEMA["properties"]["schemaVersion"]["const"] == "0.1"
    assert set(PROFILE_SCHEMA["$defs"]["kind"]["enum"]) == set(validator.PROFILE_KINDS)


def test_profile_negatives():
    """NEG-P01..NEG-P14: each controlled Profile defect is rejected as PROFILE_INVALID."""

    cases = [case for case in validator.negative_cases(ROOT) if case[0].startswith("NEG-P")]
    assert len(cases) == 14
    for case_id, expected, check in cases:
        findings = check()
        assert expected in _codes(findings), f"{case_id}: expected {expected}, got {sorted(_codes(findings))}"


def test_unknown_field_and_kind_rejected_explicitly():
    """CHK-02, NEG-P04/NEG-P05: fail-closed on an unknown kind or top-level field."""

    assert validator.validate_profile_payload({"schemaVersion": "0.1", "kind": "nope"}, PROFILE_SCHEMA)
    good = _profile_payloads()[0][1]
    mutated = json.loads(json.dumps(good))
    mutated["kind"] = "unknown-policy"
    assert validator.PROFILE_INVALID in _codes(
        validator.validate_profile_payload(mutated, PROFILE_SCHEMA)
    )
