# T032 Architecture — Separate-Process Synthetic Client and Generated-Client Contract Tests

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T032 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → architecture |
| Revision | 1 (separate-process synthetic-client conformance slice) |
| Baseline revision | `e6197c67868213ffb6523d8bf62ed4c2c4e3b0af` |
| Affected source paths | `src/xverse/xcom/fixtures/synthetic_tool.cpp` (new, fixture executable `xverse_xcom_synthetic_client`); `tests/xcom/tool_gateway/synthetic_client_*.cpp` / `synthetic_client_support.hpp` (new); `src/xverse/xcom/CMakeLists.txt` (edit, additive executable + test registration); T009/T010 planned→established path-status reconciliation; engineering trace/validation records |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-010` local tool gateway, `XCOM-CMP-011` synthetic sink/tools, `XCOM-CMP-012` external validation tool, `XCOM-XB-010` synthetic-client→gateway IPC boundary, `XCOM-XLC-002` external-rpc contract, `XCOM-INV-08`/`XCOM-INV-13`/`XCOM-INV-15` safety invariants); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-021` separate-process synthetic tool client; `XCOM-DU-019`/`XCOM-DU-020` consumed read-only); `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-SW-GW-003`); accepted T030 generated messages; accepted T031 gateway public header; `specs/007-xcom-core/contracts/tool-gateway.md`; `specs/007-xcom-core/plan.md`; ADR-0016, ADR-0018, ADR-0019, ADR-0020 |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T032 is the **conformance-client** task of the gateway (`GW`) family. T030 defined the versioned `XCOM-XLC-002`
contract and generated the C++ message types; T031 realized it as a bounded, host-protected local-IPC-only gateway.
T032 adds the accepted `XCOM-DU-021` separate-process synthetic tool client and proves with generated-client contract
tests that observation and every allowed stimulation action complete through the host-protected local endpoint with no
TCP listener and zero items from invalid or expired sessions (`SC-011`).

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013/T-CORE vocabulary (read-only)
   → T017–T020 XDL Profile + activation-plan digest binding (read-only)
   → T021–T024 observation boundary (read-only) → T025–T029 stimulation boundary (read-only)
   → T030 versioned external-tool contract + generated messages (read-only)
   → T031 bounded local-IPC-only gateway session (read-only)
   → T032 separate-process synthetic client + generated-client contract tests (this slice)
   → T033 reusable suites → T034 second provider → T035–T041 evidence/review/acceptance
```

T032 changes exactly one production fixture source (the separate-process synthetic client), one additive fixture
executable and one additive test family, and shared build tracing. It changes no accepted `src/` runtime source other
than the additive `src/xverse/xcom/CMakeLists.txt` wiring, no accepted test, target, label, command, or expected
value, and no accepted register except the status-only path reconciliation.

## 3. Boundary and context

### 3.1 System context

```text
   ┌────────────── accepted capability-007 anchors (read-only) ──────────────┐
   │  spec.md FR-007/010/011/012/013/016/017/018/021/022/023/027/028/029/030/ │
   │    032/034/035 · SC-007 · SC-011 · contracts/tool-gateway.md            │
   │  t009 XCOM-CMP-010/011/012 · XCOM-XB-010 · XCOM-XLC-002                 │
   │  t009 XCOM-INV-08 · XCOM-INV-13 · XCOM-INV-15                           │
   │  t010 XCOM-DU-021 (separate-process synthetic tool client)              │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ realized by
   ┌──────── accepted boundaries (read-only, consumed) ─────────────────────┐
   │  T031 LocalIpcEndpoint / GatewaySession / gateway_decode_request_frame  │
   │      / gateway_operation_names() · T030 generated messages + descriptor │
   │  T025–T029 permit/journal/guard/action-path/lease · T021–T024 hub       │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ composed by
   ┌──────────────────── T032 owned artifacts (this slice) ────────────────────────┐
   │  src/xverse/xcom/fixtures/synthetic_tool.cpp   (separate-process client)      │
   │  xverse_xcom_synthetic_client (fixture executable, not a runtime library)      │
   │  tests/xcom/tool_gateway/synthetic_client_support.hpp                        │
   │  tests/xcom/tool_gateway/synthetic_client_{observation,stimulation,          │
   │      contract,negative,bounds}_tests.cpp                                      │
   │  guarantee : separate-process, AF_UNIX local only, no TCP listener, exact     │
   │      permit, observation + four stimulation actions, zero invalid emission   │
   └──────────────────────────────────┬──────────────────────────────────────────────┘
                                      ▼
              T033 reusable suites · T034 second provider · T035–T041 evidence
