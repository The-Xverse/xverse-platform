# T026 Requirements — Bounded Durable Stimulation Intent/Outcome Journal

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T026 (capability 007, slice `T-STIM`) |
| Task title | Specify and implement bounded durable stimulation intent/outcome journaling without unrestricted payload logs, including journal-before-emission ordering, atomic/partial-write behavior, finite capacity and retention, disk-full/I/O failure, restart recovery, and evidence-incomplete outcomes |
| Stage / role | plan → requirements |
| Revision | 1 (durable stimulation journal) |
| Baseline revision | `1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d` |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC006`, `ACC010`, `ACC011`, `ACC014`, `ACC015`); `ADR-0016` (subsystem naming); `ADR-0018` (platform-first); `ADR-0019` (stimulation ownership); `ADR-0020` (repository-owned work products and exact-candidate evidence) |
| Owning slice | `T-STIM` (T007 ownership register) |
| Predecessor | T025 — bounded time authority, immutable validation permit, and bounded session lifecycle; accepted `4b01586b438a8587d231ee8828d896c206c06a96`, implementation `cc9044ab28d0ae9b4df8447072f68b73b3db184a` |
| Producer dependencies | T011 admitted offline build envelope (read-only inputs); T012 subtree CMake/CTest contract and warning-as-error rule; T013 immutable core value/diagnostic types (read-only); T025 `validation_session.hpp`/`.cpp` in-process contract `XCOM-XLC-006`, `Permit`/`PermitId`/`SessionId`/`PlanDigest`/`ActionMask`/`Timestamp`/`ClockDomainId`/`Tag`/`Result`/`Diagnostic`/`canonical_digest` (consumed read-only) |
| Successor tasks | T027 (fail-closed pre-emission guard), T028 (guarded injection/invocation/exclusive service emulation), T029 (full matrix and lifecycle completion), T030–T034 (gateway/conformance), T035–T041 (evidence, review, acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}` (`T-STIM` slice evidence names); `docs/engineering/xcom/t008/requirements-register.{json,md}` (`XCOM-SW-STIM-003`, `XCOM-SW-STIM-007`); `docs/engineering/xcom/t009/architecture-model.{json,md}` (`XCOM-CMP-009`, `XCOM-XLC-006`, `XCOM-INV-05`, `XCOM-INV-07`); `docs/engineering/xcom/t010/unit-design.{json,md}` (`XCOM-DU-016`) |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production
source or test change and does not implement, accept, or integrate the candidate. The T026 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T026 — Specify and implement bounded durable stimulation intent/outcome journaling without
> unrestricted payload logs, including journal-before-emission ordering, atomic/partial-write behavior,
> finite capacity and retention, disk-full/I/O failure, restart recovery, and evidence-incomplete
> outcomes.

### 1.1 Authority statement

This document specifies only the bounded T026 slice. It elaborates two accepted software requirements
from `docs/engineering/xcom/t008/requirements-register.{json,md}`:

- `XCOM-SW-STIM-007` "Journal-before-emission intent and outcome" — "Durably journal stimulation intent
  before emission, followed by an outcome, and keep every incomplete outcome explicit without converting
  it to success." (refines `XCOM-SYS-FR-021`, spec `FR-021`); and
- `XCOM-SW-STIM-003` "Persistent synthetic provenance" — "Classify every injected item visibly as
  synthetic or tool-originated and preserve tool, session, request, correlation, and causal identity
  through routing, observation, and restart." (refines `XCOM-SYS-FR-017`, spec `FR-017`; success criterion
  `SC-006`).

It consumes the accepted design unit `XCOM-DU-016` "Durable stimulation intent and outcome journal"
(component `XCOM-CMP-009` "Validation stimulation session", contract `XCOM-XLC-006`, family `STIM`,
ownership `platform-owns-shared`, lifetime `session-scoped`, thread-safety `internally-synchronized`,
bounds `bytes`/`capacity`, overflow `fail-closed`), the accepted data-model entities
`StimulationRequest`/`StimulationOutcome` and `ValidationSession` terminal state `evidence-incomplete`,
and the accepted validation-tool contract (`specs/007-xcom-core/contracts/validation-tool.md`:
"persist intent before routing an accepted stimulus; emit and observe a bounded outcome").

It completes the T007 `T-STIM` slice evidence names `journal-before-emission` and
`journal-failure-recovery`, and it contributes the journal-persistence half of `synthetic-provenance`
(`deterministic-concurrency`, `drain-terminal`, `lease-conflicts`, `loop-bounds`,
`permit-action-mismatch-matrix`, `quotas`, `unmapped-clocks`, and `zero-emission-after-rejection` remain
with T027–T029).

**Boundary honesty for `XCOM-SW-STIM-003`.** The register attributes `XCOM-SW-STIM-003` to T026, but the
accepted unit design links the routing/observation half of that requirement to `XCOM-DU-018` (T028). T026
therefore implements only the **durable persistence and restart-surfacing** portion of persistent
synthetic provenance; the visible synthetic classification of a routed item and its propagation through
routing and observation remain **partial/allocated to T028**, and their end-to-end tests remain T029.
T026 records `XCOM-SW-STIM-003` as **partial**, never `implemented`.

