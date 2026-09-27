# T021 Detailed Design — Declared Observation Policy, Filter, Record, and Authority Rules

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T021 (capability 007, slice `T-OBS`) |
| Stage / role | plan → detailed design (pre-code) |
| Revision | 1 |
| Baseline revision | `8e3c4cf6a127e094cd1aecaee2b46024c7c9bcda` |
| Affected source paths | `src/xverse/xcom/include/xverse/xcom/observation.hpp` (edit), `src/xverse/xcom/src/observation.cpp` (edit), `tests/xcom/observation/core/unit_tests.cpp` (edit), `tests/xcom/observation/integration/test_support.hpp` (edit), `tests/xcom/observation/integration/integration_tests.cpp` (edit); no build file |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Declaration authority | `xdl/profiles/xcom-v0.1.schema.json` `observation-policy`; `src/xverse/xcom/contracts/v1/activation-plan.schema.json` `observationPoint`; `specs/007-xcom-core/contracts/observation.md`; `specs/007-xcom-core/data-model.md` |
| Realization vocabulary | T010 `bound_kind_vocabulary`, `overflow_policy_vocabulary`, `outcome_vocabulary`, `thread_safety_vocabulary` |
| Classification | Public-safe engineering work product |

The rules below are normative for the implementation stage. Every accepted baseline behaviour of the
observation boundary — version check, filter matching, payload-mode and bound validation, record capacity,
overflow vocabulary, attach/authentication/generation/capacity, retention drop/coalesce/lossless rules,
counter updates, snapshot, acknowledgement, detach, sink behaviour, and the enumerated outcome vocabulary —
is preserved exactly. The new material is the declared observation-point identity, the declared
filter-constraint accessors, the declared validity-effect vocabulary, the self-describing immutable record,
and the declared identity/validity effect in the snapshot. A conflict is resolved in favour of the accepted
source and recorded, not guessed.

## 2. Preserved baseline behaviour (must remain byte-identical)

| Area | Preserved rule |
| --- | --- |
| Contract version | `kObservationContractVersion == "1.0.0"`; a declaration with any other version is rejected. |
| Filter matching | Each declared constraint constrains only when present; `matches()` returns true exactly when every declared constraint is satisfied. |
| Payload modes | `metadata_only` (default) → `PayloadViewState::omitted`, zero bytes; `bounded_prefix` → `complete` when the source fits, otherwise `truncated`, never more than the declared bound; `redacted` → `PayloadViewState::redacted`, zero bytes. |
| Schema status | `PayloadSchemaState::undecoded` for every record; no decoder is introduced. |
| Overflow vocabulary | `drop_newest`, `coalesce_latest`, `lossless_validation`; unknown → no policy value. |
| Capacity | `kMaximumObservationTaps == 8`; `kMaximumObservationRecordsPerTap == 16`; declared capacity 1…16; `kMaximumObservedPayloadBytes == 1024`. |
| Attach | First free fixed slot; generation advanced by one; counters, reservation, claim, and degraded markers reset; full registry → `tap_capacity_exhausted`; exhausted generation → `tap_capacity_exhausted`. |
| Authentication | Exact hub instance, tap slot in `1…8`, matching generation, and an occupied slot are all required. |
| Retention | `drop_newest` drops the new record and increments `dropped`; `coalesce_latest` replaces the newest queued record with an identical logical key or drops the new record; `lossless_validation` over capacity increments `backpressure_rejections` and sets the degraded marker. |
| Counters | `accepted`, `dropped`, `coalesced`, `backpressure_rejections`, `experiment_validity_degraded`, `queued` keep their exact meanings and update points. |
| Handle outcomes | `accepted`, `invalid_argument`, `tap_capacity_exhausted`, `record_capacity_exhausted`, `invalid_tap_handle`, `invalid_reservation`, `tap_closed`, `tap_busy`, `observation_backpressure`, `no_record`, `sink_disconnected`; **no new outcome value is added**. |
| Concurrency | Hub mutation and pull serialized by one mutex; returned records/snapshots copied after unlock; no callback. |

## 3. Filter declaration rules (`T21-CMP-FILTER`, `XCOM-DU-012`)

### 3.1 Declared constraint vocabulary (unchanged)

