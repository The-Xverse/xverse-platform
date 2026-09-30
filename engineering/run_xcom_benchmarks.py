#!/usr/bin/env python3
"""T036 controlled disabled/enabled observation-tap benchmark harness.

This repository-owned harness drives the *accepted* owned-loopback and
observation boundaries (read-only) and records the disabled (same-baseline) and
enabled observation-tap results with environment, uncertainty, raw paired
samples, method, explicit non-production limitations, and an exact-candidate
binding in ``reports/xcom-queue/t036-benchmark.json``.

The harness adds no byte to any accepted production source, header, contract,
schema, register, XDL profile, accepted test, target, label, command, or
expected value. It compiles the accepted sources and a task-owned measurement
driver into an isolated temporary benchmark build, runs it locally/offline, and
uses only the standard library and the admitted offline toolchain.

Subcommands
-----------
``--report PATH`` (default ``reports/xcom-queue/t036-benchmark.json``)
    Run the controlled benchmark, write the evidence report, and exit ``0`` only
    when both SC-008 (tap-disabled versus same-baseline) median comparisons are
    within the accepted 2% threshold.

``--verify PATH``
    Re-read the report and exit ``0`` only when the required fields, method,
    uncertainty, candidate binding, artifact hashes, and raw samples are present
    and internally consistent and the 2% threshold holds; otherwise it exits
    nonzero.

Exact-candidate revision contract
---------------------------------
A committed report cannot contain its own commit hash (writing the hash would
change the commit), so the report binds the exact candidate by
``baseline_revision`` plus the sorted material-input inventory, the
``material_digest``, and the per-file ``hashes``. ``--verify`` accepts exactly
two revisions for that binding: ``HEAD == baseline_revision`` (the measured
working-tree successor, before the reviewed files are committed) and ``HEAD``
as the *direct child* of ``baseline_revision`` (the committed candidate). Every
other revision -- a foreign commit, an unrelated history, or an extra successor
commit -- is rejected. The material digest and hashes are unchanged, so any
changed candidate material still fails closed.

The measurement kernel is single-threaded, offline, and opens no network
listener, ``AF_INET``/``AF_INET6`` socket, DNS, resolver, TLS, external peer,
legacy binary, or production workload.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_REPORT = REPO_ROOT / "reports/xcom-queue/t036-benchmark.json"
DEFAULT_BUILD = REPO_ROOT / "build/f8bench"

TASK_ID = "T036"
CAPABILITY = "007"
THRESHOLD_PERCENT = 2.0
PAIRED_SAMPLES = 21
ITERATIONS_PER_SAMPLE = 5000
WARMUP_RUNS = 1
OPTIMIZATION = "-O2"
CXX_STANDARD = "-std=c++20"

# The admitted T011/T025 offline inputs are resolved by name only; the harness
# never commits or prints a host-specific absolute path.
ADMITTED_INPUTS = {
    "XVERSE_XCOM_TOOLCHAIN": "directory",
    "XVERSE_XCOM_PACKAGE_MANIFEST": "file",
    "XVERSE_XCOM_T025_TEST_TOOLCHAIN": "directory",
}

# Accepted read-only sources compiled into the isolated benchmark build.
ACCEPTED_SOURCES = (
    "src/xverse/xcom/src/contract.cpp",
    "src/xverse/xcom/src/diagnostic.cpp",
    "src/xverse/xcom/src/item.cpp",
    "src/xverse/xcom/src/value.cpp",
    "src/xverse/xcom/src/observation.cpp",
    "src/xverse/xcom/src/endpoint_route_lifecycle.cpp",
    "src/xverse/xcom/src/provider.cpp",
    "src/xverse/xcom/src/loopback_provider.cpp",
)
INCLUDE_DIRS = (
    "src/xverse/xcom/include",
    "tests/xcom/observation/integration",
)

# Candidate material inputs bound into the report. Human-readable run records
# (implementation.md, review-index.md) and the report itself are intentionally
# excluded so the binding is acyclic and reproducible.
MATERIAL_GLOBS = (
    "docs/engineering/xcom/t010/design-units.md",
    "docs/engineering/xcom/t010/unit-design.json",
    "docs/engineering/xcom/t036/architecture.md",
    "docs/engineering/xcom/t036/detailed-design.md",
    "docs/engineering/xcom/t036/requirements.md",
    "docs/engineering/xcom/t036/unit-specifications.md",
    "docs/engineering/xcom/t036/verification-plan.md",
    "engineering/architecture/components/T036-SR-*-CMP.json",
    "engineering/project.json",
    "engineering/requirements/T036-*.json",
    "engineering/run_xcom_benchmarks.py",
    "engineering/trace/links.json",
    "engineering/unit-specifications/T036-SR-*-U.json",
    "engineering/validation/scenarios/T036-VS-ACCUMULATED.json",
    "specs/007-xcom-core/tasks.md",
)

DRIVER_SOURCE = r"""/**
 * @file t036_benchmark_driver.cpp
 * @brief Task-owned T036 measurement driver over the accepted owned loopback and observation boundaries.
 *
 * Generated into an isolated temporary benchmark build by
 * engineering/run_xcom_benchmarks.py; never committed. It measures three cases
 * on the same owned-loopback workload: the admitted pre-observation submit
 * (baseline), the public submit with observation disabled (tap_disabled), and
 * the public submit with a bounded observation tap attached (tap_enabled).
 * Measurement is single-threaded; the process opens no network resource.
 */
