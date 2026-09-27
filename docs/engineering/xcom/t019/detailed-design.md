# T019 Detailed Design — `xverse::xcom::plan` Bounded Activation-Plan Decoder

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T019 |
| Stage / role | plan → detailed design |
| Revision | 1 |
| Baseline revision | `199de0baa1f50e1d429527b6d6525a6e5d8cf7cf` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Output-schema authority | `src/xverse/xcom/contracts/v1/activation-plan.schema.json` (T017) and `specs/007-xcom-core/contracts/communication-plan.md` |
| Digest-rule authority | `specs/007-xcom-core/contracts/xdl-profile.md` "Activation-plan v1 digest and provenance"; `docs/engineering/xcom/t017/detailed-design.md` §5; `scripts/validate_xcom_plan.py` (`canonical_bytes`, `compute_digest`, `check_digest`) |
| Reference producer | `src/xverse_xdl/xcom_plan.py` (T018; anchored, unchanged) |
| Governing ADRs | ADR-0016, ADR-0018, ADR-0020 |
| Language / tooling | C++20; only the standard library and the admitted `nlohmann/json` 3.10.5 header at compile and link time |

This design is written **before** implementation. The implementation must realise every named identifier and
rule. The identifiers below are fixed by this document; the plan member names are the T017 schema's interface.

## 2. Fixed identifiers and vocabularies

### 2.1 Artifact identifiers

| Identifier | Path |
| --- | --- |
| `DECODER_HEADER` | `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp` |
| `DECODER_SOURCE` | `src/xverse/xcom/src/activation_plan.cpp` |
| `DECODER_TESTS_UNIT` | `tests/xcom/activation_plan/decoder_unit_tests.cpp` |
| `DECODER_TESTS_NEGATIVE` | `tests/xcom/activation_plan/decoder_negative_tests.cpp` |
| `PLAN_SCHEMA` | `src/xverse/xcom/contracts/v1/activation-plan.schema.json` (anchored, unchanged) |
| `PLAN_FIXTURES` | `tests/xcom/activation_plan/fixtures/plan/valid/` (anchored, read-only) |
| `BUILD_WIRING` | `src/xverse/xcom/CMakeLists.txt` (shared) |
| `PLAN_DOCS` | `docs/engineering/xcom/t019/` |

### 2.2 Constants

| Name | Value |
| --- | --- |
| `kNamespace` | `xverse::xcom::plan` |
| `TASK_ID` | `"T019"` (documentation/evidence only; never emitted into a decoded plan) |
| `kPlanVersion` | `"1"` |
| `kDigestAlgorithm` | `"sha256"` |
| `kPlanDomainSeparator` | `"xverse.xcom.activation-plan.v1"` (30 bytes) + one `'\0'` byte |
| `kPlanTarget` | `"xcom-plan"` (fixed diagnostic target for plan-level findings) |
| `kDigestHexLength` | `64` |

### 2.3 Outcome and code vocabularies (closed)

| Name | Values |
| --- | --- |
| `DecodeOutcome` (enum class) | `accepted`, `rejected`, `failed` |
| `DecodeCode` (closed string vocabulary) | `XCOM-DECODE-INPUT`, `XCOM-DECODE-SHAPE`, `XCOM-DECODE-VERSION`, `XCOM-DECODE-DIGEST`, `XCOM-DECODE-CAPABILITY`, `XCOM-DECODE-REFERENCE`, `XCOM-DECODE-UNRESOLVED`, `XCOM-DECODE-BOUND`, `XCOM-DECODE-UNKNOWN` |

Every code matches `^XCOM-[A-Z0-9-]{3,64}$`. Outcome mapping: `XCOM-DECODE-BOUND` and
`XCOM-DECODE-UNKNOWN` are `failed`; every other code is `rejected`; an absent code is `accepted`.

### 2.4 Plan member and vocabulary tables (drift-guarded against `PLAN_SCHEMA`)

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
  `unresolved`}; `resourceRef.kind` ∈ {`Component`, `Deployment`, `Scenario`}; `digest.algorithm` ∈
  {`sha256`}.
