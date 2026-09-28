#!/usr/bin/env python3
"""Offline validator for the X-COM capability-007 architecture/boundary/contract
model (task T009).

The model is the canonical, schema-versioned component/boundary/contract/diagram/
invariant view of the accepted capability-007 architecture. It elaborates -- it
does not replace -- ``specs/007-xcom-core/plan.md``, ``data-model.md``, and the
accepted ``contracts/*.md``. This validator is a repository-owned, deterministic,
single-threaded, offline checker. It reads only repository-relative files, never
writes the candidate tree, never opens a network peer or a subprocess, and returns
a distinct nonzero exit class per failure family so callers (including the
``--self-test`` fixtures) can bind a result to the exact defect it detected.

Public safety: the model, its Markdown projection, and this validator's output must
not contain credentials, private addresses, proprietary source excerpts,
unrestricted payloads, private-key markers, or absolute host paths. ``--verify``
scans for the mechanically detectable classes; the review stage judges the classes
that are not mechanically decidable.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T009_DIR = ROOT / "docs" / "engineering" / "xcom" / "t009"
MODEL_JSON = T009_DIR / "architecture-model.json"
MODEL_MD = T009_DIR / "architecture-model.md"
OWNERSHIP_JSON = ROOT / "docs" / "engineering" / "xcom" / "task-ownership.json"
REQUIREMENT_REGISTER_JSON = (
    ROOT / "docs" / "engineering" / "xcom" / "t008" / "requirements-register.json"
)

EXIT_OK = 0
EXIT_SCHEMA = 2
EXIT_IDENTITY = 3
EXIT_BOUNDARY = 4
EXIT_CONTRACT = 5
EXIT_DIAGRAM = 6
EXIT_GOVERNANCE = 7
EXIT_SAFETY = 8
EXIT_BINDING = 9
EXIT_DETERMINISM = 10
EXIT_PUBLIC_SAFETY = 11
EXIT_PATH = 12
EXIT_IO = 13

CLASS_NAMES = {
    EXIT_OK: "OK",
    EXIT_SCHEMA: "SCHEMA_INVALID",
    EXIT_IDENTITY: "IDENTITY_INVALID",
    EXIT_BOUNDARY: "BOUNDARY_INVALID",
    EXIT_CONTRACT: "CONTRACT_INVALID",
    EXIT_DIAGRAM: "DIAGRAM_INVALID",
    EXIT_GOVERNANCE: "GOVERNANCE_INVALID",
    EXIT_SAFETY: "SAFETY_INVALID",
    EXIT_BINDING: "BINDING_INVALID",
    EXIT_DETERMINISM: "DETERMINISM_INVALID",
    EXIT_PUBLIC_SAFETY: "PUBLIC_SAFETY_INVALID",
    EXIT_PATH: "PATH_INVALID",
    EXIT_IO: "IO_ERROR",
}

MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 4 * 1024 * 1024

TASK_ID = "T009"
CAPABILITY = "007-xcom-core"
SCHEMA_VERSION = 1

LAYER_VOCABULARY = [
    "boundary",
    "build-time",
    "data-plane",
    "derived-artifact",
    "downstream",
    "edge",
    "external",
    "test-fixture",
    "xdl-input",
]
LANGUAGE_VOCABULARY = ["cpp", "external", "json", "protobuf", "python"]
BOUNDARY_KIND_VOCABULARY = [
    "artifact",
    "data",
    "in-process",
    "ipc",
    "language",
    "realization",
    "trust",
]
CONTRACT_KIND_VOCABULARY = [
    "cross-language-schema",
    "external-rpc",
    "in-process-cpp",
    "schema",
]
DIAGRAM_KIND_VOCABULARY = ["component", "sequence"]
MATURITY_VOCABULARY = [
    "allocated",
    "conflicting",
    "deferred",
    "implemented",
    "needs_clarification",
    "partial",
    "superseded",
]
INVARIANT_KIND_VOCABULARY = [
    "architecture",
    "data-model",
    "dependency",
    "neutrality",
    "safety",
]
DIRECTION_VOCABULARY = ["bidirectional", "one-way", "request-response", "stream"]
AUTHORIZATION_VOCABULARY = [
    "exact-handle-required",
    "none",
    "plan-digest-bound",
    "tap-policy-required",
    "validation-permit-required",
]
ADR_VOCABULARY = ["ADR-0016", "ADR-0018", "ADR-0019", "ADR-0020"]
ACCEPTED_AUTHORIZATION = [f"ACC{number:03d}" for number in range(1, 16)] + [
    "ADR-0018",
    "ADR-0019",
    "ADR-0020",
]

MODEL_TOP = [
    "schema_version",
    "task_id",
    "capability",
    "baseline_revision",
    "candidate_revision_rule",
    "layer_vocabulary",
    "language_vocabulary",
    "boundary_kind_vocabulary",
    "contract_kind_vocabulary",
    "diagram_kind_vocabulary",
    "maturity_vocabulary",
    "invariant_kind_vocabulary",
    "direction_vocabulary",
    "authorization_vocabulary",
    "adr_vocabulary",
    "authorization_records",
    "ref002",
    "counts",
    "components",
    "boundaries",
    "contracts",
    "diagrams",
    "invariants",
]

VOCABULARY_FIELDS = {
    "layer_vocabulary": LAYER_VOCABULARY,
    "language_vocabulary": LANGUAGE_VOCABULARY,
    "boundary_kind_vocabulary": BOUNDARY_KIND_VOCABULARY,
    "contract_kind_vocabulary": CONTRACT_KIND_VOCABULARY,
    "diagram_kind_vocabulary": DIAGRAM_KIND_VOCABULARY,
    "maturity_vocabulary": MATURITY_VOCABULARY,
    "invariant_kind_vocabulary": INVARIANT_KIND_VOCABULARY,
    "direction_vocabulary": DIRECTION_VOCABULARY,
    "authorization_vocabulary": AUTHORIZATION_VOCABULARY,
    "adr_vocabulary": ADR_VOCABULARY,
}

FAMILIES = ("components", "boundaries", "contracts", "diagrams", "invariants")

COMPONENT_FIELDS = [
    "id",
    "name",
    "layer",
    "language",
    "scope",
    "responsibility",
    "owning_slice",
    "owning_tasks",
    "maturity",
    "accepted_revision",
    "reconciliation",
    "artifact_paths",
    "requirement_links",
    "governing_adrs",
    "constraints",
    "intra_layer",
]
BOUNDARY_FIELDS = [
    "id",
    "name",
    "kind",
    "from_component",
    "to_component",
    "from_language",
    "to_language",
    "direction",
    "scope",
    "contract",
    "authorization",
    "safety",
    "failure_semantics",
    "maturity",
    "accepted_revision",
]
CONTRACT_FIELDS = [
    "id",
    "name",
    "kind",
    "producer_components",
    "consumer_components",
    "endpoint_languages",
    "version",
    "canonical_artifact",
    "encoding",
    "unknown_field_policy",
    "evolution_rule",
    "governing_adrs",
    "maturity",
    "accepted_revision",
]
DIAGRAM_FIELDS = ["id", "kind", "title", "user_story", "participants", "steps"]
STEP_FIELDS = ["from", "to", "boundary", "note"]
INVARIANT_FIELDS = ["id", "kind", "statement", "applies_to", "source", "enforcement"]
PATH_FIELDS = ["path", "status"]
REF002_FIELDS = ["disposition", "promoted", "source"]

REQUIRED_COMPONENTS = [f"XCOM-CMP-{number:03d}" for number in range(1, 14)]
REQUIRED_BOUNDARIES = [f"XCOM-XB-{number:03d}" for number in range(1, 12)]
REQUIRED_CONTRACTS = [f"XCOM-XLC-{number:03d}" for number in range(1, 7)]
REQUIRED_DIAGRAMS = [f"XCOM-DGM-{number:03d}" for number in range(1, 6)]
REQUIRED_USER_STORIES = ["US1", "US2", "US3", "US4"]
# Invariants whose absence or weakening is an explicit safety-boundary failure:
# every declared safety/neutrality/dependency invariant plus INV-03 and INV-06.
REQUIRED_SAFETY_INVARIANTS = [
    "XCOM-INV-03",
    "XCOM-INV-06",
    "XCOM-INV-08",
    "XCOM-INV-11",
    "XCOM-INV-12",
    "XCOM-INV-13",
    "XCOM-INV-15",
]
REQUIRED_DIRECTION_INVARIANTS = ["XCOM-INV-11", "XCOM-INV-12"]

# Accepted requirement anchors a component may cite in ``requirement_links`` beside a
# T008 register id, per ``specs/007-xcom-core/spec.md``: FR-001..FR-035, SC-001..SC-011,
# and user stories US1..US4. This is a closed set, so an anchor such as ``FR-999`` that
# merely matches the FR-/SC-/US pattern is rejected (T009-IR-04).
ACCEPTED_FR_ANCHORS = {f"FR-{number:03d}" for number in range(1, 36)}
ACCEPTED_SC_ANCHORS = {f"SC-{number:03d}" for number in range(1, 12)}
ACCEPTED_US_ANCHORS = {"US1", "US2", "US3", "US4"}
ACCEPTED_REQUIREMENT_ANCHORS = (
    ACCEPTED_FR_ANCHORS | ACCEPTED_SC_ANCHORS | ACCEPTED_US_ANCHORS
)

# Required safety-boundary invariants pinned to their accepted ``(kind, statement)``
# content, not merely their presence (T009-IR-03). Sources: ``data-model.md`` invariants
# 3/6/8 (INV-03/06/08); Constitution art. II/VIII and ADR-0018 (INV-11/12); ``spec.md``
# FR-028/FR-032 (INV-13/15). Rewriting one to permit a TCP listener, make the permit
# optional, or default observation to payload capture is a ``SAFETY_INVALID`` failure.
EXPECTED_REQUIRED_INVARIANTS = {
    "XCOM-INV-03": (
        "data-model",
        "Synthetic origin survives routing and observation.",
    ),
    "XCOM-INV-06": (
        "data-model",
        "Metadata-only observation contains no payload bytes.",
    ),
    "XCOM-INV-08": (
        "safety",
        "Local tool transport access never replaces validation-permit checks.",
    ),
    "XCOM-INV-11": (
        "dependency",
        "Dependencies flow one-way from blueprints to domain profiles to XDL/platform "
        "APIs to runtime abstractions.",
    ),
    "XCOM-INV-12": (
        "neutrality",
        "Core components contain no domain-specific primitive.",
    ),
    "XCOM-INV-13": (
        "safety",
        "The first proof exposes no TCP listener except the host-protected local tool "
        "gateway.",
    ),
    "XCOM-INV-15": (
        "safety",
        "The first proof executes no legacy workload and contacts no external network "
        "peer.",
    ),
}

BOUNDARY_CONTRACT_KINDS = {
    "data": {"schema"},
    "artifact": {"schema", "cross-language-schema"},
    "language": {"cross-language-schema"},
    "in-process": {"in-process-cpp"},
    "realization": {"in-process-cpp"},
    "ipc": {"external-rpc"},
    "trust": {"in-process-cpp", "external-rpc", "cross-language-schema"},
}

UPSTREAM_LAYERS = {"xdl-input", "build-time", "derived-artifact"}
RUNTIME_LAYERS = {"data-plane", "boundary", "edge"}
CORE_LAYERS = {"data-plane", "boundary", "edge"}
PYTHON_LAYERS = {"xdl-input", "build-time"}
SCOPES = ("first-proof", "later")

BASELINE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TASK_RE = re.compile(r"^T\d{3}$")
CMP_ID_RE = re.compile(r"^XCOM-CMP-\d{3}$")
XB_ID_RE = re.compile(r"^XCOM-XB-\d{3}$")
XLC_ID_RE = re.compile(r"^XCOM-XLC-\d{3}$")
DGM_ID_RE = re.compile(r"^XCOM-DGM-\d{3}$")
INV_ID_RE = re.compile(r"^XCOM-INV-\d{2}$")
REQ_ID_RE = re.compile(r"^XCOM-(?:STK|SYS-FR|SYS-SC|SW-[A-Z]+)-\d{3}$")
FR_ANCHOR_RE = re.compile(r"^FR-\d{3}$")
SC_ANCHOR_RE = re.compile(r"^SC-\d{3}$")
US_ANCHOR_RE = re.compile(r"^US[1-4]$")
DOMAIN_PRIMITIVE_RE = re.compile(r"\b(?:ECU|CAN|SOME/IP|Zenoh|AUTOSAR|FlexRay|MOST)\b")

PUBLIC_SAFETY_PATTERNS = (
    (
        "absolute host path",
        re.compile(
            r"(?<![\w/])/(?:home|Users|root|mnt|opt|var|tmp|etc|usr)/"
            r"|(?:^|[\s\"'`=:(\[])[A-Za-z]:\\\\"
        ),
    ),
    (
        "private IPv4 address",
        re.compile(
            r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
            r"|192\.168\.\d{1,3}\.\d{1,3}"
            r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
        ),
    ),
    (
        "credential assignment",
        re.compile(
            r"(?i)\b(?:password|passwd|passphrase|api[_-]?key|secret|token"
            r"|credential|private[_-]?key)\s*[:=]"
        ),
    ),
    (
        "private-key marker",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ),
    (
        "unbounded payload token",
        re.compile(r"[A-Za-z0-9+/=_-]{240,}"),
    ),
)


class Findings:
    """Collect classified diagnostics and compute the precedence exit code."""

    def __init__(self) -> None:
        self.by_class: dict[int, list[str]] = {}

    def add(self, exit_class: int, message: str) -> None:
        self.by_class.setdefault(exit_class, []).append(message)

    def exit_code(self) -> int:
        return min(self.by_class) if self.by_class else EXIT_OK

    def diagnostics(self) -> list[str]:
        lines: list[str] = []
        for exit_class in sorted(self.by_class):
            for message in sorted(self.by_class[exit_class]):
                lines.append(f"[{CLASS_NAMES[exit_class]}] {message}")
        return lines


def serialize(model: dict) -> str:
    """Return the canonical byte-stable JSON serialization of a model."""

    return json.dumps(model, indent=2, ensure_ascii=False) + "\n"


def _md_cell(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _mermaid_component(diagram: dict, component_names: dict[str, str]) -> str:
    lines = ["flowchart TB"]
    for component_id in diagram["participants"]:
        alias = component_id.replace("-", "_")
        lines.append(f'  {alias}["{component_id} {component_names.get(component_id, "")}"]')
    return "\n".join(lines)


def _mermaid_sequence(diagram: dict) -> str:
    lines = ["sequenceDiagram"]
    for component_id in diagram["participants"]:
        lines.append(f"  participant {component_id.replace('-', '_')} as {component_id}")
    for step in diagram["steps"]:
        source = step["from"].replace("-", "_")
        target = step["to"].replace("-", "_")
        lines.append(f"  {source}->>{target}: {step['boundary']} {step['note']}")
    return "\n".join(lines)


def project_markdown(model: dict) -> str:
    """Return the deterministic Markdown projection of a model."""

    component_names = {
        component["id"]: component["name"] for component in model["components"]
    }
    lines: list[str] = []
    lines.append("# X-COM Architecture Contract Model — Deterministic Projection")
    lines.append("")
    lines.append(
        "> Generated deterministically from `architecture-model.json` (schema version 1)"
    )
    lines.append(
        "> by `scripts/validate_xcom_architecture_contracts.py`. Do not edit by hand; run"
    )
    lines.append("> `--check-human` to confirm this projection is exact.")
    lines.append("")

    lines.append("## 1. Identity")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Task | {model['task_id']} |")
    lines.append(f"| Capability | {model['capability']} |")
    lines.append(f"| Baseline revision | `{model['baseline_revision']}` |")
    lines.append(f"| Candidate revision rule | {_md_cell(model['candidate_revision_rule'])} |")
    counts = model["counts"]
    for family, label in (
        ("components", "Components"),
        ("boundaries", "Boundaries"),
        ("contracts", "Contracts"),
        ("diagrams", "Diagrams"),
        ("invariants", "Invariants"),
    ):
        lines.append(f"| {label} | {counts[family]} |")
    lines.append(
        f"| REF-002 disposition | {model['ref002']['disposition']} "
        f"(promoted: {len(model['ref002']['promoted'])}) |"
    )
    lines.append("")

    lines.append("## 2. Components")
    lines.append("")
    lines.append("| Id | Name | Layer | Language | Scope | Owning slice | Maturity |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for component in model["components"]:
        lines.append(
            "| {id} | {name} | {layer} | {language} | {scope} | {owning_slice} | "
            "{maturity} |".format(
                id=component["id"],
                name=_md_cell(component["name"]),
                layer=component["layer"],
                language=component["language"],
                scope=component["scope"],
                owning_slice=component["owning_slice"],
                maturity=component["maturity"],
            )
        )
    lines.append("")

    lines.append("## 3. Boundaries")
    lines.append("")
    lines.append(
        "| Id | Kind | From → To | Languages | Direction | Contract | "
        "Authorization | Scope | Maturity |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for boundary in model["boundaries"]:
        lines.append(
            "| {id} | {kind} | {source} → {target} | {src_lang} → {dst_lang} | "
            "{direction} | {contract} | {authorization} | {scope} | {maturity} |".format(
                id=boundary["id"],
                kind=boundary["kind"],
                source=boundary["from_component"],
                target=boundary["to_component"],
                src_lang=boundary["from_language"],
                dst_lang=boundary["to_language"],
                direction=boundary["direction"],
                contract=boundary["contract"],
                authorization=boundary["authorization"],
                scope=boundary["scope"],
                maturity=boundary["maturity"],
            )
        )
    lines.append("")

    lines.append("## 4. Contracts")
    lines.append("")
    lines.append(
        "| Id | Kind | Version | Canonical artifact | Unknown-field policy | Maturity |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for contract in model["contracts"]:
        lines.append(
            "| {id} | {kind} | {version} | {artifact} | {policy} | {maturity} |".format(
                id=contract["id"],
                kind=contract["kind"],
                version=contract["version"],
                artifact=_md_cell(contract["canonical_artifact"]),
                policy=contract["unknown_field_policy"],
                maturity=contract["maturity"],
            )
        )
    lines.append("")

    lines.append("## 5. Invariants")
    lines.append("")
    lines.append("| Id | Kind | Statement | Enforcement |")
    lines.append("| --- | --- | --- | --- |")
    for invariant in model["invariants"]:
        lines.append(
            "| {id} | {kind} | {statement} | {enforcement} |".format(
                id=invariant["id"],
                kind=invariant["kind"],
                statement=_md_cell(invariant["statement"]),
                enforcement=_md_cell(invariant["enforcement"]),
            )
        )
    lines.append("")

    lines.append("## 6. Diagrams")
    lines.append("")
    for diagram in model["diagrams"]:
        lines.append(f"### {diagram['id']} — {_md_cell(diagram['title'])}")
        lines.append("")
        lines.append(f"- Kind: `{diagram['kind']}`")
        lines.append(f"- User story: `{diagram['user_story']}`")
        lines.append("")
        lines.append("```mermaid")
        if diagram["kind"] == "component":
            lines.append(_mermaid_component(diagram, component_names))
        else:
            lines.append(_mermaid_sequence(diagram))
        lines.append("```")
        lines.append("")

    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def _sorted_unique_strings(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item for item in value)
        and value == sorted(value)
        and len(set(value)) == len(value)
    )


def _ids_of(entries: object) -> list:
    """Return the family ids coerced to hashable strings.

    Coercion keeps ordering, uniqueness, and set-difference checks total even when a
    malformed model carries a non-string id; ``_check_model_schema`` reports the
    non-string id itself as a ``SCHEMA_INVALID`` finding (T009-IR-02).
    """

    if not isinstance(entries, list):
        return []
    return [str(entry.get("id")) for entry in entries if isinstance(entry, dict)]


def _resolves(value: object, known: set) -> bool:
    return isinstance(value, str) and value in known


def _check_model_schema(model: object, findings: Findings) -> None:
    if not isinstance(model, dict):
        findings.add(EXIT_SCHEMA, "architecture-model.json root is not a JSON object")
        return
    if list(model.keys()) != MODEL_TOP:
        findings.add(
            EXIT_SCHEMA,
            "architecture-model.json top-level field set or order differs from the schema",
        )
    if model.get("schema_version") != SCHEMA_VERSION:
        findings.add(EXIT_SCHEMA, "schema_version must be 1")
    if model.get("task_id") != TASK_ID:
        findings.add(EXIT_SCHEMA, "task_id must be T009")
    if model.get("capability") != CAPABILITY:
        findings.add(EXIT_SCHEMA, "capability must be 007-xcom-core")
    if not isinstance(model.get("baseline_revision"), str) or not str(
        model.get("baseline_revision")
    ).strip():
        findings.add(EXIT_SCHEMA, "baseline_revision must be a non-empty string")
    if not isinstance(model.get("candidate_revision_rule"), str) or not str(
        model.get("candidate_revision_rule")
    ).strip():
        findings.add(EXIT_SCHEMA, "candidate_revision_rule must be a non-empty string")
    for field, expected in VOCABULARY_FIELDS.items():
        if model.get(field) != expected:
            findings.add(EXIT_SCHEMA, f"{field} must equal the declared closed set")
    records = model.get("authorization_records")
    if not _sorted_unique_strings(records):
        findings.add(
            EXIT_SCHEMA, "authorization_records must be a sorted, duplicate-free string array"
        )
    ref002 = model.get("ref002")
    if not isinstance(ref002, dict) or list(ref002.keys()) != REF002_FIELDS:
        findings.add(EXIT_SCHEMA, "ref002 must declare disposition, promoted, source in order")
    else:
        if not isinstance(ref002["disposition"], str) or not ref002["disposition"].strip():
            findings.add(EXIT_SCHEMA, "ref002.disposition must be a non-empty string")
        if not isinstance(ref002["promoted"], list):
            findings.add(EXIT_SCHEMA, "ref002.promoted must be an array")
        if not isinstance(ref002["source"], str) or not ref002["source"].strip():
            findings.add(EXIT_SCHEMA, "ref002.source must be a non-empty string")
    counts = model.get("counts")
    if not isinstance(counts, dict):
        findings.add(EXIT_SCHEMA, "counts must be an object")
    for family in FAMILIES:
        entries = model.get(family)
        if not isinstance(entries, list) or not entries:
            findings.add(EXIT_SCHEMA, f"{family} must be a non-empty array")
            continue
        if isinstance(counts, dict) and counts.get(family) != len(entries):
            findings.add(EXIT_SCHEMA, f"counts.{family} does not match the {family} length")
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                findings.add(EXIT_SCHEMA, f"{family}[{index}] is not an object")
                continue
            entry_id = entry.get("id")
            if not isinstance(entry_id, str) or not entry_id:
                findings.add(
                    EXIT_SCHEMA, f"{family}[{index}].id must be a non-empty string"
                )


def _check_ordering(model: dict, findings: Findings) -> None:
    for family in FAMILIES:
        entries = model.get(family)
        if not isinstance(entries, list):
            continue
        ids = _ids_of(entries)
        if len(ids) != len(entries):
            continue
        if ids != sorted(ids):
            findings.add(EXIT_SCHEMA, f"{family} must be sorted by id in ascending order")


def _check_identity(model: dict, findings: Findings) -> None:
    components = model.get("components")
    if not isinstance(components, list):
        return
    ids = _ids_of(components)
    if sorted(ids, key=str) != REQUIRED_COMPONENTS:
        findings.add(
            EXIT_IDENTITY, "required component set must be exactly XCOM-CMP-001..013"
        )
    if len(ids) != len(set(ids)):
        findings.add(EXIT_IDENTITY, "component ids must be unique")
    for index, component in enumerate(components):
        if not isinstance(component, dict):
            findings.add(EXIT_IDENTITY, f"components[{index}] is not an object")
            continue
        label = component.get("id") if isinstance(component.get("id"), str) else index
        if list(component.keys()) != COMPONENT_FIELDS:
            findings.add(EXIT_IDENTITY, f"components[{index}] field set or order differs")
        component_id = component.get("id")
        if not isinstance(component_id, str) or not CMP_ID_RE.fullmatch(component_id):
            findings.add(EXIT_IDENTITY, f"components[{index}].id is not XCOM-CMP-###")
        for field in ("name", "responsibility", "owning_slice"):
            value = component.get(field)
            if not isinstance(value, str) or not value.strip():
                findings.add(EXIT_IDENTITY, f"{label}.{field} must be a non-empty string")
        if component.get("layer") not in LAYER_VOCABULARY:
            findings.add(EXIT_IDENTITY, f"{label}.layer is not in the layer vocabulary")
        if component.get("language") not in LANGUAGE_VOCABULARY:
            findings.add(
                EXIT_IDENTITY, f"{label}.language is not in the language vocabulary"
            )
        if component.get("scope") not in SCOPES:
            findings.add(EXIT_IDENTITY, f"{label}.scope must be first-proof or later")
        if component.get("maturity") not in MATURITY_VOCABULARY:
            findings.add(EXIT_IDENTITY, f"{label}.maturity is not in the maturity vocabulary")
        if not isinstance(component.get("intra_layer"), bool):
            findings.add(EXIT_IDENTITY, f"{label}.intra_layer must be a boolean")
        layer = component.get("layer")
        owning_slice = component.get("owning_slice")
        tasks = component.get("owning_tasks")
        if layer == "external" and owning_slice != "external":
            findings.add(EXIT_IDENTITY, f"{label} external layer must be owned by external")
        if layer == "downstream" and owning_slice != "downstream":
            findings.add(
                EXIT_IDENTITY, f"{label} downstream layer must be owned by downstream"
            )
        if owning_slice in ("external", "downstream"):
            if tasks != []:
                findings.add(
                    EXIT_IDENTITY,
                    f"{label} external/downstream component must own no tasks",
                )
        elif not (
            isinstance(tasks, list)
            and tasks
            and all(isinstance(task, str) and TASK_RE.fullmatch(task) for task in tasks)
            and tasks == sorted(tasks)
            and len(set(tasks)) == len(tasks)
        ):
            findings.add(
                EXIT_IDENTITY,
                f"{label}.owning_tasks must be a sorted unique non-empty T0xx array",
            )
        paths = component.get("artifact_paths")
        if not isinstance(paths, list) or not paths:
            findings.add(EXIT_IDENTITY, f"{label} must declare at least one artifact path")
        else:
            path_values = [entry.get("path") for entry in paths if isinstance(entry, dict)]
            if len(path_values) != len(paths) or not all(
                isinstance(value, str) and value.strip() for value in path_values
            ):
                findings.add(EXIT_IDENTITY, f"{label}.artifact_paths entries must carry a path")
            else:
                if path_values != sorted(path_values):
                    findings.add(
                        EXIT_IDENTITY, f"{label}.artifact_paths must be sorted by path"
                    )
                if len(set(path_values)) != len(path_values):
                    findings.add(
                        EXIT_IDENTITY, f"{label}.artifact_paths must not repeat a path"
                    )
            for entry in paths:
                if not isinstance(entry, dict):
                    continue
                if list(entry.keys()) != PATH_FIELDS:
                    findings.add(EXIT_IDENTITY, f"{label}.artifact_paths entry field set differs")
                    continue
                if entry.get("status") not in ("established", "planned"):
                    findings.add(
                        EXIT_IDENTITY,
                        f"{label}.artifact_paths entry status must be established/planned",
                    )
                if entry.get("path") == "n/a" and layer not in ("external", "downstream"):
                    findings.add(
                        EXIT_IDENTITY,
                        f"{label} may use the n/a path marker only for external/downstream",
                    )
        links = component.get("requirement_links")
        if not isinstance(links, list) or not links or not all(
            isinstance(link, str) and link for link in links
        ):
            findings.add(EXIT_IDENTITY, f"{label}.requirement_links must be non-empty")
        adrs = component.get("governing_adrs")
        if not isinstance(adrs, list) or not adrs:
            findings.add(EXIT_IDENTITY, f"{label}.governing_adrs must be non-empty")
        constraints = component.get("constraints")
        if not isinstance(constraints, list) or not constraints:
            findings.add(EXIT_IDENTITY, f"{label}.constraints must be non-empty")
        accepted = component.get("accepted_revision")
        if accepted is not None and not (
            isinstance(accepted, str) and BASELINE_SHA_RE.fullmatch(accepted)
        ):
            findings.add(
                EXIT_IDENTITY, f"{label}.accepted_revision must be null or a 40-hex SHA"
            )
        reconciliation = component.get("reconciliation")
        if reconciliation is not None and not (
            isinstance(reconciliation, str) and reconciliation.strip()
        ):
            findings.add(
                EXIT_IDENTITY, f"{label}.reconciliation must be null or a non-empty string"
            )


def _check_paths(model: dict, findings: Findings) -> None:
    components = model.get("components")
    if not isinstance(components, list):
        return
    for component in components:
        if not isinstance(component, dict):
            continue
        component_id = component.get("id")
        for entry in component.get("artifact_paths", []) or []:
            if not isinstance(entry, dict):
                continue
            path = entry.get("path")
            status = entry.get("status")
            if not isinstance(path, str) or path == "n/a":
                continue
            target = ROOT / path
            if status == "established" and not target.exists():
                findings.add(
                    EXIT_PATH,
                    f"{component_id} established path is absent from the tree: {path}",
                )
            if status == "planned" and target.exists():
                findings.add(
                    EXIT_PATH,
                    f"{component_id} planned path is already present in the tree: {path}",
                )


def _check_boundaries(model: dict, findings: Findings) -> None:
    boundaries = model.get("boundaries")
    if not isinstance(boundaries, list):
        return
    component_ids = set(_ids_of(model.get("components")))
    ids = _ids_of(boundaries)
    if sorted(ids, key=str) != REQUIRED_BOUNDARIES:
        findings.add(EXIT_BOUNDARY, "required boundary set must be exactly XCOM-XB-001..011")
    if len(ids) != len(set(ids)):
        findings.add(EXIT_BOUNDARY, "boundary ids must be unique")
    for index, boundary in enumerate(boundaries):
        if not isinstance(boundary, dict):
            findings.add(EXIT_BOUNDARY, f"boundaries[{index}] is not an object")
            continue
        label = boundary.get("id") if isinstance(boundary.get("id"), str) else index
        if list(boundary.keys()) != BOUNDARY_FIELDS:
            findings.add(EXIT_BOUNDARY, f"boundaries[{index}] field set or order differs")
        boundary_id = boundary.get("id")
        if not isinstance(boundary_id, str) or not XB_ID_RE.fullmatch(boundary_id):
            findings.add(EXIT_BOUNDARY, f"boundaries[{index}].id is not XCOM-XB-###")
        if not isinstance(boundary.get("name"), str) or not boundary["name"].strip():
            findings.add(EXIT_BOUNDARY, f"{label}.name must be a non-empty string")
        if boundary.get("kind") not in BOUNDARY_KIND_VOCABULARY:
            findings.add(EXIT_BOUNDARY, f"{label}.kind is not in the boundary-kind vocabulary")
        if not _resolves(boundary.get("from_component"), component_ids):
            findings.add(EXIT_BOUNDARY, f"{label}.from_component does not resolve")
        if not _resolves(boundary.get("to_component"), component_ids):
            findings.add(EXIT_BOUNDARY, f"{label}.to_component does not resolve")
        for field in ("from_language", "to_language"):
            if boundary.get(field) not in LANGUAGE_VOCABULARY:
                findings.add(EXIT_BOUNDARY, f"{label}.{field} is not in the language vocabulary")
        if (
            boundary.get("kind") == "language"
            and boundary.get("from_language") == boundary.get("to_language")
        ):
            findings.add(EXIT_BOUNDARY, f"{label} language boundary endpoints must differ")
        if boundary.get("direction") not in DIRECTION_VOCABULARY:
            findings.add(EXIT_BOUNDARY, f"{label}.direction is not in the direction vocabulary")
        if boundary.get("scope") not in SCOPES:
            findings.add(EXIT_BOUNDARY, f"{label}.scope must be first-proof or later")
        if not isinstance(boundary.get("contract"), str) or not boundary["contract"].strip():
            findings.add(EXIT_BOUNDARY, f"{label}.contract must be a non-empty string")
        if boundary.get("authorization") not in AUTHORIZATION_VOCABULARY:
            findings.add(
                EXIT_BOUNDARY, f"{label}.authorization is not in the authorization vocabulary"
            )
        safety = boundary.get("safety")
        if not isinstance(safety, list) or not safety or not all(
            isinstance(item, str) and item for item in safety
        ):
            findings.add(EXIT_BOUNDARY, f"{label}.safety must be a non-empty string array")
        if not isinstance(boundary.get("failure_semantics"), str) or not boundary[
            "failure_semantics"
        ].strip():
            findings.add(EXIT_BOUNDARY, f"{label}.failure_semantics must be non-empty")
        if boundary.get("maturity") not in MATURITY_VOCABULARY:
            findings.add(EXIT_BOUNDARY, f"{label}.maturity is not in the maturity vocabulary")
        accepted = boundary.get("accepted_revision")
        if accepted is not None and not (
            isinstance(accepted, str) and BASELINE_SHA_RE.fullmatch(accepted)
        ):
            findings.add(
                EXIT_BOUNDARY, f"{label}.accepted_revision must be null or a 40-hex SHA"
            )


def _check_contracts(model: dict, findings: Findings) -> None:
    contracts = model.get("contracts")
    if not isinstance(contracts, list):
        return
    component_ids = set(_ids_of(model.get("components")))
    ids = _ids_of(contracts)
    if sorted(ids, key=str) != REQUIRED_CONTRACTS:
        findings.add(EXIT_CONTRACT, "required contract set must be exactly XCOM-XLC-001..006")
    if len(ids) != len(set(ids)):
        findings.add(EXIT_CONTRACT, "contract ids must be unique")
    contract_by_id = {
        str(contract.get("id")): contract
        for contract in contracts
        if isinstance(contract, dict)
    }
    for index, contract in enumerate(contracts):
        if not isinstance(contract, dict):
            findings.add(EXIT_CONTRACT, f"contracts[{index}] is not an object")
            continue
        label = contract.get("id") if isinstance(contract.get("id"), str) else index
        if list(contract.keys()) != CONTRACT_FIELDS:
            findings.add(EXIT_CONTRACT, f"contracts[{index}] field set or order differs")
        contract_id = contract.get("id")
        if not isinstance(contract_id, str) or not XLC_ID_RE.fullmatch(contract_id):
            findings.add(EXIT_CONTRACT, f"contracts[{index}].id is not XCOM-XLC-###")
        if not isinstance(contract.get("name"), str) or not contract["name"].strip():
            findings.add(EXIT_CONTRACT, f"{label}.name must be a non-empty string")
        kind = contract.get("kind")
        if kind not in CONTRACT_KIND_VOCABULARY:
            findings.add(EXIT_CONTRACT, f"{label}.kind is not in the contract-kind vocabulary")
        for field in ("producer_components", "consumer_components"):
            value = contract.get(field)
            if not isinstance(value, list) or not value or not all(
                _resolves(item, component_ids) for item in value
            ):
                findings.add(EXIT_CONTRACT, f"{label}.{field} must resolve to components")
        languages = contract.get("endpoint_languages")
        if not _sorted_unique_strings(languages) or not all(
            language in LANGUAGE_VOCABULARY for language in languages or []
        ):
            findings.add(
                EXIT_CONTRACT,
                f"{label}.endpoint_languages must be a sorted non-empty subset of the language "
                "vocabulary",
            )
        for field in ("version", "encoding", "evolution_rule"):
            value = contract.get(field)
            if not isinstance(value, str) or not value.strip():
                findings.add(EXIT_CONTRACT, f"{label}.{field} must be a non-empty string")
        policy = contract.get("unknown_field_policy")
        if kind == "in-process-cpp":
            if policy not in ("fail-closed", "n/a"):
                findings.add(
                    EXIT_CONTRACT,
                    f"{label}.unknown_field_policy must be fail-closed or n/a",
                )
        elif policy != "fail-closed":
            findings.add(
                EXIT_CONTRACT, f"{label}.unknown_field_policy must be fail-closed"
            )
        adrs = contract.get("governing_adrs")
        if not isinstance(adrs, list) or not adrs:
            findings.add(EXIT_CONTRACT, f"{label}.governing_adrs must be non-empty")
        if contract.get("maturity") not in MATURITY_VOCABULARY:
            findings.add(EXIT_CONTRACT, f"{label}.maturity is not in the maturity vocabulary")
        accepted = contract.get("accepted_revision")
        if accepted is not None and not (
            isinstance(accepted, str) and BASELINE_SHA_RE.fullmatch(accepted)
        ):
            findings.add(
                EXIT_CONTRACT, f"{label}.accepted_revision must be null or a 40-hex SHA"
            )
    for boundary in model.get("boundaries", []) or []:
        if not isinstance(boundary, dict):
            continue
        label = boundary.get("id")
        referral = boundary.get("contract")
        if not isinstance(referral, str):
            continue
        contract = contract_by_id.get(referral)
        if contract is None:
            findings.add(
                EXIT_CONTRACT,
                f"{label}.contract={referral} does not resolve to a declared contract",
            )
            continue
        allowed = BOUNDARY_CONTRACT_KINDS.get(boundary.get("kind"))
        if allowed is not None and contract.get("kind") not in allowed:
            findings.add(
                EXIT_CONTRACT,
                f"{label} boundary kind {boundary.get('kind')} is incompatible with "
                f"contract kind {contract.get('kind')}",
            )
        endpoints = contract.get("endpoint_languages")
        if isinstance(endpoints, list):
            for field in ("from_language", "to_language"):
                language = boundary.get(field)
                if language not in endpoints:
                    findings.add(
                        EXIT_CONTRACT,
                        f"{label}.{field}={language} is not in {referral}.endpoint_languages",
                    )


def _check_diagrams(model: dict, findings: Findings) -> None:
    diagrams = model.get("diagrams")
    if not isinstance(diagrams, list):
        return
    component_ids = set(_ids_of(model.get("components")))
    boundary_ids = set(_ids_of(model.get("boundaries")))
    contract_ids = set(_ids_of(model.get("contracts")))
    boundary_by_id = {
        str(boundary.get("id")): boundary
        for boundary in model.get("boundaries", []) or []
        if isinstance(boundary, dict)
    }
    ids = _ids_of(diagrams)
    if sorted(ids, key=str) != REQUIRED_DIAGRAMS:
        findings.add(EXIT_DIAGRAM, "required diagram set must be exactly XCOM-DGM-001..005")
    if len(ids) != len(set(ids)):
        findings.add(EXIT_DIAGRAM, "diagram ids must be unique")
    participants_union: set = set()
    boundaries_used: set = set()
    sequence_stories: list = []
    for index, diagram in enumerate(diagrams):
        if not isinstance(diagram, dict):
            findings.add(EXIT_DIAGRAM, f"diagrams[{index}] is not an object")
            continue
        label = diagram.get("id") if isinstance(diagram.get("id"), str) else index
        if list(diagram.keys()) != DIAGRAM_FIELDS:
            findings.add(EXIT_DIAGRAM, f"diagrams[{index}] field set or order differs")
        diagram_id = diagram.get("id")
        if not isinstance(diagram_id, str) or not DGM_ID_RE.fullmatch(diagram_id):
            findings.add(EXIT_DIAGRAM, f"diagrams[{index}].id is not XCOM-DGM-###")
        kind = diagram.get("kind")
        if kind not in DIAGRAM_KIND_VOCABULARY:
            findings.add(EXIT_DIAGRAM, f"{label}.kind is not in the diagram-kind vocabulary")
        if not isinstance(diagram.get("title"), str) or not diagram["title"].strip():
            findings.add(EXIT_DIAGRAM, f"{label}.title must be a non-empty string")
        participants = diagram.get("participants")
        if not _sorted_unique_strings(participants) or not all(
            participant in component_ids for participant in participants or []
        ):
            findings.add(
                EXIT_DIAGRAM,
                f"{label}.participants must be a sorted unique set of declared components",
            )
        else:
            participants_union |= set(participants)
        steps = diagram.get("steps")
        if kind == "component":
            if diagram.get("user_story") != "-":
                findings.add(EXIT_DIAGRAM, f"{label}.user_story must be '-' for a component view")
            if steps != []:
                findings.add(EXIT_DIAGRAM, f"{label} component view must have no steps")
        elif kind == "sequence":
            story = diagram.get("user_story")
            if story not in REQUIRED_USER_STORIES:
                findings.add(EXIT_DIAGRAM, f"{label}.user_story must be US1..US4")
            else:
                sequence_stories.append(story)
            if not isinstance(steps, list) or not steps:
                findings.add(EXIT_DIAGRAM, f"{label} sequence view must have steps")
        if isinstance(steps, list):
            for step in steps:
                if not isinstance(step, dict) or list(step.keys()) != STEP_FIELDS:
                    findings.add(EXIT_DIAGRAM, f"{label} step field set differs")
                    continue
                if isinstance(participants, list):
                    if step.get("from") not in participants or step.get("to") not in participants:
                        findings.add(
                            EXIT_DIAGRAM,
                            f"{label} step endpoints must be declared participants",
                        )
                if step.get("boundary") not in boundary_ids:
                    findings.add(
                        EXIT_DIAGRAM,
                        f"{label} step boundary={step.get('boundary')} is not a declared boundary",
                    )
                else:
                    boundaries_used.add(step.get("boundary"))
                if not isinstance(step.get("note"), str) or not step["note"].strip():
                    findings.add(EXIT_DIAGRAM, f"{label} step note must be non-empty")
    for component_id in sorted(component_ids - participants_union):
        findings.add(
            EXIT_DIAGRAM, f"component {component_id} is not covered by any diagram"
        )
    for boundary_id in sorted(boundary_ids - boundaries_used):
        findings.add(
            EXIT_DIAGRAM, f"boundary {boundary_id} is not covered by any diagram step"
        )
    referenced_contracts = {
        boundary_by_id[boundary_id].get("contract")
        for boundary_id in boundaries_used
        if boundary_id in boundary_by_id
    }
    for contract_id in sorted(contract_ids - referenced_contracts):
        findings.add(
            EXIT_DIAGRAM,
            f"contract {contract_id} is not referenced by any covered boundary",
        )
    if sorted(sequence_stories) != REQUIRED_USER_STORIES:
        findings.add(EXIT_DIAGRAM, "US1..US4 must each have exactly one sequence diagram")


def _check_governance(model: dict, findings: Findings) -> None:
    for component in model.get("components", []) or []:
        if not isinstance(component, dict):
            continue
        for adr in component.get("governing_adrs", []) or []:
            if adr not in ADR_VOCABULARY:
                findings.add(
                    EXIT_GOVERNANCE,
                    f"{component.get('id')} cites an unknown governing ADR {adr}",
                )
    for contract in model.get("contracts", []) or []:
        if not isinstance(contract, dict):
            continue
        for adr in contract.get("governing_adrs", []) or []:
            if adr not in ADR_VOCABULARY:
                findings.add(
                    EXIT_GOVERNANCE,
                    f"{contract.get('id')} cites an unknown governing ADR {adr}",
                )
    ref002 = model.get("ref002")
    if isinstance(ref002, dict):
        if ref002.get("disposition") != "unchanged":
            findings.add(EXIT_GOVERNANCE, "ref002.disposition must be unchanged")
        promoted = ref002.get("promoted")
        if not isinstance(promoted, list) or promoted:
            findings.add(
                EXIT_GOVERNANCE, "ref002.promoted must be empty (no REF-002 promotion)"
            )


def _check_neutrality(model: dict, findings: Findings) -> None:
    components = model.get("components")
    if not isinstance(components, list):
        return
    by_id = {
        str(component.get("id")): component
        for component in components
        if isinstance(component, dict)
    }
    for component in components:
        if not isinstance(component, dict):
            continue
        label = component.get("id")
        if component.get("language") == "python" and component.get("layer") not in PYTHON_LAYERS:
            findings.add(
                EXIT_GOVERNANCE,
                f"{label} python code must be confined to the xdl-input/build-time layers",
            )
        if component.get("layer") == "data-plane" and component.get("language") != "cpp":
            findings.add(EXIT_GOVERNANCE, f"{label} data-plane component must be C++")
        if component.get("layer") in CORE_LAYERS:
            text = " ".join(
                [
                    str(component.get("name", "")),
                    str(component.get("responsibility", "")),
                    " ".join(component.get("constraints", []) or []),
                ]
            )
            if DOMAIN_PRIMITIVE_RE.search(text):
                findings.add(
                    EXIT_GOVERNANCE,
                    f"{label} core component names a domain-specific primitive",
                )
    for boundary in model.get("boundaries", []) or []:
        if not isinstance(boundary, dict):
            continue
        source = by_id.get(boundary.get("from_component"))
        target = by_id.get(boundary.get("to_component"))
        if not source or not target:
            continue
        if source.get("layer") in RUNTIME_LAYERS and target.get("layer") in UPSTREAM_LAYERS:
            findings.add(
                EXIT_GOVERNANCE,
                f"{boundary.get('id')} introduces a reverse dependency "
                f"({source.get('layer')} -> {target.get('layer')})",
            )
    invariant_ids = {
        str(invariant.get("id"))
        for invariant in model.get("invariants", []) or []
        if isinstance(invariant, dict)
    }
    for invariant_id in REQUIRED_DIRECTION_INVARIANTS:
        if invariant_id not in invariant_ids:
            findings.add(
                EXIT_GOVERNANCE,
                f"required dependency/neutrality invariant {invariant_id} is missing",
            )


def _check_safety(model: dict, findings: Findings) -> None:
    invariants = model.get("invariants")
    if not isinstance(invariants, list):
        return
    known_targets = set(_ids_of(model.get("components"))) | set(_ids_of(model.get("boundaries")))
    ids = _ids_of(invariants)
    if len(ids) != len(set(ids)):
        findings.add(EXIT_SAFETY, "invariant ids must be unique")
    by_id = {}
    for index, invariant in enumerate(invariants):
        if not isinstance(invariant, dict):
            findings.add(EXIT_SAFETY, f"invariants[{index}] is not an object")
            continue
        label = invariant.get("id") if isinstance(invariant.get("id"), str) else index
        if list(invariant.keys()) != INVARIANT_FIELDS:
            findings.add(EXIT_SAFETY, f"invariants[{index}] field set or order differs")
        invariant_id = invariant.get("id")
        if not isinstance(invariant_id, str) or not INV_ID_RE.fullmatch(invariant_id):
            findings.add(EXIT_SAFETY, f"invariants[{index}].id is not XCOM-INV-##")
        else:
            by_id[invariant_id] = invariant
        if invariant.get("kind") not in INVARIANT_KIND_VOCABULARY:
            findings.add(EXIT_SAFETY, f"{label}.kind is not in the invariant-kind vocabulary")
        if not isinstance(invariant.get("statement"), str) or not invariant["statement"].strip():
            findings.add(EXIT_SAFETY, f"{label}.statement must be a non-empty string")
        if not isinstance(invariant.get("source"), str) or not invariant["source"].strip():
            findings.add(EXIT_SAFETY, f"{label}.source must be a non-empty string")
        enforcement = invariant.get("enforcement")
        if not isinstance(enforcement, str) or not enforcement.strip():
            findings.add(EXIT_SAFETY, f"{label}.enforcement must be a non-empty string")
        applies = invariant.get("applies_to")
        if not isinstance(applies, list) or not applies or not all(
            _resolves(target, known_targets) for target in applies
        ):
            findings.add(
                EXIT_SAFETY, f"{label}.applies_to must resolve to components or boundaries"
            )
    for invariant_id in REQUIRED_SAFETY_INVARIANTS:
        if invariant_id not in by_id:
            findings.add(
                EXIT_SAFETY, f"required safety-boundary invariant {invariant_id} is missing"
            )
            continue
        invariant = by_id[invariant_id]
        expected_kind, expected_statement = EXPECTED_REQUIRED_INVARIANTS[invariant_id]
        if invariant.get("kind") != expected_kind:
            findings.add(
                EXIT_SAFETY,
                f"required safety-boundary invariant {invariant_id} must have kind "
                f"{expected_kind}",
            )
        statement = invariant.get("statement")
        if not isinstance(statement, str) or statement.strip() != expected_statement:
            findings.add(
                EXIT_SAFETY,
                f"required safety-boundary invariant {invariant_id} statement must be the "
                "accepted text, not a weakened restatement",
            )
        if not isinstance(invariant.get("enforcement"), str) or not invariant[
            "enforcement"
        ].strip():
            findings.add(EXIT_SAFETY, f"{invariant_id}.enforcement must be non-empty")


def _accepted_reconciliation(ownership: object) -> tuple[set, dict]:
    accepted_tasks: set = set()
    revisions: dict = {}
    if not isinstance(ownership, dict):
        return accepted_tasks, revisions
    for slice_record in ownership.get("slices", []) or []:
        if not isinstance(slice_record, dict):
            continue
        for task, entry in (slice_record.get("reconciliation", {}) or {}).items():
            if isinstance(entry, dict) and entry.get("status") == "accepted":
                accepted_tasks.add(task)
                revision = entry.get("revision")
                if isinstance(revision, str) and BASELINE_SHA_RE.fullmatch(revision):
                    revisions[task] = revision
    return accepted_tasks, revisions


def _check_maturity(model: dict, ownership: object, findings: Findings) -> None:
    accepted_tasks, task_revisions = _accepted_reconciliation(ownership)
    accepted_revisions = set(task_revisions.values())
    components = model.get("components")
    if isinstance(components, list):
        for component in components:
            if not isinstance(component, dict):
                continue
            label = component.get("id")
            maturity = component.get("maturity")
            accepted = component.get("accepted_revision")
            if maturity == "implemented":
                if not (isinstance(accepted, str) and BASELINE_SHA_RE.fullmatch(accepted)):
                    findings.add(
                        EXIT_GOVERNANCE,
                        f"{label} is implemented without an exact accepted revision",
                    )
                elif accepted_tasks:
                    owning = set(component.get("owning_tasks") or [])
                    matched = owning & accepted_tasks
                    revisions = {task_revisions.get(task) for task in matched}
                    if not matched or accepted not in revisions:
                        findings.add(
                            EXIT_GOVERNANCE,
                            f"{label} implemented revision is not an accepted owning-task "
                            "revision",
                        )
            else:
                if accepted is not None:
                    findings.add(
                        EXIT_GOVERNANCE,
                        f"{label} is {maturity} but carries an accepted_revision",
                    )
                if maturity == "partial" and not (
                    isinstance(component.get("reconciliation"), str)
                    and component["reconciliation"].strip()
                ):
                    findings.add(
                        EXIT_GOVERNANCE,
                        f"{label} is partial without a reconciliation reason",
                    )
                if maturity != "partial" and component.get("reconciliation") is not None:
                    findings.add(
                        EXIT_GOVERNANCE,
                        f"{label} is {maturity} but carries a reconciliation reason",
                    )
    for family in ("boundaries", "contracts"):
        for record in model.get(family, []) or []:
            if not isinstance(record, dict):
                continue
            label = record.get("id")
            maturity = record.get("maturity")
            accepted = record.get("accepted_revision")
            if maturity == "implemented":
                if not (isinstance(accepted, str) and BASELINE_SHA_RE.fullmatch(accepted)):
                    findings.add(
                        EXIT_GOVERNANCE,
                        f"{label} is implemented without an exact accepted revision",
                    )
                elif accepted_revisions and accepted not in accepted_revisions:
                    findings.add(
                        EXIT_GOVERNANCE,
                        f"{label} implemented revision is not an accepted revision",
                    )
            elif accepted is not None:
                findings.add(
                    EXIT_GOVERNANCE,
                    f"{label} is {maturity} but carries an accepted_revision",
                )


def _check_binding(model: dict, requirement_register: object, findings: Findings) -> None:
    baseline = model.get("baseline_revision")
    if not isinstance(baseline, str) or not BASELINE_SHA_RE.fullmatch(baseline):
        findings.add(EXIT_BINDING, "baseline_revision is not a 40-hex lowercase SHA")
    rule = model.get("candidate_revision_rule")
    if not isinstance(rule, str) or not rule.strip():
        findings.add(EXIT_BINDING, "candidate_revision_rule must be non-empty")
    records = model.get("authorization_records")
    if isinstance(records, list):
        unknown = sorted(set(records) - set(ACCEPTED_AUTHORIZATION))
        missing = sorted(set(ACCEPTED_AUTHORIZATION) - set(records))
        if unknown:
            findings.add(EXIT_BINDING, f"authorization_records cites unknown records {unknown}")
        if missing:
            findings.add(EXIT_BINDING, f"authorization_records omits accepted records {missing}")
    if isinstance(requirement_register, dict):
        known = {
            requirement.get("id")
            for requirement in requirement_register.get("requirements", []) or []
            if isinstance(requirement, dict)
        }
        for component in model.get("components", []) or []:
            if not isinstance(component, dict):
                continue
            for link in component.get("requirement_links", []) or []:
                if not isinstance(link, str):
                    findings.add(
                        EXIT_BINDING,
                        f"{component.get('id')} requirement link {link!r} must be a string",
                    )
                    continue
                if link in known or link in ACCEPTED_REQUIREMENT_ANCHORS:
                    continue
                if (
                    FR_ANCHOR_RE.fullmatch(link)
                    or SC_ANCHOR_RE.fullmatch(link)
                    or US_ANCHOR_RE.fullmatch(link)
                ):
                    findings.add(
                        EXIT_BINDING,
                        f"{component.get('id')} requirement link {link} is not an accepted "
                        "FR-/SC-/US anchor",
                    )
                    continue
                findings.add(
                    EXIT_BINDING,
                    f"{component.get('id')} requirement link {link} does not resolve in the "
                    "T008 register or the accepted anchor set",
                )


def _check_dependencies(
    ownership: object, requirement_register: object, findings: Findings
) -> None:
    if not isinstance(ownership, dict) or not isinstance(ownership.get("slices"), list):
        findings.add(
            EXIT_BINDING,
            "dependency docs/engineering/xcom/task-ownership.json is missing, unreadable, "
            "or malformed; reconciliation state cannot be checked",
        )
    if not isinstance(requirement_register, dict) or not isinstance(
        requirement_register.get("requirements"), list
    ):
        findings.add(
            EXIT_BINDING,
            "dependency docs/engineering/xcom/t008/requirements-register.json is missing, "
            "unreadable, or malformed; requirement links cannot be checked",
        )


def _check_determinism(
    model: object, model_raw: str | None, model_md: str | None, findings: Findings
) -> None:
    if model_raw is not None and isinstance(model, dict):
        if serialize(model) != model_raw:
            findings.add(
                EXIT_DETERMINISM, "architecture-model.json is not byte-stable canonical JSON"
            )
    if model_md is not None and isinstance(model, dict):
        if project_markdown(model) != model_md:
            findings.add(
                EXIT_DETERMINISM,
                "architecture-model.md is not the deterministic projection of the model",
            )


def _scan_public_safety(text: str | None, source: str, findings: Findings) -> None:
    if text is None:
        return
    for label, pattern in PUBLIC_SAFETY_PATTERNS:
        for match in pattern.finditer(text):
            findings.add(
                EXIT_PUBLIC_SAFETY,
                f"{source} contains a prohibited public-safety class ({label}) near offset "
                f"{match.start()}",
            )


def run_checks(
    model: object,
    *,
    ownership: object = None,
    requirement_register: object = None,
    model_raw: str | None = None,
    model_md: str | None = None,
) -> Findings:
    """Run every deterministic check and return the classified findings."""

    findings = Findings()
    _check_model_schema(model, findings)
    model_ok = isinstance(model, dict) and list(model.keys()) == MODEL_TOP
    if model_ok:
        _check_ordering(model, findings)
        _check_identity(model, findings)
        _check_paths(model, findings)
        _check_boundaries(model, findings)
        _check_contracts(model, findings)
        _check_diagrams(model, findings)
        _check_governance(model, findings)
        _check_neutrality(model, findings)
        _check_safety(model, findings)
        _check_binding(model, requirement_register, findings)
        _check_maturity(model, ownership, findings)
    _check_dependencies(ownership, requirement_register, findings)
    _check_determinism(model, model_raw, model_md, findings)
    _scan_public_safety(model_raw, "architecture-model.json", findings)
    _scan_public_safety(model_md, "architecture-model.md", findings)
    return findings


def _read_bounded(path: Path, findings: Findings) -> str | None:
    try:
        if not path.is_file():
            findings.add(EXIT_IO, f"required input is missing: {path.name}")
            return None
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            findings.add(EXIT_IO, f"{path.name} exceeds the 1 MiB input bound")
            return None
        return path.read_text(encoding="utf-8")
    except OSError as error:  # pragma: no cover - defensive, unreachable in-repo
        findings.add(EXIT_IO, f"cannot read {path.name}: {error}")
        return None


def _load_json_bounded(path: Path, label: str, findings: Findings) -> tuple[object, str | None]:
    raw_text = _read_bounded(path, findings)
    if raw_text is None:
        return None, None
    try:
        return json.loads(raw_text), raw_text
    except json.JSONDecodeError as error:
        findings.add(EXIT_SCHEMA, f"{label} is not valid JSON: {error.msg}")
        return None, raw_text


def _load_json_object(path: Path) -> object:
    try:
        if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):  # pragma: no cover - defensive
        return None


def _emit(findings: Findings) -> int:
    exit_code = findings.exit_code()
    if exit_code == EXIT_OK:
        print("X-COM architecture/contracts validation passed")
        return EXIT_OK
    print(
        f"X-COM architecture/contracts validation FAILED: {CLASS_NAMES[exit_code]} "
        f"(exit {exit_code})",
        file=sys.stderr,
    )
    for line in findings.diagnostics():
        print(f"- {line}", file=sys.stderr)
    return exit_code


def _load_inputs(
    findings: Findings, *, check_human: bool
) -> tuple[object, str | None, str | None]:
    model, model_raw = _load_json_bounded(MODEL_JSON, "architecture-model.json", findings)
    model_md = _read_bounded(MODEL_MD, findings) if check_human else None
    return model, model_raw, model_md


def _run(read_inputs: bool, check_human: bool) -> int:
    findings = Findings()
    model = model_raw = model_md = None
    if read_inputs:
        model, model_raw, model_md = _load_inputs(findings, check_human=check_human)
        if model_raw is None:
            return _emit(findings)
    ownership = _load_json_object(OWNERSHIP_JSON)
    requirement_register = _load_json_object(REQUIREMENT_REGISTER_JSON)
    result = run_checks(
        model,
        ownership=ownership,
        requirement_register=requirement_register,
        model_raw=model_raw,
        model_md=model_md,
    )
    if read_inputs:
        for exit_class, messages in result.by_class.items():
            for message in messages:
                findings.add(exit_class, message)
        return _emit(findings)
    return result.exit_code()


def _verify() -> int:
    return _run(read_inputs=True, check_human=False)


def _check_human() -> int:
    return _run(read_inputs=True, check_human=True)


def _copy(model: object) -> object:
    return json.loads(json.dumps(model))


def _sort_arrays(model: dict) -> None:
    for family in FAMILIES:
        model[family] = sorted(model[family], key=lambda item: item["id"])


def _component(model: dict, identifier: str) -> dict:
    for component in model["components"]:
        if component["id"] == identifier:
            return component
    raise KeyError(identifier)


def _boundary(model: dict, identifier: str) -> dict:
    for boundary in model["boundaries"]:
        if boundary["id"] == identifier:
            return boundary
    raise KeyError(identifier)


def _contract(model: dict, identifier: str) -> dict:
    for contract in model["contracts"]:
        if contract["id"] == identifier:
            return contract
    raise KeyError(identifier)


def _diagram(model: dict, identifier: str) -> dict:
    for diagram in model["diagrams"]:
        if diagram["id"] == identifier:
            return diagram
    raise KeyError(identifier)


def _invariant(model: dict, identifier: str) -> dict:
    for invariant in model["invariants"]:
        if invariant["id"] == identifier:
            return invariant
    raise KeyError(identifier)


def _duplicate_after(entries: list, index: int) -> None:
    entries.insert(index + 1, _copy(entries[index]))


def _sync_counts(model: dict) -> None:
    """Keep the declared counts consistent so a fixture isolates its own defect."""

    for family in FAMILIES:
        model["counts"][family] = len(model[family])


def _negative_fixtures(base: dict):
    """Yield (name, expected_exit, mutated_model) fixtures NEG-01..NEG-34.

    NEG-21 (fail-closed dependency) and NEG-22 (tampered projection) are handled
    directly by ``_self_test`` because they are not model mutations.
    """

    fixtures = []

    # NEG-01: remove a required top-level field.
    model = _copy(base)
    del model["counts"]
    fixtures.append(("NEG-01", EXIT_SCHEMA, model))

    # NEG-02: duplicate a component id (kept adjacent, so ordering still passes).
    model = _copy(base)
    _duplicate_after(model["components"], 0)
    fixtures.append(("NEG-02", EXIT_IDENTITY, model))

    # NEG-03: unknown layer token.
    model = _copy(base)
    _component(model, "XCOM-CMP-004")["layer"] = "garbage"
    fixtures.append(("NEG-03", EXIT_IDENTITY, model))

    # NEG-04: empty a mandatory component field.
    model = _copy(base)
    _component(model, "XCOM-CMP-001")["responsibility"] = ""
    fixtures.append(("NEG-04", EXIT_IDENTITY, model))

    # NEG-05: boundary endpoint at an undeclared component.
    model = _copy(base)
    _boundary(model, "XCOM-XB-001")["from_component"] = "XCOM-CMP-999"
    fixtures.append(("NEG-05", EXIT_BOUNDARY, model))

    # NEG-06: unknown boundary kind.
    model = _copy(base)
    _boundary(model, "XCOM-XB-001")["kind"] = "nonsense"
    fixtures.append(("NEG-06", EXIT_BOUNDARY, model))

    # NEG-07: remove a required boundary and its diagram step. XB-002 is chosen so a
    # sibling boundary (XB-003) still references contract XLC-001, keeping the defect
    # isolated to the required-boundary-set check.
    model = _copy(base)
    model["boundaries"] = [b for b in model["boundaries"] if b["id"] != "XCOM-XB-002"]
    diagram = _diagram(model, "XCOM-DGM-002")
    diagram["steps"] = [
        step for step in diagram["steps"] if step["boundary"] != "XCOM-XB-002"
    ]
    fixtures.append(("NEG-07", EXIT_BOUNDARY, model))

    # NEG-08: dangling boundary-to-contract reference (another boundary still covers XLC-003).
    model = _copy(base)
    _boundary(model, "XCOM-XB-006")["contract"] = "XCOM-XLC-999"
    fixtures.append(("NEG-08", EXIT_CONTRACT, model))

    # NEG-09: language pair not in the contract endpoint languages.
    model = _copy(base)
    _boundary(model, "XCOM-XB-003")["from_language"] = "external"
    fixtures.append(("NEG-09", EXIT_CONTRACT, model))

    # NEG-10: remove a contract version.
    model = _copy(base)
    del _contract(model, "XCOM-XLC-006")["version"]
    fixtures.append(("NEG-10", EXIT_CONTRACT, model))

    # NEG-11: undeclared diagram participant.
    model = _copy(base)
    diagram = _diagram(model, "XCOM-DGM-002")
    diagram["participants"] = sorted(diagram["participants"] + ["XCOM-CMP-999"])
    fixtures.append(("NEG-11", EXIT_DIAGRAM, model))

    # NEG-12: undeclared boundary in a sequence step.
    model = _copy(base)
    _diagram(model, "XCOM-DGM-002")["steps"][0]["boundary"] = "XCOM-XB-999"
    fixtures.append(("NEG-12", EXIT_DIAGRAM, model))

    # NEG-13: remove the US2 sequence diagram (user-story and boundary coverage loss).
    model = _copy(base)
    model["diagrams"] = [d for d in model["diagrams"] if d["id"] != "XCOM-DGM-003"]
    fixtures.append(("NEG-13", EXIT_DIAGRAM, model))

    # NEG-14: unknown governing ADR.
    model = _copy(base)
    _component(model, "XCOM-CMP-004")["governing_adrs"].append("ADR-9999")
    fixtures.append(("NEG-14", EXIT_GOVERNANCE, model))

    # NEG-15: promote a REF-002 target.
    model = _copy(base)
    model["ref002"]["promoted"] = ["XVE-SYS-0139"]
    fixtures.append(("NEG-15", EXIT_GOVERNANCE, model))

    # NEG-16: introduce a reverse dependency (runtime -> XDL build-time).
    model = _copy(base)
    boundary = _boundary(model, "XCOM-XB-001")
    boundary["from_component"] = "XCOM-CMP-004"
    boundary["to_component"] = "XCOM-CMP-002"
    fixtures.append(("NEG-16", EXIT_GOVERNANCE, model))

    # NEG-17: add a domain primitive to a core-layer component.
    model = _copy(base)
    _component(model, "XCOM-CMP-006")["constraints"].append("CAN bus domain primitive")
    fixtures.append(("NEG-17", EXIT_GOVERNANCE, model))

    # NEG-18: remove a required safety invariant.
    model = _copy(base)
    model["invariants"] = [
        inv for inv in model["invariants"] if inv["id"] != "XCOM-INV-13"
    ]
    fixtures.append(("NEG-18", EXIT_SAFETY, model))

    # NEG-19: malformed baseline.
    model = _copy(base)
    model["baseline_revision"] = "abc"
    fixtures.append(("NEG-19", EXIT_BINDING, model))

    # NEG-20: unknown authorization record.
    model = _copy(base)
    model["authorization_records"] = sorted(model["authorization_records"] + ["ACC099"])
    fixtures.append(("NEG-20", EXIT_BINDING, model))

    # NEG-23: prohibited public content (absolute host path).
    model = _copy(base)
    _component(model, "XCOM-CMP-001")["responsibility"] = (
        "fixture only; forbidden path /home/jefferson/secret"
    )
    fixtures.append(("NEG-23", EXIT_PUBLIC_SAFETY, model))

    # NEG-24: a component with no artifact path.
    model = _copy(base)
    _component(model, "XCOM-CMP-001")["artifact_paths"] = []
    fixtures.append(("NEG-24", EXIT_IDENTITY, model))

    # NEG-25: mark an absent path established.
    model = _copy(base)
    _component(model, "XCOM-CMP-010")["artifact_paths"][0]["status"] = "established"
    fixtures.append(("NEG-25", EXIT_PATH, model))

    # NEG-26: mark a present path planned.
    model = _copy(base)
    _component(model, "XCOM-CMP-001")["artifact_paths"][0]["status"] = "planned"
    fixtures.append(("NEG-26", EXIT_PATH, model))

    # NEG-27: duplicate a boundary id (kept adjacent).
    model = _copy(base)
    _duplicate_after(model["boundaries"], 0)
    fixtures.append(("NEG-27", EXIT_BOUNDARY, model))

    # NEG-28: duplicate a contract id (kept adjacent).
    model = _copy(base)
    _duplicate_after(model["contracts"], 0)
    fixtures.append(("NEG-28", EXIT_CONTRACT, model))

    # NEG-29: store the component array out of id order.
    model = _copy(base)
    model["components"][0], model["components"][1] = (
        model["components"][1],
        model["components"][0],
    )
    fixtures.append(("NEG-29", EXIT_SCHEMA, model))

    # NEG-30: mark an unreconciled component implemented without an accepted revision.
    model = _copy(base)
    component = _component(model, "XCOM-CMP-004")
    component["maturity"] = "implemented"
    component["accepted_revision"] = None
    fixtures.append(("NEG-30", EXIT_GOVERNANCE, model))

    # NEG-31: point a requirement link at an id absent from the T008 register.
    model = _copy(base)
    _component(model, "XCOM-CMP-001")["requirement_links"] = ["XCOM-SW-NOPE-999"]
    fixtures.append(("NEG-31", EXIT_BINDING, model))

    # NEG-32: a family id that is not a string. It must be a classified SCHEMA_INVALID
    # failure, never an uncaught TypeError from the ordering/uniqueness checks.
    model = _copy(base)
    model["components"][0]["id"] = 5
    fixtures.append(("NEG-32", EXIT_SCHEMA, model))

    # NEG-33: weaken a required safety invariant to permit an unrestricted TCP listener;
    # presence alone must not suffice.
    model = _copy(base)
    _invariant(model, "XCOM-INV-13")["statement"] = (
        "The first proof may expose a TCP listener on any interface."
    )
    fixtures.append(("NEG-33", EXIT_SAFETY, model))

    # NEG-34: cite an anchor that matches the FR-### pattern but is not in the accepted
    # spec anchor set.
    model = _copy(base)
    _component(model, "XCOM-CMP-001")["requirement_links"] = ["FR-999"]
    fixtures.append(("NEG-34", EXIT_BINDING, model))

    # NEG-35..NEG-39: a family id that is an unhashable container (list or dict). As with
    # NEG-32, each must be a classified SCHEMA_INVALID failure, never an uncaught TypeError
    # from an id-keyed dict/set built in _check_contracts, _check_diagrams, _check_neutrality,
    # or _check_safety. One fixture per affected family, plus a dict id for components.
    model = _copy(base)
    model["components"][0]["id"] = ["x"]
    fixtures.append(("NEG-35", EXIT_SCHEMA, model))

    model = _copy(base)
    model["components"][0]["id"] = {"a": 1}
    fixtures.append(("NEG-36", EXIT_SCHEMA, model))

    model = _copy(base)
    model["boundaries"][0]["id"] = ["x"]
    fixtures.append(("NEG-37", EXIT_SCHEMA, model))

    model = _copy(base)
    model["contracts"][0]["id"] = ["x"]
    fixtures.append(("NEG-38", EXIT_SCHEMA, model))

    model = _copy(base)
    model["invariants"][0]["id"] = ["x"]
    fixtures.append(("NEG-39", EXIT_SCHEMA, model))

    return fixtures


def _self_test() -> int:
    findings = Findings()
    model, model_raw = _load_json_bounded(MODEL_JSON, "architecture-model.json", findings)
    if model is None or model_raw is None:
        for exit_class, messages in findings.by_class.items():
            for message in messages:
                print(f"- [{CLASS_NAMES[exit_class]}] {message}", file=sys.stderr)
        print(
            "X-COM architecture/contracts self-test FAILED: positive fixture is unavailable",
            file=sys.stderr,
        )
        return EXIT_IO
    model_md = _read_bounded(MODEL_MD, findings)
    ownership = _load_json_object(OWNERSHIP_JSON)
    requirement_register = _load_json_object(REQUIREMENT_REGISTER_JSON)

    positive = run_checks(
        model,
        ownership=ownership,
        requirement_register=requirement_register,
        model_raw=model_raw,
        model_md=model_md,
    )
    if positive.exit_code() != EXIT_OK:
        for line in positive.diagnostics():
            print(f"- {line}", file=sys.stderr)
        print(
            "X-COM architecture/contracts self-test FAILED: positive fixture did not pass",
            file=sys.stderr,
        )
        return EXIT_DETERMINISM

    failures = 0
    print("positive fixture: passed")
    for name, expected, mutated in _negative_fixtures(model):
        if isinstance(mutated.get("counts"), dict):
            _sync_counts(mutated)
        raw = serialize(mutated)
        result = run_checks(
            mutated,
            ownership=ownership,
            requirement_register=requirement_register,
            model_raw=raw,
        )
        actual = result.exit_code()
        if actual == expected:
            print(f"{name}: rejected with {CLASS_NAMES[expected]} (exit {expected})")
        else:
            failures += 1
            print(
                f"{name}: expected {CLASS_NAMES[expected]} (exit {expected}) but got "
                f"{CLASS_NAMES.get(actual, actual)} (exit {actual})",
                file=sys.stderr,
            )
            for line in result.diagnostics():
                print(f"- {line}", file=sys.stderr)

    # NEG-21: an unavailable reconciliation dependency must fail closed.
    result = run_checks(
        model,
        ownership=None,
        requirement_register=None,
        model_raw=model_raw,
    )
    if result.exit_code() == EXIT_BINDING:
        print("NEG-21: missing dependencies rejected with BINDING_INVALID (exit 9)")
    else:
        failures += 1
        print(
            f"NEG-21: expected BINDING_INVALID (exit 9) but got exit {result.exit_code()}",
            file=sys.stderr,
        )
        for line in result.diagnostics():
            print(f"- {line}", file=sys.stderr)

    # NEG-22: a tampered human projection must be detected as a determinism defect.
    tampered = project_markdown(model) + "tampered\n"
    result = run_checks(
        model,
        ownership=ownership,
        requirement_register=requirement_register,
        model_raw=model_raw,
        model_md=tampered,
    )
    if result.exit_code() == EXIT_DETERMINISM:
        print("NEG-22: tampered projection rejected with DETERMINISM_INVALID (exit 10)")
    else:
        failures += 1
        print(
            f"NEG-22: expected DETERMINISM_INVALID (exit 10) but got exit {result.exit_code()}",
            file=sys.stderr,
        )
        for line in result.diagnostics():
            print(f"- {line}", file=sys.stderr)

    if failures:
        print(
            f"X-COM architecture/contracts self-test FAILED: {failures} fixture(s) did not "
            "behave as declared",
            file=sys.stderr,
        )
        return EXIT_GOVERNANCE
    print("X-COM architecture/contracts self-test passed")
    return EXIT_OK


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--self-test", action="store_true", help="run controlled positive/negative fixtures"
    )
    group.add_argument(
        "--verify", action="store_true", help="validate the model JSON (default)"
    )
    group.add_argument(
        "--check-human",
        action="store_true",
        help="validate the model JSON and its Markdown projection",
    )
    args = parser.parse_args()

    findings = Findings()
    total = 0
    for path in (MODEL_JSON, MODEL_MD, OWNERSHIP_JSON, REQUIREMENT_REGISTER_JSON):
        if path.is_file():
            size = path.stat().st_size
            total += size
            if size > MAX_FILE_BYTES:
                findings.add(EXIT_IO, f"{path.name} exceeds the 1 MiB input bound")
    if total > MAX_TOTAL_BYTES:
        findings.add(EXIT_IO, "total input exceeds the 4 MiB bound")
    if findings.by_class:
        return _emit(findings)

    if args.self_test:
        return _self_test()
    if args.check_human:
        return _check_human()
    return _verify()


if __name__ == "__main__":
    raise SystemExit(main())
