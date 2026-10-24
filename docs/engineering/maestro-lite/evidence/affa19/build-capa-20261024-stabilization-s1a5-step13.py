"""Build the parent-preserving CAPA successor step 13 for the Thesis Lite stabilization stack repair S1a-5.

Usage: python3 -I build-capa-20261024-stabilization-s1a5-step13.py <decisive-run-dir relative to this folder>

Parent: capa-20261023-stabilization-s1a3-step12 (56 records / 718 bindings, sha d095ac07...). Additive only: file
bindings for the S1b review log (findings 14-19: the start-up failure revoke, its diagnosis, the S1a-5 repair and its
review), the ADR-ML3-AFFA-0001 amendment S1a-5, the changed run_authority.c, the reproduction test and the decisive
full installed-wheel run (SHA256SUMS, DV12 gate verdict). No record is opened, changed or closed: a defect present
since increment 17, exposed by the S1c-2 part 2 live run, recorded before diagnosis, reproduced deterministically and
repaired in this unaccepted candidate. The expired-lease residual stays a declared fail-closed limit.
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
PARENT_DIR = BASE / "capa-20261023-stabilization-s1a3-step12"
OUT = BASE / "capa-20261024-stabilization-s1a5-step13"
RUN = BASE / sys.argv[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "d095ac0769944532d6dd4d93d922dc27bb16421b498f7be22c4946747c36ddec"
assert len(parent["records"]) == 56 and len(parent["evidence"]) == 718
verdict = read(RUN / "dv12-gate-verdict.json")
assert verdict.get("accepted_as_evidence") is True, "the decisive run's DV12 gate must accept it"
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)
new_evidence = {
    "E-S1A5-REVIEW-LOG-S1B": file(ROOT / "docs/engineering/maestro-lite/review-stabilization-s1b.md"),
    "E-S1A5-ADR-AFFA": file(ROOT / "docs/engineering/maestro-lite/ADR-ML3-AFFA-0001.md"),
    "E-S1A5-RUN-AUTHORITY": file(ROOT / "src/xverse/maestro/native/run_authority.c"),
    "E-S1A5-TESTS-START-FAILURE": file(ROOT / "tests/thesis_lite/maestro/test_stabilization_s1b_start_failure.py"),
    "E-S1A5-RUN-SUMS": file(RUN / "SHA256SUMS"),
    "E-S1A5-RUN-GATE": file(RUN / "dv12-gate-verdict.json"),
}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
register["selected_findings"] = parent["selected_findings"]
register["stabilizationS1a5"] = dict(
    increment="S1a-5 (on the S1a-3 branch)", branch="candidate/lite-stabilization-s1a3-20261023", base="d747f1e0c",
    head=subprocess.check_output(["git", "rev-parse", "--short=9", "HEAD"], cwd=ROOT, text=True).strip(),
    review_log="docs/engineering/maestro-lite/review-stabilization-s1b.md findings 14-19",
    decisive_run=RUN.name, decisive_gate_accepted=bool(verdict.get("accepted_as_evidence")),
    capa_records_opened=0,
    capa_rationale=("a defect present since increment 17 (a deadline-free cancel in the open lease's last second is "
                    "rejected natively and revoked), recorded before diagnosis (finding 14), reproduced (15) and repaired "
                    "under ADR-ML3-AFFA-0001 amendment S1a-5 (16-19)"),
    recorded_at=datetime.now(timezone.utc).isoformat(), accepted=False, merged=False)
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
