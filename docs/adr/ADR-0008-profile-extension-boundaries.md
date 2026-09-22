# ADR-0008: Profile and extension boundaries

**Status**: Accepted — user approved M1 architecture review on 2026-09-20.
**Date**: 2026-09-20

## Context

The platform must integrate existing standards and specialized domains while keeping a small core
that can evolve independently of each provider or industry.

## Decision

Use declared namespaces and profiles for specialized concepts, mappings, provider capabilities, and
standard bindings. An extension may add attributes, concepts, and mappings; it may not redefine a
core object’s identity, required relationships, or validation meaning. Standards and external model
formats are referenced through provenance and bindings rather than reimplemented in the core.

## Consequences and alternatives

Profiles can evolve alongside compatibility adapters and blueprints, while core consumers need only
understand stable references. Adding specialized concepts to the core or creating a competing
general-purpose modeling language was rejected as incompatible with the architectural baseline.

## Evidence and scope

Guidance sections 11–13, 16–20, 24, 33, 36–38, and 48. This does not define XDL namespace syntax,
schema validation, importer behavior, or any profile implementation.
