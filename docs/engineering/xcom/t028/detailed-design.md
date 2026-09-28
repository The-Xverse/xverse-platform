# T028 Detailed Design — Action Path, Exclusive Lease, Bounds, Failure Semantics, and Tests

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T028 (capability 007, slice `T-STIM`) |
| Stage / role | plan → detailed design (pre-code) |
| Revision | 1 (guarded actions and exclusive service-emulation lease) |
| Baseline revision | `c518c5e4fcb2055666db25cb62018769e7f56ae4` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Accepted design unit | `XCOM-DU-018` guarded injection and exclusive service-emulation lease (component `XCOM-CMP-009`, contract `XCOM-XLC-006`, boundary `XCOM-XB-007`) |
| Classification | Public-safe engineering work product |

This design is written **before** implementation. Every constant, bound, check order, and expected value
below is a verification contract: the implementation must realize it, and weakening an expected value
requires a reviewed successor candidate.

## 2. Design principles

1. **Fail closed.** Every check that cannot be satisfied declines the action; only an authorized,
   journal-durable, single emission reports success.
2. **Decline without mutation.** A decline leaves the accepted guard state, the lease table, the pending
   queue, the lineage window, and the durable journal unchanged in the declined dimension, and emits
   nothing.
3. **Consume, do not re-implement.** The guard owns the fail-closed pre-emission decision and the journal
   owns durable intent/outcome ordering; T028 evaluates each exactly through its public surface.
4. **Exclusive emulation.** One active lease per endpoint generation and per `(endpoint, session)`, acquired
   atomically and bound to the exact session, endpoint, generation, and plan digest.
5. **Synthetic provenance always.** Every emitted item carries `OriginKind::validation_tool` and the exact
   bound identity; no path emits a differently classified item.
6. **Bounded and deterministic.** Closed vocabularies, finite queue/lease/lineage/budget, stable precedence,
   identical results and snapshots across runs; no wall-clock dependence.
7. **Additive and read-only on predecessors.** T025/T026/T027 accepted bytes are consumed read-only; the
   unit is new and authors no transport, route, provider, or gateway.
8. **Host seam for realization.** Transport is a host-supplied `ActionEmitter` seam; the accepted T-CORE
   provider boundary owns realization and T030–T034 owns the gateway.

## 3. Types and canonical vocabulary

Namespace: `xverse::xcom::validation` (the accepted `XCOM-XLC-006` family), following T025–T027. The unit
reuses `Permit`, `PermitId`, `SessionId`, `PlanDigest`, `Timestamp`, `ClockDomainId`, `Generation`, `Tag`,
`Result`, `Diagnostic`, `LifecycleState`, `is_terminal`, and `TimeAuthority` from `validation_session.hpp`
read-only; `StimulationAction`, `StimulationActionMask`, `StimulationPolicy`, `StimulationRequest`,
`ResolvedTime`, `GuardOutcome`, `GuardReason`, `GuardDiagnostic`, `StimulationGuard` from
`stimulation_guard.hpp` read-only; `StimulationJournal`, `StimulationIntent`, `StimulationOutcome`,
`OutcomeKind`, `JournalStatus` from `stimulation_journal.hpp` read-only; and `OriginKind` from the accepted
core `item.hpp` read-only. No identity, digest, diagnostic, interaction, origin, or action type is
redefined.

### 3.1 Constants

| Constant | Value | Meaning |
| --- | --- | --- |
| `kActionPathMaxPendingActions` | `64` | maximum declared pending scheduled actions |
| `kActionPathMaxLineage` | `64` | maximum declared emission-time lineage depth |
| `kActionPathMaxDrainSteps` | `64` | maximum pending actions completed by one `drain`/completion call |
| `kActionPathMaxPayloadBytes` | `4096` | maximum call-scoped payload view forwarded to the emitter |
| `kActionPathMaxActiveLeases` | `64` | maximum active service-emulation leases in one registry |

### 3.2 `ActionStatus`

Closed, deterministically ordered; declaration order is stable.

| Enumerator | Meaning |
| --- | --- |
| `Emitted` | authorized, intent durable, emitted exactly once, outcome durable |
| `Rejected` | the guard declined with a definite declared mismatch; no emission, no journal |
| `Failed` | the guard could not complete deterministically; no emission, no journal |
| `LeaseConflict` | emulation requested but the exclusive lease could not be acquired or validated |
| `Queued` | an authorized scheduled action entered the bounded pending queue |
| `Cancelled` | a pending action was cancelled by completion; no emission |
| `Expired` | a pending action lapsed under the declared late policy; no emission |
| `EvidenceIncomplete` | the intent is durable but no durable outcome exists; never success |
| `JournalFailed` | the intent append/sync failed; no emission |
| `CapacityExhausted` | a declared queue/lease bound would be exceeded; fail closed |
| `NotActive` | the addressed session is not active for the requested operation |
| `NotOpen` | the action path is closed and evaluates nothing |
| `RejectedConfiguration` | a malformed request or invalid declared configuration |
| `EmissionRejected` | authorized, intent and outcome durable, but the host rejected the descriptor; not delivered, never success |
| `EmissionUnavailable` | authorized, intent durable, but the host emission outcome is explicitly unknown; not delivered, never success |

### 3.3 `LeaseStatus`, `LeaseState`, `DrainState`, `EmissionStatus`, `CompletionOutcome`

- `LeaseStatus` (closed): `Ok`, `Conflict`, `NotFound`, `NotHeld`, `AlreadyReleased`, `SessionMismatch`,
  `GenerationMismatch`, `PlanMismatch`, `Expired`, `Quarantined`, `CapacityExhausted`,
  `RejectedConfiguration`.
