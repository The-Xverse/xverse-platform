# T028 Unit Specifications — Action Path, Lease Registry, and Test Units: Ownership, Lifetime, Thread-Safety, Bounds, Failure Semantics

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T028 (capability 007, slice `T-STIM`) |
| Stage / role | plan → unit specifications (pre-code) |
| Revision | 1 (guarded actions and exclusive service-emulation lease) |
| Baseline revision | `c518c5e4fcb2055666db25cb62018769e7f56ae4` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Accepted design unit | `XCOM-DU-018` guarded injection and exclusive service-emulation lease (component `XCOM-CMP-009`, contract `XCOM-XLC-006`, boundary `XCOM-XB-007`) |
| Classification | Public-safe engineering work product |

## 2. Unit summary

T028 delivers one production unit composed of six design components (`T28-CMP-VOCAB`, `-MODEL`, `-PATH`,
`-LEASE`, `-EMIT`, `-COMPLETE`) and twenty **test units** across five new GoogleTest executables. A test
unit is one case function plus any case-local helper. The candidate discovers twenty-two case functions:
the twenty declared units below plus the two additional lifecycle case functions
`LifecycleTerminalEvidenceIncompleteNeverClosed` and `LifecycleNonActiveCompletionFailsClosed` (see
`verification-plan.md` CHK-04).

| Unit | Case function | File | Evidence name(s) | Owning slice |
| --- | --- | --- | --- | --- |
| `T28-TS-001` | `ActionPathExecutesNominalActionKinds` | `tests/xcom/stimulation_actions/action_tests.cpp` | `zero-emission-after-rejection` (positive control) | T-STIM |
| `T28-TS-002` | `ActionPathGuardDecisionMapping` | `tests/xcom/stimulation_actions/action_tests.cpp` | `permit-action-mismatch-matrix` (guard mapping) | T-STIM |
| `T28-TS-003` | `ActionPathSyntheticProvenance` | `tests/xcom/stimulation_actions/action_tests.cpp` | `synthetic-provenance` (descriptor half) | T-STIM |
| `T28-TS-004` | `ActionPathVocabularyAndDeterminism` | `tests/xcom/stimulation_actions/action_tests.cpp` | `deterministic-concurrency` (determinism) | T-STIM |
| `T28-TS-005` | `ActionPathConfigAndPreconditionMatrix` | `tests/xcom/stimulation_actions/action_tests.cpp` | `zero-emission-after-rejection` (precondition) | T-STIM |
| `T28-TS-006` | `LeaseAcquireIdentityBindingMatrix` | `tests/xcom/stimulation_actions/lease_tests.cpp` | `lease-conflicts` (identity) | T-STIM |
| `T28-TS-007` | `LeaseConflictAndCapacityMatrix` | `tests/xcom/stimulation_actions/lease_tests.cpp` | `lease-conflicts` | T-STIM |
| `T28-TS-008` | `LeaseReleaseQuarantineMatrix` | `tests/xcom/stimulation_actions/lease_tests.cpp` | `lease-conflicts` (release/quarantine) | T-STIM |
| `T28-TS-009` | `LeaseExpiryAndDomainMatrix` | `tests/xcom/stimulation_actions/lease_tests.cpp` | `unmapped-clocks` (lease expiry) | T-STIM |
| `T28-TS-010` | `LeaseGenerationSupersessionMatrix` | `tests/xcom/stimulation_actions/lease_tests.cpp` | `lease-conflicts` (generation) | T-STIM |
| `T28-TS-011` | `LifecycleScheduledQueueAndOrdering` | `tests/xcom/stimulation_actions/lifecycle_tests.cpp` | `drain-terminal` (queue/order) | T-STIM |
| `T28-TS-012` | `LifecycleLateItemPolicyMatrix` | `tests/xcom/stimulation_actions/lifecycle_tests.cpp` | `drain-terminal` (late), `loop-bounds` (lineage) | T-STIM |
| `T28-TS-013` | `LifecycleDrainCloseRevokeExpire` | `tests/xcom/stimulation_actions/lifecycle_tests.cpp` | `drain-terminal` | T-STIM |
| `T28-TS-014` | `LifecycleEvidenceIncompleteCompletion` | `tests/xcom/stimulation_actions/lifecycle_tests.cpp` | `drain-terminal` (evidence-incomplete) | T-STIM |
| `T28-TS-015` | `LifecycleImmediateAndUnmappedClock` | `tests/xcom/stimulation_actions/lifecycle_tests.cpp` | `unmapped-clocks` (immediate/tolerance) | T-STIM |
| `T28-TS-016` | `ActionPathDeclineZeroMutationAndZeroEmission` | `tests/xcom/stimulation_actions/negative_tests.cpp` | `zero-emission-after-rejection` | T-STIM |
| `T28-TS-017` | `ActionPathClosedAndCapacityReject` | `tests/xcom/stimulation_actions/negative_tests.cpp` | `zero-emission-after-rejection` (precondition) | T-STIM |
| `T28-TS-018` | `ActionPathPayloadFreeDeclarationInspection` | `tests/xcom/stimulation_actions/negative_tests.cpp` | `zero-emission-after-rejection` (surface) | T-STIM |
| `T28-TS-019` | `ActionPathBoundedDeterministicConcurrency` | `tests/xcom/stimulation_actions/concurrency_tests.cpp` | `deterministic-concurrency`, `quotas` | T-STIM |
| `T28-TS-020` | `LeaseConcurrentRaceSingleWinner` | `tests/xcom/stimulation_actions/concurrency_tests.cpp` | `lease-conflicts` (race), `deterministic-concurrency` | T-STIM |

