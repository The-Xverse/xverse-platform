# T028 Architecture — Guarded Actions and the Exclusive Service-Emulation Lease

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T028 (capability 007, slice `T-STIM`) |
| Stage / role | plan → architecture |
| Revision | 1 (guarded actions and exclusive service-emulation lease) |
| Baseline revision | `c518c5e4fcb2055666db25cb62018769e7f56ae4` |
| Affected source paths | `src/xverse/xcom/include/xverse/xcom/stimulation_actions.hpp` (new), `src/xverse/xcom/src/stimulation_actions.cpp` (new), `src/xverse/xcom/CMakeLists.txt` (edit), `tests/xcom/stimulation_actions/**` (new) |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-009` validation stimulation session, `XCOM-XB-007` validation-session-to-core boundary, `XCOM-XLC-006` in-process contract, `XCOM-INV-03`/`04`/`07`/`09`/`10`); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-018` guarded injection and exclusive service-emulation lease); `docs/engineering/xcom/t009/architecture.md`; `docs/engineering/xcom/t010/detailed-design.md`; `specs/007-xcom-core/data-model.md`; `specs/007-xcom-core/contracts/validation-tool.md`; ADR-0016, ADR-0018, ADR-0019, ADR-0020 |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T028 is the **action path** of the stimulation boundary. It consumes the accepted T027 guard decision and
executes exactly one of the four declared stimulation actions — inject signal, inject message, invoke
service, emulate service — through a durable journal-before-emission seam, holds an exclusive
generation-bound service-emulation lease, and completes the session lifecycle (drain, close, revoke,
expiry, evidence-incomplete) with zero emission on every decline. It is the implementation half of
`XCOM-DU-018`; T029 is the verification matrix that closes the slice.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013/T-CORE contract + origin/diagnostic vocabulary (read-only)
   → T025 time authority + permit + session lifecycle (accepted, read-only)
   → T026 durable intent/outcome journal (present at baseline, read-only)
   → T027 fail-closed pre-emission guard (present at baseline, read-only)
   → T028 guarded injection/invocation/emulation + exclusive generation-bound lease + completion
   → T029 complete stimulation matrix → T030–T034 gateway/conformance
   → T035–T041 evidence/review/acceptance
```

T028 is an **implementation** slice: the deterministic gate requires at least one changed
`src/xverse/xcom/` path and at least one changed `tests/` path. It adds exactly one production target and
additive tests; it changes no accepted production behavior and no accepted byte of T025, T026, or T027.

## 3. Boundary and context

### 3.1 System context

```text
   ┌──────── XDL / io.xverse.xcom Profile + activation plan (read-only, T017–T019) ──────────┐
   │  declared plan: allowed interfaces/actions, schemas, service ownership, limits            │
   └─────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │ derived by the caller into the guard policy + config
   ┌──────── accepted T025/T026/T027 in-process contracts (read-only, src/xverse/xcom) ───────┐
   │  validation_session.hpp : Permit · PermitId · SessionId · PlanDigest · Timestamp ·         │
   │    ClockDomainId · Tag · Generation · Result · Diagnostic · LifecycleState · is_terminal   │
   │  stimulation_journal.hpp : StimulationIntent · StimulationOutcome · OutcomeKind ·          │
   │    JournalStatus · StimulationJournal (journal_then_emit, resolve)                          │
   │  stimulation_guard.hpp : StimulationAction · StimulationRequest · StimulationPolicy ·       │
   │    ResolvedTime · GuardOutcome · GuardReason · StimulationGuard · GuardSnapshot             │
   │  core (T-CORE) : OriginKind::validation_tool · InteractionKind · EndpointDirection          │
   └─────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │ reused read-only (no write, no redefinition)
   ┌──────────────────────── T028 action path (this slice, src/xverse/xcom) ──────────────────┐
   │  stimulation_actions.hpp/.cpp                                                              │
   │    vocabularies   ActionStatus · LeaseStatus · LeaseState · OrderingRule ·                 │
   │                   LateItemPolicy · DrainState · EmissionStatus · CompletionOutcome          │
   │    bounded values ActionPathConfig · EndpointGeneration · EmulationLease · LeaseSnapshot ·  │
   │                   PendingAction · SyntheticStimulationItem · ActionDiagnostic ·             │
   │                   ActionPathSnapshot · CompletionReport                                     │
   │    seam           ActionEmitter (host-supplied; owns transport, holds no payload)           │
   │    components     StimulationActionPath (guard + journal + queue + lineage + completion)    │
   │                   ServiceEmulationRegistry (exclusive lease table)                          │
   │    guarantee      every decline emits nothing and journals nothing; only Authorized emits   │
   └─────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │ SyntheticStimulationItem (OriginKind::validation_tool)
                                             ▼
                        host ActionEmitter → accepted T-CORE provider/route boundary (T-CORE)
                                             │
                                             ▼
                        T029 matrix · T035–T040 evidence · T039/T041 review/acceptance
