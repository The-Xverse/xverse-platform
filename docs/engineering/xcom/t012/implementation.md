# T012 Implementation Record — X-COM Subtree CMake/CTest Targets and Warning-as-Error Rules

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T012 (capability 007, slice `T-CORE`) |
| Stage / role | implementation → implementation record |
| Revision | 1 |
| Authorized baseline | `ade79ee1f73f176c0178b77d6b10ed8ba8587da6` |
| Predecessor | T011 reviewed terminal package (`docs/engineering/xcom/t011/`) |
| Candidate state | working tree over the authorized baseline (staged for the deterministic gate; candidate revision assigned when the workflow checkpoints) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Internal review | [`internal-review.json`](internal-review.json) (separate read-only DeepSeek review of this candidate) |
| Package record | `reports/xcom-queue/t012-package.json` (written by the deterministic package action) |
| Authorization | ACC002/ACC004/ACC005/ACC006/ACC007/ACC010/ACC011/ACC014/ACC015; ADR-0018; ADR-0020; `specs/007-xcom-core/tasks.md` T012 |
| Maturity | Prototype-only subtree build/test work product implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T012 implements the bounded slice required by the T012 task entry: *"Add CMake/CTest targets and
warning-as-error rules under `src/xverse/xcom/`."*

The candidate changes exactly one production path — the shared subtree contract
`src/xverse/xcom/CMakeLists.txt` — and adds the six T012 repository-owned work products. It:

1. declares the ordered six-library runtime inventory (`XVERSE_XCOM_RUNTIME_TARGETS`);
2. fails closed at configure time when the inherited `xverse::xcom_warnings` target is absent or
   does not promote warnings to errors (`xverse_xcom_assert_runtime_warning_policy`);
3. resolves the opt-in `XVERSE_XCOM_SANITIZERS` selection over `{address, thread, undefined}` and
   rejects unknown entries and the ASan+TSan combination (`xverse_xcom_runtime_sanitizers`);
4. routes every runtime and test target through one uniform helper
   (`xverse_xcom_apply_runtime_rules`), which applies the shared warning target and any selected
   sanitizer compile/link flags;
5. emits the effective policy as build-tree evidence (`xcom-runtime-contract.json`) and verifies it
   with one deterministic, offline CTest target (`xcom_build_contract`, label `t012`).

T012 claims **no** runtime behavior, public C++ interface, provider, observation, stimulation, or
gateway behavior. The candidate changes **no** `.cpp`/`.hpp`, `tests/`, `xdl/`, or `proto/` path; it
adds no mandatory environment input, opens no network endpoint, and resolves no package. It compiles
and registers the existing T013–T015/T019/T025 sources and the existing tests unchanged, and adds no
test source.

## 3. Implemented change

| Path | Change | Role |
| --- | --- | --- |
| `src/xverse/xcom/CMakeLists.txt` | edit | subtree CMake/CTest contract: inventory, warning assertion, sanitizer selector, uniform application helper, generated evidence and verifier, `xcom_build_contract` registration (the only production path) |
| `docs/engineering/xcom/t012/requirements.md` | add (plan stage, frozen) | T012-STK/T012-SR requirements, scope, authorities, affected paths, REF-002 disposition, gaps, requirement-to-check index |
| `docs/engineering/xcom/t012/architecture.md` | add (plan stage, frozen) | subtree boundary, trust boundaries, components, ordered data flow, interfaces, quality attributes, traceability |
| `docs/engineering/xcom/t012/detailed-design.md` | add (plan stage, frozen) | rules block, sanitizer mapping, inventory, contract evidence, failure semantics, bounds, public-safety design |
| `docs/engineering/xcom/t012/unit-specifications.md` | add (plan stage, frozen) | build-contract units `T012-U-RULES/WARN/SAN/INV/CTEST/CONTRACT` and work-product units `T012-U-W01..W06` |
| `docs/engineering/xcom/t012/verification-plan.md` | add (plan stage, frozen) | deterministic gate, CHK-01–CHK-18, NEG-01–NEG-22, candidate-bound evidence, exit criteria |
| `docs/engineering/xcom/t012/implementation.md` | add (this record) | realized change, symbols, commands and results, negative coverage, limitations, traceability |
| `specs/007-xcom-core/tasks.md` | edit (T012 checkbox `[ ]` → `[X]`) | capability task ledger; marked complete only after the authorized work and every required local check passed |

