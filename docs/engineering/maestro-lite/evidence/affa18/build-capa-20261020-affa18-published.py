"""Build the parent-preserving CAPA successor that binds the publication of main and the note application (finding 413).

Usage: python3 -I build-capa-20261020-affa18-published.py

Parent: capa-20261020-affa18-merge/register.json (50 records / 491 bindings). Additive only: the push/note
record and review span 412 (413 is bound by the next successor); the main_merge block gains the published
origin/main commit; no record state, cause or effectiveness changes.
"""
from pathlib import Path
import copy
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261020-affa18-merge"
OUT = BASE / "capa-20261020-affa18-published"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa18.md"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "64579304880cd7c1791f68b2800ea3fb42dd533614406ec06820c5ab685f291f"
assert len(parent["records"]) == 50 and len(parent["evidence"]) == 491
register = copy.deepcopy(parent)

def span(start, end):
    text = REVIEW.read_text()
    body = text[text.index("\n" + start) + 1:text.index("\n" + end)]
    return dict(kind="review_span", path=rel(REVIEW), start=start, end=end, sha256=hashlib.sha256(body.encode()).hexdigest())

merge = BASE / "main-push-and-note-20261020.json"
record = read(merge)
new_evidence = {"review:412": span("412.", "413."),
                "E-MAIN-PUSH-AND-NOTE": dict(kind="file", path=rel(merge), sha256=sha(merge))}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
assert all(plan["effectiveness"]["status"] == "NOT_DEMONSTRATED" for plan in register["action_plans"].values())
assert parent["increment18"]["accepted"] is True and parent["merged"] is True
register["main_merge"] = dict(parent["main_merge"], pushed_to_origin_main=True, published_record="E-MAIN-PUSH-AND-NOTE", published_finding=413,
                              origin_main=record["main"]["origin_main_after_push"], record_merge_commit=record["main"]["record_merge_commit"])
register["canonical_note_applied"] = dict(record="E-MAIN-PUSH-AND-NOTE", sha256_after=record["canonical_note"]["sha256_after"], committed=False)
register["selected_findings"] = parent["selected_findings"] + [413]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"),
                      origin_main=record["main"]["origin_main_after_push"])))
