# T037 Unit Specifications — Complete Doxygen Comments and Warning-Free Generated Reference Documentation

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T037 (capability 007, slice `T-INTG`/documentation) |
| Stage / role | plan → unit specifications |
| Revision | 1 (Phase 8 Doxygen-completion slice) |
| Baseline revision | `8757a79d4e6b2630124d774fcba2a55d6342a879` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit framework | the admitted offline C++20 build, CTest, the accepted contract/negative/concurrency suites, and the Python documentation checker; evidence units are the repository-owned Doxygen configuration, checker, and report |
| Classification | Public-safe engineering work product |

T037 adds no accepted production unit and no compiled symbol. Each requirement `T037-SR-###` owns one
verification unit specification `T037-SR-###-U` whose cases are **contributory** already-discovered cases of
the accepted suites (the exact IDs selected by the trusted unit measure) and the task-owned Doxygen route.
"Verified" means the named case, command, or inspection exists, is deterministic, and passes at the recorded
candidate revision; it is not a deployed-service, compatibility, or production-readiness claim.

## 2. Unit inventory

| Unit | Component | Source of truth | Kind | Cases |
| --- | --- | --- | --- | --- |
| `T037-SR-001-U` | `T037-SR-001-CMP` | `src/xverse/xcom/**` Doxygen comments | complete owned public documentation | `T033ObserverContractSuite.AcceptedObservationHubConforms` |
| `T037-SR-002-U` | `T037-SR-002-CMP` | `Doxyfile` + `scripts/check_doxygen.py` | strict C++ zero-warning reference | `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` |
| `T037-SR-003-U` | `T037-SR-003-CMP` | `Doxyfile` | warning-free repository route | `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue` |
| `T037-SR-004-U` | `T037-SR-004-CMP` | `scripts/check_doxygen.py` | warning-free HTML/XML generation | `T033GatewayContractSuite.AcceptedGatewaySessionConforms` |
| `T037-SR-005-U` | `T037-SR-005-CMP` | `reports/xcom-queue/t037-doxygen.json` | exact-candidate documentation evidence | `XcomToolGatewayBounds.MessageSizeBoundEnforced` |
| `T037-SR-006-U` | `T037-SR-006-CMP` | `engineering/project.json` | behavior-preservation | `T034SecondProviderSuite.ReusedProviderContractSuitePasses` |
| `T037-SR-007-U` | `T037-SR-007-CMP` | `docs/engineering/xcom/t037/requirements.md` | public-safe evidence | `XcomToolGatewayNegative.NoTcpOrAddressPrimitive` |
| `T037-SR-008-U` | `T037-SR-008-CMP` | `docs/engineering/xcom/t037/architecture.md` | offline/no-legacy, no new dependency | `T034VersionRejection.RejectionEmitsNothing` |
| `T037-SR-009-U` | `T037-SR-009-CMP` | `engineering/trace/links.json` | governance and trace reconciliation | `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource` |
| `T037-SR-010-U` | `T037-SR-010-CMP` | `scripts/check_doxygen.py` | fail-closed documentation gate | `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch` |

## 3. Unit specifications

### T037-SR-001-U — Complete owned public documentation

- **Inputs:** the owned `src/xverse/xcom` C++ headers, sources, and fixtures; the T010 `doxygen_plan` tags.
- **Outputs:** the completed file blocks and declaration comments with the mandatory contract clauses.
- **Invariants:** every public declaration carries `@brief` and the applicable params/returns and
  ownership/lifetime/thread-safety/failure clauses; every owned file carries the mandatory file block.
- **Cases (contributory, already discovered):** `T033ObserverContractSuite.AcceptedObservationHubConforms`.
- **Static checks:** the admitted-offline dependency preflight.

### T037-SR-002-U — Strict C++ zero-warning reference

- **Inputs:** the owned C++ inputs; the strict scope and exclusion list.
- **Outputs:** the strict C++ warning count and coverage-gap count.
- **Invariants:** `EXTRACT_ALL = NO`, public declarations only, strict warnings, `WARN_AS_ERROR = YES`; zero
  warnings and zero coverage gaps.
- **Cases (contributory):** `T033ProviderContractSuite.AcceptedLoopbackProviderConforms`.

### T037-SR-003-U — Warning-free repository route

