# T029 Requirements — Complete Stimulation Verification Matrix and Owned Conformance Fixtures

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T029 (capability 007, slice `T-STIM`) |
| Task title | Test the complete permit/action mismatch matrix, journal-before-emission and journal failure/recovery, zero emission after every rejection, persistent synthetic provenance, unmapped clocks, quotas, loop bounds, lease conflicts, drain/terminal behavior, and deterministic concurrency |
| Stage / role | plan → requirements |
| Revision | 1 (complete T-STIM cross-cutting verification matrix) |
| Baseline revision | `4d3985855ef7a62b68aa4c66d3b7df032b29f5e9` |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC006`, `ACC010`, `ACC011`, `ACC014`, `ACC015`); `ADR-0016` (subsystem naming); `ADR-0018` (platform-first); `ADR-0019` (stimulation observation/stimulation ownership); `ADR-0020` (repository-owned work products and exact-candidate evidence) |
| Owning slice | `T-STIM` (T007 ownership register); T029 is the last `T-STIM` task and closes the slice evidence |
| Predecessors | T025 — bounded time authority, immutable validation permit, and bounded session lifecycle (accepted, consumed read-only); T026 — bounded durable stimulation intent/outcome journal (present at the baseline, consumed read-only); T027 — fail-closed pre-emission guard (present at the baseline, consumed read-only); T028 — guarded injection/invocation/emulation, exclusive generation-bound lease, and lifecycle completion (present at the baseline `4d3985855ef7a62b68aa4c66d3b7df032b29f5e9`, consumed read-only) |
| Producer dependencies | T011 admitted offline build envelope (read-only inputs); T012 subtree CMake/CTest contract and warning-as-error rule; T013/T-CORE immutable contract/item-origin/interaction vocabulary (`xverse::xcom::OriginKind`, `InteractionKind`, `EndpointDirection`, `CommunicationItem`, consumed read-only); T014/T015 endpoint/route lifecycle and loopback provider (read-only); T021–T024 observation boundary (`ObservationHub`, `ObservationTapSpec`, `SyntheticObservationSink`, read-only); T025 `validation_session.hpp`; T026 `stimulation_journal.hpp`; T027 `stimulation_guard.hpp`; T028 `stimulation_actions.hpp` |
| Successor tasks | T030–T034 (gateway/conformance), T035–T041 (evidence, review, acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}` (`T-STIM` slice evidence names; T029 exclusive path `docs/engineering/xcom/t029/`); `docs/engineering/xcom/t008/requirements-register.{json,md}` (`XCOM-SW-STIM-003`, `XCOM-SW-STIM-009` owning/contributing rows plus `-005`/`-006`/`-008`); `docs/engineering/xcom/t009/architecture-model.{json,md}` (`XCOM-CMP-009`, `XCOM-XB-007`, `XCOM-XLC-006`, `XCOM-INV-03`, `XCOM-INV-04`, `XCOM-INV-05`, `XCOM-INV-07`, `XCOM-INV-09`, `XCOM-INV-10`); `docs/engineering/xcom/t010/unit-design.{json,md}` (`XCOM-DU-014`…`XCOM-DU-018`) |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any test change and does
not implement, accept, or integrate the candidate. The T029 task entry in `specs/007-xcom-core/tasks.md` is the
authorized scope:

> T029 — Test the complete permit/action mismatch matrix, journal-before-emission and journal failure/recovery,
> zero emission after every rejection, persistent synthetic provenance, unmapped clocks, quotas, loop bounds,
> lease conflicts, drain/terminal behavior, and deterministic concurrency.

### 1.1 Authority statement

This document specifies only the bounded T029 slice. T029 is a **test-only** task: it authors no production
behaviour and changes no production header, source, or target. It closes the `T-STIM` verification matrix by
adding bounded, owned-fixture tests over the already implemented and accepted T025/T026/T027/T028 surfaces.

It implements one accepted software requirement from `docs/engineering/xcom/t008/requirements-register.{json,md}`
that the register allocates to T029:

- `XCOM-SW-STIM-009` "Owned action conformance and lifecycle completion" — "Demonstrate signal injection,
  message injection, service invocation, and bounded service emulation with owned fixtures plus drain, close,
  revoke, expiry, and evidence-incomplete lifecycle completion." (refines `XCOM-SYS-SC-007`, spec `SC-007`).

It closes the remaining maturity of a second accepted software requirement that the register allocates to T026
and that T026 and T028 recorded **partial**:

- `XCOM-SW-STIM-003` "Persistent synthetic provenance" — "Classify every injected item visibly as synthetic or
  tool-originated and preserve tool, session, request, correlation, and causal identity through routing,
  observation, and restart." (refines `XCOM-SYS-FR-017`, `XCOM-SYS-SC-006`, spec `FR-017`/`SC-006`). T029
  supplies the routed, observed, and restarted identity-persistence proof through the accepted provider route,
  the accepted observation boundary, and a journal restart, so `XCOM-SW-STIM-003` is recorded **implemented**
  by the T029 per-task projection.

It contributes the complete cross-cutting verification evidence toward three accepted requirements already
recorded **implemented** by T028, without changing their owning task or their recorded disposition:

- `XCOM-SW-STIM-005` "Loop bounding and conflict rejection" (`XCOM-SYS-FR-019`, `FR-019`);
- `XCOM-SW-STIM-006` "Scheduling, clock authority, and tolerance" (`XCOM-SYS-FR-020`/`FR-033`, `FR-020`/`FR-033`);
  and
- `XCOM-SW-STIM-008` "Exclusive service-emulation lease" (`XCOM-SYS-FR-034`, `FR-034`).

It consumes the accepted design units `XCOM-DU-014` (time authority), `XCOM-DU-015` (permit and session
lifecycle), `XCOM-DU-016` (durable journal), `XCOM-DU-017` (fail-closed guard), and `XCOM-DU-018` (guarded
injection and exclusive service-emulation lease), the accepted component `XCOM-CMP-009` "Validation stimulation
session", the accepted boundary `XCOM-XB-007` ("Fail-closed pre-emission guard; rejection emits zero normal-route
items"), the accepted contract `XCOM-XLC-006`, and the accepted safety/data-model invariants `XCOM-INV-03`
(synthetic origin survives routing and observation), `XCOM-INV-04` (one permitted service-emulation owner per
endpoint and session), `XCOM-INV-05` (all queues and quotas are finite with declared overflow behaviour),
`XCOM-INV-07` (every stimulation decision is bound to the exact plan digest), `XCOM-INV-09` (scheduled requests
never compare or order unmapped clock domains), and `XCOM-INV-10` (one endpoint generation has at most one active
service-emulation lease).

