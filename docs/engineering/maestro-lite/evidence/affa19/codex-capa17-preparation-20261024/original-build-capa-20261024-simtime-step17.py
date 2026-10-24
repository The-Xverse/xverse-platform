"""Prospective additive CAPA17 builder; guarded by actual clean run and accepted DV12 evidence."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,subprocess,sys
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[4]
PARENT=BASE/"capa-20261024-c1-config-bound-step16/register.json"
PARENT_SHA="bf39b0875a3f1606a2027718c570f5b17846065bf70b2d9aead382c408ae2ad8"
TESTED="4bedba9efd21c750b84322e5fc265eb6adf86cc9"
OUT=BASE/"capa-20261024-simtime-faults-step17"
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_bytes())
rel=lambda p:str(Path(p).resolve().relative_to(ROOT))
def file(p):
 p=Path(p)
 assert p.is_file() and not p.is_symlink()
 return dict(kind="file",path=rel(p),sha256=sha(p))
assert len(sys.argv)==2,"supply decisive run path relative to affa19"
run=(BASE/sys.argv[1]).resolve();run.relative_to(BASE)
assert sha(PARENT)==PARENT_SHA
parent=read(PARENT);assert len(parent["records"])==56 and len(parent["evidence"])==757
wheel=read(run/"wheel-receipt.json");gate=read(run/"dv12-gate-verdict.json")
assert wheel["returncode"]==0 and wheel["passed_exit_status"] is True and not wheel["outer_timeout"]
assert wheel["git_head"]==TESTED and wheel["collected"]==3039
assert gate.get("accepted_as_evidence") is True,"DV12 must actually accept this run"
assert not OUT.exists()
D=ROOT/"docs/engineering/maestro-lite";M=ROOT/"src/xverse/maestro";F=ROOT/"src/xverse/faults"
evidence={
 "E-SIMTIME-REVIEW":file(D/"review-simtime-faults.md"),
 "E-SIMTIME-ADR":file(D/"ADR-ML3-SIMTIME-0001.md"),
 "E-SIMTIME-CHANNEL-SCHEDULER":file(F/"simtime.py"),
 "E-SIMTIME-TESTS":file(ROOT/"tests/thesis_lite/faults/test_simtime.py"),
 "E-SIMTIME-COLLECTION":file(M/"collection_runtime.py"),
 "E-SIMTIME-LIFECYCLE-JOURNAL":file(M/"lifecycle_evidence.py"),
 "E-SIMTIME-FAULT-JOURNAL":file(M/"schedule_evidence.py"),
 "E-SIMTIME-RUN-SUMS":file(run/"SHA256SUMS"),
 "E-SIMTIME-RUN-GATE":file(run/"dv12-gate-verdict.json"),
 "E-SIMTIME-RUN-RECEIPT":file(run/"wheel-receipt.json"),
 "E-SIMTIME-PRIOR-FAILURE":file(BASE/"stabilization-s1a3/platform-regression-20261024i-codex-1/wheel-receipt.json"),
 "E-SIMTIME-STEP17-PLAN":file(BASE/"simtime-step17-plan.md"),
 "E-SIMTIME-STEP17-BUILDER":file(Path(__file__)),
}
for name in ("admission.py","dispatcher.py","persistence.py","persistence_worker.py","projection.py","runtime_entry.py","schedule_plan.py"):
 evidence["E-SIMTIME-"+name[:-3].upper().replace("_","-")]=file(M/name)
for name in ("__init__.py","resolve.py","vocabulary.py"):
 evidence["E-SIMTIME-FAULTS-"+name[:-3].upper().replace("_","-")]=file(F/name)
assert not set(evidence)&set(parent["evidence"])
patch=subprocess.check_output(["git","diff","b40acce49d181058ac61cd651650d18779af8027",TESTED,"--","src/xverse/maestro/collection_runtime.py","src/xverse/maestro/lifecycle_evidence.py","src/xverse/maestro/schedule_evidence.py"],cwd=ROOT)
assert patch
OUT.mkdir()
patch_path=OUT/"collection-continuity.patch";patch_path.write_bytes(patch)
evidence["E-SIMTIME-COLLECTION-PATCH"]=file(patch_path)
register=copy.deepcopy(parent);register["evidence"].update(evidence)
identifier="ML-CAPA-SIMTIME-COLLECTION-20261024";assert identifier not in {r["capa_id"] for r in parent["records"]}
now=datetime.now(timezone.utc).isoformat()
register["records"].append(dict(schema_version="1.0",capa_id=identifier,incident_ids=["review-simtime:8"],state="TRIAGED",root_cause_status="HYPOTHESIS",root_cause_summary="ST2a composed runs exposed a collection-continuity limitation: next collection ordinal considered lifecycle/intent ordinals but not an already-flushed fault ordinal. Source4bed includes the additional fault-ordinal check and recording. Finding8 reports the pre-correction composed failure; independent cause verification and sustained effectiveness are not established.",root_cause_evidence_refs=["E-SIMTIME-REVIEW","E-SIMTIME-COLLECTION","E-SIMTIME-LIFECYCLE-JOURNAL","E-SIMTIME-FAULT-JOURNAL","E-SIMTIME-COLLECTION-PATCH"],reproducer_id=None,prevention_test_id="tests/thesis_lite/faults/test_simtime.py::test_composed_native_run_step_hold_freeze_and_relay_loss",candidate_patch_sha256=sha(patch_path),affected_versions=["b40acce49d181058ac61cd651650d18779af8027 (source-inspected shared collection path; historical runtime occurrence not independently confirmed)"],lesson_ids=[],observation_window_end=None,created_at=now,updated_at=now,policy_sha256=parent["policy_sha256"]))
register["action_plans"][identifier]=dict(containment="retain failed evidence; no acceptance before reviewed full successor and DV12",correction=dict(status="candidate_implemented",evidence_refs=["E-SIMTIME-COLLECTION-PATCH","E-SIMTIME-TESTS","E-SIMTIME-RUN-GATE"]),prevention=dict(status="candidate_coverage",evidence_refs=["E-SIMTIME-TESTS"],limits="Composed native regression covers the corrected path; no independent root-cause or long observation window is claimed."),effectiveness=dict(status="NOT_DEMONSTRATED",observation_plan=None,independent_confirmation=False),next_action="Retain as an observation; obtain independent cause confirmation and a separately admitted effectiveness observation before any CAPA state promotion.")
register["parent_register"]=dict(path=rel(PARENT),sha256=PARENT_SHA)
register["simTimeFaults"]=dict(increment="WP10#3 simulator-time faults/ST2a",base="b40acce49d181058ac61cd651650d18779af8027",tested_candidate=TESTED,review_log="docs/engineering/maestro-lite/review-simtime-faults.md",decisive_run=rel(run),decisive_gate_accepted=True,capa_records_opened=1,capa_rationale="New capability defects repaired before acceptance; separately retain the shared collection-path continuity limitation as TRIAGED/HYPOTHESIS, without cause/effectiveness closure.",recorded_at=now,accepted=False,merged=False)
assert register["records"][:-1]==parent["records"]
assert all(register["action_plans"][key]==value for key,value in parent["action_plans"].items())
assert all(register["evidence"][key]==value for key,value in parent["evidence"].items())
(OUT/"register.json").write_text(json.dumps(register,indent=2)+"\n")
print(json.dumps(dict(records=len(register["records"]),evidence=len(register["evidence"]),register_sha256=sha(OUT/"register.json"),accepted=False,merged=False)))
