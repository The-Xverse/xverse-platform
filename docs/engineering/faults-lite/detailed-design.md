# Detailed design: Phase 5 deterministic fault injection (`xverse.faults`)

Planning authority: `distributed_safety_critical_thesis/specs/026-lite-fault-schedules/` (FR-001–
FR-010, V01–V12, contract rules 1–10; planning reviews 1–2, READY FOR DETAILED DESIGN). This
document maps the requirements onto platform code. It adds no requirement.

## Modules

| Module | Responsibility | Requirements |
| --- | --- | --- |
| `xverse.faults.vocabulary` | Closed vocabulary: six executable kinds, declared-only hooks, typed parameter schemas, the reserved parameter ids `arbitration` and `on-apply-failure`; `FaultError(code)` | FR-001 |
| `xverse.faults.resolve` | `resolve_schedule(plan, planned_ticks)` → `ResolvedEntry` tuple: kind, boundary class, target collection, due/effective ticks, exact `durationTicks`, tie key, arbitration, overlap check, horizon check; fail closed | FR-002–FR-004 |
| `xverse.faults.boundary` | `InjectionBoundary` protocol, `BoundaryHandle` (run id, entry id, nonce); `MessageRelayBoundary` and `ObservationRelayBoundary` (owned in-process relays); `ProcessBoundary` (wraps a Maestro launcher's owned handle and its new `fault` operation) | FR-006 |
| `xverse.faults.scheduler` | `FaultScheduler.advance(tick)`: application/clearing at planned ticks, arbitration (`serialize`, `supersede`), bounded retry, outcomes, blocked targets, cancellation; pure function of (plan, seed, ticks) | FR-003–FR-005, FR-008 |
| `xverse.faults.evidence` | Argus `annotation` events (`producerId xverse.faults`, extension `io.xverse.faults`), causation intent → applied → cleared, closure obligations | FR-007 |
| `xverse.maestro.projection` | admit plans with resolvable schedules; carry `faults` into `PreparedLifecycle` (canonical bytes and digest change only for such plans) | FR-009 |
| `xverse.maestro.dispatcher` | call `FaultScheduler.advance` after each tick statement; record intended termination before a `kill` | FR-006, FR-009 |
| `xverse.maestro.launcher` + `native/catalog_launcher.c` | new owned request kinds `FAULT_KILL=4`, `FAULT_FREEZE=5`, `FAULT_THAW=6` (reply `FAULTED=21`), verified like `QUERY` by child pid and token; `kill` = `pidfd_send_signal(SIGKILL)` on the owned child, `freeze`/`thaw` write `cgroup.freeze` on the owned cgroup and observe `cgroup.events` | FR-006 |

## Resolution rules (from the contract)

- Target collection → boundary class: `componentInstances` → `process` (through the unit of the
  Phase 3 projection, 024 FR-002); `flows` → `message`; `sensors` → `observation`. Other
  collections → `XVERSE-FAULT-TARGET`.
- `dueTick`: `time` → `trigger.atTicks`; `declared-order` → resolved at run time to the first
  planned tick after every lower order applied; `effectiveTick` = first planned tick ≥ due; due
  beyond the last planned tick → `XVERSE-FAULT-HORIZON`.
- `durationTicks` = compiled `duration.ticks` (exact); window = `[effectiveTick, effectiveTick +
  durationTicks]`; clearing at the first planned tick ≥ window end.
- Overlap on one target without the reserved parameter `arbitration` → `XVERSE-FAULT-OVERLAP`;
  `reject` → `XVERSE-FAULT-OVERLAP`; `serialize` → later entry waits; `supersede` → earlier
  entry cleared with outcome `cancelled`.
- Tie key `(declaredOrder or inf, faultId)`.
- No retry: compiled fault entries carry no `retry` field in Phase 1, so Phase 5 applies each
  entry at most once (a future bounded retry would re-enter arbitration per attempt).

## Outcomes and run status

`applied`, `cleared`, `failed-to-apply`, `incomplete-clearing`, `cancelled`,
`declared-not-executed`. `incomplete-clearing` sets `incomplete` and blocks the target.
`failed-to-apply` ends the run as a documented failure unless `on-apply-failure == continue`.

## Evidence

One `annotation` event per phase (`intent` at run open for every entry, then `applied`,
`cleared`, `apply-failed`, `clear-failed`), causation chained from the intent event, clocks host/
utc/simulation, extension `io.xverse.faults` = `{entryId, faultId, faultKind, boundaryClass, phase,
tick, effectiveTick, parameters, outcome, diagnostic, attempt}`. One `causal-closure` obligation
per applied entry; absence at close marks the run incomplete.

## Owned process operations

The Python launcher gains `fault(handle, operation, deadline)` with `operation in (kill, freeze,
thaw)`: holder and liveness checks, exact handle equality, request kinds 4/5/6, reply 21 with
`reason 0` (done) or `6` (refused: child gone, cgroup unsupported, write failed). The native
helper handles the three kinds after the same pid/token verification as `QUERY`; a refused
operation never kills or freezes anything else. Before a `kill`, the dispatcher records the
intended termination (`terminated-by-fault` expectation) so Phase 3's health and restart rules
attribute the death to the fault; while frozen, the unit's health expectations are suspended.

## Limits

Owned relays prove message and observation faults; live X-COM flows are Phase 6. `freeze` needs
the cgroup v2 boundary of the native launcher; otherwise `failed-to-apply`. Reproducibility covers
decision sequences only.
