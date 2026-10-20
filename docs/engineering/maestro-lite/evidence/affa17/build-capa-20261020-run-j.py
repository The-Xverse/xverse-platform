"""Build the parent-preserving CAPA successor for run j (authorized terminal-budget product change).

Usage: python3 -I build-capa-20261020-run-j.py   (after run j is terminal and triaged)

Parent: capa-20261020-run-i/register.json (46 records / 332 bindings). Additive only: run j evidence,
review spans 377-379 (380 is bound by the next successor), the changed dispatcher.py as the candidate
patch; new record ML-CAPA-379 (transitive run-terminal statement margin; correction = authorized product
change of finding 377/379; prevention = run j); 366 stays REJECTED and points at 379; 222/357/359-CHILD/
364/374 gain run j as prevention observations; 359 gains run j's child outcome. No effectiveness claimed.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261020-run-i"
OUT = BASE / "capa-20261020-run-j"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa17.md"
RUN = BASE / "platform-regression-20261020j"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "49bd43abf862574ac46888cb249fd9944e873ab634b1d9ee1c7d244ea94600d2"
assert len(parent["records"]) == 46 and len(parent["evidence"]) == 332
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
timeouts = sorted(f["nodeid"] for f in triage["failures"] if "thesis_lite/maestro" in f["nodeid"]
                  and any("ML-PERSIST-TIMEOUT" in l or "TEARDOWN-INCOMPLETE" in l or "TERMINAL-INCOMPLETE" in l for l in f["traceback_last_lines"]))
terminal_incomplete = sorted(c for c in child_failed + sorted(failed) if "transitive" in c)
probe_rows = [json.loads(l) for l in (RUN / "fsync-probe.jsonl").read_text().splitlines()] if (RUN / "fsync-probe.jsonl").is_file() else []
probe_summary = next((r for r in probe_rows if r.get("summary")), None)
probe_spikes = sum(1 for r in probe_rows if "fsync_seconds" in r and not r.get("summary"))

new_evidence = {"review:377": span("377.", "378."), "review:378": span("378.", "379."), "review:379": span("379.", "380.")}
for name, path in (("RECEIPT", "source-receipt.json"), ("LOG", "source.log"), ("TRIAGE", "failure-triage.json"),
                   ("FSYNC-PROBE", "fsync-probe.jsonl"), ("GC-LOG", "gc-pauses.jsonl"), ("CONFIG", "configuration.json")):
    if (RUN / path).is_file():
        new_evidence["E-HARNESS-J-" + name] = file(RUN / path)
new_evidence["E-HARNESS-J-DRIVER"] = file(BASE / "verify-platform-regression-20261020j.py")
new_evidence["E-PRODUCT-379-DISPATCHER"] = file(ROOT / "src/xverse/maestro/dispatcher.py")
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
j_refs = [k for k in new_evidence if k.startswith("E-HARNESS-J-")] + ["review:378", "review:379"]

for capa_id, status in (
    ("ML-CAPA-357", "run_j_build_signature_absent:" + json.dumps(build_nodes_absent)),
    ("ML-CAPA-359-CHILD", "run_j_child_setup_errors:" + str(child_errors)),
    ("ML-CAPA-222", "run_j_leaf_reproducer_passed:" + json.dumps(LEAF not in failed and LEAF not in child_failed)),
    ("ML-CAPA-364", "run_j_whole_session_tmpfs_timeouts_" + str(len(timeouts)) + "_probe_spikes_" + str(probe_spikes)
                    + ("_summary_terminal" if probe_summary else "_summary_absent")),
    ("ML-CAPA-374", "run_j_schedule_worker_case_" + ("failed" if SW in child_failed or SW in failed else "passed")),
):
    r = records[capa_id]
    r["incident_ids"] += ["review:378"]
    r["root_cause_evidence_refs"] += j_refs
    r["updated_at"] = now
    plan = register["action_plans"][capa_id]
    plan["prevention"]["status"] = plan["prevention"]["status"] + "; " + status
    plan["prevention"]["evidence_refs"] = plan["prevention"]["evidence_refs"] + j_refs
r = records["ML-CAPA-359"]
r["incident_ids"] += ["review:378"]; r["root_cause_evidence_refs"] += j_refs; r["updated_at"] = now
register["action_plans"]["ML-CAPA-359"]["next_action"] += (" Run i (clean, 2096 passed): no expiries. Run j (terminal-budget product change): outer Maestro expiries "
    + json.dumps(timeouts) + "; nested child failures " + json.dumps(child_failed) + ".")
r = records["ML-CAPA-366"]
r["incident_ids"] += ["review:379"]; r["root_cause_evidence_refs"] += ["review:377", "review:379"]; r["updated_at"] = now
register["action_plans"]["ML-CAPA-366"]["next_action"] = "Superseded by ML-CAPA-379: the author authorized the product change (finding 377) applied in finding 379; this record stays REJECTED for the fixture-level correction."

template = records["ML-CAPA-364"]
new = copy.deepcopy(template)
new.update(capa_id="ML-CAPA-379", incident_ids=["review:366", "review:375", "review:377", "review:379"], state="FIX_CANDIDATE", root_cause_status="HYPOTHESIS",
    root_cause_summary="The run-terminal statement of a four-unit transitive cohort (~0.13 s typical, 0.22 s p99) ran under the operation budget (0.3 s), which the 5 s probe cap, the 2 s restart budget and the period invariant force; the teardown and cleanup statements already use per_unit_seconds. Authorized product change (finding 377): the terminal statement takes min(work_end, now + per_unit_seconds). Margin hypothesis: the terminal expiry class (run f child) disappears; a remaining expiry would be outside the fixture-margin class.",
    root_cause_evidence_refs=["review:366", "review:375", "review:377", "review:379", "E-PRODUCT-379-DISPATCHER"] + j_refs,
    reproducer_id="platform-regression-20261020f nested child: test_active_transitive_restart[omitted-dependent] ML-SCHEDULE-TERMINAL-INCOMPLETE at 0.3 s",
    prevention_test_id="tests/thesis_lite/maestro/test_active_transitive_restart.py (transitive cohort) inside full run j",
    candidate_patch_sha256=sha(ROOT / "src/xverse/maestro/dispatcher.py"),
    affected_versions=["dispatcher.py run-terminal budget operation_seconds (runs a-i, checkpoint 1e081a1b)"], lesson_ids=[], observation_window_end=None,
    created_at=now, updated_at=now)
register["records"].append(new)
register["action_plans"]["ML-CAPA-379"] = dict(
    containment="Checkpoint commit 1e081a1b retains the pre-change snapshot; run f's failing child receipt retained; no budget constant or admission invariant changed.",
    correction=dict(status="implemented_product_change_finding_379_author_authorized_finding_377", evidence_refs=["E-PRODUCT-379-DISPATCHER", "review:377", "review:379"]),
    prevention=dict(status="run_j_transitive_terminal_incomplete:" + json.dumps(terminal_incomplete) + "; targeted source-phase verification 37 passed", evidence_refs=j_refs,
                    limits="One full run after the change; the expiry class was rare (one child case in six tmpfs runs), so one clean run does not demonstrate closure."),
    effectiveness=dict(status="NOT_DEMONSTRATED", observation_plan=None, independent_confirmation=False),
    next_action="Observe the transitive modules across subsequent full runs and the ext4 reference run (disposition d).")
register["selected_findings"] = parent["selected_findings"] + [378, 379]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
register["harness_runs"] = dict(parent["harness_runs"], j=dict(returncode=receipt["returncode"], failed=triage["failed_count"],
    child_setup_errors=child_errors, child_failed=child_failed, maestro_timeouts=timeouts, probe_spikes=probe_spikes, probe_summary=probe_summary,
    collected=2096, whole_session_tmpdir_on_tmpfs=True, product_change=["dispatcher.py run-terminal statement budget per_unit_seconds (379)"],
    checkpoint_commit_before_change="1e081a1ba37a8ea9fdf0f5230ffb61a4157652d3"))
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"),
                      run_j=register["harness_runs"]["j"])))