- `LeaseState` (closed): `None`, `Active`, `Released`, `Quarantined`, `Expired`.
- `DrainState` (closed): `Idle`, `Draining`, `Drained`, `Cancelled`.
- `EmissionStatus` (closed): `Delivered`, `Rejected`, `Unavailable`.
- `CompletionOutcome` (closed): `None`, `Drained`, `Closed`, `Revoked`, `Expired`, `EvidenceIncomplete`.
- `OrderingRule` (closed): `ScheduledThenArrival` (order by `(scheduled_at, request_id)`), `Arrival` (order
  by `request_id`).
- `LateItemPolicy` (closed): `RejectLate` (a late action is cancelled and reported as late-rejected),
  `DiscardLate` (a late action is cancelled and counted as discarded).
- `QuarantineReason` (closed): `Conflict`, `Revocation`, `Disconnect`, `Expiry`.

Stable names and precedence are provided for every vocabulary by `*_name` helpers and a total
`precedence_rank`; `ActionStatus` declaration order is the stable reporting order.

### 3.4 `ActionPathConfig` (bounded, declared)

| Field | Type | Rule |
| --- | --- | --- |
| `max_pending_actions` | `std::size_t` | `1 … kActionPathMaxPendingActions` |
| `max_lineage_entries` | `std::size_t` | `1 … kActionPathMaxLineage` |
| `max_drain_steps` | `std::size_t` | `1 … kActionPathMaxDrainSteps` |
| `max_payload_bytes` | `std::size_t` | `1 … kActionPathMaxPayloadBytes` |
| `ordering` | `OrderingRule` | declared scheduled ordering rule |
| `late_policy` | `LateItemPolicy` | declared late-item policy |
| `late_tolerance` | `Timestamp` | non-negative bounded late tolerance in the validity domain |
| `tool` | `Tag` | valid tool tag bound into every intent |

### 3.5 `EndpointGeneration`, `EmulationLease`, `PendingAction`, `SyntheticStimulationItem`

| Type | Fields | Rule |
| --- | --- | --- |
| `EndpointGeneration` | `SessionId session`, `Tag endpoint`, `Generation generation`, `PlanDigest plan_digest` | the exact lease key; value equality over every field |
| `EmulationLease` | `EndpointGeneration key`, `std::uint64_t request_id`, `ClockDomainId domain`, `Timestamp acquired_at`, `Timestamp expires_at`, `LeaseState state` | a bounded lease value; `expires_at >= acquired_at` |
| `PendingAction` | `std::uint64_t request_id`, `authorization_token`, `StimulationAction action`, `ClockDomainId domain`, `Timestamp scheduled_at`, `bool immediate`, retained bounded `StimulationRequest request` | a bounded queued descriptor; `request_id` non-zero and the guard token identifies this request's reservation |
| `SyntheticStimulationItem` | `OriginKind origin`, `StimulationIntent intent` | `origin` is always `OriginKind::validation_tool`; payload-free |

### 3.6 `ActionDiagnostic`, `ActionPathSnapshot`, `LeaseSnapshot`, `CompletionReport`, `CompletionRequest`

| Type | Fields |
| --- | --- |
| `ActionDiagnostic` | `ActionStatus status`, `GuardReason guard_reason`, `LeaseStatus lease_status`, `JournalStatus journal_status`, `EmissionStatus emission_status`, `std::uint64_t request_id`, `Diagnostic detail` |
| `ActionPathSnapshot` | `bool open`, `std::size_t pending`, `std::size_t lineage_entries`, `std::uint64_t emitted`, `emission_rejected`, `emission_unavailable`, `rejected`, `failed`, `cancelled`, `expired`, `discarded`, `evidence_incomplete`, `lease_conflicts`, `DrainState drain_state` |
| `LeaseSnapshot` | `std::size_t active`, `released`, `quarantined`, `expired`, `std::uint64_t acquisitions`, `conflicts` |
| `CompletionRequest` | `Timestamp now`, `ClockDomainId domain`, `LifecycleState session_state` |
| `CompletionReport` | `CompletionOutcome outcome`, `std::size_t drained`, `cancelled`, `released_leases`, `quarantined_leases`, `evidence_incomplete`, `failed` |

All are bounded, payload-free values with defaulted equality.

## 4. Behaviour

### 4.1 `StimulationActionPath(config, journal, registry, emitter)`

Construction is non-owning: the accepted T026 journal, the `ServiceEmulationRegistry`, and the host
`ActionEmitter` must outlive the action path. The action path is non-copyable and non-movable, and holds
one mutex.

### 4.2 `open(permit, policy)` → `GuardStatus`

1. Validate the `ActionPathConfig` bounds of §3.4 and the tool tag. A zero/over-maximum bound or an invalid
   tag is `GuardStatus::RejectedConfiguration`; the action path remains closed and mutates nothing.
2. Delegate to the bound accepted T027 `StimulationGuard::open`; the guard validates policy/permit
   consistency. A non-`Ok` status leaves the action path closed.
3. On `Ok`, reset the pending queue, the lineage window, and the action counters, clear the metric counters,
   set `open = true`, and return `Ok`.

### 4.3 `execute(request, session_state, resolved_time, payload, out)` → `ActionStatus`

The action path evaluates in the order below; the first failing step determines `out.status`; no later step
runs.

