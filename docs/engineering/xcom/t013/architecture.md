# T013 Architecture — Immutable Core Value, Contract, Item, Diagnostic, and Policy Boundary

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T013 (capability 007, slice `T-CORE`) |
| Stage / role | plan → architecture |
| Revision | 1 |
| Baseline revision | `863f11ac990c1ce178a0f9d8eb2489e4a5243fe7` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-004`, `XCOM-XLC-001`, `XCOM-XLC-004`, `XCOM-XLC-005`, `XCOM-XLC-006`); `docs/engineering/xcom/t011/architecture.md` (build envelope); `docs/engineering/xcom/t012/architecture.md` (subtree build/test contract) |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T013 is the **immutable data model** of the X-COM core. It occupies the seam between the T012 subtree
build/test contract and every behavioural core unit. It owns no route, endpoint, provider, observation,
stimulation, or gateway behaviour; it defines the bounded, domain-neutral values those units exchange and
the deterministic diagnostics they report.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract
   → T013 core value/contract/item/diagnostic/policy types (this document)
   → T014 lifecycle → T015 provider/loopback → T016 core tests
   → { T-XDL, T-OBS, T-STIM } → T-INTG (T035–T038) → T-REVIEW (T039/T041)
```

T013 is a **production-path** slice: the deterministic gate requires at least one changed
`src/xverse/xcom/**` path. The change is the missing immutable **policy** declaration value plus its
policy diagnostic phase/code; the existing value, contract, item, and diagnostic sources are re-verified
unchanged. No build file, XDL schema, contract, provider, or later-slice interface changes.

## 3. Boundary and context

### 3.1 System context

```text
        ┌─────────────── XDL / io.xverse.xcom Profile (read-only, T017) ───────────────┐
        │  xdl/profiles/xcom-v0.1.schema.json: flow-policy vocabulary + numeric ranges │
        └──────────────────────────────────┬───────────────────────────────────────────┘
                                           │ same vocabulary (no competing language)
   ┌──────────────────── T013 core value model (src/xverse/xcom, xverse::xcom) ─────────┐
   │  value.hpp     Identity · SemanticVersion · Payload · Timestamp                     │
   │  contract.hpp  InteractionKind · EndpointDirection · CommunicationContract          │
   │                OrderingPolicy · ReliabilityPolicy · OverflowPolicy · FlowPolicy     │
   │  item.hpp      OriginKind · CommunicationItem (origin/time/correlation/causation)   │
   │  diagnostic.hpp DiagnosticCode · DiagnosticSeverity · ValidationPhase · DiagnosticSet│
   │  result.hpp / core_types.hpp   Result<T> · public aggregate                         │
   └──────────────────────────────────┬───────────────────────────────────────────────────┘
                                      │ immutable values + deterministic diagnostics
   ┌──────────────────────────────────▼───────────────────────────────────────────────────┐
   │  consumers (read-only): T014 lifecycle, T015 provider/loopback, T016 tests,            │
   │  T019 plan model, T021 observation, T025 validation session                            │
   └───────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T13-XB-1` Raw input vs validated value | call-scoped `*Input` aggregates and factory calls | immutable published values | Every published value is complete and validated; a rejected input yields only a non-empty `DiagnosticSet`, never a partial value. |
| `T13-XB-2` Logical identity vs realization | logical contract/interface/endpoint/schema identity | provider, protocol, address, physical realization | Logical identity is validated and owned by T013; realization identity is item provenance only and defines no logical contract. |
| `T13-XB-3` Declared policy vs enforced provider capability | the immutable declared `FlowPolicy` | provider delivery/ordering capability and route enforcement (T014/T015) | T013 declares and validates only; matching and enforcement never strengthen the declared guarantee. |
| `T13-XB-4` Core vs later slices | `xverse::xcom` value types | lifecycle/provider/observation/stimulation/gateway units | Later slices depend on T013; T013 depends on no later slice and includes no provider/route/transport type. |
| `T13-XB-5` Repository vs environment | committed source, tests, work products | admitted build inputs, build trees, host paths | Committed files are public-safe and offline; no ambient, network, filesystem, or process access is introduced. |

### 3.3 Prohibited elements (must remain absent)

