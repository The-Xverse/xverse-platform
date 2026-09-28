# T026 Architecture — Bounded Durable Stimulation Intent/Outcome Journal

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T026 (capability 007, slice `T-STIM`) |
| Stage / role | plan → architecture |
| Revision | 1 (durable stimulation journal) |
| Baseline revision | `1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d` |
| Affected source paths | `src/xverse/xcom/include/xverse/xcom/stimulation_journal.hpp` (new), `src/xverse/xcom/src/stimulation_journal.cpp` (new), `src/xverse/xcom/CMakeLists.txt` (edit), `tests/xcom/stimulation_journal/**` (new) |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-009` validation stimulation session, `XCOM-XLC-006` in-process contract, `XCOM-INV-05` finite queues/quota, `XCOM-INV-07` plan-digest binding); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-016` durable stimulation intent/outcome journal); `docs/engineering/xcom/t009/architecture.md`; `specs/007-xcom-core/data-model.md`; `specs/007-xcom-core/contracts/validation-tool.md`; ADR-0016, ADR-0018, ADR-0019, ADR-0020 |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T026 is the **durable-evidence layer** of the stimulation boundary. It records, before emission, a
payload-free intent for one stimulation action and, after emission, an explicit outcome; it bounds the
retained records, frames each record so a torn write is detectable, and surfaces every intent that lost
its outcome as an explicit `EvidenceIncomplete` orphan across a restart. It is the last dependency before
the pre-emission guard (T027) and the action paths (T028).

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013 core types (read-only)
   → T025 time authority + permit + session lifecycle (accepted, read-only)
   → T026 durable stimulation intent/outcome journal (this document)
   → T027 fail-closed pre-emission guard → T028 guarded action paths + service-emulation lease
   → T029 full stimulation matrix → T030–T034 gateway/conformance → T035–T041 evidence/review/acceptance
```

T026 is an **implementation** slice: the deterministic gate requires at least one changed
`src/xverse/xcom/` path and at least one changed `tests/` path. It adds exactly one production target and
additive tests; it changes no accepted production behavior and no accepted byte of T025.

## 3. Boundary and context

### 3.1 System context

```text
   ┌──────── XDL / io.xverse.xcom Profile + activation plan (read-only, T017–T019) ──────────┐
   │  validation policy: allowed interfaces/actions, quota, plan digest                       │
   └─────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │ consumed indirectly through T025 permit identity
   ┌──────── accepted T025 in-process contract (read-only, src/xverse/xcom) ──────────────────┐
   │  validation_session.hpp : Permit · PermitId · SessionId · PlanDigest · ActionMask ·       │
   │  Timestamp · ClockDomainId · Tag · Result · Diagnostic · canonical_digest                  │
   └─────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │ reused read-only (no write, no redefinition)
   ┌──────────────────────────── T026 journal (this slice, src/xverse/xcom) ──────────────────┐
   │  stimulation_journal.hpp/.cpp                                                             │
   │    record model   StimulationIntent · StimulationOutcome (payload-free, bounded)            │
   │    framing        magic · version · kind · length · payload digest · frame digest           │
   │    ordering       journal-before-emission seam (intent durable → callback → outcome)        │
   │    bounds         max_record_bytes · max_retained_records · max_journal_bytes (fail-closed)  │
   │    storage seam   Storage (host-injected) + local-file storage (production)                  │
   │    recovery       open/scan → index · orphans = EvidenceIncomplete · explicit resolution      │
   └─────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │ called by (T028), guarded by (T027)
                                             ▼
                       T027 pre-emission guard · T028 injection/invocation/emulation
                                             │
                                             ▼
                       T029 full matrix · T035–T040 evidence · T039/T041 review/acceptance
