# T022 Unit Specifications — Bounded Retention, Validity, Reporting, and Interval Units

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T022 (capability 007, slice `T-OBS`) |
| Stage / role | plan → unit specifications (pre-code) |
| Revision | 1 |
| Baseline revision | `7be8b9718e42e58bb1a05a486ff62e520f94567c` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Accepted unit design | `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-013` bounded observer queue, counters, and synthetic sink, owning tasks T022/T023; `XCOM-DU-012` observation record and payload-view policy, owning task T021) |
| Accepted test unit | `XCOM-T-OBS` (`tests/xcom/observation/`, `docs/engineering/xcom/t008/traceability-matrix.{json,md}`) |
| Classification | Public-safe engineering work product |

These unit specifications elaborate, without weakening, the accepted T010 unit design for `XCOM-DU-013`
and the `XCOM-DU-012` surface that T022 consumes read-only. Where the T008 register attributes
`XCOM-SW-OBS-002`/`-003` to T022 and the T008 matrix allocates them to the `XCOM-DU-OBS-BASELINE` locator
while `XCOM-DU-013` links `XCOM-SW-OBS-003`/`-004`, T022 implements the bounded queue/validity half and
leaves the payload-view half unchanged (§7 of `requirements.md`); the registers are not rewritten and no
maturity is promoted.

## 2. Unit inventory

| Unit (T022) | Accepted unit | Component | Kind | Language | Path(s) | Change |
| --- | --- | --- | --- | --- | --- | --- |
| `T022-U-BEST-EFFORT` | `XCOM-DU-013` | `T22-CMP-BEST-EFFORT` | boundary | cpp | `observation.hpp`, `observation.cpp` | extended (validity raise on drop/coalesce) |
| `T022-U-LOSSLESS` | `XCOM-DU-013` | `T22-CMP-LOSSLESS` | boundary | cpp | `observation.hpp`, `observation.cpp` | extended (validity raise on backpressure) |
| `T022-U-VALIDITY` | `XCOM-DU-013` | `T22-CMP-VALIDITY` | data | cpp | `observation.hpp`, `observation.cpp` | new (status vocabulary + raising rule) |
| `T022-U-REPORT` | `XCOM-DU-013` | `T22-CMP-REPORT` | data | cpp | `observation.hpp`, `observation.cpp` | extended (trailing `validity_state`, derived marker) |
| `T022-U-AUTHORITY` | `XCOM-DU-013` | `T22-CMP-AUTHORITY` | boundary | cpp | `observation.hpp`, `observation.cpp` | extended (acknowledge interval rule) |
| `T022-U-PAYLOAD` | `XCOM-DU-012` (T021) | `T22-CMP-PAYLOAD` | boundary | cpp | `observation.hpp`, `observation.cpp` | re-verified unchanged |
| `T022-U-DECLARATION` | `XCOM-DU-012` (T021) | `T22-CMP-DECLARATION` | boundary | cpp | `observation.hpp`, `observation.cpp` | re-verified unchanged |
| `T022-U-SINK` | `XCOM-DU-013` (T023) | `T22-CMP-SINK` | test-fixture | cpp | `observation.hpp`, `observation.cpp` | re-verified unchanged |
| `T022-U-TEST` | `XCOM-T-OBS` | `T22-WP` | test | cpp | `tests/xcom/observation/core/unit_tests.cpp` | extended (focused cases) |

## 3. Unit specifications

### 3.1 `T022-U-BEST-EFFORT` — bounded `drop_newest` and `coalesce_latest`

- **Interface**: `ObservationHub::retain` (private) reached through `reserve`/`commit`; no public signature
  changes.
- **Behaviour**: keeps every tap queue within its declared capacity; `drop_newest` drops the new record and
  increments `dropped`; `coalesce_latest` replaces the newest queued record with a matching logical key and
  increments `coalesced`, or drops the new record and increments `dropped`; retained records keep FIFO
  order; a best-effort loss never blocks, delays, reorders, or mutates the normal route.
- **Ownership**: platform-owns-shared. **Lifetime**: tap-scoped. **Thread-safety**: under the hub mutex.
- **Bounds**: declared capacity 1–16; coalescing scan ≤ capacity. **Overflow**: `drop-newest` / `coalesce`.
- **Failure**: best-effort loss reports the stable `accepted` outcome with no record and no route effect;
  `noexcept`.
