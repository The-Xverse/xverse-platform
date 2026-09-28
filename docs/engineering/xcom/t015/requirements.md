# T015 Requirements — Explicit Provider Composition and the Owned Loopback Provider

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T015 (capability 007, slice `T-CORE`) |
| Task title | Implement explicit provider composition and the owned loopback provider |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `8aaa9eb29ffb349538552d709d4e6f37011b3e65` |
| Authorization | capability 007 accepted design and bounded implementation authorization (ACC002/ACC004/ACC005/ACC006/ACC007/ACC010/ACC011/ACC014/ACC015); ADR-0016; ADR-0018; ADR-0020 |
| Owning slice | `T-CORE` (T007 ownership register) |
| Predecessor | T014 (bounded endpoint/route lifecycle and declared-policy binding; reviewed terminal package) |
| Producer dependencies | T011 admitted offline build envelope (read-only inputs); T012 subtree CMake/CTest contract; T013 immutable core value/contract/item/diagnostic/policy types; T014 `RouteSpec::has_policy()`/`policy()` and exact generation-bound handles |
| Successor tasks | T016 (consolidated core unit/negative matrix), then T017–T034, T035–T041 |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}`; `docs/engineering/xcom/t008/requirements-register.{json,md}`; `docs/engineering/xcom/t009/architecture-model.{json,md}`; `docs/engineering/xcom/t010/unit-design.{json,md}` |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production
change and does not implement, accept, or integrate the candidate. The T015 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T015 — Implement explicit provider composition and the owned loopback provider.

### 1.1 Authority statement

This document specifies only the bounded T015 slice. It elaborates the accepted architecture components
`XCOM-CMP-006` "Provider boundary and composition" and `XCOM-CMP-007` "Owned loopback provider", the accepted
design units `XCOM-DU-007` "Provider boundary and composition" and `XCOM-DU-008` "Owned loopback provider",
and the accepted software requirements `XCOM-SW-CORE-006` (stable deterministic diagnostics) and
`XCOM-SW-CORE-007` (owned loopback provider and domain-neutral local runtime) that `docs/engineering/xcom/t008/`
attributes to T015, together with the provider half of `XCOM-SW-CORE-003` (fail-closed binding and activation)
and `XCOM-SW-CORE-004` (bounded delivery policy) that T014 explicitly allocated to T015 (`T014-GAP-02`,
`T014-LIM-03`). It does **not** redesign the accepted architecture, change a functional requirement, success
criterion, ADR, schema, or contract, fix an observation/stimulation/gateway value, implement T014 or T016–T034,
add a new admitted dependency, or accept or integrate any candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, the T007
ownership register, the T008 register, the T009 architecture model, the T010 unit design, the constitution, or
an accepted ADR is resolved in favour of the accepted source. A material gap is reported rather than guessed.
Unresolved gaps are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T015)

1. **Re-verify and own explicit provider composition** under `src/xverse/xcom/` in namespace `xverse::xcom`,
   realizing `XCOM-DU-007` (`XCOM-CMP-006`): the immutable validated `ProviderDescriptor`, the fixed-capacity
   `ProviderComposition` registry with explicit `register_provider`, the exact generation-bound
   `ProviderRouteHandle`, and the `prepare_route`/`activate_route`/`submit`/`receive`/`drain_route`/`close_route`/
   `route_state`/`reconcile_route` dispatch. The baseline already provides this source; T015 owns it, re-runs its
   unit, negative, and external-consumer checks, and records the exact candidate revision.
2. **Re-verify and own the owned loopback provider** (`XCOM-DU-008`, `XCOM-CMP-007`): the fixed-capacity
   `LoopbackProvider` with one serialized mutex, fixed per-route reject-new FIFO queues, deterministic
   `prepared → active → draining → closed` route resources, and exact drain/close semantics. It is re-verified
   unchanged: the new declared-policy matching is a composition-boundary concern (`detailed-design.md` `D-01`)
   and requires no loopback change, and no later-slice realization is implemented.
3. **Complete the missing provider half of `XCOM-SW-CORE-003`/`XCOM-SW-CORE-004`** allocated to T015 by T014:
   the declared bounded `FlowPolicy` bound to a route generation (T014) is today never matched against a
   provider's advertised capability. T015 adds the minimal, additive matching at the composition boundary:
   before any provider resource is prepared, a policy-bound route's declared delivery/ordering claim, overflow,
   deadline, retry, and queue-depth bound are reconciled with the requested `ProviderRouteRequirements` and the
   selected provider descriptor, and any mismatch fails closed with a stable provider outcome and **no** provider
   dispatch and **no** mutation.
4. **Add exactly one stable provider diagnostic outcome** for the new declared-policy rejection, without
   changing any existing provider outcome, code, message, or ordering (`XCOM-SW-CORE-006`).
5. **Add focused T015 unit and negative cases** for the new declared-policy matching and for the exact
   composition/loopback boundaries it must preserve, inside the existing `tests/xcom/provider_loopback/`
   executables. The consolidated cross-cutting matrix (all interaction kinds, provider capabilities, policy,
   ownership, lifecycle, queue bounds, diagnostics, recovery) remains T016.
6. **Re-verify every T015-owned provider and loopback path unchanged** where not extended: descriptor,
   registration, compatibility, ownership, lifecycle, FIFO, saturation, recovery, replaceability, diagnostic,
   and concurrency cases must still pass without weakening, renaming, or removing a case. An unbound route
   (declared through the unchanged 3-argument `RouteSpec::create`) must prepare exactly as at the baseline.
7. The T015 repository-owned work products and the T015 package record.

### 2.2 Explicit exclusions (must remain absent from the T015 candidate)

No observation, stimulation, journaling, time-authority, service-emulation lease, Protobuf/gRPC, gateway,
Argus/Maestro/Faults, compatibility, or legacy behaviour; no `xdl/`, `proto/`, or `src/xverse_xdl/` change; no
change to a `.cmake` file, the root `CMakeLists.txt`, or `src/xverse/xcom/CMakeLists.txt` (the
`xverse_xcom_provider_loopback` target already compiles `provider.cpp`/`loopback_provider.cpp` and already
registers the three provider-loopback test executables, so no build-file change and no inherited T020 trace-link
hash refresh is required); no change to `endpoint_route_lifecycle.{hpp,cpp}`, `contract.hpp`, `diagnostic.hpp`,
`core_types.hpp`, `item.hpp`, `value.hpp`, `result.hpp`, `observation.hpp`, or any other task's source; no new
admitted dependency; no network access, TCP listener, dynamic provider discovery/loading, filesystem access,
process execution, or legacy repository/binary access; no rewrite or weakening of an accepted ADR, requirement,
contract, test, REF-002 disposition, or another task's ownership path; no promotion of any REF-002 or capability
requirement; no acceptance or integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T015 |
| --- | --- | --- |
| Immutable contract/item/policy/diagnostic values, `FlowPolicy`, `DiagnosticCode`/`ValidationPhase` | T013 | complete (predecessor); consumed read-only |
| Endpoint/route lifecycle, exact generation-bound handles, declared-policy binding and `route_policy` read | T014 | complete (predecessor); consumed read-only; T015 matches the declared policy, it does not bind it |
| XDL-derived activation plan, Profile-aware compilation, plan decoding, plan tests | T017–T020 | complete (predecessor backlog); consumed read-only; T015 does not decode a plan |
| Observation boundary, records, best-effort/lossless behaviour, synthetic sink | T021–T024 | allocated; the existing `ObservationHub` seam is consumed unchanged |
| Validation stimulation boundary | T025–T029 | allocated |
| Consolidated core unit/negative matrix (interaction kinds, capabilities, policy, ownership, lifecycle, queue bounds, diagnostics, recovery) | T016 | allocated; T015 adds only focused cases for its own matching and boundaries |
| Second minimal synthetic provider contract suite and version rejection | T034 | allocated; T015 re-verifies the existing `independent_provider.hpp` fixture only |
| Executed sanitizer/static-analysis/Doxygen evidence, benchmarks | T035–T037 | allocated |
| Integration, validation, delivery bundle | T035–T040 | allocated |
| Independent/external review and user acceptance | T039/T041 | allocated |

## 3. Stakeholder requirements (`T015-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T015-STK-001**: Before the X-COM core is accepted, the program **shall** have one repository-owned,
  bounded, domain-neutral C++20 explicit provider composition and one owned loopback provider, physically under
  `src/xverse/xcom/`, that compile with the T011-admitted toolchain under the T012 warning-as-error contract.
