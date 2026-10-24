# ADR-ML3-PROBE-0001 — Final native prerequisite observation

2026-10-19. Selected engineering refinement before implementation, full17 candidate.
Actual active-restart-c original93143 terminal1 records two prerequisite probes in
one fixed 0.5s generation operation; the final own probe expires with 66.21ms left
and 66.76ms actual duration. Do not increase that end or cache a prior observation.

For the original native RunUnitIssuer path, omit prerequisite units only from the
early all-released preflight. RunBroker.release still requires the original
DependencyGuard, both original durable revalidations, native ARM, live original
prerequisite probes after ARM and immediately before RELEASE. Unrelated released
units keep their early live observation. Legacy CatalogLauncher keeps all prior
checks. No native guard, current-handle identity, freshness or fixed end is removed.

Expected proof: exactly one successful parent probe after ARM before RELEASE;
parent death after ARM blocks RELEASE; altered deadline rejects; unrelated live
unit is sampled before ARM and its failure blocks ARM. Preserve the original
timeout and all failed attempts. One passing successor is not host stability or
full17 acceptance. Existing native checks with an expected duplicate count must
be refined to the source-derived ordering/failure contract, not merely relaxed.

## Amendment S1b-1: the admitted nonce-marker readiness probe (2026-10-23, written at 19:54:35; before implementation)

- **Scope.** Thesis S1 FR-011 and S-D3; design `design-stabilization-s1b.md`. The AF17 path only.
- **Declaration.** An observe action may declare `condition: nonce-marker` instead of `running`.
- **Challenge.** At STAGE, before `clone3`, the authority:
  1. moves a previous generation's `.xverse-ready` aside with `RENAME_NOREPLACE`;
  2. creates `.xverse-ready` (0700) in the unit's sealed cwd, which must be inside the run-scoped collection
     source root;
  3. writes `challenge`, 64 hex characters from `getrandom`, with `O_EXCL|O_NOFOLLOW`.
- **Readiness.** The unit is ready only when it is alive and `.xverse-ready/ready` is a regular 64-byte file
  equal to the nonce (`CRYPTO_memcmp`).
  - Checks run only on QUERY, at most 3 per generation natively and at most 3 per window in Python.
  - The bit latches (2048).
  - If the window expires: `ML-PROBE-NOT-READY`.
- **Unchanged.** Periodic health stays liveness-only. Undeclared and unchangeable units, such as the legacy VCU,
  stay `running`. No shell command, network discovery or log line is ever used.
- **Recorded identity.** The evidence and coverage `probe`/`ready` rows record the declared probe identity.

### Note: S1b-1 revision (RA1) (2026-10-24, written at 01:13:36; before implementation; thesis DR-15)

- **Context.** S1b review-log findings 21–22 (A), reproduced in `test_stabilization_stack_load_failures.py`.
  Nothing renews the bootstrap lease inside one dispatcher step, and the start step ends at that lease. A
  declared window W = 3.5 s therefore lost its third attempt to the lease cap, and the readiness-failure cancel
  ran with under a second of lease left. The run-bootstrap root then ended at its own lease and killed the
  authority and the storage worker.
- **Reserve.** `CANCEL_CLOSE_RESERVE_SECONDS` = 2.25 s: the native cancel close bound of 2 s
  (`run_authority.c` `close_end`) plus 0.25 s for the cancel's reply and the terminal fence.
- **Run-time cap.** For a `nonce-marker` unit, `ProcessReadiness.start` reads, at t0 (immediately after the
  release), the lease that ends the run: L = min(bootstrap root lease, native authority lease), both reachable
  through the unit's `RunUnitIssuer` broker. The window used is
  `W' = max(0, min(W, L − CANCEL_CLOSE_RESERVE_SECONDS − t0, D − t0))`, where D is the step deadline (already
  capped at the lease by the dispatcher). The start step's last attempt then ends at least
  `CANCEL_CLOSE_RESERVE_SECONDS` before the lease, and never after D.
- **Spacing.** The declared attempts are spaced over W' with the unchanged `readiness_offsets`, so every declared
  attempt is made. When W' is 0 the attempts are made back to back at t0. The `at >= deadline` drop stays as a
  defensive check.
- **Admission.** `admit_schedule` refuses, with `ML-SCHEDULE-READINESS-WINDOW`, a `nonce-marker` unit whose
  window W = min(policy timeout, observe action timeout) cannot fit a fresh lease:
  `W ≤ LEASE_MAX_SECONDS − CANCEL_CLOSE_RESERVE_SECONDS − operation_seconds`.
  - `LEASE_MAX_SECONDS` = 5 s is the native maximum of a renewal (`bootstrap.c`). `operation_seconds` is one
    bounded worker round trip for the start statement's work before the release (intent, stage, bind and the
    release revalidations).
  - With the live budgets (`operation_seconds` = 0.38 s) the bound is 2.37 s. With the composed test fixture
    (0.5 s) it is 2.25 s. The live harness's W = 3.5 s is refused; thesis DR-15 H1 lowers it.
  - The bound is necessary, not sufficient. The run-time cap is what keeps the reserve.
- **Residual (declared).** The dispatcher renews only at a statement boundary, when at most `renew_margin` is left
  (1.9 s live). A start step dispatched with between `renew_margin` and about `CANCEL_CLOSE_RESERVE_SECONDS` plus
  its pre-release work of lease left gets W' = 0 and keeps less than the full reserve. RA2 (renew before a
  readiness start step) would close this band; it is not part of DR-15.
- **Unchanged.** `running` probes, the probe identity, the native QUERY limit of 3 per generation, and
  `ML-PROBE-NOT-READY` when no attempt finds the marker.
- **Verification.** The (A) tests of `test_stabilization_stack_load_failures.py` pass by an admission refusal for
  W = 3.5 s and by three attempts within the capped window for an admitted W; unit tests cover the bound and the
  cap.
