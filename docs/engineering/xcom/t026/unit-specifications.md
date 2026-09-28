# T026 Unit Specifications — Journal Units and Test Units: Ownership, Lifetime, Thread-Safety, Bounds, Failure Semantics

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T026 (capability 007, slice `T-STIM`) |
| Stage / role | plan → unit specifications (pre-code) |
| Revision | 1 (durable stimulation journal) |
| Baseline revision | `1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Accepted design unit | `XCOM-DU-016` durable stimulation intent/outcome journal (component `XCOM-CMP-009`, contract `XCOM-XLC-006`) |
| Classification | Public-safe engineering work product |

## 2. Unit summary

T026 delivers one production unit composed of five design components (`T26-CMP-MODEL`, `-JOURNAL`,
`-FRAME`, `-STORAGE`, `-RECOVERY`) and eighteen **test units** across five new GoogleTest executables. A test
unit is one case function plus any case-local helper.

| Unit | Case function | File | Evidence name(s) | Owning slice |
| --- | --- | --- | --- | --- |
| `T26-TS-001` | `test_journal_frame_layout_and_roundtrip` | `tests/xcom/stimulation_journal/unit_tests.cpp` | `journal-before-emission` (framing) | T-STIM |
| `T26-TS-002` | `test_journal_config_validation_matrix` | `tests/xcom/stimulation_journal/unit_tests.cpp` | `journal-failure-recovery` (config) | T-STIM |
| `T26-TS-003` | `test_journal_record_size_and_tag_matrix` | `tests/xcom/stimulation_journal/unit_tests.cpp` | `journal-failure-recovery` (bounds) | T-STIM |
| `T26-TS-004` | `test_journal_status_determinism_and_no_mutation` | `tests/xcom/stimulation_journal/unit_tests.cpp` | `deterministic-concurrency` (determinism) | T-STIM |
| `T26-TS-005` | `test_journal_snapshot_and_capacity_accounting` | `tests/xcom/stimulation_journal/unit_tests.cpp` | `journal-failure-recovery` (accounting) | T-STIM |
| `T26-TS-006` | `test_journal_capacity_bound_matrix` | `tests/xcom/stimulation_journal/negative_tests.cpp` | `journal-failure-recovery` (capacity) | T-STIM |
| `T26-TS-007` | `test_journal_resolution_reference_matrix` | `tests/xcom/stimulation_journal/negative_tests.cpp` | `journal-failure-recovery` (resolution) | T-STIM |
| `T26-TS-008` | `test_journal_callback_contract_matrix` | `tests/xcom/stimulation_journal/negative_tests.cpp` | `journal-before-emission` (callback) | T-STIM |
| `T26-TS-009` | `test_journal_restart_recovery_and_orphans` | `tests/xcom/stimulation_journal/recovery_tests.cpp` | `journal-failure-recovery` | T-STIM |
| `T26-TS-010` | `test_journal_torn_tail_and_corrupt_frame` | `tests/xcom/stimulation_journal/recovery_tests.cpp` | `journal-failure-recovery` | T-STIM |
| `T26-TS-011` | `test_journal_provenance_roundtrip_matrix` | `tests/xcom/stimulation_journal/recovery_tests.cpp` | `synthetic-provenance` (journal half) | T-STIM |
| `T26-TS-012` | `test_journal_write_failure_no_emission` | `tests/xcom/stimulation_journal/failure_tests.cpp` | `journal-before-emission` | T-STIM |
| `T26-TS-013` | `test_journal_sync_failure_and_partial_write` | `tests/xcom/stimulation_journal/failure_tests.cpp` | `journal-failure-recovery` | T-STIM |
| `T26-TS-014` | `test_journal_outcome_write_failure_orphan` | `tests/xcom/stimulation_journal/failure_tests.cpp` | `journal-failure-recovery` | T-STIM |
| `T26-TS-015` | `test_journal_bounded_deterministic_concurrency` | `tests/xcom/stimulation_journal/concurrency_tests.cpp` | `deterministic-concurrency` | T-STIM |
| `T26-TS-016` | `test_journal_callback_outside_lock_probe` | `tests/xcom/stimulation_journal/concurrency_tests.cpp` | `deterministic-concurrency` | T-STIM |
| `T26-TS-017` | `test_journal_over_bound_recovery_fails_closed` | `tests/xcom/stimulation_journal/recovery_tests.cpp` | `journal-failure-recovery` (bounds) | T-STIM |
| `T26-TS-018` | `test_journal_over_long_recovered_tag_is_corrupt` | `tests/xcom/stimulation_journal/recovery_tests.cpp` | `journal-failure-recovery` (bounds) | T-STIM |

## 3. Production unit `T26-U-JOURNAL` (`XCOM-DU-016`)

- **Responsibility**: durably record a payload-free stimulation intent before emission and an explicit
  outcome after emission; bound records and bytes; frame and verify each record; recover orphans as
  `EvidenceIncomplete` and support an explicit resolution.
- **Ownership**: `platform-owns-shared` — the journal owns its bounded index and, for `open_local_file`,
  its file storage; a caller-supplied `Storage` reference is non-owning and must outlive the journal.
  Header type `StimulationJournal` owns no payload view; produced values (`Snapshot`, `RecoveryReport`,
  `StimulationIntent`, `StimulationOutcome`) are caller-owned copies.
- **Lifetime**: `session-scoped` — the journal is valid for the validation-session scope and retains at
  most `max_retained_records` records; a `Storage` reference and any scratch file must outlive the journal
  and every callback.
- **Thread-safety**: `internally-synchronized` — one per-journal mutex serializes appends, capacity
  accounting, boundary restoration, and the index; exactly one declared writer; the emission callback is
  invoked with the mutex released.
- **Bounds**: see `detailed-design.md` §8 — `max_record_bytes`, `max_retained_records`, `max_journal_bytes`,
  bounded tags, one writer, one bounded frame buffer.
- **Failure semantics**: `RejectedConfiguration`, `RecordTooLarge`, `CorruptRecord`, `PartialWrite`,
  `WriteFailed`, `CapacityExhausted`, `AlreadyResolved`, `NotFound`, `EvidenceIncomplete`, `Ok` per
  `detailed-design.md` §7. A failure mutates no complete retained record and never reports success. An
  out-of-vocabulary `OutcomeKind` and a `request_id` already carried by a retained intent are
  `RejectedConfiguration` with no append (and no emission for the request-identity case). Orphan
  accounting is one-to-one.
- **Requirements**: T026-SR-001…T026-SR-018, T026-SR-020.

## 4. Unit `T26-TS-001` — Frame layout and round-trip

- **Responsibility**: prove the exact frame layout and canonical codec for minimal/maximal intents and an
  outcome over an in-memory storage.
- **Ownership**: owns the storage, journal, intents, outcomes, and copied index values it constructs; the
  storage outlives the journal.
- **Lifetime**: all values live for the case body; reopened values are copies.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_record_bytes` 320, `max_retained_records` 4 and 8, `max_journal_bytes` 4096; ≤ 2 records.
- **Failure semantics**: fails if any offset, magic, version, kind, length, or digest differs from
  `detailed-design.md` §4, or if a round-trip loses a field.
