# T013 Requirements — Immutable Contract, Item, Origin, Time, Correlation, Diagnostic, and Policy Types

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T013 (capability 007, slice `T-CORE`) |
| Task title | Implement immutable contract, item, origin, time, correlation, diagnostic, and policy types |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `863f11ac990c1ce178a0f9d8eb2489e4a5243fe7` |
| Authorization | capability 007 accepted design and bounded implementation authorization (ACC002/ACC004/ACC005/ACC006/ACC007/ACC010/ACC011/ACC014/ACC015); ADR-0016; ADR-0018; ADR-0020 |
| Owning slice | `T-CORE` (T007 ownership register) |
| Predecessor | T012 (subtree CMake/CTest targets and warning-as-error rules; reviewed terminal package) |
| Producer dependency | T011 admitted offline build envelope (read-only inputs) |
| Successor tasks | T014 (endpoint/route lifecycle), T015 (provider composition + owned loopback), T016 (core unit/negative tests), then T017–T034, T035–T041 |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}`; `docs/engineering/xcom/t008/requirements-register.{json,md}`; `docs/engineering/xcom/t009/architecture-model.{json,md}`; `docs/engineering/xcom/t010/unit-design.{json,md}` |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production
change and does not implement, accept, or integrate the candidate. The T013 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T013 — Implement immutable contract, item, origin, time, correlation, diagnostic, and policy types.

### 1.1 Authority statement

This document specifies only the bounded T013 slice. It elaborates the accepted architecture
(`XCOM-CMP-004` "Core value, contract, and diagnostic types", responsible for the immutable,
domain-neutral contract, item, origin, time, correlation, diagnostic, **and policy** value types) and the
accepted software requirements `XCOM-SW-CORE-001`, `-002`, `-003`, `-004`, `-006`, and `-010`. It does
**not** redesign the accepted architecture, change a functional requirement, success criterion, ADR,
schema, or contract, fix a provider/route policy value, implement T014–T016 or any later task, add a new
admitted dependency, or accept or integrate any candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts,
the T007 ownership register, the T008 register, the T009 architecture model, the T010 unit design, the
constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is
reported rather than guessed. Unresolved gaps are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T013)

1. **Implement the immutable CORE value model** under `src/xverse/xcom/` in namespace `xverse::xcom`,
   realising `XCOM-DU-001` (value and payload view), `XCOM-DU-003` (item identity, origin, time,
   correlation), `XCOM-DU-004` (diagnostics and deterministic ordering), and `XCOM-DU-005` (result,
   outcome, and core-type aggregate), plus the contract/policy portion of `XCOM-DU-002`.
2. **Complete the missing immutable policy value types.** The baseline already provides the value,
   result, contract, item, origin, time, correlation, and diagnostic types, but the accepted
   `XCOM-CMP-004` responsibility requires **policy** value types and none exist. T013 adds the
   immutable, bounded `FlowPolicy` declaration value with `OrderingPolicy`, `ReliabilityPolicy`, and
   `OverflowPolicy` enumerations whose external text and value ranges are taken verbatim from the
   accepted `io.xverse.xcom` Profile `flow-policy` form
   (`xdl/profiles/xcom-v0.1.schema.json`); it invents no competing vocabulary or configuration language
   (Constitution III).
3. **Add the policy validation phase and stable policy diagnostic code** so a rejected policy produces
   the same stable, deterministically ordered diagnostics as every other core value.
4. **Add the focused T013 unit and negative cases** for the new policy value (positive vocabulary,
   boundary, immutability, and determinism cases; and one case per rejected field) inside the existing
   `tests/xcom/core_types/` executables. The consolidated cross-cutting matrix for interaction kinds,
   capabilities, ownership, lifecycle, queue bounds, and recovery remains T016.
5. **Re-verify every T013-owned core type unchanged**: the value, result, contract, item, and
   diagnostic sources are present at the baseline and are compiled, tested, and traced to the T013
   candidate revision without behavioural change or test weakening.
6. The T013 repository-owned work products and the T013 package record.

### 2.2 Explicit exclusions (must remain absent from the T013 candidate)

No endpoint/route lifecycle, provider composition, owned loopback provider, XDL/Profile/plan change,
observation, stimulation, journaling, time-authority, service-emulation lease, Protobuf/gRPC, gateway,
Argus/Maestro/Faults, compatibility, or legacy behaviour; no `xdl/`, `proto/`, or `src/xverse_xdl/`
change; no change to a `.cmake` file, the root `CMakeLists.txt`, or `src/xverse/xcom/CMakeLists.txt`
(the core-types target already compiles `contract.cpp`, so adding the policy implementation needs no
build-file change and therefore no inherited T020 trace-link hash refresh); no new admitted dependency;
no network access, TCP listener, filesystem access, process execution, or legacy repository/binary
access; no rewrite or weakening of an accepted ADR, requirement, contract, test, REF-002 disposition, or
another task's ownership path; no promotion of any REF-002 or capability requirement; no acceptance or
integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T013 |
| --- | --- | --- |
| Endpoint and route lifecycle with generation handles | T014 | allocated; T013 defines the immutable declaration value only, it does not bind, enqueue, or enforce it |
| Provider composition and owned loopback provider | T015 | allocated |
| Consolidated core unit/negative matrix (interaction kinds, capabilities, ownership, lifecycle, queue bounds, recovery) | T016 | allocated; T013 adds only focused cases for its own new policy value |
| Ordering-equivalence, malformed-plan, drift, bound, regression suites | T020 | complete (predecessor backlog) |
| Executed sanitizer/static-analysis/Doxygen evidence, benchmarks | T035–T037 | allocated |
| Integration, validation, static-analysis measures and delivery bundle | T035–T040 | allocated |
| Independent review and user acceptance | T039/T041 | allocated |

## 3. Stakeholder requirements (`T013-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T013-STK-001**: Before the X-COM core value model is accepted, the program **shall** have one
  repository-owned, bounded, domain-neutral C++20 immutable core type set — value, contract, item,
  origin, time, correlation, diagnostic, and policy — physically under `src/xverse/xcom/`, that
  compiles with the T011-admitted toolchain under the T012 warning-as-error contract.
