# T031 Requirements — Bounded Local-IPC-Only Tool Gateway

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T031 (capability 007, slice `T-CORE`/GW) |
| Task title | Implement a local-IPC-only gateway with no TCP listener, bounded messages/streams, deadlines, flow control, safe logs, and disconnect cleanup |
| Stage / role | plan → requirements |
| Revision | 1 (local-IPC gateway session slice) |
| Baseline revision | `4dded2317f895978cce0331ae88e34ac28b3a609` |
| Authorization | capability 007 accepted design and bounded implementation authorization (`ACC006`, `ACC010`, `ACC011`, `ACC014`, `ACC015`); `ADR-0016` (subsystem naming); `ADR-0018` (platform-first); `ADR-0019` (X-COM observation/stimulation boundary); `ADR-0020` (repository-owned work products and exact-candidate evidence) |
| Owning slice | `T-CORE` (T007 ownership register); T031 is the gateway-session (`GW`) task that owns the bounded local-IPC server |
| Predecessors | T030 accepted versioned `XCOM-XLC-002` contract (`proto/xverse/xcom/v1/tool_gateway.proto`, generated message library `xverse_xcom_tool_gateway_proto`); T025–T029 accepted validation-permit, journal, guard, action-path, and lease contracts (read-only); T021–T024 accepted bounded observation boundary (read-only); T011 admitted offline envelope (`protoc` 3.12.4, `grpc_cpp_plugin` 1.30.2, `libprotobuf.a`); T012 subtree CMake/CTest contract |
| Successor tasks | T032 (separate-process synthetic client + generated-client tests), T033 (reusable contract suites), T034 (second synthetic provider), T035–T041 (evidence, review, acceptance) |
| Consumed registers | `docs/engineering/xcom/task-ownership.{json,md}` (`T-CORE` slice evidence names; T031 exclusive paths `docs/engineering/xcom/t031/`, `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp`, `src/xverse/xcom/src/tool_gateway.cpp`, `reports/xcom-queue/t031-package.json`); `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-SW-GW-002` owning row); `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-010`, `XCOM-XB-008`, `XCOM-XB-010`, `XCOM-XLC-002`, `XCOM-INV-13`); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-020` local-IPC-only gateway session) |
| Classification | Public-safe engineering work product |

This document is a repository-owned work product (ADR-0020). It is written **before** any production change and
does not implement, accept, or integrate the candidate. The T031 task entry in `specs/007-xcom-core/tasks.md` is the
authorized scope:

> T031 — Implement a local-IPC-only gateway with no TCP listener, bounded messages/streams, deadlines, flow control,
> safe logs, and disconnect cleanup.

It also realizes the accepted external-tool contract statement in `specs/007-xcom-core/contracts/tool-gateway.md`
("The first external-tool proof uses a versioned gRPC service with Protocol Buffers on a host-protected local IPC
endpoint. The server must not bind a TCP address.") and success criterion `SC-011` at the gateway boundary.

### 1.1 Authority statement

T031 owns the **bounded local-IPC-only gateway session**. It implements one accepted software requirement from
`docs/engineering/xcom/t008/requirements-register.{json,md}` that the register allocates to T031:

- `XCOM-SW-GW-002` "Local-IPC-only bounded gateway" — "Expose one local-only out-of-process gateway with no TCP
  listener, host-protected IPC, bounded messages/streams, deadlines, flow control, safe logs, and the exact permit."
  (refines `XCOM-SYS-FR-032`, spec `FR-032`). T031 records this requirement **implemented** for the gateway slice by
  the T031 per-task projection; the register row is not edited (T026–T030 precedent).

It consumes the accepted T030 contract and the accepted in-process boundaries read-only, and it contributes the
server capability that the still-allocated successor requirements depend on:

- `XCOM-SW-GW-003` "Separate-process synthetic client conformance" (`XCOM-SYS-SC-011`, `SC-011`) — **T032**; T031
  provides the endpoint and operation surface the client exercises but makes no separate-process claim.

T031 realizes the accepted design unit `XCOM-DU-020` "Local-IPC-only gateway session" (family `GW`, kind `edge`,
language `cpp`, scope `first-proof`, owning task T031), the accepted component `XCOM-CMP-010` "Local tool gateway",
the accepted external-rpc contract `XCOM-XLC-002`, and the accepted IPC boundaries `XCOM-XB-008`
(`XCOM-CMP-010 → XCOM-CMP-012`, `protobuf → external`, bidirectional, validation-permit required) and `XCOM-XB-010`
(`XCOM-CMP-011 → XCOM-CMP-010`, `protobuf → cpp`, bidirectional, validation-permit required).

**Recorded contract decision (`T031-DD-01`, `T031-SR-021`).** T030 recorded `T030-GAP-02`: the T011 admitted envelope
supplies the gRPC *generation* tools and the gRPC shared objects but **not** the gRPC runtime transitive libraries
(for example `libcares.so.2`), so a standalone gRPC++ link fails closed. T030 explicitly delegated "completing the
gRPC runtime envelope" to T031 as T031's own recorded decision. T031 records that decision rather than guessing:
T031 realizes the accepted `XCOM-XLC-002` **message and method contract** (the T030-generated Protocol Buffers
messages and the ten `ToolGateway` method names) over a **bounded, host-protected AF_UNIX local-IPC framing**. It
adds no admitted dependency and does not pretend a gRPC runtime is linked. The gRPC transport runtime remains an
explicit deferred gap (`T031-GAP-01`), and the framing is bound 1:1 to the T030 method names so it introduces no
competing interface or configuration language.

**Gateway-only boundary.** T031 authors the gateway session, its bounded local-IPC endpoint, its deadline/flow-control
mechanics, its disconnect/expiry cleanup, and its safe log boundary, plus the T031 tests. It authors no separate
process, no synthetic client, no reusable provider/observer/stimulation-tool/gateway contract suite, no second
provider, and no benchmark/sanitizer/static/Doxygen/delivery bundle. Those remain T032–T040. The separate-process
client and the no-TCP-listener *separate-process* demonstration are T032 (`SC-011`); T031 proves only the
gateway-side absence of a TCP listener.

It does **not** redesign the accepted architecture, change a functional requirement, success criterion, ADR, schema,
XDL profile, or contract; modify any accepted predecessor byte under `src/`, `tests/`, `xdl/`, or
`docs/engineering/xcom/t0{07..30}/`; implement the separate-process client or reusable suites (T032/T033); add an
admitted dependency; weaken `T030-SR-*` or any accepted test; or accept or integrate any candidate.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, plan, contracts, data model, the
T007 ownership register, the T008 register, the T009 architecture model, the T010 unit design, the constitution, or
an accepted ADR is resolved in favour of the accepted source. A material gap is reported rather than guessed.
Unresolved items are recorded in §8.

## 2. Scope

### 2.1 In scope (bounded T031)

1. **One gateway production interface.** Author `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp` and
   `src/xverse/xcom/src/tool_gateway.cpp` realizing the accepted `XCOM-XLC-002` message and method contract. No
   competing contract, configuration language, or RPC definition is introduced.
2. **Complete operation surface.** Realize all ten accepted `ToolGateway` operations — `QueryVersion`,
   `OpenObservation`, `ReadObservations`, `CloseObservation`, `ArmSession`, `RevokeSession`, `SubmitStimulation`,
   `AcquireLease`, `ReleaseLease`, `QuerySession` — by their exact T030 method names, delegating to the accepted
   in-process T021–T029 contracts.
3. **Fail-closed version negotiation.** A production compatibility predicate rejects an unsupported protocol major
   before any other operation and accepts a higher minor additively.
4. **Exact permit enforcement.** Arm/revoke and every stimulation/lease operation consume the accepted T025 permit
   and session lifecycle; no gateway field, framing element, or local-IPC access bypasses the permit.
5. **Explicit bounds.** Maximum message size, maximum concurrent sessions and streams, maximum pending requests,
   maximum observation records, and maximum payload bytes are explicit gateway-configuration fields; an over-bound
   message, stream, queue, or payload is rejected fail-closed before allocation or emission.
6. **Per-request deadlines.** Every unary request carries a bounded deadline enforced against the accepted T025 time
   authority; an overdue request returns a deterministic diagnostic and emits no item.
7. **Bounded flow control.** A bounded per-session in-flight queue and request rate; saturation rejects
   deterministically, is visible in counters, cannot grow memory without bound, and never blocks the normal data
   plane without bound.
8. **Local IPC only, no TCP listener.** The endpoint is an `AF_UNIX` local socket (or an in-process bounded channel);
   no `AF_INET`/`AF_INET6`, DNS, or TLS facility is referenced or bound; a source and runtime check fails closed.
9. **Host-protected endpoint.** The local socket lives in a restricted directory and carries restrictive file
   permissions; account/socket-file boundaries restrict access, and transport access never authorizes stimulation.
10. **Deterministic disconnect and expiry cleanup.** On peer disconnect or session idle timeout, observation
    handles close, validation-owned resources drain, revoke, release, or quarantine per durable state, and pending
    requests end explicit (`evidence-incomplete`/`failed`); an unknown outcome is never reported as success.
11. **Safe logs.** A bounded structured log boundary records only stable codes, phase, logical identity, size, and
    timing; payload bytes, permit contents, and unrestricted content are never logged.
12. **Bounded session outcome/counter query.** Bounded counters, including an explicit evidence-incomplete count.
13. **Additive build wiring and generated-contract-compatible framing.** One generated-message library is reused;
    one new gateway runtime library and `t031-<kind>`-labelled test executables are added additively; the framing
    method table is pinned to the T030 descriptor method set.
14. The T031 repository-owned work products and the T031 package record.

### 2.2 Explicit exclusions (must remain absent from the T031 candidate)

No TCP listener or `AF_INET`/`AF_INET6` socket, DNS, resolver, or TLS use; no external network peer; no separate
process, subprocess, or synthetic client (T032); no reusable contract-suite abstraction (T033); no second synthetic
provider (T034); no benchmark, executed sanitizer/static/Doxygen evidence, or delivery bundle (T035–T040); no
dashboard, storage, query-presentation, or export primitive; no compiled or linked gRPC runtime; no new admitted
dependency; no ambient/secret access, dynamic load, or legacy repository/binary access; no wall-clock-dependent
verdict; no production XDL or activation-plan change; no change to any accepted predecessor path under `src/`,
`tests/`, `xdl/`, or `docs/engineering/xcom/t0{07..30}/` other than the additive `src/xverse/xcom/CMakeLists.txt`
wiring; no rewrite or weakening of an accepted ADR, requirement, contract, schema, register, target, or test; no
promotion of any REF-002 SADS ID beyond its recorded disposition; no acceptance or integration of the candidate.

### 2.3 Delegated to other tasks (not implemented or decided here)

| Area | Owner | Disposition in T031 |
| --- | --- | --- |
| Separate-process synthetic client and generated-client contract tests | T032 | allocated; T031 provides the endpoint and operation surface |
| Reusable provider/observer/stimulation-tool/gateway contract suites | T033 | allocated |
| Second minimal synthetic provider; replaceability and version rejection | T034 | allocated; T031 realizes the production version predicate but adds no second provider |
| gRPC transport runtime linkage | deferred capability gap `T031-GAP-01` | recorded, not worked around; owned decision below |
| Executed sanitizer/static-analysis/Doxygen evidence, benchmarks, delivery bundle | T035–T040 | allocated |
| Independent review and user acceptance | T039/T041 | allocated; external Codex review and acceptance deferred until backlog `xcom-t030-t034-20260928` completes |

## 3. Stakeholder requirements (`T031-STK-###`)

