# T014 Requirements — Bounded Endpoint/Route Lifecycle and Exact Generation-Bound Ownership Handles

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T014 (capability 007, slice `T-CORE`) |
| Task title | Implement bounded endpoint/route lifecycle and exact generation-bound ownership handles |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59` |
| Authorization | capability 007 accepted design and bounded implementation authorization (ACC002/ACC004/ACC005/ACC006/ACC007/ACC010/ACC011/ACC014/ACC015); ADR-0016; ADR-0018; ADR-0020 |
| Owning slice | `T-CORE` (T007 ownership register) |
| Predecessor | T013 (immutable core value, contract, item, diagnostic, and policy types; reviewed terminal package) |
| Producer dependency | T011 admitted offline build envelope (read-only inputs); T012 subtree CMake/CTest contract |
| Successor tasks | T015 (provider composition + owned loopback), T016 (core unit/negative matrix), then T017–T034, T035–T041 |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}`; `docs/engineering/xcom/t008/requirements-register.{json,md}`; `docs/engineering/xcom/t009/architecture-model.{json,md}`; `docs/engineering/xcom/t010/unit-design.{json,md}` |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production
change and does not implement, accept, or integrate the candidate. The T014 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T014 — Implement bounded endpoint/route lifecycle and exact generation-bound ownership handles.

### 1.1 Authority statement

This document specifies only the bounded T014 slice. It elaborates the accepted architecture
(`XCOM-CMP-005` "Endpoint and route lifecycle", responsible for the bounded endpoint and route lifecycle
with exact generation-bound ownership handles) and the accepted software requirements
`XCOM-SW-CORE-003` (fail-closed binding and activation), `XCOM-SW-CORE-004` (bounded delivery policy), and
`XCOM-SW-CORE-005` (endpoint/route lifecycle and issued handles) that `docs/engineering/xcom/t008/`
attributes to T014 and that `docs/engineering/xcom/t010/` maps to design unit `XCOM-DU-006`. It does
**not** redesign the accepted architecture, change a functional requirement, success criterion, ADR,
schema, or contract, fix a provider/observation/stimulation value, implement T013 or T015–T016 or any
later task, add a new admitted dependency, or accept or integrate any candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, the
T007 ownership register, the T008 register, the T009 architecture model, the T010 unit design, the
constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is reported
rather than guessed. Unresolved gaps are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T014)

1. **Re-verify and own the bounded endpoint/route lifecycle** under `src/xverse/xcom/` in namespace
   `xverse::xcom`, realising `XCOM-DU-006` (`XCOM-CMP-005`): immutable `EndpointSpec`/`RouteSpec`
   declarations, finite validated `LifecycleConfiguration`, the serialized fixed-record
   `LifecycleController`, the `declared → validated → active → draining → closed` state machine with a
   `failed` branch, idempotent safe repeats, and exact generation-bound `EndpointHandle`/`RouteHandle`
   ownership. The baseline already provides this source; T014 owns it, re-runs its unit, negative, and
   external-consumer checks, and records the exact candidate revision.
2. **Complete the missing binding half of `XCOM-SW-CORE-004`.** The accepted `io.xverse.xcom` delivery
   policy is defined as an immutable value by T013 (`FlowPolicy` in `contract.hpp`), and T013 records that
   binding it to endpoints/routes is T014's (`T013-GAP-02`, `T013-OPEN-01`). No production path binds the
   declared bounded policy to a route generation today. T014 adds the minimal, additive binding: a route
   declaration may carry exactly one immutable, already-validated `FlowPolicy`; the controller owns it in
   the route generation, exposes it only after exact handle authentication, substitutes no default, and
   offers no rebinding/upgrade path.
3. **Add focused T014 unit and negative cases** for the new declared-policy binding and for the exact
   handle boundaries it must preserve, inside the existing `tests/xcom/endpoint_route_lifecycle/`
   executables. The consolidated cross-cutting matrix (interaction kinds, provider capabilities, policy,
   ownership, lifecycle, queue bounds, diagnostic determinism, recovery) remains T016.
4. **Re-verify every T014-owned lifecycle path unchanged** where not extended: the existing declaration,
   capacity, transition, compatibility, ownership, retention, concurrency, and diagnostic cases must
   still pass without weakening, renaming, or removing a case.
5. The T014 repository-owned work products and the T014 package record.

### 2.2 Explicit exclusions (must remain absent from the T014 candidate)

