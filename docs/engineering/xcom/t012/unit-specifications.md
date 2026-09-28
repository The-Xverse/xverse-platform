# T012 Unit Specifications — Subtree Rules, Inventory, Verifier, and Work Products

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T012 |
| Stage / role | plan → unit specifications |
| Revision | 1 |
| Baseline revision | `ade79ee1f73f176c0178b77d6b10ed8ba8587da6` |
| Requirements authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Implementation artifacts | `src/xverse/xcom/CMakeLists.txt`; `docs/engineering/xcom/t012/*`; `reports/xcom-queue/t012-package.json` |

## 2. Scope, language, and conventions

T012 has two unit sets:

- **Build-contract units** (`T012-U-RULES`, `T012-U-WARN`, `T012-U-SAN`, `T012-U-INV`, `T012-U-CTEST`,
  `T012-U-CONTRACT`) — the CMake/CTest units realized in `src/xverse/xcom/CMakeLists.txt` and the files it
  generates beneath the build tree.
- **Work-product units** (`T012-U-W01`–`W06`) — the repository-owned artifacts T012 itself authors.

Conventions:

- All identifiers are stable ASCII tokens; the runtime target inventory order is declared and deterministic.
- Languages follow the accepted plan: CMake/CTest for the build-contract units; Markdown/JSON for the work
  products. No production `.cpp`/`.hpp` is authored by T012.
- **Lifetime** for the build-contract units is the configure/build/test invocation; for the work-product
  units it is the candidate lifetime.
- **Thread-safety** for every T012 unit is configure-time single-threaded or offline documentation; no unit
  starts a thread, and build/test parallelism is the caller's.
- **Doxygen** is not applicable: the CMake units define no C/C++ interface and the work products are
  Markdown/JSON. The C++ interfaces T012 compiles are documented by their owning tasks (T013–T015, T019).

**Resource and concurrency bounds (T012 units).** Configuration reads the repository and the T011 admitted
inputs only; it invokes no network client, package manager, registry, or FetchContent resolution, and its
only subprocess is the inherited admission preflight (120 s timeout). Generated evidence is written only
beneath the build directory. The verifier is a bounded `cmake -P` script that reads one small JSON file and
exits.

## 3. Build-contract units

### T012-U-RULES — Subtree rules block (`T12-CMP-RULES`)

- **Responsibility.** Declare the ordered runtime target inventory and define the subtree helpers
  (`xverse_xcom_assert_runtime_warning_policy`, `xverse_xcom_runtime_sanitizers`,
  `xverse_xcom_apply_runtime_rules`) before any target is defined.
- **Interface.** `set(XVERSE_XCOM_RUNTIME_TARGETS …)` and the three functions in
  `src/xverse/xcom/CMakeLists.txt`; consumes the root `xverse_xcom_apply_warnings` function.
- **Invariants.** The inventory is exactly the six baseline libraries in a declared order (`INV-12`); the
  helpers are defined before target definitions; the root warning/dependency modules are never redefined
  (`T12-XB-2`).
- **Failure semantics.** A missing target argument, or a target that does not exist, is a `FATAL_ERROR`;
  no partial configuration.
- **Lifetime/ownership.** Configure scope; shared (serialized) path `src/xverse/xcom/CMakeLists.txt`.
- **Bounds/thread-safety.** Configure-time, single-threaded, offline; no resource bound beyond the inherited
  preflight.
- **Requirements.** T012-STK-001, T012-SR-001, T012-SR-008.
- **Planned evidence.** CHK-03, CHK-12.

### T012-U-WARN — Warning-policy assertion (`T12-CMP-WARN`)

- **Responsibility.** Re-verify at subtree scope that the inherited `xverse::xcom_warnings` target exists
  and promotes warnings to errors before any accepted target is defined.
- **Interface.** `xverse_xcom_assert_runtime_warning_policy()`; reads
  `xverse::xcom_warnings` `INTERFACE_COMPILE_OPTIONS`.
