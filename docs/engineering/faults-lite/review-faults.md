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
