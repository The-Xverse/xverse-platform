# T027 Unit Specifications — Guard Units and Test Units: Ownership, Lifetime, Thread-Safety, Bounds, Failure Semantics

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T027 (capability 007, slice `T-STIM`) |
| Stage / role | plan → unit specifications (pre-code) |
| Revision | 1 (fail-closed pre-emission guard) |
| Baseline revision | `bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Accepted design unit | `XCOM-DU-017` fail-closed pre-emission guard (component `XCOM-CMP-009`, contract `XCOM-XLC-006`, boundary `XCOM-XB-007`) |
| Classification | Public-safe engineering work product |

## 2. Unit summary

T027 delivers one production unit composed of five design components (`T27-CMP-VOCAB`, `-MODEL`, `-GUARD`,
`-DECIDE`, `-COMMIT`) and twenty **test units** across five new GoogleTest executables. A test unit is one
case function plus any case-local helper.

| Unit | Case function | File | Evidence name(s) | Owning slice |
| --- | --- | --- | --- | --- |
| `T27-TS-001` | `test_guard_authorizes_nominal_request_and_snapshot` | `tests/xcom/stimulation_guard/unit_tests.cpp` | `zero-emission-after-rejection` (positive control) | T-STIM |
| `T27-TS-002` | `test_guard_action_interaction_direction_table` | `tests/xcom/stimulation_guard/unit_tests.cpp` | `permit-action-mismatch-matrix` | T-STIM |
| `T27-TS-003` | `test_guard_closed_vocabulary_and_precedence` | `tests/xcom/stimulation_guard/unit_tests.cpp` | `deterministic-concurrency` (determinism) | T-STIM |
| `T27-TS-004` | `test_guard_status_determinism_and_no_mutation` | `tests/xcom/stimulation_guard/unit_tests.cpp` | `zero-emission-after-rejection` (no mutation) | T-STIM |
| `T27-TS-005` | `test_guard_policy_validation_matrix` | `tests/xcom/stimulation_guard/unit_tests.cpp` | `permit-action-mismatch-matrix` (policy) | T-STIM |
| `T27-TS-006` | `test_guard_identity_and_plan_matrix` | `tests/xcom/stimulation_guard/mismatch_tests.cpp` | `permit-action-mismatch-matrix` (identity) | T-STIM |
| `T27-TS-007` | `test_guard_lifecycle_matrix` | `tests/xcom/stimulation_guard/mismatch_tests.cpp` | `zero-emission-after-rejection` (revoked/expired) | T-STIM |
| `T27-TS-008` | `test_guard_schema_and_target_matrix` | `tests/xcom/stimulation_guard/mismatch_tests.cpp` | `permit-action-mismatch-matrix` (schema/target) | T-STIM |
| `T27-TS-009` | `test_guard_action_direction_matrix` | `tests/xcom/stimulation_guard/mismatch_tests.cpp` | `permit-action-mismatch-matrix` (action) | T-STIM |
| `T27-TS-010` | `test_guard_service_ownership_matrix` | `tests/xcom/stimulation_guard/mismatch_tests.cpp` | `permit-action-mismatch-matrix` (ownership) | T-STIM |
| `T27-TS-011` | `test_guard_quota_matrix` | `tests/xcom/stimulation_guard/mismatch_tests.cpp` | `quotas` | T-STIM |
| `T27-TS-012` | `test_guard_loop_bound_matrix` | `tests/xcom/stimulation_guard/mismatch_tests.cpp` | `loop-bounds` (guard half) | T-STIM |
| `T27-TS-013` | `test_guard_scheduled_time_window_matrix` | `tests/xcom/stimulation_guard/time_tests.cpp` | `unmapped-clocks` (window) | T-STIM |
| `T27-TS-014` | `test_guard_unmapped_clock_fails_closed` | `tests/xcom/stimulation_guard/time_tests.cpp` | `unmapped-clocks` | T-STIM |
| `T27-TS-015` | `test_guard_immediate_labeling_matrix` | `tests/xcom/stimulation_guard/time_tests.cpp` | `unmapped-clocks` (immediate) | T-STIM |
| `T27-TS-016` | `test_guard_rejection_zero_mutation_and_no_emission` | `tests/xcom/stimulation_guard/negative_tests.cpp` | `zero-emission-after-rejection` | T-STIM |
| `T27-TS-017` | `test_guard_closed_guard_rejects` | `tests/xcom/stimulation_guard/negative_tests.cpp` | `zero-emission-after-rejection` (precondition) | T-STIM |
| `T27-TS-018` | `test_guard_bounds_config_matrix` | `tests/xcom/stimulation_guard/negative_tests.cpp` | `permit-action-mismatch-matrix` (bounds) | T-STIM |
| `T27-TS-019` | `test_guard_bounded_deterministic_concurrency` | `tests/xcom/stimulation_guard/concurrency_tests.cpp` | `deterministic-concurrency` | T-STIM |
| `T27-TS-020` | `test_guard_concurrent_rejection_no_mutation` | `tests/xcom/stimulation_guard/concurrency_tests.cpp` | `deterministic-concurrency` (non-mutation) | T-STIM |

## 3. Production unit `T27-U-GUARD` (`XCOM-DU-017`)

- **Responsibility**: fail-closed evaluate one declared stimulation request against an immutable validation
  permit and a bounded declared stimulation policy; on `Authorized` commit the bounded tallies and loop
  window; on `Rejected`/`Failed` return an explicit reason with no mutation and no emission.
- **Ownership**: `session-issued-handle` — only a guard opened from the session's immutable permit may
  authorize; the guard owns its bounded tallies and loop window and copies the permit and policy. It exposes
  no payload view; produced values (`GuardSnapshot`, `GuardDiagnostic`) are caller-owned copies.
- **Lifetime**: `session-scoped` — the guard is valid for the validation-session scope and retains at most
  `policy.loop_window` lineage entries and bounded counters.
- **Thread-safety**: `internally-synchronized` — one per-guard mutex serializes `open`, the checks, the
  tallies, and the loop window; exactly one declared logical writer; no callback exists.
- **Bounds**: see `detailed-design.md` §7 — `kGuardMaxSchemas`, `kGuardMaxLoopWindow`,
  `kGuardMaxActionsPerSession`, `kGuardMaxActionsPerWindow`, bounded tags, one writer, one bounded loop
  window.
- **Failure semantics**: `Authorized`/`Rejected`/`Failed` over the closed `GuardReason` vocabulary per
  `detailed-design.md` §6. A rejection/failure mutates no tally, loop window, permit, or policy byte and
  never reports `Authorized`. An invalid policy or a malformed request is `RejectedConfiguration` with no
  mutation; a closed guard is `Failed`/`NotOpen`; an absent/unmapped/out-of-tolerance time is
  `Failed`/`TimeUnmapped`.
- **Requirements**: T027-SR-001…T027-SR-018, T027-SR-021, T027-SR-022.

## 4. Unit `T27-TS-001` — Nominal authorization and snapshot

- **Responsibility**: prove that a consistent guard authorizes one nominal request of each action kind and
  commits the declared tallies and loop entries.
- **Ownership**: owns the permit, policy, requests, guard, and snapshot copies it constructs.
- **Lifetime**: the permit and policy outlive the guard; the snapshot is a value copy.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_actions_per_session` 8, `max_actions_per_window` 4, `action_window` 4, `loop_window` 4;
  ≤ 4 authorized requests.
