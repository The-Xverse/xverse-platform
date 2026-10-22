# Thesis Lite Phase 5 (deterministic fault injection) — engineering review log

Branch `candidate/faults-lite-20261022` from platform main `744b66f9c`. Planning package
(authoritative): `distributed_safety_critical_thesis/specs/026-lite-fault-schedules/`. Findings are
numbered and recorded before any repair. No legacy artifact executes; no factory run.

1. Planning package written (2026-10-22): spec (FR-001–FR-010, V01–V12, decision D5-2), plan,
    research, data model, execution contract, quickstart, tasks. Planning review 1: NOT READY
    (H1 durations are already exact compiled ticks; M1 `arbitration`/failure policy are not
    Profile keys, now reserved typed parameter ids; M2 `kill`/`freeze` are native containment
    paths only, so Phase 5 adds owned `kill`/`freeze`/`thaw` operations with Phase 3 transitions;
    M3 the dispatcher iterates the planned tick list, so a planned-tick effect rule was added; M4
    V11/V12 added). All verified against the platform before repair; review 2 requested. Code for
    T02 onward waits for its verdict.

2. Planning review 2 (2026-10-22): READY FOR DETAILED DESIGN; DRAFT; NOT READY FOR
    IMPLEMENTATION. One LOW carried into the design: a bounded retry re-enters arbitration and
    emits a fresh apply-failed/applied pair per attempt (one final outcome per entry). Detailed
    design and unit specifications follow in docs/engineering/faults-lite/.

3. P5-T01 increment (2026-10-22): `xverse.faults.vocabulary` (six executable kinds, declared-only
    hooks, typed parameter validators, reserved ids) and `xverse.faults.resolve` (boundary class
    from the target collection, due/effective/clear ticks over the planned tick list, exact
    compiled durations, tie keys, overlap arbitration, horizon), with `tests/thesis_lite/faults/`
    (fixture builder over the Maestro fixture graph plus a sensor; U-FLT-01…10). Facts learnt from
    the Phase 1 validator and corrected in the design and the thesis package: parameter ids must
    be kebab-case identifiers (`delay-ticks`, `loss-ratio`, `every`, `copies`, `window`,
    `arbitration`, `on-apply-failure`), and a declared-order fault-intent must not carry a
    `timeDomainId`. Result: 10 passed (pure Python, PYTHONPATH run; worker-side changes come later
    with a candidate venv).

4. P5-T02/T04 increment and the relays of T03 (2026-10-22): `xverse.faults.boundary` (exact
    handles per run and entry; `MessageRelayBoundary` with delay/loss/stale, `ObservationRelayBoundary`,
    `ProcessBoundary` over an owned operation set with the intended termination recorded before a
    kill; `CounterGenerator`, seeded and counter-based), `xverse.faults.scheduler` (clearing then
    application per planned tick, `(declaredOrder or inf, faultId)` order, serialize/supersede
    arbitration, blocked targets, cancellation, one final outcome per entry, run failure per
    `on-apply-failure`), `xverse.faults.evidence` (Argus annotation events with the
    `io.xverse.faults` extension chained intent → apply → clear → outcome; offline
    `reconstruct`/`closure_report`). Tests U-SCH-01…09, U-BND-01…05, U-EVD-01…03 plus scheduler
    guards: 28 passed. Design notes: Argus's `causal-closure` obligation is run-level (every
    causation id resolves), so per-entry closure is checked by `closure_report` offline and by the
    scheduler's `incomplete` flag, not by one obligation per entry (the contract's rule 7 is met
    by the pair; recorded for the thesis package); compiled entries carry no `retry` field, so no
    retry happens in Phase 5 (the review-2 LOW on retry is moot until Phase 1 exposes it).
    Process faults still act on fakes here; the owned native operations follow.

