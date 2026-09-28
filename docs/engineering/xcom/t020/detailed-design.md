# T020 Detailed Design — Test Suites for the XDL-Derived Activation-Plan Chain

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T020 |
| Stage / role | plan → detailed design |
| Revision | 2 (rev 2 repairs internal-review findings T020-IR-001 and T020-IR-002; no identifier changes) |
| Baseline revision | `1e289bfe6234553df94eb25065371f7d423fad88` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Shape authority | `src/xverse/xcom/contracts/v1/activation-plan.schema.json` (T017) and `specs/007-xcom-core/contracts/communication-plan.md` |
| Digest-rule authority | `specs/007-xcom-core/contracts/xdl-profile.md` "Activation-plan v1 digest and provenance"; `docs/engineering/xcom/t017/detailed-design.md` §5; `scripts/validate_xcom_plan.py` (`canonical_bytes`, `compute_digest`, `check_digest`) |
| Consumed decoder API | `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp` (T019; anchored, unchanged) |
| Consumed compiler | `src/xverse_xdl/xcom_plan.py` (T018; anchored, unchanged) |
| Governing ADRs | ADR-0016, ADR-0018, ADR-0020 |
| Language / tooling | C++20 GoogleTest/gmock (admitted offline GTest prefix) + Python 3.11+ `pytest`; C++ includes only the standard library, the admitted `nlohmann/json` 3.10.5 header, and `xverse/xcom/activation_plan.hpp` |

This design is written **before** implementation. The implementation must realise every named identifier and
case. The identifiers below are fixed by this document.

## 2. Fixed identifiers, constants, and golden values

### 2.1 Artifact identifiers

| Identifier | Path |
| --- | --- |
| `T020_TEST_SUPPORT` | `tests/xcom/activation_plan/t020_support.hpp` |
| `T020_TESTS_ORDERING` | `tests/xcom/activation_plan/t020_ordering_equivalence_tests.cpp` |
| `T020_TESTS_MALFORMED` | `tests/xcom/activation_plan/t020_malformed_plan_tests.cpp` |
| `T020_TESTS_DRIFT` | `tests/xcom/activation_plan/t020_drift_tests.cpp` |
| `T020_TESTS_BOUND` | `tests/xcom/activation_plan/t020_bound_matrix_tests.cpp` |
| `T020_TESTS_REGRESSION` | `tests/xcom/activation_plan/t020_regression_tests.cpp` |
| `T020_TESTS_PYTHON` | `tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py` |
| `T020_IMPL_RECORD` | `docs/engineering/xcom/t020/implementation.md` |
| `BUILD_WIRING` | `src/xverse/xcom/CMakeLists.txt` (shared) |
| `PLAN_SCHEMA` | `src/xverse/xcom/contracts/v1/activation-plan.schema.json` (anchored, unchanged) |
| `PROFILE_SCHEMA` | `xdl/profiles/xcom-v0.1.schema.json` (anchored, unchanged) |
| `PLAN_FIXTURES` | `tests/xcom/activation_plan/fixtures/plan/valid/` (anchored, read-only) |
| `PLAN_DOCS` | `docs/engineering/xcom/t020/` |

### 2.2 Test-suite identifiers and CTest targets

| GoogleTest suite | CTest target | Label | Source |
| --- | --- | --- | --- |
| `T20OrderingEquivalence` | `xverse_xcom_activation_plan_t020_ordering_equivalence_tests` | `t020-ordering-equivalence` | `T020_TESTS_ORDERING` |
| `T20MalformedPlan` | `xverse_xcom_activation_plan_t020_malformed_plan_tests` | `t020-malformed-plan` | `T020_TESTS_MALFORMED` |
| `T20Drift` | `xverse_xcom_activation_plan_t020_drift_tests` | `t020-drift` | `T020_TESTS_DRIFT` |
| `T20BoundMatrix` | `xverse_xcom_activation_plan_t020_bound_matrix_tests` | `t020-bound-matrix` | `T020_TESTS_BOUND` |
| `T20Regression` | `xverse_xcom_activation_plan_t020_regression_tests` | `t020-regression` | `T020_TESTS_REGRESSION` |

