# T016 Architecture — Consolidated Core Test Matrix, Structure, and Boundaries

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T016 (capability 007, slice `T-CORE`) |
| Stage / role | plan → architecture |
| Revision | 1 |
| Baseline revision | `44d2001d48dd42dc9ed489a40d2a5f908b734501` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture anchors | `docs/engineering/xcom/t009/architecture-model.{json,md}` (`XCOM-CMP-004…-007`, `XCOM-XB-004`, `XCOM-XB-009`, `XCOM-XLC-004`, `XCOM-INV-01/02/05/11/12`) |
| Design-unit anchors | `docs/engineering/xcom/t010/design-units.md` (`XCOM-DU-007`, `XCOM-DU-008`) |
| Classification | Public-safe engineering work product |

This document describes the structure of the T016 consolidated test matrix. It adds **no** production
component, boundary, contract, or invariant: it consumes the accepted architecture read-only and states
how the consolidated verification is arranged. It is written before implementation.

## 2. Architectural context

T016 is the verification task that closes the T-CORE first-proof core (T013–T015) and realizes the
accepted `XCOM-SW-CORE-009` and `XCOM-SW-CORE-008` verification obligations. The test matrix is an
external, read-only consumer of the accepted in-process C++ contract `XCOM-XLC-004`
(`provider.hpp`), plus the core-type, diagnostic, and lifecycle headers.

```text
                 tests/xcom/core_matrix/**            (T016, new; read-only)
                           │  includes public headers only
                           ▼
   ┌───────────────────────────────────────────────────────────────────────┐
   │ accepted T-CORE first-proof components (read-only, unchanged)         │
   │                                                                       │
   │  XCOM-CMP-004 Core value, contract, and diagnostic types  (T013)      │
   │        │  FlowPolicy, DiagnosticSet, DiagnosticCode/ValidationPhase    │
   │        ▼                                                              │
   │  XCOM-CMP-005 Endpoint and route lifecycle                (T014)      │
   │        │  exact generation-bound EndpointHandle/RouteHandle            │
   │        ▼        (XCOM-XLC-004 / XCOM-XB-004 exact-handle-required)     │
   │  XCOM-CMP-006 Provider boundary and composition           (T015)      │
   │        │  descriptor/capability masks, prepare/activate/submit/...     │
   │        ▼        (XCOM-XB-009 realization)                             │
   │  XCOM-CMP-007 Owned loopback provider                     (T015)      │
   │        │  fixed per-route reject-new FIFO (routes ≤ 4, items ≤ 8)      │
   └───────────────────────────────────────────────────────────────────────┘
                           ▲
                           │  re-run unchanged, never edited
        tests/xcom/{core_types,endpoint_route_lifecycle,provider_loopback,
                    observation,activation_plan,validation_session}/**
```

The only production-tree path T016 touches is the shared, serialized subtree build contract
`src/xverse/xcom/CMakeLists.txt`, and only additively (new test executables and `add_test`/discovery
entries). No component, boundary, contract, or invariant in `docs/engineering/xcom/t009/` is modified.

## 3. Test architecture overview

T016 is a layered, self-contained test package. Nothing under
`tests/xcom/core_matrix/` includes another task's test-support header; the package is independently
buildable and readable.

```text
tests/xcom/core_matrix/
├── test_support.hpp          independent full-stack fixture + local probe provider + helpers
├── unit_tests.cpp            nominal consolidated matrix (areas 1–7)
├── negative_tests.cpp        ≥ 20 named fail-closed rejection cases (SC-001)
├── recovery_tests.cpp        saturation recovery, rejected-op reuse, recreation, reconcile
├── concurrency_tests.cpp     bounded deterministic concurrency (exactly-once, per-route FIFO)
├── fault_boundary_tests.cpp  XCOM-SW-CORE-008 / FR-024 boundary proof
└── consumer/
    └── main.cpp              independent translation unit over the public include surface
```

### 3.1 Test components (`T016-TS-###`, T016-local identifiers)

