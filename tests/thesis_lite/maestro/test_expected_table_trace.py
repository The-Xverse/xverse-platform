"""Hand-authored expected tables are loaded and pinned (increment19, findings 414 and 420).

expected-table-trace-20261021.json maps every row of the nine platform tables and the four design
oracle tables (copied byte-identically from ML-DESIGN-2026-10-03-v2) onto the tests that inject
its condition, with a MATCH/PARTIAL/DIVERGENT/NO_TEST verdict. This module does not re-judge the
verdicts; it fails when a table changes without a new trace, when a row is unmapped or mapped
twice, or when a cited test no longer exists. The trace is a mapping, not acceptance.
"""

import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
TRACE = ROOT / "docs/engineering/maestro-lite/expected-table-trace-20261021.json"
DATA = json.loads(TRACE.read_bytes())
TABLES = sorted(DATA["tables"])


def node(table, pointer):
    value = table
    for part in pointer.strip("/").split("/"):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def rows(table, section):
    """Every addressable row of a declared section, independent of the trace's row ids."""
    value = node(table, section)
    if isinstance(value, list):
        return [f"{section}/{i}" for i in range(len(value))]
    if isinstance(value, dict) and section.count("/") == 1 and section not in ("/positive", "/aggregation_precedence"):
        return [f"{section}/{key}" for key in value]
    return [section]


def functions(path):
    tree = ast.parse(path.read_text())
    return {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def test_trace_covers_all_thirteen_tables():
    assert len(TABLES) == 13
    assert sum(1 for t in DATA["tables"].values() if "/design-oracle/" in t["path"]) == 4


@pytest.mark.parametrize("name", TABLES)
def test_table_is_pinned_and_every_row_is_mapped_once(name):
    entry = DATA["tables"][name]
    data = (ROOT / entry["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == entry["sha256"], f"{name} changed; write a new trace"
    table = json.loads(data)
    expected = [p for section in entry["sections"] for p in rows(table, section)]
    mapped = [case["locator"] for case in entry["cases"]]
    assert sorted(mapped) == sorted(expected), dict(unmapped=sorted(set(expected) - set(mapped)),
                                                     extra=sorted(set(mapped) - set(expected)),
                                                     repeated=[p for p, n in Counter(mapped).items() if n > 1])
    for case in entry["cases"]:
        node(table, case["locator"])


@pytest.mark.parametrize("name", TABLES)
def test_verdicts_and_cited_tests_are_well_formed(name):
    cache = {}
    for case in DATA["tables"][name]["cases"]:
        assert case["verdict"] in DATA["verdicts"], case
        assert bool(case["tests"]) == (case["verdict"] != "NO_TEST"), case
        if case["verdict"] == "DIVERGENT":
            assert isinstance(case.get("finding"), int), case
        for reference in case["tests"]:
            path, _, function = reference.partition("::")
            function = function.split("[", 1)[0]
            file = ROOT / path
            assert file.is_file(), reference
            if file not in cache:
                cache[file] = functions(file)
            assert function in cache[file], reference


def test_recorded_summary_equals_the_rows():
    counted = {n: dict(Counter(c["verdict"] for c in t["cases"])) for n, t in DATA["tables"].items()}
    counted["_total"] = dict(Counter(c["verdict"] for t in DATA["tables"].values() for c in t["cases"]))
    assert counted == DATA["summary"]