```

T028 introduces no transport, listener, provider, route, or endpoint of its own. It emits a bounded,
payload-free synthetic descriptor through a host-supplied emitter seam; the accepted T-CORE provider
boundary owns realization, and the later gateway (T030–T034) owns the external IPC path. T028 authors no
normal-route item and holds the "rejection emits zero normal-route items" guarantee at the action-path
level.

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T28-XB-1` Action path vs accepted T025/T026/T027 | the action path, lease registry, queue, lineage, and completion state | the accepted permit/session lifecycle, the accepted guard, and the accepted journal | T028 consumes T025/T026/T027 read-only and never mutates a permit, session, guard tally, guard loop window, or durable journal record except through the journal's own public append/resolve surface. |
| `T28-XB-2` Authorized vs emission | the guard `Authorized` decision | the host emission seam | Only `Authorized` reaches the emitter; every other guard decision and every precondition decline emits nothing and journals nothing. |
| `T28-XB-3` Lease exclusivity | one exclusive lease per endpoint generation and per `(endpoint, session)` | a second owner or a foreign/superseded generation, session, or plan | Acquisition is atomic; a conflict or identity mismatch is rejected with no mutation and no emission. |
| `T28-XB-4` Journal-before-emission | the durable intent frame | the emitter invocation | The intent is durable before the emitter runs exactly once; an intent without a durable outcome is `EvidenceIncomplete` and is never reported as success. |
| `T28-XB-5` Synthetic provenance | the `OriginKind::validation_tool` classification and the exact identity | any relabelling, drop, or inference of provenance | Every emitted item carries the synthetic classification plus the tool/session/permit/plan/request/correlation/causal identity. |
| `T28-XB-6` Scheduling vs raw clocks | a caller-resolved time in the permit validity domain | two raw mismatched clock domains and wall-clock scheduling | The action path never compares or orders unmapped clocks (`XCOM-INV-09`), performs no authority mutation, and fails closed on an unmapped/out-of-tolerance resolution. |
| `T28-XB-7` Bounded queue/lease/lineage | the finite pending queue, lease table, and lineage window | an unbounded queue, retry, wait, or growth | On a bound the action path fails closed; a decline mutates no queue, lease, or lineage entry. |
| `T28-XB-8` Lifecycle completion | bounded drain/close/revoke/expiry/evidence-incomplete completion | the accepted T025 session transition itself | T028 completes its owned pending actions and leases for a caller-supplied session state; the host applies the T025 lifecycle transition. |
| `T28-XB-9` Repository vs environment | committed source, tests, work products | admitted build inputs, host environment, payloads | Committed files are public-safe and offline; T028 performs no I/O, network, ambient/secret, dynamic-load, subprocess, or legacy access and retains/logs no payload. |
| `T28-XB-10` T028 scope vs later tasks | the guarded action path and lease | the gateway and the complete matrix | T028 implements no gateway, Protocol Buffers/gRPC, separate process, or complete matrix; it delegates transport to the host seam and the accepted provider boundary. |

