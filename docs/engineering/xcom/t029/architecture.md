# T029 Architecture — Complete Stimulation Verification Matrix and Owned Fixtures

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T029 (capability 007, slice `T-STIM`) |
| Stage / role | plan → architecture |
| Revision | 1 (complete T-STIM cross-cutting verification matrix) |
| Baseline revision | `4d3985855ef7a62b68aa4c66d3b7df032b29f5e9` |
| Affected source paths | `tests/xcom/stimulation_matrix/**` (new), `src/xverse/xcom/CMakeLists.txt` (edit, additive test registration), inherited `engineering/trace/links.json` and `engineering/stage-results/*.json` digest refresh (implementation stage) |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-009` validation stimulation session, `XCOM-XB-007` validation-session-to-core boundary, `XCOM-XLC-006` in-process contract, `XCOM-INV-03`/`04`/`05`/`07`/`09`/`10`); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-014`…`-018`); `docs/engineering/xcom/t028/architecture.md`; `docs/engineering/xcom/t009/architecture.md`; `docs/engineering/xcom/t010/detailed-design.md`; `specs/007-xcom-core/data-model.md`; `specs/007-xcom-core/contracts/validation-tool.md`; `specs/007-xcom-core/contracts/observation.md`; ADR-0016, ADR-0018, ADR-0019, ADR-0020 |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T029 is the **verification matrix** of the `T-STIM` slice. It authors no production behaviour: it composes the
already implemented and accepted T025/T026/T027/T028 surfaces into bounded owned fixtures and exercises the
complete permit/action mismatch matrix, journal ordering and recovery, zero emission after every rejection,
persistent synthetic provenance, unmapped clocks, quotas, loop bounds, lease conflicts, drain/terminal behavior,
and deterministic concurrency. It is the verification half of `XCOM-DU-018` and the closure of the `T-STIM`
slice evidence declared by the T007 ownership register.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013/T-CORE contract + origin/diagnostic vocabulary (read-only)
   → T021–T024 observation boundary (read-only)
   → T025 time authority + permit + session lifecycle (accepted, read-only)
   → T026 durable intent/outcome journal (read-only)
   → T027 fail-closed pre-emission guard (read-only)
   → T028 guarded injection/invocation/emulation + exclusive lease + completion (read-only)
   → T029 complete stimulation verification matrix (this slice, tests only)
   → T030–T034 gateway/conformance → T035–T041 evidence/review/acceptance
```

T029 is a **test-only** slice: the deterministic gate requires at least one changed `tests/` path and does not
require a production-source change. It adds six additive CTest executables and one fixture header; it changes no
accepted production byte and no accepted test, target, label, command, or expected value.

## 3. Boundary and context

### 3.1 System context

```text
   ┌──────── accepted T025/T026/T027/T028 in-process contracts (read-only, src/xverse/xcom) ───┐
   │  validation_session.hpp : Permit · PermitBuilder · SessionId · PlanDigest · Quota ·          │
   │    Timestamp · ClockDomainId · Tag · Generation · Result · Diagnostic · LifecycleState       │
   │  stimulation_journal.hpp : StimulationIntent · StimulationOutcome · OutcomeKind ·            │
   │    JournalStatus · StimulationJournal · Storage (fault-injectable) · RecoveryReport          │
   │  stimulation_guard.hpp : StimulationAction · StimulationRequest · StimulationPolicy ·         │
   │    ResolvedTime · GuardOutcome · GuardReason · StimulationGuard                              │
   │  stimulation_actions.hpp : StimulationActionPath · ServiceEmulationRegistry · ActionEmitter · │
   │    ActionStatus · LeaseStatus · CompletionOutcome · SyntheticStimulationItem                 │
   └─────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                             │ composed read-only by the T029 owned fixture
   ┌────────────────── accepted T-CORE/T-OBS public surfaces (read-only) ──────────────────────┐
   │  item.hpp : CommunicationItem · CommunicationItemInput · OriginKind::validation_tool         │
   │  observation.hpp : ObservationHub · ObservationTapSpec · ObservationFilter ·                 │
   │    ObservationRecord · SyntheticObservationSink                                              │
   │  provider.hpp : ProviderComposition (submit + observation) · ProviderDescriptor · RouteSpec  │
   │  endpoint_route_lifecycle.hpp : LifecycleController · EndpointHandle · RouteHandle          │
   └─────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                             │ exercised read-only by the provenance case
   ┌──────────────────────── T029 owned fixture + matrix (this slice, tests/xcom) ─────────────┐
   │  test_support.hpp    : bounded fixture (permit/session, policy, fault-injectable storage,    │
   │                        registry, action path, recording/fault-injectable emitter, bridge)     │
   │  permit_action_matrix_tests · journal_recovery_tests · zero_emission_tests ·                  │
   │  provenance_tests · lease_drain_tests · concurrency_tests                                    │
   │  guarantee          : every decline emits nothing and journals nothing; provenance persists   │
   └─────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                             ▼
                    T030–T034 gateway/conformance · T035–T040 evidence · T039/T041 review/acceptance
