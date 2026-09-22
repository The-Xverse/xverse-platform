#!/usr/bin/env python3
"""Validate the bounded capability-007 X-COM core-types slice offline."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import NoReturn

ROOT = Path(__file__).resolve().parents[1]
CPP_ROOT = ROOT / "src" / "xverse" / "xcom"
TEST_ROOT = ROOT / "tests" / "xcom" / "core_types"
TRACEABILITY = ROOT / "docs" / "xcom" / "core-types-traceability.json"
CANDIDATE_REVISION_ENV = "SESN_CANDIDATE_REVISION"
CANDIDATE_REVISION_BINDING = {
    "environment_variable": CANDIDATE_REVISION_ENV,
    "format": "full-lowercase-git-sha",
    "workspace_comparison": "git rev-parse HEAD",
}
REQUIREMENTS = {f"XCOM-TYPE-{number:03d}" for number in range(1, 9)}
MEASURES = {
    "VM-XCOM-TYPES-UNIT",
    "VM-XCOM-TYPES-LINT",
    "VM-XCOM-TYPES-STATIC",
    "VM-XCOM-TYPES-INTEGRATION",
    "VM-XCOM-TYPES-VALIDATION",
}
OWNED_PREFIXES = ("src/xverse/xcom/", "tests/xcom/core_types/")
OWNED_FILES = {
    "Doxyfile",
    "scripts/validate_xcom_core_types.py",
    "docs/xcom/core-types.md",
    "docs/xcom/core-types-traceability.json",
}
CORE_PRODUCTION = tuple(
    CPP_ROOT / relative
    for relative in (
        "include/xverse/xcom/contract.hpp",
        "include/xverse/xcom/core_types.hpp",
        "include/xverse/xcom/diagnostic.hpp",
        "include/xverse/xcom/item.hpp",
        "include/xverse/xcom/result.hpp",
        "include/xverse/xcom/value.hpp",
        "src/contract.cpp",
        "src/diagnostic.cpp",
        "src/item.cpp",
        "src/value.cpp",
    )
)
ACCEPTED_EXTENSION_PRODUCTION = tuple(
    CPP_ROOT / relative
    for relative in (
        "include/xverse/xcom/endpoint_route_lifecycle.hpp",
        "include/xverse/xcom/loopback_provider.hpp",
        "include/xverse/xcom/provider.hpp",
        "src/endpoint_route_lifecycle.cpp",
        "src/loopback_provider.cpp",
        "src/provider.cpp",
    )
)
DOCUMENTATION_CLAUSES = ("@file", "@ownership", "@lifetime", "@thread_safety", "@failure")
DESIGN_REQUIREMENTS = {
    "XCOM-TYPE-UNIT-001": {"XCOM-TYPE-001", "XCOM-TYPE-002", "XCOM-TYPE-003"},
    "XCOM-TYPE-UNIT-002": {"XCOM-TYPE-002", "XCOM-TYPE-003"},
    "XCOM-TYPE-UNIT-003": {"XCOM-TYPE-004"},
    "XCOM-TYPE-UNIT-004": {"XCOM-TYPE-003", "XCOM-TYPE-004", "XCOM-TYPE-005"},
    "XCOM-CORE-TYPES": {"XCOM-TYPE-006", "XCOM-TYPE-007", "XCOM-TYPE-008"},
}
DESIGN_SOURCES = {
    design: (
        "specs/012-feat-86b0e3ad8eeb4b12/unit-specifications.md"
        if design.startswith("XCOM-TYPE-UNIT-")
        else "specs/012-feat-86b0e3ad8eeb4b12/detailed-design.md"
    )
    for design in DESIGN_REQUIREMENTS
}
REPOSITORY_DOXYGEN_SETTINGS = {
    "EXTRACT_ALL": "YES",
    "EXTRACT_PRIVATE": "YES",
    "EXTRACT_STATIC": "YES",
    "WARNINGS": "YES",
    "WARN_IF_UNDOCUMENTED": "NO",
    "WARN_IF_DOC_ERROR": "YES",
    "WARN_NO_PARAMDOC": "NO",
    "WARN_AS_ERROR": "YES",
    "GENERATE_HTML": "YES",
    "GENERATE_XML": "YES",
}
STRICT_CPP_DOXYGEN_SETTINGS = {
    "EXTRACT_ALL": "NO",
    "EXTRACT_PRIVATE": "NO",
    "EXTRACT_PRIV_VIRTUAL": "YES",
    "WARN_IF_UNDOCUMENTED": "YES",
    "WARN_NO_PARAMDOC": "YES",
}


class ValidationFailure(RuntimeError):
    """Represent one deterministic validation-gate failure."""


def _fail(message: str) -> NoReturn:
    """Raise a gate failure with a concise message.

    @param message Human-readable failure detail.
    @raises ValidationFailure Always.
    """

    raise ValidationFailure(message)


def _run(
    argv: list[str], *, cwd: Path = ROOT, environment: dict[str, str] | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    """Run one bounded local command and return captured output.

    @param argv Exact argument vector; shell interpretation is never used.
    @param cwd Explicit working directory.
    @param environment Optional complete subprocess environment.
    @param timeout Maximum command duration in seconds.
    @return The successful completed process.
    @raises ValidationFailure If the command is missing, times out, or returns nonzero.
    """

    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        _fail(f"command could not complete: {argv!r}: {error}")
    if completed.returncode:
        _fail(
            f"command failed ({completed.returncode}): {argv!r}\n{completed.stdout.rstrip()}"
        )
    return completed


def _tool(name: str) -> str:
    """Resolve one required ambient host build tool.

    @param name Executable basename.
    @return Absolute executable path.
    @raises ValidationFailure If the executable is unavailable.
    """

    path = shutil.which(name)
    if path is None:
        _fail(f"required executable is unavailable: {name}")
    return path


def _candidate_revision() -> str:
    """Return the validated candidate revision supplied by the SESN host.

    @return Full lowercase Git SHA equal to the workspace HEAD.
    @raises ValidationFailure If the value is missing, malformed, or mismatched.
    """

    revision = os.environ.get(CANDIDATE_REVISION_ENV)
    if not revision:
        _fail(f"{CANDIDATE_REVISION_ENV} is unset")
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        _fail(f"{CANDIDATE_REVISION_ENV} must be a full lowercase Git SHA")
    head = _run([_tool("git"), "rev-parse", "HEAD"]).stdout.strip()
    if revision != head:
        _fail(
            f"{CANDIDATE_REVISION_ENV} {revision} differs from workspace HEAD {head}"
        )
    return revision


def _admitted_clang_tidy() -> str:
    """Resolve clang-tidy strictly below the explicit admitted prefix.

    @return Absolute admitted clang-tidy path.
    @raises ValidationFailure If the explicit prefix or executable is missing.
    """

    prefix = os.environ.get("XVERSE_XCOM_TOOLCHAIN", "")
    if not prefix:
        _fail("XVERSE_XCOM_TOOLCHAIN is unset")
    candidate = Path(prefix).resolve() / "usr" / "bin" / "clang-tidy"
    if not candidate.is_file() or not os.access(candidate, os.X_OK):
        _fail(f"admitted clang-tidy is unavailable: {candidate}")
    return str(candidate)


def _configure(build: Path) -> None:
    """Configure one disposable C++20 Ninja build with compile commands.

    @param build Empty or reusable disposable build directory.
    @raises ValidationFailure If the admitted root configuration fails.
    """

    _run(
        [
            _tool("cmake"),
            "-S",
            str(ROOT),
            "-B",
            str(build),
            "-G",
            "Ninja",
            "-DBUILD_TESTING=ON",
            "-DCMAKE_BUILD_TYPE=Debug",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        ]
    )


def _build(build: Path, targets: list[str]) -> None:
    """Build named warning-as-error targets in a configured tree.

    @param build Configured build directory.
    @param targets Exact target names.
    @raises ValidationFailure If compilation fails.
    """

    _run([_tool("cmake"), "--build", str(build), "--target", *targets, "--verbose"])


def _ctest(build: Path, expression: str) -> None:
    """Run the selected CTest fixtures.

    @param build Configured build directory.
    @param expression Anchored CTest name expression.
    @raises ValidationFailure If no selected test passes or a test fails.
    """

    _run(
        [
            _tool("ctest"),
            "--test-dir",
            str(build),
            "--output-on-failure",
            "-R",
            expression,
        ]
    )


def _cpp_files() -> tuple[Path, ...]:
    """Return every owned C++ header and source in stable order.

    @return Repository C++ paths across production and fixtures.
    """

    return tuple(
        sorted(
            (*CPP_ROOT.rglob("*.hpp"), *CPP_ROOT.rglob("*.cpp"), *TEST_ROOT.rglob("*.cpp"))
        )
    )


def _normalize_additive_owned_paths(values: list[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Validate explicit later-slice paths admitted only by the ownership gate.

    @param values Repository-relative files or directories supplied by an integrating validator.
    @return Exact file names and normalized directory prefixes.
    @raises ValidationFailure If a path is absolute, missing, broad, or escapes the repository.
    """

    files: list[str] = []
    prefixes: list[str] = []
    for value in values:
        candidate = Path(value)
        if candidate.is_absolute() or value in {"", "."} or ".." in candidate.parts:
            _fail(f"invalid additive owned path: {value!r}")
        resolved = (ROOT / candidate).resolve()
        try:
            relative = resolved.relative_to(ROOT).as_posix()
        except ValueError:
            _fail(f"additive owned path escapes repository: {value!r}")
        if not resolved.exists():
            _fail(f"additive owned path does not exist: {relative}")
        if resolved.is_dir():
            if relative == "src/xverse/xcom" or relative.startswith("src/xverse/xcom/"):
                _fail(
                    "additive production ownership must name exact files, not a directory: "
                    + relative
                )
            prefixes.append(relative.rstrip("/") + "/")
        elif resolved.is_file():
            files.append(relative)
        else:
            _fail(f"additive owned path is not a file or directory: {relative}")
    return tuple(sorted(set(files))), tuple(sorted(set(prefixes)))


