# Implementation Plan: M3 component catalog and compatibility runtime

**Branch**: `main` | **Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

## Summary

Design a domain-neutral derived component catalog and side-effect-free lifecycle planner in
xverse-platform, anchored to normalized XDL Deployment binding → System instance → Component
relationships and `io.xverse.runtime.compatibility` binding payloads. A future xverse-compat provider
will supply component-specific actions. The first implementation proves mechanics with a controlled
fixture; it cannot execute a legacy component until a matching permit and selected-target decision exist.

## Technical Context

**Existing foundation**: capability 004 `xverse_xdl` package, immutable normalized resources, local
schemas, deterministic diagnostics, and explicit Profile-schema inputs.

**Future implementation shape**: a platform catalog/planning/lifecycle library and CLI; a separately owned
compatibility-provider contract in xverse-compat; public-safe fixture/evidence assets in platform.
Runtime Profile v0.2 preserves nominated candidates as deterministic blocked plans until their
decision evidence is complete, while v0.1 remains supported for the approved fixture.

**Storage**: local versioned XDL/Profile files, explicit local execution permits, an ownership journal,
and append-only intent/outcome evidence selected by the operator; no catalog service, registry,
database, or network discovery.

**Testing**: Profile/schema/reference/derivation tests, plan determinism, fixture lifecycle,
process/provider isolation, idempotency/concurrency/interruption, ownership reconciliation, evidence
failure, permit replay/mismatch/expiry, secret-blocking, public-safety, and no-legacy-diff checks.

**Constraints**: XDL centrality; no authored catalog format; closed local inputs; permit-free planning;
single-use execution permits; no secret resolution; handle-only ownership; durable intent before
mutation; no legacy checkout changes; no broad cleanup; no automatic retry; fixture before legacy proof.

## Constitution Check

- Production safety: catalog/planner accesses only explicit public-safe XDL graphs; legacy execution
  requires later scoped authorization and preserves source checkouts.
- Domain neutrality: catalog/runtime concepts do not name automotive protocols, ECUs, vehicles, or a
  provider; those belong to xverse-compat adapters or Profiles.
- XDL centrality: entries bind to XDL Component identity and Profiles instead of defining topology.
- Logical/physical: realization overlays and external assets remain separate from logical identity.
- Compatibility: future providers wrap unchanged external boundaries and capture limits/evidence.
- Repository direction: platform owns neutral contracts; xverse-compat owns legacy-specific providers;
  blueprints only consume stable platform/compat contracts.
- Maturity/evidence: fixture, lifecycle, compatibility, parity, and production-readiness claims remain
  separate and evidence-bounded.

## Proposed delivery phases

1. Record ADRs for XDL-anchored catalog shape and lifecycle ownership/no-inferred-cleanup.
2. Define the compatibility Profile schema, derived catalog entities, execution permit, ownership
   handle, evidence journal, stable diagnostics, and local catalog/plan CLI contracts.
3. Derive the closed catalog from normalized XDL Components, Systems, Deployments, Profiles,
   interfaces, realization, and provenance; create no second descriptor format.
4. Implement deterministic permit-free planning plus explicit readiness, timeout, secret-blocking,
   ownership, and failure gates.
5. Implement isolated process/provider boundaries, single-use permit checking, idempotent lifecycle,
   exclusive mutation, restart reconciliation, durable intent/outcome evidence, and a controlled fixture.
6. Define xverse-compat provider boundary and a selected-component decision-record template without
   embedding component-specific protocol behavior in platform.
7. After the ADR-0018 platform-baseline gate, an exact selected-target decision, and explicit execution
   authorization, implement and test one selected adapter against its pinned artifact/environment;
   record lifecycle evidence only, then conduct a separate architecture review.

## Decision gates

| Gate | Required decision | Current status |
|---|---|---|
| M3 design | Approve this specification, contracts, and ADRs. | Approved for implementation on 2026-09-20. |
| Fixture implementation | Authorize platform implementation without legacy execution. | Authorized and implemented on 2026-09-20. |
| Platform baseline | Accept the main platform components and stable extension contracts identified by ADR-0018. | Required before target-specific legacy work resumes. |
| Legacy selection | Select a component, artifact, environment, owner, contract, and exclusions. | Deferred behind the platform-baseline gate; SD-0001 remains blocked on owner/environment/interface/lifecycle/retention/vendor decisions. |
| Legacy execution | Approve exact lifecycle actions and evidence handling. | Deferred and not authorized. |
| M3 acceptance | Review fixture plus selected-component lifecycle evidence. | Deferred until the platform-baseline gate passes. |

## Complexity Tracking

No exception is proposed. The catalog and lifecycle planner are required to prevent M0's source-observed
legacy launcher behavior from becoming unbounded vNext runtime behavior.
