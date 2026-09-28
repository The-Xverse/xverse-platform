# T030 Detailed Design — Versioned gRPC/Protocol Buffers Tool API and Additive Evolution Rules

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T030 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → detailed design |
| Revision | 1 (versioned external-tool contract slice) |
| Baseline revision | `80c236638e160c5e991e5a537e29d407e7462dc6` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

T030 defines the external-tool contract, generates the C++ artifacts with the T011-admitted tools, and proves the
contract with offline generated-contract tests. It authors no gateway behaviour. The design is written **before**
implementation; the implementation must realize it exactly or record a design change and re-review.

## 2. Design decisions

| ID | Decision | Rationale | Requirement |
| --- | --- | --- | --- |
| `T30-DD-01` | Single committed schema `proto/xverse/xcom/v1/tool_gateway.proto`, `package xverse.xcom.v1`, `syntax = "proto3"` | Matches accepted `XCOM-XLC-002` external-rpc v1 and `XCOM-DU-019`; one versioned source | T030-SR-001 |
| `T30-DD-02` | Generate Protocol Buffers messages with the admitted `protoc` at build time; compile them into a static library | Proves generated-code provenance and reuses the admitted `libprotobuf.a` | T030-SR-014 |
| `T30-DD-03` | Generate gRPC stubs at build time for provenance but do not compile or link them | The admitted envelope lacks the gRPC runtime transitive libraries; linking fails closed (`T030-GAP-02`) | T030-SR-014 |
| `T30-DD-04` | Verify the gRPC service contract through the generated `FileDescriptor` and the generated stub source | The descriptor carries service/method/streaming metadata without a gRPC runtime link | T030-SR-002, T030-SR-016 |
| `T30-DD-05` | Pin the field manifest and reserved bands in a committed test-local table | Makes a non-additive schema change fail the tests deterministically | T030-SR-012 |
| `T30-DD-06` | Prove unknown-field and unmapped-enum round-trip preservation | Proto3 forward compatibility is the additive-evolution wire contract | T030-SR-013 |
| `T30-DD-07` | Declare every enforced bound as an explicit schema field | No implicit or unbounded message/stream/deadline/payload | T030-SR-010 |
| `T30-DD-08` | Carry logical identities only; forbid transport/address/port/export shapes by test | Domain neutrality (`FR-022`) | T030-SR-011 |
| `T30-DD-09` | Add one runtime-target inventory entry and four `t030-<kind>` test targets, additively | T012 build contract: a new target is declared explicitly | T030-SR-015 |
| `T30-DD-10` | Test-local fail-closed major-version predicate | Demonstrates the rejection rule without claiming production behaviour | T030-SR-003 |

## 3. Contract design (`proto/xverse/xcom/v1/tool_gateway.proto`)

The implementation authors the schema below verbatim (comments may be extended but no field
number/name/type may change without a new committed field manifest revision).