```

T029 introduces no production transport, listener, provider, route, endpoint, tap, emitter, journal, guard, or
action path of its own. Its fixture is test-local and composes the accepted public surfaces; the provenance case
supplies a bounded, declared identity projection to the accepted T-CORE item vocabulary (recorded as
`T029-GAP-02`).

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T29-XB-1` Test-only slice vs production | the T029 test sources, fixture header, additive test targets, and work products | every accepted production header, source, runtime target, and existing test | T029 consumes the accepted surfaces read-only and changes no production byte and no existing test/target/label/command/value. |
| `T29-XB-2` Owned fixture vs accepted services | the bounded fixture (permit/session, policy, registry, action path, storage, emitter, bridge) | the accepted guard, journal, provider, and observation implementations | The fixture owns only bounded values and injected faults; it re-implements, weakens, or bypasses no accepted check. |
| `T29-XB-3` Authorized vs emission | the accepted guard `Authorized` decision | the host emitter seam | Only `Authorized` reaches the emitter; every rejection family records zero emitter calls and zero durable journal appends. |
| `T29-XB-4` Journal-before-emission | the durable intent frame | the emitter invocation | The matrix asserts the durable intent precedes the single emitter call, and an intent without a durable outcome is `EvidenceIncomplete`, never success. |
| `T29-XB-5` Synthetic provenance | `OriginKind::validation_tool` and the exact identity | any relabelling, drop, or inference through route, observation, or restart | The matrix asserts the classification and identity survive the accepted route, the accepted observation tap, and a journal restart. |
| `T29-XB-6` Declared clocks | a caller-resolved time in the permit validity domain | two raw mismatched clock domains, wall-clock scheduling, and authority mutation | The matrix asserts an unmapped/out-of-tolerance resolution fails closed, no raw cross-domain comparison occurs, and no time authority is called. |
| `T29-XB-7` Bounded resources | the finite queue, lease table, lineage window, drain budget, quota, threads, and iterations | an unbounded queue, thread, retry, wait, or growth | Every case declares finite bounds; a bound is exercised and fails closed as declared. |
| `T29-XB-8` Concurrency determinism | one declared writer per component and ≤ 4 test threads | a host callback under a lock and a non-deterministic outcome | The matrix asserts one lease winner, a non-exceeded quota, a deterministic total order, and identical repeated runs. |
| `T29-XB-9` Repository vs environment | committed tests, fixtures, work products | admitted build inputs, host environment, payloads | Committed files are public-safe and offline; T029 performs no network, ambient/secret, dynamic-load, subprocess, filesystem (other than the test-local injected seam), or legacy access and retains/logs no payload. |
| `T29-XB-10` T029 scope vs later tasks | the bounded in-process matrix and owned fixture | the gateway, separate process, reusable contract suites, and delivery evidence | T029 implements no gateway, Protocol Buffers/gRPC, IPC, separate process, reusable suite, benchmark, sanitizer, or Doxygen execution. |

