# T013 Detailed Design — Immutable Core Value, Contract, Policy, and Diagnostic Rules

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T013 (capability 007, slice `T-CORE`) |
| Stage / role | plan → detailed design (pre-code) |
| Revision | 1 |
| Baseline revision | `863f11ac990c1ce178a0f9d8eb2489e4a5243fe7` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Realization vocabulary | T010 `bound_kind_vocabulary`, `overflow_policy_vocabulary`, `outcome_vocabulary`, `thread_safety_vocabulary` |
| Classification | Public-safe engineering work product |

The rules below are normative for the implementation stage. Existing baseline behaviour of the value,
contract, item, diagnostic, and result units is preserved exactly; the new material is the immutable
`FlowPolicy` declaration value and its `policy` diagnostic phase/code. A conflict is resolved in favour of
the accepted source and recorded, not guessed.

## 2. Value primitive rules (`T13-CMP-VALUE`, `T13-CMP-RESULT`)

| Type | Capacity / range | Validation rule | Rejection |
| --- | --- | --- | --- |
| `Identity` | 1–128 bytes (`kMaximumIdentityBytes`) | non-empty; no ASCII control byte (0x00–0x1F, 0x7F); no leading/trailing ASCII whitespace; byte-for-byte, locale-independent | `std::nullopt` |
| `SemanticVersion` | 1–32 bytes (`kMaximumVersionBytes`) | canonical decimal `major.minor.patch`; each component non-empty digits without a leading zero; exactly two `.` | `std::nullopt` |
| `Payload` | 0–65,536 bytes (`kMaximumPayloadBytes`) | copies caller bytes into fixed storage | `std::nullopt` |
| `Timestamp` | any `std::int64_t` nanoseconds | stores the magnitude; exposes no cross-domain comparison | cannot fail |
| `Result<T>` | one `T` or one non-empty `DiagnosticSet` | exclusive `std::variant`; `noexcept` copy; assignment deleted | n/a |

Ownership: caller-owns-value. Lifetime: invocation-scoped. Thread-safety: immutable-value. Failure:
`noexcept` factories return an empty optional/failure alternative and never expose a partial value.

## 3. Contract rules (`T13-CMP-CONTRACT`)

### 3.1 Interaction and direction vocabulary

| `InteractionKind` | Source direction | Target direction |
| --- | --- | --- |
| `signal_state_update` | `produce` | `consume` |
| `message_event` | `produce` | `consume` |
| `service_request` | `request` | `respond` |
| `service_response` | `respond` | `request` |

`CommunicationContract::create` validates the five required identities/versions plus the interaction kind
and its compatible direction pair. Rejections use the stable codes in §6. Logical identity is validated
independently of any provider, protocol, address, or physical realization (T13-XB-2).

### 3.2 Item rules (`T13-CMP-ITEM`)

`CommunicationItem::create` validates eleven required identities/versions (contract id/version, interface,
endpoint, schema id/version, clock domain, correlation, causation, route, provider), the `OriginKind`
enumeration (`component`, `validation_tool`, `replay`, `provider_generated`), the payload bound, and exact
consistency of contract id/version/interface/schema id/schema version and interaction kind against the
supplied immutable contract. A non-empty item field that differs from the contract is a
`contract_mismatch`; an empty required field is `required_field`. The item retains one timestamp magnitude
and one explicit clock-domain identity and provides no cross-domain ordering (T013-SR-012).

## 4. Immutable policy design (new in T013) (`T13-CMP-CONTRACT`)

### 4.1 Vocabulary and ranges (authority: `xdl/profiles/xcom-v0.1.schema.json` flow-policy)

| Field | Type | Accepted values / range | External text |
| --- | --- | --- | --- |
| `ordering` | `OrderingPolicy` | `fifo`, `priority`, `unordered` | `"fifo"`, `"priority"`, `"unordered"` |
| `reliability` | `ReliabilityPolicy` | `at_most_once`, `at_least_once`, `exactly_once`, `best_effort` | `"at-most-once"`, `"at-least-once"`, `"exactly-once"`, `"best-effort"` |
| `overflow` | `OverflowPolicy` | `drop_oldest`, `drop_newest`, `coalesce`, `lossless_backpressure`, `reject`, `fail_closed` | `"drop-oldest"`, `"drop-newest"`, `"coalesce"`, `"lossless-backpressure"`, `"reject"`, `"fail-closed"` |
| `deadline_ms` | `std::int64_t` | 0 ≤ value ≤ 600,000 (`kMaximumDeadlineMs`) | decimal |
| `retry` | `std::int64_t` | 0 ≤ value ≤ 64 (`kMaximumRetry`) | decimal |
| `queue_depth` | `std::int64_t` | 1 ≤ value ≤ 65,536 (`kMaximumQueueDepth`) | decimal |