### 3.3 Prohibited elements (must remain absent)

No transport, listener, provider composition, route, endpoint, tap, observation record, or routed item
authored by T028; no TCP listener, external network peer, discovery, package manager/registry, ambient or
secret configuration, dynamic plugin loading, process execution, filesystem I/O, or legacy
repository/binary access; no domain-specific primitive; no payload/value logging, retention, decoder,
redaction profile, or unrestricted log; no tool gateway, Protocol Buffers/gRPC, IPC, or separate-process
client; no re-implementation, weakening, or bypass of the accepted guard or journal; no modification of
T025/T026/T027 accepted source, or of any existing test/target/label/command/value; no new admitted
dependency; no unbounded queue/table/thread/retry/wait; no host callback invoked under an action-path or
lease lock; no wall-clock verdict in tests; no time-authority mutation by the action path. No rewrite or
weakening of an accepted ADR, requirement, contract, schema, register, or REF-002 disposition. These
inherit the T007 global prohibitions, the T011 envelope, the T012 build contract, ADR-0019, ADR-0020, and
the constitution.

## 4. Components

Each component maps to a unit group in `unit-specifications.md`. `T28-*` names are local to this document;
the accepted `XCOM-DU-018`/`XCOM-CMP-009`/`XCOM-XB-007`/`XCOM-XLC-006` identifiers are the authorized
units/contracts.

### 4.1 New production components (design unit `XCOM-DU-018`, component `XCOM-CMP-009`)

- **`T28-CMP-VOCAB` Closed vocabularies** (`stimulation_actions.hpp`): `ActionStatus`, `LeaseStatus`,
  `LeaseState`, `OrderingRule`, `LateItemPolicy`, `DrainState`, `EmissionStatus`, `CompletionOutcome`, with
  stable names and precedence. Reuses the accepted T027 `StimulationAction`/`StimulationActionMask`/
  `GuardOutcome`/`GuardReason`, the accepted T026 `OutcomeKind`/`JournalStatus`, and the accepted T-CORE
  `OriginKind` read-only.
- **`T28-CMP-MODEL` Bounded values** (`stimulation_actions.hpp`): `ActionPathConfig`, `EndpointGeneration`,
  `EmulationLease`, `LeaseSnapshot`, `PendingAction`, `SyntheticStimulationItem`, `ActionDiagnostic`,
  `ActionPathSnapshot`, `CompletionReport`. Bounded, payload-free, self-checking at construction/open.
- **`T28-CMP-PATH` Action path core** (`stimulation_actions.hpp/.cpp`): the `open` guard binding, the
  bounded precondition checks, the per-request guard evaluation, the journal-before-emission emission, the
  bounded pending queue, the bounded reinjection lineage window, the counters, and the non-mutation
  guarantee.
- **`T28-CMP-LEASE` Exclusive lease registry** (`stimulation_actions.hpp/.cpp`): `ServiceEmulationRegistry`,
  the atomic `(endpoint, generation)` lease table, conflict/identity/expiry handling, and the
  release/quarantine paths.
- **`T28-CMP-EMIT` Emission seam adapter** (`stimulation_actions.cpp`): the bounded internal adapter that
  builds the `SyntheticStimulationItem`, invokes the host `ActionEmitter` exactly once through the accepted
  T026 `journal_then_emit` callback, maps the `EmissionStatus` into a bounded `StimulationOutcome`, and
  never retains or logs the payload view.
- **`T28-CMP-COMPLETE` Lifecycle completion** (`stimulation_actions.cpp`): `drain`, `close`, `revoke`,
  `expire`, and `mark_evidence_incomplete`, each producing a bounded deterministic `CompletionReport`.