## 3. Production unit `T28-U-PATH` (`XCOM-DU-018`)

- **Responsibility**: evaluate one declared request against the accepted T027 guard, emit exactly once
  through the accepted T026 journal-before-emission path on `Authorized`, carry synthetic provenance,
  bound reinjection, schedule bounded work, and complete the session lifecycle (drain, close, revoke,
  expiry, evidence-incomplete) with zero emission on every decline.
- **Ownership**: `session-issued-handle` — only an action path opened from the session's immutable permit
  may execute; the action path owns its bounded pending queue, lineage window, and counters and copies no
  permit. It retains non-owning references to the accepted journal, the lease registry, and the host emitter.
- **Lifetime**: `session-scoped` — valid for one validation-session scope and retains at most
  `config.max_pending_actions` pending descriptors and `config.max_lineage_entries` lineage entries.
- **Thread-safety**: `internally-synchronized` — one mutex serializes `open`, the checks, the queue, the
  lineage, and the counters; exactly one declared logical writer; the host emitter is invoked without the
  lock and never under a lock.
- **Bounds**: see `detailed-design.md` §7 — `kActionPathMaxPendingActions`, `kActionPathMaxLineage`,
  `kActionPathMaxDrainSteps`, `kActionPathMaxPayloadBytes`, bounded tags, one writer, one bounded queue and
  lineage window.
- **Failure semantics**: the closed `ActionStatus` vocabulary per `detailed-design.md` §6. A decline
  mutates no accepted guard state, lease, queue entry, lineage entry, or durable journal record in the
  declined dimension, emits nothing, and never reports `Emitted`; a guard decline acquires no lease, and a
  durable host `Rejected`/`Unavailable` outcome is reported as a distinct non-success status, never
  `Emitted`. A due pending action dropped by `drain`/`close` is surfaced in `CompletionReport.failed`.
- **Requirements**: T028-SR-001…T028-SR-008, T028-SR-013…T028-SR-024.

## 4. Production unit `T28-U-LEASE` (`XCOM-DU-018`)

- **Responsibility**: atomically acquire, hold, release, quarantine, and expire exclusive
  service-emulation leases bound to the exact session, endpoint, and endpoint generation, enforcing one
  active lease per endpoint generation and per `(endpoint, session)`.
- **Ownership**: `endpoint-generation` — a lease is valid only for the endpoint generation under which it
  was acquired; the registry owns its bounded lease table and is shared across session action paths.
- **Lifetime**: `endpoint-generation` — a lease is active from acquisition to release, quarantine, or
  expiry; released and quarantined entries are retained as bounded tombstones for accounting.
- **Thread-safety**: `internally-synchronized` — one mutex serializes acquisition, release, quarantine,
  expiry, and accounting; exactly one declared logical writer; no callback.
