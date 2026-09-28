# T032 Detailed Design — Separate-Process Synthetic Client and Generated-Client Contract Tests

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T032 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → detailed design |
| Revision | 1 (separate-process synthetic-client conformance slice) |
| Baseline revision | `e6197c67868213ffb6523d8bf62ed4c2c4e3b0af` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

T032 realizes the accepted `XCOM-DU-021` separate-process synthetic tool client against the accepted T031 gateway and
the T030 generated contract, and proves it with five additive `t032-<kind>` suites. It authors no reusable contract
suite (T033) and no second provider (T034). The design is written **before** implementation; the implementation must
realize it exactly or record a design change and re-review.

## 2. Design decisions

| ID | Decision | Rationale | Requirement |
| --- | --- | --- | --- |
| `T32-DD-01` | Realize the T030 generated messages and method names over the accepted T031 bounded, host-protected `AF_UNIX` framing; bind the client method table 1:1 to the generated `ToolGateway` service descriptor method set | The admitted envelope cannot link the gRPC runtime (`T030-GAP-02`, `T031-GAP-01`); the generated message/method contract is preserved and no competing interface is created | T032-SR-001, T032-SR-002, T032-SR-017 |
| `T32-DD-02` | The client is its own OS process launched by the tests with an explicit bounded argv and a scrubbed admitted environment | `SC-011` requires a separate-process synthetic client; no ambient/secret/legacy/external access is permitted | T032-SR-003 |
| `T32-DD-03` | The client connects only to a host-protected `AF_UNIX` endpoint; the endpoint family is asserted at runtime and the source is scanned to fail closed on TCP/DNS/TLS | `XCOM-INV-13`; the client must expose no TCP listener | T032-SR-004 |
| `T32-DD-04` | Observation is bounded open/read/close with metadata-only records and delivered/dropped counters | `FR-011`–`FR-013`; the accepted observation policy is metadata-only by default | T032-SR-005, T032-SR-006 |
| `T32-DD-05` | Each of the four allowed stimulation actions is submitted through the accepted guard/journal/action path with persistent synthetic provenance | `FR-015`/`FR-017`/`FR-018`/`FR-021`, `SC-007`; all four actions must be demonstrated | T032-SR-007 |
| `T32-DD-06` | The lease is acquired and released through the client as the accepted exclusive generation-bound lease | `FR-034`; lease conflicts are reported without ambiguous ownership | T032-SR-008 |
| `T32-DD-07` | An invalid or expired session emits zero normal-route items and the client reports a non-success outcome | `FR-016`/`FR-021`, `SC-011` | T032-SR-009 |
| `T32-DD-08` | The production compatibility predicate rejects an unsupported major before any other operation | `FR-032` fail-closed negotiation | T032-SR-010 |
| `T32-DD-09` | Every client bound (maximum message size, per-request deadline, transport timeout) is an explicit configuration value | `FR-007`/`FR-013`; no implicit or unbounded bound | T032-SR-011 |
| `T32-DD-10` | Failure, timeout, and disconnect-after-intent report stable non-success outcomes; unknown is never success | `FR-010`/`FR-021` | T032-SR-012 |
| `T32-DD-11` | The client and tests record stable codes/phase/identity/size/timing/outcome only | `FR-027`; payload/permit/secret/private-address/host-path are excluded | T032-SR-013 |
| `T32-DD-12` | Add one fixture executable and five `t032-<kind>` test targets, additively; the runtime-target inventory is unchanged | T012 build contract; a fixture executable is not a runtime library | T032-SR-016 |
| `T32-DD-13` | Link only the standard library, the T030 generated messages, the accepted T031/T021–T029 libraries, and GTest | Offline/no-new-dependency rule; no gRPC runtime | T032-SR-017 |
| `T32-DD-14` | Keep the T032 suites T032-local; do not abstract them into the T033 reusable suite and do not add a second provider | ADR-0020 task ownership; additivity | T032-SR-020 |

## 3. Synthetic-client interface (`src/xverse/xcom/fixtures/synthetic_tool.cpp`)