### 3.1 Realized symbols and line references (`src/xverse/xcom/CMakeLists.txt`)

| Symbol / construct | Location | Realized behaviour |
| --- | --- | --- |
| `XVERSE_XCOM_RUNTIME_TARGETS` | lines 11–22 | ordered six-target runtime inventory (`INV-12`) |
| `xverse_xcom_assert_runtime_warning_policy()` | lines 23–55 (call: line 128) | `FATAL_ERROR` on a missing warning target, empty options, or no error-promoting option; runs before any target is defined |
| `xverse_xcom_runtime_sanitizers()` | lines 57–115 (call: line 129) | validates `XVERSE_XCOM_SANITIZERS`, de-duplicates, rejects unknown entries and `address`+`thread`, publishes compile/link flags and selected names |
| `xverse_xcom_apply_runtime_rules(<target>)` | lines 117–126 | applies `xverse_xcom_apply_warnings` and any selected sanitizer flags; `FATAL_ERROR` on a missing target |
| 21 `xverse_xcom_apply_runtime_rules(...)` call sites | throughout the target/test sections | the baseline's 21 `xverse_xcom_apply_warnings(...)` calls, mechanically substituted; no target name, source, link library, or include directory changed |
| generated `xcom-runtime-contract.json` | emitted at line 188 beneath the build tree | effective `schema_version`, `task_id`, `cxx_standard`, `cxx_extensions`, `warning_options`, `sanitizers`, `runtime_targets`, `build_testing` |
| generated `verify-xcom-runtime-contract.cmake` | emitted at line 336 beneath the build tree | deterministic, offline `cmake -P` verifier; exits nonzero naming the violated invariant |
| `add_test(NAME xcom_build_contract …)` + label `t012` | lines 499–505 | the single additive CTest target (248 = 247 + 1) |

### 3.2 Detail resolutions

Two implementation decisions reconcile the realized change with the plan package. Neither changes an
accepted requirement, check, contract, boundary, or REF-002 disposition.

1. **`D-01` — the sanitizer selector additionally publishes the selected names.**
   `detailed-design.md` §4.3 specifies `xverse_xcom_runtime_sanitizers()` publishing
   `xverse_xcom_sanitize_compile`/`xverse_xcom_sanitize_link`, and §6.1 requires the evidence field
   `sanitizers`. The implementation therefore also publishes `xverse_xcom_sanitizer_names`
   (de-duplicated, declaration order) so the evidence records the selection by name rather than by
   reverse-engineering the flags. This is additive to the documented interface and weakens nothing.
2. **`D-02` — the verifier reports malformed evidence as a fail-closed read error.**
   `detailed-design.md` §6.2 requires a specific failure message per violated invariant. A JSON value
   that cannot be read (e.g. `warning_options` is not an array) fails via `string(JSON … ERROR_VARIABLE)`
   with a named read error, which is the fail-closed outcome `NEG-12` requires; a well-formed but
   out-of-policy value fails with the field-specific invariant message (`NEG-08`–`NEG-11`, `NEG-13`,
   `NEG-14`).

## 4. Verification method and evidence

Environment for this record: CMake 3.22.1, Ninja 1.10.1, CTest 3.22.1, GNU C++ (C++20), Python 3.13;
repository checkout at the authorized baseline `ade79ee1f73f176c0178b77d6b10ed8ba8587da6`. The T011
admitted inputs are required as the named variables `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN`; their values are the admitted
private-store locations and are **not** restated here (public safety, `T012-SR-009`). No new mandatory
input was introduced.

