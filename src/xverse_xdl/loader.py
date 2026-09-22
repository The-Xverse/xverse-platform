"""Bounded JSON and YAML 1.2 loading with source locations."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.constructor import DuplicateKeyError
from ruamel.yaml.error import YAMLError
from ruamel.yaml.events import (
    AliasEvent, DocumentStartEvent, MappingEndEvent, MappingStartEvent, SequenceEndEvent,
    SequenceStartEvent,
)

from .diagnostics import escape_pointer_token, make_diagnostic, sorted_diagnostics
from .models import Diagnostic, LoadLimits, SourceLocation, ValidationGate


class _DuplicateKey(ValueError):
    """Signal a duplicate JSON object key during pair-preserving decoding."""

    pass


class _NonFinite(ValueError):
    """Signal a non-finite numeric constant outside the JSON data model."""

    pass


class _ShapeError(ValueError):
    """Internal bounded-shape failure carrying a stable code and pointer."""

    def __init__(self, code: str, message: str, pointer: str) -> None:
        """Initialize a shape failure at an RFC 6901 pointer."""

        super().__init__(message)
        self.code = code
        self.pointer = pointer


@dataclass(frozen=True)
class SourceInput:
    """Named immutable input bytes supplied explicitly to the loader."""

    name: str
    data: bytes


@dataclass(frozen=True)
class ParsedDocument:
    """JSON-compatible resource plus format and authored source locations."""

    source_name: str
    data: dict[str, Any]
    source_map: dict[str, SourceLocation]
    source_format: str


def _pairs_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Construct a JSON object while rejecting duplicate member names."""

    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise _DuplicateKey(f"duplicate key {key!r}")
        value[key] = child
    return value


def _reject_constant(value: str) -> None:
    """Reject JSON decoder constants such as NaN and infinity."""

    raise _NonFinite(f"non-finite JSON number {value}")


def _location(value: Any, source: str, key: Any = None, *, sequence: bool = False) -> SourceLocation:
    """Read a ruamel location and fall back to source-only context."""

    try:
        if key is None:
            line, column = value.lc.line, value.lc.col
        elif sequence:
            line, column = value.lc.item(key)
        else:
            line, column = value.lc.value(key)
        return SourceLocation(source, int(line) + 1, int(column) + 1)
    except (AttributeError, KeyError, TypeError, ValueError):
        return SourceLocation(source)


def _convert_json_compatible(
    value: Any,
    *,
    source: str,
    limits: LoadLimits,
    pointer: str = "",
    depth: int = 0,
    stack: set[int] | None = None,
    counter: list[int] | None = None,
    source_map: dict[str, SourceLocation] | None = None,
) -> Any:
    """Convert parsed YAML values into bounded acyclic JSON-compatible data.

    @raises _ShapeError If depth, nodes, keys, cycles, or values violate loader policy.
    """

    stack = stack if stack is not None else set()
    counter = counter if counter is not None else [0]
    source_map = source_map if source_map is not None else {}
    if depth > limits.max_depth:
        raise _ShapeError("XDL-PARSE-MAX-DEPTH", f"nesting exceeds {limits.max_depth}", pointer)
    counter[0] += 1
    if counter[0] > limits.max_nodes:
        raise _ShapeError("XDL-PARSE-MAX-NODES", f"node count exceeds {limits.max_nodes}", pointer)
    source_map.setdefault(pointer, _location(value, source))

    if isinstance(value, Mapping):
        marker = id(value)
        if marker in stack:
            raise _ShapeError("XDL-PARSE-CYCLE", "cyclic YAML aliases are not valid XDL", pointer)
        stack.add(marker)
        result: dict[str, Any] = {}
        try:
            for key, child in value.items():
                if not isinstance(key, str):
                    raise _ShapeError("XDL-PARSE-NON-STRING-KEY", "mapping keys must be strings", pointer)
                child_pointer = f"{pointer}/{escape_pointer_token(key)}"
                source_map[child_pointer] = _location(value, source, key)
                result[key] = _convert_json_compatible(
                    child, source=source, limits=limits, pointer=child_pointer, depth=depth + 1,
                    stack=stack, counter=counter, source_map=source_map,
                )
        finally:
            stack.remove(marker)
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        marker = id(value)
        if marker in stack:
            raise _ShapeError("XDL-PARSE-CYCLE", "cyclic YAML aliases are not valid XDL", pointer)
        stack.add(marker)
        result_list: list[Any] = []
        try:
            for index, child in enumerate(value):
                child_pointer = f"{pointer}/{index}"
                source_map[child_pointer] = _location(value, source, index, sequence=True)
                result_list.append(_convert_json_compatible(
                    child, source=source, limits=limits, pointer=child_pointer, depth=depth + 1,
                    stack=stack, counter=counter, source_map=source_map,
                ))
        finally:
            stack.remove(marker)
        return result_list
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise _ShapeError("XDL-PARSE-NON-FINITE", "numbers must be finite", pointer)
        return value
    raise _ShapeError(
        "XDL-PARSE-NON-JSON-VALUE",
        f"value of type {type(value).__name__} is outside the JSON data model",
        pointer,
    )


