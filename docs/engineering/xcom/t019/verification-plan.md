# T019 Verification Plan — Named Checks, Commands, Negative Cases, and Expected Results (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T019 |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `199de0baa1f50e1d429527b6d6525a6e5d8cf7cf` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Test framework | GoogleTest/gmock via the admitted offline GTest prefix; CTest labels `t019;unit` / `t019;negative` |

This plan is written **before** implementation. The implementation must realise every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.

Deterministic inputs are used throughout: the committed T017 plan fixtures (read-only) and bounded,
repository-owned, public-safe inline synthetic documents and controlled mutations. No network, production
workload, or legacy repository is touched.

## 2. Build and execution environment

### 2.1 Deterministic gate (primary)

From the repository root (the gate is invoked by the Workflow harness as
`automation/xcom_feature_gate.py`; no host-specific absolute path is retained):

```sh
python3 automation/xcom_feature_gate.py verify T019 199de0baa1f50e1d429527b6d6525a6e5d8cf7cf
```

For T019 this gate requires:

- `docs/engineering/xcom/t019/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present;
- the T019 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the plan
  stage leaves it unchecked, per the stage instruction);
- a changed path under `src/xverse/xcom/` (the decoder);
- a changed path under `tests/` (the decoder tests);
- `git diff --check <baseline> --` clean;
- a passing `cmake` configure/build and a `ctest` run that discovers `Total Tests ≥ 1` and passes.

The gate performs:

```sh
cmake -S . -B build/fabro-t019 -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/fabro-t019 --parallel 4
ctest --test-dir build/fabro-t019 -N
ctest --test-dir build/fabro-t019 --output-on-failure --parallel 4
```

Supporting commands (same tools, no network):

```sh
cmake --build build/fabro-t019 --target xverse_xcom_activation_plan
ctest --test-dir build/fabro-t019 -L t019 --output-on-failure
git rev-parse 199de0baa1f50e1d429527b6d6525a6e5d8cf7cf
git diff --name-only 199de0baa1f50e1d429527b6d6525a6e5d8cf7cf --
git diff --check 199de0baa1f50e1d429527b6d6525a6e5d8cf7cf --
```

`git rev-parse` for the baseline must print the baseline SHA, proving the binding resolves.

The gate is invoked operationally by the Workflow harness (`automation/xcom_feature_gate.py`), which is
workflow infrastructure rather than T019 artifact content. The retained work products reference it only by
that environment-neutral locator, so the public-safe artifact set carries no absolute host path; see
`requirements.md` §2.4.

### 2.2 T019 authorized-path set (external boundary check)

`git diff --name-only 199de0b… --` must be a subset of:

```text
src/xverse/xcom/include/xverse/xcom/activation_plan.hpp
src/xverse/xcom/src/activation_plan.cpp
tests/xcom/activation_plan/                              # new decoder_*.cpp only; T017 modules/fixtures unchanged
src/xverse/xcom/CMakeLists.txt                           # shared build wiring
cmake/XComOfflineDependencies.cmake                      # shared, only if the A-1 fallback is required
docs/engineering/xcom/t019/
reports/xcom-queue/t019-package.json
specs/007-xcom-core/tasks.md                             # shared path, T019 checkbox line only
```

No path under `src/xverse_xdl/`, `proto/`, `xdl/`, `Doxyfile`, `scripts/`, `docs/engineering/xcom/t017/`,
`docs/engineering/xcom/t018/`, `tests/test_xcom_plan.py`, or the committed T017 fixture directories may
appear. This set is declared in the T007 `T-XDL` exclusive/shared lists
(`docs/engineering/xcom/task-ownership.json`); the external boundary check is performed by the deterministic
gate and the review stage because the decoder cannot run `git`.

### 2.3 Test targets and case mapping

| Target | Source | Cases |
| --- | --- | --- |
| `xverse_xcom_activation_plan_unit_tests` | `tests/xcom/activation_plan/decoder_unit_tests.cpp` | CHK-01..CHK-04, CHK-06, CHK-08, CHK-10; DET-01..DET-04; BND-05 |
| `xverse_xcom_activation_plan_negative_tests` | `tests/xcom/activation_plan/decoder_negative_tests.cpp` | NEG-D01..NEG-D22; CHK-05, CHK-07; BND-01..BND-03 |

Both are registered with `gtest_discover_tests(... PROPERTIES LABELS "t019;<kind>")`; the gate discovers them
via `ctest -N` and runs them via `ctest`. The existing T017 Python tests and every other CTest target are
unchanged.

### 2.4 Environment prerequisite (A-1)

The gate's `cmake` configure requires the already-admitted offline inputs documented in
`docs/engineering/xcom/build-environment.md` and `docs/engineering/xcom/t025/test-dependency-admission.md`:

| Input | Purpose |
| --- | --- |
| `XVERSE_XCOM_TOOLCHAIN` | admitted dependency prefix (nlohmann/json, protobuf, gRPC, clang-tidy) |
| `XVERSE_XCOM_PACKAGE_MANIFEST` | twelve-entry package manifest beside the retained packages |
| `XVERSE_XCOM_T025_TEST_TOOLCHAIN` | admitted GTest/gmock prefix used for the test targets |

These inputs are provisioned outside the repository and are not part of any Git artifact. The gate inherits
the run process environment. **If any input is absent, `cmake` fails in
`xverse_xcom_admit_offline_dependencies` before any T019 code is built.** The implementation stage must run
the gate's exact command first and, if it fails solely for this reason, resolve it as follows:

1. read `XVERSE_XCOM_TOOLCHAIN`/`XVERSE_XCOM_PACKAGE_MANIFEST` (and the GTest prefix
   `XVERSE_XCOM_T025_TEST_TOOLCHAIN`) from the environment when present, and otherwise from an explicit,
   previously admitted CMake cache value, exporting the value to the preflight child;
2. seed those explicit values with one configure carrying the admitted inputs; and
3. when `LD_LIBRARY_PATH` does not already name the admitted prefix's library directory
   (`<XVERSE_XCOM_TOOLCHAIN>/usr/lib/x86_64-linux-gnu`), prepend that **prefix-derived** directory so the
   preflight's locked-version executable probe can load the prefix's shared objects. This derives only from
   the explicit admitted prefix (it is applied only when the directory is absent and adds no ambient path)
   and is the narrow A-1 authorization for the shared-path edit recorded in `implementation.md`.

The hash-verified offline preflight must still run unchanged. Ambient discovery, network fetch, a disabled
preflight, a weakened admission check, or a committed host-specific path is prohibited. If the gate cannot be
satisfied this way, the implementation stage records a blocker rather than weakening the gate. Any change to
the shared `cmake/XComOfflineDependencies.cmake` or `src/xverse/xcom/CMakeLists.txt` made for this reason is
recorded in `implementation.md` and weakens no admission check.

## 3. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Decoder builds and exposes its API | `cmake --build … --target xverse_xcom_activation_plan`; `decoder_unit_tests` inspection | `xverse_xcom_activation_plan` builds with `-Werror`; `DecodeLimits`, `DecodeOutcome`, `DecodeError`, `DecodeResult`, `ActivationPlan`, `sha256_hex`, `canonical_plan_body_bytes`, `recompute_plan_digest`, `decode_activation_plan`, `is_valid` are declared in `xverse::xcom::plan` |
| CHK-02 | Positive decode of the committed fixtures | `Decode.PositiveActivatableFixture`, `Decode.PositiveInspectableFixture` | both committed T017 plan fixtures decode to `accepted` with an engaged `ActivationPlan` |
| CHK-03 | Independent digest agreement | `Decode.DigestAgreesWithT017Fixture` | the decoder's `recompute_plan_digest` equals each fixture's recorded `digest.value` (and the T017 validator's value) |
| CHK-04 | SHA-256 and version fidelity | `Decode.Sha256KnownAnswers`; negative `NEG-D09` | SHA-256 known answers hold; `planVersion` ≠ `"1"` is rejected with `XCOM-DECODE-VERSION` |
| CHK-05 | Capability/cross-reference/status closure | `decoder_negative_tests` `NEG-D13..NEG-D16`; `Decode.PositiveInspectableFixture`, `Decode.InspectableUnresolvedCapabilityIsAccepted`, `Decode.InspectableUnresolvedReferenceIsAccepted` | an insufficient capability or unresolved reference is rejected with the declared code and identifier **when the plan declares the governing resolution state `resolved`**; a schema-valid `inspectable` plan that records an unresolved capability/schema/identity state (the accepted T018 producer shape) is accepted as non-activatable; an `activatable` plan with an unresolved member is rejected |
| CHK-06 | Shape/vocabulary/order, closed digest sub-schema, and schema drift guard | `NEG-D04..NEG-D08`, `NEG-D08DigestPattern`, `NEG-D17`, `NEG-D18`; table-vs-schema test | each shape defect (including an embedded `provenance.graphDigest`/`provenance.resources[].sourceDigest` algorithm or value-pattern violation) is rejected with `XCOM-DECODE-SHAPE`; the decoder's member/enum/pattern tables equal `PLAN_SCHEMA` |
| CHK-07 | Bounds enforced, fail closed | `NEG-D19`, `NEG-D20`; `BND-01..BND-05` | an over-byte/depth/node/entity input is `failed` with `XCOM-DECODE-BOUND` and no value; an invalid `DecodeLimits` (member < 1) is `failed` with no value |
| CHK-08 | Canonicalization invariance | `Decode.CanonicalBodyIsMemberSortedWhitespaceFree`, `Decode.ReorderedDocumentSameDigestAndResult` | member-reordered, whitespace-varied, and integral-number-variant bodies share one canonical byte string and digest; the canonical body is member-ordered and whitespace-free |
| CHK-09 | Governance, boundary, and dependency | external `git diff --name-only`; source inspection | changed set ⊆ §2.2; baseline binds; the decoder includes only the standard library and `nlohmann/json`; `XCOM-SW-XDL-003`/`XCOM-SW-CORE-003` links resolve; REF-002 promoted set empty |
| CHK-10 | Doxygen and immutability obligations | header inspection; `Decode.ValueIsImmutableAndCopyable` | every public declaration carries `@brief`/ownership/lifetime/thread-safety/failure Doxygen (finalized by T037); the decoded value exposes no mutation surface and is copyable/movable |
| CHK-11 | Gate discovery and execution | `ctest -N`; `ctest` | `Total Tests ≥ 1`; the `t019`-labelled tests pass together with the existing suites; no existing test is modified |

## 4. Negative cases

Each `NEG-*` injects one controlled defect into a bounded, repository-owned, public-safe synthetic plan or a
mutation of a committed fixture and asserts the declared outcome, code, affected identifier, and the
**absence** of a decoded plan. These identifiers are T019-scoped.

### 4.1 Input and parse defects (`XCOM-DECODE-INPUT`, rejected)

| ID | Injected defect |
| --- | --- |
| `NEG-D01` | Truncated/malformed JSON |
| `NEG-D02` | A repeated object member name (duplicate-member rejection) |
| `NEG-D03` | Root is not a JSON object |
| `NEG-D21` | A non-finite (`1e999`) or integral-but-out-of-range (`1e30`, `-1e30`) numeric token |

### 4.2 Shape, vocabulary, and order defects (`XCOM-DECODE-SHAPE`, rejected)

| ID | Injected defect |
| --- | --- |
| `NEG-D04` | A required top-level member is missing |
| `NEG-D05` | An unknown top-level member is present |
| `NEG-D06` | An unknown member is present inside a nested object |
| `NEG-D07` | A closed vocabulary or const value is violated (`status`, `role`, `overflow`, `source`, `severity`) |
| `NEG-D08` | An identifier/version/digest/diagnostic pattern is violated, including the closed `$defs/digest` sub-schema of each embedded `provenance.graphDigest`/`provenance.resources[].sourceDigest` (`NEG-D08DigestPattern`) |
| `NEG-D17` | An identity-bearing collection is out of declared key order |
| `NEG-D18` | A duplicate collection key, an empty `activationOrder`/`capabilities`/`resources`, or a non-integer numeric member |

### 4.3 Version and digest defects (`XCOM-DECODE-VERSION`/`XCOM-DECODE-DIGEST`, rejected)

| ID | Injected defect |
| --- | --- |
| `NEG-D09` | `planVersion` is not `"1"` |
| `NEG-D10` | The digest algorithm is not `sha256`, or its value is not 64 lowercase hex |
| `NEG-D11` | A body member is changed but the recorded digest is unchanged (recomputed mismatch) |
| `NEG-D12` | The recorded digest is computed over a non-canonical (whitespace/reordered) serialization of the digested region |
| `NEG-D22` | The recorded digest is computed over the canonical body without the declared domain separator |

### 4.4 Capability, reference, and status defects (`XCOM-DECODE-CAPABILITY`/`-REFERENCE`/`-UNRESOLVED`, rejected)

| ID | Injected defect |
| --- | --- |
| `NEG-D13` | While `capability` is declared `resolved`, a route is declared but no provider is selected, or a provider's `requiredCapabilities` is not a subset of its `capabilities` |
| `NEG-D14` | While `schema`/`identity` is declared `resolved`, a `routes[]` `from`/`to`/`contractId` does not resolve to a declared endpoint/contract |
| `NEG-D15` | While `schema`/`identity` is declared `resolved`, an `observationPoints[].routeId` or an `activationOrder` entry does not resolve to a declared route/endpoint |
| `NEG-D16` | `status = "activatable"` while an `inputResolution` member is `unresolved` |

### 4.5 Bound defects (`XCOM-DECODE-BOUND`, failed, no plan)

| ID | Injected defect |
| --- | --- |
| `NEG-D19` | The document exceeds the byte, depth, or node bound |
| `NEG-D20` | A decoded entity count exceeds its declared cap |

### 4.6 Boundary and governance defects (failed)

| ID | Injected defect |
| --- | --- |
| `NEG-G01` | Candidate changed a path outside the §2.2 authorized set |
| `NEG-G02` | Candidate changed `src/xverse_xdl/**`, a T017/T018 artifact, `proto/**`, `xdl/**`, or `Doxyfile` |
| `NEG-G03` | A REF-002 target is recorded as promoted/implemented |
| `NEG-G04` | A source/test/evidence file contains a credential, private address, or absolute host path |
| `NEG-G05` | The T019 checkbox is marked complete in the plan stage, or an existing test/schema/contract is weakened |

## 5. Determinism checks

| ID | Check | Expected |
| --- | --- | --- |
| `DET-01` | `decode_activation_plan` run twice on the same bytes | identical outcome, code, and decoded value |
| `DET-02` | Reordered-but-equivalent document (member order, whitespace) | identical outcome, code, and recomputed digest |
| `DET-03` | Integral-number variants (`100` vs `100.0`) in a body | identical canonical bytes and digest |
| `DET-04` | `sha256_hex` over the domain separator + canonical body | deterministic across runs |

## 6. Bound checks

| ID | Bound | Expected |
| --- | --- | --- |
| `BND-01` | Plan bytes > `max_bytes` | `failed`, `XCOM-DECODE-BOUND`, no plan |
| `BND-02` | Depth > `max_depth` or nodes > `max_nodes` | `failed`, `XCOM-DECODE-BOUND`, no plan |
| `BND-03` | A decoded entity count > its cap | `failed`, `XCOM-DECODE-BOUND`, no plan |
| `BND-04` | No network / no subprocess / no filesystem write | source inspection finds no such call; the decoder is a pure function |
| `BND-05` | A `DecodeLimits` member < 1 | `failed`, `XCOM-DECODE-UNKNOWN`, no plan |

## 7. Exact planned tests (implementation stage)

| Test | Family | Asserts |
| --- | --- | --- |
| `tests/xcom/activation_plan/decoder_unit_tests.cpp::Decode.PublicApiAndConstants` | positive | CHK-01, CHK-10; `DecodeLimits` defaults |
| `…::Decode.Sha256KnownAnswers` | positive | CHK-04; DET-04 |
| `…::Decode.PositiveActivatableFixture` | positive | CHK-02, CHK-05 |
| `…::Decode.PositiveInspectableFixture` | positive | CHK-02, CHK-05 |
| `…::Decode.InspectableUnresolvedCapabilityIsAccepted` | positive | CHK-05; T019-STK-003 AC-3 (T018 producer shape) |
| `…::Decode.InspectableUnresolvedReferenceIsAccepted` | positive | CHK-05; unresolved schema/identity reference |
| `…::Decode.DigestAgreesWithT017Fixture` | positive | CHK-03 |
| `…::Decode.DecodedFieldsMatchFixture` | positive | CHK-03 |
| `…::Decode.CanonicalBodyIsMemberSortedWhitespaceFree` | canonicalization | CHK-08; DET-03 |
| `…::Decode.ReorderedDocumentSameDigestAndResult` | determinism | CHK-08; DET-01, DET-02 |
| `…::Decode.ValueIsImmutableAndCopyable` | value contract | CHK-10 |
| `…::Decode.LimitsValidationBounds` | bound | CHK-07; BND-05 |
| `…::Decode.SchemaDriftGuard` | drift | CHK-06; member/enum/pattern and `$defs/digest` table-vs-schema equality |
| `tests/xcom/activation_plan/decoder_negative_tests.cpp::DecodeNegative.NegD08DigestPattern` | negative | CHK-06, NEG-D08; embedded `graphDigest`/`sourceDigest` closed digest sub-schema (`XCOM-DECODE-SHAPE`, target `provenance`, no plan) |
| `tests/xcom/activation_plan/decoder_negative_tests.cpp::DecodeNegative.GeneratedAtDateTime` | negative/positive | R-04; invalid calendar, clock and offset values fail as `XCOM-DECODE-SHAPE`, while a real leap day with fractional seconds and offset decodes |
| `tests/xcom/activation_plan/decoder_negative_tests.cpp::DecodeNegative.NegD01…NegD22` | negative | NEG-D01..NEG-D22; CHK-04, CHK-05, CHK-06, CHK-07; BND-01..BND-03 |
| `ctest --test-dir build/fabro-t019 -L t019 --output-on-failure` | suite | the decoder tests pass |
| `ctest --test-dir build/fabro-t019 --output-on-failure` | gate | the full CTest suite passes; no existing test is modified |

The T017 Python test modules and fixtures are unchanged, so `python3 scripts/validate_xcom_plan.py --verify`
and the existing `pytest` suite remain valid (T019 changes no Python path).

## 8. Expected results and limitations

- All checks and negative cases are deterministic and offline; the decoder is a pure function that returns a
  `DecodeResult` and never reports a partial or unclassified result.
- The tests prove that the **decoder** enforces the T017 schema/digest contract for the bounded committed
  fixtures and the declared synthetic vectors. They do not prove endpoint/route/provider activation, runtime
  behaviour, throughput, timing, compatibility, or production readiness; those belong to later tasks. The
  decoder binds nothing and emits no communication item.
- **T020 extends coverage.** The ordering-equivalence, malformed-plan, drift, bound-matrix, and regression
  suites are T020's; T019 supplies the decoder unit/negative tests that prove its own units. T019 does not
  author, read, or reconcile T020's suites.
- **Environment A-1.** The gate's `cmake`/`ctest` run requires the admitted offline inputs (§2.4); the
  resolution rule is stated there and must be recorded in `implementation.md`.
- The plan-stage candidate changes only documentation; the deterministic gate cannot pass until the
  implementation stage supplies the decoder, its tests, the build wiring, and `implementation.md`, and marks
  the T019 checkbox.

## 9. Traceability of checks

| Requirement | Checks | Negative / determinism / bound cases |
| --- | --- | --- |
| T019-SR-001 | CHK-07 | NEG-D01..NEG-D03, NEG-D19, NEG-D21; BND-01, BND-02, BND-04 |
| T019-SR-002 | CHK-06, CHK-10 | NEG-D04..NEG-D08, NEG-D17, NEG-D18 |
| T019-SR-003 | CHK-02, CHK-03, CHK-04, CHK-08 | NEG-D09..NEG-D12, NEG-D22; DET-01..DET-04 |
| T019-SR-004 | CHK-05 | NEG-D13..NEG-D16 |
| T019-SR-005 | CHK-03, CHK-07, CHK-10 | NEG-D20; BND-03 |
| T019-SR-006 | CHK-04, CHK-06, CHK-08 | DET-01, DET-02; every `NEG-D*` |
| T019-SR-007 | CHK-01..CHK-11 | `ctest` gate |
| T019-SR-008 | CHK-09 | NEG-G01..NEG-G05 |

### 9.1 Accepted `XCOM-DU-011` planned-evidence tokens

The accepted T010 unit design lists `XCOM-DU-011` planned evidence as the capability-level tokens `CHK-06`,
`CHK-09`, `NEG-21`, `NEG-22`, `NEG-23`. Those tokens are T008/T010-scoped and are not decoder checks; they
are realised for `XCOM-DU-011` by the T019 check set as a whole, whose concrete decoder checks are
`CHK-01`..`CHK-11` and `NEG-D01`..`NEG-D22`/`NEG-G01`..`NEG-G05` above. T019 does not edit the T008/T010
work products; this note records the mapping so no accepted evidence identifier is left unaccounted for. The
`XCOM-SW-XDL-003`/`XCOM-SW-CORE-003` requirement links and the `XCOM-DU-XDL-BASELINE`/`XCOM-T-XDL` locators
are unchanged.

## 10. Evidence to retain with the candidate revision

- Gate command stdout/stderr and exit status, plus the `ctest -N` discovered-test count.
- The `cmake` configure/build log and the `ctest -L t019` log, bound to the exact candidate revision.
- The recomputed-versus-recorded digest values for both committed fixtures and the SHA-256 known answers.
- The exact admitted environment input identities (prefix/manifest/GTest prefix) and tool versions, and the
  A-1 resolution record if one was required.
- The candidate revision hash and `git diff --name-only`/`git diff --check` output.

Evidence must be bound to the exact candidate revision; missing, stale, or mismatched evidence cannot support
acceptance. This plan records no external-acceptance or Codex-review claim.
