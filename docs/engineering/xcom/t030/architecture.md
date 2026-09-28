# T030 Architecture — Versioned gRPC/Protocol Buffers Tool API and Additive Evolution Rules

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T030 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → architecture |
| Revision | 1 (versioned external-tool contract slice) |
| Baseline revision | `80c236638e160c5e991e5a537e29d407e7462dc6` |
| Affected source paths | `proto/xverse/xcom/v1/tool_gateway.proto` (new); `tests/xcom/tool_gateway/**` (new); `src/xverse/xcom/CMakeLists.txt` (edit, additive generation + test registration + declared runtime-inventory change); engineering trace/validation records (new); inherited `engineering/trace/links.json` and `engineering/stage-results/*.json` digest refresh (implementation stage) |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json` (`XCOM-CMP-010` local tool gateway, `XCOM-XB-008`/`XCOM-XB-010` protobuf IPC boundaries, `XCOM-XLC-002` external-rpc contract); `docs/engineering/xcom/t010/unit-design.json` (`XCOM-DU-019` tool gateway Protocol Buffers API, `XCOM-DU-020`/`-021` planned); `docs/engineering/xcom/t007/architecture.md`; `docs/engineering/xcom/t008/architecture.md`; `specs/007-xcom-core/contracts/tool-gateway.md`; `specs/007-xcom-core/data-model.md`; `specs/007-xcom-core/plan.md`; `docs/engineering/xcom/build-environment.md`; `docs/engineering/xcom/dependency-lock.md`; ADR-0016, ADR-0018, ADR-0020 |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T030 is the **contract definition** of the gateway (`GW`) family. It authors no gateway behaviour: it defines the
versioned `XCOM-XLC-002` external-rpc contract (`XCOM-DU-019`), generates the C++ Protocol Buffers messages and the
gRPC stubs from that single source with the T011-admitted generator tools, and proves the contract with bounded
offline generated-contract tests. It is the contract half of `XCOM-CMP-010`; the gateway session is T031, the
synthetic client is T032, the reusable contract suites are T033, and the second provider is T034.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013/T-CORE contract + origin/diagnostic vocabulary (read-only)
   → T017–T020 XDL Profile + activation-plan digest binding (read-only)
   → T021–T024 observation boundary (read-only) → T025–T029 stimulation boundary (read-only)
   → T030 versioned external-tool contract + generated artifacts + contract tests (this slice)
   → T031 gateway session → T032 separate-process synthetic client → T033 reusable suites → T034 second provider
   → T035–T041 evidence/review/acceptance
```

T030 changes exactly one production artifact (`proto/…/tool_gateway.proto`), one additive production library
(`xverse_xcom_tool_gateway_proto`, generated), one additive test family, and shared build tracing. It changes no
accepted `src/` runtime source, no accepted test, target, label, command, or expected value, and no accepted register.

## 3. Boundary and context

### 3.1 System context

```text
   ┌────────────── accepted capability-007 anchors (read-only) ──────────────┐
   │  spec.md FR-011/012/013/015/016/018/020/021/022/023/025/026/027/028/029/ │
   │    030/032/034/035 · SC-011                                             │
   │  t009 XCOM-CMP-010 · XCOM-XB-008 · XCOM-XB-010 · XCOM-XLC-002           │
   │  t010 XCOM-DU-019 (tool gateway proto API)                              │
   │  tool-gateway contract: versioned service, bounds, additive evolution   │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ realized by
   ┌────────────────── T011 admitted offline envelope (read-only) ──────────────────┐
   │  protoc 3.12.4 · grpc_cpp_plugin 1.30.2 · libprotobuf.a                        │
   │  (gRPC generation tools available; gRPC runtime transitive libs out of envelope)│
   └──────────────────────────────────┬──────────────────────────────────────────────┘
                                      │ generates
   ┌──────────────────── T030 owned artifacts (this slice) ────────────────────────┐
   │  proto/xverse/xcom/v1/tool_gateway.proto   (single versioned source)           │
   │  build-tree tool_gateway.pb.{h,cc}         (compiled into the proto library)    │
   │  build-tree tool_gateway.grpc.pb.{h,cc}    (provenance-only; not linked)        │
   │  xverse_xcom_tool_gateway_proto (STATIC, generated message code)                │
   │  tests/xcom/tool_gateway/{contract,evolution,negative,provenance}_tests.cpp     │
   │  guarantee : pinned fields, reserved bands, forward-compatible wire contract    │
   └──────────────────────────────────┬──────────────────────────────────────────────┘
                                      ▼
        T031 gateway session · T032 synthetic client · T033 reusable suites · T034 second provider
```

