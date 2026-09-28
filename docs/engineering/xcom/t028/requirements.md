# T028 Requirements — Guarded Injection, Service Invocation, and Exclusive Service-Emulation Lease

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T028 (capability 007, slice `T-STIM`) |
| Task title | Implement guarded signal/message injection, service invocation, and exclusive generation-bound service emulation, plus drain, close, revoke, expiry, and evidence-incomplete lifecycle completion |
| Stage / role | plan → requirements |
| Revision | 1 (guarded actions and exclusive service-emulation lease) |
| Baseline revision | `c518c5e4fcb2055666db25cb62018769e7f56ae4` |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC006`, `ACC010`, `ACC011`, `ACC014`, `ACC015`); `ADR-0016` (subsystem naming); `ADR-0018` (platform-first); `ADR-0019` (stimulation ownership); `ADR-0020` (repository-owned work products and exact-candidate evidence) |
| Owning slice | `T-STIM` (T007 ownership register) |
| Predecessors | T025 — bounded time authority, immutable validation permit, and bounded session lifecycle (accepted at `4b01586b438a8587d231ee8828d896c206c06a96`, implementation `cc9044ab28d0ae9b4df8447072f68b73b3db184a`, consumed read-only); T026 — bounded durable stimulation intent/outcome journal (present at the baseline `c518c5e4fcb2055666db25cb62018769e7f56ae4`, consumed read-only); T027 — fail-closed pre-emission guard (present at the baseline, consumed read-only) |
| Producer dependencies | T011 admitted offline build envelope (read-only inputs); T012 subtree CMake/CTest contract and warning-as-error rule; T013/T-CORE immutable contract, item-origin, and diagnostic vocabulary (`xverse::xcom::OriginKind`, `xverse::xcom::InteractionKind`, `xverse::xcom::EndpointDirection`, consumed read-only); T025 `validation_session.hpp` in-process contract `XCOM-XLC-006`; T026 `stimulation_journal.hpp` intent/outcome/journal vocabulary (consumed read-only); T027 `stimulation_guard.hpp` decision vocabulary (consumed read-only) |
| Successor tasks | T029 (complete stimulation matrix), T030–T034 (gateway/conformance), T035–T041 (evidence, review, acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}` (`T-STIM` slice evidence names); `docs/engineering/xcom/t008/requirements-register.{json,md}` (`XCOM-SW-STIM-001`, `XCOM-SW-STIM-003`, `XCOM-SW-STIM-005`, `XCOM-SW-STIM-006`, `XCOM-SW-STIM-007`, `XCOM-SW-STIM-008`, `XCOM-SW-STIM-009`); `docs/engineering/xcom/t009/architecture-model.{json,md}` (`XCOM-CMP-009`, `XCOM-XB-007`, `XCOM-XLC-006`, `XCOM-INV-03`, `XCOM-INV-04`, `XCOM-INV-07`, `XCOM-INV-09`, `XCOM-INV-10`); `docs/engineering/xcom/t010/unit-design.{json,md}` (`XCOM-DU-018`) |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production
source or test change and does not implement, accept, or integrate the candidate. The T028 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T028 — Implement guarded signal/message injection, service invocation, and exclusive generation-bound
> service emulation, plus drain, close, revoke, expiry, and evidence-incomplete lifecycle completion.

### 1.1 Authority statement

This document specifies only the bounded T028 slice. It implements three accepted software requirements
from `docs/engineering/xcom/t008/requirements-register.{json,md}` that the register allocates to T028:

- `XCOM-SW-STIM-005` "Loop bounding and conflict rejection" — "Detect or bound prohibited reinjection loops
  and reject ambiguous or conflicting service emulation." (refines `XCOM-SYS-FR-019`, spec `FR-019`);
- `XCOM-SW-STIM-006` "Scheduling, clock authority, and tolerance" — "Declare a clock domain, ordering rule,
  late-item policy, and reproducibility limits for scheduled stimulation, label immediate injection as such,
  and fail or invalidate before emission when clock domains cannot be mapped within tolerance." (refines
  `XCOM-SYS-FR-020`, `XCOM-SYS-FR-033`, spec `FR-020`/`FR-033`); and
- `XCOM-SW-STIM-008` "Exclusive service-emulation lease" — "Atomically acquire an exclusive lease bound to
  the exact session and endpoint generation and release or quarantine it on conflict, expiry, revocation, or
  disconnect without ambiguous ownership." (refines `XCOM-SYS-FR-034`, spec `FR-034`).

It contributes evidence toward two further accepted requirements whose remaining maturity is owned
elsewhere:

- `XCOM-SW-STIM-003` "Persistent synthetic provenance" (owning task T026) — T028 supplies the bounded
  synthetic-origin classification and the tool/session/request/correlation/causal identity carried by an
  emitted item, and never relabels or drops it; the routed/restarted provenance proof remains T029; and
- `XCOM-SW-STIM-009` "Owned action conformance and lifecycle completion" (owning task T029) — T028
  implements the owned action kinds (signal injection, message injection, service invocation, bounded
  service emulation) and the drain/close/revoke/expiry/evidence-incomplete completion mechanics; the
  complete owned-fixture matrix remains T029.

It consumes the accepted design unit `XCOM-DU-018` "Guarded injection and exclusive service-emulation
lease" (component `XCOM-CMP-009` "Validation stimulation session", contract `XCOM-XLC-006`, boundary
`XCOM-XB-007`, family `STIM`, ownership `session-issued-handle`, lifetime `endpoint-generation`,
thread-safety `internally-synchronized`, bounds `active leases`/`drain deadline`/`drain queue depth` with
overflow `reject`/`fail-closed`), the accepted boundary `XCOM-XB-007` ("Fail-closed pre-emission guard;
rejection emits zero normal-route items", failure semantics "An unpermitted, expired, or revoked session
emits no normal-route item"), and the accepted safety/data-model invariants `XCOM-INV-03` (synthetic origin
survives routing and observation), `XCOM-INV-04` (one permitted service-emulation owner per endpoint and
session), `XCOM-INV-07` (every stimulation decision bound to the exact plan digest), `XCOM-INV-09`
(scheduled requests never compare or order unmapped clock domains), and `XCOM-INV-10` (one endpoint
generation, at most one active service-emulation lease).

It consumes the accepted T027 fail-closed pre-emission guard read-only and **does not** re-implement,
weaken, or replace its checks; the T028 action path evaluates the guard exactly once per declared request
and acts only on `GuardOutcome::Authorized`. It consumes the accepted T026 durable journal read-only to
obtain journal-before-emission ordering, explicit outcomes, and explicit evidence-incomplete surfacing; it
does not re-implement, weaken, or bypass the journal.

