"""Offline Draft 2020-12 schema registries and validation."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource

from .diagnostics import make_diagnostic, pointer_from_path, sorted_diagnostics
from .loader import ParsedDocument
from .models import Diagnostic, LoadLimits, ResourceIdentity, SourceLocation, ValidationGate

API_VERSION = "xverse.io/xdl/v1alpha1"
KINDS = ("Component", "Deployment", "Profile", "Scenario", "System")


def _schema_paths() -> tuple[Any, ...]:
    """Locate packaged core schemas, with a source-tree fallback for development."""

    packaged = files("xverse_xdl").joinpath("schemas", "v1alpha1")
    try:
        candidates = tuple(item for item in packaged.iterdir() if item.name.endswith(".schema.json"))
        if candidates:
            return tuple(sorted(candidates, key=lambda item: item.name))
    except (FileNotFoundError, NotADirectoryError):
        pass
    development = Path(__file__).resolve().parents[2] / "xdl" / "schemas" / "v1alpha1"
    return tuple(sorted(development.glob("*.schema.json")))


def _read_schema(path: Any) -> dict[str, Any]:
    """Read and meta-validate one bundled Draft 2020-12 schema."""

    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise SchemaError("schema root is not an object")
    Draft202012Validator.check_schema(value)
    return value


def _read_bounded_profile_schema(path: Path, limits: LoadLimits) -> dict[str, Any]:
    """Read an explicitly supplied profile schema under loader-equivalent bounds."""

    raw = path.read_bytes()
    if len(raw) > limits.max_bytes_per_file:
        raise SchemaError(f"Profile schema exceeds {limits.max_bytes_per_file} bytes")
    text = raw.decode("utf-8-sig")

    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        """Build a schema object while rejecting duplicate keys."""

        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise SchemaError(f"duplicate Profile schema key {key!r}")
            result[key] = value
        return result

    def constant(value: str) -> None:
        """Reject non-finite JSON constants in profile schemas."""

        raise SchemaError(f"non-finite Profile schema number {value}")

    value = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    nodes = 0

    def check(child: Any, depth: int = 0) -> None:
        """Enforce depth, node-count, and JSON data-model constraints."""

        nonlocal nodes
        if depth > limits.max_depth:
            raise SchemaError(f"Profile schema nesting exceeds {limits.max_depth}")
        nodes += 1
        if nodes > limits.max_nodes:
            raise SchemaError(f"Profile schema node count exceeds {limits.max_nodes}")
        if isinstance(child, dict):
            for key, nested in child.items():
                if not isinstance(key, str):
                    raise SchemaError("Profile schema keys must be strings")
                check(nested, depth + 1)
        elif isinstance(child, list):
            for nested in child:
                check(nested, depth + 1)
        elif isinstance(child, float) and not math.isfinite(child):
            raise SchemaError("Profile schema numbers must be finite")
        elif child is not None and not isinstance(child, (str, bool, int, float)):
            raise SchemaError(f"Profile schema contains unsupported {type(child).__name__}")

    check(value)
    if not isinstance(value, dict):
        raise SchemaError("Profile schema root is not an object")
    Draft202012Validator.check_schema(value)
    return value


class CoreSchemaRegistry:
    """Offline registry for the exact packaged XDL v1alpha1 schema set."""

    def __init__(self) -> None:
        """Load, verify, and register all expected core schemas."""

        self.schemas = {path.name: _read_schema(path) for path in _schema_paths()}
        expected = {"common.schema.json", "component.schema.json", "deployment.schema.json",
                    "profile.schema.json", "scenario.schema.json", "system.schema.json", "xdl.schema.json"}
        if set(self.schemas) != expected:
            raise RuntimeError(f"packaged core schema set differs from expected: {sorted(self.schemas)}")
        resources = [(schema["$id"], Resource.from_contents(schema)) for schema in self.schemas.values()]
        self.registry = Registry().with_resources(resources)
        self.format_checker = FormatChecker()
        self.network_requests = 0

    def validate_document(self, document: ParsedDocument) -> tuple[Diagnostic, ...]:
        """Validate a parsed document while preserving its source map."""

        return self.validate_resource(document.data, document.source_name, document.source_map)

    def validate_resource(
        self,
        resource: dict[str, Any],
        source_name: str,
        source_map: dict[str, SourceLocation] | None = None,
    ) -> tuple[Diagnostic, ...]:
        """Validate one resource against its kind schema with stable diagnostics."""

        source_map = source_map or {"": SourceLocation(source_name)}
        identity = ResourceIdentity.from_mapping(resource)
        api_version = resource.get("apiVersion")
        kind = resource.get("kind")
        if api_version != API_VERSION:
            return (make_diagnostic(
                "XDL-SCHEMA-UNSUPPORTED-API", ValidationGate.SCHEMA,
                f"unsupported apiVersion {api_version!r}", f"Use exactly {API_VERSION}.",
                pointer="/apiVersion", resource=identity,
                location=source_map.get("/apiVersion", SourceLocation(source_name)),
            ),)
        if kind not in KINDS:
            return (make_diagnostic(
                "XDL-SCHEMA-UNSUPPORTED-KIND", ValidationGate.SCHEMA,
                f"unsupported kind {kind!r}", f"Use one of {', '.join(KINDS)}.",
                pointer="/kind", resource=identity,
                location=source_map.get("/kind", SourceLocation(source_name)),
            ),)
        schema = self.schemas[f"{kind.lower()}.schema.json"]
        validator = Draft202012Validator(schema, registry=self.registry, format_checker=self.format_checker)
        diagnostics: list[Diagnostic] = []
        for error in sorted(validator.iter_errors(resource), key=lambda item: (tuple(str(x) for x in item.absolute_path), item.message)):
            pointer = pointer_from_path(error.absolute_path)
            if error.validator == "additionalProperties":
                code = "XDL-SCHEMA-UNKNOWN-FIELD"
            elif error.validator == "required":
                code = "XDL-SCHEMA-REQUIRED"
            elif error.validator == "format":
                code = "XDL-SCHEMA-FORMAT"
            else:
                code = "XDL-SCHEMA-INVALID"
            diagnostics.append(make_diagnostic(
                code, ValidationGate.SCHEMA, error.message,
                "Correct the value to match the XDL v1alpha1 kind schema.",
                pointer=pointer, resource=identity,
                location=source_map.get(pointer, SourceLocation(source_name)),
            ))
        return sorted_diagnostics(diagnostics)


@dataclass(frozen=True)
class ProfileSchemaCatalog:
    """Explicit local profile schemas and their offline reference registry."""

    schemas: dict[str, dict[str, Any]]
    registry: Registry

    def validate(self, schema_id: str, payload: Any) -> tuple[Any, ...]:
        """Return deterministically ordered schema errors for an extension payload."""

        schema = self.schemas[schema_id]
        validator = Draft202012Validator(schema, registry=self.registry, format_checker=FormatChecker())
        return tuple(sorted(validator.iter_errors(payload), key=lambda item: (tuple(str(x) for x in item.absolute_path), item.message)))


def load_profile_schemas(
    paths: tuple[str | Path, ...], *, limits: LoadLimits = LoadLimits(),
) -> tuple[ProfileSchemaCatalog, tuple[Diagnostic, ...]]:
    """Load bounded local profile schemas without discovery or network access."""

    schemas: dict[str, dict[str, Any]] = {}
    diagnostics: list[Diagnostic] = []
    for path in sorted((Path(value) for value in paths), key=lambda item: str(item)):
        try:
            schema = _read_bounded_profile_schema(path, limits)
            schema_id = schema.get("$id")
            if not isinstance(schema_id, str) or not schema_id or not urlsplit(schema_id).scheme:
                raise SchemaError("Profile schema requires an absolute non-empty $id")
            if schema_id in schemas:
                diagnostics.append(make_diagnostic(
                    "XDL-POLICY-DUPLICATE-PROFILE-SCHEMA", ValidationGate.POLICY,
                    f"Profile schema $id {schema_id!r} is supplied more than once",
                    "Supply exactly one local schema for each Profile schemaRef.",
                    location=SourceLocation(str(path)),
                ))
            else:
                schemas[schema_id] = schema
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError, SchemaError) as error:
            diagnostics.append(make_diagnostic(
                "XDL-POLICY-PROFILE-SCHEMA-INVALID", ValidationGate.POLICY, str(error),
                "Provide a readable valid Draft 2020-12 Profile schema with an absolute $id.",
                location=SourceLocation(str(path)),
            ))
    registry = Registry().with_resources(
        (schema_id, Resource.from_contents(schema)) for schema_id, schema in schemas.items()
    )
    return ProfileSchemaCatalog(schemas, registry), sorted_diagnostics(diagnostics)
