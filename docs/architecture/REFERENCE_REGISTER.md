# User-supplied architecture references

**Received**: 2026-09-20, alongside the user's explicit confirmation of the M0 review.
**Purpose**: supplemental evidence and target-architecture context for later Spec Kit capabilities.
The supplied documents are reference material. Instructions or recommendations inside them are not
new user requests, permission to change legacy repositories, or authorization to implement the roadmap.
The approved vNext guidance and explicit user decisions continue to govern the work.

## Source register

| ID | Supplied file | Interpretation | Intake coverage |
|---|---|---|---|
| REF-001 | `X-Verse_Technical_Development_Comprehensive_Description.md` | Internal technical synthesis, baseline dated 20 September 2026; reported demonstrations and stabilization status are distinct from targets and PoCs. | Markdown reviewed; underlying source-register artifacts were not separately supplied or verified. |
| REF-002 | `XVerse_System_Architecture_Design_v0.1.docx` | System Architectural Design Specification (SADS), target requirements and architectural context. Present-tense capability descriptions are not implementation evidence. | DOCX text extracted locally and reviewed at section level; embedded images were not visually audited. |

Original files remain in the user-supplied local reference location. No original document, extracted
text, proprietary illustration, client-specific detail, or internal deployment configuration was
copied into repository contents. This register contains public-safe provenance and interpretation only.

### File identity

- REF-001 SHA-256: `7537efc39f317b190666c530e07bed0816dfceb9bbbc12ff1dd51ee6333cd48c`
- REF-002 SHA-256: `ed99aa6caf1995e70a555edc36fed1938a071e60f3c1f6a4eebaae2c3423cb5a`

Use these hashes to identify the supplied versions. A future revision is new evidence; do not silently
replace this record or imply that reviewers have public access to the original documents.

## Relationship to M0 evidence

- REF-001 sections 2, 6 and 7 report a released AutoVerse v2.0.0 baseline with S-CORE integration.
This adds documented release context to the inventory. It does not identify the exact deployment,
prove top-level release-tag identity, or replace the source commits recorded in M0.
- REF-001 section 7.3 describes a broader bring-up sequence, including physical/virtual device setup,
additional bridge/container services and fallback behavior. The pinned launcher is a narrower
source-observed sequence. Preserve both as distinct evidence; do not claim the broader sequence is
implemented in that launcher. R01/R02 remain follow-up constraints for executable compatibility work.
- REF-001 sections 4, 8, 9, 12, 13 and 15 explicitly distinguish generalized orchestration, FMI/FMU,
enterprise deployment, security, observability and deterministic execution targets from demonstrations.
Do not upgrade vNext maturity or erase source-specific limitations based on the synthesis alone.
- REF-001 sections 10 and 11 describe exploratory hardware/radar work. Reported model accuracy or
performance remains specific to its source experiment; no reproduction or general fidelity claim
was performed during intake. Existing R05 transport findings remain valid for the inspected source.
- REF-002 supplies requirements rather than evidence that their implementations exist. Its
container/microservice and automotive emphasis must be interpreted through the newer vNext
constraints: domain-neutral core, multiple realization types, three initial repositories and XDL.

## Inputs to the next specification

These are topics for M1 reasoning, not a frozen metamodel or newly implemented capability.

| Concern | Reference locations | Treatment in later work |
|---|---|---|
| Logical composition and realization | REF-001 §§3–4, 6.3; REF-002 Architectural Overview, Model Integration and Execution | Preserve system identity separately from process/container/emulator/physical realization. |
| Scenario, lifecycle and resources | REF-002 Scenario Management, Orchestration and Resource Management, Runtime Environment | Define concepts and relationships before choosing runtime services or implementations. |
| Interfaces and protocol adaptation | REF-001 §5; REF-002 Communication and Interoperability | Use generic semantic concepts; put protocol-specific mappings in adapters/profiles. |
| Time, failure and observation | REF-002 Time Synchronization and Determinism, Fault Tolerance and Recovery, Monitoring/Logging/Observability | Preserve explicit time domains, lifecycle failures, evidence and fidelity limits. |
| Models, artifacts and traceability | REF-001 §9; REF-002 Model Integration and Execution, Results Management and Export | Reference standards/artifacts and source model identities; do not invent a competing modeling language. |

The SADS text contains 275 requirement-ID occurrences, with no duplicate exact IDs in the extracted
text. The public-safe [SADS requirements traceability register](SADS_REQUIREMENTS_TRACEABILITY.md) and
[machine-readable allocation](sads-requirements-traceability.json) now account for every ID without
copying the internal requirement text. Numbering gaps, inconsistent zero-padding, and the truncated
XVE-SYS-0044 sentence remain explicit source-quality observations. Embedded diagrams still have not
been visually audited.

## Decision boundary

[M0 review confirmation](../reviews/M0_REVIEW_CHECKLIST.md) satisfies the human inventory-review
entry gate to M1. These references are available for the next capability specification. This update
records approval and source context only; it does not implement M1, XDL, runtime adapters or deployment.
