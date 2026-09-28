# T015 Detailed Design — Provider Composition Rules, Declared-Policy Matching, and the Owned Loopback

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T015 (capability 007, slice `T-CORE`) |
| Stage / role | plan → detailed design (pre-code) |
| Revision | 1 |
| Baseline revision | `8aaa9eb29ffb349538552d709d4e6f37011b3e65` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Realization vocabulary | T010 `bound_kind_vocabulary`, `overflow_policy_vocabulary`, `outcome_vocabulary`, `thread_safety_vocabulary`, `ownership_model`, `lifetime_model` |
| Classification | Public-safe engineering work product |

The rules below are normative for the implementation stage. The existing baseline behaviour of the descriptor,
registration, requested-semantics validation, provider dispatch, loopback FIFO, recovery, diagnostic, and
concurrency units is preserved exactly; the new material is the additive declared-policy ↔ provider capability
matching inside `ProviderComposition::prepare_route` and exactly one new stable provider outcome. A conflict is
resolved in favour of the accepted source and recorded, not guessed.

## 2. Descriptor and registration rules (`T15-CMP-DESC`, `T15-CMP-REG`)

| Type | Capacity / range | Validation rule | Rejection |
| --- | --- | --- | --- |
| `ProviderDescriptor` | identity 1–128 bytes; version ≤ 32 bytes canonical `major.minor[.patch]` | non-empty bounded provider identity; canonical source contract version; non-empty bounded source-link identity; nonzero interaction mask ⊆ known bits; nonzero delivery mask ⊆ known bits; nonzero ordering mask ⊆ known bits; payload 1 – `kMaximumPayloadBytes` (65,536); routes 1–32; queue 1–32 | `required_field`, `invalid_version`, `bound_exceeded` |
| `ProviderRegistryConfiguration` | capacity 1 – `ProviderComposition::kMaximumProviders` (8) | nonzero and no greater than the fixed maximum | `bound_exceeded` |
| `ProviderComposition` registry | ≤ 8 slots; generation < `std::uint64_t::max` | scan only the configured prefix; reject a non-self-consistent or unsupported-version descriptor before retention; reject duplicate identity/instance, unsafe provider object identity, and a full registry | `invalid_descriptor`, `unsupported_contract_version`, `duplicate_provider`, `provider_capacity_exhausted` |

Registration retains a **non-owning** pointer to a caller-owned `CommunicationProvider`; the caller must
outlive the composition and every handle the composition issued. Registration is explicit and one-time per
provider object; there is no discovery, default provider, implicit fallback, or dynamic loading (`T015-XB-2`).
A rejected registration leaves every existing slot and generation unchanged; a successful registration issues
a strictly advancing nonzero generation.

## 3. Route preparation rules (`T15-CMP-DISPATCH`)

`ProviderComposition::prepare_route` evaluates, in this fixed order, and returns on the first failing step. No
step invokes a provider; only step 12 dispatches.

1. **Handle/declaration identity** — the route handle identity/digest and both endpoint handle identities/digests
   equal the supplied `RouteSpec` → else `route_mismatch`.
2. **Exact lifecycle authentication** — the route, source, and destination are current records of the supplied
   `LifecycleController` → else `lifecycle_mismatch`.
3. **Retained declaration equality** — the retained route copy equals `route_spec` and both retained endpoints
   share its identity, digest, provider, contract, and source/target direction → else `route_mismatch`.
4. **State** — route `validated`; both endpoints `validated` or `active` → else `lifecycle_mismatch`.
5. **Provider selection** — a registered provider with the route's logical provider identity exists → else
   `provider_mismatch`.
6. **Contract version** — `requirements.provider_contract_version` equals the retained descriptor version →
   else `unsupported_contract_version`.
7. **Interaction family** — `requirements.interaction_kind` equals the route contract's kind and is advertised →
   else `unsupported_interaction`.
8. **Declared-policy delivery claim (new in T015)** — see §4.1 → else `unsupported_delivery`.
9. **Declared-policy ordering claim (new in T015)** — see §4.1 → else `unsupported_ordering`.
10. **Declared-policy non-capability dimensions (new in T015)** — see §4.2 → else `unsupported_policy` or
    `queue_limit_exceeded`.
11. **Requested capability and limit validation (baseline)** — requested delivery advertised → else
    `unsupported_delivery`; requested ordering advertised → else `unsupported_ordering`; nonzero payload ≤
    advertised maximum → else `payload_limit_exceeded`; nonzero queue ≤ advertised maximum → else
    `queue_limit_exceeded`.
12. **Dispatch** — build the owned `ProviderRouteBinding` and invoke the selected provider's private
    `prepare`; a non-`prepared` provider outcome is mapped to a stable composition outcome
    (`interrupted_resource` when a value is returned with an unexpected outcome), and only a `prepared` result
    issues the exact `ProviderRouteHandle`.

