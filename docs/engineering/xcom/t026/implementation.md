# T026 Implementation Record — Bounded Durable Stimulation Intent/Outcome Journal

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T026 (capability 007, slice `T-STIM`) |
| Stage / role | implementation → implementation record |
| Revision | 1 (repair revision 4, 2026-09-28 — third internal-review findings closed; §11.3) |
| Authorized baseline | `1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d` |
| Predecessor | T025 accepted bounded time authority, immutable validation permit, and session lifecycle (`docs/engineering/xcom/t025/`) |
| Candidate state | working tree over the authorized baseline (staged for the deterministic gate; candidate revision assigned at the workflow checkpoint) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Internal review | `docs/engineering/xcom/t026/internal-review.json` (separate read-only DeepSeek review, produced by the review stage) |
| Package record | `reports/xcom-queue/t026-package.json` (produced by the deterministic package action) |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC006`, `ACC010`, `ACC011`, `ACC014`, `ACC015`); ADR-0016; ADR-0018; ADR-0019; ADR-0020; `specs/007-xcom-core/tasks.md` T026 |
| Maturity | Prototype-only bounded durable intent/outcome journal implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T026 implements the bounded slice required by the T026 task entry: *"Specify and implement bounded
durable stimulation intent/outcome journaling without unrestricted payload logs, including
journal-before-emission ordering, atomic/partial-write behavior, finite capacity and retention,
disk-full/I/O failure, restart recovery, and evidence-incomplete outcomes."*

The candidate adds one additive C++20 production unit, `xverse_xcom_stimulation_journal`
(`stimulation_journal.hpp`/`.cpp`), and eighteen GoogleTest cases across five additive executables. It
records a payload-free intent durably **before** invoking a host-supplied single-shot emission callback
exactly once and outside the journal mutex, then records an explicit outcome; an intent that loses its
outcome is surfaced as an explicit `EvidenceIncomplete` orphan across a restart and is never converted
into success. It enforces a declared maximum record size, retained-record count, and journal byte size,
failing closed rather than dropping, overwriting, or truncating a complete retained record. Each record
is one self-checking frame; a short append, sync failure, or torn trailing frame fails closed without
discarding a complete preceding record. T026 implements **no** pre-emission guard (T027), injection,
service invocation, or emulation (T028), routed item, provider, endpoint, tap, gateway, Protocol
Buffers/gRPC, payload decoder, payload logging, benchmark, or later task. It emits nothing on a normal
route.

`XCOM-SW-STIM-007` (journal-before-emission intent and outcome) is **implemented** by this task.
`XCOM-SW-STIM-003` (persistent synthetic provenance) remains **partial**: T026 implements and tests only
the durable-persistence and restart-surfacing half; the routed-item classification and observation
propagation remain `XCOM-DU-018`/T028 and their end-to-end matrix is T029 (`T026-GAP-01`).

## 3. Implemented change

| Path | Change | Role |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/stimulation_journal.hpp` | add | Public journal interface: closed `JournalStatus`, `OutcomeKind`, `JournalConfig`, `StimulationIntent`, `StimulationOutcome`, `JournalSnapshot`, `RecoveryReport`, the `StimulationJournal` class with its nested `Storage` seam and `EmissionCallback`, and a compile-time payload-free rule |
| `src/xverse/xcom/src/stimulation_journal.cpp` | add | Canonical little-endian frame codec, capacity accounting, fail-closed partial-write/boundary handling, restart scan and orphan classification, and the production `LocalFileStorage` (host-supplied local path only) |
| `src/xverse/xcom/CMakeLists.txt` | edit | Add `xverse_xcom_stimulation_journal` to `XVERSE_XCOM_RUNTIME_TARGETS`; define the library linked to `xverse::xcom_validation_session`; add five additive test executables with `t026-<kind>` labels and a bounded test-local scratch path |
| `tests/xcom/stimulation_journal/unit_tests.cpp` | add | `T26-TS-001`…`T26-TS-005` |
| `tests/xcom/stimulation_journal/negative_tests.cpp` | add | `T26-TS-006`…`T26-TS-008` |
| `tests/xcom/stimulation_journal/recovery_tests.cpp` | add | `T26-TS-009`…`T26-TS-011` |
| `tests/xcom/stimulation_journal/failure_tests.cpp` | add | `T26-TS-012`…`T26-TS-014` |
| `tests/xcom/stimulation_journal/concurrency_tests.cpp` | add | `T26-TS-015`, `T26-TS-016` |
| `docs/engineering/xcom/t010/unit-design.json` | edit | Flip the three realized `XCOM-DU-016` artifact paths from `planned` to `established` (status projection only; see §7.1) |
| `docs/engineering/xcom/t010/design-units.md` | edit | Deterministic projection regenerated from the model (see §7.1) |
| `docs/engineering/xcom/t026/*.md` | add | Five plan-stage work products plus this implementation record |
| `docs/engineering/xcom/t026/internal-review.json` | add (review stage) | DeepSeek internal review |
| `reports/xcom-queue/t026-package.json` | add (package stage) | Exact-candidate package record |
| `specs/007-xcom-core/tasks.md` | edit | T026 checkbox marked complete (implementation stage only) |

No existing production header, source, target, test, label, command, or expected value is changed. No
`xdl/`, `proto/`, `src/xverse_xdl/`, `cmake/*.cmake`, root `CMakeLists.txt`, `contracts/`, T025
`validation_session.*`, or other task's path is changed. No new admitted dependency is added; the unit
links only the C++ standard library plus the accepted T025 `xverse::xcom_validation_session` contract.