- **Patterns:** identifier `^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$` (1..127); version
  `^[0-9]+\.[0-9]+(?:\.[0-9]+)?$`; digest value `^[0-9a-f]{64}$` (applied to every embedded digest — the
  top-level `digest`, `provenance.graphDigest`, and each `provenance.resources[].sourceDigest`); generator
  task `^T[0-9]{3}$`; diagnostic code `^XCOM-[A-Z0-9-]{3,64}$`; `apiVersion` const
  `xverse.io/xdl/v1alpha1`.
- **Numeric ranges:** `deadlineMs` 0..600000; `retry` 0..64; `queueDepth` 1..65536 (all integers).
- **Collection keys and minimums:** `contracts`→`contractId`, `endpoints`→`endpointId`, `routes`→`routeId`,
  `providers`→`providerId`, `observationPoints`→`tapId`, `clockDomains`→`clockDomainId`,
  `provenance.resources`→(`apiVersion`,`kind`,`namespace`,`name`,`version?`); each ordered ascending by its
  declared key with unique keys; `providers[].capabilities` `minItems: 1`; `provenance.resources`
  `minItems: 1`; `activationOrder` `minItems: 1`, duplicate-free.

A decoder constant table encodes these and a unit test asserts it equals the committed `PLAN_SCHEMA`
(`CHK-06`), so the decoder cannot silently drift from the normative schema. The tables are the same ones the
T018 compiler emits.

## 3. Public API (`DECODER_HEADER`)

```cpp
namespace xverse::xcom::plan {

/// Bounded decode limits; every value is finite and >= 1.
struct DecodeLimits {
  std::size_t max_bytes = 5u * 1024u * 1024u;
  std::size_t max_depth = 100u;
  std::size_t max_nodes = 100'000u;
  std::size_t max_string_length = 4096u;
  std::size_t max_contracts = 4096u;
  std::size_t max_endpoints = 4096u;
  std::size_t max_routes = 4096u;
  std::size_t max_providers = 256u;
  std::size_t max_observation_points = 1024u;
  std::size_t max_clock_domains = 256u;
  std::size_t max_diagnostics = 4096u;
  std::size_t max_activation_order = 8192u;
  std::size_t max_provenance_resources = 1000u;
};

enum class DecodeOutcome { accepted, rejected, failed };

/// Stable code plus the affected identifier (or kPlanTarget).
struct DecodeError {
  std::string code;       // closed DecodeCode vocabulary
  std::string target_id;  // plan identifier or "xcom-plan"
  std::string message;    // bounded; never contains payload content or an absolute path
};

// Bounded, immutable decoded value types (every string bounded, every array capped):
struct PlanDigest { std::string algorithm; std::string value; };
struct ResourceRef { std::string api_version, kind, ns, name; std::optional<std::string> version;
                     PlanDigest source_digest; };
struct Provenance { std::string generated_at; PlanDigest graph_digest;
                    std::vector<ResourceRef> resources; };
struct Contract { std::string contract_id, schema_id, schema_version; };
struct Endpoint { std::string endpoint_id, role; };
struct Route { std::string route_id, from, to, contract_id; };
struct Provider { std::string provider_id; std::vector<std::string> capabilities, required_capabilities; };
struct Policies { std::string ordering, reliability, overflow, backpressure;
                  std::int64_t deadline_ms, retry, queue_depth; };
struct ObservationPoint { std::string tap_id, route_id, payload_access, validity_effect; };
struct Stimulation { std::vector<std::string> actions, permit_policy_refs; };
struct ClockDomain { std::string clock_domain_id, source; };
struct Diagnostic { std::string code, severity, target_id; };
struct InputResolution { std::string identity, schema, capability, time, ownership, policy; };

struct ActivationPlan {
  std::string plan_version;
  PlanDigest digest;
  std::string generator_task, generator_version;
  Provenance provenance;
  std::vector<Contract> contracts;
  std::vector<Endpoint> endpoints;
  std::vector<Route> routes;
  std::vector<Provider> providers;
  Policies policies;
  std::vector<ObservationPoint> observation_points;
  Stimulation stimulation;
  std::vector<ClockDomain> clock_domains;
  std::vector<std::string> activation_order;
  std::vector<Diagnostic> diagnostics;
  std::string status;
  InputResolution input_resolution;
};

struct DecodeResult {
  DecodeOutcome outcome = DecodeOutcome::rejected;
  std::optional<ActivationPlan> plan;  // engaged iff outcome == accepted
  DecodeError error;                   // populated iff outcome != accepted
};

/// True iff every DecodeLimits member is >= 1.
bool is_valid(const DecodeLimits& limits) noexcept;

/// Lowercase-hex SHA-256 of the given bytes (pure; never throws).
std::string sha256_hex(std::string_view bytes);

/// Canonical bytes of the digested region (plan minus top-level digest).
/// On a malformed/over-bound input, returns a rejected/failed result with empty value.
struct BytesResult { DecodeOutcome outcome = DecodeOutcome::rejected; std::string value; DecodeError error; };
BytesResult canonical_plan_body_bytes(std::string_view document_json, const DecodeLimits& limits = {});

/// Recomputed domain-separated SHA-256 hex of the plan body, or a classified error.
BytesResult recompute_plan_digest(std::string_view document_json, const DecodeLimits& limits = {});

/// Bounded decode with independent version/digest/capability verification.
DecodeResult decode_activation_plan(std::string_view document_json, const DecodeLimits& limits = {});

}  // namespace xverse::xcom::plan
```

