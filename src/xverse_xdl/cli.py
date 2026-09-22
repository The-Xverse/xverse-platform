"""Local command-line interface for XDL validation and normalization."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from . import SUPPORTED_API_VERSIONS, __version__
from .diagnostics import diagnostic_to_data
from .normalize import canonical_json
from .validate import validate_files


def _parser() -> argparse.ArgumentParser:
    """Build the command parser for validation, normalization, and version output."""

    parser = argparse.ArgumentParser(prog="xdl", description="Offline XDL v1alpha1 validator and normalizer")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "normalize"):
        child = subparsers.add_parser(command)
        child.add_argument("--profile-schema", action="append", default=[], metavar="PATH")
        child.add_argument("resources", nargs="+", metavar="RESOURCE")
        if command == "validate":
            child.add_argument("--format", choices=("text", "json"), default="text")
        else:
            child.add_argument("--include-source-map", action="store_true")
            child.add_argument("-o", "--output", metavar="PATH")
    version = subparsers.add_parser("version")
    version.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def _text_report(result) -> str:
    """Render a validation result as deterministic human-readable text."""

    if not result.diagnostics:
        return f"valid: {len(result.resources)} resource(s)\n"
    lines: list[str] = []
    for item in result.diagnostics:
        location = item.location.source if item.location else "<input>"
        if item.location and item.location.line is not None:
            location += f":{item.location.line}:{item.location.column or 1}"
        lines.append(
            f"{item.severity.value.upper()} {item.code} [{item.gate.name.lower()}] "
            f"{location}{item.pointer}: {item.message}\n  correction: {item.correction}"
        )
    return "\n".join(lines) + "\n"


def _validation_json(result) -> str:
    """Render the stable machine-readable validation report envelope."""

    value = {
        "reportVersion": "1",
        "toolVersion": __version__,
        "supportedApiVersions": list(SUPPORTED_API_VERSIONS),
        "valid": result.is_valid,
        "diagnostics": [diagnostic_to_data(item) for item in result.diagnostics],
        "readiness": dict(result.readiness),
        "resourceCount": len(result.resources),
    }
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def main(arguments: Sequence[str] | None = None) -> int:
    """Execute the local XDL CLI.

    @param arguments Optional argument sequence; ``None`` reads process arguments.
    @return Zero for success, one for invalid XDL, or two for invocation/internal failures.
    """

    parser = _parser()
    args = parser.parse_args(arguments)
    if args.command == "version":
        if args.format == "json":
            print(json.dumps({
                "toolVersion": __version__,
                "supportedApiVersions": list(SUPPORTED_API_VERSIONS),
            }, sort_keys=True, separators=(",", ":")))
        else:
            print(f"xverse-xdl {__version__} ({', '.join(SUPPORTED_API_VERSIONS)})")
        return 0

    resources = tuple(Path(value) for value in args.resources)
    profile_schemas = tuple(Path(value) for value in args.profile_schema)
    if args.command == "normalize" and args.output:
        output = Path(args.output)
        input_paths = resources + profile_schemas
        if output.resolve() in {path.resolve() for path in input_paths}:
            print("xdl: output path is also an input resource", file=sys.stderr)
            return 2
    try:
        result = validate_files(resources, profile_schema_paths=profile_schemas)
    except Exception as error:
        print(f"xdl: internal capability failure: {error}", file=sys.stderr)
        return 2
    if args.command == "validate":
        sys.stdout.write(_validation_json(result) if args.format == "json" else _text_report(result))
        return 0 if result.is_valid else 1

    if not result.resources or any(item.gate.value <= 4 for item in result.diagnostics):
        sys.stderr.write(_text_report(result))
        return 1
    output_text = canonical_json(result.resources, include_source_map=args.include_source_map)
    if args.output:
        try:
            Path(args.output).write_text(output_text, encoding="utf-8")
        except OSError as error:
            print(f"xdl: cannot write output: {error}", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(output_text)
    if result.diagnostics:
        sys.stderr.write(_text_report(result))
    return 0 if result.is_valid else 1
