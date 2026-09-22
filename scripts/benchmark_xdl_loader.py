#!/usr/bin/env python3
"""Bounded reference benchmark for capability 004 acceptance evidence."""

from __future__ import annotations

import json
import platform
import resource
import sys
import time

from xverse_xdl.validate import validate_mappings


def profile(index: int) -> dict:
    """Create one deterministic public-safe Profile benchmark resource."""

    return {
        "apiVersion": "xverse.io/xdl/v1alpha1",
        "kind": "Profile",
        "metadata": {
            "namespace": "org.xverse.benchmark",
            "name": f"profile-{index:03d}",
            "version": "0.1.0",
            "provenance": {
                "source": "generated-public-benchmark",
                "revision": "capability-004",
                "maturity": "prototype",
            },
        },
        "spec": {
            "extensionNamespace": f"org.xverse.benchmark.p{index:03d}",
            "compatibleApiVersions": ["xverse.io/xdl/v1alpha1"],
            "schemaRef": f"https://example.invalid/xverse/benchmark/p{index:03d}.json",
            "documentationRef": f"https://example.invalid/xverse/benchmark/p{index:03d}/",
            "conflictPolicy": "reject",
        },
    }


def main() -> int:
    """Validate 100 generated profiles and enforce bounded time and memory goals."""

    resources = tuple(profile(index) for index in range(100))
    started = time.perf_counter()
    result = validate_mappings(resources)
    elapsed = time.perf_counter() - started
    peak_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux reports KiB; macOS reports bytes.
    peak_mib = peak_kib / (1024 * 1024 if sys.platform == "darwin" else 1024)
    report = {
        "elapsedSeconds": round(elapsed, 6),
        "peakMiB": round(peak_mib, 3),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "resourceCount": len(resources),
        "valid": result.is_valid,
    }
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if result.is_valid and elapsed < 2.0 and peak_mib < 128 else 1


if __name__ == "__main__":
    raise SystemExit(main())