1. **Precondition (closed).** If `!open`, set `NotOpen` and return. No mutation.
2. **Precondition (malformed).** If `request.request_id == 0` or the payload view exceeds
   `config.max_payload_bytes`, set `RejectedConfiguration` and return. No mutation.
3. **Precondition (capacity and lease identity).** For a scheduled (non-immediate) request, if the pending
   queue is full, set `CapacityExhausted` and return. For an emulation request, compute the
   `EndpointGeneration` key and classify it with the non-mutating `registry.precheck(key, ...)`; any
   non-`Ok` status sets `LeaseConflict` with that exact `LeaseStatus` and returns. No mutation, no guard
   evaluation, no journal.
4. **Precondition (session).** If `session_state != LifecycleState::active`, set `NotActive` and return. No
   mutation and no emission. (This mirrors the accepted guard's lifecycle rule and avoids queueing work for
   a non-active session; the guard is not called and consumes no quota.)
5. **Guarded decision.** Call the bound accepted T027 `StimulationGuard::authorize(request, session_state,
   resolved_time, guard_out)` exactly once, **before** any lease is acquired. If the outcome is not
   `Authorized`, set `out.guard_reason` from `guard_out.reason`, set `Rejected` for `GuardOutcome::Rejected`
   or `Failed` for `GuardOutcome::Failed`, increment the matching counter, and return. No lease is acquired
   or released, no journal record is written, and no emission occurs.
6. **Lease acquisition (emulation only).** For `EmulateService`, acquire the exclusive lease
   unconditionally through `registry.acquire(key, request.request_id, ...)`:
   - on `Ok`, record the held lease and continue;
   - on any non-`Ok` status (a concurrent second owner observes `Conflict`), set `LeaseConflict`, copy the
     lease status, and return with no mutation and no emission.
   - `InvokeService` acquires no emulation lease.
7. **Journal intent and emit once (immediate or service action).** Build the payload-free
   `StimulationIntent` from the bound permit and the request (permit/session/plan identity, request/
   correlation/causation ids, action mask, target, `config.tool`, quota cost, clock domain, scheduled
   timestamp, immediate flag). Call `journal.journal_then_emit(intent, adapter, outcome)`, where `adapter`
   builds the `SyntheticStimulationItem` with `origin = OriginKind::validation_tool` and invokes
   `emitter.emit(item, payload)` exactly once, mapping `EmissionStatus` to a
   `StimulationOutcome{request_id, kind, reason, domain, observed_at=resolved_time.value}`. Map the journal
   status (the bounded lineage window advances with `request.request_id` for any durable `Ok` intent):
   - `Ok` **and host `Delivered`** → `Emitted`.
   - `Ok` and host `Rejected` → `EmissionRejected`; durable `OutcomeKind::Rejected`, never success.
   - `Ok` and host `Unavailable` → `EmissionUnavailable`; durable `OutcomeKind::Unknown`, never success.
   - `EvidenceIncomplete` → `EvidenceIncomplete`.
   - `CapacityExhausted` → `CapacityExhausted`.
   - `RecordTooLarge` / `RejectedConfiguration` → `RejectedConfiguration`.
   - `WriteFailed` / `PartialWrite` / `CorruptRecord` → `JournalFailed`.
   - `AlreadyResolved` / `NotFound` → `RejectedConfiguration`.
   Increment the matching counter, copy `journal_status`/`emission_status` into `out`, and return.
8. **Queue (scheduled).** Insert a bounded `PendingAction` into the pending queue in the declared order and
   return `Queued`. The guard decision, the lease acquisition, and the queue insertion are committed
   together under the action-path mutex.
9. **Decline bookkeeping.** A declined step increments only the observable counters; the accepted guard
   state, lease table, pending queue, lineage window, and durable journal are unchanged in the declined
   dimension. A guard decline acquires no lease, so the lease table (including its acquisition and release
   accounting) is byte-identical.

An authorized request carries a unique guard token while queued. If a later journal admission fails
before emission, the action path removes only that token's quota/loop accounting and releases only
that request's held emulation lease. Other successful or still-pending authorizations retain their
accounting. A request identity already in the pending queue or retained journal is rejected before
authorization. Outcome timestamps carry the resolved completion domain; the intent retains the
request's original domain and scheduled timestamp.

### 4.4 `drain(request)` → `CompletionReport`

1. Validate `request.domain == permit.validity_domain()`; a mismatch is `CompletionOutcome::None` with no
   mutation (never compare raw clocks).
2. If `request.session_state` is `closed`, `expired`, `revoked`, or `evidence_incomplete`, cancel every
   pending action (`cancelled`, zero emission), release every held lease, set `DrainState::Cancelled`, and
   return the matching `CompletionOutcome`. A `closed` state whose journal reports a durable intent without
   a durable outcome returns `EvidenceIncomplete`, never `Closed`; `expired`/`revoked`/`evidence_incomplete`
   retain their terminal mapping.
3. Otherwise, if `request.session_state` is non-active and non-terminal (`declared`/`armed`), fail closed:
   cancel every pending action (`cancelled`, zero emission), leave the lease table unchanged (no action is
   authorized in that state), set `DrainState::Cancelled`, and return `EvidenceIncomplete` when the journal
   reports a durable intent without a durable outcome, else `CompletionOutcome::None`. No action is emitted.
