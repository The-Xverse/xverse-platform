# T033 Unit Specifications — Reusable Provider, Observer, Stimulation-Tool, and Gateway Contract Suites

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T033 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → unit specifications |
| Revision | 1 (reusable contract-suite slice) |
| Baseline revision | `2fd395e39e44e1f6fe9547998b47499d996b1756` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit framework | GoogleTest over the T011-admitted offline envelope and the T012 subtree build contract, plus the deterministic Phase 7 gate and the T007–T010 register validators for governance |
| Classification | Public-safe engineering work product |

T033 realizes four reusable contract-suite drivers under `tests/xcom/contract_suites/` and proves them with four
additive `t033-<kind>` executables (eight cases). Each requirement `T033-SR-###` owns one unit specification
`T033-SR-###-U`. "Verified" means the suite check or named inspection exists, is deterministic, and passes at the
recorded candidate revision; it is not a deployed-service, remote-tool, or compatibility claim.

## 2. Unit inventory

| Unit | Component | Source of truth | Kind | Cases |
| --- | --- | --- | --- | --- |
| `T033-SR-001-U` | `T033-SR-001-CMP` | `tests/xcom/contract_suites/provider_contract_suite.hpp` | provider suite seam/identity | `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` |
| `T033-SR-002-U` | `T033-SR-002-CMP` | `tests/xcom/contract_suites/provider_contract_suite.hpp` | provider version rejection | `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` |
| `T033-SR-003-U` | `T033-SR-003-CMP` | `tests/xcom/contract_suites/provider_contract_suite.hpp` | provider lifecycle/saturation | `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` |
| `T033-SR-004-U` | `T033-SR-004-CMP` | `tests/xcom/contract_suites/observer_contract_suite.hpp` | observer metadata/identity | `T033ObserverContractSuite.AcceptedObservationHubConforms` |
| `T033-SR-005-U` | `T033-SR-005-CMP` | `tests/xcom/contract_suites/observer_contract_suite.hpp` | observer bounds/counters | `T033ObserverContractSuite.SuiteIsReusableAcrossHubInstances` |
| `T033-SR-006-U` | `T033-SR-006-CMP` | `tests/xcom/contract_suites/observer_contract_suite.hpp` | observer detach/isolation | `T033ObserverContractSuite.AcceptedObservationHubConforms` |
| `T033-SR-007-U` | `T033-SR-007-CMP` | `tests/xcom/contract_suites/stimulation_tool_contract_suite.hpp` | stimulation actions/provenance | `T033StimulationToolContractSuite.AcceptedStimulationPathConforms` |
| `T033-SR-008-U` | `T033-SR-008-CMP` | `tests/xcom/contract_suites/stimulation_tool_contract_suite.hpp` | stimulation zero emission | `T033StimulationToolContractSuite.SuiteIsReusableAcrossFixtures` |
| `T033-SR-009-U` | `T033-SR-009-CMP` | `tests/xcom/contract_suites/gateway_contract_suite.hpp` | gateway version/op surface | `T033GatewayContractSuite.AcceptedGatewaySessionConforms` |
| `T033-SR-010-U` | `T033-SR-010-CMP` | `tests/xcom/contract_suites/gateway_contract_suite.hpp` | gateway permit/zero emission | `T033GatewayContractSuite.AcceptedGatewaySessionConforms` |
| `T033-SR-011-U` | `T033-SR-011-CMP` | `tests/xcom/contract_suites/gateway_contract_suite.hpp` | gateway observation bounds | `T033GatewayContractSuite.AcceptedGatewaySessionConforms` |
| `T033-SR-012-U` | `T033-SR-012-CMP` | `tests/xcom/contract_suites/gateway_contract_suite.hpp` | gateway actions/lease | `T033GatewayContractSuite.SuiteIsReusableAcrossFixtures` |
| `T033-SR-013-U` | `T033-SR-013-CMP` | `tests/xcom/contract_suites/gateway_contract_suite.hpp` | gateway framing/counters | `T033GatewayContractSuite.SuiteIsReusableAcrossFixtures` |
| `T033-SR-014-U` | `T033-SR-014-CMP` | `tests/xcom/contract_suites/*_contract_suite.hpp` | suite reuse/genericity | the four `SuiteIsReusable…` cases |
| `T033-SR-015-U` | `T033-SR-015-CMP` | `src/xverse/xcom/CMakeLists.txt` | additive build/public-safety | build/discovery inspection; contributory `T033GatewayContractSuite.AcceptedGatewaySessionConforms` |
| `T033-SR-016-U` | `T033-SR-016-CMP` | `docs/engineering/xcom/t033/**` | governance/documentation | register validators, gate, file-block inspection; contributory `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` |

