# T026 Verification Plan — Named Checks, Commands, Negative Cases, and Evidence (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T026 (capability 007, slice `T-STIM`) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 (durable stimulation journal) |
| Baseline revision | `1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope, plus the repository-owned Fabro gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
T026's executable checks are five new GoogleTest executables under `tests/xcom/stimulation_journal/`, the
unchanged existing suites that prove additivity, and the source inspections that prove ordering, payload
safety, bounds, partial-write/disk-full behaviour, restart recovery, determinism, offline behaviour, public
safety, and governance; the governance checks are the deterministic gate and the T007–T010 register
validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 ${XVERSE_FABRIC_ROOT}/automation/xcom_feature_gate.py verify T026 1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d
```

For T026 this gate requires:

- the six work products
  `docs/engineering/xcom/t026/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T026 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- at least one changed path under `src/xverse/xcom/` and at least one changed path under `tests/`
  (satisfied by the new journal unit and its suites);
- `cmake -S . -B build/fabro-t026 -G Ninja -DCMAKE_BUILD_TYPE=Debug`,
  `cmake --build build/fabro-t026 --parallel 4`, a non-empty `ctest --test-dir build/fabro-t026 -N`, and
  `ctest --test-dir build/fabro-t026 --output-on-failure --parallel 4` all exit 0;
- `git diff --check 1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d --` clean.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the admitted offline inputs. As accepted
for T012–T016 and T019–T025, if the gate's plain configure fails closed at the T025 test-toolchain
admission check, the only permitted resolution is the narrow A-1 cache seeding already recorded by those
slices: one configure carrying `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and
`XVERSE_XCOM_T025_TEST_TOOLCHAIN` as explicit, previously admitted cache values seeds the gate's own
git-ignored `build/fabro-t026` cache; the gate's unmodified configure/build/`ctest` sequence then reuses
it. The hash-verified preflight is unchanged, no ambient path or network resolution is added, no admission
check is weakened, and the admitted input **values** are recorded by name only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse 1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only 1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d --
git diff --check 1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d --
git ls-files --others --exclude-standard
ctest --test-dir build/fabro-t026 -N
ctest --test-dir build/fabro-t026 -R "xcom_stimulation_journal" --output-on-failure
ctest --test-dir build/fabro-t026 -R "xcom_core_types|xcom_lifecycle|xcom_provider_loopback|xcom_activation_plan|xcom_validation|xcom_observation|xcom_core_matrix" --output-on-failure
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass with
the shared T007–T010 artifacts unchanged in substance. The existing core, lifecycle, provider,
activation-plan, validation, observation, and core-matrix suites must pass unchanged, proving additivity.
Executed sanitizer/static-analysis/Doxygen/benchmark measures and the delivery bundle remain with
T035–T040; this plan requires the T026 candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T026 entry exists and states the durable intent/outcome journal scope |
| CHK-02 | Changed-path boundary | `git diff --name-only <baseline> --`; `git ls-files --others --exclude-standard` | only the §7.1 paths appear; no T025 source/test byte, no `xdl/`, `proto/`, `src/xverse_xdl/`, `cmake/*.cmake`, or root `CMakeLists.txt` change; no other task's path |
| CHK-03 | Dependency and contract reuse | inspect `stimulation_journal.hpp` includes and the CMake link line | the unit includes only the C++ standard library plus `validation_session.hpp`; no new third-party dependency; no identity/digest/diagnostic type is redefined |
| CHK-04 | Build wiring, discovery, additivity | build; `ctest -N`; run the six T026 executables and the preserved suites | `xverse_xcom_stimulation_journal` is the only new runtime target; the five new executables discover 18 cases; every existing target/test name/label/command and the discovered count of existing tests are preserved |
| CHK-05 | Payload-free records | inspect the record types; run `T26-TS-001`, `T26-TS-011` | the record types expose no payload/value/address/unbounded member by declaration inspection; a non-vacuous compile-time negative assertion fails the build if a payload-accepting constructor or an unbounded record is added (an added payload-bearing member that stays constructible from these argument types and within the size bound is not detectable at compile time and is covered by the declaration inspection) |
| CHK-06 | Configuration, size, and tag matrix | run `T26-TS-002`, `T26-TS-003`, `T26-TS-018` | every row of `detailed-design.md` §6.1 and §6.2 matches; every rejection appends nothing and mutates no byte; a recovered frame with an out-of-contract tag is `CorruptRecord` |
| CHK-07 | Journal-before-emission ordering | run `T26-TS-012`, `T26-TS-001` | the intent frame is durable before the callback runs; the callback count is exactly one on success and exactly zero when the intent append or `sync` fails; a failed intent append/sync returns exactly `WriteFailed`/`PartialWrite` and never `EvidenceIncomplete` |
| CHK-08 | Outcome durability and orphan | run `T26-TS-014` | an outcome append failure returns `EvidenceIncomplete` (never `Ok`); the callback ran exactly once; the reopened journal reports exactly one orphan |
| CHK-09 | Callback contract | run `T26-TS-008` | a null callback is `RejectedConfiguration` with no append; a throwing callback propagates its own exception, leaves a durable orphan that recovery classifies `EvidenceIncomplete`, and never reports `Ok`; a callback-returned out-of-vocabulary `OutcomeKind` is `RejectedConfiguration` with no outcome append and a still-`Ok` reopen |
| CHK-10 | Frame layout and integrity | run `T26-TS-001`; inspect frame bytes | every offset, length, kind, and value in `detailed-design.md` §4 matches; the configuration floor is 155 bytes, the minimal legal intent frame is 157 bytes, the maximal intent frame is 281 bytes, an outcome frame is 66 bytes, and both digests verify |
| CHK-11 | Partial write and sync failure | run `T26-TS-013` | a short append is detected as `PartialWrite`, a `sync` failure as `WriteFailed`, the boundary is restored where possible, and no partial frame is counted or retained |
| CHK-12 | Torn tail and corrupt frame recovery | run `T26-TS-010`, `T26-TS-018` | a torn trailing frame is discarded with its length reported; a corrupt complete frame stops the scan with `CorruptRecord`; a digest-valid frame with an over-long, empty, NUL, or non-printable tag is `CorruptRecord` with no recovered value; every complete preceding record is preserved; no false orphan is produced |
| CHK-13 | Capacity and retention fail-closed | run `T26-TS-005`, `T26-TS-006` | the §6.3 accounting table and `bytes == Σ frame sizes` identity hold; exhaustion returns `CapacityExhausted` with no append and no emission; no complete record is dropped, overwritten, or truncated |
| CHK-14 | Restart recovery and orphan classification | run `T26-TS-009`, `T26-TS-017` | every complete-content row of `detailed-design.md` §6.4 matches; every intent without an outcome is reported as an orphan and classified `EvidenceIncomplete`, never delivered; orphan accounting is one-to-one, so a crafted duplicate identity with one outcome still reports the unresolved intent as an orphan and a resolution resolves exactly one intent; a durable journal over the retained-record or byte bound fails closed with `CapacityExhausted`, presents no over-bound index, and refuses further appends |
| CHK-15 | Explicit resolution semantics | run `T26-TS-007` | an unknown request id is `NotFound`; a repeated resolution is `AlreadyResolved`; an `Unknown` resolution stays `Unknown`; an out-of-vocabulary `OutcomeKind` is `RejectedConfiguration` with no append; a repeated `request_id` intent is `RejectedConfiguration` with no append and no emission; no resolution mutates an unrelated record |
| CHK-16 | Provenance round-trip (`XCOM-SW-STIM-003` journal half) | run `T26-TS-011` | permit id, session id, plan digest, request/correlation/causation id, action mask, target, tool, quota cost, clock domain, scheduled timestamp, and immediate flag all round-trip exactly across a restart |
| CHK-17 | Determinism, status vocabulary, no-mutation | run `T26-TS-004`, `T26-TS-005` | the status vocabulary is closed with stable names/ranks and deterministic precedence; a rejected operation leaves `snapshot()` and the durable bytes identical; repeated bounded runs produce identical frames |
| CHK-18 | Bounds, callback-outside-lock, deterministic concurrency | run `T26-TS-015`, `T26-TS-016`; inspect `detailed-design.md` §8 and the tests | ≤ 4 threads, ≤ 64 bounded journal operations per case (realized maximum 52 in T26-TS-015), ≤ 12 records per journal, ≤ `max_retained_records` records, ≤ `max_record_bytes` frames, no wall-clock verdict; the callback runs with the mutex released; 4 independent journals match the single-threaded golden stream across three runs |
| CHK-19 | Offline, local-only, no new dependency | forbidden-API source scan; successful offline configure/build; inspect the storage seam | no network/socket/resolver/TLS, ambient/secret lookup, dynamic-load, subprocess, or legacy access; the only I/O is the injected storage or the host-supplied local path; no TCP listener; no new admitted dependency |
| CHK-20 | No unrestricted logging or export primitive | forbidden-vocabulary scan of the changed source/tests | no payload/value log, decoder, redaction profile, dashboard, storage-of-payload, query, presentation, export, OpenTelemetry, or adapter primitive appears in the T026 surface |
| CHK-21 | Public safety and path hygiene | scan the changed source, tests, and work products | no credential, private address, real or proprietary payload, environment-specific absolute host path, or sensitive deployment value; scratch paths are test-local and never printed into public evidence |
| CHK-22 | Doxygen declarations | inspect `stimulation_journal.hpp`; run the existing documentation configuration check | every public declaration carries `\brief` plus `\ownership`, `\lifetime`, `\thread_safety`, and `\failure` where applicable; the file block names T026 and `\ingroup xcom_stim`; the admitted configuration is unchanged |
| CHK-23 | Registers, REF-002, and maturity honesty | run the §3 validators; inspect the recorded maturity | validators pass unchanged; `ref002.disposition == unchanged` with an empty `promoted` list; `XCOM-SW-STIM-007` is recorded implemented and `XCOM-SW-STIM-003` partial with the routing/observation half deferred to T028/T029; no requirement is promoted |
| CHK-24 | Deterministic gate, diff hygiene, stage rule | run the §2 gate; `git diff --check <baseline> --`; `git diff --name-only <baseline> -- specs/007-xcom-core` | exit 0 with a `ctest:` count; the diff is whitespace-clean; the only capability-document change is the T026 checkbox line, marked complete **only** at the implementation stage |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behaviour with no
partial value, no mutation of a complete retained record, no emitted normal-route item, and no output
claiming success. NEG-01…NEG-33 are executable or source-inspection cases realized by the named checks and
the case assertions; NEG-29 is the additivity/stage repository probe.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | change a non-T026 path, weaken/rename an existing test, or change a non-additive build element | CHK-02/CHK-04 fail; the candidate exceeds the T026 boundary |
| NEG-02 | add a dependency or redefine a T025 identity/digest/diagnostic type | CHK-03/CHK-19 fail |
| NEG-03 | add a payload-accepting constructor, grow a record past its size bound, add a payload-bearing member, or write payload bytes into a journal frame | CHK-05/CHK-20 fail (the compile-time assertions catch the constructor and size cases; the member-shape case is caught by the CHK-05 declaration inspection) |
| NEG-04 | accept an encoded frame larger than `max_record_bytes` | CHK-06 fails |
| NEG-05 | accept an empty, over-long, or non-printable tag | CHK-06 fails |
| NEG-06 | invoke the emission callback before the intent frame is durable | CHK-07 fails |
| NEG-07 | invoke the emission callback despite a failed intent append/sync | CHK-07 fails (the failure must also report `WriteFailed`/`PartialWrite`, never `EvidenceIncomplete`) |
| NEG-08 | report `Ok` after an outcome append/sync failure | CHK-08 fails |
| NEG-09 | accept a null callback and append an intent | CHK-09 fails |
| NEG-10 | convert a throwing callback into `Ok`/a delivered outcome, or durably append an out-of-vocabulary outcome kind | CHK-09 fails |
| NEG-11 | treat a frame without its declared length or digests as complete | CHK-10 fails |
| NEG-12 | count a short append as a complete record | CHK-11 fails |
| NEG-13 | retain a partially written frame as a record | CHK-11/CHK-12 fail |
| NEG-14 | fail to detect a `sync` failure or fail to restore the boundary | CHK-11 fails |
| NEG-15 | retain a torn trailing frame as a record after recovery | CHK-12 fails |
| NEG-16 | produce a false orphan for a corrupt frame or discard preceding complete records | CHK-12 fails |
| NEG-17 | exceed the retained-record or retained-byte bound without `CapacityExhausted` | CHK-13 fails |
| NEG-18 | drop, overwrite, or truncate a complete record to admit a new one | CHK-13 fails |
| NEG-19 | accept a zero or inconsistent configuration | CHK-06 fails |
| NEG-20 | classify an orphan intent as delivered after a restart | CHK-14 fails |
| NEG-21 | accept a resolution for an unknown request id | CHK-15 fails |
| NEG-22 | accept a duplicate resolution or relabel `Unknown` as `Delivered` | CHK-15 fails |
| NEG-23 | lose or mutate a provenance identity field across a restart | CHK-16 fails |
| NEG-24 | default an absent correlation/causation identity | CHK-16 fails |
| NEG-25 | produce a non-deterministic status/name/rank or different bytes across runs | CHK-17 fails |
| NEG-26 | use an unbounded thread/iteration/wait or invoke a callback under the journal mutex | CHK-18 fails |
| NEG-27 | introduce network/socket/TLS/ambient/secret/process/dynamic-load/legacy access, a non-local journal path, or a new dependency | CHK-19 fails |
| NEG-28 | introduce an absolute host path, credential, or sensitive value into a committed file | CHK-21 fails |
| NEG-29 | change a non-T026 path, weaken an accepted requirement/test, implement a later task, promote a REF-002/capability requirement, or mark the T026 checkbox in the plan stage | CHK-02/CHK-23/CHK-24 fail; the candidate exceeds the T026 scope, stage, or maturity boundary |
| NEG-30 | reopen a journal whose durable bytes or complete frames exceed a declared bound and report `Ok`, present an over-bound index, read beyond the byte bound, or accept a further append | CHK-14 fails |
| NEG-31 | retain a recovered intent whose declared tag length exceeds `Tag::max_length`, or whose tag bytes are empty, NUL-containing, or non-printable | CHK-06/CHK-12 fail |
| NEG-32 | accept and durably write an `OutcomeKind` outside the closed `1..5` vocabulary in `journal_then_emit` or `resolve` | CHK-05/CHK-09/CHK-15 fail (the invalid outcome is never appended and a reopen stays `Ok`) |
| NEG-33 | allow a second retained intent with an existing `request_id`, or count a duplicate intent as resolved when only one outcome exists | CHK-07/CHK-14 fail (the second intent is refused with zero emission; one-to-one accounting keeps the unresolved intent an orphan) |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline SHA `1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d`;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting
  command;
