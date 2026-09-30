# T031 Detailed Design — Bounded Local-IPC-Only Tool Gateway

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T031 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → detailed design |
| Revision | 1 (local-IPC gateway session slice) |
| Baseline revision | `4dded2317f895978cce0331ae88e34ac28b3a609` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

T031 realizes the accepted `XCOM-XLC-002` message and method contract as a bounded, host-protected local-IPC-only
gateway session. It authors no separate-process client, reusable contract suite, or second provider. The design is
written **before** implementation; the implementation must realize it exactly or record a design change and
re-review.

## 2. Design decisions

| ID | Decision | Rationale | Requirement |
| --- | --- | --- | --- |
| `T31-DD-01` | Realize the T030 messages and method names over a bounded, host-protected `AF_UNIX` local-IPC framing; the framing operation table is pinned 1:1 to the T030 descriptor method set | The admitted envelope cannot link the gRPC runtime (`T030-GAP-02`); the message/method contract is preserved and no competing interface is created | T031-SR-001, T031-SR-002, T031-SR-021 |
| `T31-DD-02` | One gateway public interface `tool_gateway.hpp` + `tool_gateway.cpp` | Matches accepted `XCOM-DU-020`/`XCOM-CMP-010`; one versioned realization | T031-SR-001 |
| `T31-DD-03` | A production fail-closed compatibility predicate rejects any unsupported protocol major before any other operation | `FR-032` fail-closed negotiation; closes the production half of `T030-GAP-03` | T031-SR-003 |
| `T31-DD-04` | Every session/stimulation/lease operation requires the exact accepted T025 permit; the transport is never authorization | `XCOM-INV-08`; local access is not stimulation authority | T031-SR-004, T031-SR-009 |
| `T31-DD-05` | All bounds are explicit `GatewayConfig` values; an over-bound item is rejected before allocation or emission | `FR-007`/`FR-013`; no implicit or unbounded bound | T031-SR-005, T031-SR-010 |
| `T31-DD-06` | Deadlines are evaluated against the accepted T025 time authority, not an ambient wall clock | `FR-020`/`FR-033`; deterministic verdicts | T031-SR-006, T031-SR-016 |
| `T31-DD-07` | A bounded per-session in-flight queue and rate with deterministic rejection and visible counters | `FR-007`; no unbounded memory or unbounded blocking | T031-SR-007, T031-SR-016 |
| `T31-DD-08` | Only `AF_UNIX`/`socketpair` may be bound; the endpoint family is asserted at runtime and the source is scanned to fail closed on TCP/DNS/TLS | `XCOM-INV-13`; the server must not bind a TCP address | T031-SR-008 |
| `T31-DD-09` | The endpoint socket lives in a restricted directory with restrictive file permissions | `contracts/tool-gateway.md` host protection | T031-SR-009 |
| `T31-DD-10` | The safe log boundary records code/phase/identity/size/timing/outcome only | `FR-027`; payload and permit content are never logged | T031-SR-014 |
| `T31-DD-11` | Disconnect/expiry cleanup closes, drains, revokes, releases, or quarantines and ends pending requests explicitly | `FR-010`/`FR-021`; unknown is never success | T031-SR-013, T031-SR-015 |
| `T31-DD-12` | Add one runtime-target library and six `t031-<kind>` test targets, additively | T012 build contract; a new target is declared explicitly | T031-SR-017 |
| `T31-DD-13` | Link only the standard library, the T030 generated messages, the accepted in-process boundaries, and GTest | Offline/no-new-dependency rule | T031-SR-018 |

## 3. Gateway interface (`src/xverse/xcom/include/xverse/xcom/tool_gateway.hpp`)

The implementation authors the interface below. The header exposes exactly seven documented public gateway elements,
each carrying Doxygen `@brief`, `@ownership`, `@lifetime`, `@thread_safety`, and `@failure` tags, in group
`xcom_gw` (accepted `XCOM-DU-020` obligation).

