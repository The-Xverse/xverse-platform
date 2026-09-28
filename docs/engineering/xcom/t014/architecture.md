# T014 Architecture — Bounded Endpoint/Route Lifecycle and Declared-Policy Binding Boundary

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T014 (capability 007, slice `T-CORE`) |
| Stage / role | plan → architecture |
| Revision | 1 |
| Baseline revision | `93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-005`, `XCOM-CMP-004`, `XCOM-INV-02`); `docs/engineering/xcom/t011/architecture.md` (build envelope); `docs/engineering/xcom/t012/architecture.md` (subtree build/test contract) |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T014 is the **bounded endpoint/route control plane** of the X-COM core. It occupies the seam between the
T013 immutable value/contract/policy model and the T015 provider binding. It owns no provider, transport,
observation, stimulation, or gateway behaviour; it owns the finite, serialized lifecycle that turns
immutable declarations into exactly-issued generation-bound resources and binds the declared bounded
delivery policy to a route generation.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract
   → T013 core value/contract/item/diagnostic/policy types
   → T014 endpoint/route lifecycle + declared-policy binding (this document)
   → T015 provider/loopback → T016 core tests
   → { T-XDL, T-OBS, T-STIM } → T-INTG (T035–T038) → T-REVIEW (T039/T041)
