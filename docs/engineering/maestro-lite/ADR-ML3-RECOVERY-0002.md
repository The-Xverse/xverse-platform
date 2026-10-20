# Explicit active controller recovery under the original coordinator

2026-10-19. Engineering refinement before implementation of finding223. Original
ML-DESIGN-2026-10-03-v2 remains DRAFT; full increment17 is open. The delegated
blocking-run lifecycle choice remains. Existing standalone recovery is preserved.

Add opt-in allow_controller_recovery to the finite dispatcher and explicit
replace_controller(run_id, session_id, deadline) request/result tickets. One shared
control slot serializes restart cohorts and controller replacement. Exact repeated
requests return original tickets without replay. Bound the request by the original
active end and unused originally admitted controller-session budget. The original
coordinator drains the request at phase safe points before an old heartbeat; no
lost helper can race a queued replacement into an inferred automatic restart.

Add an optional sealed version5 recovery_operation_seconds. Preserve all old
serialization and deadlines. The cap is finite <=5s, active budget and cadence minus
one admitted health scan. It must accommodate original recovery's conservative
(1+2*n)*0.25s query/snapshot budget plus one metadata operation before mutation.
Runtime additionally clips the fixed end by actual health/lease/caller limits.
Reserve bounded extra RPC/event/health capacity per unused admitted controller.

Before helper mutation, renew through the original broker without consulting the
possibly dead controller, and obtain fresh original health samples. This is a
separately reserved scan; it cannot stretch freshness or a used deadline. Retire
only the original current controller using its original pidfd, parent wait and
own C1 release. Admit a genuinely new controller/session through original BS17.
Storage, authority, workload handles, permits and writer stay original.

IssuerRecovery accepts a private borrowed reservation only from the exact original
active dispatcher, original request and current successor, on its coordinator
thread. It never clears that reservation. Existing standalone conflict behavior
and reservation ownership remain unchanged. Reconcile current durable handles and
consumption, invalidate old positive views, create the genuine fresh readiness
view, and probe actual current generations. A normally-cleaned prior generation
may stay nonrunning only with exact original normal cleanup. No recreated handle,
PID/path adoption, permit minting, writer reopen or old-session reuse.

Only the validated transition commits the new facade/controller/binding pins and
a new ReverseTeardown retaining all current normal caches and historical teardown
objects. The original mutation owner remains reserved through terminal closure.
Subsequent productive work, including explicitly requested generation2, uses the
original broker and authenticated current reconciled controller.

Failure cancels monotonically. Nested recovery never closes the entire supervisor
under the borrowed reservation; the original dispatcher/RunClosure owns that job.
If views have been retired before failure, retain a genuine new cleanup-only view
from the original recovery object. It has no new positive readiness; if reconciliation
never succeeded, it has no bindings or released/attempted units. This view exists
only to let reverse teardown address the original owner's issued registry/C1.
It cannot start/restart/adopt, and the unreconciled controller plus cancellation
keep starts closed. An authentic reconciled view whose final fresh probes fail is
also usable only for cleanup. Record failed recovery separately from physical
cleanup and missing normal evidence. No fixture may assign replacement pins.

Predeclared controls: live planned handover; external-thread queue followed by
actual current-helper death before drain; exact generation2 handles survive
replacement; successful explicit productive restart after replacement; missing
snapshot/storage failure retains cleanup-only scope; forged/repeated/conflicting
requests and foreign borrowed reservations reject. Retain original pre-execution
admission/schedule/collection pins and independent closed recomputations, exact
source/wheel inputs and original wait/root facts. Old4.8s finding222 and135 remain
open; these new controls do not replace or waive them. No scientific result,
factory dispatch, acceptance, main merge or stable17 claim is authorized here.

Refinements recorded before successor repairs (findings225–227): worker snapshot
adds a distinct released row only for its own exact current generation/handle,
completed normal stop+cleanup state and original cleaned M3/mirror proof. It does
not confer running or ready credit. The host also requires actual nonrunning
native QUERY and the independently retained original normal-release predicate.
An empty failure view cannot require storage liveness. Its private constructor
capability must authenticate the original active borrowed recovery and cancellation,
keep ordinary constructors unchanged, and explicitly block bind/start/probe.
The same exact completed restart remains an inert repeat, so a conflict control
must select a different unspent original context. Preserve the first failures.

Observed storage-loss distinction (finding229): when the original authority has
confirmed the already-issued workloads' direct waits and retirement, physical
cleanup may complete even though recovery and normal evidence fail. The earlier
unknown-issuance case cannot determine this outcome. Preserve the original actual
wait facts and require failure of ordinary recovery/normal lifecycle evidence;
never force cleanup to unknown when its independent facts are confirmed.

Queued heartbeat race refinement before code (finding230): if the old heartbeat
fails after an explicit matching replacement was queued, the original coordinator
may drain that pending request before ordinary run cancellation, provided the
monotonic latch is still clear. Successful replacement already renews the original
broker lease and probes current units; return from the old renewal operation
without replaying its expired end. A rejected/failed replacement or absent request
retains the original failure/cancellation. New native race control queues from an
external thread and actually kills the original helper inside its due heartbeat.

Complete normal frontier before successor repair (findings231–233): owned/running,
normally-stopped, normally-released, never-issued and mixed states are distinct.
A stopped current generation needs its original normal stop M3/mirror plus actual
C1 empty/native wait facts. Keep its normal stop cache and finish cleanup after
handover; do not grant ready or already-released credit. A borrowed empty registry
may reconcile only when every original issuer/claim and worker row is genuinely
never-issued; ordinary standalone empty recovery still rejects. Define the expected
frontier before the loan from the current-generation original durable records.
The same fixed recovery/health/lease ends apply to every normal frontier. Retain
the typed original reconciliation result in receipts. A heartbeat race may land
after productive phases have ended; its requirement is authentic handover and
normal original closure, while separate controls prove subsequent real work.
