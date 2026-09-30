# T031 Architecture — Bounded Local-IPC-Only Tool Gateway

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T031 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → architecture |
| Revision | 1 (local-IPC gateway session slice) |
| Baseline revision | `4dded2317f895978cce0331ae88e34ac28b3a609` |
| Affected source paths | `src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp` (new); `src/xverse/xcom/src/tool_gateway.cpp` (new); `tests/xcom/tool_gateway/gateway_*.cpp`/`gateway_support.hpp` (new); `src/xverse/xcom/CMakeLists.txt` (edit, additive library + test registration + declared runtime-inventory change); T009/T010 planned→established path-status reconciliation; engineering trace/validation records |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-010` local tool gateway, `XCOM-CMP-011` synthetic sink/tools, `XCOM-CMP-012` external validation tool, `XCOM-XB-008`/`XCOM-XB-010` protobuf IPC boundaries, `XCOM-XLC-002` external-rpc contract, `XCOM-INV-08`/`XCOM-INV-13`/`XCOM-INV-15` safety invariants); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-020` local-IPC-only gateway session); `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-SW-GW-002`); accepted T021–T029 public headers; `specs/007-xcom-core/contracts/tool-gateway.md`; `specs/007-xcom-core/plan.md`; ADR-0016, ADR-0018, ADR-0019, ADR-0020 |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T031 is the **gateway session** of the gateway (`GW`) family. T030 defined and proved the versioned
`XCOM-XLC-002` external-tool contract and generated the C++ message types; T031 realizes that contract as a
bounded, host-protected local-IPC-only gateway that enforces deadlines, flow control, exact permit rules,
deterministic cleanup, and safe logging. It authors no separate-process client (T032), no reusable contract suite
(T033), and no second provider (T034).

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013/T-CORE vocabulary (read-only)
   → T017–T020 XDL Profile + activation-plan digest binding (read-only)
   → T021–T024 observation boundary (read-only) → T025–T029 stimulation boundary (read-only)
   → T030 versioned external-tool contract + generated messages (read-only)
   → T031 bounded local-IPC-only gateway session (this slice)
   → T032 separate-process synthetic client → T033 reusable suites → T034 second provider
   → T035–T041 evidence/review/acceptance
```

T031 changes exactly two production artifacts (the new gateway header and source), one additive production library
(`xverse_xcom_tool_gateway`), one additive test family, and shared build tracing. It changes no accepted `src/`
runtime source other than the additive `src/xverse/xcom/CMakeLists.txt` wiring, no accepted test, target, label,
command, or expected value, and no accepted register except the status-only path reconciliation.

## 3. Boundary and context

### 3.1 System context

```text
   ┌────────────── accepted capability-007 anchors (read-only) ──────────────┐
   │  spec.md FR-007/008/011/012/013/016/018/020/021/022/026/027/028/030/032/ │
   │    034/035 · SC-011 · contracts/tool-gateway.md                         │
   │  t009 XCOM-CMP-010/011/012 · XCOM-XB-008 · XCOM-XB-010 · XCOM-XLC-002   │
   │  t009 XCOM-INV-08 · XCOM-INV-13 · XCOM-INV-15                           │
   │  t010 XCOM-DU-020 (local-IPC-only gateway session)                      │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ realized by
   ┌──────── accepted in-process boundaries (read-only, consumed) ─────────┐
   │  T025 Permit/SessionManager/TimeAuthority · T026 StimulationJournal   │
   │  T027 StimulationGuard · T028 StimulationActionPath/Registry          │
   │  T021–T024 ObservationHub/ObservationTapSpec                          │
   │  T030 generated Protocol Buffers messages (xverse_xcom_tool_gateway_proto)
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ composed by
   ┌──────────────────── T031 owned artifacts (this slice) ────────────────────────┐
   │  src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp  (session + endpoint)   │
   │  src/xverse/xcom/src/tool_gateway.cpp                  (session + endpoint)   │
   │  xverse_xcom_tool_gateway (STATIC, gateway runtime)                            │
   │  tests/xcom/tool_gateway/gateway_{session,bounds,lifecycle,local_ipc,          │
   │      negative,logging}_tests.cpp                                              │
   │  guarantee : bounded local IPC only, no TCP listener, exact permit,           │
   │      deadlines, flow control, deterministic cleanup, payload-free logs        │
   └──────────────────────────────────┬──────────────────────────────────────────────┘
                                      ▼
              T032 separate-process client · T033 suites · T034 second provider
