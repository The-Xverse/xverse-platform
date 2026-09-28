# T030 Unit Specifications — Versioned gRPC/Protocol Buffers Tool API and Additive Evolution Rules

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T030 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → unit specifications |
| Revision | 1 (versioned external-tool contract slice) |
| Baseline revision | `80c236638e160c5e991e5a537e29d407e7462dc6` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit framework | GoogleTest over the T011-admitted offline envelope; the deterministic Phase 7 gate and the T007–T010 register validators for governance |
| Classification | Public-safe engineering work product |

T030 exposes no in-process production interface. Its units are the versioned contract artifact, the generated
artifacts, and the generated-contract tests. Each requirement `T030-SR-###` owns one unit specification
`T030-SR-###-U` whose cases are named `T30-TS-###`. "Verified" means the test exists, is deterministic, and passes at
the recorded candidate revision; it is not a deployed-service or compatibility claim.

## 2. Unit inventory

| Unit | Component | Source of truth | Kind | Cases |
| --- | --- | --- | --- | --- |
| `T030-SR-001-U` | `T030-SR-001-CMP` | `proto/xverse/xcom/v1/tool_gateway.proto` | contract artifact | T30-TS-001 |
| `T030-SR-002-U` | `T030-SR-002-CMP` | `proto/xverse/xcom/v1/tool_gateway.proto` | contract artifact | T30-TS-002, T30-TS-003 |
| `T030-SR-003-U` | `T030-SR-003-CMP` | `tests/xcom/tool_gateway/contract_tests.cpp` | generated-contract test | T30-TS-004, T30-TS-020 |
| `T030-SR-004-U` | `T030-SR-004-CMP` | `tests/xcom/tool_gateway/contract_tests.cpp` | generated-contract test | T30-TS-005 |
| `T030-SR-005-U` | `T030-SR-005-CMP` | `tests/xcom/tool_gateway/contract_tests.cpp` | generated-contract test | T30-TS-006 |
| `T030-SR-006-U` | `T030-SR-006-CMP` | `tests/xcom/tool_gateway/contract_tests.cpp` | generated-contract test | T30-TS-007 |
| `T030-SR-007-U` | `T030-SR-007-CMP` | `tests/xcom/tool_gateway/contract_tests.cpp` | generated-contract test | T30-TS-008 |
| `T030-SR-008-U` | `T030-SR-008-CMP` | `tests/xcom/tool_gateway/contract_tests.cpp` | generated-contract test | T30-TS-009 |
| `T030-SR-009-U` | `T030-SR-009-CMP` | `tests/xcom/tool_gateway/contract_tests.cpp` | generated-contract test | T30-TS-010 |
| `T030-SR-010-U` | `T030-SR-010-CMP` | `tests/xcom/tool_gateway/contract_tests.cpp` | generated-contract test | T30-TS-011, T30-TS-018 |
| `T030-SR-011-U` | `T030-SR-011-CMP` | `tests/xcom/tool_gateway/negative_tests.cpp` | generated-contract test | T30-TS-017, T30-TS-019 |
| `T030-SR-012-U` | `T030-SR-012-CMP` | `tests/xcom/tool_gateway/evolution_tests.cpp` | generated-contract test | T30-TS-012, T30-TS-013, T30-TS-021 |
| `T030-SR-013-U` | `T030-SR-013-CMP` | `tests/xcom/tool_gateway/evolution_tests.cpp` | generated-contract test | T30-TS-014, T30-TS-015, T30-TS-016 |
| `T030-SR-014-U` | `T030-SR-014-CMP` | `tests/xcom/tool_gateway/provenance_tests.cpp` | generated-code provenance | T30-TS-022, T30-TS-023, T30-TS-024 |
| `T030-SR-015-U` | `T030-SR-015-CMP` | `src/xverse/xcom/CMakeLists.txt` | build contract | build/discovery inspection |
| `T030-SR-016-U` | `T030-SR-016-CMP` | `tests/xcom/tool_gateway/**` | generated-contract test | T30-TS-002…T30-TS-011 |
| `T030-SR-017-U` | `T030-SR-017-CMP` | `tests/xcom/tool_gateway/**` | test safety | forbidden-API scan |
| `T030-SR-018-U` | `T030-SR-018-CMP` | committed T030 files | public safety | public-safety scan |
| `T030-SR-019-U` | `T030-SR-019-CMP` | `docs/engineering/xcom/t030/**` | governance | register validators |
| `T030-SR-020-U` | `T030-SR-020-CMP` | `docs/engineering/xcom/t030/**` | governance | Phase 7 gate |

