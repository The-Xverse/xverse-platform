# T022 Detailed Design — Bounded Retention, Applied Validity Effect, and Interval Rules

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T022 (capability 007, slice `T-OBS`) |
| Stage / role | plan → detailed design (pre-code) |
| Revision | 1 |
| Baseline revision | `7be8b9718e42e58bb1a05a486ff62e520f94567c` |
| Affected source paths | `src/xverse/xcom/include/xverse/xcom/observation.hpp` (edit), `src/xverse/xcom/src/observation.cpp` (edit), `tests/xcom/observation/core/unit_tests.cpp` (edit); no build file |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Declaration authority | `xdl/profiles/xcom-v0.1.schema.json` `observation-policy` (`validityEffect`, `bounds`); `specs/007-xcom-core/contracts/observation.md`; `specs/007-xcom-core/data-model.md` |
| Realization vocabulary | T010 `overflow_policy_vocabulary`, `outcome_vocabulary`, `thread_safety_vocabulary` |
| Classification | Public-safe engineering work product |

The rules below are normative for the implementation stage. Every accepted baseline behaviour of the
observation boundary that T022 does not own — contract version, filter matching, payload-mode and bound
validation, payload views, schema state, record self-description, declared identities, tap capacity,
authentication, exact handle outcomes, sink behaviour, and the enumerated outcome vocabulary — is preserved
exactly. The new material is the applied declared validity effect, the explicit realized validity-status
vocabulary, and the interval rule that acknowledgement closes a `degraded` interval while an `invalid`
status persists. A conflict is resolved in favour of the accepted source and recorded, not guessed.

## 2. Preserved baseline behaviour (must remain byte-identical)

| Area | Preserved rule |
| --- | --- |
| Contract version | `kObservationContractVersion == "1.0.0"`; any other declared version is rejected by `create`. |
| Filter matching | each declared constraint constrains only when present; `matches()` is unchanged. |
| Payload modes | `metadata_only` (default) → `omitted`, zero bytes; `bounded_prefix` → `complete`/`truncated`, never more than the declared bound; `redacted` → `redacted`, zero bytes. |
| Schema status | `PayloadSchemaState::undecoded` for every record; no decoder is introduced. |
| Payload allow-list | not implemented; `payloadAccess: allow-listed` identity allow-listing is unchanged/absent (T022-SR-017). |
| Overflow vocabulary | `drop_newest`, `coalesce_latest`, `lossless_validation`; unknown → no policy value. |
| Capacity | `kMaximumObservationTaps == 8`; `kMaximumObservationRecordsPerTap == 16`; declared capacity 1…16; `kMaximumObservedPayloadBytes == 1024`. |
| Attach | first free fixed slot; generation advanced by one; counters, reservation, claim, and validity state reset; full registry → `tap_capacity_exhausted`. |
| Authentication | exact hub instance, tap slot in `1…8`, matching generation, and occupied slot required. |
| Coalescing key | the exact accepted logical key (contract id/version, interface, endpoint, schema id/version, interaction, origin, route, provider); insertion-order newest-match scan. |
| Counter meanings | `accepted`, `dropped`, `coalesced`, `backpressure_rejections`, `queued` keep their accepted meanings and update points. |
| Handle outcomes | `accepted`, `invalid_argument`, `tap_capacity_exhausted`, `record_capacity_exhausted`, `invalid_tap_handle`, `invalid_reservation`, `tap_closed`, `tap_busy`, `observation_backpressure`, `no_record`, `sink_disconnected`; **no new outcome value is added**. |
| Sink | `SyntheticObservationSink` connect/disconnect/pull unchanged. |
| Concurrency | hub mutation and pull serialized by one mutex; returned records/snapshots copied after unlock; no callback. |

## 3. Best-effort retention rules (`T22-CMP-BEST-EFFORT`, `XCOM-DU-013`)

### 3.1 `drop_newest`

`retain` for a full tap under `drop_newest` (unchanged except for the validity raise):

1. the new record is **not** constructed and **not** stored;
2. `dropped` is incremented by exactly one;
3. `queued` and `accepted` are unchanged;
4. the already-queued records and their FIFO order are unchanged;
5. the realized validity status is raised per the declared effect (§5), because the matching item was lost;
6. the stable outcome is `accepted` (best effort never blocks the caller).

### 3.2 `coalesce_latest`

`retain` for a full tap under `coalesce_latest`:

1. scan queued records newest-first within the declared capacity (≤ 16) for the first record whose logical
   coalescing key matches the event item;