The implementation authors the interface below. The fixture source carries the X-COM Doxygen file block (`@file`,
`@brief`, `@ingroup xcom_gw`) and documents its bounded public seam with `@brief`, `@ownership`, `@lifetime`,
`@thread_safety`, and `@failure` tags (accepted `XCOM-DU-021` obligation). The listing is illustrative; the
authoritative content is the accepted generated contract and the accepted T031 gateway interface.

```cpp
namespace xverse::xcom::synthetic {

// 1. Explicit bounded client configuration.
struct SyntheticClientConfig final {
  std::size_t   max_message_bytes;      // bounded frame size, <= gateway bound
  std::uint64_t request_deadline_millis;
  std::uint64_t transport_timeout_millis;
};
[[nodiscard]] std::optional<SyntheticClientConfig>
make_client_config(std::string_view args) noexcept;   // rejects illegal/unbounded

// 2. Bounded machine-readable result line (logical identity only).
struct SyntheticClientResult final {
  std::string_view method;      // exact T030 ToolGateway method name
  std::string_view outcome;     // stable non-success/success code
  std::uint64_t size{0U};       // bounded byte/record count
  std::uint64_t timing{0U};     // declared tick/millis
};

// 3. Bounded AF_UNIX connect/read/write seam (the only client transport).
class LocalClientChannel final {
 public:
  static std::optional<LocalClientChannel> connect(std::string_view local_path) noexcept;
  [[nodiscard]] bool is_local_unix() const noexcept;   // true only when AF_UNIX
  std::size_t read(std::span<std::byte>) noexcept;
  std::size_t write(std::span<const std::byte>) noexcept;
};

// 4. The single bounded entry point.
//    argc/argv: <local_path> <exercise-mode> [declared bounds]
[[nodiscard]] int synthetic_client_run(int argc, char **argv) noexcept;

// 5. Committed client operation table, pinned to the generated descriptor method set.
[[nodiscard]] std::span<const std::string_view> synthetic_client_operation_names() noexcept;

}  // namespace xverse::xcom::synthetic
```

The generated Protocol Buffers types are named by their T030 package (`xverse::xcom::v1`); the fixture includes the
generated `tool_gateway.pb.h` through the generated-target include directory. The client reuses the accepted T031
request-frame layout so it introduces no competing transport vocabulary.

## 4. Exercise mapping (client exercise → accepted operation)

Each exercise maps one accepted T030 method onto the accepted T031 operation and delegates to the accepted in-process
boundaries in the parent harness. No accepted type is redefined, and no alternative identity/digest/diagnostic
vocabulary is introduced.

| Exercise | T030 method (exact) | Parent delegation | Notes |
| --- | --- | --- | --- |
| version | `QueryVersion` | `GatewaySession` + production predicate | returns `ProtocolVersion{major=1, minor=0}`; the client also asserts its method table equals the generated descriptor |
| observe-open | `OpenObservation` | `ObservationHub::attach` with `ObservationTapSpec` | metadata-only tap with payload exposure off; grants a bounded stream identity |
| observe-read | `ReadObservations` | `ObservationHub::poll` + `snapshot` | at most `max_observation_records` metadata-only records, then a bounded terminator |
| observe-close | `CloseObservation` | `ObservationHub::detach` + `snapshot` | returns delivered/dropped counters |
| arm | `ArmSession` | accepted T025 `Permit` + `SessionManager` | validates permit/session/plan/graph/protocol/validity |
| stimulate | `SubmitStimulation` | `StimulationGuard` + `StimulationJournal` + `StimulationActionPath` | all four allowed actions; accepted items carry persistent synthetic provenance |
| lease | `AcquireLease` / `ReleaseLease` | `ServiceEmulationRegistry` | exclusive, generation-bound; conflict reported without ambiguous ownership |
| query | `QuerySession` | `SessionManager::snapshot` | bounded counters including an explicit evidence-incomplete count |

A request that cannot map onto an accepted boundary (for example an unsupported combinatorial action) returns a
stable rejection and emits nothing.

## 5. Separate-process exchange and framing

T032 reuses the accepted T031 request-frame layout exactly; it defines no new transport and no competing interface.
A request frame is:

```text
uint32  total_length        (big-endian, excludes this prefix)
uint16  method_name_length  (big-endian)
bytes   method_name         (UTF-8, exactly one T030 RPC name)
bytes   request_message     (serialized T030 request message)
```

A response frame is `uint32 total_length` followed by the serialized response message. A `ReadObservations` exercise
returns at most the granted number of metadata-only record frames and then one bounded terminator frame (zero length).
Rules:

- `total_length` greater than the client's and gateway's configured maximum message size is rejected fail-closed
  before any allocation or dispatch (`T32-TS-020`).
- A `method_name` not present in the committed operation table is rejected fail-closed.
- The client operation table is committed in the fixture and asserted equal to the generated `ToolGateway` service
  descriptor method set in order; a mismatch fails the contract case, binding the framing 1:1 to the accepted contract
  (`T032-SR-002`, `T032-SR-017`) and introducing no competing method vocabulary.

**Launch protocol.** The launcher starts the fixture executable with an explicit bounded argument vector
(`local_path`, `exercise`, `max_message_bytes`, `request_deadline_millis`, `transport_timeout_millis`) and a scrubbed
environment: the fixture path and scratch directory are supplied only as bounded build-time compile definitions, and
no ambient/secret value is inherited. The parent then serves exactly one peer through the accepted `LocalIpcEndpoint`;
the harness and the client each perform only bounded reads/writes. The parent reaps the child within a bounded wait.

## 6. Host protection and no-TCP proof

- The parent binds one socket with the accepted `LocalIpcEndpoint::create` (`AF_UNIX` only) under a restricted
  directory with `0600` socket-file permissions; `is_local_unix()`/`family()` are asserted.
- The client connects with the same local path; it references no `AF_INET`/`AF_INET6`, `getaddrinfo`, resolver, or TLS
  facility. A source scan over the client fixture fails closed on any forbidden token, and the runtime family
  assertion fails closed on a non-local family.
- The scratch socket path is never printed into public evidence.

## 7. Bounds, deadline, and failure semantics

- **Message bound.** A frame over the configured maximum message size is rejected before allocation or dispatch.
- **Deadline.** Each request carries `deadline_millis`; a request over the configured maximum is rejected, and the
  gateway enforces the deadline against the accepted T025 time authority (never an ambient wall clock).
- **Transport timeout.** The client's bounded transport wait declares an explicit timeout; an exhausted wait reports
  `failed`, never success.
- **Failure table.**

| Event | Client report | Gateway effect | Log |
| --- | --- | --- | --- |
| peer failure / transport timeout | `failed` | pending request ends explicit | transport/`failed` |
| disconnect after an intent | `evidence_incomplete` | drain/revoke/release/quarantine | transport/`evidence_incomplete` |
| expired session | `expired` | zero normal-route items | session/`expired` |
| invalid/substituted permit | `rejected` | zero normal-route items | session/`rejected` |
| unsupported major | `rejected` | rejected before any other operation | negotiate/`rejected` |
| over-bound frame or deadline | `rejected` | rejected before allocation/dispatch | transport/`rejected` |

An unknown outcome is never recorded or returned as success.

## 8. Test design

All suites live under `tests/xcom/tool_gateway/` and use only the standard library, the generated messages, the
accepted T031/T021–T029 libraries, and GTest. `synthetic_client_support.hpp` provides the bounded test-local server
harness, the separate-process launcher, and the bounded result parser; it retains no payload byte and never prints a
host path.

### 8.1 `synthetic_client_observation_tests.cpp` — `XcomSyntheticClientObservation` (`t032-observation`)

| Unit case | Assertion |
| --- | --- |
| `T32-TS-001 ClientProcessQueryVersion` | the client in a separate process negotiates the supported protocol and reports a bounded version result; the run is deterministic and bounded |
| `T32-TS-002 ClientOpensBoundedObservationStream` | `OpenObservation` through the local endpoint grants a bounded stream identity |
| `T32-TS-003 ClientReadsMetadataOnlyRecords` | `ReadObservations` returns at most the granted number of metadata-only records before the deadline |
| `T32-TS-004 ClientClosesStreamWithCounters` | `CloseObservation` returns delivered and dropped counters |
| `T32-TS-005 ClientObservesEmittedTraffic` | a stimulated item the gateway emits is observed by the client as one metadata-only record |