- **T015-STK-002**: Provider composition **shall** fail closed: no request that cannot be honoured by the
  selected provider is dispatched, every capacity and limit is finite and explicit, no rejected operation
  mutates a registered provider, a prepared route, or a queue, and no declared delivery/ordering guarantee is
  silently strengthened or weakened.
- **T015-STK-003**: Every provider type **shall** make its ownership, lifetime, thread-safety, and failure
  contract explicit; immutable descriptors, handles, snapshots, and results **shall** be safe to copy and to
  read concurrently; no callback **shall** run under a provider or registry lock.
- **T015-STK-004**: Composition and loopback **shall** be offline and domain-neutral: normal use performs no
  network discovery, ambient configuration or secret lookup, filesystem access, process execution, dynamic
  provider loading, or legacy-repository access, contains no domain-specific primitive, and the loopback stays
  replaceable by another conforming source-linked provider.
- **T015-STK-005**: T015 **shall** preserve accepted intent: the delivered change is confined to the
  T015-owned provider/loopback paths, the T015 work products, and the capability task ledger, and it **shall**
  neither weaken an accepted requirement or test nor implement another task.

## 4. Software/engineering requirements (`T015-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Implemented" means the repository-owned source and its deterministic checks exist and pass; it is not
a runtime or production claim.

### 4.1 Immutable descriptor and explicit registration

- **T015-SR-001 [ubiquitous]**: `ProviderDescriptor` **shall** be an immutable declaration of a bounded logical
  provider identity, a canonical source-level contract version, an explicit source-link identity, nonzero
  supported interaction/delivery/ordering capability masks, and finite payload, route, and queue limits;
  `ProviderDescriptor::create` **shall** reject empty, malformed, zero, out-of-vocabulary, or over-bound input
  with a non-empty deterministic diagnostic set and **shall** expose no partial descriptor.
  - Refines: `XCOM-SW-CORE-005`, `XCOM-SW-CORE-007`; anchors FR-003, FR-009, FR-028; `XCOM-DU-007`;
    `XCOM-XLC-004`.
  - Verification intent: descriptor rejection table; CHK-04, CHK-05, NEG-01.