- **Invariants.** Accepts `-Werror`, `/WX`, or `-Werror=…` as the error-promoting option; every runtime and
  test target still receives the full warning set via T012-U-INV (`INV-02`).
- **Failure semantics.** Missing target, empty options, or no error-promoting option → `FATAL_ERROR`
  (`INV-03`); no target is generated.
- **Lifetime/ownership.** Configure scope; shared path.
- **Bounds/thread-safety.** Configure-time, single-threaded.
- **Requirements.** T012-STK-002, T012-SR-002, T012-SR-003.
- **Planned evidence.** CHK-04, NEG-03, NEG-04, NEG-13.

### T012-U-SAN — Sanitizer selection (`T12-CMP-SAN`)

- **Responsibility.** Resolve the opt-in `XVERSE_XCOM_SANITIZERS` selection into compile/link flags, or none
  for the empty default.
- **Interface.** `xverse_xcom_runtime_sanitizers()`; publishes `xverse_xcom_sanitize_compile` /
  `xverse_xcom_sanitize_link` to the caller.
- **Invariants.** Supported set `{address, thread, undefined}`; default empty adds no flag; unknown entries
  and `address`+`thread` fail configuration (`INV-04`, `INV-05`); duplicate entries are de-duplicated.
- **Failure semantics.** Unsupported entry → `FATAL_ERROR` naming the entry; conflicting selection →
  `FATAL_ERROR` naming the conflict; both before any target is defined.
- **Lifetime/ownership.** Configure scope; shared path.
- **Bounds/thread-safety.** Configure-time, single-threaded, offline.
- **Requirements.** T012-STK-003, T012-SR-004.
- **Planned evidence.** CHK-06, CHK-07, NEG-05, NEG-06.

### T012-U-INV — Runtime inventory and uniform application (`T12-CMP-INV`)

- **Responsibility.** Apply the warning target and any selected sanitizer flags uniformly to every runtime
  and test target through one helper; keep the six-library inventory and aliases unchanged.
- **Interface.** `xverse_xcom_apply_runtime_rules(<target>)`, invoked for every existing
  `xverse_xcom_apply_warnings` call site.
- **Invariants.** Every target is C++20 without extensions (`INV-01`); no target escapes the warnings or the
  optional sanitizers (`INV-02`, `INV-04`); no target name, source list, link library, or include directory
  changes; the empty default is behaviorally identical to the baseline.
- **Failure semantics.** A missing target name is a `FATAL_ERROR`; a compile failure under a selected
  sanitizer is reported by the compiler, and no sanitizer is claimed executed.
- **Lifetime/ownership.** Configure/target scope; shared path.
- **Bounds/thread-safety.** Configure-time, single-threaded; adds no thread.
- **Requirements.** T012-SR-001, T012-SR-002, T012-SR-005.
- **Planned evidence.** CHK-03, CHK-05, CHK-06, CHK-07, NEG-07.

### T012-U-CTEST — CTest registration (`T12-CMP-CTEST`)

- **Responsibility.** Preserve the baseline CTest names and labels for the runtime unit, negative, external
  consumer, integration, and performance targets, and register the added build-contract test.
- **Interface.** The existing `add_test`/`gtest_discover_tests` calls and the added
  `add_test(NAME xcom_build_contract …)` with label `t012`.
- **Invariants.** Every baseline test name and label is preserved (`INV-06`); the addition is exactly one
  test with no new label family; test discovery finds at least one test (`T012-SR-011`).
- **Failure semantics.** A missing test source fails configuration; the deterministic gate fails when CTest
  discovers no test. No test is removed or renamed.
- **Lifetime/ownership.** Configure/CTest scope; shared path.
- **Bounds/thread-safety.** Registration is configure-time and deterministic; execution bounds are the
  existing tests'.
