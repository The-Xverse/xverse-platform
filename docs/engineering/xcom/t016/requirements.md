# T016 Requirements — Consolidated X-COM Core Unit and Negative Test Matrix

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T016 (capability 007, slice `T-CORE`) |
| Task title | Add unit and negative tests for interaction kinds, capabilities, policy, ownership, lifecycle, queue bounds, deterministic diagnostics, and recovery |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `44d2001d48dd42dc9ed489a40d2a5f908b734501` |
| Authorization | capability 007 accepted design and bounded implementation authorization (ACC002/ACC004/ACC005/ACC006/ACC007/ACC010/ACC011/ACC014/ACC015); ADR-0016; ADR-0018; ADR-0020 |
| Owning slice | `T-CORE` (T007 ownership register) |
| Predecessor | T015 (explicit provider composition and owned loopback provider; reviewed terminal package) |
| Producer dependencies | T011 admitted offline build envelope (read-only inputs); T012 subtree CMake/CTest contract; T013 immutable core value/contract/item/diagnostic/policy types; T014 endpoint/route lifecycle, exact generation-bound handles, and declared-policy binding; T015 provider composition, `unsupported_policy` outcome, and loopback provider |
| Successor tasks | T021–T024 (observation), T025–T029 (stimulation), T030–T034 (gateway/conformance), T035–T041 (evidence/review/acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}`; `docs/engineering/xcom/t008/requirements-register.{json,md}`; `docs/engineering/xcom/t008/traceability-matrix.{json,md}`; `docs/engineering/xcom/t009/architecture-model.{json,md}`; `docs/engineering/xcom/t010/unit-design.{json,md}` |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production
or test change and does not implement, accept, or integrate the candidate. The T016 task entry in
`specs/007-xcom-core/tasks.md` is the authorized scope:

> T016 — Add unit and negative tests for interaction kinds, capabilities, policy, ownership, lifecycle,
> queue bounds, deterministic diagnostics, and recovery.

### 1.1 Authority statement

This document specifies only the bounded T016 slice. It elaborates the accepted verification
obligations carried by the accepted software requirements `XCOM-SW-CORE-009` "Loopback conformance and
negative-case suite" (refines `XCOM-SYS-SC-001`, spec `SC-001`) and `XCOM-SW-CORE-008` "Controlled
fault-hook boundary" (refines `XCOM-SYS-FR-024`, spec `FR-024`), which
`docs/engineering/xcom/t008/requirements-register.{json,md}` attributes to T016, and it consolidates the
cross-cutting verification that T013 (`T013-GAP-03`), T014 (`T014-GAP-03`), and T015 (`T015-GAP-02`)
explicitly allocated to the "consolidated core unit/negative matrix". It verifies — read-only — the
accepted behaviours of `XCOM-SW-CORE-001…-007` and `XCOM-SW-CORE-010` at the exact T016 baseline. It
does **not** redesign the accepted architecture, change a functional requirement, success criterion,
ADR, schema, or contract, fix an interaction/capability/policy/ownership/lifecycle/queue/diagnostic
value, implement T013–T015 or T017–T041, add a new admitted dependency, or accept or integrate any
candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, the
T007 ownership register, the T008 register/matrix, the T009 architecture model, the T010 unit design,
the constitution, or an accepted ADR is resolved in favour of the accepted source. A material gap is
reported rather than guessed. Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T016)

1. **Consolidated core test matrix (tests only).** Add one new repository-owned consolidated core test
   area under `tests/xcom/core_matrix/` that exercises the accepted core end to end across
   `xverse::xcom`'s public surface — contract → item → endpoint/route lifecycle → provider composition →
   owned loopback → bounded queue → receive → deterministic diagnostics — and that covers, in one
   auditable matrix, the eight areas named by the T016 task entry: **interaction kinds, capabilities,
   policy, ownership, lifecycle, queue bounds, deterministic diagnostics, and recovery**.
2. **SC-001 proof.** Prove the accepted `SC-001` / `XCOM-SW-CORE-009` outcome: the owned loopback
   exchanges all four interaction families, and at least twenty malformed, incompatible, over-capacity,
   or unauthorized cases are rejected fail-closed with stable diagnostics. Each negative case is an
   individually named, individually reportable test.
3. **CORE-008 boundary proof.** Verify the `XCOM-SW-CORE-008` / `FR-024` controlled fault-hook boundary
   at the T016-owned core surface: the core embeds no domain-specific fault semantics, exposes only
   bounded controlled seams, and offers no uncontrolled mutation/injection entry point. The concrete
   bounded communication hook used by the Faults subsystem is the observation tap boundary owned by
   T021–T024 (`FR-011…FR-013`, clarification C11, ACC009); T016 verifies the core-side constraint and
   does not implement that hook.
4. **Cross-cutting regressions identified by predecessors.** Add the additive strengthening cases the
   T014 and T015 internal reviews recorded: a same-identity route pair that differs **only** by declared
   `FlowPolicy` must compare unequal (T014 review note), and a positive `at_least_once → reliable`
   declared-policy mapping must prepare and activate against a provider that advertises the `reliable`
   bit (T015 review note). Neither weakens or replaces an existing case.
5. **Additive target registration.** Register the new test executables additively in the shared,
   serialized T012 subtree build contract (`src/xverse/xcom/CMakeLists.txt`) without renaming,
   relabelling, reordering, or removing any existing target, test name, label, command, or expected
   result.
6. **Additivity and boundary preservation.** Re-verify that no production source, existing test case,
   accepted requirement, ADR, contract, schema, register, or another task's path is changed, and that
   the T016 candidate implements no later task.
7. The T016 repository-owned work products and the T016 package record.

### 2.2 Explicit exclusions (must remain absent from the T016 candidate)

No production source change under `src/xverse/xcom/` other than the additive, serialized test-target
registration in `src/xverse/xcom/CMakeLists.txt`; no change to any `*.hpp` or `*.cpp` unit, to
`cmake/*.cmake`, the root `CMakeLists.txt`, or any other build file; no change to `xdl/`, `proto/`,
`src/xverse_xdl/`, or `tests/xcom/{core_types,endpoint_route_lifecycle,provider_loopback,observation,activation_plan,validation_session}`
sources (the existing suites are re-run unchanged, never weakened, renamed, or removed); no observation
record/tap, stimulation, journaling, time-authority, service-emulation, Protobuf/gRPC, gateway,
Argus/Maestro/Faults, compatibility, or legacy behaviour; no new admitted dependency; no network
access, TCP listener, DNS, TLS, filesystem access, process execution, dynamic provider discovery or
loading, ambient/secret lookup, or legacy repository/binary access; no rewrite or weakening of an
accepted ADR, requirement, contract, test, REF-002 disposition, or another task's ownership path; no
promotion of any REF-002 or capability requirement; no acceptance or integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T016 |
| --- | --- | --- |
| Immutable value/contract/item/policy/diagnostic types, `FlowPolicy`, `DiagnosticCode`/`ValidationPhase`, deterministic ordering guarantee | T013/T012 | complete (predecessor); verified read-only |
| Endpoint/route lifecycle, exact generation-bound handles, declared-policy binding and `route_policy` read | T014 | complete (predecessor); verified read-only |
| Provider composition, `unsupported_policy` outcome, owned loopback provider | T015 | complete (predecessor); verified read-only |
| Concrete bounded communication hook (observation tap) usable by Faults | T021–T024 | allocated; T016 verifies the core-side CORE-008 constraint only |
| XDL Profile/activation-plan compilation and decoding | T017–T020 | complete (predecessor backlog); consumed read-only |
| Validation stimulation boundary/journal | T025–T029 | allocated; T016 exercises no stimulation path |
| Second synthetic provider + version-rejection contract suite; tool-gateway conformance | T032–T034 | allocated |
| Executed sanitizer/static-analysis/Doxygen evidence, benchmarks | T035–T037 | allocated |
| Integration, validation, delivery bundle | T035–T040 | allocated |
| Independent/external review and user acceptance | T039/T041 | allocated |

## 3. Stakeholder requirements (`T016-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T016-STK-001**: Before the X-COM core is accepted, the program **shall** have one repository-owned,
  bounded, domain-neutral consolidated core test matrix, physically under `tests/xcom/core_matrix/`
  with its additive registration in the shared subtree build contract, that exercises all four accepted
  interaction families and the eight named core areas offline under the T011-admitted toolchain and the
  T012 warning-as-error contract.
- **T016-STK-002**: The matrix **shall** prove the accepted success criterion `SC-001`: the owned
  loopback exchanges all four interaction families, and at least twenty malformed, incompatible,
  over-capacity, or unauthorized cases are rejected fail-closed with stable, exact diagnostics, with no
  rejected operation mutating any registry, provider, route, queue, or lifecycle record.
- **T016-STK-003**: The matrix **shall** prove the accepted ownership, lifetime, thread-safety,
  determinism, and bound contracts of the core: immutable values, handles, and snapshots are safe to
  copy and to read concurrently; every capacity and limit is finite and explicit; and every resource
  the matrix itself uses (threads, items, iterations) is finite and declared.
- **T016-STK-004**: The matrix **shall** prove the accepted `FR-024` boundary: the T016-owned core
  surface embeds no domain-specific fault semantics and exposes only controlled, bounded seams, with no
  uncontrolled mutation or injection entry point.
- **T016-STK-005**: T016 **shall** preserve accepted intent: the delivered change is confined to the
  T016-owned test area, the additive build registration, the T016 work products, and the capability
  task ledger, and it **shall** neither weaken an accepted requirement or test nor implement another
  task.

## 4. Software/engineering requirements (`T016-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an
accepted anchor. "Verified" means the repository-owned test exists, is deterministic, and passes at the
recorded candidate revision; it is not a runtime, transport, timing, or production claim.

### 4.1 Consolidated harness and registration

- **T016-SR-001 [ubiquitous]**: The consolidated matrix **shall** be implemented as new executables
  under `tests/xcom/core_matrix/` with a self-contained `test_support.hpp` fixture that builds the whole
  accepted core stack independently through public headers only, **shall** not include or depend on any
  other task's `tests/xcom/*/test_support.hpp` or fixture, and **shall** be registered additively in the
  shared serialized `src/xverse/xcom/CMakeLists.txt` under a distinct `t016` label without changing any
  existing target, test name, label, command, or expected result.
  - Refines: `XCOM-SW-CORE-009`; anchors `SC-001`; T012 subtree build contract; T007 shared-path rule.
  - Verification intent: harness/target inventory; CHK-04, CHK-19, NEG-30.
- **T016-SR-002 [ubiquitous]**: The matrix **shall** exchange each of the four accepted interaction
  families (`signal_state_update`, `message_event`, `service_request`, `service_response`) end to end
  over the owned loopback — contract validation, compatible endpoint directions, route
  declare/validate/activate, provider prepare/activate, submit, receive, and close — preserving the
  exact item contract, kind, endpoints, schema, origin, timestamp/clock domain, correlation/causation,
  route, and provider binding, and returning the payload bytes unchanged.
  - Refines: `XCOM-SW-CORE-002`, `XCOM-SW-CORE-009`; anchors FR-004, FR-005; `XCOM-SYS-SC-001`; SC-001.
  - Verification intent: four-family nominal matrix; CHK-03, CHK-05, NEG-01, NEG-02, NEG-03.

### 4.2 Capabilities and policy

- **T016-SR-003 [ubiquitous]**: The matrix **shall** verify the accepted capability vocabulary and
  masks: the stable interaction/delivery/ordering mask bits, the descriptor's nonzero-mask validation,
  the exact advertised-claim containment in `prepare_route`, and a positive `at_least_once → reliable`
  declared-policy mapping that prepares and activates when the selected provider advertises the
  `reliable` bit (the additive case recorded by the T015 review).
  - Refines: `XCOM-SW-CORE-004`, `XCOM-SW-CORE-009`; anchors FR-006, FR-007, FR-008;
    `XCOM-DU-007`; T015 review note.
  - Verification intent: capability/bit matrix and positive reliable mapping; CHK-06, NEG-06, NEG-07,
    NEG-08, NEG-09, NEG-14, NEG-16.
- **T016-SR-004 [ubiquitous]**: The matrix **shall** verify declared-`FlowPolicy` binding and
  preparation-time matching: a supported declared claim (`best_effort`/`fifo`, `at_least_once`,
  `reject`, `deadline_ms == 0`, `retry == 0`) prepares when the request matches exactly; an unbound
  three-argument `RouteSpec` route is unaffected (additivity); and two routes with the **same** logical
  identity/composition that differ **only** in declared `FlowPolicy` compare unequal (the additive case
  recorded by the T014 review).
  - Refines: `XCOM-SW-CORE-003`, `XCOM-SW-CORE-004`; anchors FR-006, FR-007, FR-008; `XCOM-DU-007`;
    T014 review note.
  - Verification intent: declared-policy matching/unbound additivity/equality matrix; CHK-07, CHK-08,
    NEG-05, NEG-10, NEG-11, NEG-12, NEG-13.

### 4.3 Ownership and lifecycle

- **T016-SR-005 [ubiquitous]**: The matrix **shall** verify exact generation-bound ownership: issued
  `EndpointHandle`, `RouteHandle`, `ProviderRouteHandle`, registration, and provider-route tokens are
  copyable and concurrently readable; an inauthentic, stale, foreign, wrong-composition,
  wrong-registration, or wrong-state handle rejects with the stable outcome and mutates no record.
  - Refines: `XCOM-SW-CORE-005`; anchors FR-009, FR-010; `XCOM-DU-007`.
  - Verification intent: ownership/authenticity matrix; CHK-09, NEG-21, NEG-22, NEG-24.
- **T016-SR-006 [ubiquitous]**: The matrix **shall** verify lifecycle semantics: the endpoint and route
  state transitions accepted by the lifecycle controller (declare → validate → activate → drain → close,
  idempotence, and stale-generation rejection), and the provider route lifecycle
  `prepared → active → draining → closed`, including drain that stops new submissions while retaining
  queued items, and close that rejects a non-empty route (`queued_items_remain`) and releases only an
  empty drained route.
  - Refines: `XCOM-SW-CORE-005`, `XCOM-SW-CORE-004`; anchors FR-008, FR-009, FR-010; `XCOM-DU-007`,
    `XCOM-DU-008`.
  - Verification intent: lifecycle transition and drain/close matrix; CHK-10, CHK-11, NEG-18, NEG-20.

### 4.4 Queue bounds and deterministic diagnostics

- **T016-SR-007 [ubiquitous]**: The matrix **shall** verify finite, explicit queue and payload bounds:
  the loopback route bound (`kMaximumRoutes = 4`) and per-route queue bound (`kMaximumQueueItems = 8`),
  the provider registry bound (`kMaximumProviders = 8`), the descriptor hard limits (payload ≤ 65,536
  bytes, routes ≤ 32, queue items ≤ 32), and the reject-new behaviour that preserves every queued item
  and FIFO index on saturation, with a submit over the prepared payload bound rejected before mutation.
  - Refines: `XCOM-SW-CORE-004`, `XCOM-SW-CORE-007`; anchors FR-007, FR-028; `XCOM-DU-007`,
    `XCOM-DU-008`; T010 bounds vocabulary.
  - Verification intent: bound matrix and exhaustion cases; CHK-12, CHK-18, NEG-04, NEG-15, NEG-17,
    NEG-18, NEG-19.
- **T016-SR-008 [ubiquitous]**: The matrix **shall** verify deterministic diagnostics: the exact
  severity/phase/code/affected-identity/reason/correction content and the byte-stable serialization and
  ordering of multi-diagnostic sets, including the guarantee that equivalent normalized inputs produce
  byte-identical diagnostic ordering regardless of construction order, and that diagnostics are
  locale-independent; the provider outcome → text/code/message mapping **shall** be verified exact,
  including the T015 `unsupported_policy` (`XCOM-PROV-E030`) row.
  - Refines: `XCOM-SW-CORE-006`, `XCOM-SW-CORE-010`; anchors FR-025; SC-001; `XCOM-DU-007`,
    `XCOM-DU-008`.
  - Verification intent: exact-diagnostic and ordering matrix; CHK-13, NEG-05, NEG-11.
- **T016-SR-009 [ubiquitous]**: The matrix **shall** verify recovery: after saturation, subsequent
  receive drains accepted items in FIFO order and the route accepts new submissions again without loss,
  duplication, or reordering; a rejected operation leaves the registry, provider, route, queue, and
  lifecycle records unchanged and reusable; a closed route recreated as a new generation rejects the
  earlier generation's handles; and an unreconcilable provider/lifecycle state reports
  `interrupted_resource`, never success.
  - Refines: `XCOM-SW-CORE-005`, `XCOM-SW-CORE-009`; anchors FR-008, FR-009, FR-010; SC-001;
    `XCOM-DU-007`, `XCOM-DU-008`.
  - Verification intent: recovery/recreation/reconcile matrix; CHK-14, NEG-20, NEG-21, NEG-25.
- **T016-SR-010 [ubiquitous]**: The matrix **shall** verify deterministic concurrency with a declared,
  finite thread and iteration budget: concurrent submit/receive over one active loopback route delivers
  each accepted item exactly once with per-route FIFO order, no callback runs under a registry or
  provider lock, and repeated runs produce the same observable outcome.
  - Refines: `XCOM-SW-CORE-005`, `XCOM-SW-CORE-007`; anchors FR-010; `XCOM-DU-007`, `XCOM-DU-008`.
  - Verification intent: bounded concurrency matrix; CHK-15, NEG-18, NEG-22.

### 4.5 Fault-hook boundary and negative matrix

- **T016-SR-011 [ubiquitous]**: The consolidated negative matrix **shall** contain at least twenty
  individually named executable rejection cases spanning malformed input, incompatible capability,
  over-capacity, and unauthorized/ownership classes, with at least one named case in each of the four
  interaction families, each asserting a stable exact diagnostic and that no registry, provider, route,
  queue, or lifecycle record is mutated by the rejection.
  - Refines: `XCOM-SW-CORE-009`; anchors FR-006, FR-007, FR-008, FR-009, FR-025; `XCOM-SYS-SC-001`;
    SC-001.
  - Verification intent: consolidated negative matrix count and coverage; CHK-16, NEG-01…NEG-27.
- **T016-SR-012 [ubiquitous]**: The matrix **shall** verify the `XCOM-SW-CORE-008` / `FR-024` boundary at
  the T016-owned core surface: no public core type, factory, or operation injects or models a
  domain-specific fault campaign, taxonomy, or mutation policy; the only extension seams available are
  the controlled, bounded observation/provider seams owned by other tasks; and no uncontrolled
  injection/mutation entry point exists.
  - Refines: `XCOM-SW-CORE-008`; anchors FR-024; `XCOM-DU-007`; clarification C11; ACC009.
  - Verification intent: fault-hook boundary matrix plus forbidden-vocabulary scan; CHK-17, NEG-28.

### 4.6 Bounds, neutrality, safety, and governance

- **T016-SR-013 [ubiquitous]**: The matrix **shall** declare and stay within finite resource bounds:
  bounded thread count, bounded item count, bounded iteration count, and bounded payload sizes; no test
  performs an unbounded loop, unbounded allocation, unbounded wait, or unbounded retry, and no test
  depends on wall-clock timing for its verdict.
  - Refines: `XCOM-SW-CORE-004`, `XCOM-SW-CORE-007`; anchors FR-007; T010 bounds vocabulary.
  - Verification intent: matrix self-bound inspection and deterministic runs; CHK-18, NEG-15, NEG-22.
- **T016-SR-014 [ubiquitous]**: The T016 candidate **shall** be additive: it **shall** not remove,
  rename, weaken, retarget, or reorder any existing test case, target, label, command, threshold, or
  expected result in `core_types`, `endpoint_route_lifecycle`, `provider_loopback`, `observation`,
  `activation_plan`, or `validation_session`, and **shall** not change any production unit.
  - Refines: Constitution VII, IX; ADR-0020; T007 global prohibitions.
  - Verification intent: `git diff --name-only <baseline> --`; existing-suite source inspection;
    CHK-19, NEG-30.
- **T016-SR-015 [ubiquitous]**: The matrix **shall** be offline and domain-neutral: it **shall** use
  only the C++ standard library plus the already admitted GTest and thread test dependencies, with no
  network, socket, resolver, TLS, ambient, secret, filesystem, process, dynamic-load, or legacy access,
  and with no domain-specific primitive.
  - Refines: `XCOM-SW-CORE-007` (domain-neutral local runtime half); anchors FR-001, FR-026, FR-028;
    ADR-0018; Constitution II, VII.
  - Verification intent: forbidden-API source scan plus the successful offline build; CHK-20, NEG-28.
- **T016-SR-016 [ubiquitous]**: Committed test source and work products **shall** contain no credential,
  private address, unrestricted payload, proprietary source excerpt, environment-specific absolute host
  path, or sensitive deployment value; payload bytes used by fixtures **shall** be bounded, synthetic,
  and non-sensitive.
  - Refines: Constitution X; anchors FR-027; `XCOM-SW-INTG` public-safe evidence rule.
  - Verification intent: public-safety scan; CHK-21, NEG-29.
- **T016-SR-017 [ubiquitous]**: Every new test file and helper declaration **shall** carry useful
  Doxygen documentation including its ownership, lifetime, thread-safety, and failure contract, without
  changing the admitted repository documentation configuration.
  - Refines: `XCOM-SW-CORE` Doxygen; anchors FR-029; `XCOM-DU-007`/`XCOM-DU-008` Doxygen plan;
    Constitution X.
  - Verification intent: source inspection and the existing documentation validator; CHK-22; strict
    declaration Doxygen remains `DOX-GAP-01`, owned by T011/T037.
- **T016-SR-018 [ubiquitous]**: The T016 candidate **shall** change no accepted requirement, ADR,
  contract, schema, register, or another task's ownership path, **shall** implement no later task,
  **shall** keep the REF-002 disposition `unchanged` with an empty `promoted` list, and **shall** record
  the §7.4 attribution observation without rewriting it.
  - Refines: ADR-0018, ADR-0020; T007 global prohibitions; anchors FR-030, FR-035; Constitution VII, IX.
  - Verification intent: changed-path inspection; register validators; CHK-23, NEG-30.
- **T016-SR-019 [ubiquitous]**: The T016 candidate **shall** satisfy the deterministic Fabro gate for a
  test task: the five plan-stage work products and the implementation record exist, at least one
  `tests/` path changes, `cmake` configure, build, test discovery, and the full `ctest` suite pass, and
  `git diff --check` is clean; the T016 checkbox is marked complete **only** in the implementation
  stage.
  - Refines: ADR-0020; anchors FR-030; Constitution X.
  - Verification intent: `xcom_feature_gate.py verify T016 <baseline>`; `git diff --check`; CHK-24,
    NEG-30.
- **T016-SR-020 [ubiquitous]**: Every T016 requirement in §3–§4 **shall** map to at least one named
  check in `verification-plan.md`, and every named check **shall** trace back to a T016 requirement and
  an accepted anchor, including `XCOM-SW-CORE-008`/`XCOM-SW-CORE-009` and the predecessor gap records
  `T013-GAP-03`/`T014-GAP-03`/`T015-GAP-02`.
  - Refines: ADR-0020; anchors FR-030; `XCOM-L-0046`, `XCOM-L-0049`.
  - Verification intent: traceability and coverage tables; CHK-25.

## 5. Requirement-to-accepted-anchor traceability

| T016 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T016-STK-001 | `XCOM-SW-CORE-009` | XCOM-SYS-SC-001 | SC-001 | IX, X |
| T016-STK-002 | `XCOM-SW-CORE-009` | XCOM-SYS-SC-001 | SC-001 | IX |
| T016-STK-003 | `XCOM-SW-CORE-005/007` | XCOM-SYS-FR-010/028 | FR-010, FR-028 | IX |
| T016-STK-004 | `XCOM-SW-CORE-008` | XCOM-SYS-FR-024 | FR-024 | II, IX |
| T016-STK-005 | Constitution VII/IX; ADR-0018/0020 | – | FR-030 | VII, IX, X |
| T016-SR-001 | `XCOM-SW-CORE-009` | XCOM-SYS-SC-001 | SC-001 | VII, X |
| T016-SR-002 | `XCOM-SW-CORE-002/009` | XCOM-SYS-FR-004/005 | FR-004, FR-005 | IX |
| T016-SR-003 | `XCOM-SW-CORE-004/009` | XCOM-SYS-FR-006/007/008 | FR-006, FR-007, FR-008 | IX |
| T016-SR-004 | `XCOM-SW-CORE-003/004` | XCOM-SYS-FR-006/007/008 | FR-006, FR-007, FR-008 | IX |
| T016-SR-005 | `XCOM-SW-CORE-005` | XCOM-SYS-FR-009/010 | FR-009, FR-010 | V, IX |
| T016-SR-006 | `XCOM-SW-CORE-004/005` | XCOM-SYS-FR-008/009/010 | FR-008, FR-009, FR-010 | IX |
| T016-SR-007 | `XCOM-SW-CORE-004/007` | XCOM-SYS-FR-007/028 | FR-007, FR-028 | IX |
| T016-SR-008 | `XCOM-SW-CORE-006/010` | XCOM-SYS-FR-025 | FR-025 | SC-001 |
| T016-SR-009 | `XCOM-SW-CORE-005/009` | XCOM-SYS-FR-008/009/010 | FR-008, FR-009, FR-010 | SC-001 |
| T016-SR-010 | `XCOM-SW-CORE-005/007` | XCOM-SYS-FR-010 | FR-010 | IX |
| T016-SR-011 | `XCOM-SW-CORE-009` | XCOM-SYS-SC-001 | FR-006…FR-009, FR-025, SC-001 | IX |
| T016-SR-012 | `XCOM-SW-CORE-008` | XCOM-SYS-FR-024 | FR-024 | II, IX |
| T016-SR-013 | `XCOM-SW-CORE-004/007` | XCOM-SYS-FR-007 | FR-007 | IX |
| T016-SR-014 | Constitution VII/IX; ADR-0020 | – | FR-030 | VII, IX |
| T016-SR-015 | `XCOM-SW-CORE-007` | XCOM-SYS-FR-001/026/028 | FR-001, FR-026, FR-028 | II, VII |
| T016-SR-016 | public-safe evidence rule | XCOM-SYS-FR-027 | FR-027 | X |
| T016-SR-017 | `XCOM-SW-CORE` Doxygen | XCOM-SYS-FR-029 | FR-029 | X |
| T016-SR-018 | Constitution; ADR-0018/0020 | XCOM-SYS-FR-035 | FR-030, FR-035 | VII, IX |
| T016-SR-019 | ADR-0020 | – | FR-030 | X |
| T016-SR-020 | ADR-0020; `XCOM-L-0046/0049` | – | FR-030 | X |

`XCOM-SW-CORE-008` and `XCOM-SW-CORE-009` are the accepted capability-007 software requirements
(`docs/engineering/xcom/t008/requirements-register.{json,md}`) attributed to T016; `XCOM-SW-CORE-001…-007`
and `XCOM-SW-CORE-010` are attributed to T012–T015 and are verified here read-only. `XCOM-DU-007`/
`XCOM-DU-008` are the accepted T010 design units, the system requirements and `SC-*` are the accepted
`specs/007-xcom-core/spec.md` statements, and `XCOM-L-004{6,9}` are the accepted T008 traceability links
that record `XCOM-SW-CORE-008/009` as `verified_by` the `XCOM-T-CORE` test.

## 6. REF-002 disposition

T016 owns no REF-002 SADS ID. It provides the consolidated verification evidence against which the
allocated REF-002 communication IDs (`XVE-SYS-0139`–`0158`) and their shared contributions are later
verified. T016 changes no required disposition: the capability `ref002.disposition` stays `unchanged`
with an empty `promoted` list (T016-SR-018). No allocated, deferred, or target SADS requirement is
reported as implemented, and no `XVE-SYS-*` ID is promoted.

## 7. Affected paths

### 7.1 Paths the T016 candidate changes

| Path | Change | Notes |
| --- | --- | --- |
| `tests/xcom/core_matrix/test_support.hpp` | add | self-contained independent fixture/helpers; no other task's test-support include |
| `tests/xcom/core_matrix/unit_tests.cpp` | add | nominal consolidated matrix (interaction kinds, capabilities, policy, ownership, lifecycle, queue bounds, diagnostics) |
| `tests/xcom/core_matrix/negative_tests.cpp` | add | ≥ 20 individually named rejection cases (SC-001) across all four families |
| `tests/xcom/core_matrix/recovery_tests.cpp` | add | recovery, recreation, saturation recovery, reconciliation |
| `tests/xcom/core_matrix/fault_boundary_tests.cpp` | add | `XCOM-SW-CORE-008` controlled fault-hook boundary |
| `tests/xcom/core_matrix/concurrency_tests.cpp` | add | bounded deterministic concurrency (exactly-once, per-route FIFO) |
| `tests/xcom/core_matrix/consumer/main.cpp` | add | independent translation unit over the public include surface |
| `src/xverse/xcom/CMakeLists.txt` | edit | additive registration of the T016 executables/tests with a distinct `t016` label; existing entries untouched (shared serialized T012 path) |
| `docs/engineering/xcom/t016/requirements.md` | add | this document |
| `docs/engineering/xcom/t016/architecture.md` | add | suite context, components, data flow, interfaces |
| `docs/engineering/xcom/t016/detailed-design.md` | add | case design, fixtures, diagnostic tables, bounds, failure semantics |
| `docs/engineering/xcom/t016/unit-specifications.md` | add | units, ownership/lifetime/thread-safety/bounds, traceability |
| `docs/engineering/xcom/t016/verification-plan.md` | add | named checks, negative cases, commands |
| `docs/engineering/xcom/t016/implementation.md` | add (implementation stage) | realized change and evidence |
| `docs/engineering/xcom/t016/internal-review.json` | add (review stage) | DeepSeek internal review |
| `specs/007-xcom-core/tasks.md` | edit T016 checkbox (implementation stage) | capability task ledger |
| `reports/xcom-queue/t016-package.json` | add (package stage) | exact-candidate package record |

### 7.2 Consumed, read-only foundation (not changed by T016)

| Path | Owner | Role for T016 |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/{value,contract,item,diagnostic,result,core_types}.hpp` + `src/{value,contract,item,diagnostic}.cpp` | T013 (complete) | immutable core values, `FlowPolicy`, `DiagnosticCode`/`ValidationPhase`, exact diagnostics; read-only |
| `src/xverse/xcom/include/xverse/xcom/endpoint_route_lifecycle.hpp` + `src/endpoint_route_lifecycle.cpp` | T014 (complete) | endpoint/route lifecycle, exact generation-bound handles, declared `FlowPolicy` binding; read-only |
| `src/xverse/xcom/include/xverse/xcom/provider.hpp` + `src/provider.cpp` | T015 (complete) | provider composition, capability masks, `unsupported_policy` outcome, deterministic outcome text/code/message; read-only |
| `src/xverse/xcom/include/xverse/xcom/loopback_provider.hpp` + `src/loopback_provider.cpp` | T015 (complete) | owned loopback with fixed route/queue bounds; read-only |
| `src/xverse/xcom/include/xverse/xcom/observation.hpp` + `src/observation.cpp` | T021 (baseline, partial) | provider-neutral observation seam; the concrete bounded hook is owned by T021–T024; T016 reads it read-only where the fault-boundary check must distinguish controlled seams |
| `tests/xcom/{core_types,endpoint_route_lifecycle,provider_loopback,observation,activation_plan,validation_session}/**` | T013/T014/T015/T019/T020/T025 | existing suites; re-run unchanged, never edited |
| `cmake/*.cmake`, root `CMakeLists.txt` | shared (serialized, T012) | T011/T012 admitted envelope; T016 changes none |

