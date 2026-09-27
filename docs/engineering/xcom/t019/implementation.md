# T019 Implementation — Bounded C++ Activation-Plan Decode

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T019 (capability 007, phase 4 XDL-derived activation plan) |
| Stage / role | implementation (repaired candidate) |
| Revision | 3 |
| Baseline revision | `199de0baa1f50e1d429527b6d6525a6e5d8cf7cf` |
| Candidate | working tree over `199de0baa1f50e1d429527b6d6525a6e5d8cf7cf` (rev 3 repairs rev 2) |
| Predecessor | T017 (`56506d2`), T018 (`199de0b`) reviewed terminal packages |
| Review input | [`internal-review.json`](internal-review.json) rev 3 finding `T019-IR-006` (rev 1 `T019-IR-001`..`T019-IR-005` closed in rev 2) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Classification | Public-safe engineering work product |
| Authority | `specs/007-xcom-core/tasks.md` T019; `specs/007-xcom-core/spec.md` FR-002/FR-006/FR-031/SC-002; `docs/engineering/xcom/t010/design-units.md` `XCOM-DU-011` |

### 1.1 Scope statement

This change implements only the bounded T019 C++ decoder and its unit/negative tests on top of the
accepted T017 schema/digest contract and the accepted T018 compiler output. It authors no Python
module, no T020 ordering/malformed/drift/bound/regression suite, no activation, endpoint/route/
provider binding, observation, stimulation, permit/session, journal, or gateway unit. It changes no
T017 or T018 artifact, no `xdl/` asset, no `proto/`, and no existing test or schema.

### 1.2 Maturity classification

**Implemented (bounded prototype).** The decoder is a pure function over caller-supplied plan bytes;
it performs no filesystem, network, or subprocess access and returns an immutable value or a
classified `rejected`/`failed` outcome. It does not activate, bind, emit, or observe anything and
makes no compatibility, runtime, timing, or production-readiness claim. `XCOM-DU-011` is implemented
for this candidate; acceptance, integration, and REF-002 promotion remain separate gates. External
Codex review is deferred until the backlog completes; this document records no external acceptance.

## 2. Changed artifacts and symbols

