# T027 Requirements — Fail-Closed Pre-Emission Guard

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T027 (capability 007, slice `T-STIM`) |
| Task title | Implement the fail-closed pre-emission guard for schema, target, direction, action, time, quota, loop, service ownership, permit/session identity, revocation, and expiry; rejection must not mutate operational state or emit a normal-route item |
| Stage / role | plan → requirements |
| Revision | 1 (fail-closed pre-emission guard) |
| Baseline revision | `bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f` |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC006`, `ACC010`, `ACC011`, `ACC014`, `ACC015`); `ADR-0016` (subsystem naming); `ADR-0018` (platform-first); `ADR-0019` (stimulation ownership); `ADR-0020` (repository-owned work products and exact-candidate evidence) |
| Owning slice | `T-STIM` (T007 ownership register) |
| Predecessors | T025 — bounded time authority, immutable validation permit, and bounded session lifecycle (accepted T025 at `4b01586b438a8587d231ee8828d896c206c06a96`, implementation `cc9044ab28d0ae9b4df8447072f68b73b3db184a`); T026 — bounded durable stimulation intent/outcome journal (present at the baseline `bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f`, consumed read-only) |
| Producer dependencies | T011 admitted offline build envelope (read-only inputs); T012 subtree CMake/CTest contract and warning-as-error rule; T013/T-CORE immutable contract and diagnostic vocabulary `xverse::xcom::InteractionKind`, `xverse::xcom::EndpointDirection` (consumed read-only); T025 `validation_session.hpp` in-process contract `XCOM-XLC-006` (`Permit`/`PermitId`/`SessionId`/`PlanDigest`/`Timestamp`/`ClockDomainId`/`Tag`/`Result`/`Diagnostic`/`LifecycleState`/`TimeAuthority`, consumed read-only) |
| Successor tasks | T028 (guarded injection/invocation/exclusive service emulation), T029 (full matrix and lifecycle completion), T030–T034 (gateway/conformance), T035–T041 (evidence, review, acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}` (`T-STIM` slice evidence names); `docs/engineering/xcom/t008/requirements-register.{json,md}` (`XCOM-SW-STIM-004`, `XCOM-SW-STIM-005`, `XCOM-SW-STIM-006`); `docs/engineering/xcom/t009/architecture-model.{json,md}` (`XCOM-CMP-009`, `XCOM-XB-007`, `XCOM-XLC-006`, `XCOM-INV-04`, `XCOM-INV-07`, `XCOM-INV-09`, `XCOM-INV-10`); `docs/engineering/xcom/t010/unit-design.{json,md}` (`XCOM-DU-017`) |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production
source or test change and does not implement, accept, or integrate the candidate. The T027 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T027 — Implement the fail-closed pre-emission guard for schema, target, direction, action, time, quota,
> loop, service ownership, permit/session identity, revocation, and expiry; rejection must not mutate
> operational state or emit a normal-route item.

### 1.1 Authority statement

This document specifies only the bounded T027 slice. It implements one accepted software requirement from
`docs/engineering/xcom/t008/requirements-register.{json,md}`:

- `XCOM-SW-STIM-004` "Fail-closed pre-emission validation" — "Validate every injected item against its
  declared interaction, direction, schema, target, session scope, and quota before it can enter a route."
  (refines `XCOM-SYS-FR-018`, spec `FR-018`).

It contributes evidence toward two further accepted requirements that the register allocates to T028:

- `XCOM-SW-STIM-005` "Loop bounding and conflict rejection" — "Detect or bound prohibited reinjection loops
  and reject ambiguous or conflicting service emulation." (refines `XCOM-SYS-FR-019`, spec `FR-019`); and
- `XCOM-SW-STIM-006` "Scheduling, clock authority, and tolerance" — "Declare a clock domain, ordering rule,
  late-item policy, and reproducibility limits for scheduled stimulation, label immediate injection as such,
  and fail or invalidate before emission when clock domains cannot be mapped within tolerance." (refines
  `XCOM-SYS-FR-020`, `XCOM-SYS-FR-033`, spec `FR-020`/`FR-033`).