- **Bounds**: active leases ≤ `kActionPathMaxActiveLeases`; the registry also retains bounded tombstones.
- **Failure semantics**: the closed `LeaseStatus` vocabulary per `detailed-design.md` §6; a conflict,
  identity mismatch, unknown key, capacity exhaustion, or expiry comparison never mutates an entry and
  never compares two raw mismatched clock domains. `precheck` returns exactly the `acquire` classification
  without mutating any entry or counter, so the action path can decline before the guard.
- **Requirements**: T028-SR-002, T028-SR-009…T028-SR-012, T028-SR-017, T028-SR-019.

## 5. Test units

### 5.1 Unit `T28-TS-001` — Nominal action kinds

- **Responsibility**: prove each of the four action kinds executes once on a consistent guard with the
  intent durable before the emission.
- **Ownership**: owns the permit, guard policy, config, journal, registry, recording emitter, action path,
  and snapshots it constructs.
- **Lifetime**: the journal, registry, and emitter outlive the action path; snapshots are value copies.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_pending_actions` 8, `max_lineage_entries` 8, four actions, one endpoint generation.
- **Failure semantics**: fails if a nominal action is not `Emitted`, if the emitter ran more than once, if
  the durable intent did not precede the emission, or if a durable host `Rejected`/`Unavailable` outcome is
  reported as `Emitted` instead of `EmissionRejected`/`EmissionUnavailable`.
- **Requirements**: T028-SR-006, T028-SR-007, T028-SR-008.

### 5.2 Unit `T28-TS-002` — Guard-decision mapping

- **Responsibility**: prove every guard decline maps to a non-emitting, non-journaling `ActionStatus` with
  the guard reason preserved, and that a guard-declined `EmulateService` leaves the whole lease table
  (including acquisition and release accounting) byte-identical.
- **Ownership**: owns the guard policy, action path, journal, registry, and snapshots.
- **Lifetime**: one action path per row group.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 9 decline rows; ≤ 9 evaluations.
- **Failure semantics**: fails if a decline emits or journals, acquires or releases a lease, or if the
  action status/reason differs.
- **Requirements**: T028-SR-005, T028-SR-006, T028-SR-017.

### 5.3 Unit `T28-TS-003` — Synthetic provenance

- **Responsibility**: prove the emitted item carries `OriginKind::validation_tool` and the exact tool,
  permit, session, plan, request, correlation, and causal identity.
- **Ownership**: owns the recording emitter and the captured item.
- **Lifetime**: the capture is a value copy.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 4 emissions.
- **Failure semantics**: fails if the classification or any identity differs, or if any path emits a
  differently classified item.
- **Requirements**: T028-SR-007, T028-SR-008.

### 5.4 Unit `T28-TS-004` — Vocabulary and determinism

- **Responsibility**: prove the closed vocabularies have stable names, ranks, and totals and that three
  repeated bounded runs produce identical statuses and snapshots.
- **Ownership**: owns only vocabulary copies and the action path.
- **Lifetime**: static-lifetime vocabulary; snapshots are value copies.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 15 statuses, ≤ 12 lease statuses, ≤ 5 lease states, ≤ 6 completion outcomes, ≤ 3 runs.
- **Failure semantics**: fails if a name/rank is unstable, a vocabulary is not total, or repeated runs
  differ.
- **Requirements**: T028-SR-003, T028-SR-018.

### 5.5 Unit `T28-TS-005` — Config and precondition matrix

- **Responsibility**: prove every row of `detailed-design.md` §5.1 and the closed/malformed/capacity/
  not-active preconditions of §5.2.
- **Ownership**: owns each config/permit pair and the action path construction.
- **Lifetime**: one open attempt per row.
- **Thread-safety**: single-threaded.
- **Bounds**: 8 config rows, 4 precondition rows, no guard call on a precondition row.
- **Failure semantics**: fails if an invalid config is accepted, a legal config is rejected, or a
  precondition decline calls the guard, journals, or mutates state.
- **Requirements**: T028-SR-004, T028-SR-005.

### 5.6 Unit `T28-TS-006` — Lease identity binding

- **Responsibility**: prove the lease key binds session, endpoint, generation, and plan digest, and that a
  foreign identity maps to `LeaseConflict` with the matching `LeaseStatus`.
- **Ownership**: owns the registry, action path, and snapshots.
- **Lifetime**: one registry; leases are values.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 6 identity rows.
- **Failure semantics**: fails if a foreign/mismatched identity acquires or reuses a lease.
- **Requirements**: T028-SR-009.

### 5.7 Unit `T28-TS-007` — Lease conflict and capacity

- **Responsibility**: prove same-generation and same-`(endpoint, session)` conflicts and the capacity
  bound, each with no mutation.
- **Ownership**: owns the registry and pre/post snapshots.
- **Lifetime**: one registry.
- **Thread-safety**: single-threaded.
- **Bounds**: registry capacity 1 and 2; ≤ 6 rows.
- **Failure semantics**: fails if a conflicting acquisition succeeds or mutates an entry.
- **Requirements**: T028-SR-010.

### 5.8 Unit `T28-TS-008` — Lease release and quarantine

- **Responsibility**: prove exact-owner release, unknown/`AlreadyReleased`, quarantine, and
  no-mutation-on-failure.
- **Ownership**: owns the registry and snapshots.
- **Lifetime**: one registry.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 6 rows.
- **Failure semantics**: fails if an unknown/non-owner release mutates state or an invalid status is
  returned.
- **Requirements**: T028-SR-011.

### 5.9 Unit `T28-TS-009` — Lease expiry and domain

- **Responsibility**: prove an elapsed lease becomes inactive, a later acquisition for the generation
  succeeds, and a foreign-domain value is never compared.
- **Ownership**: owns the registry and the caller-supplied times.
- **Lifetime**: one registry; times are values.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 4 rows.
- **Failure semantics**: fails if an elapsed lease remains active, or if a foreign-domain value is
  compared/ordered.
- **Requirements**: T028-SR-012.

### 5.10 Unit `T28-TS-010` — Lease generation supersession

- **Responsibility**: prove a lease under generation `n` neither authorizes nor conflict-blocks generation
  `n+1`, the action path rejects a superseded-generation request, and a second request for an already-held
  generation is `LeaseConflict`/`Conflict` with no second-owner emission.
- **Ownership**: owns the registry, action path, and snapshots.
- **Lifetime**: one registry.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 6 rows; generations `n`, `n+1`.
- **Failure semantics**: fails if a superseded generation is authorized or conflict-blocked, or if a second
  request for a held generation emits or acquires a second lease.
- **Requirements**: T028-SR-009, T028-SR-010, T028-SR-011.

### 5.11 Unit `T28-TS-011` — Scheduled queue and ordering

- **Responsibility**: prove bounded enqueue, the declared ordering rule, and deterministic drain order.
- **Ownership**: owns the action path, pending queue, and snapshots.
- **Lifetime**: one action path.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_pending_actions` 4, `max_drain_steps` 4.
- **Failure semantics**: fails if the queue exceeds its bound, ordering differs, or the drain order is
  non-deterministic.