### 3.3 Prohibited elements (must remain absent)

No production header/source change and no production runtime-target change; no change to any existing test,
target, label, command, or expected value; no re-implementation, weakening, or bypass of the accepted guard,
journal, provider, or observation checks; no transport, listener, gateway, Protocol Buffers/gRPC, IPC, or
separate process; no reusable contract-suite abstraction; no benchmark, sanitizer/static/Doxygen execution, or
delivery bundle; no payload/value log, decoder, redaction profile, dashboard, storage, query, or export
primitive; no network/socket/TLS/resolver, ambient/secret, dynamic-load, subprocess, or legacy
repository/binary access; no unbounded queue/table/thread/retry/wait; no host callback under a lock; no
wall-clock verdict; no time-authority mutation; no new admitted dependency; no rewrite or weakening of an
accepted ADR, requirement, contract, schema, register, or REF-002 disposition. These inherit the T007 global
prohibitions, the T011 envelope, the T012 build contract, ADR-0019, ADR-0020, and the constitution.

## 4. Components

`T29-*` names are local to this document; the accepted `XCOM-DU-014`…`-018`, `XCOM-CMP-009`, `XCOM-XB-007`, and
`XCOM-XLC-006` identifiers are the authorized units/contracts.

### 4.1 New test components (no production component)

- **`T29-CMP-FIXTURE` Owned fixture harness** (`tests/xcom/stimulation_matrix/test_support.hpp`): a bounded,
  payload-free composition of an in-process accepted `Permit`/session, an accepted `StimulationPolicy`, an
  accepted `StimulationJournal` over a fault-injectable in-test `Storage` seam, an accepted
  `ServiceEmulationRegistry`, an accepted `StimulationActionPath`, a recording/fault-injectable `ActionEmitter`,
  and a bounded bridge that builds a `CommunicationItem` classified `OriginKind::validation_tool` for the
  accepted provider/observation boundary. Every bound, table, injection, and iteration is finite and declared; no
  payload byte is retained.
- **`T29-CMP-MISMATCH` Permit/action mismatch matrix** (`permit_action_matrix_tests.cpp`): every
  request-evaluation guard reason, the lifecycle-state preconditions, quotas, loop bounds, and unmapped clocks.
- **`T29-CMP-JOURNAL` Journal ordering and recovery matrix** (`journal_recovery_tests.cpp`): intent-before-emission
  ordering, intent append/sync failure, outcome failure, restart recovery, and capacity exhaustion.
- **`T29-CMP-ZERO` Zero-emission matrix** (`zero_emission_tests.cpp`): every decline family with zero emitter calls
  and unchanged durable journal bytes.
- **`T29-CMP-PROV` Provenance matrix** (`provenance_tests.cpp`): descriptor classification and identity,
  routed/observed preservation, restart identity equality, and no relabelling.
- **`T29-CMP-LEASE-DRAIN` Lease and completion matrix** (`lease_drain_tests.cpp`): lease conflicts, generation
  supersession, release/quarantine/expiry, ordering, drain budget, late policies, and terminal completion.
- **`T29-CMP-CONC` Deterministic concurrency matrix** (`concurrency_tests.cpp`): bounded threads, quota bound,
  single lease winner, and repeated-run determinism.
- **`T29-CMP-BUILD`** (T012): the subtree warning-as-error rule extended additively by six test executables; no
  runtime-target inventory change.

### 4.2 Consumed components (read-only)

- **`T29-CMP-T025`** (`XCOM-XLC-006`, `XCOM-DU-014`/`-015`) — `Permit`, `PermitBuilder`, `PermitId`, `SessionId`,
  `PlanDigest`, `Quota`, `Timestamp`, `ClockDomainId`, `Generation`, `Tag`, `Result`, `Diagnostic`,
  `LifecycleState`: consumed read-only and **not modified**.