```

T026 introduces no route, item, provider, tap, or tool path: it emits nothing on the normal route and
`FR-021` is satisfied by the journal alone (`emission_count` remains zero, as accepted for T025).

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T26-XB-1` Journal vs session/permit | the journal record and its durable file | the accepted T025 permit/session state machine | T026 consumes T025 identity types read-only and never mutates a session, permit, consumed set, or baseline. |
| `T26-XB-2` Intent vs emission | the durable intent frame | the host emission callback and the normal route | The callback is invoked exactly once, outside the journal mutex, only after the intent frame is durable; a failed intent write invokes it zero times. |
| `T26-XB-3` Outcome vs unknown | the explicit recorded outcome | any inferred, defaulted, or `Ok` outcome | An absent outcome is `EvidenceIncomplete`; recovery never converts an orphan into a delivered outcome. |
| `T26-XB-4` Record vs payload | the bounded identity/metadata frame | payload bytes, value bodies, addresses, secrets | No payload is ever written; the record has a compile-time payload-free contract and the frame is bounded. |
| `T26-XB-5` Retention vs unbounded log | the finite record/byte bounds | an unbounded or silently pruned log | On bound exhaustion the journal fails closed; complete retained records are never dropped or overwritten. |
| `T26-XB-6` Durability vs host storage | the `Storage` seam contract | the filesystem, device, and media | "Durable" is a declared write+sync through the host seam; crash/media/tamper properties are explicitly out of scope. |
| `T26-XB-7` Repository vs environment | committed source, tests, work products | admitted build inputs, host scratch paths | Committed files are public-safe and offline; the journal performs no network, ambient/secret, dynamic-load, subprocess, or legacy access. |
| `T26-XB-8` T026 scope vs later tasks | the journal and its ordering seam | the T027 guard and the T028 action paths | T026 performs no authorization, schema, target, direction, action, quota, loop, ownership, injection, invocation, or emulation behaviour. |

### 3.3 Prohibited elements (must remain absent)

No TCP listener, external network peer, discovery, package manager/registry, ambient or secret
configuration, dynamic plugin loading, process execution, legacy repository/binary access, or
domain-specific primitive. No payload/value logging, decoder, redaction profile, or unrestricted log. No
pre-emission guard, injection, service invocation, service emulation, lease, drain, or routed item. No
tool gateway, Protocol Buffers/gRPC, IPC, or separate-process client. No modification of T025 accepted
source or of any existing test/target/label/command/value. No new admitted dependency. No unbounded
queue/file/thread/retry, no callback under an X-COM lock, no wall-clock verdict in tests. No rewrite or
weakening of an accepted ADR, requirement, contract, schema, register, or REF-002 disposition. These
inherit the T007 global prohibitions, the T011 envelope, the T012 build contract, ADR-0019, ADR-0020, and
the constitution.

## 4. Components

Each component maps to a unit group in `unit-specifications.md`. `T26-*` names are local to this document;
the accepted `XCOM-DU-*`/`XCOM-CMP-*`/`XCOM-XLC-*` identifiers are the authorized units/contracts.

### 4.1 New production components (design unit `XCOM-DU-016`, component `XCOM-CMP-009`)

- **`T26-CMP-MODEL` Record model** (`stimulation_journal.hpp`): `JournalStatus` (closed status
  vocabulary), `StimulationIntent` (bounded payload-free intent value), `StimulationOutcome` (bounded
  explicit outcome value). Reuses `PermitId`, `SessionId`, `PlanDigest`, `ActionMask`, `Timestamp`,
  `ClockDomainId`, `Tag`, and `Result` from `validation_session.hpp` read-only.
- **`T26-CMP-JOURNAL` Journal core** (`stimulation_journal.hpp/.cpp`): `JournalConfig` bounds, the
  append-only framed writer, the bounded in-memory index, the journal-before-emission ordering seam,
  capacity accounting, and the deterministic `JournalStatus` result.
- **`T26-CMP-FRAME` Framing and integrity** (`stimulation_journal.cpp`): the fixed frame header/trailer,
  the canonical payload codec, and digest computation through the accepted `canonical_digest`.
- **`T26-CMP-STORAGE` Storage seam** (`stimulation_journal.hpp/.cpp`): an abstract `Storage` boundary
  (`append`, `sync`, `read_all`, `size`, `truncate`) plus a production local-file implementation. The seam
  is the only I/O boundary and is the deterministic fault-injection point for tests.
- **`T26-CMP-RECOVERY` Recovery scan** (`stimulation_journal.cpp`): full-file scan, complete-frame
  validation, torn-tail discard, bounded index rebuild, orphan (`EvidenceIncomplete`) reporting, and the
  explicit orphan-resolution append.

### 4.2 Consumed components (read-only)