- **T013-STK-002**: The core type set **shall** fail closed: no unvalidated or partial value is ever
  exposed, every resource is finite and explicit, no delivery or timing guarantee is silently
  strengthened, and no cross-clock comparison is inferred.
- **T013-STK-003**: Every core type **shall** make its ownership, lifetime, thread-safety, and failure
  contract explicit, and **shall** expose an immutable value semantic that is safe to copy and to read
  concurrently.
- **T013-STK-004**: The core type set **shall** be offline and domain-neutral: normal use performs no
  network discovery, ambient configuration or secret lookup, filesystem access, process execution, or
  legacy-repository access, and contains no domain-specific primitive.
- **T013-STK-005**: T013 **shall** preserve accepted intent: the delivered change is confined to the
  T013-owned core paths, the T013 work products, and the capability task ledger, and it **shall** neither
  weaken an accepted requirement or test nor implement another task.

## 4. Software/engineering requirements (`T013-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted
anchor. "Implemented" means the repository-owned source and its deterministic checks exist and pass; it
is not a runtime or production claim.

### 4.1 Immutable bounded value primitives

- **T013-SR-001 [ubiquitous]**: The core model **shall** provide bounded, value-owned `Identity`,
  `SemanticVersion`, `Payload`, and `Timestamp` primitives with fixed capacities, where every factory
  rejects invalid or over-bound input without allocation, exceptions, or a partial value.
  - Refines: `XCOM-SW-CORE-001`, `XCOM-SW-CORE-002`; anchors FR-003, FR-005; `XCOM-DU-001`.
  - Verification intent: positive and per-field boundary cases in `xcom_core_types_unit`/
    `xcom_core_types_negative`; CHK-03, CHK-05, CHK-09.
- **T013-SR-002 [ubiquitous]**: `CommunicationContract` **shall** be an immutable logical contract that
  validates bounded identity, semantic version, schema identity and version, one of the four declared
  interaction kinds, and its explicit compatible source/target directions, and **shall** keep logical
  identity independent of provider, protocol, address, and physical realization.
  - Refines: `XCOM-SW-CORE-001`, `XCOM-SW-CORE-002`; anchors FR-003, FR-004, FR-006; `XCOM-DU-002`.
  - Verification intent: the interaction/direction table and the contract field-boundary matrix;
    CHK-03, CHK-04, CHK-08.
