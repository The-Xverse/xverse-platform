#!/usr/bin/env python3
"""Offline acceptance checks for the proposed M2 XDL v1alpha1 package.

This bounded utility verifies the specification artifacts and examples. It is deliberately not the
production XDL loader/validator: it has no public API, registry, import, conversion, or runtime logic.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "xdl" / "schemas" / "v1alpha1"
EXAMPLE_DIR = ROOT / "xdl" / "examples" / "v1alpha1"
API_VERSION = "xverse.io/xdl/v1alpha1"
KINDS = {"System", "Component", "Deployment", "Scenario", "Profile"}
EXPECTED = {kind.lower(): kind for kind in KINDS}
ID_COLLECTIONS = {
    "nodes", "componentInstances", "devices", "sensors", "actuators", "interfaces",
    "endpoints", "flows", "networks", "links", "protocols", "models", "parameters",
    "timeDomains", "targets", "artifacts", "resources", "simulators", "bindings",
    "networkBindings", "timeMappings", "steps", "faults", "observers", "metrics",
    "artifactRequirements", "resourceRequirements",
}


class ValidationError(Exception):
    """Report a documentary M2 schema, semantic, or artifact failure."""

    pass


class UniqueKeyLoader(yaml.SafeLoader):
    """PyYAML loader configured to reject duplicate mapping keys."""

    pass


def construct_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    """Construct one YAML mapping with string-only unique keys."""

    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ValidationError(f"YAML mapping key must be a string at line {key_node.start_mark.line + 1}")
        if key in mapping:
            raise ValidationError(f"duplicate YAML key {key!r} at line {key_node.start_mark.line + 1}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load one JSON-compatible YAML example with duplicate-key protection."""

    with path.open(encoding="utf-8") as stream:
        value = yaml.load(stream, Loader=UniqueKeyLoader)
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: root must be a mapping")
    json.dumps(value, allow_nan=False)
    return value


