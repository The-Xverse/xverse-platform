from __future__ import annotations

import copy
import unittest

from xverse_xdl.validate import validate_mappings
from tests.helpers import PROFILE_SCHEMA, parsed_examples


class SemanticTests(unittest.TestCase):
    def validate(self, resources, with_profile=True):
        schemas = (PROFILE_SCHEMA,) if with_profile else ()
        return validate_mappings(resources, profile_schema_paths=schemas)

    def test_approved_graph_is_valid_and_statically_ready(self):
        result = self.validate(tuple(parsed_examples().values()))
        self.assertTrue(result.is_valid, result.diagnostics)
        self.assertEqual(dict(result.readiness).popitem()[1], "Ready")

    def test_duplicate_resource_identity_is_rejected(self):
        examples = parsed_examples()
        result = self.validate((*examples.values(), copy.deepcopy(examples["Profile"])))
        self.assertIn("XDL-REFERENCE-DUPLICATE-RESOURCE", {item.code for item in result.diagnostics})

    def test_cross_collection_element_collision_is_rejected(self):
        examples = parsed_examples()
        examples["System"]["spec"]["timeDomains"][0]["id"] = "producer-node"
        result = self.validate(tuple(examples.values()))
        self.assertIn("XDL-REFERENCE-DUPLICATE-ELEMENT", {item.code for item in result.diagnostics})

    def test_unresolved_resource_reference_is_rejected(self):
        examples = parsed_examples()
        examples["Scenario"]["spec"]["systemRef"]["name"] = "missing"
        result = self.validate(tuple(examples.values()))
        self.assertIn("XDL-REFERENCE-UNRESOLVED-RESOURCE", {item.code for item in result.diagnostics})

    def test_profile_schema_is_required_for_used_extension(self):
        result = self.validate(tuple(parsed_examples().values()), with_profile=False)
        self.assertIn("XDL-SEMANTIC-PROFILE-SCHEMA-MISSING", {item.code for item in result.diagnostics})

    def test_invalid_extension_payload_is_rejected(self):
        examples = parsed_examples()
        examples["Component"]["extensions"]["org.xverse.examples.measurement"]["quantitySystem"] = "wrong"
        result = self.validate(tuple(examples.values()))
        self.assertIn("XDL-SEMANTIC-EXTENSION-SCHEMA", {item.code for item in result.diagnostics})

    def test_physical_binding_requires_external_asset(self):
        examples = parsed_examples()
        examples["Deployment"]["spec"]["bindings"][0]["realizationClass"] = "physical"
        result = self.validate(tuple(examples.values()))
        self.assertIn("XDL-SEMANTIC-PHYSICAL-ASSET", {item.code for item in result.diagnostics})


if __name__ == "__main__":
    unittest.main()
