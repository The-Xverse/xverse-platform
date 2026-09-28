# T032 Requirements — Separate-Process Synthetic Client and Generated-Client Contract Tests

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T032 (capability 007, slice `T-CORE`/GW) |
| Task title | Implement a separate-process synthetic client and generated-client contract tests for observation and every allowed stimulation action |
| Stage / role | plan → requirements |
| Revision | 1 (separate-process synthetic-client conformance slice) |
| Baseline revision | `e6197c67868213ffb6523d8bf62ed4c2c4e3b0af` |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC006`, `ACC010`, `ACC011`, `ACC014`, `ACC015`); `ADR-0016` (subsystem naming); `ADR-0018` (platform-first); `ADR-0019` (X-COM observation/stimulation boundary); `ADR-0020` (repository-owned work products and exact-candidate evidence) |
| Owning slice | `T-CORE` (T007 ownership register); T032 is the gateway (`GW`) conformance-client task that owns the separate-process synthetic tool client and its generated-client contract tests |
| Predecessors | T031 accepted bounded local-IPC-only gateway (`tool_gateway.hpp`, `tool_gateway.cpp`, `LocalIpcEndpoint`, `GatewaySession`, `gateway_decode_request_frame`, `gateway_operation_names()`); T030 accepted versioned `XCOM-XLC-002` contract (`proto/xverse/xcom/v1/tool_gateway.proto`, generated message library `xverse_xcom_tool_gateway_proto`); T025–T029 accepted validation-permit, journal, guard, action-path, and lease contracts (read-only); T021–T024 accepted bounded observation boundary (read-only); T011 admitted offline envelope (`protoc` 3.12.4, `grpc_cpp_plugin` 1.30.2, `libprotobuf.a`); T012 subtree CMake/CTest contract |
| Successor tasks | T033 (reusable contract suites), T034 (second synthetic provider), T035–T041 (evidence, review, acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}` (`T-CORE` slice evidence names; T032 exclusive paths `docs/engineering/xcom/t032/`, `reports/xcom-queue/t032-package.json`); `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-SW-GW-003` owning row); `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-010`, `XCOM-CMP-011`, `XCOM-CMP-012`, `XCOM-XB-010`, `XCOM-XLC-002`, `XCOM-INV-08`, `XCOM-INV-13`, `XCOM-INV-15`); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-021` separate-process synthetic tool client; `XCOM-DU-019`, `XCOM-DU-020` consumed read-only) |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production change and does
not implement, accept, or integrate the candidate. The T032 task entry in `specs/007-xcom-core/tasks.md` is the
authorized scope:

> T032 — Implement a separate-process synthetic client and generated-client contract tests for observation and every
> allowed stimulation action.

It also realizes the accepted external-tool contract statement in `specs/007-xcom-core/contracts/tool-gateway.md`
(the first external-tool proof uses a versioned provider-neutral service on a host-protected local IPC endpoint with
no TCP address) and success criterion `SC-011` at the separate-process client boundary.

### 1.1 Authority statement

T032 owns the **separate-process synthetic client and its generated-client contract tests**. It implements one
accepted software requirement from `docs/engineering/xcom/t008/requirements-register.{json,md}` that the register
allocates to T032:

- `XCOM-SW-GW-003` "Separate-process synthetic client conformance" — "Prove with a separate-process synthetic client
  that observation and every allowed stimulation action work through a host-protected local endpoint with no TCP
  listener and zero items from invalid or expired sessions." (refines `XCOM-SYS-SC-011`, spec `SC-011`). T032 records
  this requirement **implemented** for the conformance-client slice by the T032 per-task projection; the register row
  is not edited (T026–T031 precedent).

It consumes the accepted T030 contract and the accepted T031 gateway read-only, and it contributes the
separate-process conformance evidence that `SC-011` names. T032 realizes the accepted design unit `XCOM-DU-021`
"Separate-process synthetic tool client" (family `GW`, kind `test-fixture`, language `cpp`, scope `first-proof`,
owning tasks T032/T033), the accepted component `XCOM-CMP-011` "Synthetic sink and tools", the accepted external-rpc
contract `XCOM-XLC-002`, and the accepted IPC boundary `XCOM-XB-010` (`XCOM-CMP-011 → XCOM-CMP-010`, `protobuf → cpp`,
bidirectional, validation-permit required, `first-proof`).

**Recorded contract decision (`T032-DD-01`, `T032-SR-017`).** The T011 admitted envelope supplies the gRPC
*generation* tools and the generated message library but **not** the gRPC runtime transitive libraries, so a
standalone gRPC++ link fails closed (`T030-GAP-02`, verified; `T031-GAP-01` recorded). T032 records its own decision
rather than guessing: it realizes the accepted `XCOM-XLC-002` **generated message and method contract** (the
T030-generated Protocol Buffers messages and the ten `ToolGateway` method names) through the same bounded,
host-protected `AF_UNIX` framing T031 defines, binding the client method table 1:1 to the generated `ToolGateway`
service descriptor method set. It adds no admitted dependency and does not pretend a gRPC runtime is linked. The gRPC
transport runtime remains an explicit deferred gap (`T032-GAP-01`), and the framing is bound 1:1 to the T030 generated
method names so it introduces no competing interface or configuration language.

**Client-only boundary.** T032 authors the separate-process synthetic client process, its bounded test-local server
harness, and the generated-client contract suites. It authors no reusable provider/observer/stimulation-tool/gateway
contract-suite abstraction (T033), no second synthetic provider (T034), no change to the accepted T030 contract or
T031 gateway production sources, and no benchmark/sanitizer/static/Doxygen/delivery bundle (T035–T040).

It does **not** redesign the accepted architecture, change a functional requirement, success criterion, ADR, schema,
XDL profile, or contract; modify any accepted predecessor byte under `src/`, `tests/`, `xdl/`, or
`docs/engineering/xcom/t0{07..31}/` other than the additive `src/xverse/xcom/CMakeLists.txt` wiring and the status-only
planned→established path reconciliation for the T032 fixture path; implement the reusable suites or second provider;
add an admitted dependency; weaken `T030-SR-*`, `T031-SR-*`, or any accepted test; or accept or integrate any
candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, data model, the
T007 ownership register, the T008 register, the T009 architecture model, the T010 unit design, the constitution, or
an accepted ADR is resolved in favour of the accepted source. A material gap is reported rather than guessed.
Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T032)

1. **One separate-process synthetic client.** Author `src/xverse/xcom/fixtures/synthetic_tool.cpp` building the
   bounded executable `xverse_xcom_synthetic_client` that realizes the accepted `XCOM-XLC-002` generated message and
   method contract for one local synthetic tool. No competing contract, configuration language, or RPC definition is
   introduced.
2. **Generated-client method surface.** The client recognizes all ten accepted `ToolGateway` operations by their exact
   T030 method names through the generated service descriptor; the committed client operation table is asserted equal
   to the generated `ToolGateway` service descriptor method set.
3. **Separate-process execution.** The client runs as its own OS process, launched by the T032 tests with an explicit
   bounded argument vector and a scrubbed, admitted environment; it contacts no legacy binary, external peer,
   production workload, or network listener.
4. **Host-protected local-only transport.** The client connects only to the accepted `AF_UNIX` host-protected local
   endpoint (`LocalIpcEndpoint` path); no `AF_INET`/`AF_INET6`, DNS, resolver, TLS, or remote peer is referenced or
   contacted.
5. **Observation through the client.** The client opens, reads, and closes a bounded, metadata-only observation
   stream over the local endpoint and reports delivered/dropped counters; the number of records returned is bounded by
   the gateway configuration and the granted capacity.
6. **Observation of emitted traffic.** The client's observation stream observes the stimulation items the gateway
   emits on the normal route.
7. **Every allowed stimulation action.** The client submits and observes an emitted outcome for each of the four
   allowed stimulation actions — signal injection, message injection, service invocation, and bounded service
   emulation — through the accepted T027 guard, T026 journal, and T028 action path; accepted items keep persistent
   synthetic provenance.
8. **Service-emulation lease round trip.** The client acquires and releases the accepted exclusive generation-bound
   lease through the gateway.
9. **Invalid and expired sessions emit zero items.** A client submission against an invalid or expired session emits
   zero normal-route items and reports a non-success outcome.
10. **Fail-closed version rejection.** An unsupported protocol major is rejected before any operation and emits no
    item.
11. **Explicit client bounds.** Maximum message size, per-request deadline, and transport timeout are explicit client
    configuration values; an over-bound message, an over-bound deadline, or a bounded timeout is handled fail-closed
    and deterministically.
12. **Deterministic failure semantics.** Peer failure, timeout, and disconnect-after-intent map to stable
    `failed`/`expired`/`evidence-incomplete` outcomes and are never reported as success.
13. **Safe logs and public-safe evidence.** The client and its tests record only stable codes, phase, logical
    identity, size, timing, and outcome; no payload byte, permit content, secret, private address, or host path enters
    a committed file or bounded log.
14. **Generated-client contract tests.** The generated request messages round-trip through the client unchanged, an
    unknown field survives the client round trip, and the client usage carries no payload or permit secret.
15. **Additive build wiring.** One fixture executable and `t032-<kind>`-labelled test executables are added
    additively; the runtime-target inventory is unchanged (the fixture executable is not a runtime library).
16. The T032 repository-owned work products and the T032 package record.

### 2.2 Explicit exclusions (must remain absent from the T032 candidate)

No TCP listener or `AF_INET`/`AF_INET6` socket, DNS, resolver, or TLS use; no external network peer; no legacy binary,
legacy repository, or production workload execution; no reusable contract-suite abstraction (T033); no second
synthetic provider (T034); no change to the accepted T030 contract or the accepted T031 gateway sources; no
benchmark, executed sanitizer/static/Doxygen evidence, or delivery bundle (T035–T040); no dashboard, storage,
query-presentation, or export primitive; no compiled or linked gRPC runtime; no new admitted dependency; no
ambient/secret access, dynamic load, or legacy repository access; no wall-clock-dependent verdict; no production XDL
or activation-plan change; no change to any accepted predecessor path under `src/`, `tests/`, `xdl/`, or
`docs/engineering/xcom/t0{07..31}/` other than the additive `src/xverse/xcom/CMakeLists.txt` wiring and the status-only
planned→established reconciliation for the T032 fixture path; no rewrite or weakening of an accepted ADR,
requirement, contract, schema, register, target, or test; no promotion of any REF-002 SADS ID beyond its recorded
disposition; no acceptance or integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T032 |
| --- | --- | --- |
| Reusable provider/observer/stimulation-tool/gateway contract suites | T033 | allocated; T032's suites are T032-local and do not become the reusable abstraction |
| Second minimal synthetic provider; replaceability and version rejection | T034 | allocated; T032 realizes one synthetic client only |
| gRPC transport runtime linkage | deferred capability gap `T032-GAP-01` | recorded, not worked around |
| Executed sanitizer/static-analysis/Doxygen evidence, benchmarks, delivery bundle | T035–T040 | allocated |
| Independent review and user acceptance | T039/T041 | allocated; external Codex review and acceptance deferred until backlog `xcom-t030-t034-20260928` completes |

## 3. Stakeholder requirements (`T032-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T032-STK-001**: The program **shall** own one separate-process synthetic tool client that exercises the accepted
  `XCOM-XLC-002` gateway contract for observation and every allowed stimulation action through a host-protected local
  endpoint.
