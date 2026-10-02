"""Argus Lite Phase 2 (ARGUS2): bounded run evidence persistence and read-only reconstruction.

Public surface: :class:`~xverse.argus.api.EvidenceStore` (``open_run``/``read_run``),
``EvidenceRun``, ``EvidenceReader``, ``EvidenceLimits``, ``EvidenceDiagnostic`` and
``EvidenceError``. Argus owns storage and offline inspection only: it performs no execution, no
control, no metric computation, no network access and no live tap attachment.
"""

from __future__ import annotations

from .api import EvidenceStore
from .diagnostics import EvidenceDiagnostic, EvidenceError
from .limits import EvidenceLimits
from .reader import EvidenceReader
from .schema import ARGUS_VERSION, EVENT_SCHEMA_VERSION, MANIFEST_VERSION
from .writer import EvidenceManifest, EvidenceRun

__all__ = [
    "ARGUS_VERSION",
    "EVENT_SCHEMA_VERSION",
    "MANIFEST_VERSION",
    "EvidenceDiagnostic",
    "EvidenceError",
    "EvidenceLimits",
    "EvidenceManifest",
    "EvidenceReader",
    "EvidenceRun",
    "EvidenceStore",
]
