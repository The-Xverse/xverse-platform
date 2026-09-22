#!/usr/bin/env python3
"""Offline admission checks for the X-COM build foundation.

The checker reads only the two explicitly named environment inputs and local
repository files. It neither installs packages nor performs network access.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from enum import Enum, IntEnum
from pathlib import Path
from unittest import mock

TOOLCHAIN_ENV = "XVERSE_XCOM_TOOLCHAIN"
MANIFEST_ENV = "XVERSE_XCOM_PACKAGE_MANIFEST"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ExitCode(IntEnum):
    """Stable process classifications for admission failures."""

    ADMITTED = 0
    INPUT_MISSING = 2
    MANIFEST_INVALID = 3
    PACKAGE_MISSING = 4
    HASH_MISMATCH = 5
    TOOL_MISSING = 6
    VERSION_MISMATCH = 7
    HEADER_MISSING = 8
    LIBRARY_MISSING = 9
    METADATA_MISSING = 10
    POLICY_INVALID = 11
    IO_ERROR = 12
    PROBE_FAILED = 13
    TIMEOUT = 14
    PAYLOAD_MISMATCH = 15


@dataclass(frozen=True, slots=True)
class PackageSpec:
    """Immutable expected identity and provenance for one locked package."""

    file: str
    sha256: str
    size: int
    package: str
    version: str
    source: str
    license: str


@dataclass(frozen=True, slots=True)
class ManifestRecord:
    """Immutable, validated representation of one manifest record."""

    file: str
    sha256: str
    size: int


@dataclass(frozen=True, order=True, slots=True)
class Diagnostic:
    """One deterministic admission result suitable for JSON serialization."""

    code: str
    category: str
    subject: str
    message: str
    exit_code: int


class ProbeFailure(Enum):
    """Expected ways an external command can fail without escaping admission."""

    EXECUTION = "execution"
    NONZERO = "nonzero"
    TIMEOUT = "timeout"


@dataclass(frozen=True, slots=True)
class CommandObservation:
    """Captured command output or a classified command failure."""

    output: str | None
    failure: ProbeFailure | None


@dataclass(frozen=True, slots=True)
class CMakePolicyEvidence:
    """Typed machine-readable evidence emitted by the configured CMake build."""

    schema_version: int
    probe_target: str
    compiler: str
    compiler_id: str
    compiler_version: str
    generator: str
    cxx_standard: int
    cxx_standard_required: bool
    cxx_extensions: bool
    build_testing: bool
    warnings_as_errors: bool
    warning_options: tuple[str, ...]
    toolchain_prefix: str
    package_manifest: str


PACKAGE_LOCK: tuple[PackageSpec, ...] = (
    PackageSpec(
        "clang-tidy-14_1%3a14.0.0-1ubuntu1.1_amd64.deb",
        "c59bd0f8089e57ae3b0aed276a28b72e674d756c880706d192dc10ad328eafe1",
        1625658,
        "clang-tidy-14",
        "1:14.0.0-1ubuntu1.1",
        "llvm-toolchain-14",
        "Apache-2.0 WITH LLVM-exception",
    ),
    PackageSpec(
        "clang-tidy_1%3a14.0-55~exp2_amd64.deb",
        "18a6c1c776bf0a10c18645d007fa4f5028861ec82c3c02eb225d4a437af099ef",
        3456,
        "clang-tidy",
        "1:14.0-55~exp2",
        "llvm-defaults (0.55~exp2)",
        "GPL-2.0-or-later",
    ),
    PackageSpec(
        "clang-tools-14_1%3a14.0.0-1ubuntu1.1_amd64.deb",
        "8eccc1c4c57e4eb225b6e4fa29a72c829caf73bc54f7985b844e9487c3ad843d",
        6961518,
        "clang-tools-14",
        "1:14.0.0-1ubuntu1.1",
        "llvm-toolchain-14",
        "Apache-2.0 WITH LLVM-exception",
    ),
    PackageSpec(
        "libgrpc++-dev_1.30.2-3build6_amd64.deb",
        "067752d39cb0bcbad10cf71d8a22d4e155e299c9f31187ceb4c400b56dd624c6",
        564346,
        "libgrpc++-dev",
        "1.30.2-3build6",
        "grpc",
        "Apache-2.0",
    ),
    PackageSpec(
        "libgrpc++1_1.30.2-3build6_amd64.deb",
        "574640b4cb72081a676889fb38469c4abd27b54c81540ee23a1f6b9cac0974eb",
        402166,
        "libgrpc++1",
        "1.30.2-3build6",
        "grpc",
        "Apache-2.0",
    ),
    PackageSpec(
        "libgrpc-dev_1.30.2-3build6_amd64.deb",
        "1c1c8a1b207a5bb10c37622e52288ec4e830f113cf735bc30544855587eb08b0",
        1065926,
        "libgrpc-dev",
        "1.30.2-3build6",
        "grpc",
        "Apache-2.0",
    ),
    PackageSpec(
        "libgrpc10_1.30.2-3build6_amd64.deb",
        "10c74dcd0d0eaeb252b4fcc286cd50325a88469d46d9706f853393809b2a1ee8",
        1469878,
        "libgrpc10",
        "1.30.2-3build6",
        "grpc",
        "Apache-2.0",
    ),
    PackageSpec(
        "libprotobuf-dev_3.12.4-1ubuntu7.22.04.6_amd64.deb",
        "1ac0147f49bc089cd57c8aabb78617211d950b3ba0df28ecd0f65e0515a5884a",
        1346664,
        "libprotobuf-dev",
        "3.12.4-1ubuntu7.22.04.6",
        "protobuf",
        "BSD-3-Clause",
    ),
    PackageSpec(
        "libprotoc23_3.12.4-1ubuntu7.22.04.6_amd64.deb",
        "470ba9e90c9aeb788abf819c71f15a69605c47e6f510d56fba723e790365b6f1",
        662358,
        "libprotoc23",
        "3.12.4-1ubuntu7.22.04.6",
        "protobuf",
        "BSD-3-Clause",
    ),
    PackageSpec(
        "nlohmann-json3-dev_3.10.5-2_all.deb",
        "0c0ab9e6baf27a930990729b3ad7123b12dfd353e7bac7bf6c77aa03eab5c639",
        166536,
        "nlohmann-json3-dev",
        "3.10.5-2",
        "nlohmann-json3",
        "MIT",
    ),
    PackageSpec(
        "protobuf-compiler-grpc_1.30.2-3build6_amd64.deb",
        "79debaed17ff25444a9c450b4b342e3d7565e80c062da2356b42ceb73e305331",
        185228,
        "protobuf-compiler-grpc",
        "1.30.2-3build6",
        "grpc",
        "Apache-2.0",
    ),
    PackageSpec(
        "protobuf-compiler_3.12.4-1ubuntu7.22.04.6_amd64.deb",
        "a124cc30fadf8e83f86fd7e1b9c776befd336d092bb81f95de1dc39d79b61ce7",
        29196,
        "protobuf-compiler",
        "3.12.4-1ubuntu7.22.04.6",
        "protobuf",
        "BSD-3-Clause",
    ),
)


def diagnostic(code: str, category: ExitCode, subject: str, message: str) -> Diagnostic:
    """Create a stable diagnostic while keeping enum conversion in one place."""

    return Diagnostic(code, category.name, subject, message, int(category))


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 digest of a local file without mutation."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_lock(
    lock: Sequence[PackageSpec], expected_count: int = 12
) -> list[Diagnostic]:
    """Validate internal lock invariants before trusting it for admission."""

    errors: list[Diagnostic] = []
    if len(lock) != expected_count:
        errors.append(
            diagnostic(
                "XCOM-BLD-E013",
                ExitCode.POLICY_INVALID,
                "package-lock",
                f"lock must contain exactly {expected_count} package entries",
            )
        )
    filenames: set[str] = set()
    packages: set[str] = set()
    for index, spec in enumerate(lock):
        if spec.file in filenames:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E014",
                    ExitCode.POLICY_INVALID,
                    spec.file,
                    "lock contains a duplicate filename",
                )
            )
        filenames.add(spec.file)
        if spec.package in packages:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E015",
                    ExitCode.POLICY_INVALID,
                    spec.package,
                    "lock contains a duplicate package name",
                )
            )
        packages.add(spec.package)
        if re.fullmatch(r"[0-9a-f]{64}", spec.sha256) is None or spec.size <= 0:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E016",
                    ExitCode.POLICY_INVALID,
                    f"lock[{index}]",
                    "lock SHA-256 must be lowercase hexadecimal and size must be positive",
                )
            )
    return sorted(errors)


def load_manifest(
    path: Path, lock: Sequence[PackageSpec] = PACKAGE_LOCK
) -> tuple[list[ManifestRecord], list[Diagnostic]]:
    """Load and strictly validate an offline package manifest."""

    try:
        manifest_exists = path.is_file()
    except OSError:
        return [], [
            diagnostic(
                "XCOM-BLD-E009",
                ExitCode.IO_ERROR,
                "manifest",
                "manifest could not be inspected",
            )
        ]
    if not manifest_exists:
        return [], [
            diagnostic(
                "XCOM-BLD-E001",
                ExitCode.INPUT_MISSING,
                MANIFEST_ENV,
                "explicit manifest is missing",
            )
        ]
    try:
        value: object = json.loads(path.read_text(encoding="utf-8"))
    except PermissionError:
        return [], [
            diagnostic(
                "XCOM-BLD-E009",
                ExitCode.IO_ERROR,
                "manifest",
                "manifest is not readable",
            )
        ]
    except OSError:
        return [], [
            diagnostic(
                "XCOM-BLD-E009",
                ExitCode.IO_ERROR,
                "manifest",
                "manifest could not be read",
            )
        ]
    except (UnicodeError, json.JSONDecodeError):
        return [], [
            diagnostic(
                "XCOM-BLD-E002",
                ExitCode.MANIFEST_INVALID,
                "manifest",
                "manifest is not valid UTF-8 JSON",
            )
        ]
    if not isinstance(value, list):
        return [], [
            diagnostic(
                "XCOM-BLD-E003",
                ExitCode.MANIFEST_INVALID,
                "manifest",
                "top level must be an array",
            )
        ]

    lock_errors = validate_lock(lock, 12 if lock is PACKAGE_LOCK else len(lock))
    if lock_errors:
        return [], lock_errors
    expected = {item.file: item for item in lock}
    observed: dict[str, ManifestRecord] = {}
    errors: list[Diagnostic] = []
    for index, raw_record in enumerate(value):
        if not isinstance(raw_record, dict) or set(raw_record) != {
            "file",
            "sha256",
            "size",
        }:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E004",
                    ExitCode.MANIFEST_INVALID,
                    f"record[{index}]",
                    "record fields must be exactly file, sha256, and size",
                )
            )
            continue
        filename = raw_record.get("file")
        sha256 = raw_record.get("sha256")
        size = raw_record.get("size")
        valid = True
        if (
            not isinstance(filename, str)
            or not filename
            or Path(filename).name != filename
        ):
            errors.append(
                diagnostic(
                    "XCOM-BLD-E005",
                    ExitCode.MANIFEST_INVALID,
                    f"record[{index}]",
                    "file must be one safe basename",
                )
            )
            valid = False
        if not isinstance(sha256, str) or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E017",
                    ExitCode.MANIFEST_INVALID,
                    f"record[{index}]",
                    "sha256 must be 64 lowercase hexadecimal characters",
                )
            )
            valid = False
        if type(size) is not int or size <= 0:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E018",
                    ExitCode.MANIFEST_INVALID,
                    f"record[{index}]",
                    "size must be a positive integer",
                )
            )
            valid = False
        if not valid:
            continue
        assert isinstance(filename, str)
        assert isinstance(sha256, str)
        assert isinstance(size, int)
        if filename in observed:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E006",
                    ExitCode.MANIFEST_INVALID,
                    filename,
                    "duplicate package record",
                )
            )
            continue
        observed[filename] = ManifestRecord(filename, sha256, size)

    if set(observed) != set(expected):
        errors.append(
            diagnostic(
                "XCOM-BLD-E007",
                ExitCode.MANIFEST_INVALID,
                "package-set",
                "manifest must contain exactly the twelve locked packages",
            )
        )
    for filename in sorted(set(observed) & set(expected)):
        record = observed[filename]
        spec = expected[filename]
        if record.sha256 != spec.sha256 or record.size != spec.size:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E008",
                    ExitCode.MANIFEST_INVALID,
                    filename,
                    "manifest hash or size differs from the lock",
                )
            )
    return [observed[name] for name in sorted(observed)], sorted(errors)


def verify_package_files(
    manifest_path: Path, lock: Sequence[PackageSpec] = PACKAGE_LOCK
) -> list[Diagnostic]:
    """Verify locked package bytes without extracting or installing payloads."""

    errors: list[Diagnostic] = []
    for spec in sorted(lock, key=lambda item: item.file):
        package_path = manifest_path.parent / spec.file
        try:
            package_exists = package_path.is_file()
        except OSError:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E012",
                    ExitCode.IO_ERROR,
                    spec.file,
                    "locked package file could not be inspected",
                )
            )
            continue
        if not package_exists:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E010",
                    ExitCode.PACKAGE_MISSING,
                    spec.file,
                    "locked package file is missing",
                )
            )
            continue
        try:
            size = package_path.stat().st_size
            observed_hash = sha256_file(package_path)
        except PermissionError:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E012",
                    ExitCode.IO_ERROR,
                    spec.file,
                    "locked package file is not readable",
                )
            )
            continue
        except OSError:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E012",
                    ExitCode.IO_ERROR,
                    spec.file,
                    "locked package file could not be read",
                )
            )
            continue
        if size != spec.size or observed_hash != spec.sha256:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E011",
                    ExitCode.HASH_MISMATCH,
                    spec.file,
                    "package byte size or SHA-256 mismatches the lock",
                )
            )
    return sorted(errors)


def _deb_fields(
    package_path: Path,
) -> tuple[Mapping[str, str] | None, ProbeFailure | None]:
    """Read package identity fields with a bounded, non-installing probe."""

    tool = shutil.which("dpkg-deb")
    if tool is None:
        return None, ProbeFailure.EXECUTION
    try:
        result = subprocess.run(
            [tool, "-f", str(package_path), "Package", "Version", "Source"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return None, ProbeFailure.TIMEOUT
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return None, ProbeFailure.EXECUTION
    if result.returncode != 0:
        return None, ProbeFailure.NONZERO
    fields: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields, None


def verify_package_metadata(manifest_path: Path) -> list[Diagnostic]:
    """Check package name, version, and source provenance in-place."""

    if shutil.which("dpkg-deb") is None:
        return [
            diagnostic(
                "XCOM-BLD-E020",
                ExitCode.TOOL_MISSING,
                "dpkg-deb",
                "offline package metadata reader is unavailable",
            )
        ]
    errors: list[Diagnostic] = []
    for spec in sorted(PACKAGE_LOCK, key=lambda item: item.file):
        fields, failure = _deb_fields(manifest_path.parent / spec.file)
        if failure is ProbeFailure.TIMEOUT:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E023",
                    ExitCode.TIMEOUT,
                    spec.file,
                    "Debian package metadata probe timed out",
                )
            )
            continue
        if failure is ProbeFailure.EXECUTION:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E024",
                    ExitCode.PROBE_FAILED,
                    spec.file,
                    "Debian package metadata probe could not execute",
                )
            )
            continue
        if failure is ProbeFailure.NONZERO or not fields:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E021",
                    ExitCode.METADATA_MISSING,
                    spec.file,
                    "Debian package metadata is unreadable",
                )
            )
            continue
        actual_source = fields.get("Source", fields.get("Package", ""))
        if (
            fields.get("Package") != spec.package
            or fields.get("Version") != spec.version
            or actual_source != spec.source
        ):
            errors.append(
                diagnostic(
                    "XCOM-BLD-E022",
                    ExitCode.VERSION_MISMATCH,
                    spec.file,
                    "package name, version, or source provenance mismatches the lock",
                )
            )
    return sorted(errors)


def extract_reference_tree(
    manifest_path: Path,
    destination: Path,
    lock: Sequence[PackageSpec] = PACKAGE_LOCK,
) -> list[Diagnostic]:
    """Extract locked packages into a disposable non-installed reference tree."""

    tool = shutil.which("dpkg-deb")
    if tool is None:
        return [
            diagnostic(
                "XCOM-BLD-E080",
                ExitCode.TOOL_MISSING,
                "dpkg-deb",
                "offline package payload extractor is unavailable",
            )
        ]
    for spec in sorted(lock, key=lambda item: item.file):
        try:
            result = subprocess.run(
                [tool, "-x", str(manifest_path.parent / spec.file), str(destination)],
                check=False,
                capture_output=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            return [
                diagnostic(
                    "XCOM-BLD-E081",
                    ExitCode.TIMEOUT,
                    spec.file,
                    "Debian package payload extraction timed out",
                )
            ]
        except (OSError, subprocess.SubprocessError):
            return [
                diagnostic(
                    "XCOM-BLD-E082",
                    ExitCode.PROBE_FAILED,
                    spec.file,
                    "Debian package payload extraction could not execute",
                )
            ]
        if result.returncode != 0:
            return [
                diagnostic(
                    "XCOM-BLD-E082",
                    ExitCode.PROBE_FAILED,
                    spec.file,
                    "Debian package payload extraction failed",
                )
            ]
    return []


def _payload_kind(path: Path) -> str | None:
    """Return a non-following filesystem type for one payload node."""

    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return None
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISDIR(mode):
        return "directory"
    return "other"


def _payload_inventory(
    root: Path, destinations: Sequence[Path] | None = None
) -> dict[Path, str]:
    """Inventory payload nodes recursively without following symbolic links."""

    inventory: dict[Path, str] = {}
    pending = list(destinations) if destinations is not None else [Path()]
    while pending:
        relative = pending.pop()
        directory = root / relative
        if destinations is not None and relative not in inventory:
            kind = _payload_kind(directory)
            if kind is None:
                continue
            inventory[relative] = kind
            if kind != "directory":
                continue
        with os.scandir(directory) as entries:
            children = sorted(entries, key=lambda entry: entry.name, reverse=True)
        for entry in children:
            child = relative / entry.name
            kind = _payload_kind(Path(entry.path))
            if kind is None:
                raise FileNotFoundError(entry.path)
            inventory[child] = kind
            if kind == "directory":
                pending.append(child)
    return inventory


def compare_payload_trees(
    prefix: Path,
    reference: Path,
) -> list[Diagnostic]:
    """Compare the complete archive payload with its isolated destinations."""

    errors: list[Diagnostic] = []
    try:
        expected = _payload_inventory(reference)
    except (PermissionError, OSError):
        return [
            diagnostic(
                "XCOM-BLD-E087",
                ExitCode.IO_ERROR,
                "payload-reference",
                "reference payload tree could not be read",
            )
        ]
    if not expected:
        return [
            diagnostic(
                "XCOM-BLD-E083",
                ExitCode.POLICY_INVALID,
                "payload-reference",
                "locked packages provide no installable payload nodes",
            )
        ]
    destinations = tuple(
        Path(name) for name in sorted({path.parts[0] for path in expected})
    )
    try:
        actual = _payload_inventory(prefix, destinations)
    except (PermissionError, OSError):
        return [
            diagnostic(
                "XCOM-BLD-E087",
                ExitCode.IO_ERROR,
                "toolchain-prefix",
                "prefix payload tree could not be read",
            )
        ]

    for relative in sorted(set(expected) - set(actual)):
        errors.append(
            diagnostic(
                "XCOM-BLD-E084",
                ExitCode.PAYLOAD_MISMATCH,
                relative.as_posix(),
                "prefix payload node is missing",
            )
        )
    for relative in sorted(set(actual) - set(expected)):
        errors.append(
            diagnostic(
                "XCOM-BLD-E107",
                ExitCode.PAYLOAD_MISMATCH,
                relative.as_posix(),
                "prefix contains an extra node within a locked payload destination",
            )
        )

    for relative in sorted(set(expected) & set(actual)):
        expected_kind = expected[relative]
        actual_kind = actual[relative]
        if actual_kind != expected_kind:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E084",
                    ExitCode.PAYLOAD_MISMATCH,
                    relative.as_posix(),
                    "prefix payload node has a different type",
                )
            )
            continue
        expected_path = reference / relative
        actual_path = prefix / relative
        if expected_kind == "symlink":
            try:
                expected_target = os.readlink(expected_path)
                actual_target = os.readlink(actual_path)
            except (PermissionError, OSError):
                errors.append(
                    diagnostic(
                        "XCOM-BLD-E087",
                        ExitCode.IO_ERROR,
                        relative.as_posix(),
                        "payload symlink target could not be read",
                    )
                )
                continue
            if actual_target != expected_target:
                errors.append(
                    diagnostic(
                        "XCOM-BLD-E086",
                        ExitCode.PAYLOAD_MISMATCH,
                        relative.as_posix(),
                        "prefix payload symlink target differs from the locked payload",
                    )
                )
            continue
        if expected_kind == "directory":
            continue
        if expected_kind != "file":
            errors.append(
                diagnostic(
                    "XCOM-BLD-E083",
                    ExitCode.POLICY_INVALID,
                    relative.as_posix(),
                    "locked payload node has an unsupported reference type",
                )
            )
            continue
        try:
            expected_hash = sha256_file(expected_path)
            actual_hash = sha256_file(actual_path)
        except (PermissionError, OSError):
            errors.append(
                diagnostic(
                    "XCOM-BLD-E087",
                    ExitCode.IO_ERROR,
                    relative.as_posix(),
                    "payload file content could not be read",
                )
            )
            continue
        if actual_hash != expected_hash:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E085",
                    ExitCode.PAYLOAD_MISMATCH,
                    relative.as_posix(),
                    "prefix payload content differs from the locked package payload",
                )
            )
    return sorted(set(errors))


def verify_payload_binding(
    prefix: Path,
    manifest_path: Path,
    lock: Sequence[PackageSpec] = PACKAGE_LOCK,
) -> list[Diagnostic]:
    """Bind the complete prefix payload to a temporary exact package reference."""

    try:
        with tempfile.TemporaryDirectory(prefix="xcom-payload-reference-") as root:
            reference = Path(root)
            errors = extract_reference_tree(manifest_path, reference, lock)
            if errors:
                return errors
            return compare_payload_trees(prefix, reference)
    except (PermissionError, OSError):
        return [
            diagnostic(
                "XCOM-BLD-E089",
                ExitCode.IO_ERROR,
                "payload-reference",
                "temporary payload reference could not be created or removed",
            )
        ]


def _read_version_from_pc(path: Path) -> str | None:
    """Read an exact Version field from local pkg-config metadata."""

    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Version:"):
            return line.partition(":")[2].strip()
    return None


def _run_version(
    executable: Path, arguments: Sequence[str] = ("--version",)
) -> CommandObservation:
    """Run a bounded local version probe and classify expected failures."""

    try:
        result = subprocess.run(
            [str(executable), *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return CommandObservation(None, ProbeFailure.TIMEOUT)
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return CommandObservation(None, ProbeFailure.EXECUTION)
    if result.returncode != 0:
        return CommandObservation(None, ProbeFailure.NONZERO)
    return CommandObservation((result.stdout + result.stderr).strip(), None)


def _has_exact_version(text: str, version: str) -> bool:
    """Match a dotted version token without accepting longer numeric versions."""

    return re.search(rf"(?<![\d.]){re.escape(version)}(?![\d.])", text) is not None


def _version_probe_diagnostic(subject: str, failure: ProbeFailure) -> Diagnostic:
    """Translate command-probe failures to stable public diagnostics."""

    if failure is ProbeFailure.TIMEOUT:
        return diagnostic(
            "XCOM-BLD-E038", ExitCode.TIMEOUT, subject, "version probe timed out"
        )
    return diagnostic(
        "XCOM-BLD-E039", ExitCode.PROBE_FAILED, subject, "version probe failed"
    )


def verify_prefix(prefix: Path, *, execute_probes: bool = True) -> list[Diagnostic]:
    """Verify prefix artifacts, optionally suppressing all executable probes."""

    errors: list[Diagnostic] = []
    executables = {
        "protoc": ("usr/bin/protoc", "3.12.4"),
        "clang-tidy": ("usr/bin/clang-tidy", "14.0.0"),
        "grpc_cpp_plugin": ("usr/bin/grpc_cpp_plugin", None),
    }
    for name, (relative, expected_version) in executables.items():
        path = prefix / relative
        try:
            executable_present = path.is_file() and os.access(path, os.X_OK)
        except OSError:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E045",
                    ExitCode.IO_ERROR,
                    name,
                    "prefix executable could not be inspected",
                )
            )
            continue
        if not executable_present:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E030",
                    ExitCode.TOOL_MISSING,
                    name,
                    "required generated-code or analysis tool is missing",
                )
            )
        elif expected_version and execute_probes:
            observation = _run_version(path)
            if observation.failure is not None:
                errors.append(_version_probe_diagnostic(name, observation.failure))
            elif not _has_exact_version(observation.output or "", expected_version):
                errors.append(
                    diagnostic(
                        "XCOM-BLD-E031",
                        ExitCode.VERSION_MISMATCH,
                        name,
                        "tool version differs from the lock",
                    )
                )

    headers = (
        "usr/include/nlohmann/json.hpp",
        "usr/include/google/protobuf/message.h",
        "usr/include/grpcpp/grpcpp.h",
    )
    for relative in headers:
        try:
            header_present = (prefix / relative).is_file()
        except OSError:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E045",
                    ExitCode.IO_ERROR,
                    relative,
                    "required header could not be inspected",
                )
            )
            continue
        if not header_present:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E032",
                    ExitCode.HEADER_MISSING,
                    relative,
                    "required header is missing",
                )
            )
    libraries = (
        "usr/lib/x86_64-linux-gnu/libprotobuf.a",
        "usr/lib/x86_64-linux-gnu/libgrpc.so",
        "usr/lib/x86_64-linux-gnu/libgrpc++.so",
    )
    for relative in libraries:
        try:
            library_present = (prefix / relative).is_file()
        except OSError:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E045",
                    ExitCode.IO_ERROR,
                    relative,
                    "required library could not be inspected",
                )
            )
            continue
        if not library_present:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E033",
                    ExitCode.LIBRARY_MISSING,
                    relative,
                    "required library is missing",
                )
            )

    metadata = {
        "nlohmann/json": ("usr/lib/pkgconfig/nlohmann_json.pc", "3.10.5"),
        "Protocol Buffers": (
            "usr/lib/x86_64-linux-gnu/pkgconfig/protobuf.pc",
            "3.12.4",
        ),
        "gRPC": ("usr/lib/x86_64-linux-gnu/pkgconfig/grpc++.pc", "1.30.2"),
    }
    for name, (relative, version) in metadata.items():
        try:
            observed = _read_version_from_pc(prefix / relative)
        except (OSError, UnicodeError):
            errors.append(
                diagnostic(
                    "XCOM-BLD-E045",
                    ExitCode.IO_ERROR,
                    name,
                    "pkg-config metadata could not be read",
                )
            )
            continue
        if observed is None:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E034",
                    ExitCode.METADATA_MISSING,
                    name,
                    "pkg-config metadata is missing",
                )
            )
        elif observed != version:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E035",
                    ExitCode.VERSION_MISMATCH,
                    name,
                    "pkg-config version differs from the lock",
                )
            )

    json_header = prefix / "usr/include/nlohmann/json.hpp"
    protobuf_header = prefix / "usr/include/google/protobuf/stubs/common.h"
    try:
        json_header_present = json_header.is_file()
    except OSError:
        json_header_present = False
        errors.append(
            diagnostic(
                "XCOM-BLD-E045",
                ExitCode.IO_ERROR,
                "nlohmann/json",
                "version header could not be inspected",
            )
        )
    if json_header_present:
        try:
            text = json_header.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            errors.append(
                diagnostic(
                    "XCOM-BLD-E045",
                    ExitCode.IO_ERROR,
                    "nlohmann/json",
                    "version header could not be read",
                )
            )
        else:
            tokens = (
                ("NLOHMANN_JSON_VERSION_MAJOR", "3"),
                ("NLOHMANN_JSON_VERSION_MINOR", "10"),
                ("NLOHMANN_JSON_VERSION_PATCH", "5"),
            )
            if any(
                re.search(rf"(?m)^\s*(?:#\s*define\s+)?{name}\s+{value}\s*$", text)
                is None
                for name, value in tokens
            ):
                errors.append(
                    diagnostic(
                        "XCOM-BLD-E036",
                        ExitCode.VERSION_MISMATCH,
                        "nlohmann/json",
                        "header version differs from 3.10.5",
                    )
                )
    try:
        protobuf_header_present = protobuf_header.is_file()
    except OSError:
        protobuf_header_present = False
        errors.append(
            diagnostic(
                "XCOM-BLD-E045",
                ExitCode.IO_ERROR,
                "Protocol Buffers",
                "version header could not be inspected",
            )
        )
    if protobuf_header_present:
        try:
            text = protobuf_header.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            errors.append(
                diagnostic(
                    "XCOM-BLD-E045",
                    ExitCode.IO_ERROR,
                    "Protocol Buffers",
                    "version header could not be read",
                )
            )
        else:
            pattern = r"(?m)^\s*(?:#\s*define\s+)?GOOGLE_PROTOBUF_VERSION\s+3012004\s*$"
            if re.search(pattern, text) is None:
                errors.append(
                    diagnostic(
                        "XCOM-BLD-E037",
                        ExitCode.VERSION_MISMATCH,
                        "Protocol Buffers",
                        "header version differs from 3.12.4",
                    )
                )
    return sorted(errors)


def _numeric_version(text: str) -> tuple[int, ...] | None:
    """Extract a comparable major/minor/patch tuple from a tool description."""

    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text)
    return tuple(int(part) for part in match.groups(default="0")) if match else None


def validate_build_tool_descriptions(
    descriptions: Mapping[str, str | None],
) -> list[Diagnostic]:
    """Validate controlled build-tool descriptions without executing tools."""

    minimums = {"cmake": (3, 22, 0), "ninja": (1, 10, 0)}
    errors: list[Diagnostic] = []
    for name in ("cmake", "ninja", "c++"):
        description = descriptions.get(name)
        if not description:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E040",
                    ExitCode.TOOL_MISSING,
                    name,
                    "required build tool is unavailable",
                )
            )
            continue
        if (
            name in minimums
            and (_numeric_version(description) or (0,)) < minimums[name]
        ):
            errors.append(
                diagnostic(
                    "XCOM-BLD-E041",
                    ExitCode.VERSION_MISMATCH,
                    name,
                    "build tool is older than the accepted minimum",
                )
            )
    return sorted(errors)


def verify_build_tools() -> list[Diagnostic]:
    """Verify host build tools and compile the accepted warning-policy probe."""

    descriptions: dict[str, str | None] = {}
    locations: dict[str, str | None] = {}
    errors: list[Diagnostic] = []
    for name in ("cmake", "ninja", "c++"):
        location = shutil.which(name)
        locations[name] = location
        if location is None:
            descriptions[name] = None
            continue
        observation = _run_version(Path(location))
        descriptions[name] = observation.output
        if observation.failure is not None:
            errors.append(_version_probe_diagnostic(name, observation.failure))
    description_errors = validate_build_tool_descriptions(descriptions)
    errors.extend(
        item
        for item in description_errors
        if not (item.code == "XCOM-BLD-E040" and locations[item.subject] is not None)
    )
    compiler = locations.get("c++")
    if compiler and not any(item.subject == "c++" for item in errors):
        try:
            result = subprocess.run(
                [
                    compiler,
                    "-x",
                    "c++",
                    "-std=c++20",
                    "-Wall",
                    "-Wextra",
                    "-Wpedantic",
                    "-Werror",
                    "-fsyntax-only",
                    "-",
                ],
                input="#include <concepts>\nstatic_assert(std::same_as<int, int>);\n",
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E043",
                    ExitCode.TIMEOUT,
                    "c++",
                    "compiler policy probe timed out",
                )
            )
        except (OSError, subprocess.SubprocessError, UnicodeError):
            errors.append(
                diagnostic(
                    "XCOM-BLD-E044",
                    ExitCode.PROBE_FAILED,
                    "c++",
                    "compiler policy probe failed",
                )
            )
        else:
            if result.returncode != 0:
                errors.append(
                    diagnostic(
                        "XCOM-BLD-E042",
                        ExitCode.POLICY_INVALID,
                        "c++",
                        "compiler does not accept the required C++20 warning policy",
                    )
                )
    return sorted(errors)


LOCK_DOCUMENT_SECTIONS = (
    "Exact Jammy package records and retrieval coordinates",
    "Admitted component and generated-code provenance",
    "Archive identity versus extracted payload identity",
)

ENVIRONMENT_DOCUMENT_SECTIONS = (
    "Explicit inputs and host envelope",
    "Deterministic offline prefix reconstruction",
    "Environment for admission and builds",
    "Offline admission and build-policy validation",
    "Classified failure and evidence semantics",
    "Requirement-to-check traceability",
)


def _level_two_markdown_sections(text: str) -> dict[str, str]:
    """Return non-overlapping level-two Markdown sections by exact heading."""

    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line.removeprefix("## ").strip()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
    return {heading: "\n".join(lines).strip() for heading, lines in sections.items()}


def _missing_sections(text: str, required: Sequence[str]) -> tuple[str, ...]:
    """Identify required headings that are absent or have no substantive body."""

    sections = _level_two_markdown_sections(text)
    return tuple(
        heading for heading in required if not sections.get(heading, "").strip()
    )


def _package_table_rows(
    section: str,
) -> tuple[dict[str, tuple[str, ...]], int]:
    """Index exact dependency-lock table rows by retained archive filename."""

    rows: dict[str, tuple[str, ...]] = {}
    row_count = 0
    for line in section.splitlines():
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
        if (
            len(cells) != 7
            or not cells[0].startswith("`")
            or not cells[0].endswith(".deb`")
        ):
            continue
        row_count += 1
        rows[cells[0][1:-1]] = cells
    return rows, row_count


def validate_dependency_lock_document(text: str) -> list[Diagnostic]:
    """Validate exact package identity and provenance in dependency-lock.md."""

    if not text.strip():
        return [
            diagnostic(
                "XCOM-BLD-E053",
                ExitCode.POLICY_INVALID,
                "dependency-lock.md",
                "dependency lock document is empty",
            )
        ]

    errors: list[Diagnostic] = []
    sections = _level_two_markdown_sections(text)
    for heading in _missing_sections(text, LOCK_DOCUMENT_SECTIONS):
        errors.append(
            diagnostic(
                "XCOM-BLD-E053",
                ExitCode.POLICY_INVALID,
                f"dependency-lock.md#{heading}",
                "required dependency lock section is missing or empty",
            )
        )

    records, record_count = _package_table_rows(
        sections.get(LOCK_DOCUMENT_SECTIONS[0], "")
    )
    expected_files = {spec.file for spec in PACKAGE_LOCK}
    if set(records) != expected_files or record_count != len(PACKAGE_LOCK):
        errors.append(
            diagnostic(
                "XCOM-BLD-E051",
                ExitCode.POLICY_INVALID,
                "dependency-lock.md#package-records",
                "lock documentation does not contain exactly the twelve package rows",
            )
        )
    for spec in PACKAGE_LOCK:
        expected_cells = (
            f"`{spec.file}`",
            str(spec.size),
            f"`{spec.sha256}`",
            f"`{spec.package}` `{spec.version}`",
            f"`{spec.source}`",
            spec.license,
        )
        row = records.get(spec.file, ())
        if row[:6] != expected_cells:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E051",
                    ExitCode.POLICY_INVALID,
                    spec.file,
                    "lock package identity, size, SHA-256, source, or license differs",
                )
            )

    provenance = sections.get(LOCK_DOCUMENT_SECTIONS[1], "")
    provenance_markers = (
        "nlohmann/json | 3.10.5",
        "Protocol Buffers | 3.12.4",
        "gRPC | 1.30.2",
        "clang-tidy / LLVM | 14.0.0",
        PACKAGE_LOCK[-1].file,
        PACKAGE_LOCK[-1].sha256,
        PACKAGE_LOCK[-2].file,
        PACKAGE_LOCK[-2].sha256,
        "input schema identity",
        "generation command",
        "grpc_cpp_plugin` has no supported version flag",
    )
    for marker in provenance_markers:
        if marker.lower() not in provenance.lower():
            errors.append(
                diagnostic(
                    "XCOM-BLD-E056",
                    ExitCode.POLICY_INVALID,
                    "dependency-lock.md#generated-code-provenance",
                    f"generated-code provenance is missing: {marker}",
                )
            )

    payload = sections.get(LOCK_DOCUMENT_SECTIONS[2], "")
    for marker in (
        "exactly the twelve retained filenames",
        "byte sizes",
        "SHA-256",
        "dpkg-deb -f",
        "dpkg-deb -x",
        TOOLCHAIN_ENV,
        "file type",
        "file content",
        "symlink text",
        "No ambient package manager",
    ):
        if marker.lower() not in payload.lower():
            errors.append(
                diagnostic(
                    "XCOM-BLD-E056",
                    ExitCode.POLICY_INVALID,
                    "dependency-lock.md#payload-provenance",
                    f"archive/payload provenance is missing: {marker}",
                )
            )
    return sorted(set(errors))


def validate_build_environment_document(text: str) -> list[Diagnostic]:
    """Validate reconstruction, limits, failure, and traceability documentation."""

    if not text.strip():
        return [
            diagnostic(
                "XCOM-BLD-E054",
                ExitCode.POLICY_INVALID,
                "build-environment.md",
                "build environment document is empty",
            )
        ]

    errors: list[Diagnostic] = []
    sections = _level_two_markdown_sections(text)
    for heading in _missing_sections(text, ENVIRONMENT_DOCUMENT_SECTIONS):
        errors.append(
            diagnostic(
                "XCOM-BLD-E054",
                ExitCode.POLICY_INVALID,
                f"build-environment.md#{heading}",
                "required build environment section is missing or empty",
            )
        )

    required_by_section = {
        "Explicit inputs and host envelope": (
            TOOLCHAIN_ENV,
            MANIFEST_ENV,
            "python3` 3.11 or newer",
            "CMake 3.22 or newer",
            "Ninja 1.10 or newer",
            "C++20",
            "dpkg-deb",
        ),
        "Deterministic offline prefix reconstruction": (
            'test ! -e "$XVERSE_XCOM_TOOLCHAIN"',
            'python3 - "$XVERSE_XCOM_PACKAGE_MANIFEST"',
            "hashlib",
            "mkdir -m 0755",
            "dpkg-deb -x",
            "does not invoke APT",
            "discard that newly created prefix",
        ),
        "Environment for admission and builds": (
            TOOLCHAIN_ENV,
            MANIFEST_ENV,
            "export PATH=",
            "export LD_LIBRARY_PATH=",
            "export PKG_CONFIG_SYSROOT_DIR=",
            "export PKG_CONFIG_PATH=",
            "export CMAKE_PREFIX_PATH=",
            "ABI-compatible Ubuntu Jammy-derived host",
            "transitive",
            "OpenSSL",
            "pinned base-system ABI",
        ),
        "Offline admission and build-policy validation": (
            "sys.version_info >= (3, 11)",
            "--self-test",
            "--verify-toolchain",
            "--all",
            "cmake -S . -B build -G Ninja -DBUILD_TESTING=ON",
            "cmake --build build --target xverse_xcom_policy_probe --verbose",
            "ctest --test-dir build --output-on-failure",
        ),
        "Classified failure and evidence semantics": (
            "admitted: true",
            "admitted: false",
            "deterministic JSON",
            "classified nonzero",
            "INPUT_MISSING",
            "POLICY_INVALID",
            "IO_ERROR",
            "PAYLOAD_MISMATCH",
            "numerically lowest applicable nonzero class",
        ),
        "Requirement-to-check traceability": (
            "XCOM-BLD-001",
            "XCOM-BLD-002",
            "XCOM-BLD-003",
            "XCOM-BLD-004",
            "XCOM-BLD-005",
            "VM-BLD-UNIT",
            "VM-BLD-INTEGRATION",
            "VM-BLD-VALIDATION",
        ),
    }
    for heading, markers in required_by_section.items():
        body = sections.get(heading, "")
        for marker in markers:
            if marker.lower() not in body.lower():
                errors.append(
                    diagnostic(
                        "XCOM-BLD-E055",
                        ExitCode.POLICY_INVALID,
                        f"build-environment.md#{heading}",
                        f"required environment declaration is missing: {marker}",
                    )
                )

    for marker in (
        "prototype-only",
        "capability 007, slice 1",
        "no X-COM runtime behavior",
        "no compatibility",
        "production-readiness",
    ):
        if marker.lower() not in text.lower():
            errors.append(
                diagnostic(
                    "XCOM-BLD-E055",
                    ExitCode.POLICY_INVALID,
                    "build-environment.md#maturity",
                    f"prototype maturity boundary is missing: {marker}",
                )
            )
    return sorted(set(errors))


def _read_repository_document(path: Path) -> tuple[str | None, list[Diagnostic]]:
    """Read one repository document without suppressing validation of its peer."""

    try:
        if not path.is_file():
            raise FileNotFoundError(path)
        return path.read_text(encoding="utf-8"), []
    except (OSError, UnicodeError):
        return None, [
            diagnostic(
                "XCOM-BLD-E050",
                ExitCode.POLICY_INVALID,
                path.name,
                "required build document is missing or unreadable",
            )
        ]


def verify_repository_documents() -> list[Diagnostic]:
    """Verify both public build documents through independent contracts."""

    document_root = REPOSITORY_ROOT / "docs/engineering/xcom"
    lock_text, lock_errors = _read_repository_document(
        document_root / "dependency-lock.md"
    )
    environment_text, environment_errors = _read_repository_document(
        document_root / "build-environment.md"
    )
    errors = [*lock_errors, *environment_errors]
    if lock_text is not None:
        errors.extend(validate_dependency_lock_document(lock_text))
    if environment_text is not None:
        errors.extend(validate_build_environment_document(environment_text))
    return sorted(set(errors))


def load_cmake_policy_evidence(
    path: Path,
) -> tuple[CMakePolicyEvidence | None, list[Diagnostic]]:
    """Load the exact schema emitted by the generated CMake policy probe."""

    try:
        evidence_exists = path.is_file()
    except OSError:
        return None, [
            diagnostic(
                "XCOM-BLD-E091",
                ExitCode.IO_ERROR,
                "xcom-build-policy.json",
                "CMake policy evidence could not be inspected",
            )
        ]
    if not evidence_exists:
        return None, [
            diagnostic(
                "XCOM-BLD-E090",
                ExitCode.POLICY_INVALID,
                "xcom-build-policy.json",
                "CMake policy evidence is missing",
            )
        ]
    try:
        value: object = json.loads(path.read_text(encoding="utf-8"))
    except PermissionError:
        return None, [
            diagnostic(
                "XCOM-BLD-E091",
                ExitCode.IO_ERROR,
                "xcom-build-policy.json",
                "CMake policy evidence is not readable",
            )
        ]
    except OSError:
        return None, [
            diagnostic(
                "XCOM-BLD-E091",
                ExitCode.IO_ERROR,
                "xcom-build-policy.json",
                "CMake policy evidence could not be read",
            )
        ]
    except (UnicodeError, json.JSONDecodeError):
        return None, [
            diagnostic(
                "XCOM-BLD-E092",
                ExitCode.POLICY_INVALID,
                "xcom-build-policy.json",
                "CMake policy evidence is not valid UTF-8 JSON",
            )
        ]

    fields = {
        "schema_version",
        "probe_target",
        "compiler",
        "compiler_id",
        "compiler_version",
        "generator",
        "cxx_standard",
        "cxx_standard_required",
        "cxx_extensions",
        "build_testing",
        "warnings_as_errors",
        "warning_options",
        "toolchain_prefix",
        "package_manifest",
    }
    if not isinstance(value, dict) or set(value) != fields:
        return None, [
            diagnostic(
                "XCOM-BLD-E093",
                ExitCode.POLICY_INVALID,
                "xcom-build-policy.json",
                "CMake policy evidence fields do not match the accepted schema",
            )
        ]

    schema_version: object = value.get("schema_version")
    probe_target: object = value.get("probe_target")
    compiler: object = value.get("compiler")
    compiler_id: object = value.get("compiler_id")
    compiler_version: object = value.get("compiler_version")
    generator: object = value.get("generator")
    cxx_standard: object = value.get("cxx_standard")
    cxx_standard_required: object = value.get("cxx_standard_required")
    cxx_extensions: object = value.get("cxx_extensions")
    build_testing: object = value.get("build_testing")
    warnings_as_errors: object = value.get("warnings_as_errors")
    warning_options: object = value.get("warning_options")
    toolchain_prefix: object = value.get("toolchain_prefix")
    package_manifest: object = value.get("package_manifest")
    strings = (
        probe_target,
        compiler,
        compiler_id,
        compiler_version,
        generator,
        toolchain_prefix,
        package_manifest,
    )
    booleans = (
        cxx_standard_required,
        cxx_extensions,
        build_testing,
        warnings_as_errors,
    )
    if (
        type(schema_version) is not int
        or any(not isinstance(item, str) or not item for item in strings)
        or type(cxx_standard) is not int
        or any(type(item) is not bool for item in booleans)
        or not isinstance(warning_options, list)
        or not warning_options
        or any(not isinstance(item, str) or not item for item in warning_options)
    ):
        return None, [
            diagnostic(
                "XCOM-BLD-E094",
                ExitCode.POLICY_INVALID,
                "xcom-build-policy.json",
                "CMake policy evidence contains invalid field types",
            )
        ]

    assert isinstance(schema_version, int)
    assert isinstance(probe_target, str)
    assert isinstance(compiler, str)
    assert isinstance(compiler_id, str)
    assert isinstance(compiler_version, str)
    assert isinstance(generator, str)
    assert isinstance(cxx_standard, int)
    assert isinstance(cxx_standard_required, bool)
    assert isinstance(cxx_extensions, bool)
    assert isinstance(build_testing, bool)
    assert isinstance(warnings_as_errors, bool)
    assert isinstance(warning_options, list)
    assert all(isinstance(item, str) for item in warning_options)
    assert isinstance(toolchain_prefix, str)
    assert isinstance(package_manifest, str)
    return (
        CMakePolicyEvidence(
            schema_version,
            probe_target,
            compiler,
            compiler_id,
            compiler_version,
            generator,
            cxx_standard,
            cxx_standard_required,
            cxx_extensions,
            build_testing,
            warnings_as_errors,
            tuple(warning_options),
            toolchain_prefix,
            package_manifest,
        ),
        [],
    )


def _same_resolved_path(left: str | Path, right: str | Path) -> bool:
    """Compare path identities without requiring either path to be writable."""

    try:
        return Path(left).resolve() == Path(right).resolve()
    except OSError:
        return False


def validate_cmake_policy_evidence(
    evidence: CMakePolicyEvidence,
    selected_compiler: Path,
    prefix: Path,
    manifest: Path,
) -> list[Diagnostic]:
    """Validate recorded policy values against controlled configuration inputs."""

    errors: list[Diagnostic] = []
    if (
        evidence.schema_version != 1
        or evidence.probe_target != "xverse_xcom_policy_probe"
        or evidence.generator != "Ninja"
        or evidence.cxx_standard != 20
        or not evidence.cxx_standard_required
        or evidence.cxx_extensions
        or not evidence.build_testing
        or not evidence.warnings_as_errors
    ):
        errors.append(
            diagnostic(
                "XCOM-BLD-E095",
                ExitCode.POLICY_INVALID,
                "xcom-build-policy.json",
                "recorded CMake language, generator, testing, or warning policy differs",
            )
        )

    accepted_options = {
        "GNU": ("-Wall", "-Wextra", "-Wpedantic", "-Werror"),
        "Clang": ("-Wall", "-Wextra", "-Wpedantic", "-Werror"),
        "AppleClang": ("-Wall", "-Wextra", "-Wpedantic", "-Werror"),
        "MSVC": ("/W4", "/WX", "/permissive-"),
    }
    if evidence.warning_options != accepted_options.get(evidence.compiler_id):
        errors.append(
            diagnostic(
                "XCOM-BLD-E096",
                ExitCode.POLICY_INVALID,
                "warning-policy",
                "recorded warning options differ from the accepted compiler policy",
            )
        )
    if (
        not _same_resolved_path(evidence.compiler, selected_compiler)
        or not evidence.compiler_version
    ):
        errors.append(
            diagnostic(
                "XCOM-BLD-E097",
                ExitCode.POLICY_INVALID,
                "CMAKE_CXX_COMPILER",
                "recorded compiler differs from the compiler selected for CMake",
            )
        )
    if not _same_resolved_path(
        evidence.toolchain_prefix, prefix
    ) or not _same_resolved_path(evidence.package_manifest, manifest):
        errors.append(
            diagnostic(
                "XCOM-BLD-E098",
                ExitCode.POLICY_INVALID,
                "offline-inputs",
                "recorded offline inputs differ from the explicit admitted inputs",
            )
        )
    return sorted(errors)


def _warning_option_negates_policy(argument: str) -> bool:
    """Inspect one direct or driver-forwarded warning-policy option."""

    normalized = argument.lower()
    if (
        normalized in {"-w", "/w"}
        or normalized.startswith(("-wno-", "/wx-", "/wx:", "@"))
        or re.fullmatch(r"/w[0-3]", normalized) is not None
        or re.fullmatch(r"/wd[0-9]+", normalized) is not None
    ):
        return True

    forwarded_payload: str | None = None
    if normalized.startswith("-wp,"):
        forwarded_payload = normalized[len("-wp,") :]
    else:
        forwarded = re.fullmatch(
            r"-x(?:clang|compiler|preprocessor)[=,](.+)", normalized
        )
        if forwarded is not None:
            forwarded_payload = forwarded.group(1)
    return forwarded_payload is not None and any(
        _warning_option_negates_policy(item)
        for item in forwarded_payload.split(",")
        if item
    )


def policy_negating_warning_options(arguments: Sequence[str]) -> tuple[str, ...]:
    """Return direct, forwarded, or opaque options that can weaken policy."""

    return tuple(
        argument for argument in arguments if _warning_option_negates_policy(argument)
    )


def verify_probe_compile_command(
    path: Path,
    evidence: CMakePolicyEvidence,
    prefix: Path,
) -> list[Diagnostic]:
    """Corroborate policy evidence against CMake's concrete compiler command."""

    try:
        value: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return [
            diagnostic(
                "XCOM-BLD-E099",
                ExitCode.POLICY_INVALID,
                "compile_commands.json",
                "CMake compile-command evidence is missing or invalid",
            )
        ]
    if not isinstance(value, list):
        return [
            diagnostic(
                "XCOM-BLD-E099",
                ExitCode.POLICY_INVALID,
                "compile_commands.json",
                "CMake compile-command evidence is missing or invalid",
            )
        ]

    probe_entry: Mapping[object, object] | None = None
    for raw_entry in value:
        if not isinstance(raw_entry, dict):
            continue
        source: object = raw_entry.get("file")
        if isinstance(source, str) and Path(source).name == "xcom_policy_probe.cpp":
            probe_entry = raw_entry
            break
    if probe_entry is None:
        return [
            diagnostic(
                "XCOM-BLD-E100",
                ExitCode.POLICY_INVALID,
                "xverse_xcom_policy_probe",
                "compile-command evidence omits the generated policy probe",
            )
        ]

    raw_arguments: object = probe_entry.get("arguments")
    raw_command: object = probe_entry.get("command")
    arguments: list[str]
    if isinstance(raw_arguments, list) and all(
        isinstance(item, str) for item in raw_arguments
    ):
        arguments = [item for item in raw_arguments if isinstance(item, str)]
    elif isinstance(raw_command, str):
        try:
            arguments = shlex.split(raw_command)
        except ValueError:
            arguments = []
    else:
        arguments = []

    expected_include = prefix / "usr/include"
    include_paths: list[str] = []
    for index, argument in enumerate(arguments):
        if argument in {"-I", "-isystem"} and index + 1 < len(arguments):
            include_paths.append(arguments[index + 1])
        elif argument.startswith("-I") and len(argument) > 2:
            include_paths.append(argument[2:])
        elif argument.startswith("-isystem") and len(argument) > len("-isystem"):
            include_paths.append(argument[len("-isystem") :])

    required_options = (*evidence.warning_options, "-std=c++20", "-c")
    negating_options = policy_negating_warning_options(arguments)
    command_matches = (
        bool(arguments)
        and _same_resolved_path(arguments[0], evidence.compiler)
        and all(option in arguments for option in required_options)
        and any(_same_resolved_path(item, expected_include) for item in include_paths)
    )
    if not command_matches:
        return [
            diagnostic(
                "XCOM-BLD-E101",
                ExitCode.POLICY_INVALID,
                "xverse_xcom_policy_probe",
                "compile command does not corroborate compiler, C++20, warnings, or prefix",
            )
        ]
    if negating_options:
        return [
            diagnostic(
                "XCOM-BLD-E102",
                ExitCode.POLICY_INVALID,
                "xverse_xcom_policy_probe",
                "compile command contains a policy-negating warning option",
            )
        ]
    return []