- **Requirements**: T026-SR-003, T026-SR-008, T026-SR-016.

## 5. Unit `T26-TS-002` — Configuration validation matrix

- **Responsibility**: prove every configuration row of `detailed-design.md` §6.1.
- **Ownership**: owns each config value, storage, and rejected journal construction.
- **Lifetime**: single open attempt per row; no durable state on rejection.
- **Thread-safety**: single-threaded.
- **Bounds**: 7 configuration rows (`max_record_bytes` 0/154/155/320, `max_retained_records` 0/1/64,
  `max_journal_bytes` 0/155/319/16384); ≤ 1 open each; one fresh in-memory storage per row.
- **Failure semantics**: fails if a zero/inconsistent bound is accepted or a legal minimum bound is
  rejected, or if a rejected open mutates a byte.
- **Requirements**: T026-SR-012.

## 6. Unit `T26-TS-003` — Record-size and tag matrix

- **Responsibility**: prove the §6.2 size and tag rows with no-append on rejection.
- **Ownership**: owns the storage, journal, and candidate intent values.
- **Lifetime**: each rejected intent is a value that never becomes durable.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_record_bytes` 155 and 320, `max_retained_records` 4, `max_journal_bytes` 2048 and 4096;
  tag lengths 0/1/3/63/64; ≤ 5 intents.
- **Failure semantics**: fails if an over-size or invalid-tag intent is appended, or if a legal 63-byte tag
  is rejected.
- **Requirements**: T026-SR-004.

## 7. Unit `T26-TS-004` — Status determinism and no-mutation

- **Responsibility**: prove the closed status vocabulary, stable names/ranks, and byte-identical
  no-mutation after a rejected operation.
- **Ownership**: owns each snapshot, journal, and storage.
- **Lifetime**: snapshots are value copies taken before and after a rejection.
- **Thread-safety**: single-threaded; three repeated bounded runs.
- **Bounds**: `max_record_bytes` 320, `max_retained_records` 4, `max_journal_bytes` 4096; ≤ 10 statuses;
  ≤ 3 runs; ≤ 2 records.
- **Failure semantics**: fails if a name/rank is unstable, if a rejected operation changes the snapshot or
  bytes, or if repeated runs differ.
- **Requirements**: T026-SR-016.

## 8. Unit `T26-TS-005` — Snapshot and capacity accounting

- **Responsibility**: prove the §6.3 accounting table and the `bytes == Σ frame sizes` identity.
- **Ownership**: owns the storage, journal, and snapshots.
- **Lifetime**: journal scoped to the case; snapshots are copies.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_record_bytes` 320, `max_retained_records` 4, `max_journal_bytes` 4096; ≤ 2 records.
- **Failure semantics**: fails if a counter differs from the table or the byte identity does not hold.
- **Requirements**: T026-SR-011, T026-SR-016.

