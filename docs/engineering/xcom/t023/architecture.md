# T023 Architecture — Synthetic Sink, Failure/Disconnect Isolation, and Visible Counters

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T023 (capability 007, slice `T-OBS`) |
| Stage / role | plan → architecture |
| Revision | 1 |
| Baseline revision | `d455c70816eb784066740427a70df9235cd1287d` |
| Affected source paths | `src/xverse/xcom/include/xverse/xcom/observation.hpp`, `src/xverse/xcom/src/observation.cpp` (production); `tests/xcom/observation/core/unit_tests.cpp`, `tests/xcom/observation/integration/integration_tests.cpp` (fixtures); no build file |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-011` synthetic sink and tools, `XCOM-CMP-008` observation boundary, `XCOM-INV-02`, `XCOM-INV-06`, `XCOM-DGM-003`); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-013` bounded observer queue/counters/synthetic sink); `docs/engineering/xcom/t021/architecture.md` (declared observation layer); `docs/engineering/xcom/t022/architecture.md` (retention and validity layer); `specs/007-xcom-core/contracts/observation.md`; ADR-0019 |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T023 is the **consumer-sink layer of the observation boundary**. It owns the synthetic observation sink:
its visible consumer counter projection, its local disconnect behavior, its failure behavior for a stale/
foreign/closed handle, and the proof that a disconnected, failed, or non-pulling sink is isolated from the
normal route. It owns no payload-view behavior, no retention or validity rule (T021/T022), no broad
observation matrix (T024), no transport/gateway consumer (T032/T033), and no presentation or storage.

T023 closes the handoff recorded by the predecessors: `T021-GAP-03` and `T022-GAP-02` — "Synthetic sink
failure/disconnect isolation and its visible counters" — allocated to T023.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013 core types → T015 provider composition
   → T019 bounded activation-plan decode → T021 declared observation layer
   → T022 bounded retention + applied validity effect
   → T023 synthetic sink, failure/disconnect isolation, visible counters (this document)
   → T024 observation matrix
   → { T-XDL consumed, T-STIM } → T-INTG (T035–T038) → T-REVIEW (T039/T041)