| Field | Type | Constraint |
| --- | --- | --- |
| `contract_id` | `std::optional<Identity>` | empty view → unconstrained; non-empty → must be a valid `Identity` |
| `interface_id` | `std::optional<Identity>` | as above |
| `endpoint_id` | `std::optional<Identity>` | as above |
| `route_id` | `std::optional<Identity>` | as above; when present it **is** the declared logical route point (T021-SR-003) |
| `provider_id` | `std::optional<Identity>` | as above |
| `interaction_kind` | `std::optional<InteractionKind>` | absent → unconstrained |
| `origin` | `std::optional<OriginKind>` | absent → unconstrained |

`Identity` validation is the accepted T013 rule: 1–128 bytes, no ASCII control byte (`0x00`–`0x1F`,
`0x7F`), no leading or trailing ASCII whitespace, byte-for-byte and locale-independent.

### 3.2 New declared-constraint accessors

`ObservationFilter` gains read-only accessors returning the owned declaration:
`contract_id()`, `interface_id()`, `endpoint_id()`, `route_id()`, `provider_id()` (each
`const std::optional<Identity>&`), `interaction_kind()` and `origin()` (each
`std::optional<InteractionKind>` / `std::optional<OriginKind>` by value). An unconstrained field returns
`std::nullopt`. The accessors are `noexcept`, return owned storage or values only, and expose no caller
view. `matches()` and the private constructor are unchanged.

## 4. Tap policy rules (`T21-CMP-SPEC`, `XCOM-DU-012`)

### 4.1 Declared fields and validation order

`ObservationTapSpecInput` keeps its name and gains the mandatory declared observation point immediately
after the version and the declared validity effect at the end:

```cpp
struct ObservationTapSpecInput final {
  std::string_view contract_version;                 ///< must equal kObservationContractVersion
  std::string_view tap_id;                           ///< NEW: declared observation-point identity
  ObservationFilterInput filter;                     ///< unchanged
  ObservationPayloadMode payload_mode{ObservationPayloadMode::metadata_only};
  std::size_t maximum_payload_bytes{0U};
  std::size_t record_capacity{0U};
  ObservationOverflowPolicy overflow_policy{ObservationOverflowPolicy::drop_newest};
  ObservationValidityEffect validity_effect{ObservationValidityEffect::none};  ///< NEW
};
```

`ObservationTapSpec::create` validates in this fixed order and returns `std::nullopt` on the first
violation; it exposes no diagnostic object (the accepted boundary reports a rejected declaration as an
absent value, unlike the T013 `Result<T>` model), so no new outcome or diagnostic code is added:

1. `contract_version` is a valid `SemanticVersion` **and** equals `kObservationContractVersion`;
2. `tap_id` is a valid `Identity` (non-empty, in-bound, no control byte, no leading/trailing whitespace);
3. `filter` satisfies `ObservationFilter::create`;
4. `payload_mode` is one of the three declared values;
5. `overflow_policy` is one of the three declared values;
6. `1 ≤ record_capacity ≤ kMaximumObservationRecordsPerTap`;
7. `validity_effect` is one of the three declared values;
8. the payload bound matches the mode: `bounded_prefix` requires
   `1 ≤ maximum_payload_bytes ≤ kMaximumObservedPayloadBytes`; `metadata_only` and `redacted` require
   `maximum_payload_bytes == 0`.

### 4.2 Declared observation point and route point

| Declared element | Accessor | Rule |
| --- | --- | --- |
| `tap_id` | `declared_tap_id() -> const Identity&` | mandatory; correlation label for the declared observation point realized by the tap; **not** authority, **not** unique (multiple observers may share it, T021-SR-013) |
| declared route point | `declared_route_point() -> const std::optional<Identity>&` | exactly `filter().route_id()`; no separate field exists, so a contradictory attachment point is structurally impossible |
| `contract_version` | `contract_version() -> const SemanticVersion&` | unchanged, the exact accepted observation-contract version |

### 4.3 Payload-policy vocabulary mapping (no renaming)