**Owned fixtures.** T029 exercises the accepted surfaces with one bounded, payload-free, offline owned fixture
harness composed in the tests (an in-process permit/session, the accepted journal over an in-test fault-injectable
storage seam, the accepted exclusive lease registry, the accepted action path, a recording/fault-injectable host
emitter, and a bounded bridge into the accepted provider/observation boundary). The harness owns only bounded
values and never re-implements, weakens, or bypasses an accepted guard, journal, provider, or observation check.

**Boundary honesty.** T029 proves the complete matrix only at the in-process stimulation boundary and the accepted
provider/observation boundary; it authors no gateway, Protocol Buffers/gRPC, IPC, separate-process client, reusable
contract-suite abstraction, benchmark, sanitizer/static/Doxygen execution, or delivery bundle. The gateway and the
reusable provider/observer/stimulation-tool contract suites remain T030–T034, and executed sanitizer/static/
Doxygen/benchmark evidence and the delivery bundle remain T035–T040.

It does **not** redesign the accepted architecture, change a functional requirement, success criterion, ADR,
schema, XDL profile, or contract; modify `validation_session.hpp`/`.cpp`, `stimulation_journal.hpp`/`.cpp`,
`stimulation_guard.hpp`/`.cpp`, `stimulation_actions.hpp`/`.cpp`, or any existing test, target, label, command, or
expected value; implement the tool gateway or Protocol Buffers/gRPC (T030–T034); add an admitted dependency; or
accept or integrate any candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, data model,
the T007 ownership register, the T008 register, the T009 architecture model, the T010 unit design, the
constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is reported rather
than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T029)

1. **New additive test-only slice.** Add bounded GoogleTest suites under a new directory
   `tests/xcom/stimulation_matrix/` and register them as new additive CTest executables in
   `src/xverse/xcom/CMakeLists.txt`. No production header, source, or runtime target changes; no existing test,
   target, test name, label, command, or expected value changes (additive only).
2. **Complete permit/action mismatch matrix (`FR-018`, `FR-019`, `XCOM-SW-STIM-005`, `XCOM-SW-STIM-006`).**
   Exercise every request-evaluation guard reason and every lifecycle-state precondition through the accepted T028
   action path, asserting the declared `ActionStatus`, the preserved `GuardReason`, exactly one guard evaluation,
   zero emission, and zero journal append. The matrix covers `RejectedConfiguration`, `PermitMismatch`,
   `SchemaMismatch`, `DirectionMismatch`, `InteractionMismatch`, `TargetMismatch`, `ActionMismatch`,
   `OwnershipConflict`, `QuotaExhausted`, `LoopBound`, `TimeOutOfWindow` (`Rejected`), and `TimeUnmapped`
   (`Failed`), plus the action-path lifecycle-state preconditions (`Revoked`, `Expired`, `NotActive` →
   `ActionStatus::NotActive`) and the directly exercised closed-guard `NotOpen` guard row.
3. **Quotas (`XCOM-SW-STIM-006`, `XCOM-INV-05`).** Exercise the finite per-session and per-window authorized-action
   budgets: the budget is committed exactly once per authorization, a budget-exhausted request is rejected with
   zero emission and zero journal, and no bounded sequence or bounded concurrent run exceeds the declared quota.
4. **Loop bounds (`XCOM-SW-STIM-005`).** Exercise the accepted guard loop window together with the action-path
   emission-time lineage window: a causal parent already retained is rejected with zero emission and zero journal,
   `causation_id == 0` is never a loop rejection, and the lineage window never exceeds its declared depth.
5. **Journal-before-emission and journal failure/recovery (`FR-021`, `XCOM-SW-STIM-007` consumed).** Prove the
   durable intent precedes the single emitter call for each of the four action kinds; a failed intent append or
   sync emits nothing and journals nothing durable; a failed outcome append surfaces `EvidenceIncomplete` and is
   never reported as success; and a journal restart over the same durable bytes recovers the exact intent identity
   and the explicit orphan classification.
6. **Zero emission after every rejection (`FR-018`, `XCOM-SW-STIM-005`).** For every decline family — closed path,
   malformed request, over-bound payload, loop, pending-queue capacity, emulation-lease conflict, non-active
   session, guard rejection, guard failure, quota exhaustion, late rejection, and unmapped/out-of-tolerance time —
   prove the recording emitter observed zero calls, the durable journal bytes are unchanged, and the operational
   snapshot is unchanged apart from declared counters.
7. **Persistent synthetic provenance (`FR-017`, `SC-006`, `XCOM-SW-STIM-003`, `XCOM-INV-03`).** Prove every emitted
   descriptor carries an explicit `OriginKind::validation_tool` classification and the exact tool, permit,
   session, plan, request, correlation, and causal identity; prove that a bridged item submitted through the
   accepted provider route and retained by the accepted observation tap keeps the synthetic classification and the
   exact correlation/causation identity; and prove the durable intent identity survives a journal restart
   unchanged. No path emits, routes, observes, relabels, or drops a differently classified item.
8. **Unmapped clocks (`FR-020`, `FR-033`, `XCOM-SW-STIM-006`, `XCOM-INV-09`).** Prove a request whose resolved time
   is absent, unmapped, or outside the declared tolerance fails closed before emission and before journaling, that
   an immediate request is explicitly labeled, and that the action path and lease registry never compare or order
   two raw mismatched clock domains and never call or mutate a time authority.
9. **Lease conflicts (`FR-034`, `XCOM-SW-STIM-008`, `XCOM-INV-04`, `XCOM-INV-10`).** Prove end-to-end: a second
   owner for one endpoint generation is rejected with zero emission; a foreign session, generation, or plan digest
   is rejected with the matching lease status and no mutation; a superseded generation neither authorizes nor
   conflict-blocks; release, quarantine, and expiry relinquish ownership; and at most one active lease exists per
   endpoint generation.
10. **Drain and terminal behavior (`SC-007`, `XCOM-SW-STIM-009`).** Prove the bounded scheduled ordering rule, the
    bounded drain step budget, both late-item policies, and the drain/close/revoke/expire/evidence-incomplete
    completion matrix: pending work is drained or cancelled as declared, every held lease is released or
    quarantined, and a durable intent without a durable outcome forces `EvidenceIncomplete` and is never reported
    as `Closed`.