### 3.1 Changed symbols

- **New public types**: `JournalStatus`, `OutcomeKind`, `JournalConfig`, `StimulationIntent`,
  `StimulationOutcome`, `JournalSnapshot`, `RecoveryReport`.
- **New public functions**: `status_name`, `precedence_rank`, `from_first`, `outcome_kind_name`.
- **New public constants**: `kJournalFrameMagic`, `kJournalFormatVersion`, `kJournalFrameOverhead`,
  `kJournalMinIntentPayload`, `kJournalOutcomePayload`, `kJournalMinRecordBytes`, `kJournalMaxRecordBytes`,
  `kJournalKindIntent`, `kJournalKindOutcome`.
- **New public class**: `StimulationJournal` with nested `Storage` and alias `EmissionCallback`; methods
  `open`, `open_local_file`, `recover`, `last_recovery`, `snapshot`, `recovered_intents`,
  `recovered_outcomes`, `journal_then_emit`, `resolve`.
- **No accepted symbol** is renamed, removed, or redefined.

### 3.2 Realized frame contract

| Frame | Legal size | Notes |
| --- | --- | --- |
| intent (tags `Lt`+`Lw`, each 1…63) | `44 + 111 + Lt + Lw` = 157…281 | header 28 B + payload + 16 B trailer |
| outcome | 66 | `44 + 22` |
| configuration floor `kJournalMinRecordBytes` | 155 | `44 + 111`, the arithmetic minimum payload; a legal record needs at least one printable byte in each tag |

Header fields: magic `0x4E524A58` (bytes `X J R N`), format version `1`, kind `1`/`2`, flags (bit 0
immediate), declared payload length, 16-byte payload digest (`canonical_digest`), payload, 16-byte frame
digest (`canonical_digest` over header+payload). All integers are little-endian.

### 3.3 Test units added

| Unit | Case | Suite |
| --- | --- | --- |
| `T26-TS-001` | `test_journal_frame_layout_and_roundtrip` | `unit` |
| `T26-TS-002` | `test_journal_config_validation_matrix` | `unit` |
| `T26-TS-003` | `test_journal_record_size_and_tag_matrix` | `unit` |
| `T26-TS-004` | `test_journal_status_determinism_and_no_mutation` | `unit` |
| `T26-TS-005` | `test_journal_snapshot_and_capacity_accounting` | `unit` |
| `T26-TS-006` | `test_journal_capacity_bound_matrix` | `negative` |
| `T26-TS-007` | `test_journal_resolution_reference_matrix` | `negative` |
| `T26-TS-008` | `test_journal_callback_contract_matrix` | `negative` |
| `T26-TS-009` | `test_journal_restart_recovery_and_orphans` | `recovery` |
| `T26-TS-010` | `test_journal_torn_tail_and_corrupt_frame` | `recovery` |
| `T26-TS-011` | `test_journal_provenance_roundtrip_matrix` | `recovery` |
| `T26-TS-012` | `test_journal_write_failure_no_emission` | `failure` |
| `T26-TS-013` | `test_journal_sync_failure_and_partial_write` | `failure` |
| `T26-TS-014` | `test_journal_outcome_write_failure_orphan` | `failure` |
| `T26-TS-015` | `test_journal_bounded_deterministic_concurrency` | `concurrency` |
| `T26-TS-016` | `test_journal_callback_outside_lock_probe` | `concurrency` |
| `T26-TS-017` | `test_journal_over_bound_recovery_fails_closed` | `recovery` |
| `T26-TS-018` | `test_journal_over_long_recovered_tag_is_corrupt` | `recovery` |

## 4. Deterministic gate and build evidence

```sh
python3 ${XVERSE_FABRIC_ROOT}/automation/xcom_feature_gate.py verify T026 1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d
```

Observed result (implementation stage): `ok`, with the six T026 work products present, the T026
checkbox marked complete, at least one `src/xverse/xcom/` and one `tests/` path changed, the
configure/build/discovery/full-`ctest` sequence exiting 0, and `git diff --check` clean. The gate's
configure reuses the T026 build cache seeded with the previously admitted A-1 `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` values (named by role only; no
ambient path or network resolution was added and no admission check was weakened).

| Item | Value |
| --- | --- |
| Configure (A-1 cache seed) | `cmake -S . -B build/fabro-t026 -G Ninja -DCMAKE_BUILD_TYPE=Debug -D<three admitted A-1 cache values>` (exit 0) |
| Configure (plain, reused by the gate) | `cmake -S . -B build/fabro-t026 -G Ninja -DCMAKE_BUILD_TYPE=Debug` (exit 0) |
| Build | `cmake --build build/fabro-t026 --parallel 4` (exit 0, no warning emitted under `-Werror`) |
| Toolchain | host GNU C++ 11.4.0 (`-std=c++20`) under the T012 `-Wall -Wextra -Wpedantic -Werror` contract |
| Discovery | `ctest --test-dir build/fabro-t026 -N` → `Total Tests: 324` (baseline 306 + 18) |
| Full suite | `ctest --test-dir build/fabro-t026 --output-on-failure --parallel 4` → `100% tests passed, 0 tests failed out of 324` |
| T026 suites | `ctest -R T026Journal` → `100% tests passed, 0 tests failed out of 18` |
| Build contract | `xcom_build_contract` passes with the added runtime target |
| Diff hygiene | `git diff --check 1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d --` → clean |

