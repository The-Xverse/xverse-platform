# ADR-0009: XDL resource model

**Status**: Accepted — user approved M2 on 2026-09-20.
**Date**: 2026-09-20

## Context

M1 defines separate system, realization, and experiment semantics. XDL needs authoring boundaries
that preserve those ownership rules while allowing resources to evolve and be reused independently.

## Decision

Define five independently versioned resource kinds: System, Component, Deployment, Scenario, and
Profile. All use a common envelope and structured references. System owns logical composition,
Component owns reusable logical capability, Deployment alone owns realization bindings, Scenario
owns experiment intent, and Profile owns an extension namespace. A Bundle/import resource is
deferred until concrete composition requirements exist.

## Consequences and alternatives

Resources have clear ownership and can be revised independently, but cross-resource validation is
required. A single monolithic document was rejected because it couples logical identity, environment
binding, and experiment revision. An open-ended `kind` mechanism was rejected for v1alpha1 because
it would weaken the reviewed semantic boundary.

## Evidence and scope

Guidance sections 15–24 and 42; approved M1 metamodel and ADR-0005–ADR-0008; M2 specification
FR-002–FR-010. This decision defines document ownership only. It does not define loader APIs,
registry behavior, imports, runtime plans, or orchestration.