It consumes the accepted design unit `XCOM-DU-017` "Fail-closed pre-emission guard" (component
`XCOM-CMP-009` "Validation stimulation session", contract `XCOM-XLC-006`, family `STIM`, ownership
`session-issued-handle`, lifetime `session-scoped`, thread-safety `internally-synchronized`, bounds
`loop-detection window`/`actions per session`/`actions per interval` with overflow `reject`/`fail-closed`),
the accepted boundary `XCOM-XB-007` ("Fail-closed pre-emission guard; rejection emits zero normal-route
items", failure semantics "An unpermitted, expired, or revoked session emits no normal-route item"), the
accepted safety invariants `XCOM-INV-04` (one permitted service-emulation owner per endpoint/session),
`XCOM-INV-07` (every stimulation decision bound to the exact plan digest), `XCOM-INV-09` (scheduled requests
never compare or order unmapped clock domains), and `XCOM-INV-10` (one endpoint generation, at most one
active service-emulation lease), and the accepted validation-tool contract
(`specs/007-xcom-core/contracts/validation-tool.md`): "The boundary rejects before emission when
authorization, plan digest, identity, schema, direction, action, time, quota, service ownership, or loop
policy fails. Rejection and unknown outcomes are evidence."

**Boundary honesty for `XCOM-SW-STIM-005` and `XCOM-SW-STIM-006`.** The register allocates both to T028.
T027 therefore implements only the **guard-level, declaration-time** portion: a bounded loop-detection
window that rejects a prohibited reinjection declaration with zero mutation, and a pre-emission time-policy
check that fails closed when a request clock domain cannot be resolved into the permit validity domain
within tolerance. The atomic exclusive service-emulation lease, the end-to-end reinjection-loop enforcement,
scheduled ordering/late-item behavior, and the full unmapped-clock/loop matrix remain **partial/allocated to
T028/T029**. T027 records `XCOM-SW-STIM-005` and `XCOM-SW-STIM-006` as **partial**, never `implemented`.

It does **not** redesign the accepted architecture, change a functional requirement, success criterion, ADR,
schema, XDL profile, or contract; implement injection, service invocation, or service emulation (T028); the
exclusive lease, drain, close, revoke, or expiry lifecycle completion (T028); the tool gateway or Protocol
Buffers/gRPC (T030–T034); an emission path, route, provider, endpoint, observation tap, or routed item;
modify `validation_session.hpp`/`.cpp` or `stimulation_journal.hpp`/`.cpp` (accepted T025/T026 bytes
preserved); add an admitted dependency; weaken an accepted requirement or test; or accept or integrate any
candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, data
model, the T007 ownership register, the T008 register, the T009 architecture model, the T010 unit design,
the constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is
reported rather than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T027)

1. **New production guard unit.** Add one additive C++20 unit under `src/xverse/xcom/`:
   - `include/xverse/xcom/stimulation_guard.hpp` — a bounded, payload-free, fail-closed pre-emission guard
     that evaluates one declared stimulation request against an immutable validation permit and a bounded
     declared stimulation policy; and
   - `src/stimulation_guard.cpp` — its implementation.
   The unit is registered as one new runtime target `xverse_xcom_stimulation_guard` in the T012
   runtime-target inventory and routed through the existing warning-as-error rule. It changes no existing
   production header, source, or target behavior.
2. **Deterministic fail-closed decision (`FR-018`, `XCOM-SW-STIM-004`).** Provide one bounded API that
   evaluates a declared request and returns exactly one of `Authorized`, `Rejected`, or `Failed` with a
   bounded, deterministic diagnostic and a closed reason vocabulary. Only `Authorized` may proceed to
   emission; every other decision proceeds to no emission.
3. **Permit/session identity and plan-digest binding.** A request whose session identity, permit identity,
   or plan digest does not match the bound immutable permit **shall** be rejected (`PermitMismatch`) before
   any state mutation, and every authorization **shall** be bound to the exact plan digest
   (`XCOM-INV-07`).
4. **Lifecycle revocation and expiry.** A revoked session **shall** be rejected (`Revoked`), an expired
   session **shall** be rejected (`Expired`), and a session in any non-`active` state **shall** be rejected
   (`NotActive`); only an `active` session may authorize a request. No stimulation is accepted outside
   `active` (accepted data-model state rule).
5. **Schema, direction, interaction, target, and action validation.** A request **shall** carry a bounded,
   non-empty schema identity/version that is a member of the declared allowed schema table, a direction and
   interaction kind consistent with a closed action→interaction→direction table and admissible by the
   declared policy, a target and interface tag equal to the bound permit, and a defined, declared-allowed
   stimulation action; any mismatch **shall** be rejected with the matching reason and no mutation.
6. **Quota bounds.** The guard **shall** enforce a finite declared per-session action budget and a finite
   declared per-window action budget; an over-budget request **shall** be rejected (`QuotaExhausted`) with
   no mutation and no emission.
7. **Bounded loop detection (`FR-019`, `XCOM-SW-STIM-005` partial).** The guard **shall** retain a bounded
   loop-detection window of authorized lineage identities and **shall** reject a request whose causal parent
   is already present in the window (`LoopBound`) with no mutation; a zero or over-maximum loop window
   **shall** fail closed at configuration.
8. **Service-ownership validation (`FR-019`, `XCOM-INV-04`/`10`, partial).** For a service invocation or
   service-emulation request, a missing, mismatched, or ambiguous declared service owner or endpoint
   generation **shall** be rejected (`OwnershipConflict`) with no mutation; the guard validates the
   declared ownership only and does not acquire, hold, release, drain, or quarantine the exclusive lease
   (`XCOM-DU-018`, T028).
9. **Pre-emission time policy (`FR-020`/`FR-033`, `XCOM-SW-STIM-006` partial, `XCOM-INV-09`).** A scheduled
   request **shall** declare a valid clock domain and a caller-resolved time expressed in the permit
   validity domain; a resolution that is absent, unmapped, or outside tolerance **shall** fail closed
   (`Failed`, `TimeUnmapped`), a resolved time outside the half-open validity interval **shall** be rejected
   (`TimeOutOfWindow`), and an immediate request **shall** be explicitly labeled and interpreted in the
   permit validity domain. The guard **shall** never compare or order two raw mismatched clock domains and
   **shall** perform no time-authority mutation of its own.
10. **Non-mutation and zero emission on rejection.** A `Rejected` or `Failed` decision **shall** leave the
    guard action tally, window tally, and loop-detection window unchanged, **shall** leave the bound permit
    and policy unchanged, and **shall** expose no emission, callback, route, provider, or item path; the
    guard **shall** have no normal-route emission entry point at all.