No provider composition, owned loopback provider, observation, stimulation, journaling, time-authority,
service-emulation lease, Protobuf/gRPC, gateway, Argus/Maestro/Faults, compatibility, or legacy behaviour;
no `xdl/`, `proto/`, or `src/xverse_xdl/` change; no change to a `.cmake` file, the root `CMakeLists.txt`,
or `src/xverse/xcom/CMakeLists.txt` (the lifecycle target already compiles
`endpoint_route_lifecycle.cpp` and already registers the three lifecycle test executables, so no build-file
change and no inherited T020 trace-link hash refresh is required); no change to `contract.hpp`,
`diagnostic.hpp`, `core_types.hpp`, `provider.hpp`, `loopback_provider.hpp`, or any other T-CORE value or
provider source; no new admitted dependency; no network access, TCP listener, filesystem access, process
execution, or legacy repository/binary access; no rewrite or weakening of an accepted ADR, requirement,
contract, test, REF-002 disposition, or another task's ownership path; no promotion of any REF-002 or
capability requirement; no acceptance or integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T014 |
| --- | --- | --- |
| Immutable `FlowPolicy` value, vocabulary, and ranges | T013 | complete (predecessor); consumed read-only from `contract.hpp` |
| Provider capability advertisement and declared-policy/endpoint capability matching | T015 | allocated; T014 binds the declared policy to the route generation only, it does not match a provider |
| Consolidated core unit/negative matrix (interaction kinds, capabilities, policy, ownership, lifecycle, queue bounds, diagnostics, recovery) | T016 | allocated; T014 adds only focused cases for its own binding and handle boundaries |
| XDL-derived activation plan, ordering-equivalence, malformed-plan, drift, bound, regression suites | T017–T020 | complete (predecessor backlog) |
| Observation boundary | T021–T024 | allocated |
| Validation stimulation boundary | T025–T029 | allocated |
| Executed sanitizer/static-analysis/Doxygen evidence, benchmarks | T035–T037 | allocated |
| Integration, validation, delivery bundle | T035–T040 | allocated |
| Independent/external review and user acceptance | T039/T041 | allocated |

## 3. Stakeholder requirements (`T014-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T014-STK-001**: Before the X-COM core is accepted, the program **shall** have one repository-owned,
  bounded, domain-neutral C++20 endpoint/route lifecycle with exact generation-bound ownership handles,
  physically under `src/xverse/xcom/`, that compiles with the T011-admitted toolchain under the T012
  warning-as-error contract.
- **T014-STK-002**: The lifecycle **shall** fail closed: no unvalidated or partial resource is ever
  exposed, every capacity is finite and explicit, no rejected operation mutates a record, and no delivery
  or timing guarantee is silently upgraded or weakened.
- **T014-STK-003**: Every lifecycle type **shall** make its ownership, lifetime, thread-safety, and failure
  contract explicit, and immutable declarations, handles, snapshots, and results **shall** be safe to copy
  and to read concurrently.
- **T014-STK-004**: The lifecycle **shall** be offline and domain-neutral: normal use performs no network
  discovery, ambient configuration or secret lookup, filesystem access, process execution, or
  legacy-repository access, and contains no domain-specific primitive.
- **T014-STK-005**: T014 **shall** preserve accepted intent: the delivered change is confined to the
  T014-owned lifecycle paths, the T014 work products, and the capability task ledger, and it **shall**
  neither weaken an accepted requirement or test nor implement another task.

## 4. Software/engineering requirements (`T014-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Implemented" means the repository-owned source and its deterministic checks exist and pass; it is
not a runtime or production claim.

### 4.1 Immutable declarations and finite configuration

- **T014-SR-001 [ubiquitous]**: `EndpointSpec` **shall** be an immutable declaration of a bounded logical
  endpoint identity, an exact 64-character lowercase-hexadecimal plan digest, an explicit logical provider
  identity, one direction declared by the supplied `CommunicationContract`, and the exact contract itself;
  `EndpointSpec::create` **shall** reject empty, malformed, over-bound, or contract-incompatible input
  with a non-empty deterministic diagnostic set and **shall** expose no partial declaration.
  - Refines: `XCOM-SW-CORE-003`, `XCOM-SW-CORE-005`; anchors FR-003, FR-006, FR-009; `XCOM-DU-006`.
  - Verification intent: declaration rejection table; CHK-04, CHK-05, CHK-09.
- **T014-SR-002 [ubiquitous]**: `RouteSpec` **shall** be an immutable declaration that copies exactly two
  distinct compatible endpoint declarations sharing one plan digest, provider identity, contract, and
  contract source/target directions; `RouteSpec::create` **shall** reject any incompatible pair with a
  stable `route_incompatible` diagnostic and **shall** expose no partial route.
  - Refines: `XCOM-SW-CORE-003`, `XCOM-SW-CORE-005`; anchors FR-003, FR-006, FR-009; `XCOM-DU-006`.
  - Verification intent: route compatibility matrix; CHK-04, CHK-05, CHK-12.
