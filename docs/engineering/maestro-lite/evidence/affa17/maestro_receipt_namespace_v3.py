"""Per-module receipt namespace plus garbage-collection pause observation (v3).

Successor of maestro_receipt_namespace.py (v2). Identical namespace behaviour for every
session, outer or nested. Additionally, when MAESTRO_GC_LOG names a file, every gen-2
garbage collection of the session's own process is appended to that file as one JSON line
with host monotonic start/end times and the current test node, so that operation stalls
retained in lazy-operations receipts can be correlated with collector pauses by clock.
Observation only: it never changes collector thresholds, tests, product code or outcomes.
"""
import gc
import json
import os
import time
from pathlib import Path

import pytest

_ROOT = os.environ.get("MAESTRO_FULL_RECEIPT_ROOT")
_GC_LOG = os.environ.get("MAESTRO_GC_LOG")
_state = {"start": None, "node": None, "pid": os.getpid()}


def _gc_callback(phase, info):
    if info.get("generation") != 2:
        return
    if phase == "start":
        _state["start"] = time.monotonic()
        return
    began = _state["start"]
    if began is None or not _GC_LOG:
        return
    ended = time.monotonic()
    row = dict(pid=_state["pid"], node=_state["node"], began=began, ended=ended,
               seconds=round(ended - began, 6), collected=info.get("collected"), uncollectable=info.get("uncollectable"))
    try:
        with open(_GC_LOG, "a") as stream:
            stream.write(json.dumps(row) + "\n")
    except OSError:
        pass


if _GC_LOG and _gc_callback not in gc.callbacks:
    gc.callbacks.append(_gc_callback)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    _state["node"] = item.nodeid
    if not _ROOT:
        return
    target = Path(_ROOT) / item.path.stem
    target.mkdir(parents=True, exist_ok=True)
    os.environ["MAESTRO_BOUNDARY_RECEIPTS"] = str(target)
    os.environ["MAESTRO_FULL_RECEIPT_ROOT"] = str(target / "nested")
    if _GC_LOG:
        os.environ["MAESTRO_GC_LOG"] = str(target / "nested-gc.jsonl")