Stakeholder requirements state the outcome the program needs. `shall`/`MUST` phrasing is normative.

- **T031-STK-001**: The program **shall** own one bounded local-IPC-only out-of-process tool gateway that serves the
  accepted `XCOM-XLC-002` message and method contract with no TCP listener and host-protected local IPC.
- **T031-STK-002**: The gateway **shall** require the exact validation permit for every session, stimulation, and
  lease operation; local transport access **shall** never substitute for authorization.
- **T031-STK-003**: The gateway **shall** enforce bounded messages and streams, per-request deadlines, and bounded
  flow control without unbounded memory growth and without unbounded blocking of the normal data plane.
- **T031-STK-004**: The gateway **shall** perform deterministic disconnect and expiry cleanup and **shall** log only
  safe identities, codes, sizes, timing, and outcomes.
- **T031-STK-005**: T031 **shall** preserve accepted intent and report maturity honestly: `XCOM-SW-GW-002` is
  recorded implemented for the gateway slice by T031, while `XCOM-SW-GW-003`/T032 and T033–T041 remain allocated and
  the REF-002 disposition stays `unchanged` with an empty `promoted` list.

## 4. Software/engineering requirements (`T031-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to an accepted anchor.
"Verified" means the repository-owned test or inspection exists, is deterministic, and passes at the recorded
candidate revision; it is not a deployed-service, separate-process, compatibility, or end-to-end route claim.