11. **Determinism and diagnostics.** Guard statuses, outcomes, and reasons **shall** be closed, enumerable,
    deterministically ordered vocabularies with stable names and precedence; the same operation sequence
    **shall** produce the same decision, reason, and snapshot across repeated bounded runs and builds.
12. **Bounded tests.** Add additive GoogleTest suites under `tests/xcom/stimulation_guard/` covering the
    nominal authorization path, the permit/identity/lifecycle/schema/target/direction/action/ownership/quota/
    loop/time mismatch matrices, the zero-mutation/zero-emission and closed-guard negative cases, the
    bounded-configuration matrix, and a bounded deterministic-concurrency check. The suites reuse the already
    admitted GTest prefix; no new dependency is admitted.
13. The T027 repository-owned work products and the T027 package record.

### 2.2 Explicit exclusions (must remain absent from the T027 candidate)

No emission, signal/message injection, service invocation, service emulation, or routed item (T028); no
exclusive service-emulation lease, drain, close, revoke, expiry, or terminal lifecycle completion (T028); no
tool gateway, Protocol Buffers/gRPC, IPC, TCP listener, or separate process (T030–T034); no payload or
value-body logging, payload decoder, redaction profile, or unrestricted log; no modification of
`validation_session.hpp`/`.cpp` or `stimulation_journal.hpp`/`.cpp`; no change to any existing test, target,
test name, label, command, or expected value (additive only); no new admitted dependency; no network, socket,
DNS, TLS, ambient/secret, dynamic-load, or legacy-repository/binary access; no process execution; no I/O,
file, or time-authority mutation by the guard; no benchmark, sanitizer/static/Doxygen *execution*, or
delivery bundle (T035–T040); no rewrite or weakening of an accepted ADR, requirement, contract, schema,
register, or test; no promotion of any REF-002 or capability requirement; no acceptance or integration of
the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T027 |
| --- | --- | --- |
| Guarded signal/message injection, service invocation, exclusive generation-bound service emulation | T028 | allocated; T027 computes only the fail-closed decision the action path must honor |
| Exclusive service-emulation lease, drain/close/revoke/expiry lifecycle completion | T028 | allocated; T027 validates declared ownership only and holds no lease |
| End-to-end reinjection-loop enforcement, scheduled ordering/late-item behavior, routed synthetic provenance | T028/`XCOM-DU-018` | allocated; T027 provides a bounded declaration-time loop window and zero-emission decision only |
| Full permit/action mismatch, quota, loop, lease, drain, unmapped-clock, zero-emission end-to-end matrix | T029 | allocated |
| Local tool gateway and versioned Protocol Buffers/gRPC contract | T030–T034 | allocated |
| Executed sanitizer/static-analysis/Doxygen evidence, benchmarks, integration, delivery bundle | T035–T040 | allocated |
| Independent review and user acceptance | T039/T041 | allocated |

## 3. Stakeholder requirements (`T027-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T027-STK-001**: Before any stimulation action path is accepted, the program **shall** have a
  repository-owned, bounded, domain-neutral, fail-closed pre-emission guard, physically under
  `src/xverse/xcom/` with tests under `tests/xcom/stimulation_guard/`, that decides whether one declared
  stimulation request may enter a route, offline under the T011-admitted toolchain and the T012
  warning-as-error contract.
- **T027-STK-002**: The guard **shall** reject a request whose authorization, plan digest, identity, session
  lifecycle, schema, direction, interaction, target, action, time, quota, loop, or service-ownership
  declaration fails, and a rejection or failed evaluation **shall** mutate no operational state and **shall**
  emit no normal-route item; an unmappable or out-of-tolerance time **shall** fail or be marked invalid
  before emission.
- **T027-STK-003**: T027 **shall** preserve accepted intent: the delivered change is confined to the T027
  source paths, its tests, the shared build files, the T027 work products, and the capability task ledger,
  and it **shall** neither modify accepted T025/T026 bytes, weaken an accepted requirement or test, nor
  implement another task.
- **T027-STK-004**: The guard **shall** be offline, local-only, bounded, and deterministic: every record,
  table, window, thread, and iteration is finite and declared; it performs no network, socket, ambient
  configuration, secret, dynamic-load, process, file, or legacy access, adds no domain-specific primitive,
  and adds no new admitted dependency.
- **T027-STK-005**: T027 **shall** report maturity honestly: `XCOM-SW-STIM-004` is implemented by this task,
  `XCOM-SW-STIM-005` and `XCOM-SW-STIM-006` remain **partial** (guard-level portion only, with T028/T029
  owning the lease, end-to-end loop, scheduling, and matrix), the REF-002 disposition stays `unchanged` with
  an empty `promoted` list, and no requirement is promoted.

## 4. Software/engineering requirements (`T027-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Verified" means the repository-owned test exists, is deterministic, and passes at the recorded
candidate revision; it is not a production, compatibility, or end-to-end route claim.

### 4.1 Unit, build wiring, and dependency reuse

