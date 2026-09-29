# T035 Unit Specifications — Exact-Candidate Verification Matrix and Repository-Owned Results

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T035 (capability 007, slice `T-INTG`/evidence) |
| Stage / role | plan → unit specifications |
| Revision | 1 (Phase 8 exact-candidate verification slice) |
| Baseline revision | `dab68568bd8d189b14c7a4a9e3a9c325085a7529` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit framework | the admitted offline C++20 build, CTest, the ASan/UBSan build, `cppcheck`, the inherited Phase 6 conformance runner, and the Python suite; evidence units are the repository-owned report and measure descriptors |
| Classification | Public-safe engineering work product |

T035 adds no production unit. Each requirement `T035-SR-###` owns one verification unit specification
`T035-SR-###-U` whose cases are **contributory** already-discovered cases of the accepted suites or a named
inspection over the repository-owned evidence. "Verified" means the named case, measure, or inspection exists,
is deterministic, and passes at the recorded candidate revision; it is not a deployed-service, compatibility,
or production-readiness claim.

## 2. Unit inventory

| Unit | Component | Source of truth | Kind | Cases |
| --- | --- | --- | --- | --- |
| `T035-SR-001-U` | `T035-SR-001-CMP` | `reports/xcom-queue/t035-verification.json` | complete C++ unit/contract matrix | `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` |
| `T035-SR-002-U` | `T035-SR-002-CMP` | `engineering/verification/measures/unit.json` | preserved inherited suites | `T034SecondProviderSuite.ReusedProviderContractSuitePasses` |
| `T035-SR-003-U` | `T035-SR-003-CMP` | `reports/xcom-queue/t035-verification.json` | negative-case matrix | `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch` |
| `T035-SR-004-U` | `T035-SR-004-CMP` | `reports/xcom-queue/t035-verification.json` | concurrency/determinism matrix | `CoreMatrixConcurrency.ConcurrentRepeatedRuns_DeterministicOutcome` |
| `T035-SR-005-U` | `T035-SR-005-CMP` | `engineering/verification/measures/sanitizer.json` | sanitizer build/run | `CoreMatrixConcurrency.ConcurrentSubmitReceive_ExactlyOncePerRouteFifo` |
| `T035-SR-006-U` | `T035-SR-006-CMP` | `engineering/verification/measures/static_analysis.json` | static analysis | `T034VersionRejection.RejectionEmitsNothing` |
| `T035-SR-007-U` | `T035-SR-007-CMP` | `reports/xcom-queue/t035-verification.json` | Python suite | `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue` |
| `T035-SR-008-U` | `T035-SR-008-CMP` | `engineering/verification/measures/integration.json` | whole-system integration | `Integration.GenerationRotationInvalidatesLiveHandle` |
| `T035-SR-009-U` | `T035-SR-009-CMP` | `engineering/verification/measures/conformance.json` | inherited conformance recheck | `XcomStimulationMatrixConcurrency.ConcurrentQuotaEmissionDeterminism` |
| `T035-SR-010-U` | `T035-SR-010-CMP` | `reports/xcom-queue/t035-verification.json` | repository-owned report | `T033GatewayContractSuite.AcceptedGatewaySessionConforms` |
| `T035-SR-011-U` | `T035-SR-011-CMP` | `reports/xcom-queue/t035-verification.json` | command/outcome honesty | `XcomToolGatewayBounds.MessageSizeBoundEnforced` |
| `T035-SR-012-U` | `T035-SR-012-CMP` | `reports/xcom-queue/t035-verification.json` | environment identity | `T033ObserverContractSuite.AcceptedObservationHubConforms` |
| `T035-SR-013-U` | `T035-SR-013-CMP` | `docs/engineering/xcom/t035/**` | public-safe evidence | `T033StimulationToolContractSuite.AcceptedStimulationPathConforms` |
| `T035-SR-014-U` | `T035-SR-014-CMP` | `engineering/verification/measures/**` | unchanged accepted behavior | `XcomToolGatewayNegative.NoTcpOrAddressPrimitive` |
| `T035-SR-015-U` | `T035-SR-015-CMP` | `engineering/trace/links.json` | governance/trace reconciliation | `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource` |
| `T035-SR-016-U` | `T035-SR-016-CMP` | `docs/engineering/xcom/t035/architecture.md` | offline/no-legacy execution | `T026JournalRecovery.test_journal_restart_recovery_and_orphans` |