```proto
syntax = "proto3";

package xverse.xcom.v1;

// Versioned X-COM external-tool gateway contract (v1).
// Evolution rules:
//   1. Field numbers and names are immutable once published.
//   2. A removed field number and name MUST be reserved here before reuse.
//   3. Only additive fields, messages, enums, and methods may be added.
//   4. An unsupported protocol major version MUST be rejected fail-closed.
//   5. No address, port, socket, DNS, TLS, credential, dashboard, storage,
//      query-presentation, or export primitive may become a core field.
//   6. Every enforced bound is an explicit field; no implicit bound is allowed.
//   7. The reserved band 1000-1999 in every message is for future additive fields.

// ---------------------------------------------------------------------------
// Version negotiation
// ---------------------------------------------------------------------------

message ProtocolVersion {
  uint32 major = 1;
  uint32 minor = 2;
}

message Capability {
  string id = 1;
  uint32 revision = 2;
}

message GatewayCapabilities {
  ProtocolVersion protocol = 1;
  repeated Capability capabilities = 2;
  uint32 max_message_bytes = 3;
  uint32 max_concurrent_streams = 4;
  uint64 max_deadline_millis = 5;
  uint32 max_observation_queue = 6;
  reserved 1000 to 1999;
}

message QueryVersionRequest {}

message QueryVersionResponse {
  ProtocolVersion protocol = 1;
  GatewayCapabilities capabilities = 2;
  Diagnostic diagnostic = 3;
}

// ---------------------------------------------------------------------------
// Diagnostics
// ---------------------------------------------------------------------------

enum Severity {
  SEVERITY_UNSPECIFIED = 0;
  SEVERITY_INFO = 1;
  SEVERITY_WARNING = 2;
  SEVERITY_ERROR = 3;
}

message Diagnostic {
  string code = 1;
  Severity severity = 2;
  string phase = 3;
  string identity = 4;
  string reason = 5;
  string correction = 6;
  reserved 1000 to 1999;
}

// ---------------------------------------------------------------------------
// Observation
// ---------------------------------------------------------------------------

enum PayloadState {
  PAYLOAD_STATE_UNSPECIFIED = 0;
  PAYLOAD_METADATA_ONLY = 1;
  PAYLOAD_VIEW_ALLOWED = 2;
  PAYLOAD_REDACTED = 3;
  PAYLOAD_TRUNCATED = 4;
}

message ObservationFilter {
  string origin_kind = 1;
  string contract_id = 2;
  string route_id = 3;
  string clock_domain = 4;
  string outcome = 5;
  reserved 1000 to 1999;
}

message Identity {
  string origin_kind = 1;
  string tool_id = 2;
  string permit_id = 3;
  string session_id = 4;
  string plan_digest = 5;
  string request_id = 6;
  string correlation_id = 7;
  uint64 causation_id = 8;
  reserved 1000 to 1999;
}

message ObservationRecord {
  Identity identity = 1;
  string route_id = 2;
  string contract_id = 3;
  string clock_domain = 4;
  uint64 sequence = 5;
  string outcome = 6;
  PayloadState payload_state = 7;
  bytes payload_view = 8;
  uint32 payload_bytes = 9;
  reserved 1000 to 1999;
}

message OpenObservationRequest {
  string tap_id = 1;
  ObservationFilter filter = 2;
  uint32 max_records = 3;
  uint32 max_record_bytes = 4;
  bool allow_payload_view = 5;
  uint64 deadline_millis = 6;
  reserved 1000 to 1999;
}

message OpenObservationResponse {
  string stream_id = 1;
  uint32 granted_max_records = 2;
  uint32 granted_max_record_bytes = 3;
  Diagnostic diagnostic = 4;
}

message ReadObservationsRequest {
  string stream_id = 1;
  uint32 max_records = 2;
  uint64 deadline_millis = 3;
  reserved 1000 to 1999;
}

message CloseObservationRequest {
  string stream_id = 1;
}

message CloseObservationResponse {
  uint64 delivered = 1;
  uint64 dropped = 2;
  Diagnostic diagnostic = 3;
}

// ---------------------------------------------------------------------------
// Validation session
// ---------------------------------------------------------------------------

enum SessionState {
  SESSION_STATE_UNSPECIFIED = 0;
  SESSION_DECLARED = 1;
  SESSION_ARMED = 2;
  SESSION_CLOSED = 3;
  SESSION_REVOKED = 4;
  SESSION_EXPIRED = 5;
  SESSION_EVIDENCE_INCOMPLETE = 6;
}

message ArmSessionRequest {
  string permit_id = 1;
  string session_id = 2;
  string plan_digest = 3;
  string graph_digest = 4;
  ProtocolVersion protocol = 5;
  uint64 validity_millis = 6;
  uint64 deadline_millis = 7;
  reserved 1000 to 1999;
}

message ArmSessionResponse {
  SessionState state = 1;
  Diagnostic diagnostic = 2;
}

message RevokeSessionRequest {
  string session_id = 1;
  string reason_code = 2;
}

message RevokeSessionResponse {
  SessionState state = 1;
  Diagnostic diagnostic = 2;
}

// ---------------------------------------------------------------------------
// Stimulation submission
// ---------------------------------------------------------------------------

enum StimulationActionKind {
  STIMULATION_ACTION_UNSPECIFIED = 0;
  STIMULATION_ACTION_INJECT_SIGNAL = 1;
  STIMULATION_ACTION_INJECT_MESSAGE = 2;
  STIMULATION_ACTION_INVOKE_SERVICE = 3;
  STIMULATION_ACTION_EMULATE_SERVICE = 4;
}

enum InteractionKind {
  INTERACTION_KIND_UNSPECIFIED = 0;
  INTERACTION_KIND_SIGNAL = 1;
  INTERACTION_KIND_MESSAGE = 2;
  INTERACTION_KIND_REQUEST = 3;
  INTERACTION_KIND_RESPONSE = 4;
}

enum Direction {
  DIRECTION_UNSPECIFIED = 0;
  DIRECTION_INBOUND = 1;
  DIRECTION_OUTBOUND = 2;
  DIRECTION_BIDIRECTIONAL = 3;
}

message StimulationAction {
  StimulationActionKind kind = 1;
  string action_id = 2;
  string correlation_id = 3;
  uint64 causation_id = 4;
  reserved 1000 to 1999;
}

enum ScheduleMode {
  SCHEDULE_MODE_UNSPECIFIED = 0;
  SCHEDULE_IMMEDIATE = 1;
  SCHEDULE_SCHEDULED = 2;
}

message Schedule {
  ScheduleMode mode = 1;
  string clock_domain = 2;
  uint64 due_nanos = 3;
  uint64 tolerance_nanos = 4;
  string ordering_rule = 5;
  string late_policy = 6;
  reserved 1000 to 1999;
}

message SubmitStimulationRequest {
  string session_id = 1;
  string request_id = 2;
  StimulationAction action = 3;
  string target_endpoint = 4;
  string contract_id = 5;
  InteractionKind interaction = 6;
  Direction direction = 7;
  Schedule schedule = 8;
  bytes payload = 9;
  uint32 payload_bytes = 10;
  uint64 deadline_millis = 11;
  reserved 1000 to 1999;
}

enum StimulationOutcomeKind {
  STIMULATION_OUTCOME_UNSPECIFIED = 0;
  STIMULATION_OUTCOME_EMITTED = 1;
  STIMULATION_OUTCOME_REJECTED = 2;
  STIMULATION_OUTCOME_FAILED = 3;
  STIMULATION_OUTCOME_QUEUED = 4;
  STIMULATION_OUTCOME_EVIDENCE_INCOMPLETE = 5;
}

message StimulationOutcome {
  StimulationOutcomeKind kind = 1;
  string request_id = 2;
  string correlation_id = 3;
  uint64 causation_id = 4;
  reserved 1000 to 1999;
}

message SubmitStimulationResponse {
  string request_id = 1;
  StimulationOutcome outcome = 2;
  Diagnostic diagnostic = 3;
}

// ---------------------------------------------------------------------------
// Service-emulation lease
// ---------------------------------------------------------------------------

enum LeaseState {
  LEASE_STATE_UNSPECIFIED = 0;
  LEASE_ACTIVE = 1;
  LEASE_RELEASED = 2;
  LEASE_QUARANTINED = 3;
  LEASE_EXPIRED = 4;
  LEASE_CONFLICT = 5;
}

message AcquireLeaseRequest {
  string session_id = 1;
  string endpoint_id = 2;
  uint64 endpoint_generation = 3;
  string plan_digest = 4;
  uint64 lease_millis = 5;
  uint64 deadline_millis = 6;
  reserved 1000 to 1999;
}

message AcquireLeaseResponse {
  string lease_id = 1;
  LeaseState state = 2;
  Diagnostic diagnostic = 3;
}

message ReleaseLeaseRequest {
  string session_id = 1;
  string lease_id = 2;
  string reason_code = 3;
}

message ReleaseLeaseResponse {
  LeaseState state = 1;
  Diagnostic diagnostic = 2;
}

// ---------------------------------------------------------------------------
// Session query
// ---------------------------------------------------------------------------

message SessionCounters {
  uint64 requests_received = 1;
  uint64 requests_authorized = 2;
  uint64 requests_rejected = 3;
  uint64 emitted = 4;
  uint64 evidence_incomplete = 5;
  reserved 1000 to 1999;
}

message QuerySessionRequest {
  string session_id = 1;
}

message QuerySessionResponse {
  SessionState state = 1;
  SessionCounters counters = 2;
  Diagnostic diagnostic = 3;
}

// ---------------------------------------------------------------------------
// Service
// ---------------------------------------------------------------------------

service ToolGateway {
  rpc QueryVersion(QueryVersionRequest) returns (QueryVersionResponse);
  rpc OpenObservation(OpenObservationRequest) returns (OpenObservationResponse);
  rpc ReadObservations(ReadObservationsRequest) returns (stream ObservationRecord);
  rpc CloseObservation(CloseObservationRequest) returns (CloseObservationResponse);
  rpc ArmSession(ArmSessionRequest) returns (ArmSessionResponse);
  rpc RevokeSession(RevokeSessionRequest) returns (RevokeSessionResponse);
  rpc SubmitStimulation(SubmitStimulationRequest) returns (SubmitStimulationResponse);
  rpc AcquireLease(AcquireLeaseRequest) returns (AcquireLeaseResponse);
  rpc ReleaseLease(ReleaseLeaseRequest) returns (ReleaseLeaseResponse);
  rpc QuerySession(QuerySessionRequest) returns (QuerySessionResponse);
}
```

