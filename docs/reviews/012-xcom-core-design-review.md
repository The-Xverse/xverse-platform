# X-COM core design review

**Review date**: 2026-09-21
**Scope**: `specs/007-xcom-core`, ADR-0018, ADR-0019, Constitution 2.0.0, and affected roadmap text
**Method**: Separate read-only architecture pass before repair
**Implementation reviewed**: None; this is a design-only review

## Initial findings

| ID | Severity | Finding | Required disposition |
|---|---|---|---|
| XCOM-D01 | MAJOR | The draft described a common external-tool boundary but limited the first proof to an in-process synthetic tool. That does not demonstrate use by an outside tool. | Add one local-only out-of-process reference gateway and separate-process synthetic client, while keeping remote control excluded. |
| XCOM-D02 | MAJOR | The plan said policy derives from XDL but did not define where interaction, provider, observation, and stimulation policy resides. | Define a namespaced `io.xverse.xcom` Profile payload attached through existing extension points and compile it into the activation plan. |
| XCOM-D03 | MAJOR | C++ JSON and tool-transport dependencies were unspecified, leaving reproducibility, licensing, and dependency risk unresolved. | Select dependency families in the plan and make exact version/hash/license/offline admission a blocking SESN preflight gate. |
| XCOM-D04 | MINOR | Timestamp fields were present without an explicit time-authority interface or behavior when clocks are incomparable. | Add a time-authority contract and fail/degrade scheduled stimulation when mapping is absent. |
| XCOM-D05 | MINOR | “At most one service emulator” lacked an exact lease/ownership lifecycle and conflict rule. | Bind a service-emulation lease to the validation-session handle and require atomic acquisition/release. |
| XCOM-D06 | ADVISORY | OpenTelemetry, ASAM XIL, and CANoe are useful integration references but could be mistaken for first-release compatibility. | Keep them in research only and repeat the no-compatibility statement in maturity/exclusions. |

No BLOCKER was found. XCOM-D01–D03 must be resolved before design acceptance. The reviewer did not
modify the reviewed files during this pass.

## Repair and re-review

The repair added FR-031–FR-034, SC-011, XDL Profile and local tool-gateway contracts, explicit
time-authority and service-lease entities, selected dependency families, and corresponding plan/tasks.
A second read-only pass verified the following:

| Finding | Resolution |
|---|---|
| XCOM-D01 | Resolved: a separate-process synthetic client must exercise a local-only gRPC/Protocol Buffers gateway; tests prove no TCP listener. |
| XCOM-D02 | Resolved: `io.xverse.xcom` Profile payload kinds and legal extension locations are defined and compiled into the activation plan. |
| XCOM-D03 | Resolved at design maturity: dependency families are selected; exact versions, hashes, licenses, generated-code provenance, and offline availability block SESN implementation admission. |
| XCOM-D04 | Resolved: scheduled stimulation uses `TimeAuthority` and fails or invalidates before emission when mapping is unavailable. |
| XCOM-D05 | Resolved: service emulation requires an atomic session/generation-bound exclusive lease. |
| XCOM-D06 | Resolved: research and exclusions repeat that no OpenTelemetry, ASAM XIL, CANoe, protocol, or legacy compatibility is delivered. |

Spec Kit prerequisite resolution selects `specs/007-xcom-core`. Placeholder, local-link, JSON, and
whitespace scans pass across the design package. All 34 functional requirements map to design and
implementation/evidence tasks. The second pass finds no unresolved BLOCKER or MAJOR issue.

**Verdict**: Ready for human design review. Source implementation remains unauthorized until ACC001–
ACC014 are accepted and the SESN dependency/toolchain preflight passes. Review 013 separately validates
the later REF-002 reconciliation amendment.
