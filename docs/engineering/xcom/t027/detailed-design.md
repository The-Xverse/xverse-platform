# T027 Detailed Design — Guard Vocabularies, Check Order, Bounds, Failure Semantics, and Tests

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T027 (capability 007, slice `T-STIM`) |
| Stage / role | plan → detailed design (pre-code) |
| Revision | 1 (fail-closed pre-emission guard) |
| Baseline revision | `bbfaccda474d5c77d17d22906b8ecfc8b5b4f78f` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Accepted design unit | `XCOM-DU-017` fail-closed pre-emission guard (component `XCOM-CMP-009`, contract `XCOM-XLC-006`, boundary `XCOM-XB-007`) |
| Classification | Public-safe engineering work product |

This design is written **before** implementation. Every constant, bound, check order, and expected value
below is a verification contract: the implementation must realize it, and weakening an expected value
requires a reviewed successor candidate.

## 2. Design principles

1. **Fail closed.** Every check that cannot be satisfied rejects the request; every indeterminate time
   resolution fails (`Failed`). Only `Authorized` may proceed to emission.
2. **Reject without mutation.** `Rejected`/`Failed` leave the tallies, loop window, permit, and policy
   unchanged and expose no emission path. Commit happens only on `Authorized`.
3. **Bind to the exact plan.** Session/permit/plan identity and the declared policy plan digest are
   cross-checked against the immutable permit (`XCOM-INV-07`).
4. **No raw-clock comparison.** The guard consumes a caller-resolved time in the permit validity domain and
   never orders two mismatched clock domains (`XCOM-INV-09`); it performs no authority mutation or I/O.
5. **Bounded and deterministic.** Closed vocabularies, finite tallies/windows/tables, stable precedence,
   identical decisions and snapshots across runs.
6. **Additive and read-only on predecessors.** T025 and T026 accepted bytes are consumed read-only; the
   guard is a new unit and adds no emission, route, lease, or action path.
7. **Decision only.** The guard computes a decision; it injects, invokes, emulates, leases, drains, closes,
   revokes, expires, and routes nothing (T028/T029).

## 3. Types and canonical vocabulary

Namespace: `xverse::xcom::validation` (the accepted `XCOM-XLC-006` family), following T025. The unit reuses
`Permit` (immutable), `PermitId`, `SessionId`, `PlanDigest`, `Timestamp`, `ClockDomainId`,
`kInvalidClockDomain`, `Tag`, `Result`, `Diagnostic`, `LifecycleState`, `is_terminal`, and `TimeAuthority`
from `validation_session.hpp` read-only, and `InteractionKind`/`EndpointDirection` from the accepted core
`contract.hpp` read-only. No identity, digest, diagnostic, interaction, or direction type is redefined.

### 3.1 Constants

| Constant | Value | Meaning |
| --- | --- | --- |
| `kGuardMaxSchemas` | `16` | maximum declared allowed-schema entries in a policy |
| `kGuardMaxLoopWindow` | `64` | maximum declared loop-detection window depth |
| `kGuardMaxActionsPerSession` | `4096` | maximum declared per-session authorized-action budget |
| `kGuardMaxActionsPerWindow` | `4096` | maximum declared per-window authorized-action budget |
| `kDefinedStimulationActions` | `0x0F` | mask of every defined stimulation-action bit |

### 3.2 `StimulationAction`

Closed, single-bit, deterministically ordered; declaration order is precedence order.

| Bit | Enumerator | Meaning | Paired interaction | Paired direction |
| --- | --- | --- | --- | --- |
| `1U<<0U` | `InjectSignal` | inject one declared signal/state update | `InteractionKind::signal_state_update` | `EndpointDirection::produce` |
| `1U<<1U` | `InjectMessage` | inject one declared message/event | `InteractionKind::message_event` | `EndpointDirection::produce` |
| `1U<<2U` | `InvokeService` | invoke one declared service operation | `InteractionKind::service_request` | `EndpointDirection::request` |
| `1U<<3U` | `EmulateService` | emulate one explicitly allowed service endpoint | `InteractionKind::service_response` | `EndpointDirection::respond` |

`using StimulationActionMask = std::uint32_t;`. Helpers: `to_stimulation_mask(StimulationAction)`,
`is_defined_stimulation_action(StimulationActionMask)`, `is_single_stimulation_action(StimulationActionMask)`,
`stimulation_action_name(StimulationActionMask) -> std::string_view`.

### 3.3 `GuardOutcome` and `GuardReason`