```

T032 introduces a real separate OS process that connects to the accepted T031 host-protected `AF_UNIX` endpoint. The
accepted `XCOM-INV-13` permits that host-protected local endpoint, and `specs/007-xcom-core/contracts/tool-gateway.md`
requires it. It links no gRPC runtime; the T011 admitted envelope cannot supply the gRPC runtime transitive libraries
and a gRPC++ link fails closed (`T030-GAP-02`, `T031-GAP-01`, verified).

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T32-XB-1` Client vs contract | the synthetic client and its operation mapping | the T030 `.proto` messages, the generated descriptor, and the method names | The client realizes the accepted generated messages/methods; it defines no competing contract, RPC, or configuration language (`T032-DD-01`). |
| `T32-XB-2` Separate process vs production | the owned, self-built `xverse_xcom_synthetic_client` fixture process | any legacy binary, external peer, subprocess of a production workload, or ambient service | Only the owned fixture process may run; it is launched with an explicit bounded argv and a scrubbed admitted environment (`XCOM-INV-15`). |
| `T32-XB-3` Local IPC vs TCP/remote | `AF_UNIX` local sockets and in-process bounded channels | `AF_INET`/`AF_INET6`, DNS, resolver, TLS, remote peers | Only `AF_UNIX`/`socketpair` may be used; a source and runtime check fails closed otherwise (`XCOM-INV-13`). |
| `T32-XB-4` Transport vs authorization | the exact T025 validation permit | local socket access, account boundary, socket-file permission | Transport access never substitutes for the permit (`XCOM-INV-08`); an invalid/expired session emits nothing. |
| `T32-XB-5` Bounds vs unbounded | explicit client message/deadline/timeout bounds and the gateway bounds | implicit or unbounded message, deadline, or timeout | Every client bound is an explicit configuration value; an over-bound message or deadline is handled fail-closed. |
| `T32-XB-6` Failure vs success | deterministic `failed`/`expired`/`evidence-incomplete` reporting | an unknown outcome reported as success | Peer failure, timeout, or disconnect-after-intent is never reported as success. |
| `T32-XB-7` Logs vs content | stable codes, phase, logical identity, size, timing, outcome | payload bytes, permit contents, secrets, private addresses, host paths | No committed file or bounded log contains payload, permit content, secret, private address, or host path. |
| `T32-XB-8` Admitted envelope vs dependency growth | the T011-admitted tools, protobuf runtime, accepted in-process libraries, and GTest | any new admitted dependency or linked gRPC runtime | T032 adds no admitted dependency and links no gRPC runtime; the transport gap is recorded, not hidden. |
| `T32-XB-9` Predecessor vs candidate | accepted T007–T031 bytes, registers, ADRs, tests, provenance | a rewrite, weakening, or unrecorded digest drift | Only the declared T032 paths change; inherited digests and the planned→established status are refreshed and recorded. |
| `T32-XB-10` Local suite vs reusable abstraction | the T032-local synthetic-client suites | the T033 reusable contract-suite abstraction | The T032 suites remain T032-local; they do not become or pre-empt the T033 abstraction (T032-SR-020). |

### 3.3 Prohibited elements (must remain absent)

No TCP listener, `AF_INET`/`AF_INET6` socket, DNS, resolver, or TLS use; no external network peer; no legacy binary,
legacy repository, or production workload; no compiled or linked gRPC runtime; no new admitted dependency; no
dashboard, storage, query-presentation, or export primitive; no unbounded message, deadline, timeout, or stream; no
permit bypass; no payload, permit, secret, private address, or host path in a log record or committed file; no
ambient wall-clock-dependent verdict; no change to an accepted predecessor `src/`, `tests/`, `xdl/`, or
`docs/engineering/xcom/t0{07..31}/` byte other than the additive `CMakeLists.txt` wiring and the status-only path
reconciliation; no rewrite or weakening of an accepted ADR, requirement, contract, schema, register, or REF-002
disposition; no acceptance or integration of the candidate.