- `ActivationPlan` is a plain aggregate value: copyable and movable, no virtual functions, no internal
  synchronization, no pointer aliasing of the input buffer. The caller owns the returned value
  (`caller-owns-value`, `immutable-value`, `plan-scoped`).
- The header exposes no `nlohmann::json` type; the third-party JSON type is an implementation detail of
  `DECODER_SOURCE`. This keeps the platform-facing API bounded and domain-neutral.
- `decode_activation_plan` falls back to `canonical_plan_body_bytes`/`recompute_plan_digest` internally so the
  tests and the decoder share exactly one canonicalization implementation.

## 4. `T019-U-01` — Bounded strict parse

`detail::parse_bounded(std::string_view bytes, const DecodeLimits&, nlohmann::json& out, DecodeError& err)`:

1. If `!is_valid(limits)` → `failed`/`XCOM-DECODE-UNKNOWN` (`kPlanTarget`); no parse.
2. If `bytes.size() > limits.max_bytes` → `failed`/`XCOM-DECODE-BOUND` (`kPlanTarget`).
3. Parse with `nlohmann::json::sax_parse(bytes, &handler, /*strict=*/true)` where `handler` is a strict
   `nlohmann::json_sax<nlohmann::json>` that:
   - builds an explicit value stack and per-open-object key set; a repeated key in one object →
     `rejected`/`XCOM-DECODE-INPUT` (`kPlanTarget`) (never collapsed last-wins);
   - counts object/array nesting and rejects depth `> max_depth` → `failed`/`XCOM-DECODE-BOUND`;
   - counts every scalar and container node and rejects nodes `> max_nodes` → `failed`/`XCOM-DECODE-BOUND`;
   - bounds every string to `max_string_length` → `rejected`/`XCOM-DECODE-SHAPE`;
   - captures `number_integer`/`number_unsigned` exactly and `number_float` only when finite and
     representable as an integer within `int64`/`uint64` (stored as an integer) or as a non-integral finite
     double; a non-finite or out-of-range number → `rejected`/`XCOM-DECODE-INPUT`.
4. Malformed JSON or a parse error with no document → `rejected`/`XCOM-DECODE-INPUT`. A non-object root →
   `rejected`/`XCOM-DECODE-INPUT`. Trailing non-whitespace content is a parse error (strict mode).
5. On success, `out` is a DOM with integral numbers normalized to their single integer form; no partial DOM is
   exposed on error.

The parse performs no file, socket, subprocess, or environment access.

## 5. `T019-U-02` — Closed shape, vocabulary, identifiers, and order