These identifiers are local to the T016 test package. They are not architecture components of the
product and must not be confused with the accepted `XCOM-CMP-*` product components.

| Id | Component | Kind | Owning file | Purpose |
| --- | --- | --- | --- | --- |
| `T016-TS-001` | Independent full-stack fixture | test fixture | `test_support.hpp` | Builds contract → endpoints → route → lifecycle → composition → loopback for a chosen interaction family and policy; owns every value and handle |
| `T016-TS-002` | Local probe provider | test fixture | `test_support.hpp` | Independently implemented `CommunicationProvider` with bounded one-route/one-item storage, observable prepare/activate/submit call counters, and a forced-failure mode |
| `T016-TS-003` | Nominal unit matrix | test suite | `unit_tests.cpp` | Four-family round trip and areas 1–7 (capabilities, policy, ownership, lifecycle, bounds, diagnostics) |
| `T016-TS-004` | Negative matrix | test suite | `negative_tests.cpp` | NEG-01…NEG-27, one named case each, spanning all four interaction families |
| `T016-TS-005` | Recovery matrix | test suite | `recovery_tests.cpp` | Saturation recovery, rejected-op reuse, recreation, reconciliation |
| `T016-TS-006` | Concurrency matrix | test suite | `concurrency_tests.cpp` | Bounded concurrent submit/receive determinism |
| `T016-TS-007` | Fault-boundary matrix | test suite | `fault_boundary_tests.cpp` | CORE-008 boundary and forbidden-vocabulary scan |
| `T016-TS-008` | External consumer | test executable | `consumer/main.cpp` | Compiles/links the public include surface in a separate translation unit |

## 4. Mapping of the T016 task entry to suites

The eight areas named by the T016 task entry map to the suites as follows; each area has at least one
nominal case and, where rejectable, at least one negative case.

| Task-entry area | Nominal suite | Negative suite |
| --- | --- | --- |
| Interaction kinds | `unit` (four families, `T016-TS-003`) | `negative` NEG-02, NEG-06, NEG-14, NEG-26 |
| Capabilities | `unit` (mask bits, positive `reliable` mapping) | `negative` NEG-07, NEG-08, NEG-09, NEG-16 |
| Policy | `unit` (declared binding, unbound additivity, policy equality) | `negative` NEG-05, NEG-10, NEG-11, NEG-12, NEG-13 |
| Ownership | `unit` (exact handles, copy/read) | `negative` NEG-21, NEG-22, NEG-24, NEG-27 |
| Lifecycle | `unit`/`recovery` (state table, drain/close) | `negative` NEG-18, NEG-20, NEG-23, NEG-25 |
| Queue bounds | `unit` (4/8/8/65536/32/32, FIFO) | `negative` NEG-04, NEG-15, NEG-17, NEG-18, NEG-19 |
| Deterministic diagnostics | `unit` (exact content, byte ordering, locale) | `negative` NEG-01, NEG-03, NEG-05 |
| Recovery | `recovery`/`concurrency` | `negative` NEG-18, NEG-20, NEG-21, NEG-25 |
| Fault-hook boundary (CORE-008) | `fault_boundary` | `fault_boundary` + NEG-28 scan |

## 5. Data flow of the consolidated matrix

One nominal case drives the accepted core end to end. The flow below is executed by
`T016-TS-001`/`T016-TS-003` for each of the four interaction families.

```text
 construct ──► CommunicationContract::create(contract, interface, schema, kind, directions)
        │            └─ success ⇒ owned immutable contract; failure ⇒ deterministic DiagnosticSet
        ├──► EndpointSpec::create(source/destination, digest, provider_id, direction)
        ├──► route  = RouteSpec::create(...[, optional FlowPolicy])
        ├──► lifecycle = LifecycleController::create({endpoints, routes})
        │        ├─ declare_endpoint ×2, declare_route, validate_*, activate_endpoint ×2
        ├──► descriptor = ProviderDescriptor::create(identity, version, link, masks, limits)
        ├──► provider   = LoopbackProvider(descriptor)
        ├──► composition= ProviderComposition(ProviderRegistryConfiguration::create(1))
        │        ├─ register_provider(provider)            ⇒ ProviderOutcome::registered
        │        └─ prepare_route(lifecycle, spec, handles, requirements)
        │                 ⇒ [declared-policy matching] ⇒ ProviderResult<ProviderRouteHandle>
        ├──► activate_route(handle, lifecycle)             ⇒ ProviderOutcome::activated
        ├──► submit(handle, item, lifecycle)               ⇒ ProviderOutcome::accepted
        ├──► receive(handle, lifecycle)                    ⇒ ProviderOutcome::received
        └──► drain_route / close_route                     ⇒ ProviderOutcome::{draining, closed}
```

