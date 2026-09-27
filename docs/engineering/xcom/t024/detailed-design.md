# T024 Detailed Design — Case Matrix, Expected Values, Fixtures, Bounds, and Failure Semantics

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T024 (capability 007, slice `T-OBS`) |
| Stage / role | plan → detailed design (pre-code) |
| Revision | 1 (observation acceptance matrix) |
| Repair revision | 3 — terminal review R-01 governance repair (see §11) |
| Baseline revision | `76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6` |
| Repair baseline | `d50bb48f45e422b8a7018710b1ac50cdadbcf8ed` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed design | accepted `src/xverse/xcom/include/xverse/xcom/observation.hpp` and `src/xverse/xcom/src/observation.cpp` (read-only); `docs/engineering/xcom/t021/detailed-design.md`, `t022/detailed-design.md`, `t023/detailed-design.md` |
| Classification | Public-safe engineering work product |

This design describes the **tests only**. It fixes the case inventory, the fixture strategy, the exact
expected values, the bounds, and the failure semantics so that the implementation stage realizes the
matrix without inventing behaviour. It changes no production unit, contract, schema, register, ADR, or
another task's artifact.

## 2. Design principles

1. **Test, do not fix.** Every case asserts the accepted behaviour of the observation boundary as it
   exists at the baseline. If a case requires a production change, the requirement is misread and the
   discrepancy is reported instead.
2. **Additive only.** New cases are appended to the two existing observation fixtures and registered in
   their existing `main()`; no existing case, assertion, expected value, or helper is modified or renamed.
3. **Explicit expected values.** Each case asserts concrete numbers (counts, byte sizes, states, ids) or
   concrete invariants; no case accepts "some value" or "no crash".
4. **Bounded and deterministic.** Every thread, tap, record, iteration, and payload is finite; no case
   depends on wall-clock timing, sleeps, or unbounded waits.
5. **Boundary-first.** Where a behaviour is a rule, the case exercises both sides of the boundary
   (minimum/maximum capacity, `source < / == / > bound`, before/after detach, before/after
   acknowledgement).
6. **No duplication.** Where an accepted predecessor case already proves a focused behaviour
   (`test_metadata_only`, `test_controlled_payload_states`, `test_drop_newest_bounded_loss`,
   `test_validity_effect_on_best_effort_loss`, `test_exact_tap_handles`, …), the T024 case adds the
   missing cross-product, boundary, or route-level dimension; it does not restate the predecessor case.

## 3. Fixture design

### 3.1 Reused helpers (unchanged)

- `tests/xcom/observation/core/unit_tests.cpp` already provides `make_item(...)`, `make_contract(...)`,
  `make_spec(...)`, and `emit(hub, item, sequence, provider_outcome)` in its anonymous namespace. T024
  reuses these helpers unchanged.
- `tests/xcom/observation/integration/integration_tests.cpp` already provides the owned
  `Scenario` fixture and `make_tap_spec(...)` through `test_support.hpp`. T024 reuses `Scenario`
  unchanged and builds any extra policy inline through `ObservationTapSpec::create` so that
  `test_support.hpp` is **not** edited.
- No new production header, no new test target, no new fixture header is introduced.

### 3.2 New case-local helpers (planned, additive)

| Helper (local to the fixture) | Purpose |
| --- | --- |
| `make_effect_spec(mode, bound, capacity, policy, tap_id, effect)` | Builds an `ObservationTapSpec` with an explicit validity effect; complements the existing `make_spec` (which fixes `none`). |
| `emit_absent_sequence(hub, item)` | Commits an `ObservationEvent` with `sequence = std::nullopt` for the edge-value case. |
| `poll_all(hub, handle, count)` | Pulls up to `count` records and returns them for FIFO assertions (a bounded loop). |

These helpers live inside the edited fixtures' anonymous namespaces; they carry `@brief` documentation in
the existing file style.

## 4. Case inventory

Nine new cases: seven in `tests/xcom/observation/core/unit_tests.cpp`, two in
`tests/xcom/observation/integration/integration_tests.cpp`. Each is registered in the existing `main()`.

### 4.1 Unit cases

#### `T24-TS-001` — `test_observation_metadata_and_payload_view_matrix`

