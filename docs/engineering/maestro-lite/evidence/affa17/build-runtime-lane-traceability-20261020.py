"""Partial bidirectional trace for the runtime lane: nine identifiers, their requirements, their evidence.

Usage: python3 -I build-runtime-lane-traceability-20261020.py

Parent trace: runtime-disposal-partial-traceability.json (inherited statuses unchanged). This record
adds the lane allocation (process_lane_case_ids on ML-SR-009/010/011/012/013/024 per the historical
verification plan) and binds it to runtime-lane-20261020a/receipt.json. It is a partial trace: the
IR-ML3-04 activation prerequisites, M1 admission, the full crash-point matrices and acceptance remain open.
"""
from pathlib import Path
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT = BASE / "runtime-disposal-partial-traceability.json"
LANE = BASE / "runtime-lane-20261020a"
OUT = BASE / "runtime-lane-partial-traceability.json"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())

parent = read(PARENT)
receipt = read(LANE / "receipt.json")
configuration = read(LANE / "configuration.json")
CASES = ("test_affa", "test_trusted_launcher", "test_prbc", "test_bounded_bootstrap",
         "test_atomic_release_cancel_stage", "test_lease_loss", "test_pre_handle_crash_survival",
         "test_residual_membership", "test_unrelated_sentinel")
LANE_MODULE = "tests/thesis_lite/maestro/test_runtime_actual.py"
COMPOSED_MODULE = "tests/thesis_lite/maestro/test_composed_authority_interruptions.py"
allocation = {
    "test_affa": (LANE_MODULE, ["ML-SR-010", "ML-SR-011", "ML-SR-012"]),
    "test_trusted_launcher": (LANE_MODULE, ["ML-SR-010", "ML-SR-012"]),
    "test_prbc": (LANE_MODULE, ["ML-SR-010", "ML-SR-012", "ML-SR-013"]),
    "test_bounded_bootstrap": (LANE_MODULE, ["ML-SR-009", "ML-SR-024"]),
    "test_atomic_release_cancel_stage": (COMPOSED_MODULE, ["ML-SR-010", "ML-SR-011"]),
    "test_lease_loss": (LANE_MODULE, ["ML-SR-009", "ML-SR-010"]),
    "test_pre_handle_crash_survival": (COMPOSED_MODULE, ["ML-SR-012", "ML-SR-013"]),
    "test_residual_membership": (LANE_MODULE, ["ML-SR-012", "ML-SR-013"]),
    "test_unrelated_sentinel": (LANE_MODULE, ["ML-SR-013"]),
}
phases = {row["phase"]: row for row in receipt["phases"]}
receipts_present = {phase: sorted(set(phases[phase]["receipts"])) for phase in phases}
lane_receipts_expected = sorted("runtime-actual-" + c + ".json" for c, (m, _) in allocation.items() if m == LANE_MODULE)
requirements = {}
for case, (module, ids) in allocation.items():
    for rid in ids:
        requirements.setdefault(rid, []).append(module + "::" + case)
rows = []
for item in parent["requirements"]:
    row = dict(item)
    if item["id"] in requirements:
        row = dict(item, component_deltas=item.get("component_deltas", []) + [dict(
            revision="ML3-AFFA17-2026-10-20-runtime-lane-v1", lane_cases=requirements[item["id"]],
            evidence="runtime-lane-20261020a/receipt.json", status="process_lane_cases_exercised_in_component_harness",
            full_requirement_closure=False)])
    rows.append(row)
record = dict(schema_version=1, revision="ML3-AFFA17-2026-10-20-runtime-lane-v1",
    parent_trace=dict(path=PARENT.name, sha256=sha(PARENT)),
    requirements=rows,
    source_parent_register=parent["source_parent_register"],
    runtime_cases={case: dict(module=module, requirements=ids,
                              receipt_file=("runtime-actual-" + case + ".json") if module == LANE_MODULE else "composed-authority-<fixture>.json")
                   for case, (module, ids) in allocation.items()},
    reverse_endpoint_requirements={**parent["reverse_endpoint_requirements"],
        **{LANE_MODULE + "::" + c: ids for c, (m, ids) in allocation.items() if m == LANE_MODULE}},
    evidence=[dict(path="runtime-lane-20261020a/receipt.json", sha256=sha(LANE / "receipt.json")),
              dict(path="runtime-lane-20261020a/configuration.json", sha256=sha(LANE / "configuration.json")),
              *[dict(path="runtime-lane-20261020a/" + p + ".log", sha256=sha(LANE / (p + ".log"))) for p in phases]],
    lane_documentation=dict(path="docs/engineering/maestro-lite/runtime-lane.md", sha256=sha(ROOT / "docs/engineering/maestro-lite/runtime-lane.md")),
    lane_module_sha256=configuration["module_sha256"][LANE_MODULE],
    composed_module_sha256=configuration["module_sha256"][COMPOSED_MODULE],
    phase_results={p: dict(returncode=phases[p]["returncode"], summary=phases[p]["summary"]) for p in phases},
    lane_receipts_expected=lane_receipts_expected,
    lane_receipts_present_per_phase=receipts_present,
    all_lane_receipts_present=all(set(lane_receipts_expected) <= set(v) for v in receipts_present.values()),
    lane_passed_both_phases=receipt["passed"],
    source_parents_retained=parent["source_parents_retained"], scenario_pairs_retained=parent["scenario_pairs_retained"],
    endpoint_obligations_retained=parent["endpoint_obligations_retained"], full_runtime_cases_retained=9,
    nine_identifiers_implemented=True, nine_identifiers_exercised_with_real_children=receipt["passed"],
    open_findings=parent["open_findings"] + [359, 364],
    authority_limits=dict(parent["authority_limits"], ir_ml3_04_activation_prerequisites_met=False,
                          runtime_case_receipts_bound_into_admission=False, crash_point_matrices_complete=False))
with OUT.open("x") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(output=str(OUT.relative_to(ROOT)), sha256=sha(OUT), lane_passed_both_phases=record["lane_passed_both_phases"],
                      all_lane_receipts_present=record["all_lane_receipts_present"], phase_results=record["phase_results"])))