Negative and recovery cases re-enter the same flow with exactly one injected defect (a mutated
identity, handle, state, capacity, or binding) and assert the stable outcome and the absence of any
mutation. Concurrency cases run bounded producers/consumers against one active route.

## 6. Interfaces consumed (read-only)

| Header | Accepted contract | T016 use |
| --- | --- | --- |
| `value.hpp` | bounded `Identity`, `SemanticVersion`, `Payload`, `Timestamp`, `kMaximumPayloadBytes = 65'536` | build items/payloads within bounds; assert bound rejection |
| `contract.hpp` | `InteractionKind`, `EndpointDirection`, `OrderingPolicy`, `ReliabilityPolicy`, `OverflowPolicy`, `FlowPolicyInput`, `FlowPolicy`, `CommunicationContract` | four families; declared-policy construction; exact contract equality |
| `item.hpp` | `CommunicationItem`, `OriginKind` | metadata round trip; item binding mismatch |
| `diagnostic.hpp` | `DiagnosticCode`, `DiagnosticSeverity`, `ValidationPhase`, `DiagnosticSet` | exact diagnostic content/ordering/locale |
| `result.hpp` | `Result<T>` | value-or-diagnostics returns; exclusive success/failure |
| `core_types.hpp` | aggregate core-type header | single include for core values |
| `endpoint_route_lifecycle.hpp` | `EndpointSpec`, `RouteSpec`, `EndpointHandle`, `RouteHandle`, `LifecycleController`, `LifecycleState`, `LifecycleConfiguration` | lifecycle state table, exact handles, declared policy |
| `provider.hpp` | `ProviderDescriptor`, `DeliveryCapability`, `OrderingCapability`, `ProviderOutcome`, `ProviderRouteRequirements`, `ProviderRouteHandle`, `ProviderRouteState`, `ProviderComposition`, `ProviderRegistryConfiguration`, `CommunicationProvider` | capabilities, policy matching, ownership, bounds, diagnostics |
| `loopback_provider.hpp` | `LoopbackProvider`, `kMaximumRoutes = 4`, `kMaximumQueueItems = 8` | FIFO, saturation, drain/close |
| `observation.hpp` | provider-neutral seam (T021 baseline) | read-only distinction of controlled seams for the CORE-008 boundary proof |

T016 adds no cross-language boundary and consumes `XCOM-XLC-004`/`XCOM-XB-004`/`XCOM-XB-009` exactly as
the accepted architecture declares.

## 7. Build and execution topology

- Each suite is one executable linked against `xverse::xcom_provider_loopback` (which transitively links
  the lifecycle and core-types libraries) plus the already admitted `GTest::gtest_main`/`GTest::gmock`
  and `Threads::Threads`.
- The consolidated suites use `gtest_discover_tests` so every case (in particular every one of the
  ≥ 20 negative cases required by `SC-001`) is an individually named, individually reportable CTest
  test. Stylistic divergence from the hand-rolled `main()` suites of T013–T015 is recorded
  (`T016-OPEN-01`); it is additive and changes no existing target.
- Labels are single hyphenated tokens (`t016-unit`, `t016-negative`, `t016-recovery`,
  `t016-concurrency`, `t016-fault-boundary`) so `ctest -L t016*` selects the matrix, matching the
  CMake-3.22 label workaround already used by T020.