#include "test_support.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <memory>
#include <vector>

namespace xverse::xcom {

/** BUILD_TESTING-only friend that invokes the pinned pre-observation submit implementation. */
class ObservationDisabledBenchmarkAccess final {
 public:
  [[nodiscard]] static ProviderStatus submit(
      ProviderComposition& composition, const ProviderRouteHandle& handle,
      const CommunicationItem& item, const LifecycleController& lifecycle) noexcept {
    return composition.submit_disabled_observation_baseline(handle, item, lifecycle);
  }
};

}  // namespace xverse::xcom

namespace {

using namespace xverse::xcom;
using xverse::xcom::observation_test::Scenario;
using xverse::xcom::observation_test::make_tap_spec;

/** Measurement case selected for one timed sample. */
enum class Case : std::uint8_t { baseline, disabled, enabled };

/** @return Compile-time target description without ambient environment access. */
[[nodiscard]] constexpr const char* target_name() noexcept {
#if defined(__linux__) && defined(__x86_64__)
  return "linux-x86_64";
#elif defined(__linux__)
  return "linux-other";
#else
  return "non-linux";
#endif
}

/**
 * @brief Time one case over a fixed iteration count on one owned loopback route.
 * @param scenario Ready fixture scenario.
 * @param item Reused immutable route-bound item.
 * @param measured_case Case to time.
 * @param iterations Fixed submit/receive pair count.
 * @return Mean operation-pair latency in nanoseconds, or infinity on failure.
 */
[[nodiscard]] double run_sample(Scenario& scenario, const CommunicationItem& item,
                                const Case measured_case, const std::size_t iterations) {
  const auto start = std::chrono::steady_clock::now();
  std::uint64_t checksum = 0U;
  for (std::size_t i = 0U; i < iterations; ++i) {
    const ProviderStatus submitted =
        measured_case == Case::baseline
            ? ObservationDisabledBenchmarkAccess::submit(
                  scenario.composition(), scenario.provider_handle(), item, scenario.lifecycle())
            : scenario.composition().submit(scenario.provider_handle(), item, scenario.lifecycle());
    const auto received =
        scenario.composition().receive(scenario.provider_handle(), scenario.lifecycle());
    if (submitted.outcome() != ProviderOutcome::accepted || !received.has_value()) {
      return std::numeric_limits<double>::infinity();
    }
    checksum += static_cast<std::uint64_t>(received.value()->payload().size());
  }
  const auto stop = std::chrono::steady_clock::now();
  if (checksum != static_cast<std::uint64_t>(iterations) * item.payload().size()) {
    return std::numeric_limits<double>::infinity();
  }
  return std::chrono::duration<double, std::nano>(stop - start).count() /
         static_cast<double>(iterations);
}

/** @param value Raw sample nanoseconds. @return Reproducible single-line decimal text. */
[[nodiscard]] std::string_view finite_text(const double value) noexcept {
  return std::isfinite(value) ? std::string_view{"finite"} : std::string_view{"nonfinite"};
}

}  // namespace

