# T036 Requirements — Controlled Disabled/Enabled-Tap Benchmarks and Repository-Owned Results

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T036 (capability 007, slice `T-INTG`/evidence) |
| Task title | Run controlled benchmarks and record environment, uncertainty, baseline, disabled/enabled tap results, and explicit non-production limitations |
| Stage / role | plan → requirements |
| Revision | 1 (Phase 8 controlled-benchmark slice) |
| Baseline revision | `8ec69ddd34ed8c7a07adbcb631dcfb2da3faf15f` |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC012`, `ACC014`, `ACC015`); `ADR-0020` (repository-owned work products and exact-candidate evidence); Constitution VII, IX, X |
| Owning slice | `T-INTG` (T007 ownership register); T036 is the benchmark task of the `T-INTG` evidence family |
| Predecessors | T035 accepted exact-candidate verification matrix and repository-owned results; T030–T034 accepted contract/gateway/client/suite/provider; T026–T029 accepted stimulation boundary; T021–T024 accepted observation boundary (including the accepted disabled-tap benchmark `xcom_observation_disabled_benchmark`, `tests/xcom/observation/integration/disabled_tap_benchmark.cpp`); T017–T020 accepted XDL activation plan; T016 accepted core matrix; T011 admitted offline envelope; T012 subtree build/CTest contract |
| Successor tasks | T037–T041 (Doxygen, traceability, external review, acceptance-bundle inspection, user acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}` (`T-INTG` slice); `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-SW-INTG-003` — the register row whose `owning_task` is T036; supporting `XCOM-SW-OBS-003`, `XCOM-SW-CORE-007`, `XCOM-SW-ENB-001`, `XCOM-SW-ENB-002`, `XCOM-SW-ENB-004`, `XCOM-SW-INTG-001`); `docs/engineering/xcom/t009/architecture-model.json`; `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-024`, the `docs/engineering/xcom/t036/` artifact path); `specs/007-xcom-core/spec.md` SC-008; `docs/engineering/xcom/build-environment.md` (evidence contract) |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any benchmark is
executed and does not itself execute, accept, or integrate the candidate. The T036 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T036 — Run controlled benchmarks and record environment, uncertainty, baseline, disabled/enabled tap
> results, and explicit non-production limitations.

It realizes the accepted delivery-phase performance-evidence step of `specs/007-xcom-core/plan.md`
("controlled performance benchmarks"), the measurable outcome `SC-008` ("With taps disabled, the
benchmark records no more than 2% median throughput regression and no more than 2% median latency
regression against the same owned loopback baseline; results must include uncertainty and environment
data and are not production claims"), the accepted `XCOM-SW-INTG-003` software requirement ("Record
disabled-tap versus same-baseline throughput and latency with uncertainty and environment data and
explicit non-production limitations"), the `XCOM-SW-ENB-001`/`XCOM-SW-ENB-004` traceability and
admitted-build obligations, and the `XCOM-SW-OBS-003`/`XCOM-SW-CORE-007` observation-bound and
owned-loopback obligations. It does not perform, duplicate, or claim the T035 verification matrix,
T037 Doxygen, T038 traceability-verifier/SADS-disposition, T039 external review, T040 acceptance-bundle
inspection, or T041 user acceptance work.

### 1.1 Authority statement

T036 owns the **controlled disabled/enabled observation-tap benchmark and its repository-owned
results**. It provides:

- a task-owned benchmark harness `engineering/run_xcom_benchmarks.py` that runs the accepted owned
  loopback workload with the observation tap disabled (same-baseline) and enabled, over controlled
  repeated paired samples, and produces both throughput and latency results;
- the repository-owned evidence report `reports/xcom-queue/t036-benchmark.json` carrying `environment`,
  `uncertainty`, `baseline`, `tap_disabled`, `tap_enabled`, `limitations`, the raw paired samples, and
  the exact-candidate identity;
- the T036 engineering records and work products that trace every T036 requirement to an accepted
  anchor, component, unit, measure, and named executed case or inspection.

The `T008` requirements register allocates `XCOM-SW-INTG-003` (`owning_task` T036) as the accepted
software anchor this task realizes, together with the supporting anchors above. The register rows are
not edited (T026–T035 precedent).

**Recorded design decision (`T036-DD-01`).** T036 adds **no change to any accepted production source,
header, contract, schema, register, XDL profile, or test byte and no new admitted dependency**. Its new
artifacts are the benchmark harness, the evidence report, the T036 work-product set, and the additive
engineering records. The trace's `implemented_by` edges point at the harness/evidence artifacts and at
the accepted code paths the benchmark exercises; the executed cases are named by the accepted suites'
existing discovered IDs plus the benchmark harness command.

**Evidence-only, additive boundary.** T036 authors one benchmark harness, one evidence report, one
work-product set, one engineering record set, and additive trace links. It authors no change to any
accepted production source, header, contract, schema, register, XDL profile, T030 contract, T031
gateway, T032 client, T033/T034 suite, or any other accepted test, target, label, command, or expected
value.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts,
data model, the T007 ownership register, the T008 register, the T009 architecture model, the T010 unit
design, the constitution, or an accepted ADR is resolved in favour of the accepted source. A material
gap is reported rather than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T036)

