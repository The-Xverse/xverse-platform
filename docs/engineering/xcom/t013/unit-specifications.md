# T013 Unit Specifications — Immutable Core Value, Contract, Policy, and Diagnostic Units

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T013 (capability 007, slice `T-CORE`) |
| Stage / role | plan → unit specifications (pre-code) |
| Revision | 1 |
| Baseline revision | `863f11ac990c1ce178a0f9d8eb2489e4a5243fe7` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Accepted unit design | `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-001`–`005`) |
| Classification | Public-safe engineering work product |

These unit specifications elaborate, without weakening, the accepted T010 unit design for
`XCOM-DU-001` (value and payload view), `XCOM-DU-002` (contract and logical identity), `XCOM-DU-003`
(item identity, origin, time, and correlation), `XCOM-DU-004` (diagnostics and deterministic ordering),
and `XCOM-DU-005` (result, outcome, and core type aggregate). `XCOM-DU-002` is recorded as T013 source
per `tasks.md`/`XCOM-CMP-004` even though `t010/unit-design.json` attributes it to T012 (T013-GAP-01);
T013 does not rewrite that register.

## 2. Unit inventory

| Unit (T013) | Accepted unit | Component | Kind | Language | Path(s) | Change |
| --- | --- | --- | --- | --- | --- | --- |
| `T013-U-VALUE` | `XCOM-DU-001` | `T13-CMP-VALUE` | data-plane | cpp | `value.hpp`, `value.cpp` | re-verified unchanged |
| `T013-U-CONTRACT` | `XCOM-DU-002` | `T13-CMP-CONTRACT` | data-plane | cpp | `contract.hpp`, `contract.cpp` | extended (policy) |
| `T013-U-ITEM` | `XCOM-DU-003` | `T13-CMP-ITEM` | data-plane | cpp | `item.hpp`, `item.cpp` | re-verified unchanged |
| `T013-U-DIAG` | `XCOM-DU-004` | `T13-CMP-DIAG` | data-plane | cpp | `diagnostic.hpp`, `diagnostic.cpp` | extended (policy phase/code) |
| `T013-U-RESULT` | `XCOM-DU-005` | `T13-CMP-RESULT` | data-plane | cpp | `result.hpp` | re-verified unchanged |
| `T013-U-POLICY` | `XCOM-DU-002` | `T13-CMP-CONTRACT` | data-plane | cpp | `contract.hpp`, `contract.cpp` | **new** |
| `T013-U-AGG` | `XCOM-DU-005` | `T13-CMP-AGG` | data-plane | cpp | `core_types.hpp` | re-verified unchanged |

## 3. Unit specifications

### 3.1 `T013-U-VALUE` — bounded value and payload primitives

- **Interface**: `Identity::create`, `SemanticVersion::create`, `Payload::create`, `Timestamp`, and the
  internal `detail::FixedText`.
- **Behaviour**: validates and copies bounded identity/version bytes; copies bounded payload bytes;
  stores a signed timestamp magnitude with no cross-domain inference.
- **Ownership**: caller-owns-value. **Lifetime**: invocation-scoped. **Thread-safety**: immutable-value.
- **Bounds**: identity 1–128 bytes; version 1–32 bytes; payload 0–65,536 bytes; capacity fixed.
  **Overflow**: `fail-closed`.
- **Failure**: empty optional on invalid/over-bound input; `noexcept`; no allocation.
- **Doxygen**: group `xcom_core`; file block plus per-declaration tags (baseline satisfied).
- **Planned evidence**: CHK-03, CHK-05, CHK-09; NEG-01, NEG-02, NEG-03.

### 3.2 `T013-U-CONTRACT` — immutable logical contract

- **Interface**: `InteractionKind`, `EndpointDirection`, `CommunicationContractInput`,
  `CommunicationContract::create`, accessors, `to_string`.
- **Behaviour**: validates five identities/versions and one compatible interaction/direction tuple; owns
  the declared logical identity independently of realization.
