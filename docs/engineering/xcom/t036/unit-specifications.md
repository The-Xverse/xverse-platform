# T036 Unit Specifications — Controlled Disabled/Enabled-Tap Benchmarks and Repository-Owned Results

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T036 (capability 007, slice `T-INTG`/evidence) |
| Stage / role | plan → unit specifications |
| Revision | 1 (Phase 8 controlled-benchmark slice) |
| Baseline revision | `8ec69ddd34ed8c7a07adbcb631dcfb2da3faf15f` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit framework | the admitted offline C++20 build, CTest, the accepted disabled-tap benchmark fixture, and the Python benchmark harness; evidence units are the repository-owned harness and report |
| Classification | Public-safe engineering work product |

T036 adds no accepted production unit. Each requirement `T036-SR-###` owns one verification unit
specification `T036-SR-###-U` whose cases are **contributory** already-discovered cases of the accepted
suites, the accepted benchmark fixture, or a named inspection over the repository-owned evidence.
"Verified" means the named case, measurement, or inspection exists, is deterministic, and passes at the
recorded candidate revision; it is not a deployed-service, compatibility, or production-readiness claim.

## 2. Unit inventory

| Unit | Component | Source of truth | Kind | Cases |
| --- | --- | --- | --- | --- |
| `T036-SR-001-U` | `T036-SR-001-CMP` | `reports/xcom-queue/t036-benchmark.json` | controlled disabled/enabled measurement | `xcom_observation_disabled_benchmark` |
| `T036-SR-002-U` | `T036-SR-002-CMP` | `reports/xcom-queue/t036-benchmark.json` | uncertainty statement | `CoreMatrixConcurrency.ConcurrentRepeatedRuns_DeterministicOutcome` |
| `T036-SR-003-U` | `T036-SR-003-CMP` | `reports/xcom-queue/t036-benchmark.json` | gated 2% median comparison (tap_disabled vs baseline) | `CoreMatrixConcurrency.ConcurrentSubmitReceive_ExactlyOncePerRouteFifo` |
| `T036-SR-004-U` | `T036-SR-004-CMP` | `reports/xcom-queue/t036-benchmark.json` | environment identity | `T033ObserverContractSuite.AcceptedObservationHubConforms` |
| `T036-SR-005-U` | `T036-SR-005-CMP` | `reports/xcom-queue/t036-benchmark.json` | raw samples and method | `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue` |
| `T036-SR-006-U` | `T036-SR-006-CMP` | `reports/xcom-queue/t036-benchmark.json` | non-production limitations | `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` |
| `T036-SR-007-U` | `T036-SR-007-CMP` | `engineering/run_xcom_benchmarks.py` | owned/local-only execution | `T026JournalRecovery.test_journal_restart_recovery_and_orphans` |
| `T036-SR-008-U` | `T036-SR-008-CMP` | `reports/xcom-queue/t036-benchmark.json` | exact-candidate binding and hashes | `T033GatewayContractSuite.AcceptedGatewaySessionConforms` |
| `T036-SR-009-U` | `T036-SR-009-CMP` | `engineering/run_xcom_benchmarks.py` | fail-closed `--verify` | `XcomToolGatewayBounds.MessageSizeBoundEnforced` |
| `T036-SR-010-U` | `T036-SR-010-CMP` | `engineering/trace/links.json` | unchanged accepted behavior | `T034SecondProviderSuite.ReusedProviderContractSuitePasses` |
| `T036-SR-011-U` | `T036-SR-011-CMP` | `engineering/trace/links.json` | governance/trace reconciliation | `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource` |
| `T036-SR-012-U` | `T036-SR-012-CMP` | `docs/engineering/xcom/t036/architecture.md` | offline/no-legacy execution and public safety | `T033StimulationToolContractSuite.AcceptedStimulationPathConforms` |

## 3. Unit specifications

### T036-SR-001-U — Controlled disabled/enabled measurement

- **Inputs:** the admitted offline toolchain, the exact candidate checkout, and the accepted owned
  loopback fixture.
- **Outputs:** the disabled and enabled median latency and throughput for the fixed sample set.
- **Invariants:** the same workload and sample count apply to both cases; the warm-up is recorded.
- **Cases (contributory, already discovered):** `xcom_observation_disabled_benchmark`.
- **Static checks:** the admitted-offline dependency preflight.

### T036-SR-002-U — Uncertainty statement

- **Inputs:** the raw paired samples for the disabled and enabled cases.
- **Outputs:** per-case sample count, median, and dispersion/interval.
- **Invariants:** the uncertainty is computed from the recorded samples and is labelled non-production.
- **Cases (contributory):** `CoreMatrixConcurrency.ConcurrentRepeatedRuns_DeterministicOutcome`.

### T036-SR-003-U — Median regression comparison

- **Inputs:** the tap-disabled and baseline medians, the enabled-versus-disabled medians, and the
  per-sample paired regressions.
- **Outputs:** the gated median latency and throughput regression of `tap_disabled` versus the same
  baseline and its 2% comparison outcome, plus the ungated enabled-versus-disabled observation.
- **Invariants:** the gated comparison is deterministic; a gated value beyond the threshold yields
  `failed`; the enabled-versus-disabled regression is recorded but not gated.
