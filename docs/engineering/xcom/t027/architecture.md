# T027 Architecture — Fail-Closed Pre-Emission Guard

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T027 (capability 007, slice `T-STIM`) |
| Stage / role | plan → architecture |
| Revision | 1 (fail-closed pre-emission guard) |
| Baseline revision | `bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f` |
| Affected source paths | `src/xverse/xcom/include/xverse/xcom/stimulation_guard.hpp` (new), `src/xverse/xcom/src/stimulation_guard.cpp` (new), `src/xverse/xcom/CMakeLists.txt` (edit), `tests/xcom/stimulation_guard/**` (new) |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-009` validation stimulation session, `XCOM-XB-007` fail-closed pre-emission guard, `XCOM-XLC-006` in-process contract, `XCOM-INV-04`/`07`/`09`/`10`); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-017` fail-closed pre-emission guard); `docs/engineering/xcom/t009/architecture.md`; `docs/engineering/xcom/t010/detailed-design.md`; `specs/007-xcom-core/data-model.md`; `specs/007-xcom-core/contracts/validation-tool.md`; ADR-0016, ADR-0018, ADR-0019, ADR-0020 |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T027 is the **pre-emission authorization gate** of the stimulation boundary. It decides, fail-closed,
whether one declared stimulation request may enter a route, and it guarantees that a rejection or a failed
evaluation mutates no operational state and emits no normal-route item. It is the last dependency before
the action paths (T028) and closes the guard-level half of the `T-STIM` mismatch evidence.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013/T-CORE contract + diagnostic vocabulary (read-only)
   → T025 time authority + permit + session lifecycle (accepted, read-only)
   → T026 durable intent/outcome journal (present at baseline, read-only)
   → T027 fail-closed pre-emission guard (this document)
   → T028 guarded injection/invocation/exclusive service emulation
   → T029 full stimulation matrix → T030–T034 gateway/conformance
   → T035–T041 evidence/review/acceptance
```

T027 is an **implementation** slice: the deterministic gate requires at least one changed
`src/xverse/xcom/` path and at least one changed `tests/` path. It adds exactly one production target and
additive tests; it changes no accepted production behavior and no accepted byte of T025 or T026.

## 3. Boundary and context

### 3.1 System context

```text
   ┌──────── XDL / io.xverse.xcom Profile + activation plan (read-only, T017–T019) ──────────┐
   │  declared plan: allowed interfaces/actions, schemas, service ownership, limits            │
   └─────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │ derived by the caller into a bounded policy value
   ┌──────── accepted T025 in-process contract (read-only, src/xverse/xcom) ──────────────────┐
   │  validation_session.hpp : Permit · PermitId · SessionId · PlanDigest · Tag · Result ·     │
   │  Diagnostic · LifecycleState · is_terminal · TimeAuthority · Action · ValidationSession   │
   │  core contract.hpp : InteractionKind · EndpointDirection (read-only)                       │
   └─────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │ reused read-only (no write, no redefinition)
   ┌──────────────────────────── T027 guard (this slice, src/xverse/xcom) ────────────────────┐
   │  stimulation_guard.hpp/.cpp                                                               │
   │    vocabularies   StimulationAction · GuardOutcome · GuardReason · GuardStatus             │
   │    bounded values StimulationPolicy · StimulationRequest · SchemaKey · ServiceOwner ·      │
   │                   ResolvedTime · GuardDiagnostic · GuardSnapshot                           │
   │    check order    identity → lifecycle → schema → direction/interaction → target → action  │
   │                   → ownership → quota → loop → time → Authorized + commit                  │
   │    tallies        per-session budget · per-window budget · bounded loop window             │
   │    guarantee      Rejected/Failed mutate no tally/loop and expose no emission path         │
   └─────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │ decision consumed by (T028)
                                             ▼
                        T028 injection/invocation/emulation + exclusive lease
                                             │
                                             ▼
                        T029 full matrix · T035–T040 evidence · T039/T041 review/acceptance
