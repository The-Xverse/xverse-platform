# T014 Detailed Design — Bounded Lifecycle Rules and Declared-Policy Binding

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T014 (capability 007, slice `T-CORE`) |
| Stage / role | plan → detailed design (pre-code) |
| Revision | 1 |
| Baseline revision | `93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Realization vocabulary | T010 `bound_kind_vocabulary`, `overflow_policy_vocabulary`, `outcome_vocabulary`, `thread_safety_vocabulary`, `ownership_model`, `lifetime_model` |
| Classification | Public-safe engineering work product |

The rules below are normative for the implementation stage. The existing baseline behaviour of the
declaration, capacity, transition, compatibility, ownership, retention, diagnostic, and concurrency units
is preserved exactly; the new material is the additive declared-policy binding on a route generation and
its exact-handle read. No diagnostic code or validation phase is added. A conflict is resolved in favour of
the accepted source and recorded, not guessed.

## 2. Declaration rules (`T14-CMP-DECL`)

| Type | Capacity / range | Validation rule | Rejection |
| --- | --- | --- | --- |
| `EndpointSpec` | identity 1–128 bytes; digest exactly 64 | non-empty bounded endpoint identity; exact lowercase-hexadecimal 64-character plan digest; non-empty bounded provider identity; `direction ∈ {contract.source_direction, contract.target_direction}` | `required_field`, `invalid_digest`, `bound_exceeded`, `incompatible_direction` |
| `RouteSpec` | inherits endpoint fields; at most one declared policy | non-empty bounded route identity; exact digest; non-empty bounded provider identity; two distinct endpoints sharing plan, provider, contract, and source/target direction | `required_field`, `invalid_digest`, `route_incompatible` |
| `LifecycleConfiguration` | endpoint capacity 1–32; route capacity 1–32 | nonzero and no greater than `LifecycleController::kMaximumEndpoints`/`kMaximumRoutes` | `bound_exceeded` |

Ownership: caller-owns-value for inputs and values; the controller owns copied records. Lifetime:
invocation-scoped for inputs, value lifetime for declarations. Thread-safety: immutable-value. Failure:
`noexcept` factories return `Result<T>::failure` with a non-empty sorted `DiagnosticSet` and expose no
partial declaration.

The declaration types contain no address, protocol, physical-device identity, or domain-specific field.
Logical identity is validated independently of any provider, protocol, address, or physical realization
(T14-XB-2).

## 3. Bounded records and exact handle rules (`T14-CMP-CTRL`, `T14-CMP-HANDLE`)

### 3.1 Fixed-capacity record store

`LifecycleController` always contains fixed `std::array<std::optional<Record>, kMaximum…>` storage (32 and
32) and considers only the configured capacity prefix. A declaration:

1. scans the configured prefix for a nonclosed record with the same logical identity (reject
   `duplicate_identity`) and for a reusable slot, preferring an empty slot and then a closed slot, and
   preferring the same logical identity;
2. rejects `capacity_exhausted` when no reusable slot lies in the configured prefix;
3. rejects `generation_exhausted` when `next_generation_` has reached the `std::uint64_t` maximum;
4. otherwise resets the selected slot, copies the declaration into a new record with the next nonzero
   generation, increments the generation, and returns the exact handle.

Storage never grows and no declaration allocates on the operational path.

### 3.2 Exact generation-bound handle

Each successful declaration returns an opaque typed handle owning the issuing controller identity,
resource kind, logical identity, exact plan digest, and a nonzero strictly advancing generation.
Construction is private to `LifecycleController`; copies preserve the exact binding; assignment is deleted.
A typed endpoint/route API makes wrong-kind use a compile-time error, and the immutable `kind()` accessor
makes the binding inspectable.

Authentication accepts a handle only when the controller identity, resource kind, logical identity, plan
digest, and generation all equal a current record. Otherwise the operation returns exactly one
`invalid_handle` diagnostic in the `ownership` phase and mutates nothing.

## 4. Declared bounded delivery-policy binding (new in T014) (`T14-CMP-POLICY`)

### 4.1 Declared interface

```cpp
// additive overload; the existing 3-argument create is unchanged
[[nodiscard]] static Result<RouteSpec> RouteSpec::create(const RouteSpecInput& input,
                                                         const EndpointSpec& source,
                                                         const EndpointSpec& destination,
                                                         const FlowPolicy& policy) noexcept;

// RouteSpec additions
[[nodiscard]] bool has_policy() const noexcept;          // false when the route generation declared none
[[nodiscard]] const FlowPolicy* policy() const noexcept; // nullptr when none; owned view while RouteSpec lives

// LifecycleSnapshot addition
[[nodiscard]] bool policy_bound() const noexcept;        // false for endpoints; route record state