Each target also defines the compile-time paths `XCOM_ACTIVATION_PLAN_FIXTURE_DIR`,
`XCOM_ACTIVATION_PLAN_SCHEMA_PATH`, and (for the drift target) `XCOM_T020_PROFILE_SCHEMA_PATH`, and links
`xverse::xcom_activation_plan` (`BUILD_WIRING` line 124–138, unchanged), `GTest::gtest_main`, `GTest::gmock`,
and `Threads::Threads`.

Each target registers its discovered tests under the single CTest label `t020-<kind>` (rev 2). A semicolon
label list (`"t020;<kind>"`) is split by `gtest_discover_tests` in the admitted CMake 3.22 toolchain, which
registers only its first element, so the hyphenated single label is used; CTest `-L` is a regular-expression
match, so both `ctest -L t020` and `ctest -L <kind>` select the intended tests. The T019/T025 target wiring is
unchanged (including the pre-existing `xcom_observation_disabled_benchmark` registration; rev 4 reverted the
out-of-scope rev-3 property change, see `implementation.md` §10).

### 2.3 Constants and golden values (pinned by the regression/drift suites)

| Name | Value | Source |
| --- | --- | --- |
| `kPlanVersion` | `"1"` | `PLAN_SCHEMA.properties.planVersion.const` |
| `kDigestAlgorithm` | `"sha256"` | `PLAN_SCHEMA.$defs.digest.properties.algorithm.enum[0]` |
| `kPlanDomainSeparator` | `"xverse.xcom.activation-plan.v1"` + `'\0'` | `contracts/xdl-profile.md`; `scripts/validate_xcom_plan.py` `DOMAIN_SEPARATOR` |
| `kPlanTarget` | `"xcom-plan"` | T019 `activation_plan.hpp` fixed diagnostic target |
| `kDigestHexPattern` | `^[0-9a-f]{64}$` | `PLAN_SCHEMA.$defs.digest.properties.value.pattern` |
| `kRequiredMemberCount` | `16` | `PLAN_SCHEMA.required` |
| `kProfileFormCount` | `5` | `PROFILE_SCHEMA` (interface-policy, flow-policy, network-provider, observation-policy, validation-policy) |
| `kFixtureActivatableFileSha256` | `8f32193b5fe9ad3546cbc291eaa276ffae6e41297fa8d990e26997f5c8bc0790` | committed fixture byte identity |
| `kFixtureActivatableBodySha256` | `03dde94859fde2503ee905930b0a75a653898a21b30fd508b4bb0322930762e5` | `sha256(canonical_body_bytes)` |
| `kFixtureActivatableDigest` | `7aaf63173194330d2debe9faaba2f5ed2125a611ce9f9accc124a9d215a5e4ce` | committed fixture `digest.value` |
| `kFixtureInspectableFileSha256` | `48be9d195ed0f324ad497437faeef6f34f6cc6a083989bf7ce3a800e4ec84cd1` | committed fixture byte identity |
| `kFixtureInspectableBodySha256` | `a97a0a6ae524373b789db5cb3b195233d7e46a6536435160c8a6c96b6836ba99` | `sha256(canonical_body_bytes)` |
| `kFixtureInspectableDigest` | `98c13f81e6945485e5ac74bbd0f44b271ca05b68c47a2ac5cc55c964c3030d3f` | committed fixture `digest.value` |

The fixture field-count goldens are `contracts=1`, `endpoints=2`, `routes=1`, `providers=1`,
`observationPoints=1`, `clockDomains=1`, `activationOrder=2`, `diagnostics=1`, `provenance.resources=2`.

**Golden-value rule.** The implementation stage captures each golden literal directly from the accepted,
unchanged artifacts at the candidate revision (via `scripts/validate_xcom_plan.py` and the committed fixture
bytes) and records the capture command and value in `T020_IMPL_RECORD`. A mismatch at test time fails the
suite; a golden may never be updated to match a drifted artifact.

### 2.4 Outcome/code vocabulary (closed, consumed)