## 3. Unit specifications

### T030-SR-001-U — Single versioned contract source

- **Inputs:** the committed `proto/xverse/xcom/v1/tool_gateway.proto`.
- **Outputs:** the generated message descriptor and the parsed package/syntax identity.
- **Invariants:** exactly one committed schema defines the contract; package `xverse.xcom.v1`; proto3; the locator
  equals `XCOM-XLC-002`.
- **Cases:** `XcomToolGatewayContract.T30-TS-001 PackageSyntaxVersioned`.
- **Static checks:** the schema parses under the admitted `protoc` during the build.

### T030-SR-002-U — Complete service surface

- **Inputs:** the generated `FileDescriptor`.
- **Outputs:** the service and method inventory.
- **Invariants:** one `ToolGateway` service; exactly the ten declared methods with the declared request/response
  pairing and streaming flags; every required message and enum present with a zero `*_UNSPECIFIED` value.
- **Cases:** `T30-TS-002 ServiceSurfaceComplete`, `T30-TS-003 MessageVocabularyComplete`.

### T030-SR-003-U — Version negotiation

- **Inputs:** `ProtocolVersion`, `GatewayCapabilities`, and the test-local compatibility predicate.
- **Outputs:** the declared version fields and the predicate verdict per tested major.
- **Invariants:** major/minor present; the predicate accepts major 1 and rejects every other major; no rejection
  depends on an absent field.
- **Cases:** `T30-TS-004 VersionNegotiationAndCapabilities`, `T30-TS-020 UnsupportedMajorVersionRejectedByPredicate`.

### T030-SR-004-U — Observation contract

- **Inputs:** `ObservationFilter`, `Identity`, `ObservationRecord`, `PayloadState`, open/read/close messages.
- **Outputs:** the metadata field inventory and the streaming flag of `ReadObservations`.
- **Invariants:** `ReadObservations` is server streaming; metadata fields present; payload view is explicit, bounded,
  and opt-in; metadata-only default.
- **Cases:** `T30-TS-005 ObservationStreamContractAndBounds`.

### T030-SR-005-U — Session contract

- **Inputs:** arm/revoke request and response messages.
- **Outputs:** the arm/revoke identity inventory.
- **Invariants:** permit, session, plan, graph, protocol, and validity fields present; `SessionState` present; no
  field bypasses the permit.
- **Cases:** `T30-TS-006 SessionArmRevokeContract`.

### T030-SR-006-U — Stimulation submission contract

- **Inputs:** `SubmitStimulationRequest`/`Response`, `StimulationAction`, `Schedule`, and the interaction/direction
  enums.
- **Outputs:** the action coverage inventory.
- **Invariants:** all four action kinds; both schedule modes; target/contract/interaction/direction present; timeline
  and payload bound present.
- **Cases:** `T30-TS-007 StimulationActionCoverage`.

### T030-SR-007-U — Service-emulation lease contract

- **Inputs:** acquire/release messages and `LeaseState`.
- **Outputs:** the lease identity inventory.
- **Invariants:** session, endpoint, generation, and plan bound on acquire; session and lease bound on release;
  exclusive states declared.
- **Cases:** `T30-TS-008 ServiceEmulationLeaseContract`.

### T030-SR-008-U — Outcome and counter contract