- **`T29-CMP-T026`** (`XCOM-DU-016`) — `StimulationJournal`, `StimulationIntent`, `StimulationOutcome`,
  `OutcomeKind`, `JournalStatus`, `RecoveryReport`, `Storage`: consumed read-only; the fixture supplies a bounded
  fault-injectable `Storage` through the accepted public seam only.
- **`T29-CMP-T027`** (`XCOM-DU-017`) — `StimulationGuard`, `StimulationPolicy`, `StimulationRequest`,
  `ResolvedTime`, `GuardOutcome`, `GuardReason`, `GuardDiagnostic`: consumed read-only.
- **`T29-CMP-T028`** (`XCOM-DU-018`) — `StimulationActionPath`, `ServiceEmulationRegistry`, `ActionEmitter`,
  `SyntheticStimulationItem`, `ActionStatus`, `LeaseStatus`, `LeaseState`, `CompletionOutcome`,
  `CompletionReport`, `ActionPathSnapshot`, `LeaseSnapshot`: consumed read-only.
- **`T29-CMP-CORE-OBS`** — accepted T-CORE `OriginKind`/`CommunicationItem`/`InteractionKind`/`EndpointDirection`
  and accepted T-OBS/provider surfaces (`ObservationHub`, `ObservationTapSpec`, `ObservationFilter`,
  `ObservationRecord`, `SyntheticObservationSink`, `ProviderComposition`, `LifecycleController`): consumed
  read-only and **not modified**; the provenance case exercises them with an owned, bounded fixture.

### 4.3 Work-product components

- **`T29-WP`** — the T029 repository-owned work-product set (`requirements.md`, `architecture.md`,
  `detailed-design.md`, `unit-specifications.md`, `verification-plan.md`, `implementation.md`,
  `internal-review.json`, and `reports/xcom-queue/t029-package.json`).

## 5. Data flow (ordered)

1. **Build the owned fixture.** A case constructs the bounded fixture: a valid accepted `Permit`/session, an
   accepted `StimulationPolicy`, an accepted `StimulationJournal` over a bounded in-test `Storage` seam, an
   accepted `ServiceEmulationRegistry`, an accepted `StimulationActionPath`, and a recording/fault-injectable
   `ActionEmitter`.
2. **Open the action path.** `StimulationActionPath::open(permit, policy)` binds the accepted guard; a case that
   needs a closed path or an invalid configuration asserts the declared rejection.
3. **Evaluate the mismatch matrix.** For each row the case submits one bounded `StimulationRequest` with the
   injected mismatch and asserts the declared `ActionStatus` and `GuardReason`, exactly one guard evaluation, zero
   emitter calls, and zero durable append.
4. **Exercise quota, loop, and clock bounds.** The case fills the declared quota/loop/lineage bound, asserts the
   bound-exhaustion status and zero emission, and asserts `causation_id == 0` is never a loop rejection and an
   unmapped/out-of-tolerance resolution fails closed.
5. **Prove journal ordering.** For each action kind the case records the durable byte count observed inside the
   single emitter call and asserts the intent was durable and non-empty before the call.
6. **Inject journal faults.** The case injects an intent append/sync failure and an outcome failure through the
   accepted `Storage` seam and asserts the matching non-emitting status (`JournalFailed`/`CapacityExhausted`/
   `RejectedConfiguration`/`EvidenceIncomplete`), with zero emission and no success claim.
7. **Restart and recover.** The case reopens a fresh `StimulationJournal` over the same durable bytes, runs the
   accepted recovery scan, and asserts the recovered intent identity equals the emitted descriptor identity and
   the orphan is classified explicitly; `mark_evidence_incomplete`/`close` report the orphan and never `Closed`.
8. **Bracket every decline.** The case snapshots the action path, the lease registry, and the durable journal
   before and after each decline family and asserts zero emitter calls and no mutation in the declined dimension.
9. **Prove provenance.** The case asserts the emitted descriptor classification and identity, builds the bounded
   bridge item, submits it through the accepted provider route, retains it in the accepted observation tap, and
   asserts the synthetic origin and exact correlation/causation identity survive; it asserts the restart identity
   equality and that an `OriginKind::validation_tool` filter matches every retained synthetic record.