- **Failure semantics**: fails if a nominal request is not `Authorized`/`None` or if a tally/loop entry
  differs from the expected commit.
- **Requirements**: T027-SR-001, T027-SR-013, T027-SR-021.

## 5. Unit `T27-TS-002` — Action/interaction/direction table

- **Responsibility**: prove every row of `detailed-design.md` §5.3.
- **Ownership**: owns the permit, policy, guard, and request values.
- **Lifetime**: one guard per row group; requests are values.
- **Thread-safety**: single-threaded.
- **Bounds**: `allowed_actions` `0x0F`, `allowed_interactions` `0x0F`, `allowed_directions` `0x0F`; ≤ 12 rows.
- **Failure semantics**: fails if a consistent triple is rejected or an inconsistent triple is authorized,
  or if the reason differs from §5.3.
- **Requirements**: T027-SR-007, T027-SR-008.

## 6. Unit `T27-TS-003` — Closed vocabulary and precedence

- **Responsibility**: prove the closed `StimulationAction`/`GuardOutcome`/`GuardReason`/`GuardStatus`
  vocabularies have stable names, ranks, and `outcome_of` values, with a total map.
- **Ownership**: owns only vocabulary copies.
- **Lifetime**: static-lifetime vocabulary.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 4 actions, ≤ 3 outcomes, ≤ 17 reasons, ≤ 3 statuses.
- **Failure semantics**: fails if a name/rank/outcome is unstable, empty, or not total over the vocabulary.
- **Requirements**: T027-SR-003, T027-SR-014.

