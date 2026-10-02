"""Explicit causal reference indexing without invention.

``causationId``/``correlationId`` are indexed by accepted ``eventId``. An unresolved target remains
visible and is reported; a causal link is explicit evidence, never proof of synchronisation, and no
predecessor is repaired or invented (``detailed-design.md`` section 6).
"""

from __future__ import annotations

from typing import Any

from .diagnostics import EvidenceDiagnostic, EvidenceError, diagnostic

__all__ = ["CausalIndex", "index_references", "unresolved_references"]


class CausalIndex:
    """Bounded index of accepted event identities and their declared causal references."""

    def __init__(self, maximum: int) -> None:
        self.maximum = maximum
        self.event_ids: set[str] = set()
        self.references: dict[str, list[str]] = {}

    def register_event(self, event_id: str) -> None:
        """Register one accepted event identity."""

        self.event_ids.add(event_id)

    def add_references(self, *, event_id: str, targets: tuple[str, ...]) -> None:
        """Record the causal targets declared by one accepted event, enforcing the finite bound."""

        for target in targets:
            if target in self.references:
                if event_id not in self.references[target]:
                    self.references[target].append(event_id)
                continue
            if len(self.references) + 1 > self.maximum:
                raise EvidenceError(
                    diagnostic(
                        "ARGUS2-BOUND-EXCEEDED",
                        f"causal index would exceed max_causal_index_entries {self.maximum}",
                        event_id=event_id,
                        remediation="Reduce the number of distinct declared causal references.",
                    )
                )
            self.references[target] = [event_id]

    def unresolved(self) -> tuple[str, ...]:
        """Return referenced targets that resolve to no accepted event, deterministically ordered."""

        return tuple(sorted(target for target in self.references if target not in self.event_ids))

    def entry_count(self) -> int:
        """Return the number of indexed causal references."""

        return len(self.references)


def index_references(events: list[dict[str, Any]], *, maximum: int) -> tuple[CausalIndex, tuple[str, ...]]:
    """Build the causal index over accepted events; return it and any diagnostics."""

    index = CausalIndex(maximum)
    diagnostics: list[EvidenceDiagnostic] = []
    for event in events:
        event_id = event.get("eventId")
        if isinstance(event_id, str):
            index.register_event(event_id)
    for event in events:
        event_id = event.get("eventId")
        targets = tuple(
            value
            for value in (event.get("causationId"), event.get("correlationId"))
            if isinstance(value, str)
        )
        try:
            index.add_references(event_id=str(event_id), targets=targets)
        except EvidenceError as error:
            diagnostics.extend(error.diagnostics)
    return index, tuple(diagnostics)


def unresolved_references(index: CausalIndex) -> tuple[str, ...]:
    """Return the unresolved causal targets of an index."""

    return index.unresolved()