### 4.2 Consumed components (read-only)

- **`T28-CMP-T025`** (`XCOM-XLC-006`, `XCOM-DU-014`/`-015`) — `Permit` (immutable identity, tags, validity,
  quotas, `permit_id`, `allows`), `PermitId`, `SessionId`, `PlanDigest`, `Timestamp`, `ClockDomainId`,
  `Generation`, `Tag`, `Result`, `Diagnostic`, `LifecycleState`, `is_terminal`: consumed read-only and
  **not modified**.
- **`T28-CMP-T026`** (`XCOM-DU-016`) — `StimulationJournal`, `StimulationIntent`, `StimulationOutcome`,
  `OutcomeKind`, `JournalStatus`, `EmissionCallback`: consumed read-only and **not modified**; it owns the
  durable intent/outcome ordering and the evidence-incomplete orphan surface.
- **`T28-CMP-T027`** (`XCOM-DU-017`) — `StimulationGuard`, `StimulationPolicy`, `StimulationRequest`,
  `ResolvedTime`, `GuardOutcome`, `GuardReason`, `GuardDiagnostic`, `GuardSnapshot`: consumed read-only and
  **not modified**; it owns the fail-closed pre-emission decision.
- **`T28-CMP-CORE`** (`XCOM-CMP-004`, `XCOM-DU-001`…`-005`) — `OriginKind`/`OriginKind::validation_tool`,
  `InteractionKind`, and `EndpointDirection` from the accepted core headers: consumed read-only and **not
  redefined**.
- **`T28-CMP-BUILD`** (T012) — the subtree warning-as-error rule, sanitizer selection, and runtime-target
  inventory: extended additively by one target.

### 4.3 Work-product components

- **`T28-WP`** — the T028 repository-owned work-product set (`requirements.md`, `architecture.md`,
  `detailed-design.md`, `unit-specifications.md`, `verification-plan.md`, `implementation.md`,
  `internal-review.json`, and `reports/xcom-queue/t028-package.json`).

## 5. Data flow (ordered)

1. **Open and bind.** The host constructs the action path from a bounded `ActionPathConfig`, a reference to
   an opened accepted T026 `StimulationJournal`, a reference to a `ServiceEmulationRegistry`, and a
   reference to a host `ActionEmitter` (all non-owning and outliving the action path). `open(permit,
   policy)` validates and binds the accepted T027 guard; an invalid or inconsistent guard policy leaves the
   action path closed and authorizes nothing.
2. **Receive a request.** The caller supplies a bounded accepted T027 `StimulationRequest`, the current
   session state (read-only `LifecycleState`), a caller-resolved `ResolvedTime` in the permit validity
   domain, and an optional bounded payload view.
3. **Check bounded preconditions.** The action path checks its own open state, declared bounds, the session
   state, and — for a scheduled or emulating request — its pending-queue or lease capacity **before** any
   guard evaluation, so that a capacity decline consumes no accepted guard quota and journals nothing.
4. **Evaluate the accepted guard once.** `StimulationGuard::authorize` is called exactly once. A
   `Rejected`/`Failed` decision returns the matching `ActionStatus` with the guard reason preserved, appends
   no journal record, and acquires no lease.
5. **Acquire the exclusive lease for emulation.** For `EmulateService`, `ServiceEmulationRegistry::acquire`
   atomically checks and inserts a lease bound to the exact session, endpoint, generation, and plan digest;
   a conflict or an identity mismatch returns `LeaseConflict`/the matching lease status with no mutation and
   no emission. Service invocation requires an authorized service action but acquires no emulation lease.
6. **Journal the intent, then emit once.** For an authorized immediate or due action the action path builds
   the bounded payload-free `StimulationIntent`, calls the accepted `StimulationJournal::journal_then_emit`
   with the bounded adapter callback, which builds the `SyntheticStimulationItem`
   (`OriginKind::validation_tool`) and invokes the host `ActionEmitter` exactly once with the call-scoped
   payload view. The action path records the explicit outcome returned through the journal.