- **T014-SR-003 [ubiquitous]**: `LifecycleConfiguration` **shall** admit only finite nonzero endpoint and
  route capacities no greater than the published compile-time maxima `kMaximumEndpoints = 32` and
  `kMaximumRoutes = 32`, and **shall** reject zero or over-maximum capacities with a stable `bound_exceeded`
  diagnostic without constructing a controller.
  - Refines: `XCOM-SW-CORE-004`, `XCOM-SW-CORE-005`; anchors FR-007, FR-009; `XCOM-DU-006`.
  - Verification intent: configuration boundary matrix; CHK-06, CHK-09.

### 4.2 Bounded records and exact generation-bound ownership handles

- **T014-SR-004 [ubiquitous]**: `LifecycleController` **shall** own fixed compile-time-bounded record
  storage, consider only the configured capacity prefix, reuse empty or closed slots (preferring the same
  logical identity), and **shall** never grow storage; a duplicate nonclosed identity **shall** be rejected
  with `duplicate_identity` and an exhausted configured capacity with `capacity_exhausted`, each without
  replacing or mutating an existing record.
  - Refines: `XCOM-SW-CORE-004`, `XCOM-SW-CORE-005`; anchors FR-007, FR-009; `XCOM-DU-006`.
  - Verification intent: capacity/isolation and duplicate cases; CHK-06, CHK-09.
- **T014-SR-005 [ubiquitous]**: Every successful declaration **shall** return an opaque typed handle that
  owns the issuing controller identity, the exact resource kind, the logical identity, the exact plan
  digest, and a nonzero, strictly advancing generation; handle construction **shall** be private to the
  controller; copying a handle **shall** preserve the exact binding.
  - Refines: `XCOM-SW-CORE-005`; anchors FR-009, FR-010; `XCOM-DU-006`; `XCOM-INV-02`.
  - Verification intent: handle binding and kind assertions; CHK-04, CHK-05, CHK-07.
- **T014-SR-006 [unwanted behaviour]**: If a handle is stale (superseded generation), foreign (different
  controller), of the wrong resource kind, or its identity/digest/generation does not match a current
  record, then the operation **shall** return a stable `invalid_handle` diagnostic in the `ownership`
  phase and **shall not** mutate any controller record.
  - Refines: `XCOM-SW-CORE-005`; anchors FR-009, FR-010; `XCOM-DU-006`; `XCOM-INV-02`.
  - Verification intent: stale/foreign route, source, and destination handle boundaries; CHK-07, NEG
    handle matrix.

### 4.3 Declared bounded delivery-policy binding (new in T014)

- **T014-SR-007 [ubiquitous]**: A route declaration **shall** be able to bind exactly one immutable,
  already-validated `FlowPolicy` at declaration time; the bound declared policy **shall** be copied into
  the owned route value, **shall** survive every later lifecycle transition and generation, and **shall**
  be reachable only through the route generation that declared it.
  - Refines: `XCOM-SW-CORE-004`; anchors FR-007, FR-008; `XCOM-DU-006`; T013-GAP-02, T013-OPEN-01.
  - Verification intent: declared-policy binding and generation cases; CHK-10, CHK-13.
- **T014-SR-008 [ubiquitous]**: The lifecycle **shall** expose the exact declared policy for a route
  generation only after authenticating its exact current `RouteHandle`; a route generation that declared no
  policy **shall** fail with a stable deterministic diagnostic and **shall not** substitute, default, or
  infer a policy.
  - Refines: `XCOM-SW-CORE-004`; anchors FR-007, FR-008; `XCOM-DU-006`; Constitution IX.
  - Verification intent: absent-policy diagnostic and no-substitution cases; CHK-10, CHK-13, NEG-14.
- **T014-SR-009 [unwanted behaviour]**: If an operation would rebind, replace, weaken, or strengthen the
  declared policy of a live route generation, then the lifecycle **shall** reject it: no such public
  operation **shall** exist, and changing the declared policy **shall** require closing and recreating the
  route as a new generation.
  - Refines: `XCOM-SW-CORE-004`; anchors FR-008; `XCOM-DU-006`; Constitution IX.
  - Verification intent: no-upgrade structural case and recreated-generation case; CHK-11, NEG-15.