```cpp
namespace xverse::xcom {

// 1. Explicit bounded configuration.
struct GatewayConfigInput final {
  std::size_t     max_message_bytes;          // bounded frame size
  std::uint32_t   max_concurrent_sessions;
  std::uint32_t   max_streams_per_session;
  std::uint32_t   max_pending_requests;       // bounded in-flight queue
  std::uint64_t   max_deadline_millis;
  std::uint64_t   session_idle_timeout_millis;
  std::uint32_t   max_observation_records;
  std::size_t     max_payload_bytes;
};
class GatewayConfig final {
 public:
  static std::optional<GatewayConfig> create(const GatewayConfigInput&) noexcept;  // rejects illegal/unbounded
  // bounded accessors for every field above
 private:
  // ...
};

// 2. Stable outcome and phase vocabulary.
enum class GatewayOutcome : std::uint8_t {
  accepted, rejected, expired, failed, evidence_incomplete,
};
enum class GatewayPhase : std::uint8_t {
  negotiate, session, observation, stimulation, lease, query, transport,
};
[[nodiscard]] std::string_view to_string(GatewayOutcome) noexcept;
[[nodiscard]] std::string_view to_string(GatewayPhase) noexcept;

// 3. Bounded, payload-free structured log boundary.
struct GatewayLogRecord final {
  GatewayOutcome outcome{GatewayOutcome::accepted};
  GatewayPhase   phase{GatewayPhase::transport};
  std::string_view code;        // stable code
  std::string_view identity;    // logical identity only
  std::uint64_t size{0U};       // byte size, never the bytes
  std::uint64_t timing{0U};     // declared tick/millis, never an ambient timestamp
};
class GatewayLogSink {
 public:
  virtual ~GatewayLogSink() = default;
  virtual void record(const GatewayLogRecord&) noexcept = 0;
};

// 4. Bounded framed local-IPC channel seam (in-process realization for tests).
class LocalIpcChannel {
 public:
  virtual ~LocalIpcChannel() = default;
  virtual std::size_t read(std::span<std::byte> destination) noexcept = 0;   // at most destination.size()
  virtual std::size_t write(std::span<const std::byte> source) noexcept = 0;  // at most source.size()
};

// 5. Host-protected AF_UNIX endpoint (the only bind path).
class LocalIpcEndpoint final {
 public:
  // AF_UNIX only; rejects any non-local path; applies restrictive socket-file permissions.
  static std::optional<LocalIpcEndpoint> create(const GatewayConfig&, std::string_view local_path) noexcept;
  [[nodiscard]] bool is_local_unix() const noexcept;   // true only when the bound family is AF_UNIX
  // bounded, non-blocking accept / read / write driven by the caller; no background thread
  // ...
 private:
  // ...
};

// 6. Non-owning dependency bundle over the accepted in-process boundaries.
struct GatewayDependencies final {
  validation::SessionManager*     sessions{nullptr};
  validation::TimeAuthority*      time_authority{nullptr};
  StimulationJournal*             journal{nullptr};
  StimulationGuard*               guard{nullptr};
  StimulationActionPath*          actions{nullptr};
  ServiceEmulationRegistry*       leases{nullptr};
  ObservationHub*                 observations{nullptr};
  GatewayLogSink*                 log{nullptr};   // optional; null disables logging
};

// 7. One accepted peer session.
class GatewaySession final {
 public:
  GatewaySession(const GatewayConfig&, const GatewayDependencies&) noexcept;   // bounded construction
  // ten operations, by their exact T030 method names:
  QueryVersionResponse       QueryVersion(const QueryVersionRequest&) noexcept;
  OpenObservationResponse    OpenObservation(const OpenObservationRequest&) noexcept;
  std::size_t                ReadObservations(const ReadObservationsRequest&,
                                              std::span<ObservationRecord> out) noexcept;
  CloseObservationResponse   CloseObservation(const CloseObservationRequest&) noexcept;
  ArmSessionResponse         ArmSession(const ArmSessionRequest&) noexcept;
  RevokeSessionResponse      RevokeSession(const RevokeSessionRequest&) noexcept;
  SubmitStimulationResponse  SubmitStimulation(const SubmitStimulationRequest&) noexcept;
  AcquireLeaseResponse       AcquireLease(const AcquireLeaseRequest&) noexcept;
  ReleaseLeaseResponse       ReleaseLease(const ReleaseLeaseRequest&) noexcept;
  QuerySessionResponse       QuerySession(const QuerySessionRequest&) noexcept;
  // lifecycle
  void on_disconnect() noexcept;                     // deterministic cleanup
  void on_idle_tick(validation::Timestamp now) noexcept;
  [[nodiscard]] GatewaySessionSnapshot snapshot() const noexcept;
};

// Committed operation-name table pinned to the T030 descriptor method set.
[[nodiscard]] std::span<const std::string_view> gateway_operation_names() noexcept;

}  // namespace xverse::xcom
```

