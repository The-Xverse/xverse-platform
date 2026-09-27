# T020 Verification Plan — Named Checks, Commands, Negative Cases, and Expected Results (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T020 |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 2 (rev 2 appends the repair-pass closure record in §12; the rev 1 named checks, cases, and expected results are unchanged) |
| Baseline revision | `1e289bfe6234553df94eb25065371f7d423fad88` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Test framework | GoogleTest/gmock via the admitted offline GTest prefix (CTest labels `t020-<kind>`) plus Python 3.11+ `pytest` |

This plan is written **before** implementation. The implementation must realise every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.

Deterministic inputs are used throughout: the committed T017 plan fixtures (read-only), the committed plan and
Profile schemas (read-only), and bounded, repository-owned, public-safe inline synthetic documents and
controlled mutations. No network, production workload, or legacy repository is touched.

## 2. Build and execution environment

### 2.1 Deterministic gate (primary)

From the repository root (the gate is invoked by the Workflow harness as
`automation/xcom_feature_gate.py`; no host-specific absolute path is retained):

```sh
python3 automation/xcom_feature_gate.py verify T020 1e289bfe6234553df94eb25065371f7d423fad88
```

For T020 this gate requires:

- `docs/engineering/xcom/t020/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present;
- the T020 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the plan
  stage leaves it unchecked, per the stage instruction);
- a changed path under `tests/` (the suites);
- `git diff --check <baseline> --` clean;
- a passing `python3 -m pytest -q`;
- a passing `cmake` configure/build and a `ctest` run that discovers `Total Tests ≥ 1` and passes.

The gate performs:

```sh
python3 -m pytest -q
cmake -S . -B build/fabro-t020 -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/fabro-t020 --parallel 4
ctest --test-dir build/fabro-t020 -N
ctest --test-dir build/fabro-t020 --output-on-failure --parallel 4
```

Supporting commands (same tools, no network):

```sh
cmake --build build/fabro-t020 --target xverse_xcom_activation_plan_t020_ordering_equivalence_tests
ctest --test-dir build/fabro-t020 -L t020 --output-on-failure
python3 -m pytest -q tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py
git rev-parse 1e289bfe6234553df94eb25065371f7d423fad88
git diff --name-only 1e289bfe6234553df94eb25065371f7d423fad88 --
git diff --check 1e289bfe6234553df94eb25065371f7d423fad88 --
```

`git rev-parse` for the baseline must print the baseline SHA, proving the binding resolves.

The gate is invoked operationally by the Workflow harness (`automation/xcom_feature_gate.py`), which is
workflow infrastructure rather than T020 artifact content. The retained work products reference it only by that
environment-neutral locator, so the public-safe artifact set carries no absolute host path; see
`requirements.md` §2.4.

### 2.2 T020 authorized-path set (external boundary check)

`git diff --name-only 1e289bf… --` must be a subset of:

```text
tests/xcom/activation_plan/t020_support.hpp
tests/xcom/activation_plan/t020_ordering_equivalence_tests.cpp
tests/xcom/activation_plan/t020_malformed_plan_tests.cpp
tests/xcom/activation_plan/t020_drift_tests.cpp
tests/xcom/activation_plan/t020_bound_matrix_tests.cpp
tests/xcom/activation_plan/t020_regression_tests.cpp
tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py
src/xverse/xcom/CMakeLists.txt                           # shared build wiring, CTest targets only
cmake/XComOfflineDependencies.cmake                      # shared, only if the A-1 fallback is required
docs/engineering/xcom/t020/
reports/xcom-queue/t020-package.json
specs/007-xcom-core/tasks.md                             # shared path, T020 checkbox line only
```

No path under `src/xverse/xcom/include/`, `src/xverse/xcom/src/`, `src/xverse_xdl/`, `scripts/`, `proto/`,
`xdl/`, `Doxyfile`, `pyproject.toml`, `tests/test_xcom_plan.py`, `tests/xcom/activation_plan/decoder_*.cpp`,
`tests/xcom/activation_plan/test_*.py`, `tests/xcom/activation_plan/fixtures/`, or
`docs/engineering/xcom/t017/`–`t019/` may appear. This set is declared in the T007 `T-XDL` exclusive/shared
lists (`docs/engineering/xcom/task-ownership.json`); the external boundary check is performed by the
deterministic gate and the review stage because the suites cannot run `git`.

### 2.3 Test targets and case mapping

| Target | Source | Cases |
| --- | --- | --- |
| `xverse_xcom_activation_plan_t020_ordering_equivalence_tests` | `tests/xcom/activation_plan/t020_ordering_equivalence_tests.cpp` | `T20-ORD-01`..`T20-ORD-08`; `T20-DET-01`..`T20-DET-04` |
| `xverse_xcom_activation_plan_t020_malformed_plan_tests` | `tests/xcom/activation_plan/t020_malformed_plan_tests.cpp` | `T20-MAL-01`..`T20-MAL-14` |
| `xverse_xcom_activation_plan_t020_drift_tests` | `tests/xcom/activation_plan/t020_drift_tests.cpp` | `T20-DRF-01`..`T20-DRF-09` |
| `xverse_xcom_activation_plan_t020_bound_matrix_tests` | `tests/xcom/activation_plan/t020_bound_matrix_tests.cpp` | `T20-BND-01`..`T20-BND-11` |
| `xverse_xcom_activation_plan_t020_regression_tests` | `tests/xcom/activation_plan/t020_regression_tests.cpp` | `T20-REG-01`..`T20-REG-10` |
| `pytest` module | `tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py` | `T20-ORD-01/02/05`, `T20-REG-03/07`, `T20-MAL-06/08`, `T20-G03`, `T20-G05` |

All C++ targets are registered with `gtest_discover_tests(... PROPERTIES LABELS "t020-<kind>")` (rev 2); the
gate discovers them via `ctest -N` and runs them via `ctest`. A single hyphenated label is used because the
admitted CMake 3.22 `gtest_discover_tests` splits a semicolon-separated label list and registers only its first
element; CTest `-L` is a regular-expression match, so both `ctest -L t020` (all 52 T020 cases) and the per-suite
`ctest -L <kind>` commands in §3 select the intended tests. The Python module is discovered by the gate's
`pytest`. The T017/T018 Python tests, the T019 decoder tests, and every other CTest target are unchanged.

### 2.4 Environment prerequisite (A-1)

The gate's `cmake` configure requires the already-admitted offline inputs documented in
`docs/engineering/xcom/build-environment.md` and `docs/engineering/xcom/t025/test-dependency-admission.md`:

| Input | Purpose |
| --- | --- |
| `XVERSE_XCOM_TOOLCHAIN` | admitted dependency prefix (nlohmann/json, protobuf, gRPC, clang-tidy) |
| `XVERSE_XCOM_PACKAGE_MANIFEST` | twelve-entry package manifest beside the retained packages |
| `XVERSE_XCOM_T025_TEST_TOOLCHAIN` | admitted GTest/gmock prefix used for the test targets |

These inputs are provisioned outside the repository and are not part of any Git artifact. The gate inherits the
run process environment. **If any input is absent, `cmake` fails in `xverse_xcom_admit_offline_dependencies`
before any T020 suite is built.** The implementation stage must run the gate's exact command first and, if it
fails solely for this reason, reuse the same narrow A-1 resolution T019 recorded:

1. read `XVERSE_XCOM_TOOLCHAIN`/`XVERSE_XCOM_PACKAGE_MANIFEST` (and the GTest prefix
   `XVERSE_XCOM_T025_TEST_TOOLCHAIN`) from the environment when present, and otherwise from an explicit,
   previously admitted CMake cache value, exporting the value to the preflight child;
2. seed those explicit values with one configure carrying the admitted inputs; and
3. when `LD_LIBRARY_PATH` does not already name the admitted prefix's library directory
   (`<XVERSE_XCOM_TOOLCHAIN>/usr/lib/x86_64-linux-gnu`), prepend that **prefix-derived** directory so the
   preflight's locked-version executable probe can load the prefix's shared objects.

The hash-verified offline preflight must still run unchanged. Ambient discovery, network fetch, a disabled
preflight, a weakened admission check, or a committed host-specific path is prohibited. If the gate cannot be
satisfied this way, the implementation stage records a blocker rather than weakening the gate. Any change to
the shared `cmake/XComOfflineDependencies.cmake` or `src/xverse/xcom/CMakeLists.txt` made for this reason is
recorded in `implementation.md` and weakens no admission check.

## 3. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-20-01 | Ordering-equivalence: one canonical body and digest | `ctest -L ordering-equivalence`; `pytest tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py` | Equivalent member-order/whitespace/integral-number variants share one canonical byte string and one recomputed digest in both C++ and Python (`T20-ORD-01/02/06/07`) |
| CHK-20-02 | Declared ordering, uniqueness, and diagnostics | `ctest -L ordering-equivalence` | Each identity-bearing collection is asserted in declared key order; a reversed collection is rejected `XCOM-DECODE-SHAPE`; `activationOrder` is duplicate-free; decoded diagnostics are ordered deterministically (`T20-ORD-03/04/05`) |
| CHK-20-03 | Malformed-plan matrix fails closed | `ctest -L malformed-plan` | Every `T20-MAL-*` case is `rejected`/`failed` with its declared code and no decoded plan; no case is `accepted` |
| CHK-20-04 | Drift guard against the normative schema and goldens | `ctest -L drift` | Decoder member/enum/pattern/ordering-key/minimum/numeric tables equal `PLAN_SCHEMA`; `$defs/digest` equals the embedded-digest rule; the plan-version const, domain separator, fixture canonical-body hashes, and fixture digests equal their goldens; the Profile form vocabulary is the accepted five forms |
| CHK-20-05 | Bound matrix at/below/over and invalid limits | `ctest -L bound-matrix` | Each `DecodeLimits` member accepts within its bound; an over-byte/depth/node/entity input is `failed` `XCOM-DECODE-BOUND`; an over-length string is `rejected` `XCOM-DECODE-SHAPE`; a limit `< 1` is `failed` `XCOM-DECODE-UNKNOWN`; no breach returns a value |
| CHK-20-06 | Cross-language equivalence on committed fixtures | `ctest -L regression`; `pytest …` | The C++ decoder's recomputed digest/canonical-body hash and the Python validator's recomputation agree with the committed fixtures' golden values |
| CHK-20-07 | Regression goldens | `ctest -L regression`; `pytest …` | The fixtures decode to `accepted`; fixture file hashes, canonical-body hashes, recorded/recomputed digests, the 16 required members, the `DecodeLimits` defaults, the closed decode-code vocabulary, and the SHA-256 known answers equal their pinned values |
| CHK-20-08 | Gate discovery and execution | `ctest -N`; `ctest`; `pytest -q` | `Total Tests ≥ 1`; the five `t020`-labelled suites and the pytest module pass together with the existing suites; no existing test's source, command, thresholds, or expected result is modified |
| CHK-20-09 | Governance, boundary, and dependency | external `git diff --name-only`; source inspection | changed set ⊆ §2.2; baseline binds; the C++ suites include only the standard library, `nlohmann/json`, GTest, and the decoder header; the Python module imports only the standard library and the repository's own modules; `XCOM-SW-XDL-001/002/003`/`XCOM-SW-CORE-003` links resolve; REF-002 promoted set empty |
| CHK-20-10 | No existing test weakened, no production path changed | `git diff --name-only`; source inspection | no `decoder_*.cpp`, T017/T018 Python test, fixture, schema, contract, or production source path appears; the T020 checkbox is marked only in the implementation stage |

## 4. Ordering-equivalence and determinism cases

| ID | Case | Expected |
| --- | --- | --- |
| `T20-ORD-01` | Two synthetic bodies differing only in member order/whitespace | one canonical byte string (byte-equal outputs) |
| `T20-ORD-02` | `dump(3)` re-serialization of a committed fixture | same canonical bytes and recomputed digest as the original |
| `T20-ORD-03` | Reversed identity-bearing collection | `rejected` `XCOM-DECODE-SHAPE`, collection target, no plan |
| `T20-ORD-04` | Duplicated `activationOrder` entry | `rejected` `XCOM-DECODE-SHAPE`, no plan |
| `T20-ORD-05` | Decoded diagnostics across equivalent representations | identical, in declared order |
| `T20-ORD-06` | Reordered-but-equivalent document | identical outcome, code, digest, and decoded fields |
| `T20-ORD-07` | Integral-number variant (`100` vs `100.0`) | same canonical body and digest; decodes `accepted` |
| `T20-ORD-08` | Repeated decode and whitespace variants | identical outcome, code, and digest |
| `T20-DET-01` | `decode_activation_plan` run twice on the same bytes | identical outcome, code, and decoded value |
| `T20-DET-02` | Reordered-but-equivalent document (C++ and Python) | identical outcome, code, canonical bytes, and digest |
| `T20-DET-03` | Integral-number variants in a body | identical canonical bytes and digest |
| `T20-DET-04` | `sha256_hex` over the domain separator + canonical body | deterministic across runs and equal to the Python reference |

## 5. Malformed-plan cases (`rejected` unless stated)

| ID | Injected defect | Code / target |
| --- | --- | --- |
| `T20-MAL-01` | Truncated document at several byte offsets | `XCOM-DECODE-INPUT` / `xcom-plan` |
| `T20-MAL-02` | Unbalanced brace/bracket | `XCOM-DECODE-INPUT` / `xcom-plan` |
| `T20-MAL-03` | Trailing content or a second document | `XCOM-DECODE-INPUT` / `xcom-plan` |
| `T20-MAL-04` | Repeated member at top level, `provenance`, `policies`, `endpoints[]` | `XCOM-DECODE-INPUT` / `xcom-plan` |
| `T20-MAL-05` | Non-object root (`[]`, `42`, `true`, `null`, `"plan"`) | `XCOM-DECODE-INPUT` / `xcom-plan` |
| `T20-MAL-06` | Wrong JSON type for a collection/scalar member | `XCOM-DECODE-SHAPE` / affected object |
| `T20-MAL-07` | `null` where an object/array is required | `XCOM-DECODE-SHAPE` / affected object |
| `T20-MAL-08` | Each of the 16 required members dropped in turn | `XCOM-DECODE-SHAPE` / `xcom-plan` |
| `T20-MAL-09` | One unknown member in each nested object | `XCOM-DECODE-SHAPE` / affected object |
| `T20-MAL-10` | Invalid UTF-8 byte in a string value | `XCOM-DECODE-INPUT` / `xcom-plan` |
| `T20-MAL-11` | Empty and whitespace-only documents | `XCOM-DECODE-INPUT` / `xcom-plan` |
| `T20-MAL-12` | Nesting depth above the default `max_depth` | **failed** `XCOM-DECODE-BOUND` / `xcom-plan` |
| `T20-MAL-13` | Aggregate: no malformed case returns a decoded plan | no plan; never `accepted` |
| `T20-MAL-14` | T020 malformed vectors are distinct from the T019 `NEG-D*` inputs | source-inspection guard passes; no T019 file edited |

## 6. Drift cases

| ID | Guard | Expected |
| --- | --- | --- |
| `T20-DRF-01` | 16 required members, `additionalProperties == false`, closed `$defs` objects | equal to `PLAN_SCHEMA` |
| `T20-DRF-02` | Closed enums of §2.6 | decoder-accepted/rejected vocabulary equals each schema enum |
| `T20-DRF-03` | Identifier/version/digest/generator-task/diagnostic-code patterns | conforming accepted, non-conforming `rejected` `XCOM-DECODE-SHAPE`; patterns equal the schema |
| `T20-DRF-04` | Ordering keys, `uniqueItems`, `minItems` (`capabilities`=1, `resources`=1, `activationOrder`=1) | equal to `PLAN_SCHEMA` |
| `T20-DRF-05` | `deadlineMs` 0..600000, `retry` 0..64, `queueDepth` 1..65536 | equal to the schema; out-of-range/non-integer `rejected` `XCOM-DECODE-SHAPE` |
| `T20-DRF-06` | `$defs/digest` closed sub-schema for every embedded digest | equal to the decoder rule; violation `rejected` `XCOM-DECODE-SHAPE` |
| `T20-DRF-07` | `planVersion` const | equal to `"1"`; `≠ "1"` `rejected` `XCOM-DECODE-VERSION` |
| `T20-DRF-08` | Domain separator and fixture canonical-body/digest goldens | equal to the pinned values |
| `T20-DRF-09` | Profile form vocabulary in `PROFILE_SCHEMA` | exactly the accepted five forms; no sixth |

## 7. Bound and regression cases

### 7.1 Bound matrix

| ID | Bound exercised | Expected |
| --- | --- | --- |
| `T20-BND-01` | `max_bytes` at/one-below the fixture length | accept / **failed** `XCOM-DECODE-BOUND`, no plan |
| `T20-BND-02` | `max_depth` at/one-above | accept / **failed** `XCOM-DECODE-BOUND` |
| `T20-BND-03` | `max_nodes` at/one-above | accept / **failed** `XCOM-DECODE-BOUND` |
| `T20-BND-04` | `max_string_length` one-over | **rejected** `XCOM-DECODE-SHAPE`, no plan |
| `T20-BND-05` | `max_contracts` at/one-below | accept / **failed** `XCOM-DECODE-BOUND` |
| `T20-BND-06` | `max_endpoints` at/one-below | accept / **failed** `XCOM-DECODE-BOUND` |
| `T20-BND-07` | `max_routes` at/one-below | accept / **failed** `XCOM-DECODE-BOUND` |
| `T20-BND-08` | `max_providers` at/one-below | accept / **failed** `XCOM-DECODE-BOUND` |
| `T20-BND-09` | `max_observation_points`, `max_clock_domains` each at/one-below | accept / **failed** `XCOM-DECODE-BOUND` |
| `T20-BND-10` | `max_diagnostics`, `max_activation_order`, `max_provenance_resources` each at/one-below | accept / **failed** `XCOM-DECODE-BOUND` |
| `T20-BND-11` | each of the 13 limits set to `0` | **failed** `XCOM-DECODE-UNKNOWN`, no plan |

### 7.2 Regression

| ID | Pinned behaviour | Expected |
| --- | --- | --- |
| `T20-REG-01` | Activatable fixture decode and field goldens | `accepted`; every pinned field/count equals the fixture |
| `T20-REG-02` | Inspectable fixture decode | `accepted`; `status = "inspectable"`; pinned unresolved member |
| `T20-REG-03` | Recorded and recomputed digests | equal `kFixture*Digest` |
| `T20-REG-04` | SHA-256 FIPS known answers | unchanged |
| `T20-REG-05` | Domain separator | with it matches; without it or over a non-canonical body `rejected` `XCOM-DECODE-DIGEST` |
| `T20-REG-06` | 16 required members, `additionalProperties == false`, closed `$defs` | unchanged |
| `T20-REG-07` | Fixture file SHA-256 | equal `kFixture*FileSha256` |
| `T20-REG-08` | `sha256(canonical_plan_body_bytes(fixture))` | equal `kFixture*BodySha256` |
| `T20-REG-09` | 13 `DecodeLimits` defaults | unchanged; `is_valid` true |
| `T20-REG-10` | Closed decode-code vocabulary and outcome mapping | exactly the nine declared codes; `BOUND`/`UNKNOWN` `failed`, rest `rejected` |

## 8. Exact planned tests (implementation stage)

The GoogleTest names below are authoritative: each appears as `TEST(<Suite>, <Test>)` in the named source, and
the plan's Python table is reconciled with the module by
`test_t020_verification_plan_lists_every_implemented_test`.

| Test | Family | Cases / asserts |
| --- | --- | --- |
| `tests/xcom/activation_plan/t020_ordering_equivalence_tests.cpp::T20OrderingEquivalence.EquivalentSyntheticPlansShareCanonicalBytes` | ordering | `T20-ORD-01`; CHK-20-01 |
| `…::T20OrderingEquivalence.ReorderedFixtureSharesCanonicalBytesAndDigest` | ordering | `T20-ORD-02`; CHK-20-01 |
| `…::T20OrderingEquivalence.DeclaredCollectionOrderingIsEnforced` | ordering | `T20-ORD-03`; CHK-20-02 |
| `…::T20OrderingEquivalence.ActivationOrderIsDuplicateFree` | ordering | `T20-ORD-04`; CHK-20-02 |
| `…::T20OrderingEquivalence.DecodedDiagnosticsAreOrderedDeterministically` | ordering | `T20-ORD-05`; CHK-20-02 |
| `…::T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue` | ordering | `T20-ORD-06`, `T20-DET-01`, `T20-DET-02` |
| `…::T20OrderingEquivalence.IntegralNumberVariantSharesCanonicalBody` | ordering | `T20-ORD-07`, `T20-DET-03` |
| `…::T20OrderingEquivalence.RepeatedDecodeAndWhitespaceVariantsAreIdentical` | determinism | `T20-ORD-08`, `T20-DET-01`, `T20-DET-04` |
| `tests/xcom/activation_plan/t020_malformed_plan_tests.cpp::T20MalformedPlan.TruncatedDocumentsAreRejected` | malformed | `T20-MAL-01` |
| `…::T20MalformedPlan.UnbalancedDelimitersAreRejected` | malformed | `T20-MAL-02` |
| `…::T20MalformedPlan.TrailingContentIsRejected` | malformed | `T20-MAL-03` |
| `…::T20MalformedPlan.DuplicateMembersAtEachLevelAreRejected` | malformed | `T20-MAL-04` |
| `…::T20MalformedPlan.NonObjectRootsAreRejected` | malformed | `T20-MAL-05` |
| `…::T20MalformedPlan.WrongJsonTypesAreRejected` | malformed | `T20-MAL-06` |
| `…::T20MalformedPlan.NullWhereObjectOrArrayRequiredIsRejected` | malformed | `T20-MAL-07` |
| `…::T20MalformedPlan.MissingRequiredMembersAreRejected` | malformed | `T20-MAL-08` |
| `…::T20MalformedPlan.UnknownNestedMembersAreRejected` | malformed | `T20-MAL-09` |
| `…::T20MalformedPlan.InvalidUtf8IsRejected` | malformed | `T20-MAL-10` |
| `…::T20MalformedPlan.EmptyAndWhitespaceOnlyDocumentsAreRejected` | malformed | `T20-MAL-11` |
| `…::T20MalformedPlan.OverNestedDocumentsFailClosed` | malformed | `T20-MAL-12` |
| `…::T20MalformedPlan.MalformedPlansNeverReturnADecodedValue` | malformed | `T20-MAL-13`; CHK-20-03 |
| `…::T20MalformedPlan.MalformedMutationsRemainDistinctFromT019Cases` | malformed | `T20-MAL-14` |
| `tests/xcom/activation_plan/t020_drift_tests.cpp::T20Drift.RequiredMemberTableMatchesSchema` | drift | `T20-DRF-01` |
| `…::T20Drift.ClosedEnumTablesMatchSchema` | drift | `T20-DRF-02` |
| `…::T20Drift.PatternTablesMatchSchema` | drift | `T20-DRF-03` |
| `…::T20Drift.CollectionKeysAndMinimumsMatchSchema` | drift | `T20-DRF-04` |
| `…::T20Drift.NumericRangesMatchSchema` | drift | `T20-DRF-05` |
| `…::T20Drift.EmbeddedDigestSubSchemaMatchesDecoder` | drift | `T20-DRF-06` |
| `…::T20Drift.PlanVersionConstMatchesDecoder` | drift | `T20-DRF-07` |
| `…::T20Drift.DomainSeparatorAndGoldenDigestsAreStable` | drift | `T20-DRF-08`; CHK-20-04 |
| `…::T20Drift.ProfileFormVocabularyIsTheAcceptedFiveForms` | drift | `T20-DRF-09` |
| `tests/xcom/activation_plan/t020_bound_matrix_tests.cpp::T20BoundMatrix.ByteBoundAtAndOver` | bound | `T20-BND-01` |
| `…::T20BoundMatrix.DepthBoundAtAndOver` | bound | `T20-BND-02` |
| `…::T20BoundMatrix.NodeBoundAtAndOver` | bound | `T20-BND-03` |
| `…::T20BoundMatrix.StringLengthOverIsRejected` | bound | `T20-BND-04` |
| `…::T20BoundMatrix.ContractCapAtAndOver` | bound | `T20-BND-05` |
| `…::T20BoundMatrix.EndpointCapAtAndOver` | bound | `T20-BND-06` |
| `…::T20BoundMatrix.RouteCapAtAndOver` | bound | `T20-BND-07` |
| `…::T20BoundMatrix.ProviderCapAtAndOver` | bound | `T20-BND-08` |
| `…::T20BoundMatrix.ObservationPointAndClockDomainCapsAtAndOver` | bound | `T20-BND-09` |
| `…::T20BoundMatrix.DiagnosticActivationOrderAndResourceCapsAtAndOver` | bound | `T20-BND-10` |
| `…::T20BoundMatrix.EveryLimitBelowOneFailsClosed` | bound | `T20-BND-11`; CHK-20-05 |
| `tests/xcom/activation_plan/t020_regression_tests.cpp::T20Regression.ActivatableFixtureDecodesWithPinnedFields` | regression | `T20-REG-01` |
| `…::T20Regression.InspectableFixtureDecodesWithPinnedFields` | regression | `T20-REG-02` |
| `…::T20Regression.GoldenRecordedAndRecomputedDigests` | regression | `T20-REG-03`; CHK-20-06 |
| `…::T20Regression.Sha256KnownAnswersUnchanged` | regression | `T20-REG-04` |
| `…::T20Regression.DomainSeparatorRegression` | regression | `T20-REG-05` |
| `…::T20Regression.RequiredMemberSetAndClosedSchemaUnchanged` | regression | `T20-REG-06` |
| `…::T20Regression.FixtureBytesAreUnchanged` | regression | `T20-REG-07` |
| `…::T20Regression.GoldenCanonicalBodyHashIsStable` | regression | `T20-REG-08` |
| `…::T20Regression.DecodeLimitsDefaultsUnchanged` | regression | `T20-REG-09` |
| `…::T20Regression.DecodeCodeVocabularyIsClosed` | regression | `T20-REG-10`; CHK-20-07 |
| `tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py::test_t020_compiler_and_validator_agree_on_canonical_bytes` | ordering (py) | `T20-ORD-01` |
| `tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py::test_t020_equivalent_graphs_produce_byte_identical_plans` | ordering (py) | `T20-ORD-02`, `T20-DET-02` |
| `tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py::test_t020_diagnostic_ordering_is_deterministic` | ordering (py) | `T20-ORD-05` |
| `tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py::test_t020_committed_fixtures_match_reference_digest` | regression (py) | `T20-REG-03`, `T20-REG-07` |
| `tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py::test_t020_malformed_plan_matrix_is_rejected` | malformed (py) | `T20-MAL-06`, `T20-MAL-08` |
| `tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py::test_t020_module_is_offline_and_pure` | governance | `T20-G03` |
| `tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py::test_t020_verification_plan_lists_every_implemented_test` | traceability | `T20-G05`; CHK-20-08 |
| `ctest --test-dir build/fabro-t020 -L t020 --output-on-failure` | suite | the five T020 suites pass |
| `ctest --test-dir build/fabro-t020 --output-on-failure` | gate | the full CTest suite passes; no existing test's source, command, thresholds, or expected result is modified |
| `python3 -m pytest -q` | gate | the pytest suite passes; the T017/T018 tests are unchanged |

**Reconciliation rule.** `test_t020_verification_plan_lists_every_implemented_test` extracts this table's
`T20<Suite>.<Test>` names (pattern `T20[A-Za-z]+\.\w+`) and the C++ sources' `TEST(<Suite>, <Test>)` names
(pattern `TEST\((T20[A-Za-z]+),\s*(\w+)\)`), and this table's Python `::test_t020_…` names (pattern
`test_t020_[a-z0-9_]+`) and the module's `def test_t020_…(` names; the two sets must be equal in each language.
A missing or extra test fails the module.

## 9. Traceability of checks

| Requirement | Checks | Cases |
| --- | --- | --- |
| T020-SR-001 | CHK-20-01, CHK-20-02 | `T20-ORD-01`..`T20-ORD-08`; `T20-DET-01`..`T20-DET-04` |
| T020-SR-002 | CHK-20-03 | `T20-MAL-01`..`T20-MAL-14` |
| T020-SR-003 | CHK-20-04 | `T20-DRF-01`..`T20-DRF-09` |
| T020-SR-004 | CHK-20-05 | `T20-BND-01`..`T20-BND-11` |
| T020-SR-005 | CHK-20-06, CHK-20-07 | `T20-REG-01`..`T20-REG-10` |
| T020-SR-006 | CHK-20-08, CHK-20-10 | `ctest`/`pytest` gates |
| T020-SR-007 | CHK-20-09 | `T20-G01`..`T20-G05`; source inspection |

### 9.1 Boundary and governance cases

| ID | Defect | Expected |
| --- | --- | --- |
| `T20-G01` | The candidate changes a path outside the §2.2 authorized set (including any production source) | external `git diff --name-only` shows no such path |
| `T20-G02` | The candidate edits a T017/T018/T019 test, schema, contract, or fixture | no such path in the diff; no existing expected result changes |
| `T20-G03` | A suite contains a network/subprocess/filesystem-write call or an absolute host path | source inspection is clean; C++ suites use only the decoder API |
| `T20-G04` | A source/test/evidence file contains a credential, private address, or absolute host path | public-safety scan is clean |
| `T20-G05` | The T020 checkbox is marked complete in the plan stage, or an existing test/schema/contract is weakened | checkbox unchecked in the plan stage; review confirms no weakening |

### 9.2 Accepted planned-evidence token mapping

The accepted T010 unit design lists `XCOM-DU-011` planned evidence as the capability-level tokens `CHK-06`,
`CHK-09`, `NEG-21`, `NEG-22`, `NEG-23` and `XCOM-DU-010` as `CHK-09`, `NEG-42`, `NEG-43`. Those tokens are
T008/T010-scoped and are not T020 checks; they are realised for those units by the T017/T018/T019 check sets as
a whole, and T020 **extends** that evidence with `CHK-20-01`..`CHK-20-10` and
`T20-ORD-*`/`T20-MAL-*`/`T20-DRF-*`/`T20-BND-*`/`T20-REG-*`/`T20-DET-*`/`T20-G*` above. T020 does not edit the
T008/T010 work products; this note records the mapping so no accepted evidence identifier is left
unaccounted for. The `XCOM-SW-XDL-001/002/003`/`XCOM-SW-CORE-003` requirement links and the
`XCOM-DU-XDL-BASELINE`/`XCOM-T-XDL` locators are unchanged.

## 10. Expected results and limitations

- All checks and cases are deterministic and offline; the C++ suites call a pure decoder API and the Python
  module calls pure compiler/validator functions. No case starts a thread, opens a network socket, spawns a
  process, or writes a file.
- The suites prove the **derived-plan chain's** ordering equivalence, malformed-plan rejection, drift
  resistance, bounds, and regression over the bounded committed fixtures and declared synthetic vectors. They
  do not prove endpoint/route/provider activation, runtime behaviour, throughput, timing, compatibility, or
  production readiness; those belong to later tasks. The suites bind nothing and emit no communication item.
- **No concurrency bound applies.** T020 introduces no thread and no mutable shared state; determinism is
  asserted by repetition within one process.
- **Environment A-1.** The gate's `cmake`/`ctest` run requires the admitted offline inputs (§2.4); the
  resolution rule is stated there and must be recorded in `implementation.md`.
- The plan-stage candidate changes only documentation; the deterministic gate cannot pass until the
  implementation stage supplies the five C++ suites, the support header, the Python module, the build wiring,
  and `implementation.md`, and marks the T020 checkbox.

## 11. Evidence to retain with the candidate revision

- Gate command stdout/stderr and exit status, plus the `ctest -N` discovered-test count and the `pytest`
  collected/selected count.
- The `cmake` configure/build log, the `ctest -L t020` log, and the `pytest` log, bound to the exact candidate
  revision.
- The golden-value capture commands and values (fixture file digests, canonical-body hashes, recorded digests)
  for both committed fixtures.
- The exact admitted environment input identities (prefix/manifest/GTest prefix) and tool versions, and the
  A-1 resolution record if one was required.
- The candidate revision hash and `git diff --name-only`/`git diff --check` output.

Evidence must be bound to the exact candidate revision; missing, stale, or mismatched evidence cannot support
acceptance. This plan records no external-acceptance or Codex-review claim.

## 12. Repair-pass closure record (revision 2)

The read-only internal review recorded `T020-IR-001` and `T020-IR-002` as low-severity
documentation/traceability findings (recorded in `internal-review.json` revision 1). Each is closed in
revision 2 as follows; **no named check, case, expected result, golden value, assertion, or test in this
plan was changed or weakened**, and no production source, test source, schema, contract, or decoder was
changed. Closing the findings also confirmed that the per-suite CTest labels declared in §2.3/§3 were not
registered by the admitted CMake 3.22 toolchain; the label scheme is corrected (see `detailed-design.md`
§2.2 and `implementation.md` §9) so the §3 per-suite commands run, without changing any check.

| Finding | Closure | Evidence |
| --- | --- | --- |
| `T020-IR-001` | `detailed-design.md` §4 `T20-ORD-04` rev 2 now states the accepted rule exactly: a duplicated or empty `activationOrder` is rejected `XCOM-DECODE-SHAPE`, and a reordered-but-complete, reference-closed sequence is accepted and preserved verbatim. The plan's `T20-ORD-04` row (§4, line 166) already required only the duplicate rejection, so it is unchanged and remains accurate. | `ctest -L t020-ordering-equivalence` 8/8; `pytest` T020 module 7/7. |
| `T020-IR-002` | `detailed-design.md` §4 `T20-ORD-06` rev 2 now names exactly the decoded fields the test compares and points whole-value identity to `T20-ORD-01`/`T20-ORD-02` and `T20-REG-01`. The plan's `T20-ORD-06` expected result (§4, line 168, "identical outcome, code, digest, and decoded fields") remains a correct, weaker-than-documented statement and is unchanged. | `ctest -L t020-ordering-equivalence` 8/8; `pytest` T020 module 7/7. |
| Label correction | The single CTest label `t020-<kind>` is registered per target; the §3 per-suite commands (`ctest -L <kind>`) and the `ctest -L t020` shared selector both match it by CTest label regex. | `ctest -N -L <kind>` selects 8/14/9/11/10 and `-L t020` selects 52 (was 0 per kind, 52 shared). |

These corrections change no expected result; the rev 1 case set (`52` C++ + `7` Python) and every pinned
golden are unchanged. The successor deterministic-gate run (`verify` → `checks: ["pytest","ctest:246"]`,
`review` → `verdict: "pass"`) and the successor internal review (revision 2, empty `findings`) are bound
to the repaired candidate revision; see `implementation.md` §9.

## 13. Repair-pass closure record (revisions 3–4) — deterministic-gate flake

A successor `verify` run failed on the retained CTest suite
(`command failed (8): ctest --test-dir build/fabro-t020 --output-on-failure`). The single failing test was
the **pre-existing** `xcom_observation_disabled_benchmark` (`performance;observation`), not a T020 or T019
case and not any path authorised in §2.2. The benchmark compares a 2% paired-median timing threshold and
failed at `paired_median_latency_regression_percent=2.01356` (threshold `2`). It is host-timing-noise
limited and independent of T020: the same benchmark also fails intermittently on the untouched pre-T020
`build/fabro-t019` (194-test) build (`3/20` in an interleaved paired run, `2/30` in a separate batch), and
its accepted evidence was recorded from an uncontended solo run at `0.74%`/`0.95%` — see
`implementation.md` §10 for the full diagnosis (D1–D7) and numbers.

**Disposition (revision 4).** Revision 3 initially set `RUN_SERIAL TRUE` on that pre-existing test; the
successor internal review (`T020-IR-003`, major) held that this edited an accepted test owned by the
observation slice (T025, accepted at revision `4b01586`) outside T020's declared scope. Revision 4
therefore **reverts** `src/xverse/xcom/CMakeLists.txt` to the baseline registration
(`set_tests_properties(xcom_observation_disabled_benchmark PROPERTIES LABELS "performance;observation")`,
no `RUN_SERIAL`), so T020 changes **no** T025 test: the only diff hunk is the T020 `foreach` block adding the
five `t020`-labelled targets. **No named check in this plan is changed or weakened**, and the case set
(`52` C++ + `7` Python) and every pinned golden are unchanged.

**Recorded external dependency / blocker (not a T020 defect).** The benchmark remains sensitive to host
timing noise and can still fail intermittently in the shared full-suite gate; making it deterministic would
require changing that accepted test's tolerance, sampling, or acceptance rule (or removing it from the
default suite), which would weaken or alter a check owned by the observation slice (T025) and is outside
T020's authorisation. It is recorded here and as `implementation.md` §10 L-6, and any remedy belongs in a
separate T025 successor candidate with its own authorisation and review. The T020-owned result
(`ctest -L t020` = `52/52`, `pytest` = `7 passed`) is deterministic.
