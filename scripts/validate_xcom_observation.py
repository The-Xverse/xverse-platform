#!/usr/bin/env python3
"""Validate the bounded, provider-neutral X-COM observation boundary offline.

This validator is an evidence orchestrator.  It never changes the candidate tree,
uses no shell interpretation, and delegates runtime acceptance to the named host
measures.  The observation implementation remains deliberately local: the checks
reject ambient I/O, dynamic storage, forbidden coupling, and traceability gaps.
"""

from __future__ import annotations

import argparse
import json
import os
import py_compile
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import NoReturn

ROOT = Path(__file__).resolve().parents[1]
CPP_ROOT = ROOT / "src" / "xverse" / "xcom"
OBSERVATION_ROOT = ROOT / "tests" / "xcom" / "observation"
TRACEABILITY = ROOT / "docs" / "xcom" / "observation-boundary-traceability.json"
VERIFICATION_PLAN = ROOT / "specs" / "019-feat-ae449f37735949a6" / "verification-measures.json"
CANDIDATE_REVISION_ENV = "SESN_CANDIDATE_REVISION"
CANDIDATE_REVISION_BINDING = {
    "environment_variable": CANDIDATE_REVISION_ENV,
    "format": "full-lowercase-git-sha",
    "workspace_comparison": "git rev-parse HEAD",
}
REQUIREMENTS = {f"XCOM-OBS-{number:03d}" for number in range(1, 11)}
MEASURES = {
    "VM-XCOM-OBS-UNIT",
    "VM-XCOM-OBS-LINT",
    "VM-XCOM-OBS-STATIC",
    "VM-XCOM-OBS-INTEGRATION",
    "VM-XCOM-OBS-PERFORMANCE",
    "VM-XCOM-OBS-VALIDATION",
}
DESIGN_REQUIREMENTS = {
    "XCOM-OBS-UNIT-001": {"XCOM-OBS-001", "XCOM-OBS-002", "XCOM-OBS-003", "XCOM-OBS-004", "XCOM-OBS-008"},
    "XCOM-OBS-UNIT-002": {"XCOM-OBS-004", "XCOM-OBS-005", "XCOM-OBS-006", "XCOM-OBS-007", "XCOM-OBS-008"},
    "XCOM-OBS-UNIT-003": {"XCOM-OBS-001", "XCOM-OBS-002", "XCOM-OBS-004", "XCOM-OBS-005", "XCOM-OBS-007"},
    "XCOM-OBS-UNIT-004": {"XCOM-OBS-006", "XCOM-OBS-007", "XCOM-OBS-008", "XCOM-OBS-009"},
    "XCOM-OBS-UNIT-005": {"XCOM-OBS-009", "XCOM-OBS-010"},
}
DESIGN_SOURCE = "specs/019-feat-ae449f37735949a6/unit-specifications.md"
SADS_DISPOSITIONS = {
    "XVE-SYS-0139": "partial",
    "XVE-SYS-0140": "partial",
    "XVE-SYS-0141": "deferred",
    "XVE-SYS-0142": "partial",
    "XVE-SYS-0143": "deferred",
    "XVE-SYS-0144": "deferred",
    "XVE-SYS-0145": "allocated",
    "XVE-SYS-0146": "partial",
    "XVE-SYS-0147": "partial",
    "XVE-SYS-0148": "deferred",
    "XVE-SYS-0149": "partial",
    "XVE-SYS-0150": "deferred",
    "XVE-SYS-0151": "deferred",
    "XVE-SYS-0152": "deferred",
    "XVE-SYS-0153": "deferred",
    "XVE-SYS-0154": "partial",
    "XVE-SYS-0155": "deferred",
    "XVE-SYS-0156": "deferred",
    "XVE-SYS-0157": "deferred",
    "XVE-SYS-0158": "deferred",
}
PRODUCTION = (
    CPP_ROOT / "include" / "xverse" / "xcom" / "observation.hpp",
    CPP_ROOT / "src" / "observation.cpp",
    CPP_ROOT / "include" / "xverse" / "xcom" / "provider.hpp",
    CPP_ROOT / "src" / "provider.cpp",
)
TEST_FILES = tuple(sorted(OBSERVATION_ROOT.rglob("*.cpp"))) + tuple(
    sorted(OBSERVATION_ROOT.rglob("*.hpp"))
)
CORE_PREDECESSOR_PATHS = (
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
)
APPROVED_CORE_TYPES_BASELINE = "39977ba9e724524dfc42a51e53fa3d61a8964a85"
PREDECESSOR_VALIDATORS = (
    "validate_xcom_core_types.py",
    "validate_xcom_endpoint_route_lifecycle.py",
    "validate_xcom_provider_loopback.py",
)
OWNED_FILES = {
    "scripts/validate_xcom_observation.py",
    "docs/xcom/observation-boundary.md",
    "docs/xcom/observation-boundary-traceability.json",
}


