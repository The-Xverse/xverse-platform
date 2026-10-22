"""Build the parent-preserving CAPA successor step 8 for Thesis Lite Phase 6 (flow runtime).

Usage: python3 -I build-capa-20261022-flows-step8.py <decisive-run-dir relative to this folder>

Parent: capa-20261022-faults-step7 (56 records / 654 bindings, sha 76a60c17...). Additive only:
file bindings for the Phase 6 review log (review-flows-lite.md), the decisive full installed-wheel
run (SHA256SUMS, DV12 gate verdict), the V10 gtest evidence and the Phase 6 test modules. No record
is opened, changed or closed: every Phase 6 defect was a defect of the unaccepted candidate,
recorded in the review log and repaired before acceptance. No cause VERIFIED, no effectiveness
claimed, no parent record loses an incident or evidence reference.
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
PARENT_DIR = BASE / "capa-20261022-faults-step7"
OUT = BASE / "capa-20261022-flows-step8"
RUN = BASE / sys.argv[1]
V10 = BASE / "flows-lite" / "v10-gtest-20261022"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "76a60c17b33046468a604fcf280b0af60b5fc34f3a521dc2d2631dce09cd541f"
assert len(parent["records"]) == 56 and len(parent["evidence"]) == 654
verdict = read(RUN / "dv12-gate-verdict.json")
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)
tests = sorted((ROOT / "tests" / "thesis_lite" / "flows").glob("test_*.py")) + [ROOT / "tests/thesis_lite/faults/test_relay_kinds.py"]
new_evidence = {
    "E-FLOWS-REVIEW-LOG": file(ROOT / "docs/engineering/maestro-lite/review-flows-lite.md"),
    "E-FLOWS-RUN-SUMS": file(RUN / "SHA256SUMS"),
    "E-FLOWS-RUN-GATE": file(RUN / "dv12-gate-verdict.json"),
    "E-FLOWS-V10-SUMS": file(V10 / "SHA256SUMS"),
    **{f"E-FLOWS-TESTS-{p.stem.upper().replace('_', '-')}": file(p) for p in tests},
}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
register["selected_findings"] = parent["selected_findings"]
register["flowsLite"] = dict(
    phase=6, branch="candidate/flows-lite-20261022", base="2d556ff24",
    head=subprocess.check_output(["git", "rev-parse", "--short=9", "HEAD"], cwd=ROOT, text=True).strip(),
    review_log="docs/engineering/maestro-lite/review-flows-lite.md",
    decisive_run=RUN.name, decisive_gate_accepted=bool(verdict.get("accepted_as_evidence")),
    capa_records_opened=0,
    capa_rationale="candidate defects only (review-flows-lite.md findings 2-11), repaired before acceptance",
    recorded_at=datetime.now(timezone.utc).isoformat(), accepted=False, merged=False)
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