### 7.3 Recorded attribution observation (not resolved by T016)

The accepted `docs/engineering/xcom/t008/requirements-register.{json,md}` attributes both
`XCOM-SW-CORE-008` (controlled fault-hook boundary, `FR-024`) and `XCOM-SW-CORE-009` (loopback
conformance and negative-case suite, `SC-001`) to T016, while the T016 task entry in
`specs/007-xcom-core/tasks.md` names only the test matrix. T016 resolves this by implementing the
**verification** obligation the register assigns: the consolidated conformance/negative suite realizes
`XCOM-SW-CORE-009`, and the CORE-008 boundary constraint is verified as the test-only negative
proposition that the core embeds no domain-specific fault semantics and exposes only controlled bounded
seams. T016 does **not** implement a new fault-hook feature, because `FR-024` declares hook exposure as
`MAY`, and clarification C11/ACC009 assign the concrete bounded communication hook to the observation
boundary owned by T021–T024. `docs/engineering/xcom/t008/traceability-matrix.{json,md}` records
`XCOM-SW-CORE-008/009` as `verified_by` `XCOM-T-CORE`; T016 satisfies that link and rewrites nothing.
The registers remain owned by T008/T009/T010 and `partial`/`unreconciled` (analysis A12).

### 7.4 Recorded cross-slice strengthening notes (additive only)