- **Cases (contributory):** `CoreMatrixConcurrency.ConcurrentSubmitReceive_ExactlyOncePerRouteFifo`.

### T036-SR-004-U — Environment identity

- **Inputs:** the resolved tool and admitted-input identities.
- **Outputs:** the recorded identities and hashes.
- **Invariants:** identities and hashes are public-safe; host-specific absolute paths are excluded.
- **Cases (contributory):** `T033ObserverContractSuite.AcceptedObservationHubConforms`.

### T036-SR-005-U — Raw samples and method

- **Inputs:** the executed measurement run.
- **Outputs:** the raw paired samples and the method record.
- **Invariants:** the samples and method are sufficient to reproduce the reported statistics.
- **Cases (contributory):** `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue`.

### T036-SR-006-U — Non-production limitations

- **Inputs:** the report limitations and the uncertainty note.
- **Outputs:** the declared non-production verdict.
- **Invariants:** no production performance claim is made; uncontrolled factors are listed.
- **Cases (contributory):** `T033ProviderContractSuite.AcceptedLoopbackProviderConforms`.

### T036-SR-007-U — Owned/local-only execution

- **Inputs:** the harness command set and the committed artifacts.
- **Outputs:** the forbidden-resource verdict.
- **Invariants:** no network, DNS, TLS, legacy binary, or production workload.
- **Cases (contributory):** `T026JournalRecovery.test_journal_restart_recovery_and_orphans`.

### T036-SR-008-U — Candidate binding and hashes

- **Inputs:** the accepted baseline revision, the candidate material inventory/digest, and the
  report/artifact contents.
- **Outputs:** the binding and hash record.
- **Invariants:** the candidate commit is the direct child of the baseline carrying the recorded material;
  a changed material digest/hash, a foreign commit, or any other revision fails `--verify`.
- **Cases (contributory):** `T033GatewayContractSuite.AcceptedGatewaySessionConforms`.

### T036-SR-009-U — Fail-closed harness verification

- **Inputs:** the report and the harness `--verify` checks.
- **Outputs:** the verification exit status.
- **Invariants:** a missing/incomplete field, incomplete method/uncertainty, stale binding, or exceeded
  threshold yields a nonzero exit.
- **Cases (contributory):** `XcomToolGatewayBounds.MessageSizeBoundEnforced`.

### T036-SR-010-U — No accepted production change

- **Inputs:** the baseline-versus-candidate diff.
- **Outputs:** the changed-path verdict and the preserved discovered inventory.
- **Invariants:** no accepted production source, test, target, label, command, or expected value changes.
- **Cases (contributory):** `T034SecondProviderSuite.ReusedProviderContractSuitePasses`.

### T036-SR-011-U — Register reconciliation and trace

- **Inputs:** the T007–T010 models and the candidate trace.
- **Outputs:** the validator verdict, recorded maturity, and trace verdict.
- **Invariants:** registers unchanged in substance; REF-002 `unchanged` with an empty `promoted` list;
  the required trace edges present.
- **Cases (contributory):** `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource`.

### T036-SR-012-U — Offline, no-legacy, and public safety

- **Inputs:** the executed command set and the committed artifacts.
- **Outputs:** the forbidden-resource and public-safety verdict.
- **Invariants:** no TCP listener, `AF_INET`/`AF_INET6` socket, DNS, resolver, TLS, external peer, legacy
  binary, production workload, credential, private address, or host path.
- **Cases (contributory):** `T033StimulationToolContractSuite.AcceptedStimulationPathConforms`.

## 4. Case index

| Case | Category | Primary requirement |
| --- | --- | --- |
| `xcom_observation_disabled_benchmark` | accepted disabled-tap benchmark | T036-SR-001 |
| `CoreMatrixConcurrency.ConcurrentRepeatedRuns_DeterministicOutcome` | concurrency/determinism | T036-SR-002 |
| `CoreMatrixConcurrency.ConcurrentSubmitReceive_ExactlyOncePerRouteFifo` | concurrency | T036-SR-003 |
| `T033ObserverContractSuite.AcceptedObservationHubConforms` | observer contract | T036-SR-004 |
| `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue` | XDL plan determinism | T036-SR-005 |
| `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` | provider contract | T036-SR-006 |
| `T026JournalRecovery.test_journal_restart_recovery_and_orphans` | journal recovery | T036-SR-007 |
| `T033GatewayContractSuite.AcceptedGatewaySessionConforms` | gateway contract | T036-SR-008 |
| `XcomToolGatewayBounds.MessageSizeBoundEnforced` | bounds | T036-SR-009 |
| `T034SecondProviderSuite.ReusedProviderContractSuitePasses` | replaceability | T036-SR-010 |
| `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource` | recovery | T036-SR-011 |
| `T033StimulationToolContractSuite.AcceptedStimulationPathConforms` | stimulation-tool contract | T036-SR-012 |

## 5. Coverage

Every `T036-SR-###` requirement is covered by at least one contributory case, the benchmark harness, or a
named inspection; every case belongs to one listed requirement and appears in the T036 selected case set.
Unit cases are contributory; the benchmark harness and report are the evidence, and the exact acceptance
decision remains T039/T041.
