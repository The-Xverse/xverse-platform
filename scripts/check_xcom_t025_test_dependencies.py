#!/usr/bin/env python3
"""Admit the exact offline GTest packages used by the T025 test targets."""

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile


PACKAGES = {
    "googletest_1.11.0-3_all.deb": (
        "googletest", "1.11.0-3", 541360,
        "7f665f45da5c1748ba85b7f7f1ff16e76ab9e6f61f2f09d8c4eb898d529c1b57",
    ),
    "libgmock-dev_1.11.0-3_amd64.deb": (
        "libgmock-dev", "1.11.0-3", 127506,
        "c34ed719d0fbb1cbcccddc3e0d119fb6b291719774f4f1465b5fe45453564f0c",
    ),
    "libgtest-dev_1.11.0-3_amd64.deb": (
        "libgtest-dev", "1.11.0-3", 250406,
        "43a86daecd536dfc36697053cf2e3351abe4c075f4963607af257faf38893317",
    ),
}


def fail(message: str) -> None:
    """Stop admission with a stable diagnostic code."""
    raise SystemExit(f"XCOM-T025-DEP-E001 {message}")


def same_payload(expected: Path, actual: Path) -> bool:
    """Compare a reference node with the independently provisioned prefix node."""
    if expected.is_symlink():
        return actual.is_symlink() and os.readlink(actual) == os.readlink(expected)
    if expected.is_file():
        return actual.is_file() and not actual.is_symlink() and (
            hashlib.sha256(expected.read_bytes()).digest()
            == hashlib.sha256(actual.read_bytes()).digest()
        )
    return expected.is_dir() and actual.is_dir() and not actual.is_symlink()


def main() -> None:
    """Check the three archives and every extracted node without installing packages."""
    if len(sys.argv) != 3:
        fail("usage: check_xcom_t025_test_dependencies.py PACKAGE_DIR PREFIX")
    package_dir, prefix = (Path(arg).resolve() for arg in sys.argv[1:])
    if not package_dir.is_dir() or not prefix.is_dir():
        fail("package directory or extracted prefix is missing")
    if {p.name for p in package_dir.glob("*.deb")} != set(PACKAGES):
        fail("package directory must contain exactly the three locked .deb files")
    with tempfile.TemporaryDirectory(prefix="xcom-t025-gtest-") as temp:
        reference = Path(temp)
        for filename, (name, version, size, sha256) in PACKAGES.items():
            package = package_dir / filename
            if package.stat().st_size != size or hashlib.sha256(package.read_bytes()).hexdigest() != sha256:
                fail(f"archive identity differs: {filename}")
            metadata = subprocess.check_output(
                ["dpkg-deb", "-f", str(package), "Package", "Version"], text=True
            ).splitlines()
            if metadata != [f"Package: {name}", f"Version: {version}"]:
                fail(f"package metadata differs: {filename}")
            subprocess.run(["dpkg-deb", "-x", str(package), str(reference)], check=True)
        for root, dirs, files in os.walk(reference, followlinks=False):
            for entry in dirs + files:
                source = Path(root) / entry
                target = prefix / source.relative_to(reference)
                if not same_payload(source, target):
                    fail(f"extracted payload differs: {source.relative_to(reference)}")
    print("XCOM-T025-DEP-I000 exact offline GTest archive and prefix payload admitted")


if __name__ == "__main__":
    main()
