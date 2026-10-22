"""Observation-only pytest plugin (ADR-ML3-BUDGET-0001 verification): after each
FiniteDispatcher.run, append the dispatcher's and every teardown's interior trace, with the test
node id and the 1-minute load, as one JSON line to $INTERIOR_TRACE_OUT. Nothing is changed."""
import json, os

import pytest


@pytest.fixture(autouse=True)
def _interior_trace(monkeypatch, request):
    from xverse.maestro.dispatcher import FiniteDispatcher
    run = FiniteDispatcher.run

    def traced(self, *args, **kwargs):
        try:
            return run(self, *args, **kwargs)
        finally:
            out = os.environ.get("INTERIOR_TRACE_OUT")
            if out:
                teardowns = (*getattr(self, "_teardown_history", ()), self.teardown)
                row = dict(node=request.node.nodeid, load=open("/proc/loadavg").read().split()[0],
                           dispatcher=getattr(self, "_interior_trace", None),
                           teardown=[e for t in teardowns for e in getattr(t, "_interior_trace", ())],
                           seen=getattr(getattr(self, "_times", None), "seen", None))
                with open(out, "a") as stream:
                    stream.write(json.dumps(row, default=str) + "\n")

    monkeypatch.setattr(FiniteDispatcher, "run", traced)