10. **Exercise leases.** The case acquires one exclusive lease, asserts a same-generation conflict, a foreign
    session/generation/plan rejection, supersession, release/quarantine/expiry, and at most one active lease per
    endpoint generation.
11. **Complete the lifecycle.** The case drains within the bounded step budget in declared order, applies both
    late-item policies with zero emission, and asserts `drain`/`close`/`revoke`/`expire`/`mark_evidence_incomplete`
    return the declared outcomes with every pending action and held lease resolved.
12. **Run bounded concurrency.** The case runs ≤ 4 threads over a finite declared operation count, asserts the
    declared quota is never exceeded, exactly one lease winner, a deterministic total order, no callback under a
    lock, and identical repeated runs.

## 6. Interfaces

T029 exposes **no production interface**. It defines one test-local fixture header and consumes the accepted
public contracts read-only.

### 6.1 Test-local fixture (`tests/xcom/stimulation_matrix/test_support.hpp`)

| Element | Contract |
| --- | --- |
| `MatrixFixture` | bounded composition of permit/session, policy, journal + injectable storage, registry, action path, recording emitter, and observation bridge; non-copyable; single declared user |
| `FaultStorage` | bounded in-test `StimulationJournal::Storage` with declared injectable failures (append/sync/read/truncate) and a bounded durable byte buffer |
| `RecordingEmitter` | bounded `ActionEmitter` counting calls, capturing the last `SyntheticStimulationItem`, and optionally returning a declared `EmissionStatus`; never invoked under a lock |
| `ObservationBridge` | bounded projection of the emitted `SyntheticStimulationItem` into a `CommunicationItem` classified `OriginKind::validation_tool` and a bounded `ObservationHub`/tap/sink for the provenance case |
| helpers | bounded `make_permit`, `make_policy`, `make_request`, `in_window`, `out_of_window`, `unmapped` builders mirroring the accepted T028 test conventions |

Ownership/lifetime: the fixture owns its bounded values; the journal, registry, emitter, hub, and lifecycle
controller are constructed before and outlive the action path. Thread-safety: the concurrency cases use one
fixture with ≤ 4 joined threads; the accepted components serialize their own state and the fixture invokes no
callback under a lock. Bounds: see §7.

### 6.2 Consumed contracts (read-only)

| Interface | Contract consumed (unchanged) |
| --- | --- |
| `xverse::xcom::validation::{Permit, PermitBuilder, PermitId, SessionId, PlanDigest, Quota, Timestamp, ClockDomainId, Generation, Tag, Result, Diagnostic, LifecycleState, is_terminal}` | accepted T025 identity/lifecycle/diagnostic vocabulary, used read-only |
| `xverse::xcom::validation::{StimulationJournal, StimulationIntent, StimulationOutcome, OutcomeKind, JournalStatus, RecoveryReport, Storage}` | accepted T026 durable intent/outcome ordering, evidence-incomplete surface, and storage seam, used read-only |
| `xverse::xcom::validation::{StimulationGuard, StimulationPolicy, StimulationRequest, ResolvedTime, GuardOutcome, GuardReason, GuardDiagnostic}` | accepted T027 fail-closed pre-emission decision, used read-only |
| `xverse::xcom::validation::{StimulationActionPath, ServiceEmulationRegistry, ActionEmitter, SyntheticStimulationItem, ActionStatus, LeaseStatus, LeaseState, CompletionOutcome, CompletionReport}` | accepted T028 action path, exclusive lease, emission seam, and completion contract, used read-only |
| `xverse::xcom::{OriginKind, CommunicationItem, CommunicationItemInput, InteractionKind, EndpointDirection}` | accepted T-CORE origin/item/interaction vocabulary, used read-only |
| `xverse::xcom::{ObservationHub, ObservationTapSpec, ObservationTapSpecInput, ObservationFilter, ObservationFilterInput, ObservationRecord, SyntheticObservationSink}` | accepted T-OBS boundary, used read-only |
| `xverse::xcom::{ProviderComposition, ProviderDescriptor, ProviderRouteRequirements, LifecycleController, RouteSpec}` | accepted T-CORE provider/route boundary, used read-only |