## 9. Unit `T26-TS-006` — Capacity-bound matrix

- **Responsibility**: prove fail-closed exhaustion at the record-count and byte bounds with zero emission
  and complete-record preservation.
- **Ownership**: owns each storage, journal, callback probe, and snapshot.
- **Lifetime**: the callback probe outlives the journal call.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_record_bytes` 157 and 320, `max_retained_records` 1 and 4, `max_journal_bytes` 200, 350,
  and 4096; ≤ 5 intents.
- **Failure semantics**: fails if exhaustion emits, drops, overwrites, or truncates a complete record, or
  reports a status other than `CapacityExhausted`.
- **Requirements**: T026-SR-011.

## 10. Unit `T26-TS-007` — Resolution reference matrix

- **Responsibility**: prove `NotFound`, `AlreadyResolved`, `Unknown`-stays-`Unknown`, the out-of-vocabulary
  rejection, and the unique-request-identity rejection.
- **Ownership**: owns the storage, journal, and resolution outcomes.
- **Lifetime**: resolutions reference durable intents; the journal outlives them.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_record_bytes` 320, `max_retained_records` 8, `max_journal_bytes` 4096; ≤ 3 intents;
  ≤ 7 resolutions; one repeated-identity attempt.
- **Failure semantics**: fails if an unknown reference mutates state, a duplicate resolution is accepted,
  `Unknown` is relabelled `Delivered`, an out-of-vocabulary kind is appended, or a repeated `request_id`
  intent is appended or emits.
- **Requirements**: T026-SR-003, T026-SR-005, T026-SR-014.

## 11. Unit `T26-TS-008` — Callback contract matrix

- **Responsibility**: prove the null-callback rejection, the throwing-callback orphan behaviour, and the
  out-of-vocabulary callback-return rejection.
- **Ownership**: owns the storage, journal, callback probe, and captured exception.
- **Lifetime**: the callback probe is valid for the call; the journal survives the throw.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_record_bytes` 320, `max_retained_records` 8, `max_journal_bytes` 4096; ≤ 3 callback
  scenarios; ≤ 2 intents.
- **Failure semantics**: fails if a null callback writes an intent or returns `Ok`, if a throwing callback
  leaves a non-orphan state or is reported as success, or if an out-of-vocabulary callback result is
  appended or makes the reopen `CorruptRecord`.
- **Requirements**: T026-SR-007.

## 12. Unit `T26-TS-009` — Restart recovery and orphans

- **Responsibility**: prove the complete-content §6.4 rows across a real-file close/reopen cycle,
  including one-to-one orphan accounting over a crafted duplicate identity.
- **Ownership**: owns the scratch directory handle, the file storage, the journal, and the report copies;
  removes only its own scratch files.
- **Lifetime**: the file storage is destroyed before the scratch directory is cleaned.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_record_bytes` 320, `max_retained_records` 8, `max_journal_bytes` 4096; 7 scratch-file
  scenarios; ≤ 2 scratch files per scenario; ≤ 3 records per file; ≤ 2 crafted duplicate records.
- **Failure semantics**: fails if an orphan is reported delivered, if an unresolved duplicate intent is
  counted resolved, if a complete pair is lost, or if the report differs from §6.4.
