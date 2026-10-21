#!/usr/bin/env python3
"""Offline replay of candidate refusal rules on rpc_timeline_plugin records (finding 438).

For every recorded request, each rule decides from information available before the send whether
it would refuse (budget < threshold). A refused request that in fact succeeded is a false refusal;
a refused request that in fact timed out (ML-PERSIST-TIMEOUT/-SENDER/-LATE) is a prevented timeout.
The full-budget candidate of 8184a2b15 is not replayable here (recorded budgets are already clipped
by every term); the A/B of finding 434 evaluates it. Replay ignores downstream effects of a refusal, so it estimates rates; it proves nothing about runs.
Usage: replay.py <out.json> <run-dir>...
"""
import json, sys
from collections import defaultdict
from pathlib import Path

LATE = {'ML-PERSIST-TIMEOUT', 'ML-PERSIST-SENDER', 'ML-PERSIST-LATE'}
tests = []
for directory in sys.argv[2:]:
    for path in sorted(Path(directory).glob('*.json')):
        data = json.loads(path.read_text())
        tests.append((path.name, data['load'], sorted(data['records'], key=lambda r: r['began'])))

def rules():
    yield 'none', lambda prior, r: 0.0
    for factor in (1.0, 1.5, 2.0):
        yield f'max-prior-same-type-x{factor}', (lambda f: lambda prior, r: f * max(prior[(r['kind'], r['action'])], default=0.0))(factor)
    yield 'last-same-type-x2', lambda prior, r: 2 * (prior[(r['kind'], r['action'])][-1] if prior[(r['kind'], r['action'])] else 0.0)

out = {}
for name, rule in rules():
    false_refusals = prevented = late_total = sent = 0
    examples = []
    for test, load, records in tests:
        prior = defaultdict(list)
        for r in records:
            threshold = rule(prior, r)
            refuse = r['budget'] < threshold
            late = r['diagnostic'] in LATE
            late_total += late; sent += 1
            if refuse and r['diagnostic'] is None:
                false_refusals += 1
                if len(examples) < 5: examples.append(dict(test=test, kind=r['kind'], action=r['action'],
                                                           budget=round(r['budget'], 4), threshold=round(threshold, 4)))
            if refuse and late: prevented += 1
            if r['diagnostic'] is None: prior[(r['kind'], r['action'])].append(r['service'])
    out[name] = dict(requests=sent, late=late_total, prevented=prevented, false_refusals=false_refusals,
                     false_refusal_examples=examples)
    print(f'{name:28s} requests={sent} late={late_total} prevented={prevented} false_refusals={false_refusals}')
Path(sys.argv[1]).write_text(json.dumps(dict(tests=len(tests), rules=out, observational_only=True), indent=1) + '\n')