def _parse_one(source: SourceInput, limits: LoadLimits) -> tuple[ParsedDocument | None, tuple[Diagnostic, ...]]:
    """Parse one bounded UTF-8 JSON or YAML 1.2 source into a document."""

    location = SourceLocation(source.name)
    if len(source.data) > limits.max_bytes_per_file:
        return None, (make_diagnostic(
            "XDL-PARSE-TOO-LARGE", ValidationGate.PARSE,
            f"input is {len(source.data)} bytes; limit is {limits.max_bytes_per_file}",
            "Reduce the file size or explicitly select a larger bounded limit.", location=location,
        ),)
    try:
        text = source.data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        return None, (make_diagnostic(
            "XDL-PARSE-UTF8", ValidationGate.PARSE, str(error),
            "Encode the resource as valid UTF-8.", location=location,
        ),)
    if not text.strip():
        return None, (make_diagnostic(
            "XDL-PARSE-EMPTY", ValidationGate.PARSE, "input is empty",
            "Provide exactly one XDL resource.", location=location,
        ),)

    suffix = Path(source.name).suffix.lower()
    source_format = "json" if suffix == ".json" or (suffix not in {".yaml", ".yml"} and text.lstrip().startswith(("{", "["))) else "yaml"
    source_map: dict[str, SourceLocation] = {"": location}
    try:
        if source_format == "json":
            raw = json.loads(text, object_pairs_hook=_pairs_object, parse_constant=_reject_constant)
        else:
            event_parser = YAML(typ="base", pure=True)
            event_parser.version = (1, 2)
            active_anchors: list[str | None] = []
            for event in event_parser.parse(text):
                if isinstance(event, DocumentStartEvent) and event.version not in (None, (1, 2)):
                    raise _ShapeError(
                        "XDL-PARSE-YAML-VERSION", f"YAML version {event.version} is not supported", ""
                    )
                if isinstance(event, (MappingStartEvent, SequenceStartEvent)):
                    active_anchors.append(event.anchor)
                elif isinstance(event, AliasEvent) and event.anchor in {item for item in active_anchors if item}:
                    raise _ShapeError("XDL-PARSE-CYCLE", "cyclic YAML aliases are not valid XDL", "")
                elif isinstance(event, (MappingEndEvent, SequenceEndEvent)):
                    active_anchors.pop()
            yaml = YAML(typ="rt", pure=True)
            yaml.version = (1, 2)
            yaml.allow_duplicate_keys = False
            yaml.max_depth = limits.max_depth + 10
            documents = list(yaml.load_all(text))
            if len(documents) != 1:
                return None, (make_diagnostic(
                    "XDL-PARSE-MULTI-DOCUMENT", ValidationGate.PARSE,
                    f"expected one YAML document, found {len(documents)}",
                    "Place each XDL resource in its own file.", location=location,
                ),)
            raw = documents[0]
        converted = _convert_json_compatible(
            raw, source=source.name, limits=limits, source_map=source_map,
        )
        if not isinstance(converted, dict):
            raise _ShapeError("XDL-PARSE-ROOT", "resource root must be a mapping", "")
        return ParsedDocument(source.name, converted, source_map, source_format), ()
    except _DuplicateKey as error:
        code, message = "XDL-PARSE-DUPLICATE-KEY", str(error)
    except DuplicateKeyError as error:
        code, message = "XDL-PARSE-DUPLICATE-KEY", str(error).splitlines()[0]
    except _NonFinite as error:
        code, message = "XDL-PARSE-NON-FINITE", str(error)
    except _ShapeError as error:
        return None, (make_diagnostic(
            error.code, ValidationGate.PARSE, str(error),
            "Correct the value or reduce the bounded input structure.", pointer=error.pointer,
            location=source_map.get(error.pointer, location),
        ),)
    except RecursionError as error:
        code, message = "XDL-PARSE-MAX-DEPTH", str(error)
    except (json.JSONDecodeError, YAMLError, ValueError) as error:
        code, message = f"XDL-PARSE-{source_format.upper()}", str(error).splitlines()[0]
    return None, (make_diagnostic(
        code, ValidationGate.PARSE, message,
        f"Correct the {source_format.upper()} syntax.", location=location,
    ),)


