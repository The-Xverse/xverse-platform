"""Immutable normalization and deterministic JSON output."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any

from .diagnostics import diagnostic_to_data
from .models import (
    Diagnostic, ElementIdentity, FrozenMap, NormalizedResource, ResolvedReference,
    ResourceIdentity, SourceLocation, ValidationResult, freeze,
)
from .semantics import SemanticGraph, iter_extension_containers


def _normalize_one(graph: SemanticGraph, record: Any) -> NormalizedResource:
    """Convert one semantic resource record into its immutable public form."""

    resource = record.document.data
    metadata = resource["metadata"]
    grouped: dict[str, dict[str, Any]] = {}
    for element_id, element in record.elements.items():
        grouped.setdefault(element.collection, {})[element_id] = element.value
    extension_payloads: dict[str, dict[str, Any]] = {}
    for extensions, pointer in iter_extension_containers(record):
        for namespace, payload in extensions.items():
            entry = extension_payloads.setdefault(namespace, {
                "profile": graph.profiles[namespace].uri,
                "payloads": [],
            })
            entry["payloads"].append({
                "pointer": f"{pointer}/{namespace.replace('~', '~0').replace('/', '~1')}",
                "value": payload,
            })
    source_map = {
        pointer: {"source": location.source, "line": location.line, "column": location.column}
        for pointer, location in record.document.source_map.items()
    }
    return NormalizedResource(
        identity=record.identity,
        revision=metadata["version"],
        provenance=freeze(metadata["provenance"]),
        labels=freeze(metadata.get("labels", {})),
        elements=freeze(grouped),
        references=graph.references.get(record.identity, ()),
        extensions=freeze(extension_payloads),
        content=freeze(resource["spec"]),
        source_map=freeze(source_map),
    )


def normalize_graph(graph: SemanticGraph) -> tuple[NormalizedResource, ...]:
    """Normalize all graph resources in deterministic identity order."""

    return tuple(_normalize_one(graph, record) for record in sorted(graph.records, key=lambda item: item.identity))


def _identity_data(value: ResourceIdentity) -> dict[str, str]:
    """Serialize a resource identity to canonical JSON-compatible fields."""

    return {
        "apiVersion": value.api_version,
        "kind": value.kind,
        "namespace": value.namespace,
        "name": value.name,
        "uri": value.uri,
    }


def _reference_data(value: ResolvedReference) -> dict[str, Any]:
    """Serialize a resolved reference and its optional element target."""

    return {
        "pointer": value.pointer,
        "target": _identity_data(value.target),
        "element": value.element.uri if value.element else None,
        "collection": value.collection,
    }


def _resource_data(value: NormalizedResource, include_source_map: bool) -> dict[str, Any]:
    """Serialize one normalized resource with optional authored locations."""

    result = {
        "identity": _identity_data(value.identity),
        "revision": value.revision,
        "provenance": _to_data(value.provenance, include_source_map),
        "labels": _to_data(value.labels, include_source_map),
        "elements": _to_data(value.elements, include_source_map),
        "references": [_reference_data(item) for item in value.references],
        "extensions": _to_data(value.extensions, include_source_map),
        "content": _to_data(value.content, include_source_map),
    }
    if include_source_map:
        result["sourceMap"] = _to_data(value.source_map, include_source_map)
    return result


def _to_data(value: Any, include_source_map: bool = False) -> Any:
    """Recursively convert public immutable model values to JSON-compatible data."""

    if isinstance(value, ValidationResult):
        return {
            "valid": value.is_valid,
            "diagnostics": [diagnostic_to_data(item) for item in value.diagnostics],
            "readiness": _to_data(value.readiness, include_source_map),
            "resources": [_resource_data(item, include_source_map) for item in value.resources],
        }
    if isinstance(value, NormalizedResource):
        return _resource_data(value, include_source_map)
    if isinstance(value, Diagnostic):
        return diagnostic_to_data(value)
    if isinstance(value, ResourceIdentity):
        return _identity_data(value)
    if isinstance(value, ElementIdentity):
        return value.uri
    if isinstance(value, ResolvedReference):
        return _reference_data(value)
    if isinstance(value, SourceLocation):
        return {"source": value.source, "line": value.line, "column": value.column}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _to_data(child, include_source_map) for key, child in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_to_data(child, include_source_map) for child in value]
    return value


def canonical_json(value: Any, *, include_source_map: bool = False) -> str:
    """Return stable compact JSON terminated by one newline.

    @param value A supported model value or sequence of normalized resources.
    @param include_source_map Include authored source positions when true.
    @return Deterministic UTF-8-safe JSON text.
    @raises ValueError If a value contains a non-finite JSON number.
    """

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        data = {"resources": [_to_data(item, include_source_map) for item in value]}
    else:
        data = _to_data(value, include_source_map)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