Additivity: the discovered count is the T026 baseline 306 plus exactly the 18 new T026 cases; every
pre-existing target, test name, label, command, and expected value is preserved, and the T012
build-contract verifier accepts the one-target inventory extension.

### 4.1 Supporting checks

```sh
python3 scripts/validate_xcom_task_ownership.py --verify        # exit 0
python3 scripts/validate_xcom_task_ownership.py --check-human   # exit 0
python3 scripts/validate_xcom_requirements_traceability.py --verify     # exit 0
python3 scripts/validate_xcom_requirements_traceability.py --check-human # exit 0
python3 scripts/validate_xcom_architecture_contracts.py --verify        # exit 0
python3 scripts/validate_xcom_architecture_contracts.py --check-human   # exit 0
python3 scripts/validate_xcom_unit_design.py --verify                   # exit 0
python3 scripts/validate_xcom_unit_design.py --check-human              # exit 0
```

## 5. Source inspections

- **Journal-before-emission ordering (CHK-07, NEG-06, NEG-07)** — `journal_then_emit` appends and syncs
  the intent frame under the mutex, releases the mutex, invokes the callback exactly once, then appends
  and syncs the outcome. Intent append/sync/capacity failure returns before the callback; `T26-TS-012`
  asserts zero emissions on every intent failure and `T26-TS-014` asserts exactly one emission when only
  the outcome fails. A `request_id` already carried by a retained intent is refused before the append
  with zero emission (`T26-TS-007`), so the request identity stays a unique durable key.
- **Throwing callback (CHK-09, NEG-10)** — `journal_then_emit` does not catch the host exception: it
  propagates unmodified after the durable intent, which has no outcome and is surfaced by recovery as an
  explicit `EvidenceIncomplete` orphan; the call never reports `Ok`. `T26-TS-008` pins the propagation,
  the single durable orphan, and the recovery report.
- **Payload-free records (CHK-05, CHK-20, NEG-03)** — the header exposes no payload/value/address/
  free-form member by declaration; `static_assert`s reject constructibility from a byte container or text
  and bound the record sizes; `T26-TS-001` replicates those assertions as a non-vacuous compile-time
  negative test that fails the build if a payload-accepting constructor or an unbounded record is added.
  The absence of a payload-bearing member is established by the declaration inspection, not claimed by
  the compile-time assertions.
- **Outcome-kind vocabulary (CHK-05, CHK-15, NEG-32)** — `outcome_kind_in_vocabulary` gates both public
  write paths before encoding: `journal_then_emit` validates the callback-returned kind and `resolve`
  validates before any mutation. An out-of-vocabulary kind is `RejectedConfiguration` with no outcome
  append, so the durable journal never contains a record that the scan would later reject as corrupt;
  `T26-TS-008` and `T26-TS-007` prove a reopen stays `Ok`.
- **Restart recovery bounds and recovered-tag validation (CHK-14, CHK-12, NEG-30, NEG-31)** — recovery
  fails closed before reading when the durable size exceeds `max_journal_bytes`, stops when one more
  complete frame would exceed `max_retained_records` or `max_journal_bytes`, reports
  `CapacityExhausted` with no over-bound index, and refuses further appends; `decode_intent_payload`
  rejects any frame whose declared target/tool length exceeds `Tag::max_length` or whose tag bytes are
  empty/NUL/non-printable, stopping the scan with `CorruptRecord`. `T26-TS-017` proves the over-bound
  fail-closed behaviour and `T26-TS-018` proves the out-of-contract recovered-tag rejection.
- **Atomic framing and partial writes (CHK-10, CHK-11, CHK-12, NEG-11…NEG-16)** — a frame is complete
  only when `28 + N + 16` bytes are present and both digests match; a short append or sync failure is
  detected and the last-good boundary is restored, otherwise the journal is marked unusable;
  `T26-TS-013` proves `PartialWrite`/`WriteFailed` with restoration, and `T26-TS-010` proves torn-tail
  discard and `CorruptRecord` stop with complete preceding records preserved.
- **Capacity and retention (CHK-13, NEG-17, NEG-18)** — declared record and byte bounds are checked
  before any append and before any emission; exhaustion is `CapacityExhausted`; no complete retained
  record is dropped, overwritten, or truncated. `T26-TS-005`/`T26-TS-006` prove the accounting and the
  `retained_bytes == Σ frame sizes` identity.
- **Restart recovery and orphans (CHK-14, NEG-20, NEG-33)** — `open`/`recover` scan complete frames,
  rebuild the bounded index, and report orphans classified `EvidenceIncomplete`; `T26-TS-009` covers
  every row of `detailed-design.md` §6.4 over a real local file, including a crafted duplicate identity
  with one outcome, which one-to-one accounting still reports as an orphan.
- **Explicit resolution (CHK-15, NEG-21, NEG-22, NEG-32)** — `resolve` rejects an out-of-vocabulary kind
  with `RejectedConfiguration` and no mutation before the reference check, returns `NotFound` for an
  unknown request identity, and returns `AlreadyResolved` only when every retained intent carrying the
  identity already has a distinct outcome (one-to-one), so a resolution resolves exactly one intent; it
  never relabels an explicit `Unknown` outcome. `T26-TS-007` proves all of these.
- **Durable provenance (CHK-16, NEG-23, NEG-24)** — `T26-TS-011` round-trips permit, session, plan
  digest, request/correlation/causation identity, action mask, target, tool, quota, clock domain,
  scheduled timestamp, and immediate flag across a close/reopen cycle.