- the configure/build/CTest results, including the `ctest -N` discovered counts (T026 adds 18 cases; the
  existing counts are preserved) and the `100% tests passed` line;
- the per-case results for `xcom_stimulation_journal_unit`, `xcom_stimulation_journal_negative`,
  `xcom_stimulation_journal_recovery`, `xcom_stimulation_journal_failure`, and
  `xcom_stimulation_journal_concurrency`, plus the unchanged preserved suites that prove additivity;
- the frame-layout evidence (configuration floor 155; minimal legal intent 157; maximal intent 281;
  outcome 66; matching digests), the capacity accounting table, the recovery scenario table, and the
  provenance round-trip matrix;
- the over-bound recovery evidence: an over-byte-bound and an over-record-bound reopen both report
  `CapacityExhausted` with `retained_records`/`retained_bytes`/`recovered_intents()` within the declared
  bounds and zero further emission; and the out-of-contract recovered-tag evidence (`CorruptRecord` for a
  digest-valid over-long or NUL tag frame with no recovered value and no false orphan);
- the fault-injection evidence: intent append failure → zero callbacks; outcome append failure → one
  orphan; short append and `sync` failure → `PartialWrite`/`WriteFailed` with boundary restoration;
- the throwing-callback evidence: the host exception propagates, the durable intent has no outcome, and
  recovery reports exactly one `EvidenceIncomplete` orphan with no `Ok` success;