```

T031 introduces a real host-protected local endpoint (`AF_UNIX`), which the accepted `XCOM-INV-13` explicitly
permits ("no TCP listener except the host-protected local tool gateway") and which
`specs/007-xcom-core/contracts/tool-gateway.md` requires. It links no gRPC runtime; the T011 admitted envelope
cannot supply the gRPC runtime transitive libraries and a gRPC++ link fails closed (`T030-GAP-02`, verified).

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T31-XB-1` Gateway vs contract | the gateway session and its operation mapping | the T030 `.proto` messages and method names | The gateway realizes the accepted messages/methods; it defines no competing contract, RPC, or configuration language (`T031-DD-01`). |
| `T31-XB-2` Local IPC vs TCP/remote | `AF_UNIX` sockets and in-process bounded channels | `AF_INET`/`AF_INET6`, DNS, resolver, TLS, remote peers | Only `AF_UNIX`/`socketpair` may be bound; a source and runtime check fails closed otherwise (`XCOM-INV-13`). |
| `T31-XB-3` Transport vs authorization | the exact T025 validation permit and session | local socket access, account boundary, socket-file permission | Transport access never substitutes for the permit (`XCOM-INV-08`); unauthorized requests emit nothing. |
| `T31-XB-4` Bounds vs unbounded | explicit message/stream/queue/record/payload bounds | implicit or unbounded message, stream, queue, or payload | Every bound is an explicit `GatewayConfig` value; an over-bound item is rejected before allocation/emission. |
| `T31-XB-5` Deadline vs wall clock | the accepted T025 time authority and declared deadlines | ambient wall-clock time | A verdict depends only on declared values and the injected time authority, never on an ambient clock. |
| `T31-XB-6` Flow control vs data plane | a bounded per-session in-flight queue and rate | unbounded memory growth or unbounded blocking | Saturation rejects deterministically, is counted, and never blocks the normal data plane without bound. |
| `T31-XB-7` Cleanup vs success | deterministic close/drain/revoke/release/quarantine and explicit incomplete/failed outcomes | an unknown outcome reported as success | Disconnect/expiry cleanup ends every pending request explicitly; unknown is never success. |
| `T31-XB-8` Logs vs content | stable codes, phase, logical identity, size, timing | payload bytes, permit contents, unrestricted content | The bounded log boundary records no payload and no permit content. |
| `T31-XB-9` Admitted envelope vs dependency growth | the T011-admitted tools, protobuf runtime, and accepted in-process libraries | any new admitted dependency or linked gRPC runtime | T031 adds no admitted dependency and links no gRPC runtime; the transport gap is recorded, not hidden. |
| `T31-XB-10` Predecessor vs candidate | accepted T007–T030 bytes, registers, ADRs, tests, provenance | a rewrite, weakening, or unrecorded digest drift | Only the declared T031 paths change; inherited digests and the planned→established status are refreshed and recorded. |

### 3.3 Prohibited elements (must remain absent)

No TCP listener, `AF_INET`/`AF_INET6` socket, DNS, resolver, or TLS use; no external network peer, subprocess, or
separate process; no compiled or linked gRPC runtime; no new admitted dependency; no dashboard, storage,
query-presentation, or export primitive; no unbounded message, stream, deadline, queue, payload, or session; no
permit bypass; no payload or permit content in a log record; no ambient wall-clock-dependent verdict; no change to
an accepted predecessor `src/`, `tests/`, `xdl/`, or `docs/engineering/xcom/t0{07..30}/` byte other than the
additive `CMakeLists.txt` wiring and the status-only path reconciliation; no rewrite or weakening of an accepted
ADR, requirement, contract, schema, register, or REF-002 disposition; no acceptance or integration of the
candidate.