11. **Deterministic concurrency (`FR-007`, `FR-014`).** Prove bounded deterministic concurrency with at most four
    threads and a finite declared operation count: a declared guard quota is never exceeded, a lease race has
    exactly one winner, concurrent completion commits a deterministic total order, repeated runs produce identical
    statuses, states, outcomes, and snapshots, and no host callback is invoked under a lock.
12. **Bounded, offline, deterministic tests.** Every fixture, table, queue, lease, thread, and iteration is finite
    and declared; the suites are offline and local-only and add no admitted dependency; no case depends on
    wall-clock timing for its verdict.
13. The T029 repository-owned work products and the T029 package record.

### 2.2 Explicit exclusions (must remain absent from the T029 candidate)

No change to any production header, source, or runtime target, including `stimulation_actions.hpp`/`.cpp`,
`stimulation_guard.hpp`/`.cpp`, `stimulation_journal.hpp`/`.cpp`, and `validation_session.hpp`/`.cpp`; no change to
any existing test, target, test name, label, command, or expected value (additive only); no re-implementation,
weakening, or bypass of the accepted guard, journal, provider, or observation checks; no tool gateway, Protocol
Buffers/gRPC, IPC, TCP listener, or separate process (T030–T034); no reusable contract-suite abstraction (T033);
no benchmark, sanitizer/static/Doxygen *execution*, or delivery bundle (T035–T040); no payload/value-body logging,
payload decoder, redaction profile, dashboard, storage, query, or export primitive; no new admitted dependency; no
network, socket, DNS, TLS, ambient/secret, dynamic-load, subprocess, or legacy-repository/binary access; no
wall-clock-dependent verdict; no time-authority mutation; no rewrite or weakening of an accepted ADR, requirement,
contract, schema, register, target, or test; no promotion of any REF-002 SADS ID beyond its recorded disposition;
no acceptance or integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T029 |
| --- | --- | --- |
| Local tool gateway, versioned Protocol Buffers/gRPC contract, separate-process synthetic client | T030–T032 | allocated |
| Reusable provider/observer/stimulation-tool/gateway contract suites and a second synthetic provider | T033/T034 | allocated; T029 authors a bounded in-test fixture only |
| Executed sanitizer/static-analysis/Doxygen evidence, benchmarks, integration, delivery bundle | T035–T040 | allocated |
| Independent review and user acceptance | T039/T041 | allocated; external Codex review and acceptance deferred until backlog `xcom-t026-t029-20260928` completes |

## 3. Stakeholder requirements (`T029-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T029-STK-001**: Before the `T-STIM` slice is presented for acceptance, the program **shall** have a
  repository-owned, bounded, offline, owned-fixture test matrix, physically under `tests/xcom/stimulation_matrix/`
  with additive CTest registration in `src/xverse/xcom/CMakeLists.txt`, that exercises the complete permit/action
  mismatch matrix, journal-before-emission and journal failure/recovery, zero emission after every rejection,
  persistent synthetic provenance, unmapped clocks, quotas, loop bounds, lease conflicts, drain/terminal behavior,
  and deterministic concurrency over the accepted T025/T026/T027/T028 surfaces.
- **T029-STK-002**: Every rejection family **shall** emit zero normal-route items, append zero durable journal
  records in the declined dimension, and mutate no operational guard, lease, queue, lineage, or journal state; an
  action that cannot be completed **shall** be surfaced explicitly and **shall never** be reported as success.
- **T029-STK-003**: T029 **shall** preserve accepted intent: the delivered change is confined to the T029 test
  paths, the shared build file, the T029 work products, the inherited provenance refresh, and the capability task
  ledger, and it **shall** neither modify an accepted production byte nor weaken an accepted requirement or test.
- **T029-STK-004**: The matrix **shall** be offline, local-only, bounded, and deterministic: every record, table,
  queue, lease, thread, and iteration is finite and declared; it performs no network, socket, ambient
  configuration, secret, dynamic-load, process, or legacy access, adds no domain-specific primitive, and adds no
  new admitted dependency.
- **T029-STK-005**: T029 **shall** report maturity honestly: `XCOM-SW-STIM-009` is recorded implemented by T029,
  `XCOM-SW-STIM-003` is recorded implemented by the T029 projection (routed, observed, and restarted proof),
  `XCOM-SW-STIM-005`/`-006`/`-008` remain implemented, and the register's REF-002 disposition stays `unchanged`
  with an empty `promoted` list; no requirement is promoted beyond its recorded disposition.

## 4. Software/engineering requirements (`T029-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted anchor.
"Verified" means the repository-owned test exists, is deterministic, and passes at the recorded candidate
revision; it is not a production, compatibility, or end-to-end route claim.

### 4.1 Test slice, build wiring, and dependency reuse

- **T029-SR-001 [ubiquitous]**: The matrix **shall** be a new, additive, test-only set of GoogleTest sources at
  `tests/xcom/stimulation_matrix/` registered as new additive CTest executables in
  `src/xverse/xcom/CMakeLists.txt` (`xverse_xcom_stimulation_matrix_<kind>_tests`) with one hyphenated `t029-<kind>`
  label each; it **shall** change no production header, source, runtime target, or existing test, target, label,
  command, or expected value, and it **shall** add no runtime target to the T012 `XVERSE_XCOM_RUNTIME_TARGETS`
  inventory.
  - Refines: `XCOM-SW-STIM-009`; anchors `XCOM-SYS-SC-007`, `XCOM-SYS-FR-030`; SC-007, FR-030; ADR-0020; T012
    subtree build contract.
  - Verification intent: changed-path and discovered-count comparison plus the full suite; CHK-02, CHK-04,
    CHK-18, NEG-01.
- **T029-SR-002 [ubiquitous]**: The fixtures and cases **shall** depend only on the C++ standard library, GTest,
  the accepted T025/T026/T027/T028 public headers, and the accepted T-CORE/T-OBS public headers (`item.hpp`,
  `observation.hpp`, `provider.hpp`, `endpoint_route_lifecycle.hpp`); they **shall** add no admitted dependency
  and **shall** redefine no identity, digest, diagnostic, interaction, origin, action, lease, or completion
  vocabulary where an accepted one exists.
  - Refines: `XCOM-SW-STIM-009`; anchors `XCOM-SYS-FR-026`, `XCOM-SYS-FR-030`; FR-026, FR-030; `XCOM-XLC-006`;
    Constitution II, VII.
  - Verification intent: include/link inspection and the offline build; CHK-03, CHK-19, NEG-02.

