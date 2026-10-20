# U3 original-worker monitoring unit specification

Revision: ML3-SUPERVISION3-2026-10-18-v3. Status: partial candidate.
Basis: U3, detailed design D3–D6; descriptor contract C04/C08 authority limits.
Numbers are bounded engineering test inputs, not scientific thresholds or measured guarantees.

| Endpoint | Invariant | Verification measure |
| --- | --- | --- |
| `WatchLimits` | Strict finite positive limits; no bool/NaN/infinity; operation ≤5 s, TERM/KILL waits ≤5 s, poll ≤50 ms | Parameterized denial; no child effect |
| `CancellationLatch.cancel` | Irreversible close, epoch 0→1 once; bounded redacted reason; no worker/coordinator callback or lock | Repeat/concurrent cancel; independent blocked child |
| `WorkerMonitor.retain` | Exact original direct-child Popen in original parent, pidfd and wait ownership retained; unique object/worker reference; deadlines fixed at retain | Real child, forged/subclass values, dead/reaped child, repeated registration |
| `WorkerMonitor.watch` | No callback/output read/Popen wait; monotonic deadline and cancel independent of blocked worker | Actual blocked provider/storage/tick fixture, paused simulation, ignored TERM→KILL |
| TERM/KILL and reaping | Signal only retained pidfd; nonblocking exact-child wait; never broaden targeting | Unrelated sentinel remains live; failed signal/wait stays unresolved |
| Cached outcome/authority | Original registry object and PID required; matching repeat gets same snapshot; uncertainty retains FD, no deadline extension | Copy, fork holder, late reply, stolen wait ownership, injected observe/signal error |
| Public outcome | No raw PID/FD/command/nonce; no lifecycle readiness, containment completeness or normal M3 success inferred | Immutable value and explicit false flags |

Fixture helper processes are owned software-component tests. They do not implement
M1/C1, grant bootstrap approval, prove descendant containment, authenticate approvals,
or close the nine full-ML3 runtime cases. Separate read-only review must record findings
before repairs. Verify the exact wheel outside source and owning-platform regression.
