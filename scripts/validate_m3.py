#!/usr/bin/env python3
"""Validate the public M3 catalog, plan, permit, fixture lifecycle, and evidence path."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from xverse_xdl.catalog import build_lifecycle_plan, derive_catalog
from xverse_xdl.lifecycle import ExecutionPermit, FileEvidenceJournal, FixtureProvider, LifecycleController
from xverse_xdl.validate import validate_files

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "xdl" / "examples" / "m3"
RESOURCES = tuple(FIXTURE / name for name in (
    "runtime-profile.xdl.yaml", "fixture-component.xdl.yaml",
    "fixture-system.xdl.yaml", "fixture-deployment.xdl.yaml",
))
PROFILE_SCHEMA = ROOT / "xdl" / "profiles" / "runtime-compatibility-v0.1.schema.json"


def main() -> int:
    """Run the complete isolated public fixture lifecycle and report JSON evidence."""

    validation = validate_files(RESOURCES, profile_schema_paths=(PROFILE_SCHEMA,))
    if not validation.is_valid:
        print(json.dumps({"valid": False, "stage": "xdl", "diagnostics": [item.code for item in validation.diagnostics]}))
        return 1
    catalog = derive_catalog(validation.resources)
    if not catalog.is_valid or len(catalog.entries) != 1:
        print(json.dumps({"valid": False, "stage": "catalog", "diagnostics": [item.code for item in catalog.diagnostics]}))
        return 1
    plan = build_lifecycle_plan(catalog.entries[0])
    now = datetime.now(timezone.utc)
    permit = ExecutionPermit(
        permit_id="m3-public-fixture-permit", nonce="m3-public-fixture-run",
        plan_digest=plan.digest, catalog_identity=plan.catalog_identity,
        environment_identity=plan.environment_identity,
        permitted_actions=tuple(item.action_id for item in plan.actions),
        approval_evidence_ref="urn:xverse:local:m3-fixture-validation",
        issuer_label="local-m3-validator",
        operation_classes=tuple(sorted({item.operation for item in plan.actions})),
        exclusions=("legacy-execution", "production-workload"),
        public_safety_classification="public-safe",
        not_before=now - timedelta(seconds=1), expires_at=now + timedelta(minutes=1),
    )
    with tempfile.TemporaryDirectory(prefix="xverse-m3-fixture-") as temporary:
        journal = FileEvidenceJournal(Path(temporary) / "evidence.jsonl")
        provider = FixtureProvider()
        controller = LifecycleController(journal)
        started = controller.start(plan, permit, provider, execution_id="m3-public-fixture")
        observed = controller.observe("m3-public-fixture", provider)
        stopped = controller.stop("m3-public-fixture", provider)
        cleaned = controller.cleanup("m3-public-fixture", provider)
        evidence_count = len(journal.records)
    report = {
        "artifactDigestCount": len(plan.artifact_digests),
        "catalogEntries": len(catalog.entries),
        "evidenceRecords": evidence_count,
        "fixtureStatuses": [started.status, observed.status, stopped.status, cleaned.status],
        "legacyExecution": False,
        "planDigest": plan.digest,
        "valid": cleaned.status == "cleaned" and evidence_count == 8,
    }
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