It does **not** redesign the accepted architecture, change a functional requirement, success criterion,
ADR, schema, XDL profile, or contract; implement the pre-emission action guard (T027), any injection,
service invocation, or service emulation (T028), the tool gateway or Protocol Buffers/gRPC (T030–T034),
the payload decoder or payload logging, observation, benchmarks, or any later task; add an admitted
dependency; weaken an accepted requirement or test; or accept or integrate any candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, data
model, the T007 ownership register, the T008 register, the T009 architecture model, the T010 unit design,
the constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is
reported rather than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T026)

1. **New production journal unit.** Add one additive C++20 unit under `src/xverse/xcom/`:
   - `include/xverse/xcom/stimulation_journal.hpp` — a bounded, payload-free, append-only
     intent/outcome journal with an explicit host storage seam; and
   - `src/stimulation_journal.cpp` — its implementation, including a host-selected local file storage
     used only on the local filesystem.
   The unit is registered as one new runtime target `xverse_xcom_stimulation_journal` in the T012
   runtime-target inventory and routed through the existing warning-as-error rule. It changes no
   existing production header, source, or target.
2. **Journal-before-emission ordering (`FR-021`, `XCOM-SW-STIM-007`).** Provide one bounded API that
   (a) durably records a payload-free intent record, (b) only then invokes a host-supplied single-shot
   emission callback exactly once and **outside** the journal mutex, and (c) durably records the
   explicit outcome. The API returns success only after both records are durable; a failed intent write
   means the callback is never invoked.
3. **Payload-free bounded records (`FR-021`, `FR-027`).** Intent and outcome records **shall** carry only
   bounded identity/metadata (permit, session, plan digest, request/correlation/causation identity,
   action mask, bounded target/tool tags, quota cost, clock domain, timestamps, immediate/scheduled
   flag) and a bounded closed outcome kind plus a bounded diagnostic code. Records **shall** contain no
   signal/message payload bytes, no value body, no free-form text, no address, and no secret.
4. **Atomic framing and partial-write behaviour.** Each record **shall** be one self-checking frame
   (magic, format version, kind, declared payload length, payload digest, and frame digest) written as
   one append. A short/failed append **shall** be detected, the journal **shall** fail closed, and any
   torn trailing frame **shall** be discarded on the next recovery without affecting complete preceding
   records.
5. **Finite capacity and retention.** The journal **shall** enforce a declared maximum record size, a
   declared maximum retained-record count, and a declared maximum journal byte size, and **shall** fail
   closed (`CapacityExhausted`) rather than silently dropping, overwriting, or truncating a complete
   retained intent to make room.
6. **Disk-full / I/O failure semantics.** A write, sync, or space failure **shall** never report success
   and **shall** never be converted into a delivered/known outcome: the intent is either durably
   recorded (then the outcome may be `EvidenceIncomplete`) or not recorded (then no emission occurs).
7. **Restart recovery.** Re-opening an existing journal **shall** scan its complete frames, rebuild the
   bounded in-memory index, preserve complete intent/outcome pairs, and surface every intent that has no
   outcome as an explicit `EvidenceIncomplete` orphan. Recovery **shall** support appending an explicit
   resolution outcome (bounded kinds, including `Unknown`) for an orphan and **shall never** infer a
   successful outcome.
8. **Durable provenance identity.** Every intent record **shall** persist the session, permit, plan
   digest, request, correlation, causation, tool, target, action, quota, and clock-domain identity so
   that identity survives a process restart and is reported by recovery (`XCOM-SW-STIM-003`, journal
   half).
9. **Determinism and diagnostics.** Status codes **shall** be a closed, enumerable, deterministic
   vocabulary with stable precedence; the same input sequence **shall** produce the same frame bytes and
   the same recovery report across runs and builds.
10. **Bounded tests.** Add additive GoogleTest suites under `tests/xcom/stimulation_journal/` covering the
    nominal path, the fail-closed negative matrix, restart recovery with a real local file, fault-injected
    write/sync/disk-full/partial-write failures, and a bounded deterministic-concurrency check. The
    suites reuse the already admitted GTest prefix; no new dependency is admitted.
11. The T026 repository-owned work products and the T026 package record.

### 2.2 Explicit exclusions (must remain absent from the T026 candidate)

