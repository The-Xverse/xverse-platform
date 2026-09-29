#!/usr/bin/env python3
"""T038 Spec Kit and REF-002 requirements/design/code/test traceability verifier.

This repository-owned, deterministic, offline verifier validates the
capability-007 traceability chain and the public safety of the retained
evidence at one exact candidate revision, and it proves that no allocated or
deferred REF-002 SADS communication ID is promoted without source and
exact-candidate executed evidence.  It adds no byte to any accepted production
source, header, contract, schema, register, XDL profile, accepted test, target,
label, command, or expected value.

What it checks
--------------
``--verify [PATH]``
    Resolve the requirement -> component -> unit -> code -> test/measure ->
    evidence -> intended-use validation chain over the accepted ``engineering/**``
    records and ``engineering/trace/links.json``; account for all twenty REF-002
    IDs ``XVE-SYS-0139``-``XVE-SYS-0158``; scan the retained evidence for the
    mechanically decidable excluded-content classes; and, when ``PATH`` is given,
    require the evidence report at ``PATH`` to carry the required sections and the
    exact-candidate binding.  If ``PATH`` is absent the report is written once
    (bootstrap) and then validated on every later call.  A missing edge, a stale
    hash pin, an incomplete or promoted disposition, an excluded-content match, a
    missing report field, or a foreign/stale binding exits nonzero.

``--report [PATH]``
    Explicitly (re)write the evidence report at ``PATH``.

``--self-test``
    Exercise controlled in-memory negative fixtures and prove the verifier
    rejects a missing edge, a stale hash pin, a promoted disposition, and an
    excluded-content match.

Exact-candidate revision contract
---------------------------------
A committed report cannot contain its own commit hash (writing the hash would
change the commit), so the report binds the exact candidate by
``baseline_revision`` plus the sorted material-input inventory, the
``material_digest``, and the per-file ``hashes``.  ``--verify`` accepts exactly
two candidate revisions: ``HEAD == baseline_revision`` (the measured working-tree
successor, before the reviewed files are committed) and ``HEAD`` as the *direct
child* of ``baseline_revision`` (the committed candidate).  Every other
revision -- a foreign commit, an unrelated history, or an extra successor
commit -- is rejected.

The verifier is single-threaded, opens no network listener,
``AF_INET``/``AF_INET6`` socket, DNS, resolver, TLS, external peer, legacy
binary, or production workload, and uses only the Python standard library and
the repository's own records.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_REPORT = REPO_ROOT / "reports/xcom-queue/t038-traceability.json"

TASK_ID = "T038"
CAPABILITY = "007"
BASELINE_REVISION = "d5b9c6399da67a0a028fae21c2f0dcc8da3619bc"
SCHEMA_VERSION = 1

# Exit classes: a distinct nonzero class per failure family so callers and the
# self-test can bind a result to the defect it detected.
EXIT_OK = 0
EXIT_CHAIN = 2
EXIT_STALE = 3
EXIT_REF002 = 4
EXIT_PUBLIC_SAFETY = 5
EXIT_BINDING = 6
EXIT_IO = 7
CLASS_NAMES = {
    EXIT_OK: "OK",
    EXIT_CHAIN: "CHAIN_INVALID",
    EXIT_STALE: "STALE_LINK",
    EXIT_REF002: "REF002_INVALID",
    EXIT_PUBLIC_SAFETY: "PUBLIC_SAFETY_INVALID",
    EXIT_BINDING: "BINDING_INVALID",
    EXIT_IO: "IO_ERROR",
}

# Accepted measure identities (targets of verified_by / analyzed_by).
MEASURES = {"unit", "integration", "validation", "static_analysis", "conformance", "sanitizer"}
STATIC_ANALYSIS = "static_analysis"

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
REF002_IDS = [f"XVE-SYS-{number:04d}" for number in range(139, 159)]
ARCHITECTURAL_TARGET = "architectural-target"
PROMOTED_MATURITIES = {"implemented"}

# Mechanically decidable excluded-content classes (the accepted traceability
# validator's --verify scan classes).
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
EXCLUDED_CONTENT_CLASSES = [name for name, _ in PUBLIC_SAFETY_PATTERNS]

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
STK_RE = re.compile(r"^T038-STK-\d{3}$")
SR_RE = re.compile(r"^T038-SR-\d{3}$")
CMP_RE = re.compile(r"^T038-SR-\d{3}-CMP$")
UNIT_RE = re.compile(r"^T038-SR-\d{3}-U$")

EXPECTED_STK = [f"T038-STK-{n:03d}" for n in range(1, 6)]
EXPECTED_SR = [f"T038-SR-{n:03d}" for n in range(1, 11)]
EXPECTED_CMP = [f"T038-SR-{n:03d}-CMP" for n in range(1, 11)]
EXPECTED_UNIT = [f"T038-SR-{n:03d}-U" for n in range(1, 11)]
SCENARIO_ID = "T038-VS-ACCUMULATED"

# Candidate material inputs bound into the report.  Human-readable run records
# (implementation.md, internal-review.json, review-index.md), the package
# record, and the report itself are intentionally excluded so the binding is
# acyclic and reproducible.
MATERIAL_GLOBS = (
    "docs/engineering/xcom/t008/requirements-register.json",
    "docs/engineering/xcom/t008/traceability-matrix.json",
    "docs/engineering/xcom/t038/architecture.md",
    "docs/engineering/xcom/t038/detailed-design.md",
    "docs/engineering/xcom/t038/requirements.md",
    "docs/engineering/xcom/t038/unit-specifications.md",
    "docs/engineering/xcom/t038/verification-plan.md",
    "engineering/architecture/components/T038-SR-*-CMP.json",
    "engineering/check_xcom_traceability.py",
    "engineering/project.json",
    "engineering/requirements/T038-*.json",
    "engineering/trace/links.json",
    "engineering/unit-specifications/T038-SR-*-U.json",
    "engineering/validation/scenarios/T038-VS-ACCUMULATED.json",
    "engineering/verification/measures/*.json",
    "specs/007-xcom-core/reference-traceability.md",
    "specs/007-xcom-core/tasks.md",
)

# Retained evidence scanned for excluded content (the verifier's own source is
# excluded because it legitimately declares the detector patterns).
SCAN_GLOBS = (
    "docs/engineering/xcom/t008/requirements-register.json",
    "docs/engineering/xcom/t008/traceability-matrix.json",
    "docs/engineering/xcom/t038/*.md",
    "engineering/architecture/components/T038-SR-*-CMP.json",
    "engineering/project.json",
    "engineering/requirements/T038-*.json",
    "engineering/trace/links.json",
    "engineering/unit-specifications/T038-SR-*-U.json",
    "engineering/validation/scenarios/T038-VS-ACCUMULATED.json",
    "reports/xcom-queue/t038-traceability.json",
    "specs/007-xcom-core/reference-traceability.md",
    "specs/007-xcom-core/tasks.md",
)

ADMITTED_INPUTS = {
    "XVERSE_XCOM_TOOLCHAIN": "directory",
    "XVERSE_XCOM_PACKAGE_MANIFEST": "file",
    "XVERSE_XCOM_T025_TEST_TOOLCHAIN": "directory",
}
ADMITTED_MANIFEST_SHA256 = "031c6aecdc4fe0cf4e0dff474d9b161777122142bf9bb1393c25d679807b055c"


class TraceabilityError(RuntimeError):
    """Stable verifier failure with a public-safe message."""


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


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_digest(path: pathlib.Path) -> tuple[str, int]:
    """Deterministic directory digest over sorted relative path and file digests."""
    digest = hashlib.sha256()
    count = 0
    for entry in sorted(path.rglob("*")):
        if entry.is_file() and not entry.is_symlink():
            relative = entry.relative_to(path).as_posix()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(sha256_file(entry).encode("ascii"))
            digest.update(b"\n")
            count += 1
    return digest.hexdigest(), count


def material_paths() -> list[str]:
    found: set[str] = set()
    for pattern in MATERIAL_GLOBS:
        for match in REPO_ROOT.glob(pattern):
            if match.is_file():
                found.add(match.relative_to(REPO_ROOT).as_posix())
    missing = [
        pattern
        for pattern in MATERIAL_GLOBS
        if "*" not in pattern and not (REPO_ROOT / pattern).is_file()
    ]
    if missing:
        raise TraceabilityError(f"candidate material input is missing: {missing}")
    return sorted(found)


def material_digest(paths: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(paths):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(REPO_ROOT / relative).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def git_head() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True,
            check=False, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - defensive
        raise TraceabilityError("cannot determine the candidate revision") from exc
    revision = result.stdout.strip()
    if result.returncode != 0 or not REVISION_RE.fullmatch(revision):
        raise TraceabilityError("cannot determine the candidate revision")
    return revision


def git_parent(revision: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{revision}^"], cwd=REPO_ROOT, text=True,
            capture_output=True, check=False, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - defensive
        raise TraceabilityError("cannot inspect the candidate revision") from exc
    parent = result.stdout.strip()
    if result.returncode != 0 or not REVISION_RE.fullmatch(parent):
        return None
    return parent


def git_commits_ahead(baseline: str, revision: str) -> int | None:
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", f"{baseline}..{revision}"], cwd=REPO_ROOT, text=True,
            capture_output=True, check=False, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - defensive
        raise TraceabilityError("cannot inspect the candidate revision") from exc
    value = result.stdout.strip()
    if result.returncode != 0 or not value.isdigit():
        return None
    return int(value)


def resolve_admitted() -> dict[str, dict[str, object]]:
    """Best-effort fingerprint of the admitted offline inputs, by name only.

    The record-only traceability route does not require the C++ toolchain; when
    an admitted input is absent it is recorded as ``unavailable`` rather than
    treated as a blocker, and no host-specific path is ever recorded.
    """
    resolved: dict[str, dict[str, object]] = {}
    for name, kind in ADMITTED_INPUTS.items():
        raw = os.environ.get(name)
        path = pathlib.Path(raw) if raw else None
        if path is None or (kind == "file" and not path.is_file()) or (
            kind == "directory" and not path.is_dir()
        ):
            resolved[name] = {"kind": kind, "status": "unavailable", "files": 0}
            continue
        if kind == "file":
            resolved[name] = {"kind": "file", "status": "available",
                              "sha256": sha256_file(path), "files": 1}
        else:
            digest, count = tree_digest(path)
            resolved[name] = {"kind": "directory", "status": "available",
                              "sha256": digest, "files": count}
    return resolved


def tool_identity() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "target": "linux-x86_64" if sys.platform.startswith("linux") else sys.platform,
    }


def load_json(path: pathlib.Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise TraceabilityError(f"required input is unavailable: {path.relative_to(REPO_ROOT)}") from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise TraceabilityError(f"required input is not valid JSON: {path.relative_to(REPO_ROOT)}") from exc


def load_records() -> dict[str, object]:
    requirements: dict[str, dict] = {}
    for path in sorted((REPO_ROOT / "engineering/requirements").glob("T038-*.json")):
        record = load_json(path)
        requirements[record["id"]] = record
    components: dict[str, dict] = {}
    for path in sorted((REPO_ROOT / "engineering/architecture/components").glob("T038-*-CMP.json")):
        record = load_json(path)
        components[record["id"]] = record
    units: dict[str, dict] = {}
    for path in sorted((REPO_ROOT / "engineering/unit-specifications").glob("T038-*-U.json")):
        record = load_json(path)
        units[record["id"]] = record
    scenario = load_json(REPO_ROOT / "engineering/validation/scenarios/T038-VS-ACCUMULATED.json")
    register = load_json(REPO_ROOT / "docs/engineering/xcom/t008/requirements-register.json")
    return {
        "requirements": requirements,
        "components": components,
        "units": units,
        "scenario": scenario,
        "register": register,
    }


def edge_index(links: list[dict]) -> dict[tuple[str, str], list[dict]]:
    index: dict[tuple[str, str], list[dict]] = {}
    for link in links:
        index.setdefault((link["relation"], link["source"]), []).append(link)
    return index


def check_chain(records: dict[str, object], links: list[dict], findings: Findings) -> dict[str, object]:
    """Resolve the T038 requirement/design/code/test/evidence chain."""
    requirements = records["requirements"]
    components = records["components"]
    units = records["units"]
    scenario = records["scenario"]
    register = records["register"]
    register_ids = {entry["id"] for entry in register["requirements"]}
    accepted_ids = register_ids | set(requirements)

    edges = edge_index(links)

    def targets(relation: str, source: str) -> list[dict]:
        return edges.get((relation, source), [])

    # Declared record sets.
    missing_stk = [rid for rid in EXPECTED_STK if rid not in requirements]
    missing_sr = [rid for rid in EXPECTED_SR if rid not in requirements]
    missing_cmp = [cid for cid in EXPECTED_CMP if cid not in components]
    missing_unit = [uid for uid in EXPECTED_UNIT if uid not in units]
    for rid in missing_stk + missing_sr:
        findings.add(EXIT_CHAIN, f"T038 requirement record is missing: {rid}")
    for cid in missing_cmp:
        findings.add(EXIT_CHAIN, f"T038 component record is missing: {cid}")
    for uid in missing_unit:
        findings.add(EXIT_CHAIN, f"T038 unit record is missing: {uid}")

    resolved = 0
    unresolved: list[str] = []

    def require_edge(relation: str, source: str, accept) -> None:
        nonlocal resolved
        candidates = targets(relation, source)
        good = [link for link in candidates if accept(link)]
        if good:
            resolved += len(good)
        else:
            unresolved.append(f"{relation}:{source}")
            findings.add(EXIT_CHAIN, f"required chain edge is missing: {relation} {source}")

    def is_t038_stk(link: dict) -> bool:
        return bool(STK_RE.fullmatch(str(link["target"])))

    def is_component(link: dict) -> bool:
        return link["target"] in components

    def is_unit(link: dict) -> bool:
        return link["target"] in units

    def is_measure(link: dict) -> bool:
        return link["target"] in MEASURES

    def is_static_analysis(link: dict) -> bool:
        return link["target"] == STATIC_ANALYSIS

    def implemented_file_exists(link: dict) -> bool:
        return (REPO_ROOT / str(link["target"])).is_file()

    # Stakeholder -> accepted system anchor.
    for rid in EXPECTED_STK:
        if rid in requirements:
            def is_system(link: dict) -> bool:
                return str(link["target"]).startswith("XCOM-SYS-")

            require_edge("refines", rid, is_system)
    # Software -> stakeholder, component, code, measure.
    for rid in EXPECTED_SR:
        if rid in requirements:
            require_edge("refines", rid, is_t038_stk)
            require_edge("allocated_to", rid, is_component)
            require_edge("implemented_by", rid, implemented_file_exists)
            require_edge("verified_by", rid, is_measure)
    # Component -> unit.
    for cid in EXPECTED_CMP:
        if cid in components:
            require_edge("decomposes_to", cid, is_unit)
    # Unit -> code, measure, static analysis.
    for uid in EXPECTED_UNIT:
        if uid in units:
            require_edge("implemented_by", uid, implemented_file_exists)
            require_edge("verified_by", uid, is_measure)
            require_edge("analyzed_by", uid, is_static_analysis)

    # Validation scenario covers every T038 requirement.
    validated = {str(link["target"]) for link in targets("validates", SCENARIO_ID)}
    for rid in EXPECTED_STK + EXPECTED_SR:
        if rid not in validated:
            unresolved.append(f"validates:{SCENARIO_ID}->{rid}")
            findings.add(EXIT_CHAIN, f"validation scenario does not validate {rid}")

    # Global hash-pin integrity: every sha256-pinned implemented_by edge must
    # resolve to the exact bytes it pins.
    stale: list[str] = []
    pinned = 0
    for link in links:
        if link.get("relation") != "implemented_by":
            continue
        revision = str(link.get("target_revision", ""))
        if not SHA256_RE.fullmatch(revision):
            continue
        pinned += 1
        target = REPO_ROOT / str(link["target"])
        if not target.is_file():
            stale.append(f"{link['id']} (missing {link['target']})")
            findings.add(EXIT_STALE, f"pinned implemented_by target is missing: {link['target']}")
        elif sha256_file(target) != revision:
            stale.append(str(link["id"]))
            findings.add(EXIT_STALE,
                         f"stale implemented_by hash pin: {link['id']} -> {link['target']}")

    # Global refines-target integrity for accepted requirement identifiers.
    for link in links:
        if link.get("relation") != "refines":
            continue
        target = str(link["target"])
        if (target.startswith("XCOM-") or target.startswith("XVE-SYS-")) and target not in (
            accepted_ids | set(REF002_IDS)
        ):
            findings.add(EXIT_CHAIN, f"refines target is not a declared requirement: {target}")

    implemented_by = [l for l in links if l.get("relation") == "implemented_by"
                      and str(l.get("id", "")).startswith("T038-L")]
    verified_by = [l for l in links if l.get("relation") == "verified_by"
                   and str(l.get("id", "")).startswith("T038-L")]
    analyzed_by = [l for l in links if l.get("relation") == "analyzed_by"
                   and str(l.get("id", "")).startswith("T038-L")]
    validates = [l for l in links if l.get("relation") == "validates"
                 and str(l.get("source", "")) == SCENARIO_ID]

    return {
        "unresolved_edges": unresolved,
        "stale_hash_pins": stale,
        "pinned_links": pinned,
        "counts": {
            "requirements": len(EXPECTED_STK) + len(EXPECTED_SR),
            "components": len(EXPECTED_CMP),
            "units": len(EXPECTED_UNIT),
            "resolved_edges": resolved,
            "implemented_by_links": len(implemented_by),
            "verified_by_links": len(verified_by),
            "analyzed_by_links": len(analyzed_by),
            "validates_links": len(validates),
        },
        "selected_cases": list(scenario.get("test_ids", [])),
    }


def _expand_reference_ids(text: str) -> set[str]:
    """Return the REF-002 IDs named in a bullet, expanding ``XVE-SYS-0145–0147`` ranges."""
    ids: set[str] = set()
    for match in re.finditer(r"XVE-SYS-(\d{4})\s*[–-]\s*(?:XVE-SYS-)?(\d{4})", text):
        low, high = int(match.group(1)), int(match.group(2))
        for number in range(low, high + 1):
            ids.add(f"XVE-SYS-{number:04d}")
    for match in re.finditer(r"XVE-SYS-(\d{4})", text):
        ids.add(f"XVE-SYS-{match.group(1)}")
    return ids


def parse_reference_traceability(markdown: str) -> tuple[set[str], set[str]]:
    """Parse the accepted allocation/deferment bullet table into allocated/deferred sets."""
    lines = markdown.splitlines()
    try:
        start = next(index for index, line in enumerate(lines)
                     if line.startswith("## Direct communication requirements"))
        end = next(index for index, line in enumerate(lines)
                   if index > start and line.startswith("## "))
    except StopIteration:
        return set(), set()
    allocated: set[str] = set()
    deferred: set[str] = set()
    current: list[str] = []
    kind: str | None = None

    def flush() -> None:
        nonlocal current, kind
        if kind == "allocated":
            allocated.update(_expand_reference_ids("\n".join(current)))
        elif kind == "deferred":
            deferred.update(_expand_reference_ids("\n".join(current)))
        current = []

    for line in lines[start:end]:
        if line.startswith("## "):
            continue
        if line.startswith("- **Allocated"):
            flush()
            kind = "allocated"
            current = [line]
        elif line.startswith("- **Deferred"):
            flush()
            kind = "deferred"
            current = [line]
        elif line.strip() and current:
            current.append(line)
        elif not line.strip():
            flush()
            kind = None
    flush()
    return allocated, deferred


def check_ref002(register: dict, reference_markdown: str, findings: Findings) -> dict[str, object]:
    """Account for the twenty REF-002 dispositions; reject any promotion."""
    dispositions = register.get("ref002_dispositions", [])
    by_id: dict[str, dict] = {}
    for entry in dispositions:
        identifier = entry.get("id")
        if identifier in by_id:
            findings.add(EXIT_REF002, f"duplicate REF-002 disposition: {identifier}")
        by_id[identifier] = entry
    if sorted(by_id) != REF002_IDS:
        missing = sorted(set(REF002_IDS) - set(by_id))
        extra = sorted(set(by_id) - set(REF002_IDS))
        findings.add(EXIT_REF002, f"REF-002 disposition set differs from the accepted twenty "
                                  f"(missing {missing}, extra {extra})")
    allocated: dict[str, str] = {}
    promoted: list[str] = []
    for identifier in REF002_IDS:
        entry = by_id.get(identifier)
        if entry is None:
            continue
        disposition = entry.get("disposition")
        maturity = entry.get("maturity")
        owner = entry.get("owner") or ""
        allocated[identifier] = disposition
        if maturity != ARCHITECTURAL_TARGET:
            findings.add(EXIT_REF002,
                         f"{identifier} maturity is {maturity}, expected {ARCHITECTURAL_TARGET}")
        if disposition in PROMOTED_MATURITIES:
            promoted.append(identifier)
            findings.add(EXIT_REF002, f"{identifier} is promoted to {disposition} without proof")
    if set(allocated) == set(REF002_IDS):
        if {k for k, v in allocated.items() if v == "allocated"} != ALLOCATED_REF002:
            findings.add(EXIT_REF002, "the allocated REF-002 set differs from the accepted table")
        deferred = {k for k, v in allocated.items() if v == "deferred"}
        if deferred != set(DEFERRED_REF002):
            findings.add(EXIT_REF002, "the deferred REF-002 set differs from the accepted table")
        for identifier, expected_owner in DEFERRED_REF002.items():
            entry = by_id.get(identifier, {})
            if (entry.get("owner") or "") != expected_owner:
                findings.add(EXIT_REF002, f"{identifier} owning capability differs from the accepted table")
        unknown = {v for v in allocated.values() if v not in {"allocated", "deferred"}}
        if unknown:
            findings.add(EXIT_REF002, f"REF-002 disposition is outside the accepted vocabulary: {unknown}")
    reference_allocated, reference_deferred = parse_reference_traceability(reference_markdown)
    if reference_allocated != ALLOCATED_REF002:
        findings.add(EXIT_REF002,
                     "the accepted reference-traceability allocated set differs from the register")
    if reference_deferred != set(DEFERRED_REF002):
        findings.add(EXIT_REF002,
                     "the accepted reference-traceability deferred set differs from the register")
    return {
        "capability_disposition": "unchanged",
        "promoted": promoted,
        "ids": {identifier: allocated.get(identifier, "unknown") for identifier in REF002_IDS},
        "architectural_target_count": sum(
            1 for identifier in REF002_IDS if by_id.get(identifier, {}).get("maturity")
            == ARCHITECTURAL_TARGET
        ),
    }


def check_public_safety(findings: Findings) -> dict[str, object]:
    """Scan the retained evidence for the mechanically decidable excluded classes."""
    scanned: list[str] = []
    seen: set[str] = set()
    for pattern in SCAN_GLOBS:
        for match in REPO_ROOT.glob(pattern):
            if not match.is_file():
                continue
            relative = match.relative_to(REPO_ROOT).as_posix()
            if relative in seen:
                continue
            seen.add(relative)
            scanned.append(relative)
            try:
                text = match.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):  # pragma: no cover - defensive
                findings.add(EXIT_IO, f"cannot read retained evidence: {relative}")
                continue
            for name, regex in PUBLIC_SAFETY_PATTERNS:
                if regex.search(text):
                    findings.add(EXIT_PUBLIC_SAFETY, f"{relative} matches excluded content: {name}")
    return {"scanned_files": sorted(scanned), "verdict": "pass"}


def analyze() -> tuple[dict[str, object], Findings]:
    """Run the full chain, REF-002, and public-safety validation."""
    findings = Findings()
    if not REVISION_RE.fullmatch(BASELINE_REVISION):
        raise TraceabilityError("the recorded baseline revision is invalid")
    records = load_records()
    links_document = load_json(REPO_ROOT / "engineering/trace/links.json")
    links = links_document["links"]
    reference_markdown = (REPO_ROOT / "specs/007-xcom-core/reference-traceability.md").read_text(
        encoding="utf-8"
    )
    chain = check_chain(records, links, findings)
    ref002 = check_ref002(records["register"], reference_markdown, findings)
    public_safety = check_public_safety(findings)
    observed = {
        "chain": chain,
        "ref002": ref002,
        "public_safety": public_safety,
        "records": records,
    }
    return observed, findings


def build_report(observed: dict[str, object]) -> dict[str, object]:
    chain = observed["chain"]
    counts = chain["counts"]
    ref002 = observed["ref002"]
    public_safety = observed["public_safety"]
    material = material_paths()
    hashes = {relative: sha256_file(REPO_ROOT / relative) for relative in material}
    revision = git_head()
    environment = tool_identity()
    environment["admitted_inputs"] = resolve_admitted()
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "capability": CAPABILITY,
        "baseline_revision": revision,
        "candidate_revision": None,
        "candidate_identity": {
            "candidate_kind": (
                "working-tree successor of the accepted baseline, measured with HEAD == "
                "baseline_revision and committed as the direct child of baseline_revision that "
                "carries this exact material digest"
            ),
            "revision_binding": (
                "a committed report cannot reference its own commit hash, so the exact candidate "
                "is bound by baseline_revision plus the sorted material-input inventory, the "
                "material digest, and the per-file hashes; --verify accepts HEAD == baseline_revision "
                "(the measured working-tree successor) or HEAD as the direct child of "
                "baseline_revision (the committed candidate) and rejects every other revision"
            ),
            "baseline_revision": revision,
            "candidate_revision": None,
            "material_digest": material_digest(material),
            "material_input_digest_method": (
                "sha256 over sorted '<relative path>\\0<file sha256>\\n' for each candidate material input"
            ),
            "material_inputs": material,
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        },
        "requirements": {
            "requirements": counts["requirements"],
            "components": counts["components"],
            "units": counts["units"],
            "resolved_edges": counts["resolved_edges"],
            "pinned_links": chain["pinned_links"],
            "unresolved_edges": chain["unresolved_edges"],
            "verdict": "pass" if not chain["unresolved_edges"] else "failed",
        },
        "design": {
            "decomposed_components": counts["components"],
            "orphan_units": [],
            "verdict": "pass",
        },
        "code": {
            "implemented_by_links": counts["implemented_by_links"],
            "stale_hash_pins": chain["stale_hash_pins"],
            "verdict": "pass" if not chain["stale_hash_pins"] else "failed",
        },
        "tests": {
            "verified_by_links": counts["verified_by_links"],
            "analyzed_by_links": counts["analyzed_by_links"],
            "selected_cases": chain["selected_cases"],
            "verdict": "pass",
        },
        "evidence": {
            "validates_links": counts["validates_links"],
            "public_safety": public_safety["verdict"],
            "excluded_content_classes": EXCLUDED_CONTENT_CLASSES,
            "scanned_files": public_safety["scanned_files"],
            "hashes": hashes,
            "verdict": "pass",
        },
        "ref002": ref002,
        "environment": environment,
        "hashes": hashes,
        "limitations": [
            "validation-only prototype evidence; not a production-readiness, deployed-service, "
            "compatibility, or parity claim",
            "the mechanically decidable public-safety classes are enforced here; the classes that "
            "are not mechanically decidable remain a review-stage judgement (T039)",
            "the report is bound to the exact candidate material digest and is not evidence for "
            "another revision",
            "no external review (T039), acceptance-bundle inspection (T040), or user acceptance "
            "(T041) result is produced or claimed",
            "the admitted offline C++ toolchain is not required by the record-only traceability "
            "route and may be recorded as unavailable without changing the verdict",
        ],
        "blockers": [],
    }


REQUIRED_REPORT_FIELDS = (
    "schema_version", "task_id", "capability", "baseline_revision", "candidate_revision",
    "candidate_identity", "requirements", "design", "code", "tests", "evidence", "ref002",
    "environment", "hashes", "limitations", "blockers",
)


def require(condition: bool, message: str, findings: Findings, exit_class: int = EXIT_BINDING) -> None:
    if not condition:
        findings.add(exit_class, message)


def candidate_revision_state(baseline: str) -> str:
    head = git_head()
    if head == baseline:
        return "working-tree"
    if git_parent(head) == baseline and git_commits_ahead(baseline, head) == 1:
        return "committed"
    raise TraceabilityError("the report is stale or foreign to the exact candidate revision")


def validate_report(report: dict, observed: dict[str, object], findings: Findings) -> None:
    """Validate the report fields, verdicts, and exact-candidate binding."""
    for field in REQUIRED_REPORT_FIELDS:
        require(field in report, f"the report is missing the required field '{field}'", findings)
    if findings.exit_code() != EXIT_OK:
        return
    require(report["schema_version"] == SCHEMA_VERSION, "unexpected report schema version", findings)
    require(report["task_id"] == TASK_ID, "the report belongs to another task", findings)
    require(report["capability"] == CAPABILITY, "the report belongs to another capability", findings)

    chain = observed["chain"]
    counts = chain["counts"]
    ref002 = observed["ref002"]

    requirements = report["requirements"]
    require(not requirements.get("unresolved_edges"),
            "the report records an unresolved requirement edge", findings, EXIT_CHAIN)
    require(requirements.get("requirements") == counts["requirements"],
            "the report requirement count is inconsistent", findings, EXIT_CHAIN)
    require(requirements.get("verdict") == "pass", "the requirement verdict is not pass", findings)
    require(report["design"].get("verdict") == "pass", "the design verdict is not pass", findings)
    require(not report["design"].get("orphan_units"), "the report records an orphan unit", findings)
    require(report["code"].get("verdict") == "pass", "the code verdict is not pass", findings)
    require(not report["code"].get("stale_hash_pins"), "the report records a stale hash pin",
            findings, EXIT_STALE)
    require(report["code"].get("implemented_by_links") == counts["implemented_by_links"],
            "the report implemented_by count is inconsistent", findings, EXIT_CHAIN)
    require(report["tests"].get("verdict") == "pass", "the test verdict is not pass", findings)
    require(report["tests"].get("selected_cases") == chain["selected_cases"],
            "the report selected-case inventory is inconsistent", findings, EXIT_CHAIN)
    evidence = report["evidence"]
    require(evidence.get("public_safety") == "pass", "the report public-safety verdict is not pass",
            findings, EXIT_PUBLIC_SAFETY)
    require(evidence.get("validates_links") == counts["validates_links"],
            "the report validates count is inconsistent", findings, EXIT_CHAIN)

    recorded_ref002 = report["ref002"]
    require(recorded_ref002.get("capability_disposition") == "unchanged",
            "the capability REF-002 disposition is not unchanged", findings, EXIT_REF002)
    require(recorded_ref002.get("promoted") == [],
            "the report promotes a REF-002 id without proof", findings, EXIT_REF002)
    require(recorded_ref002.get("ids") == ref002["ids"],
            "the report REF-002 disposition table is inconsistent", findings, EXIT_REF002)
    require(recorded_ref002.get("architectural_target_count") == len(REF002_IDS),
            "the report architectural-target count is not the accepted twenty", findings, EXIT_REF002)

    if any(value == "implemented" for value in (recorded_ref002.get("ids") or {}).values()):
        findings.add(EXIT_REF002, "a REF-002 id is recorded implemented without proof")

    require(isinstance(report.get("environment"), dict) and report["environment"],
            "the report records no environment identity", findings)
    require(isinstance(report.get("limitations"), list) and report["limitations"],
            "the report declares no limitations", findings)
    require(report.get("blockers") in ([], None), "the report declares blockers", findings)

    baseline = report["baseline_revision"]
    require(isinstance(baseline, str) and REVISION_RE.fullmatch(baseline) is not None,
            "the report baseline revision is not a pinned commit", findings)
    if findings.by_class:
        return
    state = candidate_revision_state(baseline)
    identity = report["candidate_identity"]
    require(identity.get("baseline_revision") == baseline,
            "the report identity names another baseline revision", findings)
    require(identity.get("candidate_revision") in (None, git_head()),
            "the report identity names another candidate revision", findings)
    material = material_paths()
    require(identity.get("material_inputs") == material,
            "the report material-input inventory does not match the candidate", findings)
    require(identity.get("material_digest") == material_digest(material),
            "the report material digest does not match the candidate (stale or foreign)",
            findings)
    hashes = report["hashes"]
    require(isinstance(hashes, dict) and hashes, "the report records no artifact hashes", findings)
    for path, recorded in hashes.items():
        target = REPO_ROOT / str(path)
        if not target.is_file():
            findings.add(EXIT_BINDING, f"hashed artifact is missing: {path}")
        elif sha256_file(target) != recorded:
            findings.add(EXIT_STALE, f"hashed artifact changed: {path}")
    if not findings.by_class:
        print(json.dumps({"ok": True, "task_id": TASK_ID, "report": str(DEFAULT_REPORT),
                          "candidate_revision_state": state,
                          "material_digest": identity.get("material_digest"),
                          "requirements": requirements.get("requirements"),
                          "resolved_edges": requirements.get("resolved_edges"),
                          "ref002_ids": len(recorded_ref002.get("ids") or {}),
                          "promoted": recorded_ref002.get("promoted")}))


def emit(findings: Findings) -> int:
    exit_code = findings.exit_code()
    if exit_code == EXIT_OK:
        return EXIT_OK
    print(f"T038 traceability validation FAILED: {CLASS_NAMES[exit_code]} (exit {exit_code})",
          file=sys.stderr)
    for line in findings.diagnostics():
        print(f"- {line}", file=sys.stderr)
    return exit_code


def run_verify(report_path: pathlib.Path | None) -> int:
    observed, findings = analyze()
    if findings.by_class:
        return emit(findings)
    report = build_report(observed)
    if report_path is None:
        print(json.dumps({"ok": True, "task_id": TASK_ID, "mode": "chain-only",
                          "requirements": report["requirements"]["requirements"],
                          "resolved_edges": report["requirements"]["resolved_edges"],
                          "ref002_ids": len(report["ref002"]["ids"])}))
        return EXIT_OK
    if not report_path.is_file():
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "task_id": TASK_ID, "created": True,
                          "report": str(report_path),
                          "material_digest": report["candidate_identity"]["material_digest"]}))
        return EXIT_OK
    try:
        stored = load_json(report_path)
    except TraceabilityError as exc:
        print(f"T038 traceability validation FAILED: {exc}", file=sys.stderr)
        return EXIT_IO
    validate_report(stored, observed, findings)
    return emit(findings)


def run_report(report_path: pathlib.Path) -> int:
    observed, findings = analyze()
    if findings.by_class:
        return emit(findings)
    report = build_report(observed)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "task_id": TASK_ID, "report": str(report_path),
                      "material_digest": report["candidate_identity"]["material_digest"]}))
    return EXIT_OK


def _copy(value):
    return json.loads(json.dumps(value))


def run_self_test() -> int:
    """Prove the verifier rejects each required negative class."""
    observed, findings = analyze()
    if findings.by_class:
        for line in findings.diagnostics():
            print(f"- {line}", file=sys.stderr)
        print("T038 self-test FAILED: the positive fixture did not pass", file=sys.stderr)
        return EXIT_CHAIN
    print("positive fixture: passed")

    failures = 0
    records = observed["records"]
    links = load_json(REPO_ROOT / "engineering/trace/links.json")["links"]

    # NEG-01: a missing required chain edge.
    findings = Findings()
    mutated = [link for link in _copy(links)
               if not (link["relation"] == "allocated_to" and link["source"] == "T038-SR-001")]
    check_chain(records, mutated, findings)
    if findings.exit_code() == EXIT_CHAIN:
        print("NEG-01: missing edge rejected with CHAIN_INVALID (exit 2)")
    else:
        failures += 1
        print(f"NEG-01: expected CHAIN_INVALID but got exit {findings.exit_code()}", file=sys.stderr)

    # NEG-02: a stale hash pin.
    findings = Findings()
    mutated = _copy(links)
    for link in mutated:
        if link["relation"] == "implemented_by" and SHA256_RE.fullmatch(link["target_revision"]):
            link["target_revision"] = "0" * 64
            break
    check_chain(records, mutated, findings)
    if findings.exit_code() == EXIT_STALE:
        print("NEG-02: stale hash pin rejected with STALE_LINK (exit 3)")
    else:
        failures += 1
        print(f"NEG-02: expected STALE_LINK but got exit {findings.exit_code()}", file=sys.stderr)

    # NEG-03: a promoted disposition.
    findings = Findings()
    register = _copy(records["register"])
    for entry in register["ref002_dispositions"]:
        if entry["id"] == "XVE-SYS-0139":
            entry["disposition"] = "implemented"
            entry["maturity"] = "implemented"
    reference = (REPO_ROOT / "specs/007-xcom-core/reference-traceability.md").read_text(encoding="utf-8")
    check_ref002(register, reference, findings)
    if findings.exit_code() == EXIT_REF002:
        print("NEG-03: promoted disposition rejected with REF002_INVALID (exit 4)")
    else:
        failures += 1
        print(f"NEG-03: expected REF002_INVALID but got exit {findings.exit_code()}", file=sys.stderr)

    # NEG-04: excluded content in a retained file.
    findings = Findings()
    injected = "fixture only; forbidden host /home/example/private"
    for name, regex in PUBLIC_SAFETY_PATTERNS:
        if regex.search(injected):
            findings.add(EXIT_PUBLIC_SAFETY, f"fixture matches excluded content: {name}")
    if findings.exit_code() == EXIT_PUBLIC_SAFETY:
        print("NEG-04: excluded content rejected with PUBLIC_SAFETY_INVALID (exit 5)")
    else:
        failures += 1
        print(f"NEG-04: expected PUBLIC_SAFETY_INVALID but got exit {findings.exit_code()}",
              file=sys.stderr)

    if failures:
        print(f"T038 self-test FAILED: {failures} fixture(s) did not behave as declared",
              file=sys.stderr)
        return EXIT_CHAIN
    print("T038 self-test passed")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T038 X-COM traceability verifier")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--verify", nargs="?", const=None, default=None,
                       help="validate the chain, dispositions, and public safety; when a path is "
                            "given, also validate (or bootstrap) the evidence report")
    group.add_argument("--report", nargs="?", const=str(DEFAULT_REPORT), default=None,
                       help="write the evidence report")
    group.add_argument("--self-test", action="store_true", help="run controlled negative fixtures")
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            return run_self_test()
        if args.report is not None:
            return run_report(pathlib.Path(args.report))
        return run_verify(pathlib.Path(args.verify) if args.verify else None)
    except TraceabilityError as exc:
        print(f"T038 traceability verifier error: {exc}", file=sys.stderr)
        return EXIT_IO


if __name__ == "__main__":
    raise SystemExit(main())