| Path | Change |
| --- | --- |
| `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp` | New public API in `xverse::xcom::plan`: `DecodeLimits`, `DecodeOutcome`, `DecodeError`, `PlanDigest`, `ResourceRef`, `Provenance`, `Contract`, `Endpoint`, `Route`, `Provider`, `Policies`, `ObservationPoint`, `Stimulation`, `ClockDomain`, `Diagnostic`, `InputResolution`, `ActivationPlan`, `DecodeResult`, `BytesResult`, `is_valid`, `sha256_hex`, `canonical_plan_body_bytes`, `recompute_plan_digest`, `decode_activation_plan`. The header exposes no third-party JSON type. |
| `src/xverse/xcom/src/activation_plan.cpp` | New implementation: bounded strict SAX parse (U-01), closed shape/vocabulary/order (U-02), T017 canonical serialization + in-tree FIPS 180-4 SHA-256 + independent version/digest verification (U-03), capability/cross-reference/status closure (U-04), bounded immutable model with entity caps (U-05), fixed-order deterministic outcome classification (U-06). Includes only the C++20 standard library and `nlohmann/json`. Rev 3 closes `T019-IR-006`: `require_digest` enforces the closed `$defs/digest` sub-schema (`algorithm == "sha256"`, `value =~ ^[0-9a-f]{64}$`) for every embedded digest (`provenance.graphDigest` and each `provenance.resources[].sourceDigest`); the top-level recorded `digest` is only structurally checked at the shape step so its form is classified `XCOM-DECODE-DIGEST` at the version/digest step (unchanged, `NEG-D10`). |
| `tests/xcom/activation_plan/decoder_unit_tests.cpp` | New positive, digest, canonicalization, determinism, value-contract, bound, and schema-drift tests (`Decode.*`), including `Decode.InspectableUnresolvedCapabilityIsAccepted` and `Decode.InspectableUnresolvedReferenceIsAccepted` (rev 2). Rev 3 extends `Decode.SchemaDriftGuard` to read `PLAN_SCHEMA.$defs/digest` (algorithm enum `{sha256}`, value pattern `^[0-9a-f]{64}$`, `additionalProperties: false`) and to bind a nested `graphDigest`/`sourceDigest` violation to `XCOM-DECODE-SHAPE`. |
| `tests/xcom/activation_plan/decoder_negative_tests.cpp` | New declared negative set `DecodeNegative.NegD01..NegD22` plus `BoundLimitsInvalid`; rev 2 added `NegD21`/`NegD22`, the resolved-over-claim cases in `NegD13`, and made `NegD12` exercise the declared non-canonical-serialization defect. Rev 3 adds `NegD08DigestPattern` (nested `provenance.graphDigest`/`resources[].sourceDigest` algorithm and value pattern violations → `XCOM-DECODE-SHAPE`, target `provenance`, no plan). |
| `src/xverse/xcom/CMakeLists.txt` | Shared build wiring: new `xverse_xcom_activation_plan` STATIC library (links only `nlohmann_json::nlohmann_json`) and two `t019`-labelled CTest targets; the GTest-prefix resolution accepts an explicit admitted cache value when the environment input is absent (§4 A-1). No existing target, warning policy, or test is modified. |
| `cmake/XComOfflineDependencies.cmake` | Shared dependency-admission path: reads `XVERSE_XCOM_TOOLCHAIN`/`XVERSE_XCOM_PACKAGE_MANIFEST` from the environment when present, otherwise from an explicit, previously admitted CMake cache value, exporting it to the preflight child, and (rev 2) prepends only the **named admitted prefix's** library directory to `LD_LIBRARY_PATH` when it is absent so the preflight's locked-version `protoc` probe loads the prefix's shared objects. The rev 1 unconditional `PATH` mutation is removed. The hash-verified preflight is unchanged and still runs (§4 A-1). |
| `specs/007-xcom-core/tasks.md` | Shared path: the T019 checkbox line is marked complete after the authorized work and all required local checks passed. |
| `docs/engineering/xcom/t019/implementation.md` | This record. |

Anchored, unchanged: `src/xverse_xdl/xcom_plan.py`, `tests/test_xcom_plan.py`,
`src/xverse/xcom/contracts/v1/activation-plan.schema.json`, `scripts/validate_xcom_plan.py`,
`xdl/profiles/xcom-v0.1.schema.json`, `specs/007-xcom-core/contracts/**`, `docs/engineering/xcom/t017/**`,
`docs/engineering/xcom/t018/**`, the committed fixtures under
`tests/xcom/activation_plan/fixtures/plan/valid/`, and every other `src/xverse/xcom/**` unit.

### 2.1 Cross-language contract

