#!/usr/bin/env python3
"""Validate source documentation coverage and generate warning-clean Doxygen HTML.

Three documentation obligations are supported:

* the preserved repository-wide Python/owned-C++ coverage check and warning-free
  generation over the admitted ``Doxyfile`` (the default and ``--coverage-only``
  modes);
* a strict C++-scoped generation over the owned ``src/xverse/xcom`` inputs
  (``--strict-cpp``), which fails closed on an undocumented public declaration, a
  missing mandatory file block, or any Doxygen warning;
* the repository-owned exact-candidate evidence report
  (``--report reports/xcom-queue/t037-doxygen.json``) that records the command, the
  observed warnings, the bounded output, the resolved environment, the strict
  result, artifact hashes, and the candidate material identity.
"""

from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable
from pathlib import Path
import datetime as dt
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "src" / "xverse_xdl"
SCRIPTS_ROOT = ROOT / "scripts"
TESTS_ROOT = ROOT / "tests"
CPP_ROOT = ROOT / "src" / "xverse" / "xcom"
DOXYFILE = ROOT / "Doxyfile"
OUTPUT_ROOT = ROOT / "build" / "doxygen"
WARNING_LOG = ROOT / "build" / "doxygen-warnings.log"
STRICT_OUTPUT_ROOT = ROOT / "build" / "doxygen-strict"
STRICT_WARNING_LOG = ROOT / "build" / "doxygen-strict-warnings.log"
REPORT_PATH = ROOT / "reports" / "xcom-queue" / "t037-doxygen.json"
BASELINE_REVISION = "67e38e5974f2dd827b4d7fb902343c347341c796"

# Admitted exclusion list for the strict C++-scoped route: system and generated
# headers are out of the owned hand-written documentation scope (T037-GAP-03).
STRICT_CPP_EXCLUSIONS = ("*/build/*", "*.pb.h", "*.pb.cc", "*/generated/*")

# Candidate material retained for exact binding. The evidence report itself, the
# generated internal review, the package record, and the generated stage results
# are intentionally excluded so the digest is stable across the report write.
MATERIAL_GLOBS = (
    "src/xverse/xcom/**/*.hpp",
    "src/xverse/xcom/**/*.cpp",
    "Doxyfile",
    "scripts/check_doxygen.py",
    "docs/engineering/xcom/t037/*.md",
    "engineering/requirements/T037-*.json",
    "engineering/architecture/components/T037-*.json",
    "engineering/unit-specifications/T037-*.json",
    "engineering/validation/scenarios/T037-*.json",
    "engineering/trace/links.json",
    "engineering/project.json",
    "reports/review-index.md",
    "specs/007-xcom-core/tasks.md",
)

# The implementation record cites the report material digest and report hash, so it
# is excluded from the material inventory to keep the binding acyclic (T036
# precedent). The report, the generated review, and the package record are
# likewise excluded.
MATERIAL_EXCLUDES = ("docs/engineering/xcom/t037/implementation.md",)

# Admitted offline inputs recorded by name (never by host path) for the evidence
# environment; identities match the trusted Phase 8 runner.
ADMITTED_INPUTS = {
    "XVERSE_XCOM_TOOLCHAIN": (
        "directory", Path("/home/jefferson/.cache/xverse-xcom-grpc-prefix"),
    ),
    "XVERSE_XCOM_PACKAGE_MANIFEST": (
        "file", Path("/home/jefferson/.cache/xverse-xcom-grpc-packages/package-manifest.json"),
    ),
    "XVERSE_XCOM_T025_TEST_TOOLCHAIN": (
        "directory", Path("/home/jefferson/.cache/xverse-xcom-t025-gtest-prefix"),
    ),
}


def _python_sources(root: Path) -> tuple[Path, ...]:
    """Return repository Python sources below *root* in deterministic order."""

    return tuple(sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts))


def _owned_cpp_sources() -> tuple[Path, ...]:
    """Return the owned X-COM C++ headers, sources, and fixtures in deterministic order."""

    paths = [
        path
        for path in CPP_ROOT.rglob("*")
        if path.suffix in {".hpp", ".cpp"} and "build" not in path.parts
    ]
    return tuple(sorted(paths))


