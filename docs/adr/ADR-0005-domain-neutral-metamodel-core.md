# ADR-0005: Domain-neutral metamodel core

**Status**: Accepted — user approved M1 architecture review on 2026-09-20.
**Date**: 2026-09-20

## Context

M0 shows that existing implementations use domain-specific names, lifecycle assumptions, and
protocols. The platform needs a shared semantic vocabulary without treating any existing
implementation as the core model.

## Decision

Adopt the proposed core vocabulary in [METAMODEL.md](../architecture/METAMODEL.md): System,
Scenario, Component, Node, Device, Sensor, Actuator, ComputeResource, Interface, Endpoint, Flow,
Network, Link, Protocol, Model, Artifact, ExecutionTarget, Simulator, TimeDomain, Clock, Fault,
Observer, Metric, Parameter, Resource, and Deployment. Core terms describe semantic roles only.
Domain-specific concepts are profile or adapter extensions.

## Consequences and alternatives

The core becomes more deliberate than copying terminology from legacy sources, and future XDL must
use the approved vocabulary or record a new ADR. A broad industry-specific root model was rejected
because it violates domain neutrality and makes other CPS domains depend on a single proving ground.

## Evidence and scope

Guidance sections 3, 8–10, 17, 38, 41, and 48; M0 inventory and reference register. This decision
does not define a schema, runtime API, protocol binding, adapter, or compatibility claim.