- `T014` review note: `test_route_policy_immutability` compares routes with different identities, so the
  inequality it asserts would hold on identity alone. T016 adds a **same-identity** pair differing only
  in declared `FlowPolicy` and asserts inequality (CHK-08); the T014 case is left unchanged.
- `T015` review note: no executed case prepares a successful `at_least_once → reliable` route. T016 adds
  that positive mapping case against a provider advertising the `reliable` bit (CHK-06); the T015 case
  and its `NEG-16` rejection counterpart are left unchanged.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- `T016-LIM-01` — The matrix is prototype verification evidence only: passing it proves no network
  provider, transport protocol, timing fidelity, compatibility, parity, or production readiness.
- `T016-LIM-02` — Tests exercise the in-process owned loopback and public headers; they do not execute a
  legacy binary, external peer, or any out-of-process path (that is T030–T034).
- `T016-LIM-03` — The `XCOM-SW-CORE-008` verification is a boundary/negative proof, not an
  implementation of a Faults-facing hook; the concrete bounded communication hook remains with
  T021–T024 (`T016-GAP-01`).
- `T016-LIM-04` — Strict declaration-level Doxygen (`WARN_IF_UNDOCUMENTED = YES`,
  `WARN_NO_PARAMDOC = YES`) remains open (`DOX-GAP-01`, `T011-GAP-01`), owned by T011/T037.
