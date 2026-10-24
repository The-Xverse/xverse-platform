#!/usr/bin/env python3
"""Build public reference material from an explicit set of platform inputs.

This tool parses headers and imports only admitted public Python package facades.
It never invokes a provider, launches an experiment, or reads engineering evidence.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "website"
GENERATED = SITE / "src/content/docs/docs/reference/generated"
PUBLIC = SITE / "public"
PACKAGES = ("xverse_xdl", "xverse.argus", "xverse.maestro", "xverse.faults", "xverse.flows")
PROFILES = (
    "experiment-lite-v0.1.schema.json",
    "runtime-compatibility-v0.1.schema.json",
    "runtime-compatibility-v0.2.schema.json",
    "xcom-v0.1.schema.json",
)
SCHEMAS = ("common", "component", "deployment", "profile", "scenario", "system", "xdl")
EXAMPLES = ("profile", "component", "system", "deployment", "scenario")


def clean_directory(path: Path) -> None:
    """Replace only a known, generated output directory, rejecting symlink escapes."""
    allowed = (GENERATED, PUBLIC / "reference", PUBLIC / "schemas", SITE / "reference/generated")
    if path not in allowed or path.is_symlink():
        raise ValueError(f"Refusing to clean non-generated directory: {path.name}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def write_page(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    slug = path.relative_to(SITE / "src/content/docs").with_suffix("").as_posix()
    header = f"---\ntitle: {json.dumps(title)}\nslug: {slug}\neditUrl: false\n---\n\n"
    path.write_text(header + body + "\n", encoding="utf-8")


def cell(value: object) -> str:
    return str(value).replace("|", "&#124;").replace("\n", " ").replace("<", "&lt;").replace(">", "&gt;")


def describe_schema(node: dict) -> str:
    """Retain every constraint rather than guessing how schema compositions merge."""
    return cell(json.dumps(node, ensure_ascii=False, sort_keys=True))


def schema_sections(schema: dict) -> str:
    """Render object fields with exact pointer locations, plus lossless schema JSON."""
    sections: list[str] = []

    def visit(node: object, pointer: str) -> None:
        if not isinstance(node, dict):
            return
        properties = node.get("properties", {})
        if properties:
            sections.extend([
                f"## `{pointer or '/'}`", "",
                "| Field | Required here | Definition and constraints |",
                "| --- | --- | --- |",
            ])
            for name, definition in properties.items():
                required = "Yes" if name in node.get("required", []) else "No"
                sections.append(f"| `{cell(name)}` | {required} | `{describe_schema(definition)}` |")
            sections.append("")
        for key, value in node.items():
            token = key.replace("~", "~0").replace("/", "~1")
            child_pointer = f"{pointer}/{token}"
            if isinstance(value, dict):
                visit(value, child_pointer)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    visit(child, f"{child_pointer}/{index}")

    visit(schema, "")
    sections.extend([
        "## Complete schema", "",
        "The complete schema is authoritative, including compositions, reference targets, and object-level constraints. “Required here” only describes the containing object; `anyOf` and other conditional requirements are preserved below.",
        "", "```json", json.dumps(schema, indent=2, ensure_ascii=False), "```", "",
    ])
    return "\n".join(sections)


def cli_help_tree(parser: argparse.ArgumentParser, prefix: tuple[str, ...] = ()) -> list[tuple[str, str]]:
    """Discover commands from the actual parser, including nested subcommands."""
    result = [(" ".join(("xdl", *prefix)), parser.format_help())]
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, child in action.choices.items():
                result.extend(cli_help_tree(child, (*prefix, name)))
    return result


def constant_value(value: object) -> object:
    """Serialize public constants deterministically without inherited builtin docstrings."""
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: constant_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): constant_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [constant_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [constant_value(item) for item in sorted(value)]
    if callable(value):
        return getattr(value, "__name__", type(value).__name__)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Unsupported public constant type: {type(value).__name__}")


def narrative_inputs(root: Path, mapping: dict) -> set[Path]:
    """Resolve the reviewed narrative source map, failing on missing/escaped inputs."""
    result: set[Path] = set()
    admitted_directories = {"src/xverse/xcom/include/xverse/xcom"}
    for sources in mapping["narrativeSources"].values():
        for name in sources:
            path = root / name
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError(f"Narrative source escapes repository: {name}")
            if path.is_dir() and name in admitted_directories:
                headers = list(path.glob("*.hpp"))
                if not headers:
                    raise ValueError(f"Empty admitted header directory: {name}")
                result.update(headers)
            elif path.is_file():
                result.add(path)
            else:
                raise ValueError(f"Missing or unadmitted narrative source: {name}")
    return result


def input_hashes(paths: set[Path], root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}


def normalize_cpp_language(text: str) -> str:
    """Use the site's English index across Doxygen versions (en-US vs no lang)."""
    def opening_tag(match: re.Match) -> str:
        attributes = re.sub(r'''\s+lang=(["'])[^"']*\1''', "", match.group(1), flags=re.IGNORECASE)
        return f'<html{attributes} lang="en">'

    return re.sub(r"<html\b([^>]*)>", opening_tag, text, count=1, flags=re.IGNORECASE)


