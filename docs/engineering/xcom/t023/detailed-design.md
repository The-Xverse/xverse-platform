# T023 Detailed Design — Synthetic Sink Counters, Isolation Rules, and Failure Semantics

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T023 (capability 007, slice `T-OBS`) |
| Stage / role | plan → detailed design (pre-code) |
| Revision | 1 |
| Baseline revision | `d455c70816eb784066740427a70df9235cd1287d` |
| Affected source paths | `src/xverse/xcom/include/xverse/xcom/observation.hpp` (edit), `src/xverse/xcom/src/observation.cpp` (edit), `tests/xcom/observation/core/unit_tests.cpp` (edit), `tests/xcom/observation/integration/integration_tests.cpp` (edit); no build file |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Declaration authority | `specs/007-xcom-core/contracts/observation.md`; `specs/007-xcom-core/data-model.md`; `docs/engineering/xcom/t021/detailed-design.md`; `docs/engineering/xcom/t022/detailed-design.md` |
| Realization vocabulary | T010 `outcome_vocabulary`, `thread_safety_vocabulary` |
| Classification | Public-safe engineering work product |

The rules below are normative for the implementation stage. Every accepted baseline behavior of the
observation boundary that T023 does not own — contract version, filter matching, payload-mode and bound
validation, payload views, schema state, record self-description, declared identities, tap capacity,
authentication, exact handle outcomes, retention drop/coalesce/lossless rules, the applied declared
validity effect, the realized validity status, and the enumerated outcome vocabulary — is preserved
exactly. The new material is the synthetic sink's visible consumer counter projection and the explicit
disconnect/failure/blocking isolation rules. A conflict is resolved in favour of the accepted source and
recorded, not guessed.

## 2. Preserved baseline behavior (must remain byte-identical)

| Area | Preserved rule |
| --- | --- |
| Contract version | `kObservationContractVersion == "1.0.0"`; any other declared version is rejected by `create`. |
| Payload modes | `metadata_only` (default) → `omitted`, zero bytes; `bounded_prefix` → `complete`/`truncated`, never more than the declared bound; `redacted` → `redacted`, zero bytes. |
| Schema status | `PayloadSchemaState::undecoded` for every record; no decoder is introduced. |
| Payload allow-list | not implemented; `payloadAccess: allow-listed` identity allow-listing is unchanged/absent (T023-SR-013). |
| Overflow vocabulary | `drop_newest`, `coalesce_latest`, `lossless_validation`; unknown → no policy value. |
| Validity vocabulary | `ObservationValidityEffect` (`none`, `degrade_on_loss`, `invalidate_on_loss`), `ObservationValidityState` (`valid < degraded < invalid`), and the applied raising rule; unchanged. |
| Capacity | `kMaximumObservationTaps == 8`; `kMaximumObservationRecordsPerTap == 16`; declared capacity 1…16; `kMaximumObservedPayloadBytes == 1024`. |
| Attach/authentication | first free fixed slot; generation advanced by one; counters, reservation, claim, validity state, and realized status reset; exact hub instance, slot in `1…8`, matching generation, occupied slot; full registry → `tap_capacity_exhausted`. |
| Coalescing key | the exact accepted logical key; insertion-order newest-match scan; unchanged. |
| Counter meanings | `accepted`, `dropped`, `coalesced`, `backpressure_rejections`, `queued` keep their accepted meanings and update points; `ObservationSnapshot` fields unchanged. |
| Handle outcomes | `accepted`, `invalid_argument`, `tap_capacity_exhausted`, `record_capacity_exhausted`, `invalid_tap_handle`, `invalid_reservation`, `tap_closed`, `tap_busy`, `observation_backpressure`, `no_record`, `sink_disconnected`; **no new outcome value is added**. |
| Sink surface | the constructor, `connect`, `disconnect`, `pull`, `connected` keep their accepted signatures and observable results. |
| Sink copy semantics | the sink remains copy-constructible and non-assignable; the hub pointer and exact handle are copied. |
| Concurrency | hub mutation and pull serialized by one mutex; returned records/snapshots copied after unlock; no callback. |

## 3. Visible consumer counters (`T23-CMP-SINK-COUNTERS`, `XCOM-DU-013`, `XCOM-CMP-011`)

### 3.1 Counter vocabulary (new)

```cpp
struct SyntheticSinkCounters final {
  std::uint64_t pulled{0U};        ///< Records successfully pulled and returned to the caller.
  std::uint64_t empty{0U};         ///< Pulls that found no retained record (`no_record`).
  std::uint64_t disconnected{0U};  ///< Pulls rejected by a local disconnect (`sink_disconnected`).
  std::uint64_t failed{0U};        ///< Pulls rejected for a stale/foreign/closed handle (`invalid_tap_handle`).
};
```

The vocabulary names only generic pull outcomes. It introduces no configuration vocabulary and no
domain-specific primitive, and it **does not** duplicate or reinterpret the tap loss counters
(`accepted`, `dropped`, `coalesced`, `backpressure_rejections`, `queued`), which remain on
`ObservationSnapshot`.