- **T013-SR-003 [ubiquitous]**: `CommunicationItem` **shall** be an immutable bounded item that carries
  the contract version, logical interface and endpoint identity, schema identity and version, an explicit
  origin, a timestamp with an explicit clock domain, correlation and causation identity, and route and
  provider provenance, and **shall** reject any field that is empty, over-bound, of an unknown
  enumeration, or inconsistent with its communication contract.
  - Refines: `XCOM-SW-CORE-002`, `XCOM-SW-CORE-003`; anchors FR-005; `XCOM-DU-003`.
  - Verification intent: complete-item construction after source destruction plus the per-field item
    rejection matrix; CHK-03, CHK-04, CHK-09.

### 4.2 Immutable bounded policy types (new in T013)

- **T013-SR-004 [ubiquitous]**: The core model **shall** provide an immutable, bounded `FlowPolicy`
  declaration value composed of `OrderingPolicy` ∈ {`fifo`, `priority`, `unordered`},
  `ReliabilityPolicy` ∈ {`at-most-once`, `at-least-once`, `exactly-once`, `best-effort`},
  `OverflowPolicy` ∈ {`drop-oldest`, `drop-newest`, `coalesce`, `lossless-backpressure`, `reject`,
  `fail-closed`}, and a finite `deadline_ms` ∈ [0, 600000], `retry` ∈ [0, 64], and `queue_depth`
  ∈ [1, 65536].
  - Refines: `XCOM-SW-CORE-004`; anchors FR-007, FR-008; `XCOM-DU-002`/`XCOM-DU-005`;
    `docs/engineering/xcom/t010/requirements.md` "Overflow policy set".
  - Verification intent: the policy vocabulary/range table and its boundary matrix; CHK-06, CHK-09.
- **T013-SR-005 [unwanted behaviour]**: If any policy field has an unknown enumeration value or lies
  outside its declared range, `FlowPolicy::create` **shall** return a non-empty deterministic diagnostic
  set and **shall not** expose a partial or substituted value.
  - Refines: `XCOM-SW-CORE-004`, `XCOM-SW-CORE-003`; anchors FR-006, FR-007; `XCOM-DU-002`.
  - Verification intent: NEG-13 through NEG-17 and the exact policy diagnostic sequence; CHK-05, CHK-06.
- **T013-SR-006 [ubiquitous]**: The policy value **shall** preserve the declared ordering, reliability,
  overflow, deadline, retry, and queue depth exactly, **shall not** silently upgrade a delivery or timing
  guarantee, and **shall not** substitute a default for a missing or invalid declaration.
  - Refines: `XCOM-SW-CORE-004`; anchors FR-007, FR-008; `XCOM-DU-005`; Constitution IX.
  - Verification intent: the round-trip accessor and "no upgrade" cases; CHK-06, CHK-08.
- **T013-SR-007 [ubiquitous]**: The policy vocabulary and every numeric range **shall** equal the
  accepted `io.xverse.xcom` Profile `flow-policy` form; T013 **shall** neither add a value the accepted
  form rejects nor accept a value it rejects.
  - Refines: `XCOM-SW-CORE-004`; anchors FR-002, FR-031; Constitution III; `XCOM-XLC-005` (Profile input).
  - Verification intent: cross-read against `xdl/profiles/xcom-v0.1.schema.json`; CHK-06.

### 4.3 Diagnostics, result, and ordering

- **T013-SR-008 [ubiquitous]**: The diagnostic model **shall** use stable codes and carry severity,
  validation phase, affected identity, reason, and correction with a deterministic byte-stable ordering
  key; a `DiagnosticSet` **shall** be non-empty, bounded, and sorted independently of input order.
  - Refines: `XCOM-SW-CORE-006`, `XCOM-SW-CORE-010`; anchors FR-025; SC-002, SC-009; `XCOM-DU-004`.
  - Verification intent: the exact-diagnostic and reordered multi-error cases; CHK-07.
- **T013-SR-009 [ubiquitous]**: The diagnostic model **shall** include a `policy` validation phase and a
  stable policy diagnostic code whose external text is at most 14 bytes and whose addition changes no
  existing code, phase, ordering key, or bound.
  - Refines: `XCOM-SW-CORE-006`; anchors FR-025; `XCOM-DU-004`.
  - Verification intent: `to_string` table assertions and the exact policy diagnostic bytes; CHK-06,
  CHK-07, CHK-12.