- **Inputs:** `StimulationOutcome`, `SessionCounters`, query messages.
- **Outputs:** the outcome/counter inventory.
- **Invariants:** evidence-incomplete outcome present; counters are the declared finite set; no dashboard/storage/
  query-presentation/export primitive.
- **Cases:** `T30-TS-009 SessionOutcomeCountersContract`; forbidden-vocabulary scan.

### T030-SR-009-U — Diagnostic contract

- **Inputs:** `Diagnostic`, `Severity`.
- **Outputs:** the diagnostic field inventory.
- **Invariants:** code, severity, phase, identity, reason, correction present and deterministically ordered by the
  accepted vocabulary.
- **Cases:** `T30-TS-010 DiagnosticContract`.

### T030-SR-010-U — Declared bounds

- **Inputs:** the descriptor of every bound field.
- **Outputs:** the bound inventory.
- **Invariants:** message/stream/deadline/queue/record/payload/lease bounds are explicit fields; every `bytes` field
  is accompanied by a declared size bound.
- **Cases:** `T30-TS-011 DeclaredBoundsPresent`, `T30-TS-018 NoImplicitUnboundedPayload`.

### T030-SR-011-U — Domain neutrality

- **Inputs:** every field name/type in the descriptor.
- **Outputs:** the forbidden-shape scan verdict.
- **Invariants:** no transport/address/port/socket/DNS/TLS/credential/export shape; no submission/lease without a
  session/permit identity.
- **Cases:** `T30-TS-017 NoTcpOrAddressPrimitive`, `T30-TS-019 NoBypassOfPermitOrSession`.

### T030-SR-012-U — Additive evolution rules

- **Inputs:** the descriptor, the pinned field manifest, and the reserved bands.
- **Outputs:** the additive-evolution verdict.
- **Invariants:** every message declares the 1000–1999 reserved band; no field uses a reserved number; the live field
  manifest equals the pinned manifest; a reserved number is not a live field.
- **Cases:** `T30-TS-012 ReservedExtensionBandDeclared`, `T30-TS-013 FieldNumberManifestPinned`,
  `T30-TS-021 ReservedNumberCannotBeReused`.

### T030-SR-013-U — Forward compatibility

- **Inputs:** bounded crafted wire buffers.
- **Outputs:** the round-trip preservation verdict.
- **Invariants:** an unknown field and an unmapped enum value survive a proto3 round trip and are preserved, not
  rejected or remapped.
- **Cases:** `T30-TS-014 AdditiveFieldInsertionBackwardCompatible`, `T30-TS-015 UnknownFieldForwardCompatible`,
  `T30-TS-016 UnmappedEnumValuePreserved`.

### T030-SR-014-U — Generated-code provenance

- **Inputs:** the generated Protocol Buffers and gRPC headers and the recorded generation provenance.
- **Outputs:** the provenance inspection verdict.
- **Invariants:** the generated message header carries the admitted protobuf runtime version and the schema's
  descriptor name; the generated gRPC header declares `ToolGateway` and the ten methods; the serialized descriptor
  round-trips.
- **Cases:** `T30-TS-022 GeneratedCodeProvenanceRecorded`, `T30-TS-023 GeneratedGrpcStubDeclaresService`,
  `T30-TS-024 SerializedDescriptorMatchesSource`.

### T030-SR-015-U — Additive build wiring

- **Inputs:** the build files and the test inventory.
- **Outputs:** the discovered test count and the runtime-target inventory.
- **Invariants:** one declared runtime-target addition; four additive `t030-<kind>` test targets; no existing target,
  test name, label, command, or expected value changes.
- **Cases:** changed-path and discovered-count inspection (CHK-16, CHK-17).

### T030-SR-016-U — Generated-contract test coverage

- **Inputs:** the four test suites.
- **Outputs:** the descriptor/service/version/bounds/vocabulary verdicts.
- **Invariants:** every declared contract element is asserted against the generated descriptor.
- **Cases:** `T30-TS-002`…`T30-TS-011` (see §2).

