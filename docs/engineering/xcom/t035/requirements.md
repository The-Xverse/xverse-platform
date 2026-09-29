# T035 Requirements — Exact-Candidate Verification Matrix and Repository-Owned Results

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T035 (capability 007, slice `T-INTG`/evidence) |
| Task title | Run full C++ unit/contract/integration/negative/concurrency/sanitizer/static checks and all existing Python tests; retain repository-owned manifests, bounded logs, tool/environment identity, commands, outcomes, and hashes bound to the exact candidate revision |
| Stage / role | plan → requirements |
| Revision | 1 (Phase 8 exact-candidate verification slice) |
| Baseline revision | `dab68568bd8d189b14c7a4a9e3a9c325085a7529` |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC012`, `ACC014`, `ACC015`); `ADR-0020` (repository-owned work products and exact-candidate evidence); Constitution VII, IX, X |
| Owning slice | `T-INTG` (T007 ownership register); T035 is the first task of the `T-INTG` evidence family |
| Predecessors | T034 accepted second minimal synthetic provider (`src/xverse/xcom/fixtures/synthetic_provider.{hpp,cpp}`); T030–T033 accepted contract/gateway/client/reusable-suite tasks; T026–T029 accepted stimulation boundary; T021–T024 accepted observation boundary; T017–T020 accepted XDL activation plan; T016 accepted core matrix; T011 admitted offline envelope; T012 subtree build/CTest contract |
| Successor tasks | T036–T041 (benchmark, Doxygen, traceability, review, acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}` (`T-INTG` slice); `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-STK-007`, `XCOM-SW-ENB-001`, `XCOM-SW-ENB-004`, `XCOM-SW-INTG-001`); `docs/engineering/xcom/t009/architecture-model.json`; `docs/engineering/xcom/t010/unit-design.json`; `docs/engineering/xcom/build-environment.md` (evidence contract) |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any executed
evidence is produced and does not itself execute, accept, or integrate the candidate. The T035 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T035 — Run full C++ unit/contract/integration/negative/concurrency/sanitizer/static checks and all existing
> Python tests; retain repository-owned manifests, bounded logs, tool/environment identity, commands, outcomes,
> and hashes bound to the exact candidate revision.

It realizes the accepted delivery-phase step 9 of `specs/007-xcom-core/plan.md` ("Run unit, contract,
integration, negative, concurrency/sanitizer, performance, Doxygen, public-safety, traceability, and
existing-regression checks"), the `XCOM-SW-ENB-001` bidirectional-traceability obligation, the
`XCOM-SW-ENB-004` pinned/admitted reproducible-build-environment obligation, the `XCOM-SW-INTG-001`
public-safe-evidence obligation, the `XCOM-STK-007` public-safe reproducible traced delivery statement, and the
`XCOM-SYS-FR-030` requirement/evidence obligation. It does not perform, duplicate, or claim the T036
benchmark, T037 Doxygen, T038 traceability-verifier/SADS-disposition, T039 external review, T040
acceptance-bundle inspection, or T041 user acceptance work.

### 1.1 Authority statement

T035 owns the **complete exact-candidate verification matrix and its repository-owned results**. It provides:

- the executed C++ unit/contract/integration/negative/concurrency/sanitizer checks, the `cppcheck`
  static-analysis measure, the inherited Phase 6 conformance recheck, the whole-system target-repository
  integration measure, and all existing Python tests, each recorded with its command argv, exit status, and
  deterministic outcome;
- the repository-owned evidence report `reports/xcom-queue/t035-verification.json` carrying `commands`,
  `outcomes`, `hashes`, `environment`, bounded logs, and the exact-candidate identity;
- the T035 engineering records and work products that trace every T035 requirement to an accepted anchor,
  component, unit, measure, and named executed case or inspection.

The `T008` requirements register allocates no software requirement exclusively to T035 by name; T035 therefore
realizes its per-task projection of the accepted delivery/evidence software requirements and records
`XCOM-SW-ENB-001`, `XCOM-SW-ENB-004`, and `XCOM-SW-INTG-001` — the register row whose `owning_task` is T035 —
as the accepted anchors it contributes to. The register rows are not edited (T026–T034 precedent).

**Recorded design decision (`T035-DD-01`).** T035 adds **no new production source, no new test, and no new
build target**. It executes and records the already-accepted matrix. Its "code" artifacts are the
repository-owned evidence and work products, so the trace's `implemented_by` edges point at those artifacts,
and the executed cases are named by the accepted suites' existing discovered test IDs.

**Evidence-only, additive boundary.** T035 authors one evidence report, one work-product set, one engineering
record set, additive trace links, and the Phase 8 verification-measure descriptors. It authors no change to any
accepted production source, header, contract, schema, register, XDL profile, T030 contract, T031 gateway, T032
client, T033/T034 suite, or any other accepted test, target, label, command, or expected value.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, data model,
the T007 ownership register, the T008 register, the T009 architecture model, the T010 unit design, the
constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is reported rather
than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T035)

