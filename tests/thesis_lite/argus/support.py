"""Owned neutral fixtures and helpers for the ARGUS2 Argus evidence tests.

Everything here is bounded, offline and neutral: no scientific protocol value, credential, host
address or execution request. Helpers build declared-intent XDL fixtures compiled by the real
accepted XDL compiler, frozen observation/snapshot projections and the real owned C++20 X-COM
producer fixture. The helpers never inject a platform source tree into ``sys.path``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _default_root() -> Path:
    """Resolve the checkout root from the caller environment or the repository layout."""

    override = os.environ.get("ARGUS_PLATFORM_SOURCE_ROOT")
    if override:
        return Path(override)
    return HERE.parents[2]


ROOT = _default_root()
FIXTURE_DIR = HERE / "fixtures"
FIXTURE_NAMES = ("system.json", "component.json", "profile.json", "deployment.json", "scenario.json")
FIXTURE_PATHS = tuple(FIXTURE_DIR / name for name in FIXTURE_NAMES)
CPP_FIXTURE = FIXTURE_DIR / "argus2_owned_record_producer.cpp"


def platform_source_root() -> Path:
    """Resolve accepted platform sources/fixtures from the caller environment or the repository root."""

    override = os.environ.get("ARGUS_PLATFORM_SOURCE_ROOT")
    if override:
        return Path(override)
    return ROOT


def profile_schema_path() -> Path:
    """Return the accepted experiment Profile schema path."""

    return platform_source_root() / "xdl" / "profiles" / "experiment-lite-v0.1.schema.json"


@lru_cache(maxsize=1)
def neutral_plan() -> dict[str, Any]:
    """Return one resolved plan compiled by the real accepted XDL compiler over the owned fixtures."""

    from xverse_xdl.experiment_plan import compile_experiment_files

    result = compile_experiment_files(
        FIXTURE_PATHS, profile_schema_paths=(profile_schema_path(),)
    )
    assert result.is_valid, [item.code for item in result.diagnostics]
    assert result.plan is not None
    return result.plan


def compiled_plan_bytes() -> dict[str, bytes]:
    """Return the owned neutral fixture bytes keyed by source name."""

    return {path.name: path.read_bytes() for path in FIXTURE_PATHS}


def source_byte_digests() -> dict[str, str]:
    """Return caller-declared source-byte digests for the owned fixtures."""

    import hashlib

    return {name: hashlib.sha256(data).hexdigest() for name, data in compiled_plan_bytes().items()}


def observation_record(**overrides: Any) -> dict[str, Any]:
    """Return one frozen owned-observation projection record."""

    record: dict[str, Any] = {
        "contractId": "contract.alpha",
        "contractVersion": "1.2.3",
        "interfaceId": "interface.alpha",
        "endpointId": "endpoint.alpha",
        "schemaId": "schema.alpha",
        "schemaVersion": "2.0.1",
        "interactionKind": "message_event",
        "origin": "component",
        "sourceClock": {"domain": "clock.source", "unit": "ns", "value": 100},
        "observationClock": {"domain": "clock.observation", "unit": "ns", "value": 200},
        "sequence": 7,
        "routeId": "route.alpha",
        "providerId": "provider.alpha",
        "sourcePayloadSize": 4,
        "providerOutcome": "accepted",
        "payloadViewState": "complete",
        "payloadSchemaState": "undecoded",
        "visibleBytesHex": "00ff1020",
        "visibleByteCount": 4,
        "tapId": "tap.unit",
        "counters": {"queued": 1, "accepted": 1, "dropped": 0, "coalesced": 0},
    }
    record.update(overrides)
    return record


def projection(records: list[dict[str, Any]], **overrides: Any) -> dict[str, Any]:
    """Return one frozen observation projection envelope."""

    envelope: dict[str, Any] = {
        "projectionVersion": "1.0",
        "upstreamContractVersion": "1.0.0",
        "exporter": {
            "task": "ARGUS2",
            "toolVersion": "0.1.0",
            "provenance": {"available": True, "note": "owned C++20 producer fixture"},
        },
        "records": records,
    }
    envelope.update(overrides)
    return envelope


def gateway_record() -> dict[str, Any]:
    """Return a narrower tool-gateway-shaped observation record (never the full owned projection)."""

    return {
        "route_id": "route.alpha",
        "contract_id": "contract.alpha",
        "clock_domain": "clock.observation",
        "sequence": 7,
        "outcome": "accepted",
        "payload_state": "undecoded",
        "payload_view": "complete",
        "payload_bytes": "00ff1020",
    }


def snapshot(**overrides: Any) -> dict[str, Any]:
    """Return one frozen caller-supplied snapshot projection."""

    value: dict[str, Any] = {
        "snapshotVersion": "1.0",
        "handle": {"hubInstanceId": 1, "tapId": 0, "generation": 1},
        "queued": 1,
        "accepted": 2,
        "dropped": 0,
        "coalesced": 0,
        "backpressureRejections": 0,
        "experimentValidityDegraded": False,
        "declaredTapId": "tap.unit",
        "validityEffect": "none",
        "validityState": "valid",
        "intervalProvenance": {
            "streamId": "stream.alpha",
            "intervalId": "interval.1",
            "closure": "closed",
            "start": {"domain": "clock.observation", "unit": "ns", "value": 0},
            "end": {"domain": "clock.observation", "unit": "ns", "value": 10},
            "provenance": "caller-declared",
        },
    }
    value.update(overrides)
    return value


def open_run(root: Any, **kwargs: Any):
    """Open one fresh run with the owned neutral plan and bounded caller inputs."""

    from xverse.argus import EvidenceStore

    kwargs.setdefault("run_id", "run-a")
    kwargs.setdefault("plan", neutral_plan())
    return EvidenceStore.open_run(root, **kwargs)


def run_root(tmp_path: Path, name: str = "run") -> Path:
    """Return a fresh run-root path inside a bounded temporary directory."""

    return Path(tmp_path) / name


def file_hashes(root: Path) -> dict[str, str]:
    """Return sha256 hashes of every regular file in a directory tree (read-only)."""

    import hashlib

    result: dict[str, str] = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Run the read-only ``xverse-argus`` module entry point in a subprocess."""

    environment = dict(os.environ)
    environment.setdefault("PYTHONPATH", str(ROOT / "src"))
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        environment.update(env)
    return subprocess.run(
        [sys.executable, "-m", "xverse.argus.cli", *args],
        cwd=str(HERE),
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )


def annotation_event_bytes(event_id: str = "e1", *, extensions: dict | None = None, unknown: bool = False) -> bytes:
    """Return one canonical accepted-representation annotation event line."""

    record: dict[str, Any] = {
        "schemaVersion": "1.0",
        "runId": "run-synthetic",
        "eventId": event_id,
        "producerId": "p1",
        "ingestionOrdinal": 1,
        "eventKind": "annotation",
    }
    if extensions is not None:
        record["extensions"] = extensions
    if unknown:
        record["unknownField"] = "x"
    return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"


def synthetic_run(root: Path, records: bytes, **overrides: Any) -> Path:
    """Write a minimal hand-built run root (manifest + stream) for installed-wheel read checks."""

    import hashlib

    from xverse.argus import EvidenceLimits

    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "events.jsonl").write_bytes(records)
    manifest: dict[str, Any] = {
        "schemaVersion": "1.0",
        "manifestVersion": "1.0",
        "runId": "run-synthetic",
        "plan": {
            "apiVersion": "xverse.io/xdl/v1alpha1",
            "profileVersion": "0.1.0",
            "planVersion": "1",
            "semanticDigest": {"algorithm": "sha256", "value": "0" * 64},
        },
        "sourceByteProvenance": {},
        "writerState": "closed",
        "eventCount": records.count(b"\n"),
        "eventStream": {
            "path": "events.jsonl",
            "mediaType": "application/x-ndjson",
            "schemaVersion": "1.0",
            "bytes": len(records),
            "sha256": hashlib.sha256(records).hexdigest(),
        },
        "artifacts": [],
        "obligations": [],
        "evidenceStatus": "complete",
        "evidenceReasons": [],
        "limits": EvidenceLimits().to_data(),
        "metricInputs": [],
        "clockDomains": [],
    }
    manifest.update(overrides)
    (root / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    return root


def installed_python(script: str, target: Path) -> subprocess.CompletedProcess:
    """Run a Python snippet against the installed wheel outside the source tree."""

    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(HERE),
        text=True,
        capture_output=True,
        check=False,
        env=installed_env(target),
    )