def _symbol_name(node: ast.AST, parents: tuple[str, ...]) -> str:
    """Build a readable qualified name for an AST definition node."""

    name = getattr(node, "name", "<unknown>")
    return ".".join((*parents, name))


def _missing_in_body(
    body: Iterable[ast.stmt], path: Path, parents: tuple[str, ...] = (),
) -> list[str]:
    """Find undocumented class and callable definitions recursively in an AST body."""

    missing: list[str] = []
    for node in body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            qualified = _symbol_name(node, parents)
            if ast.get_docstring(node, clean=False) is None:
                missing.append(f"{path.relative_to(ROOT)}:{node.lineno}: {qualified}")
            missing.extend(_missing_in_body(node.body, path, (*parents, node.name)))
    return missing


def find_missing_docstrings(paths: Iterable[Path]) -> tuple[str, ...]:
    """Return missing module and symbol docstrings for the supplied Python paths.

    @param paths Python files to parse.
    @return Stable, human-readable coverage errors.
    @raises SyntaxError If a source file cannot be parsed.
    """

    missing: list[str] = []
    for path in sorted(paths):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if ast.get_docstring(tree, clean=False) is None:
            missing.append(f"{path.relative_to(ROOT)}:1: <module>")
        missing.extend(_missing_in_body(tree.body, path))
    return tuple(missing)


def find_missing_file_blocks(paths: Iterable[Path]) -> tuple[str, ...]:
    """Return owned C++ files missing the mandatory Doxygen file block.

    @param paths Owned C++ headers, sources, and fixtures.
    @return Stable, human-readable coverage errors for a missing `@file`, `@brief`,
        or `@ingroup` (either the `@` or `\\` command form).
    """

    directive = {"file": re.compile(r"[@\\]file\b"), "brief": re.compile(r"[@\\]brief\b"),
                 "ingroup": re.compile(r"[@\\]ingroup\b")}
    missing: list[str] = []
    for path in sorted(paths):
        text = path.read_text(encoding="utf-8")
        for name, pattern in directive.items():
            if pattern.search(text) is None:
                missing.append(f"{path.relative_to(ROOT)}: missing mandatory file block '{name}'")
    return tuple(missing)


def _indexed_files(index_path: Path) -> set[str]:
    """Read exact repository-relative file paths from Doxygen file compounds."""

    root = ET.parse(index_path).getroot()
    indexed: set[str] = set()
    for compound in root.findall("compound[@kind='file']"):
        compound_path = index_path.parent / f"{compound.attrib['refid']}.xml"
        location = ET.parse(compound_path).find(".//compounddef/location")
        if location is not None and location.get("file"):
            indexed.add(location.get("file", ""))
    return indexed


def _indexed_python_files(index_path: Path) -> set[str]:
    """Read exact repository-relative Python paths from Doxygen file compounds."""

    return {name for name in _indexed_files(index_path) if name.endswith(".py")}


def _run(command: list[str], *, cwd: Path = ROOT, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    """Run one bounded local command and return the completed process."""

    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, timeout=timeout)


def _warning_text(log_path: Path) -> str:
    """Return the trimmed warning log text, or an empty string when absent."""

    return log_path.read_text(encoding="utf-8").strip() if log_path.exists() else ""


def _warning_count(text: str) -> int:
    """Count Doxygen warning lines (excluding continuation lines)."""

    return sum(1 for line in text.splitlines() if line.strip() and not line.startswith(" "))


def _run_doxygen() -> tuple[str, ...]:
    """Generate repository documentation and return build or coverage errors."""

    executable = shutil.which("doxygen")
    if executable is None:
        return ("doxygen executable was not found on PATH",)
    WARNING_LOG.parent.mkdir(parents=True, exist_ok=True)
    WARNING_LOG.unlink(missing_ok=True)
    index = OUTPUT_ROOT / "html" / "index.html"
    xml_index = OUTPUT_ROOT / "xml" / "index.xml"
    index.unlink(missing_ok=True)
    xml_index.unlink(missing_ok=True)
    completed = subprocess.run(
        (executable, str(DOXYFILE)), cwd=ROOT, text=True, capture_output=True, check=False,
    )
    errors: list[str] = []
    if completed.returncode:
        details = (completed.stderr or completed.stdout).strip()
        errors.append(f"doxygen exited with {completed.returncode}: {details}")
    warnings = _warning_text(WARNING_LOG)
    if warnings:
        errors.append(f"Doxygen reported warnings:\n{warnings}")
    if not index.is_file():
        errors.append(f"missing generated HTML index: {index.relative_to(ROOT)}")
    if not xml_index.is_file():
        errors.append(f"missing generated XML index: {xml_index.relative_to(ROOT)}")
    elif not errors:
        indexed = _indexed_python_files(xml_index)
        expected = {
            path.relative_to(ROOT).as_posix()
            for root in (PACKAGE_ROOT, SCRIPTS_ROOT, TESTS_ROOT)
            for path in _python_sources(root)
        }
        absent = sorted(expected - indexed)
        if absent:
            errors.append("Doxygen XML omits Python source paths: " + ", ".join(absent))
    return tuple(errors)