## 4. Components

`T32-*` names are local to this document; the accepted `XCOM-DU-021`, `XCOM-CMP-010/011`, `XCOM-XLC-002`, and
`XCOM-XB-010` identifiers are the authorized units/contracts.

### 4.1 New T032 components

- **`T32-CMP-CLIENT` Synthetic client process** (`synthetic_tool.cpp`): the bounded `xverse_xcom_synthetic_client`
  fixture executable. It parses a bounded argument vector (local socket path and a declared exercise mode), connects
  to the accepted `AF_UNIX` host-protected endpoint, serializes generated request messages into the T031 framing,
  reads bounded response frames, and emits bounded machine-readable result lines. It declares an explicit client
  configuration (maximum message size, per-request deadline, transport timeout) and adds no runtime library.
- **`T32-CMP-TRANSPORT` Client connection seam**: a bounded `AF_UNIX` connect/read/write seam over the accepted
  endpoint path. It is the only client transport; no TCP/DNS/TLS facility is referenced. The method table is bound 1:1
  to the T030 generated `ToolGateway` service descriptor method set.
- **`T32-CMP-SERVER` Test-local server harness** (`synthetic_client_support.hpp`): a bounded, single-threaded
  accept/read/dispatch/write loop that serves the accepted T031 `GatewaySession` over the accepted `LocalIpcEndpoint`,
  decodes request frames with `gateway_decode_request_frame`, dispatches by exact method name, and serializes the
  response frames (including the bounded `ReadObservations` record frames and terminator). It is test-local and is not
  the T033 reusable abstraction.
- **`T32-CMP-LAUNCH` Separate-process launcher** (`synthetic_client_support.hpp`): a bounded launcher that starts the
  fixture executable with an explicit bounded argument vector and a scrubbed admitted environment, waits with a
  bounded loop, and returns a bounded exit status plus captured result lines. No legacy binary, external peer, or
  production workload is launched.
- **`T32-CMP-TESTS` Synthetic-client tests** (`tests/xcom/tool_gateway/synthetic_client_*.cpp`): the five additive
  `t032-<kind>` suites and their bounded helper header.
- **`T32-CMP-BUILD`** (T012): the subtree warning-as-error rule extended additively by one fixture executable
  (`xverse_xcom_synthetic_client`) and five `t032-<kind>` test executables; the runtime-target inventory is unchanged.
- **`T32-WP`** — the T032 repository-owned work-product set.

### 4.2 Consumed components (read-only)

- **`T32-CMP-T031`** — the accepted bounded local-IPC-only gateway (`tool_gateway.hpp`/`tool_gateway.cpp`,
  `LocalIpcEndpoint`, `GatewaySession`, `GatewayConfig`, `gateway_decode_request_frame`, `gateway_log_sink`,
  `gateway_operation_names()`). Consumed read-only.
- **`T32-CMP-T030`** — the accepted versioned contract and generated Protocol Buffers messages and service
  descriptor (`proto/xverse/xcom/v1/tool_gateway.proto`, `xverse_xcom_tool_gateway_proto`). Consumed read-only.
- **`T32-CMP-T025`–`T32-CMP-T028`** — accepted validation-permit/session/time-authority, journal, guard, and action
  path/lease contracts. Consumed read-only through their public headers.
- **`T32-CMP-T021`–`T32-CMP-T024`** — accepted bounded observation hub and tap policy. Consumed read-only.
- **`T32-CMP-T011`/`T32-CMP-T012`** — the admitted offline envelope and the subtree build/test contract. The fixture
  executable is added without changing the runtime-target inventory; no rule is weakened.

## 5. Data flow (ordered)