`detail::validate_shape(const nlohmann::json&, const DecodeLimits&, DecodeError&)` walks the DOM against the
§2.4 tables and fails closed (`rejected`/`XCOM-DECODE-SHAPE` with the affected identifier or `kPlanTarget`):

1. The root is an object; the exact 16 required members are present and no other member exists
   (`additionalProperties: false`).
2. Nested objects are closed and carry their required members: `digest`, `generator`, `provenance`,
   `provenance.resources[]`, `provenance.graphDigest`, each `contracts[]`, `endpoints[]`, `routes[]`,
   `providers[]`, `policies`, each `observationPoints[]`, `stimulation`, each `clockDomains[]`, each
   `diagnostics[]`, and `inputResolution`.
3. Closed enums and const values match §2.4; every embedded digest carries `algorithm` ∈ {`sha256`} and a
   value matching `^[0-9a-f]{64}$`. The top-level recorded `digest`'s algorithm/hex form is deferred to the
   version/digest step for code classification (§6.3, §12), while `provenance.graphDigest` and every
   `provenance.resources[].sourceDigest` are closed here as `XCOM-DECODE-SHAPE`; the plan identifier/version/
   diagnostic-code patterns match; `apiVersion` is the const.
4. Numeric members are integers in their declared ranges; a non-integer token for an integer member, an empty
   `providers[].capabilities`, or an empty `provenance.resources` is `rejected`/`XCOM-DECODE-SHAPE`.
5. `activationOrder` is non-empty and duplicate-free.
6. Every identity-bearing collection is ordered ascending by its declared key with unique keys
   (`contracts`, `endpoints`, `routes`, `providers`, `observationPoints`, `clockDomains`,
   `provenance.resources` by the tuple with the absent optional `version` sorting first, and `diagnostics` by
   `(code, targetId)`). A duplicate key or an out-of-order collection is `rejected`/`XCOM-DECODE-SHAPE`.

A private constant table encodes the member/enum/pattern sets; a test asserts table/`PLAN_SCHEMA` equality.

## 6. `T019-U-03` — Canonicalization, SHA-256, and independent digest

### 6.1 Canonical serialization (T017 rule reproduced independently)

`detail::canonical_bytes(const json&)` emits UTF-8 with:

1. object members ordered lexicographically by member name (`std::less<std::string>`, byte-wise; identical to
   Python's code-point order for the ASCII member set);
2. no insignificant whitespace;
3. every number emitted in its single integer form (integral numbers already normalized at parse; a
   non-integral or non-finite number in the digested region is `failed`/`XCOM-DECODE-UNKNOWN`, which cannot
   occur for a shape-validated plan whose numeric members are all integers);
4. arrays in their validated order;
5. no duplicate members (already rejected at parse).

String escaping matches Python `json.dumps(..., ensure_ascii=False, separators=(",", ":"))`: `"` and `\`
escaped, `\b \f \n \r \t` short escapes, other code points < 0x20 as `\u00xx`, and all other bytes emitted as
UTF-8. Booleans emit `true`/`false`; `null` emits `null` (absent members are omitted, never emitted as
`null`).

### 6.2 SHA-256

`detail::sha256` implements FIPS 180-4 SHA-256 over the byte span and returns 32 bytes; `sha256_hex` is the
public lowercase-hex wrapper. It is exercised against the published known answers for the empty string and
`"abc"` and against the committed fixture digests, so the digest check is genuinely independent of the
compiler's Python `hashlib`.

### 6.3 Digest

`recompute_plan_digest(document_json, limits)`:

1. `parse_bounded` and `validate_shape` the document (a malformed or shape-invalid document returns the same
   error as the decoder would);
2. build the digested region as the plan value with the top-level `digest` member removed;
3. `digest = sha256_hex(kPlanDomainSeparator || canonical_bytes(body))`;
4. return the 64-lowercase-hex value.

`decode_activation_plan` verifies `planVersion == kPlanVersion` → else `rejected`/`XCOM-DECODE-VERSION`
(`kPlanTarget`); `digest.algorithm == kDigestAlgorithm` and a well-formed 64-lowercase-hex value → else
`rejected`/`XCOM-DECODE-DIGEST`; and the recomputed digest equals the recorded value → else
`rejected`/`XCOM-DECODE-DIGEST` (`kPlanTarget`). The digest is never computed over itself.

## 7. `T019-U-04` — Capability, cross-reference, and status verification

`detail::validate_capability_and_references(const ActivationPlan&)`, or the equivalent DOM pass before model
construction, rejects (`rejected`) with the affected identifier:

| Condition | Code | Defect only when the plan declares |
| --- | --- | --- |
| A plan declares one or more `routes` but selects no `providers` | `XCOM-DECODE-CAPABILITY` (`kPlanTarget`) | `inputResolution.capability == "resolved"` |
| A provider's `required_capabilities` is not a subset of its `capabilities` | `XCOM-DECODE-CAPABILITY` (`providerId`) | `inputResolution.capability == "resolved"` |
| A `routes[].contractId` does not match a declared `contracts[].contractId` | `XCOM-DECODE-REFERENCE` (`routeId`) | `inputResolution.schema == "resolved"` |
| An `observationPoints[].routeId` does not match a declared `routes[].routeId` | `XCOM-DECODE-REFERENCE` (`tapId`) | `inputResolution.schema == "resolved"` |
| A `routes[].from`/`to` does not match a declared `endpoints[].endpointId` | `XCOM-DECODE-REFERENCE` (`routeId`) | `inputResolution.identity == "resolved"` |
| An `activationOrder` entry does not match a declared endpoint or route id | `XCOM-DECODE-REFERENCE` (`kPlanTarget`) | `inputResolution.identity == "resolved"` |
| `status == "activatable"` while any `inputResolution` member is `unresolved` | `XCOM-DECODE-UNRESOLVED` (`kPlanTarget`) | (unconditional; checked after the closure rules) |

A well-formed `status == "inspectable"` plan with an explicit `unresolved` member is **accepted** (the plan
is inspectable but cannot activate); it is not an error. The plan's own `inputResolution` states are the
authority for whether a missing closure is a defect: a capability/schema/identity closure rule is enforced
only when the plan declares the corresponding state `resolved`, so an `inspectable` plan that honestly
records an unresolved capability, schema, or identity reference decodes to a non-activatable value instead
of being rejected. This mirrors the accepted T018 producer, which sets `capability = "unresolved"` when a
graph declares routes but selects no provider (or a provider is capability-insufficient) and `schema =
"unresolved"` when a route references an undeclared contract, and emits `status = "inspectable"` for any
unresolved state; such an artifact must remain decodable. A plan that claims the corresponding state
`resolved` while violating closure — including an `inspectable` plan that over-claims resolution — is
rejected, and an `activatable` plan still requires six resolved states. No capability is invented and no
reference is defaulted.

## 8. `T019-U-05` — Bounded immutable model

`detail::build_model(const json&, const DecodeLimits&, DecodeError&, ActivationPlan&)` copies each validated
member into the §3 value types and enforces the finite entity caps after validation:

| Collection | Cap (`DecodeLimits`) |
| --- | --- |
| `contracts` | `max_contracts` |
| `endpoints` | `max_endpoints` |
| `routes` | `max_routes` |
| `providers` | `max_providers` |
| `observationPoints` | `max_observation_points` |
| `clockDomains` | `max_clock_domains` |
| `diagnostics` | `max_diagnostics` |
| `activationOrder` | `max_activation_order` |
| `provenance.resources` | `max_provenance_resources` |

A cap breach is `failed`/`XCOM-DECODE-BOUND` (`kPlanTarget`) with **no** value. Every decoded string was
already bounded to `max_string_length` at parse. The value is moved into `DecodeResult.plan` only on
`accepted`; on `rejected`/`failed`, `plan` is disengaged.

## 9. `T019-U-06` — Deterministic outcome classification

`decode_activation_plan` executes the pipeline in a fixed order and returns exactly one outcome:

```text
limits check → parse → shape/vocabulary/order → version → digest → capability/reference/status → model caps → accepted
```

The first failing step determines the code and `target_id`; no later step runs after a failure, so the same
input always yields the same outcome, code, and target, and a `rejected`/`failed` result never carries a
decoded value. `message` is bounded and contains only the code, the target identifier, and a short
explanation; it never contains payload content, credentials, private addresses, or an absolute path.

## 10. `T019-U-07` — Work products and evidence record

Maintain the five plan work products and the implementation record for the exact candidate; record the
baseline, authorization, changed-path set, commands, outcomes, and limitations. `task-owns-artifact`, valid
for the candidate revision. Missing product or unsupported claim → `failed`; no acceptance claim.

## 11. `T019-U-08` — Decoder tests and CMake/CTest integration

### 11.1 Build wiring (`BUILD_WIRING`, shared)

```cmake
add_library(xverse_xcom_activation_plan STATIC src/activation_plan.cpp)
add_library(xverse::xcom_activation_plan ALIAS xverse_xcom_activation_plan)
target_include_directories(xverse_xcom_activation_plan PUBLIC "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>")
target_link_libraries(xverse_xcom_activation_plan PUBLIC nlohmann_json::nlohmann_json)
target_compile_features(xverse_xcom_activation_plan PUBLIC cxx_std_20)
xverse_xcom_apply_warnings(xverse_xcom_activation_plan)
```

Inside the existing `if(BUILD_TESTING)` block (which already finds GTest), two executables are added —
`xverse_xcom_activation_plan_unit_tests` and `xverse_xcom_activation_plan_negative_tests` — each linking
`xverse::xcom_activation_plan GTest::gtest_main Threads::Threads`, given the fixture directory through a
compile definition (`XCOM_ACTIVATION_PLAN_FIXTURE_DIR="${PROJECT_SOURCE_DIR}/tests/xcom/activation_plan/
fixtures"`; a build-time path, never a committed host path), and registered with
`gtest_discover_tests(... PROPERTIES LABELS "t019;unit")` / `"t019;negative"`. The library target is added
outside the `BUILD_TESTING` guard so the decoder is a first-class platform unit. No T025 target, warning
policy, or existing test is modified.

### 11.2 Test cases

`DECODER_TESTS_UNIT`:

- `Decode.PublicApiAndConstants` — API/constant presence and `DecodeLimits` defaults (CHK-01, CHK-10).
- `Decode.Sha256KnownAnswers` — empty string `e3b0c442…`, `"abc"` `ba7816bf…` (CHK-04).
- `Decode.PositiveActivatableFixture` / `Decode.PositiveInspectableFixture` — committed T017 fixtures decode
  to `accepted` with the expected members (CHK-02, CHK-03).
- `Decode.InspectableUnresolvedCapabilityIsAccepted` / `Decode.InspectableUnresolvedReferenceIsAccepted` — a
  digest-sealed `inspectable` plan that declares a route with no selected provider and an unresolved
  capability (the accepted T018 producer's shape) or an unresolved schema/identity reference decodes to
  `accepted` with a non-activatable value (CHK-05, T019-STK-003 AC-3).
- `Decode.DigestAgreesWithT017Fixture` — recomputed digest equals each fixture's recorded digest (CHK-02).
- `Decode.DecodedFieldsMatchFixture` — decoded member values equal the fixture (CHK-03).
- `Decode.CanonicalBodyIsMemberSortedWhitespaceFree` — canonical body bytes are member-ordered and
  whitespace-free; reordering/whitespace/integral-number variants share one digest (CHK-08, DET-03, DET-04).
- `Decode.ReorderedDocumentSameDigestAndResult` — reordered-but-equivalent document yields one digest and one
  result (DET-01, DET-02).
- `Decode.ValueIsImmutableAndCopyable` — `static_assert`s: no mutation surface, copyable/movable, no
  concurrency primitive (CHK-10).
- `Decode.LimitsValidationBounds` — every `DecodeLimits` member ≥ 1; a zeroed limit is `failed` with no plan
  (BND-05).

`DECODER_TESTS_NEGATIVE` — one test per declared case `NEG-D01`..`NEG-D22`, each asserting the declared
outcome, code, target, and the absence of a decoded plan.

## 12. Bounds, failure semantics, and concurrency

| T019 condition | Outcome |
| --- | --- |
| malformed JSON, duplicate member, non-object root, non-finite/out-of-range number | `rejected` (`XCOM-DECODE-INPUT`) |
| missing/unknown member, closed-vocabulary/pattern/range violation, empty capability resource, empty/duplicate `activationOrder`, out-of-order or duplicate-keyed collection, over-length string | `rejected` (`XCOM-DECODE-SHAPE`) |
| `planVersion` ≠ `"1"` | `rejected` (`XCOM-DECODE-VERSION`) |
| top-level recorded `digest` algorithm/hex malformed, or recomputed ≠ recorded | `rejected` (`XCOM-DECODE-DIGEST`) |
| embedded `provenance.graphDigest` or `provenance.resources[].sourceDigest` algorithm/value violates `$defs/digest` | `rejected` (`XCOM-DECODE-SHAPE`) |
| provider required capability not declared, or routes with no provider, while `capability` is `resolved` | `rejected` (`XCOM-DECODE-CAPABILITY`) |
| unresolved route/observation/activation-order reference while the governing `schema`/`identity` state is `resolved` | `rejected` (`XCOM-DECODE-REFERENCE`) |
| `activatable` with an unresolved input-resolution member | `rejected` (`XCOM-DECODE-UNRESOLVED`) |
| byte, depth, node, or decoded-entity bound exceeded | `failed` (`XCOM-DECODE-BOUND`, no value) |
| internal defect or unknown step (invalid limits, unexpected canonicalization state) | `failed` (`XCOM-DECODE-UNKNOWN`, no value) |
| all checks pass | `accepted` with an immutable decoded value |

**Concurrency.** The decoder is a pure function with no shared mutable state, no global, and no
synchronization; an accepted `ActivationPlan` is immutable and may be read concurrently by any number of
readers without a lock (`XCOM-DU-011` `immutable-value`). No concurrency test is required; the immutability
contract is enforced by the value type (no mutating accessor) and asserted at compile time.

**Limits validation.** Each `DecodeLimits` member must be ≥ 1; an invalid limit is `failed`
(`XCOM-DECODE-UNKNOWN`) before parsing. The default caps are ≥ the T018 `CompileLimits` caps
(`max_endpoints` 4096, `max_routes` 4096, `max_providers` 256, `max_observation_points` 1024,
`max_clock_domains` 256, `max_diagnostics` 4096, `max_resources` 1000, `max_bytes` 5 MiB, `max_depth` 100,
`max_nodes` 100 000), so every plan the accepted compiler can emit fits the decoder bounds; no production
numeric value is fixed.

## 13. Cross-language contract at the boundary

The plan schema and the digest rule are the **only** interface between the Python compiler (T018) and this
C++ decoder. T019 reproduces the canonicalization and digest rules independently in C++ and rejects a
version/digest/capability mismatch; it adds no contract statement and changes no T017/T018 artifact. The
decoder's internal helpers (`canonical_plan_body_bytes`, `recompute_plan_digest`, `sha256_hex`) exist so the
independence claim is directly observable in tests, not to define a new contract.

## 14. Unit and artifact trace

| Requirement | Design unit | Artifact | Design section |
| --- | --- | --- | --- |
| T019-SR-001 | `T019-U-01` | `DECODER_SOURCE` | §4 |
| T019-SR-002 | `T019-U-02` | `DECODER_SOURCE` | §5 |
| T019-SR-003 | `T019-U-03` | `DECODER_SOURCE`, `DECODER_HEADER` | §6 |
| T019-SR-004 | `T019-U-04` | `DECODER_SOURCE` | §7 |
| T019-SR-005 | `T019-U-05` | `DECODER_HEADER`, `DECODER_SOURCE` | §3, §8 |
| T019-SR-006 | `T019-U-06` | `DECODER_SOURCE` | §9 |
| T019-SR-007 | `T019-U-08` | `DECODER_TESTS_UNIT`, `DECODER_TESTS_NEGATIVE`, `BUILD_WIRING` | §11 |
| T019-SR-008 | `T019-U-07` | `PLAN_DOCS` | §10 |
