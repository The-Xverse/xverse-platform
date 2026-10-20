"""Build the parent-preserving CAPA successor adding run f as a further prevention observation.

Usage: python3 -I build-capa-20261020-run-f.py

Parent: capa-20261020-harness-repairs/register.json (44 records / 275 bindings). Additive only:
new evidence IDs for run f (receipt, log, triage, probe, GC log) and the finding-366 review span;
incident/evidence references appended to 357, 359-CHILD, 222 and 364; prevention statuses updated
from run f's actual outcome; no state is advanced beyond FIX_CANDIDATE and no effectiveness is claimed.
Run both validators afterwards.
"""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PARENT_DIR = BASE / "capa-20261020-harness-repairs"
OUT = BASE / "capa-20261020-run-f"
REVIEW = ROOT / "docs/engineering/maestro-lite/review-affa17.md"
RUN_F = BASE / "platform-regression-20261020f"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))

parent = read(PARENT_DIR / "register.json")
assert sha(PARENT_DIR / "register.json") == "bfe07733e1e9842180e9915d68690ee3285423ab8618398042a8623742298d38"
assert len(parent["records"]) == 44 and len(parent["evidence"]) == 275
register = copy.deepcopy(parent)
now = datetime.now(timezone.utc).isoformat()
records = {r["capa_id"]: r for r in register["records"]}

def span(start, end):
    text = REVIEW.read_text()
    body = text[text.index("\n" + start) + 1:text.index("\n" + end)]
    return dict(kind="review_span", path=rel(REVIEW), start=start, end=end, sha256=hashlib.sha256(body.encode()).hexdigest())

def file(path):
    path = Path(path)
    assert path.is_file() and not path.is_symlink(), path
    return dict(kind="file", path=rel(path), sha256=sha(path))

receipt = read(RUN_F / "source-receipt.json")
triage = read(RUN_F / "failure-triage.json")
failed = {f["nodeid"] for f in triage["failures"]}
build_nodes_absent = not any("No module named build" in "\n".join(f["traceback_last_lines"]) for f in triage["failures"])
child_errors = sum(1 for line in (RUN_F / "source.log").read_text().splitlines() if line.startswith("E         ERROR tests/"))
LEAF = "tests/thesis_lite/maestro/test_active_restart.py::test_original_active_explicit_restart_and_closed_generation_universe[leaf]"
timeouts = sorted(f["nodeid"] for f in triage["failures"] if "thesis_lite/maestro" in f["nodeid"]
                  and any("ML-PERSIST-TIMEOUT" in l or "TEARDOWN-INCOMPLETE" in l or "TERMINAL-INCOMPLETE" in l for l in f["traceback_last_lines"]))
probe_rows = [json.loads(l) for l in (RUN_F / "fsync-probe.jsonl").read_text().splitlines()] if (RUN_F / "fsync-probe.jsonl").is_file() else []
probe_summary = next((r for r in probe_rows if r.get("summary")), None)
probe_spikes = sum(1 for r in probe_rows if "fsync_seconds" in r and not r.get("summary"))

new_evidence = {"review:365": span("365.", "366."), "review:366": span("366.", "367.") if "\n367." in REVIEW.read_text() else None}
new_evidence = {k: v for k, v in new_evidence.items() if v}
for name, path in (("RECEIPT", "source-receipt.json"), ("LOG", "source.log"), ("TRIAGE", "failure-triage.json"),
                   ("FSYNC-PROBE", "fsync-probe.jsonl"), ("GC-LOG", "gc-pauses.jsonl"), ("FIXTURE-DIFF", "fixture-window-margin.diff"),
                   ("CONFIG", "configuration.json")):
    if (RUN_F / path).is_file():
        new_evidence["E-HARNESS-F-" + name] = file(RUN_F / path)
new_evidence["E-HARNESS-F-DRIVER"] = file(BASE / "verify-platform-regression-20261020f.py")
for key in new_evidence:
    assert key not in register["evidence"], key
register["evidence"].update(new_evidence)
f_refs = [k for k in new_evidence if k.startswith("E-HARNESS-F-")] + [k for k in new_evidence if k.startswith("review:")]

for capa_id, status in (
    ("ML-CAPA-357", "run_f_build_signature_absent:" + json.dumps(build_nodes_absent)),
    ("ML-CAPA-359-CHILD", "run_f_child_setup_errors:" + str(child_errors)),
    ("ML-CAPA-222", "run_f_leaf_reproducer_passed:" + json.dumps(LEAF not in failed)),
    ("ML-CAPA-364", "run_f_whole_session_tmpfs_timeouts_" + str(len(timeouts)) + "_probe_spikes_" + str(probe_spikes)
                    + ("_summary_terminal" if probe_summary else "_summary_absent")),
):
    r = records[capa_id]
    r["incident_ids"] += ["review:365"]
    r["root_cause_evidence_refs"] += f_refs
    r["updated_at"] = now
    plan = register["action_plans"][capa_id]
    plan["prevention"]["status"] = plan["prevention"]["status"] + "; " + status
    plan["prevention"]["evidence_refs"] = plan["prevention"]["evidence_refs"] + f_refs
r = records["ML-CAPA-359"]
r["incident_ids"] += ["review:365"]
r["root_cause_evidence_refs"] += f_refs
r["updated_at"] = now
register["action_plans"]["ML-CAPA-359"]["next_action"] += " Run f (whole session on tmpfs): Maestro expiries " + json.dumps(timeouts) + "."
register["selected_findings"] = parent["selected_findings"] + [365]
register["parent_register"] = dict(path=rel(PARENT_DIR / "register.json"), sha256=sha(PARENT_DIR / "register.json"))
register["harness_runs"] = dict(parent["harness_runs"], f=dict(returncode=receipt["returncode"], failed=triage["failed_count"],
    child_setup_errors=child_errors, maestro_timeouts=timeouts, probe_spikes=probe_spikes, probe_summary=probe_summary,
    collected=2088, whole_session_tmpdir_on_tmpfs=True))
OUT.mkdir(exist_ok=False)
with (OUT / "register.json").open("x") as stream:
    json.dump(register, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(records=len(register["records"]), evidence=len(register["evidence"]), register_sha256=sha(OUT / "register.json"),
                      run_f=register["harness_runs"]["f"])))