| Accepted declaration | Accepted contract mode | Realized type / value | Notes |
| --- | --- | --- | --- |
| `payloadAccess: metadata-only` | `metadata-only` | `ObservationPayloadMode::metadata_only` | default; zero payload bytes (invariant `XCOM-INV-06`) |
| `payloadAccess: allow-listed` | `controlled-payload` | `ObservationPayloadMode::bounded_prefix` for a prefix view, or an explicit withhold declaration realized as `ObservationPayloadMode::redacted` | explicit mode **and** explicit bound required; identity allow-listing is **not** implemented (T021-LIM-04, T022) |
| `bounds.maxPayloadBytes` | mode bound | `maximum_payload_bytes` ∈ 1…1024 for a prefix view, else 0 | over-bound request rejected |
| `bounds.maxRateHz` | rate bound | not implemented in T021 | allocated to the bounded-best-effort work (T022) |
| `validityEffect` | validity reporting | `ObservationValidityEffect` (§4.5) | declared and reported only in T021 |
| lossless mode | `lossless-validation` | `ObservationOverflowPolicy::lossless_validation` | realized as an overflow policy, not as a payload mode; behaviour unchanged (T022) |

### 4.4 Overflow policy

`ObservationOverflowPolicy` keeps its three accepted enumerators and its declared meanings; the new
cross-reference note is that `coalesce_latest` replaces only a queued record whose logical key matches, and
that the key set is unchanged. T021 adds no enumerator and changes no retention rule.

### 4.5 New declared validity-effect vocabulary

| C++ enumerator | Accepted declaration | External `to_string` text |
| --- | --- | --- |
| `ObservationValidityEffect::none` | `validityEffect: none` | `"none"` |
| `ObservationValidityEffect::degrade_on_loss` | `validityEffect: degrade-on-loss` | `"degrade-on-loss"` |
| `ObservationValidityEffect::invalidate_on_loss` | `validityEffect: invalidate-on-loss` | `"invalidate-on-loss"` |

The vocabulary and text are copied from the accepted `io.xverse.xcom` `observation-policy` form, so T021
introduces no competing vocabulary and cannot accept a declaration the Profile rejects (T021-SR-007,
Constitution III). An out-of-range `enum class` value is rejected by `create`. **T021 implements no
behaviour from this declaration**: `ObservationSnapshot::experiment_validity_degraded` keeps its exact
accepted meaning, and applying degrade/invalidate semantics is T022 (T021-LIM-03).

## 5. Immutable record rules (`T21-CMP-RECORD`, `XCOM-DU-012`)

### 5.1 Fields

`ObservationRecord` keeps every accepted field and accessor (contract identity/version, interface,
endpoint, schema identity/version, interaction kind, origin, source timestamp and clock domain, observation
timestamp and clock domain, optional sequence, correlation, causation, route, provider, source payload
size, provider outcome, payload view state, payload schema state, bounded payload bytes) and gains:

| New element | Type | Meaning |
| --- | --- | --- |
| `tap_id()` | `const Identity&` | declared observation-point identity of the producing tap (data-model "tap identity") |
| `counters()` | `const ObservationRecordCounters&` | retention-time queue-counter projection (data-model "queue counters") |

```cpp
struct ObservationRecordCounters final {
  std::size_t queued{0U};        ///< records retained at the moment of retention
  std::uint64_t accepted{0U};    ///< accepted records at the moment of retention
  std::uint64_t dropped{0U};     ///< dropped records at the moment of retention
  std::uint64_t coalesced{0U};   ///< coalesced records at the moment of retention
};
```

### 5.2 Construction discipline

- A record is constructible only by `ObservationHub` (private constructor, `friend class ObservationHub`);
  a consumer cannot forge a record.
- The declared `tap_id` is copied from the authenticated tap slot's policy, so a record can never carry a
  tap identity that did not produce it.
- Counters are stamped **after** the unchanged retention rule has updated them: a newly retained record
  carries the post-retention `queued`/`accepted`/`dropped`/`coalesced` values; a coalesced replacement
  carries the post-replacement values. A record that is dropped or rejected by backpressure is never
  constructed, so no counter stamp exists for it.
- Records remain value-owned copies with a bounded 1024-byte payload buffer; no view into hub storage is
  retained and `poll` returns a copy after the hub lock is released.

## 6. Reporting rules (`T21-CMP-REPORT`)

`ObservationSnapshot` keeps `handle`, `queued`, `accepted`, `dropped`, `coalesced`,
`backpressure_rejections`, and `experiment_validity_degraded`, and gains two trailing fields:

