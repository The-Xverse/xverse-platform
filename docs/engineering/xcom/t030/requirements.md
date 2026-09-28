# T030 Requirements — Versioned gRPC/Protocol Buffers Tool API and Additive Evolution Rules

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T030 (capability 007, slice `T-CORE`/GW) |
| Task title | Define the versioned gRPC/Protocol Buffers tool API under `proto/xverse/xcom/v1/tool_gateway.proto` with additive evolution rules |
| Stage / role | plan → requirements |
| Revision | 1 (versioned external-tool contract slice) |
| Baseline revision | `80c236638e160c5e991e5a537e29d407e7462dc6` |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC006`, `ACC010`, `ACC011`, `ACC014`, `ACC015`); `ADR-0016` (subsystem naming); `ADR-0018` (platform-first); `ADR-0020` (repository-owned work products and exact-candidate evidence) |
| Owning slice | `T-CORE` (T007 ownership register); T030 is the first gateway (`GW`) task and owns the contract artifact only |
| Predecessors | T025–T029 accepted stimulation slice (consumed as prior accepted work); T011 admitted offline dependency envelope providing `protoc` 3.12.4 and `grpc_cpp_plugin` 1.30.2 (read-only inputs); T012 subtree CMake/CTest contract and warning-as-error rule; T013 immutable T-CORE contract/item/origin vocabulary (read-only); T017/T019/T020 XDL Profile and activation-plan digest binding (read-only) |
| Successor tasks | T031 (local-IPC-only gateway session), T032 (separate-process synthetic client + generated-client contract tests), T033 (reusable provider/observer/stimulation-tool/gateway contract suites), T034 (second minimal synthetic provider), T035–T041 (evidence, review, acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}` (`T-CORE` slice evidence names; T030 exclusive path `docs/engineering/xcom/t030/`); `docs/engineering/xcom/t008/requirements-register.{json,md}` (`XCOM-SW-GW-001` owning row plus `XCOM-SW-GW-002`/`-003`); `docs/engineering/xcom/t009/architecture-model.{json,md}` (`XCOM-CMP-010`, `XCOM-XB-008`, `XCOM-XB-010`, `XCOM-XLC-002`); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-019` tool gateway Protocol Buffers API, plus planned `XCOM-DU-020`/`-021`) |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production change and does
not implement, accept, or integrate the candidate. The T030 task entry in `specs/007-xcom-core/tasks.md` is the
authorized scope:

> T030 — Define the versioned gRPC/Protocol Buffers tool API under `proto/xverse/xcom/v1/tool_gateway.proto` with
> additive evolution rules.

### 1.1 Authority statement

T030 owns the **versioned external-tool contract** and its **additive evolution rules**. It defines the accepted
`proto/xverse/xcom/v1/tool_gateway.proto` external RPC contract for capability 007
(`XCOM-XLC-002`, `XCOM-DU-019`, `XCOM-CMP-010`), generates the C++ contract artifacts from that single source with the
T011-admitted `protoc`/`grpc_cpp_plugin`, and proves the contract with offline generated-contract tests.

It implements one accepted software requirement from `docs/engineering/xcom/t008/requirements-register.{json,md}`
that the register allocates to T030:

- `XCOM-SW-GW-001` "Versioned provider-neutral tool API" — "Define the versioned gRPC/Protocol Buffers tool API with
  additive evolution so no dashboard, product, test language, or transport protocol becomes a core primitive."
  (refines `XCOM-SYS-FR-022`, spec `FR-022`). T030 is recorded **implemented** for the contract slice by the T030
  per-task projection; the register row is not edited (T026–T029 precedent).

It contributes the contract surface consumed by the two accepted gateway software requirements that remain owned by
their own tasks and keep their recorded disposition:

- `XCOM-SW-GW-002` "Local-IPC-only bounded gateway" (`XCOM-SYS-FR-032`, `FR-032`) — **T031**;
- `XCOM-SW-GW-003` "Synthetic separate-process client" (`XCOM-SYS-SC-011`, `SC-011`) — **T032**.

It consumes the accepted design unit `XCOM-DU-019` "Tool gateway Protocol Buffers API" (family `GW`, kind `edge`,
language `proto`, scope `first-proof`), the accepted component `XCOM-CMP-010` "Local tool gateway", the accepted
external-rpc contract `XCOM-XLC-002` (`proto/xverse/xcom/v1/tool_gateway.proto`, fail-closed), and the accepted
architecture boundaries `XCOM-XB-008` (`XCOM-CMP-010 → XCOM-CMP-012`, `protobuf → external`, bidirectional,
validation-permit required) and `XCOM-XB-010` (`XCOM-CMP-011 → XCOM-CMP-010`, `protobuf → cpp`, bidirectional,
validation-permit required).

**Contract-only boundary.** T030 proves the contract at the schema, generated-descriptor, and generated-source level.
It authors no gateway server, no local IPC listener, no synthetic client, and no reusable contract suite. The gateway
session, the separate-process client, the reusable provider/observer/stimulation-tool/gateway contract suites, the
second synthetic provider, and executed sanitizer/static/Doxygen/benchmark/delivery evidence remain T031–T040.

**gRPC runtime linkage is out of envelope for T030.** The T011 admitted prefix provides the gRPC *generation* tools
(`protoc`, `grpc_cpp_plugin`) and the gRPC shared objects, but linking and running the gRPC C++ runtime requires
transitive libraries (for example `libcares`) that are **not** members of the admitted twelve-package set; a link
attempt fails closed. T030 therefore generates the gRPC stubs as a provenance artifact, compiles only the Protocol
Buffers message code (which links against the admitted `libprotobuf.a` alone), and verifies the gRPC service contract
through the generated `FileDescriptor` plus the generated stub source. Completing the gRPC runtime envelope is a
gateway-stage (T031) concern and its own recorded decision, not a T030 behaviour (`T030-GAP-02`).

It does **not** redesign the accepted architecture, change a functional requirement, success criterion, ADR, schema,
XDL profile, or contract; modify any accepted predecessor byte under `src/`, `tests/`, `xdl/`, or `docs/engineering/xcom/t0{07..29}/`;
implement the gateway or client (T031/T032); add an admitted dependency; or accept or integrate any candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, data model, the
T007 ownership register, the T008 register, the T009 architecture model, the T010 unit design, the constitution, or an
accepted ADR is resolved in favour of the accepted source. A material gap is reported rather than guessed. Unresolved
items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T030)

1. **One versioned contract artifact.** Author `proto/xverse/xcom/v1/tool_gateway.proto` (`syntax = "proto3"`,
   `package xverse.xcom.v1`) as the single versioned source of the external-tool API. No duplicate or competing
   definition is introduced.
2. **gRPC service surface.** Declare `service ToolGateway` with the accepted tool-gateway contract surface: version
   and capability inspection; observation open/read/close; validation-session arm/revoke; signal/message/service/
   emulation submission; service-emulation lease acquire/release; and bounded session-outcome/counter query.
3. **Version negotiation.** Declare `ProtocolVersion` (major/minor), a bounded `GatewayCapabilities` record, and an
   explicit fail-closed compatibility rule for an unsupported major version.
4. **Additive evolution rules.** Pin the contract package and message/enum field numbers; declare a reserved extension
   band in every message; forbid renumbering, reuse, or removal-without-reservation; and require that unknown fields
   and unmapped enum values survive a proto3 round trip.
5. **Generated-code provenance.** Generate the C++ Protocol Buffers messages (compiled) and the gRPC stubs
   (provenance-only) from the `.proto` with the T011-admitted `protoc` and `grpc_cpp_plugin`, and record the input
   schema identity, generation command, generator identity, and output digests.
6. **Additive build wiring.** Add one generated-code library and additive `t030-<kind>`-labelled generated-contract
   test executables in `src/xverse/xcom/CMakeLists.txt`, declaring any runtime-inventory change explicitly.
7. **Generated-contract tests.** Prove package/version, the service and method surface, request/response and
   streaming declarations, version negotiation, declared bounds, message vocabulary, additive-evolution invariants,
   unknown-field and unmapped-enum forward compatibility, and the absence of forbidden transport/payload shapes.
8. **Bounded, offline, deterministic tests.** Every list, table, scan, and iteration is finite and declared; the
   suites are offline and local-only and add no admitted dependency; no case depends on wall-clock timing.
9. The T030 repository-owned work products and the T030 package record.

### 2.2 Explicit exclusions (must remain absent from the T030 candidate)

No gateway server, local IPC listener, socket, or separate process (T031/T032); no compiled or linked gRPC runtime;
no reusable contract-suite abstraction (T033); no second synthetic provider (T034); no benchmark, executed
sanitizer/static/Doxygen evidence, or delivery bundle (T035–T040); no dashboard, storage, query-presentation, or
export primitive; no network, socket, DNS, TLS, ambient/secret, dynamic-load, subprocess, or legacy
repository/binary access; no wall-clock-dependent verdict; no production XDL or activation-plan change; no change to
any accepted predecessor path under `src/`, `tests/`, `xdl/`, or `docs/engineering/xcom/t0{07..29}/`; no new admitted
dependency; no rewrite or weakening of an accepted ADR, requirement, contract, schema, register, target, or test; no
promotion of any REF-002 SADS ID beyond its recorded disposition; no acceptance or integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T030 |
| --- | --- | --- |
| Local-IPC-only gateway session with deadlines, flow control, safe logs, disconnect cleanup | T031 | allocated; T030 defines only the wire contract |
| Separate-process synthetic client and generated-client contract tests | T032 | allocated; T030 authors descriptor/source contract tests only |
| Reusable provider/observer/stimulation-tool/gateway contract suites | T033 | allocated |
| Second minimal synthetic provider; replaceability and version rejection | T034 | allocated; T030 verifies version negotiation at the contract level only |
| Executed sanitizer/static-analysis/Doxygen evidence, benchmarks, delivery bundle | T035–T040 | allocated |
| Independent review and user acceptance | T039/T041 | allocated; external Codex review and acceptance deferred until backlog `xcom-t030-t034-20260928` completes |

## 3. Stakeholder requirements (`T030-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T030-STK-001**: Before any gateway implementation is accepted, the program **shall** own one versioned,
  machine-readable external-tool contract at `proto/xverse/xcom/v1/tool_gateway.proto` with documented
  additive-evolution rules, generated C++ artifacts, and repository-owned generated-contract tests.
