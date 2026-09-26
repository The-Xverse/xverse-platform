# T025 Verification Plan — Named Cases and Expected Results (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T025 |
| Stage / role | design (verification intent) |
| Revision | 2 |
| Classification | SANITIZED |
| Design authority | `engineering/design.md` (rev 2) |
| Requirement authority | `engineering/requirements.md` (rev 1) |
| Test framework | GoogleTest / gmock, CTest labels `unit`, `integration`, `validation` |

This plan is written **before** implementation. The implementation stage must realise these
named cases with these expected results; weakening an expected result is a test-contract change
requiring review. Every case below names its input, stimulus, and exact expected outcome
(`Result` primary code, plus the ordered `Diagnostic` where relevant).

Deterministic injected inputs are used throughout: a fixed monotonic clock source, a fixed
wall-clock source, a fixed valid permit (see §2). No system clock, network, or filesystem is
consulted by nominal cases.

## 2. Standard fixtures

- `D_MONO`: monotonic clock domain, source returns an incrementing sequence controlled by the
  test (e.g. base 1000), bound `[0, 1'000'000]`.
- `D_WALL`: wall-clock domain, source returns a fixed value, bound `[0, 1'000'000]`.
- `P_VALID`: permit with session `S`, plan digest `PD`, tags `{scenario,deployment,environment,
  tool,interface,target}` = `{scn,dep,env,tool,iface,tgt}`, nonce `N`, validity `(D_MONO,
  valid_from=1000, valid_until=2000)`, allowed actions `{Arm,Activate,Close,Finalize}`, quotas
  `[{Operations, 10}]`.
- `CTX_VALID`: `SessionContext` identical to `P_VALID`.
- A manager configured with `max_sessions=8`, `max_domains=4`, `max_mappings=8`,
  `max_consumed_permits=16`, `max_consumed_sessions=16`.
- A host-supplied, non-zero `ManagerScope` `S_A` (distinct per manager instance/recreation) and
  a host-issued, non-zero `ControllerId` `C_A` (globally unique; never derived from a
  per-manager counter). Every nominal case declares the clock domain it uses and drives the
  injected source so that the claim `now_value` equals the authority's reading.

## 3. Time-authority cases (requirements T025-SR-001..SR-006)

| ID | Name | Stimulus | Expected |
| --- | --- | --- | --- |
| CLK-01 | Declare and query a known domain | `declare_clock(D_MONO,…)` then `now(D_MONO)` | `Ok`; returned value equals the source reading. |
| CLK-02 | Unknown clock | `now(0xDEAD)` (undeclared id) | `UnknownClock`; authority state unchanged. |
| CLK-03 | Source failure | `D_MONO` source returns `nullopt` | `ClockSourceFailure`. |
| CLK-04 | Out-of-bounds read | source returns `max+1` | `ClockOutOfBounds`; baseline unchanged. |
| CLK-05 | Monotonic regression | successive reads 1000 then 999 | second `now` → `ClockRegression`; baseline stays 1000; read 1001 → `Ok`. |
| CLK-06 | Declared mapping within tolerance | `declare_mapping(D_MONO,D_WALL,offset=+5,tol=10)`; both sources agree to 5 | `convert` → `Ok`, value = input+5, attributed to `D_WALL`. |
| CLK-07 | Reverse direction not implied | `convert(D_WALL,D_MONO,…)` with only MONO→WALL declared | `MissingMapping`. |
| CLK-08 | Undeclared pair | `convert(D_MONO,D_OTHER,…)` with no mapping | `MissingMapping`. |
| CLK-09 | Tolerance exceeded | mapped value diverges from destination `now` by `tol+1` | `ToleranceExceeded`. |
| CLK-10 | Tolerance boundary | divergence exactly `tol` | `Ok` (comparison is `<=`). |
| CLK-11 | Conversion overflow | `value=INT64_MAX`, `offset=+1` | `ClockOverflow`. |
| CLK-12 | Regression vs tolerance distinctness | construct a regression and a tolerance failure | codes are distinguishable (`ClockRegression` ≠ `ToleranceExceeded`). |
| CLK-13 | Full-range distance, negative→positive extreme | source `INT64_MIN`, destination now `INT64_MAX`, offset 0, full-range bounds, tolerance 1 | `ToleranceExceeded` (distance is `UINT64_MAX`, not 1). |
| CLK-14 | Full-range distance, positive→negative extreme | source `INT64_MAX`, destination now `INT64_MIN`, offset 0, full-range bounds, tolerance 1 | `ToleranceExceeded` (distance is `UINT64_MAX`). |
| CLK-15 | Full-range distance boundary | distance exactly `UINT64_MAX`; tolerance `UINT64_MAX` vs `UINT64_MAX−1` | tolerance `UINT64_MAX` → `Ok`; `UINT64_MAX−1` → `ToleranceExceeded`. |
| CLK-16 | Failed conversion preserves destination baseline | initialize destination baseline 100 via a successful read; change source reading to 200; convert with a mapping that fails `ToleranceExceeded` | `ToleranceExceeded`; destination baseline remains 100; subsequent `now` is unaffected (no spurious `ClockRegression`). |
| CLK-17 | Every conversion failure preserves baseline | `UnknownClock`, `MissingMapping`, `ClockOverflow`, `ClockOutOfBounds`, `ClockSourceFailure`, `ClockRegression`, `ToleranceExceeded` | baseline and output byte-identical before/after each failure (SR-015). |