No pre-emission authorization/schema/target/direction/action/time/quota/loop/ownership guard (T027); no
signal/message injection, service invocation, or service-emulation lease (T028); no routed item, provider,
endpoint, route, observation tap, or observation record; no tool gateway, Protocol Buffers/gRPC, IPC, TCP
listener, or separate process (T030–T034); no payload or value-body logging, payload decoder, redaction
profile, or unrestricted log; no modification of `validation_session.hpp`/`.cpp` (T025 accepted bytes
preserved); no change to any existing test, target, test name, label, command, or expected value
(additive only); no new admitted dependency; no network, socket, DNS, TLS, ambient/secret, dynamic-load,
or legacy-repository/binary access; no process execution; no non-local, world-writable, or
environment-derived journal path; no benchmark, sanitizer/static/Doxygen *execution*, or delivery bundle
(T035–T040); no rewrite or weakening of an accepted ADR, requirement, contract, schema, register, or test;
no promotion of any REF-002 or capability requirement; no acceptance or integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T026 |
| --- | --- | --- |
| Fail-closed pre-emission guard (schema/target/direction/action/time/quota/loop/ownership) and zero-emission-on-rejection | T027 | allocated; T026 provides only the ordering seam the guard will call |
| Guarded injection/invocation, service-emulation lease, drain/close/revoke/expiry lifecycle completion | T028 | allocated; T026 emits nothing on a normal route |
| Routing/observation propagation of synthetic provenance and end-to-end classification | T028 (`XCOM-DU-018`), T029 | allocated; T026 implements the journal/restart half of `XCOM-SW-STIM-003` only (partial) |
| Full permit/action mismatch, quota, loop, lease, drain, unmapped-clock, zero-emission matrix | T029 | allocated |
| Local tool gateway and versioned Protocol Buffers/gRPC contract | T030–T034 | allocated |
| Executed sanitizer/static-analysis/Doxygen evidence, benchmarks, integration, delivery bundle | T035–T040 | allocated |
| Independent review and user acceptance | T039/T041 | allocated |

## 3. Stakeholder requirements (`T026-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T026-STK-001**: Before any stimulation action path is accepted, the program **shall** have a
  repository-owned, bounded, domain-neutral, durable stimulation intent/outcome journal, physically under
  `src/xverse/xcom/` with tests under `tests/xcom/stimulation_journal/`, that records intent before
  emission and an explicit outcome afterwards, offline under the T011-admitted toolchain and the T012
  warning-as-error contract.
- **T026-STK-002**: The journal **shall** never convert an unknown, unwritten, or partially written
  outcome into success; an intent recorded without a durable outcome **shall** remain explicitly
  `EvidenceIncomplete` across a restart, and no payload or unrestricted content **shall** be logged.
- **T026-STK-003**: The journal **shall** preserve tool, session, request, correlation, and causal
  identity across routing-relevant inputs and a restart so that persistent synthetic provenance is not
  lost; the routed-item classification and observation propagation remain T028/T029.
- **T026-STK-004**: The journal **shall** be offline, local-only, bounded, and deterministic: every
  record, queue, file, thread, byte, and timing input is finite and declared; it performs no network,
  ambient-configuration, secret, dynamic-load, process, or legacy access, and it adds no domain-specific
  primitive and no new admitted dependency.
- **T026-STK-005**: T026 **shall** preserve accepted intent: the delivered change is confined to the T026
  source paths, its tests, the shared build files, the T026 work products, and the capability task ledger,
  and it **shall** neither weaken an accepted requirement or test nor implement another task.

## 4. Software/engineering requirements (`T026-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Verified" means the repository-owned test exists, is deterministic, and passes at the recorded
candidate revision; it is not a production, durability-under-power-loss, or compatibility claim.

### 4.1 Unit, build wiring, and additivity

- **T026-SR-001 [ubiquitous]**: The journal **shall** be a new, additive C++20 unit at
  `src/xverse/xcom/include/xverse/xcom/stimulation_journal.hpp` and
  `src/xverse/xcom/src/stimulation_journal.cpp`, exposed through one new runtime target
  `xverse_xcom_stimulation_journal` added to the T012 `XVERSE_XCOM_RUNTIME_TARGETS` inventory and routed
  through the inherited warning-as-error rule; it **shall** change no existing production header, source,
  or target behavior, and every existing test case, target, label, command, and expected value **shall**
  be preserved unchanged.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-021`, `XCOM-SYS-FR-030`; FR-021, FR-030; ADR-0020;
    T012 subtree build contract.
  - Verification intent: changed-path and discovered-count comparison plus the full suite; CHK-02, CHK-04,
    CHK-18, NEG-01.
- **T026-SR-002 [ubiquitous]**: The journal **shall** depend only on the C++ standard library plus the
  accepted T025 `validation_session.hpp` in-process contract (`XCOM-XLC-006`); it **shall** add no
  admitted dependency, no Protocol Buffers/gRPC, and no new diagnostic, digest, or identity vocabulary
  where an accepted one exists.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-026`; FR-026; `XCOM-XLC-006`; Constitution II, VII.
  - Verification intent: include/dependency inspection and the offline build; CHK-03, CHK-19, NEG-02.

### 4.2 Record content, bounds, and payload safety

