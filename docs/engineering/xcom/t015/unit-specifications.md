# T015 Unit Specifications — Provider Composition, Declared-Policy Matching, and Owned Loopback Units

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T015 (capability 007, slice `T-CORE`) |
| Stage / role | plan → unit specifications (pre-code) |
| Revision | 1 |
| Baseline revision | `8aaa9eb29ffb349538552d709d4e6f37011b3e65` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Accepted unit design | `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-007`, `XCOM-DU-008`; components `XCOM-CMP-006`, `XCOM-CMP-007`) |
| Classification | Public-safe engineering work product |

These unit specifications elaborate, without weakening, the accepted T010 unit design for `XCOM-DU-007`
"Provider boundary and composition" and `XCOM-DU-008` "Owned loopback provider". All T015 source units map to
`XCOM-DU-007`/`XCOM-DU-008` and components `XCOM-CMP-006`/`XCOM-CMP-007`; T015 does not rewrite the T009/T010
registers, and the §7.4 attribution observation in `requirements.md` is recorded only.

## 2. Unit inventory

| Unit (T015) | Accepted unit | Component | Kind | Language | Path(s) | Change |
| --- | --- | --- | --- | --- | --- | --- |
| `T015-U-DESC` | `XCOM-DU-007` | `T15-CMP-DESC` | control-plane | cpp | `provider.hpp`, `provider.cpp` | re-verified unchanged |
| `T015-U-OUTCOME` | `XCOM-DU-007` | `T15-CMP-OUTCOME` | control-plane | cpp | `provider.hpp`, `provider.cpp` | extended (one outcome) |
| `T015-U-HANDLE` | `XCOM-DU-007` | `T15-CMP-HANDLE` | control-plane | cpp | `provider.hpp`, `provider.cpp` | re-verified unchanged |
| `T015-U-PROVIDER` | `XCOM-DU-007` | `T15-CMP-PROVIDER` | control-plane | cpp | `provider.hpp` | re-verified unchanged |
| `T015-U-REG` | `XCOM-DU-007` | `T15-CMP-REG` | control-plane | cpp | `provider.hpp`, `provider.cpp` | re-verified unchanged |
| `T015-U-DISPATCH` | `XCOM-DU-007` | `T15-CMP-DISPATCH` | data-plane | cpp | `provider.hpp`, `provider.cpp` | extended (matching hook + docs) |
| `T015-U-MATCH` | `XCOM-DU-007` | `T15-CMP-MATCH` | data-plane | cpp | `provider.cpp` | **new** |
| `T015-U-LOOP` | `XCOM-DU-008` | `T15-CMP-LOOP` | test-fixture | cpp | `loopback_provider.hpp`, `loopback_provider.cpp` | re-verified unchanged |
| `T015-U-INDEP` | `XCOM-DU-008` | `T15-CMP-INDEP` | test-fixture | cpp | `tests/xcom/provider_loopback/independent_provider.hpp` | re-verified unchanged |

## 3. Unit specifications

### 3.1 `T015-U-DESC` — immutable validated provider descriptor

- **Interface**: `DeliveryCapability`, `OrderingCapability`, `ProviderDescriptorInput`, `ProviderDescriptor`
  and its factory/accessors.
- **Behaviour**: validates and owns bounded provider identity, canonical version, explicit source link, nonzero
  capability masks, and finite payload/route/queue limits, independently of any address or realization.
- **Ownership**: caller-owns-value (inputs and returned descriptor). **Lifetime**: invocation-scoped.
  **Thread-safety**: immutable-value.
- **Bounds**: identity ≤ 128 bytes; version ≤ 32 bytes; payload 1–65,536; routes 1–32; queue 1–32.
  **Overflow**: `fail-closed`.
- **Failure**: `rejected` with `required_field`, `invalid_version`, or `bound_exceeded`; `noexcept`; no partial
  descriptor.
- **Doxygen**: group `xcom_core`; per-declaration tags (baseline satisfied).
- **Planned evidence**: CHK-04, CHK-05, CHK-15; NEG-01.

### 3.2 `T015-U-OUTCOME` — stable provider outcome vocabulary (extended)

