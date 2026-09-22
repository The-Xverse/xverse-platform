#!/usr/bin/env python3
"""Validate explicit provider composition and the bounded loopback provider offline."""

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
TEST_ROOT = ROOT / "tests" / "xcom" / "provider_loopback"
TRACEABILITY = ROOT / "docs" / "xcom" / "provider-composition-loopback-traceability.json"
VERIFICATION_MEASURES = ROOT / "specs" / "014-feat-e17d4ee9f29848f5" / "verification-measures.json"
CANDIDATE_REVISION_ENV = "SESN_CANDIDATE_REVISION"
CANDIDATE_REVISION_BINDING = {
    "environment_variable": CANDIDATE_REVISION_ENV,
    "format": "full-lowercase-git-sha",
    "workspace_comparison": "git rev-parse HEAD",
}
REQUIREMENTS = {f"XCOM-PROV-{number:03d}" for number in range(1, 12)}
MEASURES = {
    "VM-XCOM-PROV-UNIT",
    "VM-XCOM-PROV-LINT",
    "VM-XCOM-PROV-STATIC",
    "VM-XCOM-PROV-INTEGRATION",
    "VM-XCOM-PROV-VALIDATION",
}
DESIGN_REQUIREMENTS = {
    "XCOM-PROV-UNIT-001": {"XCOM-PROV-001", "XCOM-PROV-002", "XCOM-PROV-007"},
    "XCOM-PROV-UNIT-002": {"XCOM-PROV-001", "XCOM-PROV-002", "XCOM-PROV-009", "XCOM-PROV-010"},
    "XCOM-PROV-UNIT-003": {"XCOM-PROV-003", "XCOM-PROV-004"},
    "XCOM-PROV-UNIT-004": {"XCOM-PROV-004", "XCOM-PROV-005", "XCOM-PROV-006"},
    "XCOM-PROV-UNIT-005": {"XCOM-PROV-005", "XCOM-PROV-006", "XCOM-PROV-007", "XCOM-PROV-009"},
    "XCOM-PROV-UNIT-006": {"XCOM-PROV-004", "XCOM-PROV-008", "XCOM-PROV-009"},
    "XCOM-PROV-UNIT-007": {"XCOM-PROV-010", "XCOM-PROV-011"},
}
DESIGN_SOURCE = "specs/014-feat-e17d4ee9f29848f5/unit-specifications.md"
OWNED_PREFIXES = ("src/xverse/xcom/", "tests/xcom/provider_loopback/")
OWNED_FILES = {
    "scripts/validate_xcom_provider_loopback.py",
    "scripts/validate_xcom_core_types.py",
    "scripts/validate_xcom_endpoint_route_lifecycle.py",
    "docs/xcom/provider-composition-loopback.md",
    "docs/xcom/provider-composition-loopback-traceability.json",
}
PRODUCTION = (
    CPP_ROOT / "include" / "xverse" / "xcom" / "provider.hpp",
    CPP_ROOT / "include" / "xverse" / "xcom" / "loopback_provider.hpp",
    CPP_ROOT / "src" / "provider.cpp",
    CPP_ROOT / "src" / "loopback_provider.cpp",
)
MUTATION_REJECTION_PROBE = TEST_ROOT / "consumer" / "provider_mutation_rejection.cpp"
CPP_CHECK_INPUTS = (
    *PRODUCTION,
    *(path for path in sorted(TEST_ROOT.rglob("*.cpp")) if path != MUTATION_REJECTION_PROBE),
)


class ValidationFailure(RuntimeError):
    """Represent one deterministic provider validation failure."""


def _fail(message: str) -> NoReturn:
    """Raise a classified gate failure."""

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
    """Return an available executable or fail closed."""

    path = shutil.which(name)
    if path is None:
        _fail(f"required executable is unavailable: {name}")
    return path


def _candidate_revision() -> str:
    """Validate the host-supplied candidate revision against unchanged HEAD."""

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
            _tool("cmake"), "-S", str(ROOT), "-B", str(build), "-G", "Ninja",
            "-DBUILD_TESTING=ON", "-DCMAKE_BUILD_TYPE=Debug",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        ]
    )


