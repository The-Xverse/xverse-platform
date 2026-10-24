"""Contract tests for drift prevention and publication failure detection."""

import argparse
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generate = load("generate")
checker = load("check_site")


class ReferenceContracts(unittest.TestCase):
    def test_new_nested_cli_command_is_discovered(self):
        parser = argparse.ArgumentParser(prog="xdl")
        compile_parser = parser.add_subparsers().add_parser("experiment").add_subparsers().add_parser("compile")
        compile_parser.add_argument("--new-contract-option")
        help_text = dict(generate.cli_help_tree(parser))
        self.assertIn("--new-contract-option", help_text["xdl experiment compile"])

    def test_schema_constraints_and_nested_fields_follow_source(self):
        schema = {"properties": {"limits": {"type": "object", "properties": {"count": {"type": "integer", "minimum": 7}}}}, "required": ["limits"], "anyOf": [{"required": ["limits"]}]}
        rendered = generate.schema_sections(schema)
        self.assertIn("/properties/limits", rendered)
        self.assertIn('"minimum": 7', rendered)
        self.assertIn('"anyOf"', rendered)
        schema["properties"]["limits"]["properties"]["count"]["minimum"] = 12
        self.assertIn('"minimum": 12', generate.schema_sections(schema))

    def test_cleanup_rejects_non_generated_directory(self):
        with self.assertRaises(ValueError):
            generate.clean_directory(generate.ROOT / "src")

    def test_broken_anchor_and_base_escape_fail_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text('<a href="/project/other.html#missing">broken</a><a href="/wrong/">escape</a>')
            (root / "other.html").write_text('<h1 id="exists">Other</h1>')
            with self.assertRaises(ValueError) as caught:
                checker.check(root, "/project/")
            self.assertIn("missing anchor", str(caught.exception))
            self.assertIn("link escapes base", str(caught.exception))

    def test_private_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text('<p>/home/operator/private-key</p>')
            with self.assertRaisesRegex(ValueError, "Private/local path"):
                checker.check(root, "/")

    def test_sphinx_build_cache_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cache = root / "reference/python/.doctrees"
            cache.mkdir(parents=True)
            (cache / "environment.pickle").write_bytes(b"internal state")
            with self.assertRaisesRegex(ValueError, "Build cache in publication"):
                checker.check(root, "/")

    def test_missing_narrative_input_fails_and_changes_alter_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mapping = {"narrativeSources": {"docs/status": ["release.md"]}}
            with self.assertRaisesRegex(ValueError, "Missing or unadmitted"):
                generate.narrative_inputs(root, mapping)
            source = root / "release.md"
            source.write_text("Release candidate")
            paths = generate.narrative_inputs(root, mapping)
            before = generate.input_hashes(paths, root)
            source.write_text("Final release")
            self.assertNotEqual(before, generate.input_hashes(paths, root))

    def test_rebuild_removes_stale_generated_page(self):
        with tempfile.TemporaryDirectory() as temp:
            generated = Path(temp) / "generated"
            generated.mkdir()
            (generated / "removed-api.md").write_text("stale")
            with patch.object(generate, "GENERATED", generated):
                generate.clean_directory(generated)
            self.assertFalse((generated / "removed-api.md").exists())

    def test_sphinx_reflects_changed_signature_and_docstring(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            (source / "conf.py").write_text("import sys\nsys.path.insert(0, " + repr(str(source)) + ")\nextensions=['sphinx.ext.autodoc']\nproject='Fixture'\n")
            (source / "index.rst").write_text("Fixture\n=======\n\n.. autofunction:: sample_api.example\n")
            module = source / "sample_api.py"
            module.write_text('def example(value):\n    """Original description."""\n    return value\n')
            args = [sys.executable, "-m", "sphinx", "-q", "-W", "-E", "-b", "html", str(source), str(root / "output")]
            subprocess.run(args, check=True, capture_output=True)
            self.assertIn("Original description", (root / "output/index.html").read_text())
            module.write_text('def example(value, new_parameter=None):\n    """Updated description."""\n    return value\n')
            subprocess.run(args, check=True, capture_output=True)
            html = (root / "output/index.html").read_text()
            self.assertIn("Updated description", html)
            self.assertIn("new_parameter", html)
            self.assertNotIn("Original description", html)


if __name__ == "__main__":
    unittest.main()