def _check_owned_paths(additive_owned_paths: list[str]) -> None:
    """Reject candidate changes outside the task's explicit ownership boundary.

    @raises ValidationFailure If tracked or untracked changed paths are outside ownership.
    """

    tracked = _run([_tool("git"), "diff", "--name-only", "--", "."]).stdout.splitlines()
    untracked = _run(
        [_tool("git"), "ls-files", "--others", "--exclude-standard"]
    ).stdout.splitlines()
    additive_files, additive_prefixes = _normalize_additive_owned_paths(additive_owned_paths)
    unexpected = sorted(
        path
        for path in set((*tracked, *untracked))
        if path not in OWNED_FILES
        and path not in additive_files
        and not path.startswith((*OWNED_PREFIXES, *additive_prefixes))
    )
    if unexpected:
        _fail("changed paths exceed task ownership: " + ", ".join(unexpected))


def _check_layout_and_format() -> None:
    """Enforce the exact bounded layout and basic deterministic text policy.

    @raises ValidationFailure If a required file is missing or text formatting differs.
    """

    required = {
        *OWNED_FILES,
        "src/xverse/xcom/CMakeLists.txt",
        "src/xverse/xcom/include/xverse/xcom/contract.hpp",
        "src/xverse/xcom/include/xverse/xcom/core_types.hpp",
        "src/xverse/xcom/include/xverse/xcom/diagnostic.hpp",
        "src/xverse/xcom/include/xverse/xcom/item.hpp",
        "src/xverse/xcom/include/xverse/xcom/result.hpp",
        "src/xverse/xcom/include/xverse/xcom/value.hpp",
        "src/xverse/xcom/src/contract.cpp",
        "src/xverse/xcom/src/diagnostic.cpp",
        "src/xverse/xcom/src/item.cpp",
        "src/xverse/xcom/src/value.cpp",
        "tests/xcom/core_types/unit_tests.cpp",
        "tests/xcom/core_types/negative_tests.cpp",
        "tests/xcom/core_types/consumer/main.cpp",
    }
    missing = sorted(path for path in required if not (ROOT / path).is_file())
    if missing:
        _fail("required core-types artifacts are missing: " + ", ".join(missing))
    text_paths = [ROOT / path for path in required]
    for path in sorted(text_paths):
        text = path.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            _fail(f"text file lacks terminal newline: {path.relative_to(ROOT)}")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.rstrip() != line:
                _fail(f"trailing whitespace: {path.relative_to(ROOT)}:{line_number}")
            if "\t" in line and path.suffix in {".cpp", ".hpp", ".py", ".md"}:
                _fail(f"tab violates formatting policy: {path.relative_to(ROOT)}:{line_number}")