- **T014-SR-010 [ubiquitous]**: A declared policy bound to a route **shall** not bypass, relax, or replace
  any existing endpoint compatibility, ownership, state, or endpoint-retention rule; a policy-bound route
  **shall** fail every incompatible validate/activate exactly as an unbound route does.
  - Refines: `XCOM-SW-CORE-003`, `XCOM-SW-CORE-004`; anchors FR-006, FR-007; `XCOM-DU-006`.
  - Verification intent: policy-bound compatibility matrix; CHK-12, NEG-16.

### 4.4 Lifecycle state machine, receipts, and recovery

- **T014-SR-011 [ubiquitous]**: The permitted endpoint and route state sequence **shall** be
  `declared → validated → active → draining → closed`, with `failed` reachable from any nonterminal
  operational state and `closed` reachable from `draining` or `failed`; repeating an already-applied
  transition in its target state **shall** be idempotent and return the same generation; a skipped or
  terminal transition **shall** be rejected with a stable `invalid_transition` diagnostic without mutation.
  - Refines: `XCOM-SW-CORE-005`; anchors FR-010, FR-025; `XCOM-DU-006`.
  - Verification intent: complete endpoint and route transition tables; CHK-08, CHK-14.
- **T014-SR-012 [ubiquitous]**: Route validation **shall** authenticate the exact current route, source,
  and destination handles and require a compatible plan/provider/contract/direction tuple with both
  endpoints `validated` or `active`; route activation **shall** repeat every check and additionally require
  both endpoints `active`; every rejection **shall** be byte-stable and **shall** leave the route and both
  endpoints unchanged.
  - Refines: `XCOM-SW-CORE-003`, `XCOM-SW-CORE-005`; anchors FR-006, FR-010; `XCOM-DU-006`.
  - Verification intent: compatibility and endpoint-state boundary matrix; CHK-12, CHK-14.
- **T014-SR-013 [ubiquitous]**: An endpoint **shall** not be drained or closed while any nonclosed route
  refers to it; the rejection **shall** be a stable `endpoint_in_use` diagnostic and **shall** leave both
  the endpoint and the referring route unchanged.
  - Refines: `XCOM-SW-CORE-005`; anchors FR-009, FR-010; `XCOM-DU-006`.
  - Verification intent: retained-endpoint closure boundary; CHK-14, NEG-12.
- **T014-SR-014 [ubiquitous]**: Closing a resource **shall** leave its handle queryable and its close
  idempotent until that identity's slot is recreated; recreation **shall** issue a strictly higher
  generation and make the earlier handle stale; restart reconciliation **shall not** infer ownership from a
  name or address, only from the exact issuing controller identity and generation.
  - Refines: `XCOM-SW-CORE-005`; anchors FR-010; `XCOM-DU-006`.
  - Verification intent: failure/recreation and stale-after-recreation cases; CHK-08, CHK-14, NEG-11.

### 4.5 Diagnostics, bounds, concurrency, and safety

- **T014-SR-015 [ubiquitous]**: Every rejection **shall** return a non-empty, bounded, deterministically
  ordered immutable `DiagnosticSet`; a caller **shall** be able to compare the exact serialized bytes
  before and after a rejected operation and observe no change.
  - Refines: `XCOM-SW-CORE-004`, `XCOM-SW-CORE-005`; anchors FR-025; SC-001; `XCOM-DU-006`.
  - Verification intent: exact-diagnostic assertions across the negative suite; CHK-07, CHK-15.
- **T014-SR-016 [ubiquitous]**: Every lifecycle unit **shall** declare finite resource bounds and a declared
  overflow behaviour: endpoint and route records ≤ 32 each and finite configured; generation space bounded
  by `std::uint64_t` with explicit `generation_exhausted` rejection; one `FlowPolicy` per route at most; no
  queue, quota, retry, or depth is unbounded. The declared policy **shall not** be reinterpreted as a
  lifecycle record capacity.
  - Refines: `XCOM-SW-CORE-004`; anchors FR-007; `XCOM-DU-006`; T010 bounds vocabulary.
  - Verification intent: bounds matrix and overflow cases; CHK-06, CHK-09.
- **T014-SR-017 [ubiquitous]**: Every controller operation, including the new declared-policy read,
  **shall** be serialized by one internal mutex; no callback **shall** run under the lock; immutable values
  **shall** support concurrent const reads; and concurrent safe repeats **shall** converge on one state and
  generation without duplicating a record.
  - Refines: `XCOM-SW-CORE-005`; anchors FR-010; `XCOM-DU-006`.
  - Verification intent: serialized safe-repeat concurrency cases; CHK-17, NEG-17.