**Boundary honesty for `XCOM-SW-STIM-003` and `XCOM-SW-STIM-009`.** The register allocates
`synthetic-provenance` end-to-end and owned action conformance to T029. T028 implements the bounded
action kinds and completion mechanics and carries the synthetic classification and identity on the emitted
item, but it does not prove routing-to-observation provenance, restart reconciliation, or the complete
mismatch/quota/loop/lease/drain matrix. T028 records `XCOM-SW-STIM-003` and `XCOM-SW-STIM-009` as
**partial**, never `implemented`.

It does **not** redesign the accepted architecture, change a functional requirement, success criterion, ADR,
schema, XDL profile, or contract; modify `validation_session.hpp`/`.cpp`, `stimulation_journal.hpp`/`.cpp`,
or `stimulation_guard.hpp`/`.cpp` (accepted T025/T026/T027 bytes preserved); implement the tool gateway or
Protocol Buffers/gRPC (T030–T034); implement the complete stimulation matrix (T029); add an admitted
dependency; weaken an accepted requirement or test; or accept or integrate any candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, data
model, the T007 ownership register, the T008 register, the T009 architecture model, the T010 unit design,
the constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is
reported rather than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T028)

1. **New production unit.** Add one additive C++20 unit under `src/xverse/xcom/`:
   - `include/xverse/xcom/stimulation_actions.hpp` — the bounded guarded action path and the exclusive
     generation-bound service-emulation lease; and
   - `src/stimulation_actions.cpp` — its implementation.
   The unit is registered as one new runtime target `xverse_xcom_stimulation_actions` in the T012
   runtime-target inventory and routed through the existing warning-as-error rule. It changes no existing
   production header, source, or target behavior.
2. **Guarded action execution (`FR-015`, `FR-018`, `XCOM-SW-STIM-005`).** Provide one bounded API that
   executes each of the four declared action kinds — inject signal, inject message, invoke service,
   emulate service — **only** on a `GuardOutcome::Authorized` decision from the accepted T027 guard, and
   that maps every other guard decision to a non-emitting, non-journaling, non-mutating action result.
3. **Exclusive generation-bound service-emulation lease (`FR-034`, `XCOM-SW-STIM-008`, `XCOM-INV-04`,
   `XCOM-INV-10`).** Provide an atomically acquired exclusive lease bound to the exact session identity,
   endpoint identity, endpoint generation, and plan digest. A second owner for the same endpoint generation,
   or a lease request under a superseded/foreign generation or session, **shall** be rejected (`LeaseConflict`
   / `LeaseStatus::GenerationMismatch` / `LeaseStatus::SessionMismatch`) with no mutation and no emission.
4. **Loop bounding and conflict rejection (`FR-019`, `XCOM-SW-STIM-005`).** The action path **shall** reuse
   the accepted T027 guard's bounded loop window as the pre-emission bound and **shall** additionally bound
   the emission-time reinjection lineage: a request whose causal parent is already in the action path's
   bounded lineage returns `Rejected` with zero emission and zero journal, and an ambiguous or conflicting
   service-emulation declaration returns `LeaseConflict` with zero emission.
5. **Journal-before-emission ordering and explicit outcome (`FR-021`, `XCOM-SW-STIM-007`, consumed).** For
   every authorized action the action path **shall** journal the payload-free intent durably through the
   accepted T026 journal **before** invoking the emission seam exactly once, then record an explicit bounded
   outcome; an intent without a durable outcome **shall** be surfaced as `EvidenceIncomplete` and **shall
   never** be reported as success.
6. **Synthetic provenance (`FR-017`, `XCOM-SW-STIM-003` partial, `XCOM-INV-03`).** Every emitted item
   **shall** carry an explicit synthetic/tool-originated classification (`xverse::xcom::OriginKind::validation_tool`)
   and the exact tool, session, permit, plan, request, correlation, and causal identity, and the action path
   **shall never** relabel, drop, or infer that identity.
7. **Scheduling, ordering, late-item policy, and immediate labeling (`FR-020`, `FR-033`,
   `XCOM-SW-STIM-006`, `XCOM-INV-09`).** A scheduled action **shall** be placed in a bounded pending queue
   ordered by a declared ordering rule and completed by a bounded drain under a declared late-item policy;
   an immediate action **shall** be explicitly labeled and interpreted in the permit validity domain; a
   request whose clock domain cannot be resolved into the permit validity domain within the declared
   tolerance **shall** fail closed before emission and before journaling intent.
8. **Exclusive ownership acquisition is atomic.** Lease acquisition **shall** be an atomic
   check-then-insert under one lease-table mutex, and a concurrently racing second owner **shall** observe
   exactly one winner and one conflicted loser for one endpoint generation.
9. **Drain, close, revoke, expiry, and evidence-incomplete completion (`XCOM-SW-STIM-009` partial).** The
   action path **shall** provide bounded completion operations: `drain` (complete due pending actions under
   the declared ordering rule and late-item policy within a bounded step budget), `close` (drain then release
   every held lease), `revoke` and `expire` (cancel every pending action with zero emission and release or
   quarantine every held lease), and `mark_evidence_incomplete` (surface every intent without a durable
   outcome explicitly and never convert it to success). Completion **shall** be deterministic, bounded, and
   free of wall-clock dependence.
10. **Non-mutation and zero emission on rejection.** A non-`Authorized` decision, a lease conflict, a
    late rejection, a cancelled pending action, an over-capacity fail-closed, and every fail-closed
    precondition **shall** leave the accepted guard state, the lease table, the pending queue, the lineage
    window, and the durable journal unchanged in the rejected dimension, and **shall** emit no normal-route
    item.
11. **Determinism and diagnostics.** Action statuses, lease statuses, lease states, ordering rules,
    late-item policies, drain states, and completion outcomes **shall** be closed, enumerable,
    deterministically ordered vocabularies with stable names and precedence; the same bounded operation
    sequence **shall** produce the same action status, lease state, completion outcome, and snapshot across
    repeated runs and builds.
12. **Bounded tests.** Add additive GoogleTest suites under `tests/xcom/stimulation_actions/` covering the
    four nominal action kinds, the journal-before-emission ordering, the exclusive lease acquire/release/
    quarantine/expire matrix and generation/session binding, the loop/late-item/unmapped-clock fail-closed
    cases, the drain/close/revoke/expiry/evidence-incomplete completion matrix, the zero-mutation/zero-emission
    negative cases, the bounded-configuration matrix, and a bounded deterministic-concurrency check. The
    suites reuse the already admitted GTest prefix; no new dependency is admitted.