1. **Controlled benchmark.** A task-owned harness `engineering/run_xcom_benchmarks.py` runs the
   accepted owned loopback workload with the observation tap disabled (same-baseline) and enabled,
   with a controlled, recorded number of interleaved paired samples.
2. **Baseline.** The same-baseline case is the accepted pre-observation/disabled-observation submit
   path on the owned loopback route, so the enabled-tap result is a regression against an identical
   workload, not against a different one.
3. **Disabled and enabled tap results.** Both the disabled and the enabled case report median latency
   and median throughput.
4. **Uncertainty.** Each case records its sample count, median, and a dispersion or interval measure;
   the uncertainty statement is explicit and does not imply production-grade confidence.
5. **Two-percent comparison.** The report records the median throughput and latency regression of the
   tap-disabled case against the same owned-loopback baseline, compares it against the accepted 2% SC-008
   threshold with a deterministic pass/fail outcome, and records the enabled-versus-disabled regression as
   an ungated observation that is not subject to the two-percent threshold.
6. **Environment identity.** The report records compiler, C++ standard, CMake, Ninja, Python, and the
   admitted offline toolchain/package-manifest/GTest-prefix identities and hashes; host-specific
   absolute paths are excluded from the public evidence.
7. **Raw samples and method.** The report exposes the raw paired samples and the measurement method so
   the result is reproducible.
8. **Repository-owned report.** `reports/xcom-queue/t036-benchmark.json` exists and carries
   `environment`, `uncertainty`, `baseline`, `tap_disabled`, `tap_enabled`, `limitations`, raw samples,
   method, and the exact-candidate identity.
9. **Fail-closed verification.** `engineering/run_xcom_benchmarks.py --verify
   reports/xcom-queue/t036-benchmark.json` re-reads the report and exits nonzero when a required field
   is missing, the method/uncertainty is incomplete, the result is stale or foreign to the candidate,
   or the gated `tap_disabled`-versus-same-baseline 2% threshold is exceeded.
10. **Non-production limitations.** The report declares explicit non-production limitations (for
    example uncontrolled CPU affinity, scheduler load, DVFS, thermal, and cache state) and does not
    claim production performance.
11. **Owned/local execution.** The benchmark uses only the accepted owned loopback and in-process
    fixtures; it opens no network, DNS, TLS, legacy, or production resource.
12. **No accepted change.** No accepted production source, header, contract, schema, register, XDL
    profile, or test changes; any harness, report, or record is additive.
