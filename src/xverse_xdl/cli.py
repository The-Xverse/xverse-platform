"""Local command-line interface for XDL validation and normalization."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from . import SUPPORTED_API_VERSIONS, __version__
from .diagnostics import diagnostic_to_data
from .experiment_plan import (
    DIGEST_HEX_PATTERN, canonical_plan_bytes, compile_experiment_files, plan_public_data,
)
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
    experiment = subparsers.add_parser("experiment")
    experiment_commands = experiment.add_subparsers(dest="experiment_command", required=True)
    compile_parser = experiment_commands.add_parser("compile")
    compile_parser.add_argument("--profile-schema", action="append", default=[], metavar="PATH")
    compile_parser.add_argument("--run-id", metavar="ID")
    compile_parser.add_argument("--generated-at", metavar="RFC3339")
    compile_parser.add_argument("--expect-input-digest", action="append", default=[], metavar="NAME=SHA256")
    compile_parser.add_argument("--format", choices=("text", "json"), default="text")
    compile_parser.add_argument("-o", "--output", metavar="PLAN.json")
    compile_parser.add_argument("resources", nargs="+", metavar="RESOURCE")
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


def _experiment_text_report(result) -> str:
    """Render a resolved experiment plan or its rejection diagnostics as deterministic text."""

    if result.plan is not None:
        return f"resolved plan {result.plan['digest']['value']} ({len(result.plan)} sections)\n"
    lines: list[str] = []
    for item in result.diagnostics:
        location = item.location.source if item.location else "<input>"
        lines.append(
            f"{item.severity.value.upper()} {item.code} [{item.gate.name.lower()}] "
            f"{location}{item.pointer}: {item.message}\n  correction: {item.correction}"
        )
    return "\n".join(lines) + ("\n" if lines else "")


def _run_experiment(args) -> int:
    """Execute the additive ``xdl experiment compile`` subcommand."""

    expected: dict[str, str] = {}
    for value in args.expect_input_digest:
        name, separator, digest = str(value).partition("=")
        if not separator or not name or not DIGEST_HEX_PATTERN.match(digest):
            print("xdl: --expect-input-digest must be NAME=SHA256", file=sys.stderr)
            return 2
        expected[name] = digest
    resources = tuple(Path(value) for value in args.resources)
    profile_schemas = tuple(Path(value) for value in args.profile_schema)
    if args.output:
        output = Path(args.output)
        if output.resolve() in {path.resolve() for path in resources + profile_schemas}:
            print("xdl: output path is also an input resource", file=sys.stderr)
            return 2
    try:
        result = compile_experiment_files(
            resources, profile_schema_paths=profile_schemas, run_id=args.run_id,
            generated_at=args.generated_at,
            expected_input_semantic_digests=expected if expected else None,
        )
    except Exception as error:  # invocation and internal failures follow the accepted exit code 2
        print(f"xdl: internal capability failure: {error}", file=sys.stderr)
        return 2
    if args.format == "json":
        sys.stdout.write(
            json.dumps(plan_public_data(result), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        )
    elif result.plan is not None:
        sys.stdout.write(_experiment_text_report(result))
    else:
        sys.stderr.write(_experiment_text_report(result))
    if result.plan is None:
        # A failed internal digest self-check is an internal failure, not a declared rejection.
        if any(item.code == "XDL1-PLAN-DIGEST-SELFCHECK" for item in result.diagnostics):
            return 2
        return 1
    if args.output:
        try:
            Path(args.output).write_bytes(canonical_plan_bytes(result.plan) + b"\n")
        except OSError as error:
            print(f"xdl: cannot write output: {error}", file=sys.stderr)
            return 2
    return 0


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

    if args.command == "experiment":
        return _run_experiment(args)

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
