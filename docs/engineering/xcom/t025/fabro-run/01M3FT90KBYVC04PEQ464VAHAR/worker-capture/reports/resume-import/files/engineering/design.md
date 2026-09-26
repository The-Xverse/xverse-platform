# T025 Design — Explicit Time Authority, Local Validation Permit, and Bounded Validation-Session Lifecycle

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T025 |
| Stage / role | design |
| Revision | 2 |
| Classification | SANITIZED |
| Requirements authority | `engineering/requirements.md` (rev 1) |
| Component records | `engineering/architecture/components/*.json` |
| Namespace | `xverse::xcom::validation` |
| Language / profile | C++20, standard library only, no predecessor headers |

Revision 2 repairs the four independently reproduced correctness defects (R1–R4) and the
incomplete terminal export (R5) recorded in `terminal-review.json`. The time-authority/claim
contract (§7.5), controller identity and uniqueness scope (§7.1), tolerance distance (§4.3), and
transactional conversion state (§4.3, §9.1) are changed as described; all accepted requirement
IDs and behaviors, REF-002 dispositions, the no-emission boundary, and the protected-check
limitations are preserved. See `engineering/design-repair.md` for the repair record.

### 1.1 Authority statement

This design is an internal, source-free engineering candidate. It does **not** establish
accepted X-COM delivery, does not claim predecessor regression, source compatibility,
repository integration, protected verification, or production readiness. Where an authoritative
predecessor interface would be needed and is unavailable, this document records an explicit
integration limit and the decision needed instead of guessing (see §10).

### 1.2 Design goals

1. **Single time authority.** No code path compares a raw timestamp from one clock domain with a
   raw timestamp from another. Every validity and lifecycle time decision is an authority query.
2. **Immutable, exactly-once permit.** One permit identity, one session identity; consumption is
   controller-scoped and atomic; replay is rejected including with a changed nonce.
3. **Controller-bound handles.** A handle is useless without the matching controller identity and
   generation; stale, foreign, and recreated-controller handles cannot address a live session.
4. **Validation before mutation.** Handle, context, time, and action are validated in a declared
   order before any state changes; every rejection is non-mutating and produces a stable,
   ordered, payload-free diagnostic.
5. **Bounded and deterministic.** Every table, set, and counter has a finite host-configured
   bound with an explicit exhaustion result; concurrency is a coarse-grained total order.
6. **Zero normal-route emission.** No communication item, transport, gateway, listener, journal,
   lease, dashboard, persistent store, or external service is created or reachable.

## 2. File layout

```
src/xverse/xcom/include/xverse/xcom/validation_session.hpp   # public API, strict Doxygen
src/xverse/xcom/src/validation_session.cpp                   # implementation
tests/validation_session_tests.cpp                           # GoogleTest/gmock cases
CMakeLists.txt                                               # standalone root build (CTest labels)
```

The public header exposes only the `xverse::xcom::validation` namespace and includes only C++20
standard-library headers (`<cstdint>`, `<array>`, `<optional>`, `<functional>`, `<mutex>`,
`<vector>`, `<string>`, `<limits>`, `<type_traits>`, `<compare>`). No predecessor header is
included or recreated.

## 3. Core vocabulary (component `validation_types`)

All value types are bounded and immutable or trivially copyable. Widths below are candidate
choices fixed by this design; they are not claims about the predecessor.

| Type | Definition | Notes |
| --- | --- | --- |
| `Timestamp` | `std::int64_t` | Domain-local integer timestamp. |
| `Tolerance` | `std::uint64_t` | Maximum admissible magnitude of a mapping divergence. |
| `ClockDomainId` | `std::uint32_t` | Authority-issued domain token; value `0` reserved as invalid. |
| `ControllerId` | `std::array<std::uint8_t,16>` | Host-issued, opaque controller identity supplied at registration; never derived from a name or a per-manager sequence. |
| `ManagerScope` | `std::array<std::uint8_t,16>` | Host-issued uniqueness scope distinguishing one manager instance (or recreation) from another; bound into every handle. |
| `Generation` | `std::uint64_t` | Monotonic generation per controller within one manager scope. |
| `SessionId` | `std::array<std::uint8_t,16>` | Host-issued session identity. |
| `PermitId` | `std::array<std::uint8_t,16>` | FNV-1a 128-bit content digest of the permit. |
| `PlanDigest` | `std::array<std::uint8_t,32>` | Host-supplied plan digest bound into the permit. |
| `Nonce` | `std::uint64_t` | Host-supplied one-time value bound into the permit. |
| `Tag` | `std::string` (≤ 63 bytes, printable ASCII, no NUL) | Scenario, deployment, environment, tool, interface, target. |
| `Action` | `enum class : std::uint32_t` bit values | Closed finite set (see §6.1). |
| `ActionMask` | `std::uint32_t` bitmask | Must contain only defined `Action` bits. |
| `Quota` | `{ QuotaKind kind; std::uint32_t limit; }` | Finite named quota. |
| `QuotaKind` | `enum class` | `Operations`, `Evidence`. Unknown kinds are invalid. |
| `LifecycleState` | `enum class` | §6.2. |
| `Result` | `enum class` | §8.1. |
| `FieldLocator` | `enum class` | Names the bound field for a `PermitMismatch`. |
| `Diagnostic` | bounded code sequence + optional locator | §8.2. |

