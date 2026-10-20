"""Endpoint reconciliation proposal v2: v1 mapping with the independent review's corrections adopted.

Usage: python3 -I build-endpoint-reconciliation-20261020-v2.py

Inputs: endpoint-reconciliation-proposal-20261020.json (v1, agent-drafted) and
endpoint-reconciliation-independent-review-20261020.json (separate agent session, finding 376). Every
DISAGREE and PREFER_ALTERNATIVE row takes the reviewer's preferred target (resolved against the current
AST); AGREE_WITH_NOTE rows keep their target and carry the note; AGREE rows are unchanged. Each row
records its v1 target and the verdict. v1 and the review are retained unchanged. This is the
reconciled proposal for the author's ruling under AD-2026-10-20-b; it closes no obligation.
"""
import ast
from pathlib import Path
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
V1 = BASE / "endpoint-reconciliation-proposal-20261020.json"
REVIEW = BASE / "endpoint-reconciliation-independent-review-20261020.json"
OUT = BASE / "endpoint-reconciliation-proposal-20261020-v2.json"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())

def resolve(target):
    if target is None: return None
    module, _, symbol = target.partition("::")
    path = ROOT / module
    if not path.is_file(): return False
    if not symbol: return True
    tree = ast.parse(path.read_text())
    cls, _, meth = symbol.partition(".")
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == cls:
            if not meth: return True
            return isinstance(node, ast.ClassDef) and any(isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name == meth for m in node.body)
    return False

v1, review = read(V1), read(REVIEW)
assert review["reviewed_proposal"]["sha256"] == sha(V1) == "80ad3bea9c75e930265fdcc5edff4ebbc98875a0b3cc2d960ff2b9d0db8556d7"
verdicts = {r["declared_endpoint"]: r for r in review["rows"]}
assert set(verdicts) == {r["declared_endpoint"] for r in v1["endpoints"]} and len(verdicts) == 62
rows, changed = [], []
for e in v1["endpoints"]:
    v = verdicts[e["declared_endpoint"]]
    row = dict(e, v1_target=e["proposed_target"], v1_confidence=e["confidence"], review_verdict=v["verdict"], review_note=v["note"])
    if v["verdict"] in ("DISAGREE", "PREFER_ALTERNATIVE"):
        target = v["preferred_target"]
        assert target and resolve(target), (e["declared_endpoint"], target)
        row.update(proposed_target=target, confidence="reviewer_corrected", rationale="Independent review: " + v["note"],
                   proposed_target_resolves=True, proposed_target_file_sha256=sha(ROOT / target.partition("::")[0]),
                   alternatives=[a for a in [e["proposed_target"], *e["alternatives"]] if a and a != target],
                   private_identity=target.rsplit(".", 1)[-1].startswith("_") or "::_" in target)
        changed.append(e["declared_endpoint"])
    elif v["verdict"] == "AGREE_WITH_NOTE":
        row["confidence"] = e["confidence"] + "+reviewer_note"
    rows.append(row)
by_declared = {r["declared_endpoint"]: r for r in rows}
obligations = []
for o in v1["obligations"]:
    r = by_declared[o["declared_endpoint"]]
    obligations.append(dict(o, proposed_target=r["proposed_target"], confidence=r["confidence"],
                            obligation_disposition="re-bound_pending_author_ruling", closed=False))
counts = {}
for r in rows: counts[r["confidence"]] = counts.get(r["confidence"], 0) + 1
record = dict(schema_version=1, revision="ML3-AFFA17-2026-10-20-endpoint-reconciliation-proposal-v2",
    parent_proposal=dict(path=V1.name, sha256=sha(V1), retained_unchanged=True),
    independent_review=dict(path=REVIEW.name, sha256=sha(REVIEW), reviewer=review["reviewer"], counts=review["counts"],
                            labelled="separate agent session; counts as independent per author sign-off 2026-10-20 (finding 373)"),
    author_decision=dict(id="AD-2026-10-20-b", signoff="2026-10-20", ruling_on_v2_pending=True),
    candidate_git_head="46e0ebfd332dd833322d764191a7cfe1e008bec1", dirty_increment17=True,
    method="v1 targets replaced by the reviewer's preferred targets where the review disagreed or preferred an alternative; every target resolved against the current AST; notes carried",
    counts=dict(endpoints=len(rows), **counts, reviewer_corrected_rows=len(changed), superseded_no_equivalent=0,
                obligations=len(obligations), obligations_closed=0),
    corrected_endpoints=changed, endpoints=rows, obligations=obligations,
    authority_limits=dict(semantic_mapping_proposed=True, independently_reviewed=True, author_ruled=False, accepted=False, trace_rebound=False))
with OUT.open("x") as stream:
    json.dump(record, stream, indent=2); stream.write("\n")
print(json.dumps(dict(output=OUT.name, sha256=sha(OUT), counts=record["counts"])))
