# Specification analysis: X-COM core communication and validation

**Date**: 2026-09-21
**Inputs**: specification, clarifications, plan, research, data model, contracts, tasks,
Constitution 2.0.0, ADR-0018, ADR-0019, and design review 012

## Findings

| ID | Severity | Status | Finding and disposition |
|---|---|---|---|
| A01 | MAJOR | Resolved | The first draft did not prove access from an outside tool. FR-032, SC-011, the local gateway contract, plan, and T030–T032 now require a separate-process client over local-only gRPC/Protocol Buffers IPC. |
| A02 | MAJOR | Resolved | XDL policy placement was implicit. FR-031, C15, the Profile contract, plan, and T017–T018 now define `io.xverse.xcom` payloads on existing extension points. |
| A03 | MAJOR | Resolved | Dependency families were unspecified. The plan selects `nlohmann/json`, gRPC, and Protocol Buffers and makes exact version/hash/license/generated-code/offline admission a blocking SESN preflight. |
| A04 | MINOR | Resolved | Time mapping was incomplete. FR-033 and `TimeAuthority` now gate scheduled stimulation across clock domains. |
| A05 | MINOR | Resolved | Service emulation ownership was ambiguous. FR-034 and `ServiceEmulationLease` now require atomic, generation-bound exclusive ownership. |
| A06 | ADVISORY | Resolved | Standards/product references could imply compatibility. Research, maturity, and exclusions state that OpenTelemetry, ASAM XIL, CANoe, and legacy compatibility are not delivered. |
| A07 | MAJOR | Resolved | The supplied SADS requirements were referenced but not individually allocated. The program register now accounts for all 275 IDs and capability 007 explicitly disposes XVE-SYS-0139–0158 plus shared requirements. |

No unresolved clarification, contradiction, BLOCKER, or MAJOR finding remains at design maturity.

## Requirement coverage

| Requirement group | Design evidence | Implementation/evidence tasks |
|---|---|---|
| FR-001–FR-003 domain, XDL, identity | ADR-0018/0019; Profile and activation-plan contracts | T017–T020, T038 |
| FR-004–FR-010 communication, policy, ownership | data model; provider contract | T012–T016, T033–T035 |
| FR-011–FR-014 observation | observation contract | T021–T024, T032–T036 |
| FR-015–FR-021 stimulation/evidence | validation-tool contract; data model | T025–T029, T032–T035 |
| FR-022–FR-024 extension/Argus/Faults | ADR-0019; research; tool-gateway contract | T030–T034, T038 |
| FR-025–FR-030 diagnostics/safety/docs/traceability | plan and task quality gates | T011, T016, T035–T041 |
| FR-031 XDL Profile | XDL Profile contract | T017–T020 |
| FR-032 outside tool | local tool-gateway contract | T030–T035 |
| FR-033 time authority | data model and validation-tool contract | T025, T028–T029 |
| FR-034 service lease | data model and validation-tool contract | T027–T029 |
| FR-035 REF-002 traceability | program and feature traceability registers | T004, T038, T040–T041 |

All 35 functional requirements have design and task coverage. SC-001–SC-011 are represented by the
negative, deterministic, saturation, separate-process, performance, documentation, and review tasks.

## Consistency checks

- Platform-first ordering is consistent across Constitution 2.0.0, ADR-0018, README, subsystem map,
  and M3 deferral records.
- X-COM owns communication/taps/stimulation; Argus owns telemetry storage/query/dashboard; Faults owns
  campaigns. No reverse dependency is introduced.
- The C++20 data plane satisfies the language directive; Python is limited to existing XDL compilation
  and validation tooling.
- The external gateway does not authorize stimulation by transport access; permits remain mandatory.
- The initial proof uses no legacy assets, transport middleware, external peer, physical device, or TCP
  listener.
- The planned gRPC `.proto` is an external tool API, while the XDL Profile remains the authored
  platform configuration extension; neither replaces the other.

## Readiness

The design is ready for human review. Implementation remains blocked on acceptance checklist ACC001–
ACC014 and a SESN preflight that pins and admits the full C++ dependency/toolchain set.