- **T030-STK-002**: The contract **shall** stay provider-neutral and domain-neutral: logical identities only, no
  transport/address/port/credential primitive, no dashboard/storage/query/export primitive, and an explicit
  fail-closed rule for an unsupported protocol version.
- **T030-STK-003**: The contract and its tests **shall** be verifiable offline against the T011-admitted envelope:
  generation provenance recorded, generated code compiled, and contract tests run without a network, listener,
  external peer, or legacy binary.
- **T030-STK-004**: T030 **shall** preserve accepted intent: additive changes only; no accepted production byte,
  existing test, ADR, contract, register, register row, or requirement weakened; predecessor work products and
  provenance preserved.
- **T030-STK-005**: T030 **shall** report maturity honestly: `XCOM-SW-GW-001` is recorded implemented by T030 for the
  contract slice, while `XCOM-SW-GW-002`/`-003` and T031–T041 remain allocated; the REF-002 disposition stays
  `unchanged` with an empty `promoted` list and no requirement is promoted beyond its recorded disposition.

## 4. Software/engineering requirements (`T030-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted anchor.
"Verified" means the repository-owned test or inspection exists, is deterministic, and passes at the recorded
candidate revision; it is not a deployed-service, compatibility, or end-to-end route claim.

### 4.1 Contract artifact and version identity