STRICT_CPP_OVERRIDES = {
    "INPUT": "src/xverse/xcom",
    "FILE_PATTERNS": "*.hpp *.cpp",
    "EXTRACT_ALL": "NO",
    "EXTRACT_PRIVATE": "NO",
    "EXTRACT_STATIC": "NO",
    "WARNINGS": "YES",
    "WARN_IF_UNDOCUMENTED": "YES",
    "WARN_IF_DOC_ERROR": "YES",
    "WARN_NO_PARAMDOC": "YES",
    "WARN_AS_ERROR": "YES",
    "GENERATE_HTML": "YES",
    "GENERATE_XML": "YES",
    "EXCLUDE_PATTERNS": " ".join(STRICT_CPP_EXCLUSIONS),
}


def _strict_configuration(path: Path, output: Path, warning_log: Path) -> Path:
    """Write the strict C++-scoped Doxygen configuration derived from the Doxyfile."""

    overrides = {
        **STRICT_CPP_OVERRIDES,
        "OUTPUT_DIRECTORY": output.as_posix(),
        "WARN_LOGFILE": warning_log.as_posix(),
        "QUIET": "YES",
    }
    body = DOXYFILE.read_text(encoding="utf-8")
    path.write_text(
        body + "\n" + "".join(f"{key} = {value}\n" for key, value in overrides.items()),
        encoding="utf-8",
    )
    return path


def _run_strict_cpp() -> dict[str, object]:
    """Run the strict C++-scoped generation and return the observed result."""

    executable = shutil.which("doxygen")
    gaps = list(find_missing_file_blocks(_owned_cpp_sources()))
    result: dict[str, object] = {
        "scope": "src/xverse/xcom",
        "exclusions": list(STRICT_CPP_EXCLUSIONS),
        "extract_all": False,
        "extract_private": False,
        "extract_static": False,
        "warn_if_undocumented": True,
        "warn_no_paramdoc": True,
        "coverage_gaps": gaps,
        "coverage_gap_count": len(gaps),
        "warning_count": 0,
        "warnings": "",
        "exit_code": 1,
        "indexed_files": 0,
        "html_index": "build/doxygen-strict/html/index.html",
        "xml_index": "build/doxygen-strict/xml/index.xml",
    }
    if executable is None:
        result["error"] = "doxygen executable was not found on PATH"
        return result
    STRICT_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    STRICT_WARNING_LOG.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="doxygen-strict-", dir=ROOT / "build") as temporary:
        config = _strict_configuration(Path(temporary) / "Doxyfile", STRICT_OUTPUT_ROOT,
                                       STRICT_WARNING_LOG)
        completed = _run([executable, str(config)])
    warnings = _warning_text(STRICT_WARNING_LOG)
    result["exit_code"] = completed.returncode
    result["warnings"] = warnings
    result["warning_count"] = _warning_count(warnings)
    html_index = STRICT_OUTPUT_ROOT / "html" / "index.html"
    xml_index = STRICT_OUTPUT_ROOT / "xml" / "index.xml"
    if xml_index.is_file():
        result["indexed_files"] = len(_indexed_files(xml_index))
    result["html_index_present"] = html_index.is_file()
    result["xml_index_present"] = xml_index.is_file()
    return result


