"""Build the parent-preserving CAPA successor for the harness and fixture repairs (findings 361–365).

Usage: python3 -I build-capa-20261020-harness-repairs.py

Parent: capa-20261019-platform-regression/register.json (43 records / 245 bindings). The successor
adds evidence IDs and records, changes states of existing records only forwards with additive
incident/evidence references (222, 357, 359, 359-CHILD), and never reuses a parent evidence ID.
Run both validators afterwards. Manual OBSERVE_ONLY; all effectiveness NOT_DEMONSTRATED.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261019-platform-regression"
OUT = BASE / "capa-20261020-harness-repairs"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa17.md"
RUNS = {k: BASE / ("platform-regression-" + v) for k, v in dict(a="20261019a", b="20261019b", c="20261020c", d="20261020d", e="20261020e").items()}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "cc1cca7748451b6ae3196e3fb40a33122ee16aa4ed5368854dd7c828898cab49"
assert len(parent["records"]) == 43 and len(parent["evidence"]) == 245
register = copy.deepcopy(parent)
now = datetime.now(timezone.utc).isoformat()
policy = parent["policy_sha256"]
records = {r["capa_id"]: r for r in register["records"]}

def span(start, end):
    text = REVIEW.read_text()
    body = text[text.index("\n" + start) + 1:text.index("\n" + end)]
    return dict(kind="review_span", path=rel(REVIEW), start=start, end=end, sha256=hashlib.sha256(body.encode()).hexdigest())

def file(path):
    path = Path(path)
    assert path.is_file() and not path.is_symlink(), path
    return dict(kind="file", path=rel(path), sha256=sha(path))

triage = {k: read(v / "failure-triage.json") for k, v in RUNS.items()}
receipt = {k: read(v / "source-receipt.json") for k, v in RUNS.items()}
failed = {k: {f["nodeid"] for f in triage[k]["failures"]} for k in RUNS}
build_nodes = {f["nodeid"] for f in triage["a"]["failures"] if f["mentions_missing_build_module"]}
assert len(build_nodes) == 13
build_remaining = {k: sorted(build_nodes & failed[k]) for k in "bcde"}
CHILD_ERRORS = 14
def child_errors(k):
    text = (RUNS[k] / "source.log").read_text()
    return sum(1 for line in text.splitlines() if line.startswith("E         ERROR tests/"))
child_error_counts = {k: child_errors(k) for k in RUNS}
assert child_error_counts["a"] == CHILD_ERRORS and child_error_counts["b"] == CHILD_ERRORS
LEAF = "tests/thesis_lite/maestro/test_active_restart.py::test_original_active_explicit_restart_and_closed_generation_universe[leaf]"
leaf_failed = {k: LEAF in failed[k] for k in RUNS}
assert leaf_failed["a"] is True
timeouts = {k: sorted(f["nodeid"] for f in triage[k]["failures"]
                      if "thesis_lite/maestro" in f["nodeid"] and any("ML-PERSIST-TIMEOUT" in l or "TEARDOWN-INCOMPLETE" in l for l in f["traceback_last_lines"]))
            for k in RUNS}

new_evidence = {
    "review:361": span("361.", "362."), "review:362": span("362.", "363."),
    "review:363": span("363.", "364."), "review:364": span("364.", "365."),
    "E-HARNESS-PLUGIN-V2": file(BASE / "maestro_receipt_namespace.py"),
    "E-HARNESS-PLUGIN-V3": file(BASE / "maestro_receipt_namespace_v3.py"),
    "E-HARNESS-ENV-C": file(BASE / "platform-environment-20261020c/preparation.json"),
    "E-HARNESS-ENV-D": file(BASE / "platform-environment-20261020d/preparation.json"),
    "E-HARNESS-C-DRIVER": file(BASE / "verify-platform-regression-20261020c.py"),
    "E-HARNESS-D-DRIVER": file(BASE / "verify-platform-regression-20261020d.py"),
    "E-HARNESS-E-DRIVER": file(BASE / "verify-platform-regression-20261020e.py"),
    "E-HARNESS-D-FIXTURE-DIFF": file(RUNS["d"] / "fixture-window-margin.diff"),
    "E-HARNESS-E-FIXTURE-DIFF": file(RUNS["e"] / "fixture-window-margin.diff"),
    "E-HARNESS-D-GC-LOG": file(RUNS["d"] / "gc-pauses.jsonl"),
    "E-HARNESS-D-FSYNC-PROBE": file(RUNS["d"] / "fsync-probe-external.jsonl"),
    "E-HARNESS-D-CORRELATION": file(RUNS["d"] / "stall-fsync-correlation.json"),
    "E-HARNESS-C-CORRELATION": file(RUNS["c"] / "stall-fsync-correlation.json"),
    "E-HARNESS-CORRELATOR": file(BASE / "correlate-stalls-fsync-20261020.py"),
    "E-HARNESS-A-LEAF-OPS": file(RUNS["a"] / "source-harness/test_active_restart/lazy-operations-test_original_active_explicit_restart_and_closed_generation_universe-leaf.json"),
}
for k in "cde":
    new_evidence["E-HARNESS-" + k.upper() + "-RECEIPT"] = file(RUNS[k] / "source-receipt.json")
    new_evidence["E-HARNESS-" + k.upper() + "-LOG"] = file(RUNS[k] / "source.log")
    new_evidence["E-HARNESS-" + k.upper() + "-TRIAGE"] = file(RUNS[k] / "failure-triage.json")
if (RUNS["e"] / "fsync-probe.jsonl").is_file():
    new_evidence["E-HARNESS-E-FSYNC-PROBE"] = file(RUNS["e"] / "fsync-probe.jsonl")
if (RUNS["e"] / "gc-pauses.jsonl").is_file():
    new_evidence["E-HARNESS-E-GC-LOG"] = file(RUNS["e"] / "gc-pauses.jsonl")
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
run_refs = lambda ks: [f"E-HARNESS-{k.upper()}-{x}" for k in ks for x in ("RECEIPT", "LOG", "TRIAGE")]

# 357: additional prevention checks in c, d, e.
r = records["ML-CAPA-357"]
r["incident_ids"] += ["review:363", "review:364"]
r["root_cause_evidence_refs"] += run_refs("cde") + ["review:363", "review:364"]
r["updated_at"] = now
register["action_plans"]["ML-CAPA-357"]["prevention"]["status"] = (
    "build_capable_environment_all13_original_build_failures_absent_in_b_c_d_e" if not any(build_remaining.values())
    else "build_failures_remaining_" + json.dumps(build_remaining))
register["action_plans"]["ML-CAPA-357"]["prevention"]["evidence_refs"] += run_refs("cde")

# 359-CHILD: receipt-namespace collision -> fix candidate.
r = records["ML-CAPA-359-CHILD"]
r["state"], r["root_cause_status"] = "FIX_CANDIDATE", "HYPOTHESIS"
r["root_cause_summary"] = ("The accepted nested platform case's child pytest inherited one shared receipt directory and ran "
    "without the per-module receipt namespace (plugins= applied to the outer session only; autoload disabled), so "
    "module-scoped fixtures collided on fixed receipt names (same mechanism as 260): identical 14 setup errors in runs "
    "a and b. Plugin v2 loaded by name through PYTEST_PLUGINS from the prepared environment gives every session, "
    "nested included, its own per-module namespace; the 14 errors are absent in runs c, d and e. Local same-session "
    "evidence; the child's own tracebacks were never retained, so the mechanism is inferred from the error set and the "
    "shared directory contents.")
r["incident_ids"] += ["review:361", "review:363", "review:364"]
r["root_cause_evidence_refs"] += ["review:358", "review:361", "review:363", "E-HARNESS-PLUGIN-V2", "E-HARNESS-ENV-C",
                                  "E-HARNESS-C-DRIVER"] + run_refs("cde")
r["reproducer_id"] = "platform-regression-20261019a/b nested child: 14 ERROR node IDs in test_composed_issuer_loss, test_composed_persistence_termination, test_runtime_issuer_loss"
r["prevention_test_id"] = "nested child error count in runs c, d, e (0 expected) with per-module nested directories present"
r["candidate_patch_sha256"] = sha(BASE / "maestro_receipt_namespace.py")
r["updated_at"] = now
register["action_plans"]["ML-CAPA-359-CHILD"] = dict(
    containment="Runs a and b retained unchanged; accepted Argus test untouched; plugin lives in the verification environment only.",
    correction=dict(status="implemented_in_verification_harness_plugin_v2_environment_c", evidence_refs=["E-HARNESS-PLUGIN-V2", "E-HARNESS-ENV-C", "E-HARNESS-C-DRIVER"]),
    prevention=dict(status="child_setup_errors_absent_in_c_d_e:" + json.dumps({k: child_error_counts[k] for k in "cde"}),
                    evidence_refs=run_refs("cde"), limits="Same-session evidence; no independent cause confirmation; child tracebacks not retained."),
    effectiveness=dict(status="NOT_DEMONSTRATED", observation_plan=None, independent_confirmation=False),
    next_action="Keep the plugin in every prepared verification environment; the child's nonrecurring failures stay with 359.")

# 222: residual-budget squeeze -> fix candidate (fixture window margin, 362/364).
r = records["ML-CAPA-222"]
r["state"], r["root_cause_status"] = "FIX_CANDIDATE", "HYPOTHESIS"
r["root_cause_summary"] = ("The shared fixture creates the admitted 4.8 s active window at configuration time, before worker init "
    "(median 0.38 s) and the first statement; the restart-capable schedule nominally spans 4.1–4.6 s after init, so "
    "ordinary jitter clips the final statements to residual budgets (34 ms in run a) and they expire with "
    "ML-PERSIST-TIMEOUT while the restart itself completed. Reserving the explicit restart/recovery budgets inside the "
    "4.8 s base window (5.8 s for test_active_restart) removes the squeeze; the leaf reproducer passed in runs d and e. "
    "Verification-fixture margin, not a product defect; local same-session evidence only.")
r["incident_ids"] += ["review:362", "review:364"]
r["root_cause_evidence_refs"] += ["review:359", "review:362", "review:364", "E-HARNESS-A-LEAF-OPS", "E-HARNESS-E-FIXTURE-DIFF"] + run_refs("de")
r["prevention_test_id"] = LEAF + " in runs d and e"
r["candidate_patch_sha256"] = sha(RUNS["e"] / "fixture-window-margin.diff")
r["updated_at"] = now
plan = register["action_plans"]["ML-CAPA-222"]
plan["correction"] = dict(status="implemented_in_shared_fixture_window_margin", evidence_refs=["E-HARNESS-E-FIXTURE-DIFF", "review:362", "review:364"])
plan["prevention"] = dict(status="leaf_reproducer_passed_in_d_and_e:" + json.dumps({k: (not leaf_failed[k]) for k in "de"}),
                          evidence_refs=run_refs("de"), limits="Fixture-level; no independent confirmation; the 4.8 s base window without restarts keeps its original margin.")
plan["next_action"] = "Observe the restart module across future full runs; do not widen other literal windows without their own evidence."

# 359: outer first-RPC expiries remain UNKNOWN; add observations.
r = records["ML-CAPA-359"]
r["incident_ids"] += ["review:363", "review:364"]
r["root_cause_evidence_refs"] += ["review:362", "review:363", "review:364", "E-HARNESS-D-GC-LOG", "E-HARNESS-D-FSYNC-PROBE",
                                  "E-HARNESS-D-CORRELATION", "E-HARNESS-C-CORRELATION", "E-HARNESS-CORRELATOR"] + run_refs("cde")
r["updated_at"] = now
register["action_plans"]["ML-CAPA-359"]["next_action"] = (
    "GC pauses refuted (max 0.064 s). fsync: one 1.04 s spike overlapped a 0.74 s init stall in d; 9 spikes/55 min, worst 1.11 s on the shared ext4 root. "
    "Harness mitigation (tmpfs basetemp) is tracked as 364; product budgets unchanged. Timeouts per run: " + json.dumps({k: len(timeouts[k]) for k in RUNS}))

# 364: fsync-stall mitigation candidate (harness only).
e_spikes = 0
if (RUNS["e"] / "fsync-probe.jsonl").is_file():
    e_spikes = sum(1 for line in (RUNS["e"] / "fsync-probe.jsonl").read_text().splitlines() if '"fsync_seconds"' in line)
records["ML-CAPA-364"] = dict(schema_version="1.0", capa_id="ML-CAPA-364", incident_ids=["review:362", "review:364"],
    state="FIX_CANDIDATE", root_cause_status="HYPOTHESIS",
    root_cause_summary=("Rare 0.5–1.4 s stalls occur only on durable-write operations (journal appends fsync file and directory) while "
        "non-writing operations never exceed a few ms; the shared 90%-full ext4 root carries other sessions' write load; an "
        "external probe measured 9 fsync spikes >150 ms in 55 min (worst 1.11 s) and one 1.04 s spike overlapped a stall. GC "
        "pauses are refuted. Mitigation candidate: private basetemp on tmpfs for the verification harness, declared as a "
        "fidelity change (persistent-media fsync latency not represented). Temporal association only; no causal proof."),
    root_cause_evidence_refs=["review:362", "review:364", "E-HARNESS-D-FSYNC-PROBE", "E-HARNESS-D-CORRELATION", "E-HARNESS-D-GC-LOG",
                              "E-HARNESS-E-DRIVER"] + run_refs("e"),
    reproducer_id="platform-regression-20261020d stall-fsync-correlation.json: init 0.740 s with fsync spike 1.0365 s at offset -0.342 s",
    prevention_test_id="platform-regression-20261020e (tmpfs basetemp): Maestro first-RPC expiry count and in-driver probe spikes",
    candidate_patch_sha256=sha(BASE / "verify-platform-regression-20261020e.py"),
    affected_versions=["verification drivers a–d with private basetemp on the ext4 root"], lesson_ids=[],
    observation_window_end=None, created_at=now, updated_at=now, policy_sha256=policy)
register["records"].append(records["ML-CAPA-364"])
register["action_plans"]["ML-CAPA-364"] = dict(
    containment="Product durability logic and all statement budgets unchanged; runs a–d retained.",
    correction=dict(status="implemented_in_verification_driver_e_tmpfs_basetemp", evidence_refs=["E-HARNESS-E-DRIVER"] + run_refs("e")),
    prevention=dict(status="run_e_timeouts_" + str(len(timeouts["e"])) + "_probe_spikes_" + str(e_spikes), evidence_refs=run_refs("e"),
                    limits="One run; a single clean run does not establish the stall class is closed; fidelity declared, not equivalent to persistent media."),
    effectiveness=dict(status="NOT_DEMONSTRATED", observation_plan=None, independent_confirmation=False),
    next_action="Observe across subsequent full runs on tmpfs; keep an ext4 reference probe to track the host condition.")

register["selected_findings"] = parent["selected_findings"] + [361, 362, 363, 364]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
register["harness_runs"] = {k: dict(returncode=receipt[k]["returncode"], failed=triage[k]["failed_count"],
                                    child_setup_errors=child_error_counts[k], maestro_timeouts=timeouts[k],
                                    build_failures_remaining=build_remaining.get(k)) for k in RUNS}
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"),
                      harness_runs=register["harness_runs"])))
