# Specification analysis — XDL loader, validator, and normalizer

**Date**: 2026-09-20
**Mode**: Read-only Spec Kit analysis before implementation.

## Findings

| ID | Severity | Category | Finding | Disposition |
|---|---|---|---|---|
| A01 | MAJOR (resolved in design) | Identity consistency | M2 collection-local ID prose conflicts with collection-free ElementRef/canonical identity. | ADR-0013 and FR-008 require resource-wide uniqueness; amend prose before implementation. |
| A02 | MINOR | Packaging | Authoritative schemas live outside the Python package but installed validation must remain offline. | Build must force-include the existing schema directory and a wheel-content test must prevent drift. |
| A03 | MINOR | Policy ordering | Profile payload validation is policy-like but normalized extensions require it before normalization. | Treat Profile resolution/schema validation as a semantic prerequisite and still label diagnostics with policy where appropriate. |
| A04 | MINOR | Readiness language | `Ready` could be mistaken for live readiness. | Public type and output must call it static readiness and document the evidence limit on every surface. |
| A05 | ADVISORY | API maturity | Initial Python surface may evolve while XDL semantic API remains stable. | Mark package prototype and separate package version from XDL API version. |
| A06 | REVIEW GATE | Acceptance | Human capability 004 and ADR-0013 disposition remain outstanding. | Complete after tests and separate architecture review; do not start M3 first. |

## Coverage

| Requirements | Tasks |
|---|---|
| FR-001–FR-006 | T005–T014 |
| FR-007–FR-015 | T015–T020, T023, T028 |
| FR-016–FR-019 | T021–T024, T028 |
| FR-020–FR-022 | T005, T009, T025–T027 |
| FR-023–FR-025 | T028–T035 |

All 25 functional requirements and eight success criteria map to tasks. No unresolved clarification,
template marker, constitutional violation, or unbounded implementation choice remains. Implementation
may proceed after A01's documented prose repair, which is included in T004.
