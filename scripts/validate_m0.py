#!/usr/bin/env python3
"""Offline checks for the M0 documentation package; never executes legacy code."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import quote, unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
REPOSITORIES = ("xverse-platform", "xverse-compat", "xverse-blueprints")
FIELDS = (
    "Repository name", "Primary purpose", "Language/build system",
    "Runtime artifact produced", "Runtime dependencies", "Communication interfaces",
    "Protocols used", "Input/output contracts", "Startup dependencies",
    "Configuration mechanism", "Current integration", "Classification",
    "Candidate compatibility boundary", "Risks if changed", "Recommended long-term treatment",
)
REPORTS = (
    "REPOSITORY_INVENTORY.md", "DEPENDENCY_MAP.md", "INTERFACE_CATALOG.md",
    "MIGRATION_CLASSIFICATION.md",
)
SHA = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^\s)]+)\)")


def snapshot_errors(data: dict) -> list[str]:
    """Validate documentary records, including legitimate empty-remote states."""
    errors: list[str] = []
    records = data.get("repositories", [])
    names = [r.get("name") for r in records]
    if len(names) != len(set(names)):
        errors.append("duplicate repository names")
    roles = {role: [r for r in records if r.get("role") == role] for role in ("legacy", "vnext")}
    expected = {"total": len(records), **{role: len(rows) for role, rows in roles.items()}}
    if data.get("counts") != expected or sum(len(v) for v in roles.values()) != len(records):
        errors.append("coverage counts/roles do not reconcile")
    if {r.get("name") for r in roles["vnext"]} != set(REPOSITORIES):
        errors.append("vNext repository set differs from authorized destinations")
    if data.get("runtime_executed") is not False:
        errors.append("M0 must not claim runtime execution")
    for record in records:
        name = record.get("name", "<missing>")
        pin = record.get("commit_sha")
        if record.get("full_name") != f"The-Xverse/{name}":
            errors.append(f"{name}: invalid repository identity")
        if not pin:
            if record.get("coverage") != "empty-remote" or record.get("role") != "vnext":
                errors.append(f"{name}: unexplained missing revision")
            continue
        if not SHA.fullmatch(pin):
            errors.append(f"{name}: malformed revision pin")
        base = f"https://github.com/The-Xverse/{name}"
        if record.get("tree_url") != f"{base}/tree/{pin}":
            errors.append(f"{name}: tree URL is not revision-pinned")
        if record.get("tree_truncated") is not False:
            errors.append(f"{name}: incomplete tree needs explicit disposition")
        sources = record.get("sources", [])
        paths = [source.get("path") for source in sources]
        if len(paths) != len(set(paths)):
            errors.append(f"{name}: duplicate source paths")
        for source in sources:
            path = source.get("path")
            if not path or path.startswith("/") or ".." in Path(path).parts:
                errors.append(f"{name}: missing or unsafe source path")
                continue
            if source.get("url") != f"{base}/blob/{pin}/{quote(path, safe='/')}":
                errors.append(f"{name}: source URL/path/revision mismatch")
            if not SHA.fullmatch(source.get("blob_sha", "")) or not SHA256.fullmatch(source.get("sha256", "")):
                errors.append(f"{name}: missing evidence content hashes")
        if record.get("role") == "legacy":
            if not sources:
                errors.append(f"{name}: no inspected evidence")
            if set(record.get("fields", {})) != set(FIELDS):
                errors.append(f"{name}: expected all 15 inventory fields")
            for field, value in record.get("fields", {}).items():
                if not value or not re.match(r"(?:O|D|I|U)(?:/[ODIU])* — ", value):
                    errors.append(f"{name}/{field}: missing evidence classification")
    lookup = {r.get("name"): r for r in records}
    pins = data.get("autoverse_manifest_pins", [])
    if len(pins) != 10 or len({p.get("repository") for p in pins}) != 10:
        errors.append("expected ten distinct declared AutoVerse dependencies")
    for pin in pins:
        if pin.get("status") != "resolved" or not SHA.fullmatch(pin.get("resolved_sha") or ""):
            errors.append("unresolved AutoVerse manifest version")
        if pin.get("resolved_sha") != lookup.get(pin.get("repository"), {}).get("commit_sha"):
            errors.append("manifest/default-branch equality claim needs revision")
    return errors


def authored_files(root: Path) -> list[Path]:
    """Return authored Markdown and governance files covered by M0 checks."""

    paths = list((root / "specs").rglob("*.md"))
    paths += [p for p in (root / "docs").rglob("*.md") if "architecture" not in p.parts]
    for name in REPOSITORIES:
        repo = root.parent / name
        paths += [repo / "README.md", repo / "AGENTS.md", repo / ".specify/memory/constitution.md"]
    return sorted(set(paths))


def anchors(text: str) -> set[str]:
    """Extract explicit and GitHub-style heading anchors from Markdown."""

    found = set(re.findall(r'<a id="([^"]+)"', text))
    for heading in re.findall(r"^#+\s+(.+)$", text, re.MULTILINE):
        found.add(re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-"))
    return found


def package_errors(root: Path, data: dict) -> list[str]:
    """Validate the complete M0 package, links, evidence, and preserved files."""

    errors = snapshot_errors(data)
    legacy_dir = root / "docs/legacy"
    for name in REPORTS:
        if not (legacy_dir / name).is_file():
            errors.append(f"missing report: {name}")
    inventory = (legacy_dir / REPORTS[0]).read_text() if (legacy_dir / REPORTS[0]).exists() else ""
    for record in data["repositories"]:
        if record["role"] != "legacy":
            continue
        if f'<a id="{record["anchor"]}"></a>' not in inventory:
            errors.append(f"{record['name']}: missing inventory entry")
        for index, field in enumerate(FIELDS, 1):
            value = record["fields"].get(field, "").replace("|", "/")
            if f"| {index}. {field} | {value} |" not in inventory:
                errors.append(f"{record['name']}/{field}: report and snapshot disagree")
    known_sources = {
        source["url"] for record in data["repositories"] for source in record.get("sources", [])
    } | {record["tree_url"] for record in data["repositories"] if record.get("tree_url")}
    for path in authored_files(root):
        if not path.is_file():
            errors.append(f"missing authored document: {path}")
            continue
        content = path.read_text()
        if re.search(r"\[NEEDS CLARIFICATION[^\]]*\]|\[PROJECT_NAME\]|\[FEATURE NAME\]|TODO\(", content):
            errors.append(f"{path.name}: unresolved authored placeholder")
        if re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b|/home/[^/\s]+|C:[/\\]Users[/\\]", content):
            errors.append(f"{path.name}: potential private infrastructure/path value")
        if re.search(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|-----BEGIN .*PRIVATE KEY-----", content):
            errors.append(f"{path.name}: potential credential material")
        without_fences = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        for link in LINK.findall(without_fences):
            parsed = urlsplit(link)
            if parsed.scheme:
                if parsed.netloc == "github.com" and "/The-Xverse/" in parsed.path:
                    if link.split("#")[0] not in known_sources:
                        errors.append(f"{path.name}: unregistered or unpinned evidence link: {link}")
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not target.exists():
                errors.append(f"{path.name}: broken local link: {link}")
            elif parsed.fragment and target.is_file() and target.suffix == ".md":
                if unquote(parsed.fragment) not in anchors(target.read_text()):
                    errors.append(f"{path.name}: broken anchor: {link}")
    for relative, expected_hash in data["preserved_sha256"].items():
        path = root.parent / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            errors.append(f"original file changed: {relative}")
    guidance = "XVERSE_VNEXT_ARCHITECTURE_AND_CODEX_GUIDANCE.md"
    if (root / guidance).read_bytes() != (root / "docs/architecture" / guidance).read_bytes():
        errors.append("architecture guidance copy differs from original")
    constitutions = []
    required = (
        "memory/constitution.md", "commands/speckit.specify.md", "commands/speckit.clarify.md",
        "commands/speckit.plan.md", "commands/speckit.tasks.md", "commands/speckit.analyze.md",
        "commands/speckit.implement.md", "scripts/bash/check-prerequisites.sh",
        "templates/spec-template.md", "templates/plan-template.md", "templates/tasks-template.md",
        "workflows/speckit/workflow.yml",
    )
    for name in REPOSITORIES:
        repo = root.parent / name
        for relative in required:
            if not (repo / ".specify" / relative).is_file():
                errors.append(f"{name}: missing official Spec Kit asset {relative}")
        constitutions.append((repo / ".specify/memory/constitution.md").read_bytes())
        options = json.loads((repo / ".specify/init-options.json").read_text())
        if options.get("speckit_version") != "0.14.0" or options.get("integration") != "generic":
            errors.append(f"{name}: unexpected Spec Kit setup")
    if len(set(constitutions)) != 1:
        errors.append("constitutions differ across repositories")
    pointer = json.loads((root / ".specify/feature.json").read_text())
    if pointer.get("feature_directory") != "specs/001-legacy-repository-inventory":
        errors.append("M0 feature pointer is incorrect")
    return errors


def negative_checks(data: dict) -> int:
    """Mutate in-memory copies only: no legacy or deliverable files are changed."""
    cases = []
    missing = copy.deepcopy(data)
    missing["repositories"].pop(0)
    cases.append(("missing repository", missing, "coverage counts"))
    duplicate = copy.deepcopy(data)
    duplicate["repositories"].append(copy.deepcopy(duplicate["repositories"][0]))
    cases.append(("duplicate repository", duplicate, "duplicate repository"))
    malformed = copy.deepcopy(data)
    legacy = next(r for r in malformed["repositories"] if r["role"] == "legacy")
    legacy["commit_sha"] = "main"
    cases.append(("mutable revision", malformed, "malformed revision"))
    pathless = copy.deepcopy(data)
    next(r for r in pathless["repositories"] if r["sources"])["sources"][0]["path"] = ""
    cases.append(("missing evidence path", pathless, "missing or unsafe source path"))
    incomplete = copy.deepcopy(data)
    next(r for r in incomplete["repositories"] if r["role"] == "legacy")["fields"].pop("Input/output contracts")
    cases.append(("missing required field", incomplete, "all 15 inventory fields"))
    for label, changed, expected in cases:
        if not any(expected in error for error in snapshot_errors(changed)):
            raise AssertionError(f"negative check failed: {label}")
        print(f"PASS negative check: {label}")
    return len(cases)


def negative_package_checks(root: Path, data: dict) -> int:
    """Exercise file corruption checks only in temporary copies of vNext files."""
    with tempfile.TemporaryDirectory(prefix="xverse-m0-validation-") as temporary:
        workspace = Path(temporary)
        for name in REPOSITORIES:
            shutil.copytree(
                root.parent / name, workspace / name,
                ignore=shutil.ignore_patterns(".git", ".agents", ".codex", "__pycache__"),
            )
        copied_root = workspace / root.name
        baseline_errors = package_errors(copied_root, data)
        if baseline_errors:
            raise AssertionError(f"temporary fixture failed: {baseline_errors}")
        cases = (
            (
                copied_root / "docs/architecture/XVERSE_VNEXT_ARCHITECTURE_AND_CODEX_GUIDANCE.md",
                "guidance copy mismatch", "guidance copy differs",
            ),
            (
                workspace / "xverse-compat/.specify/memory/constitution.md",
                "constitution mismatch", "constitutions differ",
            ),
        )
        for path, label, expected in cases:
            original = path.read_bytes()
            try:
                path.write_bytes(original + b"\nTemporary negative-check mutation.\n")
                if not any(expected in error for error in package_errors(copied_root, data)):
                    raise AssertionError(f"negative check failed: {label}")
            finally:
                path.write_bytes(original)
            print(f"PASS negative check: {label}")
    return len(cases)


def main() -> int:
    """Run M0 package checks and optional negative self-tests."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="also check invalid snapshots and temporary file copies")
    args = parser.parse_args()
    data = json.loads((ROOT / "docs/legacy/inventory-snapshot.json").read_text())
    errors = package_errors(ROOT, data)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    counts = data["counts"]
    print(f"PASS: {counts['total']} repositories ({counts['legacy']} legacy, {counts['vnext']} vNext); "
          "15 fields per legacy record; evidence, links, governance and preservation checks")
    if args.self_test:
        negative_checks(data)
        negative_package_checks(ROOT, data)
    print("Limits: offline checks establish structural consistency, not factual completeness, "
          "remote access, runtime compatibility or human acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
