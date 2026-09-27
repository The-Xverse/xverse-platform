# T020 Implementation — Ordering-Equivalence, Malformed-Plan, Drift, Bound, and Regression Tests

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T020 (capability 007, phase 4 XDL-derived activation plan) |
| Stage / role | implementation |
| Revision | 4 (rev 2 adds the repair-pass closure record in §9; rev 3 attempted a deterministic-gate flake closure in §10; rev 4 reverts the out-of-scope rev-3 T025 build-property change and records the benchmark as an external dependency; the rev 1 test package and its evidence are unchanged) |
| Baseline revision | `1e289bfe6234553df94eb25065371f7d423fad88` |
| Candidate | working tree over `1e289bfe6234553df94eb25065371f7d423fad88` (the reviewed T019 terminal package) |
| Predecessor | T017 (`56506d2`), T018 (`199de0b`), T019 (`1e289bf`) reviewed terminal packages |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Classification | Public-safe engineering work product |
| Authority | `specs/007-xcom-core/tasks.md` T020; `specs/007-xcom-core/spec.md` FR-002/FR-006/FR-007/FR-025/FR-027/FR-030/FR-031, SC-001/SC-002; `specs/007-xcom-core/contracts/{xdl-profile,communication-plan}.md`; `docs/engineering/xcom/t010/design-units.md` `XCOM-DU-010`/`XCOM-DU-011`; ACC002/ACC003/ACC013/ACC014/ACC015; ADR-0016/ADR-0018/ADR-0020 |

### 1.1 Scope statement

This change adds **only** the T020 test package and its build/test wiring: one header-only support
artifact, five C++ GoogleTest suites, one Python `pytest` module, five `t020`-labelled CTest
targets, this implementation record, and the T020 checkbox line. It authors no production source,
no Python compiler/validator source, no schema or Profile asset, no `proto/` file, and no new
fixture. It edits no T017/T018/T019 test, fixture, schema, or contract; anchors no legacy artifact;
and runs no production workload.

### 1.2 Maturity classification

**Implemented (bounded prototype).** The suites are pure, offline, deterministic GoogleTest and
`pytest` modules over the accepted decoder API and the accepted compiler/validator pure functions.
They prove the derived-plan chain's ordering equivalence, malformed-plan rejection, drift
resistance, decode bounds, and regression over the bounded committed fixtures and declared synthetic
vectors. They bind nothing, emit no communication item, and make no runtime, timing, compatibility,
activation, production-readiness, or acceptance claim. `XCOM-DU-010`/`XCOM-DU-011` verification
coverage is **extended**, not promoted. External Codex review is deferred until the backlog
completes; no external acceptance is recorded.

## 2. Changed artifacts and symbols