- **T032-STK-002**: The synthetic client **shall** run as its own process with no TCP listener, no external network
  peer, no legacy binary, and no production workload.
- **T032-STK-003**: The synthetic client **shall** require the exact validation permit, and an invalid or expired
  session **shall** emit zero items.
- **T032-STK-004**: The generated-client contract tests **shall** prove the generated message/method contract and
  preserve an unknown field across a client round trip.
- **T032-STK-005**: T032 **shall** preserve accepted intent and report maturity honestly: `XCOM-SW-GW-003` is recorded
  implemented for the conformance-client slice by T032, while T033–T041 remain allocated and the REF-002 disposition
  stays `unchanged` with an empty `promoted` list.

## 4. Software/engineering requirements (`T032-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted anchor.
"Verified" means the repository-owned check exists, is deterministic, and passes at the recorded candidate revision;
it is not a deployed-service, compatibility, or end-to-end route claim.

### 4.1 Client boundary and generated contract

- **T032-SR-001 [ubiquitous]**: The synthetic client **shall** be defined once by
  `src/xverse/xcom/fixtures/synthetic_tool.cpp` (executable `xverse_xcom_synthetic_client`), realizing the accepted
  `XCOM-XLC-002` generated message contract without introducing a competing contract, RPC definition, or
  configuration language.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-SC-011`, `XCOM-SYS-FR-032`; SC-011, FR-032; `XCOM-DU-021`,
    `XCOM-CMP-011`, `XCOM-XLC-002`.
  - Verification intent: source/interface inspection plus the client method-table case; `T32-TS-014`; CHK-03.
- **T032-SR-002 [ubiquitous]**: The client **shall** recognize all ten accepted `ToolGateway` operations by their
  exact T030 method names and **shall** fail closed if its committed client operation table differs from the generated
  `ToolGateway` service descriptor method set.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-022`, `XCOM-SYS-FR-032`; FR-022, FR-032; `XCOM-XLC-002`,
    `XCOM-DU-021`.
  - Verification intent: client operation-table/descriptor equality case; `T32-TS-014`; CHK-04.
