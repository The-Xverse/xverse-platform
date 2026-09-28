# T029 Unit Specifications — Owned Fixture and Test Units: Ownership, Lifetime, Thread-Safety, Bounds, Failure Semantics

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T029 (capability 007, slice `T-STIM`) |
| Stage / role | plan → unit specifications (pre-code) |
| Revision | 1 (complete T-STIM cross-cutting verification matrix) |
| Baseline revision | `4d3985855ef7a62b68aa4c66d3b7df032b29f5e9` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Accepted design units verified | `XCOM-DU-014`…`XCOM-DU-018` (component `XCOM-CMP-009`, contract `XCOM-XLC-006`, boundary `XCOM-XB-007`) |
| Classification | Public-safe engineering work product |

## 2. Unit summary

T029 delivers **no production unit**; it delivers one test-local fixture unit and twenty **test units** across six
new GoogleTest executables. A test unit is one case function plus any case-local helper. The candidate discovers
twenty case functions (one per declared unit below) in addition to the preserved baseline cases.

| Unit | Case function | File | Evidence name(s) | Owning slice |
| --- | --- | --- | --- | --- |
| `T29-U-FIXTURE` | `test_support.hpp` (no case) | `tests/xcom/stimulation_matrix/test_support.hpp` | all (owned fixture) | T-STIM |
| `T29-TS-001` | `MismatchMatrixEveryGuardReason` | `permit_action_matrix_tests.cpp` | `permit-action-mismatch-matrix` | T-STIM |
| `T29-TS-002` | `MismatchMatrixLifecycleAndClosedGuard` | `permit_action_matrix_tests.cpp` | `permit-action-mismatch-matrix` | T-STIM |
| `T29-TS-003` | `MismatchMatrixQuotaExhaustion` | `permit_action_matrix_tests.cpp` | `quotas` | T-STIM |
| `T29-TS-004` | `MismatchMatrixLoopBoundAndLineage` | `permit_action_matrix_tests.cpp` | `loop-bounds` | T-STIM |
| `T29-TS-005` | `MismatchMatrixUnmappedAndOutOfToleranceClock` | `permit_action_matrix_tests.cpp` | `unmapped-clocks` | T-STIM |
| `T29-TS-006` | `JournalIntentPrecedesSingleEmission` | `journal_recovery_tests.cpp` | `journal-before-emission` | T-STIM |
| `T29-TS-007` | `JournalIntentAppendFailureEmitsNothing` | `journal_recovery_tests.cpp` | `journal-failure-recovery`, `zero-emission-after-rejection` | T-STIM |
| `T29-TS-008` | `JournalOutcomeFailureIsEvidenceIncomplete` | `journal_recovery_tests.cpp` | `journal-failure-recovery` | T-STIM |
| `T29-TS-009` | `JournalRestartRecoversExactIdentity` | `journal_recovery_tests.cpp` | `journal-failure-recovery`, `synthetic-provenance` | T-STIM |
| `T29-TS-010` | `JournalCapacityExhaustionFailsClosed` | `journal_recovery_tests.cpp` | `journal-failure-recovery`, `quotas` | T-STIM |
| `T29-TS-011` | `ZeroEmissionAcrossEveryRejectionFamily` | `zero_emission_tests.cpp` | `zero-emission-after-rejection` | T-STIM |
| `T29-TS-012` | `ProvenanceDescriptorCarriesSyntheticIdentity` | `provenance_tests.cpp` | `synthetic-provenance` | T-STIM |
| `T29-TS-013` | `ProvenanceSurvivesRoutingAndObservation` | `provenance_tests.cpp` | `synthetic-provenance` | T-STIM |
| `T29-TS-014` | `ProvenanceSurvivesJournalRestart` | `provenance_tests.cpp` | `synthetic-provenance` | T-STIM |
| `T29-TS-015` | `ProvenanceNeverRelabelled` | `provenance_tests.cpp` | `synthetic-provenance` | T-STIM |
| `T29-TS-016` | `LeaseConflictMatrixEndToEnd` | `lease_drain_tests.cpp` | `lease-conflicts` | T-STIM |
| `T29-TS-017` | `DrainTerminalLifecycleMatrix` | `lease_drain_tests.cpp` | `drain-terminal` | T-STIM |
| `T29-TS-018` | `DrainOrderingLatePolicyAndImmediateLabel` | `lease_drain_tests.cpp` | `drain-terminal` | T-STIM |
| `T29-TS-019` | `ConcurrentQuotaEmissionDeterminism` | `concurrency_tests.cpp` | `deterministic-concurrency`, `quotas` | T-STIM |
| `T29-TS-020` | `ConcurrentLeaseSingleWinnerAndCompletion` | `concurrency_tests.cpp` | `deterministic-concurrency`, `lease-conflicts` | T-STIM |

