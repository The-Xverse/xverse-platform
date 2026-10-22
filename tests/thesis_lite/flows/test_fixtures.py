"""FR-013: the committed fixture copies equal the deterministic builder."""

from __future__ import annotations

import json

import pytest

from .support import FIXTURES, documents


@pytest.mark.parametrize("kind", ["uniform", "distinct"])
def test_committed_fixtures_match_the_builder(kind):
    built = documents(kind)
    files = sorted(path.name for path in (FIXTURES / kind).glob("*.json"))
    assert files == sorted(built)
    for name in files:
        assert json.loads((FIXTURES / kind / name).read_text()) == built[name], name
