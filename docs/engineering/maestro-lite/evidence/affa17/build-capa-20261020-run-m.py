"""Build the parent-preserving CAPA successor for run m (finding 389: review-driven test changes and the
terminal-section budget extension).

Usage: python3 -I build-capa-20261020-run-m.py   (after run m is terminal and triaged)

Parent: capa-20261020-run-l/register.json (49 records / 385 bindings). Additive only: run m evidence, lane
driver c evidence, the changed modules and dispatcher.py; new record ML-CAPA-389 (terminal-section unit
statements at the operation budget; correction = authorized extension; prevention = run m); 379 points at
it; 381-F01 gains the strengthened control; 374 gains the integer-nanosecond comparison; review spans
387-388 (389 is bound by the next successor). No effectiveness claimed. Run both validators afterwards.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261020-run-l"
OUT = BASE / "capa-20261020-run-m"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa17.md"
RUN = BASE / "platform-regression-20261020m"
LANE = BASE / "lane-admission-20261020c"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "155f89b5aa9545dff4823301b21998e3dbc01b3ece733a7237058c39d4fd048c"
assert len(parent["records"]) == 49 and len(parent["evidence"]) == 385
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
timeouts = sorted(f["nodeid"] for f in triage["failures"] if "thesis_lite/maestro" in f["nodeid"]
                  and any("ML-PERSIST-TIMEOUT" in l or "TEARDOWN-INCOMPLETE" in l or "TERMINAL-INCOMPLETE" in l for l in f["traceback_last_lines"]))
terminal_outer = sorted(f["nodeid"] for f in triage["failures"] if any("TERMINAL-INCOMPLETE" in l for l in f["traceback_last_lines"]))
terminal_child_lines = sum(1 for line in log_lines if line.startswith("E") and ("TERMINAL-INCOMPLETE" in line or "TEARDOWN-INCOMPLETE" in line))
probe_rows = [json.loads(l) for l in (RUN / "fsync-probe.jsonl").read_text().splitlines()] if (RUN / "fsync-probe.jsonl").is_file() else []
probe_summary = next((r for r in probe_rows if r.get("summary")), None)
probe_spikes = sum(1 for r in probe_rows if "fsync_seconds" in r and not r.get("summary"))
lane = read(LANE / "receipt.json")

new_evidence = {"review:387": span("387.", "388."), "review:388": span("388.", "389.")}
for name, path in (("RECEIPT", "source-receipt.json"), ("LOG", "source.log"), ("TRIAGE", "failure-triage.json"),
                   ("FSYNC-PROBE", "fsync-probe.jsonl"), ("GC-LOG", "gc-pauses.jsonl"), ("CONFIG", "configuration.json")):
    if (RUN / path).is_file():
        new_evidence["E-HARNESS-M-" + name] = file(RUN / path)
new_evidence["E-HARNESS-M-DRIVER"] = file(BASE / "verify-platform-regression-20261020m.py")
for name, path in (("RECEIPT", "receipt.json"), ("CONFIG", "configuration.json"), ("SOURCE-LOG", "source.log"), ("WHEEL-LOG", "wheel.log")):
    new_evidence["E-LANE-C-" + name] = file(LANE / path)
new_evidence["E-LANE-C-DRIVER"] = file(BASE / "verify-lane-admission-20261020c.py")
new_evidence["E-PRODUCT-389-DISPATCHER"] = file(ROOT / "src/xverse/maestro/dispatcher.py")
new_evidence["E-CONTROL-F01-MODULE-V2"] = file(ROOT / "tests/thesis_lite/maestro/test_affa_release_timeout_fence.py")
new_evidence["E-SCHEDULE-WORKER-TEST-V2"] = file(ROOT / "tests/thesis_lite/maestro/test_schedule_worker.py")
new_evidence["E-POST-RELEASE-LOSS-MODULE-V2"] = file(ROOT / "tests/thesis_lite/maestro/test_composed_post_release_loss.py")
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
m_refs = [k for k in new_evidence if k.startswith("E-HARNESS-M-")] + ["review:388"]

for capa_id, status in (
    ("ML-CAPA-357", "run_m_build_signature_absent:" + json.dumps(build_nodes_absent)),
    ("ML-CAPA-359-CHILD", "run_m_child_setup_errors:" + str(child_errors)),
    ("ML-CAPA-222", "run_m_leaf_reproducer_passed:" + json.dumps(LEAF not in failed and LEAF not in child_failed)),
    ("ML-CAPA-364", "run_m_whole_session_tmpfs_timeouts_" + str(len(timeouts)) + "_probe_spikes_" + str(probe_spikes)
                    + ("_summary_terminal" if probe_summary else "_summary_absent")),
    ("ML-CAPA-374", "run_m_schedule_worker_case_" + ("failed" if SW in child_failed or SW in failed else "passed") + "_integer_nanosecond_comparison_finding_389"),
    ("ML-CAPA-379", "run_m_terminal_incomplete:" + json.dumps(terminal_outer) + "; terminal-section unit statements now tracked by ML-CAPA-389"),
    ("ML-CAPA-381-F01", "lane_driver_c_strengthened_control_passed:" + json.dumps(lane["passed"]) + "; run_m_control_passed:" + json.dumps(F01 not in failed and F01 not in child_failed)),
):
    r = records[capa_id]
    r["incident_ids"] += ["review:388"]
    r["root_cause_evidence_refs"] += m_refs
    r["updated_at"] = now
    plan = register["action_plans"][capa_id]
    plan["prevention"]["status"] = plan["prevention"]["status"] + "; " + status
    plan["prevention"]["evidence_refs"] = plan["prevention"]["evidence_refs"] + m_refs
register["action_plans"]["ML-CAPA-381-F01"]["prevention"]["evidence_refs"] += ["E-LANE-C-RECEIPT", "E-CONTROL-F01-MODULE-V2"]
register["action_plans"]["ML-CAPA-374"]["prevention"]["evidence_refs"] += ["E-SCHEDULE-WORKER-TEST-V2"]
r = records["ML-CAPA-359"]
r["incident_ids"] += ["review:388"]; r["root_cause_evidence_refs"] += m_refs; r["updated_at"] = now
register["action_plans"]["ML-CAPA-359"]["next_action"] += (" Run m (terminal-section extension): outer Maestro expiries " + json.dumps(timeouts)
    + "; nested child failures " + json.dumps(child_failed) + ".")

template = records["ML-CAPA-379"]
new = copy.deepcopy(template)
new.update(capa_id="ML-CAPA-389", incident_ids=["review:383", "review:388"], state="FIX_CANDIDATE", root_cause_status="HYPOTHESIS",
    root_cause_summary="The terminal section's failure diagnostic, step-disposition and unit-disposition statements ran under the 0.3 s operation budget (dispatcher.py); on the persistent-media reference run k a unit-disposition statement overran it by 0.4 ms under fsync stalls (finding 383). Author-authorized extension (findings 385/389): these statements take min(work_end, now + per_unit_seconds) like run-terminal; the admission reserve formula is unchanged, so the admitted window is never extended but can be consumed earlier under stall (finding 386 N-01).",
    root_cause_evidence_refs=["review:383", "review:388", "E-PRODUCT-389-DISPATCHER"] + m_refs,
    reproducer_id="platform-regression-20261020k outer: test_active_control_deadlines[past-restart] unit-disposition 0.300 s budget overrun by 0.4 ms",
    prevention_test_id="tests/thesis_lite/maestro/test_active_control_deadlines.py inside full run m; ext4 recurrence only observable in a later persistent-media reference run",
    candidate_patch_sha256=sha(ROOT / "src/xverse/maestro/dispatcher.py"),
    affected_versions=["dispatcher.py terminal-section unit statements at operation_seconds (checkpoints 1e081a1b..12ef8655)"], lesson_ids=[], observation_window_end=None,
    created_at=now, updated_at=now)
register["records"].append(new)
register["action_plans"]["ML-CAPA-389"] = dict(
    containment="Checkpoint 12ef86553 retains the pre-extension snapshot; run k's receipts retained; no admission constant changed.",
    correction=dict(status="implemented_product_change_finding_389_author_authorized_finding_385", evidence_refs=["E-PRODUCT-389-DISPATCHER", "review:388"]),
    prevention=dict(status="run_m_terminal_incomplete:" + json.dumps(terminal_outer) + "_child_lines:" + str(terminal_child_lines), evidence_refs=m_refs,
                    limits="One tmpfs full run after the change; the overrun was observed on persistent media, so closure of that class needs a later ext4 reference run."),
    effectiveness=dict(status="NOT_DEMONSTRATED", observation_plan=None, independent_confirmation=False),
    next_action="Observe in the next persistent-media reference run; no further product change proposed.")
register["selected_findings"] = parent["selected_findings"] + [388, 389]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
register["harness_runs"] = dict(parent["harness_runs"], m=dict(returncode=receipt["returncode"], failed=triage["failed_count"],
    child_setup_errors=child_errors, child_failed=child_failed, maestro_timeouts=timeouts, probe_spikes=probe_spikes, probe_summary=probe_summary,
    collected=2098, whole_session_tmpdir_on_tmpfs=True, product_change=["dispatcher.py terminal-section failure/step-disposition/unit-disposition statements at per_unit_seconds (389)"],
    test_changes=["F-01 discriminators (B-02)", "integer-nanosecond comparison (N-02)", "at-most-once docstring (N-03)"], checkpoint_commit_before="12ef86553"))
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"),
                      run_m=register["harness_runs"]["m"])))