## 3. Test-local fixture unit `T29-U-FIXTURE`

- **Responsibility**: compose the accepted T025/T026/T027/T028 surfaces and the accepted T-CORE/T-OBS surfaces
  into one bounded owned fixture for the matrix cases; inject declared journal-storage faults; record emitter
  calls; bridge the emitted descriptor to the accepted observation boundary.
- **Ownership**: owns the permit/session values, policy, bounded journal storage, journal, registry, action path,
  recording emitter, and observation hub; the journal, registry, emitter, hub, and lifecycle controller are
  constructed before and outlive the action path. It retains no payload byte.
- **Lifetime**: one fixture per case; the action path is destroyed before its referenced services.
- **Thread-safety**: single declared user per case except the concurrency cases, which use ≤ 4 joined threads; the
  accepted components serialize their own state; the fixture invokes no callback under a lock.
- **Bounds**: durable bytes ≤ 16 KiB; ≤ 4 declared injection points; ≤ 64 operations; ≤ 1 captured descriptor; the
  observation hub uses one tap and a fixed record capacity.
- **Failure semantics**: a fixture construction or `open` failure fails the case; an injected fault returns the
  declared `JournalStatus`/`EmissionStatus` and never silently succeeds.
- **Requirements**: T029-SR-003, T029-SR-022.

## 4. Test units

### 4.1 Unit `T29-TS-001` — Mismatch matrix: request-evaluation guard reasons

- **Responsibility**: exercise every request-evaluation guard reason (M-02…M-12) through the accepted action path
  and assert the declared `ActionStatus` and preserved `GuardReason`.
- **Ownership**: owns the fixture, one request per row, and pre/post snapshots.
- **Lifetime**: one fixture reused across rows; snapshots are value copies.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 11 rows; ≤ 11 evaluations; zero emitter calls; zero durable appends.
- **Failure semantics**: fails if any row emits, journals, evaluates the guard more than once, or returns a
  different status/reason.
- **Requirements**: T029-SR-004.

### 4.2 Unit `T29-TS-002` — Mismatch matrix: lifecycle and closed guard

- **Responsibility**: assert the `revoked`/`expired`/`declared`/`armed`/`closing` preconditions map to
  `ActionStatus::NotActive` and that a directly evaluated closed accepted guard is `Failed`/`NotOpen`.
- **Ownership**: owns the fixture and the direct guard instance.
- **Lifetime**: one fixture; one direct guard.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 5 rows; ≤ 5 evaluations.
- **Failure semantics**: fails if a lifecycle precondition emits or journals, or if the closed guard returns a
  non-`Failed` outcome.
- **Requirements**: T029-SR-005.

### 4.3 Unit `T29-TS-003` — Mismatch matrix: quotas

- **Responsibility**: prove the per-session and per-window budget is committed exactly once per authorization and
  that a budget-exhausted request is `Rejected`/`QuotaExhausted` with zero emission.
- **Ownership**: owns the fixture and the quota counters.
- **Lifetime**: one fixture per budget configuration.
- **Thread-safety**: single-threaded.
- **Bounds**: budget 1 … 8; ≤ 16 evaluations.
- **Failure semantics**: fails if a budget-exhausted request is authorized or emits.
- **Requirements**: T029-SR-006.

### 4.4 Unit `T29-TS-004` — Mismatch matrix: loop and lineage

- **Responsibility**: prove a retained causal parent is `Rejected`/`LoopBound`, `causation_id == 0` is never a
  loop, and the lineage window never exceeds its declared depth.
- **Ownership**: owns the fixture, the lineage window, and snapshots.
- **Lifetime**: one fixture per lineage configuration.
- **Thread-safety**: single-threaded.
- **Bounds**: lineage 2, 4, 8; ≤ 16 evaluations.
- **Failure semantics**: fails if a reinjection is authorized or the window exceeds its bound.
- **Requirements**: T029-SR-007.

