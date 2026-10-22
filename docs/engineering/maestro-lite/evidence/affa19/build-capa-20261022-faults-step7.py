"""Build the parent-preserving CAPA successor step 7 for Thesis Lite Phase 5 (fault injection).

Usage: python3 -I build-capa-20261022-faults-step7.py <decisive-run-dir relative to this folder>

Parent: capa-20261022-affa19-step6 (56 records / 647 bindings, sha fb8d7058...). Additive only:
file bindings for the Phase 5 review log (review-faults-lite.md), the decisive full installed-wheel
run (SHA256SUMS, DV12 gate verdict) and the Phase 5 test modules. No record is opened, changed or
closed: every defect found during Phase 5 was a defect of the unaccepted candidate, recorded in the
review log and repaired before acceptance; none concerns an accepted component. No cause VERIFIED,
no effectiveness claimed, no parent record loses an incident or evidence reference.
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
PARENT_DIR = BASE / "capa-20261022-affa19-step6"
OUT = BASE / "capa-20261022-faults-step7"
RUN = BASE / sys.argv[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "fb8d70588223c284ffcf3e2fb454ceeddf4470f8e5a1923476b44d4110cdfff2"
assert len(parent["records"]) == 56 and len(parent["evidence"]) == 647
verdict = read(RUN / "dv12-gate-verdict.json")
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)
tests = sorted((ROOT / "tests" / "thesis_lite" / "faults").glob("test_*.py"))
new_evidence = {
    "E-FAULTS-REVIEW-LOG": file(ROOT / "docs/engineering/maestro-lite/review-faults-lite.md"),
    "E-FAULTS-RUN-SUMS": file(RUN / "SHA256SUMS"),
    "E-FAULTS-RUN-GATE": file(RUN / "dv12-gate-verdict.json"),
    **{f"E-FAULTS-TESTS-{p.stem.upper().replace('_', '-')}": file(p) for p in tests},
}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
register["selected_findings"] = parent["selected_findings"]
register["faultsLite"] = dict(
    phase=5, branch="candidate/faults-lite-20261022", base="744b66f9c",
    head=subprocess.check_output(["git", "rev-parse", "--short=9", "HEAD"], cwd=ROOT, text=True).strip(),
    review_log="docs/engineering/maestro-lite/review-faults-lite.md",
    decisive_run=RUN.name, decisive_gate_accepted=bool(verdict.get("accepted_as_evidence")),
    capa_records_opened=0,
    capa_rationale="candidate defects only (review-faults-lite.md findings 2-10), repaired before acceptance",
    recorded_at=datetime.now(timezone.utc).isoformat(), accepted=False, merged=False)
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