### 4.1 Gateway interface and operation surface

- **T031-SR-001 [ubiquitous]**: The gateway **shall** be defined once by
  `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp` and `src/xverse/xcom/src/tool_gateway.cpp`, realizing the
  accepted `XCOM-XLC-002` message contract without introducing a competing contract, RPC definition, or
  configuration language.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-032`; FR-032; `XCOM-DU-020`, `XCOM-CMP-010`, `XCOM-XLC-002`.
  - Verification intent: source/interface inspection; `T31-TS-003`; CHK-01, CHK-03.
- **T031-SR-002 [ubiquitous]**: The gateway **shall** recognize all ten accepted `ToolGateway` operations by their
  exact T030 method names and **shall** fail closed if its committed operation table differs from the T030
  descriptor method set.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-022`, `XCOM-SYS-FR-032`; FR-022, FR-032; `XCOM-XLC-002`,
    `XCOM-DU-019`, `XCOM-DU-020`.
  - Verification intent: operation-table/descriptor equality test; `T31-TS-003`; CHK-04.

### 4.2 Version, permit, and bounds

- **T031-SR-003 [event-driven]**: When a tool negotiates the protocol, the gateway **shall** apply a production
  compatibility predicate that accepts the supported major (and a higher minor additively) and rejects any other
  major fail-closed before any other operation executes.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-032`, `XCOM-SYS-FR-022`; FR-032, FR-022; `XCOM-DU-020`;
    closes the production half of `T030-GAP-03`.
  - Verification intent: version-negotiation tests; `T31-TS-001`, `T31-TS-002`, `T31-TS-020`; CHK-05, NEG-05.
- **T031-SR-004 [event-driven]**: When a tool arms, revokes, submits, or acquires against a session, the gateway
  **shall** require the exact accepted T025 permit and session identity; no field, framing element, or local-IPC
  access **shall** bypass the permit, and an unauthorized, expired, or mismatched request **shall** be rejected with
  no emitted normal-route item.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-016`, `XCOM-SYS-FR-032`; FR-016, FR-032; `XCOM-INV-08`,
    `XCOM-XB-008`, `XCOM-XB-010`.
  - Verification intent: permit-enforcement tests; `T31-TS-004`, `T31-TS-019`, `T31-TS-021`; CHK-06, NEG-03.