### 4.5 Unit `T29-TS-005` — Mismatch matrix: unmapped and out-of-tolerance clocks

- **Responsibility**: prove an absent/unmapped/out-of-tolerance resolution fails before emission and journaling,
  an out-of-window value is `Rejected`/`TimeOutOfWindow`, no raw cross-domain comparison occurs, and no time
  authority is called.
- **Ownership**: owns the fixture, the resolved-time values, and the lease registry.
- **Lifetime**: one fixture; times are values.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 8 rows; resolutions `UnknownClock`, `MissingMapping`, `ToleranceExceeded`, `Ok`.
- **Failure semantics**: fails if an unmapped/out-of-tolerance request emits or journals, or if a foreign-domain
  value is compared.
- **Requirements**: T029-SR-008.

### 4.6 Unit `T29-TS-006` — Journal intent precedes single emission

- **Responsibility**: for each of the four action kinds, record the durable byte count inside the single emitter
  call and prove the intent was durable and non-empty before it; a durable host non-delivery maps to the distinct
  non-success statuses.
- **Ownership**: owns the fixture, the recording emitter, and the durable byte view.
- **Lifetime**: one fixture; the recording emitter outlives the action path.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 4 action kinds + 2 non-delivery rows.
- **Failure semantics**: fails if the intent is not durable before the call, the emitter runs more than once, or a
  non-delivery is reported as `Emitted`.
- **Requirements**: T029-SR-009.

### 4.7 Unit `T29-TS-007` — Journal intent append failure emits nothing

- **Responsibility**: inject an intent append failure and an intent sync failure and prove zero emission and zero
  durable records.
- **Ownership**: owns the fault-injecting storage, the fixture, and the emitter counter.
- **Lifetime**: one fixture per injected fault; faults are removed after the row.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 2 injection rows.
- **Failure semantics**: fails if an intent append/sync failure emits or commits a durable record.
- **Requirements**: T029-SR-010.

### 4.8 Unit `T29-TS-008` — Journal outcome failure is evidence-incomplete

- **Responsibility**: inject an outcome append failure after a durable intent and prove `EvidenceIncomplete`,
  never `Emitted`, with exactly one durable intent.
- **Ownership**: owns the fault-injecting storage, the fixture, and the durable byte view.
- **Lifetime**: one fixture per injected fault.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 2 injection rows.
- **Failure semantics**: fails if an incomplete outcome is reported as `Emitted` or success.
- **Requirements**: T029-SR-011.

### 4.9 Unit `T29-TS-009` — Journal restart recovers exact identity

- **Responsibility**: reopen a fresh accepted journal over the same durable bytes and prove the recovered orphan
  identity equals the emitted descriptor identity.
- **Ownership**: owns the durable storage, both journal generations, and the captured descriptor.
- **Lifetime**: the second journal outlives the first; storage outlives both.
- **Thread-safety**: single-threaded.
- **Bounds**: one reopen; ≤ 16 KiB durable bytes.
- **Failure semantics**: fails if recovery loses, changes, or relabels the intent identity.
- **Requirements**: T029-SR-011, T029-SR-015.

### 4.10 Unit `T29-TS-010` — Journal capacity exhaustion fails closed

- **Responsibility**: exceed a declared journal bound and prove `CapacityExhausted` with zero emission and no
  over-bound record.
- **Ownership**: owns the fixture and the bounded journal configuration.
- **Lifetime**: one fixture per bound.
- **Thread-safety**: single-threaded.
- **Bounds**: one bound; ≤ 8 attempts.
- **Failure semantics**: fails if an over-capacity append succeeds, emits, or retains an over-bound record.
- **Requirements**: T029-SR-010.

### 4.11 Unit `T29-TS-011` — Zero emission across every rejection family

- **Responsibility**: for each decline family (Z-01…Z-11) prove zero emitter calls, zero durable byte delta, and
  an operational snapshot unchanged apart from declared counters.
- **Ownership**: owns the fixture, the recording emitter, and pre/post snapshots.
- **Lifetime**: one fixture reused across families.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 11 families; ≤ 11 evaluations.
- **Failure semantics**: fails if any decline emits or mutates state in the declined dimension.
- **Requirements**: T029-SR-012.

### 4.12 Unit `T29-TS-012` — Provenance descriptor carries synthetic identity