```

T027 introduces no route, item, provider, tap, lease, gateway, or emission path: it emits nothing, and
`FR-018` is satisfied by the guard decision alone. `XCOM-XB-007` ("rejection emits zero normal-route
items") is realized at the guard level by exposing no emission surface; the end-to-end route proof belongs
to T028/T029.

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T27-XB-1` Guard vs accepted T025/T026 | the guard and its bounded tallies | the accepted permit, session lifecycle, time authority, and journal | T027 consumes T025/T026 types read-only and never mutates a permit, session, authority baseline, consumed set, or journal record. |
| `T27-XB-2` Decision vs emission | the fail-closed decision | the normal route and the T028 action path | The guard exposes no emission/callback/route/injection/invocation/emulation/lease path; a non-`Authorized` decision proceeds to no emission. |
| `T27-XB-3` Authorization vs identity | the bound permit/session/plan identity | a foreign or absent request identity | A request whose session, permit, or plan identity differs from the bound permit is rejected before any mutation. |
| `T27-XB-4` Lifecycle vs request | the live session state supplied by the caller | declared/armed/closing/closed/expired/revoked/evidence-incomplete sessions | Only an `active` session authorizes; revoked/expired/non-active requests are rejected with zero mutation. |
| `T27-XB-5` Declared policy vs request | the bounded declared stimulation policy | the request's schema/direction/interaction/target/action/ownership | A declaration not present in or inconsistent with the declared policy is rejected; the policy is cross-checked against the immutable permit at open. |
| `T27-XB-6` Quota/loop vs unbounded state | the finite per-session, per-window, and loop-window bounds | an unbounded tally, window, retry, or wait | On a bound the guard fails closed; a rejection mutates no tally or window; the loop window never grows past its declared depth. |
| `T27-XB-7` Time vs raw clocks | a caller-resolved time in the permit validity domain | two raw mismatched clock domains | The guard never compares or orders unmapped clocks (`XCOM-INV-09`), performs no authority mutation, and fails closed (`Failed`) on an absent/unmapped/out-of-tolerance resolution. |
| `T27-XB-8` Repository vs environment | committed source, tests, work products | admitted build inputs, host environment | Committed files are public-safe and offline; the guard performs no I/O, network, ambient/secret, dynamic-load, subprocess, or legacy access. |
| `T27-XB-9` T027 scope vs later tasks | the guard decision | the T028 lease/action paths and the T029 matrix | T027 performs no injection, invocation, emulation, lease, drain, close, revoke, expiry, routing, or observation behavior. |

### 3.3 Prohibited elements (must remain absent)

No emission, route, item, provider, endpoint, tap, observation record, injection, invocation, service
emulation, or exclusive lease. No TCP listener, external network peer, discovery, package manager/registry,
ambient or secret configuration, dynamic plugin loading, process execution, filesystem I/O, or legacy
repository/binary access. No domain-specific primitive. No payload/value logging, decoder, redaction
profile, or unrestricted log. No tool gateway, Protocol Buffers/gRPC, IPC, or separate-process client. No
modification of T025 or T026 accepted source, or of any existing test/target/label/command/value. No new
admitted dependency. No unbounded queue/table/thread/retry/wait, no callback under an X-COM lock, no
wall-clock verdict in tests, no time-authority mutation by the guard. No rewrite or weakening of an accepted
ADR, requirement, contract, schema, register, or REF-002 disposition. These inherit the T007 global
prohibitions, the T011 envelope, the T012 build contract, ADR-0019, ADR-0020, and the constitution.

## 4. Components

Each component maps to a unit group in `unit-specifications.md`. `T27-*` names are local to this document;
the accepted `XCOM-DU-017`/`XCOM-CMP-009`/`XCOM-XLC-006` identifiers are the authorized units/contracts.

### 4.1 New production components (design unit `XCOM-DU-017`, component `XCOM-CMP-009`)

- **`T27-CMP-VOCAB` Closed vocabularies** (`stimulation_guard.hpp`): `StimulationAction` with a defined-bit
  mask and stable names, `GuardOutcome` (`Authorized`/`Rejected`/`Failed`), `GuardReason` (one enumerator
  per failing check plus `None`), and `GuardStatus` for the open/precondition boundary. Reuses the accepted
  core `InteractionKind`/`EndpointDirection` and T025 `Result`/`Diagnostic` read-only.
