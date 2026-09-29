# T038 Unit Specifications — Spec Kit and REF-002 Requirements/Design/Code/Test Traceability and Public-Safe Evidence

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T038 (capability 007, slice `T-INTG`/traceability) |
| Stage / role | plan → unit specifications |
| Revision | 1 (Phase 8 traceability slice) |
| Baseline revision | `d5b9c6399da67a0a028fae21c2f0dcc8da3619bc` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit framework | the admitted offline C++20 build, CTest, the accepted contract/negative/concurrency suites, and the Python traceability verifier; evidence units are the repository-owned task-owned verifier and report |
| Classification | Public-safe engineering work product |

T038 adds no accepted production unit and no compiled symbol. Each requirement `T038-SR-###` owns one
verification unit specification `T038-SR-###-U` whose cases are **contributory** already-discovered cases of
the accepted suites (the exact IDs selected by the trusted unit measure) and the task-owned traceability route.
"Verified" means the named case, command, or inspection exists, is deterministic, and passes at the recorded
candidate revision; it is not a deployed-service, compatibility, or production-readiness claim.

## 2. Unit inventory

| Unit | Component | Source of truth | Kind | Cases |
| --- | --- | --- | --- | --- |
| `T038-SR-001-U` | `T038-SR-001-CMP` | `engineering/check_xcom_traceability.py` + `engineering/trace/links.json` | complete chain validation | `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource` |
| `T038-SR-002-U` | `T038-SR-002-CMP` | `docs/engineering/xcom/t008/requirements-register.json` | REF-002 disposition accounting | `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue` |
| `T038-SR-003-U` | `T038-SR-003-CMP` | `specs/007-xcom-core/reference-traceability.md` | no promotion without proof | `XcomToolGatewayBounds.MessageSizeBoundEnforced` |
| `T038-SR-004-U` | `T038-SR-004-CMP` | `reports/xcom-queue/t038-traceability.json` | exact-candidate evidence | `T026JournalRecovery.test_journal_restart_recovery_and_orphans` |
| `T038-SR-005-U` | `T038-SR-005-CMP` | `docs/engineering/xcom/t038/architecture.md` | public-safe evidence | `T033ObserverContractSuite.AcceptedObservationHubConforms` |
| `T038-SR-006-U` | `T038-SR-006-CMP` | `engineering/project.json` | behavior preservation | `T034SecondProviderSuite.ReusedProviderContractSuitePasses` |
| `T038-SR-007-U` | `T038-SR-007-CMP` | `engineering/trace/links.json` | governance and maturity reconciliation | `T034VersionRejection.RejectionEmitsNothing` |
| `T038-SR-008-U` | `T038-SR-008-CMP` | `docs/engineering/xcom/t038/detailed-design.md` | offline/no-legacy, no new dependency | `XcomToolGatewayNegative.NoTcpOrAddressPrimitive` |
| `T038-SR-009-U` | `T038-SR-009-CMP` | `engineering/check_xcom_traceability.py` | fail-closed traceability gate | `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch` |
| `T038-SR-010-U` | `T038-SR-010-CMP` | `docs/engineering/xcom/t038/verification-plan.md` | task-owned route and preserved suites | `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` |

## 3. Unit specifications

### T038-SR-001-U — Complete chain validation

- **Inputs:** the accepted `engineering/requirements/**`, `architecture/components/**`,
  `unit-specifications/**`, `verification/measures/**`, `validation/scenarios/**`, `engineering/trace/links.json`,
  and the owned code/test artifacts.
- **Outputs:** the resolved/unresolved edge counts and the chain verdict.
- **Invariants:** every `refines`/`allocated_to`/`decomposes_to`/`implemented_by`/`verified_by`/`analyzed_by`/
  `validates` edge resolves to a declared artifact of the expected group; no edge is missing or stale.
- **Cases (contributory, already discovered):**
  `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource`.
- **Static checks:** the admitted-offline dependency preflight.

### T038-SR-002-U — REF-002 disposition accounting

- **Inputs:** `specs/007-xcom-core/reference-traceability.md`, the T008 register/matrix, and the task-owned
  verifier's disposition table.
- **Outputs:** the twenty-disposition verdict and the capability disposition.
- **Invariants:** all twenty IDs `XVE-SYS-0139`–`0158` carry an explicit disposition and owning capability;
  the capability disposition is `unchanged`.
- **Cases (contributory):** `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue`.

### T038-SR-003-U — No promotion without proof

- **Inputs:** the accepted dispositions and the candidate source/test/evidence inventory.
- **Outputs:** the promoted-list verdict.
- **Invariants:** no allocated, deferred, architectural-target, or superseded ID is recorded implemented; the
  `promoted` list is empty.
