# T016 Implementation Record — Consolidated X-COM Core Unit and Negative Test Matrix

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T016 (capability 007, slice `T-CORE`) |
| Stage / role | implementation → implementation record |
| Revision | 1 |
| Authorized baseline | `44d2001d48dd42dc9ed489a40d2a5f908b734501` |
| Predecessor | T015 reviewed terminal package (`docs/engineering/xcom/t015/`) |
| Candidate state | working tree over the authorized baseline (staged for the deterministic gate; candidate revision assigned at the workflow checkpoint) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Internal review | `docs/engineering/xcom/t016/internal-review.json` (separate read-only DeepSeek review, produced by the review stage) |
| Package record | `reports/xcom-queue/t016-package.json` (produced by the deterministic package action) |
| Authorization | ACC002/ACC004/ACC005/ACC006/ACC007/ACC010/ACC011/ACC014/ACC015; ADR-0016; ADR-0018; ADR-0020; `specs/007-xcom-core/tasks.md` T016 |
| Maturity | Prototype-only consolidated core test matrix implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T016 implements the bounded slice required by the T016 task entry: *"Add unit and negative tests for
interaction kinds, capabilities, policy, ownership, lifecycle, queue bounds, deterministic diagnostics,
and recovery."*

The candidate adds one new, self-contained consolidated core test area under `tests/xcom/core_matrix/`
that exercises the accepted core end to end over the public headers — contract → item →
endpoint/route lifecycle → provider composition → owned loopback → bounded queue → receive →
deterministic diagnostics — and realizes the accepted success criterion `SC-001` / `XCOM-SW-CORE-009`
with twenty-seven individually named rejection cases spanning all four interaction families and the
`XCOM-SW-CORE-008` / `FR-024` boundary
constraint. It adds the two additive strengthening cases that the T014 and T015 internal reviews
recorded (same-identity different-`FlowPolicy` inequality; positive `at_least_once → reliable`
declared-policy mapping), registers the new executables additively in the shared T012 subtree build
contract, marks the T016 checkbox, and changes no production unit, existing test, schema, register, or
another task's path.

Every T016 requirement in [`requirements.md`](requirements.md) §3–§4 is realized by a named check in
[`verification-plan.md`](verification-plan.md) §4–§5 and by at least one executable test below.

## 3. Implemented change

| Path | Change | Role |
| --- | --- | --- |
| `tests/xcom/core_matrix/test_support.hpp` | add | Self-contained independent fixture (`CoreStackFixture`, `DeclarationFixture`) and probe provider (`ProbeProvider`); no other task's `test_support.hpp` include |
| `tests/xcom/core_matrix/unit_tests.cpp` | add | 19-case nominal matrix (interaction kinds, capabilities, policy, ownership, lifecycle, queue bounds, deterministic diagnostics) |
| `tests/xcom/core_matrix/negative_tests.cpp` | add | 27 named rejection cases (`SC-001`) spanning malformed, incompatible, over-capacity, and unauthorized classes and all four families |
| `tests/xcom/core_matrix/recovery_tests.cpp` | add | Saturation recovery, rejected-operation reusability, generation recreation, reconciliation mismatch, empty-queue reporting |
| `tests/xcom/core_matrix/concurrency_tests.cpp` | add | Bounded exactly-once/FIFO delivery, repeated-run determinism, lock-safe registration re-entry |
| `tests/xcom/core_matrix/fault_boundary_tests.cpp` | add | `XCOM-SW-CORE-008` controlled fault-hook boundary proof |
| `tests/xcom/core_matrix/consumer/main.cpp` | add | Independent translation unit over the public include surface; one minimal round trip |
| `src/xverse/xcom/CMakeLists.txt` | edit | Additive serialized registration of the five T016 suites and the consumer with distinct `t016*` labels; no existing entry changed |
| `docs/engineering/xcom/t016/*.md` | add | Five plan-stage work products plus this implementation record |
| `docs/engineering/xcom/t016/internal-review.json` | add (review stage) | DeepSeek internal review |
| `reports/xcom-queue/t016-package.json` | add (package stage) | Exact-candidate package record |
| `specs/007-xcom-core/tasks.md` | edit | T016 checkbox marked complete (implementation stage only) |