13. The T028 repository-owned work products and the T028 package record.

### 2.2 Explicit exclusions (must remain absent from the T028 candidate)

No tool gateway, Protocol Buffers/gRPC, IPC, TCP listener, or separate process (T030–T034); no modification
of `validation_session.hpp`/`.cpp`, `stimulation_journal.hpp`/`.cpp`, or `stimulation_guard.hpp`/`.cpp`;
no re-implementation, weakening, or bypass of the accepted guard or journal; no payload/value-body logging,
payload decoder, redaction profile, or unrestricted log; no observation tap, route, provider, endpoint, or
routed normal-route item authored by T028 (the emission seam is host-supplied and the accepted provider
boundary owns transport); no change to any existing test, target, test name, label, command, or expected
value (additive only); no new admitted dependency; no network, socket, DNS, TLS, ambient/secret,
dynamic-load, or legacy-repository/binary access; no process execution; no wall-clock-dependent verdict;
no time-authority mutation by the action path (it consumes a caller-resolved time); no benchmark,
sanitizer/static/Doxygen *execution*, or delivery bundle (T035–T040); no rewrite or weakening of an
accepted ADR, requirement, contract, schema, register, or test; no promotion of any REF-002 or capability
requirement beyond its recorded disposition; no acceptance or integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T028 |
| --- | --- | --- |
| Complete permit/action mismatch, quota, loop, lease, drain, unmapped-clock, zero-emission end-to-end matrix | T029 | allocated; T028 tests the behaviour it implements, T029 closes the cross-cutting matrix |
| Routed/restarted synthetic provenance proof through observation | T029/`XCOM-DU-014` | allocated; T028 carries the classification and identity only |
| Local tool gateway and versioned Protocol Buffers/gRPC contract | T030–T034 | allocated |
| Executed sanitizer/static-analysis/Doxygen evidence, benchmarks, integration, delivery bundle | T035–T040 | allocated |
| Independent review and user acceptance | T039/T041 | allocated |

## 3. Stakeholder requirements (`T028-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T028-STK-001**: Before the stimulation action paths are accepted, the program **shall** have a
  repository-owned, bounded, domain-neutral, offline guarded action path and exclusive service-emulation
  lease, physically under `src/xverse/xcom/` with tests under `tests/xcom/stimulation_actions/`, that
  execute signal injection, message injection, service invocation, and bounded service emulation only on an
  authorized pre-emission decision, offline under the T011-admitted toolchain and the T012 warning-as-error
  contract.
- **T028-STK-002**: Every non-authorized decision, lease conflict, late rejection, cancelled action, and
  fail-closed precondition **shall** mutate no operational state and **shall** emit zero normal-route items;
  an action that cannot be completed **shall** be surfaced explicitly and **shall never** be reported as
  success.
- **T028-STK-003**: T028 **shall** preserve accepted intent: the delivered change is confined to the T028
  source paths, its tests, the shared build files, the T028 work products, and the capability task ledger,
  and it **shall** neither modify accepted T025/T026/T027 bytes, weaken an accepted requirement or test, nor
  implement another task.
- **T028-STK-004**: The action path **shall** be offline, local-only, bounded, and deterministic: every
  record, table, queue, lease, thread, and iteration is finite and declared; it performs no network, socket,
  ambient configuration, secret, dynamic-load, process, or legacy access, adds no domain-specific primitive,
  and adds no new admitted dependency.
- **T028-STK-005**: T028 **shall** report maturity honestly: `XCOM-SW-STIM-005`, `XCOM-SW-STIM-006`, and
  `XCOM-SW-STIM-008` are implemented by this task; `XCOM-SW-STIM-003` and `XCOM-SW-STIM-009` remain
  **partial** (T029 owns routed provenance and the complete matrix); the REF-002 disposition stays
  `unchanged` with an empty `promoted` list, and no requirement is promoted beyond its recorded disposition.

## 4. Software/engineering requirements (`T028-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Verified" means the repository-owned test exists, is deterministic, and passes at the recorded
candidate revision; it is not a production, compatibility, or end-to-end route claim.

### 4.1 Unit, build wiring, and dependency reuse

- **T028-SR-001 [ubiquitous]**: The action path and lease **shall** be a new, additive C++20 unit at
  `src/xverse/xcom/include/xverse/xcom/stimulation_actions.hpp` and
  `src/xverse/xcom/src/stimulation_actions.cpp`, exposed through one new runtime target
  `xverse_xcom_stimulation_actions` added to the T012 `XVERSE_XCOM_RUNTIME_TARGETS` inventory and routed
  through the inherited warning-as-error rule; it **shall** change no existing production header, source,
  or target behavior, and every existing test case, target, label, command, and expected value **shall** be
  preserved unchanged.
  - Refines: `XCOM-SW-STIM-008`; anchors `XCOM-SYS-FR-034`, `XCOM-SYS-FR-030`; FR-034, FR-030; ADR-0020;
    T012 subtree build contract.
  - Verification intent: changed-path and discovered-count comparison plus the full suite; CHK-02, CHK-04,
    CHK-18, NEG-01.
- **T028-SR-002 [ubiquitous]**: The unit **shall** depend only on the C++ standard library, the accepted
  T025 `validation_session.hpp` in-process contract (`XCOM-XLC-006`), the accepted T026
  `stimulation_journal.hpp` vocabulary, the accepted T027 `stimulation_guard.hpp` vocabulary, and the
  accepted T-CORE `contract.hpp`/`item.hpp`/`result.hpp` interaction, origin, and diagnostic vocabulary; it
  **shall** add no admitted dependency, no Protocol Buffers/gRPC, and **shall** redefine no identity,
  digest, diagnostic, interaction, origin, or action vocabulary where an accepted one exists.
  - Refines: `XCOM-SW-STIM-008`; anchors `XCOM-SYS-FR-034`, `XCOM-SYS-FR-026`; FR-034, FR-026;
    `XCOM-XLC-006`; Constitution II, VII.
  - Verification intent: include/link inspection and the offline build; CHK-03, CHK-19, NEG-02.

### 4.2 Closed vocabularies, bounded values, and payload safety