```cpp
struct ObservationSnapshot final {
  ObservationTapHandle handle;                                   ///< exact current authority
  /* ... accepted baseline counter fields unchanged ... */
  Identity declared_tap_id;                                      ///< NEW: declared observation point
  ObservationValidityEffect validity_effect{ObservationValidityEffect::none};  ///< NEW
};
```

`snapshot()` returns `std::nullopt` for an invalid, foreign, stale, or closed handle, exactly as before.
The tap lifecycle state model `declared → attached → active → degraded → detached` is realized as: a
validated `ObservationTapSpec` (declared); an occupied slot reached by an exact handle
(attached/active); `experiment_validity_degraded == true` (degraded); a freed slot where the same handle
reports `tap_closed` or `invalid_tap_handle` (detached). T021 adds no new lifecycle enumerator.

## 7. Authority rules (`T21-CMP-AUTHORITY`)

- `ObservationTapHandle` remains an opaque, copy-constructible, non-assignable value carrying only hub
  instance, tap slot, and generation; T021 adds **no** accessor to it (the declared identity is reported
  through the policy, record, and snapshot, `T21-XB-2`).
- `poll`, `snapshot`, `acknowledge`, and `detach` require the exact current handle; foreign, stale, or
  closed handles produce only the accepted stable outcomes with no unrelated mutation.
- `detach` preserves its exact behaviour: duplicate close → `tap_closed`; in-flight claim → `tap_busy`
  with no slot mutation; on success only that slot's records are discarded.
- Tap capacity and generation behaviour are unchanged; a recreated slot has a new generation and the old
  handle is stale.

## 8. Failure semantics

| Condition | Layer | Outcome |
| --- | --- | --- |
| malformed or empty declared observation-point identity | `ObservationTapSpec::create` | no policy value (`std::nullopt`); no partial declaration |
| malformed non-empty filter constraint | `ObservationFilter::create` | no filter value |
| declaration version ≠ `"1.0.0"` | `ObservationTapSpec::create` | no policy value |
| unknown payload mode, overflow policy, or validity effect | `ObservationTapSpec::create` | no policy value |
| prefix bound 0, > 1024, or non-zero on a non-prefix mode; record capacity 0 or > 16 | `ObservationTapSpec::create` | no policy value |
| no free tap slot / exhausted slot generation | `ObservationHub::attach` | `tap_capacity_exhausted`; no mutation |
| invalid event observation clock domain or mismatched reserved item | `commit` | `invalid_argument` / `invalid_reservation`; no retention |
| invalid, foreign, stale, or closed handle | poll/snapshot/acknowledge/detach | `invalid_tap_handle` / `no_record` / `tap_closed` / absent snapshot; no unrelated mutation |
| lossless capacity unavailable before provider mutation | `reserve` | `observation_backpressure`; provider not invoked |
| full queue under `drop_newest`, or coalesce with no matching key | `retain` | `accepted` with `dropped` incremented; the retained records are unchanged |
| disconnected synthetic sink | `SyntheticObservationSink::pull` | `sink_disconnected`; no route effect |

No condition in this slice produces an unvalidated value, a silent default, an inferred success, or an
emitted normal-route item.

Negative-case mapping (`verification-plan.md` §5): malformed/absent declared identity and version → NEG-01…NEG-04;
filter validation → NEG-04, NEG-05; payload mode, bound, and capacity → NEG-06…NEG-08; overflow policy →
NEG-09; validity effect → NEG-10; handle authority → NEG-11…NEG-13; capacity → NEG-14; lossless
backpressure → NEG-15; drop/coalesce retention → NEG-16, NEG-17; event and reservation validity → NEG-18;
lifetime/callback → NEG-19; boundary, offline, public-safety, and governance probes → NEG-20…NEG-24.

## 9. Bounds