```

T014 is a **production-path** slice: the deterministic gate requires at least one changed
`src/xverse/xcom/**` path. The change is the additive declared-policy binding on the route generation plus
its exact-handle read; the existing declaration, capacity, transition, compatibility, and ownership
mechanics are re-verified unchanged. No build file, XDL schema, contract, provider, or later-slice
interface changes.

## 3. Boundary and context

### 3.1 System context

```text
        ┌──────────── XDL / io.xverse.xcom Profile + activation plan (read-only, T017/T019) ───────────┐
        │  declared bounded delivery policy (queue/ordering/reliability/deadline/overflow/retry)        │
        └──────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                                   │ already decoded + validated upstream
   ┌──────────────── T014 endpoint/route lifecycle (src/xverse/xcom, xverse::xcom) ─────────────────────┐
   │  endpoint_route_lifecycle.hpp/.cpp                                                                 │
   │   EndpointSpec · RouteSpec (+ declared FlowPolicy) · LifecycleConfiguration                        │
   │   EndpointHandle · RouteHandle · LifecycleSnapshot                                                 │
   │   LifecycleController: declare / snapshot / declaration / validate / activate / drain / fail /     │
   │                       close / route_policy   — one mutex, fixed arrays, exact handle auth          │
   └──────────────────────────────────────────┬───────────────────────────────────────────────────────┘
                                              │ immutable declarations, handles, snapshots, diagnostics
   ┌──────────────────────────────────────────▼───────────────────────────────────────────────────────┐
   │  consumers (read-only): T015 provider/loopback (route_spec/handle), T016 tests, T019 plan model,   │
   │  T021 observation, T025 validation session                                                          │
   └──────────────────────────────────────────────────────────────────────────────────────────────────┘
        ┌──────────── T013 immutable values (read-only): CommunicationContract, FlowPolicy ─────────────┐
        │  FlowPolicy = declared bounded delivery policy; DiagnosticCode/ValidationPhase/DiagnosticSet   │
        └────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T14-XB-1` Raw input vs validated declaration | call-scoped `EndpointSpecInput`, `RouteSpecInput`, `LifecycleConfigurationInput` | immutable published declarations | Every published declaration is complete and validated; a rejected input yields only a non-empty `DiagnosticSet`, never a partial or default-substituted value. |
| `T14-XB-2` Declaration vs issued resource | immutable `EndpointSpec`/`RouteSpec` values | controller-owned generation-bound records and handles | Only the exact issued handle for the current controller and generation authenticates a record; names, addresses, and stale generations never grant ownership. |
| `T14-XB-3` Declared policy vs provider capability | the immutable `FlowPolicy` bound to a route generation | provider delivery/ordering capability and wire enforcement (T015) | T014 binds and exposes the declaration exactly; it substitutes no default, strengthens nothing, and matches no provider. |
| `T14-XB-4` Core vs later slices | `xverse::xcom` lifecycle types | provider/observation/stimulation/gateway units | Later slices depend on T014; T014 depends on no later slice and includes no provider/transport type. |
| `T14-XB-5` Repository vs environment | committed source, tests, work products | admitted build inputs, build trees, host paths | Committed files are public-safe and offline; no ambient, network, filesystem, or process access is introduced. |

### 3.3 Prohibited elements (must remain absent)

No TCP listener, external network peer, discovery, package manager/registry, filesystem access, process
execution, legacy repository/binary access, dynamic plugin discovery, domain-specific primitive (ECU, CAN,
SOME/IP, Zenodo, or product name), new admitted dependency, competing configuration language, or unbounded
resource. These inherit the T007 global prohibitions, the T011 envelope, the T012 build contract, and the
constitution.

## 4. Components

Each component maps to a unit in `unit-specifications.md`. `T14-CMP-*` names are local to this document;
the accepted `XCOM-DU-006` identifier is the authorised design unit.

### 4.1 Lifecycle components

- **`T14-CMP-DECL`** (`XCOM-DU-006`) — `endpoint_route_lifecycle.hpp`/`.cpp`: `EndpointSpec`,
  `RouteSpec` (with the **new** owned declared `FlowPolicy`), `ResourceKind`, `LifecycleState`, and their
  validation. Bounded, value-owned, exception-free content.
- **`T14-CMP-CONFIG`** (`XCOM-DU-006`) — the `LifecycleConfiguration` finite-capacity value.
- **`T14-CMP-HANDLE`** (`XCOM-DU-006`) — the opaque `EndpointHandle`/`RouteHandle` exact ownership tokens.
- **`T14-CMP-SNAP`** (`XCOM-DU-006`) — the immutable `LifecycleSnapshot` observation, including the **new**
  declared-policy-bound flag.
- **`T14-CMP-CTRL`** (`XCOM-DU-006`) — the serialized fixed-capacity `LifecycleController` and its
  declaration, authentication, transition, and **new** exact-handle declared-policy read.
- **`T14-CMP-POLICY`** (`XCOM-DU-006`, **new in T014**) — the declared bounded delivery-policy binding on a
  route generation, realised through the `RouteSpec` overload and the controller read.

### 4.2 Work-product components

- **`T14-WP`** — the T014 repository-owned work-product set (`requirements.md`, `architecture.md`,
  `detailed-design.md`, `unit-specifications.md`, `verification-plan.md`, `implementation.md`,
  `internal-review.json`, and `reports/xcom-queue/t014-package.json`).

### 4.3 Consumed components (read-only)

`XCOM-CMP-004` core value/contract/policy types (`FlowPolicy`, `CommunicationContract`, `EndpointDirection`,
`DiagnosticCode`, `ValidationPhase`, `DiagnosticSet`), `XCOM-CMP-006` provider, `XCOM-CMP-007` owned
loopback, `XCOM-CMP-008` observation, `XCOM-CMP-009` validation session, and the XDL Profile/plan schema are
consumed or matched but neither implemented nor altered by T014. The declared `FlowPolicy` is consumed from
`contract.hpp`; no vocabulary is added.

## 5. Data flow (ordered)

1. **Construct input** — a consumer builds a call-scoped `EndpointSpecInput`, `RouteSpecInput`,
   `LifecycleConfigurationInput`, or an already-validated `FlowPolicy` (from T013).
2. **Validate and bind** — `EndpointSpec::create` / `RouteSpec::create` validate bounded identity, digest,
   provider, contract, direction, and endpoint compatibility; the additive `RouteSpec::create` overload
   copies the supplied `FlowPolicy` into owned storage as the route's declared policy.
3. **Declare** — `LifecycleController::declare_endpoint`/`declare_route` authenticate the configured
   capacity and duplicate state, select a reusable empty/closed slot without growing storage, advance the
   controller generation, copy the declaration into the bounded record, and return the exact handle.
4. **Observe** — `endpoint_snapshot`/`route_snapshot` authenticate the exact current handle and return an
   owned `LifecycleSnapshot`; a route snapshot reports `policy_bound()`. `route_policy` authenticates the
   exact current route handle and returns the exact declared `FlowPolicy` (or a stable diagnostic when the
   generation declared none).
5. **Transition** — `validate`/`activate`/`drain`/`fail`/`close` authenticate the handle, check the state
   edge and endpoint compatibility/retention, and mutate one record under the controller mutex. A rejected
   operation leaves every record and generation unchanged.
6. **Consume** — T015 reads the route declaration and handle to bind a provider; the declared policy is
   available for T015 capability matching without being strengthened.

## 6. Interfaces

T014 exposes an in-process C++20 API only (no transport, no external ABI).

| Interface | Contract |
| --- | --- |
| `EndpointSpec::create(EndpointSpecInput, const CommunicationContract&)` | `noexcept`; `Result<EndpointSpec>`; validates identity (1–128 bytes), 64-char lowercase-hex digest, provider identity, and a contract-declared direction. |
| `RouteSpec::create(RouteSpecInput, const EndpointSpec&, const EndpointSpec&)` | `noexcept`; `Result<RouteSpec>`; requires distinct compatible endpoints sharing plan, provider, contract, and source/target direction. |
| `RouteSpec::create(RouteSpecInput, const EndpointSpec&, const EndpointSpec&, const FlowPolicy&)` **(new)** | `noexcept`; as above plus exactly one owned declared policy; additively overloaded, the 3-argument form is unchanged. |
| `RouteSpec::has_policy()`, `RouteSpec::policy()` **(new)** | `noexcept`; const; reports and views the owned declared policy (`nullptr` when none); no mutation and no default substitution. |
| `LifecycleConfiguration::create(LifecycleConfigurationInput)` | `noexcept`; `Result<LifecycleConfiguration>`; finite nonzero capacities ≤ 32/32. |
| `LifecycleController::declare_endpoint/declare_route` | `noexcept`; `Result<Handle>`; exact generation-bound handle or stable declaration diagnostic. |
| `LifecycleController::endpoint_snapshot`/`route_snapshot` | `noexcept`; `Result<LifecycleSnapshot>`; exact handle authentication; route snapshot exposes `policy_bound()`. |
| `LifecycleController::endpoint_declaration`/`route_declaration` | `noexcept`; `Result<Spec>`; owned copy after exact handle authentication. |
| `LifecycleController::route_policy(const RouteHandle&)` **(new)** | `noexcept`; const; `Result<FlowPolicy>`; exact current route handle only; a generation with no declared policy fails with a stable diagnostic and no substitution. |
| `validate_/activate_/drain_/fail_/close_endpoint`, `validate_/activate_/drain_/fail_/close_route` | `noexcept`; `Result<LifecycleSnapshot>`; serialized, idempotent-or-rejected transitions with no mutation on rejection. |
| `EndpointHandle`/`RouteHandle` accessors | `noexcept`; const; opaque controller id, kind, identity, plan digest, nonzero generation; assignment deleted. |

## 7. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Fail-closed safety | every factory and controller operation returns a value or a non-empty diagnostic set; a rejected operation mutates nothing | T014-SR-001/002/006/014; NEG-01..NEG-18 |
| Explicit ownership | only the exact issued generation-bound handle authenticates a record; names and addresses never grant ownership | T014-SR-005/006/014; CHK-07 |
| Bounded resources | fixed compile-time arrays, configured capacity prefix, finite generations, at most one declared policy per route | T014-SR-016; CHK-06, CHK-09 |
| No silent upgrade | the declared policy is immutable on a generation; there is no rebind/upgrade operation; change requires a new generation | T014-SR-009; CHK-11 |
| Determinism | stable diagnostic codes, byte-stable ordering, unchanged snapshot before/after rejection | T014-SR-015; CHK-15 |
| Concurrency | one internal mutex serializes every operation; no callback under the lock; immutable values permit concurrent reads | T014-SR-017; CHK-17, NEG-17 |
| Domain neutrality | no provider, protocol, address, or domain primitive in a logical lifecycle value | T014-SR-001/002; CHK-10 |
| Offline safety | standard-library only; no network, ambient, filesystem, or process access | T014-SR-018; CHK-18 |
| Public safety | committed files carry no secret, private address, payload, or host path | T014-SR-019; CHK-19 |
| Documentation | every new/changed public declaration documents ownership/lifetime/thread-safety/failure | T014-SR-020; CHK-20 |
| Governance | no accepted artifact rewritten; registers re-validated; REF-002 unchanged | T014-SR-021; CHK-21, CHK-25 |

## 8. Consistency and constraints

- **Dependency direction preserved.** T014 depends only on T013 values and the standard library; no later
  slice is referenced and no runtime unit depends on a build file.
- **Domain neutrality preserved.** No vocabulary is added and no automotive or product primitive is
  introduced; the route binds the accepted `FlowPolicy` value unchanged.
- **XDL centrality preserved.** The declared policy originates from the accepted Profile/plan; T014 neither
  parses nor authors XDL and defines no competing configuration language.
- **Ownership preserved.** Only T014-owned lifecycle paths, the T014 work products, and the T014 checkbox
  change; no other task's path or test moves.
- **Maturity preserved.** The lifecycle stays a prototype control-plane library; provider matching,
  consolidated tests, executed sanitizer/static/Doxygen evidence, and acceptance remain with T015/T016,
  T035–T037, and T039/T041.
- **Non-breaking.** The declared-policy binding is additive: existing 3-argument `RouteSpec::create`
  callers, existing `LifecycleConfiguration::create({...})` callers, and every existing test compile and
  behave unchanged.

## 9. Traceability

| Architecture element | T014 requirements |
| --- | --- |
| `T14-XB-1`, `T14-CMP-DECL`, `T14-CMP-CONFIG` | T014-STK-002, T014-SR-001, T014-SR-002, T014-SR-003 |
| `T14-CMP-HANDLE`, `T14-XB-2` | T014-SR-004, T014-SR-005, T014-SR-006 |
| `T14-CMP-POLICY`, `T14-XB-3` | T014-STK-002, T014-SR-007, T014-SR-008, T014-SR-009, T014-SR-010 |
| `T14-CMP-CTRL`, `T14-CMP-SNAP` | T014-STK-003, T014-SR-011, T014-SR-012, T014-SR-013, T014-SR-014, T014-SR-017 |
| `T14-XB-4` | T014-SR-015, T014-SR-016 |
| `T14-XB-5`, `T14-WP` | T014-STK-004, T014-STK-005, T014-SR-018, T014-SR-019, T014-SR-020, T014-SR-021, T014-SR-022 |
