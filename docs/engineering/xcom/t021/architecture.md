# T021 Architecture — Declared Observation Value-and-Authority Boundary

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T021 (capability 007, slice `T-OBS`) |
| Stage / role | plan → architecture |
| Revision | 1 |
| Baseline revision | `8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda` |
| Affected source paths | `src/xverse/xcom/include/xverse/xcom/observation.hpp`, `src/xverse/xcom/src/observation.cpp` (production); `tests/xcom/observation/core/unit_tests.cpp`, `tests/xcom/observation/integration/test_support.hpp`, `tests/xcom/observation/integration/integration_tests.cpp` (fixtures); no build file |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-008` observation boundary, `XCOM-CMP-011` synthetic sink and tools, `XCOM-XLC-003` observation contract, `XCOM-INV-02`, `XCOM-INV-06`, `XCOM-DGM-003`); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-012`, `XCOM-DU-013`); `docs/engineering/xcom/t015/architecture.md` (provider composition seam); ADR-0019 |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T021 is the **declared value-and-authority layer of the observation boundary**. It owns the immutable tap
policy (declared observation point, filter, payload policy, overflow policy, validity effect), the declared
filter accessors, the immutable normalized record, and the exact tap handle authority. It owns no
retention policy behaviour, no sink behaviour, and no queue-dynamics semantics.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013 core types → T015 provider composition
   → T019 bounded activation-plan decode (declared ObservationPoint model)
   → T021 observation declaration, record, and tap authority (this document)
   → T022 retention policy → T023 synthetic sink → T024 observation matrix
   → { T-XDL consumed, T-STIM } → T-INTG (T035–T038) → T-REVIEW (T039/T041)
