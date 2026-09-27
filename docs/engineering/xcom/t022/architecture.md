# T022 Architecture — Bounded Retention and Applied Validity Effect

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T022 (capability 007, slice `T-OBS`) |
| Stage / role | plan → architecture |
| Revision | 1 |
| Baseline revision | `7be8b9718e42e58bb1a05a486ff62e520f94567c` |
| Affected source paths | `src/xverse/xcom/include/xverse/xcom/observation.hpp`, `src/xverse/xcom/src/observation.cpp` (production); `tests/xcom/observation/core/unit_tests.cpp` (fixture); no build file |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-008` observation boundary, `XCOM-INV-02`, `XCOM-INV-06`, `XCOM-DGM-003`); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-013` bounded observer queue/counters; `XCOM-DU-012`); `docs/engineering/xcom/t021/architecture.md` (declared observation layer); `specs/007-xcom-core/contracts/observation.md`; ADR-0019 |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T022 is the **retention and validity layer of the observation boundary**. It owns the bounded best-effort
drop and coalesce modes, the explicit lossless-validation mode, the application of the declared validity
effect to every matching loss, and the observable realized validity status. It owns no payload-view
behavior, no synthetic sink behavior, no queue-dynamics beyond the accepted drop/coalesce/lossless rules,
and no presentation or storage.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013 core types → T015 provider composition
   → T019 bounded activation-plan decode → T021 declared observation layer (this baseline)
   → T022 bounded retention + applied validity effect (this document)
   → T023 synthetic sink → T024 observation matrix
   → { T-XDL consumed, T-STIM } → T-INTG (T035–T038) → T-REVIEW (T039/T041)
```

T022 is a **production-path** slice: the deterministic gate requires at least one changed
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
   ┌──────────────── T022 retention boundary (src/xverse/xcom, xverse::xcom) ──────────────┐
   │  observation.hpp/cpp                                                                    │
   │    producer seam    ObservationHub::reserve/commit/cancel (claim before provider)         │
   │    retention layer  drop_newest · coalesce_latest · lossless_validation                   │
   │    validity layer   ObservationValidityState (valid<degraded<invalid) + applied effect    │
   │    reporting layer  ObservationSnapshot::validity_state + accepted counters/marker         │
   │    authority layer  ObservationTapHandle · acknowledge/detach/recreate interval rules     │
   └────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │ counters + realized validity status (value-owned)
   ┌────────────────────────────────────▼──────────────────────────────────────────────────┐
   │  consumers: T023 synthetic sink, T024 observation matrix, T032/T033 contract suites       │
   └────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T22-XB-1` Loss visibility vs normal route | per-tap counters and realized validity status | the normal provider queue, ordering, and delivery outcome | A matching loss is counted and reflected in validity status only; it never blocks, reorders, or drops a normal-route item (`XCOM-INV-02`-adjacent ownership; FR-013). |
| `T22-XB-2` Declaration vs realized status | declared `ObservationValidityEffect` and declared `overflow_policy` | realized `ObservationValidityState` and counters | The declared effect selects the realized status; no status is inferred beyond the declaration, and the lossless mode realizes at least `degraded`. |
| `T22-XB-3` Interval status vs durable validity | interval status held until acknowledgement/detach | durable experiment-result validity (Argus/Faults) | The realized status is an in-process, per-tap projection only; X-COM owns no durable validity, storage, or presentation (`T22-XB-5`). |
| `T22-XB-4` Exact authority vs observation | `ObservationTapHandle` authority | declared tap/route identity | Only the exact current handle observes, acknowledges, or detaches; declared identity confers no authority. |
| `T22-XB-5` Observation vs export/storage | normalized in-process counters and status | Argus, OpenTelemetry, files, dashboards, databases, adapters | X-COM owns no rendering, storage, query, or export; a consumer adapter is a separate capability (`XCOM-CMP-013`, deferred). |
| `T22-XB-6` Repository vs environment | committed source, tests, work products | admitted build inputs, build trees, host paths | Committed files are public-safe and offline; no ambient, network, filesystem, or process access is introduced. |