Steps 8–10 apply **only** when `route_spec.has_policy()` is true; when it is false, steps 8–10 are skipped and
the behaviour is exactly the baseline (T015-SR-010). Because steps 6/7 and 11 are unchanged, an unbound
route's outcome sequence is byte-identical to the baseline.

## 4. Declared-policy matching (new in T015) (`T15-CMP-MATCH`)

### 4.1 Declared claim mapping (delivery and ordering)

A declared policy is satisfiable by a provider only when the provider advertises the exact claim the declaration
requires. The mapping is exact; a claim the admitted vocabulary cannot express is rejected rather than mapped to
a different guarantee (no strengthening, no weakening).

| `FlowPolicy::reliability()` | Required `DeliveryCapability` | Rule |
| --- | --- | --- |
| `best_effort` | `best_effort` | exact |
| `at_least_once` | `reliable` | `reliable` is the admitted claim that can honour at-least-once |
| `at_most_once` | none | no admitted capability bounds attempts to one → `unsupported_delivery` |
| `exactly_once` | none | stronger than `reliable` → `unsupported_delivery` |

| `FlowPolicy::ordering()` | Required `OrderingCapability` | Rule |
| --- | --- | --- |
| `unordered` | `unordered` | exact |
| `fifo` | `per_route_fifo` | exact |
| `priority` | none | no admitted capability expresses priority → `unsupported_ordering` |

For a policy-bound route, `requirements.delivery` and `requirements.ordering` **must equal** the mapped claims.
A weaker or stronger request, or a request against an unmappable declared claim, rejects with
`unsupported_delivery`/`unsupported_ordering` before dispatch. This makes the requested requirements and the
declared policy a single consistent decision instead of two independent claims (T015-SR-007, T015-SR-008).
The selected descriptor must additionally advertise the mapped bit; this is guaranteed by step 11 once
`requirements` equals the mapped claim, so the descriptor check remains the baseline check.

### 4.2 Declared non-capability dimensions (overflow, deadline, retry, queue depth)

The admitted providers advertise no overflow, deadline, or retry capability and implement a single reject-new
queue, so a declared policy whose non-capability dimensions ask for behaviour the provider does not implement
is rejected fail-closed rather than silently accepted.

| Declared value | Rule for a policy-bound route | Rejection |
| --- | --- | --- |
| `overflow == reject` | accepted (matches the reject-new implementation) | – |
| `overflow != reject` (`drop_oldest`, `drop_newest`, `coalesce`, `lossless_backpressure`, `fail_closed`) | not implemented by the selected provider | `unsupported_policy` |
| `deadline_ms == 0` | accepted (no timing claim is made) | – |
| `deadline_ms > 0` | no admitted provider implements a deadline | `unsupported_policy` |
| `retry == 0` | accepted (no retry is attempted) | – |
| `retry > 0` | no admitted provider implements a retry budget | `unsupported_policy` |
| `queue_depth >= requirements.queue_capacity` | the configured queue never exceeds the declared bound | – |
| `queue_depth < requirements.queue_capacity` | the provider queue would retain more than declared | `queue_limit_exceeded` |

`FlowPolicy::create` (T013) has already validated every declared number, so a negative `queue_depth` is not
reachable; the comparison is still written defensively. The declared `queue_depth` is **not** reinterpreted as
a provider or registry capacity (T015-SR-017).

### 4.3 Precedence and determinism

Checks execute in the fixed order of §3. When several defects are present, the first failing check decides the
outcome: `unsupported_delivery` precedes `unsupported_ordering`, which precedes `unsupported_policy`, which
precedes `queue_limit_exceeded`, which precedes the baseline descriptor checks. No provider is dispatched and no
record is mutated on any rejection, so a caller can compare the exact before/after provider snapshot and
lifecycle snapshot and observe no change.

## 5. Provider dispatch, operation, and loopback rules (`T15-CMP-DISPATCH`, `T15-CMP-LOOP`)

### 5.1 Exact-handle operations

`activate_route` requires the exact registered provider, the exact provider-local token, a route in
`validated`/`active`, and both endpoints active; the first activation transitions the lifecycle route after the
provider reports `activated`, and a repeat is safe while the route remains consistent. `submit` requires the
exact active handle, an item whose contract/interface/schema/kind/source/route/provider metadata equals the
route declaration, and a payload no larger than the prepared bound; it then reserves lossless observation
capacity before provider mutation when a hub is enabled. `receive`, `drain_route`, `close_route`,
`route_state`, and `reconcile_route` authenticate the exact handle and the embedded lifecycle route/endpoint
generations and state. An inauthentic, stale, foreign, wrong-state, or inactive request returns a stable
outcome (`invalid_provider_route_handle`, `lifecycle_mismatch`, `inactive_route`, `interrupted_resource`) and
mutates nothing (T015-SR-006, T015-SR-015).

