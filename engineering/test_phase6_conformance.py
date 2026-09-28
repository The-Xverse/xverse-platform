"""Negative controls for the Phase 6 source and documentation inspections."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import check_phase6_conformance as checker


class ConformanceNegativeControls(unittest.TestCase):
    def test_scoped_inventory_includes_json_evidence_and_task_tests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            doc = root / "docs/engineering/xcom/t026/internal-review.json"
            test = root / "tests/xcom/stimulation_journal/negative_tests.cpp"
            doc.parent.mkdir(parents=True)
            test.parent.mkdir(parents=True)
            doc.write_text('{"source": "' + "/" + "home/synthetic/fabric/automation/check.py" + '"}')
            test.write_text("// synthetic test\n")
            with patch.object(checker, "ROOT", root):
                inventory = checker.content_paths(26)
                self.assertIn(doc, inventory)
                self.assertIn(test, inventory)
                with self.assertRaisesRegex(ValueError, "public-content pattern"):
                    checker.scan_content([doc, test])
                doc.write_text("{}")
                test.write_text('const char* fixture = "' + '192.' + '168.1.2' + '";\n')
                with self.assertRaisesRegex(ValueError, "public-content pattern"):
                    checker.scan_content([doc, test])

    def test_removed_public_method_documentation_is_rejected(self) -> None:
        documented = "  /// \\brief Opens the journal.\n  /// \\return Ok.\n  JournalStatus open(Storage &storage);\n"
        self.assertIn("\\brief", checker.method_documentation(documented, "open"))
        with self.assertRaisesRegex(ValueError, "lacks its own Doxygen block"):
            checker.method_documentation("  JournalStatus open(Storage &storage);\n", "open")


if __name__ == "__main__":
    unittest.main()