def command(args: list[str], *, expected: int = 0, env: dict | None = None) -> str:
    completed = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, check=False)
    output = completed.stdout + completed.stderr
    if completed.returncode != expected:
        raise RuntimeError(f"{args[0]} failed ({completed.returncode}):\n{output[-16000:]}")
    if output.strip():
        print(output[-4000:].strip())
    return output


def validate_examples() -> None:
    from xverse_xdl import compile_experiment_files, validate_files

    schema = ROOT / "tests/fixtures/measurement-profile.schema.json"
    resources = [ROOT / f"xdl/examples/v1alpha1/{name}.xdl.yaml" for name in EXAMPLES]
    result = validate_files(resources, profile_schema_paths=[schema])
    if not result.is_valid:
        raise RuntimeError(f"Public example validation failed: {result.diagnostics}")
    lite = ROOT / "tests/thesis_lite/xdl/fixtures"
    compiled = compile_experiment_files(
        [lite / f"{name}.xdl.yaml" for name in EXAMPLES],
        profile_schema_paths=[ROOT / "xdl/profiles/experiment-lite-v0.1.schema.json"],
    )
    if compiled.plan is None:
        raise RuntimeError(f"Public experiment example compilation failed: {compiled.diagnostics}")
    home = validate_files([SITE / "examples/system.xdl.yaml"])
    if not home.is_valid:
        raise RuntimeError(f"Home-page example validation failed: {home.diagnostics}")
    print(f"Examples checked: {len(resources)} resources; experiment digest {compiled.plan['digest']['value']}")