Covers `metadata-only-zero-payload` and `controlled-payload-view`.

- **Part A — metadata completeness.** Attach one `metadata_only` tap (bound 0, capacity 16, tap id
  `tap.t024.metadata`) and emit `4 families × 3 source sizes {0,1,4}` = 12 synthetic items with increasing
  sequence `1…12`. Before pulling, assert `snapshot->accepted == 12 && snapshot->queued == 12`. Pull all
  twelve and, for each, assert: `payload_bytes().empty()`, `payload_view_state() == omitted`,
  `payload_schema_state() == undecoded`, `source_payload_size()` equals the emitted size, `interaction_kind()`
  equals the emitted family, `origin() == component`, `contract_id()/interface_id()/endpoint_id()/schema_id()`
  round-trip, `source_timestamp()` and `observation_timestamp()` equal the emitted values,
  `source_clock_domain()`/`observation_clock_domain()` equal the emitted domains, `sequence()` equals the
  emitted sequence, `correlation_id()/causation_id()/route_id()/provider_id()` round-trip,
  `provider_outcome() == accepted`, and `tap_id().value() == "tap.t024.metadata"`. This proves "100 % of
  emitted records" for the matched batch (SC-003).
- **Part B — prefix boundary table.** For each row of §5.1, build a fresh hub + tap and emit one item of
  the stated source size; assert the visible view exactly. Also assert the minimum bound (1) and the
  maximum bound (`kMaximumObservedPayloadBytes`) produce a valid policy.
- **Part C — redacted/metadata views.** Assert a `redacted` tap exposes zero bytes with
  `PayloadViewState::redacted` and a `metadata_only` tap exposes zero bytes with `omitted`, both with
  `undecoded` and the full `source_payload_size`.
- **Part D — rejected policy bounds.** Assert `ObservationTapSpec::create` returns no value for a prefix
  bound of zero and for a prefix bound of `kMaximumObservedPayloadBytes + 1`, and for a non-zero bound on a
  non-prefix mode.

#### `T24-TS-002` — `test_observation_ordering_matrix`

Covers `ordering`.

- Attach, on one hub, `tap.t024.drop` (`drop_newest`, capacity 4) and `tap.t024.coalesce`
  (`coalesce_latest`, capacity 4), both matching the same route. Emit the same `alpha` item with sequences
  `1…5`.
  - `tap.t024.drop`: `accepted == 4`, `dropped == 1`, `queued == 4`; pulls return sequences `1,2,3,4`
    (FIFO, oldest retained).
  - `tap.t024.coalesce`: `accepted == 4`, `coalesced == 1`, `queued == 4`; pulls return sequences
    `1,2,3,5` (the newest matching record replaced sequence 4 and moved to the newest position).
- **Multi-tap independence.** On a fresh hub, attach `tap.t024.a` and `tap.t024.b` (both `metadata_only`,
  capacity 2). Emit 3 items. Assert both snapshots report `accepted == 2 && queued == 2`. Pull `a` twice →
  sequences `1,2`; assert `b`'s snapshot still reports `queued == 2`; pull `b` twice → sequences `1,2`.
- **Strictly increasing.** For the drop tap above, assert the pulled sequence list is strictly increasing.

#### `T24-TS-003` — `test_observation_saturation_bound_matrix`

Covers `saturation`.

- **Drop-newest minimum.** `drop_newest`, capacity 1, tap `tap.t024.drop1`; emit sequences `1…5`.
  Assert `accepted == 1`, `dropped == 4`, `queued == 1`; pull → sequence 1; next poll → `no_record`;
  assert `accepted + dropped == 5`.
- **Drop-newest maximum.** `drop_newest`, capacity `kMaximumObservationRecordsPerTap` (16), tap
  `tap.t024.drop16`; emit sequences `1…20`. Assert `accepted == 16`, `dropped == 4`, `queued == 16`;
  pull 16 records → sequences `1…16` in order; next poll → `no_record`; `accepted + dropped == 20`.
- **Coalesce key selection.** `coalesce_latest`, capacity 1, tap `tap.t024.coal1`; emit `alpha` seq 1,
  `beta` seq 2, `alpha` seq 3, `gamma` seq 4. Assert `accepted == 1`, `dropped == 2`, `coalesced == 1`,
  `queued == 1`; pull → `alpha` seq 3.