1. **Complete C++ matrix.** Build and run the full discovered CTest suite of the accepted capability-007
   platform — unit, contract, integration, negative, recovery, and concurrency cases — at the exact candidate
   revision, and record the discovered and passed counts.
2. **Preserved inherited behavior.** The T016/T020/T026–T034 suites and their exact accepted behavior are
   preserved; no existing target, test name, label, command, or expected value changes and no discovered count
   is reduced.
3. **Negative-case matrix.** The accepted malformed, incompatible, over-capacity, and unauthorized negative
   cases execute and pass.
4. **Concurrency and determinism matrix.** The accepted deterministic-concurrency cases execute and pass.
5. **Sanitizer matrix.** A separate AddressSanitizer/UndefinedBehaviorSanitizer build of the platform runs the
   full suite; the outcome is recorded (or recorded as an explicit failure/blocker, never as pass).
6. **Static analysis.** The `cppcheck` static-analysis measure over `src/xverse/xcom/src` executes and records
   its exit status and outcome.
7. **Python suite.** All existing Python tests execute; the collected/passed count and outcome are recorded.
8. **Whole-system integration.** The trusted target-repository integration measure assembles the pinned
   platform and runs the whole system; its outcome is recorded.
9. **Inherited conformance.** The Phase 6 conformance recheck (T026–T029) executes against the exact candidate;
   its outcome is recorded.
10. **Repository-owned report.** `reports/xcom-queue/t035-verification.json` exists and carries `commands`,
    `outcomes`, `hashes`, `environment`, bounded logs, and the exact-candidate identity.
11. **Honest outcomes.** Every command carries its argv and exit status; an outcome is `pass` only when the
    trusted discovery check is satisfied, and a missing, stale, mismatched, skipped, or failed measure is
    recorded as `failed` or `blocked`.
12. **Environment identity.** Compiler, CMake, Ninja, `cppcheck`, Python, and the admitted offline toolchain,
    package-manifest, and GTest-prefix identities and hashes are recorded; host-specific absolute paths are
    excluded from the public evidence.
13. **Public safety.** No payload byte, permit content, secret, private address, host path, or proprietary
    source excerpt appears in any committed T035 artifact, report, or bounded log.
14. **No accepted change.** No accepted production source, header, contract, schema, register, XDL profile, or
    test changes; any build-wiring touch is additive.
15. **Governance honesty.** The T007 ownership register, T008 register, T009 architecture model, and T010 unit
    design are reconciled without rewriting or weakening them; the REF-002 disposition stays `unchanged` with an
    empty `promoted` list; T035 is recorded implemented while T036–T041 remain allocated.
16. The T035 repository-owned work products and the T035 package record.

### 2.2 Explicit exclusions (must remain absent from the T035 candidate)

