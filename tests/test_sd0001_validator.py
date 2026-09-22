"""Integration tests for the side-effect-free SD-0001 candidate validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_sd0001.py"


def load_validator():
    """Load a fresh validator module so tests can replace only its lock path."""

    spec = spec_from_file_location("validate_sd0001_test_instance", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("validator module could not be loaded")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_validator(module) -> tuple[int, dict]:
    """Run one validator module and return its code and parsed JSON report."""

    output = StringIO()
    with redirect_stdout(output):
        code = module.main()
    return code, json.loads(output.getvalue())


class Sd0001ValidatorTests(unittest.TestCase):
    """Prove exact success and fail-closed lock handling without lifecycle execution."""

    def test_reviewed_candidate_passes_but_remains_unplannable(self):
        """Accept the exact graph while reporting zero execution eligibility."""

        code, report = run_validator(load_validator())
        self.assertEqual(code, 0)
        self.assertTrue(report["valid"])
        self.assertFalse(report["plannable"])
        self.assertFalse(report["executionEligible"])
        self.assertFalse(report["legacyExecution"])
        self.assertEqual(len(report["blockers"]), 7)

    def test_resource_digest_drift_fails_before_xdl_validation(self):
        """Reject changed candidate content before deriving a catalog or plan."""

        module = load_validator()
        lock = json.loads(module.LOCK_PATH.read_text(encoding="utf-8"))
        lock["resources"][0]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            module.LOCK_PATH = Path(temporary) / "candidate.lock.json"
            module.LOCK_PATH.write_text(json.dumps(lock), encoding="utf-8")
            code, report = run_validator(module)
        self.assertEqual(code, 1)
        self.assertFalse(report["valid"])
        self.assertEqual(report["mismatches"], ["resource-digest:xdl/candidates/sd0001/component.xdl.yaml"])

    def test_lock_path_traversal_returns_stable_public_failure(self):
        """Reject a path outside the reviewed candidate root without echoing host detail."""

        module = load_validator()
        lock = json.loads(module.LOCK_PATH.read_text(encoding="utf-8"))
        lock["resources"][0]["path"] = "../outside"
        with tempfile.TemporaryDirectory() as temporary:
            module.LOCK_PATH = Path(temporary) / "candidate.lock.json"
            module.LOCK_PATH.write_text(json.dumps(lock), encoding="utf-8")
            code, report = run_validator(module)
        self.assertEqual(code, 1)
        self.assertEqual(
            report,
            {"legacyExecution": False, "mismatches": ["candidate-lock-invalid"], "valid": False},
        )

    def test_intermediate_symlink_cannot_escape_candidate_root(self):
        """Reject an allowed-looking path whose parent symlink resolves outside the root."""

        module = load_validator()
        with tempfile.TemporaryDirectory() as temporary:
            module.ROOT = Path(temporary)
            allowed = module.ROOT / "xdl" / "candidates" / "sd0001"
            outside = module.ROOT / "outside"
            allowed.mkdir(parents=True)
            outside.mkdir()
            (allowed / "escape").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                module._checked_path(
                    "xdl/candidates/sd0001/escape/resource.xdl.yaml",
                    "xdl/candidates/sd0001",
                )


if __name__ == "__main__":
    unittest.main()
