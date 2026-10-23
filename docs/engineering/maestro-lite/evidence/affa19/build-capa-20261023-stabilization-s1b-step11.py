"""Build the parent-preserving CAPA successor step 11 for Thesis Lite stabilization S1b.

Usage: python3 -I build-capa-20261023-stabilization-s1b-step11.py <decisive-run-dir relative to this folder>

Parent: capa-20261023-stabilization-s1a2-step10 (56 records / 687 bindings, sha 4b04cb4a...). Additive only: file
bindings for the S1b review log (findings 1-11+), the S1b design record, the ADR amendments S1b-1 (teardown,
launcher, probe), the changed native and Python sources, the schema, the SD-0001 lock, the new test modules and the
decisive full installed-wheel run (SHA256SUMS, DV12 gate verdict). No record is opened, changed or closed: S1b adds
author-decided capabilities (S1 FR-009 to FR-013, S-D2, S-D3) and every defect was a defect of this unaccepted
candidate, recorded as a finding before its repair. No cause VERIFIED, no effectiveness claimed for live runs.
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
PARENT_DIR = BASE / "capa-20261023-stabilization-s1a2-step10"
OUT = BASE / "capa-20261023-stabilization-s1b-step11"
RUN = BASE / sys.argv[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "4b04cb4aee387323fc123395e7ecf58e491f7384b4fbebce8ed668ab747569d0"
assert len(parent["records"]) == 56 and len(parent["evidence"]) == 687
verdict = read(RUN / "dv12-gate-verdict.json")
assert verdict.get("accepted_as_evidence") is True, "the decisive run's DV12 gate must accept it"
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)
M = ROOT / "src/xverse/maestro"
D = ROOT / "docs/engineering/maestro-lite"
T = ROOT / "tests/thesis_lite/maestro"
files = {
    "E-S1B-REVIEW-LOG": D / "review-stabilization-s1b.md",
    "E-S1B-DESIGN": D / "design-stabilization-s1b.md",
    "E-S1B-ADR-TEARDOWN": D / "ADR-ML3-TEARDOWN-0001.md",
    "E-S1B-ADR-LAUNCHER": D / "ADR-ML3-LAUNCHER-0001.md",
    "E-S1B-ADR-PROBE": D / "ADR-ML3-PROBE-0001.md",
    "E-S1B-RUN-AUTHORITY": M / "native/run_authority.c",
    "E-S1B-AFFA-PROTOCOL": M / "affa_protocol.py",
    "E-S1B-AFFA-CLIENT": M / "affa_client.py",
    "E-S1B-RUN-BROKER": M / "run_broker.py",
    "E-S1B-PROVIDERS": M / "providers.py",
    "E-S1B-PROBE-IDENTITY": M / "probe_identity.py",
    "E-S1B-TEARDOWN": M / "teardown.py",
    "E-S1B-SCHEDULE-PLAN": M / "schedule_plan.py",
    "E-S1B-LIFECYCLE-EVIDENCE": M / "lifecycle_evidence.py",
    "E-S1B-COVERAGE": M / "coverage.py",
    "E-S1B-LAUNCHER": M / "launcher.py",
    "E-S1B-CATALOG": ROOT / "src/xverse_xdl/catalog.py",
    "E-S1B-SCHEMA-V02": ROOT / "xdl/profiles/runtime-compatibility-v0.2.schema.json",
    "E-S1B-SD0001-LOCK": ROOT / "xdl/candidates/sd0001/candidate.lock.json",
    "E-S1B-TESTS-NATIVE": T / "test_stabilization_s1b_native.py",
    "E-S1B-TESTS-BROKER": T / "test_stabilization_s1b_broker.py",
    "E-S1B-TESTS-READINESS": T / "test_stabilization_s1b_readiness.py",
    "E-S1B-TESTS-WORKLOAD": T / "catalog_workload.c",
    "E-S1B-RUN-SUMS": RUN / "SHA256SUMS",
    "E-S1B-RUN-GATE": RUN / "dv12-gate-verdict.json",
}
new_evidence = {key: file(path) for key, path in files.items()}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
register["selected_findings"] = parent["selected_findings"]
register["stabilizationS1b"] = dict(
    increment="S1b", branch="candidate/lite-stabilization-s1b-20261023", base="6f669ec4e (S1a-2 candidate head)",
    head=subprocess.check_output(["git", "rev-parse", "--short=9", "HEAD"], cwd=ROOT, text=True).strip(),
    review_log="docs/engineering/maestro-lite/review-stabilization-s1b.md",
    decisive_run=RUN.name, decisive_gate_accepted=bool(verdict.get("accepted_as_evidence")),
    capa_records_opened=0,
    capa_rationale=("author-decided capabilities (FR-009 to FR-013, S-D2, S-D3; delegated DR-7 to DR-10 flagged for the "
                    "author); candidate defects recorded as findings before their repairs (findings 4-11)"),
    recorded_at=datetime.now(timezone.utc).isoformat(), accepted=False, merged=False)
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