- **T014-SR-018 [ubiquitous]**: The lifecycle **shall** perform no network, ambient, secret, filesystem,
  process, or legacy access, and **shall** add no admitted dependency beyond the C++ standard library.
  - Refines: `XCOM-SW-CORE-007` (domain-neutral local runtime half); anchors FR-026, FR-028; ADR-0018;
    Constitution IX.
  - Verification intent: forbidden-API source scan plus the successful offline build; CHK-18, NEG-19,
    NEG-24.
- **T014-SR-019 [ubiquitous]**: Committed source, tests, and work products **shall** contain no credential,
  private address, unrestricted payload, proprietary source excerpt, environment-specific absolute host
  path, or sensitive deployment value.
  - Refines: Constitution X; anchors FR-027; `XCOM-SW-INTG` public-safe evidence rule.
  - Verification intent: public-safety scan; CHK-19, NEG-21.
- **T014-SR-020 [ubiquitous]**: Every new or changed public C/C++ declaration **shall** carry useful
  Doxygen documentation including its ownership, lifetime, thread-safety, and failure contract, without
  weakening the admitted repository documentation configuration.
  - Refines: `XCOM-SW-CORE`; anchors FR-029; `XCOM-DU-006` Doxygen plan; Constitution X.
  - Verification intent: declaration inspection and the existing documentation validator; CHK-20;
    strict-declaration Doxygen remains `DOX-GAP-01`, owned by T011/T037.
- **T014-SR-021 [ubiquitous]**: The T014 candidate **shall** change no accepted requirement, ADR, contract,
  schema, another task's ownership path, or existing test case, **shall** implement no later task,
  **shall** keep the REF-002 disposition `unchanged` with an empty `promoted` list, and **shall** record —
  without rewriting — the `XCOM-CMP-005`/`XCOM-SW-CORE-002` attribution anomaly described in §7.3.
  - Refines: ADR-0018, ADR-0020; T007 global prohibitions; anchors FR-030, FR-035; Constitution VII, IX.
  - Verification intent: `git diff --name-only <baseline> --` boundary inspection; register validators;
    CHK-02, CHK-21, CHK-22, CHK-25.
- **T014-SR-022 [ubiquitous]**: The T014 candidate **shall** satisfy the deterministic Fabro gate for
  implementation tasks: the five plan-stage work products and the implementation record exist, at least one
  `src/xverse/xcom/**` path changes, `cmake` configure, build, test discovery, and the full `ctest` suite
  pass, and `git diff --check` is clean; the T014 checkbox is marked complete **only** in the
  implementation stage.
  - Refines: ADR-0020; anchors FR-030; Constitution X.
  - Verification intent: `xcom_feature_gate.py verify T014 <baseline>`; `git diff --check`; CHK-23, NEG-22.

## 5. Requirement-to-accepted-anchor traceability