def _build(build: Path, targets: list[str]) -> None:
    """Build exact named targets in the disposable tree."""

    _run([_tool("cmake"), "--build", str(build), "--target", *targets, "--verbose"])


def _ctest(build: Path, expression: str) -> None:
    """Run exact CTest fixtures selected by an anchored expression."""

    _run([_tool("ctest"), "--test-dir", str(build), "--output-on-failure", "-R", expression])


def _check_owned_paths() -> None:
    """Reject changed paths outside this SESN task's ownership boundary."""

    changed = _run([_tool("git"), "diff", "--name-only", "--", "."]).stdout.splitlines()
    untracked = _run([_tool("git"), "ls-files", "--others", "--exclude-standard"]).stdout.splitlines()
    unexpected = sorted(
        path for path in set((*changed, *untracked))
        if path not in OWNED_FILES and not path.startswith(OWNED_PREFIXES)
    )
    if unexpected:
        _fail("changed paths exceed task ownership: " + ", ".join(unexpected))


def _check_layout_and_text() -> None:
    """Require every owned artifact and deterministic text formatting."""

    required = {
        *OWNED_FILES,
        "src/xverse/xcom/CMakeLists.txt",
        "src/xverse/xcom/include/xverse/xcom/provider.hpp",
        "src/xverse/xcom/include/xverse/xcom/loopback_provider.hpp",
        "src/xverse/xcom/src/provider.cpp",
        "src/xverse/xcom/src/loopback_provider.cpp",
        "tests/xcom/provider_loopback/test_support.hpp",
        "tests/xcom/provider_loopback/independent_provider.hpp",
        "tests/xcom/provider_loopback/unit_tests.cpp",
        "tests/xcom/provider_loopback/negative_tests.cpp",
        "tests/xcom/provider_loopback/consumer/main.cpp",
        "tests/xcom/provider_loopback/consumer/provider_mutation_rejection.cpp",
    }
    missing = sorted(path for path in required if not (ROOT / path).is_file())
    if missing:
        _fail("required provider artifacts are missing: " + ", ".join(missing))
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


def _check_provider_boundaries() -> None:
    """Reject dynamic storage, ambient access, excluded dependencies, and missing fixed bounds."""

    patterns = {
        r"#\s*include\s*[<\"](?:filesystem|fstream|cstdio|cstdlib|dlfcn|grpc|google/protobuf|nlohmann)":
            "forbidden external or ambient header",
        r"\b(?:getenv|system|popen|fork|exec[a-z]*|socket|connect|listen|accept|dlopen|dlsym)\s*\(":
            "ambient/process/network/dynamic-loader API",
        r"\bstd::(?:vector|deque|list|map|unordered_map|set|unordered_set)\b":
            "dynamic provider container",
        r"\boperator\s+new\b|\bnew\s+[A-Za-z_:][A-Za-z0-9_:<>]*\s*(?:\(|\{|\[)":
            "explicit dynamic allocation",
    }
    for path in PRODUCTION:
        text = path.read_text(encoding="utf-8")
        for pattern, label in patterns.items():
            if re.search(pattern, text):
                _fail(f"{label} found in {path.relative_to(ROOT)}")
    header = PRODUCTION[0].read_text(encoding="utf-8")
    loopback = PRODUCTION[1].read_text(encoding="utf-8")
    source = PRODUCTION[3].read_text(encoding="utf-8")
    required_tokens = (
        "static constexpr std::size_t kMaximumProviders = 8U",
        "std::array<std::optional<ProviderSlot>, kMaximumProviders>",
        "static constexpr std::size_t kMaximumRoutes = 4U",
        "static constexpr std::size_t kMaximumQueueItems = 8U",
        "std::array<std::optional<CommunicationItem>, kMaximumQueueItems>",
        "std::array<std::optional<RouteRecord>, kMaximumRoutes>",
    )
    for token in required_tokens[:2]:
        if token not in header:
            _fail(f"fixed provider-registry declaration differs: {token}")
    for token in required_tokens[2:]:
        if token not in loopback:
            _fail(f"fixed loopback declaration differs: {token}")
    if "std::lock_guard" not in source or "queue_saturated" not in source:
        _fail("serialized reject-new queue mechanics are absent")
    if "composition_instance_id" not in header or "descriptor_compatible" not in loopback:
        _fail("exact composition ownership or implementation descriptor gate is absent")