- **T030-SR-001 [ubiquitous]**: The contract **shall** be defined once at `proto/xverse/xcom/v1/tool_gateway.proto`
  using `syntax = "proto3"` and `package xverse.xcom.v1`, and **shall** be the single versioned source of the tool
  API (no duplicate or competing definition), matching the accepted `XCOM-XLC-002` external-rpc contract locator.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-022`; FR-022; `XCOM-XLC-002`, `XCOM-DU-019`.
  - Verification intent: source inspection and the package/syntax test; CHK-01, CHK-03.
- **T030-SR-002 [ubiquitous]**: The contract **shall** declare the `ToolGateway` service surface required by the
  accepted tool-gateway contract: version/capability inspection; observation open, read (server streaming), and close;
  validation-session arm and revoke; signal/message/service/emulation submission; service-emulation lease acquire and
  release; and bounded session-outcome/counter query.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-022`, `XCOM-SYS-FR-023`; FR-022, FR-023; `XCOM-CMP-010`,
    `XCOM-XB-008`, `XCOM-XB-010`.
  - Verification intent: service-surface descriptor test; CHK-04.

### 4.2 Version negotiation

- **T030-SR-003 [event-driven]**: When a tool negotiates the protocol, the contract **shall** expose an explicit
  `ProtocolVersion` (major/minor) and a bounded capability record, and **shall** permit an unsupported major version
  to be rejected by an explicit fail-closed predicate that does not depend on an absent field.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-022`, `XCOM-SYS-FR-032`; FR-022, FR-032; `XCOM-DU-019`.
  - Verification intent: version-negotiation descriptor test and the test-local compatibility predicate;
    CHK-05, CHK-14.

### 4.3 Observation, session, and stimulation surface

- **T030-SR-004 [ubiquitous]**: The observation surface **shall** be a bounded contract carrying normalized metadata
  (identity, route, contract, clock domain, sequence, outcome), with an explicit bounded opt-in payload view and a
  payload-state field; metadata-only records **shall** carry no payload bytes.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-011`, `XCOM-SYS-FR-012`, `XCOM-SYS-FR-023`; FR-011, FR-012,
    FR-023; `XCOM-XLC-002`.
  - Verification intent: observation-contract descriptor test; CHK-06.