The vocabulary and ranges are copied from the accepted Profile form so T013 introduces no competing
configuration language and cannot accept a declaration the XDL Profile rejects (T013-SR-007,
Constitution III). Provider **capability** advertisements (T015 `DeliveryCapability`/`OrderingCapability`)
remain distinct from this declared **policy**; T014/T015 match them without strengthening the declaration.

### 4.2 Declared interface

```cpp
enum class OrderingPolicy { fifo, priority, unordered };
enum class ReliabilityPolicy { at_most_once, at_least_once, exactly_once, best_effort };
enum class OverflowPolicy { drop_oldest, drop_newest, coalesce, lossless_backpressure, reject, fail_closed };

[[nodiscard]] std::string_view to_string(OrderingPolicy) noexcept;
[[nodiscard]] std::string_view to_string(ReliabilityPolicy) noexcept;
[[nodiscard]] std::string_view to_string(OverflowPolicy) noexcept;

struct FlowPolicyInput final {
  OrderingPolicy ordering;
  ReliabilityPolicy reliability;
  OverflowPolicy overflow;
  std::int64_t deadline_ms;
  std::int64_t retry;
  std::int64_t queue_depth;
};

class FlowPolicy final {
 public:
  static constexpr std::int64_t kMaximumDeadlineMs = 600000;
  static constexpr std::int64_t kMaximumRetry = 64;
  static constexpr std::int64_t kMaximumQueueDepth = 65536;
  [[nodiscard]] static Result<FlowPolicy> create(const FlowPolicyInput& input) noexcept;
  FlowPolicy(const FlowPolicy& other) noexcept = default;      // copy only
  FlowPolicy& operator=(const FlowPolicy&) = delete;
  [[nodiscard]] OrderingPolicy ordering() const noexcept;
  [[nodiscard]] ReliabilityPolicy reliability() const noexcept;
  [[nodiscard]] OverflowPolicy overflow() const noexcept;
  [[nodiscard]] std::int64_t deadline_ms() const noexcept;
  [[nodiscard]] std::int64_t retry() const noexcept;
  [[nodiscard]] std::int64_t queue_depth() const noexcept;
  friend bool operator==(const FlowPolicy&, const FlowPolicy&) = default;
 private:
  explicit FlowPolicy(const FlowPolicyInput& input) noexcept;
  OrderingPolicy ordering_;
  ReliabilityPolicy reliability_;
  OverflowPolicy overflow_;
  std::int64_t deadline_ms_;
  std::int64_t retry_;
  std::int64_t queue_depth_;
};
```

Ownership: caller-owns-value. Lifetime: invocation-scoped (not retained beyond the consuming invocation).
Thread-safety: immutable-value (safe copy; concurrent const reads). Failure: `create` is `noexcept`, is
allocation-free, and never substitutes a default for a missing or invalid declaration.

### 4.3 Validation rules and diagnostics

`FlowPolicy::create` accumulates one `invalid_policy` diagnostic per violated field, in the fixed order
`ordering`, `reliability`, `overflow`, `deadline_ms`, `retry`, `queue_depth` (at most six), and returns
`failure` with the deterministically sorted `DiagnosticSet` when any field is violated, otherwise
`success` with every field copied exactly.

| Condition | Code | Phase | Affected field | Reason | Correction |
| --- | --- | --- | --- | --- | --- |
| `ordering` is not a declared value | `XCOM-TYPE-E006` | `policy` | `ordering` | `ordering policy is outside the declared vocabulary` | `use one declared ordering policy` |
| `reliability` is not a declared value | `XCOM-TYPE-E006` | `policy` | `reliability` | `reliability policy is outside the declared vocabulary` | `use one declared reliability policy` |
| `overflow` is not a declared value | `XCOM-TYPE-E006` | `policy` | `overflow` | `overflow policy is outside the declared vocabulary` | `use one declared overflow policy` |
| `deadline_ms` < 0 or > 600,000 | `XCOM-TYPE-E006` | `policy` | `deadline_ms` | `deadline is outside the declared range` | `use a deadline between 0 and 600000 milliseconds` |
| `retry` < 0 or > 64 | `XCOM-TYPE-E006` | `policy` | `retry` | `retry is outside the declared range` | `use a retry count between 0 and 64` |
| `queue_depth` < 1 or > 65,536 | `XCOM-TYPE-E006` | `policy` | `queue_depth` | `queue depth is outside the declared range` | `use a finite queue depth between 1 and 65536` |

The "no upgrade" rule is structural: there is no factory overload that supplies a default policy, no
"stronger" substitution, and `operator==` compares every declared field, so a weaker and a stronger
declaration are never equal (T013-SR-006).

## 5. Diagnostic rules (`T13-CMP-DIAG`)

- **Additive additions**: `DiagnosticCode::invalid_policy` → external text `XCOM-TYPE-E006`;
  `ValidationPhase::policy` → external text `"policy"`.