**Digest.** `PermitId` is computed by canonicalizing every bound field into a byte sequence and
applying FNV-1a with a 128-bit output. It is a deterministic local bookkeeping identity for
exactly-once bookkeeping, **not** a cryptographic or security claim.

## 4. Time authority (component `validation_time_authority`)

### 4.1 Ownership and lifetime

`TimeAuthority` is **non-copyable and non-movable** (deleted copy/move constructors and
assignment). It owns a domain table and a mapping table; moving would silently invalidate the
injected host sources and regression baselines. Lifetime is explicit: construct with capacities,
destroy before any thread that used it exits. All methods are internally synchronized.

### 4.2 Clock domains and bounded reads

`declare_clock(id, source, kind, min, max)` registers a domain with an injected
`ClockSource = std::function<std::optional<Timestamp>()>`, a kind (`Monotonic` or `WallClock`),
and an inclusive `[min,max]` bound. `now(id)`:

1. Unknown domain → `UnknownClock`.
2. Host source returns `nullopt` → `ClockSourceFailure`.
3. Reading outside `[min,max]` → `ClockOutOfBounds`.
4. Monotonic domain and reading `<` prior reading → `ClockRegression` (baseline unchanged).
5. Otherwise record the reading as the new baseline and return it.

Reads never fabricate time and never fall back to another domain.

### 4.3 Directed mapping with tolerance

`declare_mapping(src, dst, offset, tolerance)` registers a **directed** rule. `convert(src, dst,
value)`:

1. Unknown `src` or `dst` → `UnknownClock`.
2. No declared `src→dst` mapping → `MissingMapping`. A declared `A→B` never enables `B→A`.
3. Compute `candidate = value + offset` with checked signed arithmetic → `ClockOverflow` if not
   representable, and `ClockOutOfBounds` if `candidate` is outside the destination domain bound.
4. Read the destination current time `dst_now` **without committing the monotonic baseline**
   (with the same failure semantics as `now` for source availability, bounds, and regression).
5. Compute the magnitude `|candidate − dst_now|` as a full-range unsigned distance over the
   ordering of the signed values: `candidate >= dst_now ? (std::uint64_t)candidate −
   (std::uint64_t)dst_now : (std::uint64_t)dst_now − (std::uint64_t)candidate`. This is exact
   over the entire signed 64-bit domain (maximum `UINT64_MAX`); it never wraps modulo 2^64 and
   never treats the top bit as a sign bit. If the distance exceeds `tolerance` →
   `ToleranceExceeded`.
6. Commit the destination monotonic baseline to `dst_now`, then return `candidate` attributed to
   `dst`. Steps 4–6 run in one critical section, so a rejected conversion (including
   `ToleranceExceeded`) leaves the baseline, the output value, and all authority state unchanged.

The tolerance check is therefore a live cross-check that the mapped source time agrees with the
destination clock within the declared tolerance. Regression and overflow are distinct from
tolerance failure and from each other, satisfying SR-004. Because the distance is computed from
the ordering of the original signed values without two's-complement wraparound, maximally
separated timestamps (`INT64_MIN`/`INT64_MAX` and vice versa) yield the correct `UINT64_MAX`
distance and fail any `tolerance < UINT64_MAX` (SR-003).

### 4.4 Concurrency

One `std::mutex` guards all mutable authority state. Concurrent `now`/`convert` calls serialize
into a deterministic total order. Because the baseline is updated under the same lock, concurrent
readers observe a consistent, race-free sequence.

