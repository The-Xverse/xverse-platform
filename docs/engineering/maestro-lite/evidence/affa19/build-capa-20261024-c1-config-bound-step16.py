"""Build the parent-preserving CAPA successor step 16 for X-Verse increment C1 (the role-3 persistence configuration bound).

Usage: python3 -I build-capa-20261024-c1-config-bound-step16.py <decisive-run-dir relative to this folder>

Parent: capa-20261024-stabilization-s1a6-step15 (56 records / 749 bindings, sha 6be1a184...). Additive only: file
bindings for the C1 review log (findings 1-5), the ADR-ML3-BOOTSTRAP-0001 amendment C1 and its ADR-ML3-PERSISTENCE-0001
note, bootstrap.py, native/bootstrap.c, the bound tests and the decisive full installed-wheel run (SHA256SUMS, DV12 gate
verdict). No record is opened, changed or closed: a capacity extension required by the Phase 8 unit allocation
(thesis 002 decisions §J), not a defect repair. The other role inputs stay at 65536.
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
PARENT_DIR = BASE / "capa-20261024-stabilization-s1a6-step15"
OUT = BASE / "capa-20261024-c1-config-bound-step16"
RUN = BASE / sys.argv[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "6be1a184fc2261663266e9f1e46f84207465d7efa248b9a79f9b17f65ed79c64"
assert len(parent["records"]) == 56 and len(parent["evidence"]) == 749
verdict = read(RUN / "dv12-gate-verdict.json")
assert verdict.get("accepted_as_evidence") is True, "the decisive run's DV12 gate must accept it"
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)
M = ROOT / "src/xverse/maestro"
T = ROOT / "tests/thesis_lite/maestro"
D = ROOT / "docs/engineering/maestro-lite"
new_evidence = {
    "E-C1-REVIEW-LOG": file(D / "review-c1.md"),
    "E-C1-ADR-BOOTSTRAP": file(D / "ADR-ML3-BOOTSTRAP-0001.md"),
    "E-C1-ADR-PERSISTENCE": file(D / "ADR-ML3-PERSISTENCE-0001.md"),
    "E-C1-BOOTSTRAP-PY": file(M / "bootstrap.py"),
    "E-C1-BOOTSTRAP-C": file(M / "native" / "bootstrap.c"),
    "E-C1-TESTS-BOUND": file(next(ROOT.glob("tests/**/test_persistence_config_bound.py"))),
    "E-C1-RUN-SUMS": file(RUN / "SHA256SUMS"),
    "E-C1-RUN-GATE": file(RUN / "dv12-gate-verdict.json"),
}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
register["selected_findings"] = parent["selected_findings"]
register["c1ConfigBound"] = dict(
    increment="C1 (role-3 persistence configuration bound 65536 -> 262144 B)", branch="candidate/lite-c1-config-bound-20261024",
    base="64ff9d3eb",
    head=subprocess.check_output(["git", "rev-parse", "--short=9", "HEAD"], cwd=ROOT, text=True).strip(),
    review_log="docs/engineering/maestro-lite/review-c1.md findings 1-5",
    decisive_run=RUN.name, decisive_gate_accepted=bool(verdict.get("accepted_as_evidence")),
    capa_records_opened=0,
    capa_rationale=("a capacity extension for the Phase 8 six-unit allocation (thesis 002 decisions §J): the 64 KiB "
                    "role-input seal refused every Phase 8 configuration; the role-3 bound becomes 256 KiB, other roles "
                    "unchanged; reviewed in finding 3 (PASS WITH NOTES), repaired in findings 4-5"),
    recorded_at=datetime.now(timezone.utc).isoformat(), accepted=False, merged=False)
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
