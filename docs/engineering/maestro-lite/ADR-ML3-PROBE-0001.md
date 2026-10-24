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

### Note: S1b-1 revision (RA2, RA5, the window record) (2026-10-24, written at 01:47:51; before implementation; thesis DR-16)

- **Context.** S1b review-log finding 24 (independent review of DR-15), MEDIUM-1, MEDIUM-2 and LOW-5; thesis DR-16
  is the disposition. MEDIUM-1: the dispatcher renews only at a statement boundary, so a marker start step usually
  meets `L − t0 < W + reserve` and the RA1 cap spends W' < W silently; in the finding 22 placement W' ≈ 0–0.26 s
  for any W. MEDIUM-2: the RA1 reserve (2 s close + 0.25 s) does not cover the `failure` statement, a storage RPC
  that runs after the readiness-failure cancel and before the terminal fence, the first call that extends the root
  lease (`_cleanup` → `RunBroker.service_terminal`).
- **Renewal today (unchanged by this note).** `FiniteDispatcher._service`, at each statement boundary, renews when
  `min(lease ends) − now ≤ renew_margin = service_calls × operation_seconds + operation_seconds` (live: 4 × 0.38 +
  0.38 = 1.9 s; composed fixture: 4 × 0.5 + 0.5 = 2.5 s), and also before an earlier health scan whose service
  window would consume that margin. `_renew_service` takes `next_end = min(now + 5 s, generation − 2 s)`: 5 s is
  the native maximum of every lease, the initial one and each renewal (`bootstrap.c:136,338`), and `generation −
  2 s` is the native bound `until ≤ generation − 2 s`. It refuses `ML-SCHEDULE-LEASE-EXHAUSTED` when `next_end`
  is not above the bootstrap lease. On the native path it sends the controller heartbeat first and then
  `RunBroker.renew`, which, under the owner lock and then the broker lock, runs one storage audit
  (`revalidate_run`, one request), renews the bootstrap root lease (`session.renew`) and sends K.RENEW to the
  authority with the same target. The bootstrap lease and the authority lease therefore move together to one
  target; the broker refuses a target that is not above both or exceeds either generation − 2 s, and an uncertain
  renewal cancels the run. Nothing renews inside `facade.start`.
- **RA2 (decision).** In `FiniteDispatcher._effect`, for a `start` step of a unit whose readiness probe is
  `nonce-marker`, after the step's `_service()` and before its end D is computed, the dispatcher renews through
  the unchanged `_renew_service` when `min(lease ends) − now < readiness_lease_need(W, operation_seconds) = W +
  cancel_close_reserve(operation_seconds) + operation_seconds`, where W = min(policy timeout, observe timeout). The
  need is the admission bound read the other way (`W ≤ 5 − reserve − operation_seconds`), so an admitted W always
  fits the renewed lease. Its D is then `min(active end, now + start budget, renewed lease, health term)`.
  - It renews only on the native path (a marker unit is always a `RunUnitIssuer`) and only when
    `min(now + 5 s, generation − 2 s)` is above both leases. Otherwise, near the generation end, it does not renew;
    the cap then spends W' < W and the cut is recorded (below). This adds no new failure mode: a renewal that fails
    keeps `_renew_service`'s existing fail-closed handling.
  - **Authority lease.** RA2 is an ordinary renewal: same thread, same lock order, same target for both leases. The
    providers' L = min(root lease, authority lease) read at t0 is still conservative, because both leases only grow
    and only the dispatcher thread renews them. The S1a-5 admission of a CANCEL past the authority lease is
    unchanged.
  - **Request budget.** Each RA2 renewal costs one storage audit. `admit_schedule` adds one request per marker
    unit to `required_requests`. That changes the schedule bytes only for schedules with marker units, with no
    version change. Running-only schedules are unchanged.
  - **Not covered.** A restarted marker unit (`_restart_unit`) is not renewed by RA2; it keeps the run-time cap and
    the window record. RA3 (renewal between attempts) stays deferred.
