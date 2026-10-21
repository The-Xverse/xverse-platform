"""Build the parent-preserving CAPA successor for increment19 step 3 (findings 459-472).

Usage: python3 -I build-capa-20261021-affa19-step3.py

Parent: evidence/affa19/capa-20261021-affa19-step2/register.json (56 records / 572 bindings).
Additive only: review spans 459-472 of review-affa19.md, run u/v gate verdicts, the gate inputs of
the author's decisions (468), the loaded A/B d2, the run-v nested reruns, the C1 evidence and patch.
Record changes, each by an author decision of finding 468 or a recorded finding:
- ML-CAPA-418 (F-08/F-09) stays FIX_CANDIDATE; v2 accepted by the author as a partial mitigation
  only (468 A2; condition of 469 held); F-08/F-09 stay open; loaded evidence 467, 469 added.
- ML-CAPA-439 (F-10) stays FIX_CANDIDATE; accepted by the author as an engineering fix candidate
  (468 A1), increment acceptance still pending.
- ML-CAPA-444-D09 TRIAGED -> FIX_CANDIDATE on C1 cc3d444c1 (468 C1 ruling, 471-472).
- ML-CAPA-359 UNRESOLVED/UNKNOWN -> TRIAGED/HYPOTHESIS (468 D4): host-load class of F-08/F-09,
  supported by its first recurrence under natural load only (467) and the loaded A/B (469); not
  confirmed.
No cause is VERIFIED, no effectiveness is claimed, no parent record loses an incident or reference.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json
import subprocess

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261021-affa19-step2"
OUT = BASE / "capa-20261021-affa19-step3"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa19.md"
TESTS = ROOT / "tests/thesis_lite/maestro"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "335f93f6d21049fde040a7e3feb18a2cb2a3023a52680c91aa6e7d75738cccd5"
assert len(parent["records"]) == 56 and len(parent["evidence"]) == 572
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)
LAST = 472  # 473 records this successor and is bound by the next one


def span(n):
    text = REVIEW.read_text()
    body = text[text.index(f"\n{n}.") + 1:text.index(f"\n{n + 1}.")]
    return dict(kind="review_span", path=rel(REVIEW), start=f"{n}.", end=f"{n + 1}.",
                sha256=hashlib.sha256(body.encode()).hexdigest())


C1 = OUT / "c1.patch"
C1.write_bytes(subprocess.check_output(["git", "diff", "8a19e35a4", "cc3d444c1", "--", "src"], cwd=ROOT))
E = BASE
new_evidence = {
    **{f"review:{n}": span(n) for n in range(459, LAST + 1)},
    "E-AFFA19-C1-PATCH": file(C1),
    "E-AFFA19-C1-EVIDENCE": file(E / "c1-20261021/SHA256SUMS"),
    "E-AFFA19-C1-TESTS": file(TESTS / "test_c1_documented_failure_finalize.py"),
    "E-AFFA19-C1-FAULT-TEST": file(TESTS / "test_c1_failed_finalize_fault.py"),
    "E-AFFA19-DV09-NATIVE-TESTS-C1": file(TESTS / "test_dv09_native_failed_lifecycle.py"),
    "E-AFFA19-RUN-U-RECEIPT": file(E / "platform-regression-20261021u/wheel-receipt.json"),
    "E-AFFA19-RUN-U-GATE-468": file(E / "acceptance-inputs/dv12-gate-run-u-with-468-inputs.json"),
    "E-AFFA19-GATE-ALLOWLIST": file(E / "acceptance-inputs/allowlist.json"),
    "E-AFFA19-GATE-G4": file(E / "acceptance-inputs/g4.json"),
    "E-AFFA19-RUN-V-RECEIPT": file(E / "platform-regression-20261021v/wheel-receipt.json"),
    "E-AFFA19-RUN-V-SUMS": file(E / "platform-regression-20261021v/SHA256SUMS"),
    "E-AFFA19-RUN-V-NESTED-RERUN": file(E / "platform-regression-20261021v/nested-rerun/rerun.log"),
    "E-AFFA19-RUN-V-NESTED-RERUN-QUIET": file(E / "platform-regression-20261021v/nested-rerun-quiet/rerun.log"),
    "E-AFFA19-RUN-V-GUARD-TRACE": file(E / "platform-regression-20261021v/nested-rerun/guard-trace.jsonl"),
    "E-AFFA19-AB-D-DRIVER": file(E / "ab-f08v2-loaded-20261021d.py"),
    "E-AFFA19-AB-D2-SUMMARY": file(E / "ab-f08v2-loaded-20261021d2/summary.json"),
    "E-AFFA19-AB-D2-LOG": file(E / "ab-f08v2-loaded-20261021d2/driver.log"),
    "E-AFFA19-DECISION-REQUEST": file(E / "author-decision-request-20261021.md"),
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


extend("ML-CAPA-418", ["review:467", "review:468", "review:469"],
       ["review:467", "review:469", "E-AFFA19-RUN-V-NESTED-RERUN", "E-AFFA19-RUN-V-GUARD-TRACE",
        "E-AFFA19-AB-D2-SUMMARY", "E-AFFA19-AB-D2-LOG"],
       root_cause_summary=records["ML-CAPA-418"]["root_cause_summary"] + (
           " Under natural load (467, 469): at load 13-15 the 12 load-sensitive tests fail in most runs with or "
           "without v2 (A/B d2: A 20, B 19 failures); v2 replaces persist timeouts by refusals without more "
           "failures. The dominant cause is the fixed RPC and phase budgets against host load; v2 narrows F-08/F-09 "
           "and does not remove them. Author decision 468 A2: accepted as a partial mitigation only."))
register["action_plans"]["ML-CAPA-418"].update(
    correction={"status": "v2_f4262c285_accepted_by_author_as_partial_mitigation_468_A2_F08_F09_open",
                "evidence_refs": ["review:468", "review:469", "E-AFFA19-F08V2-PATCH"]},
    prevention={"status": "quiet host: no persist timeout in arm B; loaded host: no failure increase",
                "evidence_refs": ["E-AFFA19-AB-F08-V2B", "E-AFFA19-AB-F08-V2C", "E-AFFA19-AB-D2-SUMMARY"],
                "limits": "Removing F-08/F-09 needs load-aware budgets (design scope, T01); not attempted in increment 19."},
    next_action="Design-scope decision on load-aware RPC and phase budgets; full runs read with host load recorded (469 (3)).")
extend("ML-CAPA-439", ["review:468"], ["review:468"])
register["action_plans"]["ML-CAPA-439"]["correction"] = {
    "status": "fix_candidate_e9b346a05_accepted_by_author_468_A1_increment_acceptance_pending",
    "evidence_refs": ["review:448", "review:468", "E-AFFA19-F10-PATCH"]}
register["action_plans"]["ML-CAPA-439"]["next_action"] = "Increment 19 acceptance after a clean full run (468 D2)."
extend("ML-CAPA-444-D09", ["review:468", "review:471", "review:472"],
       ["review:468", "review:471", "review:472", "E-AFFA19-C1-PATCH", "E-AFFA19-C1-EVIDENCE", "E-AFFA19-C1-TESTS",
        "E-AFFA19-C1-FAULT-TEST", "E-AFFA19-DV09-NATIVE-TESTS-C1"],
       state="FIX_CANDIDATE",
       root_cause_summary=records["ML-CAPA-444-D09"]["root_cause_summary"] + (
           " Author ruling 468 C1: the design branch is kept and the product changed. Candidate cc3d444c1 (471, 472): "
           "a report whose only blocker is terminal-outcome and which is otherwise complete and published is "
           "finalizable; worker, parent ACK, RunClosure and dispatcher use one predicate; eligibility unchanged. "
           "Independent review PASS; three negative controls; D-09 test strict and discriminating."),
       reproducer_id="tests/thesis_lite/maestro/test_dv09_native_failed_lifecycle.py::"
                     "test_actual_native_failed_lifecycle_is_overall_complete_per_design_branch (fails on 8a19e35a4)",
       prevention_test_id="test_dv09_native_failed_lifecycle.py (6 tests), test_c1_documented_failure_finalize.py, "
                          "test_c1_failed_finalize_fault.py",
       candidate_patch_sha256=sha(C1))
register["action_plans"]["ML-CAPA-444-D09"].update(
    containment="xfail(strict) until the candidate; removed with allowlist entry B2 (472)",
    correction={"status": "fix_candidate_cc3d444c1_review_PASS_not_accepted",
                "evidence_refs": ["review:471", "review:472", "E-AFFA19-C1-PATCH"]},
    prevention={"status": "strict design-branch test plus negative controls (second blocker aborts; finalize fault "
                          "falls through; closure both directions)",
                "evidence_refs": ["E-AFFA19-C1-TESTS", "E-AFFA19-C1-FAULT-TEST", "E-AFFA19-DV09-NATIVE-TESTS-C1"],
                "limits": "Lazy native stack; full run on the C1 head owed."},
    next_action="Full installed-wheel run on cc3d444c1 or later; increment acceptance (468 D2).")
extend("ML-CAPA-359", ["review:467", "review:469"],
       ["review:467", "review:469", "E-AFFA19-RUN-V-NESTED-RERUN", "E-AFFA19-RUN-V-NESTED-RERUN-QUIET",
        "E-AFFA19-AB-D2-SUMMARY"],
       state="TRIAGED", root_cause_status="HYPOTHESIS",
       root_cause_summary=(records["ML-CAPA-359"]["root_cause_summary"] or "Cause unknown (parent record).") + (
           " Hypothesis (author decision 468 D4): host-load class of F-08/F-09. Its tests "
           "[seeded-flush-persistent] and transitive [cleaned-leaf] recurred for the first time in run v's nested "
           "suite under natural load (load to 15) and passed on the quiet rerun (467); in the loaded A/B d2 both "
           "arms failed them at load 13-15 (469). Supported, not confirmed."))
register["action_plans"]["ML-CAPA-359"]["next_action"] = (
    register["action_plans"]["ML-CAPA-359"]["next_action"] + " Increment19 (467, 469): recurrence under natural "
    "load only; cause moved to HYPOTHESIS (468 D4); tracked with ML-CAPA-418.")
register["selected_findings"] = parent["selected_findings"] + list(range(459, LAST + 1))
register["increment19"] = dict(parent["increment19"], step3_head="cc3d444c1", accepted=False, merged=False,
                               author_decisions="review-affa19.md finding 468",
                               task_closure=dict(parent["increment19"].get("task_closure", {}), confirmed_by="468 D1"))
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