### 3.1 Service surface (descriptor expectation)

| Method | Request | Response | Streaming |
| --- | --- | --- | --- |
| `QueryVersion` | `QueryVersionRequest` | `QueryVersionResponse` | unary |
| `OpenObservation` | `OpenObservationRequest` | `OpenObservationResponse` | unary |
| `ReadObservations` | `ReadObservationsRequest` | `ObservationRecord` | server streaming |
| `CloseObservation` | `CloseObservationRequest` | `CloseObservationResponse` | unary |
| `ArmSession` | `ArmSessionRequest` | `ArmSessionResponse` | unary |
| `RevokeSession` | `RevokeSessionRequest` | `RevokeSessionResponse` | unary |
| `SubmitStimulation` | `SubmitStimulationRequest` | `SubmitStimulationResponse` | unary |
| `AcquireLease` | `AcquireLeaseRequest` | `AcquireLeaseResponse` | unary |
| `ReleaseLease` | `ReleaseLeaseRequest` | `ReleaseLeaseResponse` | unary |
| `QuerySession` | `QuerySessionRequest` | `QuerySessionResponse` | unary |

### 3.2 Additive-evolution rules (normative)

1. **Immutable identity.** The `package` and every published field number/name are immutable. A change to a field
   number or name is a breaking change and is prohibited in v1.