No modification of any accepted production source, header, contract, schema, register, XDL profile, accepted
test, target, label, command, or expected value; no new admitted dependency; no new runtime library; no compiled
or linked gRPC runtime; no TCP listener or `AF_INET`/`AF_INET6` socket, DNS, resolver, or TLS use; no external
network peer; no legacy binary, legacy repository, or production workload execution; no benchmark result
(T036); no Doxygen source-comment or generated-documentation change (T037); no traceability-verifier or
REF-002/SADS promotion (T038); no external review record (T039); no acceptance-bundle inspection record (T040);
no user acceptance or platform-main merge (T041); no ambient/secret access or dynamic load; no
wall-clock-dependent verdict; no rewrite or weakening of an accepted ADR, requirement, contract, schema,
register, or test; no promotion of any REF-002 SADS ID beyond its recorded disposition; no acceptance or
integration of the candidate; no claim of runtime, compatibility, performance, or production readiness beyond
the executed checks.

### 2.3 Delegated to other tasks (not performed or decided here)

| Area | Owner | Disposition in T035 |
| --- | --- | --- |
| Controlled disabled/enabled-tap benchmarks and uncertainty | T036 | allocated; not run or reported by T035 |
| Complete Doxygen comments and warning-free generated reference | T037 | allocated; not run or reported by T035 |
| Spec Kit + REF-002 traceability verifier, public-safe log validation, SADS disposition proof | T038 | allocated; not run or reported by T035 |
| Independent read-only review | T039 | allocated; deferred until the ordered backlog `xcom-t030-t034-20260928` completes |
| Acceptance-bundle assembly and inspection | T040 | allocated |
| Explicit user acceptance and platform-main delivery | T041 | allocated |

## 3. Stakeholder requirements (`T035-STK-###`)

- **T035-STK-001**: Before any capability-007 acceptance claim, the program **shall** execute the complete
  exact-candidate verification matrix — C++ unit/contract/integration/negative/concurrency, sanitizer, static
  analysis, inherited conformance, whole-system integration, and all existing Python tests — against the exact
  candidate revision.
- **T035-STK-002**: Every retained verification result **shall** be bound to the exact candidate revision and
  **shall** identify its command argv, exit status, deterministic outcome, tool/environment identity, bounded
  log, and artifact hashes.
- **T035-STK-003**: Verification evidence and logs **shall** be repository-owned, bounded, and public-safe, and
  **shall** exclude credentials, private addresses, unrestricted payloads, proprietary source excerpts, and
  sensitive deployment or host-specific values.
- **T035-STK-004**: Every applied T035 requirement **shall** trace to its accepted X-COM system/software anchor
  and **shall** be verified by a named executed case or a named inspection, not by source inspection alone.
- **T035-STK-005**: T035 **shall** preserve accepted intent and report maturity honestly: it changes no accepted
  production source or test, keeps the accepted registers and the REF-002 disposition `unchanged` with an empty
  `promoted` list, and leaves T036–T041 allocated.

## 4. Software/engineering requirements (`T035-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Verified" means the named case, measure, or inspection exists, is deterministic, and passes at the
recorded candidate revision; it is not a deployed-service, compatibility, or production-readiness claim.

### 4.1 Complete C++ verification matrix

- **T035-SR-001 [ubiquitous]**: At the exact candidate revision, the platform **shall** build under the accepted
  warning-as-error policy and the full discovered CTest suite **shall** execute, with the discovered and passed
  counts recorded.
  - Refines: `T035-STK-001`; anchors `XCOM-SYS-FR-030`; `XCOM-SW-ENB-004`, `XCOM-SW-CORE-009`;
    `XCOM-DU-001`…`XCOM-DU-024`.
  - Verification intent: `T033ProviderContractSuite.AcceptedLoopbackProviderConforms`.
- **T035-SR-002 [ubiquitous]**: The inherited T016/T020/T026–T034 suites **shall** retain their exact accepted
  behavior, and no existing target, test name, label, command, or expected value **shall** change or be
  reduced.
  - Refines: `T035-STK-001`, `T035-STK-005`; anchors `XCOM-SYS-FR-030`; `XCOM-SW-CORE-009`.
  - Verification intent: `T034SecondProviderSuite.ReusedProviderContractSuitePasses`.