---
## 5. Immutable permit (component `validation_permit`)

### 5.1 Bound envelope

A permit binds, exactly and immutably:

- one `SessionId` (session identity),
- one `PlanDigest` (plan digest),
- one `Tag` each for scenario, deployment, environment, tool, interface, and target,
- one `Nonce`,
- one validity interval `(validity_domain, valid_from, valid_until)` declared in a single clock
  domain, with `valid_from <= valid_until`,
- one allowed action set (a bounded list of explicitly allowed `ActionMask` values), and
- a bounded list of finite `Quota` entries.

### 5.2 Construction validation

The `PermitBuilder` rejects (returns `InvalidPermit` with the offending `FieldLocator`):

- any absent or default-initialised identity-bearing field (empty tag, zero session id, zero plan
  digest, empty allowed-action list, empty validity);
- any `ActionMask` containing an undefined `Action` bit;
- any `ActionMask` not listed explicitly (a composite value is never interpreted as its
  components — it must be listed verbatim to be allowed);
- any unknown `QuotaKind`, a zero `limit`, or more than the bounded quota count;
- a validity interval whose endpoints are out of range or inverted.

### 5.3 Identity and immutability

A built `Permit` exposes const accessors only. `PermitId` is the FNV-1a 128-bit digest over all
bound fields **including the nonce**, so a changed nonce produces a different `PermitId`. The
permit is copyable (value semantics) because it is immutable, and may be shared across threads
without synchronisation.

### 5.4 Runtime context

Consumption is presented with a `SessionContext` — the caller's asserted envelope with the same
fields. The manager compares `SessionContext` to the permit field-by-field (see §7.3); the first
mismatch is reported with its `FieldLocator`. This gives the exact field-mismatch matrix required
by SR-007.

## 6. Permit registry (component `validation_permit_registry`)

### 6.1 Controller-scoped, exactly-once consumption

The registry maintains two bounded sets per controller scope:

- consumed **permit identities** (`PermitId`), and
- consumed **session identities** (`SessionId`).

`try_consume(controller, permit_id, session_id)` performs a single atomic check-then-insert:

1. If `session_id` is already consumed → `SessionAlreadyConsumed`.
2. Else if `permit_id` is already consumed → `PermitAlreadyConsumed`.
3. Else if either bounded set is full → `CapacityExhausted` (consumption is refused, nothing is
   inserted).
4. Else insert both identities and return `Ok`.

Replay scope is **controller-scoped**: the same `PermitId` may not be consumed twice by the same
controller, and a `SessionId` bound to a consumed permit may not be consumed again. A changed
nonce changes `PermitId` but leaves `SessionId` unchanged, so the session-key check still rejects
it (`SessionAlreadyConsumed`), satisfying SR-009.

### 6.2 Boundedness

Both sets use fixed-capacity, `std::array`-backed open addressing. Sizes never exceed the
host-configured capacities; overflow is refused with `CapacityExhausted`, which is the explicit
exhaustion behavior rather than silent growth. The registry is non-copyable and non-movable and
is reached only under the manager's lock.

## 7. Session lifecycle and manager (components `validation_session`, `validation_session_manager`)

### 7.1 Controller identity, generation, and uniqueness scope

The manager is constructed with a host-supplied, non-zero **uniqueness scope** (`ManagerScope`,
16 bytes) carried in `ManagerConfig::scope`. The host MUST mint a fresh, distinct scope for every
manager instance and for every recreation of a manager (for example a fresh random or UUID per
construction); a zero scope is rejected at construction. This scope is the only source of
cross-instance and cross-recreation uniqueness.

`register_controller(controller_id, name)` registers a host-supplied, non-zero, globally unique
`ControllerId` under `name` and issues a `Generation` of 1. The manager never derives an identity
from the name or from a per-manager sequence, so a per-manager counter is **never** assumed
globally unique. Registering a name that is already current supersedes the previous identity in
a **bounded** superseded-controller window; presenting a zero or already-registered identity is
rejected with `InvalidController` (the controller table is left unchanged). A full controller
table with no evictable superseded entry yields `CapacityExhausted`.