- **Doxygen**: group `xcom_obs`; the retention rules re-documented with the validity-raise note.
- **Planned evidence**: CHK-05, CHK-06, CHK-13; `test_drop_newest_bounded_loss`,
  `test_coalesce_latest_key_selection`, `test_best_effort_overflow` (preserved).

### 3.2 `T022-U-LOSSLESS` — explicit `lossless_validation`

- **Interface**: `ObservationHub::reserve`/`commit`/`cancel`, the `ObservationReservation` value, and the
  private `retain` over-capacity branch (a **non-constructible defensive guard**; see `verification-plan.md`
  §5 NEG-05); no public signature changes.
- **Behaviour**: claims exact capacity before provider mutation; returns `observation_backpressure` before
  provider mutation when capacity is unavailable; increments `backpressure_rejections`; consumes or releases
  a reservation exactly once; emits no normal-route item and retains no record on rejection.
- **Ownership**: platform-owns-shared for slot state; the reservation owns single-use claim authority.
  **Lifetime**: the issuing hub must outlive the reservation. **Thread-safety**: hub operations serialized;
  a reservation is single-owner state.
- **Bounds**: per-tap declared capacity 1–16; claim count bounded by the matching taps. **Overflow**:
  `lossless-backpressure`.
- **Failure**: `observation_backpressure` / `invalid_reservation` / `invalid_argument` with no unrelated
  mutation; `noexcept`.
- **Doxygen**: group `xcom_obs`; the pre-dispatch and validity-raise rules documented.
- **Planned evidence**: CHK-07, CHK-08; `test_lossless_backpressure_pre_dispatch`,
  `test_lossless_reservations` and `test_competing_reservation_interleaving` (preserved).

### 3.3 `T022-U-VALIDITY` — realized declared-effect status (new)

- **Interface**: `ObservationValidityState` (`valid`, `degraded`, `invalid`; ordered) and
  `to_string(ObservationValidityState)`; the private `raise_realized_validity(TapSlot&, bool)` helper.
- **Behaviour**: raises the realized status on every matching loss per the declared `validityEffect`
  (`none` → no change for best-effort loss; `degrade_on_loss` → ≥ `degraded`; `invalidate_on_loss` →
  `invalid`), with a lossless backpressure realizing at least `degraded`; monotonic within an interval;
  never lowered except by acknowledgement (`degraded` → `valid`) or detach/recreation.
- **Ownership**: owned by the hub slot. **Lifetime**: interval-scoped to the tap until detach/recreation.
  **Thread-safety**: updated only under the hub mutex; the vocabulary functions are pure and `noexcept`.
- **Bounds**: one enumerator per tap; three declared values. **Overflow**: `fail-closed` (no status raised
  without a matching loss).
- **Failure**: `to_string` returns stable text and `noexcept`; an out-of-range value never arises from the
  accepted declarations.
- **Doxygen**: group `xcom_obs`; the vocabulary documented with ownership/lifetime/thread-safety/failure.
- **Planned evidence**: CHK-09, CHK-10, CHK-11; `test_validity_effect_on_best_effort_loss`,
  `test_validity_effect_on_lossless_backpressure`, `test_validity_state_vocabulary`.

### 3.4 `T022-U-REPORT` — realized-status reporting

- **Interface**: `ObservationSnapshot` (accepted fields plus the new trailing `validity_state`),
  `ObservationStatus`, `ObservationOutcome`, `to_string(ObservationOutcome)` (unchanged).
- **Behaviour**: `snapshot()` returns `queued`, `accepted`, `dropped`, `coalesced`,
  `backpressure_rejections`, the `experiment_validity_degraded` compatibility projection, the declared
  identity/effect, and the realized `validity_state` for an authenticated handle, and `std::nullopt`
  otherwise.
- **Ownership**: caller-owns-value. **Lifetime**: invocation-scoped. **Thread-safety**: immutable-value.
- **Bounds**: fixed counter fields, one declared identity, one declared effect, one realized status.
  **Overflow**: `n/a`.
- **Failure**: absent snapshot for an invalid, foreign, stale, or closed handle; no new outcome value.
- **Doxygen**: group `xcom_obs`; the new field and the derived marker documented.
- **Planned evidence**: CHK-11; `test_validity_state_vocabulary`, `test_acknowledge_closes_validity_interval`,
  `test_snapshot_reports_declaration` (preserved).

### 3.5 `T022-U-AUTHORITY` — exact handle and interval authority