- **T026-SR-003 [ubiquitous]**: An intent record **shall** carry exactly the bounded metadata
  {permit id, session id, plan digest, request id, correlation id, causation id, action mask, bounded
  target tag, bounded tool tag, quota cost, clock domain, scheduled timestamp, immediate flag} and an
  outcome record **shall** carry exactly {request id, closed outcome kind, bounded diagnostic code,
  clock domain, observed timestamp}; the header **shall** expose no payload, value, address, free-form
  text, or unbounded member; a compile-time rule **shall** reject construction of either record from a
  payload byte container or free-form text and **shall** bound the record size; and the absence of a
  payload-bearing member **shall** be established by declaration inspection. The closed `OutcomeKind`
  vocabulary **shall** be validated on the public write path: a `journal_then_emit` callback result or
  a `resolve` outcome whose `kind` is outside the vocabulary **shall** be rejected
  (`RejectedConfiguration`) without appending that outcome.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-021`, `XCOM-SYS-FR-027`; FR-021, FR-027; `XCOM-DU-016`.
  - Verification intent: field inspection, a non-vacuous compile-time negative assertion that a
    payload-accepting constructor or an unbounded record fails to compile, and write-path
    vocabulary cases; CHK-05, CHK-20, NEG-03, NEG-32.
- **T026-SR-004 [ubiquitous]**: A record whose encoded frame exceeds the declared maximum record size
  **shall** be rejected (`RecordTooLarge`) with no append, and a bounded target/tool tag that is empty,
  longer than the accepted `Tag` maximum, or non-printable **shall** be rejected (`RejectedConfiguration`)
  with no append. The same bounded-tag contract **shall** hold on recovery: a complete frame whose
  declared target/tool length exceeds `Tag::max_length`, or whose tag bytes are empty, NUL-containing,
  or non-printable, **shall** stop the scan with `CorruptRecord`, **shall** yield no recovered value,
  and **shall** not manufacture a false orphan.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-007`; FR-007; `XCOM-DU-016` bounds.
  - Verification intent: record-size and tag-validity boundary cases plus a crafted digest-valid
    out-of-contract recovery frame; CHK-06, NEG-04, NEG-05, NEG-31.

### 4.3 Journal-before-emission ordering (`XCOM-SW-STIM-007`)

- **T026-SR-005 [event-driven]**: When a host requests one stimulation emission, the journal **shall**
  first durably append and sync the intent frame; only after the append and sync succeed **shall** it
  invoke the host-supplied emission callback exactly once, and the callback **shall** be invoked
  **outside** the journal mutex; a failed intent append or sync **shall** return `WriteFailed` (or
  `PartialWrite` when fewer bytes than requested were appended) without invoking the callback at all.
  `EvidenceIncomplete` is reserved for the case where the intent is durable and only its outcome is
  missing, and **shall not** be returned for a failed intent append or sync. A retained intent's
  `request_id` is its durable unique key: a request whose `request_id` is already carried by a
  retained intent **shall** be rejected (`RejectedConfiguration`) before any append and before any
  emission, so no unresolved duplicate intent can exist.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-021`, `XCOM-SYS-FR-027`; FR-021, FR-027;
    `XCOM-DU-016`; contracts/validation-tool.md "persist intent before routing an accepted stimulus".
  - Verification intent: an ordering probe proving the durable intent precedes the callback and the
    callback count is exactly one on success and zero on intent failure, with the exact
    `WriteFailed`/`PartialWrite` status asserted, plus a repeated-request-identity rejection with
    zero emission; CHK-07, NEG-06, NEG-07, NEG-33.
- **T026-SR-006 [event-driven]**: After the callback returns an explicit outcome, the journal **shall**
  durably append and sync an outcome frame; if the outcome append or sync fails, the API **shall** report
  `EvidenceIncomplete` and **shall** not report success, and a recovery scan **shall** surface the intent
  as an orphan until an explicit resolution outcome is written.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-021`; FR-021; `XCOM-DU-016`.
  - Verification intent: outcome-write-failure and orphan-surfacing cases; CHK-08, CHK-12, NEG-08, NEG-13.
- **T026-SR-007 [unwanted]**: If the emission callback is absent (null) the request **shall** be rejected
  (`RejectedConfiguration`) before any intent is written; if the callback returns an outcome whose
  `kind` is outside the closed `OutcomeKind` vocabulary the invalid outcome **shall not** be appended
  and the call **shall** report `RejectedConfiguration`, leaving the durable intent an explicit
  orphan; and if the callback throws a host exception the journal **shall** contain a durable intent
  with no outcome, the host exception **shall** propagate unmodified, recovery **shall** classify that
  intent `EvidenceIncomplete`, and the call **shall never** report `Ok`.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-021`; FR-021, FR-007.
  - Verification intent: null-callback, out-of-vocabulary-return, and throwing-callback cases;
    CHK-09, NEG-09, NEG-10, NEG-32.

### 4.4 Atomic framing and partial-write behaviour

- **T026-SR-008 [ubiquitous]**: Every record **shall** be written as one frame with a fixed header
  (magic, format version, kind, declared payload length, payload digest), the canonical payload, and a
  trailing frame digest computed with the accepted `canonical_digest`; a frame **shall** be considered
  complete only when its declared length is present and both digests match.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-021`; FR-021; `XCOM-DU-016`.
  - Verification intent: exact frame-layout table and digest-mismatch cases; CHK-10, NEG-11, NEG-12.