- **T032-SR-003 [event-driven]**: When the T032 tests exercise the client, the client **shall** run as its own OS
  process launched with an explicit bounded argument vector and a scrubbed admitted environment, and **shall not**
  require an ambient value, a legacy binary, a subprocess of a production workload, or an external peer.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-SC-011`, `XCOM-SYS-FR-028`; SC-011, FR-028; `XCOM-DU-021`,
    `XCOM-CMP-011`, `XCOM-INV-15`.
  - Verification intent: separate-process launch and environment-hygiene cases; `T32-TS-001`, `T32-TS-019`; CHK-05,
    NEG-01.
- **T032-SR-004 [unwanted]**: If the client used any `AF_INET`/`AF_INET6`, DNS, resolver, TLS, or remote facility, the
  tests **shall** fail closed; the client **shall** connect only to a host-protected `AF_UNIX` local endpoint and
  **shall** expose no TCP listener.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-028`, `XCOM-SYS-FR-032`; FR-028, FR-032; `XCOM-INV-13`,
    `XCOM-XB-010`.
  - Verification intent: endpoint-family/no-TCP and forbidden-API cases; `T32-TS-015`, `T32-TS-019`; CHK-06, NEG-01.

### 4.2 Observation

- **T032-SR-005 [event-driven]**: When the client opens, reads, and closes an observation stream, the gateway
  **shall** serve at most the granted bounded number of metadata-only records through the local endpoint, and the
  client **shall** report the delivered/dropped counters on close.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-011`, `XCOM-SYS-FR-012`, `XCOM-SYS-FR-013`, `XCOM-SYS-FR-032`;
    FR-011–FR-013, FR-032; `XCOM-DU-021`, `XCOM-CMP-011`.
  - Verification intent: bounded observation open/read/close cases; `T32-TS-002`, `T32-TS-003`, `T32-TS-004`; CHK-07,
    CHK-08, CHK-09, NEG-06.
- **T032-SR-006 [event-driven]**: When the gateway emits an accepted stimulation item while the client observes, the
  client **shall** observe the emitted item as one metadata-only observation record.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-017`, `XCOM-SYS-FR-023`; FR-017, FR-023; `XCOM-DU-021`,
    `XCOM-CMP-011`.
  - Verification intent: observed-emitted-traffic case; `T32-TS-005`; CHK-10.

