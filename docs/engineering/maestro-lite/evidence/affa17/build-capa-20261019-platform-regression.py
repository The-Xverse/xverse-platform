"""Build the parent-preserving CAPA successor for the broader platform regression (findings 357/359).

Usage: python3 -I build-capa-20261019-platform-regression.py

Parent: capa-20261019-reviewer-shape/register.json (40 records / 216 bindings). The successor
copies the parent byte-for-byte in content, then only adds evidence IDs and records, and
appends incident/evidence references to existing records 222 and 318 (recurrences). No parent
evidence ID is reused with a new meaning; no old record identity changes. Run both validators
afterwards: verify-capa-register-20261019.py <folder> and
check-capa-parent-preservation-20261019.py <folder>/register.json <folder>/parent-preservation.json.
Manual OBSERVE_ONLY; no automatic CAPA engine, no effectiveness demonstration, no acceptance.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261019-reviewer-shape"
OUT = BASE / "capa-20261019-platform-regression"
RUN_A = BASE / "platform-regression-20261019a"
RUN_B = BASE / "platform-regression-20261019b"
ENV = BASE / "platform-environment-20261019b"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa17.md"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(p.resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "c04badb5049ce92802384d6992e0266da3a9075ed348fa031eb5ad9ff4f5a1b3"
assert len(parent["records"]) == 40 and len(parent["evidence"]) == 216
register = copy.deepcopy(parent)
now = datetime.now(timezone.utc).isoformat()
policy = parent["policy_sha256"]

def span(start, end):
    text = REVIEW.read_text()
    body = text[text.index("\n" + start) + 1:text.index("\n" + end)]
    return dict(kind="review_span", path=rel(REVIEW), start=start, end=end,
                sha256=hashlib.sha256(body.encode()).hexdigest())

def file(path):
    path = Path(path)
    assert path.is_file() and not path.is_symlink(), path
    return dict(kind="file", path=rel(path), sha256=sha(path))

receipt_a = read(RUN_A / "source-receipt.json")
triage_a = read(RUN_A / "failure-triage.json")
receipt_b = read(RUN_B / "source-receipt.json")
triage_b = read(RUN_B / "failure-triage.json")
assert receipt_a["returncode"] == 1 and not receipt_a["outer_timeout"] and not receipt_a["changed_frozen_inputs"]
assert triage_a["failed_count"] == 17 and triage_a["error_count"] == 0
assert not receipt_b["outer_timeout"] and not receipt_b["changed_frozen_inputs"]
build_nodes_a = {f["nodeid"] for f in triage_a["failures"] if f["mentions_missing_build_module"]}
assert len(build_nodes_a) == 13
failed_b = {f["nodeid"] for f in triage_b["failures"]}
build_failures_remaining_in_b = sorted(build_nodes_a & failed_b)
build_signature_in_b = [f["nodeid"] for f in triage_b["failures"] if f["mentions_missing_build_module"]]

new_evidence = {
    "review:357": span("357.", "358."),
    "review:358": span("358.", "359."),
    "review:359": span("359.", "360."),
    "E-PLATFORM-A-DRIVER": file(BASE / "verify-platform-regression-20261019a.py"),
    "E-PLATFORM-A-RECEIPT": file(RUN_A / "source-receipt.json"),
    "E-PLATFORM-A-LOG": file(RUN_A / "source.log"),
    "E-PLATFORM-A-TRIAGE": file(RUN_A / "failure-triage.json"),
    "E-PLATFORM-A-CONFIG": file(RUN_A / "configuration.json"),
    "E-PLATFORM-TRIAGE-TOOL": file(BASE / "triage-platform-regression-20261019a.py"),
    "E-PLATFORM-HANDOVER-TRIAGE": file(BASE / "claude-handover-20261019/failure-triage.json"),
    "E-PLATFORM-ORIGINAL-BUILD-CHECK": file(BASE / "claude-handover-20261019/original-python-build-check.log"),
    "E-PLATFORM-ENV-PREPARATION": file(ENV / "preparation.json"),
    "E-PLATFORM-ENV-PIP-LIST": file(ENV / "pip-list.log"),
    "E-PLATFORM-ENV-BUILDER": file(BASE / "prepare-platform-environment-20261019b.py"),
    "E-PLATFORM-B-DRIVER": file(BASE / "verify-platform-regression-20261019b.py"),
    "E-PLATFORM-B-PREFLIGHT": file(RUN_B / "preflight.json"),
    "E-PLATFORM-B-CONFIG": file(RUN_B / "configuration.json"),
    "E-PLATFORM-B-RECEIPT": file(RUN_B / "source-receipt.json"),
    "E-PLATFORM-B-LOG": file(RUN_B / "source.log"),
    "E-PLATFORM-B-TRIAGE": file(RUN_B / "failure-triage.json"),
    "E-PLATFORM-A-RESTART-LEAF": file(RUN_A / "source-harness/test_active_restart/active-restart-leaf.json"),
    "E-PLATFORM-A-RESTART-LEAF-OPS": file(RUN_A / "source-harness/test_active_restart/lazy-operations-test_original_active_explicit_restart_and_closed_generation_universe-leaf.json"),
    "E-PLATFORM-A-CONTROL-BEYOND": file(RUN_A / "source-harness/test_active_control_deadlines/control-deadline-recovery-beyond-active.json"),
    "E-PLATFORM-A-CONTROL-BEYOND-OPS": file(RUN_A / "source-harness/test_active_control_deadlines/lazy-operations-test_original_control_rejection_keeps_unspent_authority-beyond-active-recovery.json"),
    "E-PLATFORM-A-STREAM-SEEDED": file(RUN_A / "source-harness/test_native_writer_stream_faults/stream-result-seeded-flush-persistent.json"),
    "E-PLATFORM-A-STREAM-SEEDED-OPS": file(RUN_A / "source-harness/test_native_writer_stream_faults/lazy-operations-test_native_stream_fault_preserves_public_writer_and_original_cleanup-seeded-flush-persistent.json"),
    "E-PLATFORM-A-CHILD-SHARED-HEARTBEAT": file(RUN_A / "source-harness/test_argus2_integration/heartbeat-compiler.json"),
    "E-PLATFORM-B-COHORT-CLEANED-LEAF": file(RUN_B / "source-harness/test_active_transitive_restart/cohort-cleaned-leaf.json"),
    "E-PLATFORM-B-COHORT-CLEANED-LEAF-OPS": file(RUN_B / "source-harness/test_active_transitive_restart/lazy-operations-test_original_transitive_cohort_retains_unrelated_and_all_generations-cleaned-leaf.json"),
}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)

refs_357 = ["review:357", "review:359", "E-PLATFORM-ORIGINAL-BUILD-CHECK", "E-PLATFORM-HANDOVER-TRIAGE",
            "E-PLATFORM-A-RECEIPT", "E-PLATFORM-A-LOG", "E-PLATFORM-A-TRIAGE", "E-PLATFORM-TRIAGE-TOOL",
            "E-PLATFORM-A-DRIVER", "E-PLATFORM-A-CONFIG"]
refs_357_fix = ["E-PLATFORM-ENV-BUILDER", "E-PLATFORM-ENV-PREPARATION", "E-PLATFORM-ENV-PIP-LIST",
                "E-PLATFORM-B-DRIVER", "E-PLATFORM-B-PREFLIGHT", "E-PLATFORM-B-CONFIG",
                "E-PLATFORM-B-RECEIPT", "E-PLATFORM-B-LOG", "E-PLATFORM-B-TRIAGE"]
refs_359_outer = ["review:359", "E-PLATFORM-A-RECEIPT", "E-PLATFORM-A-LOG", "E-PLATFORM-A-TRIAGE",
                  "E-PLATFORM-A-RESTART-LEAF", "E-PLATFORM-A-RESTART-LEAF-OPS", "E-PLATFORM-A-CONTROL-BEYOND",
                  "E-PLATFORM-A-CONTROL-BEYOND-OPS", "E-PLATFORM-A-STREAM-SEEDED", "E-PLATFORM-A-STREAM-SEEDED-OPS",
                  "E-PLATFORM-B-RECEIPT", "E-PLATFORM-B-TRIAGE", "E-PLATFORM-B-LOG",
                  "E-PLATFORM-B-COHORT-CLEANED-LEAF", "E-PLATFORM-B-COHORT-CLEANED-LEAF-OPS"]
refs_359_child = ["review:358", "review:359", "E-PLATFORM-A-LOG", "E-PLATFORM-A-TRIAGE", "E-PLATFORM-B-LOG",
                  "E-PLATFORM-A-CHILD-SHARED-HEARTBEAT", "E-PLATFORM-B-RECEIPT", "E-PLATFORM-B-TRIAGE"]

prevention_357 = ("successor_b_build_capable_environment_" +
                  ("all13_original_build_failures_absent" if not build_failures_remaining_in_b else
                   "build_failures_remaining_" + str(len(build_failures_remaining_in_b))))
records = [
    dict(schema_version="1.0", capa_id="ML-CAPA-357", incident_ids=["review:357", "review:359"],
         state="FIX_CANDIDATE", root_cause_status="HYPOTHESIS",
         root_cause_summary=("Verification driver a selected a Python environment without build/hatchling, while "
                             "Argus support.wheel_and_target() invokes sys.executable -m build --no-isolation; 13 "
                             "original Argus packaging/installed-wheel cases fail with the exact 'No module named "
                             "build' traceback. Successor b runs the identical 1903-file snapshot in a separately "
                             "prepared, preflight-bound build-capable environment. Verification-environment "
                             "omission; accepted Argus and product code unchanged. Same-session local support."),
         root_cause_evidence_refs=refs_357 + refs_357_fix,
         reproducer_id="platform-regression-20261019a: 13 Argus wheel_and_target cases (consumer_unit 9, integration 2, validation 2)",
         prevention_test_id="platform-regression-20261019b preflight.json plus the same 13 node IDs in its terminal receipt/triage",
         candidate_patch_sha256=sha(BASE / "verify-platform-regression-20261019b.py"),
         affected_versions=["verify-platform-regression-20261019a.py with /tmp/maestro-lite-integrated-maestro-target-20261019b"],
         lesson_ids=[], observation_window_end=None, created_at=now, updated_at=now, policy_sha256=policy),
    dict(schema_version="1.0", capa_id="ML-CAPA-359", incident_ids=["review:359"],
         state="UNRESOLVED", root_cause_status="UNKNOWN", root_cause_summary=None,
         root_cause_evidence_refs=refs_359_outer,
         reproducer_id=("platform-regression-20261019a outer session: test_original_control_rejection_keeps_unspent_authority"
                        "[beyond-active-recovery], test_original_active_explicit_restart_and_closed_generation_universe[leaf], "
                        "test_native_stream_fault_preserves_public_writer_and_original_cleanup[seeded-flush-persistent]; all "
                        "ML-PERSIST-TIMEOUT, health_scans=0, lease_renewals=2. Run b outer session: "
                        "test_original_transitive_cohort_retains_unrelated_and_all_generations[cleaned-leaf] "
                        "(ML-SCHEDULE-TEARDOWN-INCOMPLETE after teardown ML-PERSIST-TIMEOUT) and "
                        "test_full_five_phase_dispatch_records_actual_outcomes_and_dispositions (ML-PERSIST-TIMEOUT); none recurred across a/b"),
         prevention_test_id=None, candidate_patch_sha256=None,
         affected_versions=["exact platform-regression-20261019a frozen snapshot (identical 273 Maestro inputs passed 1501/1501 twice earlier)"],
         lesson_ids=[], observation_window_end=None, created_at=now, updated_at=now, policy_sha256=policy),
    dict(schema_version="1.0", capa_id="ML-CAPA-359-CHILD", incident_ids=["review:359"],
         state="UNRESOLVED", root_cause_status="UNKNOWN", root_cause_summary=None,
         root_cause_evidence_refs=refs_359_child,
         reproducer_id=("test_existing_platform_pytest_regression_unchanged_in_assembled_target child pytest 1678188: "
                        "12 failed/1770 passed/14 errors; only the last 4000 stdout characters are retained"),
         prevention_test_id=None, candidate_patch_sha256=None,
         affected_versions=["platform-regression-20261019a nested child (12 failed/1770 passed/14 errors)",
                            "platform-regression-20261019b nested child (0 failed/1782 passed/identical 14 error node IDs); shared inherited receipt directory without per-module namespace (hypothesis, findings 358/359/360)"],
         lesson_ids=[], observation_window_end=None, created_at=now, updated_at=now, policy_sha256=policy),
]
for row in records:
    assert row["capa_id"] not in {r["capa_id"] for r in register["records"]}
    register["records"].append(row)

# Recurrences of existing unresolved records: additive incident/evidence references only.
for capa_id in ("ML-CAPA-222", "ML-CAPA-318"):
    row = next(r for r in register["records"] if r["capa_id"] == capa_id)
    assert row["state"] == "UNRESOLVED" and row["root_cause_status"] == "UNKNOWN"
    row["incident_ids"] = row["incident_ids"] + ["review:359"]
    row["root_cause_evidence_refs"] = row["root_cause_evidence_refs"] + ["review:359", "E-PLATFORM-A-TRIAGE", "E-PLATFORM-A-RECEIPT"]
    row["updated_at"] = now
    register["action_plans"][capa_id]["next_action"] = (
        register["action_plans"][capa_id]["next_action"] +
        " Recurred in platform-regression-20261019a (finding 359); still UNKNOWN, no cause inferred.")

register["action_plans"]["ML-CAPA-357"] = dict(
    containment="Original run a and its environment are retained unchanged; no tool was installed into the live environment; no accepted Argus test was skipped or modified.",
    correction=dict(status="implemented_in_successor_verification_driver_and_separate_environment", evidence_refs=refs_357_fix),
    prevention=dict(status=prevention_357, evidence_refs=refs_357 + refs_357_fix,
                    limits="Same-session evidence; environment identity differs from original b (packaging 26.3, pluggy 1.7.0); no independent cause confirmation or effectiveness observation."),
    effectiveness=dict(status="NOT_DEMONSTRATED", observation_plan=None, independent_confirmation=False),
    next_action="Add build-tool preflight to every future packaging-dependent driver; keep run a evidence; continue full 024 scope.")
register["action_plans"]["ML-CAPA-359"] = dict(
    containment="Original failed receipts, operation timelines and log retained; no retry for luck; no deadline change; no product change.",
    correction=dict(status="none", evidence_refs=[]),
    prevention=dict(status="none", evidence_refs=[], limits="Cause unknown; successor b result is a separate observation, not an explanation."),
    effectiveness=dict(status="NOT_DEMONSTRATED", observation_plan=None, independent_confirmation=False),
    next_action="Compare operation timelines across a, b and the earlier 1501/1501 phases before any hypothesis; relate to 222/287/318/330 only with evidence.")
register["action_plans"]["ML-CAPA-359-CHILD"] = dict(
    containment="Child output beyond the retained 4000-character tail is lost by the accepted test; shared receipt directory retained as-is.",
    correction=dict(status="none", evidence_refs=[]),
    prevention=dict(status="none", evidence_refs=[], limits="Receipt-namespace collision is a hypothesis with local file evidence only; a harness successor with its own finding is required before any claim."),
    effectiveness=dict(status="NOT_DEMONSTRATED", observation_plan=None, independent_confirmation=False),
    next_action="Decide a separate harness successor that gives the nested child a per-module receipt namespace without touching accepted tests; retain run a/b child outcomes.")
register["selected_findings"] = parent["selected_findings"] + [357, 359]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
register["successor_run_b"] = dict(returncode=receipt_b["returncode"], passed_exit_status=receipt_b["passed_exit_status"],
    failed=triage_b["failed_count"], errors=triage_b["error_count"],
    build_signature_failures_in_b=build_signature_in_b, original_build_failures_remaining_in_b=build_failures_remaining_in_b,
    failures_in_b=sorted(failed_b))
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
    register_sha256=sha(OUT / "register.json"), prevention_357=prevention_357,
    build_failures_remaining_in_b=build_failures_remaining_in_b, failures_in_b=sorted(failed_b))))