- **T026-SR-009 [unwanted]**: If a storage append reports fewer bytes than requested (partial write) or a
  transient write/sync failure, the journal **shall** fail closed: it **shall** attempt to restore the
  last complete frame boundary (truncate to the last known-good offset) and, if it cannot, **shall**
  mark the journal unusable for further appends and report `PartialWrite`/`WriteFailed`; it **shall**
  never count a partial frame as a retained record.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-021`; FR-021; `XCOM-DU-016` failure semantics.
  - Verification intent: fault-injected short append and sync failure with boundary restoration;
    CHK-11, NEG-12, NEG-14.
- **T026-SR-010 [event-driven]**: On recovery, a torn or truncated trailing frame **shall** be discarded
  (and its bytes excluded from the retained view) while every complete preceding frame is preserved
  exactly; a complete frame whose digest does not match **shall** stop the scan with `CorruptRecord`
  without discarding the preceding complete records.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-021`; FR-021; `XCOM-DU-016`.
  - Verification intent: truncated-tail and corrupt-frame recovery cases; CHK-12, NEG-15, NEG-16.

### 4.5 Finite capacity and retention

- **T026-SR-011 [ubiquitous]**: The journal **shall** enforce a declared maximum retained-record count
  and a declared maximum journal byte size; when a new intent would exceed either bound the request
  **shall** be rejected with `CapacityExhausted` **before** any append and **before** any emission, and
  every already-complete retained record **shall** be preserved byte-for-byte.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-007`, `XCOM-SYS-FR-021`; FR-007, FR-021;
    `XCOM-INV-05`; `XCOM-DU-016` overflow `fail-closed`.
  - Verification intent: record-count and byte-capacity boundaries at minimum and maximum with
    zero-emission checks and byte-preservation; CHK-13, NEG-17, NEG-18.
- **T026-SR-012 [ubiquitous]**: A journal configuration with a zero or inconsistent bound (zero maximum
  record size, zero retained-record count, zero byte capacity, or a byte capacity smaller than one
  maximal record) **shall** be rejected (`RejectedConfiguration`) at open with no file mutation.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-007`; FR-007; `XCOM-DU-016` "journal configuration
    rejected".
  - Verification intent: configuration boundary cases; CHK-06, NEG-19.

### 4.6 Restart recovery and durable provenance

- **T026-SR-013 [event-driven]**: Opening an existing journal **shall** scan every complete frame,
  rebuild the bounded index, and report a deterministic recovery summary (complete intents, outcomes,
  orphan intents, discarded trailing bytes, retained records, retained bytes); every intent without an
  outcome **shall** be reported as an orphan and classified `EvidenceIncomplete`, never as delivered.
  Orphan accounting **shall** be one-to-one: each durable outcome resolves at most one intent, so an
  intent that shares a request identity with a resolved intent but has no outcome of its own **shall**
  still be reported as an orphan.
  When the durable content already exceeds the declared retained-record or byte bound, the open **shall**
  fail closed (`CapacityExhausted`) **before** reading more than the declared byte bound, **shall**
  present no over-bound index (`retained_records`/`retained_bytes` and `recovered_intents()` remain
  within the declared bounds), and **shall** refuse further appends.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-021`; FR-021; `XCOM-DU-016` "intent recorded without
    an outcome → evidence-incomplete"; `XCOM-INV-05` bounded resources.
  - Verification intent: real-file restart recovery, one-to-one duplicate-identity orphan reporting, and
    over-bound fail-closed cases; CHK-14, NEG-20, NEG-30, NEG-33.
- **T026-SR-014 [event-driven]**: For an orphan intent, the journal **shall** allow appending exactly one
  explicit resolution outcome with a bounded kind (including `Unknown`) that references the original
  request id; a repeated or unknown-resolution request **shall** be rejected without mutation, an
  `OutcomeKind` outside the closed vocabulary **shall** be rejected (`RejectedConfiguration`) without
  appending, and an explicit `Unknown` resolution **shall** never be relabelled delivered.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-021`; FR-021; `XCOM-DU-016`.
  - Verification intent: resolution, out-of-vocabulary, and duplicate/unknown-reference cases;
    CHK-15, NEG-21, NEG-22, NEG-32.
- **T026-SR-015 [ubiquitous]**: Across a close/reopen cycle the recovered intent **shall** preserve
  permit id, session id, plan digest, request id, correlation id, causation id, action mask, target,
  tool, quota cost, clock domain, and scheduled timestamp exactly (`XCOM-SW-STIM-003` journal half).
  - Refines: `XCOM-SW-STIM-003`; anchors `XCOM-SYS-FR-017`, `XCOM-SYS-SC-006`; FR-017, SC-006;
    `XCOM-DU-016`; consumed `XCOM-DU-018` (routing/observation half deferred to T028).
  - Verification intent: restart provenance round-trip matrix; CHK-16, NEG-23, NEG-24.

### 4.7 Determinism, concurrency, and diagnostics

