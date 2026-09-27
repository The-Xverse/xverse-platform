# T012 Verification Plan — Named Checks, Commands, and Expected Results (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T012 |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `ade79ee1f73f176c0178b77d6b10ed8ba8587da6` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope plus the repository-owned Fabro gate and register validators |

This plan is written **before** implementation. The implementation must realize every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
Because T012 is a build-contract task, the executable checks are CMake configure probes, a build, the CTest
suite, and the generated build-contract test; the governance checks are the deterministic gate and the
T007–T010 register validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T012 ade79ee1f73f176c0178b77d6b10ed8ba8587da6
```

For T012 this gate requires:

- the six work products `docs/engineering/xcom/t012/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T012 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- at least one changed path that starts with `src/xverse/xcom/` and ends with `CMakeLists.txt` or `.cmake`;
- `cmake -S . -B build/fabro-t012 -G Ninja -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build/fabro-t012 --parallel 4`,
  a non-empty `ctest --test-dir build/fabro-t012 -N`, and
  `ctest --test-dir build/fabro-t012 --output-on-failure --parallel 4` all exit 0;
- `git diff --check <baseline> --` clean.

## 3. Admitted inputs

The CMake configure/build/test commands consume the T011 admitted inputs, supplied as environment variables
by the repository harness (names only; values are the admitted private-store locations and are not restated
here):

| Input | Role |
| --- | --- |
| `XVERSE_XCOM_TOOLCHAIN` | admitted offline prefix (nlohmann/json, protobuf, gRPC, clang-tidy) |
| `XVERSE_XCOM_PACKAGE_MANIFEST` | admitted 12-record package manifest |
| `XVERSE_XCOM_T025_TEST_TOOLCHAIN` | admitted GTest prefix used by the baseline test targets |

No new mandatory input is introduced (`T012-SR-001`, `T012-SR-008`).

### 3.1 Environment prerequisite (A-1)

The gate inherits the run process environment and does not itself export the three admitted inputs. The
environment carried none of them, so the gate's plain
`cmake -S . -B build/fabro-t012 -G Ninja -DCMAKE_BUILD_TYPE=Debug` failed closed at
`src/xverse/xcom/CMakeLists.txt:487` with `T025 tests require the admitted
XVERSE_XCOM_T025_TEST_TOOLCHAIN prefix` before any T012 contract was evaluated (recorded as
`T012-IR-02`). The only permitted resolution is the narrow A-1 fallback already recorded by the accepted
T019/T020 slices:

1. `cmake/XComOfflineDependencies.cmake` reads `XVERSE_XCOM_TOOLCHAIN` and `XVERSE_XCOM_PACKAGE_MANIFEST`
   from the environment when present, and otherwise from an explicit, previously admitted CMake cache
   value, exporting it to the hash-verified preflight child.
2. `src/xverse/xcom/CMakeLists.txt` applies the same explicit-cache fallback to the admitted GTest prefix
   `XVERSE_XCOM_T025_TEST_TOOLCHAIN`; no new mandatory input is added.
3. the implementation stage seeds those explicit values with one configure carrying the three admitted
   inputs into the gate's own build directory, so the gate's subsequent, unmodified configure reuses the
   seeded cache.

The hash-verified offline preflight (`scripts/xcom_dependency_preflight.py --cmake-dependency-check`) still
runs unchanged. Ambient discovery, network fetch, a disabled preflight, a weakened admission check, or a
committed host-specific path is prohibited. The admitted input values live only in the git-ignored `build/`
tree and are recorded here by name. Any shared-path edit made for this reason is recorded in
`implementation.md` and weakens no admission check.

## 4. Supporting commands (same tools, offline)

```sh
git rev-parse ade79ee1f73f176c0178b77d6b10ed8ba8587da6
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only ade79ee1f73f176c0178b77d6b10ed8ba8587da6 --
git diff --check ade79ee1f73f176c0178b77d6b10ed8ba8587da6 --
git ls-files --others --exclude-standard
```

`git rev-parse` for the baseline must print the baseline SHA, proving the binding resolves. The register
validators must still pass with the shared T007–T010 artifacts unchanged in substance.

> Recorded plan-stage observation (not candidate evidence): at baseline
> `ade79ee1f73f176c0178b77d6b10ed8ba8587da6`, a Debug Ninja configure and build succeeded and
> `ctest --test-dir <build> --output-on-failure --parallel 4` reported `100% tests passed, 0 tests failed out
> of 247` in ~3 s, with labels `t019`, `t020-*`, `t025`, `observation`, and `performance`. This is a baseline
> sanity observation; acceptance still requires fresh candidate-bound evidence per §7.