## 7. Concurrency and resource bounds

| Aspect | T029 decision |
| --- | --- |
| Production footprint | none; six additive test executables and one fixture header only |
| Build inventory | no runtime-target change; six additive test targets under the T012 warning-as-error rule |
| Writers | one declared writer per fixture component; the accepted components serialize their own state |
| Threads in tests | ≤ 4, joined before the fixture is destroyed, only in the concurrency cases |
| Operations per case | ≤ 64 bounded operations; no unbounded loop, retry, or wait |
| Pending queue in tests | 4, 8; `max_drain_steps` 4, 8 |
| Lineage window in tests | 2, 4, 8 |
| Active leases in tests | 1, 2 |
| Guard quota in tests | 1 … 8 |
| Injection table | ≤ 4 declared storage fault points; one injected fault per case step |
| Restart attempts | one reopen per restart case; bounded durable bytes ≤ 16 KiB |
| Durable durable bytes | bounded by the accepted `JournalConfig`; no unbounded buffer |
| Payload view | the emitted helper is payload-free; the bridge item carries no payload byte; no case retains or logs a payload |
| Wall-clock | no case depends on wall-clock timing for its verdict; every time is caller-supplied |
| I/O | none in production; only the test-local in-test storage seam (and a bounded optional test-local scratch path for the restart case) |
| Determinism | every case asserts stable statuses, states, outcomes, and snapshots; repeated runs are equal |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Complete mismatch coverage | every request-evaluation guard reason and lifecycle precondition is exercised through the accepted action path | T029-SR-004, T029-SR-005; CHK-06, CHK-15 |
| Journal integrity | intent durable before the single emitter call; intent/outcome failure surfaced explicitly; restart recovers the exact identity | T029-SR-009, T029-SR-010, T029-SR-011; CHK-10, CHK-11, CHK-14 |
| Zero emission | every decline family records zero emitter calls and unchanged durable bytes | T029-SR-012; CHK-12 |
| Persistent provenance | synthetic classification and exact identity survive descriptor, route, observation, and restart | T029-SR-013, T029-SR-014, T029-SR-015; CHK-13 |
| Exclusive lease | one active lease per endpoint generation; conflict/identity/supersession rejected without mutation | T029-SR-016, T029-SR-017; CHK-17 |
| Lifecycle completion | ordered bounded drain; declared terminal outcomes; evidence-incomplete never `Closed` | T029-SR-018, T029-SR-019; CHK-14, CHK-18 |
| Bounded determinism | ≤ 4 threads, finite operations, one lease winner, identical repeated runs | T029-SR-020, T029-SR-021; CHK-16 |
| Offline safety | accepted headers plus GTest only; no network/ambient/secret/process/legacy; no payload retention | T029-SR-002, T029-SR-022; CHK-19, CHK-20 |
| Public safety | no secret, private address, real payload, or host path in committed files/evidence | T029-SR-023; CHK-21 |
| Governance | registers re-validated; REF-002 unchanged; T029 records STIM-009 and STIM-003 closed | T029-SR-024, T029-SR-025; CHK-23, CHK-24 |

## 9. Consistency and constraints

- **Dependency direction preserved.** T029 consumes the accepted T025/T026/T027/T028 in-process contracts and the
  accepted T-CORE/T-OBS public surfaces; it introduces no dependency on a later slice, adapter, gateway, or legacy
  repository, and no new admitted dependency.
- **Domain neutrality preserved.** The matrix uses only generic stimulation vocabulary (action, request, policy,
  lease, generation, session, queue, drain, ordering, late item, clock domain, quota, provenance); no automotive,
  product, protocol, or configuration primitive is introduced.
- **XDL centrality preserved.** T029 neither parses nor authors XDL; it consumes bounded identity values that the
  accepted plan already binds and cross-checks the plan digest against the immutable permit and the guard policy.