`GuardOutcome` is closed: `Authorized` (all checks passed and committed), `Rejected` (a definite declared
mismatch), `Failed` (the evaluation could not complete deterministically; the outcome is unknown, so the
caller must record an explicit incomplete/unknown outcome through the accepted T026 journal).

`GuardReason` is closed and ordered; declaration order **is** evaluation order and precedence order (a lower
rank is evaluated earlier and binds). `outcome_of(reason)` is a pure total function.

| Rank | `GuardReason` | Outcome | Meaning |
| ---: | --- | --- | --- |
| 0 | `NotOpen` | `Failed` | the guard is closed; no request is evaluated |
| 1 | `RejectedConfiguration` | `Rejected` | a malformed request or invalid/zero/inconsistent bound |
| 2 | `PermitMismatch` | `Rejected` | session, permit, or plan identity differs from the bound permit |
| 3 | `Revoked` | `Rejected` | the session is revoked |
| 4 | `Expired` | `Rejected` | the session is expired |
| 5 | `NotActive` | `Rejected` | the session is in a non-`active`, non-revoked, non-expired state |
| 6 | `SchemaMismatch` | `Rejected` | the schema is undeclared or not admissible |
| 7 | `DirectionMismatch` | `Rejected` | the direction is inconsistent or not admissible |
| 8 | `InteractionMismatch` | `Rejected` | the interaction kind is inconsistent or not admissible |
| 9 | `TargetMismatch` | `Rejected` | the target or interface tag differs from the permit |
| 10 | `ActionMismatch` | `Rejected` | the action is defined but not declared allowed |
| 11 | `OwnershipConflict` | `Rejected` | a service owner/generation is missing, mismatched, or ambiguous |
| 12 | `QuotaExhausted` | `Rejected` | the per-session or per-window budget is exhausted |
| 13 | `LoopBound` | `Rejected` | a prohibited reinjection or a loop-window bound |
| 14 | `TimeOutOfWindow` | `Rejected` | the resolved time is outside the permit validity interval |
| 15 | `TimeUnmapped` | `Failed` | the time resolution is absent, unmapped, or outside tolerance |
| 16 | `None` | `Authorized` | every check passed; tallies committed |

`reason_name(GuardReason)`, `precedence_rank(GuardReason)`, and `outcome_of(GuardReason)` return stable
values; `GuardStatus` is closed (`Ok`, `RejectedConfiguration`, `NotOpen`) for the open/precondition
boundary, with `guard_status_name(GuardStatus)`.

### 3.4 `StimulationPolicy` (bounded, declared)

| Field | Type | Rule |
| --- | --- | --- |
| `plan_digest` | `PlanDigest` | must equal `permit.plan_digest()` at open |
| `interface_tag` | `Tag` | valid tag; must equal `permit.interface_name()` at open |
| `target` | `Tag` | valid tag; must equal `permit.target()` at open |
| `validity_domain` | `ClockDomainId` | non-`kInvalidClockDomain`; must equal `permit.validity_domain()` at open |
| `allowed_actions` | `StimulationActionMask` | non-zero and only defined bits |
| `allowed_interactions` | `std::uint8_t` | non-zero and only bits `0x0F` (see §3.5) |
| `allowed_directions` | `std::uint8_t` | non-zero and only bits `0x0F` (see §3.5) |
| `allowed_schemas` | `std::vector<SchemaKey>` | non-empty and ≤ `kGuardMaxSchemas`; every key valid |
| `max_actions_per_session` | `std::size_t` | `1 … kGuardMaxActionsPerSession` |
| `max_actions_per_window` | `std::size_t` | `1 … max_actions_per_session` |
| `action_window` | `std::size_t` | `1 … kGuardMaxActionsPerWindow` |
| `loop_window` | `std::size_t` | `1 … kGuardMaxLoopWindow` |
| `allow_service_emulation` | `bool` | when `true` and `EmulateService` is allowed, `service_owner.declared` must be `true` |
| `service_owner` | `ServiceOwner` | declared endpoint tag + generation |

`SchemaKey { Tag id; Tag version; }`; `ServiceOwner { Tag endpoint; std::uint64_t generation; bool declared; }`.
Both are bounded, payload-free values with defaulted equality. `StimulationPolicy` is a caller-owned,
copyable value.

### 3.5 Interaction/direction bit mapping