## 5. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T012 entry exists and states the CMake/CTest scope |
| CHK-02 | Changed-path boundary | `git diff --name-only <baseline> --` | the only production path is `src/xverse/xcom/CMakeLists.txt`; no other `src/`, no `tests/`, `xdl/`, or `proto/` path; the work products and the one-line `tasks.md` checkbox are the remainder |
| CHK-03 | C++20 and warning options per target | configure with `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON`; inspect `compile_commands.json` | each runtime target compiles with `-std=c++20` (not `gnu++20`) and `-Wall -Wextra -Wpedantic -Werror` |
| CHK-04 | Fail-closed warning assertion | read the assertion in `src/xverse/xcom/CMakeLists.txt`; run NEG-03/NEG-04 | the assertion runs before target definition and fails configuration without emitting an accepted target set |
| CHK-05 | Default sanitizer-off | configure with `XVERSE_XCOM_SANITIZERS` unset; inspect `compile_commands.json` and the contract JSON | no `-fsanitize` flag appears on any target; `sanitizers` is empty; 247 baseline tests still register |
| CHK-06 | `address` selection | configure with `-DXVERSE_XCOM_SANITIZERS=address`; build; run `ctest -R xcom_build_contract` | `-fsanitize=address -fno-omit-frame-pointer` on compile and `-fsanitize=address` on link for runtime and test targets; the contract test passes |
| CHK-07 | `thread` and `undefined` selections | configure with `-DXVERSE_XCOM_SANITIZERS=thread` and `-DXVERSE_XCOM_SANITIZERS=undefined`; run `ctest -R xcom_build_contract` | each selection applies its declared flags to runtime and test targets; the contract test passes |
| CHK-08 | CTest inventory preserved | `ctest --test-dir <build> -N` before and after | every baseline test name and label is present; the total is 247 + 1 = 248 tests |
| CHK-09 | Build-contract test | `ctest --test-dir <build> -R xcom_build_contract --output-on-failure`; inspect the generated JSON | the test passes and asserts C++20, extensions off, an error-promoting warning option with `-Wall -Wextra -Wpedantic`, the six-target inventory, `BUILD_TESTING=ON`, and a valid sanitizer selection |
| CHK-10 | Full build and suite | `cmake --build <build> --parallel 4`; `ctest --test-dir <build> --output-on-failure --parallel 4` | build exits 0; `100% tests passed` out of 248 |
| CHK-11 | Determinism | reconfigure twice with identical inputs; diff `ctest -N` output and the contract JSON | the target/test name set and the contract JSON's policy fields are identical; ordering is stable |
| CHK-12 | Offline and bounded | source inspection of `src/xverse/xcom/CMakeLists.txt` and the root modules | no network client/resolver, package manager, registry, FetchContent resolution, or added thread; the only subprocess is the inherited admission preflight |
| CHK-13 | Public safety | scan the candidate's committed files for environment-specific absolute paths (host prefix, manifest, test-toolchain, temporary, private store), credentials, private addresses, and sensitive values | no committed environment-specific absolute path, credential, private address, or sensitive value; the only retained absolute path is the repository harness gate invocation permitted by `T012-SR-009`; generated evidence exists only beneath the build directory |
| CHK-14 | Requirement-to-check coverage | cross-read `requirements.md` §10, this plan §8, and `unit-specifications.md` §5 | every T012 requirement maps to ≥ 1 check and ≥ 1 unit with byte-equal per-requirement check lists across the two indices |
| CHK-15 | Runtime behavior and public interface unchanged | `git diff --name-only <baseline> --`; hash the baseline `.hpp`/`.cpp` files | no `src/xverse/xcom/**/*.hpp` or `*.cpp` appears in the diff; the header and source hashes equal the baseline |
| CHK-16 | Register reconciliation and REF-002 | run the T007–T010 validators; inspect the REF-002 disposition | the validators pass unchanged; `ref002.disposition == unchanged` with an empty `promoted` list; the T008/T010 T012-attribution observation is recorded without promotion |
| CHK-17 | Deterministic gate and diff hygiene | run the §2 gate; `git diff --check <baseline> --` | exit 0 with `checks` containing a `ctest:` count; the diff is whitespace-clean; the T012 checkbox is complete only at the implementation stage |
| CHK-18 | Later-task boundary | `git diff --name-only <baseline> --`; read `specs/007-xcom-core/tasks.md` | no T013+ artifact, directory, or checkbox changes; only the T012 checkbox flips, and only in the implementation stage |