| T014 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T014-STK-001 | `XCOM-SW-CORE-005` | XCOM-SYS-FR-009/010 | FR-009, FR-010 | IX, X |
| T014-STK-002 | `XCOM-SW-CORE-003/004` | XCOM-SYS-FR-006/007/008 | FR-006, FR-007, FR-008 | IX |
| T014-STK-003 | `XCOM-SW-CORE-005` | XCOM-SYS-FR-009 | FR-009 | V, IX |
| T014-STK-004 | `XCOM-SW-CORE-007` | XCOM-SYS-FR-026/028 | FR-026, FR-028 | II, VII |
| T014-STK-005 | Constitution VII/IX; ADR-0018/0020 | – | FR-030 | VII, IX, X |
| T014-SR-001 | `XCOM-SW-CORE-003/005` | XCOM-SYS-FR-003/006/009 | FR-003, FR-006, FR-009 | V, IX |
| T014-SR-002 | `XCOM-SW-CORE-003/005` | XCOM-SYS-FR-003/006/009 | FR-003, FR-006, FR-009 | V, IX |
| T014-SR-003 | `XCOM-SW-CORE-004/005` | XCOM-SYS-FR-007/009 | FR-007, FR-009 | IX |
| T014-SR-004 | `XCOM-SW-CORE-004/005` | XCOM-SYS-FR-007/009 | FR-007, FR-009 | IX |
| T014-SR-005 | `XCOM-SW-CORE-005` | XCOM-SYS-FR-009/010 | FR-009, FR-010 | IX |
| T014-SR-006 | `XCOM-SW-CORE-005` | XCOM-SYS-FR-009/010 | FR-009, FR-010 | IX |
| T014-SR-007 | `XCOM-SW-CORE-004` | XCOM-SYS-FR-007/008 | FR-007, FR-008 | III, IX |
| T014-SR-008 | `XCOM-SW-CORE-004` | XCOM-SYS-FR-007/008 | FR-007, FR-008 | IX |
| T014-SR-009 | `XCOM-SW-CORE-004` | XCOM-SYS-FR-008 | FR-008 | IX |
| T014-SR-010 | `XCOM-SW-CORE-003/004` | XCOM-SYS-FR-006/007 | FR-006, FR-007 | IX |
| T014-SR-011 | `XCOM-SW-CORE-005` | XCOM-SYS-FR-010/025 | FR-010, FR-025 | IX |
| T014-SR-012 | `XCOM-SW-CORE-003/005` | XCOM-SYS-FR-006/010 | FR-006, FR-010 | IX |
| T014-SR-013 | `XCOM-SW-CORE-005` | XCOM-SYS-FR-009/010 | FR-009, FR-010 | IX |
| T014-SR-014 | `XCOM-SW-CORE-005` | XCOM-SYS-FR-010 | FR-010 | IX |
| T014-SR-015 | `XCOM-SW-CORE-004/005` | XCOM-SYS-FR-025 | FR-025 | SC-001 |
| T014-SR-016 | `XCOM-SW-CORE-004` | XCOM-SYS-FR-007 | FR-007 | IX |
| T014-SR-017 | `XCOM-SW-CORE-005` | XCOM-SYS-FR-010 | FR-010 | IX |
| T014-SR-018 | `XCOM-SW-CORE-007` | XCOM-SYS-FR-026/028 | FR-026, FR-028 | IX |
| T014-SR-019 | public-safe evidence rule | XCOM-SYS-FR-027 | FR-027 | X |
| T014-SR-020 | `XCOM-SW-CORE` Doxygen | XCOM-SYS-FR-029 | FR-029 | X |
| T014-SR-021 | Constitution; ADR-0018/0020 | XCOM-SYS-FR-035 | FR-030, FR-035 | VII, IX |
| T014-SR-022 | ADR-0020 | – | FR-030 | X |

`XCOM-SW-CORE-003/004/005` are the accepted capability-007 software requirements
(`docs/engineering/xcom/t008/requirements-register.{json,md}`) attributed to T014. They are accepted text;
T014 refines and consumes them and does not rewrite them. `XCOM-DU-006` is the accepted T010 design unit,
`XCOM-CMP-005` the accepted T009 architecture component, and the system requirements and `SC-*` are the
accepted `specs/007-xcom-core/spec.md` statements.

## 6. REF-002 disposition

T014 owns no REF-002 SADS ID. It provides the bounded endpoint/route lifecycle and the declared-policy
binding against which the allocated REF-002 communication IDs (`XVE-SYS-0139`–`0158`) and their shared
contributions are later implemented and verified. T014 changes no required disposition: the capability
`ref002.disposition` stays `unchanged` with an empty `promoted` list (T014-SR-021). No allocated, deferred,
or target SADS requirement is reported as implemented, and no `XVE-SYS-*` ID is promoted.

## 7. Affected paths

### 7.1 Paths the T014 candidate changes