## 7. Unit `T27-TS-004` — Determinism and no-mutation

- **Responsibility**: prove identical decisions/reasons/snapshots across three repeated runs and an
  unchanged snapshot after a rejected evaluation.
- **Ownership**: owns the guard and pre/post snapshot copies.
- **Lifetime**: snapshots are value copies taken before and after an evaluation.
- **Thread-safety**: single-threaded; three repeated bounded runs.
- **Bounds**: ≤ 3 runs; ≤ 8 evaluations per run; `max_actions_per_session` 4.
- **Failure semantics**: fails if a repeated run differs or a rejected evaluation changes the snapshot.
- **Requirements**: T027-SR-013, T027-SR-014.

## 8. Unit `T27-TS-005` — Policy validation matrix

- **Responsibility**: prove every row of `detailed-design.md` §5.1.
- **Ownership**: owns each policy/permit pair and the guard construction.
- **Lifetime**: one `open` attempt per row; a rejected open leaves the guard closed.
- **Thread-safety**: single-threaded.
- **Bounds**: 9 policy rows; `kGuardMaxSchemas` 16; `kGuardMaxLoopWindow` 64; no request evaluated.
- **Failure semantics**: fails if an invalid/inconsistent policy is accepted or a legal policy is rejected,
  or if a rejected open mutates state.
- **Requirements**: T027-SR-021.

## 9. Unit `T27-TS-006` — Identity and plan matrix

- **Responsibility**: prove every row of `detailed-design.md` §5.6.
- **Ownership**: owns the permit, policy, guard, and request values.
- **Lifetime**: one guard; requests are values.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 5 rows; one guard.
- **Failure semantics**: fails if a session/permit/plan mismatch is authorized or reports a reason other than
  `PermitMismatch`.
- **Requirements**: T027-SR-005.

## 10. Unit `T27-TS-007` — Lifecycle matrix

- **Responsibility**: prove every row of `detailed-design.md` §5.2.
- **Ownership**: owns the permit, policy, guard, and lifecycle values.
- **Lifetime**: one guard; lifecycle values are supplied per evaluation.
- **Thread-safety**: single-threaded.
- **Bounds**: 8 lifecycle rows.
- **Failure semantics**: fails if a revoked/expired/non-active session is authorized, if a reason differs, or
  if a rejection mutates a tally.
- **Requirements**: T027-SR-006.

## 11. Unit `T27-TS-008` — Schema and target matrix

- **Responsibility**: prove declared/undeclared schema, invalid schema tags, and target/interface mismatch
  rows.