## 4. Nominal cases (T025-SR-005, SR-012, SR-013)

| ID | Name | Stimulus | Expected |
| --- | --- | --- | --- |
| NOM-01 | Happy-path lifecycle | consume `P_VALID` with `CTX_VALID`, then `Arm`→`Activate`→`Close`→`Finalize` at `now=1500` (D_MONO) | consume `Ok` (handle issued, state `declared`); each step `Ok`; final state `closed`. |
| NOM-02 | In-domain validity | transition at `now=1500` within `[1000,2000)` | `Ok`. |
| NOM-03 | Foreign-domain validity with mapping | `now_domain=D_WALL`, mapping D_WALL→D_MONO declared, mapped into `[1000,2000)` | `Ok` after `convert`. |
| NOM-04 | Foreign-domain validity without mapping | `now_domain=D_WALL`, no mapping declared | `MissingMapping`. |

## 5. Permit mismatch matrix (T025-SR-007)

Each row keeps every other field equal to `CTX_VALID` and changes exactly one field.

| ID | Changed field | Expected |
| --- | --- | --- |
| MIS-01 | session id | `PermitMismatch`, locator `SessionId`. |
| MIS-02 | plan digest | `PermitMismatch`, locator `PlanDigest`. |
| MIS-03 | scenario | `PermitMismatch`, locator `Scenario`. |
| MIS-04 | deployment | `PermitMismatch`, locator `Deployment`. |
| MIS-05 | environment | `PermitMismatch`, locator `Environment`. |
| MIS-06 | tool | `PermitMismatch`, locator `Tool`. |
| MIS-07 | interface | `PermitMismatch`, locator `Interface`. |
| MIS-08 | target | `PermitMismatch`, locator `Target`. |
| MIS-09 | nonce | `PermitMismatch`, locator `Nonce`. |
| MIS-10 | allowed action set (drop one allowed mask) | `PermitMismatch`, locator `AllowedActions`. |
| MIS-11 | validity interval | `PermitMismatch`, locator `Validity`. |
| MIS-12 | quota list | `PermitMismatch`, locator `Quota`. |
| MIS-13 | (baseline) all fields equal | consume `Ok`, handle issued. |

Each mismatch must be non-mutating: consumed sets, session capacity, and authority state are
unchanged after the rejected consume.

## 6. Replay matrix (T025-SR-009)

