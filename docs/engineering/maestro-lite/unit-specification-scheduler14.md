# Scheduler unit specification — before code

ScheduleAdmission is pure and immutable. Exact original prepared identity, policies,
finite monotonic tick values (zero and pauses allowed), horizon, host pacing and
bounded operation/active/teardown budgets are required. Reject bool/NaN/infinity,
rewinds, out-of-range clocks, missing units/policies, infeasible cadence, insufficient
request/event budgets and unsupported step phases before any Release. Canonical
serialization/digest are rederived independently by the original persistence child.

Worst-case admission includes existing committed calls, two Release revalidations,
all prior-unit and twice-transitive-prerequisite probes, all readiness attempts,
finite host health slots, explicit scheduled observations, four normal teardown
records per unit, step/disposition/tick records and terminal/abort reserve. Private
request sequence remains globally monotonic and bounded by the exact admitted cap.
Default unscheduled sessions retain 128 requests and exact legacy initialization.

FiniteDispatcher is an original-process holder pinned to the original facade,
bootstrap, gates/handles and schedule admission. No copying, new registry, changed
session or callback can create authority. Mutation lock conflicts reject promptly;
cancellation bypasses locks. Each tick first services required host health, dispatches
eligible work in actual combined order, then records tick completion. Dispatch and
completion enforce windows/durations. Positive readiness is required for start
completion and scheduled observe. Actual stop/cleanup phases precede their outcomes.

Host health/lease service is independent of tick progression. Cap every operation
by original active end and next health/lease end, reserving scan/renewal time. Missed
cadence/lease, dead issuer/provider, missing ACK, exhausted/rewound source or missed
window closes starts and initiates original reverse teardown within the original
reserve. Normal failure/disposition records never replace missing outcomes.

Verify actual owned two-unit start/dependency order, all five scheduled phases,
positive tick pauses/durations and automatic cadence, readiness/health loss,
blocked dependent dispositions, real tick/storage stalls, malformed reply and
clock/window violations, request/event admission/exhaustion, cancellation/conflicts,
normal/emergency reverse cleanup and matching repeats. Validate actual public
payload schema, clocks, M3 hashes/causation/normal gaps. Use installed wheel and full
platform regression; retain actual root/helper/worker reaping and unresolved controls.