- **T027-SR-001 [ubiquitous]**: The guard **shall** be a new, additive C++20 unit at
  `src/xverse/xcom/include/xverse/xcom/stimulation_guard.hpp` and
  `src/xverse/xcom/src/stimulation_guard.cpp`, exposed through one new runtime target
  `xverse_xcom_stimulation_guard` added to the T012 `XVERSE_XCOM_RUNTIME_TARGETS` inventory and routed
  through the inherited warning-as-error rule; it **shall** change no existing production header, source,
  or target behavior, and every existing test case, target, label, command, and expected value **shall** be
  preserved unchanged.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-018`, `XCOM-SYS-FR-030`; FR-018, FR-030; ADR-0020;
    T012 subtree build contract.
  - Verification intent: changed-path and discovered-count comparison plus the full suite; CHK-02, CHK-04,
    CHK-18, NEG-01.
- **T027-SR-002 [ubiquitous]**: The guard **shall** depend only on the C++ standard library, the accepted
  T025 `validation_session.hpp` in-process contract (`XCOM-XLC-006`), and the accepted T-CORE
  `contract.hpp`/`result.hpp` interaction and diagnostic vocabulary; it **shall** add no admitted
  dependency, no Protocol Buffers/gRPC, and **shall** redefine no identity, digest, diagnostic, or
  interaction vocabulary where an accepted one exists.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-018`, `XCOM-SYS-FR-026`; FR-018, FR-026;
    `XCOM-XLC-006`; Constitution II, VII.
  - Verification intent: include/link inspection and the offline build; CHK-03, CHK-19, NEG-02.

### 4.2 Closed vocabularies, bounded values, and payload safety

- **T027-SR-003 [ubiquitous]**: The guard **shall** expose closed, enumerable, deterministically ordered
  vocabularies: a stimulation-action vocabulary (inject signal / inject message / invoke service / emulate
  service) with a defined-bit mask and stable names; a closed `GuardOutcome` (`Authorized`, `Rejected`,
  `Failed`); a closed `GuardReason` naming each failing check; and a closed guard-status vocabulary for the
  open/precondition boundary. A `GuardReason` or `GuardOutcome` **shall** never be a catch-all, and stable
  precedence **shall** be declared.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-018`, `XCOM-SYS-FR-025`; FR-018, FR-025;
    `XCOM-DU-017`.
  - Verification intent: vocabulary inspection and determinism cases; CHK-17, NEG-28.
- **T027-SR-004 [ubiquitous]**: The guard's bounded values (`StimulationPolicy`, `StimulationRequest`,
  `SchemaKey`, `ServiceOwner`, `ResolvedTime`, `GuardDiagnostic`, `GuardSnapshot`) **shall** carry no payload,
  value body, address, free-form text, or unbounded member; the declared allowed-schema table **shall** be
  bounded by a declared maximum; a compile-time rule **shall** reject construction from a payload byte
  container or free-form text and **shall** bound each value's size; and the absence of a payload-bearing
  member **shall** be established by declaration inspection.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-018`, `XCOM-SYS-FR-027`; FR-018, FR-027;
    `XCOM-DU-017`.
  - Verification intent: field inspection and a non-vacuous compile-time negative assertion; CHK-05, CHK-20,
    NEG-03, NEG-05.

### 4.3 Identity, lifecycle, schema, direction, target, and action checks

- **T027-SR-005 [event-driven]**: When a request is evaluated, if its session identity, permit identity, or
  plan digest differs from the bound immutable permit, the guard **shall** reject it (`PermitMismatch`)
  before any state mutation and before any emission; every authorization **shall** be bound to the exact
  plan digest (`XCOM-INV-07`).
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-018`; FR-018; `XCOM-DU-017`; `XCOM-INV-07`.
  - Verification intent: identity/plan mismatch matrix; CHK-06, CHK-16, NEG-06, NEG-07.
- **T027-SR-006 [event-driven]**: If the addressed session is revoked the request **shall** be rejected
  (`Revoked`); if it is expired the request **shall** be rejected (`Expired`); if it is in any non-`active`
  state the request **shall** be rejected (`NotActive`); in every case no operational state **shall** be
  mutated and no emission **shall** occur.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-018`, `XCOM-SYS-FR-016`; FR-016, FR-018;
    `XCOM-XB-007`; `XCOM-DU-017`.
  - Verification intent: lifecycle matrix over every declared state; CHK-07, NEG-08, NEG-09, NEG-10.
- **T027-SR-007 [event-driven]**: A request whose schema identity/version is empty, over-bound,
  non-printable, or not a member of the declared allowed-schema table **shall** be rejected
  (`SchemaMismatch`) with no mutation; a request whose interaction kind and direction are inconsistent with
  the closed action→interaction→direction table, or are not admissible by the declared policy, **shall** be
  rejected (`DirectionMismatch`/`InteractionMismatch`) with no mutation; and a request whose target or
  interface tag differs from the bound permit **shall** be rejected (`TargetMismatch`) with no mutation.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-018`; FR-018; `XCOM-DU-017`.
  - Verification intent: schema/direction/interaction/target matrix; CHK-08, CHK-09, NEG-05, NEG-11,
    NEG-12, NEG-13, NEG-14.
- **T027-SR-008 [event-driven]**: A request carrying a zero, composite, or out-of-vocabulary stimulation
  action **shall** be rejected as malformed (`RejectedConfiguration`); a request carrying a defined action not
  declared allowed by the session policy **shall** be rejected (`ActionMismatch`); in every case with no
  mutation and no emission.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-018`; FR-018; `XCOM-DU-017`.
  - Verification intent: action matrix; CHK-09, NEG-04, NEG-15.

### 4.4 Quota, loop, and service ownership