`DecodeOutcome` ∈ {`accepted`, `rejected`, `failed`}. `DecodeCode` ∈ {`XCOM-DECODE-INPUT`,
`XCOM-DECODE-SHAPE`, `XCOM-DECODE-VERSION`, `XCOM-DECODE-DIGEST`, `XCOM-DECODE-CAPABILITY`,
`XCOM-DECODE-REFERENCE`, `XCOM-DECODE-UNRESOLVED`, `XCOM-DECODE-BOUND`, `XCOM-DECODE-UNKNOWN`}.
`BOUND`/`UNKNOWN` are `failed`; every other code is `rejected`; an absent code is `accepted`.

### 2.5 Case-identifier vocabulary (T020-scoped)

`T20-ORD-01`..`T20-ORD-08` (ordering-equivalence), `T20-MAL-01`..`T20-MAL-14` (malformed-plan),
`T20-DRF-01`..`T20-DRF-09` (drift), `T20-BND-01`..`T20-BND-11` (bound matrix),
`T20-REG-01`..`T20-REG-10` (regression), `T20-DET-01`..`T20-DET-04` (determinism),
`T20-G01`..`T20-G05` (boundary/governance). These identifiers are T020-scoped and are distinct from the T019
`NEG-D*`/`NEG-G*` and `BND-*` identifiers; T020 neither reuses nor edits them.

### 2.6 Declared tables the drift suite asserts (from `PLAN_SCHEMA`)

- **Required top-level members (16):** `planVersion`, `digest`, `generator`, `provenance`, `contracts`,
  `endpoints`, `routes`, `providers`, `policies`, `observationPoints`, `stimulation`, `clockDomains`,
  `activationOrder`, `diagnostics`, `status`, `inputResolution`.
- **Closed enums:** `status` ∈ {`inspectable`, `activatable`}; endpoint `role` ∈ {`initiator`, `responder`,
  `observer`, `tool`}; `ordering` ∈ {`fifo`, `priority`, `unordered`}; `reliability` ∈ {`at-most-once`,
  `at-least-once`, `exactly-once`, `best-effort`}; `overflow` ∈ {`drop-oldest`, `drop-newest`, `coalesce`,
  `lossless-backpressure`, `reject`, `fail-closed`}; `backpressure` ∈ {`fail-closed`, `reject`,
  `lossless-backpressure`}; `payloadAccess` ∈ {`metadata-only`, `allow-listed`}; `validityEffect` ∈ {`none`,
  `degrade-on-loss`, `invalidate-on-loss`}; `clockDomain.source` ∈ {`monotonic`, `local-validation-clock`,
  `unmapped`}; `severity` ∈ {`error`, `warning`, `info`}; each `inputResolution` member ∈ {`resolved`,
  `unresolved`}; `resourceRef.kind` ∈ {`Component`, `Deployment`, `Scenario`}; `digest.algorithm` ∈ {`sha256`}.
- **Patterns:** identifier `^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$`; version `^[0-9]+\.[0-9]+(?:\.[0-9]+)?$`;
  digest value `^[0-9a-f]{64}$` (every embedded digest); generator task `^T[0-9]{3}$`; diagnostic code
  `^XCOM-[A-Z0-9-]{3,64}$`; `apiVersion` const `xverse.io/xdl/v1alpha1`.
- **Numeric ranges:** `deadlineMs` 0..600000; `retry` 0..64; `queueDepth` 1..65536 (all integers).
- **Collection keys and minimums:** `contracts`→`contractId`, `endpoints`→`endpointId`, `routes`→`routeId`,
  `providers`→`providerId`, `observationPoints`→`tapId`, `clockDomains`→`clockDomainId`,
  `provenance.resources`→(`apiVersion`,`kind`,`namespace`,`name`,`version?`); each ordered ascending by its
  declared key with unique keys; `providers[].capabilities` `minItems: 1`; `provenance.resources`
  `minItems: 1`; `activationOrder` `minItems: 1`, duplicate-free; top-level and every object
  `additionalProperties: false`.

## 3. Shared bounded test support (`T020_TEST_SUPPORT`)

A header-only, `inline`-only helper used by all five C++ suites. It adds no library and no target.