- **Responsibility**: for each action kind assert the emitted descriptor carries
  `OriginKind::validation_tool` and the exact tool/permit/session/plan/request/correlation/causation identity.
- **Ownership**: owns the recording emitter and the captured descriptor.
- **Lifetime**: captures are value copies.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 4 emissions.
- **Failure semantics**: fails if the classification or any identity differs.
- **Requirements**: T029-SR-013.

### 4.13 Unit `T29-TS-013` — Provenance survives routing and observation

- **Responsibility**: build the bounded bridge item, submit it through the accepted provider route with the
  observation hub enabled, and assert the retained record preserves the synthetic origin and exact
  correlation/causation identity; assert the `validation_tool` filter matches only synthetic records.
- **Ownership**: owns the bridge, the observation hub/tap/sink, the lifecycle controller, and the provider
  composition.
- **Lifetime**: the hub, controller, and composition outlive the tap and sink.
- **Thread-safety**: single-threaded.
- **Bounds**: one item; one tap; one sink; ≤ 1 commit and ≤ 1 poll.
- **Failure semantics**: fails if the origin is relabelled or the identity is dropped or altered.
- **Requirements**: T029-SR-014.

### 4.14 Unit `T29-TS-014` — Provenance survives journal restart

- **Responsibility**: assert the restarted recovered intent identity equals the emitted descriptor identity and
  the synthetic classification is unchanged.
- **Ownership**: owns the durable storage, both journal generations, and the captured descriptor.
- **Lifetime**: the second journal outlives the first; storage outlives both.
- **Thread-safety**: single-threaded.
- **Bounds**: one reopen.
- **Failure semantics**: fails if the restarted identity differs from the emitted identity.
- **Requirements**: T029-SR-015.

### 4.15 Unit `T29-TS-015` — Provenance is never relabelled

- **Responsibility**: assert no case emits, routes, observes, relabels, or drops provenance; a foreign-origin item
  does not match the synthetic filter.
- **Ownership**: owns the fixture, the bridge, and the observation tap.
- **Lifetime**: one fixture.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 4 emissions; ≤ 2 filter rows.
- **Failure semantics**: fails if any path yields a non-synthetic or identity-less item.
- **Requirements**: T029-SR-013, T029-SR-014.

### 4.16 Unit `T29-TS-016` — Lease conflict matrix end-to-end

- **Responsibility**: prove same-generation conflict, foreign session/generation/plan mismatch, supersession,
  exact-owner release, quarantine, expiry, capacity, no mutation, and zero second-owner emission.
- **Ownership**: owns the registry, the action path, and pre/post snapshots.
- **Lifetime**: one registry per fixture.
- **Thread-safety**: single-threaded.
- **Bounds**: registry capacity 1, 2; ≤ 12 rows.
- **Failure semantics**: fails if a second owner acquires/emits, a foreign identity acquires, or a decline mutates
  an entry.
- **Requirements**: T029-SR-016, T029-SR-017.

### 4.17 Unit `T29-TS-017` — Drain and terminal lifecycle matrix

- **Responsibility**: prove the declared `drain`/`close`/`revoke`/`expire`/`mark_evidence_incomplete` outcomes,
  pending cancellation, lease release/quarantine/expiry, and that an orphan intent is never `Closed`.
- **Ownership**: owns the fixture, the pending queue, the registry, and the completion reports.
- **Lifetime**: one fixture per row group.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 9 rows; `max_drain_steps` 4.
- **Failure semantics**: fails if a completion emits when it must cancel, leaves a held lease, or reports
  `Closed` with an orphan intent.
- **Requirements**: T029-SR-019.

### 4.18 Unit `T29-TS-018` — Drain ordering, late policy, and immediate label

- **Responsibility**: prove ordered drain within the budget, both late-item policies emit nothing, a dropped due
  action surfaces in `CompletionReport.failed`, and an immediate request is explicitly labeled.