4. Otherwise (`active` or `closing`), iterate the pending queue in the declared order for at most
   `config.max_drain_steps` actions; for each action due at `request.now` (in the validity domain):
   - if `request.now > scheduled_at + config.late_tolerance`, apply `config.late_policy`: `RejectLate`
     cancels the action as `Expired`/late-rejected (`expired`), `DiscardLate` cancels it as discarded
     (`discarded`); either way zero emission;
   - otherwise run the §4.3 step-7 journal-and-emit path (with the accepted guard not re-evaluated, because
     the action was authorized at enqueue time) and classify the result as in §4.3 step 7; a non-active
     state or a released/quarantined/expired lease for an emulation action cancels the action with zero
     emission. A due action that cannot be completed (a journal failure or a non-delivered host emission)
     increments `failed` and is surfaced, never silently dropped.
5. Set `DrainState::Drained` when the queue is empty, else `DrainState::Idle`; assign `evidence_incomplete`
   the authoritative count of durable intents without a durable outcome (which already includes a
   drain-time outcome-append failure) and return `Drained` only when the queue is empty, `failed == 0`, and
   no durable intent lacks a durable outcome; return `EvidenceIncomplete` when the queue is empty but a
   dropped action was surfaced or an incomplete intent remains, else `None` with the per-action counts.

### 4.5 `close`, `revoke`, `expire`, `mark_evidence_incomplete`

| Operation | Behaviour | Outcome |
| --- | --- | --- |
| `close(request)` | drain every due pending action within the bounded step budget, cancel the rest, release every held lease | `Closed`, or `EvidenceIncomplete` when a held intent has no durable outcome or a due action was dropped (`failed > 0`) |
| `revoke(request)` | cancel every pending action (zero emission), release every held lease | `Revoked` |
| `expire(request)` | cancel every pending action (zero emission), expire every held lease | `Expired` |
| `mark_evidence_incomplete(request)` | cancel every pending action (zero emission), release every held lease, and count every durable intent without a durable outcome from the accepted journal's recovered index | `EvidenceIncomplete` |

Each operation validates `request.domain == permit.validity_domain()` (else `CompletionOutcome::None`, no
mutation), is bounded by `config.max_drain_steps`, and returns a deterministic `CompletionReport`. A session
whose completion surfaces an evidence-incomplete intent returns `EvidenceIncomplete` and never `Closed`,
including a terminal `closed` request whose journal holds a durable intent without a durable outcome.
`close` drains and releases every held lease for an `active`/`closing` state; `drain` drains for an
`active`/`closing` state; a non-active, non-terminal state (`declared`/`armed`) fails closed by cancelling
every pending action with zero emission, leaving the lease table unchanged, and returning `None` (or
`EvidenceIncomplete` when the journal already holds a durable intent without a durable outcome).
`revoke`/`expire`/`mark_evidence_incomplete` accept any caller-supplied state and are idempotent-safe (a
second call on an empty queue and empty lease table is a no-op with the same outcome).

### 4.6 `ServiceEmulationRegistry(max_active_leases)`

1. Construction clamps/validates the capacity to `1 … kActionPathMaxActiveLeases`; zero or over-maximum is
   a rejected configuration (the constructor throws `std::invalid_argument`, following the accepted T025
   `SessionManager` construction convention).
2. `acquire(key, request_id, domain, acquired_at, expires_at)`:
   - if an `Active` lease already exists with the same `(endpoint, generation)`, return `Conflict`;
   - if an `Active` lease already exists with the same `(endpoint, session)`, return `Conflict`;
   - if the active-lease capacity is reached, return `CapacityExhausted`;
   - otherwise insert one `Active` lease and return `Ok`.
   The check-and-insert is atomic under the registry mutex.
   An active lease with the same endpoint but a differing plan digest, session, or generation is
   classified `PlanMismatch`/`SessionMismatch`/`GenerationMismatch`; a superseded generation neither
   authorizes nor conflict-blocks. `precheck(key, domain, acquired_at, expires_at)` returns the exact
   `LeaseStatus` that `acquire` would return without mutating any entry or counter, so the action path can
   classify an emulation precondition before a guard evaluation and still acquire atomically afterwards.
3. `release(key, request_id)`: an unknown key is `NotFound`; a key whose lease is not `Active` is
   `NotHeld`/`AlreadyReleased`; on success the lease becomes `Released` and the entry is retained as a
   bounded tombstone for accounting. No mutation on failure.
4. `quarantine(key, reason)`: an unknown key is `NotFound`; on success the lease becomes `Quarantined` and
   is no longer active; no mutation on failure.
5. `expire_elapsed(domain, now)`: transitions every `Active` lease whose `domain` equals `domain` and whose
   `expires_at <= now` to `Expired`; leases in another domain are never compared or ordered
   (`XCOM-INV-09`). Returns the count expired.
6. `holds(key)`, `state_of(key)`, and `snapshot()` never mutate state.

### 4.7 Identity, ownership, and provenance rules

- The lease key session is always the bound permit session (`permit.session_id()`); a lease whose key
  session differs from the bound permit is never held by this action path.
- The lease plan digest is always the bound permit plan digest (`XCOM-INV-07`); a held lease whose plan
  digest differs is `PlanMismatch`.
- The emitted `SyntheticStimulationItem::origin` is always `OriginKind::validation_tool`; the intent carries
  the exact tool tag, permit/session/plan identity, and request/correlation/causation identity; no code path
  sets a different origin or omits an identity (`XCOM-INV-03`).

## 5. Expected-value tables

### 5.1 Open/configuration acceptance

