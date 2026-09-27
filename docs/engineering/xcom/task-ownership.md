# X-COM Task Ownership Register

> Deterministic projection of `task-ownership.json` (schema version 1).
> Do not edit by hand; regenerate from the model and re-run
> `scripts/validate_xcom_task_ownership.py --check-human`.

## Register identity

| Field | Value |
| --- | --- |
| Task | T007 |
| Schema version | 1 |
| Baseline revision | `923a6db65aafbcdbf33a1461e93622777e902deb` |
| Candidate revision rule | Every candidate records its own exact revision and the exact accepted predecessor revision it derives from; acceptance is per candidate and is never inherited from a sibling or inferred from source presence. |
| Slices | 7 |

## Shared path rule

A shared build or specification path is edited by one slice at a time, in the declared dependency order, under the owning task's exact candidate revision and retained evidence.  A shared path is never claimed as exclusive, and no exclusive path is declared shared.

## Authorization records

`ACC001`, `ACC002`, `ACC003`, `ACC004`, `ACC005`, `ACC006`, `ACC007`, `ACC008`, `ACC009`, `ACC010`, `ACC011`, `ACC012`, `ACC013`, `ACC014`, `ACC015`, `ADR-0018`, `ADR-0019`, `ADR-0020`

## Global prohibitions

- no TCP listener
- no execution of any legacy binary or workload
- no external network peer
- no modification of any legacy The-Xverse repository
- no public evidence containing sensitive deployment values, private addresses, unrestricted payloads, or absolute host paths
- no rewrite of an accepted ADR or weakening of an existing requirement or test

## Shared (serialized) paths

- `CMakeLists.txt`
- `cmake/XComOfflineDependencies.cmake`
- `cmake/XComWarnings.cmake`
- `docs/engineering/xcom/task-ownership.json`
- `docs/engineering/xcom/task-ownership.md`
- `scripts/validate_xcom_task_ownership.py`
- `specs/007-xcom-core/tasks.md`
- `src/xverse/xcom/CMakeLists.txt`

## Slices (declared order)

### T-CORE — C++ core: contracts, items, diagnostics, providers, routes, loopback, external-tool boundary

**Purpose.** Contract/item/diagnostic/policy value types, bounded endpoint/route lifecycle with exact generation-bound handles, explicit provider composition and the owned loopback provider, the versioned local tool gateway, and reusable provider/observer/stimulation/gateway contract suites.

| Field | Value |
| --- | --- |
| Owning tasks | T012, T013, T014, T015, T016, T030, T031, T032, T033, T034 |
| Authorized baseline | `923a6db65aafbcdbf33a1461e93622777e902deb` |
| Authorization refs | `ACC002`, `ACC004`, `ACC005`, `ACC006`, `ACC007`, `ACC010`, `ACC011`, `ACC014`, `ACC015`, `ADR-0018`, `ADR-0019`, `ADR-0020` |
| Dependencies | T-ENABLER |
| Acceptance gate | per-task exact-candidate verification and independent review, then T035/T039/T041 |
| REF-002 disposition | unchanged |

Exclusive paths:

- `docs/engineering/xcom/t012/`
- `docs/engineering/xcom/t013/`
- `docs/engineering/xcom/t014/`
- `docs/engineering/xcom/t015/`
- `docs/engineering/xcom/t016/`
- `docs/engineering/xcom/t030/`
- `docs/engineering/xcom/t031/`
- `docs/engineering/xcom/t032/`
- `docs/engineering/xcom/t033/`
- `docs/engineering/xcom/t034/`
- `proto/xverse/xcom/v1/tool_gateway.proto`
- `reports/xcom-queue/t012-package.json`
- `reports/xcom-queue/t013-package.json`
- `reports/xcom-queue/t014-package.json`
- `reports/xcom-queue/t015-package.json`
- `reports/xcom-queue/t016-package.json`
- `reports/xcom-queue/t030-package.json`
- `reports/xcom-queue/t031-package.json`
- `reports/xcom-queue/t032-package.json`
- `reports/xcom-queue/t033-package.json`
- `reports/xcom-queue/t034-package.json`
- `scripts/validate_xcom_core_types.py`
- `scripts/validate_xcom_endpoint_route_lifecycle.py`
- `scripts/validate_xcom_provider_loopback.py`
- `src/xverse/xcom/include/xverse/xcom/contract.hpp`
- `src/xverse/xcom/include/xverse/xcom/core_types.hpp`
- `src/xverse/xcom/include/xverse/xcom/diagnostic.hpp`
- `src/xverse/xcom/include/xverse/xcom/endpoint_route_lifecycle.hpp`
- `src/xverse/xcom/include/xverse/xcom/item.hpp`
- `src/xverse/xcom/include/xverse/xcom/loopback_provider.hpp`
- `src/xverse/xcom/include/xverse/xcom/provider.hpp`
- `src/xverse/xcom/include/xverse/xcom/result.hpp`
- `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp`
- `src/xverse/xcom/include/xverse/xcom/value.hpp`
- `src/xverse/xcom/src/contract.cpp`
- `src/xverse/xcom/src/core.cpp`
- `src/xverse/xcom/src/diagnostic.cpp`
- `src/xverse/xcom/src/endpoint_route_lifecycle.cpp`
- `src/xverse/xcom/src/item.cpp`
- `src/xverse/xcom/src/loopback_provider.cpp`
- `src/xverse/xcom/src/provider.cpp`
- `src/xverse/xcom/src/tool_gateway.cpp`
- `src/xverse/xcom/src/value.cpp`
- `tests/xcom/core_types/`
- `tests/xcom/endpoint_route_lifecycle/`
- `tests/xcom/provider_loopback/`
- `tests/xcom/tool_gateway/`

Shared paths:

- `CMakeLists.txt`
- `cmake/XComOfflineDependencies.cmake`
- `cmake/XComWarnings.cmake`
- `specs/007-xcom-core/tasks.md`
- `src/xverse/xcom/CMakeLists.txt`

Required evidence:

- `contract`
- `deterministic-diagnostics`
- `later-integration-run`
- `negative`
- `no-tcp-listener`
- `queue-bound`
- `recovery`
- `second-provider-replaceability`
- `unit`
- `version-rejection`

Prohibitions:

- no TCP listener
- no execution of any legacy binary or workload
- no external network peer
- no modification of any legacy The-Xverse repository
- no public evidence containing sensitive deployment values, private addresses, unrestricted payloads, or absolute host paths
- no rewrite of an accepted ADR or weakening of an existing requirement or test

Reconciliation:

- T012: unreconciled — source present in the baseline but the capability task checkbox is open and no accepted exact-candidate revision is recorded (analysis A12; review 016 XCOM-NOSESN-08)
- T013: unreconciled — source present in the baseline but the capability task checkbox is open and no accepted exact-candidate revision is recorded (analysis A12; review 016 XCOM-NOSESN-08)
- T014: unreconciled — source present in the baseline but the capability task checkbox is open and no accepted exact-candidate revision is recorded (analysis A12; review 016 XCOM-NOSESN-08)
- T015: unreconciled — source present in the baseline but the capability task checkbox is open and no accepted exact-candidate revision is recorded (analysis A12; review 016 XCOM-NOSESN-08)
- T016: unreconciled — source present in the baseline but the capability task checkbox is open and no accepted exact-candidate revision is recorded (analysis A12; review 016 XCOM-NOSESN-08)
- T030: allocated
- T031: allocated
- T032: allocated
- T033: allocated
- T034: allocated

### T-XDL — XDL compiler: io.xverse.xcom Profile v0.1, activation-plan v1, bounded C++ decode

**Purpose.** Validate the io.xverse.xcom Profile v0.1 and canonical activation-plan v1 schema and digest/provenance contract; deterministic Profile-aware plan compilation in src/xverse_xdl/xcom_plan.py; bounded C++ plan decoding with independent version/digest/capability checks; ordering-equivalence, malformed-plan, drift, bound, and regression tests.