def _check_verification_repairs() -> None:
    """Require the independent, re-entry, negative-matrix, overlap, and regression fixtures."""

    independent = (TEST_ROOT / "independent_provider.hpp").read_text(encoding="utf-8")
    rejection_probe = MUTATION_REJECTION_PROBE.read_text(encoding="utf-8")
    unit = (TEST_ROOT / "unit_tests.cpp").read_text(encoding="utf-8")
    negative = (TEST_ROOT / "negative_tests.cpp").read_text(encoding="utf-8")
    required = {
        "independent provider implementation": (
            independent,
            "class IndependentProvider final : public CommunicationProvider",
        ),
        "external raw-mutation rejection probe": (
            rejection_probe,
            "XCOM_PROBE_RECONCILE",
        ),
        "registration re-entry probe": (unit, "test_registration_reentry"),
        "overlapping producer/consumer assertion": (unit, "overlap_observed"),
        "unique delivered-content assertion": (unit, "seen[sequence - 1U].exchange(true)"),
        "retained declaration matrix": (negative, "mismatched_routes"),
        "route/endpoint generation matrix": (negative, "test_prepare_generation_rejection"),
        "fresh pre-dispatch compatibility matrix": (
            negative,
            "test_fresh_prepare_rejection_matrix",
        ),
        "failed/closed/recreated activation matrix": (
            negative,
            "test_activation_rejection_matrix",
        ),
        "active route-capacity isolation": (
            negative,
            "test_route_capacity_after_activation",
        ),
        "item contract/schema/version/kind matrix": (negative, "mismatched_contract_items"),
        "pre-dispatch item no-mutation matrix": (
            negative,
            "test_fresh_submit_rejection_matrix",
        ),
        "exact diagnostic-byte matrix": (negative, "test_exact_provider_diagnostics"),
        "per-rejection queue no-mutation check": (
            negative,
            "item mismatch mutated the destination queue",
        ),
    }
    for label, (text, token) in required.items():
        if token not in text:
            _fail(f"verification repair is absent: {label}")
    validator_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_monkeypatches = (
        "module." + "OWNED_PREFIXES =",
        "module." + "OWNED_FILES =",
        "module." + "_cpp_files =",
        "module." + "_check_forbidden_cpp_apis =",
        "module." + "_run_repository_documentation_gate =",
        "module." + "_run_core_types_regression =",
    )
    present = [token for token in forbidden_monkeypatches if token in validator_text]
    if present:
        _fail("prior-validator monkeypatch remains: " + ", ".join(present))


def _check_external_mutation_rejection() -> None:
    """Compile one public control and reject each interface and concrete mutation access."""

    command = [
        _tool("c++"),
        "-std=c++20",
        "-Wall",
        "-Wextra",
        "-Wpedantic",
        "-Werror",
        "-I",
        str(CPP_ROOT / "include"),
        "-fsyntax-only",
        str(MUTATION_REJECTION_PROBE),
    ]
    _run([*command, "-DXCOM_PROBE_CONTROL"])
    probes = {
        "XCOM_PROBE_PREPARE": "prepare",
        "XCOM_PROBE_ACTIVATE": "activate",
        "XCOM_PROBE_SUBMIT": "submit",
        "XCOM_PROBE_RECEIVE": "receive",
        "XCOM_PROBE_DRAIN": "drain",
        "XCOM_PROBE_CLOSE": "close",
        "XCOM_PROBE_STATE": "state",
        "XCOM_PROBE_RECONCILE": "reconcile",
    }
    scopes = {
        "interface": [],
        "concrete": ["-DXCOM_PROBE_CONCRETE"],
    }
    for macro, operation in probes.items():
        for scope, scope_arguments in scopes.items():
            try:
                completed = subprocess.run(
                    [*command, f"-D{macro}", *scope_arguments],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                    timeout=120,
                )
            except (OSError, subprocess.TimeoutExpired) as error:
                _fail(
                    "provider mutation rejection probe could not complete: "
                    f"{macro}/{scope}: {error}"
                )
            diagnostics = completed.stdout.lower()
            if completed.returncode == 0:
                _fail(
                    f"external consumer compiled raw {scope} provider mutation: "
                    + operation
                )
            if "private" not in diagnostics or operation not in diagnostics:
                _fail(
                    f"external {scope} {operation} probe failed for an unrelated reason:\n"
                    + completed.stdout.rstrip()
                )


