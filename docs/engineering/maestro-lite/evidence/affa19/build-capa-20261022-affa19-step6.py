"""Build the parent-preserving CAPA successor for increment19 step 6 (findings 492-494).

Usage: python3 -I build-capa-20261022-affa19-step6.py

Parent: capa-20261022-affa19-step5 (56 records / 644 bindings, sha a934c2d8...). Additive only:
review spans 492-494; ML-CAPA-337 UNRESOLVED/UNKNOWN -> TRIAGED/HYPOTHESIS (494 (2), F-09 signature
of its first bad RPC; supported, not confirmed); ML-CAPA-286 unchanged; increment19 accepted (493)
and merged (63f5cb8c7). No cause VERIFIED, no effectiveness claimed, no parent reference lost.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261022-affa19-step5"
OUT = BASE / "capa-20261022-affa19-step6"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa19.md"
LAST = 494  # 495 records this successor and is bound by the next one
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "a934c2d84979948f2e1c884c5a582f17e5ad104f4349859de99fff5c7cac90dc"
assert len(parent["records"]) == 56 and len(parent["evidence"]) == 644
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)


def span(n):
    text = REVIEW.read_text()
    body = text[text.index(f"\n{n}.") + 1:text.index(f"\n{n + 1}.")]
    return dict(kind="review_span", path=rel(REVIEW), start=f"{n}.", end=f"{n + 1}.",
                sha256=hashlib.sha256(body.encode()).hexdigest())


new_evidence = {f"review:{n}": span(n) for n in range(492, LAST + 1)}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
now = datetime.now(timezone.utc).isoformat()
records = {r["capa_id"]: r for r in register["records"]}
row = records["ML-CAPA-337"]
assert row["state"] == "UNRESOLVED" and row["root_cause_status"] == "UNKNOWN"
row["incident_ids"] += [i for i in ["review:494"] if i not in row["incident_ids"]]
row["root_cause_evidence_refs"] += [r for r in ["review:464", "review:494"] if r not in row["root_cause_evidence_refs"]]
row.update(state="TRIAGED", root_cause_status="HYPOTHESIS", updated_at=now,
           root_cause_summary=(row["root_cause_summary"] or "Cause unknown (parent record).") + (
               " Hypothesis (494 (2), author delegation 476): F-09 class. The first retained bad RPC is a "
               "source-generation-1 teardown record that timed out with ML-PERSIST-TIMEOUT inside a 0.25 s window, "
               "the F-09 signature (teardown record sent with less remaining time than its service time). No "
               "recurrence in the quiet step-4 campaign (464) or the clean run 22a-1 (491). Supported, not confirmed."))
register["action_plans"]["ML-CAPA-337"]["next_action"] += (
    " Increment19 (494): cause moved to HYPOTHESIS (F-09 class); tracked correction E1 (897d9dc50, ML-CAPA-418).")
register["selected_findings"] = parent["selected_findings"] + list(range(492, LAST + 1))
register["increment19"] = dict(parent["increment19"], accepted=True, accepted_by="review-affa19.md finding 493 (476 E3)",
                               merged=True, merge_commit="63f5cb8c7", merge_parent_main="557619e0c",
                               task_rulings="review-affa19.md finding 494")
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