### 3.3 Prohibited elements (must remain absent)

No TCP listener, external network peer, discovery, package manager/registry, filesystem access, process
execution, legacy repository/binary access, dynamic plugin discovery, domain-specific primitive, new
admitted dependency, competing configuration language, unbounded resource, consumer callback under an
X-COM lock, or export/dashboard/storage/query behavior. These inherit the T007 global prohibitions, the
T011 envelope, the T012 build contract, ADR-0019, and the constitution.

## 4. Components

Each component maps to a unit in `unit-specifications.md`. `T22-CMP-*` names are local to this document;
the accepted `XCOM-DU-*` identifiers are the authorized design units.

### 4.1 Retention components (design unit `XCOM-DU-013`)

- **`T22-CMP-BEST-EFFORT`** — the `drop_newest` and `coalesce_latest` retention rules inside the private
  `ObservationHub::retain` path: bounded queue, FIFO order, logical-key coalescing, and the `dropped`/
  `coalesced` counter update points.
- **`T22-CMP-LOSSLESS`** — the `lossless_validation` claim path: `ObservationHub::reserve` (pre-provider
  exact claim), `commit`/`cancel` (exact single-use consumption), the private `retain` over-capacity branch,
  and the `backpressure_rejections` counter.
- **`T22-CMP-VALIDITY`** — **new** `ObservationValidityState` vocabulary plus the applied-effect rule that
  raises the realized status on every matching loss, including the lossless "at least `degraded`" rule.
- **`T22-CMP-REPORT`** — `ObservationSnapshot` extended with the **new** trailing `validity_state` field;
  the accepted counters, `backpressure_rejections`, and `experiment_validity_degraded` compatibility
  projection re-verified unchanged in meaning.
- **`T22-CMP-AUTHORITY`** — `ObservationTapHandle` and the `acknowledge`/`detach` interval rules: the
  accepted lossless-degradation reset extended to close the realized `degraded` interval while an `invalid`
  status persists; foreign/stale/closed rejection unchanged.

### 4.2 Preserved components (read-only for T022)

- **`T22-CMP-PAYLOAD`** (`XCOM-DU-012`) — the declared payload mode/bound policy, the accepted
  `omitted`/`complete`/`truncated`/`redacted` payload view states, and `PayloadSchemaState::undecoded`:
  **re-verified unchanged**; no allow-list or decoder is added.
- **`T22-CMP-SINK`** (`XCOM-CMP-011`, T023) — `SyntheticObservationSink`: re-verified unchanged.
- **`T22-CMP-DECLARATION`** (`XCOM-DU-012`) — filter matching, declared tap/route identity, and the
  immutable record projection: consumed read-only.

### 4.3 Work-product components

- **`T22-WP`** — the T022 repository-owned work-product set (`requirements.md`, `architecture.md`,
  `detailed-design.md`, `unit-specifications.md`, `verification-plan.md`, `implementation.md`,
  `internal-review.json`, and `reports/xcom-queue/t022-package.json`).

### 4.4 Consumed components (read-only)

`XCOM-CMP-006` provider composition (`reserve`/`commit` seam), `XCOM-CMP-002` X-COM Profile/schema,
`XCOM-CMP-003` activation plan, `XCOM-CMP-004` core value types, and the accepted XDL Profile schema are
consumed or matched but neither implemented nor altered by T022.

## 5. Data flow (ordered)

1. **Declare** — a consumer builds a validated `ObservationTapSpec` naming the overflow policy
   (`drop_newest`/`coalesce_latest`/`lossless_validation`), the declared validity effect, the record
   capacity, and the payload policy (T021, unchanged).
2. **Attach** — `ObservationHub::attach` claims the first free fixed slot, advances its generation, and
   resets counters, reservation state, and the realized validity status to `valid`.
3. **Reserve (lossless only)** — `reserve` claims every currently matching tap before normal provider
   submission; for a `lossless_validation` tap whose capacity is unavailable it returns
   `observation_backpressure` **before** provider mutation, increments `backpressure_rejections`, and raises
   the realized status to at least `degraded` (escalated to `invalid` under `invalidate_on_loss`).
