# T034 Unit Specifications — Second Minimal Synthetic Provider and Replaceability / Version-Rejection / Failure-Isolation Proof

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T034 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → unit specifications |
| Revision | 1 (second-provider replaceability slice) |
| Baseline revision | `f63491101aed1c4f7db57fa7c506ad5c0510038f` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit framework | GoogleTest over the T011-admitted offline envelope and the T012 subtree build contract, plus the deterministic Phase 7 gate and the T007–T010 register validators for governance |
| Classification | Public-safe engineering work product |

T034 realizes one second minimal synthetic provider and three additive `t034-<kind>` drivers (thirteen cases).
Each requirement `T034-SR-###` owns one unit specification `T034-SR-###-U`. "Verified" means the named case or
inspection exists, is deterministic, and passes at the recorded candidate revision; it is not a
deployed-service, remote-tool, or compatibility claim.

## 2. Unit inventory

| Unit | Component | Source of truth | Kind | Cases |
| --- | --- | --- | --- | --- |
| `T034-SR-001-U` | `T034-SR-001-CMP` | `src/xverse/xcom/fixtures/synthetic_provider.{hpp,cpp}` | second provider interface/identity | `T034SecondProviderSuite.ProviderIsIndependentOfLoopback` |
| `T034-SR-002-U` | `T034-SR-002-CMP` | `tests/xcom/contract_suites/second_provider_suite_tests.cpp` | reused-suite replaceability | `T034SecondProviderSuite.ReusedProviderContractSuitePasses` |
| `T034-SR-003-U` | `T034-SR-003-CMP` | `src/xverse/xcom/fixtures/synthetic_provider.cpp` | bounded capability/saturation | `T034SecondProviderSuite.BoundedCapabilitiesAndSaturation` |
| `T034-SR-004-U` | `T034-SR-004-CMP` | `src/xverse/xcom/fixtures/synthetic_provider.cpp` | bounded provider lifecycle | `T034SecondProviderLifecycle.CompletesFullBoundedLifecycle` |
| `T034-SR-005-U` | `T034-SR-005-CMP` | `tests/xcom/contract_suites/second_provider_version_tests.cpp` | misreported-version rejection at registration | `T034VersionRejection.MisreportedContractVersionRejectedAtRegistration` |
| `T034-SR-006-U` | `T034-SR-006-CMP` | `tests/xcom/contract_suites/second_provider_version_tests.cpp` | unsupported-requested-version rejection | `T034VersionRejection.UnsupportedRequestedVersionRejectedBeforeActivation` |
| `T034-SR-007-U` | `T034-SR-007-CMP` | `tests/xcom/contract_suites/second_provider_version_tests.cpp` | capability misreport/mismatch rejection | `T034VersionRejection.MisreportedCapabilityRejectedAtRegistration`, `T034VersionRejection.UnsupportedRequestedCapabilityRejectedBeforeActivation` |
| `T034-SR-008-U` | `T034-SR-008-CMP` | `tests/xcom/contract_suites/second_provider_isolation_tests.cpp` | provider failure, no emission | `T034FailureIsolation.ProviderFailureYieldsStableOutcomeNoEmission` |
| `T034-SR-009-U` | `T034-SR-009-CMP` | `tests/xcom/contract_suites/second_provider_isolation_tests.cpp` | unrelated-route isolation | `T034FailureIsolation.UnrelatedRouteRemainsActiveAndBounded`, `T034FailureIsolation.UnrelatedRouteStateStaysObservable`, `T034FailureIsolation.RejectedAdapterLeavesUnrelatedRouteIntact` |
| `T034-SR-010-U` | `T034-SR-010-CMP` | `tests/xcom/contract_suites/second_provider_suite_tests.cpp` | reused-header consumption | `T034SecondProviderSuite.ReusedProviderContractSuitePasses` |
| `T034-SR-011-U` | `T034-SR-011-CMP` | `src/xverse/xcom/CMakeLists.txt` | additive build wiring | build/discovery inspection; contributory `T034SecondProviderSuite.BoundedCapabilitiesAndSaturation` |
| `T034-SR-012-U` | `T034-SR-012-CMP` | `docs/engineering/xcom/t034/**` | public-safe evidence and Doxygen | file-block/safety inspection; contributory `T034FailureIsolation.UnrelatedRouteRemainsActiveAndBounded` |
| `T034-SR-013-U` | `T034-SR-013-CMP` | `docs/engineering/xcom/t034/**` | governance/documentation | register validators, gate, trace validation; contributory `T034SecondProviderSuite.ProviderIsIndependentOfLoopback` |
| `T034-SR-014-U` | `T034-SR-014-CMP` | `src/xverse/xcom/fixtures/synthetic_provider.cpp` | in-process-only / no legacy | forbidden-API inspection; contributory `T034SecondProviderSuite.ReusedProviderContractSuitePasses` |

