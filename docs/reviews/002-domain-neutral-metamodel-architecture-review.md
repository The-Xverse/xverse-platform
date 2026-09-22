# M1 architecture review — domain-neutral metamodel

**Date**: 2026-09-20  
**Scope**: Approved M1 metamodel, diagram, ADR-0005 through ADR-0008, and Spec Kit package.  
**Review method**: Separate read-only review after document implementation and validation.  
**Disposition**: The user approved M1 on 2026-09-20. M2 specification/design may begin; its own
acceptance gates still apply.

## Architecture gates

| Concern | Assessment |
|---|---|
| Domain neutrality | Pass: core vocabulary has no industry-specific concept, provider, equipment class, simulator brand, or concrete protocol dependency. |
| Logical and physical separation | Pass: Deployment is the only logical-to-realization binding; Device realizations are explicit. |
| Production safety | Pass: M0 assets remain external; no legacy execution, checkout mutation, adapter, or compatibility claim is introduced. |
| XDL centrality and standards | Pass: M1 supplies semantic inputs to XDL, references external standards, and introduces neither custom grammar nor competing language. |
| Repository direction | Pass: architecture remains in platform; no companion implementation or reverse dependency appears. |
| Lifecycle, failure, and time | Pass for architecture: semantic profiles and explicit failure/evidence constraints are declared; runtime behavior is correctly deferred. |
| Reproducibility and maturity | Pass: Artifact/provenance/maturity rules distinguish declared and demonstrated behavior. |
| Documentation and public safety | Pass: no source excerpts, credentials, private addresses, or sensitive deployment values are present. |

## Findings

**BLOCKER**: none.  
**MAJOR**: none.

| ID | Severity | Finding / impact | Disposition |
|---|---|---|---|
| M1-R01 | Accepted MINOR | Identifier syntax and registry governance are intentionally deferred. Different downstream serializations could diverge without a single M2 decision. | Accepted as an M2 decision/ADR requirement before schemas or imports are implemented. |
| M1-R02 | Accepted MINOR | A generic lifecycle profile does not choose concrete readiness probes, cleanup ownership, or recovery behavior for any provider. | Accepted as a M3/M4 compatibility/runtime contract and test requirement. |
| M1-R03 | Resolved ADVISORY | The conceptual Mermaid diagram was not rendered by the documentation viewer. | Resolved in a subsequent render pass: [METAMODEL_DIAGRAM.svg](../architecture/METAMODEL_DIAGRAM.svg) is a standalone SVG; Mermaid remains editable source. Confirm visual semantics during human review. |
| M1-R04 | Accepted ADVISORY | Profile governance (registration, compatibility versioning, and conflict resolution) is not specified. | Address it when M2 defines XDL namespaces/versioning and before external profiles are accepted. |

## Review checklist

- [X] Core concepts are checked against the M1 directive.
- [X] Logical identity and realization separation are checked in text and diagram.
- [X] M0 R01–R05 are retained as constraints, not converted into runtime claims.
- [X] ADR scope and proposed status are checked.
- [X] XDL/schema/runtime exclusions are checked.
- [X] Domain neutrality, profile isolation, and standards-reference posture are checked.
- [X] Public-safe and maturity language is checked.
- [X] The user approved the M1 architecture and ADRs on 2026-09-20.

## Handoff

Resolve M1-R01 during M2 specification. M1-R02 remains a compatibility/runtime acceptance concern;
M1-R03 and M1-R04 remain review/governance follow-ups. The approved
[M1 decision record](../../specs/002-domain-neutral-metamodel/checklists/acceptance.md) satisfies
the entry gate for M2.
