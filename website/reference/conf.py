"""Public-export-only Python reference. No runtime worker imports or source browser."""

import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
project = "X-Verse Python API"
copyright = "X-Verse contributors"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]
html_theme = "alabaster"
html_title = project
html_show_sourcelink = False
html_copy_source = False
html_show_sphinx = False
html_static_path = ["_static"]
html_css_files = ["reference.css"]
html_js_files = ["return-link.js"]
html_theme_options = {"description": "Public package exports · bounded Lite APIs", "fixed_sidebar": True}
autodoc_typehints = "signature"
autodoc_member_order = "bysource"
autodoc_inherit_docstrings = False
nitpicky = False
exclude_patterns = ["_build", ".venv"]
source_suffix = ".rst"
root_doc = "index"


def normalize_comments(app, what, name, obj, options, lines):
    """Render existing Doxygen-style Python docstrings without duplicating source docs."""
    for index, line in enumerate(lines):
        line = re.sub(r"@param\s+(\w+)\s+", r":param \1: ", line)
        line = re.sub(r"@returns?\s+", ":returns: ", line)
        line = re.sub(r"@raises\s+(\w+)\s+", r":raises \1: ", line)
        lines[index] = line


def setup(app):
    app.connect("autodoc-process-docstring", normalize_comments)