- **`T27-CMP-MODEL` Bounded values** (`stimulation_guard.hpp`): `StimulationPolicy` (declared
  session-scoped policy), `StimulationRequest` (one declared request), `SchemaKey`, `ServiceOwner`,
  `ResolvedTime`, `GuardDiagnostic`, `GuardSnapshot`. Bounded, payload-free, self-checking at construction.
- **`T27-CMP-GUARD` Guard core** (`stimulation_guard.hpp/.cpp`): the `open` policy validation, the
  deterministic check order, `authorize`, the bounded per-session/per-window tallies, the bounded
  loop-detection window, and the non-mutation guarantee.
- **`T27-CMP-DECIDE` Decision functions** (`stimulation_guard.cpp`): the pure check predicates
  (identity/lifecycle/schema/direction/interaction/target/action/ownership), the closed
  action→interaction→direction table, and the time-policy / quota / loop predicates.
- **`T27-CMP-COMMIT` Bounded commit** (`stimulation_guard.cpp`): the single mutex-protected
  check-then-commit that advances the tallies and loop window only on `Authorized`.

### 4.2 Consumed components (read-only)

- **`T27-CMP-T025`** (`XCOM-XLC-006`, `XCOM-DU-014`/`-015`) — `Permit` (immutable identity, tags, validity,
  allowed lifecycle actions, quotas, `permit_id`, `allows`), `PermitId`, `SessionId`, `PlanDigest`,
  `Timestamp`, `ClockDomainId`, `Tag`, `Result`, `Diagnostic`, `LifecycleState`, `is_terminal`,
  `TimeAuthority`: consumed read-only and **not modified**.
- **`T27-CMP-CORE`** (`XCOM-CMP-004`, `XCOM-DU-001`…`-005`) — the accepted `InteractionKind` and
  `EndpointDirection` vocabulary from `contract.hpp`: consumed read-only and **not redefined**.
- **`T27-CMP-JOURNAL`** (T026 `XCOM-DU-016`) — not called or modified by T027; the unknown/`Failed` outcome
  is recorded by the T028 action path through the accepted journal.
- **`T27-CMP-BUILD`** (T012) — the subtree warning-as-error rule, sanitizer selection, and runtime-target
  inventory: extended additively by one target.

### 4.3 Work-product components

- **`T27-WP`** — the T027 repository-owned work-product set (`requirements.md`, `architecture.md`,
  `detailed-design.md`, `unit-specifications.md`, `verification-plan.md`, `implementation.md`,
  `internal-review.json`, and `reports/xcom-queue/t027-package.json`).

## 5. Data flow (ordered)

1. **Open and validate the policy** — the host constructs the guard from an immutable `Permit` and a
   bounded `StimulationPolicy`. The guard validates the policy bounds (non-zero, ≤ declared maxima) and its
   consistency with the permit (`plan_digest`, interface tag, target, validity domain) at open; an invalid
   or inconsistent policy is `RejectedConfiguration` and the guard authorizes nothing.
2. **Receive a request and session state** — the caller supplies a bounded `StimulationRequest`, the current
   session state (a bounded `LifecycleState` value read from the accepted T025 session), and a bounded
   `ResolvedTime` produced by the caller from the accepted `TimeAuthority`.
3. **Check identity and lifecycle** — session/permit/plan identity must equal the bound permit
   (`PermitMismatch`); the lifecycle must be `active` (else `Revoked`/`Expired`/`NotActive`). All reject with
   no mutation.
4. **Check schema, direction, interaction, target, and action** — the schema must be a declared member of
   the bounded allowed-schema table; the `(action, interaction, direction)` triple must be consistent with
   the closed table and admissible by the policy; the target/interface tags must equal the permit; the
   action must be a defined single bit (a zero, composite, or out-of-vocabulary action is
   `RejectedConfiguration` at rank 1) and declared allowed (else `ActionMismatch`). Each mismatch rejects
   with its reason and no mutation.
5. **Check service ownership** — a service invocation/emulation must name a declared owner and generation
   matching the policy; a missing, mismatched, or ambiguous declaration is `OwnershipConflict`, no mutation.