- **T013-SR-010 [ubiquitous]**: `Result<T>` **shall** hold exactly one validated value or one non-empty
  immutable diagnostic set; validated construction **shall** be `noexcept` and allocation-free; copy
  construction **shall** leave the source valid and unchanged; assignment **shall** be unavailable so a
  returned accessor cannot be invalidated.
  - Refines: `XCOM-SW-CORE-003`; anchors FR-006, FR-025; `XCOM-DU-005`.
  - Verification intent: the rvalue-source-invariant and exclusivity cases; CHK-03, CHK-08, NEG-18.

### 4.4 Bounds, safety, and governance

- **T013-SR-011 [ubiquitous]**: Every core unit **shall** declare finite resource bounds and a declared
  overflow behaviour: identities ≤ 128 bytes, versions ≤ 32 bytes, payload ≤ 65,536 bytes, diagnostic
  texts ≤ 256 bytes, a diagnostic set ≤ 32 entries, and the policy ranges of T013-SR-004; no queue,
  quota, retry, or depth is unbounded.
  - Refines: `XCOM-SW-CORE-004`; anchors FR-007; `XCOM-DU-001`–`005`; T010 bounds vocabulary.
  - Verification intent: the boundary matrix; CHK-09.
- **T013-SR-012 [ubiquitous]**: The core model **shall** perform no cross-clock inference: an item
  carries one timestamp magnitude and one explicit clock-domain identity, and no API orders or compares
  values across clock domains.
  - Refines: `XCOM-SW-CORE-002`; anchors FR-005, FR-033; `XCOM-DU-003`; data-model invariant 9.
  - Verification intent: source inspection of `Timestamp`/`item.hpp`; CHK-04, NEG-19.
- **T013-SR-013 [ubiquitous]**: The core model **shall** perform no network, ambient, secret, filesystem,
  process, or legacy access, and **shall** add no admitted dependency beyond the C++ standard library.
  - Refines: `XCOM-SW-CORE-007` (domain-neutral local runtime half); anchors FR-026, FR-028; ADR-0018;
    Constitution IX.
  - Verification intent: the forbidden-API source scan plus the successful offline build; CHK-10, NEG-20,
    NEG-25.

### 4.5 Public safety, documentation, and process

- **T013-SR-014 [ubiquitous]**: Committed source, tests, and work products **shall** contain no
  credential, private address, unrestricted payload, proprietary source excerpt, environment-specific
  absolute host path, or sensitive deployment value.
  - Refines: Constitution X; anchors FR-027; `XCOM-SW-INTG` public-safe evidence rule.
  - Verification intent: the public-safety scan; CHK-11, NEG-23.
- **T013-SR-015 [ubiquitous]**: Every new or changed public C/C++ declaration **shall** carry useful
  Doxygen documentation including its ownership, lifetime, thread-safety, and failure contract, without
  weakening the admitted repository documentation configuration.
  - Refines: `XCOM-SW-CORE`; anchors FR-029; `XCOM-DU-022` Doxygen plan; Constitution X.
  - Verification intent: declaration inspection and the existing documentation validator; CHK-12;
    strict-declaration Doxygen remains `DOX-GAP-01`, owned by T011/T037.
- **T013-SR-016 [ubiquitous]**: The T013 candidate **shall** change no accepted requirement, ADR,
  contract, schema, another task's ownership path, or existing test, **shall** implement no later task,
  **shall** keep the REF-002 disposition `unchanged` with an empty `promoted` list, and **shall** record —
  without rewriting — the T008/T010 attribution anomaly described in §7.3.
  - Refines: ADR-0018, ADR-0020; T007 global prohibitions; anchors FR-030, FR-035; Constitution VII, IX.
  - Verification intent: `git diff --name-only <baseline> --` boundary inspection; the register
    validators; CHK-02, CHK-14, CHK-15, CHK-18.
- **T013-SR-017 [ubiquitous]**: The T013 candidate **shall** satisfy the deterministic Fabro gate for
  implementation tasks: the six named work products exist, at least one `src/xverse/xcom/**` path changes,
  `cmake` configure, build, test discovery, and the full `ctest` suite pass, and `git diff --check` is
  clean; the T013 checkbox is marked complete **only** in the implementation stage.
  - Refines: ADR-0020; anchors FR-030; Constitution X.
  - Verification intent: `xcom_feature_gate.py verify T013 <baseline>`; `git diff --check`; CHK-16, NEG-24.

## 5. Requirement-to-accepted-anchor traceability