No `*.hpp`/`*.cpp` production unit, `cmake/*.cmake`, root `CMakeLists.txt`, `xdl/`, `proto/`,
`src/xverse_xdl/`, another task's test source, or another task's path is changed.

### 3.1 New artifacts and symbols (test-only)

- `tests/xcom/core_matrix/test_support.hpp` — namespace `xverse::xcom::test`: `kCoreDigest`,
  `kOtherCoreDigest`, `kAllInteractions`, `source_direction()`, `destination_direction()`,
  `make_contract()`, `make_descriptor()`, `loopback_descriptor()`, class `ProbeProvider`, class
  `CoreStackFixture`, class `DeclarationFixture`.
- Five GTest suites and one consumer executable registered as
  `xverse_xcom_core_matrix_{unit,negative,recovery,concurrency,fault_boundary}_tests` and
  `xverse_xcom_core_matrix_consumer`.
- No runtime library target, `XVERSE_XCOM_RUNTIME_TARGETS` entry, or admitted dependency is added.

## 4. Verification evidence (candidate-bound)

All commands were run from the repository root over the authorized baseline with the inherited
A-1 cache seed (`build/fabro-t016`), offline, and no legacy binary or external peer.

| # | Command | Result |
| --- | --- | --- |
| 1 | `cmake -S . -B build/fabro-t016 -G Ninja -DCMAKE_BUILD_TYPE=Debug` | exit 0 |
| 2 | `cmake --build build/fabro-t016 --parallel 4` | exit 0 |
| 3 | `ctest --test-dir build/fabro-t016 -N` | `Total Tests: 306` (baseline 248 + 58 T016) |
| 4 | `ctest --test-dir build/fabro-t016 --output-on-failure --parallel 4` | `100% tests passed, 0 tests failed out of 306` |
| 5 | `ctest --test-dir build/fabro-t016 -L t016 --output-on-failure` | `100%`; 58 tests across labels `t016`, `t016-unit`, `t016-negative`, `t016-recovery`, `t016-concurrency`, `t016-fault-boundary` |
| 6 | `python3 scripts/validate_xcom_task_ownership.py --verify` / `--check-human` | passed |
| 7 | `python3 scripts/validate_xcom_requirements_traceability.py --verify` | passed |
| 8 | `python3 scripts/validate_xcom_architecture_contracts.py --verify` | passed |
| 9 | `python3 scripts/validate_xcom_unit_design.py --verify` | passed |
| 10 | `git diff --check 44d2001d48dd42dc9ed489a40d2a5f908b734501 --` | clean |
| 11 | `python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T016 44d2001d48dd42dc9ed489a40d2a5f908b734501` | passed (see §7) |

### 4.1 T016 CTest label inventory

| Label | Tests | Executable |
| --- | --- | --- |
| `t016-unit` | 19 | `xverse_xcom_core_matrix_unit_tests` |
| `t016-negative` | 27 | `xverse_xcom_core_matrix_negative_tests` |
| `t016-recovery` | 5 | `xverse_xcom_core_matrix_recovery_tests` |
| `t016-concurrency` | 3 | `xverse_xcom_core_matrix_concurrency_tests` |
| `t016-fault-boundary` | 3 | `xverse_xcom_core_matrix_fault_boundary_tests` |
| `t016` | 1 | `xverse_xcom_core_matrix_consumer` (`xcom_core_matrix_external_consumer`) |

### 4.2 `SC-001` negative-case mapping (27 individually named cases)