2. **Reserved extension band.** Every message declares `reserved 1000 to 1999;`. No v1 field uses a number in the
   band. Future additive fields use numbers below 1000 that are not already used.
3. **Remove = reserve.** Removing or renaming a field requires reserving its number and name in the same change; the
   tests fail if a reserved number reappears as a field.
4. **Additive only.** New messages, enums, enum values, fields with fresh numbers, and new methods may be added. No
   field may change type, label, or number; no enum value number may be reused.
5. **Wire forward compatibility.** A consumer must preserve unknown fields and unmapped enum values across a proto3
   round trip and must not fail on them.
6. **Version negotiation.** An unsupported `ProtocolVersion.major` is rejected fail-closed; a higher minor is
   accepted additively.

### 3.3 Pinned field manifest (test-local, committed)

`tests/xcom/tool_gateway/contract_support.hpp` pins at least:

| Message | Pinned `number → name` |
| --- | --- |
| `ProtocolVersion` | `1→major`, `2→minor` |
| `GatewayCapabilities` | `1→protocol`, `2→capabilities`, `3→max_message_bytes`, `4→max_concurrent_streams`, `5→max_deadline_millis`, `6→max_observation_queue` |
| `ObservationRecord` | `1→identity`, `2→route_id`, `3→contract_id`, `4→clock_domain`, `5→sequence`, `6→outcome`, `7→payload_state`, `8→payload_view`, `9→payload_bytes` |
| `ArmSessionRequest` | `1→permit_id`, `2→session_id`, `3→plan_digest`, `4→graph_digest`, `5→protocol`, `6→validity_millis`, `7→deadline_millis` |
| `SubmitStimulationRequest` | `1→session_id`, `2→request_id`, `3→action`, `4→target_endpoint`, `5→contract_id`, `6→interaction`, `7→direction`, `8→schedule`, `9→payload`, `10→payload_bytes`, `11→deadline_millis` |
| `AcquireLeaseRequest` | `1→session_id`, `2→endpoint_id`, `3→endpoint_generation`, `4→plan_digest`, `5→lease_millis`, `6→deadline_millis` |
| `SessionCounters` | `1→requests_received`, `2→requests_authorized`, `3→requests_rejected`, `4→emitted`, `5→evidence_incomplete` |
| `Diagnostic` | `1→code`, `2→severity`, `3→phase`, `4→identity`, `5→reason`, `6→correction` |