- **`T26-CMP-T025`** (`XCOM-XLC-006`, `XCOM-DU-014`/`-015`) — `Permit`/`PermitId`, `SessionId`,
  `PlanDigest`, `ActionMask`, `Timestamp`, `ClockDomainId`, `Tag`, `Result`, `Diagnostic`,
  `canonical_digest` from `validation_session.hpp`/`.cpp`: consumed read-only and **not modified**.
- **`T26-CMP-CORE`** (`XCOM-CMP-004`, `XCOM-DU-001`…`-005`) — accepted core value/diagnostic types:
  neither implemented nor altered by T026.
- **`T26-CMP-BUILD`** (T012) — the subtree warning-as-error rule, sanitizer selection, and the
  runtime-target/build-contract inventory: extended additively by one target.

### 4.3 Work-product components

- **`T26-WP`** — the T026 repository-owned work-product set (`requirements.md`, `architecture.md`,
  `detailed-design.md`, `unit-specifications.md`, `verification-plan.md`, `implementation.md`,
  `internal-review.json`, and `reports/xcom-queue/t026-package.json`).

## 5. Data flow (ordered)

1. **Open and recover** — the host supplies a `JournalConfig` and either a `Storage` seam or a local file
   path. The journal validates the configuration (fail closed on a zero/inconsistent bound); a durable
   journal that already exceeds a declared retained-record or byte bound fails closed with
   `CapacityExhausted`, presenting no over-bound index and reading no more than the declared byte bound;
   otherwise it scans any existing bytes, discards a torn trailing frame, rebuilds the bounded index, and
   reports the recovery summary with any orphan intents as `EvidenceIncomplete`. A complete frame whose
   recovered target/tool tag violates the bounded `Tag` contract stops the scan as `CorruptRecord`.
2. **Validate an intent** — a request encodes the bounded intent metadata; an over-size frame is
   `RecordTooLarge` and an invalid/over-long/empty tag is `RejectedConfiguration`, both with no append.
3. **Admit under bounds** — the journal checks the retained-record and retained-byte bounds; exhaustion is
   `CapacityExhausted` with no append and no emission.
4. **Persist intent durably** — the intent frame is appended as one write and synced; failure is
   `WriteFailed`/`PartialWrite` with the last complete boundary restored where possible and no emission
   (`EvidenceIncomplete` is reserved for a durable intent whose outcome is missing, step 6). A
   `request_id` already carried by a retained intent is refused before the append (the request identity
   is the durable unique key), so no unresolved duplicate intent exists.
5. **Emit once, outside the lock** — the host emission callback is invoked exactly once, after the durable
   intent, with the journal mutex released; the callback returns a bounded explicit outcome whose `kind`
   is validated against the closed vocabulary before encoding. A throwing callback propagates its own
   exception after the durable intent (that intent becomes an `EvidenceIncomplete` orphan) and is never
   converted to `Ok`; an out-of-vocabulary result is `RejectedConfiguration` with no outcome append.
6. **Persist outcome durably** — the outcome frame is appended and synced; a failure leaves the intent as
   an orphan (`EvidenceIncomplete`) and never reports success.
7. **Resolve an orphan** — after a restart, an intent without an outcome can receive exactly one explicit
   resolution outcome (including `Unknown`) whose `kind` is validated against the closed vocabulary;
   accounting is one-to-one, so a resolution resolves exactly one still-unresolved intent and the journal
   never infers a delivered outcome.
8. **Close and reopen** — on the next open, the scan reproduces the same index and the same orphan set;
   provenance identity from step 2 round-trips exactly.

## 6. Interfaces

T026 exposes one new in-process C++20 contract (`T26-IF-1`) and consumes the accepted `XCOM-XLC-006`
contract read-only.

### 6.1 `T26-IF-1` stimulation journal (new, in-process C++20)

