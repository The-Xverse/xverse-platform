# ADR-0011: XDL serialization and schema foundation

**Status**: Accepted — user approved M2 on 2026-09-20.
**Date**: 2026-09-20

## Context

The architecture requires schema-first YAML/JSON and prohibits a premature custom language. XDL
needs one data model, strict typo detection, modular schemas, and tooling based on published standards.

## Decision

Use the JSON data model, with JSON or YAML 1.2.2 syntax, and JSON Schema Draft 2020-12 for structural
validation. Each kind has a schema, shared definitions live in `common.schema.json`, and
`xdl.schema.json` dispatches across kinds. Unknown core fields are rejected. Duplicate YAML keys,
non-string keys, and values without a JSON equivalent are parse errors. Presentation order, comments,
anchors, and aliases do not affect normalized meaning.

## Consequences and alternatives

The design can use mature parsers and validators while keeping one semantic representation. Semantic,
reference, readiness, and policy rules remain normative prose where JSON Schema is insufficient.
A custom grammar, YAML-specific semantics, permissive unknown fields, and schema-only validation were
rejected.

## Evidence and scope

Guidance sections 27, 34, 42, and 44; JSON Schema Draft 2020-12; YAML 1.2.2; M2 FR-001, FR-011,
FR-015, and FR-016. The M2 utility is acceptance tooling, not a production loader/validator library.