- **T026-SR-016 [ubiquitous]**: The journal status vocabulary **shall** be closed, enumerable, and
  deterministically ordered; the same operation sequence **shall** produce the same primary status, the
  same frame bytes, and the same recovery summary across repeated bounded runs, and a failure **shall**
  leave the retained count, retained bytes, and index unchanged except for a declared boundary
  restoration.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-025`, `XCOM-SYS-FR-021`; FR-021, FR-025;
    `XCOM-DU-016`.
  - Verification intent: repeated-run byte equality and no-mutation checks; CHK-17, NEG-25.
- **T026-SR-017 [ubiquitous]**: The journal **shall** declare single-writer serialization under one
  per-journal mutex, **shall** invoke no host callback while holding that mutex, and the tests **shall**
  use only a bounded, finite thread count and iteration count with no wall-clock verdict; two independent
  journals driven in parallel **shall** each produce the single-threaded golden byte stream.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-014`, `XCOM-SYS-FR-007`; FR-007, FR-014;
    `XCOM-DU-016` `internally-synchronized`/single-writer.
  - Verification intent: callback-outside-lock probe and bounded deterministic-concurrency check;
    CHK-17, CHK-18, NEG-26.

### 4.8 Safety, public safety, and governance

- **T026-SR-018 [ubiquitous]**: The journal **shall** be local-only and offline: it **shall** access only
  a host-provided local file path or an injected storage seam, perform no network/socket/resolver/TLS,
  ambient-configuration, secret, dynamic-load, subprocess, or legacy-repository/binary access, and add no
  domain-specific primitive.
  - Refines: `XCOM-SW-CORE-007` (domain-neutral local runtime half); anchors `XCOM-SYS-FR-026`,
    `XCOM-SYS-FR-028`; FR-026, FR-028; ADR-0019; Constitution II, VII; `XCOM-INV-13`, `XCOM-INV-15`.
  - Verification intent: forbidden-API source scan, no-listener/no-network check, and the offline build;
    CHK-19, NEG-27.
- **T026-SR-019 [ubiquitous]**: Committed source, tests, work products, and evidence **shall** contain no
  credential, private address, unrestricted or real payload, proprietary source excerpt,
  environment-specific absolute host path, or sensitive deployment value; test scratch files **shall**
  be bounded, synthetic, and created under a test-local, host-derived build/scratch path that is never
  printed into public evidence.
  - Refines: Constitution X; anchors `XCOM-SYS-FR-027`; FR-027; public-safe evidence rule.
  - Verification intent: public-safety scan and path-hygiene inspection; CHK-21, NEG-28.
- **T026-SR-020 [ubiquitous]**: Every new public C++ declaration **shall** carry useful Doxygen
  documentation including ownership, lifetime, thread-safety, and failure contract, and the header file
  block **shall** name T026 and `\ingroup xcom_stim`; the admitted repository documentation
  configuration **shall** be unchanged.
  - Refines: `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-029`; FR-029; `XCOM-DU-016` Doxygen obligation;
    Constitution X.
  - Verification intent: declaration inspection and the existing documentation configuration check;
    CHK-22.
- **T026-SR-021 [ubiquitous]**: T026 **shall** reconcile with the T007 ownership register, the T008
  requirement register, the T009 architecture model, and the T010 unit design without rewriting or
  weakening them; **shall** keep the REF-002 disposition `unchanged` with an empty `promoted` list; and
  **shall** record honestly that `XCOM-SW-STIM-007` is implemented by this task, that
  `XCOM-SW-STIM-003` remains **partial** (journal/restart half only, routing/observation deferred to
  T028/T029), and that T027–T041 remain allocated.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-035`, `XCOM-SYS-FR-030`; FR-030, FR-035; Constitution VII, IX.
  - Verification intent: register validators plus the recorded-maturity inspection; CHK-23, NEG-29.
- **T026-SR-022 [ubiquitous]**: The T026 candidate **shall** satisfy the deterministic Fabro gate for an
  implementation task: the six named work products exist, at least one `src/xverse/xcom/` path and at
  least one `tests/` path change, `cmake` configure, build, discovery, and the full `ctest` suite pass,
  and `git diff --check` is clean; the T026 checkbox is marked complete **only** in the implementation
  stage.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-030`; FR-030; Constitution X.
  - Verification intent: `xcom_feature_gate.py verify T026 <baseline>`; `git diff --check`; CHK-24, NEG-29.

## 5. Requirement-to-accepted-anchor traceability