| Config / permit | Expected `open` |
| --- | --- |
| valid config, consistent permit/policy | `Ok`, open with zero counters |
| `max_pending_actions = 0` or `> kActionPathMaxPendingActions` | `RejectedConfiguration` |
| `max_lineage_entries = 0` or `> kActionPathMaxLineage` | `RejectedConfiguration` |
| `max_drain_steps = 0` or `> kActionPathMaxDrainSteps` | `RejectedConfiguration` |
| `max_payload_bytes = 0` or `> kActionPathMaxPayloadBytes` | `RejectedConfiguration` |
| invalid/empty tool tag | `RejectedConfiguration` |
| guard policy inconsistent with the permit | `RejectedConfiguration` (guard open fails) |
| `ServiceEmulationRegistry(0)` or `> kActionPathMaxActiveLeases` | constructor throws `std::invalid_argument` |

### 5.2 Action-kind decision (post-precondition)

| Request | Expected |
| --- | --- |
| `InjectSignal`, guard `Authorized`, immediate | `Emitted`; intent durable before the single emit; origin synthetic |
| `InjectMessage`, guard `Authorized`, immediate | `Emitted`; intent durable before the single emit; origin synthetic |
| `InvokeService`, guard `Authorized`, immediate, no lease | `Emitted`; no emulation lease acquired |
| `EmulateService`, guard `Authorized`, lease acquires `Ok` | `Emitted`; lease held; origin synthetic |
| any action, guard `Authorized`, host returns `Rejected` | `EmissionRejected`; durable `OutcomeKind::Rejected`; never success |
| any action, guard `Authorized`, host returns `Unavailable` | `EmissionUnavailable`; durable `OutcomeKind::Unknown`; never success |
| any action, guard `Rejected` | `Rejected`, guard reason preserved; no lease acquired, no journal, no emission |
| any action, guard `Failed` | `Failed`, guard reason preserved; no journal, no emission |
| `EmulateService`, conflicting lease | `LeaseConflict`, matching lease status; no guard quota consumed, no journal, no emission |
| scheduled (non-immediate), guard `Authorized`, queue not full | `Queued` |
| scheduled, pending queue full | `CapacityExhausted`; no guard call, no journal, no emission |
| closed action path | `NotOpen`; no mutation |
| `request_id == 0` or over-max payload | `RejectedConfiguration`; no mutation |
| session not `active` | `NotActive`; no guard call, no journal, no emission |

### 5.3 Lease decision

| Operation / state | Expected |
| --- | --- |
| `acquire` free `(endpoint, generation)` within capacity | `Ok`; one `Active` lease |
| `acquire` with an existing `Active` same generation | `Conflict`; no mutation |
| `acquire` with an existing `Active` same `(endpoint, session)` | `Conflict`; no mutation |
| `acquire` at capacity | `CapacityExhausted`; no mutation |
| `acquire` under a foreign session/generation/plan handled at the action path | `LeaseConflict` with `SessionMismatch`/`GenerationMismatch`/`PlanMismatch` |
| `precheck` for any state | returns exactly the `acquire` status with no mutation and no counter change |
| `release` exact owner key | `Ok`; state `Released` |
| `release` unknown key | `NotFound`; no mutation |
| `release` on a `Released` lease | `AlreadyReleased`; no mutation |
| `quarantine` a held lease | `Ok`; state `Quarantined`; not active |
| `expire_elapsed(domain, now)` with `expires_at <= now` | lease `Expired`; not active; counted |
| `expire_elapsed` with a foreign domain | skipped; no comparison across domains |

### 5.4 Scheduling, loop, and late-item decision

| State / request | Expected |
| --- | --- |
| `causation_id` present in the lineage window | `Rejected`; no emission, no journal |
| `causation_id == 0` | never a loop rejection |
| after lineage bound emissions | window retains exactly the bound; oldest evicted |
| `drain` with `now >= scheduled_at`, within tolerance | action emitted; deterministic order |
| `drain` with `now > scheduled_at + late_tolerance`, `RejectLate` | action cancelled as late-rejected; zero emission |
| `drain` with `now > scheduled_at + late_tolerance`, `DiscardLate` | action discarded; zero emission |
| `drain` with a domain differing from the permit validity domain | `None`; no mutation |
| `drain` bounded by `max_drain_steps` | at most `max_drain_steps` actions completed per call |

### 5.5 Completion decision

| Operation / session state | Expected |
| --- | --- |
| `drain`, `active`/`closing`, due actions | emits due actions; `Drained` only when the queue empties with no dropped action and no incomplete intent, else `EvidenceIncomplete` |
| `drain`, a due action whose intent append fails | `failed` surfaced; `EvidenceIncomplete`; never `Drained` |
| `drain`, terminal state | cancels every pending action; zero emission; matching outcome, with a `closed` state holding an orphan intent returning `EvidenceIncomplete` |
| `close` | drains due actions, cancels the rest, releases all leases; `Closed` |
| `close` with an intent lacking a durable outcome or a dropped due action | `EvidenceIncomplete`; never `Closed` |
| `drain`/`close`, non-active non-terminal (`declared`/`armed`) | cancels every pending action; zero emission; `None` (or `EvidenceIncomplete` with an orphan intent); never `Drained`/`Closed` |
| `revoke` | cancels all pending; releases all leases; `Revoked` |
| `expire` | cancels all pending; expires all leases; `Expired` |
| `mark_evidence_incomplete` | cancels all pending; releases all leases; counts evidence-incomplete intents; `EvidenceIncomplete` |
| any completion with a foreign domain | `None`; no mutation |

## 6. Failure semantics