```

T023 is a **production-path** slice: the deterministic gate requires at least one changed
`src/xverse/xcom/**` path, satisfied by `observation.hpp`/`observation.cpp`. No build file, XDL schema,
contract, provider, plan, or later-slice interface changes.

## 3. Boundary and context

### 3.1 System context

```text
   ┌──────── XDL / io.xverse.xcom Profile + activation plan (read-only, T017–T019) ────────┐
   │  observation-policy: payloadAccess · bounds · validityEffect                            │
   │  observationPoints[]: tapId · routeId · payloadAccess · validityEffect                  │
   └────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │ declared vocabulary (no competing language)
   ┌──────────────── T021/T022 observation boundary (src/xverse/xcom, xverse::xcom) ────────┐
   │  observation.hpp/cpp                                                                    │
   │    producer seam    ObservationHub::reserve/commit/cancel (claim before provider)         │
   │    retention layer  drop_newest · coalesce_latest · lossless_validation                   │
   │    validity layer   ObservationValidityState + applied declared effect                    │
   │    reporting layer  ObservationSnapshot counters + validity_state                          │
   │    authority layer  ObservationTapHandle · poll/snapshot/acknowledge/detach               │
   └────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │ poll(exact handle) → value-owned record / stable outcome
   ┌────────────────────────────────────▼──────────────────────────────────────────────────┐
   │  T023 synthetic consumer: SyntheticObservationSink + SyntheticSinkCounters (this slice)   │
   │    connect() · disconnect() · pull() · connected() · counters()                           │
   └──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T23-XB-1` Consumer vs normal route | the sink's local connected flag, counters, and copied handle | the normal provider queue, ordering, and delivery outcome | The sink observes only; a disconnect, failure, or blocked consumer never blocks, reorders, emits, or mutates a normal-route item (SC-005). |
| `T23-XB-2` Consumer counters vs tap counters | the sink's `pulled`/`empty`/`disconnected`/`failed` projection | the tap's `accepted`/`dropped`/`coalesced`/`backpressure_rejections` counters and validity status | The sink counters describe the consumer's own pull outcomes; the tap loss counters stay on `ObservationHub::snapshot`; neither is inferred from the other. |
| `T23-XB-3` Local disconnect vs tap lifecycle | `disconnect()`/`connect()` on one sink | the tap's attach/detach/generation state | A disconnect is local to one sink and never detaches, acknowledges, or recreates a tap. |
| `T23-XB-4` Exact handle vs declared identity | the copied generation-bound `ObservationTapHandle` | declared tap/route/filter identity | Only the copied exact handle is used; a stale/foreign/closed handle yields the stable failure outcome with no mutation. Failure is reported with the accepted `invalid_tap_handle`, not a new outcome. |
| `T23-XB-5` Observation vs export/storage | in-process consumer counters | Argus, OpenTelemetry, files, dashboards, databases, adapters, the tool gateway | X-COM owns no rendering, storage, query, or export; the counters are an in-process projection only (Argus boundary, ADR-0019; T032/T033 own the gateway consumer). |
| `T23-XB-6` Repository vs environment | committed source, tests, work products | admitted build inputs, build trees, host paths | Committed files are public-safe and offline; no ambient, network, filesystem, or process access is introduced. |

### 3.3 Prohibited elements (must remain absent)

No TCP listener, external network peer, discovery, package manager/registry, filesystem access, process
execution, legacy repository/binary access, dynamic plugin discovery, domain-specific primitive, new
admitted dependency, competing configuration language, unbounded resource, consumer callback under an
X-COM lock, or export/dashboard/storage/query behavior. No new `ObservationOutcome` value. These inherit
the T007 global prohibitions, the T011 envelope, the T012 build contract, ADR-0019, and the constitution.

## 4. Components

Each component maps to a unit in `unit-specifications.md`. `T23-CMP-*` names are local to this document;
the accepted `XCOM-DU-*`/`XCOM-CMP-*` identifiers are the authorized design units/components.

### 4.1 New and extended components (design unit `XCOM-DU-013`, component `XCOM-CMP-011`)

- **`T23-CMP-SINK-COUNTERS`** — **new** `SyntheticSinkCounters`: an immutable, value-owned consumer
  counter projection (`pulled`, `empty`, `disconnected`, `failed`) and the sink's read-only `counters()`
  accessor. It is the "visible counters" deliverable of T023.
- **`T23-CMP-SINK`** — the extended `SyntheticObservationSink`: constructor, `connect()`, `disconnect()`,
  `pull()`, `connected()`, and the new `counters()`. `pull()` maintains the visible counters on the actual
  outcome; `connect()` re-validates the exact handle and updates the local flag; `disconnect()` stays a
  local action.
- **`T23-CMP-ISOLATION`** — the behavior rule that a disconnect, a stale/foreign/closed handle, or a
  non-pulling consumer is isolated: no tap or route mutation and no blocking/reordering of the normal
  route, with the tap loss counters still visible through the exact-handle snapshot.

### 4.2 Preserved components (read-only for T023)

- **`T23-CMP-HUB`** (`XCOM-CMP-008`, `XCOM-DU-013`) — `ObservationHub` attach/reserve/commit/cancel/poll/
  snapshot/acknowledge/detach, the mutex serialization, and the exact-handle authentication: **re-verified
  unchanged**; the sink consumes only the const/pull path.
- **`T23-CMP-RETENTION`** (`XCOM-DU-013`, T022) — the accepted `drop_newest`/`coalesce_latest`/
  `lossless_validation` rules and the applied declared validity effect: **re-verified unchanged**.
- **`T23-CMP-DECLARATION`** (`XCOM-DU-012`, T021) — filter matching, declared tap/route identity, the
  immutable record/counter projection, and the payload view policy: **re-verified unchanged**.
- **`T23-CMP-ROUTE`** (`XCOM-CMP-006`, T015) — provider composition and the owned loopback provider:
  consumed read-only by the integration isolation case.

### 4.3 Work-product components

- **`T23-WP`** — the T023 repository-owned work-product set (`requirements.md`, `architecture.md`,
  `detailed-design.md`, `unit-specifications.md`, `verification-plan.md`, `implementation.md`,
  `internal-review.json`, and `reports/xcom-queue/t023-package.json`).

### 4.4 Consumed components (read-only)

`XCOM-CMP-006` provider composition, `XCOM-CMP-002` X-COM Profile/schema, `XCOM-CMP-003` activation plan,
and `XCOM-CMP-004` core value types are consumed or matched but neither implemented nor altered by T023.

## 5. Data flow (ordered)

1. **Attach** — a consumer builds a validated `ObservationTapSpec` and attaches it; the hub issues an exact
   `ObservationTapHandle` (T021, unchanged).
2. **Bind sink** — a `SyntheticObservationSink` is constructed from the hub and a copy of the exact handle;
   it stores a non-owning hub pointer, the copied handle, a local connected flag, and zeroed counters.
3. **Pull (connected)** — `pull()` delegates to `ObservationHub::poll(handle)`:
   - a retained record → returns the value-owned record and increments `pulled`;
   - no retained record → returns `no_record` and increments `empty`;
   - a stale/foreign/closed handle → returns `invalid_tap_handle` and increments `failed`.
4. **Pull (disconnected)** — a locally disconnected sink returns `sink_disconnected`, increments
   `disconnected`, and does not call `poll`; no record is consumed.
5. **Inspect sink** — `counters()` returns the immutable consumer counter projection; `connected()` returns
   the local flag.
6. **Inspect tap** — `ObservationHub::snapshot(exact handle)` returns the accepted tap counters
   (`queued`, `accepted`, `dropped`, `coalesced`, `backpressure_rejections`), the validity status, and the
   declared identity for an authenticated handle; it remains the source of tap loss evidence.
7. **Disconnect / reconnect** — `disconnect()` disables only that sink; `connect()` re-validates the exact
   handle, enabling pulls on success and reporting `invalid_tap_handle` (leaving the sink disabled) on a
   stale/foreign/closed handle.
8. **Observer removal** — an external `detach()` closes the tap and discards only its records; the sink's
   copied handle is now stale, so the next `pull()` reports `invalid_tap_handle` and increments `failed`,
   while the normal route continues unchanged.

## 6. Interfaces

T023 exposes an in-process C++20 API only (no transport, no external ABI).

| Interface | Contract |
| --- | --- |
| `SyntheticSinkCounters` | immutable, value-owned consumer counter projection with `pulled`, `empty`, `disconnected`, `failed`; safe to copy and read concurrently; no view into hub storage. |
| `SyntheticObservationSink::SyntheticObservationSink(ObservationHub&, const ObservationTapHandle&)` | `noexcept`; binds a non-owning hub reference and a copied exact handle; counters start at zero. |
| `SyntheticObservationSink::connect()` | `noexcept`; `accepted` and enabled on a valid exact handle; `invalid_tap_handle` and disabled otherwise; mutates no tap. |
| `SyntheticObservationSink::disconnect()` | `noexcept`; disables only this sink; never detaches or mutates a tap. |
| `SyntheticObservationSink::pull()` | `noexcept`; a value-owned record (`accepted`, `pulled` + 1), `no_record` (`empty` + 1), `sink_disconnected` (`disconnected` + 1), or `invalid_tap_handle` (`failed` + 1). |
| `SyntheticObservationSink::connected()` | `noexcept`; the local enabled flag (unchanged surface). |
| `SyntheticObservationSink::counters()` | `noexcept`; the immutable consumer counter projection for the sink's lifetime. |
| `ObservationHub::poll(const ObservationTapHandle&)` / `snapshot(...)` | consumed unchanged; the tap loss counters remain on the snapshot. |

## 7. Concurrency and resource bounds

| Aspect | T023 decision |
| --- | --- |
| Sink serialization | each sink call executes through the hub's single mutex for its tap; `pull()` is a serialized `poll`. |
| Counter updates | performed on the calling thread only; the counter projection is copied by value from `counters()`; no shared mutable state is added to the hub. |
| Returned values | records and counter projections are value copies; no view into hub or sink storage escapes through a reference that outlives the call. |
| Callbacks | none; no consumer code is invoked under any X-COM lock (the boundary is pull-only). |
| Handle authority | one copied generation-bound handle per sink; a stale/foreign/closed handle yields the stable failure outcome. |
| Sink footprint | one non-owning `ObservationHub*`, one copied handle (three 64-bit fields), one bool, four 64-bit counters; no allocation. |
| Tap/record bounds | inherited unchanged: `kMaximumObservationTaps` = 8, `kMaximumObservationRecordsPerTap` = 16, `kMaximumObservedPayloadBytes` = 1024. |
| Duration/retry/rate/quota | none; the sink has no timer, retry, rate, or quota. |
| Test bounds | ≤ 4 threads, ≤ 16 record slots, finite items, 4-byte fixture payloads; no wall-clock threshold. |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Fail-closed safety | a disconnect, failure, or blocked consumer never blocks, reorders, emits, or mutates the route; the outcome is a stable accepted value | T023-SR-003…-007; NEG-03…NEG-08 |
| Visible counters | the sink exposes an immutable consumer counter projection; the tap loss counters stay on the exact-handle snapshot | T023-SR-001, T023-SR-002; CHK-06 |
| Exact authority | only the copied exact handle is observed; a stale/foreign/closed handle fails without mutation | T023-SR-004, T023-SR-005; CHK-08 |
| Route neutrality | the sink is read-only (`poll`/const authentication); it never detaches or acknowledges | T023-SR-007; CHK-10 |
| Concurrency safety | sink calls serialize through the hub mutex; counters are caller-thread; no callback | T023-SR-008; CHK-11, CHK-12 |
| Bounded resources | fixed counters and copied handle; no allocation, timer, retry, rate, or quota | T023-SR-009; CHK-13 |
| Domain neutrality | no provider, protocol, address, domain, or product primitive; the counters name only pull outcomes | T023-SR-010; CHK-17 |
| Offline safety | standard-library only; no network, ambient, filesystem, or process access | T023-SR-010; CHK-17, NEG-10 |
| Public safety | committed files carry no secret, private address, real payload, or host path | T023-SR-011; CHK-18, NEG-11 |
| Documentation | every new/changed public declaration documents ownership/lifetime/thread-safety/failure | T023-SR-012; CHK-19 |
| Governance | no accepted artifact rewritten; registers re-validated; REF-002 unchanged; T021/T022 behavior unchanged | T023-SR-013, T023-SR-015, T023-SR-016; CHK-14, CHK-20, CHK-22 |

## 9. Consistency and constraints

- **Dependency direction preserved.** T023 consumes the accepted XDL/plan declaration model and the
  T021/T022 observation layer; it introduces no dependency on a later slice and no adapter, storage, or
  dashboard element.
- **Domain neutrality preserved.** The only vocabulary added (`SyntheticSinkCounters`) names generic pull
  outcomes; no automotive or product primitive is introduced and no configuration language is authored.
- **XDL centrality preserved.** T023 neither parses nor authors XDL and mirrors the accepted declaration
  only indirectly through the consumed tap policy.
- **Logical/physical separation preserved.** The sink counters are logical, per-sink values; no address,
  provider, or transport identity enters them.
- **Argus boundary preserved.** The counters are normalized in-process values only; X-COM owns no
  rendering, storage, query, or presentation (`T23-XB-5`, ADR-0019).
- **Ownership preserved.** Only T023-owned observation paths, the T023 work products, and the T023
  checkbox change; the accepted T021/T022 declaration, retention, and validity behavior is re-verified
  unchanged, T024 keeps the matrix, and no prior declaration is weakened.
- **Maturity preserved.** The observation boundary stays a bounded prototype; executed sanitizer/static/
  Doxygen evidence, benchmarks, integration, and acceptance remain with T035–T041.

## 10. Traceability

| Architecture element | T023 requirements |
| --- | --- |
| `T23-XB-1`, `T23-CMP-ISOLATION` | T023-STK-002, T023-SR-003, T023-SR-004, T023-SR-006 |
| `T23-XB-2`, `T23-CMP-SINK-COUNTERS` | T023-SR-001, T023-SR-002, T023-SR-016 |
| `T23-XB-3`, `T23-CMP-SINK` | T023-SR-003, T023-SR-005, T023-SR-007 |
| `T23-XB-4` | T023-STK-003, T023-SR-004, T023-SR-005 |
| `T23-XB-5`, `T23-CMP-SINK-COUNTERS` | T023-STK-004, T023-SR-010, T023-SR-011 |
| `T23-XB-6`, `T23-WP` | T023-STK-005, T023-SR-012, T023-SR-014, T023-SR-015 |
| `T23-CMP-HUB`, `T23-CMP-RETENTION`, `T23-CMP-DECLARATION`, `T23-CMP-ROUTE` | T023-SR-006, T023-SR-008, T023-SR-013, T023-SR-016 (re-verified unchanged) |
