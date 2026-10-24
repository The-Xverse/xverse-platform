# Finite lifecycle dispatcher and supervised tick progression

ML3-SCHEDULER14-2026-10-18-v1; parent 4b1c427. Recorded before product code.
Thesis capability 024 remains authoritative; this increment is partial P3-T03/T04/T05.
All seven full P3 tasks and the full nine-phase Lite program remain binding.

Python composes the original ProcessReadiness, ReverseTeardown, BootstrapSession,
GateConnection and isolated persistence owner. Native wire/C sources and accepted
M3/Argus APIs stay unchanged. Add a typed pure ScheduleAdmission, closed worker-side
schedule journal/tick cursor and one original-holder FiniteDispatcher. No arbitrary
callback, command string or discovery becomes authority. Tick inputs are a finite
admitted sequence in the existing PreparedLifecycle TickDomain, executed/validated
in the original supervised storage worker. Repeated ticks are pauses. Host pacing,
health and lease deadlines remain separate; host time never invents simulation ticks.
The built-in sequence is a bounded tick source, not an external simulator adapter.

Admission rederives exact unit/policy sets, full step graph/windows, finite active
and operation/health/teardown/event/call bounds. Private protocol keeps version 1,
64 KiB framing and original credentials; an explicit hashed request limit may be
128..8192 instead of the legacy default 128. Legacy configurations keep their exact
shape/default. Client and worker independently rederive/validate schedule admission
before first Release and enforce its request/event caps. No silent cap increase.

Health starts before its next declared deadline, reserving a full finite scan.
Every intervening dispatcher operation is capped by that health/lease deadline;
late or unavailable observations close starts and initiate original cleanup. Poll
only within admitted host pacing; a paused tick cannot suspend health or leases.
Original root and individual gate leases renew separately before expiry, within
original generation and <=5 s. Gate renewal uses the existing native RENEW/RENEWED
exchange; a receipt cannot revive cancellation or manufacture a new scope.

Dispatch every admitted prepare/start/observe/stop/cleanup step using the prepared
combined graph, windows, durations and deterministic ties. Explicit scoped stop and
cleanup are separate normal phases, using the original live issuer/handle and C1;
retire stopped units from active health without authorizing restart. No dependent
may run against a stopped prerequisite. Final-horizon reverse cleanup is mandatory.

All schedule validation, tick completion, step dispatch/completion and terminal
failure/blocked/cancelled dispositions use the original sole storage worker, public
M3/Argus APIs and flush ACKs. Closed original active-step tokens gate requests;
worker rederives identities, clock/window/order and actual prior lifecycle sources.
A failed write stays a normal-record gap. After normal health/start failure, attempt
bounded factual failure/disposition records only while the original worker remains
usable; no cancelled start authority is reopened. Cleanup remains independent.

Return immutable step/unit execution facts separately from normal records, original
child waits, C1 cleanup and evidence coverage. Matching repeat returns retained
facts; changed scope rejects. Full helper/RunResult closure, restart/recovery, U7
provisional/offline assessment, U8 collection, full original admission/M1/runtime,
independent review and author acceptance remain open. No full lifecycle success or
experiment readiness is inferred. This increment composes already-issued original
resources; original external bootstrap/admission remains a separate obligation.

Keep all 24 ML-SR and 18 unvalidated/null-mapped REF-002 source parents, all 30
scenario pairs/90 declared endpoints and nine runtime cases. No factory run,
canonical-note edit, main merge, legacy execution or scientific parameter/result
change. Sol/high recommended for this lifecycle/concurrency step.

Note ST-1 (2026-10-24, ADR-ML3-SIMTIME-0001): `FiniteDispatcher` takes an optional trusted
`fault_clock_channel` (a `HubChannel`). When the prepared lifecycle carries a simulation-clock binding,
the Phase 5 scheduler slot holds a `SimTimeFaultScheduler`. That scheduler is polled once per tick
cycle without blocking, under the same `advance`/`cancel`/`finish` contract. A missing channel is
refused at begin (`ML-SCHEDULE-FAULT-CLOCK`). Host pacing, health, leases and the tick sequence are
unchanged; simulator time never drives Maestro ticks.
