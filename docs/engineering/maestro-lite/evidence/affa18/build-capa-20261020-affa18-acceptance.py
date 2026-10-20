"""Build the parent-preserving CAPA successor that binds the author's acceptance of increment18 (finding 411).

Usage: python3 -I build-capa-20261020-affa18-acceptance.py

Parent: capa-20261020-affa18-run-s/register.json (50 records / 487 bindings). Additive only: the acceptance
record and review span 410 (411 is bound by the next successor); the `increment18` block gains accepted True
with the scope and carried-open items; `merged` stays False everywhere; no record state, cause or
effectiveness changes. Run both validators afterwards.
"""
from pathlib import Path
import copy
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261020-affa18-run-s"
OUT = BASE / "capa-20261020-affa18-acceptance"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa18.md"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "4fd92f3fb2b9af81e229f8393193bb1e518c68820c95614c2463f59138014b20"
assert len(parent["records"]) == 50 and len(parent["evidence"]) == 487
register = copy.deepcopy(parent)

def span(start, end):
    text = REVIEW.read_text()
    body = text[text.index("\n" + start) + 1:text.index("\n" + end)]
    return dict(kind="review_span", path=rel(REVIEW), start=start, end=end, sha256=hashlib.sha256(body.encode()).hexdigest())

acceptance = BASE / "author-acceptance-increment18-20261020.json"
new_evidence = {"review:410": span("410.", "411."),
                "E-AUTHOR-ACCEPTANCE-INCREMENT18": dict(kind="file", path=rel(acceptance), sha256=sha(acceptance))}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
unknown = sorted(r["capa_id"] for r in register["records"] if r["root_cause_status"] == "UNKNOWN")
assert unknown == ["ML-CAPA-135", "ML-CAPA-286", "ML-CAPA-287", "ML-CAPA-318", "ML-CAPA-324", "ML-CAPA-330", "ML-CAPA-331", "ML-CAPA-332", "ML-CAPA-337", "ML-CAPA-359"], unknown
assert all(plan["effectiveness"]["status"] == "NOT_DEMONSTRATED" for plan in register["action_plans"].values())
assert parent["increment18"]["accepted"] is False and parent["merged"] is False
register["increment18"] = dict(parent["increment18"], accepted=True, merged=False,
    acceptance=dict(record="E-AUTHOR-ACCEPTANCE-INCREMENT18", review_finding=411, date="2026-10-20", accepted_as="engineering increment",
                    checkpoints=["7abdb9dc0", "d52683ad5", "18547fd6c", "e290ce78c", "b1dc99792", "3bee8fb9d"],
                    carried_open_unknown_causes=unknown, effectiveness="NOT_DEMONSTRATED for every record",
                    deferred=["F02D-01 owner-unreadable authority image", "F02D-02 comment correction", "F-05 wire revision"],
                    not_covered=["lane activation", "M1 admission", "merges of increments 17 and 18 into main", "remaining 024 scope",
                                 "factory runs", "canonical-note edits", "scientific claims"]))
register["merged"] = False
register["selected_findings"] = parent["selected_findings"] + [410, 411]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"),
                      increment18_accepted=True, merged=False)))
