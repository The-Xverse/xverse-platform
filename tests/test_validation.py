from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from xverse_xdl.loader import SourceInput
from xverse_xdl.models import LoadLimits
from xverse_xdl.validate import validate_mappings, validate_sources
from tests.helpers import PROFILE_SCHEMA, parsed_examples


class NegativeValidationTests(unittest.TestCase):
    def graph(self):
        return parsed_examples()

    def validate(self, examples):
        return validate_mappings(tuple(examples.values()), profile_schema_paths=(PROFILE_SCHEMA,))

    def assert_result_code(self, result, code):
        self.assertFalse(result.is_valid)
        self.assertIn(code, {item.code for item in result.diagnostics})

    def test_empty_input(self):
        self.assert_result_code(validate_sources((SourceInput("empty.yaml", b""),)), "XDL-PARSE-EMPTY")

    def test_invalid_utf8(self):
        self.assert_result_code(validate_sources((SourceInput("bad.yaml", b"\xff"),)), "XDL-PARSE-UTF8")

    def test_non_mapping_root(self):
        self.assert_result_code(validate_sources((SourceInput("array.json", b"[]"),)), "XDL-PARSE-ROOT")

    def test_resource_count_limit(self):
        sources = (SourceInput("a.yaml", b"a: 1"), SourceInput("b.yaml", b"b: 2"))
        result = validate_sources(sources, limits=LoadLimits(max_resources=1))
        self.assert_result_code(result, "XDL-PARSE-MAX-RESOURCES")

    def test_unsupported_kind(self):
        examples = self.graph()
        examples["Profile"]["kind"] = "Bundle"
        self.assert_result_code(self.validate(examples), "XDL-SCHEMA-UNSUPPORTED-KIND")

    def test_missing_required_field(self):
        examples = self.graph()
        del examples["Component"]["spec"]["capabilities"]
        self.assert_result_code(self.validate(examples), "XDL-SCHEMA-REQUIRED")

    def test_unresolved_element(self):
        examples = self.graph()
        examples["Scenario"]["spec"]["steps"][0]["targetRef"]["element"] = "missing"
        self.assert_result_code(self.validate(examples), "XDL-REFERENCE-UNRESOLVED-ELEMENT")

    def test_system_endpoint_owner(self):
        examples = self.graph()
        examples["System"]["spec"]["endpoints"][0]["ownerId"] = "missing"
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-ENDPOINT-OWNER")

    def test_flow_direction(self):
        examples = self.graph()
        examples["System"]["spec"]["endpoints"][0]["direction"] = "input"
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-FLOW-DIRECTION")

    def test_flow_network(self):
        examples = self.graph()
        examples["System"]["spec"]["flows"][0]["networkId"] = "missing"
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-NETWORK")

    def test_binding_target(self):
        examples = self.graph()
        examples["Deployment"]["spec"]["bindings"][0]["targetId"] = "missing"
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-TARGET")

    def test_scenario_time_domain(self):
        examples = self.graph()
        examples["Scenario"]["spec"]["steps"][0]["timeDomainId"] = "missing"
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-TIME-DOMAIN")

    def test_metric_observer(self):
        examples = self.graph()
        examples["Scenario"]["spec"]["metrics"][0]["observerIds"] = ["missing"]
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-OBSERVER")

    def test_duplicate_profile_namespace(self):
        examples = self.graph()
        duplicate = copy.deepcopy(examples["Profile"])
        duplicate["metadata"]["name"] = "measurement-profile-copy"
        result = validate_mappings((*examples.values(), duplicate), profile_schema_paths=(PROFILE_SCHEMA,))
        self.assert_result_code(result, "XDL-SEMANTIC-DUPLICATE-PROFILE-NAMESPACE")

    def test_invalid_profile_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.json"
            path.write_text('{"$schema":"https://json-schema.org/draft/2020-12/schema","type":42}')
            result = validate_mappings(tuple(self.graph().values()), profile_schema_paths=(path,))
        self.assert_result_code(result, "XDL-POLICY-PROFILE-SCHEMA-INVALID")

    def test_core_schema_failure_precedes_profile_schema_policy_failure(self):
        examples = self.graph()
        del examples["Component"]["spec"]["capabilities"]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.json"
            path.write_text('{"type":42}')
            result = validate_mappings(tuple(examples.values()), profile_schema_paths=(path,))
        self.assert_result_code(result, "XDL-SCHEMA-REQUIRED")
        self.assertNotIn("XDL-POLICY-PROFILE-SCHEMA-INVALID", {item.code for item in result.diagnostics})

    def test_relative_profile_schema_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "relative.json"
            path.write_text('{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"relative.json","type":"object"}')
            result = validate_mappings(tuple(self.graph().values()), profile_schema_paths=(path,))
        self.assert_result_code(result, "XDL-POLICY-PROFILE-SCHEMA-INVALID")

    def test_endpoint_interface_direction(self):
        examples = self.graph()
        examples["Component"]["spec"]["interfaces"][0]["direction"] = "input"
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-ENDPOINT-DIRECTION")

    def test_scenario_target_outside_selected_graph(self):
        examples = self.graph()
        target = examples["Scenario"]["spec"]["steps"][0]["targetRef"]
        target.update({"kind": "Component", "name": "signal-source", "element": "samples-out"})
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-SCENARIO-TARGET")

    def test_multiple_scenario_time_domains_require_mapping(self):
        examples = self.graph()
        examples["System"]["spec"]["timeDomains"].append({
            "id": "observer-time", "clockClass": "logical", "epoch": "scenario-start",
            "rate": "one-unit-per-second", "monotonic": True,
        })
        examples["Scenario"]["spec"]["observers"][0]["timeDomainId"] = "observer-time"
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-TIME-MAPPING")

    def test_every_used_time_domain_pair_requires_mapping(self):
        examples = self.graph()
        examples["System"]["spec"]["timeDomains"].extend([
            {"id": "observer-time", "clockClass": "logical", "epoch": "scenario-start",
             "rate": "one-unit-per-second", "monotonic": True},
            {"id": "fault-time", "clockClass": "logical", "epoch": "scenario-start",
             "rate": "one-unit-per-second", "monotonic": True},
        ])
        examples["Scenario"]["spec"]["observers"][0]["timeDomainId"] = "observer-time"
        second_step = copy.deepcopy(examples["Scenario"]["spec"]["steps"][0])
        second_step["id"] = "second-step"
        second_step["timeDomainId"] = "fault-time"
        examples["Scenario"]["spec"]["steps"].append(second_step)
        examples["Scenario"]["spec"]["timeMappings"] = [{
            "sourceTimeDomainId": "observer-time", "targetTimeDomainId": "fault-time",
            "mapping": "identity", "tolerance": {"value": 1, "unit": "ms"},
        }]
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-TIME-MAPPING")

    def test_component_instance_must_reference_component(self):
        examples = self.graph()
        reference = examples["System"]["spec"]["componentInstances"][0]["componentRef"]
        reference.update({"kind": "System", "name": examples["System"]["metadata"]["name"]})
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-COMPONENT-REFERENCE")

    def test_deployment_network_binding_requires_system_network(self):
        examples = self.graph()
        examples["Deployment"]["spec"]["networkBindings"] = [{
            "id": "network-binding",
            "logicalNetworkRef": {
                "apiVersion": "xverse.io/xdl/v1alpha1", "kind": "System",
                "namespace": "org.xverse.examples", "name": "sample-loop",
                "element": "experiment-time",
            },
            "profileRef": {
                "apiVersion": "xverse.io/xdl/v1alpha1", "kind": "Profile",
                "namespace": "org.xverse.examples", "name": "measurement-profile",
            },
            "limitations": ["illustrative"],
        }]
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-NETWORK-REFERENCE")

    def test_deployment_network_binding_requires_profile(self):
        examples = self.graph()
        examples["Deployment"]["spec"]["networkBindings"] = [{
            "id": "network-binding",
            "logicalNetworkRef": {
                "apiVersion": "xverse.io/xdl/v1alpha1", "kind": "System",
                "namespace": "org.xverse.examples", "name": "sample-loop",
                "element": "logical-network",
            },
            "profileRef": {
                "apiVersion": "xverse.io/xdl/v1alpha1", "kind": "Profile",
                "namespace": "org.xverse.examples", "name": "measurement-profile",
            },
            "limitations": ["illustrative"],
        }]
        profile_ref = examples["Deployment"]["spec"]["networkBindings"][0]["profileRef"]
        profile_ref.update({"kind": "System", "name": examples["System"]["metadata"]["name"]})
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-PROFILE-REFERENCE")

    def test_deployment_target_profile_reference_requires_profile(self):
        examples = self.graph()
        examples["Deployment"]["spec"]["targets"][0]["profileRefs"] = [{
            "apiVersion": "xverse.io/xdl/v1alpha1", "kind": "System",
            "namespace": "org.xverse.examples", "name": "sample-loop",
        }]
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-PROFILE-REFERENCE")

    def test_deployment_time_mapping_requires_time_domain_elements(self):
        examples = self.graph()
        system_ref = {
            "apiVersion": "xverse.io/xdl/v1alpha1", "kind": "System",
            "namespace": "org.xverse.examples", "name": "sample-loop",
        }
        examples["Deployment"]["spec"]["timeMappings"] = [{
            "id": "clock-mapping",
            "sourceTimeDomainRef": {**system_ref, "element": "logical-network"},
            "targetTimeDomainRef": {**system_ref, "element": "experiment-time"},
            "mapping": "identity", "tolerance": {"value": 1, "unit": "ms"},
        }]
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-TIME-DOMAIN-REFERENCE")

    def test_scenario_deployment_must_select_same_system(self):
        examples = self.graph()
        other_system = copy.deepcopy(examples["System"])
        other_system["metadata"]["name"] = "other-system"
        examples["Scenario"]["spec"]["systemRef"]["name"] = "other-system"
        result = validate_mappings((*examples.values(), other_system), profile_schema_paths=(PROFILE_SCHEMA,))
        self.assert_result_code(result, "XDL-SEMANTIC-SCENARIO-DEPLOYMENT-SYSTEM")

    def test_model_ports_must_reference_interfaces(self):
        examples = self.graph()
        examples["System"]["spec"]["models"] = [{
            "id": "illustrative-model", "modelKind": "equation",
            "externalRef": "urn:xverse:example:model", "inputs": ["missing"],
            "outputs": ["sample-stream"], "maturity": "architectural-target",
            "limitations": ["illustrative"],
        }]
        self.assert_result_code(self.validate(examples), "XDL-SEMANTIC-INTERFACE")

    def test_open_parameter_payload_is_not_interpreted_as_core_structure(self):
        examples = self.graph()
        examples["System"]["spec"]["componentInstances"][0]["parameterValues"] = {
            "address": "domain-owned-value",
            "reference-shaped-data": {
                "apiVersion": "external.example/v1", "kind": "ExternalRecord",
                "namespace": "external.example", "name": "not-an-xdl-reference",
            },
            "extensions": {"external-owned-key": {"runtime": "opaque"}},
        }
        result = self.validate(examples)
        self.assertTrue(result.is_valid, result.diagnostics)

    def test_missing_artifact_digest_blocks_static_readiness_but_not_normalization(self):
        examples = self.graph()
        del examples["Deployment"]["spec"]["artifacts"][0]["digest"]
        result = self.validate(examples)
        self.assert_result_code(result, "XDL-BINDING-ARTIFACT-INTEGRITY")
        self.assertEqual(len(result.resources), 5)
        self.assertIn("NotReady", set(result.readiness.values()))


if __name__ == "__main__":
    unittest.main()