- **Requirements**: T026-SR-013.

## 13. Unit `T26-TS-010` — Torn tail and corrupt frame

- **Responsibility**: prove tail discard, `CorruptRecord` stop, and preservation of complete preceding
  records.
- **Ownership**: owns the scratch file and injects a bounded torn tail/corrupted digest directly.
- **Lifetime**: one file per scenario; cleanup after reopen.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_record_bytes` 320, `max_retained_records` 8, `max_journal_bytes` 4096; torn tail 40
  bytes (< one frame); 2 scenarios; ≤ 1 complete record before the defect.
- **Failure semantics**: fails if a torn tail is retained as a record, if a corrupt frame yields a false
  orphan, or if preceding complete records are discarded.
- **Requirements**: T026-SR-009, T026-SR-010.

## 14. Unit `T26-TS-011` — Provenance round-trip matrix

- **Responsibility**: prove every §3.3 identity field survives a restart (`XCOM-SW-STIM-003` journal half).
- **Ownership**: owns the storage, journal, intent values, and recovered copies.
- **Lifetime**: values are copied out before the journal is destroyed.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_record_bytes` 320, `max_retained_records` 8, `max_journal_bytes` 4096; ≤ 3 intents with
  distinct identity tuples; 1 reopen cycle.
- **Failure semantics**: fails if any of permit id, session id, plan digest, request/correlation/causation
  id, action mask, target, tool, quota cost, clock domain, scheduled timestamp, or immediate flag differs
  after recovery.
- **Requirements**: T026-SR-015.

## 15. Unit `T26-TS-012` — Write failure, no emission

- **Responsibility**: prove an intent write failure invokes the callback zero times.
- **Ownership**: owns the fault-injecting storage, journal, and callback counter.
- **Lifetime**: the fault is configured before the call and cleared afterwards.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_record_bytes` 320, `max_retained_records` 4, `max_journal_bytes` 4096; ≤ 3 injected
  failure points; 1 intent.
- **Failure semantics**: fails if the callback runs, if any intent byte is retained, or if the status is
  `Ok`.
- **Requirements**: T026-SR-005.

## 16. Unit `T26-TS-013` — Sync failure and partial write

- **Responsibility**: prove `sync` failure and short-append detection with boundary restoration.
- **Ownership**: owns the fault-injecting storage, journal, and snapshots.
- **Lifetime**: one fault per scenario; boundary restored before the next scenario.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_record_bytes` 320, `max_retained_records` 4, `max_journal_bytes` 4096; ≤ 3 injected
  failures (sync failure; sync failure with failed boundary restoration; a post-failure append).
- **Failure semantics**: fails if a partial frame is retained, if the journal reports `Ok`, or if a
  complete preceding record is lost.
- **Requirements**: T026-SR-009.

## 17. Unit `T26-TS-014` — Outcome write failure orphan

- **Responsibility**: prove an outcome write failure yields `EvidenceIncomplete` and exactly one recovered
  orphan.