The manifest is the additive-evolution guard: the tests compare the live descriptor to it exactly, so a renumbering,
rename, or silent removal fails deterministically.

## 4. Generation design

### 4.1 Generation command and provenance

The build generates both artifacts from the committed schema with the T011-admitted tools:

```text
protoc -I <repo>/proto --cpp_out=<build>/t030-proto-gen \
       --grpc_out=<build>/t030-proto-gen \
       --plugin=protoc-gen-grpc=<admitted-prefix-bin>/grpc_cpp_plugin \
       xverse/xcom/v1/tool_gateway.proto
```

- `.pb.{h,cc}` — Protocol Buffers messages, compiled into `xverse_xcom_tool_gateway_proto`.
- `.grpc.pb.{h,cc}` — gRPC stubs, generated for provenance, not compiled or linked (`T030-GAP-02`).

Recorded generated-code provenance: input schema identity (`proto/xverse/xcom/v1/tool_gateway.proto`, SHA-256),
generation command, generator identity (`protoc` 3.12.4 and `grpc_cpp_plugin` 1.30.2 from the T011 dependency-lock),
and output digests. The generator runs offline with the admitted prefix library directory on the process library
path; no ambient discovery or network resolution occurs.

### 4.2 Build wiring (`src/xverse/xcom/CMakeLists.txt`, additive)

- Add `xverse_xcom_tool_gateway_proto` to `XVERSE_XCOM_RUNTIME_TARGETS` (one declared inventory addition; the T012
  generated `xcom_build_contract` expectation moves with it).
- Add one `add_custom_command` generating `.pb.{h,cc}` and one generating `.grpc.pb.{h,cc}`, then
  `add_library(xverse_xcom_tool_gateway_proto STATIC <build>/t030-proto-gen/xverse/xcom/v1/tool_gateway.pb.cc)`
  linking `protobuf::libprotobuf` only, routed through `xverse_xcom_apply_runtime_rules`.
- Add four additive test executables, one per kind, each linking `xverse::xcom_tool_gateway_proto` and GTest, with a
  single hyphenated `t030-<kind>` label: `t030-contract`, `t030-evolution`, `t030-negative`, `t030-provenance`.
- Do not compile or link the gRPC stubs, and do not change any existing target, test name, label, command, or value.

## 5. Test design

### 5.1 `contract_tests.cpp` — `XcomToolGatewayContract` (`t030-contract`)