- **Ownership**: owns the fixture, the pending queue, and the reports.
- **Lifetime**: one fixture per policy.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_pending_actions` 4, 8; `max_drain_steps` 4; `late_tolerance` 0, 4.
- **Failure semantics**: fails if a late action emits, ordering differs, more than the budget completes, or a
  dropped due action is masked.
- **Requirements**: T029-SR-018, T029-SR-019.

### 4.19 Unit `T29-TS-019` — Concurrent quota and emission determinism

- **Responsibility**: run ≤ 4 threads over a finite declared operation count and prove the declared quota is never
  exceeded, no callback runs under a lock, and three runs are identical.
- **Ownership**: owns one fixture, ≤ 4 joined threads, and the golden result.
- **Lifetime**: every thread is joined before the fixture is destroyed.
- **Thread-safety**: ≤ 4 threads; one declared writer per accepted component.
- **Bounds**: quota 7; ≤ 16 evaluations per thread; 3 runs.
- **Failure semantics**: fails if more than the quota is authorized/emitted, a run differs, or a callback runs
  under a lock.
- **Requirements**: T029-SR-020, T029-SR-021.

### 4.20 Unit `T29-TS-020` — Concurrent lease single winner and completion

- **Responsibility**: run ≤ 4 threads racing one endpoint generation and prove exactly one winner and a
  deterministic final snapshot, including concurrent execution versus completion.
- **Ownership**: owns one registry, ≤ 4 joined threads, and pre/post snapshots.
- **Lifetime**: the registry outlives every thread.
- **Thread-safety**: ≤ 4 threads on one registry.
- **Bounds**: ≤ 4 threads; ≤ 16 acquisition attempts per thread; 3 runs.
- **Failure semantics**: fails if two acquisitions return `Ok`, an unexpected status is returned, or the snapshot
  is non-deterministic.
- **Requirements**: T029-SR-016, T029-SR-020.

## 5. Concurrency/resource bound summary

| Aspect | Bound | Units |
| --- | --- | --- |
| Threads | ≤ 4 | TS-019, TS-020 |
| Writers per accepted component | 1 | all |
| Operations per case | ≤ 64 bounded operations | all |
| Pending queue in tests | 4, 8 | TS-018, TS-019 |
| Drain budget in tests | 4, 8 | TS-018, TS-019 |
| Lineage window in tests | 2, 4, 8 | TS-004 |
| Active leases in tests | 1, 2 | TS-016, TS-020 |
| Guard quota in tests | 1 … 8 | TS-003, TS-019 |
| Durable bytes | ≤ 16 KiB | TS-006…TS-010, TS-014 |
| Injected fault points | ≤ 4 declared | TS-007, TS-008 |
| Wall-clock | none | all |
| Callbacks | exactly one emitter call per `Emitted` action, never under a lock | TS-006, TS-011, TS-019 |
| I/O | none in production; only the test-local in-test storage seam | all |

## 6. Traceability

| Unit | T029 requirements | Accepted software req | Spec anchor | Design unit |
| --- | --- | --- | --- | --- |
| `T29-U-FIXTURE` | T029-SR-003, T029-SR-022 | `XCOM-SW-STIM-009` | SC-007 | `XCOM-DU-018` |
| `T29-TS-001` | T029-SR-004 | `XCOM-SW-STIM-005` | FR-018, FR-019 | `XCOM-DU-017`, `XCOM-DU-018` |
| `T29-TS-002` | T029-SR-005 | `XCOM-SW-STIM-009` | FR-018, SC-007 | `XCOM-DU-015`, `XCOM-DU-018` |
| `T29-TS-003` | T029-SR-006 | `XCOM-SW-STIM-006` | FR-019, FR-020 | `XCOM-DU-017`, `XCOM-DU-018` |
| `T29-TS-004` | T029-SR-007 | `XCOM-SW-STIM-005` | FR-019 | `XCOM-DU-017`, `XCOM-DU-018` |
| `T29-TS-005` | T029-SR-008 | `XCOM-SW-STIM-006` | FR-020, FR-033 | `XCOM-DU-014`, `XCOM-DU-018` |
| `T29-TS-006` | T029-SR-009 | `XCOM-SW-STIM-007` (consumed) | FR-021 | `XCOM-DU-016`, `XCOM-DU-018` |
| `T29-TS-007` | T029-SR-010 | `XCOM-SW-STIM-007`, `-009` | FR-021 | `XCOM-DU-016`, `XCOM-DU-018` |
| `T29-TS-008` | T029-SR-011 | `XCOM-SW-STIM-007`, `-009` | FR-021, SC-007 | `XCOM-DU-016`, `XCOM-DU-018` |
| `T29-TS-009` | T029-SR-011, T029-SR-015 | `XCOM-SW-STIM-003`, `-009` | FR-017, FR-021 | `XCOM-DU-016`, `XCOM-DU-018` |
| `T29-TS-010` | T029-SR-010 | `XCOM-SW-STIM-007`, `-009` | FR-021 | `XCOM-DU-016`, `XCOM-DU-018` |
| `T29-TS-011` | T029-SR-012 | `XCOM-SW-STIM-005`, `-008` | FR-019, FR-034 | `XCOM-DU-018` |
| `T29-TS-012` | T029-SR-013 | `XCOM-SW-STIM-003` | FR-017 | `XCOM-DU-018` |
| `T29-TS-013` | T029-SR-014 | `XCOM-SW-STIM-003` | FR-017, SC-006 | `XCOM-DU-018` |
| `T29-TS-014` | T029-SR-015 | `XCOM-SW-STIM-003` | FR-017 | `XCOM-DU-016`, `XCOM-DU-018` |
| `T29-TS-015` | T029-SR-013, T029-SR-014 | `XCOM-SW-STIM-003` | FR-017 | `XCOM-DU-018` |
| `T29-TS-016` | T029-SR-016, T029-SR-017 | `XCOM-SW-STIM-008` | FR-033, FR-034 | `XCOM-DU-018` |
| `T29-TS-017` | T029-SR-019 | `XCOM-SW-STIM-009` | SC-007 | `XCOM-DU-018` |
| `T29-TS-018` | T029-SR-018, T029-SR-019 | `XCOM-SW-STIM-006`, `-009` | FR-020, SC-007 | `XCOM-DU-018` |
| `T29-TS-019` | T029-SR-020, T029-SR-021 | `XCOM-SW-STIM-008`, `-009` | FR-007, FR-014 | `XCOM-DU-017`, `XCOM-DU-018` |
| `T29-TS-020` | T029-SR-016, T029-SR-020 | `XCOM-SW-STIM-008` | FR-014, FR-034 | `XCOM-DU-018` |

## 7. Maturity and open items

- `XCOM-SW-STIM-009` is **implemented** by T029 (the register's owning task); T029 provides the complete
  owned-fixture action-conformance and lifecycle-completion matrix.
- `XCOM-SW-STIM-003` is **implemented** by the T029 projection: descriptor classification and identity, routed and
  observed preservation, and restart identity persistence. `T029-GAP-02` records that the fixture identity
  projection is test-local and a canonical production projection remains T032/T033.
- `XCOM-SW-STIM-005`/`-006`/`-008` remain **implemented** (T028); T029 supplies the complete cross-cutting
  evidence without changing their disposition.
- `T029-GAP-03` — clean-boundary restart, not a crash-consistency test.
- `T029-GAP-05` — the fixture is T029-local, not the T033 reusable contract suite.
- Strict declaration-level Doxygen execution remains `DOX-GAP-01` (T011/T037); T029 supplies the declarations
  only.

## 8. Negative-case mapping (unit view)

| Unit | Realizes negative cases |
| --- | --- |
| `T29-U-FIXTURE` | NEG-02, NEG-03, NEG-34 |
| `T29-TS-001` | NEG-04, NEG-05, NEG-18, NEG-19 |
| `T29-TS-002` | NEG-06 |
| `T29-TS-003` | NEG-07 |
| `T29-TS-004` | NEG-09, NEG-10, NEG-20 |
| `T29-TS-005` | NEG-11, NEG-12, NEG-26 |
| `T29-TS-006` | NEG-13 |
| `T29-TS-007` | NEG-14, NEG-15 |
| `T29-TS-008` | NEG-16 |
| `T29-TS-009` | NEG-23 |
| `T29-TS-010` | NEG-07 |
| `T29-TS-011` | NEG-04, NEG-05, NEG-06, NEG-18, NEG-19, NEG-20 |
| `T29-TS-012` | NEG-21 |
| `T29-TS-013` | NEG-22, NEG-23 |
| `T29-TS-014` | NEG-23 |
| `T29-TS-015` | NEG-21, NEG-22 |
| `T29-TS-016` | NEG-24, NEG-25 |
| `T29-TS-017` | NEG-17, NEG-29, NEG-30 |
| `T29-TS-018` | NEG-27, NEG-28, NEG-30 |
| `T29-TS-019` | NEG-08, NEG-31, NEG-33 |
| `T29-TS-020` | NEG-24, NEG-31, NEG-32 |
| Build/governance (source inspection) | NEG-01, NEG-35, NEG-36, NEG-37 |
