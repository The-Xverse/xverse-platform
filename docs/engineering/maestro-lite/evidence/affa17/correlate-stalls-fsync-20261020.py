"""Read-only correlation of operation stalls in one run's timelines with fsync-latency probe spikes.

Usage: python3 -I correlate-stalls-fsync-20261020.py <run-directory> <probe.jsonl> <output.json>

A stall is any operation whose observed duration exceeds STALL_SECONDS and that is not an
intended fault wait (diagnostic None, or ML-PERSIST-TIMEOUT in a case the run reports as
failed). A spike is a probe sample whose fsync took longer than SPIKE_SECONDS. Both use the
host monotonic clock. A stall is "matched" when a spike lies within WINDOW_SECONDS of the
stall interval. This is a temporal association, not a causal proof.
"""
from pathlib import Path
import glob
import hashlib
import json
import statistics
import sys

STALL_SECONDS, SPIKE_SECONDS, WINDOW_SECONDS = 0.5, 0.15, 2.0
run = Path(sys.argv[1]).resolve(strict=True)
probe = Path(sys.argv[2]).resolve(strict=True)
output = Path(sys.argv[3])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

spikes, summary = [], None
for line in probe.read_text().splitlines():
    row = json.loads(line)
    if row.get("summary"):
        summary = row
    elif row["fsync_seconds"] > SPIKE_SECONDS:
        spikes.append(row)
if summary:
    probe_start = summary["started_monotonic"]
    if "seconds" in summary:
        probe_end = probe_start + summary["seconds"]
    else:  # duration not recorded: the window ends at the last spike seen (documented inference)
        probe_end = max([s["monotonic"] for s in spikes] + [probe_start])
        summary = dict(summary, window_end_inferred_from_last_spike=True)
else:  # probe still running: window spans the observed samples so far
    probe_start = min((s["monotonic"] for s in spikes), default=0.0)
    probe_end = max((s["monotonic"] for s in spikes), default=0.0)
    summary = dict(summary=False, note="probe not terminal at correlation time", spikes_seen=len(spikes))

triage = json.loads((run / "failure-triage.json").read_bytes()) if (run / "failure-triage.json").is_file() else None
failed = {f["nodeid"].split("::")[-1] for f in triage["failures"]} if triage else set()

stalls, durations = [], []
for f in sorted(glob.glob(str(run / "source-harness/*/lazy-operations-*.json"))):
    try:
        ops = json.loads(Path(f).read_bytes())["operations"]
    except Exception:
        continue
    if not ops:
        continue
    case = Path(f).name[len("lazy-operations-"):-len(".json")]
    for o in ops:
        if not o.get("ended"):
            continue
        d = o["ended"] - o["began"]
        durations.append(d)
        intended = o.get("diagnostic") not in (None, "ML-PERSIST-TIMEOUT")
        if d <= STALL_SECONDS or intended:
            continue
        if o.get("diagnostic") == "ML-PERSIST-TIMEOUT" and not any(case.startswith(x) or x in case for x in failed):
            continue  # a timeout inside a passing case is an intended fault wait
        near = [s for s in spikes if o["began"] - WINDOW_SECONDS <= s["monotonic"] <= o["ended"] + WINDOW_SECONDS]
        stalls.append(dict(module=Path(f).parent.name, case=case, kind=o["kind"], action=o["action"], step=o["step"],
                           seconds=round(d, 3), budget=round(o["end"] - o["began"], 3) if o.get("end") else None,
                           diagnostic=o.get("diagnostic"), began_monotonic=o["began"],
                           inside_probe_window=probe_start <= o["began"] <= probe_end,
                           matched_spikes=[dict(offset=round(s["monotonic"] - o["began"], 3), fsync_seconds=s["fsync_seconds"]) for s in near]))

inside = [s for s in stalls if s["inside_probe_window"]]
result = dict(run=str(run), probe=str(probe), probe_sha256=sha(probe), probe_summary=summary,
              stall_threshold_seconds=STALL_SECONDS, spike_threshold_seconds=SPIKE_SECONDS, window_seconds=WINDOW_SECONDS,
              operations=len(durations), stalls=len(stalls), stalls_inside_probe_window=len(inside),
              stalls_inside_window_with_spike=sum(1 for s in inside if s["matched_spikes"]),
              spikes=len(spikes), spike_seconds_max=max([s["fsync_seconds"] for s in spikes], default=0),
              stall_rows=stalls, temporal_association_only=True, causal_proof=False)
with output.open("x") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps({k: result[k] for k in ("operations", "stalls", "stalls_inside_probe_window",
                                          "stalls_inside_window_with_spike", "spikes", "spike_seconds_max")}))