def _check_forbidden_cpp_apis() -> None:
    """Reject ambient I/O, execution, discovery, and excluded subsystem APIs.

    @raises ValidationFailure If production C++ contains a forbidden include or call.
    """

    patterns = {
        r"#\s*include\s*[<\"](?:filesystem|fstream|cstdio|cstdlib)": "ambient I/O/process header",
        r"\b(?:std::filesystem|std::fstream|std::ifstream|std::ofstream)\b": "filesystem API",
        r"\b(?:getenv|system|popen|fork|exec[a-z]*|socket|connect|listen|accept)\s*\(": "ambient/process/network API",
        r"#\s*include\s*[<\"](?:grpc|google/protobuf|nlohmann)": "excluded external dependency",
        r"#\s*include\s*<cctype>|\bstd::is(?:alnum|alpha|blank|cntrl|digit|graph|lower|print|punct|space|upper|xdigit)\s*\(": "locale-sensitive character classification",
    }
    production = tuple(sorted((*CPP_ROOT.rglob("*.hpp"), *CPP_ROOT.rglob("*.cpp"))))
    unaccounted = sorted(
        path.relative_to(ROOT).as_posix()
        for path in production
        if path not in CORE_PRODUCTION and path not in ACCEPTED_EXTENSION_PRODUCTION
    )
    if unaccounted:
        _fail("unadmitted production unit present: " + ", ".join(unaccounted))
    for path in production:
        text = path.read_text(encoding="utf-8")
        for pattern, label in patterns.items():
            if re.search(pattern, text):
                _fail(f"{label} found in {path.relative_to(ROOT)}")
    excluded_stems = {
        "endpoint",
        "route",
        "provider",
        "observation",
        "stimulation",
        "journal",
        "lease",
        "gateway",
        "time_authority",
    }
    present = sorted(
        path.name
        for path in production
        if path not in ACCEPTED_EXTENSION_PRODUCTION and path.stem in excluded_stems
    )
    if present:
        _fail("excluded subsystem unit present: " + ", ".join(present))
    allocation_containers = {
        r"\bstd::vector\b": "dynamic vector in validated core construction unit",
        r"\bstd::ostringstream\b": "dynamic stream in validated core construction unit",
    }
    for path in production:
        text = path.read_text(encoding="utf-8")
        for pattern, label in allocation_containers.items():
            if re.search(pattern, text):
                _fail(f"{label} found in {path.relative_to(ROOT)}")