- **Ownership**: owns the permit, policy (schema table), guard, and requests.
- **Lifetime**: one guard with a bounded schema table.
- **Thread-safety**: single-threaded.
- **Bounds**: 2–16 declared schemas; ≤ 8 rows.
- **Failure semantics**: fails if an undeclared/invalid schema or a target/interface mismatch is authorized
  or reports the wrong reason.
- **Requirements**: T027-SR-007.

## 12. Unit `T27-TS-009` — Action and direction matrix

- **Responsibility**: prove the defined-action-not-allowed, interaction-exclusion, direction-exclusion,
  and malformed-action (zero/composite/out-of-vocabulary) rows of `detailed-design.md` §5.3.
- **Ownership**: owns the permit, policy, guard, and requests.
- **Lifetime**: one guard.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 9 rows; `allowed_actions` `0x01`.
- **Failure semantics**: fails if a disallowed action/interaction/direction is authorized, reports the
  wrong reason, or if a zero/composite/out-of-vocabulary action is not `RejectedConfiguration` at rank 1.
- **Requirements**: T027-SR-007, T027-SR-008.

## 13. Unit `T27-TS-010` — Service-ownership matrix

- **Responsibility**: prove declared/missing/mismatched owner and generation, emulation-requires-owner, and
  invoke-vs-emulate rows.
- **Ownership**: owns the permit, policy (service owner), guard, and requests; acquires no lease.
- **Lifetime**: one guard; owner values are supplied per evaluation.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 8 rows.
- **Failure semantics**: fails if a missing/mismatched/ambiguous owner is authorized, if an emulation without
  a declared owner is accepted, or if a non-owner reason is reported.
- **Requirements**: T027-SR-011.

## 14. Unit `T27-TS-011` — Quota matrix

