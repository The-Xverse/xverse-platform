from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import EXAMPLE_PATHS, PROFILE_SCHEMA, ROOT


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments: str):
        return subprocess.run(
            [sys.executable, "-m", "xverse_xdl", *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def graph_args(self) -> list[str]:
        return ["--profile-schema", str(PROFILE_SCHEMA), *(str(path) for path in EXAMPLE_PATHS)]

    def test_version_json(self):
        completed = self.run_cli("version", "--format", "json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        value = json.loads(completed.stdout)
        self.assertEqual(value["supportedApiVersions"], ["xverse.io/xdl/v1alpha1"])

    def test_validate_valid_graph_as_json(self):
        completed = self.run_cli("validate", "--format", "json", *self.graph_args())
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["valid"])

    def test_validate_invalid_input_returns_one(self):
        completed = self.run_cli("validate", "--format", "json", "missing.xdl.yaml")
        self.assertEqual(completed.returncode, 1)
        self.assertFalse(json.loads(completed.stdout)["valid"])

    def test_normalize_is_deterministic_across_argument_order(self):
        forward = self.run_cli("normalize", *self.graph_args())
        reverse_args = ["--profile-schema", str(PROFILE_SCHEMA), *(str(path) for path in reversed(EXAMPLE_PATHS))]
        reverse = self.run_cli("normalize", *reverse_args)
        self.assertEqual(forward.returncode, 0, forward.stderr)
        self.assertEqual(forward.stdout, reverse.stdout)

    def test_explicit_output_is_written(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "normalized.json"
            completed = self.run_cli("normalize", "-o", str(output), *self.graph_args())
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(len(json.loads(output.read_text())["resources"]), 5)

    def test_input_output_collision_is_rejected(self):
        resource = EXAMPLE_PATHS[0]
        completed = self.run_cli("normalize", "-o", str(resource), str(resource))
        self.assertEqual(completed.returncode, 2)
        self.assertIn("output path is also an input", completed.stderr)

    def test_profile_schema_output_collision_is_rejected(self):
        completed = self.run_cli(
            "normalize", "-o", str(PROFILE_SCHEMA), *self.graph_args()
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("output path is also an input", completed.stderr)


if __name__ == "__main__":
    unittest.main()