# --------------------------------------------------------------------------------------
# Offline wheel build/install and real C++ producer helpers
# --------------------------------------------------------------------------------------

_WHEEL_CACHE: dict[str, str] = {}


def wheel_and_target() -> tuple[Path, Path]:
    """Build the wheel offline once and install it into an isolated target with no dependencies."""

    if "wheel" in _WHEEL_CACHE:
        return Path(_WHEEL_CACHE["wheel"]), Path(_WHEEL_CACHE["target"])
    base = Path(tempfile.mkdtemp(prefix="argus2-wheel-"))
    dist = base / "dist"
    target = base / "site"
    dist.mkdir()
    target.mkdir()
    build = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(dist)],
        cwd=str(platform_source_root()),
        text=True,
        capture_output=True,
        check=False,
    )
    if build.returncode != 0:
        raise AssertionError(f"wheel build failed: {build.stdout}\n{build.stderr}")
    wheels = sorted(dist.glob("*.whl"))
    assert wheels, f"no wheel produced: {build.stdout}"
    wheel = wheels[0]
    install = subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "--no-deps", "--no-index",
            "--target", str(target), str(wheel),
        ],
        cwd=str(platform_source_root()),
        text=True,
        capture_output=True,
        check=False,
    )
    if install.returncode != 0:
        raise AssertionError(f"wheel install failed: {install.stdout}\n{install.stderr}")
    _WHEEL_CACHE["wheel"] = str(wheel)
    _WHEEL_CACHE["target"] = str(target)
    return wheel, target


def installed_env(target: Path) -> dict[str, str]:
    """Return a subprocess environment that resolves packages only from the installed target."""

    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(target)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["ARGUS_PLATFORM_SOURCE_ROOT"] = str(platform_source_root())
    return environment


def copy_owned_tests(destination: Path, *, include_consumer: bool = False) -> Path:
    """Copy the owned Argus tests outside the source tree for an installed-wheel run."""

    source = HERE
    for entry in sorted(source.iterdir()):
        if entry.name in {"__pycache__", ".pytest_cache"}:
            continue
        if entry.name.startswith("test_argus2_integration") or entry.name.startswith("test_argus2_validation"):
            continue
        if entry.name.startswith("test_argus2_consumer") and not include_consumer:
            continue
        if entry.is_dir():
            shutil.copytree(entry, destination / entry.name)
        else:
            shutil.copy2(entry, destination / entry.name)
    return destination


@lru_cache(maxsize=1)
def compiled_producer() -> Path:
    """Compile the real owned C++20 X-COM producer fixture once under /tmp."""

    root = platform_source_root()
    xcom = root / "src" / "xverse" / "xcom"
    include = xcom / "include"
    sources = [
        xcom / "src" / "observation.cpp",
        xcom / "src" / "item.cpp",
        xcom / "src" / "contract.cpp",
        xcom / "src" / "value.cpp",
        xcom / "src" / "diagnostic.cpp",
    ]
    output_dir = Path(tempfile.mkdtemp(prefix="argus2-cpp-"))
    binary = output_dir / "argus2_owned_record_producer"
    command = [
        "g++", "-std=c++20", "-O0", "-I", str(include),
        str(CPP_FIXTURE), *(str(source) for source in sources), "-o", str(binary),
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise AssertionError(f"C++ fixture compile failed:\n{result.stdout}\n{result.stderr}")
    return binary


def run_producer() -> dict[str, Any]:
    """Run the compiled producer and return its JSON projection output."""

    binary = compiled_producer()
    result = subprocess.run([str(binary)], text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise AssertionError(f"C++ producer failed:\n{result.stdout}\n{result.stderr}")
    return json.loads(result.stdout)


__all__ = [
    "CPP_FIXTURE",
    "FIXTURE_DIR",
    "FIXTURE_NAMES",
    "FIXTURE_PATHS",
    "HERE",
    "ROOT",
    "annotation_event_bytes",
    "cli",
    "compiled_plan_bytes",
    "compiled_producer",
    "copy_owned_tests",
    "file_hashes",
    "gateway_record",
    "installed_env",
    "installed_python",
    "neutral_plan",
    "observation_record",
    "open_run",
    "platform_source_root",
    "profile_schema_path",
    "projection",
    "run_producer",
    "run_root",
    "snapshot",
    "source_byte_digests",
    "synthetic_run",
    "wheel_and_target",
]