- **T028-SR-003 [ubiquitous]**: The unit **shall** expose closed, enumerable, deterministically ordered
  vocabularies: `ActionStatus` (one enumerator per bounded action outcome), `LeaseStatus` (one enumerator
  per bounded lease operation outcome), `LeaseState` (`None`/`Active`/`Released`/`Quarantined`/`Expired`),
  `OrderingRule`, `LateItemPolicy`, `DrainState`, `EmissionStatus`, and `CompletionOutcome`; it **shall**
  reuse the accepted T027 `StimulationAction`/`StimulationActionMask`/`GuardReason`/`GuardOutcome` and the
  accepted T026 `OutcomeKind`/`JournalStatus` and the accepted T-CORE `OriginKind` rather than redefining
  them, and stable precedence **shall** be declared.
  - Refines: `XCOM-SW-STIM-008`; anchors `XCOM-SYS-FR-034`, `XCOM-SYS-FR-025`; FR-034, FR-025;
    `XCOM-DU-018`.
  - Verification intent: vocabulary inspection and determinism cases; CHK-17, NEG-28.
- **T028-SR-004 [ubiquitous]**: The unit's bounded values (`ActionPathConfig`, `EndpointGeneration`,
  `EmulationLease`, `LeaseSnapshot`, `PendingAction`, `SyntheticStimulationItem`, `ActionDiagnostic`,
  `ActionPathSnapshot`, `CompletionReport`) **shall** carry no payload, value body, address, free-form text,
  or unbounded member; a declared per-action payload view **shall** be forwarded to the emission seam only
  and **shall** be retained, journaled, or logged by nothing; the pending queue, lease table, and lineage
  window **shall** be bounded by declared maxima; and a compile-time rule **shall** reject construction from
  a payload byte container or free-form text and **shall** bound each value's size.
  - Refines: `XCOM-SW-STIM-008`; anchors `XCOM-SYS-FR-034`, `XCOM-SYS-FR-027`; FR-034, FR-027;
    `XCOM-DU-018`.
  - Verification intent: field inspection and a non-vacuous compile-time negative assertion; CHK-05, CHK-20,
    NEG-03, NEG-05.

### 4.3 Guarded action execution and identity

- **T028-SR-005 [event-driven]**: When the action path executes a request, it **shall** first validate its
  own bounded preconditions (open guard, non-zero declared bounds, pending-queue and lease capacity where
  applicable, valid session state read-only from the accepted T025 session); a failed precondition **shall**
  return the matching `ActionStatus` and **shall** mutate no accepted guard state, lease, queue, lineage, or
  journal record.
  - Refines: `XCOM-SW-STIM-005`; anchors `XCOM-SYS-FR-019`, `XCOM-SYS-FR-018`; FR-018, FR-019;
    `XCOM-DU-018`.
  - Verification intent: precondition/configuration matrix; CHK-06, CHK-18, NEG-33, NEG-34.
- **T028-SR-006 [event-driven]**: When the action path evaluates a request against the accepted T027 guard,
  only a `GuardOutcome::Authorized` decision **shall** proceed; a `Rejected` or `Failed` decision **shall**
  return the matching non-emitting `ActionStatus` with the guard reason preserved, **shall** append no
  journal record, and **shall** acquire no lease.
  - Refines: `XCOM-SW-STIM-005`; anchors `XCOM-SYS-FR-019`, `XCOM-SYS-FR-018`; FR-018, FR-019;
    `XCOM-DU-018`, `XCOM-CMP-009`.
  - Verification intent: guard-decision mapping matrix; CHK-07, CHK-14, NEG-06, NEG-26, NEG-27.
- **T028-SR-007 [event-driven]**: For `InjectSignal`, `InjectMessage`, and `InvokeService`, an authorized
  request **shall** journal its payload-free intent through the accepted T026 journal before emission,
  invoke the emission seam exactly once, record an explicit outcome, and return `ActionStatus::Emitted`
  only when the journal reports `Ok` **and** the host emission reports `EmissionStatus::Delivered`; when the
  intent is durable but the outcome is not, the action path **shall** return
  `ActionStatus::EvidenceIncomplete` and **shall never** report `Emitted`; when the intent and outcome are
  durable but the host reports `Rejected` or `Unavailable`, the action path **shall** return the distinct
  non-success `ActionStatus::EmissionRejected`/`EmissionUnavailable` and **shall never** report `Emitted`
  (`T028-STK-002`).
  - Refines: `XCOM-SW-STIM-005`, `XCOM-SW-STIM-006`; anchors `XCOM-SYS-FR-019`, `XCOM-SYS-FR-021`;
    FR-019, FR-021; `XCOM-DU-018`.
  - Verification intent: nominal action and evidence-incomplete cases; CHK-08, CHK-15, CHK-16, NEG-07,
    NEG-25.
- **T028-SR-008 [event-driven]**: Every emitted item **shall** carry `OriginKind::validation_tool`
  together with the exact tool tag, permit identity, session identity, plan digest, request identity,
  correlation identity, and causal identity bound into the durable intent, and the action path **shall**
  expose no path that emits an item with a different or absent synthetic classification.
  - Refines: `XCOM-SW-STIM-003` (partial); anchors `XCOM-SYS-FR-017`; FR-017; `XCOM-INV-03`.
  - Verification intent: synthetic-provenance field inspection and emission capture; CHK-09, NEG-08.

### 4.4 Exclusive generation-bound service-emulation lease

- **T028-SR-009 [event-driven]**: A service-emulation request **shall** acquire an exclusive lease bound to
  the exact session identity, endpoint identity, endpoint generation, and plan digest before emission; a
  missing, foreign, or mismatched identity **shall** be rejected (`LeaseStatus::SessionMismatch` /
  `GenerationMismatch` / `PlanMismatch`) with no mutation and no emission.
  - Refines: `XCOM-SW-STIM-008`; anchors `XCOM-SYS-FR-034`; FR-034; `XCOM-INV-04`, `XCOM-INV-10`;
    `XCOM-DU-018`.
  - Verification intent: lease identity/binding matrix; CHK-10, NEG-09, NEG-10.
- **T028-SR-010 [event-driven]**: Lease acquisition **shall** be an atomic check-then-insert under one
  lease-table mutex; a conflicting second owner for the same endpoint generation or the same
  `(endpoint, session)` **shall** be rejected (`LeaseStatus::Conflict`) with no mutation, and a concurrent
  race **shall** produce exactly one winner and one conflicted loser.
  - Refines: `XCOM-SW-STIM-008`; anchors `XCOM-SYS-FR-034`, `XCOM-SYS-FR-014`; FR-014, FR-034;
    `XCOM-INV-04`, `XCOM-INV-10`; `XCOM-DU-018`.
  - Verification intent: conflict matrix and the bounded concurrent-race case; CHK-11, CHK-18, NEG-11,
    NEG-29.