7. **Classify the result.** A journal `Ok` with a host `Delivered` emission maps to
   `ActionStatus::Emitted`; a host `Rejected`/`Unavailable` outcome is durable but maps to the distinct
   non-success `EmissionRejected`/`EmissionUnavailable`; an intent without a durable outcome maps to
   `ActionStatus::EvidenceIncomplete` and is never reported as success; a journal rejection maps to the
   matching non-emitting status.
8. **Schedule bounded work.** An authorized scheduled action is placed in the bounded pending queue ordered
   by the declared `OrderingRule`; the queue is drained by bounded `drain` calls under the declared
   `LateItemPolicy`. A full queue fails closed with no emission and no journal.
9. **Bound reinjection.** On emission the request lineage advances in the bounded lineage window; a request
   whose causal parent is already present is `Rejected` with no emission and no journal.
10. **Complete the lifecycle.** `drain` completes due pending actions within the bounded step budget;
    `close` drains then releases every held lease; `revoke` and `expire` cancel every pending action with
    zero emission and release or quarantine every held lease; `mark_evidence_incomplete` surfaces every
    intent without a durable outcome. Every completion is deterministic, bounded, and free of wall-clock
    dependence.
11. **Never mutate on a decline.** A precondition decline, a guard decline, a lease conflict, a late
    rejection, a cancelled action, and an over-capacity fail-closed leave the accepted guard state, the
    lease table, the pending queue, the lineage window, and the durable journal unchanged in the declined
    dimension, and emit nothing.

## 6. Interfaces

T028 exposes one new in-process C++20 contract (`T28-IF-1`) and consumes the accepted `XCOM-XLC-006`
contract plus the accepted T026/T027 vocabulary and the accepted core origin/interaction vocabulary
read-only.

### 6.1 `T28-IF-1` guarded action path, exclusive lease, and completion (new, in-process C++20)

| Element | Contract |
| --- | --- |
| `enum class ActionStatus` | closed action-path outcome vocabulary (`Emitted`, `Rejected`, `Failed`, `LeaseConflict`, `Queued`, `Cancelled`, `Expired`, `EvidenceIncomplete`, `CapacityExhausted`, `NotActive`, `RejectedConfiguration`, `EmissionRejected`, `EmissionUnavailable`) |
| `enum class LeaseStatus` | closed lease-operation vocabulary (`Ok`, `Conflict`, `NotFound`, `NotHeld`, `AlreadyReleased`, `SessionMismatch`, `GenerationMismatch`, `PlanMismatch`, `Expired`, `Quarantined`, `CapacityExhausted`, `RejectedConfiguration`) |
| `enum class LeaseState` | closed lease-state vocabulary (`None`, `Active`, `Released`, `Quarantined`, `Expired`) |
| `enum class OrderingRule` | closed scheduled-ordering vocabulary (`ScheduledThenArrival`, `Arrival`) |
| `enum class LateItemPolicy` | closed late-item vocabulary (`RejectLate`, `DiscardLate`) |
| `enum class DrainState` | closed drain-state vocabulary (`Idle`, `Draining`, `Drained`, `Cancelled`) |
| `enum class EmissionStatus` | closed emitter-seam vocabulary (`Delivered`, `Rejected`, `Unavailable`) |
| `enum class CompletionOutcome` | closed completion vocabulary (`None`, `Drained`, `Closed`, `Revoked`, `Expired`, `EvidenceIncomplete`) |
| `struct ActionPathConfig` | bounded declared configuration: max active leases, max pending actions, drain step budget, ordering rule, late-item policy, max payload bytes, tool tag |
| `struct EndpointGeneration` | bounded lease key: session id, endpoint tag, generation, plan digest |
| `struct EmulationLease` | bounded lease value: key, owner request id, acquired/expiry time, domain, state |
| `struct SyntheticStimulationItem` | bounded emitted descriptor: `OriginKind origin`, the accepted `StimulationIntent` identity/metadata |
| `class ActionEmitter` | host emission seam: `emit(const SyntheticStimulationItem&, std::span<const std::byte>)` returning `EmissionStatus`; non-owning, must outlive the action path |
| `class ServiceEmulationRegistry` | `precheck` (non-mutating classification), `acquire`, `release`, `quarantine`, `expire_elapsed`, `holds`, `state_of`, `snapshot`; non-copyable/non-movable, `internally-synchronized` |
| `class StimulationActionPath` | `open(const Permit&, const StimulationPolicy&)`, `execute(const StimulationRequest&, LifecycleState, const ResolvedTime&, std::span<const std::byte>, ActionDiagnostic&)`, `drain`, `close`, `revoke`, `expire`, `mark_evidence_incomplete`, `snapshot`, `is_open`; non-copyable/non-movable, `internally-synchronized` |