The first deterministic-gate invocation failed closed because the run process environment carried none of
the three inputs: `cmake -S . -B build/fabro-t012 -G Ninja -DCMAKE_BUILD_TYPE=Debug` aborted at
`src/xverse/xcom/CMakeLists.txt:487` with `T025 tests require the admitted XVERSE_XCOM_T025_TEST_TOOLCHAIN
prefix`. This is `T012-IR-02`. It is resolved only through the narrow A-1 fallback recorded in
[`verification-plan.md`](verification-plan.md) §3.1 (the same mechanism accepted for T019/T020): the two
root dependencies accept an explicit, previously admitted CMake cache value when the environment input is
absent, the subtree applies the same explicit-cache fallback to the admitted GTest prefix, and one seeding
configure carrying the three admitted inputs writes those values into the gate's own `build/fabro-t012`
cache (git-ignored; no host path is committed). The gate's unmodified
configure/build/`ctest` sequence then passes. The hash-verified offline preflight is unchanged, no ambient
path or network resolution was added, and no admission check was weakened.

### 4.1 Commands and observed results

| # | Command | Exit | Result |
| ---: | --- | ---: | --- |
| 1 | `git rev-parse ade79ee1f73f176c0178b77d6b10ed8ba8587da6` | 0 | Prints the baseline SHA; the binding resolves (CHK-01). |
| 2 | `cmake -S . -B build/t012-cand -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON` | 0 | Configure succeeds with the default (empty) sanitizer selection (CHK-03, CHK-05). |
| 3 | `cmake --build build/t012-cand --parallel 4` | 0 | All targets build with no warning promoted to an error (CHK-10). |
| 4 | `ctest --test-dir build/t012-cand -N` (post-build) | 0 | `Total Tests: 248` (CHK-08). |
| 5 | `ctest --test-dir build/t012-cand --output-on-failure --parallel 4` | 0 | `100% tests passed, 0 tests failed out of 248` in ~3.1 s (CHK-10). |
| 6 | `ctest --test-dir build/t012-cand -R xcom_build_contract -V` | 0 | `xcom_build_contract: effective X-COM subtree policy verified`; test `Passed` (CHK-09). |
| 7 | compile-commands inspection (all 34 compile entries; 32 under the subtree) | 0 | every runtime `.cpp` and test source compiles with `-std=c++20` (never `gnu++20`) and `-Wall -Wextra -Wpedantic -Werror`; no `-fsanitize` flag (CHK-03, CHK-05). |
| 8 | baseline vs candidate test-name sets (`ctest -N --show-only=json-v1`) | 0 | baseline 247, candidate 248; zero removed/renamed; the only addition is `xcom_build_contract` (CHK-08). |
| 9 | `-DXVERSE_XCOM_SANITIZERS=address / thread / undefined / address,undefined` configure + contract test | 0 | each selection applies its declared compile/link flags to all 32 subtree compile entries and records the names in the evidence; the contract test passes (CHK-06, CHK-07). |
| 10 | `cmake --build build/t012-san-address --parallel 4` | 0 | the ASan configuration links every target; the contract test passes (CHK-06). |
| 11 | NEG-01 `-G "Unix Makefiles"` | 1 | `CMake Error at CMakeLists.txt:11: X-COM requires a Ninja generator` (NEG-01). |
| 12 | NEG-02 `-DBUILD_TESTING=OFF` | 1 | `CMake Error at CMakeLists.txt:20: X-COM requires BUILD_TESTING=ON` (NEG-02). |
| 13 | NEG-03 throwaway-copy probe removing the `xverse::xcom_warnings` alias | 1 | `CMake Error at src/xverse/xcom/CMakeLists.txt:25: X-COM subtree requires the inherited xverse::xcom_warnings target` (NEG-03). |
| 14 | NEG-04 throwaway-copy probe dropping `-Werror` from the GNU/Clang warning policy | 1 | `CMake Error at src/xverse/xcom/CMakeLists.txt:49: X-COM warning policy does not promote warnings to errors` (NEG-04). |
| 15 | NEG-05 `-DXVERSE_XCOM_SANITIZERS=foo` | 1 | `CMake Error at src/xverse/xcom/CMakeLists.txt:69: Unsupported XVERSE_XCOM_SANITIZERS entry 'foo'` (NEG-05). |
| 16 | NEG-06 `-DXVERSE_XCOM_SANITIZERS=address,thread` | 1 | `CMake Error at src/xverse/xcom/CMakeLists.txt:83: address and thread are mutually exclusive` (NEG-06). |
| 17 | NEG-08..NEG-14 verifier probes over a mutated contract JSON copy | 1 each | each case exits nonzero naming the violated invariant (`-Wall`/`-Wextra`/`-Wpedantic` missing; inventory mismatch; malformed read; `cxx_standard`/`cxx_extensions`; unsupported sanitizer) and the untampered copy passes (NEG-08..NEG-14, CHK-09). |
| 18 | NEG-15 unset `XVERSE_XCOM_TOOLCHAIN` | 1 | `CMake Error at cmake/XComOfflineDependencies.cmake:41: Required explicit input XVERSE_XCOM_TOOLCHAIN is unset` (NEG-15). |
| 19 | NEG-16 unset `XVERSE_XCOM_PACKAGE_MANIFEST` | 1 | `CMake Error at cmake/XComOfflineDependencies.cmake:41: Required explicit input XVERSE_XCOM_PACKAGE_MANIFEST is unset` (NEG-16). |
| 20 | `python3 scripts/validate_xcom_task_ownership.py --verify` and `--check-human` | 0 | `X-COM task-ownership validation passed` (CHK-16). |
| 21 | `python3 scripts/validate_xcom_requirements_traceability.py --verify` | 0 | `X-COM requirements/traceability validation passed` (CHK-16). |
| 22 | `python3 scripts/validate_xcom_architecture_contracts.py --verify` | 0 | `X-COM architecture/contracts validation passed` (CHK-16). |
| 23 | `python3 scripts/validate_xcom_unit_design.py --verify` | 0 | `X-COM unit-design validation passed` (CHK-16). |
| 24 | `git diff --name-only ade79ee1f73f176c0178b77d6b10ed8ba8587da6 --` | 0 | exactly the six T012 work products, `src/xverse/xcom/CMakeLists.txt`, and the one-line `specs/007-xcom-core/tasks.md` checkbox; no other `src/`, no `tests/`, `xdl/`, or `proto/` path (CHK-02, CHK-15, CHK-18). |
| 25 | `git diff --check ade79ee1f73f176c0178b77d6b10ed8ba8587da6 --` | 0 | Empty output; the candidate diff is whitespace-clean (CHK-17). |
| 26 | `python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T012 ade79ee1f73f176c0178b77d6b10ed8ba8587da6` (successor candidate; process environment without the three admitted inputs) | 0 | `{"ok": true, "task_id": "T012", "changed_paths": 8, "checks": ["ctest:248"]}` (CHK-17; closes `T012-IR-02`). |
| 27 | Determinism: two identical fresh configures; `diff` of the contract JSON and of the `ctest -N` test sets | 0 | both configures exit 0; the contract JSON and the discovered test-name set are byte-identical (CHK-11, T012-STK-004). |
| 28 | gate configure before the A-1 resolution: `env -u XVERSE_XCOM_TOOLCHAIN -u XVERSE_XCOM_PACKAGE_MANIFEST -u XVERSE_XCOM_T025_TEST_TOOLCHAIN -u LD_LIBRARY_PATH cmake -S . -B build/fabro-t012 -G Ninja -DCMAKE_BUILD_TYPE=Debug` | 1 | `CMake Error at src/xverse/xcom/CMakeLists.txt:487 (message): T025 tests require the admitted XVERSE_XCOM_T025_TEST_TOOLCHAIN prefix`; the recorded trigger for `T012-IR-02`. |
| 29 | A-1 seeding configure (the gate command plus the three admitted inputs as explicit cache values), then the unmodified command 26 | 0 | `-- Configuring done` / `-- Generating done`; the gate's own configure/build/`ctest` sequence then passes with `checks: ["ctest:248"]`. |

