"""Build the parent-preserving CAPA successor for run k (ext4 reference run) and the IR-ML3-04 records.

Usage: python3 -I build-capa-20261020-run-k.py   (after run k is terminal and triaged)

Parent: capa-20261020-run-j/register.json (47 records / 343 bindings). Additive only: run k evidence
(persistent-media reference under disposition d; expiries are host-condition observations), review span
380 (381 is bound by the next successor), the helper-bytes independent review, the lane admission
proposal and the composed-case indexes; new records ML-CAPA-381-F01 and ML-CAPA-381-F02 (independent
review observations on run_authority.c, UNRESOLVED, no correction, author disposition pending);
222/357/359-CHILD/364/374/379 gain run k as observations; 359 gains run k's child outcome.
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
PARENT_DIR = BASE / "capa-20261020-run-j"
OUT = BASE / "capa-20261020-run-k"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa17.md"
RUN = BASE / "platform-regression-20261020k"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "5442b5438788fe280d9a4b73137d56c631ec900f4aa9bc4f5d28c2f97173d976"
assert len(parent["records"]) == 47 and len(parent["evidence"]) == 343
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
probe_rows = [json.loads(l) for l in (RUN / "fsync-probe.jsonl").read_text().splitlines()] if (RUN / "fsync-probe.jsonl").is_file() else []
probe_summary = next((r for r in probe_rows if r.get("summary")), None)
probe_spikes = sum(1 for r in probe_rows if "fsync_seconds" in r and not r.get("summary"))
correlation = read(RUN / "stall-fsync-correlation.json") if (RUN / "stall-fsync-correlation.json").is_file() else None
helper_review = read(BASE / "helper-bytes-independent-review-20261020.json")
medium = {f["id"]: f for f in helper_review["findings"] if f["severity"] == "MEDIUM"}

terminal_outer = sorted(f["nodeid"] for f in triage["failures"] if any("TERMINAL-INCOMPLETE" in l for l in f["traceback_last_lines"]))
terminal_child_lines = sum(1 for line in log_lines if line.startswith("E") and ("TERMINAL-INCOMPLETE" in line or "TEARDOWN-INCOMPLETE" in line))
new_evidence = {"review:380": span("380.", "381.")}
for name, path in (("RECEIPT", "source-receipt.json"), ("LOG", "source.log"), ("TRIAGE", "failure-triage.json"),
                   ("FSYNC-PROBE", "fsync-probe.jsonl"), ("GC-LOG", "gc-pauses.jsonl"), ("CONFIG", "configuration.json"),
                   ("STALL-CORRELATION", "stall-fsync-correlation.json")):
    if (RUN / path).is_file():
        new_evidence["E-HARNESS-K-" + name] = file(RUN / path)
new_evidence["E-HARNESS-K-DRIVER"] = file(BASE / "verify-platform-regression-20261020k.py")
new_evidence["E-IR04-HELPER-REVIEW"] = file(BASE / "helper-bytes-independent-review-20261020.json")
new_evidence["E-IR04-HELPER-REVIEW-SUMMARY"] = file(BASE / "helper-bytes-independent-review-20261020.md")
new_evidence["E-IR04-LANE-PROPOSAL"] = file(BASE / "lane-admission-proposal-20261020.json")
new_evidence["E-IR04-LANE-PROPOSAL-BUILDER"] = file(BASE / "build-lane-admission-proposal-20261020.py")
for case in ("test_atomic_release_cancel_stage", "test_pre_handle_crash_survival"):
    new_evidence["E-IR04-CASE-INDEX-" + case.upper()] = file(BASE / ("lane-case-index-" + case + "-20261020.json"))
new_evidence["E-IR04-RUN-AUTHORITY-SOURCE"] = file(ROOT / "src/xverse/maestro/native/run_authority.c")
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
k_refs = [k for k in new_evidence if k.startswith("E-HARNESS-K-")] + ["review:380"]

for capa_id, status in (
    ("ML-CAPA-357", "run_k_ext4_build_signature_absent:" + json.dumps(build_nodes_absent)),
    ("ML-CAPA-359-CHILD", "run_k_ext4_child_setup_errors:" + str(child_errors)),
    ("ML-CAPA-222", "run_k_ext4_leaf_reproducer_passed:" + json.dumps(LEAF not in failed and LEAF not in child_failed)),
    ("ML-CAPA-364", "run_k_persistent_media_reference_timeouts_" + str(len(timeouts)) + "_child_failed_" + str(len(child_failed)) + "_probe_spikes_" + str(probe_spikes)
                    + ("_summary_terminal" if probe_summary else "_summary_absent")),
    ("ML-CAPA-374", "run_k_ext4_schedule_worker_case_" + ("failed" if SW in child_failed or SW in failed else "passed")),
    ("ML-CAPA-379", "run_k_ext4_terminal_incomplete:" + json.dumps(terminal_outer) + "_child_terminal_or_teardown_incomplete_lines:" + str(terminal_child_lines)),
):
    r = records[capa_id]
    r["incident_ids"] += ["review:380"]
    r["root_cause_evidence_refs"] += k_refs
    r["updated_at"] = now
    plan = register["action_plans"][capa_id]
    plan["prevention"]["status"] = plan["prevention"]["status"] + "; " + status
    plan["prevention"]["evidence_refs"] = plan["prevention"]["evidence_refs"] + k_refs
register["action_plans"]["ML-CAPA-364"]["prevention"]["limits"] += (" Run k is the persistent-media reference run of disposition d: its expiries are host-condition observations (ext4 root 91 percent full), "
    "not acceptance failures; correlation " + json.dumps({k: correlation[k] for k in ("stalls", "spikes", "stalls_inside_window_with_spike")} if correlation else None) + ".")
r = records["ML-CAPA-359"]
r["incident_ids"] += ["review:380"]; r["root_cause_evidence_refs"] += k_refs; r["updated_at"] = now
register["action_plans"]["ML-CAPA-359"]["next_action"] += (" Run k (ext4 reference): outer Maestro expiries " + json.dumps(timeouts)
    + "; nested child failures " + json.dumps(child_failed) + "; probe spikes " + str(probe_spikes) + ".")

template = records["ML-CAPA-359"]
for fid in ("F-01", "F-02"):
    f = medium[fid]
    new = copy.deepcopy(template)
    new.update(capa_id="ML-CAPA-381-" + fid.replace("-", ""), incident_ids=["review:380"], state="UNRESOLVED", root_cause_status="HYPOTHESIS",
        root_cause_summary="Independent helper-bytes review (separate agent session, finding 381) observation " + fid + " on run_authority.c (" + f["file"] + ":" + str(f["line"]) + "): "
            + f["title"] + ". Scenario: " + f["scenario"] + " Verified against the source by the implementing session; no runtime reproduction; author disposition pending (helper change with new frozen hashes and a fresh review, or a documented Python-side precondition).",
        root_cause_evidence_refs=["E-IR04-HELPER-REVIEW", "E-IR04-HELPER-REVIEW-SUMMARY", "E-IR04-RUN-AUTHORITY-SOURCE", "review:380"],
        reproducer_id=None, prevention_test_id=None, candidate_patch_sha256=None,
        affected_versions=["run_authority.c 2a2ee8306a7f45186355b548888d00e3df9fd22f20fd9fbe9435afa718874563 (frozen bytes reviewed)"],
        lesson_ids=[], observation_window_end=None, created_at=now, updated_at=now)
    register["records"].append(new)
    register["action_plans"][new["capa_id"]] = dict(
        containment="Frozen helper bytes unchanged; the Python callers' existing checks (revoke-then-cleanup; affa_client._watched) remain the enforcing layer; no lane activation.",
        correction=dict(status="none_pending_author_disposition", evidence_refs=[]),
        prevention=dict(status="none", evidence_refs=[], limits="Source-reading observation; not reproduced at runtime."),
        effectiveness=dict(status="NOT_DEMONSTRATED", observation_plan=None, independent_confirmation=False),
        next_action="Author disposition: " + f.get("recommendation", "helper change or documented precondition") + ".")
register["selected_findings"] = parent["selected_findings"] + [380, 381]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
register["harness_runs"] = dict(parent["harness_runs"], k=dict(returncode=receipt["returncode"], failed=triage["failed_count"],
    child_setup_errors=child_errors, child_failed=child_failed, maestro_timeouts=timeouts, probe_spikes=probe_spikes, probe_summary=probe_summary,
    collected=2096, persistent_media_reference=True, whole_session_tmpdir_on_tmpfs=False, filesystem="ext4:/tmp",
    stall_fsync_correlation={k: correlation[k] for k in ("operations", "stalls", "spikes", "stalls_inside_window_with_spike", "spike_seconds_max")} if correlation else None))
register["ir_ml3_04"] = dict(helper_review="E-IR04-HELPER-REVIEW", verdicts=helper_review["counts"], lane_admission_proposal="E-IR04-LANE-PROPOSAL",
                             activation_approved=False, m1_admission=False, acceptance=False)
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"),
                      run_k=register["harness_runs"]["k"])))