- **T027-SR-009 [event-driven]**: The guard **shall** enforce a finite declared per-session authorized-action
  budget and a finite declared per-window authorized-action budget; a request that would exceed either bound
  **shall** be rejected (`QuotaExhausted`) with no mutation and no emission, and the tally **shall** advance
  only on `Authorized`.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-018`, `XCOM-SYS-FR-007`; FR-007, FR-018;
    `XCOM-INV-05`; `XCOM-DU-017`.
  - Verification intent: per-session and per-window boundary cases; CHK-10, NEG-16, NEG-17, NEG-36.
- **T027-SR-010 [event-driven]**: The guard **shall** retain a bounded loop-detection window of authorized
  lineage identities; a request whose causal parent is already present in the window **shall** be rejected
  (`LoopBound`) with no mutation, and on authorization the request lineage **shall** be recorded and the
  window **shall** advance under the declared depth bound without unbounded growth.
  - Refines: `XCOM-SW-STIM-005` (partial); anchors `XCOM-SYS-FR-019`; FR-019; `XCOM-DU-017`.
  - Verification intent: reinjection and window-bound cases; CHK-12, NEG-18, NEG-19.
- **T027-SR-011 [event-driven]**: For a service invocation or service-emulation request, the guard **shall**
  reject a missing, mismatched, or ambiguous declared service owner or endpoint generation
  (`OwnershipConflict`) with no mutation; it **shall** validate the declared ownership identity only and
  **shall** acquire, hold, release, drain, or quarantine no exclusive lease (that remains `XCOM-DU-018`/
  T028).
  - Refines: `XCOM-SW-STIM-005` (partial); anchors `XCOM-SYS-FR-019`, `XCOM-SYS-FR-034`; FR-019, FR-034;
    `XCOM-INV-04`, `XCOM-INV-10`; `XCOM-DU-017`.
  - Verification intent: ownership declaration matrix; CHK-11, NEG-20, NEG-21.

### 4.5 Time policy, non-mutation, and determinism

- **T027-SR-012 [event-driven]**: For a scheduled request, the guard **shall** require a valid declared clock
  domain and a caller-resolved time expressed in the permit validity domain; when the resolution is absent,
  unmapped, or outside the declared tolerance the guard **shall** return `Failed` (`TimeUnmapped`) and allow
  no emission; when the resolved time is outside the half-open permit validity interval the guard **shall**
  return `Rejected` (`TimeOutOfWindow`); an immediate request **shall** be explicitly labeled and interpreted
  in the permit validity domain; the guard **shall** never compare or order two raw mismatched clock domains
  (`XCOM-INV-09`) and **shall** perform no time-authority mutation or I/O.
  - Refines: `XCOM-SW-STIM-006` (partial); anchors `XCOM-SYS-FR-020`, `XCOM-SYS-FR-033`; FR-020, FR-033;
    `XCOM-INV-09`; `XCOM-DU-017`.
  - Verification intent: time-window, unmapped-clock, and immediate-labeling cases; CHK-13, CHK-19, NEG-22,
    NEG-23, NEG-24, NEG-25, NEG-35.
- **T027-SR-013 [unwanted]**: If an evaluation returns `Rejected` or `Failed`, the guard **shall** leave its
  action tally, window tally, loop-detection window, bound permit, and bound policy unchanged, **shall**
  return an explicit reason, and **shall** expose no emission, callback, route, provider, item, or lease
  path; a rejected or failed evaluation **shall never** report `Authorized`.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-018`; FR-018; `XCOM-XB-007`; `XCOM-DU-017`.
  - Verification intent: zero-mutation snapshot comparison, no-emission surface inspection, and closed-guard
    cases; CHK-14, CHK-15, CHK-21, NEG-26, NEG-27, NEG-34.
- **T027-SR-014 [ubiquitous]**: The same operation sequence **shall** produce the same decision, the same
  primary reason, the same diagnostic detail, and the same snapshot across repeated bounded runs and builds;
  precedence **shall** be stable so that a request failing more than one check always reports the same
  declared first check.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-018`, `XCOM-SYS-FR-025`; FR-018, FR-025;
    `XCOM-DU-017`.
  - Verification intent: repeated-run equality and precedence cases; CHK-17, NEG-28.
- **T027-SR-015 [ubiquitous]**: The guard **shall** serialize evaluation and commit under one per-guard
  mutex, **shall** invoke no host callback, and the tests **shall** use only a bounded, finite thread and
  iteration count with no wall-clock verdict; concurrent evaluations of one guard **shall** commit a
  deterministic total order and **shall never** exceed the declared quota or loop-window bounds or mutate
  state on a rejection.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-014`, `XCOM-SYS-FR-007`; FR-007, FR-014;
    `XCOM-DU-017` `internally-synchronized`.
  - Verification intent: bounded deterministic-concurrency and concurrent-rejection cases; CHK-18,
    NEG-29, NEG-36.

### 4.6 Safety, public safety, and governance