| ID | Name | Stimulus | Expected |
| --- | --- | --- | --- |
| RP-01 | Exact permit re-presentation | consume `P_VALID`/`CTX_VALID`, then consume again | first `Ok`; second `SessionAlreadyConsumed`. |
| RP-02 | Changed nonce, same session | consume `P_VALID`, then consume `P_VALID'` (nonce `N+1`, same session `S`) | second `SessionAlreadyConsumed` (session identity already consumed). |
| RP-03 | Same permit, different session | consume `P_VALID`, then consume same `PermitId` with a different session id | `PermitAlreadyConsumed`. |
| RP-04 | Permit bound to another session | after RP-03's first consume, present the already-bound permit for a third session | `PermitAlreadyConsumed`. |
| RP-05 | Independent permits/sessions | consume two distinct valid permits | both `Ok`. |

## 7. Quota and capacity boundaries (T025-SR-010, SR-014)

| ID | Name | Setup | Expected |
| --- | --- | --- | --- |
| QUO-01 | Quota limit 1 | permit quota `{Operations,1}` | first mutating transition `Ok`, next `QuotaExhausted`; state unchanged on exhaustion. |
| QUO-02 | Quota boundary N | permit quota `{Operations,3}` | third transition `Ok`, fourth `QuotaExhausted`. |
| QUO-03 | Session capacity | fill `max_sessions=8` | 8 consumes `Ok`; 9th `CapacityExhausted` with no handle. |
| QUO-04 | Slot reclamation | fill, then `Finalize`/terminal one session | freed slot reusable; a new consume `Ok`. |
| QUO-05 | Consumed-identity capacity | `max_consumed_permits=2`, consume 3 distinct permits | 3rd consume `CapacityExhausted`; no partial insertion. |
| QUO-06 | Exhaustion is non-mutating | a `QuotaExhausted` and a `CapacityExhausted` case | counters, sets, and state identical before/after. |

## 8. Lifecycle transition table (T025-SR-012, SR-013)

`P_VALID` allows `{Arm,Activate,Close,Finalize}`; all rows at `now=1500`.

| ID | Start state | Action | Expected |
| --- | --- | --- | --- |
| LIF-01 | declared | Arm | `Ok` → armed |
| LIF-02 | armed | Activate | `Ok` → active |
| LIF-03 | active | Close | `Ok` → closing |
| LIF-04 | closing | Finalize | `Ok` → closed |
| LIF-05 | armed | Expire | `Ok` → expired (terminal) |
| LIF-06 | active | Revoke | `Ok` → revoked (terminal) |
| LIF-07 | active | MarkEvidenceIncomplete | `Ok` → evidence_incomplete (terminal) |
| LIF-08 | expired | Arm | `TerminalState` (no outgoing transition) |
| LIF-09 | closed | Arm | `TerminalState` |
| LIF-10 | declared | Activate | `InvalidTransition` |
| LIF-11 | active | Arm | `InvalidTransition` |
| LIF-12 | armed | Arm | `AlreadyApplied` (safe repeat; state stays armed) |
| LIF-13 | closed | Finalize | `AlreadyApplied` |
| LIF-14 | revoked | Revoke | `AlreadyApplied` |
| LIF-15 | declared | Close | `InvalidTransition` |
| LIF-16 | every state reachable | table-driven walk of all 8 states | each state reached via its defined operation |

## 9. Handle ownership and recreation (T025-SR-011)