| Field | Value |
| --- | --- |
| Owning tasks | T017, T018, T019, T020 |
| Authorized baseline | `923a6db65aafbcdbf33a1461e93622777e902deb` |
| Authorization refs | `ACC002`, `ACC003`, `ACC013`, `ACC014`, `ACC015`, `ADR-0018`, `ADR-0020` |
| Dependencies | T-CORE |
| Acceptance gate | per-task exact-candidate verification and independent review, then T035/T039/T041 |
| REF-002 disposition | unchanged |

Exclusive paths:

- `docs/engineering/xcom/t017/`
- `docs/engineering/xcom/t018/`
- `docs/engineering/xcom/t019/`
- `docs/engineering/xcom/t020/`
- `reports/xcom-queue/t017-package.json`
- `reports/xcom-queue/t018-package.json`
- `reports/xcom-queue/t019-package.json`
- `reports/xcom-queue/t020-package.json`
- `scripts/validate_xcom_plan.py`
- `specs/007-xcom-core/contracts/xdl-profile.md`
- `src/xverse/xcom/contracts/v1/activation-plan.schema.json`
- `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp`
- `src/xverse/xcom/src/activation_plan.cpp`
- `src/xverse_xdl/xcom_plan.py`
- `tests/test_xcom_plan.py`
- `tests/xcom/activation_plan/`
- `xdl/profiles/xcom-v0.1.schema.json`

Shared paths:

- `CMakeLists.txt`
- `cmake/XComOfflineDependencies.cmake`
- `cmake/XComWarnings.cmake`
- `specs/007-xcom-core/tasks.md`
- `src/xverse/xcom/CMakeLists.txt`

Required evidence:

- `bound`
- `cpp-decoder-tests`
- `drift`
- `malformed-plan`
- `ordering-equivalence`
- `profile-schema-validation`
- `python-suite`
- `regression`

Prohibitions:

- no TCP listener
- no execution of any legacy binary or workload
- no external network peer
- no modification of any legacy The-Xverse repository
- no public evidence containing sensitive deployment values, private addresses, unrestricted payloads, or absolute host paths
- no rewrite of an accepted ADR or weakening of an existing requirement or test

Reconciliation:

- T017: allocated
- T018: allocated
- T019: allocated
- T020: allocated

### T-OBS — Observation boundary: immutable records, bounded taps, synthetic sink

**Purpose.** Immutable observation records/filters/payload policy/tap handles, bounded best-effort drop/coalesce and explicit lossless-validation modes, synthetic sink with failure/disconnect isolation and visible counters, and their tests.

| Field | Value |
| --- | --- |
| Owning tasks | T021, T022, T023, T024 |
| Authorized baseline | `923a6db65aafbcdbf33a1461e93622777e902deb` |
| Authorization refs | `ACC005`, `ACC010`, `ACC011`, `ACC014`, `ACC015`, `ADR-0019`, `ADR-0020` |
| Dependencies | T-CORE |
| Acceptance gate | per-task exact-candidate verification and independent review, then T035/T036/T039/T041 |
| REF-002 disposition | unchanged |

Exclusive paths:

- `docs/engineering/xcom/t021/`
- `docs/engineering/xcom/t022/`
- `docs/engineering/xcom/t023/`
- `docs/engineering/xcom/t024/`
- `reports/xcom-queue/t021-package.json`
- `reports/xcom-queue/t022-package.json`
- `reports/xcom-queue/t023-package.json`
- `reports/xcom-queue/t024-package.json`
- `scripts/validate_xcom_observation.py`
- `src/xverse/xcom/include/xverse/xcom/observation.hpp`
- `src/xverse/xcom/src/observation.cpp`
- `tests/xcom/observation/`

Shared paths:

- `CMakeLists.txt`
- `cmake/XComOfflineDependencies.cmake`
- `cmake/XComWarnings.cmake`
- `specs/007-xcom-core/tasks.md`
- `src/xverse/xcom/CMakeLists.txt`

Required evidence:

- `controlled-payload-view`
- `degraded-validity`
- `disabled-tap-performance`
- `metadata-only-zero-payload`
- `ordering`
- `safe-detach`
- `saturation`

Prohibitions:

- no TCP listener
- no execution of any legacy binary or workload
- no external network peer
- no modification of any legacy The-Xverse repository
- no public evidence containing sensitive deployment values, private addresses, unrestricted payloads, or absolute host paths
- no rewrite of an accepted ADR or weakening of an existing requirement or test