- **Interface**: `ObservationTapHandle` (unchanged surface) and `ObservationHub::acknowledge`/`detach`.
- **Behaviour**: `acknowledge` closes the interval for the exact current handle — `backpressure_rejections`
  → 0 and a `degraded` status → `valid`, while an `invalid` status persists; a foreign/stale/closed handle
  returns `invalid_tap_handle` with no reset. `detach` keeps its accepted duplicate-close/`tap_busy`/stale
  semantics and discards the realized status with the slot.
- **Ownership**: caller-owns-value (handle); the hub exclusively owns slot state.
  **Lifetime**: the hub must outlive every issued handle. **Thread-safety**: serialized by one mutex.
- **Bounds**: 8 fixed slots; generation increments per reuse. **Overflow**: `tap_capacity_exhausted`.
- **Failure**: the accepted stable outcomes only; declared identity and realized status confer no authority.
- **Doxygen**: group `xcom_obs`; the interval rule documented on `acknowledge`.
- **Planned evidence**: CHK-10, NEG-10, NEG-11; `test_acknowledge_closes_validity_interval`,
  `test_exact_tap_handles` (preserved).

### 3.6 `T022-U-PAYLOAD` — payload view policy (T021-owned; read-only for T022)

- **Interface**: `ObservationPayloadMode`, `ObservationTapSpec` payload accessors, `PayloadViewState`,
  `PayloadSchemaState` (unchanged).
- **Behaviour**: `metadata_only` → `omitted`, zero bytes; `bounded_prefix` → `complete`/`truncated`, at most
  the declared bound; `redacted` → `redacted`, zero bytes; schema state `undecoded`; **no** identity
  allow-list and no decoder is added.
- **Ownership**: caller-owns-value. **Lifetime**: invocation-scoped. **Thread-safety**: immutable-value.
- **Bounds**: 0 or 1–1024 payload bytes. **Overflow**: `fail-closed` at declaration.
- **Failure**: invalid mode/bound → no policy value (T021 scope).
- **Doxygen**: group `xcom_obs`; unchanged baseline documentation retained.
- **Planned evidence**: CHK-14, NEG-19; `test_metadata_only`, `test_controlled_payload_states` (preserved).

### 3.7 `T022-U-DECLARATION` — declared observation layer (T021-owned; read-only for T022)

- **Interface**: `ObservationFilter`, `ObservationTapSpec`, `ObservationRecord`, `ObservationEvent`
  (unchanged).
- **Behaviour**: filter matching, declared identity/route, payload/overflow/validity declaration, and the
  immutable record/counter projection are unchanged; T022 adds only the retention-time validity raise.
- **Ownership**: caller-owns-value / platform-owns-shared. **Lifetime**: invocation-scoped. **Thread-safety**:
  immutable-value.
- **Bounds**: fixed identities and 1024-byte record buffer. **Overflow**: `fail-closed`.
- **Failure**: unchanged stable outcomes.
- **Doxygen**: group `xcom_obs`; unchanged baseline documentation retained.
- **Planned evidence**: CHK-14; `test_record_self_description`, `test_record_counter_projection` (preserved).

### 3.8 `T022-U-SINK` — synthetic pull sink (T023-owned; read-only for T022)

- **Interface**: `SyntheticObservationSink` constructor, `connect`, `disconnect`, `pull`, `connected`.
- **Behaviour**: pulls through the hub with the copied exact handle; a local disconnect yields
  `sink_disconnected` and never detaches, blocks, or mutates the tap.
- **Ownership**: caller-owns-value (sink state); the hub is referenced non-owning.
  **Lifetime**: the hub must outlive the sink. **Thread-safety**: serialized through the hub.
- **Bounds**: none beyond the hub's. **Overflow**: `n/a`.
- **Failure**: `sink_disconnected` / underlying hub status; no route effect.
- **Doxygen**: group `xcom_obs`; unchanged baseline documentation retained.
- **Planned evidence**: CHK-12; `test_synthetic_sink_concurrency` (preserved).

### 3.9 `T022-U-TEST` — T-OBS focused retention/validity fixture update

- **Interface / behaviour**: extends the existing observation unit fixture with the focused T022 cases; no
  existing assertion is weakened and the integration fixtures are unchanged.
- **Ownership**: test-owned fixtures. **Lifetime**: process-scoped. **Thread-safety**: the reused
  concurrency fixtures use ≤ 4 threads with joined, finite loops.
- **Bounds**: finite item counts, 4-byte synthetic payloads, ≤ 16 record slots. **Overflow**: `n/a`.
- **Failure**: a failed expectation prints to `stderr` and returns a non-zero exit status; no external I/O.
- **Doxygen**: file block plus `@brief` on every new helper and case.
- **Planned evidence**: all executable checks in `verification-plan.md` §4.

