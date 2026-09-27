# T021 Unit Specifications — Observation Filter, Policy, Record, Reporting, and Authority Units

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T021 (capability 007, slice `T-OBS`) |
| Stage / role | plan → unit specifications (pre-code) |
| Revision | 1 |
| Baseline revision | `8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Accepted unit design | `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-012` observation record and payload-view policy, owning task T021; `XCOM-DU-013` bounded observer queue, counters, and synthetic sink, owning tasks T022/T023) |
| Accepted test unit | `XCOM-T-OBS` (`tests/xcom/observation/`, `docs/engineering/xcom/t008/traceability-matrix.{json,md}`) |
| Classification | Public-safe engineering work product |

These unit specifications elaborate, without weakening, the accepted T010 unit design for `XCOM-DU-012`
and the `XCOM-DU-013` surface that T021 observes read-only. Where `XCOM-DU-012` links
`XCOM-SW-OBS-002`/`-005` to the T021-owned unit while the T008 register attributes those software
requirements to T022/T024, T021 implements only the declaration and projection half (§8.4 of
`requirements.md`); the register is not rewritten and no maturity is promoted.

## 2. Unit inventory

| Unit (T021) | Accepted unit | Component | Kind | Language | Path(s) | Change |
| --- | --- | --- | --- | --- | --- | --- |
| `T021-U-FILTER` | `XCOM-DU-012` | `T21-CMP-FILTER` | boundary | cpp | `observation.hpp`, `observation.cpp` | extended (declared accessors) |
| `T021-U-SPEC` | `XCOM-DU-012` | `T21-CMP-SPEC` | boundary | cpp | `observation.hpp`, `observation.cpp` | extended (declared point + validity effect) |
| `T021-U-RECORD` | `XCOM-DU-012` | `T21-CMP-RECORD` | data | cpp | `observation.hpp`, `observation.cpp` | extended (declared identity + counters) |
| `T021-U-REPORT` | `XCOM-DU-012` | `T21-CMP-REPORT` | data | cpp | `observation.hpp`, `observation.cpp` | extended (declaration reporting) |
| `T021-U-AUTHORITY` | `XCOM-DU-012` | `T21-CMP-AUTHORITY` | boundary | cpp | `observation.hpp`, `observation.cpp` | re-verified unchanged |
| `T021-U-RETENTION` | `XCOM-DU-013` (T022) | `T21-CMP-RETENTION` | data | cpp | `observation.hpp`, `observation.cpp` | re-verified unchanged (record stamping only) |
| `T021-U-SINK` | `XCOM-DU-013` (T023) | `T21-CMP-SINK` | test-fixture | cpp | `observation.hpp`, `observation.cpp` | re-verified unchanged |
| `T021-U-TEST` | `XCOM-T-OBS` | `T21-WP` | test | cpp | `tests/xcom/observation/core/unit_tests.cpp`, `tests/xcom/observation/integration/{test_support.hpp,integration_tests.cpp}` | extended (focused cases + declaration update) |

## 3. Unit specifications

### 3.1 `T021-U-FILTER` — declared exact-field filter

- **Interface**: `ObservationFilterInput` (unchanged) and `ObservationFilter::create`, `matches` plus the
  new `contract_id`, `interface_id`, `endpoint_id`, `route_id`, `provider_id`, `interaction_kind`,
  `origin` accessors.
- **Behaviour**: validates and owns every non-empty identity constraint; the accessors return the exact
  declared constraint or `std::nullopt`; `matches()` is unchanged and true only when every declared
  constraint is satisfied.
- **Ownership**: caller-owns-value (the filter owns its constraints). **Lifetime**: invocation-scoped for
  the value; accessor views are valid while the filter lives. **Thread-safety**: immutable-value
  (concurrent const access safe).
- **Bounds**: ≤ 5 identities of 1–128 bytes each; two optional enumerations. **Overflow**: `fail-closed`.
- **Failure**: `std::nullopt` for a malformed or over-bound non-empty constraint; `noexcept`; no allocation
  beyond the owned fixed identity storage.
- **Doxygen**: group `xcom_obs`; file block plus `@brief`/`@ownership`/`@lifetime`/`@thread_safety`/
  `@failure` on the new accessors.
- **Planned evidence**: CHK-06, CHK-21; `test_filter_declared_constraints`,
  `test_values_filters_and_versions`.

### 3.2 `T021-U-SPEC` — immutable declared tap policy

- **Interface**: `ObservationPayloadMode`, `ObservationOverflowPolicy` (unchanged); new
  `ObservationValidityEffect` and `to_string(ObservationValidityEffect)`; `ObservationTapSpecInput` with the
  new mandatory `tap_id` and new `validity_effect`; `ObservationTapSpec::create` with the new
  `declared_tap_id()`, `declared_route_point()`, and `validity_effect()` accessors.
- **Behaviour**: validates the single accepted contract version, the declared observation-point identity,
  the filter, the payload mode and bound, the record capacity, the overflow policy, and the declared
  validity effect in the fixed order of `detailed-design.md` §4.1; preserves every declared value exactly;
  never substitutes a default and never strengthens a guarantee.
- **Ownership**: caller-owns-value. **Lifetime**: invocation-scoped. **Thread-safety**: immutable-value;
  construction is call-local with no shared state.
- **Bounds**: declared identity 1–128 bytes; record capacity 1–16; prefix bound 0 or 1–1024; 8 fixed
  fields. **Overflow**: `fail-closed` (no polluting or partial declaration).
- **Failure**: `std::nullopt` for any violation; `noexcept`; no diagnostic object and no new outcome code.
- **Doxygen**: group `xcom_obs`; the new vocabulary and every new accessor documented.
- **Planned evidence**: CHK-03, CHK-04, CHK-05, CHK-07, CHK-08, CHK-09, CHK-15; `test_declared_tap_binding`,
  `test_declared_tap_rejections`, `test_validity_effect_vocabulary`, `test_payload_policy_bounds`.

### 3.3 `T021-U-RECORD` — immutable self-describing normalized record

- **Interface**: `ObservationEvent` (unchanged) and `ObservationRecord` with the new `tap_id()` and
  `counters()` accessors and the new `ObservationRecordCounters` projection, in addition to every accepted
  accessor.
- **Behaviour**: copies the authenticated tap's declared identity and the post-retention counter values
  into the record; keeps the policy-bounded payload view and `PayloadSchemaState::undecoded`; a record is
  created only by `ObservationHub`.
- **Ownership**: platform-owns-shared (the platform builds the record and hands out value-owned copies).
  **Lifetime**: bounded to the returned record value and the observation scope. **Thread-safety**:
  immutable-value; copies are safe to read concurrently.
- **Bounds**: fixed record storage plus a 1024-byte payload buffer and four counter values; no dynamic
  allocation. **Overflow**: `fail-closed` (a record beyond the declared bound is never built).
- **Failure**: no public constructor; an invalid observation clock domain or an unmatched reservation
  yields no record.
- **Doxygen**: group `xcom_obs`; the new projection documented with ownership/lifetime tags.
- **Planned evidence**: CHK-10, CHK-11; `test_record_self_description`, `test_record_counter_projection`.

### 3.4 `T021-U-REPORT` — declared snapshot and stable outcomes

- **Interface**: `ObservationStatus`, `ObservationOutcome`, `to_string(ObservationOutcome)` (unchanged) and
  `ObservationSnapshot` with the new trailing `declared_tap_id` and `validity_effect` fields.
- **Behaviour**: `snapshot()` returns the declared identity, declared validity effect, `queued`, `accepted`,
  `dropped`, `coalesced`, `backpressure_rejections`, and `experiment_validity_degraded` for an authenticated
  handle, and `std::nullopt` otherwise.
- **Ownership**: caller-owns-value. **Lifetime**: invocation-scoped. **Thread-safety**: immutable-value.
- **Bounds**: fixed counter fields plus one identity. **Overflow**: `n/a`.
- **Failure**: absent snapshot for an invalid, foreign, stale, or closed handle; no new outcome value.
- **Doxygen**: group `xcom_obs`; the two new fields documented.
- **Planned evidence**: CHK-12, CHK-13; `test_snapshot_reports_declaration`.

### 3.5 `T021-U-AUTHORITY` — exact generation-bound tap authority (re-verified unchanged)

- **Interface**: `ObservationTapHandle` (hub instance, tap slot, generation; copy-constructible and
  non-assignable) and `ObservationHub::attach`/`poll`/`snapshot`/`acknowledge`/`detach`.
- **Behaviour**: attach claims the first free slot and advances its generation; authentication requires the
  exact hub instance, slot, generation, and an occupied slot; foreign/stale/closed handles are rejected;
  duplicate close reports `tap_closed`; an in-flight claim reports `tap_busy` without mutation.
- **Ownership**: caller-owns-value (handle); the hub exclusively owns slot state.
  **Lifetime**: the hub must outlive every issued handle. **Thread-safety**: hub operations serialized by
  one mutex; the handle is an immutable value.
- **Bounds**: 8 fixed slots; generation increments per reuse. **Overflow**: `tap_capacity_exhausted` with no
  mutation.
- **Failure**: the accepted stable outcomes only; the declared tap identity confers no authority.
- **Doxygen**: group `xcom_obs`; unchanged baseline documentation retained.
- **Planned evidence**: CHK-13; `test_exact_tap_handles`, `test_repeated_declaration_capacity`,
  NEG-11…NEG-13.

### 3.6 `T021-U-RETENTION` — bounded retention policy (T022-owned; read-only for T021)

- **Interface**: `ObservationHub::reserve`/`commit` and the private `retain` path.
- **Behaviour**: `drop_newest` drops the new record; `coalesce_latest` replaces the newest record with a
  matching logical key or drops the new record; `lossless_validation` rejects before provider mutation when
  capacity is unavailable; counters and the degraded marker update exactly as accepted. T021 adds only the
  record stamping of already-maintained counters and the declared identity.
- **Ownership**: platform-owns-shared. **Lifetime**: tap-scoped. **Thread-safety**: under the hub mutex.
- **Bounds**: per-tap declared capacity 1–16. **Overflow**: the declared policies.
- **Failure**: unchanged stable outcomes.
- **Doxygen**: group `xcom_obs`; unchanged baseline documentation retained.
- **Planned evidence**: CHK-11, CHK-16, CHK-21; `test_best_effort_overflow`, `test_lossless_reservations`,
  `test_record_counter_projection`.

### 3.7 `T021-U-SINK` — synthetic pull sink (T023-owned; read-only for T021)

- **Interface**: `SyntheticObservationSink` constructor, `connect`, `disconnect`, `pull`, `connected`.
- **Behaviour**: pulls through the hub with the copied exact handle; a local disconnect yields
  `sink_disconnected` and never detaches, blocks, or mutates the tap; records are owned by the return value.
- **Ownership**: caller-owns-value (sink state); the hub is referenced non-owning.
  **Lifetime**: the hub must outlive the sink. **Thread-safety**: serialized through the hub; one sink is
  not designed for concurrent connect/disconnect.
- **Bounds**: none beyond the hub's. **Overflow**: `n/a`.
- **Failure**: `sink_disconnected` / the underlying hub status; no route effect.
- **Doxygen**: group `xcom_obs`; unchanged baseline documentation retained.
- **Planned evidence**: CHK-16; `test_synthetic_sink_concurrency`.

### 3.8 `T021-U-TEST` — T-OBS observation fixture update

- **Interface / behaviour**: extends the existing observation unit fixture with the focused T021 cases and
  declares a valid observation point in the shared fixture helpers so every existing T022/T023 case still
  compiles and behaves identically.
- **Ownership**: test-owned fixtures. **Lifetime**: process-scoped. **Thread-safety**: the concurrency
  fixture uses ≤ 4 threads with joined, finite loops.
- **Bounds**: finite item counts, 4-byte synthetic payloads, ≤ 64 iterations. **Overflow**: `n/a`.
- **Failure**: a failed expectation prints to `stderr` and returns a non-zero exit status; no external I/O.
- **Doxygen**: file block plus `@brief` on every new helper and case.
- **Planned evidence**: all executable checks in `verification-plan.md` §4.

## 4. Work-product units

| Unit | Artifact | Owner | Check |
| --- | --- | --- | --- |
| `T021-W01` | `docs/engineering/xcom/t021/requirements.md` | T021 | CHK-23 |
| `T021-W02` | `docs/engineering/xcom/t021/architecture.md` | T021 | CHK-23 |
| `T021-W03` | `docs/engineering/xcom/t021/detailed-design.md` | T021 | CHK-23 |
| `T021-W04` | `docs/engineering/xcom/t021/unit-specifications.md` | T021 | CHK-23 |
| `T021-W05` | `docs/engineering/xcom/t021/verification-plan.md` | T021 | CHK-23 |
| `T021-W06` | `docs/engineering/xcom/t021/implementation.md` | T021 | CHK-22 |
| `T021-W07` | `docs/engineering/xcom/t021/internal-review.json` | T021 | review gate |
| `T021-W08` | `reports/xcom-queue/t021-package.json` | T021 | package gate |

## 5. Planned tests (exact)

No new CTest target, test name, or label is added. The focused cases extend the existing T-OBS
executable `xverse_xcom_observation_unit_tests` (registered as `xcom_observation_unit`), so the discovered
test count is unchanged. `xcom_observation_integration` and `xcom_observation_disabled_benchmark` keep
their exact names, labels, commands, and expected results.

| CTest target | Test name | Added cases | Existing cases (preserved) |
| --- | --- | --- | --- |
| `xcom_observation_unit` | `xcom_observation_unit` | `test_filter_declared_constraints`, `test_declared_tap_binding`, `test_declared_tap_rejections`, `test_validity_effect_vocabulary`, `test_payload_policy_bounds`, `test_record_self_description`, `test_record_counter_projection`, `test_snapshot_reports_declaration`, `test_repeated_declaration_capacity` | `test_values_filters_and_versions` (declared-point update only), `test_metadata_only`, `test_controlled_payload_states`, `test_best_effort_overflow`, `test_lossless_reservations`, `test_competing_reservation_interleaving`, `test_exact_tap_handles`, `test_synthetic_sink_concurrency` |
| `xcom_observation_integration` | `xcom_observation_integration` | none | every accepted case, with the shared `make_tap_spec` helper declaring a valid observation point |
| `xcom_observation_disabled_benchmark` | `xcom_observation_disabled_benchmark` | none (not edited) | unchanged |

Case intent:

- `test_filter_declared_constraints` — a filter declaring all seven constraints returns each exact declared
  value from the new accessors; a route-only filter returns `std::nullopt` from the other six; `matches()`
  results for the same inputs are unchanged.
- `test_declared_tap_binding` — a declaration with a valid `tap_id`, a route-constrained filter, a payload
  mode/bound, a capacity, an overflow policy, and a declared validity effect is accepted; `declared_tap_id()`
  is the exact declared identity; `declared_route_point()` equals the filter's declared route identity;
  `validity_effect()` and every accepted accessor round-trip exactly.
- `test_declared_tap_rejections` — each individually injected defect fails closed with `std::nullopt` and no
  partial value: empty `tap_id`; `tap_id` of 129 bytes; `tap_id` containing an ASCII control byte; `tap_id`
  with leading/trailing whitespace; wrong contract version; unknown payload mode; unknown overflow policy;
  unknown validity effect; capacity 0; capacity 17; prefix bound 0 with `bounded_prefix`; prefix bound 1025;
  non-zero bound with `metadata_only`; malformed non-empty filter identity.
- `test_validity_effect_vocabulary` — `to_string` returns `"none"`, `"degrade-on-loss"`,
  `"invalidate-on-loss"` exactly; all three are accepted by `create`; an out-of-range value is rejected.
- `test_payload_policy_bounds` — prefix bounds 1 and 1024 and record capacities 1 and 16 are accepted and
  round-trip; a zero-byte source under `bounded_prefix` yields `complete` with zero bytes; a source equal to
  the bound yields `complete` and one byte larger yields `truncated` with exactly the bound bytes.
- `test_record_self_description` — a pulled record reports the declared `tap_id()` of its producing tap and
  every accepted baseline field (contract, interface, endpoint, schema identity/version, interaction kind,
  origin, source/observation timestamp, source/observation clock domain, sequence, correlation, causation,
  route, provider, source payload size, provider outcome, payload view state, payload schema state,
  payload bytes) unchanged.
- `test_record_counter_projection` — with capacity 1 the first retained record reports
  `{queued=1, accepted=1, dropped=0, coalesced=0}`, a second `drop_newest` submission produces no record and
  `dropped == 1` in the snapshot; with capacity 2 and `coalesce_latest` a matching-key replacement reports
  `coalesced == 1` with `queued` preserved; a lossless backpressure rejection produces no record.
- `test_snapshot_reports_declaration` — the snapshot reports the declared `tap_id`, the declared
  `validity_effect`, and unchanged counters for the exact handle, and no snapshot exists for a foreign or
  stale handle.
- `test_repeated_declaration_capacity` — two taps declaring the same observation point attach into distinct
  slots with distinct handles and generations, report the same declared identity, keep independent counters,
  and detaching one leaves the other active (multiple observers of one declared point).

## 6. Requirement-to-unit-to-test traceability

| Requirement | Unit(s) | Planned test case(s) | Check(s) |
| --- | --- | --- | --- |
| T021-SR-001 | `T021-U-SPEC` | `test_declared_tap_binding`, `test_declared_tap_rejections` | CHK-03, NEG-01 |
| T021-SR-002 | `T021-U-SPEC` | `test_declared_tap_binding`, `test_declared_tap_rejections` | CHK-04, CHK-05, NEG-02…NEG-04 |
| T021-SR-003 | `T021-U-SPEC` | `test_declared_tap_binding` | CHK-07, NEG-05 |
| T021-SR-004 | `T021-U-FILTER` | `test_filter_declared_constraints`, `test_values_filters_and_versions` | CHK-06, CHK-21 |
| T021-SR-005 | `T021-U-SPEC` | `test_payload_policy_bounds`, `test_declared_tap_rejections` | CHK-09, CHK-15, NEG-06…NEG-08 |
| T021-SR-006 | `T021-U-SPEC` | `test_declared_tap_rejections` | CHK-08, CHK-21, NEG-09 |
| T021-SR-007 | `T021-U-SPEC` | `test_validity_effect_vocabulary`, `test_declared_tap_rejections` | CHK-08, NEG-10 |
| T021-SR-008 | `T021-U-RECORD` | `test_record_self_description` | CHK-10 |
| T021-SR-009 | `T021-U-RECORD` | `test_record_counter_projection` | CHK-11 |
| T021-SR-010 | `T021-U-RECORD`, `T021-U-REPORT` | `test_record_self_description`, `test_snapshot_reports_declaration` | CHK-10, CHK-21, NEG-19 |
| T021-SR-011 | `T021-U-AUTHORITY` | `test_exact_tap_handles`, `test_repeated_declaration_capacity` | CHK-13, NEG-11…NEG-13 |
| T021-SR-012 | `T021-U-REPORT` | `test_snapshot_reports_declaration` | CHK-12, NEG-11 |
| T021-SR-013 | `T021-U-AUTHORITY` | `test_repeated_declaration_capacity` | CHK-13 |
| T021-SR-014 | `T021-U-SPEC`, `T021-U-FILTER` | `test_declared_tap_binding` (concurrent construction probe) | CHK-14, CHK-16 |
| T021-SR-015 | `T021-U-SPEC`, `T021-U-RECORD` | bounds cases above plus constant inspection | CHK-14, CHK-18 |
| T021-SR-016 | `T021-U-RETENTION`, `T021-U-SINK` | `test_synthetic_sink_concurrency`, `test_competing_reservation_interleaving` | CHK-16, NEG-19 |
| T021-SR-017 | all units | forbidden-API scan plus the offline build | CHK-17, NEG-20, NEG-21 |
| T021-SR-018 | work products and tests | public-safety scan | CHK-18, NEG-22 |
| T021-SR-019 | all changed units | declaration inspection plus the documentation validator | CHK-19 |
| T021-SR-020 | work products and tests | changed-path and test-name comparison | CHK-02, CHK-21, NEG-23, NEG-24 |
| T021-SR-021 | work products | deterministic gate | CHK-22 |
| T021-SR-022 | work products | register validators plus attribution inspection | CHK-20, CHK-23 |

## 7. Scope-preservation notes

- Retention policy, the synthetic sink, and the broad saturation/ordering/degraded-validity/safe-detach
  matrix remain T022/T023/T024 (`T021-GAP-01`…`-04`); T021 adds declaration, projection, and reporting only.
- No existing test case is removed, renamed, or weakened. The only existing-test edits are the declaration
  update required by the new mandatory policy field, plus the shared integration helper; every original
  assertion, target, label, and expected result is preserved.
- `tests/xcom/observation/integration/disabled_tap_benchmark.cpp` is not edited; its paired-baseline seam
  and threshold are governed by T036.
- `scripts/validate_xcom_observation.py` is legacy SESN-era tooling in the T-OBS path set and is neither
  executed nor edited by the repository-owned workflow (`T021-LIM-06`).
- No CMake file changes: the existing `xverse::xcom_observation` target compiles the changed unit and the
  existing `xcom_observation_unit` executable compiles the changed fixture.