### 4.3 Stimulation and lease

- **T032-SR-007 [event-driven]**: When the client submits each of the four allowed stimulation actions, the gateway
  **shall** route it through the accepted T027 pre-emission guard, T026 journal, and T028 action path, the client
  **shall** observe an emitted outcome, and the accepted item **shall** carry persistent synthetic provenance.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-015`, `XCOM-SYS-FR-017`, `XCOM-SYS-FR-018`,
    `XCOM-SYS-FR-021`; FR-015, FR-017, FR-018, FR-021; `XCOM-DU-021`, `XCOM-CMP-011`, `XCOM-INV-08`.
  - Verification intent: four stimulation-action cases plus a provenance assertion; `T32-TS-006`, `T32-TS-007`,
    `T32-TS-008`, `T32-TS-009`; CHK-11, NEG-03, NEG-04.
- **T032-SR-008 [event-driven]**: When the client acquires or releases a service-emulation lease, the gateway **shall**
  delegate to the accepted T028 exclusive generation-bound lease and the client **shall** observe the resulting lease
  state.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-034`; FR-034; `XCOM-DU-021`, `XCOM-CMP-011`.
  - Verification intent: lease acquire/release round-trip case; `T32-TS-010`; CHK-12.

### 4.4 Permit, version, and failure semantics

- **T032-SR-009 [unwanted]**: If a client submission targets an invalid or expired session, the gateway **shall** emit
  zero normal-route items and the client **shall** report a non-success outcome.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-016`, `XCOM-SYS-FR-021`, `XCOM-SYS-SC-011`; FR-016, FR-021,
    SC-011; `XCOM-DU-021`, `XCOM-INV-08`.
  - Verification intent: invalid- and expired-session zero-emission cases; `T32-TS-016`, `T32-TS-017`; CHK-13, NEG-03,
    NEG-04.
- **T032-SR-010 [event-driven]**: When the client negotiates an unsupported protocol major, the gateway **shall**
  reject the session fail-closed before any other operation and emit no item.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-032`, `XCOM-SYS-FR-022`; FR-032, FR-022; `XCOM-DU-021`.
  - Verification intent: unsupported-major fail-closed case; `T32-TS-018`; CHK-14, NEG-05.
- **T032-SR-011 [ubiquitous]**: The client **shall** declare and enforce every client bound — maximum message size,
  per-request deadline, and transport timeout — as an explicit configuration value, and **no** bound **shall** be
  implicit or unbounded.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-007`, `XCOM-SYS-FR-013`, `XCOM-SYS-FR-032`; FR-007, FR-013,
    FR-032; `XCOM-DU-021`.
  - Verification intent: declared-bounds and over-bound cases; `T32-TS-020`, `T32-TS-021`, `T32-TS-022`; CHK-15,
    NEG-06.
- **T032-SR-012 [event-driven]**: When the peer fails, the transport times out, or the peer disconnects after an
  intent, the client **shall** report a stable non-success outcome (`failed`, `expired`, or `evidence-incomplete`)
  and **shall never** report an unknown outcome as success.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-010`, `XCOM-SYS-FR-021`; FR-010, FR-021; `XCOM-DU-021`.
  - Verification intent: transport-timeout and expired-session cases; `T32-TS-017`, `T32-TS-022`; CHK-16, NEG-04.

### 4.5 Evidence, safety, and governance

- **T032-SR-013 [ubiquitous]**: The client and its tests **shall** record only stable codes, phase, logical identity,
  size, timing, and outcome; committed files and bounded logs **shall not** contain a payload byte, permit content,
  secret, private address, or host path.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-027`; FR-027; `XCOM-DU-021`; Constitution VII.
  - Verification intent: usage-safety case and public-safety inspection; `T32-TS-011`; CHK-17, NEG-08.
- **T032-SR-014 [ubiquitous]**: The synthetic-client exchange **shall** be deterministic and bounded under fixed
  inputs; no verdict **shall** depend on ambient wall-clock time, randomness, or environment.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-007`, `XCOM-SYS-FR-030`; FR-007, FR-030; `XCOM-DU-021`.
  - Verification intent: repeatable separate-process case plus finite-operation inspection; `T32-TS-001`; CHK-05.
- **T032-SR-015 [ubiquitous]**: The generated-client contract tests **shall** prove that the generated request
  messages round-trip through the client unchanged and that an unknown field survives a client round trip.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-022`; FR-022; `XCOM-XLC-002`.
  - Verification intent: generated round-trip and unknown-field cases; `T32-TS-012`, `T32-TS-013`; CHK-18.
- **T032-SR-016 [ubiquitous]**: Build wiring **shall** be additive: one new fixture executable and additive
  `t032-<kind>`-labelled test executables registered in `src/xverse/xcom/CMakeLists.txt`, with any inventory change
  declared explicitly and no existing target, test name, label, command, or expected value changed.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-030`; FR-030; T012 subtree build contract.
  - Verification intent: changed-path and discovered-count inspection; CHK-19, NEG-06, NEG-10.