| T026 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T026-STK-001 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-021` | FR-021 | IX, X |
| T026-STK-002 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-021` | FR-021 | IX |
| T026-STK-003 | `XCOM-SW-STIM-003` | `XCOM-SYS-FR-017`, `XCOM-SYS-SC-006` | FR-017, SC-006 | IX |
| T026-STK-004 | `XCOM-SW-CORE-007` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | II, VII, IX |
| T026-STK-005 | Constitution VII/IX; ADR-0018/0020 | `XCOM-SYS-FR-030` | FR-030 | VII, IX, X |
| T026-SR-001 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-021/030` | FR-021, FR-030 | VII, X |
| T026-SR-002 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-026` | FR-026 | II, VII |
| T026-SR-003 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-021/027` | FR-021, FR-027 | IX, X |
| T026-SR-004 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-007` | FR-007 | IX |
| T026-SR-005 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-021/027` | FR-021, FR-027 | IX |
| T026-SR-006 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-021` | FR-021 | IX |
| T026-SR-007 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-021/007` | FR-021, FR-007 | IX |
| T026-SR-008 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-021` | FR-021 | IX |
| T026-SR-009 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-021` | FR-021 | IX |
| T026-SR-010 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-021` | FR-021 | IX |
| T026-SR-011 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-007/021` | FR-007, FR-021 | V, IX |
| T026-SR-012 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-007` | FR-007 | IX |
| T026-SR-013 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-021` | FR-021 | IX |
| T026-SR-014 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-021` | FR-021 | IX |
| T026-SR-015 | `XCOM-SW-STIM-003` | `XCOM-SYS-FR-017`, `XCOM-SYS-SC-006` | FR-017, SC-006 | IX |
| T026-SR-016 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-021/025` | FR-021, FR-025 | IX |
| T026-SR-017 | `XCOM-SW-STIM-007` | `XCOM-SYS-FR-007/014` | FR-007, FR-014 | IX |
| T026-SR-018 | `XCOM-SW-CORE-007` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | II, VII, IX |
| T026-SR-019 | public-safe evidence rule | `XCOM-SYS-FR-027` | FR-027 | X |
| T026-SR-020 | `XCOM-SW-STIM-007` Doxygen | `XCOM-SYS-FR-029` | FR-029 | X |
| T026-SR-021 | Constitution; ADR-0020 | `XCOM-SYS-FR-030/035` | FR-030, FR-035 | VII, IX |
| T026-SR-022 | ADR-0020 | `XCOM-SYS-FR-030` | FR-030 | X |

`XCOM-SW-STIM-003` and `XCOM-SW-STIM-007` are accepted capability-007 software requirements
(`docs/engineering/xcom/t008/requirements-register.{json,md}`). They are accepted text; T026 refines and
consumes them and does not rewrite them. No register row is changed and no maturity is promoted.

## 6. REF-002 disposition

T026 owns no REF-002 SADS ID and promotes none. It provides evidence toward the allocated communication
IDs already exercised by the stimulation boundary: `XVE-SYS-0147` (bounded queueing/overflow and explicit
failure), `XVE-SYS-0149` (deterministic diagnostics and metrics), and the bounded-failure portion of
`XVE-SYS-0158` (deferred automatic recovery; capability 007 defines the bounded failure outcome). It
promotes nothing, and the capability `ref002.disposition` stays `unchanged` with an empty `promoted` list
(T026-SR-021). No allocated, deferred, architectural-target, or superseded SADS requirement is reported
as implemented.

## 7. Affected paths

### 7.1 Paths the T026 candidate changes (implementation stage)

| Path | Change | Notes |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/stimulation_journal.hpp` | add | new public journal interface (types, bounds, ordering seam, recovery) |
| `src/xverse/xcom/src/stimulation_journal.cpp` | add | implementation, including the local-file storage seam |
| `src/xverse/xcom/CMakeLists.txt` | edit | add `xverse_xcom_stimulation_journal` to `XVERSE_XCOM_RUNTIME_TARGETS`; define the library; add the additive test targets and labels |
| `tests/xcom/stimulation_journal/unit_tests.cpp` | add | nominal path and frame-layout cases |
| `tests/xcom/stimulation_journal/negative_tests.cpp` | add | fail-closed configuration/record/capacity/reference matrix |
| `tests/xcom/stimulation_journal/recovery_tests.cpp` | add | real-file restart recovery, orphan surfacing, provenance round-trip |
| `tests/xcom/stimulation_journal/failure_tests.cpp` | add | fault-injected write/sync/disk-full/partial-write/callback failures |
| `tests/xcom/stimulation_journal/concurrency_tests.cpp` | add | bounded deterministic concurrency and callback-outside-lock |
| `docs/engineering/xcom/t026/requirements.md` | add | this document |
| `docs/engineering/xcom/t026/architecture.md` | add | T026 architecture |
| `docs/engineering/xcom/t026/detailed-design.md` | add | T026 detailed design |
| `docs/engineering/xcom/t026/unit-specifications.md` | add | T026 unit specifications |
| `docs/engineering/xcom/t026/verification-plan.md` | add | T026 verification plan |
| `docs/engineering/xcom/t026/implementation.md` | add | implementation-stage record |
| `docs/engineering/xcom/t026/internal-review.json` | add | internal-review record |
| `specs/007-xcom-core/tasks.md` | edit | one-line T026 checkbox, **implementation stage only** |
| `reports/xcom-queue/t026-package.json` | add | implementation-stage package record |

### 7.2 Consumed read-only (not changed by T026)

`src/xverse/xcom/include/xverse/xcom/validation_session.hpp`,
`src/xverse/xcom/src/validation_session.cpp`, `tests/xcom/validation_session/**`,
`src/xverse/xcom/include/xverse/xcom/core_types.hpp` and the other accepted core headers,
`docs/engineering/xcom/task-ownership.*`, `docs/engineering/xcom/t008/**`,
`docs/engineering/xcom/t009/**`, `docs/engineering/xcom/t010/**`, `specs/007-xcom-core/**` (other than the
checkbox), `xdl/**`, `cmake/XComOfflineDependencies.cmake`, `cmake/XComWarnings.cmake`, and the root
`CMakeLists.txt`.