- **Requirements.** T012-SR-006.
- **Planned evidence.** CHK-08, CHK-10.

### T012-U-CONTRACT — Build-contract evidence and verifier (`T12-CMP-CONTRACT`)

- **Responsibility.** Emit the effective policy as generated evidence beneath the build tree and verify it
  with one deterministic, offline CTest target.
- **Interface.** Generated `xcom-runtime-contract.json` and `verify-xcom-runtime-contract.cmake`; CTest
  target `xcom_build_contract`.
- **Invariants.** Asserts C++20, extensions off, error-promoting warnings with `-Wall -Wextra -Wpedantic`,
  the expected inventory, `BUILD_TESTING=ON`, and a valid sanitizer selection (`INV-07`); reads only its own
  directory; exits nonzero naming the violated invariant.
- **Failure semantics.** Any policy deviation → CTest failure with a specific message; no success is
  reported for a weakened policy.
- **Lifetime/ownership.** Per-configuration generated artifacts; build-tree only (`INV-10`); shared path.
- **Bounds/thread-safety.** Offline, single-threaded, bounded to one small JSON read.
- **Requirements.** T012-STK-004, T012-SR-007, T012-SR-009.
- **Planned evidence.** CHK-09, CHK-11, NEG-08, NEG-09, NEG-10, NEG-11, NEG-12, NEG-14.

## 4. T012 work-product units

### T012-U-W01 — Requirements work product

- **Responsibility.** Register scope, stakeholder/engineering requirements, accepted anchors, affected
  paths, REF-002 disposition, gaps, and the requirement-to-check index.
- **Interface.** `docs/engineering/xcom/t012/requirements.md`.
- **Invariants.** Every requirement has an accepted anchor and ≥ 1 named check; no accepted intent is
  weakened; T012 and the baseline revision are identified.
- **Failure semantics.** A dangling anchor or unmapped requirement fails CHK-14.
- **Lifetime/ownership.** Candidate lifetime; `T-CORE` (T012).
- **Requirements.** T012-STK-005, T012-SR-009, T012-SR-010, T012-SR-012.
- **Planned evidence.** CHK-14, CHK-16, CHK-18.

### T012-U-W02 — Architecture work product

- **Responsibility.** Specify the subtree boundary, trust boundaries, components, data flow, interfaces, and
  quality attributes.
- **Interface.** `docs/engineering/xcom/t012/architecture.md`.
- **Invariants.** No prohibited element; dependency direction and domain neutrality preserved; consumed root
  modules never redefined.
- **Failure semantics.** A reverse dependency or prohibited element fails CHK-15/CHK-18.
- **Lifetime/ownership.** Candidate lifetime; `T-CORE` (T012).
- **Requirements.** T012-STK-005, T012-SR-009, T012-SR-010.
- **Planned evidence.** CHK-15, CHK-18.

### T012-U-W03 — Detailed-design work product

- **Responsibility.** Specify the rules, sanitizer mapping, inventory, contract evidence, failure semantics,
  bounds, and public-safety design.
- **Interface.** `docs/engineering/xcom/t012/detailed-design.md`.
- **Invariants.** Every failure maps to a stable behavior; no claim beyond the design.
- **Failure semantics.** An undocumented behavior or a claim beyond the design fails CHK-14.
- **Lifetime/ownership.** Candidate lifetime; `T-CORE` (T012).
- **Requirements.** T012-STK-005, T012-SR-009, T012-SR-010.
- **Planned evidence.** CHK-03, CHK-14.

### T012-U-W04 — Unit-specifications work product

- **Responsibility.** Specify the build-contract and work-product units with responsibility, interface,
  invariants, failure semantics, lifetime/ownership, bounds, requirements, and evidence.
- **Interface.** `docs/engineering/xcom/t012/unit-specifications.md`.
- **Invariants.** Every unit names its ownership, bounds, requirements, and planned evidence; requirement
  coverage is total.