- `T016-LIM-05` — Deterministic concurrency is asserted by bounded repeated runs, not by a formal race
  proof; executed sanitizer evidence is T035’s obligation.
- `T016-LIM-06` — Restart reconciliation across processes is not implemented; "recovery" here means
  in-process saturation recovery, rejected-operation reusability, and generation recreation.

### 8.2 Gaps with owning tasks

| Gap | Description | Owner | Disposition |
| --- | --- | --- | --- |
| `T016-GAP-01` | Concrete bounded communication hook usable by the Faults subsystem. | T021–T024 | allocated; T016 verifies the core-side CORE-008 constraint only |
| `T016-GAP-02` | Executed sanitizer/static-analysis/Doxygen/benchmark evidence and the delivery bundle. | T035–T040 | allocated |
| `T016-GAP-03` | Candidate acceptance under capability 007. | T039/T041 | allocated; T016 submits for review |
| `T016-GAP-04` | Second synthetic provider and version-rejection contract suite. | T032–T034 | allocated |

### 8.3 Open items

- `T016-OPEN-01` — T016 uses GTest/discovered per-case reporting for the consolidated matrix (unlike the
  hand-rolled `main()` suites of T013–T015) to make each of the ≥ 20 negative cases individually named
  and reportable for `SC-001`. This is additive and changes no existing target; if a later task unifies
  the core suites, it must preserve each T016 case name or replace it with an equivalent stronger case.