NEG-07 ("apply the selected sanitizer to a subset of targets only") is the inverse of command 9: the
compile-commands inspection found the selected flag on **all** 32 subtree compile entries and on no
non-subtree entry except the two root probe objects that T012 does not own. NEG-17..NEG-22 are
repository/inspection probes carried by commands 4, 8, 24 and CHK-13/CHK-15/CHK-18.

### 4.2 Generated evidence (candidate, default configuration)

```json
{
  "schema_version": 1,
  "task_id": "T012",
  "cxx_standard": 20,
  "cxx_extensions": "OFF",
  "warning_options": ["-Wall", "-Wextra", "-Wpedantic", "-Werror"],
  "sanitizers": [],
  "runtime_targets": ["xverse_xcom_core_types", "xverse_xcom_observation", "xverse_xcom_endpoint_route_lifecycle", "xverse_xcom_provider_loopback", "xverse_xcom_validation_session", "xverse_xcom_activation_plan"],
  "build_testing": "ON"
}
```

The file exists only beneath the build directory (`build/t012-cand/src/xverse/xcom/`), is not
committed, and is regenerated per configuration (CHK-11: two identical configurations produce a
byte-identical policy field set).

### 4.3 Artifact identity at this candidate state

| Artifact | SHA-256 | Bytes |
| --- | --- | ---: |
| `docs/engineering/xcom/t012/requirements.md` | `61ced918a61aa9186b7ce868aa373d4081c7071232ce51246ecc591738a88a68` | 20133 |
| `docs/engineering/xcom/t012/architecture.md` | `981be1cd9052e81ecb2d0fca11e5986024323941f0da099f611888fe5627a234` | 13439 |
| `docs/engineering/xcom/t012/detailed-design.md` | `cf92284d5d936acf1677f1af9a22b92deafffaf822df8694ed42f64ddf2ec2ac` | 14601 |
| `docs/engineering/xcom/t012/unit-specifications.md` | `ffa70c88d7e0d19f2caf5097e539efe5b993c82dffc42841eb7d31ef37766de9` | 14227 |
| `docs/engineering/xcom/t012/verification-plan.md` | `40ebd64c02cf470ebec2caa1e5e0dc76c91f271d13806e2213050181838c7595` | 16170 |
| `src/xverse/xcom/CMakeLists.txt` | `3174c0c182ce53f541609795bd47d139c331aa106b969874c0ee4fababbf8100` | 27967 |
| `specs/007-xcom-core/tasks.md` | `da515f35c4a9b72df32db0e84fc4356d141b476eee6b62137449bfb813a34317` | 8026 |