- **T015-SR-002 [ubiquitous]**: `ProviderComposition::register_provider` **shall** retain only an explicitly
  supplied source-linked provider whose retained descriptor is self-consistent, whose declared contract version
  equals the admitted source contract version, and whose object identity is nonzero; it **shall** reject a
  duplicate identity or instance (`duplicate_provider`), an unsupported version
  (`unsupported_contract_version`), an incompatible descriptor (`invalid_descriptor`), and a full configured
  registry (`provider_capacity_exhausted`) without replacing or mutating any existing slot, and **shall** issue
  a strictly advancing nonzero registration generation.
  - Refines: `XCOM-SW-CORE-005`, `XCOM-SW-CORE-007`; anchors FR-003, FR-009, FR-028; `XCOM-DU-007`;
    `XCOM-XLC-004`.
  - Verification intent: registration rejection matrix and re-entry case; CHK-04, CHK-05, NEG-02.
- **T015-SR-003 [ubiquitous]**: The provider registry **shall** be a fixed compile-time-bounded store
  (`kMaximumProviders = 8`) scanned only over the validated configured capacity prefix, **shall** never grow or
  allocate on the operational path, and **shall** perform no dynamic discovery, implicit default provider, or
  arbitrary library loading.
  - Refines: `XCOM-SW-CORE-007`; anchors FR-026, FR-028; `XCOM-DU-007`; T007 global prohibitions.
  - Verification intent: capacity/registration exhaustion and forbidden-API scan; CHK-02, CHK-05, CHK-15,
    CHK-17, NEG-02, NEG-23.

### 4.2 Exact route preparation and dispatch

- **T015-SR-004 [ubiquitous]**: `ProviderComposition::prepare_route` **shall** authenticate the exact supplied
  lifecycle route, source, and destination handles and their retained declarations, requiring exact identity,
  plan digest, provider identity, contract, and source/target directions, the route in `validated`, and both
  endpoints in `validated` or `active`; a route/digest/provider/contract/direction or state mismatch **shall**
  reject with a stable outcome (`route_mismatch`/`lifecycle_mismatch`/`provider_mismatch`) and **shall** prepare
  no provider resource.
  - Refines: `XCOM-SW-CORE-003`, `XCOM-SW-CORE-005`; anchors FR-006, FR-009; `XCOM-DU-007`; `XCOM-XB-004`.
  - Verification intent: preparation identity/state matrix; CHK-06, NEG-03, NEG-04, NEG-05.
- **T015-SR-005 [ubiquitous]**: Before dispatching to a provider, `prepare_route` **shall** validate the
  requested `ProviderRouteRequirements` against the selected provider descriptor: exact contract version,
  the interaction family contained in the advertised `interaction_mask`, the requested delivery and ordering
  contained in the advertised masks, a nonzero requested payload limit no greater than the advertised maximum,
  and a nonzero requested queue capacity no greater than the advertised maximum queue items; an unsupported
  request **shall** reject with the stable `unsupported_*`/`*_limit_exceeded` outcome and **shall** dispatch
  nothing.
  - Refines: `XCOM-SW-CORE-003`, `XCOM-SW-CORE-004`; anchors FR-006, FR-007; `XCOM-DU-007`; `XCOM-XB-004`.
  - Verification intent: requested-capability/limit rejection matrix; CHK-07, NEG-06..NEG-10.
- **T015-SR-006 [ubiquitous]**: `activate_route`, `submit`, `receive`, `drain_route`, `close_route`,
  `route_state`, and `reconcile_route` **shall** authenticate the exact composition instance, provider object,
  registration generation, provider identity, provider-local route token, and the embedded lifecycle route and
  endpoint generations/states; an inauthentic, stale, foreign, wrong-state, or inactive request **shall** reject
  with a stable outcome (`invalid_provider_route_handle`/`lifecycle_mismatch`/`inactive_route`/
  `interrupted_resource`) and **shall not** mutate a provider or lifecycle record.
  - Refines: `XCOM-SW-CORE-005`; anchors FR-009, FR-010; `XCOM-DU-007`; `XCOM-XB-004`.
  - Verification intent: handle/state/activation/submit/reconcile matrices; CHK-11, NEG-17, NEG-18, NEG-20.

### 4.3 Declared bounded delivery-policy ↔ provider capability matching (new in T015)

- **T015-SR-007 [ubiquitous]**: When the bound route declaration carries a declared `FlowPolicy`
  (`RouteSpec::has_policy()`), `prepare_route` **shall** derive the required delivery claim from
  `FlowPolicy::reliability()` and the required ordering claim from `FlowPolicy::ordering()` and **shall**
  require the requested `requirements.delivery`/`requirements.ordering` to equal those claims exactly; a
  contradiction **shall** reject with `unsupported_delivery`/`unsupported_ordering` before any provider
  dispatch and without mutation.
  - Refines: `XCOM-SW-CORE-003`, `XCOM-SW-CORE-004`; anchors FR-006, FR-007, FR-008; `XCOM-DU-007`;
    `T014-GAP-02`.
  - Verification intent: declared-policy requirement-contradiction cases; CHK-08, NEG-11, NEG-12.
- **T015-SR-008 [ubiquitous]**: The declared-claim mapping **shall** be exact and shall never substitute a
  weaker or stronger claim: `best-effort`→`best_effort`, `at-least-once`→`reliable`, `fifo`→`per_route_fifo`,
  `unordered`→`unordered`; a declared claim the admitted provider capability vocabulary cannot express
  (`at-most-once`, `exactly-once`, `priority`) **shall** reject with the stable
  `unsupported_delivery`/`unsupported_ordering` outcome rather than being mapped to a different guarantee, and
  the selected provider descriptor **shall** advertise the mapped claim bit.
  - Refines: `XCOM-SW-CORE-004`; anchors FR-006, FR-007, FR-008; `XCOM-DU-007`; `T014-GAP-02`.
  - Verification intent: unmappable-claim and provider-advertisement cases; CHK-08, NEG-11, NEG-12, NEG-16.