| Helper | Signature / behaviour |
| --- | --- |
| `t20::read_text(path)` | Read a bounded text file (binary); returns the bytes. |
| `t20::plan_fixture(name)` | Read `XCOM_ACTIVATION_PLAN_FIXTURE_DIR "/plan/valid/" name` read-only. |
| `t20::activatable()` / `t20::inspectable()` | `json::parse` of the two committed fixtures. |
| `t20::seal(json plan)` | Recompute the canonical digest with `recompute_plan_digest` and write `digest.value`; returns `plan.dump()`. Used to isolate a mutation's intended defect. |
| `t20::canonical_body(text)` | `canonical_plan_body_bytes(text)`, asserting acceptance. |
| `t20::expect_error(result, code, target)` | Assert `!plan`, outcome matches the code's `failed`/`rejected` mapping, and code/target match (empty target means "any non-empty identifier"). |
| `t20::expect_accepted(result)` | Assert `accepted` with an engaged plan and empty code. |
| `t20::reorder(value)` / `t20::with_whitespace(text)` | Deterministic member-order/whitespace permutations of a JSON value. |
| `t20::two_item_collection(plan, member, key)` | Build a valid two-item collection with unique keys in declared order to exercise an entity cap at small size. |

The helper performs no network, subprocess, clock, or filesystem **write** access; it holds no global mutable
state.

## 4. Ordering-equivalence suite (`T020_TESTS_ORDERING`, suite `T20OrderingEquivalence`)

| Test | Case | Asserts |
| --- | --- | --- |
| `EquivalentSyntheticPlansShareCanonicalBytes` | `T20-ORD-01` | Two synthetic bodies that differ only in member order/whitespace yield one canonical byte string; `canonical_plan_body_bytes` outputs are byte-equal. |
| `ReorderedFixtureSharesCanonicalBytesAndDigest` | `T20-ORD-02` | A `dump(3)` re-serialization of a committed fixture yields the same canonical bytes and recomputed digest as the original. |
| `DeclaredCollectionOrderingIsEnforced` | `T20-ORD-03` | Each identity-bearing collection in the fixture is in declared key order; a reversed collection is rejected `XCOM-DECODE-SHAPE` with the collection target. |
| `ActivationOrderIsDuplicateFree` | `T20-ORD-04` | A duplicated or empty `activationOrder` is rejected `XCOM-DECODE-SHAPE` at the `activationOrder` target; a reordered-but-complete, reference-closed sequence is accepted and preserved verbatim — `activationOrder` is an explicit sequence, not a sorted collection, so no ascending rule applies (rev 2; T020-IR-001 closure). |
| `DecodedDiagnosticsAreOrderedDeterministically` | `T20-ORD-05` | The decoded `diagnostics` sequence equals the fixture's declared order and is identical across equivalent input representations. |
| `ReorderedDocumentSameOutcomeAndDecodedValue` | `T20-ORD-06` | `decode_activation_plan` on the original and the reordered document returns identical outcome, code, digest (`value`, `algorithm`), and the compared decoded fields `plan_version`, `status`, `activation_order`, the `endpoints`/`provenance.resources` counts, `input_resolution.time`, and `policies.deadline_ms`; a repeated decode is also identical. Whole-value identity remains proven by the canonical-byte/digest equality of `T20-ORD-01`/`T20-ORD-02` and the field goldens of `T20-REG-01`, not by this spot-check (rev 2; T020-IR-002 closure) (`T20-DET-01`, `T20-DET-02`). |
| `IntegralNumberVariantSharesCanonicalBody` | `T20-ORD-07` | Replacing an integral token (`100`) with `100.0` yields the same canonical body and digest and still decodes (`T20-DET-03`). |
| `RepeatedDecodeAndWhitespaceVariantsAreIdentical` | `T20-ORD-08` | Repeated decodes and whitespace variants yield identical outcome/code/digest (`T20-DET-01`, `T20-DET-04`). |

The Python module adds the cross-language leg: `compiler.compile_plan_text(graph)` and
`validator.canonical_bytes(plan)` agree byte-for-byte for a bounded synthetic normalized graph, and the
reordered-equivalent graph yields byte-identical plans/digests (`T20-DET-02`, `SC-002`).

## 5. Malformed-plan suite (`T020_TESTS_MALFORMED`, suite `T20MalformedPlan`)