## 3. Unit specifications

### T034-SR-001-U — Second provider interface and identity

- **Inputs:** a `ProviderDescriptor` within the second provider's finite storage.
- **Outputs:** the retained descriptor, `descriptor_compatible()`, and a nonzero instance identity.
- **Invariants:** the provider implements only the accepted `CommunicationProvider` interface; the identity is
  distinct from the loopback provider; no accepted provider/composition/loopback byte changes.
- **Cases:** `T034SecondProviderSuite.ProviderIsIndependentOfLoopback`.
- **Static checks:** the fixture compiles under the accepted warning-as-error profile.

### T034-SR-002-U — Replaceability via the reused suite

- **Inputs:** a new `ProviderSubject` over the second provider.
- **Outputs:** the `SuiteReport` from the unchanged T033 `ProviderContractSuite::run`.
- **Invariants:** `P-01`…`P-13` pass; the suite body is not edited; the subject names the second provider only.
- **Cases:** `T034SecondProviderSuite.ReusedProviderContractSuitePasses`.

### T034-SR-003-U — Bounded capability and saturation

- **Inputs:** a reject-new queue of capacity one over the second provider.
- **Outputs:** provider checks `P-02`, `P-06`, `P-07`, `P-08`.
- **Invariants:** the first submit is `accepted`; the second is `queue_saturated` without losing the first; the
  active state reports `queued_items()==1` and `queue_capacity()==1`.
- **Cases:** `T034SecondProviderSuite.BoundedCapabilitiesAndSaturation`.

### T034-SR-004-U — Bounded lifecycle

- **Inputs:** the accepted provider/route lifecycle over the second provider.
- **Outputs:** provider checks `P-05`, `P-09`…`P-13`.
- **Invariants:** prepare/activate succeed; the exact FIFO item is received; drain and close complete; reconcile
  is bounded and no item is lost or duplicated.
- **Cases:** `T034SecondProviderLifecycle.CompletesFullBoundedLifecycle`.

### T034-SR-005-U — Misreported contract version rejected at registration

- **Inputs:** a second provider over a descriptor declaring contract version `2.0.0`.
- **Outputs:** the registration outcome.
- **Invariants:** registration returns `unsupported_contract_version` before any route preparation or activation
  and issues no handle.
- **Cases:** `T034VersionRejection.MisreportedContractVersionRejectedAtRegistration`.

### T034-SR-006-U — Unsupported requested version rejected before activation

- **Inputs:** a registered `1.0.0` second provider and a request naming `9.9.9`.
- **Outputs:** the preparation outcome and fixture state.
- **Invariants:** preparation returns `unsupported_contract_version`; the fixture is neither prepared nor
  activated.
- **Cases:** `T034VersionRejection.UnsupportedRequestedVersionRejectedBeforeActivation`.

### T034-SR-007-U — Capability misreport and mismatch rejection

- **Inputs:** a descriptor claiming more routes/queue items than the finite storage, and a request naming an
  unadvertised delivery claim.
- **Outputs:** the registration and preparation outcomes.
- **Invariants:** the misreporting descriptor fails registration with `invalid_descriptor`; the unsupported
  request fails preparation with the matching stable `unsupported_*` outcome before activation.
- **Cases:** `T034VersionRejection.MisreportedCapabilityRejectedAtRegistration`,
  `T034VersionRejection.UnsupportedRequestedCapabilityRejectedBeforeActivation`.

### T034-SR-008-U — Provider failure yields a stable non-success with no emission

- **Inputs:** a second provider configured with a forced stable failure outcome.
- **Outputs:** the prepare/submit outcome and the emission count.
- **Invariants:** the configured outcome is returned, unrelated state is not mutated, and zero items are emitted.
- **Cases:** `T034FailureIsolation.ProviderFailureYieldsStableOutcomeNoEmission`.

### T034-SR-009-U — Unrelated-route isolation

- **Inputs:** an active unrelated loopback route and a failing or rejected second-provider route.
- **Outputs:** the unrelated route's activity, queue state, and snapshot after the failure.
- **Invariants:** the unrelated route stays active with unchanged bounds, still accepts and returns its exact
  items, and stays observable; the rejected provider issues no handle.