- **T015-SR-009 [ubiquitous]**: For a declared policy, `prepare_route` **shall** also match the non-capability
  dimensions the selected provider does not implement: the declared `overflow` **shall** be `reject`, and the
  declared `deadline_ms`/`retry` **shall** be `0`; otherwise it **shall** reject with the new stable
  `unsupported_policy` outcome. The requested `queue_capacity` **shall** not exceed the declared
  `queue_depth`, otherwise it **shall** reject with `queue_limit_exceeded`. Every rejection **shall** occur
  before provider dispatch and **shall not** mutate any record.
  - Refines: `XCOM-SW-CORE-004`; anchors FR-007, FR-008; `XCOM-DU-007`; `T014-GAP-02`.
  - Verification intent: overflow/deadline/retry/queue-depth rejection cases; CHK-09, NEG-13, NEG-14, NEG-15.
- **T015-SR-010 [ubiquitous]**: When the bound route declaration carries **no** declared policy
  (`RouteSpec::has_policy()` false), `prepare_route` **shall** behave exactly as at the baseline; the matching
  **shall** add no requirement, default, or restriction to an unbound route, so every existing unbound route
  caller and test compiles and behaves unchanged.
  - Refines: `XCOM-SW-CORE-003`, `XCOM-SW-CORE-004`; anchors FR-007; `XCOM-DU-007`; Constitution VII.
  - Verification intent: unbound-route additivity and regression cases; CHK-10, NEG-10.
- **T015-SR-011 [unwanted behaviour]**: If a request would weaken, strengthen, or silently replace a declared
  policy on a prepared or live route generation, then composition **shall** reject it: the declared policy is
  matched once at preparation, no public operation rebinds it afterwards, and changing it **shall** require
  closing and recreating the route as a new generation.
  - Refines: `XCOM-SW-CORE-004`; anchors FR-008; `XCOM-DU-007`; Constitution IX.
  - Verification intent: no-rebind structural case and recreated-generation case; CHK-08, CHK-11, NEG-11,
    NEG-12.

### 4.4 Owned loopback provider and provider operations

- **T015-SR-012 [ubiquitous]**: The owned `LoopbackProvider` **shall** own fixed compile-time-bounded route
  storage (`kMaximumRoutes = 4`) and one fixed reject-new FIFO queue per route
  (`kMaximumQueueItems = 8`), consider only the configured prefix, reuse empty/closed slots without growing
  storage, and issue a nonzero strictly advancing provider route generation; a duplicate nonclosed route
  identity or an exhausted prefix **shall** reject with `route_mismatch`/`route_capacity_exhausted` and
  **shall** leave every existing route unchanged.
  - Refines: `XCOM-SW-CORE-007`, `XCOM-SW-CORE-005`; anchors FR-007, FR-009, FR-028; `XCOM-DU-008`.
  - Verification intent: loopback capacity/isolation and reuse cases; CHK-12, NEG-21.
- **T015-SR-013 [ubiquitous]**: The loopback provider **shall** exchange all four interaction families
  deterministically: `submit` **shall** validate item contract/kind/source/route/provider binding and the
  per-route payload bound before copying an item into the queue, reject a full queue with `queue_saturated`
  while preserving every queued item and FIFO index, and `receive` **shall** return the oldest item as an
  independent owned copy or an explicit `queue_empty`; a draining route **shall** reject new submissions and a
  route **shall** release its resource only after an empty drain (`queued_items_remain` otherwise).
  - Refines: `XCOM-SW-CORE-004`, `XCOM-SW-CORE-007`; anchors FR-007, FR-008, FR-028; `XCOM-DU-008`.
  - Verification intent: interaction-family, saturation/FIFO/recovery, and drain/close cases; CHK-12,
    NEG-19, NEG-20.
- **T015-SR-014 [ubiquitous]**: A second, independently implemented source-linked provider object **shall**
  compose, register, prepare, activate, and exchange items through the same `CommunicationProvider` and
  `ProviderComposition` boundary, proving replaceability; a rejection or failure of one provider **shall not**
  change any unrelated registered provider or route.
  - Refines: `XCOM-SW-CORE-007`; anchors FR-009, FR-028; `XCOM-DU-007`, `XCOM-DU-008`.
  - Verification intent: independent-provider contract and isolation cases; CHK-13, NEG-05.
- **T015-SR-015 [ubiquitous]**: `ProviderComposition` **shall** reconcile persisted provider and lifecycle
  state without inferring ownership from a name or address: `reconcile_route` **shall** accept only an exact
  handle whose provider state and lifecycle generation/state agree and **shall** report mismatch as an explicit
  `interrupted_resource` outcome, never as success.
  - Refines: `XCOM-SW-CORE-005`; anchors FR-010; `XCOM-DU-007`.
  - Verification intent: reconciliation mismatch case; CHK-11, NEG-20.

### 4.5 Diagnostics, bounds, concurrency, and safety

- **T015-SR-016 [ubiquitous]**: Every provider outcome **shall** map to a stable external text, diagnostic
  code, and explanation with deterministic ordering, and the new declared-policy rejection **shall** add
  exactly one stable provider outcome (`unsupported_policy`) without renaming, recoding, reordering, or
  removing any existing provider outcome, code, or message.
  - Refines: `XCOM-SW-CORE-006`; anchors FR-025; SC-001; `XCOM-DU-007`, `XCOM-DU-008`.
  - Verification intent: exact-diagnostic byte table extended by the new row; CHK-14, NEG-13.
