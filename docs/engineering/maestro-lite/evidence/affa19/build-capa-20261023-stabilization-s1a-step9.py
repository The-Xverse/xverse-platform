"""Build the parent-preserving CAPA successor step 9 for Thesis Lite stabilization S1a.

Usage: python3 -I build-capa-20261023-stabilization-s1a-step9.py <decisive-run-dir relative to this folder>

Parent: capa-20261022-flows-step8 (56 records / 665 bindings, sha 49f25e74...). Additive only: file
bindings for the S1a review log (review-stabilization-s1a.md), the decisive full installed-wheel run
(SHA256SUMS, DV12 gate verdict), the S1a test modules and the bench tooling. No record is opened, changed
or closed: every S1a defect was either a defect of this unaccepted candidate or a pre-existing limit
recorded as a finding (review-stabilization-s1a.md findings 1-13), repaired or dispositioned before
acceptance. No cause VERIFIED, no effectiveness claimed, no parent record loses an incident or evidence
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
PARENT_DIR = BASE / "capa-20261022-flows-step8"
OUT = BASE / "capa-20261023-stabilization-s1a-step9"
RUN = BASE / sys.argv[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "49f25e7488667b61c6b8e9e82c5f2d58d4b97f8e00b5f0a8664077a72fd16f84"
assert len(parent["records"]) == 56 and len(parent["evidence"]) == 665
verdict = read(RUN / "dv12-gate-verdict.json")
assert verdict.get("accepted_as_evidence") is True, "the decisive run's DV12 gate must accept it"
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)
tests = [ROOT / "tests/thesis_lite/maestro/test_stabilization_cancel.py",
         ROOT / "tests/thesis_lite/maestro/test_stabilization_journal_reload.py",
         ROOT / "tests/thesis_lite/argus/test_stabilization_read_records.py",
         ROOT / "tests/thesis_lite/maestro/test_outcomes.py",
         ROOT / "tests/thesis_lite/maestro/test_active_controller_recovery.py"]
bench = sorted((ROOT / "tools/bench/persistence_scaling").glob("*"))
new_evidence = {
    "E-S1A-REVIEW-LOG": file(ROOT / "docs/engineering/maestro-lite/review-stabilization-s1a.md"),
    "E-S1A-ADR-PERSISTENCE": file(ROOT / "docs/engineering/maestro-lite/ADR-ML3-PERSISTENCE-0001.md"),
    "E-S1A-ADR-OUTCOMES": file(ROOT / "docs/engineering/maestro-lite/ADR-ML3-OUTCOMES-0001.md"),
    "E-S1A-ARGUS-DESIGN": file(ROOT / "docs/engineering/argus-lite/detailed-design.md"),
    "E-S1A-RUN-SUMS": file(RUN / "SHA256SUMS"),
    "E-S1A-RUN-GATE": file(RUN / "dv12-gate-verdict.json"),
    **{f"E-S1A-TESTS-{p.stem.upper().replace('_', '-')}": file(p) for p in tests},
    **{f"E-S1A-BENCH-{p.name.upper().replace('_', '-').replace('.', '-')}": file(p) for p in bench if p.is_file()},
}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
register["selected_findings"] = parent["selected_findings"]
register["stabilizationS1a"] = dict(
    increment="S1a", branch="candidate/lite-stabilization-s1a-20261023", base="8b3d8c8e8",
    head=subprocess.check_output(["git", "rev-parse", "--short=9", "HEAD"], cwd=ROOT, text=True).strip(),
    review_log="docs/engineering/maestro-lite/review-stabilization-s1a.md",
    decisive_run=RUN.name, decisive_gate_accepted=bool(verdict.get("accepted_as_evidence")),
    capa_records_opened=0,
    capa_rationale=("candidate defects and pre-existing limits recorded as findings (review-stabilization-s1a.md "
                    "findings 1-13), repaired or dispositioned before acceptance"),
    recorded_at=datetime.now(timezone.utc).isoformat(), accepted=False, merged=False)
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