`docs/engineering/xcom/t012/implementation.md` is bound by the package record's per-file SHA-256
together with the seven artifacts above. `docs/engineering/xcom/t012/internal-review.json` and
`reports/xcom-queue/t012-package.json` are the untracked review and package outputs produced after the
deterministic gate; the package action recomputes every changed tracked path's SHA-256. A successor
candidate must record its own exact revision and repeat every affected check.

### 4.4 Inherited provenance repair (T012 successor revision)

The first feature-delivery attempt for this candidate passed scope, checkpoint, review, package,
unit, static-analysis, target-repository integration, and validation, then failed the final
delivery gate with `stale endpoint revision in T020-L-046`. T012 edited the shared subtree contract
`src/xverse/xcom/CMakeLists.txt`, which is also the code endpoint of the inherited T020 trace link
`T020-L-046` and of one artifact row in the inherited `engineering/stage-results/implementation.json`.
Both records still carried the pre-T012 hash of that file. This successor revision refreshes only
those current-provenance hash fields; it changes no relation, no CMake behaviour, no source file,
and no test.

| Record | Field | Before | After |
| --- | --- | --- | --- |
| `engineering/trace/links.json` (`T020-L-046`, `implemented_by`, `T020-SR-006` → `src/xverse/xcom/CMakeLists.txt`) | `target_revision` | `8f301734…` | `3174c0c182ce53f541609795bd47d139c331aa106b969874c0ee4fababbf8100` |
| `engineering/stage-results/implementation.json` | `artifacts[src/xverse/xcom/CMakeLists.txt].sha256` | `8f301734…` | `3174c0c182ce53f541609795bd47d139c331aa106b969874c0ee4fababbf8100` |