The generated Protocol Buffers types are named by their T030 package (`xverse::xcom::v1`); the header includes the
generated `tool_gateway.pb.h` through the generated-target include directory.

## 4. Operation mapping (message contract → accepted in-process boundary)

Each handler maps the T030 request fields onto the accepted in-process types. No accepted type is redefined, and no
alternative identity/digest/diagnostic vocabulary is introduced.

| T031 operation (exact T030 name) | Delegates to | Notes |
| --- | --- | --- |
| `QueryVersion` | `GatewayConfig` + production predicate | returns `ProtocolVersion{major=1, minor=kSupportedMinor}` and the bounded `GatewayCapabilities`; rejects an unsupported major before any other operation |
| `OpenObservation` | `ObservationHub::attach` with `ObservationTapSpec` | maps the filter, payload mode (metadata-only by default), record capacity, and overflow policy; grants a bounded stream identity |
| `ReadObservations` | `ObservationHub::poll` + `snapshot` | returns at most `max_records` records before the deadline; metadata-only records carry no payload bytes |
| `CloseObservation` | `ObservationHub::detach` + `snapshot` | returns delivered/dropped counters |
| `ArmSession` | `validation::Permit` + `SessionManager` | validates permit/session/plan/graph/protocol/validity; no field bypasses the permit |
| `RevokeSession` | `SessionManager` revoke | terminal state; repeat revoke is rejected without side effects |
| `SubmitStimulation` | `StimulationGuard` + `StimulationJournal` + `StimulationActionPath` | all four allowed actions; accepted items carry persistent synthetic provenance; a rejected/failed request emits zero normal-route items |
| `AcquireLease` | `ServiceEmulationRegistry` | exclusive, generation-bound lease; conflict is reported without ambiguous ownership |
| `ReleaseLease` | `ServiceEmulationRegistry` | releases or quarantines per durable state |
| `QuerySession` | `SessionManager::snapshot` | bounded counters including an explicit evidence-incomplete count |

A handler that cannot map a valid request onto an accepted boundary (for example, a message with an unsupported
combinatorial action) returns `STIMULATION_OUTCOME_REJECTED` with a stable `Diagnostic` and emits nothing.

## 5. Local-IPC framing (bounded, method-name-addressed)

The framing is a transport binding of the accepted messages, not a competing interface. A request frame is:

```text
uint32  total_length        (big-endian, excludes this prefix)
uint16  method_name_length  (big-endian)
bytes   method_name         (UTF-8, exactly one T030 RPC name)
bytes   request_message     (serialized T030 request message)
```

A response frame is `uint32 total_length` followed by the serialized response message. `ReadObservations` returns at
most the granted number of record frames and then one bounded terminator frame (zero length). Rules:

- `total_length` greater than `max_message_bytes` is rejected fail-closed before any allocation or dispatch.
- A `method_name` not present in `gateway_operation_names()` is rejected fail-closed.
- The method-name table is committed in the gateway source and asserted equal to the T030 descriptor method set in
  order; a mismatch fails the operation-surface test. This binds the framing 1:1 to the accepted contract
  (`T031-SR-002`, `T031-SR-021`) and introduces no competing method vocabulary.

## 6. Endpoint realization and host protection

`LocalIpcEndpoint::create(config, local_path)`:

1. Creates one socket with `socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0)`. No `AF_INET`/`AF_INET6`, no
   `getaddrinfo`, no TLS.
2. Binds it to `sockaddr_un` at `local_path` under a restricted directory and applies restrictive socket-file
   permissions (`0600`), rejecting a non-local or empty path.
