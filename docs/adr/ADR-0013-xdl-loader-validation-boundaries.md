# ADR-0013: XDL loader and validation boundaries

**Status**: Accepted — user approved capability 004 on 2026-09-20.
**Date**: 2026-09-20

## Context

The approved XDL v1alpha1 contract needs an executable reference loader. Deterministic reference
resolution, extension validation, untrusted-input limits, and the handoff to normalized semantics
must be fixed before code. M2 prose also described element IDs as collection-local while ElementRef
and canonical element identity do not include a collection, permitting ambiguous references.

## Decision

Implement a local, offline, bounded pipeline with ordered parse, schema, reference, semantic,
normalization, static binding/readiness, and policy stages. Inputs are an explicit closed resource set.
Core and Profile schemas are explicit local registries; no resolver performs network or ambient
filesystem discovery. Return stable diagnostics and no partial normalized graph after a gate 1–4 error.

Element IDs are unique across the complete owning resource. This is a semantic clarification of
v1alpha1 necessitated by the approved collection-free ElementRef shape. It preserves current schemas,
examples, and canonical URI syntax while rejecting previously ambiguous documents.

Static Deployment readiness evaluates declared completeness only. It does not retrieve artifacts,
probe targets, allocate resources, or establish live readiness.

## Consequences and alternatives

Validation is reproducible and safe for local automation, but callers must supply a complete graph and
Profile schemas. Registry discovery and streaming are deferred. Adding a collection field to ElementRef
was rejected because it would break the approved alpha schema; allowing duplicate cross-collection IDs
was rejected because reference resolution would be nondeterministic.

A Python reference package uses maintained YAML 1.2 and JSON Schema Draft 2020-12 libraries rather
than reimplementing those standards. Its package API is prototype maturity and is not a production
service contract.

## Evidence and scope

Approved M2 `VALIDATION.md`, `NORMALIZED_MODEL.md`, ADR-0009–ADR-0012, capability 004 clarification
C01–C10, and dependency research. This ADR does not authorize runtime plans, orchestration, live
readiness, registries, adapters, catalogs, blueprints, or legacy execution.
