# T016 Detailed Design — Consolidation Rules, Fixtures, Case Matrix, and Failure Semantics

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T016 (capability 007, slice `T-CORE`) |
| Stage / role | plan → detailed design |
| Revision | 1 |
| Baseline revision | `44d2001d48dd42dc9ed489a40d2a5f908b734501` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

This is the pre-code detailed design of the T016 consolidated core test matrix. It fixes the fixture
shape, the case inventory, the exact rejection expectations, the bounds, and the build wiring so the
implementation stage is mechanical and auditable. It is written before implementation and adds no
production behaviour.

## 2. Design principles

- **D-01** New package `tests/xcom/core_matrix/`; every existing suite byte-identical.
- **D-02** Self-contained fixture; no other task's test-support include.
- **D-03** GTest with discovered per-case names for `SC-001` evidence.
- **D-04** Additive build-contract registration under distinct `t016-*` labels.
- **D-05** Every case asserts an exact stable outcome and the absence of mutation on rejection.
- **D-06** Every case is deterministic: no wall-clock dependency, bounded threads/items/iterations.

## 3. Fixture design (`test_support.hpp`, namespace `xverse::xcom::test`)

### 3.1 Helpers

| Helper | Signature (design) | Contract |
| --- | --- | --- |
| `core_digest()` | `std::string_view` | one fixed 64-hex-character plan digest constant, synthetic and non-sensitive |
| `source_direction(kind)` / `destination_direction(kind)` | `EndpointDirection` | compatible direction per interaction family (as the accepted direction table) |
| `make_contract(suffix, kind)` | `std::optional<CommunicationContract>` | builds a valid contract for the family |
| `loopback_descriptor(provider_id, delivery, ordering, routes, queue)` | `ProviderDescriptor` | valid descriptor with caller-selected claim bits and finite limits |
| `make_item(fixture, sequence)` | `Result<CommunicationItem>` | valid route-bound item with one bounded payload byte |

### 3.2 `CoreStackFixture` (`T016-TS-001`)

Owns, by value: one `CommunicationContract`; `EndpointSpec` source/destination; one `RouteSpec`
(policy-bound or unbound); one `LifecycleController` (endpoint capacity 2, route capacity 2); the
declared endpoint/route handles; one `LoopbackProvider`; one `ProviderComposition`; the prepared
`ProviderRouteHandle`; and the requested `ProviderRouteRequirements`.

Construction follows the accepted lifecycle exactly: declare → validate endpoints → validate route →
activate endpoints → register provider → `prepare_route` → optional `activate_route`. `ready()` is
false and no usable state is exposed if any step fails.

Accessors mirror the accepted vocabulary: `contract()`, `route_spec()`, `source_spec()`,
`destination_spec()`, `source_handle()`, `destination_handle()`, `route_handle()`, `provider_handle()`,
`lifecycle()`, `composition()`, `provider()`, `requirements()`, `item(sequence)`, and
`item_with_binding(...)`.

Ownership/lifetime: the fixture owns every retained value and handle; returned items are independent
owned copies valid after later provider operations. Thread-safety: construction is single-threaded;
the immutable values support concurrent const reads; mutation goes through the provider/composition
mutexes only. Failure: a failed construction leaves `ready()` false and exposes nothing usable.

### 3.3 `ProbeProvider` (`T016-TS-002`)

An independently implemented `CommunicationProvider` (modeled on, but not including, the accepted
`independent_provider.hpp`) with:

- a retained immutable `ProviderDescriptor` and a caller-selected nonzero `instance_id()`;
- `descriptor_compatible()` requiring the descriptor to fit its one-route/one-item storage;
- observable counters `prepare_calls()`, `activate_calls()`, `submit_calls()` guarded by one mutex;
- a `configure_forced_failure(ProviderOutcome)` mode that makes `prepare`/`submit` return the selected
  stable outcome while still incrementing the counter, used only to prove fail-closed/no-mutation
  behaviour and provider isolation.

