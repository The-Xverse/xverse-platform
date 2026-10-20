# Original private run registry and active control routing

Status: DRAFT refinement before code, finding283. Extends RUNTIME-0001–0003;
no acceptance, public execution admission or scientific scope change.

Retain one already-original `_OriginalRuntimeRun` before its first birth in a
private `_OriginalRuntimeRegistry`. Capacity is explicitly1–128, retaining the
bootstrap reservation cap. Never evict/reuse a terminal ID. A run claims exactly
one original registry; matching registration returns that original object without
new admission/time validation. Reject changed original objects, foreign/late
registration, closed launcher and capacity overflow before effects.

Ordinary lookup/start/collection/restart/controller-recovery require live original
registry identity and exact run identity. Store a separate immutable original
cleanup-only log before any birth. Independent stop may reach the same original
run through that log after ordinary map-reference loss; it cannot start, replace
an issuer, infer a PID, mint a permit or restore ordinary ownership. Lost cleanup
log rejects explicitly. Cancellation does not acquire the start/reservation lock.

Complete thin forwarding to existing dispatcher restart-many and explicit
controller replacement/results; retain native epoch, mutation coordinator,
fresh-generation permits, original requests and all existing safe-point rules.
No new restart execution path or implicit writer reopen is introduced.

Owned tests use separate explicit original bootstrap/permit scope. Verify genuine
controller replacement followed by productive work on an upfront admitted20s
active/3s recovery scope from the existing engineering design. This distinct
case does not repair, extend or waive original4.8s teardown findings135/222.
Current public approval/receipt/source-parent/facility/M1, full matrices/regression
and complete separate review remain gates. Python retains control composition;
native BS17/AFFA and accepted XDL/M3/Argus contracts remain unchanged.