- **T030-SR-005 [event-driven]**: When a tool arms or revokes a validation session, the contract **shall** carry the
  exact permit, session, plan digest, graph digest, protocol identity, and validity bound in the request and a bounded
  session state plus diagnostic in the response; the contract **shall** define no field that bypasses the permit.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-016`, `XCOM-SYS-FR-032`; FR-016, FR-032; `XCOM-XLC-002`.
  - Verification intent: session-contract descriptor test; CHK-07.
- **T030-SR-006 [ubiquitous]**: The submission surface **shall** represent all four allowed stimulation actions
  (inject signal, inject message, invoke service, emulate service) with explicit action, target endpoint, contract,
  interaction, direction, correlation, causation, schedule, deadline, and bounded payload-size declarations.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-015`, `XCOM-SYS-FR-018`, `XCOM-SYS-FR-020`; FR-015, FR-018,
    FR-020; `XCOM-XLC-002`.
  - Verification intent: stimulation-action descriptor test; CHK-08.
- **T030-SR-007 [event-driven]**: When a tool acquires, uses, or releases a service-emulation lease, the contract
  **shall** bind the request to the exact session, endpoint identity, endpoint generation, and plan digest, and
  **shall** expose the exclusive lease state.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-034`; FR-034; `XCOM-XLC-002`.
  - Verification intent: lease-contract descriptor test; CHK-09.
- **T030-SR-008 [ubiquitous]**: The contract **shall** expose bounded session outcome and counter queries with
  declared finite counters and an explicit evidence-incomplete state, and **shall not** expose dashboard, storage,
  query-presentation, or export primitives.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-021`, `XCOM-SYS-FR-023`; FR-021, FR-023; `XCOM-XLC-002`.
  - Verification intent: outcome/counter descriptor test and the forbidden-vocabulary scan; CHK-10, CHK-13.
- **T030-SR-009 [ubiquitous]**: The contract **shall** define a deterministic diagnostic record (stable code,
  severity, phase, affected identity, reason, correction) consistent with the accepted T-CORE diagnostic vocabulary.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-025`; FR-025; T013 diagnostic vocabulary.
  - Verification intent: diagnostic descriptor test; CHK-11.

### 4.4 Bounds and domain neutrality

- **T030-SR-010 [ubiquitous]**: The contract **shall** declare every bound the gateway must enforce — maximum
  message size, maximum concurrent streams, maximum deadline, observation record/queue bounds, payload bound, and
  lease duration — as explicit fields; no bound **shall** be implicit or unbounded.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-013`, `XCOM-SYS-FR-020`; FR-013, FR-020; `XCOM-XLC-002`.
  - Verification intent: declared-bounds descriptor test; CHK-12.
- **T030-SR-011 [unwanted]**: If the schema exposed a transport, address, port, socket, DNS, TLS, credential, or
  TCP-listener primitive, the contract tests **shall** fail closed; the contract **shall** carry logical identities
  only.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-022`, `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028`; FR-022, FR-026,
    FR-028; `XCOM-XLC-002`.
  - Verification intent: forbidden-shape descriptor scan; CHK-13, NEG-01, NEG-02, NEG-03.

### 4.5 Additive evolution

- **T030-SR-012 [ubiquitous]**: The contract **shall** encode additive-evolution rules: package and field
  numbers/names are pinned, a reserved extension band is declared in every message, and no field number **shall** be
  renumbered, reused, or removed without reservation.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-022`; FR-022; `XCOM-XLC-002`, `XCOM-DU-019`.
  - Verification intent: reserved-band and field-manifest pinning tests; CHK-14, CHK-15.