Purpose: assert `prepare_calls() == 0` where the accepted design requires a rejection **before** any
provider dispatch, and prove a failing provider changes no unrelated registered provider or route
(`XCOM-SW-CORE-007`).

## 4. Suite and case inventory

### 4.1 `unit_tests.cpp` (`T016-TS-003`) — nominal consolidated matrix

| Case | Area | Assertion |
| --- | --- | --- |
| `InteractionKind_SignalStateUpdate_RoundTripsExactly` | kinds | full-stack round trip; contract/kind/bindings/payload preserved |
| `InteractionKind_MessageEvent_RoundTripsExactly` | kinds | as above |
| `InteractionKind_ServiceRequest_RoundTripsExactly` | kinds | request/respond directions preserved |
| `InteractionKind_ServiceResponse_RoundTripsExactly` | kinds | respond/request directions preserved |
| `CapabilityMask_StableBitsAndDescriptorValidation` | capabilities | `interaction_capability_bit` = 1/2/4/8; `delivery_capability_bit`/`ordering_capability_bit` stable; descriptor rejects zero/unknown masks |
| `CapabilityContainment_RequestMustBeAdvertised` | capabilities | requested family/delivery/ordering contained in advertised masks prepares; helper for claim selection |
| `DeclaredPolicy_AtLeastOnceMapsToReliable_Positive` | capabilities/policy | declared `at_least_once` + provider advertising `reliable` prepares and activates (T015 review strengthening) |
| `DeclaredPolicy_SupportedClaimPreparesAndActivates` | policy | declared `best_effort`/`fifo`/`reject`/`0`/`0` matching request prepares and activates |
| `DeclaredPolicy_UnboundRouteIsUnaffected` | policy | three-argument `RouteSpec` route prepares exactly as baseline (additivity) |
| `DeclaredPolicy_SameIdentityDifferentPolicyCompareUnequal` | policy | two routes with the same identity/digest/provider/endpoints differing only in `FlowPolicy` compare unequal (T014 review strengthening) |
| `Ownership_ExactHandlesAreCopyableAndReadable` | ownership | copied handles/snapshots/values compare equal and remain readable after source destruction/rvalue construction |
| `Lifecycle_EndpointAndRouteStateTable` | lifecycle | accepted declare→validate→activate→drain→close transitions and idempotence; wrong-order transitions rejected |
| `Lifecycle_ProviderRoutePreparedActiveDrainingClosed` | lifecycle | provider route state sequence and drain/close semantics |
| `QueueBounds_FixedLimitsAreExact` | bounds | `kMaximumRoutes == 4`, `kMaximumQueueItems == 8`, `kMaximumProviders == 8`, descriptor payload ≤ 65,536 / routes ≤ 32 / queue ≤ 32 |
| `QueueBounds_SaturationPreservesFifoAndItems` | bounds | reject-new saturation preserves every queued item and FIFO index |
| `Diagnostics_ExactProviderOutcomeMapping` | diagnostics | every `ProviderOutcome` maps to its exact text/code/message, including `unsupported_policy` = `XCOM-PROV-E030` |
| `Diagnostics_ByteStableOrderingAcrossConstructionOrder` | diagnostics | equivalent inputs constructed in different orders serialize byte-identically |
| `Diagnostics_LocaleIndependent` | diagnostics | diagnostic text/code/serialization unchanged under a different process locale |

### 4.2 `negative_tests.cpp` (`T016-TS-004`) — `SC-001` matrix

Each row is one GTest case named `Neg<nn>_<Class>_<Expected>`. NEG-01…NEG-05 malformed, NEG-06…NEG-14
incompatible, NEG-15…NEG-20 over-capacity, NEG-21…NEG-25 unauthorized/ownership. NEG-26 and NEG-27 are
the family-coverage cases added to close `T016-IR-01`: NEG-26 is an incompatible-capability rejection on
a `signal_state_update` route and NEG-27 an unauthorized/item-binding rejection on a `service_response`
route, so the executable matrix spans all four interaction families.

