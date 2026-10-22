"""Build the parent-preserving CAPA successor that opens ML-CAPA-418 (F-08, findings 418 and 420).

Usage: python3 -I build-capa-20261021-affa19-f08.py

Parent: evidence/affa18/capa-20261020-affa18-published/register.json (50 records / 493 bindings),
merged into this branch from the record branch. Additive only: review-affa18.md as a whole file
(finding 413 is its last entry, so it has no closing span marker), review spans 414-419 of
review-affa19.md (420 is bound by the next successor), the T3 probe evidence and the new test
modules; one new record ML-CAPA-418 in state TRIAGED with a same-session hypothesis. No existing
record state, cause or effectiveness changes.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE.parent / "affa18" / "capa-20261020-affa18-published"
OUT = BASE / "capa-20261021-affa19-f08"
REVIEW18 = ROOT / "docs/engineering/maestro-lite/review-affa18.md"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa19.md"
TESTS = ROOT / "tests/thesis_lite/maestro"
PROBE = BASE / "t3-active-end-probe"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "a6b6c4354d2db6a467e087bd910198690727e0af2cd607b174b9eeb91e47d615"
assert len(parent["records"]) == 50 and len(parent["evidence"]) == 493
register = copy.deepcopy(parent)


def span(start, end):
    text = REVIEW.read_text()
    body = text[text.index("\n" + start) + 1:text.index("\n" + end)]
    return dict(kind="review_span", path=rel(REVIEW), start=start, end=end, sha256=hashlib.sha256(body.encode()).hexdigest())


new_evidence = {
    "E-REVIEW-AFFA18-FINAL": file(REVIEW18),
    **{f"review:{n}": span(f"{n}.", f"{n + 1}.") for n in range(414, 420)},
    "E-AFFA19-T3-PROBE": file(PROBE / "probe_test.py"),
    "E-AFFA19-T3-RUNNER": file(PROBE / "run19.sh"),
    "E-AFFA19-T3-RUNS": file(PROBE / "runs.txt"),
    "E-AFFA19-T04-TESTS": file(TESTS / "test_time_context_controls.py"),
    "E-AFFA19-T02-TESTS": file(TESTS / "test_preparation_rejections.py"),
    "E-AFFA19-DV02-TESTS": file(TESTS / "test_projection_discriminating.py"),
    "E-AFFA19-TABLE-TRACE": file(ROOT / "docs/engineering/maestro-lite/expected-table-trace-20261021.json"),
    "E-AFFA19-TABLE-TRACE-TEST": file(TESTS / "test_expected_table_trace.py"),
}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
assert "ML-CAPA-418" not in {r["capa_id"] for r in register["records"]}
now = datetime.now(timezone.utc).isoformat()
register["records"].append({
    "schema_version": "1.0",
    "capa_id": "ML-CAPA-418",
    "incident_ids": ["review:418"],
    "state": "TRIAGED",
    "root_cause_status": "HYPOTHESIS",
    "root_cause_summary": (
        "F-08: FiniteDispatcher._end returns min(active end, now + operation budget, ...) and raises "
        "ML-SCHEDULE-SERVICE-DEADLINE only when that end has already passed, so near the active end it "
        "issues schedule/tick RPCs whose remaining budget is shorter than the worker's normal service "
        "time; the RPC times out (ML-PERSIST-TIMEOUT) or is refused at send (ML-PERSIST-SENDER), the "
        "persistence channel is failed and the run ends without a terminal record. Observed in the same "
        "session only (10 instrumented repeats: 4 clean, 5 timeout, 1 sender). Whether this mechanism "
        "explains the earlier ML-PERSIST-TIMEOUT failures (run r, finding 409) is not established; the "
        "same error code alone does not prove the same cause."),
    "root_cause_evidence_refs": ["review:418", "E-AFFA19-T3-PROBE", "E-AFFA19-T3-RUNNER", "E-AFFA19-T3-RUNS",
                                 "E-AFFA19-T04-TESTS"],
    "reproducer_id": "tests/thesis_lite/maestro/test_time_context_controls.py::"
                     "test_paused_simulation_does_not_hold_the_run_past_its_host_deadline (timeout/sender branch); "
                     "evidence/affa19/t3-active-end-probe",
    "prevention_test_id": None,
    "candidate_patch_sha256": None,
    "affected_versions": ["dispatcher.py FiniteDispatcher._end at main 557619e0c (and earlier)"],
    "lesson_ids": [],
    "observation_window_end": None,
    "created_at": now,
    "updated_at": now,
    "policy_sha256": parent["policy_sha256"],
})
register["action_plans"]["ML-CAPA-418"] = {
    "containment": "T3 asserts each observed variant exactly; no product change; no deadline widened.",
    "correction": {"status": "not_started_repair_scoped_in_a_later_finding_with_its_own_expectations",
                   "evidence_refs": ["review:418"]},
    "prevention": {"status": "planned: T3 tightened to the clean branch, repeated under recorded host load",
                   "evidence_refs": ["E-AFFA19-T04-TESTS"],
                   "limits": "Same-session reproducer on tmpfs under shared-host load; no persistent-media run."},
    "effectiveness": {"status": "NOT_DEMONSTRATED", "observation_plan": None, "independent_confirmation": False},
    "next_action": "Scope the dispatcher repair (refuse a send whose remaining budget is below its service floor) "
                   "and its review before any product edit.",
}
register["selected_findings"] = parent["selected_findings"] + [414, 415, 416, 417, 418, 419]
register["increment19"] = dict(branch="candidate/maestro-lite-affa19-20261021", parent_main="557619e0c",
                               record_branch_merge="576511629", review_log=rel(REVIEW), accepted=False, merged=False,
                               authorization="author text 'go for your propose order of work' (finding 414)")
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
