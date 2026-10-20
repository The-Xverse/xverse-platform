"""Build the parent-preserving CAPA successor for run i (sign-off, redesign results, crash-matrix b).

Usage: python3 -I build-capa-20261020-run-i.py   (after run i is terminal and triaged)

Parent: capa-20261020-author-decisions/register.json (45 records / 307 bindings). Additive only:
evidence for run i, crash-matrix b, the sign-off record, the independent endpoint review (if present)
and review spans 371-376 (377 is bound by the next successor); new record ML-CAPA-374 (schedule-worker
nanosecond-rounding test defect, FIX_CANDIDATE with run i as its prevention observation); 366 gains
finding 375 (fixture redesign infeasible, product proposal) and stays REJECTED; 222/357/359-CHILD/364
gain run i as prevention observations; 359 gains run i's child outcome. No effectiveness is claimed.
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
PARENT_DIR = BASE / "capa-20261020-author-decisions"
OUT = BASE / "capa-20261020-run-i"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa17.md"
RUN = BASE / "platform-regression-20261020i"
CRASH = BASE / "crash-matrix-20261020b"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "9b9cba0ea0eea76fe0e22d80dd84a18965fc5b4ab8a9fb1eafc2a6b2c642cddb"
assert len(parent["records"]) == 45 and len(parent["evidence"]) == 307
register = copy.deepcopy(parent)
now = datetime.now(timezone.utc).isoformat()
records = {r["capa_id"]: r for r in register["records"]}
template = records["ML-CAPA-364"]

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
timeouts = sorted(f["nodeid"] for f in triage["failures"] if "thesis_lite/maestro" in f["nodeid"]
                  and any("ML-PERSIST-TIMEOUT" in l or "TEARDOWN-INCOMPLETE" in l or "TERMINAL-INCOMPLETE" in l for l in f["traceback_last_lines"]))
probe_rows = [json.loads(l) for l in (RUN / "fsync-probe.jsonl").read_text().splitlines()] if (RUN / "fsync-probe.jsonl").is_file() else []
probe_summary = next((r for r in probe_rows if r.get("summary")), None)
probe_spikes = sum(1 for r in probe_rows if "fsync_seconds" in r and not r.get("summary"))

new_evidence = {"review:368": span("368.", "369."),  # run h review, unbound until now (last-finding rule)
                "review:371": span("371.", "372."), "review:372": span("372.", "373."), "review:373": span("373.", "374."),
                "review:374": span("374.", "375.")}
for name, path in (("RECEIPT", "source-receipt.json"), ("LOG", "source.log"), ("TRIAGE", "failure-triage.json"),
                   ("FSYNC-PROBE", "fsync-probe.jsonl"), ("GC-LOG", "gc-pauses.jsonl"), ("CONFIG", "configuration.json")):
    if (RUN / path).is_file():
        new_evidence["E-HARNESS-I-" + name] = file(RUN / path)
new_evidence["E-HARNESS-I-DRIVER"] = file(BASE / "verify-platform-regression-20261020i.py")
new_evidence["E-HARNESS-I-SCHEDULE-WORKER-TEST"] = file(ROOT / "tests/thesis_lite/maestro/test_schedule_worker.py")
for name, path in (("RECEIPT", "receipt.json"), ("CONFIG", "configuration.json"), ("SOURCE-LOG", "source.log"), ("WHEEL-LOG", "wheel.log")):
    new_evidence["E-CRASH-B-" + name] = file(CRASH / path)
new_evidence["E-CRASH-B-DRIVER"] = file(BASE / "verify-crash-matrix-20261020b.py")
new_evidence["E-CRASH-B-MODULE"] = file(ROOT / "tests/thesis_lite/maestro/test_composed_post_release_loss.py")
new_evidence["E-SIGNOFF-20261020"] = file(BASE / "author-signoff-20261020.json")
review_path = BASE / "endpoint-reconciliation-independent-review-20261020.json"
new_evidence["E-DECISIONS-20261020-ENDPOINT-INDEPENDENT-REVIEW"] = file(review_path)
new_evidence["E-DECISIONS-20261020-ENDPOINT-PROPOSAL-V2"] = file(BASE / "endpoint-reconciliation-proposal-20261020-v2.json")
new_evidence["review:375"] = span("375.", "376.")
new_evidence["review:376"] = span("376.", "377.")
new_evidence["E-DECISIONS-20261020-ENDPOINT-REBOUND-TRACE"] = file(BASE / "endpoint-rebound-traceability-20261020.json")
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
i_refs = [k for k in new_evidence if k.startswith("E-HARNESS-I-")] + ["review:374"]

for capa_id, status in (
    ("ML-CAPA-357", "run_i_build_signature_absent:" + json.dumps(build_nodes_absent)),
    ("ML-CAPA-359-CHILD", "run_i_child_setup_errors:" + str(child_errors)),
    ("ML-CAPA-222", "run_i_leaf_reproducer_passed:" + json.dumps(LEAF not in failed)),
    ("ML-CAPA-364", "run_i_whole_session_tmpfs_timeouts_" + str(len(timeouts)) + "_probe_spikes_" + str(probe_spikes)
                    + ("_summary_terminal" if probe_summary else "_summary_absent")),
):
    r = records[capa_id]
    r["incident_ids"] += ["review:374"]
    r["root_cause_evidence_refs"] += i_refs
    r["updated_at"] = now
    plan = register["action_plans"][capa_id]
    plan["prevention"]["status"] = plan["prevention"]["status"] + "; " + status
    plan["prevention"]["evidence_refs"] = plan["prevention"]["evidence_refs"] + i_refs
r = records["ML-CAPA-359"]
r["incident_ids"] += ["review:374"]; r["root_cause_evidence_refs"] += i_refs; r["updated_at"] = now
register["action_plans"]["ML-CAPA-359"]["next_action"] += (" Run i (test redesign 374): outer Maestro expiries " + json.dumps(timeouts)
    + "; nested child failures " + json.dumps(child_failed) + ". Run h's child case reclassified as a nanosecond-rounding test defect (ML-CAPA-374).")
r = records["ML-CAPA-366"]
r["incident_ids"] += ["review:374"]; r["root_cause_evidence_refs"] += ["review:374"]; r["updated_at"] = now
register["action_plans"]["ML-CAPA-366"]["next_action"] = ("Fixture redesign found infeasible (finding 375: probe values capped at 5 s, restart budget 2 s, "
    "period invariant allow op < 1/3 s). Product proposal pending author decision: run-terminal statement (dispatcher.py:1465) to use per_unit_seconds. "
    "Transitive budget stays 0.3 s; run i child transitive outcome: " + json.dumps([c for c in child_failed if "transitive" in c]) + ".")

new = copy.deepcopy(template)
new.update(capa_id="ML-CAPA-374", incident_ids=["review:368", "review:374"], state="FIX_CANDIDATE", root_cause_status="HYPOTHESIS",  # policy enum: UNKNOWN|HYPOTHESIS|VERIFIED; no independent confirmation
    root_cause_summary="test_schedule_worker compared the gate's renewal receipt with the requested HostDeadline by float equality; the gate quantizes the request to integer nanoseconds (owner._deadline) and reports next_lease/1e9, and the float round trip differs by one unit in the last place for value-dependent inputs, so the equality fails intermittently (run h child, first occurrence in a-h). Test precision defect; the quantized report is the correct product value.",
    root_cause_evidence_refs=["review:368", "review:374", "E-HARNESS-I-SCHEDULE-WORKER-TEST"] + i_refs,
    reproducer_id="platform-regression-20261020h nested child: monotonic_seconds 1051666.733586106 != 1051666.733586107",
    prevention_test_id=SW, candidate_patch_sha256=sha(ROOT / "tests/thesis_lite/maestro/test_schedule_worker.py"),
    affected_versions=["test_schedule_worker.py before the nanosecond comparison (runs a-h)"], lesson_ids=[], observation_window_end=None,
    created_at=now, updated_at=now)
register["records"].append(new)
register["action_plans"]["ML-CAPA-374"] = dict(
    containment="Run h's failing child receipt and traceback retained; no product change; no retry for luck.",
    correction=dict(status="implemented_in_test_nanosecond_comparison_finding_374", evidence_refs=["E-HARNESS-I-SCHEDULE-WORKER-TEST", "review:374"]),
    prevention=dict(status="run_i_schedule_worker_case_" + ("failed" if SW in child_failed or SW in failed else "passed"), evidence_refs=i_refs,
                    limits="One full run; the defect is value-dependent, so one pass does not demonstrate closure."),
    effectiveness=dict(status="NOT_DEMONSTRATED", observation_plan=None, independent_confirmation=False),
    next_action="Observe across subsequent full runs; no further action unless the comparison fails again.")
register["selected_findings"] = parent["selected_findings"] + [372, 373, 374, 375, 376, 377]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
register["harness_runs"] = dict(parent["harness_runs"], i=dict(returncode=receipt["returncode"], failed=triage["failed_count"],
    child_setup_errors=child_errors, child_failed=child_failed, maestro_timeouts=timeouts, probe_spikes=probe_spikes, probe_summary=probe_summary,
    collected=2096, whole_session_tmpdir_on_tmpfs=True, test_redesign=["test_schedule_worker.py nanosecond comparison (374)"]))
register["author_signoff_20261020"] = dict(record="E-SIGNOFF-20261020", dispositions_confirmed=["AD-2026-10-20-a", "AD-2026-10-20-b", "AD-2026-10-20-c", "AD-2026-10-20-d"],
    source_parent_v4=dict(path="specs/024-maestro-lite-lifecycle/engineering/successors/ML-SOURCE-PARENT-2026-10-20-v4/source-parent-register.json",
                          repository="/home/jefferson/distributed_safety_critical_thesis", sha256="41e28ad0f5f440ab87dad014205a8ffc3780427aa6311c4745be765f4554115d"),
    endpoint_independent_review_present=True, endpoint_v2_author_accepted=True, terminal_budget_product_change_authorized=True, commit_authorized_after_clean_full_run=True, accepted=False, merged=False)
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"),
                      run_i=register["harness_runs"]["i"])))