- **Ownership**: platform-owns-shared. **Lifetime**: plan-scoped. **Thread-safety**: immutable-value.
- **Bounds**: fixed descriptor capacities. **Overflow**: `n/a`.
- **Failure**: `rejected` with `required_field`, `bound_exceeded`, `invalid_version`, or
  `incompatible_direction`; `noexcept`.
- **Doxygen**: group `xcom_core`; per-declaration tags (baseline satisfied).
- **Planned evidence**: CHK-03, CHK-04, CHK-08; NEG-01, NEG-02, NEG-03, NEG-04, NEG-05.

### 3.3 `T013-U-ITEM` — item identity, origin, time, and correlation

- **Interface**: `OriginKind`, `CommunicationItemInput`, `CommunicationItem::create`, accessors,
  `to_string`.
- **Behaviour**: validates eleven required identities/versions, the origin enumeration, the payload bound,
  and exact contract consistency; carries type/origin/time/correlation/causation/route/provider.
- **Ownership**: caller-owns-value. **Lifetime**: invocation-scoped. **Thread-safety**: immutable-value.
- **Bounds**: item record fixed; identifier elements fixed; payload 0–65,536 bytes.
  **Overflow**: `fail-closed`.
- **Failure**: `rejected` with `required_field`, `bound_exceeded`, `contract_mismatch`, or
  `incompatible_direction`; `noexcept`.
- **Doxygen**: group `xcom_core`; per-declaration tags (baseline satisfied).
- **Planned evidence**: CHK-03, CHK-04, CHK-09; NEG-06, NEG-07, NEG-08, NEG-09, NEG-19.

### 3.4 `T013-U-POLICY` — immutable bounded flow-policy declaration (new)

- **Interface**: `OrderingPolicy`, `ReliabilityPolicy`, `OverflowPolicy`, their `to_string` overloads,
  `FlowPolicyInput`, `FlowPolicy::create`, accessors, `operator==`.
- **Behaviour**: validates the three policy enumerations and the `deadline_ms` (0–600,000), `retry`
  (0–64), and `queue_depth` (1–65,536) ranges; preserves the declaration exactly; never substitutes a
  default and never strengthens a guarantee.
- **Ownership**: caller-owns-value. **Lifetime**: invocation-scoped. **Thread-safety**: immutable-value.
- **Bounds**: `deadline_ms` ≤ 600,000; `retry` ≤ 64; `queue_depth` ≤ 65,536 and ≥ 1; 6 fields.
  **Overflow**: `reject`.
- **Failure**: `rejected` with `XCOM-TYPE-E006` (`invalid_policy`) for any unknown enumeration or
  out-of-range field; at most six diagnostics; `noexcept`; no partial value.
- **Doxygen**: group `xcom_core`; file block plus per-declaration `@ownership`/`@lifetime`/
  `@thread_safety`/`@failure`.
- **Planned evidence**: CHK-06, CHK-07, CHK-08, CHK-12; NEG-13, NEG-14, NEG-15, NEG-16, NEG-17.

### 3.5 `T013-U-DIAG` — stable diagnostics and deterministic ordering

- **Interface**: `DiagnosticCode` (+ `invalid_policy`), `DiagnosticSeverity`, `ValidationPhase`
  (+ `policy`), `Diagnostic::create`, `DiagnosticSet::create`/`create_from_inputs`, `serialize`,
  `ordering_key`, `to_string`.
- **Behaviour**: validates bounded text and enumerations; builds the escaped `phase|severity|code|
  identity|reason|correction` key; sorts the set by that key.
- **Ownership**: caller-owns-value. **Lifetime**: invocation-scoped. **Thread-safety**: immutable-value.
- **Bounds**: identity ≤ 128; reason/correction ≤ 256; code ≤ 14; phase ≤ 23; set ≤ 32.
  **Overflow**: `n/a` (fixed-capacity, fail-closed).
- **Failure**: `rejected` for empty/over-bound/invalid input; `noexcept`; `serialize` may throw
  `std::bad_alloc`.
