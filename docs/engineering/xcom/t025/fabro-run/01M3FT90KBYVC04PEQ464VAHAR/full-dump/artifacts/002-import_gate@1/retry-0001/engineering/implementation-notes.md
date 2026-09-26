# T025 Implementation Notes — Repaired Standalone C++20 Foundation

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T025 |
| Stage / role | implementation |
| Revision | 4 |
| Classification | SANITIZED |
| Source | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp`, `src/xverse/xcom/src/validation_session.cpp` |
| Tests | `tests/validation_session_{tests,integration_tests,validation_tests}.cpp` |
| Design authority | `engineering/design.md` (rev 3), `engineering/verification-plan.md` (rev 2) |

This note records the repaired implementation that realises the four independently reproduced
correctness fixes (R1–R4 of `terminal-review.json`) plus the required regression coverage. Revision 3
also repairs the two implementation-inspection findings F-IMP-01 (replay precedence over capacity,
transactional rejection) and F-IMP-02 (`@unitspec` ownership of `precedence_rank`/`compare`). It is
internal worker evidence; it is not accepted delivery. Revision 4 realises the R6 baseline contract:
a successful lifecycle transition establishes or advances the retained monotonic baselines it
observed, and every rejection leaves them unchanged. R5 (terminal-collection completeness) is not
addressed here and remains pending the host terminal collector.

## 2. Repaired contracts realised in code

### 2.1 R1 — every time decision resolves through the authority (SR-005)

`SessionManager::transition` now treats `now_domain`/`now_value` strictly as a caller **claim**:

1. `now(now_domain)` obtains the authoritative reading `auth_now` — **including the same-domain
   case** — so an undeclared, failed, out-of-bounds, or regressing clock is rejected
   (`UnknownClock`/`ClockSourceFailure`/`ClockOutOfBounds`/`ClockRegression`).
2. The claim is cross-checked against `auth_now` using the full-range unsigned distance; a
   non-zero distance is `ToleranceExceeded`, so a stale claim can never authorize an action.
3. The authoritative reading (never the claim) is mapped into the validity domain when needed,
   then compared against `[valid_from, valid_until)`.

The manager resolves time through the authority's non-mutating peek paths (`now_impl(..., commit=
false)` and `convert_impl(..., commit=false)`). Only after the transition succeeds does it advance
the retained baselines of the observed domains (R6, §2.5); every rejection returns before that
advance, so a rejected transition never changes an authority baseline (SR-015).

### 2.2 R2 — host-issued controller identity and a non-zero uniqueness scope (SR-011)

- `ManagerScope` (16 bytes) is a new type carried in `ManagerConfig::scope`. A zero scope is
  rejected at construction (`std::invalid_argument`).
- `register_controller(ControllerId id, std::string_view name)` registers a **host-issued, non-zero,
  globally unique** identity; the manager never derives identity from a name or a per-manager
  counter. A zero or already-registered identity is rejected with `InvalidController`.
- `SessionHandle` is the quadruple `{scope, controller, generation, session}`; handle validation
  compares the scope first, so a foreign or recreated manager's handle is `ForeignHandle` before
  any session is addressed.

### 2.3 R3 — full-range tolerance distance (SR-003)

`convert` computes `|candidate − dst_now|` with a file-local `unsigned_distance` that takes the
magnitude from the ordering of the original signed values (`candidate >= dst_now ? uint64(candidate)
− uint64(dst_now) : uint64(dst_now) − uint64(candidate)`). This is exact over the whole signed
64-bit domain (maximum `UINT64_MAX`) and never wraps modulo 2^64 or interprets a top bit as a sign.

### 2.4 R4 — transactional conversion state (SR-015)

The destination read is performed **without** committing the monotonic baseline; the baseline is
committed only after overflow, bounds, and tolerance all pass, inside the same critical section.
Every failed conversion preserves the baseline, the output value, and all authority state.

### 2.5 R6 — successful transitions establish the regression baseline (SR-004, SR-005, SR-015)

Previously `SessionManager::transition` resolved time only through the non-mutating peek paths, so a
successful transition left the authority baseline unset or stale; a later backward monotonic reading
was therefore accepted, applied, and charged quota. The repaired contract is:

1. Resolution remains non-mutating: `now_impl(..., commit=false)` reads the claim domain and
   `convert_impl(..., commit=false, &destination_reading)` reads the destination domain, capturing
   the destination host reading used for the tolerance check.
2. Every time, validity, action, state, and quota check runs before any mutation; a rejection returns
   before any baseline change.
3. Only when `ValidationSession::apply` returns `Result::Ok` does the manager call
   `TimeAuthority::advance_baseline` for the resolved (`now`) domain and, for a mapped resolution,
   for the destination (validity) domain. That authority method takes the authority mutex and never
   lowers an existing baseline (`!baseline || reading >= *baseline`), so it serializes with
   concurrent public `now`/`convert` calls and monotonic baselines never move backwards.
4. `AlreadyApplied`, every rejection, and every terminal-state repeat advance no baseline.

Regression coverage: `BUG_R6_UnseededSameDomain` (empty baseline established by a successful
transition), `BUG_R6_SeededSameDomain` (public-seeded baseline advanced by a successful transition),
`BUG_R6_MappedDomain` (both source and destination baselines advanced through a declared mapping),
`BUG_R6_RejectionPreservesState` (time, validity, action, state, and quota rejections leave
baselines, session state, and quota unchanged), and `BUG_R6_ConcurrentAuthorityAccess` (the deferred
advance races concurrent public reads without lowering the baseline).

## 3. Deliberate orderings (visible, test-covered)

1. **Quota before idempotency.** `ValidationSession::apply` checks the operations quota before the
   `AlreadyApplied` repeat, matching the pre-written `QUO-01`/`QUO-02` expected results.
2. **Replay before live-session capacity, with transactional insertion.** `SessionManager::consume`
   probes the registry read-only (`is_consumed_session` then `is_consumed_permit`) before it
   reserves a live slot, so a replayed permit on a full session table reports
   `SessionAlreadyConsumed`/`PermitAlreadyConsumed` rather than `CapacityExhausted`. The atomic
   `PermitRegistry::try_consume` runs only after a slot is available, so an unconsumed permit
   rejected on a full table is never persisted and both consumed sets stay unchanged.
3. **Terminal slot reclamation.** A slot whose session reaches a terminal/closed state is
   reclaimable by a later `consume`, freeing exactly one capacity slot.

## 4. Boundaries preserved

- Standalone C++20 standard library only; no predecessor header, no network/transport/journal/
  persistence surface; zero normal-route emission (`emission_count()` is always `0`).
- All result-returning public methods are `[[nodiscard]]`; rejections are non-mutating and produce
  ordered, payload-free `Diagnostic` codes.
- `TimeAuthority`, `PermitRegistry`, and `SessionManager` are non-copyable and non-movable
  (`static_assert`-enforced).

## 5. Protected checks

ThreadSanitizer (`STC-TIME-04`), CodeQL, ASan/UBSan (`STC-06`), predecessor integration/regression,
and external acceptance are **not executed** in this sandbox and are not claimed; they remain
protected host steps.
