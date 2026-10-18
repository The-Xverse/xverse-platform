# Recovery read-only findings

18 October 2026. Separate same-agent component inspection; independent full-candidate review remains pending. Record findings before successor repairs.

1. MAJOR durable-status inspection: a genuine staged handle with no journal sample
   or normal start outcome should return a consumed-intent cleanup-only row, not
   the same error used for a mismatched durable handle. Existing conflicting handle
   evidence still rejects. Never fabricate a normal handle record.
2. MAJOR concurrency inspection: the draft releases its own recovery lock before
   failure cleanup and result publication. Retain that one nonblocking lock through
   cleanup/cache publication while releasing original owner/view/root locks before
   RunClosure. Concurrent recovery must not start a second reconciliation.
3. MINOR input/lint inspection: explicitly reject non-persistence original owners
   before accessing their child, and replace the expected-count test lambda with a
   function. No product permission or timeout is expanded.
4. Clarification: snapshot is read-only for the durable journal and Argus. It also
   retires the worker's prior in-memory positive applicability at the new view
   epoch. Preserve started/handle/history and sample sequencing; no old positive
   may satisfy a dependency after reconstruction. Same host process retains its
   original host clock; this view epoch does not establish process/new-session
   recovery or M1 release-epoch enforcement.
5. MAJOR independent-budget inspection: client preflight reserves follow-up
   probes/terminal capacity, but the original worker must independently check its
   actual remaining RPC capacity before retiring readiness at a recovery epoch.
   Add that check using its own request sequence/cap. Exercise real original
   health RPCs to approach the legacy cap, rather than changing a client counter.
6. MINOR measured fixture finding: focused-v2 passes 94 checks but the genuine
   126-call capacity control reaches ML-BOOT-CLOSED while filling its health RPCs.
   Durable mirror verification makes that fill outlive the original 4.9-second
   root lease. Exercise existing exact root/gate renewals during this bounded test
   fill; do not change product lease/operation maxima or alter counters. Retain
   the failed run, then verify both-side capacity rejection with live issuers.

Final separate read-only product pass after focused-v3: inspected recovery, worker
reconciliation, owner/provider retirement, persistence RPC and all 31 recovery cases.
Findings 1–6 are repaired; focused-v3 passes 97 checks. No additional product finding
in this pass. Full source/wheel, trace and cleanup audits remain required. This is
same-agent component review; independent full-candidate review remains pending.

7. Measured full-regression finding, before any response: full-v1 returns 1 failed/
   1223 passed/24 subtests. The nested unchanged-platform replay alone fails the
   inherited 40-paused-tick nominal test; the outer source copy and installed wheel
   pass that same test. Retained nested M3 facts run from 17:52:47.768 schedule begin
   to 17:52:55.524 final cleanup intent (7.756 s) inside its declared 8-second active
   horizon, with no final cleanup outcome. The source and wheel suites were running
   concurrently. All 1098 fixture roots are absent and the full evidence audit
   otherwise passes. This does not prove a new recovery defect or justify increasing
   product/fixture bounds. First re-exercise the affected unchanged test alone and
   inspect whether a serialized full-source replay can satisfy the same exact inputs.
   Preserve the failed full run and every receipt; do not call it passing.

Finding7 response: the unchanged paused-tick test passes alone (1 check, 9.00 s,
original session40660). Repeat the full source suite without simultaneous wheel
load; keep the actual passing wheel suite after rechecking every installed module
and unchanged product/test/native inputs. No product or fixture timeout is relaxed.
Revisionv2 changes this review, freezing metadata and a new serial driver only.
The concurrent failure remains a measured host-load/timing limitation, not erased.

8. MAJOR confirmed scope/budget finding before repair: serialized-v2 completes with
   1 failed/1223 passed/24 subtests. Only the outer closure/dispatcher integration
   fails (ML-PERSIST-TIMEOUT); both paused-tick copies pass. Retained M3 facts and
   source inspection in serial-failure-inspection-before-repair.md show an explicit
   observe-source performing both source and sink probes under one unit's end.
   Add exact-unit observation and use it for the declared observe step. Preserve
   periodic all-unit health, all operation/fixture/lease bounds and conservative
   admitted scan/event budgets. Add real two-unit scope and conflict controls.
   Serialization alone did not establish stability; retain both failed full runs.

Final separate read-only successor pass after finding8: inspected exact-unit
validation, original holder/lock/freshness checks, durable probe/cancellation paths,
dispatcher target binding and unchanged periodic all-unit service. Both new controls
fail for the expected scope/API reasons before code and pass afterward. Combined
focused-v4 passes117 checks in160.52s (actual terminal session79757). No additional
product finding in this pass. Full source and installed-wheel regressions remain
required for v3; no passing v1/v2 wheel evidence is reused for the changed product.
The full v3 source/wheel jobs are scheduled sequentially; all product/fixture bounds
are unchanged. Independent full-candidate review and acceptance remain pending.