### T030-SR-017-U — Test safety

- **Inputs:** the test sources and the build link line.
- **Outputs:** the forbidden-API scan verdict.
- **Invariants:** only the C++ standard library, GTest, and the admitted protobuf runtime are used; no network,
  socket, resolver, TLS, ambient/secret, dynamic-load, subprocess, or legacy access; no new admitted dependency.
- **Cases:** forbidden-API source inspection (CHK-18).

### T030-SR-018-U — Public safety

- **Inputs:** every committed T030 file and evidence.
- **Outputs:** the public-safety scan verdict.
- **Invariants:** no credential, private address, real or proprietary payload, host path, or sensitive deployment
  value.
- **Cases:** public-safety inspection (CHK-19).

### T030-SR-019-U — Governance reconciliation

- **Inputs:** the T007–T010 registers and the work products.
- **Outputs:** the validator verdict and the recorded maturity.
- **Invariants:** registers unchanged; REF-002 `unchanged` with an empty `promoted` list; `XCOM-SW-GW-001` recorded
  implemented for the contract slice; T031–T041 remain allocated.
- **Cases:** register validators (CHK-20).

### T030-SR-020-U — Deterministic gate

- **Inputs:** the candidate revision and the Phase 7 gate.
- **Outputs:** the gate verdict.
- **Invariants:** the gate passes with a `t030-`-labelled discovered case; the checkbox is marked complete only at
  implementation; the diff is whitespace-clean.
- **Cases:** `xcom_phase7_gate.py verify T030 <baseline>` (CHK-21).

## 4. Case index

| Case | Suite | Primary requirement |
| --- | --- | --- |
| T30-TS-001 | XcomToolGatewayContract | T030-SR-001 |
| T30-TS-002 | XcomToolGatewayContract | T030-SR-002, T030-SR-016 |
| T30-TS-003 | XcomToolGatewayContract | T030-SR-002, T030-SR-016 |
| T30-TS-004 | XcomToolGatewayContract | T030-SR-003 |
| T30-TS-005 | XcomToolGatewayContract | T030-SR-004 |
| T30-TS-006 | XcomToolGatewayContract | T030-SR-005 |
| T30-TS-007 | XcomToolGatewayContract | T030-SR-006 |
| T30-TS-008 | XcomToolGatewayContract | T030-SR-007 |
| T30-TS-009 | XcomToolGatewayContract | T030-SR-008 |
| T30-TS-010 | XcomToolGatewayContract | T030-SR-009 |
| T30-TS-011 | XcomToolGatewayContract | T030-SR-010 |
| T30-TS-012 | XcomToolGatewayEvolution | T030-SR-012 |
| T30-TS-013 | XcomToolGatewayEvolution | T030-SR-012 |
| T30-TS-014 | XcomToolGatewayEvolution | T030-SR-013 |
| T30-TS-015 | XcomToolGatewayEvolution | T030-SR-013 |
| T30-TS-016 | XcomToolGatewayEvolution | T030-SR-013 |
| T30-TS-017 | XcomToolGatewayNegative | T030-SR-011 |
| T30-TS-018 | XcomToolGatewayNegative | T030-SR-010 |
| T30-TS-019 | XcomToolGatewayNegative | T030-SR-011 |
| T30-TS-020 | XcomToolGatewayNegative | T030-SR-003 |
| T30-TS-021 | XcomToolGatewayNegative | T030-SR-012 |
| T30-TS-022 | XcomToolGatewayProvenance | T030-SR-014 |
| T30-TS-023 | XcomToolGatewayProvenance | T030-SR-014 |
| T30-TS-024 | XcomToolGatewayProvenance | T030-SR-014 |

## 5. Coverage

Every `T030-SR-###` requirement is covered by at least one unit case or named inspection; every case belongs to
exactly one listed requirement and one suite. Unit cases are contributory; the exact acceptance decision remains
T039/T041.
