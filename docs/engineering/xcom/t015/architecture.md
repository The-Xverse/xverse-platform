# T015 Architecture — Explicit Provider Composition, Declared-Policy Matching, and the Owned Loopback Boundary

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T015 (capability 007, slice `T-CORE`) |
| Stage / role | plan → architecture |
| Revision | 1 |
| Baseline revision | `8aaa9eb29ffb349538552d709d4e6f37011b3e65` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-006`, `XCOM-CMP-007`, `XCOM-XLC-004`, `XCOM-XB-004`, `XCOM-XB-009`); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-007`, `XCOM-DU-008`); `docs/engineering/xcom/t011/architecture.md` (build envelope); `docs/engineering/xcom/t012/architecture.md` (subtree build/test contract); `docs/engineering/xcom/t014/architecture.md` (declared-policy binding) |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T015 is the **explicit provider composition and owned loopback boundary** of the X-COM core. It occupies the
seam between the T014 immutable endpoint/route lifecycle (with the declared bounded `FlowPolicy` on a route
generation) and the later observation, stimulation, and external-tool slices. It owns no observation,
stimulation, gateway, time-authority, or service-emulation behaviour; it owns the finite, serialized registry
that turns explicitly supplied source-linked provider objects into exact generation-bound provider-route
handles, the owned loopback realization, and the declared-policy ↔ provider capability matching that T014
allocated to it (`T014-GAP-02`).

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract
   → T013 core value/contract/item/diagnostic/policy types
   → T014 endpoint/route lifecycle + declared-policy binding
   → T015 explicit provider composition + declared-policy matching + owned loopback (this document)
   → T016 core tests
   → { T-XDL, T-OBS, T-STIM } → T-INTG (T035–T038) → T-REVIEW (T039/T041)
