# T012 Requirements — X-COM Subtree CMake/CTest Targets and Warning-as-Error Rules

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T012 (capability 007, slice `T-CORE`) |
| Task title | Add CMake/CTest targets and warning-as-error rules under `src/xverse/xcom/` |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `ade79ee1f73f176c0178b77d6b10ed8ba8587da6` |
| Authorization | capability 007 accepted design and bounded implementation authorization (ACC002/ACC004/ACC005/ACC006/ACC007/ACC010/ACC011/ACC014/ACC015); ADR-0018; ADR-0020 |
| Owning slice | `T-CORE` (T007 ownership register) |
| Predecessor | T011 (engineering baseline, admitted build envelope) |
| Successor tasks | T013–T016 (core types/lifecycle/provider/tests), then T017–T034, T035–T041 |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production
change and does not implement, accept, or integrate the candidate. The T012 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T012 — Add CMake/CTest targets and warning-as-error rules under `src/xverse/xcom/`.

## 2. Scope

### 2.1 In scope

- The **subtree build contract** for the X-COM C++ core under `src/xverse/xcom/`: the CMake target
  inventory, the C++20 target configuration, the warning-as-error application to every runtime and test
  target, CTest registration, and the sanctioned opt-in sanitizer selection.
- A **fail-closed subtree warning assertion**: configuration stops when the T011-admitted warning-as-error
  policy is absent or is not promoted to an error.
