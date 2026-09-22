#!/usr/bin/env python3
"""Validate the locked SD-0001 XDL candidate without executing any lifecycle action."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from xverse_xdl.catalog import build_lifecycle_plan, derive_catalog
from xverse_xdl.validate import validate_files

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "xdl" / "candidates" / "sd0001" / "candidate.lock.json"


def _sha256(path: Path) -> str:
    """Return the hexadecimal SHA-256 digest of one local file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _emit(report: dict[str, Any]) -> None:
    """Print one deterministic compact JSON report."""

    print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _checked_path(relative: str, required_root: str) -> Path:
    """Resolve a traversal-free repository path below one required relative root."""

    authored = PurePosixPath(relative)
    if authored.is_absolute() or ".." in authored.parts:
        raise ValueError("locked path must be repository-relative and traversal-free")
    resolved = ROOT.joinpath(*authored.parts)
    resolved.resolve(strict=False).relative_to((ROOT / required_root).resolve())
    return resolved


def _validate_candidate() -> int:
    """Perform exact candidate validation after the public wrapper handles input errors."""

    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    required_fields = {
        "artifactDigests", "blockers", "candidate", "catalogIdentity", "legacyExecution",
        "planDigest", "profileSchema", "provider", "resources", "resourceVersions",
        "schemaVersion",
    }
    if not isinstance(lock, dict) or not required_fields.issubset(lock):
        raise ValueError("candidate lock lacks required fields")

    mismatches: list[str] = []
    resources: list[Path] = []
    for record in lock["resources"]:
        relative = str(record["path"])
        path = _checked_path(relative, "xdl/candidates/sd0001")
        resources.append(path)
        if path.is_symlink() or not path.is_file() or _sha256(path) != record["sha256"]:
            mismatches.append(f"resource-digest:{relative}")

    schema_record = lock["profileSchema"]
    schema_path = _checked_path(str(schema_record["path"]), "xdl/profiles")
    if schema_path.is_symlink() or not schema_path.is_file() or _sha256(schema_path) != schema_record["sha256"]:
        mismatches.append("profile-schema-digest")
    if lock.get("legacyExecution") is not False:
        mismatches.append("legacy-execution-flag")
    if lock.get("candidate") != "SD-0001":
        mismatches.append("candidate-identity")
    if lock.get("schemaVersion") != "1.0.0":
        mismatches.append("lock-schema-version")
    if mismatches:
        _emit({"legacyExecution": False, "mismatches": sorted(mismatches), "valid": False})
        return 1

    validation = validate_files(tuple(resources), profile_schema_paths=(schema_path,))
    if not validation.is_valid:
        _emit({
            "diagnostics": sorted(item.code for item in validation.diagnostics),
            "legacyExecution": False,
            "stage": "xdl",
            "valid": False,
        })
        return 1

    catalog = derive_catalog(validation.resources)
    if not catalog.is_valid or len(catalog.entries) != 1:
        _emit({
            "catalogEntries": len(catalog.entries),
            "diagnostics": sorted(item.code for item in catalog.diagnostics),
            "legacyExecution": False,
            "stage": "catalog",
            "valid": False,
        })
        return 1

    entry = catalog.entries[0]
    plan = build_lifecycle_plan(entry)
    actual_versions = {
        resource.identity.uri: resource.revision for resource in validation.resources
    }
    exact_checks = {
        "artifactDigests": list(plan.artifact_digests) == lock["artifactDigests"],
        "blockers": list(plan.blockers) == lock["blockers"],
        "catalogIdentity": entry.identity == lock["catalogIdentity"],
        "planDigest": plan.digest == lock["planDigest"],
        "profileSchema": entry.profile_revision == "0.2.0",
        "provider": {
            "id": entry.provider_id,
            "kind": entry.provider_kind,
        } == lock["provider"],
        "resourceVersions": actual_versions == lock["resourceVersions"],
    }
    valid = (
        all(exact_checks.values())
        and not plan.is_plannable
        and not plan.execution_eligible
        and bool(plan.blockers)
    )
    _emit({
        "blockers": list(plan.blockers),
        "catalogIdentity": entry.identity,
        "checks": exact_checks,
        "executionEligible": plan.execution_eligible,
        "legacyExecution": False,
        "planDigest": plan.digest,
        "plannable": plan.is_plannable,
        "resourceCount": len(validation.resources),
        "valid": valid,
    })
    return 0 if valid else 1


def main() -> int:
    """Verify locked candidate data and return a stable public-safe result.

    @return Zero only when the complete candidate matches the reviewed lock and remains blocked.
    """

    try:
        return _validate_candidate()
    except (json.JSONDecodeError, KeyError, OSError, TypeError, ValueError):
        _emit({
            "legacyExecution": False,
            "mismatches": ["candidate-lock-invalid"],
            "valid": False,
        })
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