A handle is the opaque quadruple
`SessionHandle{ ManagerScope scope; ControllerId controller; Generation generation; SessionId session; }`.
Handle validation compares `scope` first (see §7.2): a handle carrying a scope other than this
manager's is `ForeignHandle`, so a handle issued by a different manager instance or by a prior
recreation can never address a live session — no hash collision or guessed secret is needed.
Authenticity relies on the manager's internal table plus the host-controlled scope (opaque
issuance), not on cryptography — a bounded prototype control, recorded as such (§10).

### 7.2 Handle validation outcomes

| Condition | Result |
| --- | --- |
| Handle scope differs from this manager's scope | `ForeignHandle` |
| Quadruple matches no live session and the controller id is unknown | `InvalidHandle` (forged) |
| Controller id was never registered by this manager | `ForeignHandle` |
| Controller id is in the superseded window (same name, recreated) | `RecreatedController` |
| Controller id matches but generation is older than current | `StaleHandle` |
| Controller id and generation match but session id is not live | `SessionNotFound` |

A stale, foreign, recreated, or forged handle cannot address any live session; rejection leaves
all sessions unchanged.

### 7.3 Permit consumption and session creation

`consume(controller, permit, context, handle&)` runs in one critical section:

1. **Permit/context** — compare `context` to `permit` field-by-field; first mismatch →
   `PermitMismatch(locator)`.
2. **Replay** — `try_consume` (→ `SessionAlreadyConsumed`, `PermitAlreadyConsumed`,
   `CapacityExhausted`).
3. **Capacity** — live session table full → `CapacityExhausted`; no handle returned.
4. **Bind** — create the session in `declared`, bind the permit identity and quota counters, and
   return a current handle.

A failed creation returns no usable handle and leaves capacity and both consumed sets unchanged.

### 7.4 Lifecycle state machine

States: `declared`, `armed`, `active`, `closing`, `closed`, `expired`, `revoked`,
`evidence_incomplete`. `closed`, `expired`, `revoked`, and `evidence_incomplete` are terminal.

Actions and legal transitions:

| Action | Predecessor | Successor |
| --- | --- | --- |
| `Arm` | declared | armed |
| `Activate` | armed | active |
| `Close` | active | closing |
| `Finalize` | closing | closed |
| `Expire` | declared/armed/active/closing | expired |
| `Revoke` | declared/armed/active/closing | revoked |
| `MarkEvidenceIncomplete` | declared/armed/active/closing | evidence_incomplete |

Idempotent (safe) repeats return `AlreadyApplied` without changing state:

| Action | Current state giving `AlreadyApplied` |
| --- | --- |
| `Arm` | armed |
| `Activate` | active |
| `Close` | closing |
| `Finalize` | closed |
| `Expire` | expired |
| `Revoke` | revoked |
| `MarkEvidenceIncomplete` | evidence_incomplete |

Any action attempted from a terminal state returns `TerminalState`. Any other pair returns
`InvalidTransition`. The transition table is a `constexpr` static table, so it is exhaustive and
directly testable.

### 7.5 Per-transition validation order

`transition(handle, action, now_domain, now_value, diagnostic&)` validates in the declared order
and mutates only after every check passes. `now_domain`/`now_value` is the caller's current-time
claim; the manager resolves time through the authority (never by direct comparison) and compares
the authoritative time against the permit validity interval, which is expressed in the permit's
own declared domain:

1. **Handle** — `InvalidHandle` → `ForeignHandle` → `RecreatedController` → `StaleHandle` →
   `SessionNotFound` (first applicable).
2. **Context** — the session addressed by the handle must be the one bound to that handle.
3. **Time** — `now_domain`/`now_value` is a caller-supplied time **claim** and is never trusted
   directly. The manager resolves time through the authority in a fixed order:
   a. `now(now_domain)` obtains the authority's authoritative reading `auth_now`, **even when
      `now_domain == permit.validity_domain`** (→ `UnknownClock` → `ClockSourceFailure` →
      `ClockOutOfBounds` → `ClockRegression`). A same-domain operation therefore still checks
      domain registration, source availability, bounds, and regression.
   b. **Claim cross-check** — the claim `now_value` must agree with `auth_now`; the full-range
      unsigned distance `|now_value − auth_now|` must be zero. A divergent claim →
      `ToleranceExceeded`. This is the API semantic that prevents a caller-supplied stale time
      from authorizing an action: the authority's reading is authoritative, and a claim that does
      not agree with it cannot pass.
   c. If `now_domain != permit.validity_domain`, map the **authoritative** reading via
      `convert(now_domain, validity_domain, auth_now, mapped)` (→ `MissingMapping` →
      `ClockOverflow` → `ClockOutOfBounds` → `ToleranceExceeded`); otherwise the authoritative
      reading is already in the validity domain.
   d. Compare the resolved authoritative time against `[valid_from, valid_until)`: before →
      `PermitNotYetValid`, at/after → `PermitExpired`.