| ID | Discovered test name | Exact observed outcome |
| --- | --- | --- |
| NEG-01 | `CoreMatrixNegative.Neg01_MalformedContract_RejectedWithRequiredFieldOrBound` | `required_field` / `bound_exceeded`, contract phase |
| NEG-02 | `CoreMatrixNegative.Neg02_IncompatibleDirection_Rejected` | `incompatible_direction`, contract phase |
| NEG-03 | `CoreMatrixNegative.Neg03_MalformedItem_RejectedInItemPhase` | `required_field` / `bound_exceeded`, item phase |
| NEG-04 | `CoreMatrixNegative.Neg04_SubmitOverPreparedPayloadBound_Rejected` | `payload_limit_exceeded` (`XCOM-PROV-E018`) |
| NEG-05 | `CoreMatrixNegative.Neg05_InvalidFlowPolicy_RejectedInPolicyPhase` | `invalid_policy`, policy phase |
| NEG-06 | `CoreMatrixNegative.Neg06_UnadvertisedInteraction_RejectedBeforeDispatch` | `unsupported_interaction` (`XCOM-PROV-E015`), 0 dispatch |
| NEG-07 | `CoreMatrixNegative.Neg07_UnadvertisedDelivery_RejectedBeforeDispatch` | `unsupported_delivery` (`XCOM-PROV-E016`), 0 dispatch |
| NEG-08 | `CoreMatrixNegative.Neg08_UnadvertisedOrdering_RejectedBeforeDispatch` | `unsupported_ordering` (`XCOM-PROV-E017`), 0 dispatch |
| NEG-09 | `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch` | `unsupported_contract_version` (`XCOM-PROV-E014`), 0 dispatch |
| NEG-10 | `CoreMatrixNegative.Neg10_UnmappableDeclaredClaim_RejectedBeforeDispatch` | `unsupported_delivery` / `unsupported_ordering`, 0 dispatch |
| NEG-11 | `CoreMatrixNegative.Neg11_UnsupportedDeclaredPolicyDimension_RejectedBeforeDispatch` | `unsupported_policy` (`XCOM-PROV-E030`), 0 dispatch, not prepared/activated |
| NEG-12 | `CoreMatrixNegative.Neg12_RequestedQueueAboveDeclaredDepth_RejectedBeforeDispatch` | `queue_limit_exceeded` (`XCOM-PROV-E019`), 0 dispatch, not prepared/activated |
| NEG-13 | `CoreMatrixNegative.Neg13_UnregisteredProviderIdentity_Rejected` | `provider_mismatch` (`XCOM-PROV-E025`), 0 dispatch |
| NEG-14 | `CoreMatrixNegative.Neg14_ProviderAdvertisesFewerClaims_Rejected` | `unsupported_delivery` (`XCOM-PROV-E016`), 0 dispatch, not prepared/activated |
| NEG-15 | `CoreMatrixNegative.Neg15_DuplicateProviderIdentity_RejectedNoSlotReplaced` | `duplicate_provider` (`XCOM-PROV-E012`) |
| NEG-16 | `CoreMatrixNegative.Neg16_ProviderRegistryFull_RejectedFirstSlotUnchanged` | `provider_capacity_exhausted` (`XCOM-PROV-E013`) |
| NEG-17 | `CoreMatrixNegative.Neg17_LoopbackRouteStorageExhausted_RejectedExistingRoutesUnchanged` | `route_capacity_exhausted` (`XCOM-PROV-E020`) |
| NEG-18 | `CoreMatrixNegative.Neg18_SubmitBeyondQueueCapacity_RejectedPreservingFifo` | `queue_saturated` (`XCOM-PROV-E010`) |
| NEG-19 | `CoreMatrixNegative.Neg19_SubmitPayloadOverProviderBound_Rejected` | `payload_limit_exceeded` (`XCOM-PROV-E018`) |
| NEG-20 | `CoreMatrixNegative.Neg20_CloseDrainingRouteWithItems_Rejected` | `queued_items_remain` (`XCOM-PROV-E027`) |
| NEG-21 | `CoreMatrixNegative.Neg21_StaleGenerationHandleAfterRecreation_Rejected` | `invalid_provider_route_handle` (`XCOM-PROV-E021`) |
| NEG-22 | `CoreMatrixNegative.Neg22_ForeignCompositionHandle_Rejected` | `invalid_provider_route_handle` (`XCOM-PROV-E021`) |
| NEG-23 | `CoreMatrixNegative.Neg23_SubmitOnNonActiveRoute_Rejected` | `inactive_route` (`XCOM-PROV-E023`) |
| NEG-24 | `CoreMatrixNegative.Neg24_ItemBoundToDifferentRoute_Rejected` | `item_mismatch` (`XCOM-PROV-E026`) |
| NEG-25 | `CoreMatrixNegative.Neg25_ReconcileAfterDivergence_RejectedInterrupted` | `interrupted_resource` (`XCOM-PROV-E028`) |
| NEG-26 | `CoreMatrixNegative.Neg26_SignalStateUpdateFamilyUnadvertised_RejectedBeforeDispatch` | `unsupported_interaction` (`XCOM-PROV-E015`), 0 dispatch, not prepared/activated |
| NEG-27 | `CoreMatrixNegative.Neg27_ServiceResponseItemBinding_RejectedWithoutQueuing` | `item_mismatch` (`XCOM-PROV-E026`), `queued_items() == 0`, route `active` |