| Id | Injected defect | Expected stable outcome |
| --- | --- | --- |
| NEG-01 | empty / over-bound / non-canonical contract identity, interface, or schema field | core `DiagnosticSet` with `required_field` or `bound_exceeded`; no contract value |
| NEG-02 | incompatible interaction/direction tuple (e.g. `service_request` with `produce`/`consume`) | `incompatible_direction` (contract phase); no contract value |
| NEG-03 | item missing route, provider, or clock domain, or over-long correlation | core `DiagnosticSet` `required_field`/`bound_exceeded` (item phase); no item |
| NEG-04 | payload over the per-route prepared bound | `payload_limit_exceeded` (`XCOM-PROV-E018`); queue unchanged |
| NEG-05 | invalid `FlowPolicy` field (out-of-vocabulary or `queue_depth == 0`) | `invalid_policy` (policy phase), sorted deterministic set; no policy value |
| NEG-06 | requested family not advertised by the descriptor | `unsupported_interaction` (`XCOM-PROV-E015`); `prepare_calls() == 0` |
| NEG-07 | requested delivery not advertised | `unsupported_delivery` (`XCOM-PROV-E016`); no dispatch |
| NEG-08 | requested ordering not advertised | `unsupported_ordering` (`XCOM-PROV-E017`); no dispatch |
| NEG-09 | requested provider contract version ≠ admitted version | `unsupported_contract_version` (`XCOM-PROV-E014`); no dispatch |
| NEG-10 | declared claim unmappable (`at_most_once`, `exactly_once`, `priority`) | `unsupported_delivery`/`unsupported_ordering`; `prepare_calls() == 0` |
| NEG-11 | declared non-`reject` overflow, or nonzero `deadline_ms`/`retry` | `unsupported_policy` (`XCOM-PROV-E030`); no dispatch; no mutation |
| NEG-12 | requested queue capacity > declared `queue_depth` | `queue_limit_exceeded` (`XCOM-PROV-E019`); no dispatch |
| NEG-13 | route declaring an unregistered `provider_id` | `provider_mismatch` (`XCOM-PROV-E025`); no dispatch |
| NEG-14 | provider advertises fewer delivery/ordering bits than the declared claim requires | `unsupported_delivery`/`unsupported_ordering`; no dispatch |
| NEG-15 | duplicate provider identity/instance registered twice | `duplicate_provider` (`XCOM-PROV-E012`); no slot replaced |
| NEG-16 | registry full: capacity-1 registry receives a second provider | `provider_capacity_exhausted` (`XCOM-PROV-E013`); first slot unchanged |
| NEG-17 | loopback route storage exhausted: prepare 5th route | `route_capacity_exhausted` (`XCOM-PROV-E020`); existing routes unchanged |
| NEG-18 | submit beyond configured queue capacity | `queue_saturated` (`XCOM-PROV-E010`); every queued item and FIFO index preserved |
| NEG-19 | submit payload over the prepared provider bound | `payload_limit_exceeded` (`XCOM-PROV-E018`); queue unchanged |
| NEG-20 | close a draining route that still retains items | `queued_items_remain` (`XCOM-PROV-E027`); resource retained |
| NEG-21 | stale generation handle after route recreation | `invalid_handle`/`invalid_provider_route_handle` (`XCOM-PROV-E021`); no mutation |
| NEG-22 | handle issued by a foreign composition/provider instance | `invalid_provider_route_handle` (`XCOM-PROV-E021`) or `provider_mismatch` (`XCOM-PROV-E025`); no mutation |
| NEG-23 | submit/receive on a route not `active` (prepared/draining/closed) | `inactive_route` (`XCOM-PROV-E023`); no delivery |
| NEG-24 | item bound to a different route/provider/endpoint than the prepared route | `item_mismatch` (`XCOM-PROV-E026`); queue unchanged |
| NEG-25 | reconcile after provider/lifecycle divergence | `interrupted_resource` (`XCOM-PROV-E028`); never reported as success |
| NEG-26 | `signal_state_update` route requesting a family the descriptor does not advertise | `unsupported_interaction` (`XCOM-PROV-E015`); `prepare_calls() == 0`; not prepared; not activated |
| NEG-27 | `service_response` route submitted an item bound to a different route | `item_mismatch` (`XCOM-PROV-E026`); `queued_items() == 0`; route still `active` |