- **No existing value changes**: the existing codes `XCOM-TYPE-E001`–`E005`, `XCOM-LIFE-E006`–`E013`,
  the three severities, the eight existing phases, the ordering-key layout, `kMaximumCodeBytes = 14`,
  `kMaximumPhaseBytes = 23`, `kMaximumTextBytes = 256`, and `kMaximumDiagnostics = 32` are unchanged.
  `"policy"` (6 bytes) and `XCOM-TYPE-E006` (14 bytes) fit the existing bounds.
- **Ordering key**: `phase|severity|code|affected_identity|reason|correction`, each field escaped with
  `\` before `\` and `|`; `DiagnosticSet` sorts by this key with a stable insertion sort, so equivalent
  invalid inputs serialize to byte-identical sequences regardless of input order.
- **Public helpers**: `serialize()` returns a dynamic `std::string` and may propagate `std::bad_alloc`
  (reporting convenience); allocation-free inspection uses `ordering_key()`/`values()`.

## 6. Failure semantics and outcome mapping

| Condition | Outcome (T010 vocabulary) | Observable result |
| --- | --- | --- |
| Missing/empty required field or version | `rejected` | non-empty `DiagnosticSet` with `required_field` |
| Over-bound identity, version, payload, or text | `rejected` | `DiagnosticSet` with `bound_exceeded` (or `invalid_version`) |
| Unknown enumeration (interaction, direction, origin, policy) | `rejected` | `DiagnosticSet` with the mapped code |
| Policy field outside the declared vocabulary or range | `rejected` | `DiagnosticSet` with `invalid_policy` (`XCOM-TYPE-E006`) |
| Item field inconsistent with its contract | `rejected` | `DiagnosticSet` with `contract_mismatch` |
| Internal defect in a core type (not reachable from valid input) | `failed` | reported by the owning unit; never a partial value |
| Unknown outcome for any core factory | `failed` | never reported as success |

No core factory performs I/O; no rejected operation mutates the caller's input or leaves a partially
published value.

## 7. Bounds and concurrency summary

| Unit | Bound kind | Value | Overflow policy |
| --- | --- | --- | --- |
| Value/payload | bytes (payload) | 65,536 | `fail-closed` |
| Value/payload | capacity (elements) | fixed | `fail-closed` |
| Contract/item record | bytes | fixed capacities | `fail-closed` |
| Policy | quota (queue depth) | 1–65,536 | `reject` |
| Policy | retry | 0–64 | `reject` |
| Policy | deadline | 0–600,000 ms | `reject` |
| Diagnostics | capacity | 32 entries | `fail-closed` |

Concurrency: every published value is immutable (`immutable-value`), copy construction is `noexcept`, and
assignment is deleted so a returned accessor/span cannot be invalidated. Separate values share no state,
so concurrent const reads are safe without a lock. The core adds no thread.

## 8. Doxygen design

Every new/changed public declaration carries a `@brief`, and the new `FlowPolicy` API additionally carries
`@ownership`, `@lifetime`, `@thread_safety`, and `@failure` clauses; `@param`, `@return`, and `@retval`
are supplied where a parameter or result exists. The file header blocks keep the mandatory `@file`,
`@brief`, and `@ingroup` (group `xcom_core`). The admitted `Doxyfile` configuration is not changed;
strict declaration-level Doxygen stays `DOX-GAP-01` (T011/T037).

## 9. Public-safety design

The candidate contains repository-relative paths, type and field names, stable code text, and pass/fail
outcomes only. It embeds no credential, private address, unrestricted payload, proprietary source excerpt,
environment-specific absolute host path, or sensitive deployment value. Diagnostic reasons/corrections
are fixed, bounded, non-sensitive text.

## 10. Design decisions and open items

- `D-01` — **The policy type is a standalone immutable declaration value, not embedded into
  `CommunicationContract`.** The accepted data-model lists policy on the contract, and the plan-level
  `Policies` model (T019) decodes it; composing the declared policy into `CommunicationContract` or a
  route is `XCOM-SW-CORE-004`'s binding half, owned by T014 (`T013-GAP-02`, `T013-OPEN-01`). Keeping it
  standalone makes the change purely additive and leaves every existing contract/item consumer and test
  unchanged.
- `D-02` — **The policy vocabulary is copied from the accepted Profile schema, not invented.**
  `xdl/profiles/xcom-v0.1.schema.json` is the canonical declaration; the C++ value mirrors it verbatim
  (T013-SR-007).
- `D-03` — **The policy diagnostic code is a new stable code `XCOM-TYPE-E006` in the TYPE family**, so the
  existing `XCOM-LIFE-E006` (invalid digest) and every ordering key are unchanged (T013-SR-009).
- `D-04` — **The implementation lives in the existing `contract.cpp` translation unit**, already compiled
  by the T012 `xverse_xcom_core_types` target, so no CMake/`.cmake` file changes and no inherited T020
  trace-link hash refresh is required (`T013-OPEN-02`).