- **Failure semantics.** A unit without bounds or evidence fails CHK-14.
- **Lifetime/ownership.** Candidate lifetime; `T-CORE` (T012).
- **Requirements.** T012-STK-005, T012-SR-009, T012-SR-010, T012-SR-012.
- **Planned evidence.** CHK-14, CHK-18.

### T012-U-W05 — Verification-plan work product

- **Responsibility.** Name the deterministic gate, nominal checks, negative cases, evidence retention, and
  exit criteria before implementation.
- **Interface.** `docs/engineering/xcom/t012/verification-plan.md`.
- **Invariants.** Every requirement maps to ≥ 1 check; every check states an expected result; negative cases
  fail closed.
- **Failure semantics.** A missing check or unstated expectation fails CHK-14.
- **Lifetime/ownership.** Candidate lifetime; `T-CORE` (T012).
- **Requirements.** T012-STK-005, T012-SR-009, T012-SR-010.
- **Planned evidence.** CHK-14, CHK-17.

### T012-U-W06 — Implementation record and package

- **Responsibility.** Record the realized change, commands, results, limitations, and trace links, and write
  the exact-candidate package record.
- **Interface.** `docs/engineering/xcom/t012/implementation.md`,
  `reports/xcom-queue/t012-package.json`, `docs/engineering/xcom/t012/internal-review.json`.
- **Invariants.** The package lists every changed path and hashes and binds the baseline revision; the
  record claims no acceptance; the review inventory equals the baseline diff.
- **Failure semantics.** A package that omits a changed path or binds a stale revision fails CHK-17.
- **Lifetime/ownership.** Candidate lifetime; `T-CORE` (T012); produced in the implementation/review stages.
- **Requirements.** T012-STK-005, T012-SR-009, T012-SR-010, T012-SR-011, T012-SR-012.
- **Planned evidence.** CHK-17, CHK-18.

## 5. Requirement-to-unit traceability

| Requirement | Unit(s) |
| --- | --- |
| T012-STK-001 | T012-U-RULES, T012-U-INV, T012-U-W01, T012-U-W02 |
| T012-STK-002 | T012-U-WARN |
| T012-STK-003 | T012-U-SAN |
| T012-STK-004 | T012-U-CONTRACT, T012-U-CTEST |
| T012-STK-005 | T012-U-W01, T012-U-W02, T012-U-W03, T012-U-W04, T012-U-W05, T012-U-W06 |
| T012-SR-001 | T012-U-RULES, T012-U-INV |
| T012-SR-002 | T012-U-WARN, T012-U-INV |
| T012-SR-003 | T012-U-WARN |
| T012-SR-004 | T012-U-SAN |
| T012-SR-005 | T012-U-SAN, T012-U-INV |
| T012-SR-006 | T012-U-CTEST |
| T012-SR-007 | T012-U-CONTRACT |
| T012-SR-008 | T012-U-RULES, T012-U-CONTRACT |
| T012-SR-009 | T012-U-CONTRACT, T012-U-W01, T012-U-W02, T012-U-W03, T012-U-W04, T012-U-W05, T012-U-W06 |
| T012-SR-010 | T012-U-W01, T012-U-W02, T012-U-W03, T012-U-W04, T012-U-W05, T012-U-W06 |
| T012-SR-011 | T012-U-W06 |
| T012-SR-012 | T012-U-W01, T012-U-W04, T012-U-W06 |

## 6. Coverage and exemptions

- Every T012 requirement in `requirements.md` §3–§4 is covered by ≥ 1 build-contract or work-product unit.
- `T012-STK-003`/`T012-SR-004` cover only the **wiring and fail-closed selection** of sanitizers; executed
  sanitizer evidence is exempt from T012 and owned by T035 (`T012-LIM-01`, `T011-GAP-03`, unchanged).
- No unit is exempt without a reason and an owning task, and no exemption closes a gap silently.