// LifecycleController addition
[[nodiscard]] Result<FlowPolicy> route_policy(const RouteHandle& handle) const noexcept;
```

`RouteSpec` gains one private `std::optional<FlowPolicy> policy_` member, set only by the 4-argument
factory through the shared private `create_impl` path; `operator==` is defaulted and therefore compares the
declared policy as well. The 3-argument factory leaves `policy_` empty. The existing
`EndpointSpec`/`RouteSpec`/`LifecycleConfiguration` public shapes that other slices consume are unchanged
(the overload is additive).

### 4.2 Semantics

- **Explicit.** A route generation either declared exactly one immutable `FlowPolicy` or declared none;
  the controller exposes that state through `RouteSpec::has_policy()`, `LifecycleSnapshot::policy_bound()`,
  and `route_policy()`.
- **Bounded.** At most one declared policy is stored per route record; the policy itself is already bounded
  and validated by T013, and T014 does not reinterpret `queue_depth`, `deadline_ms`, or `retry` as a
  lifecycle record capacity (T014-SR-016).
- **No substitution.** `RouteSpec::policy()` returns `nullptr` for an unbound route; `route_policy()`
  returns a stable failure for a generation that declared none. No default `FlowPolicy` is ever synthesised.
- **No silent upgrade.** There is no public operation that rebinds, replaces, weakens, or strengthens the
  declared policy of a live route generation. Changing the declared policy requires closing the route and
  recreating it, which issues a new generation; the earlier generation's policy is then unreachable through
  the earlier handle.
- **No bypass.** A declared policy never relaxes endpoint compatibility, ownership, state, or
  endpoint-retention checks; a policy-bound route fails every incompatible validate/activate exactly as an
  unbound route does.

### 4.3 Validation rules and diagnostics

The declared-policy binding adds no validation failure of its own: the 4-argument factory performs exactly
the 3-argument compatibility validation and then copies the already-validated policy. The only new
diagnostic is the absent-policy failure produced by `route_policy()`. It reuses the existing
`DiagnosticCode::required_field` (`XCOM-TYPE-E001`) and `ValidationPhase::route_declaration`; no code or
phase is added, so every existing code, phase, ordering key, and bound is unchanged.

| Condition | Code | Phase | Affected | Reason | Correction |
| --- | --- | --- | --- | --- | --- |
| `route_policy` on a generation that declared no policy | `XCOM-TYPE-E001` | `route_declaration` | route identity | `route generation declares no bounded flow policy` | `declare the route with an exact validated flow policy` |
| `route_policy` on a stale, foreign, wrong-kind, or digest/generation-mismatched handle | `XCOM-LIFE-E009` | `ownership` | handle identity | `handle does not identify the current resource owned by this controller` | `use the exact handle issued for the current controller and generation` |

The expected serialized absent-policy diagnostic is therefore
`route_declaration|error|XCOM-TYPE-E001|<route_id>|route generation declares no bounded flow policy|declare the route with an exact validated flow policy`.

## 5. Lifecycle state machine (`T14-CMP-CTRL`)

```text
declared -> validated -> active -> draining -> closed
    |           |          |          |
    +-----------+----------+----------+-> failed -> closed