- **T015-SR-017 [ubiquitous]**: Every provider unit **shall** declare finite resource bounds and a declared
  overflow behaviour: providers ≤ 8; loopback routes ≤ 4 and queue items ≤ 8; descriptor limits payload
  ≤ 65,536 bytes, routes ≤ 32, and queue items ≤ 32; provider and registration generations bounded by
  `std::uint64_t` with explicit exhaustion; no queue, retry, or depth is unbounded; and the declared policy is
  never reinterpreted as a provider or registry capacity.
  - Refines: `XCOM-SW-CORE-004`, `XCOM-SW-CORE-007`; anchors FR-007; `XCOM-DU-007`, `XCOM-DU-008`; T010 bounds
    vocabulary.
  - Verification intent: bounds matrix and exhaustion cases; CHK-15, NEG-02, NEG-10, NEG-15, NEG-21.
- **T015-SR-018 [ubiquitous]**: Provider composition and every provider operation, including the new
  declared-policy matching, **shall** be serialized by one internal mutex per unit; no provider callback or
  registry callback **shall** run under a lock (and never while holding both the registry and a provider lock);
  immutable values, handles, and snapshots **shall** support concurrent const reads; and concurrent
  submit/receive **shall** deliver each accepted item exactly once without loss, duplication, or reordering
  within a route.
  - Refines: `XCOM-SW-CORE-005`, `XCOM-SW-CORE-007`; anchors FR-010; `XCOM-DU-007`, `XCOM-DU-008`.
  - Verification intent: registration re-entry, concurrent submit/receive, and serialized matching cases;
    CHK-16, NEG-22.
- **T015-SR-019 [ubiquitous]**: Provider composition and the loopback provider **shall** perform no network,
  socket, resolver, TLS, ambient, secret, filesystem, process, dynamic-load, or legacy access, **shall** add no
  admitted dependency beyond the C++ standard library, and **shall** remain domain-neutral.
  - Refines: `XCOM-SW-CORE-007` (domain-neutral local runtime half); anchors FR-001, FR-026, FR-028; ADR-0018;
    Constitution IX.
  - Verification intent: forbidden-API source scan plus the successful offline build; CHK-17, NEG-23.
- **T015-SR-020 [ubiquitous]**: Committed source, tests, and work products **shall** contain no credential,
  private address, unrestricted payload, proprietary source excerpt, environment-specific absolute host path,
  or sensitive deployment value.
  - Refines: Constitution X; anchors FR-027; `XCOM-SW-INTG` public-safe evidence rule.
  - Verification intent: public-safety scan; CHK-18, NEG-24.
- **T015-SR-021 [ubiquitous]**: Every new or changed public C/C++ declaration **shall** carry useful Doxygen
  documentation including its ownership, lifetime, thread-safety, and failure contract, without weakening the
  admitted repository documentation configuration.
  - Refines: `XCOM-SW-CORE` Doxygen; anchors FR-029; `XCOM-DU-007`/`XCOM-DU-008` Doxygen plan; Constitution X.
  - Verification intent: declaration inspection and the existing documentation validator; CHK-19; strict
    declaration Doxygen remains `DOX-GAP-01`, owned by T011/T037.
- **T015-SR-022 [ubiquitous]**: The T015 candidate **shall** change no accepted requirement, ADR, contract,
  schema, another task's ownership path, or existing test case, **shall** implement no later task, **shall**
  keep the REF-002 disposition `unchanged` with an empty `promoted` list, and **shall** record the
  `XCOM-CMP-006`/`XCOM-SW-CORE-003` link observation described in §7.3 without rewriting it.
  - Refines: ADR-0018, ADR-0020; T007 global prohibitions; anchors FR-030, FR-035; Constitution VII, IX.
  - Verification intent: `git diff --name-only <baseline> --` boundary inspection; register validators;
    CHK-02, CHK-20, CHK-21, CHK-25.
- **T015-SR-023 [ubiquitous]**: The T015 candidate **shall** satisfy the deterministic Fabro gate for
  implementation tasks: the five plan-stage work products and the implementation record exist, at least one
  `src/xverse/xcom/**` path changes, `cmake` configure, build, test discovery, and the full `ctest` suite pass,
  and `git diff --check` is clean; the T015 checkbox is marked complete **only** in the implementation stage.
  - Refines: ADR-0020; anchors FR-030; Constitution X.
  - Verification intent: `xcom_feature_gate.py verify T015 <baseline>`; `git diff --check`; CHK-22, CHK-23,
    NEG-25.

## 5. Requirement-to-accepted-anchor traceability

