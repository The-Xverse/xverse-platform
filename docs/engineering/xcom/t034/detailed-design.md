# T034 Detailed Design — Second Minimal Synthetic Provider and Replaceability / Version-Rejection / Failure-Isolation Proof

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T034 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → detailed design |
| Revision | 1 (second-provider replaceability slice) |
| Baseline revision | `f63491101aed1c4f7db57fa7c506ad5c0510038f` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

T034 authors one second minimal synthetic provider over the accepted `CommunicationProvider` boundary and proves
replaceability, fail-closed version/capability rejection, and unrelated-route isolation with three additive
`t034-<kind>` drivers. The design is written **before** implementation; the implementation must realize it
exactly or record a design change and re-review.

## 2. Design decisions

| ID | Decision | Rationale | Requirement |
| --- | --- | --- | --- |
| `T34-DD-01` | The second provider is validated by the **unchanged** T033 `ProviderContractSuite` through a new `ProviderSubject` adapter | Realizes the accepted provider-contract replaceability statement without a second conformance definition | T034-SR-002, T034-SR-010 |
| `T34-DD-02` | `SyntheticProvider` uses independently written fixed route slots and a fixed reject-new queue prefix, distinct from the accepted loopback provider's storage | Proves the provider boundary is implementation-agnostic | T034-SR-001, T034-SR-003 |
| `T34-DD-03` | `SyntheticProvider::descriptor_compatible()` admits only nonzero masks within the finite storage limits and does not itself check the contract version | Keeps the version gate where the accepted composition owns it (registration), and makes capability misreporting observable as `invalid_descriptor` | T034-SR-001, T034-SR-007 |
| `T34-DD-04` | A `configure_forced_failure(ProviderOutcome)` test seam returns a configured stable outcome from `prepare`/`submit` without mutating route state | Makes the failure-isolation proof deterministic without weakening the accepted composition | T034-SR-008, T034-SR-009 |
| `T34-DD-05` | Version and capability rejection are exercised both at explicit registration (misreporting provider) and at preparation (unsupported request) | Covers the accepted User Story 4 "rejected when they misreport capability ... or emit an unsupported contract version" | T034-SR-005…`-007` |
| `T34-DD-06` | Isolation is proven for an unrelated active route on an independently composed provider **and** for a rejected provider registered into the same composition | The accepted composition owns one registry and one active route per fixture; both proofs bound the containment claim honestly | T034-SR-009 |
| `T34-DD-07` | The fixture source is compiled directly into each `t034-<kind>` test executable; no library target is added | Keeps `XVERSE_XCOM_RUNTIME_TARGETS` unchanged, mirroring the T032 fixture executable | T034-SR-011 |
| `T34-DD-08` | Three additive test drivers: `t034-replaceability`, `t034-version`, `t034-isolation` | Named, discoverable, bounded, and isolated per concern | T034-SR-011 |
| `T34-DD-09` | The drivers consume only the admitted offline toolchain and the accepted in-process libraries; no admitted dependency is added and no gRPC runtime is linked | Offline/no-new-dependency rule (`T032-GAP-01`) | T034-SR-014 |
| `T34-DD-10` | Committed fixtures and drivers retain no payload byte, permit content, secret, private address, or host path | Public-safety rule | T034-SR-012 |
| `T34-DD-11` | T034 changes no accepted provider/composition/loopback/T033 byte | Ownership and maturity separation | T034-SR-013 |

## 3. Second minimal synthetic provider (`synthetic_provider.hpp`)

