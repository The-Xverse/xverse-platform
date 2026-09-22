# ADR-0012: XDL extensions and standards references

**Status**: Accepted — user approved M2 on 2026-09-20.
**Date**: 2026-09-20

## Context

Domain and provider vocabularies must evolve without entering the core, and XDL must interoperate
with existing modeling, simulation, interface, and telemetry standards without reimplementing them.

## Decision

Place extension payloads only under an `extensions` map keyed by a reverse-domain namespace. Each key
must resolve to a compatible Profile with an external schema and conflict policy `reject`. Profiles
may add attributes and relationships but cannot replace identity, core relationships, or validation
meaning. XDL references standards and artifacts using versioned provenance and bindings; it does not
copy their complete semantic models.

## Consequences and alternatives

Specializations remain independently governed and unknown namespaces fail visibly. A global bag of
unvalidated properties and direct inclusion of industry/provider fields in core schemas were rejected.
Full reproduction of SysML/UML, SSP/FMI/FMU, protocol, or provider models was also rejected.

## Evidence and scope

Guidance sections 11–13, 24, 27, 33, 36–38, 42, and 48; ADR-0008; M2 FR-010, FR-012, FR-017, and
FR-018. No Profile implementation, standards adapter, catalog entry, or compatibility certification
is created by this decision.