## 4. Components

`T31-*` names are local to this document; the accepted `XCOM-DU-020`, `XCOM-CMP-010`, `XCOM-XLC-002`, `XCOM-XB-008`,
and `XCOM-XB-010` identifiers are the authorized units/contracts.

### 4.1 New T031 components

- **`T31-CMP-CONFIG` Gateway configuration and bounds** (`tool_gateway.hpp`): `GatewayConfigInput`/`GatewayConfig`
  carry the explicit maximum message size, concurrent sessions/streams, pending requests, observation records, and
  payload bytes, plus the maximum deadline and session idle timeout. An illegal or unbounded configuration is
  rejected by `create()`.
- **`T31-CMP-SESSION` Gateway session core** (`tool_gateway.cpp`): one accepted peer session owns a per-session
  mutex, a bounded in-flight request queue, the negotiated protocol identity, and the deterministic
  disconnect/expiry cleanup. It maps each of the ten accepted operations onto the accepted in-process boundaries.
- **`T31-CMP-OPS` Operation handlers**: bounded adapters that map the T030 request/response messages onto the
  accepted T025 permit/session, T026 journal, T027 guard, T028 action path and lease registry, and T021–T024
  observation hub. They construct the accepted request types from the message fields; they define no new contract.
- **`T31-CMP-IPC` Bounded local-IPC endpoint and framing**: `LocalIpcChannel` (a bounded framed read/write seam used
  by the in-process tests) and `LocalIpcEndpoint` (the `AF_UNIX` host-protected realization). The framing is
  method-name-addressed with a bounded length prefix; its committed operation table is pinned to the T030 descriptor
  method set.
- **`T31-CMP-LOG` Safe log boundary**: `GatewayLogSink` and a bounded record type carrying code, phase, logical
  identity, size, timing, and outcome only.
- **`T31-CMP-TESTS` Gateway tests** (`tests/xcom/tool_gateway/gateway_*.cpp`): the six additive `t031-<kind>` suites
  and their bounded helper header.
- **`T31-CMP-BUILD`** (T012): the subtree warning-as-error rule and runtime-target inventory extended additively by
  one gateway library and six `t031-<kind>` test executables.
- **`T31-WP`** — the T031 repository-owned work-product set.

### 4.2 Consumed components (read-only)

- **`T31-CMP-T030`** — the accepted versioned contract and generated Protocol Buffers messages
  (`proto/xverse/xcom/v1/tool_gateway.proto`, `xverse_xcom_tool_gateway_proto`). Consumed read-only.
- **`T31-CMP-T025`–`T31-CMP-T028`** — accepted validation-permit/session/time-authority, journal, guard, and action
  path/lease contracts. Consumed read-only through their public headers; T031 redefines no accepted type.
- **`T31-CMP-T021`–`T31-CMP-T024`** — accepted bounded observation hub and tap policy. Consumed read-only.
- **`T31-CMP-T011`/`T31-CMP-T012`** — the admitted offline envelope and the subtree build/test contract. The
  runtime-target inventory is extended additively and declared; no rule is weakened.
- **`T31-CMP-PLAN`** — accepted `XCOM-XLC-002` locator and plan/graph digest identities consumed as opaque logical
  strings; T031 parses no XDL and no activation plan.

## 5. Data flow (ordered)

1. **Create the endpoint.** `LocalIpcEndpoint::create(config, local_path)` opens an `AF_UNIX` stream socket, binds it
   to a path under a restricted directory, applies restrictive socket-file permissions, and computes the bound
   capabilities. No `AF_INET`/`AF_INET6`, DNS, or TLS facility is referenced.
2. **Accept bounded peer sessions.** The endpoint accepts at most `max_concurrent_sessions` peers; the accept is
   bounded and non-blocking so it never blocks the normal data plane without bound.
3. **Read a bounded frame.** A frame is `uint32 total_length`, `uint16 method_name_length`, the exact T030 method
   name, and the serialized request message. A frame whose length exceeds `max_message_bytes` or whose method name
   is not in the committed operation table is rejected fail-closed before dispatch.