## 3. Unit specifications

### T035-SR-001-U — Complete C++ unit/contract matrix

- **Inputs:** the admitted offline toolchain and the exact candidate checkout.
- **Outputs:** the discovered and passed CTest counts for the full suite.
- **Invariants:** the build is warning-as-error C++20; the full discovered suite runs; the counts are recorded.
- **Cases (contributory, already discovered):** `T033ProviderContractSuite.AcceptedLoopbackProviderConforms`.
- **Static checks:** the admitted-offline dependency preflight.

### T035-SR-002-U — Preserved inherited suites and behavior

- **Inputs:** the inherited T016/T020/T026–T034 suites.
- **Outputs:** the preserved discovered inventory and pass outcome.
- **Invariants:** no existing target, test name, label, command, or expected value changes or is reduced.
- **Cases (contributory):** `T034SecondProviderSuite.ReusedProviderContractSuitePasses`.

### T035-SR-003-U — Negative-case matrix

- **Inputs:** the accepted malformed/incompatible/over-capacity/unauthorized cases.
- **Outputs:** the per-negative-case outcomes.
- **Invariants:** every negative path is rejected fail-closed with the accepted stable outcome.
- **Cases (contributory):** `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch`.

### T035-SR-004-U — Concurrency and determinism matrix

- **Inputs:** the accepted deterministic-concurrency cases.
- **Outputs:** the repeated-run determinism outcomes.
- **Invariants:** repeated runs produce equal results; no verdict depends on ambient timing.
- **Cases (contributory):** `CoreMatrixConcurrency.ConcurrentRepeatedRuns_DeterministicOutcome`.

### T035-SR-005-U — Sanitizer build and run

- **Inputs:** a separate ASan/UBSan configuration of the candidate.
- **Outputs:** the sanitizer build and suite outcome.
- **Invariants:** a sanitizer failure is recorded as failed, never suppressed.
- **Cases (contributory):** `CoreMatrixConcurrency.ConcurrentSubmitReceive_ExactlyOncePerRouteFifo`.

### T035-SR-006-U — Static analysis

- **Inputs:** `src/xverse/xcom/src` and the `cppcheck` tool.
- **Outputs:** the `cppcheck` exit status and outcome.
- **Invariants:** error-exit is enabled; a finding is recorded verbatim.
- **Cases (contributory):** `T034VersionRejection.RejectionEmitsNothing`.

### T035-SR-007-U — Existing Python tests

- **Inputs:** the repository Python test suite.
- **Outputs:** the collected/passed counts and outcome.
- **Invariants:** the Python suite executes; its result is recorded, not inferred.
- **Cases (contributory):** `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue`.

### T035-SR-008-U — Whole-system integration measure

- **Inputs:** the pinned target repository and the trusted assembly contract.
- **Outputs:** the assembled-revision identity and outcome.
- **Invariants:** only the trusted target-repository measure is reported as integration.
- **Cases (contributory):** `Integration.GenerationRotationInvalidatesLiveHandle`.

### T035-SR-009-U — Inherited Phase 6 conformance recheck

- **Inputs:** the inherited T026–T029 conformance inspections.
- **Outputs:** the 26 inspection outcomes.
- **Invariants:** a changed protected Phase 6 input fails the recheck closed.
- **Cases (contributory):** `XcomStimulationMatrixConcurrency.ConcurrentQuotaEmissionDeterminism`.

### T035-SR-010-U — Repository-owned report

- **Inputs:** the executed command results.
- **Outputs:** `reports/xcom-queue/t035-verification.json`.
- **Invariants:** the report carries `commands`, `outcomes`, `hashes`, `environment`, bounded logs, and the
  exact-candidate identity.
- **Cases (contributory):** `T033GatewayContractSuite.AcceptedGatewaySessionConforms`.

### T035-SR-011-U — Command, exit status, and honest outcome

