"""Build the parent-preserving CAPA successor recording the proposed author dispositions (finding 369).

Usage: python3 -I build-capa-20261020-author-decisions.py

Parent: capa-20261020-run-h/register.json (45 records). Additive only: new evidence IDs for the
decision record, the endpoint reconciliation proposal and the review spans 369-371; next_action and
prevention limits of ML-CAPA-364 (tmpfs declaration, persistent-media reference run) and ML-CAPA-366
(deferred redesign with trigger and computed shape) updated; no state advanced, no effectiveness
claimed, no harness run added. Run both validators afterwards.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261020-run-h"
OUT = BASE / "capa-20261020-author-decisions"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa17.md"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "f563f188df02e10a1fd7a6a423dc6533a28327e836459e35f3913fcc44419a10"
assert len(parent["records"]) == 45
register = copy.deepcopy(parent)
now = datetime.now(timezone.utc).isoformat()
records = {r["capa_id"]: r for r in register["records"]}

def span(start, end):
    text = REVIEW.read_text()
    a = text.index("\n" + start) + 1
    b = text.index("\n" + end) if end else len(text)
    body = text[a:b]
    return dict(kind="review_span", path=rel(REVIEW), start=start, end=end or "EOF", sha256=hashlib.sha256(body.encode()).hexdigest())

def file(path):
    path = Path(path)
    assert path.is_file() and not path.is_symlink(), path
    return dict(kind="file", path=rel(path), sha256=sha(path))

decisions = read(BASE / "author-decisions-proposed-20261020.json")
by_id = {d["id"]: d for d in decisions["decisions"]}
new_evidence = {
    # The validator needs a real end marker; the last finding (371) is bound by the next successor, as for 368.
    "review:369": span("369.", "370."), "review:370": span("370.", "371."),
    "E-DECISIONS-20261020-RECORD": file(BASE / "author-decisions-proposed-20261020.json"),
    "E-DECISIONS-20261020-ENDPOINT-PROPOSAL": file(BASE / "endpoint-reconciliation-proposal-20261020.json"),
    "E-DECISIONS-20261020-ENDPOINT-BUILDER": file(BASE / "build-endpoint-reconciliation-20261020.py"),
}
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
refs = ["E-DECISIONS-20261020-RECORD", "review:369"]

d = by_id["AD-2026-10-20-d"]
r = records["ML-CAPA-364"]
r["incident_ids"] += ["review:369"]; r["root_cause_evidence_refs"] += refs; r["updated_at"] = now
plan = register["action_plans"]["ML-CAPA-364"]
plan["prevention"]["evidence_refs"] = plan["prevention"]["evidence_refs"] + refs
plan["prevention"]["limits"] += " Disposition AD-2026-10-20-d (agent proposal under the author's proceed instruction, not an author approval): tmpfs is the declared harness filesystem for baseline runs; it is never a product durability property."
plan["next_action"] = ("Keep TMPDIR and the private basetemp on tmpfs for baseline runs with the fidelity declaration in each configuration.json and the fsync probe outside the basetemp; "
                       "run one persistent-media (ext4) reference run per increment before acceptance evidence is assembled and triage its expiries as observations; "
                       "keep an ext4 reference probe to track the host condition. (AD-2026-10-20-d; author confirmation pending.)")

c = by_id["AD-2026-10-20-c"]
r = records["ML-CAPA-366"]
r["incident_ids"] += ["review:369"]; r["root_cause_evidence_refs"] += refs; r["updated_at"] = now
plan = register["action_plans"]["ML-CAPA-366"]
plan["prevention"]["limits"] += " Disposition AD-2026-10-20-c: redesign DEFERRED with trigger '" + c["trigger"] + "'."
plan["next_action"] = ("Deferred (AD-2026-10-20-c). Trigger: " + c["trigger"] + ". Shape if triggered: cadence 8 s, operation 0.5 s, 4 units, service_operation_count 4 "
                       "(admission check: scan 2.0 s, period 3.5 s > scan, poll 0.05 s within period, horizon 45 s, 15 slots versus 19 today; restart bound 3.5 s; recovery bound 5 s, minimum 2.75 s); "
                       "asserted scan and slot counts in the transitive modules must be re-authored under their own finding. Run h: no transitive expiry.")

register["selected_findings"] = parent["selected_findings"] + [369, 370, 371]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
register["author_decisions_proposed"] = dict(record="E-DECISIONS-20261020-RECORD", ids=sorted(by_id), author_approved=False,
    source_parent_successor=dict(path="specs/024-maestro-lite-lifecycle/engineering/successors/ML-SOURCE-PARENT-2026-10-20-v3/source-parent-register.json",
                                 repository="/home/jefferson/distributed_safety_critical_thesis",
                                 sha256="e37b4ee88d5dc0d51d8816afdb6c98ab57e42ac8d2196728c6d958a24668383c", status="DRAFT_PROVISIONAL"),
    endpoint_reconciliation=dict(evidence="E-DECISIONS-20261020-ENDPOINT-PROPOSAL", obligations_closed=0, independent_review=False))
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2); stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"))))