4. **Negotiate.** The session applies the production compatibility predicate: an unsupported major is rejected
   before any other operation; a supported major with a higher minor is accepted additively.
5. **Enforce the deadline.** The session converts the request's `deadline_millis` to an absolute due time using the
   accepted T025 time authority and rejects a request whose deadline exceeds the configured maximum.
6. **Enforce flow control.** A request is admitted only when the bounded per-session in-flight queue and rate have
   room; otherwise it is rejected deterministically and counted, with no unbounded memory and no unbounded block.
7. **Dispatch.** The operation handler maps the request onto the accepted in-process boundary: permit/session arm
   and revoke, guard/journal/action-path submission, exclusive generation-bound lease acquire/release, or bounded
   observation open/read/close. A rejection emits no normal-route item.
8. **Respond.** The response message is serialized and written as one bounded frame; a streaming read returns at
   most the granted number of record frames and then a bounded terminator.
9. **Log safely.** The safe log boundary receives a bounded record with code, phase, identity, size, timing, and
   outcome only; no payload or permit content is ever recorded.
10. **Clean up.** On peer disconnect, session idle timeout, or shutdown, the session closes observation handles,
    drains/revokes/releases/quarantines validation-owned resources per durable state, and ends pending requests as
    `evidence-incomplete` or `failed`; a subsequent operation is rejected.
11. **Wire additively.** The build registers one gateway library and six `t031-<kind>` test executables; the runtime
    inventory is extended by exactly the one gateway library.

## 6. Interfaces

### 6.1 Gateway public interface (`src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp`)

| Element | Contract |
| --- | --- |
| `GatewayConfigInput` / `GatewayConfig` | explicit bounds; `create()` rejects an illegal or unbounded configuration |
| `GatewayOutcome`, `GatewayPhase` | stable bounded vocabulary (`accepted`, `rejected`, `expired`, `failed`, `evidence_incomplete`) and phase (`negotiate`, `session`, `observation`, `stimulation`, `lease`, `query`, `transport`) |
| `GatewayLogRecord`, `GatewayLogSink` | bounded payload-free structured log record and its sink seam |
| `LocalIpcFrame` / `LocalIpcChannel` | bounded framed read/write seam; a bounded in-process channel realizes the tests |
| `LocalIpcEndpoint` | `AF_UNIX` host-protected endpoint; `create()` is the only bind path; no TCP |
| `GatewayDependencies` | non-owning references to the accepted in-process boundaries (permit/session, journal, guard, action path/lease registry, observation hub, safe log sink) |
| `GatewaySession` | one accepted peer session: negotiation, the ten operations, deadline/flow-control enforcement, `on_disconnect()`/`on_idle_tick()`, and a bounded snapshot |
| `GatewayOperationName` | the committed operation-name table pinned to the T030 descriptor method set |

Ownership/lifetime: the endpoint and session own their bounded state; `GatewayDependencies` holds non-owning
references that must outlive the session. Thread-safety: internally synchronized (one per-session mutex plus a
bounded queue); the endpoint poll is serialized by its caller. Failure: invalid, over-bound, expired, unauthorized,
or unsupported-version operations return stable outcomes without unrelated mutation and without emitting an item.

### 6.2 Consumed contract (read-only)

| Interface | Contract consumed (unchanged) |
| --- | --- |
| `xverse::xcom::tool_gateway_proto` (T030) | generated Protocol Buffers request/response messages and the `ToolGateway` service descriptor |
| T025 `Permit`, `SessionManager`, `SessionHandle`, `TimeAuthority` | validation permit/session lifecycle and the injected time authority |
| T026 `StimulationJournal` | journal-before-emission intent/outcome |
| T027 `StimulationGuard` | fail-closed pre-emission guard |
| T028 `StimulationActionPath`, `ServiceEmulationRegistry` | guarded emission and exclusive generation-bound lease |
| T021–T024 `ObservationHub`, `ObservationTapSpec`, `ObservationTapHandle` | bounded metadata-only observation |
| GTest (T025 test toolchain) | the accepted offline test framework |

