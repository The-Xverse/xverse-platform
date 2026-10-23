"""Build the parent-preserving CAPA successor step 12 for Thesis Lite stabilization S1a-3.

Usage: python3 -I build-capa-20261023-stabilization-s1a3-step12.py <decisive-run-dir relative to this folder>

Parent: capa-20261023-stabilization-s1b-step11 (56 records / 712 bindings, sha 3eb39cda...). Additive only: file
bindings for the S1a review log (findings 28-31, the S1a-3 terminal-cost repair), the ADR-ML3-EVIDENCE-0001
amendment S1a-4, the changed evidence.py, the byte-identity differential test and the decisive full installed-wheel
run (SHA256SUMS, DV12 gate verdict). No record is opened, changed or closed: the long-run terminal-budget limit (thesis
S-D9, S1c finding 32) was profiled as finding 28 before any repair and repaired by FR-002's prescribed path in this
unaccepted candidate. No effectiveness claimed for live runs (the long-run is confirmed in S1d).
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
PARENT_DIR = BASE / "capa-20261023-stabilization-s1b-step11"
OUT = BASE / "capa-20261023-stabilization-s1a3-step12"
RUN = BASE / sys.argv[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "3eb39cda32a0376eefe44099e4eff3c573f1d26253986627bde697b0d2ea99d5"
assert len(parent["records"]) == 56 and len(parent["evidence"]) == 712
verdict = read(RUN / "dv12-gate-verdict.json")
assert verdict.get("accepted_as_evidence") is True, "the decisive run's DV12 gate must accept it"
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)
new_evidence = {
    "E-S1A3-REVIEW-LOG": file(ROOT / "docs/engineering/maestro-lite/review-stabilization-s1a.md"),
    "E-S1A3-ADR-EVIDENCE": file(ROOT / "docs/engineering/maestro-lite/ADR-ML3-EVIDENCE-0001.md"),
    "E-S1A3-EVIDENCE-PY": file(ROOT / "src/xverse/maestro/evidence.py"),
    "E-S1A3-TESTS-BOUNDED": file(ROOT / "tests/thesis_lite/maestro/test_stabilization_bounded_encoding.py"),
    "E-S1A3-RUN-SUMS": file(RUN / "SHA256SUMS"),
    "E-S1A3-RUN-GATE": file(RUN / "dv12-gate-verdict.json"),
}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
register["selected_findings"] = parent["selected_findings"]
register["stabilizationS1a3"] = dict(
    increment="S1a-3", branch="candidate/lite-stabilization-s1a3-20261023", base="0929bd2d5 (S1b candidate head)",
    head=subprocess.check_output(["git", "rev-parse", "--short=9", "HEAD"], cwd=ROOT, text=True).strip(),
    review_log="docs/engineering/maestro-lite/review-stabilization-s1a.md findings 28-31",
    decisive_run=RUN.name, decisive_gate_accepted=bool(verdict.get("accepted_as_evidence")),
    capa_records_opened=0,
    capa_rationale=("a terminal-budget limit of the S-D1 long-run found by S1c finding 32 (thesis S-D9), profiled as "
                    "finding 28 before any repair and repaired by FR-002's prescribed path under ADR-ML3-EVIDENCE-0001 "
                    "amendment S1a-4 in this unaccepted candidate (findings 29-31)"),
    recorded_at=datetime.now(timezone.utc).isoformat(), accepted=False, merged=False)
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