def _check_cpp_documentation() -> None:
    """Require ownership, lifetime, thread-safety, and failure clauses in each C++ unit.

    @raises ValidationFailure If a changed unit lacks a required Doxygen clause.
    """

    for path in _cpp_files():
        text = path.read_text(encoding="utf-8")
        missing = [clause for clause in DOCUMENTATION_CLAUSES if clause not in text]
        if missing:
            _fail(
                f"Doxygen contract clauses missing in {path.relative_to(ROOT)}: "
                + ", ".join(missing)
            )
        if path.suffix == ".hpp":
            lines = text.splitlines()
            for index, line in enumerate(lines):
                if "[[nodiscard]]" not in line:
                    continue
                end = index - 1
                while end >= 0 and not lines[end].strip():
                    end -= 1
                start = end
                while start >= 0 and "/**" not in lines[start]:
                    start -= 1
                if end < 0 or "*/" not in lines[end] or start < 0:
                    _fail(
                        "public result declaration lacks Doxygen documentation: "
                        f"{path.relative_to(ROOT)}:{index + 1}"
                    )
    doxyfile = (ROOT / "Doxyfile").read_text(encoding="utf-8")
    for setting, expected in REPOSITORY_DOXYGEN_SETTINGS.items():
        match = re.search(rf"^{re.escape(setting)}\s*=\s*(\S+)", doxyfile, re.MULTILINE)
        if match is None or match.group(1) != expected:
            _fail(f"Doxygen declaration-level gate differs: {setting} must equal {expected}")