### 4.2 Owned fixture harness

- **T029-SR-003 [ubiquitous]**: The slice **shall** provide one shared, bounded, payload-free owned fixture in
  `tests/xcom/stimulation_matrix/test_support.hpp` that composes an in-process accepted `Permit` and session, an
  accepted `StimulationPolicy`, an accepted `StimulationJournal` over an in-test fault-injectable `Storage` seam,
  an accepted `ServiceEmulationRegistry`, an accepted `StimulationActionPath`, a recording/fault-injectable
  `ActionEmitter`, and a bounded bridge that builds a `CommunicationItem` for the accepted provider/observation
  boundary; every bound, table, and injected fault **shall** be finite and declared, and the fixture **shall**
  retain no payload byte.
  - Refines: `XCOM-SW-STIM-009`, `XCOM-SW-STIM-003`; anchors `XCOM-SYS-SC-007`, `XCOM-SYS-FR-017`; SC-007,
    FR-017; `XCOM-INV-03`; `XCOM-DU-014`…`-018`.
  - Verification intent: fixture declaration inspection plus the build; CHK-05, CHK-20, NEG-03.

### 4.3 Complete permit/action mismatch matrix

- **T029-SR-004 [event-driven]**: When the matrix evaluates a request, every request-evaluation guard reason
  **shall** be exercised through the accepted action path and **shall** map to the declared `ActionStatus`
  (`Rejected` for a definite mismatch, `Failed` for an indeterminate evaluation) with the exact `GuardReason`
  preserved; the accepted guard **shall** be evaluated exactly once per request, the recording emitter **shall**
  observe zero calls, and the durable journal **shall** append zero records.
  - Refines: `XCOM-SW-STIM-005`, `XCOM-SW-STIM-004` (consumed); anchors `XCOM-SYS-FR-018`, `XCOM-SYS-FR-019`;
    FR-018, FR-019; `XCOM-XB-007`; `XCOM-DU-017`, `XCOM-DU-018`.
  - Verification intent: mismatch-row matrix; CHK-06, CHK-15, NEG-04, NEG-05.
- **T029-SR-005 [event-driven]**: When the matrix evaluates a lifecycle-state precondition, a `revoked`,
  `expired`, `declared`, `armed`, or `closing` session state **shall** decline at the action path with
  `ActionStatus::NotActive` before any emission or journal append, and a directly evaluated closed guard **shall**
  return `Failed`/`NotOpen`, with zero emission in both cases.
  - Refines: `XCOM-SW-STIM-009`, `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-018`, `XCOM-SYS-SC-007`; FR-018, SC-007;
    `XCOM-XB-007`; `XCOM-DU-015`, `XCOM-DU-018`.
  - Verification intent: lifecycle-precondition matrix; CHK-06, NEG-06.
- **T029-SR-006 [event-driven]**: When the matrix exercises quotas, the finite per-session and per-window
  authorized-action budgets **shall** be committed exactly once per authorization; a budget-exhausted request
  **shall** be `Rejected`/`QuotaExhausted` with zero emission and zero journal; and no bounded sequential or
  bounded concurrent run **shall** exceed the declared budget.
  - Refines: `XCOM-SW-STIM-006`, `XCOM-SW-STIM-005`; anchors `XCOM-SYS-FR-019`, `XCOM-SYS-FR-020`; FR-019, FR-020;
    `XCOM-INV-05`; `XCOM-DU-017`, `XCOM-DU-018`.
  - Verification intent: quota-bound matrix and the bounded concurrency quota check; CHK-07, CHK-16, NEG-07,
    NEG-08.
- **T029-SR-007 [event-driven]**: When the matrix exercises loop bounds, a request whose causal parent is already
  retained in the accepted guard loop window **or** in the action-path emission-time lineage window **shall** be
  `Rejected`/`LoopBound` with zero emission and zero journal; `causation_id == 0` **shall never** be a loop
  rejection; and the lineage window **shall never** exceed its declared depth and **shall** evict the oldest
  identity.
  - Refines: `XCOM-SW-STIM-005`; anchors `XCOM-SYS-FR-019`; FR-019; `XCOM-DU-017`, `XCOM-DU-018`.
  - Verification intent: loop-bound and lineage-eviction matrix; CHK-08, NEG-09, NEG-10.
- **T029-SR-008 [event-driven]**: When the matrix exercises clock resolution, an absent, unmapped, or
  out-of-tolerance resolved time **shall** fail closed before emission and before journaling intent; an immediate
  request **shall** be explicitly labeled; and the action path and lease registry **shall never** compare or order
  two raw mismatched clock domains and **shall** call no time authority.
  - Refines: `XCOM-SW-STIM-006`; anchors `XCOM-SYS-FR-020`, `XCOM-SYS-FR-033`; FR-020, FR-033; `XCOM-INV-09`;
    `XCOM-DU-014`, `XCOM-DU-018`.
  - Verification intent: unmapped/out-of-tolerance and no-authority-call matrix; CHK-09, NEG-11, NEG-12.

### 4.4 Journal ordering, failure, and recovery

- **T029-SR-009 [event-driven]**: For each of the four action kinds, the durable intent record **shall** be
  present and non-empty inside the single emitter invocation, and the emitter **shall** be invoked exactly once
  per authorized emission and never before the intent is durable.
  - Refines: `XCOM-SW-STIM-007` (consumed), `XCOM-SW-STIM-009`; anchors `XCOM-SYS-FR-021`; FR-021; `XCOM-DU-016`,
    `XCOM-DU-018`.
  - Verification intent: journal-before-emission ordering observation; CHK-10, NEG-13.
- **T029-SR-010 [event-driven]**: When an intent append or sync fails, the action **shall** return the matching
  non-emitting `ActionStatus` (`JournalFailed`/`CapacityExhausted`/`RejectedConfiguration`), the emitter **shall**
  observe zero calls, and no durable record **shall** be committed.
  - Refines: `XCOM-SW-STIM-009`, `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-021`; FR-021; `XCOM-DU-016`,
    `XCOM-DU-018`.
  - Verification intent: injected intent-append/sync failure matrix; CHK-11, NEG-14, NEG-15.