| Test | Case | Injected defect → declared outcome/code |
| --- | --- | --- |
| `TruncatedDocumentsAreRejected` | `T20-MAL-01` | Truncate the fixture body at several byte offsets → `rejected` `XCOM-DECODE-INPUT`, target `xcom-plan`. |
| `UnbalancedDelimitersAreRejected` | `T20-MAL-02` | Drop/duplicate a closing brace or bracket → `rejected` `XCOM-DECODE-INPUT`. |
| `TrailingContentIsRejected` | `T20-MAL-03` | Append `{}`, `trailing`, or a second document → `rejected` `XCOM-DECODE-INPUT`. |
| `DuplicateMembersAtEachLevelAreRejected` | `T20-MAL-04` | Repeat a member at the top level, in `provenance`, in `policies`, and in an `endpoints[]` object → `rejected` `XCOM-DECODE-INPUT`. |
| `NonObjectRootsAreRejected` | `T20-MAL-05` | `[]`, `42`, `true`, `null`, `"plan"` roots → `rejected` `XCOM-DECODE-INPUT`. |
| `WrongJsonTypesAreRejected` | `T20-MAL-06` | A collection given as an object or scalars given as arrays → `rejected` `XCOM-DECODE-SHAPE`. |
| `NullWhereObjectOrArrayRequiredIsRejected` | `T20-MAL-07` | `null` for `policies`, `provenance`, `contracts`, `inputResolution` → `rejected` `XCOM-DECODE-SHAPE`. |
| `MissingRequiredMembersAreRejected` | `T20-MAL-08` | Each of the 16 required members dropped in turn → `rejected` `XCOM-DECODE-SHAPE`, target `xcom-plan`. |
| `UnknownNestedMembersAreRejected` | `T20-MAL-09` | One unknown member in each nested object (`provenance`, `policies`, `generator`, `contracts[]`, `endpoints[]`, `routes[]`, `providers[]`, `observationPoints[]`, `stimulation`, `clockDomains[]`, `inputResolution`) → `rejected` `XCOM-DECODE-SHAPE` with that object's target. |
| `InvalidUtf8IsRejected` | `T20-MAL-10` | A lone `0xFF` byte inside a string value → `rejected` `XCOM-DECODE-INPUT`. |
| `EmptyAndWhitespaceOnlyDocumentsAreRejected` | `T20-MAL-11` | Empty string and whitespace-only document → `rejected` `XCOM-DECODE-INPUT`. |
| `OverNestedDocumentsFailClosed` | `T20-MAL-12` | A nesting depth above the default `max_depth` → `failed` `XCOM-DECODE-BOUND`. |
| `MalformedPlansNeverReturnADecodedValue` | `T20-MAL-13` | Every malformed case above returns no plan and never `accepted` (aggregate guard). |
| `MalformedMutationsRemainDistinctFromT019Cases` | `T20-MAL-14` | The T020 malformed vectors are a distinct set from the T019 `NEG-D*` inputs (source-inspection guard over the T019 test file, read-only). |

Malformed-plan defects that the T019 `NEG-D*` set already exercises at unit level (e.g. a single repeated
member) are re-exercised here only inside the broader matrix; no T019 file is edited.

## 6. Drift suite (`T020_TESTS_DRIFT`, suite `T20Drift`)