13. **Governance honesty.** The T007–T010 models are reconciled without rewrite; the REF-002
    disposition stays `unchanged` with an empty `promoted` list; T036 is recorded implemented while
    T037–T041 remain allocated.
14. The T036 repository-owned work products and the T036 package record.

### 2.2 Explicit exclusions (must remain absent from the T036 candidate)

No modification of any accepted production source, header, contract, schema, register, XDL profile,
accepted test, target, label, command, or expected value; no new admitted dependency; no new runtime
library; no compiled or linked gRPC runtime; no TCP listener or `AF_INET`/`AF_INET6` socket, DNS,
resolver, or TLS use; no external network peer; no legacy binary, legacy repository, or production
workload execution; no re-run or re-claim of the T035 verification matrix; no Doxygen source-comment
or generated-documentation change (T037); no traceability-verifier or REF-002/SADS promotion (T038);
no external review record (T039); no acceptance-bundle inspection record (T040); no user acceptance or
platform-main merge (T041); no ambient/secret access or dynamic load; no wall-clock-dependent verdict
outside the recorded uncertainty statement; no claim of production, deployed-service, network,
transport, compatibility, or timing fidelity; no rewrite or weakening of an accepted ADR,
requirement, contract, schema, register, or test; no promotion of any REF-002 SADS ID beyond its
recorded disposition; no acceptance or integration of the candidate.

### 2.3 Delegated to other tasks (not performed or decided here)

| Area | Owner | Disposition in T036 |
| --- | --- | --- |
| Complete exact-candidate verification matrix and repository-owned results | T035 | accepted; consumed read-only, not re-run or re-claimed by T036 |
| Complete Doxygen comments and warning-free generated reference | T037 | allocated; not run or reported by T036 |
| Spec Kit + REF-002 traceability verifier, public-safe log validation, SADS disposition proof | T038 | allocated; not run or reported by T036 |
| Independent read-only review | T039 | allocated; deferred until the ordered backlog `xcom-t030-t034-20260928` completes |
| Acceptance-bundle assembly and inspection | T040 | allocated |
| Explicit user acceptance and platform-main delivery | T041 | allocated |

## 3. Stakeholder requirements (`T036-STK-###`)

- **T036-STK-001**: Before any capability-007 performance claim, the program **shall** record controlled
  benchmark results for the observation tap enabled and disabled against the same owned loopback
  baseline, with the method, environment, uncertainty, and explicit non-production limitations.
- **T036-STK-002**: Every retained benchmark result **shall** be bound to the accepted baseline revision
  and the exact candidate material (a sorted material-input inventory, a material digest, and per-file
  SHA-256 hashes) and **shall** identify its method, raw samples, environment, uncertainty, and artifact
  hashes. Because a committed report cannot contain the hash of the commit that contains it, the candidate
  commit is identified as the direct child of the accepted baseline carrying that material.
- **T036-STK-003**: Benchmark evidence and logs **shall** be repository-owned, bounded, and public-safe,
  and **shall** exclude credentials, private addresses, unrestricted payloads, proprietary source
  excerpts, and host-specific or sensitive deployment values.
- **T036-STK-004**: Every applied T036 requirement **shall** trace to its accepted X-COM system/software
  anchor and **shall** be verified by a named executed measurement or inspection, not by source
  inspection alone.
- **T036-STK-005**: T036 **shall** preserve accepted intent and report maturity honestly: it changes no
  accepted production source or test, keeps the accepted registers and the REF-002 disposition
  `unchanged` with an empty `promoted` list, and leaves T037–T041 allocated.

## 4. Software/engineering requirements (`T036-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an
accepted anchor. "Verified" means the named case, measure, or inspection exists, is deterministic, and
passes at the recorded candidate revision; it is not a deployed-service, compatibility, or
production-readiness claim.

### 4.1 Controlled disabled/enabled-tap benchmark