- **T029-SR-011 [event-driven]**: When a durable intent cannot obtain a durable outcome, the action **shall** be
  surfaced as `ActionStatus::EvidenceIncomplete` and **shall never** be reported as `Emitted`; a restart over the
  same durable bytes **shall** recover the exact intent identity and classify it as an explicit orphan; and
  `mark_evidence_incomplete`/`close` **shall** report the orphan and **shall never** return `Closed` while it
  exists.
  - Refines: `XCOM-SW-STIM-009`, `XCOM-SW-STIM-007`; anchors `XCOM-SYS-FR-021`, `XCOM-SYS-SC-007`; FR-021, SC-007;
    `XCOM-DU-016`, `XCOM-DU-018`.
  - Verification intent: injected outcome failure, restart recovery, and completion orphan matrix; CHK-11, CHK-14,
    NEG-16, NEG-17.

### 4.5 Zero emission and non-mutation

- **T029-SR-012 [unwanted]**: If any precondition, guard, lease, quota, loop, late-policy, journal, or clock
  decision declines, the matrix **shall** observe zero emitter calls, byte-identical durable journal bytes, and an
  operational snapshot unchanged apart from the declared rejection/latency counters; a declined action **shall
  never** return `Emitted`.
  - Refines: `XCOM-SW-STIM-005`, `XCOM-SW-STIM-008`; anchors `XCOM-SYS-FR-019`, `XCOM-SYS-FR-034`; FR-019, FR-034;
    `XCOM-XB-007`; `XCOM-DU-018`.
  - Verification intent: decline-family snapshot comparison with zero-call counting; CHK-12, NEG-18, NEG-19,
    NEG-20.

### 4.6 Persistent synthetic provenance

- **T029-SR-013 [ubiquitous]**: Every emitted descriptor **shall** carry `OriginKind::validation_tool` and the
  exact tool, permit, session, plan, request, correlation, and causal identity of the authorized request, for each
  of the four action kinds.
  - Refines: `XCOM-SW-STIM-003`; anchors `XCOM-SYS-FR-017`; FR-017; `XCOM-INV-03`; `XCOM-DU-018`.
  - Verification intent: descriptor classification and identity matrix; CHK-13, NEG-21.
- **T029-SR-014 [event-driven]**: When a stimulus classified `OriginKind::validation_tool` is submitted through
  the accepted provider route and retained by the accepted observation tap, the retained record **shall** preserve
  the synthetic classification and the exact correlation and causation identity, and **shall** not relabel, drop,
  or infer provenance.
  - Refines: `XCOM-SW-STIM-003`; anchors `XCOM-SYS-FR-017`, `XCOM-SYS-SC-006`; FR-017, SC-006; `XCOM-INV-03`;
    `XCOM-DU-018`; accepted T-OBS boundary.
  - Verification intent: routed/observed provenance preservation; CHK-13, NEG-22.
- **T029-SR-015 [event-driven]**: After a journal restart over the same durable bytes, the recovered intent
  identity **shall** equal the identity of the emitted descriptor, and a filter constrained to
  `OriginKind::validation_tool` **shall** match every retained synthetic record and no other origin.
  - Refines: `XCOM-SW-STIM-003`; anchors `XCOM-SYS-FR-017`; FR-017; `XCOM-INV-03`, `XCOM-INV-07`; `XCOM-DU-016`,
    `XCOM-DU-018`.
  - Verification intent: restart identity equality and origin filter; CHK-13, NEG-23.

### 4.7 Lease conflicts

- **T029-SR-016 [event-driven]**: When the matrix exercises the exclusive lease end-to-end, a second owner for one
  endpoint generation **shall** be rejected with zero emission; a foreign session, generation, or plan digest
  **shall** be rejected with the matching lease status and no mutation; a superseded generation **shall** neither
  authorize nor conflict-block; release, quarantine, and expiry **shall** relinquish ownership; and at most one
  active lease **shall** exist per endpoint generation (`XCOM-INV-04`, `XCOM-INV-10`).
  - Refines: `XCOM-SW-STIM-008`; anchors `XCOM-SYS-FR-034`; FR-034; `XCOM-INV-04`, `XCOM-INV-10`; `XCOM-DU-018`.
  - Verification intent: end-to-end lease conflict/generation/release/quarantine/expiry matrix; CHK-08, CHK-17,
    NEG-24, NEG-25.
- **T029-SR-017 [event-driven]**: An elapsed lease in a declared domain **shall** become inactive and **shall** no
  longer authorize or conflict-block, and a value in a foreign domain **shall never** be compared or ordered
  (`XCOM-INV-09`).
  - Refines: `XCOM-SW-STIM-008`; anchors `XCOM-SYS-FR-033`, `XCOM-SYS-FR-034`; FR-033, FR-034; `XCOM-INV-09`;
    `XCOM-DU-018`.
  - Verification intent: lease-expiry and cross-domain matrix; CHK-09, CHK-17, NEG-12, NEG-26.

### 4.8 Drain and terminal behavior

- **T029-SR-018 [event-driven]**: The matrix **shall** prove the declared scheduled ordering rule, the bounded
  drain step budget, and both late-item policies: a due action drains in declared order, at most `max_drain_steps`
  pending actions complete per call, a full queue fails closed, and a late action under either policy emits
  nothing.
  - Refines: `XCOM-SW-STIM-006`, `XCOM-SW-STIM-009`; anchors `XCOM-SYS-FR-020`, `XCOM-SYS-SC-007`; FR-020, SC-007;
    `XCOM-DU-018`.
  - Verification intent: ordering/drain-budget/late-policy matrix; CHK-18, NEG-27, NEG-28.
- **T029-SR-019 [event-driven]**: The matrix **shall** prove the completion contract end-to-end: `drain`, `close`,
  `revoke`, `expire`, and `mark_evidence_incomplete` return the declared bounded outcomes; every pending action is
  drained or cancelled as declared; every held lease is released or quarantined; and a durable intent without a
  durable outcome forces `EvidenceIncomplete` and is never reported as `Closed`.
  - Refines: `XCOM-SW-STIM-009`; anchors `XCOM-SYS-SC-007`; SC-007; `XCOM-DU-018`.
  - Verification intent: drain/terminal/evidence-incomplete completion matrix; CHK-14, CHK-18, NEG-17, NEG-29,
    NEG-30.

### 4.9 Determinism, concurrency, and safety