- **Determinism and concurrency (CHK-17, CHK-18, NEG-25, NEG-26)** — the status vocabulary is closed with
  stable names/ranks and deterministic precedence; `T26-TS-004` proves three byte-identical repeated
  runs and a no-mutation rejection; `T26-TS-015` proves four independent journals reproduce the
  single-threaded golden stream across three runs; `T26-TS-016` proves the callback runs with the mutex
  released via a re-entrant probe under a bounded five-second wait. Bounds: ≤ 4 threads, ≤ 16 bounded
  operations per journal, no wall-clock verdict.
- **Offline and local-only (CHK-19, NEG-27)** — the unit includes only the C++ standard library plus
  `validation_session.hpp` and the POSIX local-file calls declared by the accepted design; a forbidden-
  API scan of the changed source and tests finds no network/socket/resolver/TLS, ambient/secret,
  dynamic-load, subprocess, or legacy access; the only I/O is the injected `Storage` seam or the
  host-supplied local path.
- **Public safety (CHK-21, NEG-28)** — a scan of the changed files finds no credential, private address,
  real or proprietary payload, environment-specific absolute path, or sensitive value; scratch files are
  test-local, bounded, git-ignored under `build/`, removed after each case, and never printed.
- **Doxygen (CHK-22)** — every public declaration carries `\brief` plus `\ownership`, `\lifetime`,
  `\thread_safety`, and `\failure` where applicable; the file block names T026 and `\ingroup xcom_stim`;
  the admitted documentation configuration is unchanged.

## 6. Requirement-to-change-to-check traceability

| Requirement | Realized by | Check(s) |
| --- | --- | --- |
| T026-SR-001 | new additive unit + one new runtime target + five additive test executables | CHK-02, CHK-04, CHK-18 |
| T026-SR-002 | includes only `<…>` standard headers plus `validation_session.hpp`; links `xverse::xcom_validation_session` | CHK-03, CHK-19 |
| T026-SR-003 | bounded payload-free `StimulationIntent`/`StimulationOutcome` + compile-time constructor/size assertions + declaration-inspection member check + write-path `OutcomeKind` validation | CHK-05, CHK-20, CHK-15 |
| T026-SR-004 | `RecordTooLarge` pre-append; `Tag::is_valid` rejects empty/over-long/non-printable tags; recovery rejects out-of-contract recovered tags with `CorruptRecord` | CHK-06 |
| T026-SR-005 | `journal_then_emit` ordering seam; callback outside the mutex; intent append/sync failure returns `WriteFailed`/`PartialWrite` with zero emission; repeated `request_id` refused before append | CHK-07, CHK-18 |
| T026-SR-006 | outcome append/sync failure returns `EvidenceIncomplete`; recovery reports the orphan | CHK-08, CHK-12 |
| T026-SR-007 | null callback rejected before append; throwing callback propagates and leaves a durable `EvidenceIncomplete` orphan; out-of-vocabulary callback result rejected with no outcome append | CHK-09, CHK-12, CHK-15 |
| T026-SR-008 | self-checking frame with two `canonical_digest`s | CHK-10 |
| T026-SR-009 | short append/sync failure detection + last-good boundary restoration or unusable marking | CHK-11 |
| T026-SR-010 | torn-tail discard; `CorruptRecord` stop; complete records preserved | CHK-12 |
| T026-SR-011 | record/byte bound checks with fail-closed `CapacityExhausted` | CHK-13 |
| T026-SR-012 | `config_is_legal` at open with no file mutation | CHK-06 |
| T026-SR-013 | restart scan + deterministic `RecoveryReport` + one-to-one orphan classification + over-bound fail-closed `CapacityExhausted` with no over-bound index | CHK-14 |
| T026-SR-014 | `resolve` with out-of-vocabulary rejection, one-to-one `NotFound`/`AlreadyResolved`, and `Unknown` semantics | CHK-15 |
| T026-SR-015 | intent identity codec + `recovered_intents` round-trip | CHK-16 |
| T026-SR-016 | closed status vocabulary + deterministic bytes + no-mutation | CHK-17 |
| T026-SR-017 | one mutex, callback outside it, bounded deterministic concurrency | CHK-18 |
| T026-SR-018 | local-only offline unit; no domain-specific primitive | CHK-19 |
| T026-SR-019 | public-safe source/tests/work products; bounded test-local scratch | CHK-21 |
| T026-SR-020 | Doxygen on every public declaration; `\ingroup xcom_stim` | CHK-22 |
| T026-SR-021 | registers re-validated; `XCOM-SW-STIM-007` implemented, `XCOM-SW-STIM-003` partial; REF-002 unchanged | CHK-23 |
| T026-SR-022 | deterministic gate; clean diff; checkbox marked only in this stage | CHK-24 |

Check and negative-case identifiers are the accepted [`verification-plan.md`](verification-plan.md)
§4–§5.

## 7. Plan-stage reconciliation (recorded, not silently edited)

The pre-code work products are the accepted plan for this task. Three implementation facts required an
honest, recorded reconciliation rather than editing an accepted predecessor or silently departing from
the plan. No requirement or check is weakened.

### 7.1 T010 `XCOM-DU-016` artifact-path status projection