- **T028-SR-011 [event-driven]**: A held lease **shall** be releasable by its exact owner and **shall** be
  releasable by lifecycle completion; a release or quarantine by a non-owner, an unknown lease, or an
  already-released lease **shall** fail closed (`LeaseStatus::NotFound` / `NotHeld` / `AlreadyReleased`)
  with no mutation; on expiry, revocation, or disconnect the lease **shall** be released or quarantined
  without ambiguous ownership.
  - Refines: `XCOM-SW-STIM-008`; anchors `XCOM-SYS-FR-034`; FR-034; `XCOM-INV-04`; `XCOM-DU-018`.
  - Verification intent: release/quarantine/expiry matrix; CHK-12, NEG-12, NEG-13.
- **T028-SR-012 [event-driven]**: An elapsed lease (a caller-supplied `now >= expires_at` in the lease's
  declared clock domain) **shall** become inactive and **shall** no longer authorize or conflict-block; the
  action path **shall** compare only values in one declared domain and **shall** never compare or order two
  raw mismatched clock domains (`XCOM-INV-09`) and **shall** perform no time-authority mutation.
  - Refines: `XCOM-SW-STIM-008`, `XCOM-SW-STIM-006`; anchors `XCOM-SYS-FR-034`, `XCOM-SYS-FR-033`;
    FR-033, FR-034; `XCOM-INV-09`; `XCOM-DU-018`.
  - Verification intent: lease-expiry and unmapped-domain cases; CHK-13, NEG-14, NEG-23.

### 4.5 Loop bounding, scheduling, and lifecycle completion

- **T028-SR-013 [event-driven]**: The action path **shall** retain a bounded emission-time lineage window and
  **shall** reject a request whose causal parent is already present (`ActionStatus::Rejected`) with no
  emission and no journal; `causation_id == 0` **shall never** be a loop rejection; on emission the lineage
  **shall** advance under the declared depth bound without unbounded growth.
  - Refines: `XCOM-SW-STIM-005`; anchors `XCOM-SYS-FR-019`; FR-019; `XCOM-DU-018`.
  - Verification intent: reinjection and lineage-bound cases; CHK-14, NEG-15, NEG-16.
- **T028-SR-014 [event-driven]**: An authorized scheduled request **shall** be placed in a bounded pending
  queue ordered by the declared `OrderingRule`; `drain` **shall** complete due pending actions within a
  bounded step budget under the declared `LateItemPolicy`; a full queue **shall** fail closed
  (`ActionStatus::CapacityExhausted`) with no emission and no journal; a request that becomes late **shall**
  be rejected or discarded as declared, with zero emission.
  - Refines: `XCOM-SW-STIM-006`; anchors `XCOM-SYS-FR-020`; FR-020; `XCOM-DU-018`.
  - Verification intent: queue-bound, ordering, and late-policy cases; CHK-15, NEG-17, NEG-18.
- **T028-SR-015 [event-driven]**: An immediate request **shall** be explicitly labeled and interpreted in
  the permit validity domain; a scheduled request whose clock domain cannot be resolved into the permit
  validity domain, or whose resolved time lies outside the declared tolerance, **shall** fail closed before
  emission and before journaling intent; the action path **shall** consume a caller-resolved time and
  **shall** call no time authority.
  - Refines: `XCOM-SW-STIM-006`; anchors `XCOM-SYS-FR-020`, `XCOM-SYS-FR-033`; FR-020, FR-033;
    `XCOM-INV-09`; `XCOM-DU-018`.
  - Verification intent: immediate-labeling and unmapped-tolerance cases; CHK-13, CHK-19, NEG-19, NEG-23,
    NEG-24.
- **T028-SR-016 [event-driven]**: `drain` **shall** complete due pending actions in deterministic order
  within the bounded step budget; `close` **shall** drain then release every held lease; `revoke` and
  `expire` **shall** cancel every pending action with zero emission and release or quarantine every held
  lease; `mark_evidence_incomplete` **shall** surface every intent without a durable outcome explicitly;
  each completion operation **shall** return a bounded, deterministic `CompletionReport`; and a due,
  previously authorized pending action that cannot be completed (a failed intent append or a non-delivered
  host emission) **shall** be surfaced in that report (`CompletionReport.failed`) and **shall never** be
  reported as a clean `Drained`/`Closed` while a due action was dropped without a durable intent.
  - Refines: `XCOM-SW-STIM-009` (partial); anchors `XCOM-SYS-SC-007`; SC-007; `XCOM-DU-018`.
  - Verification intent: drain/close/revoke/expiry/evidence-incomplete matrix; CHK-16, NEG-20, NEG-21,
    NEG-22.

### 4.6 Non-mutation, determinism, and safety

- **T028-SR-017 [unwanted]**: If any precondition, guard, lease, journal, late-policy, or completion
  decision declines, the action path **shall** mutate no accepted guard state, no lease-table entry, no
  pending-queue entry, no lineage entry, and no durable journal record in the declined dimension, **shall**
  return an explicit bounded status, and **shall** emit no normal-route item; a declined action **shall
  never** return `Emitted`.
  - Refines: `XCOM-SW-STIM-005`, `XCOM-SW-STIM-008`; anchors `XCOM-SYS-FR-019`, `XCOM-SYS-FR-034`;
    FR-019, FR-034; `XCOM-XB-007`; `XCOM-DU-018`.
  - Verification intent: zero-mutation snapshot comparison and no-emission inspection; CHK-21, NEG-25,
    NEG-26, NEG-27.
- **T028-SR-018 [ubiquitous]**: The same bounded operation sequence **shall** produce the same action status,
  the same lease state, the same completion outcome, and the same snapshot across repeated runs and builds;
  precedence and ordering rules **shall** be stable and declared.
  - Refines: `XCOM-SW-STIM-006`; anchors `XCOM-SYS-FR-025`; FR-025; `XCOM-DU-018`.
  - Verification intent: repeated-run equality and precedence cases; CHK-17, NEG-28.
- **T028-SR-019 [ubiquitous]**: The action path and lease **shall** serialize their state under one mutex
  each, **shall** invoke no host callback under a lock, and the tests **shall** use only a bounded, finite
  thread and iteration count with no wall-clock verdict; concurrent action execution, lease acquisition, and
  completion **shall** commit a deterministic total order and **shall never** exceed the declared queue,
  lease, quota, or lineage bounds or mutate state on a decline.
  - Refines: `XCOM-SW-STIM-008`; anchors `XCOM-SYS-FR-014`, `XCOM-SYS-FR-007`; FR-007, FR-014;
    `XCOM-DU-018` `internally-synchronized`.
  - Verification intent: bounded deterministic-concurrency and concurrent-conflict cases; CHK-18, NEG-29,
    NEG-36.
