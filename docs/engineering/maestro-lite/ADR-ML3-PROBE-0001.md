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