- **T029-SR-020 [ubiquitous]**: The bounded deterministic-concurrency cases **shall** use at most four threads and
  a finite declared operation count, invoke no host callback under a lock, never exceed the declared queue, lease,
  quota, or lineage bounds, commit a deterministic total order, and produce identical statuses, states, outcomes,
  and snapshots across repeated runs; a lease race **shall** yield exactly one winner.
  - Refines: `XCOM-SW-STIM-008`, `XCOM-SW-STIM-009`; anchors `XCOM-SYS-FR-007`, `XCOM-SYS-FR-014`; FR-007, FR-014;
    `XCOM-DU-017`, `XCOM-DU-018`.
  - Verification intent: bounded deterministic-concurrency, quota, and single-winner cases; CHK-16, NEG-08,
    NEG-31, NEG-32.
- **T029-SR-021 [ubiquitous]**: The slice **shall** be deterministic: the same bounded operation sequence **shall**
  produce the same action status, lease state, completion outcome, and snapshot across repeated runs and builds,
  and the accepted closed vocabularies **shall** be exercised with their stable names/ranks.
  - Refines: `XCOM-SW-STIM-006`, `XCOM-SW-STIM-009`; anchors `XCOM-SYS-FR-025`; FR-025; `XCOM-DU-018`.
  - Verification intent: repeated-run equality and vocabulary-stability cases; CHK-16, CHK-19, NEG-31, NEG-33.
- **T029-SR-022 [ubiquitous]**: The slice **shall** be local-only and offline beyond the test-local fault-injectable
  journal storage seam and a bounded optional test-local scratch path for the restart case; it **shall** perform no
  network, socket, resolver, TLS, ambient-configuration, secret, dynamic-load, subprocess, or legacy
  repository/binary access, **shall** retain or log no payload byte, and **shall** add no domain-specific primitive.
  - Refines: `XCOM-SW-STIM-009`; anchors `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028`; FR-026, FR-028; ADR-0019;
    Constitution II, VII; `XCOM-INV-06`.
  - Verification intent: forbidden-API source scan and the offline build; CHK-19, CHK-20, NEG-34.
- **T029-SR-023 [ubiquitous]**: Committed tests, fixtures, work products, and evidence **shall** contain no
  credential, private address, unrestricted or real payload, proprietary source excerpt, environment-specific
  absolute host path, or sensitive deployment value.
  - Refines: Constitution X; anchors `XCOM-SYS-FR-027`; FR-027; public-safe evidence rule.
  - Verification intent: public-safety scan; CHK-21, NEG-35.

### 4.10 Governance and gate