def _run_repository_route() -> dict[str, object]:
    """Run the repository-wide warning-as-error generation and return the result."""

    executable = shutil.which("doxygen")
    output = ROOT / "build" / "doxygen-repository"
    log = ROOT / "build" / "doxygen-repository-warnings.log"
    result: dict[str, object] = {
        "command": "doxygen Doxyfile",
        "exit_code": 1,
        "warning_count": 0,
        "warnings": "",
        "html_index": "build/doxygen-repository/html/index.html",
        "xml_index": "build/doxygen-repository/xml/index.xml",
        "indexed_files": 0,
    }
    if executable is None:
        result["error"] = "doxygen executable was not found on PATH"
        return result
    output.mkdir(parents=True, exist_ok=True)
    log.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="doxygen-repository-", dir=ROOT / "build") as temporary:
        config = Path(temporary) / "Doxyfile"
        config.write_text(
            DOXYFILE.read_text(encoding="utf-8")
            + f"\nOUTPUT_DIRECTORY = {output.as_posix()}\nWARN_AS_ERROR = YES\nQUIET = YES\n"
            + f"WARN_LOGFILE = {log.as_posix()}\n",
            encoding="utf-8",
        )
        completed = _run([executable, str(config)])
    warnings = _warning_text(log)
    result["exit_code"] = completed.returncode
    result["warnings"] = warnings
    result["warning_count"] = _warning_count(warnings)
    html_index = output / "html" / "index.html"
    xml_index = output / "xml" / "index.xml"
    result["html_index_present"] = html_index.is_file()
    result["xml_index_present"] = xml_index.is_file()
    if xml_index.is_file():
        result["indexed_files"] = len(_indexed_files(xml_index))
    return result


def _self_test() -> tuple[str, ...]:
    """Verify that the coverage gate rejects an undocumented synthetic symbol."""

    (ROOT / "build").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="doxygen-self-test-", dir=ROOT / "build") as temporary:
        fixture = Path(temporary) / "undocumented.py"
        fixture.write_text("def missing(value):\n    return value\n", encoding="utf-8")
        failures = find_missing_docstrings((fixture,))
        block_fixture = Path(temporary) / "undocumented.hpp"
        block_fixture.write_text("int undocumented();\n", encoding="utf-8")
        block_failures = find_missing_file_blocks((block_fixture,))
    expected = ("<module>", "missing")
    absent = tuple(name for name in expected if not any(name in failure for failure in failures))
    problems = [] if not absent else ["coverage self-test did not detect: " + ", ".join(absent)]
    block_absent = tuple(
        name for name in ("file", "brief", "ingroup")
        if not any(name in failure for failure in block_failures)
    )
    if block_absent:
        problems.append("file-block self-test did not detect: " + ", ".join(block_absent))
    return tuple(problems)


def _sha256_bytes(payload: bytes) -> str:
    """Return the lowercase-hex SHA-256 of *payload*."""

    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    """Return the lowercase-hex SHA-256 of a file."""

    return _sha256_bytes(path.read_bytes())


def _material_inputs() -> list[str]:
    """Return the sorted repository-relative candidate material inventory."""

    paths: set[str] = set()
    for pattern in MATERIAL_GLOBS:
        for path in ROOT.glob(pattern):
            if path.is_file():
                relative = path.relative_to(ROOT).as_posix()
                if relative not in MATERIAL_EXCLUDES:
                    paths.add(relative)
    return sorted(paths)


def _material_identity() -> dict[str, object]:
    """Return the exact-candidate material inventory, digest, and per-file hashes."""

    inputs = _material_inputs()
    lines = "".join(f"{name}\0{_sha256_file(ROOT / name)}\n" for name in inputs)
    return {
        "candidate_kind": (
            "working-tree successor of the accepted baseline, measured with HEAD == "
            "baseline_revision and committed as the direct child of baseline_revision that "
            "carries this exact material digest"
        ),
        "revision_binding": (
            "a committed report cannot reference its own commit hash, so the exact candidate is "
            "bound by baseline_revision plus the sorted material-input inventory, the material "
            "digest, and the per-file hashes"
        ),
        "baseline_revision": BASELINE_REVISION,
        "candidate_revision": None,
        "material_digest": _sha256_bytes(lines.encode("utf-8")),
        "material_input_digest_method": (
            "sha256 over sorted '<relative path>\\0<file sha256>\\n' for each candidate "
            "material input"
        ),
        "material_inputs": inputs,
    }


