#!/usr/bin/env python3
"""Validate the bounded endpoint and route lifecycle slice offline."""

from __future__ import annotations

import argparse
import importlib.util
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
TEST_ROOT = ROOT / "tests" / "xcom" / "endpoint_route_lifecycle"
TRACEABILITY = ROOT / "docs" / "xcom" / "endpoint-route-lifecycle-traceability.json"
VERIFICATION_MEASURES = (
    ROOT / "specs" / "013-feat-5cfe89f5d1214030" / "verification-measures.json"
)
CANDIDATE_REVISION_ENV = "SESN_CANDIDATE_REVISION"
CANDIDATE_REVISION_BINDING = {
    "environment_variable": CANDIDATE_REVISION_ENV,
    "format": "full-lowercase-git-sha",
    "workspace_comparison": "git rev-parse HEAD",
}
REQUIREMENTS = {f"XCOM-LIFE-{number:03d}" for number in range(1, 12)}
MEASURES = {
    "VM-XCOM-LIFE-UNIT",
    "VM-XCOM-LIFE-LINT",
    "VM-XCOM-LIFE-STATIC",
    "VM-XCOM-LIFE-INTEGRATION",
    "VM-XCOM-LIFE-VALIDATION",
}
DESIGN_REQUIREMENTS = {
    "XCOM-LIFE-UNIT-001": {"XCOM-LIFE-001", "XCOM-LIFE-002", "XCOM-LIFE-009"},
    "XCOM-LIFE-UNIT-002": {"XCOM-LIFE-002", "XCOM-LIFE-008"},
    "XCOM-LIFE-UNIT-003": {"XCOM-LIFE-003", "XCOM-LIFE-006"},
    "XCOM-LIFE-UNIT-004": {
        "XCOM-LIFE-004",
        "XCOM-LIFE-005",
        "XCOM-LIFE-006",
        "XCOM-LIFE-011",
    },
    "XCOM-LIFE-UNIT-005": {"XCOM-LIFE-007", "XCOM-LIFE-009"},
    "XCOM-LIFE-UNIT-006": {"XCOM-LIFE-010"},
    "XCOM-LIFE-UNIT-007": {"XCOM-LIFE-006", "XCOM-LIFE-008", "XCOM-LIFE-011"},
}
DESIGN_SOURCE = "specs/013-feat-5cfe89f5d1214030/unit-specifications.md"
OWNED_PREFIXES = ("src/xverse/xcom/", "tests/xcom/endpoint_route_lifecycle/")
OWNED_FILES = {
    "scripts/validate_xcom_endpoint_route_lifecycle.py",
    "docs/xcom/endpoint-route-lifecycle.md",
    "docs/xcom/endpoint-route-lifecycle-traceability.json",
}
LIFECYCLE_CPP = (
    CPP_ROOT / "include" / "xverse" / "xcom" / "endpoint_route_lifecycle.hpp",
    CPP_ROOT / "src" / "endpoint_route_lifecycle.cpp",
)
CPP_CHECK_INPUTS = (*LIFECYCLE_CPP, *sorted(TEST_ROOT.rglob("*.cpp")))


class ValidationFailure(RuntimeError):
    """Represent one deterministic validation-gate failure."""


def _fail(message: str) -> NoReturn:
    """Raise a classified validation failure."""

    raise ValidationFailure(message)


def _run(
    argv: list[str], *, cwd: Path = ROOT, timeout: int = 300
) -> subprocess.CompletedProcess[str]:
    """Run one bounded local command without shell interpretation."""

    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        _fail(f"command could not complete: {argv!r}: {error}")
    if completed.returncode:
        _fail(f"command failed ({completed.returncode}): {argv!r}\n{completed.stdout.rstrip()}")
    return completed


def _tool(name: str) -> str:
    """Return an available executable path or fail closed."""

    path = shutil.which(name)
    if path is None:
        _fail(f"required executable is unavailable: {name}")
    return path


def _candidate_revision() -> str:
    """Validate the SESN candidate revision against the unchanged workspace HEAD."""

    revision = os.environ.get(CANDIDATE_REVISION_ENV)
    if revision is None or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        _fail(f"{CANDIDATE_REVISION_ENV} must be a full lowercase Git SHA")
    head = _run([_tool("git"), "rev-parse", "HEAD"]).stdout.strip()
    if revision != head:
        _fail(f"{CANDIDATE_REVISION_ENV} {revision} differs from workspace HEAD {head}")
    return revision