Reconciliation:

- T021: unreconciled — source present in the baseline but the capability task checkbox is open and no accepted exact-candidate revision is recorded (analysis A12; review 016 XCOM-NOSESN-08)
- T022: unreconciled — source present in the baseline but the capability task checkbox is open and no accepted exact-candidate revision is recorded (analysis A12; review 016 XCOM-NOSESN-08)
- T023: unreconciled — source present in the baseline but the capability task checkbox is open and no accepted exact-candidate revision is recorded (analysis A12; review 016 XCOM-NOSESN-08)
- T024: unreconciled — source present in the baseline but the capability task checkbox is open and no accepted exact-candidate revision is recorded (analysis A12; review 016 XCOM-NOSESN-08)

### T-STIM — Validation stimulation boundary: time authority, permit/session, journal, guard, actions

**Purpose.** Explicit time-authority interface, local permit/session lifecycle, bounded durable intent/outcome journal, fail-closed pre-emission guard, guarded injection/invocation/exclusive service emulation, and the full mismatch/lifecycle/concurrency tests.

| Field | Value |
| --- | --- |
| Owning tasks | T025, T026, T027, T028, T029 |
| Authorized baseline | `923a6db65aafbcdbf33a1461e93622777e902deb` |
| Authorization refs | `ACC006`, `ACC010`, `ACC011`, `ACC014`, `ACC015`, `ADR-0019`, `ADR-0020` |
| Dependencies | T-CORE, T-OBS |
| Acceptance gate | per-task exact-candidate verification and independent review, then T035/T039/T041 |
| REF-002 disposition | unchanged |

Exclusive paths:

- `docs/engineering/xcom/t025/`
- `docs/engineering/xcom/t026/`
- `docs/engineering/xcom/t027/`
- `docs/engineering/xcom/t028/`
- `docs/engineering/xcom/t029/`
- `reports/xcom-queue/t025-package.json`
- `reports/xcom-queue/t026-package.json`
- `reports/xcom-queue/t027-package.json`
- `reports/xcom-queue/t028-package.json`
- `reports/xcom-queue/t029-package.json`
- `scripts/check_xcom_t025_test_dependencies.py`
- `src/xverse/xcom/include/xverse/xcom/stimulation_journal.hpp`
- `src/xverse/xcom/include/xverse/xcom/validation_session.hpp`
- `src/xverse/xcom/src/stimulation_journal.cpp`
- `src/xverse/xcom/src/validation_session.cpp`
- `tests/xcom/stimulation_journal/`
- `tests/xcom/validation_session/`

Shared paths:

- `CMakeLists.txt`
- `cmake/XComOfflineDependencies.cmake`
- `cmake/XComWarnings.cmake`
- `specs/007-xcom-core/tasks.md`
- `src/xverse/xcom/CMakeLists.txt`

Required evidence:

- `deterministic-concurrency`
- `drain-terminal`
- `journal-before-emission`
- `journal-failure-recovery`
- `lease-conflicts`
- `loop-bounds`
- `permit-action-mismatch-matrix`
- `quotas`
- `synthetic-provenance`
- `unmapped-clocks`
- `zero-emission-after-rejection`

Prohibitions:

- no TCP listener
- no execution of any legacy binary or workload
- no external network peer
- no modification of any legacy The-Xverse repository
- no public evidence containing sensitive deployment values, private addresses, unrestricted payloads, or absolute host paths
- no rewrite of an accepted ADR or weakening of an existing requirement or test

Reconciliation:

- T025: accepted (`4b01586b438a8587d231ee8828d896c206c06a96`) — accepted T025 successor; implementation cc9044ab28d0ae9b4df8447072f68b73b3db184a
- T026: allocated
- T027: allocated
- T028: allocated
- T029: allocated

### T-INTG — Integration, evidence, and documentation

**Purpose.** Run the full unit/contract/integration/negative/concurrency/sanitizer/static/Python checks and controlled benchmarks; produce warning-free Doxygen; validate Spec Kit plus REF-002 requirements/design/code/test traceability and public-safe logs; assemble the exact-candidate evidence bundle; own the dependency-admission environment (T011) and build documentation.

