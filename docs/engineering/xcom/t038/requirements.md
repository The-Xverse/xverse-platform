# T038 Requirements — Spec Kit and REF-002 Requirements/Design/Code/Test Traceability and Public-Safe Evidence

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T038 (capability 007, slice `T-INTG`/traceability) |
| Task title | Validate Spec Kit plus REF-002 requirements/design/code/test traceability and public-safe logs/evidence; do not promote allocated or deferred SADS targets without proof |
| Stage / role | plan → requirements |
| Revision | 1 (Phase 8 traceability slice) |
| Baseline revision | `d5b9c6399da67a0a028fae21c2f0dcc8da3619bc` |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC012`, `ACC014`, `ACC015`); `ADR-0020` (repository-owned work products and exact-candidate evidence); Constitution VI, IX, X |
| Owning slice | `T-INTG` (T007 ownership register); T038 is the traceability/evidence task of the `T-INTG` evidence family and the sole owner of the task-owned traceability verifier and its exact-candidate report |
| Predecessors | T035 accepted exact-candidate verification matrix and repository-owned results; T036 accepted controlled disabled/enabled-tap benchmark; T037 accepted complete Doxygen documentation and warning-free generated reference; T030–T034 accepted contract/gateway/client/suite/provider; T026–T029 accepted stimulation boundary; T021–T024 accepted observation boundary; T017–T020 accepted XDL activation plan; T016 accepted core matrix; T011 admitted offline toolchain and environment; T008 accepted requirements register and REF-002 dispositions; T009 accepted architecture model; T010 accepted unit design |
| Successor tasks | T039–T041 (external review, acceptance-bundle inspection, user acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}` (`T-INTG` slice, `T038` assignment); `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-SW-ENB-001`, `XCOM-SW-ENB-002`, `XCOM-SW-INTG-001`, `XCOM-SW-INTG-002`, `XCOM-SW-ENB-004`, `XCOM-SW-CORE-007`; system anchors `XCOM-SYS-FR-026/027/028/029/030/035`, `XCOM-SYS-SC-009`); `docs/engineering/xcom/t009/architecture-model.json`; `docs/engineering/xcom/t010/unit-design.json`; `specs/007-xcom-core/{spec,plan,tasks,reference-traceability}.md`; `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md`; `docs/architecture/sads-requirements-traceability.json`; `scripts/validate_xcom_requirements_traceability.py`; `engineering/trace/links.json` |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** the traceability
validation is executed and does not itself execute, accept, or integrate the candidate. The T038 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T038 — Validate Spec Kit plus REF-002 requirements/design/code/test traceability and public-safe
> logs/evidence; do not promote allocated or deferred SADS targets without proof.