`interaction_bit(InteractionKind)`: `signal_state_update`=`1U<<0U`, `message_event`=`1U<<1U`,
`service_request`=`1U<<2U`, `service_response`=`1U<<3U`. `direction_bit(EndpointDirection)`:
`produce`=`1U<<0U`, `consume`=`1U<<1U`, `request`=`1U<<2U`, `respond`=`1U<<3U`. Helpers return `0` for an
out-of-vocabulary value.

### 3.6 `StimulationRequest` (bounded, declared)

| Field | Type | Rule |
| --- | --- | --- |
| `permit_id` | `PermitId` | must equal `permit.permit_id()` |
| `session_id` | `SessionId` | must equal `permit.session_id()` |
| `plan_digest` | `PlanDigest` | must equal `permit.plan_digest()` |
| `action` | `StimulationAction` | a defined single-bit action |
| `interaction` | `InteractionKind` | a defined enumerator |
| `direction` | `EndpointDirection` | a defined enumerator |
| `schema` | `SchemaKey` | valid tag id/version |
| `target` | `Tag` | valid tag; must equal `permit.target()` |
| `interface_tag` | `Tag` | valid tag; must equal `permit.interface_name()` |
| `service_owner` | `ServiceOwner` | validated only for service actions |
| `clock_domain` | `ClockDomainId` | non-invalid for a scheduled request; equal to the validity domain for an immediate request |
| `scheduled_at` | `Timestamp` | declared schedule in `clock_domain` (informational) |
| `immediate` | `bool` | explicit immediate/scheduled label |
| `request_id` | `std::uint64_t` | non-zero identity |
| `correlation_id` | `std::uint64_t` | any |
| `causation_id` | `std::uint64_t` | any; a non-zero value present in the loop window is a prohibited reinjection |
| `quota_cost` | `std::uint32_t` | informational; the guard's budget is per authorized action |

### 3.7 `ResolvedTime` and diagnostics

`ResolvedTime { ClockDomainId domain; Timestamp value; Result resolution; }` — the caller obtains it from the
accepted `TimeAuthority` (`convert`/`now`). `GuardDiagnostic { GuardReason reason; Diagnostic detail; }` —
`detail` is the accepted T025 bounded payload-free diagnostic (ordered `Result` codes plus an optional
numeric locator). `GuardSnapshot` is defined in §4.4.

## 4. Guard behaviour

### 4.1 `open(permit, policy)` → `GuardStatus`

1. If the guard is already open, re-open validates and replaces the binding (idempotent configuration).
2. Validate every policy bound of §3.4. A zero/over-maximum/inconsistent bound, an over-full or empty schema
   table, or an invalid tag is `RejectedConfiguration` — the guard remains closed and no external state is
   mutated.
3. Validate policy consistency with the permit: `plan_digest`, `interface_tag`, `target`, and
   `validity_domain` must match the immutable permit. A mismatch is `RejectedConfiguration`.
4. Store a copy of the permit and the policy, reset the tallies, loop window, and bounded
   request-authorization ledger to zero, set `open = true`,
   and return `Ok`.

### 4.2 `authorize(request, session_state, resolved_time, out)` → `GuardOutcome`

The guard evaluates the checks in §3.3 rank order. The first failing check determines `out.reason` and the
outcome; no later check runs.

1. **Open (rank 0).** If `!open`, set `NotOpen` and return `Failed`.
2. **Malformed request (rank 1).** Action must be a defined single bit: `is_defined_stimulation_action`
   and `is_single_stimulation_action` must both hold, so a zero, composite, or out-of-vocabulary action
   (including a single undefined bit such as `0x10`) is `RejectedConfiguration` and is never reported as a
   later direction/interaction/action-table mismatch (rank 1 binds before ranks 7/8/10). `request_id` must
   be non-zero; `clock_domain` must be valid (scheduled) or equal the validity domain (immediate). Any
   violation is `RejectedConfiguration` with no mutation. An invalid/empty/over-long schema tag or an
   undeclared schema is `SchemaMismatch` (rank 6, step 5) and an invalid, empty, or mismatched
   target/interface tag is `TargetMismatch` (rank 9, step 8), per `T027-SR-007`,
   `verification-plan.md` CHK-08/NEG-05; an out-of-vocabulary direction is `DirectionMismatch`
   (step 6) and an out-of-vocabulary interaction is `InteractionMismatch` (step 7). This clause was
   reconciled at the
   implementation stage: the more specific requirement reasons take precedence over an
   undifferentiated `RejectedConfiguration` (see `implementation.md` §7.2).
