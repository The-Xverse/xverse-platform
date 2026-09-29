# T035 Detailed Design — Exact-Candidate Verification Matrix and Repository-Owned Results

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T035 (capability 007, slice `T-INTG`/evidence) |
| Stage / role | plan → detailed design |
| Revision | 1 (Phase 8 exact-candidate verification slice) |
| Baseline revision | `dab68568bd8d189b14c7a4a9e3a9c325085a7529` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

T035 executes the accepted capability-007 verification matrix at one exact candidate revision and records the
results in repository-owned evidence. The design is written **before** execution; the implementation must
realize it exactly or record a design change and re-review.

## 2. Design decisions

| ID | Decision | Rationale | Requirement |
| --- | --- | --- | --- |
| `T035-DD-01` | T035 adds no production source, test, or build target; it executes and records the accepted matrix | T035 owns evidence, not new behavior; adding code would change the verified object | T035-SR-014 |
| `T035-DD-02` | The verification route is the admitted offline build plus the full CTest suite, a separate ASan/UBSan build, `cppcheck`, the Phase 6 conformance recheck, the trusted whole-system integration measure, and the Python suite | Matches the accepted plan step 9 and the trusted policy measure set | T035-SR-001…`-009` |
| `T035-DD-03` | A measure outcome is `pass` only when its trusted discovery check is satisfied; otherwise it is `failed`, and an unavailable input is `blocked` | Prevents stale, skipped, or failed evidence from supporting acceptance | T035-SR-011 |
| `T035-DD-04` | The report `reports/xcom-queue/t035-verification.json` carries `commands`, `outcomes`, `hashes`, `environment`, bounded logs, and exact-candidate identity | Implements the repository-owned evidence contract from `build-environment.md` | T035-SR-010, T035-SR-011 |
| `T035-DD-05` | The public report records tool identities and hashes, not host-specific absolute prefix, manifest, or evidence-store paths | Public-safety rule and reviewer expectation | T035-SR-012 |
| `T035-DD-06` | The `engineering/verification/measures/**` descriptors are refreshed content-only with `revision` preserved (and a new `sanitizer` descriptor) | A revision bump would stale every accepted `verified_by`/`analyzed_by` link | T035-SR-014, `T035-OPEN-01` |
| `T035-DD-07` | Whole-system integration is only the trusted target-repository measure; candidate-local unit/static/sanitizer/validation runs are never reported as integration | The trusted policy defines the integration contract; honesty rule | T035-SR-008, T035-GAP-02 |
| `T035-DD-08` | T035 links `implemented_by` to its own repository-owned evidence and work products, and names executed cases by their accepted discovered test IDs | T035's realized artifacts are evidence, not new code | T035-SR-015 |
| `T035-DD-09` | The candidate-local selected case set uses only already-discovered CTest names, so the trusted measures' exact-discovery check is satisfied without adding tests | Keeps the discovered inventory unchanged | T035-SR-002 |
| `T035-DD-10` | T035 does not run, duplicate, or claim the T036/T037/T038/T039/T040/T041 deliverables | Scope and maturity separation | T035-SR-010, T035-SR-015 |

## 3. Verification route (exact commands)

The route below is the repository-owned verification matrix. `${XVERSE_FABRIC_ROOT}` and the admitted inputs are
resolved by the trusted policy; the admitted inputs are `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN`. The implementation records the exact
resolved argv and exit status actually observed.