Ownership/lifetime: `session-issued-handle`; only an action path opened from the session's immutable permit
may execute, and the action path is `session-scoped`. The lease registry is `endpoint-generation`-scoped:
a lease is valid only for the endpoint generation under which it was acquired. Thread-safety:
`internally-synchronized` with one mutex per action path and one per lease registry; the host emitter is
invoked without either lock held; there is no callback under a lock.

### 6.2 Consumed contracts (read-only)

| Interface | Contract consumed (unchanged) |
| --- | --- |
| `xverse::xcom::validation::{Permit, PermitId, SessionId, PlanDigest, Timestamp, ClockDomainId, Generation, Tag, Result, Diagnostic, LifecycleState, is_terminal}` | accepted T025 identity/lifecycle/diagnostic vocabulary, used read-only and never redefined |
| `xverse::xcom::validation::{StimulationJournal, StimulationIntent, StimulationOutcome, OutcomeKind, JournalStatus}` | accepted T026 durable intent/outcome ordering and evidence-incomplete surface, used read-only |
| `xverse::xcom::validation::{StimulationGuard, StimulationPolicy, StimulationRequest, ResolvedTime, GuardOutcome, GuardReason, GuardDiagnostic}` | accepted T027 fail-closed pre-emission decision, used read-only |
| `xverse::xcom::{OriginKind, InteractionKind, EndpointDirection}` | accepted T-CORE origin/interaction vocabulary, used read-only and never redefined |
| `xverse::xcom::validation::TimeAuthority` | the accepted mapping/tolerance mechanism; the caller resolves the request time with it (no action-path call, no mutation) |

## 7. Concurrency and resource bounds