| T015 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T015-STK-001 | `XCOM-SW-CORE-006/007` | XCOM-SYS-FR-001/025/026/028 | FR-001, FR-025, FR-026, FR-028 | IX, X |
| T015-STK-002 | `XCOM-SW-CORE-003/004/006` | XCOM-SYS-FR-006/007/008/025 | FR-006, FR-007, FR-008, FR-025 | IX |
| T015-STK-003 | `XCOM-SW-CORE-005` | XCOM-SYS-FR-009/010 | FR-009, FR-010 | V, IX |
| T015-STK-004 | `XCOM-SW-CORE-007` | XCOM-SYS-FR-001/026/028 | FR-001, FR-026, FR-028 | II, VII |
| T015-STK-005 | Constitution VII/IX; ADR-0018/0020 | – | FR-030 | VII, IX, X |
| T015-SR-001 | `XCOM-SW-CORE-005/007` | XCOM-SYS-FR-003/009 | FR-003, FR-009, FR-028 | IX |
| T015-SR-002 | `XCOM-SW-CORE-005/007` | XCOM-SYS-FR-003/009 | FR-003, FR-009, FR-028 | IX |
| T015-SR-003 | `XCOM-SW-CORE-007` | XCOM-SYS-FR-026/028 | FR-026, FR-028 | II, VII |
| T015-SR-004 | `XCOM-SW-CORE-003/005` | XCOM-SYS-FR-006/009 | FR-006, FR-009 | IX |
| T015-SR-005 | `XCOM-SW-CORE-003/004` | XCOM-SYS-FR-006/007 | FR-006, FR-007 | IX |
| T015-SR-006 | `XCOM-SW-CORE-005` | XCOM-SYS-FR-009/010 | FR-009, FR-010 | IX |
| T015-SR-007 | `XCOM-SW-CORE-003/004` | XCOM-SYS-FR-006/007/008 | FR-006, FR-007, FR-008 | IX |
| T015-SR-008 | `XCOM-SW-CORE-004` | XCOM-SYS-FR-007/008 | FR-007, FR-008 | IX |
| T015-SR-009 | `XCOM-SW-CORE-004` | XCOM-SYS-FR-007/008 | FR-007, FR-008 | IX |
| T015-SR-010 | `XCOM-SW-CORE-003/004` | XCOM-SYS-FR-006/007 | FR-006, FR-007 | VII, IX |
| T015-SR-011 | `XCOM-SW-CORE-004` | XCOM-SYS-FR-008 | FR-008 | IX |
| T015-SR-012 | `XCOM-SW-CORE-005/007` | XCOM-SYS-FR-007/009/028 | FR-007, FR-009, FR-028 | IX |
| T015-SR-013 | `XCOM-SW-CORE-004/007` | XCOM-SYS-FR-007/008/028 | FR-007, FR-008, FR-028 | IX |
| T015-SR-014 | `XCOM-SW-CORE-007` | XCOM-SYS-FR-009/028 | FR-009, FR-028 | IX |
| T015-SR-015 | `XCOM-SW-CORE-005` | XCOM-SYS-FR-010 | FR-010 | IX |
| T015-SR-016 | `XCOM-SW-CORE-006` | XCOM-SYS-FR-025 | FR-025 | SC-001 |
| T015-SR-017 | `XCOM-SW-CORE-004/007` | XCOM-SYS-FR-007/028 | FR-007, FR-028 | IX |
| T015-SR-018 | `XCOM-SW-CORE-005/007` | XCOM-SYS-FR-010/028 | FR-010, FR-028 | IX |
| T015-SR-019 | `XCOM-SW-CORE-007` | XCOM-SYS-FR-001/026/028 | FR-001, FR-026, FR-028 | II, VII |
| T015-SR-020 | public-safe evidence rule | XCOM-SYS-FR-027 | FR-027 | X |
| T015-SR-021 | `XCOM-SW-CORE` Doxygen | XCOM-SYS-FR-029 | FR-029 | X |
| T015-SR-022 | Constitution; ADR-0018/0020 | XCOM-SYS-FR-035 | FR-030, FR-035 | VII, IX |
| T015-SR-023 | ADR-0020 | – | FR-030 | X |

`XCOM-SW-CORE-006` and `XCOM-SW-CORE-007` are the accepted capability-007 software requirements
(`docs/engineering/xcom/t008/requirements-register.{json,md}`) attributed to T015; `XCOM-SW-CORE-003`,
`-004`, and `-005` are attributed to T013/T014 and are refined here only for their allocated provider half.
`XCOM-DU-007`/`XCOM-DU-008` are the accepted T010 design units, `XCOM-CMP-006`/`XCOM-CMP-007` the accepted T009
architecture components, `XCOM-XLC-004` the accepted provider contract, and the system requirements and `SC-*`
the accepted `specs/007-xcom-core/spec.md` statements.

## 6. REF-002 disposition

T015 owns no REF-002 SADS ID. It provides the explicit provider composition, the owned loopback provider, and
the declared-policy capability matching against which the allocated REF-002 communication IDs
(`XVE-SYS-0139`–`0158`) and their shared contributions are later implemented and verified. T015 changes no
required disposition: the capability `ref002.disposition` stays `unchanged` with an empty `promoted` list
(T015-SR-022). No allocated, deferred, or target SADS requirement is reported as implemented, and no
`XVE-SYS-*` ID is promoted.

## 7. Affected paths

### 7.1 Paths the T015 candidate changes