```cpp
namespace xverse::xcom {

/**
 * @brief Second owned in-process synthetic provider for provider-replaceability evidence only.
 * @details Implements the accepted CommunicationProvider interface with independent fixed route slots
 *          and a fixed reject-new queue prefix. It models no network, transport, clock, retry, timing,
 *          reliability, or compatibility behavior.
 */
class SyntheticProvider final : public CommunicationProvider {
 public:
  static constexpr std::size_t kMaximumRoutes = 2U;      // finite storage
  static constexpr std::size_t kMaximumQueueItems = 8U;  // finite per-route storage

  explicit SyntheticProvider(const ProviderDescriptor& descriptor) noexcept;

  [[nodiscard]] const ProviderDescriptor& descriptor() const noexcept override;
  [[nodiscard]] bool descriptor_compatible() const noexcept override;  // nonzero masks + within storage
  [[nodiscard]] std::uint64_t instance_id() const noexcept override;    // distinct per instance

  /** Test seam: return a configured stable outcome from prepare/submit without mutating state. */
  void configure_forced_failure(ProviderOutcome outcome) noexcept;

 private:
  friend class ProviderComposition;
  [[nodiscard]] ProviderResult<ProviderRouteToken> prepare(const ProviderRouteBinding&) noexcept override;
  [[nodiscard]] ProviderStatus activate(const ProviderRouteToken&, const LifecycleController&) noexcept override;
  [[nodiscard]] ProviderStatus submit(const ProviderRouteToken&, const CommunicationItem&,
                                      const LifecycleController&) noexcept override;
  [[nodiscard]] ProviderResult<CommunicationItem> receive(const ProviderRouteToken&,
                                                          const LifecycleController&) noexcept override;
  [[nodiscard]] ProviderStatus drain(const ProviderRouteToken&, const LifecycleController&) noexcept override;
  [[nodiscard]] ProviderStatus close(const ProviderRouteToken&, const LifecycleController&) noexcept override;
  [[nodiscard]] ProviderResult<ProviderRouteStateValue> state(const ProviderRouteToken&) const noexcept override;
  [[nodiscard]] ProviderResult<ProviderRouteStateValue> reconcile(const ProviderRouteToken&,
                                                                   const LifecycleController&) const noexcept override;
  // ... fixed slots, reject-new queue ring, instance identity, mutex ...
};

}  // namespace xverse::xcom
```

Behavioral contract (identical outcomes to the accepted loopback provider where the accepted suite requires
them):

| Operation | Outcome |
| --- | --- |
| `prepare` over a one-item queue | `prepared` with a nonzero token, or the configured forced failure, or a stable limit outcome |
| `activate` | `activated` only for an exact current binding |
| `submit` into a full reject-new queue | `queue_saturated`; every earlier item preserved |
| `receive` | `received` with the exact oldest item, or `queue_empty` |
| `drain` / `close` | `draining` / `closed` |
| `state` / `reconcile` | bounded `ProviderRouteStateValue`, or `interrupted_resource` |
| `prepare` after activation | `inactive_route` (no silent replacement) |
| invalid/foreign token | `invalid_provider_route_handle` without mutation |
| forced failure set | the configured stable outcome, no state mutation |

## 4. Replaceability driver (`second_provider_suite_tests.cpp`, label `t034-replaceability`)

Subject seam (new adapter, T033 `ProviderSubject` unchanged):

```cpp
class SyntheticProviderSubject final : public ProviderSubject {
 public:
  SyntheticProviderSubject()
      : descriptor_(make_descriptor("provider.t034.synthetic", kAllInteractions,
                                    delivery_capability_bit(DeliveryCapability::best_effort),
                                    ordering_capability_bit(OrderingCapability::per_route_fifo),
                                    1U, 1U, 1U)),
        provider_(descriptor_) {}
  CommunicationProvider& provider() noexcept override { return provider_; }
 private:
  ProviderDescriptor descriptor_;
  SyntheticProvider provider_;
};
```