def _configure(build: Path) -> None:
    """Configure one disposable warning-as-error Ninja build."""

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
    """Build exact named targets in the disposable tree."""

    _run([_tool("cmake"), "--build", str(build), "--target", *targets, "--verbose"])


def _ctest(build: Path, expression: str) -> None:
    """Run exact CTest fixtures selected by an anchored expression."""

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


def _normalize_additive_owned_paths(values: list[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Validate explicit later-slice paths admitted only by the ownership gate."""

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
    """Reject changed paths outside this SESN task's ownership boundary."""

    changed = _run([_tool("git"), "diff", "--name-only", "--", "."]).stdout.splitlines()
    untracked = _run(
        [_tool("git"), "ls-files", "--others", "--exclude-standard"]
    ).stdout.splitlines()
    additive_files, additive_prefixes = _normalize_additive_owned_paths(additive_owned_paths)
    unexpected = sorted(
        path
        for path in set((*changed, *untracked))
        if path not in OWNED_FILES
        and path not in additive_files
        and not path.startswith((*OWNED_PREFIXES, *additive_prefixes))
    )
    if unexpected:
        _fail("changed paths exceed task ownership: " + ", ".join(unexpected))


def _check_layout_and_text() -> None:
    """Require every owned artifact and deterministic repository text formatting."""

    required = {
        *OWNED_FILES,
        "src/xverse/xcom/CMakeLists.txt",
        "src/xverse/xcom/include/xverse/xcom/diagnostic.hpp",
        "src/xverse/xcom/include/xverse/xcom/endpoint_route_lifecycle.hpp",
        "src/xverse/xcom/src/diagnostic.cpp",
        "src/xverse/xcom/src/endpoint_route_lifecycle.cpp",
        "tests/xcom/endpoint_route_lifecycle/unit_tests.cpp",
        "tests/xcom/endpoint_route_lifecycle/negative_tests.cpp",
        "tests/xcom/endpoint_route_lifecycle/consumer/main.cpp",
    }
    missing = sorted(path for path in required if not (ROOT / path).is_file())
    if missing:
        _fail("required lifecycle artifacts are missing: " + ", ".join(missing))
    for relative in sorted(required):
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            _fail(f"text file lacks terminal newline: {relative}")
        for number, line in enumerate(text.splitlines(), start=1):
            if line.rstrip() != line:
                _fail(f"trailing whitespace: {relative}:{number}")
            if "\t" in line and path.suffix in {".cpp", ".hpp", ".py", ".md"}:
                _fail(f"tab violates formatting policy: {relative}:{number}")


def _check_bounded_control_plane() -> None:
    """Reject data retention, dynamic containers, external access, and excluded dependencies."""

    patterns = {
        r"\bCommunicationItem\b": "CommunicationItem reference in lifecycle unit",
        r"#\s*include\s*[<\"](?:filesystem|fstream|cstdio|cstdlib|grpc|google/protobuf|nlohmann)":
            "forbidden external or ambient header",
        r"\b(?:getenv|system|popen|fork|exec[a-z]*|socket|connect|listen|accept)\s*\(":
            "ambient/process/network API",
        r"\bstd::(?:vector|deque|list|map|unordered_map|set|unordered_set)\b":
            "dynamic lifecycle container",
        r"\bnew\s+": "explicit dynamic allocation",
    }
    for path in LIFECYCLE_CPP:
        text = path.read_text(encoding="utf-8")
        for pattern, label in patterns.items():
            if re.search(pattern, text):
                _fail(f"{label} found in {path.relative_to(ROOT)}")
    header = LIFECYCLE_CPP[0].read_text(encoding="utf-8")
    source = LIFECYCLE_CPP[1].read_text(encoding="utf-8")
    required_tokens = (
        "std::array<std::optional<EndpointRecord>, kMaximumEndpoints>",
        "std::array<std::optional<RouteRecord>, kMaximumRoutes>",
        "static constexpr std::size_t kMaximumEndpoints = 32U",
        "static constexpr std::size_t kMaximumRoutes = 32U",
        "mutable std::mutex mutex_",
    )
    for token in required_tokens:
        if token not in header:
            _fail(f"fixed-capacity/thread-safety declaration differs: {token}")
    if "std::lock_guard" not in source:
        _fail("controller operations do not show serialized lock ownership")
    route_compatibility_tokens = (
        "route->spec.provider_id() == source_record->spec.provider_id()",
        "route->spec.provider_id() == destination_record->spec.provider_id()",
        "source_record->spec.direction() == route->spec.contract().source_direction()",
        "destination_record->spec.direction() == route->spec.contract().target_direction()",
    )
    for token in route_compatibility_tokens:
        if source.count(token) != 2:
            _fail(
                "route validation and activation must both enforce exact compatibility: "
                + token
            )


def _check_diagnostic_compatibility() -> None:
    """Prove old stable codes remain byte-exact and lifecycle additions are unique."""

    source = (CPP_ROOT / "src" / "diagnostic.cpp").read_text(encoding="utf-8")
    expected = {
        "required_field": "XCOM-TYPE-E001",
        "bound_exceeded": "XCOM-TYPE-E002",
        "invalid_version": "XCOM-TYPE-E003",
        "incompatible_direction": "XCOM-TYPE-E004",
        "contract_mismatch": "XCOM-TYPE-E005",
        "invalid_digest": "XCOM-LIFE-E006",
        "capacity_exhausted": "XCOM-LIFE-E007",
        "duplicate_identity": "XCOM-LIFE-E008",
        "invalid_handle": "XCOM-LIFE-E009",
        "invalid_transition": "XCOM-LIFE-E010",
        "endpoint_in_use": "XCOM-LIFE-E011",
        "route_incompatible": "XCOM-LIFE-E012",
        "generation_exhausted": "XCOM-LIFE-E013",
    }
    for enumerator, external in expected.items():
        fragment = f'case DiagnosticCode::{enumerator}:\n      return "{external}";'
        if fragment not in source:
            _fail(f"stable diagnostic mapping differs: {enumerator} -> {external}")
    if len(set(expected.values())) != len(expected):
        _fail("diagnostic code mapping is not unique")


def _run_doxygen() -> None:
    """Generate strict warning-free Doxygen for lifecycle public and test contracts."""

    _run([sys.executable, str(ROOT / "scripts" / "check_doxygen.py"), "--self-test"])
    with tempfile.TemporaryDirectory(prefix="xcom-life-doxygen-") as temporary:
        temp = Path(temporary)
        output = temp / "output"
        warning_log = temp / "warnings.log"
        configuration = temp / "Doxyfile"
        inputs = (ROOT / "docs" / "xcom" / "endpoint-route-lifecycle.md", *LIFECYCLE_CPP)
        overrides = {
            "OUTPUT_DIRECTORY": output.as_posix(),
            "WARN_LOGFILE": warning_log.as_posix(),
            "INPUT": " ".join(path.as_posix() for path in inputs),
            "USE_MDFILE_AS_MAINPAGE": inputs[0].as_posix(),
            "EXTRACT_ALL": "NO",
            "WARN_IF_UNDOCUMENTED": "YES",
            "WARN_NO_PARAMDOC": "YES",
            "WARN_AS_ERROR": "YES",
            "GENERATE_HTML": "YES",
            "GENERATE_XML": "YES",
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
                else "warning log was not created"
            )
            _fail(f"strict Doxygen generation failed: {error}\n{warnings}")
        if warning_log.is_file() and warning_log.read_text(encoding="utf-8").strip():
            _fail("strict Doxygen warning log is not empty:\n" + warning_log.read_text(encoding="utf-8"))
        for relative in ("html/index.html", "xml/index.xml"):
            if not (output / relative).is_file():
                _fail(f"strict Doxygen output is missing: {relative}")


def _run_clang_tidy(build: Path) -> None:
    """Run admitted compiler diagnostics and analyzers on every lifecycle C++ unit."""

    prefix = os.environ.get("XVERSE_XCOM_TOOLCHAIN", "")
    executable = Path(prefix).resolve() / "usr" / "bin" / "clang-tidy"
    if not prefix or not executable.is_file() or not os.access(executable, os.X_OK):
        _fail(f"admitted clang-tidy is unavailable: {executable}")
    for path in CPP_CHECK_INPUTS:
        _run(
            [
                str(executable),
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
    """Validate reciprocal requirement/design/code/test/check edges and revision binding."""

    try:
        data = json.loads(TRACEABILITY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"traceability cannot be read: {error}")
    if data.get("schema_version") != 1 or data.get("state") != "READY_FOR_REVIEW":
        _fail("traceability schema/state differs")
    if data.get("feature_id") != "FEAT-5cfe89f5d1214030" or data.get(
        "baseline_id"
    ) != "BASE-39bb479b857541a99bab":
        _fail("traceability feature or baseline identity differs")
    if data.get("candidate_revision_binding") != CANDIDATE_REVISION_BINDING:
        _fail("traceability candidate revision binding differs")
    if candidate_revision != _candidate_revision():
        _fail("candidate revision changed during validation")
    records = data.get("requirements")
    designs = data.get("designs")
    artifacts = data.get("artifacts")
    if not isinstance(records, list) or not isinstance(designs, dict) or not isinstance(artifacts, dict):
        _fail("traceability collection shapes differ")
    records_by_id = {
        record.get("id"): record for record in records if isinstance(record, dict)
    }
    if set(records_by_id) != REQUIREMENTS or len(records) != len(REQUIREMENTS):
        _fail("traceability does not cover every requirement exactly once")
    if set(designs) != set(DESIGN_REQUIREMENTS):
        _fail("traceability design catalog differs")
    try:
        measure_records = json.loads(VERIFICATION_MEASURES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"authoritative verification measures cannot be read: {error}")
    if not isinstance(measure_records, list):
        _fail("authoritative verification-measure catalog shape differs")
    measures_by_id = {
        measure.get("id"): measure
        for measure in measure_records
        if isinstance(measure, dict)
    }
    if set(measures_by_id) != MEASURES or len(measure_records) != len(MEASURES):
        _fail("authoritative verification-measure catalog differs")
    expected_checks = {requirement: set() for requirement in REQUIREMENTS}
    for measure_id, measure in measures_by_id.items():
        requirement_ids = measure.get("requirement_ids")
        if (
            not isinstance(requirement_ids, list)
            or not requirement_ids
            or not set(requirement_ids) <= REQUIREMENTS
            or len(requirement_ids) != len(set(requirement_ids))
        ):
            _fail(f"authoritative requirement allocation differs: {measure_id}")
        for requirement in requirement_ids:
            expected_checks[requirement].add(measure_id)
    source_text = (ROOT / DESIGN_SOURCE).read_text(encoding="utf-8")
    for design_id, expected_requirements in DESIGN_REQUIREMENTS.items():
        design = designs[design_id]
        if design.get("source") != DESIGN_SOURCE or design_id not in source_text:
            _fail(f"design source differs or omits identifier: {design_id}")
        if set(design.get("requirements", [])) != expected_requirements:
            _fail(f"design requirement allocation differs: {design_id}")
        for category in ("code", "tests"):
            paths = design.get(category)
            if not isinstance(paths, list) or not paths:
                _fail(f"design has no {category} links: {design_id}")
            for path in paths:
                if not isinstance(path, str) or not (ROOT / path).is_file():
                    _fail(f"design references missing {category}: {design_id} -> {path}")
    for requirement, record in records_by_id.items():
        for key in ("design", "code", "tests", "checks"):
            if not isinstance(record.get(key), list) or not record[key]:
                _fail(f"{requirement} has empty {key} trace")
        if set(record["checks"]) != expected_checks[requirement]:
            _fail(f"{requirement} verification allocation is not authoritative and reciprocal")
        for design_id in record["design"]:
            if requirement not in designs[design_id]["requirements"]:
                _fail(f"unsupported requirement-to-design edge: {requirement} -> {design_id}")
        for category in ("code", "tests"):
            for path in record[category]:
                if not (ROOT / path).is_file():
                    _fail(f"{requirement} references missing artifact: {path}")
                if requirement not in artifacts.get(path, []):
                    _fail(f"missing reverse artifact edge: {path} -> {requirement}")
                if not any(path in designs[item][category] for item in record["design"]):
                    _fail(f"missing design bridge: {requirement} -> {path}")
    for design_id, design in designs.items():
        for requirement in design["requirements"]:
            if design_id not in records_by_id[requirement]["design"]:
                _fail(f"missing reverse design edge: {design_id} -> {requirement}")
    for path, requirement_ids in artifacts.items():
        if not (ROOT / path).is_file() or not isinstance(requirement_ids, list) or not requirement_ids:
            _fail(f"invalid reverse artifact trace: {path}")
        for requirement in requirement_ids:
            record = records_by_id.get(requirement)
            if record is None or path not in {*record["code"], *record["tests"]}:
                _fail(f"missing forward artifact edge: {requirement} -> {path}")


def _run_core_types_regression(additive_owned_paths: list[str]) -> None:
    """Run the complete accepted core-types validator on the integrated candidate."""

    validator = ROOT / "scripts" / "validate_xcom_core_types.py"
    spec = importlib.util.spec_from_file_location("xcom_core_types_validator", validator)
    if spec is None or spec.loader is None:
        _fail("accepted core-types validator cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    admitted = [
        "scripts/validate_xcom_endpoint_route_lifecycle.py",
        "docs/xcom/endpoint-route-lifecycle.md",
        "docs/xcom/endpoint-route-lifecycle-traceability.json",
        "tests/xcom/endpoint_route_lifecycle",
        "src/xverse/xcom/include/xverse/xcom/endpoint_route_lifecycle.hpp",
        "src/xverse/xcom/src/endpoint_route_lifecycle.cpp",
        *additive_owned_paths,
    ]
    arguments = ["--all"]
    for path in admitted:
        arguments.extend(("--additive-owned-path", path))
    result = module.main(arguments)
    if result != 0:
        _fail("accepted core-types validator rejected the integrated candidate")


def _unit(build: Path) -> None:
    """Build and run lifecycle unit, negative, state, capacity, and concurrency tests."""

    _build(build, ["xverse_xcom_lifecycle_unit_tests", "xverse_xcom_lifecycle_negative_tests"])
    _ctest(build, "^xcom_lifecycle_(unit|negative)$")


def _lint(build: Path, additive_owned_paths: list[str]) -> None:
    """Run ownership, formatting, forbidden-boundary, diagnostic, and warning gates."""

    _check_owned_paths(additive_owned_paths)
    _check_layout_and_text()
    _check_bounded_control_plane()
    _check_diagnostic_compatibility()
    _build(
        build,
        [
            "xverse_xcom_endpoint_route_lifecycle",
            "xverse_xcom_lifecycle_unit_tests",
            "xverse_xcom_lifecycle_negative_tests",
            "xverse_xcom_lifecycle_consumer",
        ],
    )


def _static(build: Path, candidate_revision: str) -> None:
    """Run analyzer, Doxygen, bounded-layout, and reciprocal traceability checks."""

    _build(build, ["xverse_xcom_endpoint_route_lifecycle"])
    _run_clang_tidy(build)
    _run_doxygen()
    _check_bounded_control_plane()
    _validate_traceability(candidate_revision)


def _integration(build: Path) -> None:
    """Build and run the separate item-free public lifecycle consumer."""

    _build(build, ["xverse_xcom_lifecycle_consumer"])
    _ctest(build, "^xcom_lifecycle_external_consumer$")


def main(arguments: list[str] | None = None) -> int:
    """Select and execute one or every declared SESN verification measure."""

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
        with tempfile.TemporaryDirectory(prefix="xcom-lifecycle-") as temporary:
            build = Path(temporary) / "build"
            _configure(build)
            if args.unit or args.all:
                _unit(build)
            if args.lint or args.all:
                _lint(build, args.additive_owned_path)
            if args.static or args.all:
                _static(build, candidate_revision)
            if args.integration or args.all:
                _integration(build)
            if args.all:
                _run_core_types_regression(args.additive_owned_path)
                _validate_traceability(candidate_revision)
    except ValidationFailure as error:
        print(f"X-COM endpoint/route lifecycle validation failed: {error}", file=sys.stderr)
        return 1
    selected = next(name for name in ("unit", "lint", "static", "integration", "all") if getattr(args, name))
    print(f"X-COM endpoint/route lifecycle {selected} validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