- **Interface**: `ProviderOutcome`, the capability-bit helpers, `to_string`, `provider_diagnostic_code`,
  `provider_diagnostic_message`, `ProviderRouteState`, `ProviderResult<T>`, `ProviderStatus`.
- **Behaviour**: maps every outcome to stable external text, code, and explanation; **adds exactly one** value
  `unsupported_policy` with text `unsupported-policy`, code `XCOM-PROV-E030`, and the fixed message; every
  existing value/code/message is unchanged.
- **Ownership**: caller-owns-value. **Lifetime**: invocation-scoped. **Thread-safety**: immutable-value.
- **Bounds**: fixed enumeration and fixed text. **Overflow**: `n/a`.
- **Failure**: an unknown (out-of-vocabulary) outcome is never produced by the units; the mapping switches are
  exhaustive over the declared values.
- **Doxygen**: group `xcom_core`; the new value carries `@brief` and the inherited ownership/lifetime/
  thread-safety/failure clauses.
- **Planned evidence**: CHK-14; NEG-13.

### 3.3 `T015-U-HANDLE` — opaque provider-route handle, snapshot, and registration

- **Interface**: `ProviderRouteHandle`, `ProviderRouteSnapshot`, `ProviderRegistration`,
  `ProviderRouteToken`, `ProviderRouteStateValue`, `ProviderRouteBinding`.
- **Behaviour**: owns the exact composition/provider/registration generations, route identity/digest, lifecycle
  generations, provider route generation, payload/queue bounds, and point-in-time state; copies preserve the
  binding; assignment is deleted where exact binding must be preserved.
- **Ownership**: composition-issued-handle; providers own their own route resources.
  **Lifetime**: registration-generation for handles; invocation-scoped for snapshots. **Thread-safety**:
  immutable-value.
- **Bounds**: fixed fields; nonzero generations ≤ `std::uint64_t::max − 1`. **Overflow**: `reject`.
- **Failure**: only `ProviderComposition` can issue a handle; an inauthentic handle is rejected by every
  operation with `invalid_provider_route_handle`.
- **Doxygen**: group `xcom_core`; per-declaration tags (baseline satisfied).
- **Planned evidence**: CHK-03, CHK-11; NEG-17.

### 3.4 `T015-U-PROVIDER` — source-level provider interface

- **Interface**: `CommunicationProvider` (`descriptor`, `descriptor_compatible`, `instance_id` public;
  `prepare`/`activate`/`submit`/`receive`/`drain`/`close`/`state`/`reconcile` private to composition).
- **Behaviour**: exposes an in-process source-level contract with no stable binary ABI, no discovery, and no
  dynamic loading; an implementation owns its route resources and validates the exact binding it receives.
- **Ownership**: implementer-owns-resources; composition owns none of them. **Lifetime**: the implementation
  must outlive the composition and every handle it issued. **Thread-safety**: every virtual operation must
  serialize shared mutation and return owned results.
- **Bounds**: not applicable to the interface. **Overflow**: `n/a`.
- **Failure**: an operation must reject before mutation when exact binding validation fails.
- **Doxygen**: group `xcom_core`; per-declaration tags (baseline satisfied).
- **Planned evidence**: CHK-13; NEG-05.

### 3.5 `T015-U-REG` — fixed-capacity explicit registry

- **Interface**: `ProviderRegistryConfiguration`, `ProviderComposition` construction/`instance_id`/
  `register_provider`.
- **Behaviour**: explicit source-linked registration into fixed `std::array` slots over the configured prefix;
  rejects duplicate, unsupported-version, incompatible, and full cases without replacing a slot; issues a
  strictly advancing generation; performs no discovery or implicit default.
- **Ownership**: platform-owns-shared (the registry owns slots; callers own providers and registrations).
  **Lifetime**: composition-scoped. **Thread-safety**: internally-synchronized (registry mutex held only for
  inspection/mutation; provider callbacks run after release).
- **Bounds**: providers ≤ 8; generation < `std::uint64_t::max`. **Overflow**: `reject`.
- **Failure**: `rejected` with `invalid_descriptor`, `duplicate_provider`, `unsupported_contract_version`, or
  `provider_capacity_exhausted`; `noexcept`; no slot mutated on rejection.