## 7. Concurrency and resource bounds

| Aspect | T031 decision |
| --- | --- |
| Production footprint | one public header, one implementation source, one additive runtime library, six additive test executables, one test helper header |
| Build inventory | one runtime-target addition `xverse_xcom_tool_gateway`, declared in `XVERSE_XCOM_RUNTIME_TARGETS`; six additive `t031-<kind>` test targets (`session`, `bounds`, `lifecycle`, `local-ipc`, `negative`, `logging`) |
| Writers | one declared writer per artifact; the gateway owns its session state; the accepted boundaries own their own state |
| Threads | one per-session mutex plus a bounded queue; the endpoint is poll-driven by its caller; no unbounded thread or queue |
| Operations per case | finite and declared; every queue, frame scan, and record pull is bounded by a `GatewayConfig` value |
| Message and stream | every frame is bounded by `max_message_bytes`; every stream returns at most `max_observation_records`; concurrent sessions/streams are bounded |
| Payload | the gateway carries a declared bounded payload field; the tests retain no real payload byte and log records never contain payload |
| Wall-clock | no verdict depends on ambient wall-clock time; deadlines use the injected T025 time authority |
| I/O | the local-IPC suite binds one bounded `AF_UNIX` socket under a build-tree scratch directory; no network, DNS, TLS, subprocess, or legacy access |
| Determinism | the operation table, framing, bounds enforcement, and cleanup are deterministic for fixed inputs; repeated runs are equal |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Single contract realization | one gateway interface mapping the T030 messages/methods; no competing interface | `T031-SR-001`, `T031-SR-002`; CHK-03, CHK-04 |
| Fail-closed version negotiation | production compatibility predicate rejects an unsupported major before any operation | `T031-SR-003`; CHK-05 |
| Exact permit | every session/stimulation/lease operation requires the accepted permit; transport never authorizes | `T031-SR-004`, `T031-SR-009`; CHK-06, CHK-11 |
| Declared bounds | every message/stream/queue/record/payload bound is an explicit config value | `T031-SR-005`, `T031-SR-010`; CHK-07, CHK-12 |
| Deadlines | every unary request deadline is bounded and enforced against the accepted time authority | `T031-SR-006`; CHK-08 |
| Bounded flow control | bounded in-flight queue/rate; deterministic rejection; visible counters | `T031-SR-007`, `T031-SR-016`; CHK-09 |
| Local IPC only | `AF_UNIX`/`socketpair` only; no TCP/DNS/TLS; host-protected permissions | `T031-SR-008`, `T031-SR-009`; CHK-10, CHK-11, CHK-20 |
| Deterministic cleanup | disconnect/expiry closes, drains, revokes, releases, or quarantines; explicit incomplete/failed | `T031-SR-013`; CHK-16 |
| Safe logs | payload-free and permit-free bounded records | `T031-SR-014`; CHK-17 |
| Additive delivery | one declared inventory change; no existing target/test/label/value changed | `T031-SR-017`; CHK-19 |
| Offline safety | admitted libraries plus GTest only; no network/ambient/secret/process/legacy | `T031-SR-018`; CHK-20 |
| Governance and envelope honesty | registers re-validated; REF-002 unchanged; gRPC transport gap recorded | `T031-SR-019`, `T031-SR-021`; CHK-21 |

## 9. Consistency and constraints

- **Dependency direction preserved.** T031 consumes the accepted T007–T030 design and the T011 envelope; it
  introduces no dependency on a later slice, an external peer, or a legacy repository, and adds no admitted
  dependency.
- **Domain neutrality preserved.** Only generic X-COM vocabulary appears (gateway, session, observation,
  stimulation, lease, identity, generation, clock domain, deadline, bound, provenance); no automotive, product,
  protocol, or configuration primitive is introduced.
- **XDL centrality preserved.** T031 neither parses nor authors XDL; plan and graph digests enter only as opaque
  logical identity strings already bound by the accepted plan.
- **Logical/physical separation preserved.** The gateway carries logical identities only; the local socket is a
  realization detail and no address or port enters the accepted message contract.