| # | Measure | Command (portable descriptor) | Trusted discovery check |
| --- | --- | --- | --- |
| M-1 | unit | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py unit` | `100% tests passed` |
| M-2 | integration | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py integration` | `100% tests passed` |
| M-3 | validation | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py validation` | `[1-9][0-9]* passed` |
| M-4 | static_analysis | `cppcheck --error-exitcode=1 --quiet --std=c++20 --language=c++ --suppress=invalidLifetime src/xverse/xcom/src` | exit code `0` |
| M-5 | conformance | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_conformance.py` | `26 conformance inspections passed` |
| M-6 | sanitizer | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py sanitizer` | `100% tests passed` |

The candidate-local route additionally runs `python3 -m pytest -q` for the existing Python tests and records
the collected/passed count. A candidate-local build is a candidate-local check and is labelled as such.

## 4. Evidence report schema (`reports/xcom-queue/t035-verification.json`)

```json
{
  "schema_version": 1,
  "task_id": "T035",
  "baseline_revision": "<40-hex accepted baseline>",
  "candidate_revision": "<40-hex candidate commit>",
  "candidate_identity": {"material_digest": "<sha256>", "generated_at": "<iso-8601>"},
  "environment": {
    "compiler": "<identity>", "cmake": "<version>", "ninja": "<version>",
    "cppcheck": "<version>", "python": "<version>",
    "admitted_toolchain_sha256": "<sha256>", "package_manifest_sha256": "<sha256>",
    "gtest_prefix_sha256": "<sha256>"
  },
  "commands": [{"id": "M-1", "argv": ["..."], "exit_code": 0, "log_sha256": "<sha256>"}],
  "outcomes": {"M-1": "pass", "M-2": "pass", "M-3": "pass",
               "M-4": "pass", "M-5": "pass", "M-6": "pass",
               "python": "pass"},
  "hashes": {"<artifact path>": "<sha256>", "report_self": "<sha256>"},
  "logs": {"M-1": "<bounded public-safe excerpt>", "...": "..."},
  "limitations": ["verification-only; no runtime, compatibility, performance, or production claim"]
}
```

- `commands[i].argv` is the exact resolved argv that was executed; `exit_code` is the observed status.
- `outcomes[m]` is derived from the trusted discovery check for `m`; it is `failed` when the check is not
  satisfied and `blocked` when a required input is unavailable.
- `hashes` records SHA-256 of the retained evidence and of the changed T035 artifacts; it never records a
  host-specific absolute path.
- `logs` holds bounded excerpts only; a full private log is retained outside the public report.

## 5. Measure descriptor refresh (`engineering/verification/measures/**`)

| Descriptor | Change | Constraint |
| --- | --- | --- |
| `unit.json` | content-only refresh: Phase 8 route, T035 selected case set | `id` `unit`, `revision` `1`, `kind` `unit` preserved |
| `integration.json` | content-only refresh: Phase 8 route, T035 selected case set | `id` `integration`, `revision` `1`, `kind` `integration` preserved |
| `validation.json` | content-only refresh: Phase 8 route, T035 selected case set | `id` `validation`, `revision` `1`, `kind` `validation` preserved |
| `static_analysis.json` | content-only refresh: title/`command_runs` only | `id` `static_analysis`, `revision` `1`, `kind` `static_analysis` preserved; `command` unchanged |
| `sanitizer.json` | add | new `id` `sanitizer`, `revision` `1`, `kind` `sanitizer`; `command` = M-6 |
| `conformance.json` | unchanged | its 26 named inspections remain the accepted conformance set |

## 6. Selected case set (already-discovered CTest names)

The T035 selected case set names only cases that the accepted suites already discover. It is used by the unit,
integration, and validation descriptors and by `T035-VS-ACCUMULATED`; it is not a new test definition.

| Case | Category |
| --- | --- |
| `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` | provider contract |
| `T033ObserverContractSuite.AcceptedObservationHubConforms` | observer contract |
| `T033StimulationToolContractSuite.AcceptedStimulationPathConforms` | stimulation-tool contract |
| `T033GatewayContractSuite.AcceptedGatewaySessionConforms` | gateway contract |
| `T034SecondProviderSuite.ReusedProviderContractSuitePasses` | replaceability |
| `T034VersionRejection.RejectionEmitsNothing` | negative / zero emission |
| `T034VersionRejection.UnsupportedRequestedCapabilityRejectedBeforeActivation` | negative / capability |
| `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch` | negative |
| `CoreMatrixConcurrency.ConcurrentRepeatedRuns_DeterministicOutcome` | concurrency / determinism |
| `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource` | recovery |
| `XcomStimulationGuardConcurrency.GuardBoundedDeterministicConcurrency` | stimulation concurrency |
| `XcomStimulationMatrixConcurrency.ConcurrentQuotaEmissionDeterminism` | stimulation concurrency |
| `XcomToolGatewayNegative.NoTcpOrAddressPrimitive` | no network primitive |
| `XcomToolGatewayBounds.MessageSizeBoundEnforced` | bounds |
| `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue` | XDL plan determinism |
| `T026JournalRecovery.test_journal_restart_recovery_and_orphans` | stimulation journal recovery |

## 7. Failure semantics

| Condition | Outcome |
| --- | --- |
| a measure's trusted discovery check is not satisfied | outcome `failed`; the report does not claim pass (`T035-SR-011`) |
| a required admitted input or tool is unavailable | outcome `blocked` with the reason; the candidate fails closed (`T035-OPEN-04`) |
| the candidate revision or material digest changes between commands | the affected evidence is stale and is re-run or reported `failed` (`T035-SR-011`) |
| a sanitizer, static-analysis, or conformance check fails | the failure is recorded verbatim; no suppression (`T035-SR-005`…`-009`) |
| a committed artifact or bounded log would contain private content | the content is redacted/omitted before commit (`T035-SR-013`) |
| a measure `revision` would change | the change is rejected; descriptors stay content-only (`T035-SR-014`) |

## 8. Determinism and safety

- Every executed suite is finite and bounded; no T035 verdict depends on ambient wall-clock time, randomness,
  or environment beyond the recorded identities.
- No verification command opens a network listener or socket, resolves a name, or contacts a legacy or external
  resource.
- Committed files and bounded logs contain no credential, private address, real or proprietary payload, or
  host-specific absolute path.

## 9. Traceability

| Design element | Requirement | Checks |
| --- | --- | --- |
| `T035-DD-01`/`-02` executed matrix | T035-SR-001…`-009` | CHK-01…CHK-10 |
| `T035-DD-03`/`-04`/`-07` outcomes and report | T035-SR-010, T035-SR-011 | CHK-11, CHK-19 |
| `T035-DD-05` public safety | T035-SR-012, T035-SR-013 | CHK-12, CHK-13 |
| `T035-DD-06` descriptor refresh | T035-SR-014 | CHK-16, CHK-17 |
| `T035-DD-08` evidence trace | T035-SR-015 | CHK-14, CHK-18, CHK-20 |
| `T035-DD-09`/`-10` unchanged inventory and scope | T035-SR-002, T035-SR-016 | CHK-03, CHK-05, CHK-15 |

## 10. Doxygen and documentation

T035 adds no C/C++ interface, so it adds no Doxygen comment obligation; the Doxygen completion and
warning-free-generation obligation is T037. T035 documents the verification route, the report schema, and the
measure refresh in this work-product set only.

## 11. Compatibility contract and generated-code provenance

- T035 adds **no** generated code and **no** admitted dependency. It does not touch
  `proto/xverse/xcom/v1/tool_gateway.proto` or any `XCOM-XLC-002` message and links no transport runtime.
- **Compatibility contract.** T035 re-runs the accepted version/generation/capability checks and records their
  outcomes; it defines no competing interface, contract, or configuration language and promotes no REF-002
  target.