1. **Build the fixture.** The subtree build compiles the accepted T031 gateway, the T030 generated message library,
   the T032 synthetic-client executable, and the five `t032-<kind>` test executables under the warning-as-error
   policy. The runtime-target inventory is unchanged.
2. **Bind the endpoint (parent).** The test process builds the accepted in-process boundaries and one bounded
   `GatewaySession`, then binds one host-protected `AF_UNIX` `LocalIpcEndpoint` under the bounded build-tree scratch
   directory.
3. **Launch the client (parent).** The launcher starts `xverse_xcom_synthetic_client` with an explicit bounded argv
   (socket path, declared exercise mode, client bounds) and a scrubbed admitted environment. `T032-DD-02`.
4. **Connect (client).** The client connects only to the `AF_UNIX` socket path; no TCP/DNS/TLS or remote peer is
   contacted.
5. **Serve (parent).** The test-local harness accepts the bounded peer and reads bounded request frames; a frame whose
   length exceeds the configured bound or whose method name is not in the committed table is rejected fail-closed
   before dispatch.
6. **Negotiate and enforce.** The session applies the production compatibility predicate (unsupported major rejected
   first), the deadline rule against the accepted T025 time authority, and the bounded in-flight budget.
7. **Dispatch.** The harness maps each decoded request onto the corresponding accepted `GatewaySession` operation and
   delegates to the accepted T025–T028 / T021–T024 boundaries; a rejection emits no normal-route item.
8. **Observe.** For an observation exercise the harness writes at most the granted number of metadata-only record
   frames and then a bounded terminator; the client reports the observed record count and, on close, the
   delivered/dropped counters.
9. **Stimulate.** For each of the four allowed stimulation actions the client submits one bounded request; the gateway
   routes it through the accepted guard/journal/action path with persistent synthetic provenance, and the client
   reports the emitted outcome.
10. **Report (client).** The client writes bounded machine-readable result lines (method name, stable outcome/code,
    bounded size/timing, logical identity only) and exits with a bounded status; it writes no payload, permit content,
    secret, private address, or host path.
11. **Verify (parent).** The test parses the bounded result lines, checks the bounded frame/method inventory, and
    asserts the expected outcome and emission counts (including zero emission for invalid/expired sessions).
12. **Clean up.** The harness ends the peer session deterministically; the client process exits and is reaped within a
    bounded wait; the endpoint unlinks its socket path on destruction.
13. **Wire additively.** The build registers one fixture executable and five `t032-<kind>` test executables; the
    runtime-target inventory is unchanged.

## 6. Interfaces

### 6.1 Synthetic-client interface (`src/xverse/xcom/fixtures/synthetic_tool.cpp`)

| Element | Contract |
| --- | --- |
| `SyntheticClientConfig` | explicit bounds: maximum message size, per-request deadline, transport timeout; an illegal/unbounded value fails closed |
| `SyntheticClientResult` | bounded report: method name, stable outcome code, bounded size/timing, logical identity only |
| `synthetic_client_run(argc, argv)` | the single bounded entry point: connect to the local path, run the declared exercise, emit bounded result lines, return a bounded status |
| bounded local connect/read/write seam | `AF_UNIX` only to the accepted endpoint path; no TCP/DNS/TLS |
| client method table | pinned 1:1 and in order to the T030 generated `ToolGateway` service descriptor method set |

Ownership/lifetime: the client owns its bounded buffers and one socket descriptor for the process lifetime; it holds
no gateway session handle directly (the parent owns the accepted `GatewaySession`). Thread-safety: one declared user;
one request or stream at a time per session (accepted `XCOM-DU-021` externally-synchronized model). Failure: an
invalid, over-bound, timed-out, or disconnected exchange returns a stable non-success result and never reports success.

### 6.2 Consumed contract (read-only)