- **T032-SR-017 [ubiquitous]**: Because the T011 admitted envelope cannot link the gRPC runtime (`T030-GAP-02`,
  `T031-GAP-01`), the client **shall** realize the accepted generated message and method contract over the bounded,
  host-protected local-IPC framing bound 1:1 to the T030 generated method names; it **shall** add no admitted
  dependency and **shall not** claim a linked gRPC runtime. The deferred gRPC transport runtime **shall** be recorded
  as an explicit gap (`T032-GAP-01`).
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-032`, `XCOM-SYS-FR-030`; FR-032, FR-030; `XCOM-XLC-002`,
    `XCOM-DU-021`.
  - Verification intent: envelope-decision inspection and forbidden-API scan; `T32-TS-014`, `T32-TS-019`; CHK-04,
    CHK-20, NEG-07.
- **T032-SR-018 [ubiquitous]**: T032 **shall** reconcile with the T007 ownership register, the T008 register, the
  T009 architecture model, and the T010 unit design without rewriting or weakening them; **shall** keep the register
  REF-002 disposition `unchanged` with an empty `promoted` list; and **shall** record honestly that `XCOM-SW-GW-003`
  is implemented for the conformance-client slice by T032 while T033–T041 remain allocated. The planned→established
  path-status reconciliation for the now-present `src/xverse/xcom/fixtures/synthetic_tool.cpp` path is a status-only
  change.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-035`, `XCOM-SYS-FR-030`; FR-030, FR-035; Constitution VII, IX.
  - Verification intent: register validators plus the recorded-maturity inspection; CHK-21, NEG-09, NEG-10.
- **T032-SR-019 [ubiquitous]**: The T032 candidate **shall** satisfy the deterministic Phase 7 gate: the five plan
  work products and the implementation record exist; at least one `tests/` path changes; the Phase 7 runner's unit
  configure/build and `t032-`-labelled discovery pass; `git diff --check` is clean; and the T032 checkbox is marked
  complete **only** in the implementation stage.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-030`; FR-030; Constitution X.
  - Verification intent: `xcom_phase7_gate.py verify T032 <baseline>`; `git diff --check`; CHK-22, NEG-10.
- **T032-SR-020 [ubiquitous]**: T032 **shall** keep the accepted T030 contract, the accepted T031 gateway, and every
  accepted test unchanged and **shall not** implement the T033 reusable contract-suite abstraction or the T034 second
  provider; the T032 suites remain T032-local.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-030`; FR-030; T007 ownership register.
  - Verification intent: changed-path inspection plus the passing preserved suites; CHK-02, CHK-19, NEG-10.
- **T032-SR-021 [ubiquitous]**: The client source **shall** carry the Doxygen file block and public-element tags that
  the accepted `XCOM-DU-021` requires (group `xcom_gw`, file block, ownership/lifetime/thread-safety/failure tags),
  and the T032 hand-written public seam **shall** be documented; generated Protocol Buffers documentation remains
  `DOX-GAP-02`.
  - Refines: `XCOM-SW-GW-003`; anchors `XCOM-SYS-FR-029`; FR-029; `XCOM-DU-021`.
  - Verification intent: Doxygen file-block inspection; CHK-03, CHK-19.

## 5. Requirement-to-accepted-anchor traceability

| T032 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T032-STK-001 | `XCOM-SW-GW-003` | `XCOM-SYS-SC-011` | SC-011 | SC-011, VII |
| T032-STK-002 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-028` | FR-028 | II, VII |
| T032-STK-003 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-016` | FR-016 | VII |
| T032-STK-004 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-022` | FR-022 | IX |
| T032-STK-005 | Constitution VII/IX; ADR-0020 | `XCOM-SYS-FR-035` | FR-035 | VII, IX |
| T032-SR-001 | `XCOM-SW-GW-003` | `XCOM-SYS-SC-011/FR-032` | SC-011, FR-032 | VII, IX |
| T032-SR-002 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-022/032` | FR-022, FR-032 | IX |
| T032-SR-003 | `XCOM-SW-GW-003` | `XCOM-SYS-SC-011/FR-028` | SC-011, FR-028 | II, VII |
| T032-SR-004 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-028/032` | FR-028, FR-032 | II, VII |
| T032-SR-005 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-011/012/013/032` | FR-011–FR-013, FR-032 | IX |
| T032-SR-006 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-017/023` | FR-017, FR-023 | IX |
| T032-SR-007 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-015/017/018/021` | FR-015, FR-017, FR-018, FR-021 | IX |
| T032-SR-008 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-034` | FR-034 | IX |
| T032-SR-009 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-016/021` | FR-016, FR-021 | VII, IX |
| T032-SR-010 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-032/022` | FR-032, FR-022 | IX |
| T032-SR-011 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-007/013/032` | FR-007, FR-013, FR-032 | IX |
| T032-SR-012 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-010/021` | FR-010, FR-021 | IX |
| T032-SR-013 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-027` | FR-027 | VII |
| T032-SR-014 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-007/030` | FR-007, FR-030 | IX |
| T032-SR-015 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-022` | FR-022 | IX |
| T032-SR-016 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-030` | FR-030 | VII, X |
| T032-SR-017 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-032/030` | FR-032, FR-030 | IX, X |
| T032-SR-018 | Constitution; ADR-0020 | `XCOM-SYS-FR-030/035` | FR-030, FR-035 | VII, IX |
| T032-SR-019 | ADR-0020 | `XCOM-SYS-FR-030` | FR-030 | X |
| T032-SR-020 | ADR-0020 | `XCOM-SYS-FR-030` | FR-030 | VII, IX |
| T032-SR-021 | `XCOM-SW-GW-003` | `XCOM-SYS-FR-029` | FR-029 | VII |