- **RA5 (decision): the reserve covers the failure statement.** `CANCEL_CLOSE_RESERVE` becomes
  `cancel_close_reserve(operation_seconds) = NATIVE_CANCEL_CLOSE_SECONDS (2 s) + operation_seconds +
  CANCEL_FENCE_MARGIN_SECONDS (0.25 s)`.
  - The middle term is the admitted budget of one terminal-section statement, the `failure` statement that runs
    after the readiness-failure cancel and before the terminal fence. The 0.25 s keeps its earlier meaning: the
    cancel's reply and the terminal fence.
  - The path it covers is: `owner.cancel`, up to the 2 s native close for a responsive authority; the `failure`
    statement; `_close_restarts`, which is local; and `_cleanup`, whose broker cancel returns the cached result
    before `service_terminal` moves the root into terminal mode.
  - **Admission bound.** `readiness_window_bound(op) = LEASE_MAX_SECONDS − cancel_close_reserve(op) − op = 2.75 s −
    2·op`. With the live `operation_seconds` of 0.38 s it is 1.99 s (reserve 2.63 s). With the composed fixture's
    0.5 s it is 1.75 s (reserve 2.75 s).
  - **Effect on H1.** DR-15 H1 (W = 2.0 s) is now refused live, by 0.01 s. H1 must be re-derived as W ≤ 1.99 s, for
    example 1.9 s.
  - **Run time.** `ProcessReadiness.start` takes `operation_seconds` from the persistence client's admitted
    schedule. A facade used without a schedule has no dispatcher and so no `failure` statement, and the term is
    0 there.
  - **A fence-first terminal service is rejected** (DR-16): it would change the order of the closure records on
    which S1a and S1b were accepted.
  - **Residual (declared).** The `failure` statement's own deadline stays `min(work end, now + per_unit_seconds)`,
    so a storage RPC slower than `operation_seconds` (a stalled device) can still pass L. The fence's own deadline,
    `now + operation_seconds` capped at the lease, is covered only by the 0.25 s margin. Both remain fail-closed
    under the owner decision of finding 18 (LOW-2): the root ends at its lease and the closure is incomplete, not
    silent.
- **The window record (decision).** At t0, `ProcessReadiness.start` records for each marker start step a frozen
  `ReadinessWindow(unit_id, generation, declared_seconds = W, window_seconds = W', lease_end = L, began = t0,
  cut = W' < W)`. L and t0 are host-monotonic seconds of the run's host session, the domain of the evidence
  `clocks.host`. The records are exposed in order as `ProcessReadiness.readiness_windows` and
  `DispatchResult.readiness_windows`, which the runtime result carries (`RuntimeResult.dispatch`) to the
  harness's run record (thesis H3). Every value is public-safe: a unit id, an integer generation, three durations
  or times in seconds and a boolean. There are no paths, nonces, handles or digests.
- **The cut is a distinct diagnostic.** When W' < W and no attempt finds the marker, `start` raises
  `ML-PROBE-WINDOW-CUT` instead of `ML-PROBE-NOT-READY`. That code reaches the dispatch result, the
  `failure` statement and, through its existing `diagnosticCode` field, the closed Argus evidence. The dispatcher
  maps a diagnostic containing `WINDOW` to the cause `deadline-exceeded`, which is correct here: the window was
  cut by the lease or by the step deadline. A cut window whose marker is found still succeeds, and its record says
  `cut: true`.
  - **Why a diagnostic and not a field on the not-ready row.** The lifecycle annotation payload v2.0 is closed:
    the schema sets `additionalProperties: false`, `coverage.PAYLOAD_OPTIONAL` lists the admitted keys, and
    `validate_receipt` checks the exact key set. A field on the probe row would be an evidence-format change,
    with a payload version, coverage and receipt changes, and a re-acceptance of S1b's evidence. A diagnostic uses a
    field that every consumer already reads, so a cut cannot be mistaken for "not ready within W".
  - **Limit (declared).** W, W', L and t0 are in the result objects, not in the Argus records.
- **L5 correction (rationale of the S1b-1 RA1 admission).** The `operation_seconds` term does not stand for "one
  bounded worker round trip". It is a nominal allowance for the whole pre-release work of the start step: the lazy
  `commit_intent`, `stage` and `bind`; the prerequisite and health QUERYs; ARM; and RELEASE with its
  revalidations. That is several round trips. The bound stays necessary, not sufficient. RA2 renews with the same
  allowance. When that work exceeds it, W' < W, and the cut is now recorded and diagnosed rather than silent. This
  correction changes no safety claim.
- **Unchanged.** The spacing (`readiness_offsets` over W'), the `at >= deadline` drop, the probe identity, the
  native QUERY limit of 3 per generation, and readiness only from a verified marker.
- **Verification.** `test_stabilization_stack_load_failures.py`:
  - a marker start placed with less than the need of lease left is renewed and keeps W' = W;
  - a forced cut (RA2 disabled) is recorded and ends `ML-PROBE-WINDOW-CUT`;
  - a cut window whose cancel takes the full 2.0 s native close still reaches the fence with the root and the
    authority alive and closes completely.

  Unit tests cover the reserve, the bound and the cap. The dispatcher, lease-renewal, schedule, readiness and
  closure suites must stay unchanged.