- **T030-SR-013 [event-driven]**: When a producer sends an unknown field or an unmapped enum value, the generated
  contract **shall** preserve the value across a proto3 round trip rather than failing the parse or silently remapping
  it, so an additive producer change cannot corrupt an older consumer.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-022`; FR-022; `XCOM-DU-019`.
  - Verification intent: unknown-field and unmapped-enum forward-compatibility tests; CHK-15, NEG-04, NEG-05.

### 4.6 Generated-code provenance and build wiring

- **T030-SR-014 [ubiquitous]**: The repository **shall** generate the C++ contract artifacts from the `.proto` with
  the T011-admitted `protoc` and `grpc_cpp_plugin` during the build, and **shall** record the input-schema identity,
  generation command, generator identity, and output digests as generated-code provenance.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-029`, `XCOM-SYS-FR-030`; FR-029, FR-030; T011 dependency-lock
    generated-code provenance; `T011-GAP-02`.
  - Verification intent: generation-provenance inspection and generated-source assertions; CHK-16.
- **T030-SR-015 [ubiquitous]**: Build wiring **shall** be additive: one generated-code library and additive
  `t030-<kind>`-labelled generated-contract test executables registered in `src/xverse/xcom/CMakeLists.txt`, with any
  runtime-inventory change declared explicitly and no existing target, test name, label, command, or expected value
  changed.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-030`; FR-030; T012 subtree build contract.
  - Verification intent: changed-path and discovered-count comparison; CHK-16, CHK-17, NEG-06.

### 4.7 Generated-contract tests and safety

- **T030-SR-016 [ubiquitous]**: The generated-contract tests **shall** verify, against the generated descriptor, the
  package/version, the exact service and method surface, every request/response and streaming declaration, version
  negotiation, every declared bound, and the presence of every required message and enum.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-022`, `XCOM-SYS-FR-030`; FR-022, FR-030; `XCOM-DU-019`.
  - Verification intent: contract-suite descriptor tests; CHK-04, CHK-05, CHK-06, CHK-08, CHK-12.
- **T030-SR-017 [ubiquitous]**: The tests **shall** be offline and local-only: they **shall** use only the C++
  standard library, GTest, and the admitted Protocol Buffers runtime; they **shall** perform no network, socket,
  resolver, TLS, ambient/secret, dynamic-load, subprocess, or legacy access and **shall** add no new admitted
  dependency.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028`; FR-026, FR-028; ADR-0019; Constitution
    II, VII.
  - Verification intent: forbidden-API source scan and the offline build; CHK-18, NEG-07.
- **T030-SR-018 [ubiquitous]**: The committed contract, generated provenance, tests, and work products **shall**
  contain no credential, private address, real or proprietary payload, environment-specific absolute host path, or
  sensitive deployment value.
  - Refines: `XCOM-SW-GW-001`; anchors `XCOM-SYS-FR-027`; FR-027; Constitution X; public-safe evidence rule.
  - Verification intent: public-safety scan; CHK-19, NEG-08.

### 4.8 Governance and gate

- **T030-SR-019 [ubiquitous]**: T030 **shall** reconcile with the T007 ownership register, the T008 requirement
  register, the T009 architecture model, and the T010 unit design without rewriting or weakening them; **shall** keep
  the register REF-002 disposition `unchanged` with an empty `promoted` list; and **shall** record honestly that
  `XCOM-SW-GW-001` is implemented for the contract slice by T030 while `XCOM-SW-GW-002`/`-003` and T031–T041 remain
  allocated.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-035`, `XCOM-SYS-FR-030`; FR-030, FR-035; Constitution VII, IX.
  - Verification intent: register validators plus the recorded-maturity inspection; CHK-20, NEG-09.
- **T030-SR-020 [ubiquitous]**: The T030 candidate **shall** satisfy the deterministic Phase 7 gate: the five plan
  work products and the implementation record exist; `proto/xverse/xcom/v1/tool_gateway.proto` and at least one
  `tests/` path change; the Phase 7 runner's unit configure/build and `t030-`-labelled discovery pass; `git diff
  --check` is clean; and the T030 checkbox is marked complete **only** in the implementation stage.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-030`; FR-030; Constitution X.
  - Verification intent: `xcom_phase7_gate.py verify T030 <baseline>`; `git diff --check`; CHK-21, NEG-10.

