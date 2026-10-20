# ADR-ML3-RESTART-0003 — Explicit transitive cohort and released generations

2026-10-19. Selected engineering refinement before implementation; full17 remains
open. External v2 source remains DRAFT. This follows the delegated active-run choice.

Add restart_many(run_id, requests, *, deadline), where requests is a nonempty tuple
of (unit_id, exact sealed future permit, next generation). This is one explicit
control request, not automatic recovery or inferred restart scheduling. Normalize
the unique selected units by the original dependency order. One cohort may be
pending/in-progress; every member has its own original retained ticket/result.
Existing restart is the single-member API and retains matching repeat semantics.

Validate all members and all active transitive dependents before effects. A live
dependent outside the selection blocks the entire cohort without stop or permit
consumption. Allow an exact normally-cleaned prior generation as well as a live
released generation; require retained normal cleanup and authentic original issuer
revalidation. No emergency observation substitutes for normal prior release.

Quiesce selected units only, in reverse dependency order, retaining old stop/cleanup
results. Per selected unit stop+cleanup share one original per-unit teardown end,
also clipped by caller/active/health/lease ends; matching cached results are reused.
Then prepare/ADVANCE/Stage/start in dependency order with each member's sealed
restart cap and fresh dependency probes. Service health/leases between operations.
After a failure post-mutation, cancel monotonically; preserve completed member facts,
mark the failing member failed and unstarted members cancelled. No replay or rollback
of uncertain consumption. The original writer and all old/new generations remain.

If a restarted unit's original logical work is already complete, its new generation
still needs terminal teardown. At the horizon, or when an eligible declared parent
stop requires it, reverse-teardown such finished restarted units using original
normal authority. Do not add duplicate logical starts/stops. This terminal rule is
not used to grant a rejected restart request or stop an unselected live dependent.

Larger cohorts also require phase-specific operation bounds. Add an opt-in sealed
version4 schedule flag use_action_timeouts. Recompute and retain the complete
unit/phase timeout table from the original admitted catalog plans (positive <=5s).
Metadata, tick and health/lease service keep operation_seconds; phase effects use
their declared action bounds, clipped by the existing active/health/lease ends.
No prior version1/2/3 admission changes. Do not increase old failed-run deadlines.
This prevents a metadata RPC budget from silently becoming the whole multi-RPC
start/stop budget. The new fixture's larger active budget is frozen before birth
for its larger declared unit scope, not an extension of an old run.

Expected controls: actual three-node transitive generation2 with an unchanged live
unrelated handle; exact reverse quiescence/forward birth and fresh generation2
parent probes; omitted live descendant rejection; normally-cleaned single-unit
restart with correct horizon cleanup; loss during cohort retains partial facts;
old admission serialization, single-unit behavior and all full17 gates preserved.

Refinement after original transitive-b observations (finding218), before repair:
phase dispatch/completion statements are bounded operations of the declared phase,
including its multi-record durable evidence. In opt-in v4, use the original
unit/phase action cap for those statements as well as the phase effect. Each
operation still has one finite end, clipped by the caller's unchanged active,
health and lease ends. Tick, host-health, lease and run-level metadata retain
operation_seconds. This does not increase the whole phase's previously sealed
operation limit in an old version, reset a used deadline or change an action
timeout. Preserve b's source55/56 and wheel56/56 results; the actual successful
wheel execution does not erase the source timeout. Future evidence must explicitly
check the new statement end against the originally admitted action table.

Service ordering refinement after transitive-c finding220, before repair:
when health is due, reserve its admitted scan plus the existing renewal margin
against the current earliest lease. If that combined service cannot fit, renew
first, under the existing operation cap and old health deadline minus scan.
Recompute current leases after the authenticated renewal, then run the due
health scan. If either original end cannot be met, fail closed. Keep the same
finite service count, health freshness, renewal cap and active/generation ends.
The existing health-first path remains when there is admitted room for both.
This is service-order correction, not a fresh deadline or extra authority.

Safe-point refinement after transitive-c finding221, before repair: service
health/leases immediately before each original phase statement and phase effect,
not only before an aggregate loop iteration. An earlier successful operation
may consume the remaining margin. Each next operation obtains its own end only
after this safe-point service, clipped as before; no in-flight end is extended.
This applies to old versions too, retaining their exact sealed caps and clocks.

Cancellation preflight refinement before repair (finding238): an original queued
request whose monotonic latch is already cancelled when drain preflight begins
must be rejected before the mutation flag or any selected quiescence. Retain the
original request/result and ML-SCHEDULE-CANCELLED diagnostic, then let the original
dispatcher finish cancellation and teardown. A cancelled request with no resource
effect is not a failed post-mutation restart. Keep all later native/owner latch and
epoch checks; this early check does not claim to eliminate concurrent cancellation
between checks or authorize rollback/replay. Requests already mutated retain their
existing failed/cancelled member semantics.