| Condition | Outcome / status |
| --- | --- |
| action path closed | `NotOpen`; no mutation |
| malformed request or invalid declared configuration | `RejectedConfiguration`; no mutation |
| pending queue or lease table at capacity | `CapacityExhausted`; no mutation, no emission |
| session not `active` | `NotActive`; no emission |
| guard `Rejected` | `Rejected` with the guard reason; no lease acquired, no journal, no emission |
| guard `Failed` | `Failed` with the guard reason; no lease acquired, no journal, no emission |
| lease conflict / foreign identity | `LeaseConflict` with the matching lease status; no journal, no emission |
| intent append/sync failure | `JournalFailed`; no emission |
| intent durable, outcome not durable | `EvidenceIncomplete`; never success |
| intent and outcome durable, host rejected | `EmissionRejected`; never success |
| intent durable, host outcome unknown | `EmissionUnavailable`; never success |
| due pending action dropped at drain/close | `CompletionReport.failed` surfaced; completion outcome never `Drained`/`Closed` |
| prohibited reinjection | `Rejected`; no emission, no journal |
| late action | `Expired`/discarded per the declared policy; no emission |
| completion with a foreign clock domain | `CompletionOutcome::None`; no mutation |
| every step passed | `Emitted` (or `Queued` for a scheduled action) |

No condition maps to `Emitted` except a durable intent, a single host `Delivered` emission, and a durable
outcome. A host `Rejected`/`Unavailable` outcome is durable but is reported as a distinct non-success
status. No decline mutates a lease, the pending queue, the lineage window, or the durable journal in the
declined dimension, and no decline emits.

### 6.1 Negative-case mapping

Each failure condition has a negative case in `verification-plan.md` §5: closed/malformed
`NEG-33`/`NEG-34`, guard decline `NEG-06`, `NEG-26`, `NEG-27`, lease conflict/identity `NEG-09`…`NEG-13`,
journal-order/incomplete `NEG-07`, `NEG-25`, provenance `NEG-08`, time `NEG-14`, `NEG-19`, `NEG-23`,
`NEG-24`, loop `NEG-15`, `NEG-16`, queue/late `NEG-17`, `NEG-18`, completion `NEG-20`…`NEG-22`,
non-mutation `NEG-26`, determinism `NEG-28`, concurrency `NEG-29`, `NEG-36`, offline/payload
`NEG-02`, `NEG-03`, `NEG-05`, `NEG-30`, public safety `NEG-31`, and governance/scope
`NEG-01`/`NEG-32`.

## 7. Bounds and resource design

| Resource | Kind | Design value | Declared in |
| --- | --- | --- | --- |
| pending queue | depth | ≤ `kActionPathMaxPendingActions` = 64 | `ActionPathConfig` |
| lineage window | depth | ≤ `kActionPathMaxLineage` = 64 | `ActionPathConfig` |
| drain budget | count | ≤ `kActionPathMaxDrainSteps` = 64 per call | `ActionPathConfig` |
| payload view | bytes | ≤ `kActionPathMaxPayloadBytes` = 4096, call-scoped | `ActionPathConfig` |
| active leases | capacity | ≤ `kActionPathMaxActiveLeases` = 64 | `ServiceEmulationRegistry` |
| bounded tags | bytes | ≤ `Tag::max_length` = 63 each | `Tag` (T025, read-only) |
| writer count | thread count | 1 declared writer per action path and per registry | documentation |
| test threads | thread count | ≤ 4 (concurrency cases only) | tests |
| iterations | count | ≤ 64 bounded operations per case | tests |

The action path allocates only its bounded pending vector, lineage vector, and counter set; the registry
allocates only its bounded lease vector. No unbounded allocation, loop, wait, retry, I/O, or thread exists
on any path.

## 8. Build wiring design

- Add `xverse_xcom_stimulation_actions` to `XVERSE_XCOM_RUNTIME_TARGETS` in
  `src/xverse/xcom/CMakeLists.txt` (the generated build-contract verifier derives its expectation from the
  same list).
- Define `add_library(xverse_xcom_stimulation_actions STATIC src/stimulation_actions.cpp)`, alias
  `xverse::xcom_stimulation_actions`, include directory `include/`, and PUBLIC link to
  `xverse::xcom_stimulation_guard`, `xverse::xcom_stimulation_journal`,
  `xverse::xcom_validation_session`, and `xverse::xcom_core_types`; route it through
  `xverse_xcom_apply_runtime_rules`.
- Add one `add_executable` per test kind (`action`, `lease`, `lifecycle`, `negative`, `concurrency`) with
  `GTest::gtest_main`, `GTest::gmock`, and `Threads::Threads`, using `gtest_discover_tests` with the
  hyphenated label `t028-<kind>` (CMake 3.22 label workaround, as accepted for T020/T024/T026/T027). No
  scratch directory is required (the action path performs no file I/O).
- Pass the committed header and source paths to the negative suite as
  `XCOM_T028_HEADER_PATH`/`XCOM_T028_SOURCE_PATH` for the declaration inspection, following the accepted
  T027 pattern; no absolute host path is embedded in committed evidence.
- Reuse the admitted `XVERSE_XCOM_T025_TEST_TOOLCHAIN` GTest prefix unchanged; add no dependency and
  introduce no new mandatory input.
- Add no root-`CMakeLists.txt`, `cmake/*.cmake`, XDL, or proto change.

## 9. Doxygen plan