`XCOM-SW-GW-003` is an accepted capability-007 software requirement
(`docs/engineering/xcom/t008/requirements-register.{json,md}`). It is accepted text; T032 satisfies it for the
conformance-client slice and does not rewrite it. The register row is not changed and no register maturity is promoted
by the plan stage; the per-task maturity projection is recorded in the T032 work products, following the T030/T031
precedent.

### 5.1 Stakeholder-to-software refinement and validation coverage

Every accepted T032 software requirement refines at least one `T032-STK-###` stakeholder requirement through an
explicit `refines` trace link in `engineering/trace/links.json`, following the T030/T031 precedent. The refinement
links below were added by the T032 trace-repair successor recorded in `implementation.md` §13; no requirement text,
system anchor, component, unit, test, or validation case is changed, and no trace checker or accepted measure is
weakened.

| Stakeholder | Refining software requirements (link ID) | Statement-level justification |
| --- | --- | --- |
| `T032-STK-001` | `T032-SR-001` (`T032-L-0258`), `T032-SR-003` (`-0260`), `T032-SR-004` (`-0262`), `T032-SR-005` (`-0264`), `T032-SR-006` (`-0265`), `T032-SR-007` (`-0266`), `T032-SR-008` (`-0268`), `T032-SR-010` (`-0270`), `T032-SR-011` (`-0271`), `T032-SR-012` (`-0272`), `T032-SR-013` (`-0273`), `T032-SR-014` (`-0274`), `T032-SR-017` (`-0277`), `T032-SR-021` (`-0281`) | The client is defined once, runs as its own process, connects only to the host-protected local endpoint, opens/serves bounded observation, observes emitted traffic, performs every allowed stimulation action and the lease round trip, negotiates/rejects versions fail-closed, enforces explicit bounds, reports deterministic failure outcomes, keeps safe evidence, is deterministic, realizes `XCOM-XLC-002`, and is documented. |
| `T032-STK-002` | `T032-SR-003` (`T032-L-0261`), `T032-SR-004` (`-0263`) | The separate-process launch with a scrubbed admitted environment and no legacy/production/external peer, and the `AF_UNIX`-only connect with no TCP listener/DNS/TLS, directly refine the no-TCP/no-external/no-legacy/no-production clause. |
| `T032-STK-003` | `T032-SR-007` (`T032-L-0267`), `T032-SR-009` (`-0269`) | Stimulation routes through the accepted T027 pre-emission guard (the permit-enforcement inspection behind `NEG-03`), and an invalid or expired session emits zero normal-route items with a non-success outcome. |
| `T032-STK-004` | `T032-SR-002` (`T032-L-0259`), `T032-SR-015` (`-0275`) | The committed client operation table is asserted equal to the generated `ToolGateway` service descriptor method set, and the generated request messages round-trip with an unknown field preserved. |
| `T032-STK-005` | `T032-SR-016` (`T032-L-0276`), `T032-SR-018` (`-0278`), `T032-SR-019` (`-0279`), `T032-SR-020` (`-0280`) | Additive build wiring, the registers/REF-002/recorded-maturity reconciliation (`XCOM-SW-GW-003` implemented; T033–T041 allocated; REF-002 `unchanged` with an empty `promoted` list), the deterministic Phase 7 gate, and preserving the accepted T030/T031 material directly refine the "preserve accepted intent and report maturity honestly" clause. |

**Validation coverage.** `T032-VS-ACCUMULATED` validates `T032-SR-001`…`-021` and names the 22 `t032-` cases that
the trusted validation measure `engineering/verification/measures/validation.json` selects and executes. Because every
`T032-SR-###` is a validated refining requirement of its stakeholder(s), the traceability matrix reports each
`T032-STK-###` row with both its refining software requirements and the executed `T032-VS-ACCUMULATED` scenario; no
stakeholder row is left without a refinement or a validation link. The governance clause of `T032-STK-005` is checked
by the named register/maturity inspections (`CHK-21`, `NEG-09`, `NEG-10`) recorded in the verification plan, following
the accepted T030/T031 treatment of governance stakeholder requirements.

## 6. REF-002 disposition

T032 owns no REF-002 SADS ID and promotes none. It contributes separate-process conformance evidence toward the
allocated communication IDs already exercised by the communication boundary: `XVE-SYS-0141` is **deferred**
("protocol/provider capabilities") in the accepted allocation, and `XVE-SYS-0142`–`0158` retain their accepted
dispositions. The separate-process client is recorded as a **partial contribution** to the deferred target and is
**not** promoted; nothing in the `promoted` list changes. The capability `ref002.disposition` stays `unchanged`
(T032-SR-018). No allocated, deferred, architectural-target, or superseded SADS requirement is reported as
implemented.