### 8.2 `synthetic_client_stimulation_tests.cpp` — `XcomSyntheticClientStimulation` (`t032-stimulation`)

| Unit case | Assertion |
| --- | --- |
| `T32-TS-006 ClientInjectsSignal` | the client submits signal injection and observes an emitted outcome |
| `T32-TS-007 ClientInjectsMessage` | the client submits message injection and observes an emitted outcome |
| `T32-TS-008 ClientInvokesService` | the client submits service invocation and observes an emitted outcome |
| `T32-TS-009 ClientEmulatesService` | the client submits bounded service emulation and observes an emitted outcome |
| `T32-TS-010 ClientAcquiresAndReleasesLease` | the client acquires and releases the accepted exclusive generation-bound lease |

Each emitted item carries persistent synthetic provenance (asserted on the accepted item/emitter fixture).

### 8.3 `synthetic_client_contract_tests.cpp` — `XcomSyntheticClientContract` (`t032-contract`)

| Unit case | Assertion |
| --- | --- |
| `T32-TS-011 ClientUsageCarriesNoPayloadOrPermitSecret` | the captured client result lines and harness records contain no payload byte and no permit content |
| `T32-TS-012 GeneratedRequestRoundTripsThroughClient` | a generated request message round-trips through the client exchange unchanged |
| `T32-TS-013 UnknownFieldSurvivesClientRoundTrip` | an unknown field survives a proto3 client round trip unchanged |
| `T32-TS-014 ClientOperationTableMatchesGeneratedDescriptor` | the committed client operation table equals the generated `ToolGateway` service descriptor method set in order |

### 8.4 `synthetic_client_negative_tests.cpp` — `XcomSyntheticClientNegative` (`t032-negative`)

| Unit case | Assertion |
| --- | --- |
| `T32-TS-015 NoTcpListenerForClientEndpoint` | the endpoint family is `AF_UNIX` only; no `AF_INET`/`AF_INET6` family is bound or contacted |
| `T32-TS-016 InvalidSessionEmitsZeroItems` | an invalid/substituted permit emits zero normal-route items |
| `T32-TS-017 ExpiredSessionEmitsZeroItems` | an expired session emits zero normal-route items |
| `T32-TS-018 UnsupportedMajorFailsClosed` | an unsupported major is rejected before any operation and emits no item |
| `T32-TS-019 ClientForbiddenApiScan` | the client fixture contains no `AF_INET`/`AF_INET6`, DNS, resolver, TLS, legacy, external-peer, or production-workload token |

### 8.5 `synthetic_client_bounds_tests.cpp` — `XcomSyntheticClientBounds` (`t032-bounds`)

| Unit case | Assertion |
| --- | --- |
| `T32-TS-020 MessageSizeBoundEnforced` | a frame over the configured maximum message size is rejected before dispatch |
| `T32-TS-021 DeadlineBoundEnforced` | a request over the configured maximum deadline is rejected with no emitted item |
| `T32-TS-022 TransportTimeoutBounded` | an exhausted transport wait reports a stable non-success outcome, never success |

## 9. Failure semantics

| Condition | Outcome |
| --- | --- |
| unsupported protocol major | rejected before any other operation, `T32-TS-018` |
| invalid/substituted permit | rejected with zero emitted items, `T32-TS-016` |
| expired session submission | zero normal-route items, `T32-TS-017` |
| over-bound frame or deadline | rejected before allocation/dispatch, `T32-TS-020`/`T32-TS-021` |
| exhausted transport wait | stable `failed`, never success, `T32-TS-022` |
| TCP/DNS/TLS attempt | source and runtime check fail closed; not attempted, `T32-TS-015`/`T32-TS-019` |
| unknown outcome | reported `evidence_incomplete`/`failed`, never success, `T32-TS-017`/`T32-TS-022` |
| client source unavailable to the scan | the forbidden-API case fails closed (`T32-TS-019`) |
| gRPC runtime link attempted | fails closed; not attempted by T032 (`T032-GAP-01`) |

