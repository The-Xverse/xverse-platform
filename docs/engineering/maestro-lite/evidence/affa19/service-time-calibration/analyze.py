#!/usr/bin/env python3
"""Summarize rpc_timeline_plugin records (finding 437/438). Usage: analyze.py <out.json> <run-dir>...

Per request type (kind, action): count, service-time quantiles, sent-budget quantiles, failures, and
the smallest observed margin (budget - service) of successful requests; also how often a request was
sent with a budget below the type's own p99 service time. Observation only.
"""
import json, sys
from collections import defaultdict
from pathlib import Path

def q(values, p):
    values = sorted(values)
    return values[min(len(values) - 1, int(p * (len(values) - 1) + 0.5))] if values else None

rows, loads, files = defaultdict(list), [], 0
for directory in sys.argv[2:]:
    for path in sorted(Path(directory).glob('*.json')):
        data = json.loads(path.read_text()); files += 1; loads.append(data['load'])
        for r in data['records']:
            rows[(r['kind'], r['action'] or '-')].append(r)
summary = {}
for (kind, action), rs in sorted(rows.items()):
    service = [r['service'] for r in rs if r['diagnostic'] is None]
    budget = [r['budget'] for r in rs]
    p99 = q(service, .99)
    summary[f'{kind}/{action}'] = dict(
        n=len(rs), failed=sum(r['diagnostic'] is not None for r in rs),
        diagnostics=sorted({r['diagnostic'] for r in rs if r['diagnostic']}),
        service_ms={k: round(1e3 * q(service, p), 2) if service else None
                    for k, p in (('p50', .5), ('p90', .9), ('p99', .99), ('max', 1.0))},
        budget_ms={k: round(1e3 * q(budget, p), 1) for k, p in (('min', 0), ('p01', .01), ('p50', .5))},
        min_success_margin_ms=round(1e3 * min(r['budget'] - r['service'] for r in rs if r['diagnostic'] is None), 2) if service else None,
        sent_below_own_p99=sum(r['budget'] < p99 for r in rs) if p99 else None)
allservice = [r['service'] for rs in rows.values() for r in rs if r['diagnostic'] is None]
out = dict(files=files, load_min=min(loads), load_max=max(loads), requests=sum(map(len, rows.values())),
           all_service_ms={k: round(1e3 * q(allservice, p), 2) for k, p in (('p50', .5), ('p99', .99), ('p999', .999), ('max', 1.0))},
           by_type=summary, observational_only=True)
Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + '\n')
print(json.dumps({k: v for k, v in out.items() if k != 'by_type'}, indent=1))
for k, v in summary.items():
    print(f"{k:40s} n={v['n']:5d} fail={v['failed']:3d} svc p50/p99/max={v['service_ms']['p50']}/{v['service_ms']['p99']}/{v['service_ms']['max']} "
          f"budget min={v['budget_ms']['min']} margin={v['min_success_margin_ms']} below_p99={v['sent_below_own_p99']}")
