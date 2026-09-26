# Specification analysis: X-COM core communication and validation

**Date**: 2026-09-21
**Inputs**: specification, clarifications, plan, research, data model, contracts, tasks,
Constitution 2.0.0, ADR-0018, ADR-0019, and design review 012

## Findings

| ID | Severity | Status | Finding and disposition |
|---|---|---|---|
| A01 | MAJOR | Resolved | The first draft did not prove access from an outside tool. FR-032, SC-011, the local gateway contract, plan, and T030–T032 now require a separate-process client over local-only gRPC/Protocol Buffers IPC. |
| A02 | MAJOR | Resolved | XDL policy placement was implicit. FR-031, C15, the Profile contract, plan, and T017–T018 now define `io.xverse.xcom` payloads on existing extension points. |
| A03 | MAJOR | Resolved | Dependency families were unspecified. The plan selects `nlohmann/json`, gRPC, and Protocol Buffers and makes exact version/hash/license/generated-code/offline admission a blocking repository-owned preflight. |
| A04 | MINOR | Resolved | Time mapping was incomplete. FR-033 and `TimeAuthority` now gate scheduled stimulation across clock domains. |
| A05 | MINOR | Resolved | Service emulation ownership was ambiguous. FR-034 and `ServiceEmulationLease` now require atomic, generation-bound exclusive ownership. |
| A06 | ADVISORY | Resolved | Standards/product references could imply compatibility. Research, maturity, and exclusions state that OpenTelemetry, ASAM XIL, CANoe, and legacy compatibility are not delivered. |
| A07 | MAJOR | Resolved | The supplied SADS requirements were referenced but not individually allocated. The program register now accounts for all 275 IDs and capability 007 explicitly disposes XVE-SYS-0139–0158 plus shared requirements. |

No unresolved clarification, contradiction, BLOCKER, or MAJOR finding remained at the original
design maturity.

## 2026-09-26 workflow amendment

Review 015 evaluated T026–T041 after the user retired SESN from future work.

| ID | Severity | Status | Finding and disposition |
|---|---|---|---|
| A08 | BLOCKER | Resolved for governance | ADR-0020, ACC015, the plan, tasks, contracts, traceability, and build-evidence language now assign future work to the repository-owned Spec Kit workflow. |
| A09 | BLOCKER | Open implementation prerequisite | T025 has no accepted successor in the current baseline. T026 remains blocked until T025 passes exact-candidate verification, separate review, and explicit user acceptance. |
| A10 | MAJOR | Resolved in tasks | T026 now defines bounded durability/failure semantics; T027 provides the pre-emission guard before T028 action paths; T029 covers journal, rejection, lifecycle, and concurrency behavior. |
| A11 | MAJOR | Resolved for workflow | T039–T041 now require separate read-only review, a repository-owned exact-candidate bundle, and explicit user acceptance. |
| A12 | MINOR | Open reconciliation | T012–T024 task checkboxes still require reconciliation against exact accepted revisions; source presence alone is insufficient. |

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

- Platform-first ordering is consistent across Constitution 2.1.0, ADR-0018, README, subsystem map,
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

The technical design remains accepted. Future implementation follows ACC015 and ADR-0020. T026 is
blocked until T025 has an accepted successor, the dependency/toolchain set is admitted through the
repository-owned preflight, and accepted earlier slices are reconciled to exact revisions.