| Aspect | T028 decision |
| --- | --- |
| Writers | one declared logical writer per action path and per lease registry; `execute`, `open`, and the completion operations serialize under one mutex each |
| Callbacks | exactly one host emitter call per authorized emission, invoked **outside** the action-path and lease-registry locks; no callback under a lock |
| Threads in tests | ≤ 4, and only in the bounded deterministic-concurrency cases |
| Pending queue | ≤ `max_pending_actions`; a full queue fails closed before the guard is evaluated |
| Active leases | ≤ `max_active_leases`; an over-capacity acquisition fails closed |
| Lineage window | ≤ a declared maximum; never grows past its declared depth |
| Drain budget | ≤ `max_drain_steps` per `drain` call; no unbounded loop, retry, or wait |
| Payload view | ≤ `max_payload_bytes`; forwarded to the emitter only, retained/logged nowhere |
| Values | every bounded value has a compile-time size bound; no payload/address/free-form member |
| Iterations | finite, declared loop counts; no unbounded loop, retry, or wait |
| Wall-clock | no case depends on wall-clock timing for its verdict; scheduling uses caller-supplied time |
| I/O | none; the action path performs no file, socket, authority, or environment access |
| Production footprint | one new static library and additive tests; no other production behavior changes |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Fail closed | a precondition, guard, lease, late-policy, or completion decline emits nothing and journals nothing; only `Authorized` emits | T028-STK-002, T028-SR-006, T028-SR-017; CHK-07, CHK-21 |
| Exclusive emulation | atomic lease acquisition bound to the exact session/endpoint/generation/plan; conflict is rejected | T028-SR-009, T028-SR-010, T028-SR-011; CHK-10, CHK-11, CHK-12 |
| Journal-before-emission | intent durable before the single emitter call; an intent without an outcome is `EvidenceIncomplete` | T028-SR-007; CHK-08, CHK-16 |
| Synthetic provenance | every emitted item carries `OriginKind::validation_tool` and the exact identity | T028-SR-008; CHK-09 |
| Loop bounding | bounded emission-time lineage window; a prohibited reinjection is rejected | T028-SR-013; CHK-14 |
| Scheduling declared | declared ordering rule and late-item policy; bounded drain; immediate labeled | T028-SR-014, T028-SR-015; CHK-15, CHK-13 |
| Lifecycle completion | bounded deterministic drain/close/revoke/expiry/evidence-incomplete reports | T028-SR-016; CHK-16 |
| Zero mutation on decline | guard, lease, queue, lineage, and journal unchanged in the declined dimension | T028-SR-017; CHK-21, NEG-25…NEG-27 |
| Bounded resources | finite queue, lease table, lineage window, drain budget, and iterations; fail-closed on a bound | T028-SR-004, T028-SR-014, T028-SR-019; CHK-05, CHK-18 |
| No raw-clock comparison | caller-resolved time in the permit validity domain; unmapped/out-of-tolerance fails closed | T028-SR-012, T028-SR-015; CHK-13, NEG-23 |
| Determinism | closed vocabularies; same sequence → same status/state/outcome/snapshot | T028-SR-018; CHK-17 |
| Concurrency | one mutex per component; no callback under a lock; bounded threads/iterations | T028-SR-019; CHK-18, NEG-29 |
| Offline safety | standard library plus accepted headers; no I/O/network/ambient/secret/legacy; no payload retention | T028-SR-020; CHK-19, CHK-20 |
| Public safety | no secret, private address, real payload, or host path in committed files/evidence | T028-SR-021; CHK-21 |
| Documentation | Doxygen ownership/lifetime/thread-safety/failure on every public declaration | T028-SR-022; CHK-22 |
| Governance | registers re-validated; REF-002 unchanged; STIM-005/006/008 implemented; STIM-003/009 partial | T028-SR-023, T028-SR-024; CHK-23, CHK-24 |

## 9. Consistency and constraints

- **Dependency direction preserved.** T028 consumes the accepted T025 in-process contract, the accepted
  T026 journal, the accepted T027 guard, and the accepted T-CORE origin vocabulary; it introduces no
  dependency on a later slice, adapter, gateway, or legacy repository.
- **Domain neutrality preserved.** The unit uses only generic stimulation vocabulary (action, request,
  policy, lease, generation, session, queue, drain, ordering, late item, clock domain, quota, provenance);
  no automotive, product, protocol, or configuration primitive is introduced.
- **XDL centrality preserved.** T028 neither parses nor authors XDL; it consumes bounded identity values
  that the accepted plan already binds and cross-checks the plan digest against the immutable permit and the
  guard policy.
- **Logical/physical separation preserved.** Requests and leases carry logical identity, plan digest, clock
  domain, and bounded tags only; no address, transport, or environment identity enters a decision.
- **Synthetic origin preserved.** The emitted descriptor always carries `OriginKind::validation_tool` and
  the exact bound identity; T028 exposes no path to emit a differently classified item.
