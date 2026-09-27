# T023 Unit Specifications — Synthetic Sink Counters, Isolation, and Test Units

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T023 (capability 007, slice `T-OBS`) |
| Stage / role | plan → unit specifications (pre-code) |
| Revision | 1 |
| Baseline revision | `d455c70816eb784066740427a70df9235cd1287d` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Accepted unit design | `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-013` bounded observer queue, counters, and synthetic sink, owning tasks T022/T023; `XCOM-DU-012` observation record and payload-view policy, owning task T021) |
| Accepted components | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-011` synthetic sink and tools, owning tasks T023/T032/T033; `XCOM-CMP-008` observation boundary) |
| Accepted test unit | `XCOM-T-OBS` (`tests/xcom/observation/`, `docs/engineering/xcom/t008/traceability-matrix.{json,md}`) |
| Classification | Public-safe engineering work product |

These unit specifications elaborate, without weakening, the accepted T010 unit design for `XCOM-DU-013`,
the `XCOM-CMP-011` synthetic-sink component, and the `XCOM-DU-012`/`XCOM-CMP-008` surface that T023
consumes read-only. Where the T008 register attributes `XCOM-SW-OBS-004` to T023 while T010 links
`XCOM-DU-013` to `XCOM-SW-OBS-003`/`-004` and `XCOM-CMP-011` to `XCOM-SW-OBS-005`, T023 implements the
synthetic-sink counter/isolation half, preserves the accepted declaration/retention/validity half
unchanged (§7 of `requirements.md`), does not rewrite the registers, and promotes no maturity.

## 2. Unit inventory

| Unit (T023) | Accepted unit | Component | Kind | Language | Path(s) | Change |
| --- | --- | --- | --- | --- | --- | --- |
| `T023-U-COUNTERS` | `XCOM-DU-013` | `T23-CMP-SINK-COUNTERS` | data | cpp | `observation.hpp`, `observation.cpp` | new (`SyntheticSinkCounters` + `counters()`) |
| `T023-U-SINK` | `XCOM-DU-013` | `T23-CMP-SINK` | test-fixture | cpp | `observation.hpp`, `observation.cpp` | extended (`pull`/`connect` maintain the visible counters) |
| `T023-U-ISOLATION` | `XCOM-DU-013` | `T23-CMP-ISOLATION` | boundary | cpp | `observation.hpp`, `observation.cpp` | new behavior rules over the existing surface |
| `T023-U-HUB` | `XCOM-DU-013` | `T23-CMP-HUB` | boundary | cpp | `observation.hpp`, `observation.cpp` | re-verified unchanged (consumed read-only) |
| `T023-U-RETENTION` | `XCOM-DU-013` (T022) | `T23-CMP-RETENTION` | boundary | cpp | `observation.hpp`, `observation.cpp` | re-verified unchanged |
| `T023-U-DECLARATION` | `XCOM-DU-012` (T021) | `T23-CMP-DECLARATION` | boundary | cpp | `observation.hpp`, `observation.cpp` | re-verified unchanged |
| `T023-U-ROUTE` | `XCOM-CMP-006` (T014/T015) | `T23-CMP-ROUTE` | boundary | cpp | `provider.hpp`, `loopback_provider.hpp` | re-verified unchanged (consumed by the integration case) |
| `T023-U-TEST` | `XCOM-T-OBS` | `T23-WP` | test | cpp | `tests/xcom/observation/` | extended (focused cases) |

## 3. Unit specifications

### 3.1 `T023-U-COUNTERS` — visible consumer counter projection (new)

- **Interface**: `SyntheticSinkCounters` (`pulled`, `empty`, `disconnected`, `failed`; four fixed
  `std::uint64_t` fields) and `SyntheticObservationSink::counters()`.
- **Behaviour**: exposes the consumer's own pull outcomes as an immutable value copy; monotonic over the
  sink's lifetime; updated only by `pull()`; never duplicating or reinterpreting the tap loss counters.
- **Ownership**: owned by the sink, copied out by value. **Lifetime**: the sink's lifetime; discarded with
  the sink. **Thread-safety**: updated on the calling thread only; a single sink is not used concurrently.
- **Bounds**: four fixed 64-bit counters; no allocation. **Overflow**: `n/a` (64-bit monotonic; the
  accounting identity holds).
- **Failure**: `counters()` is `noexcept` and returns a stable value; no counter is raised without a
  matching pull outcome.
- **Doxygen**: group `xcom_obs`; the four fields and the accessor documented with
  ownership/lifetime/thread-safety/failure.
- **Planned evidence**: CHK-06; `test_synthetic_sink_visible_counters`.

### 3.2 `T023-U-SINK` — synthetic pull sink (extended surface)

- **Interface**: `SyntheticObservationSink` constructor, `connect`, `disconnect`, `pull`, `connected`
  (unchanged signatures) plus the new `counters()` accessor.
- **Behaviour**: pulls through the hub with the copied exact handle; a successful pull returns a value-owned
  record and increments `pulled`; an empty pull returns `no_record` and increments `empty`; a local
  disconnect yields `sink_disconnected` and increments `disconnected`; a stale/foreign/closed handle yields
  `invalid_tap_handle` and increments `failed`; the sink never detaches, acknowledges, or mutates a tap.
- **Ownership**: caller-owns-value (sink state); the hub is referenced non-owning.
  **Lifetime**: the hub must outlive the sink. **Thread-safety**: serialized through the hub; one sink is
  single-owner state.
- **Bounds**: one pointer, one copied handle, one bool, four counters. **Overflow**: `n/a`.
- **Failure**: the accepted stable `sink_disconnected` / `no_record` / `invalid_tap_handle` outcomes plus the
  underlying hub status; no route effect; `noexcept`.
- **Doxygen**: group `xcom_obs`; the counter semantics documented on `pull`/`counters`.
- **Planned evidence**: CHK-06, CHK-08, CHK-10; `test_synthetic_sink_visible_counters`,
  `test_synthetic_sink_failure_isolation`, `test_synthetic_sink_concurrency` (preserved).

### 3.3 `T023-U-ISOLATION` — disconnect/failure/blocking isolation (new behavior rules)

- **Interface**: the existing `connect`/`disconnect`/`pull` surface; no new authority and no hub mutation.
- **Behaviour**: a local disconnect affects only that sink; a stale/foreign/closed handle fails without
  mutating any tap; a connected sink that does not pull never blocks, delays, reorders, or changes a
  submission, and the observed tap's bounded drop/coalesce counters stay visible on the exact-handle
  snapshot.
- **Ownership**: the route is owned by its provider/composition; the tap is owned by the hub; the sink owns
  only its local state. **Lifetime**: route-scoped to the tap/sink interval. **Thread-safety**: serialized
  through the hub mutex.
- **Bounds**: the tap queue is bounded 1–16 by the declared capacity; the sink adds no unbounded resource.
  **Overflow**: the accepted `drop-newest`/`coalesce`/`lossless-backpressure` rules.
- **Failure**: a disconnect/failure/blocked consumer leaves the normal route and unrelated taps unchanged;
  the accepted stable outcomes are returned.
- **Doxygen**: group `xcom_obs`; the isolation contract documented on the sink and file block.
- **Planned evidence**: CHK-07, CHK-09, CHK-10; `test_synthetic_sink_disconnect_isolation`,
  `test_synthetic_sink_blocking_isolation`, `test_synthetic_sink_route_isolation_counters`.

### 3.4 `T023-U-HUB` / `T023-U-RETENTION` / `T023-U-DECLARATION` — preserved observation boundary (read-only for T023)

- **Interface**: `ObservationHub` operations, `ObservationRecord`, `ObservationTapSpec`, `ObservationFilter`,
  `ObservationSnapshot`, the payload-mode/validity/overflow vocabularies (unchanged).
- **Behaviour**: attach/authentication/generation/capacity, filter matching, payload views, schema state,
  retention rules (drop/coalesce/lossless), the applied validity effect, the realized validity status, and
  the snapshot projection are all unchanged; the sink is a new read-only consumer of the existing
  `poll`/`snapshot` path.
- **Ownership**: platform-owns-shared; caller-owns-value for records/snapshots. **Lifetime**: route/tap
  scoped. **Thread-safety**: one hub mutex, copy-after-unlock, no callback.
- **Bounds**: 8 tap slots, 16 record slots per tap, 1024-byte payload prefixes. **Overflow**: accepted
  policies.
- **Failure**: the accepted stable outcomes only; no new outcome value is added.
- **Doxygen**: group `xcom_obs`; unchanged baseline documentation retained.
- **Planned evidence**: CHK-05, CHK-14, CHK-20; the preserved unit and integration cases.

### 3.5 `T023-U-ROUTE` — provider composition and loopback route (consumed read-only)

- **Interface**: `ProviderComposition::submit`/`receive`/`route_state`, the loopback provider (unchanged).
- **Behaviour**: the integration isolation case submits through the owned loopback route to prove that a
  disconnected/failed sink does not change the normal-route item count, order, or outcome.
- **Ownership**: scenario-owned. **Lifetime**: scenario lifetime. **Thread-safety**: the composed provider
  and hub serialize their own operations.
- **Bounds**: the loopback route's fixed queue/item bounds. **Overflow**: `queue_saturated` (accepted).
- **Failure**: unchanged provider outcomes and diagnostics.
- **Doxygen**: unchanged baseline documentation retained.
- **Planned evidence**: CHK-09; `test_synthetic_sink_route_isolation_counters` and the preserved
  `test_best_effort_isolation`.

### 3.6 `T023-U-TEST` — T-OBS focused sink-counter/isolation fixture update

- **Interface / behaviour**: extends the existing observation unit fixture with the focused T023 cases and
  adds one route-level integration case; no existing assertion is weakened and no target, test name, or
  label is added, renamed, or removed.
- **Ownership**: test-owned fixtures. **Lifetime**: process-scoped. **Thread-safety**: the reused
  concurrency fixtures use ≤ 4 threads with joined, finite loops.
- **Bounds**: finite item counts, 4-byte synthetic payloads, ≤ 16 record slots. **Overflow**: `n/a`.
- **Failure**: a failed expectation prints to `stderr` and returns a non-zero exit status; no external I/O.
- **Doxygen**: file block plus `@brief` on every new helper and case.
- **Planned evidence**: all executable checks in `verification-plan.md` §4.

## 4. Work-product units

| Unit | Artifact | Owner | Check |
| --- | --- | --- | --- |
| `T023-W01` | `docs/engineering/xcom/t023/requirements.md` | T023 | CHK-22 |
| `T023-W02` | `docs/engineering/xcom/t023/architecture.md` | T023 | CHK-22 |
| `T023-W03` | `docs/engineering/xcom/t023/detailed-design.md` | T023 | CHK-22 |
| `T023-W04` | `docs/engineering/xcom/t023/unit-specifications.md` | T023 | CHK-22 |
| `T023-W05` | `docs/engineering/xcom/t023/verification-plan.md` | T023 | CHK-22 |
| `T023-W06` | `docs/engineering/xcom/t023/implementation.md` | T023 | CHK-21 |
| `T023-W07` | `docs/engineering/xcom/t023/internal-review.json` | T023 | review gate |
| `T023-W08` | `reports/xcom-queue/t023-package.json` | T023 | package gate |

## 5. Planned tests (exact)

No new CTest target, test name, or label is added. The focused unit cases extend the existing T-OBS
executable `xverse_xcom_observation_unit_tests` (registered as `xcom_observation_unit`) and the one
route-level case extends `xverse_xcom_observation_integration_tests` (registered as
`xcom_observation_integration`), so the discovered test count is unchanged from the baseline 306.
`xcom_observation_disabled_benchmark` keeps its exact name, label, command, and expected result and is not
edited.

| CTest target | Test name | Added cases | Existing cases (preserved) |
| --- | --- | --- | --- |
| `xcom_observation_unit` | `xcom_observation_unit` | `test_synthetic_sink_visible_counters`, `test_synthetic_sink_disconnect_isolation`, `test_synthetic_sink_failure_isolation`, `test_synthetic_sink_blocking_isolation` | every accepted case, including `test_synthetic_sink_concurrency` and the T021/T022 cases |
| `xcom_observation_integration` | `xcom_observation_integration` | `test_synthetic_sink_route_isolation_counters` | every accepted case, including `test_best_effort_isolation` |
| `xcom_observation_disabled_benchmark` | `xcom_observation_disabled_benchmark` | none (not edited) | unchanged |

Case intent:

- `test_synthetic_sink_visible_counters` — a sink performs a deterministic pull sequence: two retained
  records (→ `pulled == 2`, records returned in FIFO order), one empty pull (→ `empty == 1`), a local
  disconnect followed by a pull (→ `disconnected == 1`, `sink_disconnected`, no record consumed), a
  reconnect, and then a pull after the tap is detached (→ `failed == 1`, `invalid_tap_handle`); the
  accounting identity `pulled + empty + disconnected + failed == pull attempts` holds and `connected()`
  reflects each state transition.
- `test_synthetic_sink_disconnect_isolation` — two sinks are attached to two independent taps; sink A is
  disconnected while its tap still holds retained records; pulling sink A returns `sink_disconnected` and
  consumes nothing, so the tap's `size`/`queued` and counters are unchanged; sink B and its tap are
  unaffected; reconnecting sink A restores pulls and the retained records.
- `test_synthetic_sink_failure_isolation` — a sink bound to a handle whose tap is later detached, and a sink
  bound to a handle from a foreign hub, both report `invalid_tap_handle` and increment `failed`; the
  observed tap (detached or recreated) and the unrelated tap are not mutated, the recreated slot keeps its
  own counters, and `connect()` on the stale/foreign handle reports `invalid_tap_handle` and leaves the
  sink disabled without touching any tap.
- `test_synthetic_sink_blocking_isolation` — a connected sink is created but never pulls while a writer
  submits more than the declared capacity; the tap queue stays within its declared bound, the deterministic
  `dropped`/`coalesced` counters are visible on the exact-handle snapshot, the retained records keep FIFO
  order, and the sink's counters remain all zero until it pulls.
- `test_synthetic_sink_route_isolation_counters` (integration) — using one `Scenario` over the owned
  loopback route, a sink is disconnected; the route still accepts the configured items in order with
  unchanged outcomes, the sink's `disconnected` counter is visible, and after the observed tap is detached
  the route still accepts a further item while the sink records `failed` and the stale tap snapshot is
  absent.

## 6. Requirement-to-unit-to-test traceability

| Requirement | Unit(s) | Planned test case(s) | Check(s) |
| --- | --- | --- | --- |
| T023-SR-001 | `T023-U-COUNTERS` | `test_synthetic_sink_visible_counters` | CHK-06, NEG-01 |
| T023-SR-002 | `T023-U-COUNTERS`, `T023-U-SINK` | `test_synthetic_sink_visible_counters` | CHK-06, NEG-01, NEG-02 |
| T023-SR-003 | `T023-U-ISOLATION`, `T023-U-SINK` | `test_synthetic_sink_disconnect_isolation`, `test_synthetic_sink_route_isolation_counters` | CHK-07, NEG-03, NEG-05 |
| T023-SR-004 | `T023-U-ISOLATION`, `T023-U-HUB` | `test_synthetic_sink_failure_isolation`, `test_synthetic_sink_route_isolation_counters` | CHK-08, NEG-04, NEG-05 |
| T023-SR-005 | `T023-U-SINK` | `test_synthetic_sink_failure_isolation`, `test_synthetic_sink_disconnect_isolation` | CHK-07, NEG-03, NEG-04 |
| T023-SR-006 | `T023-U-ISOLATION`, `T023-U-RETENTION` | `test_synthetic_sink_blocking_isolation` | CHK-09, NEG-06, NEG-07 |
| T023-SR-007 | `T023-U-SINK`, `T023-U-ISOLATION` | `test_synthetic_sink_failure_isolation`, `test_synthetic_sink_blocking_isolation` | CHK-10, NEG-05, NEG-08 |
| T023-SR-008 | `T023-U-SINK`, `T023-U-HUB` | `test_synthetic_sink_concurrency` (preserved) | CHK-11, CHK-12, NEG-09 |
| T023-SR-009 | `T023-U-COUNTERS`, `T023-U-SINK` | constants/member inspection plus the fixed-bound cases | CHK-13, CHK-18 |
| T023-SR-010 | all units | forbidden-API scan plus the offline build | CHK-17, NEG-10 |
| T023-SR-011 | work products and tests | public-safety scan | CHK-18, NEG-11 |
| T023-SR-012 | all changed units | declaration inspection plus the documentation validator | CHK-19 |
| T023-SR-013 | work products and tests | changed-path and test-name comparison; preserved-behavior regression | CHK-02, CHK-14, CHK-20, NEG-12, NEG-13 |
| T023-SR-014 | work products | deterministic gate | CHK-21 |
| T023-SR-015 | work products | register validators plus attribution inspection | CHK-20, CHK-22 |
| T023-SR-016 | `T023-U-COUNTERS`, `T023-U-SINK` | outcome-vocabulary inspection plus the isolation cases | CHK-05, CHK-14 |

## 7. Scope-preservation notes

- The broad observation matrix (T024), the disabled-tap benchmark (T036), the separate-process synthetic
  client and tool gateway (T032/T033), and the payload identity allow-list/decoder remain with their owning
  tasks (`T023-GAP-01`…`-04`); T023 adds only the synthetic-sink visible counters and the focused
  disconnect/failure/blocking isolation cases.
- No existing test case is removed, renamed, or weakened. `test_support.hpp` is not edited because its
  shared `make_tap_spec` helper already declares a valid observation point and the default `none` effect.
- `tests/xcom/observation/integration/disabled_tap_benchmark.cpp` is not edited; its paired-baseline seam
  and threshold are governed by T036.
- `scripts/validate_xcom_observation.py` is legacy SESN-era tooling in the T-OBS path set and is neither
  executed nor edited by the repository-owned workflow (`T023-LIM-06`).
- No CMake file changes: the existing `xverse::xcom_observation` target compiles the changed unit and the
  existing observation executables compile the changed fixtures.