| Path | Change |
| --- | --- |
| `tests/xcom/activation_plan/t020_support.hpp` | New header-only `t20` namespace: `read_text`, `plan_fixture`, `activatable`, `inspectable`, `plan_schema`, `profile_schema`, `seal`, `canonical_body`, `recompute_digest`, `expect_error`, `expect_accepted`, `emit_reversed`/`reverse_key_order_text`, `with_whitespace`, `for_each_limit`, the closed `kCode*`/`kPlanTarget` vocabulary, `required_members()`, the `kFixture*`/`kT019NegativeFileSha256` goldens, and `kDecodeLimitCount`. Includes only the C++20 standard library, `nlohmann/json`, GTest, and the T019 decoder header; no network, subprocess, clock, or filesystem-write access. |
| `tests/xcom/activation_plan/t020_ordering_equivalence_tests.cpp` | New `T20OrderingEquivalence` suite (`T20-ORD-01`..`T20-ORD-08`, `T20-DET-01`..`T20-DET-04`): canonical-body/digest equivalence across member-order, whitespace, and integral-number variants; declared per-collection ordering; duplicate-free/non-empty `activationOrder`; deterministic diagnostics; repeated-decode and domain-separated-SHA-256 determinism. |
| `tests/xcom/activation_plan/t020_malformed_plan_tests.cpp` | New `T20MalformedPlan` suite (`T20-MAL-01`..`T20-MAL-14`): truncation, unbalanced delimiters, trailing content, duplicate members at four levels, non-object roots, wrong JSON types, `null` where an object/array is required, each of the 16 required members dropped, unknown nested members in 12 object/element locations, invalid UTF-8, empty/whitespace documents, over-nesting, the aggregate no-value guard, and the T019 distinctness/hash guard. |
| `tests/xcom/activation_plan/t020_drift_tests.cpp` | New `T20Drift` suite (`T20-DRF-01`..`T20-DRF-09`): required-member/closed-object table, all 13 closed enums (18 member probes) with an out-of-vocabulary rejection, six patterns plus the `apiVersion` const, collection keys/uniqueness/minimums, the three numeric ranges, the closed `$defs/digest` sub-schema, the `planVersion` const, the domain-separator/fixture goldens, and the accepted five Profile forms. |
| `tests/xcom/activation_plan/t020_bound_matrix_tests.cpp` | New `T20BoundMatrix` suite (`T20-BND-01`..`T20-BND-11`): byte/depth/node bounds at-and-over, over-length string rejection, the nine decoded-entity caps at-and-over using bounded two-item vectors, and every one of the 13 `DecodeLimits` members set to zero failing closed with `XCOM-DECODE-UNKNOWN`. |
| `tests/xcom/activation_plan/t020_regression_tests.cpp` | New `T20Regression` suite (`T20-REG-01`..`T20-REG-10`): pinned fixture decode/fields/counts, recorded and recomputed golden digests, SHA-256 known answers, domain-separator regression, the 16-member/closed-schema guard, fixture file hashes, canonical-body hashes, the 13 `DecodeLimits` defaults, and the nine-code closed vocabulary/outcome mapping. |
| `tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py` | New pure `pytest` module: the Python cross-language leg. Compiles a bounded, public-safe synthetic normalized graph with the accepted T018 compiler and cross-checks the accepted T017 validator (`canonical_bytes`, `compute_digest`, `check_digest`, `validate_plan_structure`); reorders the graph for byte/digest identity; asserts deterministic diagnostic ordering; pins the committed fixtures' golden digest/file hash; rejects declared schema/digest mutations; proves the module is offline/pure; and reconciles `verification-plan.md` §8 with the implemented tests. |
| `src/xverse/xcom/CMakeLists.txt` | Shared build wiring: one `foreach` block adding five `t020`-labelled CTest targets (`xverse_xcom_activation_plan_t020_{ordering_equivalence,malformed_plan,drift,bound_matrix,regression}_tests`) linking `xverse::xcom_activation_plan`, `GTest::gtest_main`, `GTest::gmock`, `Threads::Threads`, defining the fixture/plan-schema/Profile-schema compile paths, and using `gtest_discover_tests(... PROPERTIES LABELS "t020-<kind>")` (rev 2; see §9). The T019 library and targets, the pre-existing `xcom_observation_disabled_benchmark` registration, and every other test's command, source, and thresholds are unchanged (rev 4 reverted the out-of-scope rev-3 `RUN_SERIAL` change; see §10). |
| `specs/007-xcom-core/tasks.md` | Shared path: the T020 checkbox line is marked complete **only after** the authorized work and every required local check passed. |
| `docs/engineering/xcom/t020/implementation.md` | This record. |

Anchored, unchanged (read read-only): `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp`,
`src/xverse/xcom/src/activation_plan.cpp`, `tests/xcom/activation_plan/decoder_unit_tests.cpp`,
`tests/xcom/activation_plan/decoder_negative_tests.cpp`, `src/xverse_xdl/xcom_plan.py`,
`tests/test_xcom_plan.py`, `scripts/validate_xcom_plan.py`,
`src/xverse/xcom/contracts/v1/activation-plan.schema.json`, `xdl/profiles/xcom-v0.1.schema.json`,
`specs/007-xcom-core/contracts/**`, `docs/engineering/xcom/t017/**`–`t019/**`, and every committed
fixture under `tests/xcom/activation_plan/fixtures/`.

### 2.1 Cross-language contract

The plan schema and the domain-separated digest rule remain the only interface between the Python
chain (T017/T018) and the C++ decoder (T019). T020 adds no adapter, FFI, second configuration
language, or admitted dependency: the C++ suites use only the standard library, the admitted
`nlohmann/json` header, GTest, and the T019 decoder; the Python module uses only the standard
library and the repository's own `xverse_xdl.xcom_plan`/`scripts/validate_xcom_plan.py` modules. Both
languages independently reproduce the same fixtures' canonical body and digest and agree on the
pinned golden values (A-4: no cross-process invocation).

