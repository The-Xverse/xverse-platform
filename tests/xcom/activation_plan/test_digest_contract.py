"""Canonical serialization, digest/provenance, and boundary checks for T017.

The tests import the repository-owned validator's pure functions; they perform no network access,
start no child process, and write no file.
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import copy
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_xcom_plan.py"
FIXTURES = ROOT / "tests" / "xcom" / "activation_plan" / "fixtures"


def load_validator():
    """Load a fresh validator module from its repository path."""

    spec = spec_from_file_location("validate_xcom_plan_digest_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("validator module could not be loaded")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def _plan() -> dict:
    path = FIXTURES / "plan" / "valid" / "plan-activatable.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _reorder(value):
    if isinstance(value, dict):
        return {key: _reorder(value[key]) for key in reversed(list(value.keys()))}
    if isinstance(value, list):
        return [_reorder(item) for item in value]
    return value


def _codes(findings) -> set[int]:
    return {finding.code for finding in findings}


def test_canonical_bytes_and_digest_are_key_order_stable():
    """CHK-10, DET-02: reordered members produce identical canonical bytes and digest."""

    plan = _plan()
    reordered = _reorder(plan)
    assert validator.canonical_bytes(plan) == validator.canonical_bytes(reordered)
    assert validator.compute_digest(plan) == validator.compute_digest(reordered)
    whitespaced = json.loads(json.dumps(plan, indent=4))
    assert validator.canonical_bytes(plan) == validator.canonical_bytes(whitespaced)


def test_digest_round_trip():
    """CHK-10: a recorded digest over the canonical body recomputes exactly."""

    plan = copy.deepcopy(_plan())
    plan["digest"]["value"] = validator.compute_digest(plan)
    assert validator.check_digest(plan) == []
    drifted = copy.deepcopy(plan)
    drifted["generator"]["version"] = "0.2.0"
    assert validator.DIGEST_INVALID in _codes(validator.check_digest(drifted))


def test_digest_region_excludes_digest_member():
    """NEG-D04 guard: the digested body never contains the digest member."""

    plan = _plan()
    assert "digest" not in validator.canonical_body(plan)


def test_digest_negatives():
    """NEG-D01..NEG-D04: each canonical/digest defect is rejected as DIGEST_INVALID."""

    cases = [case for case in validator.negative_cases(ROOT) if case[0].startswith("NEG-D")]
    assert len(cases) == 4
    for case_id, expected, check in cases:
        findings = check()
        assert expected in _codes(findings), f"{case_id}: expected {expected}, got {sorted(_codes(findings))}"


def test_validator_and_governance_negatives():
    """NEG-V01..NEG-V08 and NEG-G01..NEG-G05 behave at their declared exit classes."""

    cases = [
        case
        for case in validator.negative_cases(ROOT)
        if case[0].startswith("NEG-V") or case[0].startswith("NEG-G")
    ]
    assert len(cases) == 13
    for case_id, expected, check in cases:
        findings = check()
        assert expected in _codes(findings), f"{case_id}: expected {expected}, got {sorted(_codes(findings))}"


def test_canonical_bytes_normalize_integral_numbers():
    """T017-IR-001 closure: ``100`` and ``100.0`` share one canonical form and digest."""

    assert validator.canonical_bytes({"a": 1}) == validator.canonical_bytes({"a": 1.0})
    assert validator.canonical_bytes({"a": 1.0}) == b'{"a":1}'

    plan = _plan()
    integral = copy.deepcopy(plan)
    integral["policies"]["deadlineMs"] = 100
    fractional_form = copy.deepcopy(plan)
    fractional_form["policies"]["deadlineMs"] = 100.0
    assert validator.compute_digest(integral) == validator.compute_digest(fractional_form)

    fractional_form["digest"]["value"] = validator.compute_digest(fractional_form)
    assert validator.check_digest(fractional_form) == []


def test_duplicate_json_member_rejected():
    """T017-IR-002 closure: a repeated object member is rejected fail-closed, not collapsed."""

    try:
        validator.parse_json_text('{"a": 1, "a": 2}', "probe")
    except validator.PlanError as exc:
        assert exc.code == validator.IO_ERROR
    else:  # pragma: no cover - guards a regression
        raise AssertionError("duplicate JSON member was accepted")


def test_declared_bounds_enforced():
    """T017-IR-005 closure: fixture size, depth, and wall bounds are enforced."""

    assert validator.IO_ERROR in _codes(
        validator.check_input_bounds(
            {"a": 1}, size_bytes=validator.MAX_FIXTURE_BYTES + 1, max_bytes=validator.MAX_FIXTURE_BYTES
        )
    )
    assert validator.IO_ERROR in _codes(validator.check_input_bounds(validator.deep_probe_value()))
    assert validator.IO_ERROR in _codes(validator.check_wall_bound(validator.WALL_BOUND_SECONDS + 1))
    assert validator.check_wall_bound(0.0) == []


def test_authorized_path_boundary_consumes_changed_set():
    """T017-IR-003 closure: the repository-level path consumes a real changed set."""

    findings = validator.run_checks(ROOT, changed_paths=["src/xverse_xdl/xcom_plan.py"])
    assert validator.BOUNDARY_INVALID in _codes(findings)
    assert validator.run_checks(ROOT, changed_paths=["scripts/validate_xcom_plan.py"]) == []


def test_ref002_authoritative_record_not_promoted():
    """T017-IR-004 closure: REF-002 promotion is read from the authoritative record."""

    record = validator.load_json(ROOT / validator.REF002_RECORD_REL)
    assert validator.check_ref002(record["requirements"]) == []
    promoted = copy.deepcopy(record["requirements"])
    for entry in promoted:
        if entry.get("source_id") == "XVE-SYS-0139":
            entry["disposition"] = "implemented"
    assert validator.BOUNDARY_INVALID in _codes(validator.check_ref002(promoted))


def test_verification_plan_lists_every_implemented_test():
    """T017-IR-007 closure: the verification-plan test table and the modules agree exactly."""

    plan = (ROOT / "docs" / "engineering" / "xcom" / "t017" / "verification-plan.md").read_text(
        encoding="utf-8"
    )
    listed = set(re.findall(r"test_[a-z_]+\.py::(test_[a-z0-9_]+)", plan))
    implemented: set[str] = set()
    for module in ("test_profile_schema.py", "test_activation_plan_schema.py", "test_digest_contract.py"):
        source = (FIXTURES.parent / module).read_text(encoding="utf-8")
        implemented |= set(re.findall(r"^def (test_[a-z0-9_]+)\(", source, re.MULTILINE))
    assert implemented <= listed, f"tests missing from verification-plan.md §7: {sorted(implemented - listed)}"
    assert listed <= implemented, f"verification-plan.md §7 lists absent tests: {sorted(listed - implemented)}"


def test_self_test_entry_point_passes():
    """CHK-11, CHK-13: the validator self-test accepts the real artifacts and all negatives."""

    assert validator.self_test(ROOT) == validator.OK
    assert validator.run_checks(ROOT) == []