def _run_repository_documentation_gate() -> None:
    """Run preserved repository coverage plus strict owned-C++ Doxygen generation.

    @raises ValidationFailure If either repository-wide or strict C++ documentation fails.
    """

    _run([sys.executable, str(ROOT / "scripts" / "check_doxygen.py"), "--self-test"])
    with tempfile.TemporaryDirectory(prefix="xcom-doxygen-") as temporary:
        output = Path(temporary) / "output"
        warning_log = Path(temporary) / "warnings.log"
        configuration = Path(temporary) / "Doxyfile"
        overrides = {
            **STRICT_CPP_DOXYGEN_SETTINGS,
            "OUTPUT_DIRECTORY": output.as_posix(),
            "WARN_LOGFILE": warning_log.as_posix(),
            "INPUT": " ".join(
                path.as_posix()
                for path in (
                    ROOT / "docs" / "xcom" / "core-types.md",
                    CPP_ROOT,
                    TEST_ROOT,
                )
            ),
            "USE_MDFILE_AS_MAINPAGE": (
                ROOT / "docs" / "xcom" / "core-types.md"
            ).as_posix(),
        }
        configuration.write_text(
            f"@INCLUDE = {(ROOT / 'Doxyfile').as_posix()}\n"
            + "".join(f"{key} = {value}\n" for key, value in overrides.items()),
            encoding="utf-8",
        )
        try:
            _run([_tool("doxygen"), str(configuration)])
        except ValidationFailure as error:
            warnings = (
                warning_log.read_text(encoding="utf-8")
                if warning_log.is_file()
                else ""
            )
            _fail(f"strict C++ Doxygen generation failed: {error}\n{warnings}")
        if warning_log.is_file() and warning_log.read_text(encoding="utf-8").strip():
            _fail(
                "strict C++ Doxygen warning log is not empty:\n"
                + warning_log.read_text(encoding="utf-8")
            )
        for relative in ("html/index.html", "xml/index.xml"):
            if not (output / relative).is_file():
                _fail(f"strict C++ Doxygen output is missing: {relative}")


def _run_clang_tidy(build: Path) -> None:
    """Run admitted clang-tidy diagnostics/analyzers on every changed C++ unit.

    @param build Build directory containing compile_commands.json.
    @raises ValidationFailure If any clang diagnostic or analyzer finding occurs.
    """

    executable = _admitted_clang_tidy()
    for path in _cpp_files():
        _run(
            [
                executable,
                str(path),
                "-p",
                str(build),
                "--checks=-*,clang-diagnostic-*,clang-analyzer-*",
                "--warnings-as-errors=*",
                "--quiet",
            ],
            timeout=120,
        )