- **Ownership preserved.** Only T028 source/test paths, the shared build files, the T028 work products, the
  recorded derived status projection, and the T028 checkbox change; T025/T026/T027 accepted bytes are
  consumed read-only and preserved.
- **Maturity preserved.** The action path stays a bounded prototype; the gateway, the complete matrix,
  sanitizer/static/Doxygen execution, benchmarks, and acceptance remain with T029–T041.
- **Scope preserved.** T028 authors no transport, route, provider, endpoint, tap, or routed item; the host
  emitter and the accepted provider boundary own realization, and the gateway remains T030–T034.

## 10. Traceability

| Architecture element | T028 requirements |
| --- | --- |
| `T28-XB-1`, `T28-CMP-T025`, `T28-CMP-T026`, `T28-CMP-T027`, `T28-CMP-CORE` | T028-SR-002, T028-SR-007, T028-SR-012 |
| `T28-XB-2`, `T28-CMP-PATH` | T028-SR-005, T028-SR-006 |
| `T28-XB-3`, `T28-CMP-LEASE` | T028-SR-009, T028-SR-010, T028-SR-011 |
| `T28-XB-4`, `T28-CMP-EMIT` | T028-SR-007 |
| `T28-XB-5` | T028-SR-008 |
| `T28-XB-6` | T028-SR-012, T028-SR-015 |
| `T28-XB-7` | T028-SR-004, T028-SR-013, T028-SR-014, T028-SR-019 |
| `T28-XB-8`, `T28-CMP-COMPLETE` | T028-SR-016 |
| `T28-XB-9`, `T28-WP` | T028-SR-020, T028-SR-021, T028-SR-022 |
| `T28-XB-10` | T028-SR-023 |
| `T28-CMP-VOCAB`, `T28-CMP-MODEL` | T028-SR-003, T028-SR-004, T028-SR-018 |
| `T28-CMP-BUILD` | T028-SR-001, T028-SR-024 |

## 11. Negative cases (architecture view)

Every boundary has a declared fail-closed behaviour and a negative-case owner; the executable cases are
listed in `verification-plan.md` §5.

| Boundary | Injected defect | Negative case |
| --- | --- | --- |
| `T28-XB-1` | T028 mutates accepted T025/T026/T027 state or re-implements a guard/journal check | NEG-01, NEG-02, NEG-35 |
| `T28-XB-2` | a non-authorized decision reaches the emitter | NEG-06, NEG-27 |
| `T28-XB-3` | a second owner or a foreign/superseded generation, session, or plan acquires a lease | NEG-09, NEG-10, NEG-11, NEG-12, NEG-13 |
| `T28-XB-4` | emission precedes the durable intent, or an incomplete outcome is reported as success | NEG-07, NEG-25 |
| `T28-XB-5` | a differently classified or identity-less item is emitted | NEG-08 |
| `T28-XB-6` | an unmapped/out-of-tolerance time is emitted, or a raw clock comparison occurs | NEG-14, NEG-19, NEG-23, NEG-24 |
| `T28-XB-7` | a queue/lease/lineage bound is exceeded, or a decline mutates state | NEG-16, NEG-17, NEG-18, NEG-26 |
| `T28-XB-8` | a completion operation emits, or fails to cancel/release/quarantine | NEG-20, NEG-21, NEG-22 |
| `T28-XB-9` | a new dependency, I/O, payload retention, or public-safety violation | NEG-02, NEG-03, NEG-05, NEG-30, NEG-31 |
| `T28-XB-10` | T028 implements T029 or a later task | NEG-01, NEG-32 |
| Vocabularies/values | an open vocabulary, an unstable precedence, or a payload-bearing value | NEG-03, NEG-04, NEG-28 |
| Concurrency | an unbounded thread/iteration/wait, a callback under a lock, or a lease race with two winners | NEG-29, NEG-36 |
| Governance | a weakened requirement/test or a promoted REF-002 disposition | NEG-01, NEG-32 |