3. **Identity (rank 2).** `request.session_id == permit.session_id()`, `request.permit_id ==
   permit.permit_id()`, `request.plan_digest == permit.plan_digest()`, and `policy.plan_digest ==
   request.plan_digest`; otherwise `PermitMismatch`.
4. **Lifecycle (ranks 3–5).** `session_state == revoked` → `Revoked`; `expired` → `Expired`; anything other
   than `active` → `NotActive`. Only `active` continues.
5. **Schema (rank 6).** `request.schema` must be a member of `policy.allowed_schemas`; otherwise
   `SchemaMismatch`.
6. **Direction (rank 7).** `direction_bit(request.direction) == direction_bit(table[request.action])` and
   `request.direction` is admissible by `policy.allowed_directions`; otherwise `DirectionMismatch`.
7. **Interaction (rank 8).** `interaction_bit(request.interaction) == interaction_bit(table[request.action])`
   and admissible by `policy.allowed_interactions`; otherwise `InteractionMismatch`.
8. **Target (rank 9).** `request.target == permit.target()` and `request.interface_tag ==
   permit.interface_name()`; otherwise `TargetMismatch`.
9. **Action (rank 10).** `to_stimulation_mask(request.action)` is contained in `policy.allowed_actions`;
   otherwise `ActionMismatch`.
10. **Service ownership (rank 11).** For `InvokeService`/`EmulateService`: `policy.service_owner.declared`
    must be `true`, `request.service_owner.declared` must be `true`, and the endpoint tag and generation must
    equal the policy's; `EmulateService` additionally requires `policy.allow_service_emulation`; a missing,
    mismatched, or ambiguous declaration is `OwnershipConflict`. The guard acquires no lease
    (`XCOM-INV-04`/`10` remain `XCOM-DU-018`/T028).
11. **Quota (rank 12).** `actions_authorized_ + 1 <= policy.max_actions_per_session` and `window_actions_ + 1
    <= policy.max_actions_per_window`; otherwise `QuotaExhausted`.
12. **Loop (rank 13).** `request.causation_id != 0` and `request.causation_id` present in the loop window →
    `LoopBound`.
13. **Time (ranks 14–15).** If `resolved_time.resolution != Result::Ok` or `resolved_time.domain !=
    policy.validity_domain` → `Failed` (`TimeUnmapped`). Else the resolved value must satisfy
    `permit.valid_from() <= value < permit.valid_until()`; otherwise `Rejected` (`TimeOutOfWindow`). The
    guard performs no time-authority call and no raw clock comparison.
14. **Authorize and commit.** When every check passes, under the one mutex: increment `actions_authorized_`
    and `window_actions_` (resetting `window_actions_` to `0` when it reaches `action_window`), push
    `request.request_id` into the loop window (evicting the oldest entry when full), increment
    `evaluations_`, set `out.reason = None`, and return `Authorized`.
15. **Rejection bookkeeping.** On `Rejected`/`Failed` the guard increments only the observable
    `evaluations_`/`rejections_`/`failures_` counters; the action tallies and loop window are **not**
    mutated, and no permit/policy byte changes.

### 4.3 `snapshot` and `is_open`

`snapshot()` returns a `GuardSnapshot` value under the mutex without a scan. `is_open()` reports the open
flag. Neither mutates state.

### 4.4 `GuardSnapshot`

| Field | Meaning |
| --- | --- |
| `open` | whether the guard is open |
| `actions_authorized` | authorized actions since open |
| `actions_remaining` | `max_actions_per_session - actions_authorized` |
| `window_actions` | authorized actions in the current ordinal window |
| `window_remaining` | `max_actions_per_window - window_actions` |
| `loop_entries` | lineage entries currently retained in the loop window |
| `evaluations` | total `authorize` calls |
| `rejections` | `Rejected` outcomes |
| `failures` | `Failed` outcomes |

Value equality is defaulted over every field.

## 5. Expected-value tables

### 5.1 Policy/open acceptance