- **T031-SR-005 [ubiquitous]**: The gateway **shall** declare and enforce every bound — maximum message size,
  maximum concurrent sessions and streams, maximum pending requests, maximum observation records, and maximum
  payload bytes — as an explicit configuration value; **no** bound **shall** be implicit or unbounded, and an
  over-bound message, stream, queue, or payload **shall** be rejected before allocation or emission.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-007`, `XCOM-SYS-FR-013`, `XCOM-SYS-FR-032`; FR-007, FR-013,
    FR-032; `XCOM-DU-020`.
  - Verification intent: declared-bounds and over-bound tests; `T31-TS-007`, `T31-TS-018`, `T31-TS-010`; CHK-07,
    CHK-12, NEG-06.

### 4.3 Deadlines and flow control

- **T031-SR-006 [event-driven]**: When a unary request arrives, the gateway **shall** enforce its declared deadline
  against the accepted T025 time authority (not an ambient wall clock); an overdue request **shall** return a
  deterministic diagnostic and emit no item.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-007`, `XCOM-SYS-FR-020`, `XCOM-SYS-FR-032`; FR-007, FR-020,
    FR-032; `XCOM-DU-020`.
  - Verification intent: deadline-enforcement test; `T31-TS-008`; CHK-08, NEG-06.
- **T031-SR-007 [unwanted]**: If a session's bounded in-flight queue or request rate is exhausted, the gateway
  **shall** reject deterministically, record a visible counter, grow no unbounded memory, and **shall not** block
  the normal data plane without bound.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-007`, `XCOM-SYS-FR-013`, `XCOM-SYS-FR-032`; FR-007, FR-013,
    FR-032; `XCOM-DU-020`, `XCOM-INV-06`.
  - Verification intent: flow-control and observation-queue bound tests; `T31-TS-009`, `T31-TS-010`; CHK-09, CHK-12.

### 4.4 Local IPC, host protection, and observation

- **T031-SR-008 [unwanted]**: If the gateway endpoint used any `AF_INET`/`AF_INET6`, DNS, resolver, or TLS
  facility, the tests **shall** fail closed; the gateway **shall** expose only host-protected local IPC
  (`AF_UNIX`/`socketpair`) and **shall** bind no TCP address.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-028`, `XCOM-SYS-FR-032`; FR-028, FR-032; `XCOM-INV-13`,
    `XCOM-XB-008`.
  - Verification intent: endpoint-family, no-TCP, and forbidden-API tests; `T31-TS-015`, `T31-TS-016`,
    `T31-TS-022`; CHK-10, NEG-01.
- **T031-SR-009 [ubiquitous]**: The gateway endpoint **shall** be host-protected: a restricted local directory and
  restrictive socket-file permissions **shall** bound peer access, and transport access **shall** confer no
  stimulation authorization.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-026`, `XCOM-SYS-FR-032`; FR-026, FR-032; `XCOM-INV-08`,
    `XCOM-INV-13`.
  - Verification intent: endpoint-permission and transport-not-authorization tests; `T31-TS-017`, `T31-TS-021`;
    CHK-11, NEG-03.
- **T031-SR-010 [event-driven]**: When a tool opens, reads, or closes an observation stream, the gateway **shall**
  use the accepted bounded observation boundary, return at most the granted number of metadata-only records before
  the deadline, and return delivered and dropped counters on close.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-011`, `XCOM-SYS-FR-012`, `XCOM-SYS-FR-013`,
    `XCOM-SYS-FR-032`; FR-011, FR-012, FR-013, FR-032; `XCOM-INV-06`, `XCOM-DU-020`.
  - Verification intent: observation-stream bound test; `T31-TS-010`, `T31-TS-011`; CHK-12, CHK-13.

### 4.5 Stimulation, lease, and cleanup

- **T031-SR-011 [event-driven]**: When a tool submits a stimulation action, the gateway **shall** route all four
  allowed actions through the accepted T027 pre-emission guard, T026 journal, and T028 action path; an accepted item
  **shall** carry persistent synthetic provenance, and a rejected or failed request **shall** emit zero normal-route
  items.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-015`, `XCOM-SYS-FR-017`, `XCOM-SYS-FR-018`,
    `XCOM-SYS-FR-021`; FR-015, FR-017, FR-018, FR-021; `XCOM-INV-03`.
  - Verification intent: stimulation submission and rejection tests; `T31-TS-008`, `T31-TS-018`, `T31-TS-019`;
    CHK-14, NEG-03, NEG-04.
- **T031-SR-012 [event-driven]**: When a tool acquires or releases a service-emulation lease, the gateway **shall**
  delegate to the accepted T028 exclusive generation-bound lease, and conflict, expiry, or disconnect **shall**
  release or quarantine the lease without ambiguous ownership.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-034`; FR-034; `XCOM-DU-020`.
  - Verification intent: lease acquire/release and cleanup tests; `T31-TS-012`, `T31-TS-021`; CHK-15, NEG-03.