/** @return Zero only when every case ran and produced finite samples. */
int main(int argc, char** argv) {
  if (argc != 3) {
    std::cerr << "usage: t036_benchmark_driver PAIRED_SAMPLES ITERATIONS_PER_SAMPLE\n";
    return 2;
  }
  const auto paired_samples = static_cast<std::size_t>(std::strtoull(argv[1], nullptr, 10));
  const auto iterations = static_cast<std::size_t>(std::strtoull(argv[2], nullptr, 10));
  if (paired_samples == 0U || iterations == 0U) {
    std::cerr << "invalid sample configuration\n";
    return 2;
  }

  auto baseline = std::make_unique<Scenario>("bench.a", InteractionKind::message_event, 1U);
  auto disabled = std::make_unique<Scenario>("bench.b", InteractionKind::message_event, 1U);
  auto hub = std::make_unique<ObservationHub>();
  auto enabled =
      std::make_unique<Scenario>("bench.c", InteractionKind::message_event, 1U, hub.get());
  const auto baseline_item = baseline->item(1U, 1U);
  const auto disabled_item = disabled->item(1U, 1U);
  const auto enabled_item = enabled->item(1U, 1U);
  if (!baseline->ready() || !disabled->ready() || !enabled->ready() ||
      !baseline_item.has_value() || !disabled_item.has_value() || !enabled_item.has_value()) {
    std::cerr << "benchmark setup failed\n";
    return 1;
  }
  const auto spec = make_tap_spec({}, ObservationPayloadMode::metadata_only, 0U, 16U,
                                  ObservationOverflowPolicy::drop_newest);
  const auto attached = hub->attach(spec);
  if (!attached.status.succeeded() || !attached.handle.has_value()) {
    std::cerr << "observation tap attach failed\n";
    return 1;
  }
  const ObservationTapHandle tap = *attached.handle;

  static_cast<void>(run_sample(*baseline, *baseline_item.value(), Case::baseline, iterations));
  static_cast<void>(run_sample(*disabled, *disabled_item.value(), Case::disabled, iterations));
  static_cast<void>(run_sample(*enabled, *enabled_item.value(), Case::enabled, iterations));

  std::vector<double> baseline_latency;
  std::vector<double> disabled_latency;
  std::vector<double> enabled_latency;
  baseline_latency.reserve(paired_samples);
  disabled_latency.reserve(paired_samples);
  enabled_latency.reserve(paired_samples);

  for (std::size_t sample = 0U; sample < paired_samples; ++sample) {
    double b = 0.0;
    double d = 0.0;
    double e = 0.0;
    if (sample % 2U == 0U) {
      b = run_sample(*baseline, *baseline_item.value(), Case::baseline, iterations);
      d = run_sample(*disabled, *disabled_item.value(), Case::disabled, iterations);
      e = run_sample(*enabled, *enabled_item.value(), Case::enabled, iterations);
    } else {
      e = run_sample(*enabled, *enabled_item.value(), Case::enabled, iterations);
      d = run_sample(*disabled, *disabled_item.value(), Case::disabled, iterations);
      b = run_sample(*baseline, *baseline_item.value(), Case::baseline, iterations);
    }
    if (!std::isfinite(b) || !std::isfinite(d) || !std::isfinite(e)) {
      std::cerr << "benchmark route operation failed\n";
      return 1;
    }
    baseline_latency.push_back(b);
    disabled_latency.push_back(d);
    enabled_latency.push_back(e);
    // Drain the bounded tap so retention stays within its fixed capacity; this
    // does not affect the timed loop above.
    while (hub->poll(tap).status.succeeded()) {
    }
  }

  std::cout << "fixture=owned-loopback-disabled-enabled-observation\n"
            << "target=" << target_name() << '\n'
            << "compiler=" << __VERSION__ << '\n'
            << "steady_clock=" << (std::chrono::steady_clock::is_steady ? "true" : "false") << '\n'
            << "paired_samples=" << paired_samples << '\n'
            << "iterations_per_sample=" << iterations << '\n'
            << "pair_order=alternating\n";
  for (std::size_t sample = 0U; sample < paired_samples; ++sample) {
    std::cout << "sample[" << sample << "].baseline_latency_ns=" << baseline_latency[sample]
              << " status=" << finite_text(baseline_latency[sample]) << '\n'
              << "sample[" << sample << "].disabled_latency_ns=" << disabled_latency[sample]
              << " status=" << finite_text(disabled_latency[sample]) << '\n'
              << "sample[" << sample << "].enabled_latency_ns=" << enabled_latency[sample]
              << " status=" << finite_text(enabled_latency[sample]) << '\n';
  }
  std::cout << "ok=true\n";
  return 0;
}
"""


class HarnessError(RuntimeError):
    """Stable harness failure with a public-safe message."""


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


def resolve_admitted() -> dict[str, dict[str, object]]:
    """Resolve and fingerprint the admitted offline inputs by environment name."""
    resolved: dict[str, dict[str, object]] = {}
    for name, kind in ADMITTED_INPUTS.items():
        raw = os.environ.get(name)
        if not raw:
            raise HarnessError(
                f"admitted offline input is unavailable: set {name} (no host path is recorded)"
            )
        path = pathlib.Path(raw)
        if kind == "file":
            if not path.is_file():
                raise HarnessError(f"admitted offline input {name} is not a readable file")
            resolved[name] = {"kind": "file", "sha256": sha256_file(path), "files": 1}
        else:
            if not path.is_dir():
                raise HarnessError(f"admitted offline input {name} is not a readable directory")
            digest, count = tree_digest(path)
            resolved[name] = {"kind": "directory", "sha256": digest, "files": count}
    manifest = str(resolved["XVERSE_XCOM_PACKAGE_MANIFEST"]["sha256"])
    if manifest != "9879911b35058e8c8e0ee78ad5faef258c34d9e490b78b2121d6b9565c92945c":
        raise HarnessError("admitted offline package manifest digest changed")
    return resolved


def tool_identity() -> dict[str, str]:
    def first_line(*argv: str) -> str:
        try:
            result = subprocess.run(argv, text=True, capture_output=True, check=False, timeout=30)
        except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - defensive
            raise HarnessError(f"tool unavailable: {argv[0]}") from exc
        if result.returncode != 0:
            raise HarnessError(f"tool failed: {argv[0]}")
        return result.stdout.splitlines()[0].strip() if result.stdout.strip() else "unknown"

    return {
        "compiler": first_line("g++", "--version"),
        "cxx_standard": "c++20 warning-as-error (T012)",
        "cmake": first_line("cmake", "--version").replace("cmake version ", ""),
        "ninja": first_line("ninja", "--version"),
        "python": sys.version.split()[0],
        "target": "linux-x86_64" if sys.platform.startswith("linux") else sys.platform,
    }


def material_paths() -> list[str]:
    found: set[str] = set()
    for pattern in MATERIAL_GLOBS:
        for match in REPO_ROOT.glob(pattern):
            if match.is_file():
                found.add(match.relative_to(REPO_ROOT).as_posix())
    missing = [
        pattern
        for pattern in MATERIAL_GLOBS
        if not any(REPO_ROOT.glob(pattern)) and "*" not in pattern
    ]
    if missing:
        raise HarnessError(f"candidate material input is missing: {missing}")
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
        raise HarnessError("cannot determine the candidate revision") from exc
    revision = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise HarnessError("cannot determine the candidate revision")
    return revision


def git_parent(revision: str) -> str | None:
    """Return the first parent commit of ``revision``, or ``None`` when absent."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{revision}^"], cwd=REPO_ROOT, text=True,
            capture_output=True, check=False, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - defensive
        raise HarnessError("cannot inspect the candidate revision") from exc
    parent = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", parent):
        return None
    return parent


