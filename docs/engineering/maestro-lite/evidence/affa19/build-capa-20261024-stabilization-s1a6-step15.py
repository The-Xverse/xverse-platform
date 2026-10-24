"""Build the parent-preserving CAPA successor step 15 for the Thesis Lite stabilization repair S1a-6 (DR-20).

Usage: python3 -I build-capa-20261024-stabilization-s1a6-step15.py <decisive-run-dir relative to this folder>

Parent: capa-20261024-stabilization-stack-load-step14 (56 records / 741 bindings, sha fb5eb459...). Additive only: file
bindings for the S1b review log (findings 30-32: a health slot due inside the Stop bracket reported unverifiable
although a valid sample discharged it, its diagnosis, the DR-20 repair and its review), the coverage contract, the
coverage/runtime composition note, the ADR-ML3-EVIDENCE-0001 amendment S1a-6, coverage.py, the reproduction test and
the decisive full installed-wheel run (SHA256SUMS, DV12 gate verdict). No record is opened, changed or closed: a
fail-closed false failure exposed by the unaccepted S1c-2 live harness (dev7), recorded before diagnosis, reproduced
deterministically and repaired in this candidate. A bracket slot without a valid sample before the Stop request stays
unverifiable (declared fail-closed limit).
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
PARENT_DIR = BASE / "capa-20261024-stabilization-stack-load-step14"
OUT = BASE / "capa-20261024-stabilization-s1a6-step15"
RUN = BASE / sys.argv[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "fb5eb4598266e1cd5178d9508830cdc00933550b64e353485f65be9517efbf03"
assert len(parent["records"]) == 56 and len(parent["evidence"]) == 741
verdict = read(RUN / "dv12-gate-verdict.json")
assert verdict.get("accepted_as_evidence") is True, "the decisive run's DV12 gate must accept it"
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)
M = ROOT / "src/xverse/maestro"
T = ROOT / "tests/thesis_lite/maestro"
D = ROOT / "docs/engineering/maestro-lite"
new_evidence = {
    "E-S1A6-REVIEW-LOG-S1B": file(D / "review-stabilization-s1b.md"),
    "E-S1A6-COVERAGE-CONTRACT": file(D / "coverage-assessment.md"),
    "E-S1A6-COVERAGE-COMPOSITION": file(D / "affa-coverage-runtime-composition.md"),
    "E-S1A6-ADR-EVIDENCE": file(D / "ADR-ML3-EVIDENCE-0001.md"),
    "E-S1A6-COVERAGE": file(M / "coverage.py"),
    "E-S1A6-TESTS-HEALTH-BOUNDARY": file(T / "test_stabilization_coverage_health_boundary.py"),
    "E-S1A6-RUN-SUMS": file(RUN / "SHA256SUMS"),
    "E-S1A6-RUN-GATE": file(RUN / "dv12-gate-verdict.json"),
}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
register["selected_findings"] = parent["selected_findings"]
register["stabilizationS1a6"] = dict(
    increment="S1a-6 (DR-20)", branch="candidate/lite-stabilization-s1a6-20261024", base="ee91697a4",
    head=subprocess.check_output(["git", "rev-parse", "--short=9", "HEAD"], cwd=ROOT, text=True).strip(),
    review_log="docs/engineering/maestro-lite/review-stabilization-s1b.md findings 30-32",
    decisive_run=RUN.name, decisive_gate_accepted=bool(verdict.get("accepted_as_evidence")),
    capa_records_opened=0,
    capa_rationale=("a fail-closed false failure: a health slot due inside the Stop bracket was reported unverifiable "
                    "although a valid sample before the Stop request discharged it (finding 30); repaired under the "
                    "ADR-ML3-EVIDENCE-0001 amendment S1a-6 (31) and reviewed (32)"),
    recorded_at=datetime.now(timezone.utc).isoformat(), accepted=False, merged=False)
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
