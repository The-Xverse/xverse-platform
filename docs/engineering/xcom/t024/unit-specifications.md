# T024 Unit Specifications — Test Units, Ownership, Lifetime, Thread-Safety, Bounds, and Failure Semantics

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T024 (capability 007, slice `T-OBS`) |
| Stage / role | plan → unit specifications (pre-code) |
| Revision | 1 |
| Baseline revision | `76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Accepted design units | `XCOM-DU-012` (declared observation layer), `XCOM-DU-013` (bounded observer queue, counters, and synthetic sink) |
| Classification | Public-safe engineering work product |

## 2. Unit summary

T024 adds nine **test units** to the two existing T-OBS observation executables. A unit is one matrix case
function plus any case-local helper. No production unit is added or changed.

| Unit | Case function | File | Evidence name(s) | Owning slice |
| --- | --- | --- | --- | --- |
| `T24-TS-001` | `test_observation_metadata_and_payload_view_matrix` | `tests/xcom/observation/core/unit_tests.cpp` | `metadata-only-zero-payload`, `controlled-payload-view` | T-OBS |
| `T24-TS-002` | `test_observation_ordering_matrix` | `tests/xcom/observation/core/unit_tests.cpp` | `ordering` | T-OBS |
| `T24-TS-003` | `test_observation_saturation_bound_matrix` | `tests/xcom/observation/core/unit_tests.cpp` | `saturation` | T-OBS |
| `T24-TS-004` | `test_observation_validity_interval_matrix` | `tests/xcom/observation/core/unit_tests.cpp` | `degraded-validity` | T-OBS |
| `T24-TS-005` | `test_observation_safe_detach_matrix` | `tests/xcom/observation/core/unit_tests.cpp` | `safe-detach` | T-OBS |
| `T24-TS-006` | `test_observation_normalized_record_matrix` | `tests/xcom/observation/core/unit_tests.cpp` | `metadata-only-zero-payload` (normalized record) | T-OBS |
| `T24-TS-007` | `test_observation_record_edge_value_matrix` | `tests/xcom/observation/core/unit_tests.cpp` | `controlled-payload-view` (edge values) | T-OBS |
| `T24-TS-008` | `test_observation_route_ordering_neutrality_matrix` | `tests/xcom/observation/integration/integration_tests.cpp` | `ordering`, `safe-detach` (route) | T-OBS |
| `T24-TS-009` | `test_observation_route_saturation_safe_detach_matrix` | `tests/xcom/observation/integration/integration_tests.cpp` | `saturation`, `degraded-validity`, `safe-detach` (route) | T-OBS |

All nine units are registered in the existing `main()` of their fixture; the discovered CTest count is
unchanged.

## 3. `T24-TS-001` — Metadata and payload-view matrix

- **Responsibility**: prove `metadata_only` zero-payload completeness and the `bounded_prefix`/`redacted`
  view boundary.
- **Ownership**: owns every `ObservationHub`, tap, item, and pulled record it constructs; the hub must
  outlive its handles; no view escapes a call.
- **Lifetime**: every constructed value lives for the case body; returned records are value copies.
- **Thread-safety**: single-threaded; hub operations serialize through the hub mutex.
- **Bounds**: one tap per sub-part; capacity 16; ≤ 12 items per sub-part; 0–4-byte payloads; prefix bound
  1…1024.
- **Failure semantics**: fails if any payload byte is exposed under metadata/redacted, if a
  complete/truncated/redacted/omitted state is wrong, if a schema state is not `undecoded`, if a normalized
  identity is lost, or if an out-of-bound prefix policy is accepted.
- **Requirements**: T024-SR-003, T024-SR-005, T024-SR-006.

## 4. `T24-TS-002` — Ordering matrix

- **Responsibility**: prove per-tap FIFO under drop/coalesce, coalesce replacement position, and multi-tap
  independence.
- **Ownership**: owns two hubs (one for the drop/coalesce pair, one for the multi-tap pair), each tap, item,
  and record; no view escapes.
- **Lifetime**: value copies; every record is pulled before scope end.
- **Thread-safety**: single-threaded.
- **Bounds**: capacity 4 and 2; ≤ 5 items per hub; 0–4-byte payloads.
- **Failure semantics**: fails if a retained record order differs from the table in `detailed-design.md`
  §5.3, if a coalesced replacement keeps an old position, or if pulling one tap changes another's queue.
- **Requirements**: T024-SR-007.

## 5. `T24-TS-003` — Saturation bound matrix

- **Responsibility**: prove `drop_newest` at minimum and maximum capacity, `coalesce_latest` key selection,
  `lossless_validation` pre-mutation rejection and recovery, and bounded deterministic concurrency over one
  lossless tap, with exact counters and a queue that never exceeds its declared bound.
- **Ownership**: owns each hub, tap, reservation, thread, and record; every reservation is committed,
  cancelled, or scope-cancelled; the hub outlives every reservation and joined thread.
- **Lifetime**: reservations are single-use and move-only; a value record is pulled before scope end; every
  publisher thread is joined before its hub is destroyed.
- **Thread-safety**: hub calls serialize through the hub mutex; all but the bounded concurrency sub-check are
  single-threaded, and the sub-check uses ≤ 4 threads with atomic flags, no callback, and no wall-clock wait.
- **Bounds**: capacities 1 and 16; ≤ 20 submissions; the concurrency sub-check uses ≤ 4 threads and ≤ 16
  bounded reserve/commit attempts over a capacity-4 lossless tap, repeated three times; ≤ 4-byte payloads;
  no wall-clock input.
- **Failure semantics**: fails if a queue exceeds its bound, if a loss is not counted, if the accounting
  identity fails, if lossless rejection mutates state before rejecting, if capacity does not recover, or if
  concurrent publishers lose or duplicate a claim or leave an inconsistent counter/queue state.
- **Requirements**: T024-SR-004, T024-SR-008, T024-SR-009, T024-SR-010, T024-SR-018.

## 6. `T24-TS-004` — Validity interval matrix

- **Responsibility**: prove the declared-effect → realized-status mapping, the lossless at-least-degraded
  rule, monotonicity, acknowledgement, and discard on detach/recreation.
- **Ownership**: owns each hub, tap, reservation, snapshot, and record; reservations are consumed.
- **Lifetime**: the realized status is per-interval and discarded by detach/recreation; snapshots are value
  copies.
- **Thread-safety**: single-threaded.
- **Bounds**: capacity 1; ≤ 4 items per tap; ≤ 4-byte payloads.
- **Failure semantics**: fails if the effect is not applied, if lossless is below `degraded`, if the status
  decreases without acknowledgement/detach, if `invalid` does not persist, or if recreation does not start
  `valid`.
- **Requirements**: T024-SR-011, T024-SR-012.

## 7. `T24-TS-005` — Safe-detach matrix

- **Responsibility**: prove detach/ownership semantics (`tap_busy`, `tap_closed`, foreign, stale,
  recreation, own-records-only discard).
- **Ownership**: owns each hub (including a foreign hub), tap, handle, reservation, and snapshot.
- **Lifetime**: the copied handle is valid only for its issuing hub, tap id, and current generation; a
  reservation is consumed before the hub is destroyed.
- **Thread-safety**: single-threaded.
- **Bounds**: ≤ 3 taps per hub; capacity 1–2; ≤ 2 items; ≤ 4-byte payloads.
- **Failure semantics**: fails if detach mutates another tap, if a stale/foreign/claimed/closed handle is
  handled wrongly, or if a recreated generation is not independent.
- **Requirements**: T024-SR-013.

## 8. `T24-TS-006` — Normalized-record matrix

- **Responsibility**: prove the complete, self-describing, provider-neutral normalized record for each
  family, origin, and provider outcome (`XCOM-SW-OBS-005`).
- **Ownership**: owns each hub, tap, item, and pulled record; copied records remain owned by the case.
- **Lifetime**: value copies independent of later hub mutation.
- **Thread-safety**: single-threaded.
- **Bounds**: one hub per provider outcome; capacity 16; 12 items per outcome; ≤ 4-byte payloads.
- **Failure semantics**: fails if a normalized field is lost or renamed, if a record is not a value copy,
  or if a provider-specific/address/transport accessor is required.
- **Requirements**: T024-SR-015, T024-SR-016.

## 9. `T24-TS-007` — Record edge-value matrix

- **Responsibility**: prove normalized edge values (absent sequence, distinct observation clock, zero-length
  payload, counter projection, four families).
- **Ownership**: owns each hub, tap, event, and record.
- **Lifetime**: value copies; the absent-sequence event is committed immediately.
- **Thread-safety**: single-threaded.
- **Bounds**: capacity 2; ≤ 4 items; payload 0–4 bytes.
- **Failure semantics**: fails if an absent sequence is defaulted, if clock domains are not preserved
  independently, or if the counter projection is wrong.
- **Requirements**: T024-SR-002, T024-SR-015.

## 10. `T24-TS-008` — Route ordering and neutrality matrix

- **Responsibility**: prove route `per_route_fifo` order and SC-005 neutrality across the four families and
  the blocking/removed/failed observer states.
- **Ownership**: owns each `Scenario` (lifecycle, provider, composition, handles), hub, tap, sink, item, and
  record; the hub outlives every scenario handle.
- **Lifetime**: scenario references remain valid for the case body; a sink's hub reference outlives the sink.
- **Thread-safety**: single-threaded; the composed provider and hub serialize their own operations.
- **Bounds**: queue capacity 8; ≤ 3 items per family; capacity 16/8 taps; ≤ 4-byte payloads.
- **Failure semantics**: fails if the route item count, receive order, or delivery outcome changes while an
  observer is blocked, removed, or failed, or if a detached handle still authenticates.
- **Requirements**: T024-SR-007, T024-SR-014.

## 11. `T24-TS-009` — Route saturation and safe-detach matrix

- **Responsibility**: prove route-level saturation loss counters and degraded validity while the route still
  delivers, and that a safe detach leaves the route and other taps intact.
- **Ownership**: owns each hub, `Scenario`, tap, reservation, sink, item, and record; reservations are
  consumed.
- **Lifetime**: value copies; every reservation is committed, cancelled, or scope-cancelled.
- **Thread-safety**: single-threaded.
- **Bounds**: queue capacity 8; capacities 1 and 4; ≤ 4 submissions; ≤ 4-byte payloads.
- **Failure semantics**: fails if saturation changes the route count/order/outcome, if lossless rejection
  mutates the route before rejecting, if the degraded status is not visible, or if detach affects another
  tap or the route.
- **Requirements**: T024-SR-010, T024-SR-013, T024-SR-014.

## 12. Concurrency/resource bound summary

| Aspect | Bound | Units |
| --- | --- | --- |
| Threads | ≤ 4 | TS-003 (bounded competing lossless reservations with atomic flags) |
| Taps per hub | ≤ 8 | TS-001…TS-005, TS-009 |
| Records per tap | ≤ 16 | TS-003 |
| Items per case | ≤ 64 | all (largest loop 20) |
| Payload bytes | ≤ 4 | all |
| Prefix bound | 1…1024 | TS-001 |
| Wall-clock | none | all |
| Callbacks | none | all |

## 13. Traceability

| Unit | T024 requirements | Accepted software req | Spec / success anchor | Design units |
| --- | --- | --- | --- | --- |
| `T24-TS-001` | T024-SR-003, T024-SR-005, T024-SR-006 | `XCOM-SW-OBS-001`, `-002`, `-005` | FR-011, FR-012, SC-003 | `XCOM-DU-012`, `XCOM-DU-013` |
| `T24-TS-002` | T024-SR-007 | `XCOM-SW-OBS-003` | FR-013, SC-004 | `XCOM-DU-013` |
| `T24-TS-003` | T024-SR-004, T024-SR-008…-010, T024-SR-018 | `XCOM-SW-OBS-003`, `-004`, `-005` | FR-013, FR-014, SC-003, SC-004 | `XCOM-DU-013` |
| `T24-TS-004` | T024-SR-011, T024-SR-012 | `XCOM-SW-OBS-003`, `-004` | FR-013, FR-014, SC-004 | `XCOM-DU-013` |
| `T24-TS-005` | T024-SR-013 | `XCOM-SW-OBS-004` | FR-009, FR-014, SC-005 | `XCOM-DU-013` |
| `T24-TS-006` | T024-SR-015, T024-SR-016 | `XCOM-SW-OBS-005` | FR-023 | `XCOM-DU-012`, `XCOM-DU-013` |
| `T24-TS-007` | T024-SR-002, T024-SR-015 | `XCOM-SW-OBS-005` | FR-023 | `XCOM-DU-012`, `XCOM-DU-013` |
| `T24-TS-008` | T024-SR-007, T024-SR-014 | `XCOM-SW-OBS-003`, `-004` | FR-013, FR-014, SC-004, SC-005 | `XCOM-DU-013`, `XCOM-CMP-006` |
| `T24-TS-009` | T024-SR-010, T024-SR-013, T024-SR-014 | `XCOM-SW-OBS-003`, `-004` | FR-013, FR-014, SC-004, SC-005 | `XCOM-DU-013`, `XCOM-CMP-006` |

## 14. Bounds and open items

- The `payloadAccess: allow-listed` identity allow-list, a redaction profile, and any decoder/schema status
  beyond `PayloadSchemaState::undecoded` remain unimplemented and partial (`T024-GAP-01`); no unit tests an
  unrealized behaviour.
- The disabled-tap performance benchmark and its `SC-008` threshold remain T036 (`T024-GAP-02`); no unit
  claims `disabled-tap-performance`.
- The separate-process synthetic client and tool-gateway observation path remain T032/T033 (`T024-GAP-03`).
- Strict declaration-level Doxygen remains `DOX-GAP-01` (T011/T037).
- `T024-OPEN-02` records the choice to continue the hand-rolled observation fixture style rather than add a
  separate test target; a later unification must preserve every T024 case name or replace it with an
  equivalent stronger case.
