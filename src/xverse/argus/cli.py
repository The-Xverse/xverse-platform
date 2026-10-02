"""Read-only ``xverse-argus`` command line entry point.

``verify <run-root>`` prints the manifest/verification summary as JSON and returns 0 for complete,
1 for incomplete/corrupt and 2 for a usage/input error. ``export <run-root> [--format json|jsonl]``
writes the canonical export to stdout. Writing is programmatic only through
``EvidenceStore.open_run``; the CLI never mutates a run root.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import Any

from .api import EvidenceStore
from .schema import canonical_json

__all__ = ["main"]

_USAGE = "usage: xverse-argus {verify|export} <run-root> [--format json|jsonl]"


def _summary(reader) -> dict[str, Any]:
    manifest = reader.manifest
    return {
        "runId": manifest.get("runId"),
        "writerState": manifest.get("writerState"),
        "evidenceStatus": reader.assessed_evidence_status,
        "evidenceReasons": reader.assessed_evidence_reasons,
        "recordedEvidenceStatus": reader.recorded_evidence_status,
        "recordedEvidenceReasons": reader.recorded_evidence_reasons,
        "assessedEvidenceStatus": reader.assessed_evidence_status,
        "assessedEvidenceReasons": reader.assessed_evidence_reasons,
        "eventCount": manifest.get("eventCount", 0),
        "diagnostics": [item.to_data() for item in reader.diagnostics],
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the read-only command line entry point and return the process exit status."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        print(_USAGE, file=sys.stderr)
        return 2
    command = arguments[0]
    if command == "verify":
        if len(arguments) != 2:
            print(_USAGE, file=sys.stderr)
            return 2
        reader = EvidenceStore.read_run(arguments[1])
        print(canonical_json(_summary(reader)))
        if reader.assessed_evidence_status == "complete" and not reader.diagnostics:
            return 0
        return 1
    if command == "export":
        if len(arguments) not in (2, 4):
            print(_USAGE, file=sys.stderr)
            return 2
        fmt = "json"
        if len(arguments) == 4:
            if arguments[2] != "--format":
                print(_USAGE, file=sys.stderr)
                return 2
            fmt = arguments[3]
        if fmt not in ("json", "jsonl"):
            print(_USAGE, file=sys.stderr)
            return 2
        reader = EvidenceStore.read_run(arguments[1])
        if fmt == "jsonl":
            sys.stdout.write(reader.export_jsonl())
        else:
            sys.stdout.write(reader.export_json())
        return 0
    print(_USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":  # pragma: no cover - module execution path
    raise SystemExit(main())