| T013 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T013-STK-001 | `XCOM-SW-CORE-001/002` | XCOM-SYS-FR-003/004 | FR-003, FR-004 | IX, X |
| T013-STK-002 | `XCOM-SW-CORE-003/004` | XCOM-SYS-FR-006/007/008 | FR-006, FR-007, FR-008 | IX |
| T013-STK-003 | `XCOM-SW-CORE-001` | XCOM-SYS-FR-005 | FR-005 | IX |
| T013-STK-004 | `XCOM-SW-CORE-007` | XCOM-SYS-FR-026/028 | FR-026, FR-028 | II, VII |
| T013-STK-005 | Constitution VII/IX; ADR-0018/0020 | – | FR-030 | VII, IX, X |
| T013-SR-001 | `XCOM-SW-CORE-001/002` | XCOM-SYS-FR-005 | FR-003, FR-005 | IX, X |
| T013-SR-002 | `XCOM-SW-CORE-001/002` | XCOM-SYS-FR-003/004 | FR-003, FR-004, FR-006 | II, V |
| T013-SR-003 | `XCOM-SW-CORE-002/003` | XCOM-SYS-FR-005 | FR-005 | V, IX |
| T013-SR-004 | `XCOM-SW-CORE-004` | XCOM-SYS-FR-007/008 | FR-007, FR-008 | III, IX |
| T013-SR-005 | `XCOM-SW-CORE-003/004` | XCOM-SYS-FR-006/007 | FR-006, FR-007 | IX |
| T013-SR-006 | `XCOM-SW-CORE-004` | XCOM-SYS-FR-008 | FR-008 | IX |
| T013-SR-007 | `XCOM-SW-CORE-004` | XCOM-SYS-FR-002/031 | FR-002, FR-031 | III |
| T013-SR-008 | `XCOM-SW-CORE-006/010` | XCOM-SYS-FR-025 | FR-025 | SC-002, SC-009 |
| T013-SR-009 | `XCOM-SW-CORE-006` | XCOM-SYS-FR-025 | FR-025 | IX |
| T013-SR-010 | `XCOM-SW-CORE-003` | XCOM-SYS-FR-006 | FR-006, FR-025 | IX |
| T013-SR-011 | `XCOM-SW-CORE-004` | XCOM-SYS-FR-007 | FR-007 | IX |
| T013-SR-012 | `XCOM-SW-CORE-002` | XCOM-SYS-FR-005/033 | FR-005, FR-033 | I, V |
| T013-SR-013 | `XCOM-SW-CORE-007` | XCOM-SYS-FR-026/028 | FR-026, FR-028 | IX |
| T013-SR-014 | public-safe evidence rule | XCOM-SYS-FR-027 | FR-027 | X |
| T013-SR-015 | `XCOM-SW-CORE` Doxygen | XCOM-SYS-FR-029 | FR-029 | X |
| T013-SR-016 | Constitution; ADR-0018/0020 | XCOM-SYS-FR-035 | FR-030, FR-035 | VII, IX |
| T013-SR-017 | ADR-0020 | – | FR-030 | X |

`XCOM-SW-CORE-001`–`-010` are the accepted capability-007 software requirements
(`docs/engineering/xcom/t008/requirements-register.{json,md}`). They are accepted text; T013 refines and
consumes them and does not rewrite them. The system requirements and `SC-*` are the accepted
`specs/007-xcom-core/spec.md` statements.

## 6. REF-002 disposition

T013 owns no REF-002 SADS ID. It provides the immutable communication value types against which the
allocated REF-002 communication IDs (`XVE-SYS-0139`–`0158`) and their shared contributions are later
implemented and verified. T013 changes no required disposition: the capability `ref002.disposition`
stays `unchanged` with an empty `promoted` list (T013-SR-016). No allocated, deferred, or target SADS
requirement is reported as implemented, and no `XVE-SYS-*` ID is promoted.

## 7. Affected paths

### 7.1 Paths the T013 candidate changes