def _validate_traceability(candidate_revision: str) -> None:
    """Validate revision-bound bidirectional requirement/artifact/check traceability.

    @param candidate_revision Host-supplied revision already matched to workspace HEAD.
    @raises ValidationFailure If the JSON schema subset, paths, or reverse links differ.
    """

    try:
        data = json.loads(TRACEABILITY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"traceability cannot be read: {error}")
    if data.get("schema_version") != 1 or data.get("state") != "READY_FOR_REVIEW":
        _fail("traceability schema/state differs")
    if data.get("candidate_revision_binding") != CANDIDATE_REVISION_BINDING:
        _fail("traceability candidate revision binding differs")
    if candidate_revision != _candidate_revision():
        _fail("candidate revision changed during traceability validation")
    records = data.get("requirements")
    designs = data.get("designs")
    artifacts = data.get("artifacts")
    if (
        not isinstance(records, list)
        or not isinstance(designs, dict)
        or not isinstance(artifacts, dict)
    ):
        _fail("traceability requirement/design/artifact shapes differ")
    observed = {record.get("id") for record in records if isinstance(record, dict)}
    if observed != REQUIREMENTS or len(records) != len(REQUIREMENTS):
        _fail("traceability does not cover each requirement exactly once")
    if set(designs) != set(DESIGN_REQUIREMENTS):
        _fail("traceability design catalog differs from the accepted design units")
    for design_id, expected_requirements in DESIGN_REQUIREMENTS.items():
        design = designs[design_id]
        if not isinstance(design, dict):
            _fail(f"design trace is not an object: {design_id}")
        source = design.get("source")
        if source != DESIGN_SOURCES[design_id]:
            _fail(f"design source differs for {design_id}")
        source_path = ROOT / source
        if not source_path.is_file():
            _fail(f"design source is missing for {design_id}: {source}")
        source_text = source_path.read_text(encoding="utf-8")
        if design_id not in source_text:
            _fail(f"design identifier is absent from its source: {design_id}")
        observed_requirements = design.get("requirements")
        if (
            not isinstance(observed_requirements, list)
            or set(observed_requirements) != expected_requirements
            or len(observed_requirements) != len(expected_requirements)
        ):
            _fail(f"design requirement allocation differs for {design_id}")
        if design_id.startswith("XCOM-TYPE-UNIT-"):
            section_match = re.search(
                rf"^## {re.escape(design_id)}\b(?P<body>.*?)(?=^## |\Z)",
                source_text,
                re.MULTILINE | re.DOTALL,
            )
            if section_match is None:
                _fail(f"unit design section is missing: {design_id}")
            source_match = re.search(
                r"^Source:\s*(?P<ids>[^\n]+)$",
                section_match.group("body"),
                re.MULTILINE,
            )
            allocated = (
                set(re.findall(r"XCOM-TYPE-\d{3}", source_match.group("ids")))
                if source_match is not None
                else set()
            )
            if allocated != expected_requirements:
                _fail(f"unit design Source allocation differs for {design_id}")
        for category in ("code", "tests"):
            paths = design.get(category)
            if not isinstance(paths, list) or not paths:
                _fail(f"design {design_id} has empty or invalid {category} links")
            for path in paths:
                if not isinstance(path, str) or not (ROOT / path).is_file():
                    _fail(f"design {design_id} references missing {category} artifact: {path}")
    for record in records:
        requirement = record["id"]
        for key in ("design", "code", "tests", "checks"):
            if not isinstance(record.get(key), list) or not record[key]:
                _fail(f"{requirement} has empty or invalid {key} trace")
        unknown_designs = sorted(set(record["design"]) - set(DESIGN_REQUIREMENTS))
        if unknown_designs:
            _fail(f"{requirement} references unknown designs: {unknown_designs}")
        for design_id in record["design"]:
            if requirement not in designs[design_id]["requirements"]:
                _fail(f"unsupported design allocation {requirement} -> {design_id}")
        unknown_checks = sorted(set(record["checks"]) - MEASURES)
        if unknown_checks:
            _fail(f"{requirement} references unknown checks: {unknown_checks}")
        for category in ("code", "tests"):
            for path in record[category]:
                if not (ROOT / path).is_file():
                    _fail(f"{requirement} references missing artifact: {path}")
                reverse = artifacts.get(path)
                if not isinstance(reverse, list) or requirement not in reverse:
                    _fail(f"missing reverse trace {path} -> {requirement}")
                if not any(path in designs[design_id][category] for design_id in record["design"]):
                    _fail(
                        f"missing design-to-{category} trace "
                        f"{requirement} -> {record['design']} -> {path}"
                    )
    records_by_id = {record["id"]: record for record in records}
    for design_id, design in designs.items():
        for requirement in design["requirements"]:
            if design_id not in records_by_id[requirement]["design"]:
                _fail(f"missing reverse design trace {design_id} -> {requirement}")
    for path, requirement_ids in artifacts.items():
        if not (ROOT / path).is_file():
            _fail(f"reverse trace references missing artifact: {path}")
        if not isinstance(requirement_ids, list) or not requirement_ids:
            _fail(f"reverse trace is empty: {path}")
        if not set(requirement_ids) <= REQUIREMENTS:
            _fail(f"reverse trace has unknown requirement: {path}")
        for requirement in requirement_ids:
            record = records_by_id[requirement]
            if path not in {*record["code"], *record["tests"]}:
                _fail(f"missing forward trace {requirement} -> {path}")