3. Asserts `is_local_unix()` using `getsockname` and requires the address family to be `AF_UNIX`.
4. Accepts at most `max_concurrent_sessions` peers through a bounded, non-blocking `poll()`-style step driven by the
   caller. There is no background accept thread and no blocking listen loop.

The endpoint is poll-driven so the tests are deterministic and the design has no unbounded thread or queue. The
local-IPC suite binds the socket under a bounded build-tree scratch directory supplied as a compile definition
(`XCOM_T031_SCRATCH_DIR`, the T026 precedent); the path is never printed into public evidence.

## 7. Deadline, flow control, and cleanup

- **Deadline.** Each unary request carries `deadline_millis`. A request whose deadline exceeds `max_deadline_millis`
  is rejected. An admitted request computes an absolute due time from the injected `validation::TimeAuthority`; when
  the due time passes before dispatch, the request returns a deterministic diagnostic and emits no item.
- **Flow control.** A session admits a request only when its bounded in-flight queue has room and its bounded rate
  permits it. Saturation rejects deterministically, increments a visible counter, and never blocks the normal data
  plane without bound. No queue grows beyond its configured bound.
- **Cleanup table.**

| Event | Observation | Session | Lease | Pending request | Log |
| --- | --- | --- | --- | --- | --- |
| peer disconnect | `detach` handles | drain/revoke per durable state | release or quarantine | end `evidence_incomplete`/`failed` | `transport`/`failed` record |
| idle timeout | `detach` handles | revoke/expire | release or quarantine | end `failed`/`expired` | `session`/`expired` record |
| explicit close | `detach` exact handle | terminal/unchanged | release | unchanged | `observation` record |
| over-bound frame | unchanged | unchanged | unchanged | rejected | `transport`/`rejected` record |

A terminal session rejects further operations. An unknown outcome is never recorded or returned as success.

## 8. Test design

All suites live under `tests/xcom/tool_gateway/` and use only the standard library, the generated messages, the
accepted in-process libraries, and GTest. `gateway_support.hpp` provides a bounded manual-clock-driven time
authority, an in-process `LocalIpcChannel`, a bounded log-capture sink, and the production source paths (as compile
definitions) for the forbidden-API scan.

### 8.1 `gateway_session_tests.cpp` — `XcomToolGatewaySession` (`t031-session`)

| Unit case | Assertion |
| --- | --- |
| `T31-TS-001 VersionNegotiationAcceptsSupportedMajor` | `QueryVersion` returns the supported major with a higher minor treated additively |
| `T31-TS-002 VersionNegotiationRejectsUnsupportedMajor` | any other major is rejected fail-closed before any operation |
| `T31-TS-003 OperationSurfaceMatchesContract` | `gateway_operation_names()` equals the T030 descriptor method set in order |
| `T31-TS-004 ArmRequiresExactPermit` | an exact permit arms; a missing/mismatched permit is rejected and emits nothing |
| `T31-TS-005 RevokeTerminalState` | revoke is terminal; a repeat revoke is rejected without side effects |
| `T31-TS-006 QuerySessionCountersBounded` | the counter set is finite and includes an evidence-incomplete count |

### 8.2 `gateway_bounds_tests.cpp` — `XcomToolGatewayBounds` (`t031-bounds`)

| Unit case | Assertion |
| --- | --- |
| `T31-TS-007 MessageSizeBoundEnforced` | a frame over `max_message_bytes` is rejected before dispatch |
| `T31-TS-008 DeadlineEnforcedBeforeEmission` | an overdue request returns a deterministic diagnostic and emits no item |
| `T31-TS-009 FlowControlWindowBounded` | the in-flight queue never exceeds its bound under saturation; rejection is counted |
| `T31-TS-010 ObservationQueueBounded` | observation reads return at most the granted record count; the tap queue stays bounded |

### 8.3 `gateway_lifecycle_tests.cpp` — `XcomToolGatewayLifecycle` (`t031-lifecycle`)

| Unit case | Assertion |
| --- | --- |
| `T31-TS-011 DisconnectClosesObservationStreams` | disconnect detaches every observation handle owned by the session |
| `T31-TS-012 DisconnectDrainsOrQuarantinesLease` | disconnect releases or quarantines a held emulation lease with no ambiguous ownership |
| `T31-TS-013 PendingRequestEndsEvidenceIncomplete` | a pending request at disconnect ends explicit, never success |
| `T31-TS-014 IdleTimeoutCleanup` | idle timeout performs the cleanup table and rejects later operations |

