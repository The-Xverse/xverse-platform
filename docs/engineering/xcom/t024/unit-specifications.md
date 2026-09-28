# T024 Unit Specifications — Test Units, Ownership, Lifetime, Thread-Safety, Bounds, and Failure Semantics

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T024 (capability 007, slice `T-OBS`) |
| Stage / role | plan → unit specifications (pre-code) |
| Revision | 1 (observation acceptance matrix) |
| Repair revision | 3 — terminal review R-01 governance repair (see §15) |
| Baseline revision | `76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6` |
| Repair baseline | `d50bb48f45e422b8a7018710b1ac50cdadbcf8ed` |
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

## 15. Revision 3 — R-01 governance-repair units (`T24-R01-TS-###`)

These units verify the repair. Each is a repository-owned, offline, single-threaded check driven by an
existing validator; none is a runtime component, and none changes a Revision 1 case. "Lifetime" is a
single deterministic invocation; "thread-safety" is not applicable because no shared mutable state or
concurrency exists.

### 15.1 `T24-R01-TS-001` — Register delivered-reconciliation unit

- **Responsibility**: the T007 register records T012–T016/T021–T024 as `delivered` at exactly the pinned
  candidate revision with a non-empty pending-acceptance reason.
- **Owning paths**: `docs/engineering/xcom/task-ownership.json`, `scripts/validate_xcom_task_ownership.py`.
- **Positive check**: `--verify` exits `0`; `--check-human` exits `0`.
- **Negative fixtures (validator self-test)**: `delivered` with `revision == null`; `delivered` with a
  short/wrong revision; `delivered` with an empty reason; a required task reverted to `unreconciled`; a
  `delivered` task relabelled `accepted`. Each must fail `GATE_INVALID` (`exit 8`) with no partial pass.
- **Bounds**: input ≤ 1 MiB; no network/subprocess/clock.
- **Failure semantics**: any mismatch fails closed with the classified exit code; the candidate tree is
  never written.

### 15.2 `T24-R01-TS-002` — Deterministic projection unit

- **Responsibility**: `docs/engineering/xcom/task-ownership.md` is the byte-exact projection of the JSON.
- **Owning paths**: `docs/engineering/xcom/task-ownership.{json,md}`.
- **Check**: `--check-human` exits `0`; a tampered projection fails `DETERMINISM_INVALID` (`exit 9`).
- **Bounds**: total input ≤ 4 MiB.

### 15.3 `T24-R01-TS-003` — Requirements traceability delivered-coverage unit

- **Responsibility**: a requirement whose owning task is `delivered` stays `partial` with a recorded
  reconciliation reason and is never `implemented`.
- **Owning paths**: `docs/engineering/xcom/t008/requirements-register.json`,
  `scripts/validate_xcom_requirements_traceability.py`.
- **Check**: `--verify` and `--check-human` exit `0`; self-test `NEG-17` (drop the reason on
  `XCOM-SW-CORE-001`, owning task T012) fails `MATURITY_INVALID` (`exit 8`).
- **Bounds**: input bounded by the validator's file limits.

### 15.4 `T24-R01-TS-004` — Accepted predecessor preservation unit

- **Responsibility**: the accepted T008/T009/T010 artifacts are byte-unchanged by the repair.
- **Owning paths**: `docs/engineering/xcom/t008/**`, `docs/engineering/xcom/t009/**`,
  `docs/engineering/xcom/t010/**`.
- **Check**: `git diff --name-only <baseline> -- docs/engineering/xcom/t00{8,9}` and
  `docs/engineering/xcom/t010` is empty.
- **Negative fixture**: none. Predecessor preservation is a repository-inventory check (`git diff
  --name-only`) with no validator exit class; a non-empty inventory fails R01-CHK-05/R01-CHK-13 at the
  deterministic gate, and `R01-NEG-08` (public safety, `exit 10`) is scoped to the task-ownership register
  inputs and does not apply here.

### 15.5 `T24-R01-TS-005` — Analysis disposition unit

- **Responsibility**: A12 records the delivered-pending-acceptance disposition and a dated successor note.
- **Owning paths**: `specs/007-xcom-core/analysis.md`.
- **Check**: R01-CHK-04 inspection plus a public-safety scan; no `implemented` or accepted claim appears.

### 15.6 `T24-R01-TS-006` — Governance regression test unit

- **Responsibility**: pin the repaired delivered state, the byte-stable projection, the checked capability
  ledger, and the analysis disposition so a regression to the old checkbox-open reason fails locally.
- **Owning paths**: `tests/test_xcom_task_ownership_reconciliation.py`.
- **Check**: `pytest tests/test_xcom_task_ownership_reconciliation.py` collects seven passing cases; the
  T024 deterministic gate requires the `tests/` path change; R01-CHK-15; R01-NEG-09.
- **Bounds**: offline, deterministic, single-threaded; loads the validator as a module; starts no child
  process; writes no file.
- **Failure semantics**: any restored `unreconciled`/checkbox-open state, wrong revision, empty reason,
  accepted relabel, projection drift, unchecked ledger entry, or missing analysis disposition fails.

### 15.7 Traceability (repair units)

| Unit | Requirements | Checks |
| --- | --- | --- |
| `T24-R01-TS-001` | `T024-R01-SR-001`, `T024-R01-SR-004` | R01-CHK-01..03, R01-NEG-01..05 |
| `T24-R01-TS-002` | `T024-R01-SR-001` | R01-CHK-03, R01-NEG-06 |
| `T24-R01-TS-003` | `T024-R01-SR-004`, `T024-R01-SR-005` | R01-CHK-07..08, R01-NEG-07 |
| `T24-R01-TS-004` | `T024-R01-SR-003`, `T024-R01-SR-007` | R01-CHK-05, R01-CHK-13 |
| `T24-R01-TS-005` | `T024-R01-SR-002`, `T024-R01-SR-005` | R01-CHK-04, R01-CHK-09 |
| `T24-R01-TS-006` | `T024-R01-SR-009` | R01-CHK-15; R01-NEG-09 |
