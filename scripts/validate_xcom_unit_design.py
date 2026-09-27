#!/usr/bin/env python3
"""Offline validator for the X-COM T010 unit-design model.

The model is the single authoritative unit design of capability 007: one record
per design unit declaring its identity, ownership, lifetime, thread-safety and
concurrency behaviour, failure semantics, finite resource bounds, planned
evidence, and public-interface Doxygen obligation.  This validator is a
repository-owned, deterministic, single-threaded, offline checker.  It reads only
repository-relative files, never writes the candidate tree, never opens a network
peer or a subprocess, and returns a distinct nonzero exit class per failure family
so callers (including the ``--self-test`` fixtures) can bind a result to the
exact defect it detected.

The model is a derived, machine-checkable projection of the accepted capability
007 specification, plan, data model, contracts, and the T007/T008/T009 enablers.
It designs no runtime behaviour and asserts no measured result.

Public safety: the model, its Markdown projection, and this validator's output
must not contain credentials, private addresses, proprietary source excerpts,
unrestricted payloads, or absolute host paths.  ``--verify`` scans for the
mechanically detectable classes (absolute host paths, private IPv4 ranges,
credential assignment tokens, private-key markers, and unbounded base64-like
blobs); the review stage judges the classes that are not mechanically decidable.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_JSON = ROOT / "docs" / "engineering" / "xcom" / "t010" / "unit-design.json"
MODEL_MD = ROOT / "docs" / "engineering" / "xcom" / "t010" / "design-units.md"
DEP_TASK_OWNERSHIP = ROOT / "docs" / "engineering" / "xcom" / "task-ownership.json"
DEP_REQUIREMENT_REGISTER = ROOT / "docs" / "engineering" / "xcom" / "t008" / "requirements-register.json"
DEP_ARCHITECTURE_MODEL = ROOT / "docs" / "engineering" / "xcom" / "t009" / "architecture-model.json"

RUN_BASELINE = "abb81681e0d844edaecbaf2843f1c2a7deb1e40f"

EXIT_OK = 0
EXIT_SCHEMA = 2
EXIT_IDENTITY = 3
EXIT_OWNERSHIP = 4
EXIT_THREAD = 5
EXIT_BOUNDS = 6
EXIT_FAILURE = 7
EXIT_DOXYGEN = 8
EXIT_GOVERNANCE = 9
EXIT_BINDING = 10
EXIT_DETERMINISM = 11
EXIT_PUBLIC_SAFETY = 12
EXIT_PATH = 13
EXIT_IO = 14

CLASS_NAMES = {
    EXIT_OK: "OK",
    EXIT_SCHEMA: "SCHEMA_INVALID",
    EXIT_IDENTITY: "IDENTITY_INVALID",
    EXIT_OWNERSHIP: "OWNERSHIP_INVALID",
    EXIT_THREAD: "THREAD_INVALID",
    EXIT_BOUNDS: "BOUNDS_INVALID",
    EXIT_FAILURE: "FAILURE_INVALID",
    EXIT_DOXYGEN: "DOXYGEN_INVALID",
    EXIT_GOVERNANCE: "GOVERNANCE_INVALID",
    EXIT_BINDING: "BINDING_INVALID",
    EXIT_DETERMINISM: "DETERMINISM_INVALID",
    EXIT_PUBLIC_SAFETY: "PUBLIC_SAFETY_INVALID",
    EXIT_PATH: "PATH_INVALID",
    EXIT_IO: "IO_ERROR",
}

MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 4 * 1024 * 1024

# ---------------------------------------------------------------------------
# Closed vocabularies (authored order is significant: the model must equal them)
# ---------------------------------------------------------------------------

FAMILY_VOCABULARY = ["CORE", "ENB", "GW", "INTG", "OBS", "STIM", "XDL"]
KIND_VOCABULARY = [
    "boundary",
    "build-time",
    "data-plane",
    "derived-artifact",
    "documentation",
    "edge",
    "evidence",
    "test-fixture",
]
LANGUAGE_VOCABULARY = ["cpp", "json", "markdown", "proto", "python"]
MATURITY_VOCABULARY = [
    "allocated",
    "conflicting",
    "deferred",
    "implemented",
    "needs_clarification",
    "partial",
    "superseded",
]
OWNERSHIP_VOCABULARY = [
    "caller-owns-value",
    "gateway-issued-handle",
    "platform-owns-shared",
    "provider-issued-handle",
    "session-issued-handle",
    "task-owns-artifact",
]
LIFETIME_VOCABULARY = [
    "document-scoped",
    "endpoint-generation",
    "invocation-scoped",
    "plan-scoped",
    "process-scoped",
    "route-scoped",
    "session-scoped",
    "static-immutable",
]
THREAD_SAFETY_VOCABULARY = [
    "externally-synchronized",
    "immutable-value",
    "internally-synchronized",
    "message-passing",
    "offline-single-threaded",
    "process-isolated",
    "read-only-static",
    "single-thread-owner",
]
BOUND_KIND_VOCABULARY = [
    "bytes",
    "capacity",
    "deadline",
    "depth",
    "quota",
    "rate",
    "retry",
    "thread-count",
    "timeout",
]
OVERFLOW_POLICY_VOCABULARY = [
    "coalesce",
    "drop-newest",
    "drop-oldest",
    "fail-closed",
    "lossless-backpressure",
    "n/a",
    "reject",
]
OUTCOME_VOCABULARY = [
    "accepted",
    "cancelled",
    "delivered",
    "evidence-incomplete",
    "expired",
    "failed",
    "rejected",
    "unknown",
]
DOXYGEN_TAG_VOCABULARY = [
    "brief",
    "failure",
    "file",
    "ingroup",
    "lifetime",
    "note",
    "ownership",
    "param",
    "post",
    "pre",
    "retval",
    "return",
    "thread_safety",
]
ADR_VOCABULARY = ["ADR-0016", "ADR-0018", "ADR-0019", "ADR-0020"]

AUTHORIZATION_RECORDS = sorted(
    [f"ACC{number:03d}" for number in range(1, 16)]
    + ["ADR-0018", "ADR-0019", "ADR-0020"]
)

TOP_FIELDS = [
    "schema_version",
    "task_id",
    "capability",
    "baseline_revision",
    "candidate_revision_rule",
    "family_vocabulary",
    "kind_vocabulary",
    "language_vocabulary",
    "maturity_vocabulary",
    "ownership_vocabulary",
    "lifetime_vocabulary",
    "thread_safety_vocabulary",
    "bound_kind_vocabulary",
    "overflow_policy_vocabulary",
    "outcome_vocabulary",
    "doxygen_tag_vocabulary",
    "adr_vocabulary",
    "authorization_records",
    "ref002",
    "dependencies",
    "coverage",
    "doxygen_plan",
    "counts",
    "units",
    "invariants",
]

VOCABULARY_FIELDS = {
    "family_vocabulary": FAMILY_VOCABULARY,
    "kind_vocabulary": KIND_VOCABULARY,
    "language_vocabulary": LANGUAGE_VOCABULARY,
    "maturity_vocabulary": MATURITY_VOCABULARY,
    "ownership_vocabulary": OWNERSHIP_VOCABULARY,
    "lifetime_vocabulary": LIFETIME_VOCABULARY,
    "thread_safety_vocabulary": THREAD_SAFETY_VOCABULARY,
    "bound_kind_vocabulary": BOUND_KIND_VOCABULARY,
    "overflow_policy_vocabulary": OVERFLOW_POLICY_VOCABULARY,
    "outcome_vocabulary": OUTCOME_VOCABULARY,
    "doxygen_tag_vocabulary": DOXYGEN_TAG_VOCABULARY,
    "adr_vocabulary": ADR_VOCABULARY,
}

EXPECTED_FAMILY_COUNTS = {"CORE": 8, "ENB": 5, "GW": 3, "INTG": 4, "OBS": 2, "STIM": 5, "XDL": 3}
EXPECTED_UNIT_TOTAL = 30
EXPECTED_INVARIANT_COUNT = 14
REQUIRED_UNIT_IDS = [f"XCOM-DU-{number:03d}" for number in range(1, EXPECTED_UNIT_TOTAL + 1)]
UNIT_ID_RE = re.compile(r"^XCOM-DU-\d{3}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

DOXYGEN_GROUPS = {
    "CORE": "xcom_core",
    "XDL": "xcom_xdl",
    "OBS": "xcom_obs",
    "STIM": "xcom_stim",
    "GW": "xcom_gw",
    "INTG": "xcom_intg",
    "ENB": "xcom_enb",
}
MANDATORY_FILE_BLOCK = ["file", "brief", "ingroup"]
MANDATORY_PUBLIC_TAGS = ["brief", "ownership", "lifetime", "thread_safety", "failure"]

# The pinned safety/contract invariants: the validator requires them to be present
# AND to carry this exact (kind, statement) text, so removing or weakening one is
# a GOVERNANCE_INVALID failure rather than a silently tolerated edit.
PINNED_INVARIANTS = {
    "XCOM-UDI-05": (
        "bounds",
        "Every queue, quota, depth, rate, byte, and retry bound is finite and declared with its source.",
    ),
    "XCOM-UDI-06": (
        "bounds",
        "No unit silently retries or silently upgrades delivery guarantees.",
    ),
    "XCOM-UDI-07": (
        "failure",
        "An unknown or incomplete outcome is never reported as success.",
    ),
    "XCOM-UDI-08": (
        "doxygen",
        "Every public C/C++ interface documents its ownership, lifetime, thread-safety, and failure "
        "contract.",
    ),
    "XCOM-UDI-13": (
        "safety",
        "The first proof executes no legacy workload, contacts no external peer, and exposes no TCP "
        "listener except the host-protected local tool gateway.",
    ),
}
REQUIRED_PRESENT_INVARIANTS = ("XCOM-UDI-11", "XCOM-UDI-12", "XCOM-UDI-14")

# Consistency predicates used by the per-unit contract checks.
MUTATING_THREAD_MODELS = {
    "single-thread-owner",
    "externally-synchronized",
    "internally-synchronized",
    "message-passing",
}
ISSUED_HANDLE_OWNERSHIP = {
    "provider-issued-handle",
    "session-issued-handle",
    "gateway-issued-handle",
    "platform-owns-shared",
}
# A unit may declare non-empty shared_state only when its model explicitly guards
# that state: internally synchronized, externally synchronized, or by message
# passing.  The remaining models own no shared mutable state and must therefore
# declare an empty shared_state and a null synchronization (XCOM-UDI-04).
SYNCHRONIZING_THREAD_MODELS = {
    "internally-synchronized",
    "externally-synchronized",
    "message-passing",
}
UNSYNCHRONIZED_THREAD_MODELS = {
    "immutable-value",
    "read-only-static",
    "single-thread-owner",
    "offline-single-threaded",
    "process-isolated",
}
NO_SHARED_STATE_THREAD_MODELS = UNSYNCHRONIZED_THREAD_MODELS
CAPACITY_LIKE_KINDS = {"capacity", "quota", "depth", "rate"}
NON_SUCCESS_OUTCOMES = {"rejected", "expired", "cancelled", "failed", "evidence-incomplete"}
DURABLE_MARKERS = ("journal", "durable")
UNKNOWN_CONDITION_RE = re.compile(r"\b(unknown|indeterminate)\b")
DOMAIN_PRIMITIVES = ("ECU", "CAN", "SOME/IP", "SOMEIP", "Zenoh", "AUTOSAR", "FlexRay", "MOST")
RUNTIME_FAMILIES = {"CORE", "OBS", "STIM", "GW"}
UPSTREAM_COMPONENT_LAYERS = {"xdl-input", "build-time"}
SORTED_UNIT_ARRAYS = (
    "owning_tasks",
    "shared_state",
    "component_refs",
    "contract_refs",
    "governing_adrs",
)

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


def serialize(model: object) -> str:
    """Return the canonical byte-stable JSON serialization of a model."""

    return json.dumps(model, indent=2, ensure_ascii=False) + "\n"


def _md_cell(value: object) -> str:
    """Escape a value for a single Markdown table cell."""

    return str(value).replace("|", "\\|").replace("\n", " ")


def _code_list(values: object) -> str:
    if not isinstance(values, list) or not values:
        return "none"
    return ", ".join(f"`{_md_cell(value)}`" for value in values)


def project_markdown(model: dict) -> str:
    """Return the deterministic human-readable projection of a unit-design model."""

    lines: list[str] = []
    lines.append("# X-COM Unit Design — Capability 007")
    lines.append("")
    lines.append("> Deterministic projection of `unit-design.json` (schema version 1).")
    lines.append("> Do not edit by hand; regenerate from the model and re-run")
    lines.append("> `scripts/validate_xcom_unit_design.py --check-human`.")
    lines.append("")
    lines.append("## Model identity")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Task | {model.get('task_id')} |")
    lines.append(f"| Capability | {model.get('capability')} |")
    lines.append(f"| Schema version | {model.get('schema_version')} |")
    lines.append(f"| Baseline revision | `{model.get('baseline_revision')}` |")
    lines.append(f"| Candidate revision rule | {_md_cell(model.get('candidate_revision_rule'))} |")
    lines.append(f"| Units | {len(model.get('units', []))} |")
    lines.append(f"| Invariants | {len(model.get('invariants', []))} |")
    lines.append("")
    lines.append("## REF-002 disposition")
    lines.append("")
    ref002 = model.get("ref002", {})
    lines.append(f"- Disposition: `{ref002.get('disposition')}`")
    lines.append(f"- Promoted: {_code_list(ref002.get('promoted'))}")
    lines.append(f"- Source: `{ref002.get('source')}`")
    lines.append("")
    lines.append("## Coverage")
    lines.append("")
    coverage = model.get("coverage", {})
    lines.append("Component exemptions:")
    lines.append("")
    if coverage.get("component_exemptions"):
        for entry in coverage["component_exemptions"]:
            tasks = ", ".join(entry.get("owning_tasks", []))
            lines.append(f"- `{entry.get('id')}` — {_md_cell(entry.get('reason'))} (owners: {tasks})")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("Requirement exemptions:")
    lines.append("")
    if coverage.get("requirement_exemptions"):
        for entry in coverage["requirement_exemptions"]:
            tasks = ", ".join(entry.get("owning_tasks", []))
            lines.append(f"- `{entry.get('id')}` — {_md_cell(entry.get('reason'))} (owners: {tasks})")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Declared counts")
    lines.append("")
    lines.append("| Family | Units |")
    lines.append("| --- | ---: |")
    counts = model.get("counts", {})
    for family in FAMILY_VOCABULARY:
        lines.append(f"| {family} | {counts.get(family)} |")
    lines.append(f"| **units** | **{counts.get('units')}** |")
    lines.append(f"| **invariants** | **{counts.get('invariants')}** |")
    lines.append("")
    lines.append("## Doxygen plan (DOX-01)")
    lines.append("")
    plan = model.get("doxygen_plan", {})
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Configuration | `{plan.get('configuration')}` |")
    lines.append(f"| Warning-as-error | {plan.get('warn_as_error')} |")
    lines.append(f"| Mandatory file block | {_code_list(plan.get('mandatory_file_block'))} |")
    lines.append(f"| Mandatory public tags | {_code_list(plan.get('mandatory_public_tags'))} |")
    lines.append(f"| Conditional public tags | {_code_list(plan.get('conditional_public_tags'))} |")
    lines.append(f"| Coverage rule | {_md_cell(plan.get('coverage_rule'))} |")
    lines.append("")
    lines.append("Groups:")
    lines.append("")
    for family in FAMILY_VOCABULARY:
        lines.append(f"- `{family}` -> `{plan.get('groups', {}).get(family)}`")
    lines.append("")
    lines.append("Known gaps (recorded, never reported as closed):")
    lines.append("")
    lines.append("| Gap | Description | Owning tasks | Status |")
    lines.append("| --- | --- | --- | --- |")
    for gap in plan.get("gaps", []) or []:
        lines.append(
            f"| `{gap.get('id')}` | {_md_cell(gap.get('description'))} | "
            f"{_md_cell(', '.join(gap.get('owning_tasks', [])))} | `{gap.get('status')}` |"
        )
    lines.append("")
    lines.append("## Units")
    for unit in model.get("units", []):
        lines.append("")
        lines.append(f"### {unit.get('id')} — {unit.get('name')}")
        lines.append("")
        lines.append(f"**Responsibility.** {unit.get('responsibility')}")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("| --- | --- |")
        lines.append(f"| Family | `{unit.get('family')}` |")
        lines.append(f"| Kind | `{unit.get('kind')}` |")
        lines.append(f"| Language | `{unit.get('language')}` |")
        lines.append(f"| Scope | `{unit.get('scope')}` |")
        lines.append(f"| Owning slice | `{unit.get('owning_slice')}` |")
        lines.append(f"| Owning tasks | {_md_cell(', '.join(unit.get('owning_tasks', [])))} |")
        lines.append(f"| Maturity | `{unit.get('maturity')}` |")
        lines.append(f"| Accepted revision | {unit.get('accepted_revision')} |")
        lines.append(f"| Reconciliation | {_md_cell(unit.get('reconciliation') or '')} |")
        lines.append("")
        lines.append("**Artifact paths:**")
        lines.append("")
        for artifact in unit.get("artifact_paths", []):
            lines.append(f"- `{artifact.get('path')}` ({artifact.get('status')})")
        lines.append("")
        lines.append("**Ownership / lifetime.**")
        lines.append("")
        lines.append(f"- Ownership: `{unit.get('ownership_model')}` — {unit.get('ownership_rationale')}")
        lines.append(f"- Lifetime: `{unit.get('lifetime_model')}` — {unit.get('lifetime_rationale')}")
        lines.append(f"- Exposes view: {unit.get('exposes_view')}; view lifetime: {unit.get('view_lifetime')}")
        lines.append("")
        thread = unit.get("thread_safety", {})
        lines.append("**Thread-safety.**")
        lines.append("")
        lines.append(f"- Model: `{thread.get('model')}` — {thread.get('rationale')}")
        lines.append(f"- Shared state: {_code_list(thread.get('shared_state'))}")
        lines.append(f"- Synchronization: {thread.get('synchronization')}")
        lines.append("")
        lines.append("**Bounds:**")
        lines.append("")
        lines.append("| Resource | Kind | Configured | Value | Declared in |")
        lines.append("| --- | --- | --- | --- | --- |")
        for bound in unit.get("bounds", []):
            lines.append(
                f"| {_md_cell(bound.get('resource'))} | `{bound.get('kind')}` | "
                f"{bound.get('configured')} | {bound.get('value')} | {_md_cell(bound.get('declared_in'))} |"
            )
        lines.append("")
        lines.append(f"Overflow policies: {_code_list(unit.get('overflow_policies'))}")
        lines.append("")
        lines.append("**Failure semantics:**")
        lines.append("")
        lines.append("| Condition | Outcome |")
        lines.append("| --- | --- |")
        for entry in unit.get("failure_semantics", []):
            lines.append(f"| {_md_cell(entry.get('condition'))} | `{entry.get('outcome')}` |")
        lines.append("")
        doxygen = unit.get("doxygen", {})
        lines.append("**Doxygen obligation.**")
        lines.append("")
        if doxygen.get("required"):
            lines.append(f"- Group: `{doxygen.get('group')}`")
            lines.append(f"- File block: {_code_list(doxygen.get('file_block'))}")
            lines.append(f"- Public tags: {_code_list(doxygen.get('public_tags'))}")
            lines.append(
                f"- Elements: documented {doxygen.get('documented_elements')} / "
                f"public {doxygen.get('public_elements')}"
            )
        else:
            lines.append(f"- Required: false — {doxygen.get('reason')}")
        lines.append("")
        lines.append(f"**Requirement links:** {_code_list(unit.get('requirement_links'))}")
        lines.append("")
        lines.append(f"**Component refs:** {_code_list(unit.get('component_refs'))}")
        lines.append("")
        lines.append(f"**Contract refs:** {_code_list(unit.get('contract_refs'))}")
        lines.append("")
        lines.append(f"**Governing ADRs:** {_code_list(unit.get('governing_adrs'))}")
        lines.append("")
        lines.append(f"**Planned evidence:** {_code_list(unit.get('planned_evidence'))}")
    lines.append("")
    lines.append("## Invariants")
    lines.append("")
    lines.append("| Id | Kind | Statement | Enforcing check |")
    lines.append("| --- | --- | --- | --- |")
    for invariant in model.get("invariants", []):
        lines.append(
            f"| `{invariant.get('id')}` | `{invariant.get('kind')}` | "
            f"{_md_cell(invariant.get('statement'))} | {_md_cell(invariant.get('enforcing_check'))} |"
        )
    lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------
# Schema, ordering, and identity
# ---------------------------------------------------------------------------


def _is_sorted_unique_strings(value: object) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) for item in value)
        and value == sorted(set(value))
    )


def _ids_of(entries: object) -> list[str]:
    ids: list[str] = []
    if not isinstance(entries, list):
        return ids
    for entry in entries:
        raw = entry.get("id") if isinstance(entry, dict) else entry
        try:
            ids.append(str(raw))
        except Exception:  # pragma: no cover - str() never raises for JSON values
            ids.append("")
    return ids


def _check_model_schema(model: object, findings: Findings) -> bool:
    """Check the top-level schema; return True when the remaining checks may run."""

    if not isinstance(model, dict):
        findings.add(EXIT_SCHEMA, "unit-design root is not a JSON object")
        return False
    if list(model.keys()) != TOP_FIELDS:
        findings.add(EXIT_SCHEMA, "top-level field set or order differs from the schema")
        return False
    if model["schema_version"] != 1:
        findings.add(EXIT_SCHEMA, "schema_version must be 1")
    if model["task_id"] != "T010":
        findings.add(EXIT_SCHEMA, "task_id must be T010")
    if model["capability"] != "007-xcom-core":
        findings.add(EXIT_SCHEMA, "capability must be 007-xcom-core")
    if not isinstance(model["candidate_revision_rule"], str) or not model[
        "candidate_revision_rule"
    ].strip():
        findings.add(EXIT_SCHEMA, "candidate_revision_rule must be a non-empty string")
    for field, expected in VOCABULARY_FIELDS.items():
        if model.get(field) != expected:
            findings.add(EXIT_SCHEMA, f"{field} must equal the declared closed vocabulary")
    if not _is_sorted_unique_strings(model.get("authorization_records")):
        findings.add(EXIT_SCHEMA, "authorization_records must be a sorted, duplicate-free string array")
    if not isinstance(model.get("ref002"), dict):
        findings.add(EXIT_SCHEMA, "ref002 must be an object")
    if not isinstance(model.get("dependencies"), dict):
        findings.add(EXIT_SCHEMA, "dependencies must be an object")
    coverage = model.get("coverage")
    if not isinstance(coverage, dict):
        findings.add(EXIT_SCHEMA, "coverage must be an object")
    elif not isinstance(coverage.get("component_exemptions"), list) or not isinstance(
        coverage.get("requirement_exemptions"), list
    ):
        findings.add(EXIT_SCHEMA, "coverage exemptions must be arrays")
    if not isinstance(model.get("doxygen_plan"), dict):
        findings.add(EXIT_SCHEMA, "doxygen_plan must be an object")
    if not isinstance(model.get("counts"), dict):
        findings.add(EXIT_SCHEMA, "counts must be an object")

    for field in ("units", "invariants"):
        entries = model.get(field)
        if not isinstance(entries, list) or not entries:
            findings.add(EXIT_SCHEMA, f"{field} must be a non-empty array")
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                findings.add(EXIT_SCHEMA, f"{field}[{index}] is not an object")
                continue
            raw_id = entry.get("id")
            if not isinstance(raw_id, str) or not raw_id:
                findings.add(EXIT_SCHEMA, f"{field}[{index}].id must be a non-empty string")

    _check_counts(model, findings)
    return True


def _check_counts(model: dict, findings: Findings) -> None:
    units = model.get("units")
    invariants = model.get("invariants")
    counts = model.get("counts")
    if not isinstance(counts, dict) or not isinstance(units, list) or not isinstance(invariants, list):
        return
    for family, expected in EXPECTED_FAMILY_COUNTS.items():
        if counts.get(family) != expected:
            findings.add(EXIT_SCHEMA, f"counts.{family} must be {expected}")
    if counts.get("units") != EXPECTED_UNIT_TOTAL or len(units) != EXPECTED_UNIT_TOTAL:
        findings.add(
            EXIT_SCHEMA,
            f"units count must be {EXPECTED_UNIT_TOTAL} (declared {counts.get('units')}, "
            f"found {len(units)})",
        )
    if counts.get("invariants") != EXPECTED_INVARIANT_COUNT or len(invariants) != EXPECTED_INVARIANT_COUNT:
        findings.add(
            EXIT_SCHEMA,
            f"invariants count must be {EXPECTED_INVARIANT_COUNT} (declared "
            f"{counts.get('invariants')}, found {len(invariants)})",
        )


def _check_ordering(model: dict, findings: Findings) -> None:
    units = model.get("units")
    invariants = model.get("invariants")
    if isinstance(units, list):
        ids = _ids_of(units)
        if ids != sorted(ids):
            findings.add(EXIT_SCHEMA, "units must be stored in ascending id order")
        for unit in units:
            if not isinstance(unit, dict):
                continue
            artifacts = unit.get("artifact_paths")
            if isinstance(artifacts, list):
                paths = [a.get("path") for a in artifacts if isinstance(a, dict)]
                if all(isinstance(p, str) for p in paths) and paths != sorted(paths):
                    findings.add(EXIT_SCHEMA, f"{unit.get('id')}: artifact_paths must be stored sorted by path")
            bounds = unit.get("bounds")
            if isinstance(bounds, list):
                keys = [
                    (b.get("kind"), b.get("resource"))
                    for b in bounds
                    if isinstance(b, dict) and isinstance(b.get("kind"), str) and isinstance(b.get("resource"), str)
                ]
                if len(keys) == len(bounds) and keys != sorted(keys):
                    findings.add(EXIT_SCHEMA, f"{unit.get('id')}: bounds must be stored sorted by (kind, resource)")
            failures = unit.get("failure_semantics")
            if isinstance(failures, list):
                keys = [
                    (f.get("outcome"), f.get("condition"))
                    for f in failures
                    if isinstance(f, dict) and isinstance(f.get("outcome"), str) and isinstance(f.get("condition"), str)
                ]
                if len(keys) == len(failures) and keys != sorted(keys):
                    findings.add(
                        EXIT_SCHEMA,
                        f"{unit.get('id')}: failure_semantics must be stored sorted by (outcome, condition)",
                    )
            for array_field in SORTED_UNIT_ARRAYS:
                value = unit.get(array_field)
                if value is not None and not _is_sorted_unique_strings(value):
                    findings.add(
                        EXIT_SCHEMA,
                        f"{unit.get('id')}.{array_field} must be a sorted, duplicate-free string array",
                    )
    if isinstance(invariants, list):
        ids = _ids_of(invariants)
        if ids != sorted(ids):
            findings.add(EXIT_SCHEMA, "invariants must be stored in ascending id order")


def _check_identity(model: dict, findings: Findings) -> None:
    units = model.get("units")
    if not isinstance(units, list):
        return
    ids = _ids_of(units)
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        findings.add(EXIT_IDENTITY, f"duplicate unit ids: {duplicates}")
    for unit in units:
        if not isinstance(unit, dict):
            continue
        unit_id = unit.get("id")
        if isinstance(unit_id, str) and not UNIT_ID_RE.fullmatch(unit_id):
            findings.add(EXIT_IDENTITY, f"unit id {unit_id!r} does not match XCOM-DU-###")
        for field, vocabulary in (
            ("family", FAMILY_VOCABULARY),
            ("kind", KIND_VOCABULARY),
            ("language", LANGUAGE_VOCABULARY),
            ("scope", ("first-proof", "later")),
            ("maturity", MATURITY_VOCABULARY),
        ):
            # Every mandatory per-unit scalar must be present AND a member of its
            # closed set (T010-SR-002, detailed-design.md §12.1): an absent or null
            # value is a missing mandatory field, reported as IDENTITY_INVALID (3),
            # never skipped.
            if field not in unit:
                findings.add(EXIT_IDENTITY, f"{unit_id}: missing mandatory field {field}")
                continue
            value = unit[field]
            if not isinstance(value, str) or value not in vocabulary:
                findings.add(EXIT_IDENTITY, f"{unit_id}: unknown {field} token {value!r}")
        if not isinstance(unit.get("name"), str) or not unit["name"].strip():
            findings.add(EXIT_IDENTITY, f"{unit_id}: name must be a non-empty string")
        if not isinstance(unit.get("responsibility"), str) or not unit["responsibility"].strip():
            findings.add(EXIT_IDENTITY, f"{unit_id}: responsibility must be a non-empty string")
        artifacts = unit.get("artifact_paths")
        if not isinstance(artifacts, list) or not artifacts:
            findings.add(EXIT_IDENTITY, f"{unit_id}: at least one artifact path is required")
        else:
            # Each artifact entry must carry a non-empty string path (detailed-design
            # §3 line 84): a status-only entry is a missing mandatory field and is
            # reported as IDENTITY_INVALID (3) rather than silently skipped.
            for artifact in artifacts:
                path = artifact.get("path") if isinstance(artifact, dict) else None
                if not isinstance(path, str) or not path.strip():
                    findings.add(
                        EXIT_IDENTITY,
                        f"{unit_id}: every artifact path entry must carry a non-empty string path",
                    )
        planned_evidence = unit.get("planned_evidence")
        if (
            not isinstance(planned_evidence, list)
            or not planned_evidence
            or not all(isinstance(item, str) and item.strip() for item in planned_evidence)
        ):
            findings.add(
                EXIT_IDENTITY,
                f"{unit_id}: planned_evidence must be a non-empty string array",
            )
        thread = unit.get("thread_safety")
        if isinstance(thread, dict):
            thread_model = thread.get("model")
            if thread_model is not None and (
                not isinstance(thread_model, str) or thread_model not in THREAD_SAFETY_VOCABULARY
            ):
                findings.add(EXIT_IDENTITY, f"{unit_id}: unknown thread-safety model token {thread_model!r}")
        failures = unit.get("failure_semantics")
        if isinstance(failures, list):
            for entry in failures:
                if isinstance(entry, dict):
                    outcome = entry.get("outcome")
                    if outcome is not None and (
                        not isinstance(outcome, str) or outcome not in OUTCOME_VOCABULARY
                    ):
                        findings.add(EXIT_IDENTITY, f"{unit_id}: unknown failure outcome token {outcome!r}")


# ---------------------------------------------------------------------------
# Per-unit contracts
# ---------------------------------------------------------------------------


def _check_ownership(model: dict, task_ownership: object, findings: Findings) -> None:
    units = model.get("units")
    if not isinstance(units, list):
        return
    assignment = task_ownership.get("task_assignment") if isinstance(task_ownership, dict) else None
    for unit in units:
        if not isinstance(unit, dict):
            continue
        unit_id = unit.get("id")
        slice_id = unit.get("owning_slice")
        tasks = unit.get("owning_tasks")
        if not isinstance(slice_id, str) or not slice_id:
            findings.add(EXIT_OWNERSHIP, f"{unit_id}: owning_slice must be a non-empty string")
        if not isinstance(tasks, list) or not tasks:
            findings.add(EXIT_OWNERSHIP, f"{unit_id}: owning_tasks must be a non-empty task set")
        elif isinstance(assignment, dict):
            for task in tasks:
                if assignment.get(task) != slice_id:
                    findings.add(
                        EXIT_OWNERSHIP,
                        f"{unit_id}: owning task {task} does not belong to slice {slice_id} "
                        "in the T007 register",
                    )
        ownership = unit.get("ownership_model")
        if not isinstance(ownership, str) or ownership not in OWNERSHIP_VOCABULARY:
            findings.add(EXIT_OWNERSHIP, f"{unit_id}: ownership_model must be a vocabulary member")
        if not isinstance(unit.get("ownership_rationale"), str) or not unit["ownership_rationale"].strip():
            findings.add(EXIT_OWNERSHIP, f"{unit_id}: ownership_rationale must be a non-empty string")
        lifetime = unit.get("lifetime_model")
        if not isinstance(lifetime, str) or lifetime not in LIFETIME_VOCABULARY:
            findings.add(EXIT_OWNERSHIP, f"{unit_id}: lifetime_model must be a vocabulary member")
        if not isinstance(unit.get("lifetime_rationale"), str) or not unit["lifetime_rationale"].strip():
            findings.add(EXIT_OWNERSHIP, f"{unit_id}: lifetime_rationale must be a non-empty string")
        exposes_view = unit.get("exposes_view")
        view_lifetime = unit.get("view_lifetime")
        if exposes_view is True:
            if not isinstance(view_lifetime, str) or not view_lifetime.strip() or view_lifetime == "n/a":
                findings.add(EXIT_OWNERSHIP, f"{unit_id}: an exposed view requires a bounded view_lifetime")
        elif exposes_view is False:
            if view_lifetime not in (None, "", "n/a"):
                findings.add(EXIT_OWNERSHIP, f"{unit_id}: view_lifetime must be null when no view is exposed")
        else:
            findings.add(EXIT_OWNERSHIP, f"{unit_id}: exposes_view must be a boolean")
        thread = unit.get("thread_safety")
        thread_model = thread.get("model") if isinstance(thread, dict) else None
        if thread_model in MUTATING_THREAD_MODELS and ownership not in ISSUED_HANDLE_OWNERSHIP:
            findings.add(
                EXIT_OWNERSHIP,
                f"{unit_id}: a unit owning mutable runtime state must declare an issued-handle or "
                "platform-owned rule, not caller-owns-value",
            )


def _check_thread_safety(model: dict, findings: Findings) -> None:
    units = model.get("units")
    if not isinstance(units, list):
        return
    for unit in units:
        if not isinstance(unit, dict):
            continue
        unit_id = unit.get("id")
        thread = unit.get("thread_safety")
        if not isinstance(thread, dict):
            findings.add(EXIT_THREAD, f"{unit_id}: thread_safety declaration is missing")
            continue
        thread_model = thread.get("model")
        if not isinstance(thread_model, str) or not thread_model:
            findings.add(EXIT_THREAD, f"{unit_id}: thread-safety model is missing")
        if not isinstance(thread.get("rationale"), str) or not thread["rationale"].strip():
            findings.add(EXIT_THREAD, f"{unit_id}: thread-safety rationale must be a non-empty string")
        shared_state = thread.get("shared_state")
        if not isinstance(shared_state, list) or not all(isinstance(item, str) for item in shared_state):
            findings.add(EXIT_THREAD, f"{unit_id}: shared_state must be a string array")
            shared_state = []
        synchronization = thread.get("synchronization")
        # XCOM-UDI-04: shared mutable state is admissible only when the declared
        # model guards it (internally/externally synchronized or message passing).
        if shared_state and thread_model in NO_SHARED_STATE_THREAD_MODELS:
            findings.add(
                EXIT_THREAD,
                f"{unit_id}: model {thread_model} cannot declare shared mutable state",
            )
        if thread_model == "internally-synchronized":
            if not shared_state:
                findings.add(EXIT_THREAD, f"{unit_id}: internally-synchronized must declare its shared state")
            if not isinstance(synchronization, str) or not synchronization.strip():
                findings.add(
                    EXIT_THREAD,
                    f"{unit_id}: internally-synchronized must name its synchronization mechanism",
                )
        if thread_model in ("externally-synchronized", "message-passing"):
            if not isinstance(synchronization, str) or not synchronization.strip():
                findings.add(
                    EXIT_THREAD,
                    f"{unit_id}: model {thread_model} must declare its synchronization or boundary rule",
                )
        # A model that owns no shared mutable state must not claim a
        # synchronization mechanism: synchronization is null for exactly the
        # immutable-value/read-only-static/single-thread-owner/
        # offline-single-threaded/process-isolated models (and non-null above).
        if thread_model in UNSYNCHRONIZED_THREAD_MODELS and synchronization is not None:
            findings.add(
                EXIT_THREAD,
                f"{unit_id}: model {thread_model} must declare synchronization = null",
            )
        if thread_model == "message-passing":
            bounds = unit.get("bounds")
            kinds = {
                bound.get("kind")
                for bound in bounds
                if isinstance(bound, dict)
            } if isinstance(bounds, list) else set()
            if "capacity" not in kinds:
                findings.add(EXIT_THREAD, f"{unit_id}: message-passing requires a capacity bound")
            policies = unit.get("overflow_policies")
            if not isinstance(policies, list) or not policies or policies == ["n/a"]:
                findings.add(
                    EXIT_THREAD,
                    f"{unit_id}: message-passing requires a declared non-'n/a' overflow policy set",
                )


def _check_bounds(model: dict, findings: Findings) -> None:
    units = model.get("units")
    if not isinstance(units, list):
        return
    for unit in units:
        if not isinstance(unit, dict):
            continue
        unit_id = unit.get("id")
        bounds = unit.get("bounds")
        if not isinstance(bounds, list) or not bounds:
            findings.add(EXIT_BOUNDS, f"{unit_id}: at least one finite resource bound is required")
            continue
        seen: set[tuple[object, object]] = set()
        capacity_like = False
        for bound in bounds:
            if not isinstance(bound, dict):
                findings.add(EXIT_BOUNDS, f"{unit_id}: each bound must be an object")
                continue
            resource = bound.get("resource")
            kind = bound.get("kind")
            configured = bound.get("configured")
            value = bound.get("value")
            declared_in = bound.get("declared_in")
            if not isinstance(resource, str) or not resource.strip():
                findings.add(EXIT_BOUNDS, f"{unit_id}: bound resource must be a non-empty string")
            if not isinstance(kind, str) or kind not in BOUND_KIND_VOCABULARY:
                findings.add(EXIT_BOUNDS, f"{unit_id}: unknown bound kind {kind!r}")
            elif kind in CAPACITY_LIKE_KINDS:
                capacity_like = True
            if configured is not True:
                findings.add(EXIT_BOUNDS, f"{unit_id}: bound {resource!r} must declare configured = true")
            if value is not None:
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    findings.add(
                        EXIT_BOUNDS,
                        f"{unit_id}: bound {resource!r} value must be a non-negative integer or null",
                    )
                elif kind == "thread-count" and value < 1:
                    findings.add(EXIT_BOUNDS, f"{unit_id}: a thread-count bound must be at least 1")
                elif kind == "retry" and value != 0:
                    findings.add(EXIT_BOUNDS, f"{unit_id}: a retry bound must be 0 unless the plan permits one")
            if not isinstance(declared_in, str) or not declared_in.strip():
                findings.add(EXIT_BOUNDS, f"{unit_id}: bound {resource!r} must name its configuring source")
            key = (kind, resource)
            if key in seen:
                findings.add(EXIT_BOUNDS, f"{unit_id}: duplicate bound for (kind, resource) {key}")
            seen.add(key)
        policies = unit.get("overflow_policies")
        if not isinstance(policies, list) or not policies or not all(
            isinstance(policy, str) and policy in OVERFLOW_POLICY_VOCABULARY for policy in policies
        ):
            findings.add(EXIT_BOUNDS, f"{unit_id}: overflow_policies must be a non-empty policy vocabulary subset")
        elif capacity_like:
            if "n/a" in policies:
                findings.add(
                    EXIT_BOUNDS,
                    f"{unit_id}: a capacity/quota/depth/rate bound requires a real overflow policy, not 'n/a'",
                )
        elif policies != ["n/a"]:
            findings.add(
                EXIT_BOUNDS,
                f"{unit_id}: overflow_policies must be exactly ['n/a'] when no capacity/quota/depth/rate bound exists",
            )


def _is_durable_writer(unit: dict) -> bool:
    text = f"{unit.get('name', '')} {unit.get('responsibility', '')}".lower()
    return any(marker in text for marker in DURABLE_MARKERS)


def _check_failure(model: dict, findings: Findings) -> None:
    units = model.get("units")
    if not isinstance(units, list):
        return
    for unit in units:
        if not isinstance(unit, dict):
            continue
        unit_id = unit.get("id")
        failures = unit.get("failure_semantics")
        if not isinstance(failures, list) or not failures:
            findings.add(EXIT_FAILURE, f"{unit_id}: failure_semantics must declare at least one condition")
            continue
        outcomes = set()
        for entry in failures:
            if not isinstance(entry, dict):
                findings.add(EXIT_FAILURE, f"{unit_id}: each failure entry must be an object")
                continue
            condition = entry.get("condition")
            outcome = entry.get("outcome")
            if not isinstance(condition, str) or not condition.strip():
                findings.add(EXIT_FAILURE, f"{unit_id}: failure condition must be a non-empty string")
            if not isinstance(outcome, str):
                findings.add(EXIT_FAILURE, f"{unit_id}: failure outcome must be a string")
                continue
            outcomes.add(outcome)
            if isinstance(condition, str) and UNKNOWN_CONDITION_RE.search(condition):
                if outcome not in NON_SUCCESS_OUTCOMES:
                    findings.add(
                        EXIT_FAILURE,
                        f"{unit_id}: an unknown/indeterminate condition must not map to success ({outcome})",
                    )
        if _is_durable_writer(unit) and "evidence-incomplete" not in outcomes:
            findings.add(
                EXIT_FAILURE,
                f"{unit_id}: a journaled or durably written unit must declare an evidence-incomplete outcome",
            )


def _check_doxygen(model: dict, findings: Findings) -> None:
    plan = model.get("doxygen_plan")
    if not isinstance(plan, dict):
        findings.add(EXIT_DOXYGEN, "doxygen_plan must be an object")
        return
    if not isinstance(plan.get("configuration"), str) or not plan["configuration"].strip():
        findings.add(EXIT_DOXYGEN, "doxygen_plan must name its admitted configuration")
    if plan.get("warn_as_error") is not True:
        findings.add(EXIT_DOXYGEN, "doxygen_plan must declare the warning-as-error gate")
    if plan.get("mandatory_file_block") != MANDATORY_FILE_BLOCK:
        findings.add(EXIT_DOXYGEN, "doxygen_plan.mandatory_file_block differs from the declared set")
    mandatory_tags = plan.get("mandatory_public_tags")
    if not isinstance(mandatory_tags, list) or not set(MANDATORY_PUBLIC_TAGS).issubset(mandatory_tags):
        findings.add(EXIT_DOXYGEN, "doxygen_plan.mandatory_public_tags omits a required alias")
    groups = plan.get("groups")
    if not isinstance(groups, dict) or any(
        not isinstance(groups.get(family), str) or not groups.get(family) for family in FAMILY_VOCABULARY
    ):
        findings.add(EXIT_DOXYGEN, "doxygen_plan must declare one group per family")
        groups = groups if isinstance(groups, dict) else {}
    if not isinstance(plan.get("coverage_rule"), str) or not plan["coverage_rule"].strip():
        findings.add(EXIT_DOXYGEN, "doxygen_plan must declare its coverage rule")
    gaps = plan.get("gaps")
    if not isinstance(gaps, list) or not gaps:
        findings.add(EXIT_DOXYGEN, "doxygen_plan must record its known gaps")
    else:
        for gap in gaps:
            if not isinstance(gap, dict):
                findings.add(EXIT_DOXYGEN, "each Doxygen gap must be an object")
                continue
            if not isinstance(gap.get("owning_tasks"), list) or not gap["owning_tasks"]:
                findings.add(EXIT_DOXYGEN, f"gap {gap.get('id')} must name its owning tasks")
            if gap.get("status") in ("closed", "implemented"):
                findings.add(EXIT_DOXYGEN, f"gap {gap.get('id')} must not be reported as closed")

    units = model.get("units")
    if not isinstance(units, list):
        return
    for unit in units:
        if not isinstance(unit, dict):
            continue
        unit_id = unit.get("id")
        doxygen = unit.get("doxygen")
        if not isinstance(doxygen, dict):
            findings.add(EXIT_DOXYGEN, f"{unit_id}: doxygen obligation is missing")
            continue
        if unit.get("language") == "cpp":
            if doxygen.get("required") is not True:
                findings.add(EXIT_DOXYGEN, f"{unit_id}: every cpp unit must require a Doxygen obligation")
                continue
            if doxygen.get("group") != groups.get(unit.get("family")):
                findings.add(EXIT_DOXYGEN, f"{unit_id}: Doxygen group must equal the plan group for its family")
            file_block = doxygen.get("file_block")
            if not isinstance(file_block, list) or not set(MANDATORY_FILE_BLOCK).issubset(file_block):
                findings.add(EXIT_DOXYGEN, f"{unit_id}: mandatory file-block tags are incomplete")
            public_tags = doxygen.get("public_tags")
            if not isinstance(public_tags, list) or not set(MANDATORY_PUBLIC_TAGS).issubset(public_tags):
                findings.add(EXIT_DOXYGEN, f"{unit_id}: mandatory public tags are incomplete")
            documented = doxygen.get("documented_elements")
            public = doxygen.get("public_elements")
            if not isinstance(public, int) or isinstance(public, bool) or public < 1:
                findings.add(EXIT_DOXYGEN, f"{unit_id}: public_elements must be a positive integer")
            elif documented != public:
                findings.add(
                    EXIT_DOXYGEN,
                    f"{unit_id}: documented_elements must equal public_elements "
                    "for a required obligation",
                )
        else:
            if doxygen.get("required") is not False:
                findings.add(EXIT_DOXYGEN, f"{unit_id}: a non-cpp unit must declare required = false")
            if not isinstance(doxygen.get("reason"), str) or not doxygen["reason"].strip():
                findings.add(EXIT_DOXYGEN, f"{unit_id}: a non-cpp unit must give a reason")


# ---------------------------------------------------------------------------
# Cross-resolution, coverage, governance, binding, paths
# ---------------------------------------------------------------------------


def _component_index(architecture_model: object) -> dict[str, dict]:
    if not isinstance(architecture_model, dict):
        return {}
    return {
        str(component.get("id")): component
        for component in architecture_model.get("components", [])
        if isinstance(component, dict)
    }


def _contract_ids(architecture_model: object) -> set[str]:
    if not isinstance(architecture_model, dict):
        return set()
    return {
        str(contract.get("id"))
        for contract in architecture_model.get("contracts", [])
        if isinstance(contract, dict)
    }


def _register_ids(requirement_register: object) -> set[str]:
    if not isinstance(requirement_register, dict):
        return set()
    return {
        str(requirement.get("id"))
        for requirement in requirement_register.get("requirements", [])
        if isinstance(requirement, dict)
    }


def _check_coverage(
    model: dict,
    architecture_model: object,
    requirement_register: object,
    findings: Findings,
) -> None:
    units = model.get("units")
    if not isinstance(units, list):
        return
    components = _component_index(architecture_model)
    contracts = _contract_ids(architecture_model)
    register = _register_ids(requirement_register)
    if not components or not contracts or not register:
        findings.add(EXIT_BINDING, "component, contract, or requirement dependency is unavailable")
        return

    required = [f"XCOM-DU-{number:03d}" for number in range(1, EXPECTED_UNIT_TOTAL + 1)]
    declared = [str(unit.get("id")) for unit in units if isinstance(unit, dict)]
    if sorted(declared) != required:
        findings.add(EXIT_BINDING, "the declared unit-id set must equal XCOM-DU-001..030 exactly")

    covered_components: set[str] = set()
    covered_requirements: set[str] = set()
    for unit in units:
        if not isinstance(unit, dict):
            continue
        unit_id = unit.get("id")
        family = unit.get("family")
        component_refs = unit.get("component_refs")
        contract_refs = unit.get("contract_refs")
        for ref in component_refs if isinstance(component_refs, list) else []:
            if ref not in components:
                findings.add(EXIT_BINDING, f"{unit_id}: component reference {ref!r} does not resolve")
            else:
                covered_components.add(ref)
        for ref in contract_refs if isinstance(contract_refs, list) else []:
            if ref not in contracts:
                findings.add(EXIT_BINDING, f"{unit_id}: contract reference {ref!r} does not resolve")
        if family in ("CORE", "XDL", "OBS", "STIM", "GW") and not component_refs:
            findings.add(EXIT_BINDING, f"{unit_id}: family {family} requires at least one component reference")
        for link in unit.get("requirement_links") if isinstance(unit.get("requirement_links"), list) else []:
            if link not in register:
                findings.add(EXIT_BINDING, f"{unit_id}: requirement link {link!r} does not resolve in the T008 register")
            else:
                covered_requirements.add(link)

    coverage = model.get("coverage") if isinstance(model.get("coverage"), dict) else {}
    component_exemptions = coverage.get("component_exemptions", [])
    requirement_exemptions = coverage.get("requirement_exemptions", [])
    exempt_components = {
        entry.get("id") for entry in component_exemptions if isinstance(entry, dict)
    } if isinstance(component_exemptions, list) else set()
    exempt_requirements = {
        entry.get("id") for entry in requirement_exemptions if isinstance(entry, dict)
    } if isinstance(requirement_exemptions, list) else set()

    for component_id, component in components.items():
        if component.get("scope") != "first-proof":
            continue
        if component_id in covered_components or component_id in exempt_components:
            continue
        findings.add(EXIT_BINDING, f"first-proof component {component_id} is covered by no unit")

    software_requirements = {
        requirement_id for requirement_id in register if requirement_id.startswith("XCOM-SW-")
    }
    for requirement_id in sorted(software_requirements):
        if requirement_id in covered_requirements or requirement_id in exempt_requirements:
            continue
        findings.add(EXIT_BINDING, f"software requirement {requirement_id} is covered by no unit")

    for entry in component_exemptions if isinstance(component_exemptions, list) else []:
        if not isinstance(entry, dict):
            findings.add(EXIT_BINDING, "each component exemption must be an object")
            continue
        target = entry.get("id")
        if target not in components:
            findings.add(EXIT_BINDING, f"component exemption {target!r} does not resolve")
        elif target in covered_components:
            findings.add(EXIT_BINDING, f"component exemption {target} is invalid: the component is covered")
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            findings.add(EXIT_BINDING, f"component exemption {target} must carry a reason")
        if not isinstance(entry.get("owning_tasks"), list) or not entry["owning_tasks"]:
            findings.add(EXIT_BINDING, f"component exemption {target} must name its owning tasks")
    for entry in requirement_exemptions if isinstance(requirement_exemptions, list) else []:
        if not isinstance(entry, dict):
            findings.add(EXIT_BINDING, "each requirement exemption must be an object")
            continue
        target = entry.get("id")
        if target not in register:
            findings.add(EXIT_BINDING, f"requirement exemption {target!r} does not resolve")
        elif target in covered_requirements:
            findings.add(EXIT_BINDING, f"requirement exemption {target} is invalid: the requirement is covered")
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            findings.add(EXIT_BINDING, f"requirement exemption {target} must carry a reason")
        if not isinstance(entry.get("owning_tasks"), list) or not entry["owning_tasks"]:
            findings.add(EXIT_BINDING, f"requirement exemption {target} must name its owning tasks")


def _check_governance(
    model: dict,
    architecture_model: object,
    task_ownership: object,
    findings: Findings,
) -> None:
    units = model.get("units")
    if not isinstance(units, list):
        return
    components = _component_index(architecture_model)
    # The implemented-implies-accepted cross-check is only meaningful when the T007
    # register is available; an unavailable dependency is a BINDING_INVALID failure
    # reported by _check_dependencies, never a governance failure here.
    accepted_tasks: dict[str, str] | None = None
    if isinstance(task_ownership, dict) and isinstance(task_ownership.get("slices"), list):
        accepted_tasks = {}
        for slice_record in task_ownership.get("slices", []):
            if not isinstance(slice_record, dict):
                continue
            for task, entry in slice_record.get("reconciliation", {}).items():
                if isinstance(entry, dict) and entry.get("status") == "accepted":
                    accepted_tasks[task] = entry.get("revision")

    for unit in units:
        if not isinstance(unit, dict):
            continue
        unit_id = unit.get("id")
        adrs = unit.get("governing_adrs")
        if not isinstance(adrs, list) or not adrs or not set(adrs).issubset(ADR_VOCABULARY):
            findings.add(EXIT_GOVERNANCE, f"{unit_id}: governing_adrs must be a non-empty accepted subset")
        maturity = unit.get("maturity")
        revision = unit.get("accepted_revision")
        reconciliation = unit.get("reconciliation")
        if maturity == "implemented":
            if not isinstance(revision, str) or not SHA_RE.fullmatch(revision):
                findings.add(
                    EXIT_GOVERNANCE,
                    f"{unit_id}: an implemented unit requires an exact 40-hex accepted revision",
                )
            if reconciliation not in (None, ""):
                findings.add(EXIT_GOVERNANCE, f"{unit_id}: an implemented unit must not carry a reconciliation reason")
            tasks = unit.get("owning_tasks") if isinstance(unit.get("owning_tasks"), list) else []
            if accepted_tasks is not None:
                for task in tasks:
                    if accepted_tasks.get(task) is None:
                        findings.add(
                            EXIT_GOVERNANCE,
                            f"{unit_id}: implemented ownership task {task} is not accepted in the T007 register",
                        )
                    elif revision != accepted_tasks[task]:
                        findings.add(
                            EXIT_GOVERNANCE,
                            f"{unit_id}: accepted revision differs from the recorded T007 revision for {task}",
                        )
        elif maturity == "partial":
            if not isinstance(reconciliation, str) or not reconciliation.strip():
                findings.add(
                    EXIT_GOVERNANCE,
                    f"{unit_id}: an unreconciled partial unit must carry a reconciliation reason",
                )
            if revision not in (None, ""):
                findings.add(EXIT_GOVERNANCE, f"{unit_id}: a partial unit must not carry an accepted revision")
        else:
            if revision not in (None, ""):
                findings.add(EXIT_GOVERNANCE, f"{unit_id}: only an implemented unit may carry an accepted revision")
            if reconciliation not in (None, ""):
                findings.add(EXIT_GOVERNANCE, f"{unit_id}: only a partial unit may carry a reconciliation reason")

        if unit.get("family") == "CORE":
            text = " ".join(
                str(unit.get(field, "")) for field in ("name", "responsibility", "notes")
            )
            for primitive in DOMAIN_PRIMITIVES:
                if re.search(rf"\b{re.escape(primitive)}\b", text):
                    findings.add(
                        EXIT_GOVERNANCE,
                        f"{unit_id}: core unit names a domain-specific primitive ({primitive})",
                    )
        if unit.get("family") in RUNTIME_FAMILIES:
            for ref in unit.get("component_refs") if isinstance(unit.get("component_refs"), list) else []:
                component = components.get(ref)
                if isinstance(component, dict) and component.get("layer") in UPSTREAM_COMPONENT_LAYERS:
                    findings.add(
                        EXIT_GOVERNANCE,
                        f"{unit_id}: reverse dependency on upstream component {ref} ({component.get('layer')})",
                    )

    ref002 = model.get("ref002") if isinstance(model.get("ref002"), dict) else {}
    if ref002.get("disposition") != "unchanged":
        findings.add(EXIT_GOVERNANCE, "ref002.disposition must remain unchanged")
    if ref002.get("promoted") not in ([], None):
        findings.add(EXIT_GOVERNANCE, "ref002.promoted must be empty; T010 promotes no target")

    invariants = model.get("invariants")
    if isinstance(invariants, list):
        index = {
            str(invariant.get("id")): invariant
            for invariant in invariants
            if isinstance(invariant, dict)
        }
        for invariant_id, (kind, statement) in PINNED_INVARIANTS.items():
            invariant = index.get(invariant_id)
            if invariant is None:
                findings.add(EXIT_GOVERNANCE, f"pinned invariant {invariant_id} is absent")
            elif invariant.get("kind") != kind or invariant.get("statement") != statement:
                findings.add(EXIT_GOVERNANCE, f"pinned invariant {invariant_id} was weakened or reworded")
        for invariant_id in REQUIRED_PRESENT_INVARIANTS:
            if invariant_id not in index:
                findings.add(EXIT_GOVERNANCE, f"required invariant {invariant_id} is absent")


def _check_dependencies(
    task_ownership: object,
    requirement_register: object,
    architecture_model: object,
    findings: Findings,
) -> None:
    if not isinstance(task_ownership, dict) or not isinstance(task_ownership.get("task_assignment"), dict):
        findings.add(EXIT_BINDING, "the T007 task-ownership dependency is unavailable or malformed")
    if not isinstance(requirement_register, dict) or not isinstance(
        requirement_register.get("requirements"), list
    ):
        findings.add(EXIT_BINDING, "the T008 requirement-register dependency is unavailable or malformed")
    if not isinstance(architecture_model, dict) or not isinstance(
        architecture_model.get("components"), list
    ):
        findings.add(EXIT_BINDING, "the T009 architecture-model dependency is unavailable or malformed")


def _check_binding(
    model: dict,
    task_ownership: object,
    requirement_register: object,
    architecture_model: object,
    findings: Findings,
) -> None:
    baseline = model.get("baseline_revision")
    if not isinstance(baseline, str) or not SHA_RE.fullmatch(baseline):
        findings.add(EXIT_BINDING, "baseline_revision must be a 40-hex lowercase SHA")
    elif baseline != RUN_BASELINE:
        findings.add(EXIT_BINDING, "baseline_revision must bind the authorized run baseline")
    if model.get("authorization_records") != AUTHORIZATION_RECORDS:
        findings.add(
            EXIT_BINDING,
            "authorization_records must equal the closed accepted set ACC001-ACC015 and ADR-0018..0020",
        )
    units = model.get("units")
    if isinstance(units, list):
        for unit in units:
            if not isinstance(unit, dict):
                continue
            for artifact in unit.get("artifact_paths") if isinstance(unit.get("artifact_paths"), list) else []:
                if not isinstance(artifact, dict) or artifact.get("status") not in ("established", "planned"):
                    findings.add(
                        EXIT_BINDING,
                        f"{unit.get('id')}: every artifact path must be tagged established or planned",
                    )
    _check_dependencies(task_ownership, requirement_register, architecture_model, findings)


def _check_paths(model: dict, findings: Findings) -> None:
    units = model.get("units")
    if not isinstance(units, list):
        return
    for unit in units:
        if not isinstance(unit, dict):
            continue
        for artifact in unit.get("artifact_paths") if isinstance(unit.get("artifact_paths"), list) else []:
            if not isinstance(artifact, dict):
                continue
            path = artifact.get("path")
            status = artifact.get("status")
            if not isinstance(path, str) or not path:
                continue
            exists = (ROOT / path).exists()
            if status == "established" and not exists:
                findings.add(EXIT_PATH, f"{unit.get('id')}: established path {path} is absent from the tree")
            elif status == "planned" and exists:
                findings.add(EXIT_PATH, f"{unit.get('id')}: planned path {path} is already present in the tree")


def _check_determinism(model: dict, raw_text: str | None, markdown_text: str | None, source: str, findings: Findings) -> None:
    if raw_text is not None and serialize(model) != raw_text:
        findings.add(EXIT_DETERMINISM, "model serialization is not byte-stable canonical JSON")
    if markdown_text is not None and project_markdown(model) != markdown_text:
        findings.add(EXIT_DETERMINISM, f"{source} is not the deterministic projection of the model")


def _scan_public_safety(text: str, source: str, findings: Findings) -> None:
    for label, pattern in PUBLIC_SAFETY_PATTERNS:
        for match in pattern.finditer(text):
            findings.add(
                EXIT_PUBLIC_SAFETY,
                f"{source} contains a prohibited public-safety class ({label}) near offset {match.start()}",
            )


def run_checks(
    model: object,
    *,
    task_ownership: object,
    requirement_register: object,
    architecture_model: object,
    raw_text: str | None = None,
    markdown_text: str | None = None,
    markdown_source: str = "design-units.md",
) -> Findings:
    """Run every deterministic check and return the classified findings."""

    findings = Findings()
    if not _check_model_schema(model, findings):
        return findings
    assert isinstance(model, dict)
    _check_ordering(model, findings)
    _check_identity(model, findings)
    _check_ownership(model, task_ownership, findings)
    _check_thread_safety(model, findings)
    _check_bounds(model, findings)
    _check_failure(model, findings)
    _check_doxygen(model, findings)
    _check_coverage(model, architecture_model, requirement_register, findings)
    _check_governance(model, architecture_model, task_ownership, findings)
    _check_binding(model, task_ownership, requirement_register, architecture_model, findings)
    _check_paths(model, findings)
    _check_determinism(model, raw_text, markdown_text, markdown_source, findings)
    if raw_text is not None:
        _scan_public_safety(raw_text, "unit-design.json", findings)
    if markdown_text is not None:
        _scan_public_safety(markdown_text, markdown_source, findings)
    return findings


# ---------------------------------------------------------------------------
# CLI, loading, and evidence emission
# ---------------------------------------------------------------------------


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


def _parse_json(raw_text: str | None, path: Path, findings: Findings, exit_class: int) -> object:
    if raw_text is None:
        return None
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as error:
        findings.add(exit_class, f"{path.name} is not valid JSON: {error.msg}")
        return None


def _load_json(path: Path, findings: Findings, exit_class: int) -> object:
    return _parse_json(_read_bounded(path, findings), path, findings, exit_class)


def _load_context() -> tuple[object, object, object, object, str | None, Findings]:
    findings = Findings()
    total = 0
    for path in (MODEL_JSON, MODEL_MD, DEP_TASK_OWNERSHIP, DEP_REQUIREMENT_REGISTER, DEP_ARCHITECTURE_MODEL):
        if path.is_file():
            total += path.stat().st_size
    if total > MAX_TOTAL_BYTES:
        findings.add(EXIT_IO, "total input exceeds the 4 MiB bound")
    model_text = _read_bounded(MODEL_JSON, findings)
    model = _parse_json(model_text, MODEL_JSON, findings, EXIT_SCHEMA)
    task_ownership = _load_json(DEP_TASK_OWNERSHIP, findings, EXIT_BINDING)
    requirement_register = _load_json(DEP_REQUIREMENT_REGISTER, findings, EXIT_BINDING)
    architecture_model = _load_json(DEP_ARCHITECTURE_MODEL, findings, EXIT_BINDING)
    return model, task_ownership, requirement_register, architecture_model, model_text, findings


def _emit(findings: Findings) -> int:
    exit_code = findings.exit_code()
    if exit_code == EXIT_OK:
        print("X-COM unit-design validation passed")
        return EXIT_OK
    print(
        f"X-COM unit-design validation FAILED: {CLASS_NAMES[exit_code]} (exit {exit_code})",
        file=sys.stderr,
    )
    for line in findings.diagnostics():
        print(f"- {line}", file=sys.stderr)
    return exit_code


def _verify() -> int:
    model, task_ownership, requirement_register, architecture_model, raw_text, findings = _load_context()
    if model is None:
        return _emit(findings)
    result = run_checks(
        model,
        task_ownership=task_ownership,
        requirement_register=requirement_register,
        architecture_model=architecture_model,
        raw_text=raw_text,
    )
    for exit_class, messages in result.by_class.items():
        for message in messages:
            findings.add(exit_class, message)
    return _emit(findings)


def _check_human() -> int:
    model, task_ownership, requirement_register, architecture_model, raw_text, findings = _load_context()
    if model is None:
        return _emit(findings)
    markdown_text = _read_bounded(MODEL_MD, findings)
    result = run_checks(
        model,
        task_ownership=task_ownership,
        requirement_register=requirement_register,
        architecture_model=architecture_model,
        raw_text=raw_text,
        markdown_text=markdown_text,
        markdown_source=MODEL_MD.name,
    )
    for exit_class, messages in result.by_class.items():
        for message in messages:
            findings.add(exit_class, message)
    return _emit(findings)


# ---------------------------------------------------------------------------
# Self-test fixtures
# ---------------------------------------------------------------------------


def _copy(model: dict) -> dict:
    return json.loads(json.dumps(model))


def _unit(model: dict, unit_id: str) -> dict:
    for unit in model["units"]:
        if unit.get("id") == unit_id:
            return unit
    raise KeyError(unit_id)


def _negative_fixtures(base: dict, task_ownership: object) -> list[tuple[str, int, dict]]:
    """Return the declared NEG-01..NEG-46 fixtures (each isolates one defect)."""

    fixtures: list[tuple[str, int, dict]] = []

    model = _copy(base)
    del model["counts"]
    fixtures.append(("NEG-01", EXIT_SCHEMA, model))

    model = _copy(base)
    model["counts"]["CORE"] = model["counts"]["CORE"] + 1
    fixtures.append(("NEG-02", EXIT_SCHEMA, model))

    model = _copy(base)
    model["units"] = list(reversed(model["units"]))
    fixtures.append(("NEG-03", EXIT_SCHEMA, model))

    model = _copy(base)
    model["units"][0]["id"] = 5
    fixtures.append(("NEG-04", EXIT_SCHEMA, model))

    model = _copy(base)
    model["units"][0]["id"] = ["XCOM-DU-001"]
    fixtures.append(("NEG-05", EXIT_SCHEMA, model))

    model = _copy(base)
    model["units"][0]["id"] = {"name": "XCOM-DU-001"}
    fixtures.append(("NEG-05b", EXIT_SCHEMA, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-005")["id"] = "XCOM-DU-004"
    fixtures.append(("NEG-06", EXIT_IDENTITY, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["family"] = "CORE2"
    fixtures.append(("NEG-07", EXIT_IDENTITY, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["name"] = ""
    fixtures.append(("NEG-08", EXIT_IDENTITY, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["artifact_paths"] = []
    fixtures.append(("NEG-09", EXIT_IDENTITY, model))

    # T010-IR-07: every mandatory per-unit scalar must be present, not skipped.
    # Delete each of family/kind/language/scope/maturity from a non-cpp unit
    # (XCOM-DU-026) and from a cpp unit (XCOM-DU-006); each is IDENTITY_INVALID (3).
    for offset, field in enumerate(("family", "kind", "language", "scope", "maturity")):
        model = _copy(base)
        del _unit(model, "XCOM-DU-026")[field]
        fixtures.append((f"NEG-08{chr(ord('b') + offset)}", EXIT_IDENTITY, model))
    for offset, field in enumerate(("family", "kind", "language", "scope", "maturity")):
        model = _copy(base)
        del _unit(model, "XCOM-DU-006")[field]
        fixtures.append((f"NEG-08{chr(ord('g') + offset)}", EXIT_IDENTITY, model))

    # T010-IR-08: planned_evidence must be a non-empty string array, and each
    # artifact_paths entry must carry a non-empty string path.
    model = _copy(base)
    _unit(model, "XCOM-DU-002")["planned_evidence"] = []
    fixtures.append(("NEG-08l", EXIT_IDENTITY, model))

    model = _copy(base)
    del _unit(model, "XCOM-DU-002")["planned_evidence"]
    fixtures.append(("NEG-08m", EXIT_IDENTITY, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["artifact_paths"] = [{"status": "established"}]
    fixtures.append(("NEG-09b", EXIT_IDENTITY, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["thread_safety"]["model"] = "chaotic"
    fixtures.append(("NEG-10", EXIT_IDENTITY, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["failure_semantics"][0]["outcome"] = "ok"
    fixtures.append(("NEG-11", EXIT_IDENTITY, model))

    model = _copy(base)
    del _unit(model, "XCOM-DU-002")["ownership_model"]
    fixtures.append(("NEG-12", EXIT_OWNERSHIP, model))

    model = _copy(base)
    del _unit(model, "XCOM-DU-002")["lifetime_model"]
    fixtures.append(("NEG-13", EXIT_OWNERSHIP, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["owning_tasks"] = []
    fixtures.append(("NEG-14", EXIT_OWNERSHIP, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-006")["ownership_model"] = "caller-owns-value"
    fixtures.append(("NEG-15", EXIT_OWNERSHIP, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["owning_slice"] = "T-OBS"
    fixtures.append(("NEG-16", EXIT_OWNERSHIP, model))

    model = _copy(base)
    del _unit(model, "XCOM-DU-006")["thread_safety"]["model"]
    fixtures.append(("NEG-17", EXIT_THREAD, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-001")["thread_safety"]["shared_state"] = ["mutable cache"]
    fixtures.append(("NEG-18", EXIT_THREAD, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-008")["thread_safety"]["shared_state"] = ["per-route in-flight queue"]
    fixtures.append(("NEG-18b", EXIT_THREAD, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-006")["thread_safety"]["synchronization"] = None
    fixtures.append(("NEG-19", EXIT_THREAD, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-001")["thread_safety"]["synchronization"] = "claim a mutex where none is needed"
    fixtures.append(("NEG-19b", EXIT_THREAD, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-001")["view_lifetime"] = None
    fixtures.append(("NEG-20", EXIT_OWNERSHIP, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["bounds"] = []
    fixtures.append(("NEG-21", EXIT_BOUNDS, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["bounds"][0]["value"] = -1
    fixtures.append(("NEG-22", EXIT_BOUNDS, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-006")["overflow_policies"] = []
    fixtures.append(("NEG-23", EXIT_BOUNDS, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-006")["overflow_policies"] = ["n/a"]
    fixtures.append(("NEG-24", EXIT_BOUNDS, model))

    model = _copy(base)
    for bound in _unit(model, "XCOM-DU-006")["bounds"]:
        if bound["kind"] == "retry":
            bound["value"] = 1
    fixtures.append(("NEG-24b", EXIT_BOUNDS, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["failure_semantics"] = []
    fixtures.append(("NEG-25", EXIT_FAILURE, model))

    model = _copy(base)
    for entry in _unit(model, "XCOM-DU-006")["failure_semantics"]:
        if UNKNOWN_CONDITION_RE.search(entry["condition"]):
            entry["outcome"] = "accepted"
    fixtures.append(("NEG-26", EXIT_FAILURE, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-016")["failure_semantics"] = [
        entry
        for entry in _unit(model, "XCOM-DU-016")["failure_semantics"]
        if entry["outcome"] != "evidence-incomplete"
    ]
    fixtures.append(("NEG-27", EXIT_FAILURE, model))

    model = _copy(base)
    tags = _unit(model, "XCOM-DU-006")["doxygen"]["public_tags"]
    _unit(model, "XCOM-DU-006")["doxygen"]["public_tags"] = [tag for tag in tags if tag != "ownership"]
    fixtures.append(("NEG-28", EXIT_DOXYGEN, model))

    model = _copy(base)
    model["doxygen_plan"]["warn_as_error"] = False
    fixtures.append(("NEG-29", EXIT_DOXYGEN, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-006")["doxygen"]["documented_elements"] = 3
    fixtures.append(("NEG-30", EXIT_DOXYGEN, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["governing_adrs"] = sorted(
        _unit(model, "XCOM-DU-002")["governing_adrs"] + ["ADR-9999"]
    )
    fixtures.append(("NEG-31", EXIT_GOVERNANCE, model))

    model = _copy(base)
    model["ref002"]["promoted"] = ["XVE-SYS-0139"]
    fixtures.append(("NEG-32", EXIT_GOVERNANCE, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["reconciliation"] = None
    fixtures.append(("NEG-33", EXIT_GOVERNANCE, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-028")["maturity"] = "implemented"
    fixtures.append(("NEG-33b", EXIT_GOVERNANCE, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["name"] = "Contract and logical identity (ECU/CAN bridge)"
    fixtures.append(("NEG-34", EXIT_GOVERNANCE, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-006")["component_refs"] = ["XCOM-CMP-002"]
    fixtures.append(("NEG-34b", EXIT_GOVERNANCE, model))

    model = _copy(base)
    model["baseline_revision"] = "abc"
    fixtures.append(("NEG-35", EXIT_BINDING, model))

    model = _copy(base)
    records = list(model["authorization_records"])
    records[records.index("ACC015")] = "ACC099"
    model["authorization_records"] = records
    fixtures.append(("NEG-36", EXIT_BINDING, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["requirement_links"] = ["XCOM-SW-CORE-001", "XCOM-SW-CORE-999"]
    fixtures.append(("NEG-37", EXIT_BINDING, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["requirement_links"] = ["XCOM-SW-CORE-001", "FR-001"]
    fixtures.append(("NEG-39", EXIT_BINDING, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["notes"] = "/home/someuser/secret.txt"
    fixtures.append(("NEG-41", EXIT_PUBLIC_SAFETY, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["artifact_paths"] = [
        {"path": "src/xverse/xcom/include/xverse/xcom/absent_header.hpp", "status": "established"}
    ]
    fixtures.append(("NEG-42", EXIT_PATH, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-002")["artifact_paths"] = [
        {"path": "src/xverse/xcom/include/xverse/xcom/contract.hpp", "status": "planned"}
    ]
    fixtures.append(("NEG-43", EXIT_PATH, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-006")["component_refs"] = ["XCOM-CMP-004"]
    fixtures.append(("NEG-44", EXIT_BINDING, model))

    model = _copy(base)
    _unit(model, "XCOM-DU-013")["requirement_links"] = ["XCOM-SW-OBS-003"]
    fixtures.append(("NEG-45", EXIT_BINDING, model))

    model = _copy(base)
    model["coverage"]["component_exemptions"] = [
        {
            "id": "XCOM-CMP-004",
            "reason": "controlled self-test fixture for an invalid exemption",
            "owning_tasks": ["T012"],
        }
    ]
    fixtures.append(("NEG-46", EXIT_BINDING, model))

    return fixtures


def _self_test() -> int:
    model, task_ownership, requirement_register, architecture_model, model_text, load_findings = _load_context()
    if model is None:
        for line in load_findings.diagnostics():
            print(f"- {line}", file=sys.stderr)
        print("X-COM unit-design self-test FAILED: positive fixture is unavailable", file=sys.stderr)
        return EXIT_IO

    raw = model_text if model_text is not None else serialize(model)
    markdown = project_markdown(model)
    positive = run_checks(
        model,
        task_ownership=task_ownership,
        requirement_register=requirement_register,
        architecture_model=architecture_model,
        raw_text=raw,
        markdown_text=markdown,
    )
    if positive.exit_code() != EXIT_OK:
        for line in positive.diagnostics():
            print(f"- {line}", file=sys.stderr)
        print("X-COM unit-design self-test FAILED: positive fixture did not pass", file=sys.stderr)
        return EXIT_DETERMINISM

    failures = 0
    print("positive fixture: passed")
    for name, expected, mutated in _negative_fixtures(model, task_ownership):
        result = run_checks(
            mutated,
            task_ownership=task_ownership,
            requirement_register=requirement_register,
            architecture_model=architecture_model,
            raw_text=serialize(mutated),
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

    # NEG-38: an unavailable dependency is a hard BINDING_INVALID, never a skipped check.
    withheld = run_checks(
        model,
        task_ownership=None,
        requirement_register=requirement_register,
        architecture_model=architecture_model,
        raw_text=raw,
    )
    if withheld.exit_code() == EXIT_BINDING:
        print("NEG-38: withheld dependency rejected with BINDING_INVALID (exit 10)")
    else:
        failures += 1
        print(
            f"NEG-38: expected BINDING_INVALID (exit 10) but got exit {withheld.exit_code()}",
            file=sys.stderr,
        )

    # NEG-40: a tampered Markdown projection is a determinism defect.
    tampered = markdown + "tampered\n"
    projection = run_checks(
        model,
        task_ownership=task_ownership,
        requirement_register=requirement_register,
        architecture_model=architecture_model,
        raw_text=raw,
        markdown_text=tampered,
    )
    if projection.exit_code() == EXIT_DETERMINISM:
        print("NEG-40: tampered projection rejected with DETERMINISM_INVALID (exit 11)")
    else:
        failures += 1
        print(
            f"NEG-40: expected DETERMINISM_INVALID (exit 11) but got exit {projection.exit_code()}",
            file=sys.stderr,
        )

    if failures:
        print(
            f"X-COM unit-design self-test FAILED: {failures} fixture(s) did not behave as declared",
            file=sys.stderr,
        )
        return EXIT_GOVERNANCE
    print("X-COM unit-design self-test passed")
    return EXIT_OK


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--self-test", action="store_true", help="run controlled positive/negative fixtures")
    group.add_argument("--verify", action="store_true", help="validate the unit-design model (default)")
    group.add_argument(
        "--check-human",
        action="store_true",
        help="validate the model and its deterministic Markdown projection",
    )
    args = parser.parse_args()
    if args.self_test:
        return _self_test()
    if args.check_human:
        return _check_human()
    return _verify()


if __name__ == "__main__":
    raise SystemExit(main())
