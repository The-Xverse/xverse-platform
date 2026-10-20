"""Bind both completed original Maestro phases without closing wider gates."""
from pathlib import Path
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
OUT = BASE / "integrated-maestro-20261019b"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
ref = lambda p: dict(path=str(p.relative_to(ROOT)), sha256=sha(p))
manifest = read(OUT / "frozen-inputs.json")
assert len(manifest) == 273 and all(sha(ROOT / n) == h for n, h in manifest.items())
assert read(OUT / "result-after-wheel.json")["full_maestro_regression_passed"]
phases = {}
for phase in ("source", "wheel"):
    label = "maestro_full-" + phase
    receipt_path = OUT / (label + "-receipt.json")
    audit_path = OUT / (label + "-terminal-audit/audit.json")
    receipt, audit = read(receipt_path), read(audit_path)
    assert receipt["returncode"] == audit["original_returncode"] == 0
    assert not receipt["outer_timeout"] and audit["terminal_receipt_sha256"] == sha(receipt_path)
    assert audit["observed_counts"] == dict(passed=1501, failed=0, skipped=0, errors=0, xfailed=0, xpassed=0)
    assert sha(OUT / (label + ".log")) == receipt["log_sha256"]
    assert not audit["receipt_parse_errors"] and audit["all_recorded_roots_removed_and_workers_reaped"]
    for item in audit["receipt_inventory"] + audit["public_projections"]:
        assert sha(OUT / item["path"]) == item["sha256"]
    for item in audit["root_reservations"]:
        assert item["recorded_removed"] and item["recorded_workers_reaped"] and item["actual_path_absent"]
    phases[phase] = dict(receipt=ref(receipt_path), audit=ref(audit_path), counts=audit["observed_counts"],
        original_pid=receipt["original_pid"], elapsed_seconds=receipt["elapsed_seconds"],
        retained_files=len(audit["receipt_inventory"]), owned_roots_absent=len(audit["root_reservations"]),
        public_projections=len(audit["public_projections"]), source_links=audit["source_links"],
        explicit_reader_reference_gaps=audit["projection_reader_gaps"],
        closed_recomputations={str(value): sum(r.get("complete") is value for r in audit["original_input_closed_recomputations"])
                               for value in (True, False, None)})
folder = BASE / "capa-20261019-reviewer-shape"
capa, validation, preservation = [read(folder / n) for n in ("register.json", "verification-recheck.json", "parent-preservation.json")]
assert len(capa["records"]) == 40 and len(capa["evidence"]) == 216
assert validation["register_sha256"] == preservation["register_sha256"] == sha(folder / "register.json")
assert preservation["parent_preserved"] and preservation["parent_evidence_bindings_checked"] == 210
proposal = Path("/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/review/source-parent-semantics-proposal-20261019-v2/proposal.json")
assert sha(proposal) == "0183f57a7977a3d7ce4021e06ea0dfe56293552a66d910474224a16ce6960caf"
result = dict(schema_version=1, checkpoint="complete_current_maestro_source_and_wheel_regression",
    builder_sha256=sha(Path(__file__)), original_driver_exec_session=97867, phases=phases,
    frozen_inputs=ref(OUT / "frozen-inputs.json"), frozen_files=273, packaged_python_c_files=81,
    source_phase_checkpoint=ref(OUT / "source-phase-checkpoint.json"),
    scoped_writer_table_review=ref(OUT / "source-writer-table-review.json"),
    partial_requirement_trace=ref(BASE / "runtime-disposal-partial-traceability.json"),
    capa_register=ref(folder / "register.json"), capa_validation=ref(folder / "verification-recheck.json"),
    capa_parent_preservation=ref(folder / "parent-preservation.json"),
    source_parent_projection=dict(path=str(proposal), sha256=sha(proposal), author_approval_recorded=False),
    historical_timeout_causes_unknown=[135, 222, 286, 287, 318, 324, 330, 331, 332, 337],
    preserved_obligations=dict(software_requirements=24, source_parents=18, scenario_pairs=30,
        declared_endpoints=90, full_runtime_cases=9, full_P3_tasks=7),
    full_maestro_regression_passed=True, whole_platform_regression=False,
    full_runtime_cases_complete=False, actual_M1_admissions=0, independent_complete_review=False,
    CAPA_effectiveness_demonstrated=False, stable_increment17=False, accepted=False, merged=False,
    canonical_note_edited=False, scientific_result=False)
with (OUT / "terminal-checkpoint.json").open("x") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(checkpoint_sha256=sha(OUT / "terminal-checkpoint.json"),
    passing_executions=3002, roots_absent=sum(r["owned_roots_absent"] for r in phases.values()),
    source_links=sum(r["source_links"] for r in phases.values()),
    explicit_gaps=sum(r["explicit_reader_reference_gaps"] for r in phases.values()))))