## 7. Affected paths

### 7.1 Paths the T032 candidate changes (implementation stage)

| Path | Change | Notes |
| --- | --- | --- |
| `src/xverse/xcom/fixtures/synthetic_tool.cpp` | add | separate-process synthetic client realizing `XCOM-DU-021`/`XCOM-CMP-011` over the accepted local-IPC framing and generated messages |
| `src/xverse/xcom/CMakeLists.txt` | edit (additive) | add the `xverse_xcom_synthetic_client` fixture executable and the `t032-<kind>` test executables; no existing target/label/value changes |
| `tests/xcom/tool_gateway/synthetic_client_support.hpp` | add | bounded test-local server harness, separate-process launcher, and result parser (payload-free) |
| `tests/xcom/tool_gateway/synthetic_client_observation_tests.cpp` | add | `T32-TS-001`…`T32-TS-005` |
| `tests/xcom/tool_gateway/synthetic_client_stimulation_tests.cpp` | add | `T32-TS-006`…`T32-TS-010` |
| `tests/xcom/tool_gateway/synthetic_client_contract_tests.cpp` | add | `T32-TS-011`…`T32-TS-014` |
| `tests/xcom/tool_gateway/synthetic_client_negative_tests.cpp` | add | `T32-TS-015`…`T32-TS-019` |
| `tests/xcom/tool_gateway/synthetic_client_bounds_tests.cpp` | add | `T32-TS-020`…`T32-TS-022` |
| `docs/engineering/xcom/t009/architecture-model.{json,md}` | edit | `XCOM-CMP-011` planned→established path status only (status field) |
| `docs/engineering/xcom/t010/unit-design.{json,md}` | edit | `XCOM-DU-021` planned→established path status only (status field) |
| `docs/engineering/xcom/t010/design-units.md` | edit | `XCOM-DU-021` planned→established path status only (status field) |
| `engineering/project.json` | edit | current task T032 and accepted baseline `e6197c67868213ffb6523d8bf62ed4c2c4e3b0af` |
| `engineering/requirements/T032-STK-00{1..5}.json`, `T032-SR-0{01..21}.json` | add | current-task requirement records |
| `engineering/architecture/components/T032-SR-0{01..21}-CMP.json` | add | current-task component allocations |
| `engineering/unit-specifications/T032-SR-0{01..21}-U.json` | add | current-task unit specifications |
| `engineering/validation/scenarios/T032-VS-ACCUMULATED.json` | add | current-task validation scenario |
| `engineering/trace/links.json` | edit (implementation) | additive T032 trace links and the inherited digest refresh |
| `engineering/verification/measures/{unit,integration,validation}.json` | edit (implementation) | refreshed to the discovered T032 cases |
| `engineering/stage-results/*.json` | edit (implementation) | inherited artifact-digest refresh when `src/xverse/xcom/CMakeLists.txt` changes |
| `docs/engineering/xcom/t032/requirements.md` | add | this document |
| `docs/engineering/xcom/t032/architecture.md` | add | T032 architecture |
| `docs/engineering/xcom/t032/detailed-design.md` | add | T032 detailed design |
| `docs/engineering/xcom/t032/unit-specifications.md` | add | T032 unit specifications |
| `docs/engineering/xcom/t032/verification-plan.md` | add | T032 verification plan |
| `docs/engineering/xcom/t032/implementation.md` | add | implementation-stage record |
| `docs/engineering/xcom/t032/internal-review.json` | add | internal-review record |
| `reports/review-index.md` | edit | T032 candidate section appended |
| `specs/007-xcom-core/tasks.md` | edit | one-line T032 checkbox, **implementation stage only** |
| `reports/xcom-queue/t032-package.json` | add | implementation-stage package record |

### 7.2 Consumed read-only (not changed by T032)

`proto/xverse/xcom/v1/tool_gateway.proto`; `cmake/XComOfflineDependencies.cmake`; `cmake/XComWarnings.cmake`; the
root `CMakeLists.txt`; `scripts/**`; `xdl/**`; `src/xverse_xdl/**`; all accepted `src/xverse/xcom/**` runtime
sources, headers, and library targets (including `tool_gateway.hpp`/`.cpp`) other than the additive build wiring;
every accepted test under `tests/xcom/**` other than the new T032 suites; `docs/engineering/xcom/task-ownership.*`;
`docs/engineering/xcom/t00{7,8,9,10}/**` other than the status-only path reconciliation;
`docs/engineering/xcom/t0{01..31}/**`; `docs/engineering/xcom/build-environment.md`;
`docs/engineering/xcom/dependency-lock.md`; and `specs/007-xcom-core/**` (other than the T032 checkbox).

### 7.3 Explicitly not implemented by T032

The reusable provider/observer/stimulation-tool/gateway contract suites (T033), the second synthetic provider (T034),
the benchmark/sanitizer/static/Doxygen/delivery tasks (T035–T040), the gRPC transport runtime linkage
(`T032-GAP-01`), the executed gRPC server, and any change to the accepted T030 contract or T031 gateway. External
Codex review and user acceptance remain T039/T041 and are deferred until the ordered backlog
`xcom-t030-t034-20260928` completes.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- **T032-GAP-01 — gRPC transport runtime deferred.** The T011 admitted envelope cannot link the gRPC runtime
  (`T030-GAP-02`, `T031-GAP-01`). T032 realizes the accepted generated message and method contract over the bounded,
  host-protected `AF_UNIX` local-IPC framing bound 1:1 to the T030 generated method names and records the deferred
  gRPC transport runtime. No new dependency is added and no gRPC-runtime link is claimed.
