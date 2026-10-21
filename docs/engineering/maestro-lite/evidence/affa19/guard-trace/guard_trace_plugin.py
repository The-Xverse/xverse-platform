"""Observation-only pytest plugin (increment19, finding 453): attribute F-08/F-09 v2 guard refusals.

Wraps FiniteDispatcher._send and ReverseTeardown._record. A refusal is logged when the call raises
the guard's code while the instance carries the v2 estimate and the remaining time was below it,
which is exactly the guard's condition; on an arm without v2 the attributes are absent and nothing
is logged. Each record goes as one JSON line to $GUARD_TRACE_OUT. No argument, result or exception
is changed.
"""
import json, os, time

import pytest


def _log(**values):
    out = os.environ.get('GUARD_TRACE_OUT')
    if out:
        with open(out, 'a') as stream:
            stream.write(json.dumps(values) + '\n')


@pytest.fixture(autouse=True)
def _guard_trace(monkeypatch, request):
    from xverse.maestro.dispatcher import FiniteDispatcher
    from xverse.maestro.teardown import ReverseTeardown
    send, record = FiniteDispatcher._send, ReverseTeardown._record

    def traced_send(self, kind, deadline, **values):
        remaining = deadline.monotonic_seconds - time.monotonic()
        estimate = getattr(self, '_service_seen', {}).get(kind)
        try:
            return send(self, kind, deadline, **values)
        except Exception as error:
            if str(error) == 'ML-SCHEDULE-SERVICE-DEADLINE' and estimate is not None and remaining < estimate:
                _log(node=request.node.nodeid, guard='F-08', kind=kind, remaining=remaining, estimate=estimate)
            raise

    def traced_record(self, unit, phase, stage, descriptor, handle, deadline, **observed):
        remaining = deadline.monotonic_seconds - time.monotonic()
        estimate = getattr(self, '_record_seen', None)
        try:
            return record(self, unit, phase, stage, descriptor, handle, deadline, **observed)
        except Exception as error:
            if str(error) == 'ML-TEARDOWN-RECORD-BUDGET' and estimate is not None and remaining < estimate:
                _log(node=request.node.nodeid, guard='F-09', phase=phase, stage=stage, remaining=remaining,
                     estimate=estimate)
            raise

    monkeypatch.setattr(FiniteDispatcher, '_send', traced_send)
    monkeypatch.setattr(ReverseTeardown, '_record', traced_record)
    yield