- **Lossless rejection and recovery.** `lossless_validation`, capacity 1, tap `tap.t024.lossless`; claim a
  reservation for `alpha`, then a second reserve → `observation_backpressure`, `backpressure_rejections == 1`,
  `queued == 0` and the first claim's route/queue untouched; cancel the claim; reserve and commit → accepted
  with `queued == 1`; pull → the committed sequence.
- **Bound invariant.** After each emission step assert the tap's `queued <= declared capacity`.
- **Bounded deterministic concurrency (`T024-SR-018`).** On one fresh `lossless_validation` tap of
  capacity 4, four publisher threads each perform four reserve/commit attempts (16 bounded attempts,
  ≤ 4 threads, atomic flags). Because a lossless claim is taken before provider mutation and every
  successful claim is committed, exactly four commits and twelve `observation_backpressure`
  rejections occur independently of thread interleaving; after `join` assert the atomic commit/reject
  counts, `accepted == 4`, `queued == 4`, `dropped == 0`, `coalesced == 0`,
  `backpressure_rejections == 12`, degraded validity, and four distinct retained sequences (no lost or
  duplicated claim). Repeat the whole block three times and require the same observable outcome. No
  callback and no wall-clock wait is used.

#### `T24-TS-004` — `test_observation_validity_interval_matrix`

Covers `degraded-validity`.

- **Effect table (best-effort drop, capacity 1).** For each effect and expected state of §5.2: emit two
  items, then assert `snapshot->validity_state == expected` and
  `snapshot->experiment_validity_degraded == (expected != valid)` and `dropped == 1`.
- **Monotonicity and acknowledgement.** With `degrade_on_loss`: after the loss assert `degraded`; read the
  snapshot again and assert still `degraded` (never lowered without acknowledgement); `acknowledge(handle)`
  → `accepted` and `snapshot->validity_state == valid`, `backpressure_rejections == 0`,
  `experiment_validity_degraded == false`; emit two more items → `degraded` again.
- **Invalid persistence.** With `invalidate_on_loss`: after the loss assert `invalid`; `acknowledge` →
  `accepted` but `snapshot->validity_state == invalid` (persists) and a further loss keeps `invalid`.
- **Discard on safe detach/recreation.** Start from a `degraded` interval; `detach` → `accepted`; re-attach
  the same tap id; assert the new generation's `snapshot->validity_state == valid`, `accepted == 0`,
  `queued == 0`, `dropped == 0`, and the old handle no longer authenticates.
- **Lossless at-least-degraded.** With `none` and `lossless_validation` (capacity 1), a second reservation
  while the first is held → `observation_backpressure`, `validity_state == degraded` (required loss raises
  at least `degraded`), `backpressure_rejections == 1`.

#### `T24-TS-005` — `test_observation_safe_detach_matrix`

Covers `safe-detach`.

- **Own-records-only discard.** Hub with `tap.t024.detach.a` and `tap.t024.detach.b` (both `metadata_only`,
  capacity 2). Emit 2 items; `detach(a)` → `accepted`; assert `snapshot(a)` absent; `poll(a)` →
  `invalid_tap_handle`; `snapshot(b)` → `queued == 2`, `accepted == 2`, `dropped == 0`, still authenticates;
  `poll(b)` → sequence 1.
- **Duplicate close.** `detach(a)` again with the closed exact handle → `tap_closed`.
- **Claimed tap.** `tap.t024.detach.c` (`lossless_validation`, capacity 1); hold a reservation; `detach(c)`
  → `tap_busy` and the retained state unchanged; `cancel` the reservation; `detach(c)` → `accepted`.
- **Foreign handle.** `foreign_hub` with an attached tap; this hub's `detach(foreign_handle)` →
  `invalid_tap_handle`; `snapshot(foreign_handle)` still absent on this hub and the foreign slot unchanged.
- **Stale recreation.** Re-attach `tap.t024.detach.a`; assert the new handle's generation is greater and its
  snapshot is `valid` with zero counters; `detach` with the old `a` handle → `invalid_tap_handle`.
- **In-flight after recreation.** No case leaves an active claim at scope end (every reservation is
  committed, cancelled, or scope-cancelled).