- **T028-SR-020 [ubiquitous]**: The unit **shall** be local-only and offline: it **shall** perform no file,
  network, socket, resolver, TLS, ambient-configuration, secret, dynamic-load, subprocess, or
  legacy-repository/binary access, **shall** own no I/O boundary, **shall** retain or log no payload byte,
  and **shall** add no domain-specific primitive.
  - Refines: `XCOM-SW-STIM-008`; anchors `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028`; FR-026, FR-028; ADR-0019;
    Constitution II, VII; `XCOM-INV-13`, `XCOM-INV-15`.
  - Verification intent: forbidden-API source scan, no-I/O and no-payload-retention inspection, and the
    offline build; CHK-19, CHK-20, NEG-30.
- **T028-SR-021 [ubiquitous]**: Committed source, tests, work products, and evidence **shall** contain no
  credential, private address, unrestricted or real payload, proprietary source excerpt,
  environment-specific absolute host path, or sensitive deployment value.
  - Refines: Constitution X; anchors `XCOM-SYS-FR-027`; FR-027; public-safe evidence rule.
  - Verification intent: public-safety scan; CHK-21, NEG-31.
- **T028-SR-022 [ubiquitous]**: Every new public C++ declaration **shall** carry useful Doxygen
  documentation including ownership, lifetime, thread-safety, and failure contract, and the header file
  block **shall** name T028 and `\ingroup xcom_stim`; the admitted repository documentation configuration
  **shall** be unchanged.
  - Refines: `XCOM-SW-STIM-008`; anchors `XCOM-SYS-FR-029`; FR-029; `XCOM-DU-018` Doxygen obligation;
    Constitution X.
  - Verification intent: declaration inspection and the existing documentation configuration check;
    CHK-22.
- **T028-SR-023 [ubiquitous]**: T028 **shall** reconcile with the T007 ownership register, the T008
  requirement register, the T009 architecture model, and the T010 unit design without rewriting or
  weakening them; **shall** keep the REF-002 disposition `unchanged` with an empty `promoted` list; and
  **shall** record honestly that `XCOM-SW-STIM-005`, `XCOM-SW-STIM-006`, and `XCOM-SW-STIM-008` are
  implemented by this task, that `XCOM-SW-STIM-003` and `XCOM-SW-STIM-009` remain **partial** (T029 owns
  routed provenance and the complete matrix), and that T029–T041 remain allocated.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-035`, `XCOM-SYS-FR-030`; FR-030, FR-035; Constitution VII, IX.
  - Verification intent: register validators plus the recorded-maturity inspection; CHK-23, NEG-32.
- **T028-SR-024 [ubiquitous]**: The T028 candidate **shall** satisfy the deterministic Fabro gate for an
  implementation task: the six named work products exist, at least one `src/xverse/xcom/` path and at least
  one `tests/` path change, `cmake` configure, build, discovery, and the full `ctest` suite pass, and
  `git diff --check` is clean; the T028 checkbox is marked complete **only** in the implementation stage.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-030`; FR-030; Constitution X.
  - Verification intent: `xcom_feature_gate.py verify T028 <baseline>`; `git diff --check`; CHK-24,
    NEG-32.

## 5. Requirement-to-accepted-anchor traceability

| T028 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T028-STK-001 | `XCOM-SW-STIM-008` | `XCOM-SYS-FR-034` | FR-034 | IX, X |
| T028-STK-002 | `XCOM-SW-STIM-005` | `XCOM-SYS-FR-019` | FR-019 | IX |
| T028-STK-003 | Constitution VII/IX; ADR-0020 | `XCOM-SYS-FR-030` | FR-030 | VII, IX, X |
| T028-STK-004 | `XCOM-SW-STIM-008` | `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028` | FR-026, FR-028 | II, VII, IX |
| T028-STK-005 | ADR-0020 | `XCOM-SYS-FR-035` | FR-035 | VII, IX |
| T028-SR-001 | `XCOM-SW-STIM-008` | `XCOM-SYS-FR-034/030` | FR-034, FR-030 | VII, X |
| T028-SR-002 | `XCOM-SW-STIM-008` | `XCOM-SYS-FR-034/026` | FR-034, FR-026 | II, VII |
| T028-SR-003 | `XCOM-SW-STIM-008` | `XCOM-SYS-FR-034/025` | FR-034, FR-025 | IX |
| T028-SR-004 | `XCOM-SW-STIM-008` | `XCOM-SYS-FR-034/027` | FR-034, FR-027 | IX, X |
| T028-SR-005 | `XCOM-SW-STIM-005` | `XCOM-SYS-FR-018/019` | FR-018, FR-019 | IX |
| T028-SR-006 | `XCOM-SW-STIM-005` | `XCOM-SYS-FR-018/019` | FR-018, FR-019 | IX |
| T028-SR-007 | `XCOM-SW-STIM-005/006` | `XCOM-SYS-FR-019/021` | FR-019, FR-021 | IX |
| T028-SR-008 | `XCOM-SW-STIM-003` (partial) | `XCOM-SYS-FR-017` | FR-017 | IX |
| T028-SR-009 | `XCOM-SW-STIM-008` | `XCOM-SYS-FR-034` | FR-034 | IX |
| T028-SR-010 | `XCOM-SW-STIM-008` | `XCOM-SYS-FR-014/034` | FR-014, FR-034 | V, IX |
| T028-SR-011 | `XCOM-SW-STIM-008` | `XCOM-SYS-FR-034` | FR-034 | IX |
| T028-SR-012 | `XCOM-SW-STIM-006/008` | `XCOM-SYS-FR-033/034` | FR-033, FR-034 | IX |
| T028-SR-013 | `XCOM-SW-STIM-005` | `XCOM-SYS-FR-019` | FR-019 | IX |
| T028-SR-014 | `XCOM-SW-STIM-006` | `XCOM-SYS-FR-020` | FR-020 | IX |
| T028-SR-015 | `XCOM-SW-STIM-006` | `XCOM-SYS-FR-020/033` | FR-020, FR-033 | IX |
| T028-SR-016 | `XCOM-SW-STIM-009` (partial) | `XCOM-SYS-SC-007` | SC-007 | IX |
| T028-SR-017 | `XCOM-SW-STIM-005/008` | `XCOM-SYS-FR-019/034` | FR-019, FR-034 | IX |
| T028-SR-018 | `XCOM-SW-STIM-006` | `XCOM-SYS-FR-025` | FR-025 | IX |
| T028-SR-019 | `XCOM-SW-STIM-008` | `XCOM-SYS-FR-007/014` | FR-007, FR-014 | V, IX |
| T028-SR-020 | `XCOM-SW-STIM-008` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | II, VII, IX |
| T028-SR-021 | public-safe evidence rule | `XCOM-SYS-FR-027` | FR-027 | X |
| T028-SR-022 | `XCOM-SW-STIM-008` Doxygen | `XCOM-SYS-FR-029` | FR-029 | X |
| T028-SR-023 | Constitution; ADR-0020 | `XCOM-SYS-FR-030/035` | FR-030, FR-035 | VII, IX |
| T028-SR-024 | ADR-0020 | `XCOM-SYS-FR-030` | FR-030 | X |

