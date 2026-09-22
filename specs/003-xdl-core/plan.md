# Implementation Plan: M2 XDL Core v0.1 specification

**Branch**: \`main\` (unchanged); **Spec Kit feature key**: \`003-xdl-core\`
**Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

## Summary

Produce an architecture-grade XDL v1alpha1 specification with five resource kinds, strict Draft
2020-12 schema drafts, YAML examples, normalized-model and validation rules, versioning, four ADRs,
offline documentary checks, and a separate review. No loader/runtime code is included.

## Technical Context

**Language/Version**: Markdown; JSON Schema Draft 2020-12; YAML 1.2.2; Python 3 validator using the
standard library plus already-available PyYAML for example parsing.
**Primary Dependencies**: Spec Kit 0.14.0, Python 3, PyYAML 6.0.3.
**Storage**: repository files only; no service or database.
**Testing**: JSON/YAML parsing, schema/ref integrity, positive examples, negative semantic fixtures,
traceability, placeholder/link checks, public-safety scan, separate architecture review.
**Target Platform**: portable specification; validation executed in the current Linux workspace.
**Project Type**: language specification and schema design.
**Performance Goals**: none; no production validator/runtime is implemented.
**Constraints**: domain neutrality, XDL centrality, M1 invariants, legacy immutability, standards
reference over duplication, public-safe examples, local changes only.
**Scale/Scope**: five resource schemas, shared schema, root dispatch schema, five examples, six
negative fixtures, four ADRs, specification/review package.

## Constitution Check

Pass, subject to M2 human review. XDL is the canonical representation, starts with the approved M1
semantics, uses YAML/JSON schemas, keeps logical identity separate from Deployment, treats physical
realization explicitly, isolates profiles/extensions, references standards, records maturity and
provenance, and changes no legacy repository. Loader/runtime/adapter work is excluded.

## Project Structure

\`\`\`text
specs/003-xdl-core/
├── spec.md
├── clarifications.md
├── research.md
├── data-model.md
├── plan.md
├── quickstart.md
├── tasks.md
├── analysis.md
├── validation.md
└── checklists/
    ├── requirements.md
    └── acceptance.md
xdl/
├── specification/
│   ├── XDL_CORE_V0_1.md
│   ├── RESOURCE_MODEL.md
│   ├── VALIDATION.md
│   └── VERSIONING.md
├── metamodel/
│   └── NORMALIZED_MODEL.md
├── schemas/v1alpha1/
│   ├── common.schema.json
│   ├── component.schema.json
│   ├── deployment.schema.json
│   ├── profile.schema.json
│   ├── scenario.schema.json
│   ├── system.schema.json
│   └── xdl.schema.json
└── examples/v1alpha1/
    ├── component.xdl.yaml
    ├── deployment.xdl.yaml
    ├── profile.xdl.yaml
    ├── scenario.xdl.yaml
    └── system.xdl.yaml
docs/
├── adr/ADR-0009...ADR-0012...
└── reviews/003-xdl-core-architecture-review.md
scripts/
└── validate_m2.py
\`\`\`

## Execution

1. Specify and clarify the M2 language boundary.
2. Record external-format research and architecture decisions.
3. Define resource envelope, identity/reference, versioning, extension, normalization, and validation.
4. Create strict structural schemas and public-safe examples for all five kinds.
5. Add documentary validator and negative fixtures generated in memory during self-test.
6. Analyze cross-artifact coverage and perform a separate read-only architecture review.
7. Present M2 for human approval before any loader/validator/runtime implementation capability.

## Failure semantics

A failure reports gate, stable code, severity, resource identity when available, source location or
JSON Pointer, message, and related references. Parse or schema failure blocks normalization. Reference
or semantic failure blocks a valid model. Binding/readiness failure blocks executable readiness.
Policy failure blocks the action required by policy; it must not silently rewrite the document.

## Complexity Tracking

No constitutional violation. Modular schemas are justified by independent resource ownership and
reuse. The local validator is documentary conformance tooling, not the future XDL loader/validator
library; it performs bounded checks required to make the schema package reviewable.

