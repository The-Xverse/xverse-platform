"""Caller-configured finite evidence bounds.

``EvidenceLimits`` is the frozen bound set of ``detailed-design.md`` section 10. Every field is a
positive integer supplied by the caller and echoed into the manifest so the reader verifies under
the same bounds. A non-positive field is a library programming error (``ValueError``), never an
evidence diagnostic. These bounds are implementation limits, not scientific or safety thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["EvidenceLimits"]

_FIELDS = (
    "max_event_bytes",
    "max_events",
    "max_id_length",
    "max_text_length",
    "max_payload_bytes",
    "max_artifacts",
    "max_obligations",
    "max_diagnostic_count",
    "max_manifest_bytes",
    "max_causal_index_entries",
    "max_read_records",
)


@dataclass(frozen=True)
class EvidenceLimits:
    """Finite, caller-supplied evidence bounds; the frozen library defaults are documented limits."""

    max_event_bytes: int = 1_048_576
    max_events: int = 100_000
    max_id_length: int = 128
    max_text_length: int = 256
    max_payload_bytes: int = 1_024
    max_artifacts: int = 256
    max_obligations: int = 64
    max_diagnostic_count: int = 256
    max_manifest_bytes: int = 4_194_304
    max_causal_index_entries: int = 4_096
    max_read_records: int = 100_000

    def __post_init__(self) -> None:
        for name in _FIELDS:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"all evidence limits must be positive integers: {name}")

    def to_data(self) -> dict[str, int]:
        """Return the canonical manifest echo of the effective limits."""

        return {name: getattr(self, name) for name in _FIELDS}

    @classmethod
    def from_data(cls, data: dict) -> EvidenceLimits:
        """Rebuild limits from a manifest echo, rejecting unknown or malformed entries."""

        if not isinstance(data, dict):
            raise ValueError("limits echo must be an object")  # noqa: TRY004 - preserve the frozen API
        unknown = [key for key in data if key not in _FIELDS]
        if unknown:
            raise ValueError(f"unknown limit fields: {sorted(unknown)}")
        return cls(**{name: data[name] for name in _FIELDS if name in data})