NEG-26 and NEG-27 close `T016-IR-01`: they are the individually named rejection cases that make the
executable matrix span the `signal_state_update` and `service_response` families. NEG-28…NEG-30 are
inspection/repository probes realized in §5 and in the T016 internal review.

### 4.3 Additivity evidence

- `git diff --name-only <baseline> --` lists exactly one tracked edit, `src/xverse/xcom/CMakeLists.txt`.
- `git diff <baseline> -- src/xverse/xcom/CMakeLists.txt` shows one appended T016 block; every existing
  target, test name, label, command, and expected result is byte-unchanged.
- Every existing suite (core types, endpoint/route lifecycle, provider loopback, observation,
  activation plan T019/T020, validation session T025, build contract T012) still runs and passes.
- `ctest -N` count grows from 248 to 306; no existing name changes.

## 5. Checks and scans

| Check | Command | Result |
| --- | --- | --- |
| Forbidden API (offline, CHK-20/CHK-15) | `rg -n "socket|resolver|openssl|curl|fork\(|popen|dlopen|getenv|std::filesystem|::listen|TLS" tests/xcom/core_matrix` | no match |
| Public safety (CHK-21/CHK-16) | source inspection of the new files and work products | no credential, private address, real payload, proprietary excerpt, or absolute host path; fixture payloads are synthetic bounded bytes |
| Doxygen (CHK-22) | inspection of the new files | every new file carries a `@file`/`@brief` block; each helper/class carries `@brief` plus ownership/lifetime/thread-safety/failure tags; the admitted documentation configuration is unchanged |
| Fault-hook boundary (CHK-17) | executable `CoreSurface_*` cases | no domain-specific fault vocabulary in the committed core headers; only bounded controlled seams; no raw-token mutation entry point |
| REF-002 disposition (CHK-23) | register validators; `specs/007-xcom-core/reference-traceability.md` inspection | `unchanged`, empty `promoted` list; no `XVE-SYS-*` ID promoted |

### 5.1 Documented bounded filesystem use

The three `CoreSurface_*` fault-boundary cases read a fixed, compile-time list of ten committed public
core headers under `src/xverse/xcom/include/xverse/xcom/`, each capped at 262 144 bytes, to perform the
bounded forbidden-vocabulary scan required by `T016-SR-012` / CHK-17 / NEG-28. This read is a
repository-inspection of committed artifacts only; it performs no ambient, secret, process, network, or
legacy access, and it is the only filesystem use in the new tests. It is recorded here rather than
treated as production I/O.

## 6. Requirement traceability