| Policy / permit | Expected `open` |
| --- | --- |
| consistent policy, `allowed_actions = 0x0F`, `loop_window = 8`, budgets `8/4/4`, 2 schemas | `Ok` |
| `allowed_actions = 0` | `RejectedConfiguration` |
| `loop_window = 0` or `> kGuardMaxLoopWindow` | `RejectedConfiguration` |
| `max_actions_per_session = 0` or `> kGuardMaxActionsPerSession` | `RejectedConfiguration` |
| `max_actions_per_window > max_actions_per_session` | `RejectedConfiguration` |
| `action_window = 0` or `> kGuardMaxActionsPerWindow` | `RejectedConfiguration` |
| `allowed_schemas` empty or `> kGuardMaxSchemas` | `RejectedConfiguration` |
| `plan_digest` / `interface_tag` / `target` / `validity_domain` differs from the permit | `RejectedConfiguration` |
| `allow_service_emulation = true` with `EmulateService` allowed and `service_owner.declared = false` | `RejectedConfiguration` |

### 5.2 Lifecycle decision

| Session state | Expected |
| --- | --- |
| `active` | continues to the remaining checks |
| `revoked` | `Rejected`, `Revoked` |
| `expired` | `Rejected`, `Expired` |
| `declared`, `armed`, `closing`, `closed`, `evidence_incomplete` | `Rejected`, `NotActive` |

### 5.3 Action/interaction/direction decision

| Request triple | Expected |
| --- | --- |
| `InjectSignal` + `signal_state_update` + `produce`, all admissible | continues |
| `InjectMessage` + `message_event` + `produce`, all admissible | continues |
| `InvokeService` + `service_request` + `request`, owner declared and matching | continues |
| `EmulateService` + `service_response` + `respond`, emulation allowed and owner matching | continues |
| `InjectSignal` + `message_event` + `produce` | `Rejected`, `InteractionMismatch` |
| `InjectSignal` + `signal_state_update` + `consume` | `Rejected`, `DirectionMismatch` |
| a defined action outside `policy.allowed_actions` | `Rejected`, `ActionMismatch` |
| a zero/composite/out-of-vocabulary action | `Rejected`, `RejectedConfiguration` |
| an interaction/direction excluded by the policy masks | `Rejected`, `InteractionMismatch`/`DirectionMismatch` |

### 5.4 Quota and loop decision

| State | Expected |
| --- | --- |
| `actions_authorized < max_actions_per_session`, `window_actions < max_actions_per_window` | continues |
| `actions_authorized == max_actions_per_session` | `Rejected`, `QuotaExhausted`, no mutation |
| `window_actions == max_actions_per_window` | `Rejected`, `QuotaExhausted`, no mutation |
| after `action_window` authorized actions | `window_actions` resets to `0` |
| `causation_id` present in the loop window | `Rejected`, `LoopBound`, no mutation |
| `causation_id == 0` | never a loop rejection |
| after `loop_window` authorized actions | the window retains exactly `loop_window` entries, oldest evicted |

The per-window budget binds only while `max_actions_per_window < action_window`; when
`max_actions_per_window >= action_window` the ordinal `window_actions` tally resets at `action_window`
before the window bound can be reached, so only the per-session budget (and the `window_actions <=
max_actions_per_window` invariant, which still holds) caps authorizations. The per-session budget always
bounds every authorized action, so no combination is unbounded. Policy validation does not reject the
non-binding combination; hosts that intend the per-window budget to bind must declare `action_window >
max_actions_per_window`.

### 5.5 Time decision

| Request / resolution | Expected |
| --- | --- |
| scheduled, `resolution == Ok`, `domain == validity_domain`, `valid_from <= value < valid_until` | continues |
| scheduled, `resolution != Ok` (unknown/unmapped/tolerance/source failure) | `Failed`, `TimeUnmapped` |
| scheduled, `resolution == Ok` but `domain != validity_domain` | `Failed`, `TimeUnmapped` |
| resolved `value < valid_from` or `value >= valid_until` | `Rejected`, `TimeOutOfWindow` |
| immediate, `immediate == true`, `clock_domain == validity_domain`, in window | continues |
| immediate with a non-validity `clock_domain` | `Rejected`, `RejectedConfiguration` |

### 5.6 Identity decision

| Request vs permit | Expected |
| --- | --- |
| session, permit, and plan digest all equal | continues |
| session differs | `Rejected`, `PermitMismatch` |
| permit identity differs | `Rejected`, `PermitMismatch` |
| plan digest differs (request) | `Rejected`, `PermitMismatch` |
| plan digest differs (policy) | `RejectedConfiguration` at open (`T027-SR-021`) |

## 6. Failure semantics of the guard

