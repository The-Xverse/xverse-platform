# T012 Architecture — Subtree Build/Test Boundary and Warning-as-Error Enforcement

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T012 (capability 007, slice `T-CORE`) |
| Stage / role | plan → architecture |
| Revision | 1 |
| Baseline revision | `ade79ee1f73f176c0178b77d6b10ed8ba8587da6` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture.md` (`XCOM-CMP-*`, `XCOM-XB-*`); `docs/engineering/xcom/t011/architecture.md` (`XCOM-BLD-*`) |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T012 occupies the seam between the **admitted engineering baseline** (T011) and the **X-COM C++ core
source** (T013–T016, T019). It does not implement communication behavior. It establishes, physically under
`src/xverse/xcom/`, the CMake/CTest contract by which the core targets are configured, compiled with a
fail-closed warning-as-error policy, optionally instrumented with sanitizers, and registered for CTest.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract (this document)
   → T013 core types → T014 lifecycle → T015 provider/loopback → T016 core tests
   → { T-XDL, T-OBS, T-STIM } → T-INTG (T035–T038) → T-REVIEW (T039/T041)
```

T012 is a **production-path** slice: the deterministic gate requires exactly one changed CMake/`.cmake` path
under `src/xverse/xcom/`. The change is confined to build/test configuration; no compiled translation unit,
public header, or existing test source changes, so the runtime object code and public interfaces are
preserved.

## 3. Boundary and context

### 3.1 System context

```text
   ┌────────────────────────── T011 admitted envelope (read-only inputs) ───────────────────────────┐
   │  XVERSE_XCOM_TOOLCHAIN  XVERSE_XCOM_PACKAGE_MANIFEST  XVERSE_XCOM_T025_TEST_TOOLCHAIN          │
   │  imported targets: nlohmann_json::nlohmann_json, protobuf::*, gRPC::*                          │
   └───────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                   │ consumed, never redefined
   ┌──────────────── repo root build contract (CMakeLists.txt, cmake/*.cmake) ──────────────────────┐
   │  xverse_xcom_configure_warnings()  xverse_xcom_apply_warnings()  xverse::xcom_warnings          │
   │  Ninja-only · C++20 · BUILD_TESTING=ON · policy evidence xcom-build-policy.json                 │
   └───────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                   │ include
   ┌──────────────────── T012 subtree build/test contract (src/xverse/xcom/CMakeLists.txt) ──────────┐
   │  assert_runtime_warning_policy()  select_sanitizers()  apply_runtime_rules()                    │
   │  runtime target inventory (6 libraries + aliases) · CTest registration · contract verifier      │
   └───────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                   │ compiles / registers
   ┌──────────────────────────── core source and tests (read-only for T012) ─────────────────────────┐
   │  src/xverse/xcom/src/*.cpp  include/xverse/xcom/*.hpp  tests/xcom/**                            │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T12-XB-1` Configure versus run | CMake configure-time policy resolution and generated evidence | compiled/linked object code and executed tests | T012 resolves rules only; it adds no runtime path and changes no translation unit. |
| `T12-XB-2` Subtree versus root | `src/xverse/xcom/CMakeLists.txt` consumes the root modules | `CMakeLists.txt`, `cmake/XComWarnings.cmake`, `cmake/XComOfflineDependencies.cmake` | The subtree never redefines the root warning or dependency functions; it asserts their policy and applies it. |
| `T12-XB-3` Default versus sanitizer | the empty default selection (no flags) | the opt-in `XVERSE_XCOM_SANITIZERS` selection | The default build is byte-identical to the baseline; sanitizers are additive and fail closed on an invalid or conflicting selection. |
| `T12-XB-4` Repository versus build output | committed CMake files, work products, package record | generated contract evidence and build trees | Generated evidence exists only beneath the build directory and carries no source-controlled absolute path. |
| `T12-XB-5` Public versus private | package names, flags, target names, diagnostic messages | host prefix/manifest/toolchain absolute paths | Committed files exclude absolute host paths and sensitive values. |

### 3.3 Prohibited elements (must remain absent)

No TCP listener, no external network peer, no package manager or registry, no FetchContent network
resolution, no legacy repository read/write, no legacy binary or workload execution, no dynamic plugin
discovery, no domain-specific primitive, and no new mandatory environment input. These inherit the T007
global prohibitions, T011's envelope rules, and the constitution.

## 4. Components

Each component maps to a unit in `unit-specifications.md`.

### 4.1 Subtree rule components

- **`T12-CMP-RULES`** — `src/xverse/xcom/CMakeLists.txt` rule section: the declared runtime target
  inventory, the warning-policy assertion, the sanitizer selection, and the per-target application helper.
- **`T12-CMP-WARN`** — the fail-closed assertion `xverse_xcom_assert_runtime_warning_policy()`: the subtree
  re-verifies that the inherited `xverse::xcom_warnings` target exists and promotes warnings to errors.
- **`T12-CMP-SAN`** — the sanitizer selector `xverse_xcom_runtime_sanitizers()`: validates
  `XVERSE_XCOM_SANITIZERS`, rejects unknown and conflicting selections, and returns the compile/link flags.
- **`T12-CMP-INV`** — the runtime target inventory and its uniform configuration: `XVERSE_XCOM_RUNTIME_TARGETS`
  plus `xverse_xcom_apply_runtime_rules(<target>)`, which applies the warning target and any selected
  sanitizer flags to each runtime and test target.

### 4.2 Verification components

- **`T12-CMP-CTEST`** — CTest registration: the existing `add_test`/`gtest_discover_tests` calls and their
  labels remain authoritative; T012 preserves every baseline name and label and adds one target.
