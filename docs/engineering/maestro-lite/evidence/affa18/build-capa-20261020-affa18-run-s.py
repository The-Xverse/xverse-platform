"""Build the increment18 CAPA successor for the clean full run s on the F-02 bytes.

Usage: python3 -I build-capa-20261020-affa18-run-s.py   (after run s is terminal and triaged)

Parent: capa-20261020-affa18-run-r/register.json (50 records / 478 bindings). Additive only: run s evidence
and review span 409 (410 is bound by the next successor); run s, launched under the finding-409 host load,
is added as a prevention observation on 222/357/359-CHILD/364/374/379/381-F01/381-F02/389; 359 gains run s's
child outcome. No state, cause or effectiveness changes.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261020-affa18-run-r"
OUT = BASE / "capa-20261020-affa18-run-s"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa18.md"
RUN = BASE / "platform-regression-20261020s"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "7f46df79cbcee43791a10b1a924ff5959c0d64e480a27ae8ba3cda02a22935f2"
assert len(parent["records"]) == 50 and len(parent["evidence"]) == 478
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
terminal_child_lines = sum(1 for line in log_lines if line.startswith("E") and ("TERMINAL-INCOMPLETE" in line or "TEARDOWN-INCOMPLETE" in line))
probe_rows = [json.loads(l) for l in (RUN / "fsync-probe.jsonl").read_text().splitlines()] if (RUN / "fsync-probe.jsonl").is_file() else []
probe_summary = next((r for r in probe_rows if r.get("summary")), None)
probe_spikes = sum(1 for r in probe_rows if "fsync_seconds" in r and not r.get("summary"))
correlation = read(RUN / "stall-fsync-correlation.json") if (RUN / "stall-fsync-correlation.json").is_file() else None

new_evidence = {"review:409": span("409.", "410.")}  # 410 has no end marker yet; bound by the next successor
for name, path in (("RECEIPT", "source-receipt.json"), ("LOG", "source.log"), ("TRIAGE", "failure-triage.json"),
                   ("FSYNC-PROBE", "fsync-probe.jsonl"), ("GC-LOG", "gc-pauses.jsonl"), ("CONFIG", "configuration.json"),
                   ("STALL-CORRELATION", "stall-fsync-correlation.json")):
    if (RUN / path).is_file():
        new_evidence["E-AFFA18-S-" + name] = file(RUN / path)
new_evidence["E-AFFA18-S-DRIVER"] = file(BASE / "verify-platform-regression-20261020s.py")
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
p_refs = [k for k in new_evidence if k.startswith("E-AFFA18-S-")] + ["review:409"]
config = read(RUN / "configuration.json")
for capa_id, status in (
    ("ML-CAPA-357", "affa18_run_s_build_signature_absent:" + json.dumps(build_nodes_absent)),
    ("ML-CAPA-359-CHILD", "affa18_run_s_child_setup_errors:" + str(child_errors)),
    ("ML-CAPA-222", "affa18_run_s_leaf_reproducer_passed:" + json.dumps(LEAF not in failed and LEAF not in child_failed)),
    ("ML-CAPA-364", "affa18_run_s_whole_session_tmpfs_under_host_load_timeouts_" + str(len(timeouts)) + "_child_failed_" + str(len(child_failed)) + "_probe_spikes_" + str(probe_spikes)
                    + ("_summary_terminal" if probe_summary else "_summary_absent")),
    ("ML-CAPA-374", "affa18_run_s_schedule_worker_case_" + ("failed" if SW in child_failed or SW in failed else "passed")),
    ("ML-CAPA-379", "affa18_run_s_terminal_incomplete:" + json.dumps(terminal_outer)),
    ("ML-CAPA-381-F01", "affa18_run_s_control_passed:" + json.dumps(F01 not in failed and F01 not in child_failed)),
    ("ML-CAPA-381-F02", "affa18_run_s_first_clean_full_run_on_f02_bytes_f02_failures:" + json.dumps(f02_failed)),
    ("ML-CAPA-389", "affa18_run_s_terminal_incomplete:" + json.dumps(terminal_outer) + "_child_terminal_or_teardown_lines:" + str(terminal_child_lines)),
):
    r = records[capa_id]
    r["incident_ids"] += ["review:409"]
    r["root_cause_evidence_refs"] += p_refs
    r["updated_at"] = now
    plan = register["action_plans"][capa_id]
    plan["prevention"]["status"] = plan["prevention"]["status"] + "; " + status
    plan["prevention"]["evidence_refs"] = plan["prevention"]["evidence_refs"] + p_refs
r = records["ML-CAPA-359"]
r["incident_ids"] += ["review:409"]; r["root_cause_evidence_refs"] += p_refs; r["updated_at"] = now
register["action_plans"]["ML-CAPA-359"]["next_action"] += (" Increment18 run s (clean, under the finding-409 host load): outer Maestro expiries " + json.dumps(timeouts)
    + "; nested child failures " + json.dumps(child_failed) + "; probe spikes " + str(probe_spikes) + ".")
register["selected_findings"] = parent["selected_findings"] + [409]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
register["harness_runs"] = dict(parent["harness_runs"], affa18_s=dict(returncode=receipt["returncode"], failed=triage["failed_count"],
    child_setup_errors=child_errors, child_failed=child_failed, maestro_timeouts=timeouts, probe_spikes=probe_spikes, probe_summary=probe_summary,
    collected=2104, clean=receipt["returncode"] == 0 and triage["failed_count"] == 0, whole_session_tmpdir_on_tmpfs=True,
    tested_src_tests_identical_to="e290ce78c", host_condition_at_launch=config["host_condition_at_launch"],
    stall_fsync_correlation={k: correlation[k] for k in ("operations", "stalls", "spikes", "stalls_inside_window_with_spike", "spike_seconds_max")} if correlation else None))
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"),
                      run_s=register["harness_runs"]["affa18_s"])))