#### `T24-TS-006` — `test_observation_normalized_record_matrix`

Covers `XCOM-SW-OBS-005`.

- Attach one `metadata_only` tap (capacity 16, tap id `tap.t024.norm`) matching everything. Emit one item
  for each combination of `4 families × 3 origins {component, replay, validation_tool} × 3 provider outcomes
  {not_attempted, accepted, rejected}` = 36 items is above the capacity; therefore use three taps
  (`tap.t024.norm.a/.b/.c`, capacity 16 each) split by family pair, or loop one outcome at a time with a
  fresh hub per outcome and 12 items each (`4 × 3`). The design chooses **fresh hub per provider outcome,
  12 items, capacity 16**.
- For each record assert the complete normalized field set of §4.1 Part A plus
  `provider_outcome() == <outcome>` and `payload_view_state() == omitted`; assert `queued == 12`,
  `accepted == 12`.
- **Value ownership.** Copy one pulled `ObservationRecord`; emit further items; assert the copy's
  `sequence()`, `route_id()`, `source_payload_size()`, and `counters()` are unchanged.
- **Provider neutrality.** Assert no accessor exposes a provider-specific, address, transport, or
  domain-specific value (compile-time surface check, no such accessor exists).

#### `T24-TS-007` — `test_observation_record_edge_value_matrix`

Covers normalized edge values (complements `T24-TS-006`).

- **Absent sequence.** Commit an event with `sequence = std::nullopt`; assert `record.sequence()` has no
  value while every other field is preserved.
- **Distinct observation clock.** Commit an event whose `observation_timestamp` and
  `observation_clock_domain` differ from the item's source values; assert both are preserved independently
  and not compared.
- **Zero-length payload.** Emit a 0-byte item; assert `source_payload_size() == 0`,
  `payload_view_state() == omitted` under `metadata_only`.
- **Counter projection.** Assert the pulled record's `counters()` equals the retention-time projection
  (`queued == 1`, `accepted == 1`, `dropped == 0`, `coalesced == 0`) for a fresh tap, and that a
  coalesced replacement reports `coalesced == 1`.
- **All four families.** Assert one record per family with the family preserved.

### 4.2 Integration cases

#### `T24-TS-008` — `test_observation_route_ordering_neutrality_matrix`

Covers `ordering` and route neutrality (SC-005) across the four families.

- **Four-family route order.** For each of the four families, build a fresh `Scenario(suffix, family, 8,
  &hub)` with a matching `metadata_only` tap (capacity 16). Submit 3 items; assert the route
  `queued_items() == 3` and each submission outcome is `accepted`; pull the tap → sequences `1,2,3`; receive
  from the route → sequences `1,2,3` (per-route FIFO unchanged by observation).
- **Blocking observer.** New scenario + `metadata_only` tap (capacity 8); a `SyntheticObservationSink` is
  connected but never pulls; submit 4 items; assert the route `queued_items() == 4`, the tap snapshot
  `queued == 4`, the sink counters stay zero, and the route receive order is `1,2,3,4`.
- **Observer removed.** `detach` the tap; submit 2 more items; assert the route accepts them and the receive
  order continues `5,6`; assert `poll(stale_handle)` → `invalid_tap_handle`.
- **Observer failed.** A second sink bound to the detached tap; `pull()` → `invalid_tap_handle` with
  `counters().failed == 1`; assert the route count/order are unchanged.

#### `T24-TS-009` — `test_observation_route_saturation_safe_detach_matrix`

Covers `saturation`, `degraded-validity`, and `safe-detach` at the route boundary.

- **Route unaffected by saturation.** Hub with `tap.t024.route.drop` (`drop_newest`, capacity 1) and
  `tap.t024.route.aux` (`metadata_only`, capacity 4). Scenario `message_event`, queue 8; submit 4 items.
  Assert: drop tap `accepted == 1`, `dropped == 3`, `queued == 1`; aux tap `accepted == 4`, `queued == 4`;
  route `queued_items() == 4`; receive order `1,2,3,4`.