- **Cases (contributory):** `XcomToolGatewayBounds.MessageSizeBoundEnforced`.

### T038-SR-004-U — Exact-candidate evidence

- **Inputs:** the accepted baseline revision, the candidate material inventory/digest, and the report contents.
- **Outputs:** `reports/xcom-queue/t038-traceability.json` with `requirements`, `design`, `code`, `tests`,
  `evidence`, environment, hashes, and the candidate identity.
- **Invariants:** the candidate commit is the direct child of the baseline carrying the recorded material; a
  missing required field or a stale/foreign binding fails the verifier.
- **Cases (contributory):** `T026JournalRecovery.test_journal_restart_recovery_and_orphans`.

### T038-SR-005-U — Public-safe evidence

- **Inputs:** the committed report, logs, work products, and excerpts.
- **Outputs:** the public-safety verdict.
- **Invariants:** no credential, private address, payload, proprietary excerpt, or host-specific path; the five
  mechanically decidable excluded-content classes are clean.
- **Cases (contributory):** `T033ObserverContractSuite.AcceptedObservationHubConforms`.

### T038-SR-006-U — Behavior preservation

- **Inputs:** the baseline-versus-candidate diff over the accepted artifacts.
- **Outputs:** the additive-only diff verdict and the preserved discovered inventory.
- **Invariants:** no accepted requirement, compiled token, signature, type, default, test, target, label,
  command, expected value, contract, schema, register, or ADR changes.
- **Cases (contributory):** `T034SecondProviderSuite.ReusedProviderContractSuitePasses`.

### T038-SR-007-U — Governance and maturity reconciliation

- **Inputs:** the T007–T010 models, the accepted registers, and the candidate trace.
- **Outputs:** the reconciled maturity and trace verdict.
- **Invariants:** registers unchanged in substance; the current-task pointer set; T038 recorded implemented and
  T039–T041 allocated; REF-002 `unchanged` with an empty `promoted` list; no stale hash pin after the refresh.
- **Cases (contributory):** `T034VersionRejection.RejectionEmitsNothing`.

### T038-SR-008-U — Offline, no-legacy, no new dependency

- **Inputs:** the executed command set and the committed artifacts.
- **Outputs:** the forbidden-resource and dependency verdict.
- **Invariants:** no TCP listener, `AF_INET`/`AF_INET6` socket, DNS, resolver, TLS, external peer, legacy
  binary, production workload, or added dependency.
- **Cases (contributory):** `XcomToolGatewayNegative.NoTcpOrAddressPrimitive`.

### T038-SR-009-U — Fail-closed traceability gate

- **Inputs:** the verifier checks and the retained evidence.
- **Outputs:** the verifier exit status.
- **Invariants:** a missing edge, a stale pin, a promoted or incomplete disposition, or an excluded-content
  match yields a nonzero exit.
- **Cases (contributory):**
  `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch`.

### T038-SR-010-U — Task-owned route and preserved suites

- **Inputs:** the task-owned verifier route and the accepted measure set.
- **Outputs:** the route exit status and the preserved discovered inventory.
- **Invariants:** the trusted T038 validation measure invokes B-1; every accepted target, label, command, test,
  and expected value is preserved.
- **Cases (contributory):** `T033ProviderContractSuite.AcceptedLoopbackProviderConforms`.

## 4. Case index

| Case | Category | Primary requirement |
| --- | --- | --- |
| `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource` | recovery | T038-SR-001 |
| `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue` | XDL plan determinism | T038-SR-002 |
| `XcomToolGatewayBounds.MessageSizeBoundEnforced` | bounds | T038-SR-003 |
| `T026JournalRecovery.test_journal_restart_recovery_and_orphans` | journal recovery | T038-SR-004 |
| `T033ObserverContractSuite.AcceptedObservationHubConforms` | observer contract | T038-SR-005 |
| `T034SecondProviderSuite.ReusedProviderContractSuitePasses` | replaceability | T038-SR-006 |
| `T034VersionRejection.RejectionEmitsNothing` | version rejection | T038-SR-007 |
| `XcomToolGatewayNegative.NoTcpOrAddressPrimitive` | negative/resource | T038-SR-008 |
| `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch` | negative | T038-SR-009 |
| `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` | provider contract | T038-SR-010 |

## 5. Coverage

Every `T038-SR-###` requirement is covered by at least one contributory discovered case and the task-owned
traceability route; every case belongs to one listed requirement and appears in the T038 selected case set.
Unit cases are contributory; the task-owned verifier and report are the evidence, and the exact acceptance
decision remains T039/T041.