| Condition | Outcome / reason |
| --- | --- |
| guard closed | `Failed`, `NotOpen` |
| malformed request or invalid/zero/inconsistent policy bound | `Rejected`, `RejectedConfiguration` (policy invalid at open) |
| session/permit/plan identity mismatch | `Rejected`, `PermitMismatch` |
| session revoked / expired / non-active | `Rejected`, `Revoked` / `Expired` / `NotActive` |
| schema undeclared or inadmissible | `Rejected`, `SchemaMismatch` |
| direction inconsistent or inadmissible | `Rejected`, `DirectionMismatch` |
| interaction inconsistent or inadmissible | `Rejected`, `InteractionMismatch` |
| target/interface mismatch | `Rejected`, `TargetMismatch` |
| defined action not declared allowed | `Rejected`, `ActionMismatch` |
| service owner missing/mismatched/ambiguous | `Rejected`, `OwnershipConflict` |
| per-session or per-window budget exhausted | `Rejected`, `QuotaExhausted` |
| prohibited reinjection | `Rejected`, `LoopBound` |
| resolved time outside the validity interval | `Rejected`, `TimeOutOfWindow` |
| time resolution absent/unmapped/out-of-tolerance | `Failed`, `TimeUnmapped` |
| every check passed | `Authorized`, `None`, tallies committed |

No condition maps to `Authorized` except the last. No rejection or failure mutates a tally, the loop window,
the permit, or the policy, and no condition emits, injects, invokes, emulates, leases, or routes anything.

### 6.1 Negative-case mapping

Each failure condition above has a negative case in `verification-plan.md` §5: malformed/policy
`NEG-04`/`NEG-33`, identity `NEG-06`/`NEG-07`, lifecycle `NEG-08`/`NEG-09`/`NEG-10`, schema/direction/
interaction/target `NEG-11`/`NEG-12`/`NEG-13`/`NEG-14`, action `NEG-15`, ownership `NEG-20`/`NEG-21`, quota
`NEG-16`/`NEG-17`/`NEG-36`, loop `NEG-18`/`NEG-19`, time `NEG-22`/`NEG-23`/`NEG-24`/`NEG-25`, non-mutation
`NEG-26`, emission surface `NEG-27`, determinism `NEG-28`, concurrency `NEG-29`, offline/public safety
`NEG-30`/`NEG-31`, closed guard `NEG-34`, time-authority/I-O `NEG-35`, and governance/scope `NEG-01`/
`NEG-02`/`NEG-32`.

## 7. Bounds and resource design

| Resource | Kind | Design value | Declared in |
| --- | --- | --- | --- |
| allowed-schema table | capacity | ≤ `kGuardMaxSchemas` = 16 | `StimulationPolicy` |
| loop-detection window | depth | ≤ `kGuardMaxLoopWindow` = 64 | `StimulationPolicy` |
| actions per session | quota | ≤ `kGuardMaxActionsPerSession` = 4096 | `StimulationPolicy` |
| actions per window | rate | ≤ `kGuardMaxActionsPerWindow` = 4096 | `StimulationPolicy` |
| window width | count | 1 … `kGuardMaxActionsPerWindow` | `StimulationPolicy` |
| bounded tags | bytes | ≤ `Tag::max_length` = 63 each | `Tag` (T025, read-only) |
| writer count | thread count | 1 declared writer + 1 mutex | documentation |
| test threads | thread count | ≤ 4 (concurrency case only) | tests |
| iterations | depth | ≤ 64 bounded guard operations per case | tests |

The guard allocates only its bounded schema vector (copied into the policy) and its bounded loop window
(≤ `loop_window` entries). No unbounded allocation, loop, wait, retry, I/O, or thread exists on any path.

## 8. Build wiring design

- Add `xverse_xcom_stimulation_guard` to `XVERSE_XCOM_RUNTIME_TARGETS` in `src/xverse/xcom/CMakeLists.txt`
  (the generated build-contract verifier derives its expectation from the same list).
- Define `add_library(xverse_xcom_stimulation_guard STATIC src/stimulation_guard.cpp)`, alias
  `xverse::xcom_stimulation_guard`, include directory `include/`, and PUBLIC link to
  `xverse::xcom_validation_session` and `xverse::xcom_core_types`; route it through
  `xverse_xcom_apply_runtime_rules`.
- Add one `add_executable` per test kind (`unit`, `mismatch`, `time`, `negative`, `concurrency`) with
  `GTest::gtest_main`, `GTest::gmock`, and `Threads::Threads`, using `gtest_discover_tests` with the
  hyphenated label `t027-<kind>` (CMake 3.22 label workaround, as accepted for T020/T024/T026). No scratch
  directory is required (the guard performs no file I/O).
