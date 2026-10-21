# ADR-ML3-BUDGET-0001: Load-aware interior time allocation inside hard admitted bounds

Status: SELECTED ENGINEERING REFINEMENT BEFORE IMPLEMENTATION (2026-10-21; agent decision E1 under
the author's delegation, review-affa19.md finding 476; scope finding 477). Not accepted.

## Context

F-08/F-09 (findings 427-438, 467-469): interior deadlines are fixed. Each effect, quiesce and
non-lazy terminal phase receives `min(outer bound, now + operation_seconds)` (or `per_unit_seconds`
in the terminal `run()`), and `ReverseTeardown.phase()`/`run()` give the normal path 0.6 of that
window for several persistence records plus process work. Under host load the round trips grow two
to five times, the normal share runs out while the outer bound still has seconds of slack, and the
run ends with ML-SCHEDULE-TEARDOWN-INCOMPLETE (emergency, units unresolved) or ML-PERSIST-TIMEOUT
(channel failed, terminal records lost). The v2 guard (f4262c285) converts some of these into
refusals but does not remove them (469).

## Decision

1. **Outer bounds stay hard and unchanged:** admitted active end, `_work_end`/terminal deadline,
   drain, bootstrap and gate leases, generation bound, health-slot capacity, lease-renewal rules,
   the terminal report window (`terminal_seconds`), declared action timeouts
   (ADR-ML3-RESTART-0003, "clipped by the existing ends"), and every sealed admission field.
2. **One per-run service-time estimator** (`service_time.ServiceTimes`, lifetime maximum per kind,
   the statistic v2 already uses), shared by the dispatcher and its teardowns. Kinds: the statement
   kinds, `teardown-record`, `phase:stop`, `phase:cleanup` (success spans; failed or refused spans
   recorded as lower bounds), `restart:unit`. A kind not yet seen estimates 0, as in v2.
3. **M2, widening only.** At effect stop/cleanup, quiesce, non-lazy terminal phases and the
   terminal `run()`, the interior deadline becomes
   `max(today's deadline, min(now + need + 0.4 w0, cap))`, with `need = 1.5 x sum of the phase
   estimates` and `cap` = the outer bound minus the reserve still needed by later work, the next
   health deadline minus scan and renewal margin, and every live lease minus renewal margin. It is
   never earlier than today's deadline and equals it whenever the need fits in today's normal
   share, so a quiet host sees today's deadlines. Inside `phase()`/`run()` the admitted budget
   becomes a floor of the normal share instead of a cap, and the 0.4 emergency share is kept.
   Not widened: start/observe effects and `_restart_unit` (their ends also bound readiness waits),
   active-phase statements (their limit is the window itself), terminal statements, health scans,
   renewals, collection, the report, and the dispatcher deadline of anything under declared action
   timeouts (inside such a deadline the teardown's normal share may grow up to, never beyond, it;
   finding 480 (5)). The terminal `run()` window is also capped by `teardown._deadline`'s 80 s, the
   boundary teardown deadline and, in the non-lazy profile, the live leases themselves; in the lazy
   profile the terminal records renew the lease, so no lease cap applies (findings 480 (1), 482 (1)).
   The general lease-minus-margin and health caps above apply to active-phase deadlines, where
   renewals and scans happen between operations; they do not apply to the terminal window. The
   lease rule is a property of the dispatcher's terminal window, not of `ReverseTeardown.run()`,
   which a closure path may call with its own deadline (finding 484 (3)). Known conservative
   bias: M1 checks stop plus cleanup against one normal share (finding 484 (2)).
4. **M1, decisions before mutation** (estimate x 1.0, no floor): a stop or cleanup step-dispatch
   whose estimated dispatch plus phase spans no longer fit before the active end is refused with
   the existing ML-SCHEDULE-SERVICE-DEADLINE, so the run ends through normal terminal teardown as a
   documented failure (finding 475); a restart whose estimated quiesce plus restart spans do not fit
   before `min(ticket deadline, active end)` is rejected with the existing
   ML-SCHEDULE-RESTART-DEADLINE before any mutation; a finished-restart quiesce that does not fit is
   left to terminal cleanup instead of failing at the active end.
5. **v2 is kept** as the last pre-send check, reading the shared estimator.
6. **Observability:** a refused teardown record keeps ML-TEARDOWN-RECORD-BUDGET as the
   `UnitTeardown.diagnostic` (finding 474 item 3); the dispatcher code stays
   ML-SCHEDULE-TEARDOWN-INCOMPLETE. An observation-only interior trace records each widening and
   each M1 stop (site, kind, remaining, estimate).
7. **No new diagnostic code, RPC, wire field, admission field or sealed knob.** The margins (1.5
   sizing, 1.0 decision) are module constants of this engineering refinement.

## Consequences

- At high load, active-window exhaustion is an outer bound and still ends runs; the expected
  change is fewer persist timeouts and emergency teardowns and more finalizable documented
  failures, not more successes.
- Deadlines inside the outer bounds now depend on timing observed in the run; every one is
  bounded above by the outer bounds and below by today's value.
- Risks: false M1 stops in fixtures with almost no margin; widening on a quiet host if a quiet
  phase span exceeds today's normal share (to be measured, not assumed); designed-stall tests reach
  their emergency later only when estimates are already large.

## Verification (finding 477)

Deterministic seeded controls for each site; the existing F-08/F-09 controls and T3 unchanged; the
affected modules on a quiet host with the interior trace showing whether any widening or stop
occurs; an interleaved A/B under natural external load against the head without this change, with
expectations recorded first. Independent review before any acceptance proposal.
