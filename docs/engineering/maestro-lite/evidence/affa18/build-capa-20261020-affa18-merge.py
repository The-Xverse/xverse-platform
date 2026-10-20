"""Build the parent-preserving CAPA successor that binds the merge of increments 17 and 18 into main (finding 412).

Usage: python3 -I build-capa-20261020-affa18-merge.py

Parent: capa-20261020-affa18-acceptance/register.json (50 records / 489 bindings). Additive only: the merge
record and review span 411 (412 is bound by the next successor); top-level `merged` and the increment18
block's `merged` become True with the merge commit named; no record state, cause or effectiveness changes.
"""
from pathlib import Path
import copy
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261020-affa18-acceptance"
OUT = BASE / "capa-20261020-affa18-merge"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa18.md"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "a2e751c6e6a1e257ddf9bc1805aac9f48f99b0e92b9965ac3cb91949784628ae"
assert len(parent["records"]) == 50 and len(parent["evidence"]) == 489
register = copy.deepcopy(parent)

def span(start, end):
    text = REVIEW.read_text()
    body = text[text.index("\n" + start) + 1:text.index("\n" + end)]
    return dict(kind="review_span", path=rel(REVIEW), start=start, end=end, sha256=hashlib.sha256(body.encode()).hexdigest())

merge = BASE / "main-merge-increments17-18-20261020.json"
record = read(merge)
new_evidence = {"review:411": span("411.", "412."),
                "E-MAIN-MERGE-INCREMENTS17-18": dict(kind="file", path=rel(merge), sha256=sha(merge))}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
assert all(plan["effectiveness"]["status"] == "NOT_DEMONSTRATED" for plan in register["action_plans"].values())
assert parent["increment18"]["accepted"] is True and parent["merged"] is False
merged = dict(record="E-MAIN-MERGE-INCREMENTS17-18", review_finding=412, date="2026-10-20", repository=record["repository"],
              merge_commit=record["merge_commit"], merge_tree=record["merge_tree"], main_before=record["main_before"],
              pushed_to_origin_main=False)
register["merged"] = True
register["main_merge"] = merged
register["increment18"] = dict(parent["increment18"], merged=True)
register["selected_findings"] = parent["selected_findings"] + [412]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"),
                      merged=True, merge_commit=record["merge_commit"])))
