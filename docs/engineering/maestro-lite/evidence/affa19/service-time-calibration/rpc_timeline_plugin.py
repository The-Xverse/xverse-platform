"""Observation-only pytest plugin (increment19, finding 437): one record per original persistence RPC.

Wraps PersistenceClient._rpc for every test; records kind, action, the budget it was sent with
(deadline - start), its service time and its diagnostic, and writes one JSON file per test into
$RPC_TIMELINE_OUT. It never changes an argument, a result or an exception.
"""
import json, os, time
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _rpc_timeline(monkeypatch, request):
    from xverse.maestro.persistence import PersistenceClient
    original = PersistenceClient._rpc
    records = []

    def observed(self, kind, body, end, **kw):
        began = time.monotonic(); error = None
        try:
            return original(self, kind, body, end, **kw)
        except BaseException as exc:
            error = str(exc) if str(exc).startswith('ML-') else type(exc).__name__
            raise
        finally:
            ended = time.monotonic()
            records.append(dict(kind=kind, action=body.get('kind', body.get('action')) if isinstance(body, dict) else None,
                                began=began, budget=end.monotonic_seconds - began, service=ended - began,
                                diagnostic=error))
    monkeypatch.setattr(PersistenceClient, '_rpc', observed)
    yield
    out = os.environ.get('RPC_TIMELINE_OUT')
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        name = request.node.nodeid.replace('/', '_').replace('::', '__').replace('[', '-').replace(']', '')
        outcome = getattr(request.node, 'rep_call', None)
        Path(out, name + '.json').write_text(json.dumps(dict(node=request.node.nodeid, load=os.getloadavg()[0],
                                                             records=records, observational_only=True)) + '\n')