def _admitted_input_identity(name: str, kind: str, path: Path) -> dict[str, object]:
    """Return the name-bound identity (kind, digest, file count) of an admitted input."""

    if kind == "file":
        available = path.is_file()
        return {
            "kind": kind,
            "available": available,
            "sha256": _sha256_file(path) if available else None,
            "files": 1 if available else 0,
        }
    if not path.is_dir():
        return {"kind": kind, "available": False, "sha256": None, "files": 0}
    digest = hashlib.sha256()
    count = 0
    for candidate in sorted(path.rglob("*")):
        if candidate.is_file():
            digest.update(candidate.relative_to(path).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(_sha256_file(candidate).encode("ascii"))
            digest.update(b"\n")
            count += 1
    return {"kind": kind, "available": True, "sha256": digest.hexdigest(), "files": count}


def _tool_version(argv: list[str]) -> str | None:
    """Return a bounded first-line version identity for a local tool, or None."""

    executable = shutil.which(argv[0])
    if executable is None:
        return None
    try:
        completed = _run([executable, *argv[1:]], timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    text = (completed.stdout or completed.stderr).strip().splitlines()
    return text[0] if text else None


def _environment() -> dict[str, object]:
    """Return the resolved public-safe documentation environment identity."""

    return {
        "doxygen": _tool_version(["doxygen", "--version"]),
        "compiler": _tool_version(["g++", "--version"]),
        "cxx_standard": "c++20",
        "cmake": _tool_version(["cmake", "--version"]),
        "ninja": _tool_version(["ninja", "--version"]),
        "python": platform.python_version(),
        "target": f"{platform.system().lower()}-{platform.machine()}",
        "admitted_inputs": {
            name: _admitted_input_identity(name, kind, path)
            for name, (kind, path) in ADMITTED_INPUTS.items()
        },
    }


def _write_report() -> tuple[dict[str, object], bool]:
    """Run both routes and write the repository-owned evidence report."""

    repository = _run_repository_route()
    strict = _run_strict_cpp()
    warnings_text = "\n".join(
        text for text in (str(repository["warnings"]), str(strict["warnings"])) if text
    )
    warnings_count = int(repository["warning_count"]) + int(strict["warning_count"])
    passing = (
        int(repository["exit_code"]) == 0
        and bool(repository["html_index_present"])
        and bool(repository["xml_index_present"])
        and int(strict["exit_code"]) == 0
        and int(strict["warning_count"]) == 0
        and int(strict["coverage_gap_count"]) == 0
        and bool(strict["html_index_present"])
        and bool(strict["xml_index_present"])
    )
    identity = _material_identity()
    report: dict[str, object] = {
        "schema_version": 1,
        "task_id": "T037",
        "capability": "007",
        "baseline_revision": BASELINE_REVISION,
        "candidate_revision": None,
        "candidate_identity": identity,
        "command": {
            "repository_route": "doxygen Doxyfile (WARN_AS_ERROR = YES)",
            "strict_cpp_route": "python3 scripts/check_doxygen.py --strict-cpp",
            "report_route": "python3 scripts/check_doxygen.py --report "
            "reports/xcom-queue/t037-doxygen.json",
            "resolved_argv": ["doxygen", "Doxyfile"],
        },
        "warnings": {"count": warnings_count, "log": warnings_text},
        "output": {
            "repository_exit_code": repository["exit_code"],
            "strict_cpp_exit_code": strict["exit_code"],
            "repository_indexed_files": repository["indexed_files"],
            "strict_cpp_indexed_files": strict["indexed_files"],
            "html_index": repository["html_index"],
            "xml_index": repository["xml_index"],
            "strict_html_index": strict["html_index"],
            "strict_xml_index": strict["xml_index"],
            "bounded_stdout": (
                f"repository route exit={repository['exit_code']} "
                f"warnings={repository['warning_count']}; strict C++ route "
                f"exit={strict['exit_code']} warnings={strict['warning_count']} "
                f"coverage_gaps={strict['coverage_gap_count']}"
            ),
        },
        "environment": _environment(),
        "strict_cpp": {
            "scope": strict["scope"],
            "exclusions": strict["exclusions"],
            "extract_all": strict["extract_all"],
            "extract_private": strict["extract_private"],
            "extract_static": strict["extract_static"],
            "warn_if_undocumented": strict["warn_if_undocumented"],
            "warn_no_paramdoc": strict["warn_no_paramdoc"],
            "warning_count": strict["warning_count"],
            "coverage_gap_count": strict["coverage_gap_count"],
            "coverage_gaps": strict["coverage_gaps"],
        },
        "hashes": {name: _sha256_file(ROOT / name) for name in identity["material_inputs"]},
        "limitations": [
            "documentation-only prototype evidence; not a production-readiness, compatibility, "
            "or deployed-service claim",
            "the strict declaration-level route is scoped to the owned src/xverse/xcom C++ inputs; "
            "the repository-wide route keeps WARN_IF_UNDOCUMENTED=NO and WARN_NO_PARAMDOC=NO "
            "because its inputs include out-of-scope Python and test sources (T037-GAP-02)",
            "generated protobuf C++ provenance and system/third-party headers remain out of the "
            "owned documentation scope and are deferred to the admitted exclusion list "
            "(T037-GAP-03)",
            "the inherited Python docstring coverage findings in scripts/ and src/xverse_xdl/ are "
            "preserved as a limitation and are not reported as passing (T037-OPEN-06)",
            "no T038 traceability-verifier/SADS, T039/T040 review, or T041 user acceptance result "
            "is produced or claimed",
        ],
        "blockers": [],
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report, passing


def main(arguments: list[str] | None = None) -> int:
    """Run coverage checks and, unless requested otherwise, build Doxygen output.

    @param arguments Optional command-line arguments for tests and embedding.
    @return Zero on complete warning-free documentation; one otherwise.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--coverage-only", action="store_true", help="check docstrings without invoking Doxygen",
    )
    parser.add_argument(
        "--self-test", action="store_true", help="prove the coverage gate rejects missing docstrings",
    )
    parser.add_argument(
        "--strict-cpp", action="store_true",
        help="run the strict C++-scoped zero-warning generation over src/xverse/xcom",
    )
    parser.add_argument(
        "--report", metavar="PATH", nargs="?", const=str(REPORT_PATH),
        help="run both routes and write the exact-candidate evidence report",
    )
    args = parser.parse_args(arguments)

    if args.report is not None:
        report, passing = _write_report()
        print(f"evidence report: {Path(args.report).relative_to(ROOT) if Path(args.report).is_absolute() else args.report}")
        print(
            f"repository route exit={report['output']['repository_exit_code']} "
            f"warnings={report['warnings']['count']}; strict C++ coverage gaps="
            f"{report['strict_cpp']['coverage_gap_count']}"
        )
        return 0 if passing else 1

    if args.strict_cpp:
        strict = _run_strict_cpp()
        if strict.get("error"):
            print(f"documentation validation failed: {strict['error']}", file=sys.stderr)
            return 1
        if strict["coverage_gap_count"]:
            print("documentation validation failed:", file=sys.stderr)
            for gap in strict["coverage_gaps"]:
                print(f"- {gap}", file=sys.stderr)
            return 1
        if strict["exit_code"] or strict["warning_count"]:
            print("strict C++ Doxygen generation is not warning-free:", file=sys.stderr)
            print(strict["warnings"], file=sys.stderr)
            return 1
        print(
            f"strict C++ documentation passed: {strict['indexed_files']} indexed files, "
            f"0 warnings, 0 coverage gaps"
        )
        return 0

    production_paths = (*_python_sources(PACKAGE_ROOT), *_python_sources(SCRIPTS_ROOT))
    errors = list(find_missing_docstrings(production_paths))
    if args.self_test:
        errors.extend(_self_test())
    if not args.coverage_only and not errors:
        errors.extend(_run_doxygen())
    if errors:
        print("documentation validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    source_count = sum(
        len(_python_sources(root)) for root in (PACKAGE_ROOT, SCRIPTS_ROOT, TESTS_ROOT)
    )
    print(f"documentation validation passed: {len(production_paths)} covered files")
    if args.self_test:
        print("coverage self-test passed: undocumented module and function rejected")
    if not args.coverage_only:
        print(f"Doxygen indexed {source_count} Python source files")
        print(f"HTML index: {(OUTPUT_ROOT / 'html' / 'index.html').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
