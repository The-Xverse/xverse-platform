from __future__ import annotations

import json
import unittest

from xverse_xdl import canonical_json, validate_sources
from xverse_xdl.loader import SourceInput
from xverse_xdl.models import FrozenMap
from tests.helpers import EXAMPLE_PATHS, PROFILE_SCHEMA


class NormalizeTests(unittest.TestCase):
    def test_approved_examples_normalize_immutably(self):
        result = __import__("xverse_xdl").validate_files(EXAMPLE_PATHS, profile_schema_paths=(PROFILE_SCHEMA,))
        self.assertTrue(result.is_valid, result.diagnostics)
        self.assertEqual(len(result.resources), 5)
        self.assertIsInstance(result.resources[0].content, FrozenMap)
        with self.assertRaises(TypeError):
            result.resources[0].content["new"] = "value"

    def test_equivalent_yaml_and_json_have_same_semantic_json(self):
        data = {
            "apiVersion": "xverse.io/xdl/v1alpha1",
            "kind": "Profile",
            "metadata": {"namespace": "org.example", "name": "p", "version": "0.1.0",
                         "provenance": {"source": "test", "revision": "1", "maturity": "prototype"}},
            "spec": {"extensionNamespace": "org.example.p", "compatibleApiVersions": ["xverse.io/xdl/v1alpha1"],
                     "schemaRef": "https://example.invalid/p.json", "documentationRef": "https://example.invalid/p/",
                     "conflictPolicy": "reject"},
        }
        yaml_text = """apiVersion: xverse.io/xdl/v1alpha1
kind: Profile
metadata:
  version: 0.1.0
  name: p
  namespace: org.example
  provenance: {maturity: prototype, revision: '1', source: test}
spec:
  conflictPolicy: reject
  documentationRef: https://example.invalid/p/
  schemaRef: https://example.invalid/p.json
  compatibleApiVersions: [xverse.io/xdl/v1alpha1]
  extensionNamespace: org.example.p
"""
        yaml_result = validate_sources((SourceInput("p.yaml", yaml_text.encode()),))
        json_result = validate_sources((SourceInput("p.json", json.dumps(data).encode()),))
        self.assertTrue(yaml_result.is_valid, yaml_result.diagnostics)
        self.assertEqual(canonical_json(yaml_result.resources), canonical_json(json_result.resources))

    def test_no_partial_normalization_after_schema_error(self):
        valid = b'{"apiVersion":"xverse.io/xdl/v1alpha1","kind":"Profile","metadata":{}}'
        result = validate_sources((SourceInput("bad.json", valid),))
        self.assertFalse(result.is_valid)
        self.assertEqual(result.resources, ())

    def test_public_validate_sources_accepts_name_byte_pairs(self):
        resource = b'{"apiVersion":"xverse.io/xdl/v1alpha1","kind":"Profile","metadata":{"namespace":"org.example","name":"p","version":"0.1.0","provenance":{"source":"test","revision":"1","maturity":"prototype"}},"spec":{"extensionNamespace":"org.example.p","compatibleApiVersions":["xverse.io/xdl/v1alpha1"],"schemaRef":"https://example.invalid/p.json","documentationRef":"https://example.invalid/p/","conflictPolicy":"reject"}}'
        result = validate_sources((("p.json", resource),))
        self.assertTrue(result.is_valid, result.diagnostics)

    def test_frozen_mapping_storage_cannot_be_mutated(self):
        result = __import__("xverse_xdl").validate_files(EXAMPLE_PATHS, profile_schema_paths=(PROFILE_SCHEMA,))
        with self.assertRaises(TypeError):
            result.resources[0].content._index["new"] = "value"


if __name__ == "__main__":
    unittest.main()