No TCP listener, external network peer, discovery, package manager/registry, filesystem access, process
execution, legacy repository/binary access, dynamic plugin discovery, domain-specific primitive (ECU,
CAN, SOME/IP, Zenodo, or product name), new admitted dependency, competing configuration language, or
unbounded resource. These inherit the T007 global prohibitions, the T011 envelope, the T012 build
contract, and the constitution.

## 4. Components

Each component maps to a unit in `unit-specifications.md`. `T13-CMP-*` names are local to this document;
the accepted `XCOM-DU-*` identifiers are the authorised design units.

### 4.1 Immutable value components

- **`T13-CMP-VALUE`** (`XCOM-DU-001`) — `value.hpp`/`value.cpp`: `Identity`, `SemanticVersion`,
  `Payload`, `Timestamp`, and the internal fixed-capacity text storage. Bounded, value-owned,
  exception-free factories.
- **`T13-CMP-CONTRACT`** (`XCOM-DU-002`) — `contract.hpp`/`contract.cpp`: `InteractionKind`,
  `EndpointDirection`, `CommunicationContract`, and **new** `OrderingPolicy`, `ReliabilityPolicy`,
  `OverflowPolicy`, `FlowPolicyInput`, `FlowPolicy`.
- **`T13-CMP-ITEM`** (`XCOM-DU-003`) — `item.hpp`/`item.cpp`: `OriginKind`, `CommunicationItemInput`,
  `CommunicationItem`, with origin, timestamp + clock domain, correlation, causation, route/provider
  provenance, and the bounded payload.
- **`T13-CMP-DIAG`** (`XCOM-DU-004`) — `diagnostic.hpp`/`diagnostic.cpp`: `DiagnosticCode`,
  `DiagnosticSeverity`, `ValidationPhase`, `Diagnostic`, `DiagnosticSet`, plus **new**
  `DiagnosticCode::invalid_policy` and `ValidationPhase::policy`.
- **`T13-CMP-RESULT`** (`XCOM-DU-005`) — `result.hpp`: the exclusive `Result<T>` success-or-diagnostics
  value.
- **`T13-CMP-AGG`** (`XCOM-DU-005`) — `core_types.hpp`: the public umbrella that exposes the whole
  immutable value model to consumers.

### 4.2 Work-product components

- **`T13-WP`** — the T013 repository-owned work-product set (`requirements.md`, `architecture.md`,
  `detailed-design.md`, `unit-specifications.md`, `verification-plan.md`, `implementation.md`,
  `internal-review.json`, and `reports/xcom-queue/t013-package.json`).

### 4.3 Consumed components (read-only)

`XCOM-CMP-002` X-COM Profile/schema, `XCOM-CMP-005` lifecycle, `XCOM-CMP-006` provider, `XCOM-CMP-007`
owned loopback, `XCOM-CMP-008` observation, `XCOM-CMP-009` validation session, and the XDL Profile
schema are consumed or matched but neither implemented nor altered by T013.

## 5. Data flow (ordered)

1. **Construct input** — a consumer builds a call-scoped `CommunicationContractInput`,
   `CommunicationItemInput`, `FlowPolicyInput`, or `DiagnosticInput` that borrows caller-owned views.
2. **Validate** — the factory validates bounded lexical form, semantic version, interaction/direction
   compatibility, item/contract consistency, policy vocabulary and range, and enumerations, accumulating
   deterministic diagnostics in call-local storage.
3. **Reject or publish** — on any violation the factory returns `Result<T>::failure` with a non-empty,
   sorted `DiagnosticSet` and exposes no value; otherwise it copies every field into fixed-capacity,
   value-owned storage and returns `Result<T>::success`.
4. **Consume** — later slices read immutable accessors; the caller keeps the value alive for the accessor
   and span lifetime. `FlowPolicy` is read as a declaration by T014/T015, which match it to provider
   capability without strengthening it.

## 6. Interfaces

T013 exposes an in-process C++20 API only (no transport, no external ABI).