| ID | Name | Stimulus | Expected |
| --- | --- | --- | --- |
| HND-01 | Current handle | transition with the handle returned at consume | `Ok`. |
| HND-02 | Stale handle | save handle, then advance controller generation, reuse old handle | `StaleHandle`. |
| HND-03 | Foreign handle | handle carrying a controller id never registered | `ForeignHandle`. |
| HND-04 | Recreated controller | re-register same controller name (new id), reuse the old handle | `RecreatedController`. |
| HND-05 | Forged handle | handle with random controller/session bytes | `InvalidHandle`. |
| HND-06 | Borrowed session id | valid controller+generation, but session id of a different controller's session | `SessionNotFound`. |
| HND-07 | Rejection isolates sessions | any rejected handle case | no other live session changes state. |
| HND-08 | Cross-manager handle (distinct scopes) | two managers with distinct scopes each register the same name and host-issued id; manager B receives manager A's handle | `ForeignHandle`; B's target session state and counters unchanged. |
| HND-09 | Destruction and recreation | recreate a manager with a fresh scope after destroying the original; reuse the pre-recreation handle | `ForeignHandle`; no live session is addressed. |
| HND-10 | Duplicate controller identity | register the same host-issued `ControllerId` twice in one manager | second registration rejected (`InvalidController`), controller table unchanged. |
| HND-11 | Zero controller identity / zero scope | register a zero `ControllerId`; construct a manager with a zero scope | registration rejected (`InvalidController`); construction rejected. |

## 10. Concurrency (T025-SR-017)

| ID | Name | Stimulus | Expected |
| --- | --- | --- | --- |
| CON-01 | Concurrent double consumption | 16 threads consume the same `P_VALID` | exactly 1 `Ok`; 15 `SessionAlreadyConsumed`. |
| CON-02 | Concurrent same transition | 16 threads `Arm` one session | exactly 1 `Ok`; 15 `AlreadyApplied`; final state `armed`. |
| CON-03 | Concurrent distinct permits | 8 threads consume 8 distinct permits | 8 `Ok`. |
| CON-04 | Concurrent authority reads | threads call `now(D_MONO)` | no data race (TSan clean); each read deterministic. |
| CON-05 | Mixed consume/transition stress | bounded loop across permits and transitions | no duplicate success, no corrupted state, no exception. |

## 11. No-mutation-on-rejection (T025-SR-015)

Every negative case in §3–§10 must additionally assert a **snapshot equality** across the
manager, registry, and authority: session state, consumed permit set, consumed session set,
quota counters, live-session count, and authority regression baselines are byte-identical before
and after the rejected call.

| ID | Policy case | Expected |
| --- | --- | --- |
| NOMUT-01 | Each mismatch row MIS-01..MIS-12 | snapshot equality after `PermitMismatch`. |
| NOMUT-02 | Each replay row RP-01..RP-04 | snapshot equality after rejection. |
| NOMUT-03 | Each clock row CLK-02..CLK-11 | authority state unchanged after the failure. |
| NOMUT-04 | LIF-08..LIF-15 | state unchanged after `TerminalState`/`InvalidTransition`/`AlreadyApplied`. |
| NOMUT-05 | QUO-01, QUO-03, QUO-05 exhaustion | no partial application; counters and sets unchanged. |
| NOMUT-06 | Rejection isolation | rejecting session A leaves session B untouched. |
| NOMUT-07 | Failed conversion transactional state | each conversion failure in CLK-16/CLK-17 | destination baseline, output value, session state, quota counters, and permit bookkeeping all byte-identical before/after; a subsequent operation observes no `ClockRegression` attributable to the rejection. |

## 12. Zero-emission (T025-SR-018)

| ID | Name | Check | Expected |
| --- | --- | --- | --- |
| ZEM-01 | API surface | enumerate public symbols | no emission/transport/journal/persistence entry point exists. |
| ZEM-02 | Emission counter | run full nominal scenario (NOM-01) | `emission_count()` is `0` before and after. |
| ZEM-03 | No I/O | static scan + file-descriptor delta | nominal path opens no file/socket and performs no environment I/O. |

## 13. Static checks (T025-SR-006, SR-016, SR-018)

| ID | Tool / check | Expected |
| --- | --- | --- |
| STC-01 | `std::is_copy_constructible_v`/`is_move_constructible_v` | `false` for `TimeAuthority`, `PermitRegistry`, `SessionManager`. |
| STC-02 | clang-tidy + source scan | no raw cross-domain timestamp comparison; every comparison via the authority. |
| STC-03 | `static_assert` on `Diagnostic` members | holds only enumerable codes and a numeric locator (no string/payload). |
| STC-04 | Doxygen (`WARN_AS_ERROR=YES`) | strict public-API documentation passes. |
| STC-05 | clang-format / clang-tidy / gcovr | clean formatting, no enabled-tidy diagnostics, coverage recorded. |
| STC-06 | ASan/UBSan + TSan run | no memory/UB errors; no data race. |

