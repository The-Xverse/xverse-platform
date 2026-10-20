"""Build the first increment18 CAPA successor (native F-01 fix, run o).

Usage: python3 -I build-capa-20261020-affa18-run-o.py   (after run o and lane driver d are terminal)

Parent: ../affa17/capa-20261020-acceptance/register.json (50 records / 408 bindings; increment17 accepted).
Additive only: the frozen increment17 review log as a file binding (its last finding 392 has no end
marker), review-affa18 spans 393-400 (401 is bound by the next successor), the changed helper, the F-01 control, environment f, runtime lane
c, crash-point d, lane admission d, the two independent reviews, the aborted run n and run o.
ML-CAPA-381-F01 moves to FIX_CANDIDATE with the native correction and its prevention observations;
ML-CAPA-381-F02 records the deferral with design options; run o is added as a prevention observation on
222/357/359-CHILD/364/374/379/389. The register's increment17 acceptance stays as recorded; a new
increment18 block says not accepted. No effectiveness claimed. Run both validators afterwards.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
AFFA17 = BASE.parent / "affa17"
PARENT_DIR = AFFA17 / "capa-20261020-acceptance"
OUT = BASE / "capa-20261020-affa18-run-o"
REVIEW17 = ROOT / "docs/engineering/maestro-lite/review-affa17.md"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa18.md"
RUN = BASE / "platform-regression-20261020o"
ABORTED = BASE / "platform-regression-20261020n"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "6931d9cbd7bdd80a86d8a666ea43fcb7b95e2628ba7b49c7de2b87cd5152e779"
assert len(parent["records"]) == 50 and len(parent["evidence"]) == 408
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
probe_rows = [json.loads(l) for l in (RUN / "fsync-probe.jsonl").read_text().splitlines()] if (RUN / "fsync-probe.jsonl").is_file() else []
probe_summary = next((r for r in probe_rows if r.get("summary")), None)
probe_spikes = sum(1 for r in probe_rows if "fsync_seconds" in r and not r.get("summary"))
lane = read(BASE / "lane-admission-20261020e" / "receipt.json")

new_evidence = {"E-REVIEW-AFFA17-FROZEN": file(REVIEW17)}
for n in range(393, 401):
    new_evidence["review:%d" % n] = span("%d." % n, "%d." % (n + 1))
for name, path in (("RECEIPT", "source-receipt.json"), ("LOG", "source.log"), ("TRIAGE", "failure-triage.json"),
                   ("FSYNC-PROBE", "fsync-probe.jsonl"), ("GC-LOG", "gc-pauses.jsonl"), ("CONFIG", "configuration.json")):
    if (RUN / path).is_file():
        new_evidence["E-AFFA18-O-" + name] = file(RUN / path)
new_evidence["E-AFFA18-O-DRIVER"] = file(BASE / "verify-platform-regression-20261020o.py")
for name, path in (("LOG", "source.log"), ("CONFIG", "configuration.json")):
    new_evidence["E-AFFA18-N-ABORTED-" + name] = file(ABORTED / path)
for key, path in (("E-AFFA18-ENV-F", "platform-environment-20261020f/preparation.json"),
                  ("E-AFFA18-ENV-F-BUILDER", "prepare-platform-environment-20261020f.py"),
                  ("E-AFFA18-LANE-C", "runtime-lane-20261020c/receipt.json"),
                  ("E-AFFA18-CRASH-D", "crash-matrix-20261020d/receipt.json"),
                  ("E-AFFA18-LANE-ADMISSION-E", "lane-admission-20261020e/receipt.json"),
                  ("E-AFFA18-LANE-PROPOSAL-C", "lane-admission-proposal-20261020c.json"),
                  ("E-AFFA18-LANE-PROPOSAL-B-SUPERSEDED", "lane-admission-proposal-20261020b.json"),
                  ("E-AFFA18-REVIEW-F01", "helper-change-f01-independent-review-20261020.json"),
                  ("E-AFFA18-REVIEW-TWOPASS", "helper-change-twopass-independent-review-20261020.json")):
    new_evidence[key] = file(BASE / path)
new_evidence["E-AFFA18-RUN-AUTHORITY"] = file(ROOT / "src/xverse/maestro/native/run_authority.c")
new_evidence["E-AFFA18-F01-CONTROL"] = file(ROOT / "tests/thesis_lite/maestro/test_affa_release_timeout_fence.py")
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
o_refs = [k for k in new_evidence if k.startswith("E-AFFA18-O-")]

for capa_id, status in (
    ("ML-CAPA-357", "affa18_run_o_build_signature_absent:" + json.dumps(build_nodes_absent)),
    ("ML-CAPA-359-CHILD", "affa18_run_o_child_setup_errors:" + str(child_errors)),
    ("ML-CAPA-222", "affa18_run_o_leaf_reproducer_passed:" + json.dumps(LEAF not in failed and LEAF not in child_failed)),
    ("ML-CAPA-364", "affa18_run_o_whole_session_tmpfs_timeouts_" + str(len(timeouts)) + "_probe_spikes_" + str(probe_spikes)
                    + ("_summary_terminal" if probe_summary else "_summary_absent")),
    ("ML-CAPA-374", "affa18_run_o_schedule_worker_case_" + ("failed" if SW in child_failed or SW in failed else "passed")),
    ("ML-CAPA-379", "affa18_run_o_terminal_incomplete:" + json.dumps(terminal_outer)),
    ("ML-CAPA-389", "affa18_run_o_terminal_incomplete:" + json.dumps(terminal_outer)),
):
    r = records[capa_id]
    r["incident_ids"] += ["review:397"]
    r["root_cause_evidence_refs"] += o_refs
    r["updated_at"] = now
    plan = register["action_plans"][capa_id]
    plan["prevention"]["status"] = plan["prevention"]["status"] + "; " + status
    plan["prevention"]["evidence_refs"] = plan["prevention"]["evidence_refs"] + o_refs
r = records["ML-CAPA-359"]
r["incident_ids"] += ["review:397"]; r["root_cause_evidence_refs"] += o_refs; r["updated_at"] = now
register["action_plans"]["ML-CAPA-359"]["next_action"] += (" Increment18 run o: outer Maestro expiries " + json.dumps(timeouts)
    + "; nested child failures " + json.dumps(child_failed) + ".")

r = records["ML-CAPA-381-F01"]
r["state"] = "FIX_CANDIDATE"
r["incident_ids"] += ["review:394", "review:395", "review:396", "review:397"]
r["root_cause_evidence_refs"] += ["review:394", "review:395", "review:396", "review:397", "E-AFFA18-RUN-AUTHORITY", "E-AFFA18-F01-CONTROL",
                                  "E-AFFA18-REVIEW-F01", "E-AFFA18-REVIEW-TWOPASS"] + o_refs
r["candidate_patch_sha256"] = sha(ROOT / "src/xverse/maestro/native/run_authority.c")
r["prevention_test_id"] = F01
r["affected_versions"] = r["affected_versions"] + ["fixed candidate run_authority.c " + sha(ROOT / "src/xverse/maestro/native/run_authority.c") + " (increment18)"]
r["updated_at"] = now
plan = register["action_plans"]["ML-CAPA-381-F01"]
plan["correction"] = dict(status="native_fix_implemented_increment18_findings_394_397_two_pass_freeze_independent_close_budget",
                          evidence_refs=["review:394", "review:395", "review:397", "E-AFFA18-RUN-AUTHORITY", "E-AFFA18-REVIEW-F01", "E-AFFA18-REVIEW-TWOPASS"])
plan["prevention"] = dict(
    status=("control_asserts_native_refreeze; negative_check_increment17_helper_fails (finding 395); lane_admission_e_passed:" + json.dumps(lane["passed"])
            + "; affa18_run_o_control_passed:" + json.dumps(F01 not in failed and F01 not in child_failed)),
    evidence_refs=["E-AFFA18-F01-CONTROL", "E-AFFA18-LANE-ADMISSION-E", "E-AFFA18-LANE-C", "E-AFFA18-CRASH-D"] + o_refs,
    limits="The control reaches the reason-4 path only; the reason-6 (FREEZE_FAILED) and bounded-wait branches are not exercised. The increment17 helper's behaviour is now reproduced at runtime by the negative check. F01R-01 (late CANCEL/REJECTED reply under slow freezing) is a recorded conservative behaviour change; F01R-03 (closed-loop retry) is deferred.")
plan["next_action"] = "Observe across subsequent full runs and a persistent-media reference run; the Python-side precondition stays in force as defence in depth."
r = records["ML-CAPA-381-F02"]
r["incident_ids"] += ["review:394"]; r["root_cause_evidence_refs"] += ["review:394"]; r["updated_at"] = now
register["action_plans"]["ML-CAPA-381-F02"]["next_action"] = ("Deferred (finding 394 d): a native watch proof needs either a supervisor-issued WATCH token keyed by a secret the "
    "supervisor generates and passes to the authority at birth, or ADVANCE descriptors routed through the supervisor on a new supervisor-authority channel; "
    "both change two helpers and the Python client; author choice requested. The Python precondition affa_client._watched stays the enforcing layer.")
register["selected_findings"] = parent["selected_findings"] + [392, 393, 394, 395, 396, 397, 398, 399, 400]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
register["harness_runs"] = dict(parent["harness_runs"],
    affa18_n=dict(aborted=True, reason="stopped deliberately when the F-01 review recommended the two-pass change (finding 396)", collected=2098),
    affa18_o=dict(returncode=receipt["returncode"], failed=triage["failed_count"], child_setup_errors=child_errors, child_failed=child_failed,
                  maestro_timeouts=timeouts, probe_spikes=probe_spikes, probe_summary=probe_summary, collected=2098,
                  whole_session_tmpdir_on_tmpfs=True, environment="platform-environment-20261020f (wheel of the increment18 tree)",
                  product_change=["run_authority.c F-01: freeze write never skipped, two-pass wait, independent close budget"]))
register["increment18"] = dict(branch="candidate/maestro-lite-affa18-20261020", parent_checkpoint="bdf7b29cc", checkpoint_18_1="7abdb9dc0", accepted=False, merged=False,
                               review_log="docs/engineering/maestro-lite/review-affa18.md")
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"),
                      run_o=register["harness_runs"]["affa18_o"])))