- **Lossless pre-mutation rejection at the route.** Fresh hub + `tap.t024.route.lossless`
  (`lossless_validation`, capacity 1); submit item 1 → `accepted`; submit item 2 → `observation_backpressure`
  with diagnostic `XCOM-PROV-E029`; assert the route `queued_items() == 1` (no mutation before rejection)
  and the snapshot `experiment_validity_degraded == true`, `backpressure_rejections == 1`; drain and
  acknowledge; submit item 2 again → `accepted`.
- **Safe detach leaves the route intact.** `detach(drop_handle)` → `accepted`; assert the aux tap snapshot
  is unchanged (`queued == 4`), the route still holds 4 items, the receive order is `1,2,3,4`, and
  `poll(drop_handle)` → `invalid_tap_handle`.
- **Claimed detach.** Hold a reservation on the lossless tap; `detach` → `tap_busy`; cancel; `detach` →
  `accepted`; assert the route item count unchanged.

## 5. Expected-value tables

### 5.1 Prefix view boundary

Source sizes use the 4-byte fixture `{s0,s1,s2,s3}` truncated to the requested size. "Lead" means the
leading bytes are byte-equal to the source prefix.

| Mode | Bound | Source size | `payload_bytes().size()` | `payload_view_state()` | `payload_schema_state()` |
| --- | --- | --- | --- | --- | --- |
| `bounded_prefix` | 1 | 0 | 0 | `complete` | `undecoded` |
| `bounded_prefix` | 1 | 1 | 1 | `complete` | `undecoded` |
| `bounded_prefix` | 1 | 4 | 1 | `truncated` | `undecoded` |
| `bounded_prefix` | 3 | 4 | 3 | `truncated` | `undecoded` |
| `bounded_prefix` | 4 | 4 | 4 | `complete` | `undecoded` |
| `bounded_prefix` | `kMaximumObservedPayloadBytes` (1024) | 4 | 4 | `complete` | `undecoded` |
| `redacted` | 0 | 4 | 0 | `redacted` | `undecoded` |
| `metadata_only` | 0 | 4 | 0 | `omitted` | `undecoded` |

In every row, `source_payload_size()` equals the source size and every visible byte equals the
corresponding leading source byte.

### 5.2 Validity effect → realized status

| Declared effect | Best-effort drop/coalesce loss | Lossless-validation backpressure | `experiment_validity_degraded` |
| --- | --- | --- | --- |
| `none` | `valid` | `degraded` (required loss) | `state != valid` |
| `degrade_on_loss` | `degraded` | `degraded` | `state != valid` |
| `invalidate_on_loss` | `invalid` | `invalid` | `state != valid` |

### 5.3 Saturation counters

| Policy | Capacity | Submissions | `accepted` | `dropped` | `coalesced` | `queued` | Pulled sequences |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `drop_newest` | 1 | 5 | 1 | 4 | 0 | 1 | `1` |
| `drop_newest` | 16 | 20 | 16 | 4 | 0 | 16 | `1…16` |
| `coalesce_latest` | 4 | 5 (`alpha` 1–5) | 4 | 0 | 1 | 4 | `1,2,3,5` |
| `coalesce_latest` | 1 | 4 (alpha,beta,alpha,gamma) | 1 | 2 | 1 | 1 | `alpha` seq 3 |

`accepted + dropped + coalesced == retained-or-resolved submissions` for `coalesce_latest`, and
`accepted + dropped == submissions` for `drop_newest` where no coalescing occurs.

## 6. Bounds and resource design

| Resource | Bound | Where |
| --- | --- | --- |
| Threads | ≤ 4 | concurrency sub-check in `T24-TS-003` (`test_observation_saturation_bound_matrix`, four competing lossless publishers) |
| Items per case | ≤ 64 | largest loop is 20 submissions; concurrency uses ≤ 64 |
| Taps per hub | ≤ 8 (`kMaximumObservationTaps`) | most cases use 1–3 |
| Records per tap | ≤ 16 (`kMaximumObservationRecordsPerTap`) | `T24-TS-003` maximum-capacity case |
| Payload bytes | ≤ 4 synthetic bytes | all fixtures |
| Prefix bound | 1 … 1024 | `T24-TS-001` |
| Iterations | finite, declared | every case |
| Wall-clock | none | every case |
| Allocation | ordinary test-local values only | every case |

## 7. Failure semantics of the matrix