- **T035-SR-003 [ubiquitous]**: The accepted negative-case matrix — malformed contract, incompatible identity
  or direction, over-capacity, unadvertised capability, and unauthorized stimulus rejection — **shall** execute
  and pass.
  - Refines: `T035-STK-001`; anchors `XCOM-SYS-FR-006`, `XCOM-SYS-FR-007`; `XCOM-SW-CORE-003`.
  - Verification intent: `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch`.
- **T035-SR-004 [ubiquitous]**: The accepted concurrency and recovery matrix **shall** execute and demonstrate
  deterministic repeated outcomes.
  - Refines: `T035-STK-001`; anchors `XCOM-SYS-FR-010`; `XCOM-SW-CORE-005`.
  - Verification intent: `CoreMatrixConcurrency.ConcurrentRepeatedRuns_DeterministicOutcome`.

### 4.2 Sanitizer, static analysis, and language suites

- **T035-SR-005 [ubiquitous]**: A separate AddressSanitizer/UndefinedBehaviorSanitizer build **shall** run the
  full suite and its outcome **shall** be recorded; a sanitizer failure **shall** be reported as failed, not
  suppressed.
  - Refines: `T035-STK-001`, `T035-STK-002`; anchors `XCOM-SYS-FR-030`; `XCOM-SW-ENB-004`.
  - Verification intent: `CoreMatrixConcurrency.ConcurrentSubmitReceive_ExactlyOncePerRouteFifo`.
- **T035-SR-006 [ubiquitous]**: The `cppcheck` static-analysis measure **shall** execute over
  `src/xverse/xcom/src` with error-exit enabled, and its exit status and outcome **shall** be recorded.
  - Refines: `T035-STK-001`, `T035-STK-002`; anchors `XCOM-SYS-FR-029`; `XCOM-SW-ENB-004`.
  - Verification intent: `T034VersionRejection.RejectionEmitsNothing`.
- **T035-SR-007 [ubiquitous]**: All existing Python tests **shall** execute and their collected/passed counts
  and outcome **shall** be recorded.
  - Refines: `T035-STK-001`; anchors `XCOM-SYS-FR-030`; `XCOM-SW-XDL-002`, `XCOM-SW-XDL-003`.
  - Verification intent: `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue`.

### 4.3 Whole-system, conformance, and cross-cutting measures

- **T035-SR-008 [event-driven]**: When the trusted target-repository integration measure assembles the pinned
  platform revision and runs the whole system, its assembled-revision identity and outcome **shall** be
  recorded.
  - Refines: `T035-STK-001`, `T035-STK-002`; anchors `XCOM-SYS-FR-030`; `XCOM-SW-ENB-001`.
  - Verification intent: `Integration.GenerationRotationInvalidatesLiveHandle`.
- **T035-SR-009 [event-driven]**: When the inherited Phase 6 conformance recheck runs against the candidate,
  every named inspection's outcome **shall** be recorded.
  - Refines: `T035-STK-001`, `T035-STK-002`; anchors `XCOM-SYS-FR-030`; `XCOM-SW-CORE-009`.
  - Verification intent: `XcomStimulationMatrixConcurrency.ConcurrentQuotaEmissionDeterminism`.
- **T035-SR-010 [ubiquitous]**: The repository **shall** retain
  `reports/xcom-queue/t035-verification.json` carrying `commands`, `outcomes`, `hashes`, `environment`,
  bounded logs, and the exact-candidate identity.
  - Refines: `T035-STK-002`, `T035-STK-003`; anchors `XCOM-SYS-FR-030`; `XCOM-SW-INTG-001`.
  - Verification intent: `T033GatewayContractSuite.AcceptedGatewaySessionConforms`.