- **Doxygen**: group `xcom_core`; per-declaration tags (baseline satisfied).
- **Planned evidence**: CHK-04, CHK-05, CHK-15, CHK-16; NEG-02.

### 3.6 `T015-U-DISPATCH` — exact-handle route dispatch (extended)

- **Interface**: `ProviderRouteRequirements`, `ProviderComposition::prepare_route`/`activate_route`/`submit`/
  `receive`/`drain_route`/`close_route`/`route_state`/`reconcile_route`.
- **Behaviour**: authenticates the exact lifecycle handles/declarations and the requested semantics, then —
  **new** — invokes the declared-policy matching before any provider dispatch; prepares/activates/submits/
  receives/drains/closes/reconciles only through the exact provider route handle; observes the optional
  `ObservationHub` seam without holding an X-COM lock across a provider call.
- **Ownership**: platform-owns-shared (composition owns no provider resources; providers own them).
  **Lifetime**: registration/production-generation handles; exact lifecycle generations. **Thread-safety**:
  internally-synchronized (registry mutex released before provider calls; hub reservations span dispatch).
- **Bounds**: per-route payload ≤ prepared bound; per-route queue ≤ prepared bound; provider routes ≤ descriptor
  maximum and loopback maximum. **Overflow**: `reject` (`payload_limit_exceeded`, `queue_saturated`,
  `route_capacity_exhausted`).
- **Failure**: `rejected`/`failed` with the stable outcomes of `detailed-design.md` §6; `noexcept`; no mutation
  on rejection; an unexpected provider result is reported as `interrupted_resource`, never as success.
- **Doxygen**: group `xcom_core`; `prepare_route` documents the declared-policy matching contract, and the new
  outcome and matching helper carry the inherited ownership/lifetime/thread-safety/failure clauses.
- **Planned evidence**: CHK-06..CHK-11, CHK-13, CHK-16; NEG-03..NEG-05, NEG-17..NEG-20, NEG-22.

### 3.7 `T015-U-MATCH` — declared-policy ↔ provider capability matching (new)

- **Interface**: internal helpers `declared_delivery_claim(ReliabilityPolicy)`,
  `declared_ordering_claim(OrderingPolicy)` plus the matching block inside `prepare_route`; no new public
  declaration.
- **Behaviour**: for a policy-bound route, derives the exact delivery/ordering claim, requires the requested
  requirements to equal it, rejects an unmappable claim or a non-`reject` overflow or a nonzero deadline/retry,
  and rejects a requested queue capacity that exceeds the declared `queue_depth`; every rejection occurs before
  provider dispatch with no mutation. Unbound routes are untouched.
- **Ownership**: pure computation; owns nothing. **Lifetime**: invocation-scoped (the provider dispatch).
  **Thread-safety**: runs under no registry or provider lock; reads immutable declarations only.
- **Bounds**: at most one declaration per route; exact mapping table of `detailed-design.md` §4. **Overflow**:
  `fail-closed`.
- **Failure**: `rejected` with `unsupported_delivery`, `unsupported_ordering`, `unsupported_policy`
  (`XCOM-PROV-E030`), or `queue_limit_exceeded`; `noexcept`; no dispatch and no mutation.
- **Doxygen**: group `xcom_core`; documented through `prepare_route` and the `detailed-design.md` §4 rules.
- **Planned evidence**: CHK-08, CHK-09, CHK-10; NEG-11..NEG-16.

### 3.8 `T015-U-LOOP` — owned fixed-capacity loopback provider

- **Interface**: `LoopbackProvider` (`descriptor`, `descriptor_compatible`, `instance_id`; private route
  operations), `kMaximumRoutes = 4`, `kMaximumQueueItems = 8`.
- **Behaviour**: owns fixed route storage over the configured provider prefix and one reject-new FIFO per
  route; reuses empty/closed slots without growing storage; validates the exact binding, item metadata, and
  payload bound; preserves FIFO order and every queued item on saturation; drains, closes only when empty, and
  reports state/reconciliation as owned bounded values.