| Element | Contract |
| --- | --- |
| `enum class JournalStatus` | closed, enumerable, deterministically ordered status vocabulary (`Ok`, `RejectedConfiguration`, `RecordTooLarge`, `CapacityExhausted`, `WriteFailed`, `PartialWrite`, `CorruptRecord`, `NotFound`, `AlreadyResolved`, `EvidenceIncomplete`) |
| `struct JournalConfig` | `max_record_bytes`, `max_retained_records`, `max_journal_bytes` (all non-zero; byte capacity ≥ one maximal record) |
| `struct StimulationIntent` | bounded payload-free identity: permit id, session id, plan digest, request/correlation/causation ids, action mask, target tag, tool tag, quota cost, clock domain, scheduled timestamp, immediate flag; `request_id` is the durable unique linking key |
| `struct StimulationOutcome` | request id, closed outcome kind (`Delivered`/`Rejected`/`Expired`/`Cancelled`/`Unknown`, validated on both write paths), bounded diagnostic code, clock domain, observed timestamp |
| `class StimulationJournal` | `open(Storage&, JournalConfig)`, `open_local_file(path, JournalConfig)`, `journal_then_emit(intent, emit, out)`, `resolve(request_id, outcome)`, `snapshot()`, `recover()`; non-copyable, non-movable; nested `Storage` seam and nested `Snapshot`/`RecoveryReport` values |

Ownership/lifetime: `platform-owns-shared`; the journal owns its index and (for `open_local_file`) its file
storage, and is `session-scoped` in practice. Thread-safety: `internally-synchronized` with one per-journal
mutex and a single declared writer; the emission callback is invoked outside the mutex.

### 6.2 Consumed contract (read-only)

| Interface | Contract consumed (unchanged) |
| --- | --- |
| `xverse::xcom::validation::{PermitId, SessionId, PlanDigest, ActionMask, Timestamp, ClockDomainId, Tag, Result, Diagnostic, canonical_digest}` | accepted identity/diagnostic/digest vocabulary, used read-only and never redefined |

## 7. Concurrency and resource bounds

| Aspect | T026 decision |
| --- | --- |
| Writers | one declared writer per journal; the journal serializes appends with one mutex |
| Callbacks | the single emission callback runs outside the mutex; no callback runs under the lock |
| Threads in tests | ≤ 4, and only in the bounded deterministic-concurrency case (independent journals) |
| Records | ≤ `max_retained_records`; tests exercise the declared minimum and maximum bounds; recovery stops at the bound and reports `CapacityExhausted` rather than presenting an over-bound index |
| Record size | ≤ `max_record_bytes`; the encoded frame is bounded by the declaration |
| Journal bytes | ≤ `max_journal_bytes`; fail-closed at exhaustion, and recovery reads no more than the declared byte bound |
| Iterations | finite, declared loop counts; no unbounded loop, retry, or wait |
| Wall-clock | no case depends on wall-clock timing for its verdict |
| File scratch | bounded, test-local, host-derived, git-ignored, bounded in size; never printed in public evidence |
| Production footprint | one new static library and additive tests; no other production behavior changes |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Journal-before-emission ordering | intent is durable before the single callback; zero callbacks on intent failure | T026-SR-005, T026-SR-007; CHK-07, CHK-09 |
| Never-infer-success | an absent outcome is `EvidenceIncomplete`; recovery never relabels an orphan | T026-SR-006, T026-SR-013, T026-SR-014; CHK-08, CHK-14, CHK-15 |
| Payload safety | bounded payload-free records; no payload member; no payload bytes on disk | T026-SR-003; CHK-05, CHK-20 |
| Atomicity | self-checking frames; torn tail discarded; corrupt frame stops the scan | T026-SR-008, T026-SR-009, T026-SR-010; CHK-10, CHK-11, CHK-12 |
| Bounded retention | finite record/byte bounds; fail-closed with byte-preservation of complete records | T026-SR-011, T026-SR-012; CHK-13 |
| Durable provenance | tool/session/request/correlation/causation identity round-trips across restart | T026-SR-015; CHK-16 |
| Determinism | closed status vocabulary; identical bytes and recovery summary across runs | T026-SR-016; CHK-17 |
| Concurrency | single writer; callback outside the lock; bounded threads/iterations | T026-SR-017; CHK-18 |
| Offline safety | standard library plus the injected storage seam; local file only; no network/ambient/secret/legacy | T026-SR-018; CHK-19 |
| Public safety | no secret, private address, real payload, or host path in committed files/evidence | T026-SR-019; CHK-21 |
| Documentation | Doxygen ownership/lifetime/thread-safety/failure on every public declaration | T026-SR-020; CHK-22 |
| Governance | registers re-validated; REF-002 unchanged; STIM-003 partial; checkbox only at implementation | T026-SR-021, T026-SR-022; CHK-23, CHK-24 |

