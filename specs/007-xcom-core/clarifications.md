# Clarification record: X-COM core communication and validation

**Date**: 2026-09-21
**Method**: Spec Kit ambiguity scan against the user decisions, Constitution 2.0.0, XDL v1alpha1,
ADR-0018, ADR-0019, and the existing M3 ownership/evidence semantics.

| ID | Area | Decision | Effect |
|---|---|---|---|
| C01 | Delivery order | Implement platform baselines before target-specific legacy integration. | SD-0001 remains preserved and deferred; X-COM uses owned fixtures only. |
| C02 | Capability scope | Normal communication, passive observation, and controlled stimulation are part of the first X-COM contract. | Validation is not added later as an ungoverned side channel. |
| C03 | Dashboard responsibility | X-COM publishes normalized tap records; Argus or third-party adapters own storage, queries, and dashboards. | No UI or telemetry database enters X-COM core. |
| C04 | Tool access | Define a provider-neutral contract and prove one local-only out-of-process gRPC/Protocol Buffers gateway with a separate-process synthetic client. | No TCP listener or remote authentication enters the first capability. |
| C05 | Stimulation authority | Stimulation is disabled by default and requires an exact bounded local validation permit. | Unauthorized or mismatched requests emit no traffic. |
| C06 | Interaction model | Distinguish signal/state, message/event, and service request/response semantics. | Providers cannot flatten semantic differences without declaring loss. |
| C07 | Observation payload | Metadata-only is the default; payload access is explicit, filterable, and auditable. | Sniffers and dashboards can operate without unrestricted payload disclosure. |
| C08 | Observer backpressure | Best-effort observation cannot block normal traffic; explicit lossless validation mode may. | Queue policy and effect on validity are evidence. |
| C09 | Provenance | Injected traffic remains synthetic/tool-originated through routing, tapping, and outcomes. | Validation evidence cannot confuse stimulus with SUT output. |
| C10 | Time | Every item identifies a clock domain; scheduled stimulation declares ordering and late policy. | Determinism and timing fidelity are not inferred. |
| C11 | Fault ownership | Faults owns campaigns and fault semantics; X-COM supplies bounded communication hooks. | Avoids coupling communication core to a fault taxonomy. |
| C12 | Language | X-COM's performance-critical core is C++ based. | The technical plan selects a supported C++ standard and versioned ABI boundaries. |
| C13 | CANoe reference | Treat CANoe as capability inspiration only. | No proprietary model reuse or compatibility claim. |
| C14 | Initial environment | Use loopback providers and synthetic nodes/tools without external peers. | Initial success is prototype evidence, not network or production readiness. |
| C15 | XDL policy placement | Use a versioned `io.xverse.xcom` Profile payload on existing interface, flow, network-binding, and scenario extension points. | The activation plan remains derived; no competing authored configuration is introduced. |
| C16 | Tool transport | Use pinned gRPC/Protocol Buffers over host-protected local IPC for the first external-tool proof. | Multi-language unary/streaming contracts are available while remote endpoints remain disabled. |
| C17 | Time authority | Scheduled stimulation requires an explicit clock-domain mapping and tolerance. | Missing or incomparable time fails or invalidates before emission as declared. |
| C18 | Service emulation | Acquire an exclusive lease bound to session, endpoint generation, and expiry. | Real and synthetic providers cannot ambiguously own one service endpoint. |

No clarification remains unresolved. Exact remote protocol, dashboard implementation, persistent
recording format, diagnostic databases, and first legacy adapter are intentionally separate features.
