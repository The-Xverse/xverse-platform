from __future__ import annotations

import copy
import unittest

from xverse_xdl.schema import CoreSchemaRegistry
from tests.helpers import parsed_examples


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.registry = CoreSchemaRegistry()

    def test_all_five_examples_pass_kind_schemas(self):
        for resource in parsed_examples().values():
            with self.subTest(kind=resource["kind"]):
                self.assertEqual(self.registry.validate_resource(resource, "fixture"), ())

    def test_unknown_field_has_stable_code_and_pointer(self):
        resource = copy.deepcopy(parsed_examples()["Component"])
        resource["unexpected"] = True
        diagnostics = self.registry.validate_resource(resource, "fixture")
        self.assertEqual(diagnostics[0].code, "XDL-SCHEMA-UNKNOWN-FIELD")
        self.assertEqual(diagnostics[0].pointer, "")

    def test_unsupported_api_version_has_stable_code(self):
        resource = copy.deepcopy(parsed_examples()["Profile"])
        resource["apiVersion"] = "xverse.io/xdl/v1alpha2"
        diagnostics = self.registry.validate_resource(resource, "fixture")
        self.assertIn("XDL-SCHEMA-UNSUPPORTED-API", {item.code for item in diagnostics})

    def test_core_schemas_are_valid_and_offline(self):
        self.assertEqual(len(self.registry.schemas), 7)
        self.assertEqual(self.registry.network_requests, 0)


if __name__ == "__main__":
    unittest.main()