Every rejection case additionally asserts: no registry slot, registered provider, prepared route,
queue element, or lifecycle record is mutated, and no normal-route item is emitted.

### 4.3 `recovery_tests.cpp` (`T016-TS-005`)

| Case | Scenario | Assertion |
| --- | --- | --- |
| `Saturation_ThenDrainRecoversFifo` | fill to `queue_saturated`, then receive all, then submit again | every accepted item received once in FIFO order; new submissions accepted |
| `RejectedOperationLeavesStateReusable` | reject a submit (payload/binding) then submit a valid item | route unchanged and accepts the valid item |
| `ClosedRouteRecreatedAsNewGenerationRejectsStaleHandles` | close empty route, recreate, use old handle | old handle rejected with a stable outcome; new route works |
| `Reconcile_MismatchReportsInterruptedResource` | diverge provider/lifecycle state | `interrupted_resource`; never success |
| `ReceiveAfterEmptyReportsQueueEmpty` | receive on an empty active route | `queue_empty` (`XCOM-PROV-I009`) |

### 4.4 `concurrency_tests.cpp` (`T016-TS-006`)

| Case | Bounds | Assertion |
| --- | --- | --- |
| `ConcurrentSubmitReceive_ExactlyOncePerRouteFifo` | ≤ 4 threads, ≤ 8 items total (queue bound) | each accepted item received exactly once, per-route FIFO preserved |
| `ConcurrentRepeatedRuns_DeterministicOutcome` | ≤ 4 threads, ≤ 32 iterations | identical observable outcome each run; no lost/duplicated item |
| `NoCallbackUnderLock_ReentryCompletes` | 2 threads, 1 re-entry | registration re-entry completes without deadlock; no callback under registry/provider lock |

### 4.5 `fault_boundary_tests.cpp` (`T016-TS-007`)

| Case | Assertion |
| --- | --- |
| `CoreSurface_ExposesNoDomainSpecificFaultSemantics` | no public core declaration names a fault campaign, fault taxonomy, mutation policy, or domain fault primitive; the forbidden-vocabulary scan over the T016-owned surface and the accepted core headers finds none |
| `CoreSurface_ExposesOnlyBoundedControlledSeams` | the only externally usable extension seams are the accepted bounded observation/provider seams; no unbounded or ad-hoc injection entry point |
| `CoreSurface_HasNoUncontrolledMutationEntryPoint` | no public operation mutates a route, queue, or record without its exact issued handle |

### 4.6 `consumer/main.cpp` (`T016-TS-008`)

A separate translation unit that includes every accepted public core header and performs one minimal
four-family-agnostic round trip, proving the public include/build/link surface is stable for an
out-of-package consumer. Returns 0 on success, 1 otherwise.

## 5. Exact diagnostic and determinism design

- Core diagnostics are asserted against the exact `DiagnosticCode`, `DiagnosticSeverity`, and
  `ValidationPhase` produced by the accepted factories, and against `DiagnosticSet::serialize()` bytes.
- Provider outcomes are asserted against `to_string(outcome)`, `provider_diagnostic_code(outcome)`,
  and `provider_diagnostic_message(outcome)`; the `unsupported_policy` row is asserted as
  `XCOM-PROV-E030`. No existing outcome, code, message, or ordering is asserted as changed.
- Ordering determinism: the same logical input built by permuted construction order must produce an
  identical serialized diagnostic sequence (`XCOM-SW-CORE-010`).
- Locale independence: `Diagnostics_LocaleIndependent` runs under a non-default `LC_ALL`/`LC_NUMERIC`
  process locale and asserts unchanged bytes.

## 6. Bounds and resource design

