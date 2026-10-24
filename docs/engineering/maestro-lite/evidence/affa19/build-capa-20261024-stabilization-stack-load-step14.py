"""Build the parent-preserving CAPA successor step 14 for the Thesis Lite stabilization stack load repairs (DR-15/16/17).

Usage: python3 -I build-capa-20261024-stabilization-stack-load-step14.py <decisive-run-dir relative to this folder>

Parent: capa-20261024-stabilization-s1a5-step13 (56 records / 724 bindings, sha cdbb1506...). Additive only: file
bindings for the S1b review log (findings 21-29: the two load failures of the S1c-2 part 2 live re-verification, their
diagnosis, the repairs RB1, RA1, RA4 (DR-15), RA2, RA5 and the window record (DR-16), the fence cap and the L1 carry
(DR-17), three independent reviews and their dispositions), the ADR notes (PERSISTENCE-0001, PROBE-0001, AFFA-0001),
the S1b design record, the changed sources and tests, and the decisive full installed-wheel run (SHA256SUMS, DV12 gate
verdict). No record is opened, changed or closed: defects exposed under load by the unaccepted S1c-2 live harness,
recorded before diagnosis, reproduced deterministically and repaired in this unaccepted candidate. The declared
residuals (W' = 0 for restarts and generation-limited starts, sub-round-trip caps, expired caps, the fence's own
0.25 s margin, the pre-cancel fault statements) stay declared fail-closed limits.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261024-stabilization-s1a5-step13"
OUT = BASE / "capa-20261024-stabilization-stack-load-step14"
RUN = BASE / sys.argv[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "cdbb1506b655708857ee920e0ef968bd2c263ef62e9bda056920edce228284e7"
assert len(parent["records"]) == 56 and len(parent["evidence"]) == 724
verdict = read(RUN / "dv12-gate-verdict.json")
assert verdict.get("accepted_as_evidence") is True, "the decisive run's DV12 gate must accept it"
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)
M = ROOT / "src/xverse/maestro"
T = ROOT / "tests/thesis_lite/maestro"
D = ROOT / "docs/engineering/maestro-lite"
new_evidence = {
    "E-STACK-LOAD-REVIEW-LOG-S1B": file(D / "review-stabilization-s1b.md"),
    "E-STACK-LOAD-DESIGN-S1B": file(D / "design-stabilization-s1b.md"),
    "E-STACK-LOAD-ADR-PERSISTENCE": file(D / "ADR-ML3-PERSISTENCE-0001.md"),
    "E-STACK-LOAD-ADR-PROBE": file(D / "ADR-ML3-PROBE-0001.md"),
    "E-STACK-LOAD-ADR-AFFA": file(D / "ADR-ML3-AFFA-0001.md"),
    "E-STACK-LOAD-PERSISTENCE": file(M / "persistence.py"),
    "E-STACK-LOAD-PROVIDERS": file(M / "providers.py"),
    "E-STACK-LOAD-DISPATCHER": file(M / "dispatcher.py"),
    "E-STACK-LOAD-RUN-BROKER": file(M / "run_broker.py"),
    "E-STACK-LOAD-SCHEDULE-PLAN": file(M / "schedule_plan.py"),
    "E-STACK-LOAD-TESTS-LOAD-FAILURES": file(T / "test_stabilization_stack_load_failures.py"),
    "E-STACK-LOAD-TESTS-READINESS": file(T / "test_stabilization_s1b_readiness.py"),
    "E-STACK-LOAD-TESTS-START-FAILURE": file(T / "test_stabilization_s1b_start_failure.py"),
    "E-STACK-LOAD-TESTS-SCHEDULE-PLAN": file(T / "test_schedule_plan.py"),
    "E-STACK-LOAD-TESTS-RECOVERY": file(T / "test_active_controller_recovery.py"),
    "E-STACK-LOAD-RUN-SUMS": file(RUN / "SHA256SUMS"),
    "E-STACK-LOAD-RUN-GATE": file(RUN / "dv12-gate-verdict.json"),
}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
register["selected_findings"] = parent["selected_findings"]
register["stabilizationStackLoad"] = dict(
    increment="S1b-stack load repairs DR-15/16/17 (on the S1a-3 branch)", branch="candidate/lite-stabilization-s1a3-20261023",
    base="0dc9ffec3",
    head=subprocess.check_output(["git", "rev-parse", "--short=9", "HEAD"], cwd=ROOT, text=True).strip(),
    review_log="docs/engineering/maestro-lite/review-stabilization-s1b.md findings 21-29",
    decisive_run=RUN.name, decisive_gate_accepted=bool(verdict.get("accepted_as_evidence")),
    capa_records_opened=0,
    capa_rationale=("two defects exposed at load 8.4-8.7 by the unaccepted S1c-2 live harness (finding 21): a cancel "
                    "between the two cancel reads of PersistenceClient._live failed storage (B), and a readiness window "
                    "not sized against the bootstrap lease left a cancel without its native close time (A); recorded "
                    "before diagnosis, reproduced (22) and repaired under ADR notes (23-29) with three independent reviews"),
    recorded_at=datetime.now(timezone.utc).isoformat(), accepted=False, merged=False)
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
