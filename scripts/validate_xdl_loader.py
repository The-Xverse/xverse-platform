#!/usr/bin/env python3
"""Repeatable offline acceptance checks for capability 004."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

from xverse_xdl import canonical_json, validate_files
from xverse_xdl.schema import CoreSchemaRegistry

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "specs" / "004-xdl-loader-validator"
EXAMPLES = tuple(sorted((ROOT / "xdl" / "examples" / "v1alpha1").glob("*.xdl.yaml")))
PROFILE_SCHEMA = ROOT / "tests" / "fixtures" / "measurement-profile.schema.json"
REQUIRED = (
    FEATURE / "spec.md",
    FEATURE / "clarifications.md",
    FEATURE / "research.md",
    FEATURE / "data-model.md",
    FEATURE / "plan.md",
    FEATURE / "tasks.md",
    FEATURE / "analysis.md",
    FEATURE / "validation.md",
    FEATURE / "quickstart.md",
    FEATURE / "contracts" / "library.md",
    FEATURE / "contracts" / "cli.md",
    FEATURE / "checklists" / "requirements.md",
    FEATURE / "checklists" / "acceptance.md",
    ROOT / "docs" / "adr" / "ADR-0013-xdl-loader-validation-boundaries.md",
    ROOT / "docs" / "reviews" / "004-xdl-loader-validator-architecture-review.md",
)
PLACEHOLDER = re.compile(r"NEEDS CLARIFICATION|\[FEATURE(?: NAME)?\]|\[DATE\]|<FEATURE")
NETWORK_MODULES = {"aiohttp", "httpx", "requests", "socket", "urllib.request"}


class AcceptanceError(RuntimeError):
    """Report a failed capability 004 acceptance assertion."""

    pass


def check(condition: bool, message: str) -> None:
    """Raise an acceptance error when *condition* is false."""

    if not condition:
        raise AcceptanceError(message)


def check_source_imports() -> None:
    """Reject network-capable imports from the offline XDL package."""

    for path in sorted((ROOT / "src" / "xverse_xdl").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                check(name not in NETWORK_MODULES, f"network-capable import {name!r} in {path}")


def main() -> int:
    """Run capability 004 artifact, offline, and deterministic-output checks."""

    feature_pointer = json.loads((ROOT / ".specify" / "feature.json").read_text(encoding="utf-8"))
    check(feature_pointer == {"feature_directory": "specs/004-xdl-loader-validator"},
          "Spec Kit feature pointer does not resolve capability 004")
    for path in REQUIRED:
        check(path.is_file() and path.stat().st_size > 0, f"missing required artifact: {path}")
        check(not PLACEHOLDER.search(path.read_text(encoding="utf-8")),
              f"unresolved template marker in {path}")

    task_text = (FEATURE / "tasks.md").read_text(encoding="utf-8")
    check(len(re.findall(r"^- \[X\] T0(?:0[1-9]|[12][0-9]|3[0-5])\b", task_text, re.MULTILINE)) == 35,
          "capability tasks T001-T035 are not all complete")
    acceptance_text = (FEATURE / "checklists" / "acceptance.md").read_text(encoding="utf-8")
    check(len(re.findall(r"^- \[X\] ACC0(?:0[1-9]|1[0-6])\b", acceptance_text, re.MULTILINE)) == 16,
          "acceptance items ACC001-ACC016 are not complete")

    registry = CoreSchemaRegistry()
    check(len(registry.schemas) == 7, "authoritative seven-schema package is incomplete")
    check(registry.network_requests == 0, "core schema registry attempted network access")

    forward = validate_files(EXAMPLES, profile_schema_paths=(PROFILE_SCHEMA,))
    reverse = validate_files(tuple(reversed(EXAMPLES)), profile_schema_paths=(PROFILE_SCHEMA,))
    check(forward.is_valid, f"approved graph failed: {forward.diagnostics}")
    check(len(forward.resources) == 5, "approved graph did not normalize five resources")
    check(canonical_json(forward.resources) == canonical_json(reverse.resources),
          "canonical normalization depends on input argument order")
    check(dict(forward.readiness) == dict(reverse.readiness),
          "static readiness depends on input argument order")

    check_source_imports()
    print("capability 004 validation passed: 5 resources, 7 schemas, offline deterministic normalization")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AcceptanceError as error:
        print(f"capability 004 validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