def _run_doxygen() -> None:
    """Generate strict warning-free Doxygen for the public provider contract."""

    _run([sys.executable, str(ROOT / "scripts" / "check_doxygen.py"), "--self-test"])
    with tempfile.TemporaryDirectory(prefix="xcom-provider-doxygen-") as temporary:
        temp = Path(temporary)
        output = temp / "output"
        warning_log = temp / "warnings.log"
        configuration = temp / "Doxyfile"
        inputs = (ROOT / "docs" / "xcom" / "provider-composition-loopback.md", *PRODUCTION)
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
            warnings = warning_log.read_text(encoding="utf-8") if warning_log.is_file() else ""
            _fail(f"strict Doxygen generation failed: {error}\n{warnings}")
        if warning_log.is_file() and warning_log.read_text(encoding="utf-8").strip():
            _fail("strict Doxygen warning log is not empty:\n" + warning_log.read_text(encoding="utf-8"))
        for relative in ("html/index.html", "xml/index.xml"):
            if not (output / relative).is_file():
                _fail(f"strict Doxygen output is missing: {relative}")


def _run_clang_tidy(build: Path) -> None:
    """Run admitted compiler diagnostics and analyzers on every provider C++ unit."""

    prefix = os.environ.get("XVERSE_XCOM_TOOLCHAIN", "")
    executable = Path(prefix).resolve() / "usr" / "bin" / "clang-tidy"
    if not prefix or not executable.is_file() or not os.access(executable, os.X_OK):
        _fail(f"admitted clang-tidy is unavailable: {executable}")
    for path in CPP_CHECK_INPUTS:
        _run(
            [str(executable), str(path), "-p", str(build),
             "--checks=-*,clang-diagnostic-*,clang-analyzer-*",
             "--warnings-as-errors=*", "--quiet"],
            timeout=120,
        )


def _check_binary_isolation(build: Path) -> None:
    """Reject forbidden dynamic symbols or linked transport/external libraries."""

    executable = build / "src" / "xverse" / "xcom" / "xverse_xcom_provider_loopback_consumer"
    symbols = _run([_tool("nm"), "-u", str(executable)]).stdout
    forbidden_symbols = re.compile(r"\b(?:socket|connect|listen|accept|dlopen|dlsym|system|popen|getenv)@")
    if forbidden_symbols.search(symbols):
        _fail("forbidden ambient or transport symbol is linked into provider consumer")
    dependencies = _run([_tool("ldd"), str(executable)]).stdout.lower()
    forbidden_dependencies = ("grpc", "protobuf", "ssl", "crypto", "curl", "zenoh", "someip")
    present = sorted(item for item in forbidden_dependencies if item in dependencies)
    if present:
        _fail("forbidden provider dependency linked: " + ", ".join(present))


def _validate_traceability(candidate_revision: str) -> None:
    """Validate reciprocal requirement/design/code/test/check edges and revision binding."""

    try:
        data = json.loads(TRACEABILITY.read_text(encoding="utf-8"))
        measure_records = json.loads(VERIFICATION_MEASURES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"traceability input cannot be read: {error}")
    if data.get("schema_version") != 1 or data.get("state") != "READY_FOR_REVIEW":
        _fail("traceability schema/state differs")
    if data.get("feature_id") != "FEAT-e17d4ee9f29848f5" or data.get("baseline_id") != "BASE-bef10959e1488206a1cc":
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
    records_by_id = {record.get("id"): record for record in records if isinstance(record, dict)}
    if set(records_by_id) != REQUIREMENTS or len(records) != len(REQUIREMENTS):
        _fail("traceability does not cover every requirement exactly once")
    if set(designs) != set(DESIGN_REQUIREMENTS):
        _fail("traceability design catalog differs")
    if not isinstance(measure_records, list):
        _fail("verification-measure catalog shape differs")
    measures_by_id = {item.get("id"): item for item in measure_records if isinstance(item, dict)}
    if set(measures_by_id) != MEASURES or len(measure_records) != len(MEASURES):
        _fail("authoritative verification-measure catalog differs")
    expected_checks = {requirement: set() for requirement in REQUIREMENTS}
    for measure_id, measure in measures_by_id.items():
        requirement_ids = measure.get("requirement_ids")
        if not isinstance(requirement_ids, list) or not requirement_ids or not set(requirement_ids) <= REQUIREMENTS:
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