- Reuse the admitted `XVERSE_XCOM_T025_TEST_TOOLCHAIN` GTest prefix unchanged; add no dependency and
  introduce no new mandatory input.
- Add no root-`CMakeLists.txt`, `cmake/*.cmake`, XDL, or proto change.

## 9. Doxygen plan

| Element | Required tags |
| --- | --- |
| file block (`stimulation_guard.hpp`) | `\file`, `\brief`, `\ingroup xcom_stim` |
| `StimulationAction`, `GuardOutcome`, `GuardReason`, `GuardStatus`, `StimulationPolicy`, `StimulationRequest`, `SchemaKey`, `ServiceOwner`, `ResolvedTime`, `GuardDiagnostic`, `GuardSnapshot`, `StimulationGuard` | `\brief`, plus `\ownership`, `\lifetime`, `\thread_safety`, `\failure` on the type. |
| every public method | `\brief`, `\param`, `\return`/`\retval` where applicable, and `\pre`/`\post` where the contract requires ordering |

The count of documented public elements is recorded at implementation; a delta from the T010 `XCOM-DU-017`
plan (6 documented/public elements) is handled by `T027-OPEN-01` rather than by silently editing the
accepted T010 artifact.

## 10. Case inventory (planned tests)

All cases are additive GoogleTest cases registered by `gtest_discover_tests` with one `t027-<kind>` label.

### 10.1 `tests/xcom/stimulation_guard/unit_tests.cpp`

- **`T27-TS-001` `test_guard_authorizes_nominal_request_and_snapshot`** — open a consistent guard and
  authorize a nominal request of each action kind; assert `Authorized`, `None`, the committed snapshot, and
  the tallies/loop entries. (CHK-04, CHK-14)
- **`T27-TS-002` `test_guard_action_interaction_direction_table`** — every row of §5.3. (CHK-09)
- **`T27-TS-003` `test_guard_closed_vocabulary_and_precedence`** — stable names, ranks, and
  `outcome_of` for every `GuardReason`/`GuardOutcome`/`GuardStatus`. (CHK-17)
- **`T27-TS-004` `test_guard_status_determinism_and_no_mutation`** — three repeated bounded runs produce
  identical decisions, reasons, and snapshots; a rejected evaluation leaves `snapshot()` identical. (CHK-17)
- **`T27-TS-005` `test_guard_policy_validation_matrix`** — every row of §5.1. (CHK-06)

### 10.2 `tests/xcom/stimulation_guard/mismatch_tests.cpp`

- **`T27-TS-006` `test_guard_identity_and_plan_matrix`** — every row of §5.6. (CHK-16)
- **`T27-TS-007` `test_guard_lifecycle_matrix`** — every row of §5.2. (CHK-07)
- **`T27-TS-008` `test_guard_schema_and_target_matrix`** — declared/undeclared schema, invalid schema tags,
  target/interface mismatch. (CHK-08)
- **`T27-TS-009` `test_guard_action_direction_matrix`** — the defined-action-not-allowed and
  interaction/direction exclusion rows of §5.3. (CHK-09)
- **`T27-TS-010` `test_guard_service_ownership_matrix`** — declared/missing/mismatched owner and generation,
  emulation-requires-owner, invoke-vs-emulate. (CHK-11)
- **`T27-TS-011` `test_guard_quota_matrix`** — every row of §5.4 except loop; per-session and per-window
  boundaries with no mutation. (CHK-10)
- **`T27-TS-012` `test_guard_loop_bound_matrix`** — the loop rows of §5.4: prohibited reinjection, `0`
  causation, and window depth/eviction. (CHK-12)

### 10.3 `tests/xcom/stimulation_guard/time_tests.cpp`

- **`T27-TS-013` `test_guard_scheduled_time_window_matrix`** — the in-window and out-of-window rows of §5.5.
  (CHK-13)
- **`T27-TS-014` `test_guard_unmapped_clock_fails_closed`** — every non-`Ok` resolution and a
  domain-mismatch resolution return `Failed`/`TimeUnmapped` with no mutation. (CHK-13)
- **`T27-TS-015` `test_guard_immediate_labeling_matrix`** — the immediate rows of §5.5. (CHK-13)

### 10.4 `tests/xcom/stimulation_guard/negative_tests.cpp`

- **`T27-TS-016` `test_guard_rejection_zero_mutation_and_no_emission`** — for each rejection family, assert
  the snapshot is byte-identical, the loop window is unchanged, and the guard type exposes no
  emission/callback/route/injection/invocation/emulation/lease member (declaration inspection). (CHK-14,
  CHK-15)