| Field | Value |
| --- | --- |
| Owning tasks | T035, T036, T037, T038, T040 |
| Authorized baseline | `923a6db65aafbcdbf33a1461e93622777e902deb` |
| Authorization refs | `ACC012`, `ACC014`, `ACC015`, `ADR-0020` |
| Dependencies | T-ENABLER, T-OBS, T-STIM, T-XDL |
| Acceptance gate | T040 inspection, then T039 independent review and T041 user acceptance |
| REF-002 disposition | unchanged |

Exclusive paths:

- `docs/engineering/xcom/build-environment.md`
- `docs/engineering/xcom/dependency-lock.md`
- `docs/engineering/xcom/t035/`
- `docs/engineering/xcom/t036/`
- `docs/engineering/xcom/t037/`
- `docs/engineering/xcom/t038/`
- `docs/engineering/xcom/t040/`
- `docs/xcom/`
- `reports/xcom-queue/t035-package.json`
- `reports/xcom-queue/t036-package.json`
- `reports/xcom-queue/t037-package.json`
- `reports/xcom-queue/t038-package.json`
- `reports/xcom-queue/t040-package.json`
- `scripts/check_doxygen.py`
- `scripts/xcom_dependency_preflight.py`
- `specs/007-xcom-core/reference-traceability.md`

Shared paths:

- `CMakeLists.txt`
- `cmake/XComOfflineDependencies.cmake`
- `cmake/XComWarnings.cmake`
- `specs/007-xcom-core/tasks.md`
- `src/xverse/xcom/CMakeLists.txt`

Required evidence:

- `benchmark-environment`
- `bounded-logs`
- `command-argv`
- `doxygen-warning-free`
- `evidence-index`
- `exit-codes`
- `hashes`
- `outcomes`
- `package-manifest`
- `raw-manifests`
- `traceability-matrix`

Prohibitions:

- no TCP listener
- no execution of any legacy binary or workload
- no external network peer
- no modification of any legacy The-Xverse repository
- no public evidence containing sensitive deployment values, private addresses, unrestricted payloads, or absolute host paths
- no rewrite of an accepted ADR or weakening of an existing requirement or test

Reconciliation:

- T035: allocated
- T036: allocated
- T037: allocated
- T038: allocated
- T040: allocated

### T-ENABLER — Engineering-baseline enabler group (not an implementation slice)

**Purpose.** Requirements/traceability (T008), architecture/boundaries/cross-language contracts (T009), unit design/ownership/lifetime/thread-safety/failure semantics/bounds/Doxygen plan (T010), and compiler/build/dependency admission with hashes, licenses, and generated-code provenance (T011).

| Field | Value |
| --- | --- |
| Owning tasks | T008, T009, T010, T011 |
| Authorized baseline | `923a6db65aafbcdbf33a1461e93622777e902deb` |
| Authorization refs | `ACC012`, `ACC014`, `ACC015`, `ADR-0020` |
| Dependencies | T007 |
| Acceptance gate | reviewed work products and a passing dependency-admission preflight before T011 completes |
| REF-002 disposition | unchanged |

Exclusive paths:

- `docs/adr/`
- `docs/engineering/xcom/t007/`
- `docs/engineering/xcom/t008/`
- `docs/engineering/xcom/t009/`
- `docs/engineering/xcom/t010/`
- `docs/engineering/xcom/t011/`
- `reports/xcom-queue/t007-package.json`
- `reports/xcom-queue/t008-package.json`
- `reports/xcom-queue/t009-package.json`
- `reports/xcom-queue/t010-package.json`
- `reports/xcom-queue/t011-package.json`
- `scripts/validate_xcom_architecture_contracts.py`
- `scripts/validate_xcom_requirements_traceability.py`
- `specs/007-xcom-core/analysis.md`
- `specs/007-xcom-core/checklists/`
- `specs/007-xcom-core/contracts/communication-plan.md`
- `specs/007-xcom-core/contracts/observation.md`
- `specs/007-xcom-core/contracts/provider.md`
- `specs/007-xcom-core/contracts/tool-gateway.md`
- `specs/007-xcom-core/contracts/validation-tool.md`
- `specs/007-xcom-core/data-model.md`
- `specs/007-xcom-core/plan.md`
- `specs/007-xcom-core/quickstart.md`
- `specs/007-xcom-core/research.md`
- `specs/007-xcom-core/spec.md`