5. P5-T03 owned process operations (2026-10-22): `native/catalog_launcher.c` gains request kinds
    FAULT_KILL=4, FAULT_FREEZE=5, FAULT_THAW=6 and reply FAULTED=21, verified by child pid and
    token exactly like QUERY; `owned_fault` acts only on the helper's own staged child (SIGKILL
    through the owned pidfd; `cgroup.freeze` on the owned cgroup with `cgroup.events frozen`
    observed within a bounded wait) and answers reason 6 without acting when the child is gone,
    the cgroup cannot be written or the state is not observed. `launcher.py`: `LaunchPacket`
    accepts the new kinds, `_rpc` takes `allowed_reasons` so a refusal is an answer rather than a
    protocol failure, and `CatalogLauncher.fault(handle, operation, deadline)` returns
    `(done, reason)` after the holder, liveness and exact-handle checks. Native tests
    `tests/thesis_lite/faults/test_process_ops.py` on the Maestro launcher stack (real helper
    compiled from the worktree source, real child in an owned cgroup-v2 boundary): freeze observed
    (frozen 1), thaw (frozen 0), kill reaped with returncode -9; kill and freeze after exit refused
    (reason 6); forged handle and unknown operation refused before any request. 3 passed (plus
    the 28 pure-Python tests). The test process imports the worktree source; the persistence
    worker runs the installed main package, which this increment does not change.