6. **Check quota and loop** — the per-session and per-window tallies must admit one more authorized action;
   the request's causal parent must not already be present in the bounded loop-detection window. Exhaustion
   is `QuotaExhausted`; a prohibited reinjection is `LoopBound`; both mutate nothing.
7. **Check the time policy** — a scheduled request must have a valid declared clock domain and a resolution
   equal to `Result::Ok` in the permit validity domain (else `Failed`, `TimeUnmapped`); the resolved value
   must lie in the half-open permit validity interval (else `Rejected`, `TimeOutOfWindow`); an immediate
   request must be explicitly labeled and is interpreted in the permit validity domain.
8. **Authorize and commit once, under the mutex** — only when every check passes does the guard advance the
   per-session and per-window tallies and record the request lineage in the loop window, then return
   `Authorized`. The commit is atomic with the checks under the one per-guard mutex, so a concurrent
   evaluation sees a deterministic total order and never exceeds a declared bound.
9. **Never mutate on rejection** — `Rejected` and `Failed` return a bounded diagnostic and leave every tally,
   the loop window, the bound permit, and the bound policy unchanged; the guard performs no I/O, no
   authority call, and no emission.

## 6. Interfaces

T027 exposes one new in-process C++20 contract (`T27-IF-1`) and consumes the accepted `XCOM-XLC-006`
contract and the accepted core interaction vocabulary read-only.

### 6.1 `T27-IF-1` fail-closed pre-emission guard (new, in-process C++20)

| Element | Contract |
| --- | --- |
| `enum class StimulationAction` | closed, single-bit action vocabulary (`InjectSignal`, `InjectMessage`, `InvokeService`, `EmulateService`) with a defined-bit mask and stable names |
| `enum class GuardOutcome` | closed decision vocabulary (`Authorized`, `Rejected`, `Failed`) |
| `enum class GuardReason` | closed failing-check vocabulary (`None`, `RejectedConfiguration`, `PermitMismatch`, `Revoked`, `Expired`, `NotActive`, `SchemaMismatch`, `DirectionMismatch`, `InteractionMismatch`, `TargetMismatch`, `ActionMismatch`, `OwnershipConflict`, `QuotaExhausted`, `LoopBound`, `TimeUnmapped`, `TimeOutOfWindow`) |
| `enum class GuardStatus` | closed open/precondition vocabulary (`Ok`, `RejectedConfiguration`, `NotOpen`) |
| `struct StimulationPolicy` | bounded declared policy: plan digest, interface tag, target, validity domain, allowed actions, allowed interaction/direction masks, bounded allowed-schema table, per-session/per-window/window action limits, loop-window depth, service-emulation flag, declared service owner |
| `struct StimulationRequest` | bounded declared request: permit/session/plan identity, action, interaction, direction, schema, target, interface tag, service owner, clock domain, scheduled time, immediate flag, request/correlation/causation ids, quota cost |
| `struct ResolvedTime` | bounded caller-resolved time: domain, value, resolution `Result` |
| `struct GuardDiagnostic` | bounded payload-free diagnostic: closed `GuardReason` plus accepted T025 `Diagnostic` detail |
| `class StimulationGuard` | `open(const Permit&, const StimulationPolicy&)`, `authorize(const StimulationRequest&, LifecycleState, const ResolvedTime&, GuardDiagnostic&)`, `snapshot()`, `is_open()`; non-copyable, non-movable; nested `GuardSnapshot` |

Ownership/lifetime: `session-issued-handle`; only a guard opened from the session's immutable permit may
authorize, and the guard is `session-scoped`. Thread-safety: `internally-synchronized` with one per-guard
mutex; `open` must complete before concurrent `authorize` calls; there is no callback.

### 6.2 Consumed contracts (read-only)

| Interface | Contract consumed (unchanged) |
| --- | --- |
| `xverse::xcom::validation::{Permit, PermitId, SessionId, PlanDigest, Timestamp, ClockDomainId, Tag, Result, Diagnostic, LifecycleState, is_terminal}` | accepted T025 identity/lifecycle/diagnostic vocabulary, used read-only and never redefined |
| `xverse::xcom::{InteractionKind, EndpointDirection}` | accepted T-CORE interaction/direction vocabulary, used read-only and never redefined |
| `xverse::xcom::validation::TimeAuthority` | the accepted mapping/tolerance mechanism; the caller resolves the request time with it (no guard call, no mutation) |