- **T036-SR-001 [ubiquitous]**: At the exact candidate revision, the benchmark **shall** measure median
  latency and throughput with the observation tap disabled (same-baseline) and enabled over the same
  owned loopback workload, using controlled repeated paired samples, and **shall** record both results.
  - Refines: `T036-STK-001`; anchors `XCOM-SW-INTG-003`, `XCOM-SW-OBS-003`; `XCOM-SYS-FR-014`,
    `XCOM-SYS-SC-008`.
  - Verification intent: `xcom_observation_disabled_benchmark`.
- **T036-SR-002 [ubiquitous]**: The benchmark **shall** compute and record an uncertainty statement
  (sample count, median, and a dispersion or interval measure) for each disabled and enabled case.
  - Refines: `T036-STK-001`; anchors `XCOM-SW-INTG-003`; `XCOM-SYS-SC-008`.
  - Verification intent: `CoreMatrixConcurrency.ConcurrentRepeatedRuns_DeterministicOutcome`.
- **T036-SR-003 [ubiquitous]**: The benchmark **shall** compare the tap-disabled case against the same
  owned-loopback baseline and **shall** record the median throughput and latency regression against the
  accepted two-percent threshold with a deterministic pass/fail outcome; the enabled-versus-disabled
  regression **shall** be recorded as an ungated observation that is not subject to the two-percent
  threshold.
  - Refines: `T036-STK-001`; anchors `XCOM-SW-INTG-003`; `XCOM-SYS-SC-008`.
  - Verification intent: `CoreMatrixConcurrency.ConcurrentSubmitReceive_ExactlyOncePerRouteFifo`.
- **T036-SR-006 [ubiquitous]**: The report **shall** declare explicit non-production limitations —
  including uncontrolled CPU affinity, scheduler load, DVFS, thermal, and cache state — and **shall
  not** claim production performance.
  - Refines: `T036-STK-001`; anchors `XCOM-SW-INTG-003`; `XCOM-SYS-FR-008`, `XCOM-SYS-SC-008`.
  - Verification intent: `T033ProviderContractSuite.AcceptedLoopbackProviderConforms`.

### 4.2 Environment, method, raw samples, and exact binding

- **T036-SR-004 [ubiquitous]**: The report **shall** record the compiler, C++ standard, CMake, Ninja,
  Python, and admitted offline toolchain/package-manifest/GTest-prefix identities and hashes, excluding
  host-specific absolute paths.
  - Refines: `T036-STK-002`, `T036-STK-003`; anchors `XCOM-SW-ENB-004`, `XCOM-SW-INTG-001`;
    `XCOM-SYS-FR-027`, `XCOM-SYS-FR-029`.
  - Verification intent: `T033ObserverContractSuite.AcceptedObservationHubConforms`.
- **T036-SR-005 [ubiquitous]**: The report **shall** expose the raw paired samples and the measurement
  method so that the reported result is reproducible.
  - Refines: `T036-STK-002`; anchors `XCOM-SW-INTG-003`; `XCOM-SYS-SC-008`, `XCOM-SYS-FR-030`.
  - Verification intent: `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue`.
- **T036-SR-008 [ubiquitous]**: The report **shall** be bound to the accepted baseline revision and the
  exact candidate material (inventory, digest, and per-file hashes) and **shall** record the SHA-256 hashes
  of the retained evidence, raw samples, and candidate artifacts; the candidate commit is the direct child
  of the baseline carrying that material.
  - Refines: `T036-STK-002`; anchors `XCOM-SW-INTG-003`, `XCOM-SW-ENB-004`; `XCOM-SYS-FR-030`.
  - Verification intent: `T033GatewayContractSuite.AcceptedGatewaySessionConforms`.

### 4.3 Fail-closed harness and local-only execution