- **Requirements**: T028-SR-014.

### 5.12 Unit `T28-TS-012` — Late-item and lineage bounds

- **Responsibility**: prove both late-item policies emit nothing, the bounded lineage window rejects a
  prohibited reinjection, and `causation_id == 0` is never a loop.
- **Ownership**: owns the action path, lineage window, and snapshots.
- **Lifetime**: one action path.
- **Thread-safety**: single-threaded.
- **Bounds**: `late_tolerance` 0 and 4; `max_lineage_entries` 2 and 4; ≤ 8 rows.
- **Failure semantics**: fails if a late action emits, a reinjection is authorized, or the lineage window
  exceeds its bound.
- **Requirements**: T028-SR-013, T028-SR-014.

### 5.13 Unit `T28-TS-013` — Drain, close, revoke, expire

- **Responsibility**: prove the §5.5 completion matrix for `drain`, `close`, `revoke`, and `expire`,
  including that a non-active, non-terminal (`declared`/`armed`) completion cancels every pending action
  with zero emission and never returns `Drained`/`Closed`.
- **Ownership**: owns the action path, registry, and reports.
- **Lifetime**: one action path per row group.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 8 completion rows; `max_drain_steps` 4.
- **Failure semantics**: fails if a completion emits when it must cancel, fails to release a lease, emits
  for a non-active state, or returns the wrong outcome.