- **T035-SR-011 [ubiquitous]**: Every recorded command **shall** carry its argv and exit status, and its
  outcome **shall** be `pass` only when the trusted discovery check is satisfied; a missing, stale, mismatched,
  skipped, or failed measure **shall** be recorded as `failed` or `blocked`.
  - Refines: `T035-STK-002`; anchors `XCOM-SYS-FR-030`; `XCOM-SW-ENB-001`, `XCOM-SW-INTG-001`.
  - Verification intent: `XcomToolGatewayBounds.MessageSizeBoundEnforced`.
- **T035-SR-012 [ubiquitous]**: The report **shall** record the compiler, CMake, Ninja, `cppcheck`, Python, and
  admitted offline toolchain/package-manifest/GTest-prefix identities and hashes, and **shall** exclude
  host-specific absolute paths from the public evidence.
  - Refines: `T035-STK-002`, `T035-STK-003`; anchors `XCOM-SYS-FR-027`; `XCOM-SW-ENB-004`,
    `XCOM-SW-INTG-001`.
  - Verification intent: `T033ObserverContractSuite.AcceptedObservationHubConforms`.

### 4.4 Public safety, ownership, and governance

- **T035-SR-013 [unwanted]**: If any payload byte, permit content, secret, private address, host path, or
  proprietary source excerpt would appear in a committed T035 artifact, report, or bounded log, it **shall** be
  redacted or omitted before the artifact is committed.
  - Refines: `T035-STK-003`; anchors `XCOM-SYS-FR-027`; `XCOM-SW-INTG-001`.
  - Verification intent: `T033StimulationToolContractSuite.AcceptedStimulationPathConforms`.
- **T035-SR-014 [ubiquitous]**: T035 **shall** change no accepted production source, header, contract, schema,
  register, XDL profile, or test byte; any build-wiring or measure-descriptor touch **shall** be additive or
  content-only and **shall** preserve every accepted target, label, command, and expected value.
  - Refines: `T035-STK-005`; anchors `XCOM-SYS-FR-030`; ADR-0020; Constitution VII, X.
  - Verification intent: `XcomToolGatewayNegative.NoTcpOrAddressPrimitive`.
- **T035-SR-015 [ubiquitous]**: T035 **shall** reconcile with the T007 ownership register, the T008 register,
  the T009 architecture model, and the T010 unit design without rewriting or weakening them; **shall** keep the
  REF-002 disposition `unchanged` with an empty `promoted` list; **shall** record T035 as implemented while
  T036–T041 remain allocated; and **shall** satisfy the deterministic Phase 8 gate and the required trace links.
  - Refines: `T035-STK-004`, `T035-STK-005`; anchors `XCOM-SYS-FR-035`, `XCOM-SYS-FR-030`; Constitution VII,
    IX, X; ADR-0020.
  - Verification intent: `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource`.
- **T035-SR-016 [unwanted]**: No verification command **shall** open a TCP listener, create an
  `AF_INET`/`AF_INET6` socket, use DNS, a resolver, or TLS, contact an external network peer, execute a legacy
  binary or production workload, or make a runtime, compatibility, performance, or production-readiness claim
  beyond the executed checks.
  - Refines: `T035-STK-003`, `T035-STK-005`; anchors `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028`;
    `XCOM-SW-CORE-007`; Constitution VII, IX.
  - Verification intent: `T026JournalRecovery.test_journal_restart_recovery_and_orphans`.

## 5. Requirement-to-accepted-anchor traceability