4. **Action** — `UndefinedAction` (undefined bits) → `ActionNotAllowed` (not in the permit's
   allowed set) → `TerminalState` → `InvalidTransition` (state legality).
5. **Quota** — the action's mapped quota (if any) must be non-zero, else `QuotaExhausted`.

Only then is the transition applied and the quota decremented atomically under the manager's
lock. `closed`, terminal transitions (`expired`, `revoked`, `evidence_incomplete`), and
`AlreadyApplied` results are stable and repeatable.

### 7.6 Session capacity and reclamation

Live sessions are bounded by `max_sessions`. A terminal or `closed` session's slot is reclaimed by
an explicit `Finalize`/terminal transition, permitting reuse; slot accounting is exact and
observable.

---
## 8. Diagnostics and precedence (component `validation_diagnostic`)

### 8.1 Result enum

The public `Result` is a closed, enumerable enum. The declared diagnostic precedence (highest
first) is:

| Rank | Result | Meaning |
| --- | --- | --- |
| 1 | `InvalidHandle` | handle does not match any live or registered controller binding |
| 2 | `ForeignHandle` | controller id was never registered by this manager |
| 3 | `RecreatedController` | controller id superseded by a recreated controller of the same name |
| 4 | `StaleHandle` | controller matches but generation is old |
| 5 | `SessionNotFound` | controller/generation match but session id is not live |
| 6 | `UnknownClock` | clock domain not declared |
| 7 | `ClockSourceFailure` | host time source returned no reading |
| 8 | `ClockOutOfBounds` | reading or mapped value outside declared bound |
| 9 | `ClockRegression` | monotonic reading earlier than prior reading |
| 10 | `ClockOverflow` | mapped value not representable |
| 11 | `MissingMapping` | no declared source→destination mapping |
| 12 | `ToleranceExceeded` | mapped value diverges from destination beyond tolerance |
| 13 | `PermitNotYetValid` | now before valid_from |
| 14 | `PermitExpired` | now at or after valid_until |
| 15 | `UndefinedAction` | requested mask contains an undefined action bit |
| 16 | `ActionNotAllowed` | requested action not in the permit's allowed set |
| 17 | `TerminalState` | transition attempted from a terminal state |
| 18 | `InvalidTransition` | legal-state conflict with a non-terminal state |
| 19 | `PermitMismatch` | context differs from permit in the locator field |
| 20 | `InvalidPermit` | permit construction validation failed |
| 21 | `SessionAlreadyConsumed` | session identity already bound to a consumed permit |
| 22 | `PermitAlreadyConsumed` | permit identity already consumed |
| 23 | `QuotaExhausted` | the action's mapped quota is zero |
| 24 | `CapacityExhausted` | a bounded table or set is full |
| 25 | `InvalidController` | a zero or duplicate controller identity was presented for registration |
| 26 | `AlreadyApplied` | safe idempotent repeat |
| 27 | `Ok` | success |

### 8.2 Diagnostic shape

`Diagnostic` is a bounded, ordered code sequence (capacity 8, highest precedence first) plus at
most one `std::optional<std::uint32_t>` locator. It contains **no** string, item, observation, or
free-form content field. The primary `Result` returned by an operation is `codes().front()`. The
same input yields the same sequence across runs and builds.

### 8.3 Precedence examples (asserted in tests)

- A foreign handle with a stale generation and an expired permit reports
  `[ForeignHandle]` (handle precedence wins).
- An expired permit with an undefined action reports `[PermitExpired]` (time precedes action).
- A permitted action attempted from a terminal state reports `[TerminalState]`.
- A mismatch in `Tool` reports `[PermitMismatch]` with locator `Tool`.

## 9. Concurrency, capacity, and emission

### 9.1 Concurrency model

- `TimeAuthority`: one `std::mutex`; concurrent `now`/`convert` serialize deterministically.
  `convert` commits the destination baseline only after every check passes, inside the same
  critical section, so a rejected conversion cannot advance a baseline (SR-015).