- **Synthetic origin preserved.** Stimulation flows through the accepted guard/journal/action path, so accepted
  items keep their persistent synthetic provenance; T031 introduces no differently-classified origin.
- **Envelope honesty.** The gRPC transport runtime gap is recorded (`T031-GAP-01`) rather than hidden by a new
  dependency or a claim that a gRPC runtime is linked (`T031-SR-021`).
- **Ownership preserved.** Only the declared T031 paths change; every accepted production byte and existing test
  is preserved except the additive `CMakeLists.txt` wiring and the status-only path reconciliation.
- **Maturity preserved.** The slice implements the gateway session only; the separate-process client, reusable
  suites, second provider, executed evidence, and acceptance remain T032–T041.

## 10. Traceability

| Architecture element | T031 requirements |
| --- | --- |
| `T31-XB-1`, `T31-CMP-SESSION` | T031-SR-001, T031-SR-002, T031-SR-021 |
| `T31-XB-2`, `T31-CMP-IPC` | T031-SR-008 |
| `T31-XB-3`, `T31-CMP-OPS` | T031-SR-004, T031-SR-009, T031-SR-011, T031-SR-012 |
| `T31-XB-4`, `T31-CMP-CONFIG` | T031-SR-005 |
| `T31-XB-5` | T031-SR-006, T031-SR-016 |
| `T31-XB-6` | T031-SR-007, T031-SR-010 |
| `T31-XB-7` | T031-SR-013, T031-SR-015 |
| `T31-XB-8`, `T31-CMP-LOG` | T031-SR-014 |
| `T31-XB-9` | T031-SR-018, T031-SR-021 |
| `T31-XB-10`, `T31-CMP-BUILD`, `T31-WP` | T031-SR-017, T031-SR-019, T031-SR-020 |

## 11. Negative cases (architecture view)

Every boundary has a declared fail-closed behaviour and a negative-case owner; the executable cases are listed in
`verification-plan.md` §5.

| Boundary | Injected defect | Negative case |
| --- | --- | --- |
| `T31-XB-1` | define a competing gateway interface or reject a T030 method | NEG-01, NEG-10 |
| `T31-XB-2` | bind a TCP/`AF_INET` listener or use DNS/TLS | NEG-01 |
| `T31-XB-3` | let local access bypass the permit | NEG-03 |
| `T31-XB-4` | omit a bound or reject after allocation/emission | NEG-06 |
| `T31-XB-5` | decide on ambient wall-clock time | NEG-06 |
| `T31-XB-6` | grow memory or block the data plane without bound | NEG-06 |
| `T31-XB-7` | report an unknown outcome as success | NEG-04 |
| `T31-XB-8` | log a payload or permit content | NEG-08 |
| `T31-XB-9` | add an admitted dependency or link the gRPC runtime | NEG-07 |
| `T31-XB-10` | weaken an accepted requirement/test/register or promote a REF-002 target | NEG-09, NEG-10 |
| Governance | mark the checkbox in the plan stage or skip the inherited provenance refresh | NEG-10 |

## Successor disposition (T039 R3, recorded 2026-09-30)

The historical statements above remain evidence for the T031 local-IPC session slice at that
revision. The T039 successor adds a linked gRPC transport for the platform gateway component, so the
"links no gRPC runtime" restriction is superseded for that component only.

- `T31-XB-9` / `T031-GAP-01`: superseded for the linked gateway component. The separate
  `xverse_xcom_tool_gateway_grpc` adapter compiles and links the admitted gRPC runtime and both
  generated services; dependency admission records the admitted prefix and package manifest, and no
  network fetch or new third-party dependency is introduced.
- The in-process gateway core (`xverse_xcom_tool_gateway`) still links no gRPC runtime; the earlier
  in-process statements remain accurate for that target.
- The logical watch owner (F02) is a lifecycle association, not OS process authentication. Host
  permissions and the exact stimulation permit remain separate controls, and a running host action
  callback must still return before shutdown completes (F06).
- No accepted requirement, expected result, negative case, or REF-002 disposition is weakened, and no
  deferred REF-002 target is promoted.