### 8.4 `gateway_local_ipc_tests.cpp` — `XcomToolGatewayLocalIpc` (`t031-local-ipc`)

| Unit case | Assertion |
| --- | --- |
| `T31-TS-015 EndpointFamilyIsUnixOnly` | `LocalIpcEndpoint::create` binds an `AF_UNIX` socket and `is_local_unix()` is true |
| `T31-TS-016 NoTcpListenerBound` | the endpoint exposes no `AF_INET`/`AF_INET6` family and binds no TCP address |
| `T31-TS-017 EndpointPermissionsRestrictAccess` | the socket file carries restrictive permissions under a restricted directory |

### 8.5 `gateway_negative_tests.cpp` — `XcomToolGatewayNegative` (`t031-negative`)

| Unit case | Assertion |
| --- | --- |
| `T31-TS-018 OverBoundMessageRejected` | an over-bound frame/payload is rejected before allocation or emission |
| `T31-TS-019 ExpiredSessionRejectedZeroEmission` | an expired/unauthorized submission emits zero normal-route items |
| `T31-TS-020 UnsupportedMajorRejectedNoItem` | an unsupported major cannot reach an operation or emit an item |
| `T31-TS-021 TransportAccessDoesNotAuthorize` | an accepted local channel without a valid permit is rejected |
| `T31-TS-022 NoInetOrDnsOrTlsApi` | the gateway source contains no `AF_INET`/`AF_INET6`, DNS, resolver, or TLS token |

### 8.6 `gateway_logging_tests.cpp` — `XcomToolGatewayLogging` (`t031-logging`)

| Unit case | Assertion |
| --- | --- |
| `T31-TS-023 PayloadNeverLogged` | a payload-bearing stimulation produces no payload byte in any log record |
| `T31-TS-024 PermitContentsNeverLogged` | no log record contains a permit or session secret/identity beyond the safe field |

## 9. Failure semantics

| Condition | Outcome |
| --- | --- |
| unsupported protocol major | rejected fail-closed before any operation, `T31-TS-002`/`T31-TS-020` |
| missing/expired/mismatched permit | rejected with zero emitted items, `T31-TS-004`/`T31-TS-019`/`T31-TS-021` |
| over-bound frame or payload | rejected before allocation/emission, `T31-TS-007`/`T31-TS-018` |
| overdue deadline | deterministic diagnostic, no item, `T31-TS-008` |
| saturated in-flight queue or record queue | deterministic rejection, counted, no unbounded growth, `T31-TS-009`/`T31-TS-010` |
| TCP/DNS/TLS attempt | source and runtime check fail closed; not attempted, `T31-TS-016`/`T31-TS-022` |
| peer disconnect or idle timeout | cleanup table; pending request explicit non-success, `T31-TS-011`…`T31-TS-014` |
| unknown outcome | returned/recorded as `evidence_incomplete`/`failed`, never success, `T31-TS-013` |
| gateway source unavailable to the scan | the forbidden-API test fails closed (`T31-TS-022`) |
| gRPC runtime link attempted | fails closed; not attempted by T031 (`T031-GAP-01`) |

## 10. Determinism and safety

- Every operation, frame scan, queue, record pull, and cleanup step is finite and bounded by a `GatewayConfig`
  value; no case depends on ambient wall-clock time, randomness, or environment.
- The local-IPC suite performs only a bounded `AF_UNIX` bind/connect/exchange under a build-tree scratch directory;
  no network, DNS, TLS, subprocess, dynamic load, or legacy access occurs.
- Committed files and evidence contain no credential, private address, real or proprietary payload, or
  environment-specific host path; log records and logs contain no payload or permit content.

## 11. Traceability