def load_sources(
    sources: Sequence[SourceInput], *, limits: LoadLimits = LoadLimits(),
) -> tuple[tuple[ParsedDocument, ...], tuple[Diagnostic, ...]]:
    """Parse explicit in-memory sources in deterministic name order.

    @return Parsed documents and no diagnostics, or no documents and sorted failures.
    """

    if len(sources) > limits.max_resources:
        return (), (make_diagnostic(
            "XDL-PARSE-MAX-RESOURCES", ValidationGate.PARSE,
            f"resource count {len(sources)} exceeds {limits.max_resources}",
            "Supply fewer resources or explicitly select a larger bounded limit.",
        ),)
    documents: list[ParsedDocument] = []
    diagnostics: list[Diagnostic] = []
    for source in sorted(sources, key=lambda item: item.name):
        document, found = _parse_one(source, limits)
        diagnostics.extend(found)
        if document:
            documents.append(document)
    if diagnostics:
        return (), sorted_diagnostics(diagnostics)
    return tuple(documents), ()


def load_file_sources(
    paths: Sequence[str | Path], *, limits: LoadLimits = LoadLimits(),
) -> tuple[tuple[ParsedDocument, ...], tuple[Diagnostic, ...]]:
    """Read explicit local paths and pass their bytes to the bounded loader."""

    sources: list[SourceInput] = []
    diagnostics: list[Diagnostic] = []
    for raw_path in sorted((Path(path) for path in paths), key=lambda path: str(path)):
        try:
            size = raw_path.stat().st_size
            if size > limits.max_bytes_per_file:
                diagnostics.append(make_diagnostic(
                    "XDL-PARSE-TOO-LARGE", ValidationGate.PARSE,
                    f"input is {size} bytes; limit is {limits.max_bytes_per_file}",
                    "Reduce the file size or explicitly select a larger bounded limit.",
                    location=SourceLocation(str(raw_path)),
                ))
                continue
            sources.append(SourceInput(str(raw_path), raw_path.read_bytes()))
        except OSError as error:
            diagnostics.append(make_diagnostic(
                "XDL-PARSE-READ", ValidationGate.PARSE, str(error),
                "Provide a readable local resource path.", location=SourceLocation(str(raw_path)),
            ))
    if diagnostics:
        return (), sorted_diagnostics(diagnostics)
    return load_sources(tuple(sources), limits=limits)