- **`T27-TS-017` `test_guard_closed_guard_rejects`** — `authorize` before `open` returns `Failed`/`NotOpen`
  with no mutation. (CHK-15)
- **`T27-TS-018` `test_guard_bounds_config_matrix`** — the remaining §5.1 bound rows and an over-full schema
  table. (CHK-18)

### 10.5 `tests/xcom/stimulation_guard/concurrency_tests.cpp`

- **`T27-TS-019` `test_guard_bounded_deterministic_concurrency`** — ≤ 4 independent guards, one thread each,
  ≤ 16 bounded evaluations each; every guard's decision sequence and final snapshot equal the single-threaded
  golden sequence. (CHK-18)
- **`T27-TS-020` `test_guard_concurrent_rejection_no_mutation`** — ≤ 4 threads submitting only rejecting
  requests to one guard; the snapshot equals the pre-call snapshot and the outcome is always `Rejected`/
  `Failed`. (CHK-18)

## 11. Traceability

| Design element | T027 requirements | Units |
| --- | --- | --- |
| Vocabularies (§3.2–3.3, §3.5) | T027-SR-003, T027-SR-014 | TS-002, TS-003 |
| Bounded values (§3.4, §3.6) | T027-SR-004 | TS-001, TS-005 |
| Open/policy validation (§4.1, §5.1) | T027-SR-021 | TS-005, TS-018 |
| Identity (§4.2 step 3, §5.6) | T027-SR-005 | TS-006 |
| Lifecycle (§4.2 step 4, §5.2) | T027-SR-006 | TS-007 |
| Schema/direction/interaction/target/action (§4.2 steps 5–9, §5.3) | T027-SR-007, T027-SR-008 | TS-002, TS-008, TS-009 |
| Ownership (§4.2 step 10) | T027-SR-011 | TS-010 |
| Quota (§4.2 step 11, §5.4) | T027-SR-009 | TS-011, TS-019 |
| Loop (§4.2 step 12, §5.4) | T027-SR-010 | TS-012, TS-019 |
| Time (§4.2 step 13, §5.5) | T027-SR-012 | TS-013, TS-014, TS-015 |
| Non-mutation/zero emission (§4.2 steps 14–15, §6) | T027-SR-013, T027-SR-022 | TS-016, TS-017, TS-020 |
| Concurrency (§4, §7) | T027-SR-015 | TS-019, TS-020 |
| Build wiring (§8) | T027-SR-001, T027-SR-002 | TS-001…TS-020 (execution) |
| Doxygen (§9) | T027-SR-018 | inspection |

## 12. Traceability to accepted `XCOM-DU-017` design

| Accepted `XCOM-DU-017` element | Design realization |
| --- | --- |
| ownership `session-issued-handle` | only a guard opened from the session's immutable permit authorizes; §4.1 |
| lifetime `session-scoped` | the guard is opened, used, and destroyed within one validation session; §2 |
| thread-safety `internally-synchronized` | one per-guard mutex serializes the checks, tallies, and loop window; §4.2 |
| bound `loop-detection window` | `policy.loop_window` ∈ `1 … kGuardMaxLoopWindow`; §5.4 |
| bound `actions per session` | `policy.max_actions_per_session`; §5.4 |
| bound `actions per interval` | `policy.max_actions_per_window` over `policy.action_window`; §5.4 |
| overflow `reject`/`fail-closed` | any bound failure is `QuotaExhausted`/`LoopBound`/`RejectedConfiguration`; §6 |
| failure `schema/target/direction/action/time/quota/loop/ownership mismatch → rejected` | §4.2 ranks 6–14; §5 |
| failure `outcome unknown after a guard evaluation → failed` | `NotOpen` and `TimeUnmapped` are `Failed`; §3.3, §6 |
| doxygen `public_elements = 6` | recorded at implementation; a delta is `T027-OPEN-01` |

## 13. Open design items handled outside this artifact

- **`T027-OPEN-01`** — the `XCOM-DU-017` bound source ("declared in validation permit") and public-element
  count are reconciled in the T027 implementation record as a successor note; the accepted T010 artifact is
  not edited.
- **`T027-OPEN-02`** — the guard consumes a caller-resolved time so that no rejection can mutate the accepted
  `TimeAuthority` baseline; the end-to-end wiring is T028 and the matrix is T029.