2. **on a match**: overwrite that record with a record built from the new event, increment `coalesced` by
   one, leave `queued`, `accepted`, and `dropped` unchanged, and raise the realized validity status per the
   declared effect (the replaced record was lost);
3. **on no match**: drop the new record, increment `dropped` by one, leave every queued record unchanged,
   and raise the realized validity status per the declared effect;
4. the FIFO order of unrelated records is unchanged.

The coalescing key and the newest-match scan are the accepted baseline rules and are not redefined.

### 3.3 Bound and ordering invariant

For every tap and every policy, after any number of submissions:

```text
0 ≤ queued ≤ record_capacity ≤ kMaximumObservationRecordsPerTap (16)
accepted + dropped + coalesced == number of matching committed submissions
```

is the accounting identity (a coalesce is counted in `coalesced`, a drop in `dropped`; the retained records
remain in insertion order minus replaced/consumed entries). This identity is the primary saturation
evidence for T022 and is completed by T024.

## 4. Explicit lossless-validation rules (`T22-CMP-LOSSLESS`, `XCOM-DU-013`)

The accepted reserve/commit/cancel path is preserved exactly:

1. `reserve(item)` locks the hub and inspects every matching tap. If a matching `lossless_validation` tap
   satisfies `size + reserved_lossless ≥ record_capacity`, it increments `backpressure_rejections`, raises
   the realized validity status (§5, `required_loss = true`), sets `unavailable`, and the whole call returns
   `observation_backpressure` with **no reservation**; the normal provider must not be mutated.
2. Otherwise `reserve` claims every matching tap exactly once (generation-stamped), increments
   `active_claims`, and increments `reserved_lossless` for lossless taps, then returns an exact single-use
   `ObservationReservation`.
3. `commit` re-authenticates the exact claim and, for each claimed tap, releases the claim and calls
   `retain`. The `lossless_validation` full-at-retention branch inside `retain` (increment
   `backpressure_rejections`, raise the realized validity status with `required_loss = true`, return
   `observation_backpressure` without retaining a record) is a **defensive guard that is not constructible
   through the public protocol**: `reserve` rejects while `size + reserved_lossless >= record_capacity` and
   `commit` decrements `reserved_lossless` before `retain`, so `size + reserved_lossless <= record_capacity`
   always holds and a claimed lossless slot reaches `retain` with `size <= record_capacity - 1 <
   record_capacity`. The guard is retained for defence in depth and is **not claimed as an exercised
   behavior** (verification-plan.md §5 NEG-05).
4. `cancel` and reservation destruction release the exact claim once; a foreign, moved-from, or completed
   reservation returns `invalid_reservation` with no unrelated mutation.

## 5. Applied declared validity-effect rules (`T22-CMP-VALIDITY`, `XCOM-DU-013`)

### 5.1 Realized status vocabulary (new)

```cpp
enum class ObservationValidityState : std::uint8_t {
  valid = 0U,     ///< No declared loss has affected the observation interval.
  degraded = 1U,  ///< A declared loss degraded experiment validity.
  invalid = 2U,   ///< A declared loss invalidated experiment validity.
};
```

The numeric values encode the monotonic ordering `valid < degraded < invalid`; a comparison of two values
compares their validity strength. `to_string` returns the stable external text `"valid"`, `"degraded"`, and
`"invalid"`. The vocabulary mirrors the accepted contract text "A test result that loses required records is
marked degraded or invalid according to its declared criterion" and the accepted tap state name `degraded`;
it introduces no competing configuration vocabulary.

### 5.2 Raising rule

On every matching loss the tap's realized status is raised by one private helper (invoked under the hub
mutex):

```text
target = valid
switch (declared validity_effect):
  none                -> target = valid
  degrade_on_loss     -> target = degraded
  invalidate_on_loss  -> target = invalid
if required_loss and target < degraded:      # lossless backpressure is a declared loss
  target = degraded
if target > current_realized_status:
  current_realized_status = target          # monotonic within the interval
```

| Loss event | `required_loss` | `none` | `degrade_on_loss` | `invalidate_on_loss` |
| --- | --- | --- | --- | --- |
| `drop_newest` drop | no | `valid` | `degraded` | `invalid` |
| `coalesce_latest` replacement | no | `valid` | `degraded` | `invalid` |
| `coalesce_latest` no-match drop | no | `valid` | `degraded` | `invalid` |
| `lossless_validation` backpressure | yes | `degraded` | `degraded` | `invalid` |