| Condition | Expected | Case |
| --- | --- | --- |
| Metadata/redacted exposes a byte, or a non-`omitted`/non-`redacted` view | assertion fails → candidate rejected | `T24-TS-001` |
| Prefix source over bound reports `complete`, or the wrong prefix is copied | assertion fails | `T24-TS-001` |
| A decode/schema success is reported | assertion fails | `T24-TS-001` |
| Retained records are not FIFO or a coalesced replacement keeps its old position | assertion fails | `T24-TS-002` |
| Pulling one tap changes another tap's queue | assertion fails | `T24-TS-002` |
| A queue exceeds its declared bound | assertion fails | `T24-TS-003` |
| A loss is not counted, or the accounting identity fails | assertion fails | `T24-TS-003` |
| Lossless rejection mutates the provider/queue before rejecting | assertion fails | `T24-TS-003` |
| The declared validity effect is not applied, or lossless is below `degraded` | assertion fails | `T24-TS-004` |
| The realized status decreases without acknowledgement/detach, or persists across recreation | assertion fails | `T24-TS-004` |
| Detach mutates another tap, or a stale/foreign/claimed/closed handle is handled wrongly | assertion fails | `T24-TS-005` |
| A normalized-record field is lost or a record is not a value copy | assertion fails | `T24-TS-006`, `T24-TS-007` |
| An observer changes the route count, order, or delivery outcome | assertion fails | `T24-TS-008`, `T24-TS-009` |
| Concurrent lossless publishers lose or duplicate a claim, or the counter/queue state is inconsistent | assertion fails | `T24-TS-003` (concurrency sub-check) |
| A forbidden access or primitive is introduced | source scan fails | verification plan CHK-21/CHK-22 |

## 8. Build wiring design

**None.** The existing `xverse_xcom_observation_unit_tests` target compiles
`tests/xcom/observation/core/unit_tests.cpp` and the existing `xverse_xcom_observation_integration_tests`
target compiles `tests/xcom/observation/integration/integration_tests.cpp`; both are already registered as
the `xcom_observation_unit` and `xcom_observation_integration` CTest tests. The new cases are discovered by
the existing registration with no target, test name, label, command, or build-file change; the discovered
`ctest` count stays at the baseline value (306).

## 9. Doxygen plan

Every new case function carries a `@brief` line naming the requirement and evidence name it realizes. New
case-local helpers carry `@brief` plus the applicable ownership/lifetime/thread-safety/failure tags in the
existing file style. The file-block `@par Traceability` note in each edited fixture is extended to name
T024 and its requirement links (`XCOM-SW-OBS-001…-005`, FR-011…FR-014, FR-023, SC-003…SC-005). The admitted
documentation configuration is unchanged; strict declaration-level Doxygen remains `DOX-GAP-01`
(T011/T037).

## 10. Traceability

| Case | Evidence name(s) | T024 requirements | Accepted anchors |
| --- | --- | --- | --- |
| `T24-TS-001` `test_observation_metadata_and_payload_view_matrix` | `metadata-only-zero-payload`, `controlled-payload-view` | T024-SR-003, T024-SR-005, T024-SR-006 | XCOM-SW-OBS-001/002/005; FR-011, FR-012, SC-003 |
| `T24-TS-002` `test_observation_ordering_matrix` | `ordering` | T024-SR-007 | XCOM-SW-OBS-003; FR-013, SC-004 |
| `T24-TS-003` `test_observation_saturation_bound_matrix` | `saturation` | T024-SR-004, T024-SR-008, T024-SR-009, T024-SR-010, T024-SR-018 | XCOM-SW-OBS-003/-004; FR-013, FR-014, SC-004 |
| `T24-TS-004` `test_observation_validity_interval_matrix` | `degraded-validity` | T024-SR-011, T024-SR-012 | XCOM-SW-OBS-003/004; FR-013, FR-014, SC-004 |
| `T24-TS-005` `test_observation_safe_detach_matrix` | `safe-detach` | T024-SR-013 | XCOM-SW-OBS-004; FR-009, FR-014, SC-005 |
| `T24-TS-006` `test_observation_normalized_record_matrix` | `metadata-only-zero-payload` (normalized record) | T024-SR-015, T024-SR-016 | XCOM-SW-OBS-005; FR-023 |
| `T24-TS-007` `test_observation_record_edge_value_matrix` | `controlled-payload-view` (edge values) | T024-SR-002, T024-SR-015 | XCOM-SW-OBS-005; FR-023 |
| `T24-TS-008` `test_observation_route_ordering_neutrality_matrix` | `ordering`, `safe-detach` (route) | T024-SR-007, T024-SR-014 | XCOM-SW-OBS-004; FR-013, FR-014, SC-004, SC-005 |
| `T24-TS-009` `test_observation_route_saturation_safe_detach_matrix` | `saturation`, `degraded-validity`, `safe-detach` (route) | T024-SR-010, T024-SR-013, T024-SR-014 | XCOM-SW-OBS-003/004; FR-013, FR-014, SC-004, SC-005 |