## 14. Case-to-requirement mapping

| Group | Requirement(s) |
| --- | --- |
| CLK-01..CLK-17 | T025-SR-001, SR-002, SR-003, SR-004, SR-006 |
| NOM-01..NOM-04 | T025-SR-005, SR-012, SR-013 |
| MIS-01..MIS-13 | T025-SR-007 |
| RP-01..RP-05 | T025-SR-009 |
| QUO-01..QUO-06 | T025-SR-010, SR-014 |
| LIF-01..LIF-16 | T025-SR-012, SR-013 |
| HND-01..HND-11 | T025-SR-011 |
| CON-01..CON-05 | T025-SR-017 |
| NOMUT-01..NOMUT-07 | T025-SR-015 |
| ZEM-01..ZEM-03, STC-03 | T025-SR-018, SR-016 |
| STC-01..STC-06 | T025-SR-006, SR-016, SR-018 |
| ADV-R1..ADV-R4 | T025-SR-005, SR-003, SR-011, SR-015 |

## 15. Independent-review adversarial regression cases (terminal-review.json R1–R4)

Each row records the exact reproduced rejected state from the independent review probe and the
subsequent required observation. These cases are mandatory and are **not** weakenable.

| ID | Reproduced probe (rejected state) | Stimulus (correcting setup) | Required subsequent observation |
| --- | --- | --- | --- |
| ADV-R1a | `transition` succeeded with **no clock declared** (same-domain path skipped the authority). | Consume a valid permit; call `transition(handle, Arm, D_UNDECLARED, value)` where `D_UNDECLARED` has no declared domain. | `UnknownClock`; session state remains `declared`; manager/authority state byte-identical. |
| ADV-R1b | After authority now=2500 and permit end=2000, caller time=1500 **still succeeded** (stale claim). | Declare `D_MONO` whose source returns 2500; permit `[1000,2000)`; call `transition(handle, Arm, D_MONO, 1500)`. | Rejected: claim 1500 diverges from authoritative 2500 → `ToleranceExceeded`; session state remains `declared`. |
| ADV-R1c | Same-domain out-of-bounds / regressing / failed clocks were never checked. | Declare `D_MONO` with source returning `max+1` (out of bounds), then a regressing sequence, then `nullopt`. | `ClockOutOfBounds`, `ClockRegression`, `ClockSourceFailure` respectively; each leaves state unchanged. |
| ADV-R1d | Same-domain expired clock was never checked. | Declare `D_MONO` source returns 2500; permit end 2000; claim 2500 (exact agreement). | `PermitExpired`; state unchanged. |
| ADV-R2a | Two managers registered the same first name; manager two **accepted manager one's handle** and mutated its session. | Two managers with distinct `ManagerScope` values each register the same name/id; manager B receives A's handle. | `ForeignHandle`; B's target session state and counters unchanged. |
| ADV-R2b | Destruction + recreation reproduced the same collision. | Recreate a manager with a fresh scope; reuse the pre-recreation handle. | `ForeignHandle`; no live session is addressed. |
| ADV-R3 | `INT64_MIN` and `INT64_MAX` with tolerance=1 **returned Ok**. | `convert` with source `INT64_MIN`, destination now `INT64_MAX`, offset 0, full-range bounds, tolerance 1. | `ToleranceExceeded` (distance `UINT64_MAX`); output and baseline unchanged. |
| ADV-R4 | A conversion rejected by tolerance **advanced the destination baseline from 100 to 200**. | Initialize destination baseline 100; change source reading to 200; request a conversion that fails `ToleranceExceeded`. | `ToleranceExceeded`; baseline stays 100; a subsequent operation observes no `ClockRegression` from the rejection. |