## 5. Requirement-to-accepted-anchor traceability

| T030 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T030-STK-001 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-022` | FR-022 | VII, X |
| T030-STK-002 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-022/026/028` | FR-022, FR-026, FR-028 | II, VII |
| T030-STK-003 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-028/029/030` | FR-028–FR-030 | II, IX |
| T030-STK-004 | Constitution VII/IX; ADR-0020 | `XCOM-SYS-FR-030` | FR-030 | VII, IX |
| T030-STK-005 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-035` | FR-035 | VII, IX |
| T030-SR-001 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-022` | FR-022 | VII, IX |
| T030-SR-002 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-022/023` | FR-022, FR-023 | IX |
| T030-SR-003 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-022/032` | FR-022, FR-032 | IX |
| T030-SR-004 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-011/012/023` | FR-011, FR-012, FR-023 | IX |
| T030-SR-005 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-016/032` | FR-016, FR-032 | IX |
| T030-SR-006 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-015/018/020` | FR-015, FR-018, FR-020 | IX |
| T030-SR-007 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-034` | FR-034 | IX |
| T030-SR-008 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-021/023` | FR-021, FR-023 | IX |
| T030-SR-009 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-025` | FR-025 | IX |
| T030-SR-010 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-013/020` | FR-013, FR-020 | IX |
| T030-SR-011 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-022/026/028` | FR-022, FR-026, FR-028 | II, VII, IX |
| T030-SR-012 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-022` | FR-022 | VII, IX |
| T030-SR-013 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-022` | FR-022 | IX |
| T030-SR-014 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-029/030` | FR-029, FR-030 | IX, X |
| T030-SR-015 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-030` | FR-030 | VII, X |
| T030-SR-016 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-022/030` | FR-022, FR-030 | IX |
| T030-SR-017 | `XCOM-SW-GW-001` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | II, VII |
| T030-SR-018 | public-safe evidence rule | `XCOM-SYS-FR-027` | FR-027 | X |
| T030-SR-019 | Constitution; ADR-0020 | `XCOM-SYS-FR-030/035` | FR-030, FR-035 | VII, IX |
| T030-SR-020 | ADR-0020 | `XCOM-SYS-FR-030` | FR-030 | X |

`XCOM-SW-GW-001` is an accepted capability-007 software requirement
(`docs/engineering/xcom/t008/requirements-register.{json,md}`). It is accepted text; T030 satisfies it for the
contract slice and does not rewrite it. The register row is not changed and no register maturity is promoted by the
plan stage; the per-task maturity projection is recorded in the T030 work products, following the T026–T029
precedent.

## 6. REF-002 disposition