| Case | Assertion |
| --- | --- |
| `T034SecondProviderSuite.ReusedProviderContractSuitePasses` | the unchanged `ProviderContractSuite::run` returns `ok()` with `P-01`…`P-13` passing on the second provider |
| `T034SecondProviderSuite.ProviderIsIndependentOfLoopback` | the second provider has a nonzero instance identity distinct from a loopback instance, a valid descriptor, and no dependence on loopback storage |
| `T034SecondProviderSuite.BoundedCapabilitiesAndSaturation` | provider checks `P-02`, `P-06`, `P-07`, `P-08` pass on the second provider (registration, accepted, `queue_saturated`, bounded active state) |
| `T034SecondProviderLifecycle.CompletesFullBoundedLifecycle` | provider checks `P-05`, `P-09`…`P-13` pass (activate, reconcile, FIFO receive, empty, drain, close) |

The driver names no concrete provider type inside the suite body; it supplies the second provider only through
the new subject (CHK-16).

## 5. Version/capability rejection driver (`second_provider_version_tests.cpp`, label `t034-version`)

| Case | Assertion |
| --- | --- |
| `T034VersionRejection.MisreportedContractVersionRejectedAtRegistration` | a `SyntheticProvider` over a descriptor declaring contract version `2.0.0` is rejected by `register_provider` with `unsupported_contract_version`, and no provider-route handle is issued |
| `T034VersionRejection.UnsupportedRequestedVersionRejectedBeforeActivation` | over a registered `1.0.0` second provider, `prepare` with requested version `9.9.9` returns `unsupported_contract_version`, `prepared()` is false, and `activated()` is false |
| `T034VersionRejection.MisreportedCapabilityRejectedAtRegistration` | a `SyntheticProvider` whose descriptor declares more routes or queue items than its finite storage is rejected by `register_provider` with `invalid_descriptor` |
| `T034VersionRejection.UnsupportedRequestedCapabilityRejectedBeforeActivation` | over a registered second provider, a request for a delivery claim it does not advertise (for example `reliable`) returns the matching stable `unsupported_*` outcome before activation |
| `T034VersionRejection.RejectionEmitsNothing` | after each rejection, the route is not prepared/active and no `submit` is dispatched, so zero items are emitted |

Every rejection path is fail-closed before provider dispatch and mutates no operational state (FR-006).

## 6. Failure-isolation driver (`second_provider_isolation_tests.cpp`, label `t034-isolation`)

| Case | Assertion |
| --- | --- |
| `T034FailureIsolation.ProviderFailureYieldsStableOutcomeNoEmission` | a second provider configured with a forced `unsupported_policy` (or another stable failure) reports that exact outcome from `prepare` and emits no item |
| `T034FailureIsolation.UnrelatedRouteRemainsActiveAndBounded` | an unrelated loopback route prepared and activated before the failure stays `active`, accepts a further item, and reports `queued_items()`/`queue_capacity()` unchanged |
| `T034FailureIsolation.UnrelatedRouteStateStaysObservable` | the unrelated route's `route_state()` snapshot and `reconcile_route()` outcome stay observable and consistent after the second provider's failure |
| `T034FailureIsolation.RejectedAdapterLeavesUnrelatedRouteIntact` | registering a misreporting (`2.0.0`) second provider into the unrelated route's composition with capacity two returns `unsupported_contract_version` and leaves the unrelated route active, bounded, and able to receive its exact queued item |

The design deliberately composes the two probes as (a) an independently composed failing route and (b) a
rejected provider registered into the same composition as the unrelated route. Both bound the containment claim
to the accepted single-registry/single-active-route composition model (T034-GAP-02).

## 7. Test design (drivers)

| Driver | Label | Cases |
| --- | --- | --- |
| `second_provider_suite_tests.cpp` | `t034-replaceability` | `ReusedProviderContractSuitePasses`, `ProviderIsIndependentOfLoopback`, `BoundedCapabilitiesAndSaturation`, `CompletesFullBoundedLifecycle` |
| `second_provider_version_tests.cpp` | `t034-version` | `MisreportedContractVersionRejectedAtRegistration`, `UnsupportedRequestedVersionRejectedBeforeActivation`, `MisreportedCapabilityRejectedAtRegistration`, `UnsupportedRequestedCapabilityRejectedBeforeActivation`, `RejectionEmitsNothing` |
| `second_provider_isolation_tests.cpp` | `t034-isolation` | `ProviderFailureYieldsStableOutcomeNoEmission`, `UnrelatedRouteRemainsActiveAndBounded`, `UnrelatedRouteStateStaysObservable`, `RejectedAdapterLeavesUnrelatedRouteIntact` |