| T035 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T035-STK-001 | `XCOM-SW-ENB-001/004`, `XCOM-SW-CORE-009` | `XCOM-SYS-FR-030` | FR-030, plan step 9, SC-009 | IX, X |
| T035-STK-002 | `XCOM-SW-ENB-001/004` | `XCOM-SYS-FR-030` | FR-030, build-environment evidence contract | X |
| T035-STK-003 | `XCOM-SW-INTG-001` | `XCOM-SYS-FR-027` | FR-027, SC-009 | VII, X |
| T035-STK-004 | `XCOM-SW-ENB-001` | `XCOM-SYS-FR-030` | FR-030, SC-009 | IX, X |
| T035-STK-005 | ADR-0020; `XCOM-SW-ENB-002` | `XCOM-SYS-FR-027/029/030/035` | FR-027, FR-029, FR-030, FR-035 | VII, IX, X |
| T035-SR-001 | `XCOM-SW-ENB-004`, `XCOM-SW-CORE-009` | `XCOM-SYS-FR-030` | FR-030, SC-009 | IX, X |
| T035-SR-002 | `XCOM-SW-CORE-009` | `XCOM-SYS-FR-030` | FR-030 | IX, X |
| T035-SR-003 | `XCOM-SW-CORE-003` | `XCOM-SYS-FR-006/007` | FR-006, FR-007 | IX |
| T035-SR-004 | `XCOM-SW-CORE-005` | `XCOM-SYS-FR-010` | FR-010 | IX |
| T035-SR-005 | `XCOM-SW-ENB-004` | `XCOM-SYS-FR-030` | FR-030 | X |
| T035-SR-006 | `XCOM-SW-ENB-004` | `XCOM-SYS-FR-029` | FR-029 | X |
| T035-SR-007 | `XCOM-SW-XDL-002/003` | `XCOM-SYS-FR-030` | FR-030, SC-002 | IX, X |
| T035-SR-008 | `XCOM-SW-ENB-001` | `XCOM-SYS-FR-030` | FR-030 | X |
| T035-SR-009 | `XCOM-SW-CORE-009` | `XCOM-SYS-FR-030` | FR-030 | IX, X |
| T035-SR-010 | `XCOM-SW-INTG-001` | `XCOM-SYS-FR-030` | FR-030, SC-009 | X |
| T035-SR-011 | `XCOM-SW-ENB-001`, `XCOM-SW-INTG-001` | `XCOM-SYS-FR-030` | FR-030, SC-009 | X |
| T035-SR-012 | `XCOM-SW-ENB-004`, `XCOM-SW-INTG-001` | `XCOM-SYS-FR-027` | FR-027 | X |
| T035-SR-013 | `XCOM-SW-INTG-001` | `XCOM-SYS-FR-027` | FR-027, SC-009 | VII, X |
| T035-SR-014 | ADR-0020; Constitution | `XCOM-SYS-FR-030` | FR-030 | VII, X |
| T035-SR-015 | `XCOM-SW-ENB-001/002` | `XCOM-SYS-FR-030/035` | FR-030, FR-035 | VII, IX, X |
| T035-SR-016 | `XCOM-SW-CORE-007` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | VII, IX |

Each accepted T035 software requirement refines at least one `T035-STK-###` stakeholder requirement through an
explicit `refines` link in `engineering/trace/links.json`. `T035-VS-ACCUMULATED` validates
`T035-SR-001`…`-016` and names the executed `t035` matrix cases that the trusted measures select.

## 6. REF-002 disposition

T035 owns no REF-002 SADS ID and promotes none. The exact-candidate verification matrix is recorded as a
**partial contribution** to the already-**allocated** `XVE-SYS-0139`–`0158` targets through their accepted
dispositions, and is **not** promoted. `XVE-SYS-0141` remains **deferred**; `XVE-SYS-0143`/`0157` remain
deferred to registry/reconfiguration; `XVE-SYS-0144`/`0153`/`0155` remain deferred to Security/deployment;
`XVE-SYS-0148`/`0150`/`0151` remain deferred to record/replay, edge/cloud, and Argus adapters; the automatic
recovery portion of `XVE-SYS-0158` remains deferred to Faults/Runtime. The capability `ref002.disposition`
stays `unchanged` (T035-SR-015). No allocated, deferred, architectural-target, or superseded SADS requirement
is reported as implemented.

## 7. Affected paths

### 7.1 Paths the T035 candidate changes (implementation stage)

