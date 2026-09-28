# T014 Unit Specifications — Bounded Lifecycle, Ownership Handles, and Declared-Policy Binding Units

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T014 (capability 007, slice `T-CORE`) |
| Stage / role | plan → unit specifications (pre-code) |
| Revision | 1 |
| Baseline revision | `93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Accepted unit design | `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-006`, component `XCOM-CMP-005`) |
| Classification | Public-safe engineering work product |

These unit specifications elaborate, without weakening, the accepted T010 unit design for `XCOM-DU-006`
"Endpoint and route lifecycle with generation handles". All T014 units map to `XCOM-DU-006` and component
`XCOM-CMP-005`; `XCOM-DU-006` is recorded as T014 source per `tasks.md`/`XCOM-CMP-005`. T014 does not
rewrite the T009/T010 registers; the §7.4 attribution observation in `requirements.md` is recorded only.

## 2. Unit inventory

| Unit (T014) | Accepted unit | Component | Kind | Language | Path(s) | Change |
| --- | --- | --- | --- | --- | --- | --- |
| `T014-U-DECL` | `XCOM-DU-006` | `T14-CMP-DECL` | data-plane | cpp | `endpoint_route_lifecycle.hpp`, `endpoint_route_lifecycle.cpp` | re-verified unchanged |
| `T014-U-CONFIG` | `XCOM-DU-006` | `T14-CMP-CONFIG` | data-plane | cpp | `endpoint_route_lifecycle.hpp`, `endpoint_route_lifecycle.cpp` | re-verified unchanged |
| `T014-U-HANDLE` | `XCOM-DU-006` | `T14-CMP-HANDLE` | data-plane | cpp | `endpoint_route_lifecycle.hpp`, `endpoint_route_lifecycle.cpp` | re-verified unchanged |
| `T014-U-SNAP` | `XCOM-DU-006` | `T14-CMP-SNAP` | data-plane | cpp | `endpoint_route_lifecycle.hpp`, `endpoint_route_lifecycle.cpp` | extended (`policy_bound`) |
| `T014-U-CTRL` | `XCOM-DU-006` | `T14-CMP-CTRL` | data-plane | cpp | `endpoint_route_lifecycle.hpp`, `endpoint_route_lifecycle.cpp` | extended (`route_policy`); declaration/transition unchanged |
| `T014-U-POLICY` | `XCOM-DU-006` | `T14-CMP-POLICY` | data-plane | cpp | `endpoint_route_lifecycle.hpp`, `endpoint_route_lifecycle.cpp` | **new** |

## 3. Unit specifications

### 3.1 `T014-U-DECL` — immutable endpoint and route declarations

- **Interface**: `ResourceKind`, `LifecycleState`, `to_string`, `EndpointSpecInput`, `EndpointSpec`,
  `RouteSpecInput`, `RouteSpec`, their factories and accessors.
- **Behaviour**: validates and copies bounded endpoint/route identity, exact plan digest, provider
  identity, direction, contract, and endpoint compatibility; owns the declaration independently of
  realization.
- **Ownership**: caller-owns-value (inputs and returned declarations). **Lifetime**: invocation-scoped.
  **Thread-safety**: immutable-value.
- **Bounds**: identity ≤ 128 bytes; digest exactly 64 bytes; fixed descriptor capacities.
  **Overflow**: `fail-closed`.
- **Failure**: `rejected` with `required_field`, `bound_exceeded`, `invalid_digest`,
  `incompatible_direction`, or `route_incompatible`; `noexcept`; no partial declaration.
- **Doxygen**: group `xcom_core`; per-declaration tags (baseline satisfied; the new `RouteSpec` policy
  overload/accessors add ownership/lifetime/thread-safety/failure clauses).
- **Planned evidence**: CHK-04, CHK-05, CHK-09; NEG-01, NEG-02, NEG-03, NEG-04.

### 3.2 `T014-U-CONFIG` — finite lifecycle configuration

- **Interface**: `LifecycleConfigurationInput`, `LifecycleConfiguration::create`, capacity accessors.
- **Behaviour**: admits finite nonzero endpoint/route capacities ≤ 32/32; rejects zero or over-maximum.
- **Ownership**: caller-owns-value. **Lifetime**: controller lifetime (copied into the controller).
  **Thread-safety**: immutable-value.
- **Bounds**: endpoint capacity 1–32; route capacity 1–32. **Overflow**: `reject`.
- **Failure**: `rejected` with `bound_exceeded`; `noexcept`.
- **Doxygen**: group `xcom_core`; per-declaration tags (baseline satisfied).
- **Planned evidence**: CHK-06, CHK-09; NEG-04.

### 3.3 `T014-U-HANDLE` — exact generation-bound ownership handles

- **Interface**: `EndpointHandle`, `RouteHandle` (controller id, kind, identity, plan digest, generation
  accessors; private construction).
- **Behaviour**: owns the exact binding issued by one declaration; copies preserve it; assignment deleted.
- **Ownership**: provider-issued-handle (`XCOM-DU-006`). **Lifetime**: endpoint-generation.
  **Thread-safety**: immutable-value.
- **Bounds**: fixed fields; nonzero generation ≤ `std::uint64_t::max − 1`. **Overflow**: `reject`.
- **Failure**: only `LifecycleController` can issue a handle; an inauthentic handle is rejected by every
  operation with `invalid_handle`.
- **Doxygen**: group `xcom_core`; per-declaration tags (baseline satisfied).
- **Planned evidence**: CHK-04, CHK-05, CHK-07; NEG-07..NEG-10, NEG-13.

### 3.4 `T014-U-SNAP` — immutable lifecycle observation (extended)

- **Interface**: `LifecycleSnapshot` accessors plus the new `policy_bound()`.
- **Behaviour**: owns a point-in-time kind, identity, plan digest, generation, state, and declared-policy
  flag; unchanged by later controller transitions.
- **Ownership**: caller-owns-value. **Lifetime**: invocation-scoped. **Thread-safety**: immutable-value.
- **Bounds**: fixed fields. **Overflow**: `n/a`.
- **Failure**: created only after exact handle authentication.
- **Doxygen**: group `xcom_core`; the new `policy_bound()` carries `@return`/`@brief` (additive).
- **Planned evidence**: CHK-10, CHK-13, CHK-15; NEG-14.

### 3.5 `T014-U-CTRL` — serialized fixed-capacity lifecycle controller (extended)

- **Interface**: `LifecycleController` declaration, snapshot, declaration-copy, transition, and the new
  `route_policy` operations.
- **Behaviour**: fixed `std::array` records over the configured prefix; reuse empty/closed slots; one
  strictly advancing generation; idempotent-or-rejected transitions; exact handle authentication for every
  operation including `route_policy`.
- **Ownership**: platform-owns-shared (controller owns records; callers own handles and snapshots).
  **Lifetime**: controller-scoped records; endpoint-generation handles. **Thread-safety**:
  internally-synchronized (one mutex; no callback under the lock).
- **Bounds**: endpoints ≤ 32; routes ≤ 32; generation < `std::uint64_t::max`. **Overflow**: `reject`.
- **Failure**: `rejected` with `duplicate_identity`, `capacity_exhausted`, `generation_exhausted`,
  `invalid_handle`, `invalid_transition`, `endpoint_in_use`, `route_incompatible`, or `required_field`
  (absent declared policy); `noexcept`; no mutation on rejection.
- **Doxygen**: group `xcom_core`; `route_policy` and the new overload carry ownership/lifetime/
  thread-safety/failure clauses.
- **Planned evidence**: CHK-06..CHK-17; NEG-05..NEG-18.

### 3.6 `T014-U-POLICY` — declared bounded delivery-policy binding (new)

- **Interface**: the additive `RouteSpec::create(input, source, destination, const FlowPolicy&)` overload,
  `RouteSpec::has_policy()`, `RouteSpec::policy()`, `LifecycleSnapshot::policy_bound()`, and
  `LifecycleController::route_policy(const RouteHandle&)`.
- **Behaviour**: copies exactly one already-validated `FlowPolicy` into the owned route value at
  declaration; the policy survives every transition and generation; `route_policy` authenticates the exact
  current route handle and returns the declared policy, or a stable diagnostic when the generation declared
  none; no default is substituted and no rebind/upgrade operation exists.
- **Ownership**: caller-owns-value (the factory copies the policy); the controller owns the record copy.
  **Lifetime**: route-generation (the bound policy is reachable only through the generation that declared
  it). **Thread-safety**: immutable-value read under the controller mutex.
- **Bounds**: at most one `FlowPolicy` per route record; the `FlowPolicy` ranges remain T013's
  (deadline 0–600,000, retry 0–64, queue depth 1–65,536) and are not reinterpreted as lifecycle capacity.
  **Overflow**: `fail-closed`.
- **Failure**: `invalid_handle` for a stale/foreign/wrong-kind/mismatched handle; `required_field` in the
  `route_declaration` phase for a generation with no declared policy; `noexcept`; no mutation.
- **Doxygen**: group `xcom_core`; every new declaration carries `@ownership`/`@lifetime`/`@thread_safety`/
  `@failure`.
- **Planned evidence**: CHK-10..CHK-13; NEG-11, NEG-14, NEG-15, NEG-16.

## 4. Work-product units

| Unit | Artifact | Owner | Check |
| --- | --- | --- | --- |
| `T014-W01` | `docs/engineering/xcom/t014/requirements.md` | T014 | CHK-21 |
| `T014-W02` | `docs/engineering/xcom/t014/architecture.md` | T014 | CHK-21 |
| `T014-W03` | `docs/engineering/xcom/t014/detailed-design.md` | T014 | CHK-21 |
| `T014-W04` | `docs/engineering/xcom/t014/unit-specifications.md` | T014 | CHK-21 |
| `T014-W05` | `docs/engineering/xcom/t014/verification-plan.md` | T014 | CHK-21 |
| `T014-W06` | `docs/engineering/xcom/t014/implementation.md` | T014 | CHK-23 |
| `T014-W07` | `docs/engineering/xcom/t014/internal-review.json` | T014 | review gate |
| `T014-W08` | `reports/xcom-queue/t014-package.json` | T014 | package gate |

## 5. Planned tests (exact)

All cases run offline in the admitted T011/T012 build envelope. No new CTest target is added; the focused
cases extend the existing T014-owned executables, so the discovered test count is unchanged (248).

| CTest target | Test name | Added cases | Covers |
| --- | --- | --- | --- |
| `xcom_lifecycle_unit` | `xcom_lifecycle_unit` | `test_route_declared_policy_binding`, `test_route_policy_generation_binding`, `test_route_policy_immutability`, `test_route_policy_concurrent_read` | T014-SR-007, -008, -009, -017 |
| `xcom_lifecycle_negative` | `xcom_lifecycle_negative` | `test_route_policy_handle_boundaries`, `test_route_policy_absent_diagnostic`, `test_policy_bound_route_compatibility_unchanged` | T014-SR-006, -008, -009, -010, -012 |
| `xcom_lifecycle_external_consumer` | `xcom_lifecycle_external_consumer` | none (must still compile and run against the public target) | T014-SR-020 |
| existing `xcom_lifecycle_*` cases | declaration, capacity, transition, compatibility, ownership, retention, concurrency, diagnostics | none | T014-SR-001..-006, -011..-016, -018 |

Case intent:

- `test_route_declared_policy_binding`: a route declared through the 4-argument factory reports
  `has_policy()` true, exposes the exact declared ordering/reliability/overflow/deadline/retry/queue-depth,
  yields a snapshot with `policy_bound()` true, and `route_policy(handle)` returns the equal policy; a
  route declared through the 3-argument factory reports `has_policy()` false, `policy()` `nullptr`,
  `policy_bound()` false, and `route_policy` failure.
- `test_route_policy_generation_binding`: after close and recreation with a different declared policy, the
  new generation's `route_policy` returns the new declaration and the earlier handle's `route_policy` fails
  with `invalid_handle`; the generation strictly advances.
- `test_route_policy_immutability`: two routes that differ only in their declared policy are not equal; a
  copied `RouteSpec` keeps its policy; `policy()` returns `nullptr` rather than a default for an unbound
  route.
- `test_route_policy_concurrent_read`: concurrent `route_policy` and `route_snapshot` reads from several
  threads return one identical declared policy with no data race.
- `test_route_policy_handle_boundaries`: a stale route handle, a foreign-controller route handle, and a
  handle whose generation was superseded each fail `route_policy` with the exact `invalid_handle`
  diagnostic bytes and mutate no record.
- `test_route_policy_absent_diagnostic`: `route_policy` on an unbound route returns exactly the serialized
  `route_declaration|error|XCOM-TYPE-E001|<route_id>|route generation declares no bounded flow policy|declare the route with an exact validated flow policy` bytes and no value.
- `test_policy_bound_route_compatibility_unchanged`: a policy-bound route rejects an incompatible endpoint
  with the exact `XCOM-LIFE-E012` diagnostic and no mutation, and its activation still requires both
  endpoints active; declaring a policy grants no compatibility bypass and no upgrade path.

## 6. Requirement-to-unit-to-test traceability

| Requirement | Unit(s) | Planned test case(s) | Check(s) |
| --- | --- | --- | --- |
| T014-SR-001 | `T014-U-DECL` | existing declaration rejection table | CHK-04, CHK-05, CHK-09 |
| T014-SR-002 | `T014-U-DECL` | existing route compatibility matrix | CHK-05, CHK-12 |
| T014-SR-003 | `T014-U-CONFIG` | existing configuration boundary cases | CHK-06, CHK-09 |
| T014-SR-004 | `T014-U-CTRL` | existing capacity/isolation cases | CHK-06, CHK-09 |
| T014-SR-005 | `T014-U-HANDLE` | existing handle binding assertions | CHK-04, CHK-05, CHK-07 |
| T014-SR-006 | `T014-U-HANDLE`, `T014-U-CTRL` | existing handle boundaries + `test_route_policy_handle_boundaries` | CHK-07, NEG-07..NEG-10, NEG-13 |
| T014-SR-007 | `T014-U-POLICY` | `test_route_declared_policy_binding` | CHK-10, CHK-13 |
| T014-SR-008 | `T014-U-POLICY` | `test_route_declared_policy_binding`, `test_route_policy_absent_diagnostic` | CHK-10, CHK-13, NEG-14 |
| T014-SR-009 | `T014-U-POLICY` | `test_route_policy_generation_binding`, `test_route_policy_immutability` | CHK-11, NEG-15 |
| T014-SR-010 | `T014-U-POLICY` | `test_policy_bound_route_compatibility_unchanged` | CHK-12, NEG-16 |
| T014-SR-011 | `T014-U-CTRL` | existing transition tables | CHK-08, CHK-14 |
| T014-SR-012 | `T014-U-CTRL` | existing compatibility/state boundaries + `test_policy_bound_route_compatibility_unchanged` | CHK-12, CHK-14 |
| T014-SR-013 | `T014-U-CTRL` | existing retained-endpoint closure boundary | CHK-14, NEG-12 |
| T014-SR-014 | `T014-U-CTRL` | existing failure/recreation and stale cases | CHK-08, CHK-14 |
| T014-SR-015 | `T014-U-CTRL`, `T014-U-SNAP` | existing exact-diagnostic suite | CHK-07, CHK-15 |
| T014-SR-016 | `T014-U-CONFIG`, `T014-U-POLICY` | bounds matrix above | CHK-06, CHK-09 |
| T014-SR-017 | `T014-U-CTRL` | existing serialized safe-repeat + `test_route_policy_concurrent_read` | CHK-17, NEG-17 |
| T014-SR-018 | all units | forbidden-API scan + offline build | CHK-18, NEG-19, NEG-24 |
| T014-SR-019 | work products | public-safety scan | CHK-19, NEG-21 |
| T014-SR-020 | `T014-U-POLICY`, all changed units | declaration inspection + documentation validator | CHK-20 |
| T014-SR-021 | work products | changed-path inspection + register validators | CHK-02, CHK-21, CHK-22, CHK-25 |
| T014-SR-022 | work products | deterministic gate | CHK-23, NEG-22 |

## 7. Scope-preservation notes

- The consolidated cross-cutting matrix (interaction kinds, provider capabilities, policy, ownership,
  lifecycle, queue bounds, diagnostics, recovery) remains T016 (`T014-GAP-03`); T014 adds only focused
  cases for its own binding and handle boundaries.
- No existing test case is removed, renamed, or weakened; additions are within the existing executables.
- `scripts/validate_xcom_endpoint_route_lifecycle.py` is legacy SESN tooling in the T014-owned path set and
  is neither executed nor edited by the repository-owned workflow (`T014-LIM-04`).
- The declared-policy binding is additive and does not change `EndpointSpecInput`, `RouteSpecInput`,
  `LifecycleConfigurationInput`, or the existing 3-argument factories, so no other slice's source or tests
  need to change.