The lossless "at least `degraded`" rule preserves the accepted baseline behavior that a lossless capacity
loss degrades experiment validity (docs/xcom/observation-boundary.md), so the accepted
`experiment_validity_degraded` marker is unchanged for the accepted lossless case.

### 5.3 Reporting and interval rules (`T22-CMP-REPORT`, `T22-CMP-AUTHORITY`)

- `ObservationSnapshot` gains one trailing field:
  ```cpp
  ObservationValidityState validity_state{ObservationValidityState::valid};  ///< realized declared-effect status
  ```
- The accepted `experiment_validity_degraded` field is retained and becomes the **compatibility projection**
  `validity_state != ObservationValidityState::valid`. For the accepted lossless case this yields exactly the
  accepted `true`/`false` values, so no existing assertion changes.
- `attach` resets the slot's realized status to `valid`.
- `acknowledge(exact handle)` closes the current observation-validity interval: it resets
  `backpressure_rejections` to zero and, when the realized status is `degraded`, returns it to `valid`.
  An `invalid` status is **not** cleared by acknowledgement; it persists until `detach` or slot recreation.
  A foreign, stale, or closed handle returns the accepted stable outcome and performs no reset.
- `detach` and slot recreation discard the realized status with the slot; `snapshot` reports no value for a
  foreign, stale, or closed handle.
- `T22-OPEN-01` records the `invalid`-persistence decision for review: acknowledgement is defined as closing
  a *degradation* interval (its accepted meaning), so it cannot restore an invalidated result. This is an
  interval-model decision, not a claim that lost records were recovered.

### 5.4 Relationship to the accepted data model

| Accepted element | Realization |
| --- | --- |
| `ObservationTap.validity effect` (declared) | `ObservationTapSpec::validity_effect()` (T021) selects the realized status here. |
| tap state `declared → attached → active → degraded → detached` | `degraded` realizes as `validity_state == degraded`; `invalid` is a stronger status; `detach` returns the slot to `declared`. |
| `ObservationTap.counters` | `dropped`, `coalesced`, `backpressure_rejections` unchanged; every loss is visible in both counters and status (SC-004). |
| contract "marked degraded or invalid according to its declared criterion" | §5.2 raising rule with stable text. |

## 6. Failure semantics

| Condition | Layer | Outcome |
| --- | --- | --- |
| full queue under `drop_newest` | `retain` | `accepted`; `dropped` + 1; no new record; FIFO unchanged; validity raised per declaration |
| full queue under `coalesce_latest`, matching key | `retain` | `accepted`; `coalesced` + 1; newest matching record replaced; validity raised per declaration |
| full queue under `coalesce_latest`, no matching key | `retain` | `accepted`; `dropped` + 1; no replacement; validity raised per declaration |
| lossless capacity unavailable before provider mutation | `reserve` | `observation_backpressure`; no reservation; no provider mutation; `backpressure_rejections` + 1; validity ≥ `degraded` |
| lossless full at retention after a valid claim (**non-constructible defensive guard**) | `retain` (via `commit`) | unreachable under `size + reserved_lossless <= record_capacity`; if ever reached the guard returns `observation_backpressure` with no record and validity ≥ `degraded` |
| foreign, stale, moved-from, or completed reservation | `commit`/`cancel` | `invalid_reservation`; no unrelated mutation |
| invalid event observation clock domain or item ≠ reserved item | `commit` | `invalid_argument` / `invalid_reservation`; no retention |
| invalid, foreign, stale, or closed handle | `snapshot`/`acknowledge`/`detach` | accepted stable outcome (`invalid_tap_handle` / `tap_closed` / absent snapshot); no reset or mutation |
| in-flight lossless claim at detach | `detach` | `tap_busy`; no mutation |
| no loss occurs | `snapshot` | realized status `valid`, `experiment_validity_degraded == false` |

No condition in this slice produces an unvalidated value, a silent default, an inferred success, a raised
validity status without a matching loss, or an emitted normal-route item.

Negative-case mapping (`verification-plan.md` §5): drop bound/order → NEG-01, NEG-13, NEG-14; coalesce
selection → NEG-02, NEG-03; lossless pre-dispatch and claim → NEG-04, NEG-12 (NEG-05 is the
non-constructible `retain` defensive guard argued in §4); best-effort validity
matrix → NEG-06…NEG-08; unknown declaration value → NEG-09; acknowledgement/interval → NEG-10, NEG-11;
concurrency/callback → NEG-15; boundary/offline/public-safety → NEG-16, NEG-17; additivity/maturity/payload
boundary → NEG-18, NEG-19.