## 4. Work-product units

| Unit | Artifact | Owner | Check |
| --- | --- | --- | --- |
| `T022-W01` | `docs/engineering/xcom/t022/requirements.md` | T022 | CHK-22 |
| `T022-W02` | `docs/engineering/xcom/t022/architecture.md` | T022 | CHK-22 |
| `T022-W03` | `docs/engineering/xcom/t022/detailed-design.md` | T022 | CHK-22 |
| `T022-W04` | `docs/engineering/xcom/t022/unit-specifications.md` | T022 | CHK-22 |
| `T022-W05` | `docs/engineering/xcom/t022/verification-plan.md` | T022 | CHK-22 |
| `T022-W06` | `docs/engineering/xcom/t022/implementation.md` | T022 | CHK-21 |
| `T022-W07` | `docs/engineering/xcom/t022/internal-review.json` | T022 | review gate |
| `T022-W08` | `reports/xcom-queue/t022-package.json` | T022 | package gate |

## 5. Planned tests (exact)

No new CTest target, test name, or label is added. The focused cases extend the existing T-OBS executable
`xverse_xcom_observation_unit_tests` (registered as `xcom_observation_unit`), so the discovered test count
is unchanged from the baseline 306. `xcom_observation_integration` and
`xcom_observation_disabled_benchmark` keep their exact names, labels, commands, and expected results and
are not edited.

| CTest target | Test name | Added cases | Existing cases (preserved) |
| --- | --- | --- | --- |
| `xcom_observation_unit` | `xcom_observation_unit` | `test_drop_newest_bounded_loss`, `test_coalesce_latest_key_selection`, `test_lossless_backpressure_pre_dispatch`, `test_validity_effect_on_best_effort_loss`, `test_validity_effect_on_lossless_backpressure`, `test_validity_state_vocabulary`, `test_acknowledge_closes_validity_interval` | `test_values_filters_and_versions`, `test_filter_declared_constraints`, `test_declared_tap_binding`, `test_declared_tap_rejections`, `test_validity_effect_vocabulary`, `test_payload_policy_bounds`, `test_record_self_description`, `test_record_counter_projection`, `test_snapshot_reports_declaration`, `test_repeated_declaration_capacity`, `test_metadata_only`, `test_controlled_payload_states`, `test_best_effort_overflow`, `test_lossless_reservations`, `test_competing_reservation_interleaving`, `test_exact_tap_handles`, `test_synthetic_sink_concurrency` |
| `xcom_observation_integration` | `xcom_observation_integration` | none (not edited) | every accepted case unchanged |
| `xcom_observation_disabled_benchmark` | `xcom_observation_disabled_benchmark` | none (not edited) | unchanged |

Case intent:

- `test_drop_newest_bounded_loss` — a `drop_newest` tap with capacity 2 receives three matching items; the
  first two are retained in FIFO order with `queued == 2`/`accepted == 2`, the third is dropped with
  `dropped == 1` and no new record, `queued` stays 2, and the two retained records keep their original
  sequences.
- `test_coalesce_latest_key_selection` — a `coalesce_latest` tap with capacity 2 receives items on two
  logical routes: a repeat of the newest matching key replaces that record (`coalesced` + 1, new sequence,
  `queued` unchanged) while a third distinct route with no matching key is dropped (`dropped` + 1, unrelated
  FIFO order preserved).
- `test_lossless_backpressure_pre_dispatch` — a `lossless_validation` tap with capacity 1 claims one
  exact reservation; a competing `reserve` returns `observation_backpressure` with no reservation and no
  record, `backpressure_rejections == 1`, and `experiment_validity_degraded == true`; cancelling the claim
  restores capacity and a subsequent reservation commits exactly one record.
- `test_validity_effect_on_best_effort_loss` — three `drop_newest` taps declaring `none`, `degrade_on_loss`,
  and `invalidate_on_loss` each lose a matching record at capacity 1; the snapshots report `valid`,
  `degraded`, and `invalid` respectively, with `experiment_validity_degraded` false/true/true, and the same
  status progression holds for a `coalesce_latest` replacement.
- `test_validity_effect_on_lossless_backpressure` — three `lossless_validation` taps declaring `none`,
  `degrade_on_loss`, and `invalidate_on_loss` each reject a matching submission at capacity 1; the realized
  status is `degraded`/`degraded`/`invalid` respectively, so a `none` lossless backpressure still degrades
  exactly as accepted.