## 10. Determinism and safety

- Every frame, read, queue, record pull, and wait step is finite and bounded by an explicit client or gateway
  configuration value; no case depends on ambient wall-clock time, randomness, or environment.
- The suites perform only a bounded `AF_UNIX` bind/connect/exchange under a build-tree scratch directory and one
  bounded launch of the owned fixture process; no network, DNS, TLS, dynamic load, legacy access, or production
  workload occurs.
- Committed files and evidence contain no credential, private address, real or proprietary payload, or
  environment-specific host path; result lines carry stable codes, phase, logical identity, size, timing, and outcome
  only.

## 11. Traceability

| Design element | Requirement | Unit cases |
| --- | --- | --- |
| `T32-DD-01` interface/contract | T032-SR-001, T032-SR-002, T032-SR-017 | `T32-TS-014` |
| `T32-DD-02` separate process | T032-SR-003, T032-SR-014 | `T32-TS-001` |
| `T32-DD-03` local transport | T032-SR-004 | `T32-TS-015`, `T32-TS-019` |
| `T32-DD-04` observation | T032-SR-005, T032-SR-006 | `T32-TS-002`…`T32-TS-005` |
| `T32-DD-05` stimulation | T032-SR-007 | `T32-TS-006`…`T32-TS-009` |
| `T32-DD-06` lease | T032-SR-008 | `T32-TS-010` |
| `T32-DD-07` invalid/expired | T032-SR-009 | `T32-TS-016`, `T32-TS-017` |
| `T32-DD-08` version | T032-SR-010 | `T32-TS-018` |
| `T32-DD-09` bounds | T032-SR-011 | `T32-TS-020`, `T32-TS-021` |
| `T32-DD-10` failure semantics | T032-SR-012 | `T32-TS-017`, `T32-TS-022` |
| `T32-DD-11` evidence safety | T032-SR-013 | `T32-TS-011` |
| generated message fidelity | T032-SR-015 | `T32-TS-012`, `T32-TS-013` |
| `T32-DD-12` build wiring | T032-SR-016 | build/discovery inspection (CHK-19) |
| `T32-DD-13` offline linkage | T032-SR-017 | `T32-TS-019` |
| `T32-DD-14` scope/handoff | T032-SR-020 | changed-path inspection (CHK-02, CHK-19) |
| work products/governance | T032-SR-018, T032-SR-019 | gate and validators (CHK-21, CHK-22) |
| documentation | T032-SR-021 | file-block inspection (CHK-03) |

## 12. Doxygen and documentation

- The new fixture source carries the X-COM file-block (`@file`, `@brief`, `@ingroup xcom_gw`) and documents its
  bounded public seam with `@brief`, `@ownership`, `@lifetime`, `@thread_safety`, and `@failure` tags, as accepted
  `XCOM-DU-021` requires.
- The test helper and suites carry the X-COM file-block tags required of changed test units.
- Generated Protocol Buffers documentation remains `DOX-GAP-02` (T037); T032 documents only the hand-written client
  seam.

## 13. Generated-code provenance and compatibility contract

- T032 adds **no** generated code. It consumes the T030-generated Protocol Buffers messages and service descriptor,
  whose committed input is `proto/xverse/xcom/v1/tool_gateway.proto` (SHA-256 recorded by the accepted T030
  provenance) and whose generator is the T011-admitted `libprotoc 3.12.4`. The generated outputs live under the
  git-ignored build tree and are regenerated by the offline build; the committed `.proto` remains the single source
  of truth. The implementation stage records the observed output digests and confirms they equal the accepted T030
  record byte-for-byte.
- **Compatibility contract.** T032 preserves the accepted `XCOM-XLC-002` additive evolution rules (immutable package
  and published field numbers/names; only additive fields/messages/enums/methods; unsupported major rejected
  fail-closed; higher minor additive; unknown field survives a proto3 round trip). `T32-TS-014` binds the client
  method table to the generated descriptor, and `T32-TS-013` proves unknown-field preservation through the client, so
  an accepted additive contract change is visible in the same change that updates the client. T032 defines no
  competing contract, RPC, or configuration language.