```

| Operation | Permitted from | Idempotent in | Rejected otherwise |
| --- | --- | --- | --- |
| `validate_*` | `declared` | `validated` | `invalid_transition` |
| `activate_*` | `validated` | `active` | `invalid_transition` |
| `drain_*` | `active` (endpoint: only when no nonclosed route uses it) | `draining` | `invalid_transition`, `endpoint_in_use` |
| `fail_*` | `declared`, `validated`, `active`, `draining` | `failed` | `invalid_transition` |
| `close_*` | `draining`, `failed` (endpoint: no nonclosed route uses it) | `closed` | `invalid_transition`, `endpoint_in_use` |

`validate_route`/`activate_route` authenticate the exact current route, source, and destination handles and
require compatible identity, plan, provider, contract, and direction; `validate_route` accepts endpoints in
`validated` or `active`, `activate_route` requires both `active`. An endpoint may not drain or close while
any nonclosed route refers to it. Every rejection returns a byte-stable diagnostic and leaves the route,
source, and destination snapshots unchanged.

## 6. Failure semantics and outcome mapping

| Condition | Outcome (T010 vocabulary) | Observable result |
| --- | --- | --- |
| Missing/empty/over-bound declaration field | `rejected` | `DiagnosticSet` with `required_field`/`bound_exceeded`/`invalid_digest` |
| Incompatible endpoint/route declaration | `rejected` | `DiagnosticSet` with `incompatible_direction`/`route_incompatible` |
| Zero or over-maximum configured capacity | `rejected` | `DiagnosticSet` with `bound_exceeded` |
| Duplicate nonclosed identity or exhausted capacity | `rejected` | `DiagnosticSet` with `duplicate_identity`/`capacity_exhausted` |
| Generation space exhausted | `rejected` | `DiagnosticSet` with `generation_exhausted` |
| Stale/foreign/wrong-kind/unknown handle | `rejected` | `DiagnosticSet` with `invalid_handle` (`XCOM-LIFE-E009`) |
| Skipped or terminal transition | `rejected` | `DiagnosticSet` with `invalid_transition` (`XCOM-LIFE-E010`) |
| Endpoint retained by a nonclosed route | `rejected` | `DiagnosticSet` with `endpoint_in_use` (`XCOM-LIFE-E011`) |
| `route_policy` on a generation with no declared policy | `rejected` | `DiagnosticSet` with `required_field` (`XCOM-TYPE-E001`), `route_declaration` phase |
| Internal defect in a lifecycle type (not reachable from valid input) | `failed` | reported by the owning unit; never a partial value |
| Unknown outcome for any lifecycle factory | `failed` | never reported as success |

No lifecycle operation performs I/O; no rejected operation mutates the caller's input or leaves a
partially published record or partially advanced generation.

## 7. Bounds and concurrency summary

| Unit | Bound kind | Value | Overflow policy |
| --- | --- | --- | --- |
| Declarations | bytes (identity/user text) | identity ≤ 128; digest exactly 64 | `fail-closed` |
| Configuration | capacity (endpoints) | 1–32 | `reject` |
| Configuration | capacity (routes) | 1–32 | `reject` |
| Controller | generation | 1 … `std::uint64_t::max − 1` | `reject` (`generation_exhausted`) |
| Route record | declared policy | ≤ 1 `FlowPolicy` | `fail-closed` (single owned value) |
| Diagnostics | capacity | 32 entries per set | `fail-closed` |

Concurrency: every controller operation (declaration, authentication, query, compatibility checking,
transition, and the new `route_policy` read) locks one internal `std::mutex`; no callback is invoked under
the lock. Immutable declarations, handles, snapshots, and results support concurrent const reads. Concurrent
safe repeats converge on one state and generation without duplicating a record or advancing its generation.
The lifecycle adds no thread.

## 8. Doxygen design

Every new/changed public declaration carries a `@brief`; the new `RouteSpec` overload/accessors,
`LifecycleSnapshot::policy_bound`, and `LifecycleController::route_policy` additionally carry
`@ownership`, `@lifetime`, `@thread_safety`, and `@failure` clauses, with `@param`, `@return`, and
`@retval` where a parameter or result exists. The file header blocks keep the mandatory `@file`, `@brief`,
and the inherited `@ownership`/`@lifetime`/`@thread_safety`/`@failure` summary (group `xcom_core`). The
admitted `Doxyfile` configuration is not changed; strict declaration-level Doxygen stays `DOX-GAP-01`
(T011/T037).

## 9. Public-safety design

The candidate contains repository-relative paths, type and field names, stable code text, and pass/fail
outcomes only. It embeds no credential, private address, unrestricted payload, proprietary source excerpt,
environment-specific absolute host path, or sensitive deployment value. Diagnostic reasons and corrections
are fixed, bounded, non-sensitive text.

## 10. Design decisions and open items

- `D-01` — **The declared policy is bound to the route generation, not to the contract or the provider
  binding.** T013 records that the composition point is T014's decision (`T013-OPEN-01`); the route
  generation is the smallest additive choice that leaves every existing contract/item/provider consumer and
  test unchanged and keeps the ownership handle exact (`T14-OPEN-01`).
- `D-02` — **The binding is a new additive `RouteSpec::create` overload; the 3-argument factory and the
  `RouteSpecInput` aggregate are unchanged.** This keeps T015/T021 callers source-compatible and prevents
  an ownership-boundary crossing into another slice's tests. It also avoids a default-substitution risk:
  no route silently acquires a policy.
- `D-03` — **No diagnostic code or phase is added.** The absent-policy failure reuses
  `required_field`/`route_declaration`, so every existing diagnostic code, phase, ordering key, and bound
  is unchanged and `diagnostic.hpp`/`diagnostic.cpp` are not touched.
- `D-04` — **The implementation stays in the existing `endpoint_route_lifecycle.cpp` translation unit**,
  already compiled by the T012 `xverse_xcom_endpoint_route_lifecycle` target, so no CMake/`.cmake` change
  and no inherited T020 trace-link hash refresh is required (`T14-OPEN-02`).
- `D-05` — **The `RouteSpec` policy view is a nullable pointer to owned storage, not a default value.** It
  makes "declared none" an explicit state rather than a substituted default (T014-SR-008).
