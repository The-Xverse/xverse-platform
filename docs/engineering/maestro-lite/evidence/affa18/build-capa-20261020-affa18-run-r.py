"""Build the increment18 CAPA successor for the native F-02 fix (checkpoint 18-4, run r).

Usage: python3 -I build-capa-20261020-affa18-run-r.py   (after run r is terminal and triaged)

Parent: capa-20261020-affa18-run-p/register.json (50 records / 446 bindings). Additive only: review spans
402-408 (409, the run-r review, is bound by the next successor), the three F-02 reviews, the changed helpers and Python modules,
the F-02 control module, environment h, runtime lane e, crash-point f, proposal d, lane admission f, the
aborted run-q preflight, run r (3 failed under a changed host condition, finding 409) and the A/B load
discrimination (F-02 not the discriminator). ML-CAPA-381-F02 moves to FIX_CANDIDATE with the native correction; run r
is added as a prevention observation on 222/357/359-CHILD/364/374/379/381-F01/381-F02/389. No effectiveness.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261020-affa18-run-p"
OUT = BASE / "capa-20261020-affa18-run-r"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa18.md"
RUN = BASE / "platform-regression-20261020r"
ABORTED = BASE / "platform-regression-20261020q"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "552f79f8e846ed7adbc29eca57d80e17a6a199240d0260835f5e4502df44693d"
assert len(parent["records"]) == 50 and len(parent["evidence"]) == 446
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
F02 = "tests/thesis_lite/maestro/test_affa_watch_token.py"
f02_failed = sorted(n for n in failed | set(child_failed) if n.startswith(F02))
timeouts = sorted(f["nodeid"] for f in triage["failures"] if "thesis_lite/maestro" in f["nodeid"]
                  and any("ML-PERSIST-TIMEOUT" in l or "TEARDOWN-INCOMPLETE" in l or "TERMINAL-INCOMPLETE" in l for l in f["traceback_last_lines"]))
terminal_outer = sorted(f["nodeid"] for f in triage["failures"] if any("TERMINAL-INCOMPLETE" in l for l in f["traceback_last_lines"]))
probe_rows = [json.loads(l) for l in (RUN / "fsync-probe.jsonl").read_text().splitlines()] if (RUN / "fsync-probe.jsonl").is_file() else []
probe_summary = next((r for r in probe_rows if r.get("summary")), None)
probe_spikes = sum(1 for r in probe_rows if "fsync_seconds" in r and not r.get("summary"))
lane = read(BASE / "lane-admission-20261020f" / "receipt.json")

new_evidence = {}
for n in range(402, 409):
    new_evidence["review:%d" % n] = span("%d." % n, "%d." % (n + 1))
for name, path in (("RECEIPT", "source-receipt.json"), ("LOG", "source.log"), ("TRIAGE", "failure-triage.json"),
                   ("FSYNC-PROBE", "fsync-probe.jsonl"), ("STALL-CORRELATION", "stall-fsync-correlation.json"), ("GC-LOG", "gc-pauses.jsonl"), ("CONFIG", "configuration.json")):
    if (RUN / path).is_file():
        new_evidence["E-AFFA18-R-" + name] = file(RUN / path)
new_evidence["E-AFFA18-R-DRIVER"] = file(BASE / "verify-platform-regression-20261020r.py")
new_evidence["E-AFFA18-R-AB-SCRIPT"] = file(BASE / "ab-load-discrimination-20261020a.py")
new_evidence["E-AFFA18-R-AB-RECEIPT"] = file(BASE / "ab-load-discrimination-20261020a" / "receipt.json")
new_evidence["E-AFFA18-Q-ABORTED-COLLECTED"] = file(ABORTED / "collected.log")
for key, path in (("E-AFFA18-ENV-H", "platform-environment-20261020h/preparation.json"),
                  ("E-AFFA18-LANE-E", "runtime-lane-20261020e/receipt.json"),
                  ("E-AFFA18-CRASH-F", "crash-matrix-20261020f/receipt.json"),
                  ("E-AFFA18-LANE-PROPOSAL-D", "lane-admission-proposal-20261020d.json"),
                  ("E-AFFA18-LANE-ADMISSION-F", "lane-admission-20261020f/receipt.json"),
                  ("E-AFFA18-REVIEW-F02", "helper-change-f02-independent-review-20261020.json"),
                  ("E-AFFA18-REVIEW-DUMPABLE", "helper-change-dumpable-independent-review-20261020.json")):
    new_evidence[key] = file(BASE / path)
for key, path in (("E-AFFA18-F02-SUPERVISOR", "src/xverse/maestro/native/bootstrap.c"),
                  ("E-AFFA18-F02-AUTHORITY", "src/xverse/maestro/native/run_authority.c"),
                  ("E-AFFA18-F02-PROTOCOL", "src/xverse/maestro/affa_protocol.py"),
                  ("E-AFFA18-F02-BOOTSTRAP-PY", "src/xverse/maestro/bootstrap.py"),
                  ("E-AFFA18-F02-CLIENT", "src/xverse/maestro/affa_client.py"),
                  ("E-AFFA18-F02-BROKER", "src/xverse/maestro/run_broker.py"),
                  ("E-AFFA18-F02-CONTROLS", "tests/thesis_lite/maestro/test_affa_watch_token.py")):
    new_evidence[key] = file(ROOT / path)
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
r_refs = [k for k in new_evidence if k.startswith("E-AFFA18-R-")] + ["review:408"]
ab = read(BASE / "ab-load-discrimination-20261020a" / "receipt.json")
ab_rates = {arm: {n.split("::")[1]: v for n, v in counts.items() if n != "runs"} for arm, counts in ab["failures_per_arm"].items()}

for capa_id, status in (
    ("ML-CAPA-357", "affa18_run_r_build_signature_absent:" + json.dumps(build_nodes_absent)),
    ("ML-CAPA-359-CHILD", "affa18_run_r_child_setup_errors:" + str(child_errors)),
    ("ML-CAPA-222", "affa18_run_r_leaf_reproducer_passed:" + json.dumps(LEAF not in failed and LEAF not in child_failed)),
    ("ML-CAPA-364", "affa18_run_r_whole_session_tmpfs_timeouts_" + str(len(timeouts)) + "_probe_spikes_" + str(probe_spikes)
                    + ("_summary_terminal" if probe_summary else "_summary_absent")
                    + "_ab_paused_shared_failures_A_" + str(ab_rates["A"]["test_paused_shared_ticks_renew_both_original_leases_and_observe_health"])
                    + "_B_" + str(ab_rates["B"]["test_paused_shared_ticks_renew_both_original_leases_and_observe_health"]) + "_of_10_under_host_load"),
    ("ML-CAPA-374", "affa18_run_r_schedule_worker_case_" + ("failed" if SW in child_failed or SW in failed else "passed")),
    ("ML-CAPA-379", "affa18_run_r_terminal_incomplete:" + json.dumps(terminal_outer)),
    ("ML-CAPA-381-F01", "affa18_run_r_control_passed:" + json.dumps(F01 not in failed and F01 not in child_failed)),
    ("ML-CAPA-389", "affa18_run_r_terminal_incomplete:" + json.dumps(terminal_outer)),
):
    r = records[capa_id]
    r["incident_ids"] += ["review:408"]
    r["root_cause_evidence_refs"] += r_refs
    r["updated_at"] = now
    plan = register["action_plans"][capa_id]
    plan["prevention"]["status"] = plan["prevention"]["status"] + "; " + status
    plan["prevention"]["evidence_refs"] = plan["prevention"]["evidence_refs"] + r_refs
r = records["ML-CAPA-359"]
r["incident_ids"] += ["review:408"]; r["root_cause_evidence_refs"] += r_refs; r["updated_at"] = now
register["action_plans"]["ML-CAPA-359"]["next_action"] += (" Increment18 run r (F-02): outer Maestro expiries " + json.dumps(timeouts)
    + "; nested child failures " + json.dumps(child_failed) + "; run under an unrelated CARLA simulator load (finding 409); A/B on the"
    " failing node IDs (pre-F-02 d52683ad vs F-02 e290ce78c, ten interleaved iterations each): " + json.dumps(ab_rates)
    + "; F-02 not the discriminator; host contention supported, not proven; a clean full run on e290ce78c is owed once the host is quiet.")

f02_refs = ["review:403", "review:404", "review:405", "review:406", "review:407", "E-AFFA18-F02-SUPERVISOR", "E-AFFA18-F02-AUTHORITY",
            "E-AFFA18-F02-PROTOCOL", "E-AFFA18-F02-BOOTSTRAP-PY", "E-AFFA18-F02-CLIENT", "E-AFFA18-F02-BROKER", "E-AFFA18-REVIEW-F02", "E-AFFA18-REVIEW-DUMPABLE"]
r = records["ML-CAPA-381-F02"]
r["state"] = "FIX_CANDIDATE"
r["incident_ids"] += ["review:403", "review:405", "review:407"]
r["root_cause_evidence_refs"] += f02_refs + ["E-AFFA18-F02-CONTROLS"] + r_refs
r["candidate_patch_sha256"] = sha(ROOT / "src/xverse/maestro/native/run_authority.c")
r["prevention_test_id"] = F02 + "::test_advance_requires_the_supervisor_watch_token"
r["affected_versions"] = r["affected_versions"] + ["fixed candidate run_authority.c " + sha(ROOT / "src/xverse/maestro/native/run_authority.c")
                                                   + " and bootstrap.c " + sha(ROOT / "src/xverse/maestro/native/bootstrap.c") + " (increment18, e290ce78c)"]
r["updated_at"] = now
plan = register["action_plans"]["ML-CAPA-381-F02"]
plan["correction"] = dict(status="native_watch_proof_implemented_increment18_findings_403_407_supervisor_hmac_token_verified_on_advance",
                          evidence_refs=f02_refs)
plan["prevention"] = dict(
    status=("controls_correct_advances_missing_foreign_forged_rejected_natively; packet_and_client_check_tests; lane_admission_f_passed:" + json.dumps(lane["passed"])
            + "; affa18_run_r_f02_failures:" + json.dumps(f02_failed)),
    evidence_refs=["E-AFFA18-F02-CONTROLS", "E-AFFA18-LANE-ADMISSION-F", "E-AFFA18-LANE-E", "E-AFFA18-CRASH-F"] + r_refs,
    limits=("Claimed against a buggy, regressed or bypassed Python precondition. Not claimed: key confidentiality against a hostile same-uid peer "
            "(F02D-01, finding 407: the authority is dumpable between execveat and main while holding the key memfd). A token proves the boundary "
            "was watched, not that the supervisor still lives (F02R-04); a token binds a boundary identity, not a unit, slot or generation (F02R-07); "
            "the negative controls run against a directly launched authority, the supervisor-born path is tested positively (F02R-05)."))
plan["next_action"] = "Observe across subsequent full runs; option for a later hardening increment: an owner-unreadable authority image enforced by the supervisor (F02D-01)."
register["selected_findings"] = parent["selected_findings"] + [402, 403, 404, 405, 406, 407, 408]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
register["harness_runs"] = dict(parent["harness_runs"],
    affa18_q=dict(aborted=True, reason="stopped at the collection preflight: 2104 collected against a declared 2102 (finding 408)", collected=2104),
    affa18_r=dict(returncode=receipt["returncode"], failed=triage["failed_count"], child_setup_errors=child_errors, child_failed=child_failed,
                  maestro_timeouts=timeouts, probe_spikes=probe_spikes, probe_summary=probe_summary, collected=2104,
                  whole_session_tmpdir_on_tmpfs=True, clean=False,
                  host_condition="unrelated CARLA simulator load from 16 min before start (finding 409)",
                  ab_discrimination=dict(receipt="ab-load-discrimination-20261020a/receipt.json", iterations=ab["iterations"], failures=ab_rates,
                                         conclusion="F-02 not the discriminator; host contention supported, not proven"), environment="platform-environment-20261020h (wheel of the increment18 tree)",
                  product_change=["native F-02 watch proof (bootstrap.c, run_authority.c, affa_protocol.py, bootstrap.py, affa_client.py, run_broker.py)"]))
register["increment18"] = dict(register["increment18"], checkpoint_18_4="e290ce78c")
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"),
                      run_r=register["harness_runs"]["affa18_r"])))