- **Logical/physical separation preserved.** Fixtures carry logical identity, plan digest, clock domain, and
  bounded tags only; no address, transport, or environment identity enters a decision.
- **Synthetic origin preserved.** Every emitted descriptor and bridged item carries `OriginKind::validation_tool`
  and the exact bound identity; no case exposes a path to a differently classified item.
- **Ownership preserved.** Only T029 test paths, the shared build file, the inherited provenance refresh, the T029
  work products, and the T029 checkbox change; every accepted production byte and existing test is preserved.
- **Maturity preserved.** The matrix stays a bounded prototype verification; the gateway, the reusable contract
  suites, executed sanitizer/static/Doxygen/benchmark evidence, and acceptance remain T030–T041.
- **Test-only scope preserved.** T029 authors no production behaviour and no reusable abstraction; the fixture is
  T029-local (`T29-GAP-05`).

## 10. Traceability

| Architecture element | T029 requirements |
| --- | --- |
| `T29-XB-1`, `T29-CMP-BUILD`, `T29-WP` | T029-SR-001, T029-SR-024, T029-SR-025 |
| `T29-XB-2`, `T29-CMP-FIXTURE` | T029-SR-003, T029-SR-022 |
| `T29-XB-3`, `T29-CMP-ZERO` | T029-SR-004, T029-SR-012 |
| `T29-XB-4`, `T29-CMP-JOURNAL` | T029-SR-009, T029-SR-010, T029-SR-011 |
| `T29-XB-5`, `T29-CMP-PROV` | T029-SR-013, T029-SR-014, T029-SR-015 |
| `T29-XB-6`, `T29-CMP-MISMATCH` | T029-SR-005, T029-SR-008 |
| `T29-XB-7`, `T29-CMP-CONC` | T029-SR-004, T029-SR-006, T029-SR-007, T029-SR-020 |
| `T29-XB-8` | T029-SR-020, T029-SR-021 |
| `T29-XB-9` | T029-SR-002, T029-SR-022, T029-SR-023 |
| `T29-XB-10`, `T29-CMP-LEASE-DRAIN` | T029-SR-016, T029-SR-017, T029-SR-018, T029-SR-019 |

## 11. Negative cases (architecture view)

Every boundary has a declared fail-closed behaviour and a negative-case owner; the executable cases are listed in
`verification-plan.md` §5.

| Boundary | Injected defect | Negative case |
| --- | --- | --- |
| `T29-XB-1` | T029 changes a production byte, an existing test, or a later-task path | NEG-01, NEG-02, NEG-37 |
| `T29-XB-2` | a fixture re-implements or bypasses an accepted check | NEG-02, NEG-03 |
| `T29-XB-3` | a mismatch or precondition decline reaches the emitter | NEG-04, NEG-05, NEG-06, NEG-18, NEG-19 |
| `T29-XB-4` | emission precedes the durable intent, or an incomplete outcome is reported as success | NEG-13, NEG-14, NEG-15, NEG-16, NEG-17 |
| `T29-XB-5` | a differently classified or identity-less item is emitted, routed, observed, or recovered | NEG-21, NEG-22, NEG-23 |
| `T29-XB-6` | an unmapped/out-of-tolerance time is emitted, a raw clock comparison occurs, or an authority is called | NEG-11, NEG-12, NEG-26 |
| `T29-XB-7` | a queue/lease/lineage/quota bound is exceeded | NEG-07, NEG-08, NEG-09, NEG-10, NEG-27, NEG-28 |
| `T29-XB-8` | a lease race has two winners, a quota is exceeded, or repeated runs differ | NEG-08, NEG-24, NEG-31, NEG-32, NEG-33 |
| `T29-XB-9` | a new dependency, I/O, payload retention, or public-safety violation | NEG-03, NEG-34, NEG-35 |
| `T29-XB-10` | T029 implements T030–T041 | NEG-01, NEG-36 |
| Governance | a weakened requirement/test or a promoted REF-002 disposition | NEG-01, NEG-36 |
