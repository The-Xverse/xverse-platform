from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from xverse_xdl.loader import load_file_sources

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "xdl" / "examples" / "v1alpha1"
PROFILE_SCHEMA = ROOT / "tests" / "fixtures" / "measurement-profile.schema.json"
EXAMPLE_PATHS = tuple(
    EXAMPLE_DIR / name
    for name in (
        "profile.xdl.yaml", "component.xdl.yaml", "system.xdl.yaml",
        "deployment.xdl.yaml", "scenario.xdl.yaml",
    )
)


def parsed_examples() -> dict[str, dict[str, Any]]:
    documents, diagnostics = load_file_sources(EXAMPLE_PATHS)
    if diagnostics:
        raise AssertionError(diagnostics)
    return {document.data["kind"]: copy.deepcopy(document.data) for document in documents}