| Test | Case | Asserts |
| --- | --- | --- |
| `RequiredMemberTableMatchesSchema` | `T20-DRF-01` | The sorted 16-member set equals `PLAN_SCHEMA.required`; `additionalProperties == false`; each object in `$defs` is closed. |
| `ClosedEnumTablesMatchSchema` | `T20-DRF-02` | For every enum in §2.6 the decoder-observed accepted/rejected vocabulary equals the schema enum (accepts each member, rejects one out-of-vocabulary token). |
| `PatternTablesMatchSchema` | `T20-DRF-03` | The identifier, version, digest, generator-task, and diagnostic-code patterns equal the schema's, evidenced by an accepted conforming value and a rejected non-conforming value per pattern. |
| `CollectionKeysAndMinimumsMatchSchema` | `T20-DRF-04` | The declared ordering keys, `uniqueItems`, `minItems` (`providers[].capabilities`=1, `provenance.resources`=1, `activationOrder`=1), and the top-level collection set equal the schema. |
| `NumericRangesMatchSchema` | `T20-DRF-05` | `deadlineMs` 0..600000, `retry` 0..64, `queueDepth` 1..65536 equal the schema bounds; an out-of-range value and a non-integer value are rejected `XCOM-DECODE-SHAPE`. |
| `EmbeddedDigestSubSchemaMatchesDecoder` | `T20-DRF-06` | `$defs/digest` (`algorithm ∈ {sha256}`, value `^[0-9a-f]{64}$`, closed) equals the decoder's embedded-digest rule for `provenance.graphDigest` and each `provenance.resources[].sourceDigest`; a violation is rejected `XCOM-DECODE-SHAPE`. |
| `PlanVersionConstMatchesDecoder` | `T20-DRF-07` | `PLAN_SCHEMA.properties.planVersion.const == "1"`; `planVersion != "1"` is rejected `XCOM-DECODE-VERSION`. |
| `DomainSeparatorAndGoldenDigestsAreStable` | `T20-DRF-08` | The domain separator matches the contract; each committed fixture's recorded digest equals its golden `kFixture*Digest` and the decoder's recomputation; the canonical body hash equals its golden `kFixture*BodySha256`. |
| `ProfileFormVocabularyIsTheAcceptedFiveForms` | `T20-DRF-09` | `PROFILE_SCHEMA` declares exactly the accepted five form kinds (`interface-policy`, `flow-policy`, `network-provider`, `observation-policy`, `validation-policy`) and no sixth; the plan schema's referenced Profile extension namespace is unchanged. |

## 7. Bound-matrix suite (`T020_TESTS_BOUND`, suite `T20BoundMatrix`)

| Test | Case | Bound exercised → expected |
| --- | --- | --- |
| `ByteBoundAtAndOver` | `T20-BND-01` | `max_bytes` set to the fixture length accepts; one byte less fails `XCOM-DECODE-BOUND`, no plan. |
| `DepthBoundAtAndOver` | `T20-BND-02` | A document exactly at `max_depth` accepts; one level deeper fails `XCOM-DECODE-BOUND`. |
| `NodeBoundAtAndOver` | `T20-BND-03` | A document exactly at `max_nodes` accepts; one node more fails `XCOM-DECODE-BOUND`. |
| `StringLengthOverIsRejected` | `T20-BND-04` | A decoded string one byte over `max_string_length` is `rejected` `XCOM-DECODE-SHAPE` with no plan (per the T019 unit contract). |
| `ContractCapAtAndOver` | `T20-BND-05` | A valid two-contract plan with `max_contracts = 2` accepts; `max_contracts = 1` fails `XCOM-DECODE-BOUND`. |
| `EndpointCapAtAndOver` | `T20-BND-06` | A valid two-endpoint plan with `max_endpoints = 2` accepts; `= 1` fails `XCOM-DECODE-BOUND`. |
| `RouteCapAtAndOver` | `T20-BND-07` | A valid two-route plan with `max_routes = 2` accepts; `= 1` fails `XCOM-DECODE-BOUND`. |
| `ProviderCapAtAndOver` | `T20-BND-08` | A valid two-provider plan with `max_providers = 2` accepts; `= 1` fails `XCOM-DECODE-BOUND`. |
| `ObservationPointAndClockDomainCapsAtAndOver` | `T20-BND-09` | `max_observation_points` and `max_clock_domains` each accept at the plan's count and fail one below. |
| `DiagnosticActivationOrderAndResourceCapsAtAndOver` | `T20-BND-10` | `max_diagnostics`, `max_activation_order`, and `max_provenance_resources` each accept at the plan's count and fail one below. |
| `EveryLimitBelowOneFailsClosed` | `T20-BND-11` | Each of the 13 `DecodeLimits` members set to `0`, with the others valid, is `failed` `XCOM-DECODE-UNKNOWN` and returns no plan. |

