# ADR-0018: Platform-first delivery sequence

**Status**: Accepted — directed by the user on 2026-09-21.

**Date**: 2026-09-21

## Context

The original architecture guidance placed a legacy cruise-control compatibility proof before native
vNext capabilities. M3 has since established useful platform-owned catalog, planning, lifecycle,
ownership, and evidence mechanics with an isolated fixture. Work toward the first legacy derivative
then exposed a sequencing risk: adapting a gateway before X-COM exists could make legacy protocol,
configuration, serialization, and lifecycle assumptions shape the platform contract.

The user made a formal decision to implement the main X-Verse platform components before attempting
integration with existing organizational repositories. Explicit user decisions may revise the
preserved guidance when their impact is recorded.

## Decision

Delivery is reordered into these architectural stages:

1. retain the approved M0–M3 evidence and platform-owned fixture mechanics;
2. specify, implement, and accept baseline capabilities for platform core/runtime, Maestro,
   simulation/model execution and FMI boundaries, X-COM, devices, time/fault handling, Argus,
   security, results, UI, SDK, and CLI through separate Spec Kit features;
3. stabilize the extension contracts that legacy adapters are required to implement;
4. resume target-specific work in `xverse-compat`, beginning with a new review of the pinned evidence;
5. perform parity and migration work only after the relevant platform and adapter gates pass.

“Baseline capability” means a reviewed contract plus an owned, isolated implementation and evidence
appropriate to that component. It does not mean every planned feature is complete or production-ready.
Dependencies continue to flow from blueprints and profiles into XDL/platform APIs and runtime
abstractions. Legacy repositories remain immutable.

SD-0001 and the controlled derivative mechanism remain retained evidence and a possible future
compatibility strategy. Target patching, provider implementation, gateway execution, and parity are
deferred until X-COM and its adjacent platform contracts are accepted. They are not rejected and their
prior evidence is not reclassified.

## Consequences

The milestone order in sections 25, 29, and 38 of the preserved architecture guidance is superseded by
this ADR and Constitution 2.0.0. “Compatibility before migration” still applies after platform
foundations exist: an initiative must prove compatibility before it can claim migration or replacement.

Platform APIs will be designed from domain-neutral requirements and controlled fixtures rather than a
single legacy bridge. Later adapters receive clearer conformance targets and should require less
target-specific logic in the platform. Cruise-control parity and M3 legacy-selection completion are
deferred until the platform-baseline gate is met.

The reordered work may delay the first legacy end-to-end demonstration. Each subsystem still requires
its own specification, authorization, validation, maturity statement, and separate review; this ADR
does not authorize all platform source code as one feature.