| Interface | Contract consumed (unchanged) |
| --- | --- |
| `xverse::xcom::tool_gateway_proto` (T030) | generated Protocol Buffers request/response messages and the `ToolGateway` service descriptor |
| T031 `LocalIpcEndpoint`, `GatewayConfig`, `GatewaySession`, `gateway_decode_request_frame`, `gateway_operation_names()`, `GatewayLogSink` | bounded host-protected `AF_UNIX` endpoint, bounded framing, ten-operation session, and payload-free log boundary |
| T025 `Permit`, `SessionManager`, `TimeAuthority` | validation permit/session lifecycle and the injected time authority |
| T026 `StimulationJournal` | journal-before-emission intent/outcome |
| T027 `StimulationGuard` | fail-closed pre-emission guard |
| T028 `StimulationActionPath`, `ServiceEmulationRegistry` | guarded emission and exclusive generation-bound lease |
| T021–T024 `ObservationHub`, `ObservationTapSpec`, `ObservationTapHandle` | bounded metadata-only observation |
| GTest and `google::protobuf::DescriptorPool` | the accepted offline test framework and generated descriptor pool |

## 7. Concurrency and resource bounds

| Aspect | T032 decision |
| --- | --- |
| Production footprint | one fixture source, one fixture executable, five additive test executables, one test helper header |
| Build inventory | one fixture executable `xverse_xcom_synthetic_client` and five `t032-<kind>` test targets (`observation`, `stimulation`, `contract`, `negative`, `bounds`); the runtime-target inventory is unchanged |
| Processes | exactly one owned fixture client process per case, launched with an explicit bounded argv; no legacy, external, or production process |
| Writers | one declared writer per artifact; the client owns its buffers; the accepted boundaries own their own state |
| Threads | single declared user per case; the harness serves one peer at a time; no unbounded thread or queue |
| Operations per case | finite and declared; every frame read, record pull, and wait step is bounded |
| Message and stream | every client and gateway frame is bounded by the configured maximum message size; every observation read returns at most the granted record count |
| Transport | one bounded `AF_UNIX` connect/exchange per case under a build-tree scratch directory; no network, DNS, TLS, legacy, or subprocess of a production workload |
| Time | no verdict depends on ambient wall-clock time; the gateway deadlines use the injected T025 time authority and the client wait is bounded |
| Determinism | the operation table, framing, bounds enforcement, and per-action outcomes are deterministic for fixed inputs; repeated runs are equal |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Single generated-contract realization | one synthetic-client interface mapping the T030 generated messages/methods; no competing interface | `T032-SR-001`, `T032-SR-002`; CHK-03, CHK-04 |
| Separate-process conformance | one owned fixture process launched with explicit bounded argv and a scrubbed environment | `T032-SR-003`; CHK-05 |
| Local-only transport | `AF_UNIX` only; no TCP/DNS/TLS; host-protected permissions | `T032-SR-004`; CHK-06 |
| Bounded observation | open/read/close bounded by configuration and granted capacity; metadata-only | `T032-SR-005`, `T032-SR-006`; CHK-07…CHK-10 |
| Complete stimulation | all four allowed actions routed through the accepted guard/journal/action path with provenance | `T032-SR-007`; CHK-11 |
| Exclusive lease | generation-bound acquire/release through the client | `T032-SR-008`; CHK-12 |
| Zero invalid emission | invalid/expired sessions emit zero normal-route items | `T032-SR-009`; CHK-13 |
| Fail-closed version rejection | unsupported major rejected before any operation | `T032-SR-010`; CHK-14 |
| Explicit bounds | message/deadline/timeout bounds are explicit client config values | `T032-SR-011`; CHK-15 |
| Deterministic failure semantics | stable non-success outcomes; never success on unknown | `T032-SR-012`; CHK-16 |
| Safe evidence | no payload/permit/secret/private-address/host-path in a committed file or log | `T032-SR-013`; CHK-17 |
| Generated message fidelity | round-trip and unknown-field preservation | `T032-SR-015`; CHK-18 |
| Additive delivery | one fixture executable and five additive test targets; no existing target/test/label/value changed | `T032-SR-016`; CHK-19 |
| Offline safety | admitted libraries plus GTest only; no new admitted dependency; no gRPC-runtime link | `T032-SR-017`; CHK-20 |
| Governance and envelope honesty | registers re-validated; REF-002 unchanged; gRPC transport gap recorded | `T032-SR-018`; CHK-21 |