## 7. Concurrency and resource bounds

| Aspect | T027 decision |
| --- | --- |
| Writers | one declared logical writer per guard; `authorize`/`open` serialize the tallies and loop window under one per-guard mutex |
| Callbacks | none; the guard invokes no host callback on any path |
| Threads in tests | ≤ 4, and only in the bounded deterministic-concurrency case (one guard, or independent guards) |
| Session tally | ≤ `max_actions_per_session`; tests exercise the declared minimum and maximum bounds |
| Window tally | ≤ `max_actions_per_window` per `action_window`; tests exercise the declared bounds |
| Loop window | ≤ `loop_window` ≤ `kGuardMaxLoopWindow`; never grows past its declared depth |
| Schema table | ≤ `kGuardMaxSchemas` declared entries; policy validation rejects an over-full table |
| Values | every bounded value has a compile-time size bound; no payload/address/free-form member |
| Iterations | finite, declared loop counts; no unbounded loop, retry, or wait |
| Wall-clock | no case depends on wall-clock timing for its verdict |
| Guard I/O | none; the guard performs no file, socket, authority, or environment access |
| Production footprint | one new static library and additive tests; no other production behavior changes |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Fail closed | any failed check rejects and every indeterminate time resolution fails; only `Authorized` proceeds | T027-STK-002, T027-SR-012; CHK-07, CHK-13, CHK-14 |
| Zero mutation on rejection | tallies, loop window, permit, and policy unchanged; commit only on `Authorized` | T027-SR-013; CHK-14, NEG-26 |
| Zero emission | no emission/callback/route/injection/invocation/emulation/lease surface exists | T027-SR-022; CHK-15, CHK-21, NEG-27 |
| Exact plan binding | request and policy plan digest cross-checked against the immutable permit | T027-SR-005; CHK-16, NEG-07 |
| Closed vocabularies | closed action/outcome/reason/status vocabularies with stable names and precedence | T027-SR-003, T027-SR-014; CHK-17, NEG-28 |
| Bounded resources | finite tallies, loop window, schema table, and iterations; fail-closed on a bound | T027-SR-009, T027-SR-010, T027-SR-021; CHK-10, CHK-12, CHK-18 |
| No raw-clock comparison | a caller-resolved time in the permit validity domain; unmapped/failed resolution fails closed | T027-SR-012; CHK-13, NEG-23 |
| Payload safety | bounded payload-free values; no payload member; no payload logged or retained | T027-SR-004; CHK-05, CHK-20 |
| Determinism | same sequence → same decision, reason, diagnostic detail, and snapshot | T027-SR-014; CHK-17, NEG-28 |
| Concurrency | one per-guard mutex; no callback; bounded threads/iterations | T027-SR-015; CHK-18, NEG-29 |
| Offline safety | standard library plus accepted T025/T-CORE headers; no I/O/network/ambient/secret/legacy | T027-SR-016; CHK-19, NEG-30 |
| Public safety | no secret, private address, real payload, or host path in committed files/evidence | T027-SR-017; CHK-21, NEG-31 |
| Documentation | Doxygen ownership/lifetime/thread-safety/failure on every public declaration | T027-SR-018; CHK-22 |
| Governance | registers re-validated; REF-002 unchanged; STIM-004 implemented; STIM-005/006 partial | T027-SR-019, T027-SR-020; CHK-23, CHK-24 |

## 9. Consistency and constraints

- **Dependency direction preserved.** T027 consumes the accepted T025 in-process contract and the accepted
  T-CORE interaction vocabulary; it introduces no dependency on a later slice, adapter, gateway, or legacy
  repository.
- **Domain neutrality preserved.** The guard uses only generic stimulation vocabulary (request, policy,
  schema, direction, action, quota, loop, ownership, clock domain); no automotive, product, protocol, or
  configuration primitive is introduced.
