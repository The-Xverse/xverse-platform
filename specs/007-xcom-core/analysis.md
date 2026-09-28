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
| A09 | BLOCKER | Resolved 2026-09-27 | The bounded T025 successor passed exact-candidate verification and separate review, was explicitly accepted, and was merged into `main` as `4b01586b438a8587d231ee8828d896c206c06a96`. This closes only T025. |
| A10 | MAJOR | Resolved in tasks | T026 now defines bounded durability/failure semantics; T027 provides the pre-emission guard before T028 action paths; T029 covers journal, rejection, lifecycle, and concurrency behavior. |
| A11 | MAJOR | Resolved for workflow | T039–T041 now require separate read-only review, a repository-owned exact-candidate bundle, and explicit user acceptance. |
| A12 | MINOR | Accepted at exact successor revision | The user accepted T011–T016 and T021–T024 on 2026-09-28 after external review closed R-01. Their checked task entries and the T007 ownership register now bind acceptance to `2f08355c418a20eb00cbea18506f85bf2ea883b7`; the decision does not promote whole-capability or production maturity. |
| A13 | MAJOR | Resolved by accepted successor | Review 017 correctly identified T017–T020 as absent at its 2026-09-27 baseline. The later accepted T007–T010/T017–T020 successor adds the Profile schema, Python compiler, C++ decoder, tests, and work products; its decision is `docs/engineering/xcom/t007-t020-acceptance-decision.md`. |

## 2026-09-27 terminal review R-01 repair

Terminal review R-01 observed that the final T011–T016/T021–T024 candidate checked T012–T016 and
T021–T024 complete in `tasks.md` while the ownership register still recorded each as `unreconciled`
"because the capability task checkbox is open", and A12 still asserted that those task checkboxes
required reconciliation. The literal checkbox-open reason is now false.

The repair replaces the false reason with a `delivered` reconciliation state in
`docs/engineering/xcom/task-ownership.json` and its deterministic projection
`docs/engineering/xcom/task-ownership.md`. Each of the nine tasks records its exact reviewed terminal
candidate revision and states that external Codex review and explicit user acceptance remain pending.
A12 is disposed above. The register validator (`scripts/validate_xcom_task_ownership.py`) pins the
delivered set and fails closed on a missing, malformed, or divergent revision or an empty reason, and
`scripts/validate_xcom_requirements_traceability.py` still requires a requirement owned by a delivered
task to stay `partial` with a recorded reason.

This is a governance-record repair only. No task is marked accepted, no requirement, component, or unit
maturity is promoted, no REF-002 disposition changes, and no production semantics, contract, schema, or
existing test expectation is altered. The only test-tree addition is a new offline governance regression
test that pins this repaired state. The accepted predecessor work products T008, T009, and T010 retain
their historical open-checkbox language byte-unchanged; that language is superseded for the current state
by this dated successor note, not rewritten. The repaired successor candidate still requires its own
external Codex review and explicit user acceptance before any task in this range closes.

## 2026-09-28 user acceptance

The user accepted the externally reviewed successor `2f08355c418a20eb00cbea18506f85bf2ea883b7`.
`docs/engineering/xcom/t011-t024-acceptance-decision.md` records the bounded decision. The T007
ownership register and deterministic projection now mark exactly T011–T016 and T021–T024 accepted at
that revision. The preceding R-01 repair text remains historical evidence of the pre-acceptance state;
it is superseded for current task status by this dated decision. Requirements still marked `partial`
retain their existing capability-level limitations; task acceptance alone does not promote them.

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

The technical design and T025 remain accepted. Review 017 records the state at its earlier baseline;
the later accepted successors close T007–T020 and T021–T024 at their exact revisions. The capability
remains partial. T026 and every other open task require their own applicable authorization and gates.