- **Ownership**: provider-owns-resources (routes and queued items).
  **Lifetime**: process-scoped fixture; returned items are independent copies. **Thread-safety**:
  internally-synchronized (one mutex; no callback under the lock); despite `XCOM-DU-008`'s
  `single-thread-owner` baseline note, the baseline implementation serializes every operation and the T015
  concurrency case exercises concurrent submit/receive.
- **Bounds**: routes ≤ 4 (prefix = descriptor `maximum_routes()`); queue ≤ 8 (prefix = configured capacity);
  route generation < `std::uint64_t::max`. **Overflow**: `reject`.
- **Failure**: `rejected` with `route_mismatch`, `route_capacity_exhausted`, `item_mismatch`,
  `payload_limit_exceeded`, `queue_saturated`, `queue_empty`, `inactive_route`, `queued_items_remain`,
  `invalid_provider_route_handle`, or `interrupted_resource`; `noexcept`; unrelated routes and FIFO items
  unchanged on rejection.
- **Doxygen**: group `xcom_core`; per-declaration tags (baseline satisfied).
- **Planned evidence**: CHK-12, CHK-14, CHK-16; NEG-19, NEG-20, NEG-21, NEG-22.

### 3.9 `T015-U-INDEP` — independent source-linked provider fixture

- **Interface**: `test::IndependentProvider` (public descriptor/compatibility/instance and dispatch counters).
- **Behaviour**: a second implementation of the same source contract with one route and one queue slot,
  countable prepare/activate/submit dispatches, and an optional one-shot registration re-entry probe; proves
  replaceability and that a rejected preparation dispatches nothing.
- **Ownership**: fixture-owns-resource. **Lifetime**: test-scoped. **Thread-safety**:
  internally-synchronized (one mutex).
- **Bounds**: one route; one queue slot; token generation < `std::uint64_t::max`. **Overflow**: `reject`.
- **Failure**: stable outcomes only; retained state unchanged on an invalid token or state.
- **Doxygen**: file/class blocks present (test fixture, not a public runtime declaration).
- **Planned evidence**: CHK-05, CHK-13, CHK-16; NEG-05, NEG-11..NEG-16.

## 4. Work-product units

| Unit | Artifact | Owner | Check |
| --- | --- | --- | --- |
| `T015-W01` | `docs/engineering/xcom/t015/requirements.md` | T015 | CHK-25 |
| `T015-W02` | `docs/engineering/xcom/t015/architecture.md` | T015 | CHK-25 |
| `T015-W03` | `docs/engineering/xcom/t015/detailed-design.md` | T015 | CHK-25 |
| `T015-W04` | `docs/engineering/xcom/t015/unit-specifications.md` | T015 | CHK-25 |
| `T015-W05` | `docs/engineering/xcom/t015/verification-plan.md` | T015 | CHK-25 |
| `T015-W06` | `docs/engineering/xcom/t015/implementation.md` | T015 | CHK-22 |
| `T015-W07` | `docs/engineering/xcom/t015/internal-review.json` | T015 | review gate |
| `T015-W08` | `reports/xcom-queue/t015-package.json` | T015 | package gate |

## 5. Planned tests (exact)

All cases run offline in the admitted T011/T012 build envelope. No new CTest target is added; the focused cases
extend the existing T015-owned executables, so the discovered test count stays at the baseline (248) and the
three provider-loopback target names/labels are unchanged.

| CTest target | Test name | Added cases | Covers |
| --- | --- | --- | --- |
| `xcom_provider_loopback_unit` | `xcom_provider_loopback_unit` | `test_policy_bound_route_matching`, `test_policy_bound_route_queue_depth_bound`, `test_policy_bound_route_all_interaction_families`, `test_unbound_route_additivity`, `test_policy_bound_concurrent_submit_receive` | T015-SR-007, -008, -009, -010, -012, -013, -018 |
| `xcom_provider_loopback_negative` | `xcom_provider_loopback_negative` | `test_declared_policy_claim_rejection`, `test_declared_policy_dimension_rejection`, `test_declared_policy_queue_depth_rejection`, `test_declared_policy_rejection_precedes_dispatch`; one added row in `test_exact_provider_diagnostics` | T015-SR-005, -006, -007, -008, -009, -016 |
| `xcom_provider_loopback_external_consumer` | `xcom_provider_loopback_external_consumer` | none (must still compile and run against the public target) | T015-SR-021 |
| existing `xcom_provider_loopback_*` cases | descriptor, registration, compatibility, ownership, lifecycle, FIFO, saturation, recovery, replaceability, diagnostics, concurrency | none | T015-SR-001..-006, -012..-021 |