| Path | Change | Notes |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/endpoint_route_lifecycle.hpp` | edit | adds an owned optional declared `FlowPolicy` to `RouteSpec` with `has_policy()`/`policy()` and an additive `create` overload; adds `LifecycleSnapshot::policy_bound()`; adds `LifecycleController::route_policy(handle)`; no existing declaration removed, renamed, or changed |
| `src/xverse/xcom/src/endpoint_route_lifecycle.cpp` | edit | implements the declared-policy binding, the snapshot flag, and the exact-handle policy read; reuses existing diagnostic codes/phases only |
| `tests/xcom/endpoint_route_lifecycle/unit_tests.cpp` | edit | adds focused declared-policy binding, generation, immutability, and concurrent-read cases (T014-owned); existing cases unchanged |
| `tests/xcom/endpoint_route_lifecycle/negative_tests.cpp` | edit | adds focused absent-policy, stale/foreign-handle policy-read, no-upgrade, and policy-bound compatibility cases (T014-owned); existing cases unchanged |
| `docs/engineering/xcom/t014/requirements.md` | add | this document |
| `docs/engineering/xcom/t014/architecture.md` | add | boundary, components, data flow, interfaces |
| `docs/engineering/xcom/t014/detailed-design.md` | add | rules, policy-binding semantics, failure semantics, bounds, Doxygen/design |
| `docs/engineering/xcom/t014/unit-specifications.md` | add | units, ownership/lifetime/thread-safety/bounds, traceability |
| `docs/engineering/xcom/t014/verification-plan.md` | add | named checks, negative cases, commands |
| `docs/engineering/xcom/t014/implementation.md` | add (implementation stage) | realized change and evidence |
| `docs/engineering/xcom/t014/internal-review.json` | add (review stage) | DeepSeek internal review |
| `specs/007-xcom-core/tasks.md` | edit T014 checkbox (implementation stage) | capability task ledger |
| `reports/xcom-queue/t014-package.json` | add (package stage) | exact-candidate package record |

### 7.2 T014-owned lifecycle paths consumed and re-verified unchanged

| Path | Owner | Role for T014 |
| --- | --- | --- |
| `tests/xcom/endpoint_route_lifecycle/consumer/main.cpp` | T-CORE (T014) | external-consumer fixture; re-verified unchanged (public include + build/link) |
| `scripts/validate_xcom_endpoint_route_lifecycle.py` | T-CORE (T014) | legacy SESN-era validator in the T014 path set; neither depended on nor edited by the repository-owned workflow (`T014-LIM-04`) |

### 7.3 Consumed, read-only foundation (not changed by T014)

| Path | Owner | Role for T014 |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/contract.hpp`, `src/xverse/xcom/src/contract.cpp` | T013 (complete) | immutable `CommunicationContract`, `InteractionKind`, `EndpointDirection`, and the declared `FlowPolicy` value; read-only |
| `src/xverse/xcom/include/xverse/xcom/diagnostic.hpp`, `src/xverse/xcom/src/diagnostic.cpp` | T013 (complete) | stable `DiagnosticCode`/`ValidationPhase`/`DiagnosticSet`; T014 adds no code or phase |
| `src/xverse/xcom/include/xverse/xcom/{value,item,result,core_types}.hpp` | T013 (complete) | bounded primitives and aggregate; read-only |
| `src/xverse/xcom/CMakeLists.txt`, `cmake/*.cmake`, `CMakeLists.txt` | shared (serialized, T012) | T012 subtree build/test contract; T014 changes none |
| `src/xverse/xcom/include/xverse/xcom/{provider,loopback_provider,observation,validation_session,activation_plan}.hpp` and sources | T015/T019/T021/T025 | later/parallel slices; T014 neither depends on nor changes them |
| `docs/engineering/xcom/t008/*`, `t009/*`, `t010/*` | T008/T009/T010 | accepted registers and models; the §7.4 anomaly is recorded, not rewritten |
| `docs/xcom/endpoint-route-lifecycle*.{md,json}`, `engineering/**/*.json` | legacy/T020 (inherited) | historical SESN evidence and inherited T020 provenance; T014 changes no linked path, so no inherited hash refresh is required |

### 7.4 Recorded attribution anomaly (not resolved by T014)

The accepted `docs/engineering/xcom/t009/architecture-model.json` lists `XCOM-CMP-005`
requirement links as `XCOM-SW-CORE-002` and `XCOM-SYS-FR-009`, while
`docs/engineering/xcom/t008/requirements-register.json` attributes `XCOM-SW-CORE-003`, `-004`, and `-005`
to T014 and `docs/engineering/xcom/t010/unit-design.json` links `XCOM-DU-006` to `XCOM-SW-CORE-003/-004/
-005`. The registers are owned by T008/T009/T010 and remain `partial`/`unreconciled` (analysis A12).
T014 records this observation, implements the source as the T008 requirement attribution and the
`XCOM-DU-006` unit design direct, and rewrites nothing (T014-SR-021).

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- `T014-LIM-01` — The lifecycle is a prototype control-plane library: it makes no runtime, transport,
  timing, compatibility, or production-readiness claim, and it is not yet user-accepted (T041).
- `T014-LIM-02` — Strict declaration-level Doxygen (`WARN_IF_UNDOCUMENTED = YES`,
  `WARN_NO_PARAMDOC = YES`) remains open (`DOX-GAP-01`, `T011-GAP-01`), owned by T011/T037; T014 documents
  every new/changed declaration but does not enable the strict configuration.
- `T014-LIM-03` — The declared `FlowPolicy` is a bound declaration only: queueing, backpressure, deadline,
  and retry are neither enforced nor measured by T014, and no timing fidelity is claimed. Provider
  capability matching is T015.
- `T014-LIM-04` — `scripts/validate_xcom_endpoint_route_lifecycle.py` is a legacy SESN-era validator in the
  T014-owned path set; the repository-owned workflow does not use it, and T014 neither depends on nor edits
  it (`docs/xcom/endpoint-route-lifecycle.md` remains historical evidence only).
