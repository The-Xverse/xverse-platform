"""Print lifecycle digests and canonical-byte hashes of four L4 plans, using the tree given in argv[1]."""
import copy, hashlib, json, sys
root = sys.argv[1]
sys.path[:0] = [root + "/src", root]
import xverse, xverse_xdl
assert xverse.__file__.startswith(root), xverse.__file__
assert xverse_xdl.__file__.startswith(root), xverse_xdl.__file__
from xverse.maestro import prepare
from tests.thesis_lite.maestro.test_preparation import PIN, compiled, documents
from tests.thesis_lite.faults.support import fault, parameter, with_sensor

def docs_with(items):
    docs = with_sensor(documents())
    docs["scenario.json"]["spec"]["faults"] = copy.deepcopy(items)
    return docs

plans = {
    "fault-less": None,
    "fault-less-sensor": [],
    "stale+crash": [fault("f-s", "stale", "sample-flow", at=1, duration=1),
                    fault("f-c", "crash", "source-instance", at=2, duration=0, recovery="manual")],
    "freeze": [fault("f-frz", "freeze", "sink-instance", at=1, duration=1)],
    "delay-ticks": [fault("f-dl", "delay", "sample-flow", at=1, duration=1, parameters=[parameter("delay-ticks", 1)])],
}
out = {}
for name, items in plans.items():
    result, resources = compiled() if items is None else compiled(docs_with(items))
    p = prepare(result, resources, provider_descriptors=(PIN,))
    out[name] = {"lifecycle": p.lifecycle_digest, "bytes": hashlib.sha256(p.canonical_bytes).hexdigest(), "faults": len(p.faults)}
print(json.dumps(out, indent=1, sort_keys=True))