4. **Dispatch** — the normal provider route executes unchanged; a best-effort observer never participates.
5. **Commit / retain** — `commit` consumes the exact claim and `retain` normalizes the event:
   - under capacity → append and increment `accepted`;
   - `drop_newest` at capacity → drop the new record, increment `dropped`, raise validity per the declared
     effect;
   - `coalesce_latest` at capacity → replace the newest matching-key record and increment `coalesced`, or
     drop the new record and increment `dropped`, raising validity per the declared effect;
   - `lossless_validation` at capacity → the private `retain` backpressure branch is a **non-constructible
     defensive guard** (not reachable through `reserve`/`commit`; see `detailed-design.md` §4), retained
     unchanged and uncovered.
6. **Inspect** — `snapshot` returns the accepted counters, the accepted marker, the declared identity/
   effect, and the **new** realized `validity_state` for an exact handle, copied after the lock is released.
7. **Acknowledge** — `acknowledge` closes the current interval for the exact handle: `backpressure_rejections`
   returns to zero and a `degraded` status returns to `valid`; an `invalid` status persists until detach.
8. **Detach** — `detach` closes the exact handle and discards only its retained records; a foreign, stale,
   or closed handle produces only the accepted stable outcome.

## 6. Interfaces

T022 exposes an in-process C++20 API only (no transport, no external ABI).

| Interface | Contract |
| --- | --- |
| `ObservationHub::attach(const ObservationTapSpec&)` | `noexcept`; exact `ObservationTapHandle` or a stable failure status without mutation; initializes the realized status `valid`. |
| `ObservationHub::reserve(const CommunicationItem&)` | `noexcept`; exact single-use claim or `observation_backpressure` before provider mutation; raises the realized status on a lossless rejection. |
| `ObservationHub::commit(ObservationReservation&&, const ObservationEvent&)` / `cancel` | `noexcept`; exact single-use consumption; retention applies the declared overflow policy and validity effect. |
| `ObservationHub::snapshot(const ObservationTapHandle&)` | `noexcept`; immutable snapshot with counters, the accepted marker, and the **new** realized `validity_state` for an authenticated handle only. |
| `ObservationHub::acknowledge(const ObservationTapHandle&)` | `noexcept`; closes the interval for the exact handle (degraded → valid; invalid persists); stable outcome otherwise. |
| `ObservationHub::detach(const ObservationTapHandle&)` | `noexcept`; exact close, duplicate `tap_closed`, in-flight `tap_busy`, foreign/stale `invalid_tap_handle`, unchanged. |
| `to_string(ObservationValidityState)` | static-lifetime stable external text: `"valid"`, `"degraded"`, `"invalid"`. |
| `ObservationSnapshot::validity_state` | immutable, value-owned realized-status projection valid for the snapshot lifetime. |

## 7. Concurrency and resource bounds

