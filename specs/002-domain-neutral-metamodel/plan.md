# Implementation Plan: M1 domain-neutral metamodel

**Branch**: \`main\` (unchanged); **Spec Kit feature key**:
\`002-domain-neutral-metamodel\`
**Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

## Summary

Define and review a domain-neutral semantic metamodel for a multi-industry cyber-physical platform.
The result is an architecture package: a normative vocabulary, conceptual diagram, four proposed ADRs,
traceability, validation, and a separate architecture review. No production/runtime implementation is
in scope.

## Technical Context

**Language/Version**: Markdown and Mermaid; Python 3 standard library for documentary validation.
**Primary Dependencies**: Spec Kit 0.14.0 assets, Bash, Python 3.
**Storage**: versioned architecture and specification documentation only.
**Testing**: prerequisite resolution, structural/semantic document validation, link checks, visual
Mermaid source inspection, public-safety review, separate architecture review.
**Target Platform**: current Linux workspace; no external runtime target.
**Project Type**: architecture documentation and governance.
**Performance Goals**: none; no runtime behavior is introduced.
**Constraints**: domain neutrality, legacy immutability, XDL centrality, explicit maturity/evidence,
local-only changes, public-safe content, no XDL/schema/runtime/adapters.
**Scale/Scope**: 26 core concepts, four ADRs, one conceptual diagram, and M1 review package.

## Constitution Check

Pass, subject to human architecture review. The model is domain-neutral; logical identity and
realization are separate; physical/hybrid realization is explicit; extensions preserve dependency
direction; M0 legacy evidence remains external and immutable; XDL remains canonical but unimplemented.
Lifecycle and evidence are semantic contracts only. No maturity claim exceeds documentation evidence.

## Project Structure

\`\`\`text
docs/
├── architecture/
│   ├── METAMODEL.md
│   └── METAMODEL_DIAGRAM.md
├── adr/
│   ├── ADR-0005-domain-neutral-metamodel-core.md
│   ├── ADR-0006-logical-identity-and-realization-binding.md
│   ├── ADR-0007-lifecycle-time-and-evidence-semantics.md
│   └── ADR-0008-profile-extension-boundaries.md
└── reviews/
    └── 002-domain-neutral-metamodel-architecture-review.md
specs/002-domain-neutral-metamodel/
├── spec.md
├── clarifications.md
├── research.md
├── data-model.md
├── plan.md
├── quickstart.md
├── tasks.md
├── analysis.md
└── checklists/
    ├── requirements.md
    └── acceptance.md
scripts/
└── validate_m1.py
\`\`\`

**Structure Decision**: Documentation-only M1 stays in the platform repository because it owns
architecture governance. Companion repositories receive no implementation or duplicate M1 spec.

## Execution

1. Create the feature specification and record bounded clarification defaults.
2. Trace the M1 vocabulary to approved guidance, M0 constraints, and supplemental reference context.
3. Define every required entity, layers, relationships, lifecycle profiles, invariants, and extension
   boundaries in public-safe language.
4. Record major modeling choices as proposed ADRs; create a relationship diagram.
5. Validate required entity coverage, links, prohibited implementation claims, ADR consistency, and
   absence of unresolved template markers.
6. Run a separate read-only architecture review. Do not repair its findings in that review pass.
7. Mark the package ready for human M1 review; human ADR approval is required before M2.

## Public interfaces and failure semantics

No runtime APIs, types, schemas, protocol identifiers, package contracts, or deployment values are
created. Semantic failures are unresolved reference, invalid ownership/direction, incompatible
contract, missing binding, absent artifact evidence, unavailable resource, missing time mapping, or
illegal profile redefinition. Their executable handling is deferred.

## Complexity Tracking

No constitutional exception. A standard-library validator is justified because it provides durable,
repeatable checks for the complete vocabulary, cross-document links, proposed-architecture status,
and forbidden runtime-scope artifacts.