- **Doxygen**: group `xcom_core`; per-declaration tags plus the new code/phase.
- **Planned evidence**: CHK-07, CHK-12; NEG-10, NEG-11, NEG-12, NEG-17.

### 3.6 `T013-U-RESULT` — exclusive result value

- **Interface**: `Result<T>::success`, `failure`, `has_value`, `value`, `diagnostics`.
- **Behaviour**: holds exactly one `T` or one non-empty `DiagnosticSet`; `noexcept` copy; assignment
  deleted.
- **Ownership**: caller-owns-value. **Lifetime**: invocation-scoped. **Thread-safety**: immutable-value.
- **Bounds**: fixed by `T` and `DiagnosticSet`. **Overflow**: `n/a`.
- **Failure**: invalid states have no public constructor; factories are `noexcept`.
- **Doxygen**: group `xcom_core`; per-declaration tags (baseline satisfied).
- **Planned evidence**: CHK-03, CHK-08; NEG-18.

### 3.7 `T013-U-AGG` — public core-type aggregate

- **Interface**: `core_types.hpp` including `contract.hpp`, `diagnostic.hpp`, `item.hpp`, `result.hpp`,
  `value.hpp` (and therefore the policy value).
- **Behaviour**: exposes the immutable value model to consumers; retains no storage.
- **Ownership**: caller-owns-value (included types). **Lifetime**: per included value.
  **Thread-safety**: per included value. **Bounds/Overflow**: n/a.
- **Failure**: per included value.
- **Doxygen**: group `xcom_core` file block (baseline satisfied).
- **Planned evidence**: CHK-03; `xcom_core_types_external_consumer` compile-and-run.

## 4. Work-product units

| Unit | Artifact | Owner | Check |
| --- | --- | --- | --- |
| `T013-W01` | `docs/engineering/xcom/t013/requirements.md` | T013 | CHK-14 |
| `T013-W02` | `docs/engineering/xcom/t013/architecture.md` | T013 | CHK-14 |
| `T013-W03` | `docs/engineering/xcom/t013/detailed-design.md` | T013 | CHK-14 |
| `T013-W04` | `docs/engineering/xcom/t013/unit-specifications.md` | T013 | CHK-14 |
| `T013-W05` | `docs/engineering/xcom/t013/verification-plan.md` | T013 | CHK-14 |
| `T013-W06` | `docs/engineering/xcom/t013/implementation.md` | T013 | CHK-16 |
| `T013-W07` | `docs/engineering/xcom/t013/internal-review.json` | T013 | review gate |
| `T013-W08` | `reports/xcom-queue/t013-package.json` | T013 | package gate |

## 5. Planned tests (exact)

All cases run offline in the admitted T011/T012 build envelope. No new CTest target is added; the focused
cases extend the existing T013-owned executables, so the discovered test count is unchanged.

| CTest target | Test name | Added cases | Covers |
| --- | --- | --- | --- |
| `xcom_core_types_unit` | `xcom_core_types_unit` | `test_flow_policy_table`, `test_flow_policy_boundaries`, `test_flow_policy_immutability_and_determinism` | T013-SR-004, -006, -007, -008, -011 |
| `xcom_core_types_negative` | `xcom_core_types_negative` | `test_flow_policy_rejections`, `test_flow_policy_exact_diagnostics` | T013-SR-005, -008, -009 |
| `xcom_core_types_external_consumer` | `xcom_core_types_external_consumer` | none (must still compile and run against the public target) | T013-SR-015 |
| existing `xcom_core_types_*` | unchanged positive/negative/interaction/rvalue/concurrency cases | none | T013-SR-001, -002, -003, -010, -012 |

Case intent:

- `test_flow_policy_table`: every declared ordering/reliability/overflow value combined with in-range
  numeric fields is accepted and round-trips exactly, including the external `to_string` text.