- **T031-SR-013 [event-driven]**: When a peer disconnects or a session reaches its idle timeout, the gateway
  **shall** close its observation handles and drain, revoke, release, or quarantine its validation-owned resources
  according to durable state; a pending request **shall** end explicit (`evidence-incomplete` or `failed`), and an
  unknown outcome **shall never** be reported as success.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-021`, `XCOM-SYS-FR-032`; FR-010, FR-021, FR-032;
    `XCOM-DU-020`.
  - Verification intent: disconnect and idle-timeout cleanup tests; `T31-TS-011`, `T31-TS-012`, `T31-TS-013`,
    `T31-TS-014`; CHK-16, NEG-04.

### 4.6 Logging, query, determinism, and build

- **T031-SR-014 [ubiquitous]**: The gateway **shall** expose a bounded structured log boundary that records only
  stable codes, phase, logical identity, size, and timing; it **shall not** log payload bytes, permit contents, or
  unrestricted content.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-027`, `XCOM-SYS-FR-032`; FR-027, FR-032; `XCOM-DU-020`.
  - Verification intent: payload-free and permit-free log tests; `T31-TS-023`, `T31-TS-024`; CHK-17, NEG-08.
- **T031-SR-015 [ubiquitous]**: The gateway **shall** expose bounded session outcome and counter queries with
  finite counters and an explicit evidence-incomplete state, and **shall not** expose dashboard, storage,
  query-presentation, or export primitives.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-021`, `XCOM-SYS-FR-032`; FR-021, FR-032; `XCOM-DU-020`.
  - Verification intent: session-query counter test; `T31-TS-006`; CHK-18.
- **T031-SR-016 [ubiquitous]**: The gateway **shall** be deterministic and bounded under concurrency: one
  per-session mutex plus a bounded request queue, a finite declared operation per call, and **no** verdict that
  depends on ambient wall-clock time, randomness, or environment.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-007`, `XCOM-SYS-FR-030`; FR-007, FR-030; `XCOM-DU-020`.
  - Verification intent: deterministic queue-bound and concurrency inspection; `T31-TS-009`, `T31-TS-010`; CHK-09.
- **T031-SR-017 [ubiquitous]**: Build wiring **shall** be additive: one new gateway runtime library and additive
  `t031-<kind>`-labelled test executables registered in `src/xverse/xcom/CMakeLists.txt`, with any runtime-inventory
  change declared explicitly and no existing target, test name, label, command, or expected value changed.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-030`; FR-030; T012 subtree build contract.
  - Verification intent: changed-path and discovered-count comparison; CHK-19, NEG-06, NEG-10.

### 4.7 Safety, envelope honesty, and governance

- **T031-SR-018 [ubiquitous]**: The gateway and its tests **shall** be offline and local-only: only the C++ standard
  library, the T030 generated Protocol Buffers message library, the accepted in-process T021–T029 libraries, and
  GTest; **no** network, `AF_INET`/`AF_INET6`, DNS, resolver, TLS, ambient/secret, dynamic-load, subprocess, or
  legacy access and **no** new admitted dependency.
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-026`, `XCOM-SYS-FR-028`; FR-026, FR-028; `XCOM-INV-15`;
    Constitution II, VII.
  - Verification intent: forbidden-API source scan and the offline build; `T31-TS-022`; CHK-20, NEG-01, NEG-07.