## 3. Requirement-to-code trace

| Requirement | Artifacts / symbols | Cases | Result |
| --- | --- | --- | --- |
| T020-SR-001 | `t020_support.hpp`, `t020_ordering_equivalence_tests.cpp` (`t20::reverse_key_order_text`, `t20::seal`, `t20::canonical_body`), Python `test_xcom_plan_ordering_equivalence.py` | `T20-ORD-01`..`T20-ORD-08`; `T20-DET-01`..`T20-DET-04` | pass |
| T020-SR-002 | `t020_support.hpp`, `t020_malformed_plan_tests.cpp` | `T20-MAL-01`..`T20-MAL-14` | pass |
| T020-SR-003 | `t020_support.hpp` (`plan_schema`, `profile_schema`, `probe_enum`), `t020_drift_tests.cpp` | `T20-DRF-01`..`T20-DRF-09` | pass |
| T020-SR-004 | `t020_support.hpp` (`for_each_limit`), `t020_bound_matrix_tests.cpp` | `T20-BND-01`..`T20-BND-11` | pass |
| T020-SR-005 | `t020_regression_tests.cpp`, Python `test_xcom_plan_ordering_equivalence.py` | `T20-REG-01`..`T20-REG-10` | pass |
| T020-SR-006 | `src/xverse/xcom/CMakeLists.txt` (five targets), `test_xcom_plan_ordering_equivalence.py` | `ctest`/`pytest` gates; `T20-G05` | pass |
| T020-SR-007 | changed-path set of §2; `ref002.disposition = "unchanged"`; promoted set empty | `T20-G01`..`T20-G05` | pass |

## 4. Environment resolution — A-1