- **T032-GAP-02 — owned separate-process proof only.** T032 proves conformance with an owned, self-built
  separate-process synthetic client over an owned local endpoint. It makes no remote-tool, distributed-authorization,
  or third-party-client compatibility claim.
- **T032-GAP-03 — no reusable abstraction.** The T032 suites are T032-local and are not the T033 reusable contract
  suite; the client is one implementation and not the T034 replaceability proof.
- **T032-GAP-04 — generated-code documentation.** The generated Protocol Buffers message/stub documentation policy
  remains `DOX-GAP-02`; T032 adds Doxygen documentation for its hand-written client seam only.
- **T032-GAP-05 — no deployed-service or compatibility claim.** The client is a bounded prototype validated with
  owned local fixtures; it makes no production-readiness or parity claim.

### 8.2 Gaps with owning tasks

| Gap | Owner |
| --- | --- |
| Reusable contract suites | T033 |
| Second minimal synthetic provider; replaceability and version rejection | T034 |
| gRPC transport runtime envelope | deferred capability gap `T032-GAP-01` |
| Executed sanitizer/static/Doxygen/benchmark and delivery bundle | T035–T040 |
| Independent review and user acceptance | T039/T041 |

### 8.3 Open items

- **T032-OPEN-01 — inherited provenance refresh.** Editing `src/xverse/xcom/CMakeLists.txt` invalidates the inherited
  `implemented_by` target digests in `engineering/trace/links.json` and the declared
  `links.json`/`CMakeLists.txt` digests in `engineering/stage-results/*.json`. Following the T020/T026–T031 precedent,
  the implementation stage refreshes those inherited digests; no requirement, link identity, relation, or stage
  result changes.
- **T032-OPEN-02 — planned→established path reconciliation.** Creating
  `src/xverse/xcom/fixtures/synthetic_tool.cpp` makes one accepted T009/T010 planned path present in the tree, so the
  T009/T010 validators require the planned→established status transition (status field only). Unit `XCOM-DU-021`
  maturity stays `allocated`.
- **T032-OPEN-03 — separate-process transport path.** The T032 suites need a bounded way to launch the client and
  hand it the local socket path: the fixture executable path and the bounded build-tree scratch directory are supplied
  as build-time compile definitions (the T026/T031 precedent); neither path is printed into public evidence.
- **T032-OPEN-04 — inventory unchanged.** The synthetic client is a fixture executable, not a runtime library, so
  `XVERSE_XCOM_RUNTIME_TARGETS` is unchanged; only additive executable/test registration is introduced.

## 9. Definition of done (requirements view)

T032 is done for a candidate revision when: every §4 requirement has at least one named check; the separate-process
synthetic client runs as its own process over a host-protected no-TCP local endpoint; observation and every allowed
stimulation action complete through the client; invalid/expired sessions emit zero items; the generated message
contract round-trips and preserves an unknown field; the explicit client bounds and deterministic failure semantics
are proven at the recorded candidate revision; `XCOM-SW-GW-003` is recorded implemented for the conformance-client
slice by T032 while T033–T041 remain allocated; the gRPC transport gap is recorded and no new dependency is added; no
accepted requirement, test, ADR, contract, register, or predecessor byte is weakened; the register validators pass
with REF-002 unchanged and nothing promoted; the deterministic Phase 7 gate passes; and a separate DeepSeek internal
review records its findings before any repair. This does not constitute user acceptance, which remains T041.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary checks |
| --- | --- |
| T032-STK-001 | CHK-01, CHK-03, CHK-05, CHK-22 |
| T032-STK-002 | CHK-05, CHK-06 |
| T032-STK-003 | CHK-13 |
| T032-STK-004 | CHK-18 |
| T032-STK-005 | CHK-21, CHK-22 |
| T032-SR-001 | CHK-03, CHK-04 |
| T032-SR-002 | CHK-04 |
| T032-SR-003 | CHK-05, CHK-20 |
| T032-SR-004 | CHK-06, CHK-20 |
| T032-SR-005 | CHK-07, CHK-08, CHK-09 |
| T032-SR-006 | CHK-10 |
| T032-SR-007 | CHK-11 |
| T032-SR-008 | CHK-12 |
| T032-SR-009 | CHK-13 |
| T032-SR-010 | CHK-14 |
| T032-SR-011 | CHK-15 |
| T032-SR-012 | CHK-16 |
| T032-SR-013 | CHK-17 |
| T032-SR-014 | CHK-05 |
| T032-SR-015 | CHK-18 |
| T032-SR-016 | CHK-19 |
| T032-SR-017 | CHK-20 |
| T032-SR-018 | CHK-21 |
| T032-SR-019 | CHK-22 |
| T032-SR-020 | CHK-02, CHK-19 |
| T032-SR-021 | CHK-03 |
