#!/usr/bin/env python3
"""DV12 acceptance-evidence gate for Maestro Lite full runs (increment19, finding 456).

Reads one full-run directory written by verify-platform-regression-20261021t.py (or a successor
with the same receipt fields) and decides whether it may be presented as acceptance evidence for
an expected candidate commit. Every blocker is reported; the gate never repairs or reruns.

Usage: validate_maestro_acceptance_evidence.py <run-dir> --candidate <commit> --g4 <file>
       [--allowlist <file>] [--repo <path>] [--archive-sha <hex>] [--scope tree|code]

Staleness (B4): --scope tree (default) requires the run's archive to equal the candidate's whole
git archive; --scope code (finding 463) instead requires the git archives of CODE_PATHS to be equal
between the run's head and the candidate, so documentation-only commits after the run do not
block. Code identity is the content-addressed listing `git ls-tree -r <commit> -- CODE_PATHS` (modes,
blob ids, paths), because archive bytes also carry the commit id and time. Which scope is
authoritative for acceptance is an author decision.

Allowlist: JSON list of {"kind": "skipped"|"xfailed", "match": <substring of the -ra line>,
"reason": <text>, "approval": <author reference>}. G4 file: JSON object with "gate": "G4",
"disposition": "waived"|"satisfied", "scope": <text>, "approval": <author reference>.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

CODE_PATHS = ("src", "tests", "scripts", "xdl", "pyproject.toml")
COUNT = re.compile(r"(\d+) (passed|failed|errors?|skipped|xfailed|xpassed|deselected|warnings?)")


def summary_counts(line: str) -> dict:
    counts = {}
    for number, label in COUNT.findall(line):
        label = {"error": "errors", "warning": "warnings"}.get(label, label)
        counts[label] = counts.get(label, 0) + int(number)
    return counts


def outcome_lines(log: str, kind: str) -> list:
    prefix = {"skipped": "SKIPPED", "xfailed": "XFAIL"}[kind]
    return [line for line in log.splitlines() if line.startswith(prefix + " ")]


def archive_sha(repo: Path, commit: str) -> str:
    digest = hashlib.sha256()
    with subprocess.Popen(["git", "archive", commit], cwd=repo, stdout=subprocess.PIPE) as process:
        for chunk in iter(lambda: process.stdout.read(1 << 20), b""):
            digest.update(chunk)
    if process.returncode:
        raise SystemExit("git archive failed for " + commit)
    return digest.hexdigest()


def code_digest(repo: Path, commit: str) -> str:
    listing = subprocess.check_output(["git", "ls-tree", "-r", commit, "--", *CODE_PATHS], cwd=repo)
    return hashlib.sha256(listing).hexdigest()


def check(run: Path, candidate: str, g4: Path | None, allowlist: list, expected_archive: str | None,
          code_digests: tuple | None = None) -> dict:
    blockers = []
    try:
        configuration = json.loads((run / "configuration.json").read_text())
        receipt = json.loads((run / "wheel-receipt.json").read_text())
        log = (run / "wheel.log").read_text()
    except (OSError, ValueError) as error:
        return dict(accepted_as_evidence=False, blockers=["B0-missing-run-files: " + type(error).__name__])
    collected = receipt.get("collected")
    lines = [line for line in log.splitlines() if line.strip()]
    counts = summary_counts(lines[-1]) if lines else {}
    executed = sum(counts.get(k, 0) for k in ("passed", "failed", "errors", "skipped", "xfailed", "xpassed"))
    if not isinstance(collected, int) or collected <= 0 or executed == 0:
        blockers.append("B1-zero-tests")
    elif executed != collected or counts.get("deselected"):
        blockers.append(f"B1-count-mismatch: summary {executed} vs collected {collected}")
    if receipt.get("returncode") != 0 or counts.get("failed") or counts.get("errors"):
        blockers.append(f"B2-failures: returncode {receipt.get('returncode')}, failed {counts.get('failed', 0)}, errors {counts.get('errors', 0)}")
    if receipt.get("outer_timeout"):
        blockers.append("B2-outer-timeout")
    for kind in ("skipped", "xfailed"):
        listed = [line for line in outcome_lines(log, kind)
                  if not any(entry.get("kind") == kind and entry.get("match") and entry["match"] in line
                             and entry.get("reason") and entry.get("approval") for entry in allowlist)]
        if counts.get(kind, 0) and len(outcome_lines(log, kind)) < counts[kind]:
            blockers.append(f"B3-{kind}-unlisted: {counts[kind]} counted, {len(outcome_lines(log, kind))} reported with -ra")
        blockers.extend(f"B3-{kind}-unlisted: {line[:200]}" for line in listed)
    if counts.get("xpassed"):
        blockers.append(f"B3-xpassed: {counts['xpassed']}")
    if code_digests is not None:
        if receipt.get("git_head") != configuration.get("git_head") or code_digests[0] != code_digests[1]:
            blockers.append(f"B4-code-mismatch: run {receipt.get('git_head')} code differs from candidate {candidate}")
    elif receipt.get("git_head") != candidate or configuration.get("git_head") != candidate:
        blockers.append(f"B4-stale-head: run {receipt.get('git_head')} vs candidate {candidate}")
    if code_digests is None and expected_archive is not None and (receipt.get("archive_sha256") != expected_archive
                                         or configuration.get("archive_sha256") != expected_archive):
        blockers.append("B4-archive-mismatch: run archive is not the candidate's git archive")
    if configuration.get("installed_equals_frozen_src") is not True or configuration.get("wheel_verification") is not True:
        blockers.append("B4-not-installed-wheel-of-frozen-src")
    record = None
    if g4 is not None:
        try:
            record = json.loads(g4.read_text())
        except (OSError, ValueError):
            record = None
    if not (isinstance(record, dict) and record.get("gate") == "G4" and record.get("disposition") in ("waived", "satisfied")
            and record.get("scope") and record.get("approval")):
        blockers.append("B5-missing-g4-disposition")
    return dict(accepted_as_evidence=not blockers, blockers=blockers, counts=counts, collected=collected,
                candidate=candidate, run_head=receipt.get("git_head"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--g4", type=Path)
    parser.add_argument("--allowlist", type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--archive-sha")
    parser.add_argument("--scope", choices=("tree", "code"), default="tree")
    args = parser.parse_args(argv)
    allowlist = json.loads(args.allowlist.read_text()) if args.allowlist else []
    if args.scope == "code":
        head = json.loads((args.run / "wheel-receipt.json").read_text()).get("git_head")
        digests = (code_digest(args.repo, head), code_digest(args.repo, args.candidate))
        verdict = check(args.run, args.candidate, args.g4, allowlist, None, digests)
        verdict["scope"] = dict(mode="code", paths=list(CODE_PATHS), run_code_sha256=digests[0], candidate_code_sha256=digests[1])
    else:
        expected = args.archive_sha or archive_sha(args.repo, args.candidate)
        verdict = check(args.run, args.candidate, args.g4, allowlist, expected)
        verdict["scope"] = dict(mode="tree")
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["accepted_as_evidence"] else 1


if __name__ == "__main__":
    sys.exit(main())