def _load_validator(name: str, path: Path):
    """Load one preserved Python validator for integrated regression execution."""

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        _fail(f"accepted validator cannot be loaded: {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_lifecycle_regression() -> None:
    """Run the complete endpoint/route lifecycle validator on the integrated candidate."""

    module = _load_validator(
        "xcom_lifecycle_validator_provider",
        ROOT / "scripts" / "validate_xcom_endpoint_route_lifecycle.py",
    )
    arguments = ["--all"]
    for path in (
        "scripts/validate_xcom_core_types.py",
        "scripts/validate_xcom_provider_loopback.py",
        "tests/xcom/provider_loopback",
        "src/xverse/xcom/include/xverse/xcom/provider.hpp",
        "src/xverse/xcom/include/xverse/xcom/loopback_provider.hpp",
        "src/xverse/xcom/src/provider.cpp",
        "src/xverse/xcom/src/loopback_provider.cpp",
    ):
        arguments.extend(("--additive-owned-path", path))
    if module.main(arguments) != 0:
        _fail("accepted endpoint/route lifecycle validator rejected the integrated candidate")


def _unit(build: Path) -> None:
    """Build and run provider unit, negative, concurrency, and lifecycle tests."""

    _build(build, ["xverse_xcom_provider_loopback_unit_tests", "xverse_xcom_provider_loopback_negative_tests"])
    _ctest(build, "^xcom_provider_loopback_(unit|negative)$")


def _lint(build: Path) -> None:
    """Run ownership, formatting, isolation, fixed-storage, and warning gates."""

    _check_owned_paths()
    _check_layout_and_text()
    _check_provider_boundaries()
    _check_verification_repairs()
    _check_external_mutation_rejection()
    _build(build, ["xverse_xcom_provider_loopback", "xverse_xcom_provider_loopback_unit_tests",
                   "xverse_xcom_provider_loopback_negative_tests", "xverse_xcom_provider_loopback_consumer"])


def _static(build: Path, candidate_revision: str) -> None:
    """Run analyzer, strict Doxygen, symbols, storage, and traceability gates."""

    _build(build, ["xverse_xcom_provider_loopback", "xverse_xcom_provider_loopback_consumer"])
    _run_clang_tidy(build)
    _run_doxygen()
    _check_provider_boundaries()
    _check_verification_repairs()
    _check_binary_isolation(build)
    _validate_traceability(candidate_revision)


def _integration(build: Path) -> None:
    """Build and run the full separate public API consumer."""

    _build(build, ["xverse_xcom_provider_loopback_consumer"])
    _check_external_mutation_rejection()
    _ctest(build, "^xcom_provider_loopback_external_consumer$")


def main(arguments: list[str] | None = None) -> int:
    """Select and execute one or every declared SESN verification measure."""

    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--unit", action="store_true")
    selection.add_argument("--lint", action="store_true")
    selection.add_argument("--static", action="store_true")
    selection.add_argument("--integration", action="store_true")
    selection.add_argument("--all", action="store_true")
    args = parser.parse_args(arguments)
    try:
        candidate_revision = _candidate_revision()
        with tempfile.TemporaryDirectory(prefix="xcom-provider-") as temporary:
            build = Path(temporary) / "build"
            _configure(build)
            if args.unit or args.all:
                _unit(build)
            if args.lint or args.all:
                _lint(build)
            if args.static or args.all:
                _static(build, candidate_revision)
            if args.integration or args.all:
                _integration(build)
            if args.all:
                _run_lifecycle_regression()
                _validate_traceability(candidate_revision)
    except ValidationFailure as error:
        print(f"X-COM provider-loopback validation failed: {error}", file=sys.stderr)
        return 1
    selected = next(name for name in ("unit", "lint", "static", "integration", "all") if getattr(args, name))
    print(f"X-COM provider-loopback {selected} validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