## 9. Consistency and constraints

- **Dependency direction preserved.** T032 consumes the accepted T007–T031 design and the T011 envelope; it
  introduces no dependency on a later slice, an external peer, or a legacy repository, and adds no admitted
  dependency.
- **Domain neutrality preserved.** Only generic X-COM vocabulary appears (synthetic client, session, observation,
  stimulation, lease, identity, generation, deadline, bound, provenance); no automotive, product, protocol, or
  configuration primitive is introduced.
- **XDL centrality preserved.** T032 neither parses nor authors XDL; plan and graph digests enter only as opaque
  logical identity strings already bound by the accepted plan.
- **Logical/physical separation preserved.** The client carries logical identities only; the local socket is a
  realization detail and no address or port enters the accepted message contract.
- **Synthetic origin preserved.** Stimulation flows through the accepted guard/journal/action path, so accepted items
  keep their persistent synthetic provenance; T032 introduces no differently-classified origin.
- **Envelope honesty.** The gRPC transport runtime gap is recorded (`T032-GAP-01`) rather than hidden by a new
  dependency or a claim that a gRPC runtime is linked (`T032-SR-017`).
- **Ownership preserved.** Only the declared T032 paths change; every accepted production byte and existing test is
  preserved except the additive `CMakeLists.txt` wiring and the status-only path reconciliation.
- **Maturity preserved.** The slice implements the separate-process synthetic client only; the reusable suites, second
  provider, executed evidence, and acceptance remain T033–T041.

## 10. Traceability

| Architecture element | T032 requirements |
| --- | --- |
| `T32-XB-1`, `T32-CMP-CLIENT` | T032-SR-001, T032-SR-002, T032-SR-017 |
| `T32-XB-2`, `T32-CMP-LAUNCH` | T032-SR-003, T032-SR-014 |
| `T32-XB-3`, `T32-CMP-TRANSPORT` | T032-SR-004 |
| `T32-XB-4` | T032-SR-009 |
| `T32-XB-5` | T032-SR-011 |
| `T32-XB-6` | T032-SR-012 |
| `T32-XB-7` | T032-SR-013 |
| `T32-XB-8` | T032-SR-017 |
| `T32-XB-9`, `T32-CMP-BUILD`, `T32-WP` | T032-SR-016, T032-SR-018, T032-SR-019 |
| `T32-XB-10`, `T32-CMP-TESTS` | T032-SR-020 |
| `T32-CMP-SERVER`, observation mapping | T032-SR-005, T032-SR-006 |
| stimulation/lease mapping | T032-SR-007, T032-SR-008 |
| version mapping | T032-SR-010 |
| generated message mapping | T032-SR-015 |
| documentation | T032-SR-021 |

## 11. Negative cases (architecture view)

Every boundary has a declared fail-closed behaviour and a negative-case owner; the executable cases are listed in
`verification-plan.md` §5.

| Boundary | Injected defect | Negative case |
| --- | --- | --- |
| `T32-XB-1` | define a competing client interface, reject a T030 method, or claim a gRPC-runtime link | NEG-02 |
| `T32-XB-2` | launch a legacy binary, external peer, or production workload | NEG-01 |
| `T32-XB-3` | bind/use TCP/`AF_INET`, DNS, or TLS | NEG-01 |
| `T32-XB-4` | let local access substitute for the permit; let an invalid/expired session emit | NEG-03, NEG-04 |
| `T32-XB-5` | omit a client bound or decide on ambient wall-clock time | NEG-06 |
| `T32-XB-6` | report a timeout, failure, or unknown outcome as success | NEG-04 |
| `T32-XB-7` | log a payload, permit, secret, private address, or host path | NEG-08 |
| `T32-XB-8` | add an admitted dependency or link the gRPC runtime | NEG-07 |
| `T32-XB-9` | weaken an accepted requirement/test/register or promote a REF-002 target | NEG-09, NEG-10 |
| `T32-XB-10` | make the T032 suite the reusable T033 abstraction or add a second provider | NEG-10 |
| Governance | mark the checkbox in the plan stage or skip the inherited provenance refresh | NEG-10 |
