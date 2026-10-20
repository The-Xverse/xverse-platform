"""Test-only original RPC timings; unchanged installed product and operation ends."""
from pathlib import Path
import functools
import json
import sys
import time
import pytest
from xverse.maestro.persistence import PersistenceClient

out = Path(sys.argv[1])
node = sys.argv[2]
observations = []
original = PersistenceClient._rpc

@functools.wraps(original)
def observed(self, kind, body, deadline):
    began = time.monotonic()
    item = dict(kind=kind, unit=body.get('unit'), phase=body.get('phase'),
                stage=body.get('stage'), remaining_seconds=deadline.monotonic_seconds-began)
    try:
        result = original(self, kind, body, deadline)
        item['acknowledged'] = True
        return result
    except Exception as error:
        item.update(acknowledged=False,error_type=type(error).__name__,diagnostic=str(error))
        raise
    finally:
        item['elapsed_seconds'] = time.monotonic()-began
        observations.append(item)

PersistenceClient._rpc = observed
try:
    status = pytest.main([node, '-q', '--basetemp', sys.argv[3]])
finally:
    PersistenceClient._rpc = original
    out.write_text(json.dumps(observations,indent=2)+'\n')
raise SystemExit(status)