| Path | Change | Notes |
| --- | --- | --- |
| `docs/engineering/xcom/t035/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md` | add | this work-product set |
| `engineering/project.json` | edit | current task T035 and accepted baseline `dab68568bd8d189b14c7a4a9e3a9c325085a7529` |
| `engineering/requirements/T035-STK-00{1..5}.json`, `T035-SR-0{01..16}.json` | add | current-task requirement records |
| `engineering/architecture/components/T035-SR-0{01..16}-CMP.json` | add | current-task component allocations |
| `engineering/unit-specifications/T035-SR-0{01..16}-U.json` | add | current-task unit specifications |
| `engineering/validation/scenarios/T035-VS-ACCUMULATED.json` | add | current-task validation scenario |
| `engineering/verification/measures/{unit,integration,validation,static_analysis}.json` | edit (content-only, revision unchanged) | refreshed to the Phase 8 verification route and the T035 selected case set |
| `engineering/verification/measures/sanitizer.json` | add | the sanitizer measure descriptor (kind `sanitizer`) |
| `engineering/trace/links.json` | edit | additive T035 trace links |
| `docs/engineering/xcom/t010/unit-design.json`, `docs/engineering/xcom/t010/design-units.md` | edit | required planned→established path-status reconciliation for the now-present `docs/engineering/xcom/t035/` path (status field only) |
| `reports/review-index.md` | edit | T035 candidate section appended |
| `reports/xcom-queue/t035-verification.json` | add | the exact-candidate verification evidence report |
| `specs/007-xcom-core/tasks.md` | edit | one-line T035 checkbox, **implementation stage only** |
| `reports/xcom-queue/t035-package.json` | add | implementation-stage package record |

### 7.2 Consumed read-only (not changed by T035)

Every accepted `src/xverse/xcom/**` source, header, contract, schema, and fixture including
`synthetic_provider.{hpp,cpp}`; every accepted test under `tests/xcom/**` and `tests/test_xcom_plan.py`;
`tests/xcom/contract_suites/**`; `proto/xverse/xcom/v1/tool_gateway.proto`;
`docs/engineering/xcom/task-ownership.*`; `docs/engineering/xcom/t00{7,8,9}/**` and
`docs/engineering/xcom/t010/unit-design.json`/`design-units.md` (read-only except the single
planned→established status field for `docs/engineering/xcom/t035/`);
`docs/engineering/xcom/t0{01..09}/**` and `docs/engineering/xcom/t0{11..34}/**`;
`docs/engineering/xcom/build-environment.md`;
`docs/engineering/xcom/dependency-lock.md`; `engineering/check_phase6_conformance.py`,
`engineering/run_phase6_conformance.py`; and `specs/007-xcom-core/**` other than the T035 checkbox.

### 7.3 Explicitly not implemented by T035

The T036 benchmarks, T037 Doxygen completion, T038 traceability verifier and SADS disposition proof, the
gRPC transport runtime linkage (`T032-GAP-01`), and any change to an accepted production source, test, target,
label, command, or expected value. External Codex review and user acceptance remain T039/T041 and are deferred
until the ordered backlog `xcom-t030-t034-20260928` completes.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- **T035-GAP-01 — verification only.** T035 executes and records the accepted matrix; it makes no
  deployed-service, network, transport, timing, compatibility, or production-readiness claim.
- **T035-GAP-02 — candidate-local vs whole-system.** The unit, static-analysis, sanitizer, and validation
  measures are candidate-local unless the trusted policy binds the whole-system target-repository integration
  measure; T035 records which measure is which and does not report a candidate-local check as whole-system
  integration.
- **T035-GAP-03 — admitted envelope.** The admitted T011 prefix cannot link the gRPC transport runtime
  (`T032-GAP-01`); the sanitizer and static-analysis measures cover the accepted in-process sources only.
- **T035-GAP-04 — no benchmark, Doxygen, or SADS claim.** Performance/uncertainty (T036), generated
  documentation (T037), traceability validation and SADS disposition (T038), review (T039/T040), and acceptance
  (T041) remain allocated.

### 8.2 Gaps with owning tasks