The deterministic gate runs the exact `cmake`/`ctest` sequence in
[`verification-plan.md`](verification-plan.md) §2.1, inheriting the run process environment. That
environment does not carry the admitted offline inputs `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, or `XVERSE_XCOM_T025_TEST_TOOLCHAIN`, so a bare configure fails in
the hash-verified admission preflight before any T020 suite builds (the same trigger T019 recorded).

Resolution, exactly as permitted by [`verification-plan.md`](verification-plan.md) §2.4 A-1 and by
the T019 terminal package:

1. The seeding configure carries the three explicit admitted inputs as CMake cache values; the
   hash-verified offline preflight (`scripts/xcom_dependency_preflight.py --cmake-dependency-check`)
   still runs unchanged and still admits.
2. `cmake/XComOfflineDependencies.cmake` and `src/xverse/xcom/CMakeLists.txt` already accept an
   explicit, previously admitted cache value when the matching environment input is absent (the T019
   A-1 fallback); no T020 change to either shared path was required for this.
3. The seed values and the admitted prefix live outside Git (`build/` is git-ignored); no absolute
   host path is recorded in any source, test, or retained work product.

Ambient discovery, a package registry, network fetch, a disabled preflight, a weakened admission
check, or a committed host-specific path is prohibited and none was introduced.

## 5. Commands and observed results

Environment: the three admitted offline inputs were supplied to the seeding configure as explicit
cache values (§4) and are not committed. `build/fabro-t020` is git-ignored.

| ID | Command | Observed result |
| --- | --- | --- |
| C1 | `cmake -S . -B build/fabro-t020 -G Ninja -DCMAKE_BUILD_TYPE=Debug -DXVERSE_XCOM_TOOLCHAIN=… -DXVERSE_XCOM_PACKAGE_MANIFEST=… -DXVERSE_XCOM_T025_TEST_TOOLCHAIN=…` (seeding configure with the admitted inputs) | configure succeeded; dependency preflight admitted (`Configuring done` / `Generating done`) |
| C2 | `cmake --build build/fabro-t020 --parallel 4` | succeeded; 49 build steps; the T019 library and all five T020 test executables produced |
| C3 | `ctest --test-dir build/fabro-t020 -N` | `Total Tests: 246` (194 pre-existing + 52 T020) |
| C4 | `ctest --test-dir build/fabro-t020 -L t020 --output-on-failure --parallel 4` | `100% tests passed, 0 tests failed out of 52` (labels `t020` = 52 tests) |
| C5 | `ctest --test-dir build/fabro-t020 --output-on-failure --parallel 4` | `100% tests passed, 0 tests failed out of 246` (144 `t025`, 38 `t019`, 52 `t020`, remainder pre-existing) |
| C6 | `python3 -m pytest -q` | `136 passed, 24 subtests passed` (129 pre-existing + 7 T020; T017/T018/T019 Python suites unchanged) |
| C7 | `python3 -m pytest -q tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py` | `7 passed` (T020 module alone) |
| C8 | `python3 scripts/validate_xcom_plan.py --verify` / `--self-test` / `--check-human` | T017 validation `profileKinds=5 planMembers=16 collections=6 digestVectors=2 exitClasses=6`; self-test `cases=53 …`; `human summary: consistent` |
| C9 | `python3 scripts/validate_xcom_task_ownership.py`; `python3 scripts/validate_xcom_requirements_traceability.py` | `X-COM task-ownership validation passed`; `X-COM requirements/traceability validation passed` |
| C10 | `python3 scripts/validate_xcom_architecture_contracts.py`; `python3 scripts/validate_xcom_unit_design.py` | `PATH_INVALID` (exit 12/13), byte-identical at the baseline commit; see §6 L-2 |
| C11 | `git diff --check 1e289bf… --` | no output; exit 0 |
| C12 | `git diff --name-only 1e289bf… --` | exactly the 14 declared T020 paths of §2 (plus this record) |
| C13 | `python3 automation/xcom_feature_gate.py verify T020 1e289bf…` (environment-neutral locator) | see §5.1 |
| C14 | `git rev-parse 1e289bfe6234553df94eb25065371f7d423fad88` | prints the baseline SHA, proving the binding resolves |

### 5.1 Deterministic gate result

The Workflow harness invokes the deterministic gate as
`python3 automation/xcom_feature_gate.py verify T020 1e289bfe6234553df94eb25065371f7d423fad88`
(an environment-neutral locator; no host-specific absolute path is retained). It requires the six
work products, the marked T020 checkbox, a changed path under `tests/`, a clean `git diff --check`,
a passing `pytest`, and a passing `cmake`/`ctest` that discovers at least one test. It passed; the
observed gate output is recorded here: `{"ok": true, "task_id": "T020", "changed_paths": 15,
"checks": ["pytest", "ctest:246"]}`.

### 5.2 Case counts per suite

| Executable | Suite label | Cases | Result |
| --- | --- | --- | --- |
| `xverse_xcom_activation_plan_t020_ordering_equivalence_tests` | `t020-ordering-equivalence` | 8 | pass |
| `xverse_xcom_activation_plan_t020_malformed_plan_tests` | `t020-malformed-plan` | 14 | pass |
| `xverse_xcom_activation_plan_t020_drift_tests` | `t020-drift` | 9 | pass |
| `xverse_xcom_activation_plan_t020_bound_matrix_tests` | `t020-bound-matrix` | 11 | pass |
| `xverse_xcom_activation_plan_t020_regression_tests` | `t020-regression` | 10 | pass |
| `test_xcom_plan_ordering_equivalence.py` | `pytest` | 7 | pass |

Total: 52 C++ cases + 7 Python cases = 59 T020 cases.

### 5.3 Golden-value capture

Captured from the accepted, unchanged artifacts at the candidate revision with the T017 validator
and the committed fixture bytes
(`python3 -c` loading `scripts/validate_xcom_plan.py` `canonical_bytes`/`canonical_body`/`compute_digest`
and `hashlib`): `plan-activatable.json` file `8f32193b…c0790`, canonical body `03dde948…62e5`,
digest `7aaf6317…e4ce`; `plan-inspectable.json` file `48be9d19…4cd1`, canonical body `a97a0a6a…ba99`,
digest `98c13f81…0d3f`. The T019 negative-test file SHA-256 is `14cb56ec…7ab5`. All values match the
`detailed-design.md` §2.3 goldens. A golden is never updated to match a drifted artifact; a mismatch
fails `T20-REG-03`/`T20-REG-07`/`T20-REG-08`/`T20-DRF-08`/`T20-MAL-14`.

## 6. Limitations and deviations

- **L-1 (`activationOrder` is an explicit order, not a sorted collection).** `verification-plan.md`
  §4 `T20-ORD-04` requires a duplicated `activationOrder` entry to be rejected
  `XCOM-DECODE-SHAPE` and the order to be duplicate-free. The accepted T019 decoder
  (`require_unique_identifiers(..., require_non_empty = true)`) rejects a duplicate or empty
  `activationOrder` but does **not** require ascending order — the order is an explicit sequence, so
  a reordered-but-complete sequence that names declared identities is accepted. `T20-ORD-04`
  therefore asserts the duplicate/empty rejection and that a reordered-but-complete sequence is
  accepted **and preserved verbatim** (the meaningful ordering property), rather than the
  `detailed-design.md` §4 sentence that predicted a rejection. This is a documented deviation of the
  pre-code design prose from the accepted decoder contract; no accepted requirement, schema,
  contract, or test is weakened, and the decoder is not changed.
- **L-2 (pre-existing validator conditions).** `validate_xcom_architecture_contracts.py` and
  `validate_xcom_unit_design.py` already fail with `PATH_INVALID` at the baseline commit because
  T017/T018/T019 artifacts are present in the tree; this candidate adds only `tests/xcom/activation_plan/`
  test sources, which `XCOM-DU-011` already lists as present, so the condition is unchanged. Neither
  validator is used by the T020 deterministic gate; the condition is reported for the reviewer, not
  repaired (repairing it would edit the T009/T010 work products owned by other tasks).
- **L-3 (no concurrency surface).** T020 introduces no thread and no mutable shared state; the C++
  suites are single-threaded GoogleTest executables and the Python module is a pure `pytest` module.
  No concurrency bound is applicable or asserted; determinism is asserted by repetition within one
  process.
- **L-4 (bounded cross-language proof, no process bridge).** The C++ suites cannot invoke Python and
  the Python module cannot load the C++ library. Cross-language equivalence is proven by both
  languages independently reproducing the same committed fixtures' canonical body and digest and
  agreeing on the pinned golden values, plus the Python module compiling a bounded synthetic graph
  and comparing the compiler to the T017 validator (A-4). No production value is fixed and no
  dependency is added.
- **L-5 (no runtime/activation proof).** The suites prove the derived-plan chain's equivalence,
  fail-closed rejection, drift resistance, bounds, and regression over the bounded committed fixtures
  and declared synthetic vectors. They do not prove endpoint/route/provider activation, runtime
  behaviour, transport, throughput, timing, compatibility, or production readiness; those belong to
  later tasks. The suites bind nothing and emit no communication item.

## 7. Trace to requirement dispositions

The suites realise the T020 slice for FR-002 (test the derived, digest-bound chain only), FR-006
(fail-closed malformed/closure rejection before activation), FR-031 (pin the versioned Profile/plan
digest contract), SC-001/SC-002 (equivalent normalized inputs derive one canonical plan body/digest
and diagnostic ordering), FR-007 (exercise the declared decode bounds), and FR-025/FR-027 (stable
codes and identifiers only, public-safe evidence). The capability-level dispositions in
[`requirements.md`](requirements.md) §7 remain **partial** for the test slices and are not promoted.
`ref002.disposition = "unchanged"` with an empty promoted set; no `XVE-SYS-0139`–`0158` or shared
target and no `implemented`/`partial`/`allocated`/`deferred` SADS disposition is changed.

## 8. Non-claims

- No external (Codex) review, protected verification, independent integration, source compatibility,
  human acceptance, or production readiness is claimed.
- No communication item, transport, gateway, network peer, payload content, legacy repository, or
  production workload was touched; the suites bind nothing and emit nothing.
- The T020 checkbox is marked only after all required local checks passed; this is not an acceptance
  or integration claim.

## 9. Repair-pass closure record (revision 2)

The read-only internal review recorded two low-severity documentation findings against revision 1
(`T020-IR-001`, `T020-IR-002`). The repair pass resolved **both** as documentation-only corrections in
[`detailed-design.md`](detailed-design.md) §4. While executing the findings' closure tests it was also
confirmed that the per-suite CTest labels declared in [`verification-plan.md`](verification-plan.md)
§2.3/§3 were not registered by the admitted CMake 3.22 `gtest_discover_tests` (which splits a
semicolon-separated label list and keeps only its first element), so the declared per-suite
`ctest -L <kind>` commands selected zero tests; the repair also corrected the T020 build wiring to a
single hyphenated label `t020-<kind>` so those commands run. No accepted requirement, expected result,
golden, test case, or production source changed. This section records the exact closure evidence.

| Finding | Required correction | Applied correction | Closure evidence |
| --- | --- | --- | --- |
| `T020-IR-001` (low) | Amend `detailed-design.md` §4 line 149 (`T20-ORD-04`) so the row states the accepted rule exactly: a duplicated **or empty** `activationOrder` is rejected `XCOM-DECODE-SHAPE`, and a reordered-but-complete, reference-closed sequence is accepted and preserved verbatim. | The `T20-ORD-04` row now states the duplicate/empty rejection at the `activationOrder` target and that a reordered-but-complete, reference-closed sequence is accepted and preserved verbatim, noting `activationOrder` is an explicit sequence (no ascending rule). | Design text now matches `T20OrderingEquivalence.ActivationOrderIsDuplicateFree` (`t020_ordering_equivalence_tests.cpp` lines 89–105) and the accepted decoder `require_unique_identifiers(..., require_non_empty = true)`; `ctest -L t020-ordering-equivalence` 8/8 and the Python module 7/7 pass (C15, C16). |
| `T020-IR-002` (low) | Either strengthen `T20-ORD-06` to compare the complete decoded value, or narrow the `detailed-design.md` §4 line 151 (`T20-ORD-06`) wording to the precise field set the test compares; prefer the documentation-only narrowing. | Option (b): the `T20-ORD-06` row now names exactly the compared fields (outcome, code, digest `value`/`algorithm`, `plan_version`, `status`, `activation_order`, the `endpoints`/`provenance.resources` counts, `input_resolution.time`, `policies.deadline_ms`) and points whole-value identity to `T20-ORD-01`/`T20-ORD-02` and `T20-REG-01`. | Design text now matches `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue` (`t020_ordering_equivalence_tests.cpp` lines 133–155); the canonical-byte/digest identity and regression-field goldens are unchanged and still pass (C15, C16). |
| Label correction (found during closure) | Make the per-suite CTest selection commands declared in `verification-plan.md` §3 executable, without weakening any check. | `src/xverse/xcom/CMakeLists.txt` (shared path) now registers each T020 target under the single label `t020-<kind>` instead of the semicolon list `"t020;<kind>"`; `detailed-design.md` §2.2, `verification-plan.md` §2.3, and this record are reconciled to that label. The five targets, executable names, test sources, and case counts are unchanged. | `ctest -N -L <kind>` now selects 8/14/9/11/10 cases for ordering-equivalence/malformed-plan/drift/bound-matrix/regression (was 0 for each); `ctest -L t020` still selects 52; `ctest -L t020-ordering-equivalence --output-on-failure` = 8/8 (C15b). |

The two findings were documentation/traceability only: no `T20-ORD-04`/`T20-ORD-06` assertion, expected
result, or golden changed. The label correction changed only the CTest label string for the five T020
targets (allowed shared build wiring); no test assertion, expected result, golden, executable, or case
count changed. In all three cases the rev 1 case counts (`52` C++ + `7` Python) are unchanged. The
affected tests were re-run after the corrections and the deterministic gate was re-run against the
successor candidate revision.

### 9.1 Repair-pass re-verification

| ID | Command | Observed result |
| --- | --- | --- |
| C15 | `ctest --test-dir build/fabro-t020 -L t020-ordering-equivalence --output-on-failure` | `100% tests passed, 0 tests failed out of 8`, closing `T20-IR-001` and `T20-IR-002` |
| C15b | `ctest --test-dir build/fabro-t020 -N -L <kind>` for each kind, and `-L t020` | ordering-equivalence `8`, malformed-plan `14`, drift `9`, bound-matrix `11`, regression `10`, `t020` `52`; confirms the corrected labels select the intended tests (was `0` per kind) |
| C16 | `python3 -m pytest -q tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py` | `7 passed`, closing `T20-IR-001` and `T20-IR-002` |
| C17 | `python3 automation/xcom_feature_gate.py verify T020 1e289bf…` (re-run) | see §9.2 |
| C18 | `python3 automation/xcom_feature_gate.py review T020 1e289bf…` (re-run) | see §9.2 |

### 9.2 Successor gate result

The deterministic gate was re-run against the repaired candidate with the same environment-neutral
locator. The observed outputs are recorded here: `verify` →
`{"ok": true, "task_id": "T020", "changed_paths": 15, "checks": ["pytest", "ctest:246"]}`;
`review` → `{"ok": true, "task_id": "T020", "verdict": "pass"}`. The changed-path set is unchanged
(the 15 paths of §2), the T020 checkbox remains marked, and `git diff --check` remains clean. The
successor internal review (`docs/engineering/xcom/t020/internal-review.json`, revision 2) carries an
empty `findings` list and records both findings as resolved.

## 10. Repair-pass closure record (revisions 3–4) — deterministic-gate flake

A successor `verify` run against the revised-2 candidate failed with
`command failed (8): ctest --test-dir build/fabro-t020 --output-on-failure: Errors while running CTest`.
The failing CTest test was identified. Revision 3 initially attempted to close it by changing the
pre-existing T025 benchmark's CTest registration; the successor internal review (`T020-IR-003`, major)
correctly held that this edited a later task's accepted test outside T020's declared scope, so revision 4
**reverts** that change and records the benchmark as an external dependency/blocker instead.
**No T020 requirement, planned check, case, expected result, golden, or test is changed or weakened by this
repair, and no later task's artifact is modified.**

### 10.1 Diagnosis

| ID | Observation | Evidence |
| --- | --- | --- |
| D1 | Exactly one test failed: `246 - xcom_observation_disabled_benchmark`; the other 245 (including all 52 `t020` and all 38 `t019` cases) passed. | `ctest --test-dir build/fabro-t020 --output-on-failure --parallel 4` → `99% tests passed, 1 tests failed out of 246`; failing list `246 - xcom_observation_disabled_benchmark` |
| D2 | The failing test is **not** a T020 artifact. It is the pre-existing `performance;observation` benchmark registered at `src/xverse/xcom/CMakeLists.txt` (target `xverse_xcom_observation_disabled_benchmark`) over `tests/xcom/observation/integration/disabled_tap_benchmark.cpp`, owned by the observation slice (`T-OBS`/T025), not by T020. | `src/xverse/xcom/CMakeLists.txt` `add_test(NAME xcom_observation_disabled_benchmark ...)`; `tests/xcom/observation/**` is outside the T020 authorised path set of [`verification-plan.md`](verification-plan.md) §2.2 |
| D3 | The test asserts a **timing** property: it fails when either paired median regression exceeds `2.0%`. The failing run measured `paired_median_latency_regression_percent=2.01356` and `paired_median_throughput_regression_percent=1.97382` against `accepted_threshold_percent=2`, i.e. a margin of ~0.01%. | benchmark stdout in the failing `ctest` log (`latency_threshold=FAIL`, `throughput_threshold=FAIL`) |
| D4 | The measurement is host-noise limited, not concurrency limited: within a single failing run the per-sample regressions ranged from about `-10%` to `+22%` while the per-sample median landed at ~`2%`, and the test failed with `2.01356`/`2.16431`/`2.31984`/`2.49566` in different runs. | benchmark per-sample output; repeated full-suite logs |
| D5 | The flake is **independent of T020**: the untouched pre-T020 build `build/fabro-t019` (194 tests, no T020 targets) fails on the same benchmark too. In an interleaved paired comparison the pre-T020 build failed `3/20` runs and the T020 build failed `1/20` runs; in separate batches the pre-T020 build failed `2/30` and the T020 build (rev 2) failed `2/14`. | repeated `ctest --test-dir build/fabro-t019 --output-on-failure --parallel 4` runs |
| D6 | The test also fails when it is run **alone** (a single-test `ctest` run of just the benchmark reproduces the failure), so plain test-concurrency is not the only cause. | repeated single-test `ctest -R xcom_observation_disabled_benchmark` runs reproduce the failure with no other test in flight |
| D7 | The accepted benchmark evidence was recorded from an **uncontended solo** invocation and passed with roughly 2.7x margin (`0.742595%` predecessor, `0.94562%` successor). The deterministic gate instead runs the whole 246-test suite in parallel on a loaded host. | `docs/engineering/xcom/t025/protected-evidence/predecessor-observation-all.log` (`1/1 Test ... Passed`), `successor-predecessor-observation-all.log` |

### 10.2 Disposition (revision 4) — no T025 artifact changed

The rev-3 change was **not** retained. The candidate for revision 4 leaves the pre-existing
`xcom_observation_disabled_benchmark` registration exactly as in baseline
`1e289bfe6234553df94eb25065371f7d423fad88`
(`set_tests_properties(xcom_observation_disabled_benchmark PROPERTIES LABELS "performance;observation")`),
with no `RUN_SERIAL` property, no source, threshold, sampling, or assertion change, and no in-file comment.
The only `src/xverse/xcom/CMakeLists.txt` change is the T020 `foreach` block that adds the five
`t020`-labelled CTest targets. The benchmark is owned by the observation slice (`T-OBS`/`T-STIM`, task T025,
accepted at revision `4b01586`); altering its accepted test configuration is outside T020's declared scope
("new CTest targets and labels only"), so revision 4 restores the baseline registration and records the flake
as an **external dependency** (§10.3) rather than an applied T020 change. A remedy, if desired, belongs in a
separate T025 successor candidate with its own authorisation and review.

### 10.3 External dependency / blocker and non-claims

- **L-6 (external, pre-existing host-timing sensitivity — not a T020 defect, not repaired under T020).** The
  benchmark compares a 2% paired-median threshold against a host whose timing noise is of the same order
  (D3–D6); it can therefore still fail intermittently in the shared full-suite gate even when isolated (D5
  shows the untouched pre-T020 build failing identically). Making it deterministic would require changing
  that accepted test's tolerance, sampling, or acceptance rule (or removing it from the default suite), which
  would weaken or alter a check owned by the observation slice (T025) and is **not** within T020's
  authorisation. It is recorded here and in [`verification-plan.md`](verification-plan.md) §13 as an external
  dependency/blocker for the full-suite gate; no T020-visible defect remains and no T025 artifact is modified.
- The revision-4 disposition adds no test, removes no test, and changes no case count: the suite remains
  `246` tests (`194` pre-existing + `52` T020) and the T020 suite remains `52` C++ + `7` Python cases.
- No production source, schema, contract, fixture, decoder, or other task's test source is changed. No
  communication item, transport, network peer, or legacy artifact is touched.

### 10.4 Re-verification after the revision-4 revert

| ID | Command | Observed result |
| --- | --- | --- |
| C19 | `cmake -S . -B build/fabro-t020 -G Ninja -DCMAKE_BUILD_TYPE=Debug`; `cmake --build build/fabro-t020 --parallel 4` | configure and build succeeded; 246 tests discovered |
| C20 | `git diff 1e289bfe6234553df94eb25065371f7d423fad88 -- src/xverse/xcom/CMakeLists.txt` | only the T020 `foreach` block adding the five `t020` targets; no hunk touches `xcom_observation_disabled_benchmark` |
| C20b | `ctest --test-dir build/fabro-t020 --show-only=json-v1` (PROPERTIES of test 246) | no `RUN_SERIAL` property; `LABELS` = `["observation","performance"]` (baseline registration) |
| C21 | `ctest --test-dir build/fabro-t020 -N -L t020`, and `-N -L <kind>` for each kind | `t020` `52`; ordering-equivalence `8`, malformed-plan `14`, drift `9`, bound-matrix `11`, regression `10` |
| C22 | `ctest --test-dir build/fabro-t020 -L t020 --output-on-failure --parallel 4` | `100% tests passed, 0 tests failed out of 52` |
| C23 | `python3 -m pytest -q tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py` | `7 passed` |
| C24 | `ctest --test-dir build/fabro-t020 --output-on-failure --parallel 4` (full suite, repeated) | T020-suite result is deterministic `52/52`; the only intermittent failure is the external T025 benchmark of D1 (L-6), identically present on the untouched pre-T020 `build/fabro-t019` build (D5) |