- **T036-SR-009 [event-driven]**: When `engineering/run_xcom_benchmarks.py --verify
  reports/xcom-queue/t036-benchmark.json` runs, it **shall** re-read the report and fail closed
  (nonzero) when a required field is missing, the method/uncertainty is incomplete, the result is stale
  or foreign to the candidate, or the gated `tap_disabled`-versus-same-baseline 2% threshold is exceeded.
  - Refines: `T036-STK-004`; anchors `XCOM-SW-INTG-003`; `XCOM-SYS-FR-030`, `XCOM-SYS-SC-008`.
  - Verification intent: `XcomToolGatewayBounds.MessageSizeBoundEnforced`.
- **T036-SR-007 [ubiquitous]**: The benchmark **shall** run only over the accepted owned loopback and
  in-process fixtures, with no network, DNS, TLS, legacy, or production resource.
  - Refines: `T036-STK-003`; anchors `XCOM-SW-CORE-007`; `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028`.
  - Verification intent: `T026JournalRecovery.test_journal_restart_recovery_and_orphans`.
- **T036-SR-012 [unwanted]**: No benchmark command **shall** open a TCP listener, create an
  `AF_INET`/`AF_INET6` socket, use DNS, a resolver, or TLS, contact an external peer, execute a legacy
  binary or production workload, or claim runtime, compatibility, or production readiness beyond the
  measured evidence.
  - Refines: `T036-STK-003`; anchors `XCOM-SW-CORE-007`, `XCOM-SW-INTG-001`; `XCOM-SYS-FR-026`,
    `XCOM-SYS-FR-027`, `XCOM-SYS-FR-028`.
  - Verification intent: `T033StimulationToolContractSuite.AcceptedStimulationPathConforms`.

### 4.4 Ownership, public safety, and governance

- **T036-SR-010 [unwanted]**: T036 **shall** change no accepted production source, header, contract,
  schema, register, XDL profile, or test byte; any additive harness, report, or record **shall**
  preserve every accepted target, label, command, and expected value.
  - Refines: `T036-STK-005`; anchors `XCOM-SW-INTG-003`, ADR-0020; `XCOM-SYS-FR-030`.
  - Verification intent: `T034SecondProviderSuite.ReusedProviderContractSuitePasses`.
- **T036-SR-011 [ubiquitous]**: T036 **shall** reconcile with the T007 ownership register, the T008
  register, the T009 architecture model, and the T010 unit design without rewriting or weakening them;
  **shall** keep the REF-002 disposition `unchanged` with an empty `promoted` list; **shall** record
  T036 as implemented while T037–T041 remain allocated; and **shall** satisfy the deterministic Phase 8
  gate and the required trace links.
  - Refines: `T036-STK-004`, `T036-STK-005`; anchors `XCOM-SW-ENB-001`, `XCOM-SW-ENB-002`;
    `XCOM-SYS-FR-030`, `XCOM-SYS-FR-035`.
  - Verification intent: `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource`.

## 5. Requirement-to-accepted-anchor traceability