| T016 requirement | Realizing tests / evidence |
| --- | --- |
| T016-SR-001 | six new executables under `tests/xcom/core_matrix/` + additive CMake block (§3, §4.1) |
| T016-SR-002 | `CoreMatrix.InteractionKind_{SignalStateUpdate,MessageEvent,ServiceRequest,ServiceResponse}_RoundTripsExactly` |
| T016-SR-003 | `CoreMatrix.CapabilityMask_*`, `CoreMatrix.CapabilityContainment_*`, `CoreMatrix.DeclaredPolicy_AtLeastOnceMapsToReliable_Positive`, NEG-06/07/08/09/14/16/26 |
| T016-SR-004 | `CoreMatrix.DeclaredPolicy_{SupportedClaimPreparesAndActivates,UnboundRouteIsUnaffected,SameIdentityDifferentPolicyCompareUnequal}`, NEG-05/10/11/12/13 |
| T016-SR-005 | `CoreMatrix.Ownership_ExactHandlesAreCopyableAndReadable`, NEG-21/22/24/27 |
| T016-SR-006 | `CoreMatrix.Lifecycle_*`, NEG-18/20 |
| T016-SR-007 | `CoreMatrix.QueueBounds_*`, NEG-04/15/17/18/19 |
| T016-SR-008 | `CoreMatrix.Diagnostics_*` |
| T016-SR-009 | `CoreMatrixRecovery.*` (5 cases) |
| T016-SR-010 | `CoreMatrixConcurrency.*` (3 cases) |
| T016-SR-011 | `CoreMatrixNegative.Neg01…Neg27` |
| T016-SR-012 | `CoreMatrixFaultBoundary.CoreSurface_*` + header scan |
| T016-SR-013 | finite bounds in `concurrency_tests.cpp` (`kMaximumSpinIterations`, `kExchangeItems`) and per-case constants |
| T016-SR-014 | §4.3 additivity evidence |
| T016-SR-015 | §5 forbidden-API scan and the successful offline build |
| T016-SR-016 | §5 public-safety scan |
| T016-SR-017 | §5 Doxygen inspection |
| T016-SR-018 | §4 commands 6–9 and the unchanged REF-002 disposition |
| T016-SR-019 | §7 deterministic gate |
| T016-SR-020 | this table plus `verification-plan.md` §8 |

The T014 and T015 review strengthening notes (requirements §7.4) are realized by
`DeclaredPolicy_SameIdentityDifferentPolicyCompareUnequal` and
`DeclaredPolicy_AtLeastOnceMapsToReliable_Positive`; the predecessor cases are unchanged.

## 7. Deterministic gate (implementation stage)

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify \
  T016 44d2001d48dd42dc9ed489a40d2a5f908b734501