| Element | Required tags |
| --- | --- |
| file block (`stimulation_actions.hpp`) | `\file`, `\brief`, `\ingroup xcom_stim` |
| `ActionStatus`, `LeaseStatus`, `LeaseState`, `OrderingRule`, `LateItemPolicy`, `DrainState`, `EmissionStatus`, `CompletionOutcome`, `QuarantineReason` | `\brief`, `\ownership`, `\lifetime`, `\thread_safety`, `\failure` on the type |
| `ActionPathConfig`, `EndpointGeneration`, `EmulationLease`, `PendingAction`, `SyntheticStimulationItem`, `ActionDiagnostic`, `ActionPathSnapshot`, `LeaseSnapshot`, `CompletionRequest`, `CompletionReport` | `\brief` plus `\ownership`, `\lifetime`, `\thread_safety`, `\failure` |
| `ActionEmitter`, `ServiceEmulationRegistry`, `StimulationActionPath` | `\brief`, `\ownership`, `\lifetime`, `\thread_safety`, `\failure` |
| every public method | `\brief`, `\param`, `\return`/`\retval` where applicable, and `\pre`/`\post` where the contract requires ordering |

The count of documented public elements is recorded at implementation; a delta from the T010
`XCOM-DU-018` plan (6 documented/public elements) is handled by `T028-OPEN-01` rather than by silently
editing the accepted T010 artifact.

## 10. Case inventory (planned tests)

All cases are additive GoogleTest cases registered by `gtest_discover_tests` with one `t028-<kind>` label.

### 10.1 `tests/xcom/stimulation_actions/action_tests.cpp`

- **`T28-TS-001` `ActionPathExecutesNominalActionKinds`** — the four action kinds on a consistent guard;
  assert `Emitted`, the committed counters, and the intent-before-emit order recorded by the test emitter;
  a host `Rejected`/`Unavailable` outcome is durable but reported as `EmissionRejected`/`EmissionUnavailable`,
  never as `Emitted`. (CHK-08, CHK-09)
- **`T28-TS-002` `ActionPathGuardDecisionMapping`** — every guard decline maps to a non-emitting,
  non-journaling `ActionStatus` with the guard reason preserved; a guard-declined `EmulateService` acquires
  no lease, so the whole lease table is byte-identical. (CHK-07)
- **`T28-TS-003` `ActionPathSyntheticProvenance`** — the emitted item carries
  `OriginKind::validation_tool` and the exact tool/permit/session/plan/request/correlation/causation
  identity. (CHK-09)
- **`T28-TS-004` `ActionPathVocabularyAndDeterminism`** — stable names, ranks, and totals; three repeated
  bounded runs produce identical statuses and snapshots. (CHK-17)
- **`T28-TS-005` `ActionPathConfigAndPreconditionMatrix`** — every row of §5.1 and the closed/malformed/
  capacity/not-active preconditions of §5.2. (CHK-06, CHK-18)

### 10.2 `tests/xcom/stimulation_actions/lease_tests.cpp`

- **`T28-TS-006` `LeaseAcquireIdentityBindingMatrix`** — session/generation/plan binding; the action path
  maps a foreign identity to `LeaseConflict` with the matching `LeaseStatus`. (CHK-10)
- **`T28-TS-007` `LeaseConflictAndCapacityMatrix`** — same-generation and same-`(endpoint, session)`
  conflicts and the capacity bound; no mutation. (CHK-11)
- **`T28-TS-008` `LeaseReleaseQuarantineMatrix`** — exact-owner release, unknown/`AlreadyReleased`,
  quarantine, and no-amendment-on-failure. (CHK-12)
- **`T28-TS-009` `LeaseExpiryAndDomainMatrix`** — elapsed lease becomes inactive; a foreign-domain value is
  never compared; no authority call. (CHK-13)
- **`T28-TS-010` `LeaseGenerationSupersessionMatrix`** — a lease under generation `n` does not authorize or
  conflict-block generation `n+1`; the action path rejects a superseded-generation request, and a second
  request for an already-held generation is `LeaseConflict`/`Conflict` and never emits as a second owner.
  (CHK-10, CHK-12)

### 10.3 `tests/xcom/stimulation_actions/lifecycle_tests.cpp`

- **`T28-TS-011` `LifecycleScheduledQueueAndOrdering`** — bounded enqueue, declared ordering, and
  deterministic drain order. (CHK-15)
- **`T28-TS-012` `LifecycleLateItemPolicyMatrix`** — `RejectLate`/`DiscardLate`, both zero emission, within
  the bounded drain budget. (CHK-15, CHK-14)
- **`T28-TS-013` `LifecycleDrainCloseRevokeExpire`** — the §5.5 completion matrix for the four terminal
  operations. (CHK-16)
- **`T28-TS-014` `LifecycleEvidenceIncompleteCompletion`** — an intent without a durable outcome surfaces
  `EvidenceIncomplete` and is never `Closed`; a due pending action whose drain-time intent append fails is
  surfaced as `CompletionReport.failed` with an `EvidenceIncomplete` outcome, never a clean `Drained`; a
  due action whose drain-time *outcome* append fails leaves one durable intent without a durable outcome,
  so `drain` and `close` return `EvidenceIncomplete` and report that single distinct orphan intent once.
  (CHK-16, CHK-08)
- **`T28-TS-015` `LifecycleImmediateAndUnmappedClock`** — immediate labeling; an unmapped/out-of-tolerance
  resolution fails before emission and before journaling. (CHK-13, CHK-19)

### 10.4 `tests/xcom/stimulation_actions/negative_tests.cpp`

- **`T28-TS-016` `ActionPathDeclineZeroMutationAndZeroEmission`** — for each decline family the snapshot is
  byte-identical, the lease table and pending queue are unchanged, and the test emitter observed no call;
  a guard quota decline on an emulation action leaves the whole lease table byte-identical. (CHK-14,
  CHK-21)