- **Inputs:** the admitted repository inputs and the `Doxyfile` alias set.
- **Outputs:** the repository-route exit status and warning log.
- **Invariants:** every command used by the admitted inputs is defined; the route is warning-free under
  `WARN_AS_ERROR = YES`.
- **Cases (contributory):** `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue`.

### T037-SR-004-U — Warning-free generated reference

- **Inputs:** the admitted inputs and the Doxygen executable identity.
- **Outputs:** the generated HTML/XML indexes and the indexed-file count.
- **Invariants:** generation is warning-free; the output lives under `build/`; only identities/hashes are
  retained.
- **Cases (contributory):** `T033GatewayContractSuite.AcceptedGatewaySessionConforms`.

### T037-SR-005-U — Exact-candidate documentation evidence

- **Inputs:** the accepted baseline revision, the candidate material inventory/digest, and the report
  contents.
- **Outputs:** `reports/xcom-queue/t037-doxygen.json` with `command`, `warnings`, `output`, environment,
  hashes, and the candidate identity.
- **Invariants:** the candidate commit is the direct child of the baseline carrying the recorded material; a
  missing required field or a stale/foreign binding fails the checker.
- **Cases (contributory):** `XcomToolGatewayBounds.MessageSizeBoundEnforced`.

### T037-SR-006-U — Behavior preservation

- **Inputs:** the baseline-versus-candidate diff over the owned sources.
- **Outputs:** the comment-only diff verdict and the preserved discovered inventory.
- **Invariants:** no compiled token, signature, type, default, test, target, label, command, or expected value
  changes.
- **Cases (contributory):** `T034SecondProviderSuite.ReusedProviderContractSuitePasses`.

### T037-SR-007-U — Public-safe evidence

- **Inputs:** the committed report, logs, work products, and excerpts.
- **Outputs:** the public-safety verdict.
- **Invariants:** no credential, private address, payload, proprietary excerpt, or host-specific path.
- **Cases (contributory):** `XcomToolGatewayNegative.NoTcpOrAddressPrimitive`.

### T037-SR-008-U — Offline, no-legacy, no new dependency

- **Inputs:** the executed command set and the committed artifacts.
- **Outputs:** the forbidden-resource and dependency verdict.
- **Invariants:** no TCP listener, `AF_INET`/`AF_INET6` socket, DNS, resolver, TLS, external peer, legacy
  binary, production workload, or added dependency.
- **Cases (contributory):** `T034VersionRejection.RejectionEmitsNothing`.

### T037-SR-009-U — Governance and trace reconciliation

- **Inputs:** the T007–T010 models, the accepted registers, and the candidate trace.
- **Outputs:** the validator verdict, recorded maturity, and trace verdict.
- **Invariants:** registers unchanged in substance; REF-002 `unchanged` with an empty `promoted` list; the
  required trace edges present; no stale hash pin after the implementation refresh.
- **Cases (contributory):** `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource`.

### T037-SR-010-U — Fail-closed documentation gate

- **Inputs:** the checker checks and the generated output.
- **Outputs:** the checker exit status.
- **Invariants:** an undocumented declaration, a missing mandatory tag, or any warning yields a nonzero exit.
- **Cases (contributory):**
  `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch`.

## 4. Case index

| Case | Category | Primary requirement |
| --- | --- | --- |
| `T033ObserverContractSuite.AcceptedObservationHubConforms` | observer contract | T037-SR-001 |
| `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` | provider contract | T037-SR-002 |
| `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue` | XDL plan determinism | T037-SR-003 |
| `T033GatewayContractSuite.AcceptedGatewaySessionConforms` | gateway contract | T037-SR-004 |
| `XcomToolGatewayBounds.MessageSizeBoundEnforced` | bounds | T037-SR-005 |
| `T034SecondProviderSuite.ReusedProviderContractSuitePasses` | replaceability | T037-SR-006 |
| `XcomToolGatewayNegative.NoTcpOrAddressPrimitive` | negative/resource | T037-SR-007 |
| `T034VersionRejection.RejectionEmitsNothing` | version rejection | T037-SR-008 |
| `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource` | recovery | T037-SR-009 |
| `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch` | negative | T037-SR-010 |

## 5. Coverage

Every `T037-SR-###` requirement is covered by at least one contributory discovered case and the task-owned
Doxygen route; every case belongs to one listed requirement and appears in the T037 selected case set. Unit
cases are contributory; the Doxygen configuration, checker, and report are the evidence, and the exact
acceptance decision remains T039/T041.