Refreshing `engineering/trace/links.json` in turn made the inherited `engineering/trace/links.json`
artifact rows in three further T020 stage records stale, so those rows were re-pinned to the exact
new trace hash as well: `engineering/stage-results/documentation.json`,
`engineering/stage-results/integration.json`, and `engineering/stage-results/internal-review.json`
(each `artifacts[engineering/trace/links.json].sha256`: `fa0dd2f7…` → `753ae487…`). No other stage
record names a T012-changed path.

Evidence: the T012 repair workflow's `audit_delivery_inputs.py` step, which imports and runs the
unchanged core `validate_project` / `validate_trace` / `validate_stage` checks, now reports
`{"ok": true, "stage_results": 8}` and exits 0, where it previously reported the `T020-L-046` trace
failure and then the `engineering/trace/links.json` stage-hash mismatch. The checker, the CMake
contract, the source, and the tests are unchanged. The hash fields are current-provenance assertions
recomputed by the validators; the historical `reports/xcom-queue/t020-package.json` snapshot is left
untouched. A successor candidate must record its own exact revision and repeat every affected check.

## 5. Requirement-to-evidence traceability

| Requirement | Primary check(s) | Evidence |
| --- | --- | --- |
| T012-STK-001 | CHK-02, CHK-03, CHK-10 | cmd 2, 3, 7, 24 |
| T012-STK-002 | CHK-04, NEG-03, NEG-04 | cmd 13, 14; §3.1 assertion |
| T012-STK-003 | CHK-05, CHK-06, CHK-07, NEG-05, NEG-06 | cmd 9, 10, 15, 16 |
| T012-STK-004 | CHK-09, CHK-11, CHK-12 | cmd 6, 8, 17, 27; §4.2 |
| T012-STK-005 | CHK-15, CHK-16, CHK-18 | cmd 20–25 |
| T012-SR-001 | CHK-03, CHK-11 | cmd 7, 8 |
| T012-SR-002 | CHK-03, CHK-09 | cmd 6, 7 |
| T012-SR-003 | CHK-04, NEG-03, NEG-04, NEG-13 | cmd 13, 14, 17 |
| T012-SR-004 | CHK-06, CHK-07, NEG-05, NEG-06 | cmd 9, 10, 15, 16 |
| T012-SR-005 | CHK-05, CHK-06, CHK-07, NEG-07 | cmd 7, 9, 10 |
| T012-SR-006 | CHK-08, CHK-10 | cmd 4, 5, 8 |
| T012-SR-007 | CHK-09, NEG-08..NEG-14 | cmd 6, 17 |
| T012-SR-008 | CHK-12, CHK-13 | §3.1 (no network/thread/subprocess); §6 |
| T012-SR-009 | CHK-13, NEG-18 | §6 |
| T012-SR-010 | CHK-02, CHK-15, NEG-19, NEG-21, NEG-22 | cmd 24, 25 |
| T012-SR-011 | CHK-17, NEG-01, NEG-02, NEG-15, NEG-16, NEG-20 | cmd 11, 12, 18, 19, 26 |
| T012-SR-012 | CHK-16, CHK-18 | cmd 20–25; REF-002 disposition unchanged |