### 5.2 Owned loopback semantics

`LoopbackProvider` owns fixed `std::array<std::optional<RouteRecord>, 4>` storage over the configured provider
prefix and one `std::array<std::optional<CommunicationItem>, 8>` reject-new FIFO per route. `prepare` reuses an
empty slot, then a same-identity closed slot, without growing storage; a duplicate nonclosed route identity or
an exhausted prefix rejects (`route_mismatch`/`route_capacity_exhausted`). `submit` rejects a full queue with
`queue_saturated` while preserving every queued item and the FIFO index; `receive` returns the oldest item as an
independent copy or `queue_empty`; a draining route rejects new submissions; `close` rejects while items remain
(`queued_items_remain`) and releases the resource only after an empty drain. All four interaction families are
exchanged deterministically. No callback, registry, filesystem, environment, process, socket, or network
operation occurs under or across the lock (T015-SR-012, T015-SR-013).

### 5.3 Replaceability and reconciliation

A second, independently implemented `CommunicationProvider` composes, registers, prepares, activates, and
exchanges items through the same boundary; a failure or rejection of one provider leaves every unrelated
registered provider and route unchanged (T015-SR-014). `reconcile_route` compares the provider-owned state with
the exact lifecycle generation/state and reports a mismatch as `interrupted_resource`, never as success; it
never infers ownership from a name or address (T015-SR-015).

## 6. Failure semantics and outcome mapping

| Condition | Outcome | Observable result |
| --- | --- | --- |
| Missing/empty/over-bound/out-of-vocabulary descriptor field | `rejected` | `invalid_descriptor` (`XCOM-PROV-E011`) with the fixed reason/correction |
| Unsupported contract version | `rejected` | `unsupported_contract_version` (`XCOM-PROV-E014`) |
| Duplicate provider identity/instance or full registry | `rejected` | `duplicate_provider` (`XCOM-PROV-E012`) / `provider_capacity_exhausted` (`XCOM-PROV-E013`); no slot mutated |
| Route/digest/provider/contract/direction mismatch | `rejected` | `route_mismatch` (`XCOM-PROV-E024`) or `provider_mismatch` (`XCOM-PROV-E025`) |
| Route or endpoint state mismatch, stale/foreign handle | `rejected` | `lifecycle_mismatch` (`XCOM-PROV-E022`) / `invalid_provider_route_handle` (`XCOM-PROV-E021`) |
| Requested interaction/delivery/ordering not advertised | `rejected` | `unsupported_interaction` (`XCOM-PROV-E015`) / `unsupported_delivery` (`XCOM-PROV-E016`) / `unsupported_ordering` (`XCOM-PROV-E017`) |
| Declared claim unmappable or contradicting the request | `rejected` | `unsupported_delivery` / `unsupported_ordering`; no dispatch |
| Declared overflow ≠ `reject`, or deadline/retry > 0 | `rejected` | **new** `unsupported_policy` (`XCOM-PROV-E030`); no dispatch |
| Declared `queue_depth` below the requested capacity, or requested capacity over the descriptor maximum | `rejected` | `queue_limit_exceeded` (`XCOM-PROV-E019`) |
| Payload over the prepared/requested bound | `rejected` | `payload_limit_exceeded` (`XCOM-PROV-E018`) |
| Full loopback queue | `rejected` (new item) | `queue_saturated` (`XCOM-PROV-E010`); queued items and FIFO index preserved |
| Submit/receive on an inactive route | `rejected` | `inactive_route` (`XCOM-PROV-E023`) |
| Close with retained items | `rejected` | `queued_items_remain` (`XCOM-PROV-E027`) |
| Provider/lifecycle state cannot reconcile | `rejected` | `interrupted_resource` (`XCOM-PROV-E028`) |
| Internal defect in a provider type (not reachable from valid input) | `failed` | reported by the owning unit; never a partial value |
| Unknown outcome for any provider operation | `failed` | never reported as success |

No provider operation performs I/O; no rejected operation mutates a registry slot, a provider route, a queue,
or a lifecycle record.

### 6.1 The new stable provider outcome

| Outcome | External text | Code | Message |
| --- | --- | --- | --- |
| `ProviderOutcome::unsupported_policy` | `unsupported-policy` | `XCOM-PROV-E030` | `declared route policy is not supported by the selected provider` |

The three existing mapping switches (`to_string`, `provider_diagnostic_code`, `provider_diagnostic_message`)
gain exactly this one case. No existing value is renamed, recoded, reordered, or removed, and no
`DiagnosticCode`/`ValidationPhase` is added, so `diagnostic.hpp`/`diagnostic.cpp` are not touched and the
provider-neutral observation boundary is unaffected (T015-SR-016).

