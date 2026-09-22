# X-Verse SADS v0.1 requirements traceability

**Source**: REF-002, `XVerse_System_Architecture_Design_v0.1.docx`
**Source SHA-256**: `ed99aa6caf1995e70a555edc36fed1938a071e60f3c1f6a4eebaae2c3423cb5a`
**Interpretation**: Target architecture and requirement input; not implementation evidence
**Machine-readable register**: [sads-requirements-traceability.json](sads-requirements-traceability.json)

## Coverage rule

All 275 unique requirement-ID occurrences in the supplied document are represented in the register.
Repository content records IDs, public-safe allocation, maturity, disposition, and feature trace only;
it does not reproduce the internal requirement text or illustrations.

Each future Spec Kit capability must select every applicable ID from this register and mark it
`implemented`, `partial`, `allocated`, `deferred`, `superseded`, `conflicting`, or
`needs_clarification`. An implemented status requires verification evidence. A requirement may span
multiple capabilities, but one owning acceptance gate must remain explicit.

## Component allocation

| SADS area | IDs accounted | vNext owner/allocation | Current maturity |
|---|---:|---|---|
| Scenario management | 28 | Maestro, Blueprints, UI, SDK | Architectural targets; XDL Scenario is an implemented precursor. |
| Model integration and execution | 25 | Simulation/model runtime, FMI boundary, Maestro | Architectural target. |
| Orchestration and resources | 58 | Maestro, Runtime, Time, Security | M3 lifecycle mechanics are a prototype precursor; generalized orchestration is a target. |
| Runtime environment | 23 | Runtime, Argus, Time, Security | M3 owned-fixture runtime is partial precursor evidence. |
| Communication and interoperability | 20 | X-COM | Capability 007 design allocation; no X-COM source exists. |
| User interface and accessibility | 20 | UI and SDK | Architectural target. |
| Monitoring, logging, observability | 19 | Argus | M3 evidence journaling is a precursor, not Argus. |
| Results management and export | 18 | Results, Argus, SDK | Architectural target. |
| Security and compliance | 20 | Security plus every subsystem’s local enforcement | Architectural target; current local permits are not platform IAM. |
| Extensibility and integration | 15 | SDK, Plugins, subsystem adapters | Architectural target; explicit composition precedes dynamic plugins. |
| Time synchronization and determinism | 14 | Time, Maestro, X-COM | Explicit time-domain models exist; runtime synchronization is a target. |
| Fault tolerance and recovery | 15 | Faults, Runtime, Maestro, Argus | Architectural target; bounded local failure semantics are precursors. |

The platform-first baseline in ADR-0018 includes all these owning components before target-specific
legacy integration resumes. This does not require one monolithic implementation feature.

## X-COM allocation

| SADS ID | Capability 007 disposition | Primary X-COM trace |
|---|---|---|
| XVE-SYS-0139 | Allocated | Domain-neutral bus and owned loopback prototype. |
| XVE-SYS-0140 | Allocated | Distinct signal/message and service interaction contracts. |
| XVE-SYS-0141 | Deferred | Protocol adapters follow the accepted provider boundary. |
| XVE-SYS-0142 | Allocated | Provider-neutral heterogeneous exchange. |
| XVE-SYS-0143 | Deferred | Initial explicit composition; registry/discovery is separate. |
| XVE-SYS-0144 | Deferred | Local validation permits do not satisfy general channel IAM. |
| XVE-SYS-0145 | Allocated | Explicit bounded QoS and capability negotiation. |
| XVE-SYS-0146 | Allocated | Schema/version and Profile-derived serialization policy. |
| XVE-SYS-0147 | Allocated | Clock-domain contract; hard real-time proof remains future work. |
| XVE-SYS-0148 | Deferred | Persistent record/replay is a later capability. |
| XVE-SYS-0149 | Allocated | Observation records, metrics, counters, and tool streams. |
| XVE-SYS-0150 | Deferred | Edge/cloud routing is outside the local prototype. |
| XVE-SYS-0151 | Deferred | Core records are defined; Argus/analytics adapters follow later. |
| XVE-SYS-0152 | Allocated | Controlled stimulation; workflow triggers also require Maestro. |
| XVE-SYS-0153 | Deferred | Remote transport security belongs to the Security baseline. |
| XVE-SYS-0154 | Allocated | Safe intent/outcome, provenance, audit evidence, and diagnostics. |
| XVE-SYS-0155 | Deferred | Multi-tenant isolation belongs to Security/deployment features. |
| XVE-SYS-0156 | Allocated | Versioned local external-tool gateway. |
| XVE-SYS-0157 | Deferred | Live protocol reconfiguration is separate from bounded lifecycle. |
| XVE-SYS-0158 | Deferred | Automatic failover/recovery follows the Faults/Runtime baselines. |

Related SADS requirements outside the communication section remain allocated to shared capabilities,
including protocol bridging/model exchange (XVE-SYS-0048–0049), communication-aware placement and
telemetry (XVE-SYS-0065, XVE-SYS-0089, XVE-SYS-0109–0111), runtime registry/metrics/traces
(XVE-SYS-0123, XVE-SYS-0126–0127), Argus integration (XVE-SYS-0179, XVE-SYS-0183,
XVE-SYS-0193–0194), extensibility (XVE-SYS-0237–0250), time (XVE-SYS-0251–0264), and communication
failure recovery (XVE-SYS-0265–0279). Capability 007 may establish contracts for these owners but does
not claim to implement their full system requirements.

## Source-quality observations

- Numeric IDs 4, 7, 104, and 105 are absent from the supplied sequence.
- `XVE-SYS-00014` and `XVE-SYS-00015` use nonstandard zero padding; their exact source IDs are
  preserved.
- `XVE-SYS-0044` ends mid-sentence in the supplied DOCX extraction. Its disposition remains
  `needs_clarification`; no missing intent is inferred.
- No duplicate exact requirement ID was found.

These observations do not authorize editorial repair of the supplied document. A corrected reference
revision must be registered by hash and reconciled explicitly.