| Gap | Owner |
| --- | --- |
| Controlled benchmark evidence | T036 |
| Warning-free generated reference documentation | T037 |
| Traceability verifier and REF-002/SADS disposition | T038 |
| Independent review, acceptance-bundle inspection, user acceptance | T039/T040/T041 |
| gRPC transport runtime envelope | deferred capability gap `T032-GAP-01` |

### 8.3 Open items

- **T035-OPEN-01 — measure-descriptor refresh is content-only.** Refreshing
  `engineering/verification/measures/{unit,integration,validation,static_analysis}.json` to the Phase 8 route
  keeps each `revision` at `1`; changing a revision would stale every accepted `verified_by`/`analyzed_by` link
  and is prohibited.
- **T035-OPEN-02 — report is implementation-stage.** `reports/xcom-queue/t035-verification.json` is produced
  only at the implementation stage from executed commands; the plan stage records the required schema and the
  exact command route rather than fabricating results.
- **T035-OPEN-03 — no inherited digest cascade.** T035 changes no production source and no build wiring, so no
  inherited `implemented_by` target or stage-result digest requires refresh; the inherited `engineering/trace/links.json`
  is extended additively only.
- **T035-OPEN-04 — unavailable inputs are blockers.** If an admitted offline input, tool, or measure is
  unavailable at the candidate revision, the affected outcome is recorded as `blocked` (with the reason) and the
  candidate does not claim a pass; the plan does not substitute inferred or stale evidence.
- **T035-OPEN-05 — planned→established path reconciliation.** The T010 unit design (`XCOM-DU-024`) declared
  `docs/engineering/xcom/t035/` as planned; because the plan stage now establishes that path, its status field is
  reconciled to established in `docs/engineering/xcom/t010/unit-design.json` and `design-units.md`. No unit,
  ownership, lifetime, bound, or requirement content changes.

## 9. Definition of done (requirements view)

T035 is done for a candidate revision when: every §4 requirement has at least one named executed case, measure,
or inspection; the full C++ suite, sanitizer build, `cppcheck`, inherited Phase 6 conformance recheck,
whole-system integration measure, and all existing Python tests execute and pass; the discovered and passed
counts are unchanged in kind and no existing target/label/value is reduced;
`reports/xcom-queue/t035-verification.json` carries `commands`, `outcomes`, `hashes`, `environment`, bounded
logs, and the exact-candidate identity; every result is public-safe; the accepted registers are reconciled with
the REF-002 disposition `unchanged` and nothing promoted; the deterministic Phase 8 gate passes; and a separate
DeepSeek internal review records its findings before any repair. This does not constitute user acceptance, which
remains T041.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary checks |
| --- | --- |
| T035-STK-001 | CHK-01, CHK-02, CHK-03, CHK-04, CHK-05, CHK-06 |
| T035-STK-002 | CHK-01, CHK-07, CHK-08, CHK-09, CHK-10, CHK-11 |
| T035-STK-003 | CHK-12, CHK-13 |
| T035-STK-004 | CHK-14, CHK-15 |
| T035-STK-005 | CHK-16, CHK-17, CHK-18 |
| T035-SR-001 | CHK-01, CHK-02 |
| T035-SR-002 | CHK-03 |
| T035-SR-003 | CHK-04 |
| T035-SR-004 | CHK-05 |
| T035-SR-005 | CHK-06 |
| T035-SR-006 | CHK-07 |
| T035-SR-007 | CHK-08 |
| T035-SR-008 | CHK-09 |
| T035-SR-009 | CHK-10 |
| T035-SR-010 | CHK-11, CHK-19 |
| T035-SR-011 | CHK-11, CHK-19 |
| T035-SR-012 | CHK-12 |
| T035-SR-013 | CHK-13 |
| T035-SR-014 | CHK-16, CHK-17 |
| T035-SR-015 | CHK-14, CHK-18, CHK-20 |
| T035-SR-016 | CHK-05, CHK-13 |
