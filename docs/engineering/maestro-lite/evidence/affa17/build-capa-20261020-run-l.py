"""Build the parent-preserving CAPA successor for run l (finding-382 controls carried in the full suite).

Usage: python3 -I build-capa-20261020-run-l.py   (after run l is terminal and triaged)

Parent: capa-20261020-run-k/register.json (49 records / 359 bindings). Additive only: run l evidence, the
lane admission two-phase evidence (driver b), the F-01/F-02 control modules and the fixture constant, review
spans 381-386 (387 is bound by the next successor) and the complete independent review; ML-CAPA-381-F01/F02 gain the documented-precondition
correction status with their owned controls (state stays UNRESOLVED: the native strengthening is queued);
222/357/359-CHILD/364/374/379 gain run l as prevention observations; 359 gains run l's child outcome.
Run both validators afterwards.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261020-run-k"
OUT = BASE / "capa-20261020-run-l"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa17.md"
RUN = BASE / "platform-regression-20261020l"
LANE = BASE / "lane-admission-20261020b"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "7bac7f7c01f6b32c7839d2c595d6b667391662607a7d4cbf8b399fb288290ba5"
assert len(parent["records"]) == 49 and len(parent["evidence"]) == 359
register = copy.deepcopy(parent)
now = datetime.now(timezone.utc).isoformat()
records = {r["capa_id"]: r for r in register["records"]}

def span(start, end):
    text = REVIEW.read_text()
    body = text[text.index("\n" + start) + 1:text.index("\n" + end)]
    return dict(kind="review_span", path=rel(REVIEW), start=start, end=end, sha256=hashlib.sha256(body.encode()).hexdigest())

def file(path):
    path = Path(path)
    assert path.is_file() and not path.is_symlink(), path
    return dict(kind="file", path=rel(path), sha256=sha(path))

receipt = read(RUN / "source-receipt.json")
triage = read(RUN / "failure-triage.json")
failed = {f["nodeid"] for f in triage["failures"]}
build_nodes_absent = not any("No module named build" in "\n".join(f["traceback_last_lines"]) for f in triage["failures"])
log_lines = (RUN / "source.log").read_text().splitlines()
child_errors = sum(1 for line in log_lines if line.startswith("E         ERROR tests/"))
child_failed = sorted({m.group(1) for line in log_lines for m in [re.match(r"^E\s+FAILED (tests/\S+)", line)] if m})
LEAF = "tests/thesis_lite/maestro/test_active_restart.py::test_original_active_explicit_restart_and_closed_generation_universe[leaf]"
SW = "tests/thesis_lite/maestro/test_schedule_worker.py::test_original_native_gate_renewal_updates_only_after_exact_ack"
F01 = "tests/thesis_lite/maestro/test_affa_release_timeout_fence.py::test_release_timeout_under_frozen_ancestor_is_fenced_before_thaw"
F02 = "tests/thesis_lite/maestro/test_affa_client.py::test_advance_requires_actual_original_watched_C1_before_send"
timeouts = sorted(f["nodeid"] for f in triage["failures"] if "thesis_lite/maestro" in f["nodeid"]
                  and any("ML-PERSIST-TIMEOUT" in l or "TEARDOWN-INCOMPLETE" in l or "TERMINAL-INCOMPLETE" in l for l in f["traceback_last_lines"]))
terminal_outer = sorted(f["nodeid"] for f in triage["failures"] if any("TERMINAL-INCOMPLETE" in l for l in f["traceback_last_lines"]))
probe_rows = [json.loads(l) for l in (RUN / "fsync-probe.jsonl").read_text().splitlines()] if (RUN / "fsync-probe.jsonl").is_file() else []
probe_summary = next((r for r in probe_rows if r.get("summary")), None)
probe_spikes = sum(1 for r in probe_rows if "fsync_seconds" in r and not r.get("summary"))
lane = read(LANE / "receipt.json")

new_evidence = {"review:381": span("381.", "382."), "review:382": span("382.", "383."), "review:383": span("383.", "384."),
                "review:384": span("384.", "385."), "review:385": span("385.", "386."),
                "E-INCREMENT-REVIEW": file(BASE / "increment17-independent-review-20261020.json"),
                "E-INCREMENT-REVIEW-SUMMARY": file(BASE / "increment17-independent-review-20261020.md"),
                "review:386": span("386.", "387."), "E-AUTHOR-CONFIRMATION-382": file(BASE / "author-confirmation-382-20261020.json")}
for name, path in (("RECEIPT", "source-receipt.json"), ("LOG", "source.log"), ("TRIAGE", "failure-triage.json"),
                   ("FSYNC-PROBE", "fsync-probe.jsonl"), ("GC-LOG", "gc-pauses.jsonl"), ("CONFIG", "configuration.json")):
    if (RUN / path).is_file():
        new_evidence["E-HARNESS-L-" + name] = file(RUN / path)
new_evidence["E-HARNESS-L-DRIVER"] = file(BASE / "verify-platform-regression-20261020l.py")
for name, path in (("RECEIPT", "receipt.json"), ("CONFIG", "configuration.json"), ("SOURCE-LOG", "source.log"), ("WHEEL-LOG", "wheel.log")):
    new_evidence["E-LANE-B-" + name] = file(LANE / path)
new_evidence["E-LANE-B-DRIVER"] = file(BASE / "verify-lane-admission-20261020b.py")
new_evidence["E-LANE-A-DRIVER-LOG"] = file(BASE / "lane-admission-20261020a.driver.log")
new_evidence["E-CONTROL-F01-MODULE"] = file(ROOT / "tests/thesis_lite/maestro/test_affa_release_timeout_fence.py")
new_evidence["E-CONTROL-F02-MODULE"] = file(ROOT / "tests/thesis_lite/maestro/test_affa_client.py")
new_evidence["E-LANE-ADMISSION-MODULE"] = file(ROOT / "tests/thesis_lite/maestro/test_runtime_lane_admission.py")
new_evidence["E-RUNTIME-ENTRY-FIXTURE"] = file(ROOT / "tests/thesis_lite/maestro/test_runtime_entry.py")
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
l_refs = [k for k in new_evidence if k.startswith("E-HARNESS-L-")] + ["review:383"]

for capa_id, status in (
    ("ML-CAPA-357", "run_l_build_signature_absent:" + json.dumps(build_nodes_absent)),
    ("ML-CAPA-359-CHILD", "run_l_child_setup_errors:" + str(child_errors)),
    ("ML-CAPA-222", "run_l_leaf_reproducer_passed:" + json.dumps(LEAF not in failed and LEAF not in child_failed)),
    ("ML-CAPA-364", "run_l_whole_session_tmpfs_timeouts_" + str(len(timeouts)) + "_probe_spikes_" + str(probe_spikes)
                    + ("_summary_terminal" if probe_summary else "_summary_absent")),
    ("ML-CAPA-374", "run_l_schedule_worker_case_" + ("failed" if SW in child_failed or SW in failed else "passed")),
    ("ML-CAPA-379", "run_l_terminal_incomplete:" + json.dumps(terminal_outer)),
):
    r = records[capa_id]
    r["incident_ids"] += ["review:383"]
    r["root_cause_evidence_refs"] += l_refs
    r["updated_at"] = now
    plan = register["action_plans"][capa_id]
    plan["prevention"]["status"] = plan["prevention"]["status"] + "; " + status
    plan["prevention"]["evidence_refs"] = plan["prevention"]["evidence_refs"] + l_refs
r = records["ML-CAPA-359"]
r["incident_ids"] += ["review:383"]; r["root_cause_evidence_refs"] += l_refs; r["updated_at"] = now
register["action_plans"]["ML-CAPA-359"]["next_action"] += (" Run l (finding-382 controls in the full suite): outer Maestro expiries " + json.dumps(timeouts)
    + "; nested child failures " + json.dumps(child_failed) + ".")
lane_ok = lane["passed"]
for cid, test, module_key, text in (
    ("ML-CAPA-381-F01", F01, "E-CONTROL-F01-MODULE", "owned control: REJECTED release under a frozen ancestor is fenced by cleanup-only termination before any thaw"),
    ("ML-CAPA-381-F02", F02, "E-CONTROL-F02-MODULE", "existing owned control: ADVANCE without the original watched C1 is rejected (UNWATCHED)"),
):
    r = records[cid]
    r["incident_ids"] += ["review:382", "review:383"]
    r["root_cause_evidence_refs"] += ["review:382", module_key, "E-LANE-B-RECEIPT"] + l_refs
    r["prevention_test_id"] = test
    r["updated_at"] = now
    plan = register["action_plans"][cid]
    plan["correction"] = dict(status="documented_python_side_precondition_finding_382_author_confirmed_finding_387_native_strengthening_queued_next_increment",
                              evidence_refs=["review:382", "review:386", "E-AUTHOR-CONFIRMATION-382", module_key])
    plan["prevention"] = dict(status=("lane_driver_b_passed:" + json.dumps(lane_ok) + "; run_l_control_passed:" + json.dumps(test not in failed and test not in child_failed)),
                              evidence_refs=["E-LANE-B-RECEIPT", module_key] + l_refs,
                              limits=text + "; the helper bytes are unchanged, so the native observation stands until the queued change-spec item is implemented and re-reviewed.")
    plan["next_action"] = "Next increment: helper change with new frozen hashes and a fresh independent review; until then the Python-side precondition is the enforcing layer."
register["selected_findings"] = parent["selected_findings"] + [382, 383, 384, 385, 386, 387]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
register["harness_runs"] = dict(parent["harness_runs"], l=dict(returncode=receipt["returncode"], failed=triage["failed_count"],
    child_setup_errors=child_errors, child_failed=child_failed, maestro_timeouts=timeouts, probe_spikes=probe_spikes, probe_summary=probe_summary,
    collected=2098, whole_session_tmpdir_on_tmpfs=True, added_modules=["test_runtime_lane_admission.py (skipped without MAESTRO_LANE_PROPOSAL)", "test_affa_release_timeout_fence.py"],
    fixture_change=["test_runtime_entry.py ENVIRONMENT_DIGEST constant"], checkpoint_commit_before="b03633329"))
register["increment_independent_review"] = dict(record="E-INCREMENT-REVIEW", acceptance_recommended=False, blocking=["B-01", "B-02", "B-03"], addressed_in="findings 386-387 and the fourth checkpoint")
register["ir_ml3_04"] = dict(register["ir_ml3_04"], lane_admission_evidence="E-LANE-B-RECEIPT", lane_admission_passed=lane_ok,
                             f01_control="E-CONTROL-F01-MODULE", f02_control="E-CONTROL-F02-MODULE", activation_approved=False, m1_admission=False, acceptance=False)
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"),
                      run_l=register["harness_runs"]["l"])))
