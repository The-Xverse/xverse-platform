# T025 Implementation Notes — Repaired Standalone C++20 Foundation

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T025 |
| Stage / role | implementation |
| Revision | 2 |
| Classification | SANITIZED |
| Source | `src/xverse/xcom/include/xverse/xcom/validation_session.hpp`, `src/xverse/xcom/src/validation_session.cpp` |
| Tests | `tests/validation_session_{tests,integration_tests,validation_tests}.cpp` |
| Design authority | `engineering/design.md` (rev 2), `engineering/verification-plan.md` (rev 2) |

This note records the repaired implementation that realises the four independently reproduced
correctness fixes (R1–R4 of `terminal-review.json`) plus the required regression coverage. It is
internal worker evidence; it is not accepted delivery.

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
false)` and `convert_impl(..., commit=false)`), so a transition never changes an authority
baseline (SR-015).

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

## 3. Deliberate orderings (visible, test-covered)

1. **Quota before idempotency.** `ValidationSession::apply` checks the operations quota before the
   `AlreadyApplied` repeat, matching the pre-written `QUO-01`/`QUO-02` expected results.
2. **Session capacity before replay bookkeeping.** `SessionManager::consume` reserves a live slot
   before `PermitRegistry::try_consume`, so a full session table reports `CapacityExhausted` and
   leaves both consumed sets unchanged.
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