## 7. Bounds and concurrency summary

| Unit | Bound kind | Value | Overflow policy |
| --- | --- | --- | --- |
| Registry | capacity (providers) | 1–8 (`kMaximumProviders`) | `reject` (`provider_capacity_exhausted`) |
| Registry | generation | 1 … `std::uint64_t::max − 1` | `reject` (`provider_capacity_exhausted`) |
| Descriptor | capabilities | nonzero masks within the declared vocabulary | `fail-closed` |
| Descriptor | limits | payload 1–65,536; routes 1–32; queue 1–32 | `fail-closed` |
| Loopback | capacity (routes) | 1–4 (`kMaximumRoutes`), prefix = descriptor `maximum_routes()` | `reject` (`route_capacity_exhausted`) |
| Loopback | capacity (queue) | 1–8 (`kMaximumQueueItems`), prefix = configured `queue_capacity` | `reject` (`queue_saturated`) |
| Loopback | route generation | 1 … `std::uint64_t::max − 1` | `reject` (`route_capacity_exhausted`) |
| Matching | declared policy | ≤ 1 `FlowPolicy` per route; matched once at preparation | `fail-closed` |

Concurrency: `ProviderComposition` serializes registry inspection/mutation with one mutex and resolves the
provider under that mutex, then releases it before any provider call; `LoopbackProvider` serializes every route
and queue operation with one mutex. No callback runs under a lock, and no path holds the registry and provider
locks at the same time (observation Hub reservations span dispatch without holding an X-COM mutex). Immutable
descriptors, handles, bindings, snapshots, and results support concurrent const reads. Concurrent submit/receive
delivers each accepted item exactly once with per-route FIFO order preserved. Neither unit adds a thread
(T015-SR-018).

## 8. Doxygen design

Every new/changed public declaration carries a `@brief`; the new `ProviderOutcome::unsupported_policy` value
and the documented declared-policy matching contract on `prepare_route` carry the inherited ownership/lifetime/
thread-safety/failure clauses, and `@param`/`@return`/`@retval` where a parameter or result exists. The file
header blocks keep the mandatory `@file`, `@brief`, and the inherited `@ownership`/`@lifetime`/`@thread_safety`/
`@failure` summary (group `xcom_core`). The admitted `Doxyfile` configuration is not changed; strict
declaration-level Doxygen stays `DOX-GAP-01` (T011/T037).

## 9. Public-safety design

The candidate contains repository-relative paths, type and field names, stable code text, bounded fixed
diagnostic text, and pass/fail outcomes only. It embeds no credential, private address, unrestricted payload,
proprietary source excerpt, environment-specific absolute host path, or sensitive deployment value. Diagnostic
reasons and corrections are fixed, bounded, non-sensitive text.

## 10. Design decisions and open items

- `D-01` — **The matching lives in `ProviderComposition::prepare_route`, not in a provider implementation.**
  The composition is the single trusted choke point that holds the selected descriptor and the exact lifecycle
  binding; a provider cannot be trusted to enforce its own capability claim. The loopback therefore needs no
  change (`T15-XB-4`).
- `D-02` — **The declared policy is derived from the existing `RouteSpec::has_policy()`/`policy()`.** No method
  parameter, aggregate field, or public signature changes, so every existing provider/observation caller and
  test compiles and behaves unchanged (`T015-SR-010`).
- `D-03` — **The mapping is exact and rejects unmappable claims rather than substituting.** Mapping
  `exactly_once` to `reliable` would silently weaken the declaration and mapping `at_most_once` to
  `best_effort` would silently strengthen it; both are prohibited, so they fail closed (`T015-OPEN-01`).
- `D-04` — **Non-capability dimensions are matched fail-closed.** Deadline, retry, and non-`reject` overflow
  have no admitted capability representation; accepting them would silently change behaviour, so a policy-bound
  route that declares them is rejected with the new `unsupported_policy` outcome rather than ignored.
- `D-05` — **Exactly one provider outcome is added.** `unsupported_policy` (`XCOM-PROV-E030`) is provider-local,
  additive, and owned by T015's `XCOM-SW-CORE-006` responsibility; no core diagnostic code or phase is added
  and no existing provider code/message changes.
- `D-06` — **The change stays in the existing `provider.cpp` translation unit.** The T012
  `xverse_xcom_provider_loopback` target already compiles it, so no CMake/`.cmake` change and no inherited T020
  trace-link hash refresh is required (`T015-OPEN-02`).
- `D-07` — **Focused T015 cases extend the existing provider-loopback executables.** No new CTest target is
  added, so the discovered test count stays at the baseline and no inherited test name or label changes.