| Path | Change | Notes |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/contract.hpp` | edit | adds `OrderingPolicy`, `ReliabilityPolicy`, `OverflowPolicy`, `FlowPolicyInput`, and the immutable `FlowPolicy` declaration; no existing declaration is removed or changed |
| `src/xverse/xcom/src/contract.cpp` | edit | implements the three policy `to_string` mappings and `FlowPolicy::create` with fail-closed vocabulary/range validation |
| `src/xverse/xcom/include/xverse/xcom/diagnostic.hpp` | edit | adds `DiagnosticCode::invalid_policy` and `ValidationPhase::policy`; no existing code, phase, or bound changes |
| `src/xverse/xcom/src/diagnostic.cpp` | edit | extends `known_code`, `known_phase`, and the two `to_string` switches for the new policy code/phase |
| `tests/xcom/core_types/unit_tests.cpp` | edit | adds focused policy positive, boundary, immutability, and determinism cases (T013-owned) |
| `tests/xcom/core_types/negative_tests.cpp` | edit | adds focused policy rejection and exact-diagnostic cases (T013-owned) |
| `docs/engineering/xcom/t013/requirements.md` | add | this document |
| `docs/engineering/xcom/t013/architecture.md` | add | boundary, components, data flow, interfaces |
| `docs/engineering/xcom/t013/detailed-design.md` | add | rules, policy tables, failure semantics, Doxygen/design |
| `docs/engineering/xcom/t013/unit-specifications.md` | add | units, ownership/lifetime/thread-safety/bounds, traceability |
| `docs/engineering/xcom/t013/verification-plan.md` | add | named checks, negative cases, commands |
| `docs/engineering/xcom/t013/implementation.md` | add (implementation stage) | realized change and evidence |
| `docs/engineering/xcom/t013/internal-review.json` | add (review stage) | DeepSeek internal review |
| `specs/007-xcom-core/tasks.md` | edit T013 checkbox (implementation stage) | capability task ledger |
| `reports/xcom-queue/t013-package.json` | add (package stage) | exact-candidate package record |

### 7.2 T013-owned core paths consumed and re-verified unchanged

| Path | Owner | Role for T013 |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/value.hpp`, `src/xverse/xcom/src/value.cpp` | T-CORE (T013) | value/payload/timestamp primitives; re-verified unchanged |
| `src/xverse/xcom/include/xverse/xcom/item.hpp`, `src/xverse/xcom/src/item.cpp` | T-CORE (T013) | item origin/time/correlation identity; re-verified unchanged |
| `src/xverse/xcom/include/xverse/xcom/result.hpp`, `src/xverse/xcom/include/xverse/xcom/core_types.hpp` | T-CORE (T013) | result and public aggregate; re-verified unchanged |
| `tests/xcom/core_types/consumer/main.cpp` | T-CORE (T013) | external-consumer fixture; re-verified unchanged |

### 7.3 Consumed, read-only foundation (not changed by T013)

| Path | Owner | Role for T013 |
| --- | --- | --- |
| `src/xverse/xcom/CMakeLists.txt`, `cmake/*.cmake`, `CMakeLists.txt` | shared (serialized) | T012 subtree build contract that compiles the core-types target; T013 changes none |
| `xdl/profiles/xcom-v0.1.schema.json` | T-XDL (T017) | authoritative source of the `flow-policy` vocabulary and ranges; read-only |
| `docs/engineering/xcom/t008/*`, `t010/*` | T008/T010 | accepted register/unit design; the §7.4 attribution anomaly is recorded, not rewritten |
| `src/xverse/xcom/include/xverse/xcom/{endpoint_route_lifecycle,provider,loopback_provider,observation,validation_session,activation_plan}.hpp` | T014/T015/T019/T021/T025 | later/parallel slices; T013 neither depends on nor changes them |
| `engineering/**/*.json` | T020 (inherited) | T013 changes no linked path, so no inherited provenance hash refresh is required |

### 7.4 Recorded attribution anomaly (not resolved by T013)

The accepted `specs/007-xcom-core/tasks.md` and `docs/engineering/xcom/t009/architecture-model.json`
(`XCOM-CMP-004 → T013`) assign the core contract and diagnostic value types to T013, while
`docs/engineering/xcom/t008/requirements-register.json` attributes `XCOM-SW-CORE-001` and
`XCOM-SW-CORE-010` to T012 and `XCOM-SW-CORE-006` to T015, and `docs/engineering/xcom/t010/unit-design.json`
attributes `XCOM-DU-002` to T012. Both registers are owned by T008/T010 and remain
`partial`/`unreconciled` (analysis A12). T013 records this observation, implements the source as
`tasks.md`/`XCOM-CMP-004` direct, and rewrites nothing (T013-SR-016).

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- `T013-LIM-01` — The core model is a prototype value library: it makes no runtime, transport, timing,
  compatibility, or production-readiness claim, and it is not yet user-accepted (T041).
