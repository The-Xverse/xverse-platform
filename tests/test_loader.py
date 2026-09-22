from __future__ import annotations

import unittest

from xverse_xdl.loader import SourceInput, load_sources
from xverse_xdl.models import LoadLimits


class LoaderTests(unittest.TestCase):
    def load(self, text: str, name: str = "resource.yaml", limits: LoadLimits | None = None):
        return load_sources((SourceInput(name, text.encode()),), limits=limits or LoadLimits())

    def assert_code(self, text: str, code: str, name: str = "resource.yaml", limits=None) -> None:
        documents, diagnostics = self.load(text, name, limits)
        self.assertFalse(documents)
        self.assertIn(code, {item.code for item in diagnostics})

    def test_yaml_uses_1_2_scalar_rules_and_source_locations(self):
        documents, diagnostics = self.load("apiVersion: xverse.io/xdl/v1alpha1\nkind: Profile\nvalue: On\n")
        self.assertFalse(diagnostics)
        self.assertEqual(documents[0].data["value"], "On")
        self.assertEqual(documents[0].source_map["/kind"].line, 2)

    def test_yaml_duplicate_key_is_rejected(self):
        self.assert_code("kind: System\nkind: Profile\n", "XDL-PARSE-DUPLICATE-KEY")

    def test_json_duplicate_key_is_rejected(self):
        self.assert_code('{"kind":"System","kind":"Profile"}', "XDL-PARSE-DUPLICATE-KEY", "x.json")

    def test_multiple_yaml_documents_are_rejected(self):
        self.assert_code("kind: System\n---\nkind: Profile\n", "XDL-PARSE-MULTI-DOCUMENT")

    def test_non_string_key_is_rejected(self):
        self.assert_code("1: value\n", "XDL-PARSE-NON-STRING-KEY")

    def test_non_finite_json_number_is_rejected(self):
        self.assert_code('{"value": NaN}', "XDL-PARSE-NON-FINITE", "x.json")

    def test_file_size_limit_is_enforced(self):
        self.assert_code("kind: Profile\n", "XDL-PARSE-TOO-LARGE", limits=LoadLimits(max_bytes_per_file=4))

    def test_depth_limit_is_enforced(self):
        self.assert_code("a:\n  b:\n    c: 1\n", "XDL-PARSE-MAX-DEPTH", limits=LoadLimits(max_depth=2))

    def test_node_limit_is_enforced(self):
        self.assert_code("a: [1, 2, 3]\n", "XDL-PARSE-MAX-NODES", limits=LoadLimits(max_nodes=3))

    def test_cyclic_alias_is_rejected(self):
        self.assert_code("a: &loop\n  self: *loop\n", "XDL-PARSE-CYCLE")

    def test_explicit_yaml_1_1_is_rejected(self):
        self.assert_code("%YAML 1.1\n---\nvalue: yes\n", "XDL-PARSE-YAML-VERSION")


if __name__ == "__main__":
    unittest.main()