def generate() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    if shutil.which("doxygen") is None:
        raise RuntimeError("Doxygen is required for the complete public reference build.")
    for path in (GENERATED, PUBLIC / "reference", PUBLIC / "schemas", SITE / "reference/generated"):
        clean_directory(path)
    (SITE / "reference/_build").mkdir(parents=True, exist_ok=True)
    inputs: set[Path] = set()

    def source(path: Path) -> str:
        if not path.is_file() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f"Missing or escaped publication input: {path.name}")
        inputs.add(path)
        return path.read_text(encoding="utf-8")

    config = tomllib.loads(source(ROOT / "pyproject.toml"))
    mapping = json.loads(source(SITE / "content-map.json"))
    for path in narrative_inputs(ROOT, mapping):
        source(path)
    version = config["project"]["version"]
    if set(config["project"]["scripts"]) != {"xdl", "xverse-argus"}:
        raise ValueError("CLI entry points changed: update the explicit public CLI documentation adapter.")
    from xverse_xdl.cli import _parser

    help_sections = [
        "Generated from the current command parser and Argus usage output. These are offline tools; their help does not start an experiment.", "",
    ]
    for name, help_text in cli_help_tree(_parser()):
        help_sections.extend([f"## `{name}`", "", "```text", help_text.strip(), "```", ""])
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "COLUMNS": "88"}
    usage = command([sys.executable, "-m", "xverse.argus.cli"], expected=2, env=env)
    help_sections.extend([
        "## `xverse-argus`", "", "```text", usage.strip(), "```", "",
        "`verify` returns 0 for complete evidence, 1 for incomplete/corrupt evidence, and 2 for usage/input errors. `export` writes JSON or JSONL to standard output; neither command mutates the supplied run.", "",
        "The Argus CLI currently has no `--help` handler; its actual usage output is captured above.",
    ])
    source(ROOT / "src/xverse_xdl/cli.py")
    source(ROOT / "src/xverse/argus/cli.py")
    write_page(GENERATED / "cli.md", "Command-line reference", "\n".join(help_sections))

    for family, paths in (
        ("schemas", [ROOT / f"xdl/schemas/v1alpha1/{name}.schema.json" for name in SCHEMAS]),
        ("profiles", [ROOT / f"xdl/profiles/{name}" for name in PROFILES]),
    ):
        for path in paths:
            text = source(path)
            schema = json.loads(text)
            from jsonschema import Draft202012Validator
            Draft202012Validator.check_schema(schema)
            destination = PUBLIC / "schemas" / family / path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(text, encoding="utf-8")
            name = path.name.removesuffix(".schema.json")
            preface = (
                f"Generated from `{path.relative_to(ROOT)}`. [Download the canonical JSON schema](/schemas/{family}/{path.name}).\n\n"
                "Field tables show raw schema definitions. Relative `$ref` values resolve against the source schema document, not against this web page.\n\n"
            )
            write_page(GENERATED / family / f"{name}.md", schema.get("title", name), preface + schema_sections(schema))

    examples = ["These examples are included directly from the source tree and validated during every build.", ""]
    for name in EXAMPLES:
        path = ROOT / f"xdl/examples/v1alpha1/{name}.xdl.yaml"
        examples.extend([f"## {name.title()}", "", f"Source: `{path.relative_to(ROOT)}`", "", "```yaml", source(path).strip(), "```", ""])
    for name in EXAMPLES:
        source(ROOT / f"tests/thesis_lite/xdl/fixtures/{name}.xdl.yaml")
    source(ROOT / "tests/fixtures/measurement-profile.schema.json")
    write_page(GENERATED / "examples.md", "Validated source examples", "\n".join(examples))
    validate_examples()

    rst = SITE / "reference/generated"
    index = ["X-Verse Python API", "==================", "", "Public package exports for the current source revision. Availability of a signature is not a production-readiness claim.", "", ".. toctree::", "   :maxdepth: 2", ""]
    for package in PACKAGES:
        module = importlib.import_module(package)
        exports = module.__all__
        slug = package.replace(".", "-")
        index.append(f"   {slug}")
        content = [package, "=" * len(package), "", f".. automodule:: {package}", "", f".. currentmodule:: {package}", ""]
        for name in exports:
            obj = getattr(module, name)
            directive = "autoclass" if isinstance(obj, type) else ("autofunction" if callable(obj) else "autodata")
            if directive == "autodata":
                content.extend([f".. py:data:: {name}", "", "   .. code-block:: json", ""])
                content.extend("      " + line for line in json.dumps(constant_value(obj), indent=2).splitlines())
                content.append("")
                continue
            content.extend([f".. {directive}:: {name}"])
            if directive == "autoclass":
                content.extend(["   :members:", "   :undoc-members:"])
            content.append("")
        (rst / f"{slug}.rst").write_text("\n".join(content), encoding="utf-8")
    (rst / "index.rst").write_text("\n".join(index) + "\n", encoding="utf-8")
    # Record the admitted package roots, including modules imported by public facades.
    for directory in (ROOT / "src/xverse_xdl", *(ROOT / "src" / p.replace(".", "/") for p in PACKAGES[1:])):
        for path in directory.rglob("*.py"):
            source(path)
    command([sys.executable, "-m", "sphinx", "-W", "--keep-going", "-b", "html", "-d", str(SITE / "reference/_build/doctrees"), "-E", "-c", str(SITE / "reference"), str(rst), str(PUBLIC / "reference/python")])
    (PUBLIC / "reference/python/.buildinfo").unlink(missing_ok=True)
    command(["doxygen", "website/Doxyfile"])
    cpp_build = PUBLIC / "reference/cpp-build"
    shutil.move(str(cpp_build / "html"), PUBLIC / "reference/cpp")
    shutil.rmtree(cpp_build)
    for path in sorted((ROOT / "src/xverse/xcom/include/xverse/xcom").glob("*.hpp")):
        source(path)
    for page in (PUBLIC / "reference/cpp").glob("*.html"):
        text = page.read_text(encoding="utf-8")
        text = normalize_cpp_language(text)
        # Doxygen 1.9.x can emit a Classes navigation link for hidden nested types.
        if 'id="nested-classes"' not in text and 'name="nested-classes"' not in text:
            text = text.replace('<a href="#nested-classes">Classes</a> &#124;', '')
        text = text.replace("</body>", '<script src="cpp-return.js"></script></body>')
        # Integrate native reference pages with the shared static search index.
        text = text.replace('<div class="contents">', '<div class="contents" data-pagefind-body>')
        page.write_text(text, encoding="utf-8")
    for page in (PUBLIC / "reference/python").rglob("*.html"):
        text = page.read_text(encoding="utf-8").replace('role="main"', 'role="main" data-pagefind-body')
        page.write_text(text, encoding="utf-8")
    for path in (SITE / "src/content/docs").rglob("*.md"):
        if not path.is_relative_to(GENERATED):
            source(path)
    for path in (SITE / "src/content/i18n").glob("*.json"):
        source(path)
    for pattern in ("*.astro", "*.css", "*.ts", "*.svg", "*.mjs"):
        for path in (SITE / "src").rglob(pattern):
            source(path)
    for path in [SITE / "astro.config.mjs", SITE / "tsconfig.json", SITE / "package.json", SITE / "package-lock.json", SITE / "Doxyfile", ROOT / "Doxyfile", SITE / "reference/conf.py", SITE / "reference/pyproject.toml", SITE / "reference/uv.lock", Path(__file__), SITE / "content-map.json", ROOT / ".github/workflows/website.yml", ROOT / "src/xverse/__init__.py", SITE / "public/favicon.svg", SITE / "examples/system.xdl.yaml"]:
        source(path)
    for pattern in ("*.py", "*.mjs", "*.css", "*.js"):
        for directory in (SITE / "scripts", SITE / "reference/_static"):
            for path in directory.glob(pattern):
                source(path)
    for path in (SITE / "reference/cpp.css", SITE / "reference/cpp-return.js"):
        source(path)
    revision = command(["git", "rev-parse", "HEAD"]).strip() if (ROOT / ".git").exists() else "unknown"
    manifest = {
        "formatVersion": 1,
        "sourceRevision": revision,
        "packageVersion": version,
        "sourceState": "see input hashes; revision alone does not identify uncommitted documentation changes",
        "inputs": input_hashes(inputs, ROOT),
        "hosting": {"basePath": os.environ.get("BASE_PATH", "/xverse-platform/"), "siteUrl": os.environ.get("SITE_URL", "https://the-xverse.github.io")},
        "generatedPages": [str(path.relative_to(GENERATED)) for path in sorted(GENERATED.rglob("*.md"))],
        "publicPythonPackages": list(PACKAGES),
        "limitations": ["Static reference generation is not runtime validation.", "Narrative maturity labels require review alongside source changes."],
    }
    (PUBLIC / "publication-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Public references generated: {len(manifest['generatedPages'])} Markdown pages; {len(inputs)} hashed inputs.")


if __name__ == "__main__":
    try:
        generate()
    except Exception as error:
        print(f"Documentation generation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