```

T015 is a **production-path** slice: the deterministic gate requires at least one changed
`src/xverse/xcom/**` path. The change is the additive declared-policy ↔ provider capability matching in
`ProviderComposition::prepare_route` plus exactly one new stable provider outcome; the existing descriptor,
registration, dispatch, loopback, FIFO, recovery, and diagnostic mechanics are re-verified unchanged. No build
file, XDL schema, contract, lifecycle, observation, or later-slice interface changes.

## 3. Boundary and context

### 3.1 System context

```text
        ┌──────────── XDL / io.xverse.xcom Profile + activation plan (read-only, T017/T019) ───────────┐
        │  declared bounded delivery policy (ordering/reliability/deadline/retry/queueDepth/overflow)   │
        └──────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                                   │ already decoded + validated upstream; T015 does not read it
   ┌──────────────── T014 endpoint/route lifecycle (read-only to T015) ──────────────────────────────────┐
   │  RouteSpec.has_policy()/policy() · RouteHandle · EndpointHandle · LifecycleController · route_policy │
   └──────────────────────────────────────────┬───────────────────────────────────────────────────────┘
                                              │ exact declarations + generation-bound handles
   ┌──────────────── T015 provider composition (src/xverse/xcom, xverse::xcom) ──────────────────────────┐
   │  provider.hpp/.cpp                                                                                   │
   │   ProviderDescriptor · DeliveryCapability · OrderingCapability · ProviderOutcome                     │
   │   ProviderRouteRequirements · ProviderRouteBinding · ProviderRouteHandle · ProviderRouteSnapshot     │
   │   ProviderRegistration · ProviderResult/ProviderStatus · CommunicationProvider (source-level IF)       │
   │   ProviderComposition: register_provider / prepare_route (+ declared-policy matching) / activate /     │
   │                        submit / receive / drain / close / route_state / reconcile                     │
   │   loopback_provider.hpp/.cpp: LoopbackProvider (fixed routes + reject-new FIFO queues)                │
   └──────────────────────────────────────────┬───────────────────────────────────────────────────────┘
                                              │ owned outcomes, immutable handles/snapshots
   ┌──────────────────────────────────────────▼───────────────────────────────────────────────────────┐
   │  consumers (read-only): T016 core tests, T021 observation integration, T025 validation session,       │
   │  T030–T034 gateway/provider contract suites                                                            │
   └───────────────────────────────────────────────────────────────────────────────────────────────────┘
        ┌──────────── T013 immutable values (read-only): FlowPolicy, Ordering/Reliability/OverflowPolicy ─┐
        │  DiagnosticCode/ValidationPhase/DiagnosticSet (T015 adds no core code or phase)                  │
        └─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T15-XB-1` Raw provider vs validated descriptor | call-scoped `ProviderDescriptorInput` | immutable `ProviderDescriptor` | Every retained descriptor is complete, bounded, and validated; a rejected input yields only a non-empty `DiagnosticSet`, never a partial or default descriptor. |
| `T15-XB-2` Registration vs ownership | an explicitly supplied caller-owned `CommunicationProvider&` | registry slots and issued provider-route handles | Only an exact registration generation plus provider/route/lifecycle generation tuple authenticates a route; names, addresses, and stale identities never grant ownership. |
| `T15-XB-3` Declared policy vs provider capability | the immutable `FlowPolicy` bound to a route generation (T014) and the requested `ProviderRouteRequirements` | the selected provider descriptor and its hard limits | T015 reconciles the two exactly at preparation: a claim, overflow, deadline, retry, or queue-depth that the provider cannot honour is rejected before any dispatch, with no substitution and no silent upgrade/weakening. |
| `T15-XB-4` Composition vs provider realization | the `CommunicationProvider` source-level interface and `ProviderRouteBinding` | concrete providers (loopback, independent fixture, future providers) | Composition validates and dispatches; a provider owns its own route resources and never receives composition or lifecycle mutation authority beyond the exact binding. |
| `T15-XB-5` Core vs later slices | `xverse::xcom` provider/loopback units | observation/stimulation/gateway adapters | Later slices consume T015; T015 depends on no later slice and embeds no transport, protocol, address, or domain primitive. |
| `T15-XB-6` Repository vs environment | committed source, tests, work products | admitted build inputs, build trees, host paths | Committed files are public-safe and offline; no ambient, network, filesystem, process, or dynamic-load access is introduced. |

### 3.3 Prohibited elements (must remain absent)

No TCP listener, external network peer, discovery, package manager/registry, dynamic provider loading,
filesystem access, process execution, legacy repository/binary access, domain-specific primitive (ECU, CAN,
SOME/IP, product name), new admitted dependency, competing configuration language, or unbounded resource.
These inherit the T007 global prohibitions, the T011 envelope, the T012 build contract, the accepted
`contracts/provider.md` "no ambient network discovery, shell execution, or legacy-repository access" rule, and
the constitution.

## 4. Components

Each component maps to a unit in `unit-specifications.md`. `T15-CMP-*` names are local to this document; the
accepted `XCOM-DU-007`/`XCOM-DU-008` identifiers and `XCOM-CMP-006`/`XCOM-CMP-007` components are the
authorised design units.

### 4.1 Provider composition components

- **`T15-CMP-DESC`** (`XCOM-DU-007`) — `provider.hpp`/`.cpp`: `DeliveryCapability`, `OrderingCapability`,
  `ProviderDescriptorInput`, and the immutable validated `ProviderDescriptor`.
- **`T15-CMP-OUTCOME`** (`XCOM-DU-007`) — the stable `ProviderOutcome` vocabulary, its `interaction/delivery/
  ordering_capability_bit` helpers, and the modeless `to_string`/`provider_diagnostic_code`/
  `provider_diagnostic_message` mappings, **extended by exactly one outcome** in T015.
- **`T15-CMP-HANDLE`** (`XCOM-DU-007`) — the opaque `ProviderRouteHandle`, `ProviderRouteSnapshot`,
  `ProviderRegistration`, `ProviderResult`/`ProviderStatus`, `ProviderRouteToken`, `ProviderRouteStateValue`,
  and `ProviderRouteBinding` values.
- **`T15-CMP-PROVIDER`** (`XCOM-DU-007`) — the `CommunicationProvider` source-level interface.
- **`T15-CMP-REG`** (`XCOM-DU-007`) — the fixed-capacity `ProviderRegistryConfiguration` and
  `ProviderComposition` registry (`kMaximumProviders = 8`).
- **`T15-CMP-DISPATCH`** (`XCOM-DU-007`) — the `prepare_route`/`activate_route`/`submit`/`receive`/
  `drain_route`/`close_route`/`route_state`/`reconcile_route` operations and their exact-handle
  authentication, including the **new** declared-policy matching.
- **`T15-CMP-MATCH`** (`XCOM-DU-007`, **new in T015**) — the declared `FlowPolicy` ↔ provider capability and
  requirement reconciliation performed inside `prepare_route` before any provider dispatch.

### 4.2 Owned loopback components

- **`T15-CMP-LOOP`** (`XCOM-DU-008`) — `loopback_provider.hpp`/`.cpp`: the fixed-capacity `LoopbackProvider`
  (`kMaximumRoutes = 4`), its one-mutex serialized route records, and its per-route reject-new FIFO queues
  (`kMaximumQueueItems = 8`); re-verified unchanged.
- **`T15-CMP-INDEP`** (`XCOM-DU-008`) — the second source-linked `IndependentProvider` test fixture proving
  replaceability; re-verified unchanged (T034 owns the fuller second-provider suite).

### 4.3 Work-product components

- **`T15-WP`** — the T015 repository-owned work-product set (`requirements.md`, `architecture.md`,
  `detailed-design.md`, `unit-specifications.md`, `verification-plan.md`, `implementation.md`,
  `internal-review.json`, and `reports/xcom-queue/t015-package.json`).

### 4.4 Consumed components (read-only)

`XCOM-CMP-004` core value/contract/policy types (`FlowPolicy`, `CommunicationContract`, `OriginKind`,
`DiagnosticCode`, `ValidationPhase`, `DiagnosticSet`), the T014 lifecycle (`RouteSpec`, `RouteHandle`,
`EndpointHandle`, `LifecycleController`), `XCOM-CMP-008` observation (`ObservationHub` seam), and the XDL
Profile/plan schema are consumed or matched but neither implemented nor altered by T015. The declared
`FlowPolicy` is consumed from `contract.hpp` and `endpoint_route_lifecycle.hpp`; no vocabulary is added.

## 5. Data flow (ordered)

1. **Validate a descriptor** — a consumer builds a call-scoped `ProviderDescriptorInput`;
   `ProviderDescriptor::create` validates bounded identity, canonical version, explicit source link, nonzero
   capability masks from the declared vocabulary, and finite limits, and returns an immutable descriptor or a
   deterministic diagnostic set.
2. **Register explicitly** — `ProviderComposition::register_provider` retains a self-consistent, explicitly
   supplied provider under the configured capacity prefix, rejects duplicate/unsupported/exhausted cases
   without mutation, and issues a strictly advancing registration generation.
3. **Prepare (authenticate)** — `prepare_route` authenticates the exact lifecycle route, source, and
   destination handles/declarations and requires the exact identity/digest/provider/contract/direction tuple,
   the route `validated`, and both endpoints `validated`/`active`.
4. **Prepare (match, new in T015)** — `prepare_route` resolves the selected registered provider descriptor,
   validates the requested `ProviderRouteRequirements` against the descriptor, and — when the bound route
   declares a `FlowPolicy` — derives the required delivery/ordering claim and reconciles the declared overflow,
   deadline, retry, and queue-depth bound with the request. Any mismatch rejects with a stable outcome before
   any provider dispatch.
5. **Prepare (dispatch)** — only after every check passes does composition build the owned
   `ProviderRouteBinding` and invoke the provider's private `prepare`, then issue the exact
   `ProviderRouteHandle` (composition/provider/registration generations, route identity/digest, lifecycle
   generations, provider route generation, payload bound, queue bound).
6. **Operate** — `activate_route` activates the provider route and, on first activation, the exact lifecycle
   route; `submit` authenticates the exact active handle and item binding, validates the payload bound, and
   (when an `ObservationHub` is enabled) reserves lossless observation capacity before provider mutation;
   `receive`/`drain_route`/`close_route`/`route_state`/`reconcile_route` authenticate the exact handle and the
   embedded lifecycle generation/state.
7. **Consume** — T016 (tests), T021 (observation), and T030–T034 (gateway/provider contract suites) consume
   the immutable descriptors, handles, snapshots, and stable outcomes without gaining registry mutation
   authority.

## 6. Interfaces

T015 exposes an in-process C++20 API only (no transport, no external ABI). The evolution rule of
`XCOM-XLC-004` ("additive methods with defaulted behaviour; no removal of an existing method") is preserved.

| Interface | Contract |
| --- | --- |
| `ProviderDescriptor::create(const ProviderDescriptorInput&)` | `noexcept`; `Result<ProviderDescriptor>`; validates identity (1–128 bytes), canonical version, source link, nonzero capability masks, and finite limits ≤ `kMaximumPayloadBytes`/32/32. |
| `ProviderComposition::register_provider(CommunicationProvider&)` | `noexcept`; `ProviderResult<ProviderRegistration>`; explicit source-linked registration; duplicate/unsupported/incompatible/full → `duplicate_provider`/`unsupported_contract_version`/`invalid_descriptor`/`provider_capacity_exhausted`; strictly advancing generation. |
| `ProviderComposition::prepare_route(lifecycle, route_spec, route_handle, source_handle, destination_handle, requirements)` | `noexcept`; `ProviderResult<ProviderRouteHandle>`; exact lifecycle authentication, requested-semantics validation, and **new** declared-policy matching before dispatch; no partial preparation. |
| `ProviderOutcome` **(extended)** | `noexcept` value enumeration; adds exactly one stable value `unsupported_policy` (external text `unsupported-policy`, code `XCOM-PROV-E030`, fixed message) for a declared policy the selected provider does not implement; every existing value/code/message is unchanged. |
| `ProviderComposition::activate_route/submit/receive/drain_route/close_route/route_state/reconcile_route` | `noexcept`; `ProviderStatus`/`ProviderResult<...>`; exact-handle and lifecycle-generation authentication; stable `invalid_provider_route_handle`/`lifecycle_mismatch`/`inactive_route`/`queue_saturated`/`interrupted_resource` outcomes; no mutation on rejection. |
| `CommunicationProvider` (source-level interface) | `noexcept` virtual operations; `descriptor()`/`descriptor_compatible()`/`instance_id()` public; `prepare`/`activate`/`submit`/`receive`/`drain`/`close`/`state`/`reconcile` private to `ProviderComposition`; no stable binary ABI and no discovery/dynamic loading. |
| `LoopbackProvider` | `noexcept`; owned fixed route/queue storage; one mutex; deterministic reject-new FIFO; `descriptor_compatible()` true only for the declared loopback claims within fixed storage. |
| `ProviderRouteHandle`/`ProviderRouteSnapshot`/`ProviderRegistration`/`ProviderResult`/`ProviderStatus` | `noexcept`; const accessors; handles/snapshots own their fixed fields and support concurrent const reads; assignment deleted where exact binding must be preserved. |

## 7. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Fail-closed safety | every descriptor, registration, preparation, dispatch, and match operation returns a value or a stable outcome; a rejected operation dispatches nothing and mutates nothing | T015-SR-001/002/004/005/007/008/009; NEG-01..NEG-21 |
| Explicit ownership | only an exact registration generation plus provider/route/lifecycle generation tuple authenticates a route; names and addresses never grant ownership | T015-SR-002/006/015; CHK-11 |
| Bounded resources | fixed compile-time registry/route/queue storage over a configured prefix, finite descriptor limits, finite generations | T015-SR-003/012/017; CHK-15 |
| No silent upgrade / no weakening | the declared policy is matched exactly once before dispatch; no substitution, no rebind; change requires a new generation | T015-SR-007/008/009/010/011; CHK-08, CHK-10 |
| Replaceability | the source-level `CommunicationProvider` boundary admits a second independent provider and isolates a failure to its own route | T015-SR-014; CHK-13 |
| Determinism | stable outcome text/code/message, byte-stable ordering, unchanged snapshots before/after rejection, deterministic FIFO | T015-SR-013/016; CHK-14 |
| Concurrency | one mutex per unit serializes mutation; no callback under a lock or while holding both unit locks; immutable values permit concurrent reads; exactly-once per-route delivery | T015-SR-018; CHK-16, NEG-22 |
| Domain neutrality | no provider address, protocol, transport, or domain primitive in a logical provider value | T015-SR-019; CHK-13, CHK-17 |
| Offline safety | standard-library only; no network, ambient, filesystem, process, or dynamic-load access | T015-SR-019; CHK-17 |
| Public safety | committed files carry no secret, private address, payload, or host path | T015-SR-020; CHK-18 |
| Documentation | every new/changed public declaration documents ownership/lifetime/thread-safety/failure | T015-SR-021; CHK-19 |
| Governance | no accepted artifact rewritten; registers re-validated; REF-002 unchanged | T015-SR-022; CHK-20, CHK-21, CHK-25 |

## 8. Consistency and constraints

- **Dependency direction preserved.** T015 depends only on T013 values, the T014 lifecycle, and the standard
  library; no later slice is referenced and no runtime unit depends on a build file.
- **Domain neutrality preserved.** No vocabulary is added beyond one provider-local outcome; the declared
  `FlowPolicy` vocabulary is consumed unchanged and no automotive or product primitive is introduced.
- **XDL centrality preserved.** The declared policy originates from the accepted Profile/plan (T017/T019); T015
  neither parses nor authors XDL, and wiring the plan policy into the route binding remains with the XDL/plan
  slices and T016 (`T015-LIM-06`).
- **Ownership preserved.** Only T015-owned provider/loopback paths, the T015 work products, and the T015
  checkbox change; no other task's path or test moves.
- **Maturity preserved.** Composition and loopback stay prototype control-plane/data-plane libraries;
  consolidated tests, executed sanitizer/static/Doxygen evidence, benchmarks, and acceptance remain with
  T016, T035–T037, and T039/T041.
- **Non-breaking.** The matching is derived from the existing `RouteSpec::has_policy()`/`policy()` and adds no
  public method parameter; unbound routes and every existing provider/observation consumer compile and behave
  unchanged. The single new `ProviderOutcome` value is additive; the three mapping switches are updated in
  place with no removed or renamed value.

## 9. Traceability

| Architecture element | T015 requirements |
| --- | --- |
| `T15-CMP-DESC`, `T15-XB-1` | T015-STK-001, T015-SR-001 |
| `T15-CMP-REG`, `T15-XB-2` | T015-STK-002, T015-SR-002, T015-SR-003 |
| `T15-CMP-DISPATCH`, `T15-XB-4` | T015-STK-003, T015-SR-004, T015-SR-005, T015-SR-006, T015-SR-015 |
| `T15-CMP-MATCH`, `T15-XB-3` | T015-STK-002, T015-STK-004, T015-SR-007, T015-SR-008, T015-SR-009, T015-SR-010, T015-SR-011 |
| `T15-CMP-LOOP`, `T15-CMP-INDEP` | T015-STK-001, T015-STK-004, T015-SR-012, T015-SR-013, T015-SR-014 |
| `T15-CMP-HANDLE`, `T15-CMP-PROVIDER` | T015-SR-006, T015-SR-015, T015-SR-018 |
| `T15-CMP-OUTCOME` | T015-SR-016 |
| `T15-XB-5` | T015-SR-019 |
| `T15-XB-6`, `T15-WP` | T015-STK-005, T015-SR-017, T015-SR-020, T015-SR-021, T015-SR-022, T015-SR-023 |