Case intent:

- `test_policy_bound_route_matching`: a route declared with `{ordering = fifo, reliability = best_effort,
  overflow = reject, deadline_ms = 0, retry = 0, queue_depth = configured capacity}` prepares, activates, and
  accepts/receives one item through the loopback provider; the prepared handle's payload/queue bounds equal the
  declared/requested bounds. Proves the matching admits the exact supported declaration.
- `test_policy_bound_route_queue_depth_bound`: two policy-bound routes whose declared `queue_depth` is at least
  the requested capacity both prepare successfully, and a route whose declared `queue_depth` equals the
  requested capacity is accepted (boundary equality).
- `test_policy_bound_route_all_interaction_families`: a policy-bound route for each of the four interaction
  kinds prepares, activates, and round-trips one item; proves the matching does not restrict the interaction
  family.
- `test_unbound_route_additivity`: a route declared through the unchanged 3-argument `RouteSpec::create`
  (no declared policy) prepares and activates exactly as the baseline fixture does, regardless of the requested
  delivery/ordering; proves the matching adds no requirement or default to an unbound route.
- `test_policy_bound_concurrent_submit_receive`: several producer and consumer threads operate on one
  policy-bound active loopback route; every accepted item is received exactly once with per-route FIFO order
  preserved and no invalid outcome, proving the matching does not alter concurrency.
- `test_declared_policy_claim_rejection`: declared `reliability ∈ {at_most_once, exactly_once}` →
  `unsupported_delivery`; declared `ordering = priority` → `unsupported_ordering`; a request whose
  delivery/ordering differs from the declared claim → `unsupported_delivery`/`unsupported_ordering`; a selected
  provider advertising fewer bits than the mapped claim → `unsupported_delivery`/`unsupported_ordering`. Each
  case asserts `IndependentProvider::prepare_calls() == 0`, `activate_calls() == 0`, `submit_calls() == 0`, and
  an unchanged fresh route/source/destination snapshot.
- `test_declared_policy_dimension_rejection`: declared `overflow ∈ {drop_oldest, drop_newest, coalesce,
  lossless_backpressure, fail_closed}` → `unsupported_policy`; declared `deadline_ms > 0` → `unsupported_policy`;
  declared `retry > 0` → `unsupported_policy`; each with zero provider dispatch and no mutation.
- `test_declared_policy_queue_depth_rejection`: declared `queue_depth` below the requested `queue_capacity` →
  `queue_limit_exceeded`; zero provider dispatch and no mutation.
- `test_declared_policy_rejection_precedes_dispatch`: for every rejection above, the composition leaves the
  provider and lifecycle observations byte-identical to a freshly declared fixture (no partial preparation),
  and the provider dispatch counters remain zero.
- added `test_exact_provider_diagnostics` row: `ProviderOutcome::unsupported_policy` maps to
  `unsupported-policy` / `XCOM-PROV-E030` /
  `declared route policy is not supported by the selected provider`; every existing row is unchanged.

## 6. Requirement-to-unit-to-test traceability