| Aspect | T022 decision |
| --- | --- |
| Validity/counter updates | performed under the single hub mutex in `reserve`/`retain`; no atomic and no new shared state. |
| Returned projections | `snapshot` copies the value before the lock is released; no view into hub storage escapes. |
| Callbacks | none; no consumer code is invoked under any X-COM lock (the boundary is pull-only). |
| Tap capacity | `kMaximumObservationTaps` = 8 fixed slots per hub. |
| Record capacity | `kMaximumObservationRecordsPerTap` = 16 fixed slots per tap, declared 1–16 per tap. |
| Coalescing scan | bounded by the declared capacity (≤ 16) and the exact accepted logical key; no window quota. |
| Payload bound | `kMaximumObservedPayloadBytes` = 1024 bytes copied per record; unchanged. |
| Validity status | one fixed enumerator in the snapshot; monotonic within an interval. |
| Record growth | none; no dynamic storage, unbounded queue, retry, quota, rate, timer, or wall-clock dependency. |
| Test bounds | ≤ 4 threads, ≤ 16 record slots, finite items, 4-byte fixture payloads; no wall-clock threshold. |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Fail-closed safety | a loss is counted and reflected in status; no normal-route item is emitted, blocked, or reordered by a best-effort observer | T022-SR-001…-003; NEG-01…NEG-04 (NEG-05 is a non-constructible defensive guard) |
| Bounded resources | eight tap slots, sixteen record slots, 1024-byte prefixes, one fixed validity enumerator | T022-SR-004, T022-SR-010; CHK-13 |
| Applied declared effect | the declared `validityEffect` selects the realized status; lossless realizes at least `degraded` | T022-SR-005, T022-SR-006; CHK-09, CHK-10 |
| Observable validity | the realized status is an explicit finite value with stable text on the exact-handle snapshot | T022-SR-007; CHK-09, CHK-11 |
| Exact authority | only the current generation-bound handle observes, acknowledges, or detaches; `invalid` persists across acknowledgement | T022-SR-008; CHK-10, NEG-11 |
| Concurrency safety | updates serialized by the hub mutex; copies returned after unlock; no callback | T022-SR-009; CHK-16 |
| Domain neutrality | no provider, protocol, address, domain, or product primitive; the only vocabulary added mirrors the accepted contract text `degraded`/`invalid` | T022-SR-011; CHK-17 |
| Offline safety | standard-library only; no network, ambient, filesystem, or process access | T022-SR-011; CHK-17, NEG-16 |
| Public safety | committed files carry no secret, private address, real payload, or host path | T022-SR-012; CHK-18, NEG-17 |
| Documentation | every new/changed public declaration documents ownership/lifetime/thread-safety/failure | T022-SR-013; CHK-19 |
| Governance | no accepted artifact rewritten; registers re-validated; REF-002 unchanged; payload behavior unchanged | T022-SR-014, T022-SR-016, T022-SR-017; CHK-14, CHK-20, CHK-22 |

## 9. Consistency and constraints

- **Dependency direction preserved.** T022 consumes the accepted XDL/plan declaration model and the T021
  declared observation layer; it introduces no dependency on a later slice and no adapter, storage, or
  dashboard element.
- **Domain neutrality preserved.** The only vocabulary added (`ObservationValidityState`) mirrors the
  accepted contract text "marked degraded or invalid according to its declared criterion"; no automotive or
  product primitive is introduced.
- **XDL centrality preserved.** The declared `validityEffect`/`overflow_policy` vocabulary mirrors the
  accepted declaration; T022 neither parses nor authors XDL and defines no competing configuration
  language.
- **Logical/physical separation preserved.** Validity status is a logical, per-tap projection; no address,
  provider, or transport identity enters it.
- **Argus boundary preserved.** Counters and status are normalized in-process values only; X-COM owns no
  rendering, storage, query, or presentation (`T22-XB-5`, ADR-0019).
- **Ownership preserved.** Only T022-owned observation paths, the T022 work products, and the T022 checkbox
  change; T023 keeps the sink, T024 the matrix, and no T021 declaration is weakened.
- **Maturity preserved.** The observation boundary stays a bounded prototype; executed
  sanitizer/static/Doxygen evidence, benchmarks, integration, and acceptance remain with T035–T041.

## 10. Traceability

| Architecture element | T022 requirements |
| --- | --- |
| `T22-XB-1`, `T22-CMP-BEST-EFFORT` | T022-STK-002, T022-SR-001, T022-SR-002, T022-SR-004 |
| `T22-XB-2`, `T22-CMP-LOSSLESS`, `T22-CMP-VALIDITY` | T022-SR-003, T022-SR-005, T022-SR-006 |
| `T22-CMP-REPORT` | T022-SR-007, T022-SR-014 |
| `T22-XB-4`, `T22-CMP-AUTHORITY` | T022-STK-003, T022-SR-008 |
| `T22-XB-3`, `T22-XB-5`, `T22-CMP-PAYLOAD` | T022-STK-004, T022-SR-011, T022-SR-017 |
| `T22-XB-6`, `T22-WP` | T022-STK-005, T022-SR-012, T022-SR-013, T022-SR-015, T022-SR-016 |
| `T22-CMP-SINK`, `T22-CMP-DECLARATION` | T022-SR-009, T022-SR-017 (re-verified unchanged) |