Every cap case builds its input at small size (a valid two-item collection with distinct keys in declared
order) so the suite allocates a bounded document; `T20-BND-01` additionally exercises the true 5 MiB default
by lowering the limit against the fixture rather than allocating an over-limit document. No case fixes a
production value.

## 8. Regression suite (`T020_TESTS_REGRESSION`, suite `T20Regression`)

| Test | Case | Asserts |
| --- | --- | --- |
| `ActivatableFixtureDecodesWithPinnedFields` | `T20-REG-01` | The activatable fixture decodes `accepted`; `plan_version`, `status`, `input_resolution.time`, and every decoded member equal the pinned fixture values and the field-count goldens. |
| `InspectableFixtureDecodesWithPinnedFields` | `T20-REG-02` | The inspectable fixture decodes `accepted` with `status == "inspectable"` and its pinned unresolved member. |
| `GoldenRecordedAndRecomputedDigests` | `T20-REG-03` | Each fixture's recorded digest equals `kFixture*Digest` and `recompute_plan_digest` equals it. |
| `Sha256KnownAnswersUnchanged` | `T20-REG-04` | The FIPS 180-4 known answers for the empty, `abc`, and `0x00 0x01 0x02` inputs are unchanged. |
| `DomainSeparatorRegression` | `T20-REG-05` | A digest computed with the domain separator matches; without it, or over a non-canonical body, it mismatches (`XCOM-DECODE-DIGEST`). |
| `RequiredMemberSetAndClosedSchemaUnchanged` | `T20-REG-06` | The 16 required members, `additionalProperties == false`, and the closed `$defs` set are unchanged. |
| `FixtureBytesAreUnchanged` | `T20-REG-07` | Each committed fixture's file SHA-256 equals `kFixture*FileSha256`, proving the anchored T017 fixtures were not mutated. |
| `GoldenCanonicalBodyHashIsStable` | `T20-REG-08` | `sha256(canonical_plan_body_bytes(fixture))` equals `kFixture*BodySha256`. |
| `DecodeLimitsDefaultsUnchanged` | `T20-REG-09` | All 13 `DecodeLimits` defaults equal their declared values and `is_valid` is true. |
| `DecodeCodeVocabularyIsClosed` | `T20-REG-10` | A representative defect per code produces exactly the nine declared codes, and `BOUND`/`UNKNOWN` map to `failed` while the rest map to `rejected`. |

## 9. Python cross-language suite (`T020_TESTS_PYTHON`)

A pure `pytest` module under `tests/xcom/activation_plan/`. It imports `xverse_xdl.xcom_plan` and loads the
T017 validator from its repository path exactly as `tests/test_xcom_plan.py` does (read-only), and it reads the
committed fixtures read-only. It performs no network, subprocess, or file write; paths derive from `__file__`.

| Function | Case | Asserts |
| --- | --- | --- |
| `test_t020_compiler_and_validator_agree_on_canonical_bytes` | `T20-ORD-01` | For a bounded synthetic normalized graph, `compiler.canonical_plan_bytes(plan)` equals `validator.canonical_bytes(plan)` byte-for-byte. |
| `test_t020_equivalent_graphs_produce_byte_identical_plans` | `T20-ORD-02`, `T20-DET-02` | Two equivalent (reordered) synthetic graphs compile to byte-identical plans and equal digests. |
| `test_t020_diagnostic_ordering_is_deterministic` | `T20-ORD-05` | The compiled diagnostic ordering is identical across equivalent inputs. |
| `test_t020_committed_fixtures_match_reference_digest` | `T20-REG-03`, `T20-REG-07` | Each committed fixture's recorded digest equals the validator's recomputation and the golden value; the fixture bytes hash to the golden file SHA-256. |
| `test_t020_malformed_plan_matrix_is_rejected` | `T20-MAL-06`, `T20-MAL-08` | Declared plan-schema/digest mutations are flagged by the validator's `validate_plan_structure`/`check_digest`. |
| `test_t020_module_is_offline_and_pure` | `T20-G03` | The module imports only the standard library and the repository's own modules; it contains no `subprocess`/`socket`/`urllib`/`open`-write and no absolute host path. |
| `test_t020_verification_plan_lists_every_implemented_test` | `T20-G05` | The plan's Python test table and this module agree exactly, and the plan's C++ test table and every `TEST(...)` name in the five C++ sources agree exactly. |

