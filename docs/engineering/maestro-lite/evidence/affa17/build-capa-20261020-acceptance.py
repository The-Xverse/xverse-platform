"""Build the parent-preserving CAPA successor that binds the author's acceptance of increment17 (finding 392).

Usage: python3 -I build-capa-20261020-acceptance.py

Parent: capa-20261020-run-m/register.json (50 records / 403 bindings). Additive only: the acceptance record,
review spans 389-391 (392 is bound by the next successor); top-level `accepted` set True with the
`increment17_acceptance` block stating scope and carried-open items; `merged` and
`full_increment17_complete` stay False; no record state, cause or effectiveness changes.
Run both validators afterwards.
"""
from pathlib import Path
import copy
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261020-run-m"
OUT = BASE / "capa-20261020-acceptance"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa17.md"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "ae11e2848c23d7839be5aa40d2724e64450d94fc4ee3cd8b52cbe67def0af3d7"
assert len(parent["records"]) == 50 and len(parent["evidence"]) == 403
register = copy.deepcopy(parent)

def span(start, end):
    text = REVIEW.read_text()
    body = text[text.index("\n" + start) + 1:text.index("\n" + end)]
    return dict(kind="review_span", path=rel(REVIEW), start=start, end=end, sha256=hashlib.sha256(body.encode()).hexdigest())

acceptance = BASE / "author-acceptance-increment17-20261020.json"
new_evidence = {"review:389": span("389.", "390."), "review:390": span("390.", "391."), "review:391": span("391.", "392."),
                "E-AUTHOR-ACCEPTANCE-INCREMENT17": dict(kind="file", path=rel(acceptance), sha256=sha(acceptance)),
                "E-VALIDATOR-20261020": dict(kind="file", path=rel(BASE / "verify-capa-register-20261020.py"), sha256=sha(BASE / "verify-capa-register-20261020.py"))}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
unknown = sorted(r["capa_id"] for r in register["records"] if r["root_cause_status"] == "UNKNOWN")
assert unknown == ["ML-CAPA-135", "ML-CAPA-286", "ML-CAPA-287", "ML-CAPA-318", "ML-CAPA-324", "ML-CAPA-330", "ML-CAPA-331", "ML-CAPA-332", "ML-CAPA-337", "ML-CAPA-359"], unknown
assert all(plan["effectiveness"]["status"] == "NOT_DEMONSTRATED" for plan in register["action_plans"].values())
register["accepted"] = True
register["increment17_acceptance"] = dict(record="E-AUTHOR-ACCEPTANCE-INCREMENT17", review_finding=392, date="2026-10-20",
    accepted_as="engineering increment", checkpoints=["1e081a1ba", "36e6bf132", "b03633329", "12ef86553", "40d8440ee"],
    carried_open_unknown_causes=unknown, effectiveness="NOT_DEMONSTRATED for every record",
    not_covered=["lane activation", "M1 admission", "main merge", "remaining 024 scope", "factory runs", "scientific claims"])
register["merged"] = False
register["full_increment17_complete"] = False
register["selected_findings"] = parent["selected_findings"] + [390, 391, 392]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"), accepted=True)))