| Design element | Requirement | Unit cases |
| --- | --- | --- |
| `T31-DD-02` interface | T031-SR-001 | `T31-TS-003` |
| `T31-DD-01`/`T31-DD-12` operation table | T031-SR-002, T031-SR-021 | `T31-TS-003` |
| `T31-DD-03` version predicate | T031-SR-003 | `T31-TS-001`, `T31-TS-002`, `T31-TS-020` |
| `T31-DD-04` permit | T031-SR-004, T031-SR-009 | `T31-TS-004`, `T31-TS-019`, `T31-TS-021` |
| `T31-DD-05` bounds | T031-SR-005, T031-SR-010 | `T31-TS-007`, `T31-TS-018`, `T31-TS-010` |
| `T31-DD-06` deadline | T031-SR-006, T031-SR-016 | `T31-TS-008`, `T31-TS-009` |
| `T31-DD-07` flow control | T031-SR-007, T031-SR-016 | `T31-TS-009`, `T31-TS-010` |
| `T31-DD-08` local IPC | T031-SR-008, T031-SR-018 | `T31-TS-015`, `T31-TS-016`, `T31-TS-022` |
| `T31-DD-09` host protection | T031-SR-009 | `T31-TS-017`, `T31-TS-021` |
| observation mapping | T031-SR-010 | `T31-TS-010`, `T31-TS-011` |
| stimulation mapping | T031-SR-011 | `T31-TS-008`, `T31-TS-018`, `T31-TS-019` |
| lease mapping | T031-SR-012 | `T31-TS-012`, `T31-TS-021` |
| `T31-DD-11` cleanup | T031-SR-013, T031-SR-015 | `T31-TS-011`…`T31-TS-014`, `T31-TS-006` |
| `T31-DD-10` logs | T031-SR-014 | `T31-TS-023`, `T31-TS-024` |
| `T31-DD-12` build wiring | T031-SR-017 | build/discovery inspection |
| `T31-DD-13` offline linkage | T031-SR-018 | `T31-TS-022` |
| work products/governance | T031-SR-019, T031-SR-020 | gate and validators |

## 12. Doxygen and documentation

- The new public header carries the X-COM file-block (`@file`, `@brief`, `@ingroup xcom_gw`) and documents exactly
  seven public gateway elements with `@brief`, `@ownership`, `@lifetime`, `@thread_safety`, and `@failure` tags, as
  accepted `XCOM-DU-020` requires.
- The test helper and suites carry the X-COM file-block tags required of changed test units.
- Generated Protocol Buffers documentation remains `DOX-GAP-02` (T037); T031 documents only the hand-written
  gateway interface.

## Successor disposition (T039 R3, recorded 2026-09-30)

`T31-DD-01` remains the historical decision for the accepted local-IPC framing. The T039 successor
supersedes its "cannot link the gRPC runtime" premise for the linked gateway component only: the
`GatewayLiveness` watch service and the `ToolGateway` service are compiled and linked by the
`xverse_xcom_tool_gateway_grpc` adapter through the admitted gRPC runtime.

The successor adds a single-owner watch association (one opaque `x-xcom-watch-id` per stateful call),
single-owned-lease enforcement (`T039-F07`), and a bounded shutdown cancellation deadline. The
dialect restriction on the separate T032 synthetic client is unchanged: it keeps its framed local-IPC
transport and does not claim a linked gRPC runtime.

## Successor disposition (T039 R4, recorded 2026-09-30)

The R3 single-owned-lease design is retained and clarified for allocation identity (`T039-F08`). The
shared design decision is that a lease release is validated against the exact successful allocation,
not against a reused endpoint-generation label. `GatewaySession` allocates each successful lease a
fresh public identity from a session-scoped, strictly monotonic sequence that never wraps, and the
generation-bound registry delegation carries that same allocation identity, so a delayed or repeated
release for an earlier allocation cannot name a later allocation of any endpoint in the session. When
the bounded identity sequence is exhausted the acquisition is declined with `LEASE_CONFLICT` before
the registry is touched, with no wraparound and no lease, registry, or sequence side effect. The
single-owned-lease boundary, the retained original identity on a declined acquisition, the
exact-session check, the generation-bound registry delegation, and the cleanup/quarantine semantics
are unchanged; the ten `ToolGateway` methods and the separate `GatewayLiveness` liveness contract are
unchanged and no additional interface or dependency is introduced.