The seven T007 `T-OBS` evidence names are covered as: `metadata-only-zero-payload` (TS-001, TS-006),
`controlled-payload-view` (TS-001, TS-007), `ordering` (TS-002, TS-008), `saturation` (TS-003, TS-009),
`degraded-validity` (TS-004, TS-009), `safe-detach` (TS-005, TS-008, TS-009); `disabled-tap-performance`
remains T036.

## 11. Revision 3 — Terminal review R-01 detailed repair design

### 11.1 Design principle

Correct **only** the false reconciliation statement and the validators that enforce it. Do not rewrite
accepted predecessor bytes, do not relabel acceptance, do not touch production semantics or maturity.
Every edit is minimal, deterministic, and reversible by git diff.

### 11.2 Register edit (`docs/engineering/xcom/task-ownership.json`)

For each task in the §11.3 map, the T-CORE and T-OBS `reconciliation` object changes on exactly three
fields:

| Field | From | To |
| --- | --- | --- |
| `status` | `unreconciled` | `delivered` |
| `revision` | `null` | the exact task candidate revision from the map |
| `reason` | `source present in the baseline but the capability task checkbox is open and no accepted exact-candidate revision is recorded (analysis A12; review 016 XCOM-NOSESN-08)` | `delivered as reviewed terminal candidate <revision> (predecessor <predecessor>) in ordered backlog xcom-t011-t016-t021-t024; the capability task checkbox is complete at that candidate; no accepted exact-candidate revision is recorded, so external Codex review and explicit user acceptance remain pending (terminal review R-01; analysis A12)` |

Every other field of the register is unchanged. T011, T017–T020, T025, and all `allocated` entries are
unchanged. The register `baseline_revision` (`923a6db…`) is the T007 authorized baseline and is **not**
changed; the delivered revisions are carried in the reconciliation entries.

### 11.3 Exact edit values

| Task | `status` | `revision` |
| --- | --- | --- |
| T012 | `delivered` | `863f11ac990c1ce178a0f9d8eb2489e4a5243fe7` |
| T013 | `delivered` | `93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59` |
| T014 | `delivered` | `8aaa9eb29ffb349538552d709d4e6f37011b3e65` |
| T015 | `delivered` | `44d2001d48dd42dc9ed489a40d2a5f908b734501` |
| T016 | `delivered` | `8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda` |
| T021 | `delivered` | `7be8b9718e42e58bb1a05a486ff62e520f94567c` |
| T022 | `delivered` | `d455c70816eb784066740427a70df9235cd1287d` |
| T023 | `delivered` | `76cdd9a533e5c4a3d5c6f583a4eff7724c18f5d6` |
| T024 | `delivered` | `d50bb48f45e422b8a7018710b1ac50cdadbcf8ed` |

### 11.4 Projection regeneration

`docs/engineering/xcom/task-ownership.md` is the deterministic projection of the JSON. It is regenerated
by importing `scripts/validate_xcom_task_ownership.py` and writing `project_markdown(model)` for the
edited model, so that `--check-human` compares byte-for-byte. The header and the note "Do not edit by
hand" are preserved by the projection function itself.

### 11.5 Validator edits

**`scripts/validate_xcom_task_ownership.py`**

