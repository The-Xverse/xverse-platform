# Original startup cleanup and private run controls

Status: partial implementation/verification with retained lifecycle failures.
[RUNTIME-0004](ADR-ML3-RUNTIME-0004.md) records the private registry allocation.
Public approved execution, complete M1/regression/review and stable17 remain open.

Startup cleanup/results now use original runtime/bootstrap/configuration pins
when ordinary session/broker/launcher aliases are lost. Ordinary access still
rejects. Original startup-a41881 has 11 pass/3 fail per phase: session/broker loss
needs 4 external fallback closures; launcher loss completes cleanup but loses 2
results. Finding 285 corrects the initial 282 fallback description. Successor
startup 14/14 controls pass per phase, retaining 12 primary results with zero fallback.
All 79 other production sources remain unchanged. Physical waits/C1 release never
supply missing normal evidence or workload ownership.

The private `_OriginalRuntimeRegistry` retains an original run before first birth,
claims it once and bounds capacity 1–128 without eviction/reuse. Matching registration
returns that run; changed/late/cross-registry registrations reject. Ordinary
start/collect/restart/recovery need the original map. Independent stop can use only
the separate original cleanup log after ordinary-map loss;lost cleanup log rejects.
No PID/path discovery,new execution permit,writer reopen or public export occurs.

Controller replacement followed by productive work retains original worker,
authority and writer and reaps both controllers. Its upfront 20s/3s engineering
scope does not extend old 4.8s findings 135/222.

| Attempt | Source / wheel | Retained result |
| --- | --- | --- |
| startup-a41881 |11 pass/3 fail each | Original alias loss;4 external fallback closures |
| controls-b85798 |22 pass /21 pass+1 fail | Startup 14 pass each;wheel recovery lifecycle fails |
| controls-c27856 |7 pass+1 fail /8 pass | Source nominal ML-PERSIST-TIMEOUT;physical cleanup confirmed |
| diagnostic-d3600 |2 pass each | One nominal/recovery probe per phase;no causal correction |

Audits23d94b/98d05c/81f4b5/bd1102 verify 28/36/16/4 absent owned reservations.
B retains 234 M3/Argus links and 3 durable closed roots; c: 224/3; d: 220/4. Original
failed audit a476c2 is preserved;v2 reads the same artifacts without native rerun.
The diagnostic probe records 266 RPCs, longest observed about 0.387s for init. It
neither establishes host timing bounds nor explains earlier failures. No further
unchanged retry is justified.135/222/286/287 stay UNRESOLVED;all effectiveness
statuses NOT_DEMONSTRATED. CAPA validates 20 records/88 bindings.

See [trace](evidence/affa17/runtime-controls-partial-traceability.json),
[CAPA](evidence/affa17/capa-20261019-runtime-controls/register.json),
[original failure](evidence/affa17/runtime-startup-faults-20261019a/verification-v2.json),
[partial successor](evidence/affa17/runtime-controls-20261019b/verification-v2.json),
[regression](evidence/affa17/runtime-controls-20261019c/verification-v2.json), and
[diagnostic](evidence/affa17/runtime-controls-diagnostic-20261019d/verification-v2.json).
Complete public approved admission, full constructor/active-control/runtime matrices,
24 requirements/18 source parents/30 pairs/90 endpoints/nine full cases/all seven
P3 tasks, M1/environment, regression and independent full review remain open.
No stable17 commit, acceptance, merge, canonical-note change,factory run or scientific
result follows from this partial scope.