6. P5-T03/T06 Maestro integration (2026-10-22; one installed version, venv /dev/shm/p5-venv built
    from this tree). Projection: the Phase 3 `ML-UNSUPPORTED` rejection is replaced by
    `validate_static` (dense ticks 0..horizon; a crash with XDL recovery other than `manual` is
    refused while D5-2 is open); resolvable schedules are frozen into `PreparedLifecycle.faults`
    with `fault_seed`, and only then enter the canonical bytes (fault-less plans keep their bytes
    and digests). Dispatcher: `_begin_faults` resolves against the planned ticks, builds one
    boundary per target (process boundaries over the unit's launcher, relays for flows and
    sensors), sends one `fault` intent statement per entry and starts the scheduler;
    `_advance_faults` runs after each tick statement; `_finish_faults` at the horizon; a refused
    application ends the run as `ML-SCHEDULE-FAULT-APPLY`, an incomplete clearing as
    `ML-SCHEDULE-FAULT-INCOMPLETE`. Worker: `ScheduleJournal` accepts a `fault` statement and
    writes one annotation event under producer `xverse.faults` (extension `io.xverse.faults`,
    correlated to the entry's intent, chained by causation); the parent validates the reply
    exactly (`_validate_fault_reply`); coverage ignores fault events; the schedule budget adds
    five statements per entry. Facade: `suspend_health`/`resume_health` while frozen;
    `terminate_by_fault` records the intended termination before a kill, and a later health
    check ends the run as `ML-PROBE-TERMINATED-BY-FAULT`. Native run authority (the path the
    live stack uses; the catalog launcher of finding 5 is the other path): request kinds
    FAULT_KILL=13, FAULT_FREEZE=14, FAULT_THAW=15 on the exact registered generation, replies
    FAULTED=29 or FAULT_REFUSED=30; the receive loop's kind bound was raised from 12 to 15
    (first run failed with `ML-AFFA-SENDER`/`ML-BOOT-CLOSED` because the authority closed on an
    out-of-range kind: recorded, then repaired); `RunUnitIssuer.fault` on the client side.
    Packaging: `src/xverse/faults` added to the wheel force-include (it was missing from the
    first wheel). Tests: `test_maestro_run.py` (U-ADM-01…03; end-to-end on the native stack:
    stale + sensorDropout + freeze/thaw complete with closed Argus chains; a crash before the
    unit's health obligation ends the run attributed to the fault; a crash after it completes
    with the termination recorded). Result: tests/thesis_lite/faults 37 passed.

7. Implementation review 1 (2026-10-22, independent read-only; 37 Phase 5 tests passed in its
    run): FAIL, recorded before any repair. HIGH: (H1) `terminated-by-fault` exists only as an
    in-memory facade record and a probe diagnostic; no journal or Argus outcome carries it, and a
    run with an unrecovered `recovery: manual` crash after the unit's last health obligation ends
    as success (test_maestro_run.py asserted that), contradicting the proposed `manual`
    semantics (documented failure). (H2) `FaultScheduler.cancel` is never called from the
    dispatcher's failure path, so a failed or cancelled run leaves frozen units unthawed and
    entries without an outcome (contract rule 6); `cancel` also emits two `final` decisions for an
    active entry. MEDIUM: (M1) native freeze/thaw that times out answers "refused" with the write
    left in place; (M2) the run authority does not check `enabled`, `released`, `retired` or the
    latest generation for fault requests (only the Python side guards it); (M3) the termination
    record is not retracted when a kill is refused, and its docstring calls it durable; (M4) no
    run-level `causal-closure` obligation, the extension lacks boundary class and parameters, and
    relay faults in a Maestro run carry no traffic without saying so; (M5) several claimed V-case
    tests are missing (native token/pid refusal, "no other pid signalled", run-authority negatives,
    kill after the window, V03 Argus chains, U-ADM-03 digest equality with main). LOW: dead
    `unit_reply_extra`, unused `coverage.fault_events`, system URI taken from the first fault, no
    time reserve for fault statements, frozen-before-first-observation probe, design-doc retry
    wording. The quiet-host loop started on 2b89b2060 was stopped before it triggered (no run
    recorded). Repairs follow in finding 8.

8. Repairs of implementation review 1 (2026-10-22). H1: an applied crash now ends the run at once
    as a documented failure of the crashed unit (`_advance_faults` raises
    `ML-SCHEDULE-TERMINATED-BY-FAULT`; the dispatcher's failure statement carries that unit and
    diagnostic into the journal and Argus); this follows the planning package's proposed `manual`
    semantics and leaves D5-2 (automatic restart) open; the earlier test asserting success after a
    tick-2 crash was wrong and is replaced by a parametrized test for both timings. H2: the
    failure path calls `_cancel_faults` before cancelling the owner (best effort: statements that
    cannot be sent are skipped), so active faults are cleared (frozen units thawed) and every entry
    is closed; `FaultScheduler.cancel` clears without finalizing and then finalizes once
    (`cancelled`, or `incomplete-clearing` when the clear fails) and releases handles. M1: a
    freeze/thaw that is not observed in time is rolled back before answering "refused" (run
    authority and catalog launcher); if the rollback fails the helper/authority fails closed. M2:
    the run authority refuses fault kinds unless the authority is enabled and open and the
    generation is released, unretired and the latest. M3: a refused kill retracts the termination
    record; the "durable" wording is corrected (the fault's journaled intent precedes the in-run
    record). M4: intent statements carry boundary class, boundary mode (`owned-process`,
    `owned-relay-fixture-no-traffic`, `declared-only`) and parameters; the per-fault Argus
    obligation is replaced in the thesis contract (rule 7, FR-007) by run-enforced closure plus
    offline reconstruction, because Argus's `causal-closure` is run-level. M5: added tests:
    single final outcome on cancel (and on a failing clear), refused kill retracts the record,
    kill after the window is refused, identical Argus chains for the same plan and seed (V03),
    native forged-token refusal with an unrelated sentinel process left alone, sentinel survival
    across freeze/thaw/kill, run-authority refusal before release, fault-less digest equal to
    platform main computed from the sibling checkout. LOW: dead `unit_reply_extra` removed; the
    coverage skip now requires producer `xverse.faults` and exactly the `io.xverse.faults`
    extension; design-doc retry wording corrected; the planner reserves operation time and
    budget for five statements per fault. Found while repairing: three faults add 12 worker round
    trips, which overran the fixture's 4.8 s window at host load 11–12
    (`ML-SCHEDULE-SERVICE-DEADLINE`, refused safely); the fault end-to-end tests use the fixture's
    8 s paused window, and the resolver/scheduler now accept paused (non-decreasing) planned ticks.
    Results: tests/thesis_lite/faults 46 passed twice (load 8–12); Maestro slice
    (preparation, launcher, run broker, shared and lazy dispatcher, coverage, AFFA native,
    AFFA protocol, schedule plan) passed. Not repaired, recorded: the system URI for faults is
    taken from the fault target (all targets are System elements of the one selected system); a
    unit frozen before its first health observation is still probed once.