- **T029-SR-024 [ubiquitous]**: T029 **shall** reconcile with the T007 ownership register, the T008 requirement
  register, the T009 architecture model, and the T010 unit design without rewriting or weakening them; **shall**
  keep the register REF-002 disposition `unchanged` with an empty `promoted` list; and **shall** record honestly
  that `XCOM-SW-STIM-009` and `XCOM-SW-STIM-003` are closed by T029, that `XCOM-SW-STIM-005`/`-006`/`-008` remain
  implemented, and that T030–T041 remain allocated.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-035`, `XCOM-SYS-FR-030`; FR-030, FR-035; Constitution VII, IX.
  - Verification intent: register validators plus the recorded-maturity inspection; CHK-23, NEG-36.
- **T029-SR-025 [ubiquitous]**: The T029 candidate **shall** satisfy the deterministic Fabro gate for a test task:
  the six named work products exist, at least one `tests/` path changes, `cmake` configure, build, discovery, and
  the full `ctest` suite pass, and `git diff --check` is clean; the T029 checkbox is marked complete **only** in
  the implementation stage, and the inherited `engineering/trace/links.json` and `engineering/stage-results/*.json`
  provenance digests are refreshed when the shared `src/xverse/xcom/CMakeLists.txt` digest changes.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-030`; FR-030; Constitution X.
  - Verification intent: `xcom_feature_gate.py verify T029 <baseline>`; `git diff --check`; CHK-24, NEG-37.

## 5. Requirement-to-accepted-anchor traceability

| T029 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T029-STK-001 | `XCOM-SW-STIM-009` | `XCOM-SYS-SC-007` | SC-007 | IX, X |
| T029-STK-002 | `XCOM-SW-STIM-005` | `XCOM-SYS-FR-019` | FR-019 | IX |
| T029-STK-003 | Constitution VII/IX; ADR-0020 | `XCOM-SYS-FR-030` | FR-030 | VII, IX, X |
| T029-STK-004 | `XCOM-SW-STIM-009` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | II, VII, IX |
| T029-STK-005 | ADR-0020 | `XCOM-SYS-FR-035` | FR-035 | VII, IX |
| T029-SR-001 | `XCOM-SW-STIM-009` | `XCOM-SYS-SC-007/FR-030` | SC-007, FR-030 | VII, X |
| T029-SR-002 | `XCOM-SW-STIM-009` | `XCOM-SYS-FR-026/030` | FR-026, FR-030 | II, VII |
| T029-SR-003 | `XCOM-SW-STIM-009/003` | `XCOM-SYS-SC-007/FR-017` | SC-007, FR-017 | IX |
| T029-SR-004 | `XCOM-SW-STIM-005` | `XCOM-SYS-FR-018/019` | FR-018, FR-019 | IX |
| T029-SR-005 | `XCOM-SW-STIM-009/004` | `XCOM-SYS-FR-018/SC-007` | FR-018, SC-007 | IX |
| T029-SR-006 | `XCOM-SW-STIM-005/006` | `XCOM-SYS-FR-019/020` | FR-019, FR-020 | IX |
| T029-SR-007 | `XCOM-SW-STIM-005` | `XCOM-SYS-FR-019` | FR-019 | IX |
| T029-SR-008 | `XCOM-SW-STIM-006` | `XCOM-SYS-FR-020/033` | FR-020, FR-033 | IX |
| T029-SR-009 | `XCOM-SW-STIM-007` (consumed) | `XCOM-SYS-FR-021` | FR-021 | IX |
| T029-SR-010 | `XCOM-SW-STIM-007/009` | `XCOM-SYS-FR-021` | FR-021 | IX |
| T029-SR-011 | `XCOM-SW-STIM-007/009` | `XCOM-SYS-FR-021/SC-007` | FR-021, SC-007 | IX |
| T029-SR-012 | `XCOM-SW-STIM-005/008` | `XCOM-SYS-FR-019/034` | FR-019, FR-034 | IX |
| T029-SR-013 | `XCOM-SW-STIM-003` | `XCOM-SYS-FR-017` | FR-017 | IX |
| T029-SR-014 | `XCOM-SW-STIM-003` | `XCOM-SYS-FR-017/SC-006` | FR-017, SC-006 | IX |
| T029-SR-015 | `XCOM-SW-STIM-003` | `XCOM-SYS-FR-017` | FR-017 | IX |
| T029-SR-016 | `XCOM-SW-STIM-008` | `XCOM-SYS-FR-034` | FR-034 | IX |
| T029-SR-017 | `XCOM-SW-STIM-008` | `XCOM-SYS-FR-033/034` | FR-033, FR-034 | IX |
| T029-SR-018 | `XCOM-SW-STIM-006/009` | `XCOM-SYS-FR-020/SC-007` | FR-020, SC-007 | IX |
| T029-SR-019 | `XCOM-SW-STIM-009` | `XCOM-SYS-SC-007` | SC-007 | IX |
| T029-SR-020 | `XCOM-SW-STIM-008/009` | `XCOM-SYS-FR-007/014` | FR-007, FR-014 | V, IX |
| T029-SR-021 | `XCOM-SW-STIM-006/009` | `XCOM-SYS-FR-025` | FR-025 | IX |
| T029-SR-022 | `XCOM-SW-STIM-009` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | II, VII, IX |
| T029-SR-023 | public-safe evidence rule | `XCOM-SYS-FR-027` | FR-027 | X |
| T029-SR-024 | Constitution; ADR-0020 | `XCOM-SYS-FR-030/035` | FR-030, FR-035 | VII, IX |
| T029-SR-025 | ADR-0020 | `XCOM-SYS-FR-030` | FR-030 | X |

`XCOM-SW-STIM-003` and `XCOM-SW-STIM-009` are accepted capability-007 software requirements
(`docs/engineering/xcom/t008/requirements-register.{json,md}`). They are accepted text; T029 verifies them and
does not rewrite them. The register rows are not changed and no register maturity is promoted by the plan stage;
the per-task maturity projection is recorded in the T029 work products, following the T026/T027/T028 precedent.

## 6. REF-002 disposition

T029 owns no REF-002 SADS ID and promotes none. It contributes verification evidence toward the allocated
communication IDs already exercised by the stimulation boundary: `XVE-SYS-0147` (bounded queueing/overflow and
explicit failure), `XVE-SYS-0149` (deterministic diagnostics), and the bounded-failure portion of `XVE-SYS-0158`
(deferred automatic recovery; capability 007 defines the bounded failure outcome and the evidence-incomplete
disposition). It promotes nothing, and the capability `ref002.disposition` stays `unchanged` with an empty
`promoted` list (T029-SR-024). No allocated, deferred, architectural-target, or superseded SADS requirement is
reported as implemented.

## 7. Affected paths

### 7.1 Paths the T029 candidate changes (implementation stage)

| Path | Change | Notes |
| --- | --- | --- |
| `tests/xcom/stimulation_matrix/test_support.hpp` | add | bounded owned fixture harness (permit/session, policy, fault-injectable journal storage, registry, action path, recording/fault-injectable emitter, observation bridge) |
| `tests/xcom/stimulation_matrix/permit_action_matrix_tests.cpp` | add | T29-TS-001…T29-TS-005 |
| `tests/xcom/stimulation_matrix/journal_recovery_tests.cpp` | add | T29-TS-006…T29-TS-010 |
| `tests/xcom/stimulation_matrix/zero_emission_tests.cpp` | add | T29-TS-011 |
| `tests/xcom/stimulation_matrix/provenance_tests.cpp` | add | T29-TS-012…T29-TS-015 |
| `tests/xcom/stimulation_matrix/lease_drain_tests.cpp` | add | T29-TS-016…T29-TS-018 |
| `tests/xcom/stimulation_matrix/concurrency_tests.cpp` | add | T29-TS-019, T29-TS-020 |
| `src/xverse/xcom/CMakeLists.txt` | edit | register six additive `xverse_xcom_stimulation_matrix_<kind>_tests` executables with `t029-<kind>` labels; no runtime-target inventory change |
| `engineering/trace/links.json` | edit | refresh the inherited `T020-L-046` `implemented_by` target digest for the new `src/xverse/xcom/CMakeLists.txt` content digest |
| `engineering/stage-results/{documentation,implementation,integration,internal-review}.json` | edit | refresh the inherited artifact digests for `engineering/trace/links.json` and `src/xverse/xcom/CMakeLists.txt` |
| `docs/engineering/xcom/t029/requirements.md` | add | this document |
| `docs/engineering/xcom/t029/architecture.md` | add | T029 architecture |
| `docs/engineering/xcom/t029/detailed-design.md` | add | T029 detailed design |
| `docs/engineering/xcom/t029/unit-specifications.md` | add | T029 unit specifications |
| `docs/engineering/xcom/t029/verification-plan.md` | add | T029 verification plan |
| `docs/engineering/xcom/t029/implementation.md` | add | implementation-stage record |
| `docs/engineering/xcom/t029/internal-review.json` | add | internal-review record |
| `specs/007-xcom-core/tasks.md` | edit | one-line T029 checkbox, **implementation stage only** |
| `reports/xcom-queue/t029-package.json` | add | implementation-stage package record |

### 7.2 Consumed read-only (not changed by T029)

`src/xverse/xcom/include/xverse/xcom/stimulation_actions.hpp`,
`src/xverse/xcom/src/stimulation_actions.cpp`, `tests/xcom/stimulation_actions/**`,
`src/xverse/xcom/include/xverse/xcom/stimulation_guard.hpp`,
`src/xverse/xcom/src/stimulation_guard.cpp`, `tests/xcom/stimulation_guard/**`,
`src/xverse/xcom/include/xverse/xcom/stimulation_journal.hpp`,
`src/xverse/xcom/src/stimulation_journal.cpp`, `tests/xcom/stimulation_journal/**`,
`src/xverse/xcom/include/xverse/xcom/validation_session.hpp`,
`src/xverse/xcom/src/validation_session.cpp`, `tests/xcom/validation_session/**`,
all accepted T-CORE headers (`contract.hpp`, `result.hpp`, `value.hpp`, `core_types.hpp`, `item.hpp`,
`diagnostic.hpp`, `endpoint_route_lifecycle.hpp`, `provider.hpp`, `loopback_provider.hpp`) and the accepted
observation header `observation.hpp` and `tests/xcom/observation/**`,
`docs/engineering/xcom/task-ownership.*`, `docs/engineering/xcom/t008/**`, `docs/engineering/xcom/t009/**`,
`docs/engineering/xcom/t010/**`, `specs/007-xcom-core/**` (other than the checkbox), `xdl/**`,
`cmake/XComOfflineDependencies.cmake`, `cmake/XComWarnings.cmake`, and the root `CMakeLists.txt`.

### 7.3 Explicitly not implemented by T029

`proto/xverse/xcom/v1/tool_gateway.proto` and the gateway (T030–T031), the separate-process synthetic client
(T032), the reusable contract suites and second synthetic provider (T033–T034), and the
benchmark/sanitizer/static/Doxygen/delivery tasks (T035–T040). External Codex review and user acceptance remain
T039/T041 and are deferred until the ordered backlog `xcom-t026-t029-20260928` completes.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- **T029-GAP-01 — test-only boundary.** T029 changes tests and the shared build file only. It proves the matrix at
  the in-process stimulation boundary and the accepted provider/observation boundary; it establishes no runtime,
  transport, gateway, compatibility, parity, or production-readiness claim.
- **T029-GAP-02 — fixture identity projection is test-declared.** The bridging fixture projects the accepted T026
  numeric intent identity onto the accepted T-CORE string identity vocabulary with a bounded, declared encoding
  (zero-padded decimal), because no canonical production numeric-to-item identity projection is accepted yet. The
  routed/observed provenance proof at the gateway/IPC boundary and any canonical projection remain T032/T033.
- **T029-GAP-03 — targeted fault injection, not a crash test.** The restart case reopens the accepted journal over
  the same durable bytes at a clean call boundary; crash consistency, media-failure atomicity, and torn-write
  recovery under process kill remain T026's own failure matrix and are not re-proven here.
- **T029-GAP-04 — single-process, single-writer.** Every case is single-process; multi-process lease arbitration
  and distributed scheduling are neither supported nor claimed.
- **T029-GAP-05 — no reusable abstraction.** The fixture is T029-local and is not the T033 reusable
  provider/observer/stimulation-tool/gateway contract suite.
- **T029-GAP-06 — no timing guarantees.** Concurrency cases assert bounded counts and deterministic outcomes, not
  latency, throughput, or real-time behaviour; those remain T036.

### 8.2 Gaps with owning tasks

| Gap | Owner |
| --- | --- |
| Local tool gateway and versioned Protocol Buffers/gRPC contract | T030–T032 |
| Reusable contract suites and second synthetic provider | T033/T034 |
| Executed sanitizer/static/Doxygen/benchmark and delivery bundle | T035–T040 |
| Independent review and user acceptance | T039/T041 |

### 8.3 Open items

- **T029-OPEN-01 — inherited provenance refresh.** Editing `src/xverse/xcom/CMakeLists.txt` invalidates the
  inherited `T020-L-046` `implemented_by` target digest in `engineering/trace/links.json` and the declared
  `links.json`/`CMakeLists.txt` digests in `engineering/stage-results/*.json`. Following the T026/T027/T028
  precedent, the implementation stage refreshes those inherited digests; no requirement, link identity, relation,
  or stage result changes. The exact digests are recorded in the implementation record.
- **T029-OPEN-02 — optional test-local scratch path.** If the restart case reuses a local file path, the case
  receives a bounded, git-ignored, build-time test-local scratch directory and never prints it into public
  evidence. The in-memory storage seam is the default so that no path is required.
- **T029-OPEN-03 — observation bridge dependency.** The routed/observed provenance case links the accepted
  `xverse::xcom_provider_loopback` and `xverse::xcom_observation` targets read-only in the test executable only; it
  authors no observation or provider behaviour and changes no T-OBS byte.

## 9. Definition of done (requirements view)

T029 is done for a candidate revision when: every §4 requirement has at least one named check; the complete
permit/action mismatch matrix, journal-before-emission ordering and journal failure/recovery, zero emission after
every rejection, persistent synthetic provenance (descriptor, routed/observed, and restarted), unmapped clocks,
quotas, loop bounds, lease conflicts, drain/terminal behavior, and deterministic concurrency are proven by
deterministic tests; `XCOM-SW-STIM-009` and `XCOM-SW-STIM-003` are recorded implemented by T029 while
`XCOM-SW-STIM-005`/`-006`/`-008` remain implemented; no accepted requirement, test, ADR, contract, register, or
production byte is weakened; the register validators pass with REF-002 unchanged and nothing promoted; the
deterministic gate passes; and a separate DeepSeek internal review records its findings before any repair. This
does not constitute user acceptance, which remains T041.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary checks |
| --- | --- |
| T029-STK-001 | CHK-01, CHK-02, CHK-04 |
| T029-STK-002 | CHK-06, CHK-08, CHK-11, CHK-12, CHK-14, CHK-17, CHK-18 |
| T029-STK-003 | CHK-02, CHK-03, CHK-24 |
| T029-STK-004 | CHK-16, CHK-19, CHK-20, CHK-21 |
| T029-STK-005 | CHK-23, CHK-24 |
| T029-SR-001 | CHK-02, CHK-04 |
| T029-SR-002 | CHK-03, CHK-19 |
| T029-SR-003 | CHK-05, CHK-20 |
| T029-SR-004 | CHK-06, CHK-15 |
| T029-SR-005 | CHK-06 |
| T029-SR-006 | CHK-07, CHK-16 |
| T029-SR-007 | CHK-08 |
| T029-SR-008 | CHK-09 |
| T029-SR-009 | CHK-10 |
| T029-SR-010 | CHK-11 |
| T029-SR-011 | CHK-11, CHK-14 |
| T029-SR-012 | CHK-12 |
| T029-SR-013 | CHK-13 |
| T029-SR-014 | CHK-13 |
| T029-SR-015 | CHK-13 |
| T029-SR-016 | CHK-08, CHK-17 |
| T029-SR-017 | CHK-09, CHK-17 |
| T029-SR-018 | CHK-18 |
| T029-SR-019 | CHK-14, CHK-18 |
| T029-SR-020 | CHK-16 |
| T029-SR-021 | CHK-16, CHK-19 |
| T029-SR-022 | CHK-19, CHK-20 |
| T029-SR-023 | CHK-21 |
| T029-SR-024 | CHK-23 |
| T029-SR-025 | CHK-24 |
