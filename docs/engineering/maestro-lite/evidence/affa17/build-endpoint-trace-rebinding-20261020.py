"""Successor trace re-binding the 90 declared endpoint obligations to the accepted v2 identities.

Usage: python3 -I build-endpoint-trace-rebinding-20261020.py

Parent trace: runtime-lane-partial-traceability.json (statuses inherited unchanged). Input: endpoint
reconciliation proposal v2 (independently reviewed, finding 376; accepted by the author, finding 377).
Each obligation row binds unit id -> declared endpoint -> accepted current identity -> current file
SHA-256. Re-binding the trace is not acceptance of the implementation, M1, merge or a scientific claim.
"""
from pathlib import Path
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT = BASE / "runtime-lane-partial-traceability.json"
V2 = BASE / "endpoint-reconciliation-proposal-20261020-v2.json"
OUT = BASE / "endpoint-rebound-traceability-20261020.json"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())

parent, v2 = read(PARENT), read(V2)
assert sha(V2) == "7e869069d96a53fbdcb74e33c7fdb99c374de5b6e52ed0cd87f8514e87b484fc"
targets = {r["declared_endpoint"]: r for r in v2["endpoints"]}
obligations = []
for o in v2["obligations"]:
    t = targets[o["declared_endpoint"]]
    module = t["proposed_target"].partition("::")[0]
    obligations.append(dict(unit_id=o["unit_id"], requirement_id=o["unit_id"].rsplit("-U", 1)[0], declared_endpoint=o["declared_endpoint"],
        captured_declared_endpoint=o.get("captured_declared_endpoint"), accepted_identity=t["proposed_target"],
        confidence=t["confidence"], review_verdict=t["review_verdict"], target_file=module, target_file_sha256=sha(ROOT / module),
        rebound=True, implementation_verified=False, closed_by_acceptance=False))
assert len(obligations) == 90
reverse = {}
for o in obligations:
    reverse.setdefault(o["accepted_identity"], set()).add(o["requirement_id"])
record = dict(schema_version=1, revision="ML3-AFFA17-2026-10-20-endpoint-rebound-v1",
    parent_trace=dict(path=PARENT.name, sha256=sha(PARENT)),
    accepted_proposal=dict(path=V2.name, sha256=sha(V2), independent_review=v2["independent_review"], author_ruling="accepted 2026-10-20 (finding 377)"),
    requirements=parent["requirements"], source_parent_register=dict(parent["source_parent_register"],
        author_confirmed_successor=dict(path="specs/024-maestro-lite-lifecycle/engineering/successors/ML-SOURCE-PARENT-2026-10-20-v4/source-parent-register.json",
                                        sha256="41e28ad0f5f440ab87dad014205a8ffc3780427aa6311c4745be765f4554115d")),
    runtime_cases=parent["runtime_cases"],
    reverse_endpoint_requirements={**parent["reverse_endpoint_requirements"], **{k: sorted(v) for k, v in reverse.items()}},
    endpoint_obligations=obligations,
    source_parents_retained=parent["source_parents_retained"], scenario_pairs_retained=parent["scenario_pairs_retained"],
    endpoint_obligations_retained=90, endpoint_obligations_rebound=90, endpoint_obligations_closed_by_acceptance=0,
    full_runtime_cases_retained=parent["full_runtime_cases_retained"],
    distinct_accepted_identities=len(reverse), open_findings=parent["open_findings"] + [375],
    authority_limits=dict(parent["authority_limits"], endpoint_mapping_independently_reviewed=True, endpoint_mapping_author_accepted=True,
                          trace_rebound=True, implementation_accepted=False, m1_complete=False, merged=False))
with OUT.open("x") as stream:
    json.dump(record, stream, indent=2); stream.write("\n")
print(json.dumps(dict(output=OUT.name, sha256=sha(OUT), rebound=record["endpoint_obligations_rebound"], identities=record["distinct_accepted_identities"])))