- **Requirements**: T028-SR-016.

### 5.14 Unit `T28-TS-014` — Evidence-incomplete completion

- **Responsibility**: prove an intent without a durable outcome surfaces `EvidenceIncomplete` and is never
  `Closed` — including from a terminal `closed` `close`/`drain` — that the journal-before-emission order
  holds when the outcome write fails, that a due action whose drain-time intent append fails is surfaced in
  `CompletionReport.failed` and never reported as a clean `Drained`, and that a due action whose drain-time
  outcome append fails leaves exactly one durable intent without a durable outcome, so `drain` and `close`
  return `EvidenceIncomplete` and report that distinct orphan once.
- **Ownership**: owns the action path, a fault-injecting journal storage seam, and the report.
- **Lifetime**: one action path; the storage seam outlives the journal.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 6 rows; one injected outcome-write failure per terminal operation, one injected drain-time
  intent-append failure, and one injected drain-time outcome-append failure per terminal operation.
- **Failure semantics**: fails if an incomplete outcome is reported as `Emitted`/`Closed`, if a terminal
  `closed` completion masks an orphan intent, if a dropped due action is reported as `Drained`, if an
  incomplete drain is reported as `Drained`, if a distinct orphan intent is counted twice, or if the intent
  did not precede the emission.
- **Requirements**: T028-SR-007, T028-SR-016.

### 5.15 Unit `T28-TS-015` — Immediate labeling and unmapped clock

- **Responsibility**: prove an immediate action is labeled and interpreted in the validity domain and an
  unmapped/out-of-tolerance resolution fails before emission and before journaling.
- **Ownership**: owns the action path, resolved-time values, and the journal.
- **Lifetime**: one action path; times are values.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 5 rows; resolutions `UnknownClock`, `MissingMapping`, `ToleranceExceeded`,
  `ClockSourceFailure`.
- **Failure semantics**: fails if an unmapped/out-of-tolerance request emits or journals, or if an
  immediate request is mislabeled.
- **Requirements**: T028-SR-015.

### 5.16 Unit `T28-TS-016` — Decline: zero mutation and zero emission

- **Responsibility**: for each decline family prove the snapshot is byte-identical (except declared
  counters), the lease table and pending queue are unchanged, and the recording emitter observed no call;
  a guard quota decline on an emulation action leaves the full lease snapshot (including `acquisitions`
  and `released`) byte-identical.
- **Ownership**: owns the action path, registry, recording emitter, and pre/post snapshots.
- **Lifetime**: one action path reused across decline families.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 11 decline families; ≤ 11 evaluations.
- **Failure semantics**: fails if any decline mutates operational state or emits.
- **Requirements**: T028-SR-017.

### 5.17 Unit `T28-TS-017` — Closed and capacity reject

- **Responsibility**: prove `NotOpen`, `CapacityExhausted`, and `RejectedConfiguration` occur before any
  guard call or journal.
- **Ownership**: owns the default-constructed and over-capacity action paths and snapshots.
- **Lifetime**: one action path per row.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 5 rows.
- **Failure semantics**: fails if a closed/over-capacity/malformed request reaches the guard or journal, or
  mutates state.
- **Requirements**: T028-SR-005, T028-SR-017.

### 5.18 Unit `T28-TS-018` — Payload-free declaration inspection

- **Responsibility**: prove the comment-stripped header and source expose no payload-retaining member and no
  forbidden I/O/emission vocabulary, with a non-vacuous compile-time payload-free/size rule.
- **Ownership**: owns the bounded scan of the committed header and source.
- **Lifetime**: one bounded scan per run.
- **Thread-safety**: single-threaded.
- **Bounds**: header ≤ 128 KiB, source ≤ 128 KiB.
- **Failure semantics**: fails if a payload-retaining member, an unbounded value, or a forbidden vocabulary
  appears.
- **Requirements**: T028-SR-004, T028-SR-020.

### 5.19 Unit `T28-TS-019` — Bounded deterministic concurrency

