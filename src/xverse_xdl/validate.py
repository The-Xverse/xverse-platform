"""Public staged validation orchestration."""

from __future__ import annotations

import copy
from pathlib import Path
from collections.abc import Sequence
from typing import Any

from .diagnostics import sorted_diagnostics
from .loader import ParsedDocument, SourceInput, load_file_sources, load_sources as parse_sources
from .models import FrozenMap, LoadLimits, SourceLocation, ValidationResult
from .normalize import normalize_graph
from .schema import CoreSchemaRegistry, load_profile_schemas
from .semantics import validate_semantics


def _validate_documents(
    documents: tuple[ParsedDocument, ...],
    *,
    profile_schema_paths: tuple[str | Path, ...] = (),
    limits: LoadLimits = LoadLimits(),
) -> ValidationResult:
    """Run schema, profile, semantic, and normalization stages on parsed documents."""

    registry = CoreSchemaRegistry()
    schema_diagnostics = sorted_diagnostics(
        item for document in documents for item in registry.validate_document(document)
    )
    if schema_diagnostics:
        return ValidationResult(schema_diagnostics)
    profile_catalog, profile_diagnostics = load_profile_schemas(profile_schema_paths, limits=limits)
    if profile_diagnostics:
        return ValidationResult(profile_diagnostics)
    graph, semantic_diagnostics = validate_semantics(documents, profile_catalog)
    if graph is None:
        return ValidationResult(semantic_diagnostics)
    resources = normalize_graph(graph)
    readiness = FrozenMap({key: value.value for key, value in graph.readiness.items()})
    return ValidationResult(sorted_diagnostics(semantic_diagnostics), resources, readiness)


def validate_sources(
    sources: Sequence[SourceInput | tuple[str, bytes]],
    *,
    profile_schema_paths: tuple[str | Path, ...] = (),
    limits: LoadLimits = LoadLimits(),
) -> ValidationResult:
    """Validate named byte sources without filesystem discovery or network access.

    @param sources Source objects or ``(name, bytes)`` pairs.
    @param profile_schema_paths Explicit local profile schema paths.
    @param limits Bounded loading limits.
    @return Staged diagnostics and immutable resources when normalization is possible.
    """

    normalized_sources = tuple(
        value if isinstance(value, SourceInput) else SourceInput(str(value[0]), bytes(value[1]))
        for value in sources
    )
    documents, diagnostics = parse_sources(normalized_sources, limits=limits)
    if diagnostics:
        return ValidationResult(diagnostics)
    return _validate_documents(documents, profile_schema_paths=profile_schema_paths, limits=limits)


def validate_files(
    paths: Sequence[str | Path],
    *,
    profile_schema_paths: tuple[str | Path, ...] = (),
    limits: LoadLimits = LoadLimits(),
) -> ValidationResult:
    """Read and validate explicitly named local XDL files."""

    documents, diagnostics = load_file_sources(paths, limits=limits)
    if diagnostics:
        return ValidationResult(diagnostics)
    return _validate_documents(documents, profile_schema_paths=profile_schema_paths, limits=limits)


def validate_mappings(
    resources: tuple[dict[str, Any], ...],
    *,
    profile_schema_paths: tuple[str | Path, ...] = (),
) -> ValidationResult:
    """Validate deep-copied in-memory resource mappings."""

    documents: list[ParsedDocument] = []
    for index, resource in enumerate(resources):
        copied = copy.deepcopy(resource)
        name = f"mapping-{index:04d}.json"
        documents.append(ParsedDocument(name, copied, {"": SourceLocation(name)}, "json"))
    return _validate_documents(tuple(documents), profile_schema_paths=profile_schema_paths)