- `PermitRegistry`: `try_consume` is a single critical section, so N concurrent consumptions of
  one permit yield exactly one `Ok` and N−1 failures.
- `SessionManager`: one `std::mutex` over the controller and session tables; all transitions run
  under it, giving a total order and race-free shared state.
- No lock-free structure or shared mutable global is used. `TimeAuthority` and `SessionManager`
  (and `PermitRegistry`) are non-copyable/non-movable; `Permit` and `Diagnostic` are immutable
  values.

### 9.2 Bounded capacity summary

| Resource | Bound | Exhaustion result |
| --- | --- | --- |
| Clock domains | `max_domains` | `CapacityExhausted` |
| Mappings | `max_mappings` | `CapacityExhausted` |
| Consumed permit identities | `max_consumed_permits` | `CapacityExhausted` |
| Consumed session identities | `max_consumed_sessions` | `CapacityExhausted` |
| Live sessions | `max_sessions` | `CapacityExhausted` |
| Superseded-controller window | `max_superseded` | oldest evicted (documented) |
| Permit quotas | bounded quota array | `QuotaExhausted` |
| Diagnostic code sequence | capacity 8 | bounded by construction |

### 9.3 Zero normal-route emissions

The public API exposes no emission, transport, gateway, listener, journal, lease, dashboard,
persistent store, or external-service entry point. No nominal code path performs file, socket, or
environment I/O, and no logging/telemetry is produced. `SessionManager::emission_count()` returns
`0` and is never incremented.

## 10. Requirement allocation

| Software requirement | Allocating component(s) |
| --- | --- |
| T025-SR-001 | `validation_time_authority` |
| T025-SR-002 | `validation_time_authority` |
| T025-SR-003 | `validation_time_authority` |
| T025-SR-004 | `validation_time_authority` |
| T025-SR-005 | `validation_time_authority`, `validation_session_manager` |
| T025-SR-006 | `validation_time_authority` |
| T025-SR-007 | `validation_permit`, `validation_session_manager` |
| T025-SR-008 | `validation_permit` |
| T025-SR-009 | `validation_permit_registry` |
| T025-SR-010 | `validation_permit_registry`, `validation_session_manager` |
| T025-SR-011 | `validation_session_manager` |
| T025-SR-012 | `validation_session` |
| T025-SR-013 | `validation_session` |
| T025-SR-014 | `validation_session_manager` |
| T025-SR-015 | `validation_session`, `validation_session_manager` |
| T025-SR-016 | `validation_diagnostic` |
| T025-SR-017 | `validation_permit_registry`, `validation_session_manager` |
| T025-SR-018 | `validation_session_manager` (absence of emission surface) |

## 11. Decisions and unresolved integration limits

| # | Decision / limit | Effect |
| --- | --- | --- |
| D-1 | `PermitId` is FNV-1a 128-bit, not cryptographic. | Bounded local bookkeeping only; no security claim. |
| D-2 | Handle authenticity is opaque issuance against the manager table, not signing. | Bounded prototype control; general channel identity remains `XVE-SYS-0144` deferred to Security. |
| D-3 | Tolerance is a live cross-check of mapped value vs destination current time. | Deterministic and testable; hard real-time proof (`XVE-SYS-0147`) remains deferred. |
| D-4 | Consumption replay scope is controller-scoped, with bounded bookkeeping. | Exactly-once within a controller lifetime; global scope is not claimed. |
| D-5 | Concurrency is a coarse-grained mutex per owning component. | Deterministic total order; no lock-free structure. |
| D-6 | Quota kinds are the closed set `{Operations, Evidence}`. | Additional kinds are a later, reviewed extension. |
| D-7 | FR-015–FR-020 and FR-033 anchor allocation is preserved but unverified. | Exact allocation requires the authoritative predecessor text (protected review). |
| D-8 | No predecessor header is included or recreated. | Repository integration and source compatibility are protected host steps. |
| D-9 | Controller uniqueness is host-controlled: a fresh `ManagerScope` per instance/recreation plus a host-issued `ControllerId`; no per-manager counter is globally unique. | Stale, foreign, and recreated-controller handles cannot address a live session (SR-011). |
| D-10 | The caller's `now_domain`/`now_value` is a claim cross-checked against the authority's authoritative reading (exact agreement); the authority's reading is authoritative for validity. | A stale caller-supplied time cannot authorize an action (SR-005). |