- the write-path vocabulary evidence: an out-of-vocabulary `OutcomeKind` passed to `journal_then_emit`
  (callback return) and to `resolve` both return `RejectedConfiguration`, append no outcome, and leave
  the durable journal decodable (reopen `Ok`) rather than exiting as `CorruptRecord`;
- the unique-identity evidence: a repeated `request_id` intent is refused with zero emission and no
  append, and a crafted duplicate identity with one outcome reports the unresolved intent as an orphan
  (one-to-one accounting) with a single resolution resolving exactly one intent;
- the bounded deterministic-concurrency evidence: 4 independent journals × ≤ 16 operations × 3 runs
  matching the single-threaded golden stream;
- the negative-case list with each NEG-ID, its realizing check, and its exact observed outcome;
- the changed-path list and the package record `reports/xcom-queue/t026-package.json` with per-file
  SHA-256;
- the register-validator results, the unchanged REF-002 disposition, and the recorded `XCOM-SW-STIM-003`
  partial disposition.

Public evidence omits host-specific, prefix, manifest, test-toolchain, scratch, temporary, and
private-store absolute paths. Missing, stale, mismatched, skipped, or failed evidence cannot support
acceptance.

## 7. Exit criteria

T026 verification is complete when: the deterministic gate passes (CHK-24); every nominal check in §4 has
its expected result; every negative case in §5 fails closed as stated; the journal-before-emission,
atomic/partial-write, capacity/retention, disk-full/I/O, restart-recovery, and evidence-incomplete
behaviours are proven; `XCOM-SW-STIM-007` is implemented and `XCOM-SW-STIM-003` is recorded partial; no
accepted requirement, test, ADR, contract, register, or T025 byte is weakened; the register validators
still pass with REF-002 unchanged and nothing promoted; and a separate DeepSeek internal review records a
passing verdict with no unresolved blocking finding. This does not constitute user acceptance, which
remains T041.

