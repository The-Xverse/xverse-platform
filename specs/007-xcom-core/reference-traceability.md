# REF-002 traceability: X-COM core

**Source register**: [SADS requirements traceability](../../docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md)
**Machine-readable allocation**: [sads-requirements-traceability.json](../../docs/architecture/sads-requirements-traceability.json)

## Direct communication requirements

Capability 007 considers all twenty REF-002 communication/interoperability IDs,
`XVE-SYS-0139` through `XVE-SYS-0158`. Their allocation is:

- **Allocated to the first X-COM prototype**: XVE-SYS-0139, XVE-SYS-0140, XVE-SYS-0142,
  XVE-SYS-0145–0147, XVE-SYS-0149, XVE-SYS-0152, XVE-SYS-0154, and XVE-SYS-0156.
- **Deferred to protocol/provider capabilities**: XVE-SYS-0141.
- **Deferred to registry/reconfiguration capabilities**: XVE-SYS-0143 and XVE-SYS-0157.
- **Deferred to Security/deployment capabilities**: XVE-SYS-0144, XVE-SYS-0153, and XVE-SYS-0155.
- **Deferred to record/replay, edge/cloud, and Argus adapters**: XVE-SYS-0148, XVE-SYS-0150, and
  XVE-SYS-0151.
- **Deferred to Faults/Runtime recovery**: the automatic recovery portion of XVE-SYS-0158; capability
  007 still defines bounded communication failure outcomes.

“Allocated” means requirements and design coverage in this feature. It does not mean implemented.
Each allocated ID remains `architectural-target` until SESN-generated source and verification evidence
pass independent and human review.

## Shared requirements

Capability 007 also contributes contracts toward XVE-SYS-0048–0049, XVE-SYS-0065, XVE-SYS-0089,
XVE-SYS-0109–0111, XVE-SYS-0123, XVE-SYS-0126–0127, XVE-SYS-0179, XVE-SYS-0183,
XVE-SYS-0193–0194, XVE-SYS-0237–0250, XVE-SYS-0251–0264, and XVE-SYS-0265–0279. Their owning
capabilities remain Maestro, Runtime, Argus, SDK/Plugins, Time, Faults, or Security as recorded in the
program register.

## Conflict and maturity rules

- SADS examples naming specific protocols are adapter targets, not X-COM core primitives.
- SADS dynamic discovery, hot plugging, remote access, multi-tenancy, encryption, persistent replay,
  automatic failover, and dashboards remain outside the first local prototype.
- Constitution 2.1.0, ADR-0018, and ADR-0019 govern domain neutrality, platform-first sequencing,
  stimulation safety, and X-COM/Argus/Faults ownership.
- The supplied DOCX is a target specification and cannot by itself establish implementation,
  performance, security, compatibility, or production-readiness evidence.