`XCOM-SW-STIM-005`, `XCOM-SW-STIM-006`, and `XCOM-SW-STIM-008` are accepted capability-007 software
requirements (`docs/engineering/xcom/t008/requirements-register.{json,md}`). They are accepted text; T028
refines and consumes them and does not rewrite them. `XCOM-SW-STIM-003` and `XCOM-SW-STIM-009` are accepted
and remain owned by T026/T029 respectively with the T028 contribution recorded partial. No register row is
changed and no maturity is promoted; the per-task maturity projection is recorded in the T028 work products,
following the T026/T027 precedent.

## 6. REF-002 disposition

T028 owns no REF-002 SADS ID and promotes none. It provides evidence toward the allocated communication
IDs already exercised by the stimulation boundary: `XVE-SYS-0147` (bounded queueing/overflow and explicit
failure), `XVE-SYS-0149` (deterministic diagnostics and metrics), and the bounded-failure portion of
`XVE-SYS-0158` (deferred automatic recovery; capability 007 defines the bounded failure outcome and the
evidence-incomplete disposition). It promotes nothing, and the capability `ref002.disposition` stays
`unchanged` with an empty `promoted` list (T028-SR-023). No allocated, deferred, architectural-target, or
superseded SADS requirement is reported as implemented.

## 7. Affected paths

### 7.1 Paths the T028 candidate changes (implementation stage)