| Location | Change |
| --- | --- |
| `RECON_STATUSES` | add `delivered` to the accepted vocabulary |
| `UNRECONCILED_TASKS` | replace with `DELIVERED_TASKS` (task → exact revision map, §11.3); `ALLOCATED_TASKS` excludes `DELIVERED_TASKS` |
| `_check_gates` | a `delivered` entry requires a 40-hex lowercase `revision` **and** a non-empty `reason`; a `delivered` task absent from the pinned map, or one whose revision differs, fails with `GATE_INVALID` |
| `_check_required_reconciliation` | T012–T016/T021–T024 must be `delivered` at the pinned exact revision |
| module/function docstrings | state the `delivered`/pending-acceptance semantics and drop the now-false "checkbox open" wording |

**`scripts/validate_xcom_requirements_traceability.py`**

| Location | Change |
| --- | --- |
| `_check_maturity` coverage branch | treat `delivered` like `unreconciled`: a requirement whose owning task is `delivered` must stay `partial` with a recorded reconciliation reason |
| `_check_reconciliation_dependency` docstring | name the `delivered` T012–T016/T021–T024 coverage |
| self-test `NEG-17` | unchanged in intent; it now exercises the `delivered` coverage branch and must still fail with `MATURITY_INVALID` |

`scripts/validate_xcom_architecture_contracts.py` and `scripts/validate_xcom_unit_design.py` consume only
the `accepted` status for the implemented-implies-accepted cross-check; they need **no** source change,
and their `--self-test` suites must pass unchanged.

**`tests/test_xcom_task_ownership_reconciliation.py` (new)**

The T024 deterministic gate requires a test task's candidate to change at least one `tests/` path. The
repair therefore adds exactly one offline governance regression test. It loads the task-ownership
validator as a module (no child process) and asserts: the `DELIVERED_TASKS` pin set equals the
nine-task delivered range (T012–T016, T021–T024); every delivered entry carries `status == "delivered"`,
its pinned revision, a non-empty pending-acceptance reason, and no "checkbox is open" text; `T025`
remains the only accepted task; the Markdown is the byte-stable projection; `run_checks` returns
`EXIT_OK`; the nine delivered capability checkboxes are `[X]` in `tasks.md`; and A12 records the
delivered-pending disposition. It starts no network peer, opens no file for writing, and mutates no
shared state.

### 11.6 Analysis edit (`specs/007-xcom-core/analysis.md`)

- A12 severity `MINOR`; status changes from `Open reconciliation` to
  `Resolved for delivery; external acceptance pending`, with text recording the nine `delivered` tasks,
  their exact revisions, and that reconciliation to accepted revisions remains pending external review
  and explicit user acceptance.
- A dated `2026-09-27 terminal review R-01 repair` successor note records that the accepted T008/T009/T010
  work products retain their historical open-checkbox language unmodified, superseded for the current
  state by this note; no task is marked accepted and no maturity is promoted.

### 11.7 Failure semantics

| Condition | Required behaviour |
| --- | --- |
| `delivered` task with `revision == null` or a non-40-hex value | validator fails `GATE_INVALID`; no partial pass |
| `delivered` task with an empty `reason` | validator fails `GATE_INVALID` |
| T012–T016/T021–T024 with a status other than `delivered` | validator fails `GATE_INVALID` |
| `delivered` task with a revision that differs from the pinned exact revision | validator fails `GATE_INVALID` |
| a `delivered` task relabelled `accepted` without an accepted record | validator fails `GATE_INVALID` |
| projection drift between JSON and Markdown | validator fails `DETERMINISM_INVALID` |
| required requirement coverage made `implemented` while its owning task is `delivered` | requirements validator fails `MATURITY_INVALID` |

No failure path writes the candidate tree, mutates accepted evidence, or emits a success claim.

### 11.8 Bounds

Single-threaded; per-file input bound 1 MiB and total bound 4 MiB in the task-ownership validator; no
network, subprocess, listener, or clock. The repair itself performs no unbounded loop or wait.

### 11.9 Traceability

`T024-R01-SR-001` → register + validator; `T024-R01-SR-002` → A12; `T024-R01-SR-003` → successor note;
`T024-R01-SR-004` → validators; `T024-R01-SR-005` → acceptance boundary; `T024-R01-SR-006` → gate;
`T024-R01-SR-007` → path boundary; `T024-R01-SR-008` → public safety.