## 6. Public safety

The T012 work products and the committed CMake contract contain repository-relative paths, target
names, compiler-flag identities, sanitizer names, diagnostic messages, and pass/fail outcomes only.
They contain no credential, private address, unrestricted payload, proprietary source excerpt, or
sensitive deployment value. The admitted input **values** (host prefix, package manifest, and
test-toolchain locations) are referenced by variable **name** and are not committed; generated
evidence exists only beneath the build directory. The single non-repository absolute path is the
workflow's own deterministic-gate invocation in command 26 and `verification-plan.md` §2
(`/home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py`), retained exactly as in the
accepted T009–T011 records; it is the workflow tool path, not a sensitive deployment value
(`CHK-13`, `NEG-18`).

## 7. Limitations, gaps, and maturity

Recorded from the requirements package and **not** resolved by T012:

- `T012-LIM-01` — sanitizer **execution** evidence (running the suite under ASan/TSan/UBSan) is not
  produced by T012. Only the opt-in wiring, fail-closed selection, uniform flag application, and
  default-unchanged behaviour are verified here; executed evidence remains T035's (`T011-GAP-03`
  execution half, unchanged). Command 10 proves the ASan configuration links, not a clean sanitizer run.
- `T012-LIM-02` — transitive host libraries and a pinned base-system ABI remain unlocked
  (`T011-LIM-01`); T012 inherits that limitation.
- `T012-LIM-03` — the subtree remains a source-level CMake contract, not a stable binary plugin ABI;
  T012 introduces no dynamic discovery.
- `T012-LIM-04` — the deterministic gate depends on the three admitted offline inputs, which are
  provisioned outside the repository and are absent from the gate process environment; the gate passes
  only through the narrow A-1 cache-seed resolution recorded in §4 and
  [`verification-plan.md`](verification-plan.md) §3.1 (`T012-IR-02`, `T012-OPEN-02`). No host path is
  committed and the hash-verified preflight is unchanged.
- `T012-GAP-01` — the T008 register and T010 unit design attribute `XCOM-SW-CORE-001`/`XCOM-SW-CORE-010`
  to T012 while `tasks.md` assigns the CORE contract/diagnostic source to T013; this build-contract
  slice records the observation and promotes nothing (`T012-SR-012`).
- `T012-GAP-02` — the strict Doxygen C++ configuration remains open (`T011-GAP-01`), owned by
  T011/T037.
- `T012-GAP-03` — candidate acceptance remains with T039/T041.

Maturity: prototype-only, Linux x86-64, source-level subtree build/test contract, locally verified,
exposing **no** X-COM runtime behavior, compatibility, or production-readiness. Not user-accepted
(T041) and not externally reviewed (Codex review deferred until this ordered backlog completes). No
REF-002 target requirement is promoted; the T008 disposition stays `unchanged` with an empty
`promoted` set.

## 8. Definition-of-done status (requirements view)

- (a) The six named work products exist under `docs/engineering/xcom/t012/` and are mutually
  consistent. ✔
- (b) Every requirement in `requirements.md` §3–§4 maps to ≥ 1 named check in `verification-plan.md`. ✔
- (c) The implementation stage delivered the single CMake change, marked the T012 checkbox, and
  recorded this note. ✔
- (d) The deterministic gate and the named checks pass at the candidate revision (commands 2–26). ✔
- (e) The package record is written by the package action after the review pass. ◐
- (f) A separate DeepSeek internal review records a passing verdict with no findings
  (`docs/engineering/xcom/t012/internal-review.json`). ◐ — produced by the review stage, not
  self-declared here.

This does **not** constitute external review or user acceptance, which remain deferred to the backlog
and to T041 respectively.