`docs/engineering/xcom/t026/requirements.md` §7.2 listed `docs/engineering/xcom/t010/**` as consumed
read-only. Implementing the unit realizes the three `XCOM-DU-016` paths that the T010 model recorded as
`planned`, and `scripts/validate_xcom_unit_design.py --verify` fails closed with `PATH_INVALID` when a
`planned` path exists (CHK-23 requires the validators to pass). The repository convention, precedented by
commit `c4b8225` ("Repair T007-T020 terminal review findings"), is to flip a realized unit's status
projection from `planned` to `established` and regenerate the deterministic Markdown projection. T026
therefore changed the status field of exactly those three entries in
`docs/engineering/xcom/t010/unit-design.json` and regenerated `docs/engineering/xcom/t010/design-units.md`
from the model; no unit identity, ownership, lifetime, thread-safety, bounds, failure semantics, planned
evidence, or Doxygen obligation is changed. This is a derived status projection update, not a design
rewrite or weakening.

### 7.2 Public surface larger than the T010 `XCOM-DU-016` plan (`T026-OPEN-01`)

The accepted design's §6.1 interface table did not name a read-back accessor, but `T026-SR-015` requires
proving that every identity field round-trips across a restart. T026 therefore added the bounded,
payload-free accessors `recovered_intents()`, `recovered_outcomes()`, and `last_recovery()` (the last
returns the summary of the most recent `open`/`recover` scan). These are value-copy accessors bounded by
`max_retained_records`; they expose no payload, add no new identity vocabulary, and realize `T026-OPEN-01`
rather than editing the accepted T010 artifact.

### 7.3 Minimal legal record size (design arithmetic vs accepted tag rule)

`detailed-design.md` §4.1 originally recorded the arithmetic "minimum intent frame = 155 bytes", which
assumes zero-length tags. `T026-SR-004` requires empty tags to be rejected, so the minimal legal record is
157 bytes (one printable byte in each of `target` and `tool`); 155 remains the configuration floor
(`kJournalMinRecordBytes = 44 + 111`). `T26-TS-001` asserts the constant `155` and the realized 157/281/66
frame sizes and the boundary matrix proves a 157-byte frame is `RecordTooLarge` under `max_record_bytes`
155. The accepted requirement (non-empty printable tags) takes precedence over the design's arithmetic
example, per `requirements.md` §1.2. This repair pass aligned `detailed-design.md` §4.1/§6.3,
`verification-plan.md` CHK-10/§6, and `unit-specifications.md` §22 to distinguish the 155-byte
configuration floor from the 157-byte minimal legal record (finding T026-IR2-05-F04).

## 8. Negative cases realized

| NEG | Realized case | Observed result |
| --- | --- | --- |
| NEG-01 | `git diff --name-only`, `ctest -N` | only T026 paths plus the T010 status projection change; existing targets/tests unchanged |
| NEG-02 | include/link inspection | only the standard library and `validation_session.hpp`; no redefined identity/digest type |
| NEG-03 | `T26-TS-001` compile-time negative test + header `static_assert`s + declaration inspection | no payload member by declaration inspection; a payload-accepting constructor or an unbounded record fails the build |
| NEG-04 | `T26-TS-003` | a 157-byte frame under `max_record_bytes` 155 is `RecordTooLarge` with no append |
| NEG-05 | `T26-TS-003` | empty / 64-byte / NUL tags are `RejectedConfiguration` with no append |
| NEG-06, NEG-07 | `T26-TS-012` | intent append/sync/partial failure emits zero times |
| NEG-08 | `T26-TS-014` | outcome append failure returns `EvidenceIncomplete`, never `Ok` |
| NEG-09 | `T26-TS-008` | a null callback is `RejectedConfiguration` with no append |
| NEG-10 | `T26-TS-008` | a throwing callback propagates and leaves a durable `EvidenceIncomplete` orphan; never converted to success |
| NEG-11 | `T26-TS-001` | a frame is complete only with both digests verified |
| NEG-12, NEG-13 | `T26-TS-012`, `T26-TS-013` | a short append is `PartialWrite` and no partial frame is retained |
| NEG-14 | `T26-TS-013` | sync failure is `WriteFailed`; restoration succeeds or the journal becomes unusable |
| NEG-15 | `T26-TS-009`, `T26-TS-010` | a torn trailing frame is discarded with its length reported |
| NEG-16 | `T26-TS-010` | a corrupt complete frame stops the scan with `CorruptRecord`; no false orphan; preceding records preserved |
| NEG-17, NEG-18 | `T26-TS-006` | record/byte exhaustion is `CapacityExhausted` with zero emission; no complete record lost |
| NEG-19 | `T26-TS-002` | zero/inconsistent configurations are `RejectedConfiguration` with no mutation |
| NEG-20 | `T26-TS-009` | an orphan intent is classified `EvidenceIncomplete`, never delivered |
| NEG-21, NEG-22 | `T26-TS-007` | unknown reference `NotFound`; duplicate resolution `AlreadyResolved`; `Unknown` stays `Unknown`; out-of-vocabulary kind `RejectedConfiguration` with no append |
| NEG-23, NEG-24 | `T26-TS-011` | every provenance field round-trips exactly; nothing is defaulted |
| NEG-25 | `T26-TS-004` | stable names/ranks; three byte-identical repeated runs |
| NEG-26 | `T26-TS-015`, `T26-TS-016` | ≤ 4 threads, ≤ 16 operations, no wall-clock verdict; callback outside the lock |
| NEG-27 | forbidden-API scan + offline build | no forbidden element; no new dependency |
| NEG-28 | public-safety scan | no forbidden content; scratch paths are test-local and never printed |
| NEG-29 | gate + diff + §7 | no non-T026 path beyond the recorded T010 projection; checkbox marked only in this stage; REF-002 unchanged |
| NEG-30 | `T26-TS-017` | an over-byte-bound and an over-record-bound reopen are `CapacityExhausted` with no over-bound index and refuse a further append with zero emission |
| NEG-31 | `T26-TS-018` | a digest-valid 64-byte-tag frame and a NUL-tag frame are `CorruptRecord` with no recovered intent and no false orphan |
| NEG-32 | `T26-TS-007`, `T26-TS-008` | an out-of-vocabulary `OutcomeKind` is `RejectedConfiguration` with no outcome append in both write paths; the journal reopens `Ok` |
| NEG-33 | `T26-TS-007`, `T26-TS-009` | a repeated `request_id` intent is refused with zero emission; a crafted duplicate identity with one outcome keeps the unresolved intent an orphan and one resolution resolves exactly one intent |