- `test_validity_state_vocabulary` — `to_string` returns `"valid"`, `"degraded"`, and `"invalid"` exactly;
  the ordering `valid < degraded < invalid` holds; a snapshot for a no-loss tap reports `valid` with
  `experiment_validity_degraded == false`, and a snapshot after a loss reports the realized status with
  `experiment_validity_degraded == (validity_state != valid)`.
- `test_acknowledge_closes_validity_interval` — acknowledgement of a `degraded` interval resets
  `backpressure_rejections` to 0 and the status to `valid`; an `invalid` status persists across
  acknowledgement and a further loss does not lower it; a foreign or stale handle acknowledgement returns
  `invalid_tap_handle` and leaves the real tap's counters and status untouched.

## 6. Requirement-to-unit-to-test traceability

| Requirement | Unit(s) | Planned test case(s) | Check(s) |
| --- | --- | --- | --- |
| T022-SR-001 | `T022-U-BEST-EFFORT` | `test_drop_newest_bounded_loss` | CHK-05, NEG-01, NEG-13 |
| T022-SR-002 | `T022-U-BEST-EFFORT` | `test_coalesce_latest_key_selection` | CHK-06, NEG-02, NEG-03 |
| T022-SR-003 | `T022-U-LOSSLESS` | `test_lossless_backpressure_pre_dispatch` | CHK-07, CHK-08, NEG-04, NEG-12 (NEG-05 is a non-constructible defensive guard) |
| T022-SR-004 | `T022-U-BEST-EFFORT` | `test_drop_newest_bounded_loss`, `test_coalesce_latest_key_selection` | CHK-13, NEG-14 |
| T022-SR-005 | `T022-U-VALIDITY` | `test_validity_effect_on_best_effort_loss` | CHK-09, NEG-06…NEG-08 |
| T022-SR-006 | `T022-U-VALIDITY` | `test_validity_effect_on_lossless_backpressure` | CHK-08, CHK-10, NEG-04 |
| T022-SR-007 | `T022-U-VALIDITY`, `T022-U-REPORT` | `test_validity_state_vocabulary` | CHK-09, CHK-11, NEG-12 |
| T022-SR-008 | `T022-U-AUTHORITY` | `test_acknowledge_closes_validity_interval` | CHK-10, NEG-10, NEG-11 |
| T022-SR-009 | `T022-U-VALIDITY`, `T022-U-SINK` | `test_synthetic_sink_concurrency`, `test_competing_reservation_interleaving` (preserved) | CHK-12, CHK-16, NEG-15 |
| T022-SR-010 | `T022-U-VALIDITY`, `T022-U-REPORT` | constants inspection plus bounds cases | CHK-13, CHK-18 |
| T022-SR-011 | all units | forbidden-API scan plus the offline build | CHK-17, NEG-16 |
| T022-SR-012 | work products and tests | public-safety scan | CHK-18, NEG-17 |
| T022-SR-013 | all changed units | declaration inspection plus the documentation validator | CHK-19 |
| T022-SR-014 | work products and tests | changed-path and test-name comparison; preserved-marker regression | CHK-02, CHK-14, CHK-20, NEG-18 |
| T022-SR-015 | work products | deterministic gate | CHK-21 |
| T022-SR-016 | work products | register validators plus attribution inspection | CHK-20, CHK-22 |
| T022-SR-017 | `T022-U-PAYLOAD`, `T022-U-DECLARATION` | payload-boundary difference inspection | CHK-14, NEG-19 |

## 7. Scope-preservation notes

- The synthetic sink and observer isolation (T023), the broad saturation/ordering/degraded-validity/
  safe-detach matrix (T024), the payload identity allow-list/decoder, and the disabled-tap performance
  benchmark (T036) remain with their owning tasks (`T022-GAP-01`…`-04`); T022 adds only the bounded
  retention, applied validity effect, and interval rule.
- No existing test case is removed, renamed, or weakened. The integration fixtures are not edited because
  they declare the default `none` effect; their lossless cases already expect the accepted degraded marker.
- `tests/xcom/observation/integration/disabled_tap_benchmark.cpp` is not edited; its paired-baseline seam
  and threshold are governed by T036.
- `scripts/validate_xcom_observation.py` is legacy SESN-era tooling in the T-OBS path set and is neither
  executed nor edited by the repository-owned workflow (`T022-LIM-06`).
- No CMake file changes: the existing `xverse::xcom_observation` target compiles the changed unit and the
  existing `xcom_observation_unit` executable compiles the changed fixture.