| Requirement | Unit(s) | Planned test case(s) | Check(s) |
| --- | --- | --- | --- |
| T015-SR-001 | `T015-U-DESC` | existing descriptor rejection table | CHK-04, CHK-05, NEG-01 |
| T015-SR-002 | `T015-U-REG` | existing registration rejection/re-entry cases | CHK-04, CHK-05, NEG-02 |
| T015-SR-003 | `T015-U-REG`, `T015-U-DISPATCH` | existing capacity/exhaustion cases + forbidden-API scan | CHK-02, CHK-05, CHK-15, CHK-17 |
| T015-SR-004 | `T015-U-DISPATCH` | existing preparation identity/state matrix | CHK-06, NEG-03, NEG-04, NEG-05 |
| T015-SR-005 | `T015-U-DISPATCH` | existing requested-semantics matrix + `test_declared_policy_rejection_precedes_dispatch` | CHK-07, NEG-06..NEG-10 |
| T015-SR-006 | `T015-U-DISPATCH`, `T015-U-HANDLE` | existing activation/submit/reconcile matrices | CHK-11, NEG-17, NEG-18, NEG-20 |
| T015-SR-007 | `T015-U-MATCH` | `test_policy_bound_route_matching`, `test_declared_policy_claim_rejection` | CHK-08, NEG-11, NEG-12 |
| T015-SR-008 | `T015-U-MATCH` | `test_declared_policy_claim_rejection` | CHK-08, NEG-11, NEG-12, NEG-16 |
| T015-SR-009 | `T015-U-MATCH` | `test_policy_bound_route_queue_depth_bound`, `test_declared_policy_dimension_rejection`, `test_declared_policy_queue_depth_rejection` | CHK-09, NEG-13, NEG-14, NEG-15 |
| T015-SR-010 | `T015-U-MATCH`, `T015-U-DISPATCH` | `test_unbound_route_additivity` | CHK-10 |
| T015-SR-011 | `T015-U-MATCH` | `test_policy_bound_route_matching` + structural no-rebind inspection | CHK-08, CHK-11 |
| T015-SR-012 | `T015-U-LOOP` | existing route-capacity/reuse/isolation cases | CHK-12, NEG-21 |
| T015-SR-013 | `T015-U-LOOP` | `test_policy_bound_route_all_interaction_families`, existing saturation/FIFO/recovery cases | CHK-12, NEG-19, NEG-20 |
| T015-SR-014 | `T015-U-PROVIDER`, `T015-U-INDEP` | existing independent-provider contract case | CHK-13, NEG-05 |
| T015-SR-015 | `T015-U-DISPATCH` | existing reconciliation mismatch case | CHK-11, NEG-20 |
| T015-SR-016 | `T015-U-OUTCOME` | `test_exact_provider_diagnostics` (extended row) | CHK-14, NEG-13 |
| T015-SR-017 | `T015-U-DESC`, `T015-U-REG`, `T015-U-LOOP` | bounds matrix in `detailed-design.md` §7 + exhaustion cases | CHK-15, NEG-02, NEG-10, NEG-15, NEG-21 |
| T015-SR-018 | `T015-U-DISPATCH`, `T015-U-LOOP`, `T015-U-REG` | `test_policy_bound_concurrent_submit_receive`, existing re-entry/concurrency cases | CHK-16, NEG-22 |
| T015-SR-019 | all units | forbidden-API scan + offline build | CHK-17, NEG-23 |
| T015-SR-020 | work products | public-safety scan | CHK-18, NEG-24 |
| T015-SR-021 | `T015-U-OUTCOME`, `T015-U-DISPATCH`, changed declarations | declaration inspection + documentation validator | CHK-19 |
| T015-SR-022 | work products | changed-path inspection + register validators | CHK-02, CHK-20, CHK-21, CHK-25 |
| T015-SR-023 | work products | deterministic gate | CHK-22, CHK-23, NEG-25 |

## 7. Scope-preservation notes

- The consolidated cross-cutting matrix (all interaction kinds, provider capabilities, policy, ownership,
  lifecycle, queue bounds, diagnostics, recovery) remains T016 (`T015-GAP-02`); T015 adds only focused cases for
  its own declared-policy matching and provider/loopback boundaries.
- No existing test case is removed, renamed, or weakened; additions are within the existing executables, and
  the exact-diagnostic table gains one row without changing any existing row.
- The declared-policy matching is additive and changes no public method signature, `ProviderRouteRequirements`
  aggregate, or `RouteSpec` API, so no other slice's source or tests need to change.
- The declared-policy matching is a composition-boundary concern; `loopback_provider.{hpp,cpp}` is re-verified
  unchanged and no later-slice behaviour is implemented.
