#!/usr/bin/env python3
"""Offline validator for the X-COM T007 task-ownership register.

The register binds the capability-007 work slices to their exact baseline, their
accepted authorization records, their exclusive/shared path ownership, their
dependency order, and their required evidence/acceptance gates.  This validator
is a repository-owned, deterministic, single-threaded, offline checker.  It reads
only repository-relative files, never writes the candidate tree, never opens a
network peer or a subprocess, and returns a distinct nonzero exit class per
failure family so callers (including the ``--self-test`` fixtures) can bind a
result to the exact defect it detected.

Public safety: the register, its Markdown projection, and this validator's output
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
REGISTER_JSON = ROOT / "docs" / "engineering" / "xcom" / "task-ownership.json"
REGISTER_MD = ROOT / "docs" / "engineering" / "xcom" / "task-ownership.md"

EXIT_OK = 0
EXIT_SCHEMA = 2
EXIT_SLICE_SET = 3
EXIT_ASSIGNMENT = 4
EXIT_BINDING = 5
EXIT_PATHS = 6
EXIT_DEPENDENCY = 7
EXIT_GATE = 8
EXIT_DETERMINISM = 9
EXIT_PUBLIC_SAFETY = 10
EXIT_IO = 11

CLASS_NAMES = {
    EXIT_OK: "OK",
    EXIT_SCHEMA: "SCHEMA_INVALID",
    EXIT_SLICE_SET: "SLICE_SET_INVALID",
    EXIT_ASSIGNMENT: "ASSIGNMENT_INVALID",
    EXIT_BINDING: "BINDING_INVALID",
    EXIT_PATHS: "PATH_OWNERSHIP_INVALID",
    EXIT_DEPENDENCY: "DEPENDENCY_INVALID",
    EXIT_GATE: "GATE_INVALID",
    EXIT_DETERMINISM: "DETERMINISM_INVALID",
    EXIT_PUBLIC_SAFETY: "PUBLIC_SAFETY_INVALID",
    EXIT_IO: "IO_ERROR",
}

MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 4 * 1024 * 1024

SLICE_ORDER = ["T-CORE", "T-XDL", "T-OBS", "T-STIM", "T-INTG", "T-ENABLER", "T-REVIEW"]
PRODUCING_TASK = "T007"
PRODUCING_OWNER = "T-PRODUCING"
# The producing task's per-task work products are owned by the engineering-baseline
# enabler group, which is the first slice to consume them (T007 -> T-ENABLER).
PRODUCING_TASK_DIR_OWNER = "T-ENABLER"
PER_TASK_DOC_DIR = "docs/engineering/xcom/{task}/"
QUEUE_PACKAGE_FILE = "reports/xcom-queue/{task}-package.json"
TASK_IDS = [f"T{number:03d}" for number in range(7, 42)]
CONSUMING_TASKS = [f"T{number:03d}" for number in range(8, 42)]
AUTH_RECORDS = [f"ACC{number:03d}" for number in range(1, 16)] + [
    "ADR-0018",
    "ADR-0019",
    "ADR-0020",
]

# The four indices below fix the minimum prohibitions; the remaining two state the
# public-safety content rule and the accepted-ADR/no-weakening boundary rule.
# ``global_prohibitions`` is stored sorted.
MINIMUM_PROHIBITIONS = (
    "no TCP listener",
    "no execution of any legacy binary or workload",
    "no external network peer",
    "no modification of any legacy The-Xverse repository",
)
PUBLIC_SAFETY_PROHIBITION = (
    "no public evidence containing sensitive deployment values, private addresses, "
    "unrestricted payloads, or absolute host paths"
)
BOUNDARY_PROHIBITION = (
    "no rewrite of an accepted ADR or weakening of an existing requirement or test"
)
GLOBAL_PROHIBITIONS = sorted(
    MINIMUM_PROHIBITIONS + (PUBLIC_SAFETY_PROHIBITION, BOUNDARY_PROHIBITION)
)

SHARED_PATH_REQUIRED_SUBSTRINGS = (
    "CMakeLists.txt",
    "src/xverse/xcom/CMakeLists.txt",
    "cmake/",
    "specs/007-xcom-core/",
)

TOP_FIELDS = [
    "schema_version",
    "task_id",
    "baseline_revision",
    "candidate_revision_rule",
    "authorization_records",
    "global_prohibitions",
    "shared_paths",
    "slices",
    "task_assignment",
    "dependency_edges",
]

SLICE_FIELDS = [
    "id",
    "title",
    "owning_tasks",
    "purpose",
    "authorized_baseline",
    "authorization_refs",
    "paths_exclusive",
    "paths_shared",
    "dependencies",
    "required_evidence",
    "acceptance_gate",
    "prohibitions",
    "reconciliation",
    "ref002_disposition",
]

SORTED_SLICE_ARRAYS = (
    "owning_tasks",
    "authorization_refs",
    "paths_exclusive",
    "paths_shared",
    "dependencies",
    "required_evidence",
    "prohibitions",
)

RECON_FIELDS = ["status", "revision", "reason"]
RECON_STATUSES = ("accepted", "delivered", "unreconciled", "allocated", "deferred")

# T011-T016/T021-T024 were explicitly accepted together after terminal review R-01.
# Their acceptance decision binds the complete successor, not the intermediate
# per-task delivery commits. Keep the accepted T025 decision bound separately.
DELIVERED_TASKS = {}
ACCEPTED_TASKS = {
    **{task: "2f08355c418a20eb00cbea18506f85bf2ea883b7" for task in (
        "T011", "T012", "T013", "T014", "T015", "T016",
        "T021", "T022", "T023", "T024",
    )},
    "T025": "4b01586b438a8587d231ee8828d896c206c06a96",
}
ALLOCATED_TASKS = [
    task for task in CONSUMING_TASKS
    if task not in DELIVERED_TASKS and task not in ACCEPTED_TASKS
]

# Ordering constraints that the validator enforces by reachability.  Every pair
# (earlier, later) must be reachable along the declared dependency edges; the
# pairs also imply that T-ENABLER transitively precedes every later slice.
REQUIRED_ORDER_PAIRS = (
    ("T-ENABLER", "T-CORE"),
    ("T-CORE", "T-XDL"),
    ("T-CORE", "T-OBS"),
    ("T-CORE", "T-STIM"),
    ("T-OBS", "T-STIM"),
    ("T-XDL", "T-INTG"),
    ("T-OBS", "T-INTG"),
    ("T-STIM", "T-INTG"),
    ("T-INTG", "T-REVIEW"),
    ("T025", "T026"),
)

BASELINE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

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
    """Return the canonical byte-stable JSON serialization of a register model."""

    return json.dumps(model, indent=2, ensure_ascii=False) + "\n"


def _md_cell(value: str) -> str:
    """Escape a value for a single Markdown table cell."""

    return value.replace("|", "\\|").replace("\n", " ")


def project_markdown(model: dict) -> str:
    """Return the deterministic human-readable projection of a register model."""

    lines: list[str] = []
    lines.append("# X-COM Task Ownership Register")
    lines.append("")
    lines.append("> Deterministic projection of `task-ownership.json` (schema version 1).")
    lines.append("> Do not edit by hand; regenerate from the model and re-run")
    lines.append("> `scripts/validate_xcom_task_ownership.py --check-human`.")
    lines.append("")
    lines.append("## Register identity")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Task | {model['task_id']} |")
    lines.append(f"| Schema version | {model['schema_version']} |")
    lines.append(f"| Baseline revision | `{model['baseline_revision']}` |")
    lines.append(f"| Candidate revision rule | {_md_cell(model['candidate_revision_rule'])} |")
    lines.append(f"| Slices | {len(model['slices'])} |")
    lines.append("")
    lines.append("## Shared path rule")
    lines.append("")
    lines.append(
        "A shared build or specification path is edited by one slice at a time, in the "
        "declared dependency order, under the owning task's exact candidate revision and "
        "retained evidence.  A shared path is never claimed as exclusive, and no exclusive "
        "path is declared shared."
    )
    lines.append("")
    lines.append("## Authorization records")
    lines.append("")
    lines.append(", ".join(f"`{record}`" for record in model["authorization_records"]))
    lines.append("")
    lines.append("## Global prohibitions")
    lines.append("")
    for prohibition in model["global_prohibitions"]:
        lines.append(f"- {prohibition}")
    lines.append("")
    lines.append("## Shared (serialized) paths")
    lines.append("")
    for path in model["shared_paths"]:
        lines.append(f"- `{path}`")
    lines.append("")
    lines.append("## Slices (declared order)")
    for slice_record in model["slices"]:
        lines.append("")
        lines.append(f"### {slice_record['id']} — {slice_record['title']}")
        lines.append("")
        lines.append(f"**Purpose.** {slice_record['purpose']}")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("| --- | --- |")
        owning = ", ".join(slice_record["owning_tasks"]) or "none"
        lines.append(f"| Owning tasks | {owning} |")
        lines.append(f"| Authorized baseline | `{slice_record['authorized_baseline']}` |")
        refs = ", ".join(f"`{ref}`" for ref in slice_record["authorization_refs"])
        lines.append(f"| Authorization refs | {refs} |")
        deps = ", ".join(slice_record["dependencies"]) or "none"
        lines.append(f"| Dependencies | {deps} |")
        lines.append(f"| Acceptance gate | {_md_cell(slice_record['acceptance_gate'])} |")
        lines.append(f"| REF-002 disposition | {slice_record['ref002_disposition']} |")
        lines.append("")
        lines.append("Exclusive paths:")
        lines.append("")
        for path in slice_record["paths_exclusive"]:
            lines.append(f"- `{path}`")
        lines.append("")
        lines.append("Shared paths:")
        lines.append("")
        if slice_record["paths_shared"]:
            for path in slice_record["paths_shared"]:
                lines.append(f"- `{path}`")
        else:
            lines.append("- none")
        lines.append("")
        lines.append("Required evidence:")
        lines.append("")
        for evidence in slice_record["required_evidence"]:
            lines.append(f"- `{evidence}`")
        lines.append("")
        lines.append("Prohibitions:")
        lines.append("")
        for prohibition in slice_record["prohibitions"]:
            lines.append(f"- {prohibition}")
        lines.append("")
        lines.append("Reconciliation:")
        lines.append("")
        for task in slice_record["owning_tasks"]:
            entry = slice_record["reconciliation"][task]
            detail = entry["status"]
            if entry.get("revision"):
                detail += f" (`{entry['revision']}`)"
            if entry.get("reason"):
                detail += f" — {entry['reason']}"
            lines.append(f"- {task}: {detail}")
    lines.append("")
    lines.append("## Task assignment")
    lines.append("")
    lines.append("| Task | Owner |")
    lines.append("| --- | --- |")
    for task in sorted(model["task_assignment"]):
        lines.append(f"| {task} | {model['task_assignment'][task]} |")
    lines.append("")
    lines.append("## Dependency edges")
    lines.append("")
    for edge in model["dependency_edges"]:
        lines.append(f"- {edge[0]} -> {edge[1]}")
    lines.append("")
    return "\n".join(lines)


def _is_sorted_unique_strings(value: object) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) for item in value)
        and value == sorted(set(value))
    )


def _check_schema(model: object, findings: Findings) -> None:
    if not isinstance(model, dict):
        findings.add(EXIT_SCHEMA, "register root is not a JSON object")
        return
    if list(model.keys()) != TOP_FIELDS:
        findings.add(EXIT_SCHEMA, "top-level field set or order differs from the schema")
        return
    if model["schema_version"] != 1:
        findings.add(EXIT_SCHEMA, "schema_version must be 1")
    if model["task_id"] != "T007":
        findings.add(EXIT_SCHEMA, "task_id must be T007")
    if not isinstance(model["baseline_revision"], str) or not BASELINE_SHA_RE.fullmatch(
        model["baseline_revision"]
    ):
        findings.add(EXIT_SCHEMA, "baseline_revision must be a 40-hex lowercase SHA")
    if not isinstance(model["candidate_revision_rule"], str) or not model[
        "candidate_revision_rule"
    ].strip():
        findings.add(EXIT_SCHEMA, "candidate_revision_rule must be a non-empty string")
    for field in ("authorization_records", "global_prohibitions", "shared_paths"):
        if not _is_sorted_unique_strings(model[field]):
            findings.add(EXIT_SCHEMA, f"{field} must be a sorted, duplicate-free string array")
    if not isinstance(model["task_assignment"], dict):
        findings.add(EXIT_SCHEMA, "task_assignment must be an object")
    if not isinstance(model["slices"], list) or not model["slices"]:
        findings.add(EXIT_SCHEMA, "slices must be a non-empty array")
        return
    for index, slice_record in enumerate(model["slices"]):
        if not isinstance(slice_record, dict):
            findings.add(EXIT_SCHEMA, f"slice[{index}] is not an object")
            continue
        if list(slice_record.keys()) != SLICE_FIELDS:
            findings.add(
                EXIT_SCHEMA,
                f"slice[{index}] field set or order differs from the schema",
            )
            continue
        if not isinstance(slice_record["id"], str) or not slice_record["id"]:
            findings.add(EXIT_SCHEMA, f"slice[{index}].id must be a non-empty string")
        if not isinstance(slice_record["title"], str) or not slice_record["title"].strip():
            findings.add(EXIT_SCHEMA, f"slice[{index}].title must be a non-empty string")
        if not isinstance(slice_record["purpose"], str) or not slice_record["purpose"].strip():
            findings.add(EXIT_SCHEMA, f"slice[{index}].purpose must be a non-empty string")
        for array_field in SORTED_SLICE_ARRAYS:
            if not _is_sorted_unique_strings(slice_record[array_field]):
                findings.add(
                    EXIT_SCHEMA,
                    f"slice[{index}].{array_field} must be a sorted, duplicate-free string array",
                )
        if not isinstance(slice_record["acceptance_gate"], str) or not slice_record[
            "acceptance_gate"
        ].strip():
            findings.add(EXIT_SCHEMA, f"slice[{index}].acceptance_gate must be a non-empty string")
        if slice_record["ref002_disposition"] != "unchanged":
            findings.add(EXIT_SCHEMA, f"slice[{index}].ref002_disposition must be unchanged")
        reconciliation = slice_record["reconciliation"]
        if not isinstance(reconciliation, dict):
            findings.add(EXIT_SCHEMA, f"slice[{index}].reconciliation must be an object")
            continue
        for task, entry in reconciliation.items():
            if not isinstance(entry, dict) or list(entry.keys()) != RECON_FIELDS:
                findings.add(
                    EXIT_SCHEMA,
                    f"slice[{index}].reconciliation[{task}] must use fields {RECON_FIELDS}",
                )
    if not isinstance(model["dependency_edges"], list):
        findings.add(EXIT_SCHEMA, "dependency_edges must be an array")
    else:
        for index, edge in enumerate(model["dependency_edges"]):
            if not isinstance(edge, list) or len(edge) != 2 or not all(
                isinstance(item, str) for item in edge
            ):
                findings.add(EXIT_SCHEMA, f"dependency_edges[{index}] must be a string pair")


def _check_slice_set(model: dict, findings: Findings) -> None:
    slices = model.get("slices")
    if not isinstance(slices, list):
        return
    identifiers = [slice_record.get("id") for slice_record in slices if isinstance(slice_record, dict)]
    if identifiers != SLICE_ORDER:
        findings.add(
            EXIT_SLICE_SET,
            "slice id set or declared order differs from "
            f"{SLICE_ORDER}; found {identifiers}",
        )


def _check_assignment(model: dict, findings: Findings) -> None:
    slices = model.get("slices")
    assignment = model.get("task_assignment")
    if not isinstance(slices, list) or not isinstance(assignment, dict):
        return
    if sorted(assignment.keys()) != sorted(TASK_IDS):
        findings.add(
            EXIT_ASSIGNMENT,
            "task_assignment must cover T007-T041 exactly once",
        )
    elif assignment[PRODUCING_TASK] != PRODUCING_OWNER:
        findings.add(
            EXIT_ASSIGNMENT,
            f"{PRODUCING_TASK} must be owned by the producing-task token {PRODUCING_OWNER}",
        )
    else:
        for task, owner in assignment.items():
            if task == PRODUCING_TASK:
                continue
            if owner not in SLICE_ORDER:
                findings.add(EXIT_ASSIGNMENT, f"task {task} has unknown owner {owner}")
    owner_count: dict[str, int] = {}
    for slice_record in slices:
        if not isinstance(slice_record, dict):
            continue
        for task in slice_record.get("owning_tasks", []):
            owner_count[task] = owner_count.get(task, 0) + 1
    for task, count in sorted(owner_count.items()):
        if count > 1:
            findings.add(EXIT_ASSIGNMENT, f"task {task} is owned by {count} slices")
    for slice_record in slices:
        if not isinstance(slice_record, dict):
            continue
        slice_id = slice_record.get("id")
        expected = sorted(
            task for task, owner in assignment.items() if owner == slice_id
        )
        if sorted(slice_record.get("owning_tasks", [])) != expected:
            findings.add(
                EXIT_ASSIGNMENT,
                f"slice {slice_id} owning_tasks disagree with task_assignment",
            )


def _check_binding(model: dict, findings: Findings) -> None:
    baseline = model.get("baseline_revision")
    if model.get("authorization_records") != sorted(AUTH_RECORDS):
        findings.add(
            EXIT_BINDING,
            "authorization_records must equal the closed accepted set ACC001-ACC015 and ADR-0018..0020",
        )
    slices = model.get("slices")
    if not isinstance(slices, list):
        return
    for slice_record in slices:
        if not isinstance(slice_record, dict):
            continue
        slice_id = slice_record.get("id")
        authorized = slice_record.get("authorized_baseline")
        if not isinstance(authorized, str) or not BASELINE_SHA_RE.fullmatch(authorized):
            findings.add(
                EXIT_BINDING,
                f"slice {slice_id} authorized_baseline is not a 40-hex lowercase SHA",
            )
        elif authorized != baseline:
            findings.add(
                EXIT_BINDING,
                f"slice {slice_id} authorized_baseline differs from the register baseline",
            )
        refs = slice_record.get("authorization_refs")
        if not isinstance(refs, list) or not refs:
            findings.add(EXIT_BINDING, f"slice {slice_id} has no authorization reference")
            continue
        unknown = sorted(set(refs) - set(AUTH_RECORDS))
        if unknown:
            findings.add(
                EXIT_BINDING,
                f"slice {slice_id} cites unknown authorization references {unknown}",
            )


def _patterns_overlap(left: str, right: str) -> bool:
    """Return True when two exclusive patterns can claim the same path entry.

    A trailing ``/`` marks a directory prefix.  Patterns overlap when they are
    equal, when the shorter pattern is a directory prefix of the longer one, or
    when the longer pattern continues from the shorter one at a ``/`` boundary.
    """

    if left == right:
        return True
    shorter, longer = sorted((left, right), key=len)
    if not longer.startswith(shorter):
        return False
    return shorter.endswith("/") or longer[len(shorter)] == "/"


def _check_paths(model: dict, findings: Findings) -> None:
    shared = model.get("shared_paths")
    slices = model.get("slices")
    if not isinstance(shared, list) or not isinstance(slices, list):
        return
    for required in SHARED_PATH_REQUIRED_SUBSTRINGS:
        if not any(required in path for path in shared):
            findings.add(
                EXIT_PATHS,
                f"shared_paths does not name the required build/specification path {required}",
            )
    exclusive_entries: list[tuple[str, str]] = []
    for slice_record in slices:
        if not isinstance(slice_record, dict):
            continue
        slice_id = slice_record.get("id")
        paths = slice_record.get("paths_exclusive")
        if not isinstance(paths, list):
            continue
        if slice_id in SLICE_ORDER and not paths:
            findings.add(
                EXIT_PATHS,
                f"slice {slice_id} declares no exclusive path",
            )
        for path in paths:
            exclusive_entries.append((path, slice_id))
    for index, (left, left_slice) in enumerate(exclusive_entries):
        for right, right_slice in exclusive_entries[index + 1:]:
            if left_slice != right_slice and _patterns_overlap(left, right):
                findings.add(
                    EXIT_PATHS,
                    f"exclusive path patterns {left} ({left_slice}) and {right} "
                    f"({right_slice}) overlap",
                )
    exclusive_owner: dict[str, str] = {}
    for path, slice_id in exclusive_entries:
        exclusive_owner.setdefault(path, slice_id)
    for path, slice_id in sorted(exclusive_owner.items()):
        if path in shared:
            findings.add(
                EXIT_PATHS,
                f"slice {slice_id} claims shared path {path} as exclusive",
            )
    for slice_record in slices:
        if not isinstance(slice_record, dict):
            continue
        for path in slice_record.get("paths_shared", []):
            if path not in shared:
                findings.add(
                    EXIT_PATHS,
                    f"slice {slice_record.get('id')} declares undeclared shared path {path}",
                )
    _check_per_task_ownership(model, findings)


def _check_per_task_ownership(model: dict, findings: Findings) -> None:
    """Every task's per-task artifacts must be reserved to exactly one slice.

    The per-task work-product directory ``docs/engineering/xcom/<task>/`` (which
    contains the task's ``internal-review.json`` and ``acceptance-decision.md``)
    and its queue package ``reports/xcom-queue/<task>-package.json`` are produced
    during that task's own run, so they belong to the slice that owns the task.
    The producing task's directory belongs to the enabler group that consumes it.
    """

    assignment = model.get("task_assignment")
    slices = model.get("slices")
    if not isinstance(assignment, dict) or not isinstance(slices, list):
        return
    exclusive_by_slice: dict[str, set[str]] = {}
    for slice_record in slices:
        if isinstance(slice_record, dict):
            exclusive_by_slice[slice_record.get("id")] = set(
                slice_record.get("paths_exclusive", [])
            )
    for task in TASK_IDS:
        owner = PRODUCING_TASK_DIR_OWNER if task == PRODUCING_TASK else assignment.get(task)
        if owner not in exclusive_by_slice:
            findings.add(
                EXIT_PATHS,
                f"task {task} has no resolvable slice owner for its per-task artifacts",
            )
            continue
        for pattern in (
            PER_TASK_DOC_DIR.format(task=task.lower()),
            QUEUE_PACKAGE_FILE.format(task=task.lower()),
        ):
            if pattern not in exclusive_by_slice[owner]:
                findings.add(
                    EXIT_PATHS,
                    f"per-task artifact {pattern} is not reserved exclusively to {owner}",
                )


def _graph(model: dict) -> dict[str, list[str]]:
    node_ids = set(SLICE_ORDER) | set(TASK_IDS)
    adjacency: dict[str, list[str]] = {node: [] for node in node_ids}
    edges = model.get("dependency_edges", [])
    if not isinstance(edges, list):
        return adjacency
    for edge in edges:
        if isinstance(edge, list) and len(edge) == 2:
            source, target = edge
            if source in adjacency and target in adjacency:
                adjacency[source].append(target)
    for node in adjacency:
        adjacency[node].sort()
    return adjacency


def _reachable(adjacency: dict[str, list[str]], source: str, target: str) -> bool:
    seen = {source}
    stack = [source]
    while stack:
        node = stack.pop()
        if node == target:
            return True
        for neighbour in adjacency.get(node, []):
            if neighbour not in seen:
                seen.add(neighbour)
                stack.append(neighbour)
    return False


def _check_dependencies(model: dict, findings: Findings) -> None:
    slices = model.get("slices")
    edges = model.get("dependency_edges")
    if not isinstance(slices, list) or not isinstance(edges, list):
        return
    node_ids = set(SLICE_ORDER) | set(TASK_IDS)
    for edge in edges:
        if not (isinstance(edge, list) and len(edge) == 2):
            continue
        for node in edge:
            if node not in node_ids:
                findings.add(EXIT_DEPENDENCY, f"dependency edge references unknown node {node}")
    adjacency = _graph(model)
    # Kahn's algorithm detects a cycle without depending on traversal order.
    indegree = {node: 0 for node in adjacency}
    for targets in adjacency.values():
        for target in targets:
            indegree[target] += 1
    ready = sorted(node for node, degree in indegree.items() if degree == 0)
    visited = 0
    while ready:
        node = ready.pop(0)
        visited += 1
        for target in adjacency[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
                ready.sort()
    if visited != len(adjacency):
        findings.add(EXIT_DEPENDENCY, "dependency graph contains a cycle")
    for source, target in REQUIRED_ORDER_PAIRS:
        if source not in adjacency or target not in adjacency:
            findings.add(
                EXIT_DEPENDENCY,
                f"required ordering nodes {source} -> {target} are absent from the graph",
            )
            continue
        if not _reachable(adjacency, source, target):
            findings.add(
                EXIT_DEPENDENCY,
                f"{source} does not precede {target} in the dependency graph",
            )
    declared = {
        slice_record.get("id"): sorted(slice_record.get("dependencies", []))
        for slice_record in slices if isinstance(slice_record, dict)
    }
    direct: dict[str, list[str]] = {slice_id: [] for slice_id in SLICE_ORDER}
    for edge in edges:
        if isinstance(edge, list) and len(edge) == 2 and edge[1] in direct:
            direct[edge[1]].append(edge[0])
    for slice_id in SLICE_ORDER:
        expected = sorted(direct[slice_id])
        if declared.get(slice_id) != expected:
            findings.add(
                EXIT_DEPENDENCY,
                f"slice {slice_id} dependencies {declared.get(slice_id)} disagree with direct "
                f"dependency edges {expected}",
            )


def _check_gates(model: dict, findings: Findings) -> None:
    global_prohibitions = set(model.get("global_prohibitions", []))
    for minimum in MINIMUM_PROHIBITIONS:
        if minimum not in global_prohibitions:
            findings.add(
                EXIT_GATE,
                f"global_prohibitions omits the minimum prohibition: {minimum}",
            )
    slices = model.get("slices")
    if not isinstance(slices, list):
        return
    for slice_record in slices:
        if not isinstance(slice_record, dict):
            continue
        slice_id = slice_record.get("id")
        evidence = slice_record.get("required_evidence")
        if not isinstance(evidence, list) or not evidence:
            findings.add(EXIT_GATE, f"slice {slice_id} has no required evidence")
        gate = slice_record.get("acceptance_gate")
        if not isinstance(gate, str) or not gate.strip():
            findings.add(EXIT_GATE, f"slice {slice_id} has no acceptance gate")
        prohibitions = set(slice_record.get("prohibitions", []))
        for minimum in GLOBAL_PROHIBITIONS:
            if minimum not in prohibitions:
                findings.add(
                    EXIT_GATE,
                    f"slice {slice_id} omits the global prohibition: {minimum}",
                )
        if slice_id == "T-REVIEW":
            lowered = gate.lower() if isinstance(gate, str) else ""
            if "review" not in lowered or "user acceptance" not in lowered:
                findings.add(
                    EXIT_GATE,
                    "T-REVIEW acceptance gate must name the read-only review and user acceptance",
                )
        reconciliation = slice_record.get("reconciliation")
        if not isinstance(reconciliation, dict):
            continue
        owning = sorted(slice_record.get("owning_tasks", []))
        if sorted(reconciliation.keys()) != owning:
            findings.add(
                EXIT_GATE,
                f"slice {slice_id} reconciliation does not cover its owning tasks exactly",
            )
        for task, entry in sorted(reconciliation.items()):
            if not isinstance(entry, dict):
                continue
            status = entry.get("status")
            if status not in RECON_STATUSES:
                findings.add(EXIT_GATE, f"{task} has unknown reconciliation status {status}")
                continue
            if status == "accepted":
                revision = entry.get("revision")
                if not isinstance(revision, str) or not BASELINE_SHA_RE.fullmatch(revision):
                    findings.add(
                        EXIT_GATE,
                        f"{task} is labelled accepted without a recorded 40-hex revision",
                    )
                if not str(entry.get("reason", "")).strip():
                    findings.add(EXIT_GATE, f"{task} is accepted without a decision reason")
            if status == "delivered":
                revision = entry.get("revision")
                if not isinstance(revision, str) or not BASELINE_SHA_RE.fullmatch(revision):
                    findings.add(
                        EXIT_GATE,
                        f"{task} is labelled delivered without a recorded 40-hex revision",
                    )
                if not str(entry.get("reason", "")).strip():
                    findings.add(EXIT_GATE, f"{task} is delivered without a recorded reason")
                pinned = DELIVERED_TASKS.get(task)
                if pinned is None:
                    findings.add(
                        EXIT_GATE,
                        f"{task} is labelled delivered but is not a pinned delivered task",
                    )
                elif revision != pinned:
                    findings.add(
                        EXIT_GATE,
                        f"{task} delivered revision differs from the pinned candidate revision",
                    )
            if status == "unreconciled" and not str(entry.get("reason", "")).strip():
                findings.add(EXIT_GATE, f"{task} is unreconciled without a recorded reason")
    _check_required_reconciliation(model, findings)


def _check_required_reconciliation(model: dict, findings: Findings) -> None:
    status_of: dict[str, str] = {}
    revision_of: dict[str, object] = {}
    for slice_record in model.get("slices", []):
        if not isinstance(slice_record, dict):
            continue
        for task, entry in slice_record.get("reconciliation", {}).items():
            if isinstance(entry, dict):
                status_of[task] = entry.get("status")
                revision_of[task] = entry.get("revision")
    for task, revision in DELIVERED_TASKS.items():
        if status_of.get(task) != "delivered":
            findings.add(EXIT_GATE, f"{task} must be recorded delivered")
        elif revision_of.get(task) != revision:
            findings.add(EXIT_GATE, f"{task} delivered revision differs from the record")
    for task in ALLOCATED_TASKS:
        if status_of.get(task) != "allocated":
            findings.add(EXIT_GATE, f"{task} must be recorded allocated")
    for task, revision in ACCEPTED_TASKS.items():
        if status_of.get(task) != "accepted":
            findings.add(EXIT_GATE, f"{task} must be recorded accepted")
        elif revision_of.get(task) != revision:
            findings.add(EXIT_GATE, f"{task} accepted revision differs from the record")
    for task, status in sorted(status_of.items()):
        if status == "accepted" and task not in ACCEPTED_TASKS:
            findings.add(EXIT_GATE, f"{task} is labelled accepted without an accepted record")
        if status == "delivered" and task not in DELIVERED_TASKS:
            findings.add(EXIT_GATE, f"{task} is labelled delivered without a delivered record")


def _check_determinism(model: dict, raw_text: str | None, findings: Findings) -> None:
    if raw_text is not None and serialize(model) != raw_text:
        findings.add(
            EXIT_DETERMINISM,
            "register serialization is not byte-stable canonical JSON",
        )


def _scan_public_safety(text: str, source: str, findings: Findings) -> None:
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
    raw_text: str | None = None,
    markdown_text: str | None = None,
    markdown_source: str = "task-ownership.md",
) -> Findings:
    """Run every deterministic check and return the classified findings."""

    findings = Findings()
    _check_schema(model, findings)
    if isinstance(model, dict) and list(model.keys()) == TOP_FIELDS:
        _check_slice_set(model, findings)
        _check_assignment(model, findings)
        _check_binding(model, findings)
        _check_paths(model, findings)
        _check_dependencies(model, findings)
        _check_gates(model, findings)
        _check_determinism(model, raw_text, findings)
        if markdown_text is not None:
            if project_markdown(model) != markdown_text:
                findings.add(
                    EXIT_DETERMINISM,
                    f"{markdown_source} is not the deterministic projection of the register",
                )
        if raw_text is not None:
            _scan_public_safety(raw_text, "task-ownership.json", findings)
        if markdown_text is not None:
            _scan_public_safety(markdown_text, markdown_source, findings)
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


def _load_register(findings: Findings) -> tuple[object, str | None]:
    raw_text = _read_bounded(REGISTER_JSON, findings)
    if raw_text is None:
        return None, None
    try:
        return json.loads(raw_text), raw_text
    except json.JSONDecodeError as error:
        findings.add(EXIT_SCHEMA, f"register is not valid JSON: {error.msg}")
        return None, raw_text


def _emit(findings: Findings) -> int:
    exit_code = findings.exit_code()
    if exit_code == EXIT_OK:
        print("X-COM task-ownership validation passed")
        return EXIT_OK
    print(
        f"X-COM task-ownership validation FAILED: {CLASS_NAMES[exit_code]} "
        f"(exit {exit_code})",
        file=sys.stderr,
    )
    for line in findings.diagnostics():
        print(f"- {line}", file=sys.stderr)
    return exit_code


def _verify() -> int:
    findings = Findings()
    model, raw_text = _load_register(findings)
    if model is None:
        return _emit(findings)
    result = run_checks(model, raw_text=raw_text)
    for exit_class, messages in result.by_class.items():
        for message in messages:
            findings.add(exit_class, message)
    return _emit(findings)


def _check_human() -> int:
    findings = Findings()
    model, raw_text = _load_register(findings)
    if model is None:
        return _emit(findings)
    markdown_text = _read_bounded(REGISTER_MD, findings)
    result = run_checks(
        model,
        raw_text=raw_text,
        markdown_text=markdown_text,
        markdown_source=REGISTER_MD.name,
    )
    for exit_class, messages in result.by_class.items():
        for message in messages:
            findings.add(exit_class, message)
    return _emit(findings)


def _copy(model: dict) -> dict:
    return json.loads(json.dumps(model))


def _normalise_arrays(model: dict) -> None:
    model["authorization_records"] = sorted(model["authorization_records"])
    model["global_prohibitions"] = sorted(model["global_prohibitions"])
    model["shared_paths"] = sorted(model["shared_paths"])
    model["task_assignment"] = dict(sorted(model["task_assignment"].items()))
    for slice_record in model["slices"]:
        for field in SORTED_SLICE_ARRAYS:
            if field in slice_record:
                slice_record[field] = sorted(slice_record[field])


def _slice(model: dict, slice_id: str) -> dict:
    for slice_record in model["slices"]:
        if slice_record["id"] == slice_id:
            return slice_record
    raise KeyError(slice_id)


def _extra_slice() -> dict:
    template = {
        "id": "T-EXTRA",
        "title": "Unnamed extra slice fixture",
        "owning_tasks": [],
        "purpose": "Controlled negative fixture that must be rejected.",
        "authorized_baseline": "923a6db65aafbcdbf33a1461e93622777e902deb",
        "authorization_refs": ["ADR-0020"],
        "paths_exclusive": [],
        "paths_shared": [],
        "dependencies": [],
        "required_evidence": ["none"],
        "acceptance_gate": "rejected fixture",
        "prohibitions": list(GLOBAL_PROHIBITIONS),
        "reconciliation": {},
        "ref002_disposition": "unchanged",
    }
    return template


def _sync_declared_dependencies(model: dict) -> None:
    """Recompute every slice's declared dependencies from the edge list."""

    for slice_record in model["slices"]:
        slice_id = slice_record["id"]
        slice_record["dependencies"] = sorted(
            edge[0]
            for edge in model["dependency_edges"]
            if isinstance(edge, list) and len(edge) == 2 and edge[1] == slice_id
        )


def _reshape_dependencies(model: dict, slice_id: str, sources: list[str]) -> None:
    """Replace the direct dependencies of one slice, keeping the model consistent."""

    model["dependency_edges"] = [
        edge
        for edge in model["dependency_edges"]
        if not (isinstance(edge, list) and len(edge) == 2 and edge[1] == slice_id)
    ]
    model["dependency_edges"].extend([source, slice_id] for source in sources)
    _sync_declared_dependencies(model)


def _negative_fixtures(base: dict) -> list[tuple[str, int, dict]]:
    fixtures: list[tuple[str, int, dict]] = []

    model = _copy(base)
    model["slices"] = [s for s in model["slices"] if s["id"] != "T-OBS"]
    _normalise_arrays(model)
    fixtures.append(("NEG-01", EXIT_SLICE_SET, model))

    model = _copy(base)
    model["slices"].append(_extra_slice())
    _normalise_arrays(model)
    fixtures.append(("NEG-02", EXIT_SLICE_SET, model))

    model = _copy(base)
    del model["task_assignment"]["T013"]
    core = _slice(model, "T-CORE")
    core["owning_tasks"] = [task for task in core["owning_tasks"] if task != "T013"]
    del core["reconciliation"]["T013"]
    _normalise_arrays(model)
    fixtures.append(("NEG-03", EXIT_ASSIGNMENT, model))

    model = _copy(base)
    model["task_assignment"]["T013"] = "T-OBS"
    _slice(model, "T-OBS")["owning_tasks"].append("T013")
    _normalise_arrays(model)
    fixtures.append(("NEG-04", EXIT_ASSIGNMENT, model))

    model = _copy(base)
    _slice(model, "T-CORE")["authorized_baseline"] = "ABC"
    _normalise_arrays(model)
    fixtures.append(("NEG-05", EXIT_BINDING, model))

    model = _copy(base)
    _slice(model, "T-CORE")["authorization_refs"].append("ADR-9999")
    _normalise_arrays(model)
    fixtures.append(("NEG-06", EXIT_BINDING, model))

    model = _copy(base)
    _slice(model, "T-OBS")["paths_exclusive"].append("tests/xcom/core_types/")
    _normalise_arrays(model)
    fixtures.append(("NEG-07", EXIT_PATHS, model))

    model = _copy(base)
    _slice(model, "T-CORE")["paths_exclusive"].append("CMakeLists.txt")
    _normalise_arrays(model)
    fixtures.append(("NEG-08", EXIT_PATHS, model))

    model = _copy(base)
    model["dependency_edges"].append(["T-REVIEW", "T-ENABLER"])
    _sync_declared_dependencies(model)
    _normalise_arrays(model)
    fixtures.append(("NEG-09", EXIT_DEPENDENCY, model))

    # NEG-10 reverses enabler -> core while keeping every declared dependency
    # consistent with the edge list, so only the ordering constraint can reject it.
    model = _copy(base)
    model["dependency_edges"] = [
        ["T-CORE", "T-ENABLER"] if edge == ["T-ENABLER", "T-CORE"] else edge
        for edge in model["dependency_edges"]
    ]
    _sync_declared_dependencies(model)
    _normalise_arrays(model)
    fixtures.append(("NEG-10", EXIT_DEPENDENCY, model))

    model = _copy(base)
    _slice(model, "T-CORE")["required_evidence"] = []
    _normalise_arrays(model)
    fixtures.append(("NEG-11", EXIT_GATE, model))

    model = _copy(base)
    core = _slice(model, "T-CORE")
    core["prohibitions"] = [
        item for item in core["prohibitions"] if item != MINIMUM_PROHIBITIONS[0]
    ]
    _normalise_arrays(model)
    fixtures.append(("NEG-12", EXIT_GATE, model))

    model = _copy(base)
    _slice(model, "T-STIM")["reconciliation"]["T026"] = {
        "status": "accepted",
        "revision": None,
        "reason": "",
    }
    _normalise_arrays(model)
    fixtures.append(("NEG-13", EXIT_GATE, model))

    # NEG-14..NEG-16 each break one required ordering constraint while leaving
    # every declared dependency consistent with the edge list.
    model = _copy(base)
    _reshape_dependencies(model, "T-XDL", ["T-ENABLER"])
    _normalise_arrays(model)
    fixtures.append(("NEG-14", EXIT_DEPENDENCY, model))

    model = _copy(base)
    _reshape_dependencies(model, "T-INTG", ["T-ENABLER"])
    _normalise_arrays(model)
    fixtures.append(("NEG-15", EXIT_DEPENDENCY, model))

    model = _copy(base)
    _reshape_dependencies(model, "T-REVIEW", ["T-ENABLER"])
    _normalise_arrays(model)
    fixtures.append(("NEG-16", EXIT_DEPENDENCY, model))

    model = _copy(base)
    model["global_prohibitions"] = [
        item
        for item in model["global_prohibitions"]
        if item != MINIMUM_PROHIBITIONS[0]
    ]
    _normalise_arrays(model)
    fixtures.append(("NEG-17", EXIT_GATE, model))

    model = _copy(base)
    _slice(model, "T-OBS")["paths_exclusive"].append("tests/xcom/")
    _normalise_arrays(model)
    fixtures.append(("NEG-18", EXIT_PATHS, model))

    model = _copy(base)
    _slice(model, "T-OBS")["paths_exclusive"] = []
    _normalise_arrays(model)
    fixtures.append(("NEG-19", EXIT_PATHS, model))

    model = _copy(base)
    owner = _slice(model, "T-ENABLER")
    owner["paths_exclusive"] = [
        path
        for path in owner["paths_exclusive"]
        if path != QUEUE_PACKAGE_FILE.format(task=PRODUCING_TASK.lower())
    ]
    _normalise_arrays(model)
    fixtures.append(("NEG-20", EXIT_PATHS, model))

    # NEG-21..NEG-25 exercise the accepted successor state. Each fails closed.
    model = _copy(base)
    _slice(model, "T-CORE")["reconciliation"]["T012"]["revision"] = None
    _normalise_arrays(model)
    fixtures.append(("NEG-21", EXIT_GATE, model))

    model = _copy(base)
    _slice(model, "T-CORE")["reconciliation"]["T012"]["revision"] = "0" * 40
    _normalise_arrays(model)
    fixtures.append(("NEG-22", EXIT_GATE, model))

    model = _copy(base)
    _slice(model, "T-CORE")["reconciliation"]["T012"]["reason"] = ""
    _normalise_arrays(model)
    fixtures.append(("NEG-23", EXIT_GATE, model))

    model = _copy(base)
    reverted = _slice(model, "T-CORE")["reconciliation"]["T012"]
    reverted["status"] = "unreconciled"
    reverted["revision"] = None
    _normalise_arrays(model)
    fixtures.append(("NEG-24", EXIT_GATE, model))

    model = _copy(base)
    _slice(model, "T-CORE")["reconciliation"]["T012"]["status"] = "delivered"
    _normalise_arrays(model)
    fixtures.append(("NEG-25", EXIT_GATE, model))

    return fixtures


def _self_test() -> int:
    findings = Findings()
    model, raw_text = _load_register(findings)
    if model is None or raw_text is None:
        for exit_class, messages in findings.by_class.items():
            for message in messages:
                print(f"- [{CLASS_NAMES[exit_class]}] {message}", file=sys.stderr)
        print("X-COM task-ownership self-test FAILED: positive fixture is unavailable", file=sys.stderr)
        return EXIT_IO

    positive = run_checks(model, raw_text=raw_text)
    if positive.exit_code() != EXIT_OK:
        for line in positive.diagnostics():
            print(f"- {line}", file=sys.stderr)
        print(
            "X-COM task-ownership self-test FAILED: positive fixture did not pass",
            file=sys.stderr,
        )
        return EXIT_DETERMINISM

    failures = 0
    print("positive fixture: passed")
    for name, expected, mutated in _negative_fixtures(model):
        raw = serialize(mutated)
        result = run_checks(mutated, raw_text=raw)
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

    # DET-02: a mutated human projection must be detected as a determinism defect.
    md_model, md_raw = _load_register(Findings())
    if md_model is not None and md_raw is not None:
        tampered = project_markdown(md_model) + "tampered\n"
        result = run_checks(md_model, raw_text=md_raw, markdown_text=tampered)
        if result.exit_code() == EXIT_DETERMINISM:
            print("DET-02: tampered projection rejected with DETERMINISM_INVALID (exit 9)")
        else:
            failures += 1
            print(
                f"DET-02: expected DETERMINISM_INVALID (exit 9) but got exit "
                f"{result.exit_code()}",
                file=sys.stderr,
            )

    if failures:
        print(
            f"X-COM task-ownership self-test FAILED: {failures} fixture(s) did not behave as declared",
            file=sys.stderr,
        )
        return EXIT_GATE
    print("X-COM task-ownership self-test passed")
    return EXIT_OK


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--self-test", action="store_true", help="run controlled positive/negative fixtures")
    group.add_argument("--verify", action="store_true", help="validate the register JSON (default)")
    group.add_argument("--check-human", action="store_true", help="validate the register and its Markdown projection")
    args = parser.parse_args()
    findings = Findings()
    total = 0
    for path in (REGISTER_JSON, REGISTER_MD):
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