T030 introduces no runtime transport, listener, server, client, or process. Its generated library contains only
Protocol Buffers message types plus the generated service descriptor metadata; the gRPC stubs are generated for
provenance but are not compiled or linked because the admitted envelope cannot supply the gRPC runtime's transitive
libraries (`T030-GAP-02`).

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T30-XB-1` Contract vs implementation | the `.proto` schema, the generated messages, and the service descriptor | the gateway session, client, and any runtime transport | T030 defines and proves the contract only; it implements no gateway behaviour (T031+) and links no transport runtime. |
| `T30-XB-2` Versioned identity vs ambient | the explicit `package xverse.xcom.v1` and `ProtocolVersion` | an implicit or ambient protocol assumption | Every negotiation is by declared major/minor; an unsupported major is rejectable fail-closed, not inferred. |
| `T30-XB-3` Logical identity vs transport | logical session/permit/plan/endpoint/generation/route/contract identities | any address, port, socket, host, DNS, TLS, or credential primitive | The schema carries logical identities only; a transport-shaped field fails the contract tests. |
| `T30-XB-4` Bounds vs unbounded | declared `max_message_bytes`, `max_concurrent_streams`, deadlines, record/queue, payload, and lease bounds | an implicit or unbounded message, stream, deadline, or payload | Every bound is an explicit schema field; a payload-bearing message must declare its size bound. |
| `T30-XB-5` Additive evolution | pinned field numbers/names, reserved extension bands, forward-compatible unknown fields and enums | renumbering, reuse, silent removal, or a breaking rename | The contract tests pin the field manifest and reserved bands; unknown fields and unmapped enums survive a proto3 round trip. |
| `T30-XB-6` Generated source vs committed source | the committed `.proto` and the committed generated-code provenance record | the build-tree generated `.pb.*`/`.grpc.pb.*` outputs | The committed source of truth is the `.proto`; generated outputs are reproducible build-tree artifacts bound to generator identity. |
| `T30-XB-7` T030 scope vs later tasks | the schema, generated messages, and descriptor tests | the gateway, separate process, reusable suites, and delivery evidence | T030 implements no gateway, IPC listener, separate process, reusable suite, benchmark, or sanitizer/Doxygen execution. |
| `T30-XB-8` Repository vs environment | commit-safe schema, provenance, tests, and work products | admitted build inputs, host environment, payloads | Committed files are public-safe and offline; T030 performs no network, ambient/secret, dynamic-load, subprocess, or legacy access and logs no payload. |
| `T30-XB-9` Admitted envelope vs dependency growth | the T011-admitted `protoc`, `grpc_cpp_plugin`, and `libprotobuf.a` | any new admitted dependency or network fetch | T030 adds no admitted dependency and resolves no network resource; the gRPC runtime envelope gap is recorded, not worked around. |
| `T30-XB-10` Predecessor vs candidate | the accepted T007–T029 bytes, registers, ADRs, tests, and provenance | a rewrite, weakening, or unrecorded digest drift | Only the declared T030 paths change; the inherited provenance digests are refreshed and recorded. |

### 3.3 Prohibited elements (must remain absent)

No gateway server, socket, listener, IPC endpoint, or separate process; no compiled or linked gRPC runtime; no
dashboard, storage, query-presentation, or export primitive; no address, port, socket, DNS, TLS, credential, or host
field in the schema; no renumbering, field reuse, or removal without reservation; no unbounded message, stream,
deadline, queue, or payload; no network/socket/TLS/resolver, ambient/secret, dynamic-load, subprocess, or legacy
repository/binary access; no new admitted dependency; no wall-clock-dependent verdict; no change to an accepted
predecessor `src/`, `tests/`, `xdl/`, or `docs/engineering/xcom/t0{07..29}/` byte; no rewrite or weakening of an
accepted ADR, requirement, contract, schema, register, or REF-002 disposition. These inherit the T007 global
prohibitions, the T011 envelope, the T012 build contract, ADR-0016, ADR-0018, ADR-0020, and the constitution.

## 4. Components

`T30-*` names are local to this document; the accepted `XCOM-DU-019`, `XCOM-CMP-010`, `XCOM-XLC-002`, `XCOM-XB-008`,
and `XCOM-XB-010` identifiers are the authorized units/contracts.

### 4.1 New T030 components (one production artifact family + tests)

- **`T30-CMP-CONTRACT` Versioned tool contract** (`proto/xverse/xcom/v1/tool_gateway.proto`): the single versioned
  external-tool API — `package xverse.xcom.v1`, `syntax = "proto3"`, the `ToolGateway` service, the negotiation,
  observation, session, stimulation, lease, outcome/counter, and diagnostic messages/enums, all bounds, and the
  reserved extension bands. Payload-free at rest (it declares a bounded optional payload view; it stores no payload).
- **`T30-CMP-GEN` Generated contract artifacts** (`xverse_xcom_tool_gateway_proto`, build-tree `tool_gateway.pb.{h,cc}`
  and provenance-only `tool_gateway.grpc.pb.{h,cc}`): the Protocol Buffers message code generated by the admitted
  `protoc` and compiled against the admitted `libprotobuf.a`, plus the not-linked gRPC stub provenance. Owns the
  generated-code provenance contract (input schema identity, generation command, generator identity, output digests).
- **`T30-CMP-CONTRACT-TESTS` Generated-contract tests** (`tests/xcom/tool_gateway/`): the four additive suites and
  their bounded helper header, linking the generated messages and GTest only.
- **`T30-CMP-BUILD`** (T012): the subtree warning-as-error rule and runtime-target inventory extended additively by
  one generated-code library and four `t030-<kind>` test executables.
- **`T30-WP`** — the T030 repository-owned work-product set.

### 4.2 Consumed components (read-only)

- **`T30-CMP-T011`** — the admitted offline envelope: `protoc` 3.12.4 and `grpc_cpp_plugin` 1.30.2 generation tools,
  `libprotobuf.a`, headers, and the generated-code provenance policy. Consumed read-only; not modified.
- **`T30-CMP-T012`** — the subtree build/test contract and warning-as-error rule. The runtime-target inventory is
  extended additively and declared; no rule is weakened.
- **`T30-CMP-T013`** — accepted T-CORE diagnostic/identity vocabulary. The contract uses consistent diagnostic field
  semantics; no accepted type is redefined.
- **`T30-CMP-PLAN`** — accepted `XCOM-XLC-002` external-rpc contract locator and the accepted plan digest identity
  consumed as an opaque logical identity in the session/lease messages; no XDL or plan byte is parsed by T030.

## 5. Data flow (ordered)

1. **Author the contract.** One committed `.proto` declares the versioned package, service, messages, enums, bounds,
   and reserved bands.
2. **Generate.** The build runs the admitted `protoc` (Protocol Buffers messages) and the admitted
   `grpc_cpp_plugin` (gRPC stubs) over the committed schema; the Protocol Buffers message code is compiled into
   `xverse_xcom_tool_gateway_proto`.
3. **Record provenance.** The input schema identity, generation command, generator identity, and output digests are
   recorded for the exact candidate revision.
4. **Open the descriptor.** Each contract test resolves the generated `FileDescriptor` for the tool-gateway file and
   asserts package, syntax/version, service, methods, request/response types, streaming flags, and message vocabulary.
5. **Assert the bounds.** The tests assert every declared bound field exists with the declared type and is referenced
   by a payload-bearing message.
6. **Assert domain neutrality.** The tests scan every field name/type for forbidden transport, address, port, socket,
   DNS, TLS, credential, or export shapes and fail closed on any match.
7. **Pin additive evolution.** The tests compare the live descriptor against the committed field manifest and reserved
   bands, and assert no field number is renumbered, reused, or removed.
8. **Prove forward compatibility.** The tests serialize a message with an extra unknown field and an unmapped enum
   value and assert the value survives a proto3 round trip.
9. **Prove version negotiation.** The tests assert the `ProtocolVersion` fields and exercise a bounded test-local
   fail-closed compatibility predicate for an unsupported major version.
10. **Inspect the generated source.** The provenance tests assert the generated Protocol Buffers header carries the
    admitted protobuf runtime version and the generated gRPC header declares the `ToolGateway` service and its
    methods.
11. **Wire additively.** The build registers one generated-code library and four `t030-<kind>`-labelled test
    executables; the runtime-target inventory is extended by exactly the one generated library.

## 6. Interfaces

T030 exposes no in-process production interface. Its production interface is the external RPC contract; its test
interface is the generated descriptor.

### 6.1 External RPC contract (`proto/xverse/xcom/v1/tool_gateway.proto`)

| Element | Contract |
| --- | --- |
| `package` / `syntax` | `xverse.xcom.v1` / `proto3`; the single version source |
| `ProtocolVersion` | `major`, `minor` |
| `GatewayCapabilities` | protocol, bounded `Capability` list, `max_message_bytes`, `max_concurrent_streams`, `max_deadline_millis`, reserved band |
| `ToolGateway` service | `QueryVersion`, `OpenObservation`, `ReadObservations` (server streaming), `CloseObservation`, `ArmSession`, `RevokeSession`, `SubmitStimulation`, `AcquireLease`, `ReleaseLease`, `QuerySession` |
| Observation | `ObservationFilter`, `Identity`, `ObservationRecord`, `PayloadState`, open/read/close messages with declared record/queue bounds; metadata-only default |
| Session | `ArmSession{Request,Response}`, `RevokeSession{Request,Response}`, `SessionState`; exact permit/session/plan/graph identity; no permit-bypass field |
| Stimulation | `SubmitStimulation{Request,Response}`, `StimulationAction`, `StimulationActionKind`, `InteractionKind`, `Direction`, `Schedule`, `ScheduleMode`, `StimulationOutcome`, `StimulationOutcomeKind` |
| Lease | `AcquireLease{Request,Response}`, `ReleaseLease{Request,Response}`, `LeaseState`; exact session/endpoint/generation/plan identity |
| Query | `QuerySession{Request,Response}`, `SessionCounters`, explicit evidence-incomplete state |
| Diagnostic | `Diagnostic`, `Severity`; stable code/phase/identity/reason/correction |
| Evolution | every message declares `reserved 1000 to 1999;`; field numbers/names pinned; removed fields must be reserved |

### 6.2 Test-local helpers (`tests/xcom/tool_gateway/contract_support.hpp`)

| Element | Contract |
| --- | --- |
| `field_manifest()` | bounded, committed `message → {number → name}` map used to pin additive evolution; payload-free |
| `reserved_bands()` | bounded expected reserved ranges per message |
| `forbidden_shapes()` | bounded list of forbidden field-name/type fragments (transport/address/port/socket/DNS/TLS/credential/export) |
| `is_supported_protocol_version(...)` | bounded test-local fail-closed predicate mirroring the documented major-version rule; not production behaviour |
| helpers | bounded `find_message`, `find_service`, `find_method`, `field_names` accessors over the generated descriptor |

Ownership/lifetime: the helpers own only bounded constants and descriptor views; the generated descriptor is a
process-lifetime read-only static. Thread-safety: single-threaded tests; the generated descriptor is read-only.
Bounds: see §7.

### 6.3 Consumed contract (read-only)

| Interface | Contract consumed (unchanged) |
| --- | --- |
| `protobuf::protoc` (T011) | admitted `protoc` 3.12.4 used to generate the message code at build time |
| `gRPC::grpc_cpp_plugin` (T011) | admitted `grpc_cpp_plugin` 1.30.2 used to generate the gRPC stubs (provenance-only) |
| `protobuf::libprotobuf` (T011) | admitted Protocol Buffers runtime linked by the generated-message library and tests |
| GTest (T025 test toolchain) | the accepted offline test framework |

## 7. Concurrency and resource bounds

| Aspect | T030 decision |
| --- | --- |
| Production footprint | one committed `.proto`, one generated-code static library, four additive test executables, one test helper header |
| Build inventory | one runtime-target addition `xverse_xcom_tool_gateway_proto`, declared in `XVERSE_XCOM_RUNTIME_TARGETS`; four additive `t030-<kind>` test targets for the four test kinds (`contract`, `evolution`, `negative`, `provenance`) |
| Writers | one declared writer per artifact; the generated library and descriptor are read-only at test time |
| Threads in tests | 1 (no concurrency case; the contract is immutable static data) |
| Operations per case | finite; each descriptor scan is bounded by the fixed message/field counts |
| Unknown-field probe | one bounded byte buffer with a fixed extra tag and value |
| Generation | one `protoc` message generation and one gRPC stub generation per build; deterministic outputs for a fixed schema and generator |
| Payload | the schema declares bounded payload fields but the tests retain no real payload byte; probe payloads are fixed and synthetic |
| Wall-clock | no case depends on wall-clock timing; every deadline/bound is a declared field value |
| I/O | build-time generation from the committed schema; tests read no production filesystem path and use the in-memory descriptor |
| Determinism | the descriptor and generated sources are deterministic for the fixed schema and generator; repeated runs are equal |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Versioned identity | explicit package and `ProtocolVersion`; fail-closed unsupported-major rule | T030-SR-001, T030-SR-003; CHK-01, CHK-05, CHK-14 |
| Complete service surface | every accepted tool-gateway operation declared with exact request/response/streaming | T030-SR-002, T030-SR-016; CHK-04 |
| Domain neutrality | logical identities only; forbidden transport/address/port/export shapes fail the tests | T030-SR-011; CHK-13 |
| Declared bounds | every enforced bound is an explicit schema field | T030-SR-010; CHK-12 |
| Additive evolution | pinned field manifest, reserved bands, forward-compatible unknown fields/enums | T030-SR-012, T030-SR-013; CHK-14, CHK-15 |
| Generated provenance | admitted generator, recorded command/identity/output digests | T030-SR-014; CHK-16 |
| Additive delivery | one declared inventory change; no existing target/test/label/value changed | T030-SR-015; CHK-17 |
| Offline safety | admitted headers/tools plus GTest only; no network/ambient/secret/process/legacy; no real payload | T030-SR-017; CHK-18 |
| Public safety | no secret, private address, real payload, or host path in committed files/evidence | T030-SR-018; CHK-19 |
| Governance | registers re-validated; REF-002 unchanged; maturity recorded honestly | T030-SR-019, T030-SR-020; CHK-20, CHK-21 |

## 9. Consistency and constraints

- **Dependency direction preserved.** T030 consumes the accepted T011 envelope and the accepted T007–T029 design; it
  introduces no dependency on a later slice, an external peer, or a legacy repository, and adds no admitted
  dependency.
- **Domain neutrality preserved.** Only generic X-COM vocabulary appears (gateway, observation, session, stimulation,
  lease, identity, generation, clock domain, deadline, bound, provenance); no automotive, product, protocol, or
  configuration primitive is introduced.
- **XDL centrality preserved.** T030 neither parses nor authors XDL; plan and graph digests enter the contract only as
  opaque logical identity strings already bound by the accepted plan.
- **Logical/physical separation preserved.** The contract carries logical identities only; no address, transport, or
  environment identity enters the schema.
- **Synthetic origin preserved.** The submission/observation messages carry the tool/session/request/correlation/
  causation identity fields that the accepted stimulation boundary already produces; T030 introduces no
  differently-classified origin.
- **Ownership preserved.** Only the declared T030 paths change; every accepted production byte and existing test is
  preserved.
- **Maturity preserved.** The slice defines the contract only; the gateway, client, reusable suites, executed
  evidence, and acceptance remain T031–T041.
- **Envelope honesty.** The gRPC runtime linkage gap is recorded (`T030-GAP-02`) rather than hidden by a workaround or
  a new dependency.

## 10. Traceability

| Architecture element | T030 requirements |
| --- | --- |
| `T30-XB-1`, `T30-CMP-WP`, `T30-CMP-BUILD` | T030-SR-015, T030-SR-019, T030-SR-020 |
| `T30-XB-2`, `T30-CMP-CONTRACT` | T030-SR-001, T030-SR-003 |
| `T30-XB-3` | T030-SR-011 |
| `T30-XB-4` | T030-SR-010 |
| `T30-XB-5`, `T30-CMP-CONTRACT-TESTS` | T030-SR-012, T030-SR-013, T030-SR-016 |
| `T30-XB-6`, `T30-CMP-GEN` | T030-SR-014 |
| `T30-XB-7`, `T30-CMP-CONTRACT` | T030-SR-002, T030-SR-004, T030-SR-005, T030-SR-006, T030-SR-007, T030-SR-008, T030-SR-009 |
| `T30-XB-8` | T030-SR-017, T030-SR-018 |
| `T30-XB-9` | T030-SR-014, T030-SR-017 |
| `T30-XB-10` | T030-SR-019, T030-SR-020 |

## 11. Negative cases (architecture view)

Every boundary has a declared fail-closed behaviour and a negative-case owner; the executable cases are listed in
`verification-plan.md` §5.

| Boundary | Injected defect | Negative case |
| --- | --- | --- |
| `T30-XB-1` | T030 either implements a gateway/client or changes a predecessor byte | NEG-01, NEG-10 |
| `T30-XB-2` | negotiate implicitly or accept an unsupported major version | NEG-04, NEG-05 |
| `T30-XB-3` | add an address/port/socket/DNS/TLS/credential/export field | NEG-01, NEG-02, NEG-03 |
| `T30-XB-4` | declare an unbounded payload/stream/deadline or omit a bound | NEG-06 |
| `T30-XB-5` | renumber/reuse a field, drop a reserved band, or break unknown-field/enum round-trip | NEG-04, NEG-05 |
| `T30-XB-6` | commit a generated file as source of truth or lose generation provenance | NEG-07 |
| `T30-XB-7` | T030 implements T031–T041 | NEG-01, NEG-10 |
| `T30-XB-8` | commit a secret, private address, real payload, or host path | NEG-08 |
| `T30-XB-9` | add an admitted dependency or fetch over the network | NEG-07 |
| `T30-XB-10` | weaken an accepted requirement/test/register or promote a REF-002 target | NEG-09, NEG-10 |
| Governance | mark the checkbox in the plan stage or skip the inherited provenance refresh | NEG-10 |