- **Cases:** `T034FailureIsolation.UnrelatedRouteRemainsActiveAndBounded`,
  `T034FailureIsolation.UnrelatedRouteStateStaysObservable`,
  `T034FailureIsolation.RejectedAdapterLeavesUnrelatedRouteIntact`.

### T034-SR-010-U — Reused suite consumed unchanged

- **Inputs:** the accepted `tests/xcom/contract_suites/provider_contract_suite.hpp` and `ProviderSubject`.
- **Outputs:** the unchanged-file verdict and the second-provider conformance verdict.
- **Invariants:** the suite header and seam are not modified; the second provider is validated through a new
  subject adapter only.
- **Cases:** `T034SecondProviderSuite.ReusedProviderContractSuitePasses`; the unchanged-header inspection.

### T034-SR-011-U — Additive build wiring

- **Inputs:** the build file and the discovered test inventory.
- **Outputs:** the discovered `t034-` count and the unchanged runtime-target inventory.
- **Invariants:** three additive `t034-<kind>` targets; the fixture is compiled into the test executables; no
  existing target/label/value changes.
- **Cases:** build/discovery inspection; contributory `T034SecondProviderSuite.BoundedCapabilitiesAndSaturation`.

### T034-SR-012-U — Public-safe evidence and Doxygen

- **Inputs:** the committed fixture, drivers, and work products.
- **Outputs:** the safety verdict and the file-block verdict.
- **Invariants:** no payload, permit content, secret, private address, or host path is committed; every changed
  unit carries the X-COM file block.
- **Cases:** file-block/safety inspection; contributory
  `T034FailureIsolation.UnrelatedRouteRemainsActiveAndBounded`.

### T034-SR-013-U — Governance and documentation

- **Inputs:** the T007–T010 registers, the work products, and the trace records.
- **Outputs:** the validator verdict, the recorded maturity, and the trace verdict.
- **Invariants:** registers unchanged in substance; REF-002 `unchanged` with an empty `promoted` list; the second
  provider recorded implemented by T034 with T035–T041 allocated; the required trace links present.
- **Cases:** register validators, the Phase 7 gate, trace validation; contributory
  `T034SecondProviderSuite.ProviderIsIndependentOfLoopback`.

### T034-SR-014-U — In-process only, no network or legacy

- **Inputs:** the fixture source and the committed test paths.
- **Outputs:** the forbidden-API verdict.
- **Invariants:** no TCP listener, `AF_INET`/`AF_INET6` socket, DNS, resolver, TLS, external peer, legacy binary,
  or production workload is used.
- **Cases:** forbidden-API inspection; contributory
  `T034SecondProviderSuite.ReusedProviderContractSuitePasses`.

## 4. Case index

| Case | Driver | Primary requirement |
| --- | --- | --- |
| `T034SecondProviderSuite.ReusedProviderContractSuitePasses` | replaceability | T034-SR-002, T034-SR-010 |
| `T034SecondProviderSuite.ProviderIsIndependentOfLoopback` | replaceability | T034-SR-001 |
| `T034SecondProviderSuite.BoundedCapabilitiesAndSaturation` | replaceability | T034-SR-003 |
| `T034SecondProviderLifecycle.CompletesFullBoundedLifecycle` | replaceability | T034-SR-004 |
| `T034VersionRejection.MisreportedContractVersionRejectedAtRegistration` | version | T034-SR-005 |
| `T034VersionRejection.UnsupportedRequestedVersionRejectedBeforeActivation` | version | T034-SR-006 |
| `T034VersionRejection.MisreportedCapabilityRejectedAtRegistration` | version | T034-SR-007 |
| `T034VersionRejection.UnsupportedRequestedCapabilityRejectedBeforeActivation` | version | T034-SR-007 |
| `T034VersionRejection.RejectionEmitsNothing` | version | T034-SR-005, T034-SR-006, T034-SR-007 |
| `T034FailureIsolation.ProviderFailureYieldsStableOutcomeNoEmission` | isolation | T034-SR-008 |
| `T034FailureIsolation.UnrelatedRouteRemainsActiveAndBounded` | isolation | T034-SR-009 |
| `T034FailureIsolation.UnrelatedRouteStateStaysObservable` | isolation | T034-SR-009 |
| `T034FailureIsolation.RejectedAdapterLeavesUnrelatedRouteIntact` | isolation | T034-SR-009 |

## 5. Coverage

Every `T034-SR-###` requirement is covered by at least one unit case or named inspection; every case belongs to
one listed requirement and one driver. Unit cases are contributory; the exact acceptance decision remains
T039/T041.