T030 owns no REF-002 SADS ID and promotes none. It contributes contract-level evidence toward the allocated
communication IDs already exercised by the communication boundary: `XVE-SYS-0141` is **deferred** ("protocol/provider
capabilities") in the accepted allocation, so the versioned external-tool contract is recorded as a **partial
contribution** to that deferred target and is **not** promoted; nothing in the `promoted` list changes. The
capability `ref002.disposition` stays `unchanged` (T030-SR-019). No allocated, deferred, architectural-target, or
superseded SADS requirement is reported as implemented.

## 7. Affected paths

### 7.1 Paths the T030 candidate changes (implementation stage)

| Path | Change | Notes |
| --- | --- | --- |
| `proto/xverse/xcom/v1/tool_gateway.proto` | add | the single versioned external-tool contract (`XCOM-XLC-002`, `XCOM-DU-019`) |
| `src/xverse/xcom/CMakeLists.txt` | edit | generate `.pb.{h,cc}` (compiled) and `.grpc.pb.{h,cc}` (provenance-only) via the admitted `protoc`/`grpc_cpp_plugin`; add `xverse_xcom_tool_gateway_proto` and register additive `t030-<kind>` test executables; extend `XVERSE_XCOM_RUNTIME_TARGETS` with the one new generated-code library |
| `tests/xcom/tool_gateway/contract_support.hpp` | add | bounded, test-local descriptor helpers and the pinned field manifest (payload-free) |
| `tests/xcom/tool_gateway/contract_tests.cpp` | add | `T30-TS-001`…`T30-TS-011` |
| `tests/xcom/tool_gateway/evolution_tests.cpp` | add | `T30-TS-012`…`T30-TS-016` |
| `tests/xcom/tool_gateway/negative_tests.cpp` | add | `T30-TS-017`…`T30-TS-021` |
| `tests/xcom/tool_gateway/provenance_tests.cpp` | add | `T30-TS-022`…`T30-TS-024` |
| `engineering/project.json` | edit | current task T030 and accepted baseline `80c2366…` |
| `engineering/requirements/T030-STK-00{1..5}.json`, `T030-SR-0{01..20}.json` | add | current-task requirement records |
| `engineering/requirements/XCOM-SYS-*.json` | add | missing accepted system-anchor records only (FR-022 and the referenced anchors) |
| `engineering/architecture/components/T030-SR-0{01..20}-CMP.json` | add | current-task component allocations |
| `engineering/unit-specifications/T030-SR-0{01..20}-U.json` | add | current-task unit specifications |
| `engineering/validation/scenarios/T030-VS-ACCUMULATED.json` | add | current-task validation scenario |
| `engineering/trace/links.json` | edit | additive T030 trace links; `implemented_by` code-digest links and the inherited `T020-L-046` digest refresh are recorded at implementation |
| `engineering/stage-results/*.json` | edit | inherited artifact-digest refresh when `src/xverse/xcom/CMakeLists.txt` changes |
| `docs/engineering/xcom/t030/requirements.md` | add | this document |
| `docs/engineering/xcom/t030/architecture.md` | add | T030 architecture |
| `docs/engineering/xcom/t030/detailed-design.md` | add | T030 detailed design |
| `docs/engineering/xcom/t030/unit-specifications.md` | add | T030 unit specifications |
| `docs/engineering/xcom/t030/verification-plan.md` | add | T030 verification plan |
| `docs/engineering/xcom/t030/implementation.md` | add | implementation-stage record |
| `docs/engineering/xcom/t030/internal-review.json` | add | internal-review record |
| `reports/review-index.md` | edit | T030 candidate section appended |
| `specs/007-xcom-core/tasks.md` | edit | one-line T030 checkbox, **implementation stage only** |
| `reports/xcom-queue/t030-package.json` | add | implementation-stage package record |

### 7.2 Consumed read-only (not changed by T030)

`cmake/XComOfflineDependencies.cmake`, `cmake/XComWarnings.cmake`, the root `CMakeLists.txt`, `scripts/**`,
`xdl/**`, `src/xverse_xdl/**`, all accepted `src/xverse/xcom/**` runtime sources and headers other than the additive
build wiring, every accepted test under `tests/xcom/**` other than the new `tests/xcom/tool_gateway/**`,
`docs/engineering/xcom/task-ownership.*`, `docs/engineering/xcom/t00{7,8,9}/**`, `docs/engineering/xcom/t0{1..29}/**`,
`docs/engineering/xcom/build-environment.md`, `docs/engineering/xcom/dependency-lock.md`, and
`specs/007-xcom-core/**` (other than the T030 checkbox).

### 7.3 Explicitly not implemented by T030

The local-IPC-only gateway session (T031), the separate-process synthetic client and generated-client tests (T032),
the reusable contract suites (T033), the second synthetic provider (T034), the benchmark/sanitizer/static/Doxygen/
delivery tasks (T035–T040), and the executed gRPC runtime server. External Codex review and user acceptance remain
T039/T041 and are deferred until the ordered backlog `xcom-t030-t034-20260928` completes.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- **T030-GAP-01 — contract-only boundary.** T030 authors the schema, generates artifacts, and proves the contract at
  the descriptor and generated-source level; it establishes no deployed service, transport, IPC, compatibility, or
  production-readiness claim.
- **T030-GAP-02 — gRPC runtime linkage out of envelope.** The T011 admitted prefix provides the gRPC generation tools
  and shared objects but not the transitive runtime libraries (for example `libcares`); a standalone gRPC++ link fails
  closed. T030 compiles only the Protocol Buffers messages and generates (does not link) the gRPC stubs; completing
  the gRPC runtime envelope is T031's recorded decision.
- **T030-GAP-03 — version rejection is contract-level.** T030 proves the schema exposes the version fields and pins a
  test-local fail-closed compatibility predicate; the production predicate and server-side rejection are T031/T034.
- **T030-GAP-04 — no separate-process proof.** T030 runs in-process descriptor tests only; the separate-process client
  proof and no-TCP-listener demonstration are T032 (`SC-011`).
- **T030-GAP-05 — generated code is not Doxygen-documented.** The generated C++ documentation policy remains
  `DOX-GAP-02`; warning-free generated-code documentation is T037.
- **T030-GAP-06 — no reusable abstraction.** The test helpers are T030-local and are not the T033 reusable gateway
  contract suite.

### 8.2 Gaps with owning tasks

| Gap | Owner |
| --- | --- |
| gRPC runtime envelope and local-IPC gateway session | T031 |
| Separate-process synthetic client and no-TCP proof (`SC-011`) | T032 |
| Reusable contract suites and second synthetic provider | T033/T034 |
| Executed sanitizer/static/Doxygen/benchmark and delivery bundle | T035–T040 |
| Independent review and user acceptance | T039/T041 |

### 8.3 Open items

- **T030-OPEN-01 — inherited provenance refresh.** Editing `src/xverse/xcom/CMakeLists.txt` invalidates the inherited
  `T020-L-046` `implemented_by` target digest in `engineering/trace/links.json` and the declared
  `links.json`/`CMakeLists.txt` digests in `engineering/stage-results/*.json`. Following the T026–T029 precedent, the
  implementation stage refreshes those inherited digests; no requirement, link identity, relation, or stage result
  changes. The exact digests are recorded in the implementation record.
- **T030-OPEN-02 — generation environment inside the build.** Running the admitted `protoc`/`grpc_cpp_plugin` during
  the build requires the admitted prefix library directory on the process library path; the build wraps the generator
  with the explicit admitted prefix path only (no ambient discovery, no network). The recorded generation command and
  generator digest are public-safe.
- **T030-OPEN-03 — runtime-inventory change.** Adding `xverse_xcom_tool_gateway_proto` updates the T012
  `XVERSE_XCOM_RUNTIME_TARGETS` inventory and the generated `xcom_build_contract` expectation in the same change, as
  the T012 contract requires.

## 9. Definition of done (requirements view)

T030 is done for a candidate revision when: every §4 requirement has at least one named check; the versioned contract,
service surface, version negotiation, additive-evolution rules, generated-code provenance, additive build wiring, and
the generated-contract tests are proven at the recorded candidate revision; `XCOM-SW-GW-001` is recorded implemented
for the contract slice by T030 while `XCOM-SW-GW-002`/`-003` and T031–T041 remain allocated; no accepted requirement,
test, ADR, contract, register, or predecessor byte is weakened; the register validators pass with REF-002 unchanged
and nothing promoted; the deterministic Phase 7 gate passes; and a separate DeepSeek internal review records its
findings before any repair. This does not constitute user acceptance, which remains T041.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary checks |
| --- | --- |
| T030-STK-001 | CHK-01, CHK-03, CHK-16 |
| T030-STK-002 | CHK-05, CHK-13, CHK-14 |
| T030-STK-003 | CHK-16, CHK-18, CHK-21 |
| T030-STK-004 | CHK-02, CHK-17, CHK-20 |
| T030-STK-005 | CHK-20, CHK-21 |
| T030-SR-001 | CHK-01, CHK-03 |
| T030-SR-002 | CHK-04 |
| T030-SR-003 | CHK-05, CHK-14 |
| T030-SR-004 | CHK-06 |
| T030-SR-005 | CHK-07 |
| T030-SR-006 | CHK-08 |
| T030-SR-007 | CHK-09 |
| T030-SR-008 | CHK-10, CHK-13 |
| T030-SR-009 | CHK-11 |
| T030-SR-010 | CHK-12 |
| T030-SR-011 | CHK-13 |
| T030-SR-012 | CHK-14, CHK-15 |
| T030-SR-013 | CHK-15 |
| T030-SR-014 | CHK-16 |
| T030-SR-015 | CHK-17 |
| T030-SR-016 | CHK-04, CHK-05, CHK-06, CHK-07, CHK-08, CHK-09, CHK-10, CHK-11, CHK-12 |
| T030-SR-017 | CHK-18 |
| T030-SR-018 | CHK-19 |
| T030-SR-019 | CHK-20 |
| T030-SR-020 | CHK-21 |