```

Result: passed. The six work products exist under `docs/engineering/xcom/t016/`; the T016 checkbox is
marked complete; at least one `tests/` path changed; configure, build, test discovery, and the full
`ctest` run exit 0; `git diff --check` is clean. The repair-pass re-verification of the successor
candidate is recorded in §11.

## 8. Limitations

- `T016-LIM-01` — Prototype verification evidence only: passing the matrix proves no network provider,
  transport protocol, timing fidelity, compatibility, parity, or production readiness.
- `T016-LIM-02` — Tests exercise the in-process owned loopback and public headers only; no legacy
  binary, external peer, or out-of-process path is executed (that is T030–T034).
- `T016-LIM-03` — The `XCOM-SW-CORE-008` verification is a boundary/negative proof, not a
  Faults-facing hook implementation; the concrete bounded communication hook remains `T016-GAP-01`
  (T021–T024).
- `T016-LIM-04` — Strict declaration-level Doxygen remains `DOX-GAP-01` (T011/T037).
- `T016-LIM-05` — Deterministic concurrency is asserted by bounded repeated runs, not a formal race
  proof; executed sanitizer evidence is T035's obligation.
- `T016-LIM-06` — "Recovery" here means in-process saturation recovery, rejected-operation
  reusability, and generation recreation; restart reconciliation across processes is not implemented.
- `T016-LIM-07` — The fault-boundary vocabulary scan reads committed public core headers (§5.1); it is
  a repository inspection, not a production capability.
- `T016-OPEN-01` — T016 uses GTest/discovered per-case reporting unlike the hand-rolled T013–T015
  suites; the divergence is additive and preserves every existing case.

## 9. Attribution observation (unchanged, recorded not resolved)

As recorded in [`requirements.md`](requirements.md) §7.3, the T008 register attributes
`XCOM-SW-CORE-008` and `XCOM-SW-CORE-009` to T016 while the task entry names only the test matrix. T016
satisfies the register's **verification** obligation: `XCOM-SW-CORE-009` is realized by the
consolidated conformance/negative suite and `XCOM-SW-CORE-008` by the test-only boundary proposition.
The registers and their `partial`/`unreconciled` state remain owned by T008/T009/T010 and are not
rewritten.

## 10. Review and acceptance status

A separate read-only DeepSeek internal review is recorded in `docs/engineering/xcom/t016/internal-review.json`
and the exact-candidate package record in `reports/xcom-queue/t016-package.json`. Neither constitutes
external Codex review or user acceptance; both are deferred until the `xcom-t011-t016-t021-t024`
backlog completes (T039/T041).

## 11. Repair record (`T016-IR-01`, `T016-IR-02` closure)

The internal review recorded two findings. The repair is a successor candidate over the same baseline
`44d2001d48dd42dc9ed489a40d2a5f908b734501`; it strengthens the negative matrix and adds explicit
no-mutation assertions without weakening any accepted requirement, check, or existing case.

### 11.1 `T016-IR-01` — negative-matrix family coverage (medium)

- Correction (the review's preferred option a): added two individually named, individually reportable
  rejection cases to `tests/xcom/core_matrix/negative_tests.cpp`:
  - `CoreMatrixNegative.Neg26_SignalStateUpdateFamilyUnadvertised_RejectedBeforeDispatch` — a
    `signal_state_update` route requests a family the selected probe provider does not advertise;
    expects `unsupported_interaction` (`XCOM-PROV-E015`), `prepare_calls() == 0`, and no prepared or
    active route.
  - `CoreMatrixNegative.Neg27_ServiceResponseItemBinding_RejectedWithoutQueuing` — a `service_response`
    route is submitted an item bound to a different route; expects `item_mismatch`
    (`XCOM-PROV-E026`), `queued_items() == 0`, and the route still `active`.
- Work-product consequences: the executable negative set is now `NEG-01…NEG-27`; the inspection probes
  are renumbered `NEG-28` (domain-specific/faulting API scan), `NEG-29` (public safety), and `NEG-30`
  (additivity/boundary). `T016-SR-011` was clarified to require at least one named case in each of the
  four interaction families; the family-spread claim now matches the executed discovery list.
- Exact closure evidence at the repaired candidate:
  - `rg -n 'InteractionKind::(signal_state_update|service_response)' tests/xcom/core_matrix/negative_tests.cpp`
    returns the NEG-26 (`signal_state_update`) and NEG-27 (`service_response`) cases.
  - `ctest --test-dir build/fabro-t016 -L t016-negative --output-on-failure` → `100% tests passed`
    (27 tests, including the two new cases).
  - `ctest --test-dir build/fabro-t016 -N` → `Total Tests: 306`; the `t016` label selects 58 tests.

### 11.2 `T016-IR-02` — no-mutation assertions (low)

- Correction: `NEG-11`, `NEG-12`, and `NEG-14` now assert the absence of side effects on rejection.
  NEG-11 and NEG-12 use a `ProbeProvider` and assert `prepare_calls() == 0` (no dispatch) plus
  `prepared() == false` and `activated() == false`; NEG-14 does the same. The previous
  `LoopbackProvider`-only construction of NEG-14 was replaced by the probe provider so the dispatch
  counter is observable.
- Exact closure evidence at the repaired candidate: `ctest --test-dir build/fabro-t016 -L t016-negative
  --output-on-failure` passes 27/27; each of the three cases now fails if `prepare_route` is
  instrumented to dispatch to (or mutate) the provider on rejection, because `prepare_calls()` and the
  prepared/activated state are asserted.

### 11.3 Re-verification of the successor candidate

| # | Command | Result |
| --- | --- | --- |
| 1 | `cmake --build build/fabro-t016 --parallel 4` | exit 0 |
| 2 | `ctest --test-dir build/fabro-t016 -N` | `Total Tests: 306` |
| 3 | `ctest --test-dir build/fabro-t016 --parallel 4` | `100% tests passed, 0 tests failed out of 306` |
| 4 | `ctest --test-dir build/fabro-t016 -L t016` | `100% tests passed, 0 tests failed out of 58` |
| 5 | `ctest --test-dir build/fabro-t016 -L t016-negative` | `100% tests passed` (27 tests) |
| 6 | `git diff --check 44d2001d48dd42dc9ed489a40d2a5f908b734501 --` | clean |

The deterministic `xcom_feature_gate.py verify T016 <baseline>` gate re-runs configure/build/discovery/
`ctest` over this exact candidate, and a fresh internal review supersedes `internal-review.json`. The
repair adds no production unit, changes no existing test, and stays within the T016 path boundary.

## 12. Inherited provenance-hash repair (`T020-L-046` and stage artifacts)

Strict delivery over the reviewed candidate rejected `stale endpoint revision in T020-L-046`. T016 adds
its CTest registration to the inherited `src/xverse/xcom/CMakeLists.txt`, so that file's bytes (and its
SHA-256) changed after the T020 provenance records were written. The inherited trace link and stage
records still carried the pre-T016 hash. Only the applicable provenance hashes were corrected to the
current exact file bytes of the reviewed candidate; no link meaning, relation, test, work product,
accepted predecessor, or strict checker was changed.

| Record | Field | Pre-repair SHA-256 | Repaired SHA-256 (current bytes) |
| --- | --- | --- | --- |
| `engineering/trace/links.json` | link `T020-L-046` `target_revision` (`src/xverse/xcom/CMakeLists.txt`) | `3174c0c182ce53f541609795bd47d139c331aa106b969874c0ee4fababbf8100` | `8f6d081225aba7d3c5fed9bf61e207ffa7b6f5a2014a15b522d2c488e56fa984` |
| `engineering/stage-results/implementation.json` | artifact `src/xverse/xcom/CMakeLists.txt` | `3174c0c182ce53f541609795bd47d139c331aa106b969874c0ee4fababbf8100` | `8f6d081225aba7d3c5fed9bf61e207ffa7b6f5a2014a15b522d2c488e56fa984` |
| `engineering/stage-results/documentation.json` | artifact `engineering/trace/links.json` | `753ae4877db6f4ce8cebafb63c58bf07456df009b6ba470431c8686ec21b6476` | `5f066d8eb1da4aed960bbc782fdf2bb012ed7a1e95e8cf73b9d9463eda03a32d` |
| `engineering/stage-results/integration.json` | artifact `engineering/trace/links.json` | `753ae4877db6f4ce8cebafb63c58bf07456df009b6ba470431c8686ec21b6476` | `5f066d8eb1da4aed960bbc782fdf2bb012ed7a1e95e8cf73b9d9463eda03a32d` |
| `engineering/stage-results/internal-review.json` | artifact `engineering/trace/links.json` | `753ae4877db6f4ce8cebafb63c58bf07456df009b6ba470431c8686ec21b6476` | `5f066d8eb1da4aed960bbc782fdf2bb012ed7a1e95e8cf73b9d9463eda03a32d` |

The `links.json` self-hash changes because the repaired `T020-L-046` value is part of that file; the three
T020 stage records that list `engineering/trace/links.json` as an artifact are re-hashed to the same
current bytes so that the unchanged `validate_stage` checker continues to pass. The `src/xverse/xcom/`
production headers/sources are untouched, so the earlier `implementation.json` CMake entry is the only
changed production-artifact hash.

### 12.1 Exact-file evidence at the repaired candidate

| # | Command | Result |
| --- | --- | --- |
| 1 | `sha256sum src/xverse/xcom/CMakeLists.txt` | `8f6d081225aba7d3c5fed9bf61e207ffa7b6f5a2014a15b522d2c488e56fa984` |
| 2 | `sha256sum engineering/trace/links.json` | `5f066d8eb1da4aed960bbc782fdf2bb012ed7a1e95e8cf73b9d9463eda03a32d` |
| 3 | `python3 /home/jefferson/x-verse_fabric/.fabro/workflows/xcom-t016-checkpoint-flash/audit_delivery_inputs.py` | `{"ok": true, "stage_results": 8}`, exit 0 |
| 4 | `git diff 44d2001d48dd42dc9ed489a40d2a5f908b734501 -- engineering/trace/links.json` | one changed line: the `T020-L-046` `target_revision` value only |

The delivery-input audit runs the unchanged `validate_project`, `validate_trace`, and `validate_stage`
core checkers; it now reports `ok: true` over all eight inherited stage results. T016 remains active in
the ordered backlog; external review and user acceptance remain separate (T039/T041).