| T036 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T036-STK-001 | `XCOM-SW-INTG-003` | `XCOM-SYS-SC-008`, `XCOM-SYS-FR-030` | SC-008, plan performance step | IX, X |
| T036-STK-002 | `XCOM-SW-INTG-003` | `XCOM-SYS-FR-030`, `XCOM-SYS-SC-008` | FR-030, SC-008 | X |
| T036-STK-003 | `XCOM-SW-INTG-001` | `XCOM-SYS-FR-027` | FR-027 | VII, X |
| T036-STK-004 | `XCOM-SW-ENB-001` | `XCOM-SYS-FR-030`, `XCOM-SYS-SC-009` | FR-030, SC-009 | IX, X |
| T036-STK-005 | `XCOM-SW-ENB-002` | `XCOM-SYS-FR-027/030/035` | FR-027, FR-030, FR-035 | VII, IX, X |
| T036-SR-001 | `XCOM-SW-INTG-003`, `XCOM-SW-OBS-003` | `XCOM-SYS-FR-014`, `XCOM-SYS-SC-008` | SC-008, FR-014 | IX, X |
| T036-SR-002 | `XCOM-SW-INTG-003` | `XCOM-SYS-SC-008` | SC-008 | X |
| T036-SR-003 | `XCOM-SW-INTG-003` | `XCOM-SYS-SC-008` | SC-008 | X |
| T036-SR-004 | `XCOM-SW-ENB-004`, `XCOM-SW-INTG-001` | `XCOM-SYS-FR-027/029` | FR-027, FR-029 | X |
| T036-SR-005 | `XCOM-SW-INTG-003` | `XCOM-SYS-SC-008`, `XCOM-SYS-FR-030` | SC-008, FR-030 | X |
| T036-SR-006 | `XCOM-SW-INTG-003` | `XCOM-SYS-FR-008`, `XCOM-SYS-SC-008` | FR-008, SC-008 | X |
| T036-SR-007 | `XCOM-SW-CORE-007` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | VII, IX |
| T036-SR-008 | `XCOM-SW-INTG-003`, `XCOM-SW-ENB-004` | `XCOM-SYS-FR-030` | FR-030, SC-009 | X |
| T036-SR-009 | `XCOM-SW-INTG-003` | `XCOM-SYS-FR-030`, `XCOM-SYS-SC-008` | FR-030, SC-008 | X |
| T036-SR-010 | ADR-0020; `XCOM-SW-INTG-003` | `XCOM-SYS-FR-030` | FR-030 | VII, X |
| T036-SR-011 | `XCOM-SW-ENB-001/002` | `XCOM-SYS-FR-030/035` | FR-030, FR-035 | VII, IX, X |
| T036-SR-012 | `XCOM-SW-CORE-007`, `XCOM-SW-INTG-001` | `XCOM-SYS-FR-026/027/028` | FR-026, FR-027, FR-028 | VII, IX |

Each accepted T036 software requirement refines at least one `T036-STK-###` stakeholder requirement
through an explicit `refines` link in `engineering/trace/links.json`. `T036-VS-ACCUMULATED` validates
`T036-SR-001`…`-012` and names the executed `t036` benchmark and inherited matrix cases that the trusted
measures select.

## 6. REF-002 disposition

T036 owns no REF-002 SADS ID and promotes none. The controlled benchmark is recorded as a **partial
contribution** to the already-**allocated** `XVE-SYS-0139`–`0158` targets through their accepted
dispositions, and is **not** promoted. `XVE-SYS-0141` remains **deferred**; `XVE-SYS-0143`/`0157` remain
deferred to registry/reconfiguration; `XVE-SYS-0144`/`0153`/`0155` remain deferred to Security/deployment;
`XVE-SYS-0148`/`0150`/`0151` remain deferred to record/replay, edge/cloud, and Argus adapters; the
automatic recovery portion of `XVE-SYS-0158` remains deferred to Faults/Runtime. The capability
`ref002.disposition` stays `unchanged` (T036-SR-011). No allocated, deferred, architectural-target, or
superseded SADS requirement is reported as implemented.

## 7. Affected paths

### 7.1 Paths the T036 candidate changes

| Path | Change | Notes |
| --- | --- | --- |
| `docs/engineering/xcom/t036/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md` | add | this work-product set |
| `engineering/run_xcom_benchmarks.py` | add (implementation stage) | the task-owned benchmark harness with `--verify` |
| `engineering/project.json` | edit | current task T036 and accepted baseline `8ec69ddd34ed8c7a07adbcb631dcfb2da3faf15f` |
| `engineering/requirements/T036-STK-00{1..5}.json`, `T036-SR-0{01..12}.json` | add | current-task requirement records |
| `engineering/architecture/components/T036-SR-0{01..12}-CMP.json` | add | current-task component allocations |
| `engineering/unit-specifications/T036-SR-0{01..12}-U.json` | add | current-task unit specifications |
| `engineering/validation/scenarios/T036-VS-ACCUMULATED.json` | add | current-task validation scenario |
| `engineering/trace/links.json` | edit | additive T036 trace links and the inherited `engineering/project.json` `implemented_by` digest refresh |
| `docs/engineering/xcom/t010/unit-design.json`, `docs/engineering/xcom/t010/design-units.md` | edit | required planned→established path-status reconciliation for the now-present `docs/engineering/xcom/t036/` path (status field only) |
| `reports/review-index.md` | edit | T036 candidate section appended |
| `reports/xcom-queue/t036-benchmark.json` | add (implementation stage) | the exact-candidate benchmark evidence report |
| `specs/007-xcom-core/tasks.md` | edit | one-line T036 checkbox, **implementation stage only** |
| `reports/xcom-queue/t036-package.json` | add (implementation stage) | package record |