- **T027-SR-016 [ubiquitous]**: The guard **shall** be local-only and offline: it **shall** perform no file,
  network, socket, resolver, TLS, ambient-configuration, secret, dynamic-load, subprocess, or
  legacy-repository/binary access, **shall** own no I/O boundary, and **shall** add no domain-specific
  primitive.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028`; FR-026, FR-028; ADR-0019;
    Constitution II, VII; `XCOM-INV-13`, `XCOM-INV-15`.
  - Verification intent: forbidden-API source scan, no-I/O inspection, and the offline build; CHK-19,
    NEG-30.
- **T027-SR-017 [ubiquitous]**: Committed source, tests, work products, and evidence **shall** contain no
  credential, private address, unrestricted or real payload, proprietary source excerpt,
  environment-specific absolute host path, or sensitive deployment value.
  - Refines: Constitution X; anchors `XCOM-SYS-FR-027`; FR-027; public-safe evidence rule.
  - Verification intent: public-safety scan; CHK-21, NEG-31.
- **T027-SR-018 [ubiquitous]**: Every new public C++ declaration **shall** carry useful Doxygen
  documentation including ownership, lifetime, thread-safety, and failure contract, and the header file
  block **shall** name T027 and `\ingroup xcom_stim`; the admitted repository documentation configuration
  **shall** be unchanged.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-029`; FR-029; `XCOM-DU-017` Doxygen obligation;
    Constitution X.
  - Verification intent: declaration inspection and the existing documentation configuration check;
    CHK-22.
- **T027-SR-019 [ubiquitous]**: T027 **shall** reconcile with the T007 ownership register, the T008
  requirement register, the T009 architecture model, and the T010 unit design without rewriting or
  weakening them; **shall** keep the REF-002 disposition `unchanged` with an empty `promoted` list; and
  **shall** record honestly that `XCOM-SW-STIM-004` is implemented by this task, that `XCOM-SW-STIM-005` and
  `XCOM-SW-STIM-006` remain **partial** (guard-level portions only, with T028/T029 owning the lease,
  end-to-end loop, scheduling, and matrix), and that T028–T041 remain allocated.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-035`, `XCOM-SYS-FR-030`; FR-030, FR-035; Constitution VII, IX.
  - Verification intent: register validators plus the recorded-maturity inspection; CHK-23, NEG-32.
- **T027-SR-020 [ubiquitous]**: The T027 candidate **shall** satisfy the deterministic Fabro gate for an
  implementation task: the six named work products exist, at least one `src/xverse/xcom/` path and at least
  one `tests/` path change, `cmake` configure, build, discovery, and the full `ctest` suite pass, and
  `git diff --check` is clean; the T027 checkbox is marked complete **only** in the implementation stage.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-030`; FR-030; Constitution X.
  - Verification intent: `xcom_feature_gate.py verify T027 <baseline>`; `git diff --check`; CHK-24,
    NEG-32.
- **T027-SR-021 [ubiquitous]**: A guard constructed from an invalid, zero, or inconsistent declared policy
  (a zero/over-maximum bound, an inconsistent plan digest / interface / target / validity domain versus the
  bound permit, or an over-full schema table) **shall** fail closed at open with `RejectedConfiguration`,
  **shall** authorize no request, and **shall** mutate no external state.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-007`, `XCOM-SYS-FR-018`; FR-007, FR-018;
    `XCOM-DU-017` overflow `reject`/`fail-closed`.
  - Verification intent: policy/open boundary cases; CHK-06, CHK-18, NEG-19, NEG-33.
- **T027-SR-022 [ubiquitous]**: The guard **shall** evaluate and return its decision without calling any
  emission, routing, injection, invocation, emulation, or lease entry point, and its public surface
  **shall** expose no such entry point; the guard **shall** be the only T027 production surface that
  produces a decision and **shall** produce no side effect outside its own bounded tallies.
  - Refines: `XCOM-SW-STIM-004`; anchors `XCOM-SYS-FR-018`; FR-018; `XCOM-XB-007`; `XCOM-DU-017`.
  - Verification intent: declaration/surface inspection and the closed-guard case; CHK-15, NEG-27,
    NEG-34.

## 5. Requirement-to-accepted-anchor traceability

| T027 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T027-STK-001 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-018` | FR-018 | IX, X |
| T027-STK-002 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-018` | FR-018 | IX |
| T027-STK-003 | Constitution VII/IX; ADR-0020 | `XCOM-SYS-FR-030` | FR-030 | VII, IX, X |
| T027-STK-004 | `XCOM-SW-CORE-007` | `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028` | FR-026, FR-028 | II, VII, IX |
| T027-STK-005 | ADR-0020 | `XCOM-SYS-FR-035` | FR-035 | VII, IX |
| T027-SR-001 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-018/030` | FR-018, FR-030 | VII, X |
| T027-SR-002 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-018/026` | FR-018, FR-026 | II, VII |
| T027-SR-003 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-018/025` | FR-018, FR-025 | IX |
| T027-SR-004 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-018/027` | FR-018, FR-027 | IX, X |
| T027-SR-005 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-018` | FR-018 | IX |
| T027-SR-006 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-016/018` | FR-016, FR-018 | IX |
| T027-SR-007 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-018` | FR-018 | IX |
| T027-SR-008 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-018` | FR-018 | IX |
| T027-SR-009 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-007/018` | FR-007, FR-018 | V, IX |
| T027-SR-010 | `XCOM-SW-STIM-005` (partial) | `XCOM-SYS-FR-019` | FR-019 | IX |
| T027-SR-011 | `XCOM-SW-STIM-005` (partial) | `XCOM-SYS-FR-019/034` | FR-019, FR-034 | IX |
| T027-SR-012 | `XCOM-SW-STIM-006` (partial) | `XCOM-SYS-FR-020/033` | FR-020, FR-033 | IX |
| T027-SR-013 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-018` | FR-018 | IX |
| T027-SR-014 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-018/025` | FR-018, FR-025 | IX |
| T027-SR-015 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-007/014` | FR-007, FR-014 | IX |
| T027-SR-016 | `XCOM-SW-CORE-007` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | II, VII, IX |
| T027-SR-017 | public-safe evidence rule | `XCOM-SYS-FR-027` | FR-027 | X |
| T027-SR-018 | `XCOM-SW-STIM-004` Doxygen | `XCOM-SYS-FR-029` | FR-029 | X |
| T027-SR-019 | Constitution; ADR-0020 | `XCOM-SYS-FR-030/035` | FR-030, FR-035 | VII, IX |
| T027-SR-020 | ADR-0020 | `XCOM-SYS-FR-030` | FR-030 | X |
| T027-SR-021 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-007/018` | FR-007, FR-018 | IX |
| T027-SR-022 | `XCOM-SW-STIM-004` | `XCOM-SYS-FR-018` | FR-018 | IX |