## 9. Limitations and gaps

- `T026-LIM-01` — Prototype only: passing the tests proves no runtime, crash-consistency, media-failure,
  power-loss, encryption, tamper-resistance, compatibility, or production-readiness claim; not
  user-accepted (T041) and not externally reviewed.
- `T026-LIM-02` — Durability is a declared write and sync through the host storage seam on the local
  filesystem, not a device-level atomicity guarantee (`T026-GAP-02`).
- `T026-LIM-03` — Retention is a declared finite record/byte bound with fail-closed behaviour; compaction,
  pruning, rotation, archival, and export are not implemented (`T026-GAP-03`).
- `T026-LIM-04` — The journal performs no authorization, schema, target, direction, action, quota, loop,
  or ownership validation (T027) and no emission (T028) (`T026-GAP-04`).
- `T026-LIM-05` — Concurrency is a single declared writer per journal; multi-writer and multi-process
  sharing are unsupported and unclaimed (`T026-GAP-05`).
- `T026-LIM-06` — `XCOM-SW-STIM-003` is **partial**: only the journal/restart half is proven; routed
  classification and observation propagation are `XCOM-DU-018`/T028 and `T26-GAP-01`.
- `T026-LIM-07` — Strict declaration-level Doxygen execution remains `DOX-GAP-01` (T011/T037); T026
  supplies the declarations only.
- `T026-LIM-08` — The FNV-1a `canonical_digest` is local integrity bookkeeping, not a cryptographic
  claim; the frame digests detect truncation and accidental corruption, not a deliberate forgery.

## 10. Definition of done (implementation view)

The implementation stage is complete when the six work products exist, the T026 checkbox is marked, the
deterministic gate and named checks pass at the candidate revision with no existing case weakened,
`XCOM-SW-STIM-007` is implemented and `XCOM-SW-STIM-003` is recorded partial, the register validators pass
with REF-002 unchanged and nothing promoted, this record is written, and a separate DeepSeek internal
review records a passing verdict with no unresolved blocking finding. This is **not** user acceptance,
which remains T041; external Codex review and acceptance are deferred until the
`xcom-t026-t029-20260928` backlog completes.

## 11. Repair records

### 11.1 Revision 2 — first internal-review findings closed

A separate read-only DeepSeek internal review (`internal-review.json`, `review_revision` 1) recorded five
findings against the first candidate and verdict `fail`. This repair pass closes every finding without
weakening an accepted requirement, check, test, or boundary. No requirement or check was relaxed; the
plan-stage work products were amended only where a correction required it, and each amendment is listed
below.

| Finding | Severity | Closure | Evidence |
| --- | --- | --- | --- |
| `T026-IR2-05-F01` | high | `scan_locked` now fails closed before reading when `storage_->size() > max_journal_bytes`, stops when one more complete frame would exceed `max_retained_records` or `max_journal_bytes`, reports `CapacityExhausted`, presents no over-bound index, and sets a new `over_bound_` state that refuses every later append/resolution with `CapacityExhausted`; the read is bounded by the declared byte bound, not the physical file length | `stimulation_journal.cpp` `scan_locked`/`append_frame_locked`/`journal_then_emit`/`resolve`; `T26-TS-017` (`100%` of the 18 T026 cases pass); gate `ctest:324` |
| `T026-IR2-05-F02` | medium | `T026-SR-005` amended so a failed intent append/sync returns `WriteFailed`/`PartialWrite` with no emission, reserving `EvidenceIncomplete` for a durable intent whose outcome is missing; `detailed-design.md` §5.1 step 3 reconciled; `verification-plan.md` CHK-07 now asserts the status, not only the count | `requirements.md` T026-SR-005; `verification-plan.md` CHK-07; `failure_tests.cpp` T26-TS-012 asserts `WriteFailed`/`PartialWrite` with zero emissions |
| `T026-IR2-05-F03` | medium | `decode_intent_payload` rejects any frame whose declared target/tool length exceeds `Tag::max_length`, or whose tag bytes are empty/NUL/non-printable, stopping the scan with `CorruptRecord` and yielding no recovered value | `stimulation_journal.cpp` `tag_bytes_valid`/`decode_intent_payload`; `T26-TS-018` crafted 64-byte-tag and NUL-tag digest-valid frames both `CorruptRecord` with no orphan |
| `T026-IR2-05-F04` | low | `detailed-design.md` §4.1/§6.3, `verification-plan.md` CHK-10/§6, and `unit-specifications.md` §22 now distinguish the 155-byte configuration floor from the 157-byte minimal legal record; no test expectation changed | doc-consistency scan; `T26-TS-001` still realizes 157/281/66 and the constant 155 |
| `T026-IR2-05-F05` | low | the vacuous runtime payload-marker scan in `T26-TS-001` was replaced by a non-vacuous compile-time negative test; the header `static_assert`s remain. (The revision-2 wording that this fails the build for a payload-bearing member was itself overstated and is corrected in §11.2 / `T026-IR2-06-F05`.) | `unit_tests.cpp` T26-TS-001 `static_assert` set; `verification-plan.md` CHK-05/NEG-03; `unit-specifications.md` §25 |

