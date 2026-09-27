#!/usr/bin/env python3
"""Offline validator for the X-COM capability-007 requirements register and
bidirectional traceability matrix (task T008).

The register is the canonical, schema-versioned stakeholder/system/software
requirement model for capability 007.  The matrix is the canonical link model
that connects every requirement to its design units, sources, tests, measures,
and the accepted REF-002 SADS dispositions.  This validator is a repository-owned,
deterministic, single-threaded, offline checker.  It reads only repository-relative
files, never writes the candidate tree, never opens a network peer or a subprocess,
and returns a distinct nonzero exit class per failure family so callers (including
the ``--self-test`` fixtures) can bind a result to the exact defect it detected.

Public safety: the register, the matrix, their Markdown projections, and this
validator's output must not contain credentials, private addresses, proprietary
source excerpts, unrestricted payloads, or absolute host paths.  ``--verify``
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
T008_DIR = ROOT / "docs" / "engineering" / "xcom" / "t008"
REGISTER_JSON = T008_DIR / "requirements-register.json"
REGISTER_MD = T008_DIR / "requirements-register.md"
MATRIX_JSON = T008_DIR / "traceability-matrix.json"
MATRIX_MD = T008_DIR / "traceability-matrix.md"
OWNERSHIP_JSON = ROOT / "docs" / "engineering" / "xcom" / "task-ownership.json"
SPEC_MD = ROOT / "specs" / "007-xcom-core" / "spec.md"

EXIT_OK = 0
EXIT_SCHEMA = 2
EXIT_ID = 3
EXIT_SYSTEM = 4
EXIT_REFINEMENT = 5
EXIT_REF002 = 6
EXIT_TRACEABILITY = 7
EXIT_MATURITY = 8
EXIT_BINDING = 9
EXIT_DETERMINISM = 10
EXIT_PUBLIC_SAFETY = 11
EXIT_IO = 12

CLASS_NAMES = {
    EXIT_OK: "OK",
    EXIT_SCHEMA: "SCHEMA_INVALID",
    EXIT_ID: "ID_INVALID",
    EXIT_SYSTEM: "SYSTEM_COVERAGE_INVALID",
    EXIT_REFINEMENT: "REFINEMENT_INVALID",
    EXIT_REF002: "REF002_INVALID",
    EXIT_TRACEABILITY: "TRACEABILITY_INVALID",
    EXIT_MATURITY: "MATURITY_INVALID",
    EXIT_BINDING: "BINDING_INVALID",
    EXIT_DETERMINISM: "DETERMINISM_INVALID",
    EXIT_PUBLIC_SAFETY: "PUBLIC_SAFETY_INVALID",
    EXIT_IO: "IO_ERROR",
}

MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 4 * 1024 * 1024

LEVELS = ["stakeholder", "system", "software"]
MATURITY_VOCABULARY = [
    "allocated",
    "conflicting",
    "deferred",
    "implemented",
    "needs_clarification",
    "partial",
    "superseded",
]
REF002_MATURITY = "architectural-target"
RELATIONS = sorted(
    ["refines", "derives_from", "allocated_to", "implemented_by", "verified_by", "evidenced_by"]
)
TARGET_KINDS = sorted(
    ["requirement", "sads", "design_unit", "source", "test", "measure", "evidence"]
)
ARTIFACT_KINDS = ["design_unit", "source", "test", "measure", "evidence"]
ARTIFACT_STATUSES = ["established", "planned"]
LINK_STATUSES = ["established", "planned"]
NO_DOWNSTREAM_MATURITIES = ("deferred", "superseded", "conflicting", "needs_clarification")

STK_PREFIX = "XCOM-STK-"
SYS_FR_PREFIX = "XCOM-SYS-FR-"
SYS_SC_PREFIX = "XCOM-SYS-SC-"
SW_PREFIX = "XCOM-SW-"
SOFTWARE_FAMILIES = ["CORE", "GW", "XDL", "OBS", "STIM", "INTG", "ENB"]
FAMILY_KEYS = [
    "XCOM-STK",
    "XCOM-SYS-FR",
    "XCOM-SYS-SC",
] + [f"XCOM-SW-{family}" for family in SOFTWARE_FAMILIES]

ID_SCHEME = {
    STK_PREFIX: "stakeholder",
    SYS_FR_PREFIX: "system",
    SYS_SC_PREFIX: "system",
}
for _family in SOFTWARE_FAMILIES:
    ID_SCHEME[f"{SW_PREFIX}{_family}-"] = "software"

FR_IDS = [f"FR-{number:03d}" for number in range(1, 36)]
SC_IDS = [f"SC-{number:03d}" for number in range(1, 12)]
REF002_IDS = [f"XVE-SYS-{number:04d}" for number in range(139, 159)]

ACCEPTED_AUTHORIZATION = [f"ACC{number:03d}" for number in range(1, 16)] + [
    "ADR-0018",
    "ADR-0019",
    "ADR-0020",
]

# Accepted capability-007 REF-002 allocation/deferment table
# (specs/007-xcom-core/reference-traceability.md).
ALLOCATED_REF002 = {
    "XVE-SYS-0139",
    "XVE-SYS-0140",
    "XVE-SYS-0142",
    "XVE-SYS-0145",
    "XVE-SYS-0146",
    "XVE-SYS-0147",
    "XVE-SYS-0149",
    "XVE-SYS-0152",
    "XVE-SYS-0154",
    "XVE-SYS-0156",
}
DEFERRED_REF002 = {
    "XVE-SYS-0141": "protocol/provider capabilities",
    "XVE-SYS-0143": "registry/reconfiguration capabilities",
    "XVE-SYS-0144": "Security/deployment capabilities",
    "XVE-SYS-0148": "record/replay, edge/cloud, and Argus adapters",
    "XVE-SYS-0150": "record/replay, edge/cloud, and Argus adapters",
    "XVE-SYS-0151": "record/replay, edge/cloud, and Argus adapters",
    "XVE-SYS-0153": "Security/deployment capabilities",
    "XVE-SYS-0155": "Security/deployment capabilities",
    "XVE-SYS-0157": "registry/reconfiguration capabilities",
    "XVE-SYS-0158": "Faults/Runtime recovery",
}

REGISTER_TOP = [
    "schema_version",
    "task_id",
    "capability",
    "baseline_revision",
    "candidate_revision_rule",
    "levels",
    "maturity_vocabulary",
    "id_scheme",
    "authorization_records",
    "counts",
    "requirements",
    "ref002_dispositions",
]
REQUIREMENT_FIELDS = [
    "id",
    "level",
    "title",
    "statement",
    "source_anchors",
    "refines",
    "family",
    "owning_task",
    "applicability",
    "maturity",
    "reconciliation",
    "verification_intent",
    "acceptance_criteria",
]
REF002_FIELDS = ["id", "disposition", "maturity", "owner", "covers", "reason"]
MATRIX_TOP = [
    "schema_version",
    "task_id",
    "baseline_revision",
    "candidate_revision_rule",
    "relation_vocabulary",
    "target_kind_vocabulary",
    "artifacts",
    "links",
]
ARTIFACT_FIELDS = ["id", "kind", "locator", "status", "revision_binding"]
LINK_FIELDS = [
    "id",
    "from",
    "from_kind",
    "relation",
    "to",
    "to_kind",
    "status",
    "revision_binding",
]

BASELINE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TASK_RE = re.compile(r"^T\d{3}$")
REQ_ID_RE = re.compile(r"^XCOM-(?:STK|SYS-FR|SYS-SC|SW-[A-Z]+)-\d{3}$")
LINK_ID_RE = re.compile(r"^XCOM-L-\d{4}$")
ARTIFACT_ID_RE = re.compile(r"^XCOM-[A-Z0-9-]+$")
FR_ANCHOR_RE = re.compile(r"^FR-\d{3}$")
SC_ANCHOR_RE = re.compile(r"^SC-\d{3}$")

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
    return str(value).replace("|", "\\|").replace("\n", " ")


def project_register_markdown(register: dict) -> str:
    """Return the deterministic human-readable projection of the register."""

    lines: list[str] = []
    lines.append("# X-COM Capability 007 Requirements Register")
    lines.append("")
    lines.append("> Deterministic projection of `requirements-register.json` (schema version 1).")
    lines.append("> Do not edit by hand; regenerate from the model and re-run")
    lines.append("> `scripts/validate_xcom_requirements_traceability.py --check-human`.")
    lines.append("")
    lines.append("## Register identity")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Task | {register['task_id']} |")
    lines.append(f"| Capability | {register['capability']} |")
    lines.append(f"| Schema version | {register['schema_version']} |")
    lines.append(f"| Baseline revision | `{register['baseline_revision']}` |")
    lines.append(f"| Candidate revision rule | {_md_cell(register['candidate_revision_rule'])} |")
    lines.append(f"| Requirement levels | {', '.join(register['levels'])} |")
    lines.append(f"| Requirements | {len(register['requirements'])} |")
    lines.append(f"| REF-002 dispositions | {len(register['ref002_dispositions'])} |")
    lines.append("")
    lines.append("## Maturity vocabulary")
    lines.append("")
    lines.append(", ".join(f"`{token}`" for token in register["maturity_vocabulary"]))
    lines.append("")
    lines.append("## Authorization records")
    lines.append("")
    lines.append(", ".join(f"`{record}`" for record in register["authorization_records"]))
    lines.append("")
    lines.append("## Declared counts")
    lines.append("")
    lines.append("| Key | Count |")
    lines.append("| --- | ---: |")
    for key in sorted(register["counts"]):
        lines.append(f"| {key} | {register['counts'][key]} |")
    lines.append("")
    lines.append("## Requirements")
    lines.append("")
    lines.append(
        "| ID | Level | Family | Owning task | Maturity | Refines | Source anchors |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for requirement in register["requirements"]:
        refines = ", ".join(requirement["refines"]) or "-"
        anchors = ", ".join(requirement["source_anchors"])
        lines.append(
            f"| {requirement['id']} | {requirement['level']} | {requirement['family']} | "
            f"{requirement['owning_task']} | {requirement['maturity']} | "
            f"{_md_cell(refines)} | {_md_cell(anchors)} |"
        )
    lines.append("")
    lines.append("## REF-002 dispositions")
    lines.append("")
    lines.append("| ID | Disposition | Maturity | Owner | Covers | Reason |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for entry in register["ref002_dispositions"]:
        covers = ", ".join(entry["covers"]) or "-"
        owner = entry["owner"] or "-"
        lines.append(
            f"| {entry['id']} | {entry['disposition']} | {entry['maturity']} | "
            f"{_md_cell(owner)} | {_md_cell(covers)} | {_md_cell(entry['reason'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def project_matrix_markdown(matrix: dict) -> str:
    """Return the deterministic human-readable projection of the matrix."""

    lines: list[str] = []
    lines.append("# X-COM Capability 007 Traceability Matrix")
    lines.append("")
    lines.append("> Deterministic projection of `traceability-matrix.json` (schema version 1).")
    lines.append("> Do not edit by hand; regenerate from the model and re-run")
    lines.append("> `scripts/validate_xcom_requirements_traceability.py --check-human`.")
    lines.append("")
    lines.append("## Matrix identity")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Task | {matrix['task_id']} |")
    lines.append(f"| Schema version | {matrix['schema_version']} |")
    lines.append(f"| Baseline revision | `{matrix['baseline_revision']}` |")
    lines.append(f"| Candidate revision rule | {_md_cell(matrix['candidate_revision_rule'])} |")
    lines.append(f"| Artifacts | {len(matrix['artifacts'])} |")
    lines.append(f"| Links | {len(matrix['links'])} |")
    lines.append("")
    lines.append("## Link relations")
    lines.append("")
    lines.append(", ".join(f"`{relation}`" for relation in matrix["relation_vocabulary"]))
    lines.append("")
    lines.append("## Target kinds")
    lines.append("")
    lines.append(", ".join(f"`{kind}`" for kind in matrix["target_kind_vocabulary"]))
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append("| ID | Kind | Locator | Status | Revision binding |")
    lines.append("| --- | --- | --- | --- | --- |")
    for artifact in matrix["artifacts"]:
        lines.append(
            f"| {artifact['id']} | {artifact['kind']} | {_md_cell(artifact['locator'])} | "
            f"{artifact['status']} | `{artifact['revision_binding']}` |"
        )
    lines.append("")
    lines.append("## Links")
    lines.append("")
    lines.append("| ID | From | Relation | To | To kind | Status | Revision binding |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for link in matrix["links"]:
        lines.append(
            f"| {link['id']} | {link['from']} | {link['relation']} | {link['to']} | "
            f"{link['to_kind']} | {link['status']} | `{link['revision_binding']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _is_sorted_unique_strings(value: object) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) for item in value)
        and value == sorted(set(value))
    )


def _check_register_schema(model: object, findings: Findings) -> None:
    if not isinstance(model, dict):
        findings.add(EXIT_SCHEMA, "register root is not a JSON object")
        return
    if list(model.keys()) != REGISTER_TOP:
        findings.add(EXIT_SCHEMA, "register top-level field set or order differs from the schema")
        return
    if model["schema_version"] != 1:
        findings.add(EXIT_SCHEMA, "register schema_version must be 1")
    if model["task_id"] != "T008":
        findings.add(EXIT_SCHEMA, "register task_id must be T008")
    if model["capability"] != "007-xcom-core":
        findings.add(EXIT_SCHEMA, "register capability must be 007-xcom-core")
    if not isinstance(model["baseline_revision"], str) or not model["baseline_revision"].strip():
        findings.add(EXIT_SCHEMA, "register baseline_revision must be a non-empty string")
    if not isinstance(model["candidate_revision_rule"], str) or not model[
        "candidate_revision_rule"
    ].strip():
        findings.add(EXIT_SCHEMA, "register candidate_revision_rule must be a non-empty string")
    if model["levels"] != LEVELS:
        findings.add(EXIT_SCHEMA, "register levels must equal the accepted three-level set")
    if model["maturity_vocabulary"] != MATURITY_VOCABULARY:
        findings.add(EXIT_SCHEMA, "register maturity_vocabulary must equal the closed vocabulary")
    if model["id_scheme"] != ID_SCHEME:
        findings.add(EXIT_SCHEMA, "register id_scheme must equal the declared family map")
    if not _is_sorted_unique_strings(model["authorization_records"]):
        findings.add(EXIT_SCHEMA, "authorization_records must be a sorted, duplicate-free array")
    if not isinstance(model["counts"], dict):
        findings.add(EXIT_SCHEMA, "counts must be an object")
    if not isinstance(model["requirements"], list) or not model["requirements"]:
        findings.add(EXIT_SCHEMA, "requirements must be a non-empty array")
    else:
        for index, requirement in enumerate(model["requirements"]):
            if not isinstance(requirement, dict):
                findings.add(EXIT_SCHEMA, f"requirements[{index}] is not an object")
                continue
            if list(requirement.keys()) != REQUIREMENT_FIELDS:
                findings.add(
                    EXIT_SCHEMA,
                    f"requirements[{index}] field set or order differs from the schema",
                )
                continue
            for field in (
                "id",
                "level",
                "title",
                "statement",
                "family",
                "owning_task",
                "applicability",
                "maturity",
                "verification_intent",
            ):
                if not isinstance(requirement[field], str):
                    findings.add(EXIT_SCHEMA, f"requirements[{index}].{field} must be a string")
            for field in ("source_anchors", "refines", "acceptance_criteria"):
                if not isinstance(requirement[field], list) or not all(
                    isinstance(item, str) for item in requirement[field]
                ):
                    findings.add(
                        EXIT_SCHEMA, f"requirements[{index}].{field} must be a string array"
                    )
            if requirement["reconciliation"] is not None and not isinstance(
                requirement["reconciliation"], str
            ):
                findings.add(
                    EXIT_SCHEMA,
                    f"requirements[{index}].reconciliation must be a string or null",
                )
    if not isinstance(model["ref002_dispositions"], list):
        findings.add(EXIT_SCHEMA, "ref002_dispositions must be an array")
    else:
        for index, entry in enumerate(model["ref002_dispositions"]):
            if not isinstance(entry, dict):
                findings.add(EXIT_SCHEMA, f"ref002_dispositions[{index}] is not an object")
                continue
            if list(entry.keys()) != REF002_FIELDS:
                findings.add(
                    EXIT_SCHEMA,
                    f"ref002_dispositions[{index}] field set or order differs from the schema",
                )


def _check_matrix_schema(matrix: object, findings: Findings) -> None:
    if not isinstance(matrix, dict):
        findings.add(EXIT_SCHEMA, "matrix root is not a JSON object")
        return
    if list(matrix.keys()) != MATRIX_TOP:
        findings.add(EXIT_SCHEMA, "matrix top-level field set or order differs from the schema")
        return
    if matrix["schema_version"] != 1:
        findings.add(EXIT_SCHEMA, "matrix schema_version must be 1")
    if matrix["task_id"] != "T008":
        findings.add(EXIT_SCHEMA, "matrix task_id must be T008")
    if not isinstance(matrix["baseline_revision"], str) or not matrix["baseline_revision"].strip():
        findings.add(EXIT_SCHEMA, "matrix baseline_revision must be a non-empty string")
    if not isinstance(matrix["candidate_revision_rule"], str) or not matrix[
        "candidate_revision_rule"
    ].strip():
        findings.add(EXIT_SCHEMA, "matrix candidate_revision_rule must be a non-empty string")
    if matrix["relation_vocabulary"] != RELATIONS:
        findings.add(EXIT_SCHEMA, "relation_vocabulary must equal the closed relation set")
    if matrix["target_kind_vocabulary"] != TARGET_KINDS:
        findings.add(EXIT_SCHEMA, "target_kind_vocabulary must equal the closed target-kind set")
    if not isinstance(matrix["artifacts"], list):
        findings.add(EXIT_SCHEMA, "artifacts must be an array")
    else:
        for index, artifact in enumerate(matrix["artifacts"]):
            if not isinstance(artifact, dict):
                findings.add(EXIT_SCHEMA, f"artifacts[{index}] is not an object")
                continue
            if list(artifact.keys()) != ARTIFACT_FIELDS:
                findings.add(
                    EXIT_SCHEMA,
                    f"artifacts[{index}] field set or order differs from the schema",
                )
                continue
            if artifact["kind"] not in ARTIFACT_KINDS:
                findings.add(EXIT_SCHEMA, f"artifacts[{index}].kind is not a declared kind")
            status = artifact["status"]
            if status not in ARTIFACT_STATUSES:
                findings.add(EXIT_SCHEMA, f"artifacts[{index}].status is not established/planned")
            elif status == "established":
                binding = artifact["revision_binding"]
                if not isinstance(binding, str) or not BASELINE_SHA_RE.fullmatch(binding):
                    findings.add(
                        EXIT_SCHEMA,
                        f"artifacts[{index}].revision_binding must be a 40-hex revision for "
                        "an established artifact",
                    )
            elif artifact["revision_binding"] != "planned":
                findings.add(
                    EXIT_SCHEMA,
                    f"artifacts[{index}].revision_binding must be the literal planned for "
                    "a planned artifact",
                )
            if not isinstance(artifact["locator"], str) or not artifact["locator"].strip():
                findings.add(EXIT_SCHEMA, f"artifacts[{index}].locator must be a non-empty string")
    if not isinstance(matrix["links"], list):
        findings.add(EXIT_SCHEMA, "links must be an array")
    else:
        for index, link in enumerate(matrix["links"]):
            if not isinstance(link, dict):
                findings.add(EXIT_SCHEMA, f"links[{index}] is not an object")
                continue
            if list(link.keys()) != LINK_FIELDS:
                findings.add(EXIT_SCHEMA, f"links[{index}] field set or order differs from the schema")
                continue
            if link["status"] not in LINK_STATUSES:
                findings.add(EXIT_SCHEMA, f"links[{index}].status is not established/planned")


def _is_sorted_ids(entries: object) -> bool:
    """True when every entry is an object with a string id and ids ascend."""

    if not isinstance(entries, list):
        return False
    ids = [entry.get("id") for entry in entries if isinstance(entry, dict)]
    if len(ids) != len(entries) or not all(isinstance(identifier, str) for identifier in ids):
        return False
    return ids == sorted(ids)


def _ids_unique(entries: object) -> bool:
    if not isinstance(entries, list):
        return False
    ids = [entry.get("id") for entry in entries if isinstance(entry, dict)]
    return len(ids) == len(entries) and len(ids) == len(set(ids))


def _check_ordering(register: dict, matrix: dict, findings: Findings) -> None:
    """Enforce the declared per-array sorted-by-id ordering and matrix id uniqueness.

    ``detailed-design.md`` §3/§4 requires ascending ``id`` order for exactly the four
    top-level arrays ``requirements``, ``ref002_dispositions``, ``artifacts``, and
    ``links``, and unique ids for the matrix ``artifacts`` and ``links``.  Nested arrays
    (``source_anchors``, ``refines``, ``acceptance_criteria``, ``covers``) preserve their
    authored order and are deliberately not checked for lexical sortedness.  Requirement
    and REF-002 identity uniqueness is reported by ``_check_identity`` and
    ``_check_ref002`` respectively.
    """

    for label, entries in (
        ("requirements", register.get("requirements")),
        ("ref002_dispositions", register.get("ref002_dispositions")),
        ("artifacts", matrix.get("artifacts")),
        ("links", matrix.get("links")),
    ):
        if not _is_sorted_ids(entries):
            findings.add(
                EXIT_SCHEMA, f"{label} must be sorted by id in ascending sequence"
            )
    for label in ("artifacts", "links"):
        entries = matrix.get(label)
        if _is_sorted_ids(entries) and not _ids_unique(entries):
            findings.add(EXIT_SCHEMA, f"{label} must not repeat an id")


def _check_identity(register: dict, findings: Findings) -> None:
    requirements = register.get("requirements")
    if not isinstance(requirements, list):
        return
    seen: set[str] = set()
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        identifier = requirement.get("id")
        if not isinstance(identifier, str) or not REQ_ID_RE.fullmatch(identifier):
            findings.add(EXIT_ID, f"requirement id {identifier!r} does not match a declared family")
            continue
        if identifier in seen:
            findings.add(EXIT_ID, f"duplicate requirement id {identifier}")
        seen.add(identifier)
        level = requirement.get("level")
        if level not in LEVELS:
            findings.add(EXIT_ID, f"requirement {identifier} has unknown level {level!r}")
        matched = [prefix for prefix in ID_SCHEME if identifier.startswith(prefix)]
        if not matched:
            findings.add(EXIT_ID, f"requirement {identifier} matches no declared prefix")
        elif level in LEVELS and ID_SCHEME[matched[0]] != level:
            findings.add(
                EXIT_ID,
                f"requirement {identifier} level {level!r} disagrees with its id family",
            )
        maturity = requirement.get("maturity")
        if maturity not in MATURITY_VOCABULARY:
            findings.add(
                EXIT_ID, f"requirement {identifier} has unknown maturity {maturity!r}"
            )
        family = requirement.get("family")
        if identifier.startswith(SW_PREFIX):
            if family not in SOFTWARE_FAMILIES:
                findings.add(EXIT_ID, f"requirement {identifier} has unknown family {family!r}")
            elif not identifier.startswith(f"{SW_PREFIX}{family}-"):
                findings.add(
                    EXIT_ID, f"requirement {identifier} family {family!r} disagrees with its id"
                )
        elif family != "-":
            findings.add(EXIT_ID, f"requirement {identifier} family must be '-' for its level")
        owning_task = requirement.get("owning_task")
        if not isinstance(owning_task, str) or not TASK_RE.fullmatch(owning_task):
            findings.add(
                EXIT_ID, f"requirement {identifier} has invalid owning_task {owning_task!r}"
            )
        for field in ("title", "statement", "applicability", "verification_intent"):
            value = requirement.get(field)
            if not isinstance(value, str) or not value.strip():
                findings.add(EXIT_ID, f"requirement {identifier} has empty {field}")
        anchors = requirement.get("source_anchors")
        if not isinstance(anchors, list) or not anchors:
            findings.add(EXIT_ID, f"requirement {identifier} has no source anchor")
        criteria = requirement.get("acceptance_criteria")
        if not isinstance(criteria, list) or not criteria:
            findings.add(EXIT_ID, f"requirement {identifier} has no acceptance criterion")
        if not isinstance(requirement.get("refines"), list):
            findings.add(EXIT_ID, f"requirement {identifier} refines must be an array")


def _actual_counts(register: dict) -> dict:
    requirements = register.get("requirements", [])
    counts = {level: 0 for level in LEVELS}
    counts.update({key: 0 for key in FAMILY_KEYS})
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        level = requirement.get("level")
        if level in counts:
            counts[level] += 1
        identifier = requirement.get("id", "")
        for key in FAMILY_KEYS:
            if identifier.startswith(f"{key}-"):
                counts[key] += 1
    return counts


def _check_system_coverage(register: dict, findings: Findings) -> None:
    requirements = register.get("requirements")
    if not isinstance(requirements, list):
        return
    fr_anchors: list[str] = []
    sc_anchors: list[str] = []
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        identifier = requirement.get("id", "")
        anchors = requirement.get("source_anchors", [])
        if identifier.startswith(SYS_FR_PREFIX):
            matched = [a for a in anchors if isinstance(a, str) and FR_ANCHOR_RE.fullmatch(a)]
            if len(matched) != 1:
                findings.add(
                    EXIT_SYSTEM,
                    f"system requirement {identifier} must anchor exactly one accepted FR id",
                )
                continue
            fr_anchors.append(matched[0])
            expected = f"FR-{identifier.rsplit('-', 1)[1]}"
            if matched[0] != expected:
                findings.add(
                    EXIT_SYSTEM,
                    f"system requirement {identifier} anchors {matched[0]} instead of {expected}",
                )
        elif identifier.startswith(SYS_SC_PREFIX):
            matched = [a for a in anchors if isinstance(a, str) and SC_ANCHOR_RE.fullmatch(a)]
            if len(matched) != 1:
                findings.add(
                    EXIT_SYSTEM,
                    f"system requirement {identifier} must anchor exactly one accepted SC id",
                )
                continue
            sc_anchors.append(matched[0])
            expected = f"SC-{identifier.rsplit('-', 1)[1]}"
            if matched[0] != expected:
                findings.add(
                    EXIT_SYSTEM,
                    f"system requirement {identifier} anchors {matched[0]} instead of {expected}",
                )
    if sorted(fr_anchors) != FR_IDS:
        findings.add(
            EXIT_SYSTEM,
            "system functional coverage must equal FR-001..FR-035 exactly once",
        )
    if sorted(sc_anchors) != SC_IDS:
        findings.add(
            EXIT_SYSTEM,
            "system success-criterion coverage must equal SC-001..SC-011 exactly once",
        )
    if register.get("counts") != _actual_counts(register):
        findings.add(
            EXIT_SYSTEM, "declared counts disagree with the requirement entries"
        )


def _parse_accepted_anchors(spec_text: str) -> dict[str, str]:
    """Return the normalized accepted FR-###/SC-### text from ``spec.md``.

    Each accepted requirement is a Markdown bullet whose normative text may wrap onto
    indented continuation lines.  The bullet text is joined and whitespace-normalized so
    it can be compared with the register without depending on source line breaks.
    """

    anchors: dict[str, list[str]] = {}
    current: str | None = None
    for line in spec_text.splitlines():
        match = re.match(r"^- \*\*(FR-\d{3}|SC-\d{3})\*\*: (.*)$", line)
        if match:
            current = match.group(1)
            anchors[current] = [match.group(2)]
            continue
        if current is not None and line.startswith("  ") and line.strip():
            anchors[current].append(line.strip())
        else:
            current = None
    return {key: " ".join(" ".join(parts).split()) for key, parts in anchors.items()}


def _check_system_fidelity(
    register: dict, spec_raw: str | None, findings: Findings
) -> None:
    """Require every system requirement to preserve its accepted FR/SC text.

    The register must not truncate, reword, or drop the accepted FR-001..FR-035 and
    SC-001..SC-011 normative text.  This check compares the normalized ``statement`` and
    the anchor-prefixed ``title`` of every system requirement with the accepted text
    parsed from ``specs/007-xcom-core/spec.md``.
    """

    if spec_raw is None:
        findings.add(
            EXIT_IO,
            "accepted specification specs/007-xcom-core/spec.md is unavailable; "
            "system requirement fidelity cannot be verified",
        )
        return
    accepted = _parse_accepted_anchors(spec_raw)
    if sorted(accepted) != FR_IDS + SC_IDS:
        findings.add(
            EXIT_SYSTEM,
            "spec.md does not expose FR-001..FR-035 and SC-001..SC-011 as accepted anchors",
        )
        return
    requirements = register.get("requirements")
    if not isinstance(requirements, list):
        return
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        identifier = requirement.get("id", "")
        if not (
            identifier.startswith(SYS_FR_PREFIX) or identifier.startswith(SYS_SC_PREFIX)
        ):
            continue
        anchors = requirement.get("source_anchors")
        if not isinstance(anchors, list) or len(anchors) != 1 or anchors[0] not in accepted:
            continue
        anchor = anchors[0]
        expected = accepted[anchor]
        statement = requirement.get("statement")
        if not isinstance(statement, str) or " ".join(statement.split()) != expected:
            findings.add(
                EXIT_SYSTEM,
                f"system requirement {identifier} statement drifts from accepted {anchor} text",
            )
        expected_title = f"{anchor} {expected}"
        title = requirement.get("title")
        if not isinstance(title, str) or " ".join(title.split()) != expected_title:
            findings.add(
                EXIT_SYSTEM,
                f"system requirement {identifier} title drifts from accepted {anchor} text",
            )


def _check_refinement(register: dict, findings: Findings) -> None:
    requirements = register.get("requirements")
    if not isinstance(requirements, list):
        return
    by_id = {
        requirement.get("id"): requirement
        for requirement in requirements
        if isinstance(requirement, dict)
    }
    parents: dict[str, list[str]] = {}
    for identifier, requirement in by_id.items():
        refines = requirement.get("refines")
        if not isinstance(refines, list):
            continue
        parents[identifier] = [parent for parent in refines if isinstance(parent, str)]
    children: dict[str, list[str]] = {identifier: [] for identifier in by_id}
    for identifier, parent_ids in parents.items():
        level = by_id[identifier].get("level")
        if level == "stakeholder" and parent_ids:
            findings.add(
                EXIT_REFINEMENT, f"stakeholder requirement {identifier} must not refine anything"
            )
        if level in ("system", "software") and not parent_ids:
            findings.add(
                EXIT_REFINEMENT, f"{level} requirement {identifier} refines nothing"
            )
        expected_parent_level = {"system": "stakeholder", "software": "system"}.get(level)
        for parent in parent_ids:
            if parent == identifier:
                findings.add(EXIT_REFINEMENT, f"requirement {identifier} refines itself")
                continue
            if parent not in by_id:
                findings.add(
                    EXIT_REFINEMENT, f"requirement {identifier} refines unknown {parent}"
                )
                continue
            if expected_parent_level and by_id[parent].get("level") != expected_parent_level:
                findings.add(
                    EXIT_REFINEMENT,
                    f"requirement {identifier} refines {parent} at the wrong level",
                )
            children[parent].append(identifier)
    for identifier, requirement in by_id.items():
        level = requirement.get("level")
        if level == "stakeholder" and not children[identifier]:
            findings.add(
                EXIT_REFINEMENT, f"stakeholder requirement {identifier} is not refined by any system requirement"
            )
        if level == "system" and not children[identifier]:
            findings.add(
                EXIT_REFINEMENT, f"system requirement {identifier} is not refined by any software requirement"
            )
    # Cycle detection (iterative colouring) over the child -> parent edges.
    state: dict[str, int] = {identifier: 0 for identifier in by_id}
    for start in sorted(by_id):
        if state[start] != 0:
            continue
        stack: list[tuple[str, int]] = [(start, 0)]
        while stack:
            node, index = stack[-1]
            if index == 0:
                state[node] = 1
            parent_ids = parents.get(node, [])
            if index < len(parent_ids):
                stack[-1] = (node, index + 1)
                parent = parent_ids[index]
                if parent not in by_id:
                    continue
                if state[parent] == 1:
                    findings.add(EXIT_REFINEMENT, "refinement graph contains a cycle")
                elif state[parent] == 0:
                    stack.append((parent, 0))
            else:
                state[node] = 2
                stack.pop()


def _check_ref002(register: dict, matrix: dict, findings: Findings) -> None:
    entries = register.get("ref002_dispositions")
    if not isinstance(entries, list):
        return
    seen: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        identifier = entry.get("id")
        seen.append(identifier)
        if identifier not in REF002_IDS:
            findings.add(EXIT_REF002, f"unknown REF-002 id {identifier!r}")
            continue
        disposition = entry.get("disposition")
        if identifier in ALLOCATED_REF002:
            if disposition != "allocated":
                findings.add(
                    EXIT_REF002, f"{identifier} disposition must be allocated, found {disposition!r}"
                )
            covers = entry.get("covers")
            if not isinstance(covers, list) or not covers:
                findings.add(EXIT_REF002, f"{identifier} must list the system requirements it covers")
            if entry.get("owner"):
                findings.add(EXIT_REF002, f"{identifier} is applied and must not name an owner")
        elif identifier in DEFERRED_REF002:
            if disposition != "deferred":
                findings.add(
                    EXIT_REF002, f"{identifier} disposition must be deferred, found {disposition!r}"
                )
            if entry.get("owner") != DEFERRED_REF002[identifier]:
                findings.add(
                    EXIT_REF002, f"{identifier} deferred owner is not the accepted owner"
                )
            if entry.get("covers"):
                findings.add(EXIT_REF002, f"{identifier} is deferred and must not cover requirements")
        if entry.get("maturity") != REF002_MATURITY:
            findings.add(
                EXIT_REF002,
                f"{identifier} maturity must stay {REF002_MATURITY} (no promotion to implemented)",
            )
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            findings.add(EXIT_REF002, f"{identifier} must record a disposition reason")
    if sorted(seen) != REF002_IDS:
        findings.add(
            EXIT_REF002, "REF-002 dispositions must equal XVE-SYS-0139..0158 exactly once"
        )
    register_ids = {
        requirement.get("id")
        for requirement in register.get("requirements", [])
        if isinstance(requirement, dict)
    }
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("disposition") != "allocated":
            continue
        for target in entry.get("covers", []):
            if target not in register_ids:
                findings.add(
                    EXIT_REF002,
                    f"{entry.get('id')} covers undeclared requirement {target}",
                )
    links = matrix.get("links")
    if isinstance(links, list):
        for link in links:
            if not isinstance(link, dict):
                continue
            if link.get("to_kind") == "sads" and (
                link.get("relation") == "implemented_by" or link.get("status") == "established"
            ):
                findings.add(
                    EXIT_REF002,
                    f"REF-002 target {link.get('to')} must not carry an implementation link",
                )


def _check_traceability(register: dict, matrix: dict, findings: Findings) -> None:
    requirements = register.get("requirements")
    if not isinstance(requirements, list):
        return
    register_ids = {
        requirement.get("id")
        for requirement in requirements
        if isinstance(requirement, dict)
    }
    ref002_ids = {
        entry.get("id")
        for entry in register.get("ref002_dispositions", [])
        if isinstance(entry, dict)
    }
    artifacts = matrix.get("artifacts")
    links = matrix.get("links")
    if not isinstance(artifacts, list) or not isinstance(links, list):
        return
    artifact_by_id: dict[str, dict] = {}
    for artifact in artifacts:
        if isinstance(artifact, dict):
            artifact_by_id[artifact.get("id")] = artifact
    declared_relations = set(matrix.get("relation_vocabulary", []))
    declared_kinds = set(matrix.get("target_kind_vocabulary", []))
    referenced: set[str] = set()
    for link in links:
        if not isinstance(link, dict):
            continue
        link_id = link.get("id")
        if not isinstance(link_id, str) or not LINK_ID_RE.fullmatch(link_id):
            findings.add(EXIT_TRACEABILITY, f"link id {link_id!r} does not match XCOM-L-####")
        if link.get("from_kind") != "requirement":
            findings.add(EXIT_TRACEABILITY, f"link {link_id} from_kind must be requirement")
        if link.get("from") not in register_ids:
            findings.add(EXIT_TRACEABILITY, f"link {link_id} from is not a register requirement")
        relation = link.get("relation")
        if relation not in declared_relations:
            findings.add(EXIT_TRACEABILITY, f"link {link_id} uses unknown relation {relation!r}")
        to_kind = link.get("to_kind")
        if to_kind not in declared_kinds:
            findings.add(EXIT_TRACEABILITY, f"link {link_id} uses unknown target kind {to_kind!r}")
            continue
        target = link.get("to")
        if to_kind == "requirement":
            if target not in register_ids:
                findings.add(EXIT_TRACEABILITY, f"link {link_id} targets unknown requirement {target}")
        elif to_kind == "sads":
            if target not in ref002_ids:
                findings.add(EXIT_TRACEABILITY, f"link {link_id} targets unknown REF-002 id {target}")
        else:
            referenced.add(target)
            artifact = artifact_by_id.get(target)
            if artifact is None:
                findings.add(EXIT_TRACEABILITY, f"link {link_id} targets undeclared artifact {target}")
            elif artifact.get("kind") != to_kind:
                findings.add(
                    EXIT_TRACEABILITY,
                    f"link {link_id} target kind {to_kind} disagrees with artifact {target}",
                )
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        identifier = artifact.get("id")
        if not isinstance(identifier, str) or not ARTIFACT_ID_RE.fullmatch(identifier):
            findings.add(EXIT_TRACEABILITY, f"artifact id {identifier!r} is malformed")
        elif identifier not in referenced:
            findings.add(EXIT_TRACEABILITY, f"artifact {identifier} is orphaned (no link references it)")
    register_refines = {
        (requirement.get("id"), parent)
        for requirement in requirements
        if isinstance(requirement, dict)
        for parent in requirement.get("refines", [])
    }
    matrix_refines = set()
    for link in links:
        if isinstance(link, dict) and link.get("relation") == "refines":
            if link.get("to_kind") != "requirement":
                findings.add(
                    EXIT_TRACEABILITY, f"link {link.get('id')} refines must target a requirement"
                )
            matrix_refines.add((link.get("from"), link.get("to")))
    if register_refines != matrix_refines:
        findings.add(
            EXIT_TRACEABILITY,
            "matrix refines links disagree with the register refines relation",
        )


def _link_revision_bound(link: dict) -> bool:
    if link.get("status") == "established":
        return isinstance(link.get("revision_binding"), str) and bool(
            BASELINE_SHA_RE.fullmatch(link["revision_binding"])
        )
    if link.get("status") == "planned":
        return link.get("revision_binding") == "planned"
    return False


def _check_maturity(
    register: dict, matrix: dict, ownership: object, findings: Findings
) -> None:
    requirements = register.get("requirements")
    links = matrix.get("links")
    artifacts = matrix.get("artifacts")
    if not isinstance(requirements, list) or not isinstance(links, list):
        return
    artifact_by_id = {
        artifact.get("id"): artifact
        for artifact in artifacts or []
        if isinstance(artifact, dict)
    }
    by_from: dict[str, list[dict]] = {}
    for link in links:
        if isinstance(link, dict):
            by_from.setdefault(link.get("from"), []).append(link)
    reconciliation_status = _reconciliation_status(ownership)
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        identifier = requirement.get("id")
        maturity = requirement.get("maturity")
        own = by_from.get(identifier, [])
        for link in own:
            if not _link_revision_bound(link):
                findings.add(
                    EXIT_MATURITY,
                    f"link {link.get('id')} status/revision binding is not honest for {identifier}",
                )
        if maturity == "implemented":
            for relation, kind in (
                ("implemented_by", "source"),
                ("verified_by", "test"),
                ("evidenced_by", "measure"),
            ):
                ok = False
                for link in own:
                    if link.get("relation") != relation or link.get("to_kind") != kind:
                        continue
                    artifact = artifact_by_id.get(link.get("to"))
                    if (
                        link.get("status") == "established"
                        and BASELINE_SHA_RE.fullmatch(str(link.get("revision_binding", "")))
                        and isinstance(artifact, dict)
                        and artifact.get("status") == "established"
                        and BASELINE_SHA_RE.fullmatch(str(artifact.get("revision_binding", "")))
                    ):
                        ok = True
                        break
                if not ok:
                    findings.add(
                        EXIT_MATURITY,
                        f"implemented requirement {identifier} lacks an established {relation} {kind}",
                    )
        elif maturity in ("partial", "allocated"):
            has_allocated = any(link.get("relation") == "allocated_to" for link in own)
            has_verified = any(link.get("relation") == "verified_by" for link in own)
            if not has_allocated:
                findings.add(
                    EXIT_MATURITY, f"{maturity} requirement {identifier} has no allocated_to link"
                )
            if not has_verified:
                findings.add(
                    EXIT_MATURITY, f"{maturity} requirement {identifier} has no verified_by link"
                )
        elif maturity == "deferred":
            if any(link.get("relation") == "implemented_by" for link in own):
                findings.add(
                    EXIT_MATURITY, f"deferred requirement {identifier} must not link implemented_by"
                )
            if not (requirement.get("reconciliation") or "").strip():
                findings.add(
                    EXIT_MATURITY, f"deferred requirement {identifier} must record a reason"
                )
        elif maturity in ("superseded", "conflicting", "needs_clarification"):
            if not (requirement.get("reconciliation") or "").strip():
                findings.add(
                    EXIT_MATURITY,
                    f"{maturity} requirement {identifier} must record a disposition note",
                )
        status = reconciliation_status.get(requirement.get("owning_task"))
        if status and status.get("status") in ("unreconciled", "delivered"):
            if maturity != "partial" or not (requirement.get("reconciliation") or "").strip():
                findings.add(
                    EXIT_MATURITY,
                    f"requirement {identifier} is covered by unreconciled or delivered source "
                    f"and must be partial with a recorded reason",
                )
        if status and status.get("status") == "accepted" and maturity == "implemented":
            revision = status.get("revision")
            bound = any(
                link.get("status") == "established"
                and link.get("revision_binding") == revision
                for link in own
            )
            if not bound:
                findings.add(
                    EXIT_MATURITY,
                    f"implemented requirement {identifier} is not bound to the accepted revision of "
                    f"its owning task",
                )


def _reconciliation_status(ownership: object) -> dict:
    result: dict[str, dict] = {}
    if not isinstance(ownership, dict):
        return result
    for slice_record in ownership.get("slices", []):
        if not isinstance(slice_record, dict):
            continue
        for task, entry in slice_record.get("reconciliation", {}).items():
            if isinstance(entry, dict):
                result[task] = entry
    return result


def _check_reconciliation_dependency(ownership: object, findings: Findings) -> None:
    """Fail closed when the T007 reconciliation dependency is unavailable.

    ``_check_maturity`` reconciles T012-T016/T021-T024 coverage against
    ``docs/engineering/xcom/task-ownership.json``.  Those tasks are recorded
    ``delivered`` (reviewed terminal candidates awaiting external acceptance), so a
    requirement they own must stay ``partial`` with a recorded reason.  A missing,
    unreadable, or malformed ownership register must be a hard failure; it must not
    silently skip that check.
    """

    if isinstance(ownership, dict):
        if not isinstance(ownership.get("slices"), list):
            findings.add(
                EXIT_BINDING,
                "reconciliation dependency docs/engineering/xcom/task-ownership.json has "
                "no slices array; coverage cannot be reconciled",
            )
        return
    findings.add(
        EXIT_BINDING,
        "reconciliation dependency docs/engineering/xcom/task-ownership.json is missing "
        "or unreadable; T012-T016/T021-T024 coverage cannot be reconciled",
    )


def _check_binding(register: dict, matrix: dict, findings: Findings) -> None:
    baseline = register.get("baseline_revision")
    if not isinstance(baseline, str) or not BASELINE_SHA_RE.fullmatch(baseline):
        findings.add(EXIT_BINDING, "register baseline_revision is not a 40-hex lowercase SHA")
    matrix_baseline = matrix.get("baseline_revision")
    if not isinstance(matrix_baseline, str) or not BASELINE_SHA_RE.fullmatch(matrix_baseline):
        findings.add(EXIT_BINDING, "matrix baseline_revision is not a 40-hex lowercase SHA")
    elif matrix_baseline != baseline:
        findings.add(EXIT_BINDING, "matrix baseline_revision differs from the register baseline")
    for label, model in (("register", register), ("matrix", matrix)):
        rule = model.get("candidate_revision_rule")
        if not isinstance(rule, str) or not rule.strip():
            findings.add(EXIT_BINDING, f"{label} candidate_revision_rule must be non-empty")
    records = register.get("authorization_records")
    if not isinstance(records, list) or not records:
        findings.add(EXIT_BINDING, "authorization_records must be a non-empty array")
    else:
        unknown = sorted(set(records) - set(ACCEPTED_AUTHORIZATION))
        if unknown:
            findings.add(EXIT_BINDING, f"authorization_records cites unknown records {unknown}")


def _check_determinism(
    register: object,
    matrix: object,
    register_raw: str | None,
    matrix_raw: str | None,
    register_md: str | None,
    matrix_md: str | None,
    findings: Findings,
) -> None:
    if register_raw is not None and isinstance(register, dict):
        if serialize(register) != register_raw:
            findings.add(
                EXIT_DETERMINISM, "requirements-register.json is not byte-stable canonical JSON"
            )
    if matrix_raw is not None and isinstance(matrix, dict):
        if serialize(matrix) != matrix_raw:
            findings.add(
                EXIT_DETERMINISM, "traceability-matrix.json is not byte-stable canonical JSON"
            )
    if register_md is not None and isinstance(register, dict):
        if project_register_markdown(register) != register_md:
            findings.add(
                EXIT_DETERMINISM,
                "requirements-register.md is not the deterministic projection of the register",
            )
    if matrix_md is not None and isinstance(matrix, dict):
        if project_matrix_markdown(matrix) != matrix_md:
            findings.add(
                EXIT_DETERMINISM,
                "traceability-matrix.md is not the deterministic projection of the matrix",
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
    register: object,
    matrix: object,
    *,
    ownership: object = None,
    spec_raw: str | None = None,
    register_raw: str | None = None,
    matrix_raw: str | None = None,
    register_md: str | None = None,
    matrix_md: str | None = None,
) -> Findings:
    """Run every deterministic check and return the classified findings."""

    findings = Findings()
    _check_register_schema(register, findings)
    _check_matrix_schema(matrix, findings)
    _check_reconciliation_dependency(ownership, findings)
    register_ok = isinstance(register, dict) and list(register.keys()) == REGISTER_TOP
    matrix_ok = isinstance(matrix, dict) and list(matrix.keys()) == MATRIX_TOP
    if register_ok:
        _check_identity(register, findings)
        _check_system_coverage(register, findings)
        _check_system_fidelity(register, spec_raw, findings)
        _check_refinement(register, findings)
    if register_ok and matrix_ok:
        _check_ordering(register, matrix, findings)
        _check_ref002(register, matrix, findings)
        _check_traceability(register, matrix, findings)
        _check_maturity(register, matrix, ownership, findings)
        _check_binding(register, matrix, findings)
    _check_determinism(
        register, matrix, register_raw, matrix_raw, register_md, matrix_md, findings
    )
    _scan_public_safety(register_raw, "requirements-register.json", findings)
    _scan_public_safety(matrix_raw, "traceability-matrix.json", findings)
    _scan_public_safety(register_md, "requirements-register.md", findings)
    _scan_public_safety(matrix_md, "traceability-matrix.md", findings)
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


def _load_ownership() -> object:
    try:
        if not OWNERSHIP_JSON.is_file():
            return None
        if OWNERSHIP_JSON.stat().st_size > MAX_FILE_BYTES:
            return None
        return json.loads(OWNERSHIP_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):  # pragma: no cover - defensive
        return None


def _emit(findings: Findings) -> int:
    exit_code = findings.exit_code()
    if exit_code == EXIT_OK:
        print("X-COM requirements/traceability validation passed")
        return EXIT_OK
    print(
        f"X-COM requirements/traceability validation FAILED: {CLASS_NAMES[exit_code]} "
        f"(exit {exit_code})",
        file=sys.stderr,
    )
    for line in findings.diagnostics():
        print(f"- {line}", file=sys.stderr)
    return exit_code


def _load_inputs(
    findings: Findings, *, check_human: bool
) -> tuple[object, object, str | None, str | None, str | None, str | None]:
    register, register_raw = _load_json_bounded(REGISTER_JSON, "requirements-register.json", findings)
    matrix, matrix_raw = _load_json_bounded(MATRIX_JSON, "traceability-matrix.json", findings)
    register_md = None
    matrix_md = None
    if check_human:
        register_md = _read_bounded(REGISTER_MD, findings)
        matrix_md = _read_bounded(MATRIX_MD, findings)
    return register, matrix, register_raw, matrix_raw, register_md, matrix_md


def _run(read_inputs: bool, check_human: bool) -> int:
    findings = Findings()
    if read_inputs:
        register, matrix, register_raw, matrix_raw, register_md, matrix_md = _load_inputs(
            findings, check_human=check_human
        )
    else:
        register = matrix = register_raw = matrix_raw = register_md = matrix_md = None
    ownership = _load_ownership()
    spec_raw = _read_bounded(SPEC_MD, findings) if read_inputs else None
    result = run_checks(
        register,
        matrix,
        ownership=ownership,
        spec_raw=spec_raw,
        register_raw=register_raw,
        matrix_raw=matrix_raw,
        register_md=register_md,
        matrix_md=matrix_md,
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


def _normalise(register: dict, matrix: dict) -> None:
    register["requirements"] = sorted(register["requirements"], key=lambda item: item["id"])
    register["ref002_dispositions"] = sorted(
        register["ref002_dispositions"], key=lambda item: item["id"]
    )
    register["authorization_records"] = sorted(register["authorization_records"])
    matrix["artifacts"] = sorted(matrix["artifacts"], key=lambda item: item["id"])
    matrix["links"] = sorted(matrix["links"], key=lambda item: item["id"])


def _req(register: dict, identifier: str) -> dict:
    for requirement in register["requirements"]:
        if requirement["id"] == identifier:
            return requirement
    raise KeyError(identifier)


def _link(matrix: dict, identifier: str) -> dict:
    for link in matrix["links"]:
        if link["id"] == identifier:
            return link
    raise KeyError(identifier)


def _first_link(matrix: dict, requirement_id: str, relation: str) -> dict:
    for link in matrix["links"]:
        if link["from"] == requirement_id and link["relation"] == relation:
            return link
    raise KeyError((requirement_id, relation))


def _fixture_artifact(matrix: dict) -> str:
    for artifact in matrix["artifacts"]:
        if artifact["kind"] == "source" and artifact["id"] == "XCOM-SRC-SPEC-007":
            return artifact["id"]
    raise KeyError("XCOM-SRC-SPEC-007")


def _negative_fixtures(
    base_register: dict, base_matrix: dict
) -> list[tuple[str, int, dict, dict]]:
    fixtures: list[tuple[str, int, dict, dict]] = []

    # NEG-01: remove a required top-level field.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    del register["counts"]
    _normalise(register, matrix)
    fixtures.append(("NEG-01", EXIT_SCHEMA, register, matrix))

    # NEG-02: duplicate a requirement id.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    duplicate = _copy(_req(register, "XCOM-SW-ENB-001"))
    register["requirements"].append(duplicate)
    _normalise(register, matrix)
    fixtures.append(("NEG-02", EXIT_ID, register, matrix))

    # NEG-03: set a requirement level to an unknown token.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    _req(register, "XCOM-SW-ENB-002")["level"] = "systemx"
    _normalise(register, matrix)
    fixtures.append(("NEG-03", EXIT_ID, register, matrix))

    # NEG-04: remove one system functional requirement.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    register["requirements"] = [
        requirement
        for requirement in register["requirements"]
        if requirement["id"] != "XCOM-SYS-FR-035"
    ]
    _normalise(register, matrix)
    fixtures.append(("NEG-04", EXIT_SYSTEM, register, matrix))

    # NEG-05: duplicate/renumber an FR anchor (two entries share FR-007).
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    _req(register, "XCOM-SYS-FR-008")["source_anchors"] = ["FR-007"]
    _normalise(register, matrix)
    fixtures.append(("NEG-05", EXIT_SYSTEM, register, matrix))

    # NEG-06: remove one system success criterion.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    register["requirements"] = [
        requirement
        for requirement in register["requirements"]
        if requirement["id"] != "XCOM-SYS-SC-011"
    ]
    _normalise(register, matrix)
    fixtures.append(("NEG-06", EXIT_SYSTEM, register, matrix))

    # NEG-07: orphan a stakeholder requirement (no system child).
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    for requirement in register["requirements"]:
        if requirement["level"] == "system":
            requirement["refines"] = [
                parent for parent in requirement["refines"] if parent != "XCOM-STK-008"
            ]
    _normalise(register, matrix)
    fixtures.append(("NEG-07", EXIT_REFINEMENT, register, matrix))

    # NEG-08: orphan a system requirement (no software child).
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    for requirement in register["requirements"]:
        if requirement["level"] == "software":
            requirement["refines"] = [
                parent for parent in requirement["refines"] if parent != "XCOM-SYS-FR-024"
            ]
    _normalise(register, matrix)
    fixtures.append(("NEG-08", EXIT_REFINEMENT, register, matrix))

    # NEG-09: introduce a self-refinement.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    self_req = _req(register, "XCOM-SW-CORE-001")
    self_req["refines"] = sorted(set(self_req["refines"]) | {self_req["id"]})
    _normalise(register, matrix)
    fixtures.append(("NEG-09", EXIT_REFINEMENT, register, matrix))

    # NEG-10: remove one REF-002 id.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    register["ref002_dispositions"] = [
        entry for entry in register["ref002_dispositions"] if entry["id"] != "XVE-SYS-0145"
    ]
    _normalise(register, matrix)
    fixtures.append(("NEG-10", EXIT_REF002, register, matrix))

    # NEG-11: promote an allocated REF-002 id to implemented.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    for entry in register["ref002_dispositions"]:
        if entry["id"] == "XVE-SYS-0139":
            entry["maturity"] = "implemented"
    _normalise(register, matrix)
    fixtures.append(("NEG-11", EXIT_REF002, register, matrix))

    # NEG-12: point a link at an undeclared artifact id.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    link = _first_link(matrix, "XCOM-STK-001", "allocated_to")
    link["to"] = "XCOM-DU-NOPE"
    _normalise(register, matrix)
    fixtures.append(("NEG-12", EXIT_TRACEABILITY, register, matrix))

    # NEG-13: use an unknown link relation.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    link = _first_link(matrix, "XCOM-STK-002", "allocated_to")
    link["relation"] = "relates_to"
    _normalise(register, matrix)
    fixtures.append(("NEG-13", EXIT_TRACEABILITY, register, matrix))

    # NEG-14: add a forward-only link target (orphan artifact).
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    matrix["artifacts"].append(
        {
            "id": "XCOM-SRC-ORPHAN",
            "kind": "source",
            "locator": "src/xverse/xcom/src/orphan.cpp",
            "status": "planned",
            "revision_binding": "planned",
        }
    )
    _normalise(register, matrix)
    fixtures.append(("NEG-14", EXIT_TRACEABILITY, register, matrix))

    # NEG-15: mark a requirement implemented without source/test/measure.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    _req(register, "XCOM-SW-ENB-001")["maturity"] = "implemented"
    _normalise(register, matrix)
    fixtures.append(("NEG-15", EXIT_MATURITY, register, matrix))

    # NEG-16: mark a requirement implemented without an exact revision binding.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    link = _first_link(matrix, "XCOM-SW-STIM-001", "implemented_by")
    link["revision_binding"] = "planned"
    _normalise(register, matrix)
    fixtures.append(("NEG-16", EXIT_MATURITY, register, matrix))

    # NEG-17: drop the delivered/unreconciled reason of a source-present requirement.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    _req(register, "XCOM-SW-CORE-001")["reconciliation"] = None
    _normalise(register, matrix)
    fixtures.append(("NEG-17", EXIT_MATURITY, register, matrix))

    # NEG-18: set the register baseline to a short string.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    register["baseline_revision"] = "abc"
    _normalise(register, matrix)
    fixtures.append(("NEG-18", EXIT_BINDING, register, matrix))

    # NEG-20: insert an absolute host path into a text field.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    _req(register, "XCOM-SW-ENB-003")["applicability"] = (
        "fixture only; forbidden path /home/jefferson/secret"
    )
    _normalise(register, matrix)
    fixtures.append(("NEG-20", EXIT_PUBLIC_SAFETY, register, matrix))

    # NEG-21: remove a required matrix top-level field (matrix-schema counterpart of NEG-01).
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    del matrix["target_kind_vocabulary"]
    _normalise(register, matrix)
    fixtures.append(("NEG-21", EXIT_SCHEMA, register, matrix))

    # NEG-22: give an established artifact a non-SHA revision binding.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    for artifact in matrix["artifacts"]:
        if artifact["id"] == "XCOM-SRC-SPEC-007":
            artifact["revision_binding"] = "not-a-sha"
    _normalise(register, matrix)
    fixtures.append(("NEG-22", EXIT_SCHEMA, register, matrix))

    # NEG-23: give a planned artifact a 40-hex revision binding.
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    for artifact in matrix["artifacts"]:
        if artifact["id"] == "XCOM-DU-CORE-BASELINE":
            artifact["revision_binding"] = base_register["baseline_revision"]
    _normalise(register, matrix)
    fixtures.append(("NEG-23", EXIT_SCHEMA, register, matrix))

    # NEG-24: truncate an accepted system requirement statement (fidelity drift).
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    _req(register, "XCOM-SYS-FR-001")["statement"] = "X-COM MUST remain domain-neutral."
    _normalise(register, matrix)
    fixtures.append(("NEG-24", EXIT_SYSTEM, register, matrix))

    # NEG-25: duplicate a link id (matrix id uniqueness).
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    matrix["links"].append(_copy(matrix["links"][0]))
    _normalise(register, matrix)
    fixtures.append(("NEG-25", EXIT_SCHEMA, register, matrix))

    # NEG-26: duplicate an artifact id (matrix id uniqueness).
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    matrix["artifacts"].append(_copy(matrix["artifacts"][0]))
    _normalise(register, matrix)
    fixtures.append(("NEG-26", EXIT_SCHEMA, register, matrix))

    # NEG-27: store the requirement array out of id order (sorted-by-id ordering).
    register = _copy(base_register)
    matrix = _copy(base_matrix)
    _normalise(register, matrix)
    register["requirements"][0], register["requirements"][1] = (
        register["requirements"][1],
        register["requirements"][0],
    )
    fixtures.append(("NEG-27", EXIT_SCHEMA, register, matrix))

    return fixtures


def _self_test() -> int:
    findings = Findings()
    register, register_raw = _load_json_bounded(
        REGISTER_JSON, "requirements-register.json", findings
    )
    matrix, matrix_raw = _load_json_bounded(MATRIX_JSON, "traceability-matrix.json", findings)
    register_md = _read_bounded(REGISTER_MD, findings)
    matrix_md = _read_bounded(MATRIX_MD, findings)
    spec_raw = _read_bounded(SPEC_MD, findings)
    if (
        not isinstance(register, dict)
        or not isinstance(matrix, dict)
        or register_raw is None
        or matrix_raw is None
        or register_md is None
        or matrix_md is None
        or spec_raw is None
    ):
        for line in findings.diagnostics():
            print(f"- {line}", file=sys.stderr)
        print(
            "X-COM requirements/traceability self-test FAILED: positive fixture unavailable",
            file=sys.stderr,
        )
        return EXIT_IO

    ownership = _load_ownership()
    positive = run_checks(
        register,
        matrix,
        ownership=ownership,
        spec_raw=spec_raw,
        register_raw=register_raw,
        matrix_raw=matrix_raw,
        register_md=register_md,
        matrix_md=matrix_md,
    )
    if positive.exit_code() != EXIT_OK:
        for line in positive.diagnostics():
            print(f"- {line}", file=sys.stderr)
        print(
            "X-COM requirements/traceability self-test FAILED: positive fixture did not pass",
            file=sys.stderr,
        )
        return EXIT_DETERMINISM

    failures = 0
    print("positive fixture: passed")
    for name, expected, mutated_register, mutated_matrix in _negative_fixtures(register, matrix):
        raw_register = serialize(mutated_register)
        raw_matrix = serialize(mutated_matrix)
        result = run_checks(
            mutated_register,
            mutated_matrix,
            ownership=ownership,
            spec_raw=spec_raw,
            register_raw=raw_register,
            matrix_raw=raw_matrix,
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

    # NEG-19: a tampered human projection must be detected as a determinism defect.
    tampered = project_register_markdown(register) + "tampered\n"
    result = run_checks(
        register,
        matrix,
        ownership=ownership,
        spec_raw=spec_raw,
        register_raw=register_raw,
        matrix_raw=matrix_raw,
        register_md=tampered,
    )
    if result.exit_code() == EXIT_DETERMINISM:
        print("NEG-19: tampered projection rejected with DETERMINISM_INVALID (exit 10)")
    else:
        failures += 1
        print(
            f"NEG-19: expected DETERMINISM_INVALID (exit 10) but got exit {result.exit_code()}",
            file=sys.stderr,
        )
        for line in result.diagnostics():
            print(f"- {line}", file=sys.stderr)

    # NEG-28: an unavailable reconciliation dependency must fail closed (T008-IR-005).
    result = run_checks(
        register,
        matrix,
        ownership=None,
        spec_raw=spec_raw,
        register_raw=register_raw,
        matrix_raw=matrix_raw,
    )
    if result.exit_code() == EXIT_BINDING:
        print("NEG-28: missing ownership register rejected with BINDING_INVALID (exit 9)")
    else:
        failures += 1
        print(
            f"NEG-28: expected BINDING_INVALID (exit 9) but got exit {result.exit_code()}",
            file=sys.stderr,
        )
        for line in result.diagnostics():
            print(f"- {line}", file=sys.stderr)

    if failures:
        print(
            f"X-COM requirements/traceability self-test FAILED: {failures} fixture(s) "
            "did not behave as declared",
            file=sys.stderr,
        )
        return EXIT_MATURITY
    print("X-COM requirements/traceability self-test passed")
    return EXIT_OK


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--self-test", action="store_true", help="run controlled positive/negative fixtures"
    )
    group.add_argument(
        "--verify", action="store_true", help="validate the register and matrix JSON (default)"
    )
    group.add_argument(
        "--check-human",
        action="store_true",
        help="validate the JSON models and their Markdown projections",
    )
    args = parser.parse_args()

    findings = Findings()
    total = 0
    for path in (REGISTER_JSON, REGISTER_MD, MATRIX_JSON, MATRIX_MD, SPEC_MD):
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