- `test_flow_policy_boundaries`: `deadline_ms` 0 and 600,000, `retry` 0 and 64, `queue_depth` 1 and
  65,536 are accepted; values one step outside each bound are rejected with one `invalid_policy`
  diagnostic.
- `test_flow_policy_immutability_and_determinism`: copy construction leaves the source valid and
  unchanged; `operator==` distinguishes a weaker from a stronger declaration; two reordered equivalent
  invalid inputs serialize to byte-identical diagnostic sequences.
- `test_flow_policy_rejections`: an unknown `ordering`, `reliability`, or `overflow`; `deadline_ms` < 0
  and > 600,000; `retry` < 0 and > 64; `queue_depth` 0 and > 65,536 each fail closed with no value.
- `test_flow_policy_exact_diagnostics`: an input with several policy violations yields the exact, sorted
  `XCOM-TYPE-E006` phase-`policy` sequence independently of the order of the violating fields.

## 6. Requirement-to-unit-to-test traceability

| Requirement | Unit(s) | Planned test case(s) | Check(s) |
| --- | --- | --- | --- |
| T013-SR-001 | `T013-U-VALUE` | existing value/boundary cases | CHK-03, CHK-05, CHK-09 |
| T013-SR-002 | `T013-U-CONTRACT` | `test_interaction_table`, `test_invalid_direction_table` | CHK-03, CHK-04, CHK-08 |
| T013-SR-003 | `T013-U-ITEM` | `test_complete_item_after_source_destruction`, `test_item_field_boundaries` | CHK-03, CHK-04, CHK-09 |
| T013-SR-004 | `T013-U-POLICY` | `test_flow_policy_table`, `test_flow_policy_boundaries` | CHK-06, CHK-09 |
| T013-SR-005 | `T013-U-POLICY` | `test_flow_policy_rejections` | CHK-05, CHK-06, NEG-13..NEG-16 |
| T013-SR-006 | `T013-U-POLICY` | `test_flow_policy_immutability_and_determinism` | CHK-06, CHK-08 |
| T013-SR-007 | `T013-U-POLICY` | `test_flow_policy_table` (cross-read against the Profile schema) | CHK-06 |
| T013-SR-008 | `T013-U-DIAG` | `test_exact_diagnostic_set`, `test_flow_policy_exact_diagnostics` | CHK-07 |
| T013-SR-009 | `T013-U-DIAG`, `T013-U-POLICY` | `test_diagnostic_boundaries_and_codes`, `test_flow_policy_exact_diagnostics` | CHK-06, CHK-07, CHK-12 |
| T013-SR-010 | `T013-U-RESULT` | `test_rvalue_source_invariants` | CHK-03, CHK-08, NEG-18 |
| T013-SR-011 | `T013-U-VALUE`, `T013-U-POLICY`, `T013-U-DIAG` | boundary cases above | CHK-09 |
| T013-SR-012 | `T013-U-ITEM`, `T013-U-VALUE` | source inspection of `Timestamp`/`item.hpp` | CHK-04, NEG-19 |
| T013-SR-013 | all units | forbidden-API scan + offline build | CHK-10, NEG-20, NEG-25 |
| T013-SR-014 | work products | public-safety scan | CHK-11, NEG-23 |
| T013-SR-015 | `T013-U-POLICY`, all changed units | declaration inspection + documentation validator | CHK-12 |
| T013-SR-016 | work products | changed-path inspection + register validators | CHK-02, CHK-14, CHK-15, CHK-18 |
| T013-SR-017 | work products | deterministic gate | CHK-16, NEG-24 |

## 7. Scope-preservation notes

- The consolidated cross-cutting matrix (interaction kinds, capabilities, ownership, lifecycle, queue
  bounds, recovery) remains T016 (`T013-GAP-03`); T013 adds only focused cases for its own new value.
- No existing test case is removed, renamed, or weakened; additions are within the existing executables.
- `scripts/validate_xcom_core_types.py` is legacy SESN tooling in the T013-owned path set and is neither
  executed nor edited by the repository-owned workflow (`T013-LIM-05`).