| Resource | Bound | Declared in |
| --- | --- | --- |
| declared observation-point identity | 1–128 bytes | `Identity` (T013) |
| tap slots per hub | 8 | `kMaximumObservationTaps` |
| record slots per tap | 1–16 | `kMaximumObservationRecordsPerTap` / declared capacity |
| payload view per record | 0 or 1–1024 bytes | `kMaximumObservedPayloadBytes` |
| record payload state | four declared states (`omitted`, `complete`, `truncated`, `redacted`) | `PayloadViewState` |
| record counter projection | four fixed `size_t`/`uint64_t` values | `ObservationRecordCounters` |
| duration / retry / quota / rate | none; the boundary has no timer, retry, rate, or quota | T021-SR-015 |
| dynamic allocation | none on any T021 path | T021-SR-015 |

## 10. Concurrency and thread-safety rules

- `ObservationFilter::create`, `ObservationTapSpec::create`, and every new accessor are `noexcept`, pure
  with respect to shared state, and operate only on call-local or owned immutable storage.
- The hub remains the only shared mutable state: one mutex guards every slot operation; counter updates
  and record retention happen inside that critical section; the returned record/snapshot is copied before
  the lock is released.
- No consumer callback exists anywhere in the boundary, so no user code runs under an X-COM lock.
- Two taps may declare the same observation point and are independent slots with independent generations
  and counters; a tap identity never selects a slot.

## 11. Documentation and public-safety design

- Every new/changed public declaration carries Doxygen in the `xcom_obs` group with `@brief` plus the
  applicable `@ownership`, `@lifetime`, `@thread_safety`, and `@failure` tags; the file block and
  `@par Traceability` note are updated to name `XCOM-SW-OBS-001` and the T021 work products. The admitted
  documentation configuration is not weakened (strict mode stays `DOX-GAP-01`, owned by T011/T037).
- Committed work products and tests contain no payload content, no credential, no private address, no
  environment-specific absolute host path, and no sensitive deployment value; fixture bytes stay synthetic
  and bounded (≤ 4 bytes in the unit fixture). Evidence names admitted inputs by name only.

## 12. Compatibility and additivity rules

- The change is **source-incompatible only at the `ObservationTapSpecInput` brace-initialization sites**,
  which are exactly the in-repository fixture call sites: `ObservationTapSpec::create` in
  `tests/xcom/observation/core/unit_tests.cpp` (the `make_spec` helper and three direct negative
  declarations), in `tests/xcom/observation/integration/test_support.hpp` (the `make_tap_spec` helper), and
  the one direct declaration in
  `tests/xcom/observation/integration/integration_tests.cpp`. Each is updated by adding one valid declared
  observation point so its original intent and every original assertion are preserved.
- `ObservationSnapshot` gains trailing fields; existing reads by name are unaffected.
- No existing enumerator, constant, function signature, outcome value, target, test name, label, or
  expected result is removed, renamed, reordered, or weakened; no binary ABI is promised (source-level
  contract only, `plan.md` "The first implementation composes providers explicitly").
- No external dependency, header, or build-file change is required.

## 13. Traceability

| Design element | Requirements | Planned tests |
| --- | --- | --- |
| §3 filter declaration rules | T021-SR-003, T021-SR-004 | `test_filter_declared_constraints`, `test_values_filters_and_versions` |
| §4.1–§4.2 policy and declared point | T021-SR-001, T021-SR-002, T021-SR-005…-007 | `test_declared_tap_binding`, `test_declared_tap_rejections` |
| §4.3–§4.4 vocabulary mapping | T021-SR-005, T021-SR-006 | `test_payload_policy_bounds`, `test_best_effort_overflow` |
| §4.5 validity effect | T021-SR-007 | `test_validity_effect_vocabulary` |
| §5 record rules | T021-SR-008, T021-SR-009, T021-SR-010 | `test_record_self_description`, `test_record_counter_projection` |
| §6 reporting rules | T021-SR-012 | `test_snapshot_reports_declaration` |
| §7 authority rules | T021-SR-011, T021-SR-013 | `test_exact_tap_handles`, `test_repeated_declaration_capacity` |
| §8–§10 bounds/concurrency | T021-SR-014, T021-SR-015, T021-SR-016 | `test_synthetic_sink_concurrency`, `test_competing_reservation_interleaving` |
| §11 documentation/public safety | T021-SR-018, T021-SR-019 | CHK-18, CHK-19 |
| §12 compatibility/additivity | T021-SR-020, T021-SR-021, T021-SR-022 | CHK-02, CHK-21, CHK-22, CHK-23 |