- **Ownership**: owns the fault-injecting storage, journal, callback probe, and recovery report.
- **Lifetime**: the intent is durable before the injected outcome failure.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_record_bytes` 320, `max_retained_records` 4, `max_journal_bytes` 4096; 1 intent + 1
  failed outcome.
- **Failure semantics**: fails if success is reported, if the callback did not run once, or if recovery
  reports zero/multiple orphans.
- **Requirements**: T026-SR-006.

## 18. Unit `T26-TS-015` — Bounded deterministic concurrency

- **Responsibility**: prove independent journals driven in parallel produce the single-threaded golden
  byte stream.
- **Ownership**: owns 4 independent in-memory storages, 4 journals, 4 joined threads, and the golden
  stream.
- **Lifetime**: every thread is joined before its journal and storage are destroyed.
- **Thread-safety**: ≤ 4 threads, one writer per journal, no shared mutable state between journals; atomic
  flags only.
- **Bounds**: `max_record_bytes` 320, `max_retained_records` 16, `max_journal_bytes` 8192; ≤ 4 threads;
  4 bounded operations per journal; 3 repeated runs.
- **Failure semantics**: fails if any journal's bytes differ from the golden stream or if repeated runs
  differ.
- **Requirements**: T026-SR-017.

## 19. Unit `T26-TS-016` — Callback outside the lock

- **Responsibility**: prove the emission callback runs with the journal mutex released.
- **Ownership**: owns the storage, journal, and a probe that calls `snapshot()`/a bounded append from
  inside the callback.
- **Lifetime**: the probe is valid for the call.
- **Thread-safety**: single-threaded but re-entrant by construction; the probe must not deadlock.
- **Bounds**: `max_record_bytes` 320, `max_retained_records` 4, `max_journal_bytes` 4096; 1 intent + 1
  outcome.
- **Failure semantics**: fails if the probe deadlocks (bounded timeout) or if the callback cannot observe
  an unlocked journal.
- **Requirements**: T026-SR-017.

## 20. Unit `T26-TS-017` — Over-bound recovery fails closed

- **Responsibility**: prove a durable journal that exceeds the declared retained-record or byte bound is
  refused at recovery (`CapacityExhausted`) with no over-bound index and no further append.
- **Ownership**: owns the writer journal that pre-populates a real scratch file, the reader journal, and
  the recovered copies; removes only its own scratch files.
- **Lifetime**: the writer is destroyed before the reader opens the file.
- **Thread-safety**: single-threaded.
- **Bounds**: writer config `{320, 64, 16384}`; ≤ 6 pre-populated pairs and ≤ 4 pre-populated intents;
  tighter reopen config `{320, 2, 320}` and `{320, 2, 4096}`; ≤ 1 later append attempt.
- **Failure semantics**: fails if the reopen reports `Ok`, if `retained_records`/`retained_bytes`/
  `recovered_intents()` exceed the tighter bound, or if a further append emits or mutates bytes.
- **Requirements**: T026-SR-011, T026-SR-013.

## 21. Unit `T26-TS-018` — Out-of-contract recovered tag is corrupt

- **Responsibility**: prove a digest-valid intent frame whose declared tag length or bytes violate the
  `Tag` contract is rejected as `CorruptRecord` with no recovered value and no false orphan.
- **Ownership**: owns the independently crafted frame bytes and the scratch file; it derives the digests
  with the accepted `canonical_digest` rather than the production encoder.
- **Lifetime**: one crafted frame per scenario; the file is removed after the reopen.
- **Thread-safety**: single-threaded.
- **Bounds**: `max_record_bytes` 320, `max_retained_records` 8, `max_journal_bytes` 4096; 2 crafted frames
  (64-byte target; NUL-containing target), each ≤ `max_record_bytes`.
- **Failure semantics**: fails if an over-long or NUL tag frame is reported `Ok`, yields a recovered
  intent, or produces a false orphan.
- **Requirements**: T026-SR-004, T026-SR-010, T026-SR-013.

## 22. Concurrency/resource bound summary

The per-case values below are the realized `JournalConfig` fields and iteration counts of the five test
executables, not plan estimates.

| Aspect | Bound | Units |
| --- | --- | --- |
| Threads | ≤ 4 | TS-015 |
| Writers per journal | 1 | all |
| Records per journal | ≤ 12 realized records (T26-TS-017 writer); contract `≤ max_retained_records` | all |
| `max_retained_records` values in tests | 0, 1, 2, 4, 8, 16, 64 | all |
| Frame bytes | ≤ `max_record_bytes` (realized frames 66…281) | all |
| `max_record_bytes` values in tests | 0, 154 (rejection rows), 155, 157, 320 | all |
| Journal bytes | ≤ `max_journal_bytes` (realized files ≤ 16384 bytes) | all |
| `max_journal_bytes` values in tests | 0, 155, 200, 319, 320, 350, 2048, 4096, 8192, 16384 (0/319 are rejection rows) | all |
| Scratch files | ≤ 2 per case, ≤ `max_journal_bytes` each | TS-009, TS-010, TS-011 |
| Iterations | ≤ 64 bounded journal operations per case (realized maximum 52 in T26-TS-015) | all |
| Wall-clock | none | all |
| Callbacks under lock | none | all |

## 23. Traceability

| Unit | T026 requirements | Accepted software req | Spec / success anchor | Design unit |
| --- | --- | --- | --- | --- |
| `T26-TS-001` | T026-SR-003, T026-SR-008, T026-SR-016 | `XCOM-SW-STIM-007` | FR-021 | `XCOM-DU-016` |
| `T26-TS-002` | T026-SR-012 | `XCOM-SW-STIM-007` | FR-007, FR-021 | `XCOM-DU-016` |
| `T26-TS-003` | T026-SR-004 | `XCOM-SW-STIM-007` | FR-007, FR-021 | `XCOM-DU-016` |
| `T26-TS-004` | T026-SR-016 | `XCOM-SW-STIM-007` | FR-021, FR-025 | `XCOM-DU-016` |
| `T26-TS-005` | T026-SR-011, T026-SR-016 | `XCOM-SW-STIM-007` | FR-007, FR-021 | `XCOM-DU-016` |
| `T26-TS-006` | T026-SR-011 | `XCOM-SW-STIM-007` | FR-007, FR-021 | `XCOM-DU-016` |
| `T26-TS-007` | T026-SR-014 | `XCOM-SW-STIM-007` | FR-021 | `XCOM-DU-016` |
| `T26-TS-008` | T026-SR-007 | `XCOM-SW-STIM-007` | FR-021 | `XCOM-DU-016` |
| `T26-TS-009` | T026-SR-013 | `XCOM-SW-STIM-007` | FR-021 | `XCOM-DU-016` |
| `T26-TS-010` | T026-SR-009, T026-SR-010 | `XCOM-SW-STIM-007` | FR-021 | `XCOM-DU-016` |
| `T26-TS-011` | T026-SR-015 | `XCOM-SW-STIM-003` | FR-017, SC-006 | `XCOM-DU-016` (routing/observation half `XCOM-DU-018`, T028) |
| `T26-TS-012` | T026-SR-005 | `XCOM-SW-STIM-007` | FR-021 | `XCOM-DU-016` |
| `T26-TS-013` | T026-SR-009 | `XCOM-SW-STIM-007` | FR-021 | `XCOM-DU-016` |
| `T26-TS-014` | T026-SR-006 | `XCOM-SW-STIM-007` | FR-021 | `XCOM-DU-016` |
| `T26-TS-015` | T026-SR-017 | `XCOM-SW-STIM-007` | FR-007, FR-014 | `XCOM-DU-016` |
| `T26-TS-016` | T026-SR-017 | `XCOM-SW-STIM-007` | FR-014 | `XCOM-DU-016` |
| `T26-TS-017` | T026-SR-011, T026-SR-013 | `XCOM-SW-STIM-007` | FR-007, FR-021 | `XCOM-DU-016` |
| `T26-TS-018` | T026-SR-004, T026-SR-010, T026-SR-013 | `XCOM-SW-STIM-007` | FR-007, FR-021 | `XCOM-DU-016` |

## 24. Bounds and open items

- `XCOM-SW-STIM-003` is **partial**: only the journal/restart half is proven by `T26-TS-011`; the routed
  classification and observation propagation are `XCOM-DU-018`/T028 and their end-to-end matrix is T029
  (`T026-GAP-01`).
- Crash consistency on arbitrary filesystems, media failure, power-loss atomicity, encryption, and tamper
  resistance are not claimed (`T026-GAP-02`).
- Compaction, pruning, rotation, archival, and export are not implemented (`T026-GAP-03`).
- Multi-writer and multi-process journal sharing are not supported (`T026-GAP-05`).
- Strict declaration-level Doxygen execution remains `DOX-GAP-01` (T011/T037); T026 supplies the
  declarations only.

## 25. Negative-case mapping (unit view)

| Unit | Realizes negative cases |
| --- | --- |
| `T26-TS-001` | NEG-03, NEG-11 |
| `T26-TS-002` | NEG-19 |
| `T26-TS-003` | NEG-04, NEG-05 |
| `T26-TS-004` | NEG-25 |
| `T26-TS-005` | NEG-17 |
| `T26-TS-006` | NEG-17, NEG-18 |
| `T26-TS-007` | NEG-21, NEG-22, NEG-32, NEG-33 |
| `T26-TS-008` | NEG-09, NEG-10, NEG-32 |
| `T26-TS-009` | NEG-20, NEG-33 |
| `T26-TS-010` | NEG-15, NEG-16 |
| `T26-TS-011` | NEG-23, NEG-24 |
| `T26-TS-012` | NEG-06, NEG-07 |
| `T26-TS-013` | NEG-12, NEG-13, NEG-14 |
| `T26-TS-014` | NEG-08 |
| `T26-TS-015` | NEG-26 |
| `T26-TS-016` | NEG-26 |
| `T26-TS-017` | NEG-30 |
| `T26-TS-018` | NEG-31 |
| Production unit (`T26-U-JOURNAL`) | NEG-01, NEG-02, NEG-27, NEG-28, NEG-29 (source-inspection cases) |