def git_commits_ahead(baseline: str, revision: str) -> int | None:
    """Count commits reachable from ``revision`` but not from ``baseline``."""
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", f"{baseline}..{revision}"], cwd=REPO_ROOT, text=True,
            capture_output=True, check=False, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - defensive
        raise HarnessError("cannot inspect the candidate revision") from exc
    value = result.stdout.strip()
    if result.returncode != 0 or not value.isdigit():
        return None
    return int(value)


def median(values: list[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2 == 0:
        return (ordered[middle - 1] + ordered[middle]) / 2.0
    return ordered[middle]


def mad(values: list[float], centre: float) -> float:
    return median([abs(value - centre) for value in values])


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise HarnessError("no samples for percentile")
    index = min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def finite(value: float) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def compile_driver(driver: pathlib.Path, executable: pathlib.Path) -> list[str]:
    compiler = shutil.which("g++")
    if compiler is None:
        raise HarnessError("admitted C++ compiler g++ is unavailable")
    argv = [
        compiler,
        CXX_STANDARD,
        OPTIMIZATION,
        "-Wall",
        "-Wextra",
        "-Wpedantic",
        "-Werror",
        "-DXVERSE_XCOM_ENABLE_DISABLED_OBSERVATION_BENCHMARK=1",
    ]
    for directory in INCLUDE_DIRS:
        argv.extend(["-I", str(REPO_ROOT / directory)])
    argv.append(str(driver))
    for source in ACCEPTED_SOURCES:
        source_path = REPO_ROOT / source
        if not source_path.is_file():
            raise HarnessError(f"accepted benchmark source is missing: {source}")
        argv.append(str(source_path))
    argv.extend(["-lpthread", "-o", str(executable)])
    result = subprocess.run(argv, cwd=REPO_ROOT, text=True, capture_output=True, check=False,
                            timeout=600)
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).strip().splitlines()
        tail = detail[-1] if detail else "no diagnostic"
        raise HarnessError(f"the isolated benchmark build failed: {tail}")
    return argv


def parse_driver_output(text: str) -> list[dict[str, float]]:
    values: dict[str, str] = {}
    samples: dict[int, dict[str, float]] = {}
    line_re = re.compile(r"^sample\[(\d+)\]\.([a-z_]+)=(.*?)(?: status=.*)?$")
    for line in text.splitlines():
        match = line_re.match(line)
        if match:
            index = int(match.group(1))
            samples.setdefault(index, {})[match.group(2)] = float(match.group(3))
            continue
        key, sep, value = line.partition("=")
        if sep:
            values[key] = value
    if values.get("ok") != "true":
        raise HarnessError("the benchmark driver did not report a complete run")
    if not samples:
        raise HarnessError("the benchmark driver produced no samples")
    ordered = [samples[index] for index in sorted(samples)]
    for sample in ordered:
        if not all(finite(sample.get(key, math.nan)) for key in
                   ("baseline_latency_ns", "disabled_latency_ns", "enabled_latency_ns")):
            raise HarnessError("the benchmark driver produced a non-finite sample")
    return ordered


def summarize(latencies: list[float]) -> dict[str, float]:
    centre = median(latencies)
    return {
        "n": len(latencies),
        "median_latency_ns": centre,
        "mad_ns": mad(latencies, centre),
        "min_latency_ns": min(latencies),
        "max_latency_ns": max(latencies),
        "p95_latency_ns": percentile(latencies, 0.95),
        "median_throughput_per_s": 1_000_000_000.0 / centre,
    }


def disabled_regressions(samples: list[dict[str, float]]) -> dict[str, list[float]]:
    latency: list[float] = []
    throughput: list[float] = []
    for sample in samples:
        baseline_latency = sample["baseline_latency_ns"]
        disabled_latency = sample["disabled_latency_ns"]
        latency.append((disabled_latency / baseline_latency - 1.0) * 100.0)
        baseline_throughput = 1_000_000_000.0 / baseline_latency
        disabled_throughput = 1_000_000_000.0 / disabled_latency
        throughput.append((1.0 - disabled_throughput / baseline_throughput) * 100.0)
    return {"latency": latency, "throughput": throughput}


def enabled_regressions(samples: list[dict[str, float]]) -> dict[str, list[float]]:
    latency: list[float] = []
    throughput: list[float] = []
    for sample in samples:
        disabled_latency = sample["disabled_latency_ns"]
        enabled_latency = sample["enabled_latency_ns"]
        latency.append((enabled_latency / disabled_latency - 1.0) * 100.0)
        disabled_throughput = 1_000_000_000.0 / disabled_latency
        enabled_throughput = 1_000_000_000.0 / enabled_latency
        throughput.append((1.0 - enabled_throughput / disabled_throughput) * 100.0)
    return {"latency": latency, "throughput": throughput}


def build_report(samples: list[dict[str, float]], environment: dict[str, object],
                 tool: dict[str, str], material: list[str]) -> dict[str, object]:
    baseline_latency = [sample["baseline_latency_ns"] for sample in samples]
    disabled_latency = [sample["disabled_latency_ns"] for sample in samples]
    enabled_latency = [sample["enabled_latency_ns"] for sample in samples]
    baseline = summarize(baseline_latency)
    disabled = summarize(disabled_latency)
    enabled = summarize(enabled_latency)

    disabled_pair = disabled_regressions(samples)
    enabled_pair = enabled_regressions(samples)
    disabled_latency_regression = median(disabled_pair["latency"])
    disabled_throughput_regression = median(disabled_pair["throughput"])
    enabled_latency_regression = median(enabled_pair["latency"])
    enabled_throughput_regression = median(enabled_pair["throughput"])

    latency_pass = disabled_latency_regression <= THRESHOLD_PERCENT
    throughput_pass = disabled_throughput_regression <= THRESHOLD_PERCENT
    outcome = "pass" if latency_pass and throughput_pass else "failed"

    revision = git_head()
    candidate_identity = {
        "candidate_kind": (
            "working-tree successor of the accepted baseline, measured with HEAD == "
            "baseline_revision and committed as the direct child of baseline_revision that "
            "carries this exact material digest"
        ),
        "revision_binding": (
            "a committed report cannot reference its own commit hash, so the exact candidate is "
            "bound by baseline_revision plus the sorted material-input inventory, the material "
            "digest, and the per-file hashes; --verify accepts HEAD == baseline_revision (the "
            "measured working-tree successor) or HEAD as the direct child of baseline_revision "
            "(the committed candidate) and rejects every other revision"
        ),
        "baseline_revision": revision,
        "candidate_revision": None,
        "material_digest": material_digest(material),
        "material_input_digest_method": (
            "sha256 over sorted '<relative path>\\0<file sha256>\\n' for each candidate material input"
        ),
        "material_inputs": material,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    hashes = {path: sha256_file(REPO_ROOT / path) for path in material}

    sample_table = []
    for index, sample in enumerate(samples):
        baseline_latency = sample["baseline_latency_ns"]
        disabled_latency = sample["disabled_latency_ns"]
        enabled_latency = sample["enabled_latency_ns"]
        sample_table.append(
            {
                "index": index,
                "baseline_latency_ns": baseline_latency,
                "disabled_latency_ns": disabled_latency,
                "enabled_latency_ns": enabled_latency,
                "baseline_throughput_per_s": 1_000_000_000.0 / baseline_latency,
                "disabled_throughput_per_s": 1_000_000_000.0 / disabled_latency,
                "enabled_throughput_per_s": 1_000_000_000.0 / enabled_latency,
                "disabled_latency_regression_percent": disabled_pair["latency"][index],
                "disabled_throughput_regression_percent": disabled_pair["throughput"][index],
                "enabled_latency_regression_percent": enabled_pair["latency"][index],
                "enabled_throughput_regression_percent": enabled_pair["throughput"][index],
            }
        )

    return {
        "schema_version": 1,
        "task_id": TASK_ID,
        "capability": CAPABILITY,
        "baseline_revision": revision,
        "candidate_revision": None,
        "candidate_identity": candidate_identity,
        "method": {
            "workload": "owned-loopback observation-tap disabled/enabled",
            "harness": "engineering/run_xcom_benchmarks.py",
            "accepted_sources": list(ACCEPTED_SOURCES),
            "build": {"standard": CXX_STANDARD, "optimization": OPTIMIZATION,
                      "warnings_as_errors": True, "isolated_build": "temporary directory"},
            "warmup_runs": WARMUP_RUNS,
            "paired_samples": PAIRED_SAMPLES,
            "iterations_per_sample": ITERATIONS_PER_SAMPLE,
            "pair_order": "alternating",
            "clock": "steady_clock",
            "single_threaded": True,
            "statistics": ["median", "min", "max", "p95", "mad"],
            "regression_statistic": "median of paired per-sample regressions",
        },
        "environment": {
            "compiler": tool["compiler"],
            "cxx_standard": tool["cxx_standard"],
            "cmake": tool["cmake"],
            "ninja": tool["ninja"],
            "python": tool["python"],
            "target": tool["target"],
            "admitted_inputs": environment,
        },
        "uncertainty": {
            "baseline": {key: baseline[key] for key in
                         ("n", "median_latency_ns", "mad_ns", "min_latency_ns", "max_latency_ns",
                          "p95_latency_ns")},
            "tap_disabled": {key: disabled[key] for key in
                             ("n", "median_latency_ns", "mad_ns", "min_latency_ns", "max_latency_ns",
                              "p95_latency_ns")},
            "tap_enabled": {key: enabled[key] for key in
                            ("n", "median_latency_ns", "mad_ns", "min_latency_ns", "max_latency_ns",
                             "p95_latency_ns")},
            "note": ("single-process steady-clock samples on a shared, uncontrolled host; this is a "
                     "dispersion declaration, not a production confidence interval"),
        },
        "baseline": {
            "case": "tap_disabled_same_baseline",
            "median_latency_ns": baseline["median_latency_ns"],
            "median_throughput_per_s": baseline["median_throughput_per_s"],
        },
        "tap_disabled": {
            "median_latency_ns": disabled["median_latency_ns"],
            "median_throughput_per_s": disabled["median_throughput_per_s"],
        },
        "tap_enabled": {
            "median_latency_ns": enabled["median_latency_ns"],
            "median_throughput_per_s": enabled["median_throughput_per_s"],
        },
        "regression": {
            "threshold_percent": THRESHOLD_PERCENT,
            "basis": ("SC-008: observation tap disabled (tap_disabled) versus the same owned-loopback "
                      "baseline; the plan performance goal bounds disabled taps"),
            "latency_regression_percent": disabled_latency_regression,
            "throughput_regression_percent": disabled_throughput_regression,
            "latency_pass": latency_pass,
            "throughput_pass": throughput_pass,
            "outcome": outcome,
            "tap_enabled_observation": {
                "basis": ("tap_enabled versus tap_disabled over the identical workload; recorded as the "
                          "observed enabled-tap overhead. SC-008 does not gate the enabled case."),
                "latency_regression_percent": enabled_latency_regression,
                "throughput_regression_percent": enabled_throughput_regression,
                "within_2_percent": (enabled_latency_regression <= THRESHOLD_PERCENT
                                     and enabled_throughput_regression <= THRESHOLD_PERCENT),
                "gated": False,
            },
        },
        "samples": sample_table,
        "hashes": hashes,
        "limitations": [
            "controlled prototype benchmark only; not a production performance, timing, transport, or "
            "compatibility claim",
            "CPU affinity, scheduler load, DVFS, thermal state, and cache state are uncontrolled on a "
            "shared host",
            "the uncertainty statement records observed dispersion and is not a production confidence "
            "interval",
            "the admitted offline envelope cannot link the gRPC transport runtime (T032-GAP-01); the "
            "workload is the in-process owned loopback and observation boundary only",
            "the enabled-tap case is recorded as an observed overhead and is not gated by the SC-008 2% "
            "disabled-tap threshold",
            "no Doxygen (T037), traceability-verifier/SADS (T038), external review (T039/T040), or user "
            "acceptance (T041) result is produced or claimed",
            "this report is bound to the exact candidate material digest and is not evidence for another "
            "revision",
        ],
        "blockers": [],
    }


def run_benchmark(report_path: pathlib.Path) -> int:
    environment = resolve_admitted()
    tool = tool_identity()
    material = material_paths()
    temporary = pathlib.Path(tempfile.mkdtemp(prefix="t036-benchmark-"))
    try:
        driver = temporary / "t036_benchmark_driver.cpp"
        executable = temporary / "t036_benchmark_driver"
        driver.write_text(DRIVER_SOURCE, encoding="utf-8")
        compile_driver(driver, executable)
        result = subprocess.run(
            [str(executable), str(PAIRED_SAMPLES), str(ITERATIONS_PER_SAMPLE)],
            cwd=str(temporary), text=True, capture_output=True, check=False, timeout=900,
        )
        if result.returncode != 0:
            detail = (result.stdout + result.stderr).strip().splitlines()
            tail = detail[-1] if detail else "no diagnostic"
            raise HarnessError(f"the benchmark run failed: {tail}")
        samples = parse_driver_output(result.stdout)
        report = build_report(samples, environment, tool, material)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n",
                               encoding="utf-8")
        outcome = report["regression"]["outcome"]
        print(json.dumps({"ok": outcome == "pass", "task_id": TASK_ID, "report": str(report_path),
                          "outcome": outcome,
                          "latency_regression_percent":
                              report["regression"]["latency_regression_percent"],
                          "throughput_regression_percent":
                              report["regression"]["throughput_regression_percent"]}))
        return 0 if outcome == "pass" else 1
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


REQUIRED_FIELDS = (
    "schema_version", "task_id", "capability", "baseline_revision", "candidate_revision",
    "candidate_identity", "method", "environment", "uncertainty", "baseline", "tap_disabled",
    "tap_enabled", "regression", "samples", "hashes", "limitations",
)
NON_PRODUCTION_MARKERS = ("not a production", "prototype", "non-production")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HarnessError(message)


def verify_report(report_path: pathlib.Path) -> int:
    require(report_path.is_file(), f"the benchmark report is missing: {report_path}")
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise HarnessError("the benchmark report is not valid JSON") from exc
    for field in REQUIRED_FIELDS:
        require(field in report, f"the benchmark report is missing the required field '{field}'")
    require(report["schema_version"] == 1, "unexpected schema version")
    require(report["task_id"] == TASK_ID, "the report belongs to another task")
    require(report["capability"] == CAPABILITY, "the report belongs to another capability")

    method = report["method"]
    for field in ("workload", "warmup_runs", "paired_samples", "iterations_per_sample", "pair_order",
                  "clock", "statistics"):
        require(field in method, f"the benchmark method is missing '{field}'")
    require(method["paired_samples"] == PAIRED_SAMPLES, "unexpected paired-sample count")
    require(method["iterations_per_sample"] == ITERATIONS_PER_SAMPLE, "unexpected iteration count")
    require(method["pair_order"] == "alternating", "unexpected pair order")

    uncertainty = report["uncertainty"]
    for case in ("baseline", "tap_disabled", "tap_enabled"):
        require(case in uncertainty, f"the uncertainty statement is missing '{case}'")
        for field in ("n", "median_latency_ns", "mad_ns"):
            require(field in uncertainty[case], f"the '{case}' uncertainty is missing '{field}'")
        require(uncertainty[case]["n"] == method["paired_samples"],
                f"the '{case}' uncertainty has the wrong sample count")
    note = str(uncertainty.get("note", "")).lower()
    require("not a production" in note or "confidence interval" in note,
            "the uncertainty statement lacks an explicit non-production note")

    samples = report["samples"]
    require(isinstance(samples, list) and len(samples) == method["paired_samples"],
            "the raw sample set is absent or has the wrong length")
    for index, sample in enumerate(samples):
        require(sample.get("index") == index, "the raw sample indices are not contiguous")
        for field in ("baseline_latency_ns", "disabled_latency_ns", "enabled_latency_ns"):
            require(finite(sample.get(field, math.nan)), f"sample {index} has a non-finite {field}")

    recomputed = disabled_regressions(samples)
    latency_regression = median(recomputed["latency"])
    throughput_regression = median(recomputed["throughput"])
    regression = report["regression"]
    require(abs(latency_regression - regression["latency_regression_percent"]) <= 1e-6,
            "the reported latency regression is inconsistent with the raw samples")
    require(abs(throughput_regression - regression["throughput_regression_percent"]) <= 1e-6,
            "the reported throughput regression is inconsistent with the raw samples")
    threshold = regression["threshold_percent"]
    require(threshold == THRESHOLD_PERCENT, "unexpected threshold")
    require(regression["latency_pass"] == (latency_regression <= threshold),
            "the latency threshold verdict is inconsistent")
    require(regression["throughput_pass"] == (throughput_regression <= threshold),
            "the throughput threshold verdict is inconsistent")
    require(regression["outcome"] in {"pass", "failed", "blocked"}, "invalid regression outcome")
    require(regression["outcome"] == "pass",
            "the benchmark did not satisfy the accepted 2% disabled-tap threshold")
    require(median([s["baseline_latency_ns"] for s in samples])
            == report["baseline"]["median_latency_ns"],
            "the reported baseline median is inconsistent with the raw samples")
    require(median([s["disabled_latency_ns"] for s in samples])
            == report["tap_disabled"]["median_latency_ns"],
            "the reported disabled median is inconsistent with the raw samples")
    require(median([s["enabled_latency_ns"] for s in samples])
            == report["tap_enabled"]["median_latency_ns"],
            "the reported enabled median is inconsistent with the raw samples")

    limitations = report["limitations"]
    require(isinstance(limitations, list) and limitations, "the report declares no limitations")
    require(any(marker in " ".join(limitations).lower() for marker in NON_PRODUCTION_MARKERS),
            "the report lacks an explicit non-production limitation")

    baseline = report["baseline_revision"]
    require(isinstance(baseline, str) and re.fullmatch(r"[0-9a-f]{40}", baseline) is not None,
            "the report baseline revision is not a pinned 40-character commit")
    head = git_head()
    if head == baseline:
        # Measured working-tree successor: HEAD is still the accepted baseline
        # and the reviewed candidate files are uncommitted.
        version_state = "working-tree"
    elif git_parent(head) == baseline and git_commits_ahead(baseline, head) == 1:
        # Committed candidate: HEAD is the direct child of the accepted
        # baseline, i.e. exactly the commit prepared from this material. The
        # ahead-count rejects a merge or any extra successor commit.
        version_state = "committed"
    else:
        raise HarnessError("the report is stale or foreign to the exact candidate revision")
    recorded_candidate = report["candidate_revision"]
    require(recorded_candidate is None or recorded_candidate == head,
            "the report candidate revision does not match the exact candidate")
    identity = report["candidate_identity"]
    require(identity.get("baseline_revision") == baseline,
            "the report identity names another baseline revision")
    require(identity.get("candidate_revision") in (None, head),
            "the report identity names another candidate revision")
    material = material_paths()
    require(identity.get("material_inputs") == material,
            "the report material-input inventory does not match the candidate")
    require(identity.get("material_digest") == material_digest(material),
            "the report material digest does not match the candidate (stale or foreign)")
    hashes = report["hashes"]
    require(isinstance(hashes, dict) and hashes, "the report records no artifact hashes")
    for path, recorded in hashes.items():
        require((REPO_ROOT / path).is_file(), f"hashed artifact is missing: {path}")
        require(sha256_file(REPO_ROOT / path) == recorded, f"hashed artifact changed: {path}")

    print(json.dumps({"ok": True, "task_id": TASK_ID, "report": str(report_path),
                      "outcome": regression["outcome"],
                      "candidate_revision_state": version_state,
                      "latency_regression_percent": latency_regression,
                      "throughput_regression_percent": throughput_regression}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T036 controlled X-COM observation-tap benchmark")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--report", nargs="?", const=str(DEFAULT_REPORT), default=None,
                       help="run the benchmark and write the evidence report")
    group.add_argument("--verify", nargs="?", const=str(DEFAULT_REPORT), default=None,
                       help="re-read and fail-closed verify the evidence report")
    args = parser.parse_args(argv)
    try:
        if args.report is not None:
            return run_benchmark(pathlib.Path(args.report))
        return verify_report(pathlib.Path(args.verify))
    except HarnessError as exc:
        print(f"T036 benchmark harness error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