The synthetic normalized graph follows the T018 public API (`compiler.API_VERSION`, `PROFILE_NAMESPACE`, the
five Profile payload forms) and is bounded and public-safe; no T017/T018 source or test is edited.

## 10. Build wiring design (`BUILD_WIRING`, shared)

A single `foreach(kind IN ITEMS ordering_equivalence malformed_plan drift bound_matrix regression)` block,
placed after the existing T019 `foreach`, adds each target with:

```cmake
add_executable(xverse_xcom_activation_plan_t020_${kind}_tests
  "${PROJECT_SOURCE_DIR}/tests/xcom/activation_plan/t020_${src}_tests.cpp")
target_compile_definitions(... PRIVATE
  "XCOM_ACTIVATION_PLAN_FIXTURE_DIR=\"${PROJECT_SOURCE_DIR}/tests/xcom/activation_plan/fixtures\""
  "XCOM_ACTIVATION_PLAN_SCHEMA_PATH=\"${PROJECT_SOURCE_DIR}/src/xverse/xcom/contracts/v1/activation-plan.schema.json\""
  "XCOM_T020_PROFILE_SCHEMA_PATH=\"${PROJECT_SOURCE_DIR}/xdl/profiles/xcom-v0.1.schema.json\"")
target_link_libraries(... PRIVATE xverse::xcom_activation_plan GTest::gtest_main GTest::gmock Threads::Threads)
xverse_xcom_apply_warnings(...)
gtest_discover_tests(... PROPERTIES LABELS "t020-${label}")
```

No library is added or changed; the T019 `xverse_xcom_activation_plan` library and its targets are untouched.
The existing T019 targets keep their `t019;...` labels; the T020 targets carry the distinct `t020-<kind>` labels
(rev 2, see §2.2).

Rev 3 briefly added a further, scheduling-only statement in the same shared block marking the pre-existing
`xcom_observation_disabled_benchmark` CTest test `RUN_SERIAL TRUE`. **Rev 4 reverted that change**: the
benchmark is owned by the observation slice (T025) and modifying its accepted test configuration is outside
T020's declared scope, so its registration is restored to baseline
(`PROPERTIES LABELS "performance;observation"`, no `RUN_SERIAL`). The pre-existing host-timing sensitivity is
recorded as an external dependency/blocker for the full-suite gate (see `implementation.md` §10 and
`verification-plan.md` §13). No T020 test's expected result is changed and no check is weakened.

## 11. Concurrency, lifetime, and failure semantics of the test units

- **Ownership.** `task-owns-artifact` for the T020 test sources and `PLAN_DOCS`; the C++ suites consume the
  decoder as `caller-owns-value`; the Python module consumes the repository modules read-only.
- **Lifetime.** `static-immutable` for the test sources (fixed for the candidate); the decoded `ActivationPlan`
  is `plan-scoped` and immutable, shared only within one test.
- **Thread-safety.** `offline-single-threaded`; each suite runs in one process with no thread and no mutable
  shared state, so **no concurrency bound is applicable or asserted**; the only `Threads::Threads` link is the
  inherited build convention and creates no thread.
- **Bounds.** Every input is finite and bounded; bound cases use small vectors and adjusted caps; overflow
  policy `fail-closed`.
- **Failure semantics.** A test that observes an unexpected outcome/code/value fails; a missing case or a
  golden mismatch fails; no partial success; the suite never weakens an expected result to pass.
- **Determinism.** The same case run repeatedly yields the same result; no clock, network, subprocess, or
  ambient-state input exists.

## 12. Governance and non-promotion

The T020 candidate changes only the declared paths of `requirements.md` §2.4. It records
`ref002.disposition = "unchanged"` with an empty promoted set, binds to baseline
`1e289bfe6234553df94eb25065371f7d423fad88`, and leaves the T020 checkbox unchecked in the plan stage. A change
outside the authorized set, an unknown authorization, a dangling link, a new dependency, a REF-002 promotion,
or a public-safety leak fails the declared checks `T20-G01`..`T20-G05`.