- **Responsibility**: prove the per-session and per-window quota rows of `detailed-design.md` §5.4.
- **Ownership**: owns the guard and pre/post snapshot copies.
- **Lifetime**: one guard; snapshot copies bracket each boundary.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_actions_per_session` 2 and 4; `max_actions_per_window` 1 and 2; `action_window` 2;
  ≤ 6 evaluations.
- **Failure semantics**: fails if an over-budget request is authorized, if `window_actions` does not reset at
  `action_window`, or if exhaustion mutates a tally.
- **Requirements**: T027-SR-009.

## 15. Unit `T27-TS-012` — Loop-bound matrix

- **Responsibility**: prove the loop rows of `detailed-design.md` §5.4.
- **Ownership**: owns the guard, the request lineage values, and snapshot copies.
- **Lifetime**: one guard; lineage advances only on `Authorized`.
- **Thread-safety**: single-threaded.
- **Bounds**: `loop_window` 2 and 4; ≤ 8 evaluations.
- **Failure semantics**: fails if a reinjection is authorized, if `causation_id == 0` is rejected as a loop,
  if the window exceeds `loop_window`, or if a rejection mutates the window.
- **Requirements**: T027-SR-010.

## 16. Unit `T27-TS-013` — Scheduled time-window matrix

- **Responsibility**: prove the in-window and out-of-window scheduled rows of `detailed-design.md` §5.5.
- **Ownership**: owns the permit (validity interval), guard, and `ResolvedTime` values.
- **Lifetime**: one guard; resolved-time values are supplied per evaluation.
- **Thread-safety**: single-threaded.
- **Bounds**: validity interval `[0, 100)` (realized values 0, 99, 100, −1); ≤ 6 rows.
- **Failure semantics**: fails if an in-window request is rejected, an out-of-window request is authorized,
  or the reason differs.
- **Requirements**: T027-SR-012.

## 17. Unit `T27-TS-014` — Unmapped clock fails closed

- **Responsibility**: prove every non-`Ok` resolution and a domain-mismatch resolution return
  `Failed`/`TimeUnmapped` with no mutation.
- **Ownership**: owns the guard and resolved-time values; calls no time authority.
- **Lifetime**: one guard; resolved-time values are supplied per evaluation.
- **Thread-safety**: single-threaded.
- **Bounds**: resolution rows `UnknownClock`, `MissingMapping`, `ToleranceExceeded`, `ClockSourceFailure`,
  `ClockRegression`, and a domain mismatch; ≤ 6 rows.
- **Failure semantics**: fails if a non-`Ok` resolution is authorized, if it reports `Rejected` rather than
  `Failed`, or if it mutates a tally.
- **Requirements**: T027-SR-012, T027-SR-016 (lineage: guard performs no authority call).

## 18. Unit `T27-TS-015` — Immediate labeling matrix

- **Responsibility**: prove the immediate rows of `detailed-design.md` §5.5.
- **Ownership**: owns the permit, guard, and request values.
- **Lifetime**: one guard.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 4 rows (immediate in/out of window; immediate with a non-validity clock domain; scheduled
  mislabeled immediate).
- **Failure semantics**: fails if an immediate request with a non-validity clock domain is authorized, or if
  the reason differs.
- **Requirements**: T027-SR-012.

## 19. Unit `T27-TS-016` — Rejection: zero mutation and no emission

- **Responsibility**: for each rejection family, prove the snapshot is byte-identical, the loop window is
  unchanged, and the guard type exposes no emission/callback/route/injection/invocation/emulation/lease
  member.
- **Ownership**: owns the guard, the pre/post snapshot copies, and the declaration-inspection target.
- **Lifetime**: one guard reused across rejection families, each bracketed by snapshot copies.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 8 rejection families; ≤ 8 evaluations.
- **Failure semantics**: fails if any rejection changes the snapshot or loop window, or if the guard surface
  exposes an emission/action member.
- **Requirements**: T027-SR-013, T027-SR-022.

## 20. Unit `T27-TS-017` — Closed guard rejects

- **Responsibility**: prove `authorize` before `open` returns `Failed`/`NotOpen` with no mutation.
- **Ownership**: owns the default-constructed guard and snapshot copies.
- **Lifetime**: the guard is never opened.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 3 evaluations; one guard.
- **Failure semantics**: fails if a closed guard authorizes, reports a non-`NotOpen` reason, or mutates state.
- **Requirements**: T027-SR-013, T027-SR-022.

## 21. Unit `T27-TS-018` — Bounds and config matrix

- **Responsibility**: prove the remaining §5.1 bound rows and an over-full schema table.
- **Ownership**: owns each policy/permit pair and the guard construction.
- **Lifetime**: one `open` attempt per row.
- **Thread-safety**: single-threaded.
- **Bounds**: `kGuardMaxSchemas + 1` schema entries; ≥ 4 bound rows.
- **Failure semantics**: fails if an over-maximum or zero bound is accepted or a rejected open mutates state.
- **Requirements**: T027-SR-021.

## 22. Unit `T27-TS-019` — Bounded deterministic concurrency

- **Responsibility**: prove independent guards driven in parallel produce the single-threaded golden decision
  sequence and final snapshot, and that concurrent authorizations against one guard commit exactly the
  declared per-session quota with no over-quota action.
- **Ownership**: owns 4 independent guards (and one shared guard for the quota case), 4 joined threads, and
  the golden sequence.
- **Lifetime**: every thread is joined before its guard is destroyed.
- **Thread-safety**: ≤ 4 threads, one logical writer per guard, no shared mutable state between guards; atomic
  flags only. The quota case submits to one guard, which serializes the check-and-commit.
- **Bounds**: `max_actions_per_session` 16 (7 for the quota case); ≤ 4 threads; ≤ 16 evaluations per
  thread (≤ 64 per guard for the quota case); 3 repeated runs.
- **Failure semantics**: fails if any guard's sequence/snapshot differs from the golden one, if repeated
  runs differ, or if the concurrent-authorization case commits more than the declared quota.
- **Requirements**: T027-SR-015.

## 23. Unit `T27-TS-020` — Concurrent rejection non-mutation

- **Responsibility**: prove that concurrent rejecting evaluations of one guard leave the snapshot equal to
  the pre-call snapshot.
- **Ownership**: owns one guard, 4 joined threads, and the pre/post snapshot copies.
- **Lifetime**: the guard outlives every thread.
- **Thread-safety**: ≤ 4 threads submitting only rejecting requests; the guard serializes them.
- **Bounds**: ≤ 4 threads; ≤ 16 evaluations per thread; one guard.
- **Failure semantics**: fails if any outcome is `Authorized`, if any outcome is not `Rejected`/`Failed`, or
  if the post snapshot differs from the pre snapshot (except the declared evaluation/rejection counters).
- **Requirements**: T027-SR-013, T027-SR-015.

## 24. Concurrency/resource bound summary

| Aspect | Bound | Units |
| --- | --- | --- |
| Threads | ≤ 4 | TS-019, TS-020 |
| Writers per guard | 1 | all |
| Authorized actions per guard | ≤ `max_actions_per_session` (realized ≤ 16) | all |
| `max_actions_per_session` values in tests | 2, 4, 8, 16 | all |
| `max_actions_per_window` values in tests | 1, 2, 4 | all |
| `action_window` values in tests | 2, 4 | all |
| `loop_window` values in tests | 2, 4, 8 | TS-012, TS-019 |
| Declared schema table | ≤ `kGuardMaxSchemas` (realized 2, `kGuardMaxSchemas + 1`) | TS-008, TS-018 |
| Iterations | ≤ 64 bounded guard operations per case | all |
| Wall-clock | none | all |
| Callbacks | none | all |
| Guard I/O | none | all |

## 25. Traceability

| Unit | T027 requirements | Accepted software req | Spec anchor | Design unit |
| --- | --- | --- | --- | --- |
| `T27-TS-001` | T027-SR-001, T027-SR-013, T027-SR-021 | `XCOM-SW-STIM-004` | FR-018 | `XCOM-DU-017` |
| `T27-TS-002` | T027-SR-007, T027-SR-008 | `XCOM-SW-STIM-004` | FR-018 | `XCOM-DU-017` |
| `T27-TS-003` | T027-SR-003, T027-SR-014 | `XCOM-SW-STIM-004` | FR-018, FR-025 | `XCOM-DU-017` |
| `T27-TS-004` | T027-SR-013, T027-SR-014 | `XCOM-SW-STIM-004` | FR-018 | `XCOM-DU-017` |
| `T27-TS-005` | T027-SR-021 | `XCOM-SW-STIM-004` | FR-007, FR-018 | `XCOM-DU-017` |
| `T27-TS-006` | T027-SR-005 | `XCOM-SW-STIM-004` | FR-018 | `XCOM-DU-017` |
| `T27-TS-007` | T027-SR-006 | `XCOM-SW-STIM-004` | FR-016, FR-018 | `XCOM-DU-017` |
| `T27-TS-008` | T027-SR-007 | `XCOM-SW-STIM-004` | FR-018 | `XCOM-DU-017` |
| `T27-TS-009` | T027-SR-007, T027-SR-008 | `XCOM-SW-STIM-004` | FR-018 | `XCOM-DU-017` |
| `T27-TS-010` | T027-SR-011 | `XCOM-SW-STIM-005` (partial) | FR-019, FR-034 | `XCOM-DU-017` |
| `T27-TS-011` | T027-SR-009 | `XCOM-SW-STIM-004` | FR-007, FR-018 | `XCOM-DU-017` |
| `T27-TS-012` | T027-SR-010 | `XCOM-SW-STIM-005` (partial) | FR-019 | `XCOM-DU-017` |
| `T27-TS-013` | T027-SR-012 | `XCOM-SW-STIM-006` (partial) | FR-020, FR-033 | `XCOM-DU-017` |
| `T27-TS-014` | T027-SR-012, T027-SR-016 | `XCOM-SW-STIM-006` (partial) | FR-033 | `XCOM-DU-017` |
| `T27-TS-015` | T027-SR-012 | `XCOM-SW-STIM-006` (partial) | FR-020 | `XCOM-DU-017` |
| `T27-TS-016` | T027-SR-013, T027-SR-022 | `XCOM-SW-STIM-004` | FR-018 | `XCOM-DU-017` |
| `T27-TS-017` | T027-SR-013, T027-SR-022 | `XCOM-SW-STIM-004` | FR-018 | `XCOM-DU-017` |
| `T27-TS-018` | T027-SR-021 | `XCOM-SW-STIM-004` | FR-007, FR-018 | `XCOM-DU-017` |
| `T27-TS-019` | T027-SR-015 | `XCOM-SW-STIM-004` | FR-007, FR-014 | `XCOM-DU-017` |
| `T27-TS-020` | T027-SR-013, T027-SR-015 | `XCOM-SW-STIM-004` | FR-007, FR-018 | `XCOM-DU-017` |

## 26. Bounds and open items

- `XCOM-SW-STIM-005` is **partial**: only the guard-level bounded loop window and declared-ownership check
  are proven by `T27-TS-010`/`T27-TS-012`; the exclusive lease and end-to-end loop enforcement are
  `XCOM-DU-018`/T028 and their matrix is T029 (`T027-GAP-01`).
- `XCOM-SW-STIM-006` is **partial**: only the guard-level pre-emission time-policy check is proven by
  `T27-TS-013`/`T27-TS-014`/`T27-TS-015`; scheduled ordering, late-item behavior, and the end-to-end
  unmapped-clock/tolerance behavior are T028/T029 (`T027-GAP-02`).
- The guard produces a decision and exposes no emission path; the end-to-end "zero normal-route item" proof
  is T028/T029 (`T027-GAP-03`).
- Service-ownership validation is declaration-level; the guard holds no lease (`T027-GAP-04`).
- Strict declaration-level Doxygen execution remains `DOX-GAP-01` (T011/T037); T027 supplies the
  declarations only.
- `XCOM-DU-017` bound source and public-element count are reconciled in the T027 implementation record as a
  successor note (`T027-OPEN-01`).

## 27. Negative-case mapping (unit view)

| Unit | Realizes negative cases |
| --- | --- |
| `T27-TS-001` | positive control for NEG-26, NEG-27 |
| `T27-TS-002` | NEG-04, NEG-12, NEG-13, NEG-15 |
| `T27-TS-003` | NEG-28 |
| `T27-TS-004` | NEG-26, NEG-28 |
| `T27-TS-005` | NEG-33 |
| `T27-TS-006` | NEG-06, NEG-07 |
| `T27-TS-007` | NEG-08, NEG-09, NEG-10 |
| `T27-TS-008` | NEG-05, NEG-11, NEG-14 |
| `T27-TS-009` | NEG-15 |
| `T27-TS-010` | NEG-20, NEG-21 |
| `T27-TS-011` | NEG-16, NEG-17, NEG-36 |
| `T27-TS-012` | NEG-18, NEG-19 |
| `T27-TS-013` | NEG-24, NEG-25 |
| `T27-TS-014` | NEG-22, NEG-23, NEG-35 |
| `T27-TS-015` | NEG-22, NEG-25 |
| `T27-TS-016` | NEG-26, NEG-27 |
| `T27-TS-017` | NEG-34 |
| `T27-TS-018` | NEG-19, NEG-33 |
| `T27-TS-019` | NEG-29, NEG-36 |
| `T27-TS-020` | NEG-26, NEG-29 |
| Production unit (`T27-U-GUARD`) | NEG-01, NEG-02, NEG-03, NEG-30, NEG-31, NEG-32 (source-inspection cases) |
