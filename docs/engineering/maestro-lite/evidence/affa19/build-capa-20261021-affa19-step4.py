"""Build the parent-preserving CAPA successor for increment19 step 4 (findings 473-485).

Usage: python3 -I build-capa-20261021-affa19-step4.py

Parent: capa-20261021-affa19-step3 (56 records / 604 bindings). Additive only: review spans 473-485,
the gate repair, the E1 patch and its evidence, A/B e and f. ML-CAPA-418 stays FIX_CANDIDATE on E1
(897d9dc50); ML-CAPA-359 notes E1 as its tracked correction. No cause VERIFIED, no effectiveness
claimed beyond the observed load, no parent record loses an incident or evidence reference.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json
import subprocess

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261021-affa19-step3"
OUT = BASE / "capa-20261021-affa19-step4"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa19.md"
TESTS = ROOT / "tests/thesis_lite/maestro"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "dc3a67a8a6ae9a7a84d90a9a6c122316522dfb8f0795b8621b8fb91aef01ebc1"
assert len(parent["records"]) == 56 and len(parent["evidence"]) == 604
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)
LAST = 485  # 486 records this successor and is bound by the next one


def span(n):
    text = REVIEW.read_text()
    body = text[text.index(f"\n{n}.") + 1:text.index(f"\n{n + 1}.")]
    return dict(kind="review_span", path=rel(REVIEW), start=f"{n}.", end=f"{n + 1}.",
                sha256=hashlib.sha256(body.encode()).hexdigest())


E1 = OUT / "e1.patch"
E1.write_bytes(subprocess.check_output(["git", "diff", "8c183333e", "897d9dc50", "--", "src"], cwd=ROOT))
E = BASE
new_evidence = {
    **{f"review:{n}": span(n) for n in range(473, LAST + 1)},
    "E-AFFA19-E1-PATCH": file(E1),
    "E-AFFA19-E1-ADR": file(ROOT / "docs/engineering/maestro-lite/ADR-ML3-BUDGET-0001.md"),
    "E-AFFA19-E1-TESTS": file(TESTS / "test_load_aware_budgets.py"),
    "E-AFFA19-E1-EVIDENCE": file(E / "budget-20261021/SHA256SUMS"),
    "E-AFFA19-AB-E-SUMMARY": file(E / "ab-budget-loaded-20261021e/summary.json"),
    "E-AFFA19-AB-F-SUMMARY": file(E / "ab-budget-loaded-20261021f/summary.json"),
    "E-AFFA19-GATE-REPAIRED": file(ROOT / "scripts/validate_maestro_acceptance_evidence.py"),
    "E-AFFA19-GATE-TESTS-REPAIRED": file(TESTS / "test_acceptance_evidence_gate.py"),
    "E-AFFA19-GUARD-CONTROLS": file(TESTS / "test_candidate_guards_and_f10_limits.py"),
    "E-AFFA19-RUN-W-SUMS": file(E / "platform-regression-20261021w/SHA256SUMS"),
}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
now = datetime.now(timezone.utc).isoformat()
records = {r["capa_id"]: r for r in register["records"]}


def extend(capa, incidents, refs, **fields):
    row = records[capa]
    row["incident_ids"] += [i for i in incidents if i not in row["incident_ids"]]
    row["root_cause_evidence_refs"] += [r for r in refs if r not in row["root_cause_evidence_refs"]]
    row.update(fields, updated_at=now)


extend("ML-CAPA-418", [f"review:{n}" for n in (476, 477, 478, 479, 480, 481, 482, 483, 484, 485)],
       ["review:477", "review:479", "review:481", "review:484", "review:485", "E-AFFA19-E1-PATCH",
        "E-AFFA19-E1-ADR", "E-AFFA19-E1-TESTS", "E-AFFA19-E1-EVIDENCE", "E-AFFA19-AB-E-SUMMARY",
        "E-AFFA19-AB-F-SUMMARY"],
       root_cause_summary=records["ML-CAPA-418"]["root_cause_summary"] + (
           " E1 (897d9dc50, author delegation 476): load-aware interior budgets inside hard admitted bounds; "
           "a shared per-run estimator, widening-only interior deadlines and refusal before mutation when the "
           "remaining work no longer fits. Natural-load A/B e: A 9 vs B 2 failures, no ML-PERSIST-TIMEOUT or "
           "TEARDOWN-INCOMPLETE as dispatcher diagnostics in B; A/B f: A 25 vs B 1, no B-only failure. "
           "Reviews FAIL, FAIL, PASS (480, 482, 484). Remaining: active-window exhaustion (outer) and the "
           "unwidened restart path."),
       candidate_patch_sha256=sha(E1))
register["action_plans"]["ML-CAPA-418"].update(
    correction={"status": "fix_candidate_E1_897d9dc50_review_PASS_not_accepted_v2_kept",
                "evidence_refs": ["review:477", "review:484", "E-AFFA19-E1-PATCH"]},
    prevention={"status": "seeded controls a-h and estimator test; natural-load A/B e and f",
                "evidence_refs": ["E-AFFA19-E1-TESTS", "E-AFFA19-AB-E-SUMMARY", "E-AFFA19-AB-F-SUMMARY"],
                "limits": "Load up to about 14 observed; restart operations not widened by design; M1 conservative bias (484 (2))."},
    next_action="Full installed-wheel run on the final head on a quiet host (469 (3)); increment acceptance (476 E3).")
extend("ML-CAPA-359", ["review:481", "review:485"], ["review:481", "review:485", "E-AFFA19-AB-F-SUMMARY"])
register["action_plans"]["ML-CAPA-359"]["next_action"] += " Tracked correction: E1 (897d9dc50, ML-CAPA-418)."
register["selected_findings"] = parent["selected_findings"] + list(range(473, LAST + 1))
register["increment19"] = dict(parent["increment19"], step4_head="897d9dc50", accepted=False, merged=False,
                               delegation="review-affa19.md finding 476")
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