## 8. Requirement-to-check coverage

| Requirement | Primary checks | Supporting checks |
| --- | --- | --- |
| T026-STK-001 | CHK-01, CHK-02, CHK-04 | CHK-24 |
| T026-STK-002 | CHK-07, CHK-08, CHK-12, CHK-14 | CHK-06, CHK-09 |
| T026-STK-003 | CHK-16 | CHK-23 |
| T026-STK-004 | CHK-17, CHK-18, CHK-19 | CHK-21 |
| T026-STK-005 | CHK-02, CHK-04, CHK-23, CHK-24 | NEG-29 |
| T026-SR-001 | CHK-02, CHK-04, CHK-18 | NEG-01 |
| T026-SR-002 | CHK-03, CHK-19 | NEG-02 |
| T026-SR-003 | CHK-05, CHK-20 | NEG-03, NEG-32 |
| T026-SR-004 | CHK-06 | NEG-04, NEG-05, NEG-31 |
| T026-SR-005 | CHK-07 | NEG-06, NEG-07, NEG-33 |
| T026-SR-006 | CHK-08 | NEG-08 |
| T026-SR-007 | CHK-09 | NEG-09, NEG-10, NEG-32 |
| T026-SR-008 | CHK-10 | NEG-11 |
| T026-SR-009 | CHK-11 | NEG-12, NEG-13, NEG-14 |
| T026-SR-010 | CHK-12 | NEG-15, NEG-16 |
| T026-SR-011 | CHK-13 | NEG-17, NEG-18 |
| T026-SR-012 | CHK-06 | NEG-19 |
| T026-SR-013 | CHK-14 | NEG-20, NEG-30, NEG-33 |
| T026-SR-014 | CHK-15 | NEG-21, NEG-22, NEG-32 |
| T026-SR-015 | CHK-16 | NEG-23, NEG-24 |
| T026-SR-016 | CHK-17 | NEG-25 |
| T026-SR-017 | CHK-18 | NEG-26 |
| T026-SR-018 | CHK-19 | NEG-27 |
| T026-SR-019 | CHK-21 | NEG-28 |
| T026-SR-020 | CHK-22 | CHK-24 |
| T026-SR-021 | CHK-23 | NEG-29 |
| T026-SR-022 | CHK-24 | NEG-29 |

