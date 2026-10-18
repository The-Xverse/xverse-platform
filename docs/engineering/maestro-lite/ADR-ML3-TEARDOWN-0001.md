# Distinct normal stop and cleanup with reverse unit teardown

ML3-TEARDOWN13-2026-10-18-v1; parent f292416. Recorded before product code.
Python composes existing original native Query/wait and C1 control APIs; native
launcher wire and accepted M3/Argus implementations remain unchanged.

Add C1 terminate-and-retain and empty-boundary-release operations, each original
capability checked with an explicit HostDeadline and nonblocking mutation entry.
Keep emergency force_cleanup compatible, optionally accepting the original caller
end. Empty/frozen C1 never implies direct-child reap or released boundary. Normal
stop requires a live original issuer's full-handle Query with actual leader reaping
and an original empty/frozen C1 observation. Normal cleanup requires a separate
intent before actual empty-boundary removal and confirmation of original release.
The admitted original C1 authorizes force termination; no new force scope is minted.
This component does not add an arbitrary graceful application stop callback.

ReverseTeardown uses the original prepared combined graph, exact original launcher
registry and retained registered C1 capabilities. It serializes with the facade and
owner, irreversibly closes local new-start admission, and visits issued units in
reverse dependency order with compiler rank/full identity tie breaking. Stop and
cleanup intent/outcome records are written by the existing isolated storage child
through accepted public journal/Argus APIs and flush acknowledgements. Stage-only
resources may be stopped without inventing a successful start. Changed/forged
handles, missing issuer and lost C1 never permit adoption.

An exact typed active-step registry binds client storage requests and observed
results. The worker checks genuine claims, fixed original handle, reverse-dependent
normal cleanup, phase order and retained public journal/mirror history. Pending
intents use action=intent/outcome=pending, anchored by the exact catalog M3 action;
normal stop/cleanup outcomes use their corresponding payload action. Schema v2.0
and accepted Argus envelope remain unchanged. Public receipts are not capabilities.

Each per-unit window reserves 40 percent for emergency cleanup after a bounded
normal attempt. A failure closes the shared latch, then original C1 cleanup is
attempted for every remaining unit, with explicit missing-normal-record and
unresolved child-reap facts. Other owned cleanup continues under the original total
end, never a renewed timeout. Kernel scheduling/control I/O stalls remain external
supervision limits, not hard-real-time guarantees. Matching repeated calls return
retained facts; changed reason/scope rejects. Cancel remains independent of normal
locks. A normal successful local barrier is not full M1/global cancellation proof.

Full helper shutdown, automatic scheduling/health/ticks, failure/disposition/restart/
recovery, dual coverage/U8, admission/G1/G3/G4/G5 and nine runtime cases remain open.
All 24 ML-SR and 18 allocation-only unvalidated source parents remain represented.
This supports ML-SR-010/011/012/013/016/018/019/022/024 partially; no full requirement
closure or acceptance. No main, legacy, scientific or canonical-note change.
Sol/high recommended for lifecycle/authority; cheaper models suit receipt handling.
No factory run; external thesis 024 governs, main default prerequisite resolves
unrelated 020; no extension hooks. Keep all seven full P3 tasks open.
