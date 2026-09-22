# Feature Specification: M0 legacy repository inventory

**Feature Branch**: `main` (existing branch; no branch creation required)
**Created**: 2026-09-20
**Status**: Implemented — M0 human review confirmed on 2026-09-20; M1 entry gate satisfied
**Input**: Implement the user-approved repository setup and public-safe M0 inventory plan.

## User Scenarios & Testing

### User Story 1 — Establish engineering governance (Priority: P1)
As a contributor, I can identify each repository's responsibility and use a consistent Spec Kit
workflow without modifying production or protected agent directories.
**Independent Test**: All three repositories contain usable Spec Kit assets, consistent constitutions,
engineering rules, and README instructions; original licenses and guidance are unchanged.
**Acceptance Scenarios**:
1. Given the three existing repositories, when initialized, then original files remain intact.
2. Given a companion repository, when following M0 documentation, then it resolves to the platform's
single feature specification rather than a duplicate.

### User Story 2 — Understand the existing ecosystem (Priority: P1)
As an architect, I can review every accessible legacy repository and trace factual claims to a
specific revision, distinguishing observed source, inference, and unknown runtime behavior.
**Independent Test**: Reconcile the inventory against a dated organization snapshot and inspect the
15 required fields and pinned sources for every repository.
**Acceptance Scenarios**:
1. Given an accessible repository, when inspected, then its source revision, purpose, interfaces,
dependencies, classification, candidate boundary, and uncertainties are recorded.
2. Given an empty, truncated, or inaccessible source, then the gap is explicit rather than fabricated.
3. Given private implementation evidence, then the deliverable contains only public-safe summaries.

### User Story 3 — Review readiness for M1 (Priority: P2)
As a reviewer, I can assess boundaries, dependencies, interfaces, classifications, and the existing
cruise-control startup chain without confusing recommendations with implemented runtime behavior.
**Independent Test**: Four inventory documents, a separate architecture review, and a human review
checklist consistently identify evidence and unresolved gaps.
**Acceptance Scenarios**:
1. Given reviewed sources, then dependency edges and interfaces have traceable evidence.
2. Given a ready M0 package, then M1 remains gated on human inventory review.

### Edge Cases
Handle empty repositories, archived/forked repositories, non-default branch baselines, missing
build/runtime contracts, API denial/rate limits, truncated trees, mutable artifact references,
contradictory documentation, private details, and unsupported claims of successful execution.

## Requirements
- **FR-001**: Initialize official Spec Kit 0.14.0 assets in all three vNext repositories without
changing protected directories, existing licenses, or the supplied guidance.
- **FR-002**: Define repository responsibilities, a consistent constitution, and ADR-0001–0004.
- **FR-003**: Enumerate all accessible organization repositories, identify vNext separately, and pin
legacy inspection to commit SHAs with coverage status.
- **FR-004**: Record the 15 section-40 fields, maturity, and evidence for every legacy repository.
- **FR-005**: Produce the four specified legacy documents, a dependency diagram, and an evidence-backed
cruise-control startup account with wrapper candidates.
- **FR-006**: Distinguish observation, inference, unknowns, redaction, and unverified runtime behavior;
exclude proprietary source excerpts, secrets, and sensitive infrastructure details.
- **FR-007**: Keep production repositories unchanged and do not launch production workloads.
- **FR-008**: Validate coverage, evidence references, document links, and preservation; record a separate
architecture review and the human review gate before M1.
- **FR-009**: Stop at setup and M0; introduce no runtime APIs, schemas, adapters, or executable blueprints.

### Key Entities
Repository snapshot; evidence reference; dependency observation; interface summary; classification;
coverage gap; review finding. These are documentation records, not an XDL metamodel.

## Success Criteria
- **SC-001**: All three repositories have consistent rules and official Spec Kit assets.
- **SC-002**: Every repository in the snapshot is accounted for as legacy or vNext.
- **SC-003**: Every legacy record contains all 15 fields, with explicit unknowns where evidence is absent.
- **SC-004**: All asserted source facts and dependency/interface observations reference pinned evidence.
- **SC-005**: The four documents and review package pass recorded validation with no unresolved
BLOCKER affecting M0 delivery; gaps that constrain M1 are listed separately.
- **SC-006**: Existing files and legacy repositories remain unchanged; no deliverable is published.

## Assumptions and clarified scope
The user selected setup + M0 and a public-safe audience on 2026-09-20. Inspect accessible repositories
using existing authenticated GitHub access. Default-branch snapshots are discovery evidence, not
necessarily deployed versions. M0 readers are contributors and architecture reviewers. All future
runtime capability decisions remain deferred.

## X-Verse capability obligations
**Compatibility impact**: None on production; documentary candidate boundaries only.
**Failure semantics**: Record read errors, missing contracts, or redacted evidence explicitly. Retry
transient reads; never silently omit a repository or infer execution success.
**Observable outcomes**: Coverage counts, source revisions, gap lists, validation results, and review findings.
**Maturity**: Documentation-only M0; no runtime capability implemented.
**Runtime tests**: Not applicable; no runtime changes or production execution.