| Unit case | Assertion |
| --- | --- |
| `T30-TS-001 PackageSyntaxVersioned` | descriptor package is `xverse.xcom.v1`; the file builds under proto3 with an explicit `ProtocolVersion` message |
| `T30-TS-002 ServiceSurfaceComplete` | exactly the 10 declared methods, in the declared request/response pairing |
| `T30-TS-003 MessageVocabularyComplete` | every required message and enum exists with a zero `*_UNSPECIFIED` value |
| `T30-TS-004 VersionNegotiationAndCapabilities` | `ProtocolVersion`/`GatewayCapabilities` field manifest and the test-local major-version predicate (accepts major 1, rejects major 0 and major 2) |
| `T30-TS-005 ObservationStreamContractAndBounds` | `ReadObservations` is server streaming; `ObservationRecord` carries identity/route/contract/clock/sequence/outcome/payload-state, and metadata-only default |
| `T30-TS-006 SessionArmRevokeContract` | arm request carries permit/session/plan/graph/protocol/validity; responses carry `SessionState`; no permit-bypass field |
| `T30-TS-007 StimulationActionCoverage` | all four action kinds, both schedule modes, direction and interaction enums, timeline and payload bound present |
| `T30-TS-008 ServiceEmulationLeaseContract` | acquire binds session/endpoint/generation/plan; release binds session/lease; `LeaseState` present |
| `T30-TS-009 SessionOutcomeCountersContract` | outcome kinds include evidence-incomplete; counters are the declared finite set |
| `T30-TS-010 DiagnosticContract` | diagnostic carries code/severity/phase/identity/reason/correction |
| `T30-TS-011 DeclaredBoundsPresent` | `max_message_bytes`, `max_concurrent_streams`, `max_deadline_millis`, `max_observation_queue`, record/payload/deadline/lease bounds present |

### 5.2 `evolution_tests.cpp` — `XcomToolGatewayEvolution` (`t030-evolution`)

| Unit case | Assertion |
| --- | --- |
| `T30-TS-012 ReservedExtensionBandDeclared` | every message declares a reserved band covering 1000–1999 and no field number falls in it |
| `T30-TS-013 FieldNumberManifestPinned` | the live descriptor equals the pinned field manifest for every manifest message |
| `T30-TS-014 AdditiveFieldInsertionBackwardCompatible` | an unknown-field-only message round-trips; a message serialized with one additive higher-numbered field parses in the older contract and preserves the unknown field |
| `T30-TS-015 UnknownFieldForwardCompatible` | a crafted wire buffer with an extra tag parses without error and exposes the unknown field through reflection |
| `T30-TS-016 UnmappedEnumValuePreserved` | an unmapped enum number survives a round trip as its numeric value and is not remapped to zero |

### 5.3 `negative_tests.cpp` — `XcomToolGatewayNegative` (`t030-negative`)

| Unit case | Assertion |
| --- | --- |
| `T30-TS-017 NoTcpOrAddressPrimitive` | no field name contains transport/address/port/socket/DNS/TLS/credential fragments |
| `T30-TS-018 NoImplicitUnboundedPayload` | every message with a `bytes` field also declares a size-bound field; no `bytes` field is unbounded by declaration |
| `T30-TS-019 NoBypassOfPermitOrSession` | no message permits a submission/lease operation without a session/permit identity field |
| `T30-TS-020 UnsupportedMajorVersionRejectedByPredicate` | the test-local compatibility predicate rejects every major other than 1 |
| `T30-TS-021 ReservedNumberCannotBeReused` | no live field number lies inside a declared reserved band; a reserved number is not a live field |

### 5.4 `provenance_tests.cpp` — `XcomToolGatewayProvenance` (`t030-provenance`)