```

T021 is a **production-path** slice: the deterministic gate requires at least one changed
`src/xverse/xcom/**` path, satisfied by `observation.hpp`/`observation.cpp`. No build file, XDL schema,
contract, provider, plan, or later-slice interface changes.

## 3. Boundary and context

### 3.1 System context

```text
   ┌──────── XDL / io.xverse.xcom Profile + activation plan (read-only, T017–T019) ────────┐
   │  observation-policy: payloadAccess · bounds{maxPayloadBytes,maxRateHz} · validityEffect │
   │  observationPoints[]: tapId · routeId · payloadAccess · validityEffect                  │
   └────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │ declared identities and vocabulary (no competing language)
   ┌──────────────── T021 declared observation boundary (src/xverse/xcom, xverse::xcom) ───┐
   │  observation.hpp/cpp                                                                    │
   │    filter layer     ObservationFilterInput · ObservationFilter(+declared accessors)      │
   │    policy layer     ObservationTapSpecInput · ObservationTapSpec · ObservationPayloadMode│
   │                     ObservationOverflowPolicy · ObservationValidityEffect                 │
   │    record layer     ObservationEvent · ObservationRecord · ObservationRecordCounters      │
   │    authority layer  ObservationTapHandle · ObservationHub(attach/poll/detach/snapshot)    │
   │    reporting layer  ObservationStatus · ObservationOutcome · ObservationSnapshot            │
   └────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │ exact handle authority + value-owned copies
   ┌────────────────────────────────────▼──────────────────────────────────────────────────┐
   │  consumers: T015 ProviderComposition (reserve/commit seam, read-only),                  │
   │  T022 retention policy, T023 synthetic sink, T024 matrix, T032/T033 contract suites      │
   └────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T21-XB-1` Declared input vs validated policy | call-scoped `ObservationFilterInput` / `ObservationTapSpecInput` views | immutable `ObservationFilter` / `ObservationTapSpec` values | A published policy is complete and validated; a rejected declaration yields `std::nullopt` and never a partial or defaulted policy. |
| `T21-XB-2` Declaration metadata vs exact authority | declared `tap_id`, declared route point, declared validity effect, counters | `ObservationTapHandle` authority | Only the exact current handle authenticates a poll, snapshot, acknowledgement, or detach; the declared identity is correlation metadata and confers no authority. |
| `T21-XB-3` Immutable projection vs hub storage | value-owned `ObservationRecord` / `ObservationSnapshot` copies | fixed hub tap/record slots | No view into hub storage escapes a call; every returned value is copied after the lock is released. |
| `T21-XB-4` Declared policy vs XDL declaration | `ObservationPayloadMode`, `ObservationOverflowPolicy`, `ObservationValidityEffect` vocabularies | the accepted `io.xverse.xcom` Profile and activation-plan declaration | The C++ vocabulary mirrors the accepted declaration textually and adds no competing value; T021 neither parses nor authors XDL. |
| `T21-XB-5` Observation vs export/storage | normalized in-process records and counters | Argus, OpenTelemetry, files, dashboards, databases, adapters | X-COM owns no rendering, storage, query, or export; a consumer adapter is a separate capability (`XCOM-CMP-013`, deferred). |
| `T21-XB-6` Repository vs environment | committed source, tests, work products | admitted build inputs, build trees, host paths | Committed files are public-safe and offline; no ambient, network, filesystem, or process access is introduced. |

### 3.3 Prohibited elements (must remain absent)

No TCP listener, external network peer, discovery, package manager/registry, filesystem access, process
execution, legacy repository/binary access, dynamic plugin discovery, domain-specific primitive, new
admitted dependency, competing configuration language, unbounded resource, consumer callback under an
X-COM lock, or export/dashboard/storage/query behaviour. These inherit the T007 global prohibitions, the
T011 envelope, the T012 build contract, ADR-0019, and the constitution.

## 4. Components

Each component maps to a unit in `unit-specifications.md`. `T21-CMP-*` names are local to this document;
the accepted `XCOM-DU-*` identifiers are the authorized design units.

### 4.1 Observation components (design unit `XCOM-DU-012`)

- **`T21-CMP-FILTER`** — `ObservationFilterInput`, `ObservationFilter::create`, `matches`, and **new**
  declared-constraint accessors for contract, interface, endpoint, route, provider, interaction kind, and
  origin.
- **`T21-CMP-SPEC`** — `ObservationPayloadMode`, `ObservationOverflowPolicy`, **new**
  `ObservationValidityEffect` (+ `to_string`), `ObservationTapSpecInput` with the **new mandatory declared
  `tap_id`** and **new declared `validity_effect`**, and `ObservationTapSpec::create` with the **new**
  `declared_tap_id()`, `declared_route_point()`, and `validity_effect()` accessors.
- **`T21-CMP-RECORD`** — `ObservationEvent`, and `ObservationRecord` extended with **new** `tap_id()` and
  `counters()` (`ObservationRecordCounters`) plus the accessors that report the observation point.
- **`T21-CMP-REPORT`** — `ObservationSnapshot` extended with the **new** declared `tap_id` and
  `validity_effect`; `ObservationStatus`/`ObservationOutcome` vocabulary re-verified unchanged.
- **`T21-CMP-AUTHORITY`** — `ObservationTapHandle` and the `ObservationHub` attach/authenticate/poll/
  snapshot/acknowledge/detach authority path, re-verified unchanged (slot generation, capacity, foreign/
  stale/closed rejection, `tap_closed`, `tap_busy`).

### 4.2 Preserved components (read-only for T021)

- **`T21-CMP-RETENTION`** (`XCOM-DU-013`, T022) — `reserve`/`commit`/`retain` drop, coalesce, lossless
  reservation, and backpressure semantics: **re-verified unchanged**; T021 only stamps the declared
  identity and the retention counters that these rules already maintain.
- **`T21-CMP-SINK`** (`XCOM-CMP-011`, T023) — `SyntheticObservationSink`: re-verified unchanged.

### 4.3 Work-product components

- **`T21-WP`** — the T021 repository-owned work-product set (`requirements.md`, `architecture.md`,
  `detailed-design.md`, `unit-specifications.md`, `verification-plan.md`, `implementation.md`,
  `internal-review.json`, and `reports/xcom-queue/t021-package.json`).

### 4.4 Consumed components (read-only)

`XCOM-CMP-006` provider composition (`reserve`/`commit` seam), `XCOM-CMP-002` X-COM Profile/schema,
`XCOM-CMP-003` activation plan, `XCOM-CMP-004` core value types, and the accepted XDL Profile schema are
consumed or matched but neither implemented nor altered by T021.

## 5. Data flow (ordered)

1. **Declare** — a consumer builds a call-scoped `ObservationFilterInput` and `ObservationTapSpecInput`
   that borrow caller-owned views, naming the declared observation point (`tap_id`), the optional route
   constraint, the payload mode and bound, the record capacity, the overflow policy, and the declared
   validity effect.
2. **Validate** — `ObservationFilter::create` validates each non-empty identity constraint, and
   `ObservationTapSpec::create` validates the single accepted contract version, the declared observation-
   point identity, the filter, the payload mode/bound, the record capacity, the overflow policy, and the
   declared validity effect; every value is copied into fixed, value-owned storage.
3. **Reject or publish** — on any violation the factory returns `std::nullopt` and exposes no policy; no
   default is substituted and no partial declaration escapes.
4. **Attach** — `ObservationHub::attach` claims the first free fixed slot, advances its generation, resets
   its counters, and returns an exact `ObservationTapHandle`; a full registry reports
   `tap_capacity_exhausted`.
5. **Reserve and commit (T022 semantics, unchanged)** — `reserve` claims matching taps before provider
   submission and `commit` retains the normalized event; T021 changes no rule here.
6. **Normalize** — `retain` builds the immutable `ObservationRecord`; T021 adds the producing tap's
   declared identity and the retention-time counter projection to that record.
7. **Pull or inspect** — `poll` returns a value-owned record and `snapshot` returns declared identity,
   declared validity effect, and counters for an exact handle only, after the hub lock is released.
8. **Consume** — later slices (T022/T023/T024, T032/T033) read the immutable accessors; the caller keeps
   the value alive for the accessor lifetime. No adapter, storage, or presentation layer is part of the
   boundary.

## 6. Interfaces

T021 exposes an in-process C++20 API only (no transport, no external ABI).

| Interface | Contract |
| --- | --- |
| `ObservationFilter::create(ObservationFilterInput)` | `noexcept`; returns an owned filter or `std::nullopt` for any malformed non-empty identity constraint. |
| `ObservationFilter::contract_id/interface_id/endpoint_id/route_id/provider_id/interaction_kind/origin` | `noexcept`; read-only declared-constraint accessors returning `std::optional`; unconstrained → `std::nullopt`. |
| `ObservationFilter::matches(const CommunicationItem&)` | `noexcept`; unchanged exact-field semantics. |
| `ObservationTapSpec::create(ObservationTapSpecInput)` | `noexcept`; returns an owned policy or `std::nullopt`; validates version, declared observation point, filter, payload mode/bound, record capacity, overflow policy, and validity effect. |
| `ObservationTapSpec::declared_tap_id/declared_route_point/validity_effect/contract_version/filter/payload_mode/maximum_payload_bytes/record_capacity/overflow_policy` | `noexcept`; immutable declared-value accessors. |
| `to_string(ObservationOutcome)`, `to_string(ObservationValidityEffect)` | static-lifetime stable external text. |
| `ObservationHub::attach(const ObservationTapSpec&)` | `noexcept`; exact `ObservationTapHandle` or a stable failure status without mutation. |
| `ObservationHub::poll(const ObservationTapHandle&)` | `noexcept`; value-owned `ObservationRecord` or a stable status. |
| `ObservationHub::snapshot(const ObservationTapHandle&)` | `noexcept`; immutable snapshot (declared identity, declared validity effect, counters, degraded marker) for an authenticated handle only. |
| `ObservationRecord::tap_id/counters` (+ accepted baseline accessors) | `noexcept`; owned immutable projection valid for the record lifetime. |

## 7. Concurrency and resource bounds

| Aspect | T021 decision |
| --- | --- |
| Declaration construction | Pure, `noexcept`, call-local; no shared mutable state, no lock, no allocation, and no partial value. |
| Hub mutation and pull | Serialized by the hub mutex; every returned record/snapshot is copied after the lock is released. |
| Callbacks | None; no consumer code is invoked under any X-COM lock (the boundary is pull-only). |
| Shared counter state | Only the accepted per-tap counters, updated under the hub mutex by the unchanged retention rules; T021 adds no new shared state and no atomic. |
| Tap capacity | `kMaximumObservationTaps` = 8 fixed slots per hub. |
| Record capacity | `kMaximumObservationRecordsPerTap` = 16 fixed slots per tap, declared 1–16 per tap. |
| Payload bound | `kMaximumObservedPayloadBytes` = 1024 bytes copied per record; `bounded_prefix` requires 1…1024; metadata-only and redacted copy zero bytes. |
| Record growth | Additive fixed fields only (one declared identity plus four counter values); no dynamic storage, no unbounded queue, no retry, no quota, no wall-clock dependency. |
| Test bounds | ≤ 4 threads, ≤ 64 iterations, finite items, 4-byte fixture payloads; no unbounded loop or wall-clock threshold. |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Fail-closed safety | every factory returns a complete validated value or `std::nullopt`; no defaulted or partial declaration | T021-SR-001, -002, -005…-007; NEG-01…NEG-10 |
| Declared boundary | a tap names its declared observation point; the declared route point has exactly one source of truth | T021-SR-002, -003; CHK-04, CHK-07 |
| Immutability | const accessors only; assignment disabled; bounded values copied on hand-off | T021-SR-010; CHK-10 |
| Exact authority | only the current generation-bound handle observes or mutates a tap | T021-SR-011; CHK-13, NEG-11…NEG-13 |
| Bounded resources | eight tap slots, sixteen record slots, 1024-byte payload prefixes, fixed record fields | T021-SR-015; CHK-14, CHK-18 |
| Concurrency safety | declaration is call-local; hub operations serialized; copies returned after unlock; no callback | T021-SR-014, -016; CHK-16 |
| Domain neutrality | no provider, protocol, address, domain, or product primitive; the only vocabulary added mirrors the accepted Profile | T021-SR-017; CHK-17 |
| Offline safety | standard-library only; no network, ambient, filesystem, or process access | T021-SR-017; CHK-17, NEG-20 |
| Public safety | committed files carry no secret, private address, real payload, or host path | T021-SR-018; CHK-18, NEG-22 |
| Documentation | every new/changed public declaration documents ownership/lifetime/thread-safety/failure | T021-SR-019; CHK-19 |
| Governance | no accepted artifact rewritten; registers re-validated; REF-002 unchanged | T021-SR-022; CHK-20, CHK-23 |

## 9. Consistency and constraints

- **Dependency direction preserved.** T021 consumes the accepted XDL/plan declaration model and the T013
  core types; it introduces no dependency on a later slice and no adapter, storage, or dashboard element.
- **Domain neutrality preserved.** The only vocabulary added (`ObservationValidityEffect`) mirrors the
  accepted `io.xverse.xcom` `validityEffect` text; no automotive or product primitive is introduced.
- **XDL centrality preserved.** Declared identities and vocabulary mirror the accepted declaration; T021
  neither parses nor authors XDL and defines no competing configuration language.
- **Logical/physical separation preserved.** Declared tap and route-point identities are logical; no
  address, provider, or transport identity enters a tap declaration or a record.
- **Argus boundary preserved.** Records are normalized in-process values only; X-COM owns no rendering,
  storage, query, or presentation (`T21-XB-5`, ADR-0019).
- **Ownership preserved.** Only T021-owned observation paths, the T021 work products, and the T021
  checkbox change; T022 keeps retention policy, T023 the sink, and T024 the matrix.
- **Maturity preserved.** The observation boundary stays a bounded prototype; executed
  sanitizer/static/Doxygen evidence, benchmarks, integration, and acceptance remain with T035–T041.

## 10. Traceability

| Architecture element | T021 requirements |
| --- | --- |
| `T21-XB-1`, `T21-CMP-SPEC` | T021-STK-001, T021-STK-002, T021-SR-001, T021-SR-002, T021-SR-005…-007 |
| `T21-XB-2`, `T21-CMP-AUTHORITY` | T021-STK-003, T021-SR-011, T021-SR-012, T021-SR-013 |
| `T21-XB-3`, `T21-CMP-RECORD`, `T21-CMP-REPORT` | T021-SR-008, T021-SR-009, T021-SR-010 |
| `T21-XB-4`, `T21-CMP-FILTER` | T021-SR-003, T021-SR-004, T021-SR-007 |
| `T21-XB-5`, `T21-STK-004` | T021-STK-004, T021-SR-017 |
| `T21-XB-6`, `T21-WP` | T021-STK-005, T021-SR-018…-022 |
| `T21-CMP-RETENTION`, `T21-CMP-SINK` | T021-SR-006, T021-SR-011, T021-SR-016 (re-verified unchanged) |