- **`T12-CMP-CONTRACT`** — the generated build-contract evidence (`xcom-runtime-contract.json` under the
  build tree) and the deterministic offline verifier test `xcom_build_contract` (label `t012`) that asserts
  the effective policy.

### 4.3 Work-product components

- **`T12-WP`** — the T012 repository-owned work-product set (`requirements.md`, `architecture.md`,
  `detailed-design.md`, `unit-specifications.md`, `verification-plan.md`, `implementation.md`,
  `internal-review.json`, and `reports/xcom-queue/t012-package.json`).

### 4.4 Consumed components (read-only)

`XCOM-CMP-004` core types, `XCOM-CMP-005` lifecycle, `XCOM-CMP-006` provider, `XCOM-CMP-007` owned loopback,
`XCOM-CMP-008` observation, `XCOM-CMP-009` validation session, and `XCOM-CMP-003` activation plan are the
compiled inputs T012 configures. T012 neither implements nor alters them.

## 5. Build/test data flow (ordered)

1. **Inherit** — CMake enters `src/xverse/xcom/` only after the root contract has created
   `xverse::xcom_warnings` and admitted the offline dependency targets.
2. **Assert** — `xverse_xcom_assert_runtime_warning_policy()` fails configuration unless the warning target
   exists and carries an error-promoting option.
3. **Select** — `xverse_xcom_runtime_sanitizers()` resolves `XVERSE_XCOM_SANITIZERS`; the empty default
   yields no flags, an unknown entry or `address`+`thread` fails configuration.
4. **Define and configure** — the six runtime library targets and their aliases are defined as in the
   baseline, and each runtime and test target is routed through `xverse_xcom_apply_runtime_rules()`.
5. **Register** — under `BUILD_TESTING`, the baseline test executables are created and registered with their
   baseline names and labels; the generated build-contract target is registered with label `t012`.
6. **Emit evidence and verify** — the effective policy is written to `xcom-runtime-contract.json` beneath the
   build tree, and `xcom_build_contract` verifies it offline and deterministically.

## 6. Interfaces

T012 exposes no runtime, transport, or C++ API. Its interfaces are the CMake/CTest contract:

| Interface | Contract |
| --- | --- |
| `XVERSE_XCOM_SANITIZERS` | CMake cache/`-D` selection; comma- or semicolon-separated subset of `{address, thread, undefined}`; default empty; invalid or conflicting selection fails configuration. |
| `xverse_xcom_assert_runtime_warning_policy()` | Function; `FATAL_ERROR` when the warning target is missing or does not promote warnings. |
| `xverse_xcom_runtime_sanitizers()` | Function; publishes `xverse_xcom_sanitize_compile`/`xverse_xcom_sanitize_link` to the caller. |
| `xverse_xcom_apply_runtime_rules(<target>)` | Function; applies the shared warnings and any selected sanitizer flags to one existing target. |
| `XVERSE_XCOM_RUNTIME_TARGETS` | Declared, ordered inventory of the six runtime library targets. |
| CTest `xcom_build_contract` | Test; exits nonzero naming the violated invariant when the effective policy deviates. |

## 7. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Fail-closed safety | the warning assertion runs before any target is defined; invalid sanitizer selections abort configuration | T012-SR-003/004; CHK-04, NEG-03..NEG-06 |
| Behavioral preservation | only the CMake contract changes; default sanitizer selection adds no flag | T012-SR-005/010; CHK-05, CHK-15 |
| Determinism | declared target inventory, stable test names/labels, generated contract evidence | T012-SR-006/007; CHK-08, CHK-09, CHK-11 |
| Offline/bounded | consumes the admitted inputs only; no network, registry, or thread | T012-SR-008; CHK-12 |
| Public safety | committed files carry no absolute host path; generated evidence stays in the build tree | T012-SR-009; CHK-13 |
| Maintainability | one subtree-owned rule section, one declaration of the inventory, one verifier | T012-STK-001/004; CHK-03, CHK-17 |
| Governance | no accepted artifact rewritten; registers re-validated; REF-002 unchanged | T012-SR-010/012; CHK-16, CHK-18 |

## 8. Consistency and constraints

- **Dependency direction preserved.** T012 consumes the T011 envelope and the root build contract; no
  runtime X-COM unit depends on the build contract, and the reverse dependency does not occur.
- **Domain neutrality preserved.** The contract names compiler flags, target names, and build paths only; no
  automotive or product primitive is introduced.
- **Ownership preserved.** The only production path changed is the declared shared `src/xverse/xcom/CMakeLists.txt`;
  no task moves to a different revision and no ownership path is re-declared.
- **Maturity preserved.** The subtree remains a prototype-only, Linux x86-64, source-level build contract;
  executed sanitizer/static/Doxygen evidence and acceptance remain with T035–T037 and T039/T041.
- **Later tasks preserved.** T013–T016 keep their own source and test ownership; T012 registers those
  targets but compiles no new behavior.

## 9. Traceability

| Architecture element | T012 requirements |
| --- | --- |
| `T12-XB-1`, `T12-CMP-RULES`, `T12-CMP-INV` | T012-STK-001, T012-SR-001, T012-SR-002, T012-SR-010 |
| `T12-XB-2`, `T12-CMP-WARN` | T012-STK-002, T012-SR-003 |
| `T12-XB-3`, `T12-CMP-SAN` | T012-STK-003, T012-SR-004, T012-SR-005 |
| `T12-XB-4`, `T12-CMP-CONTRACT` | T012-STK-004, T012-SR-007, T012-SR-009 |
| `T12-XB-5`, `T12-WP` | T012-STK-005, T012-SR-009, T012-SR-011, T012-SR-012 |
| `T12-CMP-CTEST` | T012-SR-006, T012-SR-008 |
