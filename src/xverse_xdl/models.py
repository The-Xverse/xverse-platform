"""Immutable public models for XDL validation and normalization."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from types import MappingProxyType
from typing import Any


class ValidationGate(IntEnum):
    """Ordered validation stages used to prioritize diagnostics."""

    PARSE = 1
    SCHEMA = 2
    REFERENCE = 3
    SEMANTIC = 4
    BINDING = 5
    POLICY = 6


class Severity(str, Enum):
    """Machine-stable diagnostic severity values."""

    ERROR = "error"
    WARNING = "warning"
    ADVISORY = "advisory"


class StaticReadiness(str, Enum):
    """Declaration-only readiness state; it never represents a live probe."""

    READY = "Ready"
    NOT_READY = "NotReady"
    NOT_EVALUATED = "NotEvaluated"


@dataclass(frozen=True, order=True)
class SourceLocation:
    """Best-known source file, line, and column for authored data."""

    source: str
    line: int | None = None
    column: int | None = None


@dataclass(frozen=True, order=True)
class ResourceIdentity:
    """Stable logical identity of one XDL resource."""

    api_version: str
    kind: str
    namespace: str
    name: str

    @property
    def uri(self) -> str:
        """Return the canonical XDL resource URI."""

        return f"xdl://{self.namespace}/{self.kind.lower()}/{self.name}"

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ResourceIdentity":
        """Extract identity fields from an XDL resource-like mapping."""

        metadata = value.get("metadata", value)
        return cls(
            api_version=str(value.get("apiVersion", "")),
            kind=str(value.get("kind", "")),
            namespace=str(metadata.get("namespace", "")),
            name=str(metadata.get("name", "")),
        )


@dataclass(frozen=True, order=True)
class ElementIdentity:
    """Identity of a named element owned by an XDL resource."""

    resource: ResourceIdentity
    element_id: str

    @property
    def uri(self) -> str:
        """Return the resource URI with the escaped element fragment."""

        return f"{self.resource.uri}#{self.element_id}"


@dataclass(frozen=True)
class Diagnostic:
    """Structured validation finding with correction and source context."""

    code: str
    gate: ValidationGate
    severity: Severity
    message: str
    correction: str
    pointer: str = ""
    resource: ResourceIdentity | None = None
    location: SourceLocation | None = None
    related: tuple[str, ...] = ()

    @property
    def sort_key(self) -> tuple[Any, ...]:
        """Return the deterministic ordering key for user-facing reports."""

        return (
            int(self.gate), self.resource.uri if self.resource else "", self.pointer,
            self.code, self.message, self.location.source if self.location else "",
        )


class FrozenMap(Mapping[str, Any]):
    """Small immutable mapping with deterministic iteration order."""

    __slots__ = ("_items", "_index")

    def __init__(self, items: Mapping[str, Any] | tuple[tuple[str, Any], ...] = ()) -> None:
        """Copy mapping items into immutable deterministic storage."""

        pairs = items.items() if isinstance(items, Mapping) else items
        self._items = tuple(sorted(((str(key), value) for key, value in pairs), key=lambda item: item[0]))
        self._index = MappingProxyType(dict(self._items))

    def __getitem__(self, key: str) -> Any:
        """Return the value associated with *key*."""

        return self._index[key]

    def __iter__(self) -> Iterator[str]:
        """Iterate stored keys in deterministic insertion order."""

        return (key for key, _ in self._items)

    def __len__(self) -> int:
        """Return the number of stored keys."""

        return len(self._items)

    def __repr__(self) -> str:
        """Return a constructor-like representation of the frozen mapping."""

        return f"FrozenMap({dict(self._items)!r})"


def freeze(value: Any) -> Any:
    """Recursively convert mappings and sequences to immutable equivalents."""

    if isinstance(value, FrozenMap):
        return value
    if isinstance(value, Mapping):
        return FrozenMap(tuple((str(key), freeze(child)) for key, child in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(freeze(child) for child in value)
    return value


@dataclass(frozen=True)
class ResolvedReference:
    """Authored reference resolved to a resource and optional owned element."""

    pointer: str
    target: ResourceIdentity
    element: ElementIdentity | None = None
    collection: str | None = None


@dataclass(frozen=True)
class NormalizedResource:
    """Immutable semantic representation of one validated XDL resource."""

    identity: ResourceIdentity
    revision: str
    provenance: FrozenMap
    labels: FrozenMap
    elements: FrozenMap
    references: tuple[ResolvedReference, ...]
    extensions: FrozenMap
    content: FrozenMap
    source_map: FrozenMap


@dataclass(frozen=True)
class LoadLimits:
    """Fail-closed limits for local input size, depth, nodes, and resources."""

    max_bytes_per_file: int = 5 * 1024 * 1024
    max_depth: int = 100
    max_nodes: int = 100_000
    max_resources: int = 1_000

    def __post_init__(self) -> None:
        """Reject non-positive limits that would make bounded loading ambiguous."""

        if min(self.max_bytes_per_file, self.max_depth, self.max_nodes, self.max_resources) < 1:
            raise ValueError("all load limits must be positive")


@dataclass(frozen=True)
class ValidationResult:
    """Diagnostics, normalized resources, and declaration-only readiness states."""

    diagnostics: tuple[Diagnostic, ...]
    resources: tuple[NormalizedResource, ...] = ()
    readiness: FrozenMap = field(default_factory=FrozenMap)

    @property
    def is_valid(self) -> bool:
        """Return whether the result contains no error-severity diagnostic."""

        return not any(item.severity is Severity.ERROR for item in self.diagnostics)