| Interface | Contract |
| --- | --- |
| `Identity::create`, `SemanticVersion::create`, `Payload::create` | `noexcept`; return `std::optional` empty on invalid/over-bound input; 1–128 bytes identity, 1–32 bytes version, 0–65,536 bytes payload. |
| `CommunicationContract::create(CommunicationContractInput)` | `noexcept`; `Result<CommunicationContract>`; validates identity/version/schema/kind/direction compatibility. |
| `CommunicationItem::create(CommunicationItemInput, const CommunicationContract&)` | `noexcept`; `Result<CommunicationItem>`; validates every required field, the origin enumeration, the payload bound, and contract consistency. |
| `FlowPolicy::create(FlowPolicyInput)` | `noexcept`; `Result<FlowPolicy>`; validates the three policy enumerations and the `deadline_ms`/`retry`/`queue_depth` ranges; preserves the declaration exactly. |
| `Diagnostic::create(DiagnosticInput)`, `DiagnosticSet::create`, `DiagnosticSet::create_from_inputs` | `noexcept`; bounded, non-empty, deterministically sorted diagnostics. |
| `to_string(InteractionKind/EndpointDirection/OriginKind/OrderingPolicy/ReliabilityPolicy/OverflowPolicy/DiagnosticCode/DiagnosticSeverity/ValidationPhase)` | static-lifetime stable external text. |
| `Result<T>::success/failure/value/diagnostics` | exclusive success or non-empty failure; no assignment. |

## 7. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Fail-closed safety | every factory returns a value or a non-empty diagnostic set; no partial value | T013-SR-005/010; NEG-01..NEG-18 |
| Immutability | const accessors only; assignment disabled; bounded values copied on hand-off | T013-STK-003, T013-SR-010; CHK-08 |
| Determinism | stable diagnostic codes and a byte-stable ordering key independent of input order | T013-SR-008/009; CHK-07 |
| Bounded resources | finite identity/version/payload/text/set capacities and finite policy ranges | T013-SR-011; CHK-09 |
| Domain neutrality | no provider, protocol, address, or domain primitive in a logical value | T013-SR-002; CHK-04 |
| Offline safety | standard-library only; no network, ambient, filesystem, or process access | T013-SR-013; CHK-10 |
| Public safety | committed files carry no secret, private address, payload, or host path | T013-SR-014; CHK-11 |
| Documentation | every new/changed public declaration documents ownership/lifetime/thread-safety/failure | T013-SR-015; CHK-12 |
| Governance | no accepted artifact rewritten; registers re-validated; REF-002 unchanged | T013-SR-016; CHK-14, CHK-18 |

## 8. Consistency and constraints

- **Dependency direction preserved.** T013 is a leaf: no later slice is referenced, and no runtime unit
  depends on a build file.
- **Domain neutrality preserved.** The only vocabulary added is the accepted X-COM Profile `flow-policy`
  vocabulary; no automotive or product primitive is introduced.
- **XDL centrality preserved.** Policy values mirror the accepted Profile vocabulary; T013 neither parses
  nor authors XDL and defines no competing configuration language.
- **Ownership preserved.** Only T013-owned paths, the T013 work products, and the T013 checkbox change;
  no task moves to a different revision.
- **Maturity preserved.** The core model stays a prototype value library; enforcement, integration,
  executed sanitizer/static/Doxygen evidence, and acceptance remain with T014–T016, T035–T037, and
  T039/T041.
- **Later tasks preserved.** T014–T016 keep their lifecycle, provider, and consolidated-test ownership;
  T013 adds only its own policy value and focused policy cases.

## 9. Traceability

| Architecture element | T013 requirements |
| --- | --- |
| `T13-XB-1`, `T13-CMP-VALUE` | T013-STK-001, T013-SR-001, T013-SR-010, T013-SR-011 |
| `T13-XB-2`, `T13-CMP-CONTRACT` | T013-SR-002, T013-SR-003 |
| `T13-XB-3`, `T13-CMP-CONTRACT` (policy) | T013-SR-004, T013-SR-005, T013-SR-006, T013-SR-007 |
| `T13-CMP-ITEM` | T013-SR-003, T013-SR-012 |
| `T13-XB-4`, `T13-CMP-DIAG` | T013-SR-008, T013-SR-009 |
| `T13-XB-5`, `T13-WP` | T013-STK-004, T013-STK-005, T013-SR-013, T013-SR-014, T013-SR-016, T013-SR-017 |
| `T13-CMP-RESULT`, `T13-CMP-AGG` | T013-STK-003, T013-SR-010, T013-SR-015 |