Shared paths:

- `docs/engineering/xcom/task-ownership.json`
- `docs/engineering/xcom/task-ownership.md`
- `scripts/validate_xcom_task_ownership.py`
- `specs/007-xcom-core/tasks.md`

Required evidence:

- `dependency-admission-preflight`
- `reviewed-work-products`

Prohibitions:

- no TCP listener
- no execution of any legacy binary or workload
- no external network peer
- no modification of any legacy The-Xverse repository
- no public evidence containing sensitive deployment values, private addresses, unrestricted payloads, or absolute host paths
- no rewrite of an accepted ADR or weakening of an existing requirement or test

Reconciliation:

- T008: allocated
- T009: allocated
- T010: allocated
- T011: allocated

### T-REVIEW — Independent review and explicit user acceptance

**Purpose.** The separate read-only review that records every finding before any repair, and the explicit user acceptance that closes the capability; owns capability-level review and acceptance records.

| Field | Value |
| --- | --- |
| Owning tasks | T039, T041 |
| Authorized baseline | `923a6db65aafbcdbf33a1461e93622777e902deb` |
| Authorization refs | `ACC012`, `ACC015`, `ADR-0020` |
| Dependencies | T-INTG |
| Acceptance gate | separate read-only review with no unresolved blocker or major finding, followed by explicit user acceptance; a repair creates a successor candidate and repeats affected verification and review |
| REF-002 disposition | unchanged |

Exclusive paths:

- `docs/engineering/xcom/t039/`
- `docs/engineering/xcom/t041/`
- `docs/reviews/`
- `reports/xcom-queue/t039-package.json`
- `reports/xcom-queue/t041-package.json`

Shared paths:

- `specs/007-xcom-core/tasks.md`

Required evidence:

- `acceptance-decision-record`
- `per-task-internal-review-verdicts`
- `review-report-no-unresolved-blocker-or-major`

Prohibitions:

- no TCP listener
- no execution of any legacy binary or workload
- no external network peer
- no modification of any legacy The-Xverse repository
- no public evidence containing sensitive deployment values, private addresses, unrestricted payloads, or absolute host paths
- no rewrite of an accepted ADR or weakening of an existing requirement or test

Reconciliation:

- T039: allocated
- T041: allocated

## Task assignment

| Task | Owner |
| --- | --- |
| T007 | T-PRODUCING |
| T008 | T-ENABLER |
| T009 | T-ENABLER |
| T010 | T-ENABLER |
| T011 | T-ENABLER |
| T012 | T-CORE |
| T013 | T-CORE |
| T014 | T-CORE |
| T015 | T-CORE |
| T016 | T-CORE |
| T017 | T-XDL |
| T018 | T-XDL |
| T019 | T-XDL |
| T020 | T-XDL |
| T021 | T-OBS |
| T022 | T-OBS |
| T023 | T-OBS |
| T024 | T-OBS |
| T025 | T-STIM |
| T026 | T-STIM |
| T027 | T-STIM |
| T028 | T-STIM |
| T029 | T-STIM |
| T030 | T-CORE |
| T031 | T-CORE |
| T032 | T-CORE |
| T033 | T-CORE |
| T034 | T-CORE |
| T035 | T-INTG |
| T036 | T-INTG |
| T037 | T-INTG |
| T038 | T-INTG |
| T039 | T-REVIEW |
| T040 | T-INTG |
| T041 | T-REVIEW |

## Dependency edges

- T007 -> T-ENABLER
- T-ENABLER -> T-CORE
- T-ENABLER -> T-INTG
- T-CORE -> T-XDL
- T-CORE -> T-OBS
- T-CORE -> T-STIM
- T-OBS -> T-STIM
- T-XDL -> T-INTG
- T-OBS -> T-INTG
- T-STIM -> T-INTG
- T-INTG -> T-REVIEW
- T025 -> T026
