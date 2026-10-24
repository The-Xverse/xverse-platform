"""Build the parent-preserving CAPA successor step 10 for Thesis Lite stabilization S1a-2.

Usage: python3 -I build-capa-20261023-stabilization-s1a2-step10.py <decisive-run-dir relative to this folder>

Parent: capa-20261023-stabilization-s1a-step9 (56 records / 681 bindings, sha 34c742da...). Additive only: file
bindings for the S1a review log (findings 18-26, the S1a-2 cancel-on-busy-connection repair), the
ADR-ML3-AFFA-0001 amendment S1a-3, the repaired run_broker.py, the S1a-2 test module and the decisive full
installed-wheel run (SHA256SUMS, DV12 gate verdict). No record is opened, changed or closed: the race was a defect
of merged S1a code found by the thesis live confirmation (VS-09), recorded as findings 18-21 before the repair and
repaired by this unaccepted candidate. No cause VERIFIED beyond the deterministic reproduction (finding 21), no
effectiveness claimed for live runs (VS-09 follows the merge), no parent record loses an incident or evidence
reference.
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
PARENT_DIR = BASE / "capa-20261023-stabilization-s1a-step9"
OUT = BASE / "capa-20261023-stabilization-s1a2-step10"
RUN = BASE / sys.argv[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "34c742da8952960150018f02a4bed8083d3dca0306eef41ac4531a40f767dcf3"
assert len(parent["records"]) == 56 and len(parent["evidence"]) == 681
verdict = read(RUN / "dv12-gate-verdict.json")
assert verdict.get("accepted_as_evidence") is True, "the decisive run's DV12 gate must accept it"
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)
new_evidence = {
    "E-S1A2-REVIEW-LOG": file(ROOT / "docs/engineering/maestro-lite/review-stabilization-s1a.md"),
    "E-S1A2-ADR-AFFA": file(ROOT / "docs/engineering/maestro-lite/ADR-ML3-AFFA-0001.md"),
    "E-S1A2-RUN-BROKER": file(ROOT / "src/xverse/maestro/run_broker.py"),
    "E-S1A2-TESTS-CANCEL-CONFLICT": file(ROOT / "tests/thesis_lite/maestro/test_stabilization_cancel_conflict.py"),
    "E-S1A2-RUN-SUMS": file(RUN / "SHA256SUMS"),
    "E-S1A2-RUN-GATE": file(RUN / "dv12-gate-verdict.json"),
}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
register["selected_findings"] = parent["selected_findings"]
register["stabilizationS1a2"] = dict(
    increment="S1a-2", branch="candidate/lite-stabilization-s1a2-20261023", base="b28a2aacf",
    head=subprocess.check_output(["git", "rev-parse", "--short=9", "HEAD"], cwd=ROOT, text=True).strip(),
    review_log="docs/engineering/maestro-lite/review-stabilization-s1a.md findings 18-26",
    decisive_run=RUN.name, decisive_gate_accepted=bool(verdict.get("accepted_as_evidence")),
    capa_records_opened=0,
    capa_rationale=("a defect of merged S1a code found by the live confirmation (VS-09), recorded as findings 18-21 "
                    "before any repair, reproduced deterministically (finding 21) and repaired under ADR-ML3-AFFA-0001 "
                    "amendment S1a-3 by this unaccepted candidate (findings 22-25)"),
    recorded_at=datetime.now(timezone.utc).isoformat(), accepted=False, merged=False)
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
