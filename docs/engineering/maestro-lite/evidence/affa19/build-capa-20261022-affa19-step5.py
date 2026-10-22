"""Build the parent-preserving CAPA successor for increment19 step 5 (findings 486-LAST).

Usage: python3 -I build-capa-20261022-affa19-step5.py <decisive-run-dir> <last-finding>

Parent: capa-20261021-affa19-step4 (56 records / 627 bindings, sha 7b384e75...). Additive only:
review spans 486-LAST, the quiet-host procedure (run x/y/z drivers), the full-run evidence of runs
x, y, z-1, z-2 and the decisive run, and the control (d) oracle repair (489-490, test only).
ML-CAPA-418 stays FIX_CANDIDATE on E1 (897d9dc50); acceptance of the increment, when it happens,
is recorded in the increment19 block, not as a CAPA state: no cause VERIFIED, no effectiveness
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
PARENT_DIR = BASE / "capa-20261021-affa19-step4"
OUT = BASE / "capa-20261022-affa19-step5"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa19.md"
TESTS = ROOT / "tests/thesis_lite/maestro"
RUN, LAST = BASE / sys.argv[1], int(sys.argv[2])  # LAST + 1 records this successor
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))
file = lambda p: dict(kind="file", path=rel(p), sha256=sha(p))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "7b384e75fc6e8c36289ed9be05cb652a4581e848ddcbb429881db4139b3d80f8"
assert len(parent["records"]) == 56 and len(parent["evidence"]) == 627
verdict = read(RUN / "dv12-gate-verdict.json")
register = copy.deepcopy(parent)
OUT.mkdir(exist_ok=False)


def span(n):
    text = REVIEW.read_text()
    body = text[text.index(f"\n{n}.") + 1:text.index(f"\n{n + 1}.")]
    return dict(kind="review_span", path=rel(REVIEW), start=f"{n}.", end=f"{n + 1}.",
                sha256=hashlib.sha256(body.encode()).hexdigest())


ORACLE = OUT / "control-d-oracle.patch"
ORACLE.write_bytes(subprocess.check_output(["git", "diff", "f1f0b630e", "af9bd3c72", "--", "tests"], cwd=ROOT))
E = BASE
runs = {"X": "platform-regression-20261021x", "Y": "platform-regression-20261021y",
        "Z1": "platform-regression-20261021z-1", "Z2": "platform-regression-20261021z-2"}
new_evidence = {
    **{f"review:{n}": span(n) for n in range(486, LAST + 1)},
    **{f"E-AFFA19-RUN-{k}-SUMS": file(E / v / "SHA256SUMS") for k, v in runs.items()},
    "E-AFFA19-RUN-DECISIVE-SUMS": file(RUN / "SHA256SUMS"),
    "E-AFFA19-RUN-DECISIVE-GATE": file(RUN / "dv12-gate-verdict.json"),
    "E-AFFA19-QUIET-WATCH-X": file(E / "run-x-quiet-watch.sh"),
    "E-AFFA19-QUIET-WATCH-Y": file(E / "run-y-quiet-watch.sh"),
    "E-AFFA19-QUIET-LOOP-Z": file(E / "run-z-quiet-loop.sh"),
    "E-AFFA19-CONTROL-D-ORACLE": file(ORACLE),
    "E-AFFA19-E1-TESTS-REPAIRED": file(TESTS / "test_load_aware_budgets.py"),
}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
now = datetime.now(timezone.utc).isoformat()
records = {r["capa_id"]: r for r in register["records"]}


def extend(capa, incidents, refs, **fields):
    row = records[capa]
    row["incident_ids"] += [i for i in incidents if i not in row["incident_ids"]]
    row["root_cause_evidence_refs"] += [r for r in refs if r not in row["root_cause_evidence_refs"]]
    row.update(fields, updated_at=now)


accepted = bool(verdict.get("accepted_as_evidence"))
extend("ML-CAPA-418", [f"review:{n}" for n in (487, 488, 489)],
       ["review:487", "review:488", "review:489", "review:490", "E-AFFA19-RUN-X-SUMS", "E-AFFA19-RUN-Y-SUMS",
        "E-AFFA19-RUN-Z1-SUMS", "E-AFFA19-RUN-Z2-SUMS", "E-AFFA19-RUN-DECISIVE-SUMS",
        "E-AFFA19-RUN-DECISIVE-GATE", "E-AFFA19-CONTROL-D-ORACLE"],
       root_cause_summary=records["ML-CAPA-418"]["root_cause_summary"] + (
           " Full runs on E1 (487-491): " + RUN.name + " gate " + ("accepted" if accepted else "not accepted") + "."))
assert len(records["ML-CAPA-418"]["root_cause_summary"]) <= 2000  # schema maxLength
register["action_plans"]["ML-CAPA-418"].update(
    next_action=("Full installed-wheel runs on E1: x, y and z-1 failed only under external load (samples above "
                 "10; budget-class timing failures, mostly in the nested Argus run; observations under 469); z-2 "
                 "at load at most 5.09 failed only control (d), a duration-dependent renewal-count oracle (489), "
                 "replaced by a renewal invariant (490, test only); decisive run " + RUN.name + " clean. "
                 "Increment acceptance under 476 E3 is recorded in increment19; effectiveness beyond the observed "
                 "load not demonstrated; nested-versus-outer asymmetry (488) and the test_dispatcher.py:307-314 "
                 "count oracle (490) stay under T06 observation."))
register["selected_findings"] = parent["selected_findings"] + list(range(486, LAST + 1))
register["increment19"] = dict(parent["increment19"], step5_head=subprocess.check_output(
    ["git", "rev-parse", "--short=9", "HEAD"], cwd=ROOT, text=True).strip(), decisive_run=RUN.name,
    decisive_gate_accepted=accepted, accepted=False, merged=False, delegation="review-affa19.md finding 476")
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]),
                      register_sha256=sha(OUT / "register.json"))))
