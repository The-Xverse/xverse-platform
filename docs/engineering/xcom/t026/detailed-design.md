# T026 Detailed Design — Frame Layout, Ordering Seam, Bounds, Recovery, Failure Semantics, and Tests

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T026 (capability 007, slice `T-STIM`) |
| Stage / role | plan → detailed design (pre-code) |
| Revision | 1 (durable stimulation journal) |
| Baseline revision | `1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Accepted design unit | `XCOM-DU-016` durable stimulation intent/outcome journal (component `XCOM-CMP-009`, contract `XCOM-XLC-006`) |
| Classification | Public-safe engineering work product |

This design is written **before** implementation. Every constant, offset, bound, and expected value below
is a verification contract: the implementation must realize it, and weakening an expected value requires a
reviewed successor candidate.

## 2. Design principles

1. **Intent is durable before emission; a failure never emits.** The ordering seam writes and syncs the
   intent frame, then invokes the host callback exactly once outside the journal mutex, then writes and
   syncs the outcome frame. A failed intent write invokes the callback zero times.
2. **Unknown is never success.** An intent without a durable outcome is `EvidenceIncomplete`; recovery
   surfaces it as an orphan and requires an explicit resolution.
3. **No payload ever reaches the journal.** Records are bounded identity/metadata with a compile-time
   payload-free contract; the framing layer has no payload-bearing member.
4. **Every record is self-checking and bounded.** One frame per record with a declared length and two
   digests; the frame and the file are bounded by the host-declared configuration.
5. **Fail closed, preserve evidence.** On a bound, write, sync, or framing failure the journal fails
   closed and preserves every complete preceding record byte-for-byte.
6. **Deterministic and inspectable.** A closed status vocabulary, a canonical byte codec, a stable
   precedence, and a recovery summary that is reproducible across runs and builds.
7. **Additive and read-only on the predecessor.** T025 accepted source is consumed read-only and never
   modified; the journal is a new unit.

## 3. Types and canonical vocabulary

Namespace: `xverse::xcom::validation` (the accepted `XCOM-XLC-006` family), following T025. The unit
reuses `PermitId` (16 B), `SessionId` (16 B), `PlanDigest` (32 B), `ActionMask` (u32), `Timestamp`
(i64), `ClockDomainId` (u32), `Tag`, `Result`, and `canonical_digest` from `validation_session.hpp`
read-only. No identity, digest, or diagnostic type is redefined.

### 3.1 `JournalStatus`

Closed, enumerable, deterministically ordered; declaration order is precedence order, most severe first.

| Rank | Enumerator | Meaning | Retryable by caller |
| ---: | --- | --- | --- |
| 0 | `RejectedConfiguration` | invalid/zero/inconsistent configuration or invalid tag/bound input | after correction |
| 1 | `RecordTooLarge` | encoded frame exceeds `max_record_bytes` | after reducing fields |
| 2 | `CorruptRecord` | a complete frame failed its digest check during scan | no; requires operator action |
| 3 | `PartialWrite` | a short append or a torn trailing frame was detected | after boundary restoration |
| 4 | `WriteFailed` | append/truncate I/O failure or disk full (space failure) | yes |
| 5 | `CapacityExhausted` | retained-record or retained-byte bound reached | after declared retention policy |
| 6 | `AlreadyResolved` | the referenced intent already has an outcome | no |
| 7 | `NotFound` | no intent matches the referenced request id | no |
| 8 | `EvidenceIncomplete` | intent durable but outcome not durable/unknown | via explicit resolution |
| 9 | `Ok` | operation completed and is durable | n/a |

`status_name(JournalStatus)` returns a stable non-empty view; `precedence_rank(JournalStatus)` returns the
rank; `from_first(...)` retains the highest-precedence (lowest-rank) applicable status.

### 3.2 `JournalConfig`

| Field | Type | Rule |
| --- | --- | --- |
| `max_record_bytes` | `std::size_t` | non-zero and ≥ 44 + 111 = 155 (the configuration floor: frame overhead plus the minimum intent payload for empty tags; the minimal *legal* record is 157 bytes) |
| `max_retained_records` | `std::size_t` | non-zero |
| `max_journal_bytes` | `std::size_t` | non-zero and ≥ `max_record_bytes` |

An open with a zero bound, `max_record_bytes < 155`, or `max_journal_bytes < max_record_bytes` is
`RejectedConfiguration` and mutates no file.

### 3.3 `StimulationIntent` (payload-free, bounded)

| Field | Type | Bound |
| --- | --- | --- |
| `permit_id` | `PermitId` | fixed 16 B |
| `session_id` | `SessionId` | fixed 16 B |
| `plan_digest` | `PlanDigest` | fixed 32 B |
| `request_id` | `std::uint64_t` | any |
| `correlation_id` | `std::uint64_t` | any |
| `causation_id` | `std::uint64_t` | any |
| `action_mask` | `ActionMask` | any defined mask; the journal does not authorize it |
| `target` | `Tag` | ≤ 63 printable ASCII bytes |
| `tool` | `Tag` | ≤ 63 printable ASCII bytes |
| `quota_cost` | `std::uint32_t` | any; recorded only |
| `clock_domain` | `ClockDomainId` | any non-`kInvalidClockDomain` for a scheduled intent |
| `scheduled_at` | `Timestamp` | any |
| `immediate` | `bool` | explicit immediate/scheduled label |

The struct has no payload, value, address, string-blob, or unbounded member by declaration. Compile-time
`static_assert`s reject a payload-accepting constructor and bound `sizeof`; the absence of a
payload-bearing member is established by declaration inspection, and the encode path writes only the
fields above.

### 3.4 `StimulationOutcome` (payload-free, bounded)

| Field | Type | Bound |
| --- | --- | --- |
| `request_id` | `std::uint64_t` | any |
| `kind` | `OutcomeKind` | closed: `Delivered`(1), `Rejected`(2), `Expired`(3), `Cancelled`(4), `Unknown`(5) |
| `reason` | `Result` | accepted T025 bounded code |
| `clock_domain` | `ClockDomainId` | any |
| `observed_at` | `Timestamp` | any |

`Unknown` is a first-class explicit value and is never relabelled `Delivered`. The `kind` is a closed
`1..5` vocabulary: both public write paths (`journal_then_emit`'s callback result and `resolve`) validate
it before encoding, so an out-of-vocabulary byte is never written. `reason` is a `std::uint8_t`-backed
T025 `Result`; its full underlying range is representable and is decode-tolerated (the outcome decoder
casts the byte without narrowing), so no write-path vocabulary check is applied to `reason`.

## 4. Frame layout

All integers little-endian. One frame per record.

| Offset | Size | Field | Value |
| ---: | ---: | --- | --- |
| 0 | 4 | magic | `0x4E524A58` (bytes `X J R N`) |
| 4 | 2 | format version | `1` |
| 6 | 1 | kind | `1` intent, `2` outcome |
| 7 | 1 | flags | bit 0 = immediate; bits 1–7 reserved `0` |
| 8 | 4 | payload length | `N` (declared) |
| 12 | 16 | payload digest | `canonical_digest(payload[0..N))` |
| 28 | N | payload | canonical codec (below) |
| 28+N | 16 | frame digest | `canonical_digest(bytes[0..28+N))` |

`kFrameOverhead = 44` (28 header + 16 trailer). A frame is complete only when all `28 + N + 16` bytes are
present and both digests match.

### 4.1 Intent payload codec (`kind = 1`)

| Order | Field | Bytes |
| ---: | --- | ---: |
| 1 | `permit_id` | 16 |
| 2 | `session_id` | 16 |
| 3 | `plan_digest` | 32 |
| 4 | `request_id` | 8 |
| 5 | `correlation_id` | 8 |
| 6 | `causation_id` | 8 |
| 7 | `action_mask` | 4 |
| 8 | `quota_cost` | 4 |
| 9 | `clock_domain` | 4 |
| 10 | `scheduled_at` | 8 |
| 11 | immediate flag | 1 |
| 12 | `target` length | 1 |
| 13 | `target` bytes | `Lt` |
| 14 | `tool` length | 1 |
| 15 | `tool` bytes | `Lw` |

`N_intent = 111 + Lt + Lw`, `0 ≤ Lt,Lw ≤ 63`. The arithmetic floor is `44 + 111 = 155` bytes (the
configuration minimum `kJournalMinRecordBytes`, which assumes empty tags); because T026-SR-004 rejects
empty tags, the **minimal legal record** is `44 + 111 + 1 + 1 = 157` bytes (one printable byte in each
tag). Maximum = `44 + 111 + 126 = 281` bytes.

### 4.2 Outcome payload codec (`kind = 2`)

| Order | Field | Bytes |
| ---: | --- | ---: |
| 1 | `request_id` | 8 |
| 2 | `kind` | 1 |
| 3 | `reason` | 1 |
| 4 | `clock_domain` | 4 |
| 5 | `observed_at` | 8 |

`N_outcome = 22`; every outcome frame is exactly `44 + 22 = 66` bytes.

## 5. Ordering seam and operation semantics

### 5.1 `journal_then_emit(intent, emit, out)`

1. Validate the intent: invalid/over-long/empty tag → `RejectedConfiguration`; encoded frame
   `> max_record_bytes` → `RecordTooLarge`; `emit` null → `RejectedConfiguration`. No append in any case.
2. Under the mutex: reject a `request_id` already carried by a retained intent
   (`RejectedConfiguration`) — the request identity is the durable unique key, so no unresolved
   duplicate intent can exist; check `records + 1 ≤ max_retained_records` and
   `bytes + frame ≤ max_journal_bytes`; otherwise `CapacityExhausted` — **`emit` is not invoked** for
   either rejection.
3. Under the mutex: append the intent frame and `sync`. On failure, attempt truncate-to-last-good-boundary,
   release, and return `WriteFailed` (or `PartialWrite` for a short append) — **`emit` is not invoked**.
   `EvidenceIncomplete` is not returned here; it is reserved for step 5, where the intent is durable and
   only its outcome is missing.
4. Mark the durable intent as callback-owned independently of the recovered index, release the mutex,
   and invoke `emit` exactly once. While any callback owns an intent, `recover`, `open`, and
   `open_local_file` return `RejectedConfiguration` without scanning, rebinding, or creating a file;
   `resolve` refuses an in-flight intent. Capture the returned `StimulationOutcome`. Validate
   its `kind` against the closed `1..5` vocabulary before encoding: an out-of-vocabulary kind returns
   `RejectedConfiguration` without appending the outcome (the emission callback has already run, so the
   durable intent remains as an orphan) and is never exposed through `out`.
5. Under the mutex: release callback ownership, check the outcome bound, append the outcome frame,
   and `sync`. On failure return
   `EvidenceIncomplete` (the intent remains durable and becomes an orphan); never return `Ok`.
6. Return `Ok` only when both frames are durable.

A callback that throws a host exception propagates unmodified after the durable intent; the intent is an
orphan, and the exception is not converted to `Ok` (the caller observes its own exception; recovery
classifies the durable intent `EvidenceIncomplete` for that request). Callback ownership is also
released on exception or an invalid returned outcome kind, so later recovery and explicit resolution
may process the orphan exactly once.

### 5.2 `resolve(request_id, outcome)`

Validates `outcome.kind` against the closed `1..5` vocabulary before any mutation: an out-of-vocabulary
kind is `RejectedConfiguration` with no append (vocabulary validation precedes the reference check).
Otherwise it appends exactly one explicit outcome for an intent that still has no outcome of its own
and is not owned by an in-flight emission callback. An in-flight intent returns
`RejectedConfiguration` without an append.
`NotFound` when no intent matches; `AlreadyResolved` when every retained intent carrying the identity
already has a distinct outcome (one-to-one resolution); `CapacityExhausted`/`WriteFailed` as above. An
`Unknown` resolution stays `Unknown`.

### 5.3 `open` / `open_local_file` / `recover` / `snapshot`

`open(Storage&, config)` validates the config, then performs one recovery scan and stores the report.
`open_local_file(path, config)` rejects an empty path, opens the file, and then behaves as `open`.
Both reject an active emission callback before rebinding; `open_local_file` creates no file in that
case. `recover()` refuses to scan while a callback owns a durable intent and returns
`RejectedConfiguration`; otherwise it re-runs the scan and returns the report.
`snapshot()` returns the bounded counters without a
scan. Neither `recover` nor `snapshot` mutates durable state.

## 6. Expected-value tables

### 6.1 Configuration acceptance

| Config | Expected |
| --- | --- |
| `{320, 64, 16384}` (design default) | accepted |
| `{0, 64, 16384}`; `{320, 0, 16384}`; `{320, 64, 0}` | `RejectedConfiguration` |
| `{154, 64, 16384}` (< 155) | `RejectedConfiguration` |
| `{320, 64, 319}` (`max_journal_bytes < max_record_bytes`) | `RejectedConfiguration` |
| `{155, 1, 155}` (minimum legal) | accepted |

### 6.2 Record-size and tag acceptance

| Case | Expected |
| --- | --- |
| intent with `target`/`tool` length 63 each, frame = 281 ≤ `max_record_bytes` 320 | accepted |
| intent with a frame > `max_record_bytes` (e.g. `max_record_bytes` 155 with a 1-byte tag) | `RecordTooLarge`, no append |
| `target` empty | `RejectedConfiguration`, no append |
| `target` length 64 (over `Tag::max_length`) | `RejectedConfiguration`, no append |
| `target` containing a NUL or non-printable byte | `RejectedConfiguration`, no append |

### 6.3 Capacity accounting

Let `records` be the number of complete retained frames and `bytes` the durable frame bytes.

| Step | `records` | `bytes` | Status |
| --- | ---: | ---: | --- |
| after one minimal legal intent (44 + 111 + 1 + 1 = 157 B) | 1 | 157 | `Ok` |
| after its outcome (66 B) | 2 | 223 | `Ok` |
| `max_retained_records = 2`, append another intent | 2 | 223 | `CapacityExhausted`; intent bytes unchanged |
| `max_journal_bytes = 222`, the second frame would reach 223 | 1 | 157 | `EvidenceIncomplete` when only the outcome exceeds the bound, or `CapacityExhausted` when a new intent would; the complete intent is preserved |

The arithmetic floor 155 B (`44 + 111`, empty tags) is the configuration minimum, not a legal record:
T026-SR-004 rejects empty tags, so the smallest durable record is 157 B (`implementation.md` §7.3).

The identity `bytes == Σ frame sizes of complete records` holds after every operation and after recovery.
No complete record is ever dropped, overwritten, or truncated to admit a new record.

### 6.4 Recovery scenarios (bytes on disk → report)

| On-disk state | Expected report |
| --- | --- |
| 0 bytes | `intents 0`, `outcomes 0`, `orphans 0`, `discarded_trailing_bytes 0` |
| one complete intent | `intents 1`, `outcomes 0`, `orphans 1`, `discarded_trailing_bytes 0` |
| one intent + its outcome | `intents 1`, `outcomes 1`, `orphans 0` |
| two intents, one outcome, complete | `intents 2`, `outcomes 1`, `orphans 1` |
| one complete intent + a torn trailing frame (truncated mid-frame) | `intents 1`, `orphans 1`, `discarded_trailing_bytes = torn length`, complete intent preserved |
| one complete intent + a frame with a corrupted digest | `CorruptRecord`; the complete intent preserved; scan stops; no false orphan for the corrupt frame |
| one complete intent + outcome + trailing garbage shorter than a header | `intents 1`, `outcomes 1`, `orphans 0`, `discarded_trailing_bytes = garbage length` |

### 6.5 Outcome-kind mapping

| `OutcomeKind` | Value | Never relabelled to |
| --- | ---: | --- |
| `Delivered` | 1 | — |
| `Rejected` | 2 | `Delivered` |
| `Expired` | 3 | `Delivered` |
| `Cancelled` | 4 | `Delivered` |
| `Unknown` | 5 | `Delivered` |

Any other underlying byte is outside the vocabulary: it is rejected by both public write paths
(`RejectedConfiguration`) before encoding and rejected by the decoder (`CorruptRecord`) on scan, so an
out-of-vocabulary kind is never durably written by this unit.

## 7. Failure semantics of the journal

| Condition | Status / outcome |
| --- | --- |
| invalid configuration or invalid/empty/over-long/non-printable tag | `RejectedConfiguration`, no mutation |
| encoded frame exceeds `max_record_bytes` | `RecordTooLarge`, no mutation |
| retained-record or retained-byte bound reached | `CapacityExhausted`, no append, no emission |
| intent append or `sync` failure, disk full, or partial write (before emission) | `WriteFailed`/`PartialWrite`, boundary restored where possible, no emission; **never** `EvidenceIncomplete` |
| outcome append or `sync` failure, disk full, or partial write (after emission) | `EvidenceIncomplete`; the durable intent remains an orphan, never `Ok` |
| intent recorded without a durable outcome | `EvidenceIncomplete`; recovery reports an orphan |
| outcome unknown after a journal write | `EvidenceIncomplete`; never `Ok` |
| complete frame fails its digest on scan | `CorruptRecord`; preceding complete records preserved |
| torn/truncated trailing frame | discarded; `discarded_trailing_bytes` reports its length |
| resolution for an unknown request id | `NotFound` |
| repeated resolution of the same request id | `AlreadyResolved` |
| `request_id` already carried by a retained intent | `RejectedConfiguration`, no append, no emission |
| `kind` outside the closed `1..5` vocabulary in `journal_then_emit` or `resolve` | `RejectedConfiguration`, no outcome append; the durable intent remains an orphan |
| two intents sharing a request identity with one outcome (crafted file) | one-to-one accounting reports the unresolved intent as an orphan; a resolution resolves exactly one |
| throwing host callback | propagates unmodified; the durable intent is an `EvidenceIncomplete` orphan; never `Ok` |

### 7.1 Negative-case mapping

Each failure condition above has a negative case in `verification-plan.md` §5: configuration/tag
`NEG-19`/`NEG-05`, record-size `NEG-04`, capacity `NEG-17`/`NEG-18`, write/sync/partial-write
`NEG-12`/`NEG-13`/`NEG-14`, outcome-unknown `NEG-08`, orphan classification `NEG-20`/`NEG-33`, frame
integrity `NEG-11`, torn tail/corrupt frame `NEG-15`/`NEG-16`, resolution references `NEG-21`/`NEG-22`,
out-of-vocabulary outcome kind `NEG-32`, provenance round-trip `NEG-23`/`NEG-24`, determinism `NEG-25`,
and callback contract `NEG-06`/`NEG-07`/`NEG-09`/`NEG-10`.

## 8. Bounds and resource design

| Resource | Kind | Design value | Declared in |
| --- | --- | --- | --- |
| journal record size | bytes | `max_record_bytes` ≥ 155 (default 320) | `JournalConfig` |
| retained journal records | capacity | `max_retained_records` ≥ 1 (default 64) | `JournalConfig` |
| journal bytes | bytes | `max_journal_bytes` ≥ `max_record_bytes` (default 16384) | `JournalConfig` |
| bounded tags | bytes | `Tag::max_length` = 63 each | `Tag` (T025, read-only) |
| writer count | thread count | 1 declared writer + 1 mutex | documentation |
| test threads | thread count | ≤ 4 (concurrency case only) | tests |
| iterations | depth | ≤ 64 bounded journal operations per case (realized maximum 52 in T26-TS-015) | tests |

The journal allocates only its bounded index (≤ `max_retained_records` entries) and one bounded frame
buffer (≤ `max_record_bytes`). No unbounded allocation, loop, wait, or retry exists on any path.
Recovery reads at most `max_journal_bytes`: it fails closed before reading when the durable size exceeds
the byte bound, and it stops as soon as one more complete frame would exceed the retained-record or
retained-byte bound, reporting `CapacityExhausted` and presenting no over-bound index.

## 9. Storage seam design

`StimulationJournal::Storage` is the only I/O boundary:

| Method | Contract |
| --- | --- |
| `append(std::span<const std::uint8_t>)` | appends at the end; returns `Ok`, `WriteFailed`, or `PartialWrite` (fewer bytes than requested) |
| `sync()` | flushes to durable storage; returns `Ok` or `WriteFailed` |
| `read_all(std::vector<std::uint8_t>&)` | returns every durable byte; returns `Ok` or `WriteFailed` |
| `size()` | returns the current durable byte count |
| `truncate(std::size_t)` | restores the durable end to a known-good offset; returns `Ok` or `WriteFailed` |

Production `open_local_file` uses a local-file implementation (`O_RDWR|O_CREAT|O_APPEND`, `pwrite`-style
append, `fsync` for `sync`, `ftruncate` for boundary restoration). It opens only the host-supplied path,
creates no directory, resolves no network path, reads no environment variable, and never logs payload. The
tests inject an in-memory fault-injectable `Storage` for deterministic failure cases and use a bounded,
test-local scratch directory for the real-file recovery cases.

## 10. Case inventory (planned tests)

All cases are additive GoogleTest cases registered by `gtest_discover_tests` with one `t026-<kind>` label.

### 10.1 `tests/xcom/stimulation_journal/unit_tests.cpp`

- **`T26-TS-001` `test_journal_frame_layout_and_roundtrip`** — build a minimal and a maximal intent and one
  outcome over an in-memory storage; assert the configuration floor `kJournalMinRecordBytes = 155`, the
  realized frame lengths 157/281/66, the magic/version/kind offsets, the two matching digests, and that
  reopening returns the same values. The compile-time rule rejects a payload-accepting constructor and an
  unbounded record; the absence of a payload-bearing member is established by declaration inspection.
  (CHK-04, CHK-05, CHK-10)
- **`T26-TS-002` `test_journal_config_validation_matrix`** — every row of §6.1. (CHK-06)
- **`T26-TS-003` `test_journal_record_size_and_tag_matrix`** — every row of §6.2, asserting no append on
  rejection. (CHK-06)
- **`T26-TS-004` `test_journal_status_determinism_and_no_mutation`** — status names/ranks are stable; a
  rejected operation leaves `snapshot()` byte-identical; three repeated runs produce identical frames.
  (CHK-17)
- **`T26-TS-005` `test_journal_snapshot_and_capacity_accounting`** — the §6.3 accounting table and the
  `bytes == Σ frame sizes` identity. (CHK-13)

### 10.2 `tests/xcom/stimulation_journal/negative_tests.cpp`

- **`T26-TS-006` `test_journal_capacity_bound_matrix`** — record-count and byte-capacity exhaustion at the
  minimum and design bounds, proving `CapacityExhausted`, zero emission, and complete-record preservation.
  (CHK-13)
- **`T26-TS-007` `test_journal_resolution_reference_matrix`** — `NotFound` for an unknown request id,
  `AlreadyResolved` for a repeated resolution, an `Unknown` resolution staying `Unknown`, an
  out-of-vocabulary `OutcomeKind` rejected with `RejectedConfiguration` and no mutation, and a repeated
  `request_id` intent rejected with no append and zero emission. (CHK-15)
- **`T26-TS-008` `test_journal_callback_contract_matrix`** — a null callback is `RejectedConfiguration`
  with no append; a throwing callback propagates its exception and leaves a durable `EvidenceIncomplete`
  orphan that recovery reports (never `Ok`); an out-of-vocabulary callback-returned kind is
  `RejectedConfiguration` with no outcome append and a still-`Ok` reopen. (CHK-09)

### 10.3 `tests/xcom/stimulation_journal/recovery_tests.cpp`

- **`T26-TS-009` `test_journal_restart_recovery_and_orphans`** — every complete-content row of §6.4 over a
  real local file across a close/reopen cycle; orphan intents classified `EvidenceIncomplete`; a crafted
  duplicate identity with one outcome leaves the unresolved intent as an orphan (one-to-one accounting)
  and a resolution resolves exactly one intent. (CHK-14)
- **`T26-TS-010` `test_journal_torn_tail_and_corrupt_frame`** — the torn-tail and corrupted-digest rows of
  §6.4, proving tail discard, `CorruptRecord` stop, and preservation of complete preceding records.
  (CHK-12)
- **`T26-TS-011` `test_journal_provenance_roundtrip_matrix`** — every identity field of §3.3 round-trips
  exactly across a restart; `XCOM-SW-STIM-003` journal half. (CHK-16)
- **`T26-TS-017` `test_journal_over_bound_recovery_fails_closed`** — a durable journal whose bytes exceed
  `max_journal_bytes` (and, separately, whose complete frames exceed `max_retained_records`) opened with
  the tighter bound is not `Ok`: it reports `CapacityExhausted`, presents no over-bound index
  (`retained_records <= max_retained_records`, `retained_bytes <= max_journal_bytes`,
  `recovered_intents().size() <= max_retained_records`), and refuses a further append with zero emission.
  (CHK-14, CHK-11)
- **`T26-TS-018` `test_journal_over_long_recovered_tag_is_corrupt`** — a crafted digest-valid intent frame
  whose declared target length exceeds `Tag::max_length` (and one whose target contains a NUL) stops the
  scan with `CorruptRecord`, yields no recovered intent, and produces no false orphan. (CHK-12, CHK-06)

### 10.4 `tests/xcom/stimulation_journal/failure_tests.cpp`

- **`T26-TS-012` `test_journal_write_failure_no_emission`** — an injected append failure or short append
  on the intent returns exactly `WriteFailed`/`PartialWrite` and the callback counter is exactly zero;
  `EvidenceIncomplete` is **not** returned here (it is reserved for step 5, a durable intent whose outcome
  is missing). (CHK-07)
- **`T26-TS-013` `test_journal_sync_failure_and_partial_write`** — an injected `sync` failure and a short
  append are detected, the boundary is restored where possible, and no partial frame is retained.
  (CHK-11)
- **`T26-TS-014` `test_journal_outcome_write_failure_orphan`** — an injected failure on the outcome append
  returns `EvidenceIncomplete` and the reopened journal reports exactly one orphan. (CHK-08)

### 10.5 `tests/xcom/stimulation_journal/concurrency_tests.cpp`

- **`T26-TS-015` `test_journal_bounded_deterministic_concurrency`** — ≤ 4 independent journals, one thread
  each, ≤ 16 bounded operations each; every journal's byte stream equals the single-threaded golden stream.
  (CHK-18)
- **`T26-TS-016` `test_journal_callback_outside_lock_probe`** — the emission callback observes the journal
  mutex as unlocked (a re-entrant `snapshot()`/append probe succeeds inside the callback). (CHK-18)

## 11. Build wiring design

- Add `xverse_xcom_stimulation_journal` to `XVERSE_XCOM_RUNTIME_TARGETS` in `src/xverse/xcom/CMakeLists.txt`
  (the generated build-contract verifier derives its expectation from the same list).
- Define `add_library(xverse_xcom_stimulation_journal STATIC src/stimulation_journal.cpp)`, alias
  `xverse::xcom_stimulation_journal`, include directory `include/`, and PUBLIC link to
  `xverse::xcom_validation_session`; route it through `xverse_xcom_apply_runtime_rules`.
- Add one `add_executable` per test kind (`unit`, `negative`, `recovery`, `failure`, `concurrency`) with
  `GTest::gtest_main`, `GTest::gmock`, and `Threads::Threads`, using `gtest_discover_tests` with the
  hyphenated label `t026-<kind>` (CMake 3.22 label workaround, as accepted for T020/T024).
- Reuse the admitted `XVERSE_XCOM_T025_TEST_TOOLCHAIN` GTest prefix unchanged; add no dependency and
  introduce no new mandatory input.
- Add no root-`CMakeLists.txt`, `cmake/*.cmake`, XDL, or proto change.

## 12. Doxygen plan

| Element | Required tags |
| --- | --- |
| file block (`stimulation_journal.hpp`) | `\file`, `\brief`, `\ingroup xcom_stim` |
| `JournalStatus`, `JournalConfig`, `StimulationIntent`, `StimulationOutcome`, `StimulationJournal` | `\brief`, plus `\ownership`, `\lifetime`, `\thread_safety`, `\failure` on the type. |
| every public method | `\brief`, `\param`, `\return`/`\retval` where applicable, and `\pre`/`\post` where the contract requires ordering |

The count of documented public elements is recorded at implementation; a delta from the T010 `XCOM-DU-016`
plan is handled by T026-OPEN-01 rather than by silently editing the accepted T010 artifact.

## 13. Traceability

| Design element | T026 requirements | Units |
| --- | --- | --- |
| Frame layout (§4), codecs (§4.1–4.2) | T026-SR-003, T026-SR-008, T026-SR-016 | TS-001, TS-004 |
| Ordering seam (§5.1), callback contract | T026-SR-005, T026-SR-006, T026-SR-007 | TS-007, TS-012, TS-013, TS-014, TS-016 |
| Bounds (§6.1–6.3, §8) | T026-SR-004, T026-SR-011, T026-SR-012 | TS-002, TS-003, TS-005, TS-006 |
| Recovery and provenance (§6.4, §5.2–5.3) | T026-SR-004, T026-SR-010, T026-SR-013, T026-SR-014, T026-SR-015 | TS-009, TS-010, TS-011, TS-017, TS-018 |
| Storage seam (§9) | T026-SR-009, T026-SR-018 | TS-013, TS-014 |
| Build wiring (§11) | T026-SR-001, T026-SR-002 | TS-001…TS-016 (execution) |
| Doxygen (§12) | T026-SR-020 | inspection |

## 14. Traceability to failure semantics (accepted `XCOM-DU-016`)

| Accepted condition | Design realization |
| --- | --- |
| intent recorded without an outcome → `evidence-incomplete` | §5.1 step 5, §6.4, `EvidenceIncomplete`; recovery orphan |
| journal write or fsync failure or disk full → `evidence-incomplete` | §5.1 step 5, §7; an outcome append/sync failure yields `EvidenceIncomplete` with a durable orphan, while an intent append/sync failure yields `WriteFailed`/`PartialWrite` with no emission (not `EvidenceIncomplete`) |
| outcome unknown after a journal write → `evidence-incomplete` | §5.1 step 5, `Unknown` outcome kind and `EvidenceIncomplete` status |
| journal configuration rejected → `rejected` | §6.1, `RejectedConfiguration` |