- The `consumer` executable is registered with one `add_test` under label `t016`.
- `tests/xcom/core_matrix/` is added to each GTest target's include path so `test_support.hpp` resolves
  without reaching into another test directory.
- No runtime library target is added, so `XVERSE_XCOM_EXPECTED_TARGETS` and the T012 build-contract
  verifier (`xcom_build_contract`) are unchanged.

## 8. Boundaries, invariants, and governance preserved

| Accepted element | T016 disposition |
| --- | --- |
| `XCOM-INV-01` logical identity independent of address/handle | asserted: descriptors/handles carry logical identity; no address appears (CHK-06, CHK-09) |
| `XCOM-INV-02` no mutation without the exact handle | asserted across ownership/negative cases (CHK-09, NEG-21, NEG-22) |
| `XCOM-INV-05` finite queues with declared overflow | asserted bound/exhaustion matrix (CHK-12, CHK-18, NEG-15, NEG-17) |
| `XCOM-INV-11` one-way dependency flow | unchanged: tests depend on production, never the reverse |
| `XCOM-INV-12` no domain-specific primitive | asserted by the CORE-008 forbidden-vocabulary scan (CHK-17, NEG-28) |
| `XCOM-XLC-004`, `XCOM-XB-004`, `XCOM-XB-009` | consumed read-only; not modified |
| `XCOM-CMP-004…-007`, `XCOM-DU-007`, `XCOM-DU-008` | verified read-only; no redesign |
| T007 shared-path rule | `src/xverse/xcom/CMakeLists.txt` edited additively and serialized after T015 |
| ADR-0018 platform-first, ADR-0020 work products | only local T016 test/work-product paths change; no legacy or later-task implementation |

## 9. Architectural decisions recorded for T016

- **D-01 — New package rather than extending an existing suite.** Extending an existing suite would
  couple the consolidated matrix to another task's exclusive test paths and risk weakening its cases.
  A new independent package keeps every existing case byte-identical and makes the consolidated proof
  auditable in one place.
- **D-02 — Independent fixture.** `test_support.hpp` deliberately does not include
  `tests/xcom/provider_loopback/test_support.hpp` or `independent_provider.hpp`, so a change to another
  task's fixture cannot silently change T016 evidence.
- **D-03 — GTest discovery for per-case evidence.** Chosen so each negative case has a stable external
  name for `SC-001` (see `T016-OPEN-01`).
- **D-04 — Additive registration only.** The shared build contract is edited additively; no existing
  target, test, label, command, or expected result is renamed, reordered, or removed.

## 10. Traceability

| T016 requirement | Architecture element |
| --- | --- |
| T016-SR-001 | §3, §7, D-01, D-02, D-04 |
| T016-SR-002 | §4, §5, §6 (`contract`/`item`/`lifecycle`/`provider`) |
| T016-SR-003 | §6 (`provider`), §4 (Capabilities) |
| T016-SR-004 | §6 (`contract`/`lifecycle`), §4 (Policy) |
| T016-SR-005 | §6 (`lifecycle`/`provider`), §4 (Ownership) |
| T016-SR-006 | §5, §6 (`lifecycle`/`loopback_provider`), §4 (Lifecycle) |
| T016-SR-007 | §6 (`loopback_provider`/`provider`), §8 (`XCOM-INV-05`) |
| T016-SR-008 | §6 (`diagnostic`), §4 (Diagnostics) |
| T016-SR-009 | §4, §5 (recovery flow) |
| T016-SR-010 | §3 (`T016-TS-006`), §7 |
| T016-SR-011 | §3 (`T016-TS-004`), §4 (`SC-001`) |
| T016-SR-012 | §6 (`observation` seam), §8 (`XCOM-INV-12`) |
| T016-SR-013 | §7, §3 (`T016-TS-005/006`) |
| T016-SR-014 | §2, §7, D-04 |
| T016-SR-015 | §6, §7 |
| T016-SR-016 | §7 |
| T016-SR-017 | §3 (file inventory) |
| T016-SR-018 | §8 |
| T016-SR-019 | §7 |
| T016-SR-020 | §10 |