New named checks/negative cases added by the repair: `T26-TS-017`, `T26-TS-018`, `NEG-30`, `NEG-31`
(see `verification-plan.md` §4–§5). The candidate remains additive and within the T026 boundary: no T025
byte, later-task path, dependency, or register is changed, and no maturity is promoted.

Repair verification: `ctest --test-dir build/fabro-t026 -R T026Journal` → `100% tests passed, 0 tests
failed out of 18`; `ctest --test-dir build/fabro-t026 -N` → `Total Tests: 324`. The full suite and the
deterministic Fabro gate are re-run at the repaired candidate revision, and a fresh separate read-only
DeepSeek review is required before acceptance; this record does not itself claim a passing re-review.

### 11.2 Revision 3 — second internal-review findings closed

A second separate read-only DeepSeek internal review (`internal-review.json`, `review_revision` 2) recorded
five findings (`T026-IR2-06-F01`…`F05`) against the revision-2 candidate and verdict `fail`. This repair
pass closes every finding without weakening an accepted requirement, check, test, or boundary. No
requirement or check was relaxed; the plan-stage work products were amended only where a correction
required it, and each amendment is listed below. No new test case was added, so the discovered count stays
18 T026 cases / 324 total.

| Finding | Severity | Closure | Evidence |
| --- | --- | --- | --- |
| `T026-IR2-06-F01` | medium | The throwing-callback contract was reconciled as `T026-SR-005` was: `T026-SR-007` and the `journal_then_emit` header contract now state that the host exception propagates unmodified after the durable intent, the intent is an explicit `EvidenceIncomplete` orphan, and the call never reports `Ok`; `detailed-design.md` §5.1 and `architecture.md` §5 step 5 match. No code change was needed (propagation was already correct); the contradiction was documentary and is removed | `requirements.md` T026-SR-007; `stimulation_journal.hpp` `journal_then_emit` `\note`; `verification-plan.md` CHK-09/NEG-10; `negative_tests.cpp` T26-TS-008 pins the propagation, the single durable orphan, and the recovery report |
| `T026-IR2-06-F02` | medium | `outcome_kind_in_vocabulary` now gates both public write paths before encoding: `journal_then_emit` validates the callback-returned kind (no outcome append; the durable intent stays an orphan) and `resolve` validates before any mutation. An out-of-vocabulary kind is `RejectedConfiguration`, never durably written, so a reopen is `Ok` and never `CorruptRecord`. `reason` (`Result`) is documented as full-range representable and decode-tolerated | `stimulation_journal.cpp` `outcome_kind_in_vocabulary`/`journal_then_emit`/`resolve`/`decode_outcome_payload`; `requirements.md` T026-SR-003/T026-SR-007/T026-SR-014; `negative_tests.cpp` T26-TS-007/T26-TS-008; `NEG-32` |
| `T026-IR2-06-F03` | medium | The request identity is now a unique durable key: `journal_then_emit` refuses a `request_id` already carried by a retained intent (`RejectedConfiguration`, no append, no emission), and orphan accounting/resolution is one-to-one, so a crafted duplicate identity with one outcome still reports the unresolved intent as an orphan and one resolution resolves exactly one intent | `stimulation_journal.cpp` `journal_then_emit`/`orphan_count_locked`/`orphan_ids_locked`/`resolve`; `requirements.md` T026-SR-005/T026-SR-013; `negative_tests.cpp` T26-TS-007; `recovery_tests.cpp` T26-TS-009; `NEG-33` |
| `T026-IR2-06-F04` | low | The `kJournalMinRecordBytes` header comment now calls 155 the configuration floor (the arithmetic minimum payload under empty tags) and names 157 as the minimal legal record; the constant and every test expectation are unchanged | `stimulation_journal.hpp` §constants; doc-consistency with `detailed-design.md` §4.1/§6.3, `verification-plan.md` CHK-10, `implementation.md` §3.2; `T26-TS-001` still realizes 155/157/281/66 |
| `T026-IR2-06-F05` | low | The NEG-03/CHK-05/implementation claim is corrected to the assertion's actual strength: the compile-time `static_assert`s reject a payload-accepting constructor and an unbounded record, while the absence of a payload-bearing member is established by declaration inspection (an added member that stays constructible from these argument types and within the size bound is not detectable without reflection) | `stimulation_journal.hpp` compile-time-rule comment; `unit_tests.cpp` T26-TS-001 comment; `verification-plan.md` CHK-05/NEG-03; `requirements.md` T026-SR-003; `detailed-design.md` §3.3 |

New negative cases added by this repair: `NEG-32` (out-of-vocabulary `OutcomeKind`), `NEG-33` (repeated
`request_id` / duplicate-identity orphan accounting). New unit obligations were folded into the existing
`T26-TS-007`, `T26-TS-008`, and `T26-TS-009` cases rather than adding cases, so the additive contract and
the discovered counts are unchanged. The candidate remains additive and within the T026 boundary: no
accepted T025 byte, later-task path, dependency, or register is changed, and no maturity is promoted.