- `T014-LIM-05` — The lifecycle declares an acyclic route graph implicitly by refusing to drain or close a
  retained endpoint; general loop detection and graph analysis remain outside the core.
- `T014-LIM-06` — Restart reconciliation across processes is not implemented; "restart" here means a new
  controller instance in the same process, whose handles are rejected by opaque controller identity.

### 8.2 Gaps with owning tasks

| Gap | Description | Owner | Disposition |
| --- | --- | --- | --- |
| `T014-GAP-01` | The T009 `XCOM-CMP-005` requirement links disagree with the T008/T010 T014 attribution (§7.4). | T009 (register); T014 (source) | allocated; T014 records and promotes nothing |
| `T014-GAP-02` | Matching the declared policy against a provider's advertised capability, and enforcing it on the wire, is `XCOM-SW-CORE-004`'s provider half. | T015 | allocated; T014 binds and exposes the declaration only |
| `T014-GAP-03` | Consolidated core unit/negative coverage of interaction kinds, capabilities, policy, ownership, lifecycle, queue bounds, diagnostics, and recovery. | T016 | allocated |
| `T014-GAP-04` | Candidate acceptance under capability 007 remains with T039/T041. | T039/T041 | allocated; T014 submits for review |

### 8.3 Open items

- `T014-OPEN-01` — A later slice may decide to bind the declared policy to endpoints, to a plan-level
  policy set, or to the provider binding rather than to each route; T014 chooses the route generation,
  which is the smallest additive change that leaves every existing contract/item/provider consumer
  unchanged.
- `T014-OPEN-02` — If a later task moves the declared-policy binding to its own translation unit or adds a
  diagnostic code for an absent policy, the owning task updates the build contract and the inherited T020
  trace links; T014 changes no build file and adds no diagnostic code.

## 9. Definition of done (requirements view)

T014 is complete for this slice when: (a) the five plan-stage work products exist under
`docs/engineering/xcom/t014/` and are mutually consistent; (b) every requirement in §3–§4 has ≥ 1 named
check in `verification-plan.md`; (c) the implementation stage delivers the declared-policy binding, the
focused lifecycle cases, marks the T014 checkbox, and records `implementation.md`; (d) the deterministic
gate and the named checks pass at the candidate revision; (e) the package record is written; and (f) a
separate DeepSeek internal review records a passing verdict with no findings. This does **not** constitute
user acceptance, which remains T041.

## 10. Requirement-to-check index (implemented in `verification-plan.md`)

| Requirement | Primary check(s) |
| --- | --- |
| T014-STK-001 | CHK-02, CHK-03, CHK-23 |
| T014-STK-002 | CHK-05, CHK-06, CHK-09, NEG-01..NEG-18 |
| T014-STK-003 | CHK-04, CHK-08, CHK-17, CHK-20 |
| T014-STK-004 | CHK-18, CHK-19 |
| T014-STK-005 | CHK-02, CHK-21, CHK-22, CHK-25 |
| T014-SR-001 | CHK-04, CHK-05, CHK-09, NEG-01, NEG-02 |
| T014-SR-002 | CHK-05, CHK-12, NEG-03 |
| T014-SR-003 | CHK-06, CHK-09, NEG-04 |
| T014-SR-004 | CHK-06, CHK-09, NEG-05, NEG-06 |
| T014-SR-005 | CHK-04, CHK-05, CHK-07 |
| T014-SR-006 | CHK-07, NEG-07, NEG-08, NEG-09, NEG-10, NEG-13 |
| T014-SR-007 | CHK-10, CHK-13, NEG-11 |
| T014-SR-008 | CHK-10, CHK-13, NEG-14 |
| T014-SR-009 | CHK-11, NEG-15 |
| T014-SR-010 | CHK-12, NEG-16 |
| T014-SR-011 | CHK-08, CHK-14 |
| T014-SR-012 | CHK-12, CHK-14, NEG-16 |
| T014-SR-013 | CHK-14, NEG-12 |
| T014-SR-014 | CHK-08, CHK-14, NEG-11 |
| T014-SR-015 | CHK-07, CHK-15 |
| T014-SR-016 | CHK-06, CHK-09 |
| T014-SR-017 | CHK-17, NEG-17 |
| T014-SR-018 | CHK-18, NEG-19, NEG-24 |
| T014-SR-019 | CHK-19, NEG-21 |
| T014-SR-020 | CHK-20 |
| T014-SR-021 | CHK-02, CHK-21, CHK-22, CHK-25 |
| T014-SR-022 | CHK-23, NEG-22 |