- **T031-SR-019 [ubiquitous]**: T031 **shall** reconcile with the T007 ownership register, the T008 register, the
  T009 architecture model, and the T010 unit design without rewriting or weakening them; **shall** keep the register
  REF-002 disposition `unchanged` with an empty `promoted` list; and **shall** record honestly that
  `XCOM-SW-GW-002` is implemented for the gateway slice by T031 while `XCOM-SW-GW-003` and T032–T041 remain
  allocated. The planned→established path-status reconciliation for the now-present `tool_gateway.hpp`/`.cpp` paths
  is a status-only change.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-035`, `XCOM-SYS-FR-030`; FR-030, FR-035; Constitution VII, IX.
  - Verification intent: register validators plus the recorded-maturity inspection; CHK-21, NEG-09.
- **T031-SR-020 [ubiquitous]**: The T031 candidate **shall** satisfy the deterministic Phase 7 gate: the five plan
  work products and the implementation record exist; `src/xverse/xcom/**` and at least one `tests/` path change; the
  Phase 7 runner's unit configure/build and `t031-`-labelled discovery pass; `git diff --check` is clean; and the
  T031 checkbox is marked complete **only** in the implementation stage.
  - Refines: ADR-0020; anchors `XCOM-SYS-FR-030`; FR-030; Constitution X.
  - Verification intent: `xcom_phase7_gate.py verify T031 <baseline>`; `git diff --check`; CHK-22, NEG-10.
- **T031-SR-021 [ubiquitous]**: Because the T011 admitted envelope cannot link the gRPC runtime (verified
  fail-closed; `T030-GAP-02`), the gateway **shall** realize the accepted message and method contract over a
  bounded, host-protected local-IPC framing bound 1:1 to the T030 method names; it **shall** add no admitted
  dependency and **shall not** claim a linked gRPC runtime. The deferred gRPC transport runtime **shall** be
  recorded as an explicit gap (`T031-GAP-01`).
  - Refines: `XCOM-SW-GW-002`; anchors `XCOM-SYS-FR-032`, `XCOM-SYS-FR-030`; FR-032, FR-030; `XCOM-XLC-002`,
    `XCOM-DU-020`.
  - Verification intent: envelope-decision inspection and operation-table equality; `T31-TS-001`, `T31-TS-003`;
    CHK-03, CHK-04, CHK-20.

## 5. Requirement-to-accepted-anchor traceability

| T031 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T031-STK-001 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-032` | FR-032 | SC-011, VII |
| T031-STK-002 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-016/032` | FR-016, FR-032 | II, VII |
| T031-STK-003 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-007/013/032` | FR-007, FR-013, FR-032 | II, VII |
| T031-STK-004 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-027/032` | FR-027, FR-032 | X |
| T031-STK-005 | Constitution VII/IX; ADR-0020 | `XCOM-SYS-FR-035` | FR-035 | VII, IX |
| T031-SR-001 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-032` | FR-032 | VII, IX |
| T031-SR-002 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-022/032` | FR-022, FR-032 | IX |
| T031-SR-003 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-032/022` | FR-032, FR-022 | IX |
| T031-SR-004 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-016/032` | FR-016, FR-032 | II, VII |
| T031-SR-005 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-007/013/032` | FR-007, FR-013, FR-032 | II, IX |
| T031-SR-006 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-007/020/032` | FR-007, FR-020, FR-032 | IX |
| T031-SR-007 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-007/013/032` | FR-007, FR-013, FR-032 | IX |
| T031-SR-008 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-028/032` | FR-028, FR-032 | II, VII |
| T031-SR-009 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-026/032` | FR-026, FR-032 | VII |
| T031-SR-010 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-011/012/013/032` | FR-011–FR-013, FR-032 | IX |
| T031-SR-011 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-015/017/018/021` | FR-015, FR-017, FR-018, FR-021 | IX |
| T031-SR-012 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-034` | FR-034 | IX |
| T031-SR-013 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-021/032` | FR-010, FR-021, FR-032 | IX |
| T031-SR-014 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-027/032` | FR-027, FR-032 | X |
| T031-SR-015 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-021/032` | FR-021, FR-032 | IX |
| T031-SR-016 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-007/030` | FR-007, FR-030 | IX |
| T031-SR-017 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-030` | FR-030 | VII, X |
| T031-SR-018 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-026/028` | FR-026, FR-028 | II, VII |
| T031-SR-019 | Constitution; ADR-0020 | `XCOM-SYS-FR-030/035` | FR-030, FR-035 | VII, IX |
| T031-SR-020 | ADR-0020 | `XCOM-SYS-FR-030` | FR-030 | X |
| T031-SR-021 | `XCOM-SW-GW-002` | `XCOM-SYS-FR-032/030` | FR-032, FR-030 | IX, X |

`XCOM-SW-GW-002` is an accepted capability-007 software requirement
(`docs/engineering/xcom/t008/requirements-register.{json,md}`). It is accepted text; T031 satisfies it for the
gateway slice and does not rewrite it. The register row is not changed and no register maturity is promoted by the
plan stage; the per-task maturity projection is recorded in the T031 work products, following the T030 precedent.

## 6. REF-002 disposition

T031 owns no REF-002 SADS ID and promotes none. It contributes gateway-side evidence toward the allocated
communication IDs already exercised by the communication boundary: `XVE-SYS-0141` is **deferred** ("protocol/
provider capabilities") in the accepted allocation, and `XVE-SYS-0142`–`0158` retain their accepted dispositions.
The local-IPC gateway is recorded as a **partial contribution** to the deferred target and is **not** promoted;
nothing in the `promoted` list changes. The capability `ref002.disposition` stays `unchanged` (T031-SR-019). No
allocated, deferred, architectural-target, or superseded SADS requirement is reported as implemented.

## 7. Affected paths

### 7.1 Paths the T031 candidate changes (implementation stage)

| Path | Change | Notes |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp` | add | gateway public interface: config, outcome/phase vocabulary, safe log boundary, bounded local-IPC channel, gateway session (`XCOM-DU-020`, `XCOM-CMP-010`) |
| `src/xverse/xcom/src/tool_gateway.cpp` | add | gateway session, operation dispatch, deadline/flow-control/cleanup, `AF_UNIX` endpoint, framing |
| `src/xverse/xcom/CMakeLists.txt` | edit (additive) | add `xverse_xcom_tool_gateway` to `XVERSE_XCOM_RUNTIME_TARGETS`; register `t031-<kind>` test executables; no existing target/label/value changes |
| `tests/xcom/tool_gateway/gateway_support.hpp` | add | bounded test-local manual clock, in-process channel, log capture, and source-path helpers (payload-free) |
| `tests/xcom/tool_gateway/gateway_session_tests.cpp` | add | `T31-TS-001`…`T31-TS-006` |
| `tests/xcom/tool_gateway/gateway_bounds_tests.cpp` | add | `T31-TS-007`…`T31-TS-010` |
| `tests/xcom/tool_gateway/gateway_lifecycle_tests.cpp` | add | `T31-TS-011`…`T31-TS-014` |
| `tests/xcom/tool_gateway/gateway_local_ipc_tests.cpp` | add | `T31-TS-015`…`T31-TS-017` |
| `tests/xcom/tool_gateway/gateway_negative_tests.cpp` | add | `T31-TS-018`…`T31-TS-022` |
| `tests/xcom/tool_gateway/gateway_logging_tests.cpp` | add | `T31-TS-023`, `T31-TS-024` |
| `docs/engineering/xcom/t009/architecture-model.{json,md}` | edit | `XCOM-CMP-010` planned→established path status only (status field) |
| `docs/engineering/xcom/t010/unit-design.{json,md}` | edit | `XCOM-DU-020` planned→established path status only (status field) |
| `engineering/project.json` | edit | current task T031 and accepted baseline `4dded2317f895978cce0331ae88e34ac28b3a609` |
| `engineering/requirements/T031-STK-00{1..5}.json`, `T031-SR-0{01..21}.json` | add | current-task requirement records |
| `engineering/architecture/components/T031-SR-0{01..21}-CMP.json` | add | current-task component allocations |
| `engineering/unit-specifications/T031-SR-0{01..21}-U.json` | add | current-task unit specifications |
| `engineering/validation/scenarios/T031-VS-ACCUMULATED.json` | add | current-task validation scenario |
| `engineering/trace/links.json` | edit (implementation) | additive T031 trace links and the inherited digest refresh |
| `engineering/verification/measures/{unit,integration,validation}.json` | edit (implementation) | refreshed to the discovered T031 cases |
| `engineering/stage-results/*.json` | edit (implementation) | inherited artifact-digest refresh when `src/xverse/xcom/CMakeLists.txt` changes |
| `docs/engineering/xcom/t031/requirements.md` | add | this document |
| `docs/engineering/xcom/t031/architecture.md` | add | T031 architecture |
| `docs/engineering/xcom/t031/detailed-design.md` | add | T031 detailed design |
| `docs/engineering/xcom/t031/unit-specifications.md` | add | T031 unit specifications |
| `docs/engineering/xcom/t031/verification-plan.md` | add | T031 verification plan |
| `docs/engineering/xcom/t031/implementation.md` | add | implementation-stage record |
| `docs/engineering/xcom/t031/internal-review.json` | add | internal-review record |
| `reports/review-index.md` | edit | T031 candidate section appended |
| `specs/007-xcom-core/tasks.md` | edit | one-line T031 checkbox, **implementation stage only** |
| `reports/xcom-queue/t031-package.json` | add | implementation-stage package record |

### 7.2 Consumed read-only (not changed by T031)

`proto/xverse/xcom/v1/tool_gateway.proto`; `cmake/XComOfflineDependencies.cmake`; `cmake/XComWarnings.cmake`; the
root `CMakeLists.txt`; `scripts/**`; `xdl/**`; `src/xverse_xdl/**`; all accepted `src/xverse/xcom/**` runtime
sources, headers, and library targets other than the additive build wiring; every accepted test under
`tests/xcom/**` other than the new T031 suites; `docs/engineering/xcom/task-ownership.*`; `docs/engineering/xcom/t00{7,8,9,10}/**`
other than the status-only path reconciliation; `docs/engineering/xcom/t0{1..30}/**`;
`docs/engineering/xcom/build-environment.md`; `docs/engineering/xcom/dependency-lock.md`; and
`specs/007-xcom-core/**` (other than the T031 checkbox).

### 7.3 Explicitly not implemented by T031

The separate-process synthetic client and generated-client tests (T032), the reusable contract suites (T033), the
second synthetic provider (T034), the benchmark/sanitizer/static/Doxygen/delivery tasks (T035–T040), the gRPC
transport runtime linkage (`T031-GAP-01`), and the executed gRPC server. External Codex review and user acceptance
remain T039/T041 and are deferred until the ordered backlog `xcom-t030-t034-20260928` completes.

## 8. Gaps, risks, and open items

### 8.1 Recorded limitations

- **T031-GAP-01 — gRPC transport runtime deferred.** The T011 admitted envelope cannot link the gRPC runtime
  (`libcares.so.2` and peers are absent; the link fails closed, `T030-GAP-02`). T031 realizes the accepted message
  and method contract over a bounded, host-protected `AF_UNIX` local-IPC framing bound 1:1 to the T030 method names
  and records the deferred gRPC transport runtime. No new dependency is added and no gRPC-runtime link is claimed.
- **T031-GAP-02 — gateway-side no-TCP proof only.** T031 proves the absence of a TCP listener on the gateway side
  (endpoint family, source scan, runtime `getsockname`). The separate-process client and the end-to-end `SC-011`
  no-TCP demonstration are T032.
- **T031-GAP-03 — no reusable abstraction.** The gateway tests are T031-local and are not the T033 reusable
  contract suite.
- **T031-GAP-04 — generated-code documentation.** The generated Protocol Buffers message documentation policy
  remains `DOX-GAP-02` (T037); T031 adds Doxygen documentation for the new hand-written public header only.
- **T031-GAP-05 — no deployed-service or compatibility claim.** The gateway is a bounded prototype validated only
  with owned local fixtures; it makes no production-readiness, compatibility, or parity claim.

### 8.2 Gaps with owning tasks

| Gap | Owner |
| --- | --- |
| Separate-process synthetic client and no-TCP separate-process proof (`SC-011`) | T032 |
| Reusable gateway contract suites and second synthetic provider | T033/T034 |
| gRPC transport runtime envelope | deferred capability gap `T031-GAP-01` |
| Executed sanitizer/static/Doxygen/benchmark and delivery bundle | T035–T040 |
| Independent review and user acceptance | T039/T041 |

### 8.3 Open items

- **T031-OPEN-01 — inherited provenance refresh.** Editing `src/xverse/xcom/CMakeLists.txt` invalidates the
  inherited `T020-L-046` `implemented_by` target digest in `engineering/trace/links.json` and the declared
  `links.json`/`CMakeLists.txt` digests in `engineering/stage-results/*.json`. Following the T026–T030 precedent,
  the implementation stage refreshes those inherited digests; no requirement, link identity, relation, or stage
  result changes.
- **T031-OPEN-02 — planned→established path reconciliation.** Creating `tool_gateway.hpp`/`tool_gateway.cpp` makes
  six accepted T009/T010 planned paths present in the tree, so the T009/T010 validators require the
  planned→established status transition (status field only; the same minimal normalization T030 applied). Unit
  `XCOM-DU-020` maturity stays `allocated`.
- **T031-OPEN-03 — runtime-inventory change.** Adding `xverse_xcom_tool_gateway` updates the T012
  `XVERSE_XCOM_RUNTIME_TARGETS` inventory and the generated `xcom_build_contract` expectation in the same change,
  as the T012 contract requires.
- **T031-OPEN-04 — AF_UNIX scratch path.** The local-IPC suite binds a socket under a bounded build-tree scratch
  directory supplied as a compile definition (the T026 precedent); the path is never printed into public evidence.

## 9. Definition of done (requirements view)

T031 is done for a candidate revision when: every §4 requirement has at least one named check; the bounded
local-IPC-only gateway, complete operation surface, fail-closed version negotiation, exact permit enforcement,
explicit bounds, per-request deadlines, bounded flow control, host-protected no-TCP local IPC, disconnect/expiry
cleanup, and safe logs are proven at the recorded candidate revision; `XCOM-SW-GW-002` is recorded implemented for
the gateway slice by T031 while `XCOM-SW-GW-003` and T032–T041 remain allocated; the gRPC transport gap is recorded
and no new dependency is added; no accepted requirement, test, ADR, contract, register, or predecessor byte is
weakened; the register validators pass with REF-002 unchanged and nothing promoted; the deterministic Phase 7 gate
passes; and a separate DeepSeek internal review records its findings before any repair. This does not constitute
user acceptance, which remains T041.

## 10. Requirement-to-check index (realized in `verification-plan.md`)

| Requirement | Primary checks |
| --- | --- |
| T031-STK-001 | CHK-01, CHK-03, CHK-10, CHK-22 |
| T031-STK-002 | CHK-06, CHK-11 |
| T031-STK-003 | CHK-07, CHK-08, CHK-09, CHK-12 |
| T031-STK-004 | CHK-16, CHK-17 |
| T031-STK-005 | CHK-21, CHK-22 |
| T031-SR-001 | CHK-01, CHK-03 |
| T031-SR-002 | CHK-04 |
| T031-SR-003 | CHK-05 |
| T031-SR-004 | CHK-06 |
| T031-SR-005 | CHK-07, CHK-12 |
| T031-SR-006 | CHK-08 |
| T031-SR-007 | CHK-09, CHK-12 |
| T031-SR-008 | CHK-10, CHK-20 |
| T031-SR-009 | CHK-11 |
| T031-SR-010 | CHK-12, CHK-13 |
| T031-SR-011 | CHK-14 |
| T031-SR-012 | CHK-15 |
| T031-SR-013 | CHK-16 |
| T031-SR-014 | CHK-17 |
| T031-SR-015 | CHK-18 |
| T031-SR-016 | CHK-09, CHK-19 |
| T031-SR-017 | CHK-19 |
| T031-SR-018 | CHK-20 |
| T031-SR-019 | CHK-21 |
| T031-SR-020 | CHK-22 |
| T031-SR-021 | CHK-03, CHK-04, CHK-20 |