### 7.2 Consumed read-only (not changed by T036)

Every accepted `src/xverse/xcom/**` source, header, contract, schema, and fixture including the accepted
`observation.cpp`, `provider.cpp`, `loopback_provider.cpp`, and `synthetic_provider.{hpp,cpp}`; the
accepted benchmark fixture `tests/xcom/observation/integration/disabled_tap_benchmark.cpp` and its
`test_support.hpp`; every accepted test under `tests/xcom/**` and `tests/test_xcom_plan.py`;
`tests/xcom/contract_suites/**`; `proto/xverse/xcom/v1/tool_gateway.proto`;
`docs/engineering/xcom/task-ownership.*`; `docs/engineering/xcom/t00{7,8,9}/**` and
`docs/engineering/xcom/t010/unit-design.json`/`design-units.md` (read-only except the single
planned→established status field for `docs/engineering/xcom/t036/`);
`docs/engineering/xcom/t0{01..09}/**` and `docs/engineering/xcom/t0{11..35}/**`;
`docs/engineering/xcom/build-environment.md`; `docs/engineering/xcom/dependency-lock.md`;
`engineering/verification/measures/**`; and `specs/007-xcom-core/**` other than the T036 checkbox.

### 7.3 Explicitly not implemented by T036

The T035 verification matrix (accepted; consumed read-only), T037 Doxygen completion, T038 traceability
verifier and SADS disposition proof, the gRPC transport runtime linkage (`T032-GAP-01`), and any change
to an accepted production source, test, target, label, command, or expected value. External Codex review
and user acceptance remain T039/T041 and are deferred until the ordered backlog
`xcom-t030-t034-20260928` completes.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- **T036-GAP-01 — benchmark only.** T036 records a bounded prototype benchmark; it makes no
  deployed-service, network, transport, compatibility, timing, or production-readiness claim.
- **T036-GAP-02 — admitted envelope.** The admitted T011 prefix cannot link the gRPC transport runtime
  (`T032-GAP-01`); the benchmark covers the accepted in-process owned loopback and observation boundary
  only.
- **T036-GAP-03 — inherited environment caveats.** The T035-recorded host `AF_UNIX` `sun_path`
  constraint and the inherited Phase 6 conformance-pin status (T035 `L-T035-6`/`L-T035-7`) remain
  external to T036; T036 states whether its route is affected rather than re-claiming a T035 result.
- **T036-GAP-04 — no successor claim.** Doxygen (T037), traceability verifier/SADS (T038), review
  (T039/T040), and acceptance (T041) remain allocated.

### 8.2 Gaps with owning tasks

| Gap | Owner |
| --- | --- |
| Warning-free generated reference documentation | T037 |
| Traceability verifier and REF-002/SADS disposition | T038 |
| Independent review, acceptance-bundle inspection, user acceptance | T039/T040/T041 |
| gRPC transport runtime envelope | deferred capability gap `T032-GAP-01` |

### 8.3 Open items

- **T036-OPEN-01 — report is implementation-stage.** `reports/xcom-queue/t036-benchmark.json` is
  produced only at the implementation stage from executed measurements; the plan stage records the
  required schema and the exact harness/command route rather than fabricating results.