- **`T28-TS-017` `ActionPathClosedAndCapacityReject`** — `NotOpen`, `CapacityExhausted`, and
  `RejectedConfiguration` before any guard call or journal. (CHK-18, CHK-21)
- **`T28-TS-018` `ActionPathPayloadFreeDeclarationInspection`** — the comment-stripped header and source
  expose no payload-retaining member, no forbidden I/O/emission vocabulary, and a non-vacuous compile-time
  payload-free/size rule. (CHK-05, CHK-20)

### 10.5 `tests/xcom/stimulation_actions/concurrency_tests.cpp`

- **`T28-TS-019` `ActionPathBoundedDeterministicConcurrency`** — ≤ 4 threads submit bounded immediate
  actions to one action path with a declared guard quota; exactly the quota is `Emitted`, the remainder is
  declined, and three repeated runs match the golden sequence. (CHK-18)
- **`T28-TS-020` `LeaseConcurrentRaceSingleWinner`** — ≤ 4 threads race to acquire one endpoint generation;
  exactly one `Ok` and the remainder `Conflict`, with a deterministic final snapshot. (CHK-18, CHK-11)

## 11. Traceability

| Design element | T028 requirements | Units |
| --- | --- | --- |
| Vocabularies (§3.2–3.3) | T028-SR-003, T028-SR-018 | TS-004 |
| Bounded values (§3.4–3.6) | T028-SR-004 | TS-001, TS-005, TS-018 |
| Open/config (§4.2, §5.1) | T028-SR-005 | TS-005, TS-017 |
| Guarded decision (§4.3 steps 1–6, §5.2) | T028-SR-005, T028-SR-006 | TS-002, TS-005 |
| Journal/emit (§4.3 step 7) | T028-SR-007 | TS-001, TS-014 |
| Provenance (§4.7) | T028-SR-008 | TS-003 |
| Lease acquisition/identity (§4.6, §5.3) | T028-SR-009, T028-SR-010 | TS-006, TS-007, TS-020 |
| Lease release/quarantine/expiry (§4.6) | T028-SR-011, T028-SR-012 | TS-008, TS-009, TS-010 |
| Loop/lineage (§4.3 step 7, §5.4) | T028-SR-013 | TS-012, TS-016 |
| Scheduling/late (§4.4, §5.4) | T028-SR-014 | TS-011, TS-012 |
| Immediate/unmapped time (§4.3, §5.4) | T028-SR-015 | TS-015 |
| Completion (§4.5, §5.5) | T028-SR-016 | TS-013, TS-014 |
| Non-mutation (§4.3 step 9, §6) | T028-SR-017 | TS-016, TS-017 |
| Determinism (§4, §7) | T028-SR-018 | TS-004, TS-019 |
| Concurrency (§4, §7) | T028-SR-019 | TS-019, TS-020 |
| Build wiring (§8) | T028-SR-001, T028-SR-002 | TS-001…TS-020 (execution) |
| Doxygen (§9) | T028-SR-022 | inspection |

## 12. Traceability to accepted `XCOM-DU-018` design

| Accepted `XCOM-DU-018` element | Design realization |
| --- | --- |
| ownership `session-issued-handle` | only an action path opened from the session's immutable permit executes; §4.1 |
| lifetime `endpoint-generation` | a lease is valid only for the endpoint generation under which it was acquired; §4.6 |
| thread-safety `internally-synchronized` | one mutex per action path and one per lease registry; §4.1, §4.6 |
| shared state `drain state`, `exclusive lease table keyed by endpoint and generation` | `DrainState` in the action path; the `(endpoint, generation)` lease table in the registry; §3, §4.6 |
| bound `active leases` (activation plan) | `ServiceEmulationRegistry(max_active_leases)`; §3.1, §7 |
| bound `drain deadline` / `drain queue depth` (validation permit) | `ActionPathConfig.max_drain_steps`/`max_pending_actions` cross-checked with the permit; §7, `T028-OPEN-01` |
| overflow `reject`/`fail-closed` | any bound failure is `CapacityExhausted`/`LeaseConflict`/`RejectedConfiguration`; §6 |
| failure `lease revoked, expired, or disconnected → cancelled` | release/quarantine and cancellation of pending actions; §4.5, §4.6 |
| failure `emission without a recorded outcome → evidence-incomplete` | `ActionStatus::EvidenceIncomplete`, `CompletionOutcome::EvidenceIncomplete`; §4.3, §4.5 |
| failure `outcome unknown after emission → evidence-incomplete` | the journal `Unknown`/incomplete outcome surfaces `EvidenceIncomplete`; §4.3 |
| failure `lease validity elapsed → expired` | `expire_elapsed` and the reuse check; §4.6 |
| failure `lease conflict or unauthorized action → rejected` | `LeaseConflict` and the guard decline mapping; §4.3 |
| doxygen `public_elements = 6` | recorded at implementation; a delta is `T028-OPEN-01` |

## 13. Open design items handled outside this artifact

- **`T028-OPEN-01`** — the `XCOM-DU-018` bound source ("declared in activation plan"/"declared in
  validation permit") and public-element count are reconciled in the T028 implementation record as a
  successor note; the accepted T010 artifact is not edited silently.
- **`T028-OPEN-02`** — the host `ActionEmitter` seam and the call-scoped payload view are the realization
  boundary; the accepted provider boundary owns transport and T030–T034 owns the gateway.
- **`T028-OPEN-03`** — the action path consumes a caller-resolved time so that no decline can mutate the
  accepted `TimeAuthority` baseline; the end-to-end wiring is T029/T032.