- **Responsibility**: prove ≤ 4 threads submitting bounded immediate actions to one action path with a
  declared guard quota commit exactly the quota and match the single-threaded golden sequence over three
  runs.
- **Ownership**: owns one action path, 4 joined threads, and the golden sequence.
- **Lifetime**: every thread is joined before the action path is destroyed.
- **Thread-safety**: ≤ 4 threads, one declared writer; the guard serializes the check-and-commit.
- **Bounds**: guard quota 7; ≤ 16 evaluations per thread; 3 repeated runs.
- **Failure semantics**: fails if more than the declared quota is `Emitted`, if any guard sequence differs
  from the golden one, or if repeated runs differ.
- **Requirements**: T028-SR-019.

### 5.20 Unit `T28-TS-020` — Concurrent lease race

- **Responsibility**: prove ≤ 4 threads racing to acquire one endpoint generation produce exactly one
  winner and the remainder `Conflict`, with a deterministic final snapshot.
- **Ownership**: owns one registry, ≤ 4 joined threads, and the pre/post snapshots.
- **Lifetime**: the registry outlives every thread.
- **Thread-safety**: ≤ 4 threads on one registry, which serializes acquisition.
- **Bounds**: ≤ 4 threads; ≤ 16 acquisition attempts per thread.
- **Failure semantics**: fails if two acquisitions return `Ok`, if any returns an unexpected status, or if
  the snapshot is non-deterministic.
- **Requirements**: T028-SR-010, T028-SR-019.

## 6. Concurrency/resource bound summary

| Aspect | Bound | Units |
| --- | --- | --- |
| Threads | ≤ 4 | TS-019, TS-020 |
| Writers per action path / registry | 1 | all |
| Actions per action path | ≤ guard policy quota | all |
| Pending queue in tests | 4, 8 | TS-011, TS-012 |
| Lineage window in tests | 2, 4, 8 | TS-012 |
| Drain budget in tests | 4, 8 | TS-011, TS-012, TS-013 |
| Active leases in tests | 1, 2 | TS-006…TS-010, TS-020 |
| Endpoint generations in tests | `n`, `n+1` | TS-010 |
| Iterations | ≤ 64 bounded operations per case | all |
| Wall-clock | none | all |
| Callbacks | exactly one emitter call per `Emitted` action, never under a lock | TS-001, TS-016, TS-019 |
| I/O | none in production; only the test-local injected journal storage seam | all |

## 7. Traceability

| Unit | T028 requirements | Accepted software req | Spec anchor | Design unit |
| --- | --- | --- | --- | --- |
| `T28-TS-001` | T028-SR-006, T028-SR-007, T028-SR-008 | `XCOM-SW-STIM-005/008` | FR-019, FR-034 | `XCOM-DU-018` |
| `T28-TS-002` | T028-SR-005, T028-SR-006, T028-SR-017 | `XCOM-SW-STIM-005` | FR-019 | `XCOM-DU-018` |
| `T28-TS-003` | T028-SR-007, T028-SR-008 | `XCOM-SW-STIM-003` (partial) | FR-017 | `XCOM-DU-018` |
| `T28-TS-004` | T028-SR-003, T028-SR-018 | `XCOM-SW-STIM-006` | FR-025 | `XCOM-DU-018` |
| `T28-TS-005` | T028-SR-004, T028-SR-005 | `XCOM-SW-STIM-008` | FR-034 | `XCOM-DU-018` |
| `T28-TS-006` | T028-SR-009 | `XCOM-SW-STIM-008` | FR-034 | `XCOM-DU-018` |
| `T28-TS-007` | T028-SR-010 | `XCOM-SW-STIM-008` | FR-034 | `XCOM-DU-018` |
| `T28-TS-008` | T028-SR-011 | `XCOM-SW-STIM-008` | FR-034 | `XCOM-DU-018` |
| `T28-TS-009` | T028-SR-012 | `XCOM-SW-STIM-006/008` | FR-033, FR-034 | `XCOM-DU-018` |
| `T28-TS-010` | T028-SR-009, T028-SR-011 | `XCOM-SW-STIM-008` | FR-034 | `XCOM-DU-018` |
| `T28-TS-011` | T028-SR-014 | `XCOM-SW-STIM-006` | FR-020 | `XCOM-DU-018` |
| `T28-TS-012` | T028-SR-013, T028-SR-014 | `XCOM-SW-STIM-005/006` | FR-019, FR-020 | `XCOM-DU-018` |
| `T28-TS-013` | T028-SR-016 | `XCOM-SW-STIM-009` (partial) | SC-007 | `XCOM-DU-018` |
| `T28-TS-014` | T028-SR-007, T028-SR-016 | `XCOM-SW-STIM-009` (partial) | FR-021, SC-007 | `XCOM-DU-018` |
| `T28-TS-015` | T028-SR-015 | `XCOM-SW-STIM-006` | FR-020, FR-033 | `XCOM-DU-018` |
| `T28-TS-016` | T028-SR-017 | `XCOM-SW-STIM-005/008` | FR-019, FR-034 | `XCOM-DU-018` |
| `T28-TS-017` | T028-SR-005, T028-SR-017 | `XCOM-SW-STIM-005` | FR-019 | `XCOM-DU-018` |
| `T28-TS-018` | T028-SR-004, T028-SR-020 | `XCOM-SW-STIM-008` | FR-027 | `XCOM-DU-018` |
| `T28-TS-019` | T028-SR-019 | `XCOM-SW-STIM-008` | FR-007, FR-014 | `XCOM-DU-018` |
| `T28-TS-020` | T028-SR-010, T028-SR-019 | `XCOM-SW-STIM-008` | FR-014, FR-034 | `XCOM-DU-018` |