| Unit case | Assertion |
| --- | --- |
| `T30-TS-022 GeneratedCodeProvenanceRecorded` | the generated Protocol Buffers header carries the admitted protobuf runtime version macro and the file descriptor name matches the committed schema path |
| `T30-TS-023 GeneratedGrpcStubDeclaresService` | the generated `.grpc.pb.h` declares the `ToolGateway` service class and the 10 method names (file read from the build-tree path provided as a compile definition) |
| `T30-TS-024 SerializedDescriptorMatchesSource` | the serialized `FileDescriptorProto` round-trips and equals the descriptor built from the parsed bytes (self-consistency of the compiled contract) |

## 6. Failure semantics

| Condition | Outcome |
| --- | --- |
| unknown field on the wire | preserved, not rejected (proto3 additive compatibility), `T30-TS-015` |
| unmapped enum value | preserved as its numeric value, not remapped, `T30-TS-016` |
| unsupported protocol major | rejected fail-closed by the documented rule and predicate, `T30-TS-004`/`T30-TS-020` |
| field renumbering/reuse/removal without reservation | contract test fails, `T30-TS-012`/`T30-TS-013`/`T30-TS-021` |
| transport/address/export shape in the schema | contract test fails closed, `T30-TS-017` |
| payload field without a declared bound | contract test fails closed, `T30-TS-018` |
| generation tool missing or schema invalid | build fails closed (no artifact is produced) |
| gRPC runtime link attempted | fails closed; not attempted by T030 (`T030-GAP-02`) |

## 7. Determinism and safety

- The schema, descriptor, generated messages, and tests are deterministic for the fixed admitted generator and
  schema; no wall-clock, randomness, environment, or thread affects a verdict.
- Every scan, manifest, band, probe buffer, and case count is finite and declared in `contract_support.hpp`.
- No test opens a network peer, socket, resolver, TLS session, dynamic library, subprocess, or legacy repository; the
  only file read is the bounded read of the generated build-tree headers in `T30-TS-023`.
- Committed files and evidence contain no credential, private address, real or proprietary payload, or
  environment-specific host path.

## 8. Traceability

| Design element | Requirement | Unit cases |
| --- | --- | --- |
| `T30-DD-01` `T30-CMP-CONTRACT` | T030-SR-001 | T30-TS-001 |
| `T30-DD-04` service surface | T030-SR-002, T030-SR-016 | T30-TS-002, T30-TS-003 |
| `T30-DD-10` version negotiation | T030-SR-003 | T30-TS-004, T30-TS-020 |
| observation design | T030-SR-004 | T30-TS-005 |
| session design | T030-SR-005 | T30-TS-006 |
| stimulation design | T030-SR-006 | T30-TS-007 |
| lease design | T030-SR-007 | T30-TS-008 |
| outcome/counter design | T030-SR-008 | T30-TS-009 |
| diagnostic design | T030-SR-009 | T30-TS-010 |
| `T30-DD-07` bounds | T030-SR-010 | T30-TS-011, T30-TS-018 |
| `T30-DD-08` domain neutrality | T030-SR-011 | T30-TS-017, T30-TS-019 |
| `T30-DD-05` additive evolution | T030-SR-012 | T30-TS-012, T30-TS-013, T30-TS-021 |
| `T30-DD-06` forward compatibility | T030-SR-013 | T30-TS-014, T30-TS-015, T30-TS-016 |
| `T30-DD-02`/`T30-DD-03` generation | T030-SR-014 | T30-TS-022, T30-TS-023, T30-TS-024 |
| `T30-DD-09` build wiring | T030-SR-015 | build/discovery inspection |
| test family | T030-SR-016..T030-SR-018 | all suites |
| work products/governance | T030-SR-019, T030-SR-020 | gate and validators |

## 9. Doxygen and documentation

- The `.proto` carries contract-level comments (evolution rules, version, service) as its documentation.
- The test helper and suites carry the X-COM file-block tags required of changed test units.
- Generated C++ documentation remains `DOX-GAP-02` (T037); T030 records the generated-code provenance policy
  contribution and closes the "no generated C++ exists yet" part of `T011-GAP-02` for the gateway proto.