| Path | Change | Notes |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/provider.hpp` | edit | adds exactly one `ProviderOutcome` value (`unsupported_policy`) with its documentation; documents the declared-policy matching contract on `prepare_route`; no existing declaration removed, renamed, or changed |
| `src/xverse/xcom/src/provider.cpp` | edit | adds the declared-policy ↔ provider capability matching in `prepare_route` (claim mapping, requirement consistency, overflow/deadline/retry/queue-depth reconciliation) and the serialization of the new outcome in the existing `to_string`/`provider_diagnostic_code`/`provider_diagnostic_message` switches; no existing outcome, code, message, or ordering changed |
| `tests/xcom/provider_loopback/test_support.hpp` | edit | adds an additive policy-bound fixture and a capability-selecting descriptor helper for the new T015 cases; existing `Scenario`/`descriptor` behaviour unchanged |
| `tests/xcom/provider_loopback/unit_tests.cpp` | edit | adds focused declared-policy matching, unbound-additivity, and policy-bound concurrency cases; existing cases unchanged |
| `tests/xcom/provider_loopback/negative_tests.cpp` | edit | adds focused declared-policy rejection cases and extends the exact-diagnostic table with the new outcome row; existing rows unchanged |
| `docs/engineering/xcom/t015/requirements.md` | add | this document |
| `docs/engineering/xcom/t015/architecture.md` | add | boundary, components, data flow, interfaces |
| `docs/engineering/xcom/t015/detailed-design.md` | add | matching rules, failure semantics, bounds, Doxygen/design |
| `docs/engineering/xcom/t015/unit-specifications.md` | add | units, ownership/lifetime/thread-safety/bounds, traceability |
| `docs/engineering/xcom/t015/verification-plan.md` | add | named checks, negative cases, commands |
| `docs/engineering/xcom/t015/implementation.md` | add (implementation stage) | realized change and evidence |
| `docs/engineering/xcom/t015/internal-review.json` | add (review stage) | DeepSeek internal review |
| `specs/007-xcom-core/tasks.md` | edit T015 checkbox (implementation stage) | capability task ledger |
| `reports/xcom-queue/t015-package.json` | add (package stage) | exact-candidate package record |

### 7.2 T015-owned provider/loopback paths consumed and re-verified

| Path | Owner | Role for T015 |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/loopback_provider.hpp` | T-CORE (T015) | owned loopback declaration; re-verified unchanged (matching lives in composition, no candidate change) |
| `src/xverse/xcom/src/loopback_provider.cpp` | T-CORE (T015) | loopback realization; re-verified unchanged (no candidate change) |
| `tests/xcom/provider_loopback/consumer/main.cpp` | T-CORE (T015) | external-consumer fixture; re-verified unchanged (public include + build/link) |
| `tests/xcom/provider_loopback/consumer/provider_mutation_rejection.cpp` | T-CORE (T015) | compile-time mutation-rejection fixture; re-verified unchanged |
| `tests/xcom/provider_loopback/independent_provider.hpp` | T-CORE (T015) | second source-linked provider fixture proving replaceability; re-verified unchanged |
| `tests/xcom/observation/integration/*` | T-OBS (T021) | existing consumer of the provider boundary; must still compile and pass unchanged |

### 7.3 Consumed, read-only foundation (not changed by T015)

