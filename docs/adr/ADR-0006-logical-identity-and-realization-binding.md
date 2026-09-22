# ADR-0006: Logical identity and realization binding

**Status**: Accepted — user approved M1 architecture review on 2026-09-20.
**Date**: 2026-09-20

## Context

The platform must support the same logical system across simulated, virtual, physical, and hybrid
environments. Legacy evidence also shows that environment-specific startup details are incomplete
and may differ from documentation.

## Decision

Keep System, Component, Node, Device, Interface, and Flow identities logical and stable. Use a
Deployment as the only environment-specific binding from those identities to ExecutionTargets,
Artifacts, Resources, Networks, TimeDomains, and Simulators. Provider-local addresses, credentials,
temporary paths, and process identifiers are overlay inputs and not core identity attributes.

## Consequences and alternatives

One logical device may have several bindings without identifier replacement. Resolution and
readiness become explicit validation concerns. Embedding realization facts directly in logical
objects was rejected because it destroys portability and risks exposing restricted infrastructure.

## Evidence and scope

Guidance sections 9–10, 14, 21–22, and 48; REF-001/REF-002 interpretation in the reference register.
This records semantics only; no deployment resolver or runtime lifecycle is implemented.
