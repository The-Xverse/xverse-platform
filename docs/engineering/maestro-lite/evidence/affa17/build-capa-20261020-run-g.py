"""Build the parent-preserving CAPA successor adding run g as a REJECTED correction attempt (finding 367).

Usage: python3 -I build-capa-20261020-run-f.py

Parent: capa-20261020-harness-repairs/register.json (44 records / 275 bindings). Additive only:
new evidence IDs for run f (receipt, log, triage, probe, GC log) and the finding-366 review span;
incident/evidence references appended to 357, 359-CHILD, 222 and 364; prevention statuses updated
from run f's actual outcome; no state is advanced beyond FIX_CANDIDATE and no effectiveness is claimed.
Run both validators afterwards.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261020-run-f"
OUT = BASE / "capa-20261020-run-g"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa17.md"
RUN_F = BASE / "platform-regression-20261020g"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "07e1051c606dee6667bdb16282ee28590d88b817cd2b0230bfb9912c3199ac23"
assert len(parent["records"]) == 44 and len(parent["evidence"]) == 284
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

receipt = read(RUN_F / "source-receipt.json")
triage = read(RUN_F / "failure-triage.json")
failed = {f["nodeid"] for f in triage["failures"]}
build_nodes_absent = not any("No module named build" in "\n".join(f["traceback_last_lines"]) for f in triage["failures"])
child_errors = sum(1 for line in (RUN_F / "source.log").read_text().splitlines() if line.startswith("E         ERROR tests/"))
LEAF = "tests/thesis_lite/maestro/test_active_restart.py::test_original_active_explicit_restart_and_closed_generation_universe[leaf]"
timeouts = sorted(f["nodeid"] for f in triage["failures"] if "thesis_lite/maestro" in f["nodeid"]
                  and any("ML-PERSIST-TIMEOUT" in l or "TEARDOWN-INCOMPLETE" in l or "TERMINAL-INCOMPLETE" in l for l in f["traceback_last_lines"]))
probe_rows = [json.loads(l) for l in (RUN_F / "fsync-probe.jsonl").read_text().splitlines()] if (RUN_F / "fsync-probe.jsonl").is_file() else []
probe_summary = next((r for r in probe_rows if r.get("summary")), None)
probe_spikes = sum(1 for r in probe_rows if "fsync_seconds" in r and not r.get("summary"))

new_evidence = {"review:366": span("366.", "367."), "review:367": span("367.", "368.") if "\n368." in REVIEW.read_text() else None}
new_evidence = {k: v for k, v in new_evidence.items() if v}
for name, path in (("RECEIPT", "source-receipt.json"), ("LOG", "source.log"), ("TRIAGE", "failure-triage.json"),
                   ("FSYNC-PROBE", "fsync-probe.jsonl"), ("GC-LOG", "gc-pauses.jsonl"), ("FIXTURE-DIFF", "fixture-window-margin.diff"),
                   ("CONFIG", "configuration.json")):
    if (RUN_F / path).is_file():
        new_evidence["E-HARNESS-G-" + name] = file(RUN_F / path)
new_evidence["E-HARNESS-G-DRIVER"] = file(BASE / "verify-platform-regression-20261020g.py")
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
f_refs = [k for k in new_evidence if k.startswith("E-HARNESS-G-")] + [k for k in new_evidence if k.startswith("review:")]

records["ML-CAPA-366"] = dict(schema_version="1.0", capa_id="ML-CAPA-366", incident_ids=["review:366", "review:367"],
    state="REJECTED", root_cause_status="HYPOTHESIS",
    root_cause_summary=("Transitive fixture terminal statements run at p99 usage 0.74 of their 0.3 s operation budget (finding 366). "
        "The attempted correction (operation_seconds .3 -> .5) is rejected at schedule admission by the health-capacity "
        "invariant period = cadence - n*op - (service_calls+1)*op > n*op (schedule_plan.py:152): 24 transitive cases fail "
        "at construction in run g. The 0.3 s budget is forced by the 5 s probe cadence with 4 units; any margin change must "
        "redesign cadence and scan counts together. Reverted; proposal only."),
    root_cause_evidence_refs=f_refs + ["review:366"], reproducer_id="platform-regression-20261020g: 24 ML-SCHEDULE-HEALTH-CAPACITY at admit_schedule",
    prevention_test_id=None, candidate_patch_sha256=sha(RUN_F / "fixture-window-margin.diff"),
    affected_versions=["run g snapshot only; reverted before run h"], lesson_ids=[], observation_window_end=None,
    created_at=now, updated_at=now, policy_sha256=parent["policy_sha256"])
register["records"].append(records["ML-CAPA-366"])
register["action_plans"]["ML-CAPA-366"] = dict(
    containment="Edit reverted to the admitted 0.3 s; run g retained as rejected-correction evidence; runs a-f unaffected.",
    correction=dict(status="rejected_by_schedule_admission_invariant", evidence_refs=f_refs),
    prevention=dict(status="none", evidence_refs=[], limits="Margin observation stands; a cadence/scan redesign would change asserted health-scan counts and needs its own finding."),
    effectiveness=dict(status="NOT_DEMONSTRATED", observation_plan=None, independent_confirmation=False),
    next_action="Observe the transitive modules across runs h+; if expiries recur, propose cadence>=8 s with 0.5 s budgets as a reviewed fixture redesign.")
r = records["ML-CAPA-364"]
r["incident_ids"] += ["review:367"]; r["root_cause_evidence_refs"] += f_refs; r["updated_at"] = now
register["action_plans"]["ML-CAPA-364"]["prevention"]["status"] += "; run_g_probe_terminal_samples_" + str(probe_summary["samples"] if probe_summary else 0) + "_spikes_" + str(probe_spikes)
register["action_plans"]["ML-CAPA-364"]["prevention"]["evidence_refs"] += f_refs
register["selected_findings"] = parent["selected_findings"] + [366, 367]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
register["harness_runs"] = dict(parent["harness_runs"], g=dict(returncode=receipt["returncode"], failed=triage["failed_count"],
    child_setup_errors=child_errors, maestro_timeouts=timeouts, probe_spikes=probe_spikes, probe_summary=probe_summary,
    collected=2094, whole_session_tmpdir_on_tmpfs=True, correction_rejected_at_admission=True))
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"),
                      run_g=register["harness_runs"]["g"])))