def pointer_get(value: Any, fragment: str) -> Any:
    """Resolve a local RFC 6901 JSON Pointer schema fragment."""

    if fragment in ("", "#"):
        return value
    if not fragment.startswith("#/"):
        raise ValidationError(f"unsupported schema fragment {fragment}")
    current = value
    for raw in fragment[2:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        current = current[token]
    return current


class SchemaSet:
    """Small offline schema interpreter used only for M2 documentary acceptance."""

    def __init__(self) -> None:
        """Load the exact planned schemas and verify every local reference."""

        self.by_name: dict[str, dict[str, Any]] = {}
        self.by_id: dict[str, tuple[str, dict[str, Any]]] = {}
        for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
            with path.open(encoding="utf-8") as stream:
                schema = json.load(stream)
            if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                raise ValidationError(f"{path}: wrong or missing Draft 2020-12 declaration")
            schema_id = schema.get("$id")
            if not isinstance(schema_id, str) or schema_id in self.by_id:
                raise ValidationError(f"{path}: missing or duplicate $id")
            self.by_name[path.name] = schema
            self.by_id[schema_id] = (path.name, schema)
        if set(self.by_name) != {
            "common.schema.json", "component.schema.json", "deployment.schema.json",
            "profile.schema.json", "scenario.schema.json", "system.schema.json", "xdl.schema.json",
        }:
            raise ValidationError("schema file set differs from the M2 plan")
        for name, schema in self.by_name.items():
            self._check_refs(schema, name)

    def resolve(self, ref: str, base_name: str) -> tuple[Any, str]:
        """Resolve a schema reference within the explicitly loaded local set."""

        location, marker, fragment = ref.partition("#")
        target_name = base_name
        if location:
            if location in self.by_id:
                target_name = self.by_id[location][0]
            else:
                target_name = Path(location).name
        if target_name not in self.by_name:
            raise ValidationError(f"{base_name}: unresolved schema reference {ref}")
        target = self.by_name[target_name]
        return pointer_get(target, f"#{fragment}" if marker else ""), target_name

    def _check_refs(self, value: Any, base_name: str) -> None:
        """Walk a schema and fail on any unresolved reference."""

        if isinstance(value, dict):
            if "$ref" in value:
                self.resolve(value["$ref"], base_name)
            for child in value.values():
                self._check_refs(child, base_name)
        elif isinstance(value, list):
            for child in value:
                self._check_refs(child, base_name)

    def validate(self, instance: Any, schema: dict[str, Any], base_name: str, path: str = "") -> None:
        """Apply the bounded subset of Draft 2020-12 needed by M2 examples."""

        if "$ref" in schema:
            target, target_name = self.resolve(schema["$ref"], base_name)
            self.validate(instance, target, target_name, path)
            return
        if "oneOf" in schema:
            matches = 0
            for option in schema["oneOf"]:
                try:
                    self.validate(instance, option, base_name, path)
                    matches += 1
                except ValidationError:
                    pass
            if matches != 1:
                raise ValidationError(f"{path or '/'}: expected one matching schema, found {matches}")
            return
        if "anyOf" in schema:
            matches = 0
            for option in schema["anyOf"]:
                try:
                    self.validate(instance, option, base_name, path)
                    matches += 1
                except ValidationError:
                    pass
            if matches == 0:
                raise ValidationError(f"{path or '/'}: expected at least one matching schema")
        if "const" in schema and instance != schema["const"]:
            raise ValidationError(f"{path or '/'}: expected constant {schema['const']!r}")
        if "enum" in schema and instance not in schema["enum"]:
            raise ValidationError(f"{path or '/'}: value {instance!r} is not in enum")
        types = schema.get("type")
        if types:
            allowed = types if isinstance(types, list) else [types]
            if not any(self._is_type(instance, item) for item in allowed):
                raise ValidationError(f"{path or '/'}: expected type {types}, got {type(instance).__name__}")
        if isinstance(instance, dict):
            required = schema.get("required", [])
            missing = [key for key in required if key not in instance]
            if missing:
                raise ValidationError(f"{path or '/'}: missing required fields {missing}")
            if len(instance) < schema.get("minProperties", 0):
                raise ValidationError(f"{path or '/'}: too few properties")
            properties = schema.get("properties", {})
            for key, child in instance.items():
                child_path = f"{path}/{key}"
                if key in properties:
                    self.validate(child, properties[key], base_name, child_path)
                elif schema.get("additionalProperties") is False:
                    raise ValidationError(f"{child_path}: unknown field")
                elif isinstance(schema.get("additionalProperties"), dict):
                    self.validate(child, schema["additionalProperties"], base_name, child_path)
            if "propertyNames" in schema:
                for key in instance:
                    self.validate(key, schema["propertyNames"], base_name, f"{path}/<key>")
        elif isinstance(instance, list):
            if len(instance) < schema.get("minItems", 0):
                raise ValidationError(f"{path or '/'}: too few items")
            if schema.get("uniqueItems"):
                values = [json.dumps(item, sort_keys=True) for item in instance]
                if len(values) != len(set(values)):
                    raise ValidationError(f"{path or '/'}: duplicate array item")
            if "items" in schema:
                for index, child in enumerate(instance):
                    self.validate(child, schema["items"], base_name, f"{path}/{index}")
        elif isinstance(instance, str):
            if len(instance) < schema.get("minLength", 0) or len(instance) > schema.get("maxLength", 10**9):
                raise ValidationError(f"{path or '/'}: string length constraint failed")
            if "pattern" in schema and re.fullmatch(schema["pattern"], instance) is None:
                raise ValidationError(f"{path or '/'}: string does not match {schema['pattern']}")
        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if "minimum" in schema and instance < schema["minimum"]:
                raise ValidationError(f"{path or '/'}: value is below minimum")

    @staticmethod
    def _is_type(value: Any, expected: str) -> bool:
        """Return whether a Python value matches a JSON Schema primitive type."""

        return {
            "object": isinstance(value, dict),
            "array": isinstance(value, list),
            "string": isinstance(value, str),
            "number": isinstance(value, (int, float)) and not isinstance(value, bool),
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "boolean": isinstance(value, bool),
            "null": value is None,
        }.get(expected, False)


def identity(resource: dict[str, Any]) -> tuple[str, str, str, str]:
    """Return the four-part logical identity of a resource mapping."""

    metadata = resource.get("metadata", {})
    return (
        resource.get("apiVersion", ""), resource.get("kind", ""),
        metadata.get("namespace", ""), metadata.get("name", ""),
    )


def walk(value: Any):
    """Yield a JSON-like value and all recursively nested children."""

    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def element_ids(resource: dict[str, Any]) -> set[str]:
    """Collect declared element IDs from known XDL specification collections."""

    result: set[str] = set()
    for key, value in resource.get("spec", {}).items():
        if key in ID_COLLECTIONS and isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and isinstance(item.get("id"), str):
                    result.add(item["id"])
    return result


def semantic_validate(resource: dict[str, Any], resources: dict[tuple[str, str, str, str], dict[str, Any]], profiles: set[str]) -> None:
    """Apply the selected cross-resource semantic checks required for M2 evidence."""

    spec = resource["spec"]
    for collection, values in spec.items():
        if collection in ID_COLLECTIONS and isinstance(values, list):
            ids = [item.get("id") for item in values if isinstance(item, dict) and "id" in item]
            if len(ids) != len(set(ids)):
                raise ValidationError(f"duplicate element id in {collection}")

    for value in walk(resource):
        if not isinstance(value, dict):
            continue
        required_ref = {"apiVersion", "kind", "namespace", "name"}
        if required_ref.issubset(value):
            ref_key = (value["apiVersion"], value["kind"], value["namespace"], value["name"])
            target = resources.get(ref_key)
            if target is None:
                raise ValidationError(f"unresolved resource reference {ref_key}")
            if "element" in value and value["element"] not in element_ids(target):
                raise ValidationError(f"unresolved element reference {value['element']!r} in {ref_key}")

    for value in walk(resource):
        if isinstance(value, dict) and "extensions" in value:
            for namespace in value["extensions"]:
                if namespace not in profiles:
                    raise ValidationError(f"undeclared extension namespace {namespace}")

    kind = resource["kind"]
    if kind in {"System", "Component"}:
        prohibited = {"targets", "targetClass", "artifactIds", "externalAssetRef", "secretRefs", "runtime", "host", "address", "credentials"}
        for value in walk(spec):
            if isinstance(value, dict) and prohibited.intersection(value):
                raise ValidationError(f"realization field in logical {kind}: {sorted(prohibited.intersection(value))}")
    if kind == "Component":
        interfaces = {item["id"] for item in spec.get("interfaces", [])}
        valid_owners = {resource["metadata"]["name"]}
        for endpoint in spec.get("endpoints", []):
            if endpoint["interfaceId"] not in interfaces or endpoint["ownerId"] not in valid_owners:
                raise ValidationError(f"component endpoint {endpoint['id']} has unresolved owner or interface")
    if kind == "System":
        collections = {key: {item["id"] for item in value if isinstance(item, dict) and "id" in item}
                       for key, value in spec.items() if isinstance(value, list)}
        endpoint_by_id = {item["id"]: item for item in spec.get("endpoints", [])}
        for endpoint in spec.get("endpoints", []):
            if endpoint["interfaceId"] not in collections.get("interfaces", set()):
                raise ValidationError(f"endpoint {endpoint['id']} has unresolved interface")
            owners = set().union(*(collections.get(name, set()) for name in ("nodes", "componentInstances", "devices")))
            if endpoint["ownerId"] not in owners:
                raise ValidationError(f"endpoint {endpoint['id']} has unresolved owner")
        endpoints = collections.get("endpoints", set())
        for flow in spec.get("flows", []):
            refs = [flow["sourceEndpointId"], *flow["destinationEndpointIds"]]
            if any(item not in endpoints for item in refs):
                raise ValidationError(f"flow {flow['id']} has unresolved endpoint")
            if endpoint_by_id[flow["sourceEndpointId"]]["direction"] not in {"output", "bidirectional"}:
                raise ValidationError(f"flow {flow['id']} source direction is incompatible")
            if any(endpoint_by_id[item]["direction"] not in {"input", "bidirectional"}
                   for item in flow["destinationEndpointIds"]):
                raise ValidationError(f"flow {flow['id']} destination direction is incompatible")
            if flow["interfaceId"] not in collections.get("interfaces", set()):
                raise ValidationError(f"flow {flow['id']} has unresolved interface")
            if "networkId" in flow and flow["networkId"] not in collections.get("networks", set()):
                raise ValidationError(f"flow {flow['id']} has unresolved network")
            if "timeDomainId" in flow and flow["timeDomainId"] not in collections.get("timeDomains", set()):
                raise ValidationError(f"flow {flow['id']} has unresolved time domain")
        for link in spec.get("links", []):
            if link["networkId"] not in collections.get("networks", set()):
                raise ValidationError(f"link {link['id']} has unresolved network")
            if any(item not in endpoints for item in link["participantEndpointIds"]):
                raise ValidationError(f"link {link['id']} has unresolved endpoint")
    if kind == "Deployment":
        targets = {item["id"]: item for item in spec["targets"]}
        artifacts = {item["id"] for item in spec.get("artifacts", [])}
        available_resources = {item["id"] for item in spec.get("resources", [])}
        for target in targets.values():
            if any(item not in available_resources for item in target.get("offeredResourceIds", [])):
                raise ValidationError(f"target {target['id']} has unresolved offered resource")
        for binding in spec["bindings"]:
            target = targets.get(binding["targetId"])
            if target is None:
                raise ValidationError(f"binding {binding['id']} has unresolved target")
            if any(item not in artifacts for item in binding.get("artifactIds", [])):
                raise ValidationError(f"binding {binding['id']} has unresolved artifact")
            if any(item not in available_resources for item in binding.get("resourceIds", [])):
                raise ValidationError(f"binding {binding['id']} has unresolved resource")
            if binding["realizationClass"] == "physical" and not target.get("externalAssetRef"):
                raise ValidationError(f"physical binding {binding['id']} lacks external asset reference")
        if not spec["readiness"].get("requiredConditions"):
            raise ValidationError("deployment readiness has no required conditions")
    if kind == "Scenario":
        observers = {item["id"] for item in spec["observers"]}
        system_ref = spec["systemRef"]
        system = resources[(system_ref["apiVersion"], system_ref["kind"], system_ref["namespace"], system_ref["name"])]
        time_domains = {item["id"] for item in system["spec"].get("timeDomains", [])}
        for timed in [*spec["steps"], *spec["observers"]]:
            if timed["timeDomainId"] not in time_domains:
                raise ValidationError(f"{timed['id']} has unresolved time domain")
        for metric in spec["metrics"]:
            if any(item not in observers for item in metric["observerIds"]):
                raise ValidationError(f"metric {metric['id']} has unresolved observer")


def validate_resource(resource: dict[str, Any], schemas: SchemaSet, resources: dict, profiles: set[str]) -> None:
    """Validate one example against its kind schema and selected semantic rules."""

    kind = resource.get("kind")
    if kind not in KINDS:
        raise ValidationError(f"unsupported kind {kind!r}")
    schemas.validate(resource, schemas.by_name[f"{kind.lower()}.schema.json"], f"{kind.lower()}.schema.json")
    semantic_validate(resource, resources, profiles)


def expect_failure(label: str, resource: dict[str, Any], schemas: SchemaSet, resources: dict, profiles: set[str]) -> None:
    """Require a deliberately malformed M2 resource to fail validation."""

    try:
        validate_resource(resource, schemas, resources, profiles)
    except (ValidationError, KeyError, TypeError, ValueError):
        return
    raise ValidationError(f"negative self-test unexpectedly passed: {label}")


def main() -> int:
    """Validate M2 schemas, examples, negative cases, artifacts, and local links."""

    schemas = SchemaSet()
    examples: dict[str, dict[str, Any]] = {}
    for path in sorted(EXAMPLE_DIR.glob("*.xdl.yaml")):
        resource = load_yaml(path)
        expected_kind = EXPECTED[path.name.removesuffix(".xdl.yaml")]
        if resource.get("apiVersion") != API_VERSION or resource.get("kind") != expected_kind:
            raise ValidationError(f"{path}: API version or kind does not match filename")
        examples[expected_kind] = resource
    if set(examples) != KINDS:
        raise ValidationError("example set does not cover all five kinds")

    resources = {identity(resource): resource for resource in examples.values()}
    profiles = {resource["spec"]["extensionNamespace"] for resource in examples.values() if resource["kind"] == "Profile"}
    for resource in examples.values():
        validate_resource(resource, schemas, resources, profiles)
        schemas.validate(resource, schemas.by_name["xdl.schema.json"], "xdl.schema.json")

    negative: list[tuple[str, dict[str, Any]]] = []
    unknown = copy.deepcopy(examples["Component"])
    unknown["unexpected"] = True
    negative.append(("unknown core field", unknown))
    duplicate = copy.deepcopy(examples["System"])
    duplicate["spec"]["nodes"].append(copy.deepcopy(duplicate["spec"]["nodes"][0]))
    negative.append(("duplicate identifier", duplicate))
    unresolved = copy.deepcopy(examples["Scenario"])
    unresolved["spec"]["systemRef"]["name"] = "missing-system"
    negative.append(("unresolved reference", unresolved))
    extension = copy.deepcopy(examples["Component"])
    extension["extensions"] = {"org.example.undeclared": {"mode": "test"}}
    negative.append(("undeclared extension", extension))
    realization = copy.deepcopy(examples["System"])
    realization["spec"]["nodes"][0]["runtime"] = "container"
    negative.append(("realization leakage", realization))
    readiness = copy.deepcopy(examples["Deployment"])
    del readiness["spec"]["readiness"]
    negative.append(("incomplete readiness", readiness))
    api_version = copy.deepcopy(examples["Profile"])
    api_version["apiVersion"] = "xverse.io/xdl/v1alpha2"
    negative.append(("unsupported API version", api_version))
    namespace = copy.deepcopy(examples["Profile"])
    namespace["spec"]["extensionNamespace"] = "invalid"
    negative.append(("malformed Profile namespace", namespace))
    for label, resource in negative:
        expect_failure(label, resource, schemas, resources, profiles)

    required_paths = [
        *[ROOT / "specs/003-xdl-core" / name for name in [
            "spec.md", "clarifications.md", "research.md", "data-model.md", "plan.md",
            "quickstart.md", "tasks.md", "analysis.md", "validation.md",
            "checklists/requirements.md", "checklists/acceptance.md",
        ]],
        ROOT / "xdl/specification/XDL_CORE_V0_1.md",
        ROOT / "xdl/specification/RESOURCE_MODEL.md",
        ROOT / "xdl/specification/VALIDATION.md",
        ROOT / "xdl/specification/VERSIONING.md",
        ROOT / "xdl/metamodel/NORMALIZED_MODEL.md",
        *[ROOT / f"docs/adr/ADR-{number:04d}-{name}.md" for number, name in [
            (9, "xdl-resource-model"), (10, "xdl-identity-and-versioning"),
            (11, "xdl-serialization-and-schema"), (12, "xdl-extensions-and-standards"),
        ]],
        ROOT / "docs/reviews/003-xdl-core-architecture-review.md",
    ]
    for path in required_paths:
        if not path.is_file():
            raise ValidationError(f"missing required artifact {path.relative_to(ROOT)}")
    feature_files = sorted(set(list((ROOT / "specs/003-xdl-core").rglob("*.md")) + required_paths))
    unresolved_markers = ("[FEATURE NAME]", "[DATE]", "$ARGUMENTS", "NEEDS CLARIFICATION", "TODO", "TBD")
    for path in feature_files:
        text = path.read_text(encoding="utf-8")
        for marker in unresolved_markers:
            if marker in text:
                raise ValidationError(f"{path.relative_to(ROOT)}: unresolved marker {marker}")
        for link in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
            target = link.split("#", 1)[0].strip("<>")
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
                continue
            if not (path.parent / target).resolve().exists():
                raise ValidationError(f"{path.relative_to(ROOT)}: unresolved local link {link}")

    print(f"PASS: {len(schemas.by_name)} Draft 2020-12 schemas parsed and references resolved")
    print(f"PASS: {len(examples)} YAML examples passed structural and selected semantic checks")
    print(f"PASS: {len(negative)} negative self-tests failed as required")
    print("PASS: required M2 artifacts, local links, and template-marker checks passed")
    print("Maturity: approved v1alpha1 specification/schema; no loader, runtime, or compatibility claim")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, json.JSONDecodeError, yaml.YAMLError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