| Path | Change | Notes |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/stimulation_actions.hpp` | add | new public action-path and lease interface (vocabularies, bounded values, emitter seam, action path, registry) |
| `src/xverse/xcom/src/stimulation_actions.cpp` | add | implementation of the guarded action path, exclusive lease table, pending queue, lineage window, and completion operations |
| `src/xverse/xcom/CMakeLists.txt` | edit | add `xverse_xcom_stimulation_actions` to `XVERSE_XCOM_RUNTIME_TARGETS`; define the library; add the additive test targets and `t028-<kind>` labels |
| `tests/xcom/stimulation_actions/action_tests.cpp` | add | nominal action kinds, guard mapping, journal-before-emission, synthetic provenance, evidence-incomplete |
| `tests/xcom/stimulation_actions/lease_tests.cpp` | add | exclusive lease acquire/release/quarantine/expire, generation/session/plan binding, capacity, conflict matrix |
| `tests/xcom/stimulation_actions/lifecycle_tests.cpp` | add | drain/close/revoke/expiry/evidence-incomplete completion, pending bounds, ordering, late policy, immediate labeling |
| `tests/xcom/stimulation_actions/negative_tests.cpp` | add | zero-emission/zero-journal/zero-mutation negatives, closed/rejected configuration, payload-free declaration inspection |
| `tests/xcom/stimulation_actions/concurrency_tests.cpp` | add | bounded deterministic concurrency, lease race, quota bound, concurrent completion |
| `docs/engineering/xcom/t028/requirements.md` | add | this document |
| `docs/engineering/xcom/t028/architecture.md` | add | T028 architecture |
| `docs/engineering/xcom/t028/detailed-design.md` | add | T028 detailed design |
| `docs/engineering/xcom/t028/unit-specifications.md` | add | T028 unit specifications |
| `docs/engineering/xcom/t028/verification-plan.md` | add | T028 verification plan |
| `docs/engineering/xcom/t028/implementation.md` | add | implementation-stage record |
| `docs/engineering/xcom/t028/internal-review.json` | add | internal-review record |
| `specs/007-xcom-core/tasks.md` | edit | one-line T028 checkbox, **implementation stage only** |
| `reports/xcom-queue/t028-package.json` | add | implementation-stage package record |

A derived status projection of the `XCOM-DU-018` `artifact_paths` status field in
`docs/engineering/xcom/t010/unit-design.json` (from `planned` to `established`) with a regenerated
`docs/engineering/xcom/t010/design-units.md`, following the T026/T027 precedent, is expected at the
implementation stage and is recorded as `T028-OPEN-01`; it changes no unit identity, ownership, lifetime,
thread-safety, bound, failure semantics, planned evidence, or Doxygen obligation.

### 7.2 Consumed read-only (not changed by T028)

`src/xverse/xcom/include/xverse/xcom/validation_session.hpp`, `src/xverse/xcom/src/validation_session.cpp`,
`tests/xcom/validation_session/**`, `src/xverse/xcom/include/xverse/xcom/stimulation_journal.hpp`,
`src/xverse/xcom/src/stimulation_journal.cpp`, `tests/xcom/stimulation_journal/**`,
`src/xverse/xcom/include/xverse/xcom/stimulation_guard.hpp`, `src/xverse/xcom/src/stimulation_guard.cpp`,
`tests/xcom/stimulation_guard/**`, the accepted T-CORE headers (`contract.hpp`, `result.hpp`, `value.hpp`,
`core_types.hpp`, `item.hpp`, `diagnostic.hpp`, and the other accepted core headers),
`docs/engineering/xcom/task-ownership.*`, `docs/engineering/xcom/t008/**`,
`docs/engineering/xcom/t009/**`, `docs/engineering/xcom/t010/**` (other than the recorded derived status
projection), `specs/007-xcom-core/**` (other than the checkbox), `xdl/**`,
`cmake/XComOfflineDependencies.cmake`, `cmake/XComWarnings.cmake`, and the root `CMakeLists.txt`.

### 7.3 Explicitly not implemented by T028

`proto/xverse/xcom/v1/tool_gateway.proto` and the gateway (T030–T031), the separate-process synthetic
client (T032), the reusable contract suites (T033), the second synthetic provider (T034), and the
contract/benchmark/Doxygen/delivery tasks (T033–T041). The complete stimulation matrix and the
routed/restarted synthetic-provenance and owned-action-conformance evidence remain T029.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- **T028-GAP-01 — emission seam delegated.** T028 owns the guarded action path, the journal-before-emission
  ordering, the exclusive lease, and lifecycle completion, but the transport realization is a host-supplied
  `ActionEmitter` seam (analogous to the accepted T026 `Storage` seam) so that the accepted T-CORE provider/
  route boundary owns transport and T030–T034 owns the gateway. T028 authors no route, provider, endpoint,
  or routed item.
- **T028-GAP-02 — provenance partial.** `XCOM-SW-STIM-003` remains partial: T028 carries the synthetic
  classification and the exact identity on the emitted item, but the routed/restarted provenance proof
  through observation and the gateway is T029/T033.
- **T028-GAP-03 — conformance partial.** `XCOM-SW-STIM-009` remains partial: T028 implements and tests the
  four action kinds and the completion mechanics, but the complete owned-fixture conformance matrix is T029.
- **T028-GAP-04 — bound source versus `XCOM-DU-018`.** The accepted T010 `XCOM-DU-018` records the
  `drain deadline` and `drain queue depth` as "declared in validation permit", while the accepted T025
  `Permit` carries a `Quota` list only and no drain declaration. T028 therefore supplies a bounded
  `ActionPathConfig` (active-lease capacity, pending-queue depth, drain deadline/step budget, ordering rule,
  late-item policy, payload bound) cross-checked against the immutable permit validity; the delta is
  recorded as `T028-OPEN-01` rather than editing the accepted T010 artifact silently.
- **T028-GAP-05 — single-process, single-writer.** The action path and lease table are single-process and
  serialize one declared writer per instance; multi-process or distributed lease arbitration is not
  supported and is not claimed.
- **T028-GAP-06 — scheduling bounded.** Scheduled ordering is a declared bounded rule over caller-supplied
  resolved time; sub-tick jitter, real-time guarantees, and production timing behaviour are not claimed.

### 8.2 Gaps with owning tasks

| Gap | Owner |
| --- | --- |
| Complete permit/action, quota, loop, lease, drain, unmapped-clock, zero-emission end-to-end matrix | T029 |
| Routed/restarted synthetic provenance and owned-action conformance | T029 |
| Gateway, Protocol Buffers/gRPC, separate process | T030–T034 |
| Executed sanitizer/static/Doxygen/benchmark and delivery bundle | T035–T040 |
| Independent review and user acceptance | T039/T041 |

### 8.3 Open items

- **T028-OPEN-01 — bound source and public-element count versus `XCOM-DU-018`.** The accepted T010
  `XCOM-DU-018` records the active-lease capacity as declared in the activation plan, the drain deadline and
  drain queue depth as declared in the validation permit, and six documented/public elements. The accepted
  T025 `Permit` exposes neither an active-lease capacity nor a drain declaration. T028 supplies a bounded
  `ActionPathConfig` derived by the caller from the digest-bound plan and cross-checked against the permit,
  and adds the emission seam, the lease registry, and the completion report to the public surface. The
  implementation stage records the delta and the derived T010 `artifact_paths` status projection as a
  successor note rather than editing the accepted T010 artifact silently.
- **T028-OPEN-02 — emission seam and payload view.** T028 forwards an optional bounded payload view to the
  host `ActionEmitter` and never retains, journals, or logs it. The accepted observation policy for payload
  views and the gateway that will consume the emitter are T030–T034; T028 claims only the metadata-only
  action descriptor and the synthetic classification.
- **T028-OPEN-03 — time resolution responsibility.** The action path consumes a caller-resolved time value
  rather than calling the accepted `TimeAuthority` directly, so that a decline can never mutate the
  authority's regression baseline; the accepted authority remains the only time-mapping mechanism
  (`FR-033`), and the resolved-time wiring is completed by T029/T032.

## 9. Definition of done (requirements view)

T028 is done for a candidate revision when: every §4 requirement has at least one named check; the four
nominal action kinds, the guard-decision mapping, the journal-before-emission ordering, the exclusive
generation-bound lease acquire/release/quarantine/expire behaviour, the loop/late/unmapped-clock
fail-closed behaviours, the drain/close/revoke/expiry/evidence-incomplete completion, and the
zero-mutation/zero-emission-on-decline behaviour are proven by deterministic tests; `XCOM-SW-STIM-005`,
`XCOM-SW-STIM-006`, and `XCOM-SW-STIM-008` are recorded implemented and `XCOM-SW-STIM-003`/
`XCOM-SW-STIM-009` partial; no accepted requirement, test, ADR, contract, register, or T025/T026/T027 byte
is weakened; the register validators pass with REF-002 unchanged and nothing promoted; the deterministic
gate passes; and a separate DeepSeek internal review records its findings before any repair. This does not
constitute user acceptance.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary checks |
| --- | --- |
| T028-STK-001 | CHK-01, CHK-02, CHK-04 |
| T028-STK-002 | CHK-07, CHK-10, CHK-11, CHK-14, CHK-15, CHK-16, CHK-21 |
| T028-STK-003 | CHK-02, CHK-03, CHK-23 |
| T028-STK-004 | CHK-17, CHK-18, CHK-19, CHK-20, CHK-21 |
| T028-STK-005 | CHK-23, CHK-24 |
| T028-SR-001 | CHK-02, CHK-04, CHK-18 |
| T028-SR-002 | CHK-03, CHK-19 |
| T028-SR-003 | CHK-17, CHK-20 |
| T028-SR-004 | CHK-05, CHK-20 |
| T028-SR-005 | CHK-06, CHK-18 |
| T028-SR-006 | CHK-07, CHK-14 |
| T028-SR-007 | CHK-08, CHK-16 |
| T028-SR-008 | CHK-09 |
| T028-SR-009 | CHK-10 |
| T028-SR-010 | CHK-11, CHK-18 |
| T028-SR-011 | CHK-12 |
| T028-SR-012 | CHK-13 |
| T028-SR-013 | CHK-14 |
| T028-SR-014 | CHK-15 |
| T028-SR-015 | CHK-13, CHK-19 |
| T028-SR-016 | CHK-16 |
| T028-SR-017 | CHK-21 |
| T028-SR-018 | CHK-17 |
| T028-SR-019 | CHK-18 |
| T028-SR-020 | CHK-19, CHK-20 |
| T028-SR-021 | CHK-21 |
| T028-SR-022 | CHK-22 |
| T028-SR-023 | CHK-23 |
| T028-SR-024 | CHK-24 |