Each case asserts its exact outcomes with a bounded failure detail. All cases use only the standard library, the
accepted in-process libraries, the accepted T016/T033 fixtures, and GTest.

## 8. Failure semantics

| Condition | Outcome |
| --- | --- |
| a second provider declares an unsupported contract version | registration `unsupported_contract_version`, no handle (`T034-SR-005`) |
| a route requests an unsupported version | preparation `unsupported_contract_version`, not activated (`T034-SR-006`) |
| a provider claims capability beyond its storage | registration `invalid_descriptor` (`T034-SR-007`) |
| a route requests an unsupported capability | preparation `unsupported_*`, not activated (`T034-SR-007`) |
| a second provider fails prepare/submit | the configured stable outcome, no mutation, no emission (`T034-SR-008`) |
| an unrelated route exists during the failure | it stays active, bounded, and observable with its exact items (`T034-SR-009`) |
| a required suite check is absent | `SuiteReport::passed` returns false; the case fails closed |

## 9. Determinism and safety

- Every registration, prepare, activate, submit, receive, drain, and close is finite and bounded; no case depends
  on ambient wall-clock time, randomness, or environment.
- The second provider performs only in-process operations over owned fixed storage; no network, DNS, TLS, dynamic
  load, legacy access, or production workload occurs.
- Committed files and evidence contain no credential, private address, real or proprietary payload, or
  environment-specific host path.

## 10. Traceability

| Design element | Requirement | Checks |
| --- | --- | --- |
| `T34-DD-01`/`-02` replaceability and independent storage | T034-SR-001, T034-SR-002, T034-SR-010 | CHK-02, CHK-05 |
| `T34-DD-02`/`-03` bounded capability and saturation | T034-SR-003, T034-SR-007 | CHK-03, CHK-09, CHK-10 |
| `T34-DD-02` lifecycle | T034-SR-004 | CHK-04 |
| `T34-DD-05` version/capability rejection | T034-SR-005, T034-SR-006, T034-SR-007 | CHK-07, CHK-08, CHK-09, CHK-10 |
| `T34-DD-04`/`-06` failure isolation | T034-SR-008, T034-SR-009 | CHK-11, CHK-12, CHK-13 |
| `T34-DD-07`/`-08` additive fixture compilation and drivers | T034-SR-011 | CHK-16, CHK-17 |
| `T34-DD-10` public-safety | T034-SR-012 | CHK-18, CHK-19 |
| `T34-DD-09`/`-11` offline and ownership | T034-SR-013, T034-SR-014 | CHK-01, CHK-20, CHK-21, CHK-22 |

## 11. Doxygen and documentation

- The new fixture header/source and the three drivers carry the X-COM file block (`@file`, `@brief`,
  `@ownership`, `@lifetime`, `@thread_safety`, `@failure`, `@par Traceability`) that the changed units require.
- Generated Protocol Buffers documentation remains `DOX-GAP-02` (T037); T034 documents only its hand-written
  fixture and drivers.

## 12. Compatibility contract and generated-code provenance

- T034 adds **no** generated code and **no** admitted dependency. It does not touch
  `proto/xverse/xcom/v1/tool_gateway.proto` or any `XCOM-XLC-002` message.
- **Compatibility contract.** The second provider implements the accepted `CommunicationProvider` source-level
  interface and rejects any provider-contract version other than the accepted `1.0.0` fail-closed. It defines no
  competing provider interface, RPC, or configuration language; a route that requests an unsupported version or
  capability is rejected before activation.