## 6. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behaviour with no
partial accepted target set, no evidence claiming a weakened policy, and no output claiming admission.
NEG-01..NEG-14 and NEG-17 are executable CMake/CTest probes; NEG-15..NEG-16 are configure probes over the
admitted inputs; NEG-18..NEG-22 are repository/inspection probes.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | select a non-Ninja generator | configure `FATAL_ERROR` from the root contract; no build |
| NEG-02 | set `BUILD_TESTING=OFF` | configure `FATAL_ERROR` from the root contract; no build |
| NEG-03 | remove or neutralise the `xverse::xcom_warnings` target | the subtree assertion `FATAL_ERROR`s; no target generated |
| NEG-04 | publish warning options without an error-promoting flag | the subtree assertion `FATAL_ERROR`s; no target generated |
| NEG-05 | set `XVERSE_XCOM_SANITIZERS=foo` | configure `FATAL_ERROR` naming the unsupported entry |
| NEG-06 | set `XVERSE_XCOM_SANITIZERS=address,thread` | configure `FATAL_ERROR` naming the mutual exclusion |
| NEG-07 | apply the selected sanitizer to a subset of targets only | the contract/compile-commands inspection detects a target without the selected flag |
| NEG-08 | drop `-Wall` from the effective options | the contract test fails naming the missing flag |
| NEG-09 | drop `-Wextra` from the effective options | the contract test fails naming the missing flag |
| NEG-10 | drop `-Wpedantic` from the effective options | the contract test fails naming the missing flag |
| NEG-11 | rename or remove one inventory target | the contract test fails naming the inventory mismatch |
| NEG-12 | tamper with the generated contract JSON | the contract test fails naming the violated invariant |
| NEG-13 | record C++17 or extensions-on in the contract evidence | the contract test fails naming the standard/extensions invariant; the assertion-inspected configure rejects a weakened standard |
| NEG-14 | record an unsupported sanitizer in the evidence | the contract test fails naming the sanitizer selection |
| NEG-15 | unset `XVERSE_XCOM_TOOLCHAIN` | configure `FATAL_ERROR` from the inherited admission gate |
| NEG-16 | unset `XVERSE_XCOM_PACKAGE_MANIFEST` | configure `FATAL_ERROR` from the inherited admission gate |
| NEG-17 | disable test discovery so CTest finds no test | the deterministic gate fails with "CTest discovered no tests" |
| NEG-18 | introduce an environment-specific absolute host path (prefix, manifest, test-toolchain, temporary, or private store) into a committed build file | CHK-13 public-safety scan fails; the candidate is rejected |
| NEG-19 | modify a public header or a compiled `.cpp` | CHK-15 fails; the change is outside the build-contract boundary |
| NEG-20 | mark the T012 checkbox complete in the plan stage | the deterministic gate fails ("not marked complete after implementation" is the implementation-stage rule; the plan stage must leave it unchecked) |
| NEG-21 | modify or delete a baseline test source | CHK-02/CHK-08 fail; no test may be removed or weakened |
| NEG-22 | implement a later task (e.g. add a T013 source or a T014 header) | CHK-18 fails; the candidate exceeds the T012 boundary |

## 7. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline SHA;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting
  command;
- the configure/build/CTest results, including the `ctest -N` count and the `100% tests passed` line;
- the generated `xcom-runtime-contract.json` and the `xcom_build_contract` test result for the default and
  each sanitizer selection actually exercised;
- the compile-commands inspection proving the per-target warning flags and the default `-fsanitize`-free
  build;
- the changed-path list and the package record `reports/xcom-queue/t012-package.json` with per-file SHA-256;
- the register-validator results and the unchanged REF-002 disposition.

Public evidence omits host-specific, prefix, manifest, test-toolchain, temporary, and private-store absolute
paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 8. Exit criteria

T012 verification is complete when: the deterministic gate passes (CHK-17); every nominal check in §5 has its
expected result; every negative case in §6 fails closed as stated; the register validators still pass with
REF-002 unchanged (CHK-16); the change is confined to the build-contract and work-product boundary (CHK-02,
CHK-15, CHK-18); and a separate DeepSeek internal review records a passing verdict with no findings. This
does not constitute user acceptance, which remains T041.

## 9. Requirement-to-check coverage

| Requirement | Checks |
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