- **Inputs:** each executed command and its trusted discovery check.
- **Outputs:** per-command argv, exit status, and `pass`/`failed`/`blocked` outcome.
- **Invariants:** `pass` only when the discovery check is satisfied; missing/stale/skipped/failed is never pass.
- **Cases (contributory):** `XcomToolGatewayBounds.MessageSizeBoundEnforced`.

### T035-SR-012-U — Tool and environment identity

- **Inputs:** the resolved tool and admitted-input identities.
- **Outputs:** the recorded identities and hashes.
- **Invariants:** identities and hashes are public-safe; host-specific absolute paths are excluded.
- **Cases (contributory):** `T033ObserverContractSuite.AcceptedObservationHubConforms`.

### T035-SR-013-U — Public-safe evidence and logs

- **Inputs:** the committed report, work products, and bounded logs.
- **Outputs:** the public-safety verdict.
- **Invariants:** no payload, permit content, secret, private address, host path, or proprietary excerpt.
- **Cases (contributory):** `T033StimulationToolContractSuite.AcceptedStimulationPathConforms`.

### T035-SR-014-U — No accepted production change

- **Inputs:** the baseline-versus-candidate diff.
- **Outputs:** the changed-path verdict and the preserved discovered inventory.
- **Invariants:** no accepted production source, test, target, label, command, or expected value changes.
- **Cases (contributory):** `XcomToolGatewayNegative.NoTcpOrAddressPrimitive`.

### T035-SR-015-U — Register reconciliation and trace

- **Inputs:** the T007–T010 registers and the candidate trace.
- **Outputs:** the validator verdict, recorded maturity, and trace verdict.
- **Invariants:** registers unchanged in substance; REF-002 `unchanged` with an empty `promoted` list; the
  required trace edges present.
- **Cases (contributory):** `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource`.

### T035-SR-016-U — Offline and no-legacy execution

- **Inputs:** the executed command set and the committed artifacts.
- **Outputs:** the forbidden-resource verdict.
- **Invariants:** no TCP listener, `AF_INET`/`AF_INET6` socket, DNS, resolver, TLS, external peer, legacy
  binary, or production workload.
- **Cases (contributory):** `T026JournalRecovery.test_journal_restart_recovery_and_orphans`.

## 4. Case index

| Case | Category | Primary requirement |
| --- | --- | --- |
| `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` | provider contract | T035-SR-001 |
| `T034SecondProviderSuite.ReusedProviderContractSuitePasses` | replaceability | T035-SR-002 |
| `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch` | negative | T035-SR-003 |
| `CoreMatrixConcurrency.ConcurrentRepeatedRuns_DeterministicOutcome` | concurrency | T035-SR-004 |
| `CoreMatrixConcurrency.ConcurrentSubmitReceive_ExactlyOncePerRouteFifo` | concurrency/sanitizer | T035-SR-005 |
| `T034VersionRejection.RejectionEmitsNothing` | negative | T035-SR-006 |
| `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue` | XDL plan | T035-SR-007 |
| `Integration.GenerationRotationInvalidatesLiveHandle` | integration | T035-SR-008 |
| `XcomStimulationMatrixConcurrency.ConcurrentQuotaEmissionDeterminism` | stimulation concurrency | T035-SR-009 |
| `T033GatewayContractSuite.AcceptedGatewaySessionConforms` | gateway contract | T035-SR-010 |
| `XcomToolGatewayBounds.MessageSizeBoundEnforced` | bounds | T035-SR-011 |
| `T033ObserverContractSuite.AcceptedObservationHubConforms` | observer contract | T035-SR-012 |
| `T033StimulationToolContractSuite.AcceptedStimulationPathConforms` | stimulation-tool contract | T035-SR-013 |
| `XcomToolGatewayNegative.NoTcpOrAddressPrimitive` | no-network primitive | T035-SR-014 |
| `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource` | recovery | T035-SR-015 |
| `T026JournalRecovery.test_journal_restart_recovery_and_orphans` | journal recovery | T035-SR-016 |

## 5. Coverage

Every `T035-SR-###` requirement is covered by at least one contributory case or named inspection; every case
belongs to one listed requirement and appears in the T035 selected case set. Unit cases are contributory; the
executed matrix is the evidence, and the exact acceptance decision remains T039/T041.