class ValidationFailure(RuntimeError):
    """Represent one deterministic observation validation failure."""


def _fail(message: str) -> NoReturn:
    """Raise a classified gate failure."""

    raise ValidationFailure(message)


def _run(
    argv: list[str], *, cwd: Path = ROOT, timeout: int = 300,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a bounded local command without shell interpretation."""

    try:
        completed = subprocess.run(
            argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            check=False, timeout=timeout, env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        _fail(f"command could not complete: {argv!r}: {error}")
    if completed.returncode:
        _fail(f"command failed ({completed.returncode}): {argv!r}\n{completed.stdout.rstrip()}")
    return completed


def _tool(name: str) -> str:
    """Return an available executable or fail closed."""

    path = shutil.which(name)
    if path is None:
        _fail(f"required executable is unavailable: {name}")
    return path


def _candidate_revision() -> str:
    """Require the SESN candidate revision to equal the immutable workspace HEAD."""

    revision = os.environ.get(CANDIDATE_REVISION_ENV)
    if revision is None or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        _fail(f"{CANDIDATE_REVISION_ENV} must be a full lowercase Git SHA")
    head = _run([_tool("git"), "rev-parse", "HEAD"]).stdout.strip()
    if revision != head:
        _fail(f"{CANDIDATE_REVISION_ENV} {revision} differs from workspace HEAD {head}")
    changed = _run([_tool("git"), "status", "--porcelain", "--untracked-files=all"]).stdout
    if changed:
        _fail("exact candidate revision has uncommitted or untracked inputs")
    return revision


def _configure(build: Path) -> None:
    """Configure the admitted disposable C++20 Ninja build."""

    _run([_tool("cmake"), "-S", str(ROOT), "-B", str(build), "-G", "Ninja",
          "-DBUILD_TESTING=ON", "-DCMAKE_BUILD_TYPE=Debug",
          "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"])


def _build(build: Path, targets: list[str]) -> None:
    """Build exact named targets in a disposable tree."""

    _run([_tool("cmake"), "--build", str(build), "--target", *targets, "--verbose"])


def _ctest(build: Path, expression: str, *, timeout: int = 600) -> None:
    """Run an anchored CTest expression supplied by the verification plan."""

    _run([_tool("ctest"), "--test-dir", str(build), "--output-on-failure", "-R", expression],
         timeout=timeout)


def _check_layout() -> None:
    """Require owned artifacts and reject formatting drift in local text files."""

    required = set(OWNED_FILES) | {
        "src/xverse/xcom/include/xverse/xcom/observation.hpp",
        "src/xverse/xcom/src/observation.cpp",
        "src/xverse/xcom/include/xverse/xcom/provider.hpp",
        "src/xverse/xcom/src/provider.cpp",
        "tests/xcom/observation/core/unit_tests.cpp",
        "tests/xcom/observation/integration/integration_tests.cpp",
        "tests/xcom/observation/integration/disabled_tap_benchmark.cpp",
        "tests/xcom/observation/integration/test_support.hpp",
    }
    missing = sorted(path for path in required if not (ROOT / path).is_file())
    if missing:
        _fail("required observation artifacts are missing: " + ", ".join(missing))
    for relative in sorted(required):
        text = (ROOT / relative).read_text(encoding="utf-8")
        if not text.endswith("\n"):
            _fail(f"text file lacks terminal newline: {relative}")
        if any(line.rstrip() != line for line in text.splitlines()):
            _fail(f"trailing whitespace: {relative}")
        if (ROOT / relative).suffix in {".cpp", ".hpp", ".py", ".md"} and any("\t" in line for line in text.splitlines()):
            _fail(f"tab violates formatting policy: {relative}")


def _check_boundaries() -> None:
    """Inspect the observation slice for fixed storage and forbidden operations."""

    patterns = {
        r"#\s*include\s*[<\"](?:filesystem|fstream|cstdio|cstdlib|dlfcn|netinet|sys/socket|grpc|google/protobuf)": "forbidden ambient or external header",
        r"\b(?:getenv|system|popen|fork|exec[a-z]*|socket|connect|listen|accept|dlopen|dlsym)\s*\(": "forbidden ambient/process/network API",
        r"\bstd::(?:vector|deque|list|map|unordered_map|set|unordered_set)\b": "dynamic container",
        r"\boperator\s+new\b|\bnew\s+[A-Za-z_:][A-Za-z0-9_:<>]*\s*(?:\(|\{)": "explicit dynamic allocation",
    }
    for path in PRODUCTION:
        text = path.read_text(encoding="utf-8")
        for pattern, label in patterns.items():
            for match in re.finditer(pattern, text):
                if label == "forbidden ambient/process/network API":
                    line_start = text.rfind("\n", 0, match.start()) + 1
                    line_end = text.find("\n", match.end())
                    if line_end == -1:
                        line_end = len(text)
                    line = text[line_start:line_end]
                    name = match.group(0).split("(", 1)[0].strip()
                    member_pattern = (
                        rf"(?:\b[A-Za-z_]\w*::)*{re.escape(name)}\s*\([^;]*\)"
                        rf"\s*(?:const\s*)?noexcept\s*(?:[;{{])"
                    )
                    if re.search(member_pattern, line):
                        continue
                _fail(f"{label} found in {path.relative_to(ROOT)}")
    header = (CPP_ROOT / "include" / "xverse" / "xcom" / "observation.hpp").read_text(encoding="utf-8")
    required_tokens = (
        "kMaximumObservationTaps",
        "kMaximumObservationRecordsPerTap",
        "std::array<std::optional<ObservationRecord>",
        "std::mutex mutex_",
        "ObservationTapHandle",
        "SyntheticObservationSink",
    )
    for token in required_tokens:
        if token not in header:
            _fail(f"fixed observation contract token is absent: {token}")
    if "std::lock_guard" not in (CPP_ROOT / "src" / "observation.cpp").read_text(encoding="utf-8"):
        _fail("serialized observation mutation is absent")


def _validate_traceability(candidate_revision: str) -> None:
    """Validate reciprocal requirement/design/code/test/check edges and identity binding."""

    try:
        data = json.loads(TRACEABILITY.read_text(encoding="utf-8"))
        measures = json.loads(VERIFICATION_PLAN.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"traceability input cannot be read: {error}")
    if data.get("schema_version") != 1 or data.get("state") != "READY_FOR_REVIEW":
        _fail("traceability schema/state differs")
    if data.get("feature_id") != "FEAT-ae449f37735949a6" or data.get("baseline_id") != "BASE-77de4af385e6433fb510":
        _fail("traceability feature or baseline identity differs")
    if data.get("candidate_revision_binding") != CANDIDATE_REVISION_BINDING or candidate_revision != _candidate_revision():
        _fail("traceability candidate revision binding differs")
    records = data.get("requirements")
    designs = data.get("designs")
    artifacts = data.get("artifacts")
    sads_dispositions = data.get("sads_dispositions")
    if not isinstance(records, list) or not isinstance(designs, dict) or not isinstance(artifacts, dict):
        _fail("traceability collection shapes differ")
    if not isinstance(sads_dispositions, list):
        _fail("SADS disposition collection differs")
    sads_by_id = {
        item.get("id"): item.get("disposition")
        for item in sads_dispositions if isinstance(item, dict)
    }
    if sads_by_id != SADS_DISPOSITIONS or len(sads_dispositions) != len(SADS_DISPOSITIONS):
        _fail("SADS disposition catalog differs")
    records_by_id = {item.get("id"): item for item in records if isinstance(item, dict)}
    if set(records_by_id) != REQUIREMENTS or len(records) != len(REQUIREMENTS):
        _fail("traceability does not cover every requirement exactly once")
    if set(designs) != set(DESIGN_REQUIREMENTS):
        _fail("traceability design catalog differs")
    measure_by_id = {item.get("id"): item for item in measures if isinstance(item, dict)}
    if not isinstance(measures, list) or set(measure_by_id) != MEASURES or len(measures) != len(MEASURES):
        _fail("authoritative observation measure catalog differs")
    for design_id, expected in DESIGN_REQUIREMENTS.items():
        design = designs[design_id]
        if design.get("source") != DESIGN_SOURCE:
            _fail(f"design source differs: {design_id}")
        if set(design.get("requirements", [])) != expected:
            _fail(f"design allocation differs: {design_id}")
        for key in ("code", "tests"):
            if not isinstance(design.get(key), list) or not design[key]:
                _fail(f"empty design {key} edge: {design_id}")
    for requirement in records:
        if requirement.get("id") not in REQUIREMENTS:
            _fail("unknown requirement in traceability")
        for key in ("design", "code", "tests", "checks"):
            if not isinstance(requirement.get(key), list) or not requirement[key]:
                _fail(f"empty reciprocal edge {key}: {requirement.get('id')}")
        if not set(requirement["design"]).issubset(designs):
            _fail(f"requirement design edge is unknown: {requirement['id']}")
        if not set(requirement["checks"]).issubset(MEASURES):
            _fail(f"requirement check edge is unknown: {requirement['id']}")
    for design_id, design in designs.items():
        for requirement_id in design["requirements"]:
            requirement = records_by_id[requirement_id]
            if design_id not in requirement["design"]:
                _fail(f"missing reverse design edge: {design_id} -> {requirement_id}")
            for artifact in design["code"]:
                if artifact not in requirement["code"]:
                    _fail(f"missing design-to-code edge: {design_id} -> {artifact}")
            for artifact in design["tests"]:
                if artifact not in requirement["tests"]:
                    _fail(f"missing design-to-test edge: {design_id} -> {artifact}")
    for artifact, requirement_ids in artifacts.items():
        if not requirement_ids or not set(requirement_ids).issubset(REQUIREMENTS):
            _fail(f"artifact allocation differs: {artifact}")
        if not (ROOT / artifact).is_file():
            _fail(f"traceability artifact is missing: {artifact}")
        for requirement_id in requirement_ids:
            requirement = records_by_id[requirement_id]
            if artifact not in {*requirement["code"], *requirement["tests"]}:
                _fail(f"missing forward artifact edge: {requirement_id} -> {artifact}")
    expected_artifacts = {
        artifact for item in records for artifact in (*item["code"], *item["tests"])
    }
    if set(artifacts) != expected_artifacts:
        _fail("traceability artifact catalog is not exactly reciprocal")
    for requirement in records:
        requirement_id = requirement["id"]
        expected_checks = {
            measure_id for measure_id, measure in measure_by_id.items()
            if requirement_id in measure.get("requirement_ids", [])
        }
        if set(requirement["checks"]) != expected_checks:
            _fail(f"requirement/measure allocation differs: {requirement_id}")
    for measure_id, measure in measure_by_id.items():
        requirement_ids = measure.get("requirement_ids")
        if not isinstance(requirement_ids, list) or not requirement_ids:
            _fail(f"measure requirement allocation differs: {measure_id}")
        for requirement_id in requirement_ids:
            if measure_id not in records_by_id.get(requirement_id, {}).get("checks", []):
                _fail(f"missing reverse measure edge: {measure_id} -> {requirement_id}")


def _unit(build: Path) -> None:
    """Build and run focused observation unit fixtures."""

    _build(build, ["xverse_xcom_observation_unit_tests"])
    _ctest(build, r"^xcom_observation_unit$")


def _integration(build: Path) -> None:
    """Build and run provider/observation loopback integration fixtures."""

    _build(build, ["xverse_xcom_observation_integration_tests"])
    _ctest(build, r"^xcom_observation_integration$")


def _performance(build: Path) -> None:
    """Run and retain the repeated paired disabled-tap benchmark evidence."""

    _build(build, ["xverse_xcom_observation_disabled_benchmark"])
    completed = _run(
        [_tool("ctest"), "--test-dir", str(build), "--verbose", "-R",
         r"^xcom_observation_disabled_benchmark$"],
        timeout=900,
    )
    output = completed.stdout
    required_tokens = (
        "fixture=owned-loopback-disabled-observation",
        "baseline_revision=39977ba9e724524dfc42a51e53fa3d61a8964a85",
        "candidate_path=public-submit-null-observation-hub",
        "paired_samples=21",
        "pair_order=alternating",
        "paired_median_latency_regression_percent=",
        "paired_median_throughput_regression_percent=",
        "accepted_threshold_percent=2",
        "uncertainty=",
        "sample[0].baseline_latency_ns=",
        "sample[20].throughput_regression_percent=",
        "latency_threshold=PASS",
        "throughput_threshold=PASS",
    )
    missing = [token for token in required_tokens if token not in output]
    if missing:
        _fail("benchmark output lacks retained paired evidence: " + ", ".join(missing))
    print("X-COM observation retained performance evidence:\n" + output.rstrip())


def _lint(build: Path) -> None:
    """Apply source-level warning and boundary policy checks without executing tests."""

    _check_layout()
    _check_boundaries()
    for path in (ROOT / "scripts" / "validate_xcom_observation.py",):
        try:
            py_compile.compile(
                str(path),
                cfile=str(build / "validate_xcom_observation.pyc"),
                doraise=True,
            )
        except (OSError, py_compile.PyCompileError) as error:
            _fail(f"Python syntax check failed: {path}: {error}")


def _run_doxygen() -> None:
    """Generate strict warning-free Doxygen for the observation contract and fixtures."""

    _run([sys.executable, str(ROOT / "scripts" / "check_doxygen.py"), "--self-test"])
    with tempfile.TemporaryDirectory(prefix="xcom-observation-doxygen-") as temporary:
        temp = Path(temporary)
        output = temp / "output"
        warning_log = temp / "warnings.log"
        configuration = temp / "Doxyfile"
        inputs = (
            ROOT / "docs" / "xcom" / "observation-boundary.md",
            *PRODUCTION,
            *TEST_FILES,
        )
        overrides = {
            "OUTPUT_DIRECTORY": output.as_posix(),
            "WARN_LOGFILE": warning_log.as_posix(),
            "INPUT": " ".join(path.as_posix() for path in inputs),
            "USE_MDFILE_AS_MAINPAGE": inputs[0].as_posix(),
            "EXTRACT_ALL": "NO",
            "EXTRACT_PRIVATE": "NO",
            "EXTRACT_PRIV_VIRTUAL": "YES",
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


def _static(build: Path) -> None:
    """Run strict Doxygen, admitted clang-tidy, and reciprocal evidence checks."""

    _check_layout()
    _check_boundaries()
    candidate_revision = _candidate_revision()
    _validate_traceability(candidate_revision)
    clang_tidy = Path(os.environ.get("XVERSE_XCOM_TOOLCHAIN", "")) / "usr" / "bin" / "clang-tidy"
    if not clang_tidy.is_file() or not os.access(clang_tidy, os.X_OK):
        _fail(f"admitted clang-tidy is unavailable: {clang_tidy}")
    _build(build, ["xverse_xcom_observation_unit_tests"])
    for path in PRODUCTION + TEST_FILES:
        _run([str(clang_tidy), str(path), "-p", str(build),
              "--checks=-*,clang-diagnostic-*,clang-analyzer-*",
              "--warnings-as-errors=*", "--quiet"], timeout=120)
    _run_doxygen()


def _check_core_predecessor_unchanged(candidate_revision: str) -> None:
    """Reject changes to the approved predecessor core implementation or tests."""

    baseline = _run(
        [_tool("git"), "rev-parse", "--verify", f"{APPROVED_CORE_TYPES_BASELINE}^{{commit}}"],
        timeout=30,
    ).stdout.strip()
    result = subprocess.run(
        [_tool("git"), "diff", "--quiet", baseline, candidate_revision, "--",
         *CORE_PREDECESSOR_PATHS],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode:
        _fail(
            "approved predecessor core implementation/test artifacts changed: "
            + ", ".join(CORE_PREDECESSOR_PATHS)
        )


def _prior_regressions(candidate_revision: str) -> None:
    """Run every accepted predecessor validator in a clean exact-candidate worktree.

    A separate worktree makes each predecessor validator see its native clean
    ownership boundary.  No validator module, ownership list, gate, or candidate
    input is altered; each validator executes its complete ``--all`` contract.
    """

    _check_core_predecessor_unchanged(candidate_revision)
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    with tempfile.TemporaryDirectory(prefix="xcom-observation-predecessors-") as temporary:
        worktree = Path(temporary) / "candidate"
        _run(
            [_tool("git"), "worktree", "add", "--detach", str(worktree), candidate_revision],
            timeout=120,
            environment=environment,
        )
        try:
            for validator in PREDECESSOR_VALIDATORS:
                completed = _run(
                    [sys.executable, str(worktree / "scripts" / validator), "--all"],
                    cwd=worktree,
                    timeout=1200,
                    environment=environment,
                )
                print(f"X-COM accepted predecessor {validator} evidence:\n"
                      + completed.stdout.rstrip())
        finally:
            _run(
                [_tool("git"), "worktree", "remove", "--force", str(worktree)],
                timeout=120,
                environment=environment,
            )


def main() -> int:
    """Select one or more declared host measures and report a stable result."""

    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for name in ("unit", "lint", "static", "integration", "performance", "all"):
        group.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    selected = next(name for name in ("unit", "lint", "static", "integration", "performance", "all") if getattr(args, name))
    try:
        with tempfile.TemporaryDirectory(prefix="xcom-observation-build-") as directory:
            build = Path(directory) / "build"
            _configure(build)
            if selected in {"unit", "static", "all"}:
                _unit(build)
            if selected in {"lint", "all"}:
                _lint(build)
            if selected in {"static", "all"}:
                _static(build)
            if selected in {"integration", "all"}:
                _integration(build)
            if selected in {"performance", "all"}:
                _performance(build)
            if selected == "all":
                _prior_regressions(_candidate_revision())
                _validate_traceability(_candidate_revision())
    except ValidationFailure as error:
        print(f"X-COM observation validation failed: {error}", file=sys.stderr)
        return 1
    print(f"X-COM observation {selected} validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
