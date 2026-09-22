#!/usr/bin/env python3
"""Validate source documentation coverage and generate warning-clean Doxygen HTML."""

from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "src" / "xverse_xdl"
SCRIPTS_ROOT = ROOT / "scripts"
TESTS_ROOT = ROOT / "tests"
DOXYFILE = ROOT / "Doxyfile"
OUTPUT_ROOT = ROOT / "build" / "doxygen"
WARNING_LOG = ROOT / "build" / "doxygen-warnings.log"


def _python_sources(root: Path) -> tuple[Path, ...]:
    """Return repository Python sources below *root* in deterministic order."""

    return tuple(sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts))


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


def _indexed_python_files(index_path: Path) -> set[str]:
    """Read exact repository-relative Python paths from Doxygen file compounds."""

    root = ET.parse(index_path).getroot()
    indexed: set[str] = set()
    for compound in root.findall("compound[@kind='file']"):
        name = compound.findtext("name") or ""
        if not name.endswith(".py"):
            continue
        compound_path = index_path.parent / f"{compound.attrib['refid']}.xml"
        location = ET.parse(compound_path).find(".//compounddef/location")
        if location is not None and location.get("file"):
            indexed.add(Path(location.get("file", "")).as_posix())
    return indexed


def _run_doxygen() -> tuple[str, ...]:
    """Generate documentation and return build or coverage errors."""

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
    warnings = WARNING_LOG.read_text(encoding="utf-8").strip() if WARNING_LOG.exists() else ""
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


def _self_test() -> tuple[str, ...]:
    """Verify that the coverage gate rejects an undocumented synthetic symbol."""

    (ROOT / "build").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="doxygen-self-test-", dir=ROOT / "build") as temporary:
        fixture = Path(temporary) / "undocumented.py"
        fixture.write_text("def missing(value):\n    return value\n", encoding="utf-8")
        failures = find_missing_docstrings((fixture,))
    expected = ("<module>", "missing")
    absent = tuple(name for name in expected if not any(name in failure for failure in failures))
    return (() if not absent else ("coverage self-test did not detect: " + ", ".join(absent),))


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
    args = parser.parse_args(arguments)
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