| Path | Owner | Role for T015 |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/endpoint_route_lifecycle.hpp`, `src/xverse/xcom/src/endpoint_route_lifecycle.cpp` | T014 (complete) | exact generation-bound handles, declarations, and the declared `FlowPolicy` (`has_policy()`/`policy()`/`route_policy`); read-only |
| `src/xverse/xcom/include/xverse/xcom/contract.hpp`, `src/xverse/xcom/src/contract.cpp` | T013 (complete) | `FlowPolicy`, `OrderingPolicy`, `ReliabilityPolicy`, `OverflowPolicy`, `CommunicationContract`; read-only |
| `src/xverse/xcom/include/xverse/xcom/diagnostic.hpp`, `src/xverse/xcom/src/diagnostic.cpp` | T013 (complete) | `DiagnosticCode`/`ValidationPhase`/`DiagnosticSet`; T015 adds no code or phase |
| `src/xverse/xcom/include/xverse/xcom/{value,item,result,core_types}.hpp` | T013 (complete) | bounded primitives and aggregate; read-only |
| `src/xverse/xcom/include/xverse/xcom/observation.hpp` | T021 (baseline) | provider-neutral observation hub seam consumed unchanged by `ProviderComposition` |
| `src/xverse/xcom/CMakeLists.txt`, `cmake/*.cmake`, `CMakeLists.txt` | shared (serialized, T012) | T012 subtree build/test contract; T015 changes none |
| `docs/engineering/xcom/t008/*`, `t009/*`, `t010/*` | T008/T009/T010 | accepted registers and models; the §7.4 observation is recorded, not rewritten |
| `docs/xcom/provider*.{md,json}`, `engineering/**/*.json` | legacy/T020 (inherited) | historical SESN evidence and inherited T020 provenance; T015 changes no linked path, so no inherited hash refresh is required |

### 7.4 Recorded attribution observation (not resolved by T015)

The accepted `docs/engineering/xcom/t009/architecture-model.json` lists `XCOM-CMP-006` requirement links as
`XCOM-SW-CORE-003` and `XCOM-SYS-FR-010`, and `XCOM-CMP-007` links as `XCOM-SW-CORE-004` and
`XCOM-SYS-FR-008`, while `docs/engineering/xcom/t008/requirements-register.json` attributes `XCOM-SW-CORE-006`
and `XCOM-SW-CORE-007` to T015 and `docs/engineering/xcom/t010/unit-design.json` links `XCOM-DU-007` to
`XCOM-SW-CORE-005/-007/-008` and `XCOM-DU-008` to `XCOM-SW-CORE-007/-009`. The registers are owned by
T008/T009/T010 and remain `partial`/`unreconciled` (analysis A12). T015 records this observation, implements
the source as the T008 T015 attribution and the `XCOM-DU-007`/`XCOM-DU-008` unit design direct, and rewrites
nothing (T015-SR-022).

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- `T015-LIM-01` — The composition and loopback are prototype control-plane/data-plane libraries: they make no
  runtime, transport, timing, network, compatibility, or production-readiness claim and are not yet
  user-accepted (T041).
- `T015-LIM-02` — Strict declaration-level Doxygen (`WARN_IF_UNDOCUMENTED = YES`, `WARN_NO_PARAMDOC = YES`)
  remains open (`DOX-GAP-01`, `T011-GAP-01`), owned by T011/T037; T015 documents every new/changed declaration
  but does not enable the strict configuration.
- `T015-LIM-03` — The declared-policy matching is a preparation-time decision only: deadline, retry, and
  non-`reject` overflow are rejected as unsupported rather than implemented, and no wire enforcement, timing
  fidelity, or measurement is claimed. A provider that genuinely implements them would need an extended
  capability vocabulary (recorded as `T015-OPEN-01`).
- `T015-LIM-04` — The owned loopback is test evidence only: passing its suite proves no network provider,
  transport protocol, or legacy bridge compatible (`contracts/provider.md`).
- `T015-LIM-05` — Restart reconciliation across processes is not implemented; here "restart" means a new
  composition/provider instance in the same process, whose earlier handles are rejected by opaque identity.
- `T015-LIM-06` — The declared policy is bound to a route generation by T014; wiring the activation-plan
  (T019) or Profile (T017) policy into that route binding remains with the XDL/plan slices and T016.

### 8.2 Gaps with owning tasks

| Gap | Description | Owner | Disposition |
| --- | --- | --- | --- |
| `T015-GAP-01` | Matching the declared policy against a provider's advertised capability was allocated to T015 by T014 (`T014-GAP-02`). | T015 | closed by T015-SR-007..-011 |
| `T015-GAP-02` | Consolidated core unit/negative coverage of interaction kinds, capabilities, policy, ownership, lifecycle, queue bounds, diagnostics, and recovery. | T016 | allocated |
| `T015-GAP-03` | A second, fuller synthetic provider and version-rejection contract suite. | T034 | allocated; T015 re-verifies the existing fixture only |
| `T015-GAP-04` | Executed sanitizer/static-analysis/Doxygen/benchmark evidence and the delivery bundle. | T035–T040 | allocated |
| `T015-GAP-05` | Candidate acceptance under capability 007 remains with T039/T041. | T039/T041 | allocated; T015 submits for review |

### 8.3 Open items

- `T015-OPEN-01` — The admitted provider capability vocabulary (`DeliveryCapability`, `OrderingCapability`)
  cannot express `at-most-once`, `exactly-once`, or `priority`; T015 rejects those declarations fail-closed.
  A later protocol/provider capability (T034 or an adapter capability) may extend the vocabulary additively;
  T015 adds no capability bit.
- `T015-OPEN-02` — If a later task moves the declared-policy matching into its own translation unit or adds a
  second provider outcome, the owning task updates the build contract and the inherited T020 trace links; T015
  changes no build file and adds exactly one provider outcome.

## 9. Definition of done (requirements view)

T015 is complete for this slice when: (a) the five plan-stage work products exist under
`docs/engineering/xcom/t015/` and are mutually consistent; (b) every requirement in §3–§4 has ≥ 1 named check
in `verification-plan.md`; (c) the implementation stage delivers the declared-policy matching, the new stable
provider outcome, the focused provider/loopback cases, marks the T015 checkbox, and records
`implementation.md`; (d) the deterministic gate and the named checks pass at the candidate revision; (e) the
package record is written; and (f) a separate DeepSeek internal review records a passing verdict with no
findings. This does **not** constitute user acceptance, which remains T041.

## 10. Requirement-to-check index (implemented in `verification-plan.md`)

| Requirement | Primary check(s) |
| --- | --- |
| T015-STK-001 | CHK-02, CHK-03, CHK-22 |
| T015-STK-002 | CHK-05, CHK-07, CHK-08, CHK-09, NEG-01..NEG-21 |
| T015-STK-003 | CHK-04, CHK-11, CHK-16, CHK-19 |
| T015-STK-004 | CHK-13, CHK-17, CHK-18 |
| T015-STK-005 | CHK-02, CHK-20, CHK-21, CHK-25 |
| T015-SR-001 | CHK-04, CHK-05, NEG-01 |
| T015-SR-002 | CHK-04, CHK-05, NEG-02 |
| T015-SR-003 | CHK-02, CHK-05, CHK-15, CHK-17, NEG-02, NEG-23 |
| T015-SR-004 | CHK-06, NEG-03, NEG-04, NEG-05 |
| T015-SR-005 | CHK-07, NEG-06, NEG-07, NEG-08, NEG-09, NEG-10 |
| T015-SR-006 | CHK-11, NEG-17, NEG-18, NEG-20 |
| T015-SR-007 | CHK-08, NEG-11, NEG-12 |
| T015-SR-008 | CHK-08, NEG-11, NEG-12, NEG-16 |
| T015-SR-009 | CHK-09, NEG-13, NEG-14, NEG-15 |
| T015-SR-010 | CHK-10, NEG-10 |
| T015-SR-011 | CHK-08, CHK-11, NEG-11, NEG-12 |
| T015-SR-012 | CHK-12, NEG-21 |
| T015-SR-013 | CHK-12, NEG-19, NEG-20 |
| T015-SR-014 | CHK-13, NEG-05 |
| T015-SR-015 | CHK-11, NEG-20 |
| T015-SR-016 | CHK-14, NEG-13 |
| T015-SR-017 | CHK-15, NEG-02, NEG-10, NEG-15, NEG-21 |
| T015-SR-018 | CHK-16, NEG-22 |
| T015-SR-019 | CHK-17, NEG-23 |
| T015-SR-020 | CHK-18, NEG-24 |
| T015-SR-021 | CHK-19 |
| T015-SR-022 | CHK-02, CHK-20, CHK-21, CHK-25 |
| T015-SR-023 | CHK-22, CHK-23, NEG-25 |