Repair verification: `ctest --test-dir build/fabro-t026 -R T026Journal` → `100% tests passed, 0 tests
failed out of 18`; `ctest --test-dir build/fabro-t026 -N` → `Total Tests: 324`; the full suite and the
deterministic Fabro gate are re-run at the repaired candidate revision, and a fresh separate read-only
DeepSeek review is required before acceptance; this record does not itself claim a passing re-review.

### 11.3 Revision 4 — third internal-review findings closed

A third separate read-only DeepSeek internal review (`internal-review.json`, `review_revision` 3) recorded
two low-severity work-product findings (`T026-IR3-F01`, `T026-IR3-F02`) against the revision-3 candidate
and verdict `fail`. Both are documentation/traceability defects only: the production unit, the five test
suites, every accepted requirement, and every unrelated work product are byte-unchanged by this repair, and
no requirement, check, test, or boundary is relaxed. No new test case was added, so the discovered count
stays 18 T026 cases / 324 total.

| Finding | Severity | Closure | Evidence |
| --- | --- | --- | --- |
| `T026-IR3-F01` | low | `detailed-design.md` §10.4 (T26-TS-012) now states that a failed intent append or short append returns exactly `WriteFailed`/`PartialWrite` and never `EvidenceIncomplete`; the §7 failure table now separates the pre-emission intent row (`WriteFailed`/`PartialWrite`, never `EvidenceIncomplete`) from the post-emission outcome row (`EvidenceIncomplete`, durable orphan); the §14 mapping row distinguishes the two. No constant, test expectation, or accepted requirement changed | `detailed-design.md` §5.1 step 3, §7, §10.4, §14; `requirements.md` T026-SR-005; `verification-plan.md` CHK-07/NEG-07; `failure_tests.cpp` T26-TS-012 asserts only `WriteFailed`/`PartialWrite` |
| `T026-IR3-F02` | low | `unit-specifications.md` §4–§21 per-case `Bounds` blocks and the §22 summary now record the realized test configurations and iteration counts (7-row configuration matrix; `max_retained_records` 0/1/2/4/8/16/64; `max_journal_bytes` 0/155/200/319/320/350/2048/4096/8192/16384; the 3 injected failure points in T26-TS-012; the 4 bounded operations per journal in T26-TS-015; ≤ 2 scratch files; ≤ 12 realized records per journal; ≤ 64 bounded journal operations per case). No test or accepted requirement changed | `unit-specifications.md` §4–§22 compared against every `JournalConfig` value in the five test suites |

Repair verification: `ctest --test-dir build/fabro-t026 -R T026Journal` → `100% tests passed, 0 tests
failed out of 18`; `ctest --test-dir build/fabro-t026 -N` → `Total Tests: 324`; the full suite and the
deterministic Fabro gate are re-run at the repaired candidate revision, and a fresh separate read-only
DeepSeek review is required before acceptance; this record does not itself claim a passing re-review.

### 11.4 Revision 5 — residual fourth-internal-review findings closed

A fourth separate read-only DeepSeek internal review (`internal-review.json`, `review_revision` 4) recorded
two low-severity work-product findings (`T026-IR4-F01`, `T026-IR4-F02`) against the revision-4 candidate
and verdict `fail`: the §22 summary carried stale/contradictory realized bounds that the revision-4 repair
had left unreconciled (residual of `T026-IR3-F02`). Both are documentation-only defects; the production
unit, the five test suites, every accepted requirement, and every unrelated work product are byte-unchanged
by this repair, and no requirement, check, test, or boundary is relaxed. No new test case was added, so the
discovered count stays 18 T026 cases / 324 total.

| Finding | Severity | Closure | Evidence |
| --- | --- | --- | --- |
| `T026-IR4-F01` | low | `unit-specifications.md` §22 now states the realized `Records per journal` bound: `≤ 12 realized records (T26-TS-017 writer)`, bounded by the contract `≤ max_retained_records`; the revision-4 `≤ 3` value (copied from the T26-TS-009 per-file bound) is removed. T26-TS-015 realizes 8 complete records per journal (`4 × (157 + 66)` bytes) and the T26-TS-017 writer realizes 12 (six intent+outcome pairs), so the stated bound is not smaller than the realized maximum | `unit-specifications.md` §22; `concurrency_tests.cpp:118-122,144-147`; `recovery_tests.cpp:456-466` |
| `T026-IR4-F02` | low | One metric and one bound are now stated consistently in `unit-specifications.md` §22, `detailed-design.md` §8, and `verification-plan.md` CHK-18: `≤ 64 bounded journal operations per case (realized maximum 52 in T26-TS-015)`. The conflicting revision-4 `≤ 10 per case`/`≤ 64 iterations` wording is removed; T26-TS-015 executes 13 × 4 = 52 bounded `journal_then_emit` operations in one case | `unit-specifications.md` §22; `detailed-design.md` §8; `verification-plan.md` CHK-18; `concurrency_tests.cpp:113-148` |

Repair verification: `ctest --test-dir build/fabro-t026 -R T026Journal` → `100% tests passed, 0 tests
failed out of 18`; `ctest --test-dir build/fabro-t026 -N` → `Total Tests: 324`; the full suite and the
deterministic Fabro gate are re-run at the repaired candidate revision, and a fresh separate read-only
DeepSeek review is required before acceptance; this record does not itself claim a passing re-review.