The plan schema and the digest rule are the only interface between T018 (Python) and this decoder
(C++). The decoder reproduces the canonicalization and the domain-separated SHA-256 independently
(in-tree, so it does not share the compiler's `hashlib`) and rejects a version/digest/capability
mismatch. No adapter, FFI, or second configuration language is introduced. The decoder implements no
authored-XDL parsing and adds no admitted dependency.

## 3. Requirement-to-code trace

| Requirement | Production symbols | Test cases | Result |
| --- | --- | --- | --- |
| T019-SR-001 | `BoundedSax`, `parse_bounded` | `NegD01..NegD03`, `NegD19`, `NegD21`, `BoundLimitsInvalid` | pass |
| T019-SR-002 | `validate_shape`, `check_object`, `require_enum`, `require_identifier`, `require_version`, `require_digest`, `require_digest_members`, `require_integer_range`, `check_key_order` | `NegD04..NegD08`, `NegD08DigestPattern`, `NegD17`, `NegD18`, `Decode.SchemaDriftGuard` | pass |
| T019-SR-003 | `canonical_bytes`, `sha256_bytes`, `sha256_hex`, `recompute_plan_digest`, `canonical_plan_body_bytes` | `Decode.Sha256KnownAnswers`, `Decode.DigestAgreesWithT017Fixture`, `Decode.CanonicalBodyIsMemberSortedWhitespaceFree`, `Decode.IntegralNumberVariantSharesCanonicalBytes`, `NegD09..NegD12`, `NegD22` | pass |
| T019-SR-004 | `validate_capability_and_references` | `NegD13..NegD16`, `Decode.PositiveInspectableFixture`, `Decode.InspectableUnresolvedCapabilityIsAccepted`, `Decode.InspectableUnresolvedReferenceIsAccepted` | pass |
| T019-SR-005 | `ActivationPlan` value type, `build_model` (entity caps) | `Decode.DecodedFieldsMatchFixture`, `Decode.ValueIsImmutableAndCopyable`, `NegD20` | pass |
| T019-SR-006 | `decode_activation_plan` fixed-order pipeline, `outcome_for_code` | `Decode.ReorderedDocumentSameDigestAndResult`, every `NegD*` | pass |
| T019-SR-007 | CMake targets `xverse_xcom_activation_plan`, `xverse_xcom_activation_plan_{unit,negative}_tests` | whole `t019` CTest suite | pass |
| T019-SR-008 | path/boundary/REF-002 preservation | §4 A-1/§5 boundary checks; no promoted REF-002 target | pass |

## 4. Environment resolution — A-1

The deterministic gate runs the exact `cmake`/`ctest` sequence in
[`verification-plan.md`](verification-plan.md) §2.1, inheriting the run process environment. That
environment does not carry the admitted offline inputs `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, or `XVERSE_XCOM_T025_TEST_TOOLCHAIN`; the unmodified preflight
failed with `Required explicit input XVERSE_XCOM_TOOLCHAIN is unset` before any T019 code was
exercised (observed and captured as the trigger, exactly as anticipated by
[`requirements.md`](requirements.md) §9 A-1 and [`architecture.md`](architecture.md) §7).

Resolution, as permitted by [`verification-plan.md`](verification-plan.md) §2.4 A-1:

1. `cmake/XComOfflineDependencies.cmake` reads the two authoritative inputs from the environment
   when present, and otherwise from an explicit, previously admitted CMake cache value, exporting it
   to the preflight child. The hash-verified offline preflight (`scripts/xcom_dependency_preflight.py
   --cmake-dependency-check`) is unchanged and still runs.
2. `src/xverse/xcom/CMakeLists.txt` applies the same explicit-cache fallback to the admitted GTest
   prefix `XVERSE_XCOM_T025_TEST_TOOLCHAIN`; no new mandatory input is added.
3. `cmake/XComOfflineDependencies.cmake` prepends the **named admitted prefix's** library directory
   (`<XVERSE_XCOM_TOOLCHAIN>/usr/lib/x86_64-linux-gnu`) to `LD_LIBRARY_PATH` **only when it is not
   already present**. The preflight's locked-version probe executes the prefix `protoc` by absolute
   path, and that binary resolves `libprotoc.so.23` from the prefix library directory; without this
   narrow, prefix-derived entry the probe fails to load. Rev 1 additionally mutated `PATH`; that
   mutation is removed in rev 2 because nothing in the admission or build path resolves a prefix
   tool by name, so it was unnecessary.

This narrow `LD_LIBRARY_PATH` authorization is recorded in the plan work products
([`requirements.md`](requirements.md) §2.4 and §9 A-1, [`verification-plan.md`](verification-plan.md)
§2.4 A-1, [`architecture.md`](architecture.md) §7), closes review finding `T019-IR-002`, and adds no
ambient path: the only added entry is derived from the explicit admitted prefix. The cache values were
seeded by one explicit configure carrying the three admitted inputs. Ambient discovery, network fetch,
a disabled preflight, a committed host-specific path, or any admission weakening is prohibited and none
was introduced. The admitted input identities and the seeded cache live outside Git (`build/` is
git-ignored); no absolute host path is recorded in source, tests, or this evidence.

## 5. Commands and observed results

Environment: the admitted offline inputs were provided to the seeding configure and are not committed
(§4). The gate sequence was then re-run with those variables removed from the process environment to
prove the A-1 fallback.

| ID | Command | Observed result |
| --- | --- | --- |
| C1 | `cmake -S . -B build/fabro-t019 -G Ninja -DCMAKE_BUILD_TYPE=Debug` (seeding configure with the three admitted inputs) | configure succeeded; dependency preflight admitted |
| C2 | `cmake --build build/fabro-t019 --parallel 4` | succeeded; 51 build steps; `libxverse_xcom_activation_plan.a` and both test executables produced |
| C3 | `ctest --test-dir build/fabro-t019 -N` | `Total Tests: 193` (rev 2) |
| C4 | `ctest --test-dir build/fabro-t019 -L t019 --output-on-failure --parallel 4` | `100% tests passed, 0 tests failed out of 37` (rev 2) |
| C5 | `ctest --test-dir build/fabro-t019 --output-on-failure --parallel 4` | `100% tests passed, 0 tests failed out of 193` (144 `t025`, 37 `t019`, remainder pre-existing) (rev 2) |
| C6 | `git diff --check 199de0baa1f50e1d429527b6d6525a6e5d8cf7cf --` | no output; exit 0 |
| C7 | `python3 scripts/xcom_dependency_preflight.py --cmake-dependency-check` (via C1) | admitted; hash-verified manifest unchanged |
| C8 | C1 configure with `env -u XVERSE_XCOM_TOOLCHAIN -u XVERSE_XCOM_PACKAGE_MANIFEST -u XVERSE_XCOM_T025_TEST_TOOLCHAIN -u LD_LIBRARY_PATH` | succeeded after the A-1 resolution in §4 |
| C9 | C2 build and C5 `ctest` with the same scrubbed environment | build succeeded; `100% tests passed out of 193` (rev 2) |
| C10 | `python3 -m pytest -q` | `129 passed, 24 subtests passed` (T017/T018 and pre-existing Python suites unchanged) |
| C11 | `python3 scripts/validate_xcom_plan.py --verify` / `--self-test` / `--check-human` | T017 validation, 53 self-test cases, and the human summary remain consistent; `profileKinds=5 planMembers=16 collections=6 digestVectors=2 exitClasses=6` |
| C12 | `python3 scripts/validate_xcom_task_ownership.py`; `python3 scripts/validate_xcom_requirements_traceability.py` | passed |
| C13 | `python3 scripts/validate_xcom_architecture_contracts.py`; `python3 scripts/validate_xcom_unit_design.py` | `PATH_INVALID` (12/13), identical at the baseline commit plus the two newly-present `XCOM-DU-011` implementation paths; see §6 L-2 |
| C14 | `git rev-parse 199de0baa1f50e1d429527b6d6525a6e5d8cf7cf` | prints the baseline SHA |
| C15 | rev 2 `cmake -S . -B build/fabro-t019 …` → `cmake --build …` → `ctest -N` | configure + build succeeded; `Total Tests: 193`; preflight admitted with the conditional prefix-derived `LD_LIBRARY_PATH` |
| C16 | rev 2 scrubbed-env fresh configure into `build/fabro-t019-scrub` (`env -u XVERSE_XCOM_TOOLCHAIN -u XVERSE_XCOM_PACKAGE_MANIFEST -u XVERSE_XCOM_T025_TEST_TOOLCHAIN -u LD_LIBRARY_PATH`, admitted inputs supplied as explicit cache values), then build and `ctest -L t019` | configure succeeded (preflight admitted), build succeeded, `100% tests passed out of 37`; closes `T019-IR-002` |
| C17 | independent T017-validator cross-check: load the inspectable fixture, drop `providers`, set `inputResolution.capability = "unresolved"`, `status = "inspectable"`, reseal with `scripts/validate_xcom_plan.py compute_digest`, then `validate_plan_structure(..., schema)` and `check_digest(...)` | structure findings `[]`, digest findings `[]`; the decoder now accepts the same shape (`Decode.InspectableUnresolvedCapabilityIsAccepted`); closes `T019-IR-001` |
| C18 | public-safety scan of `docs/engineering/xcom/t019/**` with the T017 `PUBLIC_SAFETY_PATTERNS` absolute-host-path regex | no match in the retained work products (rev 1's gate-path citation was removed; only this rev 2 review record is rewritten); closes `T019-IR-005` |
| C19 | `git diff --name-only 199de0baa1f50e1d429527b6d6525a6e5d8cf7cf --` | exactly the 13 declared T019 paths (unchanged from rev 1) |
| C20 | rev 3 `cmake --build build/fabro-t019 --parallel 4` after the `require_digest` closure | build succeeded; `libxverse_xcom_activation_plan.a` and both test executables relinked |
| C21 | rev 3 `ctest --test-dir build/fabro-t019 -N` | `Total Tests: 194` |
| C22 | rev 3 `ctest --test-dir build/fabro-t019 -L t019 --output-on-failure --parallel 4` | `100% tests passed, 0 tests failed out of 38`, including the new `DecodeNegative.NegD08DigestPattern` |
| C23 | rev 3 `ctest --test-dir build/fabro-t019 --output-on-failure --parallel 4` | `100% tests passed, 0 tests failed out of 194` |
| C24 | rev 3 `python3 -m pytest -q` | `129 passed, 24 subtests passed` (T017/T018 and pre-existing Python suites unchanged) |
| C25 | rev 3 read-only differential probe (compiled under `/tmp`, not retained): compare T017 `validate_plan_structure(plan, PLAN_SCHEMA)` against this decoder for `provenance.graphDigest.algorithm="md5"`, `graphDigest.value="abc"`/64-uppercase-hex, `resources[0].sourceDigest.algorithm="md5"`, and `resources[0].sourceDigest.value="zzz"`/63-hex | T017 `reject` and decoder `rejected`/`XCOM-DECODE-SHAPE`/`provenance`/no plan for all six mutations; the unmutated baseline is `accept`/`accepted` for both; closes `T019-IR-006` |
| C26 | rev 3 accepted-T018-producer compatibility: compile the 9 producer plans (positive + six unresolved families + no-deployment + removed-deployment-resource) with `src/xverse_xdl/xcom_plan.py` and decode each with the rev 3 decoder | all 9 decode `accepted` with an engaged non-activatable value where a resolution state is unresolved; no producer artifact is falsely rejected (CHK-05) |
| C27 | rev 3 adaptive differential fuzz (600 resealed structural mutations of the committed fixture): `{both_accept: 98, both_reject: 486, decoder_accept/T017_reject: 1, decoder_reject/T017_accept: 13}` | the single `decoder_accept/T017_reject` is only the declared `L-3` `generatedAt` `date-time` limitation; the 13 `decoder_reject/T017_accept` are the decoder's intended stricter `T019-SR-004` capability/reference closure that the structure+digest pair does not cover; no nested-digest laxness remains |

### 5.1 Case counts per suite

| Executable | Cases | Result |
| --- | --- | --- |
| `xverse_xcom_activation_plan_unit_tests` | `PublicApiAndConstants`, `Sha256KnownAnswers`, `PositiveActivatableFixture`, `PositiveInspectableFixture`, `InspectableUnresolvedCapabilityIsAccepted`, `InspectableUnresolvedReferenceIsAccepted`, `DigestAgreesWithT017Fixture`, `DecodedFieldsMatchFixture`, `CanonicalBodyIsMemberSortedWhitespaceFree`, `ReorderedDocumentSameDigestAndResult`, `IntegralNumberVariantSharesCanonicalBytes`, `ValueIsImmutableAndCopyable`, `LimitsValidationBounds`, `SchemaDriftGuard` | pass |
| `xverse_xcom_activation_plan_negative_tests` | `NegD01..NegD22`, `NegD08DigestPattern`, `BoundLimitsInvalid` | pass |

The declared `NEG-G01..NEG-G05` governance cases are external boundary checks performed by the
deterministic gate and the review stage (the decoder performs no `git` access); C6/C12/C13 and the
baseline binding provide that evidence.

### 5.2 Digest evidence

`recompute_plan_digest` equals the recorded `digest.value` for both committed fixtures:
`plan-activatable.json` → `7aaf63173194330d2debe9faaba2f5ed2125a611ce9f9accc124a9d215a5e4ce`,
`plan-inspectable.json` → `98c13f81e6945485e5ac74bbd0f44b271ca05b68c47a2ac5cc55c964c3030d3f`, identical to
the T017 validator. SHA-256 known answers for `""`, `"abc"`, and the three-byte vector
`00 01 02` hold.

### 5.3 Requested isolation of shape/parse defects from the digest

A body mutation normally changes the digest. For the shape, capability, reference, and status
negative cases the tests recompute and record the canonical digest (`seal`) so exactly one later
check is exercised; the digest cases deliberately do not, so the digest check is itself the isolated
defect: `NegD11` isolates a body change with an unchanged digest, `NegD12` isolates a digest computed
over a non-canonical (whitespace-bearing) serialization of the digested region, and `NegD22` isolates
a digest computed over the canonical body without the declared domain separator. `NegD21` isolates a
non-finite/out-of-range numeric token at parse. `NegD08DigestPattern` mutates a nested digest member
without resealing: the closed-shape pass precedes the version/digest step, so the schema-invalid
nested digest is rejected at the shape step (`XCOM-DECODE-SHAPE`, target `provenance`) before the
stale recorded digest is considered; a reseal is neither required nor possible because both public
canonicalization entry points validate shape first. This binds the declared pipeline order.

### 5.4 Repair-round closure of internal review rev 1 findings

| Finding | Closure in rev 2 | Evidence |
| --- | --- | --- |
| `T019-IR-001` (high) | `validate_capability_and_references` now enforces each closure rule only when the plan declares the governing `capability`/`schema`/`identity` state `resolved`; an `inspectable` plan that honestly records an unresolved closure (the accepted T018 `routes && !providers` shape, or an unresolved schema/identity reference) is accepted as non-activatable, while an over-claiming plan is rejected. | `Decode.InspectableUnresolvedCapabilityIsAccepted`, `Decode.InspectableUnresolvedReferenceIsAccepted`, the extended `NegD13`, and C17 |
| `T019-IR-002` (medium) | The unconditional `PATH`/`LD_LIBRARY_PATH` mutation is replaced by a conditional, prefix-derived `LD_LIBRARY_PATH` entry only (no `PATH` mutation), explicitly authorized in the plan work products. | §4, C15, C16 |
| `T019-IR-003` (low) | `NegD12` now computes the recorded digest over a non-canonical serialization of the digested region; the domain-separator case is retained as the distinct declared `NegD22`. | `NegD12`, `NegD22`; §5.3 |
| `T019-IR-004` (low) | `number_float` rejects an integral token outside the int64/uint64 range with `XCOM-DECODE-INPUT` (instead of retaining it as a double); the design already declared this behaviour. | `NegD21`; `detailed-design.md` §4/§12 |
| `T019-IR-005` (low) | The host-specific gate path is removed from every retained work product; the gate is referenced by the environment-neutral locator `automation/xcom_feature_gate.py` and the self-carved public-safety exemption is removed. | C18; `architecture.md` §7, `verification-plan.md` §2.1, `requirements.md` §2.4 |

### 5.5 Repair-round closure of internal review rev 3 finding `T019-IR-006`

| Finding | Closure in rev 3 | Evidence |
| --- | --- | --- |
| `T019-IR-006` (medium): nested digest members were not validated against the closed `$defs/digest` sub-schema | `require_digest` now enforces `algorithm == "sha256"` and `value =~ ^[0-9a-f]{64}$` after the structural `require_digest_members` check; `check_digest_shape` delegates to it for `provenance.graphDigest` and every `provenance.resources[].sourceDigest`, failing closed with `rejected`/`XCOM-DECODE-SHAPE`/target `provenance` and no engaged plan. The top-level recorded `digest` is structurally checked at the shape step and its algorithm/hex form remains classified at the version/digest step, so `NEG-D10` is unchanged. `Decode.SchemaDriftGuard` now reads the digest enum/pattern from `PLAN_SCHEMA.$defs/digest` and binds a nested violation to `XCOM-DECODE-SHAPE`; `NegD08DigestPattern` adds the negative cases (algorithm, 3-char value, 64-uppercase-hex, 63-hex). | C20..C25, C27; `NegD08DigestPattern`, `Decode.SchemaDriftGuard`; L-1 |

No accepted requirement, check, code, or test is weakened: the repair only makes the decoder stricter
(fail-closed) for inputs the accepted T017 validator already rejects, and every accepted T018 producer
artifact still decodes `accepted` (C26).

## 6. Limitations and deviations

- **L-1 (classification of deferred top-level value checks; scope clarified in rev 3).** To honour the
  declared per-family codes, the closed-shape pass validates the **top-level recorded** `digest` as a
  closed object with string members and `planVersion` as a string, and defers the top-level digest
  algorithm/hex value and the version const to the version/digest steps so a wrong top-level
  algorithm/value is `XCOM-DECODE-VERSION`/`XCOM-DECODE-DIGEST` rather than `XCOM-DECODE-SHAPE`,
  exactly as `verification-plan.md` §4.3 and `detailed-design.md` §12 require. Every **embedded**
  digest (`provenance.graphDigest` and each `provenance.resources[].sourceDigest`) is instead closed
  against the full `$defs/digest` sub-schema at the shape step (rev 3, `T019-IR-006`); that deferral
  never applied to them. No accepted sentence is changed; the schema's declared enum/const/pattern
  values are bound to the decoder by `Decode.SchemaDriftGuard`.
- **L-2 (pre-existing validator conditions).** `validate_xcom_architecture_contracts.py` and
  `validate_xcom_unit_design.py` already fail with `PATH_INVALID` at the baseline commit because
  T017/T018 artifacts are present in the tree; this candidate additionally makes the `XCOM-DU-011`
  planned paths present (the implementation). Neither validator is used by the T019 deterministic
  gate, and the condition is reported for the reviewer, not repaired (repairing it would edit the
  T009/T010 work products owned by other tasks).
- **L-3 (`generatedAt` format).** The decoder requires `provenance.generatedAt` to be a string but does
  not re-validate the RFC 3339 `date-time` format; the accepted T017 validator applies that
  format check. Recorded as a bounded-scope limitation, not a claim.
- **L-4 (no clang-format/clang-tidy run).** The repository defines no `.clang-format`, and no
  `clang-format` binary is present in the admitted prefix or host; formatting follows the adjacent
  X-COM files and C6 (`git diff --check`) is clean. This is an environment limitation, not a claim of
  tool-enforced formatting.
- **L-5 (no runtime/activation proof).** The tests prove the decoder's bounded, fail-closed behaviour
  for the committed fixtures and the declared synthetic vectors. They do not prove activation,
  binding, transport, runtime, throughput, timing, compatibility, or production readiness; those
  belong to later tasks. T020 owns the ordering-equivalence/malformed-plan/drift/bound/regression
  suites.

## 7. Trace to requirement dispositions

The implementation realises the T019 slice for FR-002 (decode-time derivation from the digest-bound
plan), FR-006 (fail-before-traffic capability/reference closure at decode time), FR-031 (independent
version/digest verification), SC-002 (equivalent normalized plan bodies share one canonical
bytes/digest and one result), and FR-007 (bounded policy decode); the capability-level dispositions in
[`requirements.md`](requirements.md) §7 remain **partial** for these slices and are not promoted. FR-025/
FR-027 diagnostics and FR-030 traceability remain **partial**. `ref002.disposition = "unchanged"` with
an empty promoted set; no REF-002 target and no `implemented`/`partial`/`allocated`/`deferred` SADS
disposition is changed.

## 8. Non-claims

- No external (Codex) review, protected verification, independent integration, source compatibility,
  human acceptance, or production readiness is claimed.
- No communication item, transport, gateway, network peer, payload content, legacy repository, or
  production workload was touched; the decoder binds nothing and emits nothing.
- The T019 checkbox is marked only after all required local checks passed; this is not an acceptance
  or integration claim.
