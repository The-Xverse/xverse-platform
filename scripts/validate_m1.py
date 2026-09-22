#!/usr/bin/env python3
"""Offline structural validation for M1 architecture documentation."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "specs/002-domain-neutral-metamodel"
METAMODEL = ROOT / "docs/architecture/METAMODEL.md"
REQUIRED_CONCEPTS = (
    "System", "Scenario", "Component", "Node", "Device", "Sensor", "Actuator",
    "ComputeResource", "Interface", "Endpoint", "Flow", "Network", "Link",
    "Protocol", "Model", "Artifact", "ExecutionTarget", "Simulator", "TimeDomain",
    "Clock", "Fault", "Observer", "Metric", "Parameter", "Resource", "Deployment",
)
REQUIRED_DOCUMENTS = (
    FEATURE / "spec.md",
    FEATURE / "clarifications.md",
    FEATURE / "research.md",
    FEATURE / "data-model.md",
    FEATURE / "plan.md",
    FEATURE / "quickstart.md",
    FEATURE / "tasks.md",
    FEATURE / "analysis.md",
    FEATURE / "validation.md",
    FEATURE / "checklists/requirements.md",
    FEATURE / "checklists/acceptance.md",
    METAMODEL,
    ROOT / "docs/architecture/METAMODEL_DIAGRAM.md",
    ROOT / "docs/architecture/METAMODEL_DIAGRAM.svg",
    ROOT / "docs/reviews/002-domain-neutral-metamodel-architecture-review.md",
)
REQUIRED_ADRS = tuple(
    ROOT / f"docs/adr/ADR-000{i}-{slug}.md"
    for i, slug in (
        (5, "domain-neutral-metamodel-core"),
        (6, "logical-identity-and-realization-binding"),
        (7, "lifecycle-time-and-evidence-semantics"),
        (8, "profile-extension-boundaries"),
    )
)
FIELD_MARKERS = (
    "**Purpose**:", "**Identity/lifecycle**:", "**Required**:", "**Optional**:",
    "**Relations**:", "**Validation**:", "**Extension**:",
)


def errors_for_metamodel(text: str) -> list[str]:
    """Return missing concept sections and required field markers."""

    errors: list[str] = []
    headings = list(re.finditer(r"^### (.+)$", text, flags=re.MULTILINE))
    sections: dict[str, str] = {}
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        sections[heading.group(1)] = text[heading.end():end]
    for concept in REQUIRED_CONCEPTS:
        section = sections.get(concept)
        if section is None:
            errors.append(f"missing concept heading: {concept}")
            continue
        for marker in FIELD_MARKERS:
            if marker not in section:
                errors.append(f"{concept} lacks required field marker {marker}")
    return errors


def validate() -> list[str]:
    """Validate M1 artifacts, ADRs, links, scope exclusions, and diagram sources."""

    errors: list[str] = []
    for document in REQUIRED_DOCUMENTS + REQUIRED_ADRS:
        if not document.is_file():
            errors.append(f"missing required document: {document.relative_to(ROOT)}")

    if errors:
        return errors

    texts = {document: document.read_text(encoding="utf-8") for document in REQUIRED_DOCUMENTS + REQUIRED_ADRS}
    errors.extend(errors_for_metamodel(texts[METAMODEL]))

    placeholders = re.compile(r"\[NEEDS CLARIFICATION|TODO|TKTK|\[FEATURE NAME\]|\[###-", re.IGNORECASE)
    for document, text in texts.items():
        if placeholders.search(text):
            errors.append(f"unresolved template marker in {document.relative_to(ROOT)}")

    for adr in REQUIRED_ADRS:
        text = texts[adr]
        for heading in ("## Context", "## Decision", "## Consequences and alternatives", "## Evidence and scope"):
            if heading not in text:
                errors.append(f"{adr.name} lacks {heading}")
        if "**Status**: Accepted" not in text:
            errors.append(f"{adr.name} does not record accepted M1 review status")

    expected_links = (
        ROOT / "docs/architecture/XVERSE_VNEXT_ARCHITECTURE_AND_CODEX_GUIDANCE.md",
        ROOT / "docs/architecture/REFERENCE_REGISTER.md",
        ROOT / "docs/reviews/002-domain-neutral-metamodel-architecture-review.md",
        FEATURE / "checklists/acceptance.md",
    )
    for link in expected_links:
        if not link.exists():
            errors.append(f"missing linked architecture artifact: {link.relative_to(ROOT)}")

    diagram = texts[ROOT / "docs/architecture/METAMODEL_DIAGRAM.md"]
    if "mermaid" not in diagram or "classDiagram" not in diagram or 'Deployment "*" --> "1" System : realizes' not in diagram:
        errors.append("diagram does not show the required logical-to-realization relationship")
    svg = texts[ROOT / "docs/architecture/METAMODEL_DIAGRAM.svg"]
    if "<svg" not in svg or "Deployment is the only bridge" not in svg:
        errors.append("standalone diagram SVG is missing required conceptual content")

    for path in (FEATURE / "contracts", FEATURE / "schemas", FEATURE / "xdl", FEATURE / "src"):
        if path.exists():
            errors.append(f"forbidden M1 implementation artifact: {path.relative_to(ROOT)}")

    status = texts[FEATURE / "spec.md"]
    for phrase in ("Do not create XDL schemas", "Runtime tests**: Not applicable"):
        if phrase not in status:
            errors.append(f"scope exclusion missing from spec: {phrase}")

    return errors


def self_test() -> list[str]:
    """Exercise M1 validators with complete and deliberately invalid fixtures."""

    errors: list[str] = []
    complete = "\n".join(f"### {name}\n" + " ".join(FIELD_MARKERS) for name in REQUIRED_CONCEPTS)
    if errors_for_metamodel(complete):
        errors.append("complete synthetic metamodel unexpectedly failed")
    missing = complete.replace("### System", "### MissingSystem", 1)
    if not errors_for_metamodel(missing):
        errors.append("missing concept synthetic metamodel unexpectedly passed")
    incomplete = complete.replace("**Extension**:", "", 1)
    if not errors_for_metamodel(incomplete):
        errors.append("missing-field synthetic metamodel unexpectedly passed")
    placeholders = re.compile(r"\[NEEDS CLARIFICATION|TODO|TKTK|\[FEATURE NAME\]|\[###-", re.IGNORECASE)
    if not placeholders.search("[NEEDS CLARIFICATION: synthetic]"):
        errors.append("placeholder detector synthetic case unexpectedly failed")
    return errors


def main() -> int:
    """Run normal M1 validation or its in-memory negative self-test."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    errors = self_test() if args.self_test else validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    if args.self_test:
        print("M1 validator self-test passed: 3 negative cases rejected.")
    else:
        print(f"M1 validation passed: {len(REQUIRED_CONCEPTS)} concepts and {len(REQUIRED_ADRS)} ADRs checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