### 3.2 Counter update rule

`SyntheticObservationSink::pull()` updates exactly one counter per call, on the actual outcome:

```text
if not connected_:
  ++counters_.disconnected; return sink_disconnected          # no poll, no record consumed
result = hub_->poll(handle_)
if result.status.succeeded():
  ++counters_.pulled; return result                            # value-owned record
if result.status.outcome == no_record:
  ++counters_.empty; return result
++counters_.failed; return result                              # invalid_tap_handle
```

The accounting identity `pulled + empty + disconnected + failed == number of sink pull() calls` holds for
every sink, and no counter changes on any call other than `pull()`. `connect()` and `disconnect()` never
modify the counters; `disconnect()` only clears the local flag. `counters()` returns a value copy.

### 3.3 Ownership, lifetime, and mutation

- The projection is **owned by the sink** and copied out by value; it is not a reference into hub storage.
- It is monotonic over the sink's lifetime and is discarded with the sink; it is **not** a durable log and
  is not persisted (T023-LIM-02).
- It is written only by the sink's own calls on the calling thread; concurrent use of a single sink is not
  supported (the accepted precondition of the sink surface).

## 4. Disconnect and failure isolation (`T23-CMP-ISOLATION`)

### 4.1 Local disconnect rule

1. `disconnect()` clears only this sink's `connected_` flag. It does **not** call the hub, detach a tap,
   acknowledge an interval, or clear retained records.
2. A subsequent `pull()` returns the accepted stable `sink_disconnected`, increments `disconnected`, and
   leaves the tap's `size`, retained records, and every tap counter unchanged.
3. Other sinks on the same hub and the normal route are unaffected: a second sink attached to the same tap
   can still pull, and the provider route can still accept submissions.

### 4.2 Reconnect rule

1. `connect()` calls the const authentication path (`hub_->snapshot(handle_)`):
   - a valid exact current handle → `connected_` is set and `accepted` is returned;
   - an invalid, foreign, stale, or closed handle → `connected_` stays/becomes false and
     `invalid_tap_handle` is returned; no tap is mutated.
2. `connect()` never modifies the counters.

### 4.3 Failure rule (observer removal / slot recreation)

1. A sink holds a copy of the exact handle issued at construction. If the observed tap is later detached or
   its slot is recreated, that copied handle becomes stale.
2. A `pull()` on a still-connected sink then returns the accepted stable `invalid_tap_handle` and
   increments `failed`; the observed tap's slot (if recreated) and every unrelated tap are unchanged, and
   the observed tap's counter/validity state is not reset or otherwise mutated.
3. A handle issued by a different hub is foreign for this sink's hub and yields the same stable failure
   outcome; no slot in either hub is mutated.
4. Failure is reported with the accepted `invalid_tap_handle`; **no new `ObservationOutcome` value and no
   failure-injection API** is introduced (T023-LIM-04, T023-SR-016).

### 4.4 Blocking (non-pulling) isolation rule

1. A connected sink that does not call `pull()` has no effect on submissions: the normal route accepts,
   orders, and delivers independently of the sink.
2. The observed tap's queue remains within its declared capacity `1…16`; when it saturates, the accepted
   `drop_newest`/`coalesce_latest` rules apply and the deterministic `dropped`/`coalesced` counters become
   visible through `ObservationHub::snapshot` (SC-004).
3. The sink's counters are unchanged until it pulls; a later pull observes only the records still retained
   (loss is visible through the tap counters, not hidden).

## 5. Failure semantics

| Condition | Layer | Outcome |
| --- | --- | --- |
| connected pull finds a retained record | `SyntheticObservationSink::pull` → `ObservationHub::poll` | `accepted`; value-owned record; `pulled` + 1 |
| connected pull finds no retained record | `pull` → `poll` | `no_record`; no record; `empty` + 1 |
| connected pull after the tap is detached/recreated or with a foreign handle | `pull` → `poll` | `invalid_tap_handle`; no record; `failed` + 1; no tap/route mutation |
| pull while locally disconnected | `pull` | `sink_disconnected`; no `poll`; no record; `disconnected` + 1 |
| `connect()` on a valid exact handle | `connect` | `accepted`; sink enabled; counters unchanged |
| `connect()` on an invalid/foreign/stale/closed handle | `connect` | `invalid_tap_handle`; sink disabled; no tap mutation |
| `disconnect()` | `disconnect` | local no-op on the tap; sink disabled; counters unchanged |
| connected sink never pulls while the route saturates | hub `retain` | route unaffected; tap bounded; `dropped`/`coalesced` visible on the snapshot |

No condition in this slice produces an unvalidated value, a silent default, an inferred success, a counter
raised without a matching pull outcome, an emitted normal-route item, or a mutation of a tap or route by the
sink.