No requirement is left without at least one check, and no check claims acceptance.

## 9. T-STIM slice evidence mapping (T007 register)

The T007 ownership register requires eleven evidence names for the whole `T-STIM` slice (T025–T029). T026
completes two and contributes to two, without claiming any name beyond its own exact-candidate evidence.

| Slice evidence | T026 contribution | Owning check/case |
| --- | --- | --- |
| `journal-before-emission` | intent durable before exactly one callback, zero callbacks on intent failure | CHK-07; `T26-TS-001`, `T26-TS-012` |
| `journal-failure-recovery` | partial-write/disk-full/sync failure, worst-case boundary restoration, restart recovery, orphan classification, over-bound recovery fail-closed, out-of-contract recovered-tag rejection, capacity accounting | CHK-11, CHK-12, CHK-13, CHK-14; `T26-TS-005`…`T26-TS-010`, `T26-TS-013`, `T26-TS-014`, `T26-TS-017`, `T26-TS-018` |
| `synthetic-provenance` | journal-persistence/restart half only; routed classification and observation propagation remain T028/T029 | CHK-16; `T26-TS-011` (partial) |
| `deterministic-concurrency` | bounded deterministic independent-journal concurrency and callback-outside-lock | CHK-18; `T26-TS-015`, `T26-TS-016` (partial) |
| `permit-action-mismatch-matrix`, `zero-emission-after-rejection`, `quotas`, `unmapped-clocks`, `loop-bounds`, `lease-conflicts`, `drain-terminal` | none; remain T027–T029 | — |

No evidence name above is claimed beyond what its own exact-candidate evidence shows; `synthetic-provenance`
is explicitly partial for T026 and is not reported as complete.