- **T036-OPEN-02 — harness is implementation-stage.** `engineering/run_xcom_benchmarks.py` is authored at
  the implementation stage; the plan records its required `--verify` contract and the measured cases.
- **T036-OPEN-03 — no inherited digest cascade.** T036 changes no production source and no build wiring,
  so no inherited `implemented_by` target or stage-result digest requires refresh except the
  `engineering/project.json` pointer that every task's trace currently references.
- **T036-OPEN-04 — unavailable inputs are blockers.** If the admitted offline input, the owned loopback
  build, or a timing measurement is unavailable at the candidate revision, the affected case is
  recorded as `blocked` (with the reason) and the candidate does not claim a pass; the plan does not
  substitute inferred or stale samples.
- **T036-OPEN-05 — planned→established path reconciliation.** The T010 unit design (`XCOM-DU-024`)
  declared `docs/engineering/xcom/t036/` as planned; because the plan stage now establishes that path,
  its status field is reconciled to established in `docs/engineering/xcom/t010/unit-design.json` and
  `design-units.md`. No unit, ownership, lifetime, bound, or requirement content changes.
- **T036-OPEN-06 — uncertainty is a declaration, not a guarantee.** The uncertainty statement records
  the observed dispersion under an uncontrolled shared host; it is not a production confidence interval
  and must not be read as one.
- **T036-OPEN-07 — SC-008 materialization.** The accepted register's `XCOM-SYS-SC-008` success criterion
  is the benchmark's spec anchor, but no `engineering/requirements/` record is materialized for it in the
  accepted baseline. T036 therefore traces its `refines` links to the materialized
  `XCOM-SYS-FR-014`/`FR-030`/`FR-029`/`FR-027`/`FR-035`/`SC-007` anchors and records the SC-008 mapping in
  §5, consistent with the accepted T035 precedent. Materializing an `XCOM-SYS-SC-008` record is a
  T008/T009 register action, not a T036 change.

## 9. Definition of done (requirements view)

T036 is done for a candidate revision when: every §4 requirement has at least one named executed case,
measure, or inspection; the harness runs the accepted owned loopback workload with the tap disabled and
enabled over controlled repeated paired samples; `reports/xcom-queue/t036-benchmark.json` carries
`environment`, `uncertainty`, `baseline`, `tap_disabled`, `tap_enabled`, `limitations`, raw samples,
method, and the exact-candidate identity; the gated `tap_disabled`-versus-same-baseline median regression is
compared against the 2% SC-008 threshold with an honest outcome while the enabled-versus-disabled regression
is recorded as an ungated observation; every result is public-safe; the accepted
registers are reconciled with the REF-002 disposition `unchanged` and nothing promoted; the
deterministic Phase 8 gate passes; and a separate DeepSeek internal review records its findings before
any repair. This does not constitute user acceptance, which remains T041.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary checks |
| --- | --- |
| T036-STK-001 | CHK-01, CHK-02, CHK-03, CHK-04, CHK-05 |
| T036-STK-002 | CHK-06, CHK-07, CHK-08, CHK-09 |
| T036-STK-003 | CHK-10, CHK-11 |
| T036-STK-004 | CHK-12, CHK-13 |
| T036-STK-005 | CHK-14, CHK-15, CHK-16 |
| T036-SR-001 | CHK-01, CHK-02 |
| T036-SR-002 | CHK-03 |
| T036-SR-003 | CHK-04 |
| T036-SR-004 | CHK-06, CHK-07 |
| T036-SR-005 | CHK-08 |
| T036-SR-006 | CHK-05 |
| T036-SR-007 | CHK-11 |
| T036-SR-008 | CHK-09 |
| T036-SR-009 | CHK-12, CHK-13 |
| T036-SR-010 | CHK-14 |
| T036-SR-011 | CHK-15, CHK-16 |
| T036-SR-012 | CHK-10, CHK-11 |