`XCOM-SW-STIM-004`, `XCOM-SW-STIM-005`, and `XCOM-SW-STIM-006` are accepted capability-007 software
requirements (`docs/engineering/xcom/t008/requirements-register.{json,md}`). They are accepted text; T027
refines and consumes them and does not rewrite them. No register row is changed and no maturity is promoted.

## 6. REF-002 disposition

T027 owns no REF-002 SADS ID and promotes none. It provides evidence toward the allocated communication
IDs already exercised by the stimulation boundary: `XVE-SYS-0147` (bounded queueing/overflow and explicit
failure), `XVE-SYS-0149` (deterministic diagnostics and metrics), and the bounded-failure portion of
`XVE-SYS-0158` (deferred automatic recovery; capability 007 defines the bounded failure outcome). It
promotes nothing, and the capability `ref002.disposition` stays `unchanged` with an empty `promoted` list
(T027-SR-019). No allocated, deferred, architectural-target, or superseded SADS requirement is reported as
implemented.

## 7. Affected paths

### 7.1 Paths the T027 candidate changes (implementation stage)

| Path | Change | Notes |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/stimulation_guard.hpp` | add | new public guard interface (vocabularies, bounded policy/request/time values, decision API) |
| `src/xverse/xcom/src/stimulation_guard.cpp` | add | implementation of the deterministic check order and bounded tallies |
| `src/xverse/xcom/CMakeLists.txt` | edit | add `xverse_xcom_stimulation_guard` to `XVERSE_XCOM_RUNTIME_TARGETS`; define the library; add the additive test targets and labels |
| `tests/xcom/stimulation_guard/unit_tests.cpp` | add | nominal path, action/interaction/direction table, vocabulary/precedence, policy/open matrix |
| `tests/xcom/stimulation_guard/mismatch_tests.cpp` | add | permit/identity/plan, lifecycle, schema/target, action/direction, service-ownership, quota, loop matrices |
| `tests/xcom/stimulation_guard/time_tests.cpp` | add | scheduled time-window, unmapped-clock fail-closed, immediate-labeling matrices |
| `tests/xcom/stimulation_guard/negative_tests.cpp` | add | zero-mutation/zero-emission, closed-guard, policy-bound negative cases |
| `tests/xcom/stimulation_guard/concurrency_tests.cpp` | add | bounded deterministic concurrency and concurrent-rejection non-mutation |
| `docs/engineering/xcom/t027/requirements.md` | add | this document |
| `docs/engineering/xcom/t027/architecture.md` | add | T027 architecture |
| `docs/engineering/xcom/t027/detailed-design.md` | add | T027 detailed design |
| `docs/engineering/xcom/t027/unit-specifications.md` | add | T027 unit specifications |
| `docs/engineering/xcom/t027/verification-plan.md` | add | T027 verification plan |
| `docs/engineering/xcom/t027/implementation.md` | add | implementation-stage record |
| `docs/engineering/xcom/t027/internal-review.json` | add | internal-review record |
| `specs/007-xcom-core/tasks.md` | edit | one-line T027 checkbox, **implementation stage only** |
| `reports/xcom-queue/t027-package.json` | add | implementation-stage package record |

### 7.2 Consumed read-only (not changed by T027)

`src/xverse/xcom/include/xverse/xcom/validation_session.hpp`,
`src/xverse/xcom/src/validation_session.cpp`, `tests/xcom/validation_session/**`,
`src/xverse/xcom/include/xverse/xcom/stimulation_journal.hpp`,
`src/xverse/xcom/src/stimulation_journal.cpp`, `tests/xcom/stimulation_journal/**`, the accepted T-CORE
headers (`contract.hpp`, `result.hpp`, `value.hpp`, `core_types.hpp`, `diagnostic.hpp`, `item.hpp`, and the
other accepted core headers), `docs/engineering/xcom/task-ownership.*`, `docs/engineering/xcom/t008/**`,
`docs/engineering/xcom/t009/**`, `docs/engineering/xcom/t010/**`, `specs/007-xcom-core/**` (other than the
checkbox), `xdl/**`, `cmake/XComOfflineDependencies.cmake`, `cmake/XComWarnings.cmake`, and the root
`CMakeLists.txt`.

### 7.3 Explicitly not implemented by T027

`stimulation_actions.hpp/.cpp` and the exclusive service-emulation lease (T028),
`proto/xverse/xcom/v1/tool_gateway.proto` and the gateway (T030–T031), and the contract/benchmark/
Doxygen/delivery tasks (T033–T041).

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- **T027-GAP-01 — loop partial.** `XCOM-SW-STIM-005` is implemented only at the guard's declaration-level
  bounded loop window; end-to-end reinjection-loop enforcement through routing and the atomic
  service-emulation lease remain `XCOM-DU-018`/T028 and are tested in T029. T027 claims no `loop-bounds` or
  `lease-conflicts` end-to-end evidence.
- **T027-GAP-02 — scheduling partial.** `XCOM-SW-STIM-006` is implemented only as a pre-emission time-policy
  check; scheduled ordering, late-item behavior, and the end-to-end unmapped-clock/tolerance behavior remain
  T028/T029. The guard consumes a caller-resolved time and performs no time-authority mutation.
- **T027-GAP-03 — decision, not emission.** The guard produces a decision only. It exposes no emission,
  routing, injection, invocation, emulation, or lease path; the end-to-end "zero normal-route item after
  rejection" proof requires the T028 action path and is closed by T029.
- **T027-GAP-04 — declared ownership only.** Service-ownership validation is a declaration-level check; the
  guard acquires, holds, releases, drains, and quarantines no exclusive lease (`XCOM-DU-018`, T028).
- **T027-GAP-05 — single guard per session.** Concurrency is bounded to one writer per guard; shared or
  multi-process guards are not supported and are not claimed.

### 8.2 Gaps with owning tasks

| Gap | Owner |
| --- | --- |
| Guarded injection/invocation/emulation and the exclusive service-emulation lease | T028 |
| End-to-end reinjection-loop, scheduling/late-item, and routed synthetic provenance | T028 |
| Full permit/action mismatch, quota, loop, lease, drain, unmapped-clock, zero-emission matrix | T029 |
| Gateway, Protocol Buffers/gRPC, separate process | T030–T034 |
| Executed sanitizer/static/Doxygen/benchmark and delivery bundle | T035–T040 |
| Independent review and user acceptance | T039/T041 |

### 8.3 Open items

- **T027-OPEN-01 — bound source versus `XCOM-DU-017`.** The accepted T010 `XCOM-DU-017` records the
  loop-detection window and the per-session/per-interval action limits as "declared in validation permit".
  The accepted T025 `Permit` exposes `allowed_actions` over the lifecycle `Action` vocabulary and a
  `Quota{QuotaKind::Operations, QuotaKind::Evidence}` list, and carries no stimulation-action, schema,
  interface, or loop-window declaration. T027 therefore supplies a bounded session-scoped
  `StimulationPolicy` value, derived by the caller from the digest-bound plan, whose `plan_digest`,
  interface, target, and validity domain are cross-checked against the immutable permit at open. The
  implementation stage records the delta from the accepted T010 artifact as a successor note rather than
  editing the accepted T010 artifact silently.
- **T027-OPEN-02 — time resolution responsibility.** The guard consumes a caller-resolved time value rather
  than calling the accepted `TimeAuthority` directly, so that a rejection can never mutate the authority's
  regression baseline through the guard. The accepted authority remains the only time-mapping mechanism
  (`FR-033`); T028 owns the end-to-end wiring and T029 the matrix.

## 9. Definition of done (requirements view)

T027 is done for a candidate revision when: every §4 requirement has at least one named check; the
permit/identity/lifecycle/schema/target/direction/action/ownership/quota/loop/time fail-closed behaviours
and the zero-mutation/zero-emission-on-rejection behaviour are proven by deterministic tests;
`XCOM-SW-STIM-004` is implemented and `XCOM-SW-STIM-005`/`XCOM-SW-STIM-006` are recorded partial with the
lease/end-to-end loop/scheduling portions explicitly deferred; no accepted requirement, test, ADR,
contract, register, or T025/T026 byte is weakened; the register validators pass with REF-002 unchanged and
nothing promoted; the deterministic gate passes; and a separate DeepSeek internal review records its
findings before any repair. This does not constitute user acceptance.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary checks |
| --- | --- |
| T027-STK-001 | CHK-01, CHK-02, CHK-04 |
| T027-STK-002 | CHK-07, CHK-08, CHK-09, CHK-10, CHK-12, CHK-13, CHK-14 |
| T027-STK-003 | CHK-02, CHK-03, CHK-23 |
| T027-STK-004 | CHK-17, CHK-18, CHK-19, CHK-21 |
| T027-STK-005 | CHK-23, CHK-24 |
| T027-SR-001 | CHK-02, CHK-04, CHK-18 |
| T027-SR-002 | CHK-03, CHK-19 |
| T027-SR-003 | CHK-17, CHK-20 |
| T027-SR-004 | CHK-05, CHK-20 |
| T027-SR-005 | CHK-06, CHK-16 |
| T027-SR-006 | CHK-07 |
| T027-SR-007 | CHK-08, CHK-09 |
| T027-SR-008 | CHK-09 |
| T027-SR-009 | CHK-10 |
| T027-SR-010 | CHK-12 |
| T027-SR-011 | CHK-11 |
| T027-SR-012 | CHK-13, CHK-19 |
| T027-SR-013 | CHK-14, CHK-15 |
| T027-SR-014 | CHK-17 |
| T027-SR-015 | CHK-18 |
| T027-SR-016 | CHK-19 |
| T027-SR-017 | CHK-21 |
| T027-SR-018 | CHK-22 |
| T027-SR-019 | CHK-23 |
| T027-SR-020 | CHK-24 |
| T027-SR-021 | CHK-06, CHK-18 |
| T027-SR-022 | CHK-15 |
