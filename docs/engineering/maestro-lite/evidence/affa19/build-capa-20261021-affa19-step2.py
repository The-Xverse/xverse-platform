"""Build the parent-preserving CAPA successor for increment19 step 2 (findings 420-458).

Usage: python3 -I build-capa-20261021-affa19-step2.py

Parent: evidence/affa19/capa-20261021-affa19-f08/register.json (51 records / 508 bindings).
Additive only: review spans 420-458 of review-affa19.md (459 is bound by the next successor),
the step-2 test modules, the DV12 gate, the A/B, calibration and run-t receipts, and the two
candidate patches written into this folder. Record changes: ML-CAPA-418 (F-08/F-09) TRIAGED ->
FIX_CANDIDATE on v2 f4262c285; ML-CAPA-357 gains the run-t recurrence (finding 458); new records
ML-CAPA-439 (F-10, FIX_CANDIDATE), ML-CAPA-442 (worker imports the installed package; harness
boundary, FIX_CANDIDATE), ML-CAPA-444-D09 (design divergence, TRIAGED pending the author's
ruling), ML-CAPA-445-F11 and ML-CAPA-448-F12 (pre-existing review observations, TRIAGED). No cause
is VERIFIED, no effectiveness is claimed, no parent record loses an incident or evidence reference.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json
import subprocess

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261021-affa19-f08"
OUT = BASE / "capa-20261021-affa19-step2"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa19.md"
TESTS = ROOT / "tests/thesis_lite/maestro"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "ebcc01d61f169057c42e1fdc9bca853537c78ace6e55c46e1f3479f608eef737"
assert len(parent["records"]) == 51 and len(parent["evidence"]) == 508
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)


def span(start, end):
    text = REVIEW.read_text()
    body = text[text.index("\n" + start) + 1:text.index("\n" + end)]
    return dict(kind="review_span", path=rel(REVIEW), start=start, end=end, sha256=hashlib.sha256(body.encode()).hexdigest())


def patch(name, base, head):
    diff = subprocess.check_output(["git", "diff", base, head, "--", "src"], cwd=ROOT)
    path = OUT / name
    path.write_bytes(diff)
    return path


F08 = patch("f08-f09-v2.patch", "e9b346a05", "f4262c285")
F10 = patch("f10.patch", "dd00c1db5", "e9b346a05")
E = BASE
new_evidence = {
    **{f"review:{n}": span(f"{n}.", f"{n + 1}.") for n in range(420, 459)},
    "E-AFFA19-F08V2-PATCH": file(F08),
    "E-AFFA19-F10-PATCH": file(F10),
    "E-AFFA19-AB-F08-V1": file(E / "ab-f08-repair-20261021a/receipt.json"),
    "E-AFFA19-CALIBRATION-SUMMARY": file(E / "service-time-calibration/quiet-20261021/summary.json"),
    "E-AFFA19-CALIBRATION-REPLAY": file(E / "service-time-calibration/quiet-20261021/replay.json"),
    "E-AFFA19-AB-F08-V2B": file(E / "ab-f08v2-20261021b/receipt.json"),
    "E-AFFA19-AB-F08-V2C": file(E / "ab-f08v2-20261021c/receipt.json"),
    "E-AFFA19-GUARD-TRACE": file(E / "guard-trace/guard_trace_plugin.py"),
    "E-AFFA19-F10-EVIDENCE": file(E / "f10-20261021/SHA256SUMS"),
    "E-AFFA19-DV05-DV10-EVIDENCE": file(E / "dv05-dv10-20261021/SHA256SUMS"),
    "E-AFFA19-DV04-T03-EVIDENCE": file(E / "dv04-t03-20261021/SHA256SUMS"),
    "E-AFFA19-RUN-T-RECEIPT": file(E / "platform-regression-20261021t/wheel-receipt.json"),
    "E-AFFA19-RUN-T-GATE": file(E / "platform-regression-20261021t/dv12-gate-verdict.json"),
    "E-AFFA19-RUN-T-ARGUS13": file(E / "platform-regression-20261021t/argus13-fixed-venv.log"),
    "E-AFFA19-CANDIDATE-VENV": file(E / "candidate-venv/mkvenv.sh"),
    "E-AFFA19-CANDIDATE-RUNNER": file(E / "candidate-venv/runv.sh"),
    "E-AFFA19-DV09-NATIVE-TESTS": file(TESTS / "test_dv09_native_failed_lifecycle.py"),
    "E-AFFA19-DV05-DV06-TESTS": file(TESTS / "test_dv05_dv06_bounds.py"),
    "E-AFFA19-DV04-TESTS": file(TESTS / "test_readiness_dispositions.py"),
    "E-AFFA19-DV04-N2-TESTS": file(TESTS / "test_dv04_restarted_prerequisite.py"),
    "E-AFFA19-DV03-TESTS": file(TESTS / "test_permit_release_path.py"),
    "E-AFFA19-DV10-TESTS": file(TESTS / "test_native_storage_faults.py"),
    "E-AFFA19-DV09-TESTS": file(TESTS / "test_coverage_dv09.py"),
    "E-AFFA19-DV12-GATE": file(ROOT / "scripts/validate_maestro_acceptance_evidence.py"),
    "E-AFFA19-DV12-GATE-TESTS": file(TESTS / "test_acceptance_evidence_gate.py"),
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


extend("ML-CAPA-418",
       [f"review:{n}" for n in (427, 428, 429, 430, 433, 434, 438, 447, 452, 453, 454, 455)],
       ["review:427", "review:428", "review:433", "review:434", "review:438", "review:453", "review:454", "review:455",
        "E-AFFA19-CALIBRATION-SUMMARY", "E-AFFA19-CALIBRATION-REPLAY", "E-AFFA19-AB-F08-V1", "E-AFFA19-AB-F08-V2B",
        "E-AFFA19-AB-F08-V2C", "E-AFFA19-F08V2-PATCH"],
       state="FIX_CANDIDATE",
       root_cause_summary=(
           "F-08/F-09: a schedule/tick statement or teardown record is sent with less remaining time than its normal "
           "service time (window end; shared teardown phase deadline), the persistence RPC times out, the channel is "
           "failed by design and the terminal records are lost. Limiting term measured under load (428); quiet-host "
           "service times per request type (438). First candidate 8184a2b15 (full-budget threshold) rejected by "
           "review and A/B (433, 434). v2 f4262c285 refuses a send whose remaining time is below the longest round "
           "trip already observed for its kind; A/B b and attribution A/B c on a quiet host: arm B no persist "
           "timeout, T3 clean 20/20, every refusal at the T3 active end, no failed node (454, 455). Same-session "
           "support only; false-refusal rate under load not measured (453 item 2)."),
       prevention_test_id="tests/thesis_lite/maestro/test_time_context_controls.py::"
                          "test_paused_simulation_does_not_hold_the_run_past_its_host_deadline (clean branch under v2)",
       candidate_patch_sha256=sha(F08))
extend("ML-CAPA-357", ["review:458"], ["review:458", "E-AFFA19-RUN-T-RECEIPT", "E-AFFA19-RUN-T-ARGUS13",
                                       "E-AFFA19-CANDIDATE-VENV"])


def new(capa, incidents, state, cause, summary, refs, *, reproducer=None, prevention=None, patch_sha=None,
        affected=(), plan):
    assert capa not in records, capa
    row = {"schema_version": "1.0", "capa_id": capa, "incident_ids": incidents, "state": state,
           "root_cause_status": cause, "root_cause_summary": summary, "root_cause_evidence_refs": refs,
           "reproducer_id": reproducer, "prevention_test_id": prevention, "candidate_patch_sha256": patch_sha,
           "affected_versions": list(affected), "lesson_ids": [], "observation_window_end": None,
           "created_at": now, "updated_at": now, "policy_sha256": parent["policy_sha256"]}
    register["records"].append(row)
    records[capa] = row
    register["action_plans"][capa] = plan


def plan(containment, correction, correction_refs, prevention, prevention_refs, limits, next_action):
    return {"containment": containment, "correction": {"status": correction, "evidence_refs": correction_refs},
            "prevention": {"status": prevention, "evidence_refs": prevention_refs, "limits": limits},
            "effectiveness": {"status": "NOT_DEMONSTRATED", "observation_plan": None, "independent_confirmation": False},
            "next_action": next_action}


register["action_plans"]["ML-CAPA-418"].update(
    correction={"status": "fix_candidate_v2_f4262c285_independent_review_PASS_not_accepted",
                "evidence_refs": ["review:438", "review:453", "E-AFFA19-F08V2-PATCH"]},
    prevention={"status": "T3 clean in 20 of 20 v2 runs; guard refusals attributed (A/B c)",
                "evidence_refs": ["E-AFFA19-AB-F08-V2B", "E-AFFA19-AB-F08-V2C", "E-AFFA19-GUARD-TRACE"],
                "limits": "Quiet host only (load 3.6-6.2); lifetime-maximum estimator under load unmeasured."},
    next_action="Attribution A/B under host load comparable to findings 427-428; author acceptance decision.")
new("ML-CAPA-439", [f"review:{n}" for n in (439, 440, 441, 443, 444, 445, 446, 448, 449)], "FIX_CANDIDATE", "HYPOTHESIS",
    "F-10: a lost observation (schedule failure with observation_missing) is recorded as health-loss/unknown over an "
    "M3 'unknown' observation, which the design allows; the assessor rejected it three ways (status set, parent-proof "
    "requirement, missing handleRef), so a factually complete failed native run was never normal-complete. Causes "
    "traced by instrumentation, one at a time (439-443); candidate e9b346a05 accepts the pair, requires dependencies [] "
    "and takes handleRef from the issuance of the current generation on both sides (445, 448). Two independent "
    "reviews, the second PASS; 35-module regression 362 passed in its own venv.",
    ["review:439", "review:440", "review:441", "review:443", "review:445", "review:448", "review:449",
     "E-AFFA19-F10-PATCH", "E-AFFA19-F10-EVIDENCE", "E-AFFA19-DV09-NATIVE-TESTS"],
    reproducer="tests/thesis_lite/maestro/test_dv09_native_failed_lifecycle.py (fails on dd00c1db5)",
    prevention="tests/thesis_lite/maestro/test_dv09_native_failed_lifecycle.py (three strict tests)",
    patch_sha=sha(F10), affected=["coverage.py, schedule_evidence.py, dispatcher.py at main 557619e0c"],
    plan=plan("DV09 strict test xfail until the candidate", "fix_candidate_e9b346a05_review_PASS_not_accepted",
              ["review:448", "E-AFFA19-F10-PATCH"], "three DV09 tests strict, D-09 part xfail(strict)",
              ["E-AFFA19-DV09-NATIVE-TESTS"], "Lazy native stack only; legacy CatalogLauncher path unchanged (448 item 4).",
              "Author acceptance decision."))
new("ML-CAPA-442", ["review:442", "review:458"], "FIX_CANDIDATE", "HYPOTHESIS",
    "Verification boundary: the native-started persistence worker runs python -I and imports the interpreter's "
    "installed xverse, so a PYTHONPATH=src run mixes versions whenever src differs from the install. No earlier result "
    "was affected (installed == main == src at c3a9213a1; 8184a2b15 changed parent-side files only). Candidate tooling: "
    "one installed version per arm or run (candidate-venv mkvenv.sh/runv.sh); its first full use omitted the build "
    "tools (458) and was repaired.",
    ["review:442", "review:458", "E-AFFA19-CANDIDATE-VENV", "E-AFFA19-CANDIDATE-RUNNER", "E-AFFA19-RUN-T-RECEIPT"],
    plan=plan("Worker-side candidates are tested only in their own venv", "tooling_in_use", ["E-AFFA19-CANDIDATE-VENV"],
              "run t and run u use one installed version", ["E-AFFA19-RUN-T-RECEIPT"],
              "Earlier increments' full runs used PYTHONPATH with src equal to the install.",
              "Keep the rule in every successor driver."))
new("ML-CAPA-444-D09", ["review:444"], "TRIAGED", "HYPOTHESIS",
    "D-09 design divergence: the terminal path aborts the Argus writer after a failed execution (report never "
    "eligible), and the offline verifier sets overall incomplete whenever the writer is not closed, so no failed "
    "execution reaches overall complete; the design branch normal-documented-failure expects overall complete with "
    "execution failed. Not a defect decision: awaits the author's ruling at T01 (finalize factually complete failed "
    "runs, or amend the branch).",
    ["review:444", "E-AFFA19-DV09-NATIVE-TESTS"],
    plan=plan("xfail(strict) naming D-09", "awaiting_author_ruling", ["review:444"], "none until the ruling", [],
              "Related to W-01 (writer closure).", "Author ruling at T01."))
new("ML-CAPA-445-F11", ["review:445", "review:448"], "TRIAGED", "HYPOTHESIS",
    "F-11 (pre-existing): a stale _probe_failure left by a swallowed check_health can be reported for a later failure; "
    "every _query failure cancels the owner, so only the diagnostic code can be misattributed (448).",
    ["review:445", "review:448"],
    plan=plan("none needed for the unit identity", "not_started", ["review:448"], "none", [],
              "Code reading only.", "Input to the root-cause campaign (step 4)."))
new("ML-CAPA-448-F12", ["review:448"], "TRIAGED", "HYPOTHESIS",
    "F-12 (pre-existing): between the worker's prepare_generation and the parent's _claims update, or after a failed "
    "advance, the two generation counters differ, so a failure statement naming that unit fails ML-SCHEDULE-ACK on the "
    "generation field (true at dd00c1db5).",
    ["review:448"],
    plan=plan("fails closed (ACK)", "not_started", ["review:448"], "none", [],
              "Code reading only; whether _drain_restart can run while that unit's step is current is undetermined.",
              "Input to the root-cause campaign (step 4)."))
register["selected_findings"] = parent["selected_findings"] + list(range(420, 459))
register["increment19"] = dict(parent["increment19"], step2_head="e2c338033", accepted=False, merged=False,
                               task_closure=dict(closed=["P3-T02", "P3-T04"], instruction="review the open tasks and "
                                                 "check if you can close some with the results"))
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