- `T016-OPEN-02` — If a later task adds or moves a core test target, that owning task updates the shared
  build contract and the inherited T020 trace-link hashes; T016 changes no other build file.

## 9. Definition of done (requirements view)

T016 is complete for this slice when: (a) the five plan-stage work products exist under
`docs/engineering/xcom/t016/` and are mutually consistent; (b) every requirement in §3–§4 has ≥ 1 named
check in `verification-plan.md`; (c) the implementation stage delivers the consolidated matrix, the
CORE-008 boundary proof, the two additive strengthening cases, the additive build registration, marks
the T016 checkbox, and records `implementation.md`; (d) the deterministic gate and the named checks pass
at the candidate revision; (e) the package record is written; and (f) a separate DeepSeek internal
review records a passing verdict with no findings. This does **not** constitute user acceptance, which
remains T041.

## 10. Requirement-to-check index (implemented in `verification-plan.md`)

| Requirement | Primary check(s) |
| --- | --- |
| T016-STK-001 | CHK-02, CHK-04, CHK-25 |
| T016-STK-002 | CHK-05, CHK-16, NEG-01..NEG-27 |
| T016-STK-003 | CHK-09, CHK-12, CHK-15, CHK-18 |
| T016-STK-004 | CHK-17, NEG-28 |
| T016-STK-005 | CHK-02, CHK-19, CHK-23, CHK-24 |
| T016-SR-001 | CHK-04, CHK-19, NEG-30 |
| T016-SR-002 | CHK-03, CHK-05, NEG-01, NEG-02, NEG-03 |
| T016-SR-003 | CHK-06, NEG-06, NEG-07, NEG-08, NEG-09, NEG-14, NEG-16 |
| T016-SR-004 | CHK-07, CHK-08, NEG-05, NEG-10, NEG-11, NEG-12, NEG-13 |
| T016-SR-005 | CHK-09, NEG-21, NEG-22, NEG-24 |
| T016-SR-006 | CHK-10, CHK-11, NEG-18, NEG-20 |
| T016-SR-007 | CHK-12, CHK-18, NEG-04, NEG-15, NEG-17, NEG-18, NEG-19 |
| T016-SR-008 | CHK-13, NEG-05, NEG-11 |
| T016-SR-009 | CHK-14, NEG-20, NEG-21, NEG-25 |
| T016-SR-010 | CHK-15, NEG-18, NEG-22 |
| T016-SR-011 | CHK-16, NEG-01..NEG-27 |
| T016-SR-012 | CHK-17, NEG-28 |
| T016-SR-013 | CHK-18, NEG-15, NEG-22 |
| T016-SR-014 | CHK-19, NEG-30 |
| T016-SR-015 | CHK-20, NEG-28 |
| T016-SR-016 | CHK-21, NEG-29 |
| T016-SR-017 | CHK-22 |
| T016-SR-018 | CHK-23, NEG-30 |
| T016-SR-019 | CHK-24, NEG-30 |
| T016-SR-020 | CHK-25 |
