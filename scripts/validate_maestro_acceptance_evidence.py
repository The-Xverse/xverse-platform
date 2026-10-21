#!/usr/bin/env python3
"""DV12 acceptance-evidence gate for Maestro Lite full runs (increment19, finding 456).

Reads one full-run directory written by verify-platform-regression-20261021t.py (or a successor
with the same receipt fields) and decides whether it may be presented as acceptance evidence for
an expected candidate commit. Every blocker is reported; the gate never repairs or reruns.

Usage: validate_maestro_acceptance_evidence.py <run-dir> --candidate <commit> --g4 <file>
       [--allowlist <file>] [--repo <path>] [--archive-sha <hex>] [--scope tree|code]

Staleness (B4): --scope tree (default) requires the run's archive to equal the candidate's whole
git archive; --scope code (findings 463, 474; authoritative by author decision B4, finding 468)
instead requires equal test-relevant content between the run's head and the candidate: every
tracked path except NON_TEST_INPUTS (evidence folders and review logs, which no test reads), so
evidence and review-log commits after the run do not block while any change to a file a test can
read does. Identity is the content-addressed `git ls-tree -r` listing (modes, blob ids, paths)
filtered by in_code_scope, because archive bytes also carry the commit id and time. In code scope
the run's archive_sha256 must still equal the git archive of its own head.
Log binding (finding 474): sha256(wheel.log) must equal the receipt's log_sha256.

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

NON_TEST_INPUTS = ("docs/engineering/maestro-lite/evidence/",)
NON_TEST_LOGS = ("docs/engineering/maestro-lite/review-",)


def in_code_scope(path: str) -> bool:
    """True for every tracked path a test may read (finding 474)."""
    if any(path.startswith(prefix) for prefix in NON_TEST_INPUTS):
        return False
    return not any(path.startswith(prefix) and path.endswith(".md") and "/" not in path[len(prefix):]
                   for prefix in NON_TEST_LOGS)
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


def reported_count(lines: list) -> int:
    """-ra folds identical skips into one "SKIPPED [N] ..." line (finding 474 item 6)."""
    total = 0
    for line in lines:
        grouped = re.match(r"SKIPPED \[(\d+)\] ", line)
        total += int(grouped.group(1)) if grouped else 1
    return total


def archive_sha(repo: Path, commit: str) -> str:
    digest = hashlib.sha256()
    with subprocess.Popen(["git", "archive", commit], cwd=repo, stdout=subprocess.PIPE) as process:
        for chunk in iter(lambda: process.stdout.read(1 << 20), b""):
            digest.update(chunk)
    if process.returncode:
        raise SystemExit("git archive failed for " + commit)
    return digest.hexdigest()


def code_digest(repo: Path, commit: str) -> str:
    listing = subprocess.check_output(["git", "ls-tree", "-r", "-z", commit], cwd=repo)
    kept = [row for row in listing.split(b"\0") if row and in_code_scope(row.split(b"\t", 1)[1].decode())]
    return hashlib.sha256(b"\0".join(kept)).hexdigest()


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
    if receipt.get("log_sha256") != hashlib.sha256((run / "wheel.log").read_bytes()).hexdigest():
        blockers.append("B2-log-unbound: wheel.log does not match the receipt's log_sha256")
    if receipt.get("returncode") != 0 or counts.get("failed") or counts.get("errors"):
        blockers.append(f"B2-failures: returncode {receipt.get('returncode')}, failed {counts.get('failed', 0)}, errors {counts.get('errors', 0)}")
    if receipt.get("outer_timeout"):
        blockers.append("B2-outer-timeout")
    for kind in ("skipped", "xfailed"):
        listed = [line for line in outcome_lines(log, kind)
                  if not any(entry.get("kind") == kind and entry.get("match") and entry["match"] in line
                             and entry.get("reason") and entry.get("approval") for entry in allowlist)]
        reported = reported_count(outcome_lines(log, kind))
        if counts.get(kind, 0) and reported < counts[kind]:
            blockers.append(f"B3-{kind}-unlisted: {counts[kind]} counted, {reported} reported with -ra")
        blockers.extend(f"B3-{kind}-unlisted: {line[:200]}" for line in listed)
    if counts.get("xpassed"):
        blockers.append(f"B3-xpassed: {counts['xpassed']}")
    if code_digests is not None:
        if receipt.get("git_head") != configuration.get("git_head") or code_digests[0] != code_digests[1]:
            blockers.append(f"B4-code-mismatch: run {receipt.get('git_head')} code differs from candidate {candidate}")
    elif receipt.get("git_head") != candidate or configuration.get("git_head") != candidate:
        blockers.append(f"B4-stale-head: run {receipt.get('git_head')} vs candidate {candidate}")
    if expected_archive is not None and (receipt.get("archive_sha256") != expected_archive
                                         or configuration.get("archive_sha256") != expected_archive):
        blockers.append("B4-archive-mismatch: run archive is not the git archive of "
                        + ("its own head" if code_digests is not None else "the candidate"))
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
        verdict = check(args.run, args.candidate, args.g4, allowlist, archive_sha(args.repo, head), digests)
        verdict["scope"] = dict(mode="code", excluded=[*NON_TEST_INPUTS, *(p + "*.md" for p in NON_TEST_LOGS)],
                                run_code_sha256=digests[0], candidate_code_sha256=digests[1])
    else:
        expected = args.archive_sha or archive_sha(args.repo, args.candidate)
        verdict = check(args.run, args.candidate, args.g4, allowlist, expected)
        verdict["scope"] = dict(mode="tree")
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["accepted_as_evidence"] else 1


if __name__ == "__main__":
    sys.exit(main())