## 8. Bounds and open items

- `XCOM-SW-STIM-003` is **partial**: T028 proves only the synthetic classification and identity on the
  emitted descriptor (`T28-TS-003`); routed/restarted provenance is T029/T033 (`T028-GAP-02`).
- `XCOM-SW-STIM-009` is **partial**: T028 proves the four action kinds and the completion mechanics
  (`T28-TS-001`, `T28-TS-011`…`T28-TS-014`); the complete owned-fixture conformance matrix is T029
  (`T028-GAP-03`).
- The emission seam is host-supplied and the transport realization is the accepted T-CORE provider
  boundary; T028 authors no route/provider (`T028-GAP-01`).
- Strict declaration-level Doxygen execution remains `DOX-GAP-01` (T011/T037); T028 supplies the
  declarations only.
- `XCOM-DU-018` bound source and public-element count are reconciled in the T028 implementation record as a
  successor note (`T028-OPEN-01`).
- The lease table is single-process and single-writer; distributed arbitration is not claimed
  (`T028-GAP-05`).

## 9. Negative-case mapping (unit view)

| Unit | Realizes negative cases |
| --- | --- |
| `T28-TS-001` | positive control for NEG-26, NEG-27 |
| `T28-TS-002` | NEG-06, NEG-26, NEG-27 |
| `T28-TS-003` | NEG-08 |
| `T28-TS-004` | NEG-28 |
| `T28-TS-005` | NEG-33, NEG-34 |
| `T28-TS-006` | NEG-09, NEG-10 |
| `T28-TS-007` | NEG-11, NEG-29 |
| `T28-TS-008` | NEG-12, NEG-13 |
| `T28-TS-009` | NEG-14, NEG-23 |
| `T28-TS-010` | NEG-10, NEG-13 |
| `T28-TS-011` | NEG-17 |
| `T28-TS-012` | NEG-15, NEG-16, NEG-18 |
| `T28-TS-013` | NEG-20, NEG-21, NEG-22 |
| `T28-TS-014` | NEG-07, NEG-25 |
| `T28-TS-015` | NEG-19, NEG-23, NEG-24 |
| `T28-TS-016` | NEG-26, NEG-27 |
| `T28-TS-017` | NEG-33, NEG-34 |
| `T28-TS-018` | NEG-03, NEG-04, NEG-05, NEG-30, NEG-31 |
| `T28-TS-019` | NEG-29, NEG-36 |
| `T28-TS-020` | NEG-11, NEG-29, NEG-36 |
| Production units (`T28-U-PATH`, `T28-U-LEASE`) | NEG-01, NEG-02, NEG-30, NEG-32 (source-inspection cases) |