- Closure of the T012-owned portion of `T011-GAP-03`: the sanitizer opt-in is wired for the runtime and
  test targets (executed sanitizer evidence remains T035's, per T011-GAP-03).
- A deterministic, offline **build-contract CTest target** that verifies the effective policy without new
  repository source paths.
- The T012 repository-owned work products and the T012 package record.

### 2.2 Explicit exclusions (must remain absent from the T012 candidate)

No runtime behavior, public C++ interface, or `.cpp`/`.hpp` change; no new or edited test **source** under
`tests/`; no XDL, `xdl/`, or `proto/` change; no implementation of T013–T016, T017–T034, or T035–T041; no
network access, TCP listener, package manager, registry, or FetchContent resolution; no legacy repository,
binary, or workload access; no dependency version, license, hash, or admitted-input change; no rewrite or
weakening of an accepted ADR, requirement, contract, test, task-ownership path, REF-002 disposition, or
existing CTest name/label; no invention of a domain-specific primitive; no acceptance or integration of the
candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T012 |
| --- | --- | --- |
| Core value/contract/diagnostic/policy types | T013 | allocated; T012 compiles and registers them, does not implement them |
| Endpoint/route lifecycle with generation handles | T014 | allocated |
| Provider composition and owned loopback provider | T015 | allocated |
| Core unit and negative test **sources** | T016 | allocated; T012 registers the existing targets, adds no test source |
| Executed sanitizer/static-analysis/Doxygen evidence | T035–T037 | allocated (T011-GAP-03 execution half) |
| Independent review and user acceptance | T039/T041 | allocated |

## 3. Stakeholder requirements (`T012-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T012-STK-001**: Before the X-COM C++ core is accepted, the program **shall** have one repository-owned
  CMake/CTest build contract, physically under `src/xverse/xcom/`, that compiles every core runtime target
  with the T011-admitted toolchain and the shared warning-as-error policy.
- **T012-STK-002**: The subtree build contract **shall** fail closed at configure time when a required
  admitted input or the inherited warning-as-error policy is unavailable, and **shall** never silently
  produce a target set compiled with a weakened policy.
- **T012-STK-003**: The build contract **shall** expose a bounded, opt-in sanitizer capability for the
  runtime and test targets while leaving the default build unchanged.
- **T012-STK-004**: The build contract **shall** be deterministic and offline: identical admitted inputs
  produce the same target inventory and the same CTest registration, with no network access, ambient
  discovery, or package resolution.
- **T012-STK-005**: T012 **shall** preserve accepted intent: the delivered change is confined to the
  CMake/CTest contract and the T012 work products, and it **shall** neither change runtime behavior or a
  public interface nor promote any REF-002 or capability requirement.

## 4. Software/engineering requirements (`T012-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Implemented" means the repository-owned contract and its deterministic check exist and pass; it is
not a runtime or production claim.

### 4.1 Subtree build contract

- **T012-SR-001 [ubiquitous]**: Every C++ target defined under `src/xverse/xcom/` **shall** be compiled as
  C++20 with compiler extensions disabled, and **shall** not require a mandatory environment input beyond
  the T011 admitted inputs (`XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`) and the admitted test
  toolchain prefix (`XVERSE_XCOM_T025_TEST_TOOLCHAIN`) already required by the baseline.
  - Refines: `XCOM-BLD-001`; anchors FR-026, FR-030; Constitution X.
  - Verification intent: inspect `src/xverse/xcom/CMakeLists.txt` and the generated contract evidence; the
    compile-commands/build tree records `-std=c++20` without `-std=gnu++20`.
- **T012-SR-002 [ubiquitous]**: Every runtime library target under `src/xverse/xcom/` **shall** link the
  shared `xverse::xcom_warnings` interface target so that `-Wall -Wextra -Wpedantic -Werror` applies to it.
  - Refines: `XCOM-BLD-001`; anchors FR-029, FR-030.
  - Verification intent: the effective per-target warning options contain all four flags for each runtime
    target (compile-commands inspection), and the build-contract CTest check asserts the promoted policy.
- **T012-SR-003 [unwanted behaviour]**: If the shared warning target is absent, publishes no compile
  options, or does not promote warnings to errors, configuration **shall** terminate with a clear
  `FATAL_ERROR` and **shall** generate no target set presented as accepted.
  - Refines: `XCOM-BLD-001`, `XCOM-BLD-004`; anchors FR-025, FR-030.
  - Verification intent: a configure-time assertion plus negative probes that neutralise the policy.
- **T012-SR-004 [where-supported]**: The build **shall** expose an opt-in sanitizer selection
  `XVERSE_XCOM_SANITIZERS` over the supported set `{address, thread, undefined}`; the default **shall** be
  empty (no sanitizer), an unrecognised entry **shall** fail configuration, and the incompatible
  `address` + `thread` combination **shall** fail configuration.
  - Refines: `XCOM-BLD-001`; anchors FR-030; closes the T012-owned target half of `T011-GAP-03`.
  - Verification intent: positive selects configure and pass the contract check; unknown and conflicting
    selects fail closed; executed sanitizer runs remain T035's.
- **T012-SR-005 [ubiquitous]**: When a sanitizer selection is configured, its compile and link flags
  **shall** be applied uniformly to every runtime and test target; when the selection is empty, no
  sanitizer flag **shall** be added to any target.
  - Refines: `XCOM-BLD-001`; anchors FR-030.
  - Verification intent: default vs selected configurations compared through the build-contract evidence
    and compile-commands inspection.
- **T012-SR-006 [ubiquitous]**: CTest **shall** register the existing runtime unit, negative, external
  consumer, integration, and performance targets under `src/xverse/xcom/`, and **shall** preserve every
  baseline CTest name and label without weakening or removing a test.
  - Refines: `XCOM-BLD-001`; anchors FR-030; SC-009, SC-010.
  - Verification intent: `ctest -N` before/after name-set comparison; the new build-contract test is
    additive only.

### 4.2 Deterministic build-contract verification

- **T012-SR-007 [ubiquitous]**: A deterministic, offline build-contract CTest target **shall** verify the
  effective policy — C++20, extensions off, an error-promoting warning option with `-Wall -Wextra
  -Wpedantic`, a valid sanitizer selection, `BUILD_TESTING=ON`, and the expected runtime target inventory —
  and **shall** return a specific nonzero result naming the violated invariant on any mismatch.
  - Refines: `XCOM-BLD-004`; anchors FR-025, FR-030; SC-009.
  - Verification intent: the generated contract evidence plus the `xcom_build_contract` CTest target,
    exercised by controlled mutations (NEG-03..NEG-14).
- **T012-SR-008 [ubiquitous]**: The subtree build contract **shall** be offline and bounded: no network
  client or resolver, no package manager or registry, no FetchContent network resolution, no subprocess
  beyond the admitted preflight, and no thread beyond the configure/build/test processes.
  - Refines: `XCOM-BLD-003`; anchors FR-026, FR-027; Constitution X.
  - Verification intent: source inspection of the CMake files; the inherited offline admission gate remains
    the only external process invocation.
- **T012-SR-009 [ubiquitous]**: Committed build files and T012 work products **shall** contain no
  environment-specific absolute path (host prefix, package manifest, test-toolchain, temporary, or
  private-store path), credential, private address, unrestricted payload, or sensitive deployment value;
  generated contract evidence **shall** exist only beneath the build directory. The only absolute path a T012
  work product may retain is the repository harness gate invocation
  (`…/automation/xcom_feature_gate.py`), the same public workflow-automation path already retained by the
  T007–T011 records and disclosed as such.
  - Refines: Constitution X; anchors FR-027.
  - Verification intent: a public-safety scan of the candidate's committed files that distinguishes the
    workflow-automation gate path from environment-specific absolute paths.

### 4.3 Governance, traceability, and boundary

- **T012-SR-010 [ubiquitous]**: The T012 candidate **shall** change no runtime behavior, public C++
  interface, accepted test, ownership path, or accepted ADR/requirement; its only production path is the
  CMake/CTest contract under `src/xverse/xcom/`.
  - Refines: ADR-0018, ADR-0020; T007 global prohibitions.
  - Verification intent: `git diff --name-only <baseline>` boundary inspection (CHK-02, CHK-15).
- **T012-SR-011 [ubiquitous]**: The T012 candidate **shall** satisfy the deterministic Fabro gate for
  implementation tasks: the six named work products exist, at least one `src/xverse/xcom/**` CMake/`.cmake`
  path changes, `cmake`/`ctest` configure, build, discover, and pass, `git diff --check` is clean, and the
  T012 checkbox is marked complete **only** in the implementation stage.
  - Refines: ADR-0020; anchors FR-030; Constitution X.
  - Verification intent: `xcom_feature_gate.py verify T012 <baseline>`; `git diff --check`.
- **T012-SR-012 [ubiquitous]**: T012 **shall** reconcile with the T007 ownership register, the T008
  requirement register, the T009 architecture model, and the T010 unit design without rewriting or
  weakening them; **shall** keep the REF-002 disposition `unchanged` with an empty `promoted` list; and
  **shall** record honestly that the T008/T010 registers attribute `XCOM-SW-CORE-001` and `XCOM-SW-CORE-010`
  to T012 while the accepted `tasks.md` assigns the CORE contract/diagnostic source to T013, so this
  build-contract slice neither implements nor promotes those requirements.
  - Refines: `XCOM-SW-ENB-002`; anchors FR-030, FR-035; Constitution IX.
  - Verification intent: run the T007–T010 validators and inspect the REF-002 disposition.

## 5. Requirement-to-accepted-anchor traceability

| T012 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T012-STK-001 | `XCOM-BLD-001` | XCOM-SYS-FR-029/030 | FR-029, FR-030 | SC-009; IX, X |
| T012-STK-002 | `XCOM-BLD-001`, `XCOM-BLD-004` | XCOM-SYS-FR-025 | FR-025, FR-030 | IX, X |
| T012-STK-003 | `XCOM-BLD-001` | XCOM-SYS-FR-030 | FR-030 | X |
| T012-STK-004 | `XCOM-BLD-003` | XCOM-SYS-FR-026/027 | FR-026, FR-027 | X |
| T012-STK-005 | `XCOM-BLD-004` | XCOM-SYS-FR-030 | FR-030 | VII, IX |
| T012-SR-001 | `XCOM-BLD-001` | XCOM-SYS-FR-029 | FR-029 | X |
| T012-SR-002 | `XCOM-BLD-001` | XCOM-SYS-FR-029/030 | FR-029, FR-030 | SC-009 |
| T012-SR-003 | `XCOM-BLD-001/004` | XCOM-SYS-FR-025 | FR-025 | IX |
| T012-SR-004 | `XCOM-BLD-001` | XCOM-SYS-FR-030 | FR-030 | X |
| T012-SR-005 | `XCOM-BLD-001` | XCOM-SYS-FR-030 | FR-030 | X |
| T012-SR-006 | `XCOM-BLD-001` | XCOM-SYS-FR-030 | FR-030 | SC-009, SC-010 |
| T012-SR-007 | `XCOM-BLD-004` | XCOM-SYS-FR-025 | FR-025, FR-030 | SC-009 |
| T012-SR-008 | `XCOM-BLD-003` | XCOM-SYS-FR-026/027 | FR-026, FR-027 | X |
| T012-SR-009 | `XCOM-BLD-005` | XCOM-SYS-FR-027 | FR-027 | X |
| T012-SR-010 | Constitution VII/VIII; ADR-0018/0020 | - | FR-030 | VII, VIII, IX |
| T012-SR-011 | `XCOM-BLD-004`; ADR-0020 | - | FR-030 | X |
| T012-SR-012 | `XCOM-SW-ENB-002` | XCOM-SYS-FR-035 | FR-035, FR-030 | IX, X |

`XCOM-BLD-001`–`XCOM-BLD-005` are the accepted capability-007 build-foundation requirements
(`specs/008-feat-2fcd9f8f42214262/software-requirements.md`, repaired by `specs/009`/`specs/011`). They are
accepted text; T012 refines and consumes them and does not rewrite them.

## 6. REF-002 disposition

T012 owns no REF-002 communication ID. It provides part of the reproducible engineering baseline against
which the XVE-SYS-0139–0158 allocation is implemented and verified. T012 changes no required disposition:
the capability `ref002.disposition` stays `unchanged` with an empty `promoted` list (T012-SR-012). No
allocated, deferred, or target SADS requirement is reported as implemented.

## 7. Affected paths

### 7.1 Paths the T012 candidate changes (this task)

| Path | Change | Notes |
| --- | --- | --- |
| `src/xverse/xcom/CMakeLists.txt` | edit | the subtree CMake/CTest targets and warning-as-error/sanitizer rules (the only production path) |
| `docs/engineering/xcom/t012/requirements.md` | add | this document |
| `docs/engineering/xcom/t012/architecture.md` | add | boundary, components, invariants |
| `docs/engineering/xcom/t012/detailed-design.md` | add | rules, sanitizer mapping, contract evidence |
| `docs/engineering/xcom/t012/unit-specifications.md` | add | units, interfaces, bounds, traceability |
| `docs/engineering/xcom/t012/verification-plan.md` | add | named checks, commands, negative cases |
| `docs/engineering/xcom/t012/implementation.md` | add (implementation stage) | realized change and evidence |
| `docs/engineering/xcom/t012/internal-review.json` | add (review stage) | DeepSeek internal review |
| `specs/007-xcom-core/tasks.md` | edit T012 checkbox (implementation stage) | capability task ledger |
| `reports/xcom-queue/t012-package.json` | add (package stage) | exact-candidate package record |

### 7.2 Consumed, read-only foundation (not changed by T012)

| Path | Owner | Role for T012 |
| --- | --- | --- |
| `CMakeLists.txt` | shared (serialized) | root build contract, compile-only probes, policy evidence |
| `cmake/XComWarnings.cmake` | shared (serialized) | `xverse::xcom_warnings` interface target and apply function |
| `cmake/XComOfflineDependencies.cmake` | shared (serialized) | admitted inputs and imported dependency targets |
| `docs/engineering/xcom/build-environment.md`, `dependency-lock.md` | T-INTG (T035–T038) | admitted envelope, versions, hashes, licenses |
| `src/xverse/xcom/include/xverse/xcom/*.hpp`, `src/xverse/xcom/src/*.cpp` | T-CORE (T013–T015, T019) | compiled inputs; T012 changes none |
| `tests/xcom/**` | T-CORE / T-OBS | registered inputs; T012 changes none |

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- `T012-LIM-01` — Sanitizer **execution** evidence (running the suite under ASan/TSan/UBSan) is not produced
  by T012; only the opt-in wiring, fail-closed selection, and default-unchanged behavior are verified here.
  Executed evidence is T035's (`T011-GAP-03` execution half, unchanged).
- `T012-LIM-02` — Transitive host libraries and a pinned base-system ABI remain unlocked
  (`T011-LIM-01`); T012 inherits that limitation and claims none of it.
- `T012-LIM-03` — The subtree remains a source-level CMake contract, not a stable binary plugin ABI
  (capability plan, `Project Structure`); T012 introduces no dynamic discovery.

### 8.2 Gaps with owning tasks

| Gap | Description | Owner | Disposition |
| --- | --- | --- | --- |
| `T012-GAP-01` | The T008 register and T010 unit design attribute `XCOM-SW-CORE-001`/`XCOM-SW-CORE-010` to T012 while the accepted `tasks.md` assigns the CORE contract/diagnostic source to T013; both registers are `partial`/`unreconciled` (analysis A12; review 016 XCOM-NOSESN-08). | T008/T010 (registers); T013 (source) | allocated; T012 records the observation and promotes nothing |
| `T012-GAP-02` | The strict Doxygen C++ configuration remains open (`T011-GAP-01`). | T011 (admission), T037 (execution) | allocated; unchanged |
| `T012-GAP-03` | Candidate acceptance under capability 007 remains with T039/T041. | T039/T041 | allocated; T012 submits for review |

### 8.3 Open items

- `T012-OPEN-01` — Whether T015/T019 later split the activation-plan / provider targets into further
  libraries is a later slice's decision; T012 declares the current six-target inventory and the
  build-contract check will be updated by the owning task that changes the inventory, not silently here.
- `T012-OPEN-02` — The deterministic gate's process environment does not carry the three admitted
  offline inputs, so a bare gate configure fails closed at the baseline T025 test-toolchain admission
  check (`T012-IR-02`). The implementation stage resolves this only through the narrow A-1 cache
  fallback recorded in `verification-plan.md` §3.1, seeding the git-ignored gate build directory with
  the admitted inputs; no host path is committed and the hash-verified preflight is unchanged. The
  provisioning of those inputs remains outside the repository.

## 9. Definition of done (requirements view)

T012 is complete for this slice when: (a) the five plan-stage work products exist under
`docs/engineering/xcom/t012/` and are mutually consistent; (b) every requirement in §3–§4 has ≥ 1 named
check in `verification-plan.md`; (c) the implementation stage delivers the single CMake change, marks the
T012 checkbox, and records `implementation.md`; (d) the deterministic gate and the named checks pass at the
candidate revision; (e) the package record is written; and (f) a separate DeepSeek internal review records a
passing verdict with no findings. This does **not** constitute user acceptance, which remains T041.

## 10. Requirement-to-check index (implemented in `verification-plan.md`)

| Requirement | Primary check(s) |
| --- | --- |
| T012-STK-001 | CHK-02, CHK-03, CHK-10 |
| T012-STK-002 | CHK-04, NEG-03, NEG-04 |
| T012-STK-003 | CHK-05, CHK-06, CHK-07, NEG-05, NEG-06 |
| T012-STK-004 | CHK-09, CHK-11, CHK-12 |
| T012-STK-005 | CHK-15, CHK-16, CHK-18 |
| T012-SR-001 | CHK-03, CHK-11 |
| T012-SR-002 | CHK-03, CHK-09 |
| T012-SR-003 | CHK-04, NEG-03, NEG-04, NEG-13 |
| T012-SR-004 | CHK-06, CHK-07, NEG-05, NEG-06 |
| T012-SR-005 | CHK-05, CHK-06, CHK-07, NEG-07 |
| T012-SR-006 | CHK-08, CHK-10 |
| T012-SR-007 | CHK-09, NEG-08..NEG-14 |
| T012-SR-008 | CHK-12, CHK-13 |
| T012-SR-009 | CHK-13, NEG-18 |
| T012-SR-010 | CHK-02, CHK-15, NEG-19, NEG-21, NEG-22 |
| T012-SR-011 | CHK-17, NEG-01, NEG-02, NEG-15, NEG-16, NEG-20 |
| T012-SR-012 | CHK-16, CHK-18 |