- `T013-LIM-02` — Strict declaration-level Doxygen (`WARN_IF_UNDOCUMENTED = YES`,
  `WARN_NO_PARAMDOC = YES`) remains open (`DOX-GAP-01`, `T011-GAP-01`), owned by T011/T037; T013
  documents every new/changed declaration but does not enable the strict configuration.
- `T013-LIM-03` — The policy value is a declaration/validation type; queueing, backpressure, deadline,
  and retry are neither enforced nor measured here, and no timing fidelity is claimed.
- `T013-LIM-04` — The large fixed payload capacity keeps item and successful-result objects
  correspondingly large; this is the bounded storage tradeoff inherited unchanged from the baseline.
- `T013-LIM-05` — `scripts/validate_xcom_core_types.py` is a legacy SESN-era validator in the T013-owned
  path set; the repository-owned workflow does not use it, and T013 neither depends on nor edits it.

### 8.2 Gaps with owning tasks

| Gap | Description | Owner | Disposition |
| --- | --- | --- | --- |
| `T013-GAP-01` | The T008/T010 attributions of `XCOM-SW-CORE-001`/`-006`/`-010` and `XCOM-DU-002` disagree with `tasks.md`/`XCOM-CMP-004` (§7.4). | T008/T010 (registers); T013 (source) | allocated; T013 records and promotes nothing |
| `T013-GAP-02` | Binding/enforcing the immutable policy on endpoints, routes, and provider capability matching is `XCOM-SW-CORE-004`'s runtime half. | T014/T015 | allocated; T013 defines the value only |
| `T013-GAP-03` | Consolidated core unit/negative coverage of interaction kinds, capabilities, ownership, lifecycle, queue bounds, and recovery. | T016 | allocated |
| `T013-GAP-04` | Candidate acceptance under capability 007 remains with T039/T041. | T039/T041 | allocated; T013 submits for review |

### 8.3 Open items

- `T013-OPEN-01` — Whether a later slice composes `FlowPolicy` into `CommunicationContract` or keeps it
  route-scoped is T014's decision; T013 declares the value and its validation only.
- `T013-OPEN-02` — If T014/T015 later split the core-types target or move the policy type to its own
  translation unit, the owning task updates the build contract and the inherited T020 trace links; T013
  changes no build file.

## 9. Definition of done (requirements view)

T013 is complete for this slice when: (a) the five plan-stage work products exist under
`docs/engineering/xcom/t013/` and are mutually consistent; (b) every requirement in §3–§4 has ≥ 1 named
check in `verification-plan.md`; (c) the implementation stage delivers the policy value types, the new
policy diagnostic code/phase, and the focused policy cases, marks the T013 checkbox, and records
`implementation.md`; (d) the deterministic gate and the named checks pass at the candidate revision;
(e) the package record is written; and (f) a separate DeepSeek internal review records a passing verdict
with no findings. This does **not** constitute user acceptance, which remains T041.

## 10. Requirement-to-check index (implemented in `verification-plan.md`)

| Requirement | Primary check(s) |
| --- | --- |
| T013-STK-001 | CHK-02, CHK-03, CHK-13 |
| T013-STK-002 | CHK-05, CHK-09, NEG-01..NEG-18 |
| T013-STK-003 | CHK-08, CHK-12 |
| T013-STK-004 | CHK-04, CHK-10 |
| T013-STK-005 | CHK-02, CHK-14, CHK-15, CHK-18 |
| T013-SR-001 | CHK-03, CHK-05, CHK-09 |
| T013-SR-002 | CHK-03, CHK-04, CHK-08 |
| T013-SR-003 | CHK-03, CHK-04, CHK-09 |
| T013-SR-004 | CHK-06, CHK-09 |
| T013-SR-005 | CHK-05, CHK-06, NEG-13..NEG-17 |
| T013-SR-006 | CHK-06, CHK-08 |
| T013-SR-007 | CHK-06 |
| T013-SR-008 | CHK-07, NEG-11, NEG-17 |
| T013-SR-009 | CHK-06, CHK-07, CHK-12 |
| T013-SR-010 | CHK-03, CHK-08, NEG-18 |
| T013-SR-011 | CHK-09 |
| T013-SR-012 | CHK-04, NEG-19 |
| T013-SR-013 | CHK-10, NEG-20, NEG-25 |
| T013-SR-014 | CHK-11, NEG-23 |
| T013-SR-015 | CHK-12 |
| T013-SR-016 | CHK-02, CHK-14, CHK-15, CHK-18 |
| T013-SR-017 | CHK-16, NEG-24 |