- **XDL centrality preserved.** T027 neither parses nor authors XDL; it consumes bounded identity values
  that the accepted plan already binds and cross-checks the plan digest against the immutable permit.
- **Logical/physical separation preserved.** Requests carry logical identity, plan digest, clock domain, and
  bounded tags only; no address, transport, or environment identity enters a decision.
- **Ownership preserved.** Only T027 source/test paths, the shared build files, the T027 work products, and
  the T027 checkbox change; T025/T026 accepted bytes are consumed read-only and preserved.
- **Maturity preserved.** The guard stays a bounded prototype; the exclusive lease, injection/invocation/
  emulation, end-to-end loop/scheduling enforcement, sanitizer/static/Doxygen execution, benchmarks, and
  acceptance remain with T028–T041.
- **Scope preserved.** T027 emits nothing, injects nothing, invokes nothing, emulates nothing, leases
  nothing, and routes nothing; the action paths (T028) remain a separate, dependency-ordered task.

## 10. Traceability

| Architecture element | T027 requirements |
| --- | --- |
| `T27-XB-1`, `T27-CMP-T025`, `T27-CMP-CORE` | T027-SR-002, T027-SR-005 |
| `T27-XB-2`, `T27-CMP-GUARD`, `T27-CMP-COMMIT` | T027-SR-013, T027-SR-022 |
| `T27-XB-3` | T027-SR-005 |
| `T27-XB-4` | T027-SR-006 |
| `T27-XB-5`, `T27-CMP-MODEL` | T027-SR-004, T027-SR-007, T027-SR-008, T027-SR-011 |
| `T27-XB-6` | T027-SR-009, T027-SR-010, T027-SR-021 |
| `T27-XB-7` | T027-SR-012 |
| `T27-XB-8`, `T27-WP` | T027-SR-016, T027-SR-017, T027-SR-018 |
| `T27-XB-9` | T027-SR-019, T027-SR-022 |
| `T27-CMP-VOCAB` | T027-SR-003, T027-SR-014 |
| `T27-CMP-DECIDE` | T027-SR-007, T027-SR-008, T027-SR-011, T027-SR-012 |
| `T27-IF-1` (§6.1) | T027-SR-001, T027-SR-003, T027-SR-013 |
| `T27-CMP-BUILD` | T027-SR-001, T027-SR-020 |

## 11. Negative cases (architecture view)

Every boundary has a declared fail-closed behaviour and a negative-case owner; the executable cases are
listed in `verification-plan.md` §5.

| Boundary | Injected defect | Negative case |
| --- | --- | --- |
| `T27-XB-1` | T027 mutates accepted T025/T026 state | NEG-01, NEG-02, NEG-35 |
| `T27-XB-2` | a rejection or failure emits a normal-route item | NEG-27 |
| `T27-XB-3` | a foreign/absent session, permit, or plan identity is authorized | NEG-06, NEG-07 |
| `T27-XB-4` | a revoked/expired/non-active session is authorized | NEG-08, NEG-09, NEG-10 |
| `T27-XB-5` | an undeclared/inconsistent schema, direction, target, action, or ownership declaration is authorized | NEG-04, NEG-05, NEG-11, NEG-12, NEG-13, NEG-14, NEG-15, NEG-20, NEG-21, NEG-33 |
| `T27-XB-6` | a quota or loop bound is exceeded, or a rejection mutates a tally/window | NEG-16, NEG-17, NEG-18, NEG-19, NEG-26, NEG-36 |
| `T27-XB-7` | an unmapped/out-of-tolerance time is authorized, a raw clock comparison, or a guard time-authority mutation | NEG-22, NEG-23, NEG-24, NEG-25, NEG-35 |
| `T27-XB-8` | a new dependency, I/O, or offline/public-safety violation | NEG-02, NEG-30, NEG-31 |
| `T27-XB-9` | T027 implements T028 or a later task | NEG-01, NEG-32 |
| Vocabularies/values | an open vocabulary, an unstable precedence, or a payload-bearing value | NEG-03, NEG-28 |
| Precondition | a closed guard or an invalid policy authorizes | NEG-33, NEG-34 |
| Governance | a weakened requirement/test or a promoted REF-002 disposition | NEG-01, NEG-32 |
