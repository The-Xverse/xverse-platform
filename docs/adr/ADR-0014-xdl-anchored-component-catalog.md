# ADR-0014: XDL-anchored component catalog

**Status**: Accepted — M3 fixture implementation authorized 2026-09-20.
**Date**: 2026-09-20

## Context

M3 needs externally maintained, reproducible descriptions of legacy component boundaries. A standalone
descriptor language could duplicate or drift from M2's canonical XDL resource model. M0 also shows
that repository names, README commands, mutable tags, and ambient environments are not sufficient
runtime contracts.

## Decision

Define no independently authored catalog-entry document. The catalog is a deterministic derived index
over a closed normalized XDL graph. Each entry is identified by exact Deployment identity plus binding
ID and resolves that binding through its System component instance to one exact Component identity.

Typed operational fields use the `io.xverse.runtime.compatibility` Profile payload attached only to
the Deployment binding's existing `extensions` field. Artifact provenance, realization class, target,
resources, and core lifecycle declaration remain in the existing Deployment resource. Interfaces and
logical capabilities remain in Component/System. This does not add a new XDL kind or place realization
data in a logical Component.

The catalog input set is explicit and local. Resolution is deterministic, revision-pinned, and offline;
it performs no repository scan, registry discovery, current-directory fallback, or network lookup.

## Consequences

Catalog validation can establish XDL graph completeness and reference consistency, not executable
compatibility, lifecycle success, artifact availability, or application behavior. Protocol/provider
details stay in a future xverse-compat adapter or Profile. An unpinned, ambiguous, sensitive, or
unsupported boundary fails closed.

## Scope

This ADR proposes a future Profile schema but does not introduce code, a catalog service, a selected
component-specific payload, repository change, adapter, or execution authority. Those require M3 implementation authorization and
the selected-component decision gate.