It realizes the accepted delivery-phase evidence step of `specs/007-xcom-core/plan.md` (traceability and
public-safe evidence), the measurable outcome `SC-009` ("Every requirement traces to design units and automated
evidence, and public interfaces generate warning-free Doxygen output"), the accepted software anchors
`XCOM-SW-ENB-001` ("Repository-owned requirement register and bidirectional traceability"), `XCOM-SW-ENB-002`
("REF-002 disposition accounting without promotion"), the traceability-validation portion of
`XCOM-SW-INTG-002`, and the `XCOM-SW-INTG-001` public-safe-evidence obligation. It does not perform, duplicate,
or claim the T039 external review, T040 acceptance-bundle inspection, or T041 user acceptance work, and it does
not promote any allocated or deferred REF-002 SADS target.

### 1.1 Authority statement

T038 owns the **validation of the capability-007 traceability chain and of the public safety of its retained
logs/evidence**, and the **proof required before any allocated or deferred REF-002 SADS disposition is
promoted**. It provides:

- a task-owned, deterministic, offline traceability verifier (`engineering/check_xcom_traceability.py`) that
  validates the requirement → component → unit → code → test/measure → evidence → intended-use validation chain
  over the accepted `engineering/**` records and `engineering/trace/links.json`, checks the twenty REF-002
  dispositions against `specs/007-xcom-core/reference-traceability.md` and the accepted register, and enforces
  public safety over the retained evidence;
- the repository-owned evidence report `reports/xcom-queue/t038-traceability.json` carrying the required
  `requirements`, `design`, `code`, `tests`, and `evidence` results plus the resolved environment identity,
  artifact hashes, and the exact-candidate identity;
- the additive T038 trace links and the current-task pointer that connect every T038 requirement to its
  accepted anchor, component, unit, measure, and named executed case or inspection;
- the T038 engineering records and work products that trace every T038 requirement to an accepted anchor,
  component, unit, measure, and named executed case or inspection.

The `T008` requirements register allocates `XCOM-SW-ENB-001` and `XCOM-SW-ENB-002` (maturity `partial`) to
T008 and `XCOM-SW-INTG-001`/`XCOM-SW-INTG-002` to T035/T037; T038 realizes the traceability-validation and
public-safe-evidence portions of those accepted anchors. The register rows are **not** edited (T026–T037
precedent).

**Recorded design decision (`T038-DD-01`).** T038 changes **no accepted requirement, design, code, test,
target, label, command, expected value, contract, schema, register, XDL profile, or ADR**. Its source change
set is additive: the T038 work products, the T038 engineering records, the task-owned verifier, the
exact-candidate report, the additive trace links, and the current-task pointer. It adds no accepted CTest
target, no compiled symbol, no admitted dependency, and no runtime library.

**Validation/evidence-only, behavior-preserving boundary.** T038 authors the task-owned traceability verifier,
its report, and additive trace/records; it authors no change to any compiled statement, control-flow decision,
signature, type, default value, contract, schema, register, XDL profile, accepted test, or expected value.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, data
model, the T007 ownership register, the T008 register, the T009 architecture model, the T010 unit design, the
constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is reported
rather than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 Plan-stage baseline measurement (traceability and disposition inventory)

The plan stage executed read-only probes against the accepted baseline `d5b9c63…` to size the work honestly.
No verifier, report, or generated output is committed by the plan stage.

- **Registry/trace inventory.** The trusted `validate_project`/`validate_trace` route reports the accepted
  baseline at **786 inventoried artifacts and 2855 trace links**, and the accepted `engineering/trace/links.json`
  carries **139 additive `T037-L-*` links** plus the inherited `T034`/`T035`/`T036` links; fifteen
  `implemented_by` links pin `engineering/project.json`, so the plan-stage current-task pointer change requires
  those fifteen pins to be refreshed.
- **Spec Kit register.** `scripts/validate_xcom_requirements_traceability.py --verify` validates the accepted
  `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.json` (91 requirements: 8 stakeholder,
  46 system, 37 software) and reports a clean result at the baseline.
- **REF-002 dispositions.** The accepted register records all twenty IDs `XVE-SYS-0139`…`XVE-SYS-0158`: ten
  **allocated**, ten **deferred**, every one at maturity `architectural-target`; no ID is `implemented`. The
  accepted `specs/007-xcom-core/reference-traceability.md` records the same allocation/deferment table, with
  `XVE-SYS-0141`, `0143`, `0144`, `0148`, `0150`, `0151`, `0153`, `0155`, `0157`, and `0158` deferred to their
  owning capabilities.
- **Public-safety classes.** The accepted traceability validator's `--verify` public-safety scan is the
  mechanical reference for the excluded classes (`absolute host path`, `private IPv4 address`,
  `credential assignment`, `private-key marker`, `unbounded payload token`); T038 reuses that reference for the
  retained traceability evidence.
- **Successor scope.** `docs/engineering/xcom/t038/` was declared as a material path in the trusted Phase 8
  policy; the T010 unit design did **not** name it, so no planned→established path reconciliation is performed
  (see `T038-OPEN-06`).

### 2.2 In scope (bounded T038)

1. **Task-owned traceability verifier.** `engineering/check_xcom_traceability.py` validates the
   requirement → component → unit → code → test/measure → evidence → intended-use validation chain, the
   REF-002 disposition table, and public safety, and fails closed on a missing edge, a stale hash pin, an
   incomplete or promoted disposition, or an excluded-content match.
2. **Spec Kit traceability validation.** Every accepted capability-007 requirement ID used by the traceability
   chain is present and every required relation (`refines`, `allocated_to`, `decomposes_to`, `implemented_by`,
   `verified_by`, `analyzed_by`, `validates`) resolves to a declared artifact of the expected group.
3. **REF-002 disposition accounting.** All twenty IDs `XVE-SYS-0139`–`0158` carry an explicit disposition and
   owning capability consistent with `specs/007-xcom-core/reference-traceability.md`; the capability
   `ref002.disposition` stays `unchanged`.
4. **No promotion without proof.** No allocated, deferred, architectural-target, or superseded ID is recorded
   `implemented`; promotion is impossible without source and exact-candidate executed evidence.
5. **Exact-candidate evidence report.** `reports/xcom-queue/t038-traceability.json` records `requirements`,
   `design`, `code`, `tests`, and `evidence` results, the resolved environment identity, retained-evidence
   hashes, and the exact-candidate identity.
6. **Public-safe logs/evidence.** The report, logs, work products, and bounded excerpts contain no credential,
   private address, unrestricted payload, proprietary source excerpt, or host-specific absolute path.
7. **Exact-candidate binding.** Every result is bound to the accepted baseline revision and the exact candidate
   material (a sorted material-input inventory, a material digest, and per-file SHA-256 hashes).
8. **Governance honesty.** The T007–T010 models are reconciled without rewrite; the current-task pointer is
   set; T038 is recorded implemented while T039–T041 remain allocated; nothing is promoted.
9. **Traceability.** Every applied T038 requirement traces to its accepted X-COM anchor and is verified by a
   named executed command, case, or inspection.
10. **Owned/local execution.** The route uses only the admitted offline toolchain and the owned records; it
    opens no network, DNS, TLS, legacy, or production resource.
11. **No accepted change beyond additive records.** No compiled behavior, signature, type, default, contract,
    schema, register, accepted test, target, label, command, or expected value changes.
12. The T038 repository-owned work products and the T038 package record.

### 2.3 Explicit exclusions (must remain absent from the T038 candidate)

No modification of any accepted requirement, design, code, test, target, label, command, expected value,
contract, schema, register, XDL profile, or ADR; no new admitted dependency; no new runtime library or compiled
symbol; no compiled or linked gRPC runtime; no TCP listener or `AF_INET`/`AF_INET6` socket, DNS, resolver, or
TLS use; no external network peer; no legacy binary, legacy repository, or production workload execution; no
re-run or re-claim of the T035 verification matrix, the T036 benchmark, or the T037 Doxygen result; no
external review record (T039); no acceptance-bundle inspection record (T040); no user acceptance or
platform-main merge (T041); no ambient/secret access or dynamic load; no promotion of any REF-002 SADS ID
beyond its recorded disposition; no rewrite or weakening of an accepted ADR, requirement, contract, schema,
register, or test; no acceptance or integration of the candidate.

### 2.4 Delegated to other tasks (not performed or decided here)

| Area | Owner | Disposition in T038 |
| --- | --- | --- |
| Complete exact-candidate verification matrix and repository-owned results | T035 | accepted; consumed read-only, not re-run or re-claimed by T038 |
| Controlled disabled/enabled-tap benchmark and repository-owned results | T036 | accepted; consumed read-only, not re-run or re-claimed by T038 |
| Complete Doxygen comments and warning-free generated reference | T037 | accepted; consumed read-only, not re-run or re-claimed by T038 |
| Independent read-only review | T039 | allocated; deferred until the ordered backlog `xcom-t030-t034-20260928` completes |
| Acceptance-bundle assembly and inspection | T040 | allocated |
| Explicit user acceptance and platform-main delivery | T041 | allocated |

## 3. Stakeholder requirements (`T038-STK-###`)

- **T038-STK-001**: Before any capability-007 acceptance or REF-002 disposition promotion, the program
  **shall** validate, at one exact candidate revision, that every Spec Kit requirement traces bidirectionally to
  its design units, code, tests, measures, and evidence, and **shall** record the observed result.
- **T038-STK-002**: Every retained traceability result **shall** be repository-owned, bound to the accepted
  baseline revision and the exact candidate material (a sorted material-input inventory, a material digest, and
  per-file SHA-256 hashes), and **shall** identify its command, outcomes, tool/environment identity, retained
  hashes, and any blocker.
- **T038-STK-003**: Traceability evidence, logs, work products, and excerpts **shall** be public-safe and
  **shall** exclude credentials, private addresses, unrestricted payloads, proprietary source excerpts, and
  host-specific or sensitive deployment values.
- **T038-STK-004**: Each REF-002 SADS communication requirement `XVE-SYS-0139`–`XVE-SYS-0158` **shall** retain
  an explicit implemented/partial/allocated/deferred/superseded/conflicting/needs-clarification disposition,
  and no allocated, deferred, architectural-target, or superseded ID **shall** be recorded implemented without
  source and exact-candidate executed evidence.
- **T038-STK-005**: T038 **shall** preserve accepted intent and report maturity honestly: it changes no
  accepted requirement, design, code, test, register, or ADR, keeps the capability REF-002 disposition
  `unchanged` with an empty `promoted` list, and leaves T039–T041 allocated.

## 4. Software/engineering requirements (`T038-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Verified" means the named command, case, or inspection exists, is deterministic, and passes at the
recorded candidate revision; it is not a deployed-service, compatibility, performance, or production-readiness
claim.

### 4.1 Traceability chain and REF-002 disposition

- **T038-SR-001 [ubiquitous]**: The task **shall** validate that every accepted capability-007 requirement
  traces from spec → system → software → component → unit → code → test/measure → evidence → intended-use
  validation at the exact candidate revision, and that no required relation is missing or stale.
  - Refines: `T038-STK-001`; anchors `XCOM-SW-ENB-001`, `XCOM-SW-INTG-002`; `XCOM-SYS-FR-030`,
    `XCOM-SYS-SC-009`.
  - Verification intent: `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource`.
- **T038-SR-002 [ubiquitous]**: The task **shall** validate that all twenty REF-002 communication IDs
  `XVE-SYS-0139`–`XVE-SYS-0158` carry an explicit disposition and owning capability consistent with
  `specs/007-xcom-core/reference-traceability.md` and the accepted register.
  - Refines: `T038-STK-004`; anchors `XCOM-SW-ENB-002`; `XCOM-SYS-FR-035`.
  - Verification intent: `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue`.
- **T038-SR-003 [unwanted]**: T038 **shall** keep every allocated, deferred, architectural-target, or
  superseded REF-002 ID at its recorded disposition and **shall not** record any of them implemented unless
  source and exact-candidate executed evidence exist.
  - Refines: `T038-STK-004`; anchors `XCOM-SW-ENB-002`, `XCOM-SW-INTG-002`; `XCOM-SYS-FR-035`.
  - Verification intent: `XcomToolGatewayBounds.MessageSizeBoundEnforced`.

### 4.2 Evidence, exact binding, and public safety

- **T038-SR-004 [ubiquitous]**: `reports/xcom-queue/t038-traceability.json` **shall** record the
  `requirements`, `design`, `code`, `tests`, and `evidence` results, the resolved environment identity,
  retained-evidence hashes, and the exact-candidate identity, and **shall** be bound to the accepted baseline
  revision and the exact candidate material.
  - Refines: `T038-STK-002`; anchors `XCOM-SW-ENB-001`, `XCOM-SW-INTG-001`; `XCOM-SYS-FR-030`.
  - Verification intent: `T026JournalRecovery.test_journal_restart_recovery_and_orphans`.
- **T038-SR-005 [ubiquitous]**: The committed report, logs, work products, and bounded excerpts **shall**
  contain no credential, private address, unrestricted payload, proprietary source excerpt, or host-specific
  absolute path.
  - Refines: `T038-STK-003`; anchors `XCOM-SW-INTG-001`; `XCOM-SYS-FR-027`.
  - Verification intent: `T033ObserverContractSuite.AcceptedObservationHubConforms`.
- **T038-SR-006 [unwanted]**: T038 **shall** change no compiled statement, control-flow decision, signature,
  type, default value, contract, schema, register, XDL profile, accepted requirement, or test byte; every
  change **shall** be additive and **shall** preserve every accepted target, label, command, and expected
  value.
  - Refines: `T038-STK-005`; anchors `XCOM-SW-ENB-001`, `XCOM-SW-ENB-004`; `XCOM-SYS-FR-030`.
  - Verification intent: `T034SecondProviderSuite.ReusedProviderContractSuitePasses`.

### 4.3 Governance, offline honesty, and fail-closed checking

- **T038-SR-007 [ubiquitous]**: T038 **shall** reconcile with the T007 ownership register and the
  T008/T009/T010 models without rewriting or weakening them, **shall** set the current-task pointer, **shall**
  record T038 implemented while T039–T041 remain allocated, and **shall** leave the capability REF-002
  disposition `unchanged` with an empty `promoted` list.
  - Refines: `T038-STK-005`; anchors `XCOM-SW-ENB-001`, `XCOM-SW-ENB-002`; `XCOM-SYS-FR-030`,
    `XCOM-SYS-FR-035`.
  - Verification intent: `T034VersionRejection.RejectionEmitsNothing`.
- **T038-SR-008 [unwanted]**: No T038 command **shall** open a TCP listener or `AF_INET`/`AF_INET6` socket,
  use DNS, a resolver, or TLS, contact an external peer, execute a legacy binary or production workload, or add
  an admitted dependency.
  - Refines: `T038-STK-003`; anchors `XCOM-SW-CORE-007`; `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028`.
  - Verification intent: `XcomToolGatewayNegative.NoTcpOrAddressPrimitive`.
- **T038-SR-009 [event-driven]**: When the task-owned verifier detects a missing requirement/design/code/
  test/evidence edge, a stale hash pin, an incomplete or promoted disposition, or a public-safety violation,
  it **shall** exit nonzero and record the failure class; it **shall** exit zero only for a complete, passing
  candidate.
  - Refines: `T038-STK-001`; anchors `XCOM-SW-ENB-001`, `XCOM-SW-INTG-002`; `XCOM-SYS-FR-030`,
    `XCOM-SYS-SC-009`.
  - Verification intent: `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch`.
- **T038-SR-010 [ubiquitous]**: The task **shall** provide `engineering/check_xcom_traceability.py --verify`
  as the task-owned route exercised by the trusted Phase 8 T038 validation measure and **shall** preserve every
  accepted target, label, command, test, and expected value.
  - Refines: `T038-STK-002`; anchors `XCOM-SW-INTG-002`, `XCOM-SW-ENB-001`; `XCOM-SYS-FR-030`.
  - Verification intent: `T033ProviderContractSuite.AcceptedLoopbackProviderConforms`.

## 5. Requirement-to-accepted-anchor traceability

| T038 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T038-STK-001 | `XCOM-SW-ENB-001` | `XCOM-SYS-FR-030` | FR-030 | IX, X |
| T038-STK-002 | `XCOM-SW-ENB-001`, `XCOM-SW-INTG-001` | `XCOM-SYS-SC-009` | SC-009 | X |
| T038-STK-003 | `XCOM-SW-INTG-001` | `XCOM-SYS-FR-027` | FR-027 | VII, X |
| T038-STK-004 | `XCOM-SW-ENB-002` | `XCOM-SYS-FR-035` | FR-035 | IX, X |
| T038-STK-005 | `XCOM-SW-ENB-001/002` | `XCOM-SYS-FR-030/035` | FR-030, FR-035 | VII, IX, X |
| T038-SR-001 | `XCOM-SW-ENB-001`, `XCOM-SW-INTG-002` | `XCOM-SYS-FR-030`, `XCOM-SYS-SC-009` | FR-030, SC-009 | IX, X |
| T038-SR-002 | `XCOM-SW-ENB-002` | `XCOM-SYS-FR-035` | FR-035 | IX, X |
| T038-SR-003 | `XCOM-SW-ENB-002`, `XCOM-SW-INTG-002` | `XCOM-SYS-FR-035` | FR-035 | IX, X |
| T038-SR-004 | `XCOM-SW-ENB-001`, `XCOM-SW-INTG-001` | `XCOM-SYS-FR-030` | FR-030, SC-009 | IX, X |
| T038-SR-005 | `XCOM-SW-INTG-001` | `XCOM-SYS-FR-027` | FR-027 | VII, X |
| T038-SR-006 | `XCOM-SW-ENB-001`, `XCOM-SW-ENB-004` | `XCOM-SYS-FR-030` | FR-030 | VI, X |
| T038-SR-007 | `XCOM-SW-ENB-001/002` | `XCOM-SYS-FR-030/035` | FR-030, FR-035 | VII, IX, X |
| T038-SR-008 | `XCOM-SW-CORE-007` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | VII, IX |
| T038-SR-009 | `XCOM-SW-ENB-001`, `XCOM-SW-INTG-002` | `XCOM-SYS-FR-030`, `XCOM-SYS-SC-009` | FR-030, SC-009 | IX, X |
| T038-SR-010 | `XCOM-SW-INTG-002`, `XCOM-SW-ENB-001` | `XCOM-SYS-FR-030` | FR-030 | X |

Each accepted T038 software requirement refines at least one `T038-STK-###` stakeholder requirement through an
explicit `refines` link in `engineering/trace/links.json`. `T038-VS-ACCUMULATED` validates `T038-SR-001`…`-010`
and names the executed traceability route and inherited matrix cases that the trusted measures select.

## 6. REF-002 disposition

T038 promotes no REF-002 SADS ID. It validates the accepted dispositions and records that **all twenty**
communication IDs remain at `architectural-target`: ten **allocated**, ten **deferred**, and **none
implemented**. `XVE-SYS-0141` remains deferred to protocol/provider capabilities; `XVE-SYS-0143`/`0157` remain
deferred to registry/reconfiguration; `XVE-SYS-0144`/`0153`/`0155` remain deferred to Security/deployment;
`XVE-SYS-0148`/`0150`/`0151` remain deferred to record/replay, edge/cloud, and Argus adapters; the automatic
recovery portion of `XVE-SYS-0158` remains deferred to Faults/Runtime. The capability `ref002.disposition`
stays `unchanged` with an empty `promoted` list (T038-SR-003, T038-SR-007). No allocated, deferred,
architectural-target, or superseded SADS requirement is reported as implemented.

## 7. Affected paths

### 7.1 Paths the T038 candidate changes

| Path | Change | Notes |
| --- | --- | --- |
| `docs/engineering/xcom/t038/{requirements,architecture,detailed-design,unit-specifications,verification-plan}.md` | add (plan stage) | this work-product set |
| `docs/engineering/xcom/t038/{implementation.md,internal-review.json}` | add (implementation/review stages) | not produced by the plan stage |
| `engineering/project.json` | edit (plan stage) | current task T038 and accepted baseline `d5b9c6399da67a0a028fae21c2f0dcc8da3619bc` |
| `engineering/requirements/T038-STK-00{1..5}.json`, `T038-SR-0{01..10}.json` | add (plan stage) | current-task requirement records |
| `engineering/architecture/components/T038-SR-0{01..10}-CMP.json` | add (plan stage) | current-task component allocations |
| `engineering/unit-specifications/T038-SR-0{01..10}-U.json` | add (plan stage) | current-task unit specifications |
| `engineering/validation/scenarios/T038-VS-ACCUMULATED.json` | add (plan stage) | current-task validation scenario |
| `engineering/trace/links.json` | edit (plan stage; refreshed at implementation) | additive T038 trace links and the refreshed `engineering/project.json` pins |
| `reports/review-index.md` | edit (plan stage) | T038 plan-stage candidate section appended |
| `engineering/check_xcom_traceability.py` | add (implementation stage) | the task-owned fail-closed traceability verifier |
| `reports/xcom-queue/t038-traceability.json` | add (implementation stage) | the exact-candidate evidence report (`requirements`, `design`, `code`, `tests`, `evidence`) |
| `specs/007-xcom-core/tasks.md` | edit (implementation stage only) | one-line T038 checkbox |
| `reports/xcom-queue/t038-package.json` | add (implementation stage) | package record |

### 7.2 Consumed read-only (not changed by T038)

The accepted `engineering/requirements/T038`-predecessor records and the accepted `engineering/trace/links.json`
inherited links are consumed; `engineering/verification/measures/**`; `docs/engineering/xcom/task-ownership.*`;
`docs/engineering/xcom/t00{7,8,9}/**` and `docs/engineering/xcom/t010/**`; `docs/engineering/xcom/t0{11..37}/**`;
`docs/engineering/xcom/{build-environment,dependency-lock}.md`; `specs/007-xcom-core/**` other than the T038
checkbox; and the accepted core/gateway/observation/stimulation sources and tests.

### 7.3 Explicitly not implemented by T038

The T035 verification matrix, the T036 benchmark, and the T037 Doxygen result (accepted; consumed read-only);
the T039 external review, the T040 acceptance-bundle inspection, and the T041 user acceptance; the
whole-system target-repository integration measure; and any change to compiled behavior, an accepted
requirement, test, target, label, command, or expected value. External Codex review and user acceptance remain
T039/T041 and are deferred until the ordered backlog `xcom-t030-t034-20260928` completes.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- **T038-GAP-01 — validation only.** T038 records traceability and public-safety validation; it makes no
  compiled-behavior, deployed-service, compatibility, or production-readiness claim, and it promotes no REF-002
  target.
- **T038-GAP-02 — read-only register.** The T008 register and matrix are validated read-only. Their `partial`
  maturity for `XCOM-SW-ENB-001`/`002` and the `allocated` maturity of `XCOM-SW-INTG-001`/`002` are recorded
  honestly and not rewritten by T038.
- **T038-GAP-03 — mechanical vs judged public safety.** The task-owned verifier enforces the mechanically
  decidable excluded-content classes; the classes that are not mechanically decidable remain a review-stage
  judgement (T039).
- **T038-GAP-04 — no successor claim.** External review (T039), acceptance-bundle inspection (T040), and user
  acceptance (T041) remain allocated.
- **T038-GAP-05 — inherited dispositions.** The register's ten allocated and ten deferred REF-002 dispositions
  are validated as-is; T038 neither completes nor promotes any of them.

### 8.2 Gaps with owning tasks

| Gap | Owner |
| --- | --- |
| External independent review and user acceptance | T039/T041 |
| Acceptance-bundle assembly and inspection | T040 |
| Whole-system target-repository integration | trusted delivery measure (T041) |
| REF-002 promotion (only after source + exact-candidate proof) | no current owner; remains allocated/deferred |

### 8.3 Open items

- **T038-OPEN-01 — verifier and report are implementation-stage.** `engineering/check_xcom_traceability.py`
  and `reports/xcom-queue/t038-traceability.json` are produced only at the implementation stage from executed
  validation; the plan stage records the required schema, the route, and the accepted 786-artifact/2855-link
  baseline rather than fabricating results.
- **T038-OPEN-02 — trace digest refresh.** T038 edits `engineering/project.json`, so the implementation stage
  **must** refresh the fifteen `implemented_by` pins in `engineering/trace/links.json` that target it, and any
  further edited-artifact pins, so that no stale hash remains.
- **T038-OPEN-03 — unavailable inputs are blockers.** If the accepted records, the register, the reference
  traceability register, or the Python runtime is unavailable at the candidate revision, the affected check is
  recorded as `blocked` (with the reason) and the candidate does not claim a pass; the plan does not substitute
  inferred or stale output.
- **T038-OPEN-04 — no promotion.** T038 records that nothing is promoted; if a future capability promotes an
  allocated ID, that requires its own source and exact-candidate evidence and is out of T038 scope.
- **T038-OPEN-05 — traceability verifier does not replace the T008 validator.** T038 reuses the accepted
  `scripts/validate_xcom_requirements_traceability.py` semantics as a reference but does not modify or weaken
  it; the task-owned verifier adds the candidate-binding, chain-completeness, and REF-002 disposition checks the
  trusted T038 validation measure invokes.
- **T038-OPEN-06 — no T010 path-status reconciliation required.** `docs/engineering/xcom/t038/` was not
  declared as a planned artifact path in the T010 unit design, so no planned→established path-status
  reconciliation is performed. If a reviewer requires the directory to be modeled, that is a T010/T008 register
  action, not a T038 change.

## 9. Definition of done (requirements view)

T038 is done for a candidate revision when: every §4 requirement has at least one named executed command, case,
or inspection; the task-owned verifier validates the complete requirement → component → unit → code →
test/measure → evidence → validation chain with no missing or stale edge; all twenty REF-002 IDs retain an
explicit disposition and none is promoted; `reports/xcom-queue/t038-traceability.json` carries the required
`requirements`, `design`, `code`, `tests`, and `evidence` results plus the environment identity, hashes, and
the exact-candidate identity; no accepted requirement, design, code, test, register, or ADR changes; every
retained artifact is public-safe; the accepted registers are reconciled with the REF-002 disposition
`unchanged` and nothing promoted; the deterministic Phase 8 gate passes; and a separate DeepSeek internal
review records its findings before any repair. This does not constitute user acceptance, which remains T041.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary checks |
| --- | --- |
| T038-STK-001 | CHK-01, CHK-02 |
| T038-STK-002 | CHK-03, CHK-04 |
| T038-STK-003 | CHK-05, CHK-06 |
| T038-STK-004 | CHK-02, CHK-07 |
| T038-STK-005 | CHK-08, CHK-09 |
| T038-SR-001 | CHK-01, CHK-09 |
| T038-SR-002 | CHK-02 |
| T038-SR-003 | CHK-07 |
| T038-SR-004 | CHK-03, CHK-04 |
| T038-SR-005 | CHK-05 |
| T038-SR-006 | CHK-08 |
| T038-SR-007 | CHK-09, CHK-10 |
| T038-SR-008 | CHK-06 |
| T038-SR-009 | CHK-11 |
| T038-SR-010 | CHK-12, CHK-13 |