## 3. Unit specifications

### T033-SR-001-U — Provider suite subject seam and identity

- **Inputs:** a `ProviderSubject` over an accepted `CommunicationProvider`.
- **Outputs:** provider checks `P-01`…`P-03`.
- **Invariants:** the suite names no concrete provider type; the descriptor is valid, compatible, and nonzero;
  registration succeeds and a duplicate is rejected.
- **Cases:** `T033ProviderContractSuite.AcceptedLoopbackProviderConforms`.
- **Static checks:** the suites compile under the accepted warning-as-error profile.

### T033-SR-002-U — Provider unsupported-version rejection

- **Inputs:** a prepare request whose provider-contract version is `9.9.9`.
- **Outputs:** provider check `P-04`.
- **Invariants:** an unsupported contract version is rejected with `unsupported_contract_version` before any
  provider dispatch.
- **Cases:** `T033ProviderContractSuite.AcceptedLoopbackProviderConforms`.

### T033-SR-003-U — Provider lifecycle and bounded saturation

- **Inputs:** the accepted provider/route lifecycle with a queue capacity of one item.
- **Outputs:** provider checks `P-05`…`P-13`.
- **Invariants:** prepare/activate succeed; the first submit is accepted; the second is rejected-new without
  losing the first; the exact FIFO item is received; drain and close complete; reconcile is bounded.
- **Cases:** `T033ProviderContractSuite.AcceptedLoopbackProviderConforms`.

### T033-SR-004-U — Observer metadata-only records and identity

- **Inputs:** a metadata-only tap and a published accepted item.
- **Outputs:** observer checks `O-01`…`O-04`, `O-07`.
- **Invariants:** the record carries no payload byte, reports `omitted`, preserves the exact logical identity,
  and reports the complete source payload size.
- **Cases:** `T033ObserverContractSuite.AcceptedObservationHubConforms`.

### T033-SR-005-U — Observer bounded counters

- **Inputs:** two publications against a capacity-one tap.
- **Outputs:** observer checks `O-05`, `O-06`, `O-08`.
- **Invariants:** the drop-newest counter increments, exactly one record is retained, and the queue drains
  exactly once.
- **Cases:** `T033ObserverContractSuite.SuiteIsReusableAcrossHubInstances`.

### T033-SR-006-U — Observer detach and isolation

- **Inputs:** an exact attached handle that is detached.
- **Outputs:** observer checks `O-09`…`O-11`.
- **Invariants:** detach succeeds; a detached handle is rejected by poll and snapshot; the normal route still
  accepts a further item.
- **Cases:** `T033ObserverContractSuite.AcceptedObservationHubConforms`.

### T033-SR-007-U — Stimulation four actions, provenance, and ordering

- **Inputs:** an opened accepted guard/action path over one permit/policy.
- **Outputs:** stimulation checks `S-01`, `S-02-0`…`S-02-3`, `S-05`.
- **Invariants:** each allowed action emits exactly once with synthetic provenance and preserved request
  identity, and a durable intent precedes every emission.
- **Cases:** `T033StimulationToolContractSuite.AcceptedStimulationPathConforms`.

### T033-SR-008-U — Stimulation zero emission

- **Inputs:** an out-of-window request and a non-active-session request.
- **Outputs:** stimulation checks `S-03`, `S-04`.
- **Invariants:** neither request is `Emitted`, and neither increments the emission count.
- **Cases:** `T033StimulationToolContractSuite.SuiteIsReusableAcrossFixtures`.

### T033-SR-009-U — Gateway version and operation surface

- **Inputs:** the committed gateway operation-name table exposed by `gateway_operation_names()` and the generated
  `ProtocolVersion`, `QueryVersionRequest`, and `QueryVersionResponse` messages.
- **Outputs:** gateway checks `G-02`, `G-03`, `G-04`.
- **Invariants:** the committed table has ten methods; the supported major negotiates and reports `1.0`; an
  unsupported major is rejected with no item.
- **Cases:** `T033GatewayContractSuite.AcceptedGatewaySessionConforms`.

### T033-SR-010-U — Gateway permit and zero emission

- **Inputs:** the exact permit and an unarmed session.
- **Outputs:** gateway checks `G-05`, `G-08`.
- **Invariants:** the exact permit arms the session; an unarmed session emits nothing and reports a non-success
  outcome.