## 9. Consistency and constraints

- **Dependency direction preserved.** T026 consumes the accepted T025 in-process contract and introduces
  no dependency on a later slice, adapter, gateway, or legacy repository.
- **Domain neutrality preserved.** The journal uses only generic stimulation vocabulary (intent, outcome,
  clock domain, quota cost, correlation/causation); no automotive, product, protocol, or configuration
  primitive is introduced.
- **XDL centrality preserved.** T026 neither parses nor authors XDL; it consumes permit/plan identity
  values that the accepted plan already binds.
- **Logical/physical separation preserved.** Records carry logical identity, plan digest, clock domain,
  and bounded tags only; no address, transport, or environment identity enters a record.
- **Ownership preserved.** Only T026 source/test paths, the shared build files, the T026 work products, and
  the T026 checkbox change; T025 accepted bytes are consumed read-only and preserved.
- **Maturity preserved.** The journal stays a bounded prototype; crash/media consistency, compaction,
  distribution, sanitizer/static/Doxygen execution, benchmarks, and acceptance remain with T035–T041.
- **Scope preserved.** T026 emits nothing, authorizes nothing, and injects nothing; the guard (T027) and
  action paths (T028) remain separate, dependency-ordered tasks.

## 10. Traceability

| Architecture element | T026 requirements |
| --- | --- |
| `T26-XB-1`, `T26-CMP-T025` | T026-SR-001, T026-SR-002 |
| `T26-XB-2`, `T26-CMP-JOURNAL` | T026-STK-002, T026-SR-005, T026-SR-006, T026-SR-007, T026-SR-017 |
| `T26-XB-3`, `T26-CMP-RECOVERY` | T026-SR-013, T026-SR-014 |
| `T26-XB-4`, `T26-CMP-MODEL` | T026-SR-003, T026-SR-004 |
| `T26-XB-5` | T026-SR-011, T026-SR-012 |
| `T26-XB-6`, `T26-CMP-STORAGE` | T026-SR-009, T026-SR-018 |
| `T26-XB-7`, `T26-WP` | T026-SR-019, T026-SR-020, T026-SR-022 |
| `T26-XB-8` | T026-SR-021 |
| `T26-CMP-FRAME` | T026-SR-008, T026-SR-010, T026-SR-016 |
| `T26-IF-1` (§6.1) | T026-SR-015, T026-SR-016 |
| `T26-CMP-BUILD` | T026-SR-001, T026-SR-022 |

## 11. Negative cases (architecture view)

Every boundary has a declared fail-closed behaviour and a negative-case owner; the executable cases are
listed in `verification-plan.md` §5.

| Boundary | Injected defect | Negative case |
| --- | --- | --- |
| `T26-XB-1` | T026 mutates accepted T025 state | NEG-01, NEG-02 |
| `T26-XB-2` | emission before durable intent, or emission on a failed intent write | NEG-06, NEG-07, NEG-09 |
| `T26-XB-3` | an orphan or failed outcome is reported as delivered/`Ok` | NEG-08, NEG-10, NEG-20 |
| `T26-XB-4` | a payload/value member or payload bytes reach the journal | NEG-03 |
| `T26-XB-5` | a bound is exceeded or a complete record is dropped/overwritten/truncated | NEG-17, NEG-18 |
| `T26-XB-6` | a short append, `sync` failure, or torn tail is treated as durable | NEG-11, NEG-12, NEG-13, NEG-14, NEG-15, NEG-16 |
| `T26-XB-7` | a new dependency or offline/public-safety violation | NEG-02, NEG-27, NEG-28 |
| `T26-XB-8` | T026 implements T027/T028 or a later task | NEG-29 |
| Record/config/bounds | an over-size frame or invalid tag/config is accepted | NEG-04, NEG-05, NEG-19 |
| Resolution/provenance/determinism | a resolution of an unknown/duplicate id, a lost identity field, or non-deterministic output | NEG-21, NEG-22, NEG-23, NEG-24, NEG-25 |
| Outcome vocabulary/identity | an out-of-vocabulary `OutcomeKind` is durably written, or a repeated `request_id` hides an unresolved orphan | NEG-32, NEG-33 |
| Concurrency | an unbounded wait/thread or a callback under the lock | NEG-26 |