def validate_warning_rejection_probe(returncode: int, output: str) -> list[Diagnostic]:
    """Require a corroborated warning-as-error failure from the fixture."""

    if returncode == 0:
        return [
            diagnostic(
                "XCOM-BLD-E103",
                ExitCode.POLICY_INVALID,
                "xverse_xcom_warning_rejection_probe",
                "intentional warning compiled successfully; warning-as-error is ineffective",
            )
        ]
    normalized_output = output.lower()
    expected_diagnostic = (
        "xcom_warning_rejection_probe.cpp" in normalized_output
        and "intentional_return_type_warning" in normalized_output
        and "return-type" in normalized_output
        and (
            "werror" in normalized_output or "treated as an error" in normalized_output
        )
    )
    if expected_diagnostic:
        return []
    return [
        diagnostic(
            "XCOM-BLD-E106",
            ExitCode.POLICY_INVALID,
            "xverse_xcom_warning_rejection_probe",
            "failed build did not prove the intentional warning became an error",
        )
    ]


def verify_cmake_envelope(prefix: Path, manifest: Path) -> list[Diagnostic]:
    """Configure and build the CMake policy probe in a disposable directory."""

    cmake = shutil.which("cmake")
    ninja = shutil.which("ninja")
    compiler = shutil.which("c++")
    missing = [
        name
        for name, location in (("cmake", cmake), ("ninja", ninja), ("c++", compiler))
        if location is None
    ]
    if missing:
        return [
            diagnostic(
                "XCOM-BLD-E060",
                ExitCode.TOOL_MISSING,
                name,
                "cannot validate the CMake build envelope",
            )
            for name in missing
        ]
    assert cmake is not None
    assert compiler is not None

    try:
        temporary_directory = tempfile.TemporaryDirectory(prefix="xcom-cmake-")
    except OSError:
        return [
            diagnostic(
                "XCOM-BLD-E109",
                ExitCode.IO_ERROR,
                "cmake-build-directory",
                "temporary CMake build directory could not be created",
            )
        ]

    with temporary_directory as temporary:
        build_dir = Path(temporary)
        try:
            configured = subprocess.run(
                [
                    cmake,
                    "-S",
                    str(REPOSITORY_ROOT),
                    "-B",
                    str(build_dir),
                    "-G",
                    "Ninja",
                    "-DBUILD_TESTING=ON",
                    "-DCMAKE_BUILD_TYPE=Debug",
                    "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
                    f"-DCMAKE_CXX_COMPILER={compiler}",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            return [
                diagnostic(
                    "XCOM-BLD-E062",
                    ExitCode.TIMEOUT,
                    "CMakeLists.txt",
                    "controlled Ninja configuration timed out",
                )
            ]
        except (OSError, subprocess.SubprocessError, UnicodeError):
            return [
                diagnostic(
                    "XCOM-BLD-E063",
                    ExitCode.PROBE_FAILED,
                    "CMakeLists.txt",
                    "controlled Ninja configuration could not execute",
                )
            ]
        if configured.returncode != 0:
            return [
                diagnostic(
                    "XCOM-BLD-E061",
                    ExitCode.POLICY_INVALID,
                    "CMakeLists.txt",
                    "controlled Ninja configuration failed",
                )
            ]

        try:
            built = subprocess.run(
                [
                    cmake,
                    "--build",
                    str(build_dir),
                    "--target",
                    "xverse_xcom_policy_probe",
                    "--verbose",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            return [
                diagnostic(
                    "XCOM-BLD-E088",
                    ExitCode.TIMEOUT,
                    "xverse_xcom_policy_probe",
                    "controlled policy-probe build timed out",
                )
            ]
        except (OSError, subprocess.SubprocessError, UnicodeError):
            return [
                diagnostic(
                    "XCOM-BLD-E089",
                    ExitCode.PROBE_FAILED,
                    "xverse_xcom_policy_probe",
                    "controlled policy-probe build could not execute",
                )
            ]
        if built.returncode != 0:
            return [
                diagnostic(
                    "XCOM-BLD-E064",
                    ExitCode.POLICY_INVALID,
                    "xverse_xcom_policy_probe",
                    "controlled policy-probe build failed",
                )
            ]

        probe_environment = os.environ.copy()
        probe_environment.update({"LANG": "C", "LC_ALL": "C"})
        try:
            warning_rejection = subprocess.run(
                [
                    cmake,
                    "--build",
                    str(build_dir),
                    "--target",
                    "xverse_xcom_warning_rejection_probe",
                    "--verbose",
                ],
                check=False,
                capture_output=True,
                env=probe_environment,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            return [
                diagnostic(
                    "XCOM-BLD-E104",
                    ExitCode.TIMEOUT,
                    "xverse_xcom_warning_rejection_probe",
                    "controlled warning-rejection probe timed out",
                )
            ]
        except (OSError, subprocess.SubprocessError, UnicodeError):
            return [
                diagnostic(
                    "XCOM-BLD-E105",
                    ExitCode.PROBE_FAILED,
                    "xverse_xcom_warning_rejection_probe",
                    "controlled warning-rejection probe could not execute",
                )
            ]
        rejection_output = f"{warning_rejection.stdout}\n{warning_rejection.stderr}"
        rejection_errors = validate_warning_rejection_probe(
            warning_rejection.returncode, rejection_output
        )
        if rejection_errors:
            return rejection_errors

        evidence, evidence_errors = load_cmake_policy_evidence(
            build_dir / "xcom-build-policy.json"
        )
        if evidence_errors:
            return evidence_errors
        assert evidence is not None
        errors = validate_cmake_policy_evidence(
            evidence, Path(compiler), prefix, manifest
        )
        errors.extend(
            verify_probe_compile_command(
                build_dir / "compile_commands.json", evidence, prefix
            )
        )
        return sorted(errors)


def explicit_inputs() -> tuple[Path | None, Path | None, list[Diagnostic]]:
    """Resolve only the two explicit environment inputs accepted by the CLI."""

    prefix_text = os.environ.get(TOOLCHAIN_ENV)
    manifest_text = os.environ.get(MANIFEST_ENV)
    errors: list[Diagnostic] = []
    if not prefix_text:
        errors.append(
            diagnostic(
                "XCOM-BLD-E070",
                ExitCode.INPUT_MISSING,
                TOOLCHAIN_ENV,
                "explicit toolchain prefix is unset",
            )
        )
    if not manifest_text:
        errors.append(
            diagnostic(
                "XCOM-BLD-E071",
                ExitCode.INPUT_MISSING,
                MANIFEST_ENV,
                "explicit package manifest is unset",
            )
        )
    try:
        prefix = Path(prefix_text).resolve() if prefix_text else None
        manifest = Path(manifest_text).resolve() if manifest_text else None
    except OSError:
        errors.append(
            diagnostic(
                "XCOM-BLD-E073",
                ExitCode.IO_ERROR,
                "environment",
                "explicit input path could not be resolved",
            )
        )
        return None, None, sorted(errors)
    if prefix is not None:
        try:
            prefix_exists = prefix.is_dir()
        except OSError:
            errors.append(
                diagnostic(
                    "XCOM-BLD-E073",
                    ExitCode.IO_ERROR,
                    TOOLCHAIN_ENV,
                    "explicit toolchain prefix could not be inspected",
                )
            )
        else:
            if not prefix_exists:
                errors.append(
                    diagnostic(
                        "XCOM-BLD-E072",
                        ExitCode.INPUT_MISSING,
                        TOOLCHAIN_ENV,
                        "explicit toolchain prefix is missing",
                    )
                )
    return prefix, manifest, sorted(errors)


def run_dependency_admission() -> tuple[Path | None, Path | None, list[Diagnostic]]:
    """Validate explicit package inputs and their extracted prefix binding."""

    prefix, manifest, errors = explicit_inputs()
    if errors:
        return prefix, manifest, errors
    assert prefix is not None and manifest is not None
    _, manifest_errors = load_manifest(manifest)
    errors.extend(manifest_errors)
    dependency_chain_valid = not manifest_errors
    if dependency_chain_valid:
        package_errors = verify_package_files(manifest)
        errors.extend(package_errors)
        dependency_chain_valid = not package_errors
        if dependency_chain_valid:
            metadata_errors = verify_package_metadata(manifest)
            errors.extend(metadata_errors)
            dependency_chain_valid = not metadata_errors
            if dependency_chain_valid:
                payload_errors = verify_payload_binding(prefix, manifest)
                errors.extend(payload_errors)
                dependency_chain_valid = not payload_errors
    errors.extend(verify_prefix(prefix, execute_probes=dependency_chain_valid))
    return prefix, manifest, sorted(set(errors))


def run_admission(include_validation: bool) -> list[Diagnostic]:
    """Run offline admission, optionally including the built CMake probe."""

    prefix, manifest, errors = run_dependency_admission()
    if prefix is None or manifest is None:
        return errors
    dependency_admitted = not errors
    if dependency_admitted:
        errors.extend(verify_build_tools())
    # License declarations and generated-code provenance are part of
    # dependency admission, not a validation-only afterthought.
    errors.extend(verify_repository_documents())
    if include_validation and not errors:
        errors.extend(verify_cmake_envelope(prefix, manifest))
    return sorted(set(errors))


def emit_report(errors: Iterable[Diagnostic]) -> int:
    """Emit the stable JSON report and return its classified nonzero result."""

    ordered = sorted(set(errors))
    report = {
        "admitted": not ordered,
        "diagnostics": [asdict(item) for item in ordered],
        "schema_version": 1,
    }
    if not ordered:
        report["diagnostics"] = [
            {
                "category": "ADMITTED",
                "code": "XCOM-BLD-I000",
                "message": "exact offline dependency set admitted",
                "subject": "xcom-build-foundation",
            }
        ]
    print(json.dumps(report, indent=2, sort_keys=True))
    return min((item.exit_code for item in ordered), default=int(ExitCode.ADMITTED))


class PreflightSelfTests(unittest.TestCase):
    """Table-driven regression tests for offline parser and probe failures."""

    def setUp(self) -> None:
        """Create an isolated fixture root for each self-test."""

        self.temporary = tempfile.TemporaryDirectory(prefix="xcom-preflight-")
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        """Remove the isolated fixture root."""

        self.temporary.cleanup()

    def _assert_valid_failure_report(self, errors: Sequence[Diagnostic]) -> None:
        """Require classified boundary diagnostics to retain the JSON protocol."""

        self.assertTrue(errors)
        with mock.patch("builtins.print") as output:
            result = emit_report(errors)
        self.assertNotEqual(result, int(ExitCode.ADMITTED))
        report = json.loads(output.call_args.args[0])
        self.assertFalse(report["admitted"])
        self.assertEqual(report["schema_version"], 1)
        self.assertTrue(report["diagnostics"])

    @staticmethod
    def _spec(filename: str = "fixture.deb", package: str = "fixture") -> PackageSpec:
        """Create a valid one-file lock specification for parser fixtures."""

        return PackageSpec(filename, "a" * 64, 1, package, "1", "fixture", "MIT")

    def _manifest_errors(
        self, value: object, lock: Sequence[PackageSpec] | None = None
    ) -> list[Diagnostic]:
        """Write JSON and return its parser diagnostics."""

        path = self.root / "manifest.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        _, errors = load_manifest(path, lock or (self._spec(),))
        return errors

    def test_missing_manifest_is_classified(self) -> None:
        """A missing explicit manifest remains an input failure."""

        _, errors = load_manifest(self.root / "missing.json", ())
        self.assertEqual(errors[0].category, "INPUT_MISSING")

    def test_manifest_shape_and_field_failures_are_table_driven(self) -> None:
        """Reject wrong shape, fields, digest syntax, size, and duplicate names."""

        valid = {"file": "fixture.deb", "sha256": "a" * 64, "size": 1}
        cases: tuple[tuple[str, object, str], ...] = (
            ("top-level", {"records": []}, "XCOM-BLD-E003"),
            ("record-type", ["not-a-record"], "XCOM-BLD-E004"),
            ("exact-fields", [{**valid, "extra": True}], "XCOM-BLD-E004"),
            ("safe-name", [{**valid, "file": "../fixture.deb"}], "XCOM-BLD-E005"),
            ("sha-length", [{**valid, "sha256": "a" * 63}], "XCOM-BLD-E017"),
            ("sha-case", [{**valid, "sha256": "A" * 64}], "XCOM-BLD-E017"),
            ("size-zero", [{**valid, "size": 0}], "XCOM-BLD-E018"),
            ("size-bool", [{**valid, "size": True}], "XCOM-BLD-E018"),
            ("duplicate", [valid, valid], "XCOM-BLD-E006"),
        )
        for name, value, expected_code in cases:
            with self.subTest(name=name):
                self.assertIn(
                    expected_code, {item.code for item in self._manifest_errors(value)}
                )

    def test_manifest_records_are_immutable_and_typed(self) -> None:
        """Return only immutable ManifestRecord values after validation."""

        records, errors = load_manifest(
            self._write_json_manifest(
                [{"file": "fixture.deb", "sha256": "a" * 64, "size": 1}]
            ),
            (self._spec(),),
        )
        self.assertEqual(errors, [])
        self.assertIsInstance(records[0], ManifestRecord)
        with self.assertRaises(AttributeError):
            records[0].size = 2  # type: ignore[misc]

    def _write_json_manifest(self, value: object) -> Path:
        """Write and return a UTF-8 JSON manifest fixture."""

        path = self.root / "manifest.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    @staticmethod
    def _without_markdown_section(text: str, heading: str) -> str:
        """Remove one complete level-two section for a negative fixture."""

        retained: list[str] = []
        removing = False
        for line in text.splitlines():
            if line.startswith("## "):
                removing = line.removeprefix("## ").strip() == heading
            if not removing:
                retained.append(line)
        return "\n".join(retained)

    def test_repository_documents_satisfy_independent_contracts(self) -> None:
        """Accept each authoritative document without borrowing peer content."""

        document_root = REPOSITORY_ROOT / "docs/engineering/xcom"
        lock_text = (document_root / "dependency-lock.md").read_text(encoding="utf-8")
        environment_text = (document_root / "build-environment.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(validate_dependency_lock_document(lock_text), [])
        self.assertEqual(validate_build_environment_document(environment_text), [])

    def test_empty_repository_documents_are_rejected_independently(self) -> None:
        """One populated peer cannot mask an empty required document."""

        self.assertEqual(
            validate_dependency_lock_document("")[0].code,
            "XCOM-BLD-E053",
        )
        self.assertEqual(
            validate_build_environment_document("")[0].code,
            "XCOM-BLD-E054",
        )

    def test_each_dependency_lock_section_is_required(self) -> None:
        """Reject removal of every exact lock and provenance section."""

        path = REPOSITORY_ROOT / "docs/engineering/xcom/dependency-lock.md"
        text = path.read_text(encoding="utf-8")
        for heading in LOCK_DOCUMENT_SECTIONS:
            with self.subTest(heading=heading):
                errors = validate_dependency_lock_document(
                    self._without_markdown_section(text, heading)
                )
                self.assertIn("XCOM-BLD-E053", {item.code for item in errors})

    def test_each_build_environment_section_is_required(self) -> None:
        """Reject removal of every environment, failure, and trace section."""

        path = REPOSITORY_ROOT / "docs/engineering/xcom/build-environment.md"
        text = path.read_text(encoding="utf-8")
        for heading in ENVIRONMENT_DOCUMENT_SECTIONS:
            with self.subTest(heading=heading):
                errors = validate_build_environment_document(
                    self._without_markdown_section(text, heading)
                )
                self.assertIn("XCOM-BLD-E054", {item.code for item in errors})

    def test_document_semantic_drift_is_rejected(self) -> None:
        """Reject package provenance, reconstruction, ABI, and variable drift."""

        document_root = REPOSITORY_ROOT / "docs/engineering/xcom"
        lock_text = (document_root / "dependency-lock.md").read_text(encoding="utf-8")
        environment_text = (document_root / "build-environment.md").read_text(
            encoding="utf-8"
        )
        package = PACKAGE_LOCK[0]
        lock_drift = lock_text.replace(package.source, "wrong-source", 1)
        self.assertIn(
            "XCOM-BLD-E051",
            {item.code for item in validate_dependency_lock_document(lock_drift)},
        )
        package_row = next(
            line for line in lock_text.splitlines() if f"`{package.file}`" in line
        )
        duplicate_row = lock_text.replace(
            package_row, f"{package_row}\n{package_row}", 1
        )
        self.assertIn(
            "XCOM-BLD-E051",
            {item.code for item in validate_dependency_lock_document(duplicate_row)},
        )
        for marker in (
            "dpkg-deb -x",
            "export LD_LIBRARY_PATH=",
            "ABI-compatible Ubuntu Jammy-derived host",
            "classified nonzero",
            "XCOM-BLD-005",
        ):
            with self.subTest(marker=marker):
                drifted = environment_text.replace(marker, "removed declaration")
                self.assertIn(
                    "XCOM-BLD-E055",
                    {
                        item.code
                        for item in validate_build_environment_document(drifted)
                    },
                )

    def test_manifest_text_failures_are_classified(self) -> None:
        """Convert permission, UTF-8, and JSON failures into diagnostics."""

        path = self.root / "manifest.json"
        cases = ((b"\xff", "XCOM-BLD-E002"), (b"{", "XCOM-BLD-E002"))
        for payload, expected_code in cases:
            with self.subTest(payload=payload):
                path.write_bytes(payload)
                _, errors = load_manifest(path, (self._spec(),))
                self.assertEqual(errors[0].code, expected_code)
        path.write_text("[]", encoding="utf-8")
        with mock.patch.object(Path, "read_text", side_effect=PermissionError):
            _, errors = load_manifest(path, (self._spec(),))
        self.assertEqual(errors[0].code, "XCOM-BLD-E009")

        with mock.patch.object(Path, "is_file", side_effect=PermissionError):
            _, errors = load_manifest(path, (self._spec(),))
        self.assertEqual(errors[0].code, "XCOM-BLD-E009")

    def test_lock_invariants_are_table_driven(self) -> None:
        """Reject wrong lock count and duplicate filenames or package names."""

        first = self._spec()
        cases = (
            ("count", (first,), 12, "XCOM-BLD-E013"),
            ("filename", (first, self._spec()), 2, "XCOM-BLD-E014"),
            (
                "package",
                (first, self._spec("second.deb")),
                2,
                "XCOM-BLD-E015",
            ),
        )
        for name, lock, count, expected_code in cases:
            with self.subTest(name=name):
                self.assertIn(
                    expected_code,
                    {item.code for item in validate_lock(lock, count)},
                )
        self.assertEqual(validate_lock(PACKAGE_LOCK), [])

    def test_wrong_hash_is_classified(self) -> None:
        """A package-byte mismatch returns HASH_MISMATCH."""

        package = self.root / "fixture.deb"
        package.write_bytes(b"observed")
        spec = PackageSpec(
            package.name,
            hashlib.sha256(b"expected").hexdigest(),
            len(b"observed"),
            "fixture",
            "1",
            "fixture",
            "MIT",
        )
        errors = verify_package_files(self.root / "manifest.json", (spec,))
        self.assertEqual(errors[0].category, "HASH_MISMATCH")

    def test_unreadable_package_is_classified(self) -> None:
        """A package read failure returns IO_ERROR instead of escaping."""

        package = self.root / "fixture.deb"
        package.write_bytes(b"x")
        with mock.patch(f"{__name__}.sha256_file", side_effect=PermissionError):
            errors = verify_package_files(self.root / "manifest.json", (self._spec(),))
        self.assertEqual(errors[0].category, "IO_ERROR")

        with (
            mock.patch.object(Path, "is_file", return_value=True),
            mock.patch.object(Path, "stat", side_effect=PermissionError),
        ):
            errors = verify_package_files(self.root / "manifest.json", (self._spec(),))
        self.assertEqual(errors[0].code, "XCOM-BLD-E012")

    def test_extraction_failures_are_table_driven(self) -> None:
        """Classify missing extractor, extraction timeout, and nonzero exit."""

        manifest = self.root / "manifest.json"
        destination = self.root / "reference"
        destination.mkdir()
        with mock.patch("shutil.which", return_value=None):
            errors = extract_reference_tree(manifest, destination, (self._spec(),))
        self.assertEqual(errors[0].code, "XCOM-BLD-E080")

        with (
            mock.patch("shutil.which", return_value="/usr/bin/dpkg-deb"),
            mock.patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(["dpkg-deb"], 30),
            ),
        ):
            errors = extract_reference_tree(manifest, destination, (self._spec(),))
        self.assertEqual(errors[0].code, "XCOM-BLD-E081")

        completed: subprocess.CompletedProcess[bytes] = subprocess.CompletedProcess(
            ["dpkg-deb"], returncode=1
        )
        with (
            mock.patch("shutil.which", return_value="/usr/bin/dpkg-deb"),
            mock.patch("subprocess.run", return_value=completed),
        ):
            errors = extract_reference_tree(manifest, destination, (self._spec(),))
        self.assertEqual(errors[0].code, "XCOM-BLD-E082")

    def test_temporary_payload_reference_failure_is_classified(self) -> None:
        """Contain temporary-directory creation failures before extraction."""

        with mock.patch("tempfile.TemporaryDirectory", side_effect=PermissionError):
            errors = verify_payload_binding(
                self.root / "prefix", self.root / "manifest.json", (self._spec(),)
            )
        self.assertEqual(errors[0].code, "XCOM-BLD-E089")

    def _payload_trees(self, label: str = "default") -> tuple[Path, Path]:
        """Create matching tiny prefix and extracted-reference payload trees."""

        prefix = self.root / f"payload-{label}-prefix"
        reference = self.root / f"payload-{label}-reference"
        for tree in (prefix, reference):
            binary = tree / "usr/bin"
            binary.mkdir(parents=True)
            (binary / "tool.real").write_bytes(b"locked payload")
            (binary / "tool").symlink_to("tool.real")
            include = tree / "usr/include/google/protobuf"
            include.mkdir(parents=True)
            (include / "arena.h").write_bytes(b"locked arena header")
            library = tree / "usr/lib/x86_64-linux-gnu"
            library.mkdir(parents=True)
            (library / "libprotoc.so.23.0.4").write_bytes(b"locked library")
            (library / "libprotoc.so.23").symlink_to("libprotoc.so.23.0.4")
        return prefix, reference

    def test_payload_content_and_symlink_chain_are_compared(self) -> None:
        """Compare both a required symlink and the content reached through it."""

        prefix, reference = self._payload_trees()
        self.assertEqual(compare_payload_trees(prefix, reference), [])
        (prefix / "usr/bin/tool.real").write_bytes(b"different payload")
        errors = compare_payload_trees(prefix, reference)
        self.assertEqual(errors[0].code, "XCOM-BLD-E085")
        self.assertEqual(errors[0].subject, "usr/bin/tool.real")

    def test_complete_payload_negative_fixtures_are_classified(self) -> None:
        """Reject unselected header, library, and symlink-target drift."""

        cases = (
            (
                "arena",
                "usr/include/google/protobuf/arena.h",
                "missing",
                "XCOM-BLD-E084",
            ),
            (
                "libprotoc",
                "usr/lib/x86_64-linux-gnu/libprotoc.so.23.0.4",
                "bytes",
                "XCOM-BLD-E085",
            ),
            (
                "symlink",
                "usr/lib/x86_64-linux-gnu/libprotoc.so.23",
                "target",
                "XCOM-BLD-E086",
            ),
        )
        for label, relative, mutation, expected_code in cases:
            with self.subTest(label=label):
                prefix, reference = self._payload_trees(label)
                path = prefix / relative
                if mutation == "missing":
                    path.unlink()
                elif mutation == "bytes":
                    path.write_bytes(b"different library")
                else:
                    path.unlink()
                    path.symlink_to("libprotoc.so.23.0.3")
                errors = compare_payload_trees(prefix, reference)
                matching = [item for item in errors if item.subject == relative]
                self.assertEqual([item.code for item in matching], [expected_code])

    def test_extra_node_within_locked_destination_is_classified(self) -> None:
        """Reject nodes not delivered by the lock beneath a locked root."""

        prefix, reference = self._payload_trees("extra")
        extra = prefix / "usr/share/unlocked/data.txt"
        extra.parent.mkdir(parents=True)
        extra.write_bytes(b"ambient payload")
        errors = compare_payload_trees(prefix, reference)
        self.assertIn("XCOM-BLD-E107", {item.code for item in errors})
        self.assertIn(
            extra.relative_to(prefix).as_posix(), {item.subject for item in errors}
        )

    def test_payload_type_and_symlink_differences_are_classified(self) -> None:
        """Return distinct deterministic diagnostics for type and link drift."""

        prefix, reference = self._payload_trees()
        link = prefix / "usr/bin/tool"
        link.unlink()
        link.symlink_to("other.real")
        errors = compare_payload_trees(prefix, reference)
        self.assertEqual(errors[0].code, "XCOM-BLD-E086")

        link.unlink()
        link.write_bytes(b"locked payload")
        errors = compare_payload_trees(prefix, reference)
        self.assertEqual(errors[0].code, "XCOM-BLD-E084")

    def test_unreadable_payload_content_is_classified(self) -> None:
        """Convert payload file read failures into an IO_ERROR diagnostic."""

        prefix, reference = self._payload_trees()
        with mock.patch(f"{__name__}.sha256_file", side_effect=PermissionError):
            errors = compare_payload_trees(prefix, reference)
        self.assertEqual(errors[0].code, "XCOM-BLD-E087")

    def _prefix(self) -> Path:
        """Create a minimal positive isolated-prefix fixture."""

        prefix = self.root / "prefix"
        for relative in (
            "usr/bin",
            "usr/include/nlohmann",
            "usr/include/google/protobuf/stubs",
            "usr/include/google/protobuf",
            "usr/include/grpcpp",
            "usr/lib/x86_64-linux-gnu/pkgconfig",
            "usr/lib/pkgconfig",
        ):
            (prefix / relative).mkdir(parents=True, exist_ok=True)
        scripts = {
            "protoc": "libprotoc 3.12.4",
            "clang-tidy": "LLVM version 14.0.0",
            "grpc_cpp_plugin": "",
        }
        for name, output in scripts.items():
            path = prefix / "usr/bin" / name
            path.write_text(f"#!/bin/sh\nprintf '%s\\n' '{output}'\n", encoding="utf-8")
            path.chmod(0o755)
        (prefix / "usr/include/nlohmann/json.hpp").write_text(
            "NLOHMANN_JSON_VERSION_MAJOR 3\nNLOHMANN_JSON_VERSION_MINOR 10\nNLOHMANN_JSON_VERSION_PATCH 5\n",
            encoding="utf-8",
        )
        (prefix / "usr/include/google/protobuf/message.h").touch()
        (prefix / "usr/include/google/protobuf/stubs/common.h").write_text(
            "GOOGLE_PROTOBUF_VERSION 3012004\n", encoding="utf-8"
        )
        (prefix / "usr/include/grpcpp/grpcpp.h").touch()
        for name in ("libprotobuf.a", "libgrpc.so", "libgrpc++.so"):
            (prefix / "usr/lib/x86_64-linux-gnu" / name).touch()
        (prefix / "usr/lib/pkgconfig/nlohmann_json.pc").write_text(
            "Version: 3.10.5\n", encoding="utf-8"
        )
        (prefix / "usr/lib/x86_64-linux-gnu/pkgconfig/protobuf.pc").write_text(
            "Version: 3.12.4\n", encoding="utf-8"
        )
        (prefix / "usr/lib/x86_64-linux-gnu/pkgconfig/grpc++.pc").write_text(
            "Version: 1.30.2\n", encoding="utf-8"
        )
        return prefix

    def test_prefix_present(self) -> None:
        """The controlled positive prefix produces no diagnostics."""

        self.assertEqual(verify_prefix(self._prefix()), [])

    def test_prefix_inspection_failure_is_classified(self) -> None:
        """Convert prefix Path.is_file failures into stable IO diagnostics."""

        with mock.patch.object(Path, "is_file", side_effect=PermissionError):
            errors = verify_prefix(self.root / "prefix")
        self.assertTrue(errors)
        self.assertEqual({item.category for item in errors}, {"IO_ERROR"})

    def test_rejected_hash_never_executes_prefix_binaries(self) -> None:
        """Keep executable probes behind the complete dependency admission chain."""

        prefix = self._prefix()
        manifest = self.root / "manifest.json"
        manifest.touch()
        hash_error = diagnostic(
            "XCOM-BLD-E011",
            ExitCode.HASH_MISMATCH,
            "fixture.deb",
            "package byte size or SHA-256 mismatches the lock",
        )
        with (
            mock.patch.dict(
                os.environ,
                {TOOLCHAIN_ENV: str(prefix), MANIFEST_ENV: str(manifest)},
            ),
            mock.patch(f"{__name__}.load_manifest", return_value=([], [])),
            mock.patch(f"{__name__}.verify_package_files", return_value=[hash_error]),
            mock.patch(f"{__name__}.verify_package_metadata") as metadata_probe,
            mock.patch(f"{__name__}.verify_payload_binding") as payload_probe,
            mock.patch(f"{__name__}._run_version") as version_probe,
        ):
            _, _, errors = run_dependency_admission()
        self.assertIn(hash_error, errors)
        metadata_probe.assert_not_called()
        payload_probe.assert_not_called()
        version_probe.assert_not_called()

    def test_rejected_hash_stops_full_admission_executable_probes(self) -> None:
        """Keep every executable phase behind full dependency admission."""

        prefix = self._prefix()
        manifest = self.root / "manifest.json"
        manifest.touch()
        hash_error = diagnostic(
            "XCOM-BLD-E011",
            ExitCode.HASH_MISMATCH,
            "fixture.deb",
            "package byte size or SHA-256 mismatches the lock",
        )
        prefix_path = str(prefix / "usr/bin")
        with (
            mock.patch.dict(
                os.environ,
                {
                    TOOLCHAIN_ENV: str(prefix),
                    MANIFEST_ENV: str(manifest),
                    "PATH": f"{prefix_path}{os.pathsep}{os.environ.get('PATH', '')}",
                },
            ),
            mock.patch(f"{__name__}.load_manifest", return_value=([], [])),
            mock.patch(f"{__name__}.verify_package_files", return_value=[hash_error]),
            mock.patch(f"{__name__}.verify_package_metadata") as metadata_probe,
            mock.patch(f"{__name__}.verify_payload_binding") as payload_probe,
            mock.patch(f"{__name__}.verify_build_tools") as build_tool_probe,
            mock.patch(f"{__name__}.verify_cmake_envelope") as cmake_probe,
            mock.patch(f"{__name__}.verify_repository_documents", return_value=[]),
            mock.patch("subprocess.run") as executable_probe,
        ):
            errors = run_admission(include_validation=True)
        self.assertIn(hash_error, errors)
        metadata_probe.assert_not_called()
        payload_probe.assert_not_called()
        build_tool_probe.assert_not_called()
        cmake_probe.assert_not_called()
        executable_probe.assert_not_called()

    def test_each_dependency_rejection_stops_full_executable_entry(self) -> None:
        """Gate executable phases after every dependency prerequisite failure."""

        prefix = self._prefix()
        manifest = self.root / "manifest.json"
        manifest.touch()
        cases = (
            ("manifest", "XCOM-BLD-E002", ExitCode.MANIFEST_INVALID),
            ("package-hash", "XCOM-BLD-E011", ExitCode.HASH_MISMATCH),
            ("debian-metadata", "XCOM-BLD-E022", ExitCode.VERSION_MISMATCH),
            ("extraction", "XCOM-BLD-E082", ExitCode.PROBE_FAILED),
            ("payload-binding", "XCOM-BLD-E085", ExitCode.PAYLOAD_MISMATCH),
        )
        for stage, code, category in cases:
            with self.subTest(stage=stage):
                stage_error = diagnostic(code, category, stage, "rejected fixture")
                manifest_errors = [stage_error] if stage == "manifest" else []
                package_errors = [stage_error] if stage == "package-hash" else []
                metadata_errors = [stage_error] if stage == "debian-metadata" else []
                payload_errors = (
                    [stage_error]
                    if stage in {"extraction", "payload-binding"}
                    else []
                )
                with (
                    mock.patch.dict(
                        os.environ,
                        {
                            TOOLCHAIN_ENV: str(prefix),
                            MANIFEST_ENV: str(manifest),
                        },
                    ),
                    mock.patch(
                        f"{__name__}.load_manifest",
                        return_value=([], manifest_errors),
                    ),
                    mock.patch(
                        f"{__name__}.verify_package_files",
                        return_value=package_errors,
                    ),
                    mock.patch(
                        f"{__name__}.verify_package_metadata",
                        return_value=metadata_errors,
                    ),
                    mock.patch(
                        f"{__name__}.verify_payload_binding",
                        return_value=payload_errors,
                    ),
                    mock.patch(f"{__name__}.verify_build_tools") as build_probe,
                    mock.patch(f"{__name__}.verify_cmake_envelope") as cmake_probe,
                    mock.patch(
                        f"{__name__}.verify_repository_documents", return_value=[]
                    ),
                    mock.patch("subprocess.run") as executable_probe,
                ):
                    errors = run_admission(include_validation=True)
                self.assertIn(stage_error, errors)
                build_probe.assert_not_called()
                cmake_probe.assert_not_called()
                executable_probe.assert_not_called()

    def test_expected_operational_boundaries_emit_valid_json(self) -> None:
        """Keep every required failure boundary classified and JSON serializable."""

        manifest = self.root / "manifest.json"
        manifest.write_text("[]", encoding="utf-8")
        package = self.root / "fixture.deb"
        package.write_bytes(b"x")
        spec = self._spec()

        with mock.patch.object(Path, "is_file", side_effect=PermissionError):
            _, inspection_errors = load_manifest(manifest, (spec,))
        self._assert_valid_failure_report(inspection_errors)

        with mock.patch.object(Path, "read_text", side_effect=PermissionError):
            _, read_errors = load_manifest(manifest, (spec,))
        self._assert_valid_failure_report(read_errors)

        with (
            mock.patch.object(Path, "is_file", return_value=True),
            mock.patch.object(Path, "stat", side_effect=PermissionError),
        ):
            stat_errors = verify_package_files(manifest, (spec,))
        self._assert_valid_failure_report(stat_errors)

        subprocess_failures = (
            UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid"),
            subprocess.TimeoutExpired(["probe"], 30),
            OSError("denied"),
        )
        for failure in subprocess_failures:
            with self.subTest(failure=type(failure).__name__):
                with mock.patch("subprocess.run", side_effect=failure):
                    observation = _run_version(Path("probe"))
                assert observation.failure is not None
                self._assert_valid_failure_report(
                    [_version_probe_diagnostic("probe", observation.failure)]
                )

        with mock.patch("tempfile.TemporaryDirectory", side_effect=PermissionError):
            payload_errors = verify_payload_binding(prefix=self.root, manifest_path=manifest)
        self._assert_valid_failure_report(payload_errors)

        available_tools = {
            "cmake": "/controlled/cmake",
            "ninja": "/controlled/ninja",
            "c++": "/controlled/c++",
        }
        with (
            mock.patch("shutil.which", side_effect=available_tools.get),
            mock.patch("tempfile.TemporaryDirectory", side_effect=PermissionError),
        ):
            cmake_errors = verify_cmake_envelope(self.root, manifest)
        self._assert_valid_failure_report(cmake_errors)

    def test_missing_executable_header_and_library_are_classified(self) -> None:
        """Missing prefix artifacts retain distinct classifications."""

        prefix = self._prefix()
        (prefix / "usr/bin/protoc").unlink()
        (prefix / "usr/include/grpcpp/grpcpp.h").unlink()
        (prefix / "usr/lib/x86_64-linux-gnu/libgrpc++.so").unlink()
        categories = {item.category for item in verify_prefix(prefix)}
        self.assertTrue(
            {"TOOL_MISSING", "HEADER_MISSING", "LIBRARY_MISSING"} <= categories
        )

    def test_prefix_version_drift_is_classified(self) -> None:
        """Longer tool, header, and metadata versions cannot match the lock."""

        prefix = self._prefix()
        (prefix / "usr/bin/protoc").write_text(
            "#!/bin/sh\nprintf '%s\\n' 'libprotoc 3.12.40'\n", encoding="utf-8"
        )
        (prefix / "usr/include/google/protobuf/stubs/common.h").write_text(
            "GOOGLE_PROTOBUF_VERSION 30120040\n", encoding="utf-8"
        )
        (prefix / "usr/lib/x86_64-linux-gnu/pkgconfig/protobuf.pc").write_text(
            "Version: 3.12.40\n", encoding="utf-8"
        )
        subjects = {
            item.subject
            for item in verify_prefix(prefix)
            if item.category == "VERSION_MISMATCH"
        }
        self.assertTrue({"protoc", "Protocol Buffers"} <= subjects)

    def test_command_failures_are_table_driven(self) -> None:
        """Convert subprocess execution and timeout failures deterministically."""

        cases = (
            (OSError("denied"), ProbeFailure.EXECUTION),
            (
                UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid"),
                ProbeFailure.EXECUTION,
            ),
            (subprocess.TimeoutExpired(["probe"], 30), ProbeFailure.TIMEOUT),
        )
        for failure, expected in cases:
            with self.subTest(expected=expected):
                with mock.patch("subprocess.run", side_effect=failure):
                    observed = _run_version(Path("probe"))
                self.assertIs(observed.failure, expected)

    def test_exact_version_boundaries_are_table_driven(self) -> None:
        """Reject numeric and dotted extensions of an expected version."""

        cases = (
            ("libprotoc 3.12.4", True),
            ("libprotoc 3.12.40", False),
            ("libprotoc 3.12.4.1", False),
            ("libprotoc 13.12.4", False),
        )
        for description, expected in cases:
            with self.subTest(description=description):
                self.assertEqual(_has_exact_version(description, "3.12.4"), expected)

    def test_build_tool_probe_failure_is_not_reported_missing(self) -> None:
        """Do not duplicate an execution failure as TOOL_MISSING."""

        observation = CommandObservation(None, ProbeFailure.EXECUTION)
        with (
            mock.patch("shutil.which", return_value="/controlled/tool"),
            mock.patch(f"{__name__}._run_version", return_value=observation),
        ):
            errors = verify_build_tools()
        self.assertEqual({item.category for item in errors}, {"PROBE_FAILED"})

    def test_build_tool_descriptions_present_missing_and_mismatched(self) -> None:
        """Cover present, missing, and old controlled build descriptions."""

        self.assertEqual(
            validate_build_tool_descriptions(
                {"cmake": "3.22.1", "ninja": "1.10.1", "c++": "11.4.0"}
            ),
            [],
        )
        missing = validate_build_tool_descriptions(
            {"cmake": None, "ninja": "1.10.1", "c++": "11.4.0"}
        )
        mismatch = validate_build_tool_descriptions(
            {"cmake": "3.21.0", "ninja": "1.10.1", "c++": "11.4.0"}
        )
        self.assertEqual(missing[0].category, "TOOL_MISSING")
        self.assertEqual(mismatch[0].category, "VERSION_MISMATCH")

    def _policy_evidence(self) -> CMakePolicyEvidence:
        """Create accepted CMake policy evidence rooted in this fixture."""

        return CMakePolicyEvidence(
            schema_version=1,
            probe_target="xverse_xcom_policy_probe",
            compiler=str(self.root / "c++"),
            compiler_id="GNU",
            compiler_version="11.4.0",
            generator="Ninja",
            cxx_standard=20,
            cxx_standard_required=True,
            cxx_extensions=False,
            build_testing=True,
            warnings_as_errors=True,
            warning_options=("-Wall", "-Wextra", "-Wpedantic", "-Werror"),
            toolchain_prefix=str(self.root / "prefix"),
            package_manifest=str(self.root / "manifest.json"),
        )

    def test_cmake_policy_evidence_schema_is_strict(self) -> None:
        """Classify missing, malformed, and correctly typed policy evidence."""

        path = self.root / "xcom-build-policy.json"
        evidence, errors = load_cmake_policy_evidence(path)
        self.assertIsNone(evidence)
        self.assertEqual(errors[0].code, "XCOM-BLD-E090")

        path.write_text("{}", encoding="utf-8")
        _, errors = load_cmake_policy_evidence(path)
        self.assertEqual(errors[0].code, "XCOM-BLD-E093")

        expected = self._policy_evidence()
        path.write_text(json.dumps(asdict(expected)), encoding="utf-8")
        observed, errors = load_cmake_policy_evidence(path)
        self.assertEqual(errors, [])
        self.assertEqual(observed, expected)

    def test_cmake_policy_drift_is_classified(self) -> None:
        """Reject language, warning, compiler, and offline-input drift."""

        evidence = self._policy_evidence()
        accepted = validate_cmake_policy_evidence(
            evidence,
            self.root / "c++",
            self.root / "prefix",
            self.root / "manifest.json",
        )
        self.assertEqual(accepted, [])
        drifted = replace(
            evidence,
            cxx_standard=17,
            warning_options=("-Wall",),
            compiler=str(self.root / "other-c++"),
            toolchain_prefix=str(self.root / "other-prefix"),
        )
        self.assertEqual(
            {
                item.code
                for item in validate_cmake_policy_evidence(
                    drifted,
                    self.root / "c++",
                    self.root / "prefix",
                    self.root / "manifest.json",
                )
            },
            {"XCOM-BLD-E095", "XCOM-BLD-E096", "XCOM-BLD-E097", "XCOM-BLD-E098"},
        )

    def test_compile_command_corroborates_recorded_policy(self) -> None:
        """Require the generated probe command to contain every policy input."""

        evidence = self._policy_evidence()
        compiler = Path(evidence.compiler)
        compiler.touch()
        include = Path(evidence.toolchain_prefix) / "usr/include"
        include.mkdir(parents=True)
        source = self.root / "xcom_policy_probe.cpp"
        source.touch()
        path = self.root / "compile_commands.json"
        arguments = [
            str(compiler),
            *evidence.warning_options,
            "-isystem",
            str(include),
            "-std=c++20",
            "-c",
            str(source),
        ]
        path.write_text(
            json.dumps([{"file": str(source), "arguments": arguments}]),
            encoding="utf-8",
        )
        self.assertEqual(
            verify_probe_compile_command(path, evidence, include.parents[1]), []
        )

        arguments.remove("-Werror")
        path.write_text(
            json.dumps([{"file": str(source), "arguments": arguments}]),
            encoding="utf-8",
        )
        self.assertEqual(
            verify_probe_compile_command(path, evidence, include.parents[1])[0].code,
            "XCOM-BLD-E101",
        )

        arguments.append("-Werror")
        arguments.insert(1, "-w")
        path.write_text(
            json.dumps([{"file": str(source), "arguments": arguments}]),
            encoding="utf-8",
        )
        self.assertEqual(
            verify_probe_compile_command(path, evidence, include.parents[1])[0].code,
            "XCOM-BLD-E102",
        )

        arguments[1] = "-Wp,-Wno-error=return-type"
        path.write_text(
            json.dumps([{"file": str(source), "arguments": arguments}]),
            encoding="utf-8",
        )
        self.assertEqual(
            verify_probe_compile_command(path, evidence, include.parents[1])[0].code,
            "XCOM-BLD-E102",
        )

    def test_policy_negating_warning_options_are_table_driven(self) -> None:
        """Recognize direct, forwarded, opaque, and MSVC negations."""

        rejected = (
            "-w",
            "-Wno-unused",
            "-Wno-error",
            "-Wp,-Wno-error=return-type",
            "-Xclang=-Wno-error=return-type",
            "-Xcompiler,-w",
            "@warning-policy.rsp",
            "/w",
            "/W0",
            "/wd4189",
            "/WX-",
        )
        for option in rejected:
            with self.subTest(option=option):
                self.assertEqual(policy_negating_warning_options([option]), (option,))
        self.assertEqual(
            policy_negating_warning_options(
                [
                    "-Wall",
                    "-Werror",
                    "-Wp,-DGENERATED_CODE=1",
                    "-Xclang=-Werror=return-type",
                    "/W4",
                    "/WX",
                ]
            ),
            (),
        )

    def test_cmake_rejects_inherited_and_cached_warning_negations(self) -> None:
        """Prove direct and forwarded suppressions cannot configure admission."""

        cmake = shutil.which("cmake")
        ninja = shutil.which("ninja")
        compiler = shutil.which("c++")
        if cmake is None or ninja is None or compiler is None:
            self.skipTest("CMake warning-policy regression requires build tools")

        cases = (
            ("environment-direct", "-w", None),
            ("environment-forwarded", "-Wp,-Wno-error=return-type", None),
            ("cache-direct", None, "-w"),
            ("cache-forwarded", None, "-Wp,-Wno-error=return-type"),
        )
        for name, environment_flags, cache_flags in cases:
            with self.subTest(name=name):
                build_dir = self.root / name
                command = [
                    cmake,
                    "-S",
                    str(REPOSITORY_ROOT),
                    "-B",
                    str(build_dir),
                    "-G",
                    "Ninja",
                    "-DBUILD_TESTING=ON",
                    f"-DCMAKE_CXX_COMPILER={compiler}",
                ]
                if cache_flags is not None:
                    command.append(f"-DCMAKE_CXX_FLAGS={cache_flags}")
                environment = os.environ.copy()
                environment.pop("CXXFLAGS", None)
                environment[TOOLCHAIN_ENV] = str(self.root / "prefix")
                environment[MANIFEST_ENV] = str(self.root / "manifest.json")
                if environment_flags is not None:
                    environment["CXXFLAGS"] = environment_flags
                result = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    env=environment,
                    text=True,
                    timeout=120,
                )
                output = f"{result.stdout}\n{result.stderr}"
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("X-COM warning policy rejects", output)

    def test_warning_rejection_probe_must_fail(self) -> None:
        """Only the expected warning-as-error failure proves the policy."""

        expected_output = (
            "xcom_warning_rejection_probe.cpp: error: "
            "intentional_return_type_warning [-Werror=return-type]"
        )
        self.assertEqual(validate_warning_rejection_probe(1, expected_output), [])
        self.assertEqual(
            validate_warning_rejection_probe(0, "")[0].code,
            "XCOM-BLD-E103",
        )
        self.assertEqual(
            validate_warning_rejection_probe(1, "unknown target")[0].code,
            "XCOM-BLD-E106",
        )

    def test_cmake_configure_and_build_failures_are_classified(self) -> None:
        """Keep configure/build nonzero and timeout results deterministic."""

        available_tools = {
            "cmake": "/controlled/cmake",
            "ninja": "/controlled/ninja",
            "c++": "/controlled/c++",
        }
        succeeded: subprocess.CompletedProcess[str] = subprocess.CompletedProcess(
            ["cmake"], 0, "", ""
        )
        failed: subprocess.CompletedProcess[str] = subprocess.CompletedProcess(
            ["cmake"], 1, "", ""
        )
        with (
            mock.patch("shutil.which", side_effect=available_tools.get),
            mock.patch("subprocess.run", return_value=failed),
        ):
            errors = verify_cmake_envelope(
                self.root / "prefix", self.root / "manifest.json"
            )
        self.assertEqual(errors[0].code, "XCOM-BLD-E061")

        with (
            mock.patch("shutil.which", side_effect=available_tools.get),
            mock.patch("subprocess.run", side_effect=[succeeded, failed]),
        ):
            errors = verify_cmake_envelope(
                self.root / "prefix", self.root / "manifest.json"
            )
        self.assertEqual(errors[0].code, "XCOM-BLD-E064")

        with (
            mock.patch("shutil.which", side_effect=available_tools.get),
            mock.patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(["cmake"], 120),
            ),
        ):
            errors = verify_cmake_envelope(
                self.root / "prefix", self.root / "manifest.json"
            )
        self.assertEqual(errors[0].code, "XCOM-BLD-E062")

        with (
            mock.patch("shutil.which", side_effect=available_tools.get),
            mock.patch(
                "subprocess.run",
                side_effect=[
                    succeeded,
                    subprocess.TimeoutExpired(["cmake", "--build"], 120),
                ],
            ),
        ):
            errors = verify_cmake_envelope(
                self.root / "prefix", self.root / "manifest.json"
            )
        self.assertEqual(errors[0].code, "XCOM-BLD-E088")

        with (
            mock.patch("shutil.which", side_effect=available_tools.get),
            mock.patch("tempfile.TemporaryDirectory", side_effect=PermissionError),
        ):
            errors = verify_cmake_envelope(
                self.root / "prefix", self.root / "manifest.json"
            )
        self.assertEqual(errors[0].code, "XCOM-BLD-E109")

    def test_final_cli_exception_boundary_emits_valid_json(self) -> None:
        """Contain an unexpected operational exception in the JSON protocol."""

        with (
            mock.patch(f"{__name__}.run_admission", side_effect=RuntimeError),
            mock.patch("builtins.print") as output,
        ):
            result = main(["--verify-toolchain"])
        self.assertEqual(result, int(ExitCode.PROBE_FAILED))
        report = json.loads(output.call_args.args[0])
        self.assertFalse(report["admitted"])
        self.assertEqual(report["diagnostics"][0]["code"], "XCOM-BLD-E108")


def run_self_tests() -> int:
    """Run embedded offline tests and return a conventional process status."""

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PreflightSelfTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the accepted CLI modes and return their admission status."""

    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--verify-toolchain", action="store_true")
    modes.add_argument("--all", action="store_true")
    modes.add_argument(
        "--cmake-dependency-check",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    arguments = parser.parse_args(argv)
    try:
        if arguments.self_test:
            return run_self_tests()
        if arguments.cmake_dependency_check:
            _, _, dependency_errors = run_dependency_admission()
            return emit_report(dependency_errors)
        return emit_report(run_admission(include_validation=True))
    except Exception:  # noqa: BLE001 - this is the final CLI containment boundary.
        return emit_report(
            [
                diagnostic(
                    "XCOM-BLD-E108",
                    ExitCode.PROBE_FAILED,
                    "dependency-preflight",
                    "unexpected admission failure was contained",
                )
            ]
        )


if __name__ == "__main__":
    sys.exit(main())