- **Cases:** `T033GatewayContractSuite.AcceptedGatewaySessionConforms`.

### T033-SR-011-U — Gateway observation bounds

- **Inputs:** an opened observation stream with an over-large requested record count.
- **Outputs:** gateway check `G-09`.
- **Invariants:** the granted count does not exceed the configured maximum, and a read returns no more than the
  granted or buffer bound.
- **Cases:** `T033GatewayContractSuite.AcceptedGatewaySessionConforms`.

### T033-SR-012-U — Gateway actions and lease

- **Inputs:** the four allowed actions and the acquire/release lease round trip.
- **Outputs:** gateway checks `G-01`, `G-06`, `G-07`.
- **Invariants:** the accepted action path opens; each allowed action emits exactly once; the lease acquires
  `LEASE_ACTIVE`, releases `LEASE_RELEASED`, and is not held afterwards.
- **Cases:** `T033GatewayContractSuite.SuiteIsReusableAcrossFixtures`.

### T033-SR-013-U — Gateway framing and counters

- **Inputs:** valid, over-bound, and unknown-method frames, and a normal submission.
- **Outputs:** gateway checks `G-10`, `G-11`.
- **Invariants:** framing rejects over-bound and unknown-method frames fail-closed; the bounded counters include
  an explicit evidence-incomplete count.
- **Cases:** `T033GatewayContractSuite.SuiteIsReusableAcrossFixtures`.

### T033-SR-014-U — Suite reuse and genericity

- **Inputs:** multiple subjects per suite.
- **Outputs:** the four `SuiteIsReusable…` verdicts.
- **Invariants:** the same suite body is instantiated at least twice per suite without editing the suite header;
  the provider suite passes against two independently implemented providers.
- **Cases:** `T033ProviderContractSuite.SuiteIsReusableAcrossProviderImplementations`,
  `T033ObserverContractSuite.SuiteIsReusableAcrossHubInstances`,
  `T033StimulationToolContractSuite.SuiteIsReusableAcrossFixtures`,
  `T033GatewayContractSuite.SuiteIsReusableAcrossFixtures`.

### T033-SR-015-U — Additive build wiring and public-safe evidence

- **Inputs:** the build files, the discovered test inventory, and the committed suite sources.
- **Outputs:** the discovered `t033-` count, the unchanged runtime-target inventory, and the safety verdict.
- **Invariants:** four additive `t033-<kind>` targets; no existing target/label/value changes; no payload,
  permit content, secret, private address, or host path is committed.
- **Cases:** build/discovery inspection; contributory `T033GatewayContractSuite.AcceptedGatewaySessionConforms`.

### T033-SR-016-U — Governance, maturity, and documentation

- **Inputs:** the T007–T010 registers, the work products, and the source file blocks.
- **Outputs:** the validator verdict, the recorded maturity, and the documentation verdict.
- **Invariants:** registers unchanged in substance; REF-002 `unchanged` with an empty `promoted` list; the
  reusable suites recorded implemented by T033 with T034–T041 allocated; the suite headers carry the required
  file block.
- **Cases:** register validators, the Phase 7 gate, and file-block inspection; contributory
  `T033ProviderContractSuite.AcceptedLoopbackProviderConforms`.

## 4. Case index

| Case | Suite | Primary requirement |
| --- | --- | --- |
| `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` | provider | T033-SR-001, T033-SR-002, T033-SR-003 |
| `T033ProviderContractSuite.SuiteIsReusableAcrossProviderImplementations` | provider | T033-SR-014 |
| `T033ObserverContractSuite.AcceptedObservationHubConforms` | observer | T033-SR-004, T033-SR-006 |
| `T033ObserverContractSuite.SuiteIsReusableAcrossHubInstances` | observer | T033-SR-005, T033-SR-014 |
| `T033StimulationToolContractSuite.AcceptedStimulationPathConforms` | stimulation-tool | T033-SR-007 |
| `T033StimulationToolContractSuite.SuiteIsReusableAcrossFixtures` | stimulation-tool | T033-SR-008, T033-SR-014 |
| `T033GatewayContractSuite.AcceptedGatewaySessionConforms` | gateway | T033-SR-009, T033-SR-010, T033-SR-011 |
| `T033GatewayContractSuite.SuiteIsReusableAcrossFixtures` | gateway | T033-SR-012, T033-SR-013, T033-SR-014 |

## 5. Coverage

Every `T033-SR-###` requirement is covered by at least one unit case or named inspection; every case belongs to
one listed requirement and one suite. Unit cases are contributory; the exact acceptance decision remains
T039/T041.