### 7.3 Explicitly not implemented by T026

`stimulation_guard.hpp/.cpp` (T027), `stimulation_actions.hpp/.cpp` and the service-emulation lease
(T028), `proto/xverse/xcom/v1/tool_gateway.proto` and the gateway (T030–T031), and the contract/benchmark/
Doxygen/delivery tasks (T033–T041).

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- **T026-GAP-01 — provenance partial.** `XCOM-SW-STIM-003` is implemented only on the persistence/restart
  side; routed-item classification and observation propagation remain `XCOM-DU-018`/T028 and are tested in
  T029. T026 claims no `synthetic-provenance` end-to-end evidence.
- **T026-GAP-02 — durability scope.** "Durable" means the frame is written and synced through the
  host-supplied storage seam on the local filesystem. It is not a claim of crash consistency on arbitrary
  filesystems, media failure, power-loss atomicity at the storage device, encryption, or tamper resistance;
  those remain later security/reliability capabilities.
- **T026-GAP-03 — retention policy.** Retention is a declared finite record/byte bound with fail-closed
  behaviour. Compaction, pruning, archival, rotation, and export are not implemented and remain unclaimed.
- **T026-GAP-04 — no action semantics.** The journal records and resolves intent/outcome identity; it
  performs no authorization, schema, target, direction, action, quota, loop, or ownership validation
  (T027) and no emission (T028).
- **T026-GAP-05 — single-writer.** Concurrency is bounded to one writer per journal; multi-writer or
  multi-process journal sharing is not supported and is not claimed.

### 8.2 Gaps with owning tasks

| Gap | Owner |
| --- | --- |
| Pre-emission guard and zero-emission-on-rejection | T027 |
| Injection/invocation/emulation and routed synthetic classification | T028 |
| Full matrix, quota/loop/lease/drain, end-to-end provenance tests | T029 |
| Gateway, Protocol Buffers/gRPC, separate process | T030–T034 |
| Executed sanitizer/static/Doxygen/benchmark and delivery bundle | T035–T040 |
| Independent review and user acceptance | T039/T041 |

### 8.3 Open items

- **T026-OPEN-01**: The T010 `XCOM-DU-016` plan records 5 documented public elements and planned evidence
  `CHK-07`/`NEG-27`. If the implemented public surface is larger, the implementation stage records the
  delta and the affected plan/register reconciliation as a successor note rather than editing the
  accepted T010 artifact silently.
- **T026-OPEN-02**: The real-file recovery tests require a bounded, host-derived scratch directory. The
  implementation stage records the scratch-path policy (test-local, git-ignored, never printed in public
  evidence) and fails closed if no bounded path is available.

## 9. Definition of done (requirements view)

T026 is done for a candidate revision when: every §4 requirement has at least one named check; the
journal-before-emission, atomic/partial-write, capacity/retention, disk-full/I/O, restart-recovery, and
evidence-incomplete behaviours are proven by deterministic tests; `XCOM-SW-STIM-007` is implemented and
`XCOM-SW-STIM-003` is recorded partial with the routing/observation half explicitly deferred; no accepted
requirement, test, ADR, contract, register, or T025 byte is weakened; the register validators pass with
REF-002 unchanged and nothing promoted; the deterministic gate passes; and a separate DeepSeek internal
review records its findings before any repair. This does not constitute user acceptance.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary checks |
| --- | --- |
| T026-STK-001 | CHK-01, CHK-02, CHK-24 |
| T026-STK-002 | CHK-07, CHK-08, CHK-12, CHK-14 |
| T026-STK-003 | CHK-16 |
| T026-STK-004 | CHK-17, CHK-18, CHK-19, CHK-21 |
| T026-STK-005 | CHK-02, CHK-18, CHK-23, CHK-24 |
| T026-SR-001 | CHK-02, CHK-04, CHK-18 |
| T026-SR-002 | CHK-03, CHK-19 |
| T026-SR-003 | CHK-05, CHK-20 |
| T026-SR-004 | CHK-06 |
| T026-SR-005 | CHK-07, CHK-18 |
| T026-SR-006 | CHK-08, CHK-12 |
| T026-SR-007 | CHK-09, CHK-12 |
| T026-SR-008 | CHK-10 |
| T026-SR-009 | CHK-11 |
| T026-SR-010 | CHK-12 |
| T026-SR-011 | CHK-13 |
| T026-SR-012 | CHK-06 |
| T026-SR-013 | CHK-14 |
| T026-SR-014 | CHK-15 |
| T026-SR-015 | CHK-16 |
| T026-SR-016 | CHK-17 |
| T026-SR-017 | CHK-18 |
| T026-SR-018 | CHK-19 |
| T026-SR-019 | CHK-21 |
| T026-SR-020 | CHK-22 |
| T026-SR-021 | CHK-23 |
| T026-SR-022 | CHK-24 |
