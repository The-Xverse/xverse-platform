"""Confined run-relative artifact store.

Every artifact path is a run-relative POSIX path resolved against the confined real run-root path.
Traversal, absolute paths, escaping or internal symlinks, unsafe names and non-regular files are
rejected before any access; a write outside the run root is impossible by design
(``detailed-design.md`` section 9, invariant ``ARGUS2-INV-07``).
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any

from .diagnostics import EvidenceDiagnostic, diagnostic
from .limits import EvidenceLimits
from .recovery import open_confined
from .schema import ARTIFACT_ENTRY_KEYS

__all__ = [
    "ARTIFACT_PATH_PATTERN",
    "build_index_entry",
    "confined_path",
    "sha256_file",
    "verify_index_entry",
]

ARTIFACT_PATH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,255}$")


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 hex digest of a file's bytes."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _text_diagnostics(relative: Any) -> tuple[list[EvidenceDiagnostic], list[str]]:
    diagnostics: list[EvidenceDiagnostic] = []
    if not isinstance(relative, str) or relative == "":
        return [
            diagnostic(
                "ARGUS2-PATH-UNSAFE",
                "artifact path must be a non-empty run-relative POSIX path",
                path=relative if isinstance(relative, str) else None,
                remediation="Supply a run-relative path inside the run root.",
            )
        ], []
    if relative.startswith(("/", "\\")) or "\\" in relative or "\x00" in relative:
        return [
            diagnostic(
                "ARGUS2-PATH-UNSAFE",
                f"artifact path is absolute or contains a forbidden character: {relative!r}",
                path=relative,
                remediation="Use a run-relative POSIX path with no backslash or NUL.",
            )
        ], []
    if ARTIFACT_PATH_PATTERN.match(relative) is None:
        return [
            diagnostic(
                "ARGUS2-PATH-UNSAFE",
                f"artifact path is outside the frozen name pattern: {relative!r}",
                path=relative,
                remediation="Match ^[A-Za-z0-9][A-Za-z0-9._/-]{0,255}$.",
            )
        ], []
    segments = relative.split("/")
    if any(segment == "" or segment == "." for segment in segments):
        return [
            diagnostic(
                "ARGUS2-PATH-UNSAFE",
                f"artifact path contains an empty or '.' segment: {relative!r}",
                path=relative,
                remediation="Remove empty or '.' path segments.",
            )
        ], []
    if ".." in segments:
        return [
            diagnostic(
                "ARGUS2-PATH-ESCAPE",
                f"artifact path contains a '..' traversal segment: {relative!r}",
                path=relative,
                remediation="Remove the traversal segment; artifacts stay inside the run root.",
            )
        ], []
    if diagnostics:
        return diagnostics, []
    return diagnostics, segments


def confined_path(root: Any, relative: Any) -> tuple[Path | None, list[EvidenceDiagnostic]]:
    """Resolve a run-relative path against the confined real run root, or return diagnostics."""

    diagnostics, segments = _text_diagnostics(relative)
    if diagnostics:
        return None, diagnostics
    root_path = Path(root)
    root_real = Path(os.path.realpath(root_path))
    candidate = root_real.joinpath(*segments)
    current = root_real
    for segment in segments:
        current = current / segment
        if os.path.islink(current):
            return None, [
                diagnostic(
                    "ARGUS2-PATH-SYMLINK",
                    f"artifact path component is a symlink: {relative!r}",
                    path=relative,
                    remediation="Symlinks are rejected regardless of their resolution target.",
                )
            ]
    resolved = Path(os.path.realpath(candidate))
    if not _is_within(root_real, resolved):
        return None, [
            diagnostic(
                "ARGUS2-PATH-ESCAPE",
                f"artifact path resolves outside the run root: {relative!r}",
                path=relative,
                remediation="Keep the artifact inside the confined run root.",
            )
        ]
    return candidate, []


def _is_within(root_real: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root_real)
    except ValueError:
        return False
    return True


def _file_identity(root: Any, relative: Any, *, expected_size: int | None = None):
    """Hash a safely opened descriptor with bounded chunks and a recorded-size stop."""
    diagnostics, _ = _text_diagnostics(relative)
    if diagnostics:
        return None, diagnostics
    descriptor, diagnostics = open_confined(root, relative)
    if diagnostics:
        return None, diagnostics
    size = 0
    digest = hashlib.sha256()
    try:
        if expected_size is not None and os.fstat(descriptor).st_size != expected_size:
            return None, [diagnostic("ARGUS2-CORRUPT-ARTIFACT-SIZE", "artifact size differs from the recorded value",
                path=relative, remediation="Preserve the recorded size and report incomplete evidence.")]
        while True:
            remaining = 1024 * 1024 if expected_size is None else min(1024 * 1024, expected_size - size + 1)
            chunk = os.read(descriptor, remaining)
            if not chunk:
                break
            size += len(chunk)
            if expected_size is not None and size > expected_size:
                return None, [diagnostic("ARGUS2-CORRUPT-ARTIFACT-SIZE", "artifact grew during verification",
                    path=relative, remediation="Verify only stable evidence files.")]
            digest.update(chunk)
        return (size, digest.hexdigest()), []
    except OSError:
        return None, [diagnostic("ARGUS2-IO-FAILURE", "artifact could not be read", path=relative,
            remediation="Resolve the filesystem failure; no completeness is claimed.")]
    finally:
        os.close(descriptor)


def build_index_entry(root: Any, relative: str, *, media_type: str, schema_version: str,
                      role: str, limits: EvidenceLimits) -> dict[str, Any] | None:
    """Build an artifact entry from one confined descriptor, never caller-owned identity."""
    from .diagnostics import EvidenceError

    identity, diagnostics = _file_identity(root, relative)
    if diagnostics:
        if diagnostics[0].code == "ARGUS2-MISSING-ARTIFACT":
            return None
        raise EvidenceError(tuple(diagnostics[:limits.max_diagnostic_count]))
    size, digest = identity
    return {"path": relative, "mediaType": media_type, "schemaVersion": schema_version,
            "bytes": size, "sha256": digest, "role": role}


def verify_index_entry(root: Any, entry: Any) -> list[EvidenceDiagnostic]:
    """Validate the frozen entry, then verify its exact file with bounded descriptor reads."""
    if (not isinstance(entry, dict) or set(entry) != set(ARTIFACT_ENTRY_KEYS)
            or any(not isinstance(entry.get(key), str) or not entry[key]
                   for key in ("path", "mediaType", "schemaVersion", "sha256", "role"))
            or isinstance(entry.get("bytes"), bool) or not isinstance(entry.get("bytes"), int)
            or entry["bytes"] < 0 or re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) is None):
        return [diagnostic("ARGUS2-INPUT-FIELD-INVALID", "artifact entry does not match the frozen schema",
            remediation="Preserve complete artifact identity metadata.")]
    identity, diagnostics = _file_identity(root, entry["path"], expected_size=entry["bytes"])
    if diagnostics:
        return diagnostics
    size, digest = identity
    if size != entry["bytes"]:
        return [diagnostic("ARGUS2-CORRUPT-ARTIFACT-SIZE", "artifact size differs from the recorded value",
            path=entry["path"], remediation="The recorded size is never updated on read.")]
    if digest != entry["sha256"]:
        return [diagnostic("ARGUS2-CORRUPT-ARTIFACT-HASH", "artifact hash differs from the recorded value",
            path=entry["path"], remediation="The recorded hash is never updated on read.")]
    return []