| Resource | Bound used by T016 | Notes |
| --- | --- | --- |
| Threads per concurrency case | ≤ 4 | declared per case; joined before verdict |
| Items per concurrency case | ≤ 8 (queue bound) or ≤ 32 (iteration bound) | declared per case |
| Loopback routes | 4 (`kMaximumRoutes`) | NEG-17 exercises the bound |
| Loopback queue items | 8 (`kMaximumQueueItems`) | NEG-18 exercises the bound |
| Provider registry | 8 (`kMaximumProviders`); fixtures use capacity 1–2 | NEG-16 exercises the bound |
| Descriptor payload/routes/queue | 65,536 / 32 / 32 | CHK-12 asserts exact limits |
| Payload bytes per item | bounded, synthetic, ≤ 65,536 | no sensitive or real payload |
| Iterations / waits | finite constants | no unbounded loop or wait; no wall-clock threshold |

## 7. Failure semantics of the matrix

- A failing fixture construction is a test failure, never a silent pass.
- Each rejection case asserts the exact stable outcome **and** that the injected defect produced no
  mutation and no emitted item.
- Concurrency cases join all threads before asserting; a data race or lost item is a test failure.
- The consumer returns nonzero on any expectation failure; the suites use GTest’s nonzero exit on
  failure; no case is skipped or conditionally disabled.

## 8. Build wiring design (`src/xverse/xcom/CMakeLists.txt`, additive)

- Add one `add_executable`/`target_include_directories`/`target_link_libraries`/
  `xverse_xcom_apply_runtime_rules` block per suite, linking
  `xverse::xcom_provider_loopback GTest::gtest_main GTest::gmock Threads::Threads`, with the
  `tests/xcom/core_matrix` directory on the private include path.
- Register each suite with `gtest_discover_tests(... PROPERTIES LABELS "t016-<area>")` using a
  single hyphenated label token (CMake 3.22 label workaround), and register the consumer with one
  `add_test(NAME xcom_core_matrix_external_consumer ... )` under label `t016`.
- No runtime library target, `XVERSE_XCOM_RUNTIME_TARGETS` entry, `cmake/*.cmake`, or root build file
  changes; `xcom_build_contract` stays green.
- Existing core-types, lifecycle, provider-loopback, observation, activation-plan, and
  validation-session target blocks are unchanged.

## 9. Doxygen plan

Each new file carries a file block with `@file`, `@brief`, `@ownership`, `@lifetime`, `@thread_safety`,
and `@failure`. Each helper class and public helper function carries `@brief` plus the applicable
contract tags. The admitted documentation configuration is not changed; strict declaration-level
Doxygen remains `DOX-GAP-01` (T011/T037).

## 10. Traceability

| T016 requirement | Detailed-design element |
| --- | --- |
| T016-SR-001 | §3, §8, D-01…D-04 |
| T016-SR-002 | §4.1 interaction-kind cases |
| T016-SR-003 | §4.1 capability cases; NEG-06…NEG-09, NEG-14, NEG-16 |
| T016-SR-004 | §4.1 policy cases; NEG-05, NEG-10…NEG-13 |
| T016-SR-005 | §4.1 ownership case; §3.3; NEG-21, NEG-22, NEG-24 |
| T016-SR-006 | §4.1 lifecycle cases; §4.3; NEG-18, NEG-20 |
| T016-SR-007 | §6; §4.1 bounds cases; NEG-04, NEG-15, NEG-17…NEG-19 |
| T016-SR-008 | §5; §4.1 diagnostics cases |
| T016-SR-009 | §4.3 |
| T016-SR-010 | §4.4; §6 |
| T016-SR-011 | §4.2 |
| T016-SR-012 | §4.5 |
| T016-SR-013 | §6; §7 |
| T016-SR-014 | §8; D-01…D-04 |
| T016-SR-015 | §8; §6 |
| T016-SR-016 | §6 (synthetic payloads) |
| T016-SR-017 | §9 |
| T016-SR-018 | §8 |
| T016-SR-019 | §8 |
| T016-SR-020 | §10 |