Negative-case mapping (`verification-plan.md` §5): counter accounting → NEG-01, NEG-02; disconnect/reconnect
→ NEG-03; stale/foreign/closed handle → NEG-04, NEG-05; blocking/saturation visibility → NEG-06, NEG-07;
read-only authority → NEG-08; concurrency/callback → NEG-09; boundary/offline/public-safety →
NEG-10, NEG-11; additivity/vocabulary/maturity → NEG-12, NEG-13.

## 6. Bounds

| Resource | Bound | Declared in |
| --- | --- | --- |
| sink consumer counters | four fixed 64-bit values (`pulled`, `empty`, `disconnected`, `failed`) | `SyntheticSinkCounters` |
| sink copied handle | three 64-bit opaque fields | `ObservationTapHandle` |
| sink local state | one bool, one non-owning hub pointer | `T23-CMP-SINK` |
| tap slots per hub | 8 | `kMaximumObservationTaps` |
| record slots per tap | 1–16 | `kMaximumObservationRecordsPerTap` / declared capacity |
| payload view per record | 0 or 1–1024 bytes | `kMaximumObservedPayloadBytes` |
| duration / retry / rate / quota | none; no rate limiter, timer, retry, or quota | T023-SR-009 |
| dynamic allocation | none on any T023 path | T023-SR-009 |

## 7. Concurrency and thread-safety rules

- Each sink call executes through the hub's single mutex for its tap; `pull()` is a serialized `poll`.
- The consumer counters are updated on the calling thread only; `counters()` returns a value copy and adds
  no shared mutable state to the hub. A single sink must not be used concurrently by multiple threads
  (accepted sink precondition); distinct sinks remain independent.
- `connect()`, `disconnect()`, `pull()`, `connected()`, and `counters()` are `noexcept`; no view into hub or
  sink storage escapes.
- No consumer callback exists anywhere in the boundary, so no user code runs under an X-COM lock.
- The sink never acquires, holds, or releases a hub authority it does not own: it holds a non-owning hub
  reference and a copied exact handle only.

## 8. Documentation and public-safety design

- Every new/changed public declaration (`SyntheticSinkCounters`, its four fields, and
  `SyntheticObservationSink::counters()`, plus the updated `pull`/`connect`/`disconnect` contract) carries
  Doxygen in the `xcom_obs` group with `@brief` plus the applicable `@ownership`, `@lifetime`,
  `@thread_safety`, and `@failure` tags; the file block and `@par Traceability` note are updated to name
  `XCOM-SW-OBS-004` and the T023 work products. The admitted documentation configuration is not weakened
  (strict mode stays `DOX-GAP-01`, owned by T011/T037).
- Committed work products and tests contain no payload content, no credential, no private address, no
  environment-specific absolute host path, and no sensitive deployment value; fixture bytes stay synthetic
  and bounded (≤ 4 bytes in the unit fixture). Evidence names admitted inputs by name only.

## 9. Compatibility and additivity rules

- `SyntheticSinkCounters` is a new value type; `SyntheticObservationSink` gains one trailing public
  accessor and four private counter members. No existing signature, enumerator, outcome value, target,
  test name, label, or expected result is removed, renamed, reordered, or weakened; no binary ABI is
  promised (source-level contract only).
- The sink remains copy-constructible and non-assignable; copying copies the counters. No aggregate
  initialization of the sink exists (it has a user-declared constructor), so no call site changes.
- The accepted T021/T022 declaration, retention, validity, payload, record, handle, and vocabulary behavior
  is byte-identical; the integration `test_support.hpp` helper and the existing `test_best_effort_isolation`
  assertions are unchanged.
- No external dependency, header, or build-file change is required.

## 10. Traceability

| Design element | Requirements | Planned tests |
| --- | --- | --- |
| §3.1–§3.2 counter vocabulary and update rule | T023-SR-001, T023-SR-002 | `test_synthetic_sink_visible_counters` |
| §3.3 ownership/lifetime | T023-SR-001, T023-SR-009 | `test_synthetic_sink_visible_counters` |
| §4.1 local disconnect | T023-SR-003 | `test_synthetic_sink_disconnect_isolation`, `test_synthetic_sink_route_isolation_counters` |
| §4.2 reconnect | T023-SR-005 | `test_synthetic_sink_disconnect_isolation`, `test_synthetic_sink_failure_isolation` |
| §4.3 failure (stale/foreign/closed) | T023-SR-004, T023-SR-007 | `test_synthetic_sink_failure_isolation`, `test_synthetic_sink_route_isolation_counters` |
| §4.4 blocking isolation | T023-SR-006 | `test_synthetic_sink_blocking_isolation` |
| §5 failure semantics | T023-SR-003…-007, T023-SR-016 | the four unit cases and the integration case |
| §6–§7 bounds/concurrency | T023-SR-008, T023-SR-009 | `test_synthetic_sink_concurrency` (preserved), source inspection |
| §8 documentation/public safety | T023-SR-011, T023-SR-012 | CHK-18, CHK-19 |
| §9 compatibility/additivity | T023-SR-013, T023-SR-014, T023-SR-015 | CHK-14, CHK-20, CHK-21, CHK-22 |