## 7. Bounds

| Resource | Bound | Declared in |
| --- | --- | --- |
| tap slots per hub | 8 | `kMaximumObservationTaps` |
| record slots per tap | 1–16 | `kMaximumObservationRecordsPerTap` / declared capacity |
| coalescing scan | ≤ declared capacity (≤ 16) newest-first | §3.2 |
| payload view per record | 0 or 1–1024 bytes | `kMaximumObservedPayloadBytes` |
| realized validity status | three declared values, one enumerator | `ObservationValidityState` |
| duration / retry / rate / quota | none; no rate limiter, timer, retry, or quota | T022-SR-010 |
| dynamic allocation | none on any T022 path | T022-SR-010 |

## 8. Concurrency and thread-safety rules

- Every counter and validity update happens inside the single hub mutex in `reserve`/`retain`; the new
  `raise_realized_validity` helper is called only under that lock.
- `snapshot`, `poll`, `acknowledge`, and `detach` copy or mutate under the lock and return value-owned
  results; no view into hub storage escapes.
- `to_string(ObservationValidityState)` and the new accessors are `noexcept`, pure, and introduce no shared
  mutable state.
- No consumer callback exists anywhere in the boundary, so no user code runs under an X-COM lock.
- Two taps declaring the same observation point remain independent slots with independent counters and
  independent realized status.

## 9. Documentation and public-safety design

- Every new/changed public declaration (`ObservationValidityState`, `to_string(ObservationValidityState)`,
  `ObservationSnapshot::validity_state`) carries Doxygen in the `xcom_obs` group with `@brief` plus the
  applicable `@ownership`, `@lifetime`, `@thread_safety`, and `@failure` tags; the file block and
  `@par Traceability` note are updated to name `XCOM-SW-OBS-003` and the T022 work products. The admitted
  documentation configuration is not weakened (strict mode stays `DOX-GAP-01`, owned by T011/T037).
- Committed work products and tests contain no payload content, no credential, no private address, no
  environment-specific absolute host path, and no sensitive deployment value; fixture bytes stay synthetic
  and bounded (≤ 4 bytes in the unit fixture). Evidence names admitted inputs by name only.

## 10. Compatibility and additivity rules

- `ObservationSnapshot` gains one trailing field; existing reads by name are unaffected, and the only
  positional aggregate initialization of `ObservationSnapshot` is the single in-repository site in
  `observation.cpp::snapshot`, which is updated to append the realized status.
- The accepted `experiment_validity_degraded` field is retained with unchanged accepted values for the
  lossless case; its computation becomes the documented compatibility projection of the realized status.
- No existing enumerator, constant, function signature, outcome value, target, test name, label, or
  expected result is removed, renamed, reordered, or weakened; no binary ABI is promised (source-level
  contract only).
- The integration fixtures (`test_support.hpp`, `integration_tests.cpp`) declare the default `none` effect,
  so no edit is required and their observable behavior is unchanged.
- No external dependency, header, or build-file change is required.

## 11. Traceability

| Design element | Requirements | Planned tests |
| --- | --- | --- |
| §3.1 `drop_newest` | T022-SR-001, T022-SR-004 | `test_drop_newest_bounded_loss` |
| §3.2 `coalesce_latest` | T022-SR-002, T022-SR-004 | `test_coalesce_latest_key_selection` |
| §3.3 bound/accounting invariant | T022-SR-004 | `test_drop_newest_bounded_loss`, `test_coalesce_latest_key_selection` |
| §4 lossless | T022-SR-003 | `test_lossless_backpressure_pre_dispatch` |
| §5.1–§5.2 applied effect | T022-SR-005, T022-SR-006 | `test_validity_effect_on_best_effort_loss`, `test_validity_effect_on_lossless_backpressure` |
| §5.3 reporting/interval | T022-SR-007, T022-SR-008 | `test_validity_state_vocabulary`, `test_acknowledge_closes_validity_interval` |
| §6–§8 failure/bounds/concurrency | T022-SR-009, T022-SR-010 | `test_synthetic_sink_concurrency`, `test_competing_reservation_interleaving` (unchanged) |
| §9 documentation/public safety | T022-SR-012, T022-SR-013 | CHK-18, CHK-19 |
| §10 compatibility/additivity | T022-SR-014, T022-SR-015, T022-SR-016, T022-SR-017 | CHK-14, CHK-20, CHK-21, CHK-22 |
