"""Summarize one benchmark run directory (S1-T01/T02): worker-side cost shares and client round trips by
decile of the run. Usage: python3 analyze.py RUN_DIR [--json OUT]. Read-only on the run directory."""

import argparse
import glob
import json
import statistics
from pathlib import Path

PARTS = ("argus.read_run", "outcomes.same_json", "outcomes.history", "m3.reload", "argus.append_event", "argus.flush_buffer",
         "argus.finalize", "argus.abort")


def _lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def summarize(run):
    run = Path(run)
    record = json.loads((run / "run.json").read_text())
    rpc = _lines(run / "rpc.jsonl")
    workers = sorted(glob.glob(str(run / "worker-*.jsonl")))
    worker = _lines(workers[0]) if workers else []
    load = [float(x["load"][0]) for x in _lines(run / "load.jsonl")] if (run / "load.jsonl").exists() else []
    out = {"run": run.name, "outcome": {k: record.get(k) for k in ("executionSucceeded", "cleanupComplete", "dispatchDiagnostic")},
           "units": record.get("units"), "horizon": record.get("horizon"), "load": {"max": max(load, default=None),
           "mean": round(statistics.mean(load), 2) if load else None}, "rpcCount": len(rpc),
           "rpcErrors": [r for r in rpc if r.get("error")][:5]}
    # FR-002 per-event metric: ordinary lifecycle/schedule calls; start-up and terminal calls have their own
    # budgets (start-up window; terminal-report and closure <= 2 s) and are reported separately.
    terminal_kinds = {"init", "terminal-report", "closure", "abort", "collect", "public-export", "public-blob"}
    out["terminalCallsMs"] = sorted(([r["kind"], round(r["durationNs"] / 1e6, 1)] for r in rpc if r["kind"] in terminal_kinds),
                                    key=lambda x: -x[1])[:8]
    durations = [r["durationNs"] / 1e6 for r in rpc if r["kind"] not in terminal_kinds]
    if durations:
        ordered = sorted(durations)
        out["rpcMs"] = {"p50": round(ordered[len(ordered) // 2], 2), "p99": round(ordered[int(len(ordered) * .99) - 1], 2),
                        "max": round(ordered[-1], 2)}
        n = len(durations)
        out["rpcDecileMeanMs"] = [round(statistics.mean(durations[i * n // 10:(i + 1) * n // 10]), 2) for i in range(10)]
        out["fr002"] = {"p99Ms": out["rpcMs"]["p99"], "maxMs": out["rpcMs"]["max"],
                        "lastMinusFirstDecileMs": round(out["rpcDecileMeanMs"][-1] - out["rpcDecileMeanMs"][0], 2),
                        "pass": out["rpcMs"]["p99"] <= 100 and out["rpcMs"]["max"] <= 250
                        and out["rpcDecileMeanMs"][-1] - out["rpcDecileMeanMs"][0] <= 50}
    out["durationS"] = round((record.get("monotonicEndNs", 0) - record.get("monotonicStartNs", 0)) / 1e9, 2)
    if worker:
        n = len(worker)
        deciles = []
        for i in range(10):
            chunk = worker[i * n // 10:(i + 1) * n // 10]
            if not chunk:
                continue
            handle = sum(w["handleNs"] for w in chunk)
            shares = {p: round(sum(w["parts"].get(p, 0) for w in chunk) / handle, 3) for p in PARTS if any(p in w["parts"] for w in chunk)}
            deciles.append({"events": chunk[-1]["events"], "meanHandleMs": round(handle / len(chunk) / 1e6, 2), "share": shares,
                            "readRunPerRequest": round(sum(w["calls"].get("argus.read_run", 0) for w in chunk) / len(chunk), 2),
                            "m3ReloadPerRequest": round(sum(w["calls"].get("m3.reload", 0) for w in chunk) / len(chunk), 2)})
        out["workerDeciles"] = deciles
        read = [(w["events"], w["parts"]["argus.read_run"] / w["calls"]["argus.read_run"] / 1e6) for w in worker
                if w["calls"].get("argus.read_run")]
        if len(read) > 10:
            xs, ys = zip(*read)
            slope = statistics.linear_regression(xs, ys).slope
            out["readRunMsPerEventRecorded"] = round(slope, 4)
        out["finalEvents"] = worker[-1]["events"]
        out["byKind"] = {}
        for w in worker:
            key = f'{w["kind"]}/{w["bodyKind"]}'
            item = out["byKind"].setdefault(key, [0, 0])
            item[0] += 1
            item[1] += w["handleNs"]
        out["byKind"] = {k: {"count": c, "meanMs": round(t / c / 1e6, 2)} for k, (c, t) in sorted(out["byKind"].items())}
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run")
    parser.add_argument("--json")
    args = parser.parse_args()
    summary = summarize(args.run)
    text = json.dumps(summary, indent=1)
    if args.json:
        Path(args.json).write_text(text + "\n")
    print(text)