def _unit(build: Path) -> None:
    """Build and run unit and negative component fixtures.

    @param build Configured disposable build directory.
    @raises ValidationFailure If compilation or selected CTest execution fails.
    """

    targets = ["xverse_xcom_core_types_unit_tests", "xverse_xcom_core_types_negative_tests"]
    _build(build, targets)
    _ctest(build, "^xcom_core_types_(unit|negative)$")


def _lint(build: Path, additive_owned_paths: list[str]) -> None:
    """Run ownership, layout, formatting, forbidden-API, and warning compilation gates.

    @param build Configured disposable build directory.
    @raises ValidationFailure If any lint policy or compilation fails.
    """

    _check_owned_paths(additive_owned_paths)
    _check_layout_and_format()
    _check_forbidden_cpp_apis()
    _check_cpp_documentation()
    _run_repository_documentation_gate()
    _build(
        build,
        [
            "xverse_xcom_core_types",
            "xverse_xcom_core_types_unit_tests",
            "xverse_xcom_core_types_negative_tests",
            "xverse_xcom_core_types_consumer",
        ],
    )


def _static(build: Path) -> None:
    """Run admitted clang-tidy and warning-free Doxygen checks.

    @param build Configured disposable build directory.
    @raises ValidationFailure If static analysis or documentation generation fails.
    """

    _build(build, ["xverse_xcom_core_types"])
    _run_clang_tidy(build)
    _check_cpp_documentation()
    _run_repository_documentation_gate()


def _integration(build: Path) -> None:
    """Compile and execute the separate public-target consumer fixture.

    @param build Configured disposable build directory.
    @raises ValidationFailure If consumer compilation or execution fails.
    """

    _build(build, ["xverse_xcom_core_types_consumer"])
    _ctest(build, "^xcom_core_types_external_consumer$")


def main(arguments: list[str] | None = None) -> int:
    """Select and run one or all declared SESN verification measures.

    @param arguments Optional command-line arguments for tests and embedding.
    @return Zero on success and one on a classified gate failure.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--unit", action="store_true")
    selection.add_argument("--lint", action="store_true")
    selection.add_argument("--static", action="store_true")
    selection.add_argument("--integration", action="store_true")
    selection.add_argument("--all", action="store_true")
    parser.add_argument(
        "--additive-owned-path",
        action="append",
        default=[],
        metavar="PATH",
        help="admit one exact later-slice file or directory in the ownership check",
    )
    args = parser.parse_args(arguments)

    try:
        candidate_revision = _candidate_revision()
        with tempfile.TemporaryDirectory(prefix="xcom-core-types-") as temporary:
            build = Path(temporary) / "build"
            _configure(build)
            if args.unit or args.all:
                _unit(build)
            if args.lint or args.all:
                _lint(build, args.additive_owned_path)
            if args.static or args.all:
                _static(build)
            if args.integration or args.all:
                _integration(build)
            if args.all:
                _validate_traceability(candidate_revision)
    except ValidationFailure as error:
        print(f"X-COM core-types validation failed: {error}", file=sys.stderr)
        return 1

    selected = next(
        name
        for name in ("unit", "lint", "static", "integration", "all")
        if getattr(args, name)
    )
    print(f"X-COM core-types {selected} validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
